from unittest import defaultTestLoader, runner
import sys


__all__ = ['TestRunner']


class TestRunner:

	def __init__(self, path):
		self._path = path


	def run_all(self):
		tests = defaultTestLoader.discover(self._path)

		testRunner = runner.TextTestRunner()
		result = testRunner.run(tests)

		sys.exit(not result.wasSuccessful())

