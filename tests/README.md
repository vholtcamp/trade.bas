# Test Suite README

This directory contains the pytest suite for the Python port of STAR TRADERS.

The suite is intentionally rule-focused and behavior-driven. It is designed to lock down game logic and invariants before refactoring, while avoiding UI/terminal concerns.

The test suite reflects behaviors observed in the original GW‑BASIC TRADE.BAS implementation and its implicit integer arithmetic rules.

## Goals

- Protect historically faithful gameplay rules.
- Assert behavior and invariants, not implementation details.
- Keep tests deterministic and fast.
- Avoid terminal output, blessings display logic, and input-driven flows.

## Test Design Rules

- Tests instantiate and manipulate `Game`, `Company`, `Player`, and `Map` state directly.
- Most tests avoid full gameplay flow; only targeted execution-mode smoke tests call `execute_turn()`.
- Numeric rule assertions use game constants from `trade_objects.py` whenever applicable.
- Randomness is controlled by fixture seeding and explicit board setup.
- Pricing tests rely on the price_quantum invariant rather than hard-coded monetary units.

## Directory Layout

- `conftest.py`: shared fixtures and environment guards.
- `rule_helpers.py`: thin setup/action helpers for concise, readable tests.
- `test_company_creation.py`: company founding and creation-precedence behavior.
- `test_expansion_and_splits.py`: expansion pricing, split behavior, and quantum-change rules.
- `test_mergers.py`: merger trigger conditions, winner selection, pricing/quantum effects, and player conversion/bonuses.
- `test_integration_invariants.py`: “Integration” tests here still operate at the rule-engine level and intentionally avoid UI or full gameplay loops.

## Running the Suite

From repository root:

```bash
python -m pytest -q
```

Pytest discovery is constrained by `pytest.ini`:

```ini
[pytest]
testpaths = tests
```

This prevents legacy scripts outside `tests/` from being collected as tests.

## Fixtures and Determinism

`conftest.py` provides:

- `deterministic_random_seed` (autouse): seeds randomness for stable map/player order behavior.
- `safe_currency` (autouse): monkeypatches `trade_objects.locale.currency` to avoid locale-specific failures (for example, C locale in non-interactive environments).
- `game_factory`: builds isolated `Game` instances with explicit `interactive`/`autopilot` flags, display methods stubbed to no-op, and a cleared map.
- `scripted_input`: installs fixture-local `input()` responses for isolated `@pytest.mark.interactive` tests.
- `game`: default per-test game instance.

## Thin Rule Helper Layer

`rule_helpers.py` keeps tests short and intention-revealing:

- `place_outpost(game, coord)`
- `place_star(game, coord)`
- `found_company(game, player, coord)`
- `play(game, player, coord)`
- `only_active_company(game)`
- `all_companies_obey_price_quantum(game)`

These helpers are intentionally thin orchestration wrappers that call production code directly; they do not duplicate or reimplement game logic.

## Platform-Specific Test Behavior

### Windows

The `blessings` terminal library (which relies on `curses`) is not available on Windows. Tests for `BlessingsTerminal` are automatically skipped via `@pytest.mark.skipif(not BLESSINGS_AVAILABLE, ...)` decorators in `test_terminal_backends.py`.

### Unix-like Systems (Linux, macOS)

All terminal backend tests run. The `colorama` dependency specified for Windows is ignored.

## Coverage Map (Current)

### Company Creation

- Opening share price uses:
  - `STARTING_SHARE_PRICE`
  - founding square `OUTPOST_BONUS`
  - adjacent outpost `OUTPOST_BONUS`
  - adjacent star `STAR_BONUS`
- New company creation does not occur when move touches an existing company (expansion precedence).

### Company Expansion

- Base `OUTPOST_BONUS` increment always applies.
- Adjacent stars/outposts are absorbed per current rules.
- Post-expansion invariant: `share_price % price_quantum == 0`.

### Stock Splits

- Trigger when crossing `TWO_FOR_ONE_PRICE` threshold.
- `share_price` and `price_quantum` both halve.
- Holdings double for each player.
- Post-split `share_price < TWO_FOR_ONE_PRICE`.
- `price_quantum` does not increase.

### Mergers

- Trigger only when newly played square touches two or more companies orthogonally.
- Existing adjacency alone does not trigger a merger.
- Winner selection follows current size and tie-break behavior.
- Pricing effects include additive share price, minimum quantum adoption, and quantum truncation.
- Player share conversion and cash bonuses align with current merger rules (`MERGER_BONUS`).

### Price and Quantum Invariants

- Active-company invariant maintained: `share_price % price_quantum == 0`.
- Quantum baseline and split-only change behavior checked.

### Integration Sanity

- Forced sequence regression:
  - create -> expand -> split -> merge -> expand
- Invariants remain true at each phase.

### Execution Modes

- Non-interactive construction does not call `input()` or display instructions.
- `any_to_continue()` is a no-op when `interactive=False`.
- Autopilot turns do not prompt for stock purchases.
- Manual decision mode still routes stock buying through the prompt path.
- Interactive constructor coverage uses `@pytest.mark.interactive` with fixture-local stdin responses rather than global capture changes.

## When Tests Fail

Because tests assert invariants rather than UI output, failures usually indicate
a real rule violation rather than a cosmetic issue. Investigate rule ordering,
price quantization, or state transitions before adjusting expected values.

## Notes

- Some assertions intentionally reflect current implementation behavior to prevent regression before refactoring.
- If game rules are intentionally changed later, update tests and this README together to keep the suite as the authoritative behavior contract.

## Economic Event Logging (Diagnostic Only)

Economic event logging is built into the engine as opt-in diagnostics.

Configuration lives in `trade_objects.py`:

- `DEBUG_ECON = False`
- `ECON_LOG_FILE = "econ_events.log"`

When `DEBUG_ECON` is `False`:

- no economic log output is produced
- game behavior is unchanged
- logging code paths are skipped

When `DEBUG_ECON` is `True`:

- one structured JSON line is emitted per economic event
- output is written to `ECON_LOG_FILE`

Logged event categories:

- company creation
- company expansion
- merger player effects
- merger company effects
- stock split
- dividend payout
- stock purchase

This logging is diagnostic infrastructure, not gameplay logic, and can be removed without changing economic rules.
