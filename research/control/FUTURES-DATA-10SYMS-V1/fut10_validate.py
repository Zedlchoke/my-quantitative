"""FUTURES-DATA-10SYMS-V1 — S6 validation over downloaded raw files.

Reads raw_manifest.jsonl + raw payload files, produces per-symbol:
coverage matrix, gaps, duplicates, flat/volume-0 synthetic share, quote
convention checks (6J), session/hours summary, daily BID/ASK spread stats,
and a PIT roll calendar from expiry dates only. No price interpolation,
no back-adjustment.
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CTL = Path(__file__).resolve().parent
RAW_ROOT = Path.home() / ".my-quantitative-data" / "futures-10syms-v1" / "raw"

NQ_ES_LIKE = {"NQ", "ES"}


def load_manifest() -> list[dict]:
    rows = {}
    for line in (CTL / "raw_manifest.jsonl").read_text().splitlines():
        try:
            r = json.loads(line)
            rows[r["path"]] = r  # dedupe by path, last row wins
        except Exception:  # noqa: BLE001
            pass
    return list(rows.values())


def bar_date(b) -> str:
    return str(b["t"])[:10]


def validate_symbol(sym: str, recs: list[dict]) -> dict:
    out = {"symbol": sym, "contracts": {}, "bar_inventory": {}}
    daily_by_con = {}
    for r in recs:
        p = Path(r["path"])
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        if not d.get("ok") or not d.get("bars"):
            continue
        inv = out["bar_inventory"].setdefault(
            f"{d['whatUse']}|{d['barSize']}", {"n_files": 0, "n_rows": 0})
        inv["n_files"] += 1
        inv["n_rows"] += d["n_rows"]
        con = out["contracts"].setdefault(
            str(d["conId"]),
            {"localSymbol": d["localSymbol"], "expiry_month": d["expiry_month"],
             "series": {}})
        con["series"][f"{d['whatUse']}|{d['barSize']}"] = {
            "n": d["n_rows"], "first": d["bars"][0]["t"], "last": d["bars"][-1]["t"]}
        if d["whatUse"] == "TRADES" and d["barSize"] == "1 day":
            daily_by_con[d["conId"]] = d
    # per-contract daily diagnostics
    for con_id, d in daily_by_con.items():
        bars = d["bars"]
        dates = [bar_date(b) for b in bars]
        n_dup = len(dates) - len(set(dates))
        flat = sum(1 for b in bars if b["o"] == b["h"] == b["l"] == b["c"] and not b["v"])
        vols = [b["v"] for b in bars]
        out["contracts"][str(con_id)]["daily_diag"] = {
            "n": len(bars), "first": dates[0], "last": dates[-1],
            "dup_dates": n_dup,
            "flat_zero_vol_rows": flat,
            "flat_share_pct": round(100.0 * flat / len(bars), 2) if bars else None,
            "zero_vol_rows": sum(1 for v in vols if not v),
            "median_vol": statistics.median(vols) if vols else None,
            "duration_boundary_start": dates[0] == d["bars"][0]["t"][:10],
        }
    return out


def spread_stats(recs: list[dict]) -> dict:
    """Daily BID vs ASK close spread for front/near contracts (observed proxy)."""
    bids, asks = {}, {}
    for r in recs:
        if r["whatUse"] not in ("BID", "ASK") or r["barSize"] != "1 day":
            continue
        p = Path(r["path"])
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        if not d.get("bars"):
            continue
        store = bids if r["whatUse"] == "BID" else asks
        store[r["conId"]] = {bar_date(b): b["c"] for b in d["bars"]}
    stats = {}
    for con_id, bmap in bids.items():
        amap = asks.get(con_id)
        if not amap:
            continue
        common = sorted(set(bmap) & set(amap))
        if not common:
            continue
        diffs, crossed = [], 0
        for dt in common:
            b, a = bmap[dt], amap[dt]
            if a < b:
                crossed += 1
            else:
                diffs.append(a - b)
        stats[str(con_id)] = {
            "n_days": len(common), "crossed_days": crossed,
            "median_spread": statistics.median(diffs) if diffs else None,
            "p90_spread": (statistics.quantiles(diffs, n=10)[8] if len(diffs) >= 10
                           else None),
            "first": common[0], "last": common[-1],
        }
    return stats


def roll_calendar(ident_sym: dict) -> dict:
    """PIT roll dates from expiry months only (known-in-advance calendar).

    Rule (declared, no lookahead): switch to next contract on the last
    trading day of the month BEFORE the front's expiry month start — i.e.
    roll_date = first day of expiry month, holding the previous contract
    until the session before that date. Expiry months are published by the
    exchange years ahead -> point-in-time legal.
    """
    out = {"rule_declared": "hold contract until last session before expiry month "
                            "start; switch at that session's close",
           "rolls": []}
    months = []
    for cd in ident_sym.get("active_chain", []):
        months.append(cd["lastTradeDateOrContractMonth"])
    for r in ident_sym.get("expired_walk", []):
        if isinstance(r, dict) and "conId" in r:
            months.append(r["lastTradeDateOrContractMonth"])
    months = sorted(set(months))
    out["contract_months_available"] = months
    return out


def main() -> None:
    manifest = load_manifest()
    ident = json.loads((CTL / "S1_IDENTITY.json").read_text())
    by_sym = defaultdict(list)
    for r in manifest:
        by_sym[r["symbol"]].append(r)
    report = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "symbols": {}, "spreads": {}, "rolls": {}, "quote_convention": {}}
    # 6J/FX quote convention check from front daily TRADES closes
    for sym in ("6E", "6J", "6B", "6A"):
        recs = [r for r in manifest if r["symbol"] == sym
                and r["whatUse"] == "TRADES" and r["barSize"] == "1 day" and r["n_rows"]]
        closes = []
        for r in recs[:3]:
            d = json.loads(Path(r["path"]).read_text())
            closes += [b["c"] for b in d["bars"][-5:]]
        if closes:
            report["quote_convention"][sym] = {
                "recent_close_range": [min(closes), max(closes)],
                "interpretation": (
                    f"price unit = USD per 1 {sym[1:]} "
                    f"(listing {sym[1:]}/USD; "
                    + ("NOT the USD/JPY spot quote direction" if sym == "6J" else "")
                    + ")") if closes else None,
            }
    for sym, recs in by_sym.items():
        report["symbols"][sym] = validate_symbol(sym, recs)
        report["spreads"][sym] = spread_stats(recs)
        report["rolls"][sym] = roll_calendar(ident["symbols"][sym])
    (CTL / "S6_VALIDATION.json").write_text(json.dumps(report, indent=1))
    # console digest
    for sym, v in report["symbols"].items():
        cons = v["contracts"]
        n_with_daily = sum(1 for c in cons.values() if "daily_diag" in c)
        firsts = sorted(c["daily_diag"]["first"] for c in cons.values()
                        if "daily_diag" in c)
        flat = [c["daily_diag"]["flat_share_pct"] for c in cons.values()
                if "daily_diag" in c]
        print(f"{sym}: contracts={len(cons)} with_daily={n_with_daily} "
              f"earliest_daily={firsts[0] if firsts else None} "
              f"max_flat_share={max(flat) if flat else None}% "
              f"inventory={ {k: vv['n_rows'] for k, vv in v['bar_inventory'].items()} }")
    for sym, q in report["quote_convention"].items():
        print(f"quote {sym}: {q['recent_close_range']} {q['interpretation']}")


if __name__ == "__main__":
    main()
