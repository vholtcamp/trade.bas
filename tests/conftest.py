import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import random
from types import SimpleNamespace

import pytest

import trade_objects
from trade_objects import EMPTY_SPACE, Game


@pytest.fixture(autouse=True)
def deterministic_random_seed():
    """Keep map generation and any shuffle operations deterministic in tests."""
    random.seed(10)


@pytest.fixture(autouse=True)
def safe_currency(monkeypatch):
    """Avoid locale-specific currency failures in non-interactive test environments."""
    monkeypatch.setattr(
        trade_objects.locale,
        "currency",
        lambda val, symbol=True, grouping=False, international=False: f"${val:,.0f}",
    )


@pytest.fixture
def game_factory():
    """Create isolated Game instances with explicit execution modes and no display side effects."""

    def _make_game(*, interactive=False, autopilot=True, number_of_players=2, max_turns=50):
        terminal = SimpleNamespace(clear=lambda: "")
        g = Game(
            number_of_players=number_of_players,
            terminal=terminal,
            max_turns=max_turns,
            interactive=interactive,
            autopilot=autopilot,
        )

        # Disable UI side effects for all unit tests.
        g.display.display_new_company = lambda *args, **kwargs: None
        g.display.any_to_continue = lambda *args, **kwargs: None
        g.display.display_map = lambda *args, **kwargs: None
        g.display.display_two_for_one = lambda *args, **kwargs: None
        g.display.display_merger = lambda *args, **kwargs: None

        # Build deterministic board states explicitly in tests.
        for coord in iter(g.map):
            g.map[coord] = EMPTY_SPACE

        return g

    return _make_game


@pytest.fixture
def scripted_input(monkeypatch):
    """Provide per-test stdin responses without disabling capture globally."""

    def _install(*responses):
        remaining = iter(responses)

        def fake_input(prompt=""):
            try:
                return next(remaining)
            except StopIteration as exc:
                raise AssertionError(f"unexpected input() call: {prompt}") from exc

        monkeypatch.setattr("builtins.input", fake_input)

    return _install


@pytest.fixture
def game(game_factory):
    """Default per-test game instance for concise test signatures."""
    return game_factory()


def clear_map(g):
    """Set every map square to EMPTY_SPACE for deterministic test setup."""
    for coord in iter(g.map):
        g.map[coord] = EMPTY_SPACE
