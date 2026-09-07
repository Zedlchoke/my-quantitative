# A9-F Feasibility Audit — FOREX-FREE-V4 — Handoff

Auditor: A9-F (independent feasibility auditor; no PnL computed, no backtest, no repair).
Machine-readable record: `a9_f_feasibility_v4.json` (same directory).
Base head verified: `0a34678aafcb0a0b4626d1ea231bf13f6a6731d2` on `orca/forex-free-v4-d2-a9-feasibility`.

## Verdicts

| Proposal | Verdict | Highest finding |
|---|---|---|
| FXFV4-A4-P1 (financing-budget-scaled differential carry) | FEASIBLE | HIGH x2 (fold scheme, window start) |
| FXFV4-A4-P2 (event-anchored persistence hold) | FEASIBLE | HIGH x2 (same fold/window defects + baseline-entry evidence) |
| FXFV4-A5-P1 (real-rate differential drift) | DATA_BLOCKED_VALID | MEDIUM (frozen-convention conflicts, unblock-time) |
| FXFV4-A5-P2 (PPP-deviation band reversion) | DATA_BLOCKED_VALID | HIGH (monthly clock not mechanically defined) |
| FXFV4-A6-P1 (commodity-bloc risk-off basket) | FEASIBLE | MEDIUM (fold-1 thin; dropout denominator deviation) |
| FXFV4-A6-P2 (policy-change underreaction drift) | FEASIBLE | MEDIUM (turnover counted on raw ledger; F1 at/below fold floor) |

## The three cross-cutting facts that drive the findings

1. **The actual H1 price span is 2020-01-29/30 .. 2026-09-02**, not 2018-09 as snapshot filenames suggest
   (`w1_freeze.json` `loader_manifest_7_pairs`: ~42.6–42.8k bars/pair, `gaps_gt_85h = []` on all 7 pairs).
   Under the inherited runner, entries before 2020-03-01 are warmup-region and receive **no fold**.
2. **The inherited frozen fold boundaries are (2020-03-01, 2022-05-01, 2024-07-01, 2026-09-02)**
   (`scored_runner.py` FOLD_BOUNDARIES, mirrored in V3 `baseline_invariants.json`). The A4 packets state
   "inherited frozen boundaries (2020-03-01, 2022-05-01, end 2026-09-02)" — they silently dropped the
   2024-07-01 boundary, producing a fold scheme the frozen runner cannot express.
3. **Ledger dedupe matters**: 220 raw rows → 159 unique (151 RATE_CHANGE + 8 BASELINE). All 61 duplicates
   are UNEVIDENCED→EVIDENCED upgrades (AU 25, CH 11, NZ 25), so dedupe is evidence-monotone (conservative
   direction preserved). Deduped event distribution by inherited folds: pre-2020-03-01 = 8 events (26
   pair-events, all pre-price-window), F1 = 21 (39 pair-events), F2 = 70 (130), F3 = 52 (88). **Zero deduped
   events fall in 2020-01-30..2020-03-01.** Any packet counting "212 rate changes / AU 50 / NZ 50 / CH 22" is
   counting the raw file and overstates events by ~30%.

## HIGH findings (must be resolved at D2 / before implementation)

- **A4P1-H1 / A4P2-H1 — fold-scheme contradiction.** Both A4 packets claim to inherit frozen boundaries they
  do not inherit. The packet's own scheme (F1 = 2019-01..2020-03) is not expressible on the frozen runner
  (`fold_of()` returns None before 2020-03-01); under the inherited scheme, gate arithmetic changes (first
  inherited fold is itself at the 30-trade populated floor). Since both packets *say* "inherited frozen
  boundaries", the inherited grid is the authoritative reading and the packets are runnable with degraded fold
  population — but the deviation must be recorded, not silently absorbed.
- **A4P1-H2 / A4P2-H2 — window start.** Both packets score "over 2019-01..2026-09" and populate "fold 1"
  with trades that cannot exist (zero deduped events and no price bars before 2020-01-30 in that span).
  A4-P2 additionally opens **scored entries from the window-open baseline state**, and the 8 BASELINE_LEVEL
  rows are AVAILABILITY_UNEVIDENCED with `effective_date/effective_time_utc/first_readable_decision_utc = null`
  — so the packet's "non-load-bearing, provenance-only" claim is false exactly where it opens trades on them.
  PIT-legality survives (the conservative bound 2019-01-01T23:59:59Z precedes any window), but the frozen-reader
  invariant is not mechanically evaluable on baseline rows and the initial-book/entry convention forces
  implementer judgment.

## MEDIUM findings worth controller attention

- **A4P1-M1 / A4P2-M1** — packet evidence tables use raw-file fractions ("AU 25/50", "NZ 25/50", "CH 11/22",
  "112 unevidenced rows"); the operative deduped state is AU 25/25, NZ 25/25, CH 11/11, 43+8 unevidenced rows.
  Conservative direction, no P-1 issue, but the vintage reader must be built from deduped ledger semantics.
- **A4 turnover bands overstated ~1.5–2x.** A4-P1 "120–220 trades" → auditor estimate 95–155 after hysteresis +
  saturation suppression (w pegged at ±1 while |Δr| ≥ 48 bps suppresses e.g. all 19 EMU events on EUR/USD and
  most US hikes). A4-P2 "180–360" → est. 100–130 (63-session horizons cap re-entry ~4x/pair/year).
