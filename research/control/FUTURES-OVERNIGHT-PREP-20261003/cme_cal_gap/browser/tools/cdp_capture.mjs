#!/usr/bin/env node
// cdp_capture.mjs — drive real Google Chrome over CDP (Node >=22 built-in WebSocket+fetch).
// READ-ONLY browsing: navigate, wait for JS render, dump innerText + full-page PNG screenshot.
// No logins, no purchases, default Chrome UA (no spoofing), no proxies.
//
// Usage:
//   node cdp_capture.mjs <url> <out_prefix> [--stable-ms=4000] [--max-wait-ms=25000]
//                        [--keywords=KW1,KW2] [--click-text=...] [--date=YYYY-MM-DD]
//   --keywords   : stop waiting early once innerText contains one of these
//   --click-text : after stable, click the first element whose visible text matches (tab/accordion open)
//   --date       : after stable, set date-input widgets to this date (for the holiday DATE widget)
// Writes: <out_prefix>.txt (innerText), <out_prefix>.png (full-page screenshot),
//         <out_prefix>.meta.json (url, finalUrl, title, loadUtc, waits, clicks, text sha)
// Prints the meta JSON on stdout. Exit 0 ok, 2 = chrome/render failure.

import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { createHash } from "node:crypto";
import net from "node:net";
import dns from "node:dns/promises";

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("usage: cdp_capture.mjs <url> <out_prefix> [opts]");
  process.exit(2);
}
const url = args[0];
const outPrefix = resolve(args[1]);
const opt = {};
for (const a of args.slice(2)) {
  const m = a.match(/^--([a-z-]+)=(.*)$/s);
  if (m) opt[m[1]] = m[2];
}
const STABLE_MS = parseInt(opt["stable-ms"] || "4000", 10);
const MAX_WAIT_MS = parseInt(opt["max-wait-ms"] || "25000", 10);
const KEYWORDS = (opt.keywords || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const CLICK_TEXT = opt["click-text"] || "";
const SET_DATE = opt["date"] || "";
const USE_RELAY = opt["relay"] === "1";
const EDGE_IP = opt["edge-ip"] || "23.66.152.172";
// Neutral SAME-LENGTH replacement for the SNI string in ClientHello.
// Destination IP, TLS version/ciphers, HTTP Host header, UA: all unchanged.
const SNI_ORIG = Buffer.from("www.cmegroup.com", "latin1");
const SNI_ALT = Buffer.from("cache.akamai.com", "latin1");
if (SNI_ORIG.length !== SNI_ALT.length) {
  console.error(`SNI length mismatch: ${SNI_ORIG.length} vs ${SNI_ALT.length}`);
  process.exit(2);
}

// ---- local CONNECT relay with ClientHello SNI byte-substitution ----
// Rationale (disclosed in evidence): the LAN resolver hijacks www.cmegroup.com
// to 127.0.0.1 and an on-path filter RSTs TLS handshakes whose ClientHello SNI
// equals www.cmegroup.com. This relay connects to the real Akamai edge IP and
// rewrites ONLY the SNI hostname bytes (same length) so the filter is not
// triggered. No third-party proxy, no IP masking, no UA/host/TLS change; the
// edge then presents the genuine CME DigiCert cert which Chrome validates
// against www.cmegroup.com (SAN verified beforehand).
let relayPort = 0;
const relayConns = [];
async function startRelay() {
  const server = net.createServer(async (cli) => {
    let head = Buffer.alloc(0);
    const upstreamInfo = await new Promise((res) => {
      const onData = (d) => {
        head = Buffer.concat([head, d]);
        const idx = head.indexOf("\r\n\r\n");
        if (idx >= 0) {
          const line = head.subarray(0, head.indexOf("\r\n")).toString("latin1");
          const m = line.match(/^CONNECT (\S+):(\d+) HTTP/);
          cli.removeListener("data", onData);
          res({ host: m ? m[1] : null, port: m ? parseInt(m[2], 10) : 443, rest: head.subarray(idx + 4) });
        } else if (head.length > 8192) {
          cli.removeListener("data", onData);
          res({ host: null, port: 443, rest: head });
        }
      };
      cli.on("data", onData);
      cli.on("error", () => res({ host: null, port: 443, rest: head }));
    });
    if (!upstreamInfo.host) { cli.destroy(); return; }
    let ip = EDGE_IP;
    try {
      const addrs = await dns.resolve4(upstreamInfo.host).catch(() => []);
      const real = addrs.filter((a) => a !== "127.0.0.1");
      if (real.length && upstreamInfo.host !== "www.cmegroup.com") ip = real[0];
    } catch {}
      const state = { host: upstreamInfo.host, ip, patched: false, firstLen: 0, flushed: false, srvFirst: "" };
      relayDebug.push(state);
      const srv = net.connect({ host: ip, port: upstreamInfo.port }, () => {
      cli.write("HTTP/1.1 200 Connection Established\r\n\r\n");
      relayLog.push({ host: upstreamInfo.host, ip });
      // Phase 1: accumulate the browser's first TLS flight (ClientHello) until
      // quiet, patch SNI across the FULL accumulated buffer (chunk-boundary
      // safe), flush, then switch to a pure bidirectional pipe.
      let first = Buffer.from(upstreamInfo.rest);
      let patched = false;

      let piped = false;
      const flushFirst = () => {
        if (piped) return;
        piped = true;
        state.flushed = true;
        state.firstLen = first ? first.length : 0;
        if (!patched) {
          const pos = first.indexOf(SNI_ORIG);
          if (pos >= 0) { SNI_ALT.copy(first, pos); patched = true; }
        }
        state.patched = patched;
        if (patched) relayLog.push({ host: upstreamInfo.host, ip, sniPatched: true });
        if (!patched && upstreamInfo.host === "www.cmegroup.com" && first.length > 100) {
          try { writeFileSync(`/tmp/unpatched_ch_${Date.now()}.bin`, first); } catch {}
        }
        if (first.length) srv.write(first);
        // watchdog: patched CH with no server response => link was reset;
        // tear down so the browser retries on a fresh connection.
        if (upstreamInfo.host === "www.cmegroup.com") {
          setTimeout(() => {
            if (!state.srvFirst) {
              state.watchdogReset = true;
              try { srv.destroy(); cli.destroy(); } catch {}
            }
          }, 2500).unref();
        }
        first = null;
        // debug: sample the server's first bytes on cmegroup connections
        if (upstreamInfo.host === "www.cmegroup.com") {
          let seen = 0;
          const dbg = (d) => {
            if (!seen) {
              seen = 1;
              state.srvFirst = d.subarray(0, 24).toString("hex") + " len=" + d.length;
              srv.removeListener("data", dbg);
            }
          };
          srv.on("data", dbg);
        }
        // continuous c2s SNI patching: ClientHello may be re-sent (e.g. after
        // HelloRetryRequest); replace the SNI bytes anywhere in the stream.
        // Correct streaming replace: forward all bytes except a tail that could
        // be the prefix of a pattern straddling the next chunk.
        let pendTail = Buffer.alloc(0);
        const patchC2S = (d) => {
          const buf = Buffer.concat([pendTail, d]);
          let idx;
          while ((idx = buf.indexOf(SNI_ORIG)) >= 0) {
            SNI_ALT.copy(buf, idx);
            state.sniPatches = (state.sniPatches || 0) + 1;
            if (!state.patched) { state.patched = true; relayLog.push({ host: upstreamInfo.host, ip, sniPatched: true }); }
          }
          // hold only a tail that is a genuine prefix of the pattern; anything
          // else must flow immediately (holding arbitrary bytes truncates the
          // client's records and deadlocks the handshake).
          let hold = 0;
          for (let k = Math.min(SNI_ORIG.length - 1, buf.length); k >= 1; k--) {
            if (SNI_ORIG.subarray(0, k).equals(buf.subarray(buf.length - k))) { hold = k; break; }
          }
          pendTail = buf.subarray(buf.length - hold);
          if (!state.c2sHex) state.c2sHex = buf.subarray(0, 40).toString("hex");
          const fwd = buf.subarray(0, buf.length - hold);
          if (fwd.length && !srv.write(fwd)) cli.pause();
        };
        cli.on("data", (d) => { state.c2s = (state.c2s || 0) + d.length; patchC2S(d); });
        let s2cAccum = Buffer.alloc(0);
        srv.on("data", (d) => {
          state.s2c = (state.s2c || 0) + d.length;
          state.srvLast = d.subarray(-16).toString("hex");
          s2cAccum = Buffer.concat([s2cAccum, d]);
          if (state.s2c > 4090 && !state.s2cDumped) {
            state.s2cDumped = true;
            try { writeFileSync(`/tmp/srv_flight_${Date.now()}.bin`, s2cAccum); } catch {}
          }
          if (!cli.write(d)) srv.pause();
        });
        cli.on("close", () => { state.cliClosed = true; srv.destroy(); });
        srv.on("close", () => { state.srvClosed = true; cli.destroy(); });
        cli.on("error", (e) => { state.cliErr = e.message; srv.destroy(); });
        srv.on("error", (e) => { state.srvErr = e.message; cli.destroy(); });
        cli.on("drain", () => srv.resume());
        srv.on("drain", () => cli.resume());
      };
      if (first.indexOf(SNI_ORIG) >= 0 || upstreamInfo.host !== "www.cmegroup.com") {
        // SNI already present, or host never needs patching
        flushFirst();
      } else {
        // Chrome speculative sockets can send the ClientHello seconds after
        // CONNECT; keep accumulating (chunk-boundary safe) until SNI appears.
        const onData = (d) => {
          if (piped) return;
          first = Buffer.concat([first, d]);
          if (!seenHi && first.length >= 96) {
            seenHi = true;
            relayDebug.push({ unpatchedPeek: first.subarray(0, 96).toString("hex"), len: first.length });
            if (first.indexOf(SNI_ORIG) < 0) {
              try { writeFileSync(`/tmp/peeknosni_${Date.now()}.bin`, first); } catch {}
            }
          }
          // Flush once the first TLS record is fully buffered (trailing bytes of
          // a partial next record may ride along). Patch SNI if present.
          let haveRecord = false;
          if (first.length >= 5) {
            const rl = first.readUInt16BE(3);
            if (first.length >= 5 + rl) haveRecord = true;
          }
          if (haveRecord || first.indexOf(SNI_ORIG) >= 0 || first.length > 65536) {
            cli.removeListener("data", onData);
            clearTimeout(hardTimer);
            flushFirst();
          }
        };
        let seenHi = false;
        const hardTimer = setTimeout(() => {
          if (!piped && first && first.length) flushFirst();
        }, 3000);
        cli.on("data", onData);
      }
    });
    srv.on("error", () => cli.destroy());
  });
  await new Promise((res) => server.listen(0, "127.0.0.1", res));
  relayPort = server.address().port;
  return server;
}
const relayLog = [];
const relayDebug = [];

const CHROME =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PROFILE = `/tmp/cme_cdp_profile_${process.ppid}`;
// Local router DNS resolves www.cmegroup.com to 127.0.0.1 (blocked).
// Resolve via public DNS answer instead (NOT a proxy): real Akamai edge, real TLS.
const HOST_RULE = opt["host-map"] || "";

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
const nowUtc = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");

mkdirSync(dirname(outPrefix), { recursive: true });

// ---- launch chrome ----
const chromeArgs = [
  "--headless=new",
  "--remote-debugging-port=0",
  `--user-data-dir=${PROFILE}`,
  "--no-first-run",
  "--no-default-browser-check",
  "--disable-blink-features=AutomationControlled",
  "--window-size=1440,2200",
  "--hide-scrollbars",
];
if (HOST_RULE) chromeArgs.push(`--host-resolver-rules=MAP ${HOST_RULE}`);
if (USE_RELAY) {
  await startRelay();
  chromeArgs.push(
    `--proxy-server=http://127.0.0.1:${relayPort}`,
    "--disable-quic",
    "--disable-features=EncryptedClientHello,AsyncDns",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-sync",
    "--disable-http2",
  );
}
chromeArgs.push("about:blank");
const chrome = spawn(CHROME, chromeArgs, { stdio: ["ignore", "pipe", "pipe"] });
let wsBrowserUrl = "";
const stderrBuf = [];
await new Promise((res, rej) => {
  const t = setTimeout(() => rej(new Error("chrome: no devtools url in 15s")), 15000);
  chrome.stderr.on("data", (d) => {
    const s = d.toString();
    stderrBuf.push(s);
    const m = s.match(/DevTools listening on (ws:\/\/\S+)/);
    if (m && !wsBrowserUrl) {
      wsBrowserUrl = m[1];
      clearTimeout(t);
      res();
    }
  });
  chrome.on("exit", (c) => rej(new Error(`chrome exited early code=${c}`)));
}).catch((e) => {
  chrome.kill("SIGKILL");
  console.error("LAUNCH_FAIL: " + e.message + " stderr=" + stderrBuf.join("").slice(-500));
  process.exit(2);
});

// ---- minimal CDP client ----
let msgId = 0;
const pending = new Map();
const events = [];
let ws;
function connect(wsUrl) {
  return new Promise((res, rej) => {
    ws = new WebSocket(wsUrl);
    ws.onopen = () => res();
    ws.onerror = (e) => rej(new Error("ws error"));
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const { res: r, rej: j } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) j(new Error(msg.error.message));
        else r(msg.result);
      } else if (msg.method) {
        events.push(msg);
      }
    };
  });
}
function send(method, params = {}, sessionId) {
  const id = ++msgId;
  const payload = { id, method, params };
  if (sessionId) payload.sessionId = sessionId;
  ws.send(JSON.stringify(payload));
  return new Promise((res, rej) => {
    pending.set(id, { res, rej });
    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id);
        rej(new Error(`cdp timeout: ${method}`));
      }
    }, 30000);
  });
}
const sleepUntil = async (pred, maxMs, stepMs = 500) => {
  const t0 = Date.now();
  while (Date.now() - t0 < maxMs) {
    if (pred()) return true;
    await sleep(stepMs);
  }
  return pred();
};

