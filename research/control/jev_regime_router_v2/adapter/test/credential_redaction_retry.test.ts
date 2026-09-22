// Credential + redaction + retry-discipline laws for the jrv2 adapter.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { hex16, makeRequestLine, runAdapter, tmpDir, writeRequests } from "./helpers.ts";

const SRC = resolve(import.meta.dirname, "../src");

test("credential law: the adapter never reads the credential VALUE (name-only)", () => {
  for (const f of readdirSync(SRC)) {
    if (!f.endsWith(".ts")) continue;
    const text = readFileSync(join(SRC, f), "utf8");
    // the ONLY permitted occurrence is the process.env presence check
    const matches = text.match(/TYPESAFE_API_KEY/g) ?? [];
    for (const m of matches) {
      assert.ok(text.includes("process.env.TYPESAFE_API_KEY"), `${f}: unexpected credential reference`);
    }
    // never logging / stringifying the key
    assert.doesNotMatch(text, /console\.\w+\([^)]*TYPESAFE_API_KEY/);
  }
});

test("redaction law: mock stdout is a single summary line without state bodies", async () => {
  const dir = tmpDir();
  const requests = writeRequests(dir, [makeRequestLine({ stateId: hex16(21), requestedModel: "mock-model" })]);
  const r = runAdapter([
    "--requests", requests, "--out", join(dir, "out.jsonl"),
    "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
  ]);
  assert.equal(r.status, 0);
  const lines = r.stdout.trim().split("\n");
  assert.equal(lines.length, 1);
  const summary = JSON.parse(lines[0]);
  assert.equal(summary.schema, "jrv2_adapter_summary@1");
  // no request/response bodies on stdout
  assert.equal(summary.state, undefined);
  assert.equal(summary.answers, undefined);
  assert.equal(summary.request, undefined);
});

test("redaction law: a sentinel credential VALUE never appears in mock-run artifacts", async () => {
  // LAW: tests never trigger the adapter's live path (it would attempt a
  // real network call). Redaction is proven on the mock path: the sentinel
  // value must not appear in stdout, stderr or the response file even when
  // the environment carries a credential.
  const dir = tmpDir();
  const sentinel = "sk-SENTINEL-never-a-real-key";
  const requests = writeRequests(dir, [makeRequestLine({ stateId: hex16(22), requestedModel: "mock-model" })]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter(
    [
      "--requests", requests, "--out", out,
      "--cache", join(dir, "cache"), "--model", "mock-model", "--mock",
    ],
    { TYPESAFE_API_KEY: sentinel },
  );
  assert.equal(r.status, 0);
  for (const [name, text] of [["stdout", r.stdout], ["stderr", r.stderr], ["out.jsonl", readFileSync(out, "utf8")]] as const) {
    assert.equal(text.includes(sentinel), false, `credential value leaked to ${name}`);
  }
});

test("retry discipline: adapter sources pin maxRetries 0 everywhere", () => {
  const files = ["adapter.ts", "contract.ts", "prompt.ts", "mock.ts", "freeze_digests.ts"];
  for (const f of files) {
    const text = readFileSync(join(SRC, f), "utf8");
    const pins = text.match(/maxRetries:\s*(\d+)/g) ?? [];
    for (const pin of pins) {
      assert.match(pin, /maxRetries:\s*0/, `${f}: ${pin} violates the no-retry law`);
    }
  }
});

test("timeout discipline: 10000 ms pinned", () => {
  const text = readFileSync(join(SRC, "adapter.ts"), "utf8");
  assert.match(text, /CALL_TIMEOUT_MS = 10000/);
});
