# A7-DEEP-6B — Fresh-context independent audit of 6B_DEEP_v2

- Task: FUTURES-DEEPRESEARCH-V2-20261003, lane A7-DEEP-6B (read-only auditor)
- Base HEAD: 26d96eb4bdd4be85e151055dace3354638498a44 (verified; worktree
  prep/futures-behavior-10syms-20261002; DEEP-6B lane left changes uncommitted
  with commit_sha null + disclosure — canonical per dispatch)
- Audited: dossiers_v2/6B_DEEP_v2.md + analysis/6B_deep_lib.py, 6B_build_cache.py
  (+report), 6B_a1..a7 (.{py,json}), 6B_cache/ (derived), against RAW vendor
  parquet + nonprice inputs.
- Audit method: FRESH recompute with an independent implementation (own session
  logic, own contract registry, own xlsx parser) reading only raw inputs —
  never the lane's derived caches. Scripts + outputs in this directory:
  recompute_6b_headlines.{py,json}, diff_chain_vs_lane.py, residual_checks.{py,json}.
- Audit date: 2026-10-03.

## 1. Fresh recompute results (headline numbers)

| # | dossier claim | fresh recompute | verdict |
|---|---|---|---|
| 1 | Roll-gap vs Fed−BoE differential Pearson +0.84 | +0.8423 | MATCH |
| 2 | — "rank corr = +0.84" | Spearman +0.7445 | **MISMATCH (M1)** |
| 3 | mean gap diff>0 = +9.4 ticks (n=19) | +9.368, n=19 | MATCH |
| 4 | diff<0 = −3.0 ticks (n=1, 2022-02-28, BoE 0.50/Fed 0.25) | −3.0, n=1 | MATCH |
| 5 | 7 zero-diff rolls (2022-05, 2024-11, 2025-02, 2025-11, 2026-02/05/08), gaps −5..+13 | same 7 dates, gaps −5..+13 | MATCH |
| 6 | gap dist n=27, mean +6.5, median +5, 20 pos/7 neg, min −5/max +30 | 6.481 / 5.0 / 20/7 / −5/+30 | MATCH |
| 7 | CIP slope 0.186 %/pp vs theory 0.253 → ≈73% of textbook | 0.1859 / 0.2528 / 73.5% | MATCH |
| 8 | realized +6.5 vs CIP-predicted +8.6 ticks; corr 0.83 | 6.48 / 8.62 / 0.830 | MATCH |
| 9 | 2022-09-23 −3.82%, 244,110 contracts, low 1.0840 | −3.821% / 244,110 / 1.084 | MATCH |
| 10 | 2022-09-26 record 374,255 (held), low 1.0392 | 374,255 / 1.0392 (all-front day total 374,662) | MATCH |
| 11 | 2022-09-28 +1.40%; episode ann vol 18.86%; best +2.16% (09-29) | +1.396% / 18.856% / +2.158% | MATCH |
| 12 | max drawdown −22.5% trough 2022-09-26 (still open) | −22.478% @ 2022-09-26 | MATCH |
| 13 | BoE MPC first-5m 18.7× (7,091 vs 380) | 7,090.5 / 379.5 = 18.68× | MATCH |
| 14 | ±30m 5.2× (17,454 vs 3,371); day 1.51×; range 1.02% vs 0.68% | 5.18× / 1.508× / 1.020 vs 0.677 | MATCH |
| 15 | 12:00 London spike 3,451/min vs 1,392 (12:01), 1,074 (12:02); n=56, 22 change/34 hold | 3,451 / 1,392 / 1,074; 56; 22/34 | MATCH |
| 16 | change-vs-hold first-5m 8,985 vs 6,435 | 8,985 / 6,434.5 | MATCH |
| 17 | volume crossover median 11 sessions after declared roll (9..13), 27/27 inside delivery month | 11.0 (9/10/11/11/13), 27/27 | MATCH |
| 18 | OI crossover leads volume by 5-7 days (median −6, n=11) | −6 (−7..−5), n=11 | MATCH |
| 19 | old:new at declared roll 129:1; old delivery-month volume median 824,460 | 129.1 / 824,460 | MATCH |
| 20 | London-morning share 28.7→27.5→27.5→23.7%; h8 7.7→5.7; h15 modal 12.1-12.8; evening 17.9→21.8 | 28.73/27.51/27.55/23.77; 7.75→5.74; 12.09-12.82; 17.88→21.76 | MATCH |
| 21 | VR21 0.73; 2022 VR21 0.98; VR21<1 7/7 years, min 0.53 (2026) | 0.728 / 0.985 / 7 of 7, 0.533 | MATCH |
| 22 | FOMC 53 at 14:00 ET of 58 in panel; 5 other times | 59 statements in window, ALL 59 with proof, 53 at 14:00; 58 panel days | MATCH on 53/14:00 (M4 wording) |
| 23 | FOMC first-5m 9.5× (2,266 vs 239); ±30m 2.6×; day 1.12× | 9.48× / 2.60× / 1.117× | MATCH |
| 24 | CoT corr(|z|, fwd vol) = −0.07 (signed −0.08), n=326 | −0.0742 / −0.0852 / 326 (FIXED tidy) | MATCH |
| 25 | CoT bucket medians 6.17 / 7.99 / 6.85; dd medians −1.6..−2.3 | 6.17/8.00/6.85; −1.64..−2.32 | MATCH |
| 26 | Aug-2022 crash from SHORT positioning z −0.4..−1.26, net −28k..−56k | z −0.40..−1.26, net −27,966..−56,409 | MATCH |
| 27 | gilt corr 2020..2024: −0.14/+0.17/−0.23/−0.06/−0.10; full −0.13 | −0.144/+0.172/−0.227/−0.064/−0.101; −0.125 | MATCH |
| 28 | rolling-63d min −0.57 @2022-10-17, max +0.55 @2020-12-23 | −0.570 / +0.547 | MATCH |
| 29 | episode: 09-23 2y +45bp/10y +29bp; 09-26 2y +44; 09-28 10y −38; 4-day corr −0.68 | +45.3/+29.1; +44.1; −38.2; −0.675 | MATCH |
| 30 | gilt stress days 1.40% vs 0.32% = 4.4× (n=9, dates as listed) | 1.396 / 0.318 = 4.39×, same 9 dates | MATCH |
| 31 | QA: 2,549,633 rows; eras 754,609/1,615,234/179,790; spread 37,943/135,537/15,559; 0 OHLC/0 dup/0 zero-vol/0 weekend/1 break bar | all exact | MATCH |
| 32 | butt joints 0 dup keys; gaps 0.00% / +0.074% | 0 / 0; 0.00% / +0.0740% | MATCH |
| 33 | definitions tick uniformly 0.0001 USD, 19,183 rows | 0.0001, 19,183 | MATCH |
| 34 | GCQ4 stray 2,139 bars (vendor leak) | 2,139 bars, vol 6,090, 2020-07-28→11-16 | MATCH |
| 35 | DST sessions 1294 (2021-03-15) / 1300 (2021-11-08); rules agree 1458/1746=83.5%; chain corr 0.9998; 114 <600-bar sessions; 28 front-scale quarterlies | all exact | MATCH |
| 36 | rv63 4.72%@2024-07-29 → 20.08%@2022-12-15; top-8 all 2022-11-28..12-20; vol-regime year shares | all exact | MATCH |

