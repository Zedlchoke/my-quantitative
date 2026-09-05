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

def load_panel(fields):
    """Stream the panel; keep only wanted fields.
    Returns {entity: {"sector": s, "rows": {field: [(avail, eff, value)]}}}
    sorted by (avail, eff)."""
    want = set(fields)
    out = {}
    with open(PANEL) as f:
        for line in f:
            r = json.loads(line)
            fld = r["f"]
            if fld not in want:
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
    """{entity: {"date": [...], "raw": [...], "adj": [...], "dvol": [...]}}
    sorted by date."""
    out = {}
    for fn in sorted(os.listdir(PRICES)):
        if not fn.endswith(".json"):
            continue
        cik = fn.split("__")[0]
        bars = json.load(open(f"{PRICES}/{fn}"))
        out[cik] = {
            "date": [b["date"] for b in bars],
            "raw": [float(b["close"]) for b in bars],
            "adj": [float(b["adjusted_close"]) for b in bars],
            "dvol": [float(b["close"]) * float(b["volume"]) for b in bars],
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
        ar0 = asof(rows[f0], decision_date)
        inv0 = asof(rows[f1], decision_date)
        ap0 = asof(rows[f2], decision_date)
        if prev_session_date is None:
            return None
        ar1 = asof(rows[f0], prev_session_date)
        inv1 = asof(rows[f1], prev_session_date)
        ap1 = asof(rows[f2], prev_session_date)
        legs0 = (ar0, inv0, ap0)
        legs1 = (ar1, inv1, ap1)
        if any(l is None for l in legs0) or any(l is None for l in legs1):
            return None
        den = asof(rows[spec["denominator_field"]], decision_date, spec["denominator_age"])
        if den is None or not den[2]:
            return None
        # fiscal-type match: the two leg vintages must be 330-400 eff days apart
        from datetime import date
        gap = (date.fromisoformat(ar0[1]) - date.fromisoformat(ar1[1])).days
        if not (330 <= gap <= 400):
            return None
        num = (ar0[2] - ar1[2]) + (inv0[2] - inv1[2]) - (ap0[2] - ap1[2])
        try:
            return num / float(den[2])
        except (TypeError, ZeroDivisionError):
            return None
    if spec["kind"] == "wc_stock":
        f1, f2 = spec["numerator_fields"][1], spec["numerator_fields"][2]
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
        num = asof(rows[f0], decision_date, spec["denominator_age"])
        den = asof(rows[spec["denominator_field"]], decision_date, spec["denominator_age"])
        if num is None or den is None:
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

def session_index(price, d):
    return price["date"].index(d)


def advance_sessions(price, d, k):
    i = session_index(price, d) + k
    return price["date"][i] if 0 <= i < len(price["date"]) else None


def run_arm(arm_id, panel, prices, folds, dry_run, owner_go=None,
            price_manifest_sha="", panel_sha="", code_freeze_sha=""):
    """Simulate one arm. dry_run=True: structure only, no metrics.
    scored path requires the exact owner GO phrase (fail-closed)."""
    spec = ARM_SPECS[arm_id]
    if not dry_run and owner_go != GO_PHRASE:
        raise SystemExit("SCORED EXECUTION REFUSED: owner GO phrase absent/incorrect")
    all_fields = set(spec["numerator_fields"]) | {spec["denominator_field"]}
    sample_rows = next(iter(panel.values()))["rows"] if panel else {}
    missing = [f for f in all_fields if f not in sample_rows]
    if missing:
        raise ValueError(f"panel missing required fields {missing} - fail closed")
    sect = {e: v["sector"] for e, v in panel.items()}
    f1_sessions = folds[0]["sessions"]
    # t-1y evaluation points: 252 sessions back on the global calendar
    global_days = sorted({d for p in prices.values() for d in p["date"]})
    day_pos = {d: i for i, d in enumerate(global_days)}

    decisions = []
    held = {}
    prev_w = {}
    records = []
    cumulative = 0.0
    peak = 0.0
    fold_metrics = {}
    name_contrib = {}
    decision_pnls = []

    for fold in folds:
        sess = fold["sessions"]
        grid_dates, grid_idx = decision_grid(sess)
        fold_pnls = []
        for gi, d in enumerate(grid_dates):
            is_warmup = gi < spec["warmup_decisions"] and fold["fold_id"] == "S0_FOLD_1"
            # eligibility at d
            elig = {}
            for e, p in prices.items():
                if d not in day_pos:
                    continue
                dates = p["date"]
                i = day_pos[d]
                if i >= len(dates) or dates[i] != d:
                    continue
                window = p["dvol"][max(0, i - 62): i + 1]
                if len(window) < 63:
                    continue
                adv = statistics.median(window)
                b = band_of(adv)
                if b == "UNTRADABLE" or p["raw"][i] < 1.00:
                    continue
                elig[e] = {"band": b, "i": i}
            # signals
            gi_global = day_pos[d]
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
            ranks = {k: (v, sect[k]) for k, v in ranks.items()}
            book, n_active = target_book(ranks, held, spec["direction"])
            w = weights_from_book(book, sect)
            # fills at next session close
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
                b = elig.get(n, {}).get("band", "A")
                cost += dw * BAND_BPS.get(b, 10.0) / 10000.0
            fi = day_pos[fill_d]
            decision_pnls.append({"d": d, "scored": not is_warmup})
            if not dry_run:
                # position PnL from fill close to next decision's fill close
                nxt_gi = gi + 1
                end_i = None
                if nxt_gi < len(grid_idx) and grid_dates[nxt_gi] in day_pos:
                    ng = day_pos[grid_dates[nxt_gi]]
                    if ng + 1 < len(global_days):
                        end_i = day_pos[global_days[ng + 1]]
                if end_i is None:
                    end_i = day_pos[sess[-1]]  # force flat at fold end
                pnl = 0.0
                for n in set(w) | set(prev_w):
                    p = prices.get(n)
                    if p is None or fi >= len(p["date"]) or end_i >= len(p["date"]):
                        continue
                    r = p["adj"][end_i] / p["adj"][fi] - 1.0
                    w_now = w.get(n, 0.0)
                    w_old = prev_w.get(n, 0.0)
                    pnl += w_now * r
                    name_contrib[n] = name_contrib.get(n, 0.0) + w_now * r
                pnl -= cost
                cumulative += pnl
                peak = max(peak, cumulative)
                if not is_warmup:
                    fold_pnls.append(pnl)
                    decision_pnls[-1]["pnl"] = pnl
            records.append({
                "decision_date": d, "fill_date": fill_d, "fold": fold["fold_id"],
                "eligible": len(elig), "populated": len(raw_sig),
                "active_sectors": n_active, "legs": len(w),
                "turnover": round(turnover, 6), "cost_bps_paid": round(cost * 1e4, 4),
                "warmup": is_warmup,
            })
            held = book
            prev_w = w
        if not dry_run:
            e = sum(x for x in fold_pnls)
            wins = sum(x for x in fold_pnls if x > 0)
            losses = -sum(x for x in fold_pnls if x < 0)
            cum, peak_fold = 0.0, 0.0
            mdd = 0.0
            for x in fold_pnls:
                cum += x
                peak_fold = max(peak_fold, cum)
                mdd = max(mdd, peak_fold - cum)
            fold_metrics[fold["fold_id"]] = {
                "decisions": len(fold_pnls), "sum_pnl": round(e, 8),
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
        "decisions_total": len(records),
        "scored_decisions_total": sum(1 for r in records if not r["warmup"]),
        "fold_structure": [{k: (len(v) if k == "sessions" else v) for k, v in f.items()} for f in folds],
        "schedule": records,
    }
    if not dry_run:
        scored = [x["pnl"] for x in decision_pnls if x.get("scored") and "pnl" in x]
        e = sum(scored)
        wins = sum(x for x in scored if x > 0)
        losses = -sum(x for x in scored if x < 0)
        record["metrics"] = {
            "expectancy": round(e / len(scored), 10) if scored else None,
            "sum_pnl": round(e, 8),
            "pf": round(wins / losses, 6) if losses > 0 else None,
            "folds": fold_metrics,
            "top_name_contribution": max(name_contrib.items(), key=lambda kv: kv[1]) if name_contrib else None,
        }
    return record
