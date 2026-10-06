# A7-DEEP-NQ — independent audit of `dossiers_v2/NQ_DEEP_v2.md` + `analysis/NQ_*`

- **Task:** FUTURES-DEEPRESEARCH-V2-20261003, lane A7-DEEP-NQ (fresh-context auditor; read-only on data; fixes nothing)
- **Worktree:** `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` @ `26d96eb4bdd4be85e151055dace3354638498a44`, branch `prep/futures-behavior-10syms-20261002` (DEEP outputs uncommitted, as disclosed)
- **Audited artifacts:** `dossiers_v2/NQ_DEEP_v2.md`, `analysis/NQ_a{1,2,3,4,5,7}*.{py,json}`, `analysis/NQ_cache/*`, `dispatch/handoff_DEEP-NQ.json`; cross-lane evidence `analysis/integration/nq2020_hole_probe.{md,json,py}` (INTEGRATION-FIX-V2)
- **Method:** 7 fresh recompute scripts in this directory (`r1..r7`, independent implementations, run against the lane caches, the raw vendor parquet at `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/AV1{R,T}-O1M-NQ*/`, and the fixed CoT tidy at `/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/normalized/cftc_legacy_tidy.parquet`). Raw JSON outputs sit next to the scripts.

## Verdict: **PASS_WITH_ERRATA**

No BLOCKER. 13 headline claims recomputed — all match. 3 MAJOR errata required (F1 alias misclassification of the "2020 vendor hole", F2 CoT source-layout erratum + script re-run hazard, F3 one unreproducible §1 vol number whose stated comparison direction reverses), plus 3 MINOR text errata and 4 NOTEs. The dossier's quantitative layer is sound and reproducible; its data-quality narrative layer (§7 hole, parts of §1 sensitivity prose, §5 source description) predates two later facts (the INTEGRATION-FIX-V2 alias adjudication and the CoT exact-name fix) and must be corrected before any registered cycle cites it.

---

## 1. Recomputed headline numbers (MATCH ledger)

| # | dossier claim (section) | dossier value | fresh recompute | script | verdict |
|---|---|---|---|---|---|
| 1 | VR(5/20/60) (§1) | 0.81 / 0.71 / 0.67 | 0.8077 / 0.7113 / 0.6688 | r1 | MATCH |
| 2 | v1-window rvol20 median percentile in 2010-2024 (§1) | 57th | 57.33rd (median 17.11% vs p10-p90 9.08-28.66%) | r1 | MATCH |
| 3 | rvol20 median / max / min (§1) | 16.1% / 92.4% (2020-03-27) / 4.5% (2016-09-02) | 16.13% / 92.41% @2020-03-27 / 4.52% @2016-09-02 | r1 | MATCH |
| 4 | calendar-rule ann vol (§1) | 19.6% (4,155 sessions) | 19.62% (n=4,154 returns) | r1 | MATCH |
| 5 | overnight share 2010 vs 2026 (§2) | 10.2% → 23.8% | a2 statistic (mean of per-session shares) reproduces; aggregate-volume variant 9.8% → 23.7% (see N1) | r2 | MATCH (claim) |
| 6 | 07:30 CT minute-volume share 2023-26 vs neighbors (§2) | 0.185% vs 0.041 / 0.089 | 0.1843% vs 0.0409 / 0.0881; quiet-era 07:30 = 0.0885% | r2 | MATCH |
| 7 | roll-day gap distribution + corr(gap, spread) (§3) | median −0.8, p10 −8.5, p90 +238.9, min −14, max +302, 49.2% positive; corr 0.999 | −0.75 / −8.5 / +238.85 / −14 / +302 / 49.23%; corr 0.99908 (n=65 of 66 rolls) | r3 | MATCH |
| 8 | unadjusted-chain embedded pts/yr (§3) | 2023 +723, **2024 +1,014**, 2025 +907, 2026 +810; 2010-16 −5..−31; 2018-19 +95/+110 | +722.75 / **+1,014.0** / +906.75 / +809.5; −5..−30.75; +95.25/+109.5 | r3 | MATCH |
| 9 | daily-volume-crossover DTE (§3) | median 7 (p10 4, p90 7, min 3, max 7; n=62) | identical (n=62) | r3 | MATCH |
| 10 | calendar-rule thin window (§3) | median 1.4% of market-front (p10 0.3%; 78% < 50%; n=650) | 1.38% / 0.28% / 78.5% (n=650) | r3 | MATCH |
| 11 | FOMC day-level (§4) | ×1.06 / ×1.11 / ×1.12; 60% / 62% above control; n=128 | 1.056 / 1.109 / 1.123; 60.2% / 61.7%; n=128 | r4 | MATCH |
| 12 | FOMC release windows (§4) | lull 0.68; 0..+30 2.26; +30..+60 2.64; +60..120 1.44; +120..180 1.34; **release minute ×3.5**; n=84 | 0.683 / 2.256 / 2.637 / 1.445 / 1.336 / 3.527; n=84 | r4 | MATCH |
| 13 | panel integrity (§0/§7) | 6,688,533 outright rows; 641,787 spread rows of 7,330,320; first 2010-06-06 22:00Z, last 2026-09-30 23:59Z; 0 duplicate (symbol,minute) | identical, from raw 13-file scan; duplicates 0 | r7 | MATCH |

