"""pr12a100k — FX data plane + loaders (Lane I1a, cycle PORTFOLIO-ROUTER-12ASSETS-100K-V1).

Pure functions, NO network. Reads the 5 FX panels staged by earlier cycles:

  EURUSD/GBPUSD/USDJPY  M1 bid+ask daily Dukascopy ``.bi5`` candle corpora
                        (24-byte records ``>5if`` = sec,o,c,l,h,vol; per-pair
                        price scale; stamps are UTC — DST-verified).
  USDCAD/AUDUSD         pre-aggregated H1 "ANC" parquet panels built from the
                        same Dukascopy M1 feed by ERP1-TRACKA-COHORT-1
                        (open-stamped in source, converted to close-stamp
                        here; H/L are *ancestor convention*: computed from
                        minute closes, not intrabar extremes).

Conventions enforced by this module (documented in COVERAGE_NOTE.md):

  * All bar stamps are CLOSE time, UTC. A bar labeled ``T`` aggregates the
    half-open window ``(T-rule, T]``. At decision time ``T`` every bar with
    stamp ``<= T`` is fully completed — no lookahead by construction.
  * M1 minute stamps are close times: minute record ``sec`` covers
    ``[sec, sec+60)`` and is stamped ``sec+60``.
  * ``mid = (bid + ask) / 2``; spreads are in price units
    (pip sizes in ``FX_PANELS[symbol]["pip"]``).
  * Fail-closed: missing/malformed inputs raise; nothing is silently
    imputed or forward-filled.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct
from typing import Any, Iterable

import lzma
import numpy as np
import pandas as pd

__all__ = [
    "FX_PANELS",
    "REPO_ROOT",
    "load_macro_series",
    "asof",
    "decode_bi5_minutes",
    "load_fx_m1",
    "resample_bars",
    "load_fx_h1",
    "corpus_digest",
]

# ---------------------------------------------------------------------------
# Panel registry (measured 2026-09-28; see data_manifest_fx.json for evidence)
# ---------------------------------------------------------------------------

def _find_repo_root() -> str:
    """Walk up from this file to the checkout root that owns ``.worktrees/``.

    loaders.py lives at <root>/.worktrees/<cycle>/integration/research/
    pr12a100k/loaders.py, and the FX panels are staged inside *sibling*
    worktrees of the same root, so panel paths must anchor at that shared
    root — not at this cycle's worktree.
    """
    cur = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.isdir(os.path.join(cur, ".worktrees")) and os.path.isdir(
            os.path.join(cur, "research")
        ):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise RuntimeError(
        "could not locate the shared checkout root (directory owning "
        ".worktrees/ and research/) by walking up from loaders.py"
    )


REPO_ROOT = _find_repo_root()


def _p(*parts: str) -> str:
    return os.path.join(REPO_ROOT, ".worktrees", *parts)


FX_PANELS: dict[str, dict[str, Any]] = {
    "EURUSD": {
        "panel_path_glob": _p(
            "fx-rangefade-2m-shadow-v1", "research", "control",
            "FX-RANGEFADE-2M-SHADOW-V1", "data_local", "EURUSD", "M1", "{side}", "*.bi5",
        ),
        "source_worktree": ".worktrees/fx-rangefade-2m-shadow-v1",
        "provenance_cycle": "FX-RANGEFADE-2M-SHADOW-V1",
        "kind": "m1_bi5",
        "granularity": "M1",
        "scale": 1e5,
        "pip": 1e-4,
        "file_count_per_side": 2092,
        "first_active_ts": "2021-01-03T22:00:00+00:00",
        "last_active_ts": "2026-09-23T23:59:00+00:00",
    },
    "GBPUSD": {
        "panel_path_glob": _p(
            "fx-majors-search-v1", "integration", "research", "control",
            "FX-MAJORS-SEARCH-V1", "data_local", "GBPUSD", "M1", "{side}", "*.bi5",
        ),
        "source_worktree": ".worktrees/fx-majors-search-v1",
        "provenance_cycle": "FX-MAJORS-SEARCH-V1",
        "kind": "m1_bi5",
        "granularity": "M1",
        "scale": 1e5,
        "pip": 1e-4,
        "file_count_per_side": 2092,
        "first_active_ts": "2021-01-03T22:00:00+00:00",
        "last_active_ts": "2026-09-23T23:59:00+00:00",
    },
    "USDJPY": {
        "panel_path_glob": _p(
            "fx-majors-search-v1", "integration", "research", "control",
            "FX-MAJORS-SEARCH-V1", "data_local", "USDJPY", "M1", "{side}", "*.bi5",
        ),
        "source_worktree": ".worktrees/fx-majors-search-v1",
        "provenance_cycle": "FX-MAJORS-SEARCH-V1",
        "kind": "m1_bi5",
        "granularity": "M1",
        "scale": 1e3,
        "pip": 1e-2,
        "file_count_per_side": 2092,
        "first_active_ts": "2021-01-03T22:00:00+00:00",
        "last_active_ts": "2026-09-23T23:59:00+00:00",
    },
    "USDCAD": {
        "panel_path_glob": _p(
            "erp1-tracka-cohort-1", "repro_twin", "research", "control",
            "ERP1-TRACKA-COHORT-1", "data_local", "derived", "bars1h_ANC_USDCAD.parquet",
        ),
        "source_worktree": ".worktrees/erp1-tracka-cohort-1",
        "provenance_cycle": "ERP1-TRACKA-COHORT-1",
        "kind": "anc_h1_parquet",
        "granularity": "H1",
        "scale": 1e5,
        "pip": 1e-4,
        "rows": 30386,
        "first_active_ts": "2021-01-03T23:00:00+00:00",
        "last_active_ts": "2026-06-30T23:00:00+00:00",
    },
    "AUDUSD": {
        "panel_path_glob": _p(
            "erp1-tracka-cohort-1", "repro_twin", "research", "control",
            "ERP1-TRACKA-COHORT-1", "data_local", "derived", "bars1h_ANC_AUDUSD.parquet",
        ),
        "source_worktree": ".worktrees/erp1-tracka-cohort-1",
        "provenance_cycle": "ERP1-TRACKA-COHORT-1",
        "kind": "anc_h1_parquet",
        "granularity": "H1",
        "scale": 1e5,
        "pip": 1e-4,
        "rows": 30420,
        "first_active_ts": "2021-01-03T23:00:00+00:00",
        "last_active_ts": "2026-06-30T20:00:00+00:00",
    },
}


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def corpus_digest(side_dir: str) -> str:
    """Stable corpus digest: sha256 over sorted ``filename,size`` lines.

    Cheap (no file-content hashing), order-independent, and changes whenever
    any file is added/removed/resized. Full per-file sha256 manifests exist
    alongside each M1 corpus (``m1_manifest.json``, schema ``fxm.m1_manifest@1``)
    for content-level verification.
    """
    names = sorted(os.listdir(side_dir))
    lines = [f"{n},{os.path.getsize(os.path.join(side_dir, n))}" for n in names]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


# ---------------------------------------------------------------------------
# (a) Macro loaders — FRED fredgraph CSV + NY Fed EFFR JSON
# ---------------------------------------------------------------------------

MACRO_FORMATS = ("fredgraph_csv", "nyfed_effr_json")

_FRED_MISSING = {".", "", "-"}
_EFFR_LIST_KEYS = ("refRates", "data", "rates", "observations", "results")


def load_macro_series(path: str, fmt: str) -> tuple[pd.Series, dict[str, Any]]:
    """Load a macro series into a date-indexed pandas Series + metadata dict.

    Supported formats:

    ``fredgraph_csv``  FRED fredgraph.csv export: header
        ``observation_date,<SERIES_CODE>``; dates ``YYYY-MM-DD``; missing
        values encoded as ``'.'``; extra trailing columns are rejected
        (fail-closed). The value column name is recorded as the series name.

    ``nyfed_effr_json``  NY Fed rates API JSON: records with fields
        ``effectiveDate`` (ISO date), ``percentRate`` (string or number),
        ``revisionIndicator`` (bool). Accepts a top-level JSON array or an
        object whose list payload sits under a known key
        (``refRates``/``data``/``rates``/``observations``/``results``).

    Returns ``(series, metadata)`` where ``series`` is indexed by the
    observation/effective date (tz-naive calendar dates, midnight UTC by
    convention) with float values and NaN for missing observations, and
    ``metadata`` carries fmt/path/sha256/counts for the audit trail.

    Fail-closed: unknown fmt, missing file, wrong header, unparsable rows,
    or zero usable records all raise.
    """
    if fmt not in MACRO_FORMATS:
        raise ValueError(f"unknown macro format {fmt!r}; expected one of {MACRO_FORMATS}")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"macro file not found: {path}")

    sha = _sha256_file(path)
    if fmt == "fredgraph_csv":
        series, meta = _parse_fredgraph(path)
    else:
        series, meta = _parse_effr(path)

    meta.update({"fmt": fmt, "path": path, "sha256": sha})
    return series, meta


def _parse_fredgraph(path: str) -> tuple[pd.Series, dict[str, Any]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        lines = [ln.rstrip("\r\n") for ln in fh]
    lines = [ln for ln in lines if ln.strip() != ""]
    if not lines:
        raise ValueError(f"fredgraph CSV is empty: {path}")
    header = lines[0].split(",")
    if len(header) != 2 or header[0].strip() != "observation_date":
        raise ValueError(
            f"fredgraph CSV header must be 'observation_date,<SERIES>', got {lines[0]!r}"
        )
    series_name = header[1].strip()
    if not series_name:
        raise ValueError(f"fredgraph CSV has empty series column name: {path}")

    dates: list[str] = []
    values: list[float] = []
    n_missing = 0
    for i, ln in enumerate(lines[1:], start=2):
        parts = ln.split(",")
        if len(parts) != 2:
            raise ValueError(f"fredgraph CSV row {i} must have exactly 2 fields, got {ln!r}")
        d, v = parts[0].strip(), parts[1].strip()
        try:
            ts = pd.Timestamp(d)
        except ValueError as exc:
            raise ValueError(f"fredgraph CSV row {i}: unparsable date {d!r}") from exc
        if ts.time() != pd.Timestamp("00:00").time():
            raise ValueError(f"fredgraph CSV row {i}: expected calendar date, got {d!r}")
        dates.append(d)
        if v in _FRED_MISSING:
            values.append(np.nan)
            n_missing += 1
        else:
            try:
                values.append(float(v))
            except ValueError as exc:
                raise ValueError(
                    f"fredgraph CSV row {i}: unparsable value {v!r} (missing must be '.')"
                ) from exc

    if not dates:
        raise ValueError(f"fredgraph CSV has no data rows: {path}")
    idx = pd.to_datetime(dates)
    if idx.has_duplicates:
        dup = idx[idx.duplicated()][0]
        raise ValueError(f"fredgraph CSV has duplicate observation_date {dup.date()}")
    s = pd.Series(values, index=idx, name=series_name, dtype="float64")
    s.index.name = "observation_date"
    meta = {
        "series_name": series_name,
        "n_obs": len(s),
        "n_missing": int(n_missing),
        "first_date": str(idx.min().date()),
        "last_date": str(idx.max().date()),
        "missing_token": ".",
        "tz_convention": "calendar dates, midnight UTC",
    }
    return s, meta


def _parse_effr(path: str) -> tuple[pd.Series, dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    records: Any = None
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        for key in _EFFR_LIST_KEYS:
            if isinstance(payload.get(key), list):
                records = payload[key]
                break
    if not isinstance(records, list) or not records:
        raise ValueError(
            f"NY Fed EFFR JSON must be a non-empty array (top-level or under "
            f"one of {list(_EFFR_LIST_KEYS)}): {path}"
        )

    dates: list[str] = []
    values: list[float] = []
    revisions: list[tuple[str, bool]] = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise ValueError(f"EFFR record {i} is not an object: {rec!r}")
        missing = [f for f in ("effectiveDate", "percentRate", "revisionIndicator")
                   if f not in rec]
        if missing:
            raise ValueError(f"EFFR record {i} missing fields {missing}: {rec!r}")
        d = str(rec["effectiveDate"])[:10]
        try:
            ts = pd.Timestamp(d)
        except ValueError as exc:
            raise ValueError(f"EFFR record {i}: unparsable effectiveDate {d!r}") from exc
        rate = rec["percentRate"]
        try:
            val = float(rate)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"EFFR record {i}: unparsable percentRate {rate!r}") from exc
        dates.append(d)
        values.append(val)
        revisions.append((d, bool(rec["revisionIndicator"])))

    idx = pd.to_datetime(dates)
    if idx.has_duplicates:
        dup = idx[idx.duplicated()][0]
        raise ValueError(f"EFFR JSON has duplicate effectiveDate {dup.date()}")
    s = pd.Series(values, index=idx, name="EFFR", dtype="float64")
    s.index.name = "effectiveDate"
    meta = {
        "series_name": "EFFR",
        "n_obs": len(s),
        "n_missing": 0,
        "first_date": str(idx.min().date()),
        "last_date": str(idx.max().date()),
        "n_revisions": int(sum(1 for _, r in revisions if r)),
        "revisions": [(d, r) for d, r in revisions if r],
        "tz_convention": "calendar dates, midnight UTC",
    }
    return s, meta


# ---------------------------------------------------------------------------
# (d) PIT guard
# ---------------------------------------------------------------------------

_RULE_RE = re.compile(r"^T\+(\d+)d$")


def asof(series: pd.Series, decision_ts: pd.Timestamp | str, rule: str = "T+1d") -> float:
    """Point-in-time value of ``series`` at ``decision_ts`` under ``rule``.

    ``rule`` is a publication-lag string ``'T+Nd'`` (calendar days after the
    observation date): a value observed at date ``D`` becomes visible at
    ``available_at = D + N days`` (midnight UTC). ``asof`` returns the value
    of the last observation whose ``available_at <= decision_ts`` — i.e. the
    value that was *actually knowable* at the decision time. With ``T+1d``
    a value published at T+1 is never visible at T.

    Returns NaN when nothing is visible yet (start of history). Fail-closed
    on unknown rule strings and on non-monotonic/duplicate indices.
    """
    m = _RULE_RE.match(rule.strip())
    if not m:
        raise ValueError(f"unknown PIT rule {rule!r}; expected 'T+0d' or 'T+Nd'")
    lag = pd.Timedelta(days=int(m.group(1)))

    if series.index.has_duplicates:
        raise ValueError("asof: series index has duplicate dates")
    s = series.sort_index()
    # normalize to ns so searchsorted comparisons cannot mismatch resolutions
    idx = pd.DatetimeIndex(s.index).as_unit("ns")
    vals = s.to_numpy(dtype="float64")

    dt = pd.Timestamp(decision_ts)
    if dt.tzinfo is not None:
        dt = dt.tz_convert("UTC").tz_localize(None)
    dt = dt.as_unit("ns")

    available_at = idx + lag
    pos = int(available_at.searchsorted(dt, side="right")) - 1
    if pos < 0:
        return float("nan")
    value = vals[pos]
    return float(value) if np.isfinite(value) else float("nan")


# ---------------------------------------------------------------------------
# (b) M1 .bi5 corpus loader + resampler
# ---------------------------------------------------------------------------

_BI5_RECORD = struct.Struct(">5if")  # sec_offset, open, close, low, high, volume


def decode_bi5_minutes(raw: bytes, scale: float, day: pd.Timestamp) -> pd.DataFrame:
    """Decode one Dukascopy daily M1 candle ``.bi5`` payload.

    Each 24-byte big-endian record is ``(sec, open, close, low, high, vol)``
    with integer prices scaled by ``scale`` (per pair) and ``sec`` the offset
    in seconds from 00:00 UTC of ``day``. Stamps in the source are UTC
    (DST-verified: the 2021-03-14 US spring-forward file still has 1440
    records spanning 0..86340s).

    The returned frame is indexed by minute CLOSE time (sec+60) — see module
    docstring — with columns
    ``open, high, low, close, volume``.
    """
    if not raw:
        raise ValueError("empty .bi5 payload (fail-closed)")
    try:
        plain = lzma.decompress(raw)
    except lzma.LZMAError as exc:
        raise ValueError(f".bi5 payload is not valid LZMA: {exc}") from exc
    if len(plain) % _BI5_RECORD.size != 0:
        raise ValueError(
            f".bi5 payload length {len(plain)} not a multiple of "
            f"{_BI5_RECORD.size} bytes (corrupt file)"
        )

    day0 = pd.Timestamp(day).tz_localize("UTC").normalize()
    n = len(plain) // _BI5_RECORD.size
    arr = np.frombuffer(plain, dtype=np.dtype(">i4,>i4,>i4,>i4,>i4,>f4"))
    secs = arr["f0"].astype(np.int64)
    o = arr["f1"].astype(np.float64) / scale
    c = arr["f2"].astype(np.float64) / scale
    lo = arr["f3"].astype(np.float64) / scale
    hi = arr["f4"].astype(np.float64) / scale
    vol = arr["f5"].astype(np.float64)

    if n and np.any(np.diff(secs) <= 0):
        raise ValueError(".bi5 sec offsets not strictly increasing (corrupt file)")
    if n and (secs[0] < 0 or secs[-1] > 86340):
        raise ValueError(f".bi5 sec offset out of day range: {secs[-1]}")

    index = day0 + pd.to_timedelta(secs + 60, unit="s")  # close-time stamps
    df = pd.DataFrame(
        {"open": o, "high": hi, "low": lo, "close": c, "volume": vol},
        index=pd.DatetimeIndex(index, name="ts"),
    )
    return df


def _bi5_side_dir(symbol: str, side: str, root: str | None) -> str:
    cfg = FX_PANELS[symbol] if symbol in FX_PANELS else None
    if root is not None:
        return os.path.join(root, symbol, "M1", side.upper())
    if cfg is None or cfg["kind"] != "m1_bi5":
        raise ValueError(f"symbol {symbol!r} has no M1 bi5 panel registered")
    return os.path.dirname(cfg["panel_path_glob"].format(side=side.upper()))


def load_fx_m1(
    symbol: str,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
    root: str | None = None,
    tradable_only: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Union of BID+ASK M1 candles for ``symbol`` with mid + spread columns.

    Reads the daily ``.bi5`` corpora at the registered panel path (or under
    ``root/<SYMBOL>/M1/{BID,ASK}/`` when overridden — used by tests with tiny
    synthetic corpora). Returns a DataFrame indexed by UTC minute close time
    with columns::

        bid_o bid_h bid_l bid_c ask_o ask_h ask_l ask_c
        mid_o mid_c spread_open spread_close volume tradable

    * ``mid_*`` = (bid + ask) / 2 on the open/close fields.
    * ``spread_*`` = ask - bid in price units (pip size in FX_PANELS).
    * ``tradable`` = both sides present AND minute volume > 0 on both sides.
      Weekend/flat zero-volume carry-forward minutes are present in the raw
      corpus with o=c=l=h and volume 0; they carry ``tradable=False``.
    * One-sided minutes are kept with NaN on the missing side
      (outer union) and ``tradable=False``.

    ``tradable_only=True`` drops non-tradable minutes.
    Fail-closed: symbol without a corpus, zero files found in range,
    unreadable/corrupt files all raise.
    """
    if symbol not in FX_PANELS:
        raise ValueError(f"unknown FX symbol {symbol!r}; known: {sorted(FX_PANELS)}")

    d0 = pd.Timestamp(start).tz_localize("UTC").normalize() if start is not None else None
    d1 = pd.Timestamp(end).tz_localize("UTC").normalize() if end is not None else None

    sides: dict[str, pd.DataFrame] = {}
    file_counts: dict[str, int] = {}
    for side in ("BID", "ASK"):
        side_dir = _bi5_side_dir(symbol, side, root)
        if not os.path.isdir(side_dir):
            raise FileNotFoundError(f"{symbol} {side} corpus directory not found: {side_dir}")
        names = sorted(n for n in os.listdir(side_dir) if n.endswith(".bi5"))
        if d0 is not None:
            names = [n for n in names if n[:10] >= d0.date().isoformat()]
        if d1 is not None:
            names = [n for n in names if n[:10] <= d1.date().isoformat()]
        if not names:
            raise ValueError(
                f"{symbol} {side}: no .bi5 files in requested range "
                f"[{start}, {end}] under {side_dir}"
            )
        frames = []
        for name in names:
            with open(os.path.join(side_dir, name), "rb") as fh:
                raw = fh.read()
            day = pd.Timestamp(name[:10])
            frames.append(decode_bi5_minutes(raw, FX_PANELS[symbol]["scale"], day))
        merged = pd.concat(frames)
        merged = merged.rename(
            columns={
                "open": f"{side.lower()}_o",
                "high": f"{side.lower()}_h",
                "low": f"{side.lower()}_l",
                "close": f"{side.lower()}_c",
                "volume": f"{side.lower()}_volume",
            }
        )
        sides[side] = merged
        file_counts[side] = len(names)

    if len(sides["BID"]) == 0 or len(sides["ASK"]) == 0:
        raise ValueError(f"{symbol}: decoded corpora are empty (fail-closed)")

    df = sides["BID"].join(sides["ASK"], how="outer").sort_index()
    df["mid_o"] = (df["bid_o"] + df["ask_o"]) / 2.0
    df["mid_c"] = (df["bid_c"] + df["ask_c"]) / 2.0
    df["spread_open"] = df["ask_o"] - df["bid_o"]
    df["spread_close"] = df["ask_c"] - df["bid_c"]
    df["volume"] = df["bid_volume"]
    bid_ok = df[["bid_o", "bid_h", "bid_l", "bid_c", "bid_volume"]].notna().all(axis=1)
    ask_ok = df[["ask_o", "ask_h", "ask_l", "ask_c", "ask_volume"]].notna().all(axis=1)
    df["tradable"] = bid_ok & ask_ok & (df["bid_volume"] > 0) & (df["ask_volume"] > 0)
    df = df.drop(columns=["bid_volume", "ask_volume"])

    if tradable_only:
        df = df[df["tradable"]]
        if df.empty:
            raise ValueError(f"{symbol}: no tradable minutes in range (fail-closed)")

    meta = {
        "symbol": symbol,
        "granularity": "M1",
        "index_tz": "UTC",
        "stamp_convention": "minute close time",
        "rows": int(len(df)),
        "first_ts": str(df.index.min()),
        "last_ts": str(df.index.max()),
        "files": file_counts,
        "pip": FX_PANELS[symbol]["pip"],
        "tradable_rows": int(df["tradable"].sum()) if "tradable" in df else 0,
        "provenance_cycle": FX_PANELS[symbol]["provenance_cycle"],
    }
    return df, meta


