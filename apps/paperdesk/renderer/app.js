'use strict';
// Renderer app: sidebar navigation + all views. Pure views — every number
// comes from the main process state broadcast (ledger file + /api/state),
// with explicit loading / empty / offline / error / tamper states.
const SECTIONS = [
  ['dashboard', 'Dashboard', '▤'],
  ['matches', 'Matches', '☰'],
  ['opportunities', 'Opportunities', '⏱'],
  ['health', 'System Health', '❤'],
  ['ai', 'AI Review (SHADOW)', '✦'],
  ['laws', 'Laws & Docs', '✔'],
];
let S = null;                 // latest state from main
let section = 'dashboard';
let selectedMatchId = null;
let filters = { status: 'all', league: 'All', q: '' };
let oppTab = 0;
let currentPolicy = 'ask';

const $ = sel => document.querySelector(sel);
const esc = s => String(s ?? '—').replace(/[&<>"]/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function money(cents, sign = true) {
  const d = Math.abs(cents || 0) / 100;
  const s = d.toLocaleString('en-US', { minimumFractionDigits: 2,
                                        maximumFractionDigits: 2 });
  if (!sign) return (cents < 0 ? '-' : '') + '$' + s;
  return (cents > 0 ? '+$' : cents < 0 ? '-$' : '$') + s;
}
function pct(f, d = 2) { return (f * 100).toFixed(d) + '%'; }
function badge(status, bucket) {
  const b = bucket || 'OTHER';
  return `<span class="badge b-${b}">${esc(status || '—')}</span>`;
}
function stateBox(kind, text, extra = '') {
  const icons = { loading: '◌', empty: '▢', offline: '⊘', error: '⚠',
                  tamper: '🔓', notrun: '—' };
  return `<div class="state-box ${kind === 'tamper' ? 'tamper' : ''}">
    <div class="icon">${icons[kind] || '◌'}</div>
    <div class="${kind === 'tamper' ? 'title' : ''}">${esc(text)}</div>
    ${extra}</div>`;
}

// ------------------------------------------------------------------ shell --
function buildNav() {
  const nav = $('#nav');
  nav.innerHTML = '';
  for (const [id, label, icon] of SECTIONS) {
    const b = document.createElement('button');
    b.innerHTML = `<span style="width:16px">${icon}</span>${label}`;
    if (id === section) b.classList.add('active');
    b.onclick = () => { section = id; window.paperdesk.setSection(id);
                        buildNav(); render(); };
    nav.appendChild(b);
  }
}

function renderShell() {
  if (!S) return;
  const chainOk = S.ledger.chain.ok;
  const chainEmpty = !S.ledger.rowsCount;
  $('#chain-dot').className = 'dot ' + (chainOk ? 'green'
    : chainEmpty ? 'gray' : 'red');
  $('#chain-val').textContent = chainOk
    ? `OK · ${S.ledger.chain.verified_rows} rows`
    : (chainEmpty ? 'empty' : 'FAILED');
  const r = S.runner;
  const dot = $('#runner-dot');
  const live = r.state === 'attached';
  dot.className = 'dot ' + (live ? 'green'
    : (['starting', 'stopping', 'probing'].includes(r.state)
       ? 'orange' : 'gray'));
  $('#runner-label').textContent =
    r.state === 'attached' ? `RUNNER LIVE · pid ${r.pid} · ${r.source}`
    : r.state === 'detached' ? 'RUNNER STOPPED'
    : r.state === 'starting' ? 'STARTING…'
    : r.state === 'stopping' ? 'STOPPING…'
    : r.state === 'stopped' ? 'STOPPED BY APP'
    : r.state === 'failed' ? `ERROR · ${r.error}` : 'probing…';
  $('#paused-chip').classList.toggle('hidden', !r.paused);
  $('#stale-chip').classList.toggle('hidden', !S.health.isStale);
  $('#policy-select').value =
    ({ ask: 'ask', pauseDecisions: 'pauseDecisions',
       keepRunning: 'keepRunning' })[currentPolicy] || 'ask';
  $('#policy-label').textContent = 'window close: '
    + ({ ask: 'ask', pauseDecisions: 'pause decisions',
         keepRunning: 'keep running' })[currentPolicy];
  const b = $('#banner');
  const sb = S.ledger.isSandbox || S.sandbox;
  b.className = 'banner ' + (sb ? 'sandbox' : 'paper');
  b.innerHTML = `<span>${sb
    ? '<b>SANDBOX</b> — synthetic genesis, fabricated gates. Never a production record.'
    : '<b>PAPER — VIRTUAL MONEY ONLY.</b> No Polymarket account is connected; no real order can be placed by this app.'}</span>
    <span class="seal-chip">LIVE TRADING: SEALED</span>`;
}

// ------------------------------------------------------------------ views --
function render() {
  if (!S) return;
  renderShell();
  const v = $('#view');
  try {
    if (section === 'dashboard') v.innerHTML = viewDashboard();
    else if (section === 'matches') v.innerHTML = viewMatches();
    else if (section === 'opportunities') v.innerHTML = viewOpportunities();
    else if (section === 'health') v.innerHTML = viewHealth();
    else if (section === 'ai') v.innerHTML = viewAI();
    else if (section === 'laws') v.innerHTML = viewLaws();
  } catch (e) {
    v.innerHTML = stateBox('error', 'View render failed: ' + e.message);
    console.error('render(' + section + '):', e);
  }
  wire();
  if (section === 'dashboard' && S.ledger.chain.ok) {
    EquityChart.render($('#equity-holder'), S.ledger.equity, { height: 230 });
  }
}

function kpiCard(k, v, s, cls = '') {
  return `<div class="card kpi"><div class="k">${k}</div>
    <div class="v ${cls}">${v}</div><div class="s">${s}</div></div>`;
}

function viewDashboard() {
  if (S.ledger.chain.ok === false && S.ledger.rowsCount) {
    return `<h2>Dashboard</h2>
      ${stateBox('tamper', 'LEDGER CHAIN VERIFY FAILED — all financials '
        + 'withheld',
        (S.ledger.chain.errors || []).slice(0, 4)
          .map(e => `<div class="mono-err">${esc(e)}</div>`).join(''))}`;
  }
  if (!S.ledger.rowsCount) {
    return `<h2>Dashboard</h2>${stateBox('loading',
      'Loading from ledger…')}`;
  }
  const w = S.ledger.wallet;
  const settled = w.settledCount;
  const outcomes = w.outcomes || {};
  return `<h2>Dashboard</h2>
  <div class="grid4" style="margin-bottom:12px">
    ${kpiCard('◉ Equity', money(w.equityCents, false),
      S.ledger.isSandbox ? 'SANDBOX genesis' : 'real paper wallet (virtual)')}
    ${kpiCard('↗ Realized P&L', money(w.totalPnLCents),
      `${settled} settled · W${outcomes.WIN || 0}/L${outcomes.LOSE || 0}`
      + `/R${outcomes.REFUND || 0}`,
      w.totalPnLCents >= 0 ? 'green' : 'red')}
    ${kpiCard('🔓 Open exposure', money(w.openExposureCents, false),
      `cap ${money(w.openCapCents, false)} · avail `
      + money(Math.max(0, Math.min(w.equityCents - w.openExposureCents,
        w.openCapCents - w.openExposureCents)), false))}
    ${kpiCard('↘ Drawdown', pct(w.drawdownFrac),
      w.pausedByDrawdown ? 'PAUSED — 10% law breached'
        : `pause at 10% · peak ${money(w.peakCents, false)}`,
      w.pausedByDrawdown ? 'red' : (w.drawdownFrac > 0.05 ? 'orange' : ''))}
  </div>
  <div class="card" id="equity-holder" style="margin-bottom:12px"></div>
  <div class="grid2" style="margin-bottom:12px">
    <div class="card"><div class="sec-title">REALIZED P&L BY LEAGUE</div>
      ${Object.keys(w.pnlBySport).length
        ? Object.keys(w.pnlBySport).sort().map(l =>
          `<div class="kv"><span class="kk">${esc(l)}</span>
           <span class="vv ${w.pnlBySport[l] >= 0 ? 'green' : 'red'}"
            >${money(w.pnlBySport[l])}</span></div>`).join('')
        : '<div class="dim">No settlements yet</div>'}
    </div>
    <div class="card"><div class="sec-title">CAPITAL LAW (pinned)</div>
      <div class="kv"><span class="kk">law</span><span class="vv"
        >${esc(w.capitalLaw)}</span></div>
      <div class="kv"><span class="kk">open positions</span>
        <span class="vv">${w.openCount}</span></div>
      <div class="kv"><span class="kk">ledger rows</span>
        <span class="vv">${S.ledger.rowsCount}</span></div>
      <div class="kv"><span class="kk">chain verify</span>
        <span class="vv green">OK (app-side byte check)</span></div>
      <div class="kv"><span class="kk">EV gate</span>
        <span class="vv">EV_net ≥ 5% (c=0.02) — pinned</span></div>
    </div>
  </div>
  <div class="card"><div class="sec-title">RECENT RUNNER INCIDENTS
    (ops journal)</div>
    ${incidentsHtml()}
  </div>`;
}

function incidentsHtml() {
  const inc = (S.health.live && S.health.live.incidents_tail) || [];
  if (!S.health.live) {
    return '<div class="dim">Runner state unavailable (offline or not '
      + 'started)</div>';
  }
  if (!inc.length) return '<div class="dim">No incidents</div>';
  return inc.slice(-8).reverse().map(i =>
    `<div class="inc-row"><span class="ts">${esc(i.ts_utc)}</span>
     <span class="kd ${String(i.kind || '').includes('ERROR')
       ? 'orange' : ''}">${esc(i.kind)}</span>
     <span class="dt">${esc(i.detail)}</span></div>`).join('');
}

function filteredMatches() {
  const q = filters.q.toLowerCase();
  return S.ledger.matches.filter(m => {
    if (filters.league !== 'All' && m.league !== filters.league) return false;
    switch (filters.status) {
      case 'bet': if (m.bucket !== 'BET') return false; break;
      case 'open': if (!m.isOpen) return false; break;
      case 'settled': if (!m.settlement) return false; break;
      case 'noEdge': if (m.bucket !== 'NO_EDGE') return false; break;
      case 'skipped':
        if (!['NOT_RUN', 'NO_QUOTE', 'NO_FORECAST', 'REFUSED']
          .includes(m.bucket)) return false; break;
      case 'blocked': if (m.bucket !== 'BLOCKED') return false; break;
    }
    if (q) {
      const hay = [m.matchId, m.home, m.away, m.league,
        m.decisionStatus || '',
        (m.decision && m.decision.reason) || ''].join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

function viewMatches() {
  if (S.ledger.chain.ok === false && S.ledger.rowsCount) {
    return `<h2>Matches</h2>${stateBox('tamper',
      'LEDGER CHAIN VERIFY FAILED — history withheld')}`;
  }
  const leagues = ['All', ...Array.from(
    new Set(S.ledger.matches.map(m => m.league))).sort()];
  const list = filteredMatches();
  const sel = S.ledger.matches.find(m => m.matchId === selectedMatchId);
  return `<h2>Matches</h2>
  <div class="filters">
    <span class="seg" id="f-status">
      ${[['all', 'All'], ['bet', 'BET_PAPER'], ['open', 'OPEN'],
         ['settled', 'Settled'], ['noEdge', 'NO_EDGE'],
         ['skipped', 'Skipped/NOT_RUN'], ['blocked', 'Blocked']]
        .map(([v, l]) => `<button data-v="${v}"
          class="${filters.status === v ? 'active' : ''}">${l}</button>`)
        .join('')}
    </span>
    <select id="f-league">${leagues.map(l =>
      `<option ${l === filters.league ? 'selected' : ''}>${esc(l)}</option>`)
      .join('')}</select>
    <input type="text" id="f-q" placeholder="Search team, match id, reason…"
      value="${esc(filters.q)}" />
    <span class="dim">${list.length} of ${S.ledger.matches.length} matches ·
      source: ledger file (chain-verified each load)</span>
  </div>
  <div class="grid2" style="grid-template-columns: 400px 1fr; gap: 14px;">
    <div class="card match-list" style="max-height: 66vh; overflow-y: auto;">
      ${!S.ledger.matches.length ? stateBox('loading', 'Loading from ledger…')
        : !list.length ? stateBox('empty',
          'No match passes the current filters.')
        : list.map(m => `
        <div class="match-row ${m.matchId === selectedMatchId ? 'sel' : ''}"
          data-mid="${esc(m.matchId)}">
          <span class="dot ${bucketDot(m.bucket)}"></span>
          <div>
            <div class="t">${esc(m.home)} vs ${esc(m.away)}</div>
            <div class="sub"><b>${esc(m.league)}</b>
              <span class="mono">${esc(m.kickoffUTC || '')}</span>
              ${m.chosenLeg ? `<span class="mono">${esc(m.chosenLeg)} ${
                m.stakeCents}c</span>` : ''}</div>
          </div>
          <div class="right">${badge(m.decisionStatus, m.bucket)}
            ${m.pnlCents != null ? `<span class="${
              m.pnlCents >= 0 ? 'pnl-pos' : 'pnl-neg'}">${
              money(m.pnlCents)}</span>` : ''}</div>
        </div>`).join('')}
    </div>
    <div>${sel ? matchDetail(sel)
      : stateBox('empty', 'Select a match to see the full decision chain: '
        + 'model probabilities, the three market legs, walked ask at actual '
        + 'stake, depth, fee, EV after costs, snapshot & anchor times, '
        + 'reason, settlement and P&L.')}</div>
  </div>`;
}

function bucketDot(b) {
  return { BET: 'blue', BLOCKED: 'orange', NOT_RUN: 'purple',
           NO_QUOTE: 'orange', REFUSED: 'red', NO_EDGE: 'gray' }[b] || 'gray';
}

function kv(k, v, cls = '') {
  return `<div class="kv"><span class="kk">${k}</span>
    <span class="vv ${cls}">${v}</span></div>`;
}

function matchDetail(m) {
  const d = m.decision || {};
  const f = m.forecast || {};
  const pf = (d.p_frozen && Object.keys(d.p_frozen).length)
    ? d.p_frozen : (f.p || {});
  const ev = d.ev_net_by_leg || {};
  const legOrder = ['HOME', 'DRAW', 'AWAY'].filter(l =>
    pf[l] != null || ev[l] != null);
  const aiOps = S.ai.opinions.filter(o => o.matchID === m.matchId);
  const oracle = askInfo(m);
  return `
  <div class="card" style="margin-bottom:12px">
    <div style="display:flex;gap:10px;align-items:center">
      <div style="font-size:15px;font-weight:700">${esc(m.home)} vs
        ${esc(m.away)}</div><span class="spacer"></span>
      ${badge(m.decisionStatus, m.bucket)}
      ${m.isOpen ? '<span class="badge b-BET">OPEN</span>' : ''}
    </div>
    <div class="sub dim" style="margin-top:4px;display:flex;gap:12px">
      <span><b>${esc(m.league)}</b></span>
      <span class="mono">${esc(m.kickoffUTC || '—')}</span>
      <span class="mono">${esc(m.competition || '')}</span>
    </div>
  </div>
  <div class="card" style="margin-bottom:12px">
    <div class="sec-title">DECISION (verbatim reason)</div>
    ${kv('status', esc(m.decisionStatus || '—'))}
    ${kv('chosen leg', esc(m.chosenLeg || '— (no bet)'))}
    ${kv('stake', m.stakeCents > 0
      ? `${m.stakeCents}c (${money(m.stakeCents, false)})` : '0c')}
    ${kv('model', esc(d.model_id || f.model_id
      || (d.forecast_meta && d.forecast_meta.model_version_sha) || '—'))}
    ${d.reason ? `<div class="reason-box">${esc(d.reason)}</div>` : ''}
  </div>
  <div class="card" style="margin-bottom:12px">
    <div class="sec-title">THREE MARKET LEGS (model × walked market)</div>
    ${legOrder.length ? legOrder.map(l => legCard(l, pf[l], ev[l],
      m.chosenLeg === l, oracle[l])).join('')
      : stateBox('empty', 'No frozen leg numbers on this row (refusal rows '
        + 'carry reasons instead).')}
    <div class="note">${walkCaption(m)}</div>
  </div>
  <div class="grid2" style="margin-bottom:12px">
    <div class="card"><div class="sec-title">PIT TIMING (anchor law)</div>
      ${kv('kickoff (UTC)', esc(m.kickoffUTC || '—'))}
      ${kv('forecast recorded', esc(f.recorded_at_utc
        || (d.forecast_meta && d.forecast_meta.recorded_at_utc) || '—'))}
      ${kv('quote fetched', esc((m.quote && m.quote.fetch_ts_utc)
        || d.decided_at_utc || '—'))}
      ${kv('decided', esc(m.decidedAtUTC || '—'))}
      ${kv('payload sha', esc(String((m.quote && m.quote.payload_sha256)
        || '—').slice(0, 24) + '…'))}
    </div>
    <div class="card"><div class="sec-title">SETTLEMENT</div>
      ${m.settlement ? `
        ${kv('outcome for leg', esc(m.outcomeForLeg || '—'),
          m.outcomeForLeg === 'WIN' ? 'green'
          : m.outcomeForLeg === 'LOSE' ? 'red' : '')}
        ${kv('P&L', money(m.pnlCents || 0),
          (m.pnlCents || 0) >= 0 ? 'green' : 'red')}
        ${kv('settled at', esc(m.settlement.settled_at_utc || '—'))}
        ${kv('source', esc(m.settlement.source_ref || '—'))}`
        : m.isOpen
        ? '<div class="dim">⏳ OPEN — settles only from the pinned results '
          + 'source after kickoff+grace; never inferred.</div>'
        : '<div class="dim">No settlement row (not a bet).</div>'}
    </div>
  </div>
  <div class="card" style="margin-bottom:12px">
    <div class="sec-title" style="display:flex">
      <span>AI REVIEW — SHADOW</span><span class="spacer"></span>
      <span class="badge b-NOT_RUN">${esc(S.ai.runtime)}</span></div>
    ${aiOps.length ? aiOps.map(opHtml).join('')
      : '<div class="dim">No opinion recorded for this match yet.</div>'}
    <div style="display:flex;gap:10px;align-items:center;margin-top:9px">
      <button id="ai-run" data-mid="${esc(m.matchId)}">✦ Run shadow
        review</button>
      <span class="note" style="margin:0">Advisory only — no effect on any
        decision; deadline law: must finish before the kickoff anchor.</span>
    </div>
  </div>
  <div class="card">
    <div class="sec-title">RAW ROW PROVENANCE (chain-verified)</div>
    ${[['decision', d.row_sha256], ['forecast', f.row_sha256],
       ['quote', m.quote && m.quote.row_sha256],
       ['settlement', m.settlement && m.settlement.row_sha256]]
      .filter(x => x[1])
      .map(([k, sha]) => kv(k, esc(String(sha).slice(0, 32)) + '…'))
      .join('') || '<div class="dim">—</div>'}
  </div>`;
}

function legCard(leg, p, ev, chosen, ask) {
  const evCls = ev == null ? '' : ev >= 0.05 ? 'green'
    : ev >= 0 ? 'orange' : 'dim';
  return `<div class="leg-card ${chosen ? 'chosen' : ''}">
    <div class="leg-name">${leg}${chosen
      ? '<span class="chipx">CHOSEN</span>' : ''}</div>
    <div class="leg-stat">model p <b>${p != null ? pct(p, 1) : '—'}</b></div>
    <div class="leg-stat">EV_net <b class="${evCls}">${
      ev != null ? ev.toFixed(4) : '—'}</b></div>
    <div class="leg-stat">walk @ stake <b>${esc(ask || '—')}</b></div>
  </div>`;
}

// Walked per-leg info from PM rows (vwap/best ask, shares, fee, levels).
function askInfo(m) {
  const out = {};
  const po = m.quote && m.quote.pm_outcomes;
  if (po && typeof po === 'object') {
    for (const [leg, o] of Object.entries(po)) {
      if (!o || typeof o !== 'object') continue;
      const ask = o.vwap_ask ?? o.best_ask;
      if (ask == null) continue;
      let s = `ask ${Number(ask).toFixed(4)}`;
      if (o.filled_shares != null) s += ` · ${o.filled_shares} sh`;
      if (o.fee_total != null) s += ` · fee ${o.fee_total}c`;
      if (o.levels_used != null) s += ` · ${o.levels_used} lvl`;
      if (o.spend != null) s += ` · spend ${o.spend}c`;
      out[leg] = s;
    }
  }
  return out;
}

function walkCaption(m) {
  if (m.quote && m.quote.pm_outcomes) {
    return 'Prices are walk-the-ASK at the ACTUAL stake (budget fixed-point '
      + 'incl. fee), never midpoint or naive sums.';
  }
  const odds = m.quote && m.quote.odds;
  if (odds && Object.keys(odds).length) {
    return 'Frozen listed odds (pre-anchor snapshot): ' + Object.keys(odds)
      .sort().map(k => `${k}=${odds[k]}`).join('  ');
  }
  return '';
}

function opHtml(op) {
  const verdict = op.verdict || op.status;
  return `<div class="op">
    <div class="head">
      <span class="verdict v-${esc(op.verdict || 'ABSTAIN')}">${esc(verdict)}</span>
      ${op.isMock ? '<span class="v-MOCK-chip">MOCK</span>' : ''}
      <span class="dim mono" style="font-size:10px">${esc(op.createdAtUTC)}</span>
    </div>
    ${op.rationale ? `<div style="margin-top:5px;user-select:text">${
      esc(op.rationale)}</div>` : ''}
    ${(op.uncertainties || []).map(u =>
      `<div class="src">?<span>${esc(u)}</span></div>`).join('')}
    ${(op.sources || []).map(s =>
      `<div class="src">${s.untrusted ? '⚠' : '🔗'}
        <span>${esc(s.kind)}: ${esc(s.ref)}</span>
        ${s.untrusted ? '<span class="untrusted">UNTRUSTED_DATA</span>'
          : ''}</div>`).join('')}
    ${op.error ? `<div class="src red">✖<span>${esc(op.error)}</span></div>`
      : ''}
    <div class="src dim">provider ${esc(op.provider)} · mode ${esc(op.mode)}
      · prompt sha ${esc(String(op.promptSha256 || '—').slice(0, 12))}…
      · snapshot sha ${esc(String(op.inputSnapshotSha256 || '—')
        .slice(0, 12))}…</div>
  </div>`;
}

function viewOpportunities() {
  const up = (S.health.live && S.health.live.upcoming) || [];
  let body;
  if (oppTab === 0) {
    body = !up.length
      ? stateBox(S.health.live ? 'empty' : 'offline',
          S.health.live
            ? 'No fixtures inside the cadence lookahead right now (NBA 24h '
              + '/ SOCCER+WSL 48h).'
            : 'Runner state unavailable — upcoming cadence windows need the '
              + 'live /api/state feed.')
      : `<div class="card" style="margin-bottom:12px">
          <div class="sec-title">CADENCE LOOKAHEAD (runner plan cache)</div>
          ${up.map(f => `
            <div class="kv">
              <span class="kk"><b>${esc(f.league || '?')}</b></span>
              <span class="vv">${esc(f.home || '?')} vs ${esc(f.away || '?')}
                — ${esc(f.kickoff_utc || f.date || '—')}
                ${f.not_run_reason ? `<span class="orange">${
                  esc(f.not_run_reason)}</span>` : ''}</span>
            </div>`).join('')}
        </div>
        <div class="card"><div class="sec-title">ANCHOR LAW (pinned)</div>
          ${kv('NBA / WNBA', 'T0 − 6h10m batch anchor; decisions stop at '
            + 'anchor')}
          ${kv('SOCCER / WSL', 'kickoff − 6h strict; quote snapshot strictly '
            + 'pre-anchor')}
          ${kv('missed window', 'NOT_RUN forever — no backfill')}
          ${kv('lookahead', 'NBA/WNBA 24h · SOCCER/WSL 48h')}
        </div>`;
  } else {
    const refused = S.ledger.matches.filter(m =>
      ['NOT_RUN', 'NO_QUOTE', 'NO_FORECAST', 'BLOCKED', 'REFUSED', 'NO_EDGE']
        .includes(m.bucket));
    body = !refused.length
      ? stateBox(S.ledger.matches.length ? 'empty' : 'loading',
          S.ledger.matches.length
            ? 'No refusal rows — every decided match is a bet or a '
              + 'settlement so far.'
            : 'Loading from ledger…')
      : `<div class="card">${refused.map(m => `
          <div style="padding:7px 0;border-bottom:1px solid var(--line)">
            <div style="display:flex;gap:8px;align-items:center">
              <b>${esc(m.home)} vs ${esc(m.away)}</b><span class="spacer"></span>
              ${badge(m.decisionStatus, m.bucket)}</div>
            <div class="dim" style="font-size:10.5px;margin-top:2px">
              <b>${esc(m.league)}</b>
              <span class="mono">${esc(m.kickoffUTC || '')}</span></div>
            ${m.decision && m.decision.reason
              ? `<div class="mono dim" style="font-size:10.5px;margin-top:3px"
                  >${esc(m.decision.reason)}</div>` : ''}
          </div>`).join('')}</div>`;
  }
  return `<h2>Opportunities</h2>
  <div class="filters"><span class="seg" id="opp-tab">
    <button data-t="0" class="${oppTab === 0 ? 'active' : ''}">Upcoming
      windows</button>
    <button data-t="1" class="${oppTab === 1 ? 'active' : ''}">Skipped
      &amp; refusals</button></span></div>${body}`;
}

function viewHealth() {
  const r = S.runner, h = S.health;
  const live = h.live || {};
  const svc = live.service || {};
  const hb = r.heartbeat;
  const q = live.quota || {};
  const pm = h.pmProbe;
  const stateText = r.state === 'attached'
    ? `ATTACHED pid ${r.pid} (${r.source}${r.source === 'launchd'
      ? ' — launchd-managed' : ''})`
    : r.state === 'detached' ? 'NOT RUNNING'
    : r.state === 'starting' ? 'starting…'
    : r.state === 'stopping' ? 'stopping (SIGTERM sent)…'
    : r.state === 'stopped' ? 'stopped by app'
    : r.state === 'failed' ? `FAILED: ${r.error}` : 'probing…';
  return `<h2>System Health</h2>
  <div class="card health-block">
    <div class="health-head">▸ PAPER RUNNER (exactly one)
      <span class="st badge ${r.state === 'attached' ? 'b-SETTLED'
        : 'b-BLOCKED'}">${r.state === 'attached' ? 'healthy' : 'down'}</span>
    </div>
    ${kv('state', esc(stateText),
      r.state === 'attached' ? 'green' : 'orange')}
    ${kv('pid', esc(r.pid || '—'))}
    ${kv('mode', S.sandbox ? 'SANDBOX (synthetic)' : 'REAL paper',
      S.sandbox ? 'orange' : '')}
    ${kv('heartbeat age', hb && hb.ageSeconds != null
      ? hb.ageSeconds.toFixed(0) + 's' : '—')}
    ${kv('tick count', esc(hb ? hb.tickCount : '—'))}
    ${kv('last cadence', esc((hb && hb.lastCadence) || '—'))}
    ${kv('decisions paused', r.paused ? 'YES (UI flag)' : 'no')}
    ${kv('live state API', h.liveFetchError
      ? `<span class="red">✖ ${esc(h.liveFetchError)}</span>`
      : `127.0.0.1:${svc.port || 8791}/api/state OK`, h.liveFetchError
        ? 'red' : 'green')}
    ${kv('single instance', 'lock probed each poll (service.lock)')}
  </div>
  <div class="card health-block">
    <div class="health-head">▸ DATA FEEDS
      <span class="st badge ${pm && pm.ok ? 'b-SETTLED' : 'b-BLOCKED'}">${
        pm ? (pm.ok ? 'reachable' : 'failing') : 'probing'}</span></div>
    ${kv('polymarket gamma (display)', pm
      ? (pm.ok ? `OK ${esc(pm.statusText)} · ${pm.latencyMs}ms`
        : `<span class="orange">FAIL ${esc(pm.statusText)}</span>`)
      : 'not probed yet')}
    ${kv('polymarket clob books', 'read-only walks on demand (snapshot '
      + 'journaled to pm_ui_snapshots/)')}
    ${kv('websocket market feed', 'NOT_USED_IN_THIS_BUILD — UI updates via '
      + '2–4s poll + heartbeat & stale alarm (equivalent mechanism, no venue '
      + 'WS)')}
    ${kv('fixture source', live ? 'runner plan (ESPN schedules / The Odds '
      + 'API / PM Gamma per pinned lane)' : 'runner offline')}
    ${kv('UI data source age', h.liveLastOK
      ? ((Date.now() - h.liveLastOK) / 1000).toFixed(0) + 's ago' : '—',
      h.isStale ? 'red' : 'green')}
    ${kv('stale alarm', h.isStale
      ? '<span class="red">STALE (>180s since last good state)</span>'
      : 'none', h.isStale ? 'red' : 'green')}
  </div>
  <div class="card health-block">
    <div class="health-head">▸ ODDS API QUOTA (pinned caps)</div>
    ${kv('used today', q.used_today != null
      ? `${q.used_today} / 4 credits` : '—')}
    ${kv('used this month', q.used_month != null
      ? `${q.used_month} / 120 credits` : '—')}
    ${kv('exhausted behavior', 'QUOTA_SKIP before any network call '
      + '(fail-closed)')}
  </div>
  <div class="card health-block">
    <div class="health-head">▸ AI REVIEW RUNTIME
      <span class="st badge ${S.ai.mode === 'disabled-no-entitlement'
        ? 'b-BLOCKED' : 'b-NOT_RUN'}">${esc(S.ai.runtime)}</span></div>
    ${kv('keychain key', S.ai.entitlement.present
      ? `present (sha256 ${esc(S.ai.entitlement.fingerprint)}…)`
      : '<span class="orange">NOT_RUN_AI_RUNTIME_ENTITLEMENT</span>')}
    ${kv('authority', 'SHADOW — opinions recorded, never influence '
      + 'decisions; veto/alternative needs registered policy + owner GO')}
    ${kv('web connector', 'read-only, allow-listed domains, ≤5 requests/'
      + 'opinion; all web content UNTRUSTED_DATA')}
    ${kv('opinions stored', `${S.ai.opinions.length} (sidecar ai_review/, `
      + 'not the ledger)')}
  </div>
  <div class="card health-block">
    <div class="health-head">▸ GOVERNANCE GATES (display only)</div>
    ${kv('runner GO', 'CONSUMED (capture active — runner laws live)')}
    ${kv('polymarket cutover', 'GO SPORTS PAPERTRADE EXEC V1 POLYMARKET '
      + 'CUTOVER — REGISTERED_NOT_CONSUMED (not typed here)', 'blue')}
    ${kv('live trading', 'SEALED — no cycle, no phrase, no path', 'red')}
    ${kv('AI authority', 'NOT_REGISTERED — candidate phrase lives only in '
      + 'the decision packet for the owner', 'purple')}
  </div>`;
}

function viewAI() {
  const ent = S.ai.entitlement;
  return `<h2>AI Review (SHADOW)</h2>
  <div class="card" style="margin-bottom:12px">
    <div class="sec-title" style="display:flex;align-items:center">
      <span>RUNTIME</span><span class="spacer"></span>
      <span class="seg" id="ai-mode">
        <button data-m="shadow-mock" class="${
          S.ai.mode === 'shadow-mock' ? 'active' : ''}">MOCK demo</button>
        <button data-m="shadow-live" class="${
          S.ai.mode === 'shadow-live' ? 'active' : ''}"
          ${ent.present ? '' : 'disabled'}>Z.ai SHADOW</button>
      </span></div>
    ${ent.present
      ? `<div class="green">🔑 General API key present in Keychain
          (fingerprint ${esc(ent.fingerprint)}…). SHADOW mode records
          opinions only.</div>`
      : `<div class="orange">🚫 NOT_RUN_AI_RUNTIME_ENTITLEMENT — no Z.ai
          General API key in Keychain (service com.myquant.paperdesk /
          account zai-api-key). Mock demo runs locally. The Coding-Plan API
          is banned as an opinion backend; no purchase will be made by the
          app.</div>`}
    ${S.ai.lastNote ? `<div class="note mono">last: ${esc(S.ai.lastNote)}</div>`
      : ''}
  </div>
  <div class="card" style="margin-bottom:12px">
    <div class="sec-title">FROZEN BOUNDARIES</div>
    ${kv('verdicts', 'APPROVE · VETO · CHALLENGE · ALTERNATIVE · ABSTAIN '
      + '(frozen JSON schema)')}
    ${kv('budget', '≤10 min per fixture, must COMPLETE before the decision '
      + 'deadline (anchor); late ⇒ TIMEOUT_LATE_INVALID')}
    ${kv('cannot touch', 'model p, quotes, EV, stake, fees, hard gates, '
      + 'ledger history')}
    ${kv('ALTERNATIVE rule', 'candidate leg would still pass every gate on '
      + 'the same snapshot; in SHADOW it is recorded, never applied')}
    ${kv('web content', 'UNTRUSTED_DATA — provenance only, prompt-injection '
      + 'hardened, allow-listed domains')}
    ${kv('fail-closed', 'timeout / API error / malformed JSON ⇒ explicit '
      + 'status, no silent substitute')}
  </div>
  <div class="card">
    <div class="sec-title">OPINION LEDGER (sidecar, append-only)</div>
    ${S.ai.opinions.length ? S.ai.opinions.map(opHtml).join('')
      : stateBox('empty', 'No opinions yet. Open a match and run a shadow '
        + 'review — in MOCK mode they are generated locally and clearly '
        + 'labeled.')}
  </div>`;
}

function viewLaws() {
  return `<h2>Laws & Docs</h2>
  <div class="grid2">
    <div class="card">
      <div class="sec-title">PINNED RISK / CAPITAL LAWS (display only)</div>
      ${kv('genesis wallet', '100,000c ($1,000.00), one wallet')}
      ${kv('capital law v3', 'stake 1% equity (cent, half-up); open cap '
        + '50,000c + availability bound')}
      ${kv('EV gate', 'EV_net = p·d_eff − 1 − c ≥ 0.05, c = 0.02 frozen')}
      ${kv('drawdown pause', 'pause at 10% from peak')}
      ${kv('anchors', 'NBA/WNBA T0−6h10m; SOCCER/WSL kickoff−6h strict')}
      ${kv('pricing', 'walk-the-ASK at actual stake incl. taker fee '
        + '0.05·p·(1−p) once; never midpoint, never 1X2 naive sums')}
      ${kv('quota', '4 credits/day · 120/month, precheck fail-closed')}
      ${kv('settlement', 'pinned sources only; VOID/PUSH/CANCELLED/POSTPONED '
        + '⇒ refund; never inferred')}
    </div>
    <div class="card">
      <div class="sec-title">GOVERNING DOCUMENTS (on disk)</div>
      ${kv('amendment', 'research/control/SPORTS-PAPERTRADE-EXEC-V1/'
        + 'AMENDMENT_MACOS_APP_UI_V1.md')}
      ${kv('plan', 'plans/PLAN_sports_papertrade_exec_v1.md')}
      ${kv('decision packet', 'research/control/SPORTS-PAPERTRADE-EXEC-V1/'
        + 'PAPERDESK_DECISION_PACKET_2026-10-19.md')}
      ${kv('audit', 'research/control/SPORTS-PAPERTRADE-EXEC-V1/'
        + 'PAPERDESK_A7_2026-10-19.md')}
      ${kv('runbook', 'apps/paperdesk/RUNBOOK.md')}
    </div>
  </div>
  <div class="card" style="margin-top:12px">
    <div class="sec-title red">THIS APP CANNOT</div>
    ${kv('orders', '<span class="red">✖ place any order on Polymarket '
      + '(LiveExecution sealed, no endpoint, no credentials)</span>')}
    ${kv('ledger', '<span class="red">✖ write to the paper ledger '
      + '(read-only projection; the pinned runner is the only lawful '
      + 'writer)</span>')}
    ${kv('AI', '<span class="red">✖ let AI influence decisions (SHADOW '
      + 'sidecar only)</span>')}
    ${kv('GO phrases', '<span class="red">✖ consume any GO phrase</span>')}
    <div class="note">Seal: ${esc(S.seal.statement)}</div>
  </div>`;
}

// ------------------------------------------------------------------ wire --
function wire() {
  document.querySelectorAll('#f-status button').forEach(b => {
    b.onclick = () => { filters.status = b.dataset.v; render(); };
  });
  const fl = $('#f-league');
  if (fl) fl.onchange = () => { filters.league = fl.value; render(); };
  const fq = $('#f-q');
  if (fq) fq.oninput = () => { filters.q = fq.value; renderMatchesOnly(); };
  document.querySelectorAll('.match-row').forEach(r => {
    r.onclick = () => { selectedMatchId = r.dataset.mid; render(); };
  });
  document.querySelectorAll('#opp-tab button').forEach(b => {
    b.onclick = () => { oppTab = Number(b.dataset.t); render(); };
  });
  document.querySelectorAll('#ai-mode button').forEach(b => {
    b.onclick = () => { window.paperdesk.aiSetMode(b.dataset.m); };
  });
  const aiRun = $('#ai-run');
  if (aiRun) aiRun.onclick = () => {
    const m = S.ledger.matches.find(x => x.matchId === aiRun.dataset.mid);
    if (m) window.paperdesk.aiRun({
      matchId: m.matchId, home: m.home, away: m.away, league: m.league,
      kickoffUTC: m.kickoffUTC,
      decisionStatus: m.decisionStatus,
      decision: m.decision ? { reason: m.decision.reason } : null });
  };
  const ps = $('#policy-select');
  if (ps) ps.onchange = () => { currentPolicy = ps.value;
    window.paperdesk.setPolicy(ps.value); renderShell(); };
}

// search typing should not rebuild the input (focus loss); patch list only
function renderMatchesOnly() {
  const v = $('#view');
  v.innerHTML = viewMatches();
  wire();
  const fq = $('#f-q');
  if (fq) { fq.focus(); fq.setSelectionRange(fq.value.length,
                                            fq.value.length); }
}

window.paperdesk.getState(s => {
  S = s;
  if (s && s.policy) currentPolicy = s.policy;
  // evidence tour / external navigation: main may switch the section
  if (s && s.section && s.section !== section) {
    section = s.section;
    buildNav();
  }
  render();
});

// runner menu
$('#runner-menu-btn').onclick = e => {
  e.stopPropagation();
  $('#runner-menu').classList.toggle('hidden');
};
document.addEventListener('click', () =>
  $('#runner-menu').classList.add('hidden'));
document.querySelectorAll('#runner-menu button').forEach(b => {
  b.onclick = async () => {
    $('#runner-menu').classList.add('hidden');
    const act = b.dataset.act;
    if (act === 'pause') window.paperdesk.pauseRunner(true, 'menu');
    if (act === 'resume') window.paperdesk.pauseRunner(false, 'menu');
    if (act === 'start') window.paperdesk.startRunner();
    if (act === 'stop') window.paperdesk.stopRunner();
    if (act === 'takeover') window.paperdesk.takeover();
  };
});
buildNav();
