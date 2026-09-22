// models_probe — G0 pin-probe helper (NO model selection happens here).
//
//   node src/models_probe.ts [--out <path>]
//
// If TYPESAFE_API_KEY is present (name-only check): calls models.list() and
// records {models, probed_at} WITHOUT selecting anything — model selection is
// the Lead's freeze act (plan §5). If the key is absent: records
// {status: BLOCKED_CREDENTIAL}. The key value itself is never printed.

import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname } from "node:path";
import { APIError, APITimeoutError, TypeSafeClient } from "@typesafe-ai/sdk";
import { CALL_TIMEOUT_MS } from "./adapter.ts";

export const EXIT_OK = 0;
export const EXIT_USAGE = 2;

const PROBE_SCHEMA = "jrv1_models_probe@1";

function defaultOutPath(): string {
  // <adapter>/runtime/models_probe.json (runtime/ is gitignored)
  return fileURLToPath(new URL("../runtime/models_probe.json", import.meta.url));
}

export async function main(argv: readonly string[]): Promise<number> {
  let outPath = defaultOutPath();
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--out") outPath = argv[++i] ?? outPath;
    else {
      console.error(`usage: node src/models_probe.ts [--out <path>] (unknown arg ${argv[i]})`);
      return EXIT_USAGE;
    }
  }
  mkdirSync(dirname(outPath), { recursive: true });

  const write = (payload: unknown): void => {
    writeFileSync(outPath, JSON.stringify(payload, null, 1) + "\n");
  };

  // name-only presence check; value never copied or logged
  if (process.env.TYPESAFE_API_KEY === undefined || process.env.TYPESAFE_API_KEY === "") {
    write({ schema: PROBE_SCHEMA, status: "BLOCKED_CREDENTIAL" });
    console.log(JSON.stringify({ status: "BLOCKED_CREDENTIAL", out: outPath }));
    return EXIT_OK;
  }

  try {
    const client = new TypeSafeClient({
      timeout: CALL_TIMEOUT_MS,
      retry: { maxRetries: 0 },
      logLevel: "warn",
    });
    const { data, requestId } = await client.models.list().withResponse();
    const payload = {
      schema: PROBE_SCHEMA,
      status: "OK",
      models: data.map((m) => ({ name: m.name, description: m.description, release_date: m.release_date })),
      probed_at: new Date().toISOString(),
      request_id: requestId ?? null,
    };
    write(payload);
    console.log(JSON.stringify({ status: "OK", n_models: data.length, out: outPath }));
    return EXIT_OK;
  } catch (err) {
    const status = err instanceof APITimeoutError ? "TIMEOUT" : "PROVIDER_ERROR";
    const payload = {
      schema: PROBE_SCHEMA,
      status,
      error_class: err instanceof Error ? err.constructor.name : "Unknown",
      request_id: err instanceof APIError && typeof err.requestId === "string" ? err.requestId : null,
      probed_at: new Date().toISOString(),
    };
    write(payload);
    console.log(JSON.stringify(payload));
    return EXIT_OK;
  }
}

const isMain =
  process.argv[1] !== undefined && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  main(process.argv.slice(2)).then((code) => process.exit(code));
}
