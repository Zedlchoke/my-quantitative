"""BTC-COMBO6 data plane: Binance Vision 5m zips, digest/manifest court,
funding events, complete-bucket aggregation, gap census.

Fail-closed law: every kl_*.zip sha256 (and the funding parquet sha256) is
verified against the pinned manifest research/control/BTC-COMBO6-SCORED-V1/
staging/data_manifest.json before use (PSV1: archives get rewritten upstream;
re-verify on reuse). The manifest is created on first run and committed; a
mismatch raises DataDigestMismatch and nothing downstream runs.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from . import spec

MANIFEST_SCHEMA = "btcombo6/data_manifest@1"

_BIN_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
             "quote_volume", "count", "taker_buy_base", "taker_buy_quote", "ignore"]

_TS_NS = "datetime64[ns, UTC]"


class DataDigestMismatch(RuntimeError):
    """Raised when on-disk bytes disagree with the pinned manifest."""


def canonical_json(obj) -> str:
    """Deterministic JSON used for digests and artifacts."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def worktree_path(root: str | Path, rel: str) -> Path:
    return Path(root) / rel


def kline_zip_paths(root: str | Path) -> list[Path]:
    """All kl_*.zip in the frozen kline dir, sorted by name. mk_/ix_ excluded."""
    d = worktree_path(root, spec.KLINE_DIR_REL)
    return sorted(d.glob("kl_*.zip"))


def funding_parquet_path(root: str | Path) -> Path:
    return worktree_path(root, spec.FUNDING_PARQUET_REL)


# ---------------------------------------------------------------------------
# Zip parsing (dt100 load_binance_zipdir pattern: per-file header detection)
# ---------------------------------------------------------------------------

def _load_zip_frame(zp: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zp) as z:
        name = z.namelist()[0]
        with z.open(name) as fh:
            raw = fh.read()
    df = pd.read_csv(io.BytesIO(raw), header=None, low_memory=False,
                     usecols=range(len(_BIN_COLS)))
    if df.empty:
        return pd.DataFrame(columns=["open_time", "o", "h", "l", "c", "v"])
    first = str(df.iloc[0, 0])
    if not first.isdigit():                      # newer zips carry a header row
        df = pd.read_csv(io.BytesIO(raw), header=0, low_memory=False,
                         usecols=range(len(_BIN_COLS)))
    df = df.iloc[:, :6]
    df.columns = ["open_time", "o", "h", "l", "c", "v"]
    return df


def _build_panel(zips: Iterable[Path]) -> tuple[pd.DataFrame, int]:
    frames = [_load_zip_frame(zp) for zp in zips]
    all_df = pd.concat(frames, ignore_index=True, sort=False)
    all_df["open_time"] = pd.to_numeric(all_df["open_time"]).astype("int64")
    n_dup = int(all_df["open_time"].duplicated().sum())
    all_df = (all_df.sort_values("open_time", kind="mergesort")
              .drop_duplicates("open_time", keep="first")
              .reset_index(drop=True))
    m5 = pd.DataFrame({
        "ts": pd.to_datetime(all_df["open_time"], unit="ms", utc=True)
        .astype(_TS_NS),
        "o": all_df["o"].astype(float),
        "h": all_df["h"].astype(float),
        "l": all_df["l"].astype(float),
        "c": all_df["c"].astype(float),
        "v": all_df["v"].astype(float),
    })
    # Fail closed on non-5m-aligned stamps (complete-bucket law assumes grid).
    ts_ns = m5["ts"].to_numpy(dtype="datetime64[ns]").astype("int64")
    if len(ts_ns) and np.any(ts_ns % 300_000_000_000 != 0):
        raise DataDigestMismatch("non-5m-aligned open_time in kline corpus")
    return m5, n_dup


# ---------------------------------------------------------------------------
# Manifest / digest court
# ---------------------------------------------------------------------------

def _manifest_path(root) -> Path:
    return worktree_path(root, spec.MANIFEST_REL)


def _cache_path(root) -> Path:
    return worktree_path(root, spec.M5_CACHE_REL)


