# FROZEN_RULE_DRAFT — 6J-JF1 BoJ MPM DECISION-WINDOW (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- **STATUS: PROPOSED / DRAFT-PENDING-OWNER.** This is the rule TEXT AS CODE
  ENFORCES IT for the synthetic-sandbox adapter `adapter.py` in this directory.
  It is **NOT** an approved freeze; no scored run, no real-data execution, no
  registration is authorized or implied. Outcome-blind: SIGNALS + intended
  ORDER INTENT on synthetic fixtures only.
- Parents: `../../fx_ja/SPEC_6J.md` §1/§2/§3/§4/§6/§7/§8 ·
  `../../fx_ja/CALENDAR_PIT_POLICY_6J_6A.md` §3/§5 ·
  `../../fx_ja/COST_CONTRACT_6J_6A.md` §1/§4 ·
  `../../fx_ja/IDENTITY_BUDGET_6J.md` §1/§2 (+ `.json` mirror) ·
  `../../fx_ja/GAPS_AND_DECISIONS_6J_6A.md` §(b) ·
  `../../hypo/CENSUS_5SYM.md` JF1 dossier · `../../exec/symbol_contracts.json` (6J row).
- Family: **JF1 BoJ MPM Decision-Window Resolution** — drift vs reversal in a
  35.8%-thinner book; n=54 measured MPM dates 2020–2026; per-event MDE ≈ 13–19
  bp vs modeled RT 8.5–14.7 bp — **K2 live risk stated (power honesty).**

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| BoJ MPM decision dates | injected `calendar.boj_mpm_dates[]` mirroring the measured 54-date set (`6J_a4_events.json` sha `8dab9318…`; `ja_event_pit.json` sha `003c6821…`); **FACT, day-granularity** | the decision date, 00:00 local (calendar knowledge precedes the session) |
| BoJ intraday release stamp | **NOT_IN_CORPUS.** Consuming/claiming one raises `REFUSED_BOJ_STAMP_NOT_IN_CORPUS` (`fc.consume_boj_intraday_stamp`; upgrade path owner slot **P5-HYPO-OD2**) | never on this corpus |
| decision window | **12:00–15:30 JST, a DECLARED convention** (Tokyo-afternoon block where decisions land; range-share 13.43% vs 10.35%) — never a minute-anchored release; bucketed in Asia/Tokyo via zoneinfo (DST-correct clock law, SPEC_6J §3) | window move is strict past at the window close |
| window move / tail | `close(last window bar) − open(first window bar)` **in 6J price terms**; tail UP/DN | window close, 15:30 JST = decision time |
| window ATR(20) | mean of the event-window ranges over the prior 20 MPM dates, strict past (session aggregates `window_ranges["mpm"]`) | after the 20th prior event closes; consumed at decision time |

**QUOTE-DIRECTION LAW (load-bearing, every sign).** 6J is quoted USD per JPY;
**6J price UP = yen STRENGTHENS.** Every tail, arm direction and side below is
in 6J price terms. Orientation proof (own raw slice, not vendor docs):
`fx_ja/6j_orientation_recheck.json` (sha `6ca0baeb…`) — 2024-07-11 front 6JU4
session open 0.0062485 → close 0.0063565 (+1.73%) while implied USDJPY fell
160.04 → 157.32. Re-expression in USDJPY terms requires an explicit declared
sign inversion; none exists in this family.

PIT enforcement in code: every read goes through `fx_common.session_bars(..., upto=asof)`;
the pytest PIT proof truncates the panel at decision_time − 1 min (not knowable)
and at decision_time (byte-identical to full-panel resolution).

## 2. Signal definition

- **Universe (base)**: the MPM dates (`calendar.boj_mpm_dates`) — 54 measured
  2020–2026 in the real corpus; 27 synthetic dates in the fixture.
- **tail**: UP if window move > 0, DN if < 0; exactly 0 ⇒ `TRIGGER_FLAT` NO-TRADE.
- **arms**: `DRIFT` = enter in the window-move direction (continuation);
  `REV` = enter opposite (reversal). Both tails registered simultaneously.
