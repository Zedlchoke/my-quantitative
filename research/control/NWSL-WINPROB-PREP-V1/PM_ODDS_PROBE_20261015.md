# NWSL-WINPROB-PREP-V1 — POLYMARKET ODDS PROBE 2026-10-15 (read-only; no order API)

Scope: owner instruction item 4. Read-only Gamma/CLOB public market data.
No order API, no account, no purchase. Bytes pinned under
`~/.my-quantitative-data/nwsl-winprob-prep-v1/harvest_20261015/`.

## Market presence

- Gamma public-search "NWSL": 50 events (search-capped sample) — **48 closed
  match events (2026 season) + 2 open futures** ("NWSL: 2026 Winner /
  Runner-Up", 32 markets each). Full historical census (pre-2026 seasons,
  complete pagination) = successor lane task (`NOT_RUN_CENSUS_COMPLETE`).
- **No open NWSL match market exists today** (2026 regular season ends
  2026-11-01; playoff markets not yet listed) ⇒ live-match odds leg today:
  `NOT_RUN_NO_OPEN_MARKET` (honest, not failure).

## Three-YES structure + 90-minute law

Every sampled match event carries exactly **three YES/NO markets of ONE event
slug** (`nwsl-<away>-<home>-YYYY-MM-DD`): Home win / Draw / Away win — the
same shape as the qualified WSL lane. Draw market resolution pinned verbatim
from bytes (round 1, re-confirmed): *"This market refers only to the outcome
within the first 90 minutes of regular play plus stoppage time"* + Flashscore/
Sofascore fallback chain + no-post-revision clause. The Home/Away market
descriptions do NOT contain the 90-minute clause in the sampled text — the
successor must pin the per-market settlement wording for ALL THREE legs of
each event before any BET_PAPER-grade use (`NOT_RUN_RULES` if any leg lacks
it — inherited WSL §4 law).

## Historical vs prospective odds (owner-required separation)

- **Historical (pre-2026 and 2026 archive):** closed match events RETAIN a
  timestamped price series — demonstrated: draw token of `nwsl-pri-chi-2026-
  07-24` returned **13 daily points via CLOB `prices-history` (startTs/endTs,
  fidelity=1440: 0.545 → 0.185)**. This is a genuine PIT-grade historical
  path (time-bucketed line history). Caveats measured: fidelity=60 returned
  0 points for this low-volume market (finer granularity availability must be
  measured per market); prices-history buckets are NOT executable quotes —
  execution-grade use still requires the pre-anchor snapshot law. Verdict:
  **historical odds = Class-B candidate** (timestamped but bucketed; two-sided
  YES/NO within one event; certain 1:1 join via slug+date; rights = public
  read API), `NOT_RUN` today pending the census + fidelity measurement.
- **Prospective (capturable):** the program's lawful pattern (append-only
  snapshots fetched strictly pre-anchor, `fetch_ts < anchor`, in-lock appends)
  applies unchanged; the WSL lane is the precedent. When NWSL match markets
  list, capture requires the SAME discipline. Nothing may be captured until a
  separate owner decision adds NWSL to the paper scope (`NOT_RUN_NWSL_PAPER_
  HOOKUP` stands from round 1).

## Ask / depth / fee / timestamp evidence

- Open book mechanics demonstrated on ONE open futures token (channel
  evidence only, NOT a 1X2 leg): "Will Angel City FC win the 2026 NWSL?" —
  3 ask levels, top ask 0.99 × 70.92 shares, total ask depth ≈ $188. Channel
  alive; the level-1 depth alone exceeds a v3 1%-equity stake (~$10.22 ⇒
  ≈10.3 shares), but futures depth says nothing about match-market depth.
  **Match-market depth for the 1% stake: `NOT_RUN_NO_OPEN_MARKET`.**
- Fee law (program-wide, frozen): PM Sports taker fee `0.05·p·(1−p)` per
  share inside the walked cost (fee-once-in-denominator, CAPITAL-V3 §3) —
  carried, unchanged.
- Timestamps: Gamma events carry `startDate`; CLOB carries the authoritative
  book/history timeline. Any lawful EV computation requires BOTH the
  pre-anchor snapshot and `line_update ≤ snapshot_time < tip` (Class-A row
  test) — untouched today by definition (no open markets).

## Verdict

`SOURCE_READY` for the odds CHANNEL (public read API + 90-min draw law +
timestamped history + lawful prospective pattern), `NOT_RUN_ODDS` for any
concrete odds number today (no open markets; historical census + fidelity
measurement owed). No order API was called; nothing was captured.
