# GATE_TABLE_7ASSETS — IBKR capability probe 2026-09-30, per-asset gates

Author: Lane DV (data verification), cycle PORTFOLIO-COMPOSITE-12ASSETS-100K-V1
(UNREGISTERED draft — analysis document only; no eligibility, registry, or GO
write). Every numeric claim below was independently recomputed by DV from the
131 raw files in `~/.my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930/`
(`DV_VERIFICATION_EVIDENCE.json`, same directory). All reported daily-span,
spread and XAU-overlap numbers reproduce exactly.

Gate labels: `PASS` / `FAIL` / `NOT_RUN_*` (missing evidence is NOT_RUN,
never inferred PASS — mission invariant).

## Verification summary that this table rests on

| check | result |
|---|---|
| 131/131 raw files re-hashed; 131 sha256 citations with file paths across ACQUISITION_REPORT.json + ADDENDUM_CONTFUT_6Y.json | 0 mismatches |
| ADDENDUM_FUTURES_RETRY.json citations | 9 sha256 (front FUT trades_1y / bid_5d / ask_5d × 3 assets) + 3 un-hashed contfut_history rows have **NO raw file landed** → those numbers are NOT reproducible from the raw dir (finding F-3) |
| Daily coverage (n_days/first/last/holes) for 4 spot/metals, both sides | reproduces exactly; max calendar gap 4d on all 8 side-panels |
| Daily spread p50/p90/max bps for 4 assets | reproduces exactly (XAUUSD n=1543 vs 1544 days explained: 2025-05-23 crossed book, BID close 3361.0 > ASK close 3359.78, correctly filtered by the a≥b rule) |
| XAU overlap vs TD archive | archive sha `49c2684e…` verified; 1531 aligned, abs p50 3.2462 / p95 26.5142 bps, signed mean +0.3359 USD — all reproduce exactly. Overlap ends 2026-09-16 because the TD archive ends there |
| Erratum checksum chain | PROBE_RESULT.json `c90dc665…`, FOLLOWUP_EXPIRED_ROLL.json `6ddce3b5…` re-hashed byte-identical (matches A1) |
| CONTFUT 6Y series | n/first/last/holes reproduce (1549/1526/1526; 2020-10-01→2026-09-30; 0 holes >5d) **BUT** 63%/61%/41% of bars (BRENT/WTI/NATGAS) are flat-OHLC zero-volume synthetic bars — 100% of 2020–2022 bars, 0% from 2025 — see F-1 below |

DV findings (do not smooth):
- **F-1 CONTFUT synthetic majority.** The `span_gate: PASS` in
  ADDENDUM_CONTFUT_6Y.json is arithmetically true over a series whose
  pre-2025 majority is close-only backfill (open=high=low=close, volume 0:
  BRENT 977/1549 bars flat; WTI 932/1526; NATGAS 633/1526). It is not
  traded-price evidence for anything intrabar, and it is not a roll chain.
- **F-2 XAU archive location.** `XAUUSD_1day_full.json` exists ONLY at the
  forex-ng6 worktree path hardcoded in `acquire_bounded.py`
  (`.worktrees/forex-ng6/integration/.../p0/staging/`); it is NOT under
  `research/control/DATA-FOUNDATION-SIXSOURCE-V1/` in the root checkout.
  The sha matches, but the frozen archive's canonical location should be
  pinned by the owner before gate-2 use.
- **F-3 Retry history not landed.** ADDENDUM_FUTURES_RETRY.json reports
  front-FUT 1Y TRADES (n=258/251/251) and 5-day BID/ASK with sha256 but no
  raw file exists for them anywhere in `ibkr_acq_20260930/` (131 files all
  otherwise accounted for). Treat those rows as REPORT_ONLY until re-pulled.
- **F-4 Identity fields are report-only.** conId/symbol/minTick/timeZoneId
  come from the live session; they cannot be re-derived from raw bars. They
  are frozen as-reported in IDENTITY_FREEZE_2026-09-30.json.

