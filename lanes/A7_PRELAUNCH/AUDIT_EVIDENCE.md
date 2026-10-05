# AUDIT_EVIDENCE — A7_PRELAUNCH, NFL-WINPROB-NG-SCORED-V1

Auditor: independent A7 lane · Date: 2026-10-05 (UTC) · HEAD audited `8cf29fe60809dd62c7d573292853d62b01cae0d4`
All commands run with `/Users/hoangminhlong/my-quantitative/.venv/bin/python` (or `/usr/bin/python3`,
`/usr/bin/git`, `shasum`, `grep`, `find`, `cmp` — read-only). Probe scripts + fixtures live in
`lanes/A7_PRELAUNCH/tmp/` (auditor-owned). No audited artifact modified.

---

## A7-1 SHA chain

Commands and outputs:

```
$ /usr/bin/git -C <WT> cat-file -t <sha> && git log -1 --format='%H %P %s' <sha>
TYPE=commit | f55dab66aa77…  4c2a8359…  Plans: WINPROB-PLAYERFEAT-PREP-V1 … + NFL-WINPROB-NG-SCORED-V1 (Option B successor, stop-before-GO)
TYPE=commit | 832f6956b9af…  f55dab66…  NFL-WINPROB-NG-SCORED-V1 bootstrap: lanes skeleton + control state (base f55dab66, budget 0/9, S1 sealed, GO registered NOT typed)
TYPE=commit | f6ff494556a8…  832f6956…  Lane A_DATA: pbp 2000-2017 18/18 pinned …
TYPE=commit | 69798a8389f9…  059005aa…  Control: wave2 selection event
TYPE=commit | 7ec4c539394e…  69798a83…  Lane F_FREEZE: freeze packet v1 — 3 fielded arms … GO not typed
TYPE=commit | e08e4c423f64…  7ec4c539…  Control: CODE_FREEZE_SHA addendum (7ec4c539…) + freeze event
TYPE=commit | 8cf29fe60809…  36288f1b…  Control: wave4 dry-run event
```

- `git merge-base --is-ancestor <c> HEAD` → YES for all 7 named commits (exit 0 each).
- `git log --merges --oneline f55dab66..HEAD | wc -l` → `0` (cycle segment merge-free; the only
  merges in history predate the cycle base).
- `git rev-parse HEAD` → `8cf29fe60809dd62c7d573292853d62b01cae0d4` (== dispatch SHA);
  `git branch --show-current` → `orca/nfl-winprob-ng-scored-v1-integration`;
  `git rev-parse --abbrev-ref @{upstream}` → `fatal: no upstream configured` (never pushed).
- `git status --porcelain=v1 -uall` at audit start → only `?? lanes/DISPATCH/DISPATCH_A7_PRELAUNCH.md`
  (untracked dispatch packet, by design). At audit end additionally only `?? lanes/A7_PRELAUNCH/**`
  (auditor-owned outputs). No tracked file modified.

Verdict A7-1: PASS.

## A7-2 Designed-null re-run (own synthetic stream)

Script: `lanes/A7_PRELAUNCH/tmp/audit_probe_a7_2_3.py` — first statement asserts
`sha256(arms.py) == 19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8` (freeze §9 pin),
then imports arms.py unmodified. My stream: fixture CSV, 38 loaded rows, lineages AAA–FFF,
seasons 2001–2004, one same-kickoff batch, one tie, one Neutral game, odds columns present.

```
$ /Users/hoangminhlong/my-quantitative/.venv/bin/python …/tmp/audit_probe_a7_2_3.py ; echo EXIT=$?
[sha] arms.py == freeze pin: 19dddd3f…
[stream] rows=38 seasons=[2001, 2002, 2003, 2004] ties=2 neutral=1 quarantined=['home_moneyline','over_odds','spread_line'] dropped_over_ceiling=0
[equiv] C1_B000: max|dp|=0.0 tobytes_equal=True
[equiv] C2_NULL: max|dp|=0.0 tobytes_equal=True
[equiv] C3_T000: max|dp|=0.0 tobytes_equal=True
[equiv] C4_D000: max|dp|=0.0 tobytes_equal=True
[power] C1 beta=25 max|dp| vs B1* = 0.0008965282836723709 (nonzero expected)
AUDIT_PROBE_A7_2_3: ALL PASS
EXIT=0
```

