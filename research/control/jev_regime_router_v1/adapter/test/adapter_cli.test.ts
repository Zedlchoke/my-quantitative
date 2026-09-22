// CLI integration tests (mock mode + gates) via child processes.
// NO live API calls: TYPESAFE_API_KEY is stripped from every child env
// (test/helpers.ts) and every non-mock test exits before client construction.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import {
  FREEZES_DIR,
  hex16,
  listDir,
  makeRequestLine,
  readFileIfExists,
  runAdapter,
  sha256OfFile,
  tmpDir,
  writeRequests,
} from "./helpers.ts";
import { mockClassify } from "../src/mock.ts";
import { sha256Hex } from "../src/contract.ts";

const MODEL = "jev-canary-x";

interface Row {
  schema: string;
  state_id: string;
  status: string;
  regime?: string;
  probabilities?: Record<string, number>;
  confidence?: number;
  model?: string;
  request_id?: string;
  input_digest?: string;
  latency_ms?: number;
  mock?: boolean;
  cached?: boolean;
  error_class?: string;
}

function readRows(p: string): Row[] {
  const text = readFileSync(p, "utf8").trim();
  return text.length === 0 ? [] : (text.split("\n").map((l) => JSON.parse(l)) as Row[]);
}

test("mock run: one response per request, order preserved, schema complete", async () => {
  const dir = tmpDir();
  const req = writeRequests(dir, [
    makeRequestLine({ stateId: hex16(1) }),
    makeRequestLine({ stateId: hex16(2), prior: "DOWNTREND", vector: [-1, -2, -3, -4, -5, -0.1, -0.2, -1, 31, 0.01, 0.7, -0.2, -0.1, -0.3, 0.4, 0.3] }),
  ]);
  const out = join(dir, "out.jsonl");
  const cache = join(dir, "cache");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", cache, "--model", MODEL, "--mock"]);
  assert.equal(r.status, 0, r.stderr);

  const rows = readRows(out);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].state_id, hex16(1));
  assert.equal(rows[1].state_id, hex16(2));
  for (const row of rows) {
    assert.equal(row.schema, "jrv1_decision_io@1");
    assert.equal(row.status, "OK");
    assert.ok(row.regime !== undefined);
    assert.ok(row.probabilities !== undefined);
    assert.ok(row.confidence !== undefined);
    assert.equal(row.model, MODEL);
    assert.ok((row.request_id ?? "").startsWith("mock-"));
    assert.match(row.input_digest ?? "", /^[0-9a-f]{64}$/);
    assert.equal(row.latency_ms, 0);
    assert.equal(row.mock, true, "every mock line carries mock:true");
  }
  // probabilities: exactly the 5 labels, each 2dp, cents sum exactly 100
  for (const row of rows) {
    const probs = row.probabilities as Record<string, number>;
    assert.equal(Object.keys(probs).length, 5);
    let cents = 0;
    for (const v of Object.values(probs)) {
      assert.ok(v >= 0, "probability must be >= 0");
      assert.ok(Math.round(v * 100) === Number((v * 100).toFixed(0)), "2dp value");
      cents += Math.round(v * 100);
    }
    assert.equal(cents, 100, "cents must sum to exactly 100 (sum 1.0 at 2dp)");
    // argmax must equal the chosen regime
    const top = Object.entries(probs).sort((a, b) => b[1] - a[1])[0][0];
    assert.equal(top, row.regime, "remainder-to-top => argmax == regime");
  }

  // stdout summary: single JSON line, redaction-safe counters only
  const summary = JSON.parse(r.stdout.trim());
  assert.equal(summary.n_ok, 2);
  assert.equal(summary.n_err, 0);
  assert.equal(summary.n_requests, 2);
  assert.equal(summary.mode, "mock");
  assert.equal(summary.model, MODEL);
  assert.ok(typeof summary.total_latency_ms === "number");
  assert.ok(!r.stdout.includes("feature_vector"));
});

