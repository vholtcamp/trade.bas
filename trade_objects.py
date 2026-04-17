
import collections
from collections import defaultdict, Counter, OrderedDict
import sys
import locale
locale.setlocale(locale.LC_ALL, '')

import random
from random import randint

import re
no_cents = re.compile(r'.00$')

import logging
logging.basicConfig(filename='app.log', filemode='w', level = logging.DEBUG,
                    format='%(name)s - %(levelname)s - %(message)s')


# FIXME - Remove seed for game play
random.seed(10)

# CONSTANTS

COL_LIST = list('ABCDEFGHILKL')
ROW_LIST = list('123456789')

MAP_PRINT_SPACE = '  '

STAR = '*'
OUTPOST = '+'
EMPTY_SPACE = '.'
MAX_MOVES = 5
MAX_PLAYERS = 4

STARTING_CASH = 500
STARTING_SHARE_PRICE = 100
OUTPOST_BONUS = 100
STAR_BONUS = 500
FOUNDERS_BONUS_SHARES = 5
TWO_FOR_ONE_PRICE = 3000
DIVIDEND_MULTIPLIER = 0.05
MERGER_BONUS = 10

CURRENCY_SYMBOL = '$'
CURRENCY_SEPARATOR = ','

MAP_HEADER = f' {MAP_PRINT_SPACE}{MAP_PRINT_SPACE.join(COL_LIST)}'
MAP_WIDTH = len(MAP_HEADER) + len(MAP_PRINT_SPACE)
MINI_PORTFOLIO_HEADER = '***   PORTFOLIO    ***'
MINI_PORTFOLIO_SPACER = '  |  '
MAIN_DISPLAY_HEADER = MAP_HEADER + MINI_PORTFOLIO_SPACER + MINI_PORTFOLIO_HEADER
MINI_PORTFOLIO_UNDERSCORE = '_' * 22

# Special Announcement Strings

SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL = '*'
SPECIAL_ANNOUNCEMENT_TOP_SYMBOL = '='
SPECIAL_ANNOUNCMENT_BOTTOM_SYMBOL = '='
SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE_SYMBOL = '-'
SPECIAL_ANNOUNCEMENT_WIDTH = 61
SPECIAL_ANNOUNCEMENT_TEXT_WIDTH = SPECIAL_ANNOUNCEMENT_WIDTH - len(SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL) * 2

SPECIAL_ANNOUNCEMENT_HEADER = SPECIAL_ANNOUNCEMENT_TOP_SYMBOL * SPECIAL_ANNOUNCEMENT_WIDTH
SPECIAL_ANNOUNCEMENT_FOOTER = SPECIAL_ANNOUNCMENT_BOTTOM_SYMBOL * SPECIAL_ANNOUNCEMENT_WIDTH
SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE = (SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE_SYMBOL * (SPECIAL_ANNOUNCEMENT_TEXT_WIDTH - 2))

SPECIAL_ANNOUNCEMENT_HEADER_LINE = 'SPECIAL ANNOUNCEMENT!!!'
SPECIAL_ANNOUNCEMENT_PLEASE_NOTE = 'Please note the following transactions:'

NEW_COMPANY_PHRASE = 'A new company has been formed!'

TWO_FOR_ONE_PHRASES = ['The stock of', 'has split 2:1!']
TWO_FOR_ONE_CATEGORIES = ['Player', 'Old Holdings', 'New Holdings']
TWO_FOR_ONE_COLUMNS = ['p.name[:TWO_FOR_ONE_PLAYER_NAME_LENGTH]',
                       'str(p.old_data_for_display)',
                       'str(p.portfolio[company.symbol])'
                    ]

TWO_FOR_ONE_PLAYER_NAME_LENGTH = (SPECIAL_ANNOUNCEMENT_WIDTH - 2)//len(TWO_FOR_ONE_COLUMNS) - 1


MERGER_PHRASE = 'has just merged with'
MERGER_CATEGORIES = ['Player', 'Old Stock', 'New Stock', 'Bonus']
MERGER_COLUMNS = ['p.name[:MERGER_PLAYER_NAME_LENGTH]',
                  'str(p.portfolio[losing_company.symbol])',
                  'str(p.portfolio[company.symbol])',
                  'locale.currency(p.old_data_for_display, grouping=True)'
                ]

MERGER_PLAYER_NAME_LENGTH = (SPECIAL_ANNOUNCEMENT_WIDTH - 2)//len(MERGER_COLUMNS) - 1

