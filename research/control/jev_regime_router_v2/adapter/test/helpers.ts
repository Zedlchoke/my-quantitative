// Shared helpers for the jrv2 adapter test suite.
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

export function tmpDir(prefix = "jrv2-test-"): string {
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

const FULL_BINS: Record<string, string> = {
  fast_trend: "weak_up",
  slow_trend: "flat",
  trend_strength: "medium",
  volatility_regime: "normal",
  drawdown_state: "mild",
  range_location: "middle",
  close_location: "neutral",
  volume_state: "normal",
  dist_to_ema: "at",
};

const FULL_NUMERICS: Record<string, number> = {
  short_return: 0.002,
  medium_return: 0.011,
  long_return: 0.28,
  ema_slope_fast: 0.0009,
  ema_slope_slow: 0.0004,
  dist_ema: 1.2,
  adx14: 34,
  atr_pct: 0.008,
  rv_pctile: 0.62,
  dd_168: -0.03,
  dist_low: 0.3,
  range_pos: 0.42,
  vol_z: 0.35,
  clv_24: 0.62,
};

export function makeRequestLine(opts?: {
  stateId?: string;
  bins?: Record<string, string>;
  numerics?: Record<string, number>;
  priorStructure?: string;
  priorDirection?: string;
  requestedModel?: string;
  /** producer-computed digest; computed here only because the test helper
   *  plays the producer role (default states avoid the float-format
   *  divergence window; golden vectors carry explicit Python digests). */
  inputDigest?: string;
}): string {
  const bins = opts?.bins ?? FULL_BINS;
  const numerics = opts?.numerics ?? FULL_NUMERICS;
  const priorStructure = opts?.priorStructure ?? "TREND_UP";
  const priorDirection = opts?.priorDirection ?? "UP";
  const requestedModel = opts?.requestedModel ?? "jev-canary-x";
  const state = {
    bins,
    numerics,
    prior_structure: priorStructure,
    prior_direction: priorDirection,
  };
  const inputDigest =
    opts?.inputDigest ?? computeInputDigest(state, requestedModel);
  return JSON.stringify({
    schema: "jrv2_question_io@1",
    state_id: opts?.stateId ?? hex16(1),
    state,
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
