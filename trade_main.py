'''
Container for trade game
'''
import sys
from trade_objects import Game
from terminal.blessings_term import BlessingsTerminal
import platform


# *** Set modes here ***
# Standard play is autopilot = False and interactive = True, which allows user input and interaction.
autopilot = True   # Game selects moves and stock purchases when True; can ask for user input
interactive = False # Will allow user interaction, even if autopilot is true

MAX_PLAYERS = 4
TOTAL_TURNS = 49



if platform.system() == 'Windows':
    from terminal.windows_terminal import WindowsTerminal
    term = WindowsTerminal()
else:
    from terminal.blessings_term import BlessingsTerminal
    term = BlessingsTerminal()


# Shall we play a game?

with term.fullscreen():
    
    if not autopilot:

        while True:
            print('How many players (1 - 4)? (Q to quit)')
            print('> ', end = '')
            raw_input = input()
            
            if raw_input.upper() == 'Q':
                sys.exit()
            
            if raw_input.isdecimal():
                if int(raw_input) <= 0 or int(raw_input) > MAX_PLAYERS:
                    print(f'Please enter a number between 1 and {MAX_PLAYERS}.')
                else:
                    number_of_players = int(raw_input)
                    break
            else:
                print('Please enter a number.')
        
    else:
        number_of_players = 2
        
    max_turns = TOTAL_TURNS // number_of_players
    game = Game(number_of_players, 
                term, 
                max_turns, 
                interactive=interactive,  
                autopilot=autopilot,
                debug_econ=False
                )

    while game.turn_number <= game.max_turns:
        game.round()
    
