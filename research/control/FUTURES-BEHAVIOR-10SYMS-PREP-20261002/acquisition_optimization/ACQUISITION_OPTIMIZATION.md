# ACQUISITION_OPTIMIZATION — coverage truth, optimized packages, disk gate

Task `FUTURES-BEHAVIOR-10SYMS-PREP-20261002` · lane `ACQ-OPT` · 2026-10-02 (UTC).
Namespace: `research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/acquisition_optimization/`.
Scripts: `acq_probe.py` (round 1) + `acq_probe_followup.py` (round 2) +
`finalize_analysis.py` (offline). Raw evidence: `coverage_results.json`
(every request with UTC timestamps, params, HTTP status, redacted errors).
Machine request lines: `package_manifests/pkgA.json`, `pkgA_variant_24m_floor.json`,
`pkgB.json`, `pkgC.json`. Offline derivations: `analysis_summary.json`.

**Authority scope honored:** metadata READ-ONLY against official Databento
endpoints (`https://hist.databento.com`). **238 logical requests executed
(cap 260 honored; 237x HTTP 200, 1x HTTP 422 typed and resolved; sequential;
<=3 attempts each; 0.4 s spacing). Zero data bytes downloaded, zero
purchases/subscriptions/account changes, zero credit spend.** `get_cost` is a
quote, not a charge. $100/$600 are SCENARIOS, not granted budget — budget is
PENDING with the owner. Key handled per workspace law (in-process read of the
owner 0600 file, passed only as Authorization header; never in
params/URLs/logs/artifacts; artifacts scanned for token patterns).

Endpoint/param knowledge reused verbatim from the verified METADATA-PROBE
lane (`../databento_metadata_probe/DATABENTO_METADATA_PROBE.md`, 78x200 on
2026-10-02): POST record_count/billable_size/get_cost on
hist.databento.com, `{ROOT}.FUT` parent symbols, unit prices from
list_unit_prices. Unit prices re-captured live this run (unchanged):
**ohlcv-1m $70/GB · bbo-1m $18/GB · statistics $1.0/GB · definition $1.7/GB**
(historical mode).

---

## 1. COVERAGE TRUTH (all numbers OBSERVED from live record_count probes)

Earliest-band method: ladder windows probed oldest-first
[W1 2010-06-06..2011-06-06, W2 2011..2013, W3 2013..2016, W4 2016..2019,
W5 2019..2022]; first window with records>0 sets the band, then ONE
half-year refinement [2010-06-06..2010-12-06] of that band.

**Result: EVERY cell (10 roots x 4 schemas) has records in the refinement
window 2010-06-06..2010-12-06.** No root, no schema starts later than the
dataset itself.

| root | outright daily-deepest (=ohlcv-1m depth, local aggregation) | ohlcv-1m earliest band | bbo-1m earliest band | statistics earliest band | definition earliest band | latest ohlcv-1m (2026-09-01..2026-10-02, rc) |
|---|---|---|---|---|---|---|
| NQ | 2010-06-06 | 2010-06-06..2010-12-06 | 2010-06-06..2010-12-06 | 2010-06-06..2010-12-06 | 2010-06-06..2010-12-06 | 55,801 |
| ES | 2010-06-06 | same | same | same | same | 60,406 |
| CL | 2010-06-06 | same | same | same | same | 976,594 |
| NG | 2010-06-06 | same | same | same | same | 491,514 |
| GC | 2010-06-06 | same | same | same | same | 119,742 |
| SI | 2010-06-06 | same | same | same | same | 66,835 |
| 6E | 2010-06-06 | same | same | same | same | 51,549 |
| 6J | 2010-06-06 | same | same | same | same | 52,853 |
| 6B | 2010-06-06 | same | same | same | same | 40,139 |
| 6A | 2010-06-06 | same | same | same | same | 43,179 |

