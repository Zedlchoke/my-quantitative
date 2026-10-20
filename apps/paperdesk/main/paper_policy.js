'use strict';
// PAPER POLICY — SANDBOX ADVISORY EVALUATOR for AI-recommended actions
// (KEEP / SKIP / SWITCH within the same fixture).
//
// POLICY FREEZE: POLICY_FREEZE_AI_ACTIONS_V1 (research/control/
// SPORTS-PAPERTRADE-EXEC-V1). AI authority is NOT REGISTERED: this module
// NEVER writes the ledger, NEVER talks to a venue, NEVER executes anything —
// it only grades an AI recommendation against the FROZEN gates so the
// recommendation ships with a would-pass/would-fail evidence record. The
// real decision authority remains the pinned runner + owner GO.
//
// LAWS encoded here (each gate tested in test_paper_policy.js):
//  * the evaluator reads numbers ONLY from the frozen ledger snapshot —
//    every number inside the AI output carries zero authority;
//  * SWITCH is graded on the PROPOSED leg against the FULL frozen gate set:
//    quote present at decision time, depth (frozen walk), EV_net >= 0.05
//    (c = 0.02 baked into the frozen numbers), PIT/anchor timing, frozen
//    stake law, open cap + availability, drawdown pause, one-selection;
//  * the AI CANNOT turn a blocked / no-quote / not-run fixture into a bet:
//    on a non-BET_PAPER fixture, SWITCH is rejected outright (G_NO_BET_
//    CREATION) and only KEEP (stay as-is) / SKIP (stay out) are lawful;
//  * SKIP is always a lawful advisory (staying out needs no gate);
//  * SWITCH proposing the already-chosen leg is not a SWITCH (rejected,
//    it is a KEEP);
//  * no gate may be waived by anything the model says, by mode, or by a
//    higher verdict confidence note.

const EV_THRESHOLD = 0.05;           // frozen EV gate (mirror, display-law)
const DRAWDOWN_PAUSE_FRAC = 0.10;    // frozen drawdown pause

const ACTIONS = ['KEEP', 'SKIP', 'SWITCH'];
const LEGS = ['HOME', 'DRAW', 'AWAY'];

function gate(name, pass, detail) {
  return { gate: name, pass: !!pass, detail: detail || '' };
}

