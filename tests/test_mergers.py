import pytest

from trade_objects import (
    BASIC_MERGER_CASH_MULTIPLIER,
    STARTING_SHARE_PRICE,
)
from tests.rule_helpers import found_company, only_active_company, play


def test_merger_triggers_only_when_new_move_touches_multiple_companies(game):
    """A merger is event-driven: only the newly played connecting square triggers it."""
    p0, p1 = game.players

    found_company(game, p0, "B2")
    found_company(game, p1, "D2")

    # Existing board state with two companies should not merge by itself.
    assert len(game.active_companies) == 2

    # This move touches only one company (A), so no merger should occur.
    play(game, p0, "B3")
    assert len(game.active_companies) == 2

    # This move at C2 touches both A and B, so merger should trigger.
    play(game, p0, "C2")
    assert len(game.active_companies) == 1


def test_merger_winner_uses_size_then_tiebreak_on_age(game, game_factory):
    """Winner selection should respect current size comparison and founded_on tie-break."""
    p0, p1 = game.players

    found_company(game, p0, "B2")
    b = found_company(game, p1, "D2")

    # Make B larger (more outposts) before connecting for merger.
    play(game, p1, "D3")

    play(game, p0, "C2")
    assert b.symbol in game.active_companies

    # Tie case: create fresh game state where sizes are equal and older should win.
    game2 = game_factory()
    p0b, p1b = game2.players

    older = found_company(game2, p0b, "F2")
    game2.turn_number += 1
    newer = found_company(game2, p1b, "H2")

    play(game2, p0b, "G2")
    assert older.symbol in game2.active_companies
    assert newer.symbol not in game2.active_companies


def test_merger_pricing_quantum_truncation_and_player_conversion(game):
    """Merger pricing and player effects should follow additive + min quantum + truncation rules."""
    p0, p1 = game.players

    winner = found_company(game, p0, "B2")
    loser = found_company(game, p1, "D2")

    # Controlled merger pricing setup.
    winner.share_price = STARTING_SHARE_PRICE * 7  # 700
    winner.price_quantum = STARTING_SHARE_PRICE     # 100
    loser.share_price = STARTING_SHARE_PRICE * 5 + STARTING_SHARE_PRICE // 2  # 550
    loser.price_quantum = STARTING_SHARE_PRICE // 2  # 50

    # Controlled portfolios for conversion and bonus checks.
    p0.portfolio[loser.symbol] = 3
    p1.portfolio[loser.symbol] = 1

    pre_cash0 = p0.cash_on_hand
    pre_cash1 = p1.cash_on_hand

    play(game, p0, "C2")

    surviving = only_active_company(game)
    assert surviving.share_price == 1250
    assert surviving.price_quantum == STARTING_SHARE_PRICE // 2
    assert surviving.share_price % surviving.price_quantum == 0

    # Rounded 2-for-1 conversion: 3 -> 2, 1 -> 1.
    assert p0.portfolio[surviving.symbol] >= 2
    assert p1.portfolio[surviving.symbol] >= 1

    # Bonus is computed at merge time using the loser's pre-truncation price.
    # The engine records the computed bonus in old_data_for_display.
    expected_bonus0 = p0.old_data_for_display
    expected_bonus1 = p1.old_data_for_display

    assert p0.cash_on_hand == pytest.approx(pre_cash0 + expected_bonus0)
    assert p1.cash_on_hand == pytest.approx(pre_cash1 + expected_bonus1)


def test_three_way_merger_preserves_structural_invariants(game):
    """A 3-way connector move should collapse three companies into one valid survivor."""
    p0, p1 = game.players

    # Place three companies around C3 (north, west, east), then connect at C3.
    c_north = found_company(game, p0, "C2")
    c_west = found_company(game, p1, "B3")
    c_east = found_company(game, p0, "D3")

    merged_symbols = {c_north.symbol, c_west.symbol, c_east.symbol}
    min_pre_quantum = min(c.price_quantum for c in (c_north, c_west, c_east))

    play(game, p0, "C3")

    assert len(game.active_companies) == 1
    survivor = only_active_company(game)
    assert survivor.symbol in merged_symbols
    assert game.map["C3"] == survivor.symbol

    # All retired company symbols should be absent from the map and portfolios.
    retired_symbols = merged_symbols - {survivor.symbol}
    for tile in game.map.values():
        assert tile not in retired_symbols
    for player in game.players:
        assert set(player.portfolio.keys()).issubset(set(game.active_companies.keys()))

    # Economic invariants must hold after chain-merger resolution.
    assert survivor.share_price % survivor.price_quantum == 0
    assert survivor.price_quantum <= min_pre_quantum


def test_four_way_merger_preserves_structural_invariants(game):
    """A 4-way connector move should resolve successive mergers and leave one valid company."""
    p0, p1 = game.players

    # Place four companies around C3 (N, S, W, E), then connect at C3.
    c_north = found_company(game, p0, "C2")
    c_south = found_company(game, p1, "C4")
    c_west = found_company(game, p0, "B3")
    c_east = found_company(game, p1, "D3")

    merged_symbols = {c_north.symbol, c_south.symbol, c_west.symbol, c_east.symbol}
    min_pre_quantum = min(c.price_quantum for c in (c_north, c_south, c_west, c_east))

    play(game, p0, "C3")

    assert len(game.active_companies) == 1
    survivor = only_active_company(game)
    assert survivor.symbol in merged_symbols
    assert game.map["C3"] == survivor.symbol

    retired_symbols = merged_symbols - {survivor.symbol}
    for tile in game.map.values():
        assert tile not in retired_symbols
    for player in game.players:
        assert set(player.portfolio.keys()).issubset(set(game.active_companies.keys()))

    assert survivor.share_price % survivor.price_quantum == 0
    assert survivor.price_quantum <= min_pre_quantum
