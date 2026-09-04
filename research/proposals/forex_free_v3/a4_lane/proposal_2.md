# FXFV3-A4-P2 — Rationale: Policy-rate differential divergence trend at a weekly clock

Lane A4, cycle FOREX-FREE-V3. Outcome-blind; written 2026-09-04. Companion to
`proposal_2.json` (authoritative for every frozen constant).

## Why this mechanism belongs in V3

V3's question is whether **macro conditioning on adopted policy-rate data**
adds after-cost information on the free 7-pair universe at daily-or-slower
clocks. This proposal takes the slowest honest version of that question: the
**change** in the point-in-time policy-rate differential over 26 weeks, read
at a weekly Wednesday decision point, holding one week. It is carry-adjacent
by construction, which is exactly why the frozen financing formula and the
dual book (price-only vs financing-adjusted, sign non-inversion gate) are
treated as first-class design elements rather than afterthoughts.

## Key design distinctions frozen ex ante

- **Change, not level.** Classic carry monetizes the differential LEVEL
  (Lustig-Roussanov-Verdelhan level factor, crash-risk literature). This
  proposal conditions on the trailing 26-week CHANGE — central-bank
  divergence — and the packet discloses the distinction as a novelty feature
  for A7-N. The financing term still uses the level (frozen formula), so the
  dual book directly tests whether financing manufacture is at work.
- **Slower than V2's fastest rejection mode.** V2 died to negative gross edge
  on intraday mechanisms before costs. A weekly clock with ~2-5 flips per pair
  per year carries ~9-21 bps/year cost drag per pair at base tier — the
  arithmetic a feasibility check can verify without any PnL.
- **Three arms.** Anchor: 26-week lookback. Neighbour: 52-week lookback
  (nearby variant that must preserve sign). Control: shuffled-vintage timing —
  every vintage availability stamp shifted +182 days, rates untouched —
  preregistered to NOT reproduce the anchor if contemporaneous divergence
  reading is the operative ingredient.
- **Equality => NO_TRADE** (no threshold, no hysteresis): the only
  sign-neutral case is exact equality of the as-of differential at the two
  instants, which is measure-zero and needs no tuned buffer.
- **Holiday Wednesdays are whole-week NO_TRADE**, never shifted to Thursday —
  a re-clock would be a forbidden variant operation.

## Known honest weaknesses

- The predictability literature the packet cites is honest about fragility:
  medium-horizon monetary fundamentals predictability is sample-fragile, and
  nothing in it establishes an after-cost weekly edge. The 26-week window is a
  frozen design choice, not a literature parameter; the 52-week neighbour is
  the only fragility probe allowed this cycle.
- The scored window loses ~7 months to warmup (26 weeks of bars needed by the
  benchmark, snapshot starts 2020-01-30); this is disclosed and counted as
  warmup_discarded, not hidden.
- Fold F1 is shortened by that warmup; the 2/3-folds gate still applies
  unchanged, which makes the gate harder, not easier — accepted ex ante.
- BIS live-fetch warmup coverage is NOT_PROVEN_ON_LIVE_FETCH per
  `data_authority_v3.json`; the P3/Q data-hash gate must prove it or the
  proposal is BLOCKED_DATA_OR_SELECTION.
