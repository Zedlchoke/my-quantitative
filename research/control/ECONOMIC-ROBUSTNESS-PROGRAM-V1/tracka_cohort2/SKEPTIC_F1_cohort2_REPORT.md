# SKEPTIC F-1 REPORT — ERP1-TRACKA-COHORT-2 — SKEPTIC_F1_cohort2_REPORT.md

- Cycle: `ERP1-TRACKA-COHORT-2`; Lane: `skeptic-f1` (economic skeptic — F-1
  ancestry-rho measurement, per my own frozen protocol,
  `SKEPTIC_F0_cohort2_REPORT.md` §4)
- Worktree: `.worktrees/erp1-tracka-cohort-2/integration` (branch
  `orca/erp1-tracka-cohort-2-integration`); started at `752b9028` (artifacts
  commit `0e2e2ab8`); **my commit: `c474ef44d40a14d5dbb55d321399c1604eca838e`**
  (runner + results, explicit pathspec, exactly 2 files).
- Runner: `research/control/ERP1-TRACKA-COHORT-2/scripts/f1_rho_run.py`,
  sha256 `76f2a01c2237fe9a4370c4b2806dcd1abf86d314b8fc3a663f5a406359f50b7b`
  (pinned pre-execution; bytes untouched after the measurement — a cosmetic
  stdout label defect in the final print loop is recorded below, NOT fixed,
  to preserve the sha binding).
- Machine artifact:
  `research/control/ERP1-TRACKA-COHORT-2/falsifier/F1_rho_results.json`
  (schema `tracka2.f1_rho@1`, committed in `c474ef44`).
- No PnL anywhere; the sealed window was never read (all consumed arrays are
  dev-masked by construction; dev row pins re-asserted in-run).

## 1. Pre-consumption verification (dispatch step 1) — ALL PASS

- **112/112 committed `.npy` arrays sha256-verified against
  `t2_planes_manifest.json`** (94 shadow arrays + 18 candidate arrays, both
  pairs) — zero mismatches, zero missing manifest entries.
- Consumed set: candidate ANCHOR targets only (`p3a_anchor`, `p3b_anchor`) —
  int8, len 27,608 AUDUSD / 27,583 USDCAD (dev pins re-asserted), values ⊆
  {−1,0,1}, nonzero counts match manifest (P3-A 1,171/1,229; P3-B
  6,001/4,540), warmup region flat (first nonzero bar 1,522/1,316 AUDUSD,
  1,324 USDCAD — consistent with warmup index 1,334/1,307).
- `tracka_lib.py` bytes sha-verified = pinned `1e09b368…` (A7-certified);
  `spearman_rho` imported only from those bytes.
- Shadows: **47/47 per pair, status OK, 0 `NOT_CONSTRUCTIBLE`** — R-ANCHOR,
  R-ORIG (pinned tracka_lib), `M3_SPREADGATEDFADE` (built from dev planes),
  11 census families × C1..C4 (v2_lib `efb87e37` + frozen v2_campaign
  `6147beff` configs).

## 2. Execution — one-shot, with two disclosed pre-measurement aborts

