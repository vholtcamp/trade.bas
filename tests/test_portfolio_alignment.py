from collections import OrderedDict
from types import SimpleNamespace

import trade_objects


def format_company_row(label, qty, price):
    return trade_objects.Display._format_company_row(label, qty, price)


def format_summary_row(label, price, decimal_column=None):
    return trade_objects.Display._format_summary_row(label, price, decimal_column)


def money_decimal_column(row):
    return trade_objects.Display._money_decimal_column(row)


def test_summary_decimal_aligns_with_plain_company_row():
    company_row = format_company_row("A:", 37, "$1,750.00")
    decimal_anchor = money_decimal_column(company_row)

    summary_row = format_summary_row("Stocks:", "$105,250.00", decimal_anchor)

    assert money_decimal_column(summary_row) == decimal_anchor


def test_summary_decimal_aligns_with_ansi_colored_company_row():
    colored_label = "\x1b[31mA\x1b[0m:"
    company_row = format_company_row(colored_label, 62, "$300.00")
    decimal_anchor = money_decimal_column(company_row)

    summary_row = format_summary_row("Total:", "$351,308.00", decimal_anchor)

    assert money_decimal_column(summary_row) == decimal_anchor


def test_summary_decimal_aligns_with_non_csi_terminal_escapes():
    # Some terminals emit ESC(B alongside CSI color/reset sequences.
    colored_label = "\x1b(B\x1b[31mA\x1b(B\x1b[m:"
    company_row = format_company_row(colored_label, 35, "$2,500.00")
    decimal_anchor = money_decimal_column(company_row)

    summary_row = format_summary_row("Stocks:", "$143,100.00", decimal_anchor)

    assert money_decimal_column(summary_row) == decimal_anchor


def test_display_build_portfolio_aligns_summary_rows_with_company_row(game_factory, monkeypatch):
    game = game_factory()
    player = game.players[0]

    game.terminal.supports_color = True
    game.terminal.color = lambda text, **kwargs: f"\x1b[31m{text}\x1b[0m"

    game.active_companies = OrderedDict([
        (
            "A",
            SimpleNamespace(symbol="A", share_price=2500),
        )
    ])

    player.portfolio["A"] = 35
    player.cash_on_hand = 9000

    monkeypatch.setattr(
        trade_objects.locale,
        "currency",
        lambda val, symbol=True, grouping=False, international=False: f"${val:,.2f}",
    )

    rows = game.display.build_portfolio_for_map(player)

    company_decimal = money_decimal_column(rows[0])
    stocks_decimal = money_decimal_column(rows[1])
    cash_decimal = money_decimal_column(rows[2])
    total_decimal = money_decimal_column(rows[4])

    assert stocks_decimal == company_decimal
    assert cash_decimal == company_decimal
    assert total_decimal == company_decimal
