// Frozen-contract integrity for the Jev V2 adapter.
//
// Law (dispatch + plan §8 "zero post-outcome mutation"): the adapter refuses
// to run unless the on-disk freeze files are byte-identical (sha256) to the
// digests embedded here, and the prompt is built from the EMBEDDED copies —
// never from a re-read of a possibly tampered file.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

export const EMBEDDED_FREEZE_SHA256: Readonly<Record<string, string>> = {
  // prompt-relevant contracts (question options + semantic state schema)
  "question_contract.json":
    "b14d7426c916d19b66d35b60e4266548143dfbb07b6953422dbbeaecd92622e2",
  "semantic_state_contract.json":
    "82184f1e73882535c906cf2e6bc57389e897b9ddb6f5826785f898d10698defc",
};

/** Verbatim embedded copy of freezes/question_contract.json (jrv2_question_contract@1). */
export const EMBEDDED_QUESTION_CONTRACT: {
  questions: Record<string, { options: string[]; type: string; law?: string }>;
  consistency_law: string[];
  io_schema: string;
  one_call_law: string;
  schema: string;
} = {
  questions: {
    structure: { options: ["TREND", "RANGE"], type: "choice" },
    direction: { options: ["UP", "DOWN", "NEUTRAL"], type: "choice" },
    phase: {
      law: "FORCED CHOICE — TRANSITION_UNKNOWN is NOT an option; the model may never abstain",
      options: ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"],
      type: "choice",
    },
  },
  consistency_law: [
    "TREND + UP -> UPTREND",
    "TREND + DOWN -> DOWNTREND",
    "RANGE + NEUTRAL + prior_direction DOWN -> ACCUMULATION",
    "RANGE + NEUTRAL + prior_direction UP -> DISTRIBUTION",
    "RANGE + NEUTRAL + prior_direction NEUTRAL -> contradiction (UNKNOWN)",
    "TREND + NEUTRAL -> contradiction (UNKNOWN)",
    "RANGE + UP -> contradiction (UNKNOWN)",
    "RANGE + DOWN -> contradiction (UNKNOWN)",
    "phase != structure x direction expectation -> contradiction (UNKNOWN)",
    "phase ACCUMULATION requires prior_direction DOWN; phase DISTRIBUTION requires prior_direction UP; else contradiction (UNKNOWN)",
  ],
  io_schema: "jrv2_question_io@1",
  one_call_law:
    "exactly one systemOne call per state carrying THREE typed questions; two-call designs are forbidden; no silent call-count inflation",
  schema: "jrv2_question_contract@1",
};

/** Embedded semantic-state schema text (bins + named numerics + priors). */
export const SEMANTIC_STATE_TEXT = [
  "The state is a NAMED semantic object with exactly these fields:",
  "bins (semantic labels):",
  "  fast_trend: strong_down|weak_down|flat|weak_up|strong_up  (ema_slope_fast: strong_down<-0.002<=weak_down<-0.0003<=flat<=+0.0003<=weak_up<=+0.002<strong_up)",
  "  slow_trend: same labels for ema_slope_slow (thresholds -0.0015/-0.0002/+0.0002/+0.0015)",
  "  trend_strength: low|medium|high  (adx14 Wilder standard: <20 low, 20-30 medium, >30 high)",
  "  volatility_regime: low|normal|high|extreme  (rv_pctile: <.25, .25-.75, .75-.90, >.90)",
  "  drawdown_state: deep|mild|near_high  (dd_168: <-.20 deep, -.20..-.05 mild, >-.05 near_high)",
  "  range_location: near_low|middle|near_high  (range_pos: <-.30, -.30..+.30, >+.30)",
  "  close_location: weak|neutral|strong  (clv_24: <.40, .40-.60, >.60)",
  "  volume_state: low|normal|high  (vol_z: <-1, -1..+1, >+1)",
  "  dist_to_ema: extended_below|below|at|above|extended_above  (dist_ema: <-1.5, -1.5..-.25, -.25..+.25, +.25..+1.5, >+1.5)",
  "numerics (named raw values): short_return(r4), medium_return(r24), long_return(r72), ema_slope_fast, ema_slope_slow, dist_ema, adx14, atr_pct, rv_pctile, dd_168, dist_low, range_pos, vol_z, clv_24",
  "prior_structure: TREND_UP|TREND_DOWN|RANGE|none (persisted effective regime, anonymized)",
  "prior_direction: UP|DOWN|NEUTRAL|none (persisted effective regime, anonymized)",
  "Anonymization: no symbol, no absolute dates, no price levels, no calendar features, no event names, no PnL/outcomes.",
].join("\n");

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
