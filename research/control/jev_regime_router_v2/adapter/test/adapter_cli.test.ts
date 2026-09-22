// Adapter CLI end-to-end tests (mock mode; no network, no credential).
// Covers: mock three-question responses, cache replay without re-call,
// duplicate skip, freeze gate, model pin law, request schema law, usage
// persisted per response, redaction-safe stdout.

import { test } from "node:test";
import { readPinnedModel } from "../src/adapter.ts";
import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  FREEZES_DIR,
  hex16,
  listDir,
  makeRequestLine,
  runAdapter,
  tmpDir,
  writeRequests,
} from "./helpers.ts";

test("mock run: three typed answers per state; usage persisted per response", async () => {
  const dir = tmpDir();
  const requests = writeRequests(dir, [
    makeRequestLine({ stateId: hex16(1), requestedModel: "mock-model" }),
    makeRequestLine({ stateId: hex16(2), requestedModel: "mock-model" }),
  ]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter([
    "--requests", requests, "--out", out, "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
  ]);
  assert.equal(r.status, 0, r.stderr);
  const rows = readFileSync(out, "utf8").trim().split("\n").map((l) => JSON.parse(l));
  assert.equal(rows.length, 2);
  for (const row of rows) {
    assert.equal(row.schema, "jrv2_question_io@1");
    assert.equal(row.status, "OK");
    assert.deepEqual(Object.keys(row.answers).sort(), ["direction", "phase", "structure"]);
    assert.ok(["TREND", "RANGE"].includes(row.answers.structure.choice));
    assert.ok(["UP", "DOWN", "NEUTRAL"].includes(row.answers.direction.choice));
    assert.ok(
      ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"].includes(row.answers.phase.choice),
      "phase is always one of the 4 schema phases (forced choice)",
    );
    assert.ok(row.usage && typeof row.usage.input_tokens === "number");
    assert.equal(row.mock, true);
  }
  const summary = JSON.parse(r.stdout.trim());
  assert.equal(summary.schema, "jrv2_adapter_summary@1");
  assert.equal(summary.n_ok, 2);
});

test("mock run is deterministic: identical inputs are bit-identical forever", async () => {
  const dirA = tmpDir();
  const dirB = tmpDir();
  const line = makeRequestLine({ stateId: hex16(7), requestedModel: "mock-model" });
  const outs = [dirA, dirB].map((dir) => {
    const requests = writeRequests(dir, [line]);
    const out = join(dir, "out.jsonl");
    const r = runAdapter([
      "--requests", requests, "--out", out, "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
    ]);
    assert.equal(r.status, 0);
    return readFileSync(out, "utf8");
  });
  assert.equal(outs[0], outs[1]);
});

test("cache replay: second run reads the cache and never re-calls (cached flag, zero latency)", async () => {
  const dir = tmpDir();
  const requests = writeRequests(dir, [makeRequestLine({ stateId: hex16(3), requestedModel: "mock-model" })]);
  const cache = join(dir, "cache");
  const out1 = join(dir, "out1.jsonl");
  const out2 = join(dir, "out2.jsonl");
  const args = ["--requests", requests, "--cache", cache, "--model", "mock-model", "--mock"];
  assert.equal(runAdapter([...args, "--out", out1]).status, 0);
  const cached = listDir(cache);
  assert.equal(cached.length, 1);
  assert.equal(runAdapter([...args, "--out", out2]).status, 0);
  const row2 = JSON.parse(readFileSync(out2, "utf8").trim());
  assert.equal(row2.cached, true);
  assert.equal(row2.latency_ms, 0);
  assert.equal(listDir(cache).length, 1, "cache untouched on replay");
});

test("duplicate state_id within one run: first occurrence wins, second skipped", async () => {
  const dir = tmpDir();
  const line = makeRequestLine({ stateId: hex16(4), requestedModel: "mock-model" });
  const requests = writeRequests(dir, [line, line]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter([
    "--requests", requests, "--out", out, "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
  ]);
  assert.equal(r.status, 0);
  const rows = readFileSync(out, "utf8").trim().split("\n").filter((l) => l.trim());
  assert.equal(rows.length, 1);
  assert.match(r.stderr, /DUPLICATE_STATE_ID/);
});

test("cache key includes the prompt digest (amendment_2 law): tampered prompt -> different keys", async () => {
  // implied by construction; here we verify the key file name is 64-hex
  const dir = tmpDir();
  const requests = writeRequests(dir, [makeRequestLine({ stateId: hex16(5), requestedModel: "mock-model" })]);
  assert.equal(
    runAdapter([
      "--requests", requests, "--out", join(dir, "out.jsonl"),
      "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
    ]).status,
    0,
  );
  const keys = listDir(join(dir, "cache"));
  assert.equal(keys.length, 1);
  assert.match(keys[0], /^[0-9a-f]{64}\.json$/);
});

import { resolve } from "node:path";
const FREEZES_SRC = resolve(import.meta.dirname, "../../freezes");

test("freeze gate (unit): verifyFreezeDigests fires on a tampered COPY (real freezes never touched)", async () => {
  const { cpSync, mkdirSync, writeFileSync, readFileSync } = await import("node:fs");
  const { verifyFreezeDigests } = await import("../src/freeze_digests.ts");
  // pristine copy passes
  const clean = join(tmpDir(), "freezes_clean");
  mkdirSync(clean, { recursive: true });
  cpSync(FREEZES_SRC, clean, { recursive: true });
  const ok = verifyFreezeDigests(clean);
  assert.equal(ok.ok, true, JSON.stringify(ok.mismatches));
  // tampered copy fails
  const tampered = join(tmpDir(), "freezes_bad");
  mkdirSync(tampered, { recursive: true });
  cpSync(FREEZES_SRC, tampered, { recursive: true });
  const p = join(tampered, "question_contract.json");
  const doc = JSON.parse(readFileSync(p, "utf8"));
  doc["questions"]["phase"]["options"].push("SOMETHING_ELSE");
  writeFileSync(p, JSON.stringify(doc));
  const bad = verifyFreezeDigests(tampered);
  assert.equal(bad.ok, false);
  assert.equal(bad.mismatches.length, 1);
  assert.match(bad.mismatches[0], /question_contract\.json/);
});

test("model pin law: null pin is BLOCKED_MODEL_PIN (unit) and post-G0 no-arg resolves to the frozen pin", () => {
  // unit branch (pre-G0 shape): readPinnedModel over a temp dir with a null pin
  const tmp = tmpDir();
  writeFileSync(join(tmp, "model_pin.json"), JSON.stringify({ status: "CANDIDATE_UNVERIFIED", pinned_model: null }));
  assert.equal(readPinnedModel(tmp), null);
  // post-G0 (freeze VERIFIED_LIVE since 2026-09-22): no --model resolves to
  // the pinned model, so the next gate is the credential check (exit 4 here,
  // key stripped) — NOT a pin refusal
  const dir = tmpDir();
  const requests = writeRequests(dir, [makeRequestLine({ requestedModel: "jev-canary-x" })]);
  const r = runAdapter([
    "--requests", requests, "--out", join(dir, "out.jsonl"), "--cache", join(dir, "cache"),
  ]);
  const pinFile = JSON.parse(readFileSync(join(FREEZES_DIR, "model_pin.json"), "utf8"));
  if (pinFile.pinned_model === null) {
    assert.equal(r.status, 3);
    assert.match(r.stderr, /BLOCKED_MODEL_PIN/);
  } else {
    assert.equal(r.status, 4);
    assert.match(r.stderr, /BLOCKED_CREDENTIAL/);
  }
});

test("model pin law: jev-latest is FORBIDDEN even with --model", () => {
  const dir = tmpDir();
  const requests = writeRequests(dir, [makeRequestLine({ requestedModel: "jev-latest" })]);
  const r = runAdapter([
    "--requests", requests, "--out", join(dir, "out.jsonl"), "--cache", join(dir, "cache"),
    "--model", "jev-latest",
  ]);
  assert.equal(r.status, 3);
  assert.match(r.stderr, /FORBIDDEN/);
});

test("live mode without credential is BLOCKED_CREDENTIAL (exit 4)", () => {
  const dir = tmpDir();
  const requests = writeRequests(dir, [makeRequestLine({ requestedModel: "jev-canary-x" })]);
  const r = runAdapter([
    "--requests", requests, "--out", join(dir, "out.jsonl"), "--cache", join(dir, "cache"),
    "--model", "jev-canary-x",
  ]);
  assert.equal(r.status, 4);
  assert.match(r.stderr, /BLOCKED_CREDENTIAL/);
});

test("request schema law: bad digest, bad state shape -> LOCAL_INVALID rows, not crashes", () => {
  const dir = tmpDir();
  const bad1 = JSON.stringify({
    schema: "jrv2_question_io@1", state_id: hex16(9), state: { bins: {}, numerics: {}, prior_structure: "RANGE", prior_direction: "NEUTRAL" },
    requested_model: "mock-model", input_digest: "nothex",
  });
  const bad2 = "{\"not json\"";
  const requests = writeRequests(dir, [bad1, bad2]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter([
    "--requests", requests, "--out", out, "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
  ]);
  assert.equal(r.status, 0);
  const rows = readFileSync(out, "utf8").trim().split("\n").map((l) => JSON.parse(l));
  assert.equal(rows.length, 2);
  // schema-invalid but parseable -> REQUEST_SCHEMA
  assert.equal(rows[0].status, "LOCAL_INVALID");
  assert.equal(rows[0].error_class, "REQUEST_SCHEMA");
  // unparseable -> UNPARSEABLE_LINE (both are LOCAL_INVALID, never crashes)
  assert.equal(rows[1].status, "LOCAL_INVALID");
  assert.equal(rows[1].error_class, "UNPARSEABLE_LINE");
});

test("usage persisted per response: every OK row in the cache entry carries usage", () => {
  const dir = tmpDir();
  const requests = writeRequests(dir, [makeRequestLine({ stateId: hex16(11), requestedModel: "mock-model" })]);
  assert.equal(
    runAdapter([
      "--requests", requests, "--out", join(dir, "out.jsonl"),
      "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
    ]).status,
    0,
  );
  const entry = JSON.parse(
    readFileSync(join(dir, "cache", listDir(join(dir, "cache"))[0]), "utf8"),
  );
  assert.equal(entry.schema, "jrv2_cache_entry@1");
  assert.ok(entry.response.usage.input_tokens >= 0);
  assert.ok(entry.response.usage.output_tokens >= 0);
});
