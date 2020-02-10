
from six.moves.urllib.request import urlopen


tlds_list_url = 'http://data.iana.org/TLD/tlds-alpha-by-domain.txt'

def update():
	text = None

	try:
		response = urlopen(tlds_list_url)
		text = response.read()
		response.close()
	except HTTPError as e:
		print(e.message)
		return

	tlds = []
	for line in text.splitlines():
		line = line.strip()
		if line.startswith('#'):
			continue
		tlds.append(line.lower())
		
	with open('tlds.py', 'w') as f:
		f.write('tlds = [\n')
		for tld in tlds[0:-1]:
			f.write('\t\'%s\',\n'%tld)
		f.write('\t\'%s\'\n'%tlds[-1])
		f.write(']\n')

	print('%d tlds; tlds.py written.'%len(tlds))


if __name__ == '__main__':
	update()

