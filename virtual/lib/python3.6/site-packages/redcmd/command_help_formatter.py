from argparse import HelpFormatter, _SubParsersAction, SUPPRESS, Action
import os
import textwrap

from redlib.api.misc import trim_docstring
from redlib.api.system import get_terminal_size

from . import const


class CommandHelpFormatter(HelpFormatter):

	def __init__(self, *args, **kwargs):
		if 'extrahelp' in kwargs.keys():
			self._extrahelp = kwargs['extrahelp']
			del kwargs['extrahelp']

		super(CommandHelpFormatter, self).__init__(*args, **kwargs)


	def format_help(self):
		help = self._root_section.format_help()
		if help:
		    help = self._long_break_matcher.sub('\n\n', help)
		    help = help.strip('\n') + '\n'
		    pass
		return help

	
	def _format_usage(self, usage, actions, groups, prefix):
		help = ''
		usage = 'usage: ' + self._prog + ' '

		optionals = []
		positionals = []
		col1 = 0

		for action in actions:
			if action.option_strings:
				optionals.append(action)
				names_len = len(', '.join(action.option_strings)) + 2
				col1 = names_len if names_len > col1 else col1
			else:
				positionals.append(action)
				names_len = 0
				if action.__class__ == _SubParsersAction:
					names_len = max([len(n) for n in action.choices.keys()]) + 2
				else:
					names_len = len(action.dest) + 2
				col1 = names_len if names_len > col1 else col1

		terminal_width, _ = get_terminal_size()
		col2 = terminal_width - col1
		
		def format_help_lines(lines):
			out = ''
			first_line = True
			at_least_one_line = False

			for line in lines:
				if first_line:
					out += line
					first_line = False
				else:
					out += ('{0:<%d}{1}'%col1).format('', line)
				out += os.linesep
				at_least_one_line = True

			if not at_least_one_line:
				out += os.linesep
			return out

		def format_action(name, helptext, choices, default, is_action, hidden):
			if hidden:
				return ''

			out = ''
			def wrap(text):
				lines = []
				if text is not None and len(text) > 0 :
					lines = textwrap.wrap(text, col2)
				return lines

			help_lines = []
			if helptext is not None:
				for help_line in helptext.split('\n'):
					help_lines += wrap(help_line.strip())

			if choices is not None:
				choices = 'choices: ' + ', '.join(choices)

			choices_lines = wrap(choices)

			default_lines = []

			if not is_action:
				if not default in [None, SUPPRESS] :
					default = 'default: ' + str(default)
				else:
					default = None
				
				default_lines = wrap(default)

			out += ('{0:<%d}'%(col1)).format(name)			
			out += format_help_lines(help_lines + choices_lines + default_lines)

			return out

		pos_usage = ''
		has_subcmd = False
		for p in positionals:
			if p.__class__ == _SubParsersAction:
				has_subcmd = True
				help += os.linesep + 'subcommands:' + os.linesep
				for subcmd in p.choices.keys():
					help += format_action(subcmd, p.choices[subcmd].description, None, None, False, False)

				usage += 'subcommand [args...]'
		
			else:
				hidden = getattr(p, const.action_hidden_attr, False) or False
				help += format_action(p.dest, p.help, p.choices, p.default, False, hidden)
				pos_usage += '%s '%p.dest

		if len(optionals) > 0:
			usage += '[options] ' if not has_subcmd else ''
			help += os.linesep + 'options:' + os.linesep

		usage += pos_usage

		for o in optionals:
			name = ', '.join(o.option_strings)
			is_action = True if issubclass(o.__class__, Action) else False
			hidden = getattr(o, const.action_hidden_attr, False) or False

			help += format_action(name, o.help, o.choices, o.default, is_action, hidden)


		if self._extrahelp is not None:
			help += os.linesep + trim_docstring(self._extrahelp)

		usage += os.linesep + os.linesep
		if help == '':
			return None

		return usage + help


	def _format_text(self, text):
		return trim_docstring(text) + os.linesep

