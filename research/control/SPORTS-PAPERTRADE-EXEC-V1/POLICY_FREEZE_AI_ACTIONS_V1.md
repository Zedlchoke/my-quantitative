# POLICY FREEZE — AI ADVISORY ACTIONS (KEEP / SKIP / SWITCH) — V1
# Cycle SPORTS-PAPERTRADE-EXEC-V1 · frozen 2026-10-20 · AMENDMENT_MACOS_APP_UI_V1 §9
#
# AI AUTHORITY STATUS: **NOT REGISTERED**. Nothing in this freeze activates,
# registers, or consumes any GO. The evaluator is SANDBOX/ADVISORY: it writes
# to the AI sidecar only and NEVER to the paper ledger. Executing a SWITCH on
# the standing paper decision would require a FUTURE owner-registered cycle
# with its own policy freeze + A7 prelaunch + owner GO typed at that gate.
# STOP BEFORE OWNER GO — this freeze stops exactly there.

## 1. Frozen action enum (opinion field `recommended_action`)

| Action | Meaning (advisory) | Lawful without further gates? |
|---|---|---|
| KEEP | the standing paper decision stands | always lawful (advisory) |
| SKIP | stay out of the fixture | always lawful (advisory); on an open bet the placed bet stays per ledger law |
| SWITCH | prefer `proposed_leg` INSTEAD of the standing leg, SAME fixture | graded against EVERY gate in §2; PASS is advisory-only evidence |

Anything outside the enum ⇒ recorded INVALID. `null` ⇒ no action expressed.

## 2. Frozen SWITCH gate set (ALL must pass; frozen ledger numbers ONLY)

| Gate | Frozen criterion |
|---|---|
| G_PROPOSED_LEG_VALID | proposed_leg ∈ {HOME,DRAW,AWAY} ∩ quoted legs of the fixture |
| G_NOT_SAME_LEG | proposed ≠ standing chosen leg (otherwise it is a KEEP) |
| G_QUOTE_PRESENT | frozen pre-anchor quote exists for the proposed leg |
| G_DEPTH_FROM_FROZEN_WALK | frozen decision-time walk covers the full stake for the leg |
| G_PIT_TIMING | frozen snapshot strictly pre-anchor AND the window is still open |
| G_EV_AT_LEAST_5_PERCENT | frozen EV_net(proposed) ≥ 0.05 (c = 0.02 baked into the frozen numbers) |
| G_FEES_ONCE_FROZEN | frozen numbers include the taker fee exactly once |
| G_STAKE_LAW_FROZEN | stake follows frozen v3 1%-equity law; a SWITCH never re-sizes |
| G_OPEN_CAP_AND_AVAILABILITY | exposure ≤ frozen cap AND ≤ availability |
| G_DRAWDOWN_NOT_PAUSED | drawdown < 10% and not paused |
| G_ONE_SELECTION_PER_MATCH | SWITCH replaces — still exactly one selection |

## 3. Absolute prohibitions

3.1 **The AI cannot turn a blocked / no-quote / not-run fixture into a
bet.** On any non-BET_PAPER fixture: SWITCH ⇒ REJECTED (G_NO_BET_CREATION);
KEEP ⇒ preserves the non-bet state; SKIP ⇒ lawful.
3.2 The evaluator reads numbers ONLY from the frozen ledger snapshot.
Every number inside the AI output carries ZERO authority (test:
fabricated-EV rejection).
3.3 No gate may be waived by model claims, confidence notes, mode, or any
setting. PASS is advisory evidence only.
3.4 After settlement, actions are historic ⇒ INVALID.

## 4. Frozen schema additions (opinion)

- `recommended_action`: "KEEP" | "SKIP" | "SWITCH" | null (outside ⇒ null
  + uncertainty note)
- `policyEvaluation`: { policy: "POLICY_FREEZE_AI_ACTIONS_V1",
  advisory_only: true, result: PASS | REJECTED | LAWFUL_SKIP |
  LAWFUL_KEEP | LAWFUL_KEEP_NO_BET | INVALID, gates[], failures[],
  evaluated_at_utc, fixture_match_id, fixture_status }

## 5. Frozen constants mirrors (display-law)

EV_THRESHOLD = 0.05 (c = 0.02 baked into frozen EV numbers) ·
DRAWDOWN_PAUSE_FRAC = 0.10 · anchor leads: SOCCER/WSL kickoff−6h,
NBA/WNBA T0−6h10m.

## 6. Implementation + tests

- Evaluator: `apps/paperdesk/main/paper_policy.js` (pure; never imported by
  any ledger path; the runner has no reference to it).
- Battery: `apps/paperdesk/test_paper_policy.js` — 24 adversarial cases:
  the all-gates control, each gate failed individually, the five
  blocked→bet refusals, KEEP/SKIP laws, fabricated-number rejection,
  enum rejection, ledger MatchView round-trip.
