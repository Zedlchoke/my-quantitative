// Frozen-contract integrity for the Jev adapter.
//
// Law (dispatch + plan §8 "zero post-outcome mutation"): the adapter refuses to
// run unless the on-disk freezes/regime_label_contract.json is byte-identical
// (sha256) to the digest embedded here, and the prompt is built from the
// EMBEDDED copy — never from a re-read of a possibly tampered file.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

export const EMBEDDED_FREEZE_SHA256: Readonly<Record<string, string>> = {
  "regime_label_contract.json":
    "04a12cd38cf1089e7ef8ace6bb4c2529dcc69c3d21559ea6cd509e41a626b814",
};

/** Verbatim embedded copy of freezes/regime_label_contract.json (jrv1_regime_label_contract@1). */
export const EMBEDDED_REGIME_LABEL_CONTRACT: {
  definitions_outcome_blind: Record<string, string>;
  free_text_regime: string;
  labels: string[];
  response_fields_required: string[];
  schema: string;
} = {
  definitions_outcome_blind: {
    ACCUMULATION:
      "a downtrend occurred previously; price now ranges/compresses; downside pressure is weakening (defined ONLY by past structure, never by future price direction)",
    DISTRIBUTION:
      "an uptrend occurred previously; price now ranges/compresses; upside pressure is weakening",
    DOWNTREND:
      "a negative causal trend exists now: lower-price structure and measurable downside pressure",
    TRANSITION_UNKNOWN:
      "evidence conflicts, confidence is low, data is insufficient, or the state is changing",
    UPTREND:
      "a positive causal trend exists now: higher-price structure and measurable trend strength",
  },
  free_text_regime: "REJECTED -> SCHEMA_ERROR -> TRANSITION_UNKNOWN",
  labels: [
    "ACCUMULATION",
    "UPTREND",
    "DISTRIBUTION",
    "DOWNTREND",
    "TRANSITION_UNKNOWN",
  ],
  response_fields_required: [
    "regime",
    "probabilities(all5,sum=1+/-0.01)",
    "confidence",
    "model",
    "request_id",
    "input_digest",
    "latency_ms",
    "status",
  ],
  schema: "jrv1_regime_label_contract@1",
};

export interface FreezeCheckResult {
  ok: boolean;
  mismatches: string[];
}

/** Verify every embedded freeze digest against the on-disk bytes. */
export function verifyFreezeDigests(freezesDir: string): FreezeCheckResult {
  const mismatches: string[] = [];
  for (const [name, expected] of Object.entries(EMBEDDED_FREEZE_SHA256)) {
    let actual: string;
    try {
      const bytes = readFileSync(`${freezesDir}/${name}`);
      actual = createHash("sha256").update(bytes).digest("hex");
    } catch (err) {
      mismatches.push(`${name}: unreadable (${err instanceof Error ? err.message : String(err)})`);
      continue;
    }
    if (actual !== expected) {
      mismatches.push(`${name}: sha256 ${actual} != embedded ${expected}`);
    }
  }
  return { ok: mismatches.length === 0, mismatches };
}
