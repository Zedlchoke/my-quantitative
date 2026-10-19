'use strict';
// Read-only ledger projection with byte-exact chain verification.
// The ledger FILE is the only history authority; nothing is cached as truth.
// Any parse/tamper failure => chain failed => UI withholds all financials
// (mirrors the pinned build_state fail-closed behavior).
//
// Rows are parsed with the TYPED parser (int literals stay BigInt) so the
// canonical hash matches Python byte-for-byte; every value handed to the UI
// is converted down to Number via sanitizeBigInt (ledger amounts are small).
const fs = require('fs');
const { rowSha256, jsonParseTyped, sanitizeBigInt }
  = require('./canonical');

function ledgerPathFor(dataRoot, sandbox) {
  return sandbox
    ? `${dataRoot}/sandbox/sandbox_ledger.jsonl`
    : `${dataRoot}/ledger/paper_ledger.jsonl`;
}

function statusBucket(status) {
  if (!status) return 'OTHER';
  if (status === 'BET_PAPER') return 'BET';
  if (status.startsWith('NOT_')) return 'NOT_RUN';
  if (status.startsWith('BLOCKED')) return 'BLOCKED';
  if (status.startsWith('NO_QUOTE')) return 'NO_QUOTE';
  if (status.startsWith('NO_FORECAST')) return 'NO_FORECAST';
  if (status === 'NO_EDGE') return 'NO_EDGE';
  if (/^(PIT_|QUOTE_ANOMALY|CROSSWALK_MISS|RESOURCE_CONFLICT|STALE_PRICE)/
    .test(status)) return 'REFUSED';
  return 'OTHER';
}

function parseLedger(path) {
  const snap = {
    rows: [], chain: { ok: false, errors: [], verified_rows: 0 },
    genesis: null, isSandbox: false, matches: [], equity: [], wallet: null,
    parseError: null, mtime: 0, size: 0,
  };
  let stat;
  try { stat = fs.statSync(path); } catch (e) {
    snap.parseError = 'missing';
    return snap;
  }
  snap.mtime = stat.mtimeMs; snap.size = stat.size;
  let raw;
  try { raw = fs.readFileSync(path, 'utf8'); } catch (e) {
    snap.parseError = 'unreadable';
    return snap;
  }
  const lines = raw.split('\n').filter(l => l.trim().length);
  const rows = [];
  for (let i = 0; i < lines.length; i++) {
    try { rows.push(jsonParseTyped(lines[i])); } catch (e) {
      snap.parseError = `unparseable JSON at line ${i + 1}`;
      snap.chain.errors = [`line ${i + 1}: parse failure`];
      snap.rows = rows;
      return snap;
    }
  }
  snap.rows = rows;

  // chain verify: prev links + byte-exact row hash
  const errors = [];
  let prev = '0'.repeat(64);
  rows.forEach((row, i) => {
    const got = row.prev_row_sha256;
    if (got !== prev) errors.push(`row ${i}: prev_row_sha256 mismatch`);
    if (!row.row_sha256) errors.push(`row ${i}: missing row_sha256`);
    else if (row.row_sha256 !== rowSha256(row)) {
      errors.push(`row ${i}: row_sha256 mismatch (tampered?)`);
    }
    prev = row.row_sha256 || prev;
  });
  snap.chain = errors.length
    ? { ok: false, errors: errors.slice(0, 10), verified_rows: 0 }
    : { ok: true, errors: [], verified_rows: rows.length };

  snap.genesis = rows.find(r => r.type === 'GENESIS') || null;
  snap.isSandbox = !!(snap.genesis && snap.genesis.sandbox);
  if (!snap.chain.ok) return snap;        // withhold everything else

  // Projections run on Number-converted rows (hashing already done above on
  // the typed rows — BigInt math is not needed here and Math.* rejects it).
  const srows = sanitizeBigInt(rows);
  snap.matches = buildMatches(srows);
  snap.equity = buildEquity(srows);
  snap.wallet = buildWallet(srows, snap.matches);
  return snap;
}

