import sys
from types import ModuleType
from pkgutil import iter_modules
from importlib import import_module
from os.path import dirname, join as joinpath


__all__ = ['make_api', 'Move']


# fix:
# recurse dirs
# duplicate name check
# issue deprecation warning on moves


class _RedMetaPathImporter(object):
	'A meta path importer to import api and its submodules. Copied from package: six.'

	def __init__(self, module_name):
		self.name = module_name
		self.known_modules = {}


	def _add_module(self, mod, *fullnames):
		for fullname in fullnames:
			self.known_modules[self.name + "." + fullname] = mod


	#def _get_module(self, fullname):


	def get_module(self, fullname):
		mod = self.known_modules.get(fullname, None)

		if mod is None:
			if fullname in self.moves.keys():
				mod = self.known_modules.get(self.moves[fullname], None)
			else:
				raise ImportError('cannot import name ' + fullname)

		mod.load()

		return mod


	def find_module(self, fullname, path=None):
		if fullname in self.known_modules:
			return self
		return None


	def __get_module(self, fullname):
		return self.get_module(fullname)


	def load_module(self, fullname):
		try:
			# in case of a reload
			return sys.modules[fullname]
		except KeyError:
			pass
		mod = self.__get_module(fullname)
		mod.__loader__ = self

		sys.modules[fullname] = mod
		return mod


	def is_package(self, fullname):
		'''Return true, if the named module is a package.

		We need this method to get correct spec objects with
		Python 3.4 (see PEP451)'''

		return hasattr(self.__get_module(fullname), "__path__")


	def get_code(self, fullname):
		'''Return None
		Required, if is_package is implemented'''

		self.__get_module(fullname)  # eventually raises ImportError
		return None


	get_source = get_code  # same as get_code


class GenModule(ModuleType):
	
	def __init__(self, name, dirpath, package, moves):
		super(GenModule, self).__init__(name)

		self._members	= []
		self._name	= name
		self._dirpath	= dirpath
		self._package	= package
		self._moves 	= moves

		self._loaded	= False


	def load(self):
		if self._loaded:
			return

		for _, modname, is_pkg in iter_modules(path=[joinpath(self._dirpath, self._name)]):
			if not is_pkg:
				self.add_module(self._package + '.' + self._name + '.' + modname)

		self._loaded = True


	def add_module(self, module):
		mod = import_module(module)
		all = getattr(mod, '__all__', None)

		if all is not None:
			for member in all:
				# add member to this module
				setattr(self, member, getattr(mod, member, None))
				self._members.append(member)

				# check moves
				impname = self._name + '.' + member
				for m in self._moves:
					if m.new == impname:
						setattr(self, m.old_member_name(), getattr(mod, member, None))


	def __dir__(self):
		return self._members



class Move:
	def __init__(self, old, new):
		self.old = old
		self.new = new


	def old_member_name(self):
		return self.old[self.old.rfind('.') + 1:]

	def new_member_name(self):
		return self.new[self.new.rfind('.') + 1:]


class APIPackage:
	def __init__(self, module_name, filepath, exclude, moves):
		self.module_name 	= module_name
		self.parent_package 	= module_name[0: module_name.rfind('.')]
		self.filepath		= filepath
		self.exclude		= exclude
		self.moves		= moves

		self.exclude.append(module_name[module_name.rfind('.') + 1:])
		self.importer = _RedMetaPathImporter(module_name)


	def add_modules(self):
		non_pkg = []
		dirpath = dirname(self.filepath)

		for _, name, is_pkg in iter_modules([dirpath]):
			if name not in self.exclude:
				pkg_moves = []
				if not is_pkg:
					non_pkg.append(name)
					continue

				for move in self.moves:
					if move.old.startswith(name):
						pkg_moves.append(move)

				self.importer._add_module(GenModule(name, dirpath, self.parent_package, pkg_moves), name)

		if len(non_pkg) > 0:
			api_module = import_module(self.module_name)
			non_pkg_moves = [m for m in self.moves if m.new.find('.') == -1]

			for modname in non_pkg:
				mod = import_module(self.parent_package + '.' + modname)
				all = getattr(mod, '__all__', None)

				if all is not None:
					for member in all:
						setattr(api_module, member, getattr(mod, member, None))

					for m in non_pkg_moves:
						if m.new == member:
							setattr(api_module, m.old, getattr(mod, member, None))


def make_api(module_name, api_mod_filepath, exclude=[], moves=[]):
	api_package = APIPackage(module_name, api_mod_filepath, exclude, moves)
	api_package.add_modules()

	if sys.meta_path:
		for i, importer in enumerate(sys.meta_path):
			if (type(importer).__name__ == "_RedMetaPathImporter" and
				importer.name == module_name):
				del sys.meta_path[i]
				break
			del i, importer
	sys.meta_path.append(api_package.importer)

