'''
Container for trade game
'''
import sys
from trade_objects import Game
import logging
from blessings import Terminal

logging.basicConfig(filename='myapp.log', level=logging.INFO)


# FIXME - Instructions display routine needed
TOTAL_TURNS = 49
number_of_players = 'x'

term = Terminal()

with term.fullscreen():
    # FIXME - Uncomment out ask for number of players.
    # while not number_of_players.isdecimal():
    #     print('How many players? (Q to quit)')
    #     print('> ', end = '')
    #     number_of_players = input()
    #     if number_of_players.upper() == 'Q':
    #         sys.exit()

    # number_of_players = int(number_of_players)
    number_of_players = 2
    max_turns = TOTAL_TURNS // number_of_players
    game = Game(number_of_players, term, max_turns)

    while game.turn_number < max_turns:
        game.round()
    game.quit()
