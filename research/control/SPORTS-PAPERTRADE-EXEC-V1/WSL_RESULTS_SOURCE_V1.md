# WSL RESULTS SOURCE V1 — frozen law (owner order 2026-10-20)

## Source (qualified)

The settlement source for WSL paper bets is the **Polymarket UMA resolution
of the bet's OWN tracked 3-YES 90-minute markets** — identity by
construction: the ledger MARKET_QUOTE row stores the Gamma `event_id` and
each leg's `market_id`; no name/date guessing ever occurs.

Settlement-eligible ONLY when, per the Gamma event payload (journaled raw +
sha256 + retrieval UTC under `<data-root>/data/wsl_results/`):
- each tracked market is `closed=true` and `umaResolutionStatus=resolved`;
- `outcomePrices[0]` (outcomes[0] = "Yes") is exactly 1.0 for EXACTLY ONE
  leg and exactly 0.0 for the other two;
- the market question carries the bet's kickoff date.

Semantics: awarded results resolve to the official score (settles
normally); postponed / cancelled / voided NEVER produce a clean one-of-three
YES=1 ⇒ inconclusive ⇒ the bet stays OPEN (no inference, no premature
refund).

## Execution path (unchanged pinned core)

`ops_service._fetch_results(WSL)` → `wsl_results.fetch_wsl_settleable()`
→ staged `{match_id: {result, source_ref}}` → the STANDARD pinned
`cmd_settle` → `risk.settle` → append-only ledger rows
(`source_ref = "polymarket_uma event=… winner=… markets=… resolvedBy=…").
GO gates (`require_gate`) and chain/hash law unchanged; WSL settle keeps
the ESPN_SETTLE_THROTTLE cadence.

## Gate (wsl_lane.cmd_settle)

A staged WSL results file is lawful ONLY when EVERY entry's `source_ref`
starts with `polymarket_uma event=` and `result` ∈ {HOME, DRAW, AWAY}.
Anything else (hand-built files, guessed scores, other sources, empty) ⇒
`BLOCKED_NO_RESULTS_SOURCE` — bets stay OPEN. This REPLACES the prior
blanket refusal (which existed solely because no source was pinned).

## Other sources probed and REJECTED as unusable for WSL (2026-10-20)

- The Odds API `/v4/sports`: 81 sports, zero WSL entries (no scores key).
- ESPN `soccer/eng-w.1`: endpoint exists but zero events in any window
  (league object unnamed/empty) — unusable.
