# ADAPTER_MAP_NQ — candidate → SPEC → rule draft → adapter → fixtures → tests → blockers

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-NQ**, 2026-10-05.
- All artifacts live under `research/control/FUTURES-5SYM-PRESCORED-20261005/adapt_nq/`.
- Every rule draft is **PROPOSED** (never an approved freeze). Every adapter is
  **synthetic-only**: real-data provenance refuses (`P5-NQ1`); real-data adapter execution
  = **NOT_RUN** (D9 + ceiling + D3 + registration-gated).
- Shared machinery: `nq_common.py` (session/era law, H1..H5 + FOMC exclusions, coverage
  register, cost ladders, decision-slot guards, fold/warmup, K-views, identity grammar,
  contract binding from `exec/symbol_contracts.json`). `expwitch_refusal.py` is the
  EXPWITCH-NQ refusal stub. `fixture_kit.py` + per-family `fixtures/gen_fixtures.py` +
  `fixtures/reference_expected.py` (independent expectation computation) + committed
  fixture JSON + `EXPECTED_MANIFEST.json` per family.

| family (candidate) | SPEC / owning docs | rule draft (PROPOSED) | adapter | fixtures (committed) | tests | status | blockers (all owner-side / post-approval) |
|---|---|---|---|---|---|---|---|
| **NQ-F1 FOMC-ERA** (11 IDs: 8 core + 3 controls) | `nq/SPEC_NQ.md` §4/§6/§7 · `CALENDAR_PIT_POLICY_NQ.md` §4 · `CENSUS_5SYM.md` NQ-F1 · `IDENTITY_BUDGET_NQ.md` §1/§3 | `f1_fomc_era/FROZEN_RULE_DRAFT.md` | `f1_fomc_era/adapter.py::FomcEraAdapter` (build_observables / signal / order_intent / apply_exclusions) | `f1_fomc_era/fixtures/`: f1_panel_core (UP day + SHDW Wednesday + H1 day), f1_panel_july_dn (DN day), f1_panel_era_boundary (era-A 16:15 close day), f1_panel_exclusions_2026 (H2/H3 + H4) + EXPECTED_MANIFEST | `f1_fomc_era/test_adapter_f1.py` — 23 passed | ADAPTER + TESTS PASS | P5-NQ1 (D9) · P5-NQ2 (ceiling + shadow reading) · P5-NQ3 (D3 basis) · P5-NQ6 (calendar-2026) · registration gate |
| **NQ-F2 MACRO-0730** (11 IDs) | `nq/SPEC_NQ.md` §4 · `CALENDAR_PIT_POLICY_NQ.md` §5 (vintage law, D5 pin) · `CENSUS_5SYM.md` NQ-F2 | `f2_macro_0730/FROZEN_RULE_DRAFT.md` | `f2_macro_0730/adapter.py::Macro0730Adapter` (vintage-known_by membership; D5-pin refusal; scoring-era confinement 2023-26; canceled stratum) | `f2_macro_0730/fixtures/`: f2_panel_core (CPI UP w/ TP hit + same-bar SL-priority short, CPI DN close-exit, SHDW clock day, CPI-on-FOMC day), f2_panel_era_gated_2019, f2_panel_canceled_2025, f2_panel_2026_d5 + EXPECTED_MANIFEST | `f2_macro_0730/test_adapter_f2.py` — 16 passed | ADAPTER + TESTS PASS | same as F1 (+ latency/surprise NOT_RUN inherited) |
| **NQ-F3 RUN-REV-NQ** (7 IDs) | `CENSUS_5SYM.md` NQ-F3 · rebuild precondition harness REFERENCED not duplicated: `FUTURES-K6GATE-PREP-20261004/nq/k6_compute_m34.py` + `nq_f3_rebuild_a1a2.json` (ret == `nq_held_daily_v3`, max diff 0.0, n=4,218) | `f3_run_rev/FROZEN_RULE_DRAFT.md` | `f3_run_rev/adapter.py::RunRevAdapter` (k=5 first-crossing trigger on held daily closes; REV vs CONT; fixed 5-held-session horizon; roll-cross refusal; entry/exit PIT day-law) | `f3_run_rev/fixtures/`: f3_panel_daily (3 engineered runs: roll-cross window, clean window, FOMC-entry window) + EXPECTED_MANIFEST | `f3_run_rev/test_adapter_f3.py` — 13 passed | ADAPTER + TESTS PASS | same as F1 (+ a1/a2 aggregates beyond the rebuilt ret series remain hole-era until re-run; K3 concentration measurable at run time) |
| **NQ-F4 ROLLWK Role-B** (7 draft IDs; Role-A = 0 IDs) | `CENSUS_5SYM.md` NQ-F4 · `SPEC_NQ.md` §7 NEW-4 · HYPOTHESES_R2 §8 (Role-B convention = +4 IDs/leg) · `FREEZE_BUILDER_SPEC_NQ.md` §2 (k=5 chain law) | `f4_rollwk/FROZEN_RULE_DRAFT.md` (**MACHINERY-ONLY**) | `f4_rollwk/adapter.py::RollWkAdapter` (Role-A roll calendar + NEW-4 audit + roll-week membership + event stacking; `order_intent` HARD-refuses: `ROLE_B_INTERACTION_GATE_NOT_EVIDENCED`) | `f4_rollwk/fixtures/`: f4_panel_roll (crossover 2023-09-13, PIT walker asserted, spread factor present/stripped paths) + EXPECTED_MANIFEST | `f4_rollwk/test_adapter_f4.py` — 8 passed | MACHINERY-ONLY (interaction gate NEEDS_EVIDENCE — the family K6 measurement is the missing evidence) | the K6 interaction measurement itself (0-ID PREP item) + same owner gates as F1 |
| **EXPWITCH-NQ leg** (DEAD-AT-GATE; 0 IDs minted) | `nq/SPEC_NQ.md` §8.1 · `NQ_K6_GATES.md` §2 · `IDENTITY_BUDGET_NQ.md` §1/§3 · `RUNNER_COMPAT_NQ.md` RC-6.3 | none (refusal stub only, by law) | `expwitch_refusal.py` (function + object stub; every request refuses, code `EXPWITCH_DEAD_AT_GATE`) | none (by law) | `test_expwitch_stub.py` — 5 passed | REFUSAL STUB ONLY | P5-NQ5 (owner data-plane disposition; until ruled, excluded from every slate, never re-litigated) |

