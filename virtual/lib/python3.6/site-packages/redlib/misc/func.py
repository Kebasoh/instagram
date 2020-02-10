import re
from datetime import timedelta
import hashlib

from ..system.common import is_py2
from ..py23.lang23 import cmp


__all__ = ['ob', 'str_time_period_to_seconds', 'md5hash', 'cmp_version']


def ob(input, key=b'48bldg03yghsl;741dfbml<?x8jgbv3805'):
	s = None
	mask = None

	if is_py2():
		s = bytearray(input)
		mask = bytearray(key)
	else:
		s = input
		mask = key

	lmask = len(mask)
	output = [c ^ mask[i % lmask] for i, c in enumerate(s)]

	if is_py2():
		return str(bytearray(output))
	else:
		return bytes(output)


def str_time_period_to_seconds(period):

	period_map = { 's': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks', 'M': 'months', 'Y': 'years' }
	period_regex = re.compile("(\d{1,3})((s|m|h|d|w|M|Y))")

	match = period_regex.match(period)
	
	if match is None:
		raise TimeError('bad time period: %s'%period)

	num = int(match.group(1))
	if num <= 0 :
		raise TimeError('bad time period: %s'%period)

	abbr_period = match.group(2)
	tdarg = {}	

	if abbr_period == 'M':
		tdarg['days'] = 30 * num
	elif abbr_period == 'Y':
		tdarg['days'] = 365 * num
	else:
		tdarg[period_map[abbr_period]] = num

	td = timedelta(**tdarg)
	return td.total_seconds()


def md5hash(input):
	md5h = hashlib.md5()
	md5h.update(input.encode('utf-8'))
	return md5h.hexdigest()


def cmp_version(v1, v2):
	parts1 = v1.split('.')
	parts2 = v2.split('.')

	for p1, p2 in zip(parts1, parts2):
		c = None
		try:
			i1 = int(p1)
			i2 = int(p2)
			c = cmp(i1, i2)
		except ValueError:
			c = cmp(p1, p2)

		if c != 0:
			return c

	return 0
