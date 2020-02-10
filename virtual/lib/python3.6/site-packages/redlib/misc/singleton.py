__all__ = ['Singleton']


class Singleton:
	classtype = None
	instance_map = {}

	def __init__(self, *args, **kwargs):
		ctype = self.classtype
		assert ctype

		if self.instance_map.get(ctype) is None:
			self.instance_map[ctype] = ctype(*args, **kwargs)
		

	def __getattr__(self, name):
		ctype = self.classtype
		return getattr(self.instance_map[ctype], name)

