
# TRADE.BAS

A modern Python re‑implementation of the classic 1970s/80s BASIC trading game
originally distributed as `TRADE.BAS` on systems such as the Kaypro II.
The dot in the name mirrors the original filename, a BASIC source file distributed with the Kaypro II.

This project preserves the core mechanics and feel of the original game while
providing a faithful Python implementation.

## Game Name

*Star Lanes* was the title used in the original 1977 *Interface Age* publication; `TRADE.BAS` is the filename of that listing, and most commonly used when loading the game from a floppy disk. The name *Star Traders* appears in some later distributions and is used loosely here to describe the genre of game, though *Star Traders* itself was a different game that was more RPG-like, with specific ships and trading missions originally based on arbitrage pricing of fictional space-faring commodities.

## Quick Start

Requires Python 3.8 or later. Mac and Linux only — `blessings` depends on `curses`, which is not available on Windows.

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

## Gameplay Summary

A tile-placement stock trading game: players place tiles on a grid to found companies, expand their territories, trigger mergers, and accumulate the highest net worth by game end.

- The map is a 9x12 grid (A-L columns, 1-9 rows).
- Each turn offers 5 legal moves.
- Moves can create outposts, found companies, expand companies, or trigger mergers.
- Dividends are paid before purchases each turn.
- Stock splits occur when share price crosses the split threshold.
- The game winner is the player with highest net worth at game end.

For detailed economic contracts and invariants, see docs/economic_model.md.

## Running Tests

From repository root:

```bash
python -m pytest -q
```

Pytest discovery is restricted by pytest.ini to the tests directory.

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