function buildMatches(rows) {
  const order = [];
  const byMid = new Map();
  const ensure = id => {
    if (!byMid.has(id)) { byMid.set(id, {}); order.push(id); }
  };
  for (const row of rows) {
    const mid = row.match_id;
    if (!mid) continue;
    ensure(mid);
    const e = byMid.get(mid);
    if (row.type === 'DECISION') e.decision = row;
    else if (row.type === 'FORECAST') e.forecast = row;
    else if (row.type === 'MARKET_QUOTE') e.quote = row;
    else if (row.type === 'SETTLEMENT') e.settlement = row;
  }
  const out = order.map(mid => {
    const e = byMid.get(mid);
    const d = e.decision, f = e.forecast, q = e.quote, s = e.settlement;
    const any = d || f || q;
    const status = d ? d.status : null;
    return {
      matchId: mid,
      league: (d || f || q || any || {}).league || '?',
      competition: (d || f || {}).competition || '',
      home: (d || f || {}).home || '?',
      away: (d || f || {}).away || '?',
      kickoffUTC: (d || f || q || {}).kickoff_utc || null,
      decision: d || null, forecast: f || null, quote: q || null,
      settlement: s || null,
      decisionStatus: status,
      bucket: statusBucket(status),
      chosenLeg: d ? d.chosen_leg : null,
      stakeCents: d ? (d.stake_cents || 0) : 0,
      pnlCents: s ? (s.pnl_cents || 0) : null,
      outcomeForLeg: s ? s.outcome_for_leg : null,
      isOpen: status === 'BET_PAPER' && !s,
      decidedAtUTC: d ? d.decided_at_utc : null,
    };
  });
  out.sort((a, b) => {
    const ad = a.decidedAtUTC || '', bd = b.decidedAtUTC || '';
    if (ad !== bd) return ad < bd ? 1 : -1;
    return (b.kickoffUTC || '').localeCompare(a.kickoffUTC || '');
  });
  return out;
}

function buildEquity(rows) {
  const pts = [];
  rows.forEach((row, seq) => {
    if (row.type === 'GENESIS' && row.wallet_cents != null) {
      pts.push({ seq, t: row.at_utc || '', equityCents: row.wallet_cents,
                 label: 'GENESIS', pnlCents: null });
    } else if (row.type === 'SETTLEMENT' && row.equity_after_cents != null) {
      pts.push({ seq, t: row.settled_at_utc || row.kickoff_utc || '',
                 equityCents: row.equity_after_cents,
                 label: row.match_id || '?', pnlCents: row.pnl_cents || 0 });
    }
  });
  return pts;
}

function buildWallet(rows, matches) {
  const g = rows.find(r => r.type === 'GENESIS');
  const w = {
    equityCents: g ? (g.wallet_cents || 0) : 0,
    peakCents: g ? (g.wallet_cents || 0) : 0,
    drawdownFrac: 0, pausedByDrawdown: false,
    openExposureCents: 0, openCapCents: 10000,
    capitalLaw: 'v2 fixed $5 stake; cap $100',
    openCount: 0, settledCount: 0, totalPnLCents: 0,
    pnlBySport: {}, outcomes: {},
  };
  for (const row of rows) {
    if (row.type !== 'SETTLEMENT') continue;
    if (row.equity_after_cents != null) {
      w.equityCents = row.equity_after_cents;
      w.peakCents = Math.max(w.peakCents, row.equity_after_cents);
    }
    if (row.drawdown_frac_after != null) w.drawdownFrac = row.drawdown_frac_after;
    const lg = row.league || '?';
    w.pnlBySport[lg] = (w.pnlBySport[lg] || 0) + (row.pnl_cents || 0);
    const oc = row.outcome_for_leg || '?';
    w.outcomes[oc] = (w.outcomes[oc] || 0) + 1;
    w.settledCount += 1;
  }
  w.totalPnLCents = Object.values(w.pnlBySport).reduce((a, b) => a + b, 0);
  w.pausedByDrawdown = w.drawdownFrac >= 0.10;
  if (rows.some(r => r.stake_law === 'v3-1pct')) {
    w.openCapCents = 50000;
    w.capitalLaw =
      'v3-1pct (stake 1% equity half-up; cap $500 + availability)';
  }
  w.openCount = matches.filter(m => m.isOpen).length;
  w.openExposureCents = matches.filter(m => m.isOpen)
    .reduce((a, m) => a + m.stakeCents, 0);
  return w;
}

module.exports = { parseLedger, ledgerPathFor, statusBucket };
