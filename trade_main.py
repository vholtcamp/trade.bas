'''
Container for trade game
'''
import argparse
import sys
from contextlib import nullcontext
from trade_objects import Game
import platform
from terminal.colors import ColorScheme



# *** Set modes here ***
# Standard play is autopilot = False and interactive = True, which allows user input and interaction.


def parse_bool(value):
    if isinstance(value, bool):
        return value

    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False

    raise argparse.ArgumentTypeError("Expected a boolean value: true/false")


def parse_args():
    parser = argparse.ArgumentParser(description="Run Star Traders")
    parser.add_argument(
        "--monochrome",
        action="store_true",
        help="Disable ANSI color output",
    )
    parser.add_argument(
        "--color-scheme",
        choices=[scheme.value for scheme in ColorScheme],
        default=ColorScheme.DEFAULT.value,
        help="Select color scheme",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in non-interactive mode with autoplay defaults (useful for CI)",
    )
    parser.add_argument(
        "--autopilot",
        type=parse_bool,
        nargs="?",
        const=True,
        metavar="{true,false}",
        help="Enable or disable automatic move and stock selection",
    )
    parser.add_argument(
        "--interactive",
        type=parse_bool,
        nargs="?",
        const=True,
        metavar="{true,false}",
        help="Enable or disable interactive prompts",
    )
    parser.add_argument(
        "--pause-at-end",
        type=parse_bool,
        nargs="?",
        const=True,
        metavar="{true,false}",
        help="Enable or disable end-of-game pause prompt",
    )
    parser.set_defaults(autopilot=None, interactive=None, pause_at_end=None)
    args = parser.parse_args()

    if args.headless:
        explicit_mode_flags = []
        if args.autopilot is not None:
            explicit_mode_flags.append("--autopilot")
        if args.interactive is not None:
            explicit_mode_flags.append("--interactive")
        if args.pause_at_end is not None:
            explicit_mode_flags.append("--pause-at-end")

        if explicit_mode_flags:
            parser.error(
                "--headless cannot be combined with explicit mode flags: "
                + ", ".join(explicit_mode_flags)
            )

    return args


args = parse_args()

headless = args.headless
if headless:
    interactive = False
    autopilot = True
    pause_at_end = False
else:
    interactive = True if args.interactive is None else args.interactive
    autopilot = False if args.autopilot is None else args.autopilot
    pause_at_end = True if args.pause_at_end is None else args.pause_at_end
monochrome = args.monochrome
requested_color_scheme = ColorScheme(args.color_scheme)
color_scheme = ColorScheme.DEFAULT if monochrome else requested_color_scheme




MAX_PLAYERS = 4
TOTAL_TURNS = 49


if platform.system() == 'Windows':
    from terminal.windows_terminal import WindowsTerminal
    term = WindowsTerminal(use_color=not monochrome, color_scheme=color_scheme)
else:
    from terminal.blessings_term import BlessingsTerminal
    term = BlessingsTerminal(color_scheme=color_scheme)


# Shall we play a game?

fullscreen_context = nullcontext() if monochrome else term.fullscreen()

with fullscreen_context:
    
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
                headless=headless,
                pause_at_end=pause_at_end,
                monochrome=monochrome,
                color_scheme=color_scheme,
                debug_econ=False
                )

    while game.turn_number <= game.max_turns:
        game.round()
    
