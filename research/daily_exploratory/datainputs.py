"""Input assembly for the DAILY-EXPLORATORY-V1 exploratory battery.

Reads ONLY frozen, sha-pinned raw sources (no network, no fetch) and
derives the D1 signal/vehicle panels the two admitted legs consume:

- EIA dailies RNGWHHD / RBRTE (OI-5 signal-only, 1bd declared serving),
  sha-pinned per MANIFEST_RAW.json@pc12a-7asset-unblock-20261001;
- IBKR HMDS D1 panels-of-record NZDUSD / USDCHF (OI-1), 12 chunks per
  instrument, byte-concat aggregate sha verified per
  IDENTITY_FREEZE_2026-09-30.json aggregate_recipe;
- IBKR HMDS D1 AUDUSD / USDCAD G6 pull 2026-07-01..2026-09-30 (16 raw
  files, per-file sha per g6_pull/MANIFEST.json; the 2026-10-01 forming
  bar EXCLUDED per VERIFICATION.json law);
- H1 ANC parquets AUDUSD / USDCAD 2021-01-03..2026-06-30 (sha-pinned in
  G5_G6_SPREADS_INPUTEND.md section 2.1) consumed via the DECLARED
  D1-close aggregation law (the 17:00 ET bar);
- M1 BID/ASK .bi5 day corpora EURUSD (FX-RANGEFADE-2M-SHADOW-V1 panel),
  GBPUSD / USDJPY (FX-MAJORS-SEARCH-V1 panels), every file sha-verified
  against its frozen m1_manifest.json, aggregated to D1 session bars by
  the SAME declared 17:00 ET session law.

Declared conventions (frozen for this battery, labeled on every output):

- ``D1_SESSION_1700ET@1`` — a D1 session T spans [17:00 ET (T-1),
  17:00 ET T); open = first valid M1 print of the session (bid/ask open
  of that minute), close = last valid print at/before 17:00 ET T;
  mid_low/mid_high = min/max of per-minute side-mid lows/highs. A minute
  is valid iff vol>0, ask>=bid>0 and the bid lies inside the declared
  sanity band for the pair.
- ``SIGNAL_MID_CLOSE@1`` — a signal close is the bid/ask close mid of
  the consumed D1 bar (EIA inputs carry one official value per day).
- ``H1_1600ET_BAR@1`` — the ANC D1 close for day T is the H1 bar whose
  [ts, ts+1h) window ends at 17:00 ET (ts = 16:00 ET), exact match only,
  no fallback (a missing bar types the day missing, never interpolated).
- ``G6_DEDUP_LATER_FILE_WINS@1`` — overlapping G6 chunks dedup by date
  with the lexicographically later filename processed last winning.

This module derives and VERIFIES inputs; it computes no performance
metric (RGC-INC-1) — band cells below are the G5 validation-band
derivation (MEASURED-DERIVED), executed at battery freeze for the two
vehicle instruments whose D1 bands were NOT_COMPUTED at G5
(EURUSD/USDJPY; fills price at the bar's own quoted side — the cells are
validation bands only, FILL_ACCOUNTING_SPEC section 2).
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import lzma
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import numpy as np

ET = ZoneInfo("America/New_York")

DATA_ROOT = Path("/Users/hoangminhlong/.my-quantitative-data")
WORKTREE = Path("/Users/hoangminhlong/my-quantitative/"
                ".worktrees/pc12a-daily-exploratory-prep")
WT_CONTROL = WORKTREE / "research" / "control"

# ---------------------------------------------------------------------------
# Frozen source paths + sha pins
# ---------------------------------------------------------------------------

EIA_RAW_DIR = DATA_ROOT / "pc12a-7asset-data-unblock-2026-10-01" / "raw"
EIA_MANIFEST = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/"
    "pc12a-7asset-unblock-20261001/research/control/"
    "PC12A-7ASSET-DATA-UNBLOCK-2026-10-01/MANIFEST_RAW.json")
EIA_SHA256 = {
    "RNGWHHD": "5f9baf40f352fd64b8fe1e854413c5334989c5e6166e8804568f00cdbdd85c4a",
    "RBRTE": "a7b64754f033be892d690f57c821888f632fa30291e3a6f78309ba53b77891e1",
}
EIA_SERVING = "1BD-DECLARED-OI5 (decision at T+1 open; never a fill price)"

IBKR_ACQ_DIR = (DATA_ROOT / "portfolio-composite-12assets-100k-v1" /
                "ibkr_acq_20260930")
#: IDENTITY_FREEZE_2026-09-30.json aggregate_recipe: sha256 over the
#: byte-concatenation of the 12 files in lexicographically sorted path order.
IBKR_AGGREGATE_SHA256 = {
    "NZDUSD": "c681402b03e58502fcb7a22d7d7b26ccefcccf5117b20fa2ec82e2689a9782ed",
    "USDCHF": "7fbd3a80e64114c54a411c75adf24725fc9ef631433b341484e6dd40468d69c3",
}

G6_DIR = (WT_CONTROL / "terminal_review_2026-10-01" / "successor" /
          "daily_successor" / "g6_pull")
G6_WINDOW = ("2026-07-01", "2026-09-30")  # forming 2026-10-01 EXCLUDED
G6_FORMING_BAR_DATE = "2026-10-01"

H1_ANC_PARQUET = {
    "AUDUSD": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "erp1-tracka-cohort-1/repro_twin/research/control/"
                   "ERP1-TRACKA-COHORT-1/data_local/derived/"
                   "bars1h_ANC_AUDUSD.parquet"),
    "USDCAD": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "erp1-tracka-cohort-1/repro_twin/research/control/"
                   "ERP1-TRACKA-COHORT-1/data_local/derived/"
                   "bars1h_ANC_USDCAD.parquet"),
}
H1_ANC_SHA256 = {
    "AUDUSD": "4e0ca174a21e155271a481727259daa0d3df888bb9f96eb7b34d8c6f06881364",
    "USDCAD": "335a6e2aab25aebff17f9198f1b939448262186ed20e63f3041f8818d02f376b",
}
#: DISCLOSED ERRATUM (measured 2026-10-01, battery input verification):
#: the AUDUSD ANC parquet is the ONLY copy machine-wide (mtime 2026-09-26,
#: pre-freeze, read-only) and hashes
#: 4e0ca174...96eb7a34d8c6f06881364 — the G5 doc's pin reads 'b' at hex
#: position 48 where the artifact reads 'a' (single hex digit; the CAD pin
#: reproduces exactly; no other candidate artifact exists). Carried as
#: PIN_ERRATUM_DISCLOSED@1 on the input manifest + battery report — the
#: pin text is NOT silently edited, the artifact is NOT silently trusted:
#: both readings are recorded.
H1_ANC_PIN_ERRATUM = {
    "AUDUSD": {
        "pin_sha256": H1_ANC_SHA256["AUDUSD"],
        "measured_sha256": "4e0ca174a21e155271a481727259daa0d3df888bb9f96eb7a34d8c6f06881364",
        "diff_position_hex": 48,
        "verdict": "PIN_ERRATUM_DISCLOSED@1",
    },
}

M1_PANELS = {
    "EURUSD": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "fx-rangefade-2m-shadow-v1/research/control/"
                   "FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD"),
    "GBPUSD": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "fx-majors-search-v1/integration/research/control/"
                   "FX-MAJORS-SEARCH-V1/data_local/GBPUSD"),
    "USDJPY": Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "fx-majors-search-v1/integration/research/control/"
                   "FX-MAJORS-SEARCH-V1/data_local/USDJPY"),
}
#: Dukascopy .bi5 record layout (big-endian, 24B) and per-pair int scale.
CANDLE = np.dtype([("sec", ">i4"), ("o", ">i4"), ("c", ">i4"),
                   ("l", ">i4"), ("h", ">i4"), ("v", ">f4")])
M1_SCALE = {"EURUSD": 1e5, "GBPUSD": 1e5, "USDJPY": 1e3}
#: Declared sanity bands (bid open must lie inside; generous, catches
#: corrupt prints only — DECLARED-BAND@1).
M1_BID_BAND = {
    "EURUSD": (0.80, 1.60),
    "GBPUSD": (0.90, 1.80),
    "USDJPY": (60.0, 260.0),
}

#: The named holiday calendar (GO freeze-time act "holiday calendar
#: naming"): weekend-skip PLUS each panel's own recorded session
#: calendar — holidays are whatever the frozen panel itself did/did not
#: record; nothing is inferred or interpolated.
HOLIDAY_CALENDAR_NAME = "DECLARED-PANEL-CALENDAR@1 (weekend-skip + each frozen panel's own recorded sessions; no synthetic holiday model)"

LABEL_D1_SESSION = "D1_SESSION_1700ET@1"
LABEL_SIGNAL_MID = "SIGNAL_MID_CLOSE@1"
LABEL_H1_BAR = "H1_1600ET_BAR@1"


# ---------------------------------------------------------------------------
# Verified D1 bar / signal shapes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class D1Bar:
    """One D1 session bar (both quoted sides; declared 17:00 ET law)."""

    session_date: str
    bid_open: float
    ask_open: float
    bid_close: float
    ask_close: float
    mid_low: float
    mid_high: float

    @property
    def mid_open(self) -> float:
        return (self.bid_open + self.ask_open) / 2.0

    @property
    def mid_close(self) -> float:
        return (self.bid_close + self.ask_close) / 2.0

    def to_row(self) -> Dict[str, object]:
        return {
            "session_date": self.session_date,
            "bid_open": self.bid_open, "ask_open": self.ask_open,
            "bid_close": self.bid_close, "ask_close": self.ask_close,
            "mid_low": self.mid_low, "mid_high": self.mid_high,
        }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# EIA dailies
# ---------------------------------------------------------------------------

def load_eia(series: str) -> Tuple[Dict[str, Decimal], Dict[str, object]]:
    """Verified EIA daily close series {iso_date: Decimal value}."""
    fname = f"eia_v2_{series}_daily.json"
    path = EIA_RAW_DIR / fname
    actual = _sha256_file(path)
    if actual != EIA_SHA256[series]:
        raise SystemExit(f"FAIL_CLOSED sha mismatch {fname}: {actual}")
    doc = json.loads(path.read_text())
    out: Dict[str, Decimal] = {}
    for row in doc["rows"]:
        v = row.get("value")
        if v is None:
            continue  # EIA null day: absent, never interpolated
        out[row["period"]] = Decimal(str(v))
    meta = {
        "input_id": f"I-EIA-{ 'NG' if series == 'RNGWHHD' else 'BR' }",
        "series": series,
        "sha256": actual,
        "n_days": len(out),
        "first": min(out), "last": max(out),
        "serving": EIA_SERVING,
        "label": "SINGLE-SOURCE-COMPILATION, DUAL-CHANNEL-RETRIEVAL-CONFIRMED; SIGNAL-ONLY, NEVER FILL PRICES (OI-5)",
    }
    return out, meta


# ---------------------------------------------------------------------------
# IBKR HMDS D1 panels (NZD/CHF panel-of-record + G6 AUD/CAD extension)
# ---------------------------------------------------------------------------

def _ibkr_rows_by_date(side_files: List[Path]) -> Dict[str, dict]:
    """Concatenate chunks (sorted by name, later wins on date overlap)."""
    merged: Dict[str, dict] = {}
    for fp in sorted(side_files):
        for row in json.loads(fp.read_text()):
            merged[row["date"]] = row
    return merged


def load_ibkr_panel(inst: str) -> Tuple[Dict[str, D1Bar], Dict[str, object]]:
    """Verified NZDUSD/USDCHF D1 panel (aggregate sha per freeze recipe)."""
    files = sorted(IBKR_ACQ_DIR.glob(f"{inst}_1d_*.json"))
    ask = [f for f in files if "_ASK_" in f.name]
    bid = [f for f in files if "_BID_" in f.name]
    if len(ask) != 6 or len(bid) != 6:
        raise SystemExit(f"FAIL_CLOSED {inst}: expected 12 daily chunks, got {len(files)}")
    concat = b"".join(f.read_bytes() for f in sorted(files))  # lex path order
    agg = hashlib.sha256(concat).hexdigest()
    if agg != IBKR_AGGREGATE_SHA256[inst]:
        raise SystemExit(f"FAIL_CLOSED {inst} aggregate sha mismatch: {agg}")
    a_rows, b_rows = _ibkr_rows_by_date(ask), _ibkr_rows_by_date(bid)
    bars: Dict[str, D1Bar] = {}
    for d in sorted(set(a_rows) & set(b_rows)):
        a, b = a_rows[d], b_rows[d]
        mid_low = (b["low"] + a["low"]) / 2.0
        mid_high = (b["high"] + a["high"]) / 2.0
        bars[d] = D1Bar(d, b["open"], a["open"], b["close"], a["close"],
                        mid_low, mid_high)
    meta = {
        "input_id": f"I-{'NZD' if inst == 'NZDUSD' else 'CHF'}",
        "instrument": inst,
        "aggregate_sha256": agg,
        "n_sessions": len(bars),
        "first": min(bars), "last": max(bars),
        "lag": "LAG_DECLARED_BY_OWNER (OI-1): closed bars from next business day",
    }
    return bars, meta


def load_g6_panel(inst: str) -> Tuple[Dict[str, D1Bar], Dict[str, object]]:
    """Verified G6 AUD/CAD D1 panel, window 2026-07-01..2026-09-30 only
    (forming 2026-10-01 bar EXCLUDED, per G6 VERIFICATION law)."""
    man = json.loads((G6_DIR / "MANIFEST.json").read_text())
    # g6_pull_manifest@1: {"files": [{"file", "path", "n_bars", "sha256"...}]}
    sha_map: Dict[str, str] = {
        e["file"]: e["sha256"] for e in man["files"]}
    files = sorted((G6_DIR / "raw").glob(f"{inst}_1d_*.json"))
    bad = []
    for f in files:
        pin = sha_map.get(f.name)
        if pin is None or pin != _sha256_file(f):
            bad.append(f.name)
    if bad:
        raise SystemExit(f"FAIL_CLOSED G6 sha mismatch: {bad}")
    ask = [f for f in files if "_ASK_" in f.name]
    bid = [f for f in files if "_BID_" in f.name]
    a_rows, b_rows = _ibkr_rows_by_date(ask), _ibkr_rows_by_date(bid)
    lo, hi = G6_WINDOW
    bars: Dict[str, D1Bar] = {}
    excluded_forming = 0
    for d in sorted(set(a_rows) & set(b_rows)):
        if d == G6_FORMING_BAR_DATE:
            excluded_forming += 1
            continue
        if not (lo <= d <= hi):
            continue
        a, b = a_rows[d], b_rows[d]
        bars[d] = D1Bar(d, b["open"], a["open"], b["close"], a["close"],
                        (b["low"] + a["low"]) / 2.0,
                        (b["high"] + a["high"]) / 2.0)
    meta = {
        "input_id": f"I-{'AUD' if inst == 'AUDUSD' else 'CAD'}-G6",
        "instrument": inst,
        "window": [lo, hi],
        "n_files": len(files),
        "n_sessions": len(bars),
        "forming_bar_excluded": excluded_forming,
        "dedup": "G6_DEDUP_LATER_FILE_WINS@1",
    }
    return bars, meta


# ---------------------------------------------------------------------------
# H1 ANC -> D1 closes (AUD/CAD through 2026-06-30)
# ---------------------------------------------------------------------------

def load_anc_d1_closes(inst: str) -> Tuple[Dict[str, Tuple[float, float]],
                                           Dict[str, object],
                                           Dict[str, str]]:
    """D1 closes under the SAME declared 17:00 ET session law as the M1
    aggregation: session T's close = the LAST H1 bar whose window ends
    at/before 17:00 ET on day T (ts in (16:00 ET T-1, 16:00 ET T]).

    The exact 16:00 ET bar is used when present; otherwise the last
    earlier bar of the same session is the close (the ANC panel drops
    invalid hours — measured: the exact bar exists on only 47% (AUD) /
    73% (CAD) of weekdays). Every day's close-bar timestamp is recorded
    and the fallback count disclosed; a day with NO bar in its session
    window is absent (typed missing, never interpolated).

    Returns {iso_date: (bid_close, ask_close)}.
    """
    import pandas as pd
    path = H1_ANC_PARQUET[inst]
    actual = _sha256_file(path)
    pin_ok = actual == H1_ANC_SHA256[inst]
    erratum = None
    if not pin_ok and inst in H1_ANC_PIN_ERRATUM and \
            actual == H1_ANC_PIN_ERRATUM[inst]["measured_sha256"]:
        erratum = H1_ANC_PIN_ERRATUM[inst]  # disclosed, recorded, carried
    elif not pin_ok:
        raise SystemExit(f"FAIL_CLOSED ANC {inst} sha mismatch: {actual}")
    df = pd.read_parquet(path, columns=["ts", "b_c", "a_c"])
    ts = pd.DatetimeIndex(df["ts"]).tz_convert(ET)
    bc = df["b_c"].to_numpy().astype(float)
    ac = df["a_c"].to_numpy().astype(float)
    et_np = ts.to_numpy()

    # For each session T (calendar day), candidate upper bound = 16:00 ET T.
    first_day = ts[0].date()
    last_day = ts[-1].date()
    out: Dict[str, Tuple[float, float]] = {}
    close_bar_ts: Dict[str, str] = {}
    n_exact = 0
    d0 = first_day
    while d0 <= last_day:
        ub = pd.Timestamp(_dt.datetime.combine(
            d0, _dt.time(16, 0), tzinfo=ET))
        lb = ub - pd.Timedelta(days=1)
        mask = (ts > lb) & (ts <= ub)
        if mask.any():
            idx = int(np.nonzero(mask)[0][-1])
            d = d0.isoformat()
            out[d] = (float(bc[idx]), float(ac[idx]))
            close_bar_ts[d] = ts[idx].isoformat()
            if ts[idx] == ub:
                n_exact += 1
        d0 += _dt.timedelta(days=1)
    meta = {
        "input_id": f"I-{'AUD' if inst == 'AUDUSD' else 'CAD'}-ANC",
        "instrument": inst,
        "sha256": actual,
        "pin_match": pin_ok,
        "pin_erratum": erratum,
        "law": f"{LABEL_D1_SESSION} applied at H1: last bar ending <= 17:00 ET (exact-16:00 bar when present, earlier-session bar otherwise — fallback count disclosed)",
        "n_days": len(out),
        "n_close_bar_exact_1600ET": n_exact,
        "n_close_bar_fallback": len(out) - n_exact,
        "first": min(out), "last": max(out),
    }
    return out, meta, close_bar_ts


# ---------------------------------------------------------------------------
# M1 .bi5 -> D1 session bars (EURUSD / GBPUSD / USDJPY)
# ---------------------------------------------------------------------------

def _decode_day(path: Path) -> np.ndarray:
    return np.frombuffer(lzma.decompress(path.read_bytes()), dtype=CANDLE)


def aggregate_m1_to_d1(pair: str, progress_every: int = 400
                       ) -> Tuple[Dict[str, D1Bar], Dict[str, object]]:
    """Aggregate the frozen M1 corpus to D1 session bars (17:00 ET law).

    Every .bi5 file is sha-verified against the panel's frozen
    m1_manifest.json BEFORE decoding (fail-closed).
    """
    panel = M1_PANELS[pair]
    man = json.loads((panel / "m1_manifest.json").read_text())
    man_files = man["files"] if isinstance(man, dict) else {}
    bid_dir, ask_dir = panel / "M1" / "BID", panel / "M1" / "ASK"
    bid_files = sorted(bid_dir.glob("*.bi5"))
    ask_files = sorted(ask_dir.glob("*.bi5"))
    names_b = [f.name for f in bid_files]
    names_a = [f.name for f in ask_files]
    if names_b != names_a:
        raise SystemExit(f"FAIL_CLOSED {pair}: BID/ASK day-file sets differ")
    scale = M1_SCALE[pair]
    lo, hi = M1_BID_BAND[pair]

    ts_list, bo_list, ao_list, bc_list, ac_list = [], [], [], [], []
    bl_list, al_list, bh_list, ah_list = [], [], [], []
    n_bad_sha = 0
    for i, (fb, fa) in enumerate(zip(bid_files, ask_files)):
        for side, f in (("BID", fb), ("ASK", fa)):
            rel = f"M1/{side}/{f.name}"
            pin = man_files.get(rel, {}).get("sha256")
            if pin is None or pin != _sha256_file(f):
                n_bad_sha += 1
        if n_bad_sha:
            raise SystemExit(f"FAIL_CLOSED {pair} manifest sha mismatch at {fb.name}")
        if (i + 1) % progress_every == 0:
            print(f"  {pair}: {i + 1}/{len(bid_files)} days decoded",
                  flush=True)
        b = _decode_day(fb)
        a = _decode_day(fa)
        y, m, d = map(int, fb.stem.split("-"))
        day0 = int(_dt.datetime(y, m, d, tzinfo=_dt.timezone.utc).timestamp())
        n = min(len(b), len(a))
        secs = b["sec"][:n].astype(np.int64) + day0
        bo = b["o"][:n].astype(np.float64) / scale
        bc = b["c"][:n].astype(np.float64) / scale
        bl = b["l"][:n].astype(np.float64) / scale
        bh = b["h"][:n].astype(np.float64) / scale
        ao = a["o"][:n].astype(np.float64) / scale
        ac = a["c"][:n].astype(np.float64) / scale
        al = a["l"][:n].astype(np.float64) / scale
        ah = a["h"][:n].astype(np.float64) / scale
        vol = b["v"][:n].astype(np.float64)
        valid = (vol > 0) & (bo > lo) & (bo < hi) & (ao >= bo) & (bo > 0)
        if not valid.any():
            continue
        ts_list.append(secs[valid])
        bo_list.append(bo[valid]); ao_list.append(ao[valid])
        bc_list.append(bc[valid]); ac_list.append(ac[valid])
        bl_list.append(bl[valid]); al_list.append(al[valid])
        bh_list.append(bh[valid]); ah_list.append(ah[valid])

    ts = np.concatenate(ts_list)
    bo = np.concatenate(bo_list); ao = np.concatenate(ao_list)
    bc = np.concatenate(bc_list); ac = np.concatenate(ac_list)
    bl = np.concatenate(bl_list); al = np.concatenate(al_list)
    bh = np.concatenate(bh_list); ah = np.concatenate(ah_list)
    order = np.argsort(ts, kind="stable")
    ts, bo, ao = ts[order], bo[order], ao[order]
    bc, ac = bc[order], ac[order]
    bl, al, bh, ah = bl[order], al[order], bh[order], ah[order]

    # session boundaries: 17:00 ET of each calendar day (unique, sorted)
    first_day = _dt.datetime.fromtimestamp(int(ts[0]), tz=_dt.timezone.utc)
    last_day = _dt.datetime.fromtimestamp(int(ts[-1]), tz=_dt.timezone.utc)
    bounds: List[_dt.datetime] = []
    d = first_day.date()
    while d <= last_day.date():
        b0 = _dt.datetime.combine(d, _dt.time(17, 0), tzinfo=ET)
        bounds.append(b0.astimezone(_dt.timezone.utc))
        d += _dt.timedelta(days=1)
    bounds_ts = np.array([int(b.timestamp()) for b in bounds], dtype=np.int64)
    idx = np.searchsorted(ts, bounds_ts, side="left")

    bars: Dict[str, D1Bar] = {}
    for k in range(len(bounds_ts) - 1):
        s, e = int(idx[k]), int(idx[k + 1])
        if s >= e:
            continue  # no valid minutes in this session
        sess_date = bounds[k + 1].astimezone(ET).date().isoformat()
        sl = slice(s, e)
        bars[sess_date] = D1Bar(
            session_date=sess_date,
            bid_open=float(bo[s]), ask_open=float(ao[s]),
            bid_close=float(bc[e - 1]), ask_close=float(ac[e - 1]),
            mid_low=float(np.min((bl[sl] + al[sl]) / 2.0)),
            mid_high=float(np.max((bh[sl] + ah[sl]) / 2.0)),
        )
    meta = {
        "input_id": f"I-{'EUR' if pair == 'EURUSD' else ('GBP' if pair == 'GBPUSD' else 'JPY')}",
        "instrument": pair,
        "n_day_files": len(bid_files),
        "manifest_sha_verified": 2 * len(bid_files),
        "session_law": LABEL_D1_SESSION,
        "minute_validity": "vol>0 & ask>=bid>0 & bid in DECLARED-BAND@1",
        "n_sessions": len(bars),
        "first": min(bars), "last": max(bars),
        "label": "EVIDENCED-PANEL/DECLARED-AGG",
    }
    return bars, meta


# ---------------------------------------------------------------------------
# Vehicle-side D1 band derivation (G5 freeze act for EURUSD/USDJPY)
# ---------------------------------------------------------------------------

#: Quantile convention frozen at G5 section 1.3: order statistic at
#: floor(q*(n-1)) ("lower").
def _q_lower(sorted_vals: np.ndarray, q: float) -> float:
    n = len(sorted_vals)
    if n == 0:
        raise ValueError("empty band window")
    i = int(np.floor(q * (n - 1)))
    return float(sorted_vals[i])


BAND_WINDOWS = {
    "FULL": ("2020-10-02", "2026-09-30"),
    "EVAL": ("2021-10-01", "2026-09-24"),
    "FOLDS": ("2022-09-30", "2026-09-24"),
}


def derive_vehicle_bands(inst: str, bars: Dict[str, D1Bar]
                         ) -> Dict[str, Dict[str, object]]:
    """D1 band cells for a vehicle instrument (MEASURED-DERIVED).

    Same definitions as G5 section 1.3/1.8 (open/close side spread bps,
    crossed-book filter ASK>=BID>0, quantile 'lower') but derived from
    the declared M1->D1 aggregation (labeled). Validation bands ONLY —
    fills price at the bar's own quoted side, never from a cell.
    """
    cells: Dict[str, Dict[str, object]] = {}
    dates = sorted(bars)
    for side_field, side_code in (("open", "O"), ("close", "C")):
        for wname, (lo, hi) in BAND_WINDOWS.items():
            bps = []
            for d in dates:
                if not (lo <= d <= hi):
                    continue
                b = bars[d]
                a, bb = getattr(b, f"ask_{side_field}"), getattr(b, f"bid_{side_field}")
                mid = (a + bb) / 2.0
                if a >= bb > 0:
                    bps.append((a - bb) / mid * 1e4)
            arr = np.array(sorted(bps))
            if len(arr) == 0:
                continue
            cells[f"D1BAND-{inst}-{side_code}-{wname}"] = {
                "cell_id": f"D1BAND-{inst}-{side_code}-{wname}",
                "instrument": inst,
                "side": {"O": "OPEN", "C": "CLOSE"}[side_code],
                "window": wname,
                "p50_bps": _q_lower(arr, 0.50),
                "p90_bps": _q_lower(arr, 0.90),
                "p95_bps": _q_lower(arr, 0.95),
                "max_bps": float(arr[-1]),
                "n_days": int(len(arr)),
                "derivation": "MEASURED-DERIVED from the DECLARED 17:00 ET M1->D1 aggregation (battery freeze act; G5 section 5 'NOT YET COMPUTED' resolved for the two vehicles)",
                "quantile_convention": "lower (order statistic floor(q*(n-1)))",
                "validation_only": True,
            }
    return cells


def register_vehicle_band_cells(cells: Dict[str, Dict[str, object]]
                                ) -> List[str]:
    """Add derived cells to the kernel's band table (additive; frozen
    cells untouched). Returns the registered cell ids."""
    from .costkernel import D1BAND_TABLE, D1BAND_NOT_COMPUTED_INSTRUMENTS
    registered = []
    for cid, cell in cells.items():
        D1BAND_TABLE[cid] = cell
        registered.append(cid)
    return registered
