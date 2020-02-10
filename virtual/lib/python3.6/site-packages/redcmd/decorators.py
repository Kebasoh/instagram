import inspect

from .command_collection import CommandCollection
from .exc import CommandCollectionError, MaincommandError, SubcommandError, CommandLineError
from .maincommand import Maincommand
from .subcommand import Subcommand
from . import const
from .move_collection import MoveCollection
from .add_args import AddArgs


__all__ = ['subcmd', 'maincmd', 'moved']


def subcmd(func=None, add=None, parent=None, add_rec=False, add_skip=False):
	def subcmd_dec(func):
		if add is not None or add_rec or add_skip:
			func.__dict__[const.add_attr] = AddArgs(add, add_rec=add_rec, add_skip=add_skip)

		if member_of_a_class(func): 
			func.__dict__[const.subcmd_attr] = True
			return func

		command_collection = CommandCollection()
		try:
			command_collection.add_subcommand(func, parent=parent)
		except (SubcommandError, CommandCollectionError) as e:
			print(e)
			raise CommandLineError('error creating command line structure')

		return func

	if func is None:
		return subcmd_dec
	else:
		return subcmd_dec(func)


def member_of_a_class(func):
	argspec = inspect.getargspec(func)

	if len(argspec.args) == 0:
		return False

	return argspec.args[0] == 'self'


def maincmd(func=None, add=None):
	def maincmd_dec(func):
		if add is not None:
			func.__dict__[const.add_attr] = AddArgs(add)

		if member_of_a_class(func):
			func.__dict__[const.maincmd_attr] = True
			return func

		command_collection = CommandCollection()
		try:
			command_collection.add_maincommand(func)
		except (MaincommandError, CommandCollectionError) as e:
			print(e)
			raise CommandLineError('error creating command line structure')

		return func


	if func is None:
		return maincmd_dec
	else:
		return maincmd_dec(func)
	

def moved(func=None, parent=None):
	def moved_dec(func):
		move_collection = MoveCollection()
		move_collection.add_move(parent, func.__name__)

		if member_of_a_class(func): 
			func.__dict__[const.moved_attr] = True
			return func

		try:
			move_collection.add_subcommand(func, parent=parent)
		except (SubcommandError, CommandCollectionError) as e:
			print(e)
			raise CommandLineError('error creating command line structure')

		return func

	if func is None:
		return moved_dec
	else:
		return moved_dec(func)


