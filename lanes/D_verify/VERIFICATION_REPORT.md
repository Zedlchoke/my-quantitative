# VERIFICATION_REPORT.md — Lane D independent verification, cycle NBA-WINPROB-PREP-V1

- Verifier: Lane D (independent; nothing repaired — defects only reported)
- Date: 2026-10-04 · Method: fresh re-measurement only (no chat prose trusted, no controller numbers accepted without re-derivation)
- Dispatch/actual start SHA: `8a7ebc3b1d51f067e512de90eeba04ade3afe212` (worktree HEAD, unchanged during verification)
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python` · Recounts: my own O(n) csv-module scripts (not the package's build code)

## Verdict table

| # | Claim | Verdict | Evidence (re-measured this session) |
|---|-------|---------|-------------------------------------|
| 1a | Root on `main`, last 2 commits = control plane (c7611803 + 0673a73e), clean | **PASS** | branch `main`; HEAD `0673a73e`; log: `0673a73e` (registry sync) then `c7611803` (G0 bootstrap); `git status --porcelain` empty |
| 1b | Worktree branch + HEAD + clean + 5 commits on d8cf8eca | **PASS** | branch `orca/nba-winprob-prep-v1-integration`; HEAD `8a7ebc3b1d51f067e512de90eeba04ade3afe212`; porcelain empty; `rev-list --count d8cf8eca..HEAD` = 5 |
| 1c | Each lane commit touches ONLY its lane paths | **PASS** | `git show --stat`: 14215cb8→`lanes/A_rights_audit/` (2 files); 48fc951f→`lanes/B_dataset/` (5); 09b5eb74→`lanes/C_protocol/` (2); bc19408e→`lanes/NFL_AUDIT/` (2); 8a7ebc3b→`PREP_SUMMARY.md` + `nba_winprob/` (13). No cross-lane or out-of-scope paths |
| 2a | Registry row: ACTIVE_LIGHT, budget max 0, head 8a7ebc3b | **PASS** | `plans/CYCLE_REGISTRY.json`: cycle_id `NBA-WINPROB-PREP-V1`, `lifecycle: ACTIVE_LIGHT`, `budget {used:0, max:0}`, `head: 8a7ebc3b1d51f067e512de90eeba04ade3afe212`, `go_phrase: ""`, `go_phrase_state: NOT_REGISTERED` |
| 2b | No other cycle rows modified by control-plane commits | **PASS** | `git diff d8cf8eca..0673a73e -- plans/`: CYCLE_REGISTRY.json changes = header `updated_at_utc` + `write_token` + NBA-WINPROB row insertion only; ACTIVE_CYCLES.json = projection timestamp + NBA row insertion only; events jsonl append-only. 85 other cycle rows untouched |
| 3a | Raw sha256 == d46ed354… | **PASS** | `shasum -a 256` = `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc` (18,173,265 bytes) |
| 3b | ATTRIBUTION.md with CC BY 4.0 + provenance + hash | **PASS** | File present; quotes root-README CC BY 4.0 sentence, BRef provenance, attribution string, sha256 (matches), size, usage boundary |
| 3c | Derived counts: games 63,157 / lineages 53 / participants 126,314 / f538_reference 126,314 / features 63,157 | **PASS** | `wc -l` minus header: 63,158/54/126,315/126,315/63,158 lines → 63,157/53/126,314/126,314/63,157 rows |
| 3d | Manifest hashes match actual files | **PASS (4/4 hashed)** | Recomputed sha256: games `e24d9a3b…`, lineages `c8cdd58a…`, participants `fd7cb539…`, f538_reference `c2b429f3…` — all identical to BUILD_MANIFEST.json |
| 3e | features.csv hash | **PASS, computed** (gap noted, defect D1) | FEATURES_MANIFEST.json contains NO sha256 field. My computation: `644cd740a5006c33fb0cf093244644fb02c6ffea6e680962ec624554ea3cf799` |
| 4 | Independent recount: 63,157 games / 126,314 rows / pair-repeats 5 / team-doubles 12 across 6 dates incl 2008-03-07 Hawks+Heat / 53 lineages / 1946-11-01..2015-06-16 | **PASS (all sub-claims)** | My O(n) script on RAW csv: rows=126,314; distinct game_id=63,157; distinct fran_id=53; (pair,date)>1 keys = **5** {1970-02-08 ATL/CHI, 1954-03-08 BLB/MLH, 1976-01-24 NYA/VIR, 1979-03-23 NJN/PHI, 1983-04-13 LAL/SAS}; (fran,date)>1 = **12** across **6** dates incl 2008-03-07 (Hawks, Heat); first date_game 1946-11-01, last 2015-06-16 |
| 5 | pytest: 20 passed | **PASS** | `PYTHONPATH=<wt> python -m pytest <wt>/nba_winprob/tests -q` → **20 passed in 0.22s** |
| 6 | evaluate no-args → exit 3 + REFUSED | **PASS** | Actual exit code **3**; stderr: "REFUSED: no --freeze-manifest… budget 0 scored cells and no GO phrase by law… NOT_RUN in this cycle" + successor registration path |
| 7 | No real-data scored metric anywhere | **PASS** | Grep `log.?loss|brier|accuracy` + decimal sweep: protocol.py has metric *definitions* only; test_metrics_model.py uses hand-computed synthetic fixtures (e.g. log_loss([0.8],[1])=-ln 0.8); PREP_SUMMARY numbers are synthetic golden literals (0.640065/0.640175) + explicit NOT_RUN statement; export_features.py is a pure deterministic transform (docstring + code: no metric), features.csv is label-free (no home_win field written); evaluate REFUSED (check 6) |
| 8a | 538 root README CC BY 4.0 sentence | **PASS** | Re-fetched https://github.com/fivethirtyeight/data: "Unless otherwise noted, our data sets are available under the Creative Commons Attribution 4.0 International License" — verbatim match to RIGHTS_MEMO §2.2 and ATTRIBUTION.md |
| 8b | SR ToU 5(11) AI/ML restriction present | **PASS** | Direct WebFetch → HTTP 403 this session; web_reader fetch OK. Item 11 of Section 5 prohibits using Content "for purposes of training, fine-tuning, prompting, or instructing artificial intelligence models… (ii) supporting machine learning methods used to predict, classify, label, or score inputs" — verbatim match to RIGHTS_MEMO §2.5 |
| 8c | balldontlie free tier = Teams/Players/Games only | **PASS** | Re-fetched https://docs.balldontlie.io/: free tier Teams=Yes, Players=Yes, Games=Yes; Season Averages/Injuries/Box Scores/Odds=No; 5 req/min; "An API key is required." — matches RIGHTS_MEMO §2.3 |
| 9a | Protocol sec5 arms == 9 | **PASS** | Table rows #1–#9: B0, B1-a/b/c/d (K{16,32}×HCA{0,100}), B2-a/b/c/d; "TOTAL = 9 arms (B0 = 1; B1 grid = 4; B2 variants = 4)" |
| 9b | Test seasons 2009..2015, 8,956 = 8,369 RS + 587 PO | **PASS** | DATASET_SCHEMA §7 states it; my recount of derived/games.csv: RS=8,369, PO=587, total=8,956; per-season 1,315/1,312/1,311/1,074/1,314/1,319/1,311 — all match §7 exactly |
| 10 | NFL annex: final verdict + conditions + nflverse CC BY 4.0 | **PASS** | Matrix exists; final section: "**PASS (conditional)**" + 9 numbered conditions + scope guard (no NFL cycle); E1 pins nflverse-data LICENSE.md; my re-fetch of https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md = "Attribution 4.0 International" (CC BY 4.0) — claim matches |
| 11a | Plan: budget 0, no GO phrase, date-grain as-of law | **PASS** | `plans/PLAN_nba_winprob_prep_v1.md`: "budget max = 0 scored cells" (§0/l.5, §0 consequence l.22), §8 "This cycle registers NO GO phrase" (phrase shown only as *proposed for successor*), §4 "As-of law (v1, date-grain)"; registry go_phrase empty/NOT_REGISTERED |
| 11b | PREP_SUMMARY correction #2 (pair==5) | **PASS** | Recount pair-repeats = 5; mechanism corroborated in raw bytes: games.csv `is_protest_completion` = exactly 5 rows, 4 sitting on pair-repeat days (1970-02-08, 1976-01-24, 1979-03-23, 1983-04-13) + genuine 1954-03-08 BLB/MLH doubleheader; 2008-03-07 is a different-opponents day (Hawks: vs CHA + vs MIA completion; Heat: vs GSW + vs ATL completion) — exactly as the correction states; B's "6" is the team-double date count |
| 11c | PREP_SUMMARY correction #3 (test seasons 2009..2015) | **PASS** | Verified directly (see 9b): 8,956 = 8,369 + 587; data ends 2015-06-16 |

## Defects

| ID | Severity | Description |
|----|----------|-------------|
| D1 | **LOW** | `FEATURES_MANIFEST.json` carries no sha256 for `features.csv` (the other 4 derived files are pinned in `BUILD_MANIFEST.json`). Chain-of-custody gap only — file re-hashed by me: `644cd740a5006c33fb0cf093244644fb02c6ffea6e680962ec624554ea3cf799`. Successor cycle should pin it before scoring. |
| D2 | **LOW** (source-data observation, no claim affected) | In the raw 538 file, the 2007-12-19 ATL-MIA protest completion is recorded with `date_game` 3/7/2008 while its `game_id` encodes `200803080ATL` and the regularly-scheduled rematch is a separate row `200803081ATL` dated 3/8/2008 (notes string also misspells "Competion"). Internal counts are self-consistent and every controller claim survives; noted so the successor cycle does not treat `game_id` date prefix as authoritative. |

No HIGH or MED defects. No check UNVERIFIED.

## Session verification log (honest)

- All 11 checks executed live this session against: root repo, worktree (HEAD unchanged at 8a7ebc3b throughout), `~/.my-quantitative-data/nba-538-v1/{raw,derived}`, and 4 web URLs.
- One fetch anomaly: sports-reference.com/termsofuse.html returned HTTP 403 to WebFetch (same behavior lane A logged); resolved with a single web_reader fetch — page retrieved, clause verified. Not counted as a defect.
- No git mutations, no writes outside `lanes/D_verify/`, no downloads of new data, no accounts/keys.

## Overall verdict

**VERIFICATION PASS — all 11 checks PASS (0 FAIL, 0 UNVERIFIED); 2 LOW defects (D1 manifest hash gap, D2 source-data observation); 0 HIGH/MED. Plan gate G5 requirement ("lane D report with 0 unresolved HIGH/CRITICAL") is satisfied.**
