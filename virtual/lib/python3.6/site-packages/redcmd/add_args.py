

class AddArgs:
	def __init__(self, args, add_rec=False, add_skip=False):
		self.args	= args
		self.add_rec	= add_rec
		self.add_skip	= add_skip


	def extend(self, args):
		if self.args is not None:
			self.args.extend(args)
		else:
			self.args = args

