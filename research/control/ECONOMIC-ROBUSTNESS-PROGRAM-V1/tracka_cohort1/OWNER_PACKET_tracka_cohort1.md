# OWNER PACKET — ERP1-TRACKA-COHORT-1 child-plan decision (rev 2, 2026-09-25 session 2)

Decision surface for: `plans/DRAFT_ERP1_TRACKA_COHORT_1.md` (DRAFT_FOR_OWNER_GO
— nothing registered, nothing executed, no worker touched, no S1, no orders,
no commit). Rev 2 incorporates the owner's locked decisions (D-B/D-C/D-E),
the PIT-seam incident record, the shadow classification proposal, the two
blind proposer lanes, and the A7 delta review outcome (see §5).

## 0. Decision state

| ID | Decision | State |
|---|---|---|
| D-A | GO / NO-GO registration of ERP1-TRACKA-COHORT-1 | **OPEN — this is the GO-1 gate.** Type the phrase in §2 exactly. |
| D-B | Pair slate AUDUSD + USDCAD; replication surface = the two NEW pairs only; EURUSD/GBPUSD/USDJPY stay outcome-exposed ancestry | **LOCKED by owner 2026-09-25** |
| D-C | No independent-source unblock; all results `SINGLE_SOURCE_PANEL`, paper tier only; Task-1b reconciliation-only | **LOCKED by owner 2026-09-25** |
| D-E | Blind proposer lanes added (P1+P2 ran, composition literal-compliant); no additional mechanism slots; M2 not rescued | **LOCKED by owner 2026-09-25** |
| D-F | Proposed classification of FX-RANGEFADE-2M-SHADOW-V1 as `DIAGNOSTIC_PENDING_PIT_REBASE` (proposal only; daemon/journal/ledger untouched; no promotion; no $100k-account change; fail-closed default = no change) | **OPEN** — see `PROPOSAL_SHADOW_CLASSIFICATION_FX-RANGEFADE-2M_2026-09-25.md` |

## 1. What session 2 added (all evidence-gated, nothing executed)

1. **Incident recorded** — `INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md`: the
   ancestor law's whole-day mode leak + hindsight flat-day filter + the
   three-laws seam (scored R-ORIG ≠ daemon partial-range law ≠ PIT-clean
   R-ANCHOR), with the citation law: ancestor backtests are R-ORIG-semantics
   facts and are NOT evidence for the running daemon law nor for R-ANCHOR;
   "shadow parity PASS" is never citable as semantics evidence. Daemon
   (PID 79157), journal, state, dashboard, ledgers: untouched, still running.
2. **Shadow classification proposal (D-F)** — diagnostic class pending PIT
   rebase / amendment-A1 observability; exit conditions named; explicitly
   NOT proposed: any parameter change, restart, promotion, $100k-account
   action, re-registration.
3. **Blind proposers P1+P2 (D-E)** — same blindness law, independent lanes.
   No slots opened, M2 not rescued. Their proposals are recorded as
   FUTURE-COHORT candidates (PROV-ABSORB; RECLAIM-ABSORB — with the
   explorer's retest-class veto tension flagged for a future D2;
   PROBE-DEPLETION GATE). Their design-review findings became binding plan
   law: F-3 mode-sham signal test; §9.1 inverted-control holdout companion;
   control gross+net decomposition (M3); F-4 beta-composition disclosure.
4. **Plan hardenings for C2/C3/C4** (from A7's first audit): F-1
   representation law; holdout one-look scope (dead arms take no look);
   F-5 declared-band arithmetic with the explicit no-gross-backtest-before-
   F-PIT-1-freeze clause. **C1 resolved via D-E** (proposer lanes added).
5. **Trial ledger contract frozen** (§10): append-only JSONL row schema with
   mandatory labels (`SINGLE_SOURCE_PANEL`,
   `FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK`, `PAPER_TIER`) and control-row
   gross/net decomposition.

## 2. The GO-1 gate (exact phrase; nothing pre-consumed)

```
GO ERP1 TRACKA COHORT 1 REGISTER AND COUNCIL
```

Typing it authorizes, in order: registration via `researchctl cycle
register` (payload = the plan §0 identity block); the child worktree; the
§5.2 data-gate probe downloads for AUDUSD + USDCAD (~110–150 MB bounded,
heavy-locked); the PIT/cost audits and the full falsifier battery
(F-1..F-7 incl. F-PIT-1 M-1..M-5); the trial freeze + ledger seed; A7
prelaunch; — and STOPPING before any scored cell (GO-2 is a separate fresh
phrase at the scored gate). If the falsifiers kill the cohort, the cycle
records `REJECT_ALL` / `BLOCKED_*` honestly and stops — no substitute pair,
no parameter replacement.

## 3. Honest expectation (unchanged, now sharper)

F-PIT-1 (the seam) and F-5 (cost ceiling) are the modal killers. The
R-ANCHOR law has never produced a result anywhere; if its battery fails,
falsification-with-zero-PnL is the correct, expected outcome. Best
achievable positive label: `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`
(paper tier). `REJECT_ALL` is a valid terminal verdict.

## 4. Artifacts (all under research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/ unless noted)

Plan: `plans/DRAFT_ERP1_TRACKA_COHORT_1.md` (sha256 in §5 below).
Council: EXPLORER/SKEPTIC(incl. D2)/DATACOST/PROPOSER1/PROPOSER2 reports +
6 lane handoffs. Audit: `A7_tracka1_plan_audit_REPORT.md` (round 1) +
`A7_tracka1_delta_review_REPORT.md` (round 2, this session). Records:
`INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25.md`,
`PROPOSAL_SHADOW_CLASSIFICATION_FX-RANGEFADE-2M_2026-09-25.md`. This packet.

## 5. A7 delta review (round 2) — VERDICT: PASS; GO-1 READY: YES

Round 1 (`PASS_WITH_CONDITIONS`, C1–C4) → all four conditions verified
RESOLVED in the plan text. Round 2 (`A7_tracka1_delta_review_REPORT.md`):
**PASS — 0 CRITICAL / 0 HIGH / 0 blocking conditions; GO-1 READY: YES.**
Remaining dispositions (all non-blocking, now applied to the plan):
- **D1 (MEDIUM)** — five GO-1 freeze-artifact pins (bootstrap + mode-sham
  seeds with storage path; holdout-pass membership artifact + sha;
  mode-sham outcome vocabulary; two-pair UTC close semantics; seam limb
  (iii) minimum-N floor of 20 matched pairs ⇒ NOT_RUN fail-closed) —
  integrated as plan §10 "GO-1 freeze-artifact mandatory pins"; A7
  prelaunch verifies all five before GO-2.
- **D2–D6 (LOW)** — F-5 cross-reference corrected (§7.3 field 2); stale
  Task-1b upgrade bullet marked SUPERSEDED under the D-C lock; D-B lock
  annotated in §5.2 and appendix A.1; seam limb (iii) tie-break rule
  frozen (earlier entry_ts) + minimum-N floor; P2's mode-day beta
  decomposition left report-only per A7.

## 6. What session 2 did NOT do

No cycle registration (waits for the GO phrase), no scored cell, no
download, no S1, no order, no FX worker/daemon/journal/ledger touch, no
registry write, no commit (files left untracked for your review), no GO-2.
