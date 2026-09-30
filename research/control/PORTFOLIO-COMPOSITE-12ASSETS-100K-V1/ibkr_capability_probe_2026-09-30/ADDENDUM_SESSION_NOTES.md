# ADDENDUM — session notes after the bounded acquisition (2026-09-30)

Does not edit `PROBE_RESULT.json`, `FOLLOWUP_EXPIRED_ROLL.json`, or
`ACQUISITION_REPORT.json`. Those stay as the run that produced them.

## M1 sample gate is only a non-empty check

`ACQUISITION_REPORT.json` sets `m1_sample_days: PASS` when every sample has
`n>0`. Observed windows are not full sessions on the later dates:

- `2021-01-15` BID: NZDUSD 1665 bars, `2021-01-14 13:15` through `2021-01-15 16:59` US/Eastern.
- `2023-06-15` and `2026-09-28`: about 120–345 bars, roughly a two-hour slice
  (XAGUSD `18:00`–`19:59`).

Full M1 from 2021 to now remains `NOT_RUN_SIZE_CAP`. Interior intraday gaps
remain `NOT_RUN_INTERIOR_GAPS`. Daily BID and ASK coverage is a separate gate.

## Futures rows in ACQUISITION_REPORT.json

`WTI` and `NATGAS` `contract_venue: FAIL` / `Not connected` in that file is
the socket drop after Brent error `10372` (the qualified contract echoed
`lastTradeDateOrContractMonth` as a timestamp IB then rejected). It is not a
missing-contract result. Superseded by `ADDENDUM_FUTURES_RETRY.json` and
`ADDENDUM_CONTFUT_6Y.json`, which use conId + exchange only.

`CONTFUT` daily `TRADES` with duration `6 Y` (empty end time; IB error `10339`
forbids an end time) returned:

| asset | bars | first | last | holes > 5 calendar days |
|---|---|---|---|---|
| BRENT COIL IPE | 1549 | 2020-10-01 | 2026-09-30 | 0 |
| WTI CL NYMEX | 1526 | 2020-10-01 | 2026-09-30 | 0 |
| NATGAS NG NYMEX | 1526 | 2020-10-01 | 2026-09-30 | 0 |

CL and NG still show the front outright conId on the CONTFUT details row.
The 2020 start is earlier than that outright's life, so the history behaves
as a continuous series. The roll adjustment rule is still absent.

Delayed streaming snapshot (`reqMarketDataType(3)`, 8s, not a snapshot flag):

- COIL: `marketDataType=3`, bid 103.11, ask 103.16.
- CL: error `10168` (delayed not enabled); bid/ask not positive.
- NG: error `354` plus `10167`, then a later 8s read with `marketDataType=3`
  and no positive bid/ask.
