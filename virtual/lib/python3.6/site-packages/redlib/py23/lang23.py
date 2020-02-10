
from ..system.common import *


__all__ = ['cmp', 'b', 's', 'enum_names', 'enum_values', 'enum_attr']


if is_py3():
	cmp = lambda a, b: (a > b) - (a < b)
else:
	cmp = cmp


def b(input, enc='utf-8'):
	if is_py3():
		return bytes(input, enc)
	else:
		return bytes(input)


def s(input, enc='utf-8'):
	if is_py3():
		return input.decode('utf-8')
	else:
		return input


enum_names 		= lambda e : [m.name for m in e]
enum_values 		= lambda e : [m.value for m in e]
enum_attr		= lambda e, a : getattr(e, a, None) if a is not None else None

