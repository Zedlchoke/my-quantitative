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
Runner wiring (ERRATUM W4, PAPERDESK-FIXALL-NCAA-V1 2026-10-21 — this
paragraph previously described a decision_pipeline.run() that never
existed): there IS no decision_pipeline.run(). The decide path is
execute.cmd_decide; when ai_authority_active it runs the v2 authority
gate execute.apply_ai_gate_v2 (hash-locked ALLOW|VETO opinions via
ai_gate_v2.py, PENDING_AI silence law, NOT_PLACED_AI_NO_VERDICT at
anchor-30m) — for EVERY league including WSL (wired inside
wsl_lane.cmd_decide). decision_pipeline.py remains the sandbox
gate-evaluator + candidate-hash reference; ai_gate.js / paper_policy.js
are legacy sandbox/display mirrors, unwired from authority.

## What is BUILT vs DESIGNED
BUILT: decision_pipeline.py (state machine + deterministic gate evaluator
+ AI gate grader + candidate hash), pm_moneyline.py (2-way joiner+walker,
live-verified), ai_gate.js (17/17), paper_policy.js (27/27).
DESIGNED but NOT wired into the pinned runner: per-league PM quote
dispatch, pre-decision AI call from Python, in-lock re-fetch. These
require the cutover GO and AI authority GO respectively — building them
before the GOs risks dead code and law drift. The owner should register
the cycles first, then the implementation follows in the authorized lane.
