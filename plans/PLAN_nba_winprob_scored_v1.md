# PLAN — NBA-WINPROB-SCORED-V1 (scored evaluation of the frozen win-prob protocol)

- cycle_id: NBA-WINPROB-SCORED-V1
- asset: shared · successor of NBA-WINPROB-PREP-V1 (integration base b5b5084753d213dfd793488d3c009cf4380e0323)
- budget: 9 scored arms max · GO phrase REGISTERED NOT CONSUMED (P-8)
- registered per owner chat directive 2026-10-04 (round 2), which is explicitly NOT a typed GO

## 0. Owner authority boundary

Owner accepted the FiveThirtyEight `nbaallelo.csv` path CONDITIONALLY for
internal research (attribution/URL/hash retained; Basketball-Reference
provenance + upstream-rights risk disclosed; no publication, no
redistribution, no commercial products) and authorized preparing/registering
this successor cycle and running A7 — while stating verbatim that the
message is NOT a typed GO and that GO must not be inferred from the data
acceptance. Boundaries: no S1, no scored run or LL/Brier on real outcomes
before a valid GO, no push/merge, no accounts/keys, no purchases, no betting;
NFL stays a separate audit-only annex sharing no budget.

## 1. Inheritance (frozen; semantic changes forbidden)

Inherited VERBATIM from `lanes/C_protocol/PROTOCOL_EVAL.md` (PREP commit
09b5eb74; sha256 pinned in FREEZE_MANIFEST.json): sections 2 (models/features),
3 (walk-forward), 4 (metrics), 5 (trial budget 9 arms), 6 (PASS/REJECT gates),
9 (GO gate + negative terminal outcomes + trial law). Frozen data split:
TEST seasons year_id 2009..2015, TRAIN 1947..2008 (lane B measured end of
data 2015-06-16). Protocol constants live in `nba_winprob/protocol.py` and
MUST remain byte-identical from freeze to execution.

## 2. Reconciliation of inoperative assumptions (documentation only)

The protocol text was drafted against a "data ends 2022-23" assumption that
lane B's byte audit superseded (data ends 2015-06-16). The following protocol
references are recorded as INOPERATIVE (N/A), WITHOUT any semantic
substitution — no hypothesis, threshold, fold, metric, or arm changes:
- §3/§10.2 "2022-23 complete / placeholder list 2016-17…2022-23" → the
  placeholder rule "final 7 complete seasons" resolves to 2009..2015.
- §7 NOT_RUN row "Seasons after 2022-23" → reads "seasons after 2015-06-16".
- §8.4/§8.7 bubble sensitivity segment [2020-08..2020-10] and the
  2019-20/2020-21 anomaly-era folds → N/A (no such eras exist in this file;
  inventing a replacement segment would be a post-hoc change).
- The 2012 lockout season (year_id 2012, 66 games) sits inside TEST — kept,
  documented (lane B anomaly A12).

## 3. Data authority (conditional acceptance recorded)

Source: FiveThirtyEight nbaallelo.csv, CC BY 4.0 (data), internal-research
only, attribution + provenance mandatory (raw/ATTRIBUTION.md). Raw + derived
bytes stay outside git under ~/.my-quantitative-data/nba-538-v1/; the freeze
manifest pins sha256 of raw + games/lineages/participants/features. The
quarantined f538_reference.csv (538 elo/forecast) is never a model input
(static + behavioral leakage tests enforce this). balldontlie remains
BLOCKED_NO_KEY. STOP RULE: if any re-check (this cycle's lane E2 or later)
finds the rights basis no longer appropriate → BLOCKED_DATA_RIGHTS, halt,
report to owner.

## 4. Gates

- G0 bootstrap: this plan + registry row + worktree orca/nba-winprob-scored-v1-integration.
- G1 data/freeze verification: lane E2 (independent re-hash, identity census,
  as-of law audit, no-538-leakage, rights re-check) PASS.
- G2 implementation complete: run_evaluation.py (fold loop, B0 refit, B1
  columns, B2 train-only standardization + L2, metrics, registered paired
  comparisons, ledger append) + synthetic fixtures PASS + refusal gates PASS.
- G3 freeze: FREEZE_MANIFEST.json (code_freeze_sha + data shas + protocol
  digest + arm table + split + seed) + TRIAL_LEDGER.jsonl seeded with 9
  PREREGISTERED arms, observed 0.
- G4 A7 prelaunch (independent, fresh context, audit-namespace-only writes):
  AUTHORIZED with 0 unresolved HIGH/CRITICAL per §19.3 checklist.
- G5 owner GO at THIS cycle's own gate — the ONLY key that unlocks scored
  execution. Two-key law: A7 verdict first, owner phrase second.

## 5. Scored execution (only after G5)

9 arms x 7 folds (2009..2015), regular season primary, playoffs separate
report; outputs under results/ + research/control/NBA-WINPROB-SCORED-V1/;
every computed arm appends to TRIAL_LEDGER (observed denominator);
reproduction is a separate +0-trial class (detached twin, byte-compare).
Post-outcome changes of any kind = new registered trial outside budget.

## 6. Terminal outcomes (negative-first)

- NEGATIVE-TERMINAL (calibration): REJECT conditions R1–R3 of protocol §6
  fire → program ends as a negative calibration result; prohibited responses
  listed in protocol §9 apply verbatim.
- NEGATIVE-TERMINAL (audit): lane E2/A7 fail → scored phase NOT_RUN.
- BLOCKED_DATA_RIGHTS (stop rule §3).
- TECHABORT_* for technical failures, exposure recorded per repo law.
- Positive path: PASS per protocol §6 T1–T3 is a CALIBRATION claim only —
  no PnL, no betting, no "edge" vocabulary.

## 7. GO phrase (registered, typed only at this cycle's own gate after A7)

    GO NBA WINPROB SCORED V1 EVALUATION

## 8. Boundaries re-stated

No S1 access. No push/merge. No accounts/API keys/purchases/trials. No
betting. NFL remains the audit-only annex (PREP commit bc19408e); it shares
no budget, data, or artifacts with this cycle's scoring.
