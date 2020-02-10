from os.path import exists, join as joinpath
from os import mkdir, makedirs, remove, stat
import hashlib
from glob import glob
from datetime import datetime, timedelta
from time import time

from ..misc.singleton import Singleton
from redlib.api.py23 import pickledump, pickleload
from redlib.api.misc import str_time_period_to_seconds


__all__ = ['Cache', 'CacheError']


class CacheError(Exception):
	pass


class CacheItem:
	def __init__(self, timeout, pickle=False):
		self.timeout 		= timeout
		self.pickle 		= pickle
		self.create_time 	= int(time())


class _Cache():
	db_filename 	= 'db'
	db_version 	= '1.0'
	pickle_protocol = 2

	def __init__(self, cache_dir):
		self._cache_dir = cache_dir
		self._db_filepath = joinpath(self._cache_dir, self.db_filename)

		self._db = {}
		self.init()


	def init(self):
		if not exists(self._cache_dir):
			makedirs(self._cache_dir)

		if exists(self._db_filepath):
			self.load_db()
			self.clear_expired_items()


	def load_db(self):
		with open(self._db_filepath, 'rb') as f:
			self._db = pickleload(f, fix_imports=True)[1]


	def clear_expired_items(self):
		del_list = []
		for id, cache_item in self._db.items():
			if cache_item.timeout is not None and cache_item.timeout <= int(time()):
				del_list.append(id)

		for id in del_list:
			self.delete(id)
			self._db.pop(id)

		self.save_db()
		

	def delete(self, name, hash=False):
		id = name if not hash else self.md5hash(name)
		filepath = joinpath(self._cache_dir, id)
		try:
			remove(filepath)
		except OSError as e:
			pass


	def save_db(self):
		with open(self._db_filepath, 'wb') as f:
			pickledump([self.db_version, self._db], f)
			

	def add(self, name, data, timeout, pickle=False, hash=False, updt_timeout=True):
		id = name if not hash else self.md5hash(name)

		with open(joinpath(self._cache_dir, id), 'wb') as f:
			if not pickle:
				f.write(data)
			else:
				pickledump(data, f, protocol=self.pickle_protocol, fix_imports=True)

		if not updt_timeout and self._db.get(id, None) is not None:
			pass
		else:
			self._db[id] = CacheItem(self.calc_timeout(timeout), pickle=pickle)

		self.save_db()


	def calc_timeout(self, timeout_str):
		if timeout_str == 'never':
			return None

		try:
			seconds = str_time_period_to_seconds(timeout_str)
		except TimePeriodError as e:
			raise Cache2Error()

		return int(time()) + seconds


	def md5hash(self, input):
		md5h = hashlib.md5()
		md5h.update(input.encode('utf-8'))
		return md5h.hexdigest()


	def get(self, name, hash=False):
		id, cache_item = self.get_cache_item(name, hash=hash)
		if cache_item is None:
			return None

		path = joinpath(self._cache_dir, id)
		if exists(path):
			with open(path, 'rb') as f:
				if not cache_item.pickle:
					return f.read()
				else:
					try:
						return pickleload(f, fix_imports=True)
					except EOFError:
						return None


	def get_cache_item(self, name, hash=False):
		id = name if not hash else self.md5hash(name)
		return id, self._db.get(id, None)


	def info(self, name, hash=False):
		info = {}
		id, cache_item = self.get_cache_item(name, hash=hash)
		if cache_item is not None:
			path = joinpath(self._cache_dir, id)
			if exists(path):
				st = stat(path)

				info['size'] 	= st.st_size
				info['mtime'] 	= st.st_mtime
				info['crtime'] 	= cache_item.create_time

		return info
		

	def clear_cache(self):
		for filepath in glob(joinpath(self._cache_dir, '*')):
			remove(filepath)
		open(joinpath(self._cache_dir, (datetime.today() + timedelta(days=1)).strftime('expiry%d%b%Y')), 'w').close()

		self._db = {}


class Cache(Singleton):
	classtype = _Cache