GAME_OVER_PHRASES = ['The game has ended!', 'Here are the standings:']
GAME_OVER_CATEGORIES = ['Player', 'Cash', 'Stocks', 'Net Worth']
GAME_OVER_COLUMNS = ['p.name[:GAME_OVER_PLAYER_NAME_LENGTH]',
                     'p.str_cash_on_hand',
                    'p.str_stock_value',
                    'p.str_net_worth'
                ]
GAME_OVER_PLAYER_NAME_LENGTH = (SPECIAL_ANNOUNCEMENT_WIDTH - 2)//len(GAME_OVER_COLUMNS) - 1

STD_CAT_ALIGNMENT = ['c', 'r', 'r', 'r']

TICKER_HEADER = '- S t o c k   T i c k e r --- S t o c k   T i c k e r  -'

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
COMMANDS = ('M', 'S', 'Q') # -- map, stock portfolio, quit


class Player():
    '''
    Player manages cash and portfolio, and also has "take_turn" method
    consisting of making a move and then buying stocks.
    Portfolio dictionary has key of company symbol and value of # of shares, set to
    a defaultdict (int) so that 0 will always be returned.
    '''

    def __init__(self, name, game):
        # TODO - Input values for names
        self.name = name
        self.cash_on_hand = float(STARTING_CASH)
        self.portfolio = defaultdict(int)
        self.game = game
        self.old_data_for_display = 0


    def take_turn(self, legal_moves):
        # get user choice & confirm user chose one of offered moves or COMMANDS
        while True:
            print(f'{self.name}, choose a move from: {legal_moves}')
            # move = self.display.input_prompt().upper()
            # FIXME - Take game off autopilot!
            move = legal_moves[0]
            print(f'Taking move: {move}')
            if self.game.player_move(self, legal_moves, move):
                self.game.last_move = move
                break
        self.game.pay_dividends(self)
        if len(self.game.active_companies) > 0:
            self.buy_stocks()


    def buy_stocks(self):
        '''
        Loop through all active companies and let player buy stock. Update
        portfolio and cash_on_hand as needed. Blank entry converted to zero.
        '''
        self.game.display.display_ticker()
        for c in self.game.active_companies.values():
            while c.share_price < self.cash_on_hand:
                shares = str(self.game.display.prompt_stock_purchase(c, self))
                if shares.upper() in COMMANDS:
                    self.run_player_command(shares)
                else:
                    shares = (int(shares) if shares.isdecimal() else 0)
                    if self._valid_share_purchase(c, shares):
                        self.portfolio[c.symbol] += shares
                        self.cash_on_hand -= (shares * c.share_price)
                        break


    def run_player_command(self, command):
        if command.upper() == 'P':
            self.game.display.display_portfolio(self)
        elif command.upper() == 'M':
            self.game.display.display_map(self.portfolio_for_map)
        elif command.upper() == 'Q':
            self.game.quit()


    @property
    def sorted_portfolio(self):
        return OrderedDict(sorted(self.portfolio.items()))

    @property
    def portfolio_for_map(self):
        '''
        Returns 9 line portfolio matching main display requirements:
            A:  20 @    $200
            B:  10 @    $500
            C:   0 @  $1,000
            D: 100 @  $2,990
            E:   0 @  $1,000
         Stocks:     $10,000
         Cash:      $115,000
         ___________________
         Total:   $1,111,111
        '''
        s, c, t, p = 'Stocks:', 'Cash:', 'Total:', []
        for k in self.game.active_companies.keys():
            p.append(f'{MINI_PORTFOLIO_SPACER}{k:>4}: {self.portfolio[k]:>3} @ {locale.currency(self.game.active_companies[k].share_price, grouping=True):>10}')
        p.append(f'{MINI_PORTFOLIO_SPACER}{s:>6} {locale.currency(self.stock_value, grouping=True):>14}')
        p.append(f'{MINI_PORTFOLIO_SPACER}{c:>7} {locale.currency(self.cash_on_hand, grouping=True):>14}')
        p.append(f'{MINI_PORTFOLIO_SPACER}{MINI_PORTFOLIO_UNDERSCORE}')
        p.append(f'{MINI_PORTFOLIO_SPACER}{t:>6} {locale.currency(self.net_worth, grouping=True):>15}')

        for i in range(0, (len(ROW_LIST) - len(p))):
            p.append(f'{MINI_PORTFOLIO_SPACER}')
        return p



    def _valid_share_purchase(self, c, shares):
        '''
        Check for valid entry for number of shares as well as
        ability to cover the puchase given the player's cash on hand.
        '''
        if (c.share_price * shares) > self.cash_on_hand:
            print(f'You do not have enough money to cover that purchase.')
            return False
        return True


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
        old_price = self.share_price
        self.share_price += self.calculate_price_delta(nsew, is_new_company=True)
        self.check_for_split(old_price)
        player.portfolio[self.symbol] = FOUNDERS_BONUS_SHARES
        game.active_companies[self.symbol] = self
        game.active_companies.move_to_end(self.symbol)
        self.add_outpost(nsew)
        self.game.display.display_new_company(self)
        self.game.display.any_to_continue()
        self.game.display.display_map(player.portfolio_for_map)
        assert self.share_price % 100 == 0, "Share price should always be a multiple of $100"

    @property
    def outposts(self):
        return Counter(self.game.map.map.values())[self.symbol]


    def total_shares(self):
        return sum(
            p.portfolio.get(self.symbol, 0)
            for p in self.game.players
        )

    def calculate_price_delta(self, nsew, *, is_new_company=False):
        delta = 0

        # Center square
        if is_new_company:
            delta += OUTPOST_BONUS

        # Adjacent absorbed features
        delta += nsew['outposts'] * OUTPOST_BONUS
        delta += nsew['stars'] * STAR_BONUS

        return delta


    def add_outpost(self, nsew):
        '''update map and share price based on stars/outposts'''
        self.game.map.map[nsew['center']] = self.symbol
        # TODO - Might be a smoother, more pythonic way, to do this loop...
        for k, v in nsew['coordinates'].items():
            if v == OUTPOST:
                self.game.map.map[k] = self.symbol


    def merge_players(self, losing_company):

        """
        Handle *only* player-facing effects of a merger:
        - share conversion (2-for-1, rounded)
        - cash bonuses based on ownership percentage
        """

        total_old_shares = losing_company.total_shares()

        for p in self.game.players:
            old = p.portfolio.get(losing_company.symbol, 0)

            if total_old_shares > 0:
                bonus = MERGER_BONUS * (old / total_old_shares) * losing_company.share_price
            else:
                bonus = 0

            p.portfolio[self.symbol] += int((old / 2) + 0.5)
            p.cash_on_hand += bonus
            p.old_data_for_display = bonus



    def shares(self):
        total = 0
        for p in self.game.players():
            total += p.portfolio[self.name]
        return total


    def check_for_split(self, previous_price):
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
        self.share_price /= 2
        for p in self.game.players:
            p.old_data_for_display = p.portfolio[self.symbol]
            p.portfolio[self.symbol] *= 2
        self.game.display.display_two_for_one(self)
        self.game.display.any_to_continue()



    def _retire_company(self, company):
        del self.active_companies[company.symbol]

        for p in self.players:
            if company.symbol in p.portfolio:
                del p.portfolio[company.symbol]


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

    def __init__(self, number_of_players, terminal, max_turns):
        self.turn_number = 1
        self.number_of_players = number_of_players
        self.display = Display(self)
        self.players = []
        self.terminal = terminal
        self.max_turns = max_turns
        self.last_move = ''
        self.active_player = ''


        # FIXME - Uncomment after testing
        # for i in range(1, number_of_players + 1):
        #     print(f'Player {i}, what is your name? ', end = '')
        #     p_name = input()
        #     p = Player(p_name, self)
        #     self.players.append(p)
        self.players.append(Player('Victor', self))
        self.players.append(Player('Theo', self))
        random.shuffle(self.players)
        self.map = Map()
        self.active_companies = collections.OrderedDict()

    def round(self):
        for p in self.players:
            self.active_player = p
            self.display.display_map(p.portfolio_for_map)
            p.take_turn(self._get_legal_moves(self.map))
        self.turn_number +=1

    def player_move(self, player, legal_moves, move):
            if move in legal_moves:
                self.play_move(player, move)
                self.display.display_map(player.portfolio_for_map, last_move = self.last_move)
                return True
            elif len(move) > 0 and move[0] in COMMANDS:
                self.player.run_player_command(move[0])
            return False


    def is_isolated_space(self, nsew):
        return not set(nsew['coordinates'].values()).intersection(OCCUPIED_MAP_SYMBOLS)

    def touches_exactly_one_company(self, nsew):
        return len(nsew['companies']) == 1

    def touches_multiple_companies(self, nsew):
        return len(nsew['companies']) > 1

    def can_form_new_company(self, nsew):
        return nsew['stars'] > 0 or nsew['outposts'] > 0

    def _place_outpost(self, coordinate):
        self.map.map[coordinate] = OUTPOST

    def _expand_company(self, company, nsew):
        # Mutate map only
        company.add_outpost(nsew)
        old_price = company.share_price
        company.share_price += company.calculate_price_delta(
            nsew, is_new_company=False
        )

        company.check_for_split(old_price)

        assert company.share_price % 100 == 0, \
            "Share price should always be a multiple of $100"

    def _apply_merger_pricing(self, surviving_company, losing_company):
        """
        Apply company-level pricing effects of a merger.
        """
        old_price = surviving_company.share_price
        surviving_company.share_price += losing_company.share_price
        surviving_company.check_for_split(old_price)

        assert surviving_company.share_price % 100 == 0, \
            "Share price should always be a multiple of $100"

    def _resolve_merger(self, player, nsew):
        return self.merger(nsew)

    def _update_map_after_merger(self, surviving_company, losing_company):
        """
        Replace losing company symbols on the map with the surviving symbol.
        """
        self.map.map = {
            coord: surviving_company.symbol if tile == losing_company.symbol else tile
            for coord, tile in self.map.map.items()
        }

    def _retire_company(self, company):
        del self.active_companies[company.symbol]

        for p in self.players:
            if company.symbol in p.portfolio:
                del p.portfolio[company.symbol]

    def pay_dividends(self, player):
        total = 0

        for company in self.active_companies.values():
            shares = player.portfolio.get(company.symbol, 0)
            if shares > 0:
                dividend = int(
                    DIVIDEND_MULTIPLIER * shares * company.share_price
                )
                total += dividend

        player.cash_on_hand += total

    def play_move(self, player, coordinate):
        '''
        Legal move is already confirmed, so we should be able to write it
        1. Get nsew for chosen move
        2. Check for empty space all around, if so make an outpost and move on
        3. If only one company adjacent to coordinate, add to that company
        4. If there are stars or outposts create a new company
        5. Check for mergers and process those, then write the new symbol to the map
        '''


        nsew = self.map.nsew(coordinate)

        if self.is_isolated_space(nsew):
            self._place_outpost(coordinate)
            return

        if self.touches_multiple_companies(nsew):
            surviving_company = self._resolve_merger(player, nsew)
            surviving_company.add_outpost(nsew)
            return
        
        if self.can_form_new_company(nsew):
            Company(self, player, nsew)
            return
        
        if self.touches_exactly_one_company(nsew):
            symbol = next(iter(nsew['companies']))
            company = self.active_companies[symbol]     
            self._expand_company(company, nsew)
            return

        assert self.map.map[coordinate] != EMPTY_SPACE


    def merger(self, nsew):
        merging_companies = [self.active_companies[c] for c in nsew['companies']]

        while len(merging_companies) > 1:
            merging_companies.sort()
            loser = merging_companies.pop(0)
            winner = merging_companies.pop(0)

            # Tie‑break rule (age‑based dominance)
            if winner == loser and winner.founded_on > loser.founded_on:
                winner, loser = loser, winner

            # NEW explicit merger pipeline
            winner.merge_players(loser)
                        
            self.display.display_merger(winner, loser)
            self.display.any_to_continue()

            self._apply_merger_pricing(winner, loser)
            self._update_map_after_merger(winner, loser)
            self._retire_company(loser)

            merging_companies.append(winner)

        return merging_companies[0]


    def quit(self, confirm = True):
        '''
        Ends the game - gives turn count, stats, etc.
        Confirm is defaulted to True, but will be passed as False if the game is actually
        over, either by hitting max turns or not having MAX_MOVES legal moves left.
        '''
        # TODO - Flesh out quit routine
        if confirm and self.display.input_prompt("Hit 'Y' to confirm quit.").upper()[0] != 'Y':
            return False
        self.display.display_end_of_game()
        print(f'Hit return/enter to quit.')
        x = input()
        sys.exit()


    def _get_legal_moves(self, map):
        '''
        If all companies already exist, insure no space that could create one is offered.
        If possible companies not maxed, then just return first MAX_MOVES.
        '''
        possible_moves = []
        legal_moves = [k for k, v in map.map.items() if v not in OCCUPIED_MAP_SYMBOLS]
        random.shuffle(legal_moves)
        if len(legal_moves) < MAX_MOVES:
            self.quit(confirm = False)

        if len(self.active_companies) == len(COMPANIES):
            for c in legal_moves:
                if not self._check_company_creation(c, map):
                    possible_moves.append(c)
                if len(possible_moves) == MAX_MOVES:
                    return sorted(possible_moves)
        else:
            return sorted(legal_moves[0:MAX_MOVES])


    def _check_company_creation(self, c, map):
        '''
        Returns TRUE if any coordinate around c will cause a company to form.
        '''
        if (CREATE_COMPANY_SYMBOLS).intersection(set(map.nsew(c)['coordinates'].values())):
            return True
        return False

    def get_winner(self):
        d = {player.name: player.net_worth for player in self.players}
        winning_amount = max(d.values())
        winners = [k for k,v in d.items() if v == winning_amount]
        return winners

    def __repr__(self):
        d = {
            'map': len(self.map.map),
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

    def print_map(self):
        '''Print header row of letters, then each row in turn.'''
        print(f'{MAP_HEADER}')
        for row in ROW_LIST:
            print (f'{row}', end ='')
            for char in COL_LIST:
                print(f'{MAP_PRINT_SPACE}{self.map[char + row]}', end='')
            print()


    # TODO - Create values and data properties that can return info without double map.map() notation

    def nsew(self, c):
        '''
        Given a map coordinate c, return the symbols that are North, South,
        East, and West of that coordinate, as well as counts of stars, outposts,
        empty space, and number of companies. Used for checking legal moves and
        for mergers.
        '''
        nsew = {
                'center': c, 'coordinates': {},
                'stars': 0, 'outposts': 0, 'empty_space': 0, 'companies': set()
        }

        nsew = self._get_nsew_values(c, nsew)
        for v in nsew['coordinates'].values():
            if v == STAR:
                nsew['stars'] += 1
            elif v == OUTPOST:
                nsew['outposts'] +=1
            elif v == EMPTY_SPACE:
                nsew['empty_space'] += 1
            elif v in COMPANY_SYMBOLS:
                nsew['companies'].add(v)
        return nsew

    def split_coordinate(self, c):
        '''returns tuple of column (letter) and row (number) for a given coord'''
        return (c[0], c[1])

    def get_indices(self, c):
        '''returns tuple of column (letter) and row (number) for a given coord'''
        return (COL_LIST.index(c[0]), ROW_LIST.index(c[1]))

    def _get_nsew_values(self, c, nsew):
        '''Gets surrounding values for a given point on the map'''

        col_index, row_index = self.get_indices(c)
        rows = self._get_coords(row_index, ROW_LIST, COL_LIST[col_index], prefix = True)
        cols = self._get_coords(col_index, COL_LIST, ROW_LIST[row_index], prefix = False)

        for c in (rows + cols):
            nsew['coordinates'][c] = self.map[c]
        return nsew

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
        # FIXME - Comment out seed to play game for return_vals
        if randint(0,20) == 10:
            return STAR
        else:
            return EMPTY_SPACE

    def __repr__(self):
        return(f'{self.map}')


class Display():
    '''
    Encapsulates display functions
    Eventually move this to blessings terminal manipulation
    Could later do a version for pygame
    '''

    def __init__(self, game):
        self.game = game
        '''Lots more stuff here as display gets more complex'''

    def input_prompt(self, input_string = None):
        if input_string:
            print(f'{input_string}')
        return input('> ')

    def any_to_continue(self):
        input('Press enter key to continue.')

    def prompt_player_move(self, text):
        pass
        '''Display legal moves and prompt - return move selected'''

    def prompt_stock_purchase(self, company, player):
        '''Offer stock to purchase and prompt - return number of shares to buy'''
        print(f'')
        print(f'Purchase how many shares of {company.name} at {company.str_share_price} per share?')
        print(f'Cash on hand: {player.str_cash_on_hand} ', end = '')
        print(f'Max possibe: {int(player.cash_on_hand // company.share_price)}, ', end = '')
        print(f'Current holdings: {player.portfolio[company.symbol]}')
        return self.input_prompt()


    def display_instructions(self):
        pass
        '''Full instruction display for users'''

    def display_announcement (self, lines, player_info = None, company = None, losing_company = None, alignment = 'c'):
        print(self.game.terminal.clear())
        self._print_announcement_header()
        for line in lines:
            if type(line) == list:
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


    def display_new_company(self, company):
        self.display_announcement([
                                NEW_COMPANY_PHRASE,
                                company.name.upper(),
                                " ",
                                f'Opening Price: {company.str_share_price}'
                ]
            )


    def display_two_for_one(self, company):
        self.display_announcement([
                                TWO_FOR_ONE_PHRASES[0],
                                company.name.upper(),
                                TWO_FOR_ONE_PHRASES[1],
                                " ",
                                SPECIAL_ANNOUNCEMENT_PLEASE_NOTE,
                                SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE,
                                [TWO_FOR_ONE_CATEGORIES, STD_CAT_ALIGNMENT]
                ], TWO_FOR_ONE_COLUMNS, company = company, alignment = STD_CAT_ALIGNMENT
            )

    def display_merger(self, company, losing_company):
        self.display_announcement([
                                company.name.upper(),
                                " ",
                                MERGER_PHRASE,
                                " ",
                                losing_company.name.upper(),
                                " ",
                                SPECIAL_ANNOUNCEMENT_PLEASE_NOTE,
                                SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE,
                                [MERGER_CATEGORIES, STD_CAT_ALIGNMENT]
                ], MERGER_COLUMNS, company = company, losing_company = losing_company,
                    alignment = STD_CAT_ALIGNMENT
            )


    def display_map(self, player_portfolio, last_move=None):
        '''Print map and mini portfolio for standard turn.'''
        map = self.game.map.map
        print(self.game.terminal.clear())
        print(f'Turn number: {self.game.turn_number} out of {self.game.max_turns}'.center(MAP_WIDTH))
        # TODO - Add player name to this line,
        print(f'{("-"*MAP_WIDTH).center(MAP_WIDTH)}')
        print(MAIN_DISPLAY_HEADER)
        for row_num,row in enumerate(ROW_LIST):
            print (f'{row}', end ='')
            for char in COL_LIST:
                print(f'{MAP_PRINT_SPACE}{map[char + row]}', end='')
            print(f'{player_portfolio[row_num]}')
        print(f' ')
        if last_move:
            print(f'{self.game.active_player.name} played: {last_move}')

    def display_portfolio(self, player):
        display_port = []
        for k,v in player.sorted_portfolio.items():
            display_port.append(f'{k}: {v}')
        self._print()
        print(f'{display_port}')

    def display_ticker(self):
        pass
        # ticker = []
        # for c in self.game.active_companies.values():
        #     ticker.append(f'{c.symbol} @ {c.str_share_price}')
        # print(f'')
        # self._print(SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE)
        # self._print(TICKER_HEADER)
        # self._print(ticker)
        # self._print(SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE)


    def display_end_of_game(self):
        '''Final display'''
        self.display_announcement([
                                GAME_OVER_PHRASES[0],
                                self._get_winner_string(),
                                '',
                                GAME_OVER_PHRASES[1],
                                SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE,
                                [GAME_OVER_CATEGORIES, STD_CAT_ALIGNMENT]
                ], player_info = GAME_OVER_COLUMNS, alignment = STD_CAT_ALIGNMENT
            )


        # self._print_announcement_header()
        # self._print([GAME_OVER_PHRASES[0]])
        # self._print([self._get_winner_string()])
        # self._print()
        # self._print([GAME_OVER_PHRASES[1]])
        # self._print([SPECIAL_ANNOUNCEMENT_HORIZONTAL_RULE])
        # self._print(GAME_OVER_CATEGORIES, STD_CAT_ALIGNMENT)
        # self._print_player_info(GAME_OVER_COLUMNS)
        # self._print(SPECIAL_ANNOUNCEMENT_FOOTER)
        # self._print()


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
        blank_fill = ' ' * (SPECIAL_ANNOUNCEMENT_TEXT_WIDTH - len(line))
        print(f'{SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL}{line}{blank_fill}{SPECIAL_ANNOUNCEMENT_SIDE_SYMBOL}')


    def _create_columns_line(self, columns, alignments):
        '''Given list of strings to align, returns single line with appropriate spacing '''
        result = ''
        for index, text in enumerate(columns):
            result += self._apply_display_alignment(text,
                alignment = alignments[index] if len(alignments) > index else 'c',
                col_width = SPECIAL_ANNOUNCEMENT_TEXT_WIDTH // len(columns)
            )
        return result


    def _apply_display_alignment(self, text, alignment = '', col_width = SPECIAL_ANNOUNCEMENT_TEXT_WIDTH):
        if alignment not in ('r', 'l'):
            return text.center(col_width)
        elif alignment == 'r':
            return text.rjust(col_width)
        else:
            return text.ljust(col_width)
