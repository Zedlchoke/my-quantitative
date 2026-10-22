# PAPERDESK A7 — DELTA-8 INDEPENDENT VERIFICATION (round-10 dispatch, 2026-10-20)

**VERDICT: VERIFY_PASS_WITH_FINDINGS** — 0 CRIT / 0 HIGH / 1 MED / 2 LOW / 2 INFO.

Every load-bearing end-state re-measures clean: HEAD d5854aea == registry head;
main ledger pinned verifier **True / 59 rows** with the 11 NBA FORECAST rows
present (two-way, model_version_sha == pinned nba26 predict bytes); NBA engine
worktree restored at lane HEAD 82542aa8 with both pinned files byte-exact vs
pins.json; WSL provenance chain True with 14 post-2026-10-20 FORECAST rows
(M43–M49 + NEW M50–M56 from the D-1 batch); launchd `com.myquant.wslprov.d1`
loaded with executable wrapper; all four node AI batteries pass (17/17, 43/43,
27/27, 13/13); GO/cutover/AI-authority states exactly as required; live
service HTTP 200, chain ok, **59 rows** (48→59), owner-run app + runner
untouched.

Two dispatch claims are STALE and do not reproduce as written (F-1, F-2):
the full pytest battery is **11 failed / 114 passed**, not 16/105+ — the 5
tests that stopped failing are exactly the NBA adapter/engine set explained
by round-9 commit 843fb5a3 (worktree restoration closed BLOCKED_NBA_ENTRY at
the source); and `58edc089…` is the obsolete 48-row ledger hash — at 59 rows
the measured sha is `1486e85e…`. Both discrepancies are improvements or
bookkeeping, not regressions; neither invalidates recorded evidence. One
untracked unreferenced file noted (F-3).

Verifier: A7 fresh-context subagent. Read-only except this artifact; nothing
launched, killed, or repaired; ledger untouched. Python:
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

---

## 1. Claim table

