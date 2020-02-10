__all__ = ['HtmlParserDebugger']


class HtmlParserDebugger:
	def __init__(self, debug=False, filter=None, children=True):
		self._debug = debug
		self._filter = filter
		self._start_level = None

	
	def dump_tag(self, tag, attrs=None, end=False, level=0, msg=None):
		if self._debug:
			if self._filter and self._start_level is None:
				matches = [(k, v) for (k, v) in self._filter if (k, v) in attrs] if attrs else []
				if len(matches) == 0:
					return
				self._start_level = level

			if self._start_level is not None:
				if end:
					if level == self._start_level:
						self._start_level = None
			
			spaces = ''.join([' ' for i in range(level)])
			attr_string = None
			if attrs:
				attr_string = ''
				for (k, v) in attrs:
					attr_string += ' ' + str(k) + '=\"' + str(v) + '\"'
			print(('%s<%s%s%s>%s'%(spaces, ('/' if end else ''), tag, (attr_string if attr_string else ''),
						(' ' + msg if msg else ''))))


	def is_debugging(self):
		return self._debug


	debugging = property(is_debugging)
	
