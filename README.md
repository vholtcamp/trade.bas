# Star Traders (TRADE.BAS Python Port)

This repository is a Python port of the original GW-BASIC Star Traders game.

The project currently focuses on preserving classic economic behavior while modernizing the implementation for testing and refactoring.

## What This Project Is

- A rule-faithful Python implementation of the original game loop and economy.
- A test-backed refactor target for core game rules.
- A terminal game using blessings for display.

## What This Project Is Not

- Not a clone of more complex games also named Star Traders. (The latter-day "Star Traders" were games with ship systems, fuel, or commodity trading.)

## Quick Start

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Run the game.

```bash
python trade_main.py
```

## Running Tests

From repository root:

```bash
python -m pytest -q
```

Pytest discovery is restricted by pytest.ini to the tests directory.

## Economic Event Logging (Diagnostic Only)

Economic event logging is built into the engine as opt-in diagnostics.

Configuration lives in trade_objects.py:

- DEBUG_ECON = False
- ECON_LOG_FILE = "econ_events.log"

When DEBUG_ECON is False:

- no economic log output is produced
- game behavior is unchanged
- logging code paths are skipped

When DEBUG_ECON is True:

- one structured JSON line is emitted per economic event
- output is written to ECON_LOG_FILE

Logged event categories:

- company creation
- company expansion
- merger player effects
- merger company effects
- stock split
- dividend payout
- stock purchase

Important: this logging is diagnostic infrastructure, not gameplay logic, and can be removed without changing economic rules.

## Gameplay Summary

- The map is a 9x12 grid (A-L columns, 1-9 rows).
- Each turn offers 5 legal moves.
- Moves can create outposts, found companies, expand companies, or trigger mergers.
- Dividends are paid before purchases each turn.
- Stock splits occur when share price crosses the split threshold.
- The game winner is the player with highest net worth at game end.

For detailed economic contracts and invariants, see docs/economic_model.md.

## Project Layout

- trade_main.py: terminal entry point and top-level loop.
- trade_objects.py: core domain model (Game, Company, Player, Map, Display).
- tests/: rule-focused pytest suite. See tests/README.md.
- docs/: behavioral contracts and invariants. See docs/README.md.
- diagnostics/: economic logging recipes and event log reference. See diagnostics/README.md.
- BASIC_code_files/: original GW-BASIC source, preserved as reference. See BASIC_code_files/README.md.
- archives/: legacy scripts and experiments, not part of the active codebase. See archives/README.md.
- smoke_checklist.md: manual runtime smoke checklist.

## Known Behavioral Notes

- Compared to the original BASIC game, merger tie-break behavior has been adapted to company longevity (founded earlier wins ties) in the current implementation.
- Company creation and merger precedence are event-driven and tested.

## Development Notes

- Keep rule changes synchronized across code, tests, and economic model docs.
- Prefer invariant-based tests over UI assertions.
- Avoid introducing UI dependencies in rule-engine tests.
