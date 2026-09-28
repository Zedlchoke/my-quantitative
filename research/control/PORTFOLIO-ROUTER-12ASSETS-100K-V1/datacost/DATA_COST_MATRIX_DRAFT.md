# DATA_COST_MATRIX_DRAFT — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (Lane L1, 2026-09-28)

Draft authority: LANE_CHARTER.md (this program). Every claim cites a path read
this session. Missing evidence = UNMEASURED / NOT_RUN / UNKNOWN, never inferred.
All 1,200 corpus ideas are HYPOTHESIS/NOT_RUN; nothing here is a PnL claim.

## 0. Cross-cutting laws (read before any row)

1. **No vehicle mixing in PnL.** A strategy's backtest vehicle and its live
   vehicle must be the same instrument class. Backtesting on Dukascopy-style
   spot M1 bid/ask and trading IBKR IDEALPRO, or backtesting CME micro futures
   and trading a broker CFD, are different instruments with different cost
   geometry — PnL may never be summed, averaged or ranked across vehicles.
   (Ancestry law: XAGUSD.md §1.1 "backtest bằng data venue A (futures) mà live
   venue B (broker spot) → phải reconcile identity".)
2. **Prospective data is never history.** IBKR paper-session spread streams
   (2026-09-28 onward) are PROSPECTIVE cost-band evidence only; they must never
   be relabeled as historical spread, and no historical strategy fill may be
   priced from them (DATA-FOUNDATION-SIXSOURCE-V1/ibkr_fx/L-FX_REPORT.md:
   "the cost-band must be assembled from repeated bounded sessions … before
   any research use").
3. **Network-blocked estate.** `*.cmegroup.com`, `*.dukascopy.com`,
   `www.sec.gov` are SNI-filtered on the measured network path (inherited
   ruling L-FXFF-1, restated in DATA-FOUNDATION-SIXSOURCE-V1/INTAKE.md; CME
   re-measured with SNI discrimination in cme_rates/probe_transport_transcript.json
   → BLOCKED_TRANSPORT). Dukascopy M1 corpora below are therefore **frozen
   archives**: they cannot be extended or re-fetched from this host without an
   owner network action.
4. **Cost-authority status (binding measured facts, 2026-09-26/28):**
   - IBKR IDEALPRO (paper, 5 majors incl. NZDUSD): connectivity PASS; two-sided
     LIVE streams confirmed (erratum E1, 2026-09-28); spread measured
     PROSPECTIVE-only 1 hour-bucket; commission/swap/triple-swap/rollover-clock/
     min-size/margin all NOT_RUN pending owner Activity/Flex statement
     (`~/.my-quantitative-data/ibkr_statement/` — directory does not exist as
     of this session). [VERDICT_session2.md, ERRATUM_2026-09-28_sixsource.md,
     EVIDENCE_sanitized_2026-09-26.json]
   - MT5/OANDA read-only cost collector: static audit PASS_ZERO_FORBIDDEN_CALLS
     (static_audit_result.json) but the owner-run 7-day collection has NOT been
     delivered (`~/.my-quantitative-data/forex_mt5_cost_probe_2026-09/` absent)
     → all MT5 cost components NOT_RUN.
   - XAUUSD IBKR London Gold: instrument identity MEASURED (conId 69067924,
     CMDTY, minTick 0.01); commission/storage/borrow STATED-FEE from official
     fetched pages (probes/fetched/commissions-metals.html et al.); one n=1
     live spread sample (connectivity proof only) [cost_authority_checklist.json].

## 1. Per-symbol matrix

Vehicle conventions: "Duka M1 spot" = Dukascopy-format .bi5 M1 bid/ask day
files staged in repo worktrees; "IBKR spot" = IDEALPRO CASH; "CFD" = broker
CFD (no repo cost evidence at all); "futures" = CME/ICE continuous.

| # | Symbol | Cluster | Backtest vehicle (chosen + why) | Contract spec (mult / notional / tick) | Hours | Roll rules | Bid/ask source | Commission | Financing/swap | Margin | Price history in repo | data_status | Recommendation |
|---|--------|---------|--------------------------------|----------------------------------------|-------|-----------|----------------|-----------|----------------|--------|----------------------|-------------|----------------|
| 1 | EURUSD | FX majors | **Spot M1 bid/ask (Duka archive)** for history; **IBKR IDEALPRO spot** as the only measured prospective venue. Futures 6E rejected: CME transport BLOCKED (L-FXFF-1) and roll/CIP basis would mix yield into price (EURUSD.md §1.1) | IDEALPRO CASH; minTick 5e-05 (secdef), stream steps 1e-05 (E2); $10/pip/std lot convention; 6E alt = 125,000 EUR, tick 0.00005=$6.25 (EURUSD.md §1.1) | 24/5, Sun ~21-22 GMT → Fri ~21-22 GMT; rollover 21:00 GMT, Wed 3x swap (EURUSD.md §1.1) | n/a spot; futures would roll H/M/U/Z ~1wk pre-3rd-Wed | HAVE history (per-bar s_open/s_close, sha-pinned) + IBKR paper two-sided PROSPECTIVE (1 bucket) | NOT_RUN (no statement) | NOT_RUN (no statement) | NOT_RUN (whatIf forbidden; report-only) | HAVE_REPO: (a) M1 corpus 2,092 day-files/side 2021-01-01..2026-09-23 `.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/M1/{BID,ASK}`; (b) older 1,826/side 2021-01..2025-12 `.worktrees/eurusd-open-search-v1/integration/research/control/EURUSD-OPEN-SEARCH-V1/data_local/duka/M1/{BID,ASK}`; (c) census BUILD_PASS spread curves p50 0.3 pip overall, rollover p50 0.9/p99 7.8, Sunday-open p50 3.0 (ERP tracka_cohort1/DATACOST_cohort1_REPORT.md) | HAVE_HISTORY_MEASURED_COST_CURVE / PROSPECTIVE_VENUE_UNCOSTED | **ELIGIBLE** (best-evidenced symbol in universe: 5.5y two-sided history + measured per-bar spreads + session census) — but any live-cost claim still needs the owner statement |
| 2 | GBPUSD | FX majors | Same as EURUSD | IDEALPRO CASH; minTick 5e-05; marketName GBP.USD (EVIDENCE_sanitized contract_details) | same 24/5 | n/a spot | HAVE history + PROSPECTIVE 1 bucket (erratum E1: p50 0.4/p90 0.5 pip) | NOT_RUN | NOT_RUN | NOT_RUN | HAVE_REPO: M1 2,092/side 2021-01-01..2026-09-23 `.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/M1/{BID,ASK}`; census spread p50 0.8 pip (DATACOST_cohort1) | HAVE_HISTORY_MEASURED_COST_CURVE / PROSPECTIVE_VENUE_UNCOSTED | **ELIGIBLE** (same class as EURUSD; note GBP-specific BoE/gilt idiosyncrasy does not affect data status) |
| 3 | USDJPY | FX majors | Same as EURUSD | IDEALPRO CASH; minTick 0.005 (3-decimal JPY pair, VERDICT session2 + erratum E2) | same | n/a spot | HAVE history + PROSPECTIVE (p50 0.4/p90 0.6 pip) | NOT_RUN | NOT_RUN | NOT_RUN | HAVE_REPO: M1 2,092/side 2021-01-01..2026-09-23 `.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/USDJPY/M1/{BID,ASK}`; census spread p50 0.5 pip; 1e-3 price-scale probe-proven (DATACOST_cohort1 §1.1) | HAVE_HISTORY_MEASURED_COST_CURVE / PROSPECTIVE_VENUE_UNCOSTED | **ELIGIBLE** (intervention/MoF-disclosure timing is a PIT trap for signals, not for the price panel — see PIT_SOURCE_TABLE) |
| 4 | USDCAD | Commodity-FX | Same as EURUSD; H1/15m derived planes already census-pinned | IDEALPRO CASH; minTick 5e-05 | same | n/a spot | HAVE history (census: overall open p50 1.2/p99 6.2 pips; Sunday-open p50 6.8/p99 21.4) + PROSPECTIVE (p50 0.6/p90 0.6) | NOT_RUN | NOT_RUN | NOT_RUN | HAVE_REPO: derived `bars1h/bars1h_ANC` + census_USDCAD.json + m1_manifest committed `.worktrees/erp1-tracka-cohort-1/repro_twin/research/control/ERP1-TRACKA-COHORT-1/data_local/derived/`; coverage 2021-01-03..2026-06-30 (bars1h 30,386 rows; raw M1 .bi5 no longer physically present in repro_twin — manifests + PITDATA-recorded sha256s are the anchors; 2026-H1 bars physically inside parquet, dev/holdout seam = timestamp filter) [PITDATA_cohort2_REPORT.md] | HAVE_HISTORY_MEASURED_COST_CURVE (derived planes pinned; raw M1 archive-frozen) | **ELIGIBLE** with caveat: any refresh/extension of raw M1 is BLOCKED_TRANSPORT (Dukascopy SNI, L-FXFF-1) |
| 5 | AUDUSD | Commodity-FX | Same as USDCAD | IDEALPRO CASH; minTick 5e-05 | same | n/a spot | HAVE history (census: overall open p50 1.0/p99 4.1; Sunday-open p50 4.6/p99 14.8) + PROSPECTIVE (p50 0.1/p90 0.2) | NOT_RUN | NOT_RUN | NOT_RUN | HAVE_REPO: `bars1h_ANC_AUDUSD.parquet` (sha 4e0ca174…) + census_AUDUSD.json (d337ff2c…) same dir as USDCAD; coverage 2021-01-03..2026-06-30 (bars1h 30,420 rows) | HAVE_HISTORY_MEASURED_COST_CURVE (same caveats as USDCAD) | **ELIGIBLE** (same caveats as USDCAD) |
| 6 | NZDUSD | Commodity-FX | Spot M1 (Duka-class) — but **no corpus exists**; IBKR identity measured | IDEALPRO CASH; conId 39453441, minTick 5e-05 (EVIDENCE_sanitized contract_details) | same | n/a spot | PROSPECTIVE only: NZDUSD was in the 2026-09-26 Saturday probe (0 two-sided obs, closure) and is **NOT** in the 5-pair 2026-09-28 re-measure (erratum lists EURUSD/GBPUSD/AUDUSD/USDCAD/USDJPY) → two-sided NEVER measured on NZDUSD | NOT_RUN | NOT_RUN | NOT_RUN | MISSING: no M1/H1 corpus anywhere in worktrees or data store (per-symbol dir search across `.worktrees/` found only EURUSD/GBPUSD/USDJPY/AUDUSD/USDCAD); Twelve Data ng1 4-pair grid incl. NZDUSD declared in survey (forex_frontier_2026-09/survey_report.md §"What the repo already has") but its worktree was cleaned 2026-09-12 → not physically present, coverage UNKNOWN | PRICE_HISTORY_MISSING / SPREAD_UNMEASURED_EVERYWHERE | **FLAT_BLOCKED_DATA** — reason: no price history in repo and Dukascopy fetch path network-blocked. Unblocking owner action (one): authorize+network-open a fetch lane for NZDUSD M1 history (Dukascopy SNI unblock, or name an entitled keyless vendor), or explicitly re-class the symbol out of the router universe |
| 7 | USDCHF | FX majors | Spot M1 (Duka-class) — no corpus; no IBKR probe coverage either | IDEALPRO CASH (assumed class; **no secdef measured** — USDCHF absent from both probe sessions) | same | n/a spot | UNMEASURED (never in any probe) | NOT_RUN | NOT_RUN | NOT_RUN | MISSING: no corpus found (same search as NZDUSD); ERP program explicitly lists "USDCHF/unsearched pairs … gated (data gate + owner slate amendment)" (forex_program/VIABILITY_cohort3_REPORT.md §A) | PRICE_HISTORY_MISSING / INSTRUMENT_UNMEASURED | **FLAT_BLOCKED_DATA** — reason: no price history, no measured instrument identity. Unblocking owner action: same as NZDUSD (one network/vendor decision covering both stragglers) |
| 8 | XAUUSD | Precious metals | **Backtest vehicle: TD/Twelve-Data daily archive, ARCHIVE/REFERENCE ONLY** (long-horizon context); executable-venue costs must come from the IBKR London Gold probe line (still prospective). Broker CFD rejected as unmeasured; COMEX GC rejected (CME blocked) | IBKR London Gold CMDTY: conId 69067924, minTick 0.01, SMART/USD (tws_light_check.json); retail lot 100 oz convention; GC alt = 100 oz (XAUUSD.md §1.1/§1.2 context) | near-24/5 (Sun ~22:00 → Fri ~21:00 UTC), LBMA AM 10:30/PM 15:00 London fixes (XAUUSD.md §1.1) | n/a (spot/CMDTY); CFD would embed monthly synthetic roll | IBKR: n=1 live sample 0.40 USD/oz ≈ 0.92 bps (connectivity proof ONLY); CFD STATED $0.20-0.35/oz (XAUUSD.md §1.1, unmeasured) | STATED-FEE 1.5/1.0/0.7 bps tiered, min $2.00/order (official fetched page, STATED not measured) | STATED storage 0.10%/yr long (360-day); short borrow BM+1%/0.5%/0.3% (same page) | STATED-FEE (fetched margin pages staged); measured whatIf forbidden | HAVE_REPO (restricted): `XAUUSD_1day_full.json` 1979-12-26..2026-09-16, sha256 49c2684e…, at `.worktrees/forex-ng6/integration/research/control/forex_ng6_run/p0/staging/`; **status ARCHIVE/REFERENCE ONLY** — any join to IBKR needs gates 1-3 (PIT lag, basis test, representation contract) of td_archive_join_contract.json, thresholds still TO BE FROZEN; XAUUSD-SHADOW-V1 prospective runtime (12,540 bars to 2026-09-23) is TERMINAL evidence, not a research corpus (CLOSEOUT_OWNER_REMOVAL_2026-09-24.md) | DAILY_ARCHIVE_GATED / INTRADAY_MISSING / COST_PROSPECTIVE_ONLY | **FLAT_PIT_UNPROVEN** (for any intraday or cost-bearing strategy) — reasons: (a) TD composite is not the executable venue and its PIT availability lag L is UNMEASURED (gate 1 explicitly demands declared-assumed L, never inferred); (b) no intraday bid/ask history; (c) spread distribution prospective-only (n=1). Unblocking owner action (one): resume the frozen XAUUSD IBKR resumable probe (probes/ + resumable_probe_state_design.json exist) to accumulate ≥20-day overlap + freeze basis thresholds, i.e. fund/authorize the bounded probe sessions — daily-only regime research may cite the TD archive with the declared D+1 L assumption in the interim |
| 9 | XAGUSD | Precious metals | No defensible vehicle yet. Preferred target (per XAGUSD.md §1.1): COMEX SI back-adjusted continuous — but CME is transport-blocked; broker spot CFD has zero repo evidence | COMEX SI 5,000 oz/lot, Micro SI 1,000 oz; retail 1 lot ≈ 5,000 oz ≈ $325k notional at $65 (XAGUSD.md §1.1); tick convention per broker, pip 0.001 vs 0.01 ambiguity flagged | near-24/5 (Sun ~21-22 ET → Fri 17:00 ET) (XAGUSD.md §1.2) | futures monthly roll; broker CFD embeds roll in swap | UNMEASURED everywhere (no probe, no archive) | NOT_RUN | NOT_RUN | NOT_RUN | MISSING: no XAGUSD price file anywhere (global filename search found only brainstorm docs/handoffs); LBMA auction, COMEX, CFD — none staged | PRICE_HISTORY_MISSING / COST_ALL_UNMEASURED | **FLAT_BLOCKED_DATA** — reason: zero price history, zero cost evidence, and the "right" venue (COMEX) is network-blocked. Unblocking owner action: ONE vendor/transport decision — either open SNI for the futures-data path (same owner action as CME rates) or authorize a named entitled spot-metals history source (TD/Twelve Data serves XAG/USD from 1979-class history per the XAU precedent, ng6 probes) |
| 10 | BRENT | Energy | Broker CFD (UKOIL) tracks ICE front-month — repo has **no** ICE entitlement, no CFD account evidence; ICE not in the blocked-estate list but never probed | ICE Brent 1,000 bbl/contract; CFD 10-100 bbl/lot broker-specific (BRENT.md §1.1, "(cần kiểm chứng)"); tick 0.01 | CFD ~Sun 22:00 London → Fri ~21:45-22:00 London; liquidity peak London 08:00-16:30 (BRENT.md §1.1) | monthly: ICE front ceases last business day of month T-2; broker rolls ~Friday of expiry week; **back-adjusted vs unadjusted changes breakout results qualitatively** (BRENT.md §1.1) | UNMEASURED | NOT_RUN | NOT_RUN (CFD margin 1-5% class per NATGAS.md §1.3 analog, "(cần kiểm chứng)") | NOT_RUN | MISSING: no Brent price history staged (search confirmed); only macro probes (EIA route JSONs) exist | PRICE_HISTORY_MISSING / COST_ALL_UNMEASURED / ROLL_MODEL_MISSING | **FLAT_BLOCKED_DATA** — reason: no price series, no roll series (term structure absent → cannot even model contango/backwardation carry), no cost evidence. Unblocking owner action: one entitlement/venue decision naming the Brent history+continuous-contract source (vendor EODHD-family is entitled for stocks /eod only per ng5 PROBE_INDEX — FX/commodity coverage NOT probed; owner must name the door) |
| 11 | WTI | Energy | Same class as BRENT (broker "USCRUDE/USOIL" CFD tracks NYMEX CL front-month); CL continuous preferred but CME-blocked | NYMEX CL 1,000 bbl, tick 0.01 = $10/contract; expiry ~3 business days before day-25 of prior month; roll ~5 days earlier (WTI.md §1.1) | Globex Sun 18:00 ET → Fri 17:00 ET, break 17:00-18:00 ET; EIA Wed 10:30 ET (Thu if Monday holiday — classic backtest trap, WTI.md §1.2) | monthly roll; CFD swap embeds roll cost ("roll cost là chi phí chiến lược", WTI.md §1.1) | UNMEASURED | NOT_RUN | NOT_RUN | NOT_RUN | MISSING: no WTI/CL price history staged | PRICE_HISTORY_MISSING / COST_ALL_UNMEASURED / ROLL_MODEL_MISSING | **FLAT_BLOCKED_DATA** — reason: identical to BRENT. Unblocking owner action: same single energy-data decision (one vendor/transport choice can cover BRENT+WTI+NATGAS if it serves NYMEX/ICE continuous futures) |
| 12 | NATGAS | Energy | Broker CFD proxy of NYMEX NG (NATGAS.md §1.1); NG continuous preferred but CME-blocked. Any CFD backtest MUST model: wide spreads $0.02-0.06 (0.7-2% at $3), 3-10x spread widening at EIA Thu 10:30 ET, weekend gaps 2-5% (10%+ tail), winter margin hikes, ×100 vs ×1000 quoting (NATGAS.md §1.3) | NG 10,000 MMBtu/contract, tick $0.001 = $10/contract; last trade ~3 business days before delivery month → monthly front roll inherent (NATGAS.md §1.1) | Globex Sun 18:00 ET → Fri 17:00 ET; settlement 14:30 ET; model-run digests 07:00-08:00 & 13:00-15:00 ET (NATGAS.md §1.2) | monthly roll; widow-maker Mar/Apr structure; broker expiry ≠ NYMEX expiry (NATGAS.md §1.3) | UNMEASURED (CFD spread figures are STATED knowledge, "(cần kiểm chứng theo broker)") | NOT_RUN | NOT_RUN (STATED "vài %/năm" long-carry, unmeasured) | NOT_RUN (winter deleveraging risk) | MISSING: no NATGAS/NG price history staged; only EIA weekly storage probe rows (60 rows, 2026-07-17..2026-09-04, free-data-frontier-v1/raw/eia_open_data/natural_gas_storage_weekly.json) + NWS station probes | PRICE_HISTORY_MISSING / COST_ALL_UNMEASURED / WEATHER_PIT_MISSING | **FLAT_BLOCKED_DATA** — reason: no price history AND the symbol's #1 driver (weather HDD/CDD forecasts) has no PIT-archived source (NWS probe is current obs only; forecast archives unevidenced). Unblocking owner action: same energy decision as WTI/BRENT, **plus** an explicit weather-forecast archive choice (see PIT_SOURCE_TABLE row "weather HDD/CDD") — for NATGAS these are two unblocks, but the price-history one is the single action that changes its FLAT status |

## 2. Summary recommendation table

| Symbol | Recommendation | Single unblocking owner action |
|---|---|---|
| EURUSD | ELIGIBLE | (none for research; owner IBKR Activity/Flex statement → `~/.my-quantitative-data/ibkr_statement/` unlocks commission/swap/min-size for live-cost realism) |
| GBPUSD | ELIGIBLE | same statement action |
| USDJPY | ELIGIBLE | same statement action |
| USDCAD | ELIGIBLE | same statement action (+ network unblock if raw-M1 refresh ever needed) |
| AUDUSD | ELIGIBLE | same statement action |
| NZDUSD | FLAT_BLOCKED_DATA | authorize one NZDUSD M1 history source (Dukascopy SNI unblock or named entitled vendor) |
| USDCHF | FLAT_BLOCKED_DATA | same single decision (covers NZDUSD+USDCHF) |
| XAUUSD | FLAT_PIT_UNPROVEN | resume the frozen bounded IBKR XAUUSD probe sessions (accumulate overlap + freeze basis thresholds per td_archive_join_contract.json) |
| XAGUSD | FLAT_BLOCKED_DATA | one metals-history vendor/transport decision (COMEX path unblock or entitled spot-metals history) |
| BRENT | FLAT_BLOCKED_DATA | one energy continuous-futures history decision (vendor/entitlement) |
| WTI | FLAT_BLOCKED_DATA | same single energy decision (can cover all 3 energies) |
| NATGAS | FLAT_BLOCKED_DATA | same energy decision (+ separate weather-archive decision for its driver layer) |

Vehicle-switch comparability notes (what a switch would cost):
- FX: Duka-spot history → IBKR spot: same instrument class, basis expected
  small but UNMEASURED (no overlap census exists between Duka mids and IBKR
  mids; the ERP EDQ1 independent-replication attempt died BLOCKED_SOURCE_LICENSE
  per VIABILITY_cohort3_REPORT.md §A). Cost curves are NOT transferable:
  Duka per-bar spreads vs IBKR paper books are different books.
- XAUUSD: TD daily composite → IBKR London Gold: gated by contract
  (td_archive_join_contract.json); basis metrics must be frozen pre-use.
- Any spot/CFD ↔ futures switch (6E/M6E, GC, SI, CL, NG, BZ): introduces
  roll yield, exchange margin, session gaps at 17:00-18:00 ET and different
  tick geometry — backtests are not comparable and PnL must never be pooled
  (Law §0.1). The M6E/M6B/MCD/MJY/M6A micro-futures product pages staged in
  `~/.my-quantitative-data/fx-futures-frontier-v1/raw/lane-a2/` are HTML
  reference only — zero price bytes exist for any futures series anywhere.

## 3. Evidence index (paths read this session)

- research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/LANE_CHARTER.md
- research/control/DATA-FOUNDATION-SIXSOURCE-V1/{FINAL_REPORT.md, INTAKE.md,
  ibkr_fx/L-FX_REPORT.md, ibkr_fx/sessions_index.jsonl,
  cme_rates/probe_transport_transcript.json}
- research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/
  {VERDICT_session2.md, ERRATUM_2026-09-28_sixsource.md,
  EVIDENCE_sanitized_2026-09-26.json}
- research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/DATACOST_cohort1_REPORT.md;
  tracka_cohort2/{PITDATA_cohort2_REPORT.md, COSTAUDIT_F5_cohort2_REPORT.md};
  forex_program/VIABILITY_cohort3_REPORT.md
- research/control/xauusd_ibkr_probe_2026-09/{cost_authority_checklist.json,
  td_archive_join_contract.json, probes/fetched/ listing}
- research/control/forex_mt5_cost_probe_2026-09/{OWNER_RUN.md, static_audit_result.json}
- research/control/XAUUSD-SHADOW-V1/CLOSEOUT_OWNER_REMOVAL_2026-09-24.md
- research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/{EURUSD, XAGUSD,
  XAUUSD, WTI, BRENT, NATGAS}.md §1; macro/CURRENCIES_CORE.md; README.md
- research/control/forex_frontier_2026-09/{survey_report.md, probes/PROBE_MANIFEST.json}
- research/control/ng5_ng6_frontier_2026-09/probes/{PROBE_INDEX.json,
  ng6_x2_xauusd_earliest_timestamp.json}
- Data store + worktree listings (read-only): `~/.my-quantitative-data/` tree;
  `.worktrees/{fx-rangefade-2m-shadow-v1, fx-majors-search-v1,
  eurusd-open-search-v1, erp1-tracka-cohort-1, forex-ng6}/` file counts,
  first/last day-file names, derived/ contents.
