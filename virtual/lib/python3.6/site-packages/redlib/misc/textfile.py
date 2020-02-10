import re
import sys
from glob import glob
from os import linesep
from shutil import copy
from os.path import exists, dirname, join as joinpath, basename

import six


__all__ = ['TextFile', 'TextFileError']


class TextFileError(Exception):
	pass


class LineFilter:

	def __init__(self, id=None, startswith=None, contains=None, endswith=None, regex=None, line_no=None, comment_prefix=None, count=six.MAXSIZE):
		assert id is None or (id is not None and comment_prefix is not None)

		self.re_id 	= re.compile("^.*" + comment_prefix + ".*%s.*$"%id) if id is not None else None
		self.startswith	= startswith
		self.contains	= contains
		self.endswith	= endswith
		self.regex	= re.compile(regex) if regex is not None else None
		self.rm_line_no	= line_no
		self.max_count 	= count

		self.count	= 0
		self.line_no	= 0


	def match(self, line):
		result = False

		if self.max_count is not None and self.count == self.max_count:
			return False

		if self.rm_line_no is not None:
			result = self.line_no == self.rm_line_no

		if not result and self.re_id is not None:
			result = self.re_id.match(line) is not None

		if not result and self.startswith is not None:
			result = line.startswith(self.startswith)

		if not result and self.contains is not None:
			result = line.find(self.contains) > -1

		if not result and self.endswith is not None:
			result = line.endswith(self.endswith)

		if not result and self.regex is not None:
			result = self.regex.match(line) is not None

		if result:
			self.count += 1

		self.line_no += 1
		return result


