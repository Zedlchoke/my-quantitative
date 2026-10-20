# PAPERDESK A7 — ROUND-4 DELTA VERIFICATION (2026-10-20)

- Verifier: A7, independent, fresh context. ONE artifact (this file); repaired
  nothing; started/stopped nothing; mutated no lifecycle.
- Target: `d19f559c81f81a606bbd743c4344f194b3f1fb55` (parent `0c049c67`),
  branch `orca/spt-exec-v1-integration`, worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`.
- Scope guard honored: `e2e_lifecycle.sh` / `e2e_evidence.sh` NOT_RUN by
  instruction — relied on their recorded results (RUNBOOK §6: 12/12, 19/19,
  earlier rounds; runner untouched this round).
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
- Live AI calls: ZERO by A7. The only network call made was the public,
  no-auth models listing (claim 4), as authorized. The Keychain key was never
  read, never displayed.

## VERDICT: VERIFY_PASS_WITH_FINDINGS

0 CRIT / 1 MED / 2 LOW / several INFO. All MED+LOW are presentation or
environment/residual items — none is in the live decision path, none
invalidates the round-4 owner-order implementation. Code, tests, evidence
artifact, registry, ledger, and bundle all reconcile.

## Claim-by-claim

| # | Claim | Command(s) | Result | Verdict |
|---|-------|------------|--------|---------|
| 1a | Z.ai tokens gone from live path | `grep -rn "api.z.ai\|zaiCall\|glm-5.3-flash\|z.ai-general-api" apps/paperdesk/main/ apps/paperdesk/renderer/` | exit 1 — ZERO matches | CONFIRMED |
| 1b | Z.ai mentions only as stop-record | broader `grep -rni "z\.ai\|zai\b\|zhipu" apps/paperdesk/` (code files) | only: ai.js comments/notes "Z.ai probes STOPPED by owner (2026-10-20)", main.js:114 "GLM/Z.ai live: STOPPED by owner (insufficient balance, HTTP 429 errCode 1113)", RUNBOOK §4 stop-record. **Plus stale renderer UI text — see F-1** and legacy test fixture (INFO-1) | CONFIRMED (stop-records only in main/) |
| 1c | Packaged ai.js has NO api.z.ai | `grep -c "api.z.ai" …/PaperDesk.app/Contents/Resources/app/main/ai.js` | 0 | CONFIRMED |
| 2a | Chain pinned order | read `main/ai.js` L49–55 | `OPENROUTER_FREE_CHAIN = [minimax/minimax-m3.1-flash:free, google/gemma-4-31b-it:free, nvidia/nemotron-3-ultra-550b-a55b:free, thinkingmachines/inkling:free, openrouter/free]` — exact dispatch order | CONFIRMED |
| 2b | 429/402 quota → next, no retry | read `openrouterCall` L608–620 | `fallback_reason='quota/limit — falling back'`, then `break` → next model (no retry branch taken) | CONFIRMED |
| 2c | 5xx → ONE bounded retry then next | same | `res.status >= 500 && attemptNo === 1 → continue` (retry once); attempt 2 → `break` | CONFIRMED |
| 2d | timeout/network → ONE retry then next | same, L593–598 | `res.err` branch: attempt 1 → `continue`; attempt 2 → `break` | CONFIRMED |
| 2e | 404/400 unavailable → next | same | `'model unavailable/invalid — falling back'` then `break` | CONFIRMED |
| 2f | Deadline enforced BETWEEN attempts → TIMEOUT_LATE_INVALID + ABSTAIN | L572–584 | check `Date.now() > deadlineMs - 1000` before EVERY attempt; abort journals the skipped attempt, sets `TIMEOUT_LATE_INVALID` + `verdict ABSTAIN` | CONFIRMED |
| 2g | Whole chain fails → ALL_PROVIDERS_FAILED + ABSTAIN + journal | L622–632 | `status='ALL_PROVIDERS_FAILED'`, `verdict='ABSTAIN'`, `op.attempts` = full journal (provider/model/attempt/http/elapsed_ms/error/fallback_reason); tests assert all three | CONFIRMED |
| 2h | 200 → parse; systemCaptured law carried; zero captured → ABSTAIN | `parseZAIResponse` L636–697 | claimed sources recorded `systemCaptured:false, claimed_by_model:true`, discarded; `capturedCount===0 → verdict forced ABSTAIN` | CONFIRMED |
| 2i | 10-min budget constants unchanged | L58–59 | `MAX_BUDGET_SECONDS = 600`; `START_WINDOW_SECONDS = 15*60`; post-hoc late check also present in `runReview` | CONFIRMED |
| 2j | keychain account openrouter-api-key; key ONLY in Authorization header | L238–249, L509–534, L544; grep `key\|Authorization` in ai.js | `security find-generic-password -s com.myquant.paperdesk -a openrouter-api-key -w`; `key` appears at L511/L545 (presence checks) and L522 `'Authorization': Bearer ${key}` — no other use, no logging, not in op fields | CONFIRMED |
| 3 | Evidence artifact complete | read `paperdesk_evidence_2026-10-19/model_ranking_2026-10-20.json` | `retrieved_at_utc 2026-10-20T00:05:39Z`, `source_url https://openrouter.ai/api/v1/models`, 2 docs URLs, `source_sha256_full_payload`, 5 ranked entries each with evidence rationale + context_length + created + pricing prompt/completion "0"; chain == code chain | CONFIRMED |
| 4a | Live-verify claim recorded | RUNBOOK §4 diff + AMENDMENT §8 diff + decision packet diff (git show d19f559c) | all three record "live-verified 2026-10-20: HTTP 200, strict JSON round-trip, $0" for minimax-m3.1-flash:free | CONFIRMED |
| 4b | Cheap independent re-check (models listing only) | `curl -s --max-time 30 https://openrouter.ai/api/v1/models` (no auth, no key) | minimax/minimax-m3.1-flash:free STILL LISTED, pricing prompt='0' completion='0', ctx=1000000; ALL 5 chain ids listed, all 0/0; ctx+created match artifact exactly; 470 models total | CONFIRMED |
| 5a | ai seam 43/43 | `cd apps/paperdesk && node test_ai_seam.js /tmp/a7r4_ai` | **43/43 pass**, incl. visible PASSes: 429+5xx+retry → success on later chain entry; attempt journal; provider 'openrouter'; all-429 → ALL_PROVIDERS_FAILED+ABSTAIN; deadline abort → TIMEOUT_LATE_INVALID; missing key → fail-closed; rolling-window budget (fake clock); canonical candidates; systemCaptured relabel | CONFIRMED |
| 5b | lifecycle safety 13/13 | `node test_lifecycle_safety.js` | **13/13 pass** | CONFIRMED |
| 5c | UI control seam 8 passed | `pytest tests/papertrade_exec/test_ui_control_seam.py -q` | **8 passed** | CONFIRMED |
| 5d | Baseline failures unchanged in NAME-SET | `pytest tests/papertrade_exec/ -q` → **16 failed, 94 passed** — composition identical to the documented baseline (WSL_BET_PAPER_VERIFY §F + A7-DELTA3 5d): 15×test_exec_battery + 1×test_b1r_fail_closed | CONFIRMED (scoped). Full `tests/` tree additionally shows 7 failures in `tests/test_family_failures.py` — see F-2 (environment, not this delta) | CONFIRMED (scoped) |
| 6a | registry head == d19f559c == HEAD | root `plans/CYCLE_REGISTRY.json` SPORTS-PAPERTRADE-EXEC-V1; `git rev-parse HEAD` | head `d19f559c…` == HEAD; phase "GO_CONSUMED CAPTURE_ACTIVE LIVE_SERVICE_ACTIVE … round-4 at d19f559c…"; updated 2026-10-20T00:12:30Z | CONFIRMED |
| 6b | cutover phrase REGISTERED_NOT_CONSUMED | same registry entry | go_phrase "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER", state "REGISTERED_NOT_CONSUMED (registered 2026-10-10…)"; prior RUN ALL documented OWNER_GO_TYPED+CONSUMED 2026-10-07 | CONFIRMED |
| 6c | GO_TOKEN unchanged | `git log -- GO_TOKEN.json` → last commit **b250bfb1** (2026-10-07 consumption record); not in d19f559c file list | CONFIRMED |
| 6d | pinned ledger verifier True/42 | pinned-core `PaperLedger(<real ledger>).load(); verify_chain()` (pinned root = sports-papertrade-v1 worktree) | `True`, errors `[]`, **42 rows** | CONFIRMED |
| 6e | ledger mtime 2026-10-18 | `stat` `~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl` | Oct 18 07:10:54 2026 | CONFIRMED |
| 6f | launchd agent absent | `launchctl print gui/501/com.myquant.sptexec.ops` → "Could not find service … 501"; `launchctl list` no com.myquant entry | agent NOT loaded | CONFIRMED (residual plist-file note → F-3) |
| 6g | no ops_service / PaperDesk process | `pgrep -fl` both patterns | both empty (exit 1) | CONFIRMED |
| 6h | opslock probe FREE | `.venv/bin/python apps/paperdesk/helpers/opslock.py probe ~/.my-quantitative-data/sports-papertrade-exec-v1/ops/service.lock` | **FREE** (exit 0); lock file 0 bytes, Oct 8 | CONFIRMED |
| 6i | ai_review/opinions empty; model_ranking.json in DATA ROOT | `ls` data root | opinions/ = 0 files; `ai_review/model_ranking.json` present | CONFIRMED |
| 7a | delta touches no shadow/test/plan files | `git show d19f559c --stat` | exactly 7 files: RUNBOOK.md, main/ai.js, main/main.js, test_ai_seam.js, AMENDMENT §8, decision packet, model_ranking json — ZERO under research/papertrade*, tests/papertrade_exec, plans/ | CONFIRMED |
| 7b | runner has no OpenRouter awareness | `grep -rn "openrouter" research/papertrade_exec/*.py` | exit 1 — zero matches | CONFIRMED |
| 7c | ledger/risk/GO untouched | claims 6c/6d/6e re-verified post-round | verifier True/42, mtime Oct 18, GO_TOKEN at b250bfb1 | CONFIRMED |
| 8a | codesign OK | `codesign --verify --deep --strict build/PaperDesk-darwin-arm64/PaperDesk.app` | OK | CONFIRMED |
| 8b | packaged ai.js carries chain + fail law, no api.z.ai | greps on packaged ai.js | OPENROUTER_FREE_CHAIN ×5, ALL_PROVIDERS_FAILED ×2, api.z.ai ×0; packaged ai.js/candidates.js/main.js **byte-identical** to worktree; candidates.js present (3237 B) | CONFIRMED |
| 8c | self-check CLI on REAL ledger | `…/MacOS/PaperDesk --self-check-ledger <real ledger> --auto-quit 3` | `{"rows":42,"sandbox":false,"chain_ok":true,"verified_rows":42,"errors":[]}`; no process left afterwards | CONFIRMED |

