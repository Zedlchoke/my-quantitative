# PAPERDESK A7 DELTA-6 VERIFICATION — round-6 commit d790f7b7 (WSL settlement gap CLOSED)

Verifier: A7, independent, fresh context. Date: 2026-10-20.
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`
Method: audit of the RECORDED outcome only. No settle pass, no e2e settle, no cmd_settle was
executed by this verifier. No signal was sent to any process. The only live network probe was a
GET to the public Gamma API. The real ledger was opened read-only; its sha256 was re-measured
after all verifier activity (incl. full test suites) and is unchanged.

## VERDICT

**VERIFY_PASS_WITH_FINDINGS** — 0 CRIT / 0 HIGH / 1 MED / 2 LOW / 2 INFO.
Every substantive round-6 claim (law, source, gate, pinned-core identity, real settlement
outcome, pnl math, equity chain, zero open bets, tests, registry/GO, UI) PASSES on recorded
evidence plus one independent live cross-check. The MED finding is environment drift, not a
defect of this delta: the owner's live PaperDesk/ops_service instances recorded in the dispatch
are NOT running at verification time, so three live end-state probes are NOT_RUN.

## Identity

- `git rev-parse HEAD` = `d790f7b76ac0de8605168231b5bcbd71558d3411`; parent = `521d21ae…`;
  branch `orca/spt-exec-v1-integration`; `git status --porcelain` clean.
- Pinned reference for the settlement law body: `0c049c67` (A7 delta-3 artifact commit, ancestor
  of 521d21ae in the same lineage).

## Claim table

| # | Claim | Result | Command / evidence |
|---|-------|--------|--------------------|
| 1 | LAW FILE `WSL_RESULTS_SOURCE_V1.md` | PASS | Read in full: qualified source = bet's OWN tracked 3-YES 90-minute markets, identity by construction (ledger MARKET_QUOTE event_id + per-leg market_id, "no name/date guessing ever occurs"); settlement-eligible ONLY closed=true + umaResolutionStatus=resolved + exactly-one outcomePrices[0]==1.0 with the other two ==0.0; postponed/cancelled/voided "NEVER produce a clean one-of-three YES=1 ⇒ inconclusive ⇒ the bet stays OPEN (no inference, no premature refund)"; journal law "raw + sha256 + retrieval UTC under `<data-root>/data/wsl_results/`"; lane gate law (every entry source_ref starts `polymarket_uma event=`, result ∈ {HOME,DRAW,AWAY}, else BLOCKED_NO_RESULTS_SOURCE); The Odds API (81 sports, zero WSL) and ESPN `soccer/eng-w.1` (zero events in any window) recorded as probed-and-REJECTED |
| 2 | SOURCE MODULE `research/papertrade_exec/wsl_results.py` | PASS | Read in full: `_quote_ref` requires the ledger MARKET_QUOTE row for the match (event_id + pm_outcomes per-leg market_id = identity by construction); eligibility `closed and uma=="resolved" and yp is not None and ok_id`; winners = legs with `p == 1.0`, zeros = `p == 0.0`, `len(winners)!=1 or len(zeros)!=2` → inconclusive (stays OPEN); event identity = both team names in event title, per-leg identity = team-in-question OR kickoff date in question, both THROUGH `_pm_to_fd()` which loads the pinned `WSL_PM_NAME_TO_FD_NAME` via `wsl_lane.load_pm_source()` (pin `PM_SOURCE_SHA256=4b27ab17…` re-hashed against the pinned file = match); `_norm` = `re.sub(r"[^a-z0-9]+","",casefold)` — byte-identical to pinned `polymarket_source.norm_name` (line 747 of the pinned file); journal = raw bytes + index.jsonl `{at_utc,url,sha256,bytes}` under `<dataRoot>/data/wsl_results/`; transport seam `_gamma_fetch_raw` (tests stub it); module never writes the ledger |
| 3a | Gate `wsl_lane.cmd_settle` | PASS | Read (wsl_lane.py:921-948): file missing/empty or not dict → `BLOCKED_NO_RESULTS_SOURCE`; EVERY entry must have `source_ref.startswith("polymarket_uma event=")` AND `result in ("HOME","DRAW","AWAY")` else LaneBlock BLOCKED_NO_RESULTS_SOURCE ("never a guessed settlement"); valid files delegate to `execute._cmd_settle_standard(args)` |
| 3b | `execute.cmd_settle` routing | PASS | execute.py:1592-1597: `cmd_settle` = `maybe_wsl(args,"settle")` early-return (routes league WSL to wsl_lane; other leagues unchanged) then `_cmd_settle_standard` |
| 3c | `_cmd_settle_standard` == pinned body | PASS | Mechanical diff: pinned `git show 0c049c67:research/papertrade_exec/execute.py` settle body (require_gate → verify_pins → open_ledger → per-BET_PAPER DECISION walk → risk.settle append) vs current `_cmd_settle_standard` → **byte-identical** (`diff` clean). Only change: the maybe_wsl early-return split out. Settlement law unchanged |
| 3d | `ops_service._fetch_results` WSL branch | PASS | ops_service.py:320-328: `league=="WSL"` → `wsl_results.fetch_wsl_settleable(rows, ledger_rows, data_root, sandbox)` |
| 4a | Pinned verifier on REAL ledger | PASS | Pinned `PaperLedger(<REAL>/ledger/paper_ledger.jsonl).load().verify_chain()` → **True, 48 rows, errors []** |
| 4b | Row census 42 → 48, +6 SETTLEMENT only | PASS | Census: GENESIS 1 + FORECAST 13 + MARKET_QUOTE 11 + DECISION 13 + SETTLEMENT 10 = 48 (prior: SETTLEMENT 4 = 42). Rows 43-48 are exactly the six WSL SETTLEMENTs; no DECISION/FORECAST/QUOTE row added or modified (hash-chained ledger verifies; census deltas are +6 SETTLEMENT exclusively) |
| 4c | Six settlements lawful shape | PASS | Each of FD-2026-M36/M37/M38/M39/M40/M42: result ∈ {HOME,DRAW,AWAY}; source_ref starts `polymarket_uma event=`, contains `winner=<result>`, `markets=<3 ids>`, `resolvedBy=0x69c47De9D4D3…`, `uma=resolved` |
| 4d | PnL math re-derived | PASS | From each decision row's OWN `odds_frozen[chosen_leg]` and `stake_cents=1022`: WIN `round(1022*(d-1))`, LOSE `-1022`. M37 DRAW d=12.0112 → +11253 (actual +11253); M36 HOME d=3.7089 → +2769 ✓; M38 HOME d=1.3169 → +324 ✓; M40/M39/M42 LOSE → −1022 each ✓. 6/6 exact |
| 4e | Outcome distributions | PASS | Ledger order: M37 chosen DRAW = DRAW WIN +11253; M40 chosen HOME, result AWAY LOSE −1022; M36 chosen HOME = HOME WIN +2769; M39 chosen AWAY, result HOME LOSE −1022; M42 chosen HOME, result AWAY LOSE −1022 (see F-2 label note); M38 chosen HOME = HOME WIN +324. Round-6 net +11280c |
| 4f | equity_after chain continuous | PASS | 102215 (last pre-round-6 equity) +11253=113468 (M37) → 112446 (M40) → 115215 (M36) → 114193 (M39) → 113171 (M42) → 113495 (M38). Every settlement row = previous equity + pnl; final **113495c**. Totals reconcile: genesis 100000 + 4 prior settlements (+2215) + 6 new (+11280) = 113495 (see F-3 prose note) |
| 4g | Independent live Gamma cross-check (M37) | PASS | `GET https://gamma-api.polymarket.com/events?id=1167584` (public, no key): title "Arsenal WFC vs. Birmingham City WFC"; market 5528995 (HOME) closed=true uma=resolved prices ["0","1"]; 5528996 (DRAW) closed=true uma=resolved prices ["1","0"]; 5528997 (AWAY) closed=true uma=resolved prices ["0","1"]; resolvedBy 0x69c47De9D4D3Da — exactly one YES=1 (DRAW), matching the ledger result DRAW and the journaled resolution |
| 4h | Journal integrity | PASS | `<dataRoot>/data/wsl_results/` holds raw payloads for all 6 events (2 fetch passes) + `index.jsonl` 13 entries; spot-check: file `20261020T014121Z_event_1167584.json` sha256 `197f63d0…` == index entry sha (and identical to the 01:38 probe entry — same bytes) |
| 5 | Zero open WSL bets / exposure 0 | PASS | Ledger: 6 WSL BET_PAPER decisions, 0 unsettled; open exposure = 0c. `curl http://127.0.0.1:8791/api/state` → HTTP 000 (connection refused — see F-1), so open_count=0 confirmed **offline from the chain-verified ledger**, not via the API |
| 6a | `node test_paper_policy.js` | PASS | 27/27 pass |
| 6b | `node test_ai_seam.js /tmp/a7r6` | PASS | 43/43 pass |
| 6c | `node test_lifecycle_safety.js` | PASS | 13/13 pass |
| 6d | pytest tests/papertrade_exec | PASS | **16 failed, 105 passed** in 51.1s; visible root cause `BLOCKED_SOCCER_ENTRY: Lane C replay entry absent; no fallback in real mode` (execute.py:741) = the documented sibling-entry drift |
| 6e | Failing NAME-SET == baseline | PASS | 15 × test_exec_battery + 1 × test_b1r_fail_closed (list below). Throwaway clone at pre-round `521d21ae`: 16 failed, **name-set byte-identical** (`diff` clean). Nothing new broken, nothing silently fixed |
| 6f | test_wsl_results.py | PASS | **11/11 pass** (dispatch said 10/10 — see F-5). Covers: FT draw resolution, HOME variant, ambiguous all-NO, 50/50 void, pending UMA, question-date mismatch, missing quote row, crosswalk + ampersand, transport error, lane-gate refuses foreign source file, e2e sandbox settle through pinned core |
| 7a | Root registry head == d790f7b7 == HEAD | PASS | `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json` (writable authority): SPORTS-PAPERTRADE-EXEC-V1 head = `d790f7b76ac0de8605168231b5bcbd71558d3411`, updated 2026-10-20T01:56:28Z, phase begins "GO_CONSUMED CAPTURE_ACTIVE LIVE_SERVICE_ACTIVE", round-6 text names d790f7b7. Worktree copy is the known stale mirror (F-4) |
| 7b | Cutover REGISTERED_NOT_CONSUMED | PASS | go_phrase "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER" state REGISTERED_NOT_CONSUMED (registered 2026-10-10); prior RUN ALL documented OWNER_GO_TYPED 2026-10-07T11:08:47Z + CONSUMED 11:19:08Z |
| 7c | GO_TOKEN unchanged | PASS | Last commit touching GO_TOKEN.json = `b250bfb1` ("GO CONSUMED (P-8)"); content sha256 `69027c34…` (same as A7 2026-10-19 record); content = `go_phrase_typed_by_owner: "GO SPORTS PAPERTRADE EXEC V1 RUN ALL"` |
| 7d | ai_review/opinions | PASS | 0 files, directory empty (unchanged end-state) |
| 7e | launchd end-state | PASS | `~/Library/LaunchAgents/com.myquant.sptexec.ops.plist` present (installed) but `launchctl print-disabled gui/$UID` → `"com.myquant.sptexec.ops" => disabled`; no launchd agent instance running |
| 7f | Owner pids 55580/55611 alive; opslock HELD; API open_count 0 | **NOT_RUN** | No process 55580/55611 exists; no PaperDesk/ops_service process at all; nothing listens on 8791; `lsof +D <dataRoot>` empty → ops/service.lock (present, 0 bytes, mtime Oct 8) held by NOBODY. Environment drift — see F-1 (MED). Not caused by this verifier (read-only probes only); does not affect any recorded-evidence claim |
| 8a | UI text path | PASS | renderer/app.js:362-367: OPEN card past `kickoff + 3*3600*1000` → "🏁 Match finished — settlement pending a qualified results source (90-minute law; never inferred). WSL: resolved via the tracked Polymarket markets."; pre-grace OPEN → the prior "settles only from the pinned results source…" text |
| 8b | Packaged bundle contains it + parity | PASS | `build/PaperDesk-darwin-arm64/PaperDesk.app/Contents/Resources/app/renderer/app.js` line 365 has the text; `cmp` packaged vs worktree app.js → byte-identical; bundle mtime Oct 20 08:53:55 2026 (rebuilt this round) |
| 8c | codesign | PASS | `codesign --verify --strict` OK (adhoc, Identifier=com.myquant.paperdesk) |

