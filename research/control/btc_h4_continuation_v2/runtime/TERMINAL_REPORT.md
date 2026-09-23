# BTC-H4-CONTINUATION-V2 — TERMINAL REPORT (§34.6)

terminal verdict: **BTC_H4_CONTINUATION_V2_NO_ELIGIBLE_PROPOSAL**

chain: plan a8473839 (main) → bootstrap 1442a76a (base = PSV1 terminal anchor
af52f358) → P1 forensics + P2 decision 0724542b → A7 terminal audit + F-A7-2
correction → this closeout commit. Audit artifacts:
research/control/btc_h4_continuation_v2/audits/a7_terminal_audit.{json,md}.

what was done (pre-GO turn-scope only — NO scored run ever executed):
- P1 FORENSICS: per-trade rebuild of PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION
  from the frozen PSV1 engine; HARD reconciliation gate PASS with max
  relative error 0.0 at 1.0x/1.5x/2.0x (fold nets +140,843.28 / −46,959.99 /
  +133,820.83 / −50,012.30; 86 trades; 79 DONCHIAN_STOP + 7 GATE_INACTIVE).
- P2: at-most-one-change decision record — both owner-menu branches
  ineligible on measured grounds (min-hold fix: immediate-stop
  counterfactual WORSE −3,785.07, F4 −13,066; entry confirmation: no
  separating PIT observable, slope20 anti-sorted, SMA200 gate binds 0/86
  entry bars). No candidate frozen; STOP-1 owner gate moot; GO phrase
  `GO BTC H4 CONTINUATION V2 DISCOVERY SCORED` dies UNCONSUMED at close.
- A7 terminal fresh-context: CONFIRM_WITH_FINDINGS, 0 blocking, 3 LOW +
  1 INFO; independent engine recompute rel-err 0.0 (third independent
  reproduction of the PSV1 BTC_H4 arm this day); adversarial
  strongest-alternative test (breakout-strength gate) judged not premature
  to close — any threshold now would be fold-PnL-informed (plan §2).

observed/published: 0/0 scored outcomes this cycle (forensic rebuild and
audit recomputes are reproductions of the predecessor's record, not new
trials — plan §1.1/§7); budget **0/2**; program totals unchanged 283/286 (P-9).

measured causal findings for the ledger (post-hoc S0, descriptive):
F2/F4 losses are GROSS (−41,885 / −43,504) — not cost artifacts
(fees+funding 12–13% of |net|); payoff asymmetry collapses out of structural
bulls (win/loss 3.78/2.45 → 0.95/0.66; MFE median 8.1% → 3.1–3.8% with flat
MAE); entries are mechanically identical across folds (rank 1.0, dd200≈0
median) — the follow-through regime is not identifiable by any measured
at-entry PIT state.

S1 SEALED; no orders/paper/testnet/live; no new data sources; folds/tiers/
gates never moved; PSV1 artifacts byte-untouched (audit C7). Incidents:
FORENSICS first dispatch BLOCKED on the machine-wide heavy lock (foreign
CHR3F-V1 data-staging, pid 77456; bounded retries then §8 light-exemption
with getrusage disclosure — 0.424 s wall / 122 MB; audit recompute same
discipline 0.22 s / 113.5 MB). No registry/lock anomaly unresolved.
