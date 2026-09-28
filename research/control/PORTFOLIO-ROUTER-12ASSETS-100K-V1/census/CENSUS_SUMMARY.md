# CENSUS_SUMMARY — 1,200 ideas sorted & verdicted (A1 integration, 2026-09-28)

Program PORTFOLIO-ROUTER-12ASSETS-100K-V1, pre-GO. Source corpus:
`research/control/FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/` (verified 12 ×
S1–S100 = 1,200, no gaps/dups). **Every row is HYPOTHESIS/NOT_RUN.** Protocol,
verdict tree and rubric were frozen in `CENSUS_PROTOCOL.md` BEFORE dispatch and
before any PnL existed (none exists for any of these ideas anywhere).

Artifacts: `CENSUS_1200.tsv` (merged, sorted, priority_scored) ·
`shortlist.tsv` (global exemplars: DISTINCT_TESTABLE ∪ PIT_UNPROVEN-with-payer,
deduped by family×mech_key) · `parts/census_<SYM>.tsv` (lane originals) ·
`counts.json` · `merge_census.py` (reproducible merge).

## Headline counts (1,200 rows)

| Verdict | Count | Share |
|---|---|---|
| VARIANT_OR_DUPLICATE | 548 | 45.7% |
| PIT_UNPROVEN | 433 | 36.1% |
| BLOCKED_DATA | 121 | 10.1% |
| NOT_FALSIFIABLE | 68 | 5.7% |
| DISTINCT_TESTABLE | 15 | 1.3% |
| BLOCKED_COST | 15 | 1.3% |

Data status: PUBLIC_UNEVIDENCED 753 · MISSING 207 · PARTIAL_REPO 156 ·
HAVE_REPO 50 · NA 33 · PROSPECTIVE_ONLY 1.

917 distinct (family × mech_key) groups; 87 groups span >1 symbol (cross-symbol
duplication concentrated in trend/breakout/carry/event-drift classes).

## Verdict × symbol

| Symbol | DISTINCT | PIT_UNPROV | BLOCK_DATA | BLOCK_COST | NOT_FALS | VARIANT | Σ |
|---|---|---|---|---|---|---|---|
| EURUSD | 2 | 23 | 11 | 0 | 10 | 54 | 100 |
| GBPUSD | 1 | 11 | 5 | 0 | 2 | 81 | 100 |
| USDCAD | 4 | 33 | 5 | 0 | 3 | 55 | 100 |
| USDJPY | 1 | 38 | 9 | 9 | 8 | 35 | 100 |
| AUDUSD | 7 | 42 | 6 | 0 | 0 | 45 | 100 |
| NZDUSD | 0 | 24 | 6 | 0 | 8 | 62 | 100 |
| USDCHF | 0 | 39 | 9 | 0 | 4 | 48 | 100 |
| XAUUSD | 0 | 29 | 14 | 4 | 10 | 43 | 100 |
| XAGUSD | 0 | 17 | 17 | 2 | 4 | 60 | 100 |
| BRENT | 0 | 66 | 15 | 0 | 9 | 10 | 100 |
| WTI | 0 | 62 | 19 | 0 | 0 | 19 | 100 |
| NATGAS | 0 | 49 | 5 | 0 | 10 | 36 | 100 |

## The 15 DISTINCT_TESTABLE (all clusters' fully-evidenced candidates)

| gid | Family | mech_key | Data | P | Title |
|---|---|---|---|---|---|
| GBPUSD-S079 | H | cta_unwind_join | HAVE_REPO | 8.77 | Systematic-flow unwind anticipation |
| USDJPY-S012 | B | tokyo_range_fade | HAVE_REPO | 8.77 | Tokyo session range fade |
| EURUSD-S027 | C | vol_expansion_onset | HAVE_REPO | 8.15 | ATR-ratio expansion onset |
| AUDUSD-S001 | A | ema_stack_trend | PARTIAL | 7.85 | EMA-stack multi-TF trend |
| AUDUSD-S003 | A | adx_macd_persistence | PARTIAL | 7.85 | ADX-filtered momentum persistence |
| AUDUSD-S017 | B | td_sequential_fade | PARTIAL | 7.85 | DeMark TD-Sequential exhaustion fade |
| AUDUSD-S087 | I | volume_profile_poc | PARTIAL | 7.85 | Volume-profile POC acceptance |
| AUDUSD-S088 | I | round_number_defense | PARTIAL | 7.85 | Round-number defense fade |
| AUDUSD-S002 | A | donchian_breakout | PARTIAL | 7.23 | Donchian 20/55 breakout |
| AUDUSD-S046 | E | weekday_seasonality | PARTIAL | 7.23 | Day-of-week seasonality |
| USDCAD-S025 | C | range_retest_continuation | PARTIAL | 7.23 | Multi-week range retest continuation |
| USDCAD-S047 | E | winter_seasonality | PARTIAL | 7.23 | Winter CAD strength seasonality |
| EURUSD-S009 | A | macd_divergence_exit | HAVE_REPO | 6.62 | MACD-histogram exhaustion exit |
| USDCAD-S002 | A | donchian_breakout | PARTIAL | 5.69 | Donchian 20/55 classic |
| USDCAD-S004 | A | tsmom_20d | PARTIAL | 5.69 | 200DMA dislocation momentum |

