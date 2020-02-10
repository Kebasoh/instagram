
from .. import CommandLine, CommandLineError, Subcommand, subcmd
from ..version import __version__

from .autocomp_subcommand import *


cmdline = CommandLine(prog='redcmd', description='redcmd client.',
		version=__version__)
try:
	cmdline.execute()
except CommandLineError as e:
	print(e)

