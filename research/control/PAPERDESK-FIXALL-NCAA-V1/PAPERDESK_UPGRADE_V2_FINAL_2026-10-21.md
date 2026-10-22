# PAPERDESK UPGRADE V2 — FINAL REPORT (2026-10-21)

> Lane: `.worktrees/paperdesk-fixall-ncaa-v1/integration`
> (`orca/paperdesk-fixall-ncaa-v1-integration`). HEAD: `a895cdfa`,
> working tree clean. Seal SEALED and untouched; no GO phrase typed by the
> agent anywhere; config `feature_gates` exactly as the owner set them
> (`ai_authority_active: true`, `pm_cutover_active: true` — owner GOs
> consumed at the FIXALL cutover); paper 100%; **no push, no merge**.
> A7 audit: **NOT RUN in this lane** — the integrator owns it (per
> dispatch).

## 1. Commit chain (this session, on top of U0 `5c64af01`)

| # | commit | content |
|---|---|---|
| a | `7036aa65` | U1+U2 — fee truth (FEE_ONCE_FINDING) + AI scorecard truth law |
| b | `545c2ada` | U3+U4 — strongest-first model cascade + plane hygiene |
| c | `2b0a77f7` | U5+U6 — richer AI evidence + CLV measurement plane |
| d | `a895cdfa` | U7 — FROZEN new-law spec + SHADOW evaluator + ops wiring (U6 CLV hourly tick landed in this commit's ops_service.py — one file, one commit; split recorded in HANDOVER_U7) |

Battery after EACH commit (working tree, `tests/papertrade_exec/ -q`):
(a) 270 passed, (b) 270 passed, (c) 270 passed, (d) 281 passed.
Integration wiring (producer/evidence kwargs, `cmd_ai_evidence`
passthrough, U5 board-cache + team-id lookup, U5 fixture cache reset)
landed inside the file groups that own those files and is documented in
HANDOVER_U7 §3.

## 2. Per-workstream done / proof

| WS | done | proof |
|---|---|---|
| U0 (prior) | citation filter, excerpt law, prompt-sha erratum + consumption gate, verdict canonicalization | commit `5c64af01`; battery 210/210 x2 (recorded at its commit) |
| U1 fee truth | PM fee exactly once in BOTH lanes; flat 0.02 = conservative EV-gate buffer; NO runtime change | FEE_ONCE_FINDING.md + hand-computed battery cases (test_fixall_w4, test_upgrade_u1); battery 270 after (a) |
| U2 scorecard truth | results-plane vetoes, ai_layer_value = −vetoed_hypothetical, 100-gate on actually-scored vetoes only, league/model/reason_code breakdowns | ai_scorecard.py + tests; battery 270 after (a) |
| U3 cascade | config-first strongest-first slots (UP/COOLDOWN/HALF_OPEN persisted atomically), full trigger table 429/402/5xx/timeout/garbage/400/404/401, LOW_BALANCE + budget clocks, `data_collection: deny`, no provider-internal fallback, per-model journaling | ai_producer.py + test_upgrade_u3 (652 lines); battery 270 after (b) |
| U4 plane hygiene | sandbox ai_review plane, atomic+flock pending writes, EV-outlier terminal + no-churn law, real-mode refusal of sandbox hook flags | ai_gate_v2.py/execute.py + test_upgrade_u4; battery 270 after (b) |
| U5 richer evidence | kickoff-date + today boards, roster-name news filter (once per team per day), per-team injuries endpoint, ALL cited; integrator wiring: ids auto-looked-up on the kickoff board (shared cached GET), `cmd_ai_evidence --kickoff-utc/--team-ids` | ai_research.py + test_upgrade_u5; battery 270 after (c) |
| U6 CLV plane | no-vig Pinnacle + PM near-close sidecar, MEASURE ONLY, fail-safe NO_RUN; **wired into the ops tick HOURLY** (near-kickoff 2h window + 30-min just-kicked grace, quota-guarded, WSL honestly excluded — no Pinnacle key) | clv_plane.py + test_upgrade_u6 + ops wiring tests (test_upgrade_u7); battery 270 after (c), 281 after (d) |
| U7 new-law era | spec FROZEN (sha `7a402a53…` registered, digest-blanked formula, re-measured by the battery every run) + SHADOW evaluator journaled parallel decisions ONLY; **STOPPED — awaiting a separate owner GO** | NEW_LAW_SPEC_FROZEN_V1.md + new_law_shadow.py + test_upgrade_u7 (11 tests, synthetic); battery 281 pre-commit AND post-commit (d) |

## 3. Final battery at HEAD `a895cdfa` (x2 consecutive)

| run | result |
|---|---|
| Final run 1 | **281 passed, 0 failed** in 76.7s |
| Final run 2 | **281 passed, 0 failed** in 52.0s |

(210 at U0 → 270 after U1–U6 → 281 after U7: +71 tests across the upgrade.)

## 4. Cascade state (measured on the real plane, 2026-10-21)

- Configured slot order (config `ai_provider`, CONFIG-FIRST law):
  1. `anthropic/claude-opus-5.5` (PAID head)
  2. `openai/gpt-5.6-sol` → `anthropic/claude-sonnet-5.5` →
     `google/gemini-3.1-pro-preview` → `deepseek/deepseek-v4-pro-0813` →
     `x-ai/grok-4.7` (paid)
  3. `minimax/minimax-m3.1-flash:free` → `google/gemma-4-31b-it:free` →
     `nvidia/nemotron-3-ultra-550b-a55b:free` →
     `thinkingmachines/inkling:free` → `openrouter/free` (free tail)
- Persisted slot states (`ai_review/cascade_state.json`): **ABSENT — no
  slots exist yet.** The production runner is still on the pre-upgrade
  worktree; the cascade initializes (all UP) on the first producer pass
  of the upgraded runner. Which UP: none persisted.

## 5. OpenRouter key/balance (read headless via check_balance; key NEVER printed)

- Keychain lookup: OK — service `com.myquant.paperdesk`, account
  `openrouter-api-key`, key length **73 chars** (bytes never persisted).
- `check_balance` (GET /api/v1/key): HTTP OK; envelope reports
  `is_free_tier: true`, `limit: null`, `limit_remaining: null`,
  `usage: 0` → **balance reads None (no finite figure) under the
  check_balance law**. Consequence: the LOW_BALANCE clock cannot
  preemptively hold paid slots on this key; the paid head would 402 at
  first use and fail SAFE via the 402 trigger (paid slots held +
  AI_LOW_BALANCE alarm; free tail keeps running).
- FINDING (owner act needed): the CONFIG `key_ref` string ends in
  `" (Keychain)"` — that suffix makes the producer's Keychain lookup MISS
  (the item exists under the plain account name). One-string config fix
  in the `ai_provider` block.

## 6. U5 evidence before/after

> **SIMULATED** — stub payloads from test_upgrade_u5.py (3 candidates),
> NEWS-source scope (the only layer the filter changes; the scoreboard
> gives every candidate ≥ 1 source either way). Not production traffic.

| filter | candidates with ≥1 news source | total news sources |
|---|---|---|
| OLD (team-name only) | 1 / 3 (**33.3%**) | 1 |
| NEW (roster names) | 2 / 3 (**66.7%**) | 3 |

The star-player injury headline ("Jalen Williams (knee) listed out" —
names no team) is dropped OLD, kept NEW via the roster-name filter.
With the integrator wiring, team ids are auto-looked-up on the kickoff
board, so the roster + injuries layers activate for every pending
candidate with a kickoff — no caller change needed.

## 7. U6 sidecar records so far

**0 records** (`<data>/ops/clv/` does not exist yet). The wiring is on
this branch's HEAD only; the production runner (pre-upgrade worktree)
has not run it. Fail-quiet by design until the owner restarts the runner
on this HEAD — then one record per forecast match per day appears near
kickoff (2h window), sandbox-aware.

## 8. Integration wiring delivered (dispatch items)

1. **CLV tick** — `ops_service._clv_closing_quotes()` in the tick, once
   per hour max (state timestamp via the throttle plane), verified ledger
   rows only, exact `clv_plane.record_closing_quotes` signature;
   `odds_fetch` built on `execute._odds_for` + the provider-credit guard
   + the config sport-keys mapping (NBA→basketball_nba, WNBA→
   basketball_wnba, SOCCER→first registered key, NCAA→registered keys;
   WSL excluded by law); `pm_fetch` = `pm_moneyline.discover_and_join`
   (+3-YES for soccer) + read-only CLOB book walk; ALL in-plane failures
   become the plane's own NO_RUN records; the whole hourly call is
   try/except-wrapped with a `CLV_SAMPLE_ERROR` incident — never blocks
   the tick.
2. **Evidence context** — the producer's `collect_evidence` call now
   passes `kickoff_utc=entry.context.kickoff_utc` and
   `team_ids=entry.context.team_ids` (absent ids looked up on the
   kickoff-date board inside the collector — one shared cached GET);
   `execute.cmd_ai_evidence` accepts both optionally
   (`--kickoff-utc`, `--team-ids` JSON).

## 9. Owner-only remaining items

1. **Top up / upgrade the OpenRouter key to PAID, ≥ 10 USD** — the
   current key is free-tier (`limit: null`); the paid head
   (`anthropic/claude-opus-5.5`) cannot run on it (would 402 → fail
   safe).
2. **Fix config `ai_provider.key_ref`** — drop the `" (Keychain)"`
   suffix so the producer's Keychain lookup resolves (item exists;
   73-char key).
3. **Slug verification** of all 11 model ids vs the live OpenRouter
   models list (runtime misses surface as HTTP 400/404 → CONFIG_BROKEN,
   the safe behavior).
4. **GO for the U7 new-law era** — separate, explicit, owner-typed;
   before it: execute the §3 fitting protocol and lock `w` by registered
   spec amendment.
5. **Merge/push** (lane never merges or pushes by law).
6. **Electron app rebuild** (consumes the same ai_review plane).
7. **Production runner restart on this HEAD** — activates the U3
   cascade, U6 CLV hourly tick and U7 shadow journal on the real plane.
8. **A7 audit of this upgrade** — owned by the integrator (not run here).

## 10. Laws held (checklist)

- No GO phrase typed or invented by the agent anywhere.
- `seal.js` SEALED and untouched; no GO token file touched.
- Config `feature_gates` byte-identical to the owner's post-GO state;
  the only config diff in commit (b) was the `ai_provider` block
  (verified in the staged diff before adding).
- Paper 100%; no order placement anywhere; U6/U7 are MEASURE/LOG ONLY.
- Lanes: no merges, no rebase, no push; commits by explicit pathspec
  only (`git add -A` never used).
