"""RANGEFADE-2M shadow daemon (paper only — no broker, no orders).

Polls TrueFX indicative quotes every ~15s, maintains per-pair H1 bars
(seeded from the sha-verified Dukascopy corpus + bridge), evaluates the
frozen FX2-RANGEEXP-C3 signal per pair, simulates fills at the live
opposite quote for 1.5 lots, and writes atomic state + an append-only
journal. Fail-closed on stale quotes. See PLAN_fx_rangefade_2m_shadow_v1.md.
"""
import copy
import datetime as dt
import hashlib
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE.parent.parent / "EURUSD-OPEN-SEARCH-V2" / "scripts"))
sys.path.insert(0, str(HERE.parent.parent / "FX-MAJORS-SEARCH-V1" / "scripts"))
import engine as E  # noqa: E402  (frozen semantics v1 + pip param)
import v2_lib as V  # noqa: E402  (frozen families)

SEED_DERIVED = {
    "EURUSD": HERE.parent / "data_local" / "EURUSD",  # own corpus incl. 2026-07..09 bridge
    "GBPUSD": Path("/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD"),
    "GBPUSD_note": "sha-verified FX-MAJORS corpus incl. 2026-07..09 bridge",
}
PAIRS = {"EURUSD": {"pip": 1e-4, "dollars_per_pip_per_lot": 10.0},
         "GBPUSD": {"pip": 1e-4, "dollars_per_pip_per_lot": 10.0}}
LOTS = 1.5
SEED_EQUITY = 100_000.0
POLL_SEC = 15
STALE_SEC = 15 * 60
STATE = ROOT / "shadow_state.json"
JOURNAL = ROOT / "shadow_journal.jsonl"
HEARTBEAT = ROOT / "daemon_heartbeat.json"
TRUEFX = "https://webrates.truefx.com/rates/connect.html?f=csv&c=EUR/USD,GBP/USD"


