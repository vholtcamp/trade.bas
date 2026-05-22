# docs/

This directory is for diagnostic tooling and recipes used during development and economic debugging.

## Economic Event Logging

The engine has opt-in economic event logging controlled at game startup via the `debug_econ` argument passed to `Game(...)` in `trade_main.py`.

The log destination constant lives in `trade_objects.py`:

```python
ECON_LOG_FILE = 'econ_events.log'
```

When enabled, one structured JSON line is written per economic event to `ECON_LOG_FILE`.

### Enabling Logging

Set `debug_econ=True` in the `Game(...)` call in `trade_main.py`, then run the game or any harness normally. Log output will appear in `econ_events.log` at the repository root.

Default behavior in the current entrypoint keeps this disabled (`debug_econ=False`).

### Logged Events

| Event type | Hook point |
|---|---|
| `company_creation` | `Company.apply_creation` |
| `company_expansion` | `Company.apply_expansion` |
| `merger_player_effects` | `Company.apply_merger_player_effects` |
| `merger_company_effects` | `Company.apply_merger` |
| `stock_split` | `Company.split_stock` |
| `dividend_payout` | `Game.pay_dividends` |
| `stock_purchase` | `Player.buy_stocks` |

### Log Line Shape

Each line is a JSON object with:

```json
{
  "turn": 3,
  "event_type": "company_expansion",
  "company_symbols": ["A"],
  "players": [],
  "before": {
    "companies": {
      "A": {"share_price": 800, "price_quantum": 100, "total_shares": 5}
    }
  },
  "after": {
    "companies": {
      "A": {"share_price": 1300, "price_quantum": 100, "total_shares": 5}
    }
  },
  "details": {"adjacent_stars": 1, "adjacent_outposts": 0}
}
```

### Running a Full Diagnostic Game

A non-interactive full-game harness can be used to produce a complete economic log without requiring terminal input. You can combine `debug_econ=True` with non-interactive execution modes for CI or local diagnostics.

## Notes

- Logging is diagnostic only and does not affect game logic or outcomes.
- Log files should not be committed to the repository.
- Disable `debug_econ` in startup configuration before sharing or distributing the code.
