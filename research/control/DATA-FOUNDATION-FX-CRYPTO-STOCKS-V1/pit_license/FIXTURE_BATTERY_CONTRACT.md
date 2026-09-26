# FIXTURE_BATTERY_CONTRACT.md — named PIT/quality fixture battery (draft for A1 freeze)

Cycle: DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 · Lane: L-PIT · 2026-09-26.
Plan §7 requires: "Fixture battery (each gets a named synthetic test design;
existing battery inventoried first — many already exist from EURUSD/CHR3F
cycles)". This file inventories the EXISTING implementations first (found by
searching `tests/` and `research/control/**` incl. evidence branches), then
pins each battery entry as EXISTS / PARTIAL / DESIGN-ONLY. All designs are
synthetic and hand-computable by construction. Law anchors: P-18
(truncation-proof standard), L-TRACKB1-1, L-SAMV1-1, L-SAMV1-3 (LESSONS.md).

---

## F-1. future_leak_truncation_replay — EXISTS (executed, multiple planes)

Design: replay the exact scored code on a panel truncated at each decision
point and diff against full-panel output; any difference at a decision
timestamp that uses post-`t` bytes = leak. Strongest form (ERP1 M-5): the
leaky twin MUST differ, the PIT-clean anchor MUST be byte-identical.

Existing implementations:
- `research/control/EURUSD-OPEN-SEARCH-V1/scripts/test_engine_fixtures.py::test_pit_truncation_invariance` (branch `orca/eurusd-open-search-v1-integration`).
- ERP1 F-PIT-1 M-1..M-5 designs (`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/SKEPTIC_cohort1_REPORT.md` §1.2); executed: cohort 1 (M-2 non-vacuity PASS 22.99%/20.38%; M-3 daemon seam 43.0%/63.4%), TrackB cohort 1 ("PIT battery M-1..M-5 ALL PASS (318/318 truncation replay byte-identical, P-18)"), cohort 2 ("generic PIT battery harness (pit_battery2, leak-catch proven)", F-2 PASS_PIT 4/4).
- EOSV2 RUN-1 voided pre-selection when extended truncation fixtures caught a look-ahead bug (ledger EURUSD-OPEN-SEARCH-V2 row).
- SRLV-CX-C1 pre-scoring fixtures ("truncation 0/512, mutation 0/25").

## F-2. revision_restatement_detection — PARTIAL

Design: synthetic macro series where a value changes retroactively (vintage
N+1 rewrites history); a PIT reader keyed at decision time `t` must see the
vintage that was live at `t`, and an append of a later pull with different
content at equal rank must be refused; in-place-revised tables must be
detectable (current-vintage vs vintage-dated channels disagree).

Existing implementations:
- `tests/data_fusion/test_pit.py` — `test_later_revision_does_not_leak_backward`,
  `test_vintage_series_is_append_only`,
  `test_vintage_series_never_overwrites_a_filled_rank`,
  `test_df_issue2_append_refuses_later_pull_with_different_content`,
  `test_effective_date_is_enforced`.
- NY Fed `revisionIndicator` machine-served field (FDF-V1 summary; row 11
  ruling) is the live-data counterpart.