Plus §5 CoT recomputed on the **fixed** tidy (see F2): every number matches.

## 2. The 2020 "vendor hole" — alias adjudication VERIFIED, erratum required

**F1 (MAJOR).** INTEGRATION-FIX-V2's `A_ALIAS_NOT_ABSENCE` verdict is verified in full against the raw delivered parquet (r6):

- `instrument_id 16908` carries raw_symbol `NQU8-NQM9` 2018-08-15→2020-05-31 (**92,075 bars, 24,686,121 contracts**) and `NQM0` 2020-06-01→06-19 (**19,406 bars, 5,159,596**; last bar 2020-06-19 13:29Z — the Jun-19 expiry week). Exact match to the probe.
- Hole window 2020-03-23..05-29 on id 16908: **58 trading dates, 0 weekday gaps except Good Friday 2020-04-10 (legitimate holiday), 21,824,572 contracts; Mar-23 alone 625,650** (daily range 6,838..690,803). Exact match.
- Delivered window 2020-03-01..06-30 across both chunks: **169,992 rows** == the probe's live-vendor parent quote; id-16908 window records **100,034** (80,628 alias + 19,406 relabeled) == the probe's live-vendor `NQM0` quote; per-symbol window counts (NQH0 17,932; NQU0 30,204; NQZ0 971) all match.
- Chunk `AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01` = **944,290 rows** == records_quoted. Dash-symbol uniqueness confirmed on the full NQ panel: `NQU8-NQM9` is the only dash symbol with lifetime volume > 5M contracts (24.7M; next 0.97M).

**Auditor extension beyond the probe (new evidence, r6):** the dossier §7's *supporting* narrative is also alias-contaminated, not just the headline:
- "Front-contract data degrades from 2020-03-16 (505k→85k by 03-19)" — that fade is **NQH0 expiring on 2020-03-20**; the true front (id 16908) traded **350,956 / 478,420 / 475,836 / 478,254 / 540,580** contracts on 03-16..03-20. There was no data degradation that week.
- "only the deferred NQU0_2020 trickle (~100-1,200 contracts/day) prints" — under the alias view the actual front printed **6.8k-690k contracts/day** through the "hole".

**Erratum scope (F1):** §7 "THE 2020 VENDOR HOLE" paragraph (reclassify: vendor symbology ALIAS under a dash-excluding outright filter; data present and delivered; recoverable at $0 via the view rule `instrument_id==16908 AND date<2020-06-01 → NQM0`); the "degraded from 03-16" and "NQU0 trickle" sentences; §9 item 1 (backfill recommendation → cancel, per probe: quote $0.62 recorded, NOT executed); §6 NOT_RUN inventory entry "2020-03-20..05-29 backfill"; the "2020 ann-vol 33.5% is a lower bound" caveat (2020 aggregates are recomputable at $0 and MUST be re-measured before any registered cycle uses them); `analysis/NQ_a7_quality.json` `vendor_hole_2020` block (incl. its `contracts_with_any_data` list, which omits NQM0_2020 for alias reasons); `dispatch/handoff_DEEP-NQ.json` known_limitations[0] and recommended_next_action(1). All §1/§2/§3 numbers computed on the NaN-hole series remain internally valid *as computed*; the misclassification is in the data-identity narrative, which is exactly what the mission invariant requires to reconcile.

