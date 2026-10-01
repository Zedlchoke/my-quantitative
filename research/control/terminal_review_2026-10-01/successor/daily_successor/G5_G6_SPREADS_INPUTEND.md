# G5_G6_SPREADS_INPUTEND — daily-band spread derivation (G5) + AUD/CA D1 input completion (G6)

Preparation artifact for the DAILY successor registration gates G5/G6
(`PLAN_DAILY_SUCCESSOR_DRAFT.md` §0b ¶2 gate table). **Preparation only:
nothing registered, frozen, scored or executed.** Read-only everywhere
except this one file; `.venv/bin/python` used for arithmetic on frozen
raw files only; no network, no fetch, no engine run, no S1, no orders,
no ledger/registry write. Missing evidence is `NOT_RUN`, never inferred
`PASS`. Computed 2026-10-01.

---

## 1. G5 — DAILY-clock spread band derivation (MEASURED-DERIVED)

### 1.1 Input structure disclosure (the CHECK the dispatch ordered)

Raw source: the sha-pinned IBKR HMDS daily chunks at
`~/.my-quantitative-data/portfolio-composite-12assets-100k-v1/ibkr_acq_20260930/`
— 12 files per instrument (`<INST>_1d_{ASK,BID}_{2021..2026}0930.json`),
48 files total for NZDUSD/USDCHF/XAUUSD/XAGUSD.

**Measured JSON structure (checked on disk, not assumed):** each file is a
JSON **list of per-session rows** with fields
`{date, session_date, open, high, low, close, volume}` — i.e. the daily
chunks carry **full per-day OHLC, NOT close-only** (`volume = -1.0`
placeholder). Verified example `NZDUSD_1d_BID_20260930.json`: 258 rows,
2025-10-02 → 2026-09-30, OHLC present on every row.

**Consequence for the fill model:** the next-bar-open law
(FILL_ACCOUNTING_SPEC §1.3 adapted to D1 per plan §5) is implementable
**directly** — the next day's OPEN exists on both BID and ASK sides, so a
buy fills at `ASK_open(T+1) + slip`, a sell at `BID_open(T+1) − slip`, and
`spread_once = |quoted_side − mid_open(T+1)| = (ASK_open − BID_open)/2`
of the fill bar. **The "next-day CLOSE as open proxy" fallback is NOT
needed and is NOT proposed.** The derivation below therefore computes the
band from BOTH sides of the bar: the close-side spread (continuity with
the frozen probe stats) and the open-side spread (the quantity the daily
kernel actually charges at an open fill).

### 1.2 Provenance and integrity (re-measured today)

- All 48 daily chunks re-hashed against the per-file sha256 pins in
  `IDENTITY_FREEZE_2026-09-30.json` (probe
  `IBKR-BOUNDED-ACQ-2026-09-30`): **48/48 match, 0 mismatches** (this
  re-derives the DV_VERIFICATION_EVIDENCE 131/131 result for the daily
  subset).
- Panel assembly: per side, 6 chunks concatenated and deduplicated by
  `date` (chunk boundaries overlap by design; later chunk wins). Session
  counts reproduce the freeze exactly: NZDUSD 1553, USDCHF 1553 (both
  2020-10-02 → 2026-09-30); XAUUSD 1544, XAGUSD 1544 (2020-10-02 →
  2026-09-30).
- Aggregate pins (source ids for the band table): NZDUSD
  `c681402b03e58502fcb7a22d7d7b26ccefcccf5117b20fa2ec82e2689a9782ed`,
  USDCHF `7fbd3a80e64114c54a411c75adf24725fc9ef631433b341484e6dd40468d69c3`,
  XAUUSD `02445884c9b28f4a7385e6924ae1b8827d347c41d019f7d7c063c2d54e2c653f`,
  XAGUSD `492dfbc0803dca58831490d603034859a668e633bef369cc31cfeb0368207bb7`.

### 1.3 Definitions and quantile convention

- `spread_bps(field) = (ASK[field] − BID[field]) / mid[field] × 1e4`,
  `mid = (ASK[field]+BID[field])/2`, on days where both sides exist and
  **`ASK ≥ BID > 0`** (the crossed-book filter, §1.6).
