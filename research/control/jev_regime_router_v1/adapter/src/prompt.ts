// FROZEN prompt module for the Jev adapter.
//
// The outcome-blind regime definitions are embedded VERBATIM from
// freezes/regime_label_contract.json via src/freeze_digests.ts (sha256-gated at
// startup — see verifyFreezeDigests). Free text is never invented here; every
// string below traces to an embedded freeze copy.
//
// amendment_2 (2026-09-22, canary-driven, pre-outcome): the instructions now
// embed the feature-vector schema VERBATIM from freezes/feature_contract.json
// via src/feature_digests.ts (sha256-gated the same way). Live canary evidence:
// without the schema the model received 16 anonymous floats and anchored on
// prior_regime (5/5 directional fixtures FAIL). The effective prompt version
// is hashed into the decision cache key (see contract.ts computeCacheKey).

import { choice } from "@typesafe-ai/sdk";
import type { ChoiceQuestion } from "@typesafe-ai/sdk";
import { createHash } from "node:crypto";
import { EMBEDDED_REGIME_LABEL_CONTRACT } from "./freeze_digests.ts";
import { FEATURE_SCHEMA_TEXT } from "./feature_digests.ts";
import { setPromptDigest } from "./contract.ts";
import type { RegimeLabel } from "./contract.ts";

const DEFS = EMBEDDED_REGIME_LABEL_CONTRACT.definitions_outcome_blind;
const FREE_TEXT_RULE = EMBEDDED_REGIME_LABEL_CONTRACT.free_text_regime;

/** Outcome-blind question instructions, built from embedded freeze copies. */
export const REGIME_INSTRUCTIONS: {
  role: string;
  feature_schema: string;
  state_layout: string;
  regime_definitions: Record<string, string>;
  free_text_regime: string;
  rules: string[];
} = {
  role: "You classify one market regime from an outcome-blind feature state.",
  feature_schema: FEATURE_SCHEMA_TEXT,
  state_layout:
    "The state carries feature_vector (exactly 16 numbers, in order f01..f16 of the schema above) and prior_regime (f17: the persisted regime label in force at the previous bar, or null before the first persisted state).",
  regime_definitions: DEFS,
  free_text_regime: FREE_TEXT_RULE,
  rules: [
    "Interpret each feature strictly per the schema (scales: adx14 spans 0-100; rv_pctile spans 0-1; returns/slopes/distances are normalized per the schema formulas).",
    "Use ONLY the past structure expressed by the state; never future price direction.",
    "Answer with exactly one of the five listed labels; free-text labels are rejected.",
  ],
};

/** The choice question: label -> verbatim description from the same contract. */
export function buildRegimeQuestions(): {
  regime: ChoiceQuestion<Record<RegimeLabel, string>>;
} {
  return {
    regime: choice(REGIME_INSTRUCTIONS, {
      ACCUMULATION: DEFS.ACCUMULATION!,
      UPTREND: DEFS.UPTREND!,
      DISTRIBUTION: DEFS.DISTRIBUTION!,
      DOWNTREND: DEFS.DOWNTREND!,
      TRANSITION_UNKNOWN: DEFS.TRANSITION_UNKNOWN!,
    }),
  };
}

/** amendment_2: prompt identity (V1) — digest over the frozen instruction content. */
export const PROMPT_VERSION = "V1_amendment_2";
export function computePromptDigest(): string {
  const criteria = buildRegimeQuestions().regime.criteria;
  return createHash("sha256")
    .update(JSON.stringify(REGIME_INSTRUCTIONS))
    .update(JSON.stringify(criteria, Object.keys(criteria).sort()))
    .digest("hex");
}
export function initPromptDigest(): string {
  const d = computePromptDigest();
  setPromptDigest(d);
  return d;
}
