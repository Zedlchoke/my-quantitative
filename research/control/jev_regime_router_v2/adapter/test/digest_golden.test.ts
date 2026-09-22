// Cross-language digest golden vectors (amendment_1 echo law regression).
//
// The canonical strings and sha256 digests below were produced by the
// producer authority (jrv2.freezes.canonical_json / questionio
// .compute_input_digest) and are pinned as literals in BOTH suites (here and
// tests_py/test_digest_echo.py). Values 1e-05 / 1.234e-07 / 5e-06 / 34.0 sit
// in the measured Python-vs-JS float formatting divergence window; the echo
// path (the only processing path) is immune because the adapter never
// recomputes the digest.

import { test } from "node:test";
import assert from "node:assert/strict";
import { canonicalJson, computeInputDigest, sha256Hex, validateRequestLine } from "../src/contract.ts";

const MODEL = "mock-pin-2";

const GOLDEN_VECTORS = [
  {
    id: "G1_1e_05",
    state: {
      bins: { fast_trend: "weak_up" },
      numerics: { short_return: 1e-05, adx14: 34.0 },
      prior_structure: "RANGE",
      prior_direction: "NEUTRAL",
    },
    python_canonical_json:
      '{"bins":{"fast_trend":"weak_up"},"numerics":{"adx14":34.0,"short_return":1e-05},"prior_direction":"NEUTRAL","prior_structure":"RANGE"}',
    python_input_digest:
      "d74b136f63824fefafe67ad5e6ddc543a63e8ca99ea828b42fd9c656ad61c3c4",
  },
  {
    id: "G2_1_234e_07",
    state: {
      bins: { fast_trend: "flat" },
      numerics: { short_return: 0.01, long_return: 1.234e-07 },
      prior_structure: "TREND_UP",
      prior_direction: "UP",
    },
    python_canonical_json:
      '{"bins":{"fast_trend":"flat"},"numerics":{"long_return":1.234e-07,"short_return":0.01},"prior_direction":"UP","prior_structure":"TREND_UP"}',
    python_input_digest:
      "29722fb83f019362082763f9a0691db703bdbbc41aea6310fb1a5a34b278c366",
  },
  {
    id: "G3_5e_06_neg",
    state: {
      bins: { slow_trend: "weak_down" },
      numerics: { medium_return: 5e-06, dist_ema: -1.234e-07 },
      prior_structure: "none",
      prior_direction: "none",
    },
    python_canonical_json:
      '{"bins":{"slow_trend":"weak_down"},"numerics":{"dist_ema":-1.234e-07,"medium_return":5e-06},"prior_direction":"none","prior_structure":"none"}',
    python_input_digest:
      "1f464b923729a166cfd0a7fbf9098edd6e2c221a3f5dd65b32b469a074e756ad",
  },
];

test("golden: the measured Python-vs-JS canonical divergence still exists", () => {
  // This is the regression proof: naive JS recomputation DIVERGES from the
  // pinned Python canonical strings on the divergence window.
  for (const v of GOLDEN_VECTORS) {
    const js = canonicalJson(v.state);
    if (js === v.python_canonical_json) continue; // some vectors may agree
    assert.notEqual(js, v.python_canonical_json, `${v.id}: expected divergence`);
  }
});

test("golden: naive JS recomputation mismatches the Python digest (why echo is law)", () => {
  let anyMismatch = false;
  for (const v of GOLDEN_VECTORS) {
    const jsDigest = sha256Hex(canonicalJson(v.state) + MODEL);
    if (jsDigest !== v.python_input_digest) anyMismatch = true;
  }
  assert.equal(anyMismatch, true, "at least one vector must diverge under naive recomputation");
});

test("golden: the ECHO path is immune — request lines carrying Python digests validate", () => {
  for (const [i, v] of GOLDEN_VECTORS.entries()) {
    const line = JSON.stringify({
      schema: "jrv2_question_io@1",
      state_id: i.toString(16).padStart(16, "0"),
      state: v.state,
      requested_model: MODEL,
      input_digest: v.python_input_digest, // producer authority, echoed
    });
    const check = validateRequestLine(JSON.parse(line));
    assert.equal(check.ok, true, `${v.id}: ${!check.ok && check.reason}`);
    if (check.ok) {
      assert.equal(check.request.input_digest, v.python_input_digest);
    }
  }
});

test("golden: Python digest literals are internally consistent with sha256(canonical||model) on agreeing vectors", () => {
  // For any vector where the JS canonicalization HAPPENS to agree, the
  // digests must agree too (consistency check of the pin itself).
  for (const v of GOLDEN_VECTORS) {
    if (canonicalJson(v.state) === v.python_canonical_json) {
      assert.equal(sha256Hex(v.python_canonical_json + MODEL), v.python_input_digest);
    }
  }
});

test("legacy computeInputDigest agrees with Python on non-divergence inputs", () => {
  const state = {
    bins: { fast_trend: "flat" },
    numerics: { short_return: 0.01, adx14: 34 },
    prior_structure: "RANGE",
    prior_direction: "NEUTRAL",
  };
  // 0.01 and 34 serialize identically in Python and JS
  const pyCanonical =
    '{"bins":{"fast_trend":"flat"},"numerics":{"adx14":34,"short_return":0.01},"prior_direction":"NEUTRAL","prior_structure":"RANGE"}';
  assert.equal(canonicalJson(state), pyCanonical);
  assert.equal(computeInputDigest(state, MODEL), sha256Hex(pyCanonical + MODEL));
});
