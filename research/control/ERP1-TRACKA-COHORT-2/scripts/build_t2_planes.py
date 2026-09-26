"""ERP1-TRACKA-COHORT-2 — build + persist the candidate target arrays and
the F-1 shadow arrays on the SAME dev H1 grid, with a full manifest.

Everything comes through scripts/dev_plane2.py (sealed filter ts <= 
2025-12-31 23:59:59 UTC + row pins 27608 AUDUSD / 27583 USDCAD H1; the
2026-01-01..2026-06-30 holdout is never read — day files of 2026 are never
even opened during the M1 aggregation).

Outputs (data_local/derived/):
  m1agg_{SYM}.parquet          per-dev-H1-bar M1 aggregates (P3-A inputs)
  t2_p3a_{SYM}_{arm}.npy       arms: anchor, index_shift_pool, mirror_wide,
                               volgate, ungated                (int8)
  t2_p3b_{SYM}_{arm}.npy       arms: anchor, mirror_wide, ungated,
                               weekday_shuffle                 (int8)
  t2shadow_{name}_{SYM}.npy    R-ANCHOR, R-ORIG, M3_SPREADGATEDFADE and the
                               11 census families x C1..C4 (v2_campaign.py
                               FROZEN configs — never re-chosen)
  t2_planes_manifest.json      row pins, per-array sha256, shadow status,
                               code shas, warmup index, fold table F1..F6

Shadow sources (read-only citations; shas recorded):
  tracka_lib.py (local, sha-pinned by freeze/ENGINE_INHERITANCE_shas.txt)
    -> R-ANCHOR / R-ORIG on the ANC signal plane (SignalPlane convention).
  {eurusd-open-search-v2}/scripts/v2_lib.py + v2_campaign.py -> the census
    families. v2_lib is imported VERBATIM (its own engine module provides
    E.PIP=1e4 == the pairs' pip multiplier, so numerics equal the census
    spec); build_t2_planes deliberately never imports a module named
    "engine" so v2_lib binds its own ancestor engine.

Heavy job (M1 aggregation scans every dev day file) -> machine-wide heavy
lock, NOT_RUN_RESOURCE_CONFLICT if held.
"""
from __future__ import annotations

import hashlib
import json
import lzma
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))
sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/research")

import dev_plane2  # noqa: E402
from dev_plane2 import DERIVED  # noqa: E402
from pair_config import load_pair_config  # noqa: E402
from qcrd_dinv_lib import (  # noqa: E402
    dinv_1d_target, epoch_secs, qcrd_h1_target, session_day_ordinals,
    WARMUP_TRADED_DAYS,
)

# ---- read-only raw-byte citation (cohort-1 archive; never copied) ------
C1_DUKA = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1"
    "/integration/research/control/ERP1-TRACKA-COHORT-1/data_local/duka")
RAW_M1 = C1_DUKA / "M1"

V2_SCRIPTS = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/eurusd-open-search-v2"
    "/integration/research/control/EURUSD-OPEN-SEARCH-V2/scripts")

CANDLE_DTYPE = np.dtype([("sec", ">i4"), ("o", ">i4"), ("c", ">i4"),
                         ("l", ">i4"), ("h", ">i4"), ("v", ">f4")])

P3A_ARMS = ("anchor", "index_shift_pool", "mirror_wide", "volgate",
            "ungated")
P3B_ARMS = ("anchor", "mirror_wide", "ungated", "weekday_shuffle")

