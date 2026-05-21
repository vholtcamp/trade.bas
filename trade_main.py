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

def prompt_int_with_quit(prompt, min_val, max_val):
    while True:
        print(f"{prompt} ({min_val} - {max_val})? (Q to quit)")
        print('> ', end='')
        raw_input = input().strip()

        if raw_input.upper() == 'Q':
            sys.exit()

        if raw_input.isdecimal():
            value = int(raw_input)
            if min_val <= value <= max_val:
                return value
            print(f'Please enter a number between {min_val} and {max_val}.')
            continue

        print('Please enter a number.')


def prompt_ai_difficulty(label='computer'):
    options = {
        'B': 'beginner',
        'I': 'intermediate',
        'A': 'advanced',
    }

    while True:
        print(f'Select {label} difficulty: [B]eginner, [I]ntermediate, [A]dvanced (Q to quit)')
        print('> ', end='')
        raw_input = input().strip().upper()

        if raw_input == 'Q':
            sys.exit()

        if not raw_input:
            return 'beginner'

        if raw_input in options:
            return options[raw_input]

        print('Please enter B, I, A, or Q.')


def get_startup_configuration():
    if autopilot:
        return 2, 0, 'beginner', ['beginner', 'beginner']

    if not interactive:
        return 2, 2, 'beginner', []

    number_of_players = prompt_int_with_quit('How many total players (human + computer)', 1, MAX_PLAYERS)
    human_players = prompt_int_with_quit('How many human players', 1, number_of_players)

    computer_players = number_of_players - human_players
    ai_difficulty = 'beginner'
    ai_difficulties = []
    if computer_players > 0:
        for i in range(1, computer_players + 1):
            difficulty = prompt_ai_difficulty(label=f'Computer {i}')
            ai_difficulties.append(difficulty)
        ai_difficulty = ai_difficulties[0]

    return number_of_players, human_players, ai_difficulty, ai_difficulties


def display_startup_summary(number_of_players, human_players, ai_difficulties):
    computer_players = number_of_players - human_players
    label_width = 15
    rows = [
        f"{'Total players:':<{label_width}} {number_of_players}",
        f"{'Human players:':<{label_width}} {human_players}",
        f"{'Computer seats:':<{label_width}} {computer_players}",
    ]

    if computer_players > 0:
        for i, difficulty in enumerate(ai_difficulties, start=1):
            rows.append(f"{'Computer ' + str(i) + ':':<{label_width}} {difficulty.title()}")

    border = "=" * max(len(" Game Setup Summary "), max(len(row) for row in rows))

    print()
    print(border)
    print("Game Setup Summary")
    print(border)
    for row in rows:
        print(row)
    print(border)
    print()


fullscreen_context = nullcontext() if monochrome else term.fullscreen()

with fullscreen_context:
    number_of_players, human_players, ai_difficulty, ai_difficulties = get_startup_configuration()

    if interactive and not autopilot:
        display_startup_summary(number_of_players, human_players, ai_difficulties)

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
                debug_econ=False,
                human_players=human_players,
                ai_difficulty=ai_difficulty,
                ai_difficulties=ai_difficulties,
                )

    while game.turn_number <= game.max_turns:
        game.round()
    
