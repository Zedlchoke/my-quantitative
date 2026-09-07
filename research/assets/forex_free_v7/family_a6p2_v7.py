"""FOREX-FREE-V7 family FXFV7-A6-P2 — lead-lag diffusion from large
idiosyncratic EURUSD moves (frozen at selection_freeze_v7.json).

Verbatim from the frozen proposal + selection freeze:
- series: the staged PROVIDER DAILY closes (evidenced daily spans
  2018-09-03..2026-09-01, manifest fe2155c0). A1 interpretation recorded
  for A7: the proposal's evidence pointers and declared per-fold counts
  cite the daily spans; the mechanism is next-day-entry (the 16:00-NY
  phrase defines the decision-DAY boundary, weekday rule); daily bars are
  the staged daily observable. The A4-P1 family uses the H1-derived
  16:00-NY closes because its reaction windows are intraday.
- anchor: d_t = r_EURUSD,t - mean_panel(r_t) on the common 7-pair daily
  grid; expanding 80th percentile of |d| (min 60 obs, expanding history of
  completed days strictly before t); trigger -> all 6 followers (non-EUR
  pairs) take side = sign(d_t), entry at the NEXT daily close, hold 5
  sessions, episode-level non-overlap (no new trigger while any follower
  position from the last episode is open).
- neighbour: same machinery, percentile 70.
- control (own-lag): identical trigger machinery keyed on each follower's
  OWN idiosyncratic contrast |r_j,t - mean_panel(r_t)| >= its own
  expanding 80th percentile; follower j trades sign(r_j,t). Zero lead
  content.
- warmup: 65 trading days.

Costs, financing and books are driver-owned. No PnL here.
"""
from __future__ import annotations

import glob
import json
import math
import os
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone

import numpy as np

__all__ = ["run_arm", "ARM_IDS", "HOLD", "WARMUP", "LEAD"]

UTC = timezone.utc
CYCLE_ID = "FOREX-FREE-V7"
FAMILY_ID = "FXFV7-A6-P2"

ARM_IDS = OrderedDict((
    ("anchor", "anchor_leadlead_q80_hold5"),
    ("neighbour", "neighbour_q70_hold5"),
    ("control", "ownlag_control_q80_hold5"),
))
HOLD = 5
WARMUP = 65
LEAD = "EURUSD"
MIN_OBS = 60
PAIRS = ("EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF")
FOLLOWERS = tuple(p for p in PAIRS if p != LEAD)
PAIR_AREAS = {
    "EURUSD": ("EMU", "US"), "GBPUSD": ("GB", "US"), "USDJPY": ("US", "JP"),
    "USDCAD": ("US", "CA"), "AUDUSD": ("AU", "US"), "NZDUSD": ("NZ", "US"),
    "USDCHF": ("US", "CH"),
}


class DataBlocked(RuntimeError):
    pass


_D_CACHE: dict = {}


def load_daily(price_dir: str, pair: str):
    key = (price_dir, pair)
    if key in _D_CACHE:
        return _D_CACHE[key]
    rows = []
    for fp in sorted(glob.glob(os.path.join(price_dir, f"{pair}_1day_*_a.json"))):
        d = json.load(open(fp))
        if d.get("status") != "ok":
            continue
        for v in d["values"]:
            rows.append((date.fromisoformat(v["datetime"][:10]), float(v["close"])))
    if not rows:
        raise DataBlocked(f"NO_DAILY_DATA: {pair}")
    rows.sort()
    out = (rows, dict(rows))
    _D_CACHE[key] = out
    return out


def _iso_day_ts(day: date) -> str:
    # daily-bar decision instant convention: day D 00:00Z stamp of the bar
    # that COMPLETED at D (the entry uses the next day's stamp); recorded
    # in the driver ledger rows as the daily-clock decision instant
    return f"{day.isoformat()}T00:00:00+00:00"


def fold_of(day: date, fold_starts) -> int:
    if day < fold_starts[1]:
        return 1
    if day < fold_starts[2]:
        return 2
    return 3