# FROZEN census family configs — copied verbatim from v2_campaign.py
# FAMILY_V2 (RANGEEXP covered by tracka_lib R-ANCHOR / R-ORIG). pos_keys is
# the positional order of the v2_campaign lambda calls (the config KEY NAMES
# are the freeze's; v2_lib's own parameter names differ for DOW/SESSMA, so
# the values are passed positionally exactly as v2_campaign does).
CENSUS_FAMILIES = {
    "FX2-GAP": ("f_gap", ("th", "mode"),
                [{"th": 10, "mode": "follow"},
                 {"th": 20, "mode": "follow"},
                 {"th": 10, "mode": "fade"},
                 {"th": 20, "mode": "fade"}]),
    "FX2-PDHLOC": ("f_pdhloc", ("buf", "opposite_exit"),
                   [{"buf": 0.0, "opposite_exit": True},
                    {"buf": 0.0002, "opposite_exit": True},
                    {"buf": 0.0, "opposite_exit": False},
                    {"buf": 0.0002, "opposite_exit": False}]),
    "FX2-DOW": ("f_dow_simple", ("weeks", "min_past"),
                [{"weeks": 4, "min_past": 8},
                 {"weeks": 8, "min_past": 8},
                 {"weeks": 4, "min_past": 16},
                 {"weeks": 8, "min_past": 16}]),
    "FX2-ASIAFADE": ("f_asiafade", ("asia_end", "buf"),
                     [{"asia_end": 6, "buf": 0.0},
                      {"asia_end": 7, "buf": 0.0},
                      {"asia_end": 6, "buf": 0.0001},
                      {"asia_end": 7, "buf": 0.0001}]),
    "FX2-SESSMA": ("f_sessma", ("th", "atr_n"),
                   [{"th": 1.0, "atr_n": 96},
                    {"th": 1.5, "atr_n": 96},
                    {"th": 1.0, "atr_n": 192},
                    {"th": 1.5, "atr_n": 192}]),
    "FX2-H1TSMOM": ("f_h1tsmom", ("K",),
                    [{"K": 24}, {"K": 48}, {"K": 96}, {"K": 168}]),
    "FX2-H1DONCH": ("f_h1donch", ("L", "hold_mult"),
                    [{"L": 24, "hold_mult": 4},
                     {"L": 48, "hold_mult": 4},
                     {"L": 96, "hold_mult": 3},
                     {"L": 168, "hold_mult": 3}]),
    "FX2-DAYMOM": ("f_daymom", ("N",),
                   [{"N": 2}, {"N": 3}, {"N": 5}, {"N": 10}]),
    "FX2-STOCH": ("f_stoch", ("N", "th_hi", "th_lo"),
                  [{"N": 24, "th_hi": 80, "th_lo": 20},
                   {"N": 24, "th_hi": 85, "th_lo": 15},
                   {"N": 48, "th_hi": 80, "th_lo": 20},
                   {"N": 48, "th_hi": 85, "th_lo": 15}]),
    "FX2-ROUNDNUM": ("f_roundnum", ("grid", "prox"),
                     [{"grid": 0.0025, "prox": 0.0003},
                      {"grid": 0.0050, "prox": 0.0003},
                      {"grid": 0.0025, "prox": 0.0005},
                      {"grid": 0.0050, "prox": 0.0005}]),
    "FX2-HOURREV": ("f_hourrev", ("win_days", "invert"),
                    [{"win_days": 40, "invert": True},
                     {"win_days": 80, "invert": True},
                     {"win_days": 120, "invert": True},
                     {"win_days": 40, "invert": False}]),
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ----------------------------------------------------------- M1 layer ----

def _decode_day(side: str, name: str, symbol: str, man: dict):
    """Manifest-sha-verified decode of one bi5 day file (build_bars.load_day
    semantics with the RAW path overridden to the cohort-1 archive,
    read-only; bytes never copied)."""
    path = RAW_M1 / side / symbol / name
    raw = path.read_bytes()
    entry = man["files"].get(f"{symbol}/{side}/{name}")
    if entry is None or entry.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise SystemExit(
            f"FAIL_CLOSED manifest mismatch: {symbol}/{side}/{name}")
    plain = lzma.decompress(raw)
    if len(plain) % CANDLE_DTYPE.itemsize:
        raise SystemExit(
            f"FAIL_CLOSED {symbol}/{side}/{name}: bad decompressed length")
    return np.frombuffer(plain, dtype=CANDLE_DTYPE)


def build_m1agg(symbol: str, dev1h: pd.DataFrame, heartbeat=None) -> pd.DataFrame:
    """Per-dev-H1-bar M1 aggregates (resolution R1/R2 of qcrd_dinv_lib):
    over the bar's own 60 consecutive tradable minutes:
      m1_sum_dl     = sum of the 59 intrabar dlog mid closes
      m1_sum_abs_dl = sum |dlog|  (realized vol proxy for the volgate twin)
      m1_med_spread = median of the 60 minute relative spreads
      m1_nmin       = minute count consumed (==60 gate)
    Only day files containing dev bars are opened; 2026 files never touched.
    """
    man_path = C1_DUKA / f"m1_manifest_{symbol}.json"
    man = json.loads(man_path.read_text())
    cfg = load_pair_config(symbol)
    scale = float(cfg.price_scale)
    ts = epoch_secs(dev1h)
    bar_day = ts // 86400
    by_day: dict = {}
    for i in range(len(ts)):
        by_day.setdefault(int(bar_day[i]), []).append(int(i))

    out = {
        "ts": np.zeros(len(ts), dtype=np.int64),
        "m1_sum_dl": np.full(len(ts), np.nan),
        "m1_sum_abs_dl": np.full(len(ts), np.nan),
        "m1_med_spread": np.full(len(ts), np.nan),
        "m1_nmin": np.zeros(len(ts), dtype=np.int32),
    }
    ndays = 0
    for d in sorted(by_day):
        name = f"{dt_date_str(d)}.bi5"
        b = _decode_day("BID", name, symbol, man)
        a = _decode_day("ASK", name, symbol, man)
        ndays += 1
        n = min(len(b), len(a))
        bb, aa = b[:n], a[:n]
        secs = bb["sec"].astype(np.int64)
        bc = bb["c"].astype(np.float64) / scale
        ac = aa["c"].astype(np.float64) / scale
        mid = (bc + ac) / 2.0
        sprd = np.where(mid > 0, (ac - bc) / mid, np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            dlog = np.diff(np.log(mid))
        adlog = np.abs(dlog)
        for i in by_day[d]:
            h = int((ts[i] % 86400) // 3600)
            k0, k1 = h * 60, h * 60 + 60
            if k1 > len(secs):
                continue                       # short day: nmin stays 0
            sl = slice(k0, k1)
            ok = (secs[k0] == h * 3600 and secs[k1 - 1] == h * 3600 + 59 * 60)
            if not ok:
                continue
            out["ts"][i] = ts[i]
            out["m1_sum_dl"][i] = float(dlog[sl].sum())
            out["m1_sum_abs_dl"][i] = float(adlog[sl].sum())
            out["m1_med_spread"][i] = float(np.median(sprd[sl]))
            out["m1_nmin"][i] = 60
        if heartbeat is not None and ndays % 100 == 0:
            heartbeat(extra={"symbol": symbol, "days": ndays})
    df = pd.DataFrame(out)
    df["m1_nmin"] = df["m1_nmin"].astype(np.int32)
    return df


def dt_date_str(day_epoch: int) -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(int(day_epoch) * 86400,
                                      tz=_dt.timezone.utc).date().isoformat()


def attach_m1agg(dev1h: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Load (or build) m1agg_{SYM}.parquet and left-join onto the dev plane;
    hard-gate: every dev bar must carry nmin==60 (R1)."""
    cache = DERIVED / f"m1agg_{symbol}.parquet"
    ts = epoch_secs(dev1h)
    if cache.exists():
        agg = pd.read_parquet(cache)
        if (len(agg) == len(dev1h)
                and epoch_secs(agg).tolist() == ts.tolist()):
            pass
        else:
            agg = None
    else:
        agg = None
    if agg is None:
        raise SystemExit(
            f"FAIL_CLOSED m1agg cache missing/stale for {symbol}: run "
            f"build_t2_planes.py first (heavy-lock build step)")
    merged = dev1h.reset_index(drop=True).copy()
    for c in ("m1_sum_dl", "m1_sum_abs_dl", "m1_med_spread", "m1_nmin"):
        merged[c] = agg[c].to_numpy()
    bad = int((merged["m1_nmin"].to_numpy() != 60).sum())
    if bad:
        raise SystemExit(f"FAIL_CLOSED {symbol}: {bad} dev bars without a "
                         "complete 60-minute M1 aggregate")
    return merged


# ------------------------------------------------------------- folds ----

def fold_table(ts: np.ndarray) -> dict:
    """F1..F6 chronological 6-fold over 2021-01-01..2025-12-31 BY
    TRADED-DAY COUNT (dispatch: frozen). np.array_split: first
    n%6 folds take one extra day."""
    day, dord, ord_of = session_day_ordinals(ts)
    days = sorted(ord_of)                       # session-day epochs
    chunks = [c for c in np.array_split(np.asarray(days, dtype=np.int64), 6)
              if len(c)]
    out = {}
    for j, c in enumerate(chunks, start=1):
        out[f"F{j}"] = {
            "first_day": dt_date_str(int(c[0])),
            "last_day": dt_date_str(int(c[-1])),
            "n_traded_days": int(len(c)),
            "first_day_epoch": int(c[0]), "last_day_epoch": int(c[-1]),
        }
    return out


def warmup_index(ts: np.ndarray) -> int:
    """First bar index whose session-day ordinal >= 61 (warmup flat)."""
    _, dord, _ = session_day_ordinals(ts)
    w = np.flatnonzero(dord >= WARMUP_TRADED_DAYS)
    return int(w[0])


# ---------------------------------------------------------- shadows -----

def build_shadows(sym: str, dev1h: pd.DataFrame) -> dict:
    """Build every named shadow on the dev H1 grid; NOT_CONSTRUCTIBLE is
    fail-closed with the mechanical reason — never a proxy."""
    import tracka_lib as T

    plane = T.SignalPlane(dev1h, pip_mult=1e4)
    status = {}

    def emit(name, fn):
        try:
            arr = fn()
            path = DERIVED / f"t2shadow_{name}_{sym}.npy"
            np.save(path, arr.astype(np.int8))
            status[name] = {
                "status": "OK", "sha256": sha256_file(path),
                "n_nonzero": int((arr != 0).sum()),
            }
        except Exception as e:  # noqa: BLE001  — fail-closed, mechanical reason
            status[name] = {"status": "NOT_CONSTRUCTIBLE",
                            "reason": f"{type(e).__name__}: {e}"[:300]}

    emit("R-ANCHOR", lambda: T.f_rangeexp_anchor_shift(plane))
    emit("R-ORIG", lambda: T.f_rangeexp_orig(plane))

    # M3 spread-gated-fade shadow: needs the dev 15m plane for the hour's
    # median 15m spread.
    def m3():
        b15 = dev_plane2.load_bars("bars15_ANC", sym)
        ts15 = epoch_secs(b15)
        hkey = (ts15 // 3600) * 3600
        med = pd.Series(b15["s_open"].to_numpy(float)).groupby(hkey).median()
        ts1h = epoch_secs(dev1h)
        spread15 = med.reindex(ts1h).to_numpy(float)
        return qcrd_dinv_m3(plane, spread15)
    emit("M3_SPREADGATEDFADE", m3)

    # Census families: v2_lib verbatim + frozen configs. v2_lib binds its
    # OWN ancestor engine module (E.PIP=1e4 == the pairs' pip multiplier);
    # if a module named "engine" is already loaded in this process it must
    # BE that ancestor (import-order law, checked not assumed).
    sys.path.insert(0, str(V2_SCRIPTS))
    import v2_lib as V2  # noqa: E402
    import engine as _v2engine  # noqa: E402  (resolves to v2's own engine)
    if not str(getattr(_v2engine, "__file__", "")).startswith(str(V2_SCRIPTS)):
        raise SystemExit(
            "FAIL_CLOSED import-order law: module 'engine' resolved to "
            f"{_v2engine.__file__}, not the census ancestor engine")
    for fam, (fname, pos_keys, configs) in CENSUS_FAMILIES.items():
        fn = getattr(V2, fname)
        for ci, cfg in enumerate(configs, start=1):
            emit(f"{fam}-C{ci}",
                 (lambda f=fn, c=cfg, pk=pos_keys: f(plane, *[c[k] for k in pk])))
    return status


def qcrd_dinv_m3(plane, spread15):
    from qcrd_dinv_lib import f_m3_spread_gated_fade
    return f_m3_spread_gated_fade(plane, spread15)


# ------------------------------------------------------------- main -----

def main() -> int:
    from governance import heavy_lock

    lock = None
    status, note = "FAILED", ""
    try:
        try:
            lock = heavy_lock.acquire(
                cycle_id="ERP1-TRACKA-COHORT-2",
                role="impl-t2-planes",
                worktree=str(LANE),
                command=[sys.executable, str(Path(__file__).resolve())],
                expected_artifacts=[str(DERIVED / "t2_planes_manifest.json")],
            )
        except heavy_lock.LockBusyError as e:
            print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT",
                              "reason": str(e)}))
            return 4
        return _build_all(lock)
    except Exception as e:  # noqa: BLE001
        note = f"{type(e).__name__}: {e}"[:400]
        raise
    finally:
        if lock is not None:
            lock.release(status=status, note=note)


def _build_all(lock) -> int:
    manifest = {
        "schema": "tracka2.t2_planes@1",
        "cycle_id": "ERP1-TRACKA-COHORT-2",
        "sealed_window_law": "all inputs via dev_plane2.load_bars "
                             "(ts<=2025-12-31 + row pins); M1 day files of "
                             "2026 never opened",
        "m1_source": {
            "raw_root_readonly": str(RAW_M1),
            "manifests": {s: sha256_file(C1_DUKA / f"m1_manifest_{s}.json")
                          for s in ("AUDUSD", "USDCAD")},
        },
        "code_shas": {
            name: sha256_file(LANE / "scripts" / name)
            for name in ("qcrd_dinv_lib.py", "build_t2_planes.py",
                         "dev_plane2.py", "pit_battery2.py", "tracka_lib.py")
        },
        "shadow_code_shas": {
            "v2_lib.py": sha256_file(V2_SCRIPTS / "v2_lib.py"),
            "v2_campaign.py": sha256_file(V2_SCRIPTS / "v2_campaign.py"),
        },
        "warmup_traded_days": WARMUP_TRADED_DAYS,
        "pairs": {},
    }

    for sym in ("AUDUSD", "USDCAD"):
        dev1h = dev_plane2.load_bars("bars1h_ANC", sym)   # pins asserted
        ts = epoch_secs(dev1h)

        # ---- M1 aggregates (heavy) ----
        agg = build_m1agg(sym, dev1h,
                          heartbeat=lambda extra=None: lock.heartbeat(
                              extra=extra or {}))
        if not (agg["ts"].to_numpy() == ts).all():
            raise SystemExit(f"FAIL_CLOSED {sym}: m1agg ts misalignment")
        bad = int((agg["m1_nmin"].to_numpy() != 60).sum())
        if bad:
            raise SystemExit(f"FAIL_CLOSED {sym}: {bad} bars without 60 "
                             "complete minutes")
        agg.to_parquet(DERIVED / f"m1agg_{sym}.parquet", index=False)
        df = attach_m1agg(dev1h, sym)

        # ---- candidate target arrays ----
        targets = {}
        for arm in P3A_ARMS:
            arr = qcrd_h1_target(df, mode=arm)
            p = DERIVED / f"t2_p3a_{sym}_{arm}.npy"
            np.save(p, arr.astype(np.int8))
            targets[f"p3a_{arm}"] = {
                "sha256": sha256_file(p), "n_nonzero": int((arr != 0).sum())}
        for arm in P3B_ARMS:
            arr = dinv_1d_target(df, mode=arm)
            p = DERIVED / f"t2_p3b_{sym}_{arm}.npy"
            np.save(p, arr.astype(np.int8))
            targets[f"p3b_{arm}"] = {
                "sha256": sha256_file(p), "n_nonzero": int((arr != 0).sum())}

        # ---- shadows ----
        shadows = build_shadows(sym, dev1h)

        manifest["pairs"][sym] = {
            "dev_rows": int(len(dev1h)),
            "dev_row_pin": dev_plane2.DEV_ROW_PINS[("bars1h_ANC", sym)],
            "row_pin_match": len(dev1h) == dev_plane2.DEV_ROW_PINS[("bars1h_ANC", sym)],
            "warmup_index": warmup_index(ts),
            "fold_table": fold_table(ts),
            "m1agg_sha256": sha256_file(DERIVED / f"m1agg_{sym}.parquet"),
            "targets": targets,
            "shadows": shadows,
        }
        lock.heartbeat(extra={"symbol": sym, "stage": "shadows_done"})
        print(json.dumps({sym: {
            "dev_rows": len(dev1h),
            "warmup_index": manifest["pairs"][sym]["warmup_index"],
            "folds": {k: v["n_traded_days"] for k, v
                      in manifest["pairs"][sym]["fold_table"].items()},
            "targets": {k: v["n_nonzero"] for k, v in targets.items()},
            "shadows_ok": sum(1 for v in shadows.values()
                              if v["status"] == "OK"),
            "shadows_nc": [k for k, v in shadows.items()
                           if v["status"] != "OK"],
        }}, indent=1), flush=True)

    out = DERIVED / "t2_planes_manifest.json"
    out.write_text(json.dumps(manifest, indent=1))
    print(json.dumps({"manifest": str(out)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
