
from redlib.api.py23 import enum_names, enum_attr

from .autocomp.filter import PathFilter
from .exc import CommandError


__all__ = ['Arg', 'PathArg', 'make_filter', 'EnumArg', 'IntArg', 'FloatArg', 'NumArg']


class Arg(object):
	def __init__(self, pos=True, opt=False, choices=None, default=None, nargs=None, short=None, hidden=False):
		if opt:
			pos = False

		self.pos 	= pos
		self.opt 	= opt
		self.choices 	= choices
		self.default 	= default
		self.nargs 	= nargs
		self.short	= short
		self.hidden	= hidden


	def convert(self, value, name='value'):
		return value


class PathArg(Arg):
	def __init__(self, pos=True, opt=False, short=None, hidden=False, ext_list=[], regex_list=[], glob_list=[]):
		super(PathArg, self).__init__(pos=pos, opt=opt, short=short, hidden=hidden)

		self.ext_list	= ext_list
		self.regex_list	= regex_list
		self.glob_list	= glob_list


class EnumArg(Arg):
	def __init__(self, pos=True, opt=False, short=None, hidden=False, choices=None, default=None, nargs=None):
		super(EnumArg, self).__init__(pos=pos, opt=opt, short=short, hidden=hidden)

		self.enum 	= choices
		self.choices 	= enum_names(self.enum)
		self.default 	= default.name if default is not None else None


	def convert(self, value, name='value'):
		return enum_attr(self.enum, value)


class NumArg(Arg):
	def __init__(self, pos=True, opt=False, default=None, short=None, hidden=False, min=None, max=None, ntype=None):
		super(NumArg, self).__init__(pos=pos, opt=opt, default=default, short=short, hidden=hidden)
	
		self.min 	= min
		self.max 	= max
		self.ntype 	= ntype


	def convert(self, value, name='value'):
		result = None
		if value is not None:
			try:
				result = self.cast(value)
				if self.min is not None and result < self.min:
					print('%s should be greater than or equal to %d'%(name, self.min))
					raise CommandError()
				if self.max is not None and result > self.max:
					print('%s should be less than or equal to %d'%(name, self.max))
					raise CommandError()

			except ValueError as e:
				print("'%s' is not a valid %s"%(value, self.ntype.__name__))
				raise CommandError()

		return result


	def cast(self, value):
		return self.ntype(value)


class IntArg(NumArg):
	def __init__(self, pos=True, opt=False, default=None, short=None, hidden=False, min=None, max=None):
		super(IntArg, self).__init__(pos=pos, opt=opt, default=default, ntype=int, min=min, max=max, short=short, hidden=hidden)


class FloatArg(NumArg):
	def __init__(self, pos=True, opt=False, default=None, short=None, hidden=False, min=None, max=None):
		super(FloatArg, self).__init__(pos=pos, opt=opt, default=default, ntype=float, min=min, max=max, short=short, hidden=hidden)


def make_filter(arg_obj):
	filter_obj = None

	if arg_obj.__class__ == Arg:
		pass

	elif arg_obj.__class__ == PathArg:
		filter_obj = PathFilter(path_arg_obj=arg_obj)

	return filter_obj

