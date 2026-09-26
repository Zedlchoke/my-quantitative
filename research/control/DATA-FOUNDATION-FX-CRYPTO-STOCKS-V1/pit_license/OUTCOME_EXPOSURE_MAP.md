# OUTCOME_EXPOSURE_MAP.md — exposed vs unopened data (L-PIT, 2026-09-26)

Cycle: DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 · Lane: L-PIT.
Sources (READ-ONLY, per packet): `research/wayfinder/HYPOTHESIS_LEDGER.md`
(273-line ledger, cumulative rows through ERP1-TRACKB-COHORT-1) +
`research/wayfinder/MAP.md` (sprint states through PWS-CX-SOLUSDT-C1 /
SRLV-CX-C1 terminals, 2026-09-26). Nothing in this file was inferred from
data files; sealed/holdout content was never read — ERP1 holdouts appear
here as committed-manifest/ledger METADATA only (plan §14 F8).

Definitions:
- **OUTCOME-EXPOSED** research data = every dev/holdout window actually read
  by a scored or exploratory cycle (ledger/MAP shows it was consumed by a
  cell computation, an exploratory S0 trial, or a falsifier that read
  outcomes). Confirmation weight of exposed history is 0 for new claims
  (ILLIQ-REG-V1 standing ancestry law).
- **UNOPENED** confirmation data = S1 (sealed everywhere), the ERP1 sealed
  2026-H1 AUDUSD/USDCAD holdouts (UNREAD program assets), all post-2026-09
  prospective collector streams, and all future windows.
- Not listed as either: data staged/censused but never consumed by an
  outcome-bearing or exploratory computation (e.g. FDF-V1 macro corpora) —
  research-readable, outcome-unexposed.

---

## (a) OUTCOME-EXPOSED research data (instrument × window × consuming cycle)

### FX (Dukascopy M1 bid/ask plane, owner-delegated 2026-09-23)
| Instrument | Window | Consumed by |
|---|---|---|
| EURUSD M1/15m/H1 | dev 2021-01-01..2025-12-31 (3,652 day files) | EURUSD-OPEN-SEARCH-V1 (48 exploratory S0 trials; 1 candidate FAILED its holdout look), EURUSD-RANGEEXP-SCORED-V1 (5 scored observables; S2–S6 legs both windows) |
| EURUSD H1 | holdout 2026-H1 (fresh extension) | EURUSD-OPEN-SEARCH-V2 (48 exploratory trials; FX2-RANGEEXP-C3/C4 PASSED their ONE preregistered holdout look — window now EXPOSED), EURUSD-RANGEEXP-SCORED-V1 (S1 gate 12/12 + leg decompositions on both windows) |
| EURUSD samples | 2023-06-15, 2024-03, 2025-06-13 probes | EURUSD-DATA-QUALIFICATION-V1 P1 (probe/sample decodes) |
| GBPUSD H1 | dev + 2026-H1 holdout | FX-MAJORS-SEARCH-V1 (48 trials; RANGEEXP-C3/C4 passed holdout — exposed) |
| USDJPY H1 | dev + 2026-H1 holdout | FX-MAJORS-SEARCH-V1 (48 trials; PDHLOC-C2/RANGEEXP-C3 thin pass — exposed) |
| AUDUSD + USDCAD | dev windows (range-fade replication battery) | ERP1-TRACKA-COHORT-1 (12 scored cells, R-ANCHOR/R-ORIG + falsifiers; holdouts UNREAD) |
| AUDUSD + USDCAD (F-2 battery) | PIT-battery panels | ERP1-TRACKA-COHORT-2 (0 scored cells; battery + 47-shadow rho arrays read signal-level only) |
| TD majors (5 pairs) daily + XAUUSD 1day | staging/trigger censuses (FEASIBLE, no outcomes) | FOREX-NG5 (CoT census reads), FOREX-NG7 (F5 trigger census; family never scored), FOREX-NG6 (price-side P0 census 1979-12-26..2026-09-16) |

