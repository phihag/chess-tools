#!/usr/bin/env python
import argparse
import datetime
import functools
import json
import os
import pathlib
import re

import berserk
import berserk.clients
from progress.bar import Bar


CACHE_DIR = pathlib.Path(__file__).parent / 'cache'


def json_repr(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    return json.JSONEncoder.default(obj)


def cached_request(func, cache_name):
    CACHE_DIR.mkdir(exist_ok=True)
    assert re.match(r'^[-._a-zA-Z0-9]+$', cache_name)
    cache_file = CACHE_DIR / cache_name
    tmp_file = CACHE_DIR / (cache_name + '.tmp')

    if cache_file.exists():
        with cache_file.open() as cache_handle:
            return json.load(cache_handle)

    res = func()

    with tmp_file.open('w') as cache_out:
        json.dump(res, cache_out, default=json_repr)
    tmp_file.rename(cache_file)
    return res


def get_members(team_name):
    session = berserk.TokenSession(os.environ['LICHESS_TOKEN'])
    client = berserk.Client(session=session)

    team_info = client.teams._r.get(f'api/team/{team_name}')
    count = team_info['nbMembers']

    generator = client.teams.get_members(team_name)
    with Bar('downloading members', max=count) as bar:
        return [member for member in bar.iter(generator)]


def match_members(members, search, min_rating, title):
    for m in members:
        if title is not None:
            if m.get('title') != title:
                continue

        if min_rating:
            rating_info = m['perfs'].get('rapid') or m['perfs'].get('blitz')
            if not rating_info:
                continue
            if rating_info['rating'] < min_rating:
                continue

        names = [m['id'], m['username']]

        if profile := m.get('profile'):
            if first_name := profile.get('firstName'):
                names.append(first_name)
            if last_name := profile.get('lastName'):
                names.append(last_name)
            if first_name and last_name:
                names.append(first_name + ' ' + last_name)
                names.append(last_name + ',' + first_name)
                names.append(last_name + ', ' + first_name)
            if location := profile.get('location'):
                names.append(location)

        lower_search = search.lower()
        for n in names:
            if lower_search in n.lower():
                yield m
                break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--team-name', default='chessence', help='%(default)s by default')
    parser.add_argument('--min-rating', type=int, default=None)
    parser.add_argument('--title', default=None, help='FIDE title to search for')
    parser.add_argument('NAME', help='Name to search for')
    args = parser.parse_args()

    members = cached_request(functools.partial(get_members, args.team_name), args.team_name + '-members')

    for m in match_members(members, args.NAME, args.min_rating, args.title):
        name = ''
        if profile := m.get('profile'):
            if first_name := profile.get('firstName'):
                name += first_name
            
            if last_name := profile.get('lastName'):
                name += (' ' if name else '') + last_name

            if location := profile.get('location'):
                name += ', ' + location

        rapid_info = m['perfs'].get('rapid', {})
        blitz_info = m['perfs'].get('blitz', {})
        rating_info = rapid_info if rapid_info['games'] > 0 else blitz_info
        rating_str = str(rating_info.get('rating', '-')).rjust(4) + ('?' if rating_info.get('prov') else ' ')

        print(f'{rating_str} https://lichess.org/@/' + m['id'] + ' ' + name)


if __name__ == '__main__':
    main()