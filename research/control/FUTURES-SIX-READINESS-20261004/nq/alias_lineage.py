"""NQ-ALIAS-REPAIR Task 1 — re-derive the raw alias lineage from the RAW
vendor parquets (NOT the baseline cache), full-file census.

Counts, per source dir (AV1R-O1M-NQ-DELTA + AV1T-O1M-NQ) and combined:
  * total rows; dash rows total;
  * dash rows by raw_symbol (bars/volume/first/last/instrument_ids);
  * 'NQU8-NQM9' rows (expect 92,075 per nq2020_hole_probe — re-derived here);
  * instrument_id 16908 rows split by UTC date vs 2020-06-01, by raw_symbol
    (expect 19,406 post-cutover under 'NQM0');
  * which instrument_ids exist among dash rows, so the relabel
    (id==16908 & date<2020-06-01 -> 'NQM0') provably touches ONLY id 16908;
  * id-16908 rows under NON-dash symbols before the cutover (expect none).

Read-only on the data root. Output: alias_lineage.json next to this script.
"""
from __future__ import annotations

import glob
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
DIRS = ["AV1R-O1M-NQ-DELTA", "AV1T-O1M-NQ"]
OUT = os.path.join(HERE, "alias_lineage.json")

CUTOVER = pd.Timestamp("2020-06-01", tz="UTC")


def scan_file(f: str, acc: dict) -> None:
    d = pd.read_parquet(f)
    d["dt"] = pd.to_datetime(d["ts_event"], unit="ns", utc=True)
    is_dash = d["raw_symbol"].str.contains("-", regex=False)
    acc["total_rows"] += int(len(d))
    acc["dash_rows"] += int(is_dash.sum())
    acc["plain_rows"] += int((~is_dash).sum())
    # dash rows by raw_symbol
    for sym, g in d[is_dash].groupby("raw_symbol"):
        e = acc["dash_by_symbol"].setdefault(sym, {
            "bars": 0, "volume": 0, "first": None, "last": None,
            "instrument_ids": set(), "files": 0})
        e["bars"] += int(len(g))
        e["volume"] += int(g["volume"].sum())
        e["first"] = str(min(pd.Timestamp(e["first"]), g["dt"].min())) \
            if e["first"] else str(g["dt"].min())
        e["last"] = str(max(pd.Timestamp(e["last"]), g["dt"].max())) \
            if e["last"] else str(g["dt"].max())
        e["instrument_ids"].update(int(x) for x in g["instrument_id"].unique())
        e["files"] += 1
    # instrument 16908 census
    i16908 = d[d["instrument_id"] == 16908]
    pre = i16908[i16908["dt"] < CUTOVER]
    post = i16908[i16908["dt"] >= CUTOVER]
    acc["id16908_pre_cutover_bars"] += int(len(pre))
    acc["id16908_pre_cutover_volume"] += int(pre["volume"].sum())
    for sym, g in pre.groupby("raw_symbol"):
        e = acc["id16908_pre_by_symbol"].setdefault(str(sym), {
            "bars": 0, "volume": 0, "first": None, "last": None})
        e["bars"] += int(len(g))
        e["volume"] += int(g["volume"].sum())
        e["first"] = str(min(pd.Timestamp(e["first"]), g["dt"].min())) \
            if e["first"] else str(g["dt"].min())
        e["last"] = str(max(pd.Timestamp(e["last"]), g["dt"].max())) \
            if e["last"] else str(g["dt"].max())
    acc["id16908_post_cutover_bars"] += int(len(post))
    acc["id16908_post_cutover_volume"] += int(post["volume"].sum())
    for sym, g in post.groupby("raw_symbol"):
        e = acc["id16908_post_by_symbol"].setdefault(str(sym), {
            "bars": 0, "volume": 0, "first": None, "last": None})
        e["bars"] += int(len(g))
        e["volume"] += int(g["volume"].sum())
        e["first"] = str(min(pd.Timestamp(e["first"]), g["dt"].min())) \
            if e["first"] else str(g["dt"].min())
        e["last"] = str(max(pd.Timestamp(e["last"]), g["dt"].max())) \
            if e["last"] else str(g["dt"].max())
    # do any NON-dash rows carry id 16908 before cutover? (expect none)
    pre_plain = pre[~pre["raw_symbol"].str.contains("-", regex=False)]
    if len(pre_plain):
        acc["id16908_pre_plain_rows"] += int(len(pre_plain))
        for sym, g in pre_plain.groupby("raw_symbol"):
            acc["id16908_pre_plain_symbols"][str(sym)] = \
                acc["id16908_pre_plain_symbols"].get(str(sym), 0) + int(len(g))


