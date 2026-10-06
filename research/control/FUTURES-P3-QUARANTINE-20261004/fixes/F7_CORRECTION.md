# F-7 Correction: P2B Gap-4 headline "43/45" → definitive count 52/55 in-universe

Task: FUTURES-P3-QUARANTINE-20261004 | Cycle: UNREGISTERED_PREP | Lane: Q2-FIX-VERIFY
Generated: 2026-10-04T01:06:04Z UTC
Correction class: append-only r2 (supersedes BY REFERENCE; zero committed files edited)
Corrects: SYNTH-VERIFY finding F-7 (MEDIUM) in
`research/control/FUTURES-OVERNIGHT-PREP-20261003/verify2/findings.json`
against lane P2B-CALGAP-FXCOMM's Gap-4 headline.

## 1) The definitive count (recounted by this lane, cell-by-cell, from the committed artifact)

Source of record (untouched):
`research/control/FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/fx_comm/fxcomm_gapfill_coverage.json`
→ `gap4_energy_metals_holiday_times_2011_2015.cells` (dict: 5 years × 12 holidays = 60 raw cells).

| Measure | Value |
|---|---|
| Raw grid | **60 cells** = 5 years (2011–2015) × 12 holiday slots |
| OBTAINED (status == "OBTAINED") | **52** |
| NOT_TRANSCRIBED | 1 — 2014-MLK (PDF fetched, sha256 pinned, capture 20140326160215; pypdf extraction garbled; artifact retained) |
| NOT_OBTAINED | 7 — 5 × Juneteenth (2011–2015) + 2014-Veterans + 2015-Veterans |
| Anachronistic slots (Juneteenth; not in the 2011–2015 universe — US federal holiday only from 2021; no CME per-holiday schedule file exists for those years, per the lane's own CDX inventory of `files/`) | 5 |
| **In-universe grid** | **55** = 60 − 5 Juneteenth placeholders |
| **In-universe OBTAINED** | **52/55** |

Per-year (verbatim from the artifact's computed `cell_status_counts` and confirmed by this
lane's independent recount of the cells):

| Year | OBTAINED / in-universe | Non-obtained in-universe cells |
|---|---|---|
| 2011 | 11/11 | — |
| 2012 | 11/11 | — |
| 2013 | 11/11 | — (Columbus & Veterans = official normal-schedule one-pagers, counted OBTAINED) |
| 2014 | 9/11 | MLK NOT_TRANSCRIBED; Veterans NOT_OBTAINED (archived file = settlement-procedures doc) |
| 2015 | 10/11 | Veterans NOT_OBTAINED (settlement-procedures doc) |

Sum: 11+11+11+9+10 = **52 OBTAINED of 55 in-universe** (52/60 on the raw 12-slot grid).
This matches SYNTH-VERIFY's recompute exactly (findings.json F-7: "52 obtained, 55
in-universe, 60 raw grid"). The lane's evidence narrative (FXCOMM_GAPFILL_EVIDENCE.md §4
per-year table) also lists 11/11, 11/11, 11/11, 9/11, 10/11 — i.e. the artifact, the
per-year table and this recount all agree; only the headline fraction does not.

## 2) Why the headline said "43/45" (mechanism, established)

- The "43/45" fraction exists ONLY as a **hardcoded string literal** — first inside
  `build_coverage.py` (the `'headline': '43/45 cells OBTAINED (2011 11/11, …)'` dict
  value), then copied into the coverage JSON `headline` field, the evidence MD Gap-4 row,
  the P2B handoff (authority_claims entry #4 + summary), and the comm hypotheses
  artifacts. It is **never computed** by any script.
- Proof by rerun (this lane, 2026-10-04, read-only sandbox with the committed
  `captures/` symlinked in): `build_coverage.py` regenerates
  `fxcomm_gapfill_coverage.json` **byte-identical** to the committed artifact
  (sha256 `91c0f0d939b2e63042465458823f50da15106bc798d426ab1b1bc98eff2d89e9` both sides;
  exit 0), and its own stdout prints the computed counts:
  `2011: 11, 2012: 11, 2013: 11, 2014: 9, 2015: 10` → sum 52. No "43" and no "45"
  appear in any computed output.
- Therefore the fraction was hand-composed at write time and contradicts the machine
  counts emitted by the very same script in the very same file. **No artifact documents
  any derivation of 43 or 45** — the exact arithmetic path is not reproducible
  (INFERENCE: hand-arithmetic slip at headline composition, consistent with
  SYNTH-VERIFY's classification; the numerator/denominator deltas are inconsistent
  with any single coherent universe redefinition — 52−43 = 9 obtained vs 55−45 = 10
  universe — which rules out a mere universe change and indicates a plain slip).
- Direction: **understatement of measured coverage**. In coverage accounting (cells,
  the unit every matrix in this round uses) the headline claims **9 fewer obtained
  cells** (43 vs 52) on a denominator **10 smaller** (45 vs 55) than the artifact
  actually holds. (As a bare fraction 43/45 = 95.6% > 52/55 = 94.5%, but no consumer
  in this round uses the fraction — they use cells; findings.json F-7 accordingly calls
  it "understates measured coverage by 9-10 cells (conservative direction)".) No gate,
  ranking or decision was or could have been worsened; the comm lane remains
  NOT_QUALIFIED_V2 on zero-O1M data regardless (SYNTH-VERIFY impact statement concurs).

## 3) Supersession (binding statement)

The committed files stay untouched per the append-only law. The figures below are the
authority going forward:

- **Energy/metals 2011–2015 per-holiday cells: 52 OBTAINED / 55 in-universe**
  (52/60 raw 12-slot grid; 5 Juneteenth slots anachronistic).
- In-universe non-obtained: exactly 3 cells — 2014-MLK (NOT_TRANSCRIBED, re-parse
  candidate), 2014-Veterans (NOT_OBTAINED), 2015-Veterans (NOT_OBTAINED).

Propagation sites of the stale "43/45" (all committed, all left verbatim, all superseded
by this file): `cme_cal_gap/fx_comm/FXCOMM_GAPFILL_EVIDENCE.md` (Gap-4 headline row),
`cme_cal_gap/fx_comm/build_coverage.py` (headline literal), `cme_cal_gap/fx_comm/
fxcomm_gapfill_coverage.json` (headline field only — the cells/counts in the same file
are correct), `dispatch/handoff_P2B-CALGAP-FXCOMM.json` (authority_claims entry +
summary), `hypo/comm/comm_hypotheses.json`, `hypo/comm/COMM_HYPOTHESES.md`.
The SYNTH-VERIFY round already propagated the corrected count into
`synth/BLOCKER_MATRIX.md` and `synth/blocker_matrix.json` (both read "52/55 in-universe").

## 4) Reproduction (all read-only; commands + exit codes also in this lane's handoff tests[])

```
# definitive recount (committed JSON only)
$VENV_PY - <<'EOF'   # iterate gap4 cells; count statuses; exclude Juneteenth
... (script as run; see handoff_Q2-FIX-VERIFY.json tests[2])   -> exit 0
# raw 60: OBTAINED 52, NOT_OBTAINED 7, NOT_TRANSCRIBED 1; in-universe 52/55

# determinism proof of the artifact generator (temp sandbox; captures/ symlinked)
cd $(mktemp -d) && ln -s <...>/fx_comm/captures captures && cp <...>/build_coverage.py .
$VENV_PY build_coverage.py                                        -> exit 0
# regenerated fxcomm_gapfill_coverage.json sha256 == committed 91c0f0d9...f2d89e9
# stdout computed counts: 2011 11, 2012 11, 2013 11, 2014 9, 2015 10  (sum 52)
```

$VENV_PY = /Users/hoangminhlong/my-quantitative/.venv/bin/python
All paths relative to
`research/control/FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/fx_comm/`.
