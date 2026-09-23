# PHASE-STRATEGY-V1 — TERMINAL REPORT (§34.6)

terminal verdict: **PHASE_STRATEGY_V1_NO_INCREMENTAL_VALUE**

chain: plan c6d80a9f → lanes (L1 88a42ed5/c8ea871b/458d8aa3, L2 8a427571,
L3 4c17b7f4/48388fbf) → amendment A1 eaef65d6 → P4 freeze 4b7eae34 → A7 r1
REMEDIATION_REQUIRED 991b4e02 → remediation 458d8aa3/75765be2/a7d355db →
freeze bump 8865e7d3 → A7 r2 AUTHORIZED_FOR_DISCOVERY_STOP bbc5a778 → owner
GO consumed verbatim at own gate (registry events 09:38:00Z) → scored engine
b4246ac7 → producing code state a9c8a67c → scored evidence 17a1bea5 → A7
terminal audit **af52f3582270bcc19634add3d88858e0c28959bf (terminal anchor)**.
The closeout commit carrying this report adds receipts only (runtime/closeout/)
and touches no scored artifact.

observed/published: 20/20 arm×cell outcomes (4 candidates + 4 controls +
12 baseline-cells; 52 raw computations with cost tiers folded) — counting
rule disclosed in scored_ledger.json; budget **4/15**.

family verdicts (candidates_passing_G1_G7 = []):
- PSV1-BTC_H1-UPTREND-BREAKOUT_CONT: +89,637 @1.0x — G3/G4/G5 FAIL
- PSV1-BTC_H1-ACC-FLOOR_PROVISION: +45,744 — G3/G5 FAIL (conc 0.550)
- PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT: −44,486 — G1/G2/G3/G4/G5 FAIL, G6 KILLED
- PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION: +177,692 — G1/G2/G4/G7 PASS but
  G3 FAIL (loses 7.2x to TREND_LF +1,278,271), G5 FAIL (0.5128), **G6 KILLED
  (30-bar block-shuffle placebo +190,392 > candidate — phase-break timing
  carries no information)**

reproduction: G8 byte-identical 5/5, three independent runs (receipts:
`runtime/closeout/REPRO_RECEIPTS.md`). A7 terminal: af52f358
`audits/a7_terminal_audit.{json,md}` — 0 HIGH/CRITICAL, 1 LOW (T-L1 gate-string
serialization, latent/conservative) + 4 INFO.

S1 SEALED throughout; no orders/paper/testnet/live anywhere; SPY cell closed
zero-eligible (NO_ELIGIBLE_PROPOSAL — valid result). Incidents: registry row
stale 10:21Z→close after Lead-session handover mid-P7 (cured by half-2 close,
adopted-evidence receipt above); prior-session close artifacts (ledger row +
4 FAMILY_FAILURES rows) landed inside commit 4fc3320c mixed with the AMIHUD
close — recorded here for provenance, history not rewritten.

Successor: BTC-H4-CONTINUATION-V2 (owner instruction 2026-09-23) investigates
the BTC_H4 arm's F2/F4 losses under its own plan, gates and owner GO; it does
not reopen this cycle.