Independent-implementation note (N3): the auditor's first-pass session code
used a 24-hour timedelta for the next-day roll and reproduced EXACTLY the
fall-back-DST trap the lane's lib explicitly guards against (pd.offsets.Day vs
timedelta; 6 mis-dated Sunday sessions). After correcting the auditor's code,
every chain-derived statistic matched the lane to ≥4 decimals — strong
corroboration of the dossier's DST-correctness claims (§0.1).

## 2. The v1-overturn claim (round headline) — CONFIRMED, with text errors

v1's four rolls (v1 dossier §1: 2025-11-28, 2026-02-27, 2026-05-29,
2026-08-31; gaps −2/+5/−3/+3 ticks on IBKR RTH closes). Fresh recompute of the
BoE−Fed differential (DFEDTARU − Bank Rate, step-ffill) on those exact dates:

| roll date | BoE | Fed (upper) | diff | v1 gap | v2 gap (full-session close) |
|---|---|---|---|---|---|
| 2025-11-28 | 4.00 | 4.00 | **0.00** | −2 | −2 |
| 2026-02-27 | 3.75 | 3.75 | **0.00** | +5 | −4 |
| 2026-05-29 | 3.75 | 3.75 | **0.00** | −3 | −2 |
| 2026-08-31 | 3.75 | 3.75 | **0.00** | +3 | +1 |

