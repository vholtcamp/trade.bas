from tests.rule_helpers import found_company, place_star, play
from trade_objects import OUTPOST, STARTING_CASH


def test_pay_dividends_single_company_single_player(game):
    player = game.players[0]
    company = found_company(game, player, "B2")

    # Override founder shares so expected math is explicit.
    player.portfolio[company.symbol] = 10
    company.share_price = 1200

    start_cash = player.cash_on_hand
    game.pay_dividends(player)

    expected = int(0.05 * 10 * 1200)
    assert player.cash_on_hand == start_cash + expected


def test_pay_dividends_accumulates_multiple_companies(game):
    player = game.players[0]

    a = found_company(game, player, "B2")
    b = found_company(game, player, "D2")

    player.portfolio[a.symbol] = 4
    player.portfolio[b.symbol] = 7
    a.share_price = 500
    b.share_price = 1500

    start_cash = player.cash_on_hand
    game.pay_dividends(player)

    expected = int(0.05 * 4 * 500) + int(0.05 * 7 * 1500)
    assert player.cash_on_hand == start_cash + expected


def test_player_stock_value_and_net_worth_reflect_holdings(game):
    player = game.players[0]

    a = found_company(game, player, "B2")
    b = found_company(game, player, "D2")

    player.portfolio[a.symbol] = 2
    player.portfolio[b.symbol] = 3
    a.share_price = 700
    b.share_price = 300
    player.cash_on_hand = 4321

    expected_stock_value = (2 * 700) + (3 * 300)
    assert player.stock_value == expected_stock_value
    assert player.net_worth == 4321 + expected_stock_value


def test_get_winner_returns_tied_players(game):
    p1, p2 = game.players
    p1.cash_on_hand = 9000
    p2.cash_on_hand = 9000

    winners = game.get_winner()

    assert set(winners) == {p1.name, p2.name}


def test_get_winner_returns_single_highest_net_worth_player(game):
    p1, p2 = game.players
    p1.cash_on_hand = STARTING_CASH + 10
    p2.cash_on_hand = STARTING_CASH

    winners = game.get_winner()

    assert winners == [p1.name]


def test_play_move_places_outpost_when_isolated(game):
    player = game.players[0]

    play(game, player, "B2")

    assert game.map["B2"] == OUTPOST


def test_map_nsew_corner_and_edge_neighbors(game):
    corner = game.map.nsew("A1")
    edge = game.map.nsew("A5")

    assert set(corner.neighbors.keys()) == {"A2", "B1"}
    assert set(edge.neighbors.keys()) == {"A4", "A6", "B5"}


def test_round_advances_turn_and_runs_each_player(game, monkeypatch):
    calls = []

    def fake_execute_turn(player, autopilot=False):
        calls.append((player.name, autopilot))

    monkeypatch.setattr(game, "execute_turn", fake_execute_turn)
    monkeypatch.setattr(game.display, "display_map", lambda *_args, **_kwargs: None)

    start_turn = game.turn_number
    game.round()

    assert len(calls) == len(game.players)
    assert all(autopilot is True for _, autopilot in calls)
    assert game.turn_number == start_turn + 1


def test_round_integration_applies_move_dividend_and_autobuy_for_each_player(game, monkeypatch):
    p1, p2 = game.players

    # Ensure each player's forced move founds a company at a deterministic price.
    place_star(game, "C2")
    place_star(game, "F2")

    moves = {
        p1.name: "B2",
        p2.name: "E2",
    }

    monkeypatch.setattr(
        game,
        "_get_legal_moves",
        lambda _map: [moves[game.active_player.name]],
    )

    starting_cash = {p.name: p.cash_on_hand for p in game.players}
    game.round()

    # Map mutation from played moves.
    assert game.map["B2"] in {"A", "B", "C", "D", "E"}
    assert game.map["E2"] in {"A", "B", "C", "D", "E"}

    # Round progression and company creation.
    assert game.turn_number == 2
    assert len(game.active_companies) == 2

    # Each player should have received dividends and purchased stock via autopilot.
    for player in (p1, p2):
        assert player.cash_on_hand != starting_cash[player.name]
        assert sum(player.portfolio.values()) > 0


def test_map_generate_map_contains_only_valid_symbols(game):
    assert set(game.map.values()).issubset({".", "*"})


def test_buy_stocks_rejects_insufficient_cash_then_accepts_blank(game_factory, monkeypatch, scripted_input):
    game = game_factory(interactive=False, autopilot=False)
    player = game.players[0]
    company = found_company(game, player, "B2")

    player.cash_on_hand = 100
    company.share_price = 200

    game.display.display_map = lambda *_args, **_kwargs: None

    # First attempt is unaffordable; blank skips the company cleanly.
    scripted_input("3", "")

    player.buy_stocks()

    assert player.cash_on_hand == 100
    assert player.portfolio[company.symbol] == 5
    assert game.last_action is not None
    assert "Skipped purchase" in game.last_action
