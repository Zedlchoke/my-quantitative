# FX2-A4-P2 — Pre-release liquidity-withdrawal premium: scheduled-macro-release timing in USD pairs, anchored on the New York rollover clock

Lane: `forex-f2-a4-calendar` (A4 — sessions, holidays, DST, macro clocks; macro-event timing economics).
Outcome-blind hypothesis document. The JSON file `proposal_2.json` is authoritative; this narrative
restates the same content for humans.

## Mechanism

Scheduled US macro releases are known to the minute in advance from official agency calendars, and
FX price discovery around them completes in seconds-to-minutes after the print (Andersen, Bollerslev,
Diebold, Vega 2003, AER). In equities, expected returns concentrate *before* scheduled announcements
(Lucca & Moench 2015, JF) — scheduled announcements are intervals of concentrated priced risk.

**Hypothesis.** The same announcement-timing economics exists in spot FX: market makers cap inventory
and thin quotes ahead of known release times, so risk-transfer flow into a thinning book moves price
systematically before the print. A holder of the standard G10-vs-USD basket who owns only the
preregistered pre-release window earns, on average, a spread- and rollover-adjusted premium versus
identical clock durations on matched non-release days. This is timing economics, not macro
forecasting: no released value, surprise or vintage enters any signal.

**Expected counterparty.** Dealers and fast-money liquidity providers who de-risk before releases and
are compensated by pre-release price concession; investors unwilling to hold scheduled-event exposure.

## Signal fields and publication clock

- `release_timestamp` — official wall time of each frozen-list event (BLS NFP and CPI, typically
  08:30 America/New_York; FOMC decision 14:00 America/New_York), recorded per event as published by
  the agency for that date. Only the timestamp is used — never the outcome.
- `event_pre_window` — `[first NY 17:00 rollover boundary strictly before T, T − 5min]`.
- `matched_non_release_clock` — same duration, same weekday and wall-clock phase on preregistered
  non-release days.
- `post_release_placebo_clock` — `[T + 65min, T + 65min + duration]` (price discovery is complete by
  then per Andersen et al. 2003).
- 1h bid/ask bars; midpoint diagnostics only, never an executable fill.

The clock is public, deterministic, and known before each window opens (no look-ahead). Wall times are
expressed as America/New_York via zoneinfo — DST handled by named-zone rules, never fixed offsets.
The repo's session wall-time labels are SYNTHETIC_TEST_ONLY defaults, so release hours and the
rollover convention must be reconciled to the frozen provider's documentation at freeze. Windows are
never derived from observed profitable hours.

## Formation / holding / rebalance

- **Form** at the first NY 17:00 rollover boundary before each frozen-list release: equal-risk-weighted
  G10-vs-USD basket, all seven pairs.
- **Hold** until T − 5 min (~15.5 h for 08:30 releases, crossing one rollover; ~21 h for FOMC,
  crossing two). Deliberately **does not hold through the release** — the claim is pre-release
  compensation, not print-gambling; a through-release variant would be a different, unauthorized family.
- **Rebalance:** one entry/exit per event; frozen list = 12 NFP + 12 CPI + 8 FOMC ≈ 32 events/year,
  ~64 pair-round-trips/year. Flat between windows.

## Universe and neutralization

All seven frozen pairs (USD on one side of 88% of global trades per BIS 2022, so US releases are the
common clock). The USD-direction component of the primary arm is **declared, not hidden**: it is
decomposed against the declared benchmark per PLAN §13, and a preregistered **currency-neutral
co-test** (dollar-flat equal-and-offset legs from the same pairs) runs on the same three arms to show
whether any premium survives with zero net USD. Concentration gates apply (no pair >30%, no currency
>40%).

## Expected costs

- **Spread:** pre-release windows should carry *wider* spreads (that is part of the mechanism);
  measured side-specific bid/ask per pair/window, never a global pip; spread ×1.5/×2 stresses mandatory.
- **Rollover:** material by design — windows cross one or two NY 17:00 boundaries, so long/short swap
  asymmetry enters the cost identity; authoritative rollover schedules are a hard requirement and a
  declared blocker.
- **Turnover:** low (~64 pair-round-trips/year).

## Anchor / neighbour / negative control

| Arm | Definition | Why it validates/destroys |
|---|---|---|
| **Anchor** | Basket over `[prior NY rollover, T − 5min]` for every frozen-list event | Only arm exposed to scheduled-event liquidity withdrawal. Confirmation requires *both* relative spread widening (the channel operating) and positive after-cost expectancy above the neighbour. |
| **Neighbour** | Identical basket/durations on preregistered matched non-release days (same weekday, same session phase, adjacent weeks), same window count | Shares every clock/basket input except the scheduled release. Mechanism predicts anchor > neighbour after costs; equality means generic overnight/rollover drift — the event-timing claim is dead, and a disguised "hold overnight" strategy is excluded by design. |
| **Negative control** | Identical basket/duration starting T + 65 min after each release (post-discovery), same release days | Same risk, same days, event already resolved — scheduled-event compensation cannot operate. Placebo ≈ anchor destroys the mechanism: returns would be generic intraday drift, not timing economics. |

## Expected regimes and falsification

Larger premium expected in high-uncertainty regimes (tightening cycles, crises), spread widening
concentrated near the release; FOMC windows predeclared as candidate concentration; the hypothesis is
about the frozen-list average, not every window. Falsified by: anchor ≤ neighbour after measured
spread AND rollover costs; no anchor-window spread widening; placebo ≈ anchor; effect only appearing
after relaxing the frozen list/windows (forbidden); single-release-type/pair/fold concentration
failing drop-one gates; non-positive stressed expectancy (spread ×1.5/×2, rollover ×1.5, adverse swap
schedule, one-event delay); or a "currency-neutral" claim without the neutral arm surviving. A failed
family retires as-is — no post-score re-specification.

