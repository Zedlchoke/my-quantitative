# V10-N2 — A5-N blinded novelty matrix + rubric pre-scores (recommendation input)

- **Agent / wave:** A5-N · N2 (PLAN §7; §8 firewall)
- **Worktree:** `/Users/hoangminhlong/my-quantitative-v10-wt/n2-a5-novelty`
- **Branch / HEAD:** `orca/v10-n2-a5n` @ `a1528dcb608ccdf2817b6389e524417c11f4d392` (clean at intake)
- **Machine mirror:** `research/audits/v10/a5n_novelty_v10.json`
- **Scope:** audit/scoring only. No proposal, production code or control manifest edited.
  No network, no install, no scored cell consumed.

## 1. Score table (frozen weights)

| Rank | Hypothesis ID | Novelty 35 | Mechanism 25 | PIT/data 15 | Neg-control 10 | Sample-feas 10 | Auditability 5 | **Total** |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `A8-V10-M03-…RESIDUAL-DIFFUSION` | 32.00 | 19.50 | 10.50 | 9.50 | 5.50 | 4.50 | **81.50** |
| 2 | `A8-V10-M01-…AGGRESSOR-ABSORPTION-PANEL` | 31.00 | 20.00 | 7.00 | 9.00 | 9.50 | 4.50 | **81.00** |
| 3 | `H-V10N1-A9-RVRELVAL-v1` | 31.75 | 18.50 | 10.50 | 7.00 | 6.00 | 4.50 | **78.25** |
| 4 | `H-V10N1-A9-INFSPILL-v1` | 23.75 | 20.50 | 11.00 | 9.00 | 6.50 | 4.00 | **74.75** |
| 5 | `H-V10N1-A9-FORCEDFLOW-v1` | 24.25 | 18.50 | 11.50 | 8.50 | 5.50 | 4.00 | **72.25** |
| 6 | `A8-V10-M02-…TICKET-SIZE-SIGNATURE-EPISODIC` | 29.50 | 19.00 | 6.50 | 8.00 | 5.00 | 4.00 | **72.00** |

## 2. Eligibility list (contract thresholds: total ≥75 · novelty ≥28 · 4/4 material dims · no hard/data fail)

1. `A8-V10-M03-LEAVE-ONE-OUT-RESIDUAL-DIFFUSION` — 81.50, novelty 32.00, 4/4
2. `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL` — 81.00, novelty 31.00, 4/4
3. `H-V10N1-A9-RVRELVAL-v1` — 78.25, novelty 31.75, 4/4

Not eligible:
`H-V10N1-A9-INFSPILL-v1` (74.75 total, 23.75 novelty, 3/4 dims),
`H-V10N1-A9-FORCEDFLOW-v1` (72.25 total, 24.25 novelty, 3/4 dims),
`A8-V10-M02-TICKET-SIZE-SIGNATURE-EPISODIC` (72.00 total < 75 despite passing novelty and dimensions).

**Tie-break:** "sorted by hypothesis ID" was inspected and NOT invoked — no exact tie exists
(81.50 / 81.00 / 78.25 / 74.75 / 72.25 / 72.00; minimum gap 0.25). Ordering is score alone.

**Fewer-than-two statement:** not triggered. THREE candidates clear every criterion I am
authorised to test, which exceeds the contract maximum of two selected families. V10 therefore
does not proceed toward `V10_NO_ELIGIBLE_FAMILY_NOT_RUN` on my evidence; the selector faces a
three-for-two choice (any two consume exactly six scored slots). I do not select.

## 3. Dimensional ruling summary

Pairwise: 11 of 15 mechanism pairs are MATERIAL-DIFFERENT in all four dimensions; four pairs sit
at 3/4 — `M02↔FORCEDFLOW`, `M02↔INFSPILL` (identical episodic single-leg timed-hold payoff
class), `FORCEDFLOW↔INFSPILL` (same), and `M03↔INFSPILL` (same counterparty genus: a
slow-updating alt holder; co-selecting both buys diffusion exposure twice).

Uniform D3 criterion applied to all six: a dimension counts only if it changes the *mapping from
signal to exposure vector/leg structure*; conditioning-variable novelty is scored in D2/D4. Hence
the two A9 proposals lose D3 against the historical inventory (single-leg timed directional hold
is an occupied class) while A8-M01/M03 and A9-RVRELVAL keep clear credits for
continuous-monotone-panel / orthogonalised-residual / atomic-two-leg structures absent from the
inventory. Observable claims were verified by keyword audit over every family spec, candidate.yaml,
contracts and strategy module: `taker_buy_quote_volume`, `count`, residualisation, leave-one-out,
pair log-ratio, CLV and orthogonality return **zero** hits anywhere in the prior inventory.

## 4. Data-readiness verdicts used as audit facts

| Fact | Treatment |
|---|---|
| Bars locally for BTC+ETH only; 5+ further symbols manifest-declared but unmaterialised here | F_GRADE must-materialise before prelaunch; hits all ten-symbol panel designs hardest |
| No funding/OI/liquidation companions locally (independently confirmed) | F_GRADE; native funding is inside the frozen cost baseline and is not waivable; severity scales with held-across-settlement duration |
| Bars end 2026-08-20T02:29Z (~21.7 h short of window end) | uniform window-shortfall flag; truncates final day-block (M01), final weekly crossing (M03) |
| `taker_buy_quote_volume` / `count` present in stored BinanceBar schema, VALUES unverified | fail-closed until attestation; binds M01 (`ATT-TAKER-QV`) and M02 (`ATT-COUNT`) hardest |
| Numeric sample-floor constant unknown to all proposers (verified: no such constant readable; only `historical_denominator_floor=117` and fold-PF ≥5 trades) | feasibility stays expressed in absolute counts |

E-S0 screened-window performance figures entered **no** score. Its numbers were consulted solely
for structural facts; its survivor mechanism class (thin-participation markup fade) is adopted by
none of the six proposals, so there is no rescue adjacency either.

Two verification findings worth recording:
1. **Confirmed as claimed:** A8's funding-cadence heterogeneity (1,095 × 9 symbols vs 2,189
   ENAUSDT) and its bar counts (34,983 ETH / 35,040 others) *are* present in
   `data/v9_manifests/universe_selection_v9.json`; the 57-gap ETH capture-boundary hole, BTC gap
   census of 0, and `quote_volume` provenance via the pre-window ranking rule all verify.
2. **Contradicted claim:** A9 §8 item 2 states per-symbol funding settlement row counts appear in
   no readable manifest ("files carry byte sizes only"). The v9 manifest records
   `funding_settlements_in_scored_window` for every selected symbol. This slightly improves the
   true data position versus what A9 assumed.

No candidate reaches HARD_FAIL today. Every blocker is either declared-and-pinned data awaiting
materialisation before prelaunch, or an attestation-gated field whose failure path the proposer
itself defined as fail-closed.

## 5. Contestable calls handed to A7-N

- Both A9 proposals die on D3 under my uniform criterion — A9-FORCEDFLOW self-flagged this;
  A9-INFSPILL did not. Overruling either changes its totals and possibly its eligibility.
- A8-M02 keeps a thin D3 credit (flat-default episodic + frozen record reference + calendar exit)
  yet still fails on total score, so an overturn would not change its outcome.
- A8-M03's "factor-neutral" property is ruled overstated (peer-average stripping leaves market beta
  largely intact with no hedge leg): scored as a mechanism deduction, not a novelty denial.
- RVRELVAL's D3 credit against the ROOT strategy group is credited as material because PnL exists
  only as the difference between two legs, though pairs-convergence payoff is textbook elsewhere.