## 3. CoT on the fixed tidy — numbers UNCHANGED; layout erratum + re-run hazard

**F2 (MAJOR).** The dossier's §5 numbers rest on the Consolidated line isolated by A5's own local `startswith("NASDAQ-100 Consolidated")` filter — NOT on mixed rows. The 2026-10-03 exact-name fix (uncommitted diff to `cftc_normalize.py`) preserves that line under `COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE`; recomputing the A5 logic verbatim on it (r5) reproduces **every** dossier number exactly: 850 rows 2010-06-15..2026-09-22; buckets n / fwd-10 rvol median = 105/18.48%, 195/14.02%, 123/15.34%, 170/15.49%, 91/15.26%; Σ|ret| medians 9.2/7.0/7.6/7.2/7.5%; era stability 14.4-vs-14.9 / 17.0-vs-14.4 / 17.2-vs-19.4; OI medians 94,852 (2010) → 302,385 (2026); net-noncomm %OI 8.66% → 1.98%. **No CoT number changes; no numeric erratum needed.**

However: (a) the §5 "Data discipline" paragraph describes the pre-fix mixed-tidy state, which is now historical — it must be re-pointed (source series is now the `__ALT__` id; canonical `COT_LEGACY_NQ` is the E-mini line 2006-2026); (b) **`NQ_a5_cot.py` as written selects ZERO rows on the fixed tidy** (r5 part B: filter hits 0 of 1,082 canonical rows) — a re-run would silently produce an empty analysis. Loader must be re-pointed to the `__ALT__` series id before any re-run. (c) For the owner's decision record (r5 part C): restated on the canonical E-mini line, the §5 headline conclusion still holds (extreme-short 18.39% vs mid 17.13% — still the max bucket; same era sign-flip), but context numbers differ materially (OI 359k (2010) → 284k (2026) vs consolidated 95k → 302k; net %OI 6.8% → 3.1% vs 8.7% → 2.0%).

## 4. Taxonomy / PIT discipline — PASS

- **Tags:** every section carries FACT/OBSERVED/POSTULATED/NOT_RUN tags with script + window; NOT_RUN defaults honored (CPI/NFP, TFF, consensus, PIT daily yields, BBO). PASS.
- **Strict-past thresholds:** verified in code — A5 percentile window `s.iloc[i-156:i]` excludes the current obs; A1 vol terciles use `hist = seg.iloc[:-1]`; trend label trailing-120d; rvol trailing windows. PASS.
- **No conditional mean-return selection:** A5's table conditions on positioning percentile but its outcomes are distributional risk measures (median fwd realized vol, Σ|ret|, window max-drawdown) — no signed mean returns — and it is used to *downgrade* H2 (anti-selection). A4 uses volume / |1m ret| / range only; special-time statements listed, not aggregated. Variance ratios and descriptive vol buckets are descriptive-persistence statistics, legal. H4 explicitly left NOT_RUN. No ranking/selection anywhere. PASS.
- **Event anatomy release times:** built only from statements whose own archived HTML carries "For release at H:MM … ET" (primary-source proof); 2 p.m. ET → 13:00 CT mapping correct; controls are same-weekday ±21d non-event clean sessions. PASS (control pools include future sessions — standard descriptive event-study practice, disclosed; see N3).

## 5. Mismatches (dossier text vs delivered artifacts) — errata required