- Quantile convention: **order statistic at index `floor(q·(n−1))`**
  ("lower"). With this convention **all 8 probe cross-check numbers and
  all 4 probe maxima reproduce EXACTLY to 4 decimals from the raw chunks**
  (§1.4) — the convention is therefore pinned as the frozen one.

### 1.4 Cross-check vs the probe's frozen `spread_daily` — VERIFIED

| instrument | probe p50/p90 (bps) | recomputed p50/p90 (bps) | verdict |
|---|---|---|---|
| NZDUSD | 0.8822 / 18.6544 | 0.8822 / 18.6544 | **exact** |
| USDCHF | 4.5124 / 16.0242 | 4.5124 / 16.0242 | **exact** |
| XAUUSD | 5.5163 / 18.6133 | 5.5163 / 18.6133 | **exact** |
| XAGUSD | 10.3526 / 40.8256 | 10.3526 / 40.8256 | **exact** |

Probe maxima also exact: NZD 239.0719 / CHF 216.096 / XAU 74.1656 / XAG
162.8053; XAU n=1543 (1 crossed-book exclusion) reproduces. **The probe's
spread_daily stats are CONFIRMED, not refuted.** (Linear-interpolation
quantiles would read p90 higher by ≤0.07 bps — immaterial, and not the
frozen convention.)

### 1.5 The load-bearing new finding: OPEN-side daily band ≫ CLOSE-side band

The daily kernel fills at the **open** of the next D1 bar, so the
fill-facing band is the **open-side** quoted spread — which is
materially wider than the close-side numbers the probe froze:

| instrument | close p50 → open p50 (FULL, bps) | close p90 → open p90 (FULL, bps) |
|---|---|---|
| NZDUSD | 0.88 → 2.53 (2.9×) | 18.65 → 18.89 (1.0×) |
| USDCHF | 4.51 → 24.69 (5.5×) | 16.02 → 55.65 (3.5×) |
| XAUUSD | 5.52 → 38.44 (7.0×) | 18.61 → 167.43 (9.0×) |
| XAGUSD | 10.35 → 83.17 (8.0×) | 40.83 → 523.99 (12.8×) |

**Structure disclosure (honest limit of the derivation):** in IBKR HMDS
daily bars each side's `open` is that side's **own first quote of the
session** — the two sides' opens are asynchronous first prints, not one
contemporaneous book snapshot. Tail days make this visible (raw rows
re-read and verified): XAUUSD 2026-05-04 `BID_open 4158.11` vs
`ASK_open 5071.85` (1979.9 bps; both sides then converge to
close-spread 5.4 bps); NZDUSD 2025-03-03 `ASK_open 0.58345` vs
`BID_open 0.55975` (414.6 bps); XAGUSD 2026-03-09 open spread 2454.2
bps vs 2.3 bps at close; USDCHF 2025-04-08 open 642.4 vs close 28.3
bps. The same critique applies in miniature to the close side (last
quote per side), which is why close-side tails also exist (NZD
2022-10-12 close spread 239.07 bps = the frozen max).

**Accounting consequence, stated exactly:** this is NOT a double charge —
since the kernel literally fills at `ASK_open`/`BID_open` of the fill
bar, `spread_once = half the open-side spread` is exactly the bar-quoted
cost of that fill; the spread-once identity
`spread_once + slip_beyond_halfspread == |fill − mid_at_fill|`
(FILL_ACCOUNTING_SPEC §2) holds by construction. The open-side band is
however **pessimistic in the tail** because some recorded opens are
stale/asynchronous prints rather than an executable contemporaneous
market (a buy would fill at the stale-high ask). Two tail examples
(2025-12-31 / 2026-08-31 XAU > 1889 bps) sit INSIDE the fold calendar.
Worst-fill grading (spec §1.5: buys `max(ask_open, ask_close)`, sells
`min(bid_open, bid_close)`; `mid_at_fill` stays the open mid) routes any
excess into the slip/GAP-EXCESS line and does not alter the spread band
itself. **No filter beyond the crossed-book rule was applied** — trimming
stale opens would be a new rule and belongs to the owner at the
registration freeze, disclosed here as an open choice, not silently made.

