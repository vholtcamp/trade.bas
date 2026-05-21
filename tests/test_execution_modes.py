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
    assert game.last_action.startswith("Autopilot purchased")


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
    assert game.last_action.startswith("Autopilot purchased")


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