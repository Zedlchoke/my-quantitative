'use strict';
// MANDATORY AI GATE — sandbox enforcement for the pre-BET_PAPER decision
// (owner target architecture; AI authority NOT REGISTERED — this module is
// the READY machinery that a future owner GO promotes from advisory to
// authoritative. Until then it runs ONLY in sandbox/tests and in the
// PaperDesk SHADOW display).
//
// LAWS (owner spec 2026-10-20 §D):
//  * exactly one action per opinion: KEEP | VETO | SWITCH (ABSTAIN from
//    the model or any failure => decision NOT placed);
//  * the model NEVER supplies numbers: probabilities, EV, fees, stake,
//    cap, thresholds come ONLY from the frozen snapshot;
//  * SWITCH(leg) must re-pass EVERY frozen gate as a NEW bet on the same
//    fixture: model p already recorded pre-anchor, same valid market,
//    EV_net >= 5%, depth, timing, stake, cap, drawdown;
//  * no valid fully-gated candidate => VETO / NOT_RUN (never a bet);
//  * timeout / provider error / malformed JSON / missing evidence /
//    post-deadline / price-moved => ABSTAIN => NOT placed (no silent
//    bypass path exists);
//  * blocked / no-quote / not-run fixtures: every action => NOT placed
//    (G_NO_BET_CREATION carried from POLICY_FREEZE_AI_ACTIONS_V1).

const LAWS = require('./laws_generated');   // W1.6: ONE constant source
const EV_THRESHOLD = LAWS.EV_THRESHOLD;

function gate(name, pass, detail) {
  return { gate: name, pass: !!pass, detail: detail || '' };
}

/// Fully-gate a candidate leg (KEEP leg or SWITCH leg) against the frozen
/// snapshot. Returns {ok, gates, failures}.
function gradeLeg(leg, f, { requireDepth = true } = {}) {
  const gates = [];
  const failures = [];
  const push = (name, pass, detail) => {
    gates.push(gate(name, pass, detail));
    if (!pass) failures.push(name);
    return pass;
  };
  const ev = (f.evNetByLeg || {})[leg];
  push('G_QUOTE_PRESENT', !!(f.quoteLegPresent || {})[leg],
    'frozen pre-anchor quote for ' + leg);
  if (requireDepth) {
    push('G_DEPTH_FROM_FROZEN_WALK', !!(f.depthWalked || {})[leg],
      'frozen decision-time walk covers the full stake for ' + leg);
  }
  push('G_EV_AT_LEAST_5_PERCENT',
    typeof ev === 'number' && ev >= EV_THRESHOLD,
    'frozen EV_net(' + leg + ') = ' + (typeof ev === 'number'
      ? ev.toFixed(6) : 'n/a') + ' (>= 0.05, c = 0.02 baked in)');
  push('G_PIT_TIMING', f.snapshotBeforeAnchor === true
    && f.anchorPassed !== true,
    'frozen snapshot strictly pre-anchor; window open');
  push('G_FEES_ONCE_FROZEN', f.feesFrozenOnce === true,
    'taker fee included exactly once in the frozen numbers');
  push('G_STAKE_LAW_FROZEN', f.stakeLaw === 'v3-1pct'
    && (f.stakeCents ?? 0) > 0,
    'v3 1%-equity stake (' + (f.stakeCents ?? '?') + 'c)');
  const exposure = f.openExposureCents ?? 0;
  push('G_OPEN_CAP_AND_AVAILABILITY',
    exposure <= (f.openCapCents ?? 0)
    && exposure <= (f.availableCents ?? (f.openCapCents ?? 0)),
    'exposure ' + exposure + 'c vs cap ' + (f.openCapCents ?? '?')
      + 'c / availability');
  push('G_DRAWDOWN_NOT_PAUSED',
    (f.drawdownFrac ?? 0) < 0.10 && f.drawdownPaused !== true,
    'drawdown ' + (typeof f.drawdownFrac === 'number'
      ? (f.drawdownFrac * 100).toFixed(2) + '%' : '?') + ' < 10%');
  return { ok: failures.length === 0, gates, failures };
}

