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
