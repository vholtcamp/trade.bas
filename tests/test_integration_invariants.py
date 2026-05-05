from trade_objects import (
    STARTING_SHARE_PRICE,
    TWO_FOR_ONE_PRICE,
)
from tests.rule_helpers import (
    all_companies_obey_price_quantum,
    found_company,
    only_active_company,
    place_outpost,
    play,
)


def test_forced_sequence_preserves_price_and_quantum_invariants(game):
    """Regression sequence: create -> expand -> split -> merge -> expand keeps invariants true."""
    p0, p1 = game.players

    # create
    a = found_company(game, p0, "B2")
    assert a.price_quantum == STARTING_SHARE_PRICE
    assert all_companies_obey_price_quantum(game)

    # expand
    play(game, p0, "C2")
    assert all_companies_obey_price_quantum(game)

    # split: force crossing via direct rule setup, then expand
    a.share_price = TWO_FOR_ONE_PRICE - STARTING_SHARE_PRICE
    place_outpost(game, "D3")
    play(game, p0, "D2")
    assert a.share_price < TWO_FOR_ONE_PRICE
    assert all_companies_obey_price_quantum(game)

    # merge: introduce second company then connect
    found_company(game, p1, "F2")
    play(game, p0, "E2")
    assert len(game.active_companies) == 1
    surviving = only_active_company(game)
    assert surviving.price_quantum <= STARTING_SHARE_PRICE
    assert all_companies_obey_price_quantum(game)

    # expand again
    play(game, p0, "E3")
    assert all_companies_obey_price_quantum(game)
