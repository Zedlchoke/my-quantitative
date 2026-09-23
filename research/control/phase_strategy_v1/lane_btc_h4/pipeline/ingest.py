"""PSV1 lane_btc_h4 — Binance Vision ingestion + sha256 manifest (plan §9.1).

Keyless HTTP GET of monthly 1h zips (2020-01 .. last complete month) + daily 1h
zips for the partial tail month + monthly native 4h zips (shadow cross-check
only). Raw zip bytes live in data_staging/ (gitignored); digests live in
data/manifest.json. Deterministic re-retrieval is verified on a fixed sample.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from . import config

KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "count",
    "taker_buy_volume", "taker_buy_quote_volume", "ignore",
]


def month_range(first: str, last: str) -> list[str]:
    start = datetime.strptime(first, "%Y-%m")
    end = datetime.strptime(last, "%Y-%m")
    out = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def day_range(first: str, last: str) -> list[str]:
    start = datetime.strptime(first, "%Y-%m-%d").date()
    end = datetime.strptime(last, "%Y-%m-%d").date()
    out = []
    d = start
    while d <= end:
        out.append(d.isoformat())
        d = d.fromordinal(d.toordinal() + 1)
    return out


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def url_1h_monthly(ym: str) -> str:
    return f"{config.BASE_URL}/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{ym}.zip"


def url_1h_daily(d: str) -> str:
    return f"{config.BASE_URL}/daily/klines/BTCUSDT/1h/BTCUSDT-1h-{d}.zip"


def url_4h_monthly(ym: str) -> str:
    return f"{config.BASE_URL}/monthly/klines/BTCUSDT/4h/BTCUSDT-4h-{ym}.zip"


def fetch(url: str, timeout: int = 60) -> tuple[bytes | None, int]:
    """GET bytes; returns (body, http_status). body None when not 200."""
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "psv1-lane-btc-h4/1.0"})
    if resp.status_code != 200:
        return None, resp.status_code
    return resp.content, 200


def parse_klines_zip(body: bytes) -> pd.DataFrame:
    """Unzip -> DataFrame with ms-epoch int timestamps.

    Timestamp unit is DETECTED fail-closed (Binance migrated futures klines to
    microseconds in 2025): values < 1e14 are ms, >= 1e14 are us. Anything else
    raises.
    """
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            df = pd.read_csv(fh, header=None, names=KLINE_COLUMNS)
    # Some files ship a header row; re-read with header=0 if first open_time is not numeric.
    first = df.iloc[0]["open_time"]
    if isinstance(first, str) and not first.strip().lstrip("-").isdigit():
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            with zf.open(zf.namelist()[0]) as fh:
                df = pd.read_csv(fh, header=0, names=KLINE_COLUMNS)
    return df


def normalize_klines(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce dtypes, detect/normalize timestamp unit, sort, drop dup timestamps fail-closed."""
    out = df.copy()
    for col in ["open", "high", "low", "close", "volume", "quote_volume",
                "taker_buy_volume", "taker_buy_quote_volume"]:
        out[col] = pd.to_numeric(out[col], errors="raise").astype("float64")
    out["count"] = pd.to_numeric(out["count"], errors="raise").astype("int64")

    ot = pd.to_numeric(out["open_time"], errors="raise")
    ct = pd.to_numeric(out["close_time"], errors="raise")
    unit_ot = _detect_unit(ot)
    unit_ct = _detect_unit(ct)
    if unit_ot != unit_ct:
        raise ValueError(f"open/close time unit mismatch: {unit_ot} vs {unit_ct}")
    scale = {"ms": 1, "us": 1000}[unit_ot]
    out["open_time_ms"] = (ot * scale).astype("int64")
    out["close_time_ms"] = (ct * scale).astype("int64")
    out = out.sort_values("open_time_ms", kind="stable").reset_index(drop=True)
    if out["open_time_ms"].duplicated().any():
        raise ValueError("duplicate open_time present — fail-closed per plan §9.1")
    return out


def _detect_unit(s: pd.Series) -> str:
    mx = int(s.max())
    if mx < 10**12:
        raise ValueError(f"timestamp unit looks like seconds (max={mx}) — unexpected for Vision klines")
    if mx < 10**14:
        return "ms"
    if mx < 10**17:
        return "us"
    raise ValueError(f"timestamp unit undecidable (max={mx})")


