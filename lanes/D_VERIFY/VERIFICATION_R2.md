# VERIFICATION_R2 — Lane D · VERIFY (nflng-d2-verify), cycle NFL-WINPROB-NG-PREP-V1

- verifier: Lane D quant-auditor (independent; verify-only, never repairs) — owner follow-up
  round r2, delta over landed commits `6f6c1dd2`/`869b5925` (lane A r1) + `5a185ab6`/`1ea82df8`
  (lane E).
- date: 2026-10-05 · worktree `lane-d2-verify` · branch `orca/nfl-ngprep-d2-verify`
- start HEAD = dispatch/base SHA `1ea82df8eb276e5e8a96b1dfde9d1f02ffe454ba` (verified at
  intake: `git rev-parse HEAD` = 1ea82df8…, branch `orca/nfl-ngprep-d2-verify`,
  `git status --porcelain` empty — tree byte-clean before any lane D write).
- Method: every check re-measured from bytes with explicit commands; read-only outside
  `lanes/D_VERIFY/**`; no download; no credential; no metric on any outcome (all recounts are
  schema/coverage/chronology counts; adversarial ledger probes ran on SYNTHETIC rows in a
  `tempfile` dir, removed afterwards, nothing committed).

## Verdict table

| # | check | verdict |
|---|---|---|
| R2-1 | D2-a remediation: quotes vs held LICENSE bytes + diff scope | **PASS** |
| R2-2 | 2026 recount from r1 snapshot (independent) | **PASS** |
| R2-3 | Ledger tool REAL behavior: tests + adversarial probes | **PASS** |
| R2-4 | No real team codes / predictions in ledger dir | **PASS** |
| R2-5 | Trial accounting + control plane | **PASS** |
| R2-6 | Lane E implementation vs Lane C schema cross-check | **PASS** |

**SUMMARY VERDICT: PASS — 0 blocking defects.** 2 non-blocking observations (registry head
column staleness; two documented vocabulary widenings awaiting successor freeze-packet
restatement — both already disclosed by lane E). Details below.

---

## R2-1 — D2-a remediation: PASS

Artifact: `lanes/A_DATA/DATA_AUDIT_NFL_NG.md` §1 + `## ERRATUM (r1)` (commit `6f6c1dd2`).
Held license: `~/.my-quantitative-data/nfl-ng-prep-v1/rights/nflverse-data_LICENSE.md`.

1. **Diff scope**: `git diff 447559be..HEAD -- lanes/A_DATA/DATA_AUDIT_NFL_NG.md` (447559be =
   original lane A artifacts commit) shows EXACTLY two hunks: (i) `@@ -16,14 +16,21 @@` —
   replacement of the two defective §1 bullets (§2(a)(1) grant + §3(a)(1)(A) attribution)
   with the true verbatim text; the §4 Sui Generis bullet is untouched context; (ii)
   `@@ -226,3 +233,27 @@` — append of `## ERRATUM (r1)` at document end. Nothing else in the
   document changed — matches the ERRATUM's own claim "the only edit to §1 is the
   replacement of those two bullets".
2. **License pin re-hash**: `shasum -a 256` on the held LICENSE = `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111`,
   18,651 bytes — identical to the pin recorded in DATA_AUDIT §1, ERRATUM, and
   DOWNLOAD_MANIFEST row 1. The held bytes were NOT altered by the remediation.
3. **Quote verbatim-ness** (read-only python, whitespace-normalized substring search over
   the held bytes; the ERRATUM's disclosed transformation is line-wrap collapse only):
   - grant sentence "Subject to the terms and conditions of this Public License, the
     Licensor hereby grants You a worldwide, royalty-free, non-sublicensable, non-exclusive,
     irrevocable license to **exercise the Licensed Rights** in the Licensed Material to:" —
     FOUND in LICENSE (line 140 area) and in the doc; grant+items a/b found CONTIGUOUS in
     the license.
   - "a. reproduce and Share the Licensed Material, in whole or in part; and" FOUND;
     "b. produce, reproduce, and Share Adapted Material." FOUND (lowercase — the r1 defect's
     capitalization drift is gone).
   - §3 block "If You Share the Licensed Material (including in modified form), You must:" +
     "a. retain the following…" + "i. identification of the **creator(s)** of the Licensed
     Material and any others designated to receive attribution, in any reasonable manner
     requested by the Licensor (including by pseudonym if designated);" + "ii. a copyright
     notice;" — all FOUND, contiguous in the license; "(s)" restored (grep "creator(s)"
     hits LICENSE line 223).
   - §4 Sui Generis quote (previously verified verbatim in round 1) — still verbatim.
   - Old paraphrase text "perform, Display" — 0 hits in the held LICENSE (grep exit 1),
     confirming the old quote could never have been verbatim and the ERRATUM's description
     of the defect is accurate.

