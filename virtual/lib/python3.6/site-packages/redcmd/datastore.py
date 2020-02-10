from os import mkdir, walk, remove
from os.path import exists, join as joinpath
from pickle import PicklingError, UnpicklingError
from collections import namedtuple

from redlib.api.py23 import pickledump, pickleload


from . import const


AutocompInfo = namedtuple('AutocompInfo', ['command', 'access', 'version'])


class DataStoreError(Exception):
	FILE_NOT_FOUND = 0
	
	def __init__(self, msg, reason=None):
		super(DataStoreError, self).__init__(msg)
		self.reason = reason


class DataStore:
	pickle_protocol = 2

	def __init__(self):
		self.check_dir()


	def check_dir(self, data=True, autocomp=False, script=False, create=True):
		if not exists(const.data_dir):
			self.create_dir(const.data_dir, create=create)

		if autocomp and not exists(const.autocomp_dir):
			self.create_dir(const.autocomp_dir, create=create)

		if script and not exists(const.script_dir):
			self.create_dir(const.script_dir, create=create)


	def create_dir(self, path, create=True):
		if create:
			mkdir(path)
		else:
			raise DataStoreError('%s does not exist'%path)


	def save_optiontree(self, ot, cmdname):
		self.check_dir(data=False, autocomp=True)

		with open(joinpath(const.autocomp_dir, cmdname), 'wb') as f:
			try:
				pickledump(ot, f, protocol=self.pickle_protocol, fix_imports=True)
			except PicklingError as e:
				print(e)
				raise DataStoreError('unable to save option tree')


	def load_optiontree(self, cmdname, filepath=None):
		filepath = filepath or joinpath(const.autocomp_dir, cmdname)

		if not exists(filepath):
			filepath = joinpath(const.root_autocomp_dir, cmdname)
			if not exists(filepath):
				raise DataStoreError('unable to load option tree')

		try:
			with open(filepath, 'rb') as f:
				try:
					data = pickleload(f, fix_imports=True)
				except UnpicklingError as e:
					log.error(str(e))

				#ot_version = data[0]
				#if ot_version > self.ot_version:
				#	raise DataStoreError('cannot load greater ot_version, %s > %s'%(version, self.version))
				if type(data) == list: 	# older version (1.0)
					return data[1]
				else:
					return data
		except IOError as e:
			raise DataStoreError(e)


	def remove_optiontree(self, cmdname, exc=False):
		filepath = joinpath(const.autocomp_dir, cmdname)
		return self.remove_file(filepath, exc=exc)


	def remove_all_optiontrees(self):
		for name in self.list_optiontree():
			self.remove_optiontree(name)


	def remove_file(self, filepath, exc=False):
		if exists(filepath):
			try:
				remove(filepath)
				return True
			except OSError as e:
				if exc:
					raise DataStoreError(e)
				else:
					return False
		else:
			raise DataStoreError('%s not found'%filepath, reason=DataStoreError.FILE_NOT_FOUND)


	def list_autocomp_commands(self):
		autocomp_list = []

		def add_to_list(cmd, access, dirpath):
			version = self.load_optiontree(cmd, filepath=joinpath(dirpath, cmd)).prog_version	# exc

			i = (filter(lambda i : i.command == cmd, autocomp_list) or [None])[0]
			if i is None:
				autocomp_list.append(AutocompInfo(cmd, [access], [version]))
			else:
				i.access.append(access)
				i.version.append(version)

		for _, _, files in walk(const.autocomp_dir):
			for f in files:
				add_to_list(f, 'user', const.autocomp_dir)

		for _, _, files in walk(const.root_autocomp_dir):
			for f in files:
				add_to_list(f, 'all', const.root_autocomp_dir)

		return autocomp_list