### The 16 baseline failures (name-identical at HEAD and 521d21ae)

`test_b1r_fail_closed.py::test_run_day_sandbox_soccer_journals_no_b1r`;
`test_exec_battery.py::` test_forecast_reports_wiring_status, test_nba_adapter_pin_drift_blocked,
test_nba_adapter_refuses_tampered_payload_dir,
test_nba_engine_replay_via_scored_harness_synthetic_inputs,
test_nba_outcome_leak_injected_completed_row_ignored,
test_nba_prospective_engine_success_opening_window, test_nba_window_success_chain_sandbox,
test_plan_is_readonly_with_real_tips, test_run_day_chains_three_leagues_sandbox,
test_soccer_extension_crosswalk_laws, test_soccer_forecast_real_engine_in_memory_only,
test_soccer_real_fixtures_fake_client_day_filter_snapshot,
test_soccer_stage_law_blocks_engine_before_crosswalk, test_success_path_end_to_end_sandbox,
test_wnba_engine_entry_wired_contract. (Same set as WSL_BET_PAPER_VERIFY.md §F / A7-DELTA3 5d.)

## Ledger delta summary (the exact record)

42 rows → 48 rows: +6 WSL SETTLEMENT rows, nothing else. Pinned chain verify True / 48 rows /
errors []. Ledger sha256 `58edc08965b73da31855298c63cde6b85d6d14d389cdeb97b09d2cf451aa3be2`
re-measured AFTER all verifier activity — unchanged (verifier non-interference proven).