### 1.6 Crossed-book filter (restated) and measured exclusions

Filter (frozen probe precedent, restated): a day enters the band iff both
sides exist and `ASK ≥ BID > 0` on the measured field. Measured
exclusions over 2020-10-02 → 2026-09-30:

- **CLOSE side:** XAUUSD **2025-05-23** only — the previously filtered
  crossed book: `BID_close 3361.0 > ASK_close 3359.78` (n 1544 → 1543;
  matches the freeze caveat verbatim). NZDUSD/USDCHF/XAGUSD: none.
- **OPEN side:** NZDUSD 2020-12-16 (1 tick: 0.7095/0.7096); XAGUSD
  2023-03-27 and 2025-01-30 (2 ticks each; both inside the fold window);
  USDCHF/XAUUSD: none.

If a crossed day is the would-be fill bar, the kernel still prices the
fill from the raw side quotes (the filter governs the BAND statistics
only); `UNAVAILABLE ≠ 0` fail-closed law unchanged.

### 1.7 The DECISION window restriction (OI-1 mapping)

OI-1 law (plan §0/§6-1): a decision at T+1 open consumes only closed bars
through T close (`available_time = next business day`); the fill happens
at the **T+1 bar open**. The band the cost kernel therefore consumes is
the distribution of **fill-bar (T+1) open-side spreads** over the
evaluation calendar. Windows derived (bars = potential fill bars):

- **FULL** 2020-10-02 → 2026-09-30 (probe-continuity, largest n);
- **EVAL** 2021-10-01 → 2026-09-24 (LEARN start → fold-8 end: every bar
  on which a LEARN-grid or exploratory-fold fill can occur);
- **FOLDS** 2022-09-30 → 2026-09-24 (the 8 exploratory folds only —
  where EXPLORATORY-battery fills land).

### 1.8 Frozen-READY band table (all bps, quantile convention 'lower')

Cell id scheme: `D1BAND-<INST>-<C|O>-<FULL|EVAL|FOLDS>` (C = close-side,
O = open-side). Source for every cell: the sha-pinned 12-file daily
aggregate for that instrument (§1.2 pins), recomputed from raw today;
probe-continuity column cites `IDENTITY_FREEZE_2026-09-30.json`.

**Fill-facing cells (OPEN side — what `spread_once` prices):**

| cell id | p50 | p90 | p95 | max | n days |
|---|---|---|---|---|---|
| D1BAND-NZDUSD-O-FOLDS | 2.6118 | 21.3272 | 32.7445 | 414.6256 | 1031 |
| D1BAND-NZDUSD-O-EVAL | 2.5790 | 20.1550 | 32.5256 | 414.6256 | 1291 |
| D1BAND-NZDUSD-O-FULL | 2.5268 | 18.8891 | 30.1971 | 414.6256 | 1552 |
| D1BAND-USDCHF-O-FOLDS | 27.1656 | 60.1794 | 74.3012 | 642.3908 | 1031 |
| D1BAND-USDCHF-O-EVAL | 26.1966 | 57.8974 | 71.9782 | 642.3908 | 1291 |
| D1BAND-USDCHF-O-FULL | 24.6858 | 55.6476 | 70.0525 | 642.3908 | 1553 |
| D1BAND-XAUUSD-O-FOLDS | 45.8149 | 168.5161 | 229.4216 | 1979.9436 | 1026 |
| D1BAND-XAUUSD-O-EVAL | 39.6615 | 178.8056 | 258.5901 | 1979.9436 | 1283 |
| D1BAND-XAUUSD-O-FULL | 38.4426 | 167.4323 | 242.4678 | 1979.9436 | 1544 |
| D1BAND-XAGUSD-O-FOLDS | 99.6954 | 519.7948 | 746.2894 | 2454.2424 | 1024 |
| D1BAND-XAGUSD-O-EVAL | 91.0865 | 536.4807 | 774.6032 | 2454.2424 | 1281 |
| D1BAND-XAGUSD-O-FULL | 83.1665 | 523.9870 | 766.8394 | 2454.2424 | 1542 |

**Validation / continuity cells (CLOSE side):**