## External validity risks

Hard data blockers first (see honesty statement): no PIT release-timestamp source in repo; no
rollover authority; bid/ask unavailable; holiday tables SYNTHETIC_TEST_ONLY. Substantive risks: FOMC
release-time convention changes (2011 presser cycle) handled as declared structural breaks via
chronological folds, never re-specification; documented rise-and-partial-disappearance of
pre-announcement premia in the equity literature implies possible decay under electronic
market-making; embargo/early-release incidents and flash events (single event may not dominate a
fold); findings feed-scoped, never "the global FX market" (PLAN §2).

## Trial count

Exactly **3** primary scored trials, serial: anchor → neighbour → negative control. The preregistered
currency-neutral decomposition and the mandatory stresses/context reports recompute the same arms;
every computed cell increments the observed denominator exactly once. No post-score replacement.

## PIT fields and availability (measured repo facts)

| Field | Source | Availability |
|---|---|---|
| Scheduled US release timestamps (NFP, CPI, FOMC), per event official wall time | BLS / BEA / Board of Governors calendars, owner-authorized PIT ingest | **UNAVAILABLE** — no source in repo; only timestamps needed (public deterministic facts), NOT macro vintages; **feasibility-blocked until owner authorizes ingest** |
| 1h bid/ask history ≥8y, 7 pairs, UTC stamps | owner-authorized provider (§2) | **UNAVAILABLE** — 0/7 pairs, fail-closed |
| Rollover/swap schedule with long/short asymmetry, triple-roll, holiday adjustments | provider/broker schedule | **UNAVAILABLE** — hard requirement (windows cross NY 17:00); fail-closed without it |
| Session/DST clock (NY wall times, rollover boundary) | IANA tzdb via repo zoneinfo | **AVAILABLE** — real and tested; provider-convention reconciliation needed at freeze |
| Holiday tables | authoritative per-currency source | SYNTHETIC_TEST_ONLY — blocked for scoring use |
| PIT macro vintages / released values | not used by design | UNAVAILABLE, and deliberately not required |

## Literature (all retrieved 2026-09-02T23:57:41Z)

1. Andersen, T.G., Bollerslev, T., Diebold, F.X., Vega, C. (2003), *Micro Effects of Macro
   Announcements: Real-Time Price Discovery in Foreign Exchange*, American Economic Review 93(1),
   38–62, DOI 10.1257/000282803321455151 — price discovery completes in seconds-to-minutes; grounds
   the T+65min placebo and the release-clock premise. [VERIFIED at AEA]
2. Lucca, D.O., Moench, E. (2015), *The Pre-FOMC Announcement Drift*, Journal of Finance 70(1),
   329–371 — equities: returns concentrate before scheduled FOMC announcements; cross-asset analog.
   [Existence and bibliographic location VERIFIED via citing-literature metadata; exact DOI string
   UNVERIFIED and not relied upon.]
3. Antolin-Diaz, J., Cenedese, G., Han, S., Sarno, L. (2023), *US Interest Rate Surprises and Currency
   Returns*, SSRN 4565111 (R&R, Review of Financial Studies) — US monetary-policy events are a priced
   FX channel. [VERIFIED at SSRN and author research page]
4. BIS (2022), *Triennial Central Bank Survey of FX and OTC Derivatives Markets in 2022*,
   https://www.bis.org/statistics/rpfx22_fx.htm — USD on 88% of trades; UK+US 57% of turnover.
   [VERIFIED]
5. Ranaldo, A. (2009), *Segmentation and Time-of-Day Patterns in Foreign Exchange Markets*, Journal of
   Banking and Finance 33, 2199–2206 — context only: FX time-of-day structure exists, which is why the
   neighbour and placebo arms are required. [VERIFIED]

## Prohibited shortcuts

None apply: no RSI/EMA grids (single mechanism-derived configuration; no grid search authorized); no
provider volume treated as global volume (volume never used; spread is a feed-scoped diagnostic and
cost); no carry from today's rates (no rates in any signal; rollover only as a measured cost line with
authority declared missing — a blocker, not a workaround); session/event windows from official agency
calendars and the preregistered NY rollover convention, never from observed profitable hours; midpoint
never labeled executable (side-specific bid/ask required; fail-closed without it).

## Ancestry

First-generation proposal; no previously rejected or scored FX family exists in this repo, so nothing
is being rescued. Not a disguised carry family (no rate data used; the claim is timing, not interest
differentials) and not a post-hoc session filter (windows are ex ante agency-calendar facts).
Declarative ancestry: transports scheduled-announcement risk-premium logic (Lucca-Moench 2015,
equities) and FX announcement price-discovery evidence (Andersen et al. 2003) into a G10 spot-FX
timing family anchored on the New York rollover clock, with controls designed to separate event-window
compensation from generic overnight/session drift.

## Honesty statement

Feasibility-blocked at selection absent owner authorization on three independent grounds: real FX
bid/ask UNAVAILABLE (0/7, fail-closed); PIT release timestamps UNAVAILABLE in repo (agency calendars
must be authorized and ingested; timestamps only — vintages unused); rollover/swap authority
UNAVAILABLE and required because windows cross the rollover. Holiday tables SYNTHETIC_TEST_ONLY. The
session/DST clock is real and implemented. No claim is made that any required data currently exists.