- GAP (DESIGN-ONLY): an explicit retro-restatement fixture for the
  in-place-revised channel class discovered in FOREX-NG2 ("GB revision
  stream is 60/68 one bulk 2018 re-referencing coefficient") and the V9
  binding ("GB/CA legs on current-vintage revised-in-place tables are
  forbidden — vintaged channel mandatory") — no generic fixture name carries
  this law yet.

## F-3. dst_boundary — PARTIAL

Design: synthetic session-bar stream spanning a DST transition (spring
forward: a wall-clock hour that does not exist; fall back: an hour that
occurs twice); stamps must remain UTC-unique, session labels must follow the
exchange calendar, and any wall-clock-derived feature must not double-count
or skip the transition hour.

Existing implementations:
- `tests/platform_v3/test_calendar_engine.py` — session manifests, early
  close, US-federal-vs-exchange holiday difference, lunch break,
  `test_official_discrepancy_fails_closed` (day-granularity session layer).
- GAP (DESIGN-ONLY): an intraday bar-stamp DST fixture (FX/stocks
  intraday seam; the FOREX-V5 "CA ET-as-UTC stamp labeling" carry is the
  recorded hazard class). No named intraday DST fixture exists.

## F-4. symbol_identity_change — EXISTS

Design: alias timeline where a symbol is renamed/delisted/reassigned; the
identity store must expire historical aliases, refuse to project current
aliases backward, and fail closed on overlapping conflicting aliases.

Existing implementations:
- `tests/data_fusion/test_identity.py` — `test_current_alias_is_not_projected_backward`,
  `test_historical_alias_expires`, `test_overlapping_conflicting_aliases_fail_closed`.
- Executed identity-quarantine law — STOCKS-AMIHUD-RETEST-V1: "ticker≠identity
  quarantine law + census, both-direction split/extreme-print fixture law,
  fill-feasibility execution law — the data-plane template for every future
  EODHD single-name cycle" (645 codes removed; BYON/OSTK shared-ISIN
  replicas; HTV/NLG ghost series). Root cause classes C1-C7 recorded in
  SAMV1 terminal_forensics (ledger row).

## F-5. duplicate_missing_bar — EXISTS

Design: inject exact duplicates (same event id and same identity tuple) and
delete bars inside a declared window; duplicates must be
detected/deduped (`DUPLICATE_EVENT`, idempotent re-append of identical
bytes), and missing bars must stay missing and be COUNTED — never
interpolated, forward-filled, or venue-cross-substituted.

Existing implementations:
- `research/market_data_plane/quality.py` — `DUPLICATE_EVENT`,
  `SEQUENCE_GAP`, `MANIFEST_MISMATCH` under `CONTIGUOUS` sequence semantics;
  `DedupeIndex`.
- `tests/test_mdp_bars.py::test_time_order_strict_fail_closed`.
- data_fusion idempotency — `test_vintage_series_reappend_of_identical_bytes_is_idempotent`.
- The missing-is-missing law (normative text) — cng4 freeze field 13 adopted
  by DEU Lane C: "missing bars/cells stay missing and are COUNTED; no
  interpolation, no forward-fill, no venue-cross substitution, no synthetic
  reconstruction — ever".
- US realtime CPI duplicate dedupe measured in FOREX-NG2 (481 duplicate rows).

## F-6. quote_crossed_stale — EXISTS

Design: synthetic quote stream with (a) bid>ask prints, (b) quotes older
than the staleness threshold at application time; crossed quotes must be
rejected with a reason code and stale quotes must fail the apply — with the
staleness boundary tested exactly at the threshold.

Existing implementations:
- `research/market_data_plane/quality.py` — `CROSSED_QUOTE`, `STALE_QUOTE`
  (and `IMPOSSIBLE_TIME_ORDER`).
- `tests/test_mdp_bbo.py` — `test_venue_local_staleness_boundary_exact`,
  `test_staleness_threshold_is_required_no_default`,
  `test_venue_local_out_of_order_apply_is_ignored`.
- Measured census counterpart — PWS-CX-SOLUSDT-C1 6-month bookTicker spread
  census (p50 0.469 bps, sha-pinned).

## F-7. source_disagreement — EXISTS

Design: two sources for the same logical key disagree; the cross-check must
surface the conflict (and never silently patch a primary gap), exactly one
primary is required, two primaries are refused with a stable code.

Existing implementations:
- `tests/data_fusion/test_conflicts.py` — `test_cross_check_never_patches_primary_gap`,
  `test_exactly_one_primary_is_required`, `test_two_primaries_are_refused_with_stable_code`.
- Measured precedent — EDQ1 indicative reconciliation (TD 1-min close vs
  Dukascopy tick-mid: median |Δ| 0.35 pips, max 42.65) and V6/V8
  Stooq-vs-reference OHLC corruption catches (L7 cross-check).

## F-8. stamp_scale_migration (L-TRACKB1-1) — PARTIAL

Law (LESSONS.md L-TRACKB1-1, verbatim head): "archive timestamps change
scale silently — validate the grid endpoint, not just the row count".
L-PIT packet law: assert first/last stamp within one bar of the declared
window end.

Design: a fixture stream whose final year switches stamp unit (ms → µs);
the loader must either normalize or fail loudly, and the grid-endpoint
assertion (first/last stamp within one bar of declared window start/end)
must fire on the silent-truncation mutant (row count healthy, grid short).

Existing implementations:
- Production catch — ERP1-TRACKB-COHORT-1: "µs-stamp silent grid truncation
  caught by the skeptic's independent count — spot 2025+ vision zips are
  microsecond-stamped" (ledger row; the lesson's origin).
- `research/market_data_plane/models.py` / adapters stamp normalization and
  `tests/test_mdp_bars.py::test_time_order_strict_fail_closed` partially
  cover stamp discipline.
- GAP (DESIGN-ONLY): the reusable named fixture + assertion
  (`grid_endpoint_within_one_bar(declared_window, stamps, bar_size)`) is not
  committed as a battery fixture; TrackB fixed its own loader in-cycle.

## F-9. spread_non_positive_rejection — PARTIAL

Design: synthetic bid/ask minutes containing spread == 0 and spread < 0
(crossed); both must be rejected from any spread-derived cost feature, and
the census must count them, never silently drop.

Existing implementations:
- Measured census gates — EURUSD-OPEN-SEARCH-V1 ("119,038 valid 15m bars, 0
  non-positive-spread minutes") and EDQ1 tick gate ("spread median 0.2
  pips, 0 non-positive") — the check exists and was exercised in the FX
  census builds.
- `research/market_data_plane/quality.py` `CROSSED_QUOTE` covers the crossed
  (negative) case at event level.
- GAP (DESIGN-ONLY): a named unit fixture for the exactly-zero-spread class
  (== 0 is distinct from < 0) applied to bar-derived spread features.

## F-10. volume0_unfillable_bar (L-SAMV1-3) — EXISTS (executed)

Law (LESSONS.md L-SAMV1-3): "an EOD open bar does not certify a fill —
volume=0 bars must be unfillable"; fill laws need bar-level feasibility
(volume>0 AND order notional ≤ participation fraction of that bar's dollar
volume).

Existing implementations:
- Executed in STOCKS-AMIHUD-RETEST-V1: "B2 zero-volume unfillable (452,333
  bars)" + "X1 fill feasibility (23/31/14 unfillable orders; 19/30/16 proxy
  marks)" (ledger row) — the origin record of the law (SAMV1-V1's volume-10
  HTV fantasy fill is the falsifying incident).

