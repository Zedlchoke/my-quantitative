# PAPERDESK A7 — ROUND-5 DELTA INDEPENDENT VERIFICATION (2026-10-20)

- Verifier: A7 (independent, fresh context, round-5)
- Object: commit `521d21ae67699dbdec05bcb81414821d480e54bc` on
  `orca/spt-exec-v1-integration`, worktree
  `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`
- Scope: (A) AI advisory actions KEEP/SKIP/SWITCH under
  POLICY_FREEZE_AI_ACTIONS_V1 (SANDBOX advisory; AI authority NOT
  REGISTERED; stop before owner GO) + (B) stability fixes from the owner's
  live audit + (C) NBA BLOCKED_NBA_ENTRY investigation (report-only).
- Constraints honored: the owner's live instances (PaperDesk pid 55580,
  child runner pid 55611) were NOT signaled, killed, paused or launched
  against; no e2e_evidence.sh / e2e_lifecycle.sh run; nothing started or
  stopped; nothing repaired; /api/state probed GET-only.

## VERDICT: VERIFY_PASS_WITH_FINDINGS

0 CRIT / 0 HIGH / 1 MED (F-1) / 2 INFO (F-2, F-3) / 1 INFO code note (F-4)
+ 1 observation (owner-instance timing). Every load-bearing claim of the
round reconciles: freeze document, pure evaluator + isolation, 24/24 +
43/43 + 13/13 + 8-passed battery, sidecar-only persistence, both stability
fixes, report-only NBA finding, registry/GO/ledger/end-state, rebuilt
codesigned bundle with byte-identical packaged policy module. The single
MED is a freeze-letter vs implementation mismatch on ONE sub-claim
(post-settlement result label) with zero safety consequence — post-settlement
outcomes remain fail-closed and no bet can ever be created.

## Claim table

