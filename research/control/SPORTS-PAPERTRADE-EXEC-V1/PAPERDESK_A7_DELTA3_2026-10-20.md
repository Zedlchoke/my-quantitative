# PAPERDESK A7 — DELTA-3 VERIFICATION (round-3, owner re-audit fixes), 2026-10-20

- Verifier: A7, independent, fresh context.
- DELTA commit: `2141d261d0dbcd176cea515359428e0dd20301ff` (parent
  `6055a43046754f2bddc34f53ec90edf0c69704bb`), branch `orca/spt-exec-v1-integration`,
  worktree `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`.
- Measured: `git rev-parse HEAD` == `2141d261d0dbcd176cea515359428e0dd20301ff`
  == ROOT `plans/CYCLE_REGISTRY.json` exec-v1 `head`. Worktree clean
  (`git status --porcelain` = 0 entries) at verification time.
- Scope honored: no repair, no lifecycle mutation; `e2e_lifecycle.sh` /
  `e2e_evidence.sh` NOT_RUN by instruction (recorded journals relied upon).

# VERDICT: VERIFY_PASS_WITH_FINDINGS

0 CRIT / 0 HIGH / 2 MEDIUM (both disclosure-presentation; no data, evidence-law
or lifecycle impact) / 1 LOW (stale comment wording) / 4 INFO. All three owner
re-audit items are substantively fixed in code and in the authority documents;
every runnable battery re-ran green on the delta commit; ledger, registry, GO
state and machine end-state are unchanged and clean.

## Claim-by-claim table

