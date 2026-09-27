# FETCH_LOG — I001 corpus build (Lane P2, 2026-09-27)

- Authority: base round under FREEZE_R1_ADDENDUM_constants.md (30-fetch cap) **+ supplementary
  round under FREEZE_R1_ADDENDUM_r2_supplementary.md** (≤20 more; total budget 50).
- Budget: **37 fetches used / 50 total** (30 base + 7 supplementary; supplementary round stopped
  at floor attainment — 13 supplementary slots unused).
- Counting rule (declared before corpus build, conservative): every URL-retrieving tool call
  counts — WebFetch, web_reader (mcp webReader), and `curl` alike. Tool mix over both rounds:
  5 WebFetch, 7 web_reader, 25 curl. WebSearch (discovery only; no page content used for any
  geometry or date) is NOT counted as a fetch and is listed at the end for audit transparency.
- retrieved_timestamp for all entries: 2026-09-27.
- No price panel was loaded at any time (FREEZE no-panel rule); all geometry was codified from
  fetched TEXT only. No outcome, sealed, or holdout content was sought.

## ROUND 1 (base) — fetches #1–#30

| # | tool | URL | date-fetched | date-verified-from | result | feeds |
|---|------|-----|--------------|--------------------|--------|-------|
| 1 | WebFetch | bybit.com/en/learn/strategies/breakout-trading-strategy-trading-breakouts | 2026-09-27 | — | TIMEOUT 60s | (recovered by #13) |
| 2 | WebFetch | youtube.com/watch?v=jUTKg5SiSZ0 | 2026-09-27 | — | empty JS shell | (recovered by #6, #15) |
| 3 | WebFetch | academy.binance.com/en/articles/a-beginners-guide-to-day-trading-cryptocurrency | 2026-09-27 | — | 301 redirect only | (recovered by #9, #21) |
| 4 | WebFetch | old.reddit.com/r/Daytrading/comments/1lgk0cp/ (15-min ORB thread) | 2026-09-27 | — | login wall | REJECTED-class R03 |
| 5 | WebFetch | binance.com/en/academy/articles/a-beginners-guide-to-day-trading-cryptocurrency | 2026-09-27 | — | empty (bot challenge) | (recovered by #21) |
| 6 | web_reader | youtube.com/watch?v=jUTKg5SiSZ0 | 2026-09-27 | yt uploadDate metadata | OK: channel + uploadDate 2023-05-28 | E09, U02 |
| 7 | web_reader | old.reddit.com/r/Daytrading/comments/1lgk0cp/ | 2026-09-27 | — | login wall | REJECTED-class R03 |
| 8 | web_reader | bybit.com breakout article | 2026-09-27 | byline "Bybit Learn Dec 19, 2023" | OK | U01 (UNCODIFIABLE: no target/exit) |
| 9 | web_reader | binance.com academy day-trading guide | 2026-09-27 | publishedTime 2020-07-01T02:05:40.000Z | OK | E10 |
| 10 | curl | phemex.com/academy/what-is-range-trading-strategy-crypto (URL guess) | 2026-09-27 | — | 200 but Academy hub page | (recovered by #11) |
| 11 | curl | phemex.com/academy/range-trading-strategy-crypto | 2026-09-27 | JSON-LD datePublished 2025-05-21T03:32:06.954Z | OK | E01 |
| 12 | curl | kraken.com/learn/day-trading-strategies | 2026-09-27 | JSON-LD datePublished 2025-11-04T00:00:00.000Z | OK | E02, E03, E04, E05, E06 (K-cap selection; overflow → R06) |
| 13 | curl | bybit.com breakout article | 2026-09-27 | byline Dec 19, 2023 | OK | U01 |
| 14 | curl | binance.com academy day-trading guide | 2026-09-27 | — | HTTP 202, 0 bytes (bot) | (recovered by #21) |
| 15 | curl | youtube.com/watch?v=jUTKg5SiSZ0 | 2026-09-27 | ytInitialPlayerResponse uploadDate 2023-05-28T10:54:53-07:00 | OK incl. full description | E09, U02 |
| 16 | curl | litefinance.org/blog/for-beginners/how-to-trade-crypto/crypto-day-trading-strategies/ | 2026-09-27 | page ISO metadata 2026-06-25 (3 occurrences) | OK | E07, E08, U04, U05, U06 |
| 17 | curl | reddit.com/r/algotrading/comments/1r5al3o/.json | 2026-09-27 | — | 403 | REJECTED-class R03 |
| 18 | curl | docs.google.com/presentation/d/18oepESb03nHF3NB2IrW01gZDNxLHCtuGEfcOls523_w/export/txt (DO-strategy slides; linked from the dated 2023-05-28 video's own description) | 2026-09-27 | date carried by dated parent source #15 | OK: full slide text | E09, U02 geometry |
| 19 | curl | medium.com/@cryptocreddy/technical-analysis-series-directional-bias-e5516b08f7d1 | 2026-09-27 | — | 403 | REJECTED-class R05 |
| 20 | curl | old.reddit.com/r/algotrading/comments/1r5al3o/ | 2026-09-27 | — | HTTP 200 but login-wall page | REJECTED-class R03 (Reddit abandoned after 4 attempts across 3 tools) |
| 21 | web_reader | binance.com academy day-trading guide (text mode) | 2026-09-27 | publishedTime 2020-07-01T02:05:40.000Z | OK: full text incl. range-trading rules | E10 |
| 22 | curl | tradingview.com/ideas/solusdt/ | 2026-09-27 | — | 200; zero idea links in HTML (JS-rendered) | REJECTED-class R04 |
| 23 | curl | kucoin.com/blog/day-trading-crypto | 2026-09-27 | JSON-LD datePublished 2026-03-19T06:57:02.000Z | OK | U07 (UNCODIFIABLE: no per-setup stop/exit) |
| 24 | curl | crypto.com/us/crypto/learn/stop-loss-and-take-profit-levels-crypto | 2026-09-27 | — | 200; NO date field anywhere in page | REJECTED R01: DATE_UNVERIFIED (§1.1-2) |
| 25 | curl | phemex.com/blogs/bitcoin-price-analysis-today-btc-break-75k-april-15 | 2026-09-27 | JSON-LD datePublished 2026-04-15T04:02:55.880Z | OK | U09 (UNCODIFIABLE: no stop) |
| 26 | curl | youtube.com/watch?v=7mnz-JxhHnk (CryptoCred Entry Triggers video) | 2026-09-27 | uploadDate 2022-11-16T07:33:42-08:00 | OK incl. description | U03 |
| 27 | web_reader | binance.com/en/square/post/21953893926002 | 2026-09-27 | — | OK text; NO date visible in fetched page | REJECTED R02: DATE_UNVERIFIED (search snippet said 2025-03-21, not verifiable from fetched content) |
| 28 | curl | binance.com/en/square/post/21953893926002 (JSON-LD retry) | 2026-09-27 | — | HTTP 202, 0 bytes (bot) | REJECTED R02 final |
| 29 | curl | kucoin.com/learn/crypto-futures-trading/top-strategies-for-crypto-futures-trading | 2026-09-27 | JSON-LD datePublished 2025-03-07T09:07:30.000Z (dateModified 2025-10-14) | OK | U08 (UNCODIFIABLE: no stop placement) |
| 30 | curl | docs.google.com/presentation/d/1tLtcJkvsxs-2RSJa9_IAAvpfspkVJS39CwFCWk0tT5A/export/txt (entry-triggers slides; linked from dated 2022-11-16 video description) | 2026-09-27 | date carried by dated parent source #26 | OK: full slide text; entry-mechanics definitions only, no per-setup stop/target | U03 detail (stays UNCODIFIABLE) |

## ROUND 2 (supplementary, addendum r2) — fetches #31–#37

| # | tool | URL | date-fetched | date-verified-from | result | feeds |
|---|------|-----|--------------|--------------------|--------|-------|
| 31 | curl | okx.com/learn/day-trading-strategies-trader-investment-profit | 2026-09-27 | JSON-LD datePublished 2025-10-03T22:31:16.321Z (byline Oct 04, 2025) | OK: strategies are one-line summaries | U10 (UNCODIFIABLE: no per-setup entry/stop/exit) |
| 32 | curl | coinmarketcap.com/academy/article/what-is-scalping-in-crypto | 2026-09-27 | JSON-LD datePublished 2021-10-26T09:34:42.000Z | OK: conceptual only, zero geometry terms | U11 (UNCODIFIABLE) |
| 33 | curl | bybit.com/en/learn/strategies (hub, for article links) | 2026-09-27 | — | 200; JS-rendered, zero article links in HTML | none (hub abandoned; per-article search used instead) |
| 34 | curl | phemex.com/academy/how-to-use-twiggs-money-flow-bitcoin-trading | 2026-09-27 | JSON-LD datePublished 2025-05-16T02:28:44.974Z | OK: full worked example with entry/stop/target | **E11 ADMISSIBLE** |
| 35 | curl | altrady.com/blog/crypto-trading-strategies/take-profit-and-stop-loss | 2026-09-27 | byline "Published on: May 02, 2025" + JSON-LD | OK: order-placement guide | U12 (UNCODIFIABLE: no named setup) |
| 36 | web_reader | binance.com/en/academy/articles/a-beginners-guide-to-classical-chart-patterns | 2026-09-27 | page metadata publishedTime 2020-04-08 | OK: pattern taxonomy + confirmation discussion | U13 (UNCODIFIABLE: no per-setup stop/target) |
| 37 | curl | bybit.com/en/learn/candlestick/head-and-shoulders-pattern-what-is-it-how-to-trade-with-it | 2026-09-27 | JSON-LD datePublished 2021-01-26T07:11:59.000Z (byline Jan 25, 2021) | OK: complete closed-bar geometry (neckline-close entry, head stop, measured-move target) | **E12 ADMISSIBLE** |

Supplementary-round rejected-class notes (none of these consumed a fetch beyond #31–#37):
- Gate web3 "Three Falling Peaks" article (dated 2025-12-04, explicit stop placement per snippet):
  English deep link unresolvable via search (only zh/zh-TW paths exposed) — dropped without a
  fetch (budget conservation after floor attainment).
- Bybit "double top/bottom" article URL known but not fetched (floor already met; Bybit has K-cap
  headroom; left for any future round).
- OKX "Chainlink Resistance and Support Levels" (Nov 8, 2025) market-analysis piece: not fetched
  (same class as U09 — likely missing stop; floor already met).

Content yield round 2: 6 full-content fetches, 1 JS-empty hub.

Content yield: 16 calls returned full usable page content; 5 returned date-or-partial content;
9 failed/blocked/empty/wrong-page. Every content-bearing page is accounted for in the manifest
(E01–E10 admissible; U01–U09 uncodifiable-retained) or in the rejected log below.

## Rejected / excluded log (never entered the manifest as entries)

| item | source (fetch #) | reason |
|------|------------------|--------|
| R01 | crypto.com "Stop-Loss and Take-Profit Levels" (#24) | **DATE_UNVERIFIED** — no platform date in fetched page (protocol §1.1-2) |
| R02 | Binance Square "Guide to Starting Crypto Day Trading in 2025" (#27, #28) | **DATE_UNVERIFIED** — page shows no date; JSON-LD retry bot-blocked (HTTP 202) |
| R03 | r/Daytrading 1lgk0cp 15-min ORB thread (#4, #7); r/algotrading 1r5al3o (#17, #20) | **FETCH_BLOCKED** — Reddit login wall on all attempts; no post content ever obtained |
| R04 | TradingView SOLUSDT published-idea pages (#22; no per-idea fetch attempted after JS-wall confirmed) | **FETCH_EMPTY** — idea content JS-rendered, not obtainable; TradingView author class yields zero entries |
| R05 | Medium @cryptocreddy directional-bias + trading-plan articles (#19) | **FETCH_BLOCKED** (403) |
| R06 | Kraken page overflow examples: momentum BTC (no initial stop stated), range ETH (2nd range setup, same author), scalping LTC (order-book trigger), order-flow LINK (order-book trigger), pairs BTC/ETH long-short (no stop stated) | **AUTHOR_CAP_EXCEEDED** — Kraken Learn already holds K=5 entries (E02–E06); overflow dropped before manifest per protocol §1.1-5 |
| R07 | Bybit Learn (1 of 5 K-slots used), KuCoin (2 of 5), Phemex (2 of 5), CryptoCred (3 of 5) | cap headroom unused — fetch budget exhausted before further sources could be verified |

## EX_POST_RECAP encounters

**None.** All fetched content was either a pre-entry strategy description, a pre-entry published
level-idea (U09), or an illustrative walkthrough inside a dated educational guide (the Kraken /
LiteFinance examples narrate hypothetical trades to teach a rule; their fictional P&L numbers are
recorded only as ILLUSTRATIVE_CLAIMS in the manifest claims fields and were never used as
evidence). No author trade recap, P&L screenshot, or "how I caught this trade" narrative was
encountered, so no EX_POST_RECAP rejection code was triggered.

## Discovery searches (WebSearch — not counted as fetches; zero geometry or dates taken from search snippets)

1. CryptoCred "daily open" lesson (video ID)
2. site:tradingview.com SOLUSDT ideas (weak URLs; class later found JS-inaccessible)
3. Bybit/OKX/Phemex breakout-strategy articles
4. reddit algotrading scalping threads (2 thread URLs; later blocked)
5. phemex academy range-trading exact URL
6. cointelegraph day-trading guide (not found; Kraken/LiteFinance surfaced instead)
7. crypto day-trading guides with entry/stop/TP (Kraken "10 strategies", IG, LiteFinance surfaced)
8. KuCoin/Bitget/gate.io learn day-trading (KuCoin blog + learn URLs, crypto.com surfaced)
9. CMC Alexandria day-trading article (not found)
10. IG deep link (unresolved; class dropped without spending a fetch)
11. Binance Square day-trading 2025 URL (surfaced; later rejected DATE_UNVERIFIED)

## Floor assessment (FREEZE_R1_ADDENDUM_constants.md + FREEZE_R1_ADDENDUM_r2_supplementary.md)

| metric | required | round 1 | final (after round 2) |
|--------|----------|---------|----------------------|
| admissible entries | ≥12 | 10 (E01–E10) | **12** (E01–E12) |
| distinct authors/channels | ≥5 | 5 | **6** (Phemex Academy, Kraken Learn, LiteFinance Blog, CryptoCred, Binance Academy, Bybit Learn) |
| web fetches | ≤50 (30+20) | 30 | **37** (30 + 7 supplementary; 13 supplementary slots unused) |

- **FLOOR MET.** The two remaining slots were closed by the supplementary round: E11 (Phemex
  Twiggs, 2025-05-16) and E12 (Bybit head-and-shoulders, 2021-01-26). Ranking is now LAWFUL per
  protocol §1.5; the ranked top-N is in RULE_CANDIDATES.md.
- Round-1 shortfall diagnosis (recorded for audit): the gap was structural (Reddit login wall,
  TradingView JS wall, Binance Square date-unverifiable), not search breadth. The addendum-r2
  round closed it with example-based exchange-education articles on curl-accessible domains
  (Phemex Academy, Bybit Learn) plus four new dated UNCODIFIABLE entries (OKX, CMC, Altrady,
  Binance patterns) that document the source landscape without feeding codification.

**Chưa có PnL nào được xem hoặc tính toán cho identity này.**
