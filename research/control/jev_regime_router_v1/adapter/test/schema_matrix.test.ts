// Schema accept/reject matrix for jrv1_decision_io@1 (unit-level, no IO).

import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  DECISION_IO_SCHEMA,
  LABELS,
  STATUSES,
  canonicalJson,
  computeInputDigest,
  validateProbabilities,
  validateProviderAnswer,
  validateRequestLine,
} from "../src/contract.ts";

const GOOD_VECTOR = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];

function goodRequest(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    schema: DECISION_IO_SCHEMA,
    state_id: "0123456789abcdef",
    state: { feature_vector: GOOD_VECTOR, prior_regime: null },
    requested_model: "jev-canary-x",
    ...overrides,
  };
}

function goodProbs(): Record<string, number> {
  return { ACCUMULATION: 0.1, UPTREND: 0.6, DISTRIBUTION: 0.1, DOWNTREND: 0.1, TRANSITION_UNKNOWN: 0.1 };
}

test("request: valid line accepted", () => {
  const v = validateRequestLine(goodRequest());
  assert.equal(v.ok, true);
  if (v.ok) {
    assert.equal(v.request.state_id, "0123456789abcdef");
    assert.equal(v.request.state.feature_vector.length, 16);
    assert.equal(v.request.state.prior_regime, null);
  }
});

test("request: valid prior_regime label accepted", () => {
  const v = validateRequestLine(goodRequest({ state: { feature_vector: GOOD_VECTOR, prior_regime: "UPTREND" } }));
  assert.equal(v.ok, true);
});

test("request: non-16hex state_id rejected", () => {
  for (const bad of ["xyz", "0123456789abcde", "0123456789abcdef0", "0123456789ABCDEF", "123456789012345g", ""]) {
    const v = validateRequestLine(goodRequest({ state_id: bad }));
    assert.equal(v.ok, false, `state_id ${bad} must be rejected`);
  }
});

test("request: wrong schema string rejected", () => {
  const v = validateRequestLine(goodRequest({ schema: "jrv1_decision_io@2" }));
  assert.equal(v.ok, false);
});

test("request: bad feature_vector rejected (length, non-number, NaN, missing)", () => {
  const cases: unknown[] = [
    [1, 2, 3],
    [...GOOD_VECTOR.slice(0, 15)],
    [...GOOD_VECTOR.slice(0, 15), "x"],
    [...GOOD_VECTOR.slice(0, 15), Number.NaN],
    undefined,
  ];
  for (const fv of cases) {
    const v = validateRequestLine(
      goodRequest({ state: { feature_vector: fv, prior_regime: null } }),
    );
    assert.equal(v.ok, false, `feature_vector ${JSON.stringify(fv)} must be rejected`);
  }
});

test("request: free-text prior_regime rejected", () => {
  const v = validateRequestLine(
    goodRequest({ state: { feature_vector: GOOD_VECTOR, prior_regime: "RANGE" } }),
  );
  assert.equal(v.ok, false);
});

test("request: missing requested_model / non-object line rejected", () => {
  assert.equal(validateRequestLine(goodRequest({ requested_model: "" })).ok, false);
  assert.equal(validateRequestLine(goodRequest({ requested_model: 5 })).ok, false);
  assert.equal(validateRequestLine("a line").ok, false);
  assert.equal(validateRequestLine(null).ok, false);
});

test("probabilities: valid block accepted", () => {
  const v = validateProbabilities(goodProbs());
  assert.equal(v.ok, true);
});

test("probabilities: missing label rejected", () => {
  const p = goodProbs();
  delete (p as Record<string, number | undefined>).UPTREND;
  assert.equal(validateProbabilities(p).ok, false);
});

test("probabilities: bad sum rejected (0.5)", () => {
  const p = { ACCUMULATION: 0.1, UPTREND: 0.1, DISTRIBUTION: 0.1, DOWNTREND: 0.1, TRANSITION_UNKNOWN: 0.1 };
  const v = validateProbabilities(p);
  assert.equal(v.ok, false);
  if (!v.ok) assert.match(v.reason, /sum/);
});

