# Z5 A6 audit notes — frozen family A4 implementation (schedule-only)

Lane: A6 / Z5 stocks-free-v2, family `A4_XSEC_ETF_RELATIVE_MOMENTUM`. Worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z5-family-1`,
branch `orca/stocks-free-v2-z5-family-1`, bootstrap `9124253` (identity
verified before any write: HEAD == bootstrap sha, branch matches, status
clean).

## Inputs read (read-only)

- `research/proposals/stocks_free_v2/a4_z3_relative_momentum_spec.json`
  (sha256 of exact file bytes `98d5307c…416fa`, re-verified) and its `.md`.
- `research/control/stocks_free_v2_run/selection_freeze.json` (A7 verdict
  `SELECTION_FREEZE_AUTHORIZED`; A4 `spec_sha256` matches; `o2_erratum`).
- `research/control/stocks_free_v2_run/partition.json`,
  `cohort_census.json` (digest `c9d4e88a…bc96`, 10 rankable sectors, SPY
  benchmark-only).
- `research/assets/stocks/calendar.py` imported read-only
  (`US_EQUITY_REGULAR_V1`, table `US_EQUITY_REGULAR_V1_TABLE_20260902`).

Not touched: family A5 files (A8's lane), control manifests, common
contracts, any historical artifact. No network, no API keys, no venv
creation; tests run offline on the mandated interpreter
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

## What was produced

- `research/stocks_free_v2/__init__.py`,
  `research/stocks_free_v2/family_a4/{__init__,signals,portfolio,schedule}.py`
  — one shared code path (features -> rank -> weight -> book) parameterized
  by `ArmConfig`; all three arms are configurations of that path. The
  negative control is the anchor with `ranking_sign` flipped and nothing
  else (enforced structurally by `control_differs_only_in_ranking_sign` and
  tested).
- Fail-closed spec parsing: 252/21/253/231, top-3, 35% cap and the 7 bps
  declaration are extracted from the frozen spec text by strict regexes; a
  drifted spec raises instead of silently re-freezing constants.
- `tests/stocks_free_v2/{__init__,}.py`,
  `tests/stocks_free_v2/family_a4/` — 45 offline tests, all passing
  (`python -m pytest tests/stocks_free_v2/family_a4 -q`), covering the
  mandated list: hand-computed features/selection/weights with literal
  arithmetic comments; one-event lag; no-lookahead mutation tests; raw-fill
  vs TR separation (distribution gap); ramp suppression (first 253 sessions
  -> no decisions); fold force-flat + counts vs partition; digest stability;
  double-generation equality; long-only/gross/cap/cash-residual invariants;
  expected-sign fixture (anchor selected legs beat unselected, control
  inverted).
- `research/audits/stocks_free_v2/z5_a6/digests.json` (this notes.md's
  sibling).

## Digests

- Frozen spec file-bytes sha256: `98d5307c3c3810a236f230475b190b34bd38461461cc7ea0a5ebdf38741416fa`.
- `arm_config_digest` (canonical sha256 over the parsed spec JSON, recorded
  in every `TargetBookStream`): `080c503f771cb020034238e41f340fa124f73a64ab413d2b6e23ea0b087d8468`.

## Schedule-derived counts and the recorded erratum

The frozen spec records expected S0 calendar slots fold1/2/3 = 20/28/29
(total 77). The A7 selection freeze (`o2_erratum`) already records:
"A4 fold-2 slot count 28 vs 29 derivable; totals 77 vs 78 - erratum, minima
unaffected (LOW, advisory)". The module derives counts from the frozen
calendar + spec folds and obtains exactly the erratum-corrected values:
20/29/29 = 78 valid monthly decisions (2019-01-31 .. 2025-06-30) plus the 9
declared warmup-extension slots 2018-04..2018-12 (suppressed, unscored).
Tests pin 20/29/29/78 and keep the spec-recorded 20/28/29/77 in the summary
under `spec_recorded_calendar_slots_s0` for transparency.

## Interpretation decisions (spec ambiguities, documented)

1. **Suppressed decisions** (readiness): while no symbol has the full
   253-session window, the slot exists but is suppressed — "no position
   change, unscored"; no book entry is emitted. Per-symbol holes after the
   ramp exclude the symbol from that ranking ("an ETF failing readiness is
   excluded from ranking that decision"), and fewer than 3 rankable names
   follow the spec's `partial_holdings` sentence.
2. **Partial holdings weighting**: the spec says "hold the rankable ones at
   equal (or inverse-vol) weight and put the residual in cash" without a
   size anchor; implemented deterministically as the arm's weighting scheme
   over the k names scaled to gross k/top_n (equal slots of 1/top_n),
   residual to cash — reduces exactly to the frozen full-book rules at
   k = top_n. Not expected to occur in S0.
3. **Sigma window**: "sample standard deviation of daily log TR returns over
   sessions [t-252, t-21] (… 231 daily observations)" is implemented as the
   231 log returns labelled sessions t-251..t-21 (232 window endpoints ->
   231 returns, ddof=1), matching the spec's count.
4. **Force-flat vs decision fills**: a decision whose fill lands exactly on
   a force-flat date fills at that session and is flattened at that
   session's close (fill entry strictly before the flat entry); the spec's
   example ("the 2025-06-30 decision fills 2025-07-01 and is flattened
   2025-07-24") is pinned by a test. The 2025-07-31 S0 terminal event finds
   the book already flat (no entry; recorded in the summary).
5. **Turnover convention**: one-way turnover = sum of |Δw| over ETF symbols
   (cash excluded; full 3-name rotation = 2.0, single-name change = 2/3,
   entry from flat = 1.0) — documented in the summary under
   `turnover_convention` for the Z6 feasibility check against the frozen
   6.0x ceiling. No cost is applied anywhere in this lane (schedule-only).
6. **Zero-sigma symbols** are excluded from the neighbour's mra ranking
   (fail-closed; undefined score); not expected in real data.

## Repair (Z6 integration feedback, convergent capped normalization)

Z6 integration hit a fail-closed raise from `normalize_capped` on real
staged inverse-vol inputs: the original per-pass loop recomputed the
"over-cap" set from current weights each pass and redistributed free mass
from raw across ALL uncapped names, including names pinned in earlier
passes — with concentrated 1/sigma inputs (shares ~{0.5, 0.3, 0.2} at cap
0.35) two names took turns exceeding the cap and the loop exhausted its
iteration budget (oscillation, never converged).

Fix: standard water-filling — a once-pinned name is frozen at the cap
forever (the pinned set only grows); each pass pins every unpinned name
whose proportional share exceeds the cap, redistributes `1 - pinned_mass`
among never-pinned names proportionally to raw, and iterates to the fixed
point; fail-closed if pinned mass exceeds 1.0 or the exact-sum check
fails. Fixed points are unique and order-independent. All pre-existing
hand cases are behavior-identical; regression tests pin the reported
inputs. One deviation from the integration request's literal example: the
quoted single-pass expectation `{0.5, 0.3, 0.2} -> {0.35, 0.39, 0.26}`
contains a 0.39 weight that would breach the frozen constraint
"per-ETF weight cap 35% of gross for all arms"; under the mandated
convergent algorithm the second name pins at the cap and the fixed point
is `{0.35, 0.35, 0.30}` for both requested regression inputs.
