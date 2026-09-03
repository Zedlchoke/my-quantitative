# A7-TERMINAL — V11 wave-2 audit (ILLIQ finalization + sprint close)

Auditor: A7-TERMINAL (independent). Base: `062dfcb` (my wave-1 commit, merged to
integration as `4160eec`); integration head audited: `85c14a7`. Lineage
verified (`a348122` and `4160eec` both ancestors of `85c14a7`); the only
integration changes since wave 1 are `family_verdict_illiq.json`,
`reproduction_report_illiq.json` and one event-log line — **zero changes to
research/v11/ or research/adapter_v10/ code**.

**Final terminal audit verdict: APPROVED (0 FAIL).**
**Confirmed sprint verdict: `V11_REJECT_ALL`.**

## Items

### W2-1 ILLIQ Stage-A gates — PASS (verdict V11_FAMILY_REJECT confirmed)
Recomputed with my own arithmetic from the exec-tree artifacts (3 arms x 6
cells). Anchor: net 0.581969254868 (daily basis, exact), PF 1.354841010840,
MDD 0.091821657373, 3/3 folds positive (fold PF 1.260 / 1.083 / 1.781), hit
24/52, 336 positions; stress cells all positive with PF >= 1.3526; neighbour
0.666536688576 (PF 1.3896); control −0.604185027886 (PF 0.7322, 0 positive
folds) — all match the verdict file.

**Concentration figure CONFIRMED:** largest positive-fold share =
0.705496856297 → **0.7055** (fold_metrics basis: F2 0.410577479771 of positive
total 0.581969254868). My positions-basis arithmetic gives 0.70226; the
difference is exactly the cost-allocation basis (positions carry allocated
cost, fold_metrics the full charged cost — same benign basis as LOT in wave
1). On either basis the share exceeds 0.50.

My failed-gate set equals the producer's exactly:
`{no_positive_fold_gt_50pct_of_positive_pnl}` — single frozen gate breach ⇒
`V11_FAMILY_REJECT` (12/13 PASS still rejects under the frozen all-gates
contract).

### W2-2 Vacuous drop_one_symbol — disclosed caveat (no outcome impact)
The ILLIQ drop_one_symbol cell drops 1000PEPEUSDT, which is in the 19-symbol
universe but held **zero positions** in both the anchor and neighbour
baselines; the cell reproduces the baseline byte-for-byte in metrics (336
positions, net identical). The survival PASS therefore carries no falsification
information for ILLIQ. The producer's gate detail discloses the identical nets
transparently. ILLIQ is rejected on concentration regardless; LOT's drop cell
was non-vacuous. Lesson recommendation: future drop-one-symbol cells should
drop a held symbol.

### W2-3 Reproduction spot-checks — PASS (5/5)
My own payload hashes (artifact minus hashes/artifacts, frozen `<TREE_ROOT>`
normalisation) equal across exec/repro for: LOT-RESSKEW-30D-W baseline
(`d779854c…`) + drop_one_symbol (`169e5db5…`); ILLIQ-AMIHUD-56D-W baseline
(`274718e2…`) + plus_2_ticks (`2ae5173f…`) + drop_one_fold (`c9e751f6…`) —
all match the two reproduction reports. Cumulatively A7 has independently
verified 10 of the 33 claimed ALL_MATCH cells with zero mismatches.

### W2-4 Final ledger — PASS
`verify_append_only == True`; canonical V11 ledger = exactly 6 CELL_RESULT
rows (LOT 3 + ILLIQ 3); trial keys unique, all 6 recompute from payloads, all
6 arm digests tie to `selection_freeze.json`; shard_lot (3) and shard_illiq
(3) keys are disjoint and their union equals the canonical keys; denominator
view = **{published: 6, observed_unpublished: 0}**; the 2 defective
zero-position OILEV rows remain quarantined and outside the ledger. Final
budget: 6 eligible computed ≤ 9 eligible ≤ 12; OILEV 0/3 (blocked pre-score,
no rescue); DEF 3 slots unused; +2 disclosed PIPELINE_ERROR computations.

### W2-5 Sprint verdict + amendment — PASS
Family outcomes: LOT REJECT, ILLIQ REJECT, OILEV BLOCKED (pre-score). With
zero Stage-A survivors, prelaunch passed, and Phase E/R complete, the only
applicable allowed outcome under PLAN 15 is **`V11_REJECT_ALL`**
(`…SURVIVORS…` inapplicable; `BLOCKED_PRELAUNCH` inapplicable;
`INCOMPLETE_NOT_PROMOTABLE` inapplicable). The deferred-historical-merge
amendment is byte-unchanged since wave 1 and remains fail-closed honest
(119-merge UNAVAILABLE_FAIL_CLOSED, exactly-once cross-check before any
merge). Note: `heartbeat.json` at `85c14a7` still shows the in-flight state
(predates ILLIQ completion); A1 should close it when declaring the sprint
verdict — it does not affect any recomputed outcome.

## Evidence files
- `a7_terminal_wave2.json` — itemized machine verdicts
- `scripts/a7w2_item_illiq_gates.py`, `scripts/a7w2_item_repro_spots.py`,
  `scripts/a7w2_item_ledger.py` — rerunnable audit method
- `w2_illiq_raw_output.json`, `w2_ledger_raw_output.json` — raw outputs
- `evidence/family_verdict_illiq_at85c14a7.json`,
  `evidence/reproduction_report_illiq_at85c14a7.json` — audited control bytes
