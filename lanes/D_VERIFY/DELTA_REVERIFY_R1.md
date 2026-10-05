# DELTA_REVERIFY_R1 — Lane D independent POST-FIX re-verification (task nbang-d-verify-r1)

- Cycle: `NBA-WINPROB-NG-PREP-V1` · lane: `D_VERIFY` · role: quant-auditor (fresh
  context, independent of round-0) · date: 2026-10-05 · measured on HEAD
  `2cd4674e0ed66afa5db6e6daa5a7cfb5d0068354`, branch
  `orca/nba-winprob-ng-prep-v1-integration`, worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-ng-prep-v1/integration`.
- Purpose: after the D1 remediation (owner order 2026-10-05, task
  `nbang-a-data-r1`, commit `2cd4674e`), independently re-measure from bytes that
  (a) the fix is correct everywhere and (b) the core laws still reconcile.
- Method: recompute from bytes, never repair, never ask lanes how to pass.
  Write scope = `lanes/D_VERIFY/**` only. Schema/coverage counting ONLY — no
  win-prob metric, no model, no score computed on any real outcome.
- Recompute script + machine-readable evidence (this lane):
  `lanes/D_VERIFY/delta_reverify_r1.py` → `lanes/D_VERIFY/delta_reverify_r1_evidence.json`
  (run: `.venv/bin/python lanes/D_VERIFY/delta_reverify_r1.py`, exit 0, 21/21 gates PASS).
- Inputs read: round-0 `lanes/D_VERIFY/VERIFICATION_REPORT.md`,
  `lanes/A_DATA/ERRATUM_PBP_GAP_R1.md`, corrected
  `GAME_UNIVERSE_SPEC_NBA_2016PLUS.md` (§5/§6), `PIT_AUDIT_NBA.md`,
  `handoff_A.json`, `handoff_A_r1.json`, `DOWNLOAD_MANIFEST.md`,
  `BDL_CROSSCHECK_A_DATA.json`, `BDL_CROSSCHECK_NBA.md`; data at
  `~/.my-quantitative-data/nba-hoopr-v1/raw/` and `~/.my-quantitative-data/nba-ng-prep-v1/`.

## 1. Check results (all evidence re-measured THIS session)

### Check 1 — D1 fix (played-without-pbp gap): **PASS**

- **My own re-measurement** (schedule `status_type_completed=="true"` minus
  `all-star`/`rising stars` exhibitions minus unique pbp `game_id` per season;
  pbp 2016–2025 under `~/.my-quantitative-data/nba-ng-prep-v1/pbp_2016_2025/`,
  2026 in-corpus; `game_id` dtype int32, 0 nulls in all 11 parquets; gap
  identical under str and int64 keys):
  **exactly 14 games** —
  2016×3: `400828393` (NY–ATL 2016-01-03, 111–97), `400828600` (CLE–SA
  2016-01-30, 117–103), `400828893` (WSH–CHI 2016-03-16, 117–96);
  2018×4: `400974444` (NO–GS 2017-10-20, 120–128), `400974773` (WSH–DET
  2017-10-20, 115–111), `400975617` (SAC–OKC 2018-02-22, 107–110),
  `400975670` (SAC–BKN 2018-03-01, 116–111);
  2020×6: `401161490` (POR–DET 2020-02-24, 107–104), `401161505` (GS–SAC
  2020-02-25, 94–112), `401161528` (LAC–DEN 2020-02-29, 132–103),
  `401161533` (MEM–LAL 2020-02-29, 105–88), `401161530` (ATL–POR 2020-03-01,
  129–117), `401161536` (PHX–GS 2020-03-01, 99–115);
  2026×1: `401810469` (CHI–LAC 2026-01-20, 138–110).
  **0 in 2017/2019/2021/2022/2023/2024/2025.** Set-equality against the
  erratum's 14-id list: game-for-game TRUE (all 14 status Final with scores).
- Corrected text confirmed in place: spec §5 ("**14 games**, not 4" + full
  game-id list + ERRATUM pointer + "tolerate … never silently impute");
  `PIT_AUDIT_NBA.md` §3 ("14 played games without pbp … 2016×3, 2018×4,
  2020×6, 2026×1 — full game-id list in spec §5" + tolerance law);
  `handoff_A.json` known_limitations (full 14-id list + tolerate law + R1
  correction note).
- **Stale-string grep over `lanes/A_DATA/`** (re-measured): zero stale
  assertions remain. Every remaining occurrence of the old figures is inside a
  correction-note context that quotes the defect and states the fix:
  `ERRATUM_PBP_GAP_R1.md` lines 16/94/99–100 (verifier-quote + "→ 14"
  replacement arrows), `handoff_A.json` line 68 ("corrected 4 -> 14"). No file
  asserts the 4-game figure, `All other seasons: 0`, `268,642,536`, or
  "26 requests" as current truth; the manifest now states 248,642,536 and
  36 (16+9+11).
- **D5 companion fix verified from bytes**: all 19 exhibitions carry pbp
  (per-season 1,1,2,2,2,1,1,1,1,3,4 = 19/19; my measurement, matches spec §5
  corrected bullet).
- **D3 companion fix re-summed**: `os.path.getsize` over the 10 parquets
  2016–2025 = **248,642,536 B** exactly = manifest's own per-file sum;
  all 10 sha256 **re-hashed MATCH** the manifest (bytes unchanged since
  round-0 — the fix touched no data).
- **D4 companion fix confirmed**: manifest + `BDL_CROSSCHECK_NBA.md` both state
  **36 BDL requests (16 + 9 + 11)**; zero stale "26 requests" hits.

### Check 2 — Game universe law re-check: **PASS**

- Law re-applied from the 11 CSV bytes: completed ∧ ¬exhibition ⇒ played.
  **14,254 raw = 14,168 played + 19 exhibitions + 67 postponed — exact, zero
  residue** (my arithmetic, not round-0's).
- `game_id` unique 14,254/14,254; `id == game_id` all rows; `season` field ==
  file all rows.
- Per-season played totals reproduced: 1,316/1,309/1,312/1,312/1,143/1,171/
  1,323/1,320/1,319/1,321/1,322 = 14,168.
- Composition: RS standings-embedded **1,230 ×9 seasons + 1,059 (2020) +
  1,080 (2021)**; play-in played **37** (1 + 6×6); playoffs played **919**;
  Cup finals **3** (67 cup rows/season 2024–2026, final = `Championship`
  headline, exactly 1/season).
- Postponed listings ∩ pbp = 0 (re-measured across all 11 seasons).

### Check 3 — BDL 22/22 re-verification (from stored redacted artifacts): **PASS**

- 11 redacted `resp_{season}_{date}.json` files, seasons 2016–2026 (incl.
  required 2016/2020/2026); **119 BDL game records**; union of fields =
  `{id, date, datetime, season, status, home, visitor, home_team_score,
  visitor_team_score}` — exactly the documented redacted schema, no auth
  fields anywhere.
- **Field-level re-match, done by me**: for each probed date I selected the
  first ≤2 completed non-exhibition games by `game_id` from the schedule CSV
  and matched each against the stored BDL records (abbreviation map
  NYK→NY, NOP→NO, WAS→WSH, GSW→GS, UTA→UTAH, SAS→SA applied). **22/22 MATCH**
  on `date` / `home` / `away` / `status=Final` / home+away final `score` /
  `tip_utc` (tolerance 60 s; the aggregate declares tip delta 0.0 s on all 22
  and my parses agree to the second).
- Aggregate census re-measured: BDL per-date returned counts equal hoopR
  completed-game counts on **11/11 probed dates** (12,14,9,8,10,10,7,14,11,14,10).
- Request discipline: final run **11 requests ≤ 25**; aggregate
  `budget.max_requests=12, min_interval_s=13.0, max_games_per_date=2`;
  session total **36 = 16+9+11** documented in both the cross-check doc and
  manifest; **throttle re-measured from resp file mtimes: gaps 13.4–15.5 s
  (min 13.4 s ≥ 13 s)**.
- **No key value anywhere** (grep over `lanes/A_DATA/` + all 11 redacted
  files): zero token-like strings — all pattern hits are sha256/commit digests
  or prose stating the key is never stored; `bdl_adapter.py` fail-closed
  (env → Keychain, raises `BDLKeyUnavailable` before any request, errors name
  the source never the value); the aggregate records URL patterns only, 0
  auth params.

### Check 4 — PIT law coherence with the corrected 14-game hole: **PASS**

- Spec §5 states the hole and the tolerance law ("A consumer must tolerate
  these missing-pbp games by game-id list — never silently impute"); PIT §3
  requires feature code to close windows strictly before `tip_utc` and
  tolerate the same 14 ids; `handoff_A_r1.json` impact statement binds the
  hole to pbp-derived features on those games only.
- Spread census (spec §6) still measured **on unique pbp `game_id`**, 100%
  non-null per season 2016–2026, with the **UNVERIFIED_PIT** caveat carried
  verbatim (line rides in the FINAL payload; PIT §4 keeps spread ineligible
  as a mechanism, diagnostic-only); `handoff_A_r1.json` known_limitations
  states the 14 ids carry NO spread rows while the §6 census remains 100% on
  pbp-attached games — coherent, no contradiction.
- Injury/roster **NOT_RUN_PIT unchanged** (verdicts table row 5 + §5 with the
  candidate failure table and the successor spot-sample bar).
- Cup-final discriminator and separate-reporting law untouched; tolerate-
  never-impute law present in all three post-fix documents.

### Check 5 — Scope discipline: **PASS**

- `git diff --name-status 4d387a2a..2cd4674e`: exactly **6 files, all under
  `lanes/A_DATA/`** (4 M: DOWNLOAD_MANIFEST / GAME_UNIVERSE_SPEC / PIT_AUDIT /
  handoff_A; 2 A: ERRATUM_PBP_GAP_R1 / handoff_A_r1). **Nothing else** —
  lanes/B/C and research/control untouched by the fix commit.
- Working tree: only `research/control/NBA-WINPROB-NG-PREP-V1/event_log.jsonl`
  modified (the controller's own log — its REMEDIATION_R1_LANDED entry is
  visible in the tail) + untracked `lanes/D_VERIFY/**` (this lane's write
  scope). No foreign worktree touched; branch has no upstream.
- Credential scan of the full diff body: **0 hits**.
- **0 scored outcomes still true**: grep over `lanes/**/*.py` for
  sklearn/scipy/statsmodels imports, `.fit(`, `.predict(`, `log_loss`,
  `brier`, `roc_auc`, `accuracy_score` → **0 hits** (only executables remain
  lane A's schema/coverage counter and the BDL cross-check; this lane's new
  script is coverage counting only).
- Landed-byte integrity of the fix: all 5 `handoff_A_r1.json outputs[]`
  sha256 **re-hashed MATCH** on disk (spec, PIT audit, manifest, handoff_A,
  erratum).

### Check 6 — Registry coherence (read-only): **PASS** (1 expected-pending)

- Row `NBA-WINPROB-NG-PREP-V1`: `lifecycle ACTIVE_LIGHT`, `phase REGISTERED`,
  `budget {used: 0, max: 0}`, `go_phrase: ""` with `go_phrase_state:
  "NOT_REGISTERED (P-8 …)"` — **no GO phrase registered or consumed**;
  `s1: SEALED_UNTOUCHED`; `branch` + `integration_worktree` match measured
  values; `workers: 0`, `active_heavy: false`.
- `head: 0000000000000000000000000000000000000000` vs measured branch HEAD
  `2cd4674e…` — **expected-pending**: the controller updates the registry
  head post-verification (dispatch pre-declared; `updated_at_utc` is still the
  G0 bootstrap instant). Recorded, not a defect.

## 2. Overall

**VERIFICATION_PASS** — the D1 remediation is correct everywhere it needed to
be (spec §5, PIT audit §3, handoff_A.json, manifest D3/D4 lines, exhibition
enumeration D5), every corrected figure re-measures exactly (14-game gap
game-for-game; 248,642,536 B; 19/19 exhibitions; 36 = 16+9+11), the core laws
still reconcile from bytes (14,254 = 14,168 + 19 + 67 zero residue; per-season
composition; BDL 22/22 with throttle and no key material), PIT coherence holds,
scope discipline held (only `lanes/A_DATA/**` in the fix commit), and the
registry remains 0/0 with no GO. No new defects found.

## 3. Defects table (post-R1 status)

| ID | Severity | R1 status | Evidence |
|---|---|---|---|
| D1 | MEDIUM | **REMEDIATED — re-verified** | 14-game gap re-measured game-for-game; corrected text in spec §5 / PIT §3 / handoff_A.json; zero stale assertions in lanes/A_DATA (grep adjudicated per-hit). |
| D3 | LOW | **REMEDIATED — re-verified** | Manifest total 248,642,536 = my re-sum of the 10 per-file sizes; all 10 sha256 MATCH. |
| D4 | LOW | **REMEDIATED — re-verified** | Manifest + cross-check doc both 36 (16+9+11); no "26 requests" stale hits. |
| D5 | LOW | **REMEDIATED — re-verified** | Spec §5 + handoff_A.json + erratum all 19/19; my measurement 19/19. |
| D2 | LOW | OPEN (outside R1 scope by owner order) | `measure_schedule_corpus.{py,json}` still carries the weaker dedupe law (kept_total 14,184 vs spec-law 14,168); round-0 adjudication (spec law authoritative) stands; controller/successor must annotate it as a superseded intermediate and never re-derive numbers from it. |
| D6 | INFO | OPEN (advice) | Spec §2 "6,632 ET-home rows" subset wording unchanged; round-0 superset re-verification (7,104, 0 mismatches) stands. |
| D7 | INFO | OPEN (advice) | Lane C selection folds still named S1–S4; successor should rename (SEL-1..4) pre-look. |

Remaining open items are all pre-existing round-0 findings outside the R1
owner order (D2 LOW, D6/D7 INFO) plus the expected-pending registry head
update — none blocks this cycle's PREP verdict or the successor registration.

## 4. Artifacts of this re-verification

- `lanes/D_VERIFY/delta_reverify_r1.py` — recompute script (schema/coverage
  counting only; 21/21 gates PASS, exit 0).
- `lanes/D_VERIFY/delta_reverify_r1_evidence.json` — full machine-readable
  evidence (gap rows, law per-season, pbp dtypes/sizes/hashes, BDL per-game
  verdicts, throttle gaps, gates).
- `lanes/D_VERIFY/DELTA_REVERIFY_R1.md` — this report.
- `lanes/D_VERIFY/handoff_D_r1.json` — structured handoff
  (zcode_orch_v3_handoff@1).

## 5. Verdict

**VERIFICATION_PASS**
