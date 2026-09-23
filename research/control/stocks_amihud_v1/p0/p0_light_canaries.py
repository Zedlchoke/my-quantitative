"""STOCKS-AMIHUD-V1 P0 light canaries (F1/F2/F3a light).

A handful of EODHD /eod + /exchange-symbol-list probes ONLY (no universe
crawl — that is the heavy queued job). API key is read from .env at repo
root and NEVER echoed. Artifacts land next to this script.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_PATH = Path("/Users/hoangminhlong/my-quantitative/.env")
BASE = "https://eodhd.com/api"
RATE_SLEEP = 1.2  # polite, light

# Frozen canary definitions (plan §4 F2/F3a; V8 probe precedent for dates)
DEAD_CANARIES = {  # ticker -> expected final bar (death session)
    "TWTR.US": "2022-10-27",
    "SIVB.US": "2023-03-09",
    "TWX.US": "2018-06-14",   # TWX delisted mid-2018 on the TW merger
    "FRC.US": "2023-03-09",   # V7 evidence: served only via OTC alias FRCB
}
NEVER_EXISTED = ["ZZZQQQ.US", "QQQZZZZ.US"]
LIVING = ["AAPL.US", "SPY.US"]

SPLIT_FIXTURES = {  # ticker -> (ex-date, ratio k) plan F3a
    "AAPL.US": ("2020-08-31", 4.0),
    "TSLA.US": ("2020-08-31", 5.0),
    "CMG.US": ("2024-06-26", 50.0),
    "TJX.US": ("2018-11-07", 2.0),
}


def load_token() -> str:
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("EODHD_API_KEY missing from .env")


TOKEN = load_token()


def get(path: str, params: dict) -> tuple[int, bytes]:
    q = dict(params)
    q["api_token"] = TOKEN
    url = f"{BASE}{path}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": "stocks-amihud-v1-p0-light/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:512]


def rows(payload: bytes):
    try:
        v = json.loads(payload)
        return v if isinstance(v, list) else []
    except Exception:
        return []


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    out: dict = {"schema": "p0_light_canaries/stocks_amihud_v1@1",
                 "measured_utc": datetime.now(timezone.utc).isoformat(),
                 "notes": "light probes only; no universe crawl; token never echoed"}
    raw_dir = HERE / "raw_light"
    raw_dir.mkdir(exist_ok=True)

    # F1 entitlement: living canaries served
    f1 = {}
    for t in LIVING:
        st, b = get("/eod/" + t, {"fmt": "json", "from": "2019-01-01", "to": "2019-01-10"})
        (raw_dir / f"f1_{t.replace('.','_')}.json").write_bytes(b)
        r = rows(b)
        f1[t] = {"status": st, "rows": len(r), "sha256": sha(b),
                 "first_date": r[0].get("date") if r else None}
        time.sleep(RATE_SLEEP)
    out["F1_entitlement"] = f1

    # F2 dead canaries + never-existed + double-pull byte identity
    f2 = {"dead": {}, "never_existed": {}, "double_pull": {}}
    for t, expect_last in DEAD_CANARIES.items():
        st, b = get("/eod/" + t, {"fmt": "json", "from": "2000-01-01", "to": "2026-09-23"})
        (raw_dir / f"f2_dead_{t.replace('.','_')}.json").write_bytes(b)
        r = rows(b)
        f2["dead"][t] = {"status": st, "rows": len(r),
                         "expected_final_bar": expect_last,
                         "served_final_bar": r[-1].get("date") if r else None,
                         "match": bool(r) and r[-1].get("date") == expect_last}
        time.sleep(RATE_SLEEP)
    for t in NEVER_EXISTED:
        st, b = get("/eod/" + t, {"fmt": "json", "from": "2019-01-01", "to": "2019-12-31"})
        f2["never_existed"][t] = {"status": st, "rows": len(rows(b))}
        time.sleep(RATE_SLEEP)
    # double-pull byte identity x3 on SIVB (a bounded window)
    pulls = []
    for i in range(3):
        st, b = get("/eod/SIVB.US", {"fmt": "json", "from": "2022-01-01", "to": "2023-03-31"})
        pulls.append(sha(b))
        time.sleep(RATE_SLEEP)
    f2["double_pull"]["SIVB.US_window_2022-01-01_2023-03-31"] = {
        "sha256_x3": pulls, "byte_identical": len(set(pulls)) == 1}
    out["F2_liveness"] = f2

    # F3a split fixtures: price drop ratio + volume jump ratio around ex-date
    f3 = {}
    import datetime as _dt
    for t, (ex, k) in SPLIT_FIXTURES.items():
        d0 = (_dt.date.fromisoformat(ex) - _dt.timedelta(days=10)).isoformat()
        d1 = (_dt.date.fromisoformat(ex) + _dt.timedelta(days=10)).isoformat()
        st, b = get("/eod/" + t, {"fmt": "json", "from": d0, "to": d1})
        (raw_dir / f"f3a_split_{t.replace('.','_')}_{ex}.json").write_bytes(b)
        r = rows(b)
        i_prev = None
        for i, row in enumerate(r):
            if row.get("date") >= ex and i > 0:
                i_prev = i - 1
                break
        if i_prev is None or i_prev + 1 >= len(r):
            f3[t] = {"status": st, "rows": len(r), "verdict": "UNDECIDABLE_NO_BARS"}
            time.sleep(RATE_SLEEP)
            continue
        prev, post = r[i_prev], r[i_prev + 1]
        c_prev = prev.get("close") or 0.0
        c_post = post.get("close") or 0.0
        v_prev = prev.get("volume") or 0.0
        v_post = post.get("volume") or 0.0
        price_drop = (c_prev / c_post) if c_post else None          # expect ~k
        vol_jump = (v_post / v_prev) if v_prev else None            # ~k => raw volume; ~1 => adjusted
        adj_prev = prev.get("adjusted_close") or 0.0
        adj_post = post.get("adjusted_close") or 0.0
        adj_drop = (adj_prev / adj_post) if adj_post else None      # ~1 => adjusted series smooths split
        f3[t] = {"status": st, "ex_date": ex, "split_k": k,
                 "prev_date": prev.get("date"), "post_date": post.get("date"),
                 "close_prev": c_prev, "close_post": c_post,
                 "adjusted_prev": adj_prev, "adjusted_post": adj_post,
                 "price_drop_ratio": price_drop, "volume_jump_ratio": vol_jump,
                 "adjusted_drop_ratio": adj_drop,
                 "volume_basis": ("RAW" if vol_jump and vol_jump > 1.8 else
                                  "SPLIT_ADJUSTED" if vol_jump and vol_jump < 1.25 else
                                  "UNDECIDABLE")}
        time.sleep(RATE_SLEEP)
    out["F3a_split_fixtures"] = f3

    # aggregate F3a verdict: majority basis across the four fixtures
    bases = [v.get("volume_basis") for v in f3.values() if isinstance(v, dict)]
    decided = [b_ for b_ in bases if b_ in ("RAW", "SPLIT_ADJUSTED")]
    out["F3a_aggregate"] = {
        "per_fixture": bases,
        "majority_volume_basis": (max(set(decided), key=decided.count) if decided else "UNDECIDABLE"),
        "rule": "DV pair = raw close x raw volume if RAW; split-adjusted price x volume if SPLIT_ADJUSTED; mixed pairs forbidden (plan F3a)",
    }

    (HERE / "p0_light_canary_results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"F1": {k: v["rows"] for k, v in f1.items()},
                      "F2_dead_match": {k: v["match"] for k, v in f2["dead"].items()},
                      "F2_never_existed_rows": {k: v["rows"] for k, v in f2["never_existed"].items()},
                      "F2_double_pull_identical": f2["double_pull"],
                      "F3a": {k: (v or {}).get("volume_basis") for k, v in f3.items()},
                      "F3a_aggregate": out["F3a_aggregate"]["majority_volume_basis"]}, indent=1))


if __name__ == "__main__":
    main()
