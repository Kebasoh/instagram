
from zope.interface import implementer

from .shell_script_installer import IShellScriptInstaller


@implementer(IShellScriptInstaller)
class PoshScriptInstaller:
	pass

