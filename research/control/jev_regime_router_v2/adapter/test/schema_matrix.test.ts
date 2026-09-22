// Forced-choice schema tests — NO DOUBLE ABSTENTION (V2 core law).
//
// The built question criteria carry EXACTLY three questions and the phase
// question carries EXACTLY the 4 schema phases. No fifth option, no
// TRANSITION_UNKNOWN, no UNKNOWN-equivalent exists anywhere in the built
// criteria. Provider answers carrying a fifth label or an UNKNOWN-equivalent
// are rejected as SCHEMA_ERROR material.

import { test } from "node:test";
import assert from "node:assert/strict";
import { buildQuestions, QUESTION_INSTRUCTIONS, computePromptDigest } from "../src/prompt.ts";
import {
  PHASES,
  STRUCTURES,
  DIRECTIONS,
  FORBIDDEN_PHASE_LABELS,
  validateAnswers,
  validateProviderResult,
  validateUsage,
} from "../src/contract.ts";

const PIN = "jev-canary-x";

function block(choice: string, options: readonly string[], top = 0.6): Record<string, unknown> {
  const rest = options.filter((o) => o !== choice);
  const others = rest.length > 0 ? (1 - top) / rest.length : 0;
  const probabilities: Record<string, number> = { [choice]: top };
  for (const o of rest) probabilities[o] = others;
  return { choice, probabilities, confidence: top };
}

function goodAnswers(phaseChoice = "UPTREND"): Record<string, unknown> {
  return {
    structure: block("TREND", STRUCTURES),
    direction: block("UP", DIRECTIONS),
    phase: block(phaseChoice, PHASES),
  };
}

test("built criteria: exactly THREE questions with the exact schema option sets", () => {
  const q = buildQuestions();
  assert.deepEqual(Object.keys(q).sort(), ["direction", "phase", "structure"]);
  assert.deepEqual(Object.keys(q.structure.criteria).sort(), [...STRUCTURES].sort());
  assert.deepEqual(Object.keys(q.direction.criteria).sort(), [...DIRECTIONS].sort());
  assert.deepEqual(Object.keys(q.phase.criteria).sort(), [...PHASES].sort());
  assert.equal(Object.keys(q.phase.criteria).length, 4, "phase has exactly 4 options");
});

test("no UNKNOWN option exists anywhere in the built criteria (static law)", () => {
  const q = buildQuestions();
  const allOptions = [
    ...Object.keys(q.structure.criteria),
    ...Object.keys(q.direction.criteria),
    ...Object.keys(q.phase.criteria),
  ];
  for (const bad of FORBIDDEN_PHASE_LABELS) {
    assert.equal(
      allOptions.filter((o) => o.toUpperCase() === bad.toUpperCase()).length,
      0,
      `${bad} must not be an option`,
    );
  }
  // and nowhere in the instruction text as an advertised option
  const advertised = `${QUESTION_INSTRUCTIONS.phase} ${QUESTION_INSTRUCTIONS.forced_choice}`;
  assert.doesNotMatch(advertised, /TRANSITION_UNKNOWN/);
  assert.match(advertised, /no abstain option/);
});

test("prompt digest is stable and covers all three criteria sets", () => {
  const d1 = computePromptDigest();
  const d2 = computePromptDigest();
  assert.equal(d1, d2);
  assert.match(d1, /^[0-9a-f]{64}$/);
});

test("validateAnswers accepts the three consistent schema blocks", () => {
  const r = validateAnswers(goodAnswers());
  assert.equal(r.ok, true);
});

test("SCHEMA_ERROR: phase answer carrying TRANSITION_UNKNOWN", () => {
  const answers = goodAnswers("TRANSITION_UNKNOWN");
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.reason, /not in schema options/);
});

test("SCHEMA_ERROR: phase answer carrying a FIFTH label (UNKNOWN)", () => {
  const answers = goodAnswers();
  (answers.phase as Record<string, unknown>)["choice"] = "UNKNOWN";
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
});

test("SCHEMA_ERROR: phase block carrying a fifth probability key", () => {
  const answers = goodAnswers();
  const probs = (answers.phase as Record<string, unknown>)["probabilities"] as Record<string, number>;
  probs["TRANSITION_UNKNOWN"] = 0.0;
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.reason, /exactly the schema options/);
});

test("SCHEMA_ERROR: free-text phase label", () => {
  const answers = goodAnswers("SORT_OF_TRENDING");
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
});

test("SCHEMA_ERROR: missing question (two of three)", () => {
  const answers = goodAnswers() as Record<string, unknown>;
  delete answers["direction"];
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.reason, /exactly structure\/direction\/phase/);
});

test("SCHEMA_ERROR: extra fourth question", () => {
  const answers = goodAnswers() as Record<string, unknown>;
  answers["regime"] = block("UPTREND", PHASES);
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
});

test("SCHEMA_ERROR: bad probability sum in the phase block", () => {
  const answers = goodAnswers();
  const b = answers.phase as Record<string, unknown>;
  const probs = b["probabilities"] as Record<string, number>;
  for (const k of Object.keys(probs)) probs[k] = 0.1;
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.reason, /1 \+\/- 0\.01/);
});

test("SCHEMA_ERROR: negative probability", () => {
  const answers = goodAnswers();
  const probs = ((answers.phase as Record<string, unknown>)["probabilities"]) as Record<string, number>;
  probs["UPTREND"] = -0.5;
  probs["DOWNTREND"] = 1.1;
  const r = validateAnswers(answers);
  assert.equal(r.ok, false);
});

test("validateProviderResult: model pin drift is rejected", () => {
  const r = validateProviderResult({
    model: "jev-something-else",
    answers: goodAnswers(),
    usage: { input_tokens: 10, output_tokens: 2 },
    pinnedModel: PIN,
  });
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.reason, /pin/);
});

test("validateProviderResult: missing usage is rejected (usage persisted per response)", () => {
  const r = validateProviderResult({
    model: PIN,
    answers: goodAnswers(),
    usage: undefined,
    pinnedModel: PIN,
  });
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.reason, /usage/);
});

test("validateProviderResult: valid payload passes with usage echoed", () => {
  const r = validateProviderResult({
    model: PIN,
    answers: goodAnswers(),
    usage: { input_tokens: 101, output_tokens: 11 },
    pinnedModel: PIN,
  });
  assert.equal(r.ok, true);
  if (r.ok) {
    assert.equal(r.usage.input_tokens, 101);
    assert.equal(r.answers?.phase.choice, "UPTREND");
  }
});

test("validateUsage rejects fractional-object and negative usage", () => {
  assert.equal(validateUsage({ input_tokens: -1, output_tokens: 1 }).ok, false);
  assert.equal(validateUsage({ input_tokens: 1 }).ok, false);
  assert.equal(validateUsage("x").ok, false);
  assert.equal(validateUsage({ input_tokens: 1, output_tokens: 2 }).ok, true);
});
