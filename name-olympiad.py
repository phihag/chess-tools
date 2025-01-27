#!/usr/bin/env python3

import argparse
import collections
import pathlib
import xml.dom.minidom
import xml.parsers.expat
import statistics


from lxml import etree


def parse_players(xml_path):
	doc = etree.parse(str(xml_path))
	root = doc.getroot()

	for player_el in root.findall('player'):
		props = {}
		for c in player_el:
			props[c.tag] = c.text
		yield props


def get_titles(player):
	res = []
	if t := player['title']:
		res.append(t)
	if t := player['w_title'] and t != player['title']:
		res.append(t)
	if not res and player['foa_title']:
		res.append(player['foa_title'])
	return res


def unify_name(n):
	return {
		'Alex': 'Alexander',
		'Alexander': 'Alexander',
		'Alexandr': 'Alexander',
		'Benjamin': 'Ben',
		'Dmitri': 'Dmitry',
		'Dmitriy': 'Dmitry',
		'John': 'Jon',
		'Johnathan': 'Jon',
		'Jonathan': 'Jon',
		'Josephine': 'Josefine',
		'Mike': 'Michael',
		'Mikhail': 'Michael',
		'Mohammed': 'Muhammed',
		'Olexandr': 'Alexander',
		'Pawel': 'Pavel',
		'Peta': 'Peter',
		'Petr': 'Peter',
		'Philipp': 'Philip',
		'Phillip': 'Philip',
		'Sergei': 'Sergey',
		'Vlad': 'Vladimir',
		'Wlad': 'Vladimir',
		'Wladimir': 'Vladimir',
		'Yuriy': 'Yuri',
	}.get(n, n) 


def get_rating(player):
	return int(player.get('rating') or 0)


def main():
	parser = argparse.ArgumentParser(description='A fun name Olympiad')
	parser.add_argument('-w', '--women', action='store_true', help='Only show female players')
	args = parser.parse_args()

	players = parse_players(pathlib.Path(__file__).parent / 'standard_rating_list.xml')
	by_firstname = collections.defaultdict(list)
	for p in players:
		if args.women:
			if p['sex'] != 'F':
				continue

		firstname_parts = p['name'].partition(',')[2].strip().split()
		if firstname_parts:
			firstname = firstname_parts[0]
		else:
			firstname = p['name'].partition(' ')[0]
		firstname = unify_name(firstname.partition('-')[0])
		by_firstname[firstname].append(p)

	TEAM_SIZE = 5
	for team in by_firstname.values():
		team.sort(key=lambda p: get_rating(p), reverse=True)
		if len(team) > TEAM_SIZE:
			del team[TEAM_SIZE:]

	qualifying_teams = {
		name: players for name, players in by_firstname.items()
		if len(players) >= TEAM_SIZE - 1}

	teams = sorted(
		qualifying_teams.items(),
		key=lambda spec: statistics.mean(get_rating(p) for p in spec[1]), reverse=True)

	for team_idx, (name, players) in enumerate(teams, start=1):
		avg_rating = sum(get_rating(p) for p in players) / TEAM_SIZE
		print(f'# Team {team_idx}: {name} (average {avg_rating})')
		for position, p in enumerate(players, start=1):
			title_str = '/'.join(get_titles(p))
			print(f'{position}. {get_rating(p)} {title_str} {p["name"]} [{p["country"]}]')
		print()



if __name__ == '__main__':
	main()