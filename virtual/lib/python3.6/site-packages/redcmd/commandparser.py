from argparse import ArgumentParser


class CommandParser(ArgumentParser):

	def __init__(self, *args, **kwargs):
		self.extrahelp = None
		super(CommandParser, self).__init__(*args, **kwargs)


	def format_help(self):
		'Copied from argparse. To remove third part and to swap usage and description.'

		formatter = self._get_formatter()

		# description
		formatter.add_text(self.description)

		# usage
		formatter.add_usage(self.usage, self._actions,
				self._mutually_exclusive_groups)


		# positionals, optionals and user-defined groups
		# removed

		# epilog
		formatter.add_text(self.epilog)

		# determine help from format above
		return formatter.format_help()


	def error(self, message):
		"""error(message: string)

		Prints a usage message incorporating the message to stderr and
		exits.

		If you override this in a subclass, it should not return -- it
		should either exit or raise an exception.
		"""
		#self.print_usage(_sys.stderr)

		# fix to work around change in python3.3 onwards, where subparsers were made optional
		# ref: http://bugs.python.org/issue9253
		# only if required is set to True for a subparser, it prints error if no arguments are provided
		# where a subcommand is expected
		# but, the error message has group_name as suggestion and as such only prints group name of first subparser
		# in the error message
		# so, the following condition just changes the message to a general error message
		if message.startswith("the following arguments"):
			message = "too few arguments"

		self.exit(2, ('%s: error: %s\n') % (self.prog, message))


	def set_extrahelp(self, text):
		self.extrahelp = text


	def _get_formatter(self):
		return self.formatter_class(prog=self.prog, extrahelp=self.extrahelp)

