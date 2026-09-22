// Shared helpers for the lane-ts test suite.
// SAFETY LAW: child adapter runs NEVER inherit a real TYPESAFE_API_KEY —
// the helper strips it from the child environment unless a test explicitly
// injects a fake sentinel value.

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, writeFileSync, existsSync, readFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { computeInputDigest } from "../src/contract.ts";

export const ADAPTER_TS = resolve(import.meta.dirname, "../src/adapter.ts");
export const FREEZES_DIR = resolve(import.meta.dirname, "../../freezes");

export function tmpDir(prefix = "jrv1-test-"): string {
  return mkdtempSync(join(tmpdir(), prefix));
}

export interface RunResult {
  status: number;
  stdout: string;
  stderr: string;
}

/** Run the adapter CLI in a child process. TYPESAFE_API_KEY is always stripped. */
export function runAdapter(args: readonly string[], extraEnv?: Record<string, string>): RunResult {
  const env: NodeJS.ProcessEnv = { ...process.env };
  delete env.TYPESAFE_API_KEY; // never propagate a host key into tests
  if (extraEnv !== undefined) Object.assign(env, extraEnv);
  const r = spawnSync(process.execPath, [ADAPTER_TS, ...args], { encoding: "utf8", env });
  return {
    status: r.status ?? -1,
    stdout: r.stdout ?? "",
    stderr: r.stderr ?? "",
  };
}

export function hex16(n: number): string {
  return n.toString(16).padStart(16, "0");
}

export function makeRequestLine(opts?: {
  stateId?: string;
  vector?: number[];
  prior?: string | null;
  requestedModel?: string;
  /** producer-computed digest; computed here only because the test helper
   *  plays the producer role (all default vectors avoid the float-format
   *  divergence window; golden vectors carry explicit Python digests). */
  inputDigest?: string;
}): string {
  const vector =
    opts?.vector ?? [0.01, 0.02, 0.05, 0.11, 0.28, 0.004, 0.0025, 1.2, 34, 0.008, 0.62, -0.03, 0.3, 0.42, 0.35, 0.62];
  const requestedModel = opts?.requestedModel ?? "jev-canary-x";
  const inputDigest =
    opts?.inputDigest ??
    computeInputDigest({ feature_vector: vector, prior_regime: opts?.prior ?? null }, requestedModel);
  return JSON.stringify({
    schema: "jrv1_decision_io@1",
    state_id: opts?.stateId ?? hex16(1),
    state: {
      feature_vector: vector,
      prior_regime: opts?.prior ?? null,
    },
    requested_model: requestedModel,
    input_digest: inputDigest,
  });
}

export function writeRequests(dir: string, lines: readonly string[]): string {
  const p = join(dir, "requests.jsonl");
  writeFileSync(p, lines.join("\n") + "\n", "utf8");
  return p;
}

export function readFileIfExists(p: string): string | null {
  return existsSync(p) ? readFileSync(p, "utf8") : null;
}

export function sha256OfFile(p: string): string {
  return createHash("sha256").update(readFileSync(p)).digest("hex");
}

export function listDir(p: string): string[] {
  return existsSync(p) ? readdirSync(p).sort() : [];
}
