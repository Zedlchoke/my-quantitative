// Call-discipline law, verified by source scan + imported constants:
//   - maxRetries appears ONLY as 0 in the live path (adapter + probe)
//   - per-call timeout is 10000 ms
//   - the prompt module is built from the frozen contract

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { CALL_TIMEOUT_MS } from "../src/adapter.ts";
import {
  EMBEDDED_FREEZE_SHA256,
  EMBEDDED_REGIME_LABEL_CONTRACT,
  verifyFreezeDigests,
} from "../src/freeze_digests.ts";
import { REGIME_INSTRUCTIONS, buildRegimeQuestions } from "../src/prompt.ts";
import { LABELS } from "../src/contract.ts";

const SRC_DIR = resolve(import.meta.dirname, "../src");

test("timeout constant is exactly 10000 ms", () => {
  assert.equal(CALL_TIMEOUT_MS, 10000);
});

test("source scan: maxRetries appears only as 0 (no retry law)", () => {
  let occurrences = 0;
  for (const f of ["adapter.ts", "models_probe.ts"]) {
    const code = readFileSync(join(SRC_DIR, f), "utf8");
    const all = code.match(/maxRetries\s*:/g) ?? [];
    const zero = code.match(/maxRetries\s*:\s*0(?!\d)/g) ?? [];
    assert.equal(
      all.length,
      zero.length,
      `${f}: every maxRetries occurrence must be exactly 0`,
    );
    occurrences += all.length;
  }
  assert.ok(occurrences >= 2, "expected client-config and per-call retry overrides");
});

test("source scan: per-call systemOne carries the frozen timeout and retry override", () => {
  const code = readFileSync(join(SRC_DIR, "adapter.ts"), "utf8");
  assert.match(code, /systemOne\(/);
  assert.match(code, /retry:\s*\{\s*maxRetries:\s*0\s*\},\s*timeout:\s*CALL_TIMEOUT_MS/);
  assert.match(code, /new TypeSafeClient\(\{[\s\S]*?timeout:\s*CALL_TIMEOUT_MS[\s\S]*?retry:\s*\{\s*maxRetries:\s*0\s*\}/);
});

test("source scan: no retry/re-ask loop around the provider call", () => {
  const code = readFileSync(join(SRC_DIR, "adapter.ts"), "utf8");
  // a second systemOne call site would indicate a re-ask path
  assert.equal((code.match(/systemOne\(/g) ?? []).length, 1, "exactly one systemOne call site");
});

test("freeze gate: on-disk regime_label_contract.json matches the embedded digest", () => {
  const freezesDir = resolve(import.meta.dirname, "../../freezes");
  const result = verifyFreezeDigests(freezesDir);
  assert.deepEqual(result.mismatches, [], "freeze drift detected — adapter would refuse to run");
  assert.ok(Object.keys(EMBEDDED_FREEZE_SHA256).includes("regime_label_contract.json"));
});

test("prompt is verbatim from the embedded contract copy", () => {
  const defs = EMBEDDED_REGIME_LABEL_CONTRACT.definitions_outcome_blind;
  const q = buildRegimeQuestions();
  assert.equal(Object.keys(q.regime.criteria).length, 5);
  for (const label of LABELS) {
    assert.equal(q.regime.criteria[label], defs[label], `${label} description must be verbatim`);
  }
  assert.equal(REGIME_INSTRUCTIONS.free_text_regime, "REJECTED -> SCHEMA_ERROR -> TRANSITION_UNKNOWN");
});