Gate key (per plan §2 admission law): **span** (history reaches the cohort
window), **interior gaps**, **M1** (full minute corpus), **roll rule**,
**chain** (certified tradable roll chain), **entitlement** (quotes),
**costs** (spread measured + commission/swap/slippage), **PIT**
(point-in-time provability). "n/a" = not applicable to the vehicle class.

## NZDUSD — FX spot (CASH)

- **Vehicle needed by our legs:** `FX-spot` (100/100 census rows). Referenced
  as cross-asset input by 5 triage rows (AUDUSD-S081 AUDNZD band needs the
  NZDUSD execution leg; EURUSD-S006/S061/S085 7-pair anti-USD baskets;
  USDJPY-S083 6-cross JPY basket) — all DAILY-clock rules.
- **Identity (as reported):** conId 39453441, NZD.USD, CASH, IDEALPRO, USD,
  minTick 5e-05, US/Eastern.
- **Probe delivered:** D1 BID+ASK 2020-10-02→2026-09-30, 1553 days/side,
  0 holes >5d (max gap 4d); spread p50 0.88 / p90 18.65 / max 239.07 bps;
  3 M1 sample days + 6 March H1 windows (non-empty, partial sessions).

| gate | status | evidence |
|---|---|---|
| span (daily) | **PASS** | 1553 d/side, first 2020-10-02 ≤ 2021-01-08, last 2026-09-30 ≥ 2026-09-26 — DV-verified |
| interior gaps | **PASS at daily clock** (0 holes >5 cal-days over the full span); intraday interior **NOT_RUN_INTERIOR_GAPS** | full-session intraday scan never run (erratum; M1/H1 are samples) |
| M1 | **NOT_RUN_SIZE_CAP** (samples PASS non-empty only; later windows are 2–6h slices, not sessions) | addendum session notes |
| roll rule / chain | n/a (spot) | — |
| entitlement | historical HMDS **PASS by evidence** (bars returned); live/delayed quote snapshot **NOT_RUN** | no reqMktData on spot legs |
| costs | **NOT_RUN** — spread measured (p50 0.88 bps), commission/swap/slippage unmeasured | no Activity/Flex statement |
| PIT | **NOT_RUN** — no cross-source overlap measured for NZDUSD | — |

- **Single named action per blocker:** costs → owner exports IBKR
  Activity/Flex statement (FX trades + Interest Accruals) to
  `~/.my-quantitative-data/ibkr_statement/` (P_A; one export also covers
  USDCHF/XAUUSD/XAGUSD). PIT → owner declares the panel-of-record and its
  availability lag (IBKR HMDS next-business-day, or measure vs an
  independent archive) — one decision.
- **Plan amendment needed: YES** — see footer.

## USDCHF — FX spot (CASH)

- **Vehicle needed:** `FX-spot` (100/100 census rows). Referenced by 4
  triage rows (EURUSD-S006/S061/S085 baskets; USDJPY-S083 JPY crosses) and
  1 more that stays blocked on news inputs (EURUSD-S082).
- **Identity (as reported):** conId 12087820, USD.CHF, CASH, IDEALPRO, CHF,
  minTick 5e-05, US/Eastern.
- **Probe delivered:** D1 BID+ASK 2020-10-02→2026-09-30, 1553 days/side,
  0 holes; spread p50 4.51 / p90 16.02 / max 216.10 bps; M1/H1 samples.

| gate | status |
|---|---|
| span (daily) | **PASS** (1553 d/side — DV-verified) |
| interior gaps | PASS at daily clock / intraday **NOT_RUN_INTERIOR_GAPS** |
| M1 | **NOT_RUN_SIZE_CAP** (samples partial sessions) |
| roll / chain | n/a |
| entitlement | historical PASS-by-evidence; live/delayed **NOT_RUN** |
| costs | **NOT_RUN** (spread measured; no statement) |
| PIT | **NOT_RUN** |