| cell id | p50 | p90 | p95 | max | n days |
|---|---|---|---|---|---|
| D1BAND-NZDUSD-C-FULL (= probe spread_daily, verified §1.4) | 0.8822 | 18.6544 | 33.0409 | 239.0719 | 1553 |
| D1BAND-NZDUSD-C-EVAL | 0.8834 | 21.8526 | 34.8600 | 239.0719 | 1291 |
| D1BAND-NZDUSD-C-FOLDS | 0.8616 | 22.1107 | 37.8657 | 239.0719 | 1031 |
| D1BAND-USDCHF-C-FULL (= probe, verified) | 4.5124 | 16.0242 | 22.7266 | 216.0960 | 1553 |
| D1BAND-USDCHF-C-EVAL | 5.0810 | 17.0275 | 25.3951 | 216.0960 | 1291 |
| D1BAND-USDCHF-C-FOLDS | 5.0399 | 17.9392 | 26.9498 | 216.0960 | 1031 |
| D1BAND-XAUUSD-C-FULL (= probe, verified; 1 crossed-book exclusion) | 5.5163 | 18.6133 | 27.4684 | 74.1656 | 1543 |
| D1BAND-XAUUSD-C-EVAL | 5.8348 | 19.8004 | 28.0865 | 74.1656 | 1282 |
| D1BAND-XAUUSD-C-FOLDS | 6.8696 | 22.6451 | 29.7664 | 74.1656 | 1025 |
| D1BAND-XAGUSD-C-FULL (= probe, verified) | 10.3526 | 40.8256 | 73.8310 | 162.8053 | 1544 |
| D1BAND-XAGUSD-C-EVAL | 9.3699 | 48.4475 | 75.8573 | 162.8053 | 1283 |
| D1BAND-XAGUSD-C-FOLDS | 7.9051 | 53.9084 | 82.0345 | 162.8053 | 1026 |

Tail-day disclosure (largest open-side days, for the skeptic):
NZD 2025-03-03 414.6 / 2025-06-23 216.4 / 2022-11-07 141.5; CHF
2025-04-08 642.4 / 2023-05-01 434.9 / 2024-12-13 206.3; XAU 2026-05-04
1979.9 / 2025-12-31 1974.0 / 2026-08-31 1889.8; XAG 2026-03-09 2454.2 /
2026-02-12 2025.6 / 2025-12-22 1982.1. Close-side tails: NZD 2022-10-12
239.1 / 2022-10-21 201.0; CHF 2024-03-08 216.1; XAU 2023-12-15 74.2;
XAG 2026-02-02 162.8.

**Recommendation to the registration freeze (analyst, not an executed
act):** freeze `…-O-FOLDS` as the fill-facing p50/p90 the kernel and the
×1.5 stress tier consume (fills only occur in LEARN/folds; FOLDS p90 ≥
FULL p90 for NZD/CHF, and the XAU/XAG lower FOLDS p90s differ from EVAL
by <7%); freeze `…-C-FULL` as the validation band (probe continuity,
exact reproduction); carry the stale-open tail disclosure and the
open-choice (trim vs no-trim) as an explicit owner decision. XAG cells
are derived for completeness only — XAG stays NOT_RUN under OI-4 and no
slate leg consumes it.

### 1.9 G5 status today

**Computed, log-ready, freeze-ready — PASS-pending-freeze.** The gate
itself ("daily-band spread derivation frozen (MEASURED-DERIVED, logged)")
reads PASS only when the registration freeze consumes this table; no
self-granted PASS. Nothing here depends on the OI-2 statement (spread
bands are bar-quoted, not statement components).

---

## 2. G6 — AUD/CAD D1 input completion (DS-05 consumes AUDUSD/USDCAD D1 closes)

### 2.1 What exists (measured today)