| # | Claim (dispatch mapping) | Code evidence | Re-run / real-plane evidence | Result |
|---|--------------------------|---------------|------------------------------|--------|
| 1a | Budget = ROLLING window: `requestTimes[]` + injectable `clock`; `windowUsed()` prunes by `budgetSeconds`; `withinBudget()` compares WINDOW count, not lifetime | ai.js:78–98 (`requestTimes`, `clock || (() => Date.now())`, `filter(t => now - t < budgetSeconds*1000)`) | ai battery #27–31: 4th request in-window refused, allowed again after `now += 61s`, `usedRequests === 4 && windowUsed() === 1` (lifetime separate), allow-list enforced, non-200 → `ok:false` | CONFIRMED |
| 1b | `fetch` pushes `clock()` timestamp; lifetime `usedRequests` display-only; error message states window semantics | ai.js:108–114 (`requestTimes.push(this.clock())`; error `request budget exhausted (>N in the last Ms)`) | same battery | CONFIRMED |
| 1c | `_httpsGet` transport seam so tests never hit the network | ai.js:129–138; battery stubs `conn._httpsGet = (url, done) => done(...)` | battery ran fully offline | CONFIRMED |
| 1d | Claims updated everywhere; no remaining unqualified "per 60s" / "≤5 req/60s" | RUNBOOK.md:52–53 ("≤5 requests per ROLLING 60s window"); renderer app.js:608–609 ("≤5 requests per ROLLING 60s window"); amendment §7; packet ("≤5 request/rolling-60s (trước đây ghi lifetime cap — đã sửa)"); registry phase ("ROLLING 60s window … not lifetime cap") | grep across apps/paperdesk + both control docs: every CURRENT-status mention carries ROLLING; the only unqualified "≤5 request/60s" left is amendment §6 line 109 — the historical round-2 record, explicitly superseded/corrected by §7 two paragraphs below | CONFIRMED (historical §6 retained as record — see INFO-2) |
| 2a | `buildCandidates` pure; extracted to main/candidates.js | candidates.js:22–77 (pure, no I/O, `module.exports`); main.js:20 requires it, main.js:369 uses it | battery #32–35 | CONFIRMED |
| 2b | Plan entry WITHOUT match_id → skipped with "no synthetic ids" reason | candidates.js:49–54 (`skipped.push({source:'plan', reason:'missing match_id — skipped (no synthetic ids)'…})`); main.js:372–374 journals `AI_SCHED_SKIPPED` | battery #34 (`skipped[0].reason.includes('no synthetic ids')`) | CONFIRMED |
| 2c | Fixture in both ledger+plan → ONE candidate; plan `anchor_utc` becomes candidate `deadlineUTC` (authoritative) | candidates.js:55–62 (`byId.has` → enrich `deadlineUTC = f.anchor_utc`, no second candidate); :67 plan-only `deadlineUTC: f.anchor_utc` | battery #32 (ONE canonical id), #33 (anchor authoritative) | CONFIRMED |
| 2d | main.js no longer constructs synthetic `league-home-away` ids | diff removes the whole `fromLedger`/`fromPlan` block incl. `` `${f.league || '?'}-${…}.replace(/\s+/g,'_')` ``; grep main.js for the template → only the comment "no synthetic ids" remains; `wsl-full` grep on main.js → no match (homepage webHints construction gone entirely) | — | CONFIRMED |
| 2e | AI idempotence keys (matchID, deadlineUTC) → cannot split a fixture | ai.js:325–326 (maybeAutoReview `o.matchID === c.matchId && o.deadlineUTC === deadlineUTC`), ai.js:385–387 (runReview dup check same key) | battery #36: plan view then ledger view of the SAME fixture → exactly one opinion | CONFIRMED (see INFO-4 for the anchor-equality assumption) |
| 3a | Sources carry `systemCaptured` (no bare `verified` flag); claimed → `systemCaptured:false, claimed_by_model:true` | ai.js:242–251 (pm_gamma_page), 262–270 (pm_clob_book), 281–288 (web_page) all `systemCaptured:true`; ai.js:582–589 claimed `systemCaptured:false, claimed_by_model:true`; no source object emits `verified` | battery #23, #37 (every source `systemCaptured === true` + note caveat) | CONFIRMED |
| 3b | PM source notes disclose team-name-in-title-only + NOT fixture-authenticated + no stage/kickoff/rules crosswalk | ai.js:247–251 ("MATCHED BY TEAM-NAME-IN-TITLE ONLY - no stage/kickoff/rules crosswalk; NOT fixture-authenticated"), 268–269 (CLOB "same name-match (NOT fixture-authenticated)") | notes persisted in sidecar JSON; Health disclosure line (see 3e) | CONFIRMED |
| 3c | Zero systemCaptured → forced ABSTAIN | ai.js:590–597 (`capturedCount === 0 → verdict = 'ABSTAIN'` + uncertainty) | battery #24 (zero verified → forced ABSTAIN even if model cites URLs) | CONFIRMED |
| 3d | webHints homepage removed (wsl-full.com gone from candidate hints) | main.js: no `webHints` at all; candidates.js sets `webHints: []` deliberately; only remaining `wsl-full` is ai.js:84 connector allow-list default (infrastructure, no candidate ever carries a hint) | grep | CONFIRMED |
| 3e | Renderer chips SYSTEM-CAPTURED / CLAIMED_BY_MODEL — DISCARDED; Health `pm evidence quality` + rolling-window lines | app.js:448–450 CLAIMED_BY_MODEL — DISCARDED chip present; app.js:578–580 `pm evidence quality` line added this commit; app.js:608–609 rolling-window line. **BUT**: no `SYSTEM-CAPTURED` chip exists and app.js:450 still branches on stale `s.verified` (a field ai.js no longer emits) → system-captured sources render with NO quality chip | grep app.js `SYSTEM-CAPTURED` → no match; `s.verified` → app.js:450 | **PARTIAL — MEDIUM F-1** |
| 4a | AI automation label states machinery tested + scheduler IDLE in disabled-no-entitlement | main.js:111–114 ("Machinery TESTED …; scheduler IDLE while mode is disabled-no-entitlement — no opinions are generated; GLM live is NOT_RUN_AI_RUNTIME_ENTITLEMENT"); scheduler guard main.js:360; ai.js:315–317 disabled → return, nothing recorded | — | CONFIRMED (label details partially stale — MEDIUM F-2) |
| 4b | GLM live NOT_RUN **with the probe result** in the label; probe recorded in packet/amendment | RUNBOOK.md:45–53 (key IS present, HTTP 429 / errCode 1113, quota/balance); amendment §7:136–141 (fingerprint ca2793462eda4970…, HTTP 429 errCode 1113); packet:16–22 (same); ROOT registry phase (same). **BUT** main.js aiAutomation label says "(no Z.ai General API key)" and "26/26 seam" — no 429 probe result, count stale vs 37-check battery | — | **PARTIAL — MEDIUM F-2** |
| 5a | `node test_ai_seam.js /tmp/a7r3_ai` → 37/37 | — | re-run 2026-10-20: **37/37 pass**; evidence `/tmp/a7r3_ai/ai_seam_results.json` = 37 checks, 0 fails | CONFIRMED |
| 5b | `node test_lifecycle_safety.js` → 13/13 | — | re-run: **13/13 pass** (identity, PID_REUSE_REFUSED, fail-closed stop/bootout) | CONFIRMED |
| 5c | `pytest tests/papertrade_exec/test_ui_control_seam.py -q` → 8 passed | — | re-run: **8 passed** | CONFIRMED |
| 5d | Full python suite: 16 pre-existing failures, names == documented baseline | — | re-run `pytest tests/papertrade_exec/ -q`: **16 failed, 94 passed**; composition 15×test_exec_battery + 1×test_b1r_fail_closed (`test_run_day_sandbox_soccer_journals_no_b1r`); visible assertion `BLOCKED_SOCCER_ENTRY: Lane C replay entry absent` (execute.py:741) = the documented sibling-entry drift root cause; name set matches WSL_BET_PAPER_VERIFY.md §F byte-for-byte (passed count grew 86→94 from newly added tests; failure set identical) | CONFIRMED |
| 6a | Registry exec-v1 head == 2141d261 == `git rev-parse HEAD` | ROOT plans/CYCLE_REGISTRY.json: `head: 2141d261d0dbcd176cea515359428e0dd20301ff`; phase contains "GO_CONSUMED CAPTURE_ACTIVE LIVE_SERVICE_ACTIVE | PAPERDESK.APP UI+LIFECYCLE CONTROLLER round-3 at 2141d261…" | rev-parse == same | CONFIRMED (worktree mirror stale, INFO-3 carry-over) |
| 6b | Cutover phrase REGISTERED_NOT_CONSUMED; GO_TOKEN phrase unchanged | ROOT registry `go_phrase_state: REGISTERED_NOT_CONSUMED (registered 2026-10-10… Polymarket cutover…)`; phase text "cutover phrase REGISTERED_NOT_CONSUMED untouched"; GO_TOKEN.json `"go_phrase_typed_by_owner": "GO SPORTS PAPERTRADE EXEC V1 RUN ALL"` unchanged | — | CONFIRMED |
| 6c | Ledger: pinned verifier → True / 42 rows; mtime unchanged (2026-10-18) | pinned core (sys.path sports-papertrade-v1/integration; `research.papertrade.ledger.PaperLedger` on `<dataRoot>/ledger/paper_ledger.jsonl`) → **(True, [])**, 42 rows; census GENESIS 1 / FORECAST 13 / MARKET_QUOTE 11 / DECISION 13 / SETTLEMENT 4; `ls -l` mtime **Oct 18 07:10:54 2026** | — | CONFIRMED |
| 6d | End state: launchd service absent; no ops_service process; no PaperDesk process; opslock FREE | `launchctl print gui/501/com.myquant.sptexec.ops` → "Could not find service"; `pgrep -f research.papertrade_exec.ops_service` → empty; `pgrep -f 'PaperDesk.app/Contents/MacOS/PaperDesk'` → empty; `helpers/opslock.py probe …/ops/service.lock` → **FREE** (lock file 0 bytes, Oct 8) | — | CONFIRMED |
| 6e | ai_review sidecar: no opinions produced without the app running | `~/.my-quantitative-data/sports-papertrade-exec-v1/ai_review/opinions/` → **0 files** (dir itself empty, mtime Oct 19 17:29; no index.jsonl ever created) — the scheduler never executed because the app never ran after the round-3 rebuild; nothing new since 2026-10-19 | listing | CONFIRMED |
| 7a | Rebuilt .app codesign OK | `codesign --verify --deep --strict` on build/PaperDesk-darwin-arm64/PaperDesk.app → exit 0 (adhoc, arm64); bundle timestamps Oct 20 06:44 = commit time | — | CONFIRMED |
| 7b | Packaged main/{ai.js,candidates.js,runner.js} carry rolling semantics, systemCaptured + NOT fixture-authenticated, PID_REUSE_REFUSED / IDENTITY_VIA_LAUNCHD_PLIST; candidates.js present in bundle | packaged ai.js: ROLLING wording + windowUsed/budgetSeconds/requestTimes (11 hits), systemCaptured ×6, "NOT fixture-authenticated" ×2; packaged runner.js: PID_REUSE_REFUSED + IDENTITY_VIA_LAUNCHD_PLIST ×1 each; `Contents/Resources/app/main/candidates.js` present (3237 B) | `diff -q` packaged vs worktree: ai.js, candidates.js, runner.js, main.js **all byte-identical** | CONFIRMED |

