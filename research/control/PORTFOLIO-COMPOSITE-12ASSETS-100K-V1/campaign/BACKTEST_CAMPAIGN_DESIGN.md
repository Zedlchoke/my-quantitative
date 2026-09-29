# BACKTEST_CAMPAIGN_DESIGN — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO draft)

Controlled campaign for turning corpus ideas into portfolio legs. Frozen
BEFORE any scored PnL exists (none exists for any corpus idea — verified).
Laws inherited: handbook §14 (scientific protocol), §13 (PIT), §15 (trial
identity), P-8/P-9/P-19/P-20/P-27/P-29, COST_ACCOUNTING_SPEC, RGC dry-run
PnL-leak lesson, ERP-tracka truncation-replay law.

## 1. Identity of a sub-strategy (preregistered before any computation)

Every leg carries a frozen identity tuple:
`(cycle_id, sleeve_id, corpus_gid | CLASS_CANDIDATE_id, family_id, mech_key,
 mechanism_payer, clock, entry_rule, exit_rule, size_rule_key, pit_join_list,
 cost_tier, causal_control_id, outcome_exposed_label, arm_config_digest)`.

- Corpus gids enter through ladder v2 (implementability); their
  outcome-exposed label (FAMILY_HISTORY_NEGATIVE | F0_INDIVIDUAL_REJECT |
  PRIOR_NOT_SCORED) is a permanent field of the identity — per owner
  amendment 2026-09-29 (2nd), ancestry is a disclosed label, never an
  exclusion, and never a re-branding of a dead family as a new edge.
- Clock: weekly Friday 20:00 UTC decision, next-bar-open fill (PIT freeze R3;
  M1 pairs fill from the [20:00,20:01) bar, H1 pairs from the 20:00-open bar,
  Sunday-reopen deferral charged at C3). Intraday legs (session-class) may
  declare an intrabar clock from M1 bars with session marks rebuilt from
  calendar (never hardcoded DST offsets — corpus EURUSD §1.1 note).
- Representation-rho vs dead ancestor classes (P-29) is MEASURED and
  DISCLOSED per leg (informs redundancy/diversification and the
  multiple-testing narrative); it is no longer an admission kill under the
  amended law.

## 2. Stages — discovery and scored evidence are different objects

```
Stage-A  IMPLEMENTABILITY + DIAGNOSTIC BATTERY (per candidate, TRAIN-only,
         exploratory, outcome-labeled — amended law 2026-09-29)
         mechanization (exact rule compiles; params preregistered, no grids
         beyond the frozen set) -> PIT join proof at panel clock -> decision-
         count feasibility on the real calendar (floors 20/3/100) -> cost
         bill at measured spreads + DECLARED bands (×2.0 stress) -> TRAIN
         diagnostic run + causal/placebo controls -> complementarity inputs
         (PnL corr, co-loss, overlap). Labels recorded; no ancestry kills.
Stage-B  PORTFOLIO ASSEMBLY (TRAIN folds only; policy learning, see POLICY doc)
         slate grouping by complementarity, cap assignment, conflict-rule fit,
         switching-cost budget incl. missed-profit accounting. Frozen policy
         spec + freeze SHA.
Stage-C  SCORED EVALUATION (test folds, heavy lock, GO-gated)
         frozen policy vs baseline battery; robustness tiers; reproduction twin.
```

Stage-A numbers NEVER enter any publication as evidence of edge; they are
discovery, priced by the multiple-testing ledger (§5). Only Stage-C test-fold
executions are scored evidence. Every Stage-A try is a trial-ledger row
(P-9: observed denominator counts even failed publications).

## 3. Fold calendar (reuses the sleeve-verified 286-Friday arithmetic)

- Window 2021-01-08 → 2026-06-26 (panels re-measured at registration; H1
  pairs end 2026-06, M1 pairs run to 2026-09 — the M1 tail beyond 2026-06-26
  is NOT used, keeping one common calendar; extension is an owner amendment).
