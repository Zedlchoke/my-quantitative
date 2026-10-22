'use strict';
// Byte-exact replica of the pinned ledger canonical JSON:
//   json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
// (research/papertrade/ledger.py). Verified against the runner's own
// verify_chain on the REAL ledger in the e2e battery; any drift shows up as
// a chain mismatch.
const crypto = require('crypto');

function canonicalStringify(v) {
  if (v === null || v === undefined) return 'null';
  const t = typeof v;
  if (t === 'boolean') return v ? 'true' : 'false';
  if (t === 'bigint') return String(v);            // Python int
  if (t === 'number') return pythonNumber(v);
  if (t === 'string') return pyString(v);
  if (Array.isArray(v)) return '[' + v.map(canonicalStringify).join(',') + ']';
  if (t === 'object') {
    const keys = Object.keys(v).sort();
    return '{' + keys.map(k => pyString(k) + ':' + canonicalStringify(v[k]))
      .join(',') + '}';
  }
  throw new Error('unsupported type ' + t);
}

// Python json string escaping (ensure_ascii=True): named escapes for
// " \ \n \r \t; \uXXXX (lowercase) for other control chars and ALL non-ASCII,
// astral plane as surrogate pairs.
function pyString(s) {
  let out = '"';
  for (const ch of s) {
    const c = ch.codePointAt(0);
    if (ch === '"') out += '\\"';
    else if (ch === '\\') out += '\\\\';
    else if (ch === '\n') out += '\\n';
    else if (ch === '\r') out += '\\r';
    else if (ch === '\t') out += '\\t';
    else if (c < 0x20) out += '\\u' + c.toString(16).padStart(4, '0');
    else if (c <= 0x7f) out += ch;
    else if (c > 0xffff) {
      const v = c - 0x10000;
      const hi = 0xd800 + (v >> 10), lo = 0xdc00 + (v & 0x3ff);
      out += '\\u' + hi.toString(16).padStart(4, '0') +
        '\\u' + lo.toString(16).padStart(4, '0');
    } else out += '\\u' + c.toString(16).padStart(4, '0');
  }
  return out + '"';
}

// repr(float) semantics (pyfloat.c): shortest round-trip digits, fixed
// notation for -4 <= exp10 < 16 (at least one fractional digit, "2.0"),
// scientific otherwise ("9.553106207984066e-05", 2+ exponent digits).
function pythonNumber(n) {
  if (n === 0) return Object.is(n, -0) ? '-0.0' : '0.0';
  if (Number.isInteger(n) && Math.abs(n) < 1e16) return String(n) + '.0';
  const es = n.toExponential();            // shortest digits form
  const [mant0, expStr] = es.split('e');
  const exp = parseInt(expStr, 10);
  const digits = mant0.replace(/^-/, '').replace('.', '')
    .replace(/0+$/, '') || '0';
  const sign = n < 0 ? '-' : '';
  if (exp >= 16 || exp <= -5) {
    const m = digits.length > 1
      ? digits[0] + '.' + digits.slice(1) : digits[0];
    let e = String(Math.abs(exp));
    if (e.length < 2) e = '0' + e;
    return sign + m + 'e' + (exp < 0 ? '-' : '+') + e;
  }
  if (exp >= 0) {
    const intPart = digits.slice(0, exp + 1).padEnd(exp + 1, '0');
    const frac = digits.slice(exp + 1);
    return sign + intPart + '.' + (frac || '0');
  }
  return sign + '0.' + '0'.repeat(-exp - 1) + digits;
}

function sha256Hex(s) {
  return crypto.createHash('sha256').update(s, 'utf8').digest('hex');
}

function rowSha256(row) {
  const copy = Object.assign({}, row);
  delete copy.row_sha256;
  return sha256Hex(canonicalStringify(copy));
}

// ---- typed JSON parse: preserves Python's int vs float distinction -------
// JS Number cannot; ledger rows hash over ints (e.g. wallet_cents: 100000)
// vs floats (e.g. p: 0.8243) differently, so the ledger path uses this
// parser: integer literals -> BigInt, everything else standard.
function jsonParseTyped(text) {
  let i = 0;
  const n = text.length;
  function err(msg) { throw new Error(`jsonParseTyped @${i}: ${msg}`); }
  function ws() { while (i < n && /\s/.test(text[i])) i++; }
  function value() {
    ws();
    if (i >= n) err('eof');
    const c = text[i];
    if (c === '{') return obj();
    if (c === '[') return arr();
    if (c === '"') return str();
    if (c === 't') { expect('true'); return true; }
    if (c === 'f') { expect('false'); return false; }
    if (c === 'n') { expect('null'); return null; }
    return num();
  }
  function expect(word) {
    if (text.slice(i, i + word.length) !== word) err(`expected ${word}`);
    i += word.length;
  }
  function obj() {
    i++; ws();
    const o = {};
    if (text[i] === '}') { i++; return o; }
    for (;;) {
      ws();
      if (text[i] !== '"') err('key');
      const k = str();
      ws();
      if (text[i] !== ':') err(':');
      i++;
      o[k] = value();
      ws();
      if (text[i] === ',') { i++; continue; }
      if (text[i] === '}') { i++; return o; }
      err('object');
    }
  }
  function arr() {
    i++; ws();
    const a = [];
    if (text[i] === ']') { i++; return a; }
    for (;;) {
      a.push(value());
      ws();
      if (text[i] === ',') { i++; continue; }
      if (text[i] === ']') { i++; return a; }
      err('array');
    }
  }
  function str() {
    // JSON string with escapes; ledger strings are plain ASCII+unicode
    const out = [];
    i++;                          // opening quote
    while (i < n) {
      const c = text[i];
      if (c === '"') { i++; return out.join(''); }
      if (c === '\\') {
        const d = text[i + 1];
        i += 2;
        if (d === 'u') {
          const hex = text.slice(i, i + 4);
          out.push(String.fromCharCode(parseInt(hex, 16)));
          i += 4;
        } else {
          out.push(({ '"': '"', '\\': '\\', '/': '/', b: '\b',
            f: '\f', n: '\n', r: '\r', t: '\t' })[d] ?? d);
        }
        continue;
      }
      out.push(c);
      i++;
    }
    err('string');
  }
  function num() {
    const start = i;
    if (text[i] === '-' || text[i] === '+') i++;
    let isInt = true;
    while (i < n && /[0-9.eE+-]/.test(text[i])) {
      if ('.eE'.includes(text[i])) isInt = false;
      i++;
    }
    const lit = text.slice(start, i);
    if (!lit.length || lit === '-' || lit === '+') err('number');
    return isInt ? BigInt(lit) : Number(lit);
  }
  const v = value();
  ws();
  if (i !== n) err('trailing');
  return v;
}

// Deep BigInt -> Number for UI payloads (ledger amounts are far below 2^53).
function sanitizeBigInt(v) {
  if (typeof v === 'bigint') return Number(v);
  if (Array.isArray(v)) return v.map(sanitizeBigInt);
  if (v && typeof v === 'object') {
    const o = {};
    for (const k of Object.keys(v)) o[k] = sanitizeBigInt(v[k]);
    return o;
  }
  return v;
}

module.exports = { canonicalStringify, sha256Hex, rowSha256, pythonNumber,
                   jsonParseTyped, sanitizeBigInt };
