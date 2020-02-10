import sys
from unittest import TestLoader
from functools import cmp_to_key as _CmpToKey

from ..py23.lang23 import cmp


__all__ = ['order', 'replace_default_ordering', 'restore_default_ordering']


# copied from unittest/loader/TestLoader
# modified to sort functions rather than names
def testorder_getTestCaseNames(self, testCaseClass):

        def isTestMethod(attrname, testCaseClass=testCaseClass,
                         prefix=self.testMethodPrefix):
            return attrname.startswith(prefix) and \
                hasattr(getattr(testCaseClass, attrname), '__call__')

        testFns = [getattr(testCaseClass, t) for t in filter(isTestMethod, dir(testCaseClass))]
        if self.sortTestMethodsUsing:
            testFns.sort(key=_CmpToKey(self.sortTestMethodsUsing))

        return [n.__name__ for n in testFns]


def testorder_cmp(self, tc1, tc2):
	if hasattr(tc1, '__order__') and hasattr(tc2, '__order__'):
		return cmp(tc1.__order__, tc2.__order__)
	else:
		return cmp(tc1.__name__, tc2.__name__)


orig_TestLoader_sortTestMethodsUsing = None
orig_TestLoader_getTestCaseNames = None


def replace_default_ordering():
	orig_TestLoader_getTestCaseNames = TestLoader.getTestCaseNames
	TestLoader.getTestCaseNames = testorder_getTestCaseNames

	orig_TestLoader_sortTestMethodsUsing = TestLoader.sortTestMethodsUsing
	TestLoader.sortTestMethodsUsing = testorder_cmp


def restore_default_ordering():
	TestLoader.sortTestMethodsUsing = orig_TestLoader_sortTestMethodsUsing
	TestLoader.getTestCaseNames = orig_TestLoader_getTestCaseNames


def order(i):
	'Decorator to set test case order.'

	def new_dec(func):
		func.__order__ = i
		return func

	return new_dec


replace_default_ordering()	# setup test case ordering by number when module is loaded

