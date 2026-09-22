// Cross-language golden vectors — A7-1 F1 (CRITICAL) regression proof.
//
// amendment_1 (producer-digest echo law): input_digest is computed by the
// PYTHON producer (json.dumps sort_keys canonicalization) and echoed verbatim
// by the TS adapter. These vectors use exponent-notation doubles from the
// measured divergence window: Python renders 1e-05 / 1.234e-07 / 5e-06 /
// 34.0, while TS JSON.stringify renders 0.00001 / 1.234e-7 / 0.000005 / 34 —
// so the OLD TS-side recompute produced DIFFERENT sha256 digests for the same
// state (audit measurement: 10/25 real request lines, 40%). The echo path is
// immune by construction; these tests pin both halves of that claim.
//
// The canonical strings and digests below were produced by the producer
// authority:
//   canonical_json = json.dumps(state, sort_keys=True, separators=(",",":"),
//                                ensure_ascii=True)
//   input_digest   = sha256(canonical_json(state) || requested_model) hex

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  canonicalJson,
  computeCacheKey,
  computeInputDigest,
  validateRequestLine,
} from "../src/contract.ts";
import { listDir, runAdapter, tmpDir, writeRequests } from "./helpers.ts";
import { initPromptDigest } from "../src/prompt.ts";
initPromptDigest();

interface GoldenVector {
  id: string;
  state: { feature_vector: number[]; prior_regime: string | null };
  requested_model: string;
  python_canonical_json: string;
  python_input_digest: string;
}

const GOLDEN_VECTORS: GoldenVector[] = [
  {
    id: "G1_1e_05",
    state: {
      feature_vector: [1e-05, 0.02, 0.05, 0.11, 0.28, 0.004, 0.0025, 1.2, 34.0, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62],
      prior_regime: null,
    },
    requested_model: "mock-pin-1",
    python_canonical_json:
      '{"feature_vector":[1e-05,0.02,0.05,0.11,0.28,0.004,0.0025,1.2,34.0,0.008,0.62,-0.03,0.3,0.42,0.35,0.62],"prior_regime":null}',
    python_input_digest: "6c8c858c93301d154db1a982f8f82e8a5ac488ab1a30ebf2f53c76fbb4fda7b7",
  },
  {
    id: "G2_1_234e_07",
    state: {
      feature_vector: [0.01, 1.234e-07, 0.05, 0.11, 0.28, 0.004, 0.0025, 1.2, 34.0, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62],
      prior_regime: "UPTREND",
    },
    requested_model: "mock-pin-1",
    python_canonical_json:
      '{"feature_vector":[0.01,1.234e-07,0.05,0.11,0.28,0.004,0.0025,1.2,34.0,0.008,0.62,-0.03,0.3,0.42,0.35,0.62],"prior_regime":"UPTREND"}',
    python_input_digest: "9442cc80180fdf6ff0fd6167537f5b17af93c0425fafbf19c162fff192c85b59",
  },
  {
    id: "G3_5e_06_neg",
    state: {
      feature_vector: [0.01, 0.02, 0.05, 0.11, 0.28, 5e-06, -1.234e-07, 1.2, 34.0, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62],
      prior_regime: null,
    },
    requested_model: "mock-pin-1",
    python_canonical_json:
      '{"feature_vector":[0.01,0.02,0.05,0.11,0.28,5e-06,-1.234e-07,1.2,34.0,0.008,0.62,-0.03,0.3,0.42,0.35,0.62],"prior_regime":null}',
    python_input_digest: "53e07db17238e95fbf74e58b879608a14c75aa1d40b24d49864496c5aabc9974",
  },
];

test("golden: TS canonicalization DIVERGED from the producer for every vector", () => {
  for (const v of GOLDEN_VECTORS) {
    assert.notEqual(
      canonicalJson(v.state),
      v.python_canonical_json,
      `${v.id}: TS canonicalJson must differ from the Python canonical string (this divergence is why recompute was removed)`,
    );
    assert.notEqual(
      computeInputDigest(v.state, v.requested_model),
      v.python_input_digest,
      `${v.id}: the OLD TS recompute must produce a different digest (A7-1 F1 measured divergence)`,
    );
  }
});

test("golden: producer request lines validate under the echo schema", () => {
  for (const v of GOLDEN_VECTORS) {
    const line = JSON.parse(
      JSON.stringify({
        schema: "jrv1_decision_io@1",
        state_id: "0123456789abcdef",
        state: v.state,
        requested_model: v.requested_model,
        input_digest: v.python_input_digest,
      }),
    );
    const check = validateRequestLine(line);
    assert.equal(check.ok, true, `${v.id}: valid producer line must be accepted`);
    if (check.ok) assert.equal(check.request.input_digest, v.python_input_digest);
    // and a tampered digest is refused at the format gate
    const bad = { ...line, input_digest: v.python_input_digest.slice(0, 63) };
    assert.equal(validateRequestLine(bad).ok, false);
  }
});

test("golden: adapter ECHOES the producer digest (mock end-to-end via subprocess)", () => {
  const dir = tmpDir();
  const lines = GOLDEN_VECTORS.map((v, i) => {
    const sid = (i + 1).toString(16).padStart(16, "0");
    return JSON.stringify({
      schema: "jrv1_decision_io@1",
      state_id: sid,
      state: v.state,
      requested_model: v.requested_model,
      input_digest: v.python_input_digest,
    });
  });
  const req = writeRequests(dir, lines);
  const out = join(dir, "out.jsonl");
  const cache = join(dir, "cache");
  const model = "mock-pin-1";
  const r = runAdapter(["--requests", req, "--out", out, "--cache", cache, "--model", model, "--mock"]);
  assert.equal(r.status, 0, r.stderr);

  const rows = (readFileSync(out, "utf8").trim().split("\n").map((l) => JSON.parse(l))) as Array<{
    state_id: string;
    status: string;
    input_digest: string;
  }>;
  assert.equal(rows.length, GOLDEN_VECTORS.length);
  for (const [i, v] of GOLDEN_VECTORS.entries()) {
    assert.equal(rows[i].status, "OK");
    assert.equal(
      rows[i].input_digest,
      v.python_input_digest,
      `${v.id}: response must echo the producer digest verbatim (immune to float formatting)`,
    );
    // the cache key derives from the ECHOED digest
    const sid = (i + 1).toString(16).padStart(16, "0");
    const expectedKey = computeCacheKey(model, sid, v.python_input_digest);
    assert.ok(
      listDir(cache).includes(`${expectedKey}.json`),
      `${v.id}: cache entry must be keyed by the producer digest`,
    );
    const entry = JSON.parse(readFileSync(join(cache, `${expectedKey}.json`), "utf8"));
    assert.equal(entry.input_digest, v.python_input_digest);
  }

  // replay from cache: identical digests, zero recompute, zero new entries
  const before = listDir(cache);
  const out2 = join(dir, "out2.jsonl");
  const r2 = runAdapter(["--requests", req, "--out", out2, "--cache", cache, "--model", model, "--mock"]);
  assert.equal(r2.status, 0, r2.stderr);
  assert.deepEqual(listDir(cache), before);
  const rows2 = (readFileSync(out2, "utf8").trim().split("\n").map((l) => JSON.parse(l))) as Array<{
    cached: boolean;
    input_digest: string;
  }>;
  for (const [i, v] of GOLDEN_VECTORS.entries()) {
    assert.equal(rows2[i].cached, true);
    assert.equal(rows2[i].input_digest, v.python_input_digest);
  }
});