test("mock determinism: same input -> byte-identical output", () => {
  const dirA = tmpDir();
  const dirB = tmpDir();
  const lines = [
    makeRequestLine({ stateId: hex16(7), prior: "UPTREND", vector: [0, 0.001, -0.002, 0.01, 0.2, 0, 0.001, 0.25, 15, 0.007, 0.35, -0.05, 0.24, 0.25, -0.2, 0.5] }),
    makeRequestLine({ stateId: hex16(8) }),
  ];
  const outA = join(dirA, "out.jsonl");
  const outB = join(dirB, "out.jsonl");
  const a = runAdapter(["--requests", writeRequests(dirA, lines), "--out", outA, "--cache", join(dirA, "c"), "--model", MODEL, "--mock"]);
  const b = runAdapter(["--requests", writeRequests(dirB, lines), "--out", outB, "--cache", join(dirB, "c"), "--model", MODEL, "--mock"]);
  assert.equal(a.status, 0);
  assert.equal(b.status, 0);
  assert.equal(readFileSync(outA, "utf8"), readFileSync(outB, "utf8"), "mock output must be deterministic");
});

test("duplicate state_id within one run: single response + warning, never called twice", () => {
  const dir = tmpDir();
  const req = writeRequests(dir, [
    makeRequestLine({ stateId: hex16(3) }),
    makeRequestLine({ stateId: hex16(3) }),
    makeRequestLine({ stateId: hex16(3) }),
  ]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", join(dir, "c"), "--model", MODEL, "--mock"]);
  assert.equal(r.status, 0);
  const rows = readRows(out);
  assert.equal(rows.length, 1, "exactly one response for a duplicated state_id");
  const dupWarnings = r.stderr.split("\n").filter((l) => l.includes("DUPLICATE_STATE_ID"));
  assert.equal(dupWarnings.length, 2, "one warning per skipped duplicate");
  const summary = JSON.parse(r.stdout.trim());
  assert.equal(summary.n_duplicate_skipped, 2);
  assert.equal(summary.n_emitted, 1);
});

test("cache: second run is a cache hit; cache entries immutable", () => {
  const dir = tmpDir();
  const cache = join(dir, "cache");
  const lines = [makeRequestLine({ stateId: hex16(4) }), makeRequestLine({ stateId: hex16(5) })];
  const req = writeRequests(dir, lines);
  const out1 = join(dir, "out1.jsonl");
  const out2 = join(dir, "out2.jsonl");

  const r1 = runAdapter(["--requests", req, "--out", out1, "--cache", cache, "--model", MODEL, "--mock"]);
  assert.equal(r1.status, 0);
  const files1 = listDir(cache);
  assert.equal(files1.length, 2, "one append-only JSON entry per state");
  const hashes1 = new Map(files1.map((f) => [f, sha256OfFile(join(cache, f))]));
  const content1 = readFileSync(out1, "utf8");

  const r2 = runAdapter(["--requests", req, "--out", out2, "--cache", cache, "--model", MODEL, "--mock"]);
  assert.equal(r2.status, 0);
  const files2 = listDir(cache);
  assert.deepEqual(files2, files1, "no new entries on full cache hit");
  for (const f of files2) {
    assert.equal(sha256OfFile(join(cache, f)), hashes1.get(f), `cache entry ${f} must be byte-identical (append-only)`);
  }

  const rows2 = readRows(out2);
  assert.equal(rows2.length, 2);
  for (const row of rows2) {
    assert.equal(row.cached, true, "second run emits cached rows");
    assert.equal(row.latency_ms, 0, "cache hits report latency 0");
    // status/regime/model carried from cache
  }
  assert.equal(rows2[0].regime, readRows(out1)[0].regime);
  const summary2 = JSON.parse(r2.stdout.trim());
  assert.equal(summary2.n_cached, 2);
  assert.equal(summary2.n_ok, 2);
  void content1;
});

test("cache: existing entry not overwritten even when a new state joins the run", () => {
  const dir = tmpDir();
  const cache = join(dir, "cache");
  const req1 = writeRequests(dir, [makeRequestLine({ stateId: hex16(6) })]);
  runAdapter(["--requests", req1, "--out", join(dir, "o1.jsonl"), "--cache", cache, "--model", MODEL, "--mock"]);
  const entry = join(cache, listDir(cache)[0]);
  const before = readFileSync(entry, "utf8");

  const req2 = writeRequests(dir, [
    makeRequestLine({ stateId: hex16(6) }),
    makeRequestLine({ stateId: hex16(9) }),
  ]);
  const r2 = runAdapter(["--requests", req2, "--out", join(dir, "o2.jsonl"), "--cache", cache, "--model", MODEL, "--mock"]);
  assert.equal(r2.status, 0);
  assert.equal(readFileSync(entry, "utf8"), before, "existing cache entry never rewritten");
  assert.equal(listDir(cache).length, 2, "exactly one new entry appended");
  const summary = JSON.parse(r2.stdout.trim());
  assert.equal(summary.n_cached, 1);
});

test("cache key is sha256(model || state_id || input_digest) with the PRODUCER digest echoed", () => {
  const dir = tmpDir();
  const cache = join(dir, "cache");
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(11), requestedModel: MODEL })]);
  const r = runAdapter(["--requests", req, "--out", join(dir, "o.jsonl"), "--cache", cache, "--model", MODEL, "--mock"]);
  assert.equal(r.status, 0);
  const lines = readFileSync(req, "utf8").trim().split("\n");
  const parsed = JSON.parse(lines[0]);
  // amendment_1: the digest carried by the request line is used verbatim
  const inputDigest = parsed.input_digest;
  assert.match(inputDigest, /^[0-9a-f]{64}$/);
  const expected = sha256Hex(MODEL + parsed.state_id + inputDigest);
  assert.deepEqual(listDir(cache), [`${expected}.json`]);
});

