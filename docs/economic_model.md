
***

# Economic Contracts (v1.0)

This document describes the **economic behavior contracts** for the Python port of **STAR TRADERS (TRADE.BAS)** as of the current stable implementation.

These contracts define *what must remain true* during refactoring.  
They are enforced by the test suite and reflect both explicit and implicit rules of the original GW‑BASIC game.

***

## Scope and Purpose

*   This document describes **economic rules only**: pricing, splits, mergers, dividends, and invariants.
*   UI behavior, map generation, and turn presentation are explicitly out of scope.
*   These contracts are intended to be **behavioral**, not tied to specific code structure.

Refactoring is permitted as long as these contracts remain satisfied.

***

## Core Economic Concepts

### Share Price

*   Every company has a `share_price`, an integer value.
*   All economic operations ultimately modify `share_price` via addition, halving, or truncation.
*   Fractional prices do not persist beyond an economic step.

### Price Quantum

*   Every company has a `price_quantum`, representing the smallest valid unit of its price.
*   The price quantum governs valid pricing states and truncation rules.
*   The invariant
        share_price % price_quantum == 0
    must hold at all times for every active company.

***

## Company Creation

When a new company is founded:

*   Initial `share_price` starts at:
        STARTING_SHARE_PRICE
*   The following additions apply:
    *   `OUTPOST_BONUS` for the founding square itself
    *   `OUTPOST_BONUS` for each adjacent outpost absorbed
    *   `STAR_BONUS` for each adjacent star absorbed
*   Initial `price_quantum` is:
        STARTING_SHARE_PRICE
*   Founding player receives `FOUNDERS_BONUS_SHARES`.

### Creation Precedence Rule

*   **A new company may not be created adjacent to an existing company.**
*   If a placed square is adjacent (orthogonally) to exactly one company, it expands that company instead.
*   Creation only occurs when no adjacent companies exist.

***

## Company Expansion

When a company expands into a new square:

*   Pricing effects apply in the following order:
    1.  Base increment: `OUTPOST_BONUS` (always applies)
    2.  `OUTPOST_BONUS` per absorbed outpost
    3.  `STAR_BONUS` per absorbed star
*   Expansion always takes precedence over company creation.
*   After expansion pricing:
    *   Stock splits are checked and applied if triggered.
    *   Share price is truncated to the current `price_quantum`.

***

## Stock Splits

### Trigger Condition

*   A 2‑for‑1 split is triggered when:
        previous_price < TWO_FOR_ONE_PRICE
        and
        share_price >= TWO_FOR_ONE_PRICE

### Split Effects

When a split occurs:

*   `share_price` is updated via integer division:
        share_price = share_price // 2
*   `price_quantum` is halved:
        price_quantum = price_quantum // 2
*   Each player’s holdings in the company double.
*   After the split:
        share_price < TWO_FOR_ONE_PRICE
*   `price_quantum` never increases once reduced.

***

## Mergers

### Merger Trigger Condition

*   A merger occurs **only** when the newly placed square is adjacent (N/S/E/W) to **two or more different companies**.
*   Existing adjacency elsewhere on the board never triggers a merger.
*   Mergers are event‑driven, not state‑driven.

***

### Merger Resolution

*   Companies involved in a merger are resolved iteratively until one survives.
*   Winner selection is based on:
    1.  Larger company size
    2.  Tie‑break rules as currently implemented (e.g., founding order)

***

### Player Effects of a Merger

Player-facing effects occur **before** company-level price aggregation or truncation.

For each player:

*   Shares in the losing company are converted 2‑for‑1, rounded:
        new_shares = int((old_shares / 2) + 0.5)
*   Cash bonus is awarded based on ownership percentage:
        MERGER_BONUS * (player_shares / total_shares) * losing_company.share_price
*   The bonus calculation uses the **losing company’s share price at merger time**, prior to truncation.

***

### Company Effects of a Merger

After player effects:

*   Surviving company’s `share_price` increases additively:
        share_price += losing_company.share_price
*   `price_quantum` converges to the smaller (finer) quantum:
        price_quantum = min(winner.price_quantum, loser.price_quantum)
*   Stock split is checked and applied if triggered.
*   Share price is truncated to `price_quantum`.

***

## Dividends

*   Dividends are paid per player after each completed turn.
*   For each company:
        dividend = int(DIVIDEND_MULTIPLIER * shares_owned * share_price)
*   Dividends are integer-truncated.
*   Dividend calculations do not modify company prices or price quantum.

***

## Truncation Rule (Global)

To faithfully mirror GW‑BASIC integer semantics:

*   After any economic step that modifies `share_price`:
    *   creation
    *   expansion
    *   merger aggregation
*   The following truncation applies:
        share_price = (share_price // price_quantum) * price_quantum

This ensures that no fractional price history propagates across turns.

***

## Global Invariants

At all times, for every active company:

*   `share_price` is an integer
*   `price_quantum` is an integer
*   `price_quantum` > 0
*   `share_price % price_quantum == 0`
*   `price_quantum` can only change via stock splits
*   `price_quantum` never increases

These invariants are enforced by the test suite.

***

## Contract Stability

These economic contracts define the authoritative behavior of the current engine version.

If rules are intentionally changed in the future (e.g., for a variant or fork):

*   Update this document
*   Update the test suite
*   Update both together

The tests and this document are designed to evolve in lockstep.

***