### FX macro/vintage planes (read by scored or D2-measuring cycles)
| Data | Window | Consumed by |
|---|---|---|
| Vintaged CPI GB/CA/AU/NZ/US + 323 PIT instants + TD spot grid (1,842 days) + DGS10 control | ng1-era S0 | FOREX-NG1 (6 scored cells — exposed), FOREX-NG2/NG3 (revision censuses; 0 cells), FOREX-NG4 (EZ HICP 97 vintages + EURUSD plane; 0 cells) |
| FRED granted set (DGS10/DGS2/DFII10/DFII5/T10YIE/T5YIE/CPIAUCSL) + Treasury curve + ETP legs | FOREX-V8, FOREX-NG1, RATES-NG1 S0 windows | FOREX-V8 (3 cells), FOREX-NG1 (6 cells), RATES-NG1 (3 scored cells — exposed; falsification-by-control #16) |

### Crypto (Binance Vision/fapi keyless + venue collectors)
| Instrument / panel | Window | Consumed by |
|---|---|---|
| BTC/ETH/alts perp klines + funding + OI + metrics (V-series) | S0 windows 2019/2020..2026-08 | V6–V17 governed cycles (155/158 crypto cells — exposed), incl. aggTrades 1.29B-row streaming panel (V16), UTC-H1 1.391B-row 3-symbol panel (V17) |
| S4 Binance H1 panels (365d, BTC/ETH) + OI | 2025-08..2026-08 era | CRYPTO-NG1/NG2 (D2 shadow measurements; S4 5/5 digests), cng4-a3 regime constants |
| BTC H1/H4 2020–2026 Vision klines (284 files) + measured funding | 2020-01..2026-08 | PHASE-STRATEGY-V1 (20/20), BTC-H4-CONTINUATION-V2 (forensic rebuild), BTC-H4-EDGE-SEARCH-V1 (8/8 cells + funding audit), BTC-H4-BAND-RISK-V1 (8/8 + DIAG census "NO long book passes G5 on BTC 2020-2026"), BTC-H4-TWO-REGIME-V1 (descriptive detector census, 14,589 H4 bars) |
| ETHUSDT H4 + BTC state + ETHBTC ratio + funding | 2020-01..2026-08 | ETHUSDT-OPEN-SEARCH-V1 (24/24 arm-tier computations — exposed) |
| BTC/ETH 1h perp panels | 2020-2026 | SRLV-CX-C1 (6/18 scored cells — exposed) |
| SOLUSDT klines (52,145 bars) + funding (6,580 settlements) + bookTicker census | 2020..2026-09 | PWS-CX-SOLUSDT-C1 (staging/verification/falsifier reads; **0 outcome views, 0 PnL** — exposed as READ, unexposed as outcomes) |
| Stablecoin on-chain census (USDT/USDC finalized logs) | 2025-08-22..2026-08-23 | CRYPTO-NG3 (D2 measured kills; no scored cells) |
| BTC/ETH/SOL H1 panels + OI + funding | frozen ng4 folds | CRYPTO-NG4 (D2 R0 veto all; 0 cells); prospective collectors ran 2026-09-16T22:29:29Z→2026-09-17T00:52Z then stopped (that stream window is PROSPECTIVE, see (b)) |
| ILLIQ anchor (crypto V11 lineage) | S0R 2024-08-22..2025-08-21 | ILLIQ-REG-V1 (4/4 diagnostic cells — exposed) |

### Stocks (EODHD-entitled EOD + SEC substrates)
| Data | Window | Consumed by |
|---|---|---|
| 12-ETF sector cohort daily | S0 windows V1–V5 era | STOCKS-FREE V1–V5 (21/21 cells) |
| EODHD EOD panels (current + death-inclusive cohort; 16,575-code staging; Form-4 substrate 5,453,478/1,667,422 rows) | S0 windows V8–V13 era | STOCKS-FREE V8 (6), V9 (3), V10 (6), V11 (3), V13 (3), STOCKS-NG1/NG2 (D2/P0 reads; 0 cells) |
| Identity-quarantined EODHD universe | 2019-2022 emphasis windows | STOCKS-AMIHUD-V1 (3/3), STOCKS-AMIHUD-RETEST-V1 (3/3 — exposed) |
| QQQ/SPY weekly breadth (1,064 weeks from 2006-04-28) | 2006..2026 | STOCKS-NG5 (D2 shadow measurement; 0 scored cells) |
| Single-name EODHD 2,169 symbols × 3.2M rows | S0 window | STOCKS-NG6 (D2 R0 veto all; 0 cells) |
| SPY daily | 2015-2026 frozen snapshot | PHASE-STRATEGY-V1, JEV-REGIME-ROUTER-V2 (18/18), REGIME-STRATEGY-MAPPING-V1 (45/27) |
| SEC FTD/N-PORT/Form-4 | as staged | DEU-V1 Lane S / SNG6 (censuses + PIT measurements — read, no outcomes) |

### Vol / commodities
| Data | Window | Consumed by |
|---|---|---|
| CBOE VIX/VIX9D/VIX3M/VIX6M term structure (15.69y, 2,940 instants) + EODHD vol ETP legs (incl. delisted TVIX/ZIV) | 1990..2026 staging window | VOL-NG1 (6/6 scored cells — exposed) |
| CFTC CoT positioning (deacot2016..2026) + EODHD commodity ETPs (20 market-pairs) | 2016..2026 archives | COMMODITIES-NG1 (3/3 scored cells — exposed); FOREX-NG5 (FX-plane CoT census; 0 cells) |

**Exposed-window count (table rows above): 30 instrument×window×cycle
families, of which 21 rows carry actual scored/exploratory outcome
exposure and 9 are read-for-falsifier/D2/census rows (read, 0 scored
outcomes).** Per-cell denominators behind these rows (P-9 authority):
program 400+/403+ published/observed logical cells, 0 survivors, S1 never
opened.

## (b) UNOPENED confirmation data

| Unopened asset | Seal evidence (metadata only — contents never read) |
|---|---|
| **S1 — sealed everywhere** (all asset planes) | Every ledger/MAP row carries "S1 SEALED / SEALED_UNTOUCHED"; plan §2: "S1 SEALED everywhere"; opening requires owner authorization (plan §1 non-goals) |
| **ERP1 sealed 2026-H1 AUDUSD + USDCAD holdouts** | ERP1-TRACKA-COHORT-1 ledger row: "holdout 2026-H1 both pairs UNREAD"; COHORT-2 row: "sealed holdouts 2026-H1 AUDUSD+USDCAD UNREAD (program assets)". This lane read NO holdout file content; existence/paths only via ledger+MAP text |
| **Post-2026-09 prospective collector streams** (Coinbase/Kraken Futures/Deribit shards from 2026-09-17; LIVE-DATA-GATEWAY-V1 worker stream; PROSPECTIVE-SHADOW-V1 surfaces) | DEU Lane C contract: "WebSocket data is prospective-only from collector start and can NEVER backfill history"; CRYPTO-NG4 collector run window 2026-09-16→2026-09-17 stopped cleanly at close (workers=0); plan §2: active cycles' data dirs untouchable in write mode; F5: metadata-only census for live-owned data |
| **All future windows** (every instrument, post-2026-09) | The candidate-verification doors on record: FX2-RANGEEXP-C3/C4 and GBPUSD RANGEEXP-C3/C4 are "pending PROSPECTIVE verification" (MAP) — their verification windows must OPEN FORWARD ONLY |
| **BNBUSDT plane** (PWS pair-child #2, lawful but not yet read; PWS-CX-BNBUSDT-C1 was ACTIVE_LIGHT at DFV1 intake with GO-1 in flight) | MAP SOLUSDT terminal note: "pair-child #2 (BNBUSDT) remains lawful under the approved order"; F5 racing-read rule honored — no BNB data read this cycle |

**Unopened count: 5 classes (S1-everywhere; ERP1 2026-H1 holdouts;
post-2026-09 prospective streams; all future windows; BNBUSDT pre-read
plane).**

## (c) The separation RULE (normative)

1. **Every dataset/window in the inventory carries
   `outcome_exposure` ∈ {OUTCOME_EXPOSED, UNOPENED, MIXED, NOT_APPLICABLE}**
   (authority_row_schema.json). Mixed corpora (e.g. BTC panels where
   2020–2026-08 dev is exposed but 2026-09+ is prospective) are MIXED with
   the boundary stamped per corpus.
2. **UNOPENED windows are readable only by a future owner-authorized
   confirmation plan.** No lane, cycle, shadow, or audit reads them for any
   exploratory purpose; A7 reproduction may recount committed artifact
   bytes about them (verdicts, digests) but never open the content.
3. **Prospective collectors must not be replayed into research.** A
   prospective stream (WS collector shards, live gateway) feeds only
   forward-verification/paper surfaces; replaying it into dev/falsifier
   computation converts confirmation data into exposed data and destroys
   its confirmatory weight (the ERP1/S1 doctrine generalized: P-5's
   "remediation conserved S1" precedent).
4. **Exposed history carries confirmation weight 0** (standing
   OUTCOME_EXPOSED_ANCESTRY law, ILLIQ-REG-V1 row): a new candidate may
   inherit the data, never the verdict.
5. **Boundary discipline for MIXED corpora:** a scored or exploratory read
   that crosses a stamped boundary even once reclassifies the corpus and is
   an incident (the SRLV/PSV1 "holdout unread" rows are the compliance
   pattern: 0 holdout looks is an auditable property).
