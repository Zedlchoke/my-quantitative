# A7 DISPATCH — ssearch-e2-prelaunch (fresh-context independent audit)

Cycle: STOCKS-SEARCH-V1 (registry: BLOCKED, owner remediation decision (a)).
Lane audited: ssearch-e2 (streaming scored-engine remediation) under
research/control/stocks_search_v1_run/e2/ in worktree
/Users/hoangminhlong/my-quantitative/.worktrees/stocks-search-v1/integration
(branch orca/stocks-search-v1-integration).

## You are A7 — audit ONLY

- You do NOT modify any code. You do NOT self-approve work you wrote
  (you wrote none of this lane).
- You write EXACTLY two files:
  1. research/control/stocks_search_v1_run/audits/a7_prelaunch_ssearch_e2.json
     (verdict artifact, schema a7_prelaunch_ssearch_e2@1)
  2. research/control/stocks_search_v1_run/e2/audits/ssearch-e2-a7-prelaunch.handoff.json
     (handoff, schema zcode_orch_v3_handoff@1 — see precedent:
     e2/../handoffs/ssearch-a7-prelaunch.handoff.json for field shape)
- No registry/ledger writes. No push/merge/rebase. No S1. No orders.
  No scored execution. Read-only commands only (python for recomputation
  of digests/comparisons is allowed; it must not write outside the two
  files above).

## Context to read first

1. plans/PLAN_stocks_search_v1.md (the frozen plan; §3b D2-skip; §6
   battery; §8 trading contract; §10 language).
2. research/control/stocks_search_v1_run/e/e_run_verdict.json (the
   TECHABORT being remediated: measured 28.37 GiB floor vs 6 GiB).
3. research/control/stocks_search_v1_run/i/i_engine.py and
   i/adjudicate.py — the FROZEN reference engine (READ-ONLY chain).
4. The whole e2/ lane: README.md, i_stream_engine.py, equivalence.py,
   selfcheck.py, e_stream_run.py, dispatch.json, and the evidence
   artifacts (selfcheck_verdict.json, equivalence_verdict_synthetic.json,
   equivalence_verdict_real_subset.json, equivalence_verdict_detached.json
   if present, probe_stream_rss.json, calibration_stream.json if present).

## Audit items (adjudicate each; cite file:line evidence)

A. SCIENTIFIC EQUIVALENCE of the streaming engine to the frozen path:
   - mirror fidelity: i_stream_engine.ordered_kills / stage_a_gates /
     adjudicate_candidate_stream vs i/adjudicate.py line by line — every
     threshold, every NaN rule, every dict key, every disposition
     string; k6_slow_drift stdev semantics; include_censored_nets
     (as_included) append order and spy pairing for the included variant.
   - streaming semantics: per-name iteration order vs build_all_books
     sorted(names); per-book leg order; book_log slice accumulation
     order vs i_engine._finalize; np.mean pairwise-summation
     reproduction (spilled float64 arrays in leg order); fold grouping
     by masked selection (order preservation); cohort/reversal/PIT
     per-name refactors vs the reference cross-sectional functions
     (cohort_bookable_decisions counting semantics incl. the
     counts-only-for-rt nuance; reversal worst-quintile tie-break
     (r, sym) and formation order; cal_hist twin determinism).
   - equivalence evidence integrity: rerun the digest comparisons if
     needed; confirm the verdict artifacts really say bitwise PASS for
     all 3 cells on synthetic AND real-subset; confirm the real-subset
     artifact persisted NO performance numbers (booleans/digests only).
B. RESOURCE evidence: probe_stream_rss.json peak vs the 1.5 GiB bound;
   the orchestrator's RSS watchdog (5.5 GiB abort), spill quota
   (6 GiB/cell), disk floors (6 GiB start / 2 GiB live), generation-
   numbered atomic checkpoints (transaction law: accum snapshot gen g
   fully written before the checkpoint names g; spill truncation to
   committed counts; census-based skip without re-parse — verify no
   double-count path exists).
C. FROZEN-EXPERIMENT INTEGRITY: the lane modifies NOTHING in the frozen
   chain; verify via git (worktree HEAD, clean tracked tree, e2/ files
   are the only additions) that i/, e/, s/, d1/, p0/, m0/, z/, audits/
   are byte-identical to the pre-lane commit; the 3 frozen cells, folds,
   cost bands, clock, thresholds and labels (R0 NOT_RUN / PBO NOT_RUN /
   §10 disclosure) are carried verbatim; no S1 access path exists in
   e2/; the GO gate cannot be bypassed (verify_and_pin phrase check,
   SSEARCH_E2_GO_PHRASE law, early/paraphrased refusal).
D. HONEST LABELING: verdict schemas, budget accounting (slot consumed
   at cell START; DONE-skip never re-consumes), STOP/verdict vocabulary
   matches plan §11; the wall-clock/throughput disclosure
   (names_per_second) is present and not hidden.

## Verdict rules

- For each item: PASS / FAIL / NOT_RUN with evidence (paths, line
  numbers, recomputed digests).
- Severity: HIGH/CRITICAL findings block the prelaunch; MEDIUM are
  recorded; the verdict is one of:
  AUTHORIZED_WITH_FINDINGS (0 HIGH/CRITICAL) or BLOCKED_PRELAUNCH.
- You are independent: if you cannot verify something, label it
  NOT_RUN — never an inferred PASS.
