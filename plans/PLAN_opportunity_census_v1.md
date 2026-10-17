# PLAN — OPPORTUNITY-CENSUS-V1 (cross-market post-price/fee opportunity census, budget 0/0)

- cycle_id: `OPPORTUNITY-CENSUS-V1` · asset: shared · **budget 0 scored cells by
  law (0/0)** · **NO go_phrase by design** (a census never scores; any successor
  scored phase registers its own GO at its own gate, P-8)
- Owner instruction 2026-10-17 (this chat): identify **where measurable
  post-price-and-fee advantage can exist** across prediction markets for sport
  and weather, **before** investing further in models. Scope: NBA, WNBA, men's
  football (soccer lane = men's internationals), WSL, NWSL, weather, plus every
  related cycle found in `plans/CYCLE_REGISTRY.json`. Authorized: register this
  census cycle with scored budget 0/0 **because no suitable cycle exists**
  (verified at intake 2026-10-17: closest precedents are per-league and closed —
  `WNBA-ODDS-DISCOVERY-PREP-V1` NOT_RUN_ODDS, `WSL-WINPROB-DISCOVERY-PREP-V1`
  NOT_RUN_ODDS, `SPORTS-WINPROB-DISCOVERY-PREP-V1` results-corpora only
  TERMINAL, `TARGET-CENSUS-20261016` futures-only TERMINAL).

## 0. Hard fences (violating any of these is a cycle failure)

- Census ONLY: **no model fitting, no signal trials, no scored PnL, no new TEST
  views**. `WEATHER-TEMP-PROB-V1` 6/6 cells stay consumed and untouched; every
  TERMINAL/ACTIVE cycle's rows, ledgers, keys, quotas, engines and verdicts are
  read-only to this cycle.
- No S1 access, no push, no merge to main, no history rewrite, no purchases, no
  account creation, no credentials in prompts/logs/git, no `git add -A`, no
  standing collector, no order placement (real or paper).
- Closing odds and un-timestamped prices are NEVER reported as placeable prices.
- Owner untracked files stay untouched: `.my-quantitative-data/`, `plan_ml.md`,
  `research/control/FUTURES-SLOWTREND-PREP-V1/`, `research/control/FUTURES-SLOWTREND-W3/`,
  `research/control/FUTURES-VSA-ESNQ-V1-postCAS/`, `research/control/weather_pred_prep_v1_draft/`.
- New harvest is prohibited. The only network activity allowed is (a) reading
  public ToU/docs pages, and (b) **small journaled count-level probes** of the
  two venues whose public-read probe patterns are already established by prior
  authorized cycles (Polymarket Gamma/CLOB public GETs — SPORTS-POLYMARKET-CUTOVER-PREP-V1
  pattern; Kalshi public markets GET — WSL lane precedent). Hard cap: **≤ 30
  HTTP GETs total**, no auth, $0, no pagination past 3 pages per query, storage
  limited to counts + IDs + close times + already-pinned rules text. If a
  source's rights verdict is `HOLD_PENDING_ENTITLEMENT`, its probe stays
  count-level and nothing deeper is stored or fetched.

## 1. Census unit and frozen schema `opportunity_census@1`

The census unit is **one decidable opportunity**: a single contract/outcome at a
single decision anchor, joinable to exactly one forecast row and one settlement
row. Freeze `research/control/OPPORTUNITY-CENSUS-V1/SCHEMA.md` with these
required fields (null allowed only where the evidence class says so, never
fabricated):

`opportunity_id` (sha256 of canonical field tuple) · `event_id` · `league` ·
`season` · `market_key` (market type + outcome semantics, e.g. `ML_HOME`,
`1X2_DRAW`, `TEMP_BUCKET`) · `venue` · `venue_contract_id` · `decision_time_utc`
· `forecast_version` · `forecast_issue_time_utc` · `forecast_available` ·
`quote_time_utc` · `bid` · `ask` · `mid` · `decimal_odds` · `bid_size` ·
`ask_size` · `fee_taker` · `fee_maker` · `fee_rule_ref` · `rules_version`
(sha256 of verbatim resolution text) · `settlement_source` · `settlement_value`
· `settled_at_utc` · `rights_verdict` · `rights_ref` · `evidence_class` ·
`prospective_eligible` (derived) · `provenance_url` · `provenance_sha256` ·
`exclusion_code`.

**Dedup law**: `venue_contract_id` unique per row; the YES/NO sides of one
binary contract are ONE opportunity (two-side prices on one row, never two);
a multi-outcome event (1X2, temp buckets) yields one row per outcome-contract;
the same contract re-listed under a second source alias is one row with the
primary venue and the alias recorded in provenance — never two rows.

## 2. Evidence classes (owner-defined, frozen)

Per **price source × league**:

- **A** — timestamped quote with price AND size/depth that can be matched
  placeable (resting book: Polymarket CLOB multi-level with sizes; Kalshi
  orderbook) **and** rights usable for research. Only A is proposable for
  prospective economic evaluation.
- **B** — historical price exists but lacks execution evidence (no size/depth,
  bucketed series, last_update grids, `prices-history`): The Odds API snapshots,
  Polymarket `prices-history`, Kalshi candles. Diagnostic only.
- **C** — closing odds only, or no per-row PIT timestamps: football-data.co.uk,
  OddsPortal-class display archives, opener/close-only archives.
- **D** — no price at all (results-only corpora: martj42, ewf-database,
  OpenFootball, ESPN schedule/results, GFS/NOAA panels).

Classes other than A carry the NOT_RUN family code in the exclusion ledger
(`NOT_RUN_NO_EXECUTABLE_PRICE`, `NOT_RUN_CLOSING_ODDS_ONLY`, ...) and are never
promoted by narrative. A sources failing rights (`HOLD_PENDING_ENTITLEMENT`,
`PAID_UNAUTHORIZED`) keep class A evidence-grade for price mechanics but are
**excluded from the shortlist** via the rights gate and ledgered.

## 3. Work products (all under `research/control/OPPORTUNITY-CENSUS-V1/`, worktree)

1. `INVENTORY.md` + `inventory.csv` — per league × market type × source:
   seasons, two-sidedness, odds format, PIT semantics, fees, rate limits, cost,
   rights verdict + verbatim quote, evidence class, provenance pointer to the
   prior cycle artifact that measured it.
2. `SCHEMA.md` — the frozen `opportunity_census@1` above + dedup law.
3. `COVERAGE_TABLE.csv` — league × season × market × evidence-class counts.
   Every count cites its measured source artifact (prior cycle census/panel or
   today's probe); nothing is estimated silently.
4. `EXCLUSION_LEDGER.csv` — one row per league × market × source that cannot
   decide an opportunity, with exclusion code from this frozen taxonomy:
   `NO_MARKET`, `NOT_LISTED`, `SEASON_OFF`, `NO_ODDS_SOURCE`,
   `RIGHTS_BLOCKED`, `HOLD_PENDING_ENTITLEMENT`, `PAID_UNAUTHORIZED`,
   `PIT_UNPROVABLE`, `PIT_FORECAST_ONLY_TRADING_VIEW_UNPROVEN`,
   `SETTLEMENT_UNPROVEN`, `JOIN_AMBIGUOUS`, `QUOTA_PAID_ONLY`,
   `FENCED_BY_PRIOR_CYCLE`, `NOT_RUN_RESOURCE_CONFLICT`.
5. `PROBE_JOURNAL.jsonl` + `OPEN_MARKET_CENSUS.json` — today's count-level open
   market state per venue × league (see §4).
6. `RUBRIC.md` + `rubric_scores.csv` + `SHORTLIST.md` — frozen rubric (§5),
   mechanical scoring, at most **two** shortlisted markets.
7. `verify_census.py` + `VERIFY_RECORD.json` — independent verifier (§6).
8. `MANIFEST.json` — sha256 of every census artifact.
9. `CENSUS_CLOSEOUT.md` — verdict `READY_FOR_OWNER_REVIEW` or `HOLD:<reason>`,
   first next action, missing data, owner decisions required.
10. `handoff.json` — `zcode_orch_v3_handoff@1` structured handoff.

## 4. Probes (small, limited, permitted — the only network fetches)

Pre-probe ToU reads (attempted 2026-10-17 pre-registration, journaled):
Kalshi API Developer Agreement → HTTP 429 (unreadable; same as weather prep
draft 2026-10); Polymarket `/terms` + `/terms-of-service` → HTTP 404 (not
locatable; same as weather prep draft). Rights verdicts therefore carry forward
from the prior authorized cycles verbatim: Polymarket = public read-only API,
no auth, $0, census storage at counts/metadata level only, deeper historical
harvest stays fenced (NWSL plan decision 6: `prices-history` research-only);
Kalshi = **HOLD_PENDING_ENTITLEMENT** (governing docs identified, never
byte-readable), count-level observation only, no storage of price history.

Probe queries (each journaled: url, fetched_at_utc, http_status, bytes, sha256
of the stored count-level extract):

- Polymarket Gamma public events: open (active, not closed) market counts for
  NBA, WNBA, WSL, NWSL, men's-international soccer tags/series; ≤3 pages/query.
- Polymarket CLOB book spot-check: ≤ 8 open tokens total — one snapshot each
  (top-of-book with sizes) to evidence class-A mechanics today. No history.
- Kalshi public `GET /trade-api/v2/markets` by series: `KXHIGHNY`, `KXHIGHCHI`,
  `KXHIGHMIA`, and NBA/WSL/NWSL series keys → count of open markets + tickers +
  close times only. No candlesticks, no trades, no fills.
- Weather weather: the daily-temp series are always-on; counts feed the coverage
  table directly.

If any probe returns non-200 or a wall (429/403), record it and stop that
source's probes (`NOT_RUN_RESOURCE_CONFLICT` / `RIGHTS_BLOCKED`); no retries
beyond one.

## 5. Frozen selection rubric (decided BEFORE probe numbers are read)

Gates (fail ⇒ not shortlistable, recorded with its gate code):

- G1 RIGHTS: prospective-use rights verdict for the venue is not
  HOLD/UNAUTHORIZED (`PROBE_OK`, `GRANTED_WITH_EVIDENCE`, or public-read with
  census-level storage consistent with prior cycles).
- G2 PIT: evidence class A available at the venue for the market, with a
  proven quote/decision ordering law (or a probe-verifiable one).
- G3 N: ≥ 60 independent event-opportunities in the next ~6 months of the
  league's published calendar window (measured from census counts, not hope).

Scored criteria (0–5 each, mechanical, thresholds written in `RUBRIC.md` before
scoring): S1 rights quality; S2 PIT quote ratio attainable at decision anchor;
S3 independent opportunity count per rolling 12 months; S4 spread+fee drag
(lower better, measured or vendor-documented); S5 matchability of forecast↔
contract joins (known join laws); S6 quote freshness/latency at the anchor;
S7 research cost ($0 = 5, paid = lower; existing verified adapters score high).

Shortlist = top ≤2 by total score among gate-passers. **Historical PnL is not
an input** — the rubric consumes only rights, PIT, counts, costs, joins,
latency. The scoring script is frozen before probe numbers are read and its
output is committed unmodified.

## 6. Independent verifier

`verify_census.py` re-derives from bytes only: (1) row counts reconcile across
inventory ↔ coverage table ↔ exclusion ledger; (2) uniqueness of
`venue_contract_id` and of (event, market, anchor) — dedup law; (3) timestamp
ordering: every row marked prospective-eligible must have
`quote_time_utc <= decision_time_utc` proven or the row fails; (4) every source
row carries `rights_verdict` + `rights_ref`; any HOLD source must have
`prospective_eligible=false`; (5) `MANIFEST.json` sha256 recompute matches all
artifacts; (6) rubric: shortlist ⊆ gate-passers, ≤2 entries, scores recompute
from `rubric_scores.csv`. Exit codes: `0` PASS · `2` CHECK_FAIL (list findings)
· `3` NOT_RUN_RESOURCE_CONFLICT · `4` SCHEMA_OR_CODE_ERROR. A fresh-context
verifier pass (separate agent, no shared scratch state) re-runs the script and
spot-checks ≥5 load-bearing claims against the cited prior-cycle artifacts.

## 7. Successor ladder (handoff only — none of it runs in this cycle)

Each step is its own future cycle with its own gate and owner GO:
`market-implied baseline` (per shortlisted market; B0 = market price at anchor
vs naive; diagnostic, 0 scored) → `incremental signal` (existing frozen
forecast engines vs market-implied baseline, diagnostic) → `paper prospective`
(class-A venue capture, pre-registered) → `post-fee PnL` (scored; owner typed
GO at its own gate; S1 law applies).

## 8. Stopping rule

HARD STOP at census close: no fit, no scored run, no GO phrase, no collector,
no orders, no purchases, no push/merge. Verdict is
`READY_FOR_OWNER_REVIEW` only if the verifier passes clean; otherwise
`HOLD:<reason>` with the specific failing check. Owner decisions expected (not
pre-decided): funding any paid historical source (The Odds API 20K month,
Betfair), Kalshi entitlement read path, and any successor GO.
