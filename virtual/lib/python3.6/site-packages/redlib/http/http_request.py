from io import StringIO, BytesIO
import sys
from functools import partial
import socket
import tempfile
from os import fdopen
from time import time

from enum import Enum

from redlib.api.system import *
from redlib.api.prnt import format_size
from .cache import Cache, CacheError


if is_py3():
	from urllib.error import HTTPError as UrllibHTTPError, URLError
	from urllib.request import urlopen, Request
else:
	from urllib2 import HTTPError as UrllibHTTPError, urlopen, URLError, Request


__all__ = ['HttpErrorType', 'HttpError', 'GlobalOptions', 'RequestOptions', 'HttpRequest']


HttpErrorType = Enum('HttpErrorType', ['other', 'timeout', 'size', 'length'])


class HttpError(Exception):

	def __init__(self, msg, err_type=HttpErrorType.other, code=None):
		super(HttpError, self).__init__(msg)
		self.err_type = err_type
		self.code = code


class GlobalOptions:

	def __init__(self, cache_dir=None, chunksize=50*1024, headers=None, timeout=120, max_content_length=1024*1024*10, cache_timeout='1d'):
		self.cache_dir		= cache_dir
		self.chunksize		= chunksize
		self.headers		= headers
		self.timeout		= timeout
		self.max_content_length	= max_content_length
		self.cache_timeout	= cache_timeout


class RequestOptions:

	def __init__(self, save_filepath=None, nocache=False, open_file=None, headers=None, save_to_temp_file=False,
			progress_cb=None, progress_cp=None, content_length_cb=None, rate_cb=None, cached_cb=None,
			max_content_length=None, cache_timeout=None, decode_strat='replace', decode_repl='?'):

		self.save_filepath	= save_filepath
		self.nocache		= nocache
		self.open_file		= open_file
		self.headers		= headers
		self.progress_cb	= progress_cb
		self.progress_cp	= progress_cp
		self.content_length_cb	= content_length_cb
		self.rate_cb		= rate_cb
		self.cached_cb		= cached_cb
		self.max_content_length	= max_content_length
		self.save_to_temp_file	= save_to_temp_file
		self.cache_timeout	= cache_timeout
		self.decode_strat	= decode_strat
		self.decode_repl	= decode_repl

		self.temp_filepath	= None


	def call_progress_cb(self, value):
		if self.progress_cb is not None:
			self.progress_cb(value)


	def call_progress_cp(self):
		if self.progress_cp is not None:
			self.progress_cp()


	def call_content_length_cb(self, value):
		if self.content_length_cb is not None:
			self.content_length_cb(value)


	def call_rate_cb(self, value):
		if self.rate_cb is not None:
			self.rate_cb(value)


	def call_cached_cb(self, value):
		if self.cached_cb is not None:
			self.cached_cb(value)


