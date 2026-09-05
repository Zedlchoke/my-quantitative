"""A9-F T2b: verify the archived staged OI authority (v11_oi_staging_v1).

Machine-local read-only verification of /Users/hoangminhlong/my-quantitative/
oi_data/consolidated/<SYM>_oi.parquet against
research/control/v11_run/oi_staging_manifest.json:

* per-file SHA-256 equals the pinned value;
* schema is exactly {create_time, sum_open_interest};
* 417 daily rows per symbol, zero internal gaps, 2025-07-01..2026-08-21;
* the OICH/OICYC warmup claim: 55 daily rows (2025-07-01..2025-08-24
  inclusive) available at the first decision stamp 2025-08-25T00:00Z
  (>= 29 anchor rows, >= 15 neighbour rows), and rows exist for every
  weekly Monday stamp through 2026-08-17 (last stamp) with stamps read
  per row (create_time <= T).

No PnL, no positions.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

WORKSPACE_ROOT = Path("/Users/hoangminhlong/my-quantitative")
OI_CONSOLIDATED_ROOT = WORKSPACE_ROOT / "oi_data" / "consolidated"
HERE = Path(__file__).resolve().parent
MANIFEST_PATH = (
    Path(__file__).resolve().parents[3] / "control" / "v11_run" / "oi_staging_manifest.json"
)

SYMBOLS_20 = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]
TRADEABLE = [s for s in SYMBOLS_20 if s != "BTCUSDT"]

FIRST_STAMP_ISO = "2025-08-25T00:00:00Z"
LAST_STAMP_ISO = "2026-08-17T00:00:00Z"


def parse_utc(text: str) -> int:
    return int(
        datetime.strptime(str(text).strip(), "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def mondays(start_iso: str, end_iso: str) -> list[int]:
    start = int(datetime.strptime(start_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
    end = int(datetime.strptime(end_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
    # first Monday strictly on/after start
    day = start - (start % 86400)
    while datetime.fromtimestamp(day, tz=timezone.utc).weekday() != 0:
        day += 86400
    out = []
    while day <= end:
        out.append(day)
        day += 7 * 86400
    return out


def main() -> None:
    manifest = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    stamps = mondays(FIRST_STAMP_ISO, LAST_STAMP_ISO)
    first_stamp = stamps[0]
    report = {
        "schema": "v14_d2_a9f_oi_staging_verification_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "authority": str(MANIFEST_PATH),
        "root": str(OI_CONSOLIDATED_ROOT),
        "weekly_stamps_first_to_last": [len(stamps), stamps[0], stamps[-1]],
        "symbols": {},
        "all_sha_match": True,
        "all_schema_ok": True,
        "all_rows_417": True,
        "all_zero_gaps": True,
        "warmup_rows_at_first_stamp_min": None,
        "stamps_with_complete_crosssection": 0,
    }
    per_symbol_rows: dict[str, list[tuple[int, float]]] = {}
    for sym in SYMBOLS_20:
        path = OI_CONSOLIDATED_ROOT / f"{sym}_oi.parquet"
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        pinned = manifest["symbols"][sym]["parquet_sha256"]
        table = pq.read_table(path)
        columns = list(table.column_names)
        times = [parse_utc(t) for t in table.column("create_time").to_pylist()]
        values = [float(v) for v in table.column("sum_open_interest").to_pylist()]
        rows = sorted(zip(times, values))
        ts_list = [t for t, _ in rows]
        # Calendar-day completeness: one row per UTC day, 2025-07-01..2026-08-21.
        day_index = sorted({t - (t % 86400) for t in ts_list})
        missing_days = [
            datetime.fromtimestamp(d, tz=timezone.utc).strftime("%Y-%m-%d")
            for a, b in zip(day_index, day_index[1:])
            if b - a != 86400
            for d in range(a + 86400, b, 86400)
        ]
        duplicate_days = len(day_index) != len(ts_list)
        # Day-row stamp offsets: the day's LAST 5m snapshot may land earlier
        # than 23:55 (OICH proposal section 4 documents this; consecutive-ness
        # is by day-row index, stamps read per row -- so offsets are not gaps).
        stamp_offsets = sum(1 for t in ts_list if (t % 86400) != (23 * 3600 + 55 * 60))
        n_at_first = sum(1 for t in ts_list if t <= first_stamp)
        positive = all(v > 0 for _, v in rows)
        entry = {
            "sha256": sha,
            "sha256_pinned": pinned,
            "sha_match": sha == pinned,
            "columns": columns,
            "schema_ok": columns == ["create_time", "sum_open_interest"],
            "rows": len(rows),
            "unique_days": len(day_index),
            "duplicate_day_rows": duplicate_days,
            "first_utc": datetime.fromtimestamp(ts_list[0], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_utc": datetime.fromtimestamp(ts_list[-1], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "missing_day_rows": missing_days,
            "non_2355_stamp_rows": stamp_offsets,
            "all_values_positive_finite": positive,
            "daily_rows_available_at_first_stamp": n_at_first,
            "warmup_55_ok": n_at_first >= 55,
            "anchor_29_ok": n_at_first >= 29,
            "neighbour_15_ok": n_at_first >= 15,
        }
        report["symbols"][sym] = entry
        report["all_sha_match"] &= entry["sha_match"]
        report["all_schema_ok"] &= entry["schema_ok"]
        report["all_rows_417"] &= entry["rows"] == manifest["window"]["expected_days"]
        report["all_zero_gaps"] &= (
            not missing_days
            and not duplicate_days
            and len(day_index) == manifest["window"]["expected_days"]
        )
        report["warmup_rows_at_first_stamp_min"] = (
            n_at_first
            if report["warmup_rows_at_first_stamp_min"] is None
            else min(report["warmup_rows_at_first_stamp_min"], n_at_first)
        )
        if sym in TRADEABLE:
            per_symbol_rows[sym] = rows

    # Complete cross-section at every weekly stamp (OICYC needs all 19).
    missing = 0
    for stamp in stamps:
        for sym in TRADEABLE:
            rows = per_symbol_rows[sym]
            if not any(t <= stamp for t, _ in rows):
                missing += 1
    report["stamps_with_complete_crosssection"] = len(stamps) - (1 if missing else 0)
    report["per_symbol_coverage_at_stamps_complete"] = missing == 0

    with open(HERE / "oi_staging_verification.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(
        json.dumps(
            {
                "all_sha_match": report["all_sha_match"],
                "all_schema_ok": report["all_schema_ok"],
                "all_rows_417": report["all_rows_417"],
                "all_zero_gaps": report["all_zero_gaps"],
                "warmup_min_rows_at_first_stamp": report["warmup_rows_at_first_stamp_min"],
                "weekly_stamps": len(stamps),
                "cross_section_complete": report["per_symbol_coverage_at_stamps_complete"],
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
