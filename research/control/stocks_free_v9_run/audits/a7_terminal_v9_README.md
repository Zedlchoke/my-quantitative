# A7 TERMINAL AUDIT — STOCKS-FREE-V9 (one page)

- **Auditor**: A7 independent terminal auditor, fresh context, independent of the
  A1 thread. Recompute-from-bytes, audit-to-refute; no repairs; **nothing
  committed** (this file and `a7_terminal_v9.json` are untracked by design).
- **Audited head**: `588cd4e` on `orca/stocks-free-v9-integration`, tree clean;
  chain `17e70ac (V9-R1+dryrun) -> 8702e5d (A7 prelaunch + GO consumption) ->
  588cd4e (scored outputs)` verified ancestor-ordered.
- **Artifact**: `a7_terminal_v9.json`, schema `stocks_free_v9_run/a7_terminal@1`.

## Items (7/7 PASS)

| Item | Verdict | Decisive evidence |
|---|---|---|
| A SCORED_RERUN | PASS | Own rerun with two keys, exit 0: `family_verdicts.json` **byte-identical** (sha `90349873…`); ledger 1/65 leaf diff = by-design `code_freeze_sha` provenance only; committed bytes restored, sha256/md5 match pre-run snapshot (`ebba4c05…` / `90349873…`) |
| B GATE_TABLE_RECOMPUTE | PASS | From-scratch evaluator on re-run decision records: PF 0.8095363098127486 and alpha -0.014209463976345205 identical to committed to 16/18 dp; folds 1/3; MDD 0.0791; etf_share 0.7353; SPY-excess 0/3; control +0.0033 does NOT reproduce (opposite sign); 8/10 gates FAIL, margins match |
| C DENOMINATORS_AND_BUDGET | PASS | `observed_delta=7` byte-untouched (= 3 trials + 3 stress + 1 drop-one; rerun-reproduced); publication adjudicates 3 trials append-only; budget 3/6, 3 unused never reassigned; stocks 27/27+3=30/30; program 182/185+3=185/188; survivors 0 |
| D GO_CONSUMPTION | PASS (CONSISTENT) | Timeline verified: owner phrase *"nếu A7 authorized thì GO…"* (00:10Z, recorded verbatim as non-consumable intent) → A7 AUTHORIZED (04:30Z @17e70ac) → CONSUMED (05:30Z) → scored cells. A7 key first; phrase is a complete conditional; strict-P8 dissent on record. Honest caveat: literal P-8 freshness wording would have re-asked; deviation documented two-sided; outcome-irrelevant (run REJECTED) |
| E S1_AND_BOUNDARIES | PASS | S1 sealed (no code path); no push (no origin ref for the branch, `ls-remote` empty); no V9 raw bytes tracked; live key in 0 tracked files; workers 0 |
| F NO_RESCUE_SCAN | PASS | D2 blocked 5/6 on measured rho (0.20010/0.22116/0.20282/0.41332/0.20865/0.339/0.504/…); A6 pooling re-adjudication explicitly refused as post-hoc; 6/6 proposal hashes intact; only the eligible family scored; unused slots not reallocated |
| G TERMINAL_LABEL | PASS | Single family mechanically REJECT (no falsification-shadow claim; control-beats-anchor recorded informative only); full plan arc complete (census→reproduction all artifacts present); no survivors, nothing blocked/incomplete ⇒ **STOCKS_FREE_V9_REJECT_ALL** is the strongest allowed label; dsr/pbo honest form confirmed (no positive candidate ⇒ DSR non-computable, PBO non-exercisable) |

## Verdict

**`STOCKS_FREE_V9_REJECT_ALL_CONFIRMED`** — blockers: none.

LOW findings recorded (all verdict-neutral): sum-vs-mean "expectancy" gate
semantics (-0.0812 sum vs -0.00108/decision); `control_alpha_abs_ratio`
implemented as |anchor|/|control| = 1.1336 vs packet's |c|<0.5|a| (0.8821 — both
FAIL); reproduction rule compares sums over 75 vs 79 decisions; P-8 freshness
deviation documented; stale heartbeat label.