| # | match_id | result | chosen_leg | pnl_cents | equity_after | source_ref (head) |
|---|----------|--------|-----------|-----------|--------------|-------------------|
| 43 | FD-2026-M37 | DRAW | DRAW (WIN) | +11253 | 113468 | polymarket_uma event=1167584 winner=DRAW markets=5528995/5528996/5528997 resolvedBy=0x69c47De9D4D3… uma=resolved fetched_at=2026-10-20T01:41:21Z |
| 44 | FD-2026-M40 | AWAY | HOME (LOSE) | −1022 | 112446 | polymarket_uma event=1172232 winner=AWAY markets=5575001/5575003/5575005 … |
| 45 | FD-2026-M36 | HOME | HOME (WIN) | +2769 | 115215 | polymarket_uma event=1172241 winner=HOME markets=5575144/5575145/5575146 … |
| 46 | FD-2026-M39 | HOME | AWAY (LOSE) | −1022 | 114193 | polymarket_uma event=1172245 winner=HOME markets=5575190/5575191/5575192 … |
| 47 | FD-2026-M42 | AWAY | HOME (LOSE) | −1022 | 113171 | polymarket_uma event=1172249 winner=AWAY markets=5575236/5575237/5575238 … |
| 48 | FD-2026-M38 | HOME | HOME (WIN) | +324 | 113495 | polymarket_uma event=1172253 winner=HOME markets=5575282/5575283/5575284 … fetched_at=2026-10-20T01:52:46Z |

