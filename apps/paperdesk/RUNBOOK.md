# PaperDesk — RUNBOOK (macOS UI + lifecycle controller)

Cycle: `SPORTS-PAPERTRADE-EXEC-V1` · Amendment: `AMENDMENT_MACOS_APP_UI_V1`
Scope: paper money ONLY. Live trading is SEALED (no path, no phrase, no key).
Stack: **Electron** (SwiftUI blocked by a broken CLT toolchain — see
`research/control/SPORTS-PAPERTRADE-EXEC-V1/TOOLCHAIN_BLOCKER_NOTE.md`).

## 1. Install & run

```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration
./apps/paperdesk/build_app.sh          # one command → build/PaperDesk-darwin-arm64/PaperDesk.app
open apps/paperdesk/build/PaperDesk-darwin-arm64/PaperDesk.app
```

Requirements: macOS 13+ (built on 15.4, arm64), node+npm for the build,
the repo's `.venv` python (hard path in main/runner.js), local filesystem
access to the data root `~/.my-quantitative-data/sports-papertrade-exec-v1`.

## 2. Lifecycle (owner law, encoded)

| Action | Behavior |
|---|---|
| Open app | Probes the runner: attaches to a live one (heartbeat+flock) or starts EXACTLY ONE child `ops_service`. Refuses to spawn into a held lock. |
| Launchd-managed runner found | Shows "TAKE OVER" — one click bootouts `com.myquant.sptexec.ops` (kills RunAtLoad/KeepAlive auto-start) and respawns the runner as the app's child. Takeover is journaled (`controller_log.jsonl`, `takeover.json`). |
| Close window | Asks (default): **Pause decisions** (flag `ops/control/pause_decisions.flag` — new forecast/quote/decision stop; settlement+dashboard CONTINUE) or keep running. App stays in Dock. |
| Quit (⌘Q) | Confirm dialog → graceful SIGTERM with identity verification (pid + process-start token + our data root; a recycled/foreign PID is never signaled) → waits for exit + lock release → app exits. If ANY step cannot be verified (bootout failure, lock still held, identity lost), Quit is REFUSED: the app stays open with an error. Open bets stay OPEN; missed in-scope windows (today..+2) are journaled as `MISSED_WINDOW_ANCHOR_PASSED` incidents at next start — incidents only, never ledger rows, never backfilled. |
| Not run at login | After takeover, nothing auto-starts at login; paper runs only while the app runs (or while a previously spawned child survives an app crash — it is re-adopted on relaunch). |
| Second app instance | Refused (app.lock flock) with a dialog. Second runner instance: refused by the runner's own `service.lock` (exit 3). |

## 3. What the app can and cannot do

CAN: read the ledger (byte-exact chain verify on every load, fail-closed
tamper banner), read `/api/state` (GET-only) for service health, fetch PM
Gamma/CLOB **public read-only** data with raw-response+sha256 journal under
`<data-root>/pm_ui_snapshots/`, record AI opinions to `<data-root>/ai_review/`,
pause/stop the runner.

CANNOT: write the ledger, place orders (no endpoint, no credentials —
`LiveExecution` is a sealed type), let AI affect decisions (SHADOW sidecar
only), consume any GO phrase, change any pinned number.

## 4. AI runtime (OpenRouter free chain — GLM/Z.ai STOPPED by owner)

- 2026-10-20 owner order: **stop Z.ai API probes** (account insufficient
  balance — recorded probe: HTTP 429 errCode 1113). The live SHADOW provider
  is now **OpenRouter's free model chain**, ranked by evidence from the live
  models listing (artifact: `ai_review/model_ranking.json`, sources:
  openrouter.ai/api/v1/models + openrouter.ai/docs).
- Ranked chain (fallback on 429/quota/5xx/timeout/unavailable; ONE bounded
  retry per model; deadline enforced between attempts):
  1. `minimax/minimax-m3.1-flash:free` — **live-verified 2026-10-20: HTTP
     200, strict JSON round-trip, $0**
  2. `google/gemma-4-31b-it:free`
  3. `nvidia/nemotron-3-ultra-550b-a55b:free`
  4. `thinkingmachines/inkling:free`
  5. `openrouter/free` (auto-router, last resort)
