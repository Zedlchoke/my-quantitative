# FEE_ONCE_FINDING — is the Polymarket taker fee deducted exactly ONCE per lane?

Cycle: PAPERDESK-FIXALL-NCAA-V1 / workstream U1 (owner package 2026-10-21).
Method: full trace of ONE Polymarket bet from book-walk price to final
EV_net, both lanes, against the PINNED core (read-only; pinned bytes never
touched). Battery lock: `tests/papertrade_exec/test_upgrade_u1.py`
(hand-computed numeric examples, pure functions, no ledger, no network).

## The fee law (reference)

`fee_per_share(p) = 0.05·p·(1−p)` — pinned source
`polymarket_source.py:467-479` (`PM_SPORTS_TAKER_FEE_RATE = 0.05`,
REMEDIATED form, `ERRATUM_FEE_LAW.md`, docs_fees2.html), charged per share
AT PURCHASE (pinned `walk_the_book`: `fee = taker_fee_per_share(p) * take`,
line 530). Max 0.0125/share at p=0.5; symmetric f(0.30)=f(0.70)=0.0105.
Single-source in the exec layer: `laws.py:31 PM_TAKER_FEE_RATE = 0.05`.

## Lane (a) — standard (NBA/WNBA/NCAA-*/SOCCER post-cutover): FEE ONCE ✓

Trace:

1. `research/papertrade_exec/pm_moneyline.py:214-253 walk_ask` — per level:
   line 240 `fee += 0.05 * lvl["price"] * (1 - lvl["price"]) * take`
   (the fee law, once per share); line 241
   `spend += cost + 0.05·p·(1−p)·take` — `spend` is FEE-INCLUSIVE;
   line 247 `vwap = spend / filled` — the fee-inclusive average cost per
   share.
2. `pm_quote_source.py:63` — the router passes `vwap_ask` through verbatim.
3. `execute.py:1533` (2-way) / `execute.py:1562` (3-YES) —
   `odds = round(1.0 / l["vwap_ask"], 6)`. Because vwap is fee-inclusive,
   `odds = filled_shares / (cost + fee)` — the SAME `d_eff` algebraic form
   as the WSL lane: the fee enters ONCE, in the denominator.
4. Pinned core EV: `risk.py:133` `evs = {k: ev_net(p[k], d[k])}` with
   `risk.py:22-24` `ev_net = p·d − 1 − COST_FRICTION`
   (`__init__.py:17 COST_FRICTION = 0.02`, "frozen friction ASSUMPTION").
5. Pinned settle: `risk.py:276` `pnl = round(stake·(odds_frozen[leg] − 1))`
   — odds are already fee-baked; the payout carries NO second fee.

