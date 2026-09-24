#!/usr/bin/env python
"""PROSPECTIVE-SHADOW-V1 / sleeve 4 BTC4H-BANDRIDGE — forward ledger updater.

Shadow law (plan section 2, binding): read market data only AFTER the
activation timestamp; compute the position the sleeve wants; record fills,
fees, funding, equity in an append-only virtual ledger; send NO order;
require no API key (Binance Vision keyless + public fapi fundingRate GET).

Frozen sleeve law (= the S0-characterized BANDRIDGE, NEVER edited while the
shadow lives):
  gate  = C3 band state: ON when close > SMA200(H4)*1.03, OFF when close <
          SMA200(H4)*0.97 (hysteretic; NO extra dilation)
  book  = PSV1 Donchian 30/15, min-hold 12, max-hold 450, enter only while
          gate ON; GATE_INACTIVE exit when gate OFF
  exec  = decision at H4 close, fill at next H4 open; 6 bps/side full stack
          (tier 1.0 for the shadow book); funding measured per settlement on
          held notional (Vision monthly archive; fapi public REST for the
          unresolved tail); NO leverage (fraction 1.0 of the sleeve's own
          $100,000); no fold law forward (continuous book)
  capital = $100,000 virtual, seeded at activation
ACTIVATION = 2026-09-24T00:00:00Z. Nothing before activation may enter the
ledger (forward-only; no backfill as prospective performance).

Usage: run periodically (cron/manual). Idempotent, append-only.
  .venv/bin/python scripts/update_shadow_bandridge.py
"""
from __future__ import annotations

import datetime as dt
import io
import json
import struct
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "ledger.jsonl"
STATE = HERE / "state.json"
ACTIVATION_MS = int(dt.datetime(2026, 9, 24, tzinfo=dt.timezone.utc).timestamp() * 1000)
H1_MS = 3_600_000
H4_MS = 4 * H1_MS
CAPITAL = 100_000.0
FEE = 6.0 / 1e4
BASE = "https://data.binance.vision/data/futures/um"
FAPI_FUNDING = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={ms}&limit=1000"
UA = "my-quantitative-research/1.0 (internal shadow; owner-authorized 2026-09-23; no orders)"


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"last_bucket_ms": ACTIVATION_MS - H4_MS, "equity": CAPITAL,
            "position": 0.0, "peak": None, "entry_ref": None, "state_gate": 0,
            "donch_state": 0, "bars_held": 0, "non_gate_run": 0, "filled": False,
            "pending": None}


def new_h1_bars(after_ms: int):
    """Vision 1h: monthly archives + daily tail. Returns list of (ms,o,h,l,c)."""
    rows = {}
    now = dt.datetime.now(dt.timezone.utc)
    y, m = 2020, 9  # monthly archive walked lazily from the staged horizon
    # monthly archives through last complete month
    ym = (now.year, now.month)
    yy, mm = 2020, 9
    while (yy, mm) < ym:
        url = f"{BASE}/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{yy:04d}-{mm:02d}.zip"
        try:
            raw = fetch(url)
        except Exception:
            raw = None
        if raw:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                txt = z.read(z.namelist()[0]).decode()
            for ln in txt.strip().split("\n"):
                f = ln.split(",")
                if not f[0].isdigit():
                    continue
                t = int(f[0])
                if t >= after_ms - 800 * H4_MS:  # warmup window guard
                    rows[t] = (t, float(f[1]), float(f[2]), float(f[3]), float(f[4]))
        mm += 1
        if mm == 13:
            yy, mm = yy + 1, 1
    # daily tail from the day after last state bucket
    day = dt.datetime.fromtimestamp(after_ms / 1000, tz=dt.timezone.utc).date()
    last = now.date()
    d = day - dt.timedelta(days=1)
    while d <= last:
        url = f"{BASE}/daily/klines/BTCUSDT/1h/BTCUSDT-1h-{d.isoformat()}.zip"
        try:
            raw = fetch(url)
        except Exception:
            raw = None
        if raw:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                txt = z.read(z.namelist()[0]).decode()
            for ln in txt.strip().split("\n"):
                f = ln.split(",")
                if not f[0].isdigit():
                    continue
                t = int(f[0])
                rows[t] = (t, float(f[1]), float(f[2]), float(f[3]), float(f[4]))
        d += dt.timedelta(days=1)
    return [rows[k] for k in sorted(rows)]


def funding_rate_for(ms: int) -> float:
    try:
        raw = fetch(FAPI_FUNDING.format(ms=ms - 120_000))
        data = json.loads(raw)
        for row in data:
            if abs(int(row["fundingTime"]) - ms) <= 60_000:
                return float(row["fundingRate"])
    except Exception:
        pass
    return 0.0  # fail-open on one settlement = disclosed undercharge risk; recorded


