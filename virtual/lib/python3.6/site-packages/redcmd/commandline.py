import sys

from redlib.api.misc import cmp_version

from . import const
from .client.autocomp_subcommand import *
from .command_collection import CommandCollection
from .autocomp.installer import Installer, InstallError
from .exc import CommandCollectionError, CommandLineError
from .client.redcmd_internal_subcommand import RedcmdInternalSubcommand
from .move_collection import MoveCollection
from .autocomp.shell_script_installer_factory import platform_supported


__all__ = ['CommandLine']


class CommandLine(object):
	'Command line handler.'

	def __init__(self, prog=const.prog, description=const.description, version=const.version, 
			default_subcommand=None, namespace=None, _to_hyphen=False, moves=False,
			update_autocomplete=True, update_autocomplete_cb=None):

		self._command_collection = CommandCollection()
		self._command_collection.set_details(prog=prog, description=description, version=version, _to_hyphen=_to_hyphen)

		self._default_subcommand = default_subcommand
		self._namespace = namespace
		self._prog = prog
		self._version = version

		self._moves = moves

		self._update_autocomplete = update_autocomplete
		self._update_autocomplete_cb = update_autocomplete_cb

	
	def execute(self, args=None, namespace=None):
		if len(sys.argv) > 1 and sys.argv[1] == const.internal_subcmd:
			self.execute_internal(args, namespace)
			return

		try:
			subcmd_cls = None
			if sys.argv[0].endswith('redcmd'):
				subcmd_cls = RedcmdInternalSubcommand

			self._command_collection.add_commands(subcmd_cls=subcmd_cls)
		except CommandCollectionError as e:
			raise CommandLineError('error creating command line structure')

		if self._default_subcommand is not None and len(sys.argv) == 1 :
			sys.argv.extend(self._default_subcommand.split())

		if namespace is None:
			namespace = self._namespace

		try:
			if self._moves:
				move_collection = MoveCollection()
				move_collection.set_details(prog=self._prog)
				move_collection.add_commands()
				if move_collection.is_moved(args):
					args = move_collection.move(args)

			if self._update_autocomplete and platform_supported():
				autocomp_version = self.get_autocomp_version()
				if autocomp_version is None or cmp_version(autocomp_version, self._version) < 0:
					if sys.argv[0].endswith('redcmd'):
						self.remove_base(exc=False)
						print('\n' + 'Installing new base scripts...')

					self.setup_autocomplete(exc=False)

					if self._update_autocomplete_cb is not None:
						self._update_autocomplete_cb()

			self._command_collection.execute(args, namespace)
		except CommandCollectionError as e:
			raise CommandLineError(e)


	def get_autocomp_version(self):
		ds = DataStore()

		try:
			ot = ds.load_optiontree(self._prog)
			return ot.prog_version
		except DataStoreError:
			return None

	def execute_internal(self, args=None, namespace=None):
		try:
			self._command_collection.add_internal_commands()
		except CommandCollectionError as e:
			raise CommandLineError('error creating internal command line structure')

		try:
			self._command_collection.execute(args, namespace, internal=True)
		except CommandCollectionError as e:
			raise CommandLineError(e)


	def set_default_subcommand(self, name):
		self._default_subcommand = name


	def setup_autocomplete(self, command_name=None, exc=True):
		command_name = command_name if command_name is not None else self._prog

		try:
			installer = Installer()
			installer.setup_cmd(command_name)
		except InstallError as e:
			if exc:
				raise CommandLineError(str(e))


	def remove_autocomplete(self, command_name=None):
		installer = Installer()

		if command_name is None:
			command_name = self._prog

		try:
			installer.remove_cmd(command_name)
		except InstallError as e:
			print(e)


	def remove_base(self, exc=True):
		try:
			installer = Installer()
			installer.remove_base()
		except InstallError as e:
			if exc:
				print(e)	
