"""RANGEFADE-2M shadow daemon (paper only — no broker, no orders).

Polls TrueFX indicative quotes every ~15s, maintains per-pair H1 bars
(seeded from the sha-verified Dukascopy corpus + bridge), evaluates the
frozen FX2-RANGEEXP-C3 signal per pair, simulates fills at the live
opposite quote for 1.5 lots, and writes atomic state + an append-only
journal. Fail-closed on stale quotes. See PLAN_fx_rangefade_2m_shadow_v1.md.

Restart identity (owner order 2026-09-24): at boot the journal is
REPLAYED (fx_shadow_core.replay_journal) so position, entry, realized
PnL, fill counts and every H1 bar closed since the seed corpus survive
restarts — restarting many times never erases PnL, duplicates fills or
drops a position. PnL hôm nay includes the open positions' MTM: the
book is flat at every UTC midnight by the force-flat law, so
pnl_today = realized_since_utc_midnight + unrealized_now, with the
anchor disclosed in the state file.
"""
import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "EURUSD-OPEN-SEARCH-V2" / "scripts"))
sys.path.insert(0, str(HERE.parent.parent / "FX-MAJORS-SEARCH-V1" / "scripts"))
import engine as E  # noqa: E402  (frozen semantics v1 + pip param)
import v2_lib as V  # noqa: E402  (frozen families)
import fx_shadow_core as C  # noqa: E402  (pure core: bars + replay + account)

SEED_DERIVED = {
    "EURUSD": HERE.parent / "data_local" / "EURUSD",  # own corpus incl. 2026-07..09 bridge
    "GBPUSD": Path("/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD"),
    "GBPUSD_note": "sha-verified FX-MAJORS corpus incl. 2026-07..09 bridge",
}
PAIRS = {"EURUSD": {"pip": 1e-4, "dollars_per_pip_per_lot": 10.0},
         "GBPUSD": {"pip": 1e-4, "dollars_per_pip_per_lot": 10.0}}
LOTS = C.LOTS
SEED_EQUITY = C.SEED_EQUITY
POLL_SEC = 15
STALE_SEC = 15 * 60
STATE = ROOT / "shadow_state.json"
JOURNAL = ROOT / "shadow_journal.jsonl"
HEARTBEAT = ROOT / "daemon_heartbeat.json"
EQUITY_CURVE = ROOT / "equity_curve.json"
TRUEFX = "https://webrates.truefx.com/rates/connect.html?f=csv&c=EUR/USD,GBP/USD"

STATE_SCHEMA = "phorec.shadow_state@2"


