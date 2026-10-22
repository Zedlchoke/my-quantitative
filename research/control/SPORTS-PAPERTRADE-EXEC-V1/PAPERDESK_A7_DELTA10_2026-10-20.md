# PAPERDESK A7 DELTA-10 — independent verification, round-15 HEAD 00f30eed

Verifier: A7, fresh context, 2026-10-20. Worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/sports-papertrade-exec-v1/integration`,
branch `orca/spt-exec-v1-integration`. Python `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
Ledger verifier pinned to the sports-papertrade-v1 integration checkout
(`sys.path.insert .../sports-papertrade-v1/integration`; `from research.papertrade import ledger as L`).
Read-only probes only; nothing repaired; worktree clean before and after every run.

## VERDICT

**VERIFY_PASS_WITH_FINDINGS** — 0 CRIT, 1 HIGH, 1 LOW, 1 INFO.

Items 1, 2, 3, 5, 6, 7, 8 reproduce exactly. Item 4 is **PARTIAL**: the AWAY=1−HOME
approximation is genuinely removed (zero grep hits), but the round's headline claim
"BOTH legs walked via their own CLOB tokens" is **not true of the code at HEAD** —
`probe_event_moneyline` still walks only `tokens[0]` (HOME), never returns a `legs`
key, and `quote_moneyline_2way` therefore always returns None (proven functionally
with a stubbed successful walk). Net behavior is fail-closed and pre-GO-gated
(router returns None pre-cutover; nothing imports the module), so there is **no
production or ledger impact today** — but the P0 fix is functionally incomplete and
the commit/registry prose overstates it. The one-leg walk from round-10 (d5854aea)
is unchanged underneath the new consumer.

## Claim table

| # | Claim | Result | Evidence |
|---|-------|--------|----------|
| 1 | HEAD == 00f30eed == registry exec-v1 head; tree clean | **PASS** | `git rev-parse HEAD` = `00f30eedc7e3fb4c7926d46775b82110e765ac7a`; root `plans/CYCLE_REGISTRY.json` cycles[114] SPORTS-PAPERTRADE-EXEC-V1 head = same; `git status --porcelain` empty (re-checked after all runs: still empty); branch `orca/spt-exec-v1-integration` |
| 2 | Ledger: pinned verifier True / 68 rows | **PASS** | PaperLedger on `~/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl` via pinned sports-papertrade-v1 core: `load()` → **68 rows**, `verify_chain()` = **(True, [])**; census GENESIS 1 / FORECAST 27 / MARKET_QUOTE 14 / DECISION 16 / SETTLEMENT 10; re-checked after all audit activity: still 68 rows, True (verifier non-interference) |
| 3a | `node test_ai_gate.js` 17/17 | **PASS** | `ai gate: 17/17 pass` |
| 3b | `node test_paper_policy.js` 27/27 | **PASS** | `paper policy: 27/27 pass` |
| 3c | `node test_ai_seam.js /tmp/a7r10` 43/43 | **PASS** | `ai seam: 43/43 pass` |
| 3d | `node test_lifecycle_safety.js` 13/13 | **PASS** | `lifecycle safety: 13/13 pass` |
| 3e | targeted pytest (wsl_results + ui_control_seam + pm_moneyline) all pass | **PASS** | `23 passed in 34.16s` |
| 3f | full `pytest tests/papertrade_exec -q` vs baseline | **PASS with baseline note (INFO-1)** | **11 failed, 114 passed**. Baseline per dispatch (15×test_exec_battery + 1×test_b1r_fail_closed = 16) does **not** hold verbatim — see INFO-1: the current documented baseline is 11 (A7-DELTA8, commit 10f7ee3c): 10×test_exec_battery + 1×test_b1r_fail_closed (`test_run_day_sandbox_soccer_journals_no_b1r`); the 5 absent names are exactly the 5 NBA tests delta-8 recorded as lawfully fixed by the round-9 nba26 worktree restore (843fb5a3). **Zero new failures**; visible root cause still `BLOCKED_SOCCER_ENTRY: Lane C replay entry absent` (execute.py:741) |
| 4a | pm_quote_source.py: `'1.0 - best'` and `'1.0 - vwap'` → zero hits | **PASS** | grep rc=1 for both; broader `1\.0 *-` also zero — the approximation literal is gone |
| 4b | Both legs walked via own CLOB tokens in `probe_event_moneyline` (grep `legs_result`, `all_legs_walked` in pm_moneyline.py) | **FAIL → HIGH-1** | Both greps: **zero hits**. `probe_event_moneyline` (pm_moneyline.py:157-208) walks `walk_ask(tokens[0])` ONCE (line 193-194), returns `book_walk_at_stake`; no `legs` key, no second walk, `outcomes_list` extracted but **unused**. `quote_moneyline_2way` (pm_quote_source.py:37-72) reads `result.get("legs")` → always `{}` → always returns None. Functional proof: stubbed Gamma event with `clobTokenIds ["TOKENHOME","TOKENAWAY"]` + successful stubbed walk → tokens walked = `['TOKENHOME']` only, `quote_moneyline_2way` → `None`. Fail-closed; router gate returns None pre-cutover anyway; no cadence importer |
| 5 | KEEP branch: `ok = all(g["pass"] for g in gates)` AFTER all pushes incl. G_PIT_KEEP | **PASS** | decision_pipeline.py:167-177: KEEP pushes `G_EV_KEEP` then `G_PIT_KEEP` ("PIT window"), then `ok = all(g["pass"] for g in gates)` (line 173) → `PLACE` only if ok, else `NOT_PLACED` naming failed gates |
| 6a | `grep -rn openrouter research/papertrade_exec/*.py` → zero hits | **PASS** | rc=1, no output |
| 6b | decision_pipeline imported by nothing in the cadence | **PASS** | Only in-cadence mention is a docstring cite (pm_quote_source.py:11); zero imports from execute.py / adapters.py / `__init__.py` / apps/paperdesk/main |
| 7a | `com.myquant.sptexec.ops` disabled in launchctl | **PASS** | `launchctl print-disabled gui/$(id -u)`: `"com.myquant.sptexec.ops" => disabled` (`com.myquant.wslprov.d1` enabled — separate WSL D-1 automation per round-9 design) |
| 7b | ops_service process count | **PASS (state differs from delta-6)** | `pgrep -fl ops_service` → exactly **1** (pid 10000, `python -m research.papertrade_exec.ops_service --data-root ~/.my-quantitative-data/sports-papertrade-exec-v1`, cwd = this integration worktree — manually started, not via launchd, consistent with 7a). PaperDesk.app (pid 9990) running from this worktree's build |
| 7c | opslock probe on ops/service.lock | **HELD** | `lsof ~/.my-quantitative-data/sports-papertrade-exec-v1/ops/service.lock` → held by pid 10000 (fd 3u); lock file 0 bytes, mtime Oct 8 |
| 7d | ai_review / opinions count | **PASS** | `~/.my-quantitative-data/sports-papertrade-exec-v1/ai_review/opinions/` → **2 files** (`401909090_2026-10-20T124904Z_5ed1b766.json`, `FD-2026-M44_2026-10-20T104810Z_440a4f26.json`); `ai_review/index.jsonl` 7 entries; model_ranking.json present |
| 8a | Cutover REGISTERED_NOT_CONSUMED | **PASS** | Root registry cycles[114]: `go_phrase = "GO SPORTS PAPERTRADE EXEC V1 POLYMARKET CUTOVER"`, `go_phrase_state = REGISTERED_NOT_CONSUMED (registered 2026-10-10T03:45:02Z …)` |
| 8b | GO_TOKEN phrase unchanged | **PASS** | GO_TOKEN.json content sha256 `69027c340686…` (same prefix as A7-DELTA6 7c record), phrase `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` typed 2026-10-07T11:08:47Z; last commit touching it = `b250bfb1` |
| 8c | AI authority NOT_REGISTERED | **PASS** | No AI-authority cycle anywhere in root CYCLE_REGISTRY; string `ai_authority_active` absent from the entire registry JSON |

