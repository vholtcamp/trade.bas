from trade_objects import (
    EMPTY_SPACE,
    OUTPOST_BONUS,
    STAR,
    STAR_BONUS,
    STARTING_SHARE_PRICE,
)
from tests.rule_helpers import found_company, place_outpost, place_star, play


def test_opening_share_price_uses_rule_constants(game):
    """A new company opening price should follow START + center + adjacent bonuses."""
    player = game.players[0]

    # Found at B2 with one adjacent outpost and one adjacent star.
    place_outpost(game, "B1")
    place_star(game, "C2")

    nsew = game.map.nsew("B2")
    company = found_company(game, player, "B2")

    expected = (
        STARTING_SHARE_PRICE
        + OUTPOST_BONUS  # founding square
        + OUTPOST_BONUS * nsew.outposts
        + STAR_BONUS * nsew.stars
    )
    assert company.share_price == expected


def test_new_company_cannot_form_adjacent_to_existing_company(game):
    """If the played square touches one company, expansion takes precedence over creation."""
    player = game.players[0]

    # First create company A at B2.
    place_outpost(game, "B1")
    first = found_company(game, player, "B2")

    # Now place a star near B3 so creation would be possible if no company touched.
    place_star(game, "C3")
    play(game, player, "B3")

    assert len(game.active_companies) == 1
    assert game.map["B3"] == first.symbol
    assert game.map["C3"] == STAR  # star remains a star in current rules


def test_company_creation_not_possible_next_to_company_only(game):
    """A square next to only a company symbol must not create another company."""
    player = game.players[0]

    first = found_company(game, player, "E5")

    # D5 touches E5 company tile but no stars/outposts are present.
    play(game, player, "D5")

    assert len(game.active_companies) == 1
    assert game.map["D5"] == first.symbol
    assert all(v in {EMPTY_SPACE, first.symbol} for v in game.map.values())