- **H1 ANC parquets (the frozen inputs):**
  `…/.worktrees/erp1-tracka-cohort-1/repro_twin/research/control/ERP1-TRACKA-COHORT-1/data_local/derived/bars1h_ANC_{AUDUSD,USDCAD}.parquet`,
  staged read-only in PC12A `data_freeze/H1_PANELS.json`
  (`pc12a_h1_panels_freeze@1`).
  - AUDUSD: 30,420 rows, `2021-01-03T23:00Z → 2026-06-30T20:00Z`,
    sha256 `4e0ca174a21e155271a481727259daa0d3df888bb9f96eb7b34d8c6f06881364`
    — **re-hashed today: match.**
  - USDCAD: 30,386 rows, `2021-01-03T23:00Z → 2026-06-30T23:00Z`,
    sha256 `335a6e2aab25aebff17f9198f1b939448262186ed20e63f3041f8818d02f376b`
    — **re-hashed today: match.**
  - Both panels cover the 2026-06-30 session completely (last-hour
    asymmetry 20:00Z vs 23:00Z is a recorded panel fact, not a partial
    day), so the declared D1-close aggregation ends cleanly at
    **2026-06-30** (Tuesday).
- **Dukascopy M1 estate (ERP1 lineage):** sha-pinned manifests exist
  (`data_local/duka/m1_manifest_{AUDUSD,USDCAD}.json`, window
  2021-01-01 → 2026-06-30, 4,014 files each, 0 missing days) but **0
  `.bi5` files are on disk** (measured: `find … -name '*.bi5'` → 0) —
  raw corpus absent.

### 2.2 Channel audit for an extension to 2026-09-30 (options checked, none executed)

| channel | measured state | lawful for extension? |
|---|---|---|
| Dukascopy .bi5 re-download (ERP1 raw) | raw absent; estate network-blocked on this host — **L-FXFF-1** (SLEEVE-FX5 OWNER_PACKET item 3: "raw .bi5 files are NOT on disk … network-blocked — L-FXFF-1; Action = owner names an allowed source/channel for those 2×~4,014 files") | **NO** unless the owner names an allowed channel |
| fx-majors panels (`FX-MAJORS-SEARCH-V1` worktree `data_local/`) | contains **GBPUSD, USDJPY only** (dirs listed; no AUD/CA) | NO — pairs absent (confirms the dispatch premise) |
| fx-rangefade panels (`FX-RANGEFADE-2M-SHADOW-V1` `data_local/`) | contains **EURUSD only** | NO — pair absent (confirms the dispatch premise) |
| **IBKR HMDS D1 BID/ASK pull for AUD.USD / USD.CAD** | precedent EXISTS: the executed read-only 7-asset probe (ACQUISITION_REPORT: `readonly=true`, `orders_placed=0`, `go_consumed=false`; method `acquire_bounded.py`) pulled sha-frozen daily BID/ASK for NZDUSD/USDCHF/XAUUSD/XAGUSD (7 assets incl. energy; **AUD/CA were NOT among them**); session precedent: `127.0.0.1:7497` raw-ibapi with **Read-Only API confirmed server-side** (order-channel rejected 321) per `FX-MAJORS-BROKER-COST-PROBE-V1` VERDICT_session2 V1 | **YES as a PROPOSAL — not executed here** (see §2.3) |

