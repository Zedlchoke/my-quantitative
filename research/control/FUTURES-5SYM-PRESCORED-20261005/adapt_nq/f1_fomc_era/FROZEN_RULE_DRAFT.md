# FROZEN_RULE_DRAFT — NQ-F1 FOMC-ERA (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-NQ**, 2026-10-05.
- **STATUS: PROPOSED / DRAFT-PENDING-OWNER.** This is the rule TEXT AS CODE ENFORCES IT for the
  synthetic-sandbox adapter `adapter.py` in this directory. It is **NOT** an approved freeze; no
  scored run, no real-data execution, no registration is authorized or implied. Outcome-blind:
  adapters compute SIGNALS and intended ORDER INTENT on synthetic fixtures only.
- Parents: `../../nq/SPEC_NQ.md` §4/§6/§7 · `../../nq/CALENDAR_PIT_POLICY_NQ.md` §3/§4 ·
  `../../nq/COST_CONTRACT_NQ.md` · `../../nq/IDENTITY_BUDGET_NQ.md` §1/§3 ·
  `../../hypo/CENSUS_5SYM.md` NQ-F1 row · `../../exec/RUNNER_COMPAT_NQ.md` RC-1..RC-6 ·
  `../../exec/symbol_contracts.json` (NQ row).
- Family: **NQ-F1 FOMC-ERA** — scheduled-uncertainty resolution on a ~1/5-participation book;
  mechanisms M-NQ-CONT (persistence) vs M-NQ-UNW (reversion); K6 anatomy PASS
  (h0_30 2.230x >= 2.0, m60_0 0.686x <= 0.85, n=85; `NQ_K6_GATES.md` §1).

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| FOMC statement stamps | injected `calendar.fomc_statements[]` = `{date, time_et, statement_file}` mirroring the committed archive parse (`k6_compute.py::load_fomc` class); **never live-sourced** | day `date`, 00:00 CT (calendar knowledge precedes the session) |
| anchor minute | for `time_et == "14:00"` stamps: **13:00 CT** bar of the statement session (14:00 ET = 13:00 CT; the timed-14:00-ET class, n=85 on cache_v3) | the anchor bar is consumed only AFTER it closes (decision time = anchor + 1 min) |
| trigger sign | `sign(close(anchor bar) - open(anchor bar))`; `TRIGGER_WINDOW_BARS = 1` **[DRAFT-CODE]** — the exact trigger-window constant freezes from the owning family doc at registration (IDENTITY_BUDGET §3 grammar note) | close of the anchor bar (13:01 CT) |
| ATR(20) | mean daily range (high-low) of the prior 20 held sessions, strict past, held-contract-only aggregates (chain `nq_held_daily_v3` class) | any time after the 19th prior session closes; consumed at decision time |
| held-session close | close of the session's measured last 1m bar (`last_bar_ct` aggregate; era-A Fridays measured per-session, never asserted) | at/after the era-correct close |

PIT enforcement in code: every read goes through `nq_common.bars_upto(panel, asof)` /
`session_bars(..., upto=asof)`; the pytest PIT proof feeds truncated panels (rows > T removed)
and requires byte-identical outputs.

## 2. Signal definition

- **Universe (base)**: timed-14:00-ET FOMC statement sessions only (`timed_fomc_events`),
  2016+ minute-anchored class. Stamps with other times → stratum `EMERGENCY_TIMING`
  (EXCLUDED from the base universe; sensitivity stratum only, per census F1 §6).
  Untimed statements (40 x 2011–2015) → stratum `UNTIMED_DAY_LEVEL_ONLY`: day-level
  exclusion law only — minute anatomy is a standing committed NOT_RUN and is never inferred;
  no F1 signal may be computed on them.
- **tail**: `UP` if trigger move > 0, `DN` if < 0, none (no trade) if exactly 0.
- **arms**: `CONT` = enter in the trigger-move direction (continuation);
  `REV` = enter opposite (reversal). Both registered simultaneously (falsification-by-competitor).
- **controls** (same machinery): `SHDW` clock-only shadow on matched non-FOMC 13:00-CT
  Wednesdays (single-seed/single-delay C1 class, seed 20261002, reading (a));
  `ALW` always-on in-window; `FLAT` zero-trade anchor. Controls consume identity budget
  (CONV-B: controls counted inside minimal).

## 3. Entry / exit / holding horizon

- **D0 entry**: BUY/SELL at the OPEN of the first 1m bar after the anchor minute (13:01 CT bar
  open), conservative fill law (fill = next 1m bar open; no limit/queue/BBO claims).
