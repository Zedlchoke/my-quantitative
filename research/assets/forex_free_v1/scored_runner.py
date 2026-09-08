#!/usr/bin/env python
"""FOREX-FREE-V1 central scored runner (F8). Central wiring only: it owns no
strategy logic. Cell = family x arm across the 7 authorized pairs; PnL per
trade = family net_return x FROZEN_NOTIONAL. Publication is idempotent by
cell digest and requires the W1 launch authorization artifact; every computed
cell increments the observed counter exactly once, published or not."""
import hashlib, json, os
from datetime import datetime, timezone

FROZEN_NOTIONAL = 10_000.0
FOLDS = 3
ARM_ORDER = ["anchor", "neighbour", "control"]

# --- family row adapters (verified at runtime; see runner_api_notes.json) ---

def to_family1_rows(canonical_rows):
    return [{"timestamp": datetime.fromisoformat(r["datetime"]).replace(tzinfo=timezone.utc).isoformat(),
             "open": float(r["open"]), "high": float(r["high"]),
             "low": float(r["low"]), "close": float(r["close"])} for r in canonical_rows]

def to_family2_rows(canonical_rows):
    return [{"datetime": datetime.fromisoformat(r["datetime"]).replace(tzinfo=timezone.utc).isoformat(),
             "open": float(r["open"]), "high": float(r["high"]),
             "low": float(r["low"]), "close": float(r["close"])} for r in canonical_rows]

FAMILY_ADAPTERS = {
    "family1": {"rows": to_family1_rows, "load_bars": "load_bars", "run_arm": "run_arm",
                "pnl_field": "net_return_frac", "clock": ("entry_instant", "exit_instant")},
    "family2": {"rows": to_family2_rows, "load_bars": "load_bars", "run_arm": "run_arm",
                "pnl_field": "net_ret", "clock": ("day", "day")},
}

def extract_trades(family, pair, run):
    """Per-trade records from a family run result. PnL = net_return x NOTIONAL."""
    spec = FAMILY_ADAPTERS[family]
    t0, t1 = spec["clock"]
    field = spec["pnl_field"]
    out = []
    for c in run["cashflows"]:
        if c.get(field) is None:
            continue
        out.append({"pair": pair, "trade_id": c.get("trade_id", c.get("day")),
                    "entry_ts": str(c[t0]), "exit_ts": str(c[t1]),
                    "net_return": float(c[field]),
                    "pnl": float(c[field]) * FROZEN_NOTIONAL,
                    "cost_frac": float(c.get("cost_frac", c.get("cost_ret", 0.0)))})
    return out

def run_family_cell(module, family, canonical_rows_by_pair, arm_id, cost_tier):
    """Compute one cell (family x arm x tier across pairs). Returns the cell
    record; increments nothing and publishes nothing."""
    spec = FAMILY_ADAPTERS[family]
    trades = []
    module_scoring_authorized = []
    for pair in sorted(canonical_rows_by_pair):
        bars = getattr(module, spec["load_bars"])(spec["rows"](canonical_rows_by_pair[pair]))
        run = getattr(module, spec["run_arm"])(bars, arm_id, cost_tier, pair=pair)
        # family1 exposes run_digest; family2 exposes sha256 (A7 W1 delta B1)
        digest = run.get("run_digest") or run.get("sha256")
        if not digest:
            raise ValueError(f"RUN_MISSING_DIGEST: {family} {pair} {arm_id}")
        module_scoring_authorized.append(run.get("scoring_authorized"))
        trades.extend(extract_trades(family, pair, run))
    trades.sort(key=lambda t: (t["exit_ts"], t["pair"]))
    record = {"family": family, "arm_id": arm_id, "cost_tier": cost_tier,
              "pairs": sorted(canonical_rows_by_pair), "trades": trades,
              "module_scoring_authorized_fields": module_scoring_authorized}
    record["digest"] = hashlib.sha256(json.dumps(
        {k: v for k, v in record.items()}, sort_keys=True).encode()).hexdigest()
    return record

# --- metrics (hand-verifiable; PnL list is chronological by exit) ---

def book_metrics(pnls):
    pos = sum(p for p in pnls if p > 0)
    neg = sum(p for p in pnls if p < 0)
    return {"trades": len(pnls), "total_pnl": round(sum(pnls), 10),
            "expectancy": (sum(pnls) / len(pnls)) if pnls else None,
            "profit_factor": (pos / abs(neg)) if neg else (float("inf") if pos else None),
            "positive": sum(pnls) > 0}