The four null p-streams were computed by the auditor's own code from the replay records (C1/C4
arithmetic; own C2 deviation loop with λ=0∧h=0; C3 θ=0 via frozen `replay_elo` fed a deliberately
non-zero z-table so the reversion code path runs). Max |Δp| exactly 0.0 and byte-equality vs B1*.

Verdict A7-2: PASS. Machine-readable evidence: `tmp/a7_2_3_evidence.json`.

## A7-3 No-spent-window

Code reading (arms.py, lines verified in the audited file):
- L26–27: `SEASON_MAX_GAMES = 2018`, `SEASON_MAX_PBP = 2017` (grep-auditable constants).
- L137: hard filter `df = df[(df["season"] >= SEASON_MIN_GAMES) & (df["season"] <= SEASON_MAX_GAMES)].copy()`.
- L140–141: backstop asserts `… "season > SEASON_MAX_GAMES leaked"` / `"season < SEASON_MIN_GAMES leaked"`.
- L115–128: `QUARANTINED_COLUMNS` (9 odds/probability columns) + `QUARANTINE_PATTERNS`
  ("odds","moneyline","spread") dropped at load with names recorded.
- L377–382 (`build_z_table`): loop `range(SEASON_MIN_GAMES, SEASON_MAX_PBP + 1)` (≤2017 only) +
  assert `"pbp season > SEASON_MAX_PBP leaked"`.

Runtime probes (same script, exit 0):
```
[a7-3 games] {"doctored_2019_row_injected": 1, "rows_loaded": 38, "max_season_after_load": 2004,
  "season_gt_2018_rows_in_loaded_set": 0, "n_dropped_over_ceiling": 1,
  "quarantined_columns": ["home_moneyline","over_odds","spread_line"],
  "odds_columns_in_loaded_df": []}
[a7-3 backstop] present=True fires=True msg=season > SEASON_MAX_GAMES leaked
[a7-3 pbp] {"parquet_years_on_disk": [2000..2019], "years_actually_read": [2000..2017],
  "canary_years_read_gt_2017": [], "z_table_entries": 0,
  "internal_pbp_assert_in_source": true}
```
- Doctored 2019 row: dropped by the filter (counted), zero rows > 2018 in the loaded set.
- Backstop assertion: extracted from module source and executed on an unfiltered frame →
  AssertionError "season > SEASON_MAX_GAMES leaked" (loud).
- pbp read-scope: `pq.read_table` wrapped with a spy; canary files for 2018/2019 on disk never
  opened. Extra observation: doctored non-lineage team codes (AAA/BBB) are rejected by the
  32-lineage filter (`z_table_entries=0`) — additional fail-closed behavior.
- The full 5,057-row real-data load (A7-6 replay) independently reproduced
  `n_dropped_over_ceiling=2491`, seasons 2000–2018.

