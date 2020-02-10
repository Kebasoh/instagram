# author: Amol Umrale

import re

from .tlds import tlds


__all__ = ['AbsUrl', 'RelUrl', 'UrlException', 'UrlParseException']


class UrlException(Exception):
	pass


class UrlParseException(Exception):
	pass


class AbsUrl():
	regex = re.compile(	"^([a-zA-Z][a-zA-Z0-9+-\.]+)://" +		#scheme
				"(?:(?:" +
					"(?:(" +
						"(?:[a-zA-Z0-9][a-zA-Z0-9-]{0,64}\.)*" +	#subdomain
						"(?:[a-zA-Z0-9][a-zA-Z0-9-]{0,63})" +		#hostname
						"(?:\.[a-zA-Z]{2,3}(?:\.[a-zA-Z]{2,3})?)" +	#tld
					")|(" +
						"(?:[a-zA-Z][a-zA-Z0-9-]{0,63})" +		#local hostname
					"))" +
				")|(" +
					"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" +	#ip address
				"))" +
				"[/\?]?.*$")					#rest of the url

	def __init__(self, url):
		self._url = url
		self._tld = None
		self._hostname = None
		self._subdomain = None
		self._scheme = None
		self._valid = None
		self.parse()


	def parse(self):
		match = self.regex.match(self._url)
		
		if match is None:
			self._valid = False
			return

		self._valid = True
		self._scheme = match.group(1)

		#import pdb; pdb.set_trace()

		if match.group(2) is not None:
			parts = match.group(2).split('.')
			
			if len(parts[-2]) <= 3 and parts[-2] in tlds:		#length check is a dirty fix for tlds which are also
				self._tld = parts[-2] + '.' + parts[-1]		#valid domain names
				del parts[-1]
				del parts[-1]

			else:
				self._tld = parts[-1]
				del parts[-1]

			if len(parts) == 0:
				raise UrlParseException('%s does not have a valid domain name'%self._url)

			self._hostname = parts[-1]
			del parts[-1]

			if len(parts) > 0:
				self._subdomain = '.'.join(parts)
		
		elif match.group(3) is not None:		#local hostname
			self._hostname = match.group(3)

		elif match.group(4) is not None:		#ip address
			self._hostname = match.group(4)


	def get_hostname(self):
		return self._hostname


	def get_tld(self):
		return self._tld


	def get_domain(self):
		return self._hostname + (('.' + self._tld) if self._tld is not None else '')


	def get_subdomain(self):
		return self._subdomain


	def get_scheme(self):
		return self._scheme


	def is_valid(self):
		return self._valid


	def extend(self, url):
		if not self._valid:
			raise UrlException('base url invalid')

		rel_url = RelUrl(url)

		if rel_url.protocol_relative:
			extended_url = self._scheme + '://' + rel_url.url
			return extended_url

		search_start_pos = len(self._scheme) + 3
		end_pos = None

		if rel_url.root_relative:
			end_pos = self._url.find('/', search_start_pos)
		else:
			end_pos = self._url.rfind('/', search_start_pos)
		if end_pos < 0:
			end_pos = self._url.find('?', search_start_pos)
		if end_pos < 0:
			end_pos = len(self._url)

		if rel_url.root_relative:		
			extended_url = self._url[0:end_pos] + '/' + rel_url.url
			return extended_url
		
		base_url = self._url[0:end_pos]
		base_parts = base_url.split('/')

		if rel_url.up > (len(base_parts) - 3):
			raise UrlException('invalid number of levels up')

		base_parts = base_parts[0:len(base_parts)-rel_url.up]
		extended_url = '/'.join(base_parts) + '/' + rel_url.url
		
		return extended_url


	hostname = property(get_hostname)
	tld = property(get_tld)
	domain = property(get_domain)
	subdomain = property(get_subdomain)
	scheme = property(get_scheme)
	valid = property(is_valid)


class RelUrl():
	def __init__(self, url):
		self._url = url
		self._up = 0
		self._root_rel = False
		self._proto_rel = False
		self.parse()


	def parse(self):
		if self._url.startswith('//'):
			self._proto_rel = True
			self._url = self._url[2:]
			return

		if self._url.startswith('/'):		#url relative to root
			self._root_rel = True
			self._url = self._url[1:]
			return
		
		while self._url.startswith('../'):
			self._up += 1
			self._url = self._url[3:]

		while self._url.startswith('./'):
			self._url = self._url[2:]

		if self._url.startswith('/'):		#clean any extraneous front slashes
			self._url = self._url[1:]


	def get_url(self):
		return self._url


	def get_up(self):
		return self._up

	
	def get_root_rel(self):
		return self._root_rel


	def get_proto_rel(self):
		return self._proto_rel


	url = property(get_url)
	up = property(get_up)
	root_relative = property(get_root_rel)
	protocol_relative = property(get_proto_rel)

