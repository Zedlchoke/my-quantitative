# ADAPTER_MAP_6J_6A — per-family mapping: candidate → SPEC → draft → adapter → fixtures → tests → blockers

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-FXJA**, 2026-10-05.
- **PROPOSED throughout.** All adapters are synthetic-sandbox machinery:
  SIGNALS + intended ORDER INTENT on synthetic fixtures only. Real-data
  consumption refuses fail-closed: 6J on **P5-FXJA-D1** (owner 6J ceiling —
  no cap exists, unsigned), 6A on the **P5-FXJA-D5** chain (PB3 lift → D8 →
  D9 → D2 → ABS/China calendar — 6A stays **PB3 PARK**; the 6A adapters are
  CONTINGENCY machinery, **never activated**). Real-data adapter execution on
  both symbols = **NOT_RUN**.
- Slot registry: `fx_common.GUARDS` = {P5-FXJA-D1..D5, P5-HYPO-OD2..OD4}, all
  `None` (unsigned). No lane may sign. Freeze-gates: `bind_option_6j`,
  `jf2_freeze_check`, `af1/af3/af4/rmm6a_freeze_check`.
- Outcome-blind: 0 PnL, 0 scored runs, 0 registrations, 0 network.

## 6J families (SPEC_6J.md; draft token FB6J1; IDENTITY_BUDGET_6J §2)

| candidate | SPEC section | rule draft | adapter | fixtures | tests | blockers (all owner slots, fail-closed) |
|---|---|---|---|---|---|---|
| **JF1** BoJ MPM window (11 IDs: `FB6J1-JF1-{DRIFT,REV}-{UP,DN}-{D1,D30M}-S2` + PLA/ALW/CLK) | SPEC_6J §2/§3/§6 (window-convention law; K3 ANCHOR_INSENSITIVE_AT_45MIN delivered; stamps NOT_IN_CORPUS) · CENSUS JF1 dossier | `jf1_boj_mpm/FROZEN_RULE_DRAFT.md` | `jf1_boj_mpm/adapter.py` (`build_observables`/`signal`/`order_intent`/`apply_exclusions`; 6J sign law implemented + tested) | `fixtures/jf1_panel_mpm.json` + `jf1_calendar.json` + `EXPECTED_MANIFEST.json` (27 synthetic MPM dates + controls; BoJ-window day; excluded holiday/roll/MOF-op/unverified-window days; TP-hit + SL-hit showcases; independent reference) | `test_adapter_jf1.py` — 21 passed | P5-FXJA-D1 (ceiling; `BLOCKED_NO_CEILING`) · P5-FXJA-D3/D4 (fill/cost postures) · P5-HYPO-OD2 (BoJ stamps — consumed only via the always-refusing helper) |
| **JF3** Tokyo-morning (11 IDs: `FB6J1-JF3-{CONT,FADE}-{UP,DN}-{D1,D30M}-S2` + PLA/ALW/CLK) | SPEC_6J §3/§4 (≥80% Tokyo-window coverage; DST-correct JST bucketing; C3″ falsifier) · CENSUS JF3 dossier (row-34 dead adjacency carried) | `jf3_tokyo_morning/FROZEN_RULE_DRAFT.md` | `jf3_tokyo_morning/adapter.py` | `fixtures/jf3_panel_tokyo.json` + calendar + `EXPECTED_MANIFEST.json` (range-break UP/DN days; coverage-fail day; CT-bucketing DST probe) | `test_adapter_jf3.py` — 14 passed | P5-FXJA-D1 · D3/D4 · (row-34 placebo set binds any scored future) |
| **JF2** MOF regime — **MACHINERY ONLY** (7 IDs/host: `FB6J1-JF2-{DRIFT,REV}-{UP,DN}-REG-S2` + PLA/ALW/CLK; 0 own signal) | SPEC_6J §6 (MOF ex-post-only + lag law, DC §1.4) · CENSUS JF2 dossier · HYPO_GAPS P5-HYPO-OD4 | `jf2_mof_regime/FROZEN_RULE_DRAFT.md` | `jf2_mof_regime/adapter.py` (disclosure-lag label machinery; host conditioning; same-day op read always refuses) | `fixtures/jf2_panel_host.json` + `jf2_calendar.json` (host = JF1 panel + synthetic ops with ~1-month disclosure lag) | `test_adapter_jf2.py` — 13 passed | **P5-HYPO-OD4** (zone-threshold constant — `jf2_zone_threshold()` + `jf2_freeze_check()` refuse; the block cannot freeze) · P5-FXJA-D1 |
| **RMM 6J leg** — **MACHINERY ONLY, J-C only** (4 IDs: `FB6J1-RMM-MCOMPRESS-{REV,CONT}-{D1,D30M}`) | SPEC_6J §5 (chain + cease-guard + 2022-09-20 law case) · CENSUS RMM dossier (Role-A 19/8 CLOSED; Role-B NEEDS_EVIDENCE) | `rmm_6j_leg/FROZEN_RULE_DRAFT.md` | `rmm_6j_leg/adapter.py` (mode ledger + guard disclosure + event clock; intent refuses even on synthetic) | `fixtures/rmm6j_panel_rollweek.json` + `rmm6j_roll_rows.json` (the cease-guard WEEK: U2 zero bars on the switch date, Z2 full day; baseline-vs-explicit chain; event-stacking roll) | `test_adapter_rmm6j.py` — 9 passed | **P5-FXJA-D1** then **P5-FXJA-D2** (DC §1.3 — never self-ratified) · interaction measurement NOT_RUN (the named missing evidence) |

