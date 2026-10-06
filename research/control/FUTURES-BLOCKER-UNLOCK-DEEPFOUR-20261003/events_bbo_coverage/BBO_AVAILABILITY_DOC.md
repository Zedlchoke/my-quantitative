# BBO / Depth Availability Documentation — Databento GLBX.MDP3 + CME MDP 3.0

Task FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003, lane A5-EVENTS-BBO-COVERAGE,
dimension 2. Generated 2026-10-03. **Documentation only: no purchase, no
account creation, no account-behavior claims.** This is a buy-decision INPUT
for the owner — not an acquisition. All fetch attempts in `fetch_log.jsonl`.

## 0. Governing law restated (D5, `es_schema_eval.md` §6)

> bbo-1m is NOT owned and, per Co-Owner, would be insufficient anyway.
> CAN support: tiering inputs for modeled cost.
> CANNOT support: execution realism — no fill probability, no queue position,
> no capacity, no "we would have gotten the mid/inside" claims.

Even if bbo-1m were purchased, it **cannot prove intrabar fill or queue
position**: it is a single-level best-bid/offer *sampled* snapshot schema, one
row per interval boundary, with no order-book event stream, no action/depth
semantics, and no trade-matching information. Every cost number in this repo
therefore remains **MODELED COST** regardless of any decision below. There is
no "measured cost" anywhere.

## 1. What schemas exist for GLBX.MDP3 (Databento)

FACT(source = `databento_dbn` SDK installed in the repo venv at
`.venv/lib/python3.12/site-packages/databento_dbn/`, read 2026-10-03 — the
vendor's own schema definitions, zero-fetch authoritative):

Full `Schema` enum: `mbo, mbp-1, mbp-10, tbbo, trades, ohlcv-1d, ohlcv-1h,
ohlcv-1m, ohlcv-1s, ohlcv-eod, bbo-1m, bbo-1s, cbbo-1m, cbbo-1s, cmbp-1,
definition, imbalance, statistics, status, tcbbo` (cbbo/cmbp/tcbbo are OPRA
equities options schemas, not GLBX).

Relevant to GLBX.MDP3 (CME futures), with `RType` record codes:

| schema | RType | shape (from SDK message definitions) |
|---|---|---|
| `mbo` | 160 | full market-by-order book maintenance stream (order add/modify/cancel) |
| `mbp-1` | 1 | market-by-price, **1 level**, event-driven L1: `action`, `depth`, `ts_in_delta` + level-00 bid/ask px/sz/ct |
| `mbp-10` | 10 | market-by-price, 10 levels (levels 00–09 px/sz/ct each) + `action`, `depth` |
| `tbbo` | 1 | alias: `TBboMsg = MBP1Msg` (trade-and-BBO = top-of-book + trades) |
| `trades` | — | trades only |
| `bbo-1s` / `bbo-1m` | 195 / 196 | **`BBOMsg`: single-level snapshot, level-00 only** (`bid_px_00, bid_sz_00, bid_ct_00, ask_px_00, ask_sz_00, ask_ct_00`, flags, instrument_id, publisher_id, sequence, ts_event, ts_recv). **No `action`, no `depth`, no levels 01+** — one row per interval |
| `ohlcv-1s/1m/1d` | 32/33/35 | bars (we own `ohlcv-1m`) |
| `definition` | 19 | instrument definitions (owned, ALL10) |
| `statistics` | 24 | exchange statistics incl. settlement (owned, ALL10) |
| `status` | 18 | session/instrument status |

bbo-1m provenance: databento-python CHANGELOG `[0.5.0]` 2022-09-20 (raw.githubusercontent.com/databento/databento-python/master/CHANGELOG.md): "Added support for new schemas `bbo-1s`, `bbo-1m`, and `status`" and "Fixed DBN v1 `TBboMsg` legacy bit-field layout". FACT(changelog).

## 2. Coverage / availability for our 10 codes

- Dataset page `https://databento.com/datasets/GLBX.MDP3` (rendered catalog
  widget, 2026-10-03): **"Coverage: 2010-09-27 → present"**, Standard
  Historical Data section, with per-schema size hints (e.g. mbo
  "935 KB / instrument / month"). FACT(render). **Disclosure**: the page is a
  client-side catalog app — a later no-cache re-render returned the marketing
  shell only; the numbers above are from the first render that materialized
  the widget. Wayback captures of this page (2022/2023/2024/2026) are React
  shells — no archived static catalog exists to verify widget numbers
  independently. Confidence: medium-high, single-live-render.
- Coverage is stated at dataset (market) level; it is not per-symbol. Public
  docs assert no per-symbol gaps for CME flagship codes. **What we OWN on
  disk** (footer-measured, see `COVERAGE_REMEASURE.md`): `ohlcv-1m` for
  ES, NQ (2010-06→) and 6E/6B/6A/6J (2020-01→); `definition`+`statistics`
  ALL10 (2023-10→). **No BBO/MBP/MBO schema is owned for any code**; for
  CL/NG/GC/SI we own no price schema at all. Candidate symbols for any BBO
  campaign: NQ/ES/6E/6B/6J/6A/CL/NG/GC/SI map to continuous- or
  raw-instrument requests in the vendor's own naming (GLBX.MDP3 publishes all
  CME Globex instruments 2010-09-27→present per §2 first bullet).

