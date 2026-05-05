
# TRADE.BAS

A modern Python re‑implementation of the classic 1970s/80s BASIC trading game
originally distributed as `TRADE.BAS` on systems such as the Kaypro II.
The dot in the name mirrors the original filename, a BASIC source file distributed with the Kaypro II.

This project preserves the core mechanics and feel of the original game while
providing a clean, testable, and extensible Python implementation.

## What This Project Is Not

- Not a clone of more complex games also named Star Traders. (The latter-day "Star Traders" were games with ship systems, fuel, or commodity trading.)

## Quick Start

Requires Python 3.8 or later.

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
- BASIC_code_files/: original BASIC source, preserved as reference. See BASIC_code_files/README.md.

## Known Behavioral Notes

- Compared to the original BASIC game, merger tie-break behavior has been adapted to company longevity (founded earlier wins ties) in the current implementation.
- Company creation and merger precedence are event-driven and tested.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

The original BASIC source code and accompanying publication are included for historical reference. Their original copyright status is preserved.


