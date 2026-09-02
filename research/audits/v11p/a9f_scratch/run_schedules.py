"""D2-A9-F schedule-only feasibility runs through the frozen A3 gate.

Schedule proxies only: target books are built from a deterministic,
price-independent pseudo-characteristic (no returns, no PnL). Fill prices are
real staged bar closes (cost inputs only). All feasibility math is reused
verbatim from research.v11.cost_feasibility + research.adapter_v10.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/v11/d2-a9-feasibility")

import pyarrow.parquet as pq

from research.adapter_v10.protocol import CostModel, SettlementPoint
from research.v11.cost_feasibility import (
    ScheduleArtifacts,
    ScheduleDecision,
    SignalAvailability,
    evaluate_schedule_cost_feasibility,
)

CATALOG = Path("/Users/hoangminhlong/my-quantitative/catalog_live_crypto")
FUNDING = Path("/Users/hoangminhlong/my-quantitative/funding_data/scan_2026")
DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000
SCALE = 10**16

SCORED_END_NS = 1787270400 * 10**9  # 2026-08-21T00:00:00Z (verified epoch)
HIST = {"A5": 60, "A6": 90, "SEED": 90}  # required listing history (days)

# ---------------------------------------------------------------- loaders
def iso(ns: int) -> str:
    return datetime.fromtimestamp(int(ns) / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_symbol(name: str):
    d = CATALOG / "data" / "binance_bar" / f"{name}-15-MINUTE-LAST-EXTERNAL"
    t = pq.read_table([str(f) for f in sorted(d.rglob("*.parquet"))])
    ts = t.column("ts_event").to_pylist()
    close = [int.from_bytes(c, "little", signed=True) / SCALE for c in t.column("close").to_pylist()]
    qv = [float(v) for v in t.column("quote_volume").to_pylist()]
    return ts, close, qv


symbols = sorted(p.name.split("-15-MINUTE")[0] for p in (CATALOG / "data" / "binance_bar").iterdir())
BARS = {}  # sym -> (ts list, close list)
DAILY_DV = {}  # sym -> {day_ns: dollar_volume}
DAILY_CLOSE = {}  # sym -> {day_ns: last close}
FIRST_BAR = {}
for s in symbols:
    ts, close, qv = load_symbol(s)
    BARS[s] = (ts, close)
    FIRST_BAR[s] = min(ts)
    dv, dc = {}, {}
    for x, c, v in zip(ts, close, qv):
        day = (x // DAY_NS) * DAY_NS
        dv[day] = dv.get(day, 0.0) + v
        dc[day] = c  # bars ascending -> last write = day close
    DAILY_DV[s] = dv
    DAILY_CLOSE[s] = dc

TICK = {}
INST = {}
for p in (CATALOG / "data" / "crypto_perpetual").iterdir():
    t = pq.read_table([str(f) for f in sorted(p.rglob("*.parquet"))])
    row = t.to_pylist()[0]
    TICK[row["id"]] = float(row["price_increment"])
    INST[row["id"]] = row

SETTLE = {}
for p in sorted(FUNDING.iterdir()):
    if not (p / "funding.json").exists():
        continue
    j = json.load(open(p / "funding.json"))
    SETTLE[p.name + "-PERP.BINANCE"] = tuple(
        SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 1_000_000, value=float(r["fundingRate"]))
        for r in sorted(j["rows"], key=lambda r: int(r["fundingTime"]))
    )

COST = CostModel(taker_fee_bps=5.0, adverse_tick_slip_floor=1, default_tick_sizes=dict(TICK))


# ------------------------------------------------- PIT eligibility per instant
def eligible_at(instant_ns: int, hist_days: int):
    """Listed-with-history, actively-trading, and above PIT dollar-volume median."""
    hist_ns = hist_days * DAY_NS
    listed = [s for s in symbols if FIRST_BAR[s] <= instant_ns - hist_ns]
    active = []
    for s in listed:
        ts = BARS[s][0]
        # any bar close within the last 48h before the decision
        lo, hi = 0, len(ts)
        import bisect

        i = bisect.bisect_right(ts, instant_ns) - 1
        if i >= 0 and instant_ns - ts[i] <= 48 * 3600 * 10**9:
            active.append(s)
    med = {}
    for s in active:
        vals = [v for d, v in DAILY_DV[s].items() if instant_ns - 28 * DAY_NS < d <= instant_ns]
        med[s] = sorted(vals)[len(vals) // 2] if vals else 0.0
    if len(med) < 2:
        return active, active, 0.0
    medians = sorted(med.values())
    xsec = medians[len(medians) // 2]
    above = [s for s in active if med[s] > xsec]
    return active, above, xsec


def fill_price(instant_ns: int, s: str):
    ts, close = BARS[s]
    import bisect

    i = bisect.bisect_right(ts, instant_ns)
    if i < len(ts) and ts[i] - instant_ns <= DAY_NS:
        return close[i]
    return None


# ------------------------------------------------- deterministic book builder
def pseudo_ranks(instant_ns: int):
    """Deterministic, price-independent rank key per symbol (schedule proxy)."""
    t = instant_ns / DAY_NS
    out = {}
    for i, s in enumerate(symbols):
        out[s] = 0.6 * math.sin(2 * math.pi * (t / 173.0 + 0.11 * i)) + 0.4 * math.sin(
            2 * math.pi * t / 67.0 + 2.1 * i
        )
    return out


def build_book(instant_ns: int, elig: list[str], buckets: int):
    ranks = pseudo_ranks(instant_ns)
    ordered = sorted(elig, key=lambda s: (ranks[s], s), reverse=True)
    q = max(1, len(ordered) // buckets)
    long_leg, short_leg = ordered[:q], ordered[-q:]
    w = 0.5 / q  # gross 1.0, dollar-neutral; equals cap 1/(2*N_bucket)
    bk = {s: w for s in long_leg}
    bk.update({s: -w for s in short_leg})
    return bk


def weekly_mondays():
    import calendar

    out = []
    day0 = SCORED_END_NS - 365 * DAY_NS  # 2025-08-21
    t = day0
    while t <= SCORED_END_NS:
        wd = datetime.fromtimestamp(t / 1e9, tz=timezone.utc).weekday()
        if wd == 0:  # Monday
            out.append(t)
        t += DAY_NS
    return [t for t in out if t < SCORED_END_NS]


def monthly_28d():
    out = []
    t = SCORED_END_NS - 365 * DAY_NS + 5 * 60 * 10**9  # 00:05 UTC
    while t < SCORED_END_NS:
        out.append(t)
        t += 28 * DAY_NS
    return out


TERMINAL_NS = SCORED_END_NS + 5 * 60 * 10**9  # terminal force-flat 00:05Z at window end


def run_case(label: str, cadence: str, buckets: int, hist_key: str, min_names_per_leg: int, supply_availability: bool):
    instants = weekly_mondays() if cadence == "weekly" else monthly_28d()
    hist = HIST[hist_key]
    decisions = {}
    fills = {}
    availability = {}
    elig_log = []
    missing_fills = []
    all_inst = list(instants) + [TERMINAL_NS]
    prev_book_syms: set[str] = set()
    for t in all_inst:
        if t == TERMINAL_NS:
            decisions[t] = ScheduleDecision(instant_ns=t, kind="FORCED_FLAT", weights={})
            if supply_availability:
                availability[t] = SignalAvailability(instant_ns=t, available=True, missing_symbols=())
            fp = {}
            for s in prev_book_syms:
                pr = fill_price(t, s)
                if pr is not None:
                    fp[s] = pr
                else:
                    missing_fills.append((iso(t), s, int(t)))
            fills[t] = fp
            prev_book_syms = set()
            continue
        active, above, xsec = eligible_at(t, hist)
        elig_log.append({"instant_ns": t, "instant": iso(t), "active": len(active), "above_median": len(above)})
        q = max(1, len(above) // buckets)
        ok = len(above) >= 2 * min_names_per_leg
        if supply_availability:
            availability[t] = SignalAvailability(instant_ns=t, available=ok, missing_symbols=())
        bk = build_book(t, above, buckets) if ok else {}
        decisions[t] = ScheduleDecision(instant_ns=t, kind="DISCRETIONARY", weights=bk)
        fp = {}
        for s in set(bk) | prev_book_syms:
            pr = fill_price(t, s)
            if pr is not None:
                fp[s] = pr
            else:
                missing_fills.append((iso(t), s, int(t)))
        fills[t] = fp
        prev_book_syms = set(bk)
    arts = ScheduleArtifacts(
        instants_ns=all_inst,
        decisions=decisions,
        fill_prices=fills,
        settlements=SETTLE,
        cost_model=COST,
        signal_availability=availability if supply_availability else None,
        source=f"a9f_schedule_proxy:{label}",
    )
    rep = evaluate_schedule_cost_feasibility(arts)
    counts = [e["above_median"] for e in elig_log]
    return {
        "label": label,
        "cadence": cadence,
        "buckets": buckets,
        "history_days": hist,
        "verdict": rep.payload["verdict"],
        "n_discretionary": rep.payload["metrics"]["discretionary_decision_count"]["value"],
        "n_forced_flat": rep.payload["metrics"]["forced_flat_decision_count"]["value"],
        "decisions_per_365d": rep.payload["metrics"]["decisions_per_365d"]["value"],
        "median_holding_d": rep.payload["metrics"]["median_intended_holding_days"]["value"],
        "base_drag": rep.payload["metrics"]["annualised_base_cost_drag_frac_of_gross"]["value"],
        "stressed_drag": rep.payload["metrics"]["annualised_stressed_cost_drag_frac_of_gross"]["value"],
        "max_sym_share": rep.payload["metrics"]["max_symbol_turnover_share"]["value"],
        "max_sym_share_symbol": rep.payload["metrics"].get("max_symbol_turnover_share_symbol", {}).get("value"),
        "funding_events_365d": rep.payload["metrics"]["funding_events_per_365d"]["value"],
        "floors": [
            {"floor_id": f["floor_id"], "status": f["status"], "observed": f["observed"]}
            for f in rep.payload["floors"]
        ],
        "unavailable_metrics": rep.payload["unavailable_metrics"],
        "eligibility_min_above_median": min(counts),
        "eligibility_median_above_median": sorted(counts)[len(counts) // 2],
        "eligibility_max_above_median": max(counts),
        "eligibility_per_decision": elig_log,
        "missing_fills": missing_fills[:40],
        "missing_fill_count": len(missing_fills),
        "schedule_sha256": rep.payload["schedule_sha256"],
        "metric_reasons": {
            k: m.get("reason") for k, m in rep.payload["metrics"].items() if m["status"] != "OK"
        },
    }


CASES = [
    ("a5_prop1_V11-A5-ILLIQ-PREMIUM", "weekly", 5, "A5", 1, True),
    ("a5_prop2_V11-A5-OI-HEDGEPRESSURE", "weekly", 3, "A5", 1, False),
    ("a6_prop1_V11-A6-ILLIQUIDITY-PREMIUM", "monthly28d", 3, "A6", 6, True),
    ("a6_prop2_V11-A6-POSITIONING-SATURATION", "monthly28d", 3, "A6", 6, False),
    ("a8_prop1_A8-V11-ILLIQ-AMIHUD", "weekly", 5, "A5", 1, True),
    ("a8_prop2_A8-V11-OILEVER-DELEV", "weekly", 5, "A5", 1, False),
    ("seed_defensive_residual_risk", "weekly", 5, "SEED", 1, True),
    ("seed_lottery_max_skew", "weekly", 5, "SEED", 1, True),
]

out = {"cases": [], "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
for label, cad, bk, hk, mpl, sa in CASES:
    r = run_case(label, cad, bk, hk, mpl, sa)
    r["note"] = (
        "schedule proxy: books built from a deterministic price-independent pseudo-characteristic; "
        "no scored return computed anywhere"
    )
    out["cases"].append(r)
    print(label, "->", r["verdict"], "base", r["base_drag"], "stress", r["stressed_drag"], "medhold", r["median_holding_d"], "maxshare", r["max_sym_share"], "elig[min/med/max]", r["eligibility_min_above_median"], r["eligibility_median_above_median"], r["eligibility_max_above_median"], "unavail", len(r["unavailable_metrics"]))

# also run OI-lane schedules WITH availability supplied, to isolate schedule-only floors from data absence
for label, cad, bk, hk, mpl in [
    ("a5_prop2_scheduleonly", "weekly", 3, "A5", 1),
    ("a6_prop2_scheduleonly", "monthly28d", 3, "A6", 6),
    ("a8_prop2_scheduleonly", "weekly", 5, "A5", 1),
]:
    r = run_case(label, cad, bk, hk, mpl, True)
    r["note"] = "counterfactual schedule-only run (availability supplied) to separate schedule floors from OI data absence"
    out["cases"].append(r)
    print(label, "->", r["verdict"], "base", r["base_drag"], "stress", r["stressed_drag"])

for label, cad, bk, hk, mpl in [
    ("a6_prop1_breadth_relaxed_min1", "monthly28d", 3, "A6", 1),
    ("a6_prop2_breadth_relaxed_min1", "monthly28d", 3, "A6", 1),
]:
    r = run_case(label, cad, bk, hk, mpl, True)
    r["note"] = (
        "counterfactual breadth-relaxed proxy (min 1 name/leg instead of the proposal's fail-closed "
        "min 6/leg); NOT a waiver -- shows whether the schedule floors alone would pass"
    )
    out["cases"].append(r)
    print(label, "->", r["verdict"], "base", r["base_drag"], "stress", r["stressed_drag"], "medhold", r["median_holding_d"])

json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
print("written", sys.argv[1])
