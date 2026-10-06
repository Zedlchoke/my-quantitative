# FROZEN_RULE_DRAFT — NQ-F4 ROLLWK Role-B (PROPOSED — never an approved freeze)

- Round **FUTURES-5SYM-PRESCORED-20261005**, wave-3, lane **ADAPT-NQ**, 2026-10-05.
- **STATUS: PROPOSED / MACHINERY-ONLY.** The Role-B interaction gate is **NEEDS_EVIDENCE**
  (the roll-week x session-type interaction has never been measured — it IS the family's K6
  gate; `CENSUS_5SYM.md` NQ-F4 row §2/§12; `IDENTITY_BUDGET_NQ.md` §1 "Role-B K6 interaction =
  scored-side NOT_RUN by law"). This adapter therefore delivers **machinery only**: the Role-A
  roll-construction audit (0 identities, standing law) + the roll calendar/observables + a
  hard Role-B intent gate. **Every `order_intent` raises
  `ROLE_B_INTERACTION_GATE_NOT_EVIDENCED`** — no Role-B signal exists lawfully.
- Parents: `../../nq/SPEC_NQ.md` §7 (Role-A standing law NEW-4) ·
  `../../nq/IDENTITY_BUDGET_NQ.md` §1/§3 · `../../hypo/CENSUS_5SYM.md` NQ-F4 row ·
  `HYPOTHESES_R2 §8` (Role-B convention = +4 IDs/leg, Role-A = 0 IDs —
  `FUTURES-SIX-ADOPT-PREP-20261004/hypo/HYPOTHESES_R2.md` §8) ·
  `../../exec/RUNNER_COMPAT_NQ.md` RC-6.2 (F4 → roll-week calendar + NEW-4 audit).
- Shared machinery (PIT reads, H1..H5 + FOMC exclusions, cost ladder, decision slots,
  fold/warmup, tick binding) = `../f1_fomc_era/FROZEN_RULE_DRAFT.md` via `../nq_common.py`.

## 1. Observables and their timestamp-availability law (PIT)

| observable | definition as coded | knowable at (PIT) |
|---|---|---|
| candidate volumes | per-session per-contract volumes injected in the panel (`sessions[].cand_volumes`) — the `held_volume_k5_v3` class | session close |
| roll switch date | trailing-**k=5**-session MEAN volume, hold the max-mean candidate; decided from sessions `[t-k, t-1]` (decided t-1), **held from t** (chain law, `FREEZE_BUILDER_SPEC_NQ.md` §2; `nq_f3_rebuild_a1a2.json` roll_rule) | the switch session t, from t-1 data |
| spread adjustment factor | per switch session (chain data: `v3_rolls_spread_stats` class) — required by the corr-0.999 phantom-drift law | chain data |
| dte | expiry − switch date, injected expiry (authority calendar, 68/68 quarters) | chain data |

## 2. Role-A construction audit (0 identities — standing NEW-4 law, binds EVERY NQ run)

`role_a_audit(panel)` returns `{pass, failures[], binding}`:
- **MISSING_SPREAD_ADJUSTMENT** — a switch session without a spread adjustment factor
  (corr-0.999 phantom-drift law).
- **DTE_OUT_OF_RANGE** — dte outside [0, 45] (the v2 dte>45 quarantine is retired; 66/66 v3
  rolls satisfy 0 <= dte <= 45).
- **CEASE_GUARD_VIOLATION** — an injected cease-guard violation on the cg chain (v3 measured: 0).
**A Role-A failure kills the RUN, never the hypothesis** (SPEC §7 NEW-4). The fixture proves
both a PASS and a FAIL path (factor stripped ⇒ audit fails).

## 3. Role-B conditional (gate NOT EVIDENCED — no signal may exist)

- Would-be law sketch (census F4 §5, INFERENCE-grade): roll-week membership conditioning,
  arms defined on the interaction measurement, entry next-bar open after switch. **Not
  implemented**: the interaction measurement is the missing evidence; the K6 gate failing ⇒
  the family never forms beyond Role-A.
- Machinery exposes: `roll_calendar(panel)`, `roll_week_membership(panel)` (the k=5 crossover
  window sessions), and `event_stacking_flags` (switch sessions overlapping scheduled events —
  FOMC/BLS stamps — flagged `EVENT_STACKING` for any future conditioning; exclusion law,
  census F4 §6).
- `order_intent(...)` raises `RoleBInteractionGateNotFormed`
  (code `ROLE_B_INTERACTION_GATE_NOT_EVIDENCED`) for EVERY identity, core or control.

## 4. Exclusions (machinery layer, fail-closed)

H1/H2/H3/H4/H5 + FOMC standing-outside via `nq_common` (include_fomc=True — F4 is not an
event family). Event-stacking flags on switch sessions are informational machinery (any future
Role-B conditioning would exclude them).

## 5. Tick / multiplier / cost binding

As F1 §6 (ramp-session fills plausibly worse than median — no claim beyond the {1,2,3}-tier
triple is legal; MODELED / UNDER REVIEW).

## 6. Identity enumeration (exact DRAFT IDs, quoted from IDENTITY_BUDGET_NQ.md §3)

NQ-F4 Role B = 4 core + 3 controls = **minimal 7** (CONV-B; Role-A carries 0 identities; full
grid 4 Role-B — the census "full 4" is the Role-B core itself):

```
FBNQ1-F4-CONT-UP-D0-S2   FBNQ1-F4-CONT-DN-D0-S2   FBNQ1-F4-REV-UP-D0-S2   FBNQ1-F4-REV-DN-D0-S2
FBNQ1-F4-SHDW-D0-S2      FBNQ1-F4-ALW-D0-S2       FBNQ1-F4-FLAT
```

These IDs are ENUMERABLE DRAFT strings only — no Role-B signal may be minted against them
while the interaction gate is unevidenced. Option binding raises
`RefusedPendingOwnerDecision("P5-NQ2")` while unsigned; NQ-D refuses unconditionally.

## 7. Fold / warmup / decision slots

As F1 §8/§9 (P5-NQ1 real-chain gate — the v3 roll set itself is D9-blocked for real
consumption; P5-NQ2 ceiling; P5-NQ3 cost basis; P5-NQ4 tick defect; P5-NQ5 EXPWITCH refusal;
P5-NQ6 2026 posture).

— End FROZEN_RULE_DRAFT (PROPOSED). Machinery-only; nothing herein freezes, registers,
scores, or ratifies.
