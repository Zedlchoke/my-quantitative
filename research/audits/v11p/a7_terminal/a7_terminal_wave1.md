# A7-TERMINAL — V11 Phase E/R wave-1 terminal audit

Auditor: A7-TERMINAL (independent). Head audited: `a348122` (detached, clean).
Verdict: **10/10 items PASS, 0 FAIL.** ILLIQ items are PENDING for wave 2
(chain still executing at audit time). Every number below was recomputed by
A7-TERMINAL from raw bytes/artifacts; producer claims were never trusted.

## Item verdicts

1. **Pin chain — PASS.** `a348122` descends from `c97283e` (push-verified tip)
   and from W11 `befbd20346e...`. `git diff befbd2034..a348122` touches 28
   files, all control-plane/evidence (`research/audits/v11p/*`,
   `research/control/v11_run/*`, `CONTINUE.md`); zero changes under
   `research/v11/` or `research/adapter_v10/`.
2. **SC2/SC3 equal-twin staging — PASS.** Both trees' `staged_manifest_.json`
   sha256 = `16f29cba28d63593c...` and are byte-identical. Full verification:
   83/83 files ok (0 bad, 0 missing) in exec-v11-1 AND repro-v11-1. 20/20 OI
   parquets in both trees match `oi_staging_manifest.json`. a7_prelaunch item-5
   anchors reproduce: 1000PEPE OI `3fdf681d861c284c...`, 1000PEPE bar shard
   `052b34d3e9e539c0...`.
3. **Identity — PASS.** All 9 frozen `arm_config_digest`s recomputed from the
   exec-tree frozen family builders (adapter_v10 imported first, per contract)
   equal `selection_freeze.json`; pairwise distinct.
4. **LOT recompute — PASS.** With my own arithmetic over artifact
   positions/daily ledgers: anchor PF 0.724508191586, net −0.791808705897,
   cost 0.040441002249, MDD 0.791808705897, expectancy −0.014939786904, hit
   18/53, folds 1/3 positive with F0/F2 PF<0.80, symbol share 0.27412 (ZEC),
   stress nets/PFs and drop-one-symbol −1.038154196085 all match the verdict
   file to the last digit. Control-positive falsification confirmed: control
   net **+0.710926701399** vs anchor **−0.791808705897**. My own gate
   evaluation fails the same 7 gates ⇒ `V11_FAMILY_REJECT` confirmed.
   Note (non-defect): position-level `cost_allocated_per_unit` sums to
   0.038520267072; the 0.001920735177 residual is exactly carried in the
   per-boundary cost ledger (`portfolio_payload`/`daily_returns`).
5. **Reproduction — PASS.** My own payload hash (artifact minus
   hashes/artifacts, frozen `<TREE_ROOT>` normalisation) is equal across
   exec/repro for **all 5 cells** of `LOT-RESMAX-7D-W` (minimum was 2 cells /
   1 arm); claimed `result_sha256`s match `reproduction_report_lot.json`.
6. **Ledger — PASS.** `verify_append_only == True` on
   `results/registry/experiments_v11_phase_e.jsonl`; exactly 3 rows, all
   CELL_RESULT for the three LOT arms; trial keys unique and recompute as
   sha256(canonical payload); `shard_lot.jsonl` keys == canonical keys. The
   defective quarantine holds exactly 2 zero-position CELL_RESULT rows
   (OILEV anchor/control) whose keys are absent from the canonical ledger and
   all shards. Observation: `shard_illiq.jsonl` has 2 keys not yet reconciled
   (ILLIQ in flight — wave 2).
7. **OILEV BLOCKED — PASS.** With my own loader + the frozen
   `OileverDelevPlugin` over exec-tree staging, I recomputed **52/52** stamps
   (minimum 8): status OK, `n_eligible_dv=9` everywhere, max|weight| = **0.5**
   on every stamp > frozen cap **0.30** (`DEFAULT_WEIGHT_CAP_MAX`), and the
   adapter's `normalise_target_book` raises `ContractViolation` on 52/52 —
   fail-closed before any fill. No rescue taken; 0 scored metrics.
8. **Incident honesty — PASS.** Quarantined digests match the preserved
   defective out-dir artifacts (2/2); every preserved OILEV matrix cell shows
   n_positions=0 / net 0.0 / scored=false; neighbour out-dir preserved with no
   published row; driver fix `quote_volume` present in `build_oilev` at HEAD
   (`run_v11_cell.py` line 190); LOT preflight records
   `family_accepts_drop_one_fold_cell=false` with the matrix-filter note.
9. **Budget/boundaries — PASS.** Computed scored cells so far: 3 (LOT) —
   within 9 eligible / 12 max; OILEV 0/3 slots and DEF 0/3 slots unused.
   Remote-tracking `origin/orca/v11-integration` == `c97283e0d1681c...`; it is
   the only branch containing `c97283e` — no push/main merge after it.
   Forbidden-reference scan of new tooling clean. 12h clock superseded by
   owner amendment `V11-AMEND-DEADLINE-RELIEF-20260903` (documented, stop
   rules retained).
10. **Denominator — PASS.** `denominator_split` on the canonical V11 ledger =
    {published: 3, observed_unpublished: 0}. The amendment documents logical
    denominators 119 + published_v11 / 120 + computed_v11 (+2 disclosed
    PIPELINE_ERROR computations) with the historical merge DEFERRED
    UNAVAILABLE_FAIL_CLOSED and a required exactly-once cross-check before
    any merge.

## PENDING for wave 2

- ILLIQ family gates (independent recompute) once the chain finishes.
- Reproduction payload verification for the remaining arms
  (LOT-RESSKEW-30D-W, LOT-RESMAX-7D-W-INV, ILLIQ arms).
- ILLIQ shard → canonical reconciliation and final budget/denominator view.

## Evidence files

- `a7_terminal_wave1.json` — itemized machine verdicts
- `scripts/a7_item3_digests.py`, `scripts/a7_item4_lot_recompute.py`,
  `scripts/a7_item5_repro_payload.py`, `scripts/a7_item6_ledger.py`,
  `scripts/a7_item7_oilev_cap.py` — audit method (rerunnable)
- `item3_digests_output.json`, `item4_raw_output.json`, `item6_raw_output.json`,
  `item7_raw_output.json` — raw audit outputs
