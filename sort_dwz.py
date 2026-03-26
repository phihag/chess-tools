#!/usr/bin/env python

import argparse
import csv
import re
import sys


def normalize_name(name):
    name = re.sub(r',?Dr\.\s*', '', name)
    return re.sub(r'\s*,\s*', ',', name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dwz-file', metavar='spieler.csv', default='spieler.csv',
        help='DWZ CSV file. %(default)s by default')
    parser.add_argument(
        '--dwz-encoding', default='cp1252',
        help='Encoding of the DWZ file. %(default)s by default')
    parser.add_argument(
        'PLAYERS_FILE', metavar='PLAYERS.csv',
        help='list of players, e.g. exported from DSAM')
    args = parser.parse_args()

    # Read DWZ file and build lookup dictionary
    by_player = {}
    with open(args.dwz_file, encoding=args.dwz_encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = normalize_name(row['Spielername'])
            if name in by_player:
                continue  # duplicate name, keep the first one

            dwz = row['DWZ']
            if not dwz:
                continue
            dwz = int(dwz)

            by_player[name] = dwz

    # Read players file
    players = []
    with open(args.PLAYERS_FILE) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            name = row[1]
            dwz = by_player.get(normalize_name(name), 0)
            players.append((dwz, name))

    # Sort by DWZ descending
    players.sort(key=lambda x: x[0], reverse=True)

    # Output sorted players
    writer = csv.writer(sys.stdout)
    for seed, (dwz, player) in enumerate(players, start=1):
        last_name, _, first_name = player.partition(',')
        full_name = f'{first_name.strip()} {last_name.strip()}'
        writer.writerow([seed, full_name])


if __name__ == '__main__':
    main()