**Option (a) — the lawful proposal (stated, NOT executed):** an IBKR HMDS
D1 BID/ASK pull for AUDUSD/USDCAD, 2026-07-01 → 2026-09-30, run under the
same read-only 7497 session pattern and `acquire_bounded.py` method as
the executed probe: reqContractDetails identity resolution first (no
AUD/CA identity is on file — the probe's 7 assets did not include them),
then bounded 1-day BID/ASK chunks, sha-frozen into the acquisition
report pattern like the other instruments. Scope note: this extends the
D1 INPUT side only; it does not touch the H1 ANC parquets (M1-D intraday
law unchanged) and does not unfreeze anything by itself. Decision rights:
owner dispatch to a lane; no fetch performed by this task.

### 2.3 Option (b) — typed truncation fallback (exact consequence, computed)

If no extension lands before registration, the precise typing (per plan
§2.4 "typed, never silently truncated"):

- **Boundary:** AUD/CAD D1 inputs end **2026-06-30** (Tuesday). Under the
  next-business-day serving law, the **last lawful AUD/CAD-consuming
  decision is 2026-07-01** (Wednesday, consuming the 2026-06-30 close);
  from **2026-07-02** (Thursday) the consumed bar does not exist →
  `UNAVAILABLE` → fail-closed abort (§6-1 / spec §4), rows typed
  **`NOT_RUN_INPUT_END`**.
- **Fold-8 arithmetic** (session calendar = NZDUSD 1553-day panel, 0
  holes; fold 8 = 2026-03-27 → 2026-09-24 = 182 calendar days):
  - fold-8 decision days: **130 sessions**;
  - runnable: 2026-03-27 → 2026-07-01 = **69 sessions**;
  - typed `NOT_RUN_INPUT_END`: 2026-07-02 → 2026-09-24 = **61 sessions
    = 46.9% of fold 8** (85 calendar days).
- **Affected legs:** under the §0b ¶1 operative slate — **DS-05 only**
  (its 7-pair rank needs ALL of EUR/GBP/JPY/AUD/CAD/NZD/CHF; one missing
  pair blocks the leg fail-closed). DS-03 is unaffected (EIA + USDJPY
  only) → fold 8 counts fully for DS-03. If parked legs were un-parked at
  registration, DS-01/DS-04/DS-06/DS-07 inherit the same cut (all five
  AUD/CA-consuming legs are named in plan §2.4).
- **Open-position consequence (must be frozen with the typing):** DS-05
  exits are as input-dependent as entries ("hold until out of top-3"),
  so after the cut no rule-based exit can fire; the honest typed fallback
  is **force-flat at the truncation boundary** (first unavailable
  decision, 2026-07-02; exit priced on the still-available EURUSD vehicle
  quotes; costs charged; disclosed) — the fold-edge force-flat law
  applied at the input edge rather than left holding unsupervised to
  2026-09-24. Recommended, owner-freezable either way.
- **LEARN/warmup unaffected:** AUD/CAD panels start 2021-01-03 (complete
  from the 2021-01-04 session), warmup ends 2021-09-30, LEARN
  2021-10-01 → 2022-09-22 is input-complete. **Only fold 8 truncates.**

### 2.4 Recommendation

**(a) as proposal + (b) as the standing fallback**, exactly as the
dispatch directed: dispatch the read-only IBKR HMDS D1 AUD/CA pull (the
only channel both lawful and evidenced); if it has not landed by the
registration freeze, freeze the §2.3 typing verbatim (61/130 fold-8
sessions `NOT_RUN_INPUT_END`, DS-05 only, force-flat at 2026-07-02).
No fetch was executed by this task.

### 2.5 G6 status today

**NOT_RUN — pending owner/lane action (option a) or the typed fallback
being frozen at registration (option b).** The truncation consequence is
now computed and typed precisely, but the gate itself is an
owner/registration act, not self-granted.

---

## 3. Gate status table (today, this file's scope)

| gate | statement | status today |
|---|---|---|
| G5 | Daily-band spread derivation frozen (MEASURED-DERIVED, logged) | **COMPUTED / FREEZE-READY — PASS-pending-freeze** (bands derived from sha-verified raw, probe cross-check exact, tables in §1.8; freeze act belongs to registration) |
| G6 | AUD/CAD D1 input completion OR fold-8 truncation typed | **NOT_RUN — pending owner/lane action or typed-fallback freeze** (proposal §2.3(a) stated, not executed; fallback §2.3(b) computed: last decision 2026-07-01, 61/130 fold-8 sessions typed) |

Both gates remain subject to the binding OI-2 blocker for anything
downstream that would score: statement absent ⇒ no after-cost PASS, no
scored run (nothing in this file scores).

## Boundary compliance (this task)

Read-only except this one file
(`…/successor/daily_successor/G5_G6_SPREADS_INPUTEND.md`); `.venv/bin/python`
used for hashing/quantile/date arithmetic on frozen raw files only; no
network, no fetch (the IBKR AUD/CA pull is a PROPOSAL, not executed), no
engine run, no scored computation, no registry/ledger/eligibility write,
no S1, no orders, no keys, no worktree branch writes. No PASS inferred
from any NOT_RUN cell; XAG cells derived for completeness only (OI-4
NOT_RUN stands); costs remain NOT_RUN_STATEMENT (OI-2) and nothing herein
scores.

— end of G5/G6 preparation artifact —
