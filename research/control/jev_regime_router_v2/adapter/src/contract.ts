// jrv2_question_io@1 — frozen I/O contract helpers for the Jev adapter (V2).
//
// Contract source of truth:
//   freezes/adapter_contract.json        (jrv2_adapter_contract@1)
//   freezes/question_contract.json       (jrv2_question_contract@1)
//
// FORCED-CHOICE LAW: the phase question carries EXACTLY the 4 schema phases.
// TRANSITION_UNKNOWN / UNKNOWN do not exist as provider options anywhere in
// this file's option sets. Abstention is code-owned (Python safety layer).

import { createHash } from "node:crypto";

export const QUESTION_IO_SCHEMA = "jrv2_question_io@1" as const;

export const PHASES = [
  "ACCUMULATION",
  "UPTREND",
  "DISTRIBUTION",
  "DOWNTREND",
] as const;
export const STRUCTURES = ["TREND", "RANGE"] as const;
export const DIRECTIONS = ["UP", "DOWN", "NEUTRAL"] as const;

export type Phase = (typeof PHASES)[number];
export type Structure = (typeof STRUCTURES)[number];
export type Direction = (typeof DIRECTIONS)[number];

export const PHASE_SET: ReadonlySet<string> = new Set<string>(PHASES);
export const STRUCTURE_SET: ReadonlySet<string> = new Set<string>(STRUCTURES);
export const DIRECTION_SET: ReadonlySet<string> = new Set<string>(DIRECTIONS);

// Labels that must NEVER appear as a provider choice (no-double-abstention).
export const FORBIDDEN_PHASE_LABELS = [
  "TRANSITION_UNKNOWN",
  "UNKNOWN",
  "UNCLEAR",
  "ABSTAIN",
] as const;

export const STATUSES = [
  "OK",
  "TIMEOUT",
  "PROVIDER_ERROR",
  "SCHEMA_ERROR",
  "LOCAL_INVALID",
] as const;

export type ResponseStatus = (typeof STATUSES)[number];

// ---------------------------------------------------------------------------
// canonical json + digests
//
// AMENDMENT 1 echo law (carried from V1): input_digest is computed ONLY by
// the producer (Python, canonical_json(state) || requested_model). The
// request line carries it; the adapter validates the 64-hex format and
// ECHOES it verbatim in every response line and cache entry. The adapter
// MUST NOT recompute it (Python json.dumps and JS JSON.stringify render
// doubles differently — the measured V1 divergence).
// ---------------------------------------------------------------------------

export function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return "[" + value.map(canonicalJson).join(",") + "]";
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  const parts: string[] = [];
  for (const k of keys) {
    const v = obj[k];
    if (v === undefined) continue;
    parts.push(JSON.stringify(k) + ":" + canonicalJson(v));
  }
  return "{" + parts.join(",") + "}";
}

export function sha256Hex(s: string): string {
  return createHash("sha256").update(s, "utf8").digest("hex");
}

/**
 * LEGACY (golden tests only — never used to process a request):
 * sha256(canonical_json(state) || requested_model) as the TS side would
 * compute it. Kept so cross-language golden vectors can prove the old
 * divergence and the echo path's immunity.
 */
export function computeInputDigest(state: unknown, requestedModel: string): string {
  return sha256Hex(canonicalJson(state) + requestedModel);
}

/**
 * Cache key per freeze (V1 amendment_2 law carried into V2):
 * sha256(model || state_id || input_digest || prompt_digest). The prompt
 * version is part of decision identity — different prompts over the same
 * state must never share a cache entry. promptDigest defaults to the active
 * digest set by setPromptDigest()/initPromptDigest() at adapter startup.
 */
let ACTIVE_PROMPT_DIGEST = "";
export function setPromptDigest(d: string): void {
  ACTIVE_PROMPT_DIGEST = d;
}
export function getPromptDigest(): string {
  return ACTIVE_PROMPT_DIGEST;
}
export function computeCacheKey(
  model: string,
  stateId: string,
  inputDigest: string,
  promptDigest = ACTIVE_PROMPT_DIGEST,
): string {
  return sha256Hex(model + stateId + inputDigest + promptDigest);
}

// ---------------------------------------------------------------------------
// request line
// ---------------------------------------------------------------------------

export type Jrv2State = {  // type alias: implicit index signature (SDK EntryType shape)
  bins: Record<string, string>;
  numerics: Record<string, number>;
  prior_structure: string;
  prior_direction: string;
};

export interface Jrv2Request {
  schema: string;
  state_id: string;
  state: Jrv2State;
  requested_model: string;
  /** producer-computed digest, echoed verbatim (amendment_1 law) */
  input_digest: string;
}

export type RequestValidation =
  | { ok: true; request: Jrv2Request }
  | { ok: false; reason: string };