- **regime-change subset** (titled MPMs; calendar `boj_mpm_regime_change_dates`):
  stratum tag `REGIME_CHANGE_DESCRIPTIVE_ONLY` — n=4+2 fails the ≥5/fold floor
  (pre-declared); descriptive forever, **0 identities** (`fold_floor_check`).
- **controls** (inside the 11, CONV-B reading (a)): `PLA` C1 clock-only shadow
  at identical window times on matched non-event days (single-seed/single-delay,
  seed 20261002); `ALW` C2 always-in-window on all non-event days; `CLK` C3
  weekday-matched non-event clock (family-specific negative).

## 3. Entry / exit / holding horizon

- **D1 entry**: the OPEN of the first 1m bar after the window close (15:30 JST
  bar open) — conservative fill law (fill = next-bar open; no limit/queue/BBO
  claims; requesting any raises `REFUSED_PENDING_OWNER_DECISION("P5-FXJA-D3")`).
- **D30M entry**: open of the 16:00 JST bar.
- **exit (whichever first)**: TP = entry ± 2 × SL_distance; SL = entry ∓ 1.0 ×
  window-ATR(20); same-bar TP/SL → **SL priority**; otherwise mandatory flat at
  the session's measured last bar (time exit = session close; no overnight hold
  — roll-carry never enters).
- SL/TP rounded to the 5e-07 tick grid; entry/exit asserted on-grid.

## 4. Session / event / calendar exclusions (fail-closed; ANY flag ⇒ NO-TRADE)

| code | law |
|---|---|
| `X_MOF_OP_DAY` | MOF op days EXCLUDED from the JF1 universe (census JF1 §6); the op list is a committed **ex-post universe cut**, never a decision-time input |
| `X_UNVERIFIED_OP_WINDOW_PRICE_ONLY` | the 2026-07-30 window is NOT MOF-verified — price anatomy only, never merged into any op set (SPEC_6J §6) |
| `X_ROLL_CEASE_GUARD` | the 2022-09-20 held-dead law-case session (baseline chain keeps the row, bar-level chain drops it) — flagged stratum INSIDE the Sep-2022 intervention week, never a base stratum (SPEC_6J §5) |
| `H_QUARTER_UNPROVEN` | 6J 2023Q1–Q4 + 2 unidentified expiry cells NOT_OBTAINED ⇒ whole-quarter EXCLUDE (CALENDAR §5.1; derivation FORBIDDEN) |
| `H_HOLIDAY_TIMES_NOT_OBTAINED` | holiday-shortened sessions whose FX session times cannot be proven (2024–25 explicitly NOT_OBTAINED; CALENDAR §5.2) |
| `H_PARTIAL_TAIL` | 2026-10-01 partial tail (~2h) — full-session statistics end 2026-09-30 |
| `ATR_WARMUP_INSUFFICIENT` | fewer than 20 prior MPM window ranges ⇒ NO-TRADE |
| `TRIGGER_FLAT` | window move exactly 0 ⇒ tail undefined ⇒ NO-TRADE |

## 5. Roll / cease-guard handling (chain law, SPEC_6J §5)

- The adapter consumes carried session masks and never builds the chain; the
  chain law is implemented once in `fx_common.build_roll_chain` /
  `measure_and_disclose_guard_violations` (baseline k=5 + explicit cease-guard
  variant; "decided at close t, effective t+1" verbatim; sign-non-flip check
  RMM K6(a)) and is exercised by the RMM-6J family fixtures/tests.
- Any session in `calendar.roll_guard_flagged_days` is NO-TRADE here
  (`X_ROLL_CEASE_GUARD`): the 2022-09-20 exemplar is never a base stratum.

## 6. Tick / multiplier / cost binding points

