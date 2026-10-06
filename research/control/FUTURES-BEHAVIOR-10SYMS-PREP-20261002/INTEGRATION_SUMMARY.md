# INTEGRATION_SUMMARY — FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (A1 Lead, 2026-10-02)

Prep-only task. 0 scored runs, 0 PnL/event studies/rule sweeps, 0 purchases,
0 credentials, 0 registrations. Owner framework treated as hypotheses
(snapshot + SHA256 in owner_framework/). All **14** handoff artifacts
COMPLETE — 12 lane handoffs (10 dossier + engine + data) + the A7 audit
handoff + the FIX-A7-FINDINGS handoff (dispatch/handoff_*.json, schema
zcode_orch_v3_handoff@1). [Count corrected 2026-10-02, round
co-owner-review-fix-1: the Lead commit message for eae8c3d2 miscounted
"13".] Attempt-1 originals preserved VERBATIM in
dispatch/archive_attempt1/ (ORIGINAL_SHA256SUMS.txt); canonical-form
replacements written by lane HANDOFF-RESEARCH and checked by script
dispatch/validate_handoffs.py — 14/14 structurally valid, outputs digests
re-verified at eae8c3d2. The orchestrator MCP handoff validator is NOT_RUN
in this session; "validated" above means script-validated only, never
canonical/MCP-validated.

## 1. Cross-symbol synthesis (evidence in per-symbol dossiers)

1. **Declared roll rule is defective for 9/10 symbols in different ways**
   (each OBSERVED per-dossier; CL is the non-counted symbol):
   - FX (6E/6J/6B/6A) + SI: liquid chain is cycle/quarterly-only (HMUZ;
     SI H/K/N/U/Z). Literal "next listed contract" routes into near-dead
     serial books (e.g. 6JX6 26 lots vs 6JZ6 118,886 on 2026-10-01).
     Executable baseline = cycle-chain roll (6J dossier H1 restates it).
   - NG [re-classified by the audit-M2 fix, 2026-10-02]: the rule is
     FEASIBLE on the canonical basis — expiry month = the LAST-TRADE-date
     month (raw `expiry_month` header), NOT the delivery month (S1
     `expiry_date`); the earlier "infeasible outright" claim here and in
     the NG dossier §1 applied a delivery-month reading and is retired.
     Because NG fronts stop trading on the 3rd-last business day of the
     month before delivery, a delivery-month reading would bind at the
     front's final session — the same rule's boundary consequence, not a
     fork. Residual NG defect is rule-vs-market divergence, not
     infeasibility: calendar-nearest ≠ volume-max seasonally (8/13 pairs
     months-early winter dominance), and the NG dossier's chain holds the
     live front (NGX26) ~1 month past the engine's canonical roll
     (2026-09-30); its matured rolls coincide with canonical sessions
     (expired files are cut exactly at the canonical boundary).
   - ES/NQ/GC/6A: declared timing rolls while old contract still carries
     3–7× next's volume (thin-book window 4–9 sessions/quarter); GC is the
     exception on migration shape (crossover 1–2 sessions BEFORE roll).
   - June ES expiry ≠ 3rd Friday (Juneteenth); FX IMM dates holiday-shifted
     (MLK/Presidents) — calendar code must special-case holidays.
2. **Snapshot holes make even the declared rule non-reconstructable**:
   GC 6 serials (2025-11…2026-09), 6J 8 serials, 6B all expired serials,
   6A 6 serials (2026-01…08) were never fetched. TIME-CRITICAL $0 FIX for
   owner: expired-secdef resolve window ~1y — 6A's 6AF6/6AG6 age out
   ~Jan–Mar 2027; GC/6J/6B serials similar horizon. Re-fetch under existing
   entitlement before they age out, or the calendar-roll baseline is
   permanently unprovable on this snapshot.
3. **Roll/carry structure measured**: ES 5/5, NQ 5/5, SI 6/6, GC (contango
   99.8–100% sessions), 6E 4/4 gaps positive; CL all 14 negative (steep
   backwardation 280/280 days); NG seasonal flip (m1−m2 negative on 75% of
   front-era days = contango-shaped curve: near at a discount to the
   deferred winter leg; the median flips positive mid-winter — see NG §3;
   [m1 fix 2026-10-02: an earlier revision here mislabeled the negative
   medians "backwardated"]); 6B mixed; 6A mild 2026 backwardation; 6J
   ~−2.6%/yr long-JPY drag. Unadjusted continuous chains embed these jumps
   — engine enforces feature-only adjustment (verified by regression test).
4. **True-volume front chains are 13.5–16 months only** (2025-05/08/09→now;
   definitional note, m3 fix 2026-10-02: that range uses the
   coverage-manifest CALENDAR-RUN definition — first session from which the
   declared-rule front chain prints real volume daily. Per-dossier
   real-volume ERAS on alternative chain constructions start earlier by
   design: GC 2025-01-15 (~21 months, cycle-skip chain, 424 returns) and
   6J 2025-05-20 (quarterly HMUZ chain); the starts differ because the
   chains differ, not because any measurement disagrees);
   deeper daily bars are settlement-derived deferred marks (NG: deep bars are
   strip legs, NOT contemporaneous fronts). Intraday snapshot is RTH-only
   (useRTH=true) — overnight/Globex, Asia/London sessions, BoJ timing
   NOT_RUN everywhere. AU/China/BoJ events fall entirely outside recorded
   bars (6A/6J tz asymmetry finding).
