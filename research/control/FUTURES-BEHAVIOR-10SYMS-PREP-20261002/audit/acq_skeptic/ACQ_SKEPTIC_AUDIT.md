# ACQ_SKEPTIC_AUDIT — independent skeptic audit of the ACQ-OPT lane

Task `FUTURES-BEHAVIOR-10SYMS-PREP-20261002` · lane `ACQ-SKEPTIC` (fresh-context,
read-only) · 2026-10-02 (UTC). Audited checkout: worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` at HEAD
`8ce10f7e4b43a0234f33d27fb8e4532b7ff65f9e` (branch
`prep/futures-behavior-10syms-20261002`), ACQ-OPT outputs as uncommitted
additions. This lane fixed nothing; findings only. Recomputation scripts live in
this directory (`recompute_01_requests_cost_math.py`,
`recompute_02_hypothesis_support.py`); every number below was re-derived
offline from the artifacts themselves (zero network calls by this audit).

Scope audited: `acquisition_optimization/` (acq_probe.py,
acq_probe_followup.py, finalize_analysis.py, coverage_results.json,
coverage_results_round1_asrun.json, analysis_summary.json,
ACQUISITION_OPTIMIZATION.md, package_manifests/{pkgA,pkgA_variant_24m_floor,
pkgB,pkgC}.json, probe_run.log, followup_run.log) + `dispatch/handoff_ACQ-OPT.json`.

---

## Verdict

**PASS_WITH_FINDINGS** — 0 BLOCKER, 1 MAJOR, 3 MINOR, 6 NOTE.

The lane's load-bearing claims reconcile: identity (dataset/stype/schemas/
roll-window pinning/past-only front selection), request accounting (238/260,
237x200 + 1x422 typed), record-size math (bytes == records x DBN size on
41/41 measured package lines + 45/45 request pairs), get_cost/list ratio
0.9313 (recomputed 0.931323 on 41/41 lines + 2 anchors), package totals
(A 92.04/85.72, A-v1 139.12/129.57, B 534.79/498.06 all-in, C 953.50/888.02
measured-only + 2.54/2.73 DERIVED), disk-gate arithmetic (peaks and all five
verdicts reproduce exactly), and hygiene (no credentials, no bulk payloads,
tree clean apart from expected lanes). ONE MAJOR defect: the hypothesis-support
engine evaluates cross-symbol requirements on the hypothesis's own root, so
**CL-H3 (requires RB/HO legs, explicitly outside the 10-root corpus) is
mislabeled SUPPORTED in pkgB and pkgC** — the headline counts "B: 1 of 50
unsupported" and "C: 0 of 50" are wrong; correct counts are **B: 2 (SI-H2,
CL-H3)** and **C: 1 (CL-H3)**. This changes the owner's package-comparison
numbers and must be corrected before any budget decision consumes them.

---

## 1. IDENTITY — PASS

- Dataset: every package line in all four manifests carries
  `"dataset": "GLBX.MDP3"` (pkgA.json:31 etc.); no other dataset string
  appears anywhere in the namespace (grep over package_manifests: 0 non-GLBX
  hits). Venues: correct by construction — GLBX.MDP3 is the single dataset
  covering all four CME Group venues (request_manifest.json
  `vendor_context.venues_covered` = CME/CBOT/NYMEX/COMEX, with per-root venue
  table); no per-line venue parameter exists or is needed.
- Schemas: `ohlcv-1m`, `bbo-1m`, `statistics`, `definition` all exist in the
  frozen adapter spec (`code/futbt/dbn/spec.py:168-175`, SCHEMA_OHLCV_1M,
  SCHEMA_BBO_1M, SCHEMA_STATISTICS, SCHEMA_DEFINITION) and were live-quoted
  with HTTP 200 this run. Record sizes 56/80/80/520 B confirmed at
  spec.py:372 (56), 396/517 (80), 485 (520).
- stype discipline: full lines are `stype_in: parent` on `{ROOT}.FUT`;
  continuous/CONTFUT series are NEVER purchased — `delivery_notes
  .continuous_series` in every manifest; `data/request/request_manifest.json
  conventions.stype_policy.continuous` ("NEVER purchased as a price series...
  feature-only, never fills/MTM"). No adjusted fill series anywhere.
- Symbols: all lines resolve the 10 roots via parent (10 parents enumerated
  in the joined lines; per-root lines use exactly the root's parent). The 10
  roots match the cycle's symbol set.
- Roll-window BBO pinning: `B-BBO1M-CL-ROLLWINDOWS` / `C-BBO1M-CL-ROLLWINDOWS`
  are `stype_in: raw_symbol` on "enumerated front+next raw symbols per
  monthly roll" (pkgB.json:271-286, pkgC.json:125-140), anchored on the
  measured window CLN6,CLQ6 2026-06-24..2026-07-03 (coverage_results.json
  `cl_bbo_anchors.roll_window_anchor`, stype raw_symbol). The CL PARENT bbo
  line (the far-month-noise one) was measured, REJECTED, and kept only as
  `rejected_alternative`/`optional_addon` (pkgC.json:143-147; pkgB.json:288-292
  labeled "OPTION"). Billed bbo = actual contract windows, not parent bbo.
- Serial dead books: ohlcv/bbo/trades lines contain no serial-dead-book lines
  by design; dead serials ride along only inside parent-scoped definition/
  statistics where they emit no trades bars (ACQUISITION_OPTIMIZATION.md:76-79).
  See NOTE-5 for the residual NQ-parent-bbo nuance.
- Front selection past-only with crossover history preserved: stated at
  ACQUISITION_OPTIMIZATION.md:87-90 (statistics OI/volume, OI for session t
  observable t+1) and consistent with the request_manifest `conventions
  .roll_policy` (roll built by us from per-contract data + definition
  expiration; vendor c/n/v tables are measurement objects only).

## 2. COVERAGE / PIT — PASS (one precision nit -> MINOR-3)

- Earliest-band logic: acq_probe.py:385-445 probes a 5-band ladder oldest-first
  (W1 2010-06-06..2011-06-06 ... W5 2019..2022), first window with records>0
  sets the band, then ONE half-year refinement (183 days, refine_start(),
  acq_probe.py:379-382). Recomputed from coverage_results.json: all 40 cells
  (10 roots x 4 schemas) first-hit W1 and all 40 W1R refinement probes
  returned records>0; `earliest_band` histogram = {"2010-06-06..2010-12-06":
  40}. The claim "every cell has records in the refinement window" is exactly
  what the probes show — no claim beyond probes at cell level.
- Latest month: all 10 roots current in 2026-09-01..2026-10-02 with plausible
  counts (NQ 55,801 ... CL 976,594), end-exclusive semantics stated
  (acq_probe.py:95-96). Verified against `latest` block.
- Era caveats present and sourced: FIX/FAST pre-May-2017, ms-only timestamps
  pre-2015-11-20, no ts_recv pre-2017-05-21 (ACQUISITION_OPTIMIZATION.md:66-70,
  sourced request_manifest `vendor_context.pre_2017_quality_notes`); stat_flags
  normalization pre-2015-01-20 (ACQUISITION_OPTIMIZATION.md:71-74, sourced to
  the vendor roadmap issue via DBN-ADAPTER lane README, access-dated).
- No metadata->quality inference: handoff known_limitations explicitly says
  bbo earliest-band probes "prove records exist in 2010H2; quote-book quality
  in the FIX/FAST era (pre-2017) is unverified until real delivery QA";
  ACQUISITION_OPTIMIZATION.md:76 labels ohlcv sparsity as expected behavior,
  not holes.
- MINOR-3 (below): the summary lines "Oldest COMMON window ... == 2010-06-06"
  and "No root, no schema starts later than the dataset itself" state
  band-resolution evidence (start <= 2010-12-06) as exact-date equality.

## 3. DUPLICATE COST — PASS

- No 1d/1h vendor lines in any package (all manifests `delivery_notes
  .daily_hourly`: "aggregated LOCALLY from ohlcv-1m — no ohlcv-1d/1h lines,
  no duplicate billing"); verified no ohlcv-1d/ohlcv-1h schema lines exist in
  any manifest. The UTC-day vs session-day ambiguity rationale matches
  request_manifest `timezone_and_session_notes`.
- PILOT vs packages: PILOT-01..06 remain separate; A/B/C do not contain pilot
  lines; overlap quantified (def NQ+CL ~1.3 GB/$2.2, stat NQ+CL ~0.9 GB/$0.9)
  and explicitly NOT subtracted (ACQUISITION_OPTIMIZATION.md:253-259). See
  NOTE-3 on the carve-out mechanism.
- bbo double-billing: none — CL bbo appears exactly once per package (roll
  windows, DERIVED-labeled) with the parent alternative rejected/optional and
  outside totals; NQ bbo is a single parent line per package.
- DERIVED lines: labeled `cost_basis: DERIVED...` with null record/byte
  counts (pkgB.json:281-285, pkgC.json:134-139); pkgB totals include it once
  as "all-in" with measured-only also stated (pkgB.json:28, `totals_note`);
  pkgC totals exclude it and note it separately (pkgC.json:142). Not billed
  twice. (Asymmetry -> NOTE-2.)
- Record math (spot checks, all recomputed):
  - A2-O1M-NQ: 789,572 x 56 = 44,216,032 == quoted (pkgA.json:41-42)
  - A2-O1M-CL: 7,992,734 x 56 = 447,593,104 == quoted (pkgA.json:74-75)
  - A2-definition-ALL10: 8,299,169 x 520 = 4,315,567,880 == quoted (pkgA.json:219-220)
  - B-statistics-ALL10: 159,891,069 x 80 = 12,791,285,520 == quoted (pkgB.json:247-248)
  - C-BBO1M-NQ: 17,387,590 x 80 = 1,391,007,200 == quoted (pkgC.json:118-119)
  - CL roll anchor: 9,671 x 80 = 773,680 == quoted (coverage_results cl_bbo_anchors)
  Aggregate: 41/41 measured package lines satisfy bytes == records x size;
  45/45 matched rc/bs request pairs (recompute_01). pkgC per-root ohlcv counts
  sum to exactly 219,903,747 == the joined line (pkgC.json:149-200 vs :49).
- DERIVED arithmetic: anchor get_cost $0.012969821692 x 96 = $1.2451 -> $1.25
  (pkgB.json:283); x 196 = $2.5421 -> $2.54 (pkgC.json:137); list
  $0.0139262 x 96 = $1.3369 -> $1.34 and x 196 = $2.7295 -> $2.73. All
  reproduce. (Window-count wrinkle -> MINOR-2.)
- get_cost/list ratio: recomputed 0.931323 (rounds to 0.9313) on 41/41
  measured package lines AND both anchors — stronger than the claimed 31/31
  (which counts only round-1-quoted lines). Documented as observed with
  "mechanism undocumented", get_cost treated as authoritative, both numbers
  reported throughout, "no documented validity window — re-probe before each
  spend gate" (ACQUISITION_OPTIMIZATION.md:123-130, 204-215). Observed-not-
  guaranteed framing: correct.
- Package totals recomputed from line data: A 68,201,296 rc / 8.6083 GB /
  $92.04 / $85.72; A-v1 112,561,252 / 13.6019 / $139.12 / $129.57; B
  316,113,101 / 34.6604 / $534.79 / $498.06 (all-in; measured-only
  533.45/496.81 = all-in minus DERIVED); C 551,016,260 / 61.4291 / $953.50 /
  $888.02 measured-only (+$2.73/$2.54 DERIVED). All match stored totals and
  the MD. Per-year claims check: CL $207.551527/7.75y = $26.78/y, NG
  $111.642854/5.75y = $19.42/y ("~$26.8 and ~$19.4",
  ACQUISITION_OPTIMIZATION.md:147-149); NQ/ES full-era get_cost $26.77/$31.81
  over 16.32y (line 262-263) matches the B lines.

## 4. DISK PEAK — PASS (all verdicts reproduce)

- Measured free space: statvfs of ~/.my-quantitative-data captured
  2026-10-02T11:12:30Z: available 23,249,338,368 B = 23.25 GB decimal =
  21.65 GiB; df: 228Gi/164Gi/22Gi/89%; du 3.7G. Usable at 20% reserve =
  23.25 x 0.80 = 18.60 GB. Recomputed identical (recompute_01).
- Peak model: raw 0.4-0.6x billable + parquet 0.5-1.0x + scratch <= 1.0x raw,
  concurrent; peak_lo = 2*raw_lo + pq_lo, peak_hi = 2*raw_hi + pq_hi
  (finalize_analysis.py:149-165). All ASSUMPTION ratios are labeled ASSUMED
  with "vendor publishes no compression ratios — measure at pilot and
  re-project". Recomputed:
  - PILOT 2.1999 GB (traced to METADATA-PROBE DATABENTO_METADATA_PROBE.md:264
    "billable size: 2.1999 GB"): peak 2.86-4.84 -> FITS (4.84 <= 18.6). OK.
  - pkgA v2 8.6083: raw 3.44-5.16, pq 4.30-8.61, peak 11.19-18.94 ->
    CONDITIONAL_FITS (11.19 <= 18.6 < 18.94). Matches MD "11.2 - 18.9 ...
    no headroom at unfavorable compression". OK.
  - pkgA-v1 13.6019: peak 17.68-29.92 -> CONDITIONAL_FITS / DOES_NOT_FIT at
    high end. OK.
  - pkgB 34.6604: peak 45.06-76.25 -> DOES_NOT_FIT (lo 45.06 > 18.6). OK.
  - pkgC 61.4291: peak 79.86-135.14 -> DOES_NOT_FIT. OK.
- External-drive requirement for B/C: follows — even the FAVORABLE end
  exceeds usable by 2.4x (B) / 4.3x (C); the proposal (dedicated volume,
  re-measured df at delivery, >=150 GB free for C's 135.1 GB worst case)
  is correctly sized with margin.
- No deletion/purge assumptions: "No deletions, no auto-purge (raw is kept)"
  (ACQUISITION_OPTIMIZATION.md:226); peak model keeps raw+parquet+scratch
  concurrently. Confirmed nowhere does any projection assume reclaiming space.
- Reserve interpretation -> NOTE-4.

## 5. SUPPORTED / UNSUPPORTED — ONE MAJOR DEFECT

Independent re-derivation (recompute_02): all 50 hypotheses, vendor classes
{daily_trades_per_contract, minute_trades_m1, full_session_globex_intraday,
synchronous_bbo}, floors from the yaml floor strings (24m default; SI-H2
">=10y two-leg daily" -> 120m, confirmed 2x in SI.yaml; NG-H1 "M1 >=5y" ->
60m, confirmed in NG.yaml), package windows from the manifests.

- Counts that DO reconcile: A = 42 UNSUPPORTED + 8 NOT_VENDOR_GATED (8 NVG
  set independently confirmed: 6A-H5, 6B-H2, 6E-H2, 6J-H3, ES-H2, GC-H5,
  NG-H5, SI-H3); A-v1 = 31/11/8; the 11 A-v1 unsupported = CL-H1..H5,
  NG-H1..H4, NQ-H5, SI-H2 — independently reproduced.
- Spot checks (10 hypotheses x 4 packages, all agreeing with stored verdicts
  except CL-H3): SI-H2 (120m floor; B 93.01m UNSUPPORTED, C 195.88m
  SUPPORTED — SI.yaml floor ">=10y two-leg daily" matches the 120m override);
  NG-H1 (60m floor; B NG 68.99m SUPPORTED, A-v1 11.99m UNSUPPORTED); NQ-H5 /
  CL-H5 synchronous_bbo (absent in A/A-v1 -> UNSUPPORTED with reason "no
  bbo-1m line in package"; present in B/C); CL-H1, GC-H2, ES-H4, 6J-H5, NG-H3
  depth verdicts all reproduce.
- **MAJOR-1 — CL-H3 is mislabeled SUPPORTED in B and C.** CL.yaml CL-H3
  requirements are `daily_trades_per_contract` on symbols **[RB, HO]** with
  floor "RB/HO product futures NOT in snapshot" / "product futures multi-year"
  and an explicit note "class daily_trades_per_contract on symbols outside
  the 10-sym corpus" (CL.yaml:248-249, 255; feasibility "needs RB/HO bundle").
  finalize_analysis.py:96-98 evaluates depth floors on `root =
  hyp_id.split("-H")[0]` — the hypothesis's OWN symbol (CL) — instead of the
  requirement's symbols, so CL's 93.01m window in B "covers" RB/HO legs that
  are in NO package. Correct verdicts: CL-H3 UNSUPPORTED in ALL packages;
  counts become **B: 40 SUPPORTED / 2 UNSUPPORTED (SI-H2, CL-H3)** and
  **C: 41 SUPPORTED / 1 UNSUPPORTED (CL-H3)**. Wrong headlines that must be
  corrected: ACQUISITION_OPTIMIZATION.md:175-176 ("UNSUPPORTED in B: 1 of
  50"), :195 ("UNSUPPORTED in C: 0 of 50"), :263 ("enables 41/42 floors in
  B" -> 40/42); handoff_ACQ-OPT.json summary/findings/test digest ("41/42
  vendor floors met", "pkgC ... 0 unsupported", "B 41 (1 unsupported...)",
  "C 42/42"). Not spend-authorizing, but these numbers feed the owner's
  budget decision, hence MAJOR.
- MINOR-1 — floor simplification: DEFAULT_FLOOR 24m is applied to floors that
  say more. 6E-H5's full_session floor is "M1 depth >=2019 covering full 23h
  Globex" (6E.yaml:261); A-v1's 6E window starts 2023-10-01, so under the
  literal floor 6E-H5 is NOT met in A-v1, but finalize marks SUPPORTED
  (A-v1 would be 30/12/8, not 31/11/8). NG-H4's ">=3y" (36m) floor
  (NG.yaml:218,223) is also mapped to 24m — no verdict flips there (B NG
  5.75y clears both; A/A-v1 fail both). Under the workspace's conservative
  law (never infer PASS), ambiguous floors should bind at their literal text.
- Worst-case-bound execution law (no tick resolution needed): consistent.
  `same_bar_tp_sl_worst_case_bound_no_point_pnl` is a schema CONST
  (configs/schema.json:103,277), set in every symbol config and
  configs/pilot_nq_cl.yaml:77, and implemented as stated in
  code/README.md:50 ("same-bar TP+SL -> AMBIGUOUS_ORDER (ledger books
  worst-case bound)"). Trades/ticks excluded from all packages with the
  consequence stated plainly (future intrabar-order need = UNSUPPORTED,
  separate quote round). SI-H5's "no tick model covers" note is respected.

## 6. HYGIENE — PASS

- Credential scan: `grep -rE 'db-[A-Za-z0-9_-]{12,}'` and
  `grep -rE 'Basic [A-Za-z0-9+/=]{16,}'` over the whole
  acquisition_optimization/ namespace -> 0 matches (exit 1). The only
  "Authorization" strings are the header-NAME in code
  (`req.add_header("Authorization", ...)`) and doc prose; no key material,
  no base64 credentials. Key path is read in-process from the owner 0600
  file outside the repo (acq_probe.py:56-58,164-176).
- Request count: coverage_results.json `request_count` = 238, len(requests)
  = len(order) = 238, no duplicate rids, no SKIPPED_CAP, cap_exhausted false.
  Phase split recomputed: round 1 = P0 1 + P1 80 + P2 10 + P3 103 + P4 1 =
  195 (probe_run.log tail: "195 logical requests (194 ok, 1 non-200), cap
  260 (honored)"); round 2 = P4F 1 + P3F 42 = 43; total 238 <= 260. Statuses
  237x200 + 1x422 (P4-SYMRES, typed data_start_date_before_available_start_
  date — exactly as disclosed). 238/260 claim: consistent.
- Zero data download: no file in the namespace exceeds 1 MB (find -size +1M:
  empty); coverage_results.json is 281 KB for 238 requests — metadata-sized
  payloads only (counts, sizes, costs, symbology interval lists). Endpoint
  histogram is metadata/symbology-only (get_record_count 145,
  get_billable_size 45, get_cost 45, list_unit_prices 1, symbology.resolve
  2). No timeseries/batch/live endpoints called.
- Tree state: `git status --porcelain` at audit start showed exactly 4
  untracked entries — acquisition_optimization/, dispatch/handoff_ACQ-OPT.json
  (this round's expected ACQ-OPT additions) plus dispatch/NONPRICE_DISPATCH
  .json and nonprice_acquisition/ (sibling lane, disclosed in ACQ-OPT's own
  tree_status as other-lane, untouched). No tracked-file modifications.
- Handoff sha256 binding: all 14 outputs' sha256 recomputed — 14/14 match
  handoff_ACQ-OPT.json outputs exactly. changed_paths all exist.
- Defect disclosure honesty: coverage_results_round1_asrun.json verified to
  preserve the as-run round-1 state (request_count 195; pkgA totals list
  $139.12 with get_cost 0.0 / lines_with_get_cost 0 — i.e. the disclosed
  float-aggregation bug), and the final coverage_results.json carries the
  recovered values. The two disclosed defects are real and were handled
  without re-requests.

---

## Findings register

| # | Severity | Finding | Evidence |
|---|---|---|---|
| MAJOR-1 | MAJOR | CL-H3 (RB/HO legs outside the 10-root corpus) marked SUPPORTED in pkgB/pkgC; correct counts B 40/2, C 41/1. Headline claims "B: 1 of 50", "C: 0 of 50", "41/42 floors in B" are wrong. Root cause: finalize_analysis.py:96-98 keys depth floors on hyp's own root, not the requirement's symbols. | CL.yaml:248-255; analysis_summary.json B/CL-H3 + C/CL-H3 = SUPPORTED; ACQUISITION_OPTIMIZATION.md:175,195,263; recompute_02 (mine B={40,8,2}, C={41,8,1}) |
| MINOR-1 | MINOR | 24m default floor overrides literal yaml floors: 6E-H5 "M1 depth >=2019" and NG-H4 ">=3y". 6E-H5 flips A-v1 SUPPORTED->UNSUPPORTED under literal reading (A-v1 31->30). | 6E.yaml:261; NG.yaml:218,223; finalize_analysis.py:49-56 |
| MINOR-2 | MINOR | CL roll-window count inconsistency: MD says "~93 monthly roll windows 2019..2026", manifest/code use x96 (12x8). Cost impact +$0.04 (over-estimate, safe direction). | ACQUISITION_OPTIMIZATION.md:101,168 vs pkgB.json:285; acq_probe_followup.py:370 |
| MINOR-3 | MINOR | Coverage summary lines state exact equality ("oldest common window == per-symbol longest == 2010-06-06"; "no root, no schema starts later than the dataset itself") while the probe method resolves only to the 2010-06-06..2010-12-06 band. Table itself is honest ("earliest band"). No package/quote impact (record_count measured on full windows). | ACQUISITION_OPTIMIZATION.md:38-40,55-58 vs method :31-36; handoff summary |
| NOTE-1 | NOTE | synchronous_bbo support check is has-line/has-not, not window-length-aware; B's NQ bbo window (2024-10-01..2026-10-01 = 24.0m) happens to meet the >=2y floor so no current verdict is wrong. | finalize_analysis.py:84-95; pkgB.json:254-263 |
| NOTE-2 | NOTE | Totals basis asymmetry: pkgB totals are all-in (include DERIVED 1.25/1.34) while pkgC totals are measured-only (+2.54/2.73 noted). Both labeled in place; MD reports both correctly. | pkgB.json:19-28 vs pkgC.json:18-27,142 |
| NOTE-3 | NOTE | Pilot-vs-package overlap carve-out relies on a declared manual rule; the "idempotent re-request dedupe by exact params" cannot catch it automatically (pilot lines are raw_symbol event windows; package chunks are parent/quarter — different param shapes). Disclosed, overlap not subtracted. | ACQUISITION_OPTIMIZATION.md:253-259,244-249 |
| NOTE-4 | NOTE | 20% reserve computed as 80% of currently-available (18.6 = 0.8 x 23.25). An alternative "keep 20% of the volume free" reading would permit nothing (volume already 89% full). Interpretation is stated explicitly and applied consistently. | finalize_analysis.py:131-137; ACQUISITION_OPTIMIZATION.md:219-224 |
| NOTE-5 | NOTE | NQ parent bbo-1m line carries far-month/serial books incidentally (the phenomenon measured and rejected for CL at 56.64 GB); front-book filtering is a delivery-time step. Billing math unaffected. | ACQUISITION_OPTIMIZATION.md:96-104,196-198 |
| NOTE-6 | NOTE | get_cost/list ratio verified stronger than claimed: 41/41 measured package lines + 2 anchors at 0.931323 (claim was 31/31 round-1 lines). | recompute_01 ratio histogram |

## What was NOT audited / limits

- Offline audit only: no live re-quote of any package line (would spend
  request budget); all numbers re-derived from the stored evidence, whose
  internal consistency (bytes == rc x size on every line; ratio constant;
  sha256 binding intact) is strong but is still vendor-metadata truth, not
  delivered-bytes truth — same limitation the lane itself declares.
- The DERIVED roll-window lines are anchor-times-count arithmetic; I verified
  the arithmetic and labeling, not the underlying per-window costs (by design
  they require delivered definitions + declared roll table).
- Floor-string semantics for ambiguous yaml floors (MINOR-1) involve judgment;
  I took the literal reading per the conservative-evidence law.
- I did not audit the nonprice lane or any other lane's outputs.

---

# DELTA_VERIFIED — post-audit fix verification (2026-10-02, second pass)

The implementer applied fixes for MAJOR-1 / MINOR-1 / MINOR-2 / MINOR-3. This
section records the independent re-verification (read-only; offline;
`recompute_03_delta.py` in this directory). **Delta verdict:
DELTA_VERIFIED — all four findings fixed; raw evidence untouched.**

## Per-finding status

| Finding | Status | Evidence |
|---|---|---|
| MAJOR-1 (CL-H3 / per-requirement-symbol floors) | **VERIFIED FIXED** | finalize_analysis.py (revised) `requirement_supported()` lines 108-137 now iterates THIS requirement's symbols; out-of-corpus symbol fails explicitly: stored B/CL-H3 reason = "daily_trades_per_contract[RB,HO]: RB: outside the 10-root corpus, in NO package; HO: outside the 10-root corpus, in NO package". Independently recomputed counts (recompute_03, both policies) match stored analysis_summary@2 EXACTLY: LITERAL — A 42 UNSUPPORTED + 8 NVG; A-v1 30 SUPPORTED / 12 UNSUPPORTED / 8 NVG; **B 40 / 2 (SI-H2, CL-H3) / 8; C 41 / 1 (CL-H3) / 8**; DEFAULT24 — A-v1 31/11/8, B and C identical to LITERAL. MD headlines corrected (ACQUISITION_OPTIMIZATION.md:141-142, 178-180, 203, 225, 296). |
| MINOR-1 (floor simplification) | **VERIFIED FIXED** | Dual floor policy implemented and disclosed: FLOOR_BASE (SI-H2 120m, NG-H1 60m — bind in both policies), FLOOR_LITERAL_EXTRA (NG-H4 ">=3y" = 36m; 6E-H5 "M1 depth >=2019" = 93m from 2019-01-01) binding in the LITERAL headline per the conservative-evidence law, DEFAULT24 comparison reported alongside; vague text rule ("multi-year" etc. -> 24m) labeled a disclosed policy choice (finalize_analysis.py:64-83; analysis_summary@2 `floor_policy`; MD:131-139). A-v1 dual-reported as 30 (literal) vs 31 (default) — matches my recompute. |
| MINOR-2 (93 vs 96 roll windows) | **VERIFIED FIXED** | 96 (12/yr x 8y) stated everywhere now, with the ~93 calendar-month count explicitly noted as the deliberately-not-taken lower figure: ACQUISITION_OPTIMIZATION.md:106-108 and :195 ("DERIVED (96 windows)"); DERIVED math unchanged and still exact ($1.2451->$1.25 gc, $1.3369->$1.34 list; 196-window $2.5421/$2.7295 -> $2.54/$2.73). |
| MINOR-3 (band-precision wording) | **VERIFIED FIXED** | ACQUISITION_OPTIMIZATION.md:56-61 now states "root x schema's first observed records fall inside the refinement band 2010-06-06..2010-12-06 (i.e., earliest valid date is within that band...)" with common==longest claimed only "at band resolution"; stale exact-equality strings ("== 2010-06-06", "common == longest") absent from the MD (grep-verified). |
| NOTE-4 (reserve interpretation) | **VERIFIED ADDRESSED** (beyond required) | `disk_gate.assumptions.reserve_interpretation` now documents the 0.8 x available reading and why the "20% of volume" reading would permit nothing (finalize_analysis.py:189-191). |
| NOTE-6 (ratio stronger than claimed) | **VERIFIED ADDRESSED** | MD:147-148 now cites the audit recomputation 41/41 lines + both anchors. |

## Integrity checks

- **coverage_results.json BYTE-IDENTICAL**: sha256
  319955b4b965217a71c1cf94a2b1f9c35896b245eccdf6a604d6246142de6a4d ==
  the original pre-fix value; the revised finalize_analysis.py asserts the
  two totals patches instead of rewriting the file (lines 222-228). Raw
  evidence preserved.
- **handoff_ACQ-OPT.json digests consistent**: all 13 outputs' sha256
  recomputed against the current files — 13/13 match; dispatch_sha ==
  actual_start_sha == 8ce10f7e...; post-audit corrections disclosed in
  `defects[2]` and a new post-audit rerun test entry (6 tests total);
  tree_status discloses this audit lane's outputs as other-lane/untouched.
  (Correction to my own original audit text above: the outputs list is 13
  files, not 14 — the original "14/14" was a counting typo in this
  document; the binding itself was and remains fully intact, 13/13 then
  and now.)
- **Scope discipline**: scripts acq_probe.py (7235b92f...), acq_probe_
  followup.py (7e20a2fc...), both run logs, round1-asrun artifact, and all
  four package manifests unchanged from the audited state — edits confined
  to finalize_analysis.py, analysis_summary.json (@1 -> @2),
  ACQUISITION_OPTIMIZATION.md, handoff_ACQ-OPT.json. Zero network requests
  in the fix (metadata evidence unchanged byte-for-byte).

**Delta verdict: DELTA_VERIFIED (4/4 findings fixed; A/A-v1/B/C support
counts now correct under both stated floor policies; raw evidence
byte-identical; handoff digests consistent).**
