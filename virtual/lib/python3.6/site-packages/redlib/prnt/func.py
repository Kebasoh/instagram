'This module contains miscellaneous printing functions.'

import sys

from ..colors.colortrans import rgb2short
from ..colors.clist import colorlist
from ..system.common import is_linux, is_py3
from ..system.terminalsize import get_terminal_size


__all__ = ['printc', 'prints', 'print_colorlist', 'format_size', 'terminal_utf8', 'filter_unicode_chars']


def printc(msg, color=None):
	colorval = None
	if color is not None:
		if color.startswith('0x'):
			colorval = color
		else:
			colorval = colorlist.get(color, None)

	if colorval is not None:
		short, _ = rgb2short(colorval[2 : ])
		prints('\x1b[38;5;%sm'%short)
		prints(msg)

		if is_linux():
			print('\x1b[0m')
		else:
			print('')
	else:
		print(msg)


def prints(msg):
	if sys.stdout is not None:
		sys.stdout.write(msg)
		sys.stdout.flush()


def printn(msg):
	print(msg)


def print_colorlist():
	count = 0
	color_name_col_width = 22
	terminal_width, _ = get_terminal_size()
	colors_per_line = int(terminal_width / (color_name_col_width + 3))

	for name, value in colorlist.items():
		if is_linux():
			short, _ = rgb2short(value[2 : ])
			prints('\x1b[38;5;%sm'%short)

		prints(('{0:%d}'%color_name_col_width).format(name))

		count += 1
		if count % colors_per_line == 0 :
			print('')
	if is_linux():
		print('\x1b[0m')


def format_size(num, suffix='b'):
		'''source: http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
			by: Sridhar Ratnakumar'''

		for unit in ['','K','M','G','T','P','E','Z']:
			if abs(num) < 1024.0:
				return "%3.1f%s%s" % (num, unit, suffix)
			num /= 1024.0

		return "%.1f%s%s" % (num, 'Y', suffix)


def terminal_utf8():
	return sys.stdout.encoding == 'UTF-8'


def filter_unicode_chars(s):
	if is_py3():
		s2 = bytes(s, 'utf-8') if type(s) == str else s
		return s2.decode('ascii', 'ignore')
	else:
		return s.decode('unicode_escape').encode('ascii', 'ignore')


# docs:

printc.__doc__ = \
	"""Print the given message in specified color.

	Args:
		msg (str): The message to be printed.
		color (str): Color name. (e.g. red, blue, etc.) Or, color hex value (e.g. 0xaaaaaa).

	Notes:
		If no color is specified, the message will be printed in the default color.

		Use function `print_colorlist()` to print a list of all available color names.

		Supported Platform: Linux only.

	"""

prints.__doc__ = \
	"""Python version independent (2.7/3.x) way to print without newline.

	Args:
		msg (str): The message to be printed.
	  
	"""

print_colorlist.__doc__ = \
	"""Print a list of all available color names.

	Example:

	.. testcode::

		from redlib.prnt import *
		print_colorlist()

	.. testoutput::
	    :options: +ELLIPSIS

	    indigo, 

	"""