## 6A contingency families (SPEC_6A_CONTINGENCY.md; PB3 PARK; frozen 26-ID table sha `1a96b8ea…`, total today 0)

| candidate | SPEC section | rule draft | adapter | fixtures | tests | blockers |
|---|---|---|---|---|---|---|
| **AF1** RBA decision-±5' (K0 thin-n kill PRE-REGISTERED; K2 expected; 8+3 shapes) | SPEC_6A §1-2/§4/§6 · CENSUS AF1 dossier | `af1_rba/FROZEN_RULE_DRAFT.md` (CONTINGENCY-PB3-PARK) | `af1_rba/adapter.py` (14:30-Sydney DECLARED anchor — time NOT carried, consuming a stamp refuses; era-1 trade intent raises `REFUSED_ERA1_DESCRIPTIVE_ONLY`) | `fixtures/af1_panel_rba.json` + calendar + manifest (era-2 RBA dates; FOMC day + spillover; **era-1 refusal fixture** 2020-06-02 on the 1e-4/$10 grid) | `test_adapter_af1.py` — 11 passed | **P5-FXJA-D5** (`BLOCKED_PB3_PARK`) · D8 (era law ratification) · K0 structure |
| **AF3** bimodal U-curve (8+3 shapes) | SPEC_6A §1-3/§5 (K4 China-window kill; C3″ DST falsifier) · CENSUS AF3 dossier | `af3_bimodal/FROZEN_RULE_DRAFT.md` (CONTINGENCY-PB3-PARK) | `af3_bimodal/adapter.py` (Sydney 09:30–11:30 range break; Shanghai-window membership via Asia/Shanghai; K4 intent refusal `REFUSED_CHINA_CALENDAR_NOT_RUN`) | `fixtures/af3_panel_sydney.json` + calendar + manifest (ROT/ABS break days OUTSIDE the Shanghai window; **K4 contamination day INSIDE 09:30–10:00 Shanghai**; coverage-fail day) | `test_adapter_af3.py` — 10 passed | **P5-FXJA-D5** · **P5-HYPO-OD3** (ABS/China calendars NOT_RUN — K4 boundary) · D8 |
| **AF4** tick-regime overlay (**0 standalone identities** — host era-split + 6J same-date control) | SPEC_6A §2/§5 (NO-BACK-CAST law; step test; K1–K4) · CENSUS AF4 dossier | `af4_tick_regime/FROZEN_RULE_DRAFT.md` (CONTINGENCY-PB3-PARK) | `af4_tick_regime/adapter.py` (era split; micro-step stats; **`order_intent` refuses unconditionally** — no entry ever defined from the tick era) | `fixtures/af4_panel_6a.json` + `af4_panel_6j.json` (same-date set; 6A USD step ×0.50, 6J ×1.00) | `test_adapter_af4.py` — 6 passed | **P5-FXJA-D5** · overlay law (K1 null = identity with host) |
| **RMM 6A leg** (**4 contingency IDs**; explicit cease-guard MANDATORY — 2 measured baseline violations) | SPEC_6A §3 · CENSUS RMM-6A leg | `rmm_6a_leg/FROZEN_RULE_DRAFT.md` (CONTINGENCY-PB3-PARK) | `rmm_6a_leg/adapter.py` (mandatory-guard disclosure; era-1 switch sessions descriptive-only; intent refuses D5→D2) | `fixtures/rmm6a_roll_rows.json` (the two named violations + era-1/era-2 rolls) | `test_adapter_rmm6a.py` — 6 passed | **P5-FXJA-D5** then **P5-FXJA-D2** · D9 ratification posture |

## Test totals (this wave, all synthetic, all exit code 0)

JF1 21 · JF3 14 · JF2 13 · RMM-6J 9 · AF1 11 · AF3 10 · AF4 6 · RMM-6A 6 =
**90 tests, 90 passed, 0 failed, 0 skipped** (full-run command in the handoff).

## Shared machinery (`fx_common.py`) — law carriers

QUOTE-DIRECTION LAW + orientation proof · contract binding (6J single-era,
6A two-era with the measured boundary; drift refuses) · slot registry +
`RefusedPendingOwnerDecision` + the five typed refusals (BoJ stamp, era-1,
MOF lag, RBA time, China calendar, AF4 no-entry) · era-aware modeled-cost
ladders (COST_CONTRACT §1-3 arithmetic: 67.42/8.4499 bp, 54.92/8.2019 bp,
104.92/15.1794 bp) with fee-invariant stress + session floor · fold law
(F1–F4 + 252 warmup) · exclusion engine (CALENDAR §5 inventory) · MOF
disclosure-lag label machinery + null-era audit · roll chain builder
(baseline vs explicit cease-guard, timing law, sign-non-flip) + mandatory
guard disclosure · identity enumeration (FB6J1 cores/controls; C6A0
contingency shapes; frozen-table citation) · fold-floor + DST-falsifier +
C1-shadow helpers.

## What this wave did NOT do (outcome-blind law)

No real-data consumption; no conditional-on-signal statistics on real panels;
no scoring; no registration; no GO; no writes outside
`adapt_fx_ja/**` + `dispatch/handoff_ADAPT-FXJA.json`; no commits; the
frozen 26-ID 6A table was consumed verbatim and NOT expanded; no identity
budget option was bound (all bindings refuse while P5-FXJA-D1 is unsigned).
