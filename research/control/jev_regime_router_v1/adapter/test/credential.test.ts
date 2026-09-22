// Credential law: without TYPESAFE_API_KEY the live path is BLOCKED_CREDENTIAL
// (exit 4) with a JSON summary line and NO fabricated responses.

import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { hex16, makeRequestLine, runAdapter, tmpDir, writeRequests } from "./helpers.ts";

const MODEL = "jev-canary-x";

test("live path without key: exit 4, BLOCKED_CREDENTIAL, no fabricated rows", () => {
  const dir = tmpDir();
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(21) })]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", join(dir, "c"), "--model", MODEL]);
  assert.equal(r.status, 4, `stderr=${r.stderr}`);
  assert.ok(r.stderr.includes("BLOCKED_CREDENTIAL"));
  // summary line must parse as JSON (the dispatch requires a JSON summary line)
  const jsonLine = r.stderr.trim().split("\n").find((l) => l.startsWith("{"));
  assert.ok(jsonLine, "BLOCKED_CREDENTIAL must carry a JSON summary line");
  const parsed = JSON.parse(jsonLine) as Record<string, unknown>;
  assert.equal(parsed.status, "BLOCKED_CREDENTIAL");
  assert.equal(existsSync(out), false, "no fabricated responses on credential block");
});

test("live path with EMPTY-string key is also blocked", () => {
  const dir = tmpDir();
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(22) })]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter(
    ["--requests", req, "--out", out, "--cache", join(dir, "c"), "--model", MODEL],
    { TYPESAFE_API_KEY: "" },
  );
  assert.equal(r.status, 4);
  assert.ok(r.stderr.includes("BLOCKED_CREDENTIAL"));
});

test("credential gate fires AFTER cache/mock rows would have been earned, but emits none", () => {
  const dir = tmpDir();
  // first line invalid (no provider needed), second would need the provider
  const req = writeRequests(dir, [
    "{not json",
    makeRequestLine({ stateId: hex16(23) }),
  ]);
  const out = join(dir, "out.jsonl");
  const r = runAdapter(["--requests", req, "--out", out, "--cache", join(dir, "c"), "--model", MODEL]);
  assert.equal(r.status, 4);
  assert.equal(existsSync(out), false);
});
