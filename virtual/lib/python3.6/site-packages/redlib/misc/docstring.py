import sys
import inspect
import re
import os


__all__ = ['trim_docstring', 'extract_help_w_regex', 'extract_help']


def trim_docstring(doc_string):
	if not doc_string:
		return ''
	# Convert tabs to spaces (following the normal Python rules)
	# and split into a list of lines:
	lines = doc_string.expandtabs().splitlines()
	# Determine minimum indentation (first line doesn't count):
	indent = sys.maxsize
	for line in lines[1:]:
		stripped = line.lstrip()
		if stripped:
			indent = min(indent, len(line) - len(stripped))
	# Remove indentation (first line is special):
	trimmed = [lines[0].strip()]
	if indent < sys.maxsize:
		for line in lines[1:]:
			trimmed.append(line[indent:].rstrip())
	# Strip off trailing and leading blank lines:
	while trimmed and not trimmed[-1]:
		trimmed.pop()
	while trimmed and not trimmed[0]:
		trimmed.pop(0)
	# Return a single string:
	return '\n'.join(trimmed)


def extract_help_w_regex(func):
	help = {}

	if func.__doc__ is not None:
		argspec = inspect.getargspec(func)
		if argspec.args[0] == 'self':
			del argspec.args[0]

		regex_args_help = "(.*)"				# short
		for arg in argspec.args:
			regex_args_help += "((%s):(.*))"%arg		# argument help
		regex_args_help += "(?:\n\s*\n.*)"			# longer help text

		regex = re.compile(regex_args_help, re.M | re.S)

		match = regex.match(func.__doc__)

		if match:
			help['short'] = match.group(1).strip()				# extract short description

			i = 3
			for _ in range(len(argspec.args)):
				help[match.group(i)] = match.group(i + 1).strip()
				i += 3

			help['long'] = match.group(i - 2).strip()			# extract long description

		if getattr(func, '__extrahelp__', None) is not None:			# extract any extra help
			help['extra'] = func.__extrahelp__.strip()

	return help


def extract_help(func):
	help = {
		'short'	: None,
		'long' 	: None
	}
	args = inspect.getargspec(func).args

	if func.__doc__ is not None:
		argspec = inspect.getargspec(func)
		item = 'short'

		for line in func.__doc__.splitlines():
			if len(line.strip()) == 0:
				item = 'long'
				continue

			if line.find(':') > 0:
				parts = line.split(':', 1)
				if parts[0].strip() in args:
					item = parts[0].strip()
					line = parts[1].strip()

			if item in help.keys() and help[item] is not None:
				help[item] += os.linesep + line.strip()
			else:
				help[item] = line.strip()

	return help


extract_help.__doc__ = \
	"""Extract help text from doc string of a function.

	Args:
		func: Function for which help is to be extracted.

	Returns:
		(dict): With the following elements.

		short: short help text, appearing at the beginning of the doc string\n
		long: long help text, appearing after the argument help\n
		an element for each of the argument for which help is present

	.. testcode::
		
		from redlib.misc.docstring import extract_help
		from pprint import pprint

		def div(a, b):
			'''Divide  first number by second number.
			Note: result will be float.
			
			a: 	first number
			b: 	second number
			may not be zero
			
			This is extra help text (long).'''
			pass

		help = extract_help(div)
		pprint(help)

	.. testoutput::
	
		{'a': 'first number',
		 'b': 'second number\\nmay not be zero',
		 'long': 'This is extra help text (long).',
		 'short': 'Divide  first number by second number.\\nNote: result will be float.'}
	
	**Extraction Logic**

	1. Look for docstring in function. If no docstring found, return empty help dictionary ({'short': None, 'long': None}).
	2. Extract line(s) and assign them to help['short'] until help for an argument or a blank line or end of docstring is encountered.
	3. For any line with a colon(:) in it, split it on colon and check if first part is an argument name. If yes, then, add the text following the colon to help[argument_name]. If no, then, just add the line as continuation for last help item found.
	4. If a blank line is found, the text following it is added to help['long'], unless, it is argument help.

	"""

extract_help_w_regex.__doc__ = \
	"""Extract help text from doc string of a function using regex. (Deprecated)"""

trim_docstring.__doc__ = \
	"""Trim leading and trailing blank lines as well as tabs from docstring.

	Source: https://www.python.org/dev/peps/pep-0257/"""
	
