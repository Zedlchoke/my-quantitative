# FXFV3-A5-P1 — Policy-divergence-gated daily trend (PIT vintage semantics)

Lane A5, cycle FOREX-FREE-V3. Outcome-blind. MACRO-CONDITIONED (lane quota carrier).
Machine-readable packet: `proposal_1.json` (authoritative).

## Mechanism (one paragraph)

A daily time-series momentum book on the frozen 7-pair universe whose entries require the
point-in-time policy-differential drift to AGREE with the price trend. The claim under test is
narrow: the macro gate adds after-cost information over an identical ungated momentum book —
not that macro direction alone predicts FX. Rossi (2013) is carried as the honest counterweight.

## Conditioning series

- BIS WS_CBPOL policy rates, areas US/EA/GB/JP/CH/CA/AU/NZ — AUTHORIZED_FOR_V3_RESEARCH.
- PIT rule: a decision at T never reads a row with `available_time_utc > T` (P0 regression-pinned);
  BIS effective-date semantics; date-only evidence = end-of-UTC-day upper bound, so a rate change
  becomes signal-eligible at the first daily decision strictly after its availability stamp day.
  Missing evidence fails closed.
- ECB SDMX EXR deliberately NOT used (EXR is not a policy-rate series; BIS alone carries the quota).
- Live warmup coverage is NOT_PROVEN_ON_LIVE_FETCH; proposal is BLOCKED if the P3/Q macro snapshot
  gate fails — no silent price-only fallback.

## Frozen constants

| quantity | value |
|---|---|
| decision clock | completed 16:00 America/New_York flat bar (daily) |
| momentum window m | 21 daily bars |
| differential drift g | d(t) − d(t−63), as-of reads at each past decision instant |
| activation | strict sign agreement, g ≠ 0 (no threshold parameter) |
| fills | open of next existing 16:00-NY bar (Friday decision fills Monday) |
| exits | state flip at next daily bar; force-flat at fold boundaries |
| warmup | 63 daily bars (schedule activates ~2020-05-01) |
| notional | 10000 USD |
| costs | 1.5 bps/side base; tiers 1.0/1.5/2.0 → 1.5/2.25/3.0 bps/side, F1-fixed on booked stress PnL; one-event delay stress kept separate (V3-L2) |

## Arms

- **anchor** `FXFV3-A5-P1-anchor`: long base/short quote when m>0 ∧ g>0; short when m<0 ∧ g<0; flat otherwise.
- **neighbour** `FXFV3-A5-P1-neigh` (one presumption away): macro gate as differential LEVEL
  (d vs its trailing 252-day median) instead of drift.
- **causal control** `FXFV3-A5-P1-ctrl`: macro-direction-only (sign(g)), no price trend.
  Preregistered non-reproduction rule: control expectancy > 0 AND PF ≥ 1.10 → control fires → family fails.
- **benchmark** `FXFV3-A5-P1-bench` (unscored reference inside the anchor cell): unconditional sign(m)
  book, identical clock/fills/universe/warmup/costs. Overall incremental alpha = per-pair-day
  after-cost financing-adjusted PnL, anchor − benchmark > 0.

## Carry / dual book

Carry-adjacent: financing per the frozen formula
`price_only_pnl + sign · notional · (r_base − r_quote) · holding_days/365`, per-calendar-day
accrual at the day-start as-of differential; policy-rate ≠ swap/rollover approximation disclosed.
Financing gate: price-only book must not invert anchor expectancy sign.

## Turnover / floors (schedule-level estimates, never optimized)

~1360 decisions/pair full-sample (floor ≥ 40 met by an order of magnitude); anchor 8–30
RT/pair/yr with disclosed macro-freeze flat spells; F1 thinnest (~150–450 panel trades).
Break-even headroom: 21-day moves order 30–200 bps gross vs 3–6 bps round trip.

## Drop-one

Drop-one pair: ≥ 5/7 recomputes keep positive expectancy and PF ≥ 1.00 (inherited min-of-7 5).
Drop-one fold: expectancy stays positive in all 3.

## Novelty

No session geometry anywhere (vs all four forbidden rows: different clock, different observable);
pure differential-direction rule isolated in the control; no rescue operation of any kind. Full
per-row self-check in `proposal_1.json`.
