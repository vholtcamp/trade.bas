import pytest

from trade_objects import (
    OUTPOST_BONUS,
    STAR_BONUS,
    STARTING_SHARE_PRICE,
    TWO_FOR_ONE_PRICE,
)
from tests.rule_helpers import found_company, place_outpost, place_star, play


def test_expansion_applies_base_and_feature_bonuses(game):
    """Expansion adds base OUTPOST_BONUS plus adjacent star/outpost bonuses."""
    player = game.players[0]
    company = found_company(game, player, "B2")

    place_outpost(game, "C3")
    place_star(game, "D2")

    old_price = company.share_price
    play(game, player, "C2")

    expected_increment = OUTPOST_BONUS + OUTPOST_BONUS + STAR_BONUS
    assert company.share_price == old_price + expected_increment
    assert game.map["C2"] == company.symbol
    assert game.map["C3"] == company.symbol


def test_expansion_price_respects_quantum_invariant(game):
    """After expansion, share_price must be divisible by price_quantum."""
    player = game.players[0]
    company = found_company(game, player, "B2")

    # Craft state where arithmetic would not naturally land on a quantum boundary.
    company.price_quantum = STARTING_SHARE_PRICE // 2
    company.share_price = company.price_quantum * 19 + STAR_BONUS // 2

    place_star(game, "D2")
    play(game, player, "C2")

    assert company.share_price % company.price_quantum == 0


def test_stock_split_crossing_threshold_updates_price_quantum_and_holdings(game):
    """Crossing TWO_FOR_ONE_PRICE triggers split semantics for price, quantum, and holdings."""
    p0, p1 = game.players
    company = found_company(game, p0, "B2")

    # Give both players holdings so doubling behavior is observable.
    p0.portfolio[company.symbol] = 3
    p1.portfolio[company.symbol] = 2

    # Force a crossing via expansion with one adjacent star.
    company.share_price = TWO_FOR_ONE_PRICE - OUTPOST_BONUS
    old_quantum = company.price_quantum

    place_star(game, "D2")
    play(game, p0, "C2")

    assert company.share_price < TWO_FOR_ONE_PRICE
    assert company.price_quantum == old_quantum // 2
    assert company.price_quantum <= old_quantum
    assert p0.portfolio[company.symbol] == 6
    assert p1.portfolio[company.symbol] == 4


def test_price_quantum_changes_only_on_split(game):
    """Regular expansion should keep price_quantum unchanged unless a split occurs."""
    player = game.players[0]
    company = found_company(game, player, "B2")

    old_quantum = company.price_quantum
    play(game, player, "C2")

    assert company.price_quantum == old_quantum


def test_repeated_splits_never_reduce_price_quantum_below_one(game):
    """Regression: repeated split events must keep a positive non-zero quantum."""
    player = game.players[0]
    company = found_company(game, player, "B2")

    # Simulate deep split history where quantum approaches the floor.
    company.price_quantum = 1
    company.share_price = TWO_FOR_ONE_PRICE
    old_holdings = player.portfolio[company.symbol]

    company.split_stock()

    assert company.price_quantum == 1
    assert company.share_price == TWO_FOR_ONE_PRICE // 2
    assert player.portfolio[company.symbol] == old_holdings * 2
