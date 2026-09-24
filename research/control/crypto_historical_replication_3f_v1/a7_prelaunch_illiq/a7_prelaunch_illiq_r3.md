# A7 prelaunch ILLIQ — round 3 (delta) — REFUSED

Cycle: CRYPTO-HISTORICAL-REPLICATION-3F-V1, family ILLIQ-AMIHUD-28D-W (8 planned scored cells).
Artifact of record: `a7_prelaunch_illiq/a7_prelaunch_illiq.json` (schema `chr3f_a7_prelaunch@1`, round 3).
Lane HEAD audited: `adc6e7f9` (worktree `orca/crypto-historical-replication-3f-v1-integration`); root `b7967f54`.
Supersedes r1 (`a7_prelaunch_illiq_r1_SUPERSEDED.json`, AUTHORIZED 20/20 at `ab76aba2` — issued BEFORE the two new subclass surfaces landed; superseded per P-8 post-audit drift).

## What this round audited

The delta since r1: `benchmark_context_symbols()` (9f1ab1fc) and `universe(stress)` (adc6e7f9)
overrides in `chr3f_illiq_plugin.py`, the failed-sweep forensics, and everything r1 covered
that could have moved. Everything recomputed from bytes; the empirical tests were run by this
audit with the committed frozen engine on the real staged catalog.

## What verified clean

- Engine still frozen: all 8 files (`illiq_amihud/{__init__,audits,plugin,strategy}.py`,
  `adapter_v10/{runner,benchmarks,base,protocol}.py`) byte-identical to `c97283e0`; recovered tree git-clean.
- Plugin drift vs r1 is exactly the 36-line override block; `targets_at`/folds unchanged.
- Claim (a) CONFIRMED: `_context_symbols_for` (runner.py:300) unions declared context with the
  full universe — a context-only override cannot remove unlisted names. The buy-and-hold context
  is diagnostic-only (`enters_denominator: False`, `context_only_scored_false`), sole consumer
  `result["benchmarks"]` + hash. The context-union analysis in the dispatch is accurate.
- `FIRST_ARCHIVE_MONTH` = 20/20 exact match to the measured P0 census
  (`vision_census_wave2.json`, `klines_15m_first_month_v2`).
- Failed-sweep forensics honest: 13 status rows, ALL rc=1 null-metric (8 fast `CatalogUnavailable`
  path-bug rows; 5 full-traversal rows ending in the context `ContractViolation` for 1000PEPEUSDT
  — the structural block the overrides target — plus one `DataUnavailable` terminal-valuation row
  for Y2023-ANCHOR that the implementer has not yet explained). No computed scored outcome in any
  authority surface; resume logic intact.
- Y2021/Y2022: all 7 late-listed names have ZERO bars in the load windows — the universe
  restriction is a strict no-op there (book-identical by construction, verified from bytes).
- Boundaries: sandbox/gateway untouched; fresh shadow-worktree mtimes are the shadow cycle's own
  dashboard rebuild (eb6e162b). No credentials in changed files. Census artifacts unchanged in
  substance (Y2024P 30/33 ok re-confirmed).

## Blocking finding F1 — the universe override is NOT book-identical; disclosure inaccurate

Dispatched Y2024P A/B (variant A = committed plugin; variant B = the r1-audited plugin, i.e.
frozen context/universe surfaces, everything else identical): in Y2024P the books are identical at
all 33 stamps — but that is an OUTCOME, not a construction: variant B's per-stamp eligible count
grows 17→18→19 from 2024-05-20 (BOME/ENA obtain in-window bars and frozen-PIT-eligible features)
without ever reaching a tail leg in that fold.

The same mechanism tested where it bites — Y2023, whose 1000PEPE/SUI/WLD list mid-window — flips
the result. With a harness-only load extension (window/schedule params unchanged; the engine's PIT
law never touches post-decision bars for features), variant A completes end-to-end and variant B
reproduces the context ContractViolation (the overrides are the only subclass-side path through the
frozen context law), and the per-stamp book surfaces DIFFER at 6 of 53 stamps:

| stamp | frozen-universe book | override book | n_eligible B vs A |
|---|---|---|---|
| 2023-11-27 | SUIUSDT on a leg | NEARUSDT | 15 vs 12 |
| 2023-12-04 | SUIUSDT | NEARUSDT | 15 vs 12 |
| 2023-12-11 | SUIUSDT | NEARUSDT | 15 vs 12 |
| 2023-12-18 | 1000PEPEUSDT | NEARUSDT | 15 vs 12 |
| 2023-12-25 | 1000PEPEUSDT | NEARUSDT | 15 vs 12 |
| 2024-01-01 (terminal) | SKIP_NO_SELECTION / WEIGHT_CAP_BREACH | OK 6-leg book | — |

So the committed claims — "no bars in-window, contribute no features, can never enter a book,
provably book-identical" — are false for Y2023, and false-in-mechanism for Y2024P. The override
also contradicts the plan's declared law ("Y2023+ universe changes handled by the frozen PIT
listing eligibility, no manual pruning either direction"): it prunes names the frozen law admits
mid-window, changing which book the replication scores. Dispatch conditions (b) and (c) fail.

## Blocking finding F2 — terminal-valuation wall: Y2023 and Y2024P cannot score at all

Both Y2024P variants abort identically BEFORE scoring: `DataUnavailable: valuation mark
unavailable for 1000PEPEUSDT at 2024-08-19T00:00Z`. Any fold whose window end is a Monday at the
load boundary has a terminal decision instant with no covering bar (mark law needs
`open <= t < close`; last loaded close == t). Y2023 (end 2024-01-01) hits the same wall — the
batch-2 Y2023-ANCHOR log already shows it. Consequence: launching the committed code yields at
most 4/8 scored cells (Y2021/Y2022 x anchor/inv); Y2023/Y2024P x 2 will rc=1. The dispatched
"run Y2024P twice and compare scored surfaces" test is unexecutable as specified.

The wall is a parameter, not a data law: the b20 catalog holds bars through 2024-08-31T23:45Z and
the covering bars (2024-01-01T00:15Z, 2024-08-19T00:15Z) sit strictly BEFORE the forbidden band
start 2024-08-20T00:00Z. A cell-runner load-end extension (and/or a fold-window amendment) fixes
completion without touching forbidden data — but any such change is new surface for A7 to re-audit.

## Also disclosed (non-blocking)

- The implementer's untracked `illiq_diag/Y2021-ANCHOR-v2` (08:59+0700, gate down) produced a
  completed scored-form artifact (net 1.036025187983, pf 1.468852417295, n_pos 216) — no status
  row, no ledger entry, no denominator consumption; a gate-bypass rehearsal that must be booked in
  the post-sweep narrative. result_sha256 7fb4d890bc4b9dbbd53d1b5797b6fa1ee091a1cc71f72779865e8f95975559bc.
- Heavy-lock registry stale row (pid 71445 dead, flock free); registry phase/head/budget stale
  (pre-drift head 21e4f1be, used=0/24).
- Dead clause `or s == self._benchmark` in the subclass universe() (benchmark can never re-enter).
- A7's own diagnostic numbers live only in `/tmp/a7r3_ab/` (no repo/denominator writes).

## Verdict

**REFUSED.** The launch gate (`illiq_scored.py` reads this artifact's path) stays rc=5. The
context override's diagnosis of the frozen-law block is correct and the context side is
diagnostic-only, but the universe override changes scored books in Y2023 while claiming
book-identity, and half the sweep cannot score through the terminal-valuation wall. Owner
remediation paths (context-law amendment with frozen full universe vs knowingly-amended restricted
universe with honest disclosure; plus the load-end/fold-window fix) are enumerated in the JSON.
Any remediated code returns for A7 re-audit before launch.
