# VERDICT TABLE — lane S_SYNTH · WNBA-PLAYERFEAT-SCORED-V1 (synthetic dry-run)

| slot | check | verdict | basis |
|---|---|---|---|
| frozen tree | T_SELECT --selftest re-run | PASS | 14/14 PASS, exit 0; harness/arms shas unchanged (b9446f76…, 82263eab…) |
| frozen tree | frozen-bytes gate in rehearsal driver | PASS | dryrun.py asserts T_SELECT sha256s and refuses on drift |
| rehearsal | synthetic corpus (2+ scored seasons, SYNTH_ ids, 2027+, corpus format) | PASS | warm-up 2027–28 (56, stream-only) + scored 2029–30 (112); schedule CSVs + feature parquet (2 rows/game, neutral-reason cols); all ids SYNTH_-prefixed, pairwise distinct |
| rehearsal | B0 const 0.603755 arm | PASS | pooled LL 0.696354, Brier 0.251501; slope = honest nan (constant predictor) |
| rehearsal | B1-WNBA K=32/HCA=50/γ=0.65 arm | PASS | pooled LL 0.661815, Brier 0.233977; slope 1.0974 (band [0.85,1.15]) |
| rehearsal | identical-game-set law | PASS | arm game-id sequences equal element-wise (full stream + scored folds); rows equal on (tip, season, outcome, neutral) |
| rehearsal | exact-arm ids pairwise distinct | PASS | 112/112 unique per arm |
| rehearsal | non-vacuous | PASS | 112 scored rows ≥ 1 |
| rehearsal | designed-null byte identity on synthetic | PASS | φ=0 (frozen make_x_fn + synthetic moments) and c≡1 both == frozen B1 p_home stream, float64-hex identical (168 rows) |
| rehearsal | hand-computed fixture cross-check | PASS | 3-game fixture vs independent pure-math derivation: 14/14 values agree to 1e-12 (p_home, LL, Brier, arms' means, paired ΔLL); tip-batch no-leak byte-identical |
| rehearsal | tip-date-cluster bootstrap smoke | PASS | ΔLL −0.034538 [−0.082936, +0.011913], 10,000 resamples, seed 20261005, 28 date clusters, fixed-seed rerun identical — machinery smoke only |
| rehearsal | per-fold LL/Brier/reliability/slope | PASS | all folds computed; Brier decomposition identity exact on every fold |
| OOS lock | real data + no GO token → refusal pre-read | PASS | OOS-GATE-REFUSED with audit hook observing 0 reads of any real root (feature parquet, roster_audit (53 entries present), ESPN/stats schedules, selection outputs) |
| OOS lock | CLI default source=real | PASS | exit 1, OOS-GATE-REFUSED on stderr |
| OOS lock | CLI explicit --source real | PASS | exit 1, OOS-GATE-REFUSED on stderr |
| OOS lock | fabricated token file | PASS | path-as-token → refused; --go-token-file → argparse reject (no file-based token input exists); wrong-case phrase → refused |
| OOS lock | structural backstop | PASS | even the exact registered phrase opens only the gate check; frozen tree refuses: real-data OOS execution lives POST-GO |
| OOS lock | control: --source synthetic | PASS | allowed pre-gate (exit 0) |
| determinism | full rehearsal double-run | PASS | diff -r byte-identical; 10/10 file shas equal (rehearsal.json 51a513b7…) |

Verdict vocabulary: PASS = proven on synthetic streams or refusal path in this
lane; no real OOS season was read; no real game was scored.

**LANE VERDICT: DRYRUN_PASS — the frozen 2-arm evaluation runs end-to-end on
SYNTHETIC OOS-like streams with all identity laws holding and the OOS lock
refusing real data pre-read, pre-GO, and against fabricated tokens.**
