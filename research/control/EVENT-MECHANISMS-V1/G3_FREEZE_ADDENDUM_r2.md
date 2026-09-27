# G3 FREEZE ADDENDUM r2 — EVENT-MECHANISMS-V1 (2026-09-27, pre-implementation ambiguity closure)

Closes spec ambiguities BEFORE any computation exists (§16.1: ambiguity
returns to A1 before scoring; zero PnL computed anywhere as of this
addendum). No constant of `G3_FREEZE.md` changes; everything below makes
unstated mechanics explicit so both implementations build the same object.

## R2-1 Price/return basis (L-SAMV1-1 law)

- **Raw OHLC only.** Vendor `adjusted_close` is FORBIDDEN anywhere in
  signal, direction, fills, or evaluation (as-of-pull adjustment =
  lookahead by construction).
- Direction (A1) = sign of raw (close − open) of the direction session.
- A1 entry/exit and A2 entry/exit at raw open/close of the stated sessions.

## R2-2 Corporate-action window exclusion (replaces the need for PIT-adjusted series)

- For every candidate event, if the window [entry_session … exit_session]
  contains ANY dividend/split ex-date for that name (from the EODHD
  div/splits tables on disk, dated action dates), the event is EXCLUDED.
- Excluded-event counts are measured and disclosed per fold (a feasibility
  number, not PnL). If exclusions remove >40% of any fold's events, record
  CONTAMINATION_HIGH and stop for A1 adjudication before proceeding.
- B1 both-direction extreme-print law (STOCKS-AMIHUD-RETEST frozen law)
  applies to entry/exit bars: extreme prints both directions excluded and
  counted; volume-0 bars unfillable (X1/X2 law).

## R2-3 Event-set mechanics

- A1 forms: exactly `10-Q`, `10-K`. Amendment forms (`10-Q/A`, `10-K/A`)
  EXCLUDED (original-vintage-only event set; the amendment arm was dropped
  by the G1 court).
- A1 event identity: (issuer, acceptance_instant) unique — multiple forms
  in one accession/acceptance = one event.
- A1 sequencing: direction_session = first session whose close occurs
  after acceptance (per name); entry = open of the NEXT session after the
  direction session; exit = close of session entry+H−1 (H = hold sessions,
  raw-session count). If the name lacks H sessions post-entry, exit at the
  name's last available bar and count the event as DELISTING_EXIT
  (disclosed; not dropped silently).
- A2 event: per freeze (issuer-day net open-market BUY value ≥ $100,000,
  transactionCode 'P', officers/directors); entry = first session open
  strictly after the acceptance instant; hold/exit same convention. Field
  names of form4_stream rows are MEASURED by the lane from bytes and
  recorded; any schema ambiguity returns to A1, never guessed.

## R2-4 Timezone law

- `acceptanceDateTime` values are UTC (Z-suffixed, measured). Strata
  computed in `America/New_York` via `zoneinfo` with DST-boundary fixtures
  (spring-forward/fall-back dates in the test set). ET session clock:
  [09:30,16:00) regular; weekend/holiday acceptances bucket separately
  (a session date = a date on which the name has a bar).

## R2-5 Data-surface choice law

- Price panel: the lane verifies which restored surface carries RAW OHLCV
  for the full cohort (NG6 panel vs re-pinned eod_cache), records digest
  verification of the chosen surface, and documents the choice. Digest
  fail-closed at load for every staged artifact (P-13/PIN pattern).

## R2-6 Pre-GO computation boundary (what lanes may compute)

ALLOWED pre-GO: signal/event constructions, decision sets, per-event
entry/exit prices, per-side cost bands, fold POPULATIONS, ancestry/
representation rhos, feasibility grids, dry-run record IDs.
FORBIDDEN pre-GO: any aggregation of trade returns into expectancy/
PF/PnL/drawdown at ANY depth (§19.2). G5 independent-implementation
agreement compares decision/fill/cost records only — never aggregates.
