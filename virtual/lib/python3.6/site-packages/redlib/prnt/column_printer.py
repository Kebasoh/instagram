from textwrap import wrap
from functools import partial
import sys

from redlib.api.system import get_terminal_size
from .func import prints, printn


__all__ = ['ColumnPrinter', 'Column', 'ColumnPrinterError', 'ProgressColumn', 'SepColumn', 'Callbacks']

# add ProgressColumn (normal, char, cont, rotate), SepColumn (w/ condition)
# column color, style, header

maxn = max
debug_msgs = False

def debug(msg):
	if debug_msgs:
		sys.stderr.write(msg + '\n')


class Callbacks:

	def __init__(self):
		self.col_updt_cb		= None		# column update callback
		self.col_updt_cp		= None		# column update complete callback
		self.progress_cb		= None		# progress callback
		self.progress_cp		= None		# progress complete callback


class Column:
	
	def __init__(self, width=1, fill=False, max=None, min=None, wrap=False, align='l', ratio=None, rmargin=1, lmargin=None, overlap=0):
		self.width	= width
		self.fill	= fill
		self.max	= max
		self.min	= maxn(min or 0, 1)
		self.wrap	= wrap
		self.align	= align
		self.ratio	= ratio
		self.rmargin	= rmargin
		self.lmargin	= lmargin
		self.overlap	= overlap


class ProgressColumn(Column):

	def __init__(self, pwidth=1, rmargin=1, char='#', char_rot=False, char_set=['-', '\\', '|', '/']):
		Column.__init__(self, width=pwidth+rmargin, rmargin=1)

		self.pwidth 	= pwidth
		self.char 	= char
		self.char_rot	= char_rot or (pwidth == 1)
		self.char_set	= char_set


class SepColumn(Column):

	def __init__(self, char=':', rmargin=1, cond=True):
		Column.__init__(self, width=rmargin+len(char), rmargin=rmargin)

		self.char	= char
		self.cond	= (lambda p, n : (p is not None and len(p.strip()) > 0) and (n is not None and len(n.strip()) > 0)) if cond else \
				lambda p, n : True


class ColumnPrinterError(Exception):
	pass


class Var:	# empty class used to hold variables so that they are accessible in callbacks inside printf
	pass


