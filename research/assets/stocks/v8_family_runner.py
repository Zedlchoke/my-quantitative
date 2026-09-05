"""V8 shared family runner for the two selected fundamentals families
(SFV8-F1 WC accrual-flow, SFV8-F2 depreciation-reserve coverage).

Implements the frozen proposal specs literally:
  - multi-vintage PIT as-of selection: newest filed vintage with
    avail_date < decision_date (availability stamp = end of filed UTC day,
    gate = 00:00 UTC of the decision session) and age <= clock bound;
    NEVER the latest vintage in the store (V6 canonical semantics).
  - P3 eligibility floor at each decision: panel filer + price file +
    ADV63 >= 2_000_000 USD (band C or better) + RAW close >= 1.00.
  - sector-neutral tercile books with one-decile retention hysteresis;
    sectors with fewer than 6 ranked names abstain that decision.
  - fills at the next session close after the decision (no same-session
    fill), returns on the ADJUSTED series (RAW series is primary for
    eligibility, bands and the price floor - V6 corporate-actions policy).
  - liquidity-band cost model per p3_invariants_freeze.json v8_additions,
    charged exactly once per fill on traded notional, stress = 2x.
  - folds forced flat at boundaries; per-decision and per-fold accounting.

OUTCOME DISCIPLINE: run(arm_spec, dry_run=True) computes structure only
(decisions, population, fills) and NEVER computes or prints PnL/metrics;
scored=True is gated by the owner GO phrase passed explicitly on the
command line. This keeps controller and auditors outcome-blind until
scored execution is authorized.
"""

import hashlib
import json
import os
import statistics

ROOT = os.environ.get("V8_WT_ROOT", ".")
PANEL = f"{ROOT}/.staging_sec_v8/multivintage_panel.jsonl"
PRICES = f"{ROOT}/.staging_prices_v8/eod"
BENCH = f"{ROOT}/.staging_prices_v8/benchmarks"
GO_PHRASE = "GO STOCKS V8 SCORED EXECUTION"

FOLDS = [
    {"fold_id": "S0_FOLD_1", "start": "2018-04-04", "end": "2020-09-01"},
    {"fold_id": "S0_FOLD_2", "start": "2020-09-10", "end": "2023-02-09"},
    {"fold_id": "S0_FOLD_3", "start": "2023-02-17", "end": "2025-07-24"},
]
BAND_BPS = {"A": 10.0, "B": 15.0, "C": 25.0}
GRID_START = 63
GRID_STEP = 21
MIN_SECTOR_NAMES = 6
TERCILE = 1.0 / 3.0
HYSTERESIS = 0.10

ARM_SPECS = {
    "SFV8-F1-ANCHOR": {
        "family": "SFV8-F1-WC-ACCRUAL-FLOW",
        "kind": "accrual_flow",
        "numerator_fields": ["us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet", "us-gaap:AccountsPayableCurrent"],
        "denominator_field": "us-gaap:Assets",
        "denominator_age": 400,
        "direction": "low_long",
        "warmup_decisions": 4,
    },
    "SFV8-F1-NEIGHBOUR": {
        "family": "SFV8-F1-WC-ACCRUAL-FLOW",
        "kind": "ratio_level",
        "numerator_fields": ["us-gaap:AllowanceForDoubtfulAccountsReceivableCurrent"],
        "denominator_field": "us-gaap:AccountsReceivableNetCurrent",
        "denominator_age": None,
        "direction": "high_long",
        "warmup_decisions": 4,
    },
    "SFV8-F1-CONTROL": {
        "family": "SFV8-F1-WC-ACCRUAL-FLOW",
        "kind": "wc_stock",
        "numerator_fields": ["us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet", "us-gaap:AccountsPayableCurrent"],
        "denominator_field": "us-gaap:Assets",
        "denominator_age": 400,
        "direction": "low_long",
        "warmup_decisions": 4,
    },
    "SFV8-F2-ANCHOR": {
        "family": "SFV8-F2-DEP-RESERVE-COVERAGE",
        "kind": "ratio_level",
        "numerator_fields": ["us-gaap:AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment"],
        "denominator_field": "us-gaap:PropertyPlantAndEquipmentGross",
        "denominator_age": 400,
        "direction": "high_long",
        "warmup_decisions": 0,
    },
    "SFV8-F2-NEIGHBOUR": {
        "family": "SFV8-F2-DEP-RESERVE-COVERAGE",
        "kind": "ratio_level",
        "numerator_fields": ["us-gaap:UnrecognizedTaxBenefits"],
        "denominator_field": "us-gaap:Assets",
        "denominator_age": 400,
        "direction": "high_long",
        "warmup_decisions": 0,
    },
    "SFV8-F2-CONTROL": {
        "family": "SFV8-F2-DEP-RESERVE-COVERAGE",
        "kind": "ratio_level",
        "numerator_fields": ["us-gaap:Goodwill"],
        "denominator_field": "us-gaap:Assets",
        "denominator_age": 400,
        "direction": "high_long",
        "warmup_decisions": 0,
    },
}


