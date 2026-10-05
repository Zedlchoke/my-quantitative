# AUDIT EVIDENCE — lane A7_PRELAUNCH · WNBA-PLAYERFEAT-SCORED-V1 (independent auditor)

Command + exit code + evidence record. All commands run by the auditor at HEAD
`12e05508de30de61da3825b10a6df8a87291f796` (branch `orca/wnba-playerfeat-scored-v1-integration`),
interpreter `/Users/hoangminhlong/my-quantitative/.venv/bin/python` only, git READ-ONLY.
Auditor scripts live in `lanes/A7_PRELAUNCH/tmp/` (own code; never imported/modified audited
modules except read-only in-process use of the frozen `harness` for the gate probes).

## A7-1 SHA chain (PASS)

```
$ git rev-parse HEAD
12e05508de30de61da3825b10a6df8a87291f796        == dispatch SHA  (exit 0)
$ git log --format='%H %P' -5 HEAD
12e05508… parent 5a1d0618e344844303d282923979cd949768368e   (S_SYNTH)
5a1d0618…  parent 34d8c2671f532b7eed7b6a0c6313126bf11fa3f5   (T_SELECT control event)
34d8c267…  parent 8130de5af6c05dcf8e67efdfd2f5bc6f575ca92d   (T_SELECT work)
8130de5a…  parent 03cc27f74de4e170067b0ac4390c8fcd48acf5c5   (bootstrap)
03cc27f7…  parent 4c17c787…                                   (base plans)
$ git merge-base --is-ancestor 03cc27f7 HEAD && git merge-base --is-ancestor 8130de5a HEAD
OK (exit 0; single-parent chain => linear)
$ git status --porcelain
?? lanes/DISPATCH/DISPATCH_A7_PRELAUNCH.md      # the dispatch packet, uncommitted by design
$ git branch -vv | grep wnba-playerfeat          # no upstream; ls-remote heads: 0 matches
```
All four dispatch SHAs present, order correct (T_SELECT = `34d8c267` + `5a1d0618`), HEAD on the
dispatched branch, tree clean, nothing pushed (0 matching heads on origin; 50 local commits
ahead of origin/main).

## A7-2 Own-code recompute (PASS)

Auditor script `tmp/a7_recompute.py` (fresh engine + fresh loaders, written from the frozen
engine-law text; no `arms`/`harness` import).

