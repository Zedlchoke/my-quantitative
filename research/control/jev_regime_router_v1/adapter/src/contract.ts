// jrv1_decision_io@1 — frozen I/O contract helpers for the Jev adapter.
// Boundary schema, canonical JSON, digests and validation live here so the
// exact same code runs on the writer side (adapter) and in tests.
//
// Contract source of truth:
//   freezes/adapter_contract.json   (jrv1_adapter_contract@1)
//   freezes/regime_label_contract.json (jrv1_regime_label_contract@1)

import { createHash } from "node:crypto";

export const DECISION_IO_SCHEMA = "jrv1_decision_io@1" as const;

export const LABELS = [
  "ACCUMULATION",
  "UPTREND",
  "DISTRIBUTION",
  "DOWNTREND",
  "TRANSITION_UNKNOWN",
] as const;

export type RegimeLabel = (typeof LABELS)[number];

export const LABEL_SET: ReadonlySet<string> = new Set<string>(LABELS);

export const STATUSES = [
  "OK",
  "TIMEOUT",
  "PROVIDER_ERROR",
  "SCHEMA_ERROR",
  "LOCAL_INVALID",
] as const;

export type ResponseStatus = (typeof STATUSES)[number];

export const FEATURE_VECTOR_LENGTH = 16;

// ---------------------------------------------------------------------------
// canonical json + digests
//
// AMENDMENT 1 (adapter_contract.json amendment_1, A7-1 F1 — producer-digest
// echo law): input_digest is computed ONLY by the producer (Python, from its
// stored state + requested_model via its canonical_json). The request line
// carries it; the adapter validates the 64-hex format and echoes it verbatim
// in every response line and cache entry. The adapter MUST NOT recompute it:
// canonicalJson/JSON.stringify renders doubles differently from Python
// json.dumps (e.g. 1e-05 vs 0.00001, 1.234e-07 vs 1.234e-7, 34.0 vs 34),
// which measured 10/25 digest mismatches on real request lines. The pure
// functions below are retained ONLY for golden cross-language tests that
// prove the old divergence and the echo path's immunity.
// ---------------------------------------------------------------------------

/** Recursively sort object keys; serialize with no whitespace. */
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
    if (v === undefined) continue; // JSON has no undefined; mirror JSON.stringify
    parts.push(JSON.stringify(k) + ":" + canonicalJson(v));
  }
  return "{" + parts.join(",") + "}";
}

/** sha256 hex of a UTF-8 string. */
export function sha256Hex(s: string): string {
  return createHash("sha256").update(s, "utf8").digest("hex");
}

/**
 * LEGACY (golden tests only — never used to process a request):
 * sha256(canonical_json(state) || requested_model) as the TS side used to
 * recompute it before amendment_1. Kept so the cross-language golden vectors
 * can prove the old divergence.
 */
export function computeInputDigest(state: unknown, requestedModel: string): string {
  return sha256Hex(canonicalJson(state) + requestedModel);
}

/** Cache entry key per freeze: sha256(model || state_id || input_digest). */
export function computeCacheKey(model: string, stateId: string, inputDigest: string): string {
  return sha256Hex(model + stateId + inputDigest);
}

// ---------------------------------------------------------------------------
// request line
// ---------------------------------------------------------------------------

export interface Jrv1Request {
  schema: string;
  state_id: string;
  state: Jrv1State;
  requested_model: string;
  /** producer-computed digest, echoed verbatim (amendment_1) */
  input_digest: string;
}

// (object type alias — structurally assignable to the SDK's EntryType JSON shape)
export type Jrv1State = {
  feature_vector: number[];
  prior_regime: RegimeLabel | null;
};

export type RequestValidation =
  | { ok: true; request: Jrv1Request }
  | { ok: false; reason: string };

const HEX16 = /^[0-9a-f]{16}$/;
/** amendment_1: the producer-computed input_digest is always 64 lowercase hex. */
export const HEX64 = /^[0-9a-f]{64}$/;

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