class Journal:
    """Append-only journal writer with a monotone seq + event ids."""

    def __init__(self, path: Path):
        self.path = path
        self.seq = 0
        if path.exists():
            with path.open() as f:
                for line in f:
                    if line.strip():
                        self.seq += 1

    def log(self, event: str, **kw) -> dict:
        self.seq += 1
        rec = {"seq": self.seq,
               "event_id": C.event_id(self.seq, str(kw.get("bar_ts", kw.get("quote_ts", ""))), event,
                                      str(kw.get("pair", ""))),
               "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "event": event, **kw}
        with self.path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        return rec


def atomic_write(path: Path, text: str) -> None:
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
    # The parquet carries ms-unit timestamps (datetime64[ms, UTC]); live
    # appends are ns-unit Timestamps, and pd.concat cannot unify ms/ns —
    # it silently degrades the column to object and the frozen engine's
    # .dt accessor then crashes at the first H1 boundary. Normalize the
    # seed to ns ONCE at this ingest edge (lossless for hourly bars) so
    # every later concat stays datetimelike.
    df["ts"] = df["ts"].astype("datetime64[ns, UTC]")
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
    def __init__(self, pair, pip, journal: Journal):
        self.pair, self.pip = pair, pip
        self.journal = journal
        self.df = seed_bars(pair)              # committed H1 history (seed corpus)
        # engine.Plane normalizes tz-aware datetimes itself; the shadow
        # tracks epoch SECONDS internally and converts at the append edge.
        self.seed_last_ts = int(pd.Timestamp(self.df["ts"].iloc[-1]).timestamp())
        self.pos = 0                            # -1/0/+1 (units of LOTS sign)
        self.entry_px = None
        self.entry_ts = None
        self.realized_usd = 0.0
        self.fills = 0
        self.live_bar = None                    # fx_shadow_core.LiveBar
        self.last_target = 0
        self.parity = None

    @staticmethod
    def _bar_row(row: dict) -> dict:
        """Replayed/committed bar (epoch seconds) -> df row (tz-aware ts)."""
        return {
            "ts": pd.Timestamp(row["ts"], unit="s", tz="UTC"),
            "b_o": row["b_o"], "b_h": row["b_h"], "b_l": row["b_l"],
            "b_c": row["b_c"], "a_o": row["a_o"], "a_c": row["a_c"],
            "s_open": (row["a_o"] or 0) - (row["b_o"] or 0),
            "s_close": (row["a_c"] or 0) - (row["b_c"] or 0),
        }

    def restore(self, st: dict) -> int:
        """Apply replayed journal state; append bars the seed lacks."""
        self.pos = int(st.get("pos") or 0)
        self.entry_px = st.get("entry_px")
        self.entry_ts = st.get("entry_ts")
        self.realized_usd = float(st.get("realized_usd") or 0.0)
        self.fills = int(st.get("fills") or 0)
        bars = st.get("bars") or {}
        rows = [bars[k] for k in sorted(bars)]
        fresh = [r for r in rows if r["ts"] > self.seed_last_ts]
        if fresh:
            self.df = pd.concat(
                [self.df, pd.DataFrame([self._bar_row(r) for r in fresh])],
                ignore_index=True)
            tgt, _ = targets_from_df(self.df, self.pip)
            self.last_target = int(tgt[-1])
        return len(fresh)

    def on_closed_bar(self, bar: dict) -> None:
        """bar: dict(b_o..a_c, ts in epoch seconds). Append (tz-aware for
        engine.Plane), recompute target (signal on CLOSED bar)."""
        self.df = pd.concat([self.df, pd.DataFrame([self._bar_row(bar)])],
                            ignore_index=True)
        tgt, _ = targets_from_df(self.df, self.pip)
        self.last_target = int(tgt[-1])
        self.parity = "PASS"
        self.journal.log("bar_closed", pair=self.pair, bar_ts=bar["ts"],
                         b_o=bar["b_o"], b_h=bar["b_h"], b_l=bar["b_l"],
                         b_c=bar["b_c"], a_o=bar["a_o"], a_c=bar["a_c"],
                         target=self.last_target)

    def desired_now(self):
        """Position wanted for the bar that just opened (fill allowed hour<=18 UTC)."""
        if len(self.df) == 0:
            return 0
        last_ts = int(pd.Timestamp(self.df["ts"].iloc[-1]).timestamp())
        h = (last_ts // C.HOUR) % 24
        if h >= 19:
            return 0
        return self.last_target

    def close_position(self, px: float, reason: str) -> float:
        pnl = C.pnl_of(self.pos, self.entry_px, px, self.pip)
        self.realized_usd += pnl
        self.journal.log("fill_close" if reason == "signal" else "force_flat",
                         pair=self.pair, dir=self.pos, entry_px=self.entry_px,
                         exit_px=px, pnl_usd=round(pnl, 2), lots=LOTS,
                         realized_total=round(self.realized_usd, 2), reason=reason)
        self.pos, self.entry_px, self.entry_ts = 0, None, None
        return pnl

    def open_position(self, want: int, bid: float, ask: float, qts: float) -> None:
        px = ask if want > 0 else bid
        self.pos, self.entry_px, self.entry_ts = want, px, int(qts)
        self.fills += 1
        self.journal.log("fill_open", pair=self.pair, dir=want, entry_px=px,
                         lots=LOTS, quote_ts=qts, spread=round(ask - bid, 6),
                         mark="truefx_indicative")

    def unrealized(self, mk) -> float:
        if mk is None or self.pos == 0:
            return 0.0
        px = mk["bid"] if self.pos > 0 else mk["ask"]
        return C.pnl_of(self.pos, self.entry_px, px, self.pip)

    def gross_notional(self, mk) -> float:
        if mk is None or self.pos == 0:
            return 0.0
        return LOTS * (mk["ask"] + mk["bid"]) / 2 * 100_000


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def main():
    journal = Journal(JOURNAL)
    books = {p: PairBook(p, m["pip"], journal) for p, m in PAIRS.items()}

    # --- restart identity: replay the immutable journal ---------------
    replay_lines = JOURNAL.read_text().splitlines() if JOURNAL.exists() else []
    rep = C.replay_journal(replay_lines, seed_last_ts={p: 0 for p in PAIRS})
    for p, b in books.items():
        restored = b.restore(rep["pairs"].get(p, {}))
        journal.log("boot_replay", pair=p, pos_restored=b.pos,
                    realized_restored=round(b.realized_usd, 2),
                    fills_restored=b.fills, bars_restored=restored,
                    events_read=rep["events_read"], events_dup=rep["events_dup"],
                    events_bad=rep["events_bad"])

    today_key = now_utc().strftime("%Y-%m-%d")
    realized_today = rep["realized_by_day_utc"].get(today_key, 0.0)
    session_realized = 0.0  # fills executed after this boot

    # launch parity self-test: daemon signal path vs frozen library on identical bars
    parity_rec = None
    for p, b in books.items():
        tgt_daemon, _ = targets_from_df(b.df, b.pip)
        tgt_frozen = V.f_rangeexp(plane_from_df(b.df), 0.3, 0.7, False)
        ok = np.array_equal(tgt_daemon, tgt_frozen)
        parity_rec = journal.log("parity_selftest", pair=p,
                                 result="PASS" if ok else "FAIL",
                                 n_bars=int(len(b.df)))
        if not ok:
            raise SystemExit("FAIL_CLOSED: parity self-test failed")

    journal.log("shadow_start", strategy="RANGEFADE-2M", pairs=list(PAIRS),
                lots=LOTS, seed=SEED_EQUITY, schema=STATE_SCHEMA,
                replay={"bars_restored": rep["bars_restored"],
                        "realized_restored": round(rep["realized_usd"], 2),
                        "pos": {p: b.pos for p, b in books.items()}})

    while True:
        try:
            marks = truefx_poll()
            data_stale = any(m["age"] > STALE_SEC for m in marks.values()) or len(marks) < len(PAIRS)
        except Exception:
            data_stale = True
            marks = {}
        now = now_utc()
        if now.strftime("%Y-%m-%d") != today_key:
            # UTC midnight roll: the book is FLAT here by the 20:00
            # force-flat law, so today's realized restarts from zero
            # and the unrealized part of the PnL-today anchor is 0.
            today_key = now.strftime("%Y-%m-%d")
            realized_today = 0.0
            journal.log("day_roll", day=today_key,
                        realized_total=round(sum(b.realized_usd for b in books.values()), 2))

        for p, b in books.items():
            mk = marks.get(p)
            if mk is None:
                continue
            qts = mk["ts"]
            h0 = C.floor_hour(qts)
            if b.live_bar is None or b.live_bar.ts != h0:
                # hour rolled (per the QUOTE's own timestamp, PIT):
                # the previous live bar is now CLOSED
                if b.live_bar is not None:
                    closed = b.live_bar.as_row()
                    b.on_closed_bar(closed)
                    closed_hour = (closed["ts"] // C.HOUR) % 24
                    # force-flat at the close of the 19:00 bar (= 20:00 UTC)
                    if closed_hour == 19 and b.pos != 0:
                        px = mk["bid"] if b.pos > 0 else mk["ask"]
                        session_realized += b.close_position(px, "force_flat")
                    # signal for the bar that just opened
                    want = b.desired_now()
                    if want != b.pos and closed_hour <= 18 and not data_stale:
                        if b.pos != 0:
                            px = mk["bid"] if b.pos > 0 else mk["ask"]
                            session_realized += b.close_position(px, "signal")
                        if want != 0:
                            b.open_position(want, mk["bid"], mk["ask"], qts)
                b.live_bar = C.LiveBar(h0, mk["bid"], mk["ask"])
            else:
                b.live_bar.update(mk["bid"], mk["ask"])

        # ----- account state: ONE $100k account, sleeves = contributions
        marks_fresh = not data_stale
        unreal_total = 0.0
        gross = 0.0
        sleeves = {}
        for p, b in books.items():
            mk = marks.get(p)
            unrl = b.unrealized(mk)
            unreal_total += unrl
            gross += b.gross_notional(mk)
            pos_str = "FLAT" if mk is not None else "NO_MARK"
            if mk is not None and b.pos != 0:
                pos_str = "LONG" if b.pos > 0 else "SHORT"
            sleeves[p] = {
                "position": pos_str, "lots": LOTS if b.pos != 0 else 0,
                "entry_px": b.entry_px, "entry_ts": b.entry_ts,
                "unrealized_usd": round(unrl, 2),
                "realized_usd": round(b.realized_usd, 2),
                "contribution_pnl_usd": round(b.realized_usd + unrl, 2),
                "fills": b.fills,
                "gross_exposure_usd": round(b.gross_notional(mk), 2),
                "mark": ({"bid": round(mk["bid"], 5), "ask": round(mk["ask"], 5),
                          "age_s": round(mk["age"], 1)} if mk else None),
                "next_decision": "mỗi giờ H1 (00:00–18:00 UTC); chốt phẳng 20:00 UTC",
            }
        account = C.account_block(
            realized_usd=sum(b.realized_usd for b in books.values()),
            unrealized_usd=unreal_total,
            realized_today=realized_today + session_realized,
            gross_exposure_usd=gross,
            marks_fresh=marks_fresh,
        )
        state = {
            "schema": STATE_SCHEMA,
            "strategy": "RANGEFADE-2M (wide-range-day fade, EURUSD+GBPUSD, H1, flat 20:00 UTC)",
            "account_model": ("ONE shared $100,000 paper account for BOTH pairs; "
                              "sleeves are PnL contributions, not separate accounts"),
            "updated_utc": now.isoformat(timespec="seconds"),
            "data_stale": data_stale,
            "marks_fresh": marks_fresh,
            "event_seq": journal.seq,
            "lots_per_pair": LOTS,
            "account": account,
            "parity_selftest": {"pair": parity_rec["pair"], "result": parity_rec["result"]},
            "sleeves": sleeves,
        }
        atomic_write(STATE, json.dumps(state, indent=1))
        atomic_write(HEARTBEAT, json.dumps({"pid_heartbeat_utc": now.isoformat(timespec="seconds")}))

        # equity curve: one point per hour (bounded to last 90 days)
        try:
            curve = json.loads(EQUITY_CURVE.read_text()) if EQUITY_CURVE.exists() else {"schema": "phorec.equity_curve@1", "points": []}
        except Exception:
            curve = {"schema": "phorec.equity_curve@1", "points": []}
        pts = curve.setdefault("points", [])
        hour_key = now.replace(minute=0, second=0, microsecond=0).isoformat()
        if not pts or pts[-1]["t"] != hour_key:
            sleeves_cum = {p: round(b.realized_usd + sleeves[p]["unrealized_usd"], 2)
                           for p, b in books.items()}
            pts.append({"t": hour_key, "equity": account["equity"],
                        "pnl_day": account["pnl_today"], "sleeves": sleeves_cum})
            cutoff = (now - dt.timedelta(days=90)).isoformat()
            curve["points"] = [q for q in pts if q["t"] >= cutoff]
            atomic_write(EQUITY_CURVE, json.dumps(curve))
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