- **Abort 1 (fail-closed, P-23 class):** my runner first applied the
  warmup-flat invariant to SHADOW arrays; shadows legitimately carry native
  census-builder warmups (FX2-H1TSMOM fires from bar 24; R-ANCHOR from bars
  121–215; the frozen §4 requires warmup-flat for CANDIDATES only, and
  computes rho on the full grid with each book's own warmup zeros).
  Aborted BEFORE any rho existed; invariant scope corrected.
- **Abort 2 (crash at verdict assembly):** TypeError in the candidate-verdict
  assembly line AFTER in-memory rho rows for p3a were computed, BEFORE any
  print/persist/human-readable value existed. Partial in-memory result
  discarded unpersisted, never seen.
- **Attempt 3 = the single persisted measurement** (runner sha above). Both
  aborts are recorded inside `F1_rho_results.json` (`pre_measurement_aborts`)
  and in the commit message. No verdict shopping was possible: no number was
  seen before the persisting run.

## 3. RESULTS (gate: pooled |rho| = max over 47 named shadows ≤ 0.20 per pair, immovable)

| Candidate | Pair | Pooled worst \|rho\| | Worst shadow | Verdict |
|---|---|---|---|---|
| **P3-A `TRACKA2-P3A-QCRD-H1`** | AUDUSD (home) | **0.0786** | FX2-SESSMA-C2 (rho −0.0786) | WITHIN_GATE |
| **P3-A** | USDCAD (replicate) | **0.0883** | FX2-SESSMA-C4 (rho −0.0883) | WITHIN_GATE |
| **P3-A** | — | — | — | **`PASS_F1`** |
| **P3-B `TRACKA2-P3B-DINV-1D`** | AUDUSD (replicate) | **0.3103** | FX2-H1DONCH-C1 (rho +0.3103) | ANCESTRY_RHO_BLOCK |
| **P3-B** | USDCAD (home) | **0.3032** | FX2-H1TSMOM-C1 (rho +0.3032) | ANCESTRY_RHO_BLOCK |
| **P3-B** | — | — | — | **`ANCESTRY_RHO_BLOCK` — DEAD** (home pair blocked ⇒ candidate dead per the frozen consequence; no replicate-dropper reading available since BOTH pairs block) |

Runner stdout mislabeled both blocks "P3-B" (print-loop variable reuse,
cosmetic); the JSON is the authority and is correctly keyed — the numbers
above are read from `F1_rho_results.json` fields (P-19), re-quoted here:
p3a_anchor AUDUSD pooled 0.078552 / USDCAD 0.088284; p3b_anchor AUDUSD
0.310253 / USDCAD 0.303153.

### 3.1 P3-A detail (PASS_F1)

- Worst shadows: FX2-SESSMA-C2/C1/C3/C4 (|rho| 0.075–0.089) and
  FX2-ASIAFADE-C1/C3/C4 (0.064–0.075) — session-adjacent census families,
  all far under the 0.20 bar. **Margin-to-fail (P-2 discipline): pooled
  worst 0.0883 vs bar 0.20 ⇒ margin 0.1117 on the worse pair.**
- The H1TSMOM adjacency I flagged at F-0 measured CLEAN on the frozen
  representation (H1TSMOM-C1: 0.0493 AUDUSD / 0.0504 USDCAD — the heavy
  gate, |S_t| ≥ 0.25 AND P_t ≤ 0.40 with sign flips, decorrelates the book
  from always-on momentum). R-ANCHOR/R-ORIG (range family): 0.0382/0.0479
  class — no range-edge echo. M3_SPREADGATEDFADE: ~0.05 both pairs.
- **Disclosed diagnostic (report-only, never the gate):** zero-excluded rho
  vs SESSMA/ASIAFADE is NEGATIVE −0.26..−0.36 — on occupied bars the book
  anti-correlates with session fades (state-conditioned sign flips). The
  frozen gate representation (full grid incl. zero rows, P-12) is what
  binds and what passed; the diagnostic shows the pass is NOT an artifact
  of sign dilution on a same-sign book — it is a genuinely low-overlap
  book. A7 is invited to recompute both readings.

### 3.2 P3-B detail (DEAD — `NOT_SCORED_FALSIFIED`, ANCESTRY_RHO_BLOCK class)

- Blocked on BOTH pairs, by MULTIPLE independent families over the bar:
  AUDUSD — FX2-H1DONCH-C1 0.3103, FX2-H1TSMOM-C1 0.3024, FX2-STOCH-C4
  0.2947, FX2-PDHLOC-C3 0.2909; USDCAD — FX2-H1TSMOM-C1 0.3032,
  FX2-H1DONCH-C1 0.3001, FX2-STOCH-C4 0.2952, FX2-PDHLOC-C1 0.2474. This is
  not a single-shadow knife-edge; the book's exposure shape (multi-bar holds
  in the prior day's direction) is deep inside the census
  momentum/breakout/stochastic envelope.
- **Representation-robust:** zero-excluded diagnostics are 0.60–0.74 vs the
  same families — the block holds (far worse) on either reading of the
  grid. The F-0-flagged adjacency (momentum skeleton; DAYMOM/CTA-crowding
  erosion the proposer itself declared) is exactly what fired.
- Death label: `ANCESTRY_RHO_BLOCK` pre-score — zero scored cells spent,
  zero holdout looks consumed for P3-B (its sealed look was never opened;
  A1's sealed map need only register P3-A).

## 4. Consequences for the cohort

1. **Effective slate = ONE surviving mechanism**: P3-A `TRACKA2-P3A-QCRD-H1`
   (home AUDUSD), which now proceeds to the remaining falsifiers. F-2 PIT
   battery is already `PASS_PIT` 4/4 (prep lane); the binding open items on
   P3-A are unchanged from my F-0 intake conditions — chief among them the
   **F-5 ceiling on the MEASURED tight-state conditional bucket** (declared
   band upper 2.5 bps ≈ 1.62 pips vs measured session ×2.0 RT 3.6 pips;
   ceiling positive requires measured tight-state crossing ≤ 0.41 pips at
   k=2.0 — lane C rules on the measured bucket keyed to the actual fill-hour
   distribution from `F6_census_counts.json` §5.1: entries spread over hours
   1..18, last-6m roughly uniform).
2. **Slots:** P3-B's slate slot is vacated by measurement. Per the frozen
   slot policy it is NOT refilled (no same-family replacement; a different-
   family refill requires a new open-call — an owner/council decision beyond
   this dispatch). Cohort ends falsification with **1 slated survivor +
   2 empty slots** (`SLOT_LEFT_EMPTY_NO_QUALIFIED_CANDIDATE` ×2) unless the
   owner re-opens the call. Empty remains preferred over weak filler.
3. P4-A/P4-B remain F-0-PASS / not-slated (F-5-determined negative) —
   unchanged by this measurement.
4. One-shot: this was the single F-1 execution; re-runs require an owner
   amendment (same law as F-0).

## 5. Known limitations (disclosed)

- The runner's final stdout print mislabels the candidate name (cosmetic;
  JSON authoritative; runner bytes deliberately left untouched after the
  measurement to preserve the sha binding — A7 recomputes from the JSON +
  committed runner and will see the same defect).
- Per-fold rho diagnostics computed from the committed `bars1h_ANC` plane
  timestamps mapped through the frozen fold table; they are report-only and
  the gate never depends on them.
- The M3 shadow is the prep lane's faithful implementation of my §4 spec
  text (cohort-1 M3 code not byte-available); its rho contribution is small
  (~0.05) and immaterial to either verdict.

— Lane B (economic-skeptic), `skeptic-f1`, 2026-09-26. No PnL anywhere;
sealed window never read.