**Verdict: the D2-a remediation is faithful — both quotes now byte-match the held license
modulo disclosed whitespace collapse; pin unchanged; no collateral edits.**

## R2-2 — 2026 recount from r1 snapshot: PASS

Freshest snapshot per DOWNLOAD_MANIFEST.md `## r1 refresh`: `~/.my-quantitative-data/nfl-ng-prep-v1/raw_schedules_r1_20261005/games.csv`.
Lane D did NOT trust the agent's numbers — recounted independently with read-only
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`, kickoff UTC derived as
`gameday`+`gametime` in `America/New_York` → UTC, and **Lane D's own measurement instant**
(not the agent's 07:16:19Z): `2026-10-05T07:23:28Z`.

Evidence:

- Re-hash: `shasum -a 256` = `486d72273c0d9650756176fc016a0852c65ad6f030f443805c20cb35e387a9fc`,
  2,182,513 bytes — matches manifest rows r1-1 exactly (pin verified before use).
- Independent recount results vs claims:

| quantity | claimed (r1) | Lane D recount @07:23:28Z | match |
|---|---|---|---|
| total rows in file | 7,548 | 7,548 | YES |
| 2026 scheduled | 272, all REG weeks 1–18 | 272, `game_type={REG}`, weeks 1–18 | YES |
| kickoff ≤ now (played/in-flight) | 63, every one NOT_RUN prospective forever | 63 | YES |
| — all with final scores | 63/63 (incl. `2026_04_DET_CAR` now finalized) | `all(scored)` = True, no exceptions | YES |
| future (kickoff > now) | 209 | 209 | YES |
| scored among future | 0 | 0 | YES |
| earliest future kickoff + game_id | 2026-10-06T00:15:00Z `2026_04_ATL_NO` | 2026-10-06T00:15:00Z `2026_04_ATL_NO` (ATL @ NO) | YES |
| next futures | 2026-10-09T00:15Z `2026_05_TB_DAL`; 2026-10-11T13:30Z `2026_05_PHI_JAX` | identical | YES |
| internal consistency | 63 + 209 = 272 | 272 | YES |

- **Prospective law statement confirmed in bytes**: GAMES_2026_CLASSIFICATION.md
  `## Recount r1` states games with kickoff ≤ now are "every one NOT_RUN prospective
  forever" and "**no retrospective predictions for any played game, ever**"; the 209 future
  games are the only 2026 games eligible for a genuinely prospective append-only ledger
  recorded strictly before kickoff UTC at a successor scored cycle's own gate; the cycle
  prospective epoch is UNCHANGED (2026-10-05T03:13:51Z) and the recount's "now" is a
  measurement instant, not a new epoch. handoff_A_r1 authority_claims restate the same law.
- No win-prob metric computed; schema/coverage/chronology counts only.

**Verdict: every r1 recount claim reproduces from bytes at an independent instant.**

## R2-3 — Ledger tool REAL behavior: PASS

1. **Test suite re-run by Lane D** (in the lane-d2-verify worktree):
   `/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest research/control/NFL-WINPROB-NG-PREP-V1/ledger/test_ledger_synthetic.py -v`
   → **42 passed, 0 failed, 0 skipped, exit code 0** (pytest 9.1.1, Python 3.12.14).
   Matches handoff_E's recorded result (42/42, exit 0).
2. **Code inspection** (`nfl_ng_ledger.py`):
   - R2: `if recorded >= kickoff: raise LedgerValidationError("timestamp law (R2): …strictly < kickoff_utc")` (append-time, line ~403); scoring-time re-check `actual_dt <= recorded_dt → INVALID_PROSPECTIVE` + `actual_dt < freeze_dt → NOT_RUN` (validate_for_scoring).
   - R8: `_has_outcome_key` substring-scans every key (case-insensitive) against `OUTCOME_BLOCKLIST = (score, pts, result, winner, outcome, final, margin, total, spread)`; enforced in `_validate_prediction_row_fields` AND read-side in `verify_chain`.
   - Tamper detection: `verify_chain` recomputes every `row_hash` over the row rebuilt in the binding field order and checks chain linkage; scoring refuses on ANY broken index (fail-closed program stop).
   - Write surface: the ONLY `open()` on the ledger file is `open(self._path, "r+", encoding="utf-8")` under exclusive `fcntl.flock`; the only write path is `_write_row` → `seek(0, os.SEEK_END)` → append + flush + fsync. `write_text` targets only the genesis sidecar (create-once: `create_ledger` refuses if either file exists). Static grep: ZERO `.remove/.unlink/.truncate` calls; no plain `'w'`-mode open anywhere.