def resample_bars(m1: pd.DataFrame, rule: str = "h") -> pd.DataFrame:
    """Resample minute bars to H1 (``'h'``) or D1 (``'d'``) CLOSE-stamped bars.

    Buckets on the close-stamped minute index with ``closed='right',
    label='right'`` so an H1 bar labeled ``23:00`` aggregates minutes whose
    close stamps fall in ``(22:00, 23:00]`` (wall-clock 22:00:00–22:59:59),
    and a D1 bar labeled ``2021-01-05 00:00`` aggregates the UTC calendar
    day 2021-01-04. At decision time T, every bar stamped <= T is complete.

    Buckets with no source minutes are dropped (no fabrication): real panels
    show 24 H1 bars per UTC day; a 23- or 25-bar day would only appear if the
    feed itself lost/duplicated an hour (see the DST test).

    Output columns: ``{bid,ask,mid}_{o,h,l,c}``, ``spread_open``,
    ``spread_close``, ``spread_mean``, ``volume`` (sum of per-minute
    min(bid_vol, ask_vol) where present), ``n_minutes``.
    """
    if rule not in ("h", "d", "D"):
        raise ValueError(f"rule must be 'h' or 'd', got {rule!r}")
    if m1.empty:
        raise ValueError("cannot resample an empty minute frame")
    freq = {"h": "h", "d": "D", "D": "D"}[rule]  # pandas deprecates lowercase 'd'

    df = m1.copy()
    # (output_name, source_column, func) — several outputs read the same
    # source column with different funcs, so aggregate via a col->funcs map
    # (Resampler.agg does not accept named-agg kwargs in pandas 3) and then
    # flatten the resulting MultiIndex columns.
    specs: list[tuple[str, str, str]] = []
    for pre in ("bid", "ask", "mid"):
        for suffix, func in (("o", "first"), ("h", "max"), ("l", "min"), ("c", "last")):
            col = f"{pre}_{suffix}"
            if col in df.columns:
                specs.append((col, col, func))
    specs += [
        ("spread_open", "spread_open", "first"),
        ("spread_close", "spread_close", "last"),
        ("spread_mean", "spread_open", "mean"),
    ]
    if "volume" in df.columns:
        specs.append(("volume", "volume", "sum"))
    count_col = "mid_c" if "mid_c" in df.columns else "bid_c"
    specs.append(("n_minutes", count_col, "size"))

    col_funcs: dict[str, list[str]] = {}
    name_of: dict[tuple[str, str], str] = {}
    for out_name, col, func in specs:
        col_funcs.setdefault(col, []).append(func)
        name_of[(col, func)] = out_name

    grouped = df.resample(freq, closed="right", label="right")
    out = grouped.agg(col_funcs)
    out.columns = [name_of[(c, f)] for c, f in out.columns]
    out = out.dropna(
        subset=[c for c in ("bid_o", "ask_o", "mid_o") if c in out.columns], how="all"
    )
    if out.empty:
        raise ValueError("resample produced zero bars (fail-closed)")
    out.index.name = "ts"
    return out