## Commands + results (re-run by this verifier, 2026-10-20)

```
git -C <wt> rev-parse HEAD                       -> 2141d261d0dbcd176cea515359428e0dd20301ff (branch orca/spt-exec-v1-integration)
git -C <wt> rev-parse 2141d261^                  -> 6055a43046754f2bddc34f53ec90edf0c69704bb
git -C <wt> status --porcelain | wc -l           -> 0
cd apps/paperdesk && node test_ai_seam.js /tmp/a7r3_ai
                                                 -> ai seam: 37/37 pass (evidence JSON: 37 checks / 0 fails)
node test_lifecycle_safety.js                    -> lifecycle safety: 13/13 pass
.venv/bin/python -m pytest tests/papertrade_exec/test_ui_control_seam.py -q
                                                 -> 8 passed
.venv/bin/python -m pytest tests/papertrade_exec/ -q
                                                 -> 16 failed, 94 passed (names == documented baseline; see 5d)
ROOT registry head                               -> 2141d261d0dbcd176cea515359428e0dd20301ff == HEAD
ROOT registry go_phrase_state                    -> REGISTERED_NOT_CONSUMED (Polymarket cutover, 2026-10-10)
GO_TOKEN.json                                    -> "GO SPORTS PAPERTRADE EXEC V1 RUN ALL" unchanged
pinned core PaperLedger(real ledger).verify_chain()
                                                 -> (True, []) | rows: 42 | census 1/13/11/13/4
ledger mtime                                     -> Oct 18 07:10:54 2026 (unchanged)
launchctl print gui/501/com.myquant.sptexec.ops  -> Could not find service (absent)
pgrep -f research.papertrade_exec.ops_service    -> (empty)
pgrep -f PaperDesk.app/Contents/MacOS/PaperDesk  -> (empty)
helpers/opslock.py probe <dataRoot>/ops/service.lock
                                                 -> FREE
ai_review/opinions/ listing                      -> 0 files (none new since 2026-10-19; app never ran post-rebuild)
codesign --verify --deep --strict <PaperDesk.app> -> OK (exit 0)
packaged vs worktree diff -q (ai/candidates/runner/main.js)
                                                 -> all byte-identical
```

