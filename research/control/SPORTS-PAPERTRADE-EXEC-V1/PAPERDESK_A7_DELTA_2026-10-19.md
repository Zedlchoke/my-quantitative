# PAPERDESK A7 — DELTA VERIFICATION (round-2 hardening), 2026-10-19

- Verifier: A7, independent, fresh context.
- DELTA commit: `a5e047835174fde6e19cb087deb1152f1036fa5d` (parent `afed4a4e`),
  branch `orca/spt-exec-v1-integration`, worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`.
- Measured `git rev-parse HEAD` == `a5e04783…` == registry head. Worktree also
  carries two UNCOMMITTED documentation-only edits (`AMENDMENT_MACOS_APP_UI_V1.md`
  round-2 section, `TOOLCHAIN_BLOCKER_NOTE.md` scope correction) — no code impact.

# VERDICT: VERIFY_PASS_WITH_FINDINGS

0 CRIT / 0 HIGH / 0 MEDIUM. 1 LOW (cosmetic comment path), 2 INFO
(boundary nuance; stale registry mirror in worktree). All P0/P1 claims verified
in code; all runnable batteries re-run and pass; real-plane journal evidence
confirms the fail-closed paths were exercised, not just tested.

## Per-claim table

| # | Claim (dispatch mapping) | Code evidence | Re-run / real-plane evidence | Result |
|---|--------------------------|---------------|------------------------------|--------|
| P0-1a | processIdentity = two ps calls (`lstart=`, `command=`) | runner.js:102–114 | — | CONFIRMED |
| P0-1b | identityIsOurs: command has `ops_service`; data-root form requires our dataRoot + sandbox-mode match; launchd form ONLY when `!​--data-root` AND launchdOwned AND `launchdState().pid === pid` AND `launchdPlistBindsUs()` | runner.js:116–138 | journal `IDENTITY_VIA_LAUNCHD_PLIST` ×3 (13:25:01Z, 13:38:24Z, 14:08:09Z) | CONFIRMED |
| P0-1c | launchdPlistBindsUs: plutil argv tail `-m research.papertrade_exec.ops_service` + WorkingDirectory match | runner.js:143–165 | — | CONFIRMED |
| P0-1d | ownedRunnerAlive refuses bound-lstart mismatch → `PID_REUSE_REFUSED` + detach | runner.js:216–226 | battery tests 5–7 (pid-reuse) | CONFIRMED |
| P0-1e | bootout failure → `LAUNCHD_BOOTOUT_FAILED`, stop aborted, state restored `attached`; async grace loop (10×500 ms) | runner.js:381–393 | journal `LAUNCHD_BOOTOUT_FAILED` @13:25:01Z (real fail-closed exercise, followed by QUIT_BLOCKED); battery test 12–13 | CONFIRMED |
| P0-1f | ESRCH guards on kill; gracefulStopRunner returns `clean && lock_free` | runner.js:398–400, 408, 441 | journal `GRACEFUL_STOP_END clean:true lock_free:true` ×6 | CONFIRMED |
| P0-1g | every signal path behind identity (only 3 `process.kill` sites: signal-0 probe, SIGTERM, SIGKILL — the two real signals reached only after `ownedRunnerAlive()` / re-verified identity) | grep: runner.js:68/398/408; no kill sites in main.js | battery 13/13 incl. fail-closed refusal tests | CONFIRMED |
| P0-1h | fail-closed Quit: `STOP_REFUSED_IDENTITY` + `QUIT_BLOCKED`, `STOP_REFUSED_LOCK_HELD_UNEXPLAINED`; app stays open | runner.js:357–370, main.js:277–287 | journal: STOP_REFUSED_IDENTITY ×2 (12:59:02Z, 13:11:45Z), QUIT_BLOCKED ×4, STOP_REFUSED_LOCK_HELD_UNEXPLAINED (13:49:24Z) | CONFIRMED |
| P0-1r | `node test_lifecycle_safety.js` → 13/13 | — | re-run 2026-10-19: **13/13 pass** | CONFIRMED |
| P0-2a | deadlineFor: SOCCER/WSL kickoff−6h, NBA/WNBA T0−6h10m, mirror of pinned constants, display-only | ai.js:34–45; pinned `research/papertrade_exec/__init__.py:35–36` (BATCH=6h10m, SOCCER=6h) — values match | ai battery deadline-law tests | CONFIRMED (comment path typo, F-1) |
| P0-2b | maybeAutoReview: window [deadline−15m, deadline], idempotent per (matchID, deadlineUTC), too-late → `TIMEOUT_LATE_INVALID`, disabled no-op | ai.js:274–333 (windowState + guards 302–322) | ai battery automation tests (skipped/outside window, auto-run once, idempotent no-op, TIMEOUT_LATE_INVALID visible+idempotent) | CONFIRMED (inclusive boundary nuance, F-2) |
| P0-2c | captureEvidence: system-side only — pm.lastSnapshotSha('gamma_events') + fetchBook sha; AIWebConnector allow-list + ≤5 req budget | ai.js:79–121, 205–271 | ai battery evidence-law tests | CONFIRMED |
| P0-2d | zaiCall/parseZAIResponse fail-closed: HTTP non-200 → `API_ERROR_FAIL_CLOSED`; null/missing choices → `API_ERROR_FAIL_CLOSED` | ai.js:486–491 (non-200), 521–528 (null choices) | ai battery: null-choices + non-JSON → fail-closed | CONFIRMED |
| P0-2e | model-claimed sources `verified:false, claimed_by_model:true`, count toward nothing; zero verified → forced ABSTAIN + NOT_RUN_EVIDENCE uncertainty; rationale ≤400 chars | ai.js:549, 555–569 | ai battery: "system sources kept, model-claimed recorded-but-discarded", "zero VERIFIED → forced ABSTAIN" | CONFIRMED |
| P0-2r | `node test_ai_seam.js /tmp/a7delta_ai` → 26/26 | — | re-run 2026-10-19: **26/26 pass** | CONFIRMED |
| P0-2i | isolation: no AI symbols in python runner | `grep -rn "ai_review\|AIReview" research/papertrade_exec/*.py` → empty | — | CONFIRMED |
| P0-3a | reconcile_missed_windows: scope today..+2 only, INCIDENTS only, idempotent via missed_windows.json, no ledger path | ops_service.py:123–171 (dates=range(3); only writes are `self.incident` → incidents.jsonl + state file; grep proves no ledger append in body) | — | CONFIRMED |
| P0-3b | wired at SERVICE_START with RECONCILE_ERROR guard | ops_service.py:605–611 | — | CONFIRMED |
| P0-3r | `pytest tests/papertrade_exec/test_ui_control_seam.py -q` → 8 passed | — | re-run: **8 passed** | CONFIRMED |
| P0-3c | full-suite baseline: 16 pre-existing failures unchanged | — | re-run: **16 failed, 94 passed**; composition 15×test_exec_battery + 1×test_b1r_fail_closed — name-set matches documented baseline (WSL_BET_PAPER_VERIFY.md §F "16 failed … byte-identical 16 names"); visible assertion `BLOCKED_SOCCER_ENTRY: Lane C replay entry absent` (adapters.py:817–818 expects sibling `research/papertrade_soccer/replay.py`) = the documented sibling-entry drift root cause; "sibling-entry-drift failures" phrasing in B1R_FAIL_CLOSED_REHEARSAL.json | CONFIRMED |
| P1-1a | PM snapshots unique content-addressed names (stamp + seq + kind + sha12) | market.js:110–119 | — | CONFIRMED |
| P1-1b | journalFailures counter on write failure, surfaced in uiState + renderer | market.js:90,123–127; main.js:159; renderer/app.js:570–571 | — | CONFIRMED |
| P1-1c | Health text: PM display/AI-evidence only until cutover GO consumed | renderer/app.js:573, 614–615 ("…unchanged per pinned lanes until the Polymarket cutover…", "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER — REGISTERED_NOT_CONSUMED (not typed here)") | — | CONFIRMED |
| P1-2a | registry row: head == a5e04783, phase contains GO_CONSUMED, cutover phrase REGISTERED_NOT_CONSUMED untouched | root plans/CYCLE_REGISTRY.json: head `a5e04783…`, updated 2026-10-19T14:21:21Z, phase contains GO_CONSUMED, go_phrase_state REGISTERED_NOT_CONSUMED | — | CONFIRMED (worktree mirror stale, F-3) |
| P1-2b | GO_TOKEN.json still `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` | control/GO_TOKEN.json unchanged | — | CONFIRMED |
| P1-2c | git branch HEAD == registry head | rev-parse = a5e04783, branch orca/spt-exec-v1-integration | — | CONFIRMED |
| C-6 | ledger untouched: pinned verifier True/42; census unchanged; mtime ≤ 2026-10-18 | pinned `PaperLedger.verify_chain()` (sports-papertrade-v1 core) → **True, 42 rows, no errors**; census GENESIS 1 / FORECAST 13 / MARKET_QUOTE 11 / DECISION 13 / SETTLEMENT 4; `ls -l` mtime **Oct 18 07:10** | — | CONFIRMED |
| C-7 | pause observation on real plane | incidents.jsonl:3267 `DECISIONS_PAUSED_BY_UI` reason `real-plane-pause-observation-A7-F1` @12:57:37Z; later `DECISIONS_RESUMED_BY_UI` rows (12:58:52Z … 14:14:53Z); recorded in paperdesk_evidence_2026-10-19/real_plane_pause_observation.txt; seam battery (8/8) covers the pause path | — | CONFIRMED |
| C-8 | end state clean | `launchctl print gui/501/com.myquant.sptexec.ops` → "Could not find service"; `pgrep -f research.papertrade_exec.ops_service` empty; opslock probe ops/service.lock → **FREE**; `pgrep -fil PaperDesk` empty | — | CONFIRMED |
| C-9 | rebuilt .app valid + carries guards | build/PaperDesk-darwin-arm64/PaperDesk.app exists; `codesign --verify --deep --strict` → OK; packaged main/runner.js contains PID_REUSE_REFUSED + IDENTITY_VIA_LAUNCHD_PLIST; packaged main/ai.js contains claimed_by_model ×5 + NOT_RUN_EVIDENCE ×3; packaged files byte-identical to worktree sources (diff -q) | — | CONFIRMED |

## Commands + results (re-run by this verifier, 2026-10-19)

```
git -C <wt> rev-parse HEAD            -> a5e047835174fde6e19cb087deb1152f1036fa5d (branch orca/spt-exec-v1-integration)
cd apps/paperdesk && node test_lifecycle_safety.js      -> lifecycle safety: 13/13 pass
node test_ai_seam.js /tmp/a7delta_ai                    -> ai seam: 26/26 pass
.venv/bin/python -m pytest tests/papertrade_exec/test_ui_control_seam.py -q
                                                        -> 8 passed
.venv/bin/python -m pytest tests/papertrade_exec/ -q    -> 16 failed, 94 passed (baseline, see P0-3c)
pinned core: PaperLedger(real ledger).verify_chain()    -> True | rows: 42 | errs: []
helpers/opslock.py probe <dataRoot>/ops/service.lock    -> FREE
launchctl print gui/501/com.myquant.sptexec.ops         -> Could not find service (absent)
pgrep -f research.papertrade_exec.ops_service           -> (empty)
pgrep -fil PaperDesk                                    -> (empty)
codesign --verify --deep --strict <PaperDesk.app>       -> OK
grep ai_review|AIReview research/papertrade_exec/*.py   -> no matches
cycle doctor --json                                     -> 159 findings; HEAD_MISMATCH ×5, all OTHER cycles
```

NOT RUN by instruction (would mutate lifecycle): `e2e_lifecycle.sh`,
`e2e_evidence.sh` — their effect was verified via the RECORDED journal evidence
above (IDENTITY_VIA_LAUNCHD_PLIST, GRACEFUL_STOP_BEGIN/END launchd rows with
lstart, LAUNCHD_BOOTOUT status 0, LAUNCHD_BOOTOUT_FAILED fail-closed,
STOP_REFUSED_*, QUIT_BLOCKED) and the committed evidence files.

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| F-1 | LOW (cosmetic) | ai.js:35 comment cites `research/papertrade/__init__.py` for the pinned anchor constants; the actual pinned module is `research/papertrade_exec/__init__.py` (BATCH_LEAD_SECONDS=6h10m, SOCCER_LEAD_SECONDS=6h). Mirror VALUES are correct; only the citation path is wrong. |
| F-2 | INFO | Automation window is inclusive of the deadline instant (`windowState`: too-late strictly `now > dl`), i.e. [deadline−15m, deadline] rather than the commit message's [deadline−15m, deadline). No law impact: any completion after the deadline is still forced `TIMEOUT_LATE_INVALID` (ai.js:399–404). |
| F-3 | INFO (bookkeeping) | The worktree's `plans/CYCLE_REGISTRY.json` mirror is stale (head `9a18a4f2`, updated_at 2026-10-10) while the authoritative root registry carries head `a5e04783` / updated 2026-10-19T14:21:21Z. Root is the writable authority per AGENTS.md; mirror catches up on the next CAS sync. No action taken by this verifier. |

## Residual drift — OUT OF SCOPE (other lanes)

`cycle doctor` reports 5 HEAD_MISMATCH (all LOW) on OTHER cycles:
FUTURES-ES-PB1-V1, SPORTS-PAPERTRADE-V1, NBA-WINPROB-HCAL1-PROSPECTIVE-PREP-V1,
SOL-MEME-SHADOW-PILOT-V1, PM-PAPER-CAPTURE-PREP-V1 — plus WORKTREE_MISSING /
STATE_MISSING entries for old closed cycles (CRYPTO-V17, FOREX-FREE-V8/V9,
STOCKS-FREE-V12, MARKET-DATA-PLANE-V1/V2/V2R1, ZCODE-ORCHESTRATION-V3).
SPORTS-PAPERTRADE-EXEC-V1 is NOT among the mismatches. These belong to other
lanes and are not touched or judged by this audit.

## Boundaries observed

Nothing pushed; nothing repaired; no launchd/runner start or stop; no stash;
ledger, registry, GO token untouched; e2e lifecycle/evidence scripts not
executed (recorded evidence verified instead). Two pre-existing uncommitted
doc edits in the worktree were observed and left as-is.
