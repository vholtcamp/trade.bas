from collections import OrderedDict
from types import SimpleNamespace

import pytest

import trade_objects
from trade_objects import Game, STARTING_CASH
from ai_strategies import AdvancedAIStrategy


@pytest.mark.parametrize("autopilot", [False, True])
def test_constructor_skips_input_and_instructions_when_noninteractive(monkeypatch, autopilot):
    calls = []

    def fail_input(prompt=""):
        raise AssertionError(f"input() should not be called in non-interactive mode: {prompt}")

    def record_instructions(self):
        calls.append("instructions")

    monkeypatch.setattr("builtins.input", fail_input)
    monkeypatch.setattr(trade_objects.Display, "display_instructions", record_instructions)

    game = Game(
        number_of_players=2,
        terminal=SimpleNamespace(clear=lambda: ""),
        max_turns=5,
        interactive=False,
        autopilot=autopilot,
    )

    assert game.interactive is False
    assert game.autopilot is autopilot
    expected_names = ["Computer 1", "Computer 2"] if autopilot else ["Player 1", "Player 2"]
    assert sorted(player.name for player in game.players) == expected_names
    assert calls == []


def test_any_to_continue_is_noop_when_noninteractive(game, monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": pytest.fail(f"input() should not be called: {prompt}"),
    )

    game.display.any_to_continue()


def test_any_to_continue_is_noop_when_headless(game_factory, monkeypatch):
    game = game_factory(interactive=False, autopilot=True)
    game.headless = True

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": pytest.fail(f"input() should not be called in headless mode: {prompt}"),
    )

    game.display.any_to_continue()


def test_execute_turn_autopilot_skips_stock_purchase_prompt(game, monkeypatch):
    player = game.players[0]
    company = SimpleNamespace(symbol="T", name="Test Company", share_price=100)
    game.active_companies = OrderedDict([(company.symbol, company)])

    monkeypatch.setattr(game, "_get_legal_moves", lambda _map: ["A1"])
    monkeypatch.setattr(player, "choose_move", lambda legal_moves, autopilot: legal_moves[0])
    monkeypatch.setattr(game, "play_move", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "pay_dividends", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game.display, "display_map", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        game.display,
        "prompt_stock_purchase",
        lambda *_args, **_kwargs: pytest.fail("autopilot turn should not prompt for stock purchases"),
    )

    starting_cash = player.cash_on_hand
    game.execute_turn(player, autopilot=True)

    assert player.portfolio[company.symbol] > 0
    assert player.cash_on_hand < starting_cash
    assert game.last_action.startswith("Autopilot bought")


def test_execute_turn_manual_mode_prompts_for_stock_purchase(game_factory, monkeypatch):
    game = game_factory(interactive=False, autopilot=False)
    player = game.players[0]
    company = SimpleNamespace(symbol="T", name="Test Company", share_price=100)
    game.active_companies = OrderedDict([(company.symbol, company)])

    monkeypatch.setattr(game, "_get_legal_moves", lambda _map: ["A1"])
    monkeypatch.setattr(player, "choose_move", lambda legal_moves, autopilot: legal_moves[0])
    monkeypatch.setattr(game, "play_move", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "pay_dividends", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game.display, "display_map", lambda *_args, **_kwargs: None)

    prompts = []

    def fake_prompt(prompt_company, prompt_player):
        prompts.append((prompt_company.symbol, prompt_player.name))
        return ""

    monkeypatch.setattr(game.display, "prompt_stock_purchase", fake_prompt)

    game.execute_turn(player, autopilot=False)

    assert prompts == [(company.symbol, player.name)]
    assert player.portfolio[company.symbol] == 0
    assert player.cash_on_hand == STARTING_CASH


def test_execute_turn_computer_player_skips_stock_prompt(game_factory, monkeypatch):
    game = game_factory(interactive=False, autopilot=False, number_of_players=2)
    game.human_players = 1
    game.computer_players = 1
    game.players[0].is_computer = False
    game.players[1].is_computer = True

    computer = game.players[1]
    company = SimpleNamespace(symbol="T", name="Test Company", share_price=100)
    game.active_companies = OrderedDict([(company.symbol, company)])

    monkeypatch.setattr(game, "_get_legal_moves", lambda _map: ["A1"])
    monkeypatch.setattr(computer, "choose_move", lambda legal_moves, autopilot: legal_moves[0])
    monkeypatch.setattr(game, "play_move", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "pay_dividends", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game.display, "display_map", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        game.display,
        "prompt_stock_purchase",
        lambda *_args, **_kwargs: pytest.fail("computer turn should not prompt for stock purchases"),
    )

    starting_cash = computer.cash_on_hand
    game.execute_turn(computer, autopilot=False)

    assert computer.portfolio[company.symbol] > 0
    assert computer.cash_on_hand < starting_cash