- **A6P2-M1 — turnover on the raw basis.** "344 pair-events gross / 290–315 decisions / F1 1.5–2.7x floor" →
  deduped: 283 gross / ~240–255 decisions / **F1 est. 21–27 trades = at/below the 30-trade populated floor**
  (the 2020-03 double US cut contributes ~7, not 14, after within-hold suppression). Full-sample 140 floor
  still met (~200–230 trades); F1 likely unpopulated → fold gate degrades to 2-of-2.
- **A5P1-M1 / A5P2-M3 — frozen-convention conflicts inside the blocked memos** (they commit to running "EXACTLY
  as frozen here" on unblock): purge "20/21 sessions" vs frozen PURGE_DAYS = 14; A5-P1's 12-trade fold floor vs
  frozen 30; "proportional scaling of booked PnL" prose vs the kernel's re-booking at 2.25/3.0 bps per side with
  gross tier-invariant (`book_stress`, `assert_stress_rows_distinct`). The kernel governs; the memos' prose must
  be reconciled before any unblock cycle.
- **A5P2-M2** — the early-exit rule text is garbled ("re-crosses toward Q by at least half the entry
  deviation") and is not implementable as written.
- **A6P1-M2** — 6-scenario dropout suite (5 leg-drops + best-fold, gate 5/6 = 0.833) deviates from the frozen
  8-scenario/6-survival harness; disclosed, tightening-only, justified (EUR/GBP are not traded legs), but it is
  harness-adjacent work.

## DATA_BLOCKED verification (A5-P1/P2)

Both blockers are **accurate**: `cpi_bis_ws_long_cpi` is STAGED_NOT_CITABLE with availability evidence NOT WIRED
(catalog consequence: "NOT citable by V4 D1 proposals"); `cpi_ecb_icp` is NOT_FUNDED for 7 of 8 areas. The named
unblock paths (per-print official static release calendars for BLS/ONS/ABS/StatsNZ/StatCan/SwissFSO/SBJ/Eurostat,
append-only ledger rows with archive hashes, INSTANT-or-conservative-DAY precision, re-pin → vintage regeneration
→ P2 re-gate → status upgrade) match the catalog's requirement and the existing extension tooling in the run tree
(`announcement_archives_v4_extension/`, `announcement_ledger_builder_v4_extension.py`). Caveats recorded: the
probe bytes are not staged (/tmp only), the vintage pipeline needs a monthly print-semantics extension, and the
catalog's "NOT citable by V4 D1 proposals" correctly confines both families to a future owner-authorized cycle —
which both memos already accept. **Verdicts: DATA_BLOCKED_VALID for both.** A5-P2 additionally carries a HIGH
unblock-time defect: its "MONTHLY" decision clock, read literally, fires every session (A5P2-H1) — repairable in
the frozen memo now, at zero cost, before anyone unblocks it.

## Estimated decision counts vs floors (light arithmetic; no simulation)

| Packet | Decisions (est.) | Trades (est.) | Floors | Verdict vs floors |
|---|---|---|---|---|
| A4-P1 | ~257 fillable pair-events | 95–155 round trips | 40/arm; 30/fold | arm floor met; inherited-F1 ≈ 25–32 (knife-edge); packet-scheme F1 = 0 |
| A4-P2 | ~257 | 100–130 | 40/arm; 30/fold | arm floor met; inherited-F1 ≈ 20–25 (below floor); F3 ≈ 30–45 (borderline) |
| A5-P1 | ~1,430/pair daily (blocked) | 35–84 crossings | 100/arm; 60 full-sample | decision floor met; 60-trade floor straddled |
| A5-P2 | ~43–44/pair monthly ≈ 300–310 (blocked; packet said 57/pair) | 120–215 | 200/arm; 120 full; 30/fold | decision floor met; 120-trade floor knife-edge |
| A6-P1 | ~1,600/leg ≈ 8,000 | 175–350 | 40/arm; 140 full; 30/fold | all floors met (decision floor by 2 orders); F1 thinnest, likely populated |
| A6-P2 | ~240–255 (packet said 290–315) | 200–230 | 40/arm; 140 full; 30/fold | arm/140 floors met; **F1 ≈ 21–27 → likely unpopulated** |

## Validator-precedent (ONE_EVENT_LAG_VIOLATION) test per packet

- **A6-P1 / A6-P2**: strongest compliance — explicit next-session rule, explicit 4-day bound, **explicit
  fail-closed NO_TRADE on breach**, fail-closed missing-bar/missing-evidence paths. This is the discipline the
  V3R abort demands.
- **A4-P1 / A4-P2**: control fill schedules are byte-identical to the anchor's (derangement / mirrored subset),
  so a validator abort would be structurally impossible even under implementation bugs in the control. Residual
  gap: neither packet specifies behavior if a next-bar gap ever exceeded 4 days (the snapshot's max gap ≤ 85 h
  makes this unreachable in practice, per `gaps_gt_85h = []`, but the spec path is missing).
- **A5-P1 / A5-P2**: all arms share the anchor's clock/fills; the A5-P2 stale-price control is legal under
  evidenced semantics (older reads are always safe) and cannot be refused. Same missing fail-closed-path nit.

## What this audit did NOT do

No PnL, no backtest, no schedule simulation, no price bytes read (data_raw absent in this worktree; coverage
audited from the staged manifest + w1_freeze loader manifest + A6 span claims). FEASIBLE is a
data/design-feasibility ruling only — several packets independently disclose knife-edge or likely-fail Stage-A
gates (A6-P2 USD-drift 0.2–0.5 vs 0.30 ceiling; A4 stress-tier margins; A5 thin effect sizes) and this audit
expresses no view on their outcomes. Nothing outside `research/audits/forex_free_v4/` was modified.
