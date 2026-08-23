# Capture the untouched future holdout

**Type:** task  
**Status:** open  
**Blocked by:** none

## Question

What newly captured period can serve as S1 after all candidate parameters are
locked, without reusing the already inspected S0 bars?

## Decision needed

Record the lock timestamp, capture manifest, symbol universe, and at least six
chronological OOS folds (or a predeclared low-frequency exception) before any
promotion decision.

## Evidence to collect

- a post-lock bar range with no overlap in the scored S0 window;
- complete funding coverage for every closed position and the same fee/slippage
  model as the screening run;
- immutable output hashes and a run manifest before results are inspected.
