# PAPERDESK A7 — DELTA-7 INDEPENDENT VERIFICATION (round-7, 2026-10-20)

**VERDICT: VERIFY_PASS_WITH_FINDINGS** — 0 CRIT / 0 HIGH / 2 LOW / 3 INFO.
Round-7 (WSL provenance-capture repair) reconciles end-to-end: the 7 new
FUTURE provenance FORECAST rows are lawful (chain-verified, strictly
pre-anchor, pinned adapter unmodified), the exec-side reproduction of the
forecast is BIT-EQUAL for M44/M48 with `cross_check_forecast` PASSING
(`NOT_RUN_NO_PROVENANCE_FORECAST` is gone for the Oct 24-25 window;
`BLOCKED_FORECAST_DISAGREEMENT` does not fire), the corpus-gap honesty claim
reproduces live (fresh fixturedownload probe: R6 finals still EMPTY 0/7),
and ledger/GO/registry/bundle end-state is intact.

Verifier: A7 fresh-context subagent. Read-only except this artifact.
e2e shell scripts (`e2e_evidence.sh`, `e2e_lifecycle.sh`) NOT_RUN by
dispatch instruction. Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

---

## 1. Claim table

| # | Claim | Result | Evidence (measured this pass) |
|---|-------|--------|-------------------------------|
| 1a | Provenance ledger chain verifies via pinned core | **PASS** | `execute.load_pinned_core(roots={})` + `core.ledger.PaperLedger(~/.my-quantitative-data/wsl-winprob-paper-prep-v1/ledger/paper_ledger.jsonl).load().verify_chain()` → **True, errors []** |
| 1b | Row count 22 = 15 + 7 new | **PASS** | 22 rows: 1 GENESIS + 14 FORECAST + 7 DECISION (pre-repair 15 = 1+7+7) |
| 1c | 7 new FORECAST rows M43–M49, WSL, Oct 24/25 | **PASS** | M43–M49 all `league=WSL`, `type=FORECAST`; kickoffs 2026-10-24T11:45/16:15Z (M44/M48), 2026-10-25T12:00/14:00/14:00/14:00/18:00Z (M47/M45/M46/M49/M43) |
| 1d | recorded_at 2026-10-20T03:20/03:21Z, strictly pre-anchor (kickoff−6h) | **PASS** | M44+M48 `recorded_at_utc=2026-10-20T03:20:47Z`; M43/M45/M46/M47/M49 `03:21:30Z`; every row `recorded < anchor` (anchors 05:45Z Oct 24 … 12:00Z Oct 25) |
| 1e | `date_d` fields 2026-10-24 / 2026-10-25 | **PASS** | M44/M48 `date_d=2026-10-24`; M43/M45/M46/M47/M49 `date_d=2026-10-25` |
| 1f | p = {HOME,DRAW,AWAY} floats summing ~1.0; chain links valid | **PASS** | All 7 rows have exactly HOME/DRAW/AWAY floats; sums 1.0 … 0.9999999999999999 (M43); each row's `prev_hash` == prior row's `hash` (and `verify_chain` True) |
| 2a | Delta diff 08652455..b42d8e7b touches control/evidence files only | **PASS** | `diff --name-status`: 3 added files, all under `research/control/SPORTS-PAPERTRADE-EXEC-V1/` (ERRATUM_ROUND6_HANDOFF_TABLE, WSL_PROVENANCE_REPAIR law, paperdesk_evidence/wsl_all_six_identity_audit json). Zero code changes |
| 2b | `wsl_forecast_adapter.py` NOT modified | **PASS** | File lives outside this repo (prep worktree). (i) no delta commit touches any adapter path; (ii) prep integration worktree: adapter tracked + unmodified (`git status` shows only an untracked `DISPATCH/` dir); (iii) live sha256 `c4ef9656b6ea5625ff558620e82812101501b1621431d3b7ddbf33e649118a50` == sha recorded in `lanes/L_ADAPTER/handoffs/L_ADAPTER.handoff.json` |
| 3a | 7 fixtures across the two files; ids resolve via pinned crosswalk | **PASS** | 2 (10-24) + 5 (10-25) = 7; for every fixture: csv `crosswalk_fixturedownload_to_ewf_teamid.csv[source_name]` == home/away `*_team_id` **and** byte-pinned `pm.WSL_FD_NAME_TO_TEAM_ID` agrees (15/15 rows both representations) |
| 3b | kickoff/round match exec substrate rows | **PASS** | All 7 match `wsl_fixture_substrate.jsonl` on home/away/kickoff_utc/round=7/venue |
| 4a | node test_paper_policy.js | **PASS** | **27/27** |
| 4b | node test_ai_seam.js /tmp/a7r7 | **PASS** | **43/43** |
| 4c | node test_lifecycle_safety.js | **PASS** | **13/13** |
| 4d | pytest test_wsl_results.py + test_ui_control_seam.py | **PASS** | **11 passed + 8 passed** (19 total, 0 failed) |
| 4e | full pytest tests/papertrade_exec = 16F/105P, name-set == baseline | **PASS** | **16 failed, 105 passed**; failed name-set = 15 `test_exec_battery::*` + 1 `test_b1r_fail_closed::test_run_day_sandbox_soccer_journals_no_b1r` — exactly the known baseline |
| 4f | Offline repro: provenance index contains M44+M48; exec `engine_forecast` reproduces provenance p BIT-EQUAL; `cross_check_forecast` does not raise | **PASS** | `provenance_forecast_index(WSL_PROVENANCE_LEDGER, core)` → 14 WSL FORECAST rows incl. M44/M48; from config substrate+corpus (2704 rows, last date 2026-10-04): M44 p HOME 0.15059490721574623 / DRAW 0.17524632725136496 / AWAY 0.6741587655328889, M48 p HOME 0.508826690912779 / DRAW 0.20856453177979276 / AWAY 0.2826087773074282 — repr-identical both sides, cross_check **no raise** (bit-equality, never averaged) |
| 5a | Exec corpus last date == 2026-10-04 (R5-sealed) | **PASS** | `max(date)` over `wsl_substrate_corpus.jsonl` = **2026-10-04** (2704 rows) |
| 5b | Fresh fixturedownload probe: R6 Result still EMPTY | **PASS (no change)** | `curl -s --compressed https://fixturedownload.com/download/wsl-2026-UTC.csv` → 182 data rows; R1–R5 7/7 posted, **R6 0/7 posted**, R7+ empty. R6 pairings match the exec substrate exactly. Nothing modified |
| 5c | Law file documents the gap honestly | **PASS** | `WSL_PROVENANCE_REPAIR_2026-10-20.md` records the R6-not-posted probe (01:15Z), R5-sealed ratings as lawful (like batch-B), qualified-scores source OPEN, re-probe duty each D-1 — all reproduced live this pass |
| 6a | Root registry exec-v1 head == b42d8e7b == `git rev-parse HEAD` | **PASS** | `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json` (writable authority): SPORTS-PAPERTRADE-EXEC-V1 head = `b42d8e7b51a2e87416b210ad1e03bcea2bf45b2d`; worktree HEAD = same; branch `orca/spt-exec-v1-integration` |
| 6b | phase GO_CONSUMED; cutover REGISTERED_NOT_CONSUMED | **PASS** | phase begins `GO_CONSUMED CAPTURE_ACTIVE LIVE_SERVICE_ACTIVE` with round-7 text naming b42d8e7b; `go_phrase_state` = `REGISTERED_NOT_CONSUMED` (cutover scope, 2026-10-10 registration note) |
| 6c | GO_TOKEN phrase unchanged | **PASS** | `GO_TOKEN.json`: `GO SPORTS PAPERTRADE EXEC V1 RUN ALL`, typed 2026-10-07T11:08:47Z — byte-identical to prior rounds |
| 6d | MAIN ledger pinned verifier True / 48 rows / mtime unchanged since round-6 settle | **PASS** | `verify_chain()` **True, errors []**, **48 rows** (1 GENESIS + 13 FORECAST + 11 MARKET_QUOTE + 13 DECISION + 10 SETTLEMENT); mtime **2026-10-20T01:52:47Z == last row `settled_at_utc` (FD-2026-M38)** — no writes after the settle (dispatch's "~01:40Z" is prose approximation; delta-6 itself documents the settle landing 01:52:46Z) |
| 6e | Open WSL bets 0 | **PASS** | 0 rows with type BET/BET_PAPER in open/pending state; 6 WSL SETTLEMENT rows (M36–M42); last `equity_after_cents` = **113495** ⇒ net +11280c vs genesis 102215c (matches the erratum; the raw Σ settlement pnl 13495c includes the 4 pre-genesis WNBA settles = 2215c) |
| 6f | ai_review/opinions count unchanged | **PASS** | 0 files, directory empty (delta-6 recorded "0 files, unchanged") |
| 6g | launchd label absent + disabled | **PASS** | `launchctl print gui/501/com.myquant.sptexec.ops` → "Could not find service" (not loaded); `launchctl print-disabled` → `com.myquant.sptexec.ops => disabled`; plist file still on disk in `~/Library/LaunchAgents` (inert, disabled) |
| 6h | No controller-owned ops_service/PaperDesk processes | **PASS** (owner instances PRESENT, left alone) | PaperDesk pid **73876** (PPID **1** = launchd GUI launch, started 09:47:40 ICT = 02:47:40Z) and ops_service pid **73887** (PPID **73876** — the app's own child, started 09:47:47 ICT) are running. Both pre-date the round-7 repair window (03:20Z) and are owner-owned (GUI-launched app-managed child per the lifecycle law), NOT started by any controller session. Untouched |
| 6i | opslock HELD/FREE matches reality | **PASS** | `ops/service.lock` **HELD** by pid 73887 (`lsof`: Python 73887 FD 3) — consistent with the live owner-run service; read-only probes `GET /` and `GET /api/state` (127.0.0.1:8791) → **HTTP 200**, state shows `chain.ok=true`, `rows_count=48`, `mode=REAL` |
| 7a | .app codesign OK | **PASS** | `codesign --verify --deep --strict -v` → "valid on disk / satisfies its Designated Requirement", exit 0 |
| 7b | Packaged main/paper_policy.js + ai.js + candidates.js present | **PASS** | `PaperDesk.app/Contents/Resources/app/main/` contains all three (plus canonical/ledger/main/market/runner/seal) |
| 7c | Packaged self-check CLI on REAL ledger | **PASS** | `PaperDesk.app/Contents/MacOS/PaperDesk --self-check-ledger ~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl` → `{"rows":48,"sandbox":false,"chain_ok":true,"verified_rows":48,"errors":[],"parse_error":null}` |

## 2. Commands + results (verbatim, condensed)

```
git -C <integration worktree> rev-parse HEAD   → b42d8e7b51a2e87416b210ad1e03bcea2bf45b2d  (branch orca/spt-exec-v1-integration)
git -C <integration worktree> rev-parse b42d8e7b^  → a969e0487a80ea6046f69121a22e4f6b19cbc05f  (see F-1)
git diff --name-status 08652455..b42d8e7b       → 3 A files, all research/control/SPORTS-PAPERTRADE-EXEC-V1/*
git -C <prep integration worktree> status --short → ?? research/control/.../DISPATCH/  (adapter unmodified)
shasum -a 256 <prep>/.../L_ADAPTER/wsl_forecast_adapter.py → c4ef9656… (== L_ADAPTER.handoff.json)

pinned core + PaperLedger(prov).verify_chain()  → True / 22 rows / 7 new FORECAST M43–M49
fixtures csv+pinned crosswalk recompute          → 7/7 True/True/True (csv, pinned map, substrate)
node test_paper_policy.js                        → 27/27 pass
node test_ai_seam.js /tmp/a7r7                   → 43/43 pass
node test_lifecycle_safety.js                    → 13/13 pass
pytest tests/papertrade_exec/test_wsl_results.py → 11 passed
pytest tests/papertrade_exec/test_ui_control_seam.py → 8 passed
pytest tests/papertrade_exec -q                  → 16 failed, 105 passed (name-set == baseline)
offline repro M44/M48                            → bit-equal True/True; cross_check no raise; NOT_RUN_NO_PROVENANCE_FORECAST gone
wsl_substrate_corpus.jsonl max(date)             → 2026-10-04
curl fixturedownload wsl-2026-UTC.csv            → R6 0/7 Result posted (no change)
registry exec-v1 head                            → b42d8e7b… == HEAD; phase GO_CONSUMED…round-7; cutover REGISTERED_NOT_CONSUMED
main ledger verify_chain                         → True / 48 rows / mtime 2026-10-20T01:52:47Z == last settled_at_utc; open WSL bets 0; equity_after 113495c
launchctl print gui/501/com.myquant.sptexec.ops  → not found; print-disabled → disabled
ps/lsof                                          → PaperDesk 73876 (PPID 1, owner GUI) + ops_service 73887 (PPID 73876, app child); opslock HELD by 73887
curl 127.0.0.1:8791/ and /api/state              → HTTP 200; chain ok true, rows 48, mode REAL
codesign --verify --deep --strict PaperDesk.app  → valid, exit 0
packaged self-check on REAL ledger               → chain_ok true, 48 rows
```

## 3. Findings

- **F-1 (LOW, information)** — Commit graph: the dispatch names parent `08652455`, but `b42d8e7b`'s immediate parent is `a969e048` (the ERRATUM round-6 handoff commit), whose parent is `08652455`. The delta `08652455..b42d8e7b` therefore spans both the erratum carry-over and the round-7 repair — exactly the scope the dispatch describes ("stability/erratum carry-over"); no content is missing from verification. All 3 changed files are control/evidence additions; no code path changed.
- **F-2 (LOW, pre-existing)** — The integration worktree's own `plans/CYCLE_REGISTRY.json` remains a stale mirror (capital-v3 row still pre-GO `CAPITAL_V3_READY_PENDING_OWNER_GO`; exec row at R11 head `9a18a4f2`). The root registry `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json` is the writable authority and is correct (round-7 head recorded). Same known mirror-drift finding as delta-6 (F-4 there); no action required this round.
- **F-3 (INFO)** — Main ledger mtime is `2026-10-20T01:52:47Z`, byte-locked to the last row's `settled_at_utc` (M38). The dispatch's "~01:40Z" was prose approximation; delta-6 itself already explained the settle landed at 01:52:46Z after its prose was drafted. Unchanged-since-settle holds exactly.
- **F-4 (INFO)** — End-state: the OWNER is running PaperDesk (pid 73876, GUI-launched via launchd) which spawned its own ops_service child (pid 73887) — the lifecycle law's normal "app-owned child" state. Neither process is controller-owned; both were left untouched. opslock HELD by the service matches reality; live API probes confirm chain ok / 48 rows / REAL mode. The dispatch's expected "no processes" end-state differs only by these legitimate owner instances (delta-6 recorded the opposite drift — zero instances — as its MED; neither state affects any recorded-evidence claim).
- **F-5 (INFO)** — Fresh fixturedownload probe (this pass, ~03:4xZ): R6 (Oct 17-18) finals still EMPTY 0/7 — no change against the law file's 01:15Z probe. The corpus-honesty caveat therefore still stands verbatim; nothing was modified.

## 4. What round-7 does NOT change (honest scope)

1. **Provenance capture is repaired for the Oct 24-25 window only.** The D-1
   batch automation (cron) is gone from the machine; continuity law makes the
   controller run the batch manually each D-1. M50–M56 (Oct 31–Nov 1) have no
   provenance rows yet — the same NOT_RUN would return at the next window
   unless the D-1 batch is run.
2. **Corpus remains R5-sealed (last played row 2026-10-04).** Forecasts for
   Oct 24-25 are honest but less-informed (ratings miss round 6), lawfully so
   per the repair law; UMA W/D/L results cannot feed the integer-score engine
   replay; qualified-scores source remains OPEN.
3. e2e shell scripts NOT_RUN by instruction; Polymarket live listing for the
   window (events 1212252/1212928) is accepted from the round-7 commit record,
   not re-probed (not in dispatch scope).

## 5. Verdict rationale

Every dispatch claim that could be re-measured was re-measured and matched:
pinned chain verifications on both ledgers, crosswalk/substrate recompute,
node + pytest batteries with baseline-identical failure name-set, the
bit-equality forecast reproduction (the exact refusal point eliminated),
live source probe reproducing the honesty claim, and registry/GO/ledger/
bundle end-state. Findings are LOW/informational only, none invalidate a
recorded claim. **VERIFY_PASS_WITH_FINDINGS.**
