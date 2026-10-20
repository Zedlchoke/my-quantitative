'use strict';
// POLICY_FREEZE_AI_ACTIONS_V1 adversarial battery — sandbox-only, offline.
// Proves the advisory evaluator: a SWITCH must pass EVERY frozen gate; the
// AI cannot turn blocked/no-quote into a bet; SKIP/KEEP laws; and that only
// FROZEN LEDGER numbers carry authority (fabricated AI numbers are ignored).
const path = require('path');
const { evaluateAIPaperAction, snapshotFromMatchView }
  = require('./main/paper_policy');

const results = [];
const check = (cond, name) => {
  results.push({ name, pass: !!cond });
  console.log(`[${cond ? 'PASS' : 'FAIL'}] ${name}`);
};

// A frozen fixture where a SWITCH TO AWAY passes every gate.
function validFixture(overrides = {}) {
  return Object.assign({
    matchId: 'FD-TEST-1', league: 'WSL',
    decisionStatus: 'BET_PAPER',
    chosenLeg: 'HOME',
    stakeCents: 1022,
    stakeLaw: 'v3-1pct',
    pFrozen: { HOME: 0.62, DRAW: 0.21, AWAY: 0.17 },
    evNetByLeg: { HOME: 0.12, DRAW: -0.30, AWAY: 0.31 },
    quoteLegPresent: { HOME: true, DRAW: true, AWAY: true },
    depthWalked: { HOME: true, DRAW: true, AWAY: true },
    feesFrozenOnce: true,
    snapshotBeforeAnchor: true,
    anchorPassed: false,
    kickoffUTC: '2026-10-25T13:00:00Z',
    settlement: null,
    openExposureCents: 30000,
    openCapCents: 50000,
    availableCents: 72215,
    equityCents: 102215,
    drawdownFrac: 0.0,
    drawdownPaused: false,
  }, overrides);
}
const opinion = { recommended_action: 'SWITCH', proposed_leg: 'AWAY',
  verdict: 'ALTERNATIVE' };

