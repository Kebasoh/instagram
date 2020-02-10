import inspect
import types
from argparse import _SubParsersAction, ArgumentParser, _VersionAction, _HelpAction
from copy import copy

from redlib.api.misc import Singleton, extract_help

from .command_help_formatter import CommandHelpFormatter
from .commandparser import CommandParser
from .arg import Arg, make_filter
from .cmdfunc import CmdFunc
from .maincommand import Maincommand
from .subcommand import Subcommand, InternalSubcommand
from .exc import CommandError, CommandCollectionError
from . import const
from .autocomp.option_tree import OptionTree, OptionTreeError
from .autocomp.node import Node
from .autocomp.filter import ListFilter
from .datastore import DataStore
from .helper import get_func
from .add_args import AddArgs


# Notes
# -----
#
# -1-
# ArgumentParser::add_subparsers() assigns an instance of _ArgumentGroup to its member _subparsers,
# then, it adds an instance of _SubParsersAction to _subparsers using _ArgumentGroup::_add_action()
# and return that instance of _SubParsersAction.
# In this class, we just access that instance of _SubParsersAction using _subparsers._group_actions[0] as there is only one instance ever added. (Subsequent calls to add_subparsers() would raise an error).
#
# -2-
# General Logic:
# Main command: command line execution without any subcommands, if it is present, subcommands won't be added
# Subcommands: if one or more are added, main command won't be added
#
# Top level parser is an instance of CommandParser(ArgumentParser)
# If main command is to be added, we add it to top level parser.
# If a subcommand is to be added,
#   we call add_subparsers() on the parser (top level parser if no parent parser is mentioned) (_CommandCollection::add_subcommand)
#   then, we add a parser for the subcommand to the returned _SubParsersAction instance using add_parser() [see note 1]
#   (_CommandCollection::add_subcommand_to_spa)
#   finally, we add arguments to the parser using the provided function (_CommandCollection::add_args_to_parser)
#
# -3-
# _CommandCollection is an inner class. Not meant to be used directly.
# CommandCollection is the singleton that wraps a single instance of _CommandCollection.


added_arg = lambda x : x.__class__ != _HelpAction and x.__class__ != _VersionAction


