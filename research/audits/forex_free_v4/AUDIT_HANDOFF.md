<<<<<<< HEAD
# A7-N AUDIT HANDOFF — cycle FOREX-FREE-V4 (novelty / anti-rescue)

Auditor: A7-N (independent). Branch `orca/forex-free-v4-d2-a7-novelty`, base
`0a34678aafcb0a0b4626d1ea231bf13f6a6731d2` (verified). Audit UTC
2026-09-05T05:19:31Z. I wrote audit artifacts only; I repaired nothing and
computed no PnL anywhere.

## 0. What was measured and how (bytes, not prose)

The mandated ancestry measurement reconstructs DECISION SERIES (per pair, per
daily 16:00 America/New_York decision clock: signed direction in {-1, 0, +1};
no PnL) for:

- **V3 family2 (FXFV3-A6-P1) anchor, two variants**, by importing the frozen
  `research/assets/forex_free_v3/family2.py` READ-ONLY from the V3 worktree
  and driving it with the frozen `PolicyRateReader`:
  - variant (a) as-scored: V3 asserted-bound vintages
    `data_raw/forex_free_v3_macro` (V3 tree);
  - variant (b) evidenced-corrected: `data_raw/forex_free_v3r_macro_evidenced`
    (V3R tree).
  Both variants share the identical price side (H1 snapshot) and identical
  220-valid-NY-day warmup; only the vintage availability differs.
- **FXFV4-A4-P1** (kappa = 48 bps budget sizing, 0.10 hysteresis,
  exit-on-flip/zero) over the P0a evidenced vintages (v2 ledger pin
  `ae5e1f2e...` — sha256 verified against `LEDGER_PINNED`).
- **FXFV4-A4-P2** (event-anchored entries >= 48 bps, H = 63, event-exit
  < 24 bps, crash unwind 2.5x/63-median x2 clocks + lockout) over ledger
  events deduped (area, effective_date) LAST-ROW-WINS + snapshot closes.
- **FXFV4-A6-P2** (policy-change drift, delta sign at availability, H = 10
  NY-days, US drives all 7 long-USD on hike, first_ok 2020-02-11).

Certification, all recorded in `a7_n_measurements_raw.json`:

1. My mirrored family2 walk reproduces the frozen `_schedule_pair` trips
   EXACTLY (7/7 pairs, both variants).
2. The V3R `decision_diff_table.json` is replicated ROW-EXACTLY by my two
   vintage readers: 158 differing readable-rate cells / 19 sign flips,
   identical row sets.
3. All 8 P0a evidenced-vintage canonical sha256 match both the V4 tree
   manifest and the worktree `p0a_evidenced_vintages_manifest.json`.
4. Interpretation of (2): the 158/19 availability differences land almost
   entirely outside family2's in-market states — the ancestor variant (a)
   vs (b) decision panels agree at rho 0.9993. The correction changed the
   contract, not the direction series.

## 1. Declared bar (frozen BEFORE measurement)

Written to `A7_N_DECLARED_BAR.md` before the measurement script first ran.
Gating statistic: **Spearman rho over ACTIVE shared cells** (both books
non-flat) — "when both books are in the market, do they point the same way".
|rho| < 0.5 with n_active >= 30 admits novelty; 0.5–0.7 CONDITIONAL;
> 0.7 = re-grade = REJECT; n < 30 INDETERMINATE. rho_full (flats included)
reported as a non-gating diagnostic. Front door: REJECTED if the bar is
breached vs EITHER ancestor variant.

## 2. Rho table (all comparisons)

| comparison | n_shared (total/active) | rho_gating (active) | rho_full | agreement (active) | verdict |
|---|---|---|---|---|---|
| A4-P1 vs F2 (a) as-scored | 9491 / 5335 | **1.000** | 0.750 | 100.0% | REJECT_RE_GRADE |
| A4-P1 vs F2 (b) evidenced | 9491 / 5335 | **1.000** | 0.750 | 100.0% | REJECT_RE_GRADE |
| A4-P2 vs F2 (a) as-scored | 9491 / 2283 | **0.9974** | 0.464 | 99.87% | REJECT_RE_GRADE |
| A4-P2 vs F2 (b) evidenced | 9491 / 2283 | **0.9991** | 0.465 | 99.96% | REJECT_RE_GRADE |
| A6-P2 vs F2 (a) as-scored | 9491 / 768 | **0.0537** | 0.013 | 52.7% | NOVELTY_PASS |
| A6-P2 vs F2 (b) evidenced | 9491 / 768 | **0.0538** | 0.013 | 52.7% | NOVELTY_PASS |
| F2 (a) vs F2 (b) [control] | 9491 / 5338 | 0.9993 | 0.999 | 99.96% | (control, not an admission test) |

The A4-P2 diagnostic divergence (rho_full 0.46 < 0.5 vs gating 0.997) is a
participation artifact, not direction novelty: A4-P2 holds through vol
(24% of shared cells active) while family2 goes flat in HIGH states (56%
active); A4-P2 overlaps ALL of family2's active cells and agrees on
direction ~99.9% of them. The declared bar assigns the decision to the
gating statistic; both numbers are in the owner block.

