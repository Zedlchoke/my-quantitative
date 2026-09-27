# lane_x — G5 INDEPENDENT IMPLEMENTATION (EVENT-MECHANISMS-V1)

Independent re-implementation of the frozen arms from `G3_FREEZE.md` +
`G3_FREEZE_ADDENDUM_r1.md` + `G3_FREEZE_ADDENDUM_r2.md` ALONE (no reading of
the other implementation lane's engine/tests/report before commit 1).
Written for the G5 agreement protocol: implement, commit, THEN compare
decision books.

## Layout

- `engine_x/` — lane_x implementation (own code style)
  - `tzlaw.py` — R2-4: America/New_York via zoneinfo, strata S1..S4, weekend bucket
  - `panel.py` — NG6 raw OHLCV panel (R2-1/R2-5; `adjusted_close` never read)
  - `divsplits.py` — R2-2 ex-date index (case-insensitive stem resolution)
  - `sequencing.py` — R2-3 sequencing + B1/X1 bar laws + CA exclusion
  - `a1_books.py` — A1 anchor (S1∪S3∪S4, hold 5) + A1-N2 (S2, hold 5)
  - `xml4.py` / `a2_books.py` — A2 anchor (issuer-day >= $100k officer/director
    open-market buys, original filings, entry first open strictly after
    acceptance, hold 10, long-only)
  - `run_books.py` — deterministic runner (pins verified fail-closed; sorted
    output; gzip mtime=0)
- `tests/` — hand-computed fixtures incl. the lane_s S7 fixtures
  (after-close, pre-open, DST fall-back) + spring-forward, stratum
  boundaries, delisting exit, CA exclusion boundaries, B1 both directions,
  X1 entry/exit roll, A2 floor boundary, amendment drop, officer/director
  gate, issuer-day aggregation.
- `ambiguities.md` — pre-registered readings for every spec gap (P2)
- `output/` — books (records only; NO aggregate of trade returns, R2-6),
  exclusions census, run manifest with input/output digests
- `compare/` — (commit 2) key-set + field-level agreement vs the other lane

## Run

```bash
.venv/bin/python -m pytest \
  research/control/EVENT-MECHANISMS-V1/lane_x/tests -q
.venv/bin/python -m engine_x.run_books \
  --worktree <integration root> \
  --out research/control/EVENT-MECHANISMS-V1/lane_x/output
```

(deterministic: two runs are byte-identical; verified via sha256 in
`output/determinism.txt`.)
