# A7_PRELAUNCH_VERDICT — WNBA-WINPROB-2026-REMAINDER-V1

Independent verifier (A7, fresh context). Audit-only; nothing repaired.
Audited at branch tip `d6ed119ea7385a766ba4c58b03252623fae75ca3` (measured
`git rev-parse HEAD` == claimed dispatch head; branch
`orca/wnba-2026-remainder-v1-integration`; tree clean at audit start; no
upstream configured — nothing pushed). Audit instant: 2026-10-07 (fresh
recomputation from bytes, not from lane prose).

## VERDICT: **PASS**

0 HIGH, 0 CRITICAL. 1 NOTE (non-blocking). All gates stand; no GO typed or
consumed by this audit or any lane artifact.

## Checklist recompute (all from bytes)

| # | check | measured | verdict |
|---|---|---|---|
| 1 | Registry row (read-only) | `ACTIVE_LIGHT`; head `d6ed119e…` == measured; budget 0/0; GO `GO WNBA WINPROB 2026 REMAINDER V1 PREDICTIONS` REGISTERED_NOT_CONSUMED; worktree `.worktrees/wnba-2026-remainder-v1/integration`; plan `plans/PLAN_wnba_2026_remainder_v1.md` exists and names `orca/wnba-2026-remainder-v1-integration` (plan L57) | MATCH |
| 2 | Frozen constants vs freeze docs | `arms.py` re-hashed live `.worktrees/wnba-playerfeat-scored-v1/integration/lanes/T_SELECT/arms.py` = `82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3` == ERRATUM_R1 pin (FREEZE_PACKET §1, DATA_REFRESH_MANIFEST rights table); `harness.py` = `b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e` == pin; B1-WNBA selection of record K=32/HCA=50/γ=0.65 read from `SELECTION_REPORT.md` L24 ("FROZEN: K=32, HCA=50, γ=0.65"); B0 p=0.603755 asserted literal | MATCH |
| 3 | PIT/anchor laws in code | `wnba_2026_remainder_ledger.py` L671-672: `anchor = min_tip - timedelta(minutes=370)`; `if max_rec >= anchor: raise` — EXCLUSIVE deadline, exactly-at-anchor refused; per-row law L437 `recorded_at_utc must be STRICTLY < tip_utc`; completed-only stream-state law (docstring L46-48 + test D3 with no-result and post-anchor exclusions, engine agreement <1e-12); tests pin: `test_14` exactly-at-anchor REFUSED, `test_15` +1s refused, `test_15b` 1s-inside accepted, D2/D2b dry-run refusals atomic | PASS |
| 4 | Tests (run by A7, worktree cwd) | `.venv/bin/python -m pytest tests/papertrade_wnba26 -q` → **67 passed in 0.47s** (matches lane claim 59+8=67) | PASS |
| 5 | No real rows | zero `predictions_*` files anywhere in the worktree; grep `Liberty|Dream|Aces|Valkyries` over all `*.jsonl` in the worktree: 0 hits; sandbox ledgers live OUTSIDE git under `~/.my-quantitative-data/wnba-2026-remainder-v1/sandbox/` (9 dryrun dirs), rows carry `cycle_id: SYN-W26-DRYRUN-*`, `game_id: SYN-*`, `home/away_team: SYN-HOME/SYN-AWAY`, placeholder `p_home` | PASS |
| 6 | Boundary scan | `git log 77b5310..HEAD` = 5 commits (c1a93728, e506444c, 7e6721df, 94c70599, d6ed119e); changed paths ONLY `research/control/WNBA-WINPROB-2026-REMAINDER-V1/**`, `research/papertrade_wnba26/**`, `tests/papertrade_wnba26/**`; no `plans/` writes (registry untouched by lane); `branch -vv` no upstream | PASS |
| 7 | Cutoff feasibility re-check | Pinned snapshot re-read directly: `refresh_20261007/wnba_schedule_2026.csv` rows `401918297` date `2026-10-07T23:30Z` (State Farm Arena, Atlanta home = NY@ATL SF2) and `401918298` `2026-10-08T01:30Z` (Chase Center = LV@GS). Recomputed: 23:30Z − 6h10m = **17:20:00Z**; 01:30Z − 6h10m = **19:20:00Z** — both == FREEZE_PACKET §5 + DRYRUN §4 pins. FREEZE_PACKET §6 states "**Missed anchors are NOT_RUN forever (no backfill)**"; §4 + DRYRUN §4 state MIN_VALID=300 **can never be reached** with ≤15 games (operational proof only, stated not stretched) | CONFIRMED |
| 8 | Data manifests | `DATA_REFRESH_MANIFEST.md` lists per-file URL+tag+retrieved_at+bytes+sha256 for 6 byte assets (+2 metadata captures); spot-verified 3 hashes from raw bytes: `wnba_schedule_2026.csv` `0ed97faf…` == pin, `team_box_2026.csv` `0218105a…` == pin, `~/.my-quantitative-data/wnba-v1/raw/ATTRIBUTION.md` `1068e5c7…` == pin | MATCH |

## Findings

| id | severity | finding | evidence |
|---|---|---|---|
| A7-W26-N1 | NOTE | Sandbox separation is enforced by naming convention, not a literal `sandbox:true` field: the ledger schema is a closed 18-field set with no sandbox flag; sandbox runs are distinguishable via `SYN-*` cycle ids, synthetic team names, and the real ledger filename `predictions_<real_cycle_id>_2026.jsonl` being created only post-GO (absence test-enforced). Functionally equivalent protection; recorded so a future reader does not search for a boolean that cannot exist. | ledger FIELD_ORDER L113-132; module docstring L297 ("sandbox ledgers must use a sandbox cycle id"); sandbox rows inspected |

## Cross-cycle observations carried to the consolidated report

- Anchor boundary semantics differ across the sibling cycles: THIS cycle pins
  the anchor EXCLUSIVE (exactly-at-anchor refused — a disclosed tightening of
  the frozen 2027 law); NBA-WINPROB-PROSPECTIVE-PREP-V1 pins INCLUSIVE at
  exactly 6h10m (see that cycle's verdict, finding A7-NBAPREP-F1, severity
  LOW, disclosed on both sides). No lookahead is possible under either law.

## Consolidated gate statement

No GO is typed anywhere in this cycle's artifacts; the phrase
`GO WNBA WINPROB 2026 REMAINDER V1 PREDICTIONS` remains
REGISTERED_NOT_CONSUMED (registry + FREEZE_PACKET §7 + DRYRUN §5 all
concur). Typed GO is the owner's alone. Owner gates intact.