test("probabilities: negative value rejected", () => {
  const p = goodProbs();
  p.UPTREND = -0.6;
  assert.equal(validateProbabilities(p).ok, false);
});

test("probabilities: free-text label rejected", () => {
  const p = { ...goodProbs(), RANGE: 0.0 } as unknown as Record<string, number>;
  delete p.TRANSITION_UNKNOWN;
  assert.equal(validateProbabilities(p).ok, false);
});

test("provider answer: wrong model vs pin rejected", () => {
  const v = validateProviderAnswer({
    model: "some-other-model",
    answer: { type: "choice", choice: "UPTREND", confidence: 0.9, probabilities: goodProbs() },
    pinnedModel: "jev-canary-x",
  });
  assert.equal(v.ok, false);
  if (!v.ok) assert.match(v.reason, /pin/);
});

test("provider answer: free-text regime rejected", () => {
  const v = validateProviderAnswer({
    model: "jev-canary-x",
    answer: { type: "choice", choice: "MOSTLY_BULLISH", confidence: 0.9, probabilities: goodProbs() },
    pinnedModel: "jev-canary-x",
  });
  assert.equal(v.ok, false);
});

test("provider answer: non-choice answer type rejected", () => {
  const v = validateProviderAnswer({
    model: "jev-canary-x",
    answer: { type: "noul", noul: 0.5 },
    pinnedModel: "jev-canary-x",
  });
  assert.equal(v.ok, false);
});

test("provider answer: valid answer accepted", () => {
  const v = validateProviderAnswer({
    model: "jev-canary-x",
    answer: { type: "choice", choice: "UPTREND", confidence: 0.9, probabilities: goodProbs() },
    pinnedModel: "jev-canary-x",
  });
  assert.equal(v.ok, true);
  if (v.ok) {
    assert.equal(v.regime, "UPTREND");
    assert.deepEqual(Object.keys(v.probabilities).sort(), [...LABELS].sort());
  }
});

test("status and label vocabularies frozen", () => {
  assert.deepEqual(
    [...STATUSES].sort(),
    ["LOCAL_INVALID", "OK", "PROVIDER_ERROR", "SCHEMA_ERROR", "TIMEOUT"],
  );
  assert.equal(LABELS.length, 5);
});

test("canonical json: sorted keys, no whitespace, nested", () => {
  assert.equal(canonicalJson({ b: 1, a: 2 }), '{"a":2,"b":1}');
  assert.equal(canonicalJson({ z: { y: 1, x: [2, 1] }, a: null }), '{"a":null,"z":{"x":[2,1],"y":1}}');
  assert.equal(canonicalJson("s"), '"s"');
  assert.equal(canonicalJson(0.004), "0.004");
  assert.equal(canonicalJson([1.2, -0.3]), "[1.2,-0.3]");
  assert.ok(!canonicalJson({ a: 1, b: 2 }).includes(" "));
});

test("canonical json: key order independence", () => {
  assert.equal(canonicalJson({ a: 1, b: { c: 2, d: 3 } }), canonicalJson({ b: { d: 3, c: 2 }, a: 1 }));
});

test("input digest: sha256(canonical_json(state) || requested_model)", () => {
  const state = { feature_vector: GOOD_VECTOR, prior_regime: null };
  const expected = createHash("sha256")
    .update(canonicalJson(state) + "jev-canary-x", "utf8")
    .digest("hex");
  assert.equal(computeInputDigest(state, "jev-canary-x"), expected);
  assert.equal(computeInputDigest(state, "other"), createHash("sha256").update(canonicalJson(state) + "other", "utf8").digest("hex"));
});

test("input digest: independent of state key insertion order", () => {
  const a = { feature_vector: GOOD_VECTOR, prior_regime: null };
  const b = { prior_regime: null, feature_vector: GOOD_VECTOR };
  assert.equal(computeInputDigest(a, "m"), computeInputDigest(b, "m"));
});

test("input digest: ordered vector matters", () => {
  const a = { feature_vector: [1, 2], prior_regime: null };
  const b = { feature_vector: [2, 1], prior_regime: null };
  assert.notEqual(computeInputDigest(a, "m"), computeInputDigest(b, "m"));
});
