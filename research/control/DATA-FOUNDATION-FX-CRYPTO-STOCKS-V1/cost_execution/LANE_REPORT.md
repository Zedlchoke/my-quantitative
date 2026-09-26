# LANE REPORT — L-COST (dfv1-lane-cost), cycle DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1

Scope executed per `PACKET_lane_cost.md`: consolidation of every cost/execution
authority artifact in the authorized evidence space into one COST_AUTHORITY
table (census #4), inventory rows for the measured-cost datasets, and the
IBKR/TWS presence check. ZERO network requests, zero credentials, zero
gateway connections, no sealed/holdout content read. Read-only everywhere
except `cost_execution/` in this worktree.

## 1. What was consolidated (with verification)

| Input | Artifact | Verification this cycle |
|---|---|---|
| Census #3 (DEU-V1 Lane F ten-component dossier) | `.worktrees/data-edge-unlock-v1/lane-f/research/control/data_edge_unlock_v1/lane_f/f_cost_authority_dossier.json` | read in full; verdict BLOCKED_BROKER_COST_AUTHORITY; stress 2.0 FROZEN |
| FOREX-NG6 P0-F4 | `git show orca/forex-ng6-integration:.../p0_census_verdict.json` | sha256 **matches pin** 7fbb6347…a4a8a5; all 7 cost components `measurable_from_td=false` |
| FOREX-NG7 F4 terminal | `git show orca/forex-ng7-integration:.../terminal_verdict_forex_ng7.json` | sha256 **matches pin** be73305f…2828c2; no citable financing band; reopening = owner broker-grade cost authority |
| IBKR TWS SIM probe (census #4's new measured leg) | `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/broker_cost_probe_FX_majors_2026-09/{VERDICT_session2.md, EVIDENCE_sanitized_2026-09-26.json}` | sha 8cd019f7… / 178d10f0… measured this cycle; minTick 0.5 pip ×5 pairs MEASURED account-bound; two-sided quotes NOT_SUBSCRIBED; commission/swap NOT_RUN |
| ERP1 measured cost floors | `tracka_cohort2/COSTAUDIT_cohort2_REPORT.md` + `COSTAUDIT_F5_cohort2_REPORT.md` (+ VIABILITY_cohort3) | sha 0188b793… / e1c3f6ac…; stressed RT **3.6 (AUDUSD) / 4.4 (USDCAD) pips** last-6m conditional; P3-A threshold 0.41 @k=2.0 vs measured 0.9–1.0 (p25 0.8) → CEILING_NEGATIVE_VETO |
| FX spread censuses | `census_AUDUSD.json` / `census_USDCAD.json` (sha pins **re-measured, byte-identical** d337ff2c… / 27958f5a…) + `DATACOST_cohort1_REPORT.md` (EURUSD 0.3 / GBPUSD 0.8 / USDJPY 0.5 pips) | SAMPLED |
| Crypto measured books | BTC funding 11.798%/yr (`feasibility_census.json`, sha ee2c0364… re-measured); SRLV `DATACOST_FEASIBILITY_MATRIX.md` (fees 5 bps + 1 tick DECLARED; ETH 7,305 settlements; 24.7% negative settlements in downtrend); SOL spread census p50 **0.469 bps** n=13.8M; BNB n=7,261 PASS-WITH-CAVEATS (live owner, metadata-only); LDGW amendment 11.5 calls/min live-verified + canary median ~1 bps (live owner, metadata-only) | SAMPLED / INHERITED_NOT_REHASHED_LIVE_OWNER |
| Stocks laws | `research/wayfinder/LESSONS.md` Q-2 (conditional-cost law: spread priced off the volatility you want) + L-SAMV1-3 (X1/X2 fill-feasibility: volume=0 bars unfillable) + plan §3 (EODHD entitlement; FINRA terminal) | read |
| Prior probes | `forex_mt5_cost_probe_2026-09/` (contract + read-only collector audited AUTHORIZED_WITH_FINDINGS; **no collected bytes anywhere → NOT_RUN**) and `xauusd_ibkr_probe_2026-09/` (tick 0.01 measured vs stated 0.001 — 10x discrepancy, measured wins; checklist sha **matches Lane F pin** 03da7061…; probe PAUSED at NOT_RUN_TWS_UNAVAILABLE) | SAMPLED |
| Environment | `/Users/hoangminhlong/Jts/` + `/Users/hoangminhlong/ntws/` | `ls` only — see §2 |

## 2. IBKR / TWS presence finding

Both estates EXIST (names/mtimes only; no file content read):

- `/Users/hoangminhlong/Jts/` — the live TWS estate. Extension dir contains
  `tws.20260926.105853.ibgzenc` and `audit.20260926.105906.ibgzenc` —
  **TWS executed today (2026-09-26 ~10:58)**; `launcher.log` mtime 21:40
  today. `jts.ini` present.
- `/Users/hoangminhlong/ntws/` — a second TWS install (`jts.ini`,
  extension dir with `tws.20260916.135943.ibgzenc`, `Settings/`), last used
  2026-09-16.

**Meaning for the runbook:** "owner starts TWS" is one click away — the
installation and today's runtime are proven. Combined with the probe
verdicts: socket 7497 + Read-Only API are ALREADY proven working
(server-side Read-Only confirmed by 321 rejections on order reads, 2026-09-26).
The gates are NOT installation: (a) the SIM account's two-sided FX market
data is NOT_SUBSCRIBED (bid/ask = −1), (b) no Activity/Flex statement has
ever been exported.

**What a Read-Only API session unlocks (exact mapping):**
1. Two-sided `reqMktData` → spread distribution (component 1) — ONLY after
   the owner enables free FX delayed in "Manage Data Subscriptions";
   otherwise it returns −1 (already measured, twice, 720 s).
2. `contractDetails` → tick (DONE, 0.5 pip ×5) and minSize (returns null on
   CASH — the statement is the real source for component 3).
3. Activity/Flex export (the decisive document): Trade+Commission rows →
   commission (2); Interest Accruals per FX position → swap LONG/SHORT (3/4,
   the binding PASS-minimum); dated Wednesday 3× rows → triple-swap (5);
   accrual timestamps + statement timezone → rollover clock (6); fills →
   slippage report-only (8); Account Summary InitMargin/MaintMargin →
   margin (7, REPORT-ONLY; whatIf stays forbidden).
4. One TWS restart before re-probing (measured failure mode: API
   session-slot exhaustion after ~20 probe connections).

## 3. What the ERP1 3.6/4.4-pip floor means for data-acquisition priority

The floor is the sharpest prioritization signal the program owns:

- **Cost authority outranks new price history for FX.** The floor says the
  profit space between an honest measured premium and the ×2.0 stressed RT
  (3.6 AUDUSD / 4.4 USDCAD pips; ~7–9 pips for the ~2× non-fragile line) is
  EMPTY in all 38 recorded forex failures — small-band classes die buried
  under cost, large-band classes die of ancestry/expectancy. More vendor
  OHLC/bid-ask history does NOT move this floor; **account-bound swap,
  commission and rollover bytes do** (they can move the floor itself).
- **Spread-census data is already sufficient; financing data is the
  missing trunk.** The vendor book is censused on 5 pairs (p50 0.3–1.2
  pips) and the F-5 machinery converts any declared band into a verdict
  pre-PnL. The single blocker that killed FOREX-NG6/NG7 and the carry class
  is financing authority (components 3/4/5/6). Acquisition priority is
  therefore: statement export > market-data subscription > any new corpus.
- **P3-A shows venue geometry can close doors permanently.** The measured
  IBKR tick (0.5 pip) makes the 0.41-pip threshold arithmetically
  unattainable at IDEALPRO regardless of any future spread data — future
  sub-tick mechanisms must pick venues by measured tick geometry FIRST.
- **Crypto is the measured frontier.** It is the only asset with measured
  per-settlement carry (BTC 11.798%/yr vs 1.508% constant — 7.8×
  underestimation) and a measured spread census (SOL p50 0.469 bps ≪ 5 bps
  declared fee, i.e. FEE-dominated, so the fee tier and fills — not spread
  archives — are the open crypto cost questions).

## 4. Cheapest single owner action per asset

| Asset | Cheapest action | Unlocks |
|---|---|---|
| FX majors | Export ONE Activity/Flex statement (any IBKR account, window with FX trades + overnight positions; machine-local raw, sanitized extracts into git) + enable free FX delayed market data; TWS restart; then the frozen one-command probe | components 2/3/5/6/7/8 measured; broker PASS-minimum becomes attainable; FOREX-NG7 reopening condition satisfiable |
| XAUUSD | Resume preregistered probe when TWS API is up (new preregistered handshake diagnosis required; templates frozen) | spread distribution; margin lines; upgrades STATED fee schedule |
| Crypto | Nothing owner-gated. Keyless remainders (BTC/ETH/BNB spread census, exchangeInfo filters, BNB Vision cross-check) belong to the cycles owning those corpora | closes the last crypto cost-book caveats |
| Stocks | Only lawful path is an owner broker-statement export (commission schedule + fills) IF an equities account exists; else stocks stay BLOCKED_ACCOUNT and equities designs stay restricted to illiquidity-proxy + X1/X2 law (FINRA alternative is terminal) | a real equities cost book (none exists today) |

## 5. Status summary

- Deliverables: `cost_authority_table.json` (assets × 10 components +
  FROZEN extras, every number artifact-cited),
  `COST_AUTHORITY_TABLE.md`, `inventory_rows.jsonl` (12 §5 rows: 6
  AVAILABLE_VALIDATED, 4 AVAILABLE_UNVALIDATED [3 of which are
  live-owner INHERITED_NOT_REHASHED metadata-only + 1 un-re-hashed
  inherited corpus], 1 BLOCKED_ACCOUNT, 1 NOT_RUN), this report, handoff.
- Inventory `AVAILABLE_VALIDATED` basis: sha256 re-measured THIS cycle on
  the census/report artifacts (6 files), byte-identical to their prior
  pins; coverage fields are census-declared, not re-derived from raw
  corpora (stated explicitly in each row's status_evidence). No status was
  inferred; every gap is named.

## 6. Known limitations

1. Lane is consolidation-only: no corpus re-hash beyond the small cited
   artifacts (hashing budget rule); no coverage re-census from raw bytes —
   the VALIDATED rows certify artifact integrity + inherited coverage, not
   fresh byte-level coverage censuses (that belongs to A7 F11 / integration).
2. `USDJPY`/`GBPUSD`/`EURUSD` census artifacts were cited from the committed
   DATACOST report without re-hashing their corpora (marked
   AVAILABLE_UNVALIDATED).
3. LDGW "11.5 calls/min" and canary medians are cited from the registry row
   and G1 evidence (live owner; metadata-only per §14 F5) — not re-measured.
4. The MT5 probe's collected-data absence is stated from a directory-level
   search of the authorized evidence space; a dataset outside that space
   would be invisible to this lane by design.
5. Evidence classes are never upgraded: XAUUSD "MEASURED" spread is a
   SINGLE_SAMPLE connectivity proof; crypto fees stay DECLARED (Q-8) until
   fills exist; PAPER_TIER labels carried from owning cycles.

## 7. Incidents

None. Zero network requests were made; no lock contention (light reads
only); no boundary touched. First substantive read chunk ran under
`/usr/bin/time` (0.00s CPU, ~1 MB RSS — far under abort thresholds).
