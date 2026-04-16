from trade_objects import Map, Game, Player, Company

# TODO - Turn this into unit tests
print("Map testing")
m = Map()
m.print_map()

print(m.nsew('A1'))
print(m.nsew('B3'))
print(m.nsew('F3'))
print(m.split_coordinate('A1'))
print(m)
print(m.nsew('A1'))

print("Game testing")
g = Game(number_of_players=4)
print(g.number_of_players)
print(g.turn_number)
print(g.players)
print(g.active_companies)
g.map.print_map()
print(g._get_legal_moves(g.map.map))
print(g)

print("Player testing")
p = Player("Victor", g)
print(p.name)
print(p.cash_on_hand)
print(p.portfolio)
print(p.game)
print(p.portfolio['A'])

m.map['G3'] = '+'

print("Company Testing")
c = Company(g, p, m.nsew('F3'))
print(c)
print(f'Outpost Count: {c.outposts()}')
print(f'{c.share_price}')
print(p.portfolio)
print(p.cash_on_hand)
print(p.net_worth)
p.collect_dividends()
print(p.cash_on_hand)


if __name__ == '__main__':
    pass
