"""CHR3F staging orchestrator — heavy-lock aware, paced, sha256-manifested.

Lock discipline: acquire/release PER ITEM (V13 yielding pattern) so foreign
cycles can interleave heavy work between staging items. Phase A = equivalence
data (original frozen windows; basis via the FROZEN restage_basis.py run
unmodified). Phase B = replication windows (window-parameterized runner using
the same frozen fetch protocol). Resumable via staging/state/*.done.
Exit codes: 0 complete, 4 dirty tree, 7 lock busy (retry later).
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(REPO))
from research.governance import heavy_lock  # noqa: E402

WT = Path(__file__).resolve().parents[3]
CTRL = WT / "research/control/crypto_historical_replication_3f_v1"
STAGE = CTRL / "staging"
STATE = STAGE / "state"
V14_ROOT = CTRL / "recovered/v14_root"
CYCLE = "CRYPTO-HISTORICAL-REPLICATION-3F-V1"
PY = REPO / ".venv/bin/python"

SYMS20 = ["1000PEPEUSDT","AAVEUSDT","ACEUSDT","ADAUSDT","AVAXUSDT","BCHUSDT","BNBUSDT",
          "BOMEUSDT","BTCUSDT","DOGEUSDT","ENAUSDT","ETHUSDT","LINKUSDT","NEARUSDT",
          "ONGUSDT","SOLUSDT","SUIUSDT","WLDUSDT","XRPUSDT","ZECUSDT"]
SYMS19 = [s for s in SYMS20 if s != "BTCUSDT"]
MS = lambda *a: int(datetime(*a, tzinfo=timezone.utc).timestamp()*1000)

A_KL_MONTHS = [(y,m) for y in (2024,2025,2026) for m in range(1,13)
               if MS(y,m,1) >= MS(2024,8,1) and MS(y,m,1) <= MS(2026,8,1)]
A_FUND = (MS(2024,8,20), MS(2026,8,22))
B_KL_MONTHS = [(y,m) for y in range(2020,2025) for m in range(1,13)
               if MS(y,m,1) >= MS(2020,1,1) and MS(y,m,1) <= MS(2024,8,1)]
B_FUND = (MS(2020,7,1), MS(2024,8,20))
B_BASIS = (MS(2020,6,1), MS(2024,8,19,23,59))
A_BASIS_WINDOW = (MS(2025,6,30), MS(2026,8,21,23,59))

VISION = "https://data.binance.vision/data/futures/um/monthly"
FAPI = "https://fapi.binance.com"
UA = {"User-Agent": "chr3f-staging/1 (research; paced; keyless)"}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def http_get(url: str, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return f"ERR:{type(e).__name__}", b""

def fetch_backoff(url: str, attempts=8, backoff=20.0) -> bytes:
    last = None
    for i in range(attempts):
        st, b = http_get(url)
        if st == 200:
            return b
        last = st
        time.sleep(backoff)
    raise RuntimeError(f"fail-closed after {attempts} attempts: {url[:120]} (last status {last})")

def done_key(kind, ident) -> Path:
    return STATE / f"{kind}__{ident.replace('/','_')}.done"

def manifest_write(kind, ident, rows):
    p = STAGE / "manifests" / f"{kind}__{ident.replace('/','_')}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"kind": kind, "ident": ident,
                             "written_utc": datetime.now(timezone.utc).isoformat(),
                             "entries": rows}, indent=1))

def stage_klines_sym(sym, months) -> dict:
    out = STAGE / "klines" / sym; out.mkdir(parents=True, exist_ok=True)
    entries = []
    for (y, m) in months:
        name = f"{sym}-15m-{y}-{m:02d}.zip"
        dest = out / name
        url = f"{VISION}/klines/{sym}/15m/{name}"
        if not dest.exists():
            st, b = http_get(url)
            if st != 200:
                entries.append({"file": name, "status": st, "note": "absent archive"})
                time.sleep(0.5); continue
            dest.write_bytes(b); time.sleep(0.5)
        csum = dest.with_name(name + ".CHECKSUM")
        if not csum.exists():
            st, b = http_get(url + ".CHECKSUM"); time.sleep(0.3)
            if st == 200: csum.write_bytes(b)
        ok = None
        if csum.exists():
            expected = csum.read_text().split()[0].strip().lower()
            ok = sha256_file(dest) == expected
            if not ok:
                dest.unlink()
                raise RuntimeError(f"CHECKSUM mismatch {name} - fail closed")
        entries.append({"file": name, "sha256": sha256_file(dest),
                        "bytes": dest.stat().st_size, "checksum_verified": ok, "url": url})
    manifest_write("klines", sym, entries)
    return {"symbol": sym, "files": len(entries)}

def page_fapi(url_fn, start, end, min_full) -> list:
    rows, cursor = [], start
    while cursor < end:
        batch = json.loads(fetch_backoff(url_fn(cursor, end)))
        if not batch:
            break
        rows.extend(batch)
        if isinstance(batch[0], dict):
            last = max(int(r["fundingTime"]) for r in batch)
        else:
            last = max(int(r[0]) for r in batch)
        if len(batch) < min_full:
            break
        cursor = last + 1
        time.sleep(10.0)  # 6 req/min fapi pacing
    return rows

def stage_funding_sym(sym, win) -> dict:
    rows = {}
    for r in page_fapi(lambda s, e: (f"{FAPI}/fapi/v1/fundingRate?symbol={sym}"
                                     f"&startTime={s}&endTime={e}&limit=1000"),
                       win[0], win[1], 1000):
        rows[(r["symbol"], r["fundingTime"])] = r
    out = STAGE / "funding"; out.mkdir(parents=True, exist_ok=True)
    f = out / f"{sym}_funding.json"
    f.write_text(json.dumps({"symbol": sym, "window": list(win), "n": len(rows),
                             "rows": sorted(rows.values(), key=lambda r: int(r["fundingTime"]))},
                            indent=1))
    manifest_write("funding", sym, [{"file": f.name, "sha256": sha256_file(f),
                                     "rows": len(rows)}])
    return {"symbol": sym, "rows": len(rows)}

def stage_index_sym(sym, win) -> dict:
    rows = page_fapi(lambda s, e: (f"{FAPI}/fapi/v1/indexPriceKlines?pair={sym}"
                                   f"&interval=15m&startTime={s}&endTime={e}&limit=1000"),
                     win[0], win[1], 1000)
    out = STAGE / "index"; out.mkdir(parents=True, exist_ok=True)
    f = out / f"{sym}_index_15m.json"
    f.write_text(json.dumps({"pair": sym, "window": list(win), "n": len(rows),
                             "rows": rows}))
    manifest_write("index", sym, [{"file": f.name, "sha256": sha256_file(f),
                                   "rows": len(rows)}])
    return {"symbol": sym, "rows": len(rows)}

def stage_basis_frozen(sym, out: Path) -> dict:
    """Phase A basis: the FROZEN restage_basis.py, run unmodified, one symbol."""
    r = subprocess.run([str(PY), str(V14_ROOT / "research/v14/families/basislv_premfade/restage_basis.py"),
                        "--out-root", str(out), "--symbols", sym],
                       cwd=str(V14_ROOT), capture_output=True, text=True)
    (out / f"runner_{sym}.log").write_text(r.stdout + "\n" + r.stderr)
    if r.returncode != 0:
        raise RuntimeError(f"frozen restage_basis failed rc={r.returncode} for {sym}")
    j = json.loads((out / "restage_summary.json").read_text())
    return {"mode": "frozen_script", "symbol": sym,
            "rows": j["entries"][-1]["rows"]}

def stage_basis_window_sym(sym, win, out: Path) -> dict:
    """Phase B basis: window-parameterized, SAME frozen protocol (forward-only,
    limit 500, 0.55s serial, 8x20s backoff) - derived from restage_basis.py."""
    out.mkdir(parents=True, exist_ok=True)
    start, end = win; BUCKET = 900_000; rows = {}; cursor = start
    while cursor < end:
        batch = json.loads(fetch_backoff(
            f"{FAPI}/futures/data/basis?contractType=PERPETUAL&period=15m"
            f"&limit=500&pair={sym}&startTime={cursor}&endTime={end}"))
        if not batch:
            break
        for r in batch:
            rows[int(r["timestamp"])] = r
        last = max(int(r["timestamp"]) for r in batch)
        if len(batch) < 500:
            break
        cursor = last + BUCKET
        time.sleep(0.55)
    f = out / f"{sym}_basis_15m.json"
    f.write_text(json.dumps({"pair": sym, "window": list(win), "n": len(rows),
                             "rows": [rows[k] for k in sorted(rows)]}))
    manifest_write("basis_win", sym, [{"file": f.name, "sha256": sha256_file(f),
                                       "rows": len(rows)}])
    return {"symbol": sym, "rows": len(rows)}

def sh(*a) -> str:
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout.strip()

def build_items():
    # (kind, ident, fn) triples: ident must be explicit (default-arg lambdas
    # have no closure cells - first draft skipped siblings, caught pre-run)
    items = []
    for s in SYMS20: items.append(("A_klines", s, lambda s=s: stage_klines_sym(s, A_KL_MONTHS)))
    for s in SYMS20: items.append(("A_funding", s, lambda s=s: stage_funding_sym(s, A_FUND)))
    for s in SYMS19: items.append(("A_basis", s, lambda s=s: stage_basis_frozen(s, STAGE / "basis_orig")))
    for s in SYMS19: items.append(("A_index", s, lambda s=s: stage_index_sym(s, A_BASIS_WINDOW)))
    for s in SYMS20: items.append(("B_klines", s, lambda s=s: stage_klines_sym(s, B_KL_MONTHS)))
    for s in SYMS20: items.append(("B_funding", s, lambda s=s: stage_funding_sym(s, B_FUND)))
    for s in SYMS19: items.append(("B_basis", s, lambda s=s: stage_basis_window_sym(s, B_BASIS, STAGE / "basis_win")))
    for s in SYMS19: items.append(("B_index", s, lambda s=s: stage_index_sym(s, B_BASIS)))
    return items

def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True); STATE.mkdir(parents=True, exist_ok=True)
    dirty = sh("git", "-C", str(WT), "status", "--porcelain=v1")
    if dirty:
        print(f"REFUSED dirty tree: {dirty}", file=sys.stderr); return 4
    status_path = STAGE / "stage_status.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {"items": []}
    status["last_run_utc"] = datetime.now(timezone.utc).isoformat()
    remaining = 0; completed = 0
    for (kind, ident, fn) in build_items():
        if done_key(kind, str(ident)).exists():
            continue
        remaining += 1
        try:
            handle = heavy_lock.acquire(cycle_id=CYCLE, role="data-staging",
                                        worktree=str(WT),
                                        command=[str(PY), str(Path(__file__))],
                                        expected_artifacts=[str(status_path)])
        except heavy_lock.LockBusyError:
            print(f"LOCK_BUSY ({completed} done this run, {remaining} pending) - retry later", flush=True)
            status_path.write_text(json.dumps(status, indent=1))
            return 7
        try:
            res = fn()
            status["items"].append({"kind": kind, "ident": str(ident), "res": res,
                                    "utc": datetime.now(timezone.utc).isoformat()})
            done_key(kind, str(ident)).write_text(datetime.now(timezone.utc).isoformat())
            completed += 1
            status_path.write_text(json.dumps(status, indent=1))
            print(f"DONE {kind} {ident}: {json.dumps(res)[:140]}", flush=True)
        finally:
            handle.release()
        time.sleep(5.0)  # interleave window for foreign heavy cycles
    status["finished_utc"] = datetime.now(timezone.utc).isoformat()
    status_path.write_text(json.dumps(status, indent=1))
    print("STAGING COMPLETE", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