class _CommandCollection(object):

	def __init__(self):
		self._cmdparser 		= CommandParser(formatter_class=CommandHelpFormatter)
		self._internal_cmdparser 	= None
		self._optiontree 		= None
		self._to_hyphen			= False
		self._add_arg_parsers		= {}
		self._subcmd_attr		= const.subcmd_attr


	def set_details(self, prog=None, description=None, version=None, _to_hyphen=False):
		self._cmdparser.prog 		= prog
		self._cmdparser.description 	= description
		self._to_hyphen 		= _to_hyphen
		self._version			= version

		if version is not None:
			self._cmdparser.add_argument('-v', '--version', action='version', version=version, help='print program version')


	def get_prog(self):
		return self._cmdparser.prog


	def cmdparser_populated(self):
		return self._cmdparser._subparsers is not None or any([added_arg(a) for a in self._cmdparser._actions])


	def make_option_tree(self, command_name=None, subcmd_cls=None, maincmd_cls=None, save=True):
		command_name = self._cmdparser.prog if command_name is None else command_name

		if command_name is None:
			raise CommandCollectionError('cannot create option tree without a command name')

		self._optiontree = OptionTree(self._version)
		self._optiontree.add_node(Node(command_name))

		# if cmdparser is aleady populated, add from it
		if self.cmdparser_populated():
			self.make_ot_from_cmdparser(self._cmdparser)
		else:
			self.add_commands(subcmd_cls=subcmd_cls, maincmd_cls=maincmd_cls)

		if not save:
			return self._optiontree

		dstore = DataStore()
		dstore.save_optiontree(self._optiontree, command_name)


	def make_ot_from_cmdparser(self, parser):
		if parser._subparsers is not None:
			for subcmd, subparser in parser._subparsers._group_actions[0]._name_parser_map.items():
				self._optiontree.add_node(Node(subcmd, subcmd=True))
				if subparser._subparsers is None:
					for action in subparser._actions:
						hidden = getattr(action, const.action_hidden_attr, False)
						if action.dest == 'help' or hidden:
							continue
						names = action.option_strings if len(action.option_strings) > 0 else [action.dest]
						filter = getattr(action, const.action_filter_attr, None)
						self.add_to_optiontree(names, action.default, action.choices, filter)
				else:
					self.make_ot_from_cmdparser(subparser)
				self._optiontree.pop()

		else:
			for action in parser._actions:
				hidden = getattr(action, const.action_hidden_attr, False)
				if added_arg(action) and not hidden:
					names = action.option_strings if len(action.option_strings) > 0 else [action.dest]
					filter = getattr(action, const.action_filter_attr, None)
					self.add_to_optiontree(names, action.default, action.choices, filter)



	
	def add_commands(self, maincmd_cls=None, subcmd_cls=None):			# to be called from class CommandLine to add
		if self.cmdparser_populated():						# subclass members of Maincommand and Subcommand
			return

		maincmd_cls = Maincommand if maincmd_cls is None else maincmd_cls	
		subcmd_cls = Subcommand if subcmd_cls is None else subcmd_cls

		self.add_maincommand_class(maincmd_cls)
		self.add_subcommand_classes(subcmd_cls, self._cmdparser)


	def add_internal_commands(self):
		self._internal_cmdparser = CommandParser(formatter_class=CommandHelpFormatter)
		self.add_subcommand_classes(InternalSubcommand, self._internal_cmdparser)


	def add_subcommand_classes(self, cls, parser, parent_add_args=None, parent_subcmds=[]):
		subcmd_added = False
		if getattr(cls, '__subclasses__', None) is not None:
			for subcmd_cls in cls.__subclasses__():
				#subcmd_added |= self.add_subcommand_group(subcmd_cls, parser, parent_add_args=parent_add_args)
				#return subcmd_added
				#def add_subcommand_group(self, subcmd_cls, parser, parent_add_args=None):
				#subcmd_added = False
				for member_name, member_val in inspect.getmembers(subcmd_cls, predicate=\
				lambda x : inspect.ismethod(x) or inspect.isfunction(x)):

					if True or inspect.ismethod(member_val):
						func = member_val
						if getattr(func, self._subcmd_attr, None) is not None:
							if func.__name__ in parent_subcmds:
								continue	

							if self._optiontree is not None:
								self._optiontree.add_node(Node(self.utoh(func.__name__), subcmd=True))

							add_args = getattr(func, const.add_attr, None)
							if add_args is None:
								if parent_add_args is not None:
									add_args = copy(parent_add_args)
									add_args.add_skip = False
									func.__dict__[const.add_attr] = add_args
							else:
								if parent_add_args is not None:
									add_args.extend(parent_add_args.args)

							subcmd_parser = self.add_subcommand(
										func,
										cmd_cls=subcmd_cls,
										parent=parser,
										group_name=subcmd_cls.__name__.lower())
							subcmd_added = True

							self.add_subcommand_classes(subcmd_cls, subcmd_parser, parent_add_args=add_args,
									parent_subcmds=parent_subcmds + [func.__name__])

							if self._optiontree is not None:
								self._optiontree.pop()

		return subcmd_added
		

	# Adds a subcommand to a parent subcommand.
	#
	# func: 	function to be added as subcommand target
	# cmd_cls:	Subcommand subclass of which func is a member, just passed along to another method
	# parent:	parent subcommand
	# group_name: 	dest name for adding subparsers memeber to parent
	# 
	# if parent=None, add it to top level parser
	#
	# if parent type is string,
	#   it has to be of the form 'subcommand subcommand ...'
	#   e.g. if it is 'math add', then,
	#   this subcommand will be added as a child to 'add' subcommand which in turn is a child of 'math' subcommand
	#
	# if cmd_cls=None, it means subcommand is being added using decorator only (not subclassing of Subcommand)
	# if group_name=None, cmd_cls is also None, that is, decorator only addition
	#   so, we use parent subcommand name + 'subcommand' as group_name
	#
	def add_subcommand(self, func, cmd_cls=None, parent=None, group_name=None):
		if parent is None:
			parent = self._cmdparser
			group_name = const.subcmd_dest_suffix

		elif issubclass(parent.__class__, CommandParser):
			pass

		elif type(parent) == str:
			parts = parent.split()
			parent = self._cmdparser
			for part in parts:
				if parent._subparsers is None:
					raise CommandCollectionError('trying to add subcommands to a non-existant subcommand')

				parent = parent._subparsers._group_actions[0]._name_parser_map.get(part, None)

				if parent is None:
					raise CommandCollectionError('no such subcommand: %s'%' '.join(parts))
			group_name = parts[-1] + const.subcmd_dest_suffix
			
		subparsers = parent._subparsers
		spa = None
		
		if subparsers is None:
			spa = parent.add_subparsers(dest=group_name)
			spa.required = True

			if parent._defaults.get('cmd_func', None) is not None:	# if parent has a default, subcommands will use that
				del parent._defaults['cmd_func']

		else:
			spa = subparsers._group_actions[0]	

		#print 'spa class: ', spa.__class__
		#if spa.__class__ != _SubParsersAction: import pdb; pdb.set_trace()
		return self.add_subcommand_to_spa(func, cmd_cls, spa)


	def add_subcommand_to_spa(self, func, cmd_cls, spa):		# add subcommand parser to _SubParsersAction instance
		assert spa.__class__ == _SubParsersAction

		subcmd_name = self.utoh(func.__name__)

		if subcmd_name in spa._name_parser_map:
			raise CommandCollectionError('duplicate subcommand: %s'%func.__name__)

		add_arg_parsers = self.get_add_parsers(func, cmd_cls)

		help = extract_help(func)

		parser = spa.add_parser(subcmd_name,			# add parser for subcommand
				prog=self._cmdparser.prog + ' ' + func.__name__,
				formatter_class=self._cmdparser.formatter_class,
				description=help.get('short', None),
				parents=add_arg_parsers)

		setattr(parser, const.parser_func_attr, func)		# for creating option tree after arg parser has been created
		self.add_args_to_parser(func, cmd_cls, parser)

		return parser


	def get_add_parsers(self, func, cmd_cls, main=False):
		add_args = getattr(func, const.add_attr, None)
		if add_args is None or add_args.add_skip:
			return []

		add_arg_funcs = add_args.args
		add_arg_parsers = []
		usn = ['h']
		if main:
			usn.append('v')

		if add_arg_funcs is not None:
			for a in add_arg_funcs:
				func = get_func(a, cmd_cls)

				if func is None:
					raise CommandCollectionError('invalid type for additional param function, must be function / str')

				fname = func.__name__

				if fname in self._add_arg_parsers.keys():
					arg_parser = self._add_arg_parsers[fname]
					add_arg_parsers.append(arg_parser)
				else:
					arg_parser = ArgumentParser(add_help=False)
					self.add_args_to_parser(func, cmd_cls, arg_parser, common=True, usn=usn)

					add_arg_parsers.append(arg_parser)
					self._add_arg_parsers[fname] = arg_parser

				if self._optiontree is not None:
					self._optiontree.add_common(arg_parser.common_args)	

		return add_arg_parsers



	def add_args_to_parser(self, func, cmd_cls, parser, common=False, usn=['h']):	# extract function argument information
		help = extract_help(func)						# and add them to parser,
											# extract help and add it to parser
		if common:
			parser.common_args = Node('')

		argspec = inspect.getargspec(func)
		if cmd_cls is not None:
			del argspec.args[0]				# remove arg: self in case of a class method

		if argspec.defaults is not None:			# find the offset at which arguments with default values start
			defaults_offset = len(argspec.args) - len(argspec.defaults)
		else:
			defaults_offset = len(argspec.args)

		used_short_names = list(usn)					# store used short names for arguments so as not to repeat them

		for arg in argspec.args:
			arg_index = argspec.args.index(arg)
			default = names = choices = nargs = action = filter = None
			hidden = False

			if arg_index >= defaults_offset:		# argument has a default value
				arg_default = argspec.defaults[arg_index - defaults_offset]

				def get_opt_arg_names(arg, short=None):
					short = short or self.shorten_arg_name(arg, used_short_names)
					used_short_names.append(short)

					names = ['-' + short, '--' + arg]
					return names

				if arg_default.__class__ == Arg or issubclass(arg_default.__class__, Arg):
					filter 	= make_filter(arg_default)
					choices = arg_default.choices
					default = arg_default.default
					nargs 	= arg_default.nargs
					hidden	= arg_default.hidden

					if arg_default.pos:
						if default is not None:
							nargs = '?'
						names = [arg]
					else:
						names = get_opt_arg_names(arg, arg_default.short)

					#if default is None or arg_default.pos:
					#	names = [arg]		# positional argument
				else:
					names = get_opt_arg_names(arg)
					default = arg_default

				if type(default) == bool:
					if default:
						action = 'store_false'
					else:
						action = 'store_true'
					default = None

			else:
				names = [arg]				# positional argument

			if action is None:
				kwargs = {
					'default'	: default,
					'choices'	: choices,
					'help'		: help.get(arg, None)
				}
				if nargs is not None:
					kwargs['nargs'] = nargs
			else:
				kwargs = {
					'action'	: action,
					'help'		: help.get(arg, None)
				}

			if len(names) == 1:
				kwargs['metavar'] = self.utoh(names[0])
			else:
				names = [self.utoh(n) for n in names]

			action = parser.add_argument(*names, **kwargs)
			setattr(action, const.action_filter_attr, filter)
			setattr(action, const.action_hidden_attr, hidden)

			if not hidden:
				if not common:
					self.add_to_optiontree(names, default, choices, filter)
				else:
					parser.common_args.add_child(self.make_ot_node(names, default, choices, filter))
		# end: for loop
			
		longhelp = help.get('long', None)	

		if longhelp is not None and len(longhelp) > 0:
			parser.set_extrahelp(longhelp)

		if not common:
			add_args = getattr(func, const.add_attr, None)
			add_arg_funcs = add_args.args if add_args is not None else None
			parser.set_defaults(cmd_func=CmdFunc(cmd_cls, func, add=add_arg_funcs))	# set class and function to be called for execution


	def add_to_optiontree(self, names, default, choices, filter):
		if self._optiontree is None:
			return

		self._optiontree.add_node(self.make_ot_node(names, default, choices, filter))
		self._optiontree.pop()


	def make_ot_node(self, names, default, choices, filter):
		name = self.utoh(names[0])
		alias = self.utoh(names[1]) if len(names) > 1 else None

		filters = []
		if filter is not None:
			filters.append(filter)

		if choices is not None:
			filters.append(ListFilter([str(c) for c in choices]))

		elif default is not None and default != '==SUPRESS==':
			filters.append(ListFilter([str(default)]))

		return Node(name, alias=alias, filters=filters)


	def shorten_arg_name(self, arg_name, used):
		char_count = 0
		short = None

		while short in used or short is None:
			char_count += 1
			short = arg_name[0 : char_count]

		return short


	def utoh(self, name):
		if self._to_hyphen:
			return name.replace('_', '-')
		else:
			return name
			

	def add_maincommand_class(self, cls):				# find a subclass of Maincommand, find any method decorated by @maincmd
		if getattr(cls, '__subclasses__', None) is None:	# and add it as main command
			return

		subclasses = cls.__subclasses__()

		if len(subclasses) > 1:
			raise MainCommandError('only one class should derive from MainCommand')
		elif len(subclasses) == 0:
			return		# it's ok, main command may have been added via decorator or not added at all

		maincmd_cls = subclasses[0]
		maincmd_added = False

		for member_name, member_val in inspect.getmembers(maincmd_cls, predicate=\
			lambda x : inspect.ismethod(x) or inspect.isfunction(x)):

			func = member_val
			if getattr(func, const.maincmd_attr, None) is not None:
				self.add_maincommand(func, cmd_cls=maincmd_cls)
				maincmd_added = True

		return maincmd_added


	def add_maincommand(self, func, cmd_cls=None):		# add func as main command, if cmd_cls = None, func is a non-member
		if self._cmdparser._subparsers is not None:	# function, else, it is a member of a Maincommand subclass
			raise CommandCollectionError('cannot add main command when subcommands are also added')

		if self._cmdparser.get_default('cmd_func') is not None:
			raise CommandCollectionError('main command already added')

		add_arg_parsers = self.get_add_parsers(func, cmd_cls, main=True)
		for p in add_arg_parsers:
			self._cmdparser._add_container_actions(p)

		self.add_args_to_parser(func, cmd_cls, self._cmdparser, usn=['h', 'v'])


	def execute(self, args, namespace, internal=False):	# to be called for execution of command line
		#args = None

		if not internal:
			args = self._cmdparser.parse_args(args, namespace)
		else:
			args = self._internal_cmdparser.parse_args(args, namespace)

		cmd_func = getattr(args, 'cmd_func', None)
		if cmd_func is None:
			raise CommandCollectionError('target function for command not found')

		try:
			return cmd_func.execute(args)
		except CommandError as e:
			raise CommandCollectionError(e)


	prog = property(get_prog)


class CommandCollection(Singleton):
	classtype = _CommandCollection

