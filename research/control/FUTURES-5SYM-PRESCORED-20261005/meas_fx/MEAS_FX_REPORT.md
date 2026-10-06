# MEAS_FX_REPORT — lane MEAS-FX, round FUTURES-5SYM-PRESCORED-20261005, wave-3

- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep`,
  branch `prep/futures-5sym-prescored-20261005`, HEAD at start
  `b2d086ca50996c628ec0373c4a3e8c2f2387c742` (wave-3 base, verified by
  `git rev-parse HEAD`). Wave-3 dispatch
  `dispatch/DISPATCH_MANIFEST_WAVE3.json` (base_sha 0732f22e… = wave-2
  handoff state; the lane verified its own checkout HEAD as instructed).
- Write surface: `meas_fx/**` + `dispatch/handoff_MEAS-FX.json` only. No
  commits, no other worktrees, **no network**, no S1/GO/registration.
- Locks: `researchctl.py locks inspect` at start **FREE_PROVEN**; all four
  jobs are light single-shot reads/arithmetic (<2 s each), no lock taken;
  end-of-lane inspect recorded in the handoff.
- Outcome-blind law: descriptive statistics only. m2's conditional part ran
  on synthetic fixtures with a documented fixture law; the real-data
  execution is recorded NOT_RUN (owner-gated). Missing data = NOT_RUN with
  grounds, never inferred PASS.

## Per-item table

| item | what ran | verdict | artifact | headline number | limitation |
|---|---|---|---|---|---|
| #8 G3 FX-F5 CIP-vintage sensitivity | recomputed correlation/regime statistics from the committed per-roll vintage-as-of rows (`a7_6e_recompute.json:rolls_cip`, 27 rolls, both bases) | **PASS (descriptive, partial)** + 3 NOT_RUN cells | `m1_fx_f5_cip_vintage.md` + `.json` | r = **+0.9097 latest vs −0.1068 year-end-ALFRED as-of**; regime-label flip 1/27 (2022-12-01); **0.20 rho bar passes only on latest-vintage** | vintage CSVs not in tree (fresh recomputation NOT_RUN_DATA_NOT_IN_TREE); 6B vintage-as-of NOT_RUN_DATA_NOT_IN_TREE; direct rho vs V8/V9 shadows NOT_RUN (series not in tree); owner SOFR signature stands regardless |
| #9 G4 FX-F6 transfer measurement | harness (`T` = stratum sign-agreement difference, block bootstrap) + 4 synthetic fixtures with documented fixture law; committed descriptive inputs cited | **PASS (harness+fixtures)**; real-data run **NOT_RUN-REAL-DATA** (owner-gated, conditional-on-signal) | `m2_fx_f6_transfer.md` + `.json` | fixtures 4/4 PASS (F1 null in-CI; F2 +0.10 injection recovered 0.064 [0.016, 0.101]; F3 no-lookahead; F4 obs+3 release lag); committed: fwd-21d vol 6.52% vs 7.68% (n=347), 6B falsifier −0.074 (n=326) | the intraday transfer itself remains unmeasured; mandatory release-clock control + √2 MDE inflation wired as run preconditions |
| #10 G9 AF2 K2 vintage-flip | baseline re-verified on committed latest-vintage rows; as-of machinery implemented + synthetic-proven | **PASS (machinery + baseline)**; real vintage run **NOT_RUN_DATA_NOT_IN_TREE** | `m3_af2_vintage_flip.md` + `.json` | baseline **16/16 material / 20/27 reproduced**; fixture flips 2/6 recovered exactly (kill rule evaluated, never adjudicated on synthetic data); K2 flip count on real vintages = **NOT_RUN** | no committed DFF vintage set exists ANYWHERE (external disk has SOFR year-end vintages only); 0/16 material rolls have a committed vintage-as-of differential; owner data-plane action required to close K2 |
| #12 G8 FX-F4 RT/MDE re-derivation | pure arithmetic from committed M2c-corrected census numbers + committed cost law | **PASS (descriptive arithmetic)** | `m4_fx_f4_rt_mde.md` + `.json` | corrected weekday gap-std 3.038/3.999 bp (n=1,282/1,283); ratio gap/day 0.160/0.146 vs cited 0.805; **r = RT/MDE: Reading A 0.99–1.74 (6E) / 1.46–2.60 (6B) @ census n; Reading B (corrected scale) 15.2–26.5 / 20.2–35.8; p95 gap 3.10/4.40 bp < RT floors 3.6/6.3 bp** | per-trade F4 dispersion NOT_RUN (conditional) — both readings are committed proxy constructions; costs MODELED/UNDER REVIEW (A7); BBO NOT_RUN; 6B 0/42 holiday grid stands |

## Verdict summary

- **FX-F5 (G3)**: vintage sensitivity now QUANTIFIED from committed data —
  the 0.20 rho bar's passage flips with the vintage basis (+0.91 clears /
  −0.11 fails). F5 stays NEEDS_EVIDENCE behind PB2; owner real-time SOFR
  decision remains mandatory (court §d row 7) — unchanged, now with a
  measured quantification instead of a single precedent number.
- **FX-F6 (G4)**: measurement harness delivered + proven; the transfer
  itself remains NOT_RUN-REAL-DATA (conditional-on-signal, owner-gated).
  F6 stays NEEDS_EVIDENCE behind PB2.
- **AF2 (G9)**: K2 machinery delivered + fixture-proven; the real K2 test
  is NOT_RUN_DATA_NOT_IN_TREE (no DFF vintage set exists anywhere). AF2
  stays PARK (PB3) + NEEDS_EVIDENCE (vintage item).
- **FX-F4 (G8)**: M2c-corrected power/cost arithmetic delivered — **F4
  dies at program-feasible n under the corrected scale on every committed
  reading** (r ≥ 1 with one 0.99 edge cell; r ≫ 1 at the corrected scale).
  This is the binding G8 consumption; it adjudicates no §4 refutation
  condition and schedules nothing. F4 stays HOLD (PB2) with the corrected
  arithmetic now on record for any future freeze.

## NOT_RUN register (complete, with grounds)

1. Fresh year-end-ALFRED as-of recomputation from vintage CSVs (m1, m3) —
   NOT_RUN_DATA_NOT_IN_TREE: no committed vintage capture in the tree;
   external path `/Users/hoangminhlong/.my-quantitative-data/
   futures-nonprice-10syms/fred_alfred/` (uncommitted; and holds SOFR
   year-end vintages only — no DFF set).
2. 6B vintage-as-of recomputation (m1) — NOT_RUN_DATA_NOT_IN_TREE (no
   committed 6B recomputation; US-side vintage files absent).
3. Direct 0.20-rho of F5 differential vs V8/V9 shadow series (m1) —
   NOT_RUN_DATA_NOT_IN_TREE (shadow series not committed); re-measured at
   any D2-equivalent stage by law.
4. FX-F6 real-data transfer execution (m2) — NOT_RUN-REAL-DATA
   (conditional-on-signal; owner-gated per the dispatch measurement law).
5. AF2 K2 real-vintage flip count (m3) — NOT_RUN_DATA_NOT_IN_TREE
   (grounds 1).
6. F4 per-trade dispersion (m4) — inherited NOT_RUN (conditional; K6GATE
   §6.2 stands).

## Zero-PnL statement

Every number in this lane is an unconditional descriptive statistic of
committed artifacts or a synthetic-fixture proof: correlations, label
signs, flip counts, dispersion, cost-floor arithmetic. No PnL, no
expectancy, no return conditional on any signal was computed on real data;
no position, order, parameter, family, trial, registration or schedule was
created or changed; no network was touched; no ledger/registry was
written; PB2 HOLD and PB3 PARK stand; all costs cited are MODELED per
FEES_CORRECTED (tier-1 2.46 USD/side) and UNDER REVIEW. Missing evidence
is NOT_RUN, never inferred PASS.

— End MEAS_FX_REPORT.