def h4_buckets(h1_rows):
    buckets = {}
    for (t, o, h, l, c) in h1_rows:
        b = t - t % H4_MS
        bk = buckets.setdefault(b, {"n": 0, "open": None, "high": -1e18, "low": 1e18, "close": None})
        bk["n"] += 1
        bk["open"] = o if bk["open"] is None else bk["open"]
        bk["high"] = max(bk["high"], h)
        bk["low"] = min(bk["low"], l)
        bk["close"] = c
    return {b: v for b, v in buckets.items() if v["n"] == 4}  # complete iff 4 aligned H1


def main():
    st = load_state()
    h1 = new_h1_bars(max(st["last_bucket_ms"] - 300 * H4_MS, ACTIVATION_MS - 300 * H4_MS))
    buckets = h4_buckets(h1)
    # warmup context: SMA200 + Donchian channels need history; recompute from
    # the frozen staged panel is overkill for the shadow — the state machine
    # carries its own rolling context forward deterministically.
    hist = sorted(b for b in buckets if b <= st["last_bucket_ms"])
    closes_ctx = [buckets[b]["close"] for b in hist[-200:]]
    channel_ctx = [buckets[b]["close"] for b in hist[-30:]]
    stop_ctx = [buckets[b]["close"] for b in hist[-15:]]

    out = []
    for b in sorted(buckets):
        if b <= st["last_bucket_ms"] or b < ACTIVATION_MS:
            continue
        bk = buckets[b]
        c = bk["close"]
        rec = {"ts_bucket_ms": b,
               "ts_utc": dt.datetime.fromtimestamp(b / 1000, tz=dt.timezone.utc).isoformat(),
               "open": bk["open"], "close": c, "gate_on": None, "decision": "FLAT"}
        # (1) settle a pending fill at THIS bar's open (decided at prior close)
        if st["pending"]:
            dpos = st["pending"]["side"] - st["position"]
            if abs(dpos) > 1e-12:
                fee = abs(dpos) * st["equity"] * FEE
                st["equity"] -= fee
                rec["fill"] = {"open": bk["open"], "dpos": dpos, "fee": round(fee, 2),
                               "reason": st["pending"].get("reason", "ENTRY")}
                if st["pending"]["side"] == 1.0:
                    st["peak"], st["entry_ref"], st["bars_held"], st["non_gate_run"] = bk["open"], bk["open"], 0, 0
            st["position"] = st["pending"]["side"]
            st["pending"] = None
        # (2) mark-to-market open->close on the held position
        if st["position"] > 0:
            st["peak"] = max(st["peak"], c)
            st["equity"] *= (1.0 + st["position"] * (c / bk["open"] - 1.0))
        # (3) funding at 00/08/16 UTC bucket opens on held notional
        if (b // H1_MS) % 8 == 0 and st["position"] > 0:
            pay = funding_rate_for(b) * st["position"] * st["equity"]
            st["equity"] -= pay
            rec["funding_paid"] = round(pay, 2)
        # (4) decision at THIS close -> pending fill at next bar open
        closes_ctx.append(c)
        sma = sum(closes_ctx[-200:]) / 200.0 if len(closes_ctx) >= 200 else None
        r = c / sma - 1.0 if sma else None
        if st["state_gate"] == 0:
            if r is not None and r > 0.03:
                st["state_gate"] = 1
        elif r is not None and r < -0.03:
            st["state_gate"] = 0
        gate_on = st["state_gate"] == 1
        rec["gate_on"] = gate_on
        ch30 = channel_ctx[-30:] if len(channel_ctx) >= 30 else None
        ch15 = stop_ctx[-15:] if len(stop_ctx) >= 15 else None
        if st["donch_state"] == 0:
            if gate_on and ch30 is not None and c > max(ch30):
                st["donch_state"] = 1
                st["pending"] = {"side": 1.0}
                rec["decision"] = "ENTRY"
        else:
            st["bars_held"] += 1
            st["non_gate_run"] = 0 if gate_on else st["non_gate_run"] + 1
            reason = None
            if ch15 is not None and c < min(ch15) and st["bars_held"] >= 12:
                reason = "DONCHIAN_STOP"
            if reason is None and not gate_on:
                reason = "GATE_INACTIVE"
            if reason is None and st["bars_held"] >= 450:
                reason = "MAX_HOLD"
            if reason:
                st["donch_state"] = 0
                st["pending"] = {"side": 0.0, "reason": reason}
                rec["decision"] = f"EXIT:{reason}"
            else:
                rec["decision"] = "HOLD"
        channel_ctx.append(c)
        stop_ctx.append(c)
        rec["equity_after"] = round(st["equity"], 2)
        out.append(json.dumps(rec, ensure_ascii=False))
        st["last_bucket_ms"] = b

    if out:
        with LEDGER.open("a") as f:
            for line in out:
                f.write(line + "\n")
    STATE.write_text(json.dumps(st, indent=1))
    print(f"appended {len(out)} records; last_bucket={st['last_bucket_ms']} "
          f"equity={st['equity']:.2f} position={st['position']}")


if __name__ == "__main__":
    main()
