# ERRATA_SUMMARY — DOSSIER-ERRATA-V2 (FUTURES-DEEPRESEARCH-V2-20261003)

- Lane: **DOSSIER-ERRATA-V2** (resumed after power-outage kill; partial work
  continued, not restarted).
- Base: worktree `prep/futures-behavior-10syms-20261002` @
  `26d96eb4bdd4be85e151055dace3354638498a44` (verified at resume).
- Authority inputs: the six independent A7 audit reports
  `audit/a7_{nq,es,6e,6j,6b,6a}/A7_DEEP_*.md` (all read in full).
- Owned artifacts: `dossiers_v2/*.md`, this file, `analysis/NQ_a5_cot.py`
  (+ `NQ_deep_lib.py` loader touched as part of the F2 fix),
  `dispatch/handoff_DOSSIER-ERRATA-V2.json`.
- Method: for each dossier, the A7 findings list was re-read and diffed
  against the current dossier text; ONLY missing items were applied; every
  erratum is marked `[ERRATUM <finding-id>]` at the correction site with
  old→new and evidence = finding id; nothing silently rewritten. Each
  dossier carries a full old→new ERRATA ledger section.

## 1. INCIDENT — power outage, resume from partial (2026-10-03)

A power outage killed the errata session mid-run. Partial state at kill:
NQ (12 ERRATUM sites), ES (9), 6E (14) fully applied incl. their ledgers;
6J partially applied (header summary + §0 headline sites done; §6/§7/§8/§9
sites and the §10 ledger NOT yet written); 6A and 6B untouched (0 sites).
This run resumed exactly there: NQ/ES/6E were re-diffed against their A7
findings and confirmed complete (0 additions needed); 6J's remaining sites
were applied; 6A (3 MINOR) and 6B (7 MINOR) were applied in full. No work
was duplicated; no non-owned file was touched.

## 2. Per-dossier application state

| dossier | A7 verdict | required errata | applied pre-outage | added this run (resume) | ERRATUM sites now |
|---|---|---|---|---|---|
| NQ | PASS_WITH_ERRATA | F1-F3 MAJOR, F4-F6 MINOR (+N1-N4 notes) | all 6 findings + N-note disclosures + §10 ledger | none (verified complete) | 12 |
| ES | PASS_WITH_ERRATA (0B/1M/3m/5n/1 INCIDENT) | M-1 MAJOR, m-1..m-3 MINOR, n-1 advised | all + I-1 re-verified (nonprice root repopulated, fixed tidy sha f7a2719e745c2f6f present) + §12 ledger | none (verified complete) | 9 |
| 6E | PASS WITH ERRATA (2 MAJOR, 3 MINOR) | MAJOR-1/2, MINOR-3a-d, MINOR-4/5 | all + retractions in §1/§7/§9/open-q5 + §11 ledger | none (verified complete) | 14 |
| 6J | PASS_WITH_REQUIRED_ERRATA (5 MAJOR, 6 MINOR) | M-1..M-5, m-1..m-6 | header summary, §0 headline sites (M-1..M-4, m-1..m-3, m-5, m-6), §1 m-5, §4 sites, §5 preamble | §6 M-2 "the record" claim; §7-H2 M-3 "3–7 days"; §7-H3 m-6 era ranges; §7-H5 M-4 overclaim + m-1 + M-1 81-op + m-2 6th-largest; §8 M-5 2022-09-20 + m-4 "21→20 depleted"; §9 2022-10-24 NOT_RUN bullet resolved; 4× PENDING_SOURCE_TIDY → SOURCE_TIDY_RESOLVED; §10 ledger written | 27 |
| 6B | PASS_WITH_MINOR_ERRATA (7 MINOR) | M1-M7 | none (untouched at kill) | all 7 (M1 Spearman; M2 zero-diff parenthetical; M3 QT/FOMC dating; M4 59/59-proof/53@14:00/58-panel — 2 sites; M5 drawdown wording; M6 CoT sha f7a2719e745c2f6f; M7 thinness 1,069..13,222) + §11 ledger | 9 |
| 6A | PASS_WITH_FINDINGS (3 MINOR) | MINOR-1/2/3 | none (untouched at kill) | all 3 (MINOR-1 "~4×" → 1.1×/1.3×/3.9×-vs-09:00, 2 sites; MINOR-2 2,704,795 → 2,703,211 post-exclusion, 2 sites; MINOR-3 DD peak 2021-02-25 → 02-24) + ERRATA ledger | 8 |

