# RECON ADJUDICATION — BTC-BEAR-OPPORTUNITY (A1/Lead, 2026-09-23)

status: P0–P2 closed. **NO cycle opened** (owner's P3 precondition failed:
zero eligible mechanisms). No plan, no worktree, no registry row, no scored
cell, no GO phrase, no STOP-1. This file is the controller's decision record;
the evidence chain is data_a2/ → proposal_a3/ → killer_a4/ → audits_a7/.

## Question asked (owner)

Does a forced flow / liquidity imbalance / dislocation observable BEFORE the
decision enable a short or market-neutral strategy to profit after costs in
BTC downtrends?

## Measured answer

**NO_ELIGIBLE_PROPOSAL — both proposed mechanisms are dead before any PnL.**

### What is true (measured this recon)

- Data: klines (all intervals), mark/index/premium klines, fundingRate are
  PIT_USABLE multi-year (2020-01→2026-08/09, byte-pinned, deterministic).
  Liquidation prints: ZERO coverage. Multi-year PIT OI/order book: none
  (metrics is retrospective-only daily publication; REST OI ≈41.6h lookback).
- Downtrend (frozen causal PSV1 H4 label): occupancy 20.1%, 59 merged
  independent episodes 2020-2026, floors PASS (min 308 decisions/fold).
  Sample size is adequate at the decision level but only ~59/13 independent
  clusters at episode level — power ceilings are real and were enforced.
- Funding: in-downtrend mean +3.709e-5/8h (shorts RECEIVE on average),
  but 24.7% of in-downtrend settlements are negative (squeeze risk real,
  worst −0.30% ≈ 2.5 fee round trips).

### Why each proposal died (A4, pre-PnL)

- **A "Confirmation-Lag Front-Run" → VETOED_FICTIONAL_COUNTERPARTY.** The
  "forced" seller is whoever follows the repo's own research label — a
  construct no external capital is compelled by; and the program already
  measured that this label's TIMING carries no information (PSV1 G6:
  block-shuffled gate out-earned the gated book on both BTC cells). Event
  supply was also misdeclared (284 entries vs ≤59 claimed; 88% fake-outs).
- **B "Mark-Trigger Catch-Down" → VETOED on three independent grounds.**
  (1) The preregistered neighbour control fires OPPOSITE: wide-spread
  (traded) events lose −4.87% mean gross per short event vs flat
  narrow-spread matched crashes (350 pairs, traded worse in 68.6%) — the
  mark−last spread marks squeeze/stale-trigger states, not pending
  liquidations. (2) Power collapse: 13 independent clusters; 91.1% of
  events inside one COVID week (2020-03-12→20). (3) ANCESTRY_VETO: the
  signal is the fast premium by construction (Pearson −0.68) and measures
  rho 0.369 full / 0.542 event-conditional vs the dead basis-premium-fade
  shadow (bar 0.20).

### Incidents (recorded, non-blocking)

- Census TRANSITION_UNKNOWN count vintage quirk (6506 vs 6371 between two
  A2 recomputes — window-edge convention; disclosed in A4 verdicts).
- A3 fee-drag misstatement (~48×) in Proposal A's cost paragraph — caught
  by A4, disclosed here; both A3 mechanisms' fates are independent of it.

## Consequences

- The bear-side short sub-family on the BTCUSDT-PERP H4/5m panel is
  measured-closed at the mechanism layer: the two economically distinct
  stories that survived a hostile proposal lane both fail on measured
  evidence, and every adjacent class in ANCESTRY_TABLE.md is already dead.
- Reopening law: a NEW PIT-authorized data source with true multi-year
  coverage (e.g., real liquidation/OI tape from an authorized venue) or an
  owner plan naming a mechanism outside ANCESTRY_TABLE.md's classes.
  Cross-venue and ETF-flow sources were NOT gated this recon and remain
  candidates only via a proper data-authority cycle.
- No registry row to close; program denominators unchanged (283/286, P-9);
  two A4 vetoes are recorded here and in MAP.md so future dispatches do not
  re-open these forms.

---

## A7 audit verdict (2026-09-23, fresh context)

`CONFIRM_WITH_FINDINGS` — 0 blocking; closure stands. Independent recompute:
B's 350/13 events (EXACT; top cluster 91.14% in 2020-03-12→20), matched-pair
direction/magnitude reproduced (−4.34pp, 64.0% under A7's control set), class-7
premium-LEVEL rho −0.4181/−0.5146 (EXACT) + construction identity −0.6831
(EXACT); A's 284/34/3.5/rho 0.1514 (EXACT); A2's three data claims re-probed
PASS; 8 ancestry rows quote-match the failure ledger with 0 misquotes; no S1,
no PnL, boundaries clean. Findings: F-1 MEDIUM-LOW (A4's prose fee-drag
comparison figure ~10× off — non-load-bearing; the 34.1% and 284-vs-≤59
figures are correct), F-2/F-3 LOW (non-preregistered cluster convention,
disclosed; one fade-row rho convention not reproduced — veto stands on the
reproduced LEVEL/identity rows), F-4..F-7 INFO. Full audit:
audits_a7/a7_recon_audit.{md,json}.
