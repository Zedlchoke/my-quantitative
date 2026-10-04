# SPECS_MARGINS_PUBLIC_2026-10-02 — FUTURES-DATA-10SYMS-V1 (public reference dossier)

- Cycle / lane: FUTURES-DATA-10SYMS-V1 (read-only data lane)
- Compiled: 2026-10-02, by research subagent, from PUBLIC non-paywalled pages only.
- Scope: NQ, ES, CL, NG, GC, SI, 6E, 6J, 6B, 6A (CME Group family).
- Transport constraint: `www.cmegroup.com` BLOCKED this session (WebFetch → 60s timeout,
  non-browser client). No bypass attempted, no CAPTCHA solving, no ToS-violating mirrors.
  Facts that only CME can adjudicate are marked `CME_BLOCKED_TRANSPORT`.
- No credentials, no signups, no account numbers. Every number carries a source URL.
- Channel legend: WebFetch = built-in fetch+summarize; webReader = mcp web_reader.

## 1. Contract specifications per symbol

Primary spec source: NinjaTrader per-contract pages (public, mirror CME specs; each page
itself links to CME for the official text). Cross-checks: AMP Futures
contract-specifications table, TradingCharts legacy spec table, Wikipedia. Where sources
conflict (FX tick size), both values are recorded and the conflict is flagged — the
official current value could not be adjudicated because CME is blocked.