def corpus_digest(m5: pd.DataFrame, kline_sha256s: list[tuple[str, str]],
                  funding_sha256: str) -> str:
    """sha256 over per-zip sha256s (sorted), panel rows, first/last ts,
    funding file sha256."""
    payload = {
        "schema": "btcombo6/corpus_digest@1",
        "klines": [[n, s] for n, s in sorted(kline_sha256s)],
        "panel_rows": int(len(m5)),
        "panel_first_ts": m5["ts"].iloc[0].isoformat(),
        "panel_last_ts": m5["ts"].iloc[-1].isoformat(),
        "funding_parquet_sha256": funding_sha256,
    }
    return sha256_hex(canonical_json(payload))


def _verify_zip_digests(root, zips: list[Path], manifest: dict) -> None:
    pinned = manifest.get("klines", {})
    problems = []
    for zp in zips:
        actual = file_sha256(zp)
        if zp.name not in pinned:
            problems.append(f"{zp.name}: not pinned in manifest")
        elif pinned[zp.name] != actual:
            problems.append(f"{zp.name}: pinned {pinned[zp.name]} != actual {actual}")
    extra = set(pinned) - {zp.name for zp in zips}
    for name in sorted(extra):
        problems.append(f"{name}: pinned but absent on disk")
    if problems:
        raise DataDigestMismatch(
            "kline zip digest mismatch (fail closed): " + "; ".join(problems))


def _panel_stats(m5: pd.DataFrame) -> dict:
    return {
        "rows": int(len(m5)),
        "first_ts": m5["ts"].iloc[0].isoformat(),
        "last_ts": m5["ts"].iloc[-1].isoformat(),
    }


def load_m5(root: str | Path, verify: bool = True) -> pd.DataFrame:
    """Load the 5m master panel [ts,o,h,l,c,v].

    - verifies every kl zip sha256 against the pinned manifest (creates the
      manifest on first run);
    - uses staging/m5_panel.parquet as a build cache; rebuilds from zips when
      the cache is absent.
    """
    root = Path(root)
    zips = kline_zip_paths(root)
    if not zips:
        raise FileNotFoundError(f"no kl_*.zip under {spec.KLINE_DIR_REL}")
    sha_map = {zp.name: file_sha256(zp) for zp in zips}

    manifest_file = _manifest_path(root)
    cache_file = _cache_path(root)
    manifest = None
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())
        if manifest.get("schema") != MANIFEST_SCHEMA:
            raise DataDigestMismatch(
                f"manifest schema {manifest.get('schema')!r} != {MANIFEST_SCHEMA!r}")
        if verify:
            _verify_zip_digests(root, zips, manifest)

    if manifest is not None and cache_file.exists():
        m5 = pd.read_parquet(cache_file)
        m5["ts"] = m5["ts"].astype(_TS_NS)
        stats = _panel_stats(m5)
        if stats != manifest.get("panel"):
            raise DataDigestMismatch(
                f"cached panel stats {stats} != pinned {manifest.get('panel')}")
        return m5

    m5, n_dup = _build_panel(zips)
    if manifest is None:
        # First run: pin the manifest (klines + funding sha + panel stats).
        fsha = file_sha256(funding_parquet_path(root))
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "created_utc": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
            "kline_zip_count": len(zips),
            "klines": sha_map,
            "funding_parquet_sha256": fsha,
            "panel": _panel_stats(m5),
            "duplicate_open_time_dropped": n_dup,
            "corpus_digest": corpus_digest(
                m5, sorted(sha_map.items()), fsha),
        }
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        manifest_file.write_text(canonical_json(manifest) + "\n")
    # (Re)build the cache with a build stamp recorded in the manifest dir.
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    m5.to_parquet(cache_file)
    stamp = cache_file.with_suffix(".build_stamp.json")
    stamp.write_text(canonical_json({
        "schema": "btcombo6/m5_cache_stamp@1",
        "built_utc": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "panel": _panel_stats(m5),
        "source_manifest": manifest.get("corpus_digest"),
    }) + "\n")
    return m5


