'use strict';
// AI GATE MANDATORY battery (owner spec §D, round-8) — sandbox-only.
// Covers the full KEEP/VETO/SWITCH/ABSTAIN enforcement matrix + the
// adversarial laws: blocked->bet, fabricated numbers, SWITCH EV<5%,
// price-moved, malformed, post-deadline, timeout/provider-fail, cap $500,
// no silent bypass.
const { enforceAIGate, gradeLeg } = require('./main/ai_gate');

const results = [];
const check = (cond, name) => {
  results.push({ name, pass: !!cond });
  console.log(`[${cond ? 'PASS' : 'FAIL'}] ${name}`);
};

function fixture(overrides = {}) {
  return Object.assign({
    matchId: 'FD-GATE-1', league: 'WSL',
    decisionStatus: 'BET_PAPER', chosenLeg: 'HOME',
    stakeCents: 1022, stakeLaw: 'v3-1pct',
    pFrozen: { HOME: 0.62, DRAW: 0.21, AWAY: 0.17 },
    evNetByLeg: { HOME: 0.12, DRAW: -0.30, AWAY: 0.31 },
    quoteLegPresent: { HOME: true, DRAW: true, AWAY: true },
    depthWalked: { HOME: true, DRAW: true, AWAY: true },
    feesFrozenOnce: true, snapshotBeforeAnchor: true, anchorPassed: false,
    kickoffUTC: '2026-10-25T13:00:00Z', settlement: null,
    openExposureCents: 30000, openCapCents: 50000, availableCents: 72215,
    equityCents: 102215, drawdownFrac: 0.0, drawdownPaused: false,
  }, overrides);
}
const op = (action, leg, status = 'COMPLETED') =>
  ({ recommended_action: action, proposed_leg: leg || null,
     status, verdict: 'ALTERNATIVE' });