class ColumnPrinter:

	def __init__(self, cols=[Column(fill=True, wrap=True)], row_width=None):
		self._cols 		= cols
		self._fmt_string	= None

		self._col_updt_in_progress	= False
		self._newline_pending		= False
		self._row_width			= row_width

		self.process_cols()
		self.make_fmt_string()

		self.outer_cb = None
		self.outer_cp = None
		
		self._line_num = 0


	def get_row_width(self):
		return self._row_width or (get_terminal_size()[0] - 2)


	def isatty(self):
		return sys.stdout.isatty()


	def process_cols(self):
		tw = self.get_row_width()

		if any(map(lambda c : c.width < 1, filter(lambda c : c.fill == False, self._cols))):
			raise ColumnPrinterError('column width must be at least 1')

		fill_cols = list(filter(lambda c : c.fill == True, self._cols))
		if sum(map(lambda c : c.ratio or (1 / len(fill_cols)), fill_cols)) > 1:
			raise ColumnPrinterError('total of fill column ratios > 1')

		total_fixed_width = sum(map(lambda c : (c.width or 0) if not c.fill else 0, self._cols))
		if total_fixed_width > tw:
			raise ColumnPrinterError('total width of fixed width columns exceeds terminal width, %d > %d'%(total_fixed_width, tw))

		total_fill_width = tw - total_fixed_width

		if len(fill_cols) > 0 and total_fill_width == 0:
			raise ColumnPrinterError('no space for fill columns')

		fill_width_avl = total_fill_width

		for col in fill_cols:
			if col.ratio is not None and fill_width_avl < (col.ratio * total_fill_width):
				raise ColumnPrinterError('col:%d, space for fill columns exhausted'%(self._cols.index(col) + 1))

			if col.ratio is not None:
				col.width = int(col.ratio * total_fill_width)
			else:
				col.width = int(total_fill_width / len(fill_cols))

			if col.width < col.min:
				raise ColumnPrinterError('col:%d, width < minimum width, %d < %d'%(self._cols.index(col) + 1, col.width, col.min))
			if col.max is not None and col.width > col.max:
				col.width = col.max

			fill_width_avl -= col.width


	def make_fmt_string(self):
		fmt_string = u''
		align_map = {'l': '<', 'r': '>', 'c': '^'}

		i = 0
		for c in self._cols:
			fmt_string += u'{%d:%s%d}'%(i, align_map[c.align], c.width)
			i += 1

		self._fmt_string = fmt_string


	def printf(self, *args, **kwargs):	
		if not self.isatty():
			return

		def newline():
			self._line_num += 1
			print('')

		if self._col_updt_in_progress or self._newline_pending:		# flush any remaining of the previous line or inner cp column data
			self._col_updt_in_progress = False
			self._newline_pending = False			
			newline()

		col_updt = kwargs.get('col_updt', False)
		progress = kwargs.get('progress', True)
		self._col_updt_in_progress = col_updt

		args_copy = self.copy_args(*args)	

		var = Var()

		var.line_num = self._line_num
		var.cur_row = 0					# current line number for this printf call
		var.max_row = 1					# max line number (except any inner column printers)
		var.inner_cp_max_row = 1			# max line number (for any inner column printers) 
		var.inner_col_prntrs = []			# inner column printer column numbers
		var.cur_row_inner_col_prntrs = []		# inner column printers for which callback is pending for the current line
		var.inner_col_prntr_objs = []			# inner column printer objects
	
		progress_cols = []
		progress_col_count = {}

		sep_cols = []

		def outer_cb(col, msg, updt=False):		# callback: inner CP makes to update its containing column
			if not col in var.inner_col_prntrs:		
				return						# inner cp has already called done()

			if not updt:
				args_copy[col].append(msg)
			else:
				args_copy[col] = [msg]

			var.inner_cp_max_row = maxn(var.inner_cp_max_row, len(args_copy[col]))
			if not col in var.cur_row_inner_col_prntrs:
				return

			if not updt:
				var.cur_row_inner_col_prntrs.remove(col)
			print_rows()

		def outer_cp(col):			# callback: inner CP makes to signal end of updates
			if col in var.cur_row_inner_col_prntrs:
				var.cur_row_inner_col_prntrs.remove(col)

			var.inner_col_prntrs.remove(col)
			print_rows()

		for i in range(0, len(args_copy)):	
			col = self._cols[i]
			if args_copy[i].__class__ == ColumnPrinter:
				cp = args_copy[i]
				if cp.get_row_width() > col.width:
					raise ColumnPrinterError('inner row width greater than containing column width')

				cp.outer_cb = partial(outer_cb, i)
				cp.outer_cp = partial(outer_cp, i)

				var.inner_col_prntrs.append(i)
				var.inner_col_prntr_objs.append(args_copy[i])

				args_copy[i] = []		# initially nothing, a line is appended by every callback
			else:
				width = col.width - ((col.rmargin or 0) + (col.lmargin or 0))
				lines = args_copy[i].splitlines()
				args_copy[i] = []
				for line in lines:
					if col.wrap:		# wrap
						wrapped = wrap(line, width)
						args_copy[i].extend(wrapped if len(wrapped) > 0 else [''])
						var.max_row = max(var.max_row, len(args_copy[i]))
					else:			# trim
						args_copy[i] = [line[0 : width]]
						break

				if col.__class__ == ProgressColumn and progress:
					progress_cols.append(i)
					progress_col_count[i] = 0
					self._col_updt_in_progress = True

				if col.__class__ == SepColumn:
					sep_cols.append(i)

		def prints_row(row_num):	# print a single line (row) of output
			margin = lambda col, s : s if col.align == 'c' else (((col.lmargin or 0) * ' ' + s)  if col.align == 'l' else
				(s + (col.rmargin or 0) * ' '))

			row_arg = lambda i : args_copy[i][row_num] if row_num < len(args_copy[i]) else None
			prev_col = lambda i : i and row_arg(i-1)
			next_col = lambda i : i+1 < len(self._cols) and row_arg(i+1)

			sep = lambda i, col: col.char if col.cond(prev_col(i), next_col(i)) else ''

			row = map(lambda t : ((lambda i, c : margin(c, (row_arg(i) or '')) if i not in sep_cols else sep(i, c))(*t)), enumerate(self._cols))

			output = self._fmt_string.format(*row)

			if self.outer_cb is None:
				prints(output)
			else:
				self.outer_cb(output, updt=self._col_updt_in_progress)

		def print_rows():		# print lines for current args
			for i in range(var.cur_row, maxn(var.max_row, var.inner_cp_max_row)):
				prints_row(i)

				if self._col_updt_in_progress or len(var.cur_row_inner_col_prntrs) > 0 or inner_col_updt_in_progress():
					prints('\r')
					self._newline_pending = True
					break

				if self.outer_cb is None:
					newline()
					self._newline_pending = False

				var.cur_row += 1
				wait_for_inner_cps()

		def wait_for_inner_cps():			# will not go to new line unless all inner cps call back
			var.cur_row_inner_col_prntrs = list(var.inner_col_prntrs)

		def inner_col_updt_in_progress():
			return any(filter(lambda c : c.is_col_updt_in_progress(), var.inner_col_prntr_objs))

		wait_for_inner_cps()
		print_rows()

		if col_updt or (len(progress_cols) > 0 and progress):
			cb = Callbacks()

			def col_update_cb(col_num, msg):
				if var.line_num != self._line_num:
					return			# printing has moved on to next line(s)

				col = self._cols[col_num]
				width = col.width - ((col.rmargin or 0) + (col.lmargin or 0))
				if len(msg) > width:
					msg = msg[0 : width]
				args_copy[col_num] = [msg]
				print_rows()

			def col_update_cp():
				if var.line_num != self._line_num:
					return

				self._col_updt_in_progress = False
				print_rows()

			def progress_str(col_num, progress, cp=False):
				col = self._cols[col_num]
				pstr = ''

				if not col.char_rot:
					if progress is not None:
						pstr = col.char * int((float(progress) / 100) * col.pwidth)	# progress in percentage
						progress_col_count[col_num] = None
					else:
						if progress_col_count[col_num] is not None:
							char_count = (progress_col_count[col_num] % col.pwidth + 1) if not cp else col.pwidth
							pstr = (col.char * char_count)					# continuous progress w/o known limit
							progress_col_count[col_num] += 1
						else:
							return None
				else:
					progress_col_count[col_num] += 1
					pstr = col.char_set[progress_col_count[col_num] % len(col.char_set)]

				return pstr

			def progress_cb(col_num, progress):
				if not col_num in progress_cols:
					return

				args_copy[col_num] = [progress_str(col_num, progress)]
				print_rows()

			def progress_cp(col_num):
				if col_num in progress_cols:
					progress_cols.remove(col_num)

				pstr = progress_str(col_num, None, cp=True)
				if pstr is None:
					return

				args_copy[col_num] = [pstr]
				#self.done()
				print_rows()
				self._col_updt_in_progress = False

			if col_updt:
				cb.col_updt_cb = col_update_cb
				cb.col_updt_cp = col_update_cp
			if len(progress_cols) > 0:
				cb.progress_cb = progress_cb
				cb.progress_cp = progress_cp

			return cb	# return callbacks only if column update was requested or progress column(s) present


	def copy_args(self, *args):
		col_count = len(self._cols)

		args_copy = list(args)

		sep_cols = filter(lambda i : self._cols[i].__class__ == SepColumn, range(0, len(self._cols)))
		#map(lambda i : args_copy.insert(i, ''), sep_cols)
		for i in sep_cols:
			args_copy.insert(i, '')

		if len(args_copy) < col_count:
			args_copy.extend([''] * (col_count - len(args_copy)))
		elif len(args_copy) > col_count:
			del args_copy[col_count : ]
		else:
			pass

		return args_copy


	def done(self):
		if self.outer_cp is not None:
			self.outer_cp()


	def is_col_updt_in_progress(self):
		self._col_updt_in_progress

