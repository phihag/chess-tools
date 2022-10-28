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


def json_repr(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    return json.JSONEncoder.default(obj)


def cached_request(func, cache_name):
    cache_dir = pathlib.Path('cache')
    cache_dir.mkdir(exist_ok=True)
    assert re.match(r'^[-._a-zA-Z0-9]+$', cache_name)
    cache_file = cache_dir / cache_name
    tmp_file = cache_dir / (cache_name + '.tmp')

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


def match_members(members, search):
    for m in members:
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
        for n in names:
            if search in n:
                yield m
                break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--team-name', default='chessence')
    parser.add_argument('NAME', help='Name to search for')
    args = parser.parse_args()

    members = cached_request(functools.partial(get_members, args.team_name), args.team_name + '-members')

    for m in match_members(members, args.NAME):
        name = ''
        if profile := m.get('profile'):
            if first_name := profile.get('firstName'):
                name += first_name
            
            if last_name := profile.get('lastName'):
                name += (' ' if name else '') + last_name

            if location := profile.get('location'):
                name += ', ' + location

        print('https://lichess.org/@/' + m['id'] + ' ' + name)


if __name__ == '__main__':
    main()