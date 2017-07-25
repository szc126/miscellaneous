import collections
import argparse
import colorama
import json
import os
import re
import requests

LANGUAGE = 'Default' # Default, Japanese, Romaji, English

OUTPUT_FILE = 'tag out.txt'
DELIMITER = '\t'

METADATA_FORMAT = {
	'TITLE': '$title',
	'ARTIST': '$vocalists',
	'COMPOSER': '$producers',
	'ALBUM': '',
	'GENRE': '',
	'DATE': '$year',
	'URL': '$url',
	'COMMENT': '$song_type song ; $x_db_id@$x_db',
}

service_regexes = {
	'NicoNicoDouga': '[sn]m\d+',
	'Youtube': '[A-Za-z0-9_-]{11}'
}

service_urls = {
	'NicoNicoDouga': 'http://www.nicovideo.jp/watch/{}',
	'Youtube': 'https://www.youtube.com/watch?v={}'
}

db_urls = collections.OrderedDict()
db_urls['vocadb'] = 'http://vocadb.net/api/songs/byPv?pvService={}&pvId={}&fields=Artists&lang={}'
db_urls['utaitedb'] = 'http://utaitedb.net/api/songs/byPv?pvService={}&pvId={}&fields=Artists&lang={}'

parser = argparse.ArgumentParser(description='LOREM IPSUM DOLOR SIT AMET')
parser.add_argument('FOOBAR', help='LOREM IPSUM DOLOR SIT AMET', metavar='LOREM IPSUM DOLOR SIT AMET')
args = parser.parse_args()

colorama.init(autoreset=True)

def fetch_data(service, id):
	"""Fetch PV data from the VocaDB/UtaiteDB API"""

	for db in db_urls:
		response = requests.get(db_urls[db].format(service, id, LANGUAGE))

		if not response.content == b'null':
			return db, response
			break

	print(colorama.Back.RED + f'The video \'{id}@{service}\' is not registered on VocaDB or UtaiteDB!')
	return None, None

def check_connectivity():
	"""Check to see if the NND API can be reached"""

	try:
		fetch_data('NicoNicoDouga', 'sm26661454')
	except:
		print(colorama.Back.RED + 'Server could not be reached!')
		quit()

def generate_metadata(service, id):
	"""Parse and rearrange the data from the VocaDB API"""

	db, api_data = fetch_data(service, id)

	if api_data is None:
		return None

	api_data = json.loads(api_data.content)

	metadata = {
		'title': None,
		'song_type': None,
		'publish_date': None, 'year': None,
		'producers': [],
		'vocalists': [],
		'url': [],

		# meta-metadata
		'x_db': None,
		'x_db_id': None,
		'x_synthesizers': {
			'vocaloid': None,
			'utau': None,
			'cevio': None,
			'other_synthesizer': None,
			'actual_human_people': None,
		},
	}

	metadata['x_db'] = db

	metadata['x_db_id'] = api_data['id']

	metadata['title'] = api_data['name']

	metadata['song_type'] = api_data['songType']

	if 'publishDate' in api_data:
		metadata['publish_date'] = api_data['publishDate']

		metadata['year'] = metadata['publish_date'][0:4] # it just werks

	metadata['url'] = service_urls[service].format(id)

	for artist in api_data['artists']:
		# print(artist)
		# print()

		if not 'artist' in artist: # custom artist
			pass
		elif artist['artist']['artistType'] == 'Vocaloid':
			metadata['x_synthesizers']['vocaloid'] = True
			metadata['vocalists'].append(artist['name'])
		elif artist['artist']['artistType'] == 'UTAU':
			metadata['x_synthesizers']['utau'] = True
			metadata['vocalists'].append(artist['name'])
		elif artist['artist']['artistType'] == 'CeVIO':
			metadata['x_synthesizers']['cevio'] = True
			metadata['vocalists'].append(artist['name'])
		elif artist['artist']['artistType'] == 'OtherVoiceSynthesizer':
			metadata['x_synthesizers']['other_synthesizer'] = True
			metadata['vocalists'].append(artist['name'])
		elif ('Vocalist' in artist['roles']) or ('Vocalist' in artist['categories'] and 'Default' in artist['roles']): # what's the difference between 'roles' and 'effectiveRoles'
			metadata['x_synthesizers']['actual_human_people'] = True
			metadata['vocalists'].append(artist['name'])

		elif 'Composer' in artist['roles']:
			metadata['producers'].append(artist['name'])

		elif 'Default' in artist['roles'] and 'Producer' in artist['categories']:
			metadata['producers'].append(artist['name'])

	return metadata

def determine_service_and_id(path):
	"""Test path against regexes to determine the service and PV ID"""

	for service in service_regexes:
		matches = re.search('(' + service_regexes[service] + ')' + '.+(mp3|m4a)', path)

		if matches:
			return service, matches.group(1)
			break
		else:
			print(f'tis not {service}')

def tag_file(path):
	"""Given the file path, write lines for mp3tag"""

	service, id = determine_service_and_id(path)
	print(id)

	metadata = generate_metadata(service, id)

	if metadata is None:
		return None

	def metadata_returner(x):
		metadata_value = metadata[x.group(1)]
		if type(metadata_value) is list:
			metadata_value = '; '.join(metadata_value)
		elif type(metadata_value) is int:
			metadata_value = str(metadata_value)
		return metadata_value

	with open(OUTPUT_FILE, mode='a', encoding='utf-8') as file:
		metadata_values = [path]

		for field in METADATA_FORMAT:
			metadata_value = re.sub('\$([a-z_]+)', metadata_returner, METADATA_FORMAT[field]) # pattern, repl, string
			metadata_values.append(metadata_value)

		file.write(DELIMITER.join(metadata_values) + '\n')

def write_mp3tag_format_string():
	with open(f'{OUTPUT_FILE}-format string.txt', mode='w', encoding='utf-8') as file:
		format_string = ['%_filename_ext%']

		for field in METADATA_FORMAT:
			format_string.append('%{}%'.format(field.lower()))

		file.write(DELIMITER.join(format_string) + '\n')

def main():
	check_connectivity()

	write_mp3tag_format_string()

	# tentative
	for dir, subdirs, files in os.walk(args.FOOBAR):
		for file in files:
			if file.endswith(('.mp3', '.m4a')):
				tag_file(file)

if __name__ == "__main__":
	main()
