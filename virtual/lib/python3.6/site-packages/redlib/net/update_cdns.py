import re

from six.moves.urllib.request import urlopen


src_url = 'https://raw.githubusercontent.com/WPO-Foundation/webpagetest/master/agent/wpthook/cdn.h'

def update():
	response = urlopen(src_url)
	text = response.read()
	response.close()

	cdn_list_regex = re.compile("CDN_PROVIDER\s+cdnList.*?END_MARKER", re.M | re.S)
	matches = cdn_list_regex.findall(text)

	if matches is None:
		print('error in finding cdn list in source')
		return

	cdn_list_text = matches[0]
	
	lines = cdn_list_text.splitlines()
	del lines[0]
	del lines[-1]

	cdn_record_regex = re.compile("\"(.*?)\"")
	cdn_list = []

	for line in lines:
		matches = cdn_record_regex.findall(line)
		if matches is not None:
			cdn_name = matches[0]
			cdn_list.append(cdn_name.lstrip('.'))

	with open('cdns.py', 'w') as f:
		f.write('cdns = [\n')
		f.write(',\n'.join(['\t\'%s\''%cdn for cdn in cdn_list]))
		f.write('\n]\n')

	print('cdns.py updated')


if __name__ == '__main__':
	update()