def main() -> None:
    acc = {
        "files_scanned": [],
        "total_rows": 0, "dash_rows": 0, "plain_rows": 0,
        "dash_by_symbol": {},
        "id16908_pre_cutover_bars": 0, "id16908_pre_cutover_volume": 0,
        "id16908_post_cutover_bars": 0, "id16908_post_cutover_volume": 0,
        "id16908_pre_by_symbol": {}, "id16908_post_by_symbol": {},
        "id16908_pre_plain_rows": 0, "id16908_pre_plain_symbols": {},
    }
    for dname in DIRS:
        files = sorted(glob.glob(f"{DATA_ROOT}/{dname}/*.parquet"))
        if not files:
            acc["missing_dir"] = f"{DATA_ROOT}/{dname}"
            raise SystemExit(f"missing raw dir: {DATA_ROOT}/{dname}")
        for f in files:
            acc["files_scanned"].append(os.path.relpath(f, DATA_ROOT))
            scan_file(f, acc)
            print(f"scanned {os.path.basename(f)} "
                  f"(running total {acc['total_rows']:,})", flush=True)

    # ---- derived checks ----
    nqu8 = acc["dash_by_symbol"].get("NQU8-NQM9", {})
    checks = {
        "nqu8_nqm9_bars": int(nqu8.get("bars", 0)),
        "nqu8_nqm9_expected_92075": int(nqu8.get("bars", 0)) == 92075,
        "id16908_pre_equals_alias_bars":
            acc["id16908_pre_cutover_bars"] == int(nqu8.get("bars", 0)),
        "id16908_post_bars": acc["id16908_post_cutover_bars"],
        "id16908_post_expected_19406_under_NQM0": (
            acc["id16908_post_by_symbol"].get("NQM0", {}).get("bars") == 19406
            and list(acc["id16908_post_by_symbol"]) == ["NQM0"]),
        "id16908_pre_all_under_dash_alias": (
            list(acc["id16908_pre_by_symbol"]) == ["NQU8-NQM9"]),
        "id16908_pre_plain_rows_zero": acc["id16908_pre_plain_rows"] == 0,
    }
    dash_ids = sorted({int(i) for e in acc["dash_by_symbol"].values()
                       for i in e["instrument_ids"]})
    ids_of_nqu8 = sorted(int(i) for i in nqu8.get("instrument_ids", set()))
    checks["dash_rows_instrument_ids"] = dash_ids
    checks["nqu8_nqm9_instrument_ids"] = ids_of_nqu8
    checks["relabel_touches_only_id16908"] = ids_of_nqu8 == [16908]

    res = {
        "schema": "nq_alias_lineage@1",
        "lane": "NQ-ALIAS-REPAIR",
        "cycle": "FUTURES-SIX-READINESS-20261004",
        "data_root": DATA_ROOT,
        "source_dirs": DIRS,
        "cutover_utc": "2020-06-01T00:00:00+00:00",
        "totals": {k: acc[k] for k in
                   ("total_rows", "dash_rows", "plain_rows")},
        "dash_by_symbol": {k: {kk: (sorted(vv) if isinstance(vv, set) else vv)
                               for kk, vv in v.items()}
                           for k, v in sorted(acc["dash_by_symbol"].items())},
        "id16908_pre_cutover": {
            "bars": acc["id16908_pre_cutover_bars"],
            "volume": acc["id16908_pre_cutover_volume"],
            "by_symbol": acc["id16908_pre_by_symbol"]},
        "id16908_post_cutover": {
            "bars": acc["id16908_post_cutover_bars"],
            "volume": acc["id16908_post_cutover_volume"],
            "by_symbol": acc["id16908_post_by_symbol"]},
        "id16908_pre_non_dash_rows": acc["id16908_pre_plain_rows"],
        "checks": checks,
        "verdict": ("A_ALIAS_NOT_ABSENCE re-derived from raw: ALL pre-cutover "
                    "id-16908 rows sit under dash alias 'NQU8-NQM9'; relabel "
                    "id==16908 & dt<2020-06-01 -> 'NQM0' touches ONLY id 16908"
                    ) if all(v is True for k, v in checks.items()
                             if isinstance(v, bool)) else "CHECK_FAILED",
    }
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, allow_nan=False)
    print(json.dumps(checks, indent=1))
    print("verdict:", res["verdict"])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