def test_per_computer_difficulties_are_assigned_in_order(game_factory):
    game = game_factory(interactive=False, autopilot=False, number_of_players=3)
    game = Game(
        number_of_players=3,
        terminal=game.terminal,
        max_turns=5,
        interactive=False,
        autopilot=False,
        human_players=1,
        ai_difficulty="beginner",
        ai_difficulties=["intermediate", "advanced"],
    )

    computers = [p for p in game.players if p.is_computer]
    assert len(computers) == 2
    assert sorted(p.ai_difficulty for p in computers) == ["advanced", "intermediate"]
    assert any(isinstance(p.ai_strategy, AdvancedAIStrategy) for p in computers)


def test_execute_turn_autopilot_can_render_real_map_output(game_factory, monkeypatch, capsys):
    game = game_factory(interactive=False, autopilot=True)
    player = game.players[0]
    game.active_player = player

    company = SimpleNamespace(symbol="T", name="Test Company", share_price=100)
    game.active_companies = OrderedDict([(company.symbol, company)])

    monkeypatch.setattr(game, "_get_legal_moves", lambda _map: ["A1"])
    monkeypatch.setattr(player, "choose_move", lambda legal_moves, autopilot: legal_moves[0])
    monkeypatch.setattr(game, "play_move", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "pay_dividends", lambda *_args, **_kwargs: None)

    # game_factory stubs display_map; restore the real rendering method for this test.
    game.display.display_map = trade_objects.Display.display_map.__get__(
        game.display,
        trade_objects.Display,
    )

    game.execute_turn(player, autopilot=True)

    out = capsys.readouterr().out
    assert "Turn " in out
    assert "Portfolio" in out
    assert game.last_action.startswith("Autopilot bought")


def test_execute_turn_computer_player_shows_move_and_purchase_summary_with_pauses(game_factory, monkeypatch):
    game = game_factory(interactive=False, autopilot=False, number_of_players=2)
    game.interactive = True
    game.headless = False
    game.human_players = 1
    game.computer_players = 1
    game.players[0].is_computer = False
    game.players[1].is_computer = True

    computer = game.players[1]
    game.active_player = computer

    company = SimpleNamespace(symbol="T", name="Test Company", share_price=100)
    game.active_companies = OrderedDict([(company.symbol, company)])

    monkeypatch.setattr(game, "_get_legal_moves", lambda _map: ["A1", "B2", "C3", "D4", "E5"])
    monkeypatch.setattr(computer, "choose_move", lambda legal_moves, autopilot: "A1")
    monkeypatch.setattr(game, "play_move", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "pay_dividends", lambda *_args, **_kwargs: None)

    shown_actions = []

    def record_map(_player):
        shown_actions.append(game.last_action)

    pause_calls = []
    timed_pause_calls = []

    def record_pause(*_args, **_kwargs):
        pause_calls.append(True)

    def record_timed_pause(seconds):
        timed_pause_calls.append(seconds)

    monkeypatch.setattr(game.display, "display_map", record_map)
    monkeypatch.setattr(game.display, "any_to_continue", record_pause)
    monkeypatch.setattr(game.display, "timed_pause", record_timed_pause)

    game.execute_turn(computer, autopilot=False)

    assert any(action and "[COMPUTER TURN]" in action and "is thinking" in action for action in shown_actions)
    assert any(action and "[COMPUTER TURN]" in action and "played A1 and bought" in action for action in shown_actions)
    assert game.last_action.startswith(f"[COMPUTER TURN] {computer.name} played A1 and bought")
    assert len(timed_pause_calls) == 1
    assert len(pause_calls) == 1


