# DELTA-VERIFY-DOSSIERS — independent verification of DOSSIER-ERRATA-V2

Lane `DELTA-VERIFY-DOSSIERS` (fresh-context; the original 7 A7 auditors were
lost to a power outage — this lane re-verifies their fixes) · task
`FUTURES-DEEPRESEARCH-V2-20261003` · 2026-10-03 · worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep`, branch
`prep/futures-behavior-10syms-20261002`. Dispatch base
`26d96eb4bdd4be85e151055dace3354638498a44`; observed HEAD at verification
`4f266528439639bd8e58d7e293cf33156ad5e04a` (drift = unrelated
`successor_design_2026-10-02` commits by other lanes; every file audited here
is an untracked working-tree artifact under the ignored
`research/control/FUTURES-DEEPRESEARCH-V2-20261003/` path, so the drift does
not touch audited content — dossier sha256 prefixes re-hashed this run and
match the DOSSIER-ERRATA-V2 handoff artifact block exactly). READ-ONLY except
`audit/delta/dossiers/**` + `dispatch/handoff_DELTA-DOSSIERS.json`. No network,
no key use, no raw/data writes. Vendor + nonprice roots treated read-only.

Scope: verify that every finding in the six A7 audit reports
(`audit/a7_{nq,es,6e,6j,6b,6a}/A7_DEEP_*.md`) was correctly applied by
implementer **DOSSIER-ERRATA-V2** to the current dossiers (`dossiers_v2/*`),
as marked `[ERRATUM …]` blocks + in-place fixes, plus the
`analysis/ERRATA_SUMMARY.md` §5 OI-join cross-check. Method per finding:
(1) locate the erratum site in the current dossier; (2) confirm old→new matches
the A7 prescription with exact numbers; (3) grep the whole file for the struck
old strings — they must survive only inside marked erratum/ledger text;
(4) where the finding demands live data (NQ loader, MOF tidy, CoT tidy sha),
re-derive independently with the venv Python.

## VERDICT: **PASS — 40/41 finding-level items VERIFIED, 1 PARTIAL, 0 NOT_VERIFIED**

The single PARTIAL is cosmetic in scope but real: 6E MINOR-5 was applied at one
of its two §7 label sites; the phrase "strict-past 3y percentile ≥80" survives
live at `6E_DEEP_v2.md:391` (details in the 6E table). No stale numeric claim
survives anywhere; every MAJOR retraction/restatement is in place with the A7's
exact evidence numbers.

Dossier sha256 prefixes (verified unchanged vs the DOSSIER-ERRATA-V2 handoff):
NQ `d3cf621cec3adc22` · ES `05f0874f66184ed7` · 6E `846055454ea7c795` · 6J
`ef95ad8dd062e654` · 6B `bc8a1dc357a2107a` · 6A `76d32f1c776ceaa6`;
loader `NQ_a5_cot.py` `7b5eedda1d02f363`, `NQ_deep_lib.py` `ec810b4d9b789906`.

---

## 1. A7-NQ (`audit/a7_nq/A7_DEEP_NQ.md`) → `dossiers_v2/NQ_DEEP_v2.md`

Verdict source: PASS_WITH_ERRATA (13/13 headline recomputes MATCH).

| finding | verdict | evidence (current dossier line refs) |
|---|---|---|
| F1 (MAJOR) 2020 "vendor hole" → SYMBOLOGY ALIAS reclass; strike "degraded 03-16" + "NQU0 trickle"; cancel §9 backfill; §6 NOT_RUN entry; re-measure caveat | **VERIFIED** | §7 L192: full reclassification block with every A7/r6 number (id 16908; `NQU8-NQM9` 92,075 bars / 24,686,121 contracts 2018-08-15→2020-05-31; `NQM0` 19,406 / 5,159,596, last bar 2020-06-19 13:29Z; hole window 58 dates / 21,824,572 / 625,650 Mar-23 / range 6,838..690,803; 169,992 / 100,034 = 80,628+19,406; NQH0 17,932 / NQU0 30,204 / NQZ0 971; only dash symbol >5M, 24.7M vs 0.97M; recovery view rule) + both supporting-narrative corrections (NQH0 expiry 350,956-540,580 contracts 03-16..20; true front 6.8k-690k/day) + "$0.62 quote recorded, NOT executed" + re-measure mandate. §9 L217: backfill item struck-through + CANCELLED + replacement priority. §6 L180: inventory entry. §0 L27: "reclassified by ERRATUM F1". Grep: "degraded"/"trickle"/"entirely absent" survive only inside erratum text (L192, L233). |
| F2 (MAJOR) §5 CoT source → `__ALT__` series; loader re-point before re-run | **VERIFIED (live)** | §5 L148: source paragraph re-pointed to `COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE`, canonical `COT_LEGACY_NQ` = E-mini 1,082 rows 2006-2026, "every §5 number re-verified unchanged", canonical-line owner addendum (18.39% vs 17.13%; OI 359k→284k vs 95k→302k; %OI 6.8→3.1 vs 8.7→2.0). Loader: `NQ_a5_cot.py` L34-48 pins ALT_ID with `EXPECTED_ROWS = 850` / window `("2010-06-15","2026-09-22")` hard guard. **Live run this lane** (`NQ_deep_lib.load_cot_nq_all_lines()` on the on-disk fixed tidy): ALT series = **exactly 850 rows, 2010-06-15→2026-09-22**; canonical = 1,082 rows. N4 docstring fix present in `NQ_deep_lib.load_cot_nq()` (L315ff). |
| F3 (MAJOR) "16.9% (volume rule)" → 20.1%, direction reverses | **VERIFIED** | §1 L71: "19.6% vs **20.1%** (volume rule; n=4,168 returns on the delivered hole-aware series)" + [ERRATUM F3] explaining non-reproducibility (no variant yields 16.9%), stale pre-DST-fix figure, direction reversal (19.6% < 20.1%), unfitness re-anchored to §3 thinness. Grep: "16.9%" only at L9 (summary), L71 (erratum), L235 (ledger). |
| F4 (MINOR) stale ACF/VR prose | **VERIFIED** | §1 L45: ACF(1) −0.076; rolling-252d median −0.042 (p10-p90 −0.134..+0.071); VR(20) p10 0.522 — all four corrected values in place + [ERRATUM F4]. Grep: old values only inside ledger L236. |
| F5 (MINOR) FOMC provenance 132/92/85 | **VERIFIED** | §4 L124: "147 archived files = 132 a-statements + 15 b/c …; 128 matched" [ERRATUM F5]; L126: "92 statements … 85 of 92 are 2pm" [ERRATUM F5: was "106 … 98 of 106"]; H3 L174: "92 primary-source statement timestamps [ERRATUM F5: was 106]". |
| F6 (MINOR) window typo + Friday-close count | **VERIFIED** | §9 L217: struck item carries the typo only in strikethrough + "the window end typo '2026-05-29' is also corrected to 2020-05-29 — ERRATUM F6"; JSON typo flagged (not hand-edited, L244). §2 L85: "126 era-A Friday-early-close sessions … [ERRATUM F6: was '123']". Grep: "123 era-A" only in ledger L238. |
| N1-N4 (NOTEs) | VERIFIED (disclosed) | Ledger rows L239-242 (N1 statistic named; N2 row-set disclosure; N3 control-pool note; N4 folded into F2). |

Residual observation (non-blocking, recorded): three legacy "hole" shorthand
mentions survive outside erratum blocks — L60 footnote "*COVID recovery spans
the 2020 vendor hole (§7)*", L62 "hole-adjusted sum of log rets", L196 "2020 =
202 clean sessions (hole)". None re-asserts absence, degradation, or a backfill
need (§7's reclassification governs, and A7-NQ itself uses "NaN-hole series"
terminology); judged cosmetic.

## 2. A7-ES (`audit/a7_es/A7_DEEP_ES.md`) → `dossiers_v2/ES_DEEP_v2.md`

Verdict source: PASS_WITH_ERRATA (13/13 mandated recomputes match exactly).

| finding | verdict | evidence |
|---|---|---|
| M-1 (MAJOR) OI-lead = timezone artifact → same-trading-day restatement (§0.1/§4/§8-H1) + publication-lag nuance | **VERIFIED** | §0.1 L57-59: "crosses on the **SAME trading day** as volume [ERRATUM M-1: was '1 calendar day before volume' — a timezone-labeling artifact]". §4 L226-243: full [ERRATUM M-1 — RESTATED] block — ts_ref = Chicago date of UTC midnight of trading day T (T−1); all twelve OI crossovers SUNDAYS (e.g. 2023-12-10); stat_type-6 proof 1.03–1.14× vs 0.87–12.3×; same trading day 12/12 (2023-10+ era); `oiq.index < s` consumes same-trading-day OI published next morning ~08:28–08:58 CT (98.4% agreement; no PnL impact). §8-H1 L390-396: restated + "PARAM-GAP dissolved". Grep: "leads volume"/"1 calendar day"/"positions migrate first" only inside erratum/ledger text (L42, L227-228, L394, L506). |
| m-1 (MINOR) mismatch-year attribution | **VERIFIED** | §4 L256-258: "2017×1, 2018×2, 2019×1, 2022×1 — there is NO 2021 mismatch (2021 spreads were negative with DFF≈0.08…) [ERRATUM m-1: was '2017 transition rolls and 2021']". |
| m-2 (MINOR) sd(ON) range | **VERIFIED** | §0.4 L73-75: "0.25–1.4%/day … [ERRATUM m-2: was '0.4–1.4' — … 2017 sd(ON) = 0.25%; honest full range 0.25–1.41]". Grep: "0.4–1.4" only in erratum/ledger. |
| m-3 (MINOR) elevation band + "early Globex" label | **VERIFIED** | §0.6 L83-86: "(1.1–2.7×) through +165 min [ERRATUM m-3: was '1.3–2.7× for 3+ hours' — dips 1.107 (+105) and 1.212 (+120)]". §5 L294-296: "+105→+165 min (RTH tail: 13:00 CT anchor ⇒ 15:00–15:45 CT; NOT 'early Globex' — ERRATUM m-3)". Grep: "early Globex" only in the negation + ledger. |
| n-1 (NOTE, advised) v1 +67.75 cross-check reframe | **VERIFIED (applied)** | §4 L264-270: "consistent in sign and magnitude (0.25-pt mark-convention difference…); the two +67.75s are different quantities that coincide numerically — ERRATUM n-1, was 'matches v1's +67.75 exactly — cross-validation PASS'". Grep: "cross-validation PASS" only inside erratum/ledger. |
| I-1 (INCIDENT) nonprice root emptied mid-audit | **VERIFIED** | §12 ledger L514: incident row + re-verification "root is again POPULATED (normalized/ incl. fixed cftc_legacy_tidy.parquet sha256 f7a2719e745c2f6f… verified present)". **Independently confirmed this run**: root repopulated; `shasum -a 256` of `normalized/cftc_legacy_tidy.parquet` = `f7a2719e745c2f6f…`. |
| n-2/n-3/n-4/n-5 (NOTEs) | VERIFIED (disclosed, not required) | Ledger L511-513 + L516 owner-facing note ("53/58" DISPATCH_MANIFEST figure not reproducible; dossier counts stand). A7's required-errata list did not include n-2..n-5. |

## 3. A7-6E (`audit/a7_6e/A7_DEEP_6E.md`) → `dossiers_v2/6E_DEEP_v2.md`

Verdict source: PASS WITH ERRATA (12/12 headline recomputes match; 2 MAJOR).

| finding | verdict | evidence |
|---|---|---|
| MAJOR-1 venue-OI "2.000× convention" retraction (§1/§7/§9/q5) | **VERIFIED** | §1 L88-116: RETRACTED block with every A7 number (7,615 pairs ×2 / 107 ×3 / 8 ×4 / 107 ×1; 3.000× days 2023-11-21/10-24/11-07, 2024-02-27/07-30; dedup median 1.0000, p05 1.0000 / p95 1.00005, 150/156 weeks ±0.2%; probe 2024-06-04 venue 671,736 == CFTC 671,736; residual weeks 2025-06-17 ×1.31 / 2026-03-17 ×1.27 / 2025-09-16 ×1.18 = just-expired 6EM5 232,435; a3-deduped vs a5-raw inconsistency; §5 crossover unaffected; hygiene rule). §7 L398-402: RETRACTED bullet ("joins remain fine WITHOUT scale normalization provided publications are deduplicated"). §9 L477-480: struck register line + RESOLVED. §10 q5 L502-508: struck + RESOLVED/RETRACTED + replacement item. Grep: "2.000"/"engine-critical"/"scale-normalize" survive only inside retraction/ledger text. |
| MAJOR-2 CIP vintage-sensitivity downgrade (§5 + §8-H2) | **VERIFIED** | §5 L264-289: [ERRATUM MAJOR-2] block — PIT-as-of r=−0.107 / sign 26/27 / residual +3.77 ticks from ALFRED year-end vintages (2019…2024 + 2026-09-30; no 2025 vintage); both readings on the record (stale-vintage vs latest-vintage-artifact); €STR latest-only; "PIT-robust: sign + one-sided residual; vintage-dependent: r=0.91 magnitude". §8-H2 L422-435: downgraded from "CONFIRMED descriptively"; registration spec MUST carry quantified sensitivity + real-time-SOFR source decision. Grep: "CONFIRMED descriptively" only inside erratum/ledger. |
| MINOR-3a "n=1,751" → 1,746/1,745 | **VERIFIED** | §3 L154-155 with [ERRATUM MINOR-3a]; grep clean. |
| MINOR-3b rolling-63 min date → 2026-01-16 | **VERIFIED** | §3 L164-165 with [ERRATUM MINOR-3b]; grep clean. |
| MINOR-3c p05 → 5.66 | **VERIFIED** | §3 L182-183 with [ERRATUM MINOR-3c]; grep clean. |
| MINOR-3d quiet hours → 17:00–18:00 / 23:00–24:00 CT (1.004%/1.015%; 01:00 CT = 3.99%) | **VERIFIED** | §4 L217-221 with [ERRATUM MINOR-3d]; grep clean. |
| MINOR-4 control-Wednesday peak → mode 13:59 CT (162/~340), 12:00–12:02 secondary (26) | **VERIFIED** | §6 L357-361 + §10 q4 L498-501, both with [ERRATUM MINOR-4]; FOMC ×17.2 stated unaffected; grep clean. |
| MINOR-5 "strict-past 3y percentile" label → "rolling 3y percentile incl. current week" | **PARTIAL** | §7 L377-380: latest-percentile site FIXED (label + strict-variant invariance 6.52/7.68 / 9.08 disclosed) with [ERRATUM MINOR-5]. **BUT** the second §7 site was missed: L391 still reads live "crowded-long weeks (strict-past 3y percentile ≥80, n=54)" — the exact imprecise label A7 required correcting (ledger row L526 claims "§7 labels", plural). One-line residual fix needed. |
| NOTE-6/7 | VERIFIED (disclosed) | Ledger L527-528. |

## 4. A7-6J (`audit/a7_6j/A7_DEEP_6J.md`) → `dossiers_v2/6J_DEEP_v2.md`

Verdict source: PASS_WITH_REQUIRED_ERRATA (5 MAJOR / 6 MINOR).

| finding | verdict | evidence |
|---|---|---|
| M-1 (MAJOR) MOF op count 9→10; 386-op record; 2022-10-24 anatomy row; SOURCE_TIDY_RESOLVED | **VERIFIED (live)** | Header L20-29 (386 ops 1991-05-13→2026-05-06; 300 dropped incl. 2022-10-24; regenerated tidy verified on disk; `.bak_81rows_20261003`; [ERRATUM M-1/n-2: was "81 ops 1991-04→2026-05" — wrong on both ends]). §0-6 L113-135 ("All 10 MOF yen-buying ops [ERRATUM M-1: was 'all 9'…]"; Q4 aggregate 63,499 = 56,202 + 7,296 + 1 rounding unit; 2022-10-24 anatomy −0.84% / 1.75× / TR 98th / 246,433; positivity now 8/10). §5 preamble L303-320 (full 10-op list with amounts; row-519 blank-month detail; "every dropped row has a blank month field… 0 exceptions"). §9 L513-519: struck NOT_RUN bullet RESOLVED. **Independent on-disk verification this lane**: `mof_intervention_tidy.parquet` = 386 rows, 1991-05-13→2026-05-06, 2022-10-24 row present (7,296 × ¥100m, JPY_buying, provenance `c2869df8…`), `.bak_81rows_20261003` = 81 rows. Grep: "81 ops"/"all 9"/"PENDING_SOURCE_TIDY" only inside erratum/ledger/incident text. |
| M-2 (MAJOR) "record short" → deepest-since-2007; series record −188,077 @2007-06-26 | **VERIFIED** | §0-8 L147-157 + §6 L355-364: "deepest short since 2007 / 2nd-deepest of the 20-year series; the SERIES RECORD is −188,077 on 2007-06-26" [ERRATUM M-2: was "record speculator short"]; flip +363k ~9mo; trough-to-peak 367k. |
| M-3 (MAJOR) OI-lead "3–7 days" → 1–3 calendar days vs raw volume crossover (mode 2) | **VERIFIED** | §0-7 L137-146, §4 L280-284, §7-H2 L390-394 — all three sites carry "1–3 calendar days (12/12, mode 2)" + [ERRATUM M-3] noting "3–7" is the lead over the k=5 SWITCH and the Sep-2026 exemplar (OI 09-08 → volume 09-11 = 3 days) contradiction. Grep: "3–7 days" only inside erratum text/ledger. |
| M-4 (MAJOR) "every ≥3% down leg ends at an op" → 4 of 14 | **VERIFIED** | §0-3 L82-92 ("4 of the 14 down-legs terminate within 0–2 sessions of a MOF op / op-window"; the other ten listed with all ten A7 counterexample dates incl. 2024-11-14 −11.4% "has no attached event") + §7-H5 L428-433. Grep: "every … down leg" only inside erratum text/ledger. |
| M-5 (MAJOR) 2022-09-20 "holiday" → held-rule artifact | **VERIFIED** | §8 L476-491: "15 exchange holidays + 1 held-rule artifact (2022-09-20)" + full [ERRATUM M-5] block (exchange open; Z2 traded 125,303 lots over 1,357 bars; k=5 held ceased U2; 09-21 rolled return spans two calendar days off a 97-bar stale U2 close; panel itself hole-free; chain attribution was an inferred pass). |
| m-1 TR 85th–100th (2026-05-04 = 0.849); vol 1.75–4.79× | **VERIFIED** | §0-6 L119-123, §5 L322-325, §7-H5 L434-436. |
| m-2 "6th-largest" → 11th-most-negative of 1,082 (10 below: six 2007, four 2024) | **VERIFIED** | §0-8 L153-155, §7-H5 L443-445. |
| m-3 pairs 50–83 sessions; medians −216..−90 (three pairs −97/−93/−90) | **VERIFIED** | §0-4 L93-97, §4 L267-269. |
| m-4 "21 depleted" → 20 | **VERIFIED** | §8 L486-490. |
| m-5 k=5 spec-vs-code disclosure (bit-identical sensitivity) | **VERIFIED** | §1 L168-182: [ERRATUM m-5 — spec-vs-code disclosure] with the H1 "executable PIT" caveat. |
| m-6 era roll-gap ranges → per-year medians + per-roll ranges | **VERIFIED** | §0-4 L98-103, §4 L275-277, §7-H3 L404-408 (0.52/0.13; 5.50/5.46; 2.87/2.42; ranges −0.44..+3.95 / +4.63..+6.60 / +1.70..+4.29). |
| n-1..n-6 (NOTEs) | VERIFIED (no change required) | Ledger L530-532 states why; consistent with A7 §Findings. |

## 5. A7-6B (`audit/a7_6b/A7_DEEP_6B.md`) → `dossiers_v2/6B_DEEP_v2.md`

Verdict source: PASS_WITH_MINOR_ERRATA (7 MINOR).

| finding | verdict | evidence |
|---|---|---|
| M1 "rank corr = +0.84" → Spearman +0.744 | **VERIFIED** | §3 L248-252: "rank corr (Spearman) = +0.744 [ERRATUM M1 … `spearman_corr` = 0.7445; Pearson +0.84 is correct]". Grep: old string only in erratum/ledger. |
| M2 v1-overturn parenthetical | **VERIFIED** | §3 L237-246: roll-date differential "exactly 0.00pp"; v1 gaps −3..+5; v2 re-measured −4..+1; [ERRATUM M2: was "(diff −0.25..0.00pp → gaps −2..+3 ticks)" — wrong on both ends; 80 of 395 days nonzero context; OVERTURN CONFIRMED]. |
| M3 "+13 outlier" dating | **VERIFIED** | §3 L256-261: "2 days before the 2022-06-01 QT start and ~2 weeks before the next scheduled FOMC (2022-06-15, archive `monetary20220615a.html`) [ERRATUM M3: was 'one week before a scheduled Fed hike']". |
| M4 FOMC counts 59/59-proof/53@14:00/58-panel (2 sites) | **VERIFIED** | §0 L46-51 + §4 L324-330, both with [ERRATUM M4]; §4 lists the 6 non-14:00 statements (08:00/08:30/09:10/10:00×2/17:00 ET; 5 COVID + 2025-08-22). |
| M5 drawdown wording | **VERIFIED** | §5 L361-369: "extremes carrying mildly deeper medians, within noise (z>1.5 median −2.27% vs neutral −1.64%; p05 −4.83% vs −4.31%; z<−1.5 p05 −4.88% vs −4.31%) [ERRATUM M5: was 'extremes no worse than neutral']"; vol flatness + corr −0.07 stand. |
| M6 CoT tidy sha 4f9cd789… → f7a2719e745c2f6f | **VERIFIED (live)** | §0 L52-59: canonical FIXED tidy sha + [ERRATUM M6: was 4f9cd78944ee79dc, the pre-fix tidy now `.bak_prefix_mixed_20261003`; whitespace-only for 6B, 470 rows, numbers unchanged]. **Independently confirmed**: current tidy sha256 prefix = `f7a2719e745c2f6f`. |
| M7 "13-16k/day" → 1,069..13,222 (median ~3.1k) | **VERIFIED** | §3 L293-297 with [ERRATUM M7] ("understated the thinness … STRONGER as corrected"). Grep: "13-16k" only inside erratum/ledger. |
| N1-N5 (NOTEs) | VERIFIED (no change required) | Ledger L578-583 discloses all five. |

## 6. A7-6A (`audit/a7_6a/A7_DEEP_6A.md`) → `dossiers_v2/6A_DEEP_v2.md`

Verdict source: PASS_WITH_FINDINGS (3 MINOR).

| finding | verdict | evidence |
|---|---|---|
| MINOR-1 "~4× average half-hour" → 1.1×/1.3×/3.9×-vs-09:00 (2 sites) | **VERIFIED** | §2.1 L205-212: "**11:30 2.35** (the Sydney-morning modal peak — ~1.1× the average half-hour (2.08%) and ~1.3× the median (1.77%); ~3.9× only vs the quiet 09:00 Sydney-open slot (0.60%)) [ERRATUM MINOR-1…]" and §4.3 L355-359 using the A7's prescribed wording. |
| MINOR-2 2,704,795 → 2,703,211 post-exclusion (header + §7) | **VERIFIED** | Header L23-28 ("2,703,211 outright … [ERRATUM MINOR-2: was '2,704,795 … after excluding 1,584' — pre-exclusion count…]") and §7 L461-462 ("1 break-window bar in 2,703,211 [ERRATUM MINOR-2…]"). Grep: 2,704,795 only inside erratum/ledger. |
| MINOR-3 USD-cycle DD peak 2021-02-25 → 2021-02-24 | **VERIFIED** | §1.2 L146: "2021-02-24 [ERRATUM MINOR-3: was 2021-02-25 — fresh running-max close is 02-24; depth/trough unchanged]"; depth −25.2%, trough 2025-04-08 intact. |
| NOTE-1..4 | VERIFIED (no change required) | ERRATA ledger L507-511 discloses all four. |

## 7. ERRATA_SUMMARY §5 cross-check (OI-join verdict table)

Dispatch required spot-verification of 2 "DEDUPED" verdicts; this lane
inspected the aggregation lines of **all seven** table rows at code level:

| claimed row (script) | claimed aggregation | code check | verdict |
|---|---|---|---|
| NQ `NQ_a3_term.py` | `pivot_table(..., aggfunc="last")` | L256-257: `oi.pivot_table(index="d", columns="contract", values="quantity", aggfunc="last")` | **CONFIRMED (DEDUPED)** |
| ES `ES_build_panel.py` | `groupby(...).last()` + pivot last | L222-225: `st.sort_values("pub_ts").groupby(["raw_symbol","ref_date","stat_type"], as_index=False).last()` then `pivot_table(..., aggfunc="last")` | **CONFIRMED (DEDUPED)** |
| 6E `6E_a3_term.py` | `agg(oi=("quantity","last"))` | L56-57: exact match | **CONFIRMED (DEDUPED)** |
| 6E `6E_a5_cot.py` | raw `quantity.sum()` | L156: `tot = d["quantity"].sum()` over all stat_type-9 rows on the CoT date | **CONFIRMED (sole RAW-SUM)** |
| 6B `6B_a3_term.py` | `sort_values("dt")` + `drop_duplicates("rd", keep="last")` | L186-189 per contract: exact match | **CONFIRMED (DEDUPED)** |
| 6J `6J_a3_term.py` | `pivot_table` default mean | L220: `oi.pivot_table(index="d", columns="raw_symbol", values="quantity")` (pandas default aggfunc="mean") | **CONFIRMED (dedupe-equivalent)** |
| 6A `6A_a6_hypo_quality.py` | `groupby(...)["quantity"].sum().unstack()` | L186: exact match | **CONFIRMED (SUM — timing-only use, reuse rule stated)** |

Bottom-line of §5 holds: the only raw-sum venue-OI level join in the corpus is
6E a5's retracted 2.000× ratio; every other consumer dedupes or is
dedupe-equivalent; 6A's sum is gated by the stated no-levels-reuse rule.

## 8. Completeness / ledger cross-checks

- ERRATUM-mark occurrences counted this run: NQ 14, ES 9, 6E 14, 6J 27, 6B 9,
  6A 8 — ES/6E/6J/6B/6A match the DOSSIER-ERRATA-V2 handoff claims (12/9/14/27/9/8)
  exactly except NQ (14 string occurrences vs "12 sites" claimed — a
  counting-convention difference, e.g. two [ERRATUM] mentions inside one L45
  sentence and two inside L217; not a defect).
- Every dossier carries a full old→new ERRATA ledger section (NQ §10, ES §12,
  6E §11, 6J §10, 6B §11, 6A "ERRATA applied" block) as claimed.
- Out-of-dossier items (NQ_a7_quality.json vendor_hole_2020 block;
  6E_a5_cot.json cot_oi_vs_venue_oi block; handoff_DEEP-NQ.json limitations;
  DISPATCH_MANIFEST "53/58") are flagged-for-owner, NOT edited — consistent
  with lane ownership; verified untouched by grep-level absence of edits here
  (JSON blocks still carry the superseded values, correctly disclosed).

## 9. Verdict tally and residual fix list

- 41 finding-level items checked across the six A7 reports: **40 VERIFIED,
  1 PARTIAL, 0 NOT_VERIFIED.**
- ERRATA_SUMMARY §5: all 7 rows code-confirmed.
- Residual fix for the owner/next errata pass (one line): `6E_DEEP_v2.md:391`
  — "crowded-long weeks (strict-past 3y percentile ≥80, n=54)" → "rolling 3y
  percentile incl. current week" (A7-6E MINOR-5 second site; numbers
  themselves are correct and the strict-variant invariance is already
  disclosed at the fixed site L377-380).
- Cosmetic (no action demanded): NQ L60/L62/L196 legacy "hole" shorthand.

— End of DELTA_VERIFY. Every check above is reproducible read-only from the
listed file/line evidence.
