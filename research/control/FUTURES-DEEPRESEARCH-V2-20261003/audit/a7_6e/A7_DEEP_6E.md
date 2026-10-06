# A7-DEEP-6E — Independent audit of `dossiers_v2/6E_DEEP_v2.md` + `analysis/6E_*`

Lane **A7-DEEP-6E** (fresh-context auditor), task `FUTURES-DEEPRESEARCH-V2-20261003`,
checkout `prep @ 26d96eb4` (dispatch base = actual start = 26d96eb4, verified).
Audit date 2026-10-03. READ-ONLY on data; every number below was recomputed
**from raw vendor parquet with zero DEEP-6E code imports** (fresh script
`a7_6e_recompute.py` in this directory; output `a7_6e_recompute.json`).

## Method

- Rebuilt the 6E outright panel from the 5 raw vendor files
  (3,054,311 bars, 90 contracts — matches dossier exactly), own session-dating
  (America/Chicago wall-clock, 17:00 rule), own expiry-rule implementation
  (holiday set incl. Juneteenth 2022+, Columbus Day, Good Friday, Veterans,
  weekend shifts), own held-calendar rule, own FOMC statement-time parser,
  own CoT/rates/statistics loaders.
- Cross-checked dossier text against its own JSON artifacts line by line.
- Web-verified sampled ECB assembled dates against primary ECB pages.
- CIP recomputed twice: latest-vintage rates (lane's basis) and a PIT-as-of
  reconstruction from the ALFRED year-end SOFR vintages that exist on disk.

## 1. Headline-number recomputation — match table

| # | Claim (dossier) | Lane artifact | A7 independent recompute | Verdict |
|---|---|---|---|---|
| 1 | Holiday-extended expiry model **80/80** expired contracts | build log | 80 of 80 rule-expired contracts match last observed session (90 contracts total; 10 unexpired correctly excluded); quarterly expiries **32/33 Mondays**, sole exception 6EM3 Fri 2023-06-16 | MATCH |
| 2 | v1 window vol **6.8th percentile** (5.41%, drift −5.5% at 25.8th) | a1: 5.4237%, pct 6.80%, 25.85% | 5.4237% / 6.80% / −5.498% / 25.85%; n=276 returns; roll p05/p50/p95 = 5.660/7.187/9.942 | MATCH |
| 3 | **55.3%** of front volume outside 08:30–16:00 CT (1,504,002 of 2,252,088 bars) | a6/a2 | 55.2849% / 44.7151%; 1,504,002 of 2,252,088 front bars; 1,746 sessions | MATCH |
| 4 | ECB/US-data block 06:30–08:00 CT: **15.6%** of RV with **12.5%** of volume | a2 | RV 15.5844% / volume 12.4516% (London morning 16.61/17.17; Asia 15.22/12.23 also match) | MATCH |
| 5 | 27/27 roll gaps positive; sign agreement **27/27** vs SOFR−€STR; **r=0.91** vs CIP; median residual **+6.2 ticks**; median gap +91 ticks (36..138) | a3 | 27 rolls, 27/27 positive, sign 27/27, r=0.9097, median residual +6.176 ticks, median 91 ticks, min/max 36/138 | MATCH |
| 6 | Migration crossover d−4 Thu **30.7%** → d−3 Fri **87.1%** → d−0 98.8% | a3 | 30.70 / 87.10 / 98.77 (d−7 9.53, d−5 19.57 also match) | MATCH |
| 7 | FOMC statement minute **×17.2** (+5m ×9.96, +10m ×5.61) | a4 | ×17.242 / ×9.956 / ×5.613; 58 events, 58/58 with primary "For release at" proof, 53 at 13:00 CT | MATCH |
| 8 | ECB decision minute ×1.73, presser+30 ×1.46, pre-release ×0.88–0.94; 93.6% vs 90.2% after 06:45 | a4 | ×1.732 / ×1.462 / ×0.876–0.939 / 93.64–90.19; 55/55 meetings in data | MATCH |
| 9 | Serials **0.34%** of outright volume (57 serial vs 33 quarterly contracts) | a3 | 0.34188%, 57/33 | MATCH |
| 10 | Era bar/session counts 886,127/518 · 1,823,090/1,033 · 345,094/195; strays 6JZ7 4,831 + SIJ5 1,869; spread rows 6.4/12.4/14.5% | a6/a3/integration scan | all reproduce exactly (strays 6,700 total; spread rows 60,429/256,918/58,375) | MATCH |
| 11 | CoT: min −226,560 @2015-03-31; max +211,752 @2020-08-25; latest −52,334 @2026-09-22 (9th pct); era means −44.0k/−40.4k → +61.9k/+71.7k; OI 173k→754k; 2022 path −1.5k→−47.7k(08-30)→+146.2k, OI 678k→773k | a5 | every value reproduces exactly on the FIXED tidy (see §4) | MATCH |
| 12 | Crowded-short fwd vol: ≤20 pctile → **7.7%** mean next-21d ann vol (median 7.6) vs ≥80 → 6.5% (mid 7.0), n=347/54/36 | a5 | 7.684 / 7.552 / 6.522 / 6.982, n=347/54/36 | MATCH |

Embedded-drift per year, thin-window zeros, weekday shares, DST-mismatch hour
shifts, London-local 21.6% vs CT 17.1%, Sunday-open 348 sessions/1.9%, 07:30 CT
×1.95/×1.5 on 1,732 sessions, annual table, VR/autocorr — all spot-checked
against artifacts and consistent (not all independently re-derived; the
machinery that produces them reproduced exactly wherever re-run).

**Bottom line: the dossier's quantitative core is sound.** Not one recomputed
headline number deviates from its artifact beyond display rounding.

## 2. MAJOR-1 — the "GLBX venue OI = exactly 2.000× CFTC OI" claim is a
dedupe artifact, not a convention

Dossier §1 calls this "engine-critical … systematic convention difference
(double-counting convention)"; §7 repeats "cross-venue OI joins must be
scale-normalized"; §9 logs "OI convention (2×) unresolved"; open question 5
proposes a CME spot-check. **All of this is wrong.**

A7 recompute (156 overlap weeks, 2023-10→2026-09, same join as a5):

- **Raw-row sum (the lane's a5 method): median 2.00028, p05 1.99993, p95
  2.10643, max 3.00170** — reproduces the lane's JSON to 5 decimals, so I
  confirmed their computation before overturning its interpretation.
- The GLBX statistics dataset publishes **2 rows per (contract, ref_date)**
  for stat_type 9 (7,615 pairs ×2, 107 ×3, 8 ×4, 107 ×1) — duplicate
  publication events, usually identical quantity. Summing rows without
  dedupe doubles everything; on days with 3 publications the "ratio" becomes
  **3.000×** (2023-11-21, 2023-10-24, 2023-11-07, 2024-02-27, 2024-07-30) —
  a genuine convention difference can never triple.
- **Dedup to latest publication per contract-day: median ratio 1.0000** vs
  CFTC CoT OI (p05 1.0000, p95 1.00005; 150/156 weeks within ±0.2%). Probe
  week 2024-06-04: venue sum 671,736 == CoT OI 671,736 exactly.
  The 3 residual weeks (2025-06-17 ×1.31, 2026-03-17 ×1.27, 2025-09-16 ×1.18)
  are roll/expiry weeks where the venue statistic still carries the
  just-expired contract (e.g. 6EM5 232,435 on 2025-06-17) that CFTC zeroes.
- Internal inconsistency confirming the artifact: the lane's **a3**
  OI-crossover analysis used a *deduped* table (`groupby(...).agg(last)`)
  while **a5** summed *raw* rows — the same lane's two artifacts disagreed
  by 2×, and only the a5 side was published as a "convention".

**Adjudication:** no contract-unit or convention difference exists — GLBX
stat_type-9 OI reconciles 1:1 with CFTC legacy futures-only OI (same
single-sided convention) after deduplicating publications. The dossier's
protective warning ("never mix") is harmless but the claim, the NOT_RUN
register line, and open question 5 must be corrected. The OI-vs-volume
crossover finding (§5, 5–6 day lead in 7/12 rolls) is UNAFFECTED (it used the
deduped table).

## 3. MAJOR-2 — CIP r=0.91 is vintage-fragile; the on-disk PIT
reconstruction contradicts it

Dossier §5/H2 upgrades H2 to "CONFIRMED descriptively" on 27/27 sign +
r=0.91 + residual +6.2 ticks, with a prose caveat that the rate series are
latest-vintage, not point-in-time. A7 rebuilt the rate series from the
ALFRED year-end SOFR vintages that exist on disk (2019-12-31 … 2024-12-31,
plus 2026-09-30; **no 2025-12-31 vintage exists**) as PIT-as-of each roll
date:

- latest-vintage basis: r = 0.9097, sign 27/27, median residual +6.18 ticks
  (reproduces the lane exactly);
- **year-end-vintage-as-of basis: r = −0.107, sign agreement 26/27, median
  residual +3.77 ticks.**

So the headline correlation does not merely carry a caveat — on the only
vintage data available for a PIT reconstruction it **does not hold**. Two
readings are possible and the dossier must state which it claims: (a) the
year-end vintages are simply too stale (up to 12 months; up to ~21 months for
2025-26 rolls, which have no 2025 vintage at all) to test CIP, and real-time
SOFR (knowable daily at the time, essentially unrevised) would have matched —
in which case r=0.91 is defensible but currently **unverifiable from disk**;
or (b) the correlation is a latest-vintage artifact. The €STR series is
latest-only (ECB SDW) with no vintage set on disk. Sign agreement (26/27) and
the one-sided positive residual survive both bases. The H2 registration
proposal (gap vs SOFR−€STR regression) should carry this quantified
sensitivity, not just the current one-line caveat.

## 4. CoT on the FIXED tidy — no change to any 6E number

- Value-level diff of `cftc_legacy_tidy.parquet.bak_prefix_mixed_20261003`
  vs the regenerated tidy for `COT_LEGACY_6E`: 1,082 rows joined, **0
  mismatches** in net_noncomm and OI. The integration fix (exact market-name
  mapping) did not touch the EURO FX series — it was never contaminated.
  All §7 numbers (era means, extremes, 2022 crisis path, crowded-short
  forward vol, latest percentile) reproduce **exactly** on the fixed tidy.
- The 2010-14/2015-19 → 2020-22/2023-26 flip (−44.0k/−40.4k → +61.9k/+71.7k)
  and the crowded-short forward-vol claim (≤20 pctile → 7.7% mean vs ≥80 →
  6.5%, n=36/54) stand as published.

## 5. ECB date assembly — 5/5 sampled assembled dates verified, 0 mismatches

Sampled from the 45 assembled (non-machine-verified) dates; primary ECB
pages fetched 2026-10-03:

| Date | Evidence (primary ECB) | Result |
|---|---|---|
| 2020-01-23 | `ecb.europa.eu/press/pr/date/2020/html/ecb.mp200123~ae33d37f6e.en.html` — HTTP 200, title "Monetary policy decisions", 23 January 2020 | MATCH |
| 2021-03-11 | `…/2021/html/ecb.mp210311~35ba71f535.en.html` — HTTP 200, title + date, PEPP-pace decision text | MATCH |
| 2023-06-15 | on-disk ECB SDW MRO series: 4.00% effective 2023-06-21 = decision + 6 days (ECB convention), announcement 15 June | MATCH |
| 2025-03-06 | `…/2025/html/ecb.mp250306~d4340800b3.en.html` — HTTP 200, −25bp effective 12 March 2025 (consistent with SDW eff. 2025-03-12) | MATCH |
| 2026-02-05 | `…/2026/html/ecb.mp260205~001d26959b.en.html` — HTTP 200, rates unchanged | MATCH |

Additional machine cross-check: the SDW MRO series verifies **all 20
rate-change meetings 2022-2026** in the assembled set (effective date − 6
days = assembled decision date, 20/20). The current GC calendar page shows
the remaining 2026 meetings (29 Oct, 17 Dec), consistent with the in-window
set ending 2026-09-10. The 14:15 CET release-time FACT is confirmed verbatim
on the ECB "Monetary policy decisions" index page
(`ecb.europa.eu/press/govcdec/mopo/html/index.en.html`); the 14:45
press-conference time was NOT re-verified (that index page does not state
it) — the only ECB FACT now resting solely on the lane's 2026-10-02 fetch.

## 6. Taxonomy / PIT / contaminant handling

- Tags present and used consistently (32 OBSERVED / 4 FACT / 11 POSTULATED /
  9 NOT_RUN in the dossier); §9 NOT_RUN register explicit; no PnL, no signal
  ranking, no conditional mean-return table anywhere in the 6E artifacts
  (the positioning-vs-forward-vol table conditions on positioning and
  measures forward volatility — vol/risk anatomy, disclosed as such; law-consistent).
- Contaminants: OUTRIGHT_RE fullmatch excludes exactly the 6,700 stray bars
  (6JZ7 4,831 in the AV1B file; SIJ5 1,869 in the AV1R file) and 375,722
  calendar-spread rows — reconciles 1:1 with the INTEGRATION-FIX-V2 scan;
  spread volumes never aggregated (disclosed NOT_RUN). Consistent.
- PIT: CoT forward descriptives start at obs+3 sessions (release-safe);
  FOMC times from primary statement text; held-contract rules use only
  past information; every threshold in the artifacts is rolling/strict-past
  in effect. One label imprecision below (MINOR-3).
- Handoff canonical: dispatch_sha == actual_start_sha == 26d96eb4 ✓;
  commit_sha null with honest disclosure ✓; output sha256 list present ✓.

## 7. Findings register

**BLOCKER** — none.

**MAJOR**
1. Venue-OI "2.000× convention" claim is false — publication-duplication
   artifact in a5's raw-row sum; deduped venue OI reconciles 1:1 with CFTC
   (§2 above). Erratum required for dossier §1, §7, §9 and open question 5.
2. CIP r=0.91 not reproducible from the on-disk ALFRED vintages (r=−0.11
   PIT-as-of vs 0.91 latest); H2 "CONFIRMED" rests on a basis that cannot be
   PIT-verified from disk (§3 above). Quantified sensitivity disclosure
   required before any H2 registration.

**MINOR**
3. Four places where dossier text contradicts its own artifacts:
   (a) §3 "n=1,751" — artifacts say 1,746 sessions / 1,745 returns;
   (b) §3 rolling-63 min at "2026-01-14" — artifact and recompute say
   **2026-01-16**; (c) §3 "rolling p05 5.65" — artifact 5.6601 → "5.66";
   (d) §4 "quietest hours ~01:00 CT (1.0%) and 18:00 CT (1.0%)" — the two
   quietest session hours (excluding the 16:00 break hour) are **17:00–18:00
   CT (1.004%) and 23:00–24:00 CT (1.015%)**; 01:00 CT actually carries
   3.99%. Session-hour labels (h−07, h−01) were misread as clock times.
4. §6 (and open question 4) characterize control-Wednesday peak minutes as
   "12:00–12:07 CT"; the artifact's actual mode is **13:59 CT (162 of ~340
   control Wednesdays)** with 12:00–12:02 a secondary cluster (26). The
   "different, recurring midday flow" narrative is built on the secondary
   cluster. (FOMC ×17.2 headline unaffected.)
5. a5's "strict-past 3y percentile" includes the current observation in its
   own rolling min/max window. Immaterial here (a truly strict variant gives
   identical bucket means 6.52/7.68 and the same latest percentile 9.08),
   but the label is imprecise and should read "rolling 3y percentile incl.
   current week" or be shifted one week.

**NOTE**
6. The 14:45 CET press-conference FACT could not be re-verified (ECB index
   page silent); 14:15 CET decision-release FACT verified verbatim.
7. Data window phrasing "→2026-09-30" includes one final partial session
   dated 2026-10-01 (the Tue 2026-09-30 17:00+ CT evening); 1,746 sessions
   either way — immaterial.
8. Expiry-rule "80/80" verified to mean rule-expired contracts only (80 of
   90; the other 10 are live/future contracts whose rule dates fall beyond
   the data) — dossier phrasing is accurate.
9. My independent DST-safe session-dating reproduced the front bar count
   (2,252,088) exactly, corroborating the lane's DST-fix disclosure.
10. All six input JSON artifacts' numbers are internally consistent with the
    dossier wherever I checked, except the items listed above.

## 8. Verdict

**PASS WITH ERRATA.** The DEEP-6E dossier's measured core — panel
construction, session anatomy, roll/CIP descriptives (on the stated
latest-vintage basis), event timing, CoT anatomy, contaminant handling,
taxonomy and PIT discipline — is independently reproducible from raw data to
the last displayed digit (12/12 headline recomputes match; 5/5 ECB sampled
dates verified on primary pages; 20/20 rate-change meetings machine-checked).
Two MAJOR interpretation defects require errata before any downstream use:
the venue-OI "2× convention" (wrong — dedupe artifact; venue and CFTC OI
reconcile 1:1) and the CIP r=0.91 vintage basis (not reproducible from
on-disk vintages; sensitivity must be quantified in the H2 spec). Five
MINOR text/label corrections listed above. Errata are mandatory; nothing
requires re-measurement of the panel itself.

Errata required: yes — items MAJOR-1, MAJOR-2, MINOR-3(a-d), MINOR-4,
MINOR-5 as specified in §7.
