# A7 TERMINAL AUDIT — STOCKS-FREE-V10

**Verdict: `STOCKS_FREE_V10_REJECT_ALL_CONFIRMED`** (schema `stocks_free_v10_run/a7_terminal@1`).
Fresh-context, independent of the A1 thread; every load-bearing number recomputed from bytes in this session.

## What was recomputed (all PASS)

1. **CHAIN** — `git merge-base` proves 3a61638 (V9 terminal) is the base; panel re-hashes to `67591464...af1447` exactly; timing layer = `b1477ea3...`, 5,453,478 rows; revision layer = `7110cbf0...`, 1,667,422 rows — both match `p0_v10_observable_manifest.json` pins.
2. **REPRODUCTION** — twin at 5b40d48: `family_verdicts.json` byte-equal (`c5fe68b8...`); `execution_ledger.json` differs in exactly ONE leaf (`code_freeze_sha`); publication record delta is the same provenance leaf via a compliant append. INC-V10-1 ruled honestly disclosed and outcome-neutral, not disqualifying (5b40d48 adds only the driver + run artifacts; twin at that commit reproduces the recorded outcomes exactly).
3. **VERDICTS** — all gate verdicts/margins re-evaluated against the inherited frozen threshold table (V9 p3 carry): 0 mismatches. A4-H1: expectancy +0.0197 passes but PF 1.0811 < 1.10, ETF-share 0.8333, SPY-excess 0/3, alpha −0.0123, stress −0.0240, drop-one −7.07e-05 → REJECT. A5-H1: expectancy −0.2047, PF 0.3144, 0/3 folds, stress −0.2299 → REJECT. Neither control reproduces (A4 opposite-sign −0.0278; A5 −0.0205 at 0.10x) → both REJECTs are mechanical, no falsification-shadow mislabeling.
4. **TWO-KEY** — r2 AUTHORIZED artifact (audited head afad4b1) committed at 6f72357, an ancestor of the scored commit 5b40d48, with state HARD_STOP_TWO_KEY_LAUNCH in between; exact frozen phrase enforced in code and matched against the RULES/PLAN registry; consumption record byte-identical since scoring.
5. **DENOMINATORS** — 14 = 6 trials + 6 stress + 2 drop-one (reruns not trials); published 6; v10 6/6; stocks 36/36; program 203/206 as-of-intake per P-9; survivors 0. Ledger, publication record, state and terminal report all agree.
6. **BOUNDARIES** — S1 sealed; no upstream/no push; all 8 commits are named-path (no `git add -A`); zero key material in committed bytes; `.staging_sec_v10/` gitignored; workers 0.
7. **POST-RUN** — state `CYCLE_CLOSED_PENDING_TERMINAL_A7` with the verdict; `pytest tests/stocks_free_v10/ -q` → **22 passed**.
8. **LABEL** — event log covers every scored artifact; with zero survivors, REJECT_ALL is the strongest valid plan outcome; BLOCKED_*/INCOMPLETE/SURVIVORS are factually excluded.

## Findings

- **F-1 MEDIUM (resolved-disclosed)** — INC-V10-1 uncommitted-driver provenance (see item 2).
- **F-2 MEDIUM (open, verdict-neutral)** — declared UTC timestamps inside artifacts run 1.5–2.3h ahead of the git/machine clock; order is preserved and commit order is the authoritative chronology.
- **F-3/F-4/F-5 LOW** — empty family-level margin map (per-gate margins present and verified); terminal wording on the publication-record diff is content-level; twin scratch artifacts live uncommitted in the repro worktree (V9 convention).

**Zero unresolved HIGH/CRITICAL → draft label CONFIRMED.** No survivor; S1 stays sealed; nothing to promote. This audit commits nothing and repairs nothing.