class HttpRequest:

	def __init__(self, global_options=None):
		self._goptions = GlobalOptions() if global_options is None else global_options
		self._cache = None

		if self._goptions.cache_dir is not None:
			try:
				self._cache = Cache(self._goptions.cache_dir)
			except CacheError as e:
				pass


	def get(self, url, request_options=None):
		roptions = RequestOptions() if request_options is None else request_options
		if roptions.max_content_length is None or (roptions.max_content_length > self._goptions.max_content_length):
			roptions.max_content_length = self._goptions.max_content_length

		cached_res = self.check_cache(url, roptions)
		if cached_res:
			return cached_res

		res = None
		headers = self.combine_headers(roptions)

		if headers is None:
			res = self.exc_call(urlopen, roptions, url, timeout=self._goptions.timeout)
		else:
			res = self.exc_call(urlopen, roptions, Request(url, None, headers), timeout=self._goptions.timeout)

		out = self.get_outbuffer(roptions)
		content_length = self.get_content_length(res, roptions)

		if content_length is not None and content_length > roptions.max_content_length:		# take care of open buffers
			res.close()
			raise HttpError('max content length exceeded', err_type=HttpErrorType.size)

		content_read = self.read_response_chunks(res, out, content_length, roptions)
		
		roptions.call_progress_cp()

		res.close()

		self.cache_response(url, out, roptions)
		return self.close_outbuffer(out, roptions)
	
	
	def combine_headers(self, roptions):
		headers = None
		if self._goptions.headers is not None:
			headers = self._goptions.headers
		
		if roptions.headers is not None:
			if headers is not None:
				headers.update(roptions.headers)
			else:
				headers = roptions.headers

		return headers	

	def read_response_chunks(self, response, out, content_length, roptions):
		start_time = time()
		chunk = self.exc_call(response.read, roptions, self._goptions.chunksize)

		content_read = 0.0

		while chunk:
			buf = bytes(chunk)
			out.write(buf)

			content_read += len(chunk)

			if roptions.max_content_length is not None and content_read > roptions.max_content_length:
				res.close()
				raise HttpError('max content length exceeded', err_type=HttpErrorType.size)

			roptions.call_rate_cb(int(content_read/((time() - start_time) or 1e-6)))

			if content_length is not None:
				roptions.call_progress_cb((content_read / content_length) * 100)
			else:
				roptions.call_content_length_cb(content_read)
				roptions.call_progress_cb(None)

			chunk = self.exc_call(response.read, roptions, self._goptions.chunksize)

		if content_length is not None:
			if content_read != content_length:
				raise HttpError('response incomplete / corrupt', err_type=HttpErrorType.length)

		return content_read


	def cache_response(self, url, out, roptions):
		if not roptions.nocache and self._cache is not None:
			out.seek(0)
			timeout = roptions.cache_timeout or self._goptions.cache_timeout
			self._cache.add(url, out.read(), timeout, hash=True)


	def close_outbuffer(self, out, roptions):
		if roptions.save_to_temp_file:
			out.close()
			return roptions.temp_filepath

		elif roptions.save_filepath is not None:
			out.close()
			return True

		elif roptions.open_file is not None:
			return True

		else:
			out.seek(0)
			buf = out.read()
			out.close()
			if is_py3():
				buf = buf.decode('utf-8', roptions.decode_strat)
				if roptions.decode_strat == 'replace':
					buf = buf.replace('\ufffd', roptions.decode_repl)
			return buf


	def get_outbuffer(self, roptions):
		if roptions.save_to_temp_file:
			f, path = tempfile.mkstemp()
			roptions.temp_filepath = path
			out = fdopen(f, 'r+b')

		elif roptions.save_filepath is not None:
			out = open(roptions.save_filepath, 'wb+')

		elif roptions.open_file is not None:
			out = roptions.open_file
		
		else:
			out = BytesIO()

		return out


	def get_content_length(self, response, roptions):
		content_length = response.headers.get('Content-Length')
		if content_length is not None:
			content_length = int(content_length) 

			roptions.call_content_length_cb(content_length)

		return content_length


	def exc_call(self, func, roptions, *args, **kwargs):
		exc = False

		try:
			r = func(*args, **kwargs)
			return r

		except (URLError, UrllibHTTPError) as e:
			exc = True
			err_msg = str(e)
			if type(e.reason) == socket.timeout:
				err_type = HttpErrorType.timeout
			else:
				err_type = HttpErrorType.other
		except socket.timeout as e:
			exc = True
			err_msg = str(e)
			err_type = HttpErrorType.timeout

		if exc:
			roptions.progress_cp()
			raise HttpError(err_msg, code=None, err_type=err_type)


	def check_cache(self, url, request_options=None):
		roptions = RequestOptions() if request_options is None else request_options

		if not roptions.nocache and self._cache is not None:
			data = self._cache.get(url, hash=True)
			if data is not None:
				roptions.call_content_length_cb(len(data))

				info = self._cache.info(url, hash=True)
				roptions.call_cached_cb(info)

				roptions.call_progress_cp()

				out = self.get_outbuffer(roptions)
				out.write(data)
				return self.close_outbuffer(out, roptions)
		else:
			return False


	def exists(self, url, timeout=10):
		try:
			res = urlopen(url, timeout=timeout)
			if res.code == 200:
				res.close()
				return True
		except (URLError, UrllibHTTPError) as e:
			return False