const HEX16 = /^[0-9a-f]{16}$/;
/** amendment_1: the producer-computed input_digest is always 64 lowercase hex. */
export const HEX64 = /^[0-9a-f]{64}$/;

const NUMERIC_FIELDS = new Set([
  "short_return",
  "medium_return",
  "long_return",
  "ema_slope_fast",
  "ema_slope_slow",
  "dist_ema",
  "adx14",
  "atr_pct",
  "rv_pctile",
  "dd_168",
  "dist_low",
  "range_pos",
  "vol_z",
  "clv_24",
]);

const BIN_FIELDS = new Set([
  "fast_trend",
  "slow_trend",
  "trend_strength",
  "volatility_regime",
  "drawdown_state",
  "range_location",
  "close_location",
  "volume_state",
  "dist_to_ema",
]);

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

export function validateRequestLine(raw: unknown): RequestValidation {
  if (!isPlainObject(raw)) return { ok: false, reason: "request line is not an object" };
  if (raw.schema !== QUESTION_IO_SCHEMA) {
    return { ok: false, reason: `schema must be ${QUESTION_IO_SCHEMA}` };
  }
  if (typeof raw.state_id !== "string" || !HEX16.test(raw.state_id)) {
    return { ok: false, reason: "state_id must be 16 lowercase hex chars" };
  }
  if (typeof raw.requested_model !== "string" || raw.requested_model.length === 0) {
    return { ok: false, reason: "requested_model must be a non-empty string" };
  }
  if (typeof raw.input_digest !== "string" || !HEX64.test(raw.input_digest)) {
    return { ok: false, reason: "input_digest must be producer-computed 64 lowercase hex chars" };
  }
  const st = raw.state;
  if (!isPlainObject(st)) return { ok: false, reason: "state must be an object" };
  // Named-state schema law: every bin/numeric key must be a KNOWN name (no
  // anonymous vectors, no free-text fields). Completeness of the full 14+9
  // schema is the PRODUCER's law (features.py); canary fixtures may carry a
  // reduced named subset by freeze design, so validation is a whitelist
  // subset check here.
  const bins = st.bins;
  if (!isPlainObject(bins) || Object.keys(bins).length === 0) {
    return { ok: false, reason: "state.bins must be a non-empty object of named semantic bins" };
  }
  for (const k of Object.keys(bins)) {
    if (!BIN_FIELDS.has(k) || typeof bins[k] !== "string") {
      return { ok: false, reason: `state.bins.${k} is not a named semantic bin` };
    }
  }
  const numerics = st.numerics;
  if (!isPlainObject(numerics) || Object.keys(numerics).length === 0) {
    return { ok: false, reason: "state.numerics must be a non-empty object of named raw numerics" };
  }
  for (const k of Object.keys(numerics)) {
    const v = numerics[k];
    if (!NUMERIC_FIELDS.has(k) || typeof v !== "number" || !Number.isFinite(v)) {
      return { ok: false, reason: `state.numerics.${k} must be a finite named numeric` };
    }
  }
  for (const k of ["prior_structure", "prior_direction"] as const) {
    if (typeof st[k] !== "string" || (st[k] as string).length === 0) {
      return { ok: false, reason: `state.${k} must be a non-empty string` };
    }
  }
  return {
    ok: true,
    request: {
      schema: QUESTION_IO_SCHEMA,
      state_id: raw.state_id,
      state: {
        bins: { ...bins } as Record<string, string>,
        numerics: { ...numerics } as Record<string, number>,
        prior_structure: st.prior_structure as string,
        prior_direction: st.prior_direction as string,
      },
      requested_model: raw.requested_model,
      input_digest: raw.input_digest,
    },
  };
}

// ---------------------------------------------------------------------------
// response line
// ---------------------------------------------------------------------------

export interface AnswerBlock {
  choice: string;
  probabilities: Record<string, number>;
  confidence: number;
}

export interface Jrv2Response {
  schema: string;
  state_id: string;
  status: ResponseStatus;
  answers?: {
    structure: AnswerBlock;
    direction: AnswerBlock;
    phase: AnswerBlock;
  };
  model?: string;
  request_id?: string;
  input_digest: string;
  latency_ms: number;
  usage?: { input_tokens: number; output_tokens: number };
  prior_direction?: string;
  error_class?: string;
  cached?: boolean;
  mock?: boolean;
}

/** Usage must be persisted per response (OK law). */
export function validateUsage(u: unknown): { ok: true; usage: { input_tokens: number; output_tokens: number } } | { ok: false; reason: string } {
  if (!isPlainObject(u)) return { ok: false, reason: "usage must be an object" };
  const it = u.input_tokens;
  const ot = u.output_tokens;
  if (typeof it !== "number" || !Number.isFinite(it) || it < 0) {
    return { ok: false, reason: "usage.input_tokens must be a finite number >= 0" };
  }
  if (typeof ot !== "number" || !Number.isFinite(ot) || ot < 0) {
    return { ok: false, reason: "usage.output_tokens must be a finite number >= 0" };
  }
  return { ok: true, usage: { input_tokens: it, output_tokens: ot } };
}