- **Actions:** identical to NZDUSD (same statement export; same PIT
  declaration).
- **Plan amendment needed: YES.**

## XAUUSD — spot gold (CMDTY)

- **Vehicle needed:** `metals-spot-TBC` (100/100 census rows; 90 ladder rows
  sit in BLOCKED_VENUE_UNEVIDENCED). The probe converts the venue TBC into
  pinned evidence: IBKR CMDTY XAUUSD SMART USD (London Gold), minTick 0.01 —
  usable as the executable-venue exhibit in a future amendment, NOT an
  eligibility change today.
- **Identity (as reported):** conId 69067924, XAUUSD, CMDTY, SMART, USD,
  minTick 0.01, US/Eastern.
- **Probe delivered:** D1 BID+ASK 2020-10-02→2026-09-30, 1544 days/side,
  0 holes; spread p50 5.52 / p90 18.61 / max 74.17 bps (n=1543; one crossed
  book 2025-05-23); XAU overlap vs TD archive 1531 days, abs basis p50
  3.2462 / p95 26.5142 bps, signed mean +0.3359 USD.
- **Corpus legs that would use it:** AUDUSD-S100 (crisis-alpha tail switch:
  VIX + gold + AUDUSD D1 — VIX and spot already evidenced) and USDJPY-S063
  (gold–JPY safe-haven: gold + VIX D1) — both DAILY-clock.

| gate | status |
|---|---|
| span (daily) | **PASS** (1544 d/side — DV-verified) |
| interior gaps | PASS at daily clock / intraday **NOT_RUN_INTERIOR_GAPS** |
| M1 | **NOT_RUN_SIZE_CAP** (samples partial sessions) |
| roll / chain | n/a |
| entitlement | historical PASS-by-evidence; live/delayed **NOT_RUN** |
| costs | **NOT_RUN** (spread measured; no statement) |
| PIT | **MEASURED-BUT-UNFROZEN**: overlap 1531 d, abs p50 3.25/p95 26.51 bps; `pit_lag = ASSUMED_NEXT_BUSINESS_DAY`, `pit_status = NOT_MEASURED`, `basis_acceptance = NOT_RUN_THRESHOLDS_UNFROZEN` |

- **Single named action per blocker:** costs → same Activity/Flex statement
  export (P_A). PIT → owner freezes the numeric basis-acceptance thresholds
  in `research/control/xauusd_ibkr_probe_2026-09/td_archive_join_contract.json`
  (currently unfrozen) and either accepts the assumed next-business-day lag
  or funds a publish-timestamp measurement — one decision + one threshold
  freeze. Venue → no further data action; identity is now evidenced (F-4
  caveat: as-reported).
- **Plan amendment needed: YES.**

## XAGUSD — spot silver (CMDTY)

- **Vehicle needed:** `metals-spot-TBC` (100/100 census rows). **No triage
  row needs only XAGUSD**: the one silver-adjacent row (EURUSD-S068) names
  HG copper as the input and explicitly flags the XAG proxy as unverified by
  its source — the probe does not clear it.
- **Identity (as reported):** conId 77124483, XAGUSD, CMDTY, SMART, USD,
  minTick 0.0005, US/Eastern.
- **Probe delivered:** D1 BID+ASK 2020-10-02→2026-09-30, 1544 days/side,
  0 holes; spread p50 10.35 / p90 40.83 / max 162.81 bps (widest p50 of the
  four — cost-gate relevant for any future silver leg).

| gate | status |
|---|---|
| span (daily) | **PASS** (1544 d/side — DV-verified) |
| interior gaps | PASS at daily clock / intraday **NOT_RUN_INTERIOR_GAPS** |
| M1 | **NOT_RUN_SIZE_CAP** |
| roll / chain | n/a |
| entitlement | historical PASS-by-evidence; live/delayed **NOT_RUN** |
| costs | **NOT_RUN** (spread measured; no statement) |
| PIT | **NOT_RUN** (no independent XAG archive on file to overlap against) |

