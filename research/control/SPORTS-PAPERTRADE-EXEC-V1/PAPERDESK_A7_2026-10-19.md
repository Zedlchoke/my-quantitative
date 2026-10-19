# PAPERDESK A7 INDEPENDENT VERIFICATION — 2026-10-19

Verifier: A7 (independent, fresh context). Delivery: PaperDesk.app (macOS UI +
lifecycle controller) under AMENDMENT_MACOS_APP_UI_V1, cycle
SPORTS-PAPERTRADE-EXEC-V1.
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`
(branch `orca/spt-exec-v1-integration`, HEAD `c61f7879`).
Data root: `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1`.
Verifier repaired nothing, started/stopped nothing, pushed nothing, and
modified no source file (the only file written is this audit artifact).

## VERDICT: VERIFY_PASS_WITH_FINDINGS

0 CRIT / 0 HIGH / 1 MEDIUM / 1 LOW / 3 INFO. All critical laws hold: ledger
non-interference (chain parity across Python and the packaged binary, no app
write path into any ledger), live-execution seal (no order surface), secrets
(git-clean, keychain-only), batteries reproduce (6/6 pytest, 14/14 node),
evidence artifacts present, and the machine is at the owner-law end state.

---

## Per-check table

| # | Check | Command (abridged) | Result |
|---|-------|--------------------|--------|
| 1 | Governance files exist | `ls` on AMENDMENT_MACOS_APP_UI_V1.md, PAPERDESK_DECISION_PACKET_2026-10-19.md, TOOLCHAIN_BLOCKER_NOTE.md, GO_TOKEN.json, apps/paperdesk/{RUNBOOK.md, build_app.sh, e2e_evidence.sh, e2e_lifecycle.sh, test_ai_seam.js, main/main.js} | EXIT=0 — all 10 present |
| 1 | Registry row | read `plans/CYCLE_REGISTRY.json` row SPORTS-PAPERTRADE-EXEC-V1 | `go_phrase = "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER"`; `go_phrase_state` starts `REGISTERED_NOT_CONSUMED (registered 2026-10-10T03:45:02Z …)` — PASS |
| 1 | GO_TOKEN unchanged | read `GO_TOKEN.json` (sha256 `69027c34…`) | `go_phrase_typed_by_owner = "GO SPORTS PAPERTRADE EXEC V1 RUN ALL"` (consumed 2026-10-07, per note) — meaning unchanged — PASS |
| 1 | App consumed no phrase | `grep -rin "go_phrase\|GO_TOKEN\|CYCLE_REGISTRY\|REGISTERED_NOT_CONSUMED" apps/paperdesk/{main,renderer,helpers,…}` | Only DISPLAY strings: `renderer/index.html:27` (static banner) and `renderer/app.js:602` (`'…REGISTERED_NOT_CONSUMED (not typed here)'`). No consumption logic anywhere — PASS |
| 2a | Pinned ledger verifier | `python -c "…from research.papertrade import ledger as L; …"` (pinned path `sports-papertrade-v1` worktree) | stdout `True 42`, EXIT=0 — PASS |
| 2b | Row-type census | python counter over `ledger/paper_ledger.jsonl` | 42 rows: GENESIS 1 / FORECAST 13 / MARKET_QUOTE 11 / DECISION 13 / SETTLEMENT 4; forbidden types: none — PASS |
| 2c | No app ledger write path | `grep -rn "paper_ledger" apps/paperdesk/main/` → ledger.js:17, main.js:92,114 (path construction only); ledger.js uses only `readFileSync`/`statSync` (`parseLedger` read-only projection). `grep -rn "appendFileSync\|writeFileSync" main/` → 10 hits, every target enumerated below | No target under `ledger/` or `sandbox_ledger`: ai.js→`<dataRoot>/ai_review/{opinions,index.jsonl}`; market.js→`<dataRoot>/pm_ui_snapshots/`; runner.js→`ops/control/{controller_log.jsonl,pause_decisions.flag,takeover.json}`; main.js→Electron `userData/window_close_policy` + UI-evidence PNG dirs — PASS |
| 2d | Chain parity via packaged app | `…/PaperDesk.app/Contents/MacOS/PaperDesk --self-check-ledger ~/.my-quantitative-data/…/paper_ledger.jsonl` | `{"rows":42,"sandbox":false,"chain_ok":true,"verified_rows":42,"errors":[],"parse_error":null}` EXIT=0 — exactly matches Python `True 42` — PASS |
| 3 | No order surface | greps over `main/ renderer/ helpers/` | `order`: display text / sort arrays / seal.js docs only. `POST`: ONLY `main/ai.js:185` (Z.ai `api.z.ai/api/paas/v4/chat/completions`) + comment strings. `authorization`: ONLY `main/ai.js:190` (`Bearer` from keychain). `clob.polymarket.com/order`: zero hits. `gamma-api.polymarket.com`: market.js:62,140 — both inside `https.get` (GET only). `main/seal.js` contains frozen `LIVE_EXECUTION_SEAL` (statement "LiveExecution: SEALED (no order path, no credentials, no endpoints)"; `submit()` throws; zero network code) — PASS |
| 4 | Secrets | `git grep -inE "sk-[a-z0-9]{20}\|Bearer [A-Za-z0-9]{20}" -- apps/paperdesk` (+ broadened variant) | EXIT=1 both — nothing. `ai.js:104-111`: key enters ONLY via `spawnSync('/usr/bin/security', ['find-generic-password','-s','com.myquant.paperdesk','-a','zai-api-key','-w'])` — PASS (see F3 for keychain absence) |
| 5a | pytest battery | `…/.venv/bin/python -m pytest tests/papertrade_exec/test_ui_control_seam.py -q` | `6 passed in 7.70s`, EXIT=0 — PASS |
| 5b | node AI seam battery | `cd apps/paperdesk && node test_ai_seam.js /tmp/a7_ai_evidence` | `ai seam: 14/14 pass`, EXIT=0 — PASS. (e2e_evidence.sh / e2e_lifecycle.sh deliberately NOT re-run; recorded evidence verified below) |
| 6 | UI PNGs | python inventory of `apps/paperdesk/build/e2e_evidence/ui/*.png` | 7 PNGs, 253,616–375,759 bytes, all >100KB — PASS |
| 6 | Tamper UI evidence | `ls build/e2e_evidence/ui_tamper/` | `paperdesk_section_dashboard.png` present (141,246 B, valid 2560x1578 PNG) — PASS. Bonus: all 6 section PNGs byte-identical (md5 `0662e4ed…`) = same fail-closed render on every section; tamper ledger verified broken (`chain_ok False, row 1 hash mismatch`) and packaged app reports `chain_ok:false` on it |
| 6 | Controller log events | python census of `ops/control/controller_log.jsonl` (217 rows) | APP_LAUNCH 21, ATTACH 12, SPAWN_CHILD 9, CHILD_READY 9, GRACEFUL_STOP_BEGIN 11 (all reason `app-quit`), LAUNCHD_BOOTOUT 5, PAUSE_ON 4 / PAUSE_OFF 4, UI_EVIDENCE_TOUR 4 — all required classes PRESENT. ATTACH sources: 10 `launchd` + 2 `external`, 0 `child` (see F2). GRACEFUL_STOP_BEGIN includes 5 rows with `source:'child'` |
| 6 | takeover.json | cat | exists: `{"at_utc":"2026-10-19T11:31:37Z","by":"PaperDesk.app","trigger":"quit","launchd_label":"com.myquant.sptexec.ops",…}` — PASS |
| 6 | incidents.jsonl | python census by `kind` (3,254 rows) | SERVICE_START 35, SERVICE_STOP 34 present; `DECISIONS_PAUSED_BY_UI` = 0 rows on the real plane (see F1). Compensating: sandbox e2e incidents.jsonl line 7 contains `{"kind":"DECISIONS_PAUSED_BY_UI", "detail":"{\"by\": \"e2e\", \"reason\": \"E-pause\"…}", "ts_utc":"2026-10-19T11:33:41Z"}` — the UI-flag→service-journal pathway is proven end-to-end |
| 6 | End-state machine | see dedicated section below | owner-law end state CONFIRMED |
| 7 | App bundle | `ls`, `codesign --verify --deep --strict`, PlistBuddy | bundle exists; codesign EXIT=0; `CFBundleIdentifier = com.myquant.paperdesk`; `LSUIElement` Does Not Exist (regular Dock app); `Contents/Resources/app/{main(7 modules), renderer(5), helpers/opslock.py}` present. `diff -r` main/, renderer/, opslock.py vs worktree: IDENTICAL — PASS |
| 8 | AI shadow isolation | `grep -rn "ai_review\|AIService\|AIReview" research/papertrade_exec/*.py` | EXIT=1 — zero references (guard holds). `ai.js:48-49`: opinions/index only under `<dataRoot>/ai_review/` — PASS |

## Findings

- **F1 [MEDIUM] `DECISIONS_PAUSED_BY_UI` never journaled on the REAL plane.**
  `ops/state/incidents.jsonl` (real) has 0 PAUSED rows vs 14 RESUMED. Root
  cause (verified by reading `research/papertrade_exec/ops_service.py`
  `_pause_watch`): the event fires only when the RUNNING service observes the
  flag across a tick; on the real plane every PAUSE_ON→PAUSE_OFF pair lasted
  ~1s (ui-evidence tour, controller_log 10:29:30Z…11:42:52Z), shorter than the
  service observation tick, and `_last_pause_state=None` makes a clean service
  start emit RESUMED. The pathway itself is proven: sandbox e2e
  (`build/e2e_evidence/sandbox_root/.../incidents.jsonl` 11:33:41Z,
  reason `E-pause`) shows the full flag→incident chain, and the app-side
  PAUSE_ON/PAUSE_OFF audits exist on the real plane. Not a control gap (the
  flag gates cadence fail-closed either way); it is an evidence-completeness
  gap vs the check text as written. Suggested (non-blocking) improvement: hold
  the pause flag for >1 tick in the evidence tour, or have `_pause_watch` run
  at a sub-tick interval.
- **F2 [LOW] No `ATTACH` audit row with `source:'child'`.** Real controller
  log ATTACH rows are 10x `launchd` + 2x `external`. Child-source attachment
  is instead evidenced by `CHILD_READY` (9), `GRACEFUL_STOP_BEGIN`
  `source:'child'` (5), and the sandbox e2e lifecycle
  (SPAWN_CHILD→CHILD_READY→GRACEFUL_STOP_BEGIN→CHILD_EXIT→GRACEFUL_STOP_END).
  `runner.js pollOnce()` skips the ATTACH audit when `startRunner` already set
  state directly — cosmetic audit-naming gap, not a control gap.
- **F3 [INFO] Z.ai key absent from Keychain at audit time**
  (`security find-generic-password -s com.myquant.paperdesk` → item not
  found). The app correctly fail-closes: entitlement
  `NOT_RUN_AI_RUNTIME_ENTITLEMENT`, mock-only mode (test battery asserts this).
  Shadow-GLM live path is therefore unexercised on this machine — by design
  when no entitlement exists. Code path verified: the key can ONLY enter via
  `/usr/bin/security`.
- **F4 [INFO] 2 `UNCAUGHT_EXCEPTION` rows** in the real controller log
  (11:24:14Z, 11:31:38Z): `TypeError: Object has been destroyed` — Electron
  teardown race during quit (IPC timer firing after window destruction).
  Benign; recommend guarding the broadcast/setInterval handlers at quit.
- **F5 [INFO] Off-by-one in tamper row index between implementations**: Python
  verifier reports `row 1: hash mismatch`, packaged app reports
  `row 0: row_sha256 mismatch` for the same tampered row (0-based vs 1-based
  index). Same row detected, both fail closed; cosmetic.

## End-state machine observation (owner law)

Observed 2026-10-19 ~19:0x local, after the delivery round:

| Probe | Command | Observation |
|-------|---------|-------------|
| launchd agent | `launchctl print gui/$(id -u)/com.myquant.sptexec.ops` | `Could not find service "com.myquant.sptexec.ops" in domain for user gui: 501`, exit 113 → NOT loaded |
| runner process | `pgrep -fl ops_service` | no match (exit 1); re-checked with `ps aux \| grep "[o]ps_service"` → empty |
| service lock | `python apps/paperdesk/helpers/opslock.py probe ~/.my-quantitative-data/sports-papertrade-exec-v1/ops/service.lock` | `FREE`, exit 0 |
| pause flag | `ls ops/control/` | absent (only `controller_log.jsonl`, `takeover.json`) |
| app instance | `pgrep -fl PaperDesk.app` | no match (exit 1) |
| ledger | `shasum -a 256 paper_ledger.jsonl` | `899c0ad3…`, mtime Oct 18 07:10 — untouched throughout the Oct 19 app round and this audit |

Machine state is exactly the owner-law end state: runner lifecycle follows the
app (launchd KeepAlive booted out, `takeover.json` trigger=`quit`), nothing
left running, lock free, ledger frozen and verified.

## Scope notes for the integrator

- Working tree at audit time: `apps/paperdesk/` untracked (whole delivery) and
  `research/papertrade_exec/ops_service.py` modified (+48/-1: the runner-side
  pause-flag seam, `pause_flag_payload` / `decisions_paused` /
  `_pause_watch`). Both are this round's working state; commit discipline is
  the integrator's call, not the verifier's.
- `e2e_evidence.sh` / `e2e_lifecycle.sh` were NOT re-run (per instructions:
  they mutate the real runner lifecycle). Their recorded evidence under
  `apps/paperdesk/build/e2e_evidence/` was verified instead (PNG sets, sandbox
  controller log, sandbox incidents, tamper ledger + fail-closed UI renders).
