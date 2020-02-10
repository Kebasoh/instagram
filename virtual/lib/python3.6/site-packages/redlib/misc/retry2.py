from time import sleep


__all__ = ['Retry2']


def cb(retry_num, result):
	pass


class Retry2:
	def __init__(self, count=3, delay=None, exc=None, exp_bkf=False, end=lambda r : r == True, cb=None, auto_decr=True):
		self.count = 3
		self.rleft = count
		self.delay = delay
		self.exc = exc
		self.exp_bkf = exp_bkf


	def left(self):
		pass

	def decr(self):
		pass

	def done(self):
		pass

	def do(self, method, *args, **kwargs):
		pass

