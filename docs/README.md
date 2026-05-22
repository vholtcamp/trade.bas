# docs/

This directory contains authoritative design and behavioral documentation for the Star Traders Python port.

## Files

### economic_model.md

Defines the behavioral contracts for the game economy. Covers:

- Share price and price quantum invariants
- Company creation and expansion pricing rules
- Stock split trigger and effects
- Merger resolution: player effects and company-level effects
- Dividend calculation rules
- Truncation semantics (GW-BASIC integer fidelity)

These contracts are the canonical reference for the test suite. If economic rules are intentionally changed, update this document and the tests together.

### strategy.md

Documents how computer players choose moves and buy stocks at Beginner, Intermediate, and Advanced difficulty levels, along with practical implications for human strategy.

### debug-econ.md

Explains the optional economic event logging hooks, event types, and recommended workflows for diagnostic runs.

## What Belongs Here

- Behavioral contracts and invariants
- Design intent documentation for non-obvious rules
- Notes on deviations from the original BASIC implementation

## What Does Not Belong Here

- Implementation notes tied to specific classes or methods (use inline docstrings)
- Test documentation (see tests/tests.md)
