// Client-path tests with INJECTED fetch — zero network, zero real credentials.
// The dummy key below is a static local literal used only to satisfy the
// client constructor; it is never printed and cannot authenticate anywhere.

import { test } from "node:test";
import assert from "node:assert/strict";
import {
  APIError,
  APITimeoutError,
  TypeSafeClient,
} from "@typesafe-ai/sdk";
import type { Fetch } from "@typesafe-ai/sdk";
import { buildRegimeQuestions } from "../src/prompt.ts";
import { classifyProviderError, CALL_TIMEOUT_MS } from "../src/adapter.ts";
import { validateProviderAnswer } from "../src/contract.ts";

const DUMMY_KEY = "sk-local-dummy-not-a-real-credential-0000000000"; // test-only literal
const PIN = "jev-canary-x";

function goodProbs(): Record<string, number> {
  return { ACCUMULATION: 0.1, UPTREND: 0.6, DISTRIBUTION: 0.05, DOWNTREND: 0.05, TRANSITION_UNKNOWN: 0.2 };
}

function systemOnePayload(model: string, choice: string, probs: Record<string, number>): string {
  return JSON.stringify({
    model,
    answers: { regime: { type: "choice", choice, confidence: 0.9, probabilities: probs } },
    usage: { input_tokens: 101, output_tokens: 11 },
  });
}

function fakeFetch(body: string, requestId: string | null): Fetch {
  return (_input: string, _init?: RequestInit) => {
    const headers: Record<string, string> = { "content-type": "application/json" };
    if (requestId !== null) headers["x-typesafe-request-id"] = requestId;
    return Promise.resolve(new Response(body, { status: 200, headers }));
  };
}

function makeClient(fetchImpl: Fetch): TypeSafeClient {
  return new TypeSafeClient({ apiKey: DUMMY_KEY, fetch: fetchImpl, timeout: CALL_TIMEOUT_MS });
}

test("fake fetch: systemOne answer validates OK; request_id extracted from x-typesafe-request-id", async () => {
  const client = makeClient(fakeFetch(systemOnePayload(PIN, "UPTREND", goodProbs()), "req-test-123"));
  const { data, requestId } = await client
    .systemOne(
      { state: { feature_vector: new Array(16).fill(0.1), prior_regime: null }, questions: buildRegimeQuestions(), model: PIN },
      { retry: { maxRetries: 0 }, timeout: CALL_TIMEOUT_MS },
    )
    .withResponse();
  assert.equal(requestId, "req-test-123");
  assert.equal(data.model, PIN);
  assert.equal(data.usage.input_tokens, 101);
  const ans = validateProviderAnswer({
    model: data.model,
    answer: (data.answers as Record<string, unknown>)["regime"],
    pinnedModel: PIN,
  });
  assert.equal(ans.ok, true);
  if (ans.ok) {
    assert.equal(ans.regime, "UPTREND");
    assert.equal(ans.confidence, 0.9);
    assert.equal(Object.keys(ans.probabilities).length, 5);
  }
});

test("fake fetch: response model != pin is SCHEMA_ERROR material (pin equality law)", async () => {
  const client = makeClient(fakeFetch(systemOnePayload("jev-something-else", "UPTREND", goodProbs()), null));
  const { data } = await client
    .systemOne({ state: "s", questions: buildRegimeQuestions(), model: PIN }, { retry: { maxRetries: 0 } })
    .withResponse();
  const ans = validateProviderAnswer({
    model: data.model,
    answer: (data.answers as Record<string, unknown>)["regime"],
    pinnedModel: PIN,
  });
  assert.equal(ans.ok, false);
  if (!ans.ok) assert.match(ans.reason, /pin/);
});

test("fake fetch: bad probability sum fails validation (adapter -> SCHEMA_ERROR)", async () => {
  const badProbs = { ACCUMULATION: 0.1, UPTREND: 0.1, DISTRIBUTION: 0.1, DOWNTREND: 0.1, TRANSITION_UNKNOWN: 0.1 };
  const client = makeClient(fakeFetch(systemOnePayload(PIN, "UPTREND", badProbs), null));
  const { data } = await client
    .systemOne({ state: "s", questions: buildRegimeQuestions(), model: PIN }, { retry: { maxRetries: 0 } })
    .withResponse();
  const ans = validateProviderAnswer({
    model: data.model,
    answer: (data.answers as Record<string, unknown>)["regime"],
    pinnedModel: PIN,
  });
  assert.equal(ans.ok, false);
});

test("error mapping: APITimeoutError -> TIMEOUT", () => {
  const info = classifyProviderError(new APITimeoutError(CALL_TIMEOUT_MS));
  assert.equal(info.status, "TIMEOUT");
  assert.equal(info.error_class, "APITimeoutError");
});

test("error mapping: APIError -> PROVIDER_ERROR with request_id when present", () => {
  const err = APIError.fromResponse(500, { message: "boom" }, new Headers({ "x-typesafe-request-id": "req-x" }));
  const info = classifyProviderError(err);
  assert.equal(info.status, "PROVIDER_ERROR");
  assert.equal(info.error_class, err.constructor.name);
  if (typeof err.requestId === "string") assert.equal(info.request_id, "req-x");
  else assert.equal(info.request_id, undefined);
});

test("error mapping: generic exception -> PROVIDER_ERROR with constructor name", () => {
  const info = classifyProviderError(new Error("ECONNREFUSED"));
  assert.equal(info.status, "PROVIDER_ERROR");
  assert.equal(info.error_class, "Error");
  assert.equal(info.request_id, undefined);
});

test("credential law: constructor refuses to build a client without a key", () => {
  const saved = process.env.TYPESAFE_API_KEY;
  delete process.env.TYPESAFE_API_KEY;
  try {
    assert.throws(() => new TypeSafeClient(), (err: Error) => err.constructor.name === "TypeSafeError");
  } finally {
    if (saved !== undefined) process.env.TYPESAFE_API_KEY = saved;
  }
});

test("no network: the injected fetch is the transport (sanity — fake receives the call)", async () => {
  let called = 0;
  const spy: Fetch = (input, init) => {
    called++;
    assert.equal(typeof input, "string");
    assert.equal(init?.method, "POST");
    return Promise.resolve(new Response(systemOnePayload(PIN, "DOWNTREND", goodProbs()), { status: 200 }));
  };
  const client = makeClient(spy);
  const { data } = await client
    .systemOne({ state: "s", questions: buildRegimeQuestions(), model: PIN }, { retry: { maxRetries: 0 } })
    .withResponse();
  assert.equal(called, 1, "no retries: exactly one transport call");
  assert.equal(data.model, PIN);
});