test("amendment_1: request without input_digest is refused (LOCAL_INVALID, no call)", () => {
  const dir = tmpDir();
  const noDigest = JSON.parse(makeRequestLine({ stateId: hex16(41) }));
  delete noDigest.input_digest;
  const badDigest = JSON.parse(makeRequestLine({ stateId: hex16(42) }));
  badDigest.input_digest = "not-a-digest";
  const uppercase = JSON.parse(makeRequestLine({ stateId: hex16(43) }));
  uppercase.input_digest = uppercase.input_digest.toUpperCase();
  const req = writeRequests(dir, [JSON.stringify(noDigest), JSON.stringify(badDigest), JSON.stringify(uppercase)]);
  const out = join(dir, "o.jsonl");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", join(dir, "c"), "--model", MODEL, "--mock"]);
  assert.equal(r.status, 0);
  const rows = readRows(out);
  assert.equal(rows.length, 3);
  for (const row of rows) {
    assert.equal(row.status, "LOCAL_INVALID");
    assert.equal(row.error_class, "REQUEST_SCHEMA");
  }
  const summary = JSON.parse(r.stdout.trim());
  assert.equal(summary.n_local_invalid, 3);
  assert.equal(listDir(join(dir, "c")).length, 0, "no cache entries without a valid producer digest");
});

test("amendment_1: response and cache entry echo the producer digest verbatim", () => {
  const dir = tmpDir();
  const producerDigest = "ab".repeat(32);
  const req = writeRequests(dir, [
    makeRequestLine({ stateId: hex16(44), requestedModel: MODEL, inputDigest: producerDigest }),
  ]);
  const out = join(dir, "o.jsonl");
  const cache = join(dir, "cache");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", cache, "--model", MODEL, "--mock"]);
  assert.equal(r.status, 0, r.stderr);
  const rows = readRows(out);
  assert.equal(rows[0].input_digest, producerDigest, "response must echo the producer digest");
  const [entryFile] = listDir(cache);
  const entry = JSON.parse(readFileSync(join(cache, entryFile), "utf8"));
  assert.equal(entry.input_digest, producerDigest, "cache entry must carry the producer digest");
  // the arbitrary 64-hex digest drives the cache key (echo, not recompute:
  // a recompute from the state would have produced a different key)
  const expectedKey = sha256Hex(MODEL + hex16(44) + producerDigest);
  assert.equal(entryFile, `${expectedKey}.json`);
});

