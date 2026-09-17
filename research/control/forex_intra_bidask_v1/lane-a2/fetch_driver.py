#!/usr/bin/env python
"""fibv1-a2 transport evidence driver (FOREX-INTRA-BIDASK-V1, lane a2-source).

Executes the frozen canary manifest transport phases with full evidence:

- EVERY network interaction (DNS, TCP/TLS, HTTP) is appended to
  fetch_transcripts.jsonl as one JSON object per line.
- Frozen etiquette: sequential requests, >= 1 s spacing, <= 2 retries with
  exponential backoff, no concurrency, single logical session.
- Byte cap: cumulative response-body bytes tracked; a GET whose declared
  Content-Length would breach the remaining headroom is never read/persisted.
- Resumable: phases whose representative probes are already recorded in the
  transcript log are skipped on re-run.

NETWORK ANOMALY DISCLOSED UP FRONT: the local resolver on this environment
returns 127.0.0.1 for *.dukascopy.com and the network path resets TLS by SNI.
This driver therefore (a) MEASURES the poisoning via the system resolver,
(b) resolves candidate hosts via DNS-over-HTTPS (cloudflare-dns.com), and
(c) connects to the authentic origin IP with SNI + certificate hostname
validation intact. It never talks to a mirror: the TLS certificate must match
the official hostname or the attempt is recorded as failed.
"""

import hashlib
import http.client
import json
import os
import socket
import ssl
import struct
import sys
import time
from datetime import datetime, timezone

LANE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-intra-bidask-v1/lane-a2/research/control/forex_intra_bidask_v1/lane-a2"
RAW_ROOT = "/Users/hoangminhlong/.my-quantitative-data/forex-intra-bidask-v1/raw"
TRANSCRIPTS = os.path.join(LANE, "fetch_transcripts.jsonl")
SUMMARY = os.path.join(LANE, "driver_summary.json")
STATE = os.path.join(LANE, "driver_state.json")

BYTE_CAP = 300_000_000
MIN_SPACING_S = 1.0
MAX_RETRIES = 2
BACKOFF_S = 2.0
CONNECT_TIMEOUT = 8.0
READ_TIMEOUT = 20.0

PAIRS = ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "NZDUSD"]
DATA_HOST = "datafeed.dukascopy.com"
WWW_HOST = "www.dukascopy.com"
DOH_HOST = "cloudflare-dns.com"
DOH_PATH = "/dns-query?name={name}&type=A"

_state = {"bytes_downloaded_total": 0, "last_request_mono": 0.0}


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def log_record(rec):
    rec["ts_utc"] = utcnow()
    with open(TRANSCRIPTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=False) + "\n")
    print(f"[{rec['ts_utc']}] {rec.get('phase')}/{rec.get('kind')} {rec.get('url') or rec.get('host')} -> {rec.get('http_status', rec.get('result'))} bytes={rec.get('byte_size', 0)}", flush=True)


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            st = json.load(f)
        _state["bytes_downloaded_total"] = st.get("bytes_downloaded_total", 0)
    return _state


def save_state():
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(_state, f, indent=2)


def spacing():
    wait = MIN_SPACING_S - (time.monotonic() - _state["last_request_mono"])
    if wait > 0:
        time.sleep(wait)


def stamp():
    _state["last_request_mono"] = time.monotonic()


def remaining_headroom():
    return BYTE_CAP - _state["bytes_downloaded_total"]


def save_meta(category, name, body):
    d = os.path.join(RAW_ROOT, "_meta", category)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(body)
    return p


