# S2 A4 lane — process notes (outcome-blind family discovery)

- Agent: A4-S2, worktree `/Users/hoangminhlong/my-quantitative/.worktrees/stocks/s2-prop-a4`,
  branch `orca/stocks-s2-prop-a4`, bootstrap SHA `3a00fd7653dd5ff51ca4b9be51b494638bbb6df9`.
- Identity gate: `pwd`/`git rev-parse HEAD`/`git branch --show-current` matched the
  required worktree exactly and `git status --porcelain=v1` was empty on entry.
  (Initial shell cwd was the integration worktree; the first action re-run inside
  the required worktree passed before any file was read or written.)
- Outcome-blind compliance: no scored PnL/returns/rankings computed anywhere;
  no candidate backtests run; no other proposal lane's files (s2-prop-a3,
  s2-prop-a5 or any other branch/worktree) read. Only this worktree's
  PLAN_stocks.md, research/assets/stocks/{calendar,corporate_actions}.py,
  research/assets/common/{calendar,contracts}.py and directory listings were read.
- Deliverables: `research/proposals/stocks/a4_family1.{json,md}`
  (A4_F1_PEAD_TS_V1, timestamp-safe post-earnings-announcement drift) and
  `research/proposals/stocks/a4_family2.{json,md}`
  (A4_F2_OVI_DECOMP_V1, defensive overnight-capture / overnight-vs-intraday
  decomposition). Exactly two mechanisms, three declared cells each
  (anchor / theoretically justified neighbour / causal negative control).
- Lens compliance: family 1's formation clock is expressible only with the
  A4-owned `classify_earnings_timestamp` BTO/AMC machinery (UNKNOWN fails
  closed); family 2's edge lives entirely in `session_bounds`/`next_session`
  early-close and holiday-spanning overnight intervals and halt fail-closed
  semantics. Both are PLAN §9 priority spaces; both defend novelty against the
  rejected crypto rescues (M01 aggressor-flow absorption, funding-carry,
  weekly reversal) on observable AND counterparty AND clock AND causal control.
- Honesty: all citations marked `MODEL_INTERNAL_UNVERIFIED`, no DOIs or quotes;
  turnover/capacity stated as priors; real-data readiness stated as BLOCKED
  pending owner-authorized entitlement (fields marked
  `UNAVAILABLE_PENDING_ENTITLEMENT`); synthetic-fixture implementability stated
  per proposal.
- One clean commit: `S2 A4: two outcome-blind equity mechanism proposals`
  (no merge/rebase/push/amend, no child agents, production code untouched).
