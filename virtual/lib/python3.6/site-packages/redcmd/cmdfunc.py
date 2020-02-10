import inspect

from .arg import Arg
from .helper import get_func


class CmdFunc:
	def __init__(self, cmd_cls, func, add=None):
		self.cmd_cls 	= cmd_cls		# command class
		self.func 	= func			# function to call
		self.add	= add			# additional functions (for common args)

		self._cmd_cls_instance = None

	
	def execute(self, args):
		if self.cmd_cls is not None:
			cmd_cls_instance = self.cmd_cls()

		if self.add is not None:
			for add_func in self.add:
				func = get_func(add_func, self.cmd_cls)
				func(*self.get_arg_list(func, args))

		return self.func(*self.get_arg_list(self.func, args))


	def get_arg_list(self, func, args):
		argspec = inspect.getargspec(func)
		arg_list = []

		if len(argspec.args) > 0 and argspec.args[0] == 'self':
			del argspec.args[0]
			
			if self._cmd_cls_instance is None:
				self._cmd_cls_instance = self.cmd_cls()
			arg_list.append(self._cmd_cls_instance)

		if argspec.defaults is not None:			# find the offset at which arguments with default values start
			defaults_offset = len(argspec.args) - len(argspec.defaults)
		else:
			defaults_offset = len(argspec.args)

		for arg_index in range(0, len(argspec.args)):
			arg_name = argspec.args[arg_index]
			arg_value = getattr(args, arg_name)
		
			if arg_index >= defaults_offset:
				arg_default = argspec.defaults[arg_index - defaults_offset]
				if arg_default.__class__ == Arg or issubclass(arg_default.__class__, Arg):
					arg_value = arg_default.convert(arg_value, name=arg_name)
			
			arg_list.append(arg_value)
			
		return arg_list