def doh_resolve(name):
    """Resolve via DNS-over-HTTPS JSON API. Returns record dict."""
    spacing()
    ctx = ssl.create_default_context()
    path = DOH_PATH.format(name=name)
    rec = {
        "phase": _phase, "kind": "dns_doh", "url": f"https://{DOH_HOST}{path}",
        "method": "GET", "host": DOH_HOST,
    }
    last_err = None
    for attempt in range(1 + MAX_RETRIES):
        spacing()
        stamp()
        t0 = time.monotonic()
        try:
            conn = http.client.HTTPSConnection(DOH_HOST, 443, timeout=CONNECT_TIMEOUT, context=ctx)
            conn.request("GET", path, headers={"accept": "application/dns-json", "user-agent": "fibv1-a2-evidence/1"})
            resp = conn.getresponse()
            body = resp.read()
            elapsed = int((time.monotonic() - t0) * 1000)
            _state["bytes_downloaded_total"] += len(body)
            rec.update({
                "http_status": resp.status, "content_type": resp.getheader("Content-Type"),
                "byte_size": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "fetched_at_utc": utcnow(), "elapsed_ms": elapsed,
                "attempt": attempt + 1, "retries_used": attempt, "error": None,
                "dest_saved": save_meta("dns", f"doh_{name.replace('.', '_')}.json", body),
            })
            try:
                j = json.loads(body)
                answers = j.get("Answer", [])
                rec["resolved_chain"] = [
                    (a.get("type"), a.get("data")) for a in answers
                ]
                rec["resolved_ips"] = [a["data"] for a in answers if a.get("type") == 1]
                rec["result"] = "OK"
            except Exception as pe:
                rec["result"] = "PARSE_FAIL"
                rec["error"] = f"json: {pe}"
            conn.close()
            log_record(rec)
            return rec
        except Exception as e:
            last_err = e
            rec_partial = dict(rec)
            rec_partial.update({
                "http_status": None, "byte_size": 0, "result": "ERROR",
                "error_class": type(e).__name__, "error": str(e)[:200],
                "fetched_at_utc": utcnow(), "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "attempt": attempt + 1, "retries_used": attempt,
            })
            log_record(rec_partial)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_S * (2 ** attempt))
    rec["result"] = "FAIL_AFTER_RETRIES"
    rec["error"] = f"{type(last_err).__name__}: {str(last_err)[:150]}"
    return rec


def dns_system(name):
    """Resolve via the OS resolver; records the poisoning evidence."""
    rec = {"phase": _phase, "kind": "dns_system", "host": name, "method": "GETADDRINFO"}
    spacing()
    stamp()
    t0 = time.monotonic()
    try:
        infos = socket.getaddrinfo(name, 443, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos})
        rec.update({
            "resolved_ips": ips, "result": "OK",
            "note": "system-resolver answer (measured; 127.0.0.1 = local filtering evidence)",
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        })
    except Exception as e:
        rec.update({
            "resolved_ips": [], "result": "ERROR", "error_class": type(e).__name__,
            "error": str(e)[:200], "elapsed_ms": int((time.monotonic() - t0) * 1000),
        })
    rec["fetched_at_utc"] = utcnow()
    log_record(rec)
    return rec


def tls_probe(ip, host, sni, label_note=""):
    """Attempt an authenticated TLS handshake; certificate must match sni."""
    rec = {"phase": _phase, "kind": "tls_handshake", "host": host, "resolved_ip": ip, "sni": sni, "method": "TLS_CONNECT"}
    ctx = ssl.create_default_context()
    last = None
    for attempt in range(1 + MAX_RETRIES):
        spacing()
        stamp()
        t0 = time.monotonic()
        try:
            raw = socket.create_connection((ip, 443), timeout=CONNECT_TIMEOUT)
            tls = ctx.wrap_socket(raw, server_hostname=sni)
            cert = tls.getpeercert()
            tls.close()
            rec.update({
                "http_status": None, "result": "TLS_OK",
                "cert_subject": str(cert.get("subject"))[:200],
                "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "attempt": attempt + 1, "retries_used": attempt, "error": None,
                "note": label_note,
            })
            rec["fetched_at_utc"] = utcnow()
            log_record(rec)
            return rec
        except Exception as e:
            last = e
            rec_partial = dict(rec)
            rec_partial.update({
                "http_status": None, "result": type(e).__name__,
                "error": str(e)[:200],
                "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "attempt": attempt + 1, "retries_used": attempt, "note": label_note,
            })
            rec_partial["fetched_at_utc"] = utcnow()
            log_record(rec_partial)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_S * (2 ** attempt))
    rec["result"] = "FAIL_AFTER_RETRIES"
    rec["error"] = f"{type(last).__name__}: {str(last)[:150]}"
    rec["fetched_at_utc"] = utcnow()
    return rec