- **D30 entry**: open of the 13:31 CT bar.
- **exit (whichever first)**: TP = entry ± 2 x SL_distance; SL = entry ∓ 1.0 x ATR(20);
  same-bar TP/SL → **SL priority**; otherwise mandatory flat at the era-correct close
  (exit fill = close of the session's measured last 1m bar). Intraday, same session —
  no overnight holding.
- SL/TP levels are rounded to the 0.25 tick grid; entry/exit prices asserted on-grid.

## 4. Session / event / calendar exclusions (fail-closed)

`apply_exclusions(calendar, panel)` returns per-session flags; ANY flag ⇒ NO-TRADE:

| code | law |
|---|---|
| `FOMC_STANDING_OUTSIDE` | every base-FOMC statement day EXCLUDED at day level (132 statements 2011–2026 incl. 40 untimed) — binds this family's non-event strata and every other family's base; FOMCIN-class arms use `fomcin_inverse_include()` (inverse include set) |
| `H1_RTH_COVERAGE_LT_060` | RTH-core coverage (08:30 CT → era-correct close, minutes-with-bar share) < 0.60 ⇒ EXCLUDE session (deterministic; the 154 low-coverage v3 sessions are real market structure). Coverage is a SESSION-level disposition consumed from the held-chain per-session register (`v3_qc` class) — never recomputed from truncated bars in a decision path (`nq_common.audit_coverage_from_bars` is verification-only) |
| `H2_H3_2026_DUBIOUS` | 2026 deviation-suspect days EXCLUDE fail-closed while P5-NQ6 unsigned (product-code register 0/10 NOT_OBTAINED/BLOCKED_TRANSPORT; advisory class 10/10 class-level only; named minimum: 2026-01-19, 2026-04-03, 2026-07-03) |
| `H4_EARLY_CLOSE_NOT_TRANSCRIBED` | NQ early-close times 2011 / 2021–2025 NOT_TRANSCRIBED ⇒ those days EXCLUDE until transcribed |
| `H5_QUARTER_UNPROVEN` | any quarter whose held-chain/expiry pairing cannot be proven ⇒ whole quarter EXCLUDED |
| `EMERGENCY_TIMING` | non-14:00-ET timed statements — sensitivity stratum only, no base trade |
| `UNTIMED_DAY_LEVEL_ONLY` | untimed statements — day-level law only, minute anatomy NOT_RUN |
| `ATR_WARMUP_INSUFFICIENT` | fewer than 20 prior held sessions ⇒ NO-TRADE |
| `TRIGGER_FLAT` | trigger move exactly 0 ⇒ tail undefined ⇒ NO-TRADE |

DST fall-back absolute-24h quirk PRESERVED AS MEASURED: `session_date` is consumed as carried
panel data and never re-derived from `ts`; a "DST-corrected fix" would be a contract violation
(RC-2.3). Era-A Fridays: exit uses the session's measured `last_bar_ct` (15:15 CT class), never
an asserted 16:15. A session whose carried `last_bar_ct` disagrees with its bars ⇒
`REFUSED_SESSION_MASK_MISMATCH` (RC-2.1 refuse posture).

## 5. Roll / cease-guard handling (chain law, SPEC §2)

- All masks, fills and anatomy consume the **held contract only** (`held_volume_k5_v3` class,
  RC-2.5). The panel carries the held-contract id per session/bar; fixtures are single-contract
  per session by construction.
- Chain of record = cache_v3, **canonical-CANDIDATE** while ADOPT-D9 (P5-NQ1) is unsigned:
  `require_synthetic(panel)` refuses any non-SYNTHETIC provenance (real-data execution NOT_RUN).
- Cease-guard law = max(crossover, cease-floor) — PROPOSED standard, pending D9; the adapter
  performs no chain construction and therefore never exercises the cease-guard branch; roll-week
  sessions are NOT additionally excluded for F1 (a statement may fall in a roll week; the F4
  NEW-4 audit binds the run, not this family's signals).

## 6. Tick / multiplier / cost binding points

- Quote unit: index points, USD contract; `long_base_sign = +1` (long profits when price rises).
- Bound from `exec/symbol_contracts.json` NQ row via `nq_common.load_nq_contract()`:
  **tick_size 0.25 pt · tick_value_usd $5.00 · multiplier 20** — no conflicting hardcode; a
  $2.50/tick configuration is refuse-worthy (P5-NQ4 defect guard, RC-1.1). Tick regime
  constant era-wide (no NQ tick-era break; 6A's D8 law is never inherited).
- Costs (`nq_common.cost_per_side_usd`, COST_CONTRACT_NQ §3/§4 shape): per-side all-in
  = fee + $16.25 spread half-turn (6.5-tick close proxy, high-biased) + slippage
  {S1 $5.00, S2 $10.00, S3 $15.00}/side; ladder **A 23.50/28.50/33.50**, **B 23.49/28.49/33.49**;
  RT = 2 x per-side; stress x1.0 (gate number) / x1.5 / x2.0 (disclosed views).
  **While P5-NQ3 (D3) is unsigned: Variant A, basis-only, is the fail-closed default;
  requesting Variant B raises `RefusedPendingOwnerDecision("P5-NQ3")`.**
  Labels on every cost surface: MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN;
  the words "measured cost"/"complete cost" are forbidden.

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_NQ.md §3 / identity_budget_nq.json)

Grammar `FBNQ1-<FAM>-<ARM>-<TAIL>-<DELAY>-<TIER>`; DRAFT cycle token `FBNQ1` (registered cycle ID
replaces it verbatim). NQ-F1 = 8 core + 3 controls = **minimal 11** (CONV-B; full grid 24):

```
FBNQ1-F1-CONT-UP-D0-S2   FBNQ1-F1-CONT-UP-D30-S2   FBNQ1-F1-CONT-DN-D0-S2   FBNQ1-F1-CONT-DN-D30-S2
FBNQ1-F1-REV-UP-D0-S2    FBNQ1-F1-REV-UP-D30-S2    FBNQ1-F1-REV-DN-D0-S2    FBNQ1-F1-REV-DN-D30-S2
FBNQ1-F1-SHDW-D0-S2      FBNQ1-F1-ALW-D0-S2        FBNQ1-F1-FLAT
```

Binding any OPTION (NQ-A/B/C) raises `RefusedPendingOwnerDecision("P5-NQ2")` while the owner
ceiling + clock-shadow reading are unsigned. NQ-D refuses unconditionally
(EXPWITCH leg DEAD-AT-GATE, code `EXPWITCH_DEAD_AT_GATE`).

## 8. Fold / warmup application

Folds (SPEC §6, RC-5.1): F1 2010-06..2012-12 · F2 2013-01..2017-12 · F3 2018-01..2021-12 ·
F4 2022-01..2026-09; the 2026-10-01 partial tail is outside every fold. **Warmup = 252 held
sessions excluded at each fold head** (`nq_common.scoreable_sessions`; default law constant
252 — fixtures pass a small warmup to exercise the mechanics and separately assert the
default). Folds multiply evaluation views only — identity count is invariant across folds
(RC-5.3). S1 = SEALED_UNTOUCHED (no adapter path exists; RC-5.5).

## 9. Owner-pending law — namespaced decision slots (fail-closed while unsigned)

| slot | law it gates | adapter behavior while unsigned |
|---|---|---|
| `P5-NQ1` | ADOPT-D9 Option A (cease-guard standing law + cache_v3 canonicalization) | `require_synthetic()`: any non-SYNTHETIC panel provenance raises `RefusedPendingOwnerDecision("P5-NQ1")`; real-data adapter execution = NOT_RUN |
| `P5-NQ2` | owner NQ ceiling (option A 22 / B 29 / C 36) + clock-shadow reading (a)/(b) | `nq_common.bind_option()` raises `RefusedPendingOwnerDecision("P5-NQ2")`; draft enumeration stays provisional |
| `P5-NQ3` | D3 regulatory basis (Variant A 2.25 vs B 2.24 /side) | `cost_per_side_usd(..., variant="B")` raises `RefusedPendingOwnerDecision("P5-NQ3")`; default A basis-only |
| `P5-NQ4` | annotation-only erratum ($2.50/tick pointer-line defect) | `load_nq_contract()` refuses any $2.50 configuration |
| `P5-NQ5` | EXPWITCH leg disposition (data-plane) | stub refuses all EXPWITCH requests with code `EXPWITCH_DEAD_AT_GATE` regardless of any guard state |
| `P5-NQ6` | calendar-2026 residual posture | 2026 dubious-day fail-closed exclusions stand; the documented bypass helper `unexclude_2026()` always refuses |

## 10. Era conditioning (declared K-views — evaluation labels, never identity splits)

Every intent carries `era_view = k_views(session_date)` (K-V1 session-close eras A/B,
K-V2 tri-eras, K-V3 FOMC data-eras 2016-19/2020-22/2023-26, K-V4 COVID window,
K-V5 alias-repair region, K-V6 regulatory-fee window). Era conditioning shapes
evaluation strata at a future freeze; it never gates an individual signal in this adapter
(the only hard era gates are F2's scoring-era confinement, by its own committed anatomy law).

— End FROZEN_RULE_DRAFT (PROPOSED). Nothing herein freezes, registers, scores, or ratifies.
