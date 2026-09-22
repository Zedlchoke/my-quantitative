// FROZEN prompt module for the Jev V2 adapter — THREE typed questions, ONE call.
//
// The question option sets are embedded VERBATIM from
// freezes/question_contract.json via src/freeze_digests.ts (sha256-gated at
// startup — see verifyFreezeDigests). Free text is never invented here; every
// string traces to an embedded freeze copy.
//
// NO DOUBLE ABSTENTION (static-test law): the built criteria contain exactly
// THREE questions and the phase question carries EXACTLY the 4 schema
// phases. No UNKNOWN option exists anywhere in the built criteria.

import { choice } from "@typesafe-ai/sdk";
import type { ChoiceQuestion } from "@typesafe-ai/sdk";
import { createHash } from "node:crypto";
import {
  EMBEDDED_QUESTION_CONTRACT,
  SEMANTIC_STATE_TEXT,
} from "./freeze_digests.ts";
import { setPromptDigest } from "./contract.ts";
import type { Direction, Phase, Structure } from "./contract.ts";

const Q = EMBEDDED_QUESTION_CONTRACT.questions;

/** Outcome-blind per-question instructions (embedded freeze + schema text). */
export const QUESTION_INSTRUCTIONS: {
  role: string;
  state_schema: string;
  consistency_law: string[];
  structure: string;
  direction: string;
  phase: string;
  forced_choice: string;
  anonymization: string;
} = {
  role: "You classify one market regime from an outcome-blind named semantic state by answering THREE questions about the same state.",
  state_schema: SEMANTIC_STATE_TEXT,
  consistency_law: EMBEDDED_QUESTION_CONTRACT.consistency_law,
  structure:
    "Q1 structure: is the CURRENT price structure trending or ranging? Answer TREND or RANGE.",
  direction:
    "Q2 direction: is the current directional pressure UP, DOWN, or NEUTRAL? Answer UP, DOWN, or NEUTRAL.",
  phase:
    "Q3 phase: which of the four market phases best matches the state, consistent with your structure and direction answers? Answer exactly one of ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND.",
  forced_choice:
    "All three questions are FORCED CHOICE: you must pick exactly one listed option per question. Abstaining is impossible; there is no abstain option.",
  anonymization:
    "Use ONLY the past structure expressed by the named fields; never future price direction. The state carries no symbol, dates or price levels by design.",
};

const STRUCTURE_DEFS: Record<Structure, string> = {
  TREND: "a directional causal trend exists now: measurable trend structure and strength",
  RANGE: "price is ranging/compressing now: no dominant directional trend structure",
};

const DIRECTION_DEFS: Record<Direction, string> = {
  UP: "current directional pressure is upward",
  DOWN: "current directional pressure is downward",
  NEUTRAL: "no clear current directional pressure",
};

const PHASE_DEFS: Record<Phase, string> = {
  ACCUMULATION:
    "a downtrend occurred previously; price now ranges/compresses; downside pressure is weakening (defined ONLY by past structure, never by future price direction)",
  UPTREND:
    "a positive causal trend exists now: higher-price structure and measurable trend strength",
  DISTRIBUTION:
    "an uptrend occurred previously; price now ranges/compresses; upside pressure is weakening",
  DOWNTREND:
    "a negative causal trend exists now: lower-price structure and measurable downside pressure",
};

export type QuestionSet = {  // type alias: SDK Questions shape
  structure: ChoiceQuestion<Record<Structure, string>>;
  direction: ChoiceQuestion<Record<Direction, string>>;
  phase: ChoiceQuestion<Record<Phase, string>>;
};

/**
 * The THREE typed questions of the single systemOne call.
 *
 * STATIC LAW (tested): the returned object has exactly these three keys and
 * the phase criteria contain exactly the 4 schema phases — no fifth option,
 * no TRANSITION_UNKNOWN, no UNKNOWN anywhere.
 */
export function buildQuestions(): QuestionSet {
  return {
    structure: choice(
      { ...QUESTION_INSTRUCTIONS, question: QUESTION_INSTRUCTIONS.structure, definitions: STRUCTURE_DEFS },
      STRUCTURE_DEFS,
    ),
    direction: choice(
      { ...QUESTION_INSTRUCTIONS, question: QUESTION_INSTRUCTIONS.direction, definitions: DIRECTION_DEFS },
      DIRECTION_DEFS,
    ),
    phase: choice(
      { ...QUESTION_INSTRUCTIONS, question: QUESTION_INSTRUCTIONS.phase, definitions: PHASE_DEFS },
      PHASE_DEFS,
    ),
  };
}

/** Prompt identity: digest over the frozen instruction content + criteria. */
export const PROMPT_VERSION = "V2_v0";
export function computePromptDigest(): string {
  const questions = buildQuestions();
  const criteria = {
    structure: questions.structure.criteria,
    direction: questions.direction.criteria,
    phase: questions.phase.criteria,
  };
  return createHash("sha256")
    .update(JSON.stringify(QUESTION_INSTRUCTIONS))
    .update(JSON.stringify(criteria, Object.keys(criteria).sort()))
    .digest("hex");
}
export function initPromptDigest(): string {
  const d = computePromptDigest();
  setPromptDigest(d);
  return d;
}