- Key: macOS Keychain `com.myquant.paperdesk / openrouter-api-key` — never
  logged, never rendered; only an HTTP Authorization header to
  openrouter.ai. OpenCode: NOT required (a suitable free hosted API exists
  via OpenRouter).
- Durable no-autostart: `launchctl disable gui/$(id -u)/com.myquant.sptexec.ops`
  recorded 2026-10-20 (evidence: paperdesk_evidence_2026-10-19/
  launchd_disabled_2026-10-20.txt) — even a re-login will NOT auto-start
  the supervisor; paper runs only when the app (or the owner) starts it.
  Re-enable: `launchctl enable gui/$(id -u)/com.myquant.sptexec.ops`.
- Failure law: every model fails ⇒ opinion `ALL_PROVIDERS_FAILED` with
  verdict **ABSTAIN** and a full per-attempt journal (provider/model/http/
  fallback reason); deadline aborts chain ⇒ `TIMEOUT_LATE_INVALID`.
- AI automation = tested machinery (37→43-check seam); scheduler IDLE while
  mode is disabled-no-entitlement. AI remains SHADOW: opinions are advisory
  evidence with zero effect on the paper pipeline; evidence is
  SYSTEM-CAPTURED (team-name match, NOT fixture-authenticated).

## 5. CLI modes (for e2e + A7, no UI needed)

```
PaperDesk.app/Contents/MacOS/PaperDesk --self-check-ledger <ledger.jsonl>
    # prints {"chain_ok":...,"rows":...} — diffable vs Python verify_chain
    # extra flags: --sandbox --data-root P --auto-quit N --ui-evidence DIR
```

## 6. Verification already run (see A7 file for the independent pass)

- `tests/papertrade_exec/test_ui_control_seam.py` — 6/6 PASS (pause flag:
  cadence-only gate, corrupt-flag fail-closed, transition journal, ledger
  byte-invariance while paused).
- `apps/paperdesk/test_ai_seam.js` — 26/26 PASS (round-2: anchor-law deadlines, auto-scheduler idempotence, evidence verification law, API fail-closed) (entitlement gate, MOCK
  labeling, deadline law, malformed/prompt-injection fail-closed,
  auto-ABSTAIN no-source law, sidecar store).
- `apps/paperdesk/e2e_lifecycle_safety` (test_lifecycle_safety.js) — 13/13 PASS (identity/lstart/data-root guards, PID-reuse refusal, unexplained-lock refusal, bootout-failure fail-closed)
- `apps/paperdesk/e2e_evidence.sh` — 19/19 PASS (chain parity vs pinned
  Python on the REAL ledger, attach, second-instance refusal, crash
  recovery, sandbox lifecycle incl. pause flag + graceful quit, tamper
  fail-closed + UI banner evidence, AI seam, UI screenshots).
- `apps/paperdesk/e2e_lifecycle.sh` — 12/12 PASS on the REAL runner
  (attach launchd → quit → bootout + graceful stop + takeover record →
  reopen spawns app-owned child → second graceful stop; fresh-journal
  checks, launchd absent at the end: nothing auto-runs at login).
- UI evidence PNGs: `apps/paperdesk/build/e2e_evidence/ui/` (all six
  sections + paused state, real ledger data) and `ui_tamper/` (tamper
  banner).

## 7. Troubleshooting

- "ledger file not found": wrong `--data-root`; default is
  `~/.my-quantitative-data/sports-papertrade-exec-v1`.
- Runner state gray: check `ops/state/heartbeat.json` age; stale >180 s
  raises the stale alarm in the UI.
- Chain FAILED banner: DO NOT ignore — someone/something touched
  `paper_ledger.jsonl`; the app withholds all financials by design.

## 8. PAPERDESK-FIXALL-NCAA-V1 — settlement plane laws (W0, 2026-10-21)

