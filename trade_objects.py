
import collections
from collections import defaultdict, Counter, OrderedDict
import sys
import shutil
import locale
import time
import textwrap
locale.setlocale(locale.LC_ALL, '')
import json

import random
from random import randint




# NOTE: Uncomment for reproducible board setups during manual debugging.
# random.seed(10)


from enum import Enum, auto
from typing import Dict, Set
from terminal.colors import ColorScheme, get_company_color
from ai_strategies import build_ai_strategy

from dataclasses import dataclass


import re
no_cents = re.compile(r'.00$')
ANSI_ESCAPE_RE = re.compile(
    r'\x1b(?:\[[0-?]*[ -/]*[@-~]|[@-Z\\-_]|[\(\)][A-Za-z0-9])'
)

def visible_len(text: str) -> int:
    return len(ANSI_ESCAPE_RE.sub('', text))



# -----------------------------------------------------------------------------
# Core Game Constants (Domain / Rules)
# -----------------------------------------------------------------------------

COL_LIST = list('ABCDEFGHIJKL')
ROW_LIST = list('123456789')

MAP_PRINT_SPACE = '  '
MAP_HEADER = f' {MAP_PRINT_SPACE}{MAP_PRINT_SPACE.join(COL_LIST)}'
MAP_WIDTH = len(MAP_HEADER) + len(MAP_PRINT_SPACE)

STAR = '*'
OUTPOST = '+'
EMPTY_SPACE = '.'
MAX_MOVES = 5

STARTING_CASH = 6000
STARTING_SHARE_PRICE = 100
OUTPOST_BONUS = 100
STAR_BONUS = 500
FOUNDERS_BONUS_SHARES = 5
TWO_FOR_ONE_PRICE = 3000
DIVIDEND_MULTIPLIER = 0.05
COMPUTER_THINK_DELAY_SECONDS = 1.1
ACTION_STATUS_MAX_LINES = 2

# BASIC rule: merger cash bonus is 10x losing share price,
# prorated by ownership and truncated to integer
BASIC_MERGER_CASH_MULTIPLIER = 10

# Dictionary of company names and map symbols
COMPANIES = {
            'Altair Starways': 'A',
            'Betelgeuse Ltd.': 'B',
            'Capella Freight Co.': 'C',
            'Denebola Shippers': 'D',
            'Eridani Expediters': 'E'
        }

CREATE_COMPANY_SYMBOLS = set((STAR, OUTPOST))
COMPANY_SYMBOLS = set((COMPANIES.values()))
OCCUPIED_MAP_SYMBOLS = CREATE_COMPANY_SYMBOLS.union(COMPANY_SYMBOLS)


# -----------------------------------------------------------------------------
# Domain Types and Tile Classification
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Neighborhood:
    center: str
    neighbors: Dict[str, str]
    stars: int
    outposts: int
    companies: Set[str]


class TileKind(Enum):
    EMPTY = auto()
    STAR = auto()
    OUTPOST = auto()
    COMPANY = auto()


def tile_kind_from_symbol(symbol):
    if symbol == EMPTY_SPACE:
        return TileKind.EMPTY
    if symbol == STAR:
        return TileKind.STAR
    if symbol == OUTPOST:
        return TileKind.OUTPOST
    if symbol in COMPANY_SYMBOLS:
        return TileKind.COMPANY
    raise ValueError(f"Unknown map symbol: {symbol}")


# -----------------------------------------------------------------------------
# Economic Diagnostics (Debug Logging)
# -----------------------------------------------------------------------------

# Economic event logging (diagnostic only).
# Used to inspect game economy behavior during testing.
# Safe to disable or remove without affecting gameplay.
# Set DEBUG_ECON in trade_main.py to True to enable logging of economic events,
# which will be written as JSON lines into ECON_LOG_FILE.

ECON_LOG_FILE = 'econ_events.log'


def _snapshot_company(company):
    return {
        'share_price': company.share_price,
        'price_quantum': company.price_quantum,
        'total_shares': company.total_shares(),
    }


def _snapshot_player(player, symbols):
    return {
        'cash': player.cash_on_hand,
        'shares': {
            symbol: player.portfolio.get(symbol, 0)
            for symbol in symbols
        },
    }


