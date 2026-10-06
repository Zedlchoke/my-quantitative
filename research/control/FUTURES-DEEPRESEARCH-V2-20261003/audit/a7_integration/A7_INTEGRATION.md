# A7-INTEGRATION — independent audit of INTEGRATION-FIX-V2 outputs

Lane `A7-INTEGRATION` (fresh-context auditor) · task `FUTURES-DEEPRESEARCH-V2-20261003`
· 2026-10-03 · worktree `prep` @ `26d96eb4bdd4be85e151055dace3354638498a44`
(branch `prep/futures-behavior-10syms-20261002`, verified). READ-ONLY except
this directory + the A7 handoff. No network calls, no key use, no fixes applied.

Audited: `analysis/integration/**` (contaminant scan + NQ 2020 probe), the
nonprice normalize/tests/report edits, `handoff_INTEGRATION-FIX-V2.json`, and
the regenerated out-of-tree tidy parquets. Method: independent re-derivation
from raw (auditor-written scripts in this dir), not re-runs of the lane's
measurement code; the lane's own test suite WAS rerun as shipped.

## VERDICT: **PASS_WITH_FINDINGS** — 0 BLOCKER, 2 MAJOR, 3 MINOR, 2 NOTE

All three load-bearing claims of INTEGRATION-FIX-V2 verify exactly and
independently: (1) the CoT exact-name fix delivers 10 canonical legacy series
× 1,082 weeks × 0 duplicate dates with NQ restored to 2006-01-03 and siblings
preserved under `__ALT__`; (2) the six-root contaminant inventory is correct to
the bar (11,660 foreign-outright + per-root spread counts); (3) the NQ 2020
hole is A_ALIAS_NOT_ABSENCE, fully present in our delivery, and the $0
view-rule remap + cancellation of the $0.62 re-request are sound. The findings
below are erratum/disclosure defects and one small residual data defect in the
regenerated TFF/disagg tidy — none invalidates the lane's conclusions, but
F-1 and F-2 must be corrected before any registered cycle consumes the
affected artifacts.

## 1. CoT tidy at source — VERIFIED (with F-1, F-3)

Independent re-derivation from the 21 raw `deacot20{06..26}.zip`
(`a7_cot_rederive.py` / `.json`; auditor's own family keywords, not the lane's
tables):

| canonical series | market lines (raw census) | union |
|---|---|---|
| NQ | `NASDAQ-100 STOCK INDEX (MINI)` 840 (2006-01-03..2022-02-01) + rename `NASDAQ MINI` 242 | 1,082 |
| ES | `E-MINI S&P 500 STOCK INDEX` 840 + rename `E-MINI S&P 500` 242 | 1,082 |
| 6B | `BRITISH POUND STERLING` 840 + rename `BRITISH POUND` 242 | 1,082 |
| CL | `CRUDE OIL, LIGHT SWEET - NYMEX` 840 + rename `WTI-PHYSICAL - NYMEX` 242 | 1,082 |
| NG | `NATURAL GAS - NYMEX` 840 + rename `NAT GAS NYME - NYMEX` 242 | 1,082 |
| 6E / 6J / 6A / GC / SI | single line each | 1,082 |

- All 10 canonical series in the delivered tidy: exactly 1,082 rows, 0
  duplicate dates, contiguous Tuesday weekly grid 2006-01-03..2026-09-22 (0
  irregular gaps). **NQ canonical starts 2006-01-03** (the archive floor; the
  erratum states this correctly — the A7 dispatch's "restored from
  2006-06-15" expectation was itself slightly off; "not 2010" holds: the old
  series verifiably started 2010-06-15).
- No in-scope line dropped: every raw name matching a family keyword that is
  absent from the tidy is a genuinely different instrument (S&P dividend /
  total-return / rate products, ICE basis/penultimate/diff swaps, CBOT 100oz
  gold / 5000oz silver, NFX shipping, `EURO FX/*XRATE` crosses, Coinbase
  1-oz gold…). Sibling lines preserved: **14 `__ALT__` series / 4,527 rows**;
  total 15,347 = 10,820 canonical + 4,527 ALT (matches handoff).
