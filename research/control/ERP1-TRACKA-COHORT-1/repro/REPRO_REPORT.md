# REPRO REPORT — ERP1-TRACKA-COHORT-1 (tracka1-repro, reproduction twin)

**Verdict: ALL_MATCH** (zero substantive differences; every difference
enumerated and classified below).

Per P-4: this proves only that the scored pipeline is deterministic and the
published numbers are re-derivable from the frozen inputs at the scored SHA.
It does NOT prove the numbers are *true* — single-source panel, paper tier,
M1-bidask fill-quality ceiling all inherit unchanged.

## 1. Method

1. Fresh detached worktree at the dispatch SHA:
   `git -C /Users/hoangminhlong/my-quantitative worktree add --detach
   /Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1/repro_twin
   9e21ce6f` — measured HEAD after checkout:
   `9e21ce6fe5c8450a433a67e8ece7fbd9e0e9cb8c`. The scored work commit
   `df9dda49e934c99120ed209fca69afcc09bedd86` differs from `9e21ce6f` ONLY by
   the handoff bookkeeping file (`git diff --stat df9dda49 9e21ce6f`: 1 file,
   HANDOFF_tracka1_scored.json, +95) — code and published outputs identical.
2. Published baseline: committed outputs inside the repro worktree snapshot
   copied to `repro/pre_run_snapshot/` BEFORE the re-run, and verified
   byte-identical (`cmp`) to the integration worktree's published copies
   (all 8 output files + 12 series files: SAME).
3. Machine-local inputs: the twin worktree lacks the gitignored parquets.
   Copied (read-only source) from the integration worktree:
   `data_local/derived/bars1h_ANC_AUDUSD.parquet`
   sha256 `4e0ca174a21e155271a481727259daa0d3df888bb9f96eb7a34d8c6f06881364`,
   `data_local/derived/bars1h_ANC_USDCAD.parquet`
   sha256 `335a6e2aab25aebff17f9198f1b939448262186ed20e63f3041f8818d02f376b` —
   byte-identical to source (these are the exact files the scored lane ran
   on; `scored_lib.load_plane` reads only these two). No pipeline-read file
   was modified. GO-2 record read from the root checkout at its committed
   path, clean in git, sha256
   `eb8b4f047144a3f2d781ba83884500d36d0637d996815d163775ecca3e0cd34e`
   (matches the sha recorded in the published ledger rows).
4. Re-ran the committed entry points from
   `research/control/ERP1-TRACKA-COHORT-1/` with
   `/Users/hoangminhlong/my-quantitative/.venv/bin/python`, exact committed
   configs/seeds, freeze/GO1_freeze_artifact.json (+ erratum E1) untouched:
   - `scripts/scored_run.py dryrun`  → exit 0, all dryrun gates TRUE
     (leak_scan_clean, non_vacuous, ids_pairwise_distinct, replay
     ledger_unchanged, machinery identities all true on both pairs).
   - `scripts/scored_run.py scored`  → exit 0, ~5 s wall clock.
   Heavy lock not acquired: compute-only on local parquet, ran in seconds
   (per dispatch: skip if it runs in minutes). Locks inspect before run:
   FREE_PROVEN.
5. Test suite re-run: `python -m pytest tests/ -q` → **38 passed**.

## 2. Comparison (twin re-run vs published baseline)

Per-file results (`repro/comparison_result.json`, tool
`repro/compare_repro.py`):

