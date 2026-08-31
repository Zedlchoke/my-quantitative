# Asset-specific PIT checklist

## Crypto perpetuals

- exchange/server timestamps, candle close and ingestion cutoff;
- contract listing/delisting and universe membership by date;
- funding announcement versus settlement time and revision behavior;
- open interest/liquidation/order-flow publication latency;
- executable bid/ask or frozen slippage model, never free midpoint fills;
- maintenance gaps, symbol migrations and venue-specific contract metadata.

## Stocks

- PIT security master, ticker changes, listings, delistings and index membership;
- earnings/fundamental announcement timestamp, timezone, vintage and revisions;
- split/dividend/ex-date/pay-date handling and adjusted/unadjusted policy;
- exchange calendar, early close, halt and auction eligibility;
- borrow locate availability, fee timestamp and dividend liability for shorts;
- spread, commission, impact, capacity and delisting terminal cashflow.

## Forex

- bid and ask timestamps, quote staleness, crossed quotes and provider timezone;
- pair convention, pip/point value and base/quote/account-currency conversion;
- named-zone sessions, DST, holidays and weekly market boundary;
- rollover publication time, long/short asymmetry and triple-roll schedule;
- central-bank/event release availability, vintage and embargo;
- provider gaps and executable-side fills; never substitute mid silently.
