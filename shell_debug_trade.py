'''
Container for trade game
'''
import sys
from trade_objects import Game

# TODO - Adjust max turns based on number of players?
# FIXME - Instructions display routine needed
MAX_TURNS = 49
number_of_players = 'x'

# FIXME - Uncomment out ask for number of players.
# while not number_of_players.isdecimal():
#     print('How many players? (Q to quit)')
#     print('> ', end = '')
#     number_of_players = input()
#     if number_of_players.upper() == 'Q':
#         sys.exit()

# number_of_players = int(number_of_players)
number_of_players = 2

game = Game(number_of_players)

while game.turn_number < MAX_TURNS:
    game.round()
game.quit()


