# ERRATUM — session-2 incidents (A1-recorded, 2026-09-29; M + D lanes)

Append-only disclosure. Shared evidence files (research/wayfinder, the
SLEEVE-FX5 pitcost table) are read-only for this pre-GO session; in-place
corrections belong to writable lanes post-registration. Lane artifacts are
being revised by their authors (resumed agents); this file is the
cross-lane erratum of record.

## I-1 — FAMILY_FAILURES asset-label defect (DT100 FX rows labeled "crypto") [Lane M]
## I-2 — the dead "VWAP" anchor was close-only / volume-blind [Lane M]

(As recorded below — see sections I-1/I-2 at the end of this file.)

## I-3 — M1 volume column semantics: SIZE-WEIGHTED, not tick-count [Lane D]

`poolB/data_audit/DATA_AUDIT_REPORT.md` §C: only 2.49% (EURUSD) / 3.50%
(GBPUSD) / 3.71% (USDJPY) of active minutes have integral volume — a
per-minute tick count must be integral — so the .bi5 volume field is a
size-weighted float32 sum of per-tick volumes in Dukascopy volume units
(absolute unit unverifiable from candles). Consequences:

1. The VOLPROF-M1 class spec's "tick-volume proxy" disclosure was written
   on a refuted premise; Lane M is revising section 3 to the honest
   semantics. Materially this is CLOSER to a true volume profile (trade
   size present, not just activity count) — the level-acceptance claim
   strengthens, the unit-opacity caveat remains.
2. POC/VA/LVN constructions are ratio-based → unit-invariant (being
   re-verified in the spec revision).
3. Any future design citing "tick volume" on these panels inherits this
   erratum.

## I-4 — COST_AUTHORITY_TABLE C2 Mon–Thu roll cell measured on the wrong hour [Lane D]

The SLEEVE-FX5 `pitcost/COST_AUTHORITY_TABLE.md` C2 Mon–Thu numbers match
the **22:00–23:00 UTC** hour, not the declared **(21:00,22:00]** window.
True (21:00,22:00] Mon–Thu per-minute-close p50/p90 (tradable minutes,
1,140 Mon–Thu days, full window): **EURUSD 1.2/3.7 · GBPUSD 2.8/7.8 ·
USDJPY 2.1/7.4 pips** — ~1.5–2× wider at p50 than tabled. C1 (Friday
20:00) and C2-Friday reproduce EXACTLY (n=286/286 per pair); C3 untouched
by this finding. Materiality: `S_roll = max(cell p90, general p90)`
previously UNDERCHARGED Mon–Thu rollover-window fills 1.3–2×; Lane P is
annotating FILL_ACCOUNTING_SPEC so the corrected cells govern. The
SLEEVE-FX5 table itself is owner-visible uncommitted work — flagged here,
not edited by this session.

## I-5 — clerical (prior manifests) [Lane D]

`largest_tradable_minute_run` field in audit_summary v1 was
non-reproducible (actual runs 5787/4377/5764 min at per-pair dates,
independently verified); one 1-char hash typo for USDJPY's m1_manifest.json
in a prior manifest. No numbers governing this program were affected.

---

## I-1 (full text, Lane M) — FAMILY_FAILURES asset-label defect

`research/wayfinder/FAMILY_FAILURES.jsonl` records DAYTRADER-100-V1 rows
under `asset: "crypto"` (e.g. DT100-13-VWAPMR). Lane M verified read-only
in the daytrader-100-v1 worktree engine config (`dt100/arms.py`,
`dt100/signals.py`) that DT100-13-VWAPMR ran on **EURUSD 1m** (band
2.0/1.5/2.5, hold 120/120/180 minutes, 07:00–20:00 UTC window); DT100-07
and other FX rows likewise ran on FX pairs (USDJPY among them).
Consequences:

1. The dead VWAP-MR neighbor is **same-pair, same-bar-size** as the
   VOLPROF-M1 class candidates on EURUSD — closer than the census/F-0
   salvage note implied. The class spec's representation-rho protocol
   (CLASS_SPEC_VOLPROF_M1 §8) uses the verified engine parameters for the
   reconstruction, making the rho measurement materially sharper.
2. Any ancestry statistic that grouped deaths by the `asset` field
   (including PC12A census ancestry_hits processing and the SLEEVE-FX5
   root-cause finding that "all 8 census ancestry_hits were
   crypto/stocks") under-counted FX-relevant deaths. The sleeve's standing
   fix (class-based ancestry index over full records) already mitigates
   the practice; the label defect itself needs a ledger erratum by a
   writable lane post-registration. **Owner-visible note:** this
   strengthens, not weakens, the disclosure burden on any FX leg adjacent
   to DT100 classes — carried as labels under the amended law.

## I-2 — the dead "VWAP" anchor was close-only / volume-blind

The SLEEVE-FX5 skeptic's M-3 phrasing ("volume-weighted" VWAP-MR neighbor)
is corrected by Lane M's code reading: DT100's VWAP anchor is a running
mean of M1 CLOSE prices, no volume weighting anywhere in the dead engine.
Skeleton-closer to VOLPROF-M1 (same pair/bar), information-farther (no
volume-by-price structure at all). Net effect on the amended protocol:
the "no dead family ever used volume-by-price structure" finding STANDS
(with corrected reasoning); the rho protocol remains the right
measurement; nothing in the SLEEVE-FX5 close is overturned (its slate
verdict did not rest on the M-3 phrasing).

## Disposition

- This file is the erratum of record for the pre-GO package.
- Post-registration action item (for the cycle's first writable lane):
  append correcting entries to FAMILY_FAILURES.jsonl for the DT100 FX
  rows' `asset` field per repo erratum practice; do NOT rewrite history
  in place.
- No artifact of the closed SLEEVE-FX5 or PR12A cycles was modified.
