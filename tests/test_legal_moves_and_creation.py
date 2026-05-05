import pytest

from trade_objects import EMPTY_SPACE, MAX_MOVES
from tests.rule_helpers import found_company, place_outpost, place_star


def _activate_max_companies(game, player):
    """Create one instance of each company so legal-move filtering branch is exercised."""
    # Spaced-apart coordinates keep setup deterministic and avoid accidental adjacency effects.
    for coord in ("A1", "C1", "E1", "G1", "I1"):
        found_company(game, player, coord)


def test_get_legal_moves_when_companies_below_max_returns_max_moves(game):
    """When fewer than max companies exist, legal moves should return MAX_MOVES empties."""
    moves = game._get_legal_moves(game.map)

    assert len(moves) == MAX_MOVES
    assert moves == sorted(moves)
    assert len(set(moves)) == MAX_MOVES
    assert all(game.map[m] == EMPTY_SPACE for m in moves)


def test_get_legal_moves_when_companies_maxed_filters_creation_enablers(game):
    """When all companies exist, legal moves must avoid squares that could form a new company."""
    player = game.players[0]
    _activate_max_companies(game, player)

    # Seed creation-enabling terrain so filtering must be applied.
    place_star(game, "D5")
    place_outpost(game, "F5")

    moves = game._get_legal_moves(game.map)

    assert len(moves) == MAX_MOVES

    # Behavioral assertion: returned moves should not touch star/outpost terrain.
    for coord in moves:
        neighborhood = game.map.nsew(coord)
        assert neighborhood.stars == 0
        assert neighborhood.outposts == 0


def test_check_company_creation_allowed_with_adjacent_star(game):
    """Company creation gating should allow a square adjacent to a star."""
    place_star(game, "C2")

    assert game._check_company_creation("B2", game.map) is True


def test_check_company_creation_allowed_with_adjacent_outpost(game):
    """Company creation gating should allow a square adjacent to an outpost."""
    place_outpost(game, "C2")

    assert game._check_company_creation("B2", game.map) is True


def test_check_company_creation_disallowed_with_company_adjacent_only(game):
    """Company creation gating should disallow squares touching only existing company symbols."""
    player = game.players[0]
    found_company(game, player, "E5")

    assert game._check_company_creation("D5", game.map) is False


def test_check_company_creation_disallowed_when_all_neighbors_empty(game):
    """Company creation gating should disallow fully empty neighborhoods."""
    assert game._check_company_creation("B2", game.map) is False


def test_check_company_creation_regression_uses_neighborhood_api(game):
    """Regression: _check_company_creation should work with Neighborhood.neighbors values."""
    place_star(game, "C2")

    try:
        result = game._check_company_creation("B2", game.map)
    except Exception as exc:
        pytest.fail(f"_check_company_creation raised unexpectedly: {exc}")

    assert result is True