Out-of-dossier items flagged for the owner (NOT edited by this lane, per
lane ownership):
- `analysis/NQ_a7_quality.json` `vendor_hole_2020` block (alias framing +
  "2026-05-29" typo) — regenerate, do not hand-edit (NQ F1/F6).
- `analysis/6E_a5_cot.json` block `cot_oi_vs_venue_oi` (median_ratio
  2.0003, raw-sum) — superseded by MAJOR-1; regenerate with publication
  dedupe on next a5 run.
- `dispatch/handoff_DEEP-NQ.json` known_limitations[0]/[2]/[4] +
  recommended_next_action(1) — superseded by F1/F5/F2; that handoff remains
  the DEEP-NQ lane's record.
- `DISPATCH_MANIFEST.json` "53/58" FOMC figure — not reproducible (A7-ES §5).

## 3. NQ_a5_cot.py loader fix (ERRATUM F2) — DONE, verified

The pre-fix loader filter selected ZERO rows on the fixed
`cftc_legacy_tidy.parquet` (silent-empty re-run hazard; A7-NQ r5 part B).
Fix applied (pre-outage, re-verified this run): `NQ_a5_cot.py` now pins
series id `COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE`
(via `NQ_deep_lib.load_cot_nq_all_lines()`) and HARD-FAILS on any row count
≠ 850 / window ≠ 2010-06-15..2026-09-22. Executed read-only verification
this run: the loader selects exactly **850 rows, 2010-06-15→2026-09-22**
from the on-disk fixed tidy. Numbers unchanged (A7-NQ r5 part A: every §5
number reproduces exactly on the fixed tidy).

## 4. 6J MOF op-count erratum — SOURCE_TIDY RESOLVED

The A7-6J M-1 erratum was written against a defective 81-row normalized MOF
tidy (300 of 386 official daily ops dropped by a blank-month carry-forward
defect, incl. the in-window 2022-10-24 ¥0.73T op), initially carried as
PENDING_SOURCE_TIDY. This run verified the regenerated source tidy ON DISK:
`~/.my-quantitative-data/futures-nonprice-10syms/normalized/mof_intervention_tidy.parquet`
= **386 rows** (pre-fix copy preserved as `.bak_81rows_20261003`), with the
**2022-10-24 row present (¥7,296 × ¥100m, JPY_buying, USD-sold/JPY-bought)**.
Resolved wording in 6J (header, §0-6, §5, §9, §10 ledger): op count **9 → 10**
is now stated as completed fact ("SOURCE_TIDY_RESOLVED"), not pending; the
2022-10-24 anatomy row (−0.84%, 1.75× vol, TR 98th pct, 246,433 contracts)
stands as measured by A7-6J.

## 5. A7-6E forward-flag cross-check — venue-OI join audit (per-dossier verdict)

A7-6E MAJOR-1 established that GLBX statistics stat_type-9 (open interest)
publishes MULTIPLE rows per (contract, ref_date) — duplicate publication
events (7,615 pairs ×2, 107 ×3, 8 ×4, 107 ×1) — so a raw-row SUM doubles (or
triples) venue OI, while a dedupe-to-latest reconciles 1:1 with CFTC legacy
futures-only OI (median ratio 1.0000). Forward flag: which dossiers' OI
numbers rest on a raw-sum venue-OI join vs a deduped table? Code-level
verdict per dossier (all loaders inspected this run):