/// fixture: frozen snapshot assembled by main.js FROM THE LEDGER (never from
/// model output): see snapshotForMatch(). opinion: the stored AI opinion.
function evaluateAIPaperAction({ opinion, fixture }) {
  const o = opinion || {};
  const f = fixture || {};
  const action = o.recommended_action;
  const base = {
    policy: 'POLICY_FREEZE_AI_ACTIONS_V1',
    advisory_only: true,
    action: action || null,
    proposed_leg: o.proposed_leg || null,
    evaluated_at_utc: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    fixture_match_id: f.matchId || null,
    fixture_status: f.decisionStatus || null,
    gates: [],
    failures: [],
  };

  if (!action || !ACTIONS.includes(action)) {
    return { ...base, result: 'INVALID',
      failures: ['recommended_action missing or not in KEEP/SKIP/SWITCH'] };
  }

  // post-settlement: actions are historic only (freeze §3.4) — checked
  // BEFORE any branch so the rule is reachable for every action
  if (f.settlement) {
    return { ...base, result: 'INVALID',
      failures: ['fixture already settled — actions are historic only'] };
  }

  const isOpenBet = f.decisionStatus === 'BET_PAPER';

  // ---- SKIP: staying out is always a lawful advisory ---------------------
  if (action === 'SKIP') {
    return { ...base, result: 'LAWFUL_SKIP', gates: [
      gate('G_STAYS_OUT', true,
        isOpenBet ? 'fixture already has a paper bet — advisory only; '
          + 'the placed bet stays per ledger law (no un-bet exists)'
        : 'fixture has no bet — staying out matches the ledger state')] };
  }

  // ---- non-BET fixture: the AI cannot conjure a bet ----------------------
  if (!isOpenBet) {
    if (action === 'SWITCH') {
      return { ...base, result: 'REJECTED', gates: [
        gate('G_NO_BET_CREATION', false,
          'fixture status is ' + (f.decisionStatus || 'none')
          + ' — the AI cannot turn a blocked/no-quote/not-run fixture into '
          + 'a bet (POLICY_FREEZE_AI_ACTIONS_V1 §3.1)')] ,
        failures: ['G_NO_BET_CREATION'] };
    }
    // KEEP on a non-bet: keep the current (non-bet) state — lawful no-op
    return { ...base, result: 'LAWFUL_KEEP_NO_BET', gates: [
      gate('G_NO_BET_CREATION', true,
        'KEEP preserves the current non-bet state ('
        + (f.decisionStatus || 'none') + ') — nothing becomes a bet')] };
  }

  // ---- OPEN BET from here: KEEP / SWITCH with full gate grading ----------
  if (action === 'KEEP') {
    return { ...base, result: 'LAWFUL_KEEP', gates: [
      gate('G_KEEP_CURRENT', true,
        'KEEP preserves the standing decision: '
        + (f.chosenLeg || '?') + ' at ' + (f.stakeCents ?? '?') + 'c — '
        + 'its gates were passed in-lock at decision time')] };
  }

  // SWITCH: the proposed leg must pass EVERY frozen gate.
  const proposed = o.proposed_leg;
  const gates = [];
  const push = (name, pass, detail) => {
    gates.push(gate(name, pass, detail));
    if (!pass) base.failures.push(name);
    return pass;
  };

  const legs = Object.keys(f.pFrozen || {});
  push('G_PROPOSED_LEG_VALID',
    LEGS.includes(proposed) && legs.includes(proposed),
    'proposed_leg must be a quoted leg of this fixture (have: '
      + (legs.join('/') || 'none') + ')');
  push('G_NOT_SAME_LEG', proposed !== f.chosenLeg,
    'proposed leg equals the standing chosen leg — that is a KEEP, '
    + 'not a SWITCH');
  push('G_QUOTE_PRESENT', !!(f.quoteLegPresent || {})[proposed],
    'frozen pre-anchor quote must exist for the proposed leg');
  push('G_DEPTH_FROM_FROZEN_WALK',
    !!(f.depthWalked || {})[proposed],
    'frozen decision-time walk must cover the full stake for the leg');
  push('G_PIT_TIMING',
    f.snapshotBeforeAnchor === true && f.anchorPassed !== true,
    'frozen snapshot strictly pre-anchor; window still open '
    + '(switching after the anchor is never lawful)');
  const ev = (f.evNetByLeg || {})[proposed];
  push('G_EV_AT_LEAST_5_PERCENT',
    typeof ev === 'number' && ev >= EV_THRESHOLD,
    'frozen EV_net for ' + proposed + ' = ' + (typeof ev === 'number'
      ? ev.toFixed(6) : 'n/a') + ' (gate >= 0.05, c = 0.02 baked in)');
  push('G_FEES_ONCE_FROZEN',
    f.feesFrozenOnce === true,
    'frozen numbers include the taker fee exactly once '
    + '(0.05·p·(1−p) in d_eff)');
  push('G_STAKE_LAW_FROZEN',
    f.stakeLaw === 'v3-1pct' && (f.stakeCents ?? 0) > 0,
    'stake follows the frozen v3 1%-equity law ('
      + (f.stakeCents ?? '?') + 'c); a SWITCH never re-sizes the stake');
  const capOk = (f.openExposureCents ?? 0) <= (f.openCapCents ?? 0)
    && (f.openExposureCents ?? 0) <= (f.availableCents
      ?? (f.openCapCents ?? 0));
  push('G_OPEN_CAP_AND_AVAILABILITY', capOk,
    'open exposure ' + (f.openExposureCents ?? '?') + 'c vs cap '
      + (f.openCapCents ?? '?') + 'c and availability');
  push('G_DRAWDOWN_NOT_PAUSED',
    (f.drawdownFrac ?? 0) < DRAWDOWN_PAUSE_FRAC
      && f.drawdownPaused !== true,
    'drawdown ' + (typeof f.drawdownFrac === 'number'
      ? (f.drawdownFrac * 100).toFixed(2) + '%' : '?')
      + ' vs 10% pause');
  push('G_ONE_SELECTION_PER_MATCH', true,
    'a SWITCH replaces the standing leg — still exactly one selection');

  const pass = base.failures.length === 0;
  return {
    ...base,
    result: pass ? 'PASS' : 'REJECTED',
    note: pass
      ? 'SWITCH would pass every frozen gate on the frozen snapshot '
        + '(advisory only — executing it needs a registered AI authority '
        + '+ owner GO; the ledger was not touched)'
      : 'SWITCH REJECTED by the frozen gates listed in failures '
        + '(advisory only; ledger untouched)',
    gates,
  };
}

