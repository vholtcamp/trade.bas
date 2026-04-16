import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


p1 = "Theo"
p2 = "Victor"
p3 = "A Really long name with far too many characters to display accurately"

c1 = 200
c2 = 500
c3 = 7777

SPECIAL_ANNOUNCEMENT_HEADER = '''
=========================================================
*                        ATTENTION!                     *
*             This is a special announcement            *
*                                                       *'''

TWO_FOR_ONE_MID = '''
*                     The stock of                      *'''

TWO_FOR_ONE_FOLLOW = '''
*                    has split 2:1!                     *'''

MERGER_MID = '''
*                 has just merged with                  *'''

PLEASE_NOTE = '''
*                                                       *
*          Please note the following transactions       *
* ----------------------------------------------------- *
'''



# Special Announcement Strings
SPECIAL_ANNOUNCEMENT_HEADER = '''
===============================================
*                 ATTENTION!                  *
*       This is a special announcement        *
*                                             *
'''

TWO_FOR_ONE_MID = '''*               The stock of                  *'''

TWO_FOR_ONE_FOLLOW = '''*              has split 2:1!                 *'''

MERGER_MID = '''*            has just merged with                *'''

PLEASE_NOTE = '''
*                                             *
*   Please note the following transactions    *
* ------------------------------------------- *
'''

# TODO - Make end of game components
END_OF_GAME_MID = '''
*            The game has ended!              *'''

END_OF_GAME_RESULTS_HEADER = '''
*            Here are the standings           *
* ------------------------------------------- *
*  Player    Cash      Stocks       Net Worth    *'''

SPECIAL_ANNOUNCEMENT_FOOTER = '''
==============================================='''
MINI_PORTFOLIO_SPACER = '  |  '


d = []
d.append("First List Item")
d.extend(f'{MINI_PORTFOLIO_SPACER}'*10)
for i in range(0, len(d)):
    print(d[i])
# line = f'{MINI_PORTFOLIO_SPACER}{k}: {v} @ {locale.currency(self.game.active_companies[k].share_price, grouping=True)}'
k = 'A'
v = 20
price = 500

k2 = 'B'
v2 = 200
price2 = 1500

# print(f'{MINI_PORTFOLIO_SPACER}{k:>5}: {v:>4} @ {locale.currency(price, grouping=True):>9}')
# print(f'{MINI_PORTFOLIO_SPACER}{k2:>5}: {v2:>4} @ {locale.currency(price2, grouping=True):>9}')
#
# print(f'{SPECIAL_ANNOUNCEMENT_HEADER}'
#       f'{TWO_FOR_ONE_MID}'
#       f'{PLEASE_NOTE}')
#
# print(f'(test):>5')
