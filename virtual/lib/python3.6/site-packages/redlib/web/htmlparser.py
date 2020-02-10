import re
import sys
from xml.etree.ElementTree import XMLParser, Element, SubElement, ElementTree

from ..system.common import *
from six.moves.html_parser import HTMLParser

from .htmlparser_debugger import HtmlParserDebugger


__all__ = ['HtmlParser', 'HtmlStripper']


class HtmlParser(HTMLParser):
	def __init__(self, skip_tags=[], debugger=None):
		self._root = None
		self._stack = []
		self._skip_tags = skip_tags
		self._skip = False, None
		self._hpd = debugger if debugger is not None else HtmlParserDebugger(debug=False)

		if is_py3():
			HTMLParser.__init__(self, convert_charrefs=True)
		else:
			HTMLParser.__init__(self)

	
	def handle_starttag(self, tag, attrs):
		if self._skip[0] == True:
			return
		if tag in self._skip_tags:
			self._skip = True, tag
			return

		self._hpd.dump_tag(tag, attrs, level=len(self._stack))

		attr_dict = dict((k, v) for (k, v) in attrs)
		if self._root == None:
			self._root = Element(tag, attr_dict)
			self._stack.append(self._root)
		else:
			e = SubElement(self._stack[-1], tag, attr_dict)
			self._stack.append(e)


	def handle_endtag(self, tag):
		if self._skip[0] == True:
			if tag == self._skip[1]:
				self._skip = False, None
			return
		
		if tag == self._stack[-1].tag or True:
			self._stack.pop()
		else:
			if self._hpd.debugging:
				m = self._stack[-1]
				attrs = [(k, v) for (k, v) in list(m.attrib.items())]
				self._hpd.dump_tag(m.tag, attrs=attrs, level=len(self._stack), msg='mismatch')

		self._hpd.dump_tag(tag, end=True, level=len(self._stack))


	def handle_data(self, data):
		if self._skip[0]:
			return

		if self._stack:
			if self._stack[-1].text:
				self._stack[-1].text += data
			else:
				self._stack[-1].text = data

	
	def get_element_tree(self):
		return self._root


	etree = property(get_element_tree)


class HtmlStripper(HTMLParser):
	def __init__(self):
		if is_py3():
			HTMLParser.__init__(self, convert_charrefs=True)
		else:
			HTMLParser.__init__(self)

		self._output = ''


	def handle_data(self, data):
		self._output += data + ' '


	def get_output(self):
		return self._output
	