- **Oldest COMMON window across all 10 roots — at BAND precision: every
  root x schema's first observed records fall inside the refinement band
  2010-06-06..2010-12-06** (i.e., earliest valid date is within that band;
  exact per-day start dates are NOT_RUN — they would need day-level probes).
  No cell's earliest band is LATER than 2010H2 for any root or schema, so
  no symbol is availability-limited relative to the dataset: common ==
  longest at band resolution, and any common-window choice is bounded by
  budget, not by availability. Package full-window lines
  (2010-06-06..2026-10-02) all measured records>0.
- All 10 roots are CURRENT (records in the latest-month probe; end dates
  EXCLUSIVE per API semantics — the probe window covers through 2026-10-01).
- **Daily/hourly series are aggregated LOCALLY from ohlcv-1m** — packages
  contain NO ohlcv-1d/ohlcv-1h lines, so there are no duplicate buys and no
  UTC-day vs session-day ambiguity in the fill path (vendor ohlcv-1d is
  UTC-day based; session dailies come from our own 1m aggregation or
  statistics official values, per the request manifest's convention).
- **Known gaps/quality flags (era caveats, not holes):**
  1. FIX/FAST legacy protocol pre-May-2017 (vendor docs, FACT sourced in
     request_manifest vendor_context).
  2. Timestamps pre-2015-11-20 are millisecond-resolution only; no ts_recv
     pre-2017-05-21 (same vendor docs).
  3. stat_flags normalization inconsistent pre-2015-01-20 (published vendor
     data-quality issue, issues.databento.com/roadmap/glbxmdp3-inconsistent-
     normalization-of-settlement-price-stat-flags-prior-to-2015-01-20,
     access 2026-10-02, via DBN-ADAPTER lane `code/futbt/dbn/README.md`).
  4. ohlcv bars are SPARSE (no trade => no record; docs-confirmed) —
     "expected activity" logic, not naive minute grids, for gap QA.
  5. Parent requests (`{ROOT}.FUT`) include ALL listed expiries; dead
     serial books ride along in definitions/statistics but emit no trades
     bars. No serial-dead-book ohlcv/bbo/trades lines are bought on purpose.

## 2. PACKAGE DESIGN (derived from the 50 hypotheses in configs/symbols/*.yaml)

Default core for ALL 10 roots: **ohlcv-1m + definition + statistics**.
- ohlcv-1m: daily depth (aggregated locally), full-Globex session bars,
  event-window M1 — covers every `daily_trades_per_contract`,
  `minute_trades_m1`, `full_session_globex_intraday` requirement class.
- definition: PIT universe/identity (listing/expiration/tick/multiplier).
- statistics: the only schema carrying settlement + open interest + cleared
  volume; front selection stays PAST-ONLY with actual crossover history
  preserved via statistics OI/volume (OI for session t observable t+1).
- **bbo-1m ONLY for the two execution-cost-critical hypotheses: NQ-H5 and
  CL-H5** (`synchronous_bbo`, cost_evidence class; the only two in all 50
  configs). bbo-1m is already the vendor's official 1-minute-sampled BBO
  schema (list_schemas; $18/GB vs tbbo $28/GB) — no further sampling schema
  is needed. Scope discipline: NQ = continuous 2y (floor wording ">=2y
  synchronous quotes"); CL = roll-window-enumerated only, because the CL
  PARENT bbo stream is dominated by far-month quote books (measured: 2y =
  10.80 GB/$194; full = 56.64 GB/$1,019) while the CL-H5 floor only needs
  "synchronous quotes for spread paid at switch" — a measured representative
  roll window (CLN6,CLQ6 2026-06-24..2026-07-03) costs **$0.0130**
  (get_cost), so 96 monthly roll windows for 2019..2026 (12/yr x 8y — the
  code/manifest multiplier, deliberately the SAFE over-estimate vs the ~93
  calendar-month count) ~= **$1.25 (DERIVED from anchor)** and 196 windows
  for 2010..2026 (round(12 x 16.32)) ~= **$2.54 (DERIVED)**.
- **trades/ticks: NOT in any package.** No hypothesis requires tick
  resolution: the configs' shared execution law handles same-bar TP/SL
  ambiguity by WORST-CASE BOUNDS (`same_bar_tp_sl_worst_case_bound_no_point_pnl`),
  roll cost is an adjacent-contract close gap (daily/1m sufficient), and
  SI-H5's own note says limit-style gap risk is "no tick model covers".
  Entry-delay sensitivities are 1-5 min = M1 resolution. Consequence stated
  plainly: any future hypothesis wanting intrabar ORDER resolution is
  UNSUPPORTED by these packages and would need a separately-scoped trades
  quote round (NOT_RUN now). tbbo/MBO/MBP-10/all-ticks: excluded (no
  hypothesis class justifies full-book depth; manifest discipline).
- **EXCLUDED by design:** MBO, MBP-10, all-ticks, continuous/CONTFUT price
  series (never fills/MTM; vendor c/n/v tables used only via the FREE
  symbology.resolve endpoint as measurement objects). No adjusted fills.
- **symbology.resolve fix CONFIRMED this round:** `stype_in=continuous ->
  stype_out=instrument_id` works (HTTP 200; NQ.c.0 = 67 roll intervals,
  CL.c.0 = 197). Round-1's 422 was only `start_date before available start`
  (2010-01-01 < 2010-06-06) — dates must be within range.

## 3. THE THREE PACKAGES (exact quotes; every line MEASURED unless labeled DERIVED)

**Floor policy for SUPPORTED/UNSUPPORTED verdicts (stated explicitly,
post-audit):** explicit yaml quantifiers bind — SI-H2 ">=10y two-leg daily"
= 120m and NG-H1 "M1 >=5y" = 60m in ALL verdicts; the audit-flagged floors
whose literal text exceeds the 24m bar also bind LITERALLY in the headline
counts (NG-H4 ">=3y" = 36m; 6E-H5 "M1 depth >=2019" = 93m from 2019-01-01
to package end). Vague floor text ("several years", "multi-year", ">=2y")
binds at the 24m DAILY_BT admission bar — a disclosed policy choice, not a
yaml literal. Headline = LITERAL policy (conservative-evidence law). The
only verdict difference vs the 24m-default-everywhere comparison: A-v1
30 SUPPORTED (literal) vs 31 (24m default) — 6E-H5 flips; B and C are
identical under both. Each requirement is evaluated on ITS OWN symbols
(post-audit MAJOR-1 fix): CL-H3's daily legs are RB/HO product futures,
explicitly OUTSIDE the 10-root corpus and in NO package -> CL-H3 is
UNSUPPORTED in every package regardless of CL depth.

Cost basis: `cost_usd_list = billable_GB x unit_price`;
`cost_usd_get_cost` = the API's own definitive quote. **The ratio
get_cost/list = 0.9313 EXACTLY on every measured line this round
(post-audit recomputation: 41/41 measured package lines + both bbo anchors;
originally stated 31/31 round-1 lines), consistent with the earlier probe's
2/2** — mechanism undocumented
("respects any discounts provided by flat rate plans"); get_cost treated as
authoritative. Internal consistency: billable_bytes == record_count x DBN
record size (56/80/80/520 B) EXACTLY on every line — API numbers reconcile
with the frozen adapter spec.

### Package A — "essential 10 symbols, longest within ~$100" (v2, tuned)

| line | schema | symbols | window | records | billable GB | get_cost |
|---|---|---|---|---|---|---|
| A2-O1M-{NQ,ES,GC,SI,6E,6J,6B,6A} | ohlcv-1m | per-root parent | 2025-04-01..2026-10-01 (18m) | NQ 789,572 · ES 842,779 · GC 2,202,248 · SI 1,472,279 · 6E 815,968 · 6J 746,855 · 6B 605,559 · 6A 639,311 | 0.034..0.123 each | $2.21..$8.04 each |
| A2-O1M-CL / A2-O1M-NG | ohlcv-1m | CL.FUT / NG.FUT | 2026-01-01..2026-10-01 (9m) | 7,992,734 / 4,702,368 | 0.448 / 0.263 | $29.18 / $17.17 |
| A2-definition-ALL10 | definition | all 10 parents | 2024-10-01..2026-10-01 (24m lead) | 8,299,169 | 4.316 | $6.83 |
| A2-statistics-ALL10 | statistics | all 10 parents | 2025-04-01..2026-10-01 (18m) | 39,092,454 | 3.127 | $2.91 |

**Totals A: 68,201,296 records · 8.61 GB billable · $92.04 list · $85.72
get_cost.** Coverage starts: 2025-04 (8 roots) / 2026-01 (CL, NG).
BBO included: NO. Trades: NO.
**UNSUPPORTED in A: 42 of the 50** (0 vendor-gated hypothesis floors met;
8 are NOT vendor-gated at all). At ~$100 NO package can meet even the 24m
DAILY_BT depth floor for 10 roots — CL/NG ohlcv-1m alone run ~$26.8 and
~$19.4 per year at list (measured rates: CL $207.55/7.75y, NG
$111.64/5.75y). A buys: 10-symbol IBKR-overlap validation breadth +
true-volume 1m for 18m (9m CL/NG).

**Variant pkgA-v1 (kept, fully measured): 24m for the 8 cheaper roots + 12m
CL/NG: 112,561,252 records · 13.60 GB · $139.12 list · $129.57 get_cost —
meets the >=24m floor for 8/10 roots (30/50 hypotheses' vendor floors met
under the LITERAL headline policy — 31/50 under the 24m-default comparison,
the difference being 6E-H5; 12 unsupported (literal): all CL/NG depth +
CL-H3 (RB/HO legs outside the corpus) + NQ-H5 BBO + SI-H2's 10y floor +
6E-H5's >=2019 floor).**
+$39 over the $100 scenario buys the 24m floor — owner decision.

### Package B — "10 symbols, deeper history within ~$600" (restructured)

| line | schema | window | records | billable GB | get_cost |
|---|---|---|---|---|---|
| B-O1M-NQ / ES | ohlcv-1m | 2010-06-06..2026-10-02 (full) | 7,332,132 / 8,712,384 | 0.411 / 0.488 | $26.77 / $31.81 |
| B-O1M-CL | ohlcv-1m | 2019-01-01..2026-10-02 | 52,946,818 | 2.965 | $193.30 |
| B-O1M-NG | ohlcv-1m | 2021-01-01..2026-10-02 | 28,480,320 | 1.595 | $103.98 |
| B-O1M-{GC,SI,6E,6J,6B,6A} | ohlcv-1m | 2019-01-01..2026-10-02 | 8,564,425 / 5,643,217 / 3,922,578 / 3,538,979 / 3,139,130 / 3,262,175 | 0.480/0.316/0.220/0.198/0.176/0.183 | $31.27/$20.60/$14.32/$12.92/$11.46/$11.91 |
| B-definition-ALL10 | definition | 2019-01-01..2026-10-02 | 28,146,189 | 14.64 | $23.17 |
| B-statistics-ALL10 | statistics | 2019-01-01..2026-10-02 | 159,891,069 | 12.79 | $11.91 |
| B-BBO1M-NQ | bbo-1m | 2024-10-01..2026-10-01 (2y) | 2,533,685 | 0.203 | $3.40 |
| B-BBO1M-CL-ROLLWINDOWS | bbo-1m | enumerated monthly roll windows, raw symbols | DERIVED (96 windows) | DERIVED | **$1.25 DERIVED** (anchor $0.0130/window) |

**Totals B: measured lines only — 316,113,101 records · 34.66 GB billable ·
$533.45 list · $496.81 get_cost; all-in incl. the DERIVED roll-window bbo
line — $534.79 list · $498.06.**
Coverage starts: 2010-06-06 (NQ, ES) / 2019-01-01 (CL, GC, SI, 6E, 6J, 6B,
6A) / 2021-01-01 (NG). BBO: NQ 2y continuous + CL roll windows. Trades: NO.
**UNSUPPORTED in B: 2 of 50 — SI-H2** (>=10y two-leg ratio-reversion floor;
SI+GC at 2019+ = 7.75y) **and CL-H3** (RB/HO product legs explicitly
outside the 10-root corpus, in NO package — a future RB/HO bundle would be
its own request line + quote round). Vendor floors otherwise met for 40/42
vendor-gated hypotheses. Optional add-on quoted: continuous CL parent
bbo-1m 12m =
**$92.97** (far-month books dominate; only if owner wants CL quote depth
beyond roll windows — would put B at ~$590 get_cost). REJECTED
(rejected_alternative, measured): CL parent bbo-1m continuous 2y = $194.40.

### Package C — "longest feasible history, no cost cap" (restructured)

| line | schema | window | records | billable GB | get_cost |
|---|---|---|---|---|---|
| C-ohlcv-1m-ALL10 | ohlcv-1m | 2010-06-06..2026-10-02 | 219,903,747 | 12.31 | $802.82 |
| C-definition-ALL10 | definition | 2010-06-06..2026-10-02 | 51,421,562 | 26.74 | $42.33 |
| C-statistics-ALL10 | statistics | 2010-06-06..2026-10-02 | 262,303,361 | 20.98 | $19.54 |
| C-BBO1M-NQ | bbo-1m | 2010-06-06..2026-10-02 | 17,387,590 | 1.39 | $23.32 |
| C-BBO1M-CL-ROLLWINDOWS | bbo-1m | full-era monthly roll windows | DERIVED (~196) | DERIVED | **$2.54 DERIVED** |

**Totals C (measured lines): 551,016,260 records · 61.43 GB billable ·
$953.50 list · $888.02 get_cost** (+ ~$2.54 DERIVED). Coverage starts:
2010-06-06 for ALL 10 roots. BBO: NQ full era + CL roll windows. Trades: NO.
**UNSUPPORTED in C: 1 of 50 — CL-H3 only** (RB/HO product legs outside the
10-root corpus, in NO package); all in-corpus vendor floors met incl.
SI-H2's 10y (SI+GC full era = 16.3y).
REJECTED (measured, kept as evidence): CL parent bbo-1m full = 707,977,896
records / 56.64 GB / $1,019.49 list — far-month quote noise no hypothesis
needs; buying it would nearly double C for nothing. Per-root ohlcv-1m
full-era record counts: NQ 7,332,132 · ES 8,712,384 · CL 88,789,061 · NG
61,393,041 · GC 15,820,465 · SI 10,268,845 · 6E 7,758,788 · 6J 6,976,727 ·
6B 6,286,220 · 6A 6,566,084 (all > 0; CL/NG dominate; sum reconciles
exactly with the joined line).

### Quote validity & billing exclusions (per API responses)

- Quotes captured 2026-10-02 (this run); **no documented validity window**
  — re-probe exact chunk params before each spend gate (manifest rule).
- billable size is UNCOMPRESSED DBN bytes; vendor caveat: estimates may be
  inaccurate for windows that are not multiples of 10 minutes (all quoted
  windows are whole UTC days; ends EXCLUSIVE).
- Credits ($125 signup class), account fees, usage-page arithmetic:
  NOT_RUN_DOC_UNCLEAR — no verifiable account endpoint exists; credits are
  not free spend and are not assumed anywhere here.
- get_cost/list ratio 0.9313 observed on 31/31 lines this round;
  undocumented mechanism; both numbers reported throughout.

## 4. DISK GATE (measured NOW; assumptions labeled ASSUMED)

`df`/statvfs of the destination filesystem (`~/.my-quantitative-data`, same
volume as `/System/Volumes/Data`), captured 2026-10-02T11:12:30Z:
**228 GiB total · 164 GiB used · 21.65 GiB available (23.25 GB decimal) ·
89% full · current data dir usage 3.7 GB.** Usable at the mandated >=20%
reserve: **18.6 GB**. On-disk raw (zstd DBN) ASSUMED 0.4-0.6 x billable
(vendor publishes no ratios); parquet ASSUMED 0.5-1.0 x billable; scratch
ASSUMED <= 1.0 x raw-compressed, concurrent during transform; peak =
raw + parquet + scratch. No deletions, no auto-purge (raw is kept).

| package | billable GB | peak usage GB (ASSUMED range) | verdict vs 18.6 GB usable |
|---|---|---|---|
| PILOT (already queued, NQ/CL) | 2.20 | 2.9 - 4.8 | **FITS** |
| pkgA (v2) | 8.61 | 11.2 - 18.9 | **CONDITIONAL_FITS** (no headroom at unfavorable compression) |
| pkgA-v1 variant | 13.60 | 17.7 - 29.9 | **CONDITIONAL_FITS / DOES_NOT_FIT at high end** |
| pkgB | 34.66 (+~0.07 DERIVED) | 45.1 - 76.3 | **DOES_NOT_FIT** |
| pkgC | 61.43 (+~0.14 DERIVED) | 79.9 - 135.1 | **DOES_NOT_FIT** |

This CONFIRMS and refines the earlier ~54 GB-billable vs ~22-33 GB-free
context: **the internal volume cannot hold B or C even before parquet.**
Required before any B/C spend: an external drive (proposal: a dedicated
volume mounted at `~/.my-quantitative-data/futures-10syms-v1/` with its own
df re-measured at delivery time, >=150 GB free for C's worst case) — owner
decision. **Bounded PILOT-first sequencing after budget:** PILOT (FITS,
~$3.3-3.5, acceptance bar per DATA_ACCEPTANCE_CHECKLIST) -> pkgA (or v1)
only after pilot acceptance -> B/C only after external storage exists.
**Checkpoint plan (restated binding):** chunk = (root, schema, calendar
quarter) for full lines / enumerated window for bbo roll lines; SUBMITTED-
first completion ledger; per-batch SHA256 manifests, immutable; idempotent
re-request dedupe (same exact params -> same chunk, never re-bought;
one-owner rule); resume-from-checkpoint by enumerating the recorded batch
job's files instead of blind resubmission.

## 5. PRIORITY ORDER (roots first) & pilot relationship

1. **PILOT NQ+CL (already queued separately in
   `data/request/request_manifest.json` PILOT-01..06, ~$3.3-3.5)** — NOT
   duplicated into A/B/C. Relationship: A/B/C full lines OVERLAP the
   pilot's NQ/CL definition/statistics windows; at delivery time the
   one-owner rule carves pilot-delivered chunks out of A/B/C (overlap is
   small: def NQ+CL 2024-12+ ~1.3 GB/$2.2 list; stat NQ+CL 2025-08+
   ~0.9 GB/$0.9). Package quotes above do NOT subtract this overlap.
2. **NQ, CL, ES** (pilot continuity + the deepest hypothesis density:
   event/gap/overnight/roll classes; NQ/ES full history is cheap:
   ~$26.8+$31.8 get_cost each for 16.3y).
3. **GC, SI, 6E, 6J, 6B, 6A** (2019+ tier; enables 40/42 in-corpus vendor
   floors in B — the residual two are SI-H2's 10y floor and CL-H3's
   out-of-corpus RB/HO legs).
4. **NG** (2021+ tier in B; intraday depth is the H1 constraint — 5.75y
   meets the >=5y/100-event floor at the lowest cost).
5. Depth-to-2010 for CL/NG/minors (C) only after external storage + SI-H2's
   10y floor actually matters to the owner.

## 6. Remaining NON-vendor blockers (restated; data purchase clears NONE)

Declared slippage (NO declared value exists; owner must declare nonzero
USD/contract/side) · exchange fees NOT_FETCHED 9/10 (only ES documented
$2.24 all-in) · real holiday calendar source · consensus/expectations
archives (NQ-H3, ES-H3, CL-H2/H3, NG-H1, GC-H2, 6E-H3, 6B-H2-class;
vendor does not sell) · macro/weather vintages (ALFRED, NOAA bounded
2020-04-16+, EIA) · CFTC CoT retrieval (free, unfetched) · MOF intervention
lag (6J) · HG copper / iron-ore proxies (6A-H2) · spx dividend yield (ES-H2)
· IBKR serial re-fetch deadlines (GCX5 NOW; 6JF6/6BF6/6AF6 ~Dec-2026)
· registration + owner GO for anything scored. Full per-symbol chains:
SYMBOL_READINESS.md (re-measure before relying).

## 7. NOT_RUN / limitations

- Exact per-day coverage start dates NOT_RUN: earliest evidence is the
  first-hit refinement band 2010-06-06..2010-12-06 per root x schema; no
  day-level probes were spent (band resolution is sufficient for package
  design; full-window record counts were measured directly).
- CL/NG bbo-1m roll-window DERIVED costs are anchored on ONE measured
  window ($0.0130); exact per-window enumeration needs delivered
  definitions + the declared roll table — re-quote before spend.
- Windows are quoted at package granularity; quarter-chunk additivity is
  verified (bytes = count x record size) but per-quarter splits are
  computed at delivery time, re-quoted per chunk before each spend gate.
- No account/credits endpoint exists (NOT_RUN_DOC_UNCLEAR); $125-credit
  arithmetic excluded on purpose.
- ohlcv-1s/1h/1d, status, tbbo, mbp-1, mbo not quoted (no hypothesis
  needs them this round; manifest discipline).
- Disk peak ranges are ASSUMED (labeled); vendor publishes no compression
  ratios — measure at pilot and re-project (manifest rule).

## 8. Provenance

- **Post-audit corrections (2026-10-02, per audit/acq_skeptic/
  ACQ_SKEPTIC_AUDIT.md — PASS_WITH_FINDINGS; disclosed minimal edits,
  no re-requests, all raw evidence unchanged):** MAJOR-1 support verdicts
  re-derived per-requirement-symbols (CL-H3 [RB,HO legs] now UNSUPPORTED in
  every package; headline counts B 40/2, C 41/1, A-v1 30/12 literal);
  MINOR-1 floor policy stated + dual-counted (A-v1 31/11 under the 24m
  default); MINOR-2 CL roll-window count aligned to 96 (12/yr x 8y, the
  code/manifest multiplier, safe direction; DERIVED $1.25 unchanged);
  MINOR-3 coverage claims restated at band precision. Audit namespace is
  read-only to this lane and was not touched.
- `coverage_results.json`: 238 timestamped requests (round 1: 195 via
  acq_probe.py, 194x200 + 1x422 symbology date-range; round 2: 43 via
  acq_probe_followup.py, all 200), payloads, redacted errors, disk
  snapshot, coverage grid, package quotes, cl_bbo anchors, symbology fix
  validation.
- Unit prices: live `metadata.list_unit_prices` this run (matches
  METADATA-PROBE capture).
- Hypothesis floors: `configs/symbols/*.yaml` (STRATEGY-CONFIGS lane,
  2026-10-02) + `analysis/strategy_lane/coverage_summary.md`; support
  verdicts computed in `finalize_analysis.py` -> `analysis_summary.json`.
- sha256 of every artifact in `dispatch/handoff_ACQ-OPT.json`.