# ---------------------------------------------------------------- data

def load_panel(fields, unit="USD"):
    """Stream the panel; keep only wanted fields. unit="USD" (the frozen
    specs form ratios/deltas only from USD-stamped vintages - F-A7-3
    remediation) drops non-matching rows at load, fail-visible via the
    returned row counts."""
    want = set(fields)
    out = {}
    with open(PANEL) as f:
        for line in f:
            r = json.loads(line)
            fld = r["f"]
            if fld not in want:
                continue
            if unit is not None and r.get("u") != unit:
                continue
            e = out.setdefault(r["e"], {"sector": r["s"], "rows": {}})
            if r["v"] is None:
                continue
            e["rows"].setdefault(fld, []).append((r["avail"], r["eff"], r["v"]))
    for e in out.values():
        for fld in e["rows"]:
            e["rows"][fld].sort()
    return out


def load_prices():
    """{entity: {"date", "raw", "adj", "dvol", "pos"}} sorted by date.
    pos maps each date to ITS OWN array index (never a global calendar
    index - the F-A7-1 remediation)."""
    out = {}
    for fn in sorted(os.listdir(PRICES)):
        if not fn.endswith(".json"):
            continue
        cik = fn.split("__")[0]
        bars = json.load(open(f"{PRICES}/{fn}"))
        dates = [b["date"] for b in bars]
        out[cik] = {
            "date": dates,
            "raw": [float(b["close"]) for b in bars],
            "adj": [float(b["adjusted_close"]) for b in bars],
            "dvol": [float(b["close"]) * float(b["volume"]) for b in bars],
            "pos": {d: i for i, d in enumerate(dates)},
        }
    return out


def asof(rows, decision_date, age_days=None):
    """Newest filed vintage with avail < decision_date and age <= bound.
    Scans every row (order-independent; load_panel sorts anyway)."""
    from datetime import date
    best = None
    for avail, eff, v in rows:
        if avail >= decision_date:
            continue
        if age_days is not None:
            if (date.fromisoformat(decision_date) - date.fromisoformat(avail)).days > age_days:
                continue
        if best is None or (avail, eff) > (best[0], best[1]):
            best = (avail, eff, v)
    return best


# ------------------------------------------------------------ schedule

def fold_sessions(prices):
    """Market session set = the union of all bars' dates (observed calendar);
    returns per-fold ordered session lists within [start, end]."""
    days = set()
    for p in prices.values():
        days.update(p["date"])
    all_days = sorted(days)
    folds = []
    for f in FOLDS:
        sess = [d for d in all_days if f["start"] <= d <= f["end"]]
        folds.append({"fold_id": f["fold_id"], "sessions": sess})
    return folds


def decision_grid(fold_sess):
    """Per-fold local indices 63+21k, strictly inside the fold."""
    idx = list(range(GRID_START, len(fold_sess), GRID_STEP))
    return [fold_sess[i] for i in idx], idx


# ------------------------------------------------------------- signals

def _num(names, vals):
    return float(sum(vals)) if all(isinstance(v, (int, float)) for v in vals) else None


