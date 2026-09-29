"""Leg identity + the frozen leg implementations — PC12A impl lane.

Identity tuple (campaign §1), frozen before any computation, loaded from a
JSON config per leg: ``(cycle_id, sleeve_id, corpus_gid|class_candidate_id,
family_id, mech_key, clock, frozen params, pit_join_list, cost_tier,
outcome_exposed_label, cluster_id)``.

Implementations:
(a) the 9 VOLPROF-M1 class candidates per CLASS_SPEC_VOLPROF_M1.md r2
    (size-weighted BID-side profile, 20d lookback, 0.25xATR20d bins on the
    0.1-pip grid, POC/VA70/LVN-P20/P80, weekly Friday-20:00 freeze,
    intraday London-Union-NY entry windows, flat by 19:55 UTC);
(b) 3 exemplar corpus legs from the mechanization triage:
    USDJPY-S001 Donchian-20/55 D1 trend (T1),
    GBPUSD-S027 weekday trend/MR meta-gate (T1),
    EURUSD-S009 MACD-H exhaustion exit (T2 - declared defaults frozen in
    the leg config, disclosed).

Every leg carries its outcome_exposed_label into every journal row.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import calendar_service as cal

VOLPROF_SLEEVE = "POOL_B_VOLPROF"
UNIT_FIXED_10K = 10_000  # 1 unit = 10,000 base-currency units (class spec 1.1)


# ---------------------------------------------------------------------------
# Identity + decision objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LegIdentity:
    cycle_id: str
    sleeve_id: str
    candidate_id: str          # corpus_gid or CLASS_CANDIDATE id
    family_id: str
    mech_key: str
    clock: str
    symbol: str
    pit_join_list: Tuple[str, ...]
    cost_tier: str
    outcome_exposed_label: str
    cluster_id: str
    params: Dict           # frozen parameters (never tuned post-freeze)
    arm_config_digest: str


def _digest(params: Dict, candidate_id: str) -> str:
    import hashlib

    blob = json.dumps({"candidate": candidate_id, "params": params},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


@dataclass
class LegDecision:
    vote: int                       # -1 / 0 / +1
    desired_units: int              # signed target the leg wants
    reason_code: str                # frozen enum from the leg spec
    order_kind: str = "OPEN"        # OPEN/CLOSE/ADJUST hint
    feature_pit_snapshot: List[Dict] = field(default_factory=list)
    blocked_reason: Optional[str] = None
    standing_stop: Optional[float] = None


class LegError(RuntimeError):
    pass


def load_leg_configs(config_dir: str) -> List[Dict]:
    out = []
    for fn in sorted(os.listdir(config_dir)):
        if fn.endswith(".json"):
            with open(os.path.join(config_dir, fn), encoding="utf-8") as fh:
                out.append(json.load(fh))
    return out


def make_identity(cfg: Dict) -> LegIdentity:
    return LegIdentity(
        cycle_id=cfg["cycle_id"],
        sleeve_id=cfg["sleeve_id"],
        candidate_id=cfg.get("class_candidate_id") or cfg["corpus_gid"],
        family_id=cfg["family_id"],
        mech_key=cfg["mech_key"],
        clock=cfg["clock"],
        symbol=cfg["symbol"],
        pit_join_list=tuple(cfg.get("pit_join_list", [])),
        cost_tier=cfg["cost_tier"],
        outcome_exposed_label=cfg["outcome_exposed_label"],
        cluster_id=cfg["cluster_id"],
        params=dict(cfg.get("params", {})),
        arm_config_digest=_digest(cfg.get("params", {}),
                                  cfg.get("class_candidate_id")
                                  or cfg["corpus_gid"]),
    )


# ---------------------------------------------------------------------------
# VOLPROF weekly profile (CLASS_SPEC 3.2 -- all frozen)
# ---------------------------------------------------------------------------


@dataclass
class WeeklyProfile:
    freeze_ts: dt.datetime
    poc: float
    vah: float
    val: float
    w_bin: float
    p20: float
    p80: float
    atr20d: float
    nodes: Tuple[float, ...]      # LVN run midpoints
    bin_edges: np.ndarray         # populated-bin edges (price grid)
    bin_activity: np.ndarray      # aligned populated-bin activity
    digest: str = ""


def build_profile(freeze_ts: dt.datetime, day_buffer: List[Dict]) -> WeeklyProfile:
    """Profile from the last 20 TRADING days of per-minute data.

    ``day_buffer`` entries: {date, mid_close: np.ndarray, bid_vol:
    np.ndarray, tradable: np.ndarray, day_high, day_low, day_close}.
    Trading day = UTC weekday with >= 360 tradable minutes (3.2).
    """
    days = [d for d in day_buffer
            if d["date"].weekday() < 5 and int(d["tradable"].sum()) >= 360]
    days = days[-20:]
    if len(days) < 20:
        raise LegError(f"profile freeze {freeze_ts}: only {len(days)}/20 "
                       f"trading days in buffer")
    # daily bars aggregated from M1 (3.2): high=max BID high, low=min BID
    # low, close=last M1 mid close; TR standard formula.
    closes = [d["day_close"] for d in days]
    trs = []
    for i, d in enumerate(days):
        h, l = d["day_high"], d["day_low"]
        pc = closes[i - 1] if i > 0 else None
        tr = h - l if pc is None else max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    atr20d = float(np.mean(trs))

    mids = np.concatenate([d["mid_close"][d["tradable"]] for d in days])
    vols = np.concatenate([d["bid_vol"][d["tradable"]] for d in days])
    lo = float(mids.min())
    hi = float(mids.max())
    pip_grid = _pip_grid_of(mids)
    # W_BIN = 0.25 x ATR20d quantized DOWN to the 0.1-pip grid, >= 0.1 pip
    raw_w = 0.25 * atr20d
    w_bin = max(math.floor(raw_w / pip_grid) * pip_grid, pip_grid)
    if w_bin <= 0:
        raise LegError("degenerate bin width")
    n_bins = int(math.ceil((hi - lo) / w_bin)) + 2
    idx = np.clip(((mids - lo) / w_bin).astype(np.int64), 0, n_bins - 1)
    act = np.bincount(idx, weights=vols, minlength=n_bins)
    populated = act > 0
    if not populated.any():
        raise LegError("no populated bins")

    # POC: max total assigned activity; tie -> lowest bin index
    poc_i = int(np.argmax(act))
    poc = lo + (poc_i + 0.5) * w_bin
    # VA: minimal consecutive bin set containing POC, cumulative >= 70%,
    # greedy add of the adjacent bin with greater activity (tie -> up)
    total = act.sum()
    lo_i = hi_i = poc_i
    cum = act[poc_i]
    while cum < VA_SHARE * total and (lo_i > 0 or hi_i < n_bins - 1):
        down = act[lo_i - 1] if lo_i > 0 else -1.0
        up = act[hi_i + 1] if hi_i < n_bins - 1 else -1.0
        if up >= down:  # tie -> up
            hi_i += 1
            cum += act[hi_i]
        else:
            lo_i -= 1
            cum += act[lo_i]
    vah = lo + (hi_i + 1) * w_bin   # upper boundary of the extreme bin
    val = lo + lo_i * w_bin         # lower boundary of the extreme bin

    # P20/P80 over POPULATED bins
    pop_act = act[populated]
    p20 = float(np.percentile(pop_act, 20))
    p80 = float(np.percentile(pop_act, 80))

    # LVN runs: maximal contiguous populated runs with activity <= P20,
    # bounded above AND below by populated bins with activity > P20
    nodes: List[float] = []
    i = 0
    n = n_bins
    while i < n:
        if populated[i] and act[i] <= p20:
            j = i
            while j + 1 < n and populated[j + 1] and act[j + 1] <= p20:
                j += 1
            below = i > 0 and populated[i - 1] and act[i - 1] > p20
            above = j < n - 1 and populated[j + 1] and act[j + 1] > p20
            if below and above:
                span_lo = lo + i * w_bin
                span_hi = lo + (j + 1) * w_bin
                nodes.append((span_lo + span_hi) / 2.0)
            i = j + 1
        else:
            i += 1

    prof = WeeklyProfile(freeze_ts=freeze_ts, poc=poc, vah=vah, val=val,
                         w_bin=w_bin, p20=p20, p80=p80, atr20d=atr20d,
                         nodes=tuple(nodes), bin_edges=np.array(
                             [lo + k * w_bin for k in range(n_bins + 1)]),
                         bin_activity=act)
    prof.digest = _digest(
        {"poc": poc, "vah": vah, "val": val, "w_bin": w_bin, "p20": p20,
         "p80": p80, "atr20d": atr20d, "nodes": list(nodes),
         "n_days": len(days)}, f"profile@{freeze_ts.isoformat()}")
    return prof


VA_SHARE = 0.70


def _pip_grid_of(mids: np.ndarray) -> float:
    """0.1-pip grid per pair (1e-5 for 5-decimal pairs, 1e-3 for JPY)."""
    span = float(mids.max() - mids.min())
    return 1e-3 if span > 20 else 1e-5


def bin_activity_at(profile: WeeklyProfile, price: float) -> float:
    """Frozen-profile activity of the bin containing ``price``."""
    edges = profile.bin_edges
    i = int(np.clip((price - edges[0]) / profile.w_bin,
                    0, len(profile.bin_activity) - 1))
    return float(profile.bin_activity[i])


# ---------------------------------------------------------------------------
# Shared bar context handed to legs by the engine
# ---------------------------------------------------------------------------


@dataclass
class BarContext:
    ts: dt.datetime               # decision instant == bar close time
    symbol: str
    mid_close: float
    mid_close_prev: float
    bid_open: float
    ask_open: float
    bid_close: float
    ask_close: float
    bid_low: float                # completed bar's quoted-side extremes
    ask_high: float
    atr60: float                  # mean TR of last 60 M1 bars (0 if n/a)
    in_entry_window: bool
    is_flat_instant: bool         # the 19:54 hard-flat decision instant
    day: dt.date
    profile: Optional[WeeklyProfile]
    last_data_ts: Optional[dt.datetime]  # for the 90s staleness law


# ---------------------------------------------------------------------------
# Base leg
# ---------------------------------------------------------------------------


class BaseLeg:
    wants_every_bar = False       # intraday M1 monitoring?

    def __init__(self, identity: LegIdentity):
        self.identity = identity
        self.desired_units = 0    # current standing desire (signed)

    # engine hook: weekly Friday-20:00 profile freeze (VOLPROF legs)
    def on_profile(self, profile: WeeklyProfile) -> None:  # pragma: no cover
        pass

    def on_bar(self, ctx: BarContext) -> Optional[LegDecision]:
        raise NotImplementedError


def _pit(input_id: str, available: dt.datetime, value: str,
         max_age: str, ok: bool) -> Dict:
    return {"input_id": input_id,
            "available_time_utc": cal_final(available),
            "value_digest": value, "max_age": max_age,
            "max_age_ok": ok}


def cal_final(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# (a) VOLPROF class candidates (CLASS_SPEC 5.1-5.3, frozen)
# ---------------------------------------------------------------------------


class VolprofLeg(BaseLeg):
    wants_every_bar = True
    STALE_MAX_SEC = 90            # 4.2 fail-closed staleness law

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.shape = p["shape"]               # vc1_vaedge | vc2_lvnfail | vc3_pocmag
        self.unit = int(p.get("unit_base_units", UNIT_FIXED_10K))
        self.cooldown_min = int(p.get("cooldown_min", 60))
        self.traverse_confirm_min = int(p.get("traverse_confirm_min", 60))
        self.tmax_min = int(p.get("tmax_min", 240))
        self.dev_k = float(p.get("dev_k", 3.0))
        self.profile: Optional[WeeklyProfile] = None
        # live state
        self.entry_ts: Optional[dt.datetime] = None
        self.entry_price = 0.0
        self.stop_level: Optional[float] = None
        self.cooldown_until: Optional[dt.datetime] = None
        self.pending_traverse: Optional[Dict] = None
        self.last_exit_ts: Optional[dt.datetime] = None

    def on_profile(self, profile: WeeklyProfile) -> None:
        self.profile = profile

    # -- helpers --------------------------------------------------------------

    def _cooled(self, ts: dt.datetime) -> bool:
        return self.cooldown_until is None or ts >= self.cooldown_until

    def _bin_two_beyond(self, prof: WeeklyProfile, edge: float,
                        below: bool) -> bool:
        """Activity of the TWO bins immediately beyond the edge <= P20."""
        i_edge = int(round((edge - prof.bin_edges[0]) / prof.w_bin))
        for k in (1, 2):
            i = i_edge - k if below else i_edge + k
            if i < 0 or i >= len(prof.bin_activity):
                continue  # beyond profile -> empty region -> low acceptance
            if prof.bin_activity[i] > prof.p20:
                return False
        return True

    def on_bar(self, ctx: BarContext) -> Optional[LegDecision]:
        prof = ctx.profile
        ts = ctx.ts
        flat_vote = self._flat_decision(ctx)
        if flat_vote is not None:
            return flat_vote
        if prof is None or ctx.atr60 <= 0:
            return None
        # staleness fail-closed (4.2): newest bar older than 90s -> NOT_RUN
        if ctx.last_data_ts is not None and (
                ts - ctx.last_data_ts).total_seconds() > self.STALE_MAX_SEC:
            return None

        if self.desired_units != 0:
            return self._manage_position(ctx)
        if not ctx.in_entry_window or not self._cooled(ts):
            return None

        if self.shape == "vc1_vaedge":
            return self._vc1(ctx, prof)
        if self.shape == "vc2_lvnfail":
            return self._vc2(ctx, prof)
        if self.shape == "vc3_pocmag":
            return self._vc3(ctx, prof)
        raise LegError(f"unknown shape {self.shape}")

    # -- the 19:54 hard-flat decision (flat BY 19:55 UTC, 4.1) ---------------
    def _flat_decision(self, ctx: BarContext) -> Optional[LegDecision]:
        if ctx.is_flat_instant and self.desired_units != 0:
            self._record_exit(ctx.ts, "TIME_STOP_FLAT_1955")
            return LegDecision(
                vote=0, desired_units=0, reason_code="TIME_STOP_FLAT_1955",
                order_kind="CLOSE",
                feature_pit_snapshot=[_pit(
                    f"{self.identity.symbol}_M1_MIDCLOSE",
                    ctx.ts, f"sha256:volprof:{ctx.mid_close:.10f}", "P7D",
                    True)])
        return None

    # -- exit management while holding ---------------------------------------
    def _manage_position(self, ctx: BarContext) -> Optional[LegDecision]:
        prof = ctx.profile
        long = self.desired_units > 0
        snap = [_pit(f"{self.identity.symbol}_M1_MIDCLOSE", ctx.ts,
                     f"sha256:volprof:{ctx.mid_close:.10f}", "P7D", True)]
        # 1. take-profit at/through POC (next-bar-open exit on the crossing)
        if long and ctx.mid_close >= prof.poc:
            return self._exit(ctx, "TP_POC", snap)
        if not long and ctx.mid_close <= prof.poc:
            return self._exit(ctx, "TP_POC", snap)
        # 2. ATR stop: quoted-side adverse extreme touches the level
        if self.stop_level is not None:
            if long and ctx.bid_low <= self.stop_level:
                return self._exit(ctx, "ATR_STOP", snap)
            if not long and ctx.ask_high >= self.stop_level:
                return self._exit(ctx, "ATR_STOP", snap)
        # 3. time stop (tmax minutes from entry; VC1 rides to the flat call)
        if self.entry_ts is not None and self.shape != "vc1_vaedge":
            held = (ctx.ts - self.entry_ts).total_seconds() / 60.0
            if held >= self.tmax_min:
                return self._exit(ctx, "TIME_STOP_TMAX", snap)
        return None

    def _exit(self, ctx: BarContext, code: str, snap) -> LegDecision:
        self._record_exit(ctx.ts, code)
        return LegDecision(vote=0, desired_units=0, reason_code=code,
                           order_kind="CLOSE", feature_pit_snapshot=snap)

    def _record_exit(self, ts: dt.datetime, code: str) -> None:
        self.last_exit_ts = ts
        self.cooldown_until = ts + dt.timedelta(minutes=self.cooldown_min)
        self.entry_ts = None
        self.stop_level = None
        self.desired_units = 0

    # -- entries ---------------------------------------------------------------
    def _enter(self, ctx: BarContext, direction: int, code: str,
               stop: float, snap) -> LegDecision:
        self.desired_units = direction * self.unit
        self.entry_ts = ctx.ts
        self.entry_price = ctx.mid_close
        self.stop_level = stop
        return LegDecision(vote=direction, desired_units=self.desired_units,
                           reason_code=code, order_kind="OPEN",
                           feature_pit_snapshot=snap, standing_stop=stop)

    def _vc1(self, ctx: BarContext, prof: WeeklyProfile) -> Optional[LegDecision]:
        """VA-edge rejection fade (5.1)."""
        prev, cur = ctx.mid_close_prev, ctx.mid_close
        inside = prof.val <= prev <= prof.vah
        snap = [_pit(f"{self.identity.symbol}_M1_MIDCLOSE", ctx.ts,
                     f"sha256:volprof:{cur:.10f}", "P7D", True),
                _pit(f"{self.identity.symbol}_PROFILE_{prof.digest[:16]}",
                     prof.freeze_ts, f"sha256:volprof:{prof.digest}", "P7D",
                     True)]
        if inside and cur < prof.val - prof.w_bin and self._bin_two_beyond(
                prof, prof.val, below=True):
            stop = cur - ctx.atr60
            return self._enter(ctx, +1, "VC1_EDGE_REJECT_LONG", stop, snap)
        if inside and cur > prof.vah + prof.w_bin and self._bin_two_beyond(
                prof, prof.vah, below=False):
            stop = cur + ctx.atr60
            return self._enter(ctx, -1, "VC1_EDGE_REJECT_SHORT", stop, snap)
        return None

    def _vc2(self, ctx: BarContext, prof: WeeklyProfile) -> Optional[LegDecision]:
        """LVN traverse-failure fade (5.2)."""
        if not prof.nodes:
            return None
        prev, cur = ctx.mid_close_prev, ctx.mid_close
        snap = [_pit(f"{self.identity.symbol}_M1_MIDCLOSE", ctx.ts,
                     f"sha256:volprof:{cur:.10f}", "P7D", True),
                _pit(f"{self.identity.symbol}_PROFILE_{prof.digest[:16]}",
                     prof.freeze_ts, f"sha256:volprof:{prof.digest}", "P7D",
                     True)]
        pt = self.pending_traverse
        if pt is not None and (ctx.ts - pt["ts"]).total_seconds() / 60.0 \
                > self.traverse_confirm_min:
            self.pending_traverse = None
            pt = None
        if pt is not None:
            # the confirming return bar IS the opposite-direction cross of
            # the same node -- check the confirmation BEFORE arming any new
            # traverse (the pending window owns the event, spec 5.2)
            n, side = pt["node"], pt["side"]
            returned = (cur - n) if side == -1 else (n - cur)
            if returned >= prof.w_bin:     # back on the origin side by >= W
                stop = n - ctx.atr60 if side == -1 else n + ctx.atr60
                self.pending_traverse = None
                code = ("VC2_LVNFAIL_LONG" if side == -1
                        else "VC2_LVNFAIL_SHORT")
                return self._enter(ctx, -side, code, stop, snap)
            return None
        for n in prof.nodes:
            if prev >= n and cur < n:      # downward cross
                self.pending_traverse = {"ts": ctx.ts, "node": n,
                                         "side": -1}
                return None
            if prev <= n and cur > n:      # upward cross
                self.pending_traverse = {"ts": ctx.ts, "node": n, "side": +1}
                return None
        return None

    def _vc3(self, ctx: BarContext, prof: WeeklyProfile) -> Optional[LegDecision]:
        """POC-magnet reversion inside value (5.3)."""
        cur = ctx.mid_close
        if not (prof.val < cur < prof.vah):
            return None
        dev = abs(cur - prof.poc)
        if dev < self.dev_k * ctx.atr60:
            return None
        if bin_activity_at(prof, cur) < prof.p80:
            return None
        snap = [_pit(f"{self.identity.symbol}_M1_MIDCLOSE", ctx.ts,
                     f"sha256:volprof:{cur:.10f}", "P7D", True),
                _pit(f"{self.identity.symbol}_PROFILE_{prof.digest[:16]}",
                     prof.freeze_ts, f"sha256:volprof:{prof.digest}", "P7D",
                     True)]
        direction = 1 if cur < prof.poc else -1
        stop = cur - ctx.atr60 if direction > 0 else cur + ctx.atr60
        return self._enter(ctx, direction, "VC3_POCMAG", stop, snap)


VOLPROF_DEFAULT_CONFIGS = []
for _pair in ("EURUSD", "GBPUSD", "USDJPY"):
    for _shape, _fam, _mech in (
            ("vc1_vaedge", "VOLPROF-M1-VAEDGE", "vc1_vaedge"),
            ("vc2_lvnfail", "VOLPROF-M1-LVNFAIL", "vc2_lvnfail"),
            ("vc3_pocmag", "VOLPROF-M1-POCMAG", "vc3_pocmag")):
        _cand = f"{_shape.split('_')[0].upper()}-{_fam.split('-',2)[2]}-{_pair}"
        VOLPROF_DEFAULT_CONFIGS.append({
            "cycle_id": "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1",
            "sleeve_id": VOLPROF_SLEEVE,
            "class_candidate_id": _cand,
            "family_id": _fam,
            "mech_key": _mech,
            "clock": "INTRADAY_M1_LDN_UNION_NY_FLAT1955",
            "symbol": _pair,
            "pit_join_list": [f"{_pair}_M1_BIDASK_VOL", "WEEKLY_PROFILE",
                              "TZDATA_SESSIONS"],
            "cost_tier": "PANEL_VENUE_C1_MEASURED_PLUS_U2U3U4U5_DECLARED",
            "outcome_exposed_label": "CLASS_CANDIDATE_ANCESTRY_RHO_LABELLED",
            "cluster_id": "volprof_" + _shape,
            "params": {"shape": _mech, "unit_base_units": UNIT_FIXED_10K,
                       "cooldown_min": 60, "traverse_confirm_min": 60,
                       "tmax_min": 240, "dev_k": 3.0},
        })


# ---------------------------------------------------------------------------
# (b) Exemplar corpus legs (triage defaults, frozen)
# ---------------------------------------------------------------------------


class DonchianDailyLeg(BaseLeg):
    """USDJPY-S001 'Donchian 20/55 daily breakout' (T1_RULE_READY).

    Corpus (USDJPY.md S1): D1 close above Donchian-20 -> long (55 secondary
    entry retained as a declared parameter; the dry run trades the primary
    20 channel); stop 2xATR(20d) from the channel; trail opposite 10-day
    channel. Clock: daily decision at 00:00 UTC on completed prior UTC days
    (declared mechanization of 'D1 close').
    """

    wants_every_bar = False

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.entry_n = int(p.get("entry_donchian", 20))
        self.secondary_n = int(p.get("secondary_donchian", 55))
        self.trail_n = int(p.get("trail_donchian", 10))
        self.atr_n = int(p.get("atr_n", 20))
        self.stop_atr_mult = float(p.get("stop_atr_mult", 2.0))
        self.unit = int(p.get("unit_base_units", UNIT_FIXED_10K))
        self.d1: List[Dict] = []   # completed daily aggregates
        self.stop_level: Optional[float] = None

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        """Called once per completed UTC trading day (decision at 00:00)."""
        self.d1.append(bar)
        need = max(self.entry_n, self.secondary_n, self.atr_n + 1) + 1
        if len(self.d1) < need:
            return None
        closes = [b["close"] for b in self.d1]
        highs = [b["high"] for b in self.d1]
        lows = [b["low"] for b in self.d1]
        cur = closes[-1]
        hh20 = max(highs[-self.entry_n - 1:-1])
        ll20 = min(lows[-self.entry_n - 1:-1])
        atr = _atr_daily(highs[-self.atr_n - 1:], lows[-self.atr_n - 1:],
                         closes[-self.atr_n - 1:])
        opp_hi10 = max(highs[-self.trail_n:])
        opp_lo10 = min(lows[-self.trail_n:])
        snap = [_pit(f"{self.identity.symbol}_D1_CLOSE", bar["available"],
                     f"sha256:d1:{cur:.10f}", "P7D", True)]
        if self.desired_units > 0:
            if cur < opp_lo10 or (self.stop_level is not None
                                  and cur <= self.stop_level):
                self.desired_units = 0
                self.stop_level = None
                return LegDecision(vote=0, desired_units=0,
                                   reason_code="DONCHIAN_TRAIL_EXIT",
                                   order_kind="CLOSE",
                                   feature_pit_snapshot=snap)
            return None
        if self.desired_units < 0:
            if cur > opp_hi10 or (self.stop_level is not None
                                  and cur >= self.stop_level):
                self.desired_units = 0
                self.stop_level = None
                return LegDecision(vote=0, desired_units=0,
                                   reason_code="DONCHIAN_TRAIL_EXIT",
                                   order_kind="CLOSE",
                                   feature_pit_snapshot=snap)
            return None
        if cur > hh20:
            self.stop_level = hh20 - self.stop_atr_mult * atr
            return self._long(snap)
        if cur < ll20:
            self.stop_level = ll20 + self.stop_atr_mult * atr
            return self._short(snap)
        return None

    def _long(self, snap):
        self.desired_units = self.unit
        return LegDecision(vote=1, desired_units=self.unit,
                           reason_code="DONCHIAN20_BREAK_LONG",
                           order_kind="OPEN", feature_pit_snapshot=snap)

    def _short(self, snap):
        self.desired_units = -self.unit
        return LegDecision(vote=-1, desired_units=-self.unit,
                           reason_code="DONCHIAN20_BREAK_SHORT",
                           order_kind="OPEN", feature_pit_snapshot=snap)


class WeekdayGateLeg(BaseLeg):
    """GBPUSD-S027 'weekday vol filter' (T1_RULE_READY).

    Corpus (GBPUSD.md S27): Tue-Thu breakout-reliable / Mon-Fri MR-biased
    meta-gate. Mechanized as a leg (declared default): Tue-Thu take the
    prior day's sign (trend side); Mon/Fri take the opposite (MR side);
    flat on zero prior-day move. Clock: daily 00:00 UTC.
    """

    wants_every_bar = False

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        self.unit = int(identity.params.get("unit_base_units",
                                            UNIT_FIXED_10K))
        self.prev_close: Optional[float] = None
        self.prev_day: Optional[dt.date] = None

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        close = bar["close"]
        snap = [_pit(f"{self.identity.symbol}_D1_CLOSE", bar["available"],
                     f"sha256:d1:{close:.10f}", "P7D", True)]
        decision_day = bar["available"] + dt.timedelta(days=1)
        wd = decision_day.weekday()  # 0=Mon .. 4=Fri
        decision: Optional[LegDecision] = None
        if self.prev_close is not None and close != self.prev_close:
            trend_side = 1 if close > self.prev_close else -1
            side = trend_side if wd in (1, 2, 3) else -trend_side
            self.desired_units = side * self.unit
            code = ("WEEKDAY_TREND_TUETHU" if wd in (1, 2, 3)
                    else "WEEKDAY_MR_MONFRI")
            decision = LegDecision(vote=side,
                                   desired_units=self.desired_units,
                                   reason_code=code, order_kind="ADJUST",
                                   feature_pit_snapshot=snap)
        elif self.desired_units != 0:
            self.desired_units = 0
            decision = LegDecision(vote=0, desired_units=0,
                                   reason_code="WEEKDAY_FLAT_NOMOVE",
                                   order_kind="CLOSE",
                                   feature_pit_snapshot=snap)
        self.prev_close = close
        return decision


class MacdExitLeg(BaseLeg):
    """EURUSD-S009 'MACD-histogram exhaustion exit' (T2_DEFAULTS_DECLARED).

    Corpus (EURUSD.md S9): enter trend via EMA alignment; exit on
    MACD-H(12,26,9) D dual divergence with price; coupling: only when vol
    percentile < 80. T2 declared defaults frozen here (disclosed):
    EMA alignment = EMA20>EMA50 and close>EMA20 (long; mirrored short);
    dual divergence = two successive MACD-H swing peaks with the second
    lower while price closes higher (exit-long; mirrored for shorts);
    vol percentile = 20d realized-vol percentile over trailing 252d < 80;
    single unit, full exit (the 2/3 split is a sizing rule, declared off).
    """

    wants_every_bar = False

    def __init__(self, identity: LegIdentity):
        super().__init__(identity)
        p = identity.params
        self.ema_fast = int(p.get("ema_fast", 20))
        self.ema_slow = int(p.get("ema_slow", 50))
        self.macd_fast = int(p.get("macd_fast", 12))
        self.macd_slow = int(p.get("macd_slow", 26))
        self.macd_signal = int(p.get("macd_signal", 9))
        self.vol_window = int(p.get("vol_window", 20))
        self.vol_pct_window = int(p.get("vol_pct_window", 252))
        self.vol_pct_max = float(p.get("vol_pct_max", 80.0))
        self.unit = int(p.get("unit_base_units", UNIT_FIXED_10K))
        self.closes: List[float] = []
        self.last_peak_i: Optional[int] = None
        self.last_peak_h: Optional[float] = None

    def on_daily_bar(self, bar: Dict) -> Optional[LegDecision]:
        self.closes.append(bar["close"])
        n_need = max(self.ema_slow, self.macd_slow + self.macd_signal,
                     self.vol_pct_window) + self.vol_window + 5
        if len(self.closes) < max(self.ema_slow + 2, self.macd_slow
                                  + self.macd_signal + 2):
            return None
        closes = np.asarray(self.closes, dtype=np.float64)
        snap = [_pit(f"{self.identity.symbol}_D1_CLOSE", bar["available"],
                     f"sha256:d1:{closes[-1]:.10f}", "P7D", True)]
        ema_f = _ema(closes, self.ema_fast)
        ema_s = _ema(closes, self.ema_slow)
        macd_h = _macd_hist(closes, self.macd_fast, self.macd_slow,
                            self.macd_signal)
        # vol percentile gate (declared default)
        vol_ok = True
        if len(closes) >= self.vol_window + 2:
            rets = np.diff(np.log(closes[-(self.vol_window + 1):]))
            rv = float(np.std(rets))
            if len(closes) >= n_need:
                r_all = np.diff(np.log(closes))
                vols = np.lib.stride_tricks.sliding_window_view(
                    r_all, self.vol_window)
                rvs = np.std(vols, axis=1)
                pct = 100.0 * float((rvs < rv).sum()) / len(rvs)
                vol_ok = pct < self.vol_pct_max
        aligned_long = ema_f[-1] > ema_s[-1] and closes[-1] > ema_f[-1]
        aligned_short = ema_f[-1] < ema_s[-1] and closes[-1] < ema_f[-1]
        if self.desired_units != 0:
            if self._divergence(macd_h, closes, self.desired_units > 0):
                self.desired_units = 0
                return LegDecision(vote=0, desired_units=0,
                                   reason_code="MACDH_DUAL_DIVERGENCE_EXIT",
                                   order_kind="CLOSE",
                                   feature_pit_snapshot=snap)
            return None
        if not vol_ok:
            return None
        if aligned_long:
            self.desired_units = self.unit
            return LegDecision(vote=1, desired_units=self.unit,
                               reason_code="EMA_ALIGN_LONG", order_kind="OPEN",
                               feature_pit_snapshot=snap)
        if aligned_short:
            self.desired_units = -self.unit
            return LegDecision(vote=-1, desired_units=-self.unit,
                               reason_code="EMA_ALIGN_SHORT",
                               order_kind="OPEN",
                               feature_pit_snapshot=snap)
        return None

    def _divergence(self, macd_h: np.ndarray, closes: np.ndarray,
                    long: bool) -> bool:
        """Two successive MACD-H swing peaks, second weaker, price higher
        (long exit); mirrored for shorts. Swing peak = local max/min over a
        5-bar window (declared default)."""
        k = 5
        n = len(macd_h)
        if n < 2 * k + 2:
            return False
        peaks = []
        for i in range(k, n - k):
            w = macd_h[i - k:i + k + 1]
            if long and macd_h[i] == w.max():
                peaks.append((i, float(macd_h[i])))
            if not long and macd_h[i] == w.min():
                peaks.append((i, float(macd_h[i])))
        if len(peaks) < 2:
            return False
        (i1, h1), (i2, h2) = peaks[-2], peaks[-1]
        if i2 - i1 < k:
            return False
        if long:
            return h2 < h1 and closes[i2] > closes[i1]
        return h2 > h1 and closes[i2] < closes[i1]


# ---------------------------------------------------------------------------
# numeric helpers
# ---------------------------------------------------------------------------


def _ema(x: np.ndarray, n: int) -> np.ndarray:
    alpha = 2.0 / (n + 1.0)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = alpha * x[i] + (1 - alpha) * out[i - 1]
    return out


def _macd_hist(closes: np.ndarray, fast: int, slow: int,
               signal: int) -> np.ndarray:
    ef = _ema(closes, fast)
    es = _ema(closes, slow)
    macd = ef - es
    sig = _ema(macd, signal)
    return macd - sig


def _atr_daily(highs: List[float], lows: List[float],
               closes: List[float]) -> float:
    trs = []
    for i in range(1, len(highs)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    return float(np.mean(trs)) if trs else 0.0


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


EXEMPLAR_DEFAULT_CONFIGS = [
    {
        "cycle_id": "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1",
        "sleeve_id": "POOL_B_TRIAGE",
        "corpus_gid": "USDJPY-S001",
        "family_id": "A-TREND",
        "mech_key": "donchian_breakout",
        "clock": "DAILY_00UTC_M1FILL",
        "symbol": "USDJPY",
        "pit_join_list": ["USDJPY_D1_AGGREGATE"],
        "cost_tier": "PANEL_VENUE_C1_MEASURED_PLUS_U2U3U4U5_DECLARED",
        "outcome_exposed_label": "FAMILY_HISTORY_NEGATIVE",
        "cluster_id": "trend_daily",
        "params": {"entry_donchian": 20, "secondary_donchian": 55,
                   "trail_donchian": 10, "atr_n": 20, "stop_atr_mult": 2.0,
                   "unit_base_units": UNIT_FIXED_10K},
    },
    {
        "cycle_id": "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1",
        "sleeve_id": "POOL_B_TRIAGE",
        "corpus_gid": "GBPUSD-S027",
        "family_id": "E-SESSION",
        "mech_key": "weekday_meta_gate",
        "clock": "DAILY_00UTC_M1FILL",
        "symbol": "GBPUSD",
        "pit_join_list": ["GBPUSD_D1_AGGREGATE", "TZDATA_WEEKDAYS"],
        "cost_tier": "PANEL_VENUE_C1_MEASURED_PLUS_U2U3U4U5_DECLARED",
        "outcome_exposed_label": "FAMILY_HISTORY_NEGATIVE",
        "cluster_id": "calendar_weekday",
        "params": {"unit_base_units": UNIT_FIXED_10K},
    },
    {
        "cycle_id": "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1",
        "sleeve_id": "POOL_B_TRIAGE",
        "corpus_gid": "EURUSD-S009",
        "family_id": "A-TREND",
        "mech_key": "macd_divergence_exit",
        "clock": "DAILY_00UTC_M1FILL",
        "symbol": "EURUSD",
        "pit_join_list": ["EURUSD_D1_AGGREGATE"],
        "cost_tier": "PANEL_VENUE_C1_MEASURED_PLUS_U2U3U4U5_DECLARED",
        "outcome_exposed_label": "F0_INDIVIDUAL_REJECT",
        "cluster_id": "trend_daily",
        "params": {"ema_fast": 20, "ema_slow": 50, "macd_fast": 12,
                   "macd_slow": 26, "macd_signal": 9, "vol_window": 20,
                   "vol_pct_window": 252, "vol_pct_max": 80.0,
                   "unit_base_units": UNIT_FIXED_10K},
        "declared_defaults_note": (
            "T2_DEFAULTS_DECLARED: EMA-alignment entry set, 5-bar swing "
            "dual-divergence definition, 252d vol-percentile window, full "
            "exit (2/3 split declared off) - frozen in this config"),
    },
]

_LEG_CLASSES = {
    ("POOL_B_TRIAGE", "donchian_breakout"): DonchianDailyLeg,
    ("POOL_B_TRIAGE", "weekday_meta_gate"): WeekdayGateLeg,
    ("POOL_B_TRIAGE", "macd_divergence_exit"): MacdExitLeg,
}


def build_leg(cfg: Dict) -> BaseLeg:
    ident = make_identity(cfg)
    key = (ident.sleeve_id, ident.mech_key)
    if ident.sleeve_id == VOLPROF_SLEEVE:
        return VolprofLeg(ident)
    if key in _LEG_CLASSES:
        return _LEG_CLASSES[key](ident)
    raise LegError(f"no implementation registered for {key}")


def default_leg_configs() -> List[Dict]:
    """The 9 VOLPROF class candidates + 3 exemplar corpus legs."""
    return VOLPROF_DEFAULT_CONFIGS + EXEMPLAR_DEFAULT_CONFIGS