| # | Claim | Result | Evidence (anchor) |
|---|---|---|---|
| 1 | FREEZE DOC: enum KEEP/SKIP/SWITCH, 11-gate SWITCH set, §3 prohibitions, schema, NOT-REGISTERED + stop-before-GO | PASS | POLICY_FREEZE_AI_ACTIONS_V1.md §1 (3-row enum), §2 (11 gates: G_PROPOSED_LEG_VALID, G_NOT_SAME_LEG, G_QUOTE_PRESENT, G_DEPTH_FROM_FROZEN_WALK, G_PIT_TIMING, G_EV_AT_LEAST_5_PERCENT (EV≥0.05, c=0.02), G_FEES_ONCE_FROZEN, G_STAKE_LAW_FROZEN, G_OPEN_CAP_AND_AVAILABILITY, G_DRAWDOWN_NOT_PAUSED (<0.10), G_ONE_SELECTION_PER_MATCH), §3.1–3.4 (blocked→bet refusal; frozen-numbers-only; no waivers; post-settlement INVALID), §4 schema, header + AI_ACTIONS_PACKET §4 ("NOT REGISTERED", successor-cycle order 1–3, candidate GO phrase explicitly NOT registered) |
| 2 | EVALUATOR: pure module, gates 1:1, G_NO_BET_CREATION, SKIP/KEEP laws, enum INVALID | PASS_WITH_FINDINGS | apps/paperdesk/main/paper_policy.js — zero `require()` calls, zero fs/write calls (grep); EV_THRESHOLD=0.05, DRAWDOWN_PAUSE_FRAC=0.10, stakeLaw 'v3-1pct'; SWITCH rejected on EVERY non-BET_PAPER status via `!isOpenBet` branch (5 statuses battery-proven); SKIP always lawful; KEEP on non-bet → LAWFUL_KEEP_NO_BET; outside enum → INVALID. F-1: the post-settlement INVALID branch (L90–93) is unreachable — see findings |
| 3 | ISOLATION: evaluator referenced ONLY by main.js (UI) + its test; zero references from research/papertrade_exec or any ledger-writing path | PASS | `grep -rn "paper_policy" research/ apps/paperdesk/` (excluding node_modules/.app) → exactly 3 hits: test_paper_policy.js:8, paper_policy.js:12 (self), main.js:22 |
| 4 | BATTERY 24/24 / 43/43 / 13/13 / 8 passed | PASS | `node test_paper_policy.js` → "paper policy: 24/24 pass" exit 0; `node test_ai_seam.js /tmp/a7r5_ai{,2}` → "ai seam: 43/43 pass" exit 0; `node test_lifecycle_safety.js` → "lifecycle safety: 13/13 pass" exit 0; `.venv -m pytest tests/papertrade_exec/test_ui_control_seam.py -q` → "8 passed in 11.20s" |
| 5 | SCHEMA+WIRING: prompt law, enum validation, baseOpinion null, evaluateAndPersist on BOTH paths, sidecar-only persistence | PASS | ai.js SYSTEM_PROMPT: recommended_action JSON field + law (5): grading vs EVERY frozen gate, ONLY frozen ledger numbers, "you can NEVER turn a blocked/no-quote fixture into a bet"; parse: outside enum → null + uncertainty note; baseOpinion `recommendedAction: null`; main.js evaluateAndPersist attached to manual `ai:run` AND auto `maybeAutoReview` path, snapshot from `ledger.matches` + `ledger.wallet` via snapshotFromMatchView; persists via `ai.store.save` only (sidecar dir `<dataRoot>/ai_review/opinions` + index.jsonl, ai.js L179–180). Ledger write-reachability grep: ZERO `ledger.<write>` calls in main/*.js or renderer/*.js; ledger.js uses only fs.statSync/readFileSync |
| 6 | STABILITY: 2s ticker calls runner.pollOnce() before refreshLedger/broadcast; cadenceText renders objects as compact JSON; old direct interpolation gone | PASS | main.js ticker (L382): `runner.pollOnce(); refreshLedger(); broadcast();` in order; renderer app.js cadenceText(c) (L186–193): JSON.stringify, truncate 120, wrapped `esc(cadenceText(...))`; diff removes `- ${kv('last cadence', esc((hb && hb.lastCadence) || '—'))}`; exactly one lastCadence usage site, through cadenceText |
| 7 | NBA INVESTIGATION report-only: pin nba26 worktree ABSENT, fix out-of-scope, no pin edited, 0 research/papertrade* files in commit | PASS | pin `nba26` (research/papertrade_exec/pins.json L80–96) → worktree `…/.worktrees/nba-winprob-prospective-prep-v1/integration`, pkg_dir research/papertrade_nba, loader.py/predict.py sha-pinned, lane HEAD 82542aa8, absence → BLOCKED_NBA_ENTRY; path ABSENT (both `my-quantitative/.worktrees` and `~/.worktrees` variants; dir exists but is EMPTY total-0); `git worktree list` has NO such entry; AI_ACTIONS_PACKET item 3 reports it, NOT fixed, restoration = own authorized lane; `git show --name-only 521d21ae` → 0 files under research/papertrade* (7 files, all apps/paperdesk + control docs) |
| 8 | REGISTRY: root registry head == 521d21ae == git rev-parse HEAD; phase GO_CONSUMED; cutover REGISTERED_NOT_CONSUMED; GO_TOKEN unchanged | PASS | root plans/CYCLE_REGISTRY.json (writable authority): head = 521d21ae67699dbdec05bcb81414821d480e54bc, updated 2026-10-20T00:53:53Z, phase begins "GO_CONSUMED CAPTURE_ACTIVE LIVE_SERVICE_ACTIVE"; go_phrase "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER" = REGISTERED_NOT_CONSUMED; s1 SEALED_UNTOUCHED, workers 0; GO_TOKEN.json mtime Oct 9 2026, content = 2026-10-07 consumption record, unchanged. F-2: worktree registry MIRROR is stale by established pattern (see findings) |
| 9 | LEDGER: pinned verifier True/42, mtime unchanged 2026-10-18; opinions unchanged (0) | PASS | pinned PaperLedger.verify_chain (sports-papertrade-v1 paper_core) on `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl` → True, 42 rows, errors []; file mtime Oct 18 07:10:54 2026 (unchanged); ai_review/opinions/ EMPTY (0 files, dir mtime Oct 19 17:29), no index.jsonl — the owner's app has produced NO opinions since 2026-10-19 (legitimate unchanged end-state); ai_review/model_ranking.json mtime Oct 20 07:05 = round-4 commit artifact |
| 10 | END-STATE: owner instances UNTOUCHED and ALIVE; opslock HELD by their runner; /api/state chain OK (GET-only) | PASS | ps: 55580 PaperDesk (ppid 1, started Tue Oct 20 07:33:50 2026, binary = THIS worktree's build path) and 55611 ops_service --data-root …/sports-papertrade-exec-v1 (ppid 55580, started 07:33:56) — both ALIVE, untouched; lsof ops/service.lock → held open by pid 55611 = HELD; `curl http://127.0.0.1:8791/api/state` (GET) → chain {ok:true, errors:[]}, rows_count 42, service.pid 55611, tick_count 62, last_cadence_result shows NBA THROTTLED (consistent with the NBA report) |
| 11 | BUNDLE: rebuilt (mtime today), codesign OK, packaged parity, packaged self-check on REAL ledger chain_ok true 42 | PASS | PaperDesk.app mtime Oct 20 07:52:24 2026; `codesign --verify --strict` OK (ad-hoc, com.myquant.paperdesk); packaged `Contents/Resources/app/main/paper_policy.js` BYTE-IDENTICAL (cmp) to worktree; packaged markers: G_NO_BET_CREATION ×3, pollOnce ×1 (main.js), cadenceText ×2 + "POLICY " chip ×1 (app.js); `PaperDesk --self-check-ledger <REAL ledger>` → `{"rows":42,"sandbox":false,"chain_ok":true,"verified_rows":42,"errors":[]}` |
| 12 | No push; worktree clean | PASS | `git status --porcelain` → 0 entries (pre-artifact); branch has NO upstream push — 10 local commits ahead of origin ref, none pushed by this round |

## Commands + results (verbatim anchors)

```
git rev-parse HEAD            -> 521d21ae67699dbdec05bcb81414821d480e54bc
git log -1 --format='%H %P'   -> 521d21ae… 254b49ef…   (F-3: dispatch parent note)
git show --stat 521d21ae      -> 7 files: ai.js +26, main.js +41,
                                 paper_policy.js +229, renderer/app.js +28,
                                 test_paper_policy.js +194,
                                 AI_ACTIONS_PACKET_2026-10-20.md +86,
                                 POLICY_FREEZE_AI_ACTIONS_V1.md +71
cd apps/paperdesk && node test_paper_policy.js          -> 24/24 pass, exit 0
cd apps/paperdesk && node test_ai_seam.js /tmp/a7r5_ai  -> 43/43 pass, exit 0
cd apps/paperdesk && node test_lifecycle_safety.js      -> 13/13 pass, exit 0
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
  tests/papertrade_exec/test_ui_control_seam.py -q      -> 8 passed in 11.20s
grep -rn "paper_policy" research/ apps/paperdesk/       -> 3 hits (main.js, test, self)
grep "ledger\.(append|write|save|…)" apps/paperdesk/main/*.js renderer/*.js
                                                        -> no matches
pinned PaperLedger(...).load().verify_chain()           -> True, 42 rows, []
curl -s http://127.0.0.1:8791/api/state                 -> chain ok true, 42 rows,
                                                           service.pid 55611
ps -p 55580,55611                                       -> both alive
lsof ops/service.lock                                   -> pid 55611 holds it
PaperDesk --self-check-ledger <real ledger>             -> chain_ok true, 42, sandbox:false
codesign --verify --strict PaperDesk.app                -> OK
```

## Findings

### F-1 (MEDIUM) — "post-settlement INVALID" is claimed but unreachable; dead branch + battery gap
POLICY_FREEZE_AI_ACTIONS_V1 §3.4, the commit message, and the dispatch all
say post-settlement actions ⇒ INVALID. In `evaluateAIPaperAction`
(apps/paperdesk/main/paper_policy.js): line 61
`isOpenBet = decisionStatus === 'BET_PAPER' && !f.settlement`, so a settled
fixture takes the non-BET branch (L73): SWITCH → REJECTED
(G_NO_BET_CREATION), KEEP → LAWFUL_KEEP_NO_BET, SKIP → LAWFUL_SKIP. The
INVALID-on-settlement branch at L90–93 (`if (f.settlement) return …
INVALID`) is unreachable dead code — reaching it requires `!f.settlement`,
then tests `f.settlement`. No battery case (test_paper_policy.js or
test_ai_seam.js) constructs a post-settlement fixture.
Safety consequence: NONE. Every post-settlement outcome remains
fail-closed and advisory-only; a bet can never be created (SWITCH is
rejected outright); no execution authority exists (NOT REGISTERED).
Record severity rationale: it is a freeze-letter deviation on one named
sub-claim, not a control failure. Suggested fix (NOT applied — verifier
repairs nothing): hoist the settlement check above the isOpenBet
branching and add one post-settlement battery case per action.

### F-2 (INFO) — worktree registry mirror is stale by design
The worktree's `plans/CYCLE_REGISTRY.json` still shows head 9a18a4f2
(updated 2026-10-10). The writable cycle authority is the ROOT checkout's
registry, which reads head 521d21ae, phase GO_CONSUMED, cutover
REGISTERED_NOT_CONSUMED — exactly as claimed. Mirror refreshes happen in
dedicated "registry mirror" commits; not a defect of this delta.

### F-3 (INFO) — ancestry note on the dispatch's "parent"
The immediate parent of 521d21ae is 254b49ef (the round-4 A7 delta-4
artifact commit). 0c049c67 (round-4 base) is three commits back and IS an
ancestor (verified with `git merge-base --is-ancestor`). The round chain
0c049c67 → d19f559c → 254b49ef → 521d21ae is linear and intact.

### F-4 (INFO) — dead variable in the auto-path wiring
main.js auto-path declares `const op = ai.opinions.find(o => o.matchID ===
r.matchId && o.opinionID === (r.opinionID || o.opinionID))` and never uses
it (persistence uses `latest`). Cosmetic; behavior unaffected (the newest
opinion per matchId is what gets policyEvaluation + sidecar save).

### Observation (not a finding) — owner-instance vs rebuilt-bundle timing
The owner's running PaperDesk (pid 55580) started 07:33:50; the on-disk
bundle was rebuilt 07:52:24 and codesigned — so the process predates the
rebuilt bundle it was launched from. Round-4→5 sources are packaged
byte-identical for the policy module; any pre-rebuild delta in the RUNNING
process's loaded sources is a normal consequence of the owner restarting
on their own schedule. Recorded for the next audit; no action taken.

## End-state statement

AI authority remains NOT REGISTERED: no GO typed, none consumed, none
waived; the Polymarket cutover phrase stays REGISTERED_NOT_CONSUMED;
GO_TOKEN.json untouched; the real ledger is byte-unchanged since
2026-10-18 (42 rows, pinned verify_chain True); ai_review/opinions holds 0
opinions; the owner's app (55580) + child runner (55611) run untouched on
the real data root with the ops lock HELD and /api/state chain OK; the
runner was not launched, signaled or stopped by this verification; nothing
pushed; the only file this verifier wrote is this artifact (uncommitted —
committing is the lane's call).