def signal_value(spec, panel_entity, decision_date, prev_session_date):
    """Arm signal for one name at one decision; None when unpopulated.
    prev_session_date = the session ~252 sessions before the decision
    (the t-1y evaluation point for flow arms; None for level arms)."""
    rows = panel_entity["rows"]
    f0 = spec["numerator_fields"][0]
    if spec["kind"] == "accrual_flow":
        f1, f2 = spec["numerator_fields"][1], spec["numerator_fields"][2]
        # an entity lacking a USD vintage for a field is simply unpopulated
        if any(f not in rows for f in (f0, f1, f2, spec["denominator_field"])):
            return None
        ar0 = asof(rows[f0], decision_date)
        inv0 = None if spec.get("drop_leg_index") == 1 else asof(rows[f1], decision_date)
        ap0 = asof(rows[f2], decision_date)
        if prev_session_date is None:
            return None
        ar1 = asof(rows[f0], prev_session_date)
        inv1 = None if spec.get("drop_leg_index") == 1 else asof(rows[f1], prev_session_date)
        ap1 = asof(rows[f2], prev_session_date)
        legs0 = (ar0, inv0, ap0)
        legs1 = (ar1, inv1, ap1)
        if any(l is None for l in legs0) or any(l is None for l in legs1):
            return None
        den = asof(rows[spec["denominator_field"]], decision_date, spec["denominator_age"])
        if den is None or not den[2]:
            return None
        # fiscal-type match: EACH field's two leg vintages must be
        # 330-400 eff days apart (F-A7-7 remediation: per field, not AR only)
        from datetime import date
        pairs = [(ar0, ar1)]
        if inv0 is not None and inv1 is not None:
            pairs.append((inv0, inv1))
        pairs.append((ap0, ap1))
        for leg0, leg1 in pairs:
            gap = (date.fromisoformat(leg0[1]) - date.fromisoformat(leg1[1])).days
            if not (330 <= gap <= 400):
                return None
        num = (ar0[2] - ar1[2])
        if inv0 is not None and inv1 is not None:
            num += inv0[2] - inv1[2]
        num -= (ap0[2] - ap1[2])
        try:
            return num / float(den[2])
        except (TypeError, ZeroDivisionError):
            return None
    if spec["kind"] == "wc_stock":
        f1, f2 = spec["numerator_fields"][1], spec["numerator_fields"][2]
        if any(f not in rows for f in (f0, f1, f2, spec["denominator_field"])):
            return None
        ar = asof(rows[f0], decision_date)
        inv = asof(rows[f1], decision_date)
        ap = asof(rows[f2], decision_date)
        if ar is None or inv is None or ap is None:
            return None
        den = asof(rows[spec["denominator_field"]], decision_date, spec["denominator_age"])
        if den is None or not den[2]:
            return None
        try:
            return (ar[2] + inv[2] - ap[2]) / float(den[2])
        except (TypeError, ZeroDivisionError):
            return None
    if spec["kind"] == "ratio_level":
        if f0 not in rows or spec["denominator_field"] not in rows:
            return None
        num = asof(rows[f0], decision_date, spec["denominator_age"])
        den = asof(rows[spec["denominator_field"]], decision_date, spec["denominator_age"])
        if num is None or den is None:
            return None
        # a4_h2 frozen spec: eff dates must agree within 400 days (F-A7-4)
        from datetime import date
        if abs((date.fromisoformat(num[1]) - date.fromisoformat(den[1])).days) > 400:
            return None
        try:
            if not den[2] or not num[2]:
                return None
            return float(num[2]) / float(den[2])
        except (TypeError, ZeroDivisionError):
            return None
    raise ValueError(f"unknown arm kind {spec['kind']}")


def pct_rank(values):
    """Percentile rank in [0,1]; average ranks for ties."""
    keys = list(values.keys())
    vals = [values[k] for k in keys]
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg / (len(vals) - 1) if len(vals) > 1 else 0.5
        i = j + 1
    return dict(zip(keys, ranks))


# --------------------------------------------------------------- book

def band_of(adv):
    if adv >= 50_000_000:
        return "A"
    if adv >= 10_000_000:
        return "B"
    if adv >= 2_000_000:
        return "C"
    return "UNTRADABLE"


def target_book(ranks, held, direction):
    """Sector-neutral tercile targets with one-decile retention hysteresis.
    ranks: {name: (sector, pct)}; held: {name: side} from previous decision.
    Returns {name: side} where side in {"L","S"}; sectors with < 6 ranked
    names abstain."""
    by_sector = {}
    for n, (sec, pct) in ranks.items():
        by_sector.setdefault(sec, []).append((n, pct))
    book = {}
    active = 0
    for sec, items in sorted(by_sector.items()):
        if len(items) < MIN_SECTOR_NAMES:
            continue
        active += 1
        for n, pct in items:
            prev = held.get(n)
            if direction == "low_long":
                is_long = pct <= TERCILE or (prev == "L" and pct <= TERCILE + HYSTERESIS)
                is_short = pct >= 1 - TERCILE or (prev == "S" and pct >= 1 - TERCILE - HYSTERESIS)
            else:
                is_long = pct >= 1 - TERCILE or (prev == "L" and pct >= 1 - TERCILE - HYSTERESIS)
                is_short = pct <= TERCILE or (prev == "S" and pct <= TERCILE + HYSTERESIS)
            if is_long and not is_short:
                book[n] = "L"
            elif is_short and not is_long:
                book[n] = "S"
    return book, active


