'use strict';
// AI V2 PRODUCER (PAPERDESK-FIXALL-NCAA-V1 W4.3/W4.4/W4.6) — the JS side is
// a COLLECTOR: it reads the runner's PENDING_AI queue (ai_review/pending.json
// — the runner owns the candidate hashes), gathers REAL evidence (the
// runner's own `ai-evidence` collector + system-captured PM pages), calls
// the CONFIGURED provider, enforces the FROZEN prompt + the STRICT
// {verdict: ALLOW|VETO} schema, and writes the hash-locked opinion the
// Python gate consumes. It NEVER decides placement and NEVER supplies
// numbers. Legacy ai.js stays the SHADOW display engine — unwired from
// authority.

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');

const VERDICTS_V2 = ['ALLOW', 'VETO'];

function nowZ() {
  return new Date().toISOString().replace(/\.\d+Z$/, 'Z');
}
function sha256Hex(s) {
  return crypto.createHash('sha256').update(s, 'utf8').digest('hex');
}

function loadProviderConfig(worktreeDir) {
  // W4.6: the model is CONFIG (model id, endpoint, key reference) — never
  // hard-wired. Defaults mirror config.json ai_provider.
  let cfg = {};
  try {
    const p = path.join(worktreeDir, 'research', 'papertrade_exec',
      'config.json');
    cfg = JSON.parse(fs.readFileSync(p, 'utf8')).ai_provider || {};
  } catch (e) { cfg = {}; }
  return {
    provider: cfg.provider || 'openrouter',
    endpoint: cfg.endpoint ||
      'https://openrouter.ai/api/v1/chat/completions',
    model_id: cfg.model_id || 'minimax/minimax-m3.1-flash:free',
    fallback_models: cfg.fallback_models || [],
    prompt_version: cfg.prompt_version || 'AI_PROMPT_V2',
    prompt_file: cfg.prompt_file ||
      'research/papertrade_exec/AI_PROMPT_V2.md',
    max_budget_seconds: cfg.max_budget_seconds || 600,
  };
}

function frozenPrompt(worktreeDir, cfg) {
  // The prompt is FROZEN by file: version + sha256 recorded into every
  // opinion (a prompt change invalidates every opinion's binding).
  const p = path.join(worktreeDir, cfg.prompt_file);
  const text = fs.readFileSync(p, 'utf8');
  const m = text.match(/```\n([\s\S]*?)\n```/);
  return {
    version: cfg.prompt_version,
    sha256: sha256Hex(text),
    system: m ? m[1] : text,
  };
}

function readPending(dataRoot) {
  try {
    const p = path.join(dataRoot, 'ai_review', 'pending.json');
    const pend = JSON.parse(fs.readFileSync(p, 'utf8'));
    return Object.keys(pend || {}).map(matchID => ({
      matchID, ...pend[matchID] }));
  } catch (e) { return []; }
}

// The STRICT v2 parse: two verdicts, nothing else is actionable.
function parseV2(raw) {
  let parsed = null;
  try {
    const a = raw.indexOf('{');
    const b = raw.lastIndexOf('}');
    if (a >= 0 && b > a) parsed = JSON.parse(raw.slice(a, b + 1));
  } catch (e) { parsed = null; }
  if (!parsed || typeof parsed !== 'object') {
    return { ok: false, why: 'output not parseable as one JSON object' };
  }
  const verdict = String(parsed.verdict || '').trim().toUpperCase();
  if (!VERDICTS_V2.includes(verdict)) {
    return { ok: false,
      why: `verdict ${verdict || '(empty)'} outside {ALLOW, VETO} — `
         + 'SWITCH/CHALLENGE/ALTERNATIVE/ABSTAIN are not actionable '
         + 'under owner law' };
  }
  const codes = (parsed.reason_codes || []).map(c => String(c).slice(0, 60));
  if (!codes.length) return { ok: false, why: 'missing reason_codes' };
  const summary = String(parsed.summary || '').slice(0, 600);
  if (!summary.trim()) return { ok: false, why: 'missing summary' };
  const sources = (parsed.sources || []).map(s => ({
    url: String((s && s.url) || '').slice(0, 400),
    excerpt: String((s && s.excerpt) || '').slice(0, 280),
    fetched_at_utc: nowZ(),
  })).filter(s => s.url);
  if (verdict === 'ALLOW' && !sources.length) {
    return { ok: false,
      why: 'ALLOW with zero captured sources — insufficient evidence '
         + 'is a refusal reason, never an approval' };
  }
  return { ok: true, verdict, reason_codes: codes, summary, sources };
}

function buildUserPayload(pendingEntry, candidate, evidence) {
  return JSON.stringify({
    fixture: candidate && {
      league: candidate.league, match_id: pendingEntry.matchID,
      home: candidate.home, away: candidate.away,
      kickoff_utc: candidate.kickoffUTC, competition: candidate.competition,
    },
    chosen_leg: candidate && candidate.chosenLeg,
    frozen: {
      p: candidate && candidate.p, odds: candidate && candidate.odds,
      ev_net: candidate && candidate.evNet, stake_cents:
        candidate && candidate.stakeCents,
      note: 'FROZEN — you never change numbers, never switch legs',
    },
    candidate_hash: pendingEntry.candidate_hash,
    anchor_utc: pendingEntry.anchor_utc,
    captured_sources: (evidence.sources || []).map(s => ({
      url: s.url, excerpt: s.excerpt, published: s.published_utc || null,
      fetched_at_utc: s.fetched_at_utc })),
    evidence_note: 'These are the ONLY lawful citations; citing anything '
      + 'else is fabrication and your verdict will be discarded.',
  }, null, 1);
}