- **Team identity (W0.1):** every settle identity check goes through
  `research/papertrade_exec/team_names.py` — ONE normalization
  (casefold + strip non-alnum) + the sha-pinned `TEAM_NAME_CROSSWALK.csv`
  (30 NBA + 15 WNBA teams measured from real journaled ESPN payloads and the
  pinned WNBA schedule; pin `data.team_name_crosswalk_csv` in pins.json).
  Unknown names are fail-closed: the bet stays OPEN + incident, never a
  guess. The old `abbreviation != full name` compare (root cause of the two
  live-stuck NBA bets) is gone; the three old normalizers now delegate to
  `team_names.norm`.
- **Settle retry cadence (W0.2):** the due queue is rebuilt from the ledger
  EVERY tick — a failed attempt never removes a bet from the row; only the
  per-source throttle paces network (ESPN 30 min, soccer /scores 6 h).
  Every attempt is journaled to `ops/state/settle_attempts.jsonl`.
  Measured goal: an NBA/WNBA bet settles ≤ 3 h after the match ends
  (SETTLE_GRACE_HOURS stays 3: first lawful attempt ≈ end+0.5 h).
- **Stuck alarm / dead-letter (W0.3):** OPEN past (estimated end + 6 h)
  → `SETTLE_STUCK_ALARM` incident + dashboard stuck queue; past
  (estimated end + 48 h) → `SETTLE_DEAD_LETTER` (still OPEN in the ledger,
  labeled + aged). Only the owner resolves a dead-lettered bet, via
  `python -m research.papertrade_exec.ops_service --resolve-stuck <ID>
  --resolution-results FILE` AFTER placing
  `ops/control/owner_resolution_token.json` ({by, at_utc, note}); settlement
  runs the NORMAL pinned settle path — no direct ledger write exists.
  Settled bets' ghost keep-open reasons are pruned from
  `settle_last_why.json` immediately.
- **WSL DRAW identity (W0.4):** the DRAW leg is identity-ok when the EVENT
  pairs both team names and the market id comes from the bet's own quote
  row (PM phrases DRAW markets without a date). One-of-three UMA + ambiguity
  refusals unchanged.
- **Soccer void path (W0.5):** a match past kickoff+grace standing OUTSIDE
  the stage law settles VOID (refund per `settlement_refund_results`)
  through the normal settle path with the stage refusal as source_ref.
- **ESPN scan window (W0.6):** scoreboard scan covers [D−1, D+2] around the
  ledger kickoff date; postpone/cancel recognition reads the structured
  `status.type.name`/`state` fields in addition to description text; a FINAL
  event on a different board day is reported as rescheduled (kept OPEN).
- W0 acceptance evidence:
  `research/control/PAPERDESK-FIXALL-NCAA-V1/evidence/W0_ACCEPTANCE_REPLAY_2026-10-21.json`
  (both live-stuck NBA bets settle via the normal path on a byte-copy
  ledger, chain OK, production untouched).

## 9. PAPERDESK-FIXALL-NCAA-V1 — quota/decision-path laws (W1, 2026-10-21)

- **Inactive sport keys (W1.1):** a registered soccer key whose
  `competition_law` has no window covering the requested date polls /events
  at most ONCE per UTC day (state `data/soccer_key_poll.json`). The 404ing
  `soccer_fifa_world_cup_group` key drops from ~230-280 calls/day to ≤1.
- **Provider-credit meter (W1.2):** every credit call runs through
  `quota_guard.GuardedClient` — provider-unit daily/monthly caps
  (4/day + 120/month, basketball /odds = 2 credits measured), a
  `data/provider_quota_ledger.jsonl` journal of the provider meter
  (x-requests-used/remaining), and `QUOTA_CREDIT_DRIFT` reporting when the
  meter moves more than expected. Pinned bytes untouched.
- **Constant forecast (W1.3):** root cause measured — refresh lookback 0 ⇒
  zero FINAL rows ⇒ R0=1500 cold start ⇒ pure-HCA p=0.640065 for every
  match (all 14 live NBA forecasts). Fix: refresh now walks back
  `nba_refresh_lookback_days` (config, 14); decide path permanently blocks
  a zero-variance batch (`BLOCKED_CONSTANT_FORECAST`, whole batch, high
  incident). NBA stays paused per owner QĐ1 until the root cause + block
  are on the production runner.