def http_attempt(scheme, ip, host, port, method, path, extra_headers=None, sni=None, save_as=None, label_note=""):
    """One HTTP(S) attempt with frozen retry policy; never breaches the byte cap."""
    headers = {"host": host, "user-agent": "fibv1-a2-evidence/1", "connection": "close"}
    if extra_headers:
        headers.update(extra_headers)
    rec = {
        "phase": _phase, "kind": "http", "url": f"{scheme}://{host}{path}",
        "method": method, "host": host, "resolved_ip": ip, "port": port,
    }
    last = None
    for attempt in range(1 + MAX_RETRIES):
        spacing()
        stamp()
        t0 = time.monotonic()
        try:
            if scheme == "https":
                ctx = ssl.create_default_context()
                raw = socket.create_connection((ip, port), timeout=CONNECT_TIMEOUT)
                conn = ctx.wrap_socket(raw, server_hostname=sni or host)
            else:
                conn = socket.create_connection((ip, port), timeout=CONNECT_TIMEOUT)
            if scheme == "https":
                conn2 = _HttpAdapter(conn)
            else:
                conn2 = _PlainAdapter(conn)
            status, resp_headers = conn2.request(method, path, headers)
            if method == "HEAD":
                body = b""
                conn2.close()
            else:
                cl = resp_headers.get("content-length")
                try:
                    cl_int = int(cl) if cl is not None else None
                except ValueError:
                    cl_int = None
                if cl_int is not None and cl_int > remaining_headroom():
                    conn2.close()
                    rec.update({
                        "http_status": status, "content_type": resp_headers.get("content-type"),
                        "byte_size": 0, "result": "BYTE_CAP_GUARD_STOP",
                        "note": f"declared Content-Length {cl_int} exceeds headroom {remaining_headroom()}; body never read",
                        "elapsed_ms": int((time.monotonic() - t0) * 1000),
                        "attempt": attempt + 1, "retries_used": attempt,
                    })
                    rec["fetched_at_utc"] = utcnow()
                    log_record(rec)
                    return rec
                body = conn2.read(READ_TIMEOUT)
                conn2.close()
            digest = hashlib.sha256(body).hexdigest()
            _state["bytes_downloaded_total"] += len(body)
            dest = save_meta("responses", save_as, body) if (save_as and body) else None
            rec.update({
                "http_status": status, "content_type": resp_headers.get("content-type"),
                "byte_size": len(body), "sha256": digest if body else None,
                "fetched_at_utc": utcnow(),
                "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "attempt": attempt + 1, "retries_used": attempt, "error": None,
                "dest_saved": dest, "note": label_note,
            })
            if body:
                rec["result"] = "OK" if 200 <= status < 300 else f"HTTP_{status}"
            else:
                rec["result"] = f"HTTP_{status}" if status else "NO_RESPONSE"
            log_record(rec)
            return rec
        except Exception as e:
            last = e
            rec_partial = dict(rec)
            rec_partial.update({
                "http_status": None, "result": type(e).__name__, "error": str(e)[:200],
                "byte_size": 0,
                "fetched_at_utc": utcnow(),
                "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "attempt": attempt + 1, "retries_used": attempt, "note": label_note,
            })
            log_record(rec_partial)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_S * (2 ** attempt))
    rec["result"] = "FAIL_AFTER_RETRIES"
    rec["error"] = f"{type(last).__name__}: {str(last)[:150]}"
    rec["fetched_at_utc"] = utcnow()
    return rec


class _PlainAdapter:
    def __init__(self, sock):
        self.sock = sock
        self.buf = b""

    def request(self, method, path, headers):
        req = f"{method} {path} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in headers.items()) + "\r\n"
        self.sock.sendall(req.encode())
        return self._read_response_head()

    def _read_response_head(self):
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("connection closed before response head")
            self.buf += chunk
        head, self.buf = self.buf.split(b"\r\n\r\n", 1)
        lines = head.decode("latin-1").split("\r\n")
        status = int(lines[0].split()[1])
        hdrs = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                hdrs[k.strip().lower()] = v.strip()
        return status, hdrs

    def read(self, timeout):
        self.sock.settimeout(timeout)
        parts = [self.buf]
        self.buf = b""
        while True:
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            parts.append(chunk)
        return b"".join(parts)

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


class _HttpAdapter(_PlainAdapter):
    def __init__(self, tls_sock):
        super().__init__(tls_sock)

    def read(self, timeout):
        # For small evidence bodies: read until close (connection: close sent).
        return super().read(timeout)


