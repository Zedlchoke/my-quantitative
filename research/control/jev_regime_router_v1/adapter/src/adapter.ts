// Jev (TypeSafe AI) adapter — JEV-REGIME-ROUTER-V1 lane-ts.
//
//   node src/adapter.ts --requests <file.jsonl> --out <responses.jsonl> \
//        --cache <dir> [--model <pin>] [--mock]
//
// Laws implemented here (plans/PLAN_jev_regime_router_v1.md §5/§5a/§8,
// freezes/adapter_contract.json incl. amendment_1):
//   - freeze gate: refuses to run unless freezes/regime_label_contract.json
//     sha256-matches the digest embedded in src/freeze_digests.ts
//   - model pin: --model, else freezes/model_pin.json pinned_model;
//     'jev-latest' or a missing pin is BLOCKED_MODEL_PIN (exit 3) unless --mock
//   - credential: TYPESAFE_API_KEY from environment only (name-only presence
//     checks; the value is never read into a string that could be logged)
//   - amendment_1 (A7-1 F1 producer-digest echo law): the request line carries
//     input_digest computed by the Python producer; the adapter validates the
//     64-hex format and ECHOES it verbatim in every response and cache entry.
//     The adapter NEVER recomputes it (single canonicalization authority).
//   - call discipline: maxRetries 0, timeout 10000 ms, NO retries, NO re-asks,
//     one call per state_id (duplicates warned + skipped)
//   - cache: append-only per-state JSON entries keyed
//     sha256(model || state_id || input_digest); existing entries are never
//     overwritten; replay reads cache and never re-calls
//   - stdout is a single redaction-safe summary JSON line (no headers, no key,
//     no state bodies)

import { openSync, closeSync, writeSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { pathToFileURL, fileURLToPath } from "node:url";
import { join } from "node:path";
import {
  APIError,
  APITimeoutError,
  TypeSafeClient,
} from "@typesafe-ai/sdk";
import {
  DECISION_IO_SCHEMA,
  computeCacheKey,
  sha256Hex,
  validateProviderAnswer,
  validateRequestLine,
} from "./contract.ts";
import type { Jrv1Request, Jrv1Response, ResponseStatus } from "./contract.ts";
import { verifyFreezeDigests } from "./freeze_digests.ts";
import { buildRegimeQuestions } from "./prompt.ts";
import { buildMockResponse } from "./mock.ts";

export const CALL_TIMEOUT_MS = 10000;
const FREEZE_FORBIDDEN_MODEL = "jev-latest";
const MOCK_FALLBACK_MODEL = "mock-model";
const CACHE_ENTRY_SCHEMA = "jrv1_cache_entry@1";
const SUMMARY_SCHEMA = "jrv1_adapter_summary@1";

export const EXIT_OK = 0;
export const EXIT_USAGE = 2;
export const EXIT_BLOCKED_MODEL_PIN = 3;
export const EXIT_BLOCKED_CREDENTIAL = 4;
export const EXIT_FREEZE_MISMATCH = 5;

// ---------------------------------------------------------------------------
// CLI plumbing
// ---------------------------------------------------------------------------

export interface AdapterArgs {
  requests?: string;
  out?: string;
  cache?: string;
  model?: string;
  mock: boolean;
}

export function parseArgs(argv: readonly string[]): { args: AdapterArgs; unknown: string[] } {
  const args: AdapterArgs = { mock: false };
  const unknown: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--mock") args.mock = true;
    else if (a === "--model") args.model = argv[++i];
    else if (a === "--requests") args.requests = argv[++i];
    else if (a === "--out") args.out = argv[++i];
    else if (a === "--cache") args.cache = argv[++i];
    else unknown.push(a);
  }
  return { args, unknown };
}

export function freezesDir(): string {
  return fileURLToPath(new URL("../../freezes/", import.meta.url));
}

