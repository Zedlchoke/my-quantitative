"""D2b-A9-F: weekly OI-book schedule-only floors through the FROZEN A3 gate.

Proxy methodology reused verbatim from the prior audit (d2-a9-feasibility
a9f_scratch/run_schedules.py): weekly Monday 00:00Z decisions over the
candidate scored window, quintile book from a deterministic price-independent
pseudo-characteristic on the DV-above-median eligible set, gross 1.0
dollar-neutral, weights 0.5/q, real staged 15m closes as fill-price cost
inputs only, terminal FORCED_FLAT at 2026-08-21T00:05Z. Signal availability
is now SUPPLIED from the staged OI feature (data exists): available at every
stamp where the 28d log OI-growth + trailing-28d return are computable
(re-audit measurement: 52/52 stamps, 20/20 symbols). NO scored return, PnL,
factor or ranking exists in this run.
"""
from __future__ import annotations

import bisect
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/v11/d2b-a9f-oireaudit")
WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/v11/d2b-a9f-oireaudit")
sys.path.insert(0, str(WT))

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
SCALE = 10**16

SCORED_END_NS = 1787270400 * 10**9  # 2026-08-21T00:00:00Z (same as prior audit)
HIST_DAYS = 60  # a8_prop2 declared listing history (same as prior audit)
BUCKETS = 5     # a8_prop2 quintile book (same as prior audit)

t_start = time.time()


