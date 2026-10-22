# AMENDMENT — SOURCE SWITCH: Polymarket primary price source (owner round 9, 2026-10-10; FROZEN DRAFT — activates only under the program's standing gate)

Owner instruction: switch the shared paper program's PRIMARY price source to
Polymarket's native public API for NBA, WNBA, men's-international soccer and
WSL. NOT Synpath. PAPER ONLY — no real orders to Polymarket, ever. The old
source (The Odds API / Pinnacle h2h) becomes COMPARISON-ONLY from the frozen
cutover; NO auto-fallback when Polymarket lacks a market.

## Frozen laws (config@3 to implement)

1. **Fixture↔event join:** by both teams (crosswalk) + kickoff UTC + league
   + stage; ambiguous joins refused. NBA/WNBA: moneyline only, same result
   definition as the model (no draws). Soccer/WSL: FULL Home/Draw/Away for
   90 minutes; Polymarket's 3 separate YES binaries must be proven
   same-event (one event id, kickoff tolerance ≤3600s, per-market verbatim
   90-min rule). NO(Home) is never AWAY. Season futures, handicaps, props,
   and knockout markets with non-90-min payout rules are EXCLUDED.
2. **Read-only Gamma/CLOB:** snapshots append-only (fetched_at, event/
   market/token ids, resolution rules verbatim, market status, body hashes).
   Quotes only strictly before the league anchor (NBA/WNBA T0−6h10m;
   soccer/WSL kickoff−6h). Execution price = walk-the-book ASK for the $5
   stake (multi-level; depth check; budget_short must be 0) — never
   midpoint/last/site percent.
3. **Fee/EV:** Sports taker fee = 0.05 × p × (1−p) per share (pinned docs +
   docs worked table), counted ONCE in the d_eff denominator; the wallet's
   c = 0.02 stays the GENERIC friction buffer — no double-count, no
   omission. EV/PnL under the $1-contract mechanism (win: size−5;
   lose: −5).
4. **Wallet laws unchanged:** one shared $1,000 wallet, $5 stake, $100
   shared open cap, frozen EV threshold 0.05, drawdown gate, one flock.
   **ONE paper decision per fixture across ALL sources** — no
   Polymarket+bookmaker duplicate rows. Old-source rows are append-only
   history; never edited/deleted.
5. **NOT_RUN taxonomy (per fixture, with reason):**
   NOT_RUN_NO_MARKET, NOT_RUN_MARKET_MISMATCH (cross-match/incomplete),
   NOT_RUN_RULES_MISMATCH (payout ≠ model definition/stage law),
   NOT_RUN_KICKOFF_MISMATCH, NOT_RUN_SNAPSHOT_STALE, NO_QUOTE_DEPTH,
   NOT_RUN_DUPLICATE, BLOCKED_* for gates. From cutover, a missing
   Polymarket market is NOT_RUN_NO_MARKET — the old source is never
   auto-fallback.
6. **Per-league model laws unchanged:** WNBA B1-WNBA, NBA nba26 PIT path,
   soccer-men B1 (UNL league-phase windows only per competition_law),
   WSL B1 K=24/ν=0.55/HCA=40 (D−1 day-batch). NO B1→B1R switch; NO
   World Cup/Euro additions (own gates incomplete). **NFL stays OUTSIDE
   the shared paper program** (it has its own live prospective cycle).
7. **Settlement:** per each market's own rules (postpone stays open /
   cancel per verbatim law) reconciled to the model's target result before
   a row closes; divergences recorded in-row.
8. **Dashboard:** reads the REAL ledger only; self-updates per cadence;
   sandbox renders are labeled SANDBOX and never shown as real.

## Gate structure (exactly as governance stands)

- **Shared activation gate (the program's own standing phrase, registered
  NOT_CONSUMED):** `GO SPORTS PAPERTRADE EXEC V1 RUN ALL` — typed by the
  owner activates the cutover for leagues that are READY (all gates green
  at that moment).
- **WSL split gate (registered on WSL-WINPROB-PROSPECTIVE-PAPER-PREP-V1):**
  `GO WSL WINPROB PROSPECTIVE PAPER V1 BET_PAPER` — additionally required
  for WSL BET_PAPER rows (its AMENDMENT_R4 freeze governs). Recorded here
  as the exact split; no workaround.
- No self-typing; wrong form dies unconsumed; this amendment consumes
  nothing.