def weights_from_book(book, sectors):
    """Equal-weight within legs, 1/n_active allocation per sector,
    0.5 long / 0.5 short inside each active sector. CASH absorbs net."""
    legs = {}
    by_sector = {}
    for n, side in book.items():
        by_sector.setdefault(sectors[n], {"L": [], "S": []})[side].append(n)
    active = [s for s, d in by_sector.items() if d["L"] and d["S"]]
    for s in active:
        d = by_sector[s]
        for n in d["L"]:
            legs[n] = 0.5 / (len(active) * len(d["L"]))
        for n in d["S"]:
            legs[n] = -0.5 / (len(active) * len(d["S"]))
    return legs


# ----------------------------------------------------------- simulation

def run_arm(arm_id, panel, prices, folds, dry_run, owner_go=None,
            price_manifest_sha="", panel_sha="", code_freeze_sha="",
            stress=False):
    """Simulate one arm. dry_run=True: structure only, no metrics.
    scored path requires the exact owner GO phrase (fail-closed).
    stress=True doubles the band cost (the frozen stress rerun)."""
    spec = ARM_SPECS[arm_id]
    if not dry_run and owner_go != GO_PHRASE:
        raise SystemExit("SCORED EXECUTION REFUSED: owner GO phrase absent/incorrect")
    all_fields = set(spec["numerator_fields"]) | {spec["denominator_field"]}
    available = set()
    for ent in panel.values():
        available.update(ent["rows"].keys())
        if all_fields <= available:
            break
    missing = sorted(all_fields - available)
    if missing:
        raise ValueError(f"panel missing required fields {missing} - fail closed")
    sect = {e: v["sector"] for e, v in panel.items()}
    cost_mult = 2.0 if stress else 1.0
    # global union calendar (fold/grid structure only)
    global_days = sorted({d for p in prices.values() for d in p["date"]})
    day_pos = {d: i for i, d in enumerate(global_days)}

    held = {}
    prev_w = {}
    records = []
    fold_metrics = {}
    name_contrib = {}
    decision_pnls = []
    missing_price_legs = 0

    for fold in folds:
        sess = fold["sessions"]
        grid_dates, grid_idx = decision_grid(sess)
        fold_pnls = []
        for gi, d in enumerate(grid_dates):
            is_warmup = gi < spec["warmup_decisions"] and fold["fold_id"] == "S0_FOLD_1"
            if d not in day_pos:
                continue
            gi_global = day_pos[d]
            # bands for EVERY name with 63 bars through d (F-A7-8: closes cost
            # at the name's own band even when the name fails the floor)
            bands = {}
            elig = {}
            for e, p in prices.items():
                i = p["pos"].get(d)
                if i is None or i < 62:
                    continue
                adv = statistics.median(p["dvol"][i - 62: i + 1])
                b = band_of(adv)
                bands[e] = b
                if b != "UNTRADABLE" and p["raw"][i] >= 1.00:
                    elig[e] = i
            # signals
            prev_d = global_days[gi_global - 252] if (spec["kind"] == "accrual_flow" and gi_global >= 252) else None
            raw_sig = {}
            for e in elig:
                ent = panel.get(e)
                if ent is None:
                    continue
                sig = signal_value(spec, ent, d, prev_d)
                if sig is not None and sig == sig:  # NaN guard
                    raw_sig[e] = sig
            ranks = pct_rank(raw_sig)
            ranks = {k: (sect[k], v) for k, v in ranks.items()}  # (sector, pct) as target_book expects
            book, n_active = target_book(ranks, held, spec["direction"])
            w = weights_from_book(book, sect)
            # fills at the next GLOBAL session close
            fill_d = global_days[gi_global + 1] if gi_global + 1 < len(global_days) else None
            if fill_d is None:
                continue
            turnover = 0.0
            cost = 0.0
            names_changed = set(k for k in set(w) | set(prev_w)
                                if abs(w.get(k, 0.0) - prev_w.get(k, 0.0)) > 1e-12)
            for n in names_changed:
                dw = abs(w.get(n, 0.0) - prev_w.get(n, 0.0))
                turnover += dw
                cost += dw * BAND_BPS.get(bands.get(n, "A"), 10.0) * cost_mult / 10000.0
            decision_pnls.append({"d": d, "scored": not is_warmup})
            if not dry_run:
                nxt_gi = gi + 1
                end_date = None
                if nxt_gi < len(grid_idx) and grid_dates[nxt_gi] in day_pos:
                    ng = day_pos[grid_dates[nxt_gi]]
                    if ng + 1 < len(global_days):
                        end_date = global_days[ng + 1]
                if end_date is None:
                    end_date = sess[-1]  # force flat at fold end
                pnl = 0.0
                for n in set(w) | set(prev_w):
                    p = prices.get(n)
                    if p is None:
                        continue
                    fi = p["pos"].get(fill_d)
                    ei = p["pos"].get(end_date)
                    if fi is None or ei is None or ei <= fi:
                        if w.get(n, 0.0) != 0.0:
                            missing_price_legs += 1
                        continue
                    r_ret = p["adj"][ei] / p["adj"][fi] - 1.0
                    w_now = w.get(n, 0.0)
                    pnl += w_now * r_ret
                    name_contrib[n] = name_contrib.get(n, 0.0) + w_now * r_ret
                pnl -= cost
                if not is_warmup:
                    fold_pnls.append(pnl)
                    decision_pnls[-1]["pnl"] = pnl
                    decision_pnls[-1]["fold"] = fold["fold_id"]
            records.append({
                "decision_date": d, "fill_date": fill_d, "fold": fold["fold_id"],
                "eligible": len(elig), "populated": len(raw_sig),
                "active_sectors": n_active, "legs": len(w),
                "turnover": round(turnover, 6), "cost_bps_paid": round(cost * 1e4, 4),
                "warmup": is_warmup,
            })
            held = book
            prev_w = w
        # fold boundary: force flat WITH cost (F-A7-6) and reset book state
        if prev_w:
            close_turnover = sum(abs(x) for x in prev_w.values())
            close_cost = sum(abs(x) * BAND_BPS.get(bands.get(n, "A"), 10.0) * cost_mult / 10000.0
                             for n, x in prev_w.items())
            if not dry_run and fold_pnls:
                fold_pnls[-1] -= close_cost
            records.append({
                "decision_date": sess[-1], "fill_date": sess[-1], "fold": fold["fold_id"],
                "eligible": 0, "populated": 0, "active_sectors": 0, "legs": 0,
                "turnover": round(close_turnover, 6),
                "cost_bps_paid": round(close_cost * 1e4, 4),
                "warmup": False, "event": "FOLD_FORCE_FLAT",
            })
            held = {}
            prev_w = {}
        if not dry_run:
            e_sum = sum(fold_pnls)
            wins = sum(x for x in fold_pnls if x > 0)
            losses = -sum(x for x in fold_pnls if x < 0)
            cum, peak_fold, mdd = 0.0, 0.0, 0.0
            for x in fold_pnls:
                cum += x
                peak_fold = max(peak_fold, cum)
                mdd = max(mdd, peak_fold - cum)
            fold_metrics[fold["fold_id"]] = {
                "decisions": len(fold_pnls), "sum_pnl": round(e_sum, 8),
                "pf": round(wins / losses, 6) if losses > 0 else None,
                "mdd": round(mdd, 8),
            }
    record = {
        "schema": "stocks_free_v8_run/arm_record@1",
        "arm_id": arm_id, "family_id": spec["family"],
        "arm_config_digest": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
        "data_snapshot_digest": hashlib.sha256(
            (panel_sha + price_manifest_sha).encode()).hexdigest(),
        "code_freeze_sha": code_freeze_sha,
        "dry_run": dry_run,
        "stress": stress,
        "decisions_total": len([x for x in records if x.get("event") != "FOLD_FORCE_FLAT"]),
        "scored_decisions_total": sum(1 for x in records if not x["warmup"] and x.get("event") != "FOLD_FORCE_FLAT"),
        "missing_price_legs": missing_price_legs,
        "fold_structure": [{k: (len(v) if k == "sessions" else v) for k, v in f.items()} for f in folds],
        "schedule": records,
    }
    if not dry_run:
        scored = [x["pnl"] for x in decision_pnls if x.get("scored") and "pnl" in x]
        e_sum = sum(scored)
        wins = sum(x for x in scored if x > 0)
        losses = -sum(x for x in scored if x < 0)
        record["metrics"] = {
            "expectancy": round(e_sum / len(scored), 10) if scored else None,
            "sum_pnl": round(e_sum, 8),
            "pf": round(wins / losses, 6) if losses > 0 else None,
            "folds": fold_metrics,
            "top_name_contribution": max(name_contrib.items(), key=lambda kv: kv[1]) if name_contrib else None,
            "decision_pnl": [
                {"d": x["d"], "fold": x.get("fold"), "pnl": round(x["pnl"], 10)}
                for x in decision_pnls if x.get("scored") and "pnl" in x
            ],
        }
    return record
