#!/usr/bin/env python
"""FOREX-FREE-V2: central scored runner. Calls the ACTUAL family module APIs
(family1.compute_arm_schedule / family2.compute_arm_schedule), books every
trade through the validated accounting kernel (cost once per side), assembles
cell metrics and Stage-A gates, and publishes once-only to the content
addressed ledger behind a W2 launch authorization.

Stage-A gate thresholds below were frozen BEFORE any V2 scored PnL existed
(selection_freeze.json + w2_freeze.json). No gate may be changed after any
real cell result is visible. Dummy dry-run mode books placeholder pnl=0 and
refuses publication; it reveals no scored outcome.
"""
import hashlib
import json
import math
import os
from datetime import datetime, timedelta, timezone

from research.assets.forex_free_v2 import accounting
from research.assets.forex_free_v2 import family1, family2
from research.assets.forex_free_v1 import td_loader

FAMILIES = {"family1": family1, "family2": family2}
PAIRS = td_loader.PAIRS
NOTIONAL = 10000
BASE_TIER = 1.0
STRESS_TIERS = (1.5, 2.0)
FOLD_BOUNDARIES = ("2020-03-01T00:00:00+00:00", "2022-05-01T00:00:00+00:00",
                   "2024-07-01T00:00:00+00:00", "2026-09-02T23:59:59+00:00")
PURGE_DAYS = 14
# Frozen before any V2 outcome (see w2_freeze.json):
MIN_EXPECTANCY = 0.0            # after-cost expectancy must be > 0
MIN_PF = 1.10
MIN_POSITIVE_FOLDS = 2          # of 3 populated
MIN_FOLD_PF = 0.80
FOLD_POPULATED_MIN_TRADES = 30
MDD_CEILING_USD = 2500.0        # 25% of the 10k USD-unit notional
MAX_POS_FOLD_SHARE = 0.50
MAX_PAIR_POS_SHARE = 0.40       # both selected proposals freeze <=40% gross positive
STRESS_MIN_PF = 1.00
DROPOUT_SURVIVAL_MIN = 5        # expectancy > 0 for >= 5 of 7 single-pair exclusions
NEIGHBOUR_MIN_EXPECTANCY = 0.0  # neighbour supports the anchor
CONTROL_REJECT_PF = 1.10        # placebo must not itself pass profitability
USD_CORR_CEILING = 0.30         # |corr(daily pnl, USD-index daily return)|
USD_DIAG_MIN_DAYS = 60


# ---------- session gate (frozen, outcome-blind) ----------
def is_market_open_entry(ts_iso, tz="America/New_York"):
    """Frozen trading week: Sun 21:00 New York -> Fri 16:00 New York.
    Entries outside are dropped fail-closed (weekend provider-coverage
    artifacts in the 2026+ tail must never be scored)."""
    t = datetime.fromisoformat(ts_iso)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    from zoneinfo import ZoneInfo
    ny = t.astimezone(ZoneInfo(tz))
    wd, hm = ny.weekday(), ny.hour * 60 + ny.minute
    if wd == 6:                       # Sunday
        return hm >= 21 * 60
    if wd == 4:                       # Friday
        return hm < 16 * 60
    if wd == 5:                       # Saturday
        return False
    return True                       # Mon-Thu


def apply_session_gate(trades):
    kept, dropped = [], []
    for tr in trades:
        (kept if is_market_open_entry(tr["entry_ts"]) else dropped).append(tr)
    return kept, dropped


# ---------- folds ----------
def _parse(ts):
    return datetime.fromisoformat(ts)


def fold_of(entry_ts_iso):
    """Fold index by entry instant; None if purged (within PURGE_DAYS after a
    boundary) or before the first boundary (warmup region)."""
    t = _parse(entry_ts_iso)
    for i in range(3):
        lo = _parse(FOLD_BOUNDARIES[i])
        hi = _parse(FOLD_BOUNDARIES[i + 1])
        if lo <= t < hi:
            if t < lo + timedelta(days=PURGE_DAYS):
                return None
            return i
    return None


