#!/usr/bin/env python3

from blessed import Terminal
from trade_objects import Map


term = Terminal()
m = Map()
# print ("Hello World!")
#
# print (term.bold('Hi there!'))
with term.fullscreen():
    # with term.location(0, term.height - 1):
    #     print(f'Here is the bottom')
    #     print(term.height)
    #     print(term.width)
    # print('This is back where I came from.')
    # print(f'>', end ='')
    # x = input()
    print(term.clear())

    print(term.move(term.height - 2) + "Hi there")
    with term.location(y=2, x=40):
        print("Portfolio?")
    print(term.move(term.height - 2) + "Returned?")
    x = input()
    print(term.move(term.height - 3))
    print(term.clear())
    # print(term.move(term.height))
    m.print_map()
    # OK, so to keep a standard line, you have to use an absolute ref to term height or width?


    #
    # x = input()
    # print(term.move_x(15) + term.move_y())
    # term.clear_eol
    # term.clear_eol

    x = input()
    print(term.clear())
    print ('''
            *** {PLAYER}'s PORTFOLIO *** [13 - 41]
-------------------------------------------------------
Altair Starways (A)   |      10 |     500 |       5,000
_______________________________________________________
Betelgeuse Ltd. (B)   |       0 |     200 |           0
_______________________________________________________
Capella Freight (C)   |     500 |    2990 |   1,495,000
_______________________________________________________
Denebola Shippers (D) |       0 |       0 |           0
_______________________________________________________
Eridani Expedit. (E)  |       0 |       0 |           0
=======================================================
         Cash on hand |                          10,000
_______________________________________________________
            NET WORTH |                       1,505,000

   A  B  C  D  E  F  G  H  I  L  K  L
1  .  .  .  .  .  .  .  .  .  .  .  .
2  .  .  .  .  .  .  .  .  .  .  .  .
3  .  .  .  .  .  .  *  .  .  *  .  *
4  .  .  .  .  .  *  .  .  .  .  .  .
5  .  .  .  .  .  .  .  .  .  .  .  .
6  .  .  .  .  .  .  .  .  .  .  .  .
7  .  *  .  .  .  .  .  .  .  .  .  .
8  .  .  .  .  .  .  .  .  .  .  .  .
9  .  .  .  .  .  .  .  .  .  *  .  *
'''  )  
    x = input()
