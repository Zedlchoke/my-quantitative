# LANE REPORT — L-ST (stocks data census + validation)

Cycle: DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1. Lane: L-ST.
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/data-foundation-v1/lane-st`
Branch: `orca/dfv1-lane-st`, base/dispatch SHA `189c6d23ab2a6f50475819cf6df2e2e4def92820` (verified before any write).
Mode: OFFLINE (zero network requests), read-only outside allowed paths, no heavy jobs (every substantive chunk run under `/usr/bin/time`; largest cost = 3 streamed passes over the 227 MB v13 archive, each ≈40–60 s wall).

Rows: see `inventory_rows.jsonl` (21 rows). Counts by status:
AVAILABLE_VALIDATED 9 · AVAILABLE_UNVALIDATED 8 · BLOCKED_LICENSE 1 ·
BLOCKED_ACCOUNT 1 · NOT_RUN 2 (terminal-kill rulings with no local dataset).

## 1. What exists (measured this cycle)

### EODHD panels
| Panel | Where | Census (this cycle unless noted) | Verify |
|---|---|---|---|
| STOCKS-SEARCH-V1 raw EOD cache | `.worktrees/stocks-search-v1/.../p0/raw/eod_cache/` (1.9G, 111,323 files) | 111,322 symbols; 142,609,234 served rows; 2015-01-02..2026-09-17; 7,476 zero-served names (from committed per-name census, cross-checked on 10 raw files) | SAMPLED — sha pinning covers only **6/111,322** files; CKHGF exact match |
| STOCKS-AMIHUD-V1 staging | `.worktrees/stocks-amihud-v1/.../p0/staging_eod_csv/` (219M, 8,220 CSV) | 8,219 symbols; **4,676,951 rows**; 2017-07-03..2022-12-30; 0 empty | **ALL_MATCH** — full re-hash 8,219/8,219 vs crawl_manifest_v2.jsonl (1.71 s) |
| STOCKS-AMIHUD-RETEST-V1 copy | `.worktrees/stocks-amihud-retest-v1/.../p0/staging_eod_csv/` | identical rows/window re-measured from the copy's bytes; quarantine taxonomy 9,001 codes (Q4_NO_SERIES 8,356 / Q1_GHOST 499 / Q2_VENDOR_TEST 52 / Q3 dup 10) | SAMPLED — 3/3 byte-identical to ALL_MATCH origin |
| STOCKS-NG6 cohort panel | archived `stocks-ng6_integration.tar.gz` (sha 808ca4f1 MATCH); worktree empty | 2,178 members / 2,168 unique tickers (10 ticker_reuse_risk); 3.21M rows inherited, not re-measured | SAMPLED (archive level) |
| V13 staging (Form-4 substrate + corp actions + prices + submissions) | archived `stocks-free-v13_integration.tar.gz` (sha 57a9d42c MATCH); worktree empty | form4_xml 345,150 docs; form4_stream 546,039 rows; eodhd_div 2,168; eodhd_splits 2,168; submissions_alive 410 (digest sidecar) | SAMPLED (archive level + manifest/stream shas, below) |

Defect laws carried on the EODHD price family (inherited, not re-litigated):
L-SAMV1-1 (reverse-split adjustment NOT smoothed — adjusted_close is as-of-pull,
NOT point-in-time), L-SAMV1-2 (ghost series HTV/NLG — quarantined),
L-SAMV1-3 (volume-0 bars).

### SEC EDGAR substrates
- **Form-4 XML substrate**: 345,150 docs live only inside the sha-verified v13
  archive. The substrate manifest streamed out of the archive hashes **EXACTLY**
  to the committed pin `5d351623675f71a9950d0e290b1fafff89901265f18bf6c687660e96285ea26b`
  (packet digest confirmed). Two committed full re-hashes of the 345,150 files
  exist (P0 p0_s1_repverify; A7). Per-file re-hash NOT re-run this cycle (budget).
- **form4_stream.jsonl**: streamed out of the archive and hashed **EXACTLY** to
  `6ac2cd5b…` (committed pin; 546,039 rows per committed sidecar + V3 PA0 reverify).
- **4/A amendment corpus**: archived `stocks-ng2_form4a.tar.gz` (sha 22f30ead
  MATCH vs committed sums); 6,123 corpus files + fetch_state counted from the
  tar listing; 3,062 accessions with acceptanceDateTime recorded (inherited).
- **FTD half-month archive**: 434 zips on disk (cnsfails200907a..202608b +
  22 cnsp quarterly backfill 2004q1..2009q2), 601 MB. 15/15 sampled zips MATCH
  the committed manifest; official page HTML re-hashed EXACT `e811f192…` MATCH.
  Timing contract (P-26 / FTD_CONSERVATIVE_AVAILABILITY@1): posting_bound =
  half-month end + 15 d; guard ≥16 d (17 conservative); machine-readable
  posting dates NOT found (f2 scan); settlement date NEVER availability;
  historical scored use RETROSPECTIVE_ONLY; short-attribution forbidden.
- **N-PORT 2026q2 QQQ**: zip re-hashed EXACTLY `077cc836…` MATCH; QQQ holdings
  = **102 rows** measured from `target_holdings_filtered.tsv`. FILING_DATE+1d
  availability, lag p50 57d / p95 62d, supersession rule recorded.
- **Form-15 death-inclusive cohort census**: located in git
  (`orca/stocks-free-v13-integration`, stocks_free_v9_run). cohort_v9.json
  streamed from git hashes EXACTLY to the cross-cycle pin `6a95401f…`.
  Census: 3,395 filings / 2,301 death filers; 12B/12G taxonomy buckets
  (DEATH_CANDIDATE 2,444 / CLASS_TERMINATION 538 / UNCLASSIFIED_NO_CLASS 384 /
  FORM15F_FOREIGN 8 / UNCLASSIFIED_NO_TABLE 21, fail-closed); cohort 410 ALIVE
  + 1,769 DEAD; P0d split {DEAD_PRICE_CONFIRMED 1550, NOT_DEAD_PRICE_SURVIVAL 219}.
  Raw EDGAR FTS bytes are GONE (gitignored, v9 worktree removed; hashes committed).

### Reference rates (shared)
- **OFR STFM**: 5 FNYR series + inventory (276K); 3/3 sampled shas MATCH the
  committed v1r1 manifest. RETRIEVAL_TIME_ONLY ruling.
- **NY Fed**: 5 reference-rate files; 2/2 sampled shas MATCH the committed
  manifest; `revisionIndicator` machine-served per row. RETRIEVAL_TIME_ONLY at
  acquisition but revision-aware source.

### Terminal rulings recorded (rows, evidence artifacts only)
- **Stooq bulk** — NOT_RUN (no local dataset): data-authority kill P-7
  (probe_verdict.json G3: dead canaries 0/14); zip disposed in ~/Downloads;
  can never be primary (source-side absence of dead names).
- **Twelve Data Basic** — NOT_RUN: terminal kill (p0b2_probe_verdict
  FAIL_CLOSED_BLOCKED_DATA_AUTHORITY, gate-3 delisted) + §3 NO-cost-authority (F4).
- **FINRA daily short-sale volume** — BLOCKED_LICENSE terminal (P-25);
  A7 terms snapshot with verbatim ToU quotes on disk in the ng4 evidence dir.
  Reopen = FINRA data license permitting research/bulk use.
- **EODHD earnings-history channels** — BLOCKED_ACCOUNT: /api/fundamentals/{ticker}
  and /api/calendar/earnings both 403 on the living token (NG3 terminal channel
  map). Reopen = owner entitlement upgrade, probe-first cycle.

### Shared macro consumed by stocks cycles (flagged asset_class=shared; L-PIT consolidates)
- Treasury par yields (37 years, 9,181 rows, 1990-2026-09-11; rates_r_twin archive).
- FRED granted set (7 series pinned incl. vintaged machinery fixtures; +
  vintaged S2 staged copies in the forex-v8 archive).
- CBOE VIX family (VIX/VIX9D/VIX3M/VIX6M sha-pinned at ingest with retrieved_utc;
  vol_r_twin archive).

## 2. Key findings / defects discovered

1. **stocks-search-v1 staging identity is effectively unpinned.**
   `f9_artifact_digests.json` claims raw identity is "pinned per pull
   (sha256_raw / sha256_gz)", but only 6 of 111,322 pull records carry shas
   (1 sha-pinned pull + 5 double-pull reproducibility pins). The 1.9G corpus —
   the largest stocks dataset on disk — has no per-file sha manifest. A cheap
   one-pass SHA256SUMS job (~2 min CPU) would close this.
2. **Form-4 substrate survives only inside an archive.** The worktrees holding
   it (stocks-free-v13, stocks-ng2, stocks-free-v9) are emptied; bytes live in
   `~/staging_backups` tarballs whose shas all MATCH committed sums. Digests
   verified, but any future consumption requires a restore step first.
3. **Form-15 raw EDGAR bytes are gone** (hashes + census JSON survive in git);
   the census is reproducible via keyless FTS re-enumeration.
4. **The amihud staging is the only fully-validated stocks price panel**
   (ALL_MATCH + row/window census), and it is a 2017-07..2022-12 subset —
   the broader search-v1 cache covers 2015..2026-09 but is unpinned (finding 1).
5. **EODHD adjusted prices are not PIT-safe** (inherited L-SAMV1-1, re-observed:
   AAPL 2015 adjusted_close=24.17 vs close=109.33 — adjustment as-of pull date).
   PIT corporate actions remain an open gap (G3 below).

## 3. Gap candidates (packet list)

### G1 — Earnings history with publication timestamps + revisions. PRIORITY 1 (need-now)
- Why needed: owner priority list ("earnings/filings có publication timestamp
  và revision"); Q-7 lesson says the clock is most of event variance (91.7% of
  8-K windows at the 09:30 bar) — without acceptance datetimes no earnings
  family can be clocked honestly.
- Hypothesis class opened: announcement-timing families (PEAD-class, revision
  drift, clock-conditioned event studies).
- Prior kill fixed: STOCKS-NG3 E1 kill (earnings channel 403 on EODHD).
- Falsifying control: Q-7 clock-only shadow (event credit only above the
  clock); revision-decomposition control (timing state vs restatement state).
- Cost: **EDGAR 8-K/10-Q acceptance datetimes are FREE and entitled** (declared
  UA; submissions/{CIK}.json + index.json; a cohort-scoped probe ≈ thousands of
  light calls, <100 MB, inside §8 budgets). This beats the EODHD entitlement
  upgrade (owner purchase, $) and is already license-screened. A1 probe
  candidate for a follow-up cycle.

### G2 — Trades/quotes with explicit SIP/IEX scope. PRIORITY 3 (only-with-mechanism)
- Why needed: owner priority list; no trades/quotes bytes exist on disk at all.
- Hypothesis class: microstructure/execution families (spread capture, order-flow
  states) — currently ALL blocked.
- Prior kill fixed: none (never attempted; cost/authority walls recorded at
  DATA-EDGE-UNLOCK-V1 Lane F class).
- Falsifying control: bounded-window cross-venue tape reconciliation (IEX-only
  tape vs SIP-referenced prints) — if IEX-only misprices SIP names beyond cost
  bands, the cheap substitute is killed before any family work.
- Cost: IEX Historical (keyless cart, per-file pricing ≈ $0.01/PCAP-ish scale,
  bounded slice ≈ 10–50 GB/yr) is the only plausible licensed entry; full SIP
  history is vendor-TB-scale (out of reach). Runbook inputs only — NO signup
  this cycle. BLOCKED_COST until owner action.

### G3 — Corporate actions point-in-time. PRIORITY 2 (need-now, cheap)
- Why needed: L-SAMV1-1 is a recorded defect law — EODHD adjusted series is
  as-of-pull, so any historical state computed on adjusted prices embeds
  future split/dividend knowledge (lookahead by construction).
- Hypothesis class: fixes ALL adjusted-price state families on the standing
  universe (52W-high, illiquidity, level-break) to be honestly backtestable.
- Prior kill fixed: L-SAMV1-1 (and the V13 DIV-DECOMP contamination risk).
- Falsifying control: rebuild adjusted series forward from action dates and
  compare against served adjusted_close at ≥2 vintages; drift = detection
  (L-TRACKB1-1-style last-stamp test). Note: the entitled EODHD
  dividends/splits channels already exist on disk (2,168 + 2,168 files in the
  v13 archive) — an action-date table with effective/ex-dates is buildable
  without new entitlements; EDGAR 8-K split announcements add the
  announcement-time leg.
- Cost: derivation-only (no network); ~1–2 days of pipeline work + disk for
  the restored archive.

### G4 — Borrow/short-fee history. PRIORITY 4 (only-with-mechanism)
- Why needed: owner list ("nếu định short"); no source on disk; FINRA blocked
  (P-25); IBKR securities-finance needs an account.
- Hypothesis class: short-side families (fee-adjusted carry, squeeze states).
- Prior kill fixed: none (NG2 short-interest was an entitlement kill — no
  entitled short-state exists at all).
- Falsifying control: borrow-state vs FTD-level state decorrelation (two
  different expressions of short-pressure; P-20 law).
- Cost: owner action (broker account w/ securities-finance data or a licensed
  vendor); unrunnable otherwise.

### G5 — Halts/auction calendar. PRIORITY 4 (only-with-mechanism)
- Why needed: owner list; LULD halts corrupt any event window that crosses one.
- Hypothesis class: event-window integrity (a fixture, more than a signal).
- Prior kill fixed: none.
- Falsifying control: halt-affected vs halt-free event outcome split.
- Cost: needs tape access (pairs with G2) or an exchange feed; no keyless source.

### G6 — Identity mapping (ticker↔CIK↔CUSIP/ISIN with dates). PRIORITY 2 (need-now, cheap)
- Why needed: FRC→FRCB symbol mutation is measured; CUSIPs re-use over decades;
  FTD joins without entitled historical mapping are RETROSPECTIVE_ONLY and
  survivorship-prone. This blocks G4-adjacent and FTD joins, and pollutes
  ticker-keyed panels (10 ticker_reuse_risk members already flagged in NG6).
- Hypothesis class: enables every cross-dataset join (FTD×prices, Form-4×prices,
  N-PORT×prices) to be PIT-correct.
- Prior kill fixed: partial — the Form-15 cohort + submissions_alive + EODHD
  delisted cache already give a CIK↔name↔symbol map WITH death dates; the FTD
  within-archive CUSIP+DESCRIPTION identity is solid; what is missing is a
  DATED CUSIP→ticker authority.
- Falsifying control: join-reconciliation test — same-name join vs CUSIP join
  disagreement rate on a bounded window; disagreement above a floor kills the
  mapping.
- Cost: derivation from existing entitled artifacts (SEC submissions frames +
  Form-15 cohort); ~1 day; no new entitlements.

### G7 — Real execution cost basis for equities. PRIORITY 4 (only-with-mechanism)
- Why needed: owner list ("chi phí khớp lệnh thực tế"); no measured source;
  Q-2 law: costs are conditional (time-of-day, price level, liquidity bucket).
- Hypothesis class: any family claiming net-of-cost viability on single names.
- Prior kill fixed: broker-cost authority kills (3 censuses, FX majors) have no
  equities analog yet.
- Falsifying control: spread/liquidity-bucket measurement vs the current
  static cost_bands.json (stocks-search-v1) — if static bands are within X bps
  of measured conditional costs on a bounded sample, bands stand.
- Cost: derives from G2 tape slices; blocked until G2 exists.

### Top-3 (for the gap matrix)
1. **G1 earnings timestamps via EDGAR acceptance datetimes** — free, entitled,
   directly fixes a recorded kill, highest priority.
2. **G3 PIT corporate actions** — derivation-only from already-entitled bytes,
   fixes a recorded defect law contaminating all adjusted-price families.
3. **G6 dated identity mapping** — derivation-only, unblocks honest cross-source
   joins for FTD/Form-4/N-PORT.

G2/G4/G5/G7 stay `only-with-mechanism` (G2 = owner purchase decision on IEX;
G4 = broker/vendor license; G5/G7 derive from G2).

## 4. Incidents / limitations
- One tar listing was briefly written to `/tmp/none_write_here.txt` (~50 MB,
  outside the repo, deleted in the same command). Read-only discipline applies
  to repo/data surfaces; recording for transparency. F10 temp budget (≤1 GB) held.
- OFFLINE lane: entitlement states recorded from terminal verdict artifacts
  only; no live re-probe. `.env` never read.
- STOCKS-SEARCH-V1 is BLOCKED-not-terminal: `ps aux` checked (no writers)
  before sampling; census kept metadata + ≤20-file sha sample per packet.
- Form-4 XML per-file re-hash (345,150 files) not re-run this cycle — inside a
  227 MB archive; streaming per-file verification would have required full
  extraction (disk + time). Two committed full re-hashes cover it.
- Shared macro rows are cross-asset; L-PIT consolidates per F9/F5.
- A1 integration must NOT read `~/.my-quantitative-data` bytes as validated
  beyond the per-row evidence stated here.