export function validateRequestLine(raw: unknown): RequestValidation {
  if (!isPlainObject(raw)) return { ok: false, reason: "request line is not an object" };
  if (raw.schema !== DECISION_IO_SCHEMA) {
    return { ok: false, reason: `schema must be ${DECISION_IO_SCHEMA}` };
  }
  if (typeof raw.state_id !== "string" || !HEX16.test(raw.state_id)) {
    return { ok: false, reason: "state_id must be 16 lowercase hex chars" };
  }
  if (typeof raw.requested_model !== "string" || raw.requested_model.length === 0) {
    return { ok: false, reason: "requested_model must be a non-empty string" };
  }
  // amendment_1 (A7-1 F1): the producer-computed input_digest is REQUIRED.
  // Missing or non-64-hex digests are refused — the adapter never recomputes.
  if (typeof raw.input_digest !== "string" || !HEX64.test(raw.input_digest)) {
    return { ok: false, reason: "input_digest must be producer-computed 64 lowercase hex chars" };
  }
  const st = raw.state;
  if (!isPlainObject(st)) return { ok: false, reason: "state must be an object" };
  const fv = st.feature_vector;
  if (
    !Array.isArray(fv) ||
    fv.length !== FEATURE_VECTOR_LENGTH ||
    !fv.every((x) => typeof x === "number" && Number.isFinite(x))
  ) {
    return {
      ok: false,
      reason: `state.feature_vector must be ${FEATURE_VECTOR_LENGTH} finite numbers`,
    };
  }
  const pr = st.prior_regime;
  if (pr !== null && !(typeof pr === "string" && LABEL_SET.has(pr))) {
    return { ok: false, reason: "state.prior_regime must be a contract label or null" };
  }
  return {
    ok: true,
    request: {
      schema: DECISION_IO_SCHEMA,
      state_id: raw.state_id,
      state: { feature_vector: fv.slice() as number[], prior_regime: pr as RegimeLabel | null },
      requested_model: raw.requested_model,
      input_digest: raw.input_digest,
    },
  };
}

// ---------------------------------------------------------------------------
// response line
// ---------------------------------------------------------------------------

export interface Jrv1Response {
  schema: string;
  state_id: string;
  status: ResponseStatus;
  regime?: RegimeLabel;
  probabilities?: Record<string, number>;
  confidence?: number;
  model?: string;
  request_id?: string;
  input_digest: string;
  latency_ms: number;
  error_class?: string;
  /** extra non-contract annotations (cached/mock) */
  cached?: boolean;
  mock?: boolean;
}

/**
 * Validate the 5-label probability block: exactly the contract labels, each
 * finite >= 0, sum within 1 +/- 0.01.
 */
export function validateProbabilities(
  probs: unknown,
): { ok: true; probabilities: Record<string, number> } | { ok: false; reason: string } {
  if (!isPlainObject(probs)) return { ok: false, reason: "probabilities must be an object" };
  const keys = Object.keys(probs);
  if (keys.length !== LABELS.length || !keys.every((k) => LABEL_SET.has(k))) {
    return { ok: false, reason: "probabilities must carry exactly the 5 contract labels" };
  }
  let sum = 0;
  const out: Record<string, number> = {};
  for (const k of LABELS) {
    const v = probs[k];
    if (typeof v !== "number" || !Number.isFinite(v) || v < 0) {
      return { ok: false, reason: `probability for ${k} must be a finite number >= 0` };
    }
    out[k] = v;
    sum += v;
  }
  if (Math.abs(sum - 1) > 0.01) {
    return { ok: false, reason: `probability sum ${sum} outside 1 +/- 0.01` };
  }
  return { ok: true, probabilities: out };
}

/** Validate a provider answer block (choice response) against the pin. */
export function validateProviderAnswer(args: {
  model: string | undefined;
  answer: unknown;
  pinnedModel: string;
}): { ok: true; regime: RegimeLabel; probabilities: Record<string, number>; confidence: number } | {
  ok: false;
  reason: string;
} {
  const { model, answer, pinnedModel } = args;
  if (model !== pinnedModel) {
    return { ok: false, reason: `response model ${model === undefined ? "<absent>" : model} != pin ${pinnedModel}` };
  }
  if (!isPlainObject(answer) || answer.type !== "choice") {
    return { ok: false, reason: "answer is not a choice response" };
  }
  const choice = answer.choice;
  if (typeof choice !== "string" || !LABEL_SET.has(choice)) {
    return { ok: false, reason: "free-text or unsupported regime label" };
  }
  const probs = validateProbabilities(answer.probabilities);
  if (!probs.ok) return { ok: false, reason: probs.reason };
  const confidence = answer.confidence;
  if (typeof confidence !== "number" || !Number.isFinite(confidence)) {
    return { ok: false, reason: "confidence must be a finite number" };
  }
  return { ok: true, regime: choice as RegimeLabel, probabilities: probs.probabilities, confidence };
}

export function makeResponseLine(args: {
  stateId: string;
  inputDigest: string;
  latencyMs: number;
}): Jrv1Response {
  return {
    schema: DECISION_IO_SCHEMA,
    state_id: args.stateId,
    status: "LOCAL_INVALID",
    input_digest: args.inputDigest,
    latency_ms: args.latencyMs,
  };
}
