import sys
import warnings

from redlib.api.misc import Singleton

from .commandparser import CommandParser
from . import const
from .command_collection import _CommandCollection


class _MoveCollection(_CommandCollection):

	def __init__(self, prog=None, _to_hyphen=True, warning=True):
		super(_MoveCollection, self).__init__()

		self._to_hyphen		= _to_hyphen
		self._subcmd_attr	= const.moved_attr

		self._moves		= []
		self._prog		= prog
		self._warning		= warning


	def add_move(self, parent, subcmd):
		move = (parent if parent is not None else '') + ' ' + subcmd
		self._moves.append(move)


	def is_moved(self, args):
		if args is None:
			args = sys.argv

		for m in self._moves:
			m_parts = m.split()
			if m_parts == args[1 : len(m_parts) + 1]:
				return True
		return False


	def move(self, args, namespace=None):
		target_args = self.execute(args, namespace)

		if self._warning:
			saved_showwarning = warnings.showwarning

			def _warning(message, category=DeprecationWarning, filename='', lineno=-1):
				print('[Deprecation Warning] ' + str(message))
			warnings.showwarning = _warning

			warnings.warn('moved to \'wallp source\'; executing >wallp %s'%' '.join(target_args))
			warnings.showwarning = saved_showwarning

		return target_args


class MoveCollection(Singleton):
	classtype = _MoveCollection