async function callProvider(cfg, apiKey, system, userPayload, https_mod) {
  // Single endpoint, the configured model, then the configured fallbacks.
  const models = [cfg.model_id, ...cfg.fallback_models];
  const errors = [];
  for (const model of models) {
    try {
      const body = JSON.stringify({
        model, temperature: 0,
        messages: [{ role: 'system', content: system },
                   { role: 'user', content: userPayload }],
      });
      const text = await new Promise((resolve, reject) => {
        const u = new URL(cfg.endpoint);
        const req = https_mod.request({
          hostname: u.hostname, path: u.pathname + u.search,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiKey}`,
          },
          timeout: 45000,
        }, res => {
          let buf = '';
          res.on('data', d => { buf += d; });
          res.on('end', () => resolve(buf));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(new Error('timeout')); });
        req.write(body); req.end();
      });
      let env = null;
      try { env = JSON.parse(text); } catch (e) { env = null; }
      const content = env && env.choices && env.choices[0]
        && env.choices[0].message
        && env.choices[0].message.content;
      if (!content) throw new Error('empty choices envelope');
      return { ok: true, model, content };
    } catch (e) {
      errors.push(`${model}: ${e.message}`);
    }
  }
  return { ok: false, errors };
}

// Collect research evidence through the RUNNER's own collector (one
// implementation, both sides): `python -m ... execute ai-evidence`.
function collectResearch(pythonBin, worktreeDir, dataRoot, sandbox, league,
                         matchID, home, away) {
  try {
    const out = execFileSync(pythonBin, [
      '-m', 'research.papertrade_exec.execute',
      '--worktree', worktreeDir,
      '--data-root', dataRoot,
      ...(sandbox ? ['--sandbox'] : []),
      'ai-evidence', '--league', String(league || ''),
      '--match-id', String(matchID),
      '--home', String(home || ''), '--away', String(away || ''),
    ], { timeout: 90000, encoding: 'utf8' });
    const a = out.indexOf('{');
    return JSON.parse(out.slice(a));
  } catch (e) {
    return { sources: [], why: `research collector failed: ${e.message}` };
  }
}

/**
 * Produce hash-locked v2 opinions for the runner's PENDING_AI queue.
 * @param opts {dataRoot, worktreeDir, pythonBin, sandbox, apiKey,
 *              candidateOf(matchID), https, fetchJson?}
 * @returns summary {reviewed, written, invalid, skipped}
 */
async function reviewPendingV2(opts) {
  const cfg = loadProviderConfig(opts.worktreeDir);
  const prompt = frozenPrompt(opts.worktreeDir, cfg);
  const pending = readPending(opts.dataRoot);
  const outDir = path.join(opts.dataRoot, 'ai_review', 'opinions_v2');
  fs.mkdirSync(outDir, { recursive: true });
  const summary = { reviewed: 0, written: 0, invalid: 0, skipped: 0,
    detail: [] };
  for (const entry of pending) {
    summary.reviewed += 1;
    const opinionPath = path.join(outDir,
      `${entry.matchID}_${entry.candidate_hash}.json`);
    if (fs.existsSync(opinionPath)) { summary.skipped += 1; continue; }
    const candidate = (opts.candidateOf || (() => null))(entry.matchID);
    const research = collectResearch(opts.pythonBin, opts.worktreeDir,
      opts.dataRoot, opts.sandbox, candidate && candidate.league,
      entry.matchID, candidate && candidate.home, candidate && candidate.away);
    const userPayload = buildUserPayload(entry, candidate, research);
    const call = await callProvider(cfg, opts.apiKey, prompt.system,
      userPayload, opts.https || require('https'));
    if (!call.ok) {
      // provider-side failure: NOT an opinion — the entry stays PENDING
      // (owner QĐ2: silence never becomes a verdict).
      summary.detail.push({ matchID: entry.matchID,
        outcome: 'PROVIDER_FAILED', errors: call.errors });
      continue;
    }
    const parsed = parseV2(call.content);
    if (!parsed.ok) {
      // store the invalid attempt under .invalid/ for the scorecard; the
      // entry stays PENDING (garbage output is never actionable).
      const badDir = path.join(outDir, '.invalid');
      fs.mkdirSync(badDir, { recursive: true });
      fs.writeFileSync(path.join(badDir,
        `${entry.matchID}_${entry.candidate_hash}.json`), JSON.stringify({
        match_id: entry.matchID, candidate_hash: entry.candidate_hash,
        invalid_why: parsed.why, raw: String(call.content).slice(0, 2000),
        model_id: call.model, prompt_version: prompt.version,
        prompt_sha256: prompt.sha256, created_at_utc: nowZ() }, null, 1));
      summary.invalid += 1;
      summary.detail.push({ matchID: entry.matchID,
        outcome: 'INVALID', why: parsed.why });
      continue;
    }
    const opinion = {
      match_id: entry.matchID,
      candidate_hash: entry.candidate_hash,
      verdict: parsed.verdict,
      reason_codes: parsed.reason_codes,
      summary: parsed.summary,
      sources: research.sources && research.sources.length
        ? research.sources.map(s => ({ url: s.url,
          fetched_at_utc: s.fetched_at_utc,
          excerpt: s.excerpt }))
        : parsed.sources,
      model_id: call.model,
      provider: cfg.provider,
      prompt_version: prompt.version,
      prompt_sha256: prompt.sha256,
      created_at_utc: nowZ(),
    };
    fs.writeFileSync(opinionPath, JSON.stringify(opinion, null, 1));
    summary.written += 1;
    summary.detail.push({ matchID: entry.matchID,
      outcome: opinion.verdict });
  }
  return summary;
}

module.exports = { VERDICTS_V2, loadProviderConfig, frozenPrompt,
  readPending, parseV2, buildUserPayload, reviewPendingV2,
  collectResearch, nowZ, sha256Hex };
