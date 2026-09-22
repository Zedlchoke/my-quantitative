// Redaction law (static + dynamic): the adapter never echoes credential
// material. Static scan of src/, dynamic sentinel scan of child output.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { hex16, makeRequestLine, runAdapter, tmpDir, writeRequests } from "./helpers.ts";

const SRC_DIR = resolve(import.meta.dirname, "../src");

function srcFiles(): string[] {
  return readdirSync(SRC_DIR).filter((f) => f.endsWith(".ts")).map((f) => join(SRC_DIR, f));
}

/** Extract the contents of all string literals ('...', "...", `...`). */
function stringLiterals(code: string): string[] {
  const out: string[] = [];
  const re = /(['"`])((?:\\.|(?!\1)[^\\\n])*)\1/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(code)) !== null) out.push(m[2]);
  return out;
}

test("static: no string literal in src mentions the env var name", () => {
  for (const f of srcFiles()) {
    const code = readFileSync(f, "utf8");
    for (const lit of stringLiterals(code)) {
      assert.ok(
        !/typesafe[_-]api[_-]key/i.test(lit),
        `${f}: string literal mentioning the credential env var found: ${JSON.stringify(lit)}`,
      );
    }
  }
});

test("static: adapter never passes apiKey and embeds no key-like material", () => {
  for (const f of srcFiles()) {
    const code = readFileSync(f, "utf8");
    assert.ok(!/apiKey\s*:/.test(code), `${f}: adapter must not pass apiKey explicitly`);
    assert.ok(!/sk-[A-Za-z0-9_-]{8,}/.test(code), `${f}: key-like literal found`);
  }
});

test("static: env access is name-only presence checking", () => {
  // The only permitted env access pattern: process.env.TYPESAFE_API_KEY used in
  // an undefined/empty comparison. It must never be interpolated into output.
  for (const f of srcFiles()) {
    const code = readFileSync(f, "utf8");
    for (const line of code.split("\n")) {
      if (line.includes("process.env.TYPESAFE_API_KEY")) {
        assert.match(
          line,
          /(===|!==)\s*(undefined|"")|(""|undefined)\s*(===|!==)/,
          `${f}: env access must be a presence check: ${line.trim()}`,
        );
      }
    }
  }
});

test("dynamic: no sentinel leakage in mock-run stdout/stderr/out/cache", () => {
  const SENTINEL = "sk-sentinel-DEADBEEFCAFEBABE0123456789";
  const dir = tmpDir();
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(31) })]);
  const out = join(dir, "out.jsonl");
  const cache = join(dir, "cache");
  const r = runAdapter(
    ["--requests", req, "--out", out, "--cache", cache, "--model", "jev-canary-x", "--mock"],
    { TYPESAFE_API_KEY: SENTINEL },
  );
  assert.equal(r.status, 0, r.stderr);
  const surfaces = [r.stdout, r.stderr, readFileSync(out, "utf8")];
  for (const f of readdirSync(cache)) surfaces.push(readFileSync(join(cache, f), "utf8"));
  for (const s of surfaces) {
    assert.ok(!s.includes(SENTINEL), "sentinel key material leaked");
    assert.ok(!/sk-[A-Za-z0-9_-]{16,}/.test(s), "key-like pattern in output");
    assert.ok(!s.toUpperCase().includes("TYPESAFE_API_KEY"), "env var name echoed to output");
  }
});

test("summary line is redaction-safe: no state bodies, no headers", () => {
  const dir = tmpDir();
  const req = writeRequests(dir, [makeRequestLine({ stateId: hex16(32) })]);
  const r = runAdapter(["--requests", req, "--out", join(dir, "o.jsonl"), "--cache", join(dir, "c"), "--model", "jev-canary-x", "--mock"]);
  const summary = JSON.parse(r.stdout.trim()) as Record<string, unknown>;
  const flat = JSON.stringify(summary);
  assert.ok(!flat.includes("feature_vector"));
  assert.ok(!flat.includes("prior_regime"));
  assert.ok(!flat.includes("authorization"));
  // summary carries only counters/strings we expect
  for (const k of Object.keys(summary)) {
    assert.match(
      k,
      /^(schema|mode|model|n_requests|n_emitted|n_ok|n_err|n_cached|n_duplicate_skipped|n_local_invalid|total_latency_ms|input_tokens_sum)$/,
      `unexpected summary key ${k}`,
    );
  }
});