(async () => {
  // 1. the all-gates-pass control
  let r = evaluateAIPaperAction({ opinion, fixture: validFixture() });
  check(r.result === 'PASS' && r.failures.length === 0
    && r.advisory_only === true
    && r.gates.length >= 9
    && r.gates.every(g => g.pass),
    'control: fully-gated SWITCH -> PASS with every gate green');
  check(/needs a registered AI authority \+ owner GO/.test(r.note),
    'control: PASS note states authority + owner GO requirement');

  // 2..8 — each gate individually failed
  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ evNetByLeg: { HOME: 0.12, DRAW: -0.30,
      AWAY: 0.04 } }) });
  check(r.result === 'REJECTED'
    && r.failures.includes('G_EV_AT_LEAST_5_PERCENT'),
    'gate EV: frozen EV_net 0.04 < 5% -> REJECTED');

  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ depthWalked: { HOME: true, DRAW: true,
      AWAY: false } }) });
  check(r.failures.includes('G_DEPTH_FROM_FROZEN_WALK'),
    'gate depth: frozen walk missing for AWAY -> REJECTED');

  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ quoteLegPresent: { HOME: true, DRAW: true,
      AWAY: false } }) });
  check(r.failures.includes('G_QUOTE_PRESENT'),
    'gate quote: no frozen pre-anchor quote for AWAY -> REJECTED');

  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ snapshotBeforeAnchor: false }) });
  check(r.failures.includes('G_PIT_TIMING'),
    'gate timing: snapshot not strictly pre-anchor -> REJECTED');

  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ stakeLaw: 'v2-fixed' }) });
  check(r.failures.includes('G_STAKE_LAW_FROZEN'),
    'gate stake: frozen law not v3-1pct -> REJECTED');

  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ drawdownFrac: 0.12, drawdownPaused: true }) });
  check(r.failures.includes('G_DRAWDOWN_NOT_PAUSED'),
    'gate drawdown: 12% breach + paused -> REJECTED');

  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ openExposureCents: 61000 }) });
  check(r.failures.includes('G_OPEN_CAP_AND_AVAILABILITY'),
    'gate cap: exposure over the frozen cap -> REJECTED');

  r = evaluateAIPaperAction({ opinion,
    fixture: validFixture({ feesFrozenOnce: false }) });
  check(r.failures.includes('G_FEES_ONCE_FROZEN'),
    'gate fees: fee-not-frozen-once -> REJECTED');

  // 9. SWITCH to the standing leg is a KEEP, not a SWITCH
  r = evaluateAIPaperAction({ opinion:
    { recommended_action: 'SWITCH', proposed_leg: 'HOME' },
    fixture: validFixture() });
  check(r.result === 'REJECTED'
    && r.failures.includes('G_NOT_SAME_LEG'),
    'gate selection: SWITCH to the standing leg -> rejected (it is a KEEP)');

  // 10. SWITCH to an unquoted leg
  r = evaluateAIPaperAction({ opinion:
    { recommended_action: 'SWITCH', proposed_leg: 'DRAW' },
    fixture: validFixture({ quoteLegPresent: { HOME: true, DRAW: false,
      AWAY: true }, depthWalked: { HOME: true, DRAW: false, AWAY: true } }),
    });
  check(r.failures.includes('G_PROPOSED_LEG_VALID')
    || r.failures.includes('G_QUOTE_PRESENT'),
    'gate selection: unquoted proposed leg -> REJECTED');

  // 11./12. THE LAW: AI cannot turn blocked / no-quote into a bet
  for (const status of ['NO_EDGE', 'NO_QUOTE', 'NOT_RUN_NO_B1R_FORECAST',
                        'BLOCKED_NO_GO', 'NOT_RUN_NO_MARKET']) {
    r = evaluateAIPaperAction({ opinion,
      fixture: validFixture({ decisionStatus: status }) });
    check(r.result === 'REJECTED'
      && r.failures.includes('G_NO_BET_CREATION'),
      `law blocked->bet: ${status} + SWITCH -> REJECTED (G_NO_BET_CREATION)`);
  }

  // 13./14. KEEP / SKIP laws
  r = evaluateAIPaperAction({ opinion:
    { recommended_action: 'KEEP' }, fixture: validFixture() });
  check(r.result === 'LAWFUL_KEEP',
    'law KEEP: standing decision preserved');
  r = evaluateAIPaperAction({ opinion:
    { recommended_action: 'SKIP' }, fixture: validFixture() });
  check(r.result === 'LAWFUL_SKIP'
    && /already has a paper bet/.test(r.gates[0].detail),
    'law SKIP on an open bet: lawful advisory, bet stays per ledger law');
  r = evaluateAIPaperAction({ opinion: { recommended_action: 'SKIP' },
    fixture: validFixture({ decisionStatus: 'NO_QUOTE' }) });
  check(r.result === 'LAWFUL_SKIP',
    'law SKIP on a no-quote fixture: lawful (staying out)');

  r = evaluateAIPaperAction({ opinion:
    { recommended_action: 'KEEP' },
    fixture: validFixture({ decisionStatus: 'BLOCKED_NO_GO' }) });
  check(r.result === 'LAWFUL_KEEP_NO_BET',
    'law KEEP on a blocked fixture: preserves non-bet state');

  // 15. FABRICATED NUMBERS: the model claims EV 0.90 — the frozen ledger
  //     snapshot says 0.01. Only the ledger number is graded.
  const liar = { recommended_action: 'SWITCH', proposed_leg: 'AWAY',
    verdict: 'ALTERNATIVE',
    rationale: 'I computed EV_net = 0.90 for AWAY with zero fees',
    claimed_numbers: { ev_net_away: 0.90, fees: 0 } };
  r = evaluateAIPaperAction({ opinion: liar,
    fixture: validFixture({ evNetByLeg: { HOME: 0.12, DRAW: -0.30,
      AWAY: 0.01 } }) });
  check(r.result === 'REJECTED'
    && r.failures.includes('G_EV_AT_LEAST_5_PERCENT')
    && !JSON.stringify(r.gates).includes('0.90'),
    'authority: fabricated AI EV ignored — frozen ledger EV governs');

  // 15b. post-settlement: INVALID for EVERY action (reachable branch —
  //      A7 delta-5 F-1)
  for (const action of ['SWITCH', 'KEEP', 'SKIP']) {
    r = evaluateAIPaperAction({
      opinion: action === 'SWITCH'
        ? { recommended_action: 'SWITCH', proposed_leg: 'AWAY' }
        : { recommended_action: action },
      fixture: validFixture({ settlement: { pnl_cents: 300 },
        outcomeForLeg: 'WIN' }) });
    check(r.result === 'INVALID'
      && r.failures[0]?.includes('already settled'),
      `law post-settlement: ${action} on a settled fixture -> INVALID`);
  }

  // 16. invalid action enum
  r = evaluateAIPaperAction({ opinion:
    { recommended_action: 'DOUBLE_DOWN' }, fixture: validFixture() });
  check(r.result === 'INVALID',
    'schema: action outside KEEP/SKIP/SWITCH -> INVALID');

  // 17. snapshot builder integrity: ledger MatchView -> snapshot carries
  //     the frozen numbers the evaluator grades (round-trip proof)
  const mv = {
    matchId: 'FD-2026-M50', league: 'WSL', decisionStatus: 'BET_PAPER',
    chosenLeg: 'HOME', stakeCents: 1022,
    decision: { stake_law: 'v3-1pct', p_frozen: { HOME: 0.8, DRAW: 0.1,
      AWAY: 0.1 }, ev_net_by_leg: { HOME: 0.2, DRAW: -0.2, AWAY: -0.1 } },
    quote: { odds: { HOME: 1.3, DRAW: 5.5, AWAY: 9.0 },
             fetch_ts_utc: '2026-10-24T06:00:00Z' },
    kickoffUTC: '2026-10-25T13:00:00Z', settlement: null,
  };
  const snap = snapshotFromMatchView(mv, { openExposureCents: 1022,
    openCapCents: 50000, equityCents: 102215, drawdownFrac: 0.0 });
  const rt = evaluateAIPaperAction({ opinion: { recommended_action:
    'SWITCH', proposed_leg: 'AWAY' }, fixture: snap });
  check(snap.stakeLaw === 'v3-1pct'
    && snap.quoteLegPresent.AWAY === true
    && rt.failures.includes('G_EV_AT_LEAST_5_PERCENT'),
    'snapshot: real MatchView round-trip -> frozen EV governs (AWAY -0.1 '
    + 'rejected)');

  const fails = results.filter(x => !x.pass).length;
  console.log(`paper policy: ${results.length - fails}/${results.length} `
    + 'pass');
  process.exit(fails ? 1 : 0);
})();
