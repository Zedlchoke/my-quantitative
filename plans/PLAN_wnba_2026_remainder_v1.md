# PLAN — WNBA-WINPROB-2026-REMAINDER-V1 (remaining 2026 playoffs prospective PREP, $0)

- cycle_id: `WNBA-WINPROB-2026-REMAINDER-V1` · asset: shared · budget 0/0 (ZERO
  scored cells) · registered 2026-10-07.
- Owner authority 2026-10-07 (this chat, CORRECTION): WNBA 2026 playoffs are NOT
  finished (semifinals 2026-10-07: Atlanta–NY Liberty 23:30Z, Golden State–Las
  Vegas 01:30Z — SEMIFINALS, not Finals). The 2027-frozen cycle
  `WNBA-WINPROB-PROSPECTIVE-PREP-V1` deliberately locks season ≥2027 and its
  GO/ledger MUST NOT be used for 2026. This cycle covers the REMAINDER OF 2026
  only. Explicitly **NOT a typed GO**.
- GO phrase (REGISTERED_NOT_CONSUMED, typed ONLY by the owner, verbatim, fresh,
  at this cycle's own gate):
  **`GO WNBA WINPROB 2026 REMAINDER V1 PREDICTIONS`**

## Scope (mirror of the 2027-frozen PREP, window law changed)

Prospective pre-tip forecasting of the remaining 2026 WNBA playoff games with
**B1-WNBA verbatim** (own-Elo K=32/HCA=50/γ=0.65; engine pins `arms.py`
82263eab…/`harness.py` b9446f76…, re-hashed at freeze), B0 = 0.603755 floor.
Ledger `wnba_2026_remainder_ledger@1` ported from `wnba_prospective_ledger@1`
(57/57 precedent) with provenance note; window law: season == 2026 remainder
only (playoff games from the freeze snapshot forward), never 2027.

Lanes: (1) DATA REFRESH — frozen-snapshot refresh of the espn_wnba_schedules +
espn_wnba_team_boxscores release-store lineage absorbing every COMPLETED 2026
playoff game into the rating stream as HISTORY (provenance URL+tag+timestamp+
bytes+sha256 per file; extension-only; re-verify rights bytes); tip law verbatim
(`tip_utc := parse(espn.date, ISO8601, UTC)`, `local_date := ET date`). (2)
LEDGER — port + adapt batch law: **tip-relative day-anchored batch at
T0 − 6h10m** (E-2 law: T0 = earliest tip of the ET game-day from the pinned
schedule snapshot; strict `recorded_at_utc < tip_utc` at append AND scoring;
stream state = games with tip < batch anchor AND result present — completed
only; no re-prediction, no backfill, played-before-record = NOT_RUN forever).
(3) FREEZE — constants verbatim, seed pinned once, no-parameter-change-after-
first-real-row, falsifier wording carried, per-game-batch census of the
remaining playoff slate from the pinned schedule. (4) SYNTH + DRY-RUN sandbox
(zero real rows). (5) A7 PRELAUNCH fresh context (0 unresolved HIGH/CRITICAL).

## Timing law (measured 2026-10-07T06:38Z from The Odds API events, 0 credits)

Semifinal 1 anchor **2026-10-07T17:20:00Z**; semifinal 2 anchor
**2026-10-07T19:20:00Z**. A game whose anchor passes before (owner GO + forecast
record + A7-frozen state + paper-capture GO) are all complete is **NOT_RUN
forever** — never backfilled. Feasibility is reported per-game with exact UTC
deadlines.

## Boundaries

$0; no purchases; no S1; no push/merge/rebase; registry via researchctl CAS;
heavy lock machine-wide; data under
`~/.my-quantitative-data/wnba-2026-remainder-v1/`; the 2027-frozen cycle tree
(9ed717c4) and ALL other cycles read-only; the paper-trade cycle
(`SPORTS-PAPERTRADE-V1`) consumes this cycle's forecast rows only after BOTH
gates have owner GOs; paper laws (one 1,000 USD wallet, 5.00 USD fixed stake,
100 USD open cap in-lock, EV≥5% c=0.02, drawdown pause 10%) live in
SPORTS-PAPERTRADE-V1 and are untouched here. Worktree/branch:
`orca/wnba-2026-remainder-v1-integration`. Terminal outcomes:
PRELAUNCH_READY_PENDING_OWNER_GO | PRELAUNCH_BLOCKED_<gate> |
NOT_RUN_<game/scope>_PAST_ANCHOR | TECHABORT_*. An early/paraphrased GO dies
unconsumed.
