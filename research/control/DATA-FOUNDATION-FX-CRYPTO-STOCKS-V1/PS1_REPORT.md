# PS1 probe report — Binance keyless availability (executed 2026-09-26)

11 requests / ~1.2 MB / 0 credentials (ledger: probe_ledger.json; raw:
~/.my-quantitative-data/data-foundation-v1/ps1/ with requests.log +
responses.log + fetched objects).

## Findings
1. `fapi/v1/premiumIndex` is **current-only** (startTime/endTime ignored —
   identical body with and without). No REST forecast-funding history.
2. `fapi/v1/fundingRate` serves settled history with per-settlement
   markPrice + rateType (re-confirmed live).
3. **data.binance.vision serves `premiumIndexKlines` monthly zips** (S3
   listing: aggTrades, bookTicker, fundingRate, indexPriceKlines, klines,
   markPriceKlines, premiumIndexKlines, trades). HTML host ignores
   list-type=2 — use `s3-ap-northeast-1.amazonaws.com/data.binance.vision`.
4. Channel validated end-to-end: BTCUSDT 1h 2026-07 zip sha256
   `448beab06b0f7268d39520e71fea0420cf15d67cb3415cf53efaa28e106f8443`
   == vendor `.CHECKSUM`; 745 hourly rows of premium-index OHLC
   (price-fraction units). Scale: ~16 KB/month/symbol ⇒ ~7 MB for 6
   symbols × 6 years.

## Gap-matrix consequence
**N8 (settled vs forecast funding) resolves to AVAILABLE_KEYLESS** —
forecast component reconstructable from premiumIndexKlines (reconstruction
formula: premium → funding forecast per venue rules incl. interest-rate
floor and clamp; to be pinned in the follow-up staging cycle with the
settled-rate tolerance check as the falsifying control, per the frozen
control in DATA_GAP_MATRIX N8). Mark/index klines also available in the
same family listing (cross-check leg for CHR3F-class work).