## 3. Pricing — only what is freely published

FACT(marketing pages, 2026-10-03): pricing is a **usage-license model** quoted
through the data catalog ("Go to our data catalog to start your request");
"New users get $125 in free credits"; exchange license fees are "passed
through these license fees with no upcharge" with the amount determined by a
usage questionnaire. Per-schema dollar prices are behind the catalog flow and
**NOT asserted here** (would require an account — out of scope). Historical =
data "older than 24 hours". No purchase was made; nothing here is an
account-behavior claim.

## 4. CME MDP 3.0 public docs on BBO fields

- The old `cmegroup.com/confluence` MDP 3.0 documentation home is retired
  (ECONNREFUSED / -500, logged). New official home: **CME Group Client Systems
  Wiki**, `https://cmegroupclientsite.atlassian.net` — wiki home states it "is
  the home of CME Globex, iLink, and MDP 3.0 documentation" (FACT, rendered).
- Page "CME MDP 3.0 Market Data", id 284184973
  (`/wiki/spaces/CIAMDW/pages/284184973/...`), retrieved via the wiki's public
  Confluence REST `content/<id>?expand=body.storage` (283,789-byte storage
  body). Verbatim opening: **"CME MDP 3.0 SBE is the CME Globex event-based
  bid, ask, trade and statistical market data format."** This is the official
  description of what MDP 3.0 itself distributes (event-based bid/ask/trade).
- Field-level passages (MDP 3.0 SBE MBO book maintenance, implied orders,
  BBO-handling sections) inside that 283 KB page: **NOT_RUN_PARTIAL /
  BLOCKED_TRANSPORT** — SPA page view returns a cookie shell; REST child-page
  listing 404s; three CQL text-search variants rejected by the fetch tool's
  URL validator; WebFetch of the content endpoint returned 404. Attempts
  logged. The definition sentence above + wiki location stand as the CME
  evidence; anything deeper needs a browser session (owner call).

## 5. Buy-decision input (owner framing; no recommendation executed)

- If the owner wants *bracketing* of top-of-book spread for modeled-cost
  tiering beyond the existing IBKR quote-close proxy: `bbo-1m`/`bbo-1s` are
  the cheapest relevant schemas; `mbp-1` (tbbo) adds event-driven L1 + trade
  flags; `mbp-10` adds depth; `mbo` is the only queue-position-capable feed —
  and even MBO reconstruction models fills, it does not observe them.
- Whatever is bought, D5 law (§0) is unchanged: **bbo-1m CANNOT prove
  intrabar fill/queue; everything stays MODELED COST.**
- Sizing hints from the live render: mbo ≈ 935 KB/instrument/month — mbo for
  10 codes × 16 years would be large; bbo-1m is far smaller (widget showed a
  smaller per-month hint for thinner schemas). Exact figures need the catalog
  quote (owner action).