All 15 live on 5 pairs only (EURUSD GBPUSD USDJPY AUDUSD USDCAD) — exactly the
pairs L1 found with repo price history. Zero DISTINCT_TESTABLE on NZDUSD,
USDCHF, XAUUSD, XAGUSD, BRENT, WTI, NATGAS is the honest consequence of
fail-closed data status, not absence of ideas (those symbols' candidates sit in
PIT_UNPROVEN/BLOCKED classes).

## Shortlist (deduped candidate pool)

`shortlist.tsv` = 385 rows (371 PIT_UNPROVEN + 14 DISTINCT_TESTABLE global
exemplars with named payers). By family: G-XASSET 65, F-EVENT 56,
H-POSITIONING 45, D-CARRY_TERM 45, A-TREND 36, B-MEANREV 34, C-BREAKOUT 30,
I-STATARB 30, E-SESSION 27, J-REGIME_OPT 17. **This is a candidate POOL, not a
test slate** — the master plan's test slate is a small data-gated subset
(macro-PIT exemplars near SOFR/EFFR + the 15 DISTINCT_TESTABLE), because 433
PIT_UNPROVEN rows reflect that the repo has evidenced PIT for exactly one
macro series (SOFR/EFFR daily).

## Honest caveats

1. `mech_key` granularity is agent-assigned; near-synonym keys (e.g.
   `cot_zscore_fade` vs `cot_extreme_fade`) mean 917 overstates true mechanism
   novelty and 87 cross-symbol groups understate it. The plan's F-0-style
   mechanism-class court re-adjudicates before any slot is granted.
2. Frozen order (dup-before-blocked): some VARIANT rows would also be
   data-blocked; per-symbol handoffs record those deltas. Verdict counts answer
   "is the idea distinct?", data_status cross-tab answers "is it runnable
   here?" — both published, neither hidden.
3. Ancestry sources: FAMILY_FAILURES_DIGEST.tsv (169 rows) is the family-level
   authority; JEV-REGIME-ROUTER-V2 / REGIME-STRATEGY-MAPPING-V1 /
   REGIME-GATED-COMBO-V1 deaths are charter-cited (not digest rows) and every
   lane flagged this in its handoff.

## Integration incidents (disclosed)

- `census_BRENT.tsv` arrived with the `s_id` column omitted (20 fields);
  `merge_census.py` inserted `s_id` derived from `gid` — mechanical repair, no
  content change, lane original otherwise untouched.
- 3 census dispatches (USDCAD, NZDUSD, XAGUSD) died on model-pool rate limit
  (error 1302) and were re-dispatched fresh; no partial outputs from the dead
  attempts were consumed (P-22 respected).
- WTI lane emitted 21-col header consistent with protocol; BRENT is the only
  structural defect found. 0 unresolved exemplar-reference errors across 1,200
  rows after merge.

## Erratum (A1, post-skeptic, 2026-09-28)

1. **Priority formula re-run (skeptic F-3):** the first merge implemented the
   frozen §5 rubric with 4 mapping deviations (M/F intermediate subscores
   unused; FX-spot auto C=3 despite UNMEASURED commission/swap; VARIANT A=0
   applied only to ancestry-hit rows). `merge_census.py` v2 implements the
   published formula literally (C: vehicle-known=2 incl. FX-spot, TBC=1;
   VARIANT rows all inherit A=0). Re-run changed scores (top 8.77 vs 9.23),
   changed NO verdict, no counts, and NO ordering of the DISTINCT_TESTABLE
   rows; max VARIANT score now 7.85 < every top DISTINCT row, as the frozen
   formula intends. `CENSUS_1200.tsv`/`shortlist.tsv` regenerated
   (sha256@16: dd6424c71b193449 / fe9b920916cadcd9 — see plan pin refresh).
2. **Cross-lane adjudication note (skeptic F-2):** `donchian_breakout` was
   verdicted VARIANT-vs-dead-PSV1-class in 12 rows but DISTINCT_TESTABLE in
   AUDUSD-S002/USDCAD-S002 with the same dead ids present. The F-0
   mechanism-class court at sleeve admission re-adjudicates; strict reading
   could reduce the headline 15 DISTINCT_TESTABLE to 13. Disclosed, not
   silently normalized (per-lane verdict authority respected at census stage).
3. Skeptic prereview verdict on the integrated set: AUTHORIZED_FOR_OWNER_REVIEW
   (0 CRITICAL / 0 HIGH; F-1..F-3 MEDIUM advisory — see
   `skeptic/A7_PREREVIEW.md`).
