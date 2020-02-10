import os

from redlib.api.system import is_linux, is_windows

from .bash_script_installer import BASHScriptInstaller
from .posh_script_installer import PoshScriptInstaller
from .shell_script_installer import ShellScriptInstallError


def get_shell_script_installer():
	if is_linux():
		shell = os.environ.get('SHELL', None)

		if shell is None or shell.find('bash') == -1:
			raise ShellScriptInstallError('shell not supported (currently supported: BASH)')

		return BASHScriptInstaller()

	elif is_windows():
		raise ShellScriptInstallError('platform not supported')

	else:
		raise ShellScriptInstallError('platform not supported')


def platform_supported():
	try:
		get_shell_script_installer()
	except ShellScriptInstallError:
		return False
	return True

