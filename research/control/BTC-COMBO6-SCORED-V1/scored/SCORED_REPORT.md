# SCORED_REPORT — BTC-COMBO6-SCORED-V1 — 2026-09-29

Run identity: code freeze c0f97a9d (chain 2481f307 → 2db0e19b → c0f97a9d; A7-audit/GO
commits ce1dd0ef add evidence only, engine bytes identical); corpus_digest
e270c9c77801aa19e250cceaae92b918062ed8777aea237ddf734ebcbfd06232; two-key GO
auth/GO_RECORDED.json (key_1 A7 AUTHORIZED_WITH_FINDINGS 0C/0H; key_2 owner standing
directive 2026-09-29). Execution: run_scored_locked.py under machine-wide heavy lock
(role E_SCORED_CELLS), exit 0, 7.4 s, 1 pass computing stress tiers 1.0/1.5/2.0.

## Per-cell accounting (§20.3)
| cell | stress 1.0 net ($) | PF | trades | pos folds | P1 | stress 1.5 net | content_sha256@1.0 |
|---|---|---|---|---|---|---|---|
| LEG-1 MOM4H-1PCT | −46,534.21 | 0.7813 | 3,795 | 1/10 | FAIL | — | d787697451af997b… (combo payload; per-leg digests inside) |
| LEG-2 MAS-4H24H-TURN | +4,707.81 | 1.0537 | 401 | 6/10 | PASS | — | 〃 |
| LEG-3 MAS-12H72H-TURN | +1,662.25 | 1.0280 | 226 | 5/10 | PASS | — | 〃 |
| LEG-4 MAC-2H8H | −6,618.22 | 0.9496 | 581 | 5/10 | FAIL | — | 〃 |
| LEG-5 RSI-20-55 | −9,515.51 | 0.9365 | 660 | 6/10 | FAIL | — | 〃 |
| LEG-6 MAT-2H12H | −7,319.99 | 0.9360 | 417 | 6/10 | FAIL | — | 〃 |
| COMBO | −63,617.86 | 0.9158 | 6,080 | 4/10 | FAIL | −100,107.48 (PF 0.871) | d787697451af997b0c5f314937ac46444d747c35347dba4ed4370e95c615e5e6 |

Tier ×2.0 combo: −136,597.10 (PF 0.8286). Combo max drawdown 97,271 USD on 60,000
start (equity_end −3,618 = Σ sleeves: −36,534+14,708+11,662+3,382+484+2,680).
Budget: 7/12 cells consumed (observed 7, published 7 — TRIAL_LEDGER.jsonl).
All 6 legs non-vacuous; no positions open at frame end; deferred entries 0.

## Verdict bars (engine-computed, stress 1.0)
P1 combo net > 0: FAIL. P2 PF ≥ 1.25: FAIL (0.916). P3 ≥7/10 folds: FAIL (4/10).
P4 MDD ≤ $15,000: FAIL ($97,271). P5 net>0 @×1.5: FAIL. P6 fold concentration: PASS
(vacuous — net ≤ 0). P7 combo ≥ B1 AND ≥ mean(legs): FAIL (−63,618 vs B1 +10,689
vs mean −10,603).
**TERMINAL_OUTCOME (predecided plan §7): COMBO6_NO_INCREMENTAL_VALUE** — two legs
pass P1 in isolation (LEG-2, LEG-3) but the combined portfolio fails every
risk/value bar; the active overlay is dominated by buy-and-hold.

## Baselines
- B0 FLAT: 0 (sanity).
- B1 ALWAYS-LONG $10k: net +10,689.21 (fill 33,053.93 @ 2021-01-04T00:00Z, fees
  $21.96, funding −5,887.94, wall exit at last in-window 5m close — sealed tail
  untouched).
- B3 BEST-LEG-PRIOR: −12,645.24 (selection overlay, prior folds only; F1 default
  LEG-1). Even oracle-ish leg selection inside this family set stays negative.

## Combo per-fold nets ($) — attribution walls
F1 −24,991 · F2 −12,330 · F3 −39,078 · F4 −10,639 · F5 +11,550 · F6 +10,876 ·
F7 −100 · F8 +9,504 · F9 +4,295 · F10 −12,706.
The only positive folds (F5/F6/F8/F9 ≈ 2024-2025 bull stretch) do not cover the
2021-2022 and 2025 losses.

## Reading (evidence, not rescue)
- LEG-1 alone contributes −46.5k of −63.6k: 3,795 round-trips × ~$12 fees+spread ≈
  $45.5k cost base on a symmetric ±1% TP/SL book with no gross edge (PF 0.78).
  Frequency×cost kills it — consistent with program priors (P-27 class).
- The two slowest legs (4h spread turns, 226-401 trades) are the only positive
  cells — cost drag, not signal, is the dominant differentiator inside this set.
- B1 buy-and-hold (+10.7k) dominates every active cell and the combo: the
  portfolio adds no value over passivity on this window under frozen costs.
- DSR: combo has 6,080 trade observations ≥ 100 — DSR computed in artifact;
  N_A_NO_SEARCH for PBO (no selection grid; owner-pinned params).
- NO parameter rescue, NO leg removal, NO re-run under relaxed costs after this
  PnL is visible (CLAUDE.md invariant). Any follow-up (e.g. slow-leg-only sleeve)
  requires a NEW plan with fresh identity and ancestry review vs this row.

## Gate table
| gate | verdict | evidence |
|---|---|---|
| two-key GO | PASS | auth/GO_RECORDED.json (A7 sha-pinned + owner verbatim) |
| heavy lock | PASS | acquire E_SCORED_CELLS, released FINISHED rc=0 |
| cells ≤ budget | PASS | 7/12 |
| artifact write | PASS | 3 stress JSONs + 7 ledger rows, digests above |
| dry-run pre-gate | PASS | dry_run/btcombo6_dry.json (freeze commit) |
| A7 prelaunch | PASS w/ findings | audits/A7_PRELAUNCH.md (remediated F-1..F-3) |
| reproduction | PENDING | scored_repro/ (R-REPRO lane in flight) |
