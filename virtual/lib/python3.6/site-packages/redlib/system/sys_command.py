import os
from subprocess import check_output, CalledProcessError

from .common import is_py3


__all__ = ['sys_command', 'DEVNULL']


if is_py3():
	from subprocess import DEVNULL
else:
	DEVNULL = open(os.devnull, 'wb')


def sys_command(cmd, suppress_output=False):
	try:
		output = None

		if suppress_output:
			check_output(cmd, shell=True, stderr=DEVNULL)
		else:
			output = check_output(cmd, shell=True)

		if is_py3() and not suppress_output:
			output = output.decode(encoding='utf-8')

		return 0, output

	except CalledProcessError as e:
		return e.returncode, e.output

