
from six.moves import input
from redlib.api.prnt import ColumnPrinter, Column

from ..decorators import subcmd
from ..exc import CommandError
from ..autocomp.generator import Generator, GenError
from ..autocomp.installer import Installer, InstallError
from .redcmd_internal_subcommand import RedcmdInternalSubcommand
from ..datastore import DataStore, DataStoreError
from .. import const


class AutocompSubcommand(RedcmdInternalSubcommand):

	@subcmd
	def autocomp(self):
		'Do various autocomplete actions.'
		pass


class AutocompSubSubcommands(AutocompSubcommand):

	@subcmd
	def setup(self, command_name):
		'''Install autocomplete for a command.
		command_name: command name'''

		msg_template = '{0} will now be executed for it to be setup for autocomplete.\n' + \
				'Any actions, side effects, changes that take place as a result of executing {0} will take place.\n' + \
				'Note: Autocomplete setup will only work if the {0} uses redcmd for argument parsing.\n' + \
				'Are you sure you want to continue?'

		message = msg_template.format(command_name)
		
		if command_name == const.internal_dummy_cmdname or self.confirm(message):
			self.exc_installer_method(Installer.setup_cmd_by_exe, command_name)


	@subcmd
	def remove(self, command_name):
		'''Uninstall autocomplete for a command.
		command_name: command name'''

		self.exc_installer_method(Installer.remove_cmd, command_name)


	def confirm(self, message):
		choice = input(message + ' [y/n]: ')
		return choice == 'y'


	@subcmd
	def remove_all(self, skip_confirm=False):
		'''Remove autocomplete for all commands.

		skip_confirm: Skip confirmation before removing all commands setup for autocomplete.'''

		if skip_confirm or self.confirm('Are you sure you want to remove all commands setup for autocomplete?'):
			self.exc_installer_method(Installer.remove_all)


	@subcmd
	def setup_base(self):
		'Install common base scripts for autocomplete.'
		
		self.exc_installer_method(Installer.setup_base)


	@subcmd
	def remove_base(self, skip_confirm=False):
		'''Uninstall common base scripts for autocomplete.
		Please note that all the commands setup for autocomplete will also be unregistered.

		skip_confirm: Skip confirmation before removing all commands setup for autocomplete.'''

		if skip_confirm or self.confirm('Are you sure you want to remove the base scripts setup for autocomplete?'):
			self.exc_installer_method(Installer.remove_base)


	def exc_installer_method(self, method, *args, **kwargs):
		installer = Installer()
		try:
			method(installer, *args, **kwargs)
		except InstallError as e:
			print(e)
			raise CommandError()


	@subcmd
	def gen(self, command_line, comp_word):
		'''Generate autocomplete options for a command.
		command_line: 	command line so far
		comp_word: 	word to be auto-completed'''

		try:
			g = Generator(command_line, comp_word.strip())
			g.load()
			options = g.gen()

			for option in options:
				print(option)
		except GenError as e:
			raise CommandError()


	@subcmd
	def list(self):
		'''List the commands registered for autocomplete.
		Key:
		[user]: installed for current user
		[all]: 	installed for everyone
		[user, all]: installed for current user as well as everyone'''

		try:
			dstore = DataStore()
			autocomp_list = dstore.list_autocomp_commands()
			printer = ColumnPrinter(cols=[Column(width=20), Column(width=10), Column(width=10)])

			for i in autocomp_list:
				c = len(i.access)
				printer.printf(i.command, i.access[0], i.version[0] or 'n/a')
				if c > 1:
					printer.printf('', i.access[1], i.version[1] or 'n/a')

		except DataStoreError as e:
			print(e)
			raise CommandError()

