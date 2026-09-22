# CYCLE VERDICT — EURUSD-DATA-QUALIFICATION-V1

- Date (UTC): 2026-09-22
- A1 integration HEAD: `e49c23cff682ab15507651078f399dd48e9260d`
  (branch `orca/eurusd-data-qualification-v1-integration`)
- Plan: `plans/PLAN_eurusd_data_qualification_v1.md`
- Probe lane handoff: `handoffs/lane_source_probe_handoff.json`
  (`zcode_orch_v3_handoff@1`)
- A7 fresh-context audit: `audits/a7_probe_audit.{json,md}` —
  **`AUTHORIZED_BLOCKED_SOURCE_LICENSE`** (2026-09-22; 20 checks: 17 PASS /
  0 FAIL / 3 NOT_RUN correctly scoped to P2; license quotes re-fetched
  verbatim; all 242 raw sha256 recomputed 0 mismatches; independent decoder
  reproduces 578,916 ticks / 11,527 minutes / 0 dupes; scope + credential
  scans clean). Findings disposition: F1 MEDIUM handoff-shape — normalized
  by A1 at integration (substance verified); F2–F5 LOW — recorded, no
  action required; F3 dispatch-sha typo owned by A1 (see incidents).

## VERDICT: `BLOCKED_SOURCE_LICENSE`

Exactly one enum per plan §0a. The blocker is LICENSE, not data quality —
every technical gate of the bounded probe PASSED with evidence.

## Why (one paragraph)

Dukascopy's public datafeed served the bytes without any account or key,
but no terms document governs `datafeed.dukascopy.com`; the site TCU
(quoted verbatim in `probe/license_and_terms.md`) permits personal
non-commercial download and forbids automated acquisition without prior
express written consent plus database construction, and its applicability
to the datafeed host is unstated. Per CLAUDE.md ("free ≠ authorized",
fail-closed) and the plan §3 P1 gate, an unresolved license cannot ground a
research dataset. Twelve Data IS clear for internal research on the current
plan but exposes NO bid/ask (reconciliation-only), so it cannot substitute
as the bid/ask cost authority. No terms were accepted on anyone's behalf;
resolution requires an owner/legal decision.

## Gate census (P1 bounded probe, 2024-03-04 → 2024-03-14 UTC window)

| Gate | Result | Key evidence |
|---|---|---|
| LICENSE_RESOLVED (Dukascopy) | **FAIL** | `probe/license_and_terms.md` — UNCLEAR, verbatim TCU quotes |
| LICENSE (Twelve Data) | PASS | Internal-Use clause, quoted; but bid/ask absent on plan |
| SCHEMA_DECODED | PASS | 195/195 non-empty bi5 decoded (LZMA, `>5i`, price/1e5); 4/4 decode tests |
| TIMESTAMPS_UTC_UNAMBIGUOUS | PASS | epoch-ms UTC proven (07:00:00.089Z London first tick); TD bar-open labeling proven by alignment (0.35 vs 0.60 pips) |
| COVERAGE_CONTINUOUS_TRADING_HOURS | PASS | 99.542% minute coverage; 44 enumerated micro-gaps (1–3 min); weekend Fri 21:59Z → Sun 21:00Z measured, DST shift visible |
| FIELDS_SUFFICIENT_BIDASK (Dukascopy) | PASS | 578,916 ticks with bid+ask |
| FIELDS_SUFFICIENT (Twelve Data) | PARTIAL | OHLC only — no bid/ask, no volume on this plan |
| MULTI_YEAR_AVAILABLE | PASS | 2023 + 2025 boundary files decode, same schema |
| Indicative reconciliation | PASS (indicative) | median 0.35 pips, p95 1.15, max 42.65 (rollover) over 11,459 minutes |

## Stage-2 qualification: NOT_RUN (gated by plan §3 — probe did not PASS)

Consequently these plan requirements are NOT_RUN, not FAIL:
3–5 year immutable corpus; deterministic 15m/H1 bar build; weekend calendar
validation at scale; duplicate/monotonicity/OHLC-invariant/gap census at
scale; formal §2 preregistered tolerance test; **cost authority**
(spread p50–p99 by session, rollover, weekend, next-bar-open entry/exit,
1.5×/2.0× stress); data floor (≥192-bar warmup, ≥4 folds, ≥1,000 valid H1
decisions/fold); the §6 volume-identity decision (a) tick-activity proxy
with new feature identity vs (b) volume feature dropped — NOT_RUN; it
remains a MANDATORY preregistration for any future EURUSD Jev cycle.

## Boundary compliance

No Jev/TypeSafe call (0 by construction — no key use); no strategy, PnL,
backtest, orders, paper/live, MT5/OANDA repair, S1 access; no raw vendor
bytes committed (gitignored `data_local/`, sha256 manifest only); registry
touched only via `researchctl`. `EURUSD_DATA_QUALIFIED` was never claimed;
no profitability or edge statement exists in this cycle.

## Path to unblock (owner decision, not engineering)

1. Obtain a licensed bid/ask source: e.g., written Dukascopy consent for
   automated research retrieval, OR a Twelve Data plan tier with historical
   bid/ask, OR another licensed vendor. Then P2 resumes unchanged.
2. Note: with Twelve-Data-only (no bid/ask), even a passing coverage story
   ends at `BLOCKED_COST_AUTHORITY` by plan §4 law (no invented fixed
   spreads).

Successor/precondition law: any future EURUSD Jev cycle MUST first record
the §6 volume-identity decision before any Jev call or PnL.