def iso(ns: int) -> str:
    return datetime.fromtimestamp(int(ns) / 1e9, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_symbol(name: str):
    d = CATALOG / "data" / "binance_bar" / f"{name}-15-MINUTE-LAST-EXTERNAL"
    t = pq.read_table([str(f) for f in sorted(d.rglob("*.parquet"))], columns=["ts_event", "close", "quote_volume"])
    ts = t.column("ts_event").to_pylist()
    close = [int.from_bytes(c, "little", signed=True) / SCALE for c in t.column("close").to_pylist()]
    qv = [float(v) for v in t.column("quote_volume").to_pylist()]
    return ts, close, qv


symbols = sorted(p.name.split("-15-MINUTE")[0] for p in (CATALOG / "data" / "binance_bar").iterdir())
BARS, DAILY_DV, FIRST_BAR = {}, {}, {}
for s in symbols:
    ts, close, qv = load_symbol(s)
    BARS[s] = (ts, close)
    FIRST_BAR[s] = min(ts)
    dv = {}
    for x, v in zip(ts, qv):
        day = (x // DAY_NS) * DAY_NS
        dv[day] = dv.get(day, 0.0) + v
    DAILY_DV[s] = dv

TICK = {}
for p in (CATALOG / "data" / "crypto_perpetual").iterdir():
    t = pq.read_table([str(f) for f in sorted(p.rglob("*.parquet"))])
    row = t.to_pylist()[0]
    TICK[row["id"]] = float(row["price_increment"])

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


def eligible_at(instant_ns: int, hist_days: int):
    """Identical PIT rule to the prior audit: listed+history, active 48h, DV strictly above x-sec median."""
    hist_ns = hist_days * DAY_NS
    listed = [s for s in symbols if FIRST_BAR[s] <= instant_ns - hist_ns]
    active = []
    for s in listed:
        ts = BARS[s][0]
        i = bisect.bisect_right(ts, instant_ns) - 1
        if i >= 0 and instant_ns - ts[i] <= 48 * 3600 * 10**9:
            active.append(s)
    med = {}
    for s in active:
        vals = [v for d, v in DAILY_DV[s].items() if instant_ns - 28 * DAY_NS < d <= instant_ns]
        med[s] = sorted(vals)[len(vals) // 2] if vals else 0.0
    if len(med) < 2:
        return active, active
    medians = sorted(med.values())
    xsec = medians[len(medians) // 2]
    above = [s for s in active if med[s] > xsec]
    return active, above


def fill_price(instant_ns: int, s: str):
    ts, close = BARS[s]
    i = bisect.bisect_right(ts, instant_ns)  # first completed bar strictly AFTER the decision
    if i < len(ts) and ts[i] - instant_ns <= DAY_NS:
        return close[i]
    return None


def pseudo_ranks(instant_ns: int):
    """Verbatim deterministic price-independent rank key from the prior audit."""
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
    w = 0.5 / q
    bk = {s: w for s in long_leg}
    bk.update({s: -w for s in short_leg})
    return bk


def weekly_mondays():
    out = []
    t = SCORED_END_NS - 365 * DAY_NS
    while t <= SCORED_END_NS:
        if datetime.fromtimestamp(t / 1e9, tz=timezone.utc).weekday() == 0:
            out.append(t)
        t += DAY_NS
    return [t for t in out if t < SCORED_END_NS]


TERMINAL_NS = SCORED_END_NS + 5 * 60 * 10**9

# --- OI-feature availability measured by this re-audit (scratch/feature_feasibility.json) ---
ff = json.load(open(WT / "research/audits/v11p/a9f2_scratch/feature_feasibility.json"))
FEAT_ELIG = {p["stamp"]: p["eligible"] for p in ff["per_stamp"]}


def stamp_ns(iso_s: str) -> int:
    return int(datetime.strptime(iso_s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc).timestamp() * 1e9)


instants = weekly_mondays()
decisions, fills, availability, elig_log, missing_fills = {}, {}, {}, [], []
all_inst = list(instants) + [TERMINAL_NS]
prev_book_syms: set[str] = set()
for t in all_inst:
    if t == TERMINAL_NS:
        decisions[t] = ScheduleDecision(instant_ns=t, kind="FORCED_FLAT", weights={})
        availability[t] = SignalAvailability(instant_ns=t, available=True, missing_symbols=())
        fp = {}
        for s in prev_book_syms:
            pr = fill_price(t, s)
            fp[s] = pr if pr is not None else 0.0
            if pr is None:
                missing_fills.append((iso(t), s))
        fills[t] = fp
        prev_book_syms = set()
        continue
    active, above = eligible_at(t, HIST_DAYS)
    # map stamp -> OI-feature eligible count by exact instant
    feat_count = None
    for p in ff["per_stamp"]:
        if stamp_ns(p["stamp"]) == t:
            feat_count = p["eligible"]
            break
    avail = feat_count is not None and feat_count >= 2
    availability[t] = SignalAvailability(instant_ns=t, available=avail, missing_symbols=())
    elig_log.append({"instant": iso(t), "active": len(active), "above_median": len(above),
                     "oi_feature_eligible": feat_count})
    bk = build_book(t, above, BUCKETS)
    decisions[t] = ScheduleDecision(instant_ns=t, kind="DISCRETIONARY", weights=bk)
    fp = {}
    for s in set(bk) | prev_book_syms:
        pr = fill_price(t, s)
        if pr is not None:
            fp[s] = pr
        else:
            missing_fills.append((iso(t), s))
    fills[t] = fp
    prev_book_syms = set(bk)

arts = ScheduleArtifacts(
    instants_ns=all_inst,
    decisions=decisions,
    fill_prices=fills,
    settlements=SETTLE,
    cost_model=COST,
    signal_availability=availability,
    source="a9f2_oi_reaudit:a8_prop2_weekly_oi_book_schedule_proxy",
)
rep = evaluate_schedule_cost_feasibility(arts)
payload = rep.payload
counts = [e["above_median"] for e in elig_log]
feat_counts = [e["oi_feature_eligible"] for e in elig_log]

result = {
    "label": "a8_prop2_A8-V11-OILEVER-DELEV_oi_weekly_schedule_proxy",
    "frozen_gate_module": "research.v11.cost_feasibility.evaluate_schedule_cost_feasibility (imported, not forked)",
    "cadence": "weekly_monday_0000Z",
    "buckets": BUCKETS,
    "history_days": HIST_DAYS,
    "gate_verdict": payload["verdict"],
    "discretionary_decisions": payload["metrics"]["discretionary_decision_count"]["value"],
    "forced_flat_decisions": payload["metrics"]["forced_flat_decision_count"]["value"],
    "decisions_per_365d": payload["metrics"]["decisions_per_365d"]["value"],
    "median_intended_holding_days": payload["metrics"]["median_intended_holding_days"]["value"],
    "annualised_base_cost_drag_frac_of_gross": payload["metrics"]["annualised_base_cost_drag_frac_of_gross"]["value"],
    "annualised_stressed_cost_drag_frac_of_gross": payload["metrics"]["annualised_stressed_cost_drag_frac_of_gross"]["value"],
    "max_symbol_turnover_share": payload["metrics"]["max_symbol_turnover_share"]["value"],
    "max_symbol_turnover_share_symbol": payload["metrics"]["max_symbol_turnover_share_symbol"]["value"],
    "signal_availability_fraction": payload["metrics"]["signal_availability_fraction"]["value"],
    "floors": [
        {"floor_id": f["floor_id"], "status": f["status"], "observed": f["observed"],
         "frozen_threshold": f["frozen_threshold"]}
        for f in payload["floors"]
    ],
    "unavailable_metrics": payload["unavailable_metrics"],
    "eligibility_above_median_min_median_max": [min(counts), sorted(counts)[len(counts) // 2], max(counts)],
    "oi_feature_eligible_min_median_max": [min(feat_counts), sorted(feat_counts)[len(feat_counts) // 2], max(feat_counts)],
    "missing_fill_count": len(missing_fills),
    "schedule_sha256": payload["schedule_sha256"],
    "wall_s": round(time.time() - t_start, 2),
    "note": "schedule proxy: books from deterministic price-independent pseudo-characteristic; availability from staged OI feature existence; no scored return computed anywhere",
}
json.dump({"case": result, "eligibility_per_decision": elig_log},
          open(WT / "research/audits/v11p/a9f2_scratch/schedule_gate_oi.json", "w"), indent=1)
print(json.dumps(result, indent=1))
