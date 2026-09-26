# LANE REPORT — L-FX (forex data census + validation)

Cycle: `DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1` · Lane L-FX · branch
`orca/dfv1-lane-fx` · base/dispatch SHA `189c6d23ab2a6f50475819cf6df2e2e4def92820`
(verified: worktree HEAD == dispatch SHA, porcelain clean at start).
OFFLINE lane: zero network requests made. First work chunk measured under
`/usr/bin/time` (0.06 s — orders of magnitude under the F10 abort thresholds).

Owner priority list (verbatim anchor, OWNER_DIRECTIVE.md): bid/ask có
timestamp đủ mịn, spread đúng giờ đặt lệnh, commission/slippage và
swap/financing từ broker; lịch phiên và DST; sự kiện kinh tế với thời điểm
công bố và các lần sửa số liệu; phân biệt giá indicative với quote có thể
giao dịch, dữ liệu một nguồn với replication độc lập.

## 1. Census summary

23 authority rows in `inventory_rows.jsonl`. Status counts:

| status | count | rows |
|---|---|---|
| AVAILABLE_VALIDATED | 7 | dukascopy_m1_eurusd_eosv1, dukascopy_m1_eurusd_eosv2, dukascopy_m1_eurusd_rangeexp, dukascopy_m1_gbpusd_fxmajor, dukascopy_m1_usdjpy_fxmajor, td_spot_daily_4pairs_v9, td_xauusd_1day |
| AVAILABLE_UNVALIDATED | 8 | td_spot_5pairs_ng7_archived, cpi_archives_official_v9, fred_vintaged_cpi_oecd_v9, fred_vintaged_rates_v8, macro_events_8region_v3r_archived, cftc_cot_evidence_ng5, forex_search_v1_staging, xauusd_ibkr_probe |
| BLOCKED_TRANSPORT | 2 | forex_intra_bidask_canary, fx_futures_frontier_canary |
| NOT_RUN (with reason) | 6 | erp1_tracka1_duka_audusd, erp1_tracka1_duka_usdcad, erp1_tracka2_derived, erp1_sealed_holdout_2026h1_audusd_usdcad (all F8), forex_mt5_cost_probe, + manifest_verify NOT_RUN inside ERP1 rows |
| live-owned (F5) | (1, inside AVAILABLE_UNVALIDATED) | fxrangefade_2m_eurusd_live — INHERITED_NOT_REHASHED_LIVE_OWNER |

F9 mapping note (plan §14 F9): `BLOCKED_TRANSPORT` ≡ `BLOCKED` with
cause = transport (standing environment constraint, L-FIBV1-1/L-FXFF-1) in
the owner's 7-state view. Both canary rows carry this note.

### Dukascopy M1 BID/ASK corpora (the program's only tick-adjacent FX authority)

All four corpora re-measured from bytes this cycle: file counts match their
committed per-file-sha256 manifests exactly; first/last day-file names
recorded; 5/5 sampled files per corpus re-hashed sha256+bytes == manifest
(`manifest_verify: SAMPLED`, n=5 per corpus). None exceeded the 500 MB
full-hash budget, but the packet's ≤5-file sample rule was applied as the
stricter standard.

| corpus | files (disk==manifest) | window (census) | bytes | verdict artifacts |
|---|---|---|---|---|
| EURUSD eosv1 | 3,652 | 2021-01-03T22:00Z → 2025-12-31T23:59Z (1,826 days) | 32,408,632 | census BUILD_PASS, bars15_valid 119,038 |
| EURUSD eosv2 | 4,014 | → 2026-06-30T23:59Z (2,007 days) | 35,355,502 | BUILD_PASS, bars15 130,911 |
| EURUSD rangeexp | 4,014 | identical twin of eosv2 | 35,355,502 | m1_manifest sha256 **identical** (ef154574…) — measured duplicate |
| GBPUSD fxmajors | 4,184 | → 2026-09-23 (2,092 days) | 36,601,602 | BUILD_PASS, bars15 137,135 |
| USDJPY fxmajors | 4,184 | → 2026-09-23 (2,092 days) | 38,433,187 | BUILD_PASS, bars15 137,376 |

