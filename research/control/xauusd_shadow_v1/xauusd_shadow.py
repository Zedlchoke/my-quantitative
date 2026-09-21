"""XAUUSD-SHADOW-V1 sleeve engine (plans/PLAN_xauusd_shadow_v1.md §2).

INTERNAL SHADOW ONLY: virtual ledger, TARGET_INTENT records, no orders,
no broker, no external venue writes, no new credentials (the ONLY key
used is the pre-existing EODHD_API_KEY, never echoed).  Every rendered
number carries SHADOW_OBSERVATION_ONLY semantics.

Frozen spec (daily bars — F1 re-freeze 2026-09-21 after the entitlement
probe: EODHD /eod/XAUUSD.FOREX permitted, intraday 403):
  swing level    fractal ±5 daily bars, confirmed 5 bars later; most
                 recent confirmed; tie |extreme−close_t| larger wins
  conditions     |close−L| ≤ 0.3×ATR14; right side of L; EMA9>EMA21
                 (long)/< (short); ATR14 ≥ 0.15% of close AND ≥ 1.25×
                 trailing-100-bar ATR14 median
  entry          next bar open ± half-spread; costs 4 bps round trip
  exits          EMA cross against (bar close → next open) / stop
                 1×ATR14_entry (completed-bar touch → next open) /
                 time stop 20 completed bars / session end
  sizing         10% of sleeve equity notional, one position
  warmup         200 completed bars (REPLAY_NOT_PROSPECTIVE for history;
                 decisions only on bars closing AFTER SHADOW_START)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

EOD_URL = "https://eodhd.com/api/eod/XAUUSD.FOREX"
WARMUP = 200
SWING_W = 5
SWING_CONFIRM = 5
EMA_F, EMA_S = 9, 21
VOL_PCT_MIN, VOL_MED_MULT = 0.0015, 1.25
STOP_ATR, TIME_STOP_BARS = 1.0, 20
COST_RT_BPS = 4.0
NOTIONAL_FRAC = 0.10
INITIAL_EQUITY = 100_000.0
POLL_S = 3600
#: CME Globex metals holiday dates (published calendar, embedded at
#: freeze; source: cmegroup.com holiday schedule 2026) — a missing
#: weekday bar NOT in this list is a DATA_GAP (fail-closed recorded).
CME_HOLIDAYS_2026 = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
    "2026-05-25", "2026-07-03", "2026-09-07", "2026-11-26",
    "2026-12-25",
}


def iso_z() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def chain_hash(prev: str, row: dict) -> str:
    return hashlib.sha256(
        (prev + json.dumps(row, sort_keys=True,
                           separators=(",", ":"))).encode()).hexdigest()


# ------------------------------------------------------------- indicators

def ema(values, n):
    out = [None] * len(values)
    k = 2.0 / (n + 1)
    prev = None
    for i, v in enumerate(values):
        prev = v if prev is None else v * k + prev * (1 - k)
        out[i] = prev if i >= n - 1 else None
    return out


def wilder_atr(highs, lows, closes, n=14):
    out = [None] * len(closes)
    trs = []
    for i in range(len(closes)):
        if i == 0:
            trs.append(highs[i] - lows[i])
            continue
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    prev = None
    for i, tr in enumerate(trs):
        if i == n - 1:
            prev = sum(trs[:n]) / n
            out[i] = prev
        elif i >= n:
            prev = (prev * (n - 1) + tr) / n
            out[i] = prev
    return out


def swing_levels(highs, lows):
    """Confirmed fractal swing levels: list of (confirm_index, kind,
    level) — kind 'high'|'low' — most recent last (no lookahead)."""
    out = []
    n = len(highs)
    for i in range(SWING_W, n - SWING_W):
        win_h = highs[i - SWING_W:i + SWING_W + 1]
        win_l = lows[i - SWING_W:i + SWING_W + 1]
        is_h = highs[i] == max(win_h) and win_h.count(highs[i]) == 1
        is_l = lows[i] == min(win_l) and win_l.count(lows[i]) == 1
        if is_h or is_l:
            out.append((i + SWING_CONFIRM,
                        "high" if is_h else "low",
                        highs[i] if is_h else lows[i]))
    return out


# ------------------------------------------------------------------ engine

class SleeveEngine:
    """Pure decision engine over completed daily bars (deterministic,
    no lookahead: at bar t it reads only bars <= t)."""

    def __init__(self):
        self.position = None          # dict when open
        self.events = []

    def on_bar(self, i, bars):
        """bars: list of dicts (date,o,h,l,c) up to and including i."""
        b = bars[i]
        pos = self.position
        if pos is not None:
            # exits first (completed-bar evaluation, fill next open)
            if pos["side"] == 1 and b["l"] <= pos["stop"]:
                exit_reason = "stop"          # completed-bar LOW touch
            elif pos["side"] == -1 and b["h"] >= pos["stop"]:
                exit_reason = "stop"          # completed-bar HIGH touch
            else:
                exit_reason = None
            if exit_reason is None and i >= pos["time_stop_bar"]:
                exit_reason = "time_stop"
            if exit_reason is None:
                e = self._ema_at(i, bars)
                if e is not None:
                    if (pos["side"] == 1 and e[0] <= e[1]) or \
                            (pos["side"] == -1 and e[0] >= e[1]):
                        exit_reason = "ema_cross"
            if exit_reason is not None:
                self.events.append({
                    "type": "EXIT_INTENT", "bar": b["date"], "reason":
                    exit_reason, "side": pos["side"],
                    "ref_price": b["c"]})
                self.position = None
                return None
        if pos is not None:
            return None
        if i < WARMUP:
            return None
        e9, e21 = self._ema_at(i, bars)
        atr = self._atr_at(i, bars)
        if e9 is None or e21 is None or atr is None:
            return None
        close = b["c"]
        # volatility floor
        med = self._atr_median100(i, bars)
        if med is None:
            return None
        if not (atr >= VOL_PCT_MIN * close and atr >= VOL_MED_MULT * med):
            return None
        # most recent CONFIRMED swing level as of bar i; when a high
        # and a low confirm on the same bar, the larger |extreme -
        # close_t| wins (plan §2 tie-break, reference bar pinned)
        all_lv = [x for x in swing_levels(
            [y["h"] for y in bars[:i + 1]],
            [y["l"] for y in bars[:i + 1]]) if x[0] <= i]
        if not all_lv:
            return None
        last_conf = max(x[0] for x in all_lv)
        cands = [x for x in all_lv if x[0] == last_conf]
        kind, lv = max(
            cands, key=lambda x: abs(x[2] - close))
        if abs(close - lv) > 0.3 * atr:
            return None
        if kind == "low" and close >= lv and e9 > e21:
            side = 1
        elif kind == "high" and close <= lv and e9 < e21:
            side = -1
        else:
            return None
        self.position = {
            "side": side, "entry_bar": i, "time_stop_bar": i + TIME_STOP_BARS,
            "stop": close - side * STOP_ATR * atr,
            "ref_close": close, "level": lv, "atr_entry": atr}
        self.events.append({
            "type": "ENTRY_INTENT", "bar": b["date"], "side": side,
            "level": lv, "close": close, "atr": atr})
        return self.position

    def _ema_at(self, i, bars):
        c = [x["c"] for x in bars[:i + 1]]
        if len(c) < EMA_S:
            return None
        a = ema(c, EMA_F)[i]
        b = ema(c, EMA_S)[i]
        return (a, b) if (a is not None and b is not None) else None

    def _atr_at(self, i, bars):
        return wilder_atr([x["h"] for x in bars[:i + 1]],
                          [x["l"] for x in bars[:i + 1]],
                          [x["c"] for x in bars[:i + 1]])[i]

    def _atr_median100(self, i, bars):
        atrs = wilder_atr([x["h"] for x in bars[:i + 1]],
                          [x["l"] for x in bars[:i + 1]],
                          [x["c"] for x in bars[:i + 1]])
        vals = sorted(v for v in atrs[max(0, i - 99):i + 1]
                      if v is not None)
        if not vals:
            return None
        m = len(vals)
        return vals[m // 2] if m % 2 else 0.5 * (vals[m // 2 - 1]
                                                 + vals[m // 2])


# --------------------------------------------------------------- ledger

class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.prev = "GENESIS"
        self.rows = []
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.rows.append(row)
                    self.prev = row["chain"]

    def append(self, row: dict) -> dict:
        row = dict(row)
        row["utc"] = iso_z()
        row["chain"] = chain_hash(self.prev, row)
        self.prev = row["chain"]
        with open(self.path, "a") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.rows.append(row)
        return row

    def equity(self, price: float | None) -> float | None:
        """Equity from fills + open-position mark (UNAVAILABLE_FAIL_CLOSED
        -> None when price is None and a position is open)."""
        eq = INITIAL_EQUITY
        pos = None
        for r in self.rows:
            if r["type"] == "FILL":
                if r["action"] == "ENTRY":
                    pos = r
                else:
                    gross = (r["price"] / pos["price"] - 1.0) * r["side"]
                    notional = pos["notional"]
                    eq += notional * gross - notional * COST_RT_BPS / 1e4
                    pos = None
        if pos is not None:
            if price is None:
                return None
            gross = (price / pos["price"] - 1.0) * pos["side"]
            eq += pos["notional"] * gross - pos["notional"] \
                * COST_RT_BPS / 1e4
        return eq


# ------------------------------------------------------------- collector

def fetch_daily_bars(key: str, last_n: int = 300) -> list:
    url = f"{EOD_URL}?api_token={key}&fmt=json&last={last_n}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "xauusd-shadow-keyless-read/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    rows = json.loads(raw)
    bars = [{"date": str(x["date"])[:10], "o": float(x["open"]),
             "h": float(x["high"]), "l": float(x["low"]),
             "c": float(x["adjusted_close"])} for x in rows]
    bars.sort(key=lambda b: b["date"])
    return bars


def market_gap_check(bars) -> list:
    """Missing expected weekday bars (CME calendar) — recorded, never
    imputed."""
    have = {b["date"] for b in bars}
    gaps = []
    for b in bars:
        from datetime import date, timedelta
        d0 = date.fromisoformat(b["date"])
        prev = d0 - timedelta(days=1)
        while prev.weekday() > 4 or prev.isoformat() in CME_HOLIDAYS_2026:
            prev -= timedelta(days=1)
        if prev.isoformat() not in have and prev.isoformat() >= "2026-09-01":
            gaps.append(prev.isoformat())
    return sorted(set(gaps))


# ------------------------------------------------------------------ loop

def run(runtime_root: Path, shadow_start: str, once: bool = False):
    key = os.environ.get("EODHD_API_KEY", "")
    if not key:
        raise SystemExit("EODHD_API_KEY missing (never echoed)")
    rt = Path(runtime_root)
    rt.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(rt / "ledger.jsonl")
    engine = SleeveEngine()
    status = {"pid": os.getpid(), "shadow_start": shadow_start,
              "namespace": "PROSPECTIVE", "label":
              "XAUUSD-SHADOW-V1 / SHADOW_OBSERVATION_ONLY / NOT A "
              "PROFITABILITY CLAIM / COST MODEL UNMEASURED-CONSERVATIVE",
              "initial_equity_usd": INITIAL_EQUITY}
    while True:
        raw_chain_prev = "GENESIS"
        rawp = Path(runtime_root) / "raw_bars.jsonl"
        if rawp.exists():
            for line in rawp.read_text().splitlines():
                if line.strip():
                    raw_chain_prev = json.loads(line)["chain"]
        try:
            bars = fetch_daily_bars(key)
            gaps = market_gap_check(bars)
            last_raw = bars[-1]
            _row = {"type": "RAW_BARS_SNAPSHOT", "n_bars": len(bars),
                    "last_date": last_raw["date"], "utc": iso_z()}
            _row["chain"] = chain_hash(raw_chain_prev, _row)
            with open(rawp, "a") as f:
                f.write(json.dumps(_row, sort_keys=True) + "\n")
            last = bars[-1]
            # Fill law (plan §2): decision on a COMPLETED bar close
            # fills at the NEXT bar's open.  Deterministic replay of the
            # engine over bars[0 .. n-2] (the newest bar n-1 is still
            # forming-until-next-poll; its own intent fills next loop at
            # the then-newest open).  History before shadow_start is
            # warmup REPLAY only (never reported as prospective).
            engine.position = None
            engine.events = []
            for i in range(max(0, len(bars) - 2), len(bars) - 1):
                pass  # (no-op guard; replay below is authoritative)
            start_i = 0 if len(bars) <= WARMUP + 2 else WARMUP
            # replay from warmup so swing/EMA/ATR state is identical
            # every loop; only intents on bars AFTER shadow_start may
            # produce ledger fills
            engine.position = None
            engine.events = []
            for i in range(start_i, max(start_i + 1, len(bars) - 1)):
                if bars[i]["date"] <= shadow_start:
                    continue          # warmup replay, no ledger effects
                engine.on_bar(i, bars)
            price = last["o"]         # fill at the newest bar's OPEN
            fill_bar = bars[-2]["date"] if len(bars) >= 2 else None
            for ev in engine.events:
                if ev["bar"] < (fill_bar or ev["bar"]):
                    if not any(r.get("bar") == ev["bar"] and r["type"]
                               in ("FILL", "UNFILLED_GAP")
                               for r in ledger.rows):
                        ledger.append({          # F-MED-2: never silent
                            "type": "UNFILLED_GAP", "bar": ev["bar"],
                            "intent": ev["type"], "reason":
                            "poll gap: fill window passed unfilled"})
                    continue
                if ev["bar"] != fill_bar:
                    continue
                if ev["type"] == "ENTRY_INTENT" and \
                        not any(r.get("bar") == ev["bar"] and
                                r["type"] == "FILL" and
                                r["action"] == "ENTRY"
                                for r in ledger.rows):
                    notional = NOTIONAL_FRAC * (
                        ledger.equity(price) or INITIAL_EQUITY)
                    ledger.append({
                        "type": "FILL", "action": "ENTRY",
                        "bar": ev["bar"], "side": ev["side"],
                        "price": price, "notional": round(notional, 2),
                        "level": ev["level"], "atr": round(ev["atr"], 4)})
                if ev["type"] == "EXIT_INTENT" and \
                        not any(r.get("bar") == ev["bar"] and
                                r["type"] == "FILL" and
                                r["action"] == "EXIT"
                                for r in ledger.rows):
                    ledger.append({
                        "type": "FILL", "action": "EXIT",
                        "bar": ev["bar"], "side": ev["side"],
                        "price": price, "reason": ev["reason"]})
            ledger.append({"type": "MARK_TO_MARKET",
                           "bar": last["date"], "close": last["c"],
                           "equity": ledger.equity(last["c"])})
            for ev in engine.events:
                if ev["bar"] == fill_bar:
                    ledger.append({"type": "TARGET_INTENT",
                                   "intent": ev["type"],
                                   "bar": ev["bar"], "side": ev["side"]})
            status.update({
                "last_bar": last["date"], "last_close": last["c"],
                "n_bars": len(bars), "data_gaps": gaps,
                "position": "OPEN" if any(
                    r["type"] == "FILL" and r["action"] == "ENTRY"
                    and not any(x["type"] == "FILL"
                                and x["action"] == "EXIT"
                                and x["bar"] > r["bar"]
                                for x in ledger.rows)
                    for r in ledger.rows) else "FLAT",
                "equity_usd": ledger.equity(last["c"]),
                "ledger_rows": len(ledger.rows),
                "last_loop_utc": iso_z(), "last_error": None})
        except Exception as e:                      # noqa: BLE001
            status.update({"last_error": f"{type(e).__name__}: {e}",
                           "last_loop_utc": iso_z(),
                           "equity_usd": None,       # F-MED-6: no stale
                           "last_close": None})      # marks on outage
        (rt / "status.json").write_text(
            json.dumps(status, indent=1, sort_keys=True) + "\n")
        if once:
            return status
        time.sleep(POLL_S)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", default="results/xauusd_shadow_v1")
    ap.add_argument("--shadow-start",
                    default=datetime.now(timezone.utc)
                    .strftime("%Y-%m-%d"))
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    run(Path(a.runtime_root), a.shadow_start, once=a.once)