- OVERTURN CONFIRMED: all four v1 roll dates sit in a literally zero
  differential window; v1's "mixed-sign small gaps, no direction" is exactly
  what the 27-roll evidence predicts at diff=0 (the 7 zero-diff rolls show
  small mixed-sign gaps −5..+13). v1's inference did not generalize because
  its window had no differential variation — the dossier's headline story is
  correct and now independently verified.
- TEXT ERROR (M2): the dossier parenthetical "(diff −0.25..0.00pp → gaps
  −2..+3 ticks)" is wrong on both ends: roll-date diffs are exactly 0.00
  (−0.25 is an era-path minimum, 80 of 395 days in 2025-09..2026-09 were
  nonzero); and "−2..+3" matches neither v1's own gaps (−3..+5) nor v2's
  re-measured full-session gaps on those dates (−4..+1).

## 3. Gilt DECLARED_LAG caveat — PASS

Caveat appears at every gilt-coupled location: §0 input table ("DECLARED_LAG
caveat throughout §6"), §6 header + `gilt_coverage.declared_lag_note` in JSON,
§8 H3' ("PIT only with ≥1bd lag"), §9 NOT_RUN row. Local gilt coverage
independently parsed from the BoE zip: 2016-01-04..2024-12-31 (2,273 days) —
no 2025-26 gilt number is computed anywhere in the dossier; §6 marks 2025-26
coupling NOT_RUN. No ungated gilt-coupled claim found.

## 4. CoT POUND null result on the FIXED tidy — REPRODUCES EXACTLY

Timeline: 6B_a5_cot.json generated 2026-10-03 07:58; integration-fix lane
regenerated cftc_legacy_tidy.parquet 08:43 (pre-fix preserved as
.bak_prefix_mixed_20261003). Column diff of COT_LEGACY_6B pre vs post fix:
numeric columns, observation periods, released_at ALL identical — only
`market_name` trailing whitespace stripped (470 rows). Fresh recompute of §5
on the FIXED tidy reproduces every number exactly (items 24-26 above; plus
records −107,844 @2017-03-21 / +142,183 @2024-07-23, OI-era medians, release
lag 3/2/4). The null result and the short-positioning crash-origin claim are
UNCHANGED by the fix. The integration-fix handoff's "6B as-is == canonical" is
verified. Residual issue = stale sha pointer (M6): dossier §0 cites
4f9cd78944ee79dc (now the .bak); canonical fixed tidy sha is
f7a2719e745c2f6f — erratum should be appended when the fix is folded in.

## 5. Taxonomy / PIT / contaminants / tick — PASS

- Taxonomy tags (FACT/OBSERVED/POSTULATED/NOT_RUN) used consistently; v1
  incorporation-by-reference declared; NOT_RUN never inferred PASS.
- No conditional mean-return / return-conditioned selection anywhere: a4/a5
  compute volume, |ret|-sums, ranges, unsigned rolling vol, window-local
  drawdowns only (grep + code read). Law honored.
- Strict-past: CoT z uses 156w rolling stats shift(1); volume-crossover rule
  decided at close (trailing-5 incl. current day), effective next session;
  vol-regime labels trailing-1y percentile; roll-boundary returns excluded
  from all chain statistics (116 NaN sessions disclosed).
- Contaminants: spread-instrument rows excluded and counted per era (verified
  exact); serial clusters excluded (84,339 rows / ~0.26% of volume — verified);
  GCQ4 2,139 bars + 6BM5 1,392 bars quarantined (verified; GCQ4 reconciles
  exactly with integration/contaminant_scan); registry stray logic sound.
- Tick adjudication: 19,183 GLBX definition rows for 6B quarterlies uniformly
  min_price_increment 0.0001 USD — primary-source adjudication verified
  against raw definitions parquet.
- Vintage caveats disclosed (DFEDTARU latest-not-vintage; BoE revision-free).

## 6. Findings

### BLOCKER — none.

### MAJOR — none.

### MINOR (errata required; none changes a conclusion)
- **M1** §3: "rank corr = +0.84" — actual Spearman +0.744 (6B_a3_term.json
  `spearman_corr` 0.7445). Pearson +0.84 is correct; the rank figure is wrong
  in the dossier text.
- **M2** §3 v1-overturn parenthetical "(diff −0.25..0.00pp → gaps −2..+3
  ticks)": roll-date differential is exactly 0.00 on all four v1 dates; gap
  range matches neither v1's measured −3..+5 nor v2's re-measured −4..+1.
  Overturn claim itself CONFIRMED (§2 above).