- Pre-fix state independently reproduced twice: (a) the retained
  `.bak_prefix_mixed_20261003` (sha256 `4f9cd789…` — verified bit-identical to
  the erratum's old sha) shows dup dates **ES 1,126 / CL 928 / NQ 548 / GC 164
  / NG 10 / SI 5 / FX 0**, 13,369 rows, NQ starting 2010-06-15 at 850 distinct
  dates; (b) a sandbox rerun of the git-HEAD pre-fix normalizer
  (`old_cftc_normalize_from_git.py`, OUT redirected into this dir) reproduces
  the same table exactly, including the trailing-space Consolidated variant
  (`…EXCHANGE ` 238 rows + `…EXCHANGE` 612 = the 850-row Consolidated line).
- New-file sha chain verified: legacy old `4f9cd789…` → new `f7a2719e…`; fin
  new `1dbb5e93…`; erratum block present at
  `PUBLIC_DATA_ACQUISITION_REPORT_VI.md` §ERRATUM 2026-10-03 (line 76).
- Suite rerun as shipped: **48/48 PASS, exit 0** (includes the 7 new
  regression checks; pre-fix dup pins shown in the PASS message match my
  measurements).
- Cross-lane reconciliation: DEEP-ES `ES_cot.py` filter (exact 2 e-mini
  spellings) == new canonical `COT_LEGACY_ES`; DEEP-NQ's Consolidated line
  reproduces 1:1 from `COT_LEGACY_NQ__ALT__…CONSOLIDATED…` (850 rows,
  2010-06-15..2026-09-22, OI medians 2010-2013 = 94852/89278/91118/78607 —
  exact vs `NQ_a5_cot.json`; micro 306 / NASDAQ MINI 242 exclusions match);
  old 6B as-is series (1,082 / 0 dup, same two spellings) == new canonical
  6B. "No dossier number changes" is corroborated.

## 2. Contaminant scan — VERIFIED (with F-4)

Full independent rescan of ALL six roots (`a7_contaminant_rescan.py`,
auditor-written classifier; 28,212,754 bars — row totals match the lane's to
the bar):

| root | total | root-family | spread/strip | foreign outright |
|---|---:|---:|---:|---:|
| NQ | 7,330,320 | 6,688,533 (40 syms) | 641,787 (119) | **0** |
| ES | 8,710,520 | 7,825,657 (40 syms) | 884,863 (151) | **0** |
| 6E | 3,436,733 | 3,054,311 (90) | 375,722 (341) | **6,700** = 6JZ7 4,831 (2020-04-23..08-17) + SIJ5 1,869 (2025-09-10..10-10) |
| 6J | 3,120,241 | 2,843,938 (87) | 275,066 (295) | **1,237** = 6AV3 (2020-03-24..07-13) |
| 6B | 2,738,672 | 2,547,494 (88) | 189,039 (301) | **2,139** = GCQ4 (2020-07-28..11-16) |
| 6A | 2,876,268 | 2,703,211 (86) | 171,473 (278) | **1,584** = 6BU5 (2020-05-12..08-17) |

Foreign grand total 11,660; every per-symbol bar/volume/date detail matches
`contaminant_scan.json`; sibling-lane reconciliations (6BU5/6JZ7/SIJ5/GCQ4)
match the DEEP handoffs' counts.

**Canonical regex adjudication** (`^{ROOT}[FGHJKMNQUVXZ][0-9]$`): full symbol
census per root (159/191/433/383/390/365 distinct symbols) — every non-dash
symbol in every root matches the outright pattern; every dash symbol is a
`LEG-LEG` calendar-spread shape; **zero** unclassifiable and **zero**
multi-digit-year symbols anywhere. The regex therefore wrongly excludes and
wrongly includes nothing observed (no `ESM2016`-style two-digit-year forms
exist in this feed). In-family decade-wrap is real (e.g. `NQM0` spans both
Jun-2010 and Jun-2020, first 2010-06-06, last 2020-06-19) and is correctly
kept in-family; consumers must use dates to disambiguate contracts a decade
apart — inherent vendor convention, not a scan defect. Spread/strip shares
(FX 6–15%, NQ/ES 8–10%) are order-of-magnitude sane and match the md.

## 3. NQ 2020 alias adjudication — VERIFIED, conclusions AGREED (with F-2, F-5)

All verified from OUR delivered parquet only (`a7_nq2020_verify.py`; no
network):

- `instrument_id 16908`: label `NQU8-NQM9` 2018-08-15..2020-05-31, **92,075
  bars / 24,686,121 contracts**; label `NQM0` 2020-06-01..06-19, 19,406 /
  5,159,596. Monthly ramp exact (Dec-19 1,958 → Feb-20 26,367 → Mar 6,449,335
  → Apr 9,134,344 → May 9,065,853).
- Hole window 2020-03-23..05-29 on id 16908: **58 distinct trading dates, 0
  gaps** (re-derived expected Globex calendar = Mon–Fri + Sunday opens minus
  Good Friday 2020-04-10 → exactly the 58 observed; Memorial Day 5/25
  present), **21,824,572 contracts**, Mar-23 alone 625,650 (COVID-peak front
  volume).
- Probe window 2020-03-01..06-30 local totals: all-symbols **169,992** ==
  vendor parent record_count (recorded live in the probe JSON); id-16908
  **100,034** == vendor raw `NQM0` 100,034 (= 80,628 alias + 19,406 `NQM0`);
  NQH0 17,932 ==; NQU0 30,204 ==. NQJ0 absent locally.
- Mechanism confirmed: with the outright regex applied, the hole window shows
  only the NQU0 trickle (6,412 bars / 16,444 contracts) + 58 NQZ0 bars —
  exactly DEEP-NQ's "deferred-only" view. The front bars are invisible purely
  because of the dash label.

**Adjudication (agreed):** A_ALIAS_NOT_ABSENCE is correct and fully evidenced
(our delivered chunk contains exactly the vendor's record count for the
window; the front future's entire volume sits under id 16908's dash label).
The $0 view-rule remap (`instrument_id==16908 AND date<2020-06-01 →
'NQM0'`) is vendor-corroborated by the current-symbology record_count equality
and is implementable from delivered data. The $0.62 re-request is unnecessary
— we already hold 100% of the window; cancelling the spend is sound.

## 4. Process — VERIFIED

- Handoff `handoff_INTEGRATION-FIX-V2.json`: canonical
  `zcode_orch_v3_handoff@1` (field superset of sibling DEEP handoffs);
  `dispatch_sha == actual_start_sha == 26d96eb4…` (== verified worktree HEAD);
  `commit_sha: null` with honest disclosure; `tree_status` matches `git
  status` exactly (3 tracked mods within grant + untracked lane outputs;
  foreign FX-BACKFILL changes correctly identified and untouched). All 9
  declared output sha256s re-verified — **9/9 match**.
- No key material: `db-` token scan over `analysis/integration/**` and the
  handoff — clean; the probe reads the key in-process only and redacts errors.
- Raw untouched: 6 vendor parquet files sampled (both probe-critical
  `AV1R-O1M-NQ-DELTA` chunks, AV1T ES, AV1T 6E, AV1B 6J backfill2) are
  hash-identical to the DATA-BACKUP mirror SHA-verified at 2026-10-02 23:30
  UTC, i.e. before the lane ran; nonprice raw has no Oct-3 writes; only the
  two documented tidy parquets changed (+ `.bak`).
- "DEEP lanes' caches already conformant": verified in code for **5 lanes**
  (dispatch asked 2): `6E_deep_lib.py` `^6E([FGHJKMNQUVXZ])(\d)$`,
  `6J_deep_lib.py` `^6J([FGHJKMNQUVXZ])(\d)$`, `6A_deep_lib.py`
  `^6A([FGHJKMNQUVXZ])(\d)$`, `NQ_deep_lib.py` `NQ[HMUZ]\d`,
  `ES_build_panel.py` `^ES[HMUZ][0-9]$`. All dash-excluding → every foreign
  stray incl. the new 6AV3 was already excluded from their panels.

## FINDINGS

### BLOCKER — none.

### MAJOR

**F-1. Regenerated DISAGG canonical series still carry 365 duplicate dates
(same defect class the fix targeted), undisclosed and ungated.**
`cftc_tff_disagg_tidy.parquet` (new, `1dbb5e93…`): `COT_DISAGG_CL/GC/NG/SI` =
1,424 rows over 1,059 distinct dates each — 365 value-identical duplicate
rows per series on 2010-01-05..2016-12-27, caused by double-reading the
overlapping archives `fut_disagg_txt_hist_2006_2016.zip` + annual
`fut_disagg_txt_2010..2016.zip` (provenance shas confirm). TFF series are
clean (845 each). The erratum's "0 duplicate dates" guarantee,
`assert_canonical_clean()` and the 7 new regression tests all cover LEGACY
only; no artifact discloses the residual. Impact: any consumer grouping
`COT_DISAGG_*` by `(series_id, observation_period)` double-counts 2010–2016.
Required: dedupe (or source precedence) + extend the generation gate and one
regression test to the fin tidy + one erratum line. (Values are identical, so
`drop_duplicates` is lossless; pre-fix state was worse — CL 1,649 dups.)

**F-2. Evidence misreported: NQJ0 error is HTTP 504, not HTTP 422; the
"April serial not in the GLBX feed" conclusion is an inference from absent
evidence.**
The recorded artifact (`nq2020_hole_probe.json`) says
`"raw_NQJ0_record_count…": {"error_redacted": "BentoServerError HTTP504"}` —
a gateway timeout, which supports nothing about symbol resolvability. Yet
`nq2020_hole_probe.md` and the handoff (tests log_digest AND
known_limitations) state "HTTP 422 — unresolvable in GLBX.MDP3 (April serial
not in feed)". This violates the evidence law (missing evidence must stay
NOT_RUN, never inferred) in two delivered artifacts. Not load-bearing (the
169,992 == 169,992 parent-total equality carries the adjudication
independently of NQJ0). Required: erratum correcting the code and retracting
the not-in-feed claim to "probe timed out (504); serial coverage NOT_RUN".
Related slip in the same handoff: "7 metadata calls"/"(record_count x6,
billable_size x1, get_cost x1 -> 8 calls total)" — the script makes 8 calls;
both "7"s are wrong (all free; no budget impact).