```
$ .venv/bin/python lanes/A7_PRELAUNCH/tmp/a7_recompute.py        EXIT=0
A7-RECOMPUTE PASS (26 checks, 0 failed)
```
Key lines (auditor's values vs frozen records):
- input integrity: feature table sha256 `ceaf10ba33e705b9…` == manifest
  (winprob-playerfeat-prep-v1 `lanes/B_WNBA_FEAT/FEATURE_TABLE_MANIFEST.md`) == harness
  constant; 826,415 B; 11,976 file rows; ≤2018 slice 7,990 rows = 2×3,995 games; universe
  identity 0 missing / 0 extra; warm-up 1,022 rows seasons 1997–2001; lineage unambiguous.
- B0: `0.6037546933667084` == frozen (exact).
- Grid: 27/27 ledger `mean_ll_pooled` values reproduced; max |ΔLL| = 2.220e-16
  (at K=8/HCA=100/γ=0.65). Grid run_ids/configs == dispatch constants.
- Winner K=32/HCA=50/γ=0.65: pooled validation LL auditor `0.623497720316443` vs frozen
  `0.6234977203164429` → |Δ| ≈ 1e-15, tolerance 1e-9 met (1,774 validation games).
- Kill test vs B0: point `-0.054386188557277` == frozen `-0.054386188557277046`; auditor
  bootstrap CI `[-0.070150, -0.038275]` == frozen, entirely negative → direction PASS.
- Named spot points: K=16/HCA=100/γ=0.75 |Δ|=0.000e+00; K=8/HCA=0/γ=0.85 |Δ|=1.110e-16;
  K=32/HCA=0/γ=0.65 |Δ|=0.000e+00.
- Train-window LL context `0.636540937786889` == frozen `0.6365409377868896`.
- Persisted `b1_frozen_p_stream_train.parquet`: game set exactly == auditor's ≤2018 parent
  stream (3,995 rows; no warm-up row, no OOS row); 1,089/3,995 float64-bit-identical, max
  |Δp| = 1.665e-15 (last-ulp rounding from implementation order — independent-impl agreement).
- Pinned moments recomputed exact: wf_b mean 0.117793972662138 / sd 0.010038602475928 (n=2,292);
  wf_c mean 0.107699343289122 / sd 0.103547956124905 (n=2,292); seasons 2013–2018.
Full JSON of the 26 checks: `lanes/A7_PRELAUNCH/tmp/a7_recompute_out.json`.

## A7-3 Designed null (PASS)

Real-data part (inside `a7_recompute.py`, auditor's engine, auditor's x_fn from recomputed
moments):
```
PASS A3_real_phi0_byte_identity  5017 corpus games (warm-up 1022 + train 3995)
PASS A3_real_c1_byte_identity
```
Own synthetic stream `tmp/a7_null_synth.py` (deliberately different generator: 3 seasons ×
6 teams, same-tip triple batches, 2 neutral rows, own seed):
```
$ .venv/bin/python lanes/A7_PRELAUNCH/tmp/a7_null_synth.py       EXIT=0
A3_SYNTH n=90 phi0_identical=True c1_identical=True both_identical=True
A3_SYNTH negative_control_phi25_differs=True
```
Corroborates ledger `DESIGNED_NULL_REAL_DATA designed_null_ok=true` and frozen selftest
`designed_null_byte_identity_3_synthetic_streams`. Negative control proves the probe can fail.

## A7-4 Cap / OOS lock (PASS)

```
$ cd lanes/T_SELECT && .venv/bin/python harness.py --selftest   EXIT=0
SELFTEST 14/14 PASS   (incl. doctored_2019_row_aborts,
                       evaluate_oos_refuses_real_without_go_token,
                       warmup_rows_never_scored_and_oos_out_of_scope,
                       feature_table_has_no_outcome_columns,
                       lineage_20key_canary_raw_abbrev_fails)
$ .venv/bin/python lanes/A7_PRELAUNCH/tmp/a7_gate_probe.py      EXIT=0
PASS A4_doctored_2019_aborts  HARD CAP VIOLATION [A7_doctored_2019_probe]:
                              season 2019 > SEASON_MAX_REAL=2018 …
PASS A4_cap_control_2018_passes
PASS A4_evaluate_oos_real_no_token_refused  Abort: OOS-GATE-REFUSED …
PASS A4_refusal_is_preread_zero_real_bytes  real-data fs events at refusal time: 0
PASS A4_fabricated_lowercase_token_refused  OOS-GATE-REFUSED …
PASS A4_path_as_token_refused               OOS-GATE-REFUSED …
PASS A4_control_synthetic_allowed_pregate
A7-GATE-PROBE PASS (0 fails)
```
Code-read (harness.py): `SEASON_MAX_REAL = 2018` (line 32); `enforce_season_cap` raises
`CapViolation` on any season > 2018; `load_feature_rows` filters `season <= SEASON_MAX_REAL`
at read then asserts; `main()` calls `enforce_oos_gate` BEFORE any loader for evaluate-oos;
with a correct phrase the gate check opens but execution still refuses ("real-data OOS
execution lives POST-GO", SystemExit) — this exact-phrase path was verified by code-read of
the 4-line branch only; the auditor did NOT type the registered phrase (boundary discipline;
S_SYNTH probe D4 already demonstrated it on the same frozen bytes).

## A7-5 Ledger completeness (PASS)

```
$ wc -l ~/.my-quantitative-data/wnba-playerfeat-scored-v1/selection/SELECTION_LEDGER.jsonl
49
composition: grid_fit 27 · arm_fit 11 (WF-A 1, WF-B 5, WF-C 5) · selection 3 · gentry 3 ·
kill_test 1 · designed_null 1 · diagnostic 1 · twin 1 · report_row 1
=> scored fits 38 (27+1+5+5) + 11 bookkeeping = 49; summary n_fits == ledger fit rows
all rows: mode=select, season_cap=2018, seed=20261005, cycle_id=WNBA-PLAYERFEAT-SCORED-V1
grid configs == dispatch constants K{8,16,32}×HCA{0,50,100}×γ{0.65,0.75,0.85} (27 run_ids)
$ shasum -a 256 SELECTION_LEDGER.jsonl
603aa4126e22af8f7c9b8e492638ded60991db307dc3167ad660930c3fde58df
  == handoff_T_SELECT tests[2] deterministic-rerun sha (byte-for-byte rerun claim corroborated)
all 7 handoff_T_SELECT output shas match bytes on disk (harness b9446f76…, arms 82263eab…,
SELECTION_REPORT 283165ff…, VERDICT_TABLE 221dec24…, ledger 603aa412…, summary bf62d37a…,
parquet 6a5404be…)
```

## A7-6 S_SYNTH dry-run evidence (PASS)

```
$ diff -r ~/.my-quantitative-data/wnba-playerfeat-scored-v1/sandbox/rehearsal_run1 \
          ~/.my-quantitative-data/wnba-playerfeat-scored-v1/sandbox/rehearsal_run2
(exit 0, byte-identical — determinism double-run reproduced from disk)
$ shasum -a 256 …/rehearsal_run1/rehearsal.json …/rehearsal_run2/rehearsal.json …/lock_probes/probe_results.json
51a513b78f7b2905720ce7624634da52d4485386f640c741dbf85a4e04b8f73a  (both, == recorded)
d70f2b91d272c1cf2804a4e65bc0adbeb9604f009d37a36ed12f17a9b395bd08  (== recorded)
rehearsal.json content: hand_fixture {tol 1e-12, 11 checks all ok:true,
  tip_batch_no_leak_byte_identical: true}; laws all true (designed-null byte identity,
  identical_game_set, exact_arm_ids_pairwise_distinct, nonvacuous, folds = seasons
  {2029,2030} only); predictions SYNTH_-prefixed (112 rows seasons 2029–2030)
Auditor hand-re-derivation of fixture game 1 (fresh 1500 vs 1500, HCA=50):
  p = 1/(1+10^(-50/400)) = 0.5714631174084; LL = 0.5595553342981; Brier = 0.1836438597413
  — all equal the fixture to 13 decimals.
dryrun.py code-read: frozen-bytes gate asserts T_SELECT harness/arms shas (b9446f76…,
82263eab…) and refuses on drift. lock_probe.py code-read: sys.addaudithook over all real
roots + CLI refusals + fabricated-token probes; probe_results.json matches.
```

## A7-7 Honesty (PASS)

- WF-A `MACHINERY_SUSPECT`: ledger `GENTRY_WF-A` → machinery_suspect=true, twin_dll
  −0.0009684503 (twin beats OWN parent), real ΔLL +0.0004200675 CI [−0.002750, +0.003621],
  parent real-data fold slope 0.9046813628265814 — INSIDE [0.85,1.15], so the
  miscalibrated-parent exemption correctly does NOT apply; verdict MACHINERY_SUSPECT, arm
  UN-SCORED, machinery audit owed — recorded in VERDICT_TABLE.md, SELECTION_REPORT.md §7,
  and both lane handoffs.
- WF-B/WF-C RELEASE justified: auditor recomputed all 10 per-φ pooled fold LLs; φ=0 is
  strictly minimal for both arms (WF-B: 0.641544/0.634829/0.632928/0.635825/0.643415;
  WF-C: 0.648506/0.637160/0.632928/0.636072/0.646431); φ=0 ≡ parent byte-identical
  (auditor-verified), ΔLL +0.000000 — "no train-internal signal at any pre-registered
  strength" is the honest reading, stated verbatim in the lane's own notes.
- Warm-up 1997–2001 = stream-only: code-read (warm-up rows only enter `full_games` for the
  rating stream; LL/scored sets are the 2002–2018 universe); frozen persisted stream contains
  exactly the 3,995 ≤2018 games (auditor set-equality); selftest
  `warmup_rows_never_scored_and_oos_out_of_scope` PASS; warm-up-vs-cold-start is a labeled
  diagnostic (0.636541 vs 0.636773), never an arm.

## A7-8 Boundaries (PASS)

- 0/9 scored: control state `research/control/WNBA-PLAYERFEAT-SCORED-V1/state.json`
  `budget_scored {used: 0, max: 9}`, `s1: SEALED_UNTOUCHED`; registry entry `budget
  {used: 0, max: 9}`; event log "0/9 scored; GO not typed".
- No real OOS values anywhere: ledger regex sweep — the only `2019` hit is a substring of
  `0.5862019472307427`, the only `202[0-6]` hits are the seed `20261005` (inspected, not
  season refs); persisted parquet == exactly ≤2018 games; S_SYNTH sandbox SYNTH_-only;
  lane reports reference 2019/2020–2026 only as cap law / frozen window.
- GO registered-not-typed: registry `go_phrase_state: REGISTERED_NOT_CONSUMED`; control state
  "GO phrase registered NOT typed (see plan; owner-only at own gate after A7)". This audit
  never typed the phrase.
- No push: branch has no upstream; `git ls-remote --heads origin | grep -c
  wnba-playerfeat-scored-v1` → 0; 50 commits ahead of origin/main, all local; no merge.

## A7-9 Freeze completeness for the post-GO read (PASS)

- Fielded arms: B0 constant p_home=0.603755 (frozen train rate; packet §1 law: OOS B0 refit
  per fold) + B1-WNBA fresh own-Elo K=32/HCA=50/γ=0.65 (warm-up 1997–2001) — both frozen in
  VERDICT_TABLE.md and rehearsed end-to-end by S_SYNTH as exactly this 2-arm path.
- Released slots: WF-B, WF-C (RELEASE at φ=0). Un-scored: WF-A (MACHINERY_SUSPECT; machinery
  audit owed before any continuity re-proposal).
- OOS window frozen: [2020..2026] (plan; completed seasons only; 2026 in-progress excluded;
  placeholder TBD rows never games).
- Metrics/falsifiers frozen: LL primary; Brier/reliability/slope band [0.85,1.15]; paired
  tip-date-cluster bootstrap 10,000 resamples seed 20261005; B1 falsifier (packet §3): REJECT
  vs B0 iff pooled 95% paired date-cluster-bootstrap CI of ΔLL includes 0 OR ≥ half of season
  folds non-negative; effects < ~0.003 ΔLL are INCONCLUSIVE (stated, not stretched).
- Neutral law: neutral-site rows → HCA=0 with separate report (2 train-window rows 400864492,
  400910457 handled; stats-side absence disclosed).
- Single-batch OOS law: one computation per arm on the frozen OOS seasons (plan metrics line;
  packet §7 denominator).
- Standardization/moments: pinned in outputs (n=2,292 each) but verified NOT applicable to the
  post-GO read — no φ was admitted, so nothing standardized enters the fielded arms; the
  moments exist only as release-audit evidence.

## Auditor artifacts (write scope respected)

- `lanes/A7_PRELAUNCH/A7_PRELAUNCH_VERDICT.md`, `AUDIT_EVIDENCE.md`, `OWNER_GATE_BRIEF.md`
- `lanes/A7_PRELAUNCH/tmp/{a7_recompute.py, a7_recompute_out.json, a7_null_synth.py,
  a7_gate_probe.py}`
- `lanes/DISPATCH/handoff_A7_PRELAUNCH.json`
- Nothing else written; no audited byte modified; `harness.py --selftest` and the gate probe
  were run with `PYTHONDONTWRITEBYTECODE=1`.