Measured spread census (cost-evidence pointers, p50 open pips by session,
from committed census.json artifacts): EURUSD sessions 0.3 / rollover
21–22 UTC 0.9 (p99 7.737, Sunday open 2.9); GBPUSD rollover 2.3; USDJPY
rollover 1.6. These are the only measured, order-timing-resolved spread
numbers the program holds — and they are Dukascopy indicative quotes, not
tradable quotes from a broker (see gap G2).

Packet correction (measured, not inferred): the packet's claim "EURUSD
2021–2025 +2026-H1 in eosv1/-v2/rangeexp" resolves as eosv1 = 2021–2025
only; the 2026-H1 extension lives in eosv2/rangeexp (→ 2026-06-30).
FX-MAJORS runs to 2026-09-23. Also, FOREX-NG5 measured out to be the CFTC
CoT positioning cycle (its TD legs were restored V9 4-pair legs for the
join), not an independent majors corpus.

### ERP1 corpora (sealed-holdout pairs) — F8 treatment

`erp1-tracka-cohort-1` data_local/duka = AUDUSD + USDCAD M1 BID/ASK,
2007 days × 2 sides × 2 pairs = 8,028 day-files, 2021-01-01 → 2026-06-30
(79 MB), with per-pair `m1_manifest_{AUDUSD,USDCAD}.json`. Manifest FILES
pinned by sha256 this cycle (f869cfa3… / 0f9a7df7…); zero corpus content
opened. Cohort-2 `derived/` (bars15/1h parquet + t2shadow npy) listed by
name only. The 2026-H1 AUDUSD/USDCAD holdout windows remain UNREAD program
assets — the only unexposed confirmation window for the ERP1 strategy
class. Cohort worktrees are TERMINAL cycles' control dirs (readable), but
the seal discipline (plan §2, §14 F8) was applied in full.

### TD (Twelve Data) legs

- XAU/USD 1day: full re-hash match vs committed NG6 P0 verdict sha
  (49c2684e…), 12,268 rows counted, 1979-12-26 → 2026-09-16. Standing
  ruling carried: vendor OHLC-only, **NO cost authority** — NG6 P0-F4
  measured all 7 cost components `measurable_from_td=false`; the worktree
  is kept specifically as the NG6R1 reopening price authority.
- 4-pair daily spot (AUDUSD/GBPUSD/NZDUSD/USDCAD, 5,000 bars each from
  2007-11-16): committed on `orca/forex-ng5-integration`
  (`td_spot_restored/` + `td_digest_pin.json`); all 4 files re-hashed EXACT
  vs pin this cycle; physical bytes also in `forex-v9_cpi_spot.tar.gz`
  (sha re-measured match vs SHA256SUMS).
- NG7's staged 5-pair spot legs: archived in `forex-ng7_integration.tar.gz`
  (P-13 manifest `p13_archive_manifest@1`, sha re-measured match); contents
  not extracted (restore-rule deferred).

### Macro/event archives

Located and pinned at archive level (all shas re-measured == manifests):

- `forex-v9_cpi_spot.tar.gz`: official CPI archives US (FRED CPIAUCSL
  realtime) / GB (ONS D7BT) / CA (StatCan 18100004) / AU (ABS 6401.01) +
  **FRED vintaged OECD CPI** for AU/NZ/CA/GB + manifest. This is the only
  revision-history (S2-class) CPI set the program holds.
- `forex-v8_staged_vintaged.tar.gz`: FRED vintaged T10YIE/DGS10/DFII10.
- `forex-free-v3r_full.tar.gz`: 8-region macro/event series (US/GB/CA/AU/
  NZ/JP/CH/EMU) + evidenced vintages manifest.
- CFTC CoT: censuses/mapping/verdicts committed on the NG5 branch
  (coverage 1986 → 2026-09-08, no-revision ruling critic-verified);
  **raw report pulls are absent locally** (NG5 worktree removed without a
  dedicated tarball — re-fetch is free/keyless when needed).
- BIS WS_CBPOL / ECB SDMX: NO bulk local corpus exists — only adapter test
  fixtures (bis_cbpol.json, ecb_sdmx_exr.json) inside the v3r archive and
  plan-level mentions. Honest finding: the program never held BIS/ECB bulk
  data; any policy-rate/HICP work needs a fresh (free, entitled) pull.

