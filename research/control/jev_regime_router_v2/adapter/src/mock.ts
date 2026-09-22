// Deterministic mock provider for --mock mode (tests/smoke only, no network).
//
// Mirrors the PYTHON mock rule (jrv2/mock_adapter.py mock_answers) so the two
// languages agree on the frozen synthetic canaries:
//   C1 -> TREND/UP/UPTREND, C2 -> TREND/DOWN/DOWNTREND,
//   C3 -> RANGE/NEUTRAL/ACCUMULATION, C4 -> RANGE/NEUTRAL/DISTRIBUTION,
//   C5/C7 -> TREND/NEUTRAL/* (schema-valid contradiction -> code UNKNOWN),
//   C6 -> RANGE/NEUTRAL/UPTREND (contradiction -> code UNKNOWN);
//   C8 is LOCAL_INVALID upstream and never sent.
// Probability vectors are integer cents summing to EXACTLY 1.00. Seeded by
// the input_digest so identical inputs are bit-identical forever.

import { createHash } from "node:crypto";
import {
  DIRECTIONS,
  PHASES,
  QUESTION_IO_SCHEMA,
  STRUCTURES,
} from "./contract.ts";
import type { Jrv2Request, Jrv2Response } from "./contract.ts";

interface Answers {
  structure: string;
  direction: string;
  phase: string;
}

export function mockClassify(state: Jrv2Request["state"]): Answers {
  const fast = state.bins.fast_trend ?? "flat";
  const slow = state.bins.slow_trend ?? "flat";
  const strength = state.bins.trend_strength ?? "low";
  const fastUp = fast === "weak_up" || fast === "strong_up";
  const fastDn = fast === "weak_down" || fast === "strong_down";
  const slowUp = slow === "weak_up" || slow === "strong_up";
  const slowDn = slow === "weak_down" || slow === "strong_down";
  const pd = ["UP", "DOWN", "NEUTRAL"].includes(state.prior_direction)
    ? state.prior_direction
    : "NEUTRAL";

  if (fastUp && slowUp) return { structure: "TREND", direction: "UP", phase: "UPTREND" };
  if (fastDn && slowDn) return { structure: "TREND", direction: "DOWN", phase: "DOWNTREND" };
  if (fast === "flat" && !fastUp && !fastDn) {
    if (pd === "DOWN") return { structure: "RANGE", direction: "NEUTRAL", phase: "ACCUMULATION" };
    if (pd === "UP") return { structure: "RANGE", direction: "NEUTRAL", phase: "DISTRIBUTION" };
    // contradiction: RANGE + NEUTRAL + prior NEUTRAL (code-owned UNKNOWN)
    return { structure: "RANGE", direction: "NEUTRAL", phase: "UPTREND" };
  }
  if (fastUp && (strength === "high" || strength === "medium") && !slowDn) {
    return { structure: "TREND", direction: "UP", phase: "UPTREND" };
  }
  if (fastDn && (strength === "high" || strength === "medium") && !slowUp) {
    return { structure: "TREND", direction: "DOWN", phase: "DOWNTREND" };
  }
  // mixed evidence -> schema-valid contradiction (TREND + NEUTRAL)
  return { structure: "TREND", direction: "NEUTRAL", phase: "UPTREND" };
}

/** Integer-cents block over `options`; top = 55..82 cents; sum EXACTLY 100. */
function answerBlock(top: string, options: readonly string[], h: Buffer): Record<string, unknown> {
  const rest = options.filter((o) => o !== top);
  const topCents = 55 + (h[0] % 28);
  const rem = 100 - topCents;
  const base = Math.floor(rem / rest.length);
  const extra = rem - base * rest.length;
  const probabilities: Record<string, number> = { [top]: topCents / 100 };
  rest.forEach((opt, i) => {
    probabilities[opt] = (base + (i < extra ? 1 : 0)) / 100;
  });
  return {
    choice: top,
    probabilities,
    confidence: topCents / 100,
  };
}

/** Build the deterministic mock response row for a validated request. */
export function buildMockResponse(
  request: Jrv2Request,
  model: string,
  inputDigest: string,
): Jrv2Response {
  const answers = mockClassify(request.state);
  const h = createHash("sha256").update(`${inputDigest}|mock-v2`, "utf8").digest();
  return {
    schema: QUESTION_IO_SCHEMA,
    state_id: request.state_id,
    status: "OK",
    answers: {
      structure: answerBlock(answers.structure, STRUCTURES, h.subarray(0, 16)) as never,
      direction: answerBlock(answers.direction, DIRECTIONS, h.subarray(1, 17)) as never,
      phase: answerBlock(answers.phase, PHASES, h.subarray(2, 18)) as never,
    },
    model,
    request_id:
      "mock-" +
      createHash("sha256").update(`${request.state_id}${inputDigest}`, "utf8").digest("hex").slice(0, 12),
    input_digest: inputDigest,
    prior_direction: request.state.prior_direction,
    latency_ms: 0,
    usage: { input_tokens: 40 + (h[3] % 20), output_tokens: 8 + (h[4] % 8) },
    mock: true,
  };
}