def fold_split(trades):
    k = max(1, len(trades) // FOLDS)
    return [trades[i * k:(i + 1) * k] for i in range(FOLDS) if trades[i * k:(i + 1) * k]]

def fold_metrics(trades):
    out = []
    for i, f in enumerate(fold_split(trades)):
        m = book_metrics([t["pnl"] for t in f])
        m["fold"] = f"fold{i}"
        out.append(m)
    return out

def mdd_of(pnls):
    curve = peak = mdd = 0.0
    for p in pnls:
        curve += p
        peak = max(peak, curve)
        mdd = max(mdd, peak - curve)
    return mdd

def concentration(trades):
    by_pair, total_pos = {}, 0.0
    for t in trades:
        by_pair.setdefault(t["pair"], 0.0)
        if t["pnl"] > 0:
            by_pair[t["pair"]] += t["pnl"]
            total_pos += t["pnl"]
    if total_pos == 0:
        return {k: None for k in by_pair}
    return {k: round(v / total_pos, 6) for k, v in by_pair.items()}

def fold_labeled_trades(trades):
    out = []
    for i, f in enumerate(fold_split(trades)):
        for t in f:
            out.append(dict(t, pair=f"fold{i}"))
    return out

def assemble_cell_record(cell_run, family, arm_id, tier):
    pnls = [t["pnl"] for t in cell_run["trades"]]
    folds = fold_metrics(cell_run["trades"])
    rec = {"family": family, "arm_id": arm_id, "cost_tier": tier,
           "label": f"{family}:{arm_id}:tier{tier}",
           "book": book_metrics(pnls), "mdd_usd": round(mdd_of(pnls), 6),
           "folds": folds,
           "pair_concentration": concentration(cell_run["trades"]),
           "fold_concentration": concentration(fold_labeled_trades(cell_run["trades"])),
           "module_scoring_authorized_field": None,  # recorded verbatim by executor
           "observed": True, "published": False}
    rec["digest"] = hashlib.sha256(json.dumps(
        {k: v for k, v in rec.items() if k != "digest"}, sort_keys=True).encode()).hexdigest()
    return rec

def stage_a_gates(record):
    b = record["book"]
    if b["trades"] == 0:
        return False, "NO_TRADES"
    if not (b["expectancy"] > 0):
        return False, "EXPECTANCY_NONPOSITIVE"
    if not (b["profit_factor"] >= 1.10):
        return False, "PF_BELOW_1_10"
    pos_folds = sum(1 for f in record["folds"] if f["positive"])
    if pos_folds < 2:
        return False, "FOLDS_POSITIVE_LT_2"
    for f in record["folds"]:
        if f["profit_factor"] is not None and f["profit_factor"] < 0.80:
            return False, "FOLD_PF_BELOW_0_80"
    if record["mdd_usd"] > 0.12 * FROZEN_NOTIONAL:
        return False, "MDD_ABOVE_12PCT_NOTIONAL"
    for v in record["fold_concentration"].values():
        if v is not None and v > 0.50:
            return False, "FOLD_CONCENTRATION_ABOVE_50PCT"
    for v in record["pair_concentration"].values():
        if v is not None and v > 0.40:
            return False, "PAIR_CONCENTRATION_ABOVE_40PCT"
    return True, "PASS"

# --- observed/publication/replay accounting ---

def publish_cell(ledger_path, record, launch_verdict_path, expected_w1_sha):
    """Observed counter increments for EVERY computed cell. Publication happens
    at most once per cell digest and ONLY with an authorized W1 verdict record
    whose w1_sha equals the frozen execution SHA. Returns (observed_delta, published_now)."""
    if not os.path.exists(launch_verdict_path):
        raise ValueError("LAUNCH_AUTHORIZATION_MISSING")
    verdict = json.load(open(launch_verdict_path))
    if verdict.get("verdict") != "FOREX_FREE_V1_W1_LAUNCH_AUTHORIZED":
        raise ValueError("LAUNCH_NOT_AUTHORIZED")
    if verdict.get("w1_sha") != expected_w1_sha:
        raise ValueError("W1_SHA_MISMATCH")
    lines = []
    if os.path.exists(ledger_path):
        lines = [json.loads(l) for l in open(ledger_path) if l.strip()]
    already = [l for l in lines if l.get("digest") == record["digest"]]
    if already:
        return 0, False  # idempotent replay: no observed delta, no new publication
    if record["book"]["trades"] == 0:
        # computed cell: observed counter increments even though publication
        # is refused (zero positions cannot be scored evidence)
        with open(ledger_path, "a") as f:
            f.write(json.dumps({"digest": record["digest"], "observed_only": True,
                                "reason": "REFUSED_ZERO_TRADES"}, sort_keys=True) + "\n")
        return 1, False
    entry = {"digest": record["digest"], "label": record["label"],
             "book": record["book"], "gates": stage_a_gates(record),
             "w1_sha": expected_w1_sha, "module_scoring_authorized_field": record["module_scoring_authorized_field"]}
    with open(ledger_path, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return 1, True
