// Deterministic mock provider for --mock mode (tests/smoke only, no network).
//
// - seeded by sha256 of the input_digest => same input, same output, forever.
// - labels are PLAUSIBLE, not predictive: strong trend features -> trend
//   labels; range-after-trend -> ACCUMULATION/DISTRIBUTION; noise -> UNKNOWN.
//   Heuristic aligned with freezes/synthetic_canary_fixtures.json feature
//   order: [r1, r4, r12, r24, r72, ema_slope_fast, ema_slope_slow, dist_ema,
//   adx14, atr_pct, rv_pctile, dd_168, dist_low, range_pos, vol_z, clv_24].
// - probability vectors are integer cents summing to EXACTLY 1.00 (2dp values
//   by construction; any remainder lands on the top label).

import { createHash } from "node:crypto";
import { LABELS } from "./contract.ts";
import type { Jrv1Request, Jrv1Response, RegimeLabel } from "./contract.ts";

const ADX_TREND_THRESHOLD = 22;
const VOL_Z_NOISE_THRESHOLD = 1.0;

/** Plausible-label heuristic on the frozen feature order. */
export function mockClassify(
  featureVector: readonly number[],
  priorRegime: RegimeLabel | null,
): RegimeLabel {
  const f = featureVector;
  const returns = f.slice(0, 5) as number[]; // r1, r4, r12, r24, r72
  const adx = f[8] as number;
  const volZ = f[14] as number;

  const hasPos = returns.some((x) => x > 0);
  const hasNeg = returns.some((x) => x < 0);
  const conflicting = hasPos && hasNeg;
  const trendBlock = (f.slice(0, 8) as number[]).reduce((a, b) => a + b, 0) / 8;

  // noisy / contradictory evidence -> UNKNOWN
  if (volZ > VOL_Z_NOISE_THRESHOLD) return "TRANSITION_UNKNOWN";

  if (adx >= ADX_TREND_THRESHOLD && !conflicting) {
    if (trendBlock > 0) return "UPTREND";
    if (trendBlock < 0) return "DOWNTREND";
  }

  // ranging: range-after-trend semantics from the prior label
  if (!conflicting) {
    if (priorRegime === "UPTREND") return "DISTRIBUTION";
    if (priorRegime === "DOWNTREND") return "ACCUMULATION";
  }
  return "TRANSITION_UNKNOWN";
}

/** Deterministically rotate the non-top labels by hash. */
function labelOrder(top: RegimeLabel, h: Buffer): RegimeLabel[] {
  const rest = LABELS.filter((l) => l !== top);
  const rot = h[4] % rest.length;
  return [top, ...rest.slice(rot), ...rest.slice(0, rot)];
}

/** Build the deterministic mock response row for a validated request. */
export function buildMockResponse(
  request: Jrv1Request,
  model: string,
  inputDigest: string,
): Jrv1Response {
  const regime = mockClassify(request.state.feature_vector, request.state.prior_regime);

  // probability vector: integer cents, sum EXACTLY 100; seeded by the
  // input_digest hash so identical inputs are bit-identical forever
  const h = createHash("sha256")
    .update(`${inputDigest}|${regime}|mock-probs`, "utf8")
    .digest();
  const top = 55 + (h[0] % 28); // 55..82
  const second = 8 + (h[1] % 8); // 8..15
  const rest3 = 100 - top - second; // >= 3
  const r3 = 1 + Math.floor(((rest3 - 3) * h[2]) / 255);
  const r4 = 1 + Math.floor(((rest3 - 3 - r3) * h[3]) / 255);
  const r5 = rest3 - r3 - r4; // >= 1
  const cents = [top, second, r3, r4, r5];
  const order = labelOrder(regime, h);

  const probabilities: Record<string, number> = {};
  for (const [i, label] of order.entries()) {
    const c = cents[i] ?? 0;
    probabilities[label] = Number((c / 100).toFixed(2));
  }

  return {
    schema: "jrv1_decision_io@1",
    state_id: request.state_id,
    status: "OK",
    regime,
    probabilities,
    confidence: Number((top / 100).toFixed(2)),
    model,
    request_id:
      "mock-" +
      createHash("sha256").update(`${inputDigest}|mock-rid`, "utf8").digest("hex").slice(0, 12),
    input_digest: inputDigest,
    latency_ms: 0,
    mock: true,
  };
}