/// THE GATE. op: model opinion {recommended_action, proposed_leg,
/// status, verdict}. f: frozen snapshot (ledger numbers only).
/// Returns the enforcement record that a future authoritative runner
/// would consult: {decision: 'PLACE'|'NOT_PLACED', action, reason,
/// gates, failures}.
function enforceAIGate({ opinion, fixture }) {
  const o = opinion || {};
  const f = fixture || {};
  const action = o.recommended_action || null;
  const base = {
    gate_version: 'AI_GATE_MANDATORY_V1',
    advisory_only: true,          // flips to false ONLY by owner GO
    action: action || null,
    proposed_leg: o.proposed_leg || null,
    fixture_match_id: f.matchId || null,
    fixture_status: f.decisionStatus || null,
    gates: [], failures: [],
    decision: 'NOT_PLACED', reason: '',
  };

  // 0. model-side failure laws => ABSTAIN => NOT placed
  if (o.status && o.status !== 'COMPLETED') {
    return { ...base, reason: 'model opinion not COMPLETED (' + o.status
      + ') — ABSTAIN => NOT placed' };
  }
  if (!action) {
    return { ...base, reason: 'no action expressed — ABSTAIN => NOT '
      + 'placed' };
  }

  // 1. blocked/no-quote/not-run can NEVER become a bet
  const isOpenBet = f.decisionStatus === 'BET_PAPER';
  if (!isOpenBet) {
    if (action === 'SWITCH') {
      const g = gate('G_NO_BET_CREATION', false,
        'fixture status ' + (f.decisionStatus || 'none') + ' — the AI '
        + 'cannot turn a blocked/no-quote fixture into a bet');
      return { ...base, gates: [g], failures: ['G_NO_BET_CREATION'],
        reason: 'REJECTED: ' + g.detail };
    }
    if (action === 'KEEP') {
      return { ...base, gates: [gate('G_NO_BET_CREATION', true,
        'KEEP preserves the current non-bet state')], reason:
        'LAWFUL_KEEP_NO_BET' };
    }
    // SKIP on non-bet: lawful (staying out)
    return { ...base, gates: [gate('G_STAYS_OUT', true,
      'fixture has no bet — SKIP matches the ledger state')],
      reason: 'LAWFUL_SKIP' };
  }

  // 2. open bet: KEEP / VETO / SWITCH
  if (action === 'KEEP') {
    const g = gradeLeg(f.chosenLeg || 'HOME', f);
    return { ...base, gates: g.gates, failures: g.failures,
      decision: g.ok ? 'PLACE' : 'NOT_PLACED',
      reason: g.ok ? 'KEEP passes every frozen gate on '
        + (f.chosenLeg || '?')
        : 'KEEP leg fails frozen gates: ' + g.failures.join(', ')
          + ' — NOT placed (re-evaluation, never grandfathered)' };
  }
  if (action === 'VETO') {
    return { ...base, gates: [gate('G_VETO_LAWFUL', true,
      'VETO withdraws the standing paper bet — advisory until owner GO')],
      reason: 'LAWFUL_VETO' };
  }
  if (action === 'SWITCH') {
    const proposed = o.proposed_leg;
    if (!proposed || proposed === f.chosenLeg) {
      const g = gate('G_SWITCH_TARGET', false,
        'proposed_leg missing/equal to standing leg');
      return { ...base, gates: [g], failures: ['G_SWITCH_TARGET'],
        reason: 'REJECTED: ' + g.detail };
    }
    const legs = Object.keys(f.pFrozen || {});
    if (!legs.includes(proposed)) {
      const g = gate('G_SWITCH_TARGET', false,
        'proposed leg not quoted on this fixture (have: '
        + legs.join('/') + ')');
      return { ...base, gates: [g], failures: ['G_SWITCH_TARGET'],
        reason: 'REJECTED: ' + g.detail };
    }
    const graded = gradeLeg(proposed, f);
    return { ...base, gates: graded.gates, failures: graded.failures,
      decision: graded.ok ? 'PLACE' : 'NOT_PLACED',
      reason: graded.ok
        ? 'SWITCH -> ' + proposed + ' passes every frozen gate as a new '
          + 'bet (model p already recorded pre-anchor on the same market)'
        : 'SWITCH -> ' + proposed + ' fails: ' + graded.failures.join(', ')
          + ' — NOT placed; no fully-gated candidate => VETO/NOT_RUN' };
  }
  return { ...base, reason: 'unknown action — NOT placed' };
}

module.exports = { enforceAIGate, gradeLeg, EV_THRESHOLD };
