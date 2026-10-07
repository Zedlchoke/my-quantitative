# A7 PRELAUNCH VERDICT — SPORTS-PAPERTRADE-EXEC-V1 (independent verifier, fresh context)

- Verifier: A7-EXEC (audit only; never repaired; attempted rejection)
- Date: 2026-10-07
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`
- Branch: `orca/spt-exec-v1-integration` (no upstream; `branch -vv` shows none)
- Claimed HEAD: `1ae714337a3d971dcce6666a5cca4df2642f705e`
- **Measured HEAD: `1ae714337a3d971dcce6666a5cca4df2642f705e` == claimed** (self-measured via `git rev-parse`)
- Tree: clean at measurement; boundary `8e5c8f81aeecab13539d1d771d49c739100d5306..HEAD`

## VERDICT: PASS_WITH_FINDINGS

0 CRITICAL / 0 HIGH / 1 LOW / 3 INFO. Nothing unresolved blocks the owner GO.
This verdict is PRELAUNCH ONLY. It does NOT type any GO.

**Explicit statements (load-bearing):**

1. **No GO typed.** The real control dir
   `research/control/SPORTS-PAPERTRADE-EXEC-V1/` contains NO `GO_TOKEN.json`
   (verified by filesystem search); the real registry row records
   `go_phrase_state: REGISTERED_NOT_CONSUMED`; the string `GO_CONSUMED`
   appears NOWHERE in `plans/CYCLE_REGISTRY.json` (all 115 cycles scanned).
2. **Zero real paper rows exist.** No sports ledger/GENESIS file anywhere in
   the worktree, nor under `~/.my-quantitative-data/sports-papertrade-v1/` or
   `~/.my-quantitative-data/sports-papertrade-exec-v1/`, except
   clearly-named SANDBOX files (`sandbox_ledger.jsonl` under `sandbox/`
   dirs; GENESIS rows carry `sandbox:true` / `plan_sha256:"sandbox…"` /
   `SYN-` match ids; the exec sandbox GO token is labeled
   `REHEARSAL-SANDBOX-FABRICATION (NOT an owner GO)`). The single `runs/`
   file is a pre-GO refusal record (`BLOCKED_NO_GO`), zero rows.
3. **THE ONE phrase is the single live gate:**
   `GO SPORTS PAPERTRADE EXEC V1 RUN ALL`. The four retired phrases
   (`GO SPORTS PAPERTRADE V1 CAPTURE`, `GO WNBA WINPROB 2026 REMAINDER V1
   PREDICTIONS`, `GO NBA WINPROB PROSPECTIVE V1 PREDICTIONS`,
   `GO SOCCER INTL WINPROB PROSPECTIVE V1 PREDICTIONS`) are accepted
   NOWHERE: `grep -E` over `execute.py` / `adapters.py` / `__init__.py`
   returns zero matches (exit 1).

## Claim-by-claim verification (from bytes, self-measured)

| # | Claim | Result | Evidence (exit codes / hashes are my own measurements) |
|---|---|---|---|
| 1 | Production runner exists + executable | **PASS** | `research/papertrade_exec/execute.py` present; `-m research.papertrade_exec.execute --help` exit 0 (subcommands plan/forecast/quote/decide/run-day/settle/dashboard/verify-pins/key-check; `--sandbox` family); read-only `plan --date 2026-10-08 --league WNBA` exit 0 — 1 fixture (401918298 SEMI GS@LV, tip 2026-10-08T01:30:00Z, anchor 2026-10-07T19:20:00Z) read from the pinned schedule; no writes. |
| 2 | Single-phrase GO gate | **PASS** | Retired-phrase grep: 0 matches (exit 1). Accepted phrase appears exactly once in execute.py; `GO_PHRASE` constant in `__init__.py` line 22. Gate is two-key (`exec_go_state`, execute.py:83): verbatim-phrase GO_TOKEN.json AND registry phase containing GO_CONSUMED. My refusal rehearsal in TMP registry/control (real dirs never touched): (a) no token → `BLOCKED_NO_GO` exit 3; (b) retired phrase in token (registry GO_CONSUMED) → exit 3, "phrase does not equal the registered single phrase verbatim"; (c) right phrase + registry WITHOUT GO_CONSUMED → exit 3, "token without consumption refuses"; (d) direct `exec_go_state` with both keys in TMP → `(True, ...)` — gate is genuinely two-key. Real-mode mutation pre-GO also refusal-logged in the cycle's own rehearsal (rehearsal_runs.json entries 15/16: exit 3). |
| 3 | Wiring claims | **PASS** | My `shasum -a 256`: `wnba26/predict.py` = `5fc6459c964d7802a5a796657be3819653017668a2156a9ff35686716b425fef` == pin; `soccer/replay.py` = `22553f6b62eacfc7b581737795db5a792e40b4a58a8ffa5de7f3a4e25d2a7e44` == pin; crosswalk seed `2132533b…` == pin; wnba ledger `745014f0…` == pin. Runner `verify-pins --expect-head 1ae71433…` exit 0: all 14 file pins OK + data pins OK (WNBA schedule `0ed97faf…`, NBA composite `3d527b3c…` re-derived, soccer corpus `df35268f…`), self_head == claimed. NBA fails closed: adapters.py:314 raises `BLOCKED_NBA_CORPUS_BIND` when the scored cycle's own outcome-bind law refuses the unmasked read, and adapters.py:318 raises it even if an unmasked read unexpectedly returned; I rehearsed `adapters.nba_real_corpus_read(...)` live → `BlockError BLOCKED_NBA_CORPUS_BIND` with `OutcomeBindRefused` detail. **WNBA WIRED_ENGINE_READY + SOCCER WIRED_ENGINE_READY + NBA WIRED_ENGINE_REPLAY_READY (BLOCKED_NBA_CORPUS_BIND disclosed, fail-closed) — confirmed.** |
| 4 | Rehearsal evidence | **PASS** | `rehearsal/rehearsal_row_census.json`: GENESIS 1 / FORECAST 18 / MARKET_QUOTE 18 / DECISION 18 (6 BET_PAPER + 12 NO_EDGE) / SETTLEMENT 2 — matches claim 18/18/18/2. Sandbox ledger (`~/.my-quantitative-data/sports-papertrade-exec-v1/sandbox/sandbox_ledger.jsonl`) row types match census exactly; ALL 36 FORECAST+MARKET_QUOTE rows carry `mode":"SYNTHETIC"`, `model_version_sha":"SYNTHETIC_ADAPTER_NOT_ENGINE"`, `key_fingerprint":"sandbox-synthetic-00"`, `bookmaker":"SYNTHETIC_BOOK (rehearsal)"`; zero `mode":"ENGINE"` rows anywhere. `dashboard/summary.json`: `chain_ok:true, sandbox:true`. Settlements: WIN +382 cents (+3.82 USD) and POSTPONED→REFUND 0. This cycle committed NO jsonl at all (boundary scan); the only p/odds decimals live inside clearly-labeled SYNTHETIC fixtures. |
| 5 | Test battery | **PASS** | `python -m pytest tests/papertrade_exec -q` from the worktree: **28 passed in 5.89s** (== claim 28/28), exit 0. |
| 6 | Registry | **PASS** | `plans/CYCLE_REGISTRY.json` (repo root, read-only): SPORTS-PAPERTRADE-EXEC-V1 row — lifecycle `ACTIVE_LIGHT`, head `1ae71433…` == measured, budget `{used:0,max:0}`, `go_phrase: "GO SPORTS PAPERTRADE EXEC V1 RUN ALL"`, `go_phrase_state: REGISTERED_NOT_CONSUMED`. Sibling registry heads == my measured worktree heads: SPORTS-PAPERTRADE-V1 `8105e878…` ✓, WNBA-WINPROB-2026-REMAINDER-V1 `46200b30…` ✓, NBA-WINPROB-PROSPECTIVE-PREP-V1 `d504afad…` ✓, SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1 `1ca5cd7d…` ✓. `GO_CONSUMED` string: ZERO occurrences registry-wide (115 cycles). |
| 7 | Zero real paper rows pre-GO | **PASS** | Real control dir: NO `GO_TOKEN.json` (find over the whole worktree: zero hits). No GENESIS/ledger outside sandbox dirs in either data root (see statement 2). v1-root `dashboard/summary.json` carries `sandbox:true`. `quota_journal.jsonl` (5 rows) is quota metadata, not paper rows. |
| 8 | Boundary scan | **PASS** | `git log 8e5c8f81..HEAD --name-only`: exactly 11 files, only `research/papertrade_exec/**` (6), `tests/papertrade_exec/**` (1), `research/control/SPORTS-PAPERTRADE-EXEC-V1/**` (4). `branch -vv`: `orca/spt-exec-v1-integration` has NO upstream. |
| 9 | Heavy lock | **PASS** | `researchctl.py locks inspect` → `verdict: FREE_PROVEN`, `flock_state: free`, no HELD lock. |