/** Pinned model from freezes/model_pin.json; null when absent/unfilled. */
export function readPinnedModel(dir: string): string | null {
  let raw: unknown;
  try {
    raw = JSON.parse(readFileSync(join(dir, "model_pin.json"), "utf8"));
  } catch {
    return null;
  }
  if (typeof raw !== "object" || raw === null) return null;
  const pin = (raw as Record<string, unknown>).pinned_model;
  return typeof pin === "string" && pin.length > 0 ? pin : null;
}

// ---------------------------------------------------------------------------
// cache (append-only per-state JSON; existing entries are never overwritten)
// ---------------------------------------------------------------------------

export interface CacheEntry {
  schema: string;
  key: string;
  mode: "mock" | "live";
  model: string;
  state_id: string;
  input_digest: string;
  request_sha256: string;
  response_sha256: string;
  request: unknown;
  response: Jrv1Response;
  stored_at: string;
}

function canonicalForHash(v: unknown): string {
  return JSON.stringify(v);
}

export function cachePut(cacheDir: string, entry: CacheEntry): boolean {
  const p = join(cacheDir, `${entry.key}.json`);
  const body = JSON.stringify(entry, null, 1) + "\n";
  let fd: number;
  try {
    fd = openSync(p, "wx"); // O_EXCL: refuse to touch an existing entry
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "EEXIST") return false;
    throw err;
  }
  try {
    writeSync(fd, body);
  } finally {
    closeSync(fd);
  }
  return true;
}

export function cacheGet(cacheDir: string, key: string): CacheEntry | null {
  let raw: unknown;
  try {
    raw = JSON.parse(readFileSync(join(cacheDir, `${key}.json`), "utf8"));
  } catch {
    return null;
  }
  if (typeof raw !== "object" || raw === null) return null;
  const entry = raw as CacheEntry;
  if (entry.schema !== CACHE_ENTRY_SCHEMA) return null;
  if (typeof entry.response !== "object" || entry.response === null) return null;
  return entry;
}

// ---------------------------------------------------------------------------
// live client + provider error mapping
// ---------------------------------------------------------------------------

class MissingCredentialError extends Error {
  constructor() {
    super("credential not present in environment (name-only check)");
  }
}

export function constructClient(): TypeSafeClient {
  // name-only presence check; the value itself is never copied or logged
  if (process.env.TYPESAFE_API_KEY === undefined || process.env.TYPESAFE_API_KEY === "") {
    throw new MissingCredentialError();
  }
  return new TypeSafeClient({
    timeout: CALL_TIMEOUT_MS,
    retry: { maxRetries: 0 },
    logLevel: "warn",
  });
}

export interface ProviderErrorInfo {
  status: Extract<ResponseStatus, "TIMEOUT" | "PROVIDER_ERROR">;
  error_class: string;
  request_id?: string;
}