def run_arm(arm: str, data_paths: dict):
    if arm not in ARM_IDS:
        raise ValueError(f"unknown arm {arm}")
    q = 70 if arm == "neighbour" else 80
    own_lag = arm == "control"
    price_dir = data_paths["price_dir"]
    s0_start, s0_end = data_paths["s0_start"], data_paths["s0_end"]
    fold_starts = data_paths["fold_starts"]

    closes = {p: load_daily(price_dir, p)[1] for p in PAIRS}
    common = sorted(set.intersection(*[set(closes[p]) for p in PAIRS]))
    if data_paths.get("enforce_real_spans") and common[0] > date(2018, 9, 3):
        raise DataBlocked("DAILY_SPAN_UNEXPECTED_START")
    rets = {}
    for p in PAIRS:
        ds = sorted(closes[p])
        rets[p] = {}
        for i in range(1, len(ds)):
            rets[p][ds[i]] = math.log(closes[p][ds[i]] / closes[p][ds[i - 1]])

    decisions = []
    counts = {"candidate_days": 0, "warmup": 0, "panel_incomplete": 0,
              "episodes": 0, "entry_beyond_s0": 0}
    hist_lead = []
    hist_own = {p: [] for p in FOLLOWERS}
    open_until_idx = -1

    for i in range(WARMUP, len(common)):
        t = common[i]
        if not (s0_start <= t <= s0_end):
            hist_lead.append(None)
            for p in FOLLOWERS:
                hist_own[p].append(None)
            continue
        rs = [rets[p][t] for p in PAIRS if t in rets[p]]
        if len(rs) < len(PAIRS):
            counts["panel_incomplete"] += 1
            hist_lead.append(None)
            for p in FOLLOWERS:
                hist_own[p].append(None)
            continue
        mu = float(np.mean(rs))
        d_t = rets[LEAD][t] - mu
        counts["candidate_days"] += 1

        if i <= open_until_idx:
            hist_lead.append(abs(d_t))
            for p in FOLLOWERS:
                hist_own[p].append(abs(rets[p][t] - mu))
            continue

        entry_day = common[i + 1] if i + 1 < len(common) else None
        legs = 0
        if entry_day is not None and s0_start <= entry_day <= s0_end:
            if own_lag:
                # per-follower own-contrast trigger; sign(r_j)
                for p in FOLLOWERS:
                    h = [x for x in hist_own[p] if x is not None]
                    if len(h) >= MIN_OBS:
                        thr = float(np.percentile(h, q))
                        v = rets[p][t] - mu
                        if abs(v) >= thr:
                            side = 1 if rets[p][t] > 0 else -1
                            decisions.append(_mk(p, side, entry_day, t, v, fold_starts,
                                                 common, closes))
                            decisions[-1]["arm_config_digest"] = f"a6p2:{arm}:q{q}:lead{LEAD}:hold5:nonoverlap"
                            legs += 1
            else:
                h = [x for x in hist_lead if x is not None]
                if len(h) >= MIN_OBS:
                    thr = float(np.percentile(h, q))
                    if abs(d_t) >= thr:
                        side = 1 if d_t > 0 else -1
                        for p in FOLLOWERS:
                            decisions.append(_mk(p, side, entry_day, t, d_t, fold_starts,
                                                 common, closes))
                            decisions[-1]["arm_config_digest"] = f"a6p2:{arm}:q{q}:lead{LEAD}:hold5:nonoverlap"
                            legs += 1
            if legs:
                counts["episodes"] += 1
                open_until_idx = i + HOLD
        else:
            counts["entry_beyond_s0"] += 1

        hist_lead.append(abs(d_t))
        for p in FOLLOWERS:
            hist_own[p].append(abs(rets[p][t] - mu))

    meta = {
        "family_id": FAMILY_ID, "arm": arm, "arm_id": ARM_IDS[arm],
        "percentile": q, "own_lag": own_lag, "hold": HOLD, "warmup": WARMUP,
        "counts": counts, "n_decisions": len(decisions),
        "arm_config_digest": f"a6p2:{arm}:q{q}:lead{LEAD}:hold5:nonoverlap",
        "folds": {str(f): sum(1 for d in decisions if d["fold"] == f)
                  for f in (1, 2, 3)},
    }
    return {"decisions": decisions, "meta": meta}


def _mk(pair, side, entry_day, trigger_day, contrast, fold_starts, common, closes):
    ds = sorted(closes[pair])
    ie = ds.index(entry_day)
    ix = min(ie + HOLD, len(ds) - 1)
    return {
        "pair": pair, "side": side,
        "entry_day": str(entry_day), "exit_day": str(ds[ix]),
        "entry_ts": _iso_day_ts(entry_day), "exit_ts": _iso_day_ts(ds[ix]),
        "entry_price": closes[pair][entry_day], "exit_price": closes[pair][ds[ix]],
        "trigger_day": str(trigger_day), "trigger_contrast": contrast,
        "fold": fold_of(entry_day, fold_starts),
        "areas": PAIR_AREAS[pair],
        "arm_config_digest": "",  # filled by caller loop's meta digest
    }