- 52-week warmup · 8 test folds × 26 weeks · 1-week embargo between train
  and test · remaining 26-week sealed tail = SEALED (S1-class, untouched).
- Walk-forward: expanding train (fold k uses all data before test fold k
  minus embargo). ≥6 test folds or `NOT_RUN_INSUFFICIENT_CALENDAR`.
- Sample floors per leg per fold (weekly-clock adaptation of the frozen
  20/3/100 triplet): ≥20 decisions on full window, ≥3 per fold, ≥100
  aggregate — floor failure = typed `NOT_RUN_THIN`, permanent FLAT leg row.
  Floors are frozen BEFORE Stage-A; no post-hoc relaxation (RSM mirage law;
  PR12A F2/F3 lesson recorded).

## 4. Costs, fills, accounting

- Cost kernel per COST_ACCOUNTING_SPEC + COST_AUTHORITY_TABLE: measured
  spread schedule (C1/C2/C3) + DECLARED pessimistic commission U2 (0.35 bps
  side), slippage U3 (0.2/1.0 pip), swap U4/U5 (1.0 pip/night against,
  Wed ×3, never income). GROSS and NET dual books; NET_DEFAULT_COST label
  mandatory on every survivor until the owner statement lands.
- Stress tiers ×1.0 / ×1.5 / ×2.0 on ALL cost components; a leg whose
  TRAIN expectancy dies at ×1.5 is COST_DOMINATED (typed kill).
- $100k book accounting per SHARED-PORTFOLIO-100K-V1 precedent
  (portfolio_lib laws): UNAVAILABLE ≠ 0; cash/positions/equity reconcile
  per bar; vehicle mixing forbidden (FX spot only at registration).

## 5. Multiple testing and the trial ledger

- TRIAL_LEDGER.jsonl (append-only, schema trial_ledger@1): every Stage-A
  try, every fold grid node, every Stage-B policy variant, every Stage-C
  arm, each with arm_config_digest + data_snapshot_digest + code_freeze_sha.
- Discovery-side corrections computed over the FULL ledger at Stage-C:
  DSR (deflated Sharpe) over all completed trials with pass condition
  **DSR > 0.95** (skeptic F-1: "DSR > 0" is vacuous — Φ(·) is strictly
  positive; the 0.95 threshold makes the bar bind: the policy's SR must
  exceed the expected max of N null Sharpes at the 95% level); PBO via CSCV
  on the discovery ledger with cluster-adjusted N_eff (correlated trial
  clusters — e.g. one family's shape×pair grid — count as one effective
  trial family; skeptic F-11); fold-concentration ≤50%; P-20
  arm-distinctness disclosed as measured rho (informative under the
  amended law).
- Expected false-edge arithmetic at the amended width (skeptic F-8
  refresh): a 1,500-row discovery ledger manufactures ~75 false "edges"
  at α=0.05 before any real one; DSR/PBO price exactly this. This is why
  discovery rows are TRAIN-only and the SCORED surface stays at ≤48
  identities. Scoring all 1,200 as evidence was never lawful and remains
  off the menu; the owner's wide-survey demand is met by the labeled
  discovery ledger, not by widening the scored surface.
- Fold-edge force-flat disclosure (skeptic F-7): fold-edge force-flats
  charge arms differentially by their fold-edge holdings — a systematic
  asymmetry between the policy and always-on baselines. Every Stage-C
  report must include per-arm fold-edge force-flat cost totals so P1's
  PnL leg can be read net of the asymmetry.

## 6. Budget — SUPERSEDED TIERS (v1-era) + v2 operative budget