Verdict A7-3: PASS (see VERDICT note N2 on the probe's expected failure mode).

## A7-4 Real-ledger absence / SYNTH-only / GENESIS placement

```
$ find <WT> \( -name "prediction_ledger*.jsonl" -o -name "predictions_*.jsonl" \) -not -path "*/.git/*"
(no hits — all listed *.jsonl are other cycles' control ledgers: TRIAL_LEDGER/event_log/etc.)
$ find ~/.my-quantitative-data/nfl-ng-scored-v1 -name "*.jsonl" -maxdepth 3
…/sandbox/predictions_NFL-WINPROB-NG-SCORED-V1-SANDBOX_2030.jsonl      (SANDBOX, synthetic)
…/selection/SELECTION_LEDGER.jsonl                                     (selection ledger)
$ ls research/control/NFL-WINPROB-NG-SCORED-V1/ledger/
nfl_ng_ledger.py  README.md  test_ledger_synthetic.py      (NO *.jsonl)
```

Sandbox ledger inventory (parsed):
```
rows: 45 | distinct game_ids: 15 | all SYNTH_ prefixed: True
ids: SYNTH_2030_W1_G01 … SYNTH_2030_W1_G15 | arms: ['B0','B1_STAR','C3'] | kickoff years: ['2030']
sha256 = 77029ae6713921ab204555b42eea36b368e905ec81fac7912b3ba2afa85b343c   (== DRYRUN_REPORT §2.5)
```

GENESIS digest placement:
```
$ grep -c "ae99a803" <sandbox>.jsonl <sandbox>.jsonl.genesis.json → 0  and  0
$ grep -rl "ae99a803" <WT> … → only documentation/assertion contexts:
  handoff_S_SYNTH.json, DISPATCH_A7_PRELAUNCH.md, sandbox_dryrun.py (inequality assertion),
  freeze_digests.json (pin), handoff_F_FREEZE.json, test_successor_synthetic.py (assertion),
  PORT_NOTES.md, DISPATCH_S_SYNTH.md, VERDICT_TABLE.md, DRYRUN_REPORT.md
  — and in ~/.my-quantitative-data/.../sandbox/dryrun_evidence.json solely as the field
  "freeze_genesis_digest_never_used": "ae99a803…" (a recorded negative assertion).
```
Sandbox line 1 anchors `GENESIS:e59ec10c…` (its own synthetic digest; sidecar `genesis_digest`
`e59ec10c61fa318969aa962589b8588f67b1f6aa6e36fd504b11e8e0b2d265b0`).

Verdict A7-4: PASS.

## A7-5 Rights

```
$ shasum -a 256 ~/.my-quantitative-data/nfl-ng-scored-v1/rights/nflverse-data_LICENSE.md
2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111  (18,651 bytes == freeze_digests bytes field)
```
Pin trail present: `lanes/A_DATA/DOWNLOAD_MANIFEST.md:12`, FREEZE_PACKET.md §3 (L108) and §11 (L347),
freeze_digests.json L61; `raw_pbp_2000_2017/ATTRIBUTION.md` records the live re-fetch
(2026-10-05, `https://raw.githubusercontent.com/nflverse/nflverse-data/HEAD/LICENSE.md`,
sha == pin) plus the full attribution chain (release URLs, timestamps, per-file provenance logs,
release markers; league/ESPN publication-commercial UNVERIFIED, fail-closed).
Auditor's one allowed live re-fetch: `curl …/nflverse-data/master/LICENSE` → HTTP 404 (wrong path
guess on my side); budget spent, not retried. Operative evidence = on-disk bytes + lane A's
recorded live fetch. Verdict A7-5: PASS on the evidence trail; auditor live probe NOT_CONCLUSIVE (N/A, optional).

## A7-6 Selection ledger completeness + own replay recompute

Ledger structure (parsed from `lanes/T_SELECT/SELECTION_LEDGER.jsonl`):
```
total rows: 38 | Counter: config=28, control=6, arm_verdict=4
config ids (28): B0, B1STAR, C1_B000/B025/B050/B075/B100, C2_L025_D1O2_H000/H025,
  C2_L025_D1O3_H000/H025, C2_L050_D1O2_H000/H025, C2_L050_D1O3_H000/H025,
  C2_L075_D1O2_H000/H025, C2_L075_D1O3_H000/H025, C2_NULL, C3_T000/T025/T050/T075/T100,
  C4_D000/D025/D050
arm_verdicts: [('C1','KILL',False), ('C2','KILL',True), ('C3','FIELD',False), ('C4','RELEASE',False)]
```
Grid completeness: C1×5 ✓, C2×12 + designed null ✓ (13), C3×5 ✓, C4×3 ✓, B0 + B1* ✓ = 28.

