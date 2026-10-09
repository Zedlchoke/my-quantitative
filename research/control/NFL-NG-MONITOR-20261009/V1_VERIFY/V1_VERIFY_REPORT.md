# V1_VERIFY_REPORT — independent verification of NFL-NG-MONITOR-20261009

**Verifier role:** independent fresh-context verifier (A7-style), owner-directed
DESCRIPTIVE monitoring round for cycle `NFL-WINPROB-NG-SCORED-V1`.
**Verify time:** 2026-10-09 ~11:20–11:40Z. **Verify base sha:**
`d984f9240bc96804dc3a2e80e09ed1cc653c3579` (root checkout, branch `main`,
full HEAD verified at start; unchanged at end).
**Object under verification:** commit `8a5543e66c0380edcb0a663ba26251d885b82453`
(monitor artifacts) + monitor data dir
`/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/`.

**Heavy lock:** `researchctl.py locks inspect` → verdict **FREE_PROVEN**
(no registry row, lock file not flocked). Light verification lawful; no lock
taken by this verifier. Last worker released 2026-10-09T10:11:08Z (WSL cycle,
unrelated — matches the monitor report's claim).

## OVERALL VERDICT: **VERIFY_PASS**

All six dispatched items recompute from bytes. 49/49 independent checks PASS,
zero fails. No refutation found. Recomputed numbers below.

Method: fresh-context; verifier wrote its own code
(`V1_VERIFY_RECOMPUTE.py`, not derived from `monitor_analysis.py`); strictly
read-only on every cycle path; outputs confined to `V1_VERIFY/`.

---

## Item 1 — Ledger untouched + faithful census: PASS

Ledger:
`/Users/hoangminhlong/.my-quantitative-data/nfl-ng-scored-v1/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl`

- sha256 recomputed now: `7d9af2867b480f08c7b195398e15f927fd45172e25899130125a7e8f1a922c90`
  — equals the pre-registered/prefix value. PASS.
- Line count: **129** (129 JSON rows parse). PASS.
- Census recount: **43 distinct game_ids, each with exactly rows {B0, B1_STAR,
  C3}** (rows-per-game multiset = {3}); arms set exactly {B0, B1_STAR, C3}.
  PASS.
- Weeks from game_id: W05/W06/W07 = **15/14/14 games**; per-arm-per-week also
  15/14/14 for each of the three arms (B0_w05=15, B0_w06=14, B0_w07=14, same
  for B1_STAR and C3). PASS.
- Conformance: all 129 rows `schema_version=nfl_ng_ledger@1`,
  `cycle_id=NFL-WINPROB-NG-SCORED-V1`, season 2026, `game_type=REG`,
  `recorded_by=EXEC-POST-GO-EXECUTOR`. Kickoff range
  `2026-10-09T00:15:00Z … 2026-10-27T00:15:00Z` (matches report). PASS.
- Extra (verifier-added): every row `recorded_at_utc < kickoff_utc`
  (pre-match recording identity holds 129/129). PASS.
- Extra (verifier-added): full hash chain walk — genesis link
  `GENESIS:9978a950cf…` equals the registration genesis
  `ledger_genesis_anchor=9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e`;
  all 129 `prev_row_hash` links OK; all 129 `row_hash` recomputations match
  (row minus `row_hash`, JSON `sort_keys=False, separators=(',',':')`).
  PASS.
- READ-ONLY claim: ledger mtime **2026-10-06T17:03:39.335537Z** — predates the
  monitor window (2026-10-09T10:58Z) by ~3 days; sha also unchanged from the
  pre-registered value. Both conditions hold. PASS.

## Item 2 — Snapshot provenance: PASS

Monitor data dir `…/nfl-ng-monitor-20261009/`:

- `games.csv` sha256 recomputed:
  `9c925388e875b6e90c4ba21e7029e0a0ff44648d4528dcab080d1c11dbe560e1` — matches
  report and `provenance_monitor_20261009.json`. PASS.
- `timestamp.json` sha256 recomputed:
  `0081235036d5199df02b4c11ef12515875f63d6e23fe090cd6038236abee47a2` — matches
  report and provenance JSON. PASS.
- Retrieval timestamps recorded: `retrieval_utc=2026-10-09T10:58:11Z` in
  provenance JSON and report; `timestamp.json` content
  `{"last_updated": "2026-10-09 06:46:37 EDT"}` = 10:46:37Z (~12 min pre-retrieval,
  fresh). Data-dir file mtimes fit the declared window (games.csv 10:58:10Z,
  timestamp.json 10:58:11Z, analysis 10:59:54Z, outputs 11:01:46Z). PASS.
- `provenance_monitor_20261009.json.ledger_sha256` equals the recomputed
  ledger sha. PASS.

## Item 3 — FINAL/PENDING split recompute: PASS

Own join code over the sha-verified snapshot (7,548 rows) × the 43 recorded
game_ids:

- Join failures: **0** (all 43 game_ids present in the snapshot). PASS.
- FINAL: **exactly 1** — `2026_05_TB_DAL`, snapshot `away_score=24`,
  `home_score=16` (TB 24 @ DAL 16), derived `result='-8'`, `total='40'`,
  `overtime='0'` all populated (STRICT rule satisfied; no tie). PASS.
- PENDING: **42**, each with BOTH score fields empty strings; zero
  partial/mixed score states (`NOT_RUN_STATUS_AMBIGUOUS` legitimately 0).
  PASS.
- Extra (verifier-added): ledger home/away identity equals snapshot home/away
  for all 43 games (not just the FINAL one). PASS.

Report's n=1 FINAL set matches the recompute exactly.

## Item 4 — Per-arm descriptor recompute on the FINAL game: PASS

Recomputed from the ledger's recorded `p_home` strings with outcome
`y=0` (home DAL lost 16–24; away won):

| Arm | ledger p_home | LL recomputed | LL report (6dp) | drift | Brier recomputed | Brier report (6dp) | drift | acc |
|---|---|---|---|---|---|---|---|---|
| B0 | 0.571399 | 0.8472288627675941 | 0.847229 | 1.4e-07 | 0.326496817201 | 0.326497 | 1.8e-07 | 0.0 |
| B1_STAR | 0.544343 | 0.7860149454892909 | 0.786015 | 5.5e-08 | 0.296309301649 | 0.296309 | 3.0e-07 | 0.0 |
| C3 | 0.529183 | 0.7532857954968586 | 0.753286 | 2.1e-07 | 0.280034647489 | 0.280035 | 3.5e-07 | 0.0 |

- All drifts ≤ 3.5e-07, i.e. pure 6-decimal display rounding; well inside the
  ~1e-6 tolerance. Full-precision values are **byte-identical** (0.0e+00) to
  `monitor_results_20261009.json`. PASS.
- All arms p_home > 0.5 on DAL; away won; **argmax accuracy 0.0 for all three
  arms**. PASS.
- Ordering sanity: LL monotone increasing in p_home on this observation
  (C3 0.753286 < B1_STAR 0.786015 < B0 0.847229), as the report describes.
  PASS.

Verifier transparency note: the verifier's own first implementation initially
produced LL≈0.559668/Brier≈0.183699 for B0 etc. — that was a sign flip in the
verifier's outcome indicator (computed y=1 home-win), not a monitor error.
After correcting to y=0 (the actual away-win outcome), every monitor number
reproduces exactly. This also confirms the report used the correct outcome
direction: the home-win mislabel would have produced a completely different
table.

## Item 5 — Language/boundary audit + write detection: PASS

Language (committed `MONITORING_REPORT_20261009.md`):

- `DESCRIPTIVE_MONITORING` label present (line 3). PASS.
- Explicit disclosures present: "consumes **NO scored-cell budget** of any
  cycle and modifies **NO ledger**" (L10-11); "ledger was opened READ-ONLY"
  (L11); calibration-vocabulary-only (L12-16); "n is tiny (1 game); nothing
  here is evidence of skill or of edge" (L14-15); "zero inferential weight…
  support no comparison conclusion, no ranking, and no edge claim of any
  kind" (L135-136). PASS.
- Grep audit for `edge|bet*|wager|profit|odds|stake|ROI|EV|expected value`:
  every hit is inside a negation/disclosure context; **zero affirmative
  edge/betting/profitability claims**. PASS.

Write detection (all read-only):

- Ledger: sha unchanged (Item 1) + mtime 2026-10-06T17:03:39Z. Nothing written.
- NG cadence fire_log `…/nfl-ng-scored-v1/cadence/fire_log.jsonl`: mtime
  2026-10-08T17:01:05Z (predates monitor window; sha256
  `d7f81c15edc391ff…` prefix recorded for continuity). Not touched.
- Full recursive mtime walk of `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-scored-v1/`:
  **zero files with mtime ≥ 2026-10-09T10:55Z** — the monitor created/modified
  nothing in the NG cycle data dir (its own writes are confined to
  `…/nfl-ng-monitor-20261009/`).
- NG cycle worktree: registry row pins
  `orca/nfl-winprob-ng-scored-v1-integration` at
  `f459dd6eb78ddddbaf0d2e27de52991907eae25b`; branch still at that sha
  (unchanged). The `integration/` worktree directory was already removed
  (parent dir `.worktrees/nfl-winprob-ng-scored-v1/` empty since
  2026-10-09 04:15Z, i.e. ~6.7h BEFORE the monitor window) — nothing for the
  monitor to touch and nothing touched.
- Lock: FREE_PROVEN at verify time; monitor report's own claim
  ("FREE_PROVEN… Last worker released 2026-10-09T10:11:08Z WSL, unrelated")
  matches the lock history this verifier observed. No worker was touched.

## Item 6 — Repo isolation: PASS

- `git show --stat 8a5543e6`: exactly **3 files, +424/-0**, all under
  `research/control/NFL-NG-MONITOR-20261009/`
  (`MONITORING_REPORT_20261009.md`, `joined_monitor_20261009.csv`,
  `monitor_analysis.py`). PASS.
- Monitor data dir is outside the repo:
  `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/` is not
  under `/Users/hoangminhlong/my-quantitative/`. (The untracked repo-root
  `.my-quantitative-data/` entry is a different, owner-created scratch dir —
  contains only a 0-byte `nfl-ng-scored-v1/fix_r4/final_g2_check.gate_log.jsonl`
  dated Oct 6.) PASS.
- Working tree at verify time: `plans/ACTIVE_CYCLES.json`,
  `plans/CYCLE_REGISTRY.events.jsonl`, `plans/CYCLE_REGISTRY.json` modified
  (mtime 11:06:53Z) — **attributed to a post-commit A1 governance write, not
  the monitor**: the registry's own `events.jsonl` records
  `writer="A1: XAUUSD-SHADOW-V1 owner-directed removal closeout"`,
  write_token `update:WSL-WINPROB-SCORED-PREP-V1:A7-R3 readiness verdict
  READY; head sync after verifier comm`, at `2026-10-09T11:06:53Z`, i.e.
  ~4 minutes AFTER the monitor's commit (11:02:49Z); the diff touches only the
  WSL-WINPROB-SCORED-PREP-V1 registry row (head/phase) + generated projection
  + events. The monitor commit itself contains no plans/ changes. No evidence
  implicates the monitor; at commit time (11:02:49Z) the plans/ files were
  still clean (mtime 11:06:53Z). Plus untracked: owner's
  `.my-quantitative-data/` and this verifier's own `V1_VERIFY/`. PASS with
  attribution note.

---

## Findings (non-blocking observations)

1. **Anchor location nuance:** the report says the ledger sha "matches the
   `7d9af286…` prefix registered for the cycle", but `7d9af286` appears
   nowhere in `plans/` (registry included). The actual continuity anchor is
   `research/control/VERIFY_20261007_NFL_CADENCE_V2/verify_report.md`
   (recorded 2026-10-07 as "Ledger file sha256 recorded for continuity"),
   which does predate the monitor run. The claim is materially true
   (independent pre-existing anchor exists); the word "registered" is loose
   wording, not a fabrication.
2. **Cosmetic timestamp rounding:** report header says "report written
   ~11:05Z"; actual report file mtime 11:01:46Z, commit 11:02:49Z. Immaterial.
3. **Verifier's own first-pass bug (disclosed for reproducibility):** initial
   outcome-indicator flip in verifier code produced a refutation-shaped
   mismatch on Item 4; root cause was verifier-side, fixed, and the corrected
   recompute reproduces the monitor byte-for-byte. The monitor's arithmetic
   is correct under the true (away-win) outcome.
4. NG worktree `integration/` dir absent (removed ~04:15Z, before the monitor
   window) while the registry row still names it — pre-existing state, outside
   this monitor's scope, no action required for this round.

## Gates

- Independent recompute: **PASS** (49/49 checks; run log
  `V1_VERIFY_RUN_LOG.txt`, machine results `V1_VERIFY_RESULTS.json`).
- Heavy lock: **FREE_PROVEN** (no worker disturbed).
- Verifier writes: confined to
  `research/control/NFL-NG-MONITOR-20261009/V1_VERIFY/` (untracked; controller
  commits). No cycle path modified. No commit made by the verifier.

## Deliverables (this verify round)

- `V1_VERIFY_REPORT.md` (this file)
- `V1_VERIFY_HANDOFF.json` (`zcode_orch_v3_handoff@1`, task_id
  `V1_VERIFY_MONITOR`, commit_sha null — controller commits)
- `V1_VERIFY_RECOMPUTE.py` (sha256 ce80efe021afb97cd42349c6362e9a6a0a7310c4038c1e192b77b7c7beea1f09)
- `V1_VERIFY_RUN_LOG.txt` (sha256 d198dc29a07f04460c59236eb1ba5cfd2f4663916fc3be4ad757cba16b36c148)
- `V1_VERIFY_RESULTS.json` (sha256 454ef3d4192e6df78b33893df8b5a8bedb811833a369565a8f65a928b106646f)