# ---------- metrics ----------
def book_metrics(pnls):
    gross_pos = sum(p for p in pnls if p > 0)
    gross_neg = -sum(p for p in pnls if p < 0)
    pf = (gross_pos / gross_neg) if gross_neg > 0 else (math.inf if gross_pos > 0 else 0.0)
    return {
        "trades": len(pnls),
        "total_pnl": round(sum(pnls), 10),
        "expectancy": round(sum(pnls) / len(pnls), 10) if pnls else 0.0,
        "pf": round(pf, 10) if pf != math.inf else None,
        "gross_positive": round(gross_pos, 10),
    }


def fold_metrics(trades):
    out = []
    for f in range(3):
        ftr = [t for t in trades if t["_fold"] == f]
        m = book_metrics([t["_pnl"] for t in ftr])
        m["fold"] = f
        m["populated"] = m["trades"] >= FOLD_POPULATED_MIN_TRADES
        out.append(m)
    return out


def mdd_of(pnls):
    peak = trough = 0.0
    cum = 0.0
    mdd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    return round(mdd, 10)


def concentration(trades):
    """Share of gross positive pnl by pair; USD cash can never appear (trades
    are FX pairs only; kernel also excludes it)."""
    pos = [t for t in trades if t["_pnl"] > 0]
    gp = sum(t["_pnl"] for t in pos)
    if gp <= 0:
        return {}
    shares = {}
    for t in pos:
        if t["pair"] == "USD":
            continue
        shares[t["pair"]] = shares.get(t["pair"], 0.0) + t["_pnl"]
    return {k: round(v / gp, 6) for k, v in shares.items()}


def fold_positive_share(folds):
    gp = sum(f["gross_positive"] for f in folds if f["gross_positive"] > 0)
    if gp <= 0:
        return 0.0
    return round(max(f["gross_positive"] for f in folds) / gp, 6)


def break_even_bps(trades):
    if not trades:
        return None
    gross = sum(t["_gross_move_pnl"] for t in trades)
    return round(gross / (len(trades) * 2 * NOTIONAL) * 10000, 6)


def usd_drift_corr(trades, rows_by_pair):
    """Frozen D1-D3 style diagnostic: Pearson corr between daily aggregate
    trade pnl and the equal-weight USD-index daily return, over days with
    trades (D1 attribution; D3 sign check recorded)."""
    def usd_ret(d):
        rs = []
        for pair in PAIRS:
            rows = rows_by_pair.get(pair) or []
            day = [r for r in rows if r["datetime"][:10] == d]
            if len(day) >= 2:
                sign = -1.0 if pair.split("/")[1] == "USD" else 1.0
                rs.append(sign * (day[-1]["close"] / day[0]["close"] - 1.0))
        return (sum(rs) / len(rs)) if rs else None

    daily = {}
    for t in trades:
        d = t["entry_ts"][:10]
        daily[d] = daily.get(d, 0.0) + t["_pnl"]
    days = sorted(daily)
    if len(days) < USD_DIAG_MIN_DAYS:
        return {"corr": None, "n_days": len(days), "evaluated": False}
    xs, ys = [], []
    for d in days:
        r = usd_ret(d)
        if r is not None:
            xs.append(r)
            ys.append(daily[d])
    if len(xs) < 3:
        return {"corr": None, "n_days": len(xs), "evaluated": False}
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    r = cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else 0.0
    return {"corr": round(r, 6), "n_days": len(xs), "evaluated": True}


# ---------- booking ----------
def book_trades(trades, dry_run=False):
    """Book every schedule trade through the accounting kernel exactly once
    per side. Returns trades annotated with _pnl (net, after the kernel's
    once-per-side costs) and _gross_move_pnl. In dry_run the net pnl is
    replaced by 0.0 (real_pnl=false); costs still book through the kernel so
    mechanics are exercised without revealing outcome."""
    book = accounting.PositionBook()
    out = []
    for tr in sorted(trades, key=lambda t: (t["exit_ts"], t["trade_id"])):
        book.open_position(trade_id=tr["trade_id"], pair=tr["pair"],
                           side="LONG" if tr["side"] > 0 else "SHORT",
                           notional_usd=tr["notional_usd"], price=tr["entry_price"],
                           ts_utc=tr["entry_ts"], cost_tier=tr.get("cost_tier", 1.0))
        closed = book.close_position(tr["trade_id"], tr["exit_price"], tr["exit_ts"])
        t2 = dict(tr)
        t2["_gross_move_pnl"] = round(closed.pnl_usd, 10)
        t2["_pnl"] = 0.0 if dry_run else round(closed.net_pnl_usd, 10)
        t2["_dry_run"] = dry_run
        out.append(t2)
    return out, book