### Live/blocked/probe items

- FX-RANGEFADE-2M-SHADOW-V1 (ACTIVE_LIGHT): own EURUSD corpus 4,184 bi5 +
  manifest present in its worktree; censused metadata-only
  (`INHERITED_NOT_REHASHED_LIVE_OWNER`), no hashing, no MISMATCH possible.
- Canary dirs: `forex-intra-bidask-v1` 8 KB (two DoH artifacts backing the
  committed 36/36 ConnectionResetError transcript, SNI-keyed filter proof);
  `fx-futures-frontier-v1` 0 B. Both BLOCKED_TRANSPORT with the F9 mapping.
- Cost probes: MT5 collector A7-audited `PASS_ZERO_FORBIDDEN_CALLS`
  (read-only surface), never run — zero account-bound bytes program-wide
  (3 independent censuses); IBKR probe = official margin/commission pages +
  contracts, gateway timed out unauthenticated. Both are L-COST pointers
  recorded as datasets.

## 2. Gap candidates (feeds DATA_GAP_MATRIX)

### G1 — Broker-grade spread/commission/slippage + swap for FX majors — **PRIORITY H**

- Why needed: every FX generation died at the cost floor (ERP1's 3.6/4.4-pip
  floor partitioned the space; NG6/NG7 F4 kills; DEU-LaneF "zero
  account-bound bytes in 3 independent censuses"). The owner priority list
  names this first: "spread đúng giờ đặt lệnh, commission/slippage và
  swap/financing từ broker".
- Hypothesis class opened: any net-of-cost intraday FX family on
  bid/ask-capable instruments; separates 0.3-pip-session strategies from
  9.4-bps-worst-case survivors (FOREX-SEARCH-V1 currently assumes
  STATED-CONSERVATIVE constants, not measurements).
- Recorded kill it fixes: three generations' broker-cost kills + ERP1 cost
  floor + NG6/NG7 F4.
- Falsifying control: owner-run MT5 collector spread distribution vs the
  measured Dukascopy census (p50 0.3 sessions / 0.9 rollover) — gross
  divergence flags vendor mismatch; swap bands sampled over a week vs
  triple-swap-Wednesday structure.
- Cost/volume: collector already written + audited (zero new code);
  owner-run ~1 session, <10 MB output. Unblocking action: OWNER runs
  `research/control/forex_mt5_cost_probe_2026-09/OWNER_RUN.md`.

### G2 — Tradable-vs-indicative distinction + independent second source for EURUSD — **PRIORITY H**

- Why needed: the only M1 bid/ask authority is a single Dukascopy
  indicative feed; fresh acquisition is BLOCKED_TRANSPORT (SNI) and the
  fresh TCU worsened (EURUSD-DATA-QUALIFICATION-V1). No replication
  source exists to distinguish feed artifacts from market structure.
- Hypothesis class opened: replication/robustness testing of every
  Dukascopy-scored family; "tradable quote" verification for execution
  claims.
- Recorded kill it fixes: EDQ1 TCU worsening (single-vendor lock-in) and
  the indicative-vs-tradable ambiguity the owner directive names
  explicitly.
- Falsifying control: second-source M1 bid/ask (e.g. TrueFX/OANDA v20
  practice, both owner-license-pending per §3) cross-correlation on
  sampled weeks — if spread levels/session structure disagree materially,
  Dukascopy-specific artifacts are exposed.
- Cost/volume: TrueFX free registration files ~2–4 GB/yr/pair compressed;
  OANDA practice API light. Both need owner license capture first
  (P-25 gate) — runbook entry, not a lane action.

### G3 — Economic events with publication timestamps + revision vintages (beyond CPI) — **PRIORITY M**

- Why needed: program holds vintaged CPI (AU/NZ/CA/GB) + US realtime CPI
  and 8-region event series, but ERP1-class event strategies need
  announcement-moment timestamps (the owner list: "sự kiện kinh tế với
  thời điểm công bố và các lần sửa số liệu") for GDP/employment/rate
  decisions too. BIS WS_CBPOL/ECB HICP were never bulk-acquired.
- Hypothesis class opened: PIT-correct macro conditioning beyond CPI
  (rate decisions via BIS WS_CBPOL vintages; HICP for EMU leg).
- Recorded kill it fixes: hardens the PIT law (P-18/ERP1
  truncation-proof standard) that killed ERP1 TrackA variants; prevents
  look-ahead kills of the V3/V4 class.
- Falsifying control: event-time join on a known release (e.g. FRED
  ALFRED vintage dates vs BIS amendment dates) — misaligned vintages fail
  the PIT battery.
- Cost/volume: BIS WS_CBPOL full history ~10 MB; ECB SDMX HICP ~50 MB;
  both free/keyless — within §8 probe budget for a future cycle.

### G4 — Session/DST calendar authority — **PRIORITY M**

- Why needed: session conventions are currently frozen ad hoc per cycle
  (FOREX-SEARCH-V1 master calendar sha-pinned; NG6 F2 convention frozen);
  no shared, tested session/DST authority exists (owner list: "lịch phiên
  và DST").
- Hypothesis class opened: session-conditioned strategies (rollover fade,
  Sunday-open) with a single citable calendar instead of per-cycle
  conventions; audit-proof DST handling.
- Recorded kill it fixes: pre-empts the clock/session kill class (NG5 V1
  margins anchor-clock finding; NG6 F2 needed a dedicated adjudication).
- Falsifying control: `exchange_calendars` FX-backed calendars vs the
  frozen master calendar (4,924 days, sha e511b7da…) diffed on DST
  boundaries 2021–2026; any mismatch must be adjudicated, not absorbed.
- Cost/volume: `exchange_calendars` pip install + a battery of ~20 asserts;
  effectively zero disk.

### G5 — Financed (swap) bands per pair — **PRIORITY H (owner-action-gated)**

- Why needed: NG7 died exactly here (F4 financing band unobtainable);
  FOREX-SEARCH-V1 charges financing uniformly (1.7 bps/night, worst-case
  9.4 bps round trip) as a stated constant. Any multi-day FX hold is
  unfalsifiable without per-pair long/short swap + triple-swap day.
- Hypothesis class opened: multi-day financed FX books with honest
  carry; separates price-alpha from carry-alpha (dual-books gate already
  wired fail-closed in FOREX-SEARCH-V1).
- Recorded kill it fixes: the NG7 F4 kill (financing band).
- Falsifying control: broker swap quotes (same MT5 collector run as G1)
  vs the uniform 1.7 bps assumption — if |measured − assumed| materially
  flips any dual-book arm, the constant must be retired.
- Cost/volume: rides on G1's owner run (same session); <1 MB.

## 3. Limitations & incidents

- Incidents: none. Zero network requests; zero sealed-content reads;
  zero writes outside the allowed path; no heavy jobs (first chunk
  measured 0.06 s under /usr/bin/time).
- Limitations (honest, disclosed):
  1. Archive-level validation only for the five P-13 tarball datasets
     (shas re-measured vs manifests; contents not extracted — restore rule
     respected). Their per-file rows say exactly that.
  2. ERP1 AUDUSD/USDCAD corpora: metadata + manifest-file pins only
     (F8); coverage timestamps read from day-file NAMES, not content.
  3. FX-RANGEFADE row is names-only by F5 (live owner).
  4. BIS/ECB: the packet asked to locate them; measured answer is
     "never bulk-held" — recorded as such rather than padded.
  5. CFTC raw pulls absent locally (worktree removed, no tarball);
     censuses committed on the NG5 branch are the surviving evidence.
  6. `forex-search-v1` worktree: FOREX-SEARCH-V1 does not appear as a
     registered row in the cycle list read this session; its run artifacts
     exist on disk and were censused. Flagged for A1 reconciliation.
- Storage note: the rangeexp corpus is a byte-identical duplicate of eosv2
  (35.4 MB) — consolidation candidate, flagged not acted on (no writes
  outside allowed paths).
- Disk at census end: 6.9 GiB free (floor 5.0 respected; this lane wrote
  only its three artifacts).