- **Single named action per blocker:** costs → same statement export. PIT →
  owner names an independent XAG daily archive (or declares IBKR HMDS the
  panel of record with next-business-day availability) — one decision.
- **Plan amendment needed: YES** (identity frozen for future cohorts even
  though no current leg consumes it).

## BRENT — ICE Brent outright futures (FUT COIL IPE)

- **Vehicle needed:** `energy-futures/CFD-TBC` (100/100 census rows). Frozen
  pre-declaration (erratum): ICE Brent outright, symbol COIL, exchange IPE;
  BZ (Last-Day) is the unselected alternate; BRN/IPE returned error 200; CFD
  is not a candidate. The 5-pair corpus legs that cite "Brent daily close
  (G-PIT-V3)" use the existing PIT dossier archive, NOT this probe.
- **Probe delivered:** front contract resolved (COILX6, conId 361002948,
  lastTrade 2026-09-30 19:30 GB); CONTFUT identified (conId 361002955,
  COILZ6, ≠ front). Expired FUT quarters 202103–202506 all error 200 (oldest
  resolved months: 202511/202512/202601). CONTFUT 6Y daily TRADES 1549 bars
  2020-10-01→2026-09-30, 0 holes — but 63% flat-OHLC zero-volume synthetic
  (F-1). Live quote error 354 (+10372 date-format noise); delayed no quote.
  Retry front-FUT 1Y TRADES / 5d BID/ASK numbers exist only in the addendum
  (F-3).

| gate | status |
|---|---|
| span (chain) | **FAIL** — no certified chain reaches 2021; CONTFUT span PASS is over a synthetic-majority series (F-1) |
| interior gaps | **NOT_RUN_INTERIOR_GAPS** |
| M1 | **NOT_RUN** (not requested) |
| roll rule | **FAIL** — adjustment method not in contract details; CONTFUT localSymbol is one month |
| chain | **FAIL** — expired FUT unreachable (error 200); CONTFUT ≠ tradable FUT chain |
| entitlement | **FAIL** — live 354 not subscribed; delayed NO_QUOTE |
| costs | **NOT_RUN** — no Activity/Flex statement |
| PIT | **FAIL/NOT_RUN** — no PIT source exists for a chain that does not exist |

- **Single named action per blocker:**
  - chain/span/roll (one decision): owner names the certified roll-chain
    data source — IBKR's API cannot list expired FUT (error 200), so either
    a licensed vendor/ICE-direct back-adjusted series with a documented roll
    + adjustment rule, or an owner-accepted CONTFUT convention with the
    synthetic-bar disclosure (F-1) — this single source decision clears all
    three gates' evidence path.
  - entitlement: owner enables the ICE (IPE) market-data subscription (or
    delayed data) on the paper account — one subscription toggle.
  - costs: same Activity/Flex statement export as the FX legs (one export).
- **Plan amendment needed: YES — and NOT available now.** Unlike the
  spot/metals, no honest amendment scope exists until the chain source is
  named; futures columns stay BLOCKED (FLAT-by-authority).

## WTI — NYMEX crude futures (FUT CL NYMEX)

- **Vehicle needed:** `energy-futures/CFD-TBC` (100/100 census rows).
  Triage rows needing the futures side: USDCAD-S005 (CL1–CL6 curve),
  USDCAD-S062 + S081 (short-WTI execution legs), USDCAD-S089 (S62 overlay),
  USDCAD-S098 (6M slope), USDCAD-S090 (NATGAS+WTI). Signal-only WTI daily
  close rows (USDCAD-S001/S008/S013/S017/S063) already run on the G-PIT-V3
  archive and are unaffected by this probe.
