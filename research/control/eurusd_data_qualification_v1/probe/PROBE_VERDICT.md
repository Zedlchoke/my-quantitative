# PROBE VERDICT — EDQ1 P1 bounded probe

Cycle: EURUSD-DATA-QUALIFICATION-V1 · Lane: eurusd-source-qualification · 2026-09-22

## VERDICT: PROBE_FAIL

**Failed gate: `LICENSE_RESOLVED`** — the Dukascopy public datafeed license is
UNCLEAR (see `license_and_terms.md`). All technical gates PASSED; the block is
legal/provenance, not engineering. Per plan §3 P1, a failed probe gate maps to
the cycle candidate verdict `BLOCKED_SOURCE_LICENSE` (final enum lands at P3).
No full-history download may proceed (plan §0a: "Không full-history nếu
license/schema chưa rõ").

**Not** a verdict of "license forbidden": this lane did not and will not
accept terms on anyone's behalf. Resolution requires owner action — obtain
Dukascopy's prior express written consent, or an owner legal decision on the
TCU-vs-datafeed question. Engineering work was completed so that a license
clearance can immediately unblock P2.

## Gate table

| Gate | Verdict | Key numbers |
|---|---|---|
| LICENSE_RESOLVED | **FAIL** | Dukascopy UNCLEAR; Twelve Data CLEAR_FOR_INTERNAL_RESEARCH |
| SCHEMA_DECODED | PASS | 195/195 non-empty files decode (`'>5i'` LZMA); scale int/1e5 proven (1.08377–1.09815 = real Mar-2024 range) |
| TIMESTAMPS_UTC_UNAMBIGUOUS | PASS | epoch-ms UTC offsets in-hour; London-0700 sanity tick = 07:00:00.089Z; weekend 2820 min measured; TD bar-open labeling proven (A 0.35 vs B 0.60 pips) |
| COVERAGE_CONTINUOUS_TRADING_HOURS | PASS | 99.542% of trading-span minutes (11,527/11,580); 44 micro-gaps 1–3 min enumerated (53 min, max 3); weekend closure exactly 47 h; 0 dupes; 0 monotonicity violations |
| FIELDS_SUFFICIENT_BIDASK (Dukascopy) | PASS | per-tick ask+bid; spread median 0.2 pips, 0 non-positive; volume ints = tick_activity_proxy only |
| FIELDS_SUFFICIENT (Twelve Data) | PASS (reconciliation role only) | 1min OHLC UTC, 11,509 bars; **no bid/ask, no volume on this plan** → cannot be cost authority |
| MULTI_YEAR_AVAILABLE | PASS | 2023-06-15 file (3,629 ticks, ~1.082–1.084) and 2025-06-13 file (5,092 ticks, ~1.153–1.155) decode with same schema |

## Key numbers

- Dukascopy: 242 targets → 195 non-empty (200), 47 empty weekend hours (200,
  0 bytes), **0 × HTTP 404**, 0 failures; **578,916 ticks**; 11,527 distinct
  1-min bars.
- Twelve Data: 3 paginated requests (≤8/min), 11,509 unique 1-min bars, 0
  duplicates, 12 internal gaps; requests/URLs recorded redacted of `apikey`.
- Indicative reconciliation (TD 1-min close vs Duka tick-mid close, 11,459
  minutes): median |Δ| **0.35 pips**, p95 1.15, max 42.65. INDICATIVE ONLY —
  the formal §2 tolerance test is P2.

## What would flip this verdict

1. `LICENSE_RESOLVED` → PASS via documented Dukascopy written consent or owner
   legal clearance recorded in the cycle. Technical evidence is already
   probe-grade.
2. Only then: P2 full download (3–5 y) under the heavy lock per plan §3.

## Machine-readable

`probe_verdict.json` (schema `edq1_probe_verdict@1`) — authoritative form of
this verdict.