- **Quote collision (W1.4):** one snapshot must never price two fixtures —
  identical non-trivial `payload_sha256`, or (PM-family rows only) exact
  float equality of the full odds vector ⇒ `NOT_RUN_QUOTE_COLLISION`
  terminal on BOTH the standard and the WSL decide path. Coarse bookmaker
  prices (1.85/2.05) legitimately repeat and are never a collision.
- **EV outlier quarantine (W1.5):** EV_net > 100% (`laws.
  EV_OUTLIER_THRESHOLD`) ⇒ mandatory second-source PM cross-check;
  second source agrees ⇒ `NOT_PLACED_EV_OUTLIER` terminal; disagrees ⇒
  `QUARANTINED_EV_OUTLIER` (non-terminal — re-entry ONLY against a quote
  captured after the quarantine; 3 quarantines ⇒ terminal). The 5% gate is
  untouched.
- **One constant law source (W1.6):** `research/papertrade_exec/laws.py`
  is the single source for EV threshold, drawdown pause, fees, outlier
  threshold, stake-law constants, anchor leads; the JS mirrors consume the
  GENERATED `apps/paperdesk/main/laws_generated.js`
  (`python research/papertrade_exec/build_laws_js.py`; parity-tested).
- **Incident hygiene (W1.7):** identical repeating failures collapse into
  ONE incident + counter + first/last (+ close-out when quiet);
  `DASHBOARD_REBUILT` moved to the metrics plane
  (`ops/state/metrics.jsonl`); the pause flag's first observation after a
  (re)start is silent unless the service started ALREADY paused (the 30
  RESUMED vs 4 PAUSED noise was one spurious row per process start);
  startup fail-fasts on missing required pin files (the 2026-10-09
  446-row TICK_ERROR storm). Crash-loop 2026-10-19 root cause: app
  relaunch churn (36 app boots, launchd bootouts, e2e lifecycle testing) —
  NOT a Python crash loop (2 uncaught exceptions total, all stops
  graceful).

## 10. PAPERDESK-FIXALL-NCAA-V1 — speed + one surface + visibility (W2, 2026-10-21)

- **Incremental ledger (W2.1):** the ops supervisor verifies the whole
  chain ONCE per process (`ops_service.VerifiedLedgerView`), then pays only
  for appended rows (prev-sha linkage) with an hourly full re-verify and an
  immediate full re-verify on shrink/parse anomaly — any inconsistency is
  TAMPER, fail-closed. The Electron app got the same law (`ledger.js`):
  first read full-hash, afterwards read+verify only appended bytes; a chain
  failure is NEVER cached. Old-path == new-path parity is battery-tested.
- **Parallel leagues (W2.2):** cadence chains run concurrently per league
  (worker pool ≤ 4); the settle pass always runs first in the tick. The
  pinned append refuses a stale tail by law; concurrent chains converge via
  an idempotent retry with backoff (`CADENCE_TAIL_DRIFT_RETRY`). The
  restart battery also exposed a nondeterministic in-process relaunch
  refusal (GC-timed lock release) — `run_forever` now releases the
  single-instance flock explicitly.
- **One surface (W2.3):** the Electron app is the ONLY rendering surface.
  The live_dashboard HTML page is REMOVED; `127.0.0.1:8791/` returns a
  JSON note and `/api/state` remains the state API (same builder, same
  ledger — no parallel number sources).
- **Four desk blocks (W2.4):** the dashboard (Electron + the same state
  API) now shows: (1) STUCK / DEAD-LETTER queue (from `stuck_state.json` +
  `settle_last_why.json`), (2) CLOSING LINE VALUE — captured at settle time
  into the append-only `ops/state/clv_records.jsonl` (law: the closing
  price is the bet's own league quote nearest kickoff; `clv = bet/close − 1`;
  no pre-tip quote ⇒ NO_CLOSE_PRICE, never inferred), (3) the per-league
  table (matches, BET/NO_EDGE/NO_QUOTE/other, PnL, CLV), (4) per-league
  health cards (last forecast/quote/decide ok/blocked, upcoming window
  count, provider-credit quota, lane flags incl. WSL STALE_CORPUS).