/**
 * Validate one typed answer block against EXACTLY its option set.
 * A fifth option, a free-text label or an UNKNOWN-equivalent fails here.
 */
export function validateAnswerBlock(
  block: unknown,
  options: readonly string[],
): { ok: true; block: AnswerBlock } | { ok: false; reason: string } {
  if (!isPlainObject(block)) return { ok: false, reason: "answer block is not an object" };
  const choice = block.choice;
  if (typeof choice !== "string" || !options.includes(choice)) {
    return { ok: false, reason: `choice ${String(choice)} not in schema options` };
  }
  const probs = block.probabilities;
  if (!isPlainObject(probs)) return { ok: false, reason: "probabilities must be an object" };
  const keys = Object.keys(probs);
  if (keys.length !== options.length || !keys.every((k) => options.includes(k))) {
    return { ok: false, reason: "probabilities must carry exactly the schema options" };
  }
  let sum = 0;
  for (const k of options) {
    const v = probs[k];
    if (typeof v !== "number" || !Number.isFinite(v) || v < 0) {
      return { ok: false, reason: `probability for ${k} must be a finite number >= 0` };
    }
    sum += v;
  }
  if (Math.abs(sum - 1) > 0.01) {
    return { ok: false, reason: `probability sum ${sum} outside 1 +/- 0.01` };
  }
  const confidence = block.confidence;
  if (typeof confidence !== "number" || !Number.isFinite(confidence)) {
    return { ok: false, reason: "confidence must be a finite number" };
  }
  return {
    ok: true,
    block: {
      choice,
      probabilities: Object.fromEntries(options.map((k) => [k, probs[k] as number])),
      confidence,
    },
  };
}

/**
 * Validate the THREE typed answers of a systemOne response.
 * Returns the validated answers or a violation reason (-> SCHEMA_ERROR).
 */
export function validateAnswers(
  raw: unknown,
): { ok: true; answers: Jrv2Response["answers"] } | { ok: false; reason: string } {
  if (!isPlainObject(raw)) return { ok: false, reason: "answers must be an object" };
  const keys = Object.keys(raw).sort();
  if (JSON.stringify(keys) !== JSON.stringify(["direction", "phase", "structure"])) {
    return { ok: false, reason: "answers must carry exactly structure/direction/phase" };
  }
  const structure = validateAnswerBlock(raw.structure, STRUCTURES);
  if (!structure.ok) return { ok: false, reason: `structure: ${structure.reason}` };
  const direction = validateAnswerBlock(raw.direction, DIRECTIONS);
  if (!direction.ok) return { ok: false, reason: `direction: ${direction.reason}` };
  const phase = validateAnswerBlock(raw.phase, PHASES);
  if (!phase.ok) return { ok: false, reason: `phase: ${phase.reason}` };
  const phaseChoice = (raw.phase as Record<string, unknown>)["choice"];
  if (FORBIDDEN_PHASE_LABELS.includes(phaseChoice as never)) {
    return { ok: false, reason: "forbidden UNKNOWN-equivalent phase choice" };
  }
  return {
    ok: true,
    answers: {
      structure: structure.block,
      direction: direction.block,
      phase: phase.block,
    },
  };
}

/** Validate the full provider result against the pin (all three questions). */
export function validateProviderResult(args: {
  model: string | undefined;
  answers: unknown;
  usage: unknown;
  pinnedModel: string;
}): { ok: true; answers: Jrv2Response["answers"]; usage: { input_tokens: number; output_tokens: number } } | {
  ok: false;
  reason: string;
} {
  const { model, answers, usage, pinnedModel } = args;
  if (model !== pinnedModel) {
    return {
      ok: false,
      reason: `response model ${model === undefined ? "<absent>" : model} != pin ${pinnedModel}`,
    };
  }
  const a = validateAnswers(answers);
  if (!a.ok) return { ok: false, reason: a.reason };
  const u = validateUsage(usage);
  if (!u.ok) return { ok: false, reason: u.reason };
  return { ok: true, answers: a.answers, usage: u.usage };
}

export function makeResponseLine(args: {
  stateId: string;
  inputDigest: string;
  latencyMs: number;
}): Jrv2Response {
  return {
    schema: QUESTION_IO_SCHEMA,
    state_id: args.stateId,
    status: "LOCAL_INVALID",
    input_digest: args.inputDigest,
    latency_ms: args.latencyMs,
  };
}