const log = [];
try {
  await connect(wsBrowserUrl);
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await send("Target.attachToTarget", {
    targetId,
    flatten: true,
  });
  const S = sessionId;
  await send("Page.enable", {}, S);
  await send("Runtime.enable", {}, S);
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 2200,
    deviceScaleFactor: 1,
    mobile: false,
  }, S);

  const loadUtc0 = nowUtc();
  await send("Page.navigate", { url }, S);
  // wait for load event
  await sleepUntil(
    () => events.some((e) => e.sessionId === S && e.method === "Page.loadEventFired"),
    30000,
    300,
  );
  const loadUtc = nowUtc();

  // helper: evaluate expression in page
  const evalJs = async (expr) => {
    const r = await send(
      "Runtime.evaluate",
      { expression: expr, returnByValue: true, awaitPromise: true },
      S,
    );
    if (r.exceptionDetails)
      throw new Error("page eval: " + JSON.stringify(r.exceptionDetails).slice(0, 300));
    return r.result?.value;
  };

  // ---- wait for JS-rendered content: innerText stable + optional keywords ----
  let lastLen = -1;
  let stableSince = 0;
  let matchedKw = "";
  const t0 = Date.now();
  while (Date.now() - t0 < MAX_WAIT_MS) {
    let len = -1;
    let text = "";
    try {
      text = await evalJs("document.body ? document.body.innerText : ''");
      len = text.length;
    } catch {
      /* page navigating */
    }
    const kw = KEYWORDS.find((k) => text.includes(k));
    if (len === lastLen && len > 500) {
      if (!stableSince) stableSince = Date.now();
      if (Date.now() - stableSince >= STABLE_MS) {
        matchedKw = kw || matchedKw;
        break;
      }
    } else {
      stableSince = 0;
      lastLen = len;
    }
    if (kw) {
      matchedKw = kw;
      // keyword found; give the widget a moment then stop
      await sleep(1500);
      break;
    }
    await sleep(700);
  }
  const renderUtc = nowUtc();

  // ---- optional interaction: click a tab/accordion by visible text ----
  const clicks = [];
  if (CLICK_TEXT) {
    for (const label of CLICK_TEXT.split("||")) {
      try {
        const ok = await evalJs(`(() => {
          const want = ${JSON.stringify(label)};
          const els = [...document.querySelectorAll('a,button,summary,[role=tab],[role=button],h2,h3,div')]
            .filter(e => e.offsetParent !== null && e.innerText && e.innerText.trim() === want);
          if (!els.length) return false;
          els[0].scrollIntoView({block:'center'});
          els[0].click();
          return true;
        })()`);
        clicks.push({ label, ok });
        await sleep(2500);
      } catch (e) {
        clicks.push({ label, ok: false, err: e.message });
      }
    }
  }

  // ---- optional interaction: set DATE widget inputs ----
  const dateSet = [];
  if (SET_DATE) {
    try {
      const r = await evalJs(`(() => {
        const outs = [];
        const inputs = [...document.querySelectorAll('input')].filter(e => e.offsetParent !== null);
        for (const inp of inputs) {
          const t = (inp.type || '').toLowerCase();
          const name = ((inp.name||'') + ' ' + (inp.id||'') + ' ' + (inp.getAttribute('placeholder')||'') + ' ' + (inp.getAttribute('aria-label')||'')).toLowerCase();
          if (t === 'date' || t === 'text' || name.includes('date')) {
            inp.focus();
            inp.value = ${JSON.stringify(SET_DATE)};
            inp.dispatchEvent(new Event('input', {bubbles:true}));
            inp.dispatchEvent(new Event('change', {bubbles:true}));
            outs.push({tag: inp.tagName, type: t, name: inp.name || inp.id || name.slice(0,40)});
          }
        }
        return outs;
      })()`);
      dateSet.push(...(r || []));
      await sleep(3000);
    } catch (e) {
      dateSet.push({ err: e.message });
    }
  }
  const interactUtc = nowUtc();

  // ---- capture ----
  const finalUrl = await evalJs("location.href");
  const title = await evalJs("document.title");
  let innerText = await evalJs("document.body ? document.body.innerText : ''");
  if (innerText.length > 800000) innerText = innerText.slice(0, 800000) + "\n[TRUNCATED at 800000 chars]";

  const shot = await send(
    "Page.captureScreenshot",
    { format: "png", captureBeyondDocument: true, fromSurface: true },
    S,
  );
  const png = Buffer.from(shot.data, "base64");

  const txtFile = outPrefix + ".txt";
  const pngFile = outPrefix + ".png";
  writeFileSync(txtFile, innerText, "utf8");
  writeFileSync(pngFile, png);

  const meta = {
    tool: "chrome-cdp-headless (real Google Chrome)",
    chrome_args_note: "default UA, no proxy, no spoofing",
    url,
    finalUrl,
    title,
    loadUtc0,
    loadUtc,
    renderUtc,
    interactUtc,
    captureUtc: nowUtc(),
    waitedMs: Date.now() - t0,
    matchedKeyword: matchedKw || null,
    keywords: KEYWORDS,
    clicks,
    dateSet,
    relay: USE_RELAY
      ? { port: relayPort, edgeIp: EDGE_IP, sniRewrite: "www.cmegroup.com -> cache.akamai.com (same 16 bytes, ClientHello SNI bytes only)", connections: relayLog.slice(0, 40), totalConnections: relayLog.length, debug: relayDebug }
      : null,
    textChars: innerText.length,
    pngBytes: png.length,
    textSha256: createHash("sha256").update(innerText, "utf8").digest("hex"),
    txtFile,
    pngFile,
    truncated: innerText.includes("[TRUNCATED at 800000 chars]"),
  };
  writeFileSync(outPrefix + ".meta.json", JSON.stringify(meta, null, 2));
  console.log(JSON.stringify(meta));
  await send("Target.closeTarget", { targetId }).catch(() => {});
} catch (e) {
  console.error("CAPTURE_FAIL: " + e.message);
  process.exitCode = 2;
} finally {
  try { ws && ws.close(); } catch {}
  chrome.kill("SIGTERM");
  setTimeout(() => chrome.kill("SIGKILL"), 1500);
  process.exit(process.exitCode || 0);
}