def test_execute_turn_summary_mode_appends_ai_thinking_factors(game_factory, monkeypatch):
    game = game_factory(interactive=False, autopilot=False, number_of_players=2)
    game.interactive = True
    game.headless = False
    game.human_players = 1
    game.computer_players = 1
    game.ai_thinking_mode = "summary"
    game.players[0].is_computer = False
    game.players[1].is_computer = True

    computer = game.players[1]
    game.active_player = computer
    company = SimpleNamespace(symbol="T", name="Test Company", share_price=100)
    game.active_companies = OrderedDict([(company.symbol, company)])

    def fake_choose_move(_game, _player, legal_moves, capture_trace=False):
        assert capture_trace is True
        _game.ai_last_trace = {
            "selected_move": legal_moves[0],
            "selected_factors": ["merger +1300", "adjacent stars +500"],
        }
        return legal_moves[0]

    computer.ai_strategy = SimpleNamespace(
        choose_move=fake_choose_move,
        buy_stocks=lambda *_args, **_kwargs: None,
    )

    monkeypatch.setattr(game, "_get_legal_moves", lambda _map: ["A1", "B2", "C3", "D4", "E5"])
    monkeypatch.setattr(game, "play_move", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "pay_dividends", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "_auto_buy_stocks", lambda *_args, **_kwargs: "bought 1 share of Test Company")
    monkeypatch.setattr(game.display, "display_map", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game.display, "timed_pause", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game.display, "any_to_continue", lambda *_args, **_kwargs: None)

    game.execute_turn(computer, autopilot=False)

    assert "merger +1300" in game.last_action
    assert "adjacent stars +500" in game.last_action


def test_execute_turn_detailed_mode_keeps_thinking_in_map_flow(game_factory, monkeypatch):
    game = game_factory(interactive=False, autopilot=False, number_of_players=2)
    game.interactive = True
    game.headless = False
    game.human_players = 1
    game.computer_players = 1
    game.ai_thinking_mode = "detailed"
    game.players[0].is_computer = False
    game.players[1].is_computer = True

    computer = game.players[1]
    game.active_player = computer
    company = SimpleNamespace(symbol="T", name="Test Company", share_price=100)
    game.active_companies = OrderedDict([(company.symbol, company)])

    def fake_choose_move(_game, _player, legal_moves, capture_trace=False):
        assert capture_trace is True
        _game.ai_last_trace = {
            "strategy": "advanced",
            "selected_move": "A1",
            "selected_factors": ["merger +1300"],
            "ranked_moves": [
                {"move": "A1", "score": 1820.0, "factors": ["merger +1300"]},
                {"move": "B2", "score": 950.0, "factors": ["expansion +900"]},
            ],
            "selected_components": {
                "base_score": 1600.0,
                "immediate_delta": 90.0,
                "opponent_best": 340.0,
            },
        }
        return "A1"

    computer.ai_strategy = SimpleNamespace(
        choose_move=fake_choose_move,
        buy_stocks=lambda *_args, **_kwargs: None,
    )

    map_trace_snapshots = []

    def record_map(_player):
        map_trace_snapshots.append(game.ai_last_trace)

    monkeypatch.setattr(game, "_get_legal_moves", lambda _map: ["A1", "B2", "C3", "D4", "E5"])
    monkeypatch.setattr(game, "play_move", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "pay_dividends", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game, "_auto_buy_stocks", lambda *_args, **_kwargs: "bought 1 share of Test Company")
    monkeypatch.setattr(game.display, "display_map", record_map)
    monkeypatch.setattr(game.display, "timed_pause", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(game.display, "any_to_continue", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        game.display,
        "display_announcement",
        lambda *_args, **_kwargs: pytest.fail("detailed mode should not use announcement popups"),
    )

    game.execute_turn(computer, autopilot=False)

    assert game.ai_last_trace_player == computer.name
    assert any(snapshot for snapshot in map_trace_snapshots)


@pytest.mark.interactive
def test_constructor_interactive_mode_uses_fixture_local_responses(monkeypatch, scripted_input):
    instruction_calls = []
    continue_calls = []

    def record_instructions(self):
        instruction_calls.append(self.game.interactive)

    def record_continue(self):
        continue_calls.append(self.game.interactive)

    scripted_input("Y", "Ada", "Bob")
    monkeypatch.setattr(trade_objects.Display, "display_instructions", record_instructions)
    monkeypatch.setattr(trade_objects.Display, "any_to_continue", record_continue)

    game = Game(
        number_of_players=2,
        terminal=SimpleNamespace(clear=lambda: ""),
        max_turns=5,
        interactive=True,
        autopilot=False,
    )

    assert game.interactive is True
    assert game.autopilot is False
    assert instruction_calls == [True]
    assert continue_calls == [True]
    assert sorted(player.name for player in game.players) == ["Ada", "Bob"]