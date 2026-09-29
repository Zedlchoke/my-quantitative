# LANE_CHARTER — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (session 2, pre-GO, 2026-09-29; amended mid-session)

Owner directive 2026-09-29 (this session) + **owner amendment directive
(2nd, same day, recorded in `plan/AMENDMENT_OWNER_DIRECTIVE_2026-09-29.md`)**:
push the program as far as lawfully possible BEFORE the scored GO gate;
novelty of sub-strategies is NOT required — old-family/previously-rejected
ideas are DIAGNOSTIC candidates with outcome-exposed labels; survey all
1,200 by implementability; acceptance bar unchanged (untouched-fold
after-cost PnL AND drawdown vs baselines). **This is a PREPARATION
directive, not a GO.** No scored cell, no S1, no paper/live, no orders, no
push/merge, no registry writes.

## Measured state at charter (2026-09-29, root checkout)

- Branch `main @ 40036c9aa2de17588820eb783f4b5eb46fd00385`; heavy lock
  FREE_PROVEN; registry contains NO row for this cycle (0 matches
  PORTFOLIO-COMPOSITE) — the cycle is UNREGISTERED; registration needs its
  own typed owner GO at the plan's §9 phrase. 
- Dirty tree = owner's untracked work (SLEEVE-FX5-100K-V1,
  SANDBOX-OVERFIT-3ASSETS/{data,out}, SIXSOURCE ibkr_fx windows) —
  PRESERVED, untouched. This control dir is likewise uncommitted pre-GO
  evidence awaiting owner review.
- Precedent: PR12A LANE_CHARTER (pre-GO lanes in root checkout with
  declared write-scopes + handoff JSONs, no git ops).

## Lanes (A1 integrates serially; lanes never touch each other's outputs)

| Lane | Scope | Writes (ONLY) | Handoff |
|---|---|---|---|
| D data/PIT/cost | physical audit of the 3 M1 panels (coverage, gaps, .bi5 volume field, per-hour spread spot-check vs COST_AUTHORITY_TABLE, full sha256 manifests) | `poolB/data_audit/*` | `handoffs/D_data_audit.json` |
| M mechanism/corpus (reframed mid-flight per amendment) | VOLPROF-M1 class spec: payer, observable+proxy disclosure, clock/PIT, arms, costs, controls, falsifiers; ancestry section = measured-and-disclosed (informative, NOT gating); complementarity notes | `poolB/class_spec/*` | `handoffs/M_class_spec.json` |
| P policy/journal/accounting | PASS_BARS_V2 (owner AND-semantics, full P1–P8 incl. the missing P6), FILL_ACCOUNTING_SPEC (spread-once law, book identity), 5 hand-computed fixtures, switching-cost ladder | `policy/PASS_BARS_V2.md`, `journal/FILL_ACCOUNTING_SPEC.md`, `journal/fixtures/*` | `handoffs/P_passbars_accounting.json` |
| R complementarity grouping (wave 2, after D+M+A1-ladder-v2) | from the 292 exploratory candidates: mechanization-screening priorities, proposed co-usable groups (family × asset × horizon diversity), pre-trade-only ON/OFF feature inventory, missed-profit/switching-cost measurement plan | `poolB/grouping/*` | `handoffs/R_grouping.json` |
| S skeptic (wave 3) | independent attack on the AMENDED protocol: multiple-testing surface at 292 candidates, outcome-exposure containment, baseline/null validity, fold-lock enforcement points | `poolB/skeptic/*` | `handoffs/S_skeptic.json` |
| A7 prereview (wave 4, fresh context) | read-only review of the integrated package | `audits/A7_PREREVIEW.md` | `handoffs/A7_prereview.json` |
| A1 (this session Lead) | corrections to session-1 artifacts (GBPUSD cost-axis typo + regenerate + validate 1,200 unique IDs/provenance/counts; wording precision; external pins manifest), integration of lane outputs, PASS-bar incorporation into the policy architecture, session report, owner packet, STOP at registration gate | `eligibility/*`, `SESSION_REPORT.md`, `plan/*`, `manifest/*`, `policy/PORTFOLIO_POLICY_ARCHITECTURE.md`, `LANE_CHARTER.md` | — |

## Laws binding every lane agent (inherited from PR12A charter + CLAUDE.md)

1. Read-only outside declared output files. No git write operations at all.
   No registry/ledger/MAP/LESSONS writes. No heavy jobs, no backtests, no
   S1, no network.
2. Never touch: other cycles' control dirs, `.worktrees/` (Lane D READS
   worktree panels read-only — writes stay in this control dir), `plans/`,
   `research/wayfinder/` (read OK).
3. All 1,200 ideas are HYPOTHESIS/NOT_RUN; the 3 volume-profile rows are
   candidates, not admitted legs. No lane may imply a backtest happened.
4. Every number reproducible; missing evidence is NOT_RUN/UNAVAILABLE,
   never inferred. Report BLOCKED rather than assuming.
5. One heavy job machine-wide stands; nothing in this session qualifies as
   one (read-only audit + document drafting only).

## Stop point (owner law)

Session ends at the REGISTRATION gate: the plan draft + this charter + the
poolB adjudication are complete, the A7 prereview verdict is recorded, and
the owner packet names exactly ONE next action. No GO phrase is typed,
inferred, or reused. If the F0+skeptic slate is empty, the packet's action
is the NO_ELIGIBLE_PROPOSAL decision instead of registration.