| dossier | OI consumer (script) | aggregation on stat_type-9 rows | verdict |
|---|---|---|---|
| **NQ** | `analysis/NQ_a3_term.py` (`oi_crossovers`) | `pivot_table(..., values="quantity", aggfunc="last")` — dedupe to latest publication per (date, contract) | **DEDUPED — clean.** §3's OI-crossover stat (2–3-day lead, 8 artifact-free events, tagged OBSERVED-2023+) rests on the deduped table; NQ makes NO venue-vs-CFTC level/ratio claim anywhere. |
| **ES** | `analysis/ES_build_panel.py` (`es_statistics_daily.parquet`) → `ES_chains.py` OI chain + roll OI table | `sort_values("pub_ts").groupby(["raw_symbol","ref_date","stat_type"]).last()` then `pivot_table(aggfunc="last")` — dedupe to latest publication | **DEDUPED — clean.** The M-1-restated same-trading-day OI crossover and the "prior published OI" chain rule rest on the deduped daily table; no venue-vs-CFTC level claim exists. |
| **6E** | `analysis/6E_a3_term.py` (OI crossover) | `groupby(["contract","ref_date"]).agg(oi=("quantity","last"))` — deduped | **DEDUPED — clean.** The §5 OI-vs-volume crossover finding (5–6-day lead, 7/12 rolls) is UNAFFECTED (explicitly adjudicated by A7-6E MAJOR-1). |
| **6E** | `analysis/6E_a5_cot.py` (`cot_oi_vs_venue_oi`) | `d["quantity"].sum()` over ALL stat_type-9 rows on each CoT date — **RAW-SUM, no dedupe** | **AFFECTED — the sole raw-sum consumer in the corpus.** Produced the retracted "2.000× convention" claim (median ratio 2.0003; 3-publication days → "3.000×"). RETRACTED in the 6E dossier (§1/§7/§9/open-q5); the JSON block is flagged for regeneration with dedupe. No other 6E number flows from this join — all CoT-side numbers are CFTC-sourced. |
| **6B** | `analysis/6B_a3_term.py` (`oi_vs_volume_crossover`) | per contract `sort_values("dt")` + `drop_duplicates("rd", keep="last")` — deduped | **DEDUPED — clean.** The 5–7-day OI-lead stat (median −6, n=11) rests on deduped per-contract OI; A7-6B recompute matched exactly. |
| **6J** | `analysis/6J_a3_term.py` (OI migration) | `pivot_table(index="d", columns="raw_symbol", values="quantity")` — default `aggfunc="mean"` over duplicate publications | **DEDUPE-EQUIVALENT (mean, not sum) — clean.** Duplicate publications are usually identical quantity, so the mean equals the published value (never a 2× inflation). A7-6J independently recomputed the crossovers from raw parquet: 12/12 direction and the corrected 1–3-day lead verify. No level claim vs CFTC exists. |
| **6A** | `analysis/6A_a6_hypo_quality.py` §4 (OI-front crossovers) | `groupby(["ref_date","contract"])["quantity"].sum().unstack()` — **SUM over duplicate publications per (date, contract)** | **RAW-SUM PER CONTRACT — timing-only use, audit-verified; flagged for reuse.** The sum inflates per-contract OI levels on multi-publication days, but the statistic is a WITHIN-VENUE crossover timing comparison (both sides carry the same publication multiplicity on ordinary days), not a level/ratio claim; A7-6A R5 independently recomputed roll-anchored and confirmed 2–3-day lead 12/12 with the lane's example dates reproducing exactly (also adjudicated the one disclosed 2024 outlier as an unanchored-scan artifact). No venue-vs-CFTC level claim exists in 6A. REUSE RULE: if 6A OI is ever consumed for LEVELS or cross-source ratios, re-aggregate to last-publication-per-(contract, ref_date) first. |

Bottom line: exactly one dossier number-family rested on a raw-sum
venue-OI join — 6E a5's venue-vs-CFTC ratio — and it is already retracted
and flagged for regeneration. Every other OI consumer in the corpus
dedupes (last-publication) or is dedupe-equivalent (mean), with the single
caveat that 6A's sum-aggregation is safe only for the timing comparisons
it was used for and must not be reused for levels.

## 6. Reproduction / verification commands (this lane, read-only)

```bash
# MOF tidy state (§4)
python -c "import pandas as pd; d=pd.read_parquet('~/.my-quantitative-data/futures-nonprice-10syms/normalized/mof_intervention_tidy.parquet'); print(len(d))"  # 386

# NQ loader fix (§3) — selects the __ALT__ series on the fixed tidy
python -c "import sys; sys.path.insert(0,'analysis'); import NQ_deep_lib as L; c=L.load_cot_nq_all_lines(); print(len(c[c.series_id=='COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE']))"  # 850
```

— End of ERRATA_SUMMARY.
