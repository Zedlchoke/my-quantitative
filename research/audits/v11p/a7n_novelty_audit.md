# A7-N Novelty & Anti-Rescue Audit — Sprint V11 (RETRY 3)

Producer: D2-A7-N | Branch: orca/v11d-a7-novelty | HEAD: 903ed49529de5ee56ece7dc9fe896da32804a4f8
Full machine-readable verdicts: `a7n_novelty_audit.json` (same directory). Scratch: `a7n_scratch/`.

## Headline

- Seed **DEF (V11-SEED-DEFENSIVE-RESIDUAL-RISK): BLOCKED_PRE_SCORE** — frozen-set pairwise rho vs LOT 0.5654 and vs ILLIQ 0.4815, both ≥ 0.35 (PLAN §9). Novelty itself is genuine; the failure is orthogonality.
- Seed **LOT (V11-SEED-LOTTERY-MAX-SKEW): ELIGIBLE** — pairwise vs ILLIQ 0.3098 < 0.35; Gate A pass with a flagged weekly-reversal margin (−0.4642 vs 0.50).
- **ILLIQ group: ELIGIBLE** (a8_prop1 or a5_prop1; a6_prop1 breadth FAIL). Genuine mechanism, no hidden rescue.
- **OI group: PENDING** staging re-audit (amendment V11-AMEND-OI-STAGING-20260902). Novelty conditional-PASS.
- Objections: **1 HIGH, 0 CRITICAL**, 6 MEDIUM, 5 LOW.

## Task 1 — Literature packet identity: PASS_WITH_OBJECTIONS

- S2 Grobys (2021) JIFMIM — confirmed to auditor knowledge. S3 Financial Innovation (2021) — partially confirmed. S4 Binance docs — official, fine.
- S1 Pyo & Jang (2026) FRL — beyond auditor knowledge horizon; `identity_verified:true` asserted without independent trail (OBJ-08).
- Numeric claims in S2/S3 (~1.5%/week; "3.03% vs 1.99%") unverifiable / ambiguously phrased — directional use only (OBJ-09).
- Spot→perp caveats present for all academic sources; BTC-residualisation is an extension beyond the cited spot papers (OBJ-10).

## Task 2 — Novelty map vs V1–V10 inventory: NO hidden rescue

Inventory: trend/momentum; reversal/residual MR; funding carry/crowding rescue; volume-shock continuation; weekly reversal (V8); M01 aggressor-flow absorption; plus volatility-compression-breakout and funding-price-divergence (V7) per A8 ancestry lists.

| Family | Classification |
|---|---|
| Seed DEF | genuinely new (risk-moment sort; no ancestor) |
| Seed LOT | genuinely new — reversal-adjacency margin flagged (OBJ-03) |
| a5_prop1 / a8_prop1 / a6_prop1 | genuinely new (Amihud level sort; reversal/size confounds pre-diagnosed) |
| a5_prop2 / a6_prop2 / a8_prop2 | genuinely new, CONDITIONAL on OI re-audit (funding excluded by contract; a6p2 sign-free return-orthogonalisation strongest) |

No proposal re-tunes a rejected observable; no monotone transform of a banned signal detected.

## Task 3 — Negative controls: PASS_WITH_OBJECTIONS

All 8 families use sign-inverted anchors (sign-destroying → satisfies PLAN 8.1 letter). Weakness: sign-flip is not mechanism-destroying, and on shared decision instants the inverted spread is the anchor's negative by construction; falsification content comes only from independent cell scoring (OBJ-06). The genuinely mechanism-destroying falsifiers (a5p1 Lou-Shu reversal absorption, a8p1 size-orthogonalisation, a6p2 return-orthogonalisation, a8p2 momentum-contamination) are diagnostics, not scored cells. All adapter-implementable via `control_mode` sign flip (single digest per L-V10-M01-KEY).

## Task 4 — A1 rho evidence: VALID AND BINDING (audited, not recomputed)

`a1_prewindow_rho_evidence.json` (producer A1): prewindow 2024-11-01..2025-08-21 (= A9-F, strictly before scored start 2025-08-22), Monday stamps, min 8 names, 20 symbols, frozen method note matches all four feature contracts.

- Gate A (vs rejected-ancestor proxies, |rho|<0.50): all PASS; **LOT|REV7 = −0.4642 close** → OBJ-03.
- Gate B (frozen-set pairwise, |rho|<0.35): DEF|LOT 0.5654 **FAIL**, DEF|ILLIQ 0.4815 **FAIL**, LOT|ILLIQ 0.3098 PASS. Robust to pooled-vs-mean choice.
- **Defect (OBJ-05):** A1 stamps `within_required: 0.5` on all pairs; PLAN §9 says 0.35 for frozen-set pairs — under A1's label DEF|ILLIQ would wrongly pass. Corrected here; no final outcome change.
- **Spot-check (2 stamps, ≤60s):** 2025-05-05 and 2025-07-07 recomputed from staged bars → 5/6 values inside A1's reported envelope with correct signs; LOT|ILLIQ 0.6474 exceeds A1 absmax 0.6451 by 0.0023 (one-rank sensitivity at n≈20). Independent DEF-eligible stamp count 38 vs A1's 26 (definitional delta, LOW; cannot flip verdicts).
- Caveats: ancestors are proxies (funding-carry never proxied → OBJ-04); rho_absmax up to 0.92 shows stamp-level extremes.

**Implied dispositions:** DEF → BLOCKED_PRE_SCORE (3 scored slots unused, no third discovered replacement); LOT eligible; ILLIQ eligible; OI pending re-audit.

## Task 5 — Convergence

- ILLIQ: a5_prop1 ≈ a6_prop1 ≈ a8_prop1 (one mechanism, three variants) → exactly one selectable. a6_prop1 excluded on breadth; a8_prop1 canonical candidate (A9-F PASS + deepest falsification set); a5_prop1 PASS alternative.
- OI: a5_prop2 ≈ a6_prop2 ≈ a8_prop2 → exactly one selectable, pending re-audit.
- Seeds: DEF ⊄ frozen set (orthogonality); LOT vs ILLIQ orthogonal. Four distinct mechanism classes pool-wide.

## Task 6 — Objections (1 HIGH / 0 CRITICAL / 6 MEDIUM / 5 LOW)

OBJ-01 HIGH DEF orthogonality · OBJ-02 MED quintile breadth (≈9 eligible symbols → 1–2 names/leg; Stage-A concentration gates likely to bind; escalate to HIGH if universe <8) · OBJ-03 MED LOT|REV7 margin + required reversal-exposure diagnostic · OBJ-04 MED no funding-carry proxy in Gate A · OBJ-05 MED A1 threshold-label defect · OBJ-06 MED sign-flip-only controls · OBJ-07 MED OI group conditional on staging re-audit · OBJ-08..12 LOW (S1 horizon, S2/S3 numerics, residualisation extension, retry-2 contamination quarantine, a6p1 breadth exclusion).

## D3 binding summary

Max reachable freeze as-is = LOT + ILLIQ + (OI if re-audit passes) → 9 of 12 cells; DEF slots unused. If OI fails re-audit → only one discovered family → `V11_BLOCKED_SELECTION_INSUFFICIENT` (do not lower thresholds). Full list in `a7n_novelty_audit.json → launch_readiness`.