## Findings

| ID | Severity | Finding | Evidence | Disposition |
|---|---|---|---|---|
| F1 | LOW | REHEARSAL_REPORT.md says run-day "reports go to `sandbox/`, never `runs/`", but one real-mode refusal artifact exists at `~/.my-quantitative-data/sports-papertrade-exec-v1/runs/run_day_2026-10-09_20261007T093411Z.json` (produced by the REAL-mode pre-GO refusal rehearsal, log entries 15/16). Its content is the `BLOCKED_NO_GO` refusal only — zero rows, zero probabilities. Prose imprecision in the report, not a data violation; the artifact is itself evidence of the gate working. | file content inspected (refusal JSON only); rehearsal_runs.json entries 15/16 exit 3 | Record; no action required. Optional erratum to REHEARSAL_REPORT wording. |
| F2 | INFO | Sibling worktree heads advanced past pins.json dispatch heads (paper_core a752553f→8105e878, wnba26 d6ed119e→46200b30, soccer 24e5745f→1ca5cd7d). pins.json/PINS.md declare heads ADVISORY with byte pins binding; ALL byte pins verified OK by me and by `verify-pins`. Registry rows already record the advanced heads. | verify-pins output; my shasum; registry rows | Disclosed by design; re-pin only on future byte drift (BLOCKED_PIN_DRIFT law). |
| F3 | INFO | SOCCER readiness is engine-side only: real fixtures/odds arrive post-GO via the 0-credit Odds API events endpoint; 1X2 three-leg odds remain unverified in-band (registry phase carries "conditional-1X2"; sibling cycle records NOT_RUN_ODDS_UNVERIFIED). Rehearsal soccer rows are labeled SYNTHETIC events — correctly so. | registry row; rehearsal evidence; config.json sport key | No action for this gate; the conditional is carried into the post-GO record. |
| F4 | INFO | Time-sensitive, for the owner: WNBA SF anchors are live TODAY — `plan` shows 401918298 anchor 2026-10-07T19:20:00Z (`anchor_open_now:true` at measurement ~09:43Z). Per the sibling cycle's law, a missed anchor is NOT_RUN forever. The anchor law is exclusive at/after anchor (exit 5), test-pinned. | my `plan --date 2026-10-08 --league WNBA` output | Owner awareness only; no defect. |

## What I did NOT do

No repairs, no writes outside my two artifacts, no reads of `~/.config`,
no push, no merge, no ledger/registry writes, no network, no heavy lock
taken. GO-gate rehearsals used ONLY tmp dirs (now removed) and the cycle's
own sandbox; the real control dir and real registry were read-only to me.

## Bottom line

Runner executable and law-conformant; the single live gate is
`GO SPORTS PAPERTRADE EXEC V1 RUN ALL` (two-key, refusal-rehearsed, exit 3
pre-GO); WNBA and SOCCER engines byte-pinned and wired (WIRED_ENGINE_READY);
NBA wired for replay with a disclosed, fail-closed BLOCKED_NBA_CORPUS_BIND;
28/28 battery green; zero real rows/probabilities/odds anywhere; registry
consistent (head==measured, budget 0, phrase registered-not-consumed, four
sibling heads exact); boundary and lock clean.

**PASS_WITH_FINDINGS — prelaunch verified. The GO remains the owner's alone.**