5. **Cost corrections vs S6**: SI spread row measured a dead serial book —
   liquid-era proxy ~$100/contract (SI dossier); 6A quarterly 2 ticks/$10 vs
   S6 $20 (serial). Exchange fees NOT_FETCHED 9/10 (CME transport-blocked);
   only ES all-in $2.24 documented. Slippage NOT_RUN_NO_DECLARED_VALUE.
6. **Sample-power caveats**: single-regime windows dominate (NQ/ES rally;
   SI squeeze-crash +217%/−31% days; 6J record MOF intervention year 2026).
   Any hypothesis pass must survive year-by-year/regime splits that the
   current depth cannot provide — most behavior hypotheses are vendor-gated.

## 2. Hypothesis registry (extract; full specs in dossier §5)

| ID | Symbol | Theme | Class | Testability now | Gate |
|----|--------|-------|-------|-----------------|------|
| NQ-H1..H5 | NQ | CoT positioning; consensus surprise; Globex; ≥2y depth | macro/positioning/micro | H1 cheapest (free PIT CoT) | H2-H5 vendor/consensus |
| ES-H* | ES | macro-release structure; roll-timing micro | event/micro | partial (depth 14mo) | consensus archive |
| CL-H1..H5 | CL | EIA WPSR structure; backwardation regime | event/term-structure | event calendar verified; depth thin | consensus PARAM-GAP |
| NG-H1..H5 | NG | storage-report session; seasonal curve flip | event/seasonality | EIA timing verified; ~2.2y intraday best-in-set | weather vintages |
| GC-H1..H2+ | GC | carry curve; vol regime | term-structure/macro | carry OBSERVED; consensus PARAM-GAP | vendor depth |
| SI-H* | SI | squeeze regime; GC/SI ratio | regime/cross-asset | ratio OBSERVED | regime breadth (single-event sample) |
| 6E/6J/6B/6A-H* | FX | CIP carry; intervention (6J); BoE/RBA/BoJ events | macro/positioning | CIP POSTULATED (rates not in repo); 6J intervention OBSERVED w/ 1-month publish lag | basis/quote-orientation transfer; overnight bars |

Common PARAM-GAP discipline maintained; corpus-1200 FX transfers marked
POSTULATED with basis/roll/cost differences, never "already valid".

## 3. Data-gap priorities (owner decisions)

1. **$0, time-critical**: serial re-fetch (above) before expired-resolve
   window closes. Measured age-out frontiers (SERIAL_REFETCH_MANIFEST.md):
   6JV5/6JX5 likely ALREADY past the FX resolve wall; GCX5 + F6-class
   critical by ~Dec-2026; the earlier "~Q1-2027 oldest" estimate was
   optimistic — treat as urgent.
2. **$0**: useRTH=false re-pull for Globex/overnight on same entitlement
   (NQ dossier flags it as cheap fix) — would unlock session hypotheses.
3. **Paid, owner-gated**: Databento GLBX.MDP3 per DATA_ACQUISITION_SPEC.md —
   Phase-0 FREE probes (per-symbol schema/start verification, billable size,
   record count) MUST precede any spend; Standard $199/mo = 16y L0 only.
   IBKR-overlap pilot NQ+CL acceptance thresholds specified.
4. Not solved by vendor: consensus archives, NG weather forecast vintages
   (NOAA NOMADS), macro vintages (ALFRED), broker slippage — public lawful
   options listed with URLs in DATA_ACQUISITION_SPEC.md.

## 4. Deliverables map

- 10 dossiers dossiers/*_DOSSIER.md (7 sections, taxonomy-tagged)
- Framework coverage matrix: each dossier §7 answers master-framework §1
  questions + its symbol checklist (answer + evidence class / NOT_RUN)
- Prep code + 147 offline tests (140 original + 7 audit-M3 close-only-fill-law
  regressions, 2026-10-02): code/futbt/ + code/README.md + run_tests.sh
- BACKTEST_LAUNCH_DRAFT.md (arms/variants/trials/seeds/costs/PIT/admission —
  DRAFT pending data depth + registration; no GO)
- data/COVERAGE_MANIFEST.json + DATA_ACQUISITION_SPEC.md
- Source/evidence manifests: per-dossier headers cite artifact sha256s;
  owner framework SHA256SUMS.txt; primary URLs + access dates in dossiers

## 5. What is possible today vs gates

- Today (prep only): daily signal research on 13.5–16-month true-front
  chains + settlement-derived deep reference; descriptive behavior; engine
  tested on synthetic fixtures; free-data hypotheses (CoT) specifiable.
- Before ANY backtest: serial fix (roll baseline), owner data-depth choice
  (14-month declared-cost backtest vs vendor history), declared slippage +
  9/10 exchange fees, real holiday calendar source, rule set R freeze.
- Before scored: registered budget/freeze + owner GO per workspace law.
