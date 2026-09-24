#!/usr/bin/env python
"""PIT data audit for ILLIQ-LOSS-MECH-V1 fresh folds Y2022 / Y2023.

Checks every data plane the frozen ILLIQ cell needs, for the exact failure
modes that aborted the CHR3F Y2022/Y2023 attempts (ContractViolation:
"context mark unavailable/invalid for 1000PEPEUSDT") plus warmup/formation
coverage. READ-ONLY on evidence trees; writes only inside this namespace.
Light reads only (file listings + parquet edge metadata) — no heavy job, no
PnL, no scored output.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

NS = Path("/Users/hoangminhlong/my-quantitative/.worktrees/illiq-loss-mech-v1/integration/research/control/illiq_loss_mech_v1/a7_prelaunch/a7_amendment_rerun_workdir")
CHR3F = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1")
B20 = CHR3F / "catalog_live_crypto_b20/data/binance_bar"
SCAN = CHR3F / "funding_data_scan/scan_2026"

SYMS = ["1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT", "BCHUSDT", "BNBUSDT",
        "BOMEUSDT", "BTCUSDT", "DOGEUSDT", "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT",
        "ONGUSDT", "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT"]
# plugin FIRST_ARCHIVE_MONTH (chr3f_illiq_plugin.py) — cross-validated below
FIRST_ARCHIVE_MONTH = {
    "1000PEPEUSDT": (2023, 5), "AAVEUSDT": (2020, 10), "ACEUSDT": (2023, 12),
    "ADAUSDT": (2020, 1), "AVAXUSDT": (2020, 9), "BCHUSDT": (2020, 1),
    "BNBUSDT": (2020, 2), "BOMEUSDT": (2024, 3), "BTCUSDT": (2020, 1),
    "DOGEUSDT": (2020, 7), "ENAUSDT": (2024, 4), "ETHUSDT": (2020, 1),
    "LINKUSDT": (2020, 1), "NEARUSDT": (2020, 10), "ONGUSDT": (2023, 11),
    "SOLUSDT": (2020, 9), "SUIUSDT": (2023, 5), "WLDUSDT": (2023, 7),
    "XRPUSDT": (2020, 1), "ZECUSDT": (2020, 2),
}
FOLDS = {
    "Y2022": {"start": "2022-01-03T00:00:00Z", "end": "2022-12-26T00:00:00Z"},
    "Y2023": {"start": "2023-01-02T00:00:00Z", "end": "2023-12-25T00:00:00Z"},
}
WARMUP_DAYS = 125  # runner: pre = start - 125d


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fname_dt(head: str):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})", head)
    return datetime(*(int(g) for g in m.groups()), tzinfo=timezone.utc) if m else None


def bars_info(sym: str):
    d = B20 / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    if not d.is_dir():
        return {"present": False}
    files = sorted(d.glob("*.parquet"))
    if not files:
        return {"present": False}
    starts = [fname_dt(f.name.split("_")[0]) for f in files]
    ends = [fname_dt(f.name.split("_")[1].removesuffix(".parquet")) for f in files]
    return {"present": True, "n_files": len(files),
            "first_bar": min(s for s in starts if s).isoformat(),
            "last_bar": max(e for e in ends if e).isoformat()}


def funding_info(sym: str, fold_lo: datetime, fold_hi: datetime):
    p = SCAN / sym / "funding.json"
    if not p.is_file():
        return {"present": False}
    doc = json.load(open(p))
    rows = doc.get("rows", [])
    if not rows:
        return {"present": True, "n_rows": 0}
    times = [datetime.fromtimestamp(int(r["fundingTime"]) / 1000, tz=timezone.utc) for r in rows]
    in_win = [t for t in times if fold_lo <= t < fold_hi]
    return {"present": True, "n_rows_total": len(rows),
            "first": min(times).isoformat(), "last": max(times).isoformat(),
            "n_rows_in_fold": len(in_win),
            "in_fold_coverage": (len(in_win) / max(1, int((fold_hi - fold_lo).days * 3)))}


def main() -> int:
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "catalog": str(B20), "funding_scan": str(SCAN), "symbols": {}}

    listing_xcheck = []
    for s in SYMS:
        bi = bars_info(s)
        fam = FIRST_ARCHIVE_MONTH.get(s)
        measured = None
        if bi.get("present"):
            fb = ts(bi["first_bar"])
            measured = (fb.year, fb.month)
        listing_xcheck.append({"symbol": s, "plugin_first_archive_month": list(fam) if fam else None,
                               "b20_first_bar": bi.get("first_bar"),
                               "b20_last_bar": bi.get("last_bar"),
                               "n_files": bi.get("n_files", 0),
                               "month_match": (measured == fam) if (bi.get("present") and fam) else None})
    out["listing_crosscheck"] = listing_xcheck

    for fold, fw in FOLDS.items():
        lo, hi = ts(fw["start"]), ts(fw["end"])
        warm_lo = ts((datetime.fromtimestamp(lo.timestamp() - WARMUP_DAYS * 86400, tz=timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        per = {}
        for s in SYMS:
            bi = bars_info(s)
            e = {"bars": bi}
            if bi.get("present"):
                fb, lb = ts(bi["first_bar"]), ts(bi["last_bar"])
                e["bars_cover_warmup_start"] = fb <= warm_lo
                e["bars_cover_window_end"] = lb >= hi
                e["warmup_needed_from"] = warm_lo.isoformat()
                # benchmark-context marks at first stamp require a bar at/before it
                e["mark_at_first_stamp"] = fb <= lo < lb
            fi = funding_info(s, lo, hi)
            e["funding"] = {k: v for k, v in fi.items() if k != "n_rows_in_fold"} | {"n_rows_in_fold": fi.get("n_rows_in_fold", 0)}
            per[s] = e
        # fold universe under the CHR3F A4 law (listed at window-start month)
        ym = (lo.year, lo.month)
        a4_universe = sorted(s for s in SYMS if tuple(FIRST_ARCHIVE_MONTH[s]) <= ym)
        # mid-fold entrants under a base-universe law (listed after start, during fold)
        mid_fold = sorted(s for s in SYMS if tuple(FIRST_ARCHIVE_MONTH[s]) > ym
                          and ts(f"{FIRST_ARCHIVE_MONTH[s][0]}-{FIRST_ARCHIVE_MONTH[s][1]:02d}-01T00:00:00Z") < hi)
        young_at_start = sorted(s for s in a4_universe
                                if (lo - ts(bars_info(s)["first_bar"])).days < 365)
        # young entrants mid-fold (base law): age at their own listing+365 crosses inside fold
        young_midfold = [s for s in mid_fold]
        out[fold] = {
            "window": fw, "a4_universe_n": len(a4_universe), "a4_universe": a4_universe,
            "min_eligible_ok": len(a4_universe) >= 10,
            "mid_fold_entrants_base_law": mid_fold,
            "young_lt365d_at_start_within_a4": young_at_start,
            "young_entrants_midfold_base_law": young_midfold,
            "per_symbol": per,
        }

    json.dump(out, open(NS / "pit_audit_y2022_y2023_RERUN.json", "w"), indent=1, ensure_ascii=False)

    for fold in FOLDS:
        d = out[fold]
        print(f"{fold}: A4 universe n={d['a4_universe_n']} min10={d['min_eligible_ok']} "
              f"young@start={d['young_lt365d_at_start_within_a4']} midfold={d['mid_fold_entrants_base_law']}")
    bad = [x["symbol"] for x in out["listing_crosscheck"] if x["month_match"] is False]
    print("listing month mismatches:", bad or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