def log(event, **kw):
    rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "event": event, **kw}
    with open(JOURNAL, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def atomic_write(path, text):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def truefx_poll():
    req = urllib.request.Request(TRUEFX, headers={"User-Agent": "phorec-shadow/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        rows = {}
        now = time.time()
        for line in r.read().decode().strip().splitlines():
            f = line.split(",")
            if len(f) < 6 or "/" not in f[0]:
                continue
            pair = f[0].replace("/", "")
            if pair not in PAIRS:
                continue
            ts_ms = int(f[1])
            bid = float(f[2]) + int(f[3]) * 1e-5
            ask = float(f[4]) + int(f[5]) * 1e-5
            rows[pair] = {"bid": bid, "ask": ask, "ts": ts_ms / 1000.0, "age": now - ts_ms / 1000.0}
        return rows


def seed_bars(pair):
    """H1 history from the sha-verified Dukascopy derived parquet."""
    h1 = pd.read_parquet(Path(SEED_DERIVED[pair]) / "derived" / "bars1h.parquet")
    h1 = h1.reset_index()
    df = pd.DataFrame({
        "ts": h1["ts"], "b_o": h1["b_o"], "b_h": h1["b_h"], "b_l": h1["b_l"], "b_c": h1["b_c"],
        "a_o": h1["a_o"], "a_c": h1["a_c"]})
    df["s_open"] = df["a_o"] - df["b_o"]
    df["s_close"] = df["a_c"] - df["b_c"]
    return df


def plane_from_df(df):
    return V.H1Plane(df)


def targets_from_df(df, pip):
    """Frozen signal: FX2-RANGEEXP-C3 on the full H1 series."""
    plane = plane_from_df(df)
    return V.f_rangeexp(plane, 0.3, 0.7, False), plane  # unit-free params


class PairBook:
    def __init__(self, pair, pip):
        self.pair, self.pip = pair, pip
        self.df = seed_bars(pair)              # committed H1 history
        self.pos = 0                            # -1/0/+1 (units of LOTS sign)
        self.entry_px = None
        self.entry_ts = None
        self.realized_usd = 0.0
        self.fills = 0
        self.live_bar = None                    # dict for the forming H1 bar
        self.last_target = 0
        self.parity = None

    def on_closed_bar(self, bar):
        """bar: dict(b_o..a_c, ts). Append, recompute target (signal on CLOSED bar)."""
        self.df = pd.concat([self.df, pd.DataFrame([bar])], ignore_index=True)
        tgt, _ = targets_from_df(self.df, self.pip)
        self.last_target = int(tgt[-1])
        self.parity = "PASS"

    def desired_now(self):
        """Position wanted for the bar that just opened (fill allowed hour<=18)."""
        if len(self.df) == 0:
            return 0
        h = int((int(self.df["ts"].iloc[-1]) // 3600) % 24)
        if h >= 19:
            return 0
        return self.last_target


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def main():
    books = {p: PairBook(p, m["pip"]) for p, m in PAIRS.items()}
    realized_usd = 0.0
    day_key = None
    day_start_realized = 0.0
    marks = {}
    data_stale = True
    parity_rec = None

    # launch parity self-test: daemon signal path vs frozen library on identical bars
    for p, b in books.items():
        tgt_daemon, _ = targets_from_df(b.df, b.pip)
        tgt_frozen = V.f_rangeexp(plane_from_df(b.df), 0.3, 0.7, False)
        ok = np.array_equal(tgt_daemon, tgt_frozen)
        parity_rec = log("parity_selftest", pair=p, result="PASS" if ok else "FAIL")
        if not ok:
            raise SystemExit("FAIL_CLOSED: parity self-test failed")

    log("shadow_start", strategy="RANGEFADE-2M", pairs=list(PAIRS), lots=LOTS, seed=SEED_EQUITY)

    while True:
        try:
            marks = truefx_poll()
            data_stale = any(m["age"] > STALE_SEC for m in marks.values()) or len(marks) < len(PAIRS)
        except Exception as e:
            data_stale = True
            marks = {}
        now = now_utc()
        hour = now.hour
        dk = now.strftime("%Y-%m-%d")
        if dk != day_key:
            day_key = dk
            day_start_realized = realized_usd

        for p, b in books.items():
            mk = marks.get(p)
            if mk is None:
                continue
            mid = (mk["bid"] + mk["ask"]) / 2
            # form the live H1 bar from the live mid
            h0 = int(now.replace(minute=0, second=0, microsecond=0).timestamp())
            if b.live_bar is None or b.live_bar["ts"] != h0:
                # hour rolled: the previous live bar is now CLOSED
                if b.live_bar is not None:
                    b.on_closed_bar(b.live_bar)
                    closed_ts = int(b.live_bar["ts"])
                    closed_hour = (closed_ts // 3600) % 24
                    # force-flat at the close of the 19:00 bar (= 20:00 wall clock)
                    if closed_hour == 19 and b.pos != 0:
                        px = mk["bid"] if b.pos > 0 else mk["ask"]
                        pnl = (px - b.entry_px) * b.pos * LOTS / b.pip * PAIRS[p]["dollars_per_pip_per_lot"]
                        realized_usd += pnl
                        b.realized_usd += pnl
                        log("force_flat", pair=p, exit_px=px, pnl_usd=round(pnl, 2),
                            realized_total=round(b.realized_usd, 2))
                        b.pos, b.entry_px, b.entry_ts = 0, None, None
                    # signal for the bar that just opened
                    want = b.desired_now()
                    if want != b.pos and hour <= 18 and not data_stale:
                        # marketable: opening long buys at ask; opening short sells at bid;
                        # closing long sells at bid; closing short buys at ask
                        if b.pos != 0:
                            px = mk["bid"] if b.pos > 0 else mk["ask"]
                            pnl = (px - b.entry_px) * b.pos * LOTS / b.pip * PAIRS[p]["dollars_per_pip_per_lot"]
                            realized_usd += pnl
                            b.realized_usd += pnl
                            log("fill_close", pair=p, exit_px=px, pnl_usd=round(pnl, 2), reason="signal")
                            b.pos = 0
                        if want != 0:
                            b.pos, b.entry_px, b.entry_ts = want, (mk["ask"] if want > 0 else mk["bid"]), int(now.timestamp())
                            b.fills += 1
                            log("fill_open", pair=p, dir=want, entry_px=b.entry_px, lots=LOTS)
                b.live_bar = {"ts": h0, "b_o": mk["bid"], "b_h": max(mid, mk["ask"]),
                              "b_l": min(mid, mk["bid"]), "b_c": mid,
                              "a_o": mk["ask"], "a_c": mk["ask"]}
            # update forming bar
            lb = b.live_bar
            lb["b_h"] = max(lb["b_h"], mk["bid"]); lb["b_l"] = min(lb["b_l"], mk["bid"])
            lb["b_c"] = mid; lb["a_c"] = mk["ask"]

        sleeves = {}
        unreal_total = 0.0
        gross = 0.0
        for p, b in books.items():
            mk = marks.get(p)
            unrl = 0.0
            pos_str = "FLAT"
            if mk is None:
                pos_str = "NO_MARK"
            elif b.pos != 0:
                px = mk["bid"] if b.pos > 0 else mk["ask"]
                unrl = (px - b.entry_px) * b.pos * LOTS / b.pip * PAIRS[p]["dollars_per_pip_per_lot"]
                pos_str = "LONG" if b.pos > 0 else "SHORT"
                gross += LOTS * (mk["ask"] + mk["bid"]) / 2 * 100_000
            sleeves[p] = {
                "position": pos_str, "lots": LOTS if b.pos != 0 else 0,
                "entry_px": b.entry_px, "unrealized_usd": round(unrl, 2),
                "realized_usd": round(b.realized_usd, 2), "fills": b.fills,
                "mark": ({"bid": round(mk["bid"], 5), "ask": round(mk["ask"], 5),
                           "age_s": round(mk["age"], 1)} if mk else None),
                "next_decision": "mỗi giờ H1 (00:00–18:00 UTC); chốt phẳng 20:00 UTC",
            }
            unreal_total += unrl
        equity = SEED_EQUITY + realized_usd + unreal_total
        state = {
            "schema": "phorec.shadow_state@1",
            "strategy": "RANGEFADE-2M (wide-range-day fade, EURUSD+GBPUSD, H1, flat 20:00 UTC)",
            "updated_utc": now.isoformat(timespec="seconds"),
            "data_stale": data_stale,
            "seed_equity": SEED_EQUITY, "lots_per_pair": LOTS,
            "equity": round(equity, 2),
            "pnl_total": round(equity - SEED_EQUITY, 2),
            "pnl_total_pct": round((equity - SEED_EQUITY) / SEED_EQUITY * 100, 3),
            "pnl_today": round(realized_usd - day_start_realized, 2),
            "realized_usd": round(realized_usd, 2),
            "unrealized_usd": round(unreal_total, 2),
            "gross_exposure_usd": round(gross, 2),
            "gross_pct_of_equity": round(gross / equity * 100, 1) if equity else 0,
            "parity_selftest": parity_rec,
            "sleeves": sleeves,
        }
        atomic_write(STATE, json.dumps(state, indent=1))
        atomic_write(HEARTBEAT, json.dumps({"pid_heartbeat_utc": now.isoformat(timespec="seconds")}))
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
