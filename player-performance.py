#!/usr/bin/env python3

import argparse
import statistics

import chess.pgn


def read_games(filenames):
    for filename in filenames:
        with open(filename) as f:
            while True:
                game = chess.pgn.read_game(f)
                if not game:
                    break
                yield game

FIDE_PERFORMANCE_TABLE = {
    100: 800, 83: 273, 66: 117, 49: -7, 32: -133, 15: -296,
    99: 677, 82: 262, 65: 110, 48: -14, 31: -141, 14: -309,
    98: 589, 81: 251, 64: 102, 47: -21, 30: -149, 13: -322,
    97: 538, 80: 240, 63: 95 , 46: -29, 29: -158, 12: -336,
    96: 501, 79: 230, 62: 87 , 45: -36, 28: -166, 11: -351,
    95: 470, 78: 220, 61: 80 , 44: -43, 27: -175, 10: -366,
    94: 444, 77: 211, 60: 72 , 43: -50, 26: -184, 9: -383,
    93: 422, 76: 202, 59: 65 , 42: -57, 25: -193, 8: -401,
    92: 401, 75: 193, 58: 57 , 41: -65, 24: -202, 7: -422,
    91: 383, 74: 184, 57: 50 , 40: -72, 23: -211, 6: -444,
    90: 366, 73: 175, 56: 43 , 39: -80, 22: -220, 5: -470,
    89: 351, 72: 166, 55: 36 , 38: -87, 21: -230, 4: -501,
    88: 336, 71: 158, 54: 29 , 37: -95, 20: -240, 3: -538,
    87: 322, 70: 149, 53: 21 , 36: -102, 19: -251, 2: -589,
    86: 309, 69: 141, 52: 14 , 35: -110, 18: -262, 1: -677,
    85: 296, 68: 133, 51: 7  , 34: -117, 17: -273, 0: -800,
    84: 284, 67: 125, 50: 0  , 33: -125, 16: -284,
}


# From https://en.wikipedia.org/wiki/Performance_rating_(chess)
def perfect_performance_rating(opponent_ratings: list[float], score: float) -> int:
    """Calculate mathematically perfect performance rating with binary search"""

    def expected_score(opponent_ratings: list[float], own_rating: float) -> float:
        """How many points we expect to score in a tourney with these opponents"""
        return sum(
            1 / (1 + 10**((opponent_rating - own_rating) / 400))
            for opponent_rating in opponent_ratings
        )

    lo, hi = 0, 4000

    while hi - lo > 0.001:
        mid = (lo + hi) / 2

        if expected_score(opponent_ratings, mid) < score:
            lo = mid
        else:
            hi = mid

    return round(mid)


def main():
    parser = argparse.ArgumentParser(description='Output performance of a player (with a color)')
    parser.add_argument('-c', '--color', choices=['white', 'black'])
    parser.add_argument('-p', '--player', required=True, metavar='NAME', help='Player name to search for')
    parser.add_argument('PGNS', nargs='+', help='PGN files to read')
    args = parser.parse_args()
    player = args.player

    opponent_ratings = []
    total_points = 0

    games = list(read_games(args.PGNS))
    for game in games:
        pwhite = game.headers['White']
        is_white = player in pwhite
        pblack = game.headers['Black']
        is_black = player in pblack

        assert not (is_white and is_black), \
            f'Found player search "{player}" in both white {pwhite!r} and black {pblack!r}'

        if not (is_white or is_black):
            continue

        if args.color == 'white':
            if not is_white:
                continue
        if args.color == 'black':
            if not is_black:
                continue


        white_rating_str = game.headers.get('WhiteElo', 0)
        white_rating = 0 if white_rating_str == '-' else int(white_rating_str)
        black_rating_str = game.headers.get('BlackElo', 0)
        black_rating = 0 if black_rating_str == '-' else int(black_rating_str)

        if 'Result' not in game.headers:
            print(game)
        game_result = game.headers['Result']

        game_point = {
            '1-0': 1,
            '1/2-1/2': 0.5,
            '0-1': 0,
        }[game_result]
        if is_white:
            player_rating, opponent_rating = white_rating, black_rating
        else:
            game_point = 1 - game_point
            player_rating, opponent_rating = black_rating, white_rating

        if not opponent_rating:
            continue

        total_points += game_point
        opponent_ratings.append(opponent_rating)

    game_count = len(opponent_ratings)
    if not game_count:
        raise ValueError(f'Could not find any games for player {player!r}')

    percent = int(round(100 * total_points / game_count))
    perfect_performance = perfect_performance_rating(opponent_ratings, total_points)
    fide_performance = round(statistics.mean(opponent_ratings)) + FIDE_PERFORMANCE_TABLE[percent]
    print(f'Scored {total_points} out of {game_count} games ({percent}%)')
    print(f'FIDE performance: {fide_performance}')
    print(f'Perfect performance: {perfect_performance}')

if __name__ == '__main__':
    main()