Own replay (script `tmp/audit_replay_a7_6.py` — no lane code imported; my own Elo/SOS/EPA-z
implementation per the frozen spec; zoneinfo kickoff canonicalization; raw inputs
`~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv` + 18 pbp parquets):
```
[load] rows=5057 dropped_over_ceiling=2491 seasons=2000..2018
[folds] per-fold rows {2014:255, 2015:256, 2016:254, 2017:256, 2018:254} pooled 1275
[z] entries=574 target seasons 2001..2018
[ll] B1STAR:  pooled=0.6524968479911611  (ledger 0.6524968479911611) Δ=0.0
[ll] C3_T050: pooled=0.6483475228409372  (ledger 0.6483475228409372) Δ=0.0
[ll] C1_B025: pooled=0.6526382289724465  (ledger 0.6526382289724465) Δ=0.0
[ll] B0:      pooled=0.6830369855947883  (ledger 0.6830369855947883) Δ=0.0
[B0] p0=0.5713990493903699 wins=2765 rows=4839   (== frozen B0 constant)
p range across replay rows [0.13, 0.89] → 1e-15 clamp never binds
A7_6 RECOMPUTE: ALL WITHIN 1e-9   EXIT=0
```
Interim auditor note: my first B0 side-calculation zipped a 4,839-element list against a
5,057-row mask (auditor bug, misalignment) — the ledger was never in doubt because the three
required replay-based configs already matched at Δ=0.0; B0 was recomputed from the aligned
records and also matches exactly. (Fix contained in auditor tmp script; no lane artifact touched.)
Machine-readable evidence: `tmp/a7_6_replay_evidence.json`.

Verdict A7-6: PASS.

## A7-7 Freeze packet completeness + code freeze + digests

Item mapping (DISPATCH_F_FREEZE.md "MUST BIND" 1–10 → FREEZE_PACKET.md):
1 arm enumeration → §1 (+§1.1 digests) · 2 selection ledger frozen → §2 · 3 data freeze → §3 ·
4 windows/capture → §4 · 5 ledger law → §5 · 6 GENESIS → §6 · 7 metrics/gates verbatim → §7 ·
8 power disclosure verbatim → §8 · 9 code freeze → §9 · 10 boundaries restated → §10. All 10 present.

Digest recomputes (all MATCH):
```
sha256(FREEZE_PACKET.md)                       = 9978a950cfa5…  == freeze_digests pin
sha256(canonical GENESIS payload w/ placeholders) = ae99a803dfcc… == genesis.payload_sha256_pinned
sha256(canonical B0 config)                    = bea17ae49a33…  == pin
sha256(canonical B1_STAR config)               = 5c97475c5df7…  == pin
sha256(canonical C3 config)                    = f7cde49880ee…  == pin
sha256(canonical C3_TWIN config)               = c86b3710ba16…  == pin
git cat-file -t 7ec4c539…  → commit
git ls-tree 7ec4c539 -- lanes/F_FREEZE/  → FREEZE_PACKET.md, freeze_digests.json
git show 7ec4c539:lanes/F_FREEZE/FREEZE_PACKET.md | shasum -a 256 → 9978a950…  (blob == pinned packet bytes)
CODE_FREEZE_ADDENDUM.md: "CODE_FREEZE_SHA = 7ec4c539394e68538f74df327d85fa2a477c6eb7"
```
Arm-config consistency vs SELECTION_REPORT: C3_T050 θ=50.0 fielded (slot 5), B0 constant
0.571399049390 (slot 1), B1* exempt (slot 2), C1/C2 KILL (3/4), C4 RELEASE (6), 7–9 released,
C3_TWIN diagnostic — all consistent between the two documents and the ledger verdict rows.
GENESIS placeholder discipline: packet §6 placeholders `PENDING_CONTROLLER_ADDENDUM` /
`POST_GO_TIMESTAMP` == freeze_digests literals; real GENESIS unwritten (no ledger exists).

Verdict A7-7: PASS.

## A7-8 Boundary compliance

```
registry row (read-only): budget {used: 0, max: 9}; s1: SEALED_UNTOUCHED;
  go_phrase_state: REGISTERED_NOT_CONSUMED; workers: 0
control state.json: budget_scored {used: 0, max: 9}; s1 SEALED_UNTOUCHED;
  go_phrase "… (registered, NOT typed; P-8 two-key: A7 verdict first)"
sandbox grep for real ids (2026_NN_TTT_TTT): no hits; lane docs mention 2026_04_ATL_NO /
  2026_05_TB_DAL only as kickoff/schedule facts — pattern `2026_NN_…0.x` (id + probability
  adjacency): 0 hits
GO phrase exact-string occurrences (worktree): control state.json (registered NOT typed),
  plan ×2, freeze_digests.json (registered field), FREEZE_PACKET.md §10 (boundaries verbatim),
  handoff_F_FREEZE.json item 10 — plus root plan ×2 and registry ×1 (registered contexts).
  No typed/consumed occurrence anywhere.
Suites re-run (PYTHONDONTWRITEBYTECODE=1, -p no:cacheprovider):
  pytest research/control/NFL-WINPROB-NG-SCORED-V1/ledger/test_ledger_synthetic.py → 42 passed, exit 0
  pytest lanes/S_SYNTH/test_successor_synthetic.py                                → 16 passed, exit 0
Port re-verified: cmp predecessor vs ported nfl_ng_ledger.py / test_ledger_synthetic.py → identical;
  sha256(port nfl_ng_ledger.py) = 6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c == pin
```
Verdict A7-8: PASS. (Registry head lag → VERDICT note N3.)

## A7-9 Verbatim language in FREEZE_PACKET.md

Wrap-tolerant grep (newlines flattened; bold markers accounted):
```
"Strong conclusions require ≥2 completed prospective seasons"            FOUND
"Single-season outputs are labelled **descriptive** and carry the…"       FOUND
"metric readings do NOT stop arms"                                        FOUND
"mid-window stopping on the primary metric is optional stopping and is prohibited" FOUND
"decision reads happen once per completed prospective season"             FOUND
"MDD(80%) ≈ 0.026–0.056 at 1 season"                                      FOUND
"0.019–0.039 at 2 seasons"                                                FOUND
"STARVED at 1 season"                                                     FOUND
"train-internal adjudication FIRST; prospective accrual is an evidence accumulator" FOUND
"PRIMARY: mean log loss `LL = −mean[y·ln p + (1−y)·ln(1−p)]`"             FOUND
"Brier score" / "calibration slope" / "Band: [0.85, 1.15]"                FOUND
"Playoffs separate"                                                       FOUND
"**T1 (discriminative gain over B1\*)**" incl. per-season ≥half clause    FOUND
"**R1**/**R2**/**R3**" verbatim gate sentences                            FOUND
"INCONCLUSIVE"                                                            FOUND
"Seed: INHERIT 20261005" / "10,000 resamples, percentile CI"              FOUND
"Candidate-ranking rule (REGISTERED, PROTOCOL §10-OQ-6) … C = C3 by"      FOUND
```
Verdict A7-9: PASS.

## A7-10 Coherence

- C2 MACHINERY_SUSPECT: ledger arm_verdict row `machinery_suspect: true`; SELECTION_REPORT §6
  control table row "YES — MACHINERY_SUSPECT" + §7 prose; FREEZE_PACKET §1 slot 4 (evidence
  retained, never fielded). Consistent across all three. ✓
- B1* TRAIN slope 1.605: SELECTION_REPORT §5 note ("the B1* baseline itself is underconfident on
  TRAIN (slope 1.605)"); freeze §1 slot 2 "slope 1.6051"; ledger B1STAR slope
  1.6050681017385453. ✓
- Margin config absence documented: handoff_S_SYNTH known_limitations ("Tool-level >=6h capture
  margin is NOT_RUN_MARGIN_CONFIG … enforced caller-side in sandbox_dryrun.enforce_capture_margin
  and is test-covered"); DRYRUN_REPORT §2 ("exact 6h accepted, 5h59m and post-kickoff rejected");
  VERDICT_TABLE row 13; freeze §4/§5 pins margin ≥6h. Token nuance → VERDICT note N1. ✓

Verdict A7-10: PASS.

---

## Auditor environment notes

- Probe outputs (fixtures, canary parquets, evidence JSONs, scripts) are confined to
  `lanes/A7_PRELAUNCH/tmp/`; worktree `git status` at audit end shows only auditor-owned untracked
  files + the untracked A7 dispatch packet. No tracked file, no lane artifact, no data file, no
  registry, no ledger was modified. One optional URL fetch consumed (HTTP 404 on a wrong path).
- Heavy global lock: not required (no heavy computation; the replay probe is single-process,
  minutes-scale, read-only).