Cross-family: `TRADE_JOURNAL_SCHEMA.md` (per-trade record + reconciliation contract vs
`exec/scored_runner_v2.py` ledger). Shared refusal/gate surface (`nq_common.py`):
`RefusedPendingOwnerDecision` slots P5-NQ1/2/3/5/6 · `RefusedD5PinMissing` ·
`RefusedSessionMaskMismatch` · `bind_option` (P5-NQ2; NQ-D → EXPWITCH refusal) ·
`unexclude_2026` (P5-NQ6) · `$2.50/tick` refuse (P5-NQ4 guard).

## Test summary (this lane, `.venv/bin/python -m pytest . -q`, from adapt_nq/)

```
65 passed
```
(f1 23 · f2 16 · f3 13 · f4 8 · expwitch stub 5 — counts as of 2026-10-05; the handoff
records the final full-suite summary line.)

## Explicit NOT_RUN register (lane-wide)

1. Real-data adapter execution — NOT_RUN (P5-NQ1 + P5-NQ2 + P5-NQ3 + registration).
2. Real chain consumption (cache_v3 panels, v3 roll set, held daily series at scale) — NOT_RUN.
3. Real FOMC/BLS stamps (132 statements, 204+204 CPI/EMPSIT vintages) — NOT_RUN (fixtures are
   synthetic echoes of the committed calendars).
4. Per-family MDE tables on the repaired series — NOT_RUN (post-freeze arithmetic).
5. F4 Role-B interaction measurement — NOT_RUN (the family's K6 gate; NEEDS_EVIDENCE).
6. Direct vendor contract-definition capture for NQ (multiplier/tick) — NOT_RUN (P5-NQ4-adjacent;
   identity rests on the committed arithmetic triangulation).
7. VERIFIED_VS_ACCOUNT — NOT_RUN everywhere (no account read; MODELED-COST labels carried).
