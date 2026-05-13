
# TRADE.BAS

![TRADE.BAS gameplay screenshot](docs/trade_screenshot.png)



A modern Python re‑implementation of the classic 1970s/80s BASIC game
originally distributed as `TRADE.BAS` on systems (such as the Kaypro II).

This project preserves the core mechanics and feel of the original while
making it easy to run and play on modern systems.

## Game Name

*Star Lanes* was the title used in the original 1977 *Interface Age* publication
by Steven Faber. `TRADE.BAS` is the name most commonly used when loading the game from floppy disk.

*[Star Traders](https://en.wikipedia.org/wiki/Star_Trader)* is an alternate name applied to the game at times, though the original *Star Traders* was a more-RPG style space-trading adventure, which spawned multiple variations and descendents. 

## Gameplay Summary

A tile-placement stock purchasing game for 1 - 4 players. Players place tiles on a grid to found companies, expand their territories, trigger mergers, and accumulate the highest net worth by game end.

- The map is a 9x12 grid (A-L columns, 1-9 rows).
- Each turn offers 5 legal moves, chosen at random by the computer.
- Moves can create outposts, found companies (if an outpost is placed next to another outpost or a star), expand companies (if placed next to an existing company), or trigger mergers (if two or more companies will be connected by the new placement).
- Dividends - fixed at 5% of the stock's share value - are paid before purchases each turn.
- Stock splits occur when share price crosses the split threshold (original set at $3000).
- The number of turns depends on the number of players - solo play is 49 turns, two players will have 24 turns, three players will have 16, and four players will have 12.
- The winner is the player with highest net worth at the end.


## A few updates from the original...

- *Mergers*: In the original, if two companies were merging and they were tied in terms of outposts, the company alphebetically first would win. I have tweaked this so that the oldest company comes out on top.

- *Colors:* While the original incarnations of the game would all have been in monochrome, this version does use a colorized mode as default, where company symbols and names are rendered in color. (See above for how to tweak color modes to match your preferred retro nostalgia scheme.)

- *Display:* The original version printed only the map each turn, with a special command to display a player's portfolio. This version adds an updated portfolio to the right of the map, so there is no "Display Portfolio" or "Display Map" command. Similarly, the stock purchasing display is tweaked to confirm the previous purchase (or lack thereof) for player reference. 




## Quick Start

Requires **Python 3.11 or later**.

**Platform Support:**
- **Linux and macOS**: Use the `blessings` terminal backend (full color and formatting support via curses)
- **Windows**: Use the Windows terminal backend with `colorama` for color support (ANSI emulation)

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

## Runtime Flags and Environment Variables

### Command-Line Arguments

- `--monochrome`: Disable ANSI color output. Useful for terminals with limited color support.
  ```bash
  python3 trade_main.py --monochrome
  ```

- `--color-scheme {default,green,amber,white}`: Select a color scheme. Retro terminal themes are available (`green`, `amber`, `white`).
  ```bash
  python3 trade_main.py --color-scheme amber
  ```

### Environment Variables

- `TRADE_HEADLESS`: Set to `1`, `true`, or `yes` to run in headless (non-interactive) autopilot mode. The game will run all turns automatically without waiting for user input. Used in CI testing.
  ```bash
  TRADE_HEADLESS=1 python3 trade_main.py
  ```

## Running Tests

Interested in modifying the game? Here is the key info on the current testing suite:

From repository root:

```bash
python -m pytest -q
```

Pytest discovery is restricted by `pytest.ini` to the tests directory.

**Platform-Specific Notes:**
- On Windows, tests for the `blessings` terminal backend are automatically skipped (blessings requires curses, which is unavailable on Windows).
- On Unix-like systems, the Windows terminal backend tests run normally.
- All platform-specific test skips are controlled by `@pytest.mark.skipif` decorators in the test files.

## Project Layout

- `trade_main.py`: terminal entry point and top-level loop.
- `trade_objects.py`: core domain model (Game, Company, Player, Map, Display).
- `terminal/`: platform-specific terminal backends (Windows and Blessings for Unix-like systems).
- `tests/`: rule-focused pytest suite. See [tests/README.md](tests/README.md).
- `docs/`: behavioral contracts and invariants. See [docs/README.md](docs/README.md).
- `BASIC_code_files/`: original BASIC source, preserved as reference. See [BASIC_code_files/README.md](BASIC_code_files/README.md).
- `diagnostics/`: economic event logging and debugging tools. See [diagnostics/README.md](diagnostics/README.md).



## License

This project is licensed under the MIT License. See the LICENSE file for details.

The original BASIC source code and accompanying publication are included for historical reference. Their original copyright status is preserved.