def load_funding(root: str | Path, verify: bool = True) -> pd.DataFrame:
    """Funding events -> [ts, rate].

    rate = last_funding_rate decimal per 8h, signed. Event ts floored to the
    8h slot before joining (measured jitter <=47ms off grid; never rely on
    exact-ms equality — DATA-VERIFY finding, dispatch amendment 2026-09-29).
    """
    root = Path(root)
    path = funding_parquet_path(root)
    fsha = file_sha256(path)
    manifest_file = _manifest_path(root)
    if verify and manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())
        pinned = manifest.get("funding_parquet_sha256")
        if pinned is not None and pinned != fsha:
            raise DataDigestMismatch(
                f"funding parquet sha256 mismatch: pinned {pinned} != actual {fsha}")
    f = pd.read_parquet(path)
    out = pd.DataFrame({
        "ts": f["ts"].astype(_TS_NS).dt.floor("8h"),
        "rate": f["last_funding_rate"].astype(float),
    }).sort_values("ts", kind="mergesort").reset_index(drop=True)
    if out["ts"].duplicated().any():
        dup = out.loc[out["ts"].duplicated(), "ts"].iloc[0]
        raise DataDigestMismatch(f"duplicate funding slot after 8h floor: {dup}")
    return out


def load_corpus(root: str | Path) -> dict:
    """Full verified corpus for the runners: panel + funding + digests."""
    root = Path(root)
    m5 = load_m5(root)
    funding = load_funding(root)
    manifest = json.loads(_manifest_path(root).read_text())
    kline_sha = sorted(manifest["klines"].items())
    digest = corpus_digest(m5, kline_sha, manifest["funding_parquet_sha256"])
    if digest != manifest.get("corpus_digest"):
        raise DataDigestMismatch(
            f"corpus digest drift: computed {digest} != pinned "
            f"{manifest.get('corpus_digest')}")
    return {
        "m5": m5,
        "funding": funding,
        "corpus_digest": digest,
        "manifest": manifest,
        "gap_census": gap_census(
            m5, duplicates_dropped=manifest.get("duplicate_open_time_dropped", 0)),
    }


# ---------------------------------------------------------------------------
# Aggregation + gaps
# ---------------------------------------------------------------------------

def aggregate(m5: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Aggregate 5m -> 15m/1h/4h OHLCV with the COMPLETE-BUCKET law.

    A bucket is emitted iff ALL constituent 5m bars are present on the UTC
    grid (15m=3, 1h=12, 4h=48). Incomplete buckets are ABSENT (deferred
    decisions). Output ts = bucket open time.
    """
    expected = spec.CLOCK_EXPECTED_5M[rule]
    buckets = m5["ts"].dt.floor(rule).rename("bucket")
    g = m5.groupby(buckets, sort=True)
    out = g.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"),
                c=("c", "last"), v=("v", "sum"), n=("ts", "size"))
    out = out[out["n"] == expected].drop(columns="n").reset_index()
    return out[["bucket", "o", "h", "l", "c", "v"]].rename(columns={"bucket": "ts"})


def gap_census(m5: pd.DataFrame, duplicates_dropped: int = 0) -> dict:
    """5m grid census: expected slots, missing count/ratio, max missing run,
    duplicates dropped at load."""
    if not len(m5):
        return {"expected_5m_slots": 0, "missing_count": 0, "missing_ratio": 0.0,
                "max_missing_run": 0, "duplicate_open_time_dropped": int(duplicates_dropped)}
    step = 300_000_000_000
    ts_ns = m5["ts"].to_numpy(dtype="datetime64[ns]").astype("int64")
    first, last = int(ts_ns[0]), int(ts_ns[-1])
    expected = (last - first) // step + 1
    missing_count = int(expected - len(np.unique(ts_ns)))
    if missing_count == 0:
        max_run = 0
    else:
        # slots present -> first difference of consecutive present slots
        uniq = np.unique(ts_ns)
        gaps_slots = (uniq[1:] - uniq[:-1]) // step - 1  # missing between pairs
        max_run = int(gaps_slots.max()) if len(gaps_slots) else 0
        # missing run at the edges is impossible: grid spans first..last present
    return {
        "expected_5m_slots": int(expected),
        "missing_count": missing_count,
        "missing_ratio": (float(missing_count) / expected) if expected else 0.0,
        "max_missing_run": max_run,
        "duplicate_open_time_dropped": int(duplicates_dropped),
    }
