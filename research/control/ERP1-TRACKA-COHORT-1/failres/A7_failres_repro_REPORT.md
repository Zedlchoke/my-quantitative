# A7_failres_repro_REPORT — independent reproduction of failres-attrib Phase A

**Labels (everything below): `A7_INDEPENDENT_REPRODUCTION` ·
`FAILURE_ROOT_CAUSE_RESEARCH` · `DIAGNOSTIC_OUTCOME_EXPOSED` ·
`SINGLE_SOURCE_PANEL` · `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` ·
`PAPER_TIER`.** A7 is an audit lane: it recomputes from bytes with its own
minimal code, never repairs or edits the audited lane's artifacts.

**Verdict: ALL_MATCH on all three layers.** Every headline claim C1–C5 of
`ATTRIB_failres_REPORT.md` (failres-attrib, work commit `da4a92c2`, audited
here at base `3b1c29fa`) reproduced exactly at reporting precision by
independent code. No discrepancy found. Findings (all MINOR, all about
display/precision or check-harness, none affect any claimed number) at §5.

Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1/failres-a7`,
branch `orca/erp1-ta1-failres-a7`, start HEAD `3b1c29fa5401daf9` (clean),
venv python 3.12.14. Heavy lock `FREE_PROVEN` before/after; the one heavy
job (full-corpus rebuild) held the machine-wide lock 07:38:05→07:38:25Z,
`FINISHED`, no conflicts.

---

## L1 — plane rebuild from M1 bytes: PASS (exact)

Method (own code, committed builder read for reference only, NOT executed
— see fallback disclosure in PROVENANCE): the committed diag builder
cannot run standalone in this worktree (probe-derived pair config and
corpus bytes are not committed here), so per the dispatch's sanctioned
fallback A7 re-aggregated the H1 ANC plane with its own code following the
documented convention, and strengthened the data gate: **every one of the
4,014 day files (BID+ASK) was sha256-verified against the manifest
committed in THIS worktree before decode** (the manifest's sha equals the
diag lane `copy_verify_EURUSD.json` source-manifest sha `12304eac…` —
authority chain intact), in addition to the mandated 20-file sample
(seed 20260926 → 20/20 OK).

- Corpus: 2,007 days × 2 sides, 2021-01-01..2026-06-30, read from the
  diag lane's READ-ONLY `data_local` (no writes outside A7's worktree).
- Rebuilt: 130,911 valid ANC 15m bars, 0 duplicate ts → **30,550 H1 ANC
  bars** (vs audited 30,550; day-close = 19:00 bar).
- **Comparison vs the audited `bars1h_ANC_EURUSD.parquet` (failres-attrib
  copy, sha `2e175b06…4f9d` = expected): row count equal, ts arrays equal,
  max abs diff = 0.0 on b_o/b_h/b_l/b_c/a_o/a_c/s_open/s_close.**
  Byte-exact content equality — the audited plane is fully determined by
  the pinned M1 corpus and the documented convention.
- GBPUSD not rebuilt (dispatch scope); its audited plane copy
  (`5aad8415…05b7`) was used read-only for L2/L3.

## L2 — book recomputation with A7's own executor: ALL_MATCH

A7's own fill-law executor reimplemented from the engine docstring
(`engine.py` NOT imported): signal = target on closed bar t, fill at t+1
open at the opposite quote (buy b_o+k·s_o / sell a_o−k·s_o; day-close
force-flat at close prices with s_c), no fills on/after the day-close
bar, per-trade pips rounded 2dp. Signal laws imported from committed
`tracka_lib` (the frozen objects under audit — allowed); SHORT/LONG
session targets, folds, exit-type inference, k=0 cost decomposition and
all aggregation are A7's own. EURUSD ran on A7's REBUILT plane.

**(a) C5 reconciliation — every number Δ=0.0 (tol ±0.05):**
R-DAEMON F1..F6 = −188.8 / −884.4 / +1,049.8 / +348.3 / −191.5 / +257.0
(RT 164/166/164/166/159/157, total 1,062 RT +812.2); totals R-ORIG
+7,322.7, R-ANCHOR +1,052.7, SHORT_ALWAYS +704.6, LONG_ALWAYS −1,665.5;
GBPUSD R-DAEMON total −1,708.9, F3 −1,272.7. k=0/k=1 schedule identity
asserted per book.

**(b) C1 exit-type split — matches, including all 24 pair-fold cells:**
EURUSD FF full −5,466.2 (839 RT), TE full +6,278.4 (223), REVERSAL 0;
F2 FF −2,116.5 (128) / TE +1,232.1 (38). GBPUSD FF full −9,429.7 (842) /
TE +7,720.8 (224); F2 FF −1,489.9 (131) / TE +1,601.1 (41). Per-fold
FF/TE nets AND RTs equal the REPORT §2 table in all 12 pair-folds;
FORCE_FLAT negative and TARGET_EXIT positive in every one.

**(c) C2 F2 gross/cost/direction — matches exactly:** gross −769.1,
cost −115.3, net −884.4; long −696.0 (95 RT) vs short −188.4 (71 RT).
Supplement: A7's executor at k=1.5/2.0 gives F2 −942.05 / −999.7 (the
REPORT's −942.1 is the 1dp display rounding; JSON stores −942.05).

**(d) C3 flip-day pools F2 — matches:** flip days −1,455.5 (102 RT,
mean −14.2696 → REPORT's −14.27), non-flip +571.1 (64 RT, +8.9234 →
+8.92).

**(e) C4 beta pull F2 — matches:** daily Pearson rho(daemon, SHORT) =
−0.188858 (REPORT's −0.189); daemon − SHORT = −1,723.2.

## L3 — artifact self-consistency + test re-run: ALL_MATCH

48 checks over the committed JSONs (both pairs) + the lane's pytest suite
in this worktree:

- I1 per-trade `net == gross + cost` on ALL 3,240 EURUSD + all GBPUSD
  rows (≤0.011 2dp rounding): 0 violations.
- I2 trade-table fold sums/RTs == agg `reconciliation` per-fold and
  totals for the 3 R-books (trades JSON carries R-books only, by schema —
  verified); SHORT/LONG totals covered by I3.
- I3 daily join sums == trade sums, per book full panel and daemon per
  fold, both pairs.
- I4 REPORT §3/§4 vs committed agg JSON: F2 direction/mode-entry/flip/
  beta/terciles/exit-type and k-decay all equal (at printed precision).
- I5 GBPUSD F3 block internally consistent: long+short, fade+follow,
  flip+nonflip, hour buckets, exit types each sum to the F3 net
  −1,272.7; all §4 quoted values present and equal.
- **pytest `failres/tests/test_failres_attrib.py`: 8 passed in 2.28s**
  (planes staged into this worktree's `failres/data_local/derived/`,
  gitignored).

## 5. Findings (numbered; none change any verdict)

1. **MINOR — k-decay display rounding.** REPORT prints F2 k=1.5 as
   −942.1; the true value (JSON and A7 executor agree) is −942.05.
   Harmless 1dp half-up display rounding; sign/magnitude conclusions
   unaffected.
2. **MINOR — rho display rounding.** REPORT prints −0.189 for
   −0.188858 (agg JSON). Same class, harmless.
3. **INFO — trades JSON scope.** `failres_attrib_trades_*.json` carries
   only R-DAEMON/R-ORIG/R-ANCHOR (SHORT/LONG live in the recon and daily
   tables). The REPORT's §7 description ("gross+cost on 100 sampled
   trades per pair") matches this scope; documented here so future
   readers don't misread RT counts (e.g. "n_rows 3240" vs 1,062 daemon
   RTs = 3 R-books).

## 6. Limitations / incidents

Limitations: EURUSD-only rebuild (GBPUSD on the sha-pinned audited
copy); signal laws imported from committed tracka_lib by dispatch design;
T.SignalPlane plumbing (ts/hour/day/skip masks) reused to feed those
imported laws — the fill/PnL state machine, exit types, folds and
aggregation are A7's own; REPORT display roundings checked at printed
precision; OUTCOME-EXPOSED surfaces, never promotable.

Incidents: none outside this lane. Lane-internal harness corrections
during the audit (disclosed in PROVENANCE; no audited artifact touched):
per-pair F2 FF/TE claims, printed-precision tolerances, trades-JSON book
scope, pytest cwd.

## 7. Artifacts

- `failres/failres_a7_repro_results.json` — machine-readable checks
  (L1 + 52 L2 checks + 48 L3 checks) and verdicts.
- `failres/failres_a7_repro_PROVENANCE.json` — shas, lock record,
  fallback disclosure, limitations, incidents.
- `failres-a7-work/scripts/a7_sample_sha.py`, `a7_build_h1_anc.py`,
  `a7_recompute.py`, `a7_l3_checks.py` — A7's code (committed).
- `failres-a7-work/layer_results/*.json` — raw layer results (committed).
- `failres-a7-work/derived/bars1h_ANC_EURUSD_A7.parquet` — the rebuilt
  plane (gitignored, large; regenerable from the pinned corpus via the
  committed script).
