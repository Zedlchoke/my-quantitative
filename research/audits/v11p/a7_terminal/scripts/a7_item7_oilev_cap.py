"""A7-TERMINAL item 7: independent OILEV frozen-cap-breach recompute.

Loads bars/oi/funding/ticks from the EXEC tree staging with my own minimal
loader (pattern per committed research/audits/v11i/oilever_delev_scratch/
build_artifacts.py, paths substituted), instantiates the FROZEN
OileverDelevPlugin for the anchor arm, recomputes target books at ALL 52
frozen Monday stamps and measures max |weight| per stamp, then pushes each
book through the adapter's own normalise_target_book (cap 0.30) to prove the
fail-closed ContractViolation.
Read-only over the exec tree; emits JSON to stdout.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXEC = Path(r"C:\Users\ROYAL\my-quantitative\.worktrees\v11\exec-v11-1")
sys.path.insert(0, str(EXEC))

import pyarrow.parquet as pq  # noqa: E402

import research.adapter_v10  # noqa: F401,E402  (import-order contract)
from research.adapter_v10.converters import normalise_target_book  # noqa: E402
from research.adapter_v10.protocol import ContractViolation, DEFAULT_WEIGHT_CAP_MAX  # noqa: E402
from research.v11.families.oilever_delev import OileverDelevPlugin  # noqa: E402
from research.v11.families.oilever_delev import strategy as st  # noqa: E402

CATALOG = EXEC / "catalog_live_crypto"
OI_DIR = EXEC / "oi_data" / "consolidated"
FUNDING_DIR = EXEC / "funding_data" / "scan_2026"
SCALE = 10 ** 16
HOUR_NS = st.HOUR_NS


def load_bars(symbol: str):
    directory = CATALOG / "data" / "binance_bar" / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    table = pq.read_table(
        [str(p) for p in sorted(directory.rglob("*.parquet"))],
        columns=["ts_event", "open", "high", "low", "close", "quote_volume"],
    )
    ts = [int(v) for v in table.column("ts_event").to_pylist()]

    def px(col):
        return [float(int.from_bytes(v, "little", signed=True) / SCALE)
                for v in table.column(col).to_pylist()]

    qv = [float(v) for v in table.column("quote_volume").to_pylist()]
    return tuple(
        st.Bar(ts_event_ns=t, open=o, high=h, low=l, close=c, volume=0.0, quote_volume=q)
        for t, o, h, l, c, q in zip(ts, px("open"), px("high"), px("low"), px("close"), qv)
    )


def load_oi(symbol: str):
    frame = pq.read_table(str(OI_DIR / f"{symbol}_oi.parquet")).to_pylist()
    series = []
    for row in frame:
        moment = datetime.strptime(str(row["create_time"]), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc)
        series.append((int(moment.timestamp()) * 1_000_000_000, float(row["sum_open_interest"])))
    series.sort(key=lambda item: item[0])
    return tuple(series)


def load_settlements(symbol: str):
    payload = json.loads((FUNDING_DIR / symbol / "funding.json").read_text(encoding="utf-8"))
    rows = sorted(payload["rows"], key=lambda r: int(r["fundingTime"]))
    return tuple(
        __import__("research.adapter_v10.protocol", fromlist=["SettlementPoint"]).SettlementPoint(
            publish_ts_ns=int(r["fundingTime"]) * 1_000_000, value=float(r["fundingRate"]))
        for r in rows
    )


def load_tick_sizes():
    ticks = {}
    for directory in sorted((CATALOG / "data" / "crypto_perpetual").iterdir()):
        table = pq.read_table([str(p) for p in sorted(directory.rglob("*.parquet"))])
        row = table.to_pylist()[0]
        ticks[str(row["id"])] = float(row["price_increment"])
    return ticks


def main() -> None:
    from research.adapter_v10.protocol import SettlementPoint  # proper import

    symbols = sorted(p.name.split("_oi.parquet")[0] for p in OI_DIR.glob("*_oi.parquet"))
    assert len(symbols) == 20, symbols
    bars, oi, settles = {}, {}, {}
    for s in symbols:
        bars[s] = load_bars(s)
        oi[s] = load_oi(s)
        settles[s] = load_settlements(s)
    raw_ticks = load_tick_sizes()
    ticks = {s: raw_ticks[f"{s}-PERP.BINANCE"] for s in symbols}

    plugin = OileverDelevPlugin(
        arm_id=st.ANCHOR_ARM,
        bars_by_symbol=bars,
        oi_by_symbol=oi,
        settlements_by_symbol=settles,
        tick_sizes=ticks,
    )
    schedule = plugin.schedule()
    instants = list(schedule.instants)
    universe = plugin.tradeable_universe()
    stress = plugin.baseline_stress()

    rows = []
    for instant in instants:
        book = plugin.targets_at(int(instant), universe=universe, stress=stress)
        raw_w = book["weights"]
        if isinstance(raw_w, dict):
            pairs = list(raw_w.items())
        else:
            pairs = [(p[0], p[1]) for p in raw_w]
        max_abs = max(abs(w) for _, w in pairs)
        # fail-closed: adapter normalise must refuse the book at the frozen cap
        violated = None
        try:
            normalise_target_book(book, decision_ns=int(instant), cap_max=DEFAULT_WEIGHT_CAP_MAX)
        except ContractViolation as exc:
            violated = str(exc)
        rows.append({
            "stamp": st.iso_utc(int(instant)),
            "status": str(book["status"]),
            "n_eligible_dv": int(book["diagnostics"]["n_eligible_dv"]),
            "n_book_symbols": len(pairs),
            "max_abs_weight": max_abs,
            "exceeds_cap_030": max_abs > 0.30,
            "normalise_contract_violation": violated,
        })

    n_breach = sum(1 for r in rows if r["exceeds_cap_030"])
    n_viol = sum(1 for r in rows if r["normalise_contract_violation"] is not None)
    out = {
        "schema": "a7_terminal_item7_oilev_cap_recompute_v1",
        "exec_tree": str(EXEC),
        "frozen_cap": DEFAULT_WEIGHT_CAP_MAX,
        "family_cap_max_const": st.CAP_MAX,
        "n_stamps": len(rows),
        "n_status_ok": sum(1 for r in rows if r["status"] == "OK"),
        "n_eligible_dv_values": sorted({r["n_eligible_dv"] for r in rows}),
        "n_stamps_breach_030": n_breach,
        "n_stamps_normalise_violation": n_viol,
        "max_abs_weight_min": min(r["max_abs_weight"] for r in rows),
        "max_abs_weight_max": max(r["max_abs_weight"] for r in rows),
        "rows": rows,
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
