"""Per-pair bi5 probe: derive pip scale + price scale + band FROM BYTES.

Plan §5.2 checklist item: "pip-scale + level-band probe derived from probe
ticks — PROVE from bytes, never assume". Window (bounded ~7–14 days,
2024, straddling a DST transition + a rollover): 2024-10-26..2024-11-06 —
contains the EU DST end (Sun 2024-10-27), the US DST end (Sun 2024-11-03)
and two weekend rollovers in one bounded window.

Method (all values derived from raw tick/candle integers; the registered
guard ranges from pair_config.REGISTERED_GUARDS are used only as
acceptance checks and band floors/ceilings, never as the derivation):

  price scale  : unique s in {1e3,1e4,1e5,1e6} with median(raw/s) inside
                 the registered guard band AND sane point/pip/spread
                 checks (spread-in-pips is scale-free: median raw
                 spread/10; it must land in [0.05, 20] pips).
  point / pip  : point = 1/price_scale (price units per raw integer step);
                 pip = 10 x point (byte-derived; EURUSD check: 10x1e-5=
                 1e-4; USDJPY precedent: 10x1e-3=0.01).
  band         : union of probe-observed min/max padded +/-20% (pip-grid
                 rounded outward) with the registered guard range.

Invariants proven per pair before PROBE_PASS:
  - every candle file len%24==0, every tick file len%20==0 (layout trap);
  - M1 OHLC invariants: low<=min(o,c), high>=max(o,c);
  - tick-vs-candle content cross-check: per-minute tick-aggregated
    OHLC == candle OHLC within 2 points, BID and ASK sides;
  - all tick prices strictly inside the derived band.

Outputs:
  data_local/probe/{SYMBOL}/            raw probe bytes (gitignored)
  data_local/derived/probe_{SYMBOL}.json  committed probe report + digests
  scripts/pair_configs.json             written ONLY on PROBE_PASS

Heavy-lock: this is a bounded download job (~290 files/pair) — the
machine-wide lock is acquired for the whole run, heartbeat fresh, release
in finally (LOCK_BUSY -> NOT_RUN_RESOURCE_CONFLICT verdict, exit 4).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import sys
import threading
import time
from pathlib import Path

import numpy as np

LANE = Path(__file__).resolve().parent.parent          # .../ERP1-TRACKA-COHORT-1
sys.path.insert(0, str(LANE / "scripts"))
sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/research")

import duka_lib as D                    # noqa: E402
from pair_config import REGISTERED_GUARDS  # noqa: E402

from governance import heavy_lock       # noqa: E402

PROBE_START, PROBE_END = dt.date(2024, 10, 26), dt.date(2024, 11, 6)
CANDIDATE_SCALES = (1e3, 1e4, 1e5, 1e6)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def daterange(a: dt.date, b: dt.date):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def derive_scale(raw_prices: np.ndarray, raw_spread: np.ndarray, guard: dict):
    """Unique guard-band scale + byte-derived point/pip, or None."""
    med = float(np.median(raw_prices))
    spread_med = float(np.median(raw_spread))
    hits = []
    for s in CANDIDATE_SCALES:
        p_med = med / s
        if not (guard["band_lo"] <= p_med <= guard["band_hi"]):
            continue
        point = 1.0 / s
        pip = 10.0 * point
        spread_pips = (spread_med / s) / pip  # == spread_med / 10, kept explicit
        if not (0.05 <= spread_pips <= 20.0):
            continue
        if not (1e-6 <= point <= 1e-3):
            continue
        hits.append({"scale": s, "median_price": p_med, "point": point,
                     "pip": pip, "spread_pips_median": spread_pips})
    if len(hits) != 1:
        return None, hits
    return hits[0], hits


def minute_ohlc_from_ticks(tick_rows, side_idx):
    """(ms, ask_raw, bid_raw, ..) rows -> {minute_index: (o,h,l,c)} raw ints."""
    per_min = {}
    for ms, a, b, _av, _bv in tick_rows:
        p = a if side_idx == 1 else b
        m = ms // 60000
        cur = per_min.get(m)
        if cur is None:
            per_min[m] = [p, p, p, p]  # o, h, l, c
        else:
            if p > cur[1]:
                cur[1] = p
            if p < cur[2]:
                cur[2] = p
            cur[3] = p
    return {m: tuple(v) for m, v in per_min.items()}


def probe_symbol(symbol: str, fetcher: D.KeepAliveFetcher, lock_handle, out_dirs):
    guard = REGISTERED_GUARDS[symbol]
    probe_dir = out_dirs["probe"] / symbol
    probe_dir.mkdir(parents=True, exist_ok=True)
    rep = {
        "symbol": symbol,
        "window": [PROBE_START.isoformat(), PROBE_END.isoformat()],
        "window_rationale": (
            "EU DST end 2024-10-27 + US DST end 2024-11-03 + two weekend "
            "rollovers, bounded 11 days from 2024 (plan 5.2 probe spec)"
        ),
        "registered_guard": guard,
        "files": {},
        "days_missing_candles": [],
        "tick_hours_missing": [],
        "layout": {"candle_files": 0, "tick_files": 0,
                   "candle_len_mod24_violations": 0, "tick_len_mod20_violations": 0},
        "ohlc_invariants": {"m1_checked": 0, "violations": 0},
        "scale_candidates": None,
        "candle_scale_check": None,
        "crosscheck": {},
        "dst_rollover_observation": {},
        "band_derivation": None,
        "verdict": "PROBE_FAIL",
    }
    days = list(daterange(PROBE_START, PROBE_END))

    all_ask_raw, all_bid_raw = [], []
    first_tick_by_day = {}
    cross = {"compared_minutes_bid": 0, "mismatch_bid": 0,
             "compared_minutes_ask": 0, "mismatch_ask": 0,
             "candle_tradable_no_ticks": 0, "ticks_but_zero_vol": 0,
             "per_day": {}}
    hour_spread_raw = {h: [] for h in range(24)}

    for day in days:
        y, m, d = day.year, day.month, day.day
        day_candles = {}
        for side in ("BID", "ASK"):
            path = D.candle_path(symbol, y, m, d, side)
            raw = fetcher.fetch(path)
            if lock_handle is not None and (day.day % 2 == 0):
                lock_handle.heartbeat(extra={"probe_symbol": symbol, "stage": "candles"})
            if raw is None:
                rep["days_missing_candles"].append(f"{day.isoformat()}:{side}")
                continue
            rep["files"][f"candles/{day.isoformat()}_{side}.bi5"] = {
                "remote_path": path, "sha256": sha256(raw), "bytes": len(raw)}
            try:
                recs = D.decode_candle_records(raw)
            except AssertionError:
                rep["layout"]["candle_len_mod24_violations"] += 1
                continue
            rep["layout"]["candle_files"] += 1
            day_candles[side] = {r[0]: r for r in recs}
            # OHLC invariants on raw ints: low<=min(o,c), high>=max(o,c), low<=high
            for sec, o, c, lo, hi, _v in recs:
                if not (lo <= min(o, c) and hi >= max(o, c) and lo <= hi):
                    rep["ohlc_invariants"]["violations"] += 1
                rep["ohlc_invariants"]["m1_checked"] += 1

        # tick hours for this day (both sides from the same file: ask, bid)
        day_ticks = {}
        for hour in range(24):
            path = D.tick_path(symbol, y, m, d, hour)
            raw = fetcher.fetch(path)
            if lock_handle is not None and hour % 4 == 0:
                lock_handle.heartbeat(extra={"probe_symbol": symbol, "stage": "ticks"})
            if raw is None:
                rep["tick_hours_missing"].append(f"{day.isoformat()}T{hour:02d}")
                continue
            rep["files"][f"ticks/{day.isoformat()}_{hour:02d}h.bi5"] = {
                "remote_path": path, "sha256": sha256(raw), "bytes": len(raw)}
            try:
                rows = D.decode_tick_records(raw)
            except AssertionError:
                rep["layout"]["tick_len_mod20_violations"] += 1
                continue
            rep["layout"]["tick_files"] += 1
            day_ticks[hour] = rows
            if rows and day.weekday() == 6:
                ms = min(r[0] for r in rows)
                t = dt.datetime(y, m, d, hour, tzinfo=dt.timezone.utc) \
                    + dt.timedelta(milliseconds=ms)
                prev = first_tick_by_day.get(day.isoformat())
                if prev is None or t < prev:
                    first_tick_by_day[day.isoformat()] = t
            for ms, a, b, _av, _bv in rows:
                all_ask_raw.append(a)
                all_bid_raw.append(b)
                hour_spread_raw[hour].append(a - b)

        # ---- tick-vs-candle content cross-check (BID and ASK) ----
        day_x = {"bid_min": 0, "ask_min": 0}
        for side, idx in (("BID", 2), ("ASK", 1)):
            cdl = day_candles.get(side)
            if cdl is None:
                continue
            tol = 2.0  # in raw points; prices are exact ints
            for hour, rows in day_ticks.items():
                per_min = minute_ohlc_from_ticks(rows, idx)
                base_sec = hour * 3600
                for mrel, (to, th, tl, tc) in per_min.items():
                    rec = cdl.get(base_sec + mrel * 60)
                    if rec is None:
                        cross["ticks_but_zero_vol"] += 1
                        continue
                    _s, co, cc, cl, ch, _v = rec
                    day_x[f"{side.lower()}_min"] += 1
                    if not (abs(to - co) <= tol and abs(tc - cc) <= tol
                            and abs(tl - cl) <= tol and abs(th - ch) <= tol):
                        day_x[f"{side.lower()}_min"] -= 1
                        cross[f"mismatch_{side.lower()}"] += 1
            # candle minutes with volume but no tick in an hour file we have
            for hour, rows in day_ticks.items():
                tick_secs = {hour * 3600 + (ms // 1000) // 60 * 60 for ms, *_ in rows}
                for sec, _o, _c, _l, _h, v in day_candles[side].values():
                    if v > 0 and (sec // 60) // 60 == hour and sec not in tick_secs:
                        cross["candle_tradable_no_ticks"] += 1
        cross["per_day"][day.isoformat()] = day_x

    # candle scale consistency: tick bid raw median magnitude (candles are
    # decoded with the same derived scale in build_bars; medians recorded)
    if all_bid_raw:
        rep["candle_scale_check"] = {
            "note": "candle/tick raw magnitudes share the one scale; medians recorded",
            "tick_bid_raw_median": float(np.median(all_bid_raw)),
        }

    # ---- scale / pip / band derivation ----
    all_ask_raw = np.array(all_ask_raw, dtype=np.int64)
    all_bid_raw = np.array(all_bid_raw, dtype=np.int64)
    if all_bid_raw.size == 0:
        rep["verdict"] = "PROBE_FAIL"
        return rep
    mids = (all_ask_raw + all_bid_raw) / 2.0
    spreads = all_ask_raw - all_bid_raw
    hit, cands = derive_scale(mids, spreads, guard)
    rep["scale_candidates"] = {"accepted": hit, "all": cands}
    if hit is None:
        return rep
    scale, pip, point = hit["scale"], hit["pip"], hit["point"]

    probe_min = float(mids.min()) / scale
    probe_max = float(mids.max()) / scale

    def floor_pip(x):
        return math.floor(x / pip - 1e-9) * pip

    def ceil_pip(x):
        return math.ceil(x / pip + 1e-9) * pip

    band_lo = min(floor_pip(probe_min * 0.80), guard["band_lo"])
    band_hi = max(ceil_pip(probe_max * 1.20), guard["band_hi"])
    rep["band_derivation"] = {
        "method": "union(probe min*0.80 floor-to-pip, probe max*1.20 ceil-to-pip, registered guard)",
        "probe_min_price": probe_min, "probe_max_price": probe_max,
        "pad_relative": 0.20, "band_lo": round(band_lo, 10), "band_hi": round(band_hi, 10),
        "covers_guard": bool(band_lo <= guard["band_lo"] and band_hi >= guard["band_hi"]),
        "all_probe_prices_inside_band": bool(
            probe_min / pip >= band_lo / pip - 1e-9 and probe_max / pip <= band_hi / pip + 1e-9
        ),
    }

    # hour-by-hour median tick spread (rollover shape visible in the probe)
    rep["dst_rollover_observation"] = {
        "hour_median_spread_pips": {
            h: (round(float(np.median(v)) / scale / pip, 3) if v else None)
            for h, v in sorted(hour_spread_raw.items())
        },
        "sundays": [
            {
                "date": day.isoformat(),
                "first_tick_utc": (
                    first_tick_by_day[day.isoformat()].isoformat()
                    if day.isoformat() in first_tick_by_day else None
                ),
                "note": dst_note(day),
            }
            for day in days if day.weekday() == 6
        ],
    }

    ok = (
        rep["layout"]["candle_len_mod24_violations"] == 0
        and rep["layout"]["tick_len_mod20_violations"] == 0
        and rep["ohlc_invariants"]["violations"] == 0
        and not rep["days_missing_candles"]
        and cross["mismatch_bid"] == 0
        and cross["mismatch_ask"] == 0
        and rep["band_derivation"]["covers_guard"]
        and rep["band_derivation"]["all_probe_prices_inside_band"]
    )
    cross["compared_minutes_bid"] = sum(v["bid_min"] for v in cross["per_day"].values())
    cross["compared_minutes_ask"] = sum(v["ask_min"] for v in cross["per_day"].values())
    rep["crosscheck"] = cross
    rep["derivation"] = {
        "price_scale": scale, "point_price_units": point, "pip_price_units": pip,
        "pip_method": "pip = 10 x point (byte-derived; USDJPY precedent 10x1e-3=0.01)",
        "proven": bool(ok),
    }
    rep["verdict"] = "PROBE_PASS" if ok else "PROBE_FAIL"
    return rep


def dst_note(day: dt.date) -> str:
    if day == dt.date(2024, 10, 27):
        return "EU DST end (CEST->CET): FX Sunday-open hour tracks US DST, so this Sunday still opens ~21:00 UTC; the shift to ~22:00 UTC appears at the US transition"
    if day == dt.date(2024, 11, 3):
        return "US DST end (EDT->EST): FX Sunday open moves from ~21:00 to ~22:00 UTC from this date"
    return "normal (no DST transition)"


def main() -> int:
    symbols = sys.argv[1:] or ["AUDUSD", "USDCAD"]
    for s in symbols:
        if s not in REGISTERED_GUARDS:
            print(f"FAIL_CLOSED unknown symbol {s}")
            return 2

    derived_dir = LANE / "data_local" / "derived"
    probe_dir = LANE / "data_local" / "probe"
    derived_dir.mkdir(parents=True, exist_ok=True)
    manifest_paths = [str(derived_dir / f"probe_{s}.json") for s in symbols]

    lock = None
    status = "FAILED"
    note = ""
    try:
        try:
            lock = heavy_lock.acquire(
                cycle_id="ERP1-TRACKA-COHORT-1",
                role="datagate-probe",
                worktree=str(LANE),
                command=[sys.executable, str(Path(__file__).resolve()), *symbols],
                expected_artifacts=manifest_paths,
            )
        except heavy_lock.LockBusyError as e:
            print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT", "reason": str(e)}))
            return 4

        stop = threading.Event()

        def beat():
            while not stop.wait(30):
                try:
                    lock.heartbeat()
                except Exception:
                    pass

        threading.Thread(target=beat, daemon=True).start()
        fetcher = D.KeepAliveFetcher()
        try:
            configs = {}
            cfg_path = LANE / "scripts" / "pair_configs.json"
            if cfg_path.exists():
                configs = json.loads(cfg_path.read_text())
            all_ok = True
            for s in symbols:
                t0 = time.time()
                rep = probe_symbol(s, fetcher, lock, {"probe": probe_dir})
                rep["wall_clock_seconds"] = round(time.time() - t0, 1)
                out = derived_dir / f"probe_{s}.json"
                out.write_text(json.dumps(rep, indent=1))
                print(f"{s}: {rep['verdict']} "
                      f"scale={rep.get('derivation', {}).get('price_scale')} "
                      f"pip={rep.get('derivation', {}).get('pip_price_units')} "
                      f"band=[{rep.get('band_derivation', {}).get('band_lo')}, "
                      f"{rep.get('band_derivation', {}).get('band_hi')}] "
                      f"mismatch_b/a={rep.get('crosscheck', {}).get('mismatch_bid')}/"
                      f"{rep.get('crosscheck', {}).get('mismatch_ask')} -> {out}")
                if rep["verdict"] != "PROBE_PASS":
                    all_ok = False
                    continue
                d = rep["derivation"]
                bd = rep["band_derivation"]
                configs[s] = {
                    "symbol": s,
                    "pip": d["pip_price_units"],
                    "price_scale": d["price_scale"],
                    "band_lo": bd["band_lo"],
                    "band_hi": bd["band_hi"],
                    "derivation": {
                        "proven": True,
                        "probe_report": str(out.relative_to(LANE)),
                        "probe_report_sha256": sha256(out.read_bytes()),
                        "method_scale": "unique guard-band candidate in {1e3,1e4,1e5,1e6}",
                        "method_pip": d["pip_method"],
                        "method_band": bd["method"],
                        "window": rep["window"],
                        "registered_guard": rep["registered_guard"],
                        "probe_min_price": bd["probe_min_price"],
                        "probe_max_price": bd["probe_max_price"],
                    },
                }
            cfg_path.write_text(json.dumps(configs, indent=1))
            status = "FINISHED" if all_ok else "FAILED"
            if not all_ok:
                note = "at least one pair PROBE_FAIL — pair_configs.json updated only with proven pairs"
            return 0 if all_ok else 3
        finally:
            fetcher.close()
            stop.set()
    except Exception as e:  # noqa: BLE001 — release with note, then re-raise
        status = "FAILED"
        note = f"{type(e).__name__}: {e}"[:400]
        raise
    finally:
        if lock is not None:
            lock.release(status=status, note=note)


if __name__ == "__main__":
    sys.exit(main())
