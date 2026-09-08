"""CRYPTO-V17 P0 mandatory self-audit: daily derived from H1 must reconcile
against V16's sha-pinned daily panel (BTC 5bb5016d..., ETH c5414767...).

Frozen rules live in p0_freeze_v17.json (reconciliation section):
- verify the V16 panel bytes against the V16 staging manifest pins FIRST;
- 14 exactly-decomposable fields reconciled with frozen tolerances;
- 8 retention/percentile fields + 2 bookkeeping fields on the frozen exclusion
  list (cannot be derived from bounded hourly sums - that is the point);
- any mismatch beyond tolerance = RECONCILE_FAIL = P0 blocker (BLOCKED_DATA).

Usage:
  python reconcile_v17_daily.py [--h1-dir v17_data/staging_v17] [--out PATH]
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[4]
FREEZE = WORKTREE / "research" / "control" / "v17_run" / "p0_freeze_v17.json"
V16_PANEL_DIR = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/"
                     "v16/integration/v16_data/staging_v16")
V16_MANIFEST = (Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/"
                     "v16/integration/research/control/v16_run/staging/"
                     "panel_manifest.json"))
CHUNK = 8 * 1024 * 1024

EXPECTED_DAYS = 365


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def derive_daily(symbol: str, h1_csv: Path) -> list[dict]:
    """Fold H1 rows into V16-daily-schema rows (reconciled fields only)."""
    by_day = defaultdict(list)
    with open(h1_csv) as fh:
        for row in csv.DictReader(fh):
            by_day[row["day_utc"]].append(row)
    out = []
    for day in sorted(by_day):
        rows = by_day[day]
        trade_count = sum(int(r["n_trades"]) for r in rows)
        total_qty = sum(float(r["qty_total"]) for r in rows)
        total_notional = sum(float(r["quote_total"]) for r in rows)
        buy_qty = sum(float(r["buy_qty"]) for r in rows)
        sell_qty = sum(float(r["sell_qty"]) for r in rows)
        gap_sum = sum(float(r["gap_sum_s"]) for r in rows)
        gap_n = sum(int(r["gap_count"]) for r in rows)
        # entry gaps count toward a day only when the previous kept row was in
        # the SAME day (V16's daily gap list = consecutive kept-row pairs with
        # the day; cross-midnight gaps belong to no day)
        prev = None
        for r in rows:
            if prev is not None and prev["day_utc"] == r["day_utc"]:
                gap_sum += float(r["entry_gap_s"])
                gap_n += 1
            prev = r
        traded = [r for r in rows if r["n_trades"] != "0"]
        b, s = buy_qty, sell_qty
        out.append({
            "date": day,
            "trade_count": trade_count,
            "total_qty": total_qty,
            "total_notional": total_notional,
            "buy_qty": buy_qty,
            "sell_qty": sell_qty,
            "flow_imbalance": (b - s) / (b + s) if (b + s) else 0.0,
            "vwap": total_notional / total_qty if total_qty else 0.0,
            "last_price": float(rows[-1]["last_price"]),
            "high_price": max(float(r["high_price"]) for r in traded),
            "low_price": min(float(r["low_price"]) for r in traded),
            "avg_trade_size": total_qty / trade_count if trade_count else 0.0,
            "interarrival_mean_s": gap_sum / gap_n if gap_n else 0.0,
            "first_ts_ms": int(rows[0]["first_ts_ms"]),
            "last_ts_ms": int(rows[-1]["last_ts_ms"]),
        })
    return out


def within(diff: float, tol: dict, ref: float) -> tuple[bool, float]:
    """Return (pass, margin) with margin = distance to the NEAREST failing edge
    (P-2: a pass must say how close it is; margin <= 0 means fail).
    rel tolerance anchors on |ref| = |the V16 value|."""
    margins = []
    if "abs" in tol:
        margins.append(tol["abs"] - abs(diff))
    if "rel" in tol:
        margins.append(tol["rel"] * abs(ref) - abs(diff))
    return (min(margins) > 0 if margins else False,
            round(min(margins), 12) if margins else -1.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h1-dir", default="v17_data/staging_v17")
    ap.add_argument("--out",
                    default="research/control/v17_run/staging/reconcile_v17_daily.json")
    args = ap.parse_args()
    freeze = json.loads(FREEZE.read_text())
    recon = freeze["reconciliation"]
    symbols = recon["symbols"]
    h1_dir = WORKTREE / args.h1_dir

    # step 1: verify V16 panel bytes against V16's own manifest pins
    v16_manifest = json.loads(V16_MANIFEST.read_text())
    pin_results = {}
    for sym in symbols:
        want = v16_manifest["panel_sha256"][sym]
        got = sha256_file(V16_PANEL_DIR / f"panel_{sym}_daily.csv")
        pin_results[sym] = {"pinned": want, "recomputed": got,
                            "match": want == got}
    pins_ok = all(v["match"] for v in pin_results.values())

    # step 2+3: derive daily from H1 and compare under frozen tolerances
    report = {"schema": "v17_run_artifact_v1", "artifact": "reconcile_v17_daily",
              "freeze_sha256": sha256_file(FREEZE),
              "v16_panel_pins": pin_results, "v16_pins_ok": pins_ok,
              "symbols": {}, "verdict": None}
    fail = not pins_ok
    for sym in symbols:
        derived = derive_daily(sym, h1_dir / f"panel_{sym}_h1.csv")
        with open(V16_PANEL_DIR / f"panel_{sym}_daily.csv") as fh:
            v16 = {r["date"]: r for r in csv.DictReader(fh)}
        days_derived = {r["date"] for r in derived}
        day_set_ok = days_derived == set(v16)
        field_stats = {}
        for r in derived:
            v = v16.get(r["date"])
            if v is None:
                continue
            for field, tol in recon["field_tolerances"].items():
                kind = tol.get("type", "float")
                if kind == "int":
                    mine, theirs = int(r[field]), int(v[field])
                    ok, margin = (mine == theirs,
                                  -1.0 if mine != theirs else 0.0)
                    diff = 0.0 if ok else float("inf")
                elif kind == "exact_float":
                    mine, theirs = float(r[field]), float(v[field])
                    ok, margin = (mine == theirs,
                                  -1.0 if mine != theirs else 0.0)
                    diff = 0.0 if ok else float("inf")
                else:
                    mine = float(r[field])
                    theirs = float(v[field])
                    diff = mine - theirs
                    ok, margin = within(diff, tol, theirs)
                st = field_stats.setdefault(field, {"max_abs_diff": 0.0,
                                                    "worst_day": None,
                                                    "fails": 0})
                if abs(diff) > st["max_abs_diff"]:
                    st["max_abs_diff"] = abs(diff)
                    st["worst_day"] = r["date"]
                if not ok:
                    st["fails"] += 1
                    fail = True
        report["symbols"][sym] = {
            "days_v16": len(v16), "days_derived": len(derived),
            "expected_days": EXPECTED_DAYS,
            "day_set_match": day_set_ok,
            "days_ok": len(v16) == EXPECTED_DAYS == len(derived) and day_set_ok,
            "fields": {k: {**v, "tolerance": recon["field_tolerances"][k],
                           "fail": v["fails"] > 0}
                       for k, v in field_stats.items()}}
        if not day_set_ok or not (len(v16) == EXPECTED_DAYS == len(derived)):
            fail = True
    report["reconciled_field_count"] = len(recon["field_tolerances"])
    report["excluded_fields"] = recon["excluded_fields_cannot_be_derived_from_bounded_h1"]
    report["verdict"] = "RECONCILE_FAIL_P0_BLOCKER" if fail else "RECONCILE_PASS"
    out = WORKTREE / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(f"{report['verdict']} -> {out}")
    for sym, s in report["symbols"].items():
        worst = max(s["fields"].items(), key=lambda kv: -kv[1]["max_abs_diff"])
        print(f"  {sym}: days {s['days_derived']}/{s['days_v16']} "
              f"set_match={s['day_set_match']} "
              f"worst-field {worst[0]} max|diff|={worst[1]['max_abs_diff']:.3g}")
    raise SystemExit(1 if fail else 0)


if __name__ == "__main__":
    main()