- **M3** §3: "+13 outlier (2022-05-31) sits one week before a scheduled Fed
  hike" — next scheduled FOMC after 2022-05-31 was 2022-06-15 (~2 weeks;
  archive monetary20220615a.html). Nearest scheduled Fed event was the
  2022-06-01 QT start (2 days). "One week"/"hike" is wrong as written.
- **M4** §0/§4 FOMC counts: 59 statements in the 2020-2026 window, ALL 59
  carry in-document release-time proof; 53 are at 14:00 ET; 58 dates have
  panel bars. Dossier's "53 carry in-document proof" conflates proof-count
  with 14:00-count. Substantive anchor (13:00 CT) unaffected.
- **M5** §5: "extremes no worse than neutral" is contradicted by its own
  numbers on the drawdown leg (z>1.5 median −2.27% vs neutral −1.64%; p05
  −4.83% vs −4.31%; z<−1.5 p05 −4.88% vs −4.31%). The vol-bucket flatness and
  corr −0.07 null result stand; the drawdown wording should be softened to
  "mildly deeper medians at extremes, within noise" or similar.
- **M6** §0 CoT provenance sha 4f9cd78944ee79dc is the pre-integration-fix
  tidy (now .bak); canonical is f7a2719e745c2f6f. Numbers unaffected (§4
  above); pointer must be updated with the fix erratum.
- **M7** §3 "held-contract volume 13-16k/day in 2024-03-01..12" — actual held
  volumes that window: 1,069..13,222 (median ~3.1k); only 03-11/03-12 reach
  ~13k. Understates the thinness; qualitative point (calendar rule holds a
  thin contract post-roll) intact and stronger.

### NOTE
- **N1** §1 "low 1.0392 — the all-data low": it is the held-chain low; the
  literal panel-wide low is 1.0293 (6BU3 deferred contract, 2-lot print,
  2022-09-26 01:02 UTC — same day). Scope wording should say held chain.
- **N2** §1 "4.5× the median day": base unstated — held-chain median 78.9k →
  4.7×; all-front-contract median 85.5k → 4.4×. Fine as an approximation.
- **N3** Auditor's first-pass independent code reproduced the fall-back DST
  trap the lane's lib explicitly avoids — corroborates lane DST correctness;
  after fix, all chain stats match to ≥4 decimals.
- **N4** 6B_a5_cot.json predates the CoT tidy fix by 45 minutes; verified
  numerically identical on 6B — no rerun required.
- **N5** The differential series uses FRED DFEDTARU latest (not vintage-true)
  — disclosed in dossier §3; benign for same-day policy targets; this audit
  used the same source (verification is source-internal, cross-checked
  against BoE parquet).

## 7. Verdict

**PASS_WITH_MINOR_ERRATA.**

- 0 BLOCKER, 0 MAJOR, 7 MINOR (M1-M7), 5 NOTE (N1-N5).
- ~36 headline numbers recomputed fresh from raw inputs with an independent
  implementation: every numeric claim reproduces exactly (the two initial
  mismatches — ann-vol/VR/DD micro-deltas — were the AUDITOR's own DST bug,
  corrected; and the Spearman +0.84, which is a genuine dossier text error).
- The round's headline overturn (v1's 4 rolls sat in a zero-differential
  window; roll gap = rate-differential carry, corr 0.84, ≈73% of CIP) is
  CONFIRMED and, on the differential side, even cleaner than stated
  (exactly 0.00, not −0.25..0.00).
- Required errata: M1, M2, M3, M4, M5, M7 text corrections in
  dossiers_v2/6B_DEEP_v2.md + M6 provenance sha update (fold with the
  integration-fix erratum). None blocks downstream use of the 6B v2 evidence.