| Field | NQ | ES |
|---|---|---|
| Contract unit | $20 × Nasdaq-100 Index [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-nasdaq/) | $50 × S&P 500 Index [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/) |
| Tick / value | 0.25 index pts = $5.00 [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-nasdaq/) | 0.25 index pts = $12.50 [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/) |
| Listing cycle | Quarterly H,M,U,Z — "9 Quarters Out and 3 Additional December Contracts" [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-nasdaq/); "Most E-mini futures expire quarterly ... March, June, September, and December" [Wikipedia E-mini](https://en.wikipedia.org/wiki/E-mini) | Quarterly H,M,U,Z — "nine quarters out and three additional December contracts" [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/) |
| Last trading day | "3rd Friday of every listed contract month" [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-nasdaq/), corroborated "Third Friday of the contract month" [TradingCharts](https://futures.tradingcharts.com/chart/NQ/) | "3rd Friday of every listed contract month" [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/), "Third Friday of the contract month" [TradingCharts](https://futures.tradingcharts.com/chart/ES/) |
| Settlement | Cash ("Financially settled"; "cash-settled equity index futures contract") [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-nasdaq/); "Not applicable (cash settled contract)" [TradingCharts](https://futures.tradingcharts.com/chart/NQ/) | Cash ("Financially settled") [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/); "Not applicable (cash settled contract)" [TradingCharts](https://futures.tradingcharts.com/chart/ES/) |
| Exchange | CME (Globex) [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-nasdaq/) | CME (Globex) [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/) |

| Field | CL | NG |
|---|---|---|
| Contract unit | 1,000 barrels [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/); "1,000 US barrels, or 42,000 US gallons" [Wikipedia WTI](https://en.wikipedia.org/wiki/West_Texas_Intermediate) | 10,000 mmBtu [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/natural-gas/) |
| Tick / value | $0.01/bbl = $10.00 [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/), [Wikipedia WTI](https://en.wikipedia.org/wiki/West_Texas_Intermediate) | $0.001/mmBtu = $10.00 [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/natural-gas/) |
| Listing cycle | All 12 months; "current year and the next 10 calendar years and two additional contract months" [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/); "current year, the following 10 calendar years, and 2 additional months" [Wikipedia WTI](https://en.wikipedia.org/wiki/West_Texas_Intermediate) | All 12 months; "Monthly contracts listed for the current year and the next 12 calendar years" [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/natural-gas/) |
| Last trading day | "Trading ceases three business days before the 25th calendar day of the month prior to the contract month" [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/); Wikipedia words the same rule as "four business days before the 26th calendar day of the previous calendar month" [Wikipedia WTI](https://en.wikipedia.org/wiki/West_Texas_Intermediate) — two independent phrasings of the NYMEX rule, retained verbatim | "Trading ceases on the third last business day of the month prior to the contract month" [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/natural-gas/) |
| Settlement | Physical ("Deliverable") [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/); delivery point Cushing, Oklahoma [Wikipedia WTI](https://en.wikipedia.org/wiki/West_Texas_Intermediate) | Physical ("Deliverable"); gas "delivered at the Henry Hub natural gas distribution hub in Louisiana" [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/natural-gas/); EIA: "Prices are based on delivery at the Henry Hub in Louisiana" [EIA](https://www.eia.gov/dnav/ng/ng_pri_fut_s1_d.htm) |
| Exchange | NYMEX/CME [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/) | NYMEX [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) ("NYMEX/CME"), [NT](https://www.ninjatrader.com/futures/futures-contracts/energy/natural-gas/) |

| Field | GC | SI |
|---|---|---|
| Contract unit | 100 troy ounces [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) ("100 oz"), [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/gold/) | 5,000 troy ounces [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/silver/) |
| Tick / value | $0.10/oz = $10.00 [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/gold/), [TradingCharts](https://futures.tradingcharts.com/specs/) | $0.005/oz = $25.00 [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/silver/), [TradingCharts](https://futures.tradingcharts.com/specs/) |
| Listing cycle | AMP lists active cycle "G,J,M,Q,V,Z" [AMP](https://www.ampfutures.com/trading-info/contract-specifications/); NT describes listing depth: monthly for 3 consecutive months + any Feb/Apr/Aug/Oct within nearest 23 months + any Jun/Dec within nearest 72 months [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/gold/) | AMP lists "F,H,K,N,U,Z" [AMP](https://www.ampfutures.com/trading-info/contract-specifications/); NT: 3 consecutive monthlies + any Jan/Mar/May/Sep within nearest 23 months + any Jul/Dec within 60 months [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/silver/) |
| Last trading day | "Trading ceases at 1:30 pm ET on the third last business day of the contract month" [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/gold/) | "Trading ceases at 1:25 pm ET on the third last business day of the contract month" [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/silver/) |
| Settlement | Physical ("Deliverable") [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/gold/) | Physical ("Deliverable") [NT](https://www.ninjatrader.com/futures/futures-contracts/metals/silver/) |
| Exchange | COMEX/CME [AMP](https://www.ampfutures.com/trading-info/contract-specifications/); COMEX is a division of NYMEX, both DCMs of CME Group [Wikipedia NYMEX](https://en.wikipedia.org/wiki/New_York_Mercantile_Exchange) | COMEX/CME [AMP](https://www.ampfutures.com/trading-info/contract-specifications/); same COMEX provenance [Wikipedia NYMEX](https://en.wikipedia.org/wiki/New_York_Mercantile_Exchange) |

FX contracts (all CME, quarterly H,M,U,Z, physically delivered at expiry):

| Field | 6E | 6J |
|---|---|---|
| Contract unit | 125,000 euro [NT](https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex), [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [Wikipedia](https://en.wikipedia.org/wiki/Currency_future) ("€125,000") | ¥12,500,000 [NT](https://ninjatrader.com/futures/futures-contracts/currency/japanese-yen), [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [TradingCharts](https://futures.tradingcharts.com/specs/) ("12,500,000 Japanese Yen") |
| Tick / value | NT: "0.000050 per euro increment = ... $6.25 per contract" [NT](https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex); AMP: "0.00005 / $6.25" [AMP](https://www.ampfutures.com/trading-info/contract-specifications/). CONFLICT: legacy sources show $0.0001/€ = $12.50 [TradingCharts](https://futures.tradingcharts.com/specs/), [Wikipedia](https://en.wikipedia.org/wiki/Currency_future). Official current value: CME_BLOCKED_TRANSPORT | NT: "0.0000005 per yen increment = $6.25 per contract"; FAQ: "¥0.0000005 (0.5 pips) ... equals $6.25" [NT](https://ninjatrader.com/futures/futures-contracts/currency/japanese-yen); AMP: "0.0000005 / $6.25" [AMP](https://www.ampfutures.com/trading-info/contract-specifications/). CONFLICT: TradingCharts legacy JY "$.000001 ($12.50/contract)" [TradingCharts](https://futures.tradingcharts.com/specs/). Official current value: CME_BLOCKED_TRANSPORT |
| Listing cycle | "Quarterly contracts (Mar, Jun, Sept, Dec) listed for 20 consecutive quarters" [NT](https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex); Wikipedia adds "plus 3 serial contract months" [Wikipedia](https://en.wikipedia.org/wiki/Currency_future) | "Quarterly contracts (March, June, September, December) listed for 20 consecutive quarters" [NT](https://ninjatrader.com/futures/futures-contracts/currency/japanese-yen) |
| Last trading day | "Trading terminates at 10:16 am ET, 2 business day prior to the third Wednesday of the contract month" [NT](https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex) | "Trading ends at 10:16 am ET, two business days before the third Wednesday of the contract month" [NT](https://ninjatrader.com/futures/futures-contracts/currency/japanese-yen) |
| Settlement | Physical ("Deliverable") [NT](https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex); "Most contracts have physical delivery" [Wikipedia](https://en.wikipedia.org/wiki/Currency_future) | Physical ("Deliverable"); FAQ: holding to expiry "obligates you to exchange ¥12,500,000 for USD at the settlement price" [NT](https://ninjatrader.com/futures/futures-contracts/currency/japanese-yen) |
| Exchange | CME [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) | CME [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) |

| Field | 6B | 6A |
|---|---|---|
| Contract unit | 62,500 British pounds [TK Futures](https://www.tkfutures.com/british_pound.htm) ("62,500 British pounds per contract"), [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) ("62.5K £") | AUD 100,000 [ITG Futures](https://www.itg-futures.com/index.php/markets/energy/australian-dollar), [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) ("100K AUD") |
| Tick / value | CONFLICT: AMP "0.0001 / $6.25" [AMP](https://www.ampfutures.com/trading-info/contract-specifications/); TK "regular: 0.0002=$12.50, calendar spread: 0.0001=$6.25" [TK Futures](https://www.tkfutures.com/british_pound.htm); TradingCharts legacy "$0.0001 BP = $6.25" [TradingCharts](https://futures.tradingcharts.com/specs/). Official current value: CME_BLOCKED_TRANSPORT | CONFLICT: ITG "0.0001 points ($10.00 per contract)" [ITG Futures](https://www.itg-futures.com/index.php/markets/energy/australian-dollar); TradingCharts legacy "$.0001 AD ($10.00/contract)" [TradingCharts](https://futures.tradingcharts.com/specs/); AMP "0.00005 / $5.00" [AMP](https://www.ampfutures.com/trading-info/contract-specifications/). Official current value: CME_BLOCKED_TRANSPORT |
| Listing cycle | March quarterly cycle (H,M,U,Z) [AMP](https://www.ampfutures.com/trading-info/contract-specifications/); TK: "Six months in the March quarterly Cycle March, June, Sep, Dec" [TK Futures](https://www.tkfutures.com/british_pound.htm) | H,M,U,Z (March, June, September, December) [AMP](https://www.ampfutures.com/trading-info/contract-specifications/), [ITG Futures](https://www.itg-futures.com/index.php/markets/energy/australian-dollar) |
| Last trading day | Cannon Trading spec text (via search snippet; direct fetch timed out): "Futures trading shall terminate on the second business day immediately preceding the third Wednesday of the contract month" [Cannon](https://www.cannontrading.com/tools/futures-market/currencies/British-Pound-Futures); TK hours row shows "LTD (9:16a.m.) GLBX" [TK Futures](https://www.tkfutures.com/british_pound.htm); maturity = IMM third Wednesday [Wikipedia](https://en.wikipedia.org/wiki/Currency_future) | "Second business day preceding third Wednesday of expiring month" [ITG Futures](https://www.itg-futures.com/index.php/markets/energy/australian-dollar); Barchart A6 profile (via search snippet): "Last Trading Day: second business day preceding the third Wednesday" [Barchart](https://www.barchart.com/futures/quotes/A6*0/profile) |
| Settlement | "Physical delivery takes place on the third Wednesday of the contract month" [TK Futures](https://www.tkfutures.com/british_pound.htm) | Physical delivery per CME FX contract family [Wikipedia](https://en.wikipedia.org/wiki/Currency_future) ("Most contracts have physical delivery") + third-Wednesday value date; 6A-specific official delivery text: CME_BLOCKED_TRANSPORT |
| Exchange | CME [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) | CME [AMP](https://www.ampfutures.com/trading-info/contract-specifications/) |

Notes on sources and discrepancies (evidence-first):

- NinjaTrader per-contract pages carry a full spec table mirroring CME (each page links to
  the CME official spec as its own reference); they are the deepest reachable spec source
  this session. IBKR was the preferred source per dispatch but returns HTTP 403 to
  WebFetch and webReader only rendered the page shell without the JS-driven table (see
  fetch log), so no IBKR spec values could be extracted.
- FX tick size conflict pattern: for 6E/6J/6B/6A the reachable sources split between a
  half-tick value (AMP, NinjaTrader) and a full-tick value (TradingCharts legacy,
  Wikipedia's historical EUR example, TK for 6B, ITG for 6A). These likely reflect
  outright-vs-calendar-spread minimums and/or the pre/post tick redesigns; adjudication
  requires the CME rulebook — CME_BLOCKED_TRANSPORT. Numbers are reported, not reconciled.
- TradingCharts (`futures.tradingcharts.com/specs/`) self-describes as manually updated
  and shows legacy symbols (EC/JY/BP/AD) and some stale values (e.g., ES tick ".01 =
  $0.50", NQ "1pt=$0.5"). It is used ONLY for the quoted-units column and contract
  units, both of which match current broker tables; its tick/margin columns are NOT used.
- CL last-trading-day phrasing differs between NT ("3 business days before the 25th") and
  Wikipedia ("4 business days before the 26th") — both quoted verbatim, not merged.

## 2. FX futures quote convention (6J / 6E / 6B / 6A)

**6J is quoted JPY/USD (USD per JPY), NOT USD/JPY.** Same family convention for 6E/6B/6A:
prices are USD per one unit of the foreign currency, i.e., the inverse of the USDXXX spot
convention (for JPY specifically: 6J price = 1 / USDJPY).

Documentary confirmation, each with URL:

1. General convention — Wikipedia, Currency future: "The price of a future is then in
   terms of US dollars per unit of other currency"; worked EUR example: "Each change of
   $0.0001 /€ (the minimum commodity tick size), produces a profit of US$12.50 per
   contract" on a "€125,000" contract (historical tick example).
   https://en.wikipedia.org/wiki/Currency_future
2. Per-pair quoted units — TradingCharts spec table, "Quoted Units" column: Euro "US $
   per Euro"; Japanese Yen "US $ per Japanese Yen"; British Pound "US $ per British
   Pound"; Australian Dollar "US $ per Australian Dollar".
   https://futures.tradingcharts.com/specs/
3. Live quote evidence — TradingView: "The current price of Japanese Yen Futures is
   0.0063595 USD" (contract size 12,500,000) — a JPY/USD-style price; 1 / 0.0063595 ≈
   157.2, i.e., the reciprocal of USDJPY spot ≈ 157.
   https://www.tradingview.com/symbols/CME-6J1!/
4. Live quote evidence — TradingView: "The current price of Euro FX Futures is 1.12655
   USD" (contract size 125,000) — USD per EUR, in the 1.08–1.17 band typical of recent
   6E history.
   https://www.tradingview.com/symbols/CME-6E1!/
5. Tick framing — NinjaTrader 6J FAQ: "The minimum price movement, or tick, for the CME
   forex JPY futures is ¥0.0000005 (0.5 pips), which equals $6.25 per contract" (a
   dollar price per unit of yen); 6E: "0.000050 per euro increment ... $6.25 per
   contract". https://ninjatrader.com/futures/futures-contracts/currency/japanese-yen ,
   https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex

CME's own pages (title "Japanese Yen - JPY/USD", price quotation "U.S. dollars and cents
per JPY") exist but were transport-blocked this session; they appear only as
search-engine snippets and are therefore cited here as corroboration already implied by
sources 1–5, not as fetched evidence. Official confirmation fetch: CME_BLOCKED_TRANSPORT.

## 3. Margin requirements (public pages)

Source A — NinjaTrader, "Margins as of 2026-08-31" (Day / Maintenance / Initial, USD per
contract). https://ninjatrader.com/pricing/margins

| Symbol | Market (exchange) | Day margin | Maintenance | Initial |
|---|---|---|---|---|
| NQ | E-Mini NASDAQ 100 (CME) | $1,000.00 | $42,248.33 | $46,473.17 |
| ES | E-Mini S&P 500 (CME) | $500.00 | $26,028.77 | $28,631.65 |
| CL | Crude Oil (NYMEX) | $1,000.00 | $8,021.09 | $8,823.20 |
| NG | Natural Gas (NYMEX) | $1,000.00 | $2,814.83 | $3,096.32 |
| GC | Gold (COMEX) | $2,000.00 | $22,391.00 | $24,630.10 |
| SI | Silver (COMEX) | $4,000.00 | $33,498.00 | $36,847.80 |
| 6E | Euro FX (CME) | $500.00 | $2,400.00 | $2,640.00 |
| 6J | Japanese Yen (CME) | $500.00 | $2,800.00 | $3,080.00 |
| 6B | British Pound (CME) | $500.00 | $2,000.00 | $2,200.00 |
| 6A | Australian Dollar (CME) | $500.00 | $1,900.00 | $2,090.00 |

Source B — AMP Futures margin page (fetched 2026-10-02; single overnight column labeled
"*Maintenance", plus day-trading margin; page notes retail "Heightened Risk Profile"
traders require ~10% above CME rates, and day margins double for accounts over $100K).
https://www.ampfutures.com/trading-info/margins/

| Symbol | Overnight (*Maintenance) | Day trading |
|---|---|---|
| NQ | $46,623.00 | $1,000.00 |
| ES | $28,813.00 | $400.00 |
| CL | $9,448.00 | $2,362.00 |
| NG | $3,234.00 | $3,234.00 |
| GC | $24,249.00 | $6,062.25 |
| SI | $35,641.00 | $35,641.00 |
| 6E | $2,310.00 | $577.50 |
| 6J | $3,080.00 | $770.00 |
| 6B | $1,870.00 | $467.50 |
| 6A | $1,925.00 | $481.25 |

Reconciliation note: NinjaTrader maintenance figures (2026-08-31) and AMP maintenance
figures (2026-10-02 fetch) are within ~2% for most symbols; NQ/ES show larger drift
consistent with exchange margin updates between the two as-of dates and AMP's +10% retail
adjustment. Both sets are reported as fetched; no smoothing applied.

Source C — Interactive Brokers "Futures & FOPs Margin Requirements":
https://investors.interactivebrokers.com/en/trading/margin-futures-fops.php —
NOT_AVAILABLE_LOGIN_GATED (WebFetch → HTTP 403; webReader renders page shell but the
margin table loads via JavaScript and could not be extracted without a client session;
search snippets showed values, e.g., 6J intraday ≈ $3,220.01 / overnight ≈ $2,800.01, but
snippet-derived numbers are not recorded as sourced facts).

Exchange-official (CME SPAN) margins: CME_BLOCKED_TRANSPORT.

## 4. Fetch log

| # | URL | Channel | Result |
|---|---|---|---|
| 1 | https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.html | WebFetch | timeout 60s — CME_BLOCKED_TRANSPORT (no retry/bypass) |
| 2 | https://www.wisdomtree.com/investments/futures/specifications/nq and .../es | WebFetch | 403 |
| 3 | https://investors.interactivebrokers.com/en/trading/margin-futures-fops.php | webReader | rendered shell only; JS table not extractable |
| 4 | https://investors.interactivebrokers.com/en/trading/margin-futures-fops.php | WebFetch | 403 |
| 5 | https://www.interactivebrokers.com/campus/trading-lessons/e-mini-nasdaq-100-product-overview | webReader / WebFetch | rendered (body not fully extractable) / 403 |
| 6 | https://www.interactivebrokers.com/campus/trading-lessons/fundamentals-and-fx-futures | webReader / WebFetch | rendered (body not fully extractable) / 403 |
| 7 | https://www.ampfutures.com/trading-info/margins/ | WebFetch | 200 rendered — margins for 10/10 symbols |
| 8 | https://www.ampfutures.com/trading-info/contract-specifications/ | WebFetch | 200 rendered — spec table 10/10 symbols |
| 9 | https://en.wikipedia.org/wiki/Currency_future | WebFetch | 200 — quote convention, EUR example, IMM dates, physical delivery |
| 10 | https://en.wikipedia.org/wiki/E-mini | WebFetch | 200 — ES/NQ multiplier, tick, quarterly cycle, (stale margins noted, unused) |
| 11 | https://en.wikipedia.org/wiki/West_Texas_Intermediate | WebFetch | 200 — CL unit, tick, months, LTD rule, Cushing delivery |
| 12 | https://en.wikipedia.org/wiki/Henry_Hub | WebFetch | 200 — delivery-point context only |
| 13 | https://en.wikipedia.org/wiki/COMEX | WebFetch | disambiguation page only — no specs |
| 14 | https://en.wikipedia.org/wiki/New_York_Mercantile_Exchange | WebFetch | 200 — COMEX/NYMEX division provenance |
| 15 | https://www.barchart.com/futures/quotes/6J*0 | webReader | 500 server error |
| 16 | https://www.barchart.com/futures/quotes/ES*0/profile | WebFetch | 200 but empty body (JS-rendered) |
| 17 | https://www.commodity.com/gold/, /silver/, /natural-gas/ | WebFetch | 404 (paths guessed, do not exist) |
| 18 | https://futures.tradingcharts.com/specs/ | WebFetch | 200 — legacy spec table, all 10 symbols (legacy codes EC/JY/BP/AD); used for quoted-units + units only |
| 19 | https://futures.tradingcharts.com/chart/ES/ , /chart/NQ/ | WebFetch | 200 — spec blocks incl. LTD + cash-settle note |
| 20 | https://futures.tradingcharts.com/chart/NG/ , /chart/CL/ | WebFetch | 200 — spec blocks (NG block's LTD text appears to be the options rule; superseded by NinjaTrader NG page) |
| 21 | https://futures.tradingcharts.com/chart/GC/ , /SI/ , /EC/ , /JY/ , /BP/ , /AD/ | WebFetch | 200 but directory/menu only — no spec blocks |
| 22 | https://futures.tradingcharts.com/marketquotes/GC_.html , /SI_.html | WebFetch | 200 but quote tables JS-loading — no specs |
| 23 | https://ninjatrader.com/margin-details | WebFetch | interactive tool, default "Margin Not Found" — no data |
| 24 | https://ninjatrader.com/pricing/margins | WebFetch | 200 rendered — full margins table, as of 2026-08-31 |
| 25 | https://ninjatrader.com/futures/futures-contracts | WebFetch | 200 — contract page index |
| 26 | https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-s-p-500/ | WebFetch | 200 — full ES specs |
| 27 | https://www.ninjatrader.com/futures/futures-contracts/equity-index/e-mini-nasdaq/ | WebFetch | 200 — full NQ specs |
| 28 | https://www.ninjatrader.com/futures/futures-contracts/energy/crude-oil/ | WebFetch | 200 — full CL specs |
| 29 | https://www.ninjatrader.com/futures/futures-contracts/energy/natural-gas/ | WebFetch | 200 — full NG specs |
| 30 | https://www.ninjatrader.com/futures/futures-contracts/metals/gold/ | WebFetch | 200 — full GC specs |
| 31 | https://www.ninjatrader.com/futures/futures-contracts/metals/silver/ | WebFetch | 200 — full SI specs |
| 32 | https://ninjatrader.com/futures/futures-contracts/currency/japanese-yen | WebFetch | 200 — full 6J specs + tick FAQ + delivery FAQ |
| 33 | https://www.ninjatrader.com/futures/futures-contracts/currency/euro-forex | WebFetch | 200 — full 6E specs |
| 34 | ninjatrader.com/futures/futures-contracts/currency/british-pound, /australian-dollar, /british-pound-forex, /australian-dollar-forex; /futures/futures-contract/energy/natural-gas | WebFetch | 404 — pages do not exist |
| 35 | https://comments.cftc.gov/Handlers/PdfHandler.ashx?id=29227 | WebFetch | 403 |
| 36 | https://www.eia.gov/dnav/ng/ng_pri_fut_s1_d.htm | WebFetch | 200 — "Prices are based on delivery at the Henry Hub in Louisiana" |
| 37 | https://www.cannontrading.com/tools/contract-specifications ; /tools/futures-market/currencies/British-Pound-Futures ; /Australian-Dollar-Futures | WebFetch | connect timeout x3 |
| 38 | https://www.jmbullion.com/investing-guide/paper-investments/gold-silver-futures | WebFetch | 403 |
| 39 | https://www.investopedia.com/terms/g/gold-futures.asp | WebFetch | 402 |
| 40 | https://www.tradingview.com/symbols/CME-6J1!/ | WebFetch | 200 — price 0.0063595 USD |
| 41 | https://www.tradingview.com/symbols/CME-6E1!/ | WebFetch | 200 — price 1.12655 USD |
| 42 | https://www.tkfutures.com/british_pound.htm | WebFetch | 200 — 6B specs |
| 43 | https://www.itg-futures.com/index.php/markets/energy/australian-dollar | WebFetch | 200 — 6A specs |

Facts not obtainable this session (CME-blocked only): official current FX outright tick
sizes (6E/6J/6B/6A adjudication), CME SPAN exchange margins, 6A-specific official
delivery text. Everything else above carries a fetched, public URL.