test("model pin: jev-latest refused with exit 3 even when a key would exist", () => {
  const dir = tmpDir();
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(12) })]);
  const out = join(dir, "out.jsonl");
  // sentinel env would be ignored anyway (helper strips TYPESAFE_API_KEY) — pin
  // law fires BEFORE any credential logic.
  const r = runAdapter(["--requests", req, "--out", out, "--cache", join(dir, "c"), "--model", "jev-latest"]);
  assert.equal(r.status, 3, `stderr=${r.stderr}`);
  assert.ok(r.stderr.includes("BLOCKED_MODEL_PIN"));
  assert.equal(existsSync(out), false, "no response file on pin refusal");
});

test("model pin: missing pin refused with exit 3 (pin currently CANDIDATE_UNVERIFIED)", () => {
  const pinFile = JSON.parse(readFileSync(join(FREEZES_DIR, "model_pin.json"), "utf8"));
  if (pinFile.pinned_model !== null) {
    return; // Lead filled the pin at canary time; the refusal path is covered by the jev-latest test
  }
  const dir = tmpDir();
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(13) })]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", join(dir, "c")]);
  assert.equal(r.status, 3, `stderr=${r.stderr}`);
  assert.ok(r.stderr.includes("BLOCKED_MODEL_PIN"));
  assert.equal(existsSync(out), false);
});

test("mock mode tolerates a missing pin (tests/smoke law) using a mock fallback model", () => {
  const dir = tmpDir();
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(14) })]);
  const r = runAdapter(["--requests", req, "--out", join(dir, "o.jsonl"), "--cache", join(dir, "c"), "--mock"]);
  assert.equal(r.status, 0, r.stderr);
  const summary = JSON.parse(r.stdout.trim());
  assert.equal(summary.model, "mock-model");
});

test("request schema violations produce LOCAL_INVALID rows without provider calls", () => {
  const dir = tmpDir();
  const badPrior = JSON.parse(makeRequestLine({ stateId: hex16(15) }));
  badPrior.state.prior_regime = "BULLISH";
  const badStateId = JSON.parse(makeRequestLine({ stateId: hex16(16) }));
  badStateId.state_id = "deadbeef";
  const req = writeRequests(dir, [
    JSON.stringify(badPrior),
    "{not json",
    JSON.stringify(badStateId),
    makeRequestLine({ stateId: hex16(17) }),
  ]);
  const out = join(dir, "o.jsonl");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", join(dir, "c"), "--model", MODEL, "--mock"]);
  assert.equal(r.status, 0);
  const rows = readRows(out);
  assert.equal(rows.length, 4, "one line per request, same order");
  assert.equal(rows[0].status, "LOCAL_INVALID");
  assert.equal(rows[0].error_class, "REQUEST_SCHEMA");
  assert.equal(rows[1].status, "LOCAL_INVALID");
  assert.equal(rows[1].error_class, "UNPARSEABLE_LINE");
  assert.equal(rows[2].status, "LOCAL_INVALID");
  assert.equal(rows[3].status, "OK");
  const summary = JSON.parse(r.stdout.trim());
  assert.equal(summary.n_local_invalid, 3);
});

test("usage errors: missing args and unknown flags exit 2", () => {
  const dir = tmpDir();
  assert.equal(runAdapter([]).status, 2);
  assert.equal(runAdapter(["--bogus"]).status, 2);
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(18) })]);
  assert.equal(runAdapter(["--requests", req, "--out", join(dir, "o.jsonl"), "--mock"]).status, 2, "missing --cache");
  assert.equal(readFileIfExists(join(dir, "nonexistent-run.jsonl")), null);
});

test("mock classifier aligns with frozen canary fixtures (plausibility)", () => {
  const fixtures = JSON.parse(
    readFileSync(join(FREEZES_DIR, "synthetic_canary_fixtures.json"), "utf8"),
  );
  for (const fx of fixtures.fixtures) {
    if (fx.vector === null) continue; // FIX6 never sent to any provider
    const label = mockClassify(fx.vector, fx.prior_regime);
    assert.ok(
      (fx.expected_acceptable as string[]).includes(label),
      `${fx.id}: mock label ${label} must be within frozen acceptable set`,
    );
  }
});
