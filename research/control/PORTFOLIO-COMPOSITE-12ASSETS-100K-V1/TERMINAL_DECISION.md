# TERMINAL_DECISION — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (A1, 2026-10-01)

**Typed close: `POLICY_NO_INCREMENTAL_VALUE`** — preregistered negative
(plan §7), scored evidence complete, A7 terminal
**CONFIRM_WITH_CONDITIONS** (0 CRITICAL / 1 HIGH / 2 MEDIUM / 2 LOW /
3 INFO; every governing bar recomputed independently with ZERO status
flips; audits/A7_TERMINAL_AUDIT.md).

## The scored result (one table)

| quantity | policy | B1 ALWAYS_ON | verdict |
|---|---|---|---|
| pooled net PnL (8 test folds) | +$603,340.60 | **+$688,604.03** | P1 PnL leg FAIL |
| pooled maxDD (USD) | $418,227.97 | **$397,156.85** | P1 DD leg FAIL |

The deciding layers (risk-only eligibility + supermajority netting + caps
+ cost guard) REDUCED net and RAISED drawdown versus running the same 12
diagnostic legs always-on. P3: policy objective worse than **128/128**
random gates. P5a DSR 0.0002 (PSR 0.851 — fails even with zero deflation).
P7: fold-0 = 89.7% of pooled net. P8: 7/12 removals break the coalition.
Passed: P1-B0 (net > 0 — the legs' raw carry was real; the POLICY subtracted
value), P2a, P4b, P5b (PBO 0.346), P6d, P6c.

## Chain of custody

Registration GO 2026-09-29T10:56Z → scored GO consumed 13:13:38Z (two-key:
A7 prelaunch AUTHORIZED_WITH_FINDINGS + delta CONFIRMED) → Stage-A (2
waves: 150 screened, 62 diagnosed, 43 COST_DOMINATED, 12 survivors) →
Stage-B (8 variants TRAIN-only; winner V3 frozen with honest NEGATIVE
deflated objective −$1.05M) → Stage-C (40/48 identities, 128-seed B4,
846/1500 ledger rows; budget observed == published 38/38) → A7 terminal
CONFIRM_WITH_CONDITIONS. S1 SEALED_UNTOUCHED throughout; sealed 26w tail
never loaded; heavy lock released FINISHED at every stage; no orders, no
paper/live, no push.

## A7 conditions — discharged here (recording obligations; no scored re-runs)

- **C-1 (H-1) P8 implementation erratum**: P8 ran per-leg ISOLATION pairs
  (`legs=[lid]`), not the §8 "without leg i" complement re-runs. NOT
  verdict-changing: under both readings P8 FAILs with the same close code
  `P8_COALITION` (7/12 breaks), and P1 types the close regardless. The
  frozen PASS_BARS_V2 §8 text stands for successor cycles; this erratum
  records the deviation.
- **C-2 (M-1) repro two-level proof record**: the STOP-3 trips
  ({journal: true, metrics: false}) are a comparator-standard artifact:
  field-level diff of the two metrics.json files = exactly 1 differing
  leaf of 1,372 (embedded `code_digest`), journals byte-identical, every
  numeric result identical. Root cause: `_code_digest` (run_dry.py:673)
  hashes research/pc12a/*.py at run time — the frozen orchestrate computed
  it over the code as-ran (pre final .py polish); repro at the commit
  computes over committed files (A7 recomputed the committed-tree digest
  = 8cacead5 exactly). Substantive determinism (P-4 self-consistency at
  the commit) HOLDS; the byte comparator + digest-recipe sensitivity are
  recorded as a lesson for successor engines (canonical-compare + digest
  over a frozen manifest, not a live directory).
- **C-3 (M-2) code-digest disclosure correction**: §5.6(ii)'s "one code
  digest" sentence is imprecise — the battery carries three digests (37
  orchestrate arms / B3 select run / committed tree). Engine-path
  neutrality was independently proven by A7 (B3 ≡ MO identities to 1e-6
  across code states); the disclosure is corrected here.
- **C-4 registry sync**: performed with this close (TERMINAL lifecycle,
  head, budget 40/48) via researchctl — no hand edits.

## Reopening condition (stated once)

A retry of this question shape requires a CHANGED MECHANISM AXIS (Q-10):
not threshold/parameter/leg-swap iteration on this policy. The amended-law
program's own durable assets: the 150-row mechanization triage, the
labeled discovery ledger (846 rows), the 43 COST_DOMINATED kills, the
COMPLEMENTARITY_TRAIN matrix, the engine + 376 tests, the IBKR probe
evidence chain + IDENTITY_FREEZE (7 daily candidates named, BLOCKED
pending amendment), and the TB triple-barrier design (57-row budget
registered, unspent).

## Boundaries at close

S1 SEALED_UNTOUCHED. No orders/live/paper. GO phrase of this cycle dies
consumed (P-8). Remaining headroom (8 identities / 554 ledger rows) stays
untouched — nothing further may run under this cycle. Denominators: +1
hypothesis ledger row; FAMILY_FAILURES +1 (class: risk-only portfolio
policy over diagnostic legs — dead by INCREMENTAL_ALPHA_NEGATIVE on
untouched folds).
