
from ..decorators import subcmd
from ..subcommand import InternalSubcommand


class RedcmdInternalSubcommand(InternalSubcommand):

	@subcmd
	def redcmdinternal(self):
		'redcmd internal commands'
		pass

