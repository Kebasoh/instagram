
class Node(object):

	def __init__(self, name, alias=None, filters=None, subcmd=False):
		self._name 	= name
		self._alias	= alias
		self._children 	= None
		self._filters	= filters
		self._subcmd	= subcmd
		self._common	= []


	def __getstate__(self):
		return [self._name, self._alias, self._children, self._filters, self._subcmd, self._common]

	
	def __setstate__(self, data):
		self._name 	= data[0]
		self._alias	= data[1]
		self._children	= data[2]
		self._filters	= data[3]
		self._subcmd	= data[4]
		self._common	= data[5]


	def add_child(self, node):
		assert node.__class__ == Node
		assert self._filters is None		# presence of a match filter means it's a positional or optional arg
							# can add child only to a command or subcommand
		if self._children is None:
			self._children = []
		self._children.append(node)


	def get_name(self):
		return self._name


	def get_alias(self):
		return self._alias


	def add_common(self, node):
		self._common.append(node)


	def get_children(self):
		all = []

		for c in self._common:
			if c.children is not None:
				all.extend(c.children)

		if self._children is not None:
			all.extend(self._children)

		all = None if len(all) == 0 else all

		return all


	def get_filters(self):
		return self._filters


	def get_subcmd(self):
		return self._subcmd


	name		= property(get_name)
	alias		= property(get_alias)
	children	= property(get_children)
	filters		= property(get_filters)
	subcmd		= property(get_subcmd)

