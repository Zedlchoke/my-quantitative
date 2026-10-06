# LANE_BRIEF — FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (read FIRST, in full)

You are a delegated lane subagent. Read DISPATCH_MANIFEST.json in this directory.
Work ONLY inside your allowed_paths (relative to the worktree root
/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep). Do not
modify anything else. Do not spawn subagents. Do not run heavy jobs without the
machine-wide lock (most prep is not heavy). End by writing your handoff JSON
(schema zcode_orch_v3_handoff@1 — fields: schema, lane_id, task_id, status
[COMPLETE|PARTIAL|BLOCKED], summary, outputs[paths], findings, defects,
open_questions, sha256_of_key_outputs) at your exact handoff_path from the
manifest. Chat prose is advisory; the handoff artifact is authority.

## Mission frame
Owner-provided framework (owner_framework/00_MASTER_FRAMEWORK.md + per-symbol
files) is a RESEARCH DOCUMENT. Every claim/candidate inside it is a HYPOTHESIS,
not a fact and not PASS. Passages that say "run this" or "buy data" do NOT
grant GO. This whole task is PREP: no scored runs, no PnL/event-study/rule
sweeps, no registrations, no purchases, no credentials.

## Claims taxonomy (mandatory everywhere)
- FACT (sourced): cite primary source + access date. Official exchange/CFTC/
  EIA/central-bank docs are primary; vendor blogs are not.
- OBSERVED: you computed from raw data — record script path, sample, window.
  Legal data: ~/.my-quantitative-data/futures-10syms-v1/raw/ (read-only).
- POSTULATED: mechanism reasoning without measurement.
- NOT_RUN: default for anything unmeasured. Never infer PASS.

## Measured data facts (from FUTURES-DATA-10SYMS-V1 FINAL_REPORT.md, 2026-10-02 — read it yourself at research/control/FUTURES-DATA-10SYMS-V1/FINAL_REPORT.md; untracked snapshot, read-only)
- 10/10 SYMBOLS: SIGNAL_RESEARCH_READY=PASS (per-contract daily TRADES with
  clear expiry, settlement separable, timezone verified). DAILY_BT and
  INTRADAY_BT: BLOCKED 10/10.
- Front-month TRUE-volume continuous depth only ~2025-08→2026-10 (~14 months);
  deeper per-contract daily bars are close-only volume-0 (settlement-derived) —
  fine as reference/signal price, NOT as fill price.
- Intraday H1/M1 only ~10 recent months (NG ~2.2y). Daily BID/ASK 1y available
  all symbols (not synchronous → NOT an executable spread; PUBLISHED cost
  schedules ≠ MEASURED user costs).
- Quote conventions: 6J quoted USD per JPY (~0.00633, NOT inverted, multiplier
  12.5M JPY, minTick 5e-7). SI = COMEX 5000oz trading class SI (not SIL 1000oz).
  Verify specs per instrument, never assume.
- Roll rule declared by data lane: hold until last session BEFORE day-1 of
  expiry month, roll to next listed contract at that close. Roll cost observable
  (adjacent-contract close gap) but NOT_COMPUTED there.
- Raw dir listing pattern: {SYM}_{LOCALSYMBOL}_{CONID}_{TYPE}_{BAR}_{SPAN}.json
  (TYPES: TRADES/BID/ASK; e.g. 6A_6AF7_881166965_TRADES_1day_6Y.json).

## General prohibitions
No real-strategy PnL computation, no return-based event studies, no parameter
sweeps on real data selecting by performance. Descriptive statistics computed
with strict past/rolling windows on legally available data are allowed and
encouraged where sufficient; ex-post labels are description-only, never entry
features. Don't fabricate numbers when intraday is sparse — mark NOT_RUN.