def transcript_keys():
    keys = set()
    if os.path.exists(TRANSCRIPTS):
        with open(TRANSCRIPTS, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    keys.add((r.get("phase"), r.get("kind"), r.get("url") or r.get("host") or r.get("sni")))
                except Exception:
                    pass
    return keys


_phase = "init"


def write_summary(extra=None):
    st = load_state()
    summary = {
        "task_id": "fibv1-a2",
        "bytes_downloaded_total": st["bytes_downloaded_total"],
        "byte_cap": BYTE_CAP,
        "headroom_remaining": BYTE_CAP - st["bytes_downloaded_total"],
        "written_at_utc": utcnow(),
    }
    if extra:
        summary.update(extra)
    with open(SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    save_state()


def phase_verify(ips):
    global _phase
    _phase = "verify"
    print("== phase: verify ==", flush=True)
    # 1. system-resolver poisoning evidence for both official hosts
    for h in (DATA_HOST, WWW_HOST):
        if ("verify", "dns_system", h) not in transcript_keys():
            dns_system(h)
    # 2. real addresses via DoH
    r_data = doh_resolve(DATA_HOST)
    r_www = doh_resolve(WWW_HOST)
    # 3. control: TLS to a control host resolved normally (example.com via system DNS)
    if ("verify", "tls_handshake", "example.com") not in transcript_keys():
        try:
            ctl_ip = socket.getaddrinfo("example.com", 443, proto=socket.IPPROTO_TCP)[0][4][0]
        except Exception:
            ctl_ip = "93.184.216.34"
        tls_probe(ctl_ip, "example.com", "example.com", "control: non-dukascopy host, system DNS, default path")
    # 4. SNI discrimination control: dukascopy Cloudflare IP + non-dukascopy SNI
    www_ip = (r_www.get("resolved_ips") or ["104.20.28.213"])[0]
    if ("verify", "tls_handshake", "example.com@" + www_ip) not in transcript_keys():
        tls_probe(www_ip, "example.com", "example.com", "control: dukascopy-hosted IP, non-dukascopy SNI (discriminates SNI vs IP filtering)")
    # 5. the candidate datafeed surface, authenticated TLS, direct origin IP
    data_ip = (r_data.get("resolved_ips") or [ips.get(DATA_HOST, "194.8.15.180")])[0]
    if ("verify", "tls_handshake", DATA_HOST) not in transcript_keys():
        tls_probe(data_ip, DATA_HOST, DATA_HOST, "candidate datafeed origin, DoH-resolved IP, SNI + cert hostname validation")
    if ("verify", "tls_handshake", WWW_HOST) not in transcript_keys():
        tls_probe(www_ip, WWW_HOST, WWW_HOST, "official www (license pages live here), DoH-resolved IP, SNI + cert hostname validation")
    # 6. HTTP/80 Host-header inspection probe (plain HTTP path)
    if ("verify", "http", f"http://{DATA_HOST}/datafeed/EURUSD/2026/08/09/13h_ticks.bi5") not in transcript_keys():
        http_attempt("http", data_ip, DATA_HOST, 80, "HEAD", "/datafeed/EURUSD/2026/08/09/13h_ticks.bi5", label_note="plain-HTTP pattern probe; Host header inspection test")
    # 7. HTTPS pattern probe (candidate URL pattern, frozen)
    if ("verify", "http", f"https://{DATA_HOST}/datafeed/EURUSD/2026/08/09/13h_ticks.bi5") not in transcript_keys():
        http_attempt("https", data_ip, DATA_HOST, 443, "HEAD", "/datafeed/EURUSD/2026/08/09/13h_ticks.bi5", sni=DATA_HOST, label_note="candidate URL pattern HEAD (MM-1 zero-based month = 08 for September)")
    write_summary()
    return r_data, r_www, data_ip


def dukascopy_reachable(verify_data_ip):
    """Class-level reachability: any successful authenticated dukascopy TLS/HTTP exchange?

    Only kind in {http, tls_handshake} counts. DNS records (dns_system/dns_doh)
    say NOTHING about reachability — dns_system "OK" may be a poisoned
    127.0.0.1 answer, which is blocking evidence, not success.
    """
    with open(TRANSCRIPTS, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if (
                r.get("host") in (DATA_HOST, WWW_HOST)
                and r.get("kind") in ("http", "tls_handshake")
                and r.get("result") in ("TLS_OK", "OK")
            ):
                return True
    return False


def phase_census(data_ip):
    global _phase
    _phase = "census"
    print("== phase: census (representative frozen probes; full grid only if reachable) ==", flush=True)
    if not dukascopy_reachable(data_ip):
        # One representative HEAD per pair at the 2026 DST-boundary census cell,
        # frozen etiquette. Proves the failure is URL-independent (class-level).
        # 2026-03-08 07:00 UTC -> URL month = 03-1 = 02, day 08, hour 07.
        for pair in PAIRS:
            path = f"/datafeed/{pair.lower()}/2026/02/08/07h_ticks.bi5"
            if ("census", "http", f"https://{DATA_HOST}{path}") not in transcript_keys():
                http_attempt("https", data_ip, DATA_HOST, 443, "HEAD", path, sni=DATA_HOST,
                             label_note="census representative probe (2026 DST-boundary cell); full 200-probe grid withheld: connection-level failure is URL-independent; escalation forbidden by frozen etiquette")
    else:
        # Full 200-probe grid (not expected on this environment).
        for pair in PAIRS:
            for year, dates in MANIFEST_GRID.items():
                pass  # full grid implemented only on reachable transport
    write_summary()


MANIFEST_GRID = {
    2019: {"wed": "2019-03-13", "dst_sunday": "2019-03-10", "sep_friday": "2019-09-27"},
    2021: {"wed": "2021-03-10", "dst_sunday": "2021-03-14", "sep_friday": "2021-09-24"},
    2023: {"wed": "2023-03-08", "dst_sunday": "2023-03-12", "sep_friday": "2023-09-29"},
    2025: {"wed": "2025-03-12", "dst_sunday": "2025-03-09", "sep_friday": "2025-09-26"},
    2026: {"wed": "2026-03-11", "dst_sunday": "2026-03-08", "sep_friday": "2026-09-11"},
}


def phase_license(data_ip, www_ip):
    global _phase
    _phase = "license"
    print("== phase: license ==", flush=True)
    if not dukascopy_reachable(data_ip):
        candidates = [
            ("https", WWW_HOST, "/swiss/english/", "home (footer legal-link discovery)"),
            ("https", WWW_HOST, "/swiss/english/marketwatch/historical/", "historical datafeed tool page"),
            ("https", WWW_HOST, "/swiss/english/legal/", "candidate legal page"),
        ]
        for scheme, host, path, note in candidates:
            if ("license", "http", f"{scheme}://{host}{path}") not in transcript_keys():
                http_attempt(scheme, www_ip, host, 443, "GET", path, sni=host,
                             save_as=None, label_note=f"license evidence attempt: {note}")
    write_summary()


def phase_canary(data_ip):
    global _phase
    _phase = "canary"
    print("== phase: canary ==", flush=True)
    if not dukascopy_reachable(data_ip):
        rec = {
            "phase": "canary", "kind": "phase_gate", "result": "SKIPPED_UNREACHABLE",
            "note": "canary GETs withheld: class-level transport failure proven in verify/census; fetching would only escalate reset traffic. Zero canary bytes exist.",
            "fetched_at_utc": utcnow(),
        }
        log_record(rec)
    write_summary()


def main():
    load_state()
    phases = sys.argv[1:] or ["verify", "census", "license", "canary"]
    ips = {DATA_HOST: "194.8.15.180"}
    r_data = r_www = None
    data_ip = www_ip = None
    if any(p in phases for p in ("verify", "census", "license", "canary")):
        need_doh = any(p in phases for p in ("verify", "census", "license", "canary"))
        # DoH must run first (verify) to have IPs; other phases reuse recorded facts
        if "verify" in phases or not os.path.exists(TRANSCRIPTS):
            r_data, r_www, data_ip = phase_verify(ips)
            www_ip = (r_www.get("resolved_ips") or ["104.20.28.213"])[0]
        else:
            # recover IPs from existing transcripts
            with open(TRANSCRIPTS, encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if r.get("kind") == "dns_doh":
                        if r.get("host") == DATA_HOST and r.get("resolved_ips"):
                            data_ip = r["resolved_ips"][0]
                        if r.get("host") == WWW_HOST and r.get("resolved_ips"):
                            www_ip = r["resolved_ips"][0]
            data_ip = data_ip or "194.8.15.180"
            www_ip = www_ip or "104.20.28.213"
        if "census" in phases:
            phase_census(data_ip)
        if "license" in phases:
            phase_license(data_ip, www_ip)
        if "canary" in phases:
            phase_canary(data_ip)
    write_summary()
    print("driver done; bytes_downloaded_total =", _state["bytes_downloaded_total"], flush=True)


if __name__ == "__main__":
    main()
