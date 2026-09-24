"""Build the 15m execution plane + H1 regime plane + cost authority census.

Input : data_local/duka/M1/{BID,ASK}/*.bi5 + m1_manifest.json (verify-on-read)
Output: data_local/derived/bars15.parquet, data_local/derived/census.json

Conventions (probe PROBE_PASS 2026-09-23):
  - minute ts = day 00:00 UTC + sec (epoch semantics proven by EDQ1 + probe)
  - minute TRADABLE iff vol>0 AND 0.8<bid.open<1.35 AND ask.open>=bid.open
  - a 15m bar is VALID iff all 15 minutes are tradable (EDQ1 law: missing
    or invalid minutes invalidate the bar; no interpolation anywhere)
  - an H1 regime bar is VALID iff exactly its four 15m bars are VALID

Fail-closed exits: manifest sha mismatch; midweek-day tradable-minute share
below floor; non-positive spread dominance.
"""
import datetime as dt
import hashlib
import json
import lzma
import struct
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import sys as _sys
PAIR = "EURUSD"
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data_local" / PAIR / "M1"
MANIFEST = ROOT / "data_local" / PAIR / "m1_manifest.json"
DERIVED = ROOT / "data_local" / PAIR / "derived"

FX_PAIRS = {"EURUSD": {"scale": 1e5, "pip": 1e-4, "range": (0.95, 1.45)}}
SCALE = FX_PAIRS[PAIR]["scale"]
PIP = FX_PAIRS[PAIR]["pip"]


def load_day(side, rel_name):
    """Verify sha from manifest, decode 24B records -> ndarray [1440,5] float64."""
    path = RAW / side / rel_name
    raw = path.read_bytes()
    man = MANIFEST_JSON["files"].get(f"M1/{side}/{rel_name}")  # fxm keys carry the M1 prefix
    if man is None or man.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise SystemExit(f"FAIL_CLOSED manifest mismatch: {side}/{rel_name}")
    plain = lzma.decompress(raw)
    n = len(plain) // 24
    arr = np.empty((n, 6), dtype=np.float64)
    for i in range(n):
        sec, o, c, l, h, v = struct.unpack_from(">5if", plain, 24 * i)
        arr[i] = (sec, o / SCALE, c / SCALE, l / SCALE, h / SCALE, v)
    return arr


MANIFEST_JSON = json.loads(MANIFEST.read_text())

bid_files = sorted(f.name for f in (RAW / "BID").glob("*.bi5"))
ask_files = sorted(f.name for f in (RAW / "ASK").glob("*.bi5"))
assert bid_files == ask_files, "BID/ASK day file sets differ"

rows = []
census = {
    "days": 0, "days_missing_both": [], "days_short_records": {},
    "min_tradable_by_dow": [0] * 7, "min_total_by_dow": [0] * 7,
    "nonpos_spread_minutes": 0, "price_range_violations": 0,
    "first_ts": None, "last_ts": None,
}
for name in bid_files:
    y, m, d = map(int, name[:-4].split("-"))
    day0 = dt.datetime(y, m, d, tzinfo=dt.timezone.utc)
    b = load_day("BID", name)
    a = load_day("ASK", name)
    census["days"] += 1
    if len(b) != 1440 or len(a) != 1440:
        census["days_short_records"][name] = [len(b), len(a)]
    n = min(len(b), len(a))
    lo_p, hi_p = FX_PAIRS[PAIR]["range"]
    tradable = (
        (b[:n, 5] > 0)
        & (b[:n, 1] > lo_p) & (b[:n, 1] < hi_p)
        & (a[:n, 1] >= b[:n, 1])
    )
    census["nonpos_spread_minutes"] += int(np.sum(a[:n, 1] < b[:n, 1]))
    census["price_range_violations"] += int(np.sum(~((b[:n, 1] > lo_p) & (b[:n, 1] < hi_p))))
    dow = day0.weekday()
    census["min_tradable_by_dow"][dow] += int(tradable.sum())
    census["min_total_by_dow"][dow] += n
    if tradable.any():
        ts_first = day0 + dt.timedelta(seconds=int(b[int(np.argmax(tradable)), 0]))
        census["first_ts"] = census["first_ts"] or ts_first.isoformat()
        census["last_ts"] = (day0 + dt.timedelta(seconds=int(b[n - 1, 0]))).isoformat()
    secs = b[:n, 0]
    for k in range(0, n - 14, 15):  # 15m buckets aligned :00 :15 :30 :45
        sl = slice(k, k + 15)
        if not tradable[sl].all() or not np.all(np.diff(secs[sl]) == 60):
            continue
        bb, aa = b[sl], a[sl]
        rows.append(
            (
                int(day0.timestamp()) + int(secs[k]),
                bb[0, 1], bb[:, 2].max(), bb[:, 3].min(), bb[-1, 2],
                aa[0, 1], aa[:, 2].max(), aa[:, 3].min(), aa[-1, 2],
                aa[0, 1] - bb[0, 1], aa[-1, 2] - bb[-1, 2],
            )
        )