- **Probe delivered (after the socket-drop FAIL in ACQUISITION_REPORT was
  superseded by the retry):** front CLX6 conId 304037511 (lastTrade
  20261020); CONTFUT echoes the SAME conId with single-month localSymbol
  (erratum table) — proof it is not a chain; months 202510/202511 resolve;
  CONTFUT 6Y 1526 bars, 0 holes, 61% flat synthetic; live entitlement error
  10168 (delayed not enabled); delayed type3 no positive quote.

| gate | status |
|---|---|
| span (chain) | **FAIL** (same basis as BRENT; F-1) |
| interior gaps | **NOT_RUN_INTERIOR_GAPS** |
| M1 | **NOT_RUN** |
| roll rule | **FAIL** |
| chain | **FAIL** (CONTFUT = front conId echo, single month) |
| entitlement | **FAIL** (10168 / no delayed quote) |
| costs | **NOT_RUN** |
| PIT | **FAIL/NOT_RUN** |

- **Single named actions:** chain source decision (as BRENT, NYMEX flavor);
  NYMEX market-data (or delayed) subscription; Activity/Flex statement.
- **Plan amendment needed: YES — not available now** (BLOCKED).

## NATGAS — Henry Hub futures (FUT NG NYMEX)

- **Vehicle needed:** `energy-futures/CFD-TBC` (100/100 census rows; the
  weather-gated ideas S001/S024/S058/S074/S094 in the 1,200 ladder stay
  BLOCKED_NO_PRICE_DATA). Triage rows: USDCAD-S065 (NATGAS + AECO),
  USDJPY-S065 (NATGAS+Brent), USDCAD-S090 (NATGAS/WTI ratio), EURUSD-S063
  (Henry Hub + TTF).
- **Probe delivered:** front NGX26 conId 269460170 (lastTrade 20261028);
  CONTFUT same conId echo; months 202510/202511 resolve; CONTFUT 6Y 1526
  bars 2020-10-01→2026-09-30, 0 holes, 41% flat synthetic; live 354;
  delayed 10167 then no positive quote; roll FAIL; costs NOT_RUN.

| gate | status |
|---|---|
| span (chain) | **FAIL** (F-1 caveat applies) |
| interior gaps | **NOT_RUN_INTERIOR_GAPS** |
| M1 | **NOT_RUN** |
| roll rule | **FAIL** |
| chain | **FAIL** |
| entitlement | **FAIL** |
| costs | **NOT_RUN** |
| PIT | **FAIL/NOT_RUN** |

- **Single named actions:** chain source decision (NYMEX NG); NYMEX
  subscription; Activity/Flex statement. **Extra honesty item:** AECO
  (USDCAD-S065) and TTF (EURUSD-S063) are not IBKR-traded instruments at
  all — those two rows additionally need an owner-named gas-hub price
  source; an IBKR chain alone can never clear them.
- **Plan amendment needed: YES — not available now** (BLOCKED).

## Amendment footer (all 7 assets)

Adding any of these assets to the cycle needs a **plan amendment** — plan §2:
"blocked columns activate ONLY via their named owner unblock + PIT/cost
gates, as plan amendments." Nothing in the probe is an eligibility change.

**Exact scope available today (spot/metals only):**
> Admit a **daily-clock (D1 BID/ASK) cohort on the 4 spot/metals pairs
> NZDUSD, USDCHF, XAUUSD, XAGUSD** for daily-horizon cross-asset rules only,
> identity per `data_freeze/IDENTITY_FREEZE_2026-09-30.json`, spreads
> measured (p50/p90 above), PIT and costs still gated (statement export +
> threshold freeze), **H1/M1 legs remain NOT_RUN** (probe delivered samples
> only), **BRENT/WTI/NATGAS remain BLOCKED** pending a certified roll-chain
> source. Admission of any row still requires trial-ledger accounting per
> owner law.

The 7 triage rows this would make data-ready (still BLOCKED until amended)
are listed per asset in `LEG_RESOLUTION_MATRIX.md` class (b).