## Findings

- **F-1 (MED, presentation only — renderer never updated):**
  `apps/paperdesk/renderer/app.js` L638–646 still shows the round-2/3 UI:
  the live button is labeled **"Z.ai SHADOW"**, the key-present text says
  **"General API key present in Keychain"**, and the key-absent text says
  **"no Z.ai General API key in Keychain (… account zai-api-key) … The
  Coding-Plan API is banned"**. Behavior is NOT affected — `ent.present` is
  computed in main from the OpenRouter key fingerprint, so enablement and
  mode flows are correct — but the user-facing guidance instructs storing a
  `zai-api-key`, which since round 4 has no effect. Related stale strings:
  `main/ai.js` setMode refusal "refused: no General API entitlement"
  (~L701); `main/main.js` automation label still cites "37/37 seam"
  (now 43/43; RUNBOOK correctly discloses "37→43"); RUNBOOK §6 is a
  historical list (6/6, 26/26 were true when written). Fix is renderer-text
  only; suggested for a future round.
- **F-2 (LOW, baseline scope / dispatch phrasing):** the dispatch said
  "full python suite baseline 16 pre-existing failures unchanged". Measured:
  scoped `tests/papertrade_exec/` = **16 failed / 94 passed, name-set
  identical** to the documented baseline. The FULL `tests/` tree additionally
  has **7 failures in `tests/test_family_failures.py`**
  (test_real_registry_validates + 6 core-signature params) caused by the
  SHARED ROOT checkout registry containing newer signature codes
  (`SCORED_REJECTION`, `NEGATIVE_EXPECTANCY`) unknown to this branch's pinned
  code — pre-existing environment drift, not attributable to d19f559c (the
  delta touches zero python/test files). Future dispatches should scope the
  baseline to `tests/papertrade_exec/` explicitly.
