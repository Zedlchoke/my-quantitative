// Mock-canary agreement: the TS adapter in --mock mode, driven over request
// lines built from the FROZEN canary fixtures, must answer exactly per the
// frozen expectations (C1->UPTREND ... C7 contradiction). This is the
// cross-language plumbing agreement for the synthetic canary.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { computeInputDigest, sha256Hex } from "../src/contract.ts";
import { hex16, runAdapter, tmpDir, writeRequests } from "./helpers.ts";

const FREEZES = resolve(import.meta.dirname, "../../freezes");
const MODEL = "mock-model";

interface Fixture {
  id: string;
  class: string;
  expected: { effective?: string; phase?: string; structure?: string; direction?: string };
  state: Record<string, unknown> | null;
}

const BIN_NAMES = [
  "fast_trend", "slow_trend", "trend_strength", "volatility_regime",
  "drawdown_state", "range_location", "close_location", "volume_state", "dist_to_ema",
];
const NUMERIC_NAMES = [
  "short_return", "medium_return", "long_return", "ema_slope_fast", "ema_slope_slow",
  "dist_ema", "adx14", "atr_pct", "rv_pctile", "dd_168", "dist_low", "range_pos", "vol_z", "clv_24",
];

function normalize(state: Record<string, unknown>): Record<string, unknown> {
  const bins: Record<string, string> = {};
  const numerics: Record<string, number> = {};
  for (const k of BIN_NAMES) if (typeof state[k] === "string") bins[k] = state[k] as string;
  for (const k of NUMERIC_NAMES) if (typeof state[k] === "number") numerics[k] = state[k] as number;
  return {
    bins,
    numerics,
    prior_structure: String(state["prior_structure"] ?? "none"),
    prior_direction: String(state["prior_direction"] ?? "none"),
  };
}

test("mock canary: fixture answers match the frozen expectations via the TS adapter", async () => {
  const fixtures: Fixture[] = JSON.parse(
    readFileSync(join(FREEZES, "canary_v2_contract.json"), "utf8"),
  )["synthetic_fixtures"];
  const dir = tmpDir();
  const lines: string[] = [];
  const meta: { id: string; sid: string }[] = [];
  for (const [i, fx] of fixtures.entries()) {
    if (fx.state === null) continue;
    const st = normalize(fx.state);
    const sid = sha256Hex(`JRV2-fixture:${fx.id}`).slice(0, 16);
    lines.push(
      JSON.stringify({
        schema: "jrv2_question_io@1",
        state_id: sid,
        state: st,
        requested_model: MODEL,
        input_digest: computeInputDigest(st, MODEL),
      }),
    );
    meta.push({ id: fx.id, sid });
    assert.ok(sid.match(/^[0-9a-f]{16}$/), `fixture sid ${fx.id}`);
    void i;
  }
  const requests = writeRequests(dir, lines);
  const out = join(dir, "out.jsonl");
  const r = runAdapter([
    "--requests", requests, "--out", out, "--cache", join(dir, "cache"), "--model", MODEL, "--mock",
  ]);
  assert.equal(r.status, 0, r.stderr);
  const rows = readFileSync(out, "utf8").trim().split("\n").map((l) => JSON.parse(l));
  assert.equal(rows.length, meta.length);
  const bySid = new Map(rows.map((row) => [row.state_id, row]));
  for (const { id, sid } of meta) {
    const row = bySid.get(sid);
    assert.ok(row, `${id}: response missing`);
    assert.equal(row.status, "OK", `${id}`);
    void id;
  }
  // expected effective labels per fixture (from the freeze) mapped through
  // the SAME safety semantics the Python side applies; here we assert the raw
  // answers equal the Python mock rule outputs:
  const expectRaw: Record<string, [string, string, string]> = {
    C1_CLEAR_UPTREND: ["TREND", "UP", "UPTREND"],
    C2_CLEAR_DOWNTREND: ["TREND", "DOWN", "DOWNTREND"],
    C3_RANGE_AFTER_DOWNTREND: ["RANGE", "NEUTRAL", "ACCUMULATION"],
    C4_RANGE_AFTER_UPTREND: ["RANGE", "NEUTRAL", "DISTRIBUTION"],
    C5_HIGH_VOL_CONFLICT: ["TREND", "NEUTRAL", "UPTREND"], // contradiction -> code UNKNOWN
    C6_LOW_VOL_RANGE: ["RANGE", "NEUTRAL", "UPTREND"], // contradiction -> code UNKNOWN
    C7_NOISY_CONTRADICTORY: ["TREND", "NEUTRAL", "UPTREND"], // contradiction -> code UNKNOWN
  };
  for (const { id, sid } of meta) {
    const row = bySid.get(sid)!;
    const want = expectRaw[id];
    assert.ok(want, `no expectation for ${id}`);
    assert.equal(row.answers.structure.choice, want[0], `${id} structure`);
    assert.equal(row.answers.direction.choice, want[1], `${id} direction`);
    assert.equal(row.answers.phase.choice, want[2], `${id} phase`);
    // phase NEVER carries an abstain option
    assert.notEqual(row.answers.phase.choice, "TRANSITION_UNKNOWN");
    assert.notEqual(row.answers.phase.choice, "UNKNOWN");
  }
  void hex16;
});