## Findings

- **HIGH-1 — round-15 P0 "both legs" fix is functionally incomplete (fail-closed dead path; no current production impact).**
  Commit 00f30eed fixed only the *consumer* (`pm_quote_source.py quote_moneyline_2way` now
  correctly requires per-leg `best_ask` from `result["legs"]` and no longer emits the
  `1.0 − …` approximation), and commit 9d7696cf added only an *unused* `outcomes_list`
  extraction to `probe_event_moneyline`. The *producer* was never changed to walk the
  AWAY token: pm_moneyline.py:193-194 still performs a single `walk_ask(tokens[0])` and
  the return dict has `book_walk_at_stake`, never `legs`. Consequence (proven with
  stubbed network + successful stubbed walk): `quote_moneyline_2way` ALWAYS returns None
  — the 2-way adapter can never produce a quote even when the HOME walk succeeds.
  Safety posture is intact: fail-closed (None), `QuoteSourceRouter.quote` returns None
  pre-cutover (`cutover_active` gate, pm_quote_source.py:135-136), and nothing in the
  cadence imports the module. But the commit message and the registry phase text
  ("quote_moneyline_2way walks BOTH legs via their own CLOB tokens") do not match the
  code at HEAD. Cosmetic marker of the same rushed edit: pm_quote_source.py:54 has a
  mangled single-line condition (`or            not`, a collapsed line continuation —
  parses fine, formatting only). Repair is an owner decision; this verifier repaired
  nothing.
- **LOW-1 — dead variable:** `outcomes_list` in `probe_event_moneyline` (pm_moneyline.py:186-191)
  is extracted per the commit message ("outcomes list extracted from the market's own
  field") but never used — further evidence the producer side of the fix was left
  half-landed.
- **INFO-1 — baseline arithmetic:** the dispatch's "documented baseline (15 + 1 = 16)"
  is the pre-round-9 baseline. The live documented baseline since A7-DELTA8 (commit
  10f7ee3c) is **11** (= 16 − 5 NBA tests lawfully fixed by the round-9 nba26 worktree
  restore 843fb5a3). Measured 11F/114P matches that baseline name-for-name; nothing new
  broken, nothing silently fixed since delta-8. Future dispatches should cite 11.
- **INFO-2 — end-state drift vs delta-6, benign:** delta-6 recorded ops_service NOT
  running; it now runs (pid 10000, manual, holds opslock) with PaperDesk up — this is
  the owner's live cadence operating as designed (registry phase "LIVE_SERVICE_ACTIVE"),
  not a regression. ai_review holds 2 opinion files (1 NBA, 1 WSL) + 7 index entries.

## Non-interference

Ledger re-verified AFTER all batteries: 68 rows, chain True, sha256 prefix
`594519c8cd96c902`. Worktree `git status --porcelain` empty before and after all runs.
All probes read-only; /tmp/a7r10 and /tmp/a7r10_probe scratch dirs only.
