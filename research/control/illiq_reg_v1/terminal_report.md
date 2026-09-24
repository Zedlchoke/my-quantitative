# TERMINAL REPORT — ILLIQ-REG-V1 (falsification-first gate cycle)

## Verdict

**FALSIFIED** — the preregistered O1+V2 regime gate fails the phase-1 bar on
the S0R falsification surface. Per plan §6: no gate variants are permitted in
this cycle; the family `A8-V11-ILLIQ-AMIHUD` (anchor `ILLIQ-AMIHUD-28D-W`)
returns to NOT_PROSPECTIVE diagnostics only. This is the negative terminal
the dossier's own honest single-shot reading predicted.

## Identity

- terminal SHA: `0995044cbe4a736050b46b6693eac7491164278a`
  (`orca/illiq-reg-v1-integration`; base at registration `482dc81b`;
  freeze/cells `31985732`; reproduction `0995044c`)
- plan: `plans/PLAN_illiq_reg_gate_v1.md` · engine frozen `c97283e0`
  (CHR3F `recovered/v11_root`, byte-untouched)
- budget: **4/4** observed diagnostic cells
  (`scored=False`, `REPLICATION_NOT_PROSPECTIVE`), registry cap 4; program
  denominators carried in the ledger row (P-9)
- GO chain: A7 prelaunch AUTHORIZED 0 blocking (audit 2026-09-24T05:09:04Z,
  head `eb86951e`) → owner phrase at gate → `AUTH/GO_RECORDED.json`

## Result table (S0R 2024-08-22..2025-08-21, gated run in-engine, funding-wired `scan_2026_a`, 100k baseline per-unit)

| cell | arm | stress | net_sum | MDD | PF | positions | gate |
|---|---|---|---|---|---|---|---|
| P1-C1 **falsification** | ANCHOR | baseline (fee ×1.0) | **−0.345789** | **0.419178** | 0.8382 | 272 | 43 ON / 9 OFF |
| P1-C2 | ANCHOR | fee ×1.5 | −0.349759 | 0.421401 | 0.8370 | 272 | same |
| P1-C3 | ANCHOR | fee ×2.0 | −0.353730 | 0.423625 | 0.8359 | 272 | same |
| P1-C4 (control) | INV | baseline | **+0.329724** | 0.165130 | 1.1863 | 272 | same |

Bars (frozen, no re-basing — funding-wired Δ vs no-funding baseline was 2.62
pts ≤ 5): net ≥ −0.2947 → **FAIL** (margin −0.0511); MDD ≤ 0.4372 → PASS
(margin +0.0180). Both required → **FALSIFIED**.

Readings (within the disclosed outcome-exposed ancestry, confirmation weight
0): the gate removed 9/52 weeks and improved the anchor from −0.5631
(funded, ungated) to −0.3458 (−38.6%) — directionally real but short of the
preregistered ≥50% bar. Stress shows the loss is price-driven (costs
immaterial). INV-gated flips sign coherently (+0.3297, MDD 0.165) — the gate
does the same thing to the causal negative control; no rescue interpretation.

## Reproduction & audits

- Reproduction: detached twin at `31985732` — 8/8 cell artifact+shard files
  byte-identical; status/verdict identical modulo worktree path + wall-clock
  (`reproduction_verdict.json`). Self-consistency only (§22.1), not truth.
- A7 prelaunch: AUTHORIZED, 0 blocking (prior session's lane).
- A7 terminal: **CONFIRM, 0 blocking** — independent recompute of all cell
  metrics from artifact bytes, gate-law conformance (9 OFF stamps flat in all
  4 cells), digest chain, labels (9/9 rows), budget, boundaries
  (`a7_terminal/a7_terminal_illiq_reg_v1.json`).

## Incidents (all recorded in `incidents/`, no outcome exposure)

1. Early-GO misclassification (retracted & corrected — the GO was at its
   gate; root cause: stale measurement by the bootstrap session).
2. Two launcher failures before any cell ran (v11/root `research` package
   collision; gate-map key type) + a stale lock row archived via
   `cleanup_stale()` (`pid_dead`). Fixed by the chr3f subprocess-isolation
   pattern.

## Boundaries & state

S1 SEALED_UNTOUCHED everywhere; CHR3F tree read-only (clean); no orders, no
shadow/gateway/live surfaces; workers 0; heavy lock released FINISHED.
Phase 2 and any FWD stage: never opened (phase 2 needed an owner amendment
that is now moot; FWD was confirmation-only and no gate variant may be
registered in this cycle). Successor door (not this cycle): any NEW gate
hypothesis for this family is a new preregistration subject to the standing
OUTCOME_EXPOSED_ANCESTRY law — zero confirmation weight on all history,
forward/shadow only.