/** APITimeoutError -> TIMEOUT; everything else -> PROVIDER_ERROR. No retries. */
export function classifyProviderError(err: unknown): ProviderErrorInfo {
  const error_class = err instanceof Error ? err.constructor.name : "Unknown";
  if (err instanceof APITimeoutError) return { status: "TIMEOUT", error_class };
  const info: ProviderErrorInfo = { status: "PROVIDER_ERROR", error_class };
  // APIConnectionError (non-timeout) and generic exceptions carry no request id;
  // APIError does.
  if (err instanceof APIError && typeof err.requestId === "string") {
    info.request_id = err.requestId;
  }
  return info;
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

function localInvalidRow(stateId: string, rawDigest: unknown, errorClass: string): Jrv1Response {
  // amendment_1: echo whatever digest string the request carried (never
  // recompute); "" only when the request carried no string at all. Python
  // ingest fail-closes any non-matching echo to SCHEMA_ERROR -> UNKNOWN.
  return {
    schema: DECISION_IO_SCHEMA,
    state_id: stateId,
    status: "LOCAL_INVALID",
    error_class: errorClass,
    input_digest: typeof rawDigest === "string" ? rawDigest : "",
    latency_ms: 0,
  };
}

export async function main(argv: readonly string[]): Promise<number> {
  const { args, unknown } = parseArgs(argv);
  if (unknown.length > 0 || !args.requests || !args.out || !args.cache) {
    console.error(
      "usage: node src/adapter.ts --requests <file.jsonl> --out <responses.jsonl> --cache <dir> [--model <pin>] [--mock]",
    );
    return EXIT_USAGE;
  }

  // --- freeze gate (required, both modes) ---------------------------------
  const freeze = verifyFreezeDigests(freezesDir());
  if (!freeze.ok) {
    console.error(`FREEZE_DIGEST_MISMATCH ${JSON.stringify(freeze.mismatches)}`);
    return EXIT_FREEZE_MISMATCH;
  }

  // --- model pin -----------------------------------------------------------
  const pin = args.model ?? readPinnedModel(freezesDir());
  if (!args.mock && (pin === null || pin === FREEZE_FORBIDDEN_MODEL)) {
    const why =
      pin === null
        ? "no --model given and freezes/model_pin.json has no pinned_model"
        : "jev-latest is FORBIDDEN in frozen replay (SDK default fallback trap)";
    console.error(`BLOCKED_MODEL_PIN: ${why}`);
    return EXIT_BLOCKED_MODEL_PIN;
  }
  const model = pin ?? MOCK_FALLBACK_MODEL;

  // --- read requests --------------------------------------------------------
  let text: string;
  try {
    text = readFileSync(args.requests, "utf8");
  } catch (err) {
    console.error(`USAGE_ERROR: cannot read requests file (${err instanceof Error ? err.message : String(err)})`);
    return EXIT_USAGE;
  }
  const lines = text.split("\n").filter((l) => l.trim().length > 0);
  mkdirSync(args.cache, { recursive: true });

  const rows: Jrv1Response[] = [];
  const seenStateIds = new Set<string>();
  let client: TypeSafeClient | undefined;
  let nOk = 0;
  let nErr = 0;
  let nCached = 0;
  let nDuplicateSkipped = 0;
  let nLocalInvalid = 0;
  let totalLatencyMs = 0;
  let inputTokensSum = 0;
  let anyUsage = false;

  for (const line of lines) {
    let raw: unknown;
    try {
      raw = JSON.parse(line);
    } catch {
      rows.push(localInvalidRow("", "", "UNPARSEABLE_LINE"));
      nLocalInvalid++;
      continue;
    }
    const check = validateRequestLine(raw);
    if (!check.ok) {
      const o = (typeof raw === "object" && raw !== null ? raw : {}) as Record<string, unknown>;
      rows.push(
        localInvalidRow(
          typeof o.state_id === "string" ? o.state_id : "",
          o.input_digest,
          "REQUEST_SCHEMA",
        ),
      );
      nLocalInvalid++;
      continue;
    }
    const req: Jrv1Request = check.request;

    // one call per state_id within a run: first occurrence wins
    if (seenStateIds.has(req.state_id)) {
      nDuplicateSkipped++;
      console.error(`WARNING DUPLICATE_STATE_ID ${req.state_id} skipped (one call per state_id)`);
      continue;
    }
    seenStateIds.add(req.state_id);

    // amendment_1: producer-computed digest, echoed verbatim — never recomputed
    const inputDigest = req.input_digest;
    const key = computeCacheKey(model, req.state_id, inputDigest);

    // replay reads cache, never re-calls
    const hit = cacheGet(args.cache, key);
    if (hit !== null) {
      const status = hit.response.status;
      rows.push({ ...hit.response, latency_ms: 0, cached: true });
      nCached++;
      if (status === "OK") nOk++;
      else nErr++;
      continue;
    }

    if (args.mock) {
      const row = buildMockResponse(req, model, inputDigest);
      cachePut(args.cache, {
        schema: CACHE_ENTRY_SCHEMA,
        key,
        mode: "mock",
        model,
        state_id: req.state_id,
        input_digest: inputDigest,
        request_sha256: sha256Hex(canonicalForHash(req)),
        response_sha256: sha256Hex(canonicalForHash(row)),
        request: req,
        response: row,
        stored_at: new Date().toISOString(),
      });
      rows.push(row);
      nOk++;
      continue;
    }

    // --- live path ---------------------------------------------------------
    if (client === undefined) {
      try {
        client = constructClient();
      } catch (err) {
        // No fabricated responses: emit a summary line and stop.
        const detail =
          err instanceof MissingCredentialError
            ? err.message
            : err instanceof Error
              ? err.constructor.name
              : "Unknown";
        console.error(
          JSON.stringify({
            status: "BLOCKED_CREDENTIAL",
            n_unprocessed_states: lines.length - rows.length,
            detail,
          }),
        );
        return EXIT_BLOCKED_CREDENTIAL;
      }
    }

    const t0 = performance.now();
    let resp: Jrv1Response;
    try {
      const { data, requestId } = await client
        .systemOne(
          { state: req.state, questions: buildRegimeQuestions(), model },
          { retry: { maxRetries: 0 }, timeout: CALL_TIMEOUT_MS },
        )
        .withResponse();
      const latencyMs = performance.now() - t0;
      totalLatencyMs += latencyMs;
      const answer = (data.answers as Record<string, unknown>)["regime"];
      const ans = validateProviderAnswer({ model: data.model, answer, pinnedModel: model });
      if (ans.ok) {
        resp = {
          schema: DECISION_IO_SCHEMA,
          state_id: req.state_id,
          status: "OK",
          regime: ans.regime,
          probabilities: ans.probabilities,
          confidence: ans.confidence,
          model: data.model,
          request_id: requestId,
          input_digest: inputDigest,
          latency_ms: latencyMs,
        };
        if (typeof data.usage?.input_tokens === "number") {
          inputTokensSum += data.usage.input_tokens;
          anyUsage = true;
        }
      } else {
        resp = {
          schema: DECISION_IO_SCHEMA,
          state_id: req.state_id,
          status: "SCHEMA_ERROR",
          error_class: "RESPONSE_SCHEMA",
          input_digest: inputDigest,
          latency_ms: latencyMs,
        };
      }
    } catch (err) {
      const latencyMs = performance.now() - t0;
      totalLatencyMs += latencyMs;
      const cls = classifyProviderError(err);
      resp = {
        schema: DECISION_IO_SCHEMA,
        state_id: req.state_id,
        status: cls.status,
        error_class: cls.error_class,
        ...(cls.request_id !== undefined ? { request_id: cls.request_id } : {}),
        input_digest: inputDigest,
        latency_ms: latencyMs,
      };
    }

    cachePut(args.cache, {
      schema: CACHE_ENTRY_SCHEMA,
      key,
      mode: "live",
      model,
      state_id: req.state_id,
      input_digest: inputDigest,
      request_sha256: sha256Hex(canonicalForHash(req)),
      response_sha256: sha256Hex(canonicalForHash(resp)),
      request: req,
      response: resp,
      stored_at: new Date().toISOString(),
    });
    rows.push(resp);
    if (resp.status === "OK") nOk++;
    else nErr++;
  }

  // --- write responses (same order as requests, duplicates skipped) --------
  writeFileSync(
    args.out,
    rows.map((r) => JSON.stringify(r)).join("\n") + (rows.length > 0 ? "\n" : ""),
  );

  const summary: Record<string, unknown> = {
    schema: SUMMARY_SCHEMA,
    mode: args.mock ? "mock" : "live",
    model,
    n_requests: lines.length,
    n_emitted: rows.length,
    n_ok: nOk,
    n_err: nErr,
    n_cached: nCached,
    n_duplicate_skipped: nDuplicateSkipped,
    n_local_invalid: nLocalInvalid,
    total_latency_ms: Math.round(totalLatencyMs * 1000) / 1000,
  };
  if (anyUsage) summary.input_tokens_sum = inputTokensSum;
  console.log(JSON.stringify(summary));
  return EXIT_OK;
}

const isMain =
  process.argv[1] !== undefined && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  main(process.argv.slice(2)).then((code) => process.exit(code));
}