- **F-3 (LOW, residual, pre-existing, owner-domain):**
  `~/Library/LaunchAgents/com.myquant.sptexec.ops.plist` REMAINS INSTALLED
  (mtime Oct 8, `RunAtLoad=true`, `KeepAlive=true`, no `Disabled` key, no
  disabled-db entry). The service is not loaded today (claim 6f), but a
  **re-login will auto-load it and restart the ops supervisor** — "runner
  STOPPED by owner law" is not durable across login with this file present.
  Unchanged since Oct 8 and recorded identically in prior A7 rounds; flagged
  here so the owner can `launchctl disable` / remove the plist if the stop is
  meant to be durable. A7 repairs nothing.
- **INFO-1:** `apps/paperdesk/test_ai_seam.js:67` keeps legacy fixture fields
  `model:'glm-5.3-flash', provider:'z.ai-general-api'` in a parser-test base
  object (outside the required grep scope; inert metadata overwritten by the
  parser). Cosmetic.
- **INFO-2:** commit message and amendment §8 abbreviate chain entry 3 as
  "nemotron-3-ultra-550b" / "nemotron-3-ultra:free"; the code, evidence
  artifact, RUNBOOK §4 and the live listing all pin the exact id
  `nvidia/nemotron-3-ultra-550b-a55b:free`. Code is authoritative and correct.
- **INFO-3:** `openrouterCall` uses the `new Promise(async resolve => …)`
  executor style; all paths resolve and rejections are handled internally, so
  it is functional here. Style note only.

## Residual notes

- Nothing repaired, nothing started/stopped, nothing pushed; the only A7
  mutations are this artifact and `/tmp/a7r4_ai` (test scratch) +
  `/tmp/a7r4_models.json` (public listing snapshot). No process left running
  (verified post-self-check). The Keychain key was never accessed by A7.
- e2e_lifecycle.sh (12/12) and e2e_evidence.sh (19/19) NOT re-run per
  instruction; runner/lifecycle untouched this round, so their recorded
  journals stand.
- End state re-verified after all checks: no ops_service, no PaperDesk,
  opslock FREE, launchd not loaded, ledger chain True/42.
