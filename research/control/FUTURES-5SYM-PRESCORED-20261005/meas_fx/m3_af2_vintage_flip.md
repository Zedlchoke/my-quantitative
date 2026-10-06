# m3 — AF2 K2 vintage-flip test machinery (WORK_QUEUE A-#10 / HYPO G9)

- Lane **MEAS-FX**, round **FUTURES-5SYM-PRESCORED-20261005** wave-3.
- Outcome-blind: flip counts are data-quality facts (label stability), not
  strategy returns. No PnL, no network. Machine mirror:
  `m3_af2_vintage_flip.json`. Generator: `meas_fx_m1_m3_cip_vintage.py`.
- PB3 PARK untouched; the owner real-time rates decision stands regardless.

## The K2 kill rule (committed, quoted)

JPY_AUD_HYPOTHESES §5.7 K2 / CENSUS_5SYM AF2 field 3: "recompute the
differential with year-end ALFRED vintages as-of each roll; **if the sign
regime flips on ≥3 of 16 material rolls, the conditioning variable is
vintage-fragile ⇒ dead** (the 6E precedent is the stated bar)" — the 6E
+0.91→−0.11 flip (m1) is the named precedent.

## What ran on committed data

Baseline verification on the committed latest-vintage rows
(`FUTURES-DEEPRESEARCH-V2-20261003/analysis/6A_a3_term.json:
roll_gap_vs_rate_differential`, n=27, n_material=16, |RBA−DFF|≥0.25pp):

- material sign match recomputed from the rows: **16/16** — reproduces the
  committed 100% share;
- overall sign match recomputed: **20/27** (74.07%) — reproduces the
  committed 74.07%;
- on this single (latest-vintage) basis the flip count is 0 by
  construction — 16/16 is the floor the K2 test stress-tests.

## Machinery (delivered, synthetic-proven)

`asof_differential()` implements the identical as-of rule the committed 6E
A7 audit used (for roll date d: latest vintage with as-of stamp ≤ d, then
that vintage's own nearest observation ≤ d; differential = RBA_effective(d)
− DFF_vintage(d); RBA table revision-free as-published).
`k2_flip_count()` counts material rolls with sign(diff_vintage) !=
sign(diff_latest) and evaluates the ≥3/16 kill. Pure functions over
caller-supplied vintage tables (no I/O).

Fixture law (documented in the JSON): 6 rolls, RBA flat 1.50, latest DFF
1.00 (all material, diff +0.50); one vintage table with INJECTED
opposite-sign observations (DFF 2.00) on rolls #3 and #5; same-sign values
elsewhere. Expected flips = 2, dead = False.

| fixture | expected | got | pass |
|---|---|---|---|
| injected-2-flips | n_material 6, flips 2, dead False | 6 / 2 / False | PASS |
| null (vintage == latest) | flips 0 | 0 | PASS |

## Real vintage run: NOT_RUN

**NOT_RUN_DATA_NOT_IN_TREE.** Grounds:

1. `git ls-files` finds **no committed DFF/DFEDTARU vintage capture** in
   this tree — the only ALFRED-adjacent committed file is the collector
   `FUTURES-BEHAVIOR-10SYMS-PREP-20261002/nonprice_acquisition/collect/
   fred_alfred.py`; the BLS vintage captures (committed) are release-
   schedule captures, not rate vintages.
2. The external data dir cited by the dossiers
   (`/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/
   fred_alfred/`, subdirs `latest/`, `pit/`, `vintage_attempts/`) is
   outside the repo — uncommitted, therefore not consumed by this lane.
3. Even on that external disk, only SOFR year-end vintages were captured
   (`vintage_attempts/SOFR_*.csv`); **no DFF vintage set exists anywhere**
   — the 6A lane used DFF latest-vintage only (A7_DEEP_6A; NOTE-4), and no
   committed 6A per-roll vintage-as-of recomputation exists (unlike 6E,
   where `a7_6e_recompute.json:rolls_cip` committed one).

Coverage: **0 of the 16 material rolls** have a committed vintage-as-of
differential; the computable subset from committed artifacts is the
latest-vintage baseline above. Closing K2 requires an owner data-plane
action: capture DFF/DFEDTARU vintages (year-end at minimum), commit them,
re-run the committed machinery — the machinery is now in place and
fixture-proven.

This artifact adjudicates nothing: AF2 stays PARK (PB3) + NEEDS_EVIDENCE
(vintage item); no threshold is tuned; no registration path is opened.

— End m3.