# ---------- cell assembly ----------
def compute_cell(family_id, arm, rows_by_pair, dry_run=False):
    fam = FAMILIES[family_id]
    sched_by_tier = {}
    tier_trades = {}
    for tier in (BASE_TIER,) + STRESS_TIERS:
        sched = fam.compute_arm_schedule(arm, rows_by_pair, cost_tier=tier)
        kept, dropped = apply_session_gate(sched["trades"])
        booked, _book = book_trades(kept, dry_run=dry_run)
        for t in booked:
            t["_fold"] = fold_of(t["entry_ts"])
        tier_trades[tier] = {"base": booked, "dropped_weekend": len(dropped),
                             "dropped_purged": sum(1 for t in booked if t["_fold"] is None)}
        sched_by_tier[tier] = sched
    base = tier_trades[BASE_TIER]["base"]
    scored = [t for t in base if t["_fold"] is not None]
    folds = fold_metrics(scored)
    conc = concentration(scored)
    mdd = mdd_of([t["_pnl"] for t in sorted(scored, key=lambda x: x["exit_ts"])])
    pop = [f for f in folds if f["populated"]]
    drop_one = {}
    for excl in PAIRS:
        sub = [t for t in scored if t["pair"] != excl]
        drop_one[excl] = round(sum(t["_pnl"] for t in sub) / len(sub), 10) if sub else 0.0
    usd = usd_drift_corr(scored, rows_by_pair)
    record = {
        "cell_id": f"{family_id}:{arm}:tier1.0",
        "family_id": family_id, "proposal_id": sched_by_tier[BASE_TIER]["proposal_id"],
        "arm": arm, "dry_run": dry_run, "real_pnl": not dry_run,
        "schedule_digest_base": sched_by_tier[BASE_TIER]["schedule_digest"],
        "folds_declared": list(FOLD_BOUNDARIES), "purge_days": PURGE_DAYS,
        "decisions": sched_by_tier[BASE_TIER]["decisions"],
        "weekend_gate_dropped": tier_trades[BASE_TIER]["dropped_weekend"],
        "purged_trades": tier_trades[BASE_TIER]["dropped_purged"],
        "base": book_metrics([t["_pnl"] for t in scored]),
        "folds": folds,
        "mdd_usd": mdd,
        "fold_positive_share": fold_positive_share(folds),
        "pair_concentration": conc,
        "drop_one_expectancy": drop_one,
        "break_even_cost_bps": break_even_bps(scored),
        "usd_drift_diag": usd,
        "stress": {},
        "observed": True, "published": False,
    }
    for tier in STRESS_TIERS:
        st = [t for t in tier_trades[tier]["base"] if t["_fold"] is not None]
        record["stress"][f"tier{tier}"] = book_metrics([t["_pnl"] for t in st])
        record["stress"][f"tier{tier}"]["weekend_gate_dropped"] = tier_trades[tier]["dropped_weekend"]
    return record