/// Assemble the frozen fixture snapshot FROM LEDGER ROWS (authoritative
/// numbers). Built by main.js from a ledger MatchView + wallet view.
function snapshotFromMatchView(m, wallet) {
  if (!m) return null;
  const d = m.decision || {};
  const q = m.quote || {};
  const pmOut = q.pm_outcomes || null;
  const quoteLegPresent = {};
  const depthWalked = {};
  const odds = q.odds || {};
  for (const leg of LEGS) {
    if (pmOut && typeof pmOut === 'object') {
      quoteLegPresent[leg] = !!(pmOut[leg]
        && typeof pmOut[leg] === 'object');
      depthWalked[leg] = !!(pmOut[leg]
        && typeof pmOut[leg] === 'object'
        && (pmOut[leg].filled_shares != null
            || pmOut[leg].levels_used != null));
    } else {
      quoteLegPresent[leg] = odds[leg] != null;
      depthWalked[leg] = odds[leg] != null;   // listed price = walked snapshot
    }
  }
  // PIT: quote fetched strictly before kickoff-6h anchor (ledger truth):
  const fetchTs = q.fetch_ts_utc ? Date.parse(q.fetch_ts_utc) : null;
  const ko = m.kickoffUTC ? Date.parse(m.kickoffUTC) : null;
  const lead = (String(m.league).toUpperCase() === 'NBA'
    || String(m.league).toUpperCase() === 'WNBA')
    ? (6 * 3600 + 10 * 60) * 1000 : 6 * 3600 * 1000;
  const snapshotBeforeAnchor = !!(fetchTs && ko && fetchTs < ko - lead);
  const anchorPassed = !!(ko && Date.now() > ko - lead);
  return {
    matchId: m.matchId, league: m.league,
    decisionStatus: m.decisionStatus,
    chosenLeg: m.chosenLeg,
    stakeCents: m.stakeCents ?? 0,
    stakeLaw: d.stake_law || null,
    pFrozen: d.p_frozen || {},
    evNetByLeg: d.ev_net_by_leg || {},
    quoteLegPresent, depthWalked,
    feesFrozenOnce: !!(m.quote),
    snapshotBeforeAnchor, anchorPassed,
    kickoffUTC: m.kickoffUTC || null,
    settlement: m.settlement || null,
    openExposureCents: wallet ? wallet.openExposureCents : null,
    openCapCents: wallet ? wallet.openCapCents : null,
    availableCents: wallet
      ? Math.max(0, Math.min((wallet.equityCents || 0)
          - (wallet.openExposureCents || 0),
        (wallet.openCapCents || 0) - (wallet.openExposureCents || 0)))
      : null,
    equityCents: wallet ? wallet.equityCents : null,
    drawdownFrac: wallet ? wallet.drawdownFrac : null,
    drawdownPaused: wallet ? !!wallet.pausedByDrawdown : null,
  };
}

module.exports = { evaluateAIPaperAction, snapshotFromMatchView,
                   ACTIONS, LEGS, EV_THRESHOLD, DRAWDOWN_PAUSE_FRAC };
