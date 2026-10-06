#!/usr/bin/env node
// live_fetch.mjs — fetch a live cmegroup.com URL over the SNI-swapped TLS route
// (real Akamai edge, real TLS, browser headers, HTTP/1.1; SNI rewrite disclosed
// in BROWSER_CALENDAR_EVIDENCE.md). Saves body + meta with UTC + sha256.
// Usage: node live_fetch.mjs <url> <out_prefix> [accept]
import tls from "node:tls";
import { createHash } from "node:crypto";
import { writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
function await_import_child_process() {
  return require("node:child_process");
}
function import_meta_url_to_path() {
  return fileURLToPath(import.meta.url);
}

const [urlStr, outPrefixRaw, acceptOverride] = process.argv.slice(2);
if (!urlStr || !outPrefixRaw) {
  console.error("usage: live_fetch.mjs <url> <out_prefix> [accept]");
  process.exit(2);
}
const outPrefix = resolve(outPrefixRaw);
const u = new URL(urlStr);
const EDGE = process.env.CME_EDGE_IP || "23.66.152.172";
// real 16-byte Akamai hostname used as swapped SNI (same length as
// www.cmegroup.com); HTTP Host header stays www.cmegroup.com
const SWAP_SNI = "www.akamai.com";

const nowUtc = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");

const sock = tls.connect(
  { host: EDGE, port: 443, servername: SWAP_SNI, rejectUnauthorized: false, ALPNProtocols: ["http/1.1"] },
  () => {
    const startUtc = nowUtc();
    const headers = {
      Host: u.host,
      "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
      Accept: acceptOverride || "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
      "Accept-Encoding": "identity",
      "Sec-Fetch-Mode": "navigate",
      "Sec-Fetch-Dest": "document",
      "Sec-Fetch-Site": "none",
      "Upgrade-Insecure-Requests": "1",
    };
    const lines = [`GET ${u.pathname}${u.search} HTTP/1.1`];
    for (const [k, v] of Object.entries(headers)) lines.push(`${k}: ${v}`);
    lines.push("Connection: close", "");
    sock.write(lines.join("\r\n") + "\r\n");
    const chunks = [];
    sock.on("data", (d) => chunks.push(d));
    sock.on("end", () => finish(Buffer.concat(chunks), startUtc));
    sock.on("error", (e) => finish(Buffer.from("ERR:" + e.message), startUtc));
    setTimeout(() => { sock.destroy(); finish(Buffer.concat(chunks), startUtc); }, 25000);
  },
);
sock.on("error", (e) => {
  console.error("TLSERR:" + e.message);
  process.exit(2);
});

let done = false;
function finish(raw, startUtc) {
  if (done) return;
  done = true;
  const headEnd = raw.indexOf("\r\n\r\n");
  const head = raw.subarray(0, headEnd).toString("latin1");
  const body = raw.subarray(headEnd + 4);
  const status = head.split("\r\n")[0];
  // follow one level of redirect
  if (/HTTP\/1\.[01] 30[12378]/.test(status)) {
    const loc = (head.match(/[Ll]ocation: (\S+)/) || [])[1];
    if (loc && !process.argv.includes("--nofollow")) {
      const next = loc.startsWith("http") ? loc : "https://www.cmegroup.com" + loc;
      console.log(JSON.stringify({ redirectFrom: urlStr, to: loc }));
      const { spawn } = await_import_child_process();
      const child = spawn(process.execPath, [import_meta_url_to_path(), next, outPrefixRaw, "--nofollow"].concat(process.argv.slice(4)), { stdio: "inherit" });
      child.on("exit", (c) => process.exit(c || 0));
      return;
    }
  }
  const bodyStr = body.toString("utf8");
  const sha = createHash("sha256").update(bodyStr, "utf8").digest("hex");
  writeFileSync(outPrefix + ".body", bodyStr);
  const meta = {
    tool: "node-tls-sni-swap-http1 (live fetch, disclosed method)",
    url: urlStr,
    edgeIp: EDGE,
    tlsSni: SWAP_SNI + " (swapped; length-equal; Host header = real host)",
    startUtc,
    captureUtc: nowUtc(),
    status,
    bodyBytes: body.length,
    bodySha256: sha,
    server: (head.match(/Server: (.*)/) || [])[1] || "",
  };
  writeFileSync(outPrefix + ".meta.json", JSON.stringify(meta, null, 2));
  console.log(JSON.stringify(meta));
}
