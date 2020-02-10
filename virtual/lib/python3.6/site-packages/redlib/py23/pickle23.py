import pickle

from ..system.common import *


__all__ = ['pickledump', 'pickleload', 'pickledumps', 'pickleloads']



def pickledump(obj, file, protocol=None, fix_imports=None):
	if is_py3():
		return pickle.dump(obj, file, protocol=protocol, fix_imports=fix_imports)
	else:
		return pickle.dump(obj, file, protocol=protocol)


def pickleload(file, **kwargs):
	if is_py3():
		return pickle.load(file, **kwargs)
	else:
		return pickle.load(file)


def pickledumps(obj, protocol=None, fix_imports=None):
	if is_py3():
		return pickle.dumps(obj, protocol=protocol, fix_imports=fix_imports)
	else:
		return pickle.dumps(obj, protocol=protocol)


def pickleloads(s, **kwargs):
	if is_py3():
		return pickle.loads(s, **kwargs)
	else:
		return pickle.loads(s)