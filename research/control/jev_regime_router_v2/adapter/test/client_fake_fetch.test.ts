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
import { buildQuestions } from "../src/prompt.ts";
import { classifyProviderError, CALL_TIMEOUT_MS } from "../src/adapter.ts";
import { PHASES, STRUCTURES, DIRECTIONS, validateProviderResult } from "../src/contract.ts";

const DUMMY_KEY = "sk-local-dummy-not-a-real-credential-0000000000"; // test-only literal
const PIN = "jev-canary-x";

function goodProbs(options: readonly string[], top: string): Record<string, number> {
  const rest = options.filter((o) => o !== top);
  const p: Record<string, number> = { [top]: 0.7 };
  for (const o of rest) p[o] = 0.3 / rest.length;
  return p;
}

function systemOnePayload(model: string): string {
  return JSON.stringify({
    model,
    answers: {
      structure: { type: "choice", choice: "TREND", confidence: 0.9, probabilities: goodProbs(STRUCTURES, "TREND") },
      direction: { type: "choice", choice: "UP", confidence: 0.9, probabilities: goodProbs(DIRECTIONS, "UP") },
      phase: { type: "choice", choice: "UPTREND", confidence: 0.9, probabilities: goodProbs(PHASES, "UPTREND") },
    },
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

test("fake fetch: three-question systemOne validates OK; request_id extracted; usage present", async () => {
  const client = makeClient(fakeFetch(systemOnePayload(PIN), "req-test-123"));
  const { data, requestId } = await client
    .systemOne(
      { state: "s", questions: buildQuestions(), model: PIN },
      { retry: { maxRetries: 0 }, timeout: CALL_TIMEOUT_MS },
    )
    .withResponse();
  assert.equal(requestId, "req-test-123");
  assert.equal(data.model, PIN);
  assert.equal(data.usage.input_tokens, 101);
  const result = validateProviderResult({
    model: data.model,
    answers: (data as unknown as Record<string, unknown>)["answers"],
    usage: (data as unknown as Record<string, unknown>)["usage"],
    pinnedModel: PIN,
  });
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.equal(result.answers?.structure.choice, "TREND");
    assert.equal(result.answers?.direction.choice, "UP");
    assert.equal(result.answers?.phase.choice, "UPTREND");
    assert.equal(result.usage.output_tokens, 11);
  }
});

test("fake fetch: response model != pin is SCHEMA_ERROR material (pin equality law)", async () => {
  const client = makeClient(fakeFetch(systemOnePayload("jev-something-else"), null));
  const { data } = await client
    .systemOne({ state: "s", questions: buildQuestions(), model: PIN }, { retry: { maxRetries: 0 } })
    .withResponse();
  const result = validateProviderResult({
    model: data.model,
    answers: (data as unknown as Record<string, unknown>)["answers"],
    usage: (data as unknown as Record<string, unknown>)["usage"],
    pinnedModel: PIN,
  });
  assert.equal(result.ok, false);
  if (!result.ok) assert.match(result.reason, /pin/);
});

test("fake fetch: phase answer with a fifth label is SCHEMA_ERROR material", async () => {
  const body = JSON.stringify({
    model: PIN,
    answers: {
      structure: { type: "choice", choice: "TREND", confidence: 0.9, probabilities: goodProbs(STRUCTURES, "TREND") },
      direction: { type: "choice", choice: "UP", confidence: 0.9, probabilities: goodProbs(DIRECTIONS, "UP") },
      phase: { type: "choice", choice: "TRANSITION_UNKNOWN", confidence: 0.9, probabilities: goodProbs(PHASES, "UPTREND") },
    },
    usage: { input_tokens: 5, output_tokens: 1 },
  });
  const client = makeClient(fakeFetch(body, null));
  const { data } = await client
    .systemOne({ state: "s", questions: buildQuestions(), model: PIN }, { retry: { maxRetries: 0 } })
    .withResponse();
  const result = validateProviderResult({
    model: data.model,
    answers: (data as unknown as Record<string, unknown>)["answers"],
    usage: (data as unknown as Record<string, unknown>)["usage"],
    pinnedModel: PIN,
  });
  assert.equal(result.ok, false);
  if (!result.ok) assert.match(result.reason, /not in schema options/);
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

test("no network: the injected fetch is the transport (sanity — one call, no retries)", async () => {
  let called = 0;
  const spy: Fetch = (input, init) => {
    called++;
    assert.equal(typeof input, "string");
    assert.equal(init?.method, "POST");
    return Promise.resolve(new Response(systemOnePayload(PIN), { status: 200 }));
  };
  const client = makeClient(spy);
  const { data } = await client
    .systemOne({ state: "s", questions: buildQuestions(), model: PIN }, { retry: { maxRetries: 0 } })
    .withResponse();
  assert.equal(called, 1, "no retries: exactly one transport call");
  assert.equal(data.model, PIN);
});
