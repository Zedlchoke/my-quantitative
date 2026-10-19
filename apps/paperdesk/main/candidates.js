'use strict';
// AI auto-scheduler candidate builder — PURE function (unit-tested in
// test_ai_seam.js), extracted from main.js per owner audit round-3.
//
// CANONICAL ID LAW: a candidate's matchId MUST be the ledger/plan canonical
// match_id. Plan entries without match_id are SKIPPED (counted, with reason)
// — no synthetic league-home-away ids, so the (matchID, deadline) idempotence
// key in the AI sidecar can never split one fixture into two opinions.
// A fixture present in BOTH the ledger and the runner plan yields exactly ONE
// candidate (the ledger view wins — it carries ledger context), keyed by
// canonical match id.
//
// DEADLINE: when the runner plan supplies anchor_utc, it is AUTHORITATIVE
// (computed by the pinned runner from the same anchor laws) and is used
// directly; the league-heuristic deadlineFor is only a fallback for
// ledger-only candidates.
//
// webHints: intentionally EMPTY. A generic homepage is not fixture evidence;
// per-fixture URLs may only come from a lawful lawful source later. The
// allow-listed connector remains implemented and budget-capped.

function buildCandidates({ ledgerMatches = [], upcoming = [], now = Date.now() }) {
  const byId = new Map();
  const skipped = [];
  let fromLedgerCount = 0;
  let fromPlanCount = 0;

  for (const m of ledgerMatches || []) {
    if (m.decisionStatus) continue;                 // already decided
    if (!m.kickoffUTC || !(Date.parse(m.kickoffUTC) > now)) continue;
    if (!m.matchId) {
      skipped.push({ source: 'ledger', reason: 'missing match_id',
                     ref: m.home + ' vs ' + m.away });
      continue;
    }
    byId.set(m.matchId, {
      matchId: m.matchId, home: m.home, away: m.away,
      league: m.league, kickoffUTC: m.kickoffUTC,
      decisionStatus: null, decision: null,
      deadlineUTC: null,           // fallback: anchor-law heuristic in ai.js
      webHints: [],                // no homepage hints — not fixture evidence
      origin: 'ledger',
    });
    fromLedgerCount += 1;
  }

  for (const f of upcoming || []) {
    if (!f.kickoff_utc || !(Date.parse(f.kickoff_utc) > now)) continue;
    if (!f.match_id) {
      skipped.push({ source: 'plan', reason: 'missing match_id — skipped '
        + '(no synthetic ids)', ref: (f.home || '?') + ' vs '
        + (f.away || '?') });
      continue;
    }
    if (byId.has(f.match_id)) {
      // same fixture — enrich the ledger candidate with the runner's own
      // anchor (authoritative deadline), do NOT create a second candidate
      const c = byId.get(f.match_id);
      if (f.anchor_utc) c.deadlineUTC = f.anchor_utc;
      c.planAnchorUTC = f.anchor_utc || null;
      continue;
    }
    byId.set(f.match_id, {
      matchId: f.match_id, home: f.home || '?', away: f.away || '?',
      league: f.league || '?', kickoffUTC: f.kickoff_utc,
      decisionStatus: null, decision: null,
      deadlineUTC: f.anchor_utc || null,   // authoritative when present
      planAnchorUTC: f.anchor_utc || null,
      webHints: [],
      origin: 'plan',
    });
    fromPlanCount += 1;
  }

  return { candidates: [...byId.values()], skipped,
           fromLedgerCount, fromPlanCount };
}

module.exports = { buildCandidates };
