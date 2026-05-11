from collections import OrderedDict
from types import SimpleNamespace

import pytest

import trade_objects


def format_company_row(label, qty, price):
    return trade_objects.Display._format_company_row(label, qty, price)


def format_summary_row(label, price, decimal_column=None):
    return trade_objects.Display._format_summary_row(label, price, decimal_column)


def money_decimal_column(row):
    return trade_objects.Display._money_decimal_column(row)


@pytest.mark.parametrize(
    "label,qty,company_price,summary_label,summary_price",
    [
        ("A:", 37, "$1,750.00", "Stocks:", "$105,250.00"),
        ("\x1b[31mA\x1b[0m:", 62, "$300.00", "Total:", "$351,308.00"),
        # Some terminals emit ESC(B alongside CSI color/reset sequences.
        ("\x1b(B\x1b[31mA\x1b(B\x1b[m:", 35, "$2,500.00", "Stocks:", "$143,100.00"),
    ],
)
def test_summary_decimal_aligns_with_company_row_variants(
    label,
    qty,
    company_price,
    summary_label,
    summary_price,
):
    company_row = format_company_row(label, qty, company_price)
    decimal_anchor = money_decimal_column(company_row)

    summary_row = format_summary_row(summary_label, summary_price, decimal_anchor)

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


def test_portfolio_remains_internally_aligned_in_color_and_no_color(game_factory, monkeypatch):
    game_plain = game_factory()
    game_color = game_factory()

    player_plain = game_plain.players[0]
    player_color = game_color.players[0]

    companies = OrderedDict([
        ("A", SimpleNamespace(symbol="A", share_price=2500)),
        ("B", SimpleNamespace(symbol="B", share_price=1750)),
    ])

    game_plain.active_companies = companies
    game_color.active_companies = OrderedDict([
        ("A", SimpleNamespace(symbol="A", share_price=2500)),
        ("B", SimpleNamespace(symbol="B", share_price=1750)),
    ])

    game_plain.terminal.supports_color = False
    game_plain.terminal.color = lambda text, **kwargs: text

    game_color.terminal.supports_color = True
    game_color.terminal.color = lambda text, **kwargs: f"\x1b[31m{text}\x1b[0m"

    for player in (player_plain, player_color):
        player.portfolio["A"] = 12
        player.portfolio["B"] = 9
        player.cash_on_hand = 21000

    monkeypatch.setattr(
        trade_objects.locale,
        "currency",
        lambda val, symbol=True, grouping=False, international=False: f"${val:,.2f}",
    )

    plain_rows = game_plain.display.build_portfolio_for_map(player_plain)
    color_rows = game_color.display.build_portfolio_for_map(player_color)

    plain_decimals = [money_decimal_column(row) for row in plain_rows if "." in row]
    color_decimals = [money_decimal_column(row) for row in color_rows if "." in row]

    # Each terminal mode should keep all money values internally aligned.
    assert len(set(plain_decimals)) == 1
    assert len(set(color_decimals)) == 1

    # Monetary rows should produce stable visible widths in both modes.
    plain_money_widths = [trade_objects.visible_len(row) for row in plain_rows if "." in row]
    color_money_widths = [trade_objects.visible_len(row) for row in color_rows if "." in row]

    assert len(set(plain_money_widths)) == 1
    assert len(set(color_money_widths)) == 1