# ---------------------------------------------------------------------------
# (c) ANC H1 parquet loader (USDCAD / AUDUSD)
# ---------------------------------------------------------------------------

_ANC_RENAME = {
    "b_o": "bid_o", "b_h": "bid_h", "b_l": "bid_l", "b_c": "bid_c",
    "a_o": "ask_o", "a_c": "ask_c",
}


def load_fx_h1(symbol: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load a pre-aggregated H1 'ANC' panel (USDCAD / AUDUSD) as close-stamped bars.

    Source (ERP1-TRACKA-COHORT-1, ``bars1h_ANC_<SYM>.parquet``): hourly bars
    built from Dukascopy M1 with a tradable filter (volume > 0, registered
    price band, ask >= bid, strictly consecutive minutes) — hence sparse:
    weekend hours and the ~21:00–22:00 UTC rollover hour are absent by
    construction, not data loss. Source columns ``ts, b_o, b_h, b_l, b_c,
    a_o, a_c, s_open, s_close`` are OPEN-stamped; this loader shifts the
    stamp +1h to the module-wide CLOSE-time convention.

    CAVEAT (documented in COVERAGE_NOTE.md): ``bid_h``/``bid_l`` in the ANC
    panels follow the ancestor convention — max/min of minute CLOSES, not
    intrabar extremes — inherited from the ERP1 signal plane.

    Returns frame indexed by UTC close time with columns ``bid_o, bid_h,
    bid_l, bid_c, ask_o, ask_c, mid_o, mid_c, spread_open, spread_close``.
    """
    if symbol not in FX_PANELS or FX_PANELS[symbol]["kind"] != "anc_h1_parquet":
        raise ValueError(f"symbol {symbol!r} has no ANC H1 panel (USDCAD/AUDUSD only)")
    path = FX_PANELS[symbol]["panel_path_glob"]
    if not os.path.isfile(path):
        raise FileNotFoundError(f"ANC H1 parquet not found: {path}")

    raw = pd.read_parquet(path)
    need = {"ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c", "s_open", "s_close"}
    missing = need - set(raw.columns)
    if missing:
        raise ValueError(f"ANC parquet {path} missing columns {sorted(missing)}")

    df = raw.rename(columns=_ANC_RENAME).copy()
    idx = pd.DatetimeIndex(df["ts"])
    if idx.tz is None:
        raise ValueError(f"ANC parquet {path}: ts must be tz-aware UTC")
    df.index = pd.DatetimeIndex(idx.tz_convert("UTC")) + pd.Timedelta(hours=1)
    df.index.name = "ts"
    df = df.drop(columns=["ts"]).sort_index()
    if df.index.has_duplicates:
        raise ValueError(f"ANC parquet {path}: duplicate timestamps after close-shift")
    df["mid_o"] = (df["bid_o"] + df["ask_o"]) / 2.0
    df["mid_c"] = (df["bid_c"] + df["ask_c"]) / 2.0
    df["spread_open"] = df["s_open"]
    df["spread_close"] = df["s_close"]
    df = df.drop(columns=["s_open", "s_close"])

    meta = {
        "symbol": symbol,
        "granularity": "H1",
        "index_tz": "UTC",
        "stamp_convention": "hour close time (source open-stamped, shifted +1h)",
        "rows": int(len(df)),
        "first_ts": str(df.index.min()),
        "last_ts": str(df.index.max()),
        "hl_convention": "ancestor: bid_h/bid_l are max/min of M1 closes, not intrabar extremes",
        "tradable_filter": "vol>0, price band, ask>=bid, consecutive minutes (weekend+rollover hours absent)",
        "sha256": _sha256_file(path),
        "provenance_cycle": FX_PANELS[symbol]["provenance_cycle"],
        "pip": FX_PANELS[symbol]["pip"],
    }
    return df, meta
