# TERMINAL_DECISION — PORTFOLIO-ROUTER-12ASSETS-100K-V1 (A1, 2026-09-28)

**Typed close: `ROUTER_STATES_THIN` — 0 scored cells, 0 PnL, S1 SEALED_UNTOUCHED,
budget observed 0/64.** The macro-state router is unrunnable as registered:
its state engine died at the preregistered pre-PnL battery, twice, before any
outcome data existed.

## Evidence chain (all numbers from committed artifacts)

1. **PIT gates PASSED** (owner's parallel priority, completed first):
   `pit/PIT_DOSSIER.md` — G-PIT-V1 EFFR PASS_EVIDENCED (usable d+1 15:00 ET);
   G-PIT-V2 VIX PASS_EVIDENCED (CBOE channel usable d 16:15 ET; FRED mirror
   identical 9,278/9,278 dates; no-retro-revision via 3 Wayback vintages);
   G-PIT-V3 Brent−WTI PASS_EVIDENCED with frozen conservative rule
   (observations ≤ decision−10 calendar days; EIA weekly-release cadence
   measured, T−1/T−2 rejected as lookahead). Raw store: 50 sha256'd files,
   `~/.my-quantitative-data/pr12a100k/raw/MANIFEST.json`. **The owner's
   fail-closed condition (NOT_RUN_PIT_GATE_FAILED) did NOT fire — the data
   PIT-proved clean; the engine died on statistics, not on data.**
2. **State census kill (floors):** `battery/STATE_BATTERY_REPORT.json`
   (payload_sha256 `4a5f0fc5…`, A1-reproduced): merged episodes over the full
   286-Friday calendar 2021-01→2026-06 — WAR_ENERGY 10 (F1≥10 pass, margin 0),
   RISK_STRESS 7, TIGHTENING 2, EASING 3 (all F1-fail). Per-state F2/F3
   per-fold floors fail for every state. Frozen law (policy §3.5, protocol
   §4.1): failing states ⇒ NOT_RUN_THIN ⇒ permanent FLAT rows; ≥2 states fail
   ⇒ close `ROUTER_STATES_THIN`. No post-hoc relaxation (RSM mirage law).
3. **Representation-rho kill (P-29):** V2 (VIX 252d percentile) vs the dead
   RGC-G2/FXFV3-A6 vol-percentile observable class — continuous rho 0.4828
   (n=271), indicator rho 0.3034, state-vs-RV-p80 0.2179 — all above the
   immovable 0.20 bar. The V2 state layer does not escape the dead
   representation: it is a relabeled vol-regime gate. Floor-independent kill.
4. **Engine integrity:** state_engine implemented + 33/33 tests green incl.
   no-lookahead truncation replay (ERP-tracka law), V3 10-day invisibility,
   staleness fail-closed, dwell/merge fixtures, ladder priority, determinism.

## Why no scored run (and the standing GO delegation)

With every macro state FLAT, the router degenerates BY CONSTRUCTION to the
always-eligible book (B3); P1–P7 are unmeasurable and any scored spend would
price a tautology. The owner's standing delegation ("Sau đó chạy GO scored
luôn", recorded in `plan/OWNER_DIRECTIVE_2026-09-28.md`) was conditioned on
passing A7 for a SCORED execution that no longer has a subject — **the key
dies unconsumed** (P-8 analog: no gate existed for it to open). The same
directive's own law ("không được tự thay dữ liệu để chạy tiếp" / không hạ
chuẩn) forbids exactly the moves that would resurrect a runnable router:
floor relaxation after census, or substituting a fresh state variable chosen
post-hoc. Sleeve/router implementation lanes (I1c/I1d) were therefore never
dispatched.

## Honest disclosures

- The F2/F3 per-fold floors as preregistered are arithmetically near-
  impossible (F3≥26 state-true weeks per 26-week fold ≈ 100% occupancy) — a
  specification defect in the frozen triplet, discovered post-census and
  LEFT UNTOUCHED (no re-derivation after seeing the census; recorded as a
  LESSONS candidate). The close does NOT hinge on it: F1 (≥10 episodes on
  the full set) independently kills 3 of 4 states, and the V2 rho kill is
  floor-independent. Even the sole F1 survivor (WAR_ENERGY, margin 0) cannot
  form a router alone.
- The design's own §9 predicted occupancy as the #1 kill point ("the design
  will likely lose ≥1 state to floors, and that is the system working").
  It lost all four. Five router-class attempts on this program's question
  shape have now produced the same verdict five different ways.

## Reopening condition (stated once, Q-10)

A router-class retry on this universe (or any universe) requires a CHANGED
MECHANISM AXIS — a state source whose representation escapes the dead
vol-percentile class AND whose episode structure can clear episode floors on
the available calendar — never threshold/floor/variable iteration on this
design. A sleeve-only program (always-eligible families on the 5 eligible FX
pairs) is a DIFFERENT question requiring its own cycle, census-anchored
(DISTINCT_TESTABLE pool of 15), with its own plan and trial budget.

## Next steps in-flight

A7 independent terminal audit of this close (auditor dispatch recorded in
handoffs/), then two-half close: registry TERMINAL + head/budget, projection,
HYPOTHESIS_LEDGER row, FAMILY_FAILURES append (dead class: weekly macro-
percentile 3-var state engine; kills: floors + representation-rho) +
validator --verify, MAP.md section, LESSONS (floor-geometry lesson), session
report, commits + push.

## Erratum (A1, post-A7-terminal, 2026-09-28T14:48Z)

- A7-terminal F-4: the sentence "Five router-class attempts … same verdict
  five different ways" over-counts — REGIME-GATED-COMBO-V1's reading is
  exposed-pending-owner (not terminal). Correct count of TERMINAL
  router-class ancestors at this close: three (JEV-V2, RSM-V1, PSV1), plus
  this cycle = four; RGC-V1 remains pending the owner's a/b decision.
- A7-terminal F-5: V3's historical cadence constancy is ASSERTED-conservative
  in the PIT dossier (current-era measured, pre-2025-12 asserted); the
  decision memo's word "measured" compresses that — the conservative
  direction only (the rule can cost staleness, never leak).
- A7 verdict: `A7_TERMINAL_VERDICT: CONFIRM` (0 CRITICAL / 0 HIGH / 1 MEDIUM
  / 3 LOW / 3 INFO; independent recompute of rho and episode census matched
  to ≤4e-10 / exact; findings F-1..F-7 recorded in audits/A7_TERMINAL_AUDIT.md;
  F-3 discharged by TRIAL_LEDGER.jsonl TR-0001 in the worktree).