## F-11. reverse_split_adjustment (L-SAMV1-1) — PARTIAL

Law (LESSONS.md L-SAMV1-1): "a data-availability fixture must cover BOTH
directions of every corporate action" — the forward-only split fixture let
EODHD's un-smoothed adjusted_close across reverse splits (UNT 0.0455→41.1;
408-name extreme-print class) feed fake |r|/DV terms.

Existing implementations:
- STOCKS-AMIHUD-RETEST-V1 executed the both-direction remedy: "B1
  both-direction extreme-print law (798 bars)" (ledger row) — census-class
  execution.
- Adapter-level frozen rule: `ADJUSTMENT_AVAILABILITY_RULE =
  "FACTOR_AVAILABLE_AT_EX_DATE_SESSION_OPEN"` with fail-closed divergence
  (`.worktrees/stocks-amihud-retest-v1/.../adapters/stocks/context.py`);
  V8 probe corporate-action reconciliations (CMG 50:1, TJX 2:1 vs
  SEC-recorded facts).
- GAP (DESIGN-ONLY): a reusable synthetic hand-computable reverse-split
  fixture (raw series + factor series with a 1:10 reverse split; adjusted
  series must remain continuous across the ex-date and any discontinuity
  must raise `REVERSE_SPLIT_UNSMOOTHED`) — forward direction exists in the
  SAMV1 F3a fixture; the named bidirectional unit fixture is not in `tests/`.

## F-CX-NOBOOK-1. crypto no-candle-inference (companion fixture) — DESIGN-ONLY

Named in PIPELINE_CONTRACT_DRAFT.md clause C-CX-1: a candle-only panel fed
to any book/flow-semantics consumer must fail closed with
`NO_ORDERBOOK_FROM_CANDLES`; positive control on manifest-backed tape.
Mandatory before any crypto lane consumes a book/flow-class construct.
Adjacent evidence of the law's necessity: um liquidationSnapshot 404 /
bookTicker discontinued after 2024-04 (bear-recon PIT_DISCLOSURES);
TrackB "bookTicker ABSENT → spreads DECLARED+stress" decision.

---

## Battery status summary

| # | Fixture | Status | Primary pointer |
|---|---|---|---|
| F-1 | future-leak truncation replay | EXISTS (executed ×5 cycles) | EOSV1 test_engine_fixtures; ERP1 pit_battery2 |
| F-2 | revision/restatement detection | PARTIAL | tests/data_fusion/test_pit.py; GB re-referencing fixture DESIGN-ONLY |
| F-3 | DST boundary | PARTIAL | tests/platform_v3/test_calendar_engine.py; intraday fixture DESIGN-ONLY |
| F-4 | symbol/identity change | EXISTS | tests/data_fusion/test_identity.py; SAMV1-RETEST quarantine |
| F-5 | duplicate/missing bar | EXISTS | mdp quality.py reason codes; cng4 field 13 law |
| F-6 | quote crossed/stale | EXISTS | mdp quality.py + tests/test_mdp_bbo.py |
| F-7 | source disagreement | EXISTS | tests/data_fusion/test_conflicts.py |
| F-8 | stamp-scale migration (L-TRACKB1-1) | PARTIAL | production catch TrackB; reusable fixture DESIGN-ONLY |
| F-9 | spread non-positive rejection | PARTIAL | FX census gates; zero-spread unit fixture DESIGN-ONLY |
| F-10 | volume-0 unfillable (L-SAMV1-3) | EXISTS (executed) | SAMV1-RETEST B2/X1 |
| F-11 | reverse-split adjustment (L-SAMV1-1) | PARTIAL | RETEST B1 executed; bidirectional unit fixture DESIGN-ONLY |
| F-CX-NOBOOK-1 | crypto no-candle-inference | DESIGN-ONLY | clause C-CX-1 (PIPELINE_CONTRACT_DRAFT.md) |

Count: EXISTS 6 (F-1, F-4, F-5, F-6, F-7, F-10) · PARTIAL 5 (F-2, F-3, F-8,
F-9, F-11) · DESIGN-ONLY named fixtures: F-CX-NOBOOK-1 plus the specific gap
halves of the PARTIAL entries (each named above). Promotion of the
DESIGN-ONLY halves into `tests/` is the concrete next-cycle engineering list.
