# DECISION PIPELINE V1 — DESIGN (owner target; feature-gated behind GOs)

## State machine per fixture per matchday
1. FORECAST (pinned engine, pre-anchor, existing)
2. PM QUOTE (per-league adapter; cutover-gated)
3. DETERMINISTIC GATES (EV≥5%, PIT, stake, cap, drawdown)
4. AI REVIEW (mandatory; 10-min budget; system-captured evidence)
5. IN-LOCK RE-CHECK (fresh quote hash + gate re-run)
6. APPEND (exactly one BET_PAPER via pinned core, or NOT_PLACED)

## Feature gates
- pm_cutover_active: registry phase contains cutover GO_CONSUMED
- ai_authority_active: registry phase contains AI-ACTIONS GO_CONSUMED
Both default FALSE. Pre-GO: pipeline returns NOT_RUN_CUTOVER_PENDING /
ADVISORY_ONLY respectively. Implementation: research/papertrade_exec/
decision_pipeline.py (state machine + gate evaluator, tested).
Runner wiring: the cadence calls decision_pipeline.run() when
pm_cutover_active; the AI gate is mandatory when ai_authority_active.
Until both are active the existing pinned decide path runs unchanged.

## What is BUILT vs DESIGNED
BUILT: decision_pipeline.py (state machine + deterministic gate evaluator
+ AI gate grader + candidate hash), pm_moneyline.py (2-way joiner+walker,
live-verified), ai_gate.js (17/17), paper_policy.js (27/27).
DESIGNED but NOT wired into the pinned runner: per-league PM quote
dispatch, pre-decision AI call from Python, in-lock re-fetch. These
require the cutover GO and AI authority GO respectively — building them
before the GOs risks dead code and law drift. The owner should register
the cycles first, then the implementation follows in the authorized lane.