### MINOR

**F-3. Erratum's old TFF/disagg row count is wrong: says 17,337; the actual
pre-fix file had 13,898.** The old sha `d798ed27…` is correct and the pre-fix
file is preserved in the DATA-BACKUP iCloud mirror (SHA-verified 2026-10-02
23:30 UTC, before the lane ran): mirrored `cftc_tff_disagg_tidy.parquet` =
13,898 rows, sha `d798ed27…`; my git-HEAD pre-fix code rerun reproduces 13,898
exactly (per-series: DISAGG CL 2,708 / GC 1,588 / NG 1,434 / SI 1,429; TFF ES
1,966 / NQ 1,393 / FX 845×4). The 17,337 figure (which appears only in the
erratum) overstates the old table by 3,439 rows. Also: unlike legacy, no
`.bak` was kept for the fin tidy — the mirror + git are the only old-state
evidence. Required: erratum correction (13,898).

**F-4. Spread/strip prose total overstated by exactly 100,000.**
`contaminant_scan.md` and the handoff summary say "2,637,950 spread bars";
the sum of their own (correct, and my re-verified) per-root counts is
**2,537,950** (641,787+884,863+375,722+275,066+189,039+171,473). Required:
erratum/one-line correction.

**F-5. "Only such alias in the entire six-root panel" is false; a second
dash→outright instrument exists with negligible impact.**
`NQ instrument_id 2563` carries `NQH5-NQM5` 2014-12-18..2016-05-31 (5,946
bars / 395,166 contracts) then `NQU6` 2016-06-01..09-16 (92,208 / 13,215,646)
— the same vendor dash-alias pattern as 16908. The md's parenthetical "(no
other dash symbol anywhere carries front-scale volume)" survives (395k over
18 months is deferred-scale), but the uniqueness claim does not, and a
view-rule hard-coding only id 16908 leaves 2563's thin tail quarantined.
Required: erratum noting instrument 2563; recommend generalizing the remap
rule (resolve via instrument_id where a dash label precedes an outright label
on the same instrument) or documenting the second exception.

