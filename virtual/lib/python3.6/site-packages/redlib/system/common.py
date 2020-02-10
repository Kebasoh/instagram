import sys
import platform
from os.path import expanduser, join as joinpath, exists


__all__ = ['is_linux', 'is_windows', 'is_py3', 'is_py2', 'get_pictures_dir']


def is_linux():
	return platform.system() == 'Linux'


def is_windows():
	return platform.system() == 'Windows'


def is_py3():
	version = platform.python_version()
	return version[0] == '3'


def is_py2():
	version = platform.python_version()
	return version[0] == '2'


def get_pictures_dir():
	path = joinpath(expanduser('~'), 'Pictures')
	if not exists(path):
		mkdir(path)
	return path