def log_econ_event(turn_number, event_type, company_symbols, players=None,
                   before=None, after=None, details=None):

    payload = {
        'turn': turn_number,
        'event_type': event_type,
        'company_symbols': company_symbols,
        'players': players or [],
        'before': before or {},
        'after': after or {},
        'details': details or {},
    }
    with open(ECON_LOG_FILE, 'a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(payload, sort_keys=True) + '\n')


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class Player():
    '''
    Player manages cash and portfolio, and also has "take_turn" method
    consisting of making a move and then buying stocks.
    Portfolio dictionary has key of company symbol and value of # of shares, set to
    a defaultdict (int) so that 0 will always be returned.
    '''

    def __init__(self, name, game, is_computer=False, ai_difficulty='beginner', ai_strategy=None):
        # TODO - Input values for names
        self.name = name
        self.cash_on_hand = STARTING_CASH
        self.portfolio = defaultdict(int)
        self.game = game
        self.is_computer = is_computer
        self.ai_difficulty = ai_difficulty
        self.ai_strategy = ai_strategy
        self.old_data_for_display = 0


    def choose_move(self, legal_moves, autopilot=False):
        if autopilot or self.is_computer:
            move = self.game.choose_ai_move(self, legal_moves)
            return move
        
        while True:
                moves = ", ".join(legal_moves)
                print(f"{self.name}, choose a move from: {moves}")
                raw = self.game.display.input_prompt().strip().upper()

                # Empty input → reprompt
                if not raw:
                    continue

                # # Allow quit at any input prompt
                if raw == 'Q':
                    self.game.quit()
                    continue

                # Coordinate input must be exactly 2 characters (e.g., 'G8')
                if len(raw) != 2:
                    print("Please enter a move like 'G8', or 'Q' to quit.")
                    continue
                
                if raw in legal_moves:
                    return raw

                print("That was not a legal move. Please try again.")


    def buy_stocks(self):
        '''
        Loop through all active companies and let player buy stock. Update
        portfolio and cash_on_hand as needed. Blank entry converted to zero.
        '''
        term = self.game.terminal
        for symbol in sorted(self.game.active_companies.keys()):
            c = self.game.active_companies[symbol]
            self.game.display.display_map(self)
            if self.game.display.colors_enabled:
                formatted_name = term.color(c.name, fg=self.game.display.company_color(c.symbol))
            else:
                formatted_name = c.name

            while True:
                shares_raw = self.game.display.prompt_stock_purchase(c, self)
                shares_raw = shares_raw.strip().upper()

                # Blank input → skip purchasing for this company    
                if not shares_raw:
                    self.game.last_action = f"Skipped purchase of {formatted_name}"
                    break

                # # Allow quit at any input prompt
                if shares_raw == 'Q':
                    self.game.quit()
                    continue

                # Input must be a number
                if not shares_raw.isdigit():
                    print("Please enter a number, press Enter to skip, or 'Q' to quit.")
                    continue
                
                shares = int(shares_raw)

                # Skip if player doesn't want to buy any shares of this company
                if shares == 0:
                    break

                if not self._valid_share_purchase(c, shares):
                    print("You do not have enough cash to cover that purchase.")
                    print("Try a smaller number, or press Enter to skip.")
                    continue


                
                # Valid purchase - apply it and break out of loop to move on to next company
                self.game.last_action = f"Purchased {shares} shares of {formatted_name}"

                if self.game.debug_econ:
                    symbols = [c.symbol]
                    before_company = _snapshot_company(c)
                    before_player = _snapshot_player(self, symbols)

                self.portfolio[c.symbol] += shares
                self.cash_on_hand -= shares * c.share_price

                if self.game.debug_econ:
                    log_econ_event(
                        turn_number=self.game.turn_number,
                        event_type='stock_purchase',
                        company_symbols=symbols,
                        players=[self.name],
                        before={
                            'companies': {c.symbol: before_company},
                            'players': {self.name: before_player},
                        },
                        after={
                            'companies': {c.symbol: _snapshot_company(c)},
                            'players': {self.name: _snapshot_player(self, symbols)},
                        },
                        details={
                            'shares_bought': shares,
                            'purchase_price': c.share_price,
                        },
                    )
                
                # Refresh display so player sees updated portfolio and done with this company
                self.game.display.display_map(self)
                break





    @property
    def sorted_portfolio(self):
        return OrderedDict(sorted(self.portfolio.items()))



    def _valid_share_purchase(self, c, shares):
        return (c.share_price * shares) <= self.cash_on_hand


    @property
    def stock_value(self):
        stock_value = 0
        for company in self.portfolio.keys():
                stock_value += (self.portfolio[company] * self.game.active_companies[company].share_price)
        return stock_value

    @property
    def str_stock_value(self):
        return no_cents.sub('', (f'{locale.currency(self.stock_value, grouping=True)}'))

    @property
    def net_worth(self):
        return self.cash_on_hand + self.stock_value

    @property
    def str_cash_on_hand(self):
        return no_cents.sub('',(f'{locale.currency(self.cash_on_hand, grouping=True)}'))

    @property
    def str_net_worth(self):
        return no_cents.sub('', (f'{locale.currency(self.net_worth, grouping=True)}'))


class Company():
    '''
    Takes in stars and outpost on __init__ to calculate opening price
    Adds entry to game.active_companies dictionary and player portfolio, along with founders bonus
    Key = symbol, Value = company object itself
    '''

    def __init__(self, game, player, nsew):
        self.game = game
        self.founded_on = game.turn_number
        self.name = self._get_open_company_name(self.game)
        self.symbol = COMPANIES[self.name]
        self.share_price = STARTING_SHARE_PRICE
        #price_quantum calculates the minimum factor that company price should be (used in assert statments)
        self.price_quantum = STARTING_SHARE_PRICE
        self.apply_creation(nsew)
        player.portfolio[self.symbol] = FOUNDERS_BONUS_SHARES
        game.active_companies[self.symbol] = self
        game.active_companies.move_to_end(self.symbol)
        self.attach_square(nsew)
        self.game.display.display_new_company(self)
        self.game.display.any_to_continue()
        self.game.display.display_map(player)

    @property
    def outposts(self):
        return Counter(self.game.map.values())[self.symbol]


    def total_shares(self):
        return sum(
            p.portfolio.get(self.symbol, 0)
            for p in self.game.players
        )


    def apply_creation(self, nsew):
        """
        Apply all economic effects of founding this company.
        """
        if self.game.debug_econ:
            before_company = _snapshot_company(self)

        delta = self.creation_price_delta(nsew)
        self.apply_price_change(delta)

        if self.game.debug_econ:
            log_econ_event(
                turn_number=self.game.turn_number,
                event_type='company_creation',
                company_symbols=[self.symbol],
                before={
                    'companies': {self.symbol: before_company},
                },
                after={
                    'companies': {self.symbol: _snapshot_company(self)},
                },
                details={
                    'adjacent_stars': nsew.stars,
                    'adjacent_outposts': nsew.outposts,
                },
            )


    def apply_expansion(self, nsew):
        """
        Apply all economic effects of expanding this company by one square.
        """
        if self.game.debug_econ:
            before_company = _snapshot_company(self)

        delta = self.expansion_price_delta(nsew)
        self.apply_price_change(delta)

        if self.game.debug_econ:
            log_econ_event(
                turn_number=self.game.turn_number,
                event_type='company_expansion',
                company_symbols=[self.symbol],
                before={
                    'companies': {self.symbol: before_company},
                },
                after={
                    'companies': {self.symbol: _snapshot_company(self)},
                },
                details={
                    'adjacent_stars': nsew.stars,
                    'adjacent_outposts': nsew.outposts,
                },
            )

    def apply_merger(self, losing_company):
        """
        Apply all company-level economic effects of absorbing another company.
        Player-facing effects must already have been applied.
        """
        if self.game.debug_econ:
            before_companies = {
                self.symbol: _snapshot_company(self),
                losing_company.symbol: _snapshot_company(losing_company),
            }

        # Converge price quantum first
        self.price_quantum = min(self.price_quantum, losing_company.price_quantum)

        # Apply additive merger pricing
        self.apply_price_change(losing_company.share_price)

        if self.game.debug_econ:
            after_companies = {
                self.symbol: _snapshot_company(self),
                losing_company.symbol: _snapshot_company(losing_company),
            }
            log_econ_event(
                turn_number=self.game.turn_number,
                event_type='merger_company_effects',
                company_symbols=[self.symbol, losing_company.symbol],
                before={'companies': before_companies},
                after={'companies': after_companies},
            )


    def creation_price_delta(self, nsew) -> int:
        """
        Compute the share price delta for founding a new company.
        Includes:
        - base OUTPOST_BONUS for the founding square
        - OUTPOST_BONUS per adjacent outpost
        - STAR_BONUS per adjacent star
        """
        delta = OUTPOST_BONUS
        delta += nsew.outposts * OUTPOST_BONUS
        delta += nsew.stars * STAR_BONUS
        return delta

    def expansion_price_delta(self, nsew) -> int:
        """
        Compute the share price delta for expanding an existing company.
        Includes:
        - base OUTPOST_BONUS for the new square
        - OUTPOST_BONUS per absorbed outpost
        - STAR_BONUS per absorbed star
        """
        delta = OUTPOST_BONUS
        delta += nsew.outposts * OUTPOST_BONUS
        delta += nsew.stars * STAR_BONUS
        return delta

    
    def apply_price_change(self, delta: int):
        """
        Apply a pricing delta to the company, enforcing all economic rules:
        - additive price update
        - stock split detection and application
        - BASIC-style truncation to price_quantum
        - invariant enforcement
        """
        if delta == 0:
            return

        old_price = self.share_price

        # Apply the raw price change
        self.share_price += delta

        # Apply split logic if threshold crossed
        self._apply_split_if_needed(old_price)

        # BASIC-style truncation to price quantum
        self.share_price = (
            self.share_price // self.price_quantum
        ) * self.price_quantum

        # Economic invariant
        assert self.share_price % self.price_quantum == 0, (
            "Share price violates price quantum invariant"
        )

    def attach_square(self, nsew):
        '''Attach a square to the company's territory.'''
        self.game.map[nsew.center] = self.symbol
        for coord, tile in nsew.neighbors.items():
            if tile == OUTPOST:
                self.game.map[coord] = self.symbol


    def attach_square_without_pricing(self, nsew):
        """Attach merger connector square with no economic effects."""
        self.game.map[nsew.center] = self.symbol
        for coord, value in nsew.neighbors.items():
            if value == OUTPOST:
                self.game.map[coord] = self.symbol



    def apply_merger_player_effects(self, losing_company):

        """
        Handle *only* player-facing effects of a merger:
        - share conversion (2-for-1, rounded)
        - cash bonuses based on ownership percentage
        """

        if self.game.debug_econ:
            symbols = [self.symbol, losing_company.symbol]
            before_companies = {
                self.symbol: _snapshot_company(self),
                losing_company.symbol: _snapshot_company(losing_company),
            }
            before_players = {
                p.name: _snapshot_player(p, symbols)
                for p in self.game.players
            }

        total_old_shares = losing_company.total_shares()
        assert losing_company.share_price >= 100, \
            "Merger bonus computed with unexpectedly low share price"

        for p in self.game.players:
            old = p.portfolio.get(losing_company.symbol, 0)

            if total_old_shares > 0:
                # BASIC rule: merger cash bonus is 10× losing share price,
                # prorated by ownership and truncated to integer
                bonus = int(BASIC_MERGER_CASH_MULTIPLIER * (old / total_old_shares) * losing_company.share_price)
            else:
                bonus = 0

            p.portfolio[self.symbol] += int((old / 2) + 0.5)
            p.cash_on_hand += bonus
            p.old_data_for_display = bonus

        if self.game.debug_econ:
            after_players = {
                p.name: _snapshot_player(p, symbols)
                for p in self.game.players
            }
            after_companies = {
                self.symbol: _snapshot_company(self),
                losing_company.symbol: _snapshot_company(losing_company),
            }
            log_econ_event(
                turn_number=self.game.turn_number,
                event_type='merger_player_effects',
                company_symbols=symbols,
                players=[p.name for p in self.game.players],
                before={
                    'companies': before_companies,
                    'players': before_players,
                },
                after={
                    'companies': after_companies,
                    'players': after_players,
                },
                details={
                    'losing_total_shares': total_old_shares,
                    'bonus_multiplier': BASIC_MERGER_CASH_MULTIPLIER,
                },
            )


    def _apply_split_if_needed(self, previous_price):
        crossed = (
            previous_price < TWO_FOR_ONE_PRICE
            and self.share_price >= TWO_FOR_ONE_PRICE
        )

        if crossed:
            self.split_stock()

            # Safety invariant: cannot still be over threshold
            assert self.share_price < TWO_FOR_ONE_PRICE, \
                "Split did not reduce price below threshold"


    def split_stock(self):
        if self.game.debug_econ:
            symbols = [self.symbol]
            before_company = _snapshot_company(self)
            before_players = {
                p.name: _snapshot_player(p, symbols)
                for p in self.game.players
            }

        self.share_price //= 2
        self.price_quantum = max(1, self.price_quantum // 2)
        for p in self.game.players:
            p.old_data_for_display = p.portfolio[self.symbol]
            p.portfolio[self.symbol] *= 2

        if self.game.debug_econ:
            log_econ_event(
                turn_number=self.game.turn_number,
                event_type='stock_split',
                company_symbols=symbols,
                players=[p.name for p in self.game.players],
                before={
                    'companies': {self.symbol: before_company},
                    'players': before_players,
                },
                after={
                    'companies': {self.symbol: _snapshot_company(self)},
                    'players': {
                        p.name: _snapshot_player(p, symbols)
                        for p in self.game.players
                    },
                },
                details={
                    'split_ratio': '2:1',
                },
            )

        self.game.display.display_two_for_one(self)
        self.game.display.any_to_continue()

    @property
    def str_share_price(self):
        return no_cents.sub('', (locale.currency(self.share_price, grouping=True)))

    def _get_open_company_name(self, game):
        '''
        Get available companies by deducting active companies,
        and then return the min of the remaining set to stay in
        alphabetical order like the original. (Could shift to pop method to return
        companies in semi-random order.)
        '''
        active_cos = set()
        for c in self.game.active_companies.values():
            active_cos.add(c.name)
        open_names = set(COMPANIES.keys()).difference(active_cos)
        return min(open_names)


    def __eq__(self, other):
        return self.outposts == other.outposts
    def __ne__(self, other):
        return self.outposts !=other.outposts
    def __gt__(self, other):
        return self.outposts > other.outposts
    def __lt__(self, other):
        return self.outposts < other.outposts
    def __ge__(self, other):
        return self.outposts >= other.outposts
    def __le__(self, other):
        return self.outposts <= other.outposts

    def __repr__(self):
        return str(self.__dict__)


class Game():

    def __init__(self, number_of_players, terminal, max_turns, interactive=True, autopilot=False, headless = False, pause_at_end=True, monochrome=False, color_scheme=ColorScheme.DEFAULT, debug_econ=False, human_players=None, ai_difficulty='beginner', ai_difficulties=None, ai_thinking_mode='off'):
        self.turn_number = 1
        self.number_of_players = number_of_players
        self.display = Display(self, monochrome=monochrome, color_scheme=color_scheme)
        self.players = []
        self.terminal = terminal
        self.max_turns = max_turns
        self.last_action = None
        self.active_player = None
        self.headless = headless
        self.interactive = interactive
        self.autopilot = autopilot
        self.monochrome = monochrome
        self.color_scheme = color_scheme
        self.debug_econ = debug_econ
        self.pause_at_end = pause_at_end
        self.ai_difficulty = ai_difficulty
        self.ai_difficulties = list(ai_difficulties or [])
        self.ai_thinking_mode = self._normalize_ai_thinking_mode(ai_thinking_mode)
        self.ai_last_trace = None
        self.ai_last_trace_player = None
        self.ai_last_legal_moves = []
        self.ai_last_legal_moves_player = None
        self.ai_last_stock_reason = None
        self.ai_last_stock_reason_player = None
        self._first_player_announced = False

        if human_players is None:
            self.human_players = 0 if self.autopilot else self.number_of_players
        else:
            self.human_players = max(0, min(human_players, self.number_of_players))
        self.computer_players = self.number_of_players - self.human_players

        self._build_players()

        random.shuffle(self.players)
        self.map = Map()
        self.active_companies = collections.OrderedDict()

    def _normalize_ai_thinking_mode(self, mode):
        normalized = (mode or 'off').strip().lower()
        if normalized in ('off', 'summary', 'detailed'):
            return normalized
        return 'off'

    def _build_players(self):
        if self.interactive and not self.autopilot:
            resp = input("View instructions? (y/N): ").strip().upper()
            if resp == "Y":
                self.display.display_instructions()
                self.display.any_to_continue()

            # Clear instructions before player setup
            print(self.display._clear_screen())

            self._build_interactive_players()
            return

        self._build_noninteractive_players()

    def _build_interactive_players(self):
        for i in range(1, self.human_players + 1):
            print(f'Player {i}, what is your name? ', end='')
            p_name = input()
            self.players.append(Player(p_name, self, is_computer=False))

        for i in range(1, self.computer_players + 1):
            difficulty = self._ai_difficulty_for_computer(i)
            self.players.append(
                Player(
                    f'Computer {i}',
                    self,
                    is_computer=True,
                    ai_difficulty=difficulty,
                    ai_strategy=build_ai_strategy(difficulty),
                )
            )

    def _build_noninteractive_players(self):
        computer_counter = 0
        for i in range(1, self.number_of_players + 1):
            is_computer = self.autopilot or i > self.human_players
            label = 'Computer' if is_computer else 'Player'
            if is_computer:
                computer_counter += 1
                difficulty = self._ai_difficulty_for_computer(computer_counter)
                self.players.append(
                    Player(
                        f'{label} {computer_counter}',
                        self,
                        is_computer=True,
                        ai_difficulty=difficulty,
                        ai_strategy=build_ai_strategy(difficulty),
                    )
                )
            else:
                self.players.append(Player(f'{label} {i}', self, is_computer=False))

    def _ai_difficulty_for_computer(self, computer_index):
        list_index = computer_index - 1
        if list_index < len(self.ai_difficulties):
            return self.ai_difficulties[list_index]
        return self.ai_difficulty

    def choose_ai_move(self, player, legal_moves):
        self.ai_last_trace = None
        self.ai_last_trace_player = None
        self.ai_last_stock_reason = None
        self.ai_last_stock_reason_player = None
        strategy = player.ai_strategy or build_ai_strategy(player.ai_difficulty)
        capture_trace = self._should_show_ai_thinking(player)
        selected = strategy.choose_move(self, player, legal_moves, capture_trace=capture_trace)
        if capture_trace and self.ai_last_trace:
            self.ai_last_trace_player = player.name
        return selected

    def _should_show_ai_thinking(self, player):
        return self.ai_thinking_mode != 'off' and self._should_show_computer_turn_details(player)

    def _ai_summary_from_trace(self):
        if not self.ai_last_trace:
            return ''

        factors = self.ai_last_trace.get('selected_factors') or []
        if not factors:
            return ''
        return '; '.join(factors[:3])

    def execute_turn(self, player, autopilot=False):
        is_auto_turn = autopilot or player.is_computer
        show_computer_details = self._should_show_computer_turn_details(player)
        show_ai_thinking = self._should_show_ai_thinking(player)
        legal_moves = self._get_legal_moves(self.map)

        if show_ai_thinking and self.ai_thinking_mode == 'detailed':
            self.ai_last_legal_moves = list(legal_moves)
            self.ai_last_legal_moves_player = player.name

        if show_computer_details:
            legal = ", ".join(legal_moves)
            self.last_action = f"[COMPUTER TURN] {player.name} is thinking... options: {legal}"
            self.display.display_map(player)
            self.display.timed_pause(COMPUTER_THINK_DELAY_SECONDS)

        move = player.choose_move(legal_moves, is_auto_turn)

        self.play_move(player, move)

        self.pay_dividends(player)
        self.display.display_map(player)

        if self.active_companies:
            if is_auto_turn:
                purchase_clause = self._auto_buy_stocks(player, is_autopilot_turn=autopilot)
                if show_computer_details:
                    thinking_clause = ''
                    if show_ai_thinking:
                        summary = self._ai_summary_from_trace()
                        if summary:
                            thinking_clause = f" ({summary})"
                    self.last_action = f"[COMPUTER TURN] {player.name} played {move}{thinking_clause} and {purchase_clause}"
                    self.display.display_map(player)
                    self.display.any_to_continue(leading_blank=True)
            else:
                player.buy_stocks()
        elif show_computer_details:
            thinking_clause = ''
            if show_ai_thinking:
                summary = self._ai_summary_from_trace()
                if summary:
                    thinking_clause = f" ({summary})"
            self.last_action = f"[COMPUTER TURN] {player.name} played {move}{thinking_clause}."
            self.display.display_map(player)
            self.display.any_to_continue(leading_blank=True)

    def _auto_buy_stocks(self, player, is_autopilot_turn=False):
        before_cash = player.cash_on_hand
        before_portfolio = {
            symbol: player.portfolio.get(symbol, 0)
            for symbol in self.active_companies.keys()
        }
        strategy = player.ai_strategy or build_ai_strategy(player.ai_difficulty)

        if self._should_show_ai_thinking(player) and self.ai_thinking_mode == 'detailed':
            self.ai_last_stock_reason = self._build_stock_reason(strategy, player)
            self.ai_last_stock_reason_player = player.name

        strategy.buy_stocks(self, player)
        purchase_clause = self._summarize_auto_purchases(
            player,
            before_portfolio,
            before_cash,
        )
        label = "Autopilot" if is_autopilot_turn else player.name
        self.last_action = f"{label} {purchase_clause}"
        return purchase_clause

    def _build_stock_reason(self, strategy, player):
        strategy_name = (getattr(strategy, 'name', '') or '').lower()

        if strategy_name == 'beginner':
            active_count = len(self.active_companies)
            return (
                "Stock logic: beginner sweeps companies alphabetically, buying roughly half "
                "of affordable shares per company (cap 20), with no reserve optimization "
                f"across {active_count} active companies."
            )

        reserve = max(500, int(player.net_worth * 0.1))
        base_reason = (
            "Stock logic: score-ranked buys (dividend yield, expansion lanes, split proximity, "
            f"concentration control) while keeping about ${reserve:,} cash reserve."
        )

        ranker = getattr(strategy, '_rank_affordable_companies', None)
        if callable(ranker):
            try:
                ranked = ranker(self, player, reserve)
            except Exception:
                return base_reason

            if not ranked:
                return base_reason + " No company met affordability+reserve constraints this pass."

            top_targets = []
            for score, company in ranked[:3]:
                top_targets.append(f"{company.symbol}:{score:.0f}")

            return base_reason + f" Top targets before buys: {', '.join(top_targets)}."

        return base_reason

    def _summarize_auto_purchases(self, player, before_portfolio, before_cash):
        purchases = []
        for symbol in sorted(self.active_companies.keys()):
            before = before_portfolio.get(symbol, 0)
            after = player.portfolio.get(symbol, 0)
            bought = after - before
            if bought > 0:
                company_name = self.active_companies[symbol].name
                unit = "share" if bought == 1 else "shares"
                purchases.append(f"{bought} {unit} of {company_name}")

        if not purchases:
            return "skipped stock purchases"

        spent = int(before_cash - player.cash_on_hand)
        return f"bought {'; '.join(purchases)} (spent ${spent:,})"

    def _should_show_computer_turn_details(self, player):
        return (
            player.is_computer
            and self.interactive
            and not self.headless
            and self.human_players > 0
        )

    def _should_announce_first_player(self):
        return (
            self.interactive
            and not self.headless
            and self.human_players > 0
            and self.computer_players > 0
        )

    def _announce_first_player(self):
        first_player = self.players[0]
        self.display.display_announcement([
            'I will now decide who goes first.',
            BlankLine(),
            f'{first_player.name} goes first.',
        ])
        self.display.any_to_continue()

    def round(self):
        if (
            self.turn_number == 1
            and not self._first_player_announced
            and self._should_announce_first_player()
        ):
            self._announce_first_player()
            self._first_player_announced = True

        for player in self.players:
            self.active_player = player
            # last_action is scoped to the active player only
            self.last_action = None
            self.display.display_map(player)
            self.execute_turn(player, autopilot=self.autopilot)
        
        self.turn_number +=1
        if self.turn_number > self.max_turns:
            self.quit(confirm=False)

    def play_move(self, player, coordinate):
        '''
        Legal move is already confirmed, so we should be able to write it
        1. Get nsew for chosen move
        2. Check for empty space all around, if so make an outpost and move on
        3. If only one company adjacent to coordinate, add to that company
        4. If there are stars or outposts create a new company [if not already added to new company]
        5. Check for mergers and process those, then write the new symbol to the map
        '''


        nsew = self.map.nsew(coordinate)

        if self.is_isolated_space(nsew):
            self._resolve_isolated(coordinate)
            return

        if self.touches_multiple_companies(nsew):
            return self._resolve_merger(nsew)
        
        if self.touches_exactly_one_company(nsew):
            symbol = next(iter(nsew.companies))
            company = self.active_companies[symbol]     
            self._resolve_expansion(company, nsew)
            return
            
        if self.can_form_new_company(nsew):
            self._resolve_creation(player, nsew)
            return
        
        raise AssertionError("Unhandled move type.")

    def is_isolated_space(self, nsew):
        return not set(nsew.neighbors.values()).intersection(OCCUPIED_MAP_SYMBOLS)
    
    def can_form_new_company(self, nsew):
        """Return True if a move may form a new company."""
        return nsew.stars > 0 or nsew.outposts > 0

    def touches_exactly_one_company(self, nsew):
        return len(nsew.companies) == 1

    def touches_multiple_companies(self, nsew):
        return len(nsew.companies) > 1

    def _resolve_creation(self, player, nsew):
        Company(self, player, nsew)

    def _resolve_isolated(self, coordinate):
        self.map[coordinate] = OUTPOST

    def _resolve_expansion(self, company, nsew):
        company.attach_square(nsew)
        company.apply_expansion(nsew)   

    def _update_map_after_merger(self, surviving_company, losing_company):
        """
        Replace losing company symbols on the map with the surviving symbol.
        """
        self.map.replace_symbol(losing_company.symbol, surviving_company.symbol)

    def _retire_company(self, company):
        del self.active_companies[company.symbol]

        for p in self.players:
            if company.symbol in p.portfolio:
                del p.portfolio[company.symbol]

    def pay_dividends(self, player):
        total = 0

        if self.debug_econ:
            symbols = [company.symbol for company in self.active_companies.values()]
            before_companies = {
                symbol: _snapshot_company(self.active_companies[symbol])
                for symbol in symbols
            }
            before_player = _snapshot_player(player, symbols)
            dividends_by_company = {}

        for company in self.active_companies.values():
            shares = player.portfolio.get(company.symbol, 0)
            if shares > 0:
                dividend = int(
                    DIVIDEND_MULTIPLIER * shares * company.share_price
                )
                total += dividend
                if self.debug_econ:
                    dividends_by_company[company.symbol] = dividend

        player.cash_on_hand += total

        if self.debug_econ:
            after_companies = {
                symbol: _snapshot_company(self.active_companies[symbol])
                for symbol in symbols
            }
            log_econ_event(
                turn_number=self.turn_number,
                event_type='dividend_payout',
                company_symbols=symbols,
                players=[player.name],
                before={
                    'companies': before_companies,
                    'players': {player.name: before_player},
                },
                after={
                    'companies': after_companies,
                    'players': {
                        player.name: _snapshot_player(player, symbols)
                    },
                },
                details={
                    'total_dividend': total,
                    'dividend_by_company': dividends_by_company,
                },
            )

    def _apply_merger_player_effects(self, winner, loser):
        winner.apply_merger_player_effects(loser)

    def _apply_merger_company_effects(self, winner, loser):
        winner.apply_merger(loser)

    def _select_merger_pair(self, remaining_companies):
        # Larger company wins, but tie‑break by age if equal size
        companies = sorted(remaining_companies)
        loser = companies[0]
        winner = companies[1]

        # Tie‑break rule (age‑based dominance)
        if winner == loser and winner.founded_on > loser.founded_on:
            winner, loser = loser, winner

        return winner, loser

    def _execute_single_merger(self, winner, loser):
        """Execute one atomic merger of loser into winner."""

        # 1. Player-facing effects
        self._apply_merger_player_effects(winner, loser)

        # 2. Company-facing effects
        self._apply_merger_company_effects(winner, loser)

        # 3. Presentation
        self.display.display_merger(winner, loser)
        self.display.any_to_continue()

        # 4. Map + structural cleanup
        self._update_map_after_merger(winner, loser)
        self._retire_company(loser)

    def _resolve_merger(self, nsew):
        # Resolve one or more mergers triggered by this move, and return the surviving company.
        remaining_companies = [self.active_companies[c] for c in nsew.companies]

        while len(remaining_companies) > 1:
            winner, loser = self._select_merger_pair(remaining_companies)
            self._execute_single_merger(winner, loser)
            remaining_companies.remove(loser)
            
        surviving_company = remaining_companies[0]
        # Claim square that triggered the merger for the surviving company, but with no pricing effects (since merger pricing is handled in apply_merger and not attach_square)
        # This mirrors the original GW-BASIC rule.
        surviving_company.attach_square_without_pricing(nsew)
        return surviving_company

    def quit(self, confirm=True):
        """
        Ends the game.
        If confirm is True, ask the user to confirm before quitting.
        """
        if confirm:
            response = self.display.input_prompt("Hit 'Y' to confirm quit.").strip()
            if not response or response.upper()[0] != 'Y':
                return False

        self.display.display_end_of_game()

        if self.pause_at_end and not self.headless:
            print("Hit return/enter to quit.")
            input()
        
        sys.exit()

    def _get_legal_moves(self, game_map):
        '''
        If all companies already exist, insure no space that could create one is offered.
        If possible companies not maxed, then just return first MAX_MOVES.
        '''
        possible_moves = []
        legal_moves = game_map.empty_squares()
        random.shuffle(legal_moves)
        if len(legal_moves) < MAX_MOVES:
            self.quit(confirm = False)

        if len(self.active_companies) == len(COMPANIES):
            for c in legal_moves:
                if not self._check_company_creation(c, game_map):
                    possible_moves.append(c)
                if len(possible_moves) == MAX_MOVES:
                    return sorted(possible_moves)
        else:
            return sorted(legal_moves[:MAX_MOVES])

    def _check_company_creation(self, c, game_map):
        '''
        Returns TRUE if any coordinate around c will cause a company to form.
        Creation squares are those that touch stars/outposts
        but do NOT touch any existing company
        '''
        nsew = game_map.nsew(c)
        if nsew.companies:
            return False
        
        return nsew.stars > 0 or nsew.outposts > 0 

    def get_winner(self):
        d = {player.name: player.net_worth for player in self.players}
        winning_amount = max(d.values())
        winners = [k for k,v in d.items() if v == winning_amount]
        return winners

    def __repr__(self):
        d = {
            'map': len(self.map),
            'number_of_players': self.number_of_players,
            'player list': self.players,
            'turn_number': self.turn_number,
            'active company count': len(self.active_companies),
        }
        return(f'{d}')

class Map():
    '''
    Encapsulates map functions
    '''

    def __init__(self):
        self.map = {}
        self._generate_map()

    #Get and set values on the map using map[coord] notation, where coord is a string like 'G8'

    def __getitem__(self, coord):
        return self.map[coord]

    def __setitem__(self, coord, value):
        self.map[coord] = value

    def __len__(self):
        return len(self.map)
    
    def __iter__(self):
        return iter(self.map)

    def values(self):
        """Return all tile values on the map."""
        return self.map.values()

    def replace_symbol(self, old_symbol, new_symbol):
        """Replace all instances of old_symbol on the map with new_symbol."""
        self.map = {
            coord: new_symbol if tile == old_symbol else tile
            for coord, tile in self.map.items()
        }


    def empty_squares(self):
        """Return a list of coordinates for all empty squares on the map."""
        return [coord for coord, tile in self.map.items() if tile == EMPTY_SPACE]   

    def print_map(self):
        '''Print header row of letters, then each row in turn.'''
        print(f'{MAP_HEADER}')
        for row in ROW_LIST:
            print (f'{row}', end ='')
            for char in COL_LIST:
                print(f'{MAP_PRINT_SPACE}{self.map[char + row]}', end='')
            print()


    def nsew(self, center: str) -> Neighborhood:
        '''
        Given a map coordinate c, return the symbols that are North, South,
        East, and West of that coordinate, as well as counts of stars, outposts,
        empty space, and number of companies. Used for checking legal moves and
        for mergers.
        '''

        neighbors: dict[str, str] = {}
        stars = 0
        outposts = 0
        empty_space = 0
        companies: set[str] = set()

        for coord in self._get_orthogonal_coordinates(center):
            tile = self.map[coord]
            neighbors[coord] = tile

            kind = tile_kind_from_symbol(tile)

            if kind is TileKind.STAR:
                stars += 1
            elif kind is TileKind.OUTPOST:
                outposts += 1
            elif kind is TileKind.COMPANY:
                companies.add(tile)
        
        return Neighborhood(
            center=center,
            neighbors=neighbors,
            stars=stars,
            outposts=outposts,
            companies=companies,
        )

    def split_coordinate(self, c):
        '''returns tuple of column (letter) and row (number) for a given coord'''
        return (c[0], c[1])

    def get_indices(self, c):
        '''returns tuple of column (letter) and row (number) for a given coord'''
        return (COL_LIST.index(c[0]), ROW_LIST.index(c[1]))

    def _get_orthogonal_coordinates(self, c):
        '''Gets surrounding values for a given point on the map'''

        col_index, row_index = self.get_indices(c)
        vertical = self._get_coords(row_index, ROW_LIST, COL_LIST[col_index], prefix = True)
        horizontal = self._get_coords(col_index, COL_LIST, ROW_LIST[row_index], prefix = False)
        return vertical + horizontal

    def _get_coords(self, index, axis_list, col_or_row_value, prefix = True):
        ''' Gets coordinates above and below in list indices for map grid'''
        lower, upper = None, None
        if index - 1 >= 0:
            lower = axis_list[(index -1)]
        if index + 1 < len(axis_list):
            upper = axis_list[(index + 1)]
        results = (lower, upper)

        if prefix:
            return_vals = ["".join(f'{col_or_row_value}{r}') for r in results if r is not None]
        else:
            return_vals = ["".join(f'{r}{col_or_row_value}') for r in results if r is not None]
        return return_vals




    def _generate_map(self):
        for c in COL_LIST:
            for r in ROW_LIST:
                self.map[f'{c}{r}'] = self._get_random_map_point()

    def _get_random_map_point(self):
        # This will generate a roughly 5% star density (1/20, total number of tiles is 108, so about 5-6 stars per map on average).
        if randint(0,20) == 10:
            return STAR
        else:
            return EMPTY_SPACE

    def __repr__(self):
        return(f'{self.map}')


# -----------------------------------------------------------------------------
# Display Constants and Formatting Types
# -----------------------------------------------------------------------------

PORTFOLIO_SPACER = '  |  '
PORTFOLIO_UNDERSCORE = '_' * 22

PORTFOLIO_LABEL_WIDTH = 7
PORTFOLIO_QTY_WIDTH = 3
PORTFOLIO_AT = " @ "
PORTFOLIO_MONEY_WIDTH = 14

# Special announcement strings
SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL = '*'
SPECIAL_ANNOUNCEMENT_TOP_SYMBOL = '='
SPECIAL_ANNOUNCMENT_BOTTOM_SYMBOL = '='
SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE_SYMBOL = '-'
SPECIAL_ANNOUNCEMENT_LEFT_GUTTER = 1
SPECIAL_ANNOUNCEMENT_RIGHT_GUTTER = 3   # try 2 first; 3 if you want it looser

SPECIAL_ANNOUNCEMENT_WIDTH = 61
SPECIAL_ANNOUNCEMENT_TEXT_WIDTH = (
    SPECIAL_ANNOUNCEMENT_WIDTH
    - len(SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL) * 2
    - SPECIAL_ANNOUNCEMENT_LEFT_GUTTER
    - SPECIAL_ANNOUNCEMENT_RIGHT_GUTTER
)
SPECIAL_ANNOUNCEMENT_HEADER = SPECIAL_ANNOUNCEMENT_TOP_SYMBOL * SPECIAL_ANNOUNCEMENT_WIDTH
SPECIAL_ANNOUNCEMENT_FOOTER = SPECIAL_ANNOUNCMENT_BOTTOM_SYMBOL * SPECIAL_ANNOUNCEMENT_WIDTH

SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE = (
    SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE_SYMBOL
    * (SPECIAL_ANNOUNCEMENT_TEXT_WIDTH + 2)
)

SPECIAL_ANNOUNCEMENT_HEADER_LINE = 'SPECIAL ANNOUNCEMENT!!!'
SPECIAL_ANNOUNCEMENT_PLEASE_NOTE = 'Please note the following transactions:'

NEW_COMPANY_PHRASE = 'A new company has been formed!'

TWO_FOR_ONE_PHRASES = ['The stock of', 'has split 2:1!']
TWO_FOR_ONE_CATEGORIES = ['Player', 'Old Holdings', 'New Holdings']
TWO_FOR_ONE_COLUMNS = [
    'p.name[:TWO_FOR_ONE_PLAYER_NAME_LENGTH]',
    'str(p.old_data_for_display)',
    'str(p.portfolio[company.symbol])'
]

TWO_FOR_ONE_PLAYER_NAME_LENGTH = (SPECIAL_ANNOUNCEMENT_WIDTH - 2)//len(TWO_FOR_ONE_COLUMNS) - 1

MERGER_PHRASE = 'has just been merged into'
MERGER_CATEGORIES = ['Player', 'Old Stock', 'Total New', 'Bonus']
MERGER_COLUMNS = [
    'p.name[:MERGER_PLAYER_NAME_LENGTH]',
    'str(p.portfolio[losing_company.symbol])',
    'str(p.portfolio[company.symbol])',
    'locale.currency(p.old_data_for_display, grouping=True)'
]

MERGER_PLAYER_NAME_LENGTH = (SPECIAL_ANNOUNCEMENT_WIDTH - 2)//len(MERGER_COLUMNS) - 1

GAME_OVER_PHRASES = ['The game has ended!', 'Here are the standings:']
GAME_OVER_CATEGORIES = ['Player', 'Cash', 'Stocks', 'Net Worth']
GAME_OVER_COLUMNS = [
    'p.name[:GAME_OVER_PLAYER_NAME_LENGTH]',
    'p.str_cash_on_hand',
    'p.str_stock_value',
    'p.str_net_worth'
]
GAME_OVER_PLAYER_NAME_LENGTH = (SPECIAL_ANNOUNCEMENT_WIDTH - 2)//len(GAME_OVER_COLUMNS) - 1

STD_CAT_ALIGNMENT = ['c', 'r', 'r', 'r']


class AnnouncementLine:
    """Base class for lines in announcements."""
    pass


class ContentLine(AnnouncementLine):
    def __init__(self, text, alignment='c'):
        self.text = text
        self.alignment = alignment


class RuleLine(AnnouncementLine):
    """Horizontal rule inside announcements, separating content from player info."""
    pass


class BlankLine(AnnouncementLine):
    """Blank line inside announcements."""
    pass


class Display():
    '''
    Encapsulates display functions
    Eventually move this to blessings terminal manipulation
    Could later do a version for pygame
    '''

    def __init__(self, game, monochrome=False, color_scheme=ColorScheme.DEFAULT):
        self.game = game
        self.monochrome = monochrome
        self.color_scheme = color_scheme
        '''Lots more stuff here as display gets more complex'''

    @property
    def colors_enabled(self):
        return self.game.terminal.supports_color and not self.monochrome

    def _clear_screen(self):
        return self.game.terminal.clear()

    def company_color(self, symbol):
        return get_company_color(symbol, self.color_scheme)

    @staticmethod
    def _detect_decimal_column():
        probe = Display._format_company_row("X:", 0, "$0.00")
        return visible_len(probe[: probe.index(".")])

    @staticmethod
    def _money_decimal_column(row):
        if "." in row:
            return visible_len(row[: row.index(".")])
        return visible_len(row)

    @staticmethod
    def _format_company_row(label, qty, price):
        return (
            f'{PORTFOLIO_SPACER}'
            f'{label:>{PORTFOLIO_LABEL_WIDTH}} '
            f'{qty:>{PORTFOLIO_QTY_WIDTH}}'
            f'{PORTFOLIO_AT}'
            f'{price:>{PORTFOLIO_MONEY_WIDTH}}'
        )

    @staticmethod
    def _format_summary_row(label, price, decimal_column=None):
        prefix = f'{PORTFOLIO_SPACER}{label:>{PORTFOLIO_LABEL_WIDTH}}'

        if decimal_column is None:
            decimal_column = Display._detect_decimal_column()

        price_decimal = price.index(".") if "." in price else len(price)

        # Align the decimal point (or value end when no cents are present).
        pad = decimal_column - (visible_len(prefix) + price_decimal)

        return prefix + (" " * pad) + price


    def input_prompt(self, input_string = "> "):
        return input(input_string)

    def any_to_continue(self, leading_blank=False):
        if self.game.headless:
            return
        if leading_blank:
            print('')
        input('Press enter key to continue.')

    def timed_pause(self, seconds):
        if self.game.headless or not self.game.interactive:
            return
        time.sleep(max(0.0, seconds))

    def _wrapped_action_lines(self, action_text, wrap_width):
        wrapped = textwrap.wrap(
            action_text,
            width=wrap_width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        if len(wrapped) <= ACTION_STATUS_MAX_LINES:
            return wrapped

        kept = wrapped[: ACTION_STATUS_MAX_LINES - 1]
        overflow = " ".join(wrapped[ACTION_STATUS_MAX_LINES - 1 :])
        kept.append(textwrap.shorten(overflow, width=wrap_width, placeholder="..."))
        return kept

    def _build_ai_thinking_lines(self, player, wrap_width):
        if self.game.ai_thinking_mode != 'detailed':
            return []
        if not self.game.ai_last_trace:
            return []
        if self.game.ai_last_trace_player != player.name:
            return []

        trace = self.game.ai_last_trace
        strategy_name = trace.get('strategy', 'computer').title()
        selected_move = trace.get('selected_move', '?')
        ranked_moves = trace.get('ranked_moves', [])[:3]

        lines = [f"AI analysis ({strategy_name}): selected {selected_move}"]

        if self.game.ai_last_legal_moves_player == player.name and self.game.ai_last_legal_moves:
            options = ", ".join(self.game.ai_last_legal_moves)
            options_text = textwrap.shorten(
                f"Options offered: {options}",
                width=wrap_width,
                placeholder='...'
            )
            lines.append(options_text)

        for idx, candidate in enumerate(ranked_moves, start=1):
            factors = ', '.join(candidate.get('factors', [])[:2]) or 'no major factors'
            candidate_text = (
                f"{idx}. {candidate.get('move', '?')} score {candidate.get('score', 0):.0f} "
                f"| {factors}"
            )
            lines.append(textwrap.shorten(candidate_text, width=wrap_width, placeholder='...'))

        selected_components = trace.get('selected_components') or {}
        if selected_components:
            component_text = (
                f"base {selected_components.get('base_score', 0.0):.0f}, "
                f"net delta {selected_components.get('immediate_delta', 0.0):+.0f}, "
                f"opponent best {selected_components.get('opponent_best', 0.0):.0f}"
            )
            lines.append(textwrap.shorten(component_text, width=wrap_width, placeholder='...'))

        if self.game.ai_last_stock_reason_player == player.name and self.game.ai_last_stock_reason:
            lines.append(textwrap.shorten(self.game.ai_last_stock_reason, width=wrap_width, placeholder='...'))

        return lines


    def prompt_stock_purchase(self, company, player):
        '''Offer stock to purchase and prompt - return number of shares to buy'''
        term = self.game.terminal
        print(f'')

        if self.colors_enabled:
            company_name = term.color(company.name, fg=self.company_color(company.symbol))
        else:
            company_name = company.name
       
        print(
            f'Purchase how many shares of {company_name} '
            f'at {company.str_share_price} per share?'
        )
        
        print(f'Cash on hand: {player.str_cash_on_hand} ', end = '')
        print(f'Max possible: {int(player.cash_on_hand // company.share_price)}, ', end = '')
        print(f'Current holdings: {player.portfolio[company.symbol]}')
        return self.input_prompt()


    def display_announcement (self, lines, player_info = None, company = None, losing_company = None, alignment = 'c'):
        print(self._clear_screen())
        self._print_announcement_header()
        
        for line in lines:
            if isinstance(line, RuleLine):
                self._print_rule()
            elif isinstance(line, BlankLine):
                self._print_blank()
            elif isinstance(line, ContentLine):
                self._print(line.text, alignment=line.alignment)
            elif type(line) == list:
                self._print(data=line[0], alignment=line[1])
            else:
                self._print(line)

        if player_info:
            self._print_player_info(columns = player_info,
                                    company = company,
                                    losing_company = losing_company,
                                    alignment = alignment
                                )
        self._print_announcement_footer()


    
    def _print_rule(self):
        print(f'{SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL} ' f'{SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE}' f' {SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL}')


    def _print_blank(self):
        self._print('')


    def display_new_company(self, company):
        term = self.game.terminal
        plain_name = company.name
        centered_name = self._apply_display_alignment(plain_name, alignment = 'c')
        if self.colors_enabled:
            formatted_name = centered_name.replace(plain_name, term.color(plain_name, fg=self.company_color(company.symbol)), 1)
        else:
            formatted_name = centered_name
        self.display_announcement([
                                NEW_COMPANY_PHRASE,
                                formatted_name,
                                BlankLine(),
                                f'Opening Price: {company.str_share_price}'
                ]
            )


    def display_two_for_one(self, company):
        term = self.game.terminal
        plain_company = company.name.upper()

        centered_company = self._apply_display_alignment(plain_company, alignment = 'c')

        if self.colors_enabled:
            centered_company = centered_company.replace(plain_company, term.color(plain_company, fg=self.company_color(company.symbol)), 1)

        self.display_announcement([
                                TWO_FOR_ONE_PHRASES[0],
                                centered_company,
                                TWO_FOR_ONE_PHRASES[1],
                                BlankLine(),
                                SPECIAL_ANNOUNCEMENT_PLEASE_NOTE,
                                RuleLine(),
                                [TWO_FOR_ONE_CATEGORIES, STD_CAT_ALIGNMENT]
                ], TWO_FOR_ONE_COLUMNS, company = company, alignment = STD_CAT_ALIGNMENT
            )

    def display_merger(self, company, losing_company):
        term = self.game.terminal
        plain_winner = company.name
        plain_loser = losing_company.name

        centered_winner = self._apply_display_alignment(plain_winner, alignment = 'c')
        centered_loser = self._apply_display_alignment(plain_loser, alignment = 'c')

        if self.colors_enabled:
            centered_winner = centered_winner.replace(plain_winner, term.color(plain_winner, fg=self.company_color(company.symbol)), 1)
            centered_loser = centered_loser.replace(plain_loser, term.color(plain_loser, fg=self.company_color(losing_company.symbol)), 1)

        self.display_announcement([
                                centered_loser,
                                BlankLine(),
                                MERGER_PHRASE,
                                BlankLine(),
                                centered_winner,
                                BlankLine(),
                                SPECIAL_ANNOUNCEMENT_PLEASE_NOTE,
                                RuleLine(),
                                [MERGER_CATEGORIES, STD_CAT_ALIGNMENT]
                ], MERGER_COLUMNS, company = company, losing_company = losing_company,
                    alignment = STD_CAT_ALIGNMENT
            )


    def build_portfolio_for_map(self, player):
        '''Build mini portfolio lines shown beside the map for the given player.'''
        term = self.game.terminal
        portfolio_lines = []
        summary_decimal_column = None

        for symbol in sorted(self.game.active_companies.keys()):
            company = self.game.active_companies[symbol]

            if self.colors_enabled and symbol in COMPANY_SYMBOLS:
                label = term.color(symbol, fg=self.company_color(symbol)) + ":"
            else:
                label = symbol + ":"

            price = locale.currency(company.share_price, grouping=True)
            company_row = self._format_company_row(label, player.portfolio[symbol], price)

            if summary_decimal_column is None:
                summary_decimal_column = self._money_decimal_column(company_row)

            portfolio_lines.append(company_row)

        if summary_decimal_column is None:
            summary_decimal_column = self._detect_decimal_column()

        label = "Stocks:"
        price = locale.currency(player.stock_value, grouping=True)
        portfolio_lines.append(self._format_summary_row(label, price, summary_decimal_column))

        label = "Cash:"
        price = locale.currency(player.cash_on_hand, grouping=True)
        portfolio_lines.append(self._format_summary_row(label, price, summary_decimal_column))

        portfolio_lines.append(f'{PORTFOLIO_SPACER}{PORTFOLIO_UNDERSCORE}')

        label = "Total:"
        price = locale.currency(player.net_worth, grouping=True)
        portfolio_lines.append(self._format_summary_row(label, price, summary_decimal_column))

        while len(portfolio_lines) < len(ROW_LIST):
            portfolio_lines.append(f'{PORTFOLIO_SPACER}')

        return portfolio_lines


    def display_map(self, player):
        '''Print map and mini portfolio for standard turn.'''
        term = self.game.terminal
        player_portfolio = self.build_portfolio_for_map(player)
        map = self.game.map
        print(self._clear_screen())
        turn_line = (
            f"Turn {self.game.turn_number} of {self.game.max_turns} — "
            f"{self.game.active_player.name}'s turn"
        )
        print(turn_line.center(MAP_WIDTH))
        print(f'{("-"*MAP_WIDTH).center(MAP_WIDTH)}')
        portfolio_header = f'*** {self.game.active_player.name}\'s Portfolio ***'
        header = MAP_HEADER + PORTFOLIO_SPACER + portfolio_header
        status_width = visible_len(header)
        print(header)

        for row_num,row in enumerate(ROW_LIST):
            print (f'{row}', end ='')
            for char in COL_LIST:
                symbol = map[char + row]
                if symbol in COMPANY_SYMBOLS and self.colors_enabled:
                    rendered = term.color(symbol, fg=self.company_color(symbol))
                else:
                    rendered = symbol
                print(f'{MAP_PRINT_SPACE}{rendered}', end='')

            print(f'{player_portfolio[row_num]}')
        print(f' ')
        if self.game.last_action:
            for line in self._wrapped_action_lines(self.game.last_action, status_width):
                print(line.ljust(status_width))

        ai_lines = self._build_ai_thinking_lines(player, status_width)
        if ai_lines:
            print('')
            for line in ai_lines:
                print(line.ljust(status_width))

    def display_end_of_game(self):
        '''Final display'''
        self.display_announcement([
                                GAME_OVER_PHRASES[0],
                                self._get_winner_string(),
                                BlankLine(),
                                GAME_OVER_PHRASES[1],
                                RuleLine(),
                                [GAME_OVER_CATEGORIES, STD_CAT_ALIGNMENT]
                ], player_info = GAME_OVER_COLUMNS, alignment = STD_CAT_ALIGNMENT
            )


    def _print_player_info(self, columns, company = '', losing_company = '', alignment = 'c'):
        '''Iterates through players and prints announcement-specific data.
            The columns variable is linked to list constants that have the
            specific calls (e.g p.name) as strings to be evaled by
            the routine. Cleaner than a messy if statement...'''
        for p in self.game.players:
            c = []
            for col in columns:
                c.append(eval(col))
            self._print(c, alignment)


    def _get_winner_string(self):
        winners = self.game.get_winner()
        if len(winners) == 1:
            return (f'{winners[0].upper()} has won!')
        else:
            return (f'{" and ".join(winners).upper()} have tied!')



    def _print_announcement_header(self):
        print(f'{SPECIAL_ANNOUNCEMENT_HEADER}')
        self._print(SPECIAL_ANNOUNCEMENT_HEADER_LINE)
        self._print('')


    def _print_announcement_footer(self):
        print(f'{SPECIAL_ANNOUNCEMENT_FOOTER}')
        print(f'')


    def _print(self, data = [" "], alignment = 'c'):
        '''Prints line with special announcement symbol at each side '''
        if type(data) == list:
            line = self._create_columns_line(data, alignment)
        else:
            line = self._apply_display_alignment(data, alignment)
        print(
            f'{SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL}'
            f'{" " * SPECIAL_ANNOUNCEMENT_LEFT_GUTTER}'
            f'{line}'
            f'{" " * SPECIAL_ANNOUNCEMENT_RIGHT_GUTTER}'    
            f'{SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL}'
            )


    def _create_columns_line(self, columns, alignments):
        
        """
        Given list of strings to align, returns single line with appropriate spacing.
        Ensures total visible width equals SPECIAL_ANNOUNCEMENT_TEXT_WIDTH, with spacing for borders.
        """
        
        num_cols = len(columns)
        usable_width = SPECIAL_ANNOUNCEMENT_TEXT_WIDTH
        base_width = usable_width // num_cols
        remainder = usable_width - (base_width * num_cols)


        result = ""

        for index, text in enumerate(columns):
            # Last column gets the remainder
            col_width = base_width + (remainder if index == num_cols - 1 else 0)

            result += self._apply_display_alignment(
                text,
                alignment=alignments[index] if len(alignments) > index else 'c',
                col_width=col_width
            )
        return result



    def _apply_display_alignment(self, text, alignment = '', col_width = SPECIAL_ANNOUNCEMENT_TEXT_WIDTH):

        vis_len = visible_len(text)
        pad = max(0, col_width - vis_len)

        
        if alignment == 'r':
            return ' ' * pad + text
        elif alignment == 'l':
            return text + ' ' * pad
        else:
            left = pad // 2
            right = pad - left
            return ' ' * left + text + ' ' * right

        



    
    def display_paged_paragraphs(self, paragraphs, margin=3):
        """
        Display text one page at a time, keeping paragraphs intact.
        Only call when game.interactive is True.
        """
        _, rows = shutil.get_terminal_size(fallback=(80, 24))
        max_lines = max(5, rows - margin)

        current_page = []
        current_count = 0

        for para in paragraphs:
            para_height = len(para) + 1  # +1 for spacing between paragraphs

            # If paragraph won't fit on this page, show page first
            if current_page and current_count + para_height > max_lines:
                print(self._clear_screen())
                for line in current_page:
                    print(line)
                if self.game.interactive:
                    input("\n(Press Enter to continue)")
                current_page = []
                current_count = 0

            # Add paragraph
            current_page.extend(para)
            current_page.append("")  # blank line between paragraphs
            current_count += para_height

        # Print final page
        if current_page:
            print(self._clear_screen())
            for line in current_page:
                print(line)

    

    def display_instructions(self):
        self.display_paged_paragraphs(INSTRUCTION_PARAGRAPHS)



INSTRUCTION_PARAGRAPHS = [
    [
        "STAR LANES",
        "",
        "STAR LANES IS A GAME OF INTERSTELLAR TRADING.",
        "THE OBJECT OF THE GAME IS TO AMASS THE GREATEST NET WORTH",
        "BY ESTABLISHING SHIPPING LANES AND PURCHASING STOCK.",
    ],
    [
        "THE GAME IS PLAYED ON A 9 X 12 MAP (ROWS 1–9, COLUMNS A–L).",
        "EACH TURN, FIVE POSSIBLE SPACES ARE OFFERED.",
        "",
        "TO MAKE A MOVE, ENTER THE ROW AND COLUMN (E.G. 7E, 8A).",
    ],
    [
        "THERE ARE FOUR TYPES OF MOVES:",
    ],
    [
        "1. ESTABLISH AN UNATTACHED OUTPOST",
        "   PLAY A SPACE NOT ADJACENT TO A STAR, OUTPOST, OR COMPANY.",
    ],
    [
        "2. EXPAND AN EXISTING SHIPPING LANE",
        "   PLAY A SPACE ADJACENT TO EXACTLY ONE COMPANY.",
        "   EACH NEW SQUARE ADDS $100 PER SHARE.",
        "   EACH ADJACENT STAR ADDS $500 PER SHARE.",
    ],
    [
        "3. ESTABLISH A NEW SHIPPING LANE",
        "   IF FEWER THAN FIVE COMPANIES EXIST, A NEW COMPANY",
        "   MAY BE CREATED ADJACENT TO A STAR OR OUTPOST.",
        "   THE PLAYER RECEIVES 5 SHARES IN THE NEW COMPANY.",
    ],
    [
        "4. MERGE TWO COMPANIES",
        "   PLAYING A SPACE ADJACENT TO TWO COMPANIES CAUSES A MERGER.",
        "   THE LARGER COMPANY SURVIVES; TIES ARE BROKEN BY AGE.",
        "   STOCK IS CONVERTED 2 FOR 1 AND CASH BONUSES ARE PAID.",
    ],
    [
        "AFTER EACH MOVE:",
        "• DIVIDENDS ARE PAID AT 5% OF STOCK VALUE.",
        "• THE PLAYER MAY PURCHASE STOCK.",
    ],
    [
        "STOCK CANNOT BE SOLD.",
        "",
        "IF A SHARE PRICE EXCEEDS $3000, THE STOCK SPLITS 2 FOR 1.",
    ],
    [
        "THE MAP AND YOUR PORTFOLIO ARE ALWAYS DISPLAYED.",
        "PRESS ENTER TO SKIP A STOCK PURCHASE.",
        "",
        "THE GAME ENDS AFTER THE FINAL TURN.",
        "THE PLAYER WITH THE GREATEST NET WORTH WINS.",
    ],
]