Round-6 net **+11280c**; equity 102215c → **113495c**; program settlement total +13495c over
genesis 100000c. Open WSL bets **0**, exposure **0c**.

## Findings

- **F-1 (MED, environment — not this delta, not the verifier): owner live instances ABSENT at
  verification time.** Dispatch live-context says PaperDesk pid ~55580 + child runner ~55611 are
  running the real plane. Measured: neither pid exists; no PaperDesk/ops_service/Electron paper
  process at all; nothing listening on 127.0.0.1:8791 (`curl` → HTTP 000); no process holds
  `ops/service.lock` (file present but 0 bytes, mtime Oct 8; `lsof +D` over the data root is
  empty). Consequently three end-state sub-claims (pids ALIVE, opslock HELD by 55611, API
  open_count 0 via GET) are **NOT_RUN**, and I confirm I sent no signal to anything (all probes
  read-only: ps/lsof/curl-GET/file reads). Impact on the audit: none — the settlement outcome is
  recorded evidence, verified against the pinned chain AND independently against live Gamma; the
  dispatch itself notes zero open WSL bets make the in-memory WSL branch inert. open_count=0 and
  exposure=0 were re-derived offline from the chain-verified ledger. Owner should simply observe
  whether they closed the app, and restart it when desired.
- **F-2 (LOW, claim-text label): dispatch "M42 AWAY/LOSE"** — the ledger shows M42
  chosen_leg=HOME, result=AWAY → LOSE −1022. Under the chosen-leg reading that makes M40
  "HOME/LOSE" and M39 "AWAY/LOSE" correct, M42's label should be "HOME chosen / AWAY result".
  Money and WIN/LOSE outcome identical (−1022); presentation slip in the dispatch packet only.
- **F-3 (LOW, commit-message figures): "equity 100000c->113171c … prior +22215c program pnl"**
  does not match the ledger. Measured: pre-round-6 equity 102215c (= 100000 + 2215 prior
  settlements), final 113495c. 113171c is the INTERMEDIATE equity after the 5th settlement (M42)
  — the last settle (M38) landed at 01:52:46Z, after the prose was evidently drafted — and
  "+22215" appears to be a digit transposition of "+2215". The ledger itself is exact and
  chain-continuous; commit-message prose only.
- **F-4 (INFO): worktree `plans/CYCLE_REGISTRY.json` mirror stale** (head 9a18a4f2, updated
  2026-10-10) — established pattern (delta-5 F-2 INFO); the root registry is the writable
  authority and matches d790f7b7. No action.
- **F-5 (INFO): test_wsl_results.py has 11 tests, all passing** — the dispatch said "10/10".
  Coverage exceeds the claim; the extra test is the e2e sandbox settle through the pinned core.

## Provenance / boundaries

- I did NOT run: any settle pass, cmd_settle, e2e settle script, or anything that writes the real
  plane. The real ledger was read via the pinned paper_core `PaperLedger` only.
- Test runs (node batteries, pytest worktree suite, throwaway clone at 521d21ae under /tmp) are
  sandboxed and were proven non-interfering (ledger sha before == after).
- Live network: exactly one outbound GET (gamma-api.polymarket.com event 1167584) + one refused
  localhost GET. No keys used.
- Verifier artifacts live under /tmp/a7r6/ only (audit scripts, pinned-body diffs, failure lists,
  Gamma payload copy); this file is the only control-plane artifact written.