> **ANNOTATION (A1, post-amendment + skeptic F-8/F-19):** the tier table
> below is v1-era (novelty-gated law, "runnable set is empty" headline).
> Under the amended law the operative numbers live in plan v2 §4: ladder
> v2.1 = 294 screen-passing rows; triage = the binding input-availability
> layer (147 runnable at the 292-row vintage, being updated for the
> 294-row delta); discovery-ledger cap 1,500 rows; Stage-C ≤48 scored
> IDENTITIES plus the B4 random battery as one identity executed as
> ≤128 seeded sub-runs on its own disclosed budget line (skeptic F-3
> counting unit); Stage-A worst case ≈500 engine runs breadth-first
> (Lane R sequencing). The tier table is retained as history.

| tier | precondition (owner action) | candidate legs | Stage-A rows | Stage-C scored arm-executions | wall-clock estimate* |
|---|---|---|---|---|---|
| T0 | none (today) | 0 | 0 | 0 | — (cycle cannot open; this is the honest default) |
| T1 | P_A statement | still 0 mechanisms | 0 | 0 | statement ingestion + cost-kernel re-freeze ≈ 1 session |
| T2 | P_B (+P_A recommended) | 3 corpus rows + ≤9 fresh class candidates (class spec cap) | ≤12 admission rows (+≤54 class-parameter grid nodes TRAIN-only) | ≤24 (policy 1 + baselines 9 + robustness 14: cost tiers ×3, leave-one-leg, switching ladder, controls re-runs) | ≈ 2–4 h scored under heavy lock (5.7y M1 replay × ~10 legs; btcombo6-class engine already sustains this scale) |
| T2+P_C | + ERP1 M1 re-fetch | +2 rows re-adjudicated | ≤14 | ≤26 | +1–2 h (M1 ingest dominates) |
| T3 | + P_D symbol data (any subset) | +data-checkable rows (≤411) — attrition expected ≥45.7% variant + F-0 court | priced per acquisition cycle (own plan; NOT this cycle) | own cycle | months, multi-cycle |

*T2 estimate assumes the deterministic M1 panel replay engine from prior
cycles (fx-rangefade/fx-majors panels are local .bi5; ingestion one-off).

Batching: T2 runs as ONE batch after P_B class spec freeze; T2+P_C as a
second batch appended under the same frozen protocol (class spec unchanged,
ledger continues). Ledger overflow at any point → STOP → owner decision.

Budget caps for the draft plan (owner amends at registration):
trial-ledger rows ≤ 300; Stage-C scored arm-executions ≤ 48; legs in the
assembled portfolio ≤ 12; policy variants in Stage-B ≤ 8 (frozen grid).
A NO_ELIGIBLE_PROPOSAL close at Stage-A (0 legs) is a first-class outcome
priced at 0 scored cells — precedent SLEEVE-FX5.

## 7. Stop rules (typed, before any scored PnL)

- STOP-0 registration gate: pools not opened → T0 stands, nothing runs.
- STOP-1 discovery gate: after Stage-A + Stage-B, before Stage-C: if 0 legs
  admitted OR policy spec cannot beat its own null-preview on TRAIN → close
  `NO_ELIGIBLE_PROPOSAL` / `POLICY_NO_PROSPECT`, 0 scored cells.
- STOP-2 budget gate: ledger overflow → stop, owner decision.
- STOP-3 integrity gate: any no-lookahead/PIT/accounting test fails →
  `NOT_RUN_INTEGRITY`, remediation loop, no silent continue.

## 8. Verification battery (pre-scored, exact-arm)

1. No-lookahead truncation replay: recompute fold k with data truncated at
   its start; results must be prefix-identical to the full run's prefix.
2. PIT joins: every macro/feature join keyed on available_time (EFFR d+1
   15:00 ET, VIX d 16:15 ET, Brent−WTI ≤ decision−10 calendar days);
   staleness fail-closed.
3. Accounting: journal↔positions↔cash↔equity reconcile per bar, zero
   residual; UNAVAILABLE ≠ 0.
4. Determinism: two independent runs byte-identical; reproduction twin on
   detached worktree at freeze SHA.
5. Exact-arm dry-run WITHOUT PnL (RGC-INC-1 law): prints arm identities,
   decision counts, fill counts, cost-bill totals only — never PnL/Sharpe.