class TextFile:

	section_end_prefix 	= 'end:'
	section_start_prefix 	= 'start:'
	default_comment_prefix	= '#'
	default_backup_ext	= 'bkp'


	def __init__(self, filepath, backup=False, comment_prefix=None, backup_ext=None):
		self._filepath 		= filepath
		self._backup 		= backup
		self._comment_prefix 	= comment_prefix if comment_prefix is not None else self.default_comment_prefix
		self._backup_ext 	= backup_ext if backup_ext is not None else self.default_backup_ext


	def check_file(self, create=False, exc=True):
		if not exists(self._filepath):
			if not create and exc:
				raise TextFileError('%s does not exist'%self._filepath)
			else:
				open(self._filepath, 'a').close()


	def backup(self, exc=True):
		self.check_file(exc=exc)

		if not self._backup:
			return None

		dirpath = dirname(self._filepath)
		backup_files = glob(joinpath(dirpath, basename(self._filepath) + '.' + self._backup_ext + '*'))

		def str_to_int(n):
			try:
				return int(n)
			except ValueError:
				return 0

		n = None
		if len(backup_files) > 0:
			backup_nos = [str_to_int(n) for n in [f[f.rfind(self._backup_ext) + len(self._backup_ext):] for f in backup_files]]
			n = max(backup_nos)
		else:
			n = 0

		ext = self._backup_ext if n == 0 else self._backup_ext + str(n + 1)

		try:
			backup_filepath = joinpath(dirpath, basename(self._filepath) + '.' + ext)
			copy(self._filepath, backup_filepath)
			return backup_filepath
		except IOError as e:
			raise TextFileError('aborting operation, could not create backup file: %s'%backup_filepath)


	def append_line(self, line, id=None, remove_dups=False):
		if remove_dups:
			count = self.find_lines(id=id)
			if count > 0:
				if count > 1:
					self.remove_lines(id, count=count-1)
				return

		self.backup(exc=False)
		with open(self._filepath, 'a+') as f:
			f.write(linesep)
			f.write(line + ('\t' + self._comment_prefix + id if id is not None else ''))


	def _insert_line(self, line, linefilter, before=False, after=False):
		assert before or after

		self.check_file()

		lines = []
		line_tb_inserted = line

		with open(self._filepath, 'r') as f:
			for line in f.read().splitlines():
				if linefilter.match(line):
					if after:
						lines.append(line + linesep)
						lines.append(line_tb_inserted + linesep)
					else:
						lines.append(line_tb_inserted + linesep)
						lines.append(line + linesep)
				else:
					lines.append(line + linesep)

		self.remove_last_linesep_and_write(lines)

		return linefilter.count


	def insert_line_before(self, line, id=None, startswith=None, contains=None, endswith=None, regex=None, count=1, line_no=None):
		linefilter = LineFilter(id=id, startswith=startswith, contains=contains, endswith=endswith, regex=regex, count=count,
				line_no=line_no, comment_prefix=self._comment_prefix)


		return self._insert_line(line, linefilter, before=True, after=False)


	def insert_line_after(self, line, id=None, startswith=None, contains=None, endswith=None, regex=None, count=1, line_no=None):
		linefilter = LineFilter(id=id, startswith=startswith, contains=contains, endswith=endswith, regex=regex, count=count,
				line_no=line_no, comment_prefix=self._comment_prefix)


		return self._insert_line(line, linefilter, before=False, after=True)


	def remove_lines(self, id=None, startswith=None, contains=None, endswith=None, regex=None, count=six.MAXSIZE, line_no=None):
		self.check_file()

		linefilter = LineFilter(id=id, startswith=startswith, contains=contains, endswith=endswith, regex=regex, count=count,
				line_no=line_no, comment_prefix=self._comment_prefix)

		lines = []

		with open(self._filepath, 'r') as f:
			for line in f.read().splitlines():
				if linefilter.match(line):
					continue
				lines.append(line + linesep)

		self.remove_last_linesep_and_write(lines)

		return linefilter.count


	def remove_last_linesep_and_write(self, lines):
		self.backup()

		if len(lines) > 0:
			lines[-1] = lines[-1][:-1]

		with open(self._filepath, 'w') as f:
			f.writelines(lines)


	def find_lines(self, id=None, startswith=None, contains=None, endswith=None, regex=None, line_no=None):
		self.check_file()

		linefilter = LineFilter(id=id, startswith=startswith, contains=contains, endswith=endswith, regex=regex, line_no=line_no,
				comment_prefix=self._comment_prefix)

		with open(self._filepath, 'r') as f:
			for line in f.read().splitlines():
				linefilter.match(line)

		return linefilter.count


	def find_section(self, id):
		self.check_file()

		with open(self._filepath, 'r') as f:
			return f.read().find(self._comment_prefix + self.section_start_prefix + id) > -1


	def append_section(self, text, id=None):
		self.backup(exc=False)
		
		with open(self._filepath, 'a+') as f:
			f.write(linesep)
			if id is not None:
				f.write(self._comment_prefix + self.section_start_prefix + id + linesep)
			f.write(text + linesep)
			if id is not None:
				f.write(self._comment_prefix + self.section_end_prefix + id)


	def remove_section(self, id):
		if id is None or len(id) == 0:
			raise TextFileError('need an identifier to find the section to remove')

		self.check_file()

		lines = []
		re_id_start = re.compile("^.*" + self._comment_prefix + ".*%s%s.*$"%(self.section_start_prefix, id))
		re_id_end = re.compile("^.*" + self._comment_prefix + ".*%s%s.*$"%(self.section_end_prefix, id))

		rm = False
		removed = False

		with open(self._filepath, 'r') as f:
			for line in f.read().splitlines():
				if re_id_start.match(line) is not None:
					if rm:
						raise TextFileError('cannot remove nested sections')
					rm = True
					continue

				if re_id_end.match(line) is not None:
					if rm:
						rm = False
						removed = True
					continue

				if not rm:
					lines.append(line + linesep)

		if rm:
			raise TextFileError('cannot remove section, end not found')

		self.remove_last_linesep_and_write(lines)

		return removed


	def prepend_line(self, line, id=None):
		pass

	
	def prepend_section(self, text, id=None):
		pass