## 3. Front-door admission decision (numbers to owner, either way)

- **FXFV4-A4-P1: REJECTED.** rho 1.000 vs both variants. Its book holds
  EXACTLY the ancestor's direction at every one of the 5335 shared
  in-market decision cells. The financing-budget sizing, kappa scaling and
  event hysteresis are size/timing machinery over the same direction
  series. A V4 survivor would re-grade the invalidated ancestor — forbidden
  by definition (PLAN section 1 item 4).
- **FXFV4-A4-P2: REJECTED.** rho 0.997/0.999 vs both variants. Fixed
  horizon, crash unwind and lockout change holding duration and exit
  timing, not direction; in-market direction agreement is ~99.9%.
- **The section-1.1 carry front door is CLOSED for FOREX-FREE-V4.** Any
  future front-door plan must be directionally distinct from the
  differential-carry direction, not merely cost-relieved.

## 4. Per-proposal novelty verdicts

| proposal | verdict | basis |
|---|---|---|
| FXFV4-A4-P1 | **NOVELTY_FAIL** | measured: rho 1.000 / 1.000 (re-grade) |
| FXFV4-A4-P2 | **NOVELTY_FAIL** | measured: rho 0.9974 / 0.9991 (re-grade) |
| FXFV4-A5-P1 | **CONDITIONAL** | DATA_BLOCKED, unmeasurable (CPI leg unwired). Features distinct from all V1/V2/V3-family1 rows, but the nominal component of its signal IS the ancestor's information source (its own disclosure). Its preregistered inflation-sign-inversion placebo governs at scoring; re-measure rho when the CPI ledger extension lands. |
| FXFV4-A5-P2 | **NOVELTY_PASS** | features: zero interest-rate input anywhere — cannot be a carry descendant by construction; all four features distinct from every forbidden row (data-blocked, but novelty is not the binding question) |
| FXFV4-A6-P1 | **NOVELTY_PASS** | features: price-only cross-sectional event basket; information source, clock, control, functional form all distinct from every forbidden row; explicitly checked and excluded: sign-inversion of V1-family2, session-clock relabel, vol-gate rescue of family2 |
| FXFV4-A6-P2 | **NOVELTY_PASS** | measured (mandated for the policy-event packet): rho 0.0537 / 0.0538, active agreement 52.7% = chance level. Reads the same ledger but uses the event DELTA sign at availability — decision-level orthogonal to the ancestor. Feature table distinct on all four features vs all rows. |

The full 6-proposals x 7-forbidden-rows feature table (information source,
decision clock, causal control, signal functional form, rescue-variant
check: clock relabel / sign inversion / threshold neighbourhood / pair
subset / cost relief / control swap) is in
`a7_n_novelty_v4.json -> forbidden_rows_feature_table`.

## 5. Notes the owner should read

1. Both A4 packets disclosed their confirmatory-re-entry status honestly and
   pre-committed to dying on these numbers. The rejection is the front door
   working as designed, not a packet defect: their novelty claim (cost
   survival by construction) is real but lives entirely outside the
   direction series, and the PLAN gates ancestry on the direction series.
2. The ancestor variant control (a-vs-b rho 0.9993) plus the exact 158/19
   diff-table replication means the front-door rejection does NOT depend on
   which availability convention the ancestor is graded under.
3. A5-P1 is the only remaining carry-adjacent live family. It is
   data-blocked; when the CPI evidence lands, its measured rho vs both
   ancestor variants must be taken BEFORE any scoring, per this audit's
   CONDITIONAL verdict.
4. A6-P2's PASS is measured, not argued — but its own packet discloses a
   USD-drift gate risk (~45% of pair-events are US-area). Novelty and
   viability are different gates; this audit rules only on the former.

## 6. Limitations

Recorded verbatim in `a7_n_novelty_v4.json -> limitations`. Headlines:
decision-series only (no PnL/gates); gating-vs-full rho resolution frozen ex
ante; A4-P2 crash-estimator and H-day exit offsets have +-1-session
convention freedom (immaterial at 0.997+); A5 verdicts are feature-level
until CPI evidence exists; 138 reconstructed family2 round trips per variant
are the raw schedule book, not the runner's scored/purged population.

## 7. Artifacts (this worktree only)

- `research/audits/forex_free_v4/A7_N_DECLARED_BAR.md` — bar, written first
- `research/audits/forex_free_v4/a7_n_measurements_raw.json` — raw numbers + integrity checks
- `research/audits/forex_free_v4/a7_n_novelty_v4.json` — the audit deliverable
- `research/audits/forex_free_v4/scripts/a7n_measure.py` — measurement script (replayable against the frozen inputs)

— A7-N, 2026-09-05
=======
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
>>>>>>> 2752cf2 (FOREX-FREE-V4 A9-F independent feasibility audit: six-packet audit (4 FEASIBLE, 2 DATA_BLOCKED_VALID), 30 findings incl. A4 fold-scheme/window HIGH defects, A5-P2 monthly-clock ambiguity, A6-P2 raw-vs-deduped turnover basis; no PnL computed)
