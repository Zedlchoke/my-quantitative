"""CME transport re-measure 2026-10-02 — no circumvention.

Same discrimination logic as FX-FUTURES-FRONTIER-V1 A2: plain HTTPS GET to
official CME endpoints with short timeout, plus neutral control hosts.
A measured filter is owner evidence, never bypassed.
"""
import json
import socket
import ssl
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent

TARGETS = [
    "https://www.cmegroup.com/",
    "https://www.cmegroup.com/CmeWS/mvc/Quotes/Future/305/G",
    "https://cmegroup.com/education/",
]
CONTROLS = [
    "https://www.interactivebrokers.com/",
    "https://www.nyfed.org/",
]

DNS_NAMES = ["www.cmegroup.com", "www.cmegroup.com.edgekey.net"]


def try_get(url: str, timeout: float = 10.0) -> dict:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(2048)
            return {"url": url, "ok": True, "status": r.status,
                    "elapsed_s": round(time.time() - t0, 2),
                    "body_prefix_sha_input_len": len(body)}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "ok": False, "elapsed_s": round(time.time() - t0, 2),
                "error": f"{type(e).__name__}: {e}"}


def try_dns(name: str) -> dict:
    t0 = time.time()
    try:
        infos = socket.getaddrinfo(name, 443, proto=socket.IPPROTO_TCP)
        addrs = sorted({i[4][0] for i in infos})
        return {"name": name, "addrs": addrs, "elapsed_s": round(time.time() - t0, 2)}
    except Exception as e:  # noqa: BLE001
        return {"name": name, "error": f"{type(e).__name__}: {e}"}


def try_tls_sni(host: str, sni: str | None, timeout: float = 8.0) -> dict:
    t0 = time.time()
    try:
        raw = socket.create_connection((host, 443), timeout=timeout)
        ctx = ssl.create_default_context()
        wrap_args = {"server_hostname": sni} if sni else {}
        with ctx.wrap_socket(raw, **wrap_args) as s:
            cert = s.getpeercert()
            return {"host": host, "sni": sni, "ok": True,
                    "elapsed_s": round(time.time() - t0, 2),
                    "cert_subject": dict(x[0] for x in cert.get("subject", []))}
    except Exception as e:  # noqa: BLE001
        return {"host": host, "sni": sni, "ok": False,
                "elapsed_s": round(time.time() - t0, 2),
                "error": f"{type(e).__name__}: {e}"}


def main() -> None:
    res = {"measured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "method": "plain HTTPS GET / DNS resolution / TLS handshake with-SNI vs "
                     "no-SNI, no circumvention attempted",
           "dns": [try_dns(n) for n in DNS_NAMES],
           "targets": [try_get(u) for u in TARGETS],
           "controls": [try_get(u) for u in CONTROLS]}
    dns = res["dns"][0]
    if dns.get("addrs"):
        ip = dns["addrs"][0]
        res["tls_discrimination"] = [
            try_tls_sni(ip, "www.cmegroup.com"),
            try_tls_sni(ip, None),
        ]
    (OUT / "cme_transport_recheck_2026-10-02.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("dns", "targets", "controls", "tls_discrimination")
                      if k in res}, indent=1)[:3000])


if __name__ == "__main__":
    main()
