# CYCLE_PROPOSAL — path from FUTURES-SIX-SCORED-GATE-PREP-20261004 to the first lawful scored run

- Round: **FUTURES-SIX-SCORED-GATE-PREP-20261004** (controller synthesis over
  lanes FEE-A7 / CAL-CLOSE / SHORTLIST / BUDGET at wave-1 commit `75f7ea96`).
- Law restated: the owner's "Tôi cho phép thử thêm / thử NQ với lại ES / còn
  4 mã forex thì cũng thử luôn đi" is PREP-to-gate authorization ONLY.
  **It is NOT a typed GO. Nothing in this proposal runs anything.**
  NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER stand. Registration happens at
  ROOT by the owner (this thread never touches the registry). **0 scored
  runs, 0 engine runs, 0 dry-runs, 0 PnL exist anywhere in this round.**

## 0. What changed this round (evidence, all committed)

| Former blocker | Status now | Evidence |
|---|---|---|
| Fee A7 "READY-NOT-RUN" (D2 execution half) | **EXECUTED — AUTHORIZED_WITH_FINDINGS, 0 HIGH/0 CRITICAL unresolved** (run-order steps 0-9 complete; 21/21 inputs byte-verified; validator 37/37 reproduced) | `fee_a7/A7_FEE_REAUDIT.md` + `a7_fee_digest.json` |
| D5 CPI Jan-2026 pin | **OBTAINED**: Friday **2026-02-13, embargo 08:30 a.m. ET**, USDL-26-0186, dual official artifacts (schedule snapshot + release doc) | `cal_close/CAL_CLOSE_REPORT.md` |
| NQ 2026 Good-Friday advisory | class-level **10/10** (Sep-2026 vintage capture) | `cal_close/calendar_close_delta.json` |
| ES 2026 holiday deviations | 3 windows FACT-grade (archived trading-hours captures; 1 recovered with disclosed sha discrepancy vs a round-1 claim) | `cal_close/` |
| 14 FX expiry residuals | **CLOSED_PROVEN_ABSENT** (documented exclusions, fail-closed — no longer "open") | `cal_close/RESIDUAL_INVENTORY.md` |
| ES cap arithmetic ambiguity (43 vs 60) | reconciled: 43 excludes PB1's frozen 24; 60 = 24+36; 67 = 60+7 — neither is a ceiling | `budget/IDENTITY_TABLES.md` |
| Shortlist/budget vacuum | 7-criteria shortlist + 16 exact identity-table options | `shortlist/`, `budget/` |

What did NOT change: PB2 HOLD (6E/6B), PB3 PARK (6A), ES cap 24 FROZEN,
NQ cache_v3 candidate status (D9), 6A tick-era (D8), D3 basis choice,
e.1-e.4 fee sub-rulings, and the absence of any typed GO. All remain owner
signatures — exactly as the owner's instruction demands.

## 1. Recommended structure: SPLIT CYCLES (lawful-optimal)

One 6-symbol cycle is lawful only if PB2+PB3 lifts, four ceilings, D8/D9
and the cap amendment all land at once — a maximal-signature registration.
The split reaches a first valid scored run with the FEWEST signatures and
keeps every later door open:

- **CYCLE-1 `FUTURES-ES-PB1-V1` (recommended first): ES only, PB1 only,
  24 identities — the framing-A minimum-signature path. STATUS:
  **BLOCKED_COST_FREEZE** pending the owner's D3/e.4 basis ruling
  (COST_FREEZE_ERRATUM; corrected dual-variant cost table required at
  freeze — Variant A 2.25/side, 21.00/33.50/46.00 · Variant B 2.24/side,
  20.99/33.49/45.99; the stale SPEC print 21.006/… is never consumable).**
  - Scope: the ALREADY-REGISTERED parent family PB1 (OVN pair M-A/M-B +
    FOMC 4 + C1-C4 4 = 24, SPEC_PB1_ES §6 table verbatim). **No D4 cap
    amendment is needed (24 = 24).** Zero new families = zero new
    ancestry/novelty exposure.
  - Remaining gates (in order, all owner-side or post-registration):
    1. **D3 basis signature (EXPLICIT, fail-closed — CYCLE-1 freeze is
       BLOCKED_COST_FREEZE without it; the silent-default operating rule
       is withdrawn per COST_FREEZE_ERRATUM §3.4; the lawful silent
       reading, if ever needed, is Variant A × corrected 1.38 only)** +
       e.1-e.4 fee sub-rulings signed at/before freeze (the A7 has
       executed cleanly; its findings discharge the audit precondition
       for cost-bearing cells);
    2. **Registration at ROOT** (freeze set: SPEC sha `445f7499…b7073`,
       chain digests, cost-table digest, calendar provenance manifest incl
       this round's ES-holiday FACT cells and the fail-closed exclusions);
    3. Prelaunch A7 (fresh-context, identity/cost/PIT/budget/freeze audit)
       — key 1 of 2;
    4. Exact-arm dry-run (post-registration by law);
    5. **Typed GO: `GO FUTURES-ES-PB1-V1 SCORED EXECUTION`** — key 2 of 2;
    6. Scored under heavy lock + reproduction twin + terminal A7.
  - Calendar posture: ES expiry 68/68; 2026 holidays 3 windows FACT +
    remaining product-level cells excluded fail-closed (documented).
- **CYCLE-2 `FUTURES-NQ-V1` (next, one extra signature set): NQ families
  per ceiling option NQ-A/B/C/D (22/29/36/43)** — requires D9 (cache_v3
  canonicalization + cease-guard law), the NQ ceiling choice, A7, and the
  same registration→GO sequence. Adding the NQ leg of EXPWITCH here is
  option NQ-D.
- **CYCLE-3 `FUTURES-FX-V1` (6E/6B/6J; behind PB2-lift + ceilings)**:
  options FX-A/B/C (44/66/96 CONV-D) + J-A/B/C (29/36/33-40). 6A stays a
  contingency annex (PB3 lift + D8) — its 26-identity contingency table is
  frozen in `budget/` but enters no cycle until the owner unparks it.
- A combined CYCLE-0 variant (all 6 symbols, maximal signatures) is lawful
  but NOT recommended: it couples the earliest possible scored run (ES) to
  the slowest rulings (PB2/PB3/6A-D8).

## 2. Freeze-ready elements already in place (CYCLE-1)

1. Identity table: SPEC_PB1_ES §6 (24; verbatim; untouched —
   `445f7499…b7073` re-pinned this lineage).
2. Chain of record: baseline ES chain per SPEC §1 (68/68 expiries
   re-derived, 66/66 data-side) — digest pinned at registration.
3. Cost contract: **dual-variant corrected table (COST_FREEZE_ERRATUM
   §2)** — A: fees 2.25/side, all-ins 21.00/33.50/46.00 · B: 2.24/side,
   20.99/33.49/45.99 (exchange 1.38 evidence-settled; 1.386 retired;
   MODELED, VERIFIED_VS_ACCOUNT=NOT_RUN); the executed A7 re-audit is
   clean (0 HIGH/CRITICAL); stress ladder ×1.0/×1.5/×2.0; BBO NOT_RUN
   conservative fill law. **Which variant executes = owner D3 signature
   (explicit, fail-closed) — CYCLE-1 freeze is blocked without it.**
4. PIT/exclude set: FOMC 132 statements standing-outside law; BLS vintage
   law; the new D5 pin (2026-02-13 CPI) folded into the vintage manifest;
   holiday-adjacent exclusions fail-closed per CAL-CLOSE inventory.
5. Fold structure: ES precedent 4-fold shape (F1 2010-06..2012-12 · F2
   2013-01..2017-12 · F3 2018-01..2021-12 · F4 2022-01..2026-09), warmup
   252 sessions, era K-views declared.
6. Gates: CYCLE_LAUNCH_DRAFT §6 sequence adopted verbatim (two-key law,
   GO phrase exact-match, BLOCKED_AUTHORITY consequences).

## 3. Honest statement of what "tried" means at close of this round

- **Scored trials actually run: 0.** The owner's speech is not a GO, so
  the run stops exactly here: freeze-ready, gate-mapped, signatures
  enumerated.
- **Symbols still blocked from any scored run today and why:**
  ES — **D3 cost-freeze signature (BLOCKED_COST_FREEZE until signed;
  corrected dual-variant table in COST_FREEZE_ERRATUM §2)** then
  registration + prelaunch A7 + typed GO (everything else
  closed); NQ — D9 + ceiling + registration + GO; 6E/6B — PB2 lift +
  FX ceiling + registration + GO; 6J — 6J ceiling + BBO/cost gates +
  registration + GO; 6A — PB3 lift + D8 (then contingency annex).
- The single minimal decision that unlocks the first scored run is in
  OWNER_DECISION_PACKET.md §OD-1 (CYCLE-1) — one scope choice, one D3
  signature (explicit; no silent default), then registration and the typed GO phrase.

— End CYCLE_PROPOSAL.md. Preparation, not authorization.