- Quote unit: USD per JPY; `long_base_sign = +1` — a long 6J profits when the
  yen APPRECIATES (quoted price rises). Bound from `exec/symbol_contracts.json`
  6J row via `fc.load_fx_contract("6J")` and RE-ASSERTED against the committed
  identity: **tick 5e-07 = $6.25 · multiplier 12,500,000 JPY** (SPEC_6J §1;
  drift refuses, `REFUSED_PANEL_INVALID`).
- Costs (`fc.cost_per_side_usd`, COST_CONTRACT §1): per-side = fee + m ×
  (spread + slippage); spread close-proxy $25.00/side HIGH-BIASED; slippage
  {S1 $6.25, S2 $12.50, S3 $18.75}; stress ×1.0 gate / ×1.5 / ×2.0 on
  (spread + slippage) only — fee invariant. RT T1/S1 = $67.42 = 8.4499 bp of
  $79,787.50. **Tokyo-window entry fills carry the +1-tick entry-side session
  floor (PROVISIONAL, JF1-7)** — declared, never a fill claim.
- Labels on every cost surface: MODELED COST / UNDER REVIEW /
  VERIFIED_VS_ACCOUNT=NOT_RUN; "measured cost"/"complete cost" FORBIDDEN
  (requesting a verified label refuses, `P5-FXJA-D4`).

## 7. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_6J.md §2 / .json)

Grammar `FB6J1-<FAM>-<ARM>-<TAIL>-<DELAY>-S2`; DRAFT cycle token `FB6J1` (a
registered cycle ID replaces it verbatim). JF1 = 8 core + 3 controls =
**minimal 11** (CONV-B; full grid 24). Views (0 IDs): C3′ regime-change-vs-
ordinary split; C4 delay-pair adjudication; ±45-min K3 anchor ladder (all 7
variants reported, none selectable).

```
FB6J1-JF1-DRIFT-UP-D1-S2   FB6J1-JF1-DRIFT-UP-D30M-S2   FB6J1-JF1-DRIFT-DN-D1-S2   FB6J1-JF1-DRIFT-DN-D30M-S2
FB6J1-JF1-REV-UP-D1-S2     FB6J1-JF1-REV-UP-D30M-S2     FB6J1-JF1-REV-DN-D1-S2     FB6J1-JF1-REV-DN-D30M-S2
FB6J1-PLA-JF1              FB6J1-ALW-JF1                FB6J1-CLK-JF1
```

## 8. Fold / warmup law

Folds (SPEC_6J §8 DRAFT — final boundaries fixed at registration freeze):
F1 2020-01..2021-12 · F2 2022-01..2023-12 · F3 2024-01..2025-12 · F4
2026-01..2026-09; **252-session warmup carve-out excluded from scoring at each
fold head** (`fc.scoreable_sessions`). Folds multiply evaluation, never
identities. Era seams (2021 quiet / 2022 YCC / 2024–26 intervention) are
declared K-views, never fold cuts.

## 9. Owner-pending law — namespaced slots + fail-closed refusal

| slot | law | refusal behavior |
|---|---|---|
| `P5-FXJA-D1` | 6J ceiling + clock-shadow reading (no cap exists, CENSUS_FINAL §4) | `require_synthetic(6J)` refuses any non-SYNTHETIC panel (`BLOCKED_NO_CEILING`); `bind_option_6j("J-A"/"J-B"/"J-C")` refuses while unsigned |
| `P5-FXJA-D2` | DC §1.3 boundary ruling (iff J-C) | `bind_option_6j("J-C")` refuses (never self-ratified) |
| `P5-FXJA-D3` | BBO/fill ruling | any non-conservative fill request refuses; conservative law binds |
| `P5-FXJA-D4` | fee A7 posture | any VERIFIED/measured-cost label request refuses; MODELED COST binds |
| `P5-HYPO-OD2` | BoJ intraday stamps (upgrade path) | `consume_boj_intraday_stamp()` always refuses; window-convention law stands |

Real-data adapter execution: **NOT_RUN** (this lane computes nothing against
the real 6J chain; the sandbox never writes real governance/registry/GO/ledger).