def ingest_all(staging: Path, last_complete_month: str, tail_last_day: str) -> dict:
    """Download all files, build manifest entries with sha256 + byte length.

    Returns the manifest dict. Files already present in staging are kept
    (resumable); digest always recomputed from staged bytes.
    """
    entries: list[dict] = []

    def _get(url: str, local: Path) -> tuple[bytes | None, int]:
        if local.exists():
            return local.read_bytes(), 200
        body, status = fetch(url)
        if body is not None:
            local.write_bytes(body)
        return body, status

    months = month_range(config.FIRST_MONTH, last_complete_month)
    skipped_days: list[str] = []

    for kind, urlfn, namefn, sub in [
        ("1h_monthly", url_1h_monthly, lambda ym: f"BTCUSDT-1h-{ym}.zip", "1h_monthly"),
        ("4h_monthly", url_4h_monthly, lambda ym: f"BTCUSDT-4h-{ym}.zip", "4h_monthly"),
    ]:
        for ym in months:
            url = urlfn(ym)
            local = staging / sub / namefn(ym)
            local.parent.mkdir(parents=True, exist_ok=True)
            body, status = _get(url, local)
            if body is None:
                raise RuntimeError(f"HTTP {status} for required file {url}")
            entries.append({
                "kind": kind, "period": ym, "url": url,
                "bytes": len(body), "sha256": sha256_bytes(body),
                "local": str(local.relative_to(staging)),
                "http_status": status,
            })

    # Tail-stitch: daily 1h zips for the partial month. Stop at first 404
    # (day not yet published) or at tail_last_day, whichever first.
    days = day_range(f"{last_complete_month + '-01'}", tail_last_day)
    # days actually belong to the month AFTER last_complete_month
    next_month = _next_month(last_complete_month)
    days = [d for d in days if d.startswith(next_month)]
    for d in days:
        url = url_1h_daily(d)
        local = staging / "1h_daily" / f"BTCUSDT-1h-{d}.zip"
        local.parent.mkdir(parents=True, exist_ok=True)
        body, status = _get(url, local)
        if body is None:
            if status == 404:
                skipped_days.append({"day": d, "reason": f"HTTP 404 (not published)", "url": url})
                continue
            raise RuntimeError(f"HTTP {status} for required tail file {url}")
        entries.append({
            "kind": "1h_daily", "period": d, "url": url,
            "bytes": len(body), "sha256": sha256_bytes(body),
            "local": str(local.relative_to(staging)),
            "http_status": status,
        })

    return {
        "schema": "psv1_lane_btc_h4_data_manifest@1",
        "cell": config.CELL,
        "source": "Binance Vision keyless USDT-M futures klines (data.binance.vision)",
        "retrieved_at": config.DATA_RETRIEVED_AT,
        "pit_disclosure": config.PIT_CONVENTION,
        "first_month": config.FIRST_MONTH,
        "last_complete_month": last_complete_month,
        "skipped_tail_days": skipped_days,
        "files": entries,
    }


def _next_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    m += 1
    if m == 13:
        y, m = y + 1, 1
    return f"{y:04d}-{m:02d}"


def verify_reretrieval(manifest: dict, staging: Path, sample: int = config.RERETRIEVAL_SAMPLE) -> list[dict]:
    """Re-download a deterministic sample (every k-th monthly file) and compare digests."""
    monthly = [e for e in manifest["files"] if e["kind"] == "1h_monthly"]
    step = max(1, len(monthly) // sample)
    picks = monthly[::step][:sample]
    results = []
    for e in picks:
        body, status = fetch(e["url"])
        ok = body is not None and sha256_bytes(body) == e["sha256"]
        results.append({
            "url": e["url"], "http_status": status,
            "digest_match": bool(ok),
            "expected_sha256": e["sha256"],
            "observed_sha256": sha256_bytes(body) if body is not None else None,
        })
    return results


def load_1h_from_manifest(manifest: dict, staging: Path) -> pd.DataFrame:
    """Concatenate 1h monthly + daily staged files into one normalized frame."""
    frames = []
    for e in manifest["files"]:
        if not e["kind"].startswith("1h"):
            continue
        local = staging / e["local"]
        staged = local.read_bytes()
        if sha256_bytes(staged) != e["sha256"]:
            raise ValueError(f"digest mismatch on staged file {e['local']} — fail-closed")
        frames.append(normalize_klines(parse_klines_zip(staged)))
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("open_time_ms", kind="stable").reset_index(drop=True)
    if df["open_time_ms"].duplicated().any():
        # daily tail overlaps nothing (monthly ends at last complete month), but fail-closed anyway
        raise ValueError("duplicate open_time after concat — fail-closed")
    return df


def load_4h_from_manifest(manifest: dict, staging: Path) -> pd.DataFrame:
    frames = []
    for e in manifest["files"]:
        if e["kind"] != "4h_monthly":
            continue
        local = staging / e["local"]
        staged = local.read_bytes()
        if sha256_bytes(staged) != e["sha256"]:
            raise ValueError(f"digest mismatch on staged file {e['local']} — fail-closed")
        frames.append(normalize_klines(parse_klines_zip(staged)))
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("open_time_ms", kind="stable").reset_index(drop=True)
    if df["open_time_ms"].duplicated().any():
        raise ValueError("duplicate open_time after concat — fail-closed")
    return df


def utc_ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def json_dumps(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=False, default=str)
