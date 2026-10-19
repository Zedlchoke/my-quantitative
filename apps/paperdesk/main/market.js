'use strict';
// Health + market data. HealthStore polls the runner's GET-only /api/state;
// PolymarketProvider is the read-only MarketDataProvider seam: public Gamma/
// CLOB GETs only, every response recorded (url, retrieval UTC, sha256) under
// <data-root>/pm_ui_snapshots/. There is NO write path to any venue.
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function nowZ() { return new Date().toISOString().replace(/\.\d+Z$/, 'Z'); }

class HealthStore {
  constructor() {
    this.liveState = null;
    this.liveFetchError = null;
    this.liveLastOK = null;
    this.pmProbe = null;
    this.port = 8791;
  }

  fetchState(port) {
    const p = port || this.port;
    return new Promise(resolve => {
      const req = http.get(
        { host: '127.0.0.1', port: p, path: '/api/state', timeout: 5000 },
        res => {
          let buf = '';
          res.on('data', d => { buf += d; });
          res.on('end', () => {
            if (res.statusCode !== 200) {
              this.liveFetchError = `HTTP ${res.statusCode}`;
              return resolve(null);
            }
            try {
              this.liveState = JSON.parse(buf);
              this.liveFetchError = null;
              this.liveLastOK = Date.now();
              if (this.liveState.service && this.liveState.service.port) {
                this.port = this.liveState.service.port;
              }
              resolve(this.liveState);
            } catch (e) {
              this.liveFetchError = 'malformed /api/state JSON';
              resolve(null);
            }
          });
        });
      req.on('timeout', () => { req.destroy(); });
      req.on('error', e => {
        this.liveFetchError = e.message;
        resolve(null);
      });
    });
  }

  probePolymarket() {
    return new Promise(resolve => {
      const t0 = Date.now();
      const req = https.get(
        'https://gamma-api.polymarket.com/events?limit=1&closed=false',
        { timeout: 8000 }, res => {
          res.resume();
          res.on('end', () => {
            this.pmProbe = { at: Date.now(),
                             ok: res.statusCode === 200,
                             statusText: `HTTP ${res.statusCode}`,
                             latencyMs: Date.now() - t0 };
            resolve(this.pmProbe);
          });
        });
      req.on('timeout', () => { req.destroy(); });
      req.on('error', e => {
        this.pmProbe = { at: Date.now(), ok: false,
                         statusText: e.message, latencyMs: -1 };
        resolve(this.pmProbe);
      });
    });
  }
}

class PolymarketProvider {
  // MarketDataProvider seam — READ-ONLY. No auth headers exist in this file,
  // no POST/PUT is constructed anywhere; the sealed LiveExecution lives in
  // seal.js and refuses.
  constructor(snapshotDir) {
    this.snapshotDir = snapshotDir;
    this.snapshots = [];
    this.journalFailures = 0;   // surfaced by the UI health page
    this.lastEvents = [];       // cached display payload (fresh <120s)
    this.lastEventsAt = 0;
    this.lastShaByKind = {};    // kind -> latest body sha256
    this._seq = 0;
  }

  /// Latest journaled body sha for a kind (used by the AI evidence capture
  /// to cite system-captured provenance).
  lastSnapshotSha(kind) { return this.lastShaByKind[kind] || null; }

  record(kind, url, body, status, note) {
    const sha = body
      ? crypto.createHash('sha256').update(body, 'utf8').digest('hex')
      : 'NO_BODY';
    if (body) this.lastShaByKind[kind] = sha;
    const rec = { at_utc: nowZ(), kind, url, sha256: sha, status,
                  note: note || null };
    this.snapshots.push(rec);
    if (!this.snapshotDir) return;
    try {
      fs.mkdirSync(this.snapshotDir, { recursive: true });
      if (body) {
        // unique + content-addressed name: same-second double fetches and
        // identical payloads can never overwrite journaled bytes
        this._seq += 1;
        const stamp = nowZ().replace(/[-:]/g, '').replace('Z', '');
        fs.writeFileSync(path.join(this.snapshotDir,
          `${stamp}_${String(this._seq).padStart(6, '0')}`
          + `_${kind}_${sha.slice(0, 12)}.json`), body);
      }
      fs.appendFileSync(path.join(this.snapshotDir, 'snapshots.jsonl'),
        JSON.stringify(rec) + '\n');
    } catch (e) {
      // journaling failures are counted and surfaced, never silent
      this.journalFailures += 1;
      console.error('pm snapshot journal failure #' + this.journalFailures,
                    e.message);
    }
  }

  httpsGet(url, kind) {
    return new Promise(resolve => {
      const req = https.get(url, { timeout: 10000 }, res => {
        let buf = '';
        res.on('data', d => { buf += d; });
        res.on('end', () => {
          if (res.statusCode !== 200) {
            this.record(kind, url, null, res.statusCode, 'non-200');
            return resolve(null);
          }
          this.record(kind, url, buf, 200);
          try { resolve(JSON.parse(buf)); } catch (e) { resolve(null); }
        });
      });
      req.on('timeout', () => { req.destroy(); });
      req.on('error', e => {
        this.record(kind, url, null, null, e.message);
        resolve(null);
      });
    });
  }

  async fetchEventsForDisplay(limit = 40) {
    if (Date.now() - this.lastEventsAt < 120000
        && this.lastEvents.length) return this.lastEvents;
    const data = await this.httpsGet(
      `https://gamma-api.polymarket.com/events?closed=false&limit=${limit}`
      + '&order=endDate&ascending=true', 'gamma_events');
    if (!data || !Array.isArray(data)) return [];
    const events = data.map(e => ({
      id: e.id, title: e.title, slug: e.slug, endDate: e.endDate,
      markets: (e.markets || []).slice(0, 12).map(m => ({
        id: m.id, question: m.question, closed: m.closed,
        active: m.active, outcomes: m.outcomes,
        clobTokenIds: m.clobTokenIds })),
    }));
    this.lastEvents = events;
    this.lastEventsAt = Date.now();
    return events;
  }

  async fetchBook(tokenID) {
    const data = await this.httpsGet(
      `https://clob.polymarket.com/book?token_id=${encodeURIComponent(tokenID)}`,
      'clob_book');
    if (!data || !Array.isArray(data.asks)) return null;
    return { tokenID,
             asks: data.asks.map(a => ({ price: Number(a.price),
                                         size: Number(a.size) }))
               .sort((a, b) => a.price - b.price) };
  }
}

module.exports = { HealthStore, PolymarketProvider };
