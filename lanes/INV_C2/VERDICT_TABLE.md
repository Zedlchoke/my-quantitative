# VERDICT_TABLE — Lane INV_C2, cycle NFL-WINPROB-NG-SCORED-V1

Written 2026-10-05. Verdicts: PASS / FAIL / NOT_RUN / SOUND / TAINTED / UNVERIFIABLE.
Missing evidence is NOT_RUN, never inferred PASS. This lane is diagnostic-only; it
implements nothing and changes no freeze, no ledger, no arm admission.

| # | check | verdict | evidence |
|---|---|---|---|
| 1 | Reproduce T_SELECT venue_label_permutation control ΔLL | PASS | −0.006873 [−0.009950, −0.003733], pooled 0.645624 — bit-match to SELECTION_CONTROLS.csv; rerun bit-identical (seed 20261005) |
| 2 | Reproduce parent C2_L075_D1O2_H025 ΔLL | PASS | −0.010027 [−0.014440, −0.005374], pooled 0.642470 — bit-match to SELECTION_CONFIGS.csv |
| 3 | Hypothesis (a) updates-only permutation retains signal | CONFIRMED | h never permuted (arms.py L343 keeps `+hterm`); h-only arm ΔLL −0.0041 CI<0; control deviations corr 0.72 / 74% magnitude vs parent; 68.5% of parent gain survived |
| 4 | Hypothesis (b) permuted-E double-counting | REJECTED | control deviations carry LESS signal than parent — opposite signature |
| 5 | Hypothesis (c) half-speed updates | CONFIRMED (partial) | in-role subsample keep=0.5 → −0.0084, keep=0.25 → −0.0065 brackets control −0.0069 |
| 6 | Hypothesis (d) ΔLL row-set/pairing mismatch | REJECTED | row alignment 5057==5057, same inner mask (1275 rows), paired per-row, bit-exact reproduction from raw games.csv |
| 7 | Hypothesis (e) sign/index bug swapping control/parent | REJECTED | independent reproduction matches both rows exactly; parent BEATS control (0.6425 < 0.6456) — no swap |
| 8 | Hypothesis (f) calibration-jitter toward 0.5 | REJECTED (NFL direction) | 0.5-ward jitter of B1* ΔLL +0.0157 (worse; slope 1.605→3.30). Control slope moved DOWN toward 1 (1.300) — gain is from more-extreme arguments. Cross-cycle: NBA (slope 0.7801 overconfident) twins winning IS the mirror-image (f) — direction-dependent baseline sensitivity, not one shared bug |
| 9 | Root cause identification | PASS | control-design + criterion defect: corruption structurally cannot touch the h-share of the gain and only halves/mixes the deviation channel; adjudicated "wins" vs B1* (slope 1.605) where ANY spread-adding arm beats B1* (pure logits ×1.5, zero mechanism: ΔLL −0.0054 CI<0; even full label swap: −0.0056 CI<0) |
| 10 | Control LOST to its parent (dispatch framing corrected) | PASS | control 0.645624 vs parent 0.642470 pooled — corruption did hurt the arm; `wins` fired on the vs-B1* comparison only (select.py L320 `"wins": bool(hi < 0.0)`) |
| 11 | Taint: faulty code shared with C1/C3/C4 twins? | NO | venue_perm branch only at arms.py L340 under `venue_perm_rng is not None`; sole call site select.py L234–235 (C2 venue control). C1 twin L172–198, C2 twin L201–227, C3 twin L239–254 (replay_elo — no permutation branch), C4 twin L257–276: all independent |
| 12 | Taint: shared eval_control/boot machinery faulty? | NO | bit-exact reproduction + row alignment; criterion weakness is conservative (false alarms only, never false clean) |
| 13 | C3 "shuffled control clean" verdict | **SOUND** | twin −0.000455 [−0.004890, +0.004169] nowhere near threshold; permuted z fully destroys the mechanism's only signal channel; clean is the expected null on parent C3_T050 (slope 1.079, in band) |
| 14 | C3 ADMIT stands | PASS | control evidence code-independent of the fault and correctly implemented; parent gates (point ΔLL −0.00415 < 0, slope 1.079 in band) untouched by this investigation |
| 15 | C2 stays out of slate (owner law) | PASS (a fortiori) | three independent kill grounds: control fired on the pre-registered rule; MECHANISMS §2-C2 "must destroy the gain" formally failed (31.5% destroyed); slope 1.2533 outside [0.85, 1.15] kills regardless of any control evidence. No revival proposed or permitted |
| 16 | Lane boundary compliance (read-only investigation; writes only lanes/INV_C2/** + handoff) | PASS | no git; no changes to any investigated file; probes import T_SELECT unmodified, outputs confined to lanes/INV_C2/probes/ |

Final verdict: **(i) FAULT_ISOLATED_TO_VENUE_CONTROL** — C3's control evidence and ADMIT
stand; remediation (control design + criterion calibration) is a PROPOSAL for successor
cycles only (see C2_MACHINERY_INVESTIGATION.md §7).