### NOTE

**N-1.** A7 dispatch expectation "NQ e-mini restored from 2006-06-15" is
itself slightly off: the restored canonical starts **2006-01-03** (archive
floor; erratum already states this correctly). The load-bearing contrast
("not 2010") holds — old start 2010-06-15 verified from `.bak`.

**N-2.** The probe md's aside "DEEP-NQ's 51 = weekday count" does not
reconcile with the delivered data: the 58 sessions are 49 weekdays + 9 Globex
Sunday opens (Good Friday 2020-04-10 closed). Immaterial to the adjudication;
fold into the F-2 erratum pass if convenient.

## Errata required (consolidated)

1. `PUBLIC_DATA_ACQUISITION_REPORT_VI.md` erratum block: old fin tidy rows
   17,337 → **13,898** (F-3); add DISAGG residual-dup disclosure + planned
   dedupe (F-1).
2. `analysis/integration/nq2020_hole_probe.md` + handoff log_digest /
   known_limitations: NQJ0 **HTTP504 timeout**, retract "422 / not in feed"
   (F-2); call count 7 → 8 (F-2); "only such alias" → add instrument 2563
   (F-5); 51-weekday aside → 49+9 (N-2).
3. `analysis/integration/contaminant_scan.md` + handoff summary: spread total
   2,637,950 → **2,537,950** (F-4).
4. Owner action (already recommended by the lane, endorsed by this audit):
   cancel the NQ 2020 backfill spend; apply the id-16908 view-rule remap
   (generalized per F-5) before recomputing DEEP-NQ 2020 aggregates.

## Reproduction (this directory)

- `a7_cot_rederive.py/.json` — raw deacot census, tidy cross-check, weekly grid.
- `old_cftc_normalize_from_git.py` + `oldtidy_sandbox/` — pre-fix normalizer
  rerun (from `git show HEAD:…`), reproducing both old tables.
- `a7_contaminant_rescan.py/.json` — six-root rescan + full symbol census.
- `a7_nq2020_verify.py/.json` — NQ 2020 alias evidence + alias-uniqueness sweep.
- Test suite rerun: `…/nonprice_acquisition/tests/test_parse.py` → 48/48 PASS.

Nothing in this audit is a GO; descriptive/infrastructure only. Prep law
intact; no raw/data writes; no key use; no network.