The dispatch packet's premise ("standard lane stores RAW 1/vwap_ask, no fee
baked") is DISPROVEN by `pm_moneyline.py:240-241,247`: the walk has carried
the once-per-share taker fee inside `spend`→`vwap` since its first commit
(d5854aea, round-10: "CLOB ASK walk at stake with once-per-share taker
fee"; live probe evidence "fee 12c"). The packet's line ref (~1266) also
predates the current bytes (odds law now at 1533/1562).

Hand-checked example (battery T-U1-A/B): ask 0.50 ⇒ fee/share
0.05·0.5·0.5 = 0.0125 ⇒ vwap 0.5125 ⇒ odds 1.95122 (vs raw 2.0).
EV(p=0.55) = 0.55·1.95122 − 1 − 0.02 = 0.053171. Without the fee in odds it
would have been 0.55·2 − 1.02 = 0.08: the fee in the odds is worth
−0.02683/$ at p=0.55 — bigger than the flat buffer.

## Lane (b) — WSL: FEE ONCE ✓

Trace:

1. Pinned `walk_the_book` (lines 501-546): fee per level into
   `fee_total_usdc` (line 530/535); `spend` EXCLUDES fee (line 533).
2. `wsl_lane.py:376-401 walk_budget_for_stake` — solves `B + F(B) == stake`
   (outlay across asks+fees consumes exactly the stake).
3. `wsl_lane.py:362-373 fee_law_d_eff` — `d_eff = filled_shares /
   (spend_usdc + fee_total_usdc)`; docstring lines 364-366 (R5-2): the
   taker fee "exactly ONCE in the denominator — the per-level fees enter
   through their own sum, never a second time".
4. `wsl_lane.py:509,512` — quote odds = d_eff.
5. Same pinned-core EV (`p·d_eff − 1 − 0.02`) and same settle:
   `stake·(d_eff − 1) = shares − stake`, which equals the true net win
   `shares·$1 − outlay` EXACTLY because outlay == stake (documented at
   `wsl_lane.py:366-369`).

Hand-checked example (battery T-U1-C): walk {spend 4.00, fee 0.12, shares
10.0} (ask 0.40 ⇒ fee/share 0.012 × 10 shares = 0.12): outlay 4.12,
d_eff = 10/4.12 = 2.427184… Settle at stake 412c: 412·(d_eff−1) = 588c =
shares·100 − outlay·100 = 1000 − 412 ✓ exact, no second fee.

## The flat 0.02 — a frozen BUFFER, not a second fee

Both lanes subtract the flat `COST_FRICTION = 0.02` ONCE at the EV gate
(`risk.py:22-24`, applied at `:133`; mirrored exec-side as
`laws.py:29 FLAT_FEE_PRE_CUTOVER = 0.02`,
`decision_pipeline.py:93`). It is the pinned core's frozen friction
ASSUMPTION ("pre-cutover Pinnacle EV convention — an estimate, kept
verbatim"), applied by design to EVERY lane on top of lane-specific fee
baking. It is NOT the PM fee and never enters settlement. Effect: EV_net is
understated by exactly 0.02/$1 on PM lanes — the gate is CONSERVATIVE
(blocks marginal bets); it can never overstate. Removing it would be a gate
retune of the pinned core (owner territory) — NOT done, NOT needed.

## Verdict

**CORRECT — the PM taker fee 0.05·p·(1−p) is deducted exactly ONCE in BOTH
lanes** (standard: inside `spend`→`vwap`→`odds`; WSL: inside
`spend+fee`→`d_eff`). No double-charge, no missing fee, no exec-layer fix
required. NO change made to any runtime file for U1.

Numeric bias of the flat buffer vs the true price-dependent fee (per $1
staked, fee-only drag ≈ 0.05·(1−q) at entry price q after inversion; buffer
0.02): at q=0.50 true drag ≈ 0.0244 → buffer UNDERSTATES cost by ≈ 0.0044;
at q=0.30 true drag ≈ 0.0338 → understates by ≈ 0.0138; at q=0.70 true
drag ≈ 0.0148 → buffer OVERSTATES cost by ≈ 0.0052 (conservative direction:
may refuse a marginal bet, never places one the fee would sink). The frozen
assumption is documented; any retune is an owner decision.

## Adjacent observations (documented, NOT fixed — no money-law defect)

- **Walk-target asymmetry**: `walk_ask` fills `filled_shares == stake`
  (outlay floats at stake·vwap < stake) while the WSL walk fills
  `outlay == stake`. The DECISION money law ("wager stake at decimal odds
  d") is internally consistent in both lanes — `stake·(d−1)` is exactly the
  spend-the-full-stake-at-vwap economics, so EV and settle are correct
  functions of (stake, d). The standard lane's EVIDENCE walk would
  under-fill the position its own settle models; at $5 stakes on liquid
  books (single-level fills) d is identical either way, so the practical
  bias is nil. Owner-note only; any unification is an evidence-capture
  change, not a fee fix.
- **Settlement of pre-existing OPEN bets** keeps their frozen odds — every
  decision row is self-consistent (append-only law); nothing to migrate.

## Interim safe state

No interim needed: fee once, both lanes; flat buffer conservative by
construction. If a future owner wants the buffer re-examined, the fix
requires a pinned-core re-pin (`risk.py` COST_FRICTION usage) plus a fresh
owner GO — out of scope here, pinned bytes untouched.
