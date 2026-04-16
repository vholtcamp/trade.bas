from trade_objects import map

m = Map()
m.print_map()


if __name__ == '__main__':
    main()

    # def print_portfolio(self):
    #     #Delete? This is only called by the command "S" which is redundant with new display
    #     print(f'Stock holdings')
    #     for k,v in self.portfolio.items():
    #         c = self.game.active_companies[k]
    #         print(f'{c.name} -- {v} -- {CURRENCY_SYMBOL}{v * c.share_price}')
