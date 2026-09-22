// FROZEN prompt module for the Jev adapter.
//
// The outcome-blind regime definitions are embedded VERBATIM from
// freezes/regime_label_contract.json via src/freeze_digests.ts (sha256-gated at
// startup — see verifyFreezeDigests). Free text is never invented here; every
// string below traces to the embedded freeze copy.

import { choice } from "@typesafe-ai/sdk";
import type { ChoiceQuestion } from "@typesafe-ai/sdk";
import { EMBEDDED_REGIME_LABEL_CONTRACT } from "./freeze_digests.ts";
import type { RegimeLabel } from "./contract.ts";

const DEFS = EMBEDDED_REGIME_LABEL_CONTRACT.definitions_outcome_blind;
const FREE_TEXT_RULE = EMBEDDED_REGIME_LABEL_CONTRACT.free_text_regime;

/** Outcome-blind question instructions, built from the embedded freeze copy. */
export const REGIME_INSTRUCTIONS: {
  role: string;
  regime_definitions: Record<string, string>;
  free_text_regime: string;
  rules: string[];
} = {
  role: "You classify one market regime from an outcome-blind feature state.",
  regime_definitions: DEFS,
  free_text_regime: FREE_TEXT_RULE,
  rules: [
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