3. **Adversarial live check (Lane D's own, SYNTHETIC rows, tempfile dir, not committed)**:
   - (a) `recorded_at_utc == kickoff_utc` AND `recorded_at_utc > kickoff_utc` → both RAISE `LedgerValidationError: timestamp law (R2): recorded_at_utc must be strictly < kickoff_utc`. CONFIRMED.
   - (b) Appending a row containing key `home_score` / `away_score` / `Result` / `winner_id` → all four RAISE `LedgerValidationError` (refused first by the closed-17-field-set law; the R8 blocklist is the independent second layer — direct probe `_has_outcome_key({'home_score': …})` flags every outcome-style key including `total_line`, `final_flag`, `spread_close`, `pts_for`, `margin_victory`). CONFIRMED (append refused; no outcome key can ever persist).
   - (c) After two valid appends: flipping one byte mid-file (p_home digit `0.542317→0.542318` in line 1) → `verify_chain` returns broken indices `[0]`; a same-length game_id swap-tamper → broken `[0]`; restore → `[]` (intact). CONFIRMED. (Note: chain linkage is defined over STORED hashes, so a single mid-file tamper flags exactly its own index instead of cascading — the test suite additionally proves a "competent" tamper with recomputed hash is flagged at the child index and further appends are refused fail-closed.)
   - (d) NO rewrite/delete API: module introspection + static grep — only `r+` (EOF-append under lock), sidecar write-once, no remove/unlink/truncate, `__all__` exposes no edit/delete/rewrite function. CONFIRMED.
   - Tempdir removed after the probe; no files left; nothing committed.

**Verdict: the ledger tool behaves as claimed under adversarial use.**

## R2-4 — No real team codes / predictions: PASS

Command: `grep -rnE '\b(ARZ|ATL|BAL|BUF|CAR|CHI|CIN|CLE|DAL|DEN|DET|GB|HOU|IND|JAX|KC|LAC|LAR|LV|MIA|MIN|NE|NO|NYG|NYJ|PHI|PIT|SEA|SF|TB|TEN|WAS)\b'` over
`research/control/NFL-WINPROB-NG-PREP-V1/ledger/` (case-SENSITIVE, word-bounded).

- **0 hits** in all three files (`nfl_ng_ledger.py`, `test_ledger_synthetic.py`, `README.md`)
  — stronger than the requirement (not even README prose contains real team codes; the
  README's successor-usage section is team-agnostic).
- The naive case-INSENSITIVE grep returns 683 raw lines, but every one is a substring
  artifact (e.g. `NE` inside "genesis"/"None"/"line", `NO` inside "notice"/"no", `IND`
  inside "index"/"find", `WAS` inside "was") — zero are team codes.
- Test fixtures use ONLY `TEAM_X`/`TEAM_Y`/`TEAM_Z` (13 occurrences in the test file);
  game ids are synthetic (`2026_W01_TEAMX_TEAMY`-style), digests are `aa…`/`bb…`-style
  fabrications; the README states "no real games, no real predictions, no metrics on
  outcomes, and no ledger file".

**Verdict: no real NFL team code, game, or prediction appears anywhere in the ledger dir.**

## R2-5 — Trial accounting + control plane: PASS

Commands run from root `/Users/hoangminhlong/my-quantitative` (control plane):

- `.venv/bin/python research/researchctl.py cycle list` → row
  `NFL-WINPROB-NG-PREP-V1  ACTIVE_LIGHT  0/0  03c8c87  orca/nfl-winprob-ng-prep-v1-integration`
  — lifecycle ACTIVE_LIGHT, **budget 0/0 (0 scored)**, integration branch matches state.json.
- `.venv/bin/python research/researchctl.py locks inspect` → `verdict: FREE_PROVEN`,
  `flock_state: free`, `pid: null` — heavy lock FREE (no conflict for the pytest run).
- `git -C …/integration rev-parse HEAD` = `1ea82df8eb276e5e8a96b1dfde9d1f02ffe454ba`;
  `git status --porcelain` = empty — **integration worktree CLEAN at the dispatch SHA**.
- Handoffs (python `json.load` + field assertions + git resolution):
  - `lanes/A_DATA/handoff_A_r1.json`: schema `zcode_orch_v3_handoff@1`, task_id
    `nflng-a-data-r1`, cycle_id `NFL-WINPROB-NG-PREP-V1`, dispatch_sha = actual_start_sha =
    `b075089136ed4a34968cca3d0ecb8576280f1c8f` (resolves: "NFL-NG-PREP lane A: handoff
    commit_sha backfill" — lane A round-1 tip, correct r1 base), commit_sha
    `9b03bb2d8d3807dd4dbefab106515855d4c6b021` (resolves: "NFL-NG-PREP lane A r1: D2-a
    remediation + 2026 recount" = lane-A-branch artifacts commit; `git merge-base
    --is-ancestor` dispatch→commit YES). All required fields present. `handoff_A.json`
    (round 1) untouched per changed_paths and verified unchanged in the R2-1 diff scope.
  - `lanes/E_LEDGER/handoff_E.json`: schema `zcode_orch_v3_handoff@1`, task_id
    `nflng-e-ledger`, dispatch_sha = actual_start_sha = `03c8c87dd8a25b67c402c56d273c3460326b39f9`
    (resolves: controller-synthesis commit — the integration HEAD lane E was cut from),
    commit_sha `177fa4ef7a0b7066dd0c806fc31d6258b0b97d44` (resolves: "NFL-NG-PREP lane E:
    append-only prediction ledger tool…" = lane-E-branch artifacts commit; ancestor check
    YES). All required fields present, incl. recorded test evidence 42/42 exit 0 (reproduced
    by Lane D in R2-3).
  - Note: no r1/E dispatch packets are repo-resident under `lanes/DISPATCH/` (owner
    follow-up dispatches were issued in-chat, as this lane's own was); handoff placement
    (`lanes/A_DATA/handoff_A_r1.json`, `lanes/E_LEDGER/handoff_E.json`) matches the
    round-2 owner dispatch naming and the landed tree.
- 0-scored corroboration: state.json `budget {used:0, max:0}`, `go_phrase: null`,
  `go_phrase_state: NOT_REGISTERED`; the ledger dir ships NO ledger file by construction
  (create_ledger refuses to overwrite; Lane D's probes ran in a removed tempdir).

**Observation O-1 (non-blocking)**: the registry `head` column shows `03c8c87` while the
integration branch tip is `1ea82df8` — the registry was last CAS-updated at controller
synthesis; lanes A-r1/E landed afterward without a registry write. The live SHA is carried
by the dispatch packets (this lane's base = 1ea82df8), so control coherence holds; a
controller registry refresh is housekeeping, not a defect.

## R2-6 — Lane E implementation vs Lane C schema: PASS

Cross-check of `research/control/NFL-WINPROB-NG-PREP-V1/ledger/nfl_ng_ledger.py` against
`lanes/C_PROTOCOL/LEDGER_SCHEMA.md` (programmatic field-order assertion + code read):

| schema element | implementation | match |
|---|---|---|
| §2 field names + binding order (17 fields) | `FIELD_ORDER` asserted `==` the §2 list element-for-element, exact order (programmatic check: True, n=17) | EXACT |
| §1 filename law `predictions_<cycle_id>_<season>.jsonl` | `create_ledger` refuses any other name | EXACT |
| §1 GENESIS anchor `prev_row_hash = "GENESIS:" + sha256_hex(freeze_packet_file_bytes)` | `_GENESIS_ANCHOR_RE` + line-1 linkage vs genesis-bound digest (append + verify + `expected_genesis_digest` cross-check) | EXACT |
| §3 canonical form (`,`/`:` separators, no whitespace, `ensure_ascii=false`, UTF-8) | `canonical_json` exactly this | EXACT |
| §3 `row_hash = sha256_hex(canonical_json(row − row_hash))` incl. prev_row_hash | `compute_row_hash` removes only `row_hash`, keeps `prev_row_hash`; caller-key-order independent (tested) | EXACT |
| R2 strict `recorded_at_utc < kickoff_utc` at append + scoring vs ACTUAL kickoff (`actual > recorded` AND `actual ≥ freeze`) | enforced both (append raise; `INVALID_PROSPECTIVE`/`NOT_RUN` at scoring) | EXACT |
| R6 `p_home` string, exactly 6 fractional digits, strict (0,1) | `^\d\.\d{6}$` + `Decimal` open-interval bound; `0.000001`/`0.999999` accepted, `0.000000`/`1.000000` rejected (tested) | EXACT |
| R7 enums REG/POST (PRE forbidden), season ≥ 2026 | `GAME_TYPES` + season guard | EXACT |
| R5 duplicate (game_id, arm_id) | enforced at append + read | EXACT |
| R8 no-outcome vocabulary | blocklist = schema list (score/home_score/away_score/result/winner/outcome/total/spread — the score- subsumed forms) ∪ dispatch extras (`pts`,`final`,`margin`), case-insensitive substring | EXACT ∪ documented stronger |
| R9 immutability / append-only | locked EOF-append only; no rewrite/delete API (R2-3 d) | EXACT |
| R10 classifications | `VALID_PROSPECTIVE`/`INVALID_PROSPECTIVE`/`NOT_SCORED_CANCELLED`/`NOT_RUN` + game-level `not_run_games`; only VALID aggregate-eligible; never inferred PASS from absence | EXACT + documented extension |

**Postponement/cancellation semantics**: schema fixes the classification (move later ⇒ rows
stay valid, re-confirmed vs actual kickoff at scoring; move earlier past `recorded_at_utc`
⇒ `INVALID_PROSPECTIVE`; cancel ⇒ `NOT_SCORED_CANCELLED`, no outcome join). The
implementation matches exactly and adds a hash-chained NOTICE-row disclosure mechanism
inside the same append-only file — the schema is silent on a mechanism, so this is a
documented addition, not a semantic change.

**The 6 schema-silent decisions disclosed by lane E** (README "Schema-silent decisions" 1–6
+ handoff_E authority_claims/known_limitations) — each confirmed FAITHFUL (none is a silent
semantic change):

1. **Genesis sidecar** `<ledger>.genesis.json` (self-hashed; binds genesis digest, cycle,
   season, optional arm registry R4, optional freeze timestamp). Schema fixes only line-1's
   anchor; the sidecar strengthens enforcement (append refuses without a matching binding;
   tamper fails closed). Faithful.
2. **Notice row types** (POSTPONEMENT/CANCELLATION) — mechanism for the schema's own
   classification semantics; chained into the same hash chain; nothing edited in place.
   Faithful.
3. **Fifth scoring class `NOT_SCORED_NO_ACTUAL_DATA`** — rows whose game is absent from the
   scoring input: excluded + disclosed, never dropped silently. Vocabulary widening,
   conservative direction (missing evidence stays visible). Faithful; row-level `NOT_RUN`
   (played-before-freeze write-off) is likewise consistent with the cycle prospective law
   (state.json) and the README's retro-impossibility law; restated for the freeze packet.
4. **Structural-only digest checks at append** (64-hex form); semantic R3 (match freeze
   registry, commit resolves, manifest recomputes) deferred to scoring time against the
   freeze packet — which does not exist in PREP. Faithful; successor must implement the
   semantic half (already flagged in known_limitations).
5. **Canonical field order** (§2 binding order) over the dispatch's "sorted keys" shorthand
   — the schema itself declares §2 order binding; lane E followed the named design
   authority. Faithful (schema-conformant; superseded shorthand disclosed).
6. **Locking discipline** (exclusive `fcntl.flock`; module-cooperating writers only;
   non-cooperating tampering caught by `verify_chain`, not prevented) — documented posture;
   strengthen, not weaken. Faithful.

Also verified: the PROTOCOL sections the tool cites exist (§4 ledger law at line 185,
§6.3 program-level stops at line 309, §7.3 pooling, §8 operational plan at line 342).

---

## DEFECTS

None. 0 blocking, 0 non-blocking defects this round.

## NON-BLOCKING OBSERVATIONS

1. **O-1 registry head staleness**: registry row shows head `03c8c87` vs integration tip
   `1ea82df8` (lanes A-r1/E landed after the last registry CAS). Dispatch packets carry the
   live SHA; coherence holds. Controller housekeeping only.
2. **O-2 vocabulary widenings awaiting freeze-packet restatement**: row-level `NOT_RUN`
   (played-before-freeze write-off) + fifth class `NOT_SCORED_NO_ACTUAL_DATA` extend the
   schema §4-R10 vocabulary conservatively (excluded + disclosed, never inferred PASS);
   both are disclosed by lane E (README, handoff_E) and MUST be restated in the successor
   freeze packet per lane E's own requirement. No action for THIS cycle.
3. Round-2 dispatch packets (A-r1, E, D-r2) are in-chat, not repo-resident; handoff paths
   verified against the round-2 owner dispatch naming and the landed tree.

## Verifier declarations

- Read-only outside `lanes/D_VERIFY/**` (re-hashes, greps, read-only python recounts,
  pytest run, tempfile-dir adversarial probes — tempdir removed; no bytes written elsewhere;
  no downloads; no credentials; no push/merge/rebase; no `git add -A`; no metric computed
  on any outcome; no real-game prediction made).
- Lane D did NOT repair anything this round — there was nothing to repair.
- Lane D ends with exactly the two authorized commits (artifacts + handoff_sha backfill) on
  `orca/nfl-ngprep-d2-verify`, tree clean.