- **F3 (MAJOR).** §1 "ann vol **19.6% vs 16.9%** (volume rule)": the calendar-rule 19.6% reproduces, but **"16.9% (volume rule)" is not reproducible from the delivered cache** — fresh compute on the delivered hole-aware series gives **20.1%** (n=4,168 returns); no variant (excl. 2020, excl. hole-adjacent, clean-only, ddof=0) yields 16.9%. It appears to be a stale pre-DST-fix figure. Consequence: as written, the sentence's direction ("calendar rule inflates vol") **reverses** on current artifacts (19.6% < 20.1%). §3's unfitness conclusion independently survives via the measured 1.4%-of-front-volume thinness, but the §1 vol sentence must be corrected or struck.
- **F4 (MINOR).** §1 stale secondary stats: "ACF(1) full-era −0.056" vs JSON/fresh **−0.076**; "rolling-252d median −0.045" vs **−0.042**; "p10-p90 −0.134..+0.069" vs **−0.134..+0.071**; VR(20) p10 "0.53" vs **0.522**. Same stale-prose family as F3 (post-DST-fix re-run refreshed the JSON but not all prose).
- **F5 (MINOR).** §4 provenance counts: "147 archived statements" (147 = **132** `a`-statements **+ 15 `b`/`c` implementation-note files**; the analysis ingests 132); "the 106 statements whose own HTML carries 'For release at'" (106 counts all 147 files; statements alone: **92**); "98 of 106 are 2pm" (statements: **85 of 92**). The matched counts (128 day-level; 84 clean 2 p.m.) and every ratio verify. `handoff_DEEP-NQ.json` known_limitations[2] repeats 106/147.
- **F6 (MINOR).** Window typos: "2020-03-20..**2026**-05-29" in §9 and in `NQ_a7_quality.json` (should be 2020-05-29; §7 and the handoff have the same string). Also §2 "123 era-A Friday-early-close sessions" vs `NQ_a2_sessions.json` **126**.

## 6. NOTEs

- **N1.** §2 yearly overnight share is the *mean of per-session shares* (a2's statistic); an aggregate-volume share differs by ≤0.5pp (2010: 10.2 vs 9.8; 2026: 23.8 vs 23.7). The doubling claim and 2018-19 level shift are robust to the choice; the dossier should name the statistic.
- **N2.** A5's two forward tables use slightly different row sets (mid bucket n=123 for rvol vs n=126 for max-drawdown — the latter lacks the all-NaN-return guard); the dossier's "mid −2.4%" matches the mdd table; a unified row set gives −2.58%. Definitional, worth one line of disclosure.
- **N3.** A4's ±21d control pool includes sessions *after* the event (descriptive control; not a signal threshold; disclosed). Acceptable under prep law; noted for completeness.
- **N4.** The dossier's `NQ_deep_lib.py` `load_cot_nq()` docstring/§5 wording ("mixes THREE CFTC market lines … on duplicate dates") was accurate pre-fix and is retained in `handoff_DEEP-NQ.json` known_limitations[4]; after the fix it reads as a description of the current tidy — fold into the F2 erratum wording.

## 7. Audit scope limits (honesty)

- Vendor live-metadata quotes (169,992 / 100,034 / $0.62) were NOT re-probed (API key law; metadata-only probe already redacted properly). The **delivered-side** counts were verified to equal those figures exactly, which is the strong reconciliation available read-only.
- The 2020 yearly aggregates (e.g. "+13.2%", "worst day −11.15%") were not recomputed (they sit on the NaN-hole series whose identity is corrected by F1; re-measurement belongs to the fix lane, not the auditor).
- Text-vs-JSON consistency was checked on all headline tables; the F4-F6 family shows the pattern, but an exhaustive character-level sweep of every prose number was not performed.

## 8. Errata required (consolidated, for the owner / DEEP-NQ follow-up)

1. **F1** — Reclassify the 2020 "vendor hole" as a vendor SYMBOLOGY ALIAS (view rule `instrument_id==16908 AND date<2020-06-01 → 'NQM0'`); strike/rewrite the §7 hole paragraph incl. "degraded from 03-16" and "NQU0 trickle" sentences; cancel the §9 backfill recommendation; fix the §7/§9/JSON "2026-05-29" typos; re-measure 2020 aggregates before any registered cycle.
2. **F2** — Re-point §5's source note to `COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_…` (numbers unchanged — verified); fix `NQ_a5_cot.py` loader before any re-run (currently selects 0 rows on the fixed tidy).
3. **F3** — Correct §1's "16.9% (volume rule)" (delivered-artifact value ≈20.1%; comparison direction as written reverses) and refresh the stale ACF/rounding numbers (F4).
4. **F5/F6** — Fix FOMC provenance counts (132/92/85, with 15 b/c files named as such) and the 123-vs-126 Friday-early-close count.

— End of audit. Audit scripts `r1..r7` + JSON outputs in this directory; every number above is reproducible read-only.