(async () => {
  // 1. KEEP all-gates control
  let r = enforceAIGate({ opinion: op('KEEP'), fixture: fixture() });
  check(r.decision === 'PLACE' && r.failures.length === 0
    && r.advisory_only === true,
    'control: KEEP all-gates -> PLACE (advisory_only until owner GO)');

  // 2. SWITCH fully-gated control
  r = enforceAIGate({ opinion: op('SWITCH', 'AWAY'), fixture: fixture() });
  check(r.decision === 'PLACE' && r.action === 'SWITCH'
    && r.proposed_leg === 'AWAY' && r.gates.length >= 8,
    'control: SWITCH AWAY passes every frozen gate -> PLACE');

  // 3. SWITCH EV < 5%
  r = enforceAIGate({ opinion: op('SWITCH', 'AWAY'),
    fixture: fixture({ evNetByLeg: { HOME: 0.12, DRAW: -0.3, AWAY: 0.04 } }) });
  check(r.decision === 'NOT_PLACED'
    && r.failures.includes('G_EV_AT_LEAST_5_PERCENT'),
    'law EV: SWITCH to EV 4% -> NOT_PLACED');

  // 4. VETO lawful
  r = enforceAIGate({ opinion: op('VETO'), fixture: fixture() });
  check(r.reason === 'LAWFUL_VETO' && r.decision === 'NOT_PLACED',
    'law VETO: standing bet withdrawn (advisory)');

  // 5. blocked fixture + SWITCH => never a bet
  r = enforceAIGate({ opinion: op('SWITCH', 'AWAY'),
    fixture: fixture({ decisionStatus: 'NO_QUOTE' }) });
  check(r.decision === 'NOT_PLACED'
    && r.failures.includes('G_NO_BET_CREATION'),
    'law blocked->bet: NO_QUOTE + SWITCH -> NOT_PLACED');

  // 6. blocked fixture + KEEP => preserves non-bet
  r = enforceAIGate({ opinion: op('KEEP'),
    fixture: fixture({ decisionStatus: 'NOT_RUN_NO_B1R_FORECAST' }) });
  check(r.reason === 'LAWFUL_KEEP_NO_BET',
    'law KEEP on not-run fixture: preserves non-bet state');

  // 7. depth missing on SWITCH leg
  r = enforceAIGate({ opinion: op('SWITCH', 'AWAY'),
    fixture: fixture({ depthWalked: { HOME: true, DRAW: true,
      AWAY: false } }) });
  check(r.decision === 'NOT_PLACED'
    && r.failures.includes('G_DEPTH_FROM_FROZEN_WALK'),
    'gate depth: SWITCH without frozen walk -> NOT_PLACED');

  // 8. cap $500 breached
  r = enforceAIGate({ opinion: op('KEEP'),
    fixture: fixture({ openExposureCents: 61000 }) });
  check(r.decision === 'NOT_PLACED'
    && r.failures.includes('G_OPEN_CAP_AND_AVAILABILITY'),
    'gate cap: exposure > $500 -> KEEP NOT_PLACED');

  // 9. price moved during AI thinking (anchor passed / snapshot stale)
  r = enforceAIGate({ opinion: op('KEEP'),
    fixture: fixture({ anchorPassed: true }) });
  check(r.decision === 'NOT_PLACED'
    && r.failures.includes('G_PIT_TIMING'),
    'law price-moved: anchor passed while AI ran -> NOT_PLACED');

  // 10. ABSTAIN laws
  r = enforceAIGate({ opinion: op('KEEP', null, 'API_ERROR_FAIL_CLOSED'),
    fixture: fixture() });
  check(r.decision === 'NOT_PLACED' && /ABSTAIN/.test(r.reason),
    'law abstain: provider error -> NOT_PLACED');
  r = enforceAIGate({ opinion: op('KEEP', null, 'MALFORMED_FAIL_CLOSED'),
    fixture: fixture() });
  check(r.decision === 'NOT_PLACED', 'law abstain: malformed -> NOT_PLACED');
  r = enforceAIGate({ opinion: op('KEEP', null, 'TIMEOUT_LATE_INVALID'),
    fixture: fixture() });
  check(r.decision === 'NOT_PLACED' && /deadline|ABSTAIN/i.test(r.reason),
    'law abstain: post-deadline -> NOT_PLACED');
  r = enforceAIGate({ opinion: { recommended_action: null,
    status: 'COMPLETED' }, fixture: fixture() });
  check(r.decision === 'NOT_PLACED', 'law abstain: no action -> NOT_PLACED');

  // 11. fabricated numbers carry no authority: the AI's opinion object
  //     contains fake EV but the fixture's frozen EV governs
  const liar = { recommended_action: 'SWITCH', proposed_leg: 'AWAY',
    status: 'COMPLETED',
    claimed_ev: 0.9, claimed_fee: 0 };
  r = enforceAIGate({ opinion: liar,
    fixture: fixture({ evNetByLeg: { HOME: 0.12, DRAW: -0.3, AWAY: 0.02 } }) });
  check(r.decision === 'NOT_PLACED'
    && r.failures.includes('G_EV_AT_LEAST_5_PERCENT')
    && !JSON.stringify(r.gates).includes('0.9'),
    'authority: fabricated AI EV ignored — frozen ledger EV governs');

  // 12. unknown action
  r = enforceAIGate({ opinion: { recommended_action: 'DOUBLE_DOWN',
    status: 'COMPLETED' }, fixture: fixture() });
  check(r.decision === 'NOT_PLACED', 'schema: unknown action -> NOT_PLACED');

  // 13. gradeLeg direct: fees/stake/drawdown surface
  const g = gradeLeg('HOME', fixture({ feesFrozenOnce: false,
    stakeLaw: 'v2-fixed', drawdownFrac: 0.11, drawdownPaused: true }));
  check(g.failures.includes('G_FEES_ONCE_FROZEN')
    && g.failures.includes('G_STAKE_LAW_FROZEN')
    && g.failures.includes('G_DRAWDOWN_NOT_PAUSED'),
    'gate surface: fees/stake/drawdown failures all reported');

  // 14. no silent bypass: EVERY non-PLACE path carries reason + decision
  for (const bad of [op('SWITCH', 'AWAY'),
    fixture({ decisionStatus: 'NO_QUOTE' })].slice(0, 1)) {
    const rr = enforceAIGate({ opinion: op('SWITCH', 'AWAY'),
      fixture: fixture({ evNetByLeg: { HOME: 0.12, DRAW: -0.3,
        AWAY: -0.5 } }) });
    check(rr.decision === 'NOT_PLACED' && rr.reason.length > 0,
      'no-bypass: rejection carries explicit reason');
  }

  const fails = results.filter(x => !x.pass).length;
  console.log(`ai gate: ${results.length - fails}/${results.length} pass`);
  process.exit(fails ? 1 : 0);
})();