| artifact | byte-identical | modulo wall-clock | wall-clock diffs | substantive diffs |
|---|---|---|---|---|
| scored_seam_law.json | YES | YES | 0 | 0 |
| scored_kill_laws.json | YES | YES | 0 | 0 |
| series/*.json (12 files) | YES | YES | 0 | 0 |
| scored_dev_cells.json | no | YES | 1 (created_utc) | 0 |
| scored_holdout_look.json | no | YES | 1 (created_utc) | 0 |
| scored_dsr.json | no | YES | 1 (created_utc) | 0 |
| scored_dryrun.json | no | no* | 1 (created_utc) | 3 paths* (see 3.2) |
| SCORED_REPORT.md | no | — | 1 line | 1 authored paragraph (see 3.3) |
| trial_ledger.jsonl | see 3.4 | — | 0 | 0 (1 provenance field/row, see 3.4) |

Point-by-point against the dispatch checklist:

- (a) Per-trade records: published artifacts persist per-trade content as
  `per_trade_pips_k_book` (order-preserving per-trade pip sequences, k=1.0/
  1.5/2.0) in the 12 series files — **byte-identical**; per-fold trade COUNTS,
  per-fold nets and the top-5-trade entry-ts record IDs inside
  `exclusion_zones` (dev cells) are identical within the byte-equal /
  modulo-wallclock-equal files. Any change of entry/exit ts, direction,
  price or cost would break the pip sequence, fold assignment or fold nets;
  all are pairwise identical.
- (b) Per-cell net/gross pips at k=1.0/1.5/2.0: identical (cells_equal,
  both pairs, all 6 arms incl. BASELINE-SET composite books).
- (c) PF, RT, per-fold nets, gate verdicts + margins: identical
  (`anchor_gates` equal: AUDUSD G1 PASS +323.3 / G2 FAIL PF 1.0334 /
  G3 FAIL 3-of-6 / G4 FAIL −652.35@k1.5 / G8 margin +0.0091; USDCAD G1 PASS
  +681.0 / G2 FAIL PF 1.0509 / G3 FAIL 3-of-6 / G4 FAIL −509.4 / G8 +0.0367;
  RT dev union 923 / 962).
- (d) Seam law: byte-identical file. S = +2884.1 (AUDUSD) / +4348.6 (USDCAD);
  all three limbs FIRES on both pairs; limb (iii) matched pairs 337/306,
  deltas +8.0451/+12.9562 vs c_rt 2.0/2.4; c_rt recomputation reproduces the
  frozen 2.0/2.4 exactly.
- (e) Kill laws: byte-identical file. KILL_PIT_SEAM fires both pairs;
  KILL_INVERSION fires both pairs (shadow-folds limb: AUDUSD F5, USDCAD
  F1+F6); KILL_CONTROL_REPRODUCED no (placebo −2207.3/−978.3);
  KILL_BETA_EXPLAINED no.
- (f) Ledger row content, 12 scored rows (+2 HOLDOUT_UNREAD rows):
  order-independent row-digest comparison after excluding the single
  provenance field of 3.4 → **all row content identical** (verdicts
  KILL_PIT_SEAM / HOLDOUT_UNREAD_CONSUMED_BY_NONE, net/gross/k-books, gates,
  exclusion zones, labels, freeze/census/GO-2 shas all equal). Append-only
  prefix preserved (41 committed lines untouched; 14 rows appended by twin).
- (g) DSR inputs: series files byte-identical. DSR outputs identical modulo
  created_utc: AUDUSD DSR 0.000798 (SR_hat 0.008399), USDCAD DSR 0.001631
  (SR_hat 0.013123), SR0 0.082127, N=12; PBO NOT_RUN_FAIL_CLOSED.
- Terminal verdicts reproduced: BOTH pairs **KILL_PIT_SEAM**;
  `scored_holdout_look.json` = HOLDOUT_UNREAD_CONSUMED_BY_NONE for both
  pairs — the holdout windows were again NOT read (by the twin either).

## 3. Complete difference inventory

### 3.1 Wall-clock (allowed) — 5 fields
`created_utc` in scored_dryrun.json, scored_dev_cells.json,
scored_holdout_look.json, scored_dsr.json; the `Generated:` line (line 3) of
SCORED_REPORT.md (published 2026-09-25T23:55:17+00:00 vs twin
2026-09-26T00:06:23+00:00). scored_seam_law.json, scored_kill_laws.json and
all 12 series files contain no wall-clock fields and are byte-identical.

### 3.2 Sequence-environment metadata (expected; not substantive to numbers)
`scored_dryrun.json`: `ledger_sha256_before`,
`replay_zero_denominator_delta.ledger_sha256_after`, and the copy under
`gates.replay_clean` (3 JSON paths, 2 distinct values). Published:
`5830065a…` = sha256 of the 27-line pre-scored ledger (the dry-run ran
BEFORE the scored append, per the sequence law). Twin: `83597880…` = sha256
of the 41-line ledger at twin time (scored rows already committed) —
verified by direct hash of `pre_run_snapshot/trial_ledger.jsonl` (41 lines)
and of its 27-line prefix (`5830065a…`, exact match to the published value,
independently confirming the original run sequence). `ledger_unchanged:
true` in BOTH runs — the replay law held in both.

### 3.3 SCORED_REPORT.md authored paragraph (documentation, not machine output)
The published report contains a hand-authored narrative paragraph ("The
decisive finding is the seam attribution …", published lines 117–118) that
the committed `write_report()` code does not emit (consistent with the
handoff's disclosed post-run report cleanup). Every machine number in the
paragraph was verified against the twin's regenerated artifacts and matches
(PF 1.0334/1.0509, G3 3/6, G4 −652.35/−509.4, R-ORIG +3207.4/+5029.6 PF
1.3804/1.4280 +2232.5/+3838.9 @1.5, S 2884.1/4348.6 vs 20.0/24.0, matched
deltas 8.05/12.96 on 337/306 pairs, costs ~1951.3/2380.8 RT vs
2274.6/3061.8 gross, placebo −2207.3/−978.3, KILL_INVERSION, holdout
unread) — EXCEPT one prose slip: the paragraph says USDCAD R-ORIG passed
"5/6 folds", while the machine artifacts — published AND twin, byte-equal —
record **6/6 positive folds** (G3 PASS either way; AUDUSD is 5/6). This is
a pre-existing inaccuracy of the authored prose in the published report,
NOT a reproduction difference (published and reproduced machine artifacts
are identical). Flagged for the A1 harvest; not repaired.

### 3.4 Ledger provenance field (expected; disclosed in the scored handoff)
All 14 rows appended by the twin differ from the published rows in exactly
one field: `sha_chain.scored_code["scripts/scored_lib.py"]` — published
`eabe8e84ee00c792eae824def2b2cecacf5cbd182c00aa0eda12231422d7a859` (the
file bytes at original-run time) vs twin
`1a5a9e0099efa3f997b500e73c5d5f87db1f261c390afbe808f2c5685354142c` (the
committed bytes). Finding: `eabe8e84…` corresponds to NO committed blob
(44a58af9 dryrun commit has `d8bf6777…`; df9dda49/9e21ce6f have
`1a5a9e00…`) — the scored run executed an uncommitted intermediate
scored_lib.py (the handoff's disclosed post-run float-coercion fix was
committed afterwards without a re-run). `scripts/scored_run.py` sha in the
rows matches committed bytes (`5628a60b…`) on both sides; freeze sha,
census data_manifest shas, selection digest and GO-2 record sha match on
all rows. The twin's byte-exact reproduction of every numeric artifact
empirically CONFIRMS the handoff claim that the post-run fix changed no
serialized number. Provenance gap recorded as a finding (ledger sha_chain
cites an uncommittable working state); not repairable in the twin.

**Substantive differences (numbers, verdicts, gates, margins, records): 0.**

## 4. Commands

```
cd <twin>/research/control/ERP1-TRACKA-COHORT-1
/Users/hoangminhlong/my-quantitative/.venv/bin/python scripts/scored_run.py dryrun   # exit 0
/Users/hoangminhlong/my-quantitative/.venv/bin/python scripts/scored_run.py scored   # exit 0
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/ -q            # 38 passed
/Users/hoangminhlong/my-quantitative/.venv/bin/python repro/compare_repro.py > repro/comparison_result.json
```

## 5. Incidents

None. Both committed commands exited 0 on first attempt; no file the
pipeline reads was modified; the integration worktree was not touched; no
holdout window was read; no registry/plan/FX-shadow writes.
