# A7 PRELAUNCH AUDIT — ILLIQ-REG-V1

- Verdict: **AUTHORIZED** (0 blocking, 6 non-blocking findings)
- Audit UTC: 2026-09-24T05:09:04Z · Auditor: A7 independent (fresh; no role in
  bootstrap or implementation of this cycle)
- Head audited: `eb86951eb468e6644a76dd9b9412e68f51b66d0f`
  (`orca/illiq-reg-v1-integration`, worktree clean)
- JSON authority: `a7_prelaunch_illiq_reg_v1.json` (schema `chr3f_a7_prelaunch@1`)
  in this directory. This MD is the human-readable mirror.

## What was recomputed from bytes (not trusted)

1. **Plan vs frozen spec.** Plan §3/§6 constants == PREREG yaml ==
   `gate_module.py`: S90 ON ≤ 0.021317 / OFF ≥ 0.057702; VOL floor 0.328930
   with OFF 0.296037 = ×0.90; GATED = V1 AND V2; hysteresis carry, both start
   ON; Monday 00Z PIT stamps; falsification bars net ≥ −0.2947 AND MDD ≤ 0.4372
   (inclusive, test-pinned). Budget: phase-1 cap 4 == registry
   `ILLIQ-REG-V1 {used 0, max 4}`; GO phrase matches §12 verbatim,
   `REGISTERED_NOT_CONSUMED`. Threshold provenance verified in the dossier
   single-shot output (full precision 0.02131720710… / 0.05770158… /
   0.32893024…, n=242 pre-window Mondays).
2. **Ancestry disclosure accurate.** Plan §2 chain corroborated end-to-end:
   V11 `FAMILY_REJECT` share 0.7055 (`recovered/v11_root/baseline_wave2.json`)
   → CHR3F outcome-exposed A3/A4/A4b/A5 (`amendment_a4_illiq_outcome_exposed.md`)
   → DIAG −0.589312 no-funding (B2) / −0.5631 funded (A5-funded re-disclosure)
   observed BEFORE gate design → OUTCOME_EXPOSED_ANCESTRY, confirmation weight
   0 on all history. Single-shot gated replay (−0.403022 / MDD 0.443499 / 6 OFF)
   matches the plan's disclosure including the honest expected-FAIL reading.
3. **Gate-series determinism proven by my own rerun.** I reran
   `full_build_locked.py` under the machine-wide heavy lock (FREE_PROVEN before
   acquire): rc 0, `gate_series.json` **byte-identical**
   (`sha256 e09187f925e761cfabe94e0766ca2104b3b45f5def76fadc061cdbc09c51702d`,
   `cmp` silent; `full_build.log` also unchanged; worktree still clean).
   Digests recomputed: gate_module `bd0b00da…`, wiring `f2dc5bf9…`. M0 suite
   independently rerun: 35/35 PASS. Cross-check vs dossier: s90 max abs diff
   0.0 (bit-identical, 52/52 S0R stamps).
4. **Dry-run validity.** `dryrun_report.json`: non_vacuous true, no_pnl_fields
   true, 43 ON / 9 OFF over 52 S0R stamps == gate_series recomputed by me.
   I re-walked the hysteresis machines over **all 52 stamps** with re-typed
   constants (not calling the module): **0 mismatches**. Spot stamps verified:
   2024-08-26 ON (carry), 2025-06-16 ON (rvol 0.343019 ≥ floor),
   2025-06-23 OFF (rvol 0.286173 < 0.296037); carry verified at 2025-06-30
   (rvol 0.311185 between thresholds → stays OFF). Report digests match bytes.
5. **Cell-run conformance.** Plan §7–§9/§11/§14 + specified runner
   `illiq_cell_runner.py`: per-fold funding scans hardwired (S0R/FWD →
   `scan_2026_a`; B2 fail-closed zero-coverage check; live 20/20 test with
   26 208 rows), bars −125d/+3d, GATE_OFF → STATUS_SKIP reason GATE_OFF (flat
   week, no new fill logic), 4-label invariant mechanically enforced,
   namespace `research/control/illiq_reg_v1/` only, heavy lock per sweep,
   stresses ×1.5 / ×2.0 inside cells (+ engine-native stress where exposed).
6. **Boundaries.** S1 SEALED_UNTOUCHED; CHR3F worktree git-clean (read-only
   respected; `dont_write_bytecode` before CHR3F imports); no shadow/gateway
   contact (lock history only gate-series-build roles); no credentials in the
   namespace; **no scored cells** (budget 0/4, GO unconsumed, no
   `illiq_scored_status.json`, dry-run scored=False/no-PnL).
7. **Terminals.** §13 declares `FALSIFIED` a valid, dossier-expected terminal;
   no survivor promised anywhere; phase 2 needs an owner amendment; FWD is not
   scored this cycle.

## Non-blocking findings

- **NB1 — S90 prose vs frozen semantics.** Plan §3 prose ("mean of CONC28 over
  the trailing 90 days") differs from the threshold-generating definition
  CONC(28) − CONC(90) over daily DV-shares (dossier code + module). The module
  implements and pins the generating semantics (binding docstring + M0 test +
  bit-identical cross-check); applying the prose reading would have invalidated
  the p70/p90 calibration. Plan prose is the imprecise surface.
- **NB2 — Label list.** The dispatch's label premise
  (…+ EQUIVALENCE_DATA_RESTAGE_UNPROVEN + UNIVERSE_LISTED_AT_WINDOW_START) is
  not the plan §11 invariant; the plan mandates WINDOW_FOLD +
  OUTCOME_EXPOSED_ANCESTRY + REPLICATION_NOT_PROSPECTIVE/scored=False +
  FUNDING_WIRING (enforced by `wiring.validate_labels` + tests). The dispatch
  itself defers to the plan. Substance of the universe law is carried in §4
  (listed-at-start; S0R no divergence); the restage law in §9. Future rows must
  carry the §11 four labels exactly.
- **NB3 — Random-gate controls not serialized.** Plan §10.3 says the build
  writes them with digests; implementation generates them deterministically at
  cell time (seed = sha256(cycle id)[:8], structure/determinism unit-tested).
  Disclosed in the handoff; PREREG requires only declared reproducibility.
- **NB4 — rvol30 PIT correction vs dossier replay.** Frozen module reads
  completed closes strictly before the stamp; the dossier's descriptive replay
  read ≤ stamp (future data at a 00:00Z stamp). 3/52 V2 state deltas; GATE_OFF
  run 9 stamps (2025-06-23…) vs single-shot's 6 (2025-07-14…). Disclosed in
  the artifact; direction conservative (more flat weeks); no-lookahead test
  pins the frozen reading.
- **NB5 — Frozen constants are roundings** (6-dp thresholds, 4-dp bars) of the
  dossier's full-precision quantiles / exact 50%/30% derivations; identical on
  every surface; effect < 1e-4; the rounded values are the preregistered law.
- **NB6 — Registry head lag.** Registry records the registration-time head
  `482dc81b`; worktree has advanced to `eb86951e` (M0, implementation,
  handoff). Expected mid-cycle (registry written via researchctl at gates).

## Gate to the next step

STOP per plan §10.6/§12: the owner must type the exact fresh phrase
`GO ILLIQ REG V1 SCORED EXECUTION` at its own gate before any phase-1 cell.
This audit consumes nothing and authorizes nothing beyond proceeding to that
gate. If phase 1 fails its bar, `FALSIFIED` is a valid terminal — expected per
the dossier's own honest reading.