NOT RUN by instruction (would mutate lifecycle): `e2e_lifecycle.sh`,
`e2e_evidence.sh` — covered by previously recorded journals and committed
evidence (see PAPERDESK_A7_DELTA_2026-10-19.md).

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| F-1 | MEDIUM (disclosure-presentation only) | Renderer evidence chips are half-relabeled. `renderer/app.js` opHtml has NO `SYSTEM-CAPTURED` chip and still branches on the stale field `s.verified` (line 450: `s.verified ? '<span class="green">VERIFIED</span>' : ''`) — a field ai.js no longer emits, so the branch is dead and system-captured sources render with NO quality chip at all. The CLAIMED_BY_MODEL — DISCARDED chip IS present. The owner demand "renderer chips show SYSTEM-CAPTURED / CLAIMED_BY_MODEL — DISCARDED" is therefore only half-implemented. Impact bounded: the underlying data is honest (`systemCaptured` + full caveat notes persisted in the sidecar JSON; Health shows the `pm evidence quality` disclosure), and `source.note` is not rendered by opHtml either — so nothing false is displayed, but the per-source chip disclosure the audit asked for is missing in the UI surface. |
| F-2 | MEDIUM (stale static label; no behavior impact) | main.js:111–114 `aiAutomation` (shown in Health as `auto-scheduler`): (a) says "26/26 seam" while the round-3 battery is 37 checks — the commit message itself says 37/37; (b) says "GLM live is NOT_RUN_AI_RUNTIME_ENTITLEMENT (no Z.ai General API key)" — contradicting the recorded single live probe (key IS present, fingerprint ca2793462eda4970, General API HTTP 429 errCode 1113 quota/balance) and contradicting the same Health view's `keychain key` line, which on this machine shows "present (sha256 ca2793462eda4970…)". The owner demand was that the label carry the probe result; RUNBOOK / amendment §7 / packet / registry all record it correctly — only this static UI string was not updated. Because `refreshEntitlement()` runs at construction and would flip mode to `shadow-mock` with the key present, the live-runtime classification in the label is also not machine-state-accurate; display-only, scheduler remains IDLE only in disabled mode as labeled. |
| F-3 | LOW (cosmetic) | ai.js:14–15 header comment still describes model-claimed sources as "recorded as verified:false/claimed_by_model:true" — the flag is now `systemCaptured:false` (code at ai.js:582–586 is correct). Same generation of stale prose: SYSTEM_PROMPT line "Without verified evidence, answer ABSTAIN" and mock uncertainty "no verified evidence captured" (prompt/demo prose, no flag semantics), and battery test NAMES still say "zero VERIFIED sources". |
| INFO-1 | INFO | Provenance nuance: amendment §7 header says "owner audit of a5e04783" while the delta commit message says round-3 responds to the owner re-audit of 6055a430 (a5e04783 = round-2 commit; 6055a430 = interim HEAD). Both refer to the same audit thread; no document content is affected. |
| INFO-2 | INFO | Amendment §6 (round-2 historical record) retains the old "≤5 request/60s" and "verified:false" wordings. §7 two sections later explicitly discloses both as errors and corrects them ("Claim '≤5 req/60s' trước đây thực chất là lifetime cap — đã sửa cả code lẫn claim"). History retained as record — acceptable; no current-status claim is unqualified. |
| INFO-3 | INFO (bookkeeping, carry-over of prior audit F-3) | The worktree's `plans/CYCLE_REGISTRY.json` mirror is still R11-era while the authoritative ROOT registry carries head 2141d261 + the round-3 phase paragraph. Root is the writable authority per AGENTS.md; no action taken. |
| INFO-4 | INFO | Cross-view idempotence relies on the heuristic `deadlineFor` mirror and the runner's `anchor_utc` coinciding to the millisecond (both derive from the same pinned anchor laws; kickoff-anchored). Battery #36 pins equality for the tested instant. If a future runner anchor law diverged from the ai.js mirror, a ledger-view run followed by a plan-view enrichment could in principle re-key the (matchID, deadline) pair. By construction equal today; flag for any future anchor-law change. |
| INFO-5 | INFO | Amendment §5 (2026-10-19 tech note) still lists battery counts "test_ai_seam.js (14)" / "test_ui_control_seam.py (6)" — now 37 / 8. Historical section, superseded counts documented in §7/registry phase. |

## Residual drift — OUT OF SCOPE (other lanes)

Prior audit's cycle-doctor observations (HEAD_MISMATCH on other cycles, closed-cycle
state entries) were not re-measured this round; they belong to other lanes.
`tests/papertrade_exec/` sibling-entry drift (16 failures) is the documented
pre-existing baseline and is not a PaperDesk finding.

## Boundaries observed

Nothing pushed; nothing repaired; no launchd/runner start or stop; ledger,
registry, GO token untouched (read-only verifications only); e2e lifecycle and
evidence scripts not executed per instruction. The only files created by this
verification: this audit artifact and the throwaway battery evidence
`/tmp/a7r3_ai/ai_seam_results.json`.