def stage_a_gates(rec):
    """Frozen Stage-A gate set. Returns [all_pass, [failure reasons]]."""
    g = []
    base = rec["base"]
    if not (base["expectancy"] > MIN_EXPECTANCY):
        g.append("EXPECTANCY_NONPOSITIVE")
    if base["pf"] is None or base["pf"] < MIN_PF:
        g.append("PF_BELOW_1.10")
    pop = [f for f in rec["folds"] if f["populated"]]
    if len([f for f in pop if f["expectancy"] > 0]) < MIN_POSITIVE_FOLDS:
        g.append("FEWER_THAN_2_POSITIVE_POPULATED_FOLDS")
    if any(f["pf"] is not None and f["pf"] < MIN_FOLD_PF for f in pop):
        g.append("POPULATED_FOLD_PF_BELOW_0.80")
    if rec["mdd_usd"] > MDD_CEILING_USD:
        g.append("MDD_ABOVE_FROZEN_CEILING")
    if rec["fold_positive_share"] > MAX_POS_FOLD_SHARE:
        g.append("POSITIVE_FOLD_SHARE_ABOVE_50PCT")
    if rec["pair_concentration"] and max(rec["pair_concentration"].values()) > MAX_PAIR_POS_SHARE:
        g.append("PAIR_CONCENTRATION_ABOVE_40PCT")
    for tier in STRESS_TIERS:
        st = rec["stress"][f"tier{tier}"]
        if not (st["total_pnl"] > 0 and (st["pf"] is None or st["pf"] >= STRESS_MIN_PF)):
            g.append(f"STRESS_TIER_{tier}_FAIL")
    surv = sum(1 for v in rec["drop_one_expectancy"].values() if v > 0)
    if surv < DROPOUT_SURVIVAL_MIN:
        g.append("DROP_ONE_PAIR_SURVIVAL_INSUFFICIENT")
    if rec["usd_drift_diag"]["evaluated"] and abs(rec["usd_drift_diag"]["corr"]) > USD_CORR_CEILING:
        g.append("USD_DRIFT_EXPLAINS_ANCHOR")
    return [len(g) == 0, g]


def mechanism_sanity(family_cells):
    """Cross-arm frozen rules: neighbour must support the anchor; the placebo
    must not itself be profitable-passing. Input: {'anchor':rec,'neighbour':rec,
    'control':rec} of ONE family (base tier)."""
    a, n, c = family_cells["anchor"], family_cells["neighbour"], family_cells["control"]
    g = []
    if not (n["base"]["expectancy"] > NEIGHBOUR_MIN_EXPECTANCY):
        g.append("NEIGHBOUR_DOES_NOT_SUPPORT_ANCHOR")
    if c["base"]["expectancy"] > 0 and (c["base"]["pf"] is None or c["base"]["pf"] >= CONTROL_REJECT_PF):
        g.append("CONTROL_REPRODUCES_MECHANISM")
    return [len(g) == 0, g]


# ---------- once-only publication ----------
def publish_cell(ledger_path, record, authorization_path, expected_w2_sha):
    """Publish exactly once per record digest. Requires an authorization file
    {"w2_sha": ...} whose w2_sha equals the frozen execution SHA. Returns
    (observed_delta, published_now); replay of an already-published digest is
    a zero-delta no-op. Parallel callers serialize on an flock."""
    if not os.path.exists(authorization_path):
        raise ValueError("LAUNCH_AUTHORIZATION_MISSING")
    auth = json.load(open(authorization_path))
    if auth.get("w2_sha") != expected_w2_sha:
        raise ValueError("W2_SHA_MISMATCH")
    if record.get("dry_run") or not record.get("real_pnl"):
        raise ValueError("REAL_PNL_REQUIRED_FOR_SCORED_PUBLICATION")
    payload = dict(record)
    payload["gates"], payload["gate_reasons"] = stage_a_gates(record)
    data = accounting.sha256_hex(accounting.canonical_json_bytes(payload))
    payload["digest"] = data
    line = accounting.canonical_json_bytes(payload) + b"\n"
    import fcntl
    d = os.path.dirname(os.path.abspath(ledger_path))
    os.makedirs(d, exist_ok=True)
    with open(ledger_path, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            existing = f.read().decode("utf-8")
            if f'"digest":"{data}"' in existing:
                return (0, 0)
            f.seek(0, os.SEEK_END)
            f.write(line)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return (1, 1)


def load_rows(data_root):
    rows = {}
    for pair in PAIRS:
        r, _q = td_loader.load_pair_h1(pair, data_root)
        rows[pair] = r
    return rows
