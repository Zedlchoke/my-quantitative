# A7_DELTA_REMEDIATION — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (2026-09-29)

Fresh-context, read-only delta audit of the three remediations ordered by
A7_PRELAUNCH_AUDIT (AUTHORIZED_WITH_FINDINGS 0C/0H/1M/2L/6I). Write scope
(ONLY): this file. No git operations performed (nothing committed, nothing
staged); no network; no S1; no PnL computation or estimation by the
auditor. Python: root `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.

Measured base:
- WORKTREE `.worktrees/portfolio-composite-12assets-100k-v1/integration`,
  branch `orca/portfolio-composite-12assets-100k-v1-integration`,
  HEAD `6b71f7986f4c88da840d5266f92ec2a228222157` (== the remediation
  commit, as required), working tree clean.

---

## F-1 (MEDIUM — smoke-artifact/tree mismatch): **CONFIRMED FIXED**

- `research/pc12a/smoke_dry_run_pre_fix_superseded/` exists with
  `README.txt` (4 lines: names it the impl-lane vintage, 965 rows, evidence
  of the ATR same-day lookahead bug, kept append-only per disclosure law)
  + `DRY_RUN_REPORT.json` + `journal.jsonl` — 965 rows measured,
  sha256 `41e1202be3cce8528ce462051657d1d5a51724a0d5b8acd02bb0a6841d403e3a`
  == **byte-identical** to the pre-fix journal at `git show
  317d0838:research/pc12a/smoke_dry_run/journal.jsonl` (vintage preserved,
  not regenerated).
- `research/pc12a/smoke_dry_run/` now holds the POST-FIX smoke:
  `journal.jsonl` **863 rows** measured (sha256
  `6cd82ce0c11e26a9296093b1825f371947034bdf0162a730ad947d536e6cdf25`);
  its `DRY_RUN_REPORT.json` says `journal_row_count: 863`, `leak_scan
  {clean: true, keys: []}`, 8-week window 2024-01-05..2024-02-23.
- Both committed at `6b71f798` (git log per path: the superseded dir's
  only commit is 6b71f798 with journal +965/README +4/report +188; the
  current smoke journal was rewritten in the same commit, 1824 lines
  changed).
- `FREEZE.md` "REMEDIATION APPENDIX (A1, post-A7-prelaunch, 2026-09-29)"
  (line 89, +34 lines in 6b71f798) discloses the corrected record: the
  rename, the 965/863 row counts, AND corrects the earlier freeze-commit
  message's false "removed" claim ("the earlier rm targeted a
  non-existent path — a no-op, now disclosed"). The freeze document no
  longer describes unpinned evidence nor a removal that did not happen.

## F-2 (LOW — cash_delta_usd 0.0 on non-fill rows / missing on NET_ORDER): **CONFIRMED FIXED**

Code (read at HEAD, diff vs `317d0838`):
- `research/pc12a/journal.py:129` — the offending
  `fields.setdefault("cash_delta_usd", 0.0)` is now
  `setdefault("cash_delta_usd", None)` inside the BLOCK/DEFER/
  NETTED_TO_ZERO branch; `cash_delta_usd` IS in `NULL_FILL_FIELDS`
  (journal.py:60-63) so the guard loop would raise on any non-None value
  there. Writes null, never 0.0.
- `research/pc12a/run_dry.py:500-516` — `net_order_row` gains a required
  `cash_delta_usd` wired in the engine as
  `-(delta*fill_price + commission)` for buys /
  `(-delta)*fill_price - commission` for sells — I read the adjacent book
  update (run_dry.py:472-476: `cash -= delta*fill + commission` /
  `cash += (-delta)*fill - commission`) and the sign matches it exactly.
- Regenerated full-window journal
  (`.../dry_run/full_window/journal.jsonl`): 35,504 rows measured;
  sha256 `3fb9c83d42ac5b9841e239d70d34d6461f86794af8e010ee742325679080637b`
  — starts `3fb9c83d`, matches the FREEZE appendix pin; grep
  `"cash_delta_usd":0.0` → **0 occurrences**. My own per-kind census:
  null on BLOCK 367 / DEFER 363 / NETTED_TO_ZERO 3,250 / TWIN 363
  (= 4,343, exactly the rows that previously carried the fabricated 0.0);
  real values on all 10,107 NET_ORDER rows; absent on DECISION/SWAP/HEADER.
- Independent identity check across **all 10,107 NET_ORDER rows**:
  `cash_delta_usd == -(delta*fill + commission)` (buy) /
  `(-delta)*fill - commission` (sell) recomputed from the journaled
  `delta_units`/`fill_price`/`commission_usd` — **0 mismatches**
  (tolerance 1e-9; 5,054 buys / 5,053 sells).
- Old-vs-new `DRY_RUN_REPORT.json` diff: only `code_digest` and
  `elapsed_seconds` changed — outcome histogram and cost-bill totals are
  byte-identical, confirming the fix changed journal field semantics only,
  not decisions or costs.
- Tests (ran myself, root .venv, in the worktree):
  `pytest tests/test_pc12a_a7_remediation.py -q` → **4 passed**
  (`test_f2_blocked_rows_carry_null_not_zero`,
  `test_f2_net_order_rows_carry_cash_delta`,
  `test_f3_enum_contains_unavailable_fill_bar`,
  `test_f3_unavailable_path_journals_without_crash` — the file holds
  exactly these 4). Full suite `pytest tests/ -q -k pc12a` →
  **154 passed, 0 failed, 1915 deselected (47.4s)** == FREEZE appendix
  claim "154/154 (150 + 4 remediation regressions)".

## F-3 (LOW — UNAVAILABLE_FILL_BAR not in OUTCOME_ENUM): **CONFIRMED FIXED (with corrected diagnosis)**

- `research/pc12a/journal.py:51` — `OUTCOME_ENUM` now contains
  `"UNAVAILABLE_FILL_BAR"` (frozen enum extended; comment cites the
  remediation).
- `research/pc12a/run_dry.py:439-449` — the no-fill-bar fail-closed path
  now journals `outcome="UNAVAILABLE_FILL_BAR"` (was `BLOCKED_STALE`
  overload) with detail "no fill bar before the next decision
  (fail-closed, no cash effect)".
- The journal.py module docstring documents the corrected label-divergence
  diagnosis: the path "journals the precise outcome instead of overloading
  BLOCKED_STALE; zero rows of this kind exist in the frozen full-window
  journal — the path never fired — so no committed artifact changes".
  FREEZE appendix carries the fuller corrected diagnosis ("No crash
  existed … the true defect was report-vs-journal label divergence").
- Verified from my own scans: 0 occurrences of UNAVAILABLE_FILL_BAR in the
  regenerated journal and absent from the report histogram — the path
  indeed never fired, so the enum extension alters no committed row.
- Regression tests pass (2 of the 4 above).

## Leak law re-check (RGC-INC-1) — auditor's own independent scan

On the REGENERATED artifacts (not the engine's claim):
- `dry_run/full_window/DRY_RUN_REPORT.json`: walked all 132 leaves —
  only counts (decisions, votes, fills_by_outcome, blocked histogram),
  cost-bill totals, digests, run metadata. Regex scan (key paths + raw
  text) for `pnl|profit|loss|return|equity|sharpe|drawdown|win_rate|
  expectancy|payoff|gross|performance|cagr|roi|mtm|unrealized|realized`
  → **0 hits**.
- `dry_run/full_window/journal.jsonl` (35,504 rows): distinct top-level
  key census = 64, all decision/fill/cost-bookkeeping; forbidden-key scan
  → 0; raw-text grep for each of `pnl, sharpe, profit, drawdown, equity,
  equity_delta, "return, loss, gross, net_pnl, win_rate, expectancy,
  cagr, unrealized, realized` → **0 hits each**. TWIN `would_*` fields =
  costs only (`would_fill_price, would_spread_once_usd, would_slip_usd,
  would_commission_usd`).
- Hash chain independently re-implemented and verified over all 35,504
  rows (self-hash + prev-link incl. HEADER): **OK**.
- Internal consistency: outcome histogram sum 14,087 == NET_ORDER 10,107
  + NETTED_TO_ZERO 3,250 + BLOCK 367 + DEFER 363; row-kind census sums to
  35,504 and is identical to the pre-remediation census (behavior
  unchanged).
- Spot-check: 5 random rows (SWAP seq 25077; DECISION seq 33933, 30345,
  9635; NET_ORDER seq 19046) — field sets schema-sane: SWAP carries
  swap_usd/multiplier/wed_x3/units; DECISION carries the full
  decision-state block (ids, feature_pit_snapshot, vote, eligibility/
  risk/portfolio state); NET_ORDER carries the full fill block +
  cash_delta_usd. No anomalies.

---

## Verdict

A7_DELTA_VERDICT: **CONFIRMED**

- F-1 CONFIRMED — 965-row vintage preserved byte-identical under
  `smoke_dry_run_pre_fix_superseded/` with README, 863-row post-fix smoke
  committed at `smoke_dry_run/`, both in commit `6b71f798`, and FREEZE.md's
  REMEDIATION APPENDIX discloses the corrected record (including the
  no-op-rm correction to the earlier commit-message claim).
- F-2 CONFIRMED — journal.py:129 writes null (never 0.0), run_dry.py:500
  wires the §7 per-event delta with sign exactly following the book
  update, regenerated 35,504-row journal has 0 `"cash_delta_usd":0.0`
  occurrences (4,343 nulls / 10,107 real values, identity holds on all),
  sha256 `3fb9c83d…` matches the FREEZE pin, 4/4 remediation tests +
  154/154 full pc12a suite green under my own run.
- F-3 CONFIRMED — `UNAVAILABLE_FILL_BAR` in OUTCOME_ENUM
  (journal.py:51), journaled verbatim by the no-fill-bar path
  (run_dry.py:444), docstring documents the corrected label-divergence
  diagnosis; path never fired (0 rows), so no committed artifact changed.
- Leak law re-verified clean by independent scan of the regenerated
  report + journal (0 forbidden keys/values, chain OK, histogram identity
  exact, 5-row spot-check sane).

No new findings. Scored GO remains REGISTERED_NOT_CONSUMED.