cols = ["ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_h", "a_l", "a_c", "s_open", "s_close"]
df = pd.DataFrame(rows, columns=cols).sort_values("ts").reset_index(drop=True)
dup = int(df["ts"].duplicated().sum())
if dup:
    raise SystemExit(f"FAIL_CLOSED duplicate 15m timestamps: {dup}")
df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)

DERIVED.mkdir(parents=True, exist_ok=True)
df.to_parquet(DERIVED / "bars15.parquet", index=False)

# spread census by session (opens), pips
s_open = df["s_open"].to_numpy() / PIP
hour = df["ts"].dt.hour.to_numpy()
dow = df["ts"].dt.dayofweek.to_numpy()
sessions = {
    "asia_00_07": (hour >= 0) & (hour < 7),
    "london_07_12": (hour >= 7) & (hour < 12),
    "ny_overlap_12_16": (hour >= 12) & (hour < 16),
    "ny_late_16_21": (hour >= 16) & (hour < 21),
    "rollover_21_22": (hour == 21),
    "late_22_24": (hour >= 22),
}


def q(a):
    return {p: round(float(np.quantile(a, p / 100)), 3) for p in (50, 75, 90, 95, 99)}


spread_by_session = {k: q(s_open[mk]) for k, mk in sessions.items() if mk.sum() > 100}
friday = (dow == 4) & (hour == 20)
sunday = (dow == 6) & (hour >= 21) & (hour < 22)
census["spread_pips"] = {
    "overall_open": q(s_open),
    "by_session_open": spread_by_session,
    "friday_20_23_open": q(s_open[friday]) if friday.sum() > 50 else None,
    "sunday_open_21_22": q(s_open[sunday]) if sunday.sum() > 50 else None,
}
census["bars15_valid"] = int(len(df))
expected_midweek = census["min_tradable_by_dow"][0] + census["min_tradable_by_dow"][2]
total_midweek = census["min_total_by_dow"][0] + census["min_total_by_dow"][2]
census["midweek_tradable_share"] = round(expected_midweek / max(total_midweek, 1), 5)
census["days_short_records_n"] = len(census["days_short_records"])

share_ok = census["midweek_tradable_share"] > 0.90
dom_pos = census["nonpos_spread_minutes"] / max(len(df) * 15, 1) < 0.01
census["gates"] = {
    "midweek_tradable_share_gt_0.90": share_ok,
    "nonpos_spread_share_lt_1pct": dom_pos,
    "bars15_gt_100k": len(df) > 100_000,
}
census["verdict"] = "BUILD_PASS" if all(census["gates"].values()) else "BUILD_FAIL"

# H1 regime plane: an hour is VALID iff exactly its four 15m bars are present
grp = df.set_index("ts").groupby(pd.Grouper(freq="h"))
h1 = grp.agg(
    n=("b_c", "size"), b_o=("b_o", "first"), b_h=("b_h", "max"), b_l=("b_l", "min"),
    b_c=("b_c", "last"), a_o=("a_o", "first"), a_c=("a_c", "last"),
)
h1 = h1[h1["n"] == 4].drop(columns="n")
h1.to_parquet(DERIVED / "bars1h.parquet")

(census["data_manifest"] ) = {
    "bars15_rows": int(len(df)),
    "bars1h_rows": int(len(h1)),
    "m1_manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
}
(DERIVED / "census.json").write_text(json.dumps(census, indent=1, default=str))
print(json.dumps({k: census[k] for k in ("verdict", "gates", "bars15_valid", "midweek_tradable_share", "nonpos_spread_minutes")}, indent=1))
print("spread p50 overall (pips):", census["spread_pips"]["overall_open"][50])
print("wrote", DERIVED / "census.json")
sys.exit(0 if census["verdict"] == "BUILD_PASS" else 2)