| # | Claim | Result | Evidence (measured this pass) |
|---|-------|--------|-------------------------------|
| 1a | HEAD == d5854aea (or later) | **PASS** | `git rev-parse HEAD` = `d5854aeafebebfefa3966552b46e4ff4427e5c45`, branch `orca/spt-exec-v1-integration` |
| 1b | Tree clean | **PARTIAL** | Only `?? apps/paperdesk/main/pm_stake_law.js` untracked; zero tracked modifications. The file is referenced by NO js under `apps/paperdesk` and was never committed (see F-3) |
| 2a | Main ledger pinned verifier True / 59 rows | **PASS** | `execute.load_pinned_core(roots={})` + `core.ledger.PaperLedger(~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl).load().verify_chain()` → **(True, [])**, 59 rows = 1 GENESIS + 24 FORECAST (4 WNBA + 2 SOCCER + 7 WSL + 11 NBA) + 11 MARKET_QUOTE + 13 DECISION + 10 SETTLEMENT (48 + 11 NBA) |
| 2b | Ledger sha256 starts `58edc089` | **FAIL (stale claim)** | Measured `1486e85e4d28b50714b4418988e3c4fdbf2718734e2d925fd6598d0a5454f563`. `58edc08965b73d…` is the **48-row pre-NBA** hash (delta-6 §ledger, round-8 commit "main ledger sha unchanged 58edc089"). A 59-row file cannot carry the 48-row digest — the dispatch claim is internally inconsistent with its own "59 rows" (see F-2) |
| 3a | NBA worktree exists at 82542aa8 | **PASS** | `/Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-prospective-prep-v1/integration` → HEAD `82542aa8e97206b88f7eb777f4461b09054e9b09` |
| 3b | loader.py / predict.py exist, sha == pins.json | **PASS** | loader `2679be80f1fb7f7d9862f76b65e546708aac3df6654fa7e8d866aedecd6461c8`, predict `57f0c810f8cd1a12d78bcb68881ca49b6d8bdb16a4a0f61a11dfcc7987c6d81c` — both byte-equal to `research/papertrade_exec/pins.json` `nba26` block |
| 4 | Main ledger has 11 NBA FORECAST rows | **PASS** | 11 rows, match_ids 401909091/401909834–401909842, kickoffs 2026-10-21T23:00Z … 2026-10-22T02:30Z, all `recorded_at_utc=2026-10-20T10:38:42Z`, two-way p {HOME,AWAY} (B1* law), `model_version_sha=nba26_predict@57f0c810f8cd` == pinned predict bytes |
| 5a | WSL provenance chain verifies | **PASS** | pinned-core `verify_chain()` on `~/.my-quantitative-data/wsl-winprob-paper-prep-v1/ledger/paper_ledger.jsonl` → **(True, [])**, 29 rows (1 GENESIS + 21 FORECAST + 7 DECISION; delta-7 saw 22 rows) |
| 5b | FORECAST rows kickoff > 2026-10-20 → ≥ 7 | **PASS** | **14** rows: M43–M49 (recorded 2026-10-20T03:20:47/03:21:30Z, Oct 24–25 window) **+ M50–M56** (recorded 2026-10-20T10:40:14/15Z, Oct 31–Nov 1 window — the D-1 batch fired; delta-7's "M50–M56 not yet forecast" gap is now closed) |
| 6a | launchd `com.myquant.wslprov.d1` loaded | **PASS** | `launchctl print gui/501/com.myquant.wslprov.d1` → loaded (LaunchAgent, plist `~/Library/LaunchAgents/com.myquant.wslprov.d1.plist`, state "not running" = scheduled idle); `StartCalendarInterval` 15:00 daily |
| 6b | `wsl_d1_batch.sh` exists + executable | **PASS** | `research/control/SPORTS-PAPERTRADE-EXEC-V1/wsl_d1_batch.sh` `-rwxr-xr-x` (mtime Oct 20 17:40 ICT); plist program points at this exact path |
| 7a | node test_ai_gate.js | **PASS** | **17/17** |
| 7b | node test_ai_seam.js /tmp/a7r8 | **PASS** | **43/43** |
| 7c | node test_paper_policy.js | **PASS** | **27/27** |
| 7d | node test_lifecycle_safety.js | **PASS** | **13/13** |
| 8a | pytest ui_control_seam + wsl_results → 18 passed | **PARTIAL (pass-count stale)** | Measured **19 passed** (8 ui_control_seam + 11 wsl_results), 0 failed — same 19 delta-7 measured; all green |
| 8b | Full battery 16 failed / 105+ passed, name-set == documented baseline | **PARTIAL (see F-1)** | Measured **11 failed, 114 passed** (125 tests; was 121). All 11 failures are a **strict subset** of the documented 16-name baseline (delta-6 §baseline / WSL_BET_PAPER_VERIFY §F): 10× `test_exec_battery` + `test_b1r_fail_closed::test_run_day_sandbox_soccer_journals_no_b1r`. The 5 no-longer-failing are exactly `test_nba_adapter_pin_drift_blocked`, `test_nba_adapter_refuses_tampered_payload_dir`, `test_nba_outcome_leak_injected_completed_row_ignored`, `test_nba_prospective_engine_success_opening_window`, `test_nba_window_success_chain_sandbox` — the NBA set that round-9's restoration (commit 843fb5a3, "BLOCKED_NBA_ENTRY closed at the source") lawfully fixes. +4 tests = round-10 `test_pm_moneyline.py` ("battery 4/4"). No new failure; baseline name-set drift documented only in commit messages, not yet in a control artifact |
| 9a | Registry exec-v1 head == HEAD; cutover REGISTERED_NOT_CONSUMED | **PASS** | `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json`: SPORTS-PAPERTRADE-EXEC-V1 `head=d5854aea…` == worktree HEAD; `go_phrase="GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER"`, `go_phrase_state="REGISTERED_NOT_CONSUMED (registered 2026-10-10T03:45:02Z …)"; phase names round-10 d5854aea, "cutover REGISTERED_NOT_CONSUMED, AI authority NOT_REGISTERED"; updated 2026-10-20T11:04:47Z |
| 9b | GO_TOKEN phrase unchanged | **PASS** | `GO_TOKEN.json`: `GO SPORTS PAPERTRADE EXEC V1 RUN ALL`, typed 2026-10-07T11:08:47Z — byte-identical to delta-6/7 readings |
| 9c | AI authority NOT_REGISTERED | **PASS** | 0 occurrences of any "AI AUTHORITY" phrase in the root registry; `AI_ACTIONS_PACKET_2026-10-20.md` §4: "AI authority for acting on paper decisions is **NOT REGISTERED**", candidate shape (`GO SPORTS PAPERTRADE EXEC V1 AI ACTIONS PAPER EXECUTE`) explicitly NOT registered |
| 10a | `GET /api/state` chain ok, 48→59 rows (exact) | **PASS** | HTTP 200; `chain.ok=true`, `ledger.rows_count=59`, `mode=REAL`, `generated_at_utc=2026-10-20T11:28:33Z` (listener pid 73887 on 127.0.0.1:8791) |
| 10b | runner + app processes reported | **PASS** | PaperDesk app **pid 73876** (owner GUI-launched; same instance delta-7 observed) + helpers; `ops_service` **pid 73887** (`python -m research.papertrade_exec.ops_service --data-root ~/.my-quantitative-data/sports-papertrade-exec-v1`, PPID 73876 — the app's own child per lifecycle law), LISTENing on 8791. Both owner-controlled; untouched |

## 2. Commands + results (verbatim, condensed)

```
git rev-parse HEAD                         → d5854aeafebebfefa3966552b46e4ff4427e5c45; status: 1 untracked file only
git -C <nba worktree> rev-parse HEAD       → 82542aa8e97206b88f7eb777f4461b09054e9b09
shasum -a 256 loader.py predict.py         → 2679be80… / 57f0c810… == pins.json nba26
sha256(main ledger)                        → 1486e85e4d28b50714b4418988e3c4fdbf2718734e2d925fd6598d0a5454f563 (59 rows)
pinned core verify_chain(main)             → (True, []) 59 rows
pinned core verify_chain(prov)             → (True, []) 29 rows; FORECAST kickoff>2026-10-20 = 14 (M43–M49 + M50–M56)
main ledger FORECAST leagues               → WNBA 4 / SOCCER 2 / WSL 7 / NBA 11; NBA model_version_sha == pin
launchctl print gui/501/com.myquant.wslprov.d1 → loaded; program = …/wsl_d1_batch.sh; 15:00 daily
wsl_d1_batch.sh                            → -rwxr-xr-x (executable)
node test_ai_gate.js                       → 17/17
node test_ai_seam.js /tmp/a7r8             → 43/43
node test_paper_policy.js                  → 27/27
node test_lifecycle_safety.js              → 13/13
pytest ui_control_seam + wsl_results -q    → 19 passed (8 + 11)
pytest tests/papertrade_exec -q            → 11 failed, 114 passed; failures ⊂ documented 16-name baseline (5 NBA tests fixed)
registry exec-v1                           → head d5854aea…; phase round-10; cutover REGISTERED_NOT_CONSUMED; AI authority NOT_REGISTERED
GO_TOKEN.json                              → "GO SPORTS PAPERTRADE EXEC V1 RUN ALL" @2026-10-07T11:08:47Z (unchanged)
grep "AI AUTHORITY" root registry          → 0 hits
curl 127.0.0.1:8791/api/state              → HTTP 200; chain.ok true; rows_count 59; mode REAL
pgrep / lsof                               → PaperDesk 73876 (owner) + ops_service 73887 (app child, LISTEN 8791)
```

## 3. Findings

- **F-1 (MEDIUM, dispatch-claim drift — improvement, not regression)** — The
  full battery re-measures **11 failed / 114 passed**, not the claimed
  "16 failed / 105+ passed". All 11 failures are inside the documented
  16-name baseline; the 5 that now pass are precisely the NBA
  adapter/engine tests (`test_nba_adapter_pin_drift_blocked`,
  `test_nba_adapter_refuses_tampered_payload_dir`,
  `test_nba_outcome_leak_injected_completed_row_ignored`,
  `test_nba_prospective_engine_success_opening_window`,
  `test_nba_window_success_chain_sandbox`) — the exact set round-9 commit
  843fb5a3 claims to fix by restoring the pinned NBA worktree (verified
  restored at 82542aa8 with byte-exact pins, claim 3). Test count 121→125 =
  round-10's `test_pm_moneyline.py` (4 tests). Nothing new fails. However,
  the baseline name-set was never re-documented as 11 in a control
  artifact — only in commit messages — so any future round diffing against
  the delta-6 "16 failures" section will see a mismatch. The baseline
  document should be superseded by the owner.
- **F-2 (LOW, stale hash in dispatch)** — Claim 2's sha prefix `58edc089…`
  is the 48-row pre-NBA ledger digest (delta-6 measurement; round-8 commit
  "main ledger sha unchanged 58edc089"). Round-9 lawfully appended 11 NBA
  FORECAST rows (→ 59 rows), so the file hash necessarily changed; measured
  `1486e85e4d28b50714b4418988e3c4fdbf2718734e2d925fd6598d0a5454f563`. The
  dispatch claim is internally inconsistent (59 rows cannot carry the
  48-row digest). The load-bearing part — pinned verifier True / 59 rows —
  passes.
- **F-3 (LOW, hygiene)** — Worktree tree is not fully clean: untracked
  `apps/paperdesk/main/pm_stake_law.js` (mtime Oct 20 17:35). Zero
  references from any JS under `apps/paperdesk`; never committed. Inert,
  likely a leftover scratch from the round-10 PM work. Left untouched per
  "repair nothing"; owner should commit or delete.
- **F-4 (INFO)** — Two-file battery measured **19 passed**, dispatch said
  18 (delta-7 also measured 19 = 11 wsl_results + 8 ui_control_seam).
  All green either way; the "18" appears to be a dispatch transcription slip.
- **F-5 (INFO)** — Since delta-7 the provenance ledger grew 22→29 rows:
  M50–M56 FORECAST rows (Oct 31–Nov 1 window) recorded 2026-10-20T10:40Z —
  delta-7's open caveat ("M50–M56 have no provenance rows yet; the D-1
  batch must be run") is now closed by the installed launchd agent
  (15:00 ICT daily) plus this batch. Main ledger was NOT touched by that
  work (its growth is the separate, separately-claimed NBA append).

## 4. Verdict rationale

All ten dispatch claims were re-measured. Eight reproduce exactly. The two
that do not (F-1, F-2) are stale dispatch numbers pointing at pre-round-9
state; measured reality is strictly better or bookkeeping-equivalent, is
fully explained by committed round-9/round-10 work, and breaks no law: no
new test failure, no pin edited, no GO consumed, no AI authority
registered, ledger chains verify through the pinned core on both sides,
and the live service agrees with the on-disk ledger (59 rows). No CRIT or
HIGH finding. **VERIFY_PASS_WITH_FINDINGS.**
