
# TRADE.BAS

![TRADE.BAS gameplay screenshot](docs/trade_screenshot.png)



A modern Python re‑implementation of the classic 1970s/80s BASIC trading game
originally distributed as `TRADE.BAS` on systems such as the Kaypro II.

This project preserves the core mechanics and feel of the original game while
making it easy to run and play on modern systems.

## Game Name

*Star Lanes* was the title used in the original 1977 *Interface Age* publication
by Steven Faber. `TRADE.BAS` is the filename of that listing, and the name most
commonly used when loading the game from floppy disk.

The name *Star Traders* appears in some later distributions and is used loosely
here to describe the genre. It should not be confused with the later RPG‑style
game of the same name, which involved specific ships and mission‑based trading.

## Quick Start

Requires **Python 3.8 or later**.  
**macOS and Linux only** — the game currently uses the `blessings` library, which depends on
`curses` and is not available on Windows.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate

```

2. Install dependencies.

```bash
python3 -m pip install -r requirements.txt
```

3. Run the game.

```bash
python3 trade_main.py
```

## Gameplay Summary

A tile-placement stock purchasing game: players place tiles on a grid to found companies, expand their territories, trigger mergers, and accumulate the highest net worth by game end.

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

## License

This project is licensed under the MIT License. See the LICENSE file for details.

The original BASIC source code and accompanying publication are included for historical reference. Their original copyright status is preserved.


