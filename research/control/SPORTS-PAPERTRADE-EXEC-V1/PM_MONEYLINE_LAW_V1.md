# PM MONEYLINE 2-WAY LAW — NBA/WNBA (pre-cutover build, owner order 2026-10-20)

## Source law
- Moneyline market = the market in the joined Gamma event whose
  `outcomes` are EXACTLY the two team display names (2 outcomes).
  Derivatives REFUSED: Team to Score First, Odd/Even, Halftime, Exact
  Score, Spread, Corners.
- Team identity: normalized containment of each ledger team name in the
  outcomes (bidirectional; short forms resolved by the pinned crosswalk
  inversion where applicable — e.g. '76ers' matches 'Philadelphia 76ers').
- Executable quote: CLOB `/book?token_id=` per leg. `clobTokenIds[0]` =
  YES on outcomes[0]; buying YES on the chosen leg IS the moneyline bet.
  Gamma `outcomePrices` are INDICATIVE ONLY — never a quote.
- Fee: taker 0.05·p·(1−p) per share, applied once per filled share
  (mirror of the pinned soccer/WSL formula on a 2-outcome market).

## Live evidence (2026-10-20)
Event 1185701 (76ers vs Knicks, market 5676021): joined, outcomes
["76ers","Knicks"], CLOB book walk at 1022c stake: best_ask 0.39,
VWAP 0.4019, 10.22 shares, spend 411c incl. 12c fee, 1 level. Token
1853077548…(HOME) journaled raw+sha.

## Status
MACHINERY_READY (pre-cutover build). NOT authoritative until:
1) owner consumes POLYMARKET_CUTOVER GO;
2) exec WSL-style lane wired per league (this module + tests are the
   sandbox reference);
3) A7 prelaunch on the live decision path.
