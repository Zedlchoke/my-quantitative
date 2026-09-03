"""V12 P1 A3 -- PIT data contract: frozen windows, required symbol set,
loader-selected inventory of local data, and deterministic equal-twin
staging-manifest generation.

Scope and discipline (PLAN_crypto.md section 7 / A3):

* This module NEVER fetches network data and NEVER writes raw data.
* Raw data live OUTSIDE the repo (gitignored workspace roots); only hashes
  and coverage metadata derived from them may be committed.
* The required symbol set and the coverage requirements are DECLARED here,
  before any coverage number is computed, so the ILLIQ replication window
  verdict (freeze vs ``V12_ILLIQ_REPLICATION_BLOCKED_DATA``) is checkable.
* All inventory values are LOADER-SELECTED: bars are read from the same
  Nautilus parquet layout the V11 adapter consumes (``ts_event`` = bar close
  boundary, nanoseconds); a bar is COMPLETED at instant ``t`` iff
  ``t >= ts_event``.

PIT rules enforced by the inventory:

* completed bars only -- a partial tail (a bar whose close boundary extends
  beyond the frozen window end) is not part of the window;
* no synthesized tails -- missing 15-minute slots inside a required window
  are gaps, and gaps are failures, never back-filled;
* funding settlements are native exchange records (``fundingTime``), applied
  to a holding span only when the settlement timestamp lies within
  ``[ts_opened, ts_closed]``.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Iterable, Mapping, Optional, Sequence

import pyarrow.parquet as pq

# --------------------------------------------------------------------------
# Frozen windows (authoritative; all UTC).
# --------------------------------------------------------------------------

#: V11 scored window -- MUST NOT be overlapped by the ILLIQ replication
#: window (PLAN section 7, A3 deliverable 2).
V11_SCORED_WINDOW_START_ISO = "2025-08-22T00:00:00Z"
V11_SCORED_WINDOW_END_ISO = "2026-08-21T00:00:00Z"

#: Preregistered S0R replication window -- preferred, freeze only if every
#: required symbol / field / warmup need is met from local data.
S0R_WINDOW_START_ISO = "2024-08-22T00:00:00Z"
S0R_WINDOW_END_ISO = "2025-08-21T00:00:00Z"

#: OILEV-V2 / blind family authorized snapshot (V11 S0 snapshot reuse).
S0_SNAPSHOT_WINDOW_START_ISO = V11_SCORED_WINDOW_START_ISO
S0_SNAPSHOT_WINDOW_END_ISO = V11_SCORED_WINDOW_END_ISO

_NS_PER_S = 1_000_000_000
NS_PER_DAY_NS = 86_400 * _NS_PER_S

#: Required bar cadence: 15-minute bins (frozen ILLIQ identity).
BAR_INTERVAL_NS = 900 * _NS_PER_S

#: Native Binance USDT-M funding cadence baseline; some symbols settle every
#: 4 hours, so funding inventory derives the per-symbol cadence from data.
FUNDING_INTERVAL_NS = 8 * 3600 * _NS_PER_S

# --------------------------------------------------------------------------
# Required symbol set -- DECLARED BEFORE any coverage check.
#
# Derivation:
#   * ILLIQ family universe: "20 staged binance_bar symbols; PIT eligibility
#     by listing + DV filter" (research/control/v11_run/selection_freeze_specs/
#     A8-V11-ILLIQ-AMIHUD.json, V11 selection freeze), with BTCUSDT as the
#     benchmark leg (benchmark_context_symbols / BENCHMARK_SYMBOL_EXCLUDED).
#   * OILEV-V2 / blind S0 snapshot universe: the 20 consolidated OI symbols
#     (research/control/v11_run/oi_staging_manifest.json).
# Both universes are the same 20 names; the required set below is their union
# and must equal each of them.
# --------------------------------------------------------------------------

REQUIRED_SYMBOLS: tuple[str, ...] = (
    "1000PEPEUSDT",
    "AAVEUSDT",
    "ACEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "BCHUSDT",
    "BNBUSDT",
    "BOMEUSDT",
    "BTCUSDT",
    "DOGEUSDT",
    "ENAUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "NEARUSDT",
    "ONGUSDT",
    "SOLUSDT",
    "SUIUSDT",
    "WLDUSDT",
    "XRPUSDT",
    "ZECUSDT",
)

#: Benchmark leg required by the frozen ILLIQ identity (BTC-beta-neutral).
ILLIQ_BENCHMARK_SYMBOL = "BTCUSDT"

# --------------------------------------------------------------------------
# Declared coverage requirements for the ILLIQ S0R window (checked per
# symbol; ALL must pass for the window to freeze).
# --------------------------------------------------------------------------

DECLARED_REQUIREMENTS: dict[str, Any] = {
    "bars": {
        "interval_ns": BAR_INTERVAL_NS,
        "window_rule": (
            "every 15-minute slot in [window_start, window_end) has exactly "
            "one completed bar (close ts_event at slot end); no internal "
            "gaps; no partial tail beyond window_end counted as coverage"
        ),
        # Warmup: 28d anchor formation, 56d neighbour formation, and the
        # frozen 90d daily BTC beta hedge all need completed daily blocks
        # strictly before each Monday 00:00Z decision stamp.  The binding
        # requirement at the first stamp is the maximum (90 days).
        "warmup_days_required": {
            "anchor_28d": 28,
            "neighbour_56d": 56,
            "beta_90d": 90,
            "binding_max": 90,
        },
    },
    "funding": {
        "rule": (
            "native settlements present at the symbol's own cadence over the "
            "window; any missing cadence slot inside the window is a gap"
        ),
        "pit_rule": "settlement ts within [ts_opened, ts_closed]",
    },
    "instrument_metadata": {
        "rule": (
            "crypto_perpetual metadata present with positive price_increment "
            "(tick size), price/size precision and fee fields"
        ),
    },
    "oi": {
        "required_for": "OILEV-V2 / blind S0 snapshot only (NOT the ILLIQ identity)",
    },
}


# --------------------------------------------------------------------------
# Time helpers.
# --------------------------------------------------------------------------


def parse_iso_utc_ns(iso: str) -> int:
    """Parse ``YYYY-MM-DDTHH:MM:SS[.ffffff]Z`` to epoch nanoseconds."""
    text = str(iso).strip()
    if not text.endswith("Z"):
        raise ValueError(f"expected trailing Z (UTC): {iso!r}")
    from datetime import datetime, timezone

    body = text[:-1]
    if "." in body:
        main, frac = body.split(".", 1)
    else:
        main, frac = body, ""
    dt = datetime.strptime(main, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    frac_ns = int((frac or "0").ljust(9, "0")[:9])
    return int(dt.timestamp()) * _NS_PER_S + frac_ns


def ns_to_iso_utc(ns: int) -> str:
    """Format epoch nanoseconds as ``YYYY-MM-DDTHH:MM:SSZ`` (truncated)."""
    from datetime import datetime, timezone

    dt = datetime.fromtimestamp(int(ns) // _NS_PER_S, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def windows_overlap(
    a_start_ns: int, a_end_ns: int, b_start_ns: int, b_end_ns: int
) -> bool:
    """True when the half-open windows ``(start, end]`` share any instant.

    The V11 scored window convention is ``(start, end]`` (stamps strictly
    after start through end); overlap of such intervals is overlap of the
    half-open ``[start, end)`` projections shifted -- conservatively we test
    ``a_start < b_end and b_start < a_end`` which is overlap of open
    intervals, and additionally treat boundary touching (``a_end ==
    b_start``) as non-overlap only when both ends are exclusive.
    """
    if a_end_ns <= a_start_ns or b_end_ns <= b_start_ns:
        raise ValueError("window end must be strictly after window start")
    return bool(a_start_ns < b_end_ns and b_start_ns < a_end_ns)


# --------------------------------------------------------------------------
# Hashing and canonical JSON.
# --------------------------------------------------------------------------


def sha256_file(path: str, *, chunk_size: int = 1 << 20) -> str:
    """Streamed sha256 of a file (hex)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic JSON encoding used for manifest self-hashing."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_canonical_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


# --------------------------------------------------------------------------
# Equal-twin staging manifest generator (committed: hashes only, never raw
# data).  Pattern follows research/control/v11_run/staged_manifest_w11.json.
# --------------------------------------------------------------------------

STAGED_MANIFEST_SCHEMA = "v12_staged_manifest_v1"


def build_file_manifest(
    roots: Sequence[tuple[str, str]],
    *,
    extensions: Sequence[str] = (".parquet", ".json"),
    generated_utc: Optional[str] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Build a per-file sha256 manifest over the given labeled roots.

    ``roots`` is a sequence of ``(label, absolute_root_dir)`` pairs; every
    file under a root whose extension is in ``extensions`` is hashed and
    recorded under ``<label>/<relpath>``.  The output is deterministic:
    files are sorted, and ``manifest_sha256`` hashes only the canonical
    (sorted, compact) ``files`` section, so two machines staging the same
    bytes produce byte-identical manifests (equal-twin check).
    """
    files: dict[str, Any] = {}
    for label, root in roots:
        label = str(label)
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            raise FileNotFoundError(f"manifest root missing: {root}")
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in sorted(filenames):
                if not name.endswith(tuple(extensions)):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                key = f"{label}/{rel}"
                files[key] = {
                    "sha256": sha256_file(full),
                    "bytes": int(os.path.getsize(full)),
                }
    manifest: dict[str, Any] = {
        "schema": STAGED_MANIFEST_SCHEMA,
        "generated_utc": generated_utc,
        "files_count": len(files),
        "files": dict(sorted(files.items())),
    }
    if extra:
        manifest["extra"] = dict(extra)
    manifest["manifest_sha256"] = sha256_canonical_json(manifest["files"])
    return manifest


def emit_file_manifest(
    roots: Sequence[tuple[str, str]],
    out_path: str,
    *,
    extensions: Sequence[str] = (".parquet", ".json"),
    generated_utc: Optional[str] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Build and write a staging manifest JSON; returns the manifest dict."""
    manifest = build_file_manifest(
        roots, extensions=extensions, generated_utc=generated_utc, extra=extra
    )
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return manifest


def verify_against_manifest(
    roots: Sequence[tuple[str, str]],
    manifest: Mapping[str, Any],
    *,
    extensions: Sequence[str] = (".parquet", ".json"),
) -> list[str]:
    """Re-hash ``roots`` and return the list of mismatches vs ``manifest``.

    Empty list == byte-identical staging (equal twin).  Extra/missing files
    are reported as mismatches too.
    """
    rebuilt = build_file_manifest(roots, extensions=extensions)["files"]
    expected = manifest.get("files", {})
    problems: list[str] = []
    for key in sorted(set(expected) | set(rebuilt)):
        if key not in rebuilt:
            problems.append(f"missing_on_disk:{key}")
        elif key not in expected:
            problems.append(f"not_in_manifest:{key}")
        elif rebuilt[key]["sha256"] != expected[key]["sha256"]:
            problems.append(f"sha_mismatch:{key}")
    return problems


# --------------------------------------------------------------------------
# Inventory: bars (loader-selected values from the Nautilus parquet layout).
# --------------------------------------------------------------------------


def bar_parquet_paths(bars_root: str, symbol: str) -> list[str]:
    """All parquet files for ``<SYMBOL>-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL``."""
    sym_dir = os.path.join(
        bars_root, f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    )
    if not os.path.isdir(sym_dir):
        return []
    return sorted(
        os.path.join(sym_dir, n)
        for n in os.listdir(sym_dir)
        if n.endswith(".parquet")
    )


def load_bar_close_ns(paths: Sequence[str]) -> "list[int]":
    """Sorted, de-duplicated bar-close timestamps (ns) from ts_event columns."""
    import numpy as np

    chunks: list["Any"] = []
    for path in paths:
        col = pq.read_table(path, columns=["ts_event"]).column("ts_event")
        chunks.append(col.to_numpy())
    if not chunks:
        return []
    arr = np.concatenate(chunks).astype("int64")
    arr = np.unique(arr)
    return [int(v) for v in arr]


def snap_bar_closes_to_slots(
    close_ns: Sequence[int], interval_ns: int
) -> "tuple[list[int], dict[str, int]]":
    """Snap bar-close stamps to their wall-clock slot-end boundaries.

    Binance kline data record the close time as ``end - 1ms`` (here with a
    ~1ms sub-ns artifact), so closes sit a hair BEFORE the UTC 15-minute
    boundary they terminate.  The V11 loader compares ``ts_event <= t`` by
    inequality; for slot-grid inventory we normalize each close forward to
    the boundary it terminates: ``snapped = c + ((interval - c) mod
    interval)`` when that forward distance is small (< half a slot), which
    preserves exact-boundary stamps and repairs the ~1ms offset.  Stamps
    sitting just AFTER a boundary are left untouched but counted as
    ``post_boundary_stamps`` so a silent convention change cannot masquerade
    as clean coverage.
    """
    snapped: list[int] = []
    info = {"snapped_forward": 0, "exact_boundary": 0, "post_boundary_stamps": 0}
    for c in close_ns:
        r = int(c) % int(interval_ns)
        d = (int(interval_ns) - r) % int(interval_ns)
        if d == 0:
            snapped.append(int(c))
            info["exact_boundary"] += 1
        elif d < int(interval_ns) // 2:
            snapped.append(int(c) + d)
            info["snapped_forward"] += 1
        else:
            # stamp sits just after a boundary (unexpected convention)
            snapped.append(int(c))
            info["post_boundary_stamps"] += 1
    return snapped, info


def _slot_report(
    close_ns: Sequence[int],
    window_start_ns: int,
    window_end_ns: int,
    interval_ns: int,
) -> dict[str, Any]:
    """Coverage of ``[window_start, window_end)`` by completed-bar closes.

    A slot at ``window_start + k*interval`` (k = 1..) is covered iff a bar
    closes exactly there.  Gaps inside the window are enumerated (capped).
    """
    max_report = 50
    expected: list[int] = []
    t = window_start_ns + interval_ns
    while t <= window_end_ns:
        expected.append(t)
        t += interval_ns
    present = {
        v for v in close_ns if window_start_ns < v <= window_end_ns
    }
    missing = [v for v in expected if v not in present]
    # Internal gap runs (contiguous missing slots collapsed).
    gap_runs: list[dict[str, Any]] = []
    i = 0
    n = len(missing)
    while i < n:
        j = i
        while j + 1 < n and missing[j + 1] - missing[j] == interval_ns:
            j += 1
        gap_runs.append(
            {
                "first_missing_close_ns": int(missing[i]),
                "last_missing_close_ns": int(missing[j]),
                "missing_slots": j - i + 1,
            }
        )
        i = j + 1
    report: dict[str, Any] = {
        "expected_slots": len(expected),
        "present_slots": len(expected) - len(missing),
        "missing_slots": len(missing),
        "gap_runs": gap_runs[:max_report],
        "gap_runs_total": len(gap_runs),
    }
    in_window = sorted(v for v in close_ns if window_start_ns < v <= window_end_ns)
    report["first_completed_close_ns"] = int(in_window[0]) if in_window else None
    report["last_completed_close_ns"] = int(in_window[-1]) if in_window else None
    return report


def bar_gaps_global(
    close_ns: Sequence[int], interval_ns: int, *, max_report: int = 20
) -> dict[str, Any]:
    """Internal gap census over the whole local file range."""
    gaps: list[dict[str, Any]] = []
    misaligned = 0
    for prev, nxt in zip(close_ns, close_ns[1:]):
        diff = nxt - prev
        if diff == interval_ns:
            continue
        if diff % interval_ns != 0:
            misaligned += 1
            continue
        gaps.append(
            {
                "before_close_ns": int(prev),
                "after_close_ns": int(nxt),
                "missing_slots": diff // interval_ns - 1,
            }
        )
    return {
        "gap_count": len(gaps),
        "misaligned_steps": misaligned,
        "gaps": gaps[:max_report],
        "missing_slots_total": int(sum(g["missing_slots"] for g in gaps)),
    }


def contiguous_bar_runs(
    close_ns: Sequence[int], interval_ns: int
) -> list[dict[str, int]]:
    """Maximal runs of strictly contiguous 15-minute bar closes.

    A run breaks wherever consecutive closes differ by more than one slot
    (a gap) or by a non-multiple of the interval (misalignment).
    """
    runs: list[dict[str, int]] = []
    if not close_ns:
        return runs
    start = int(close_ns[0])
    last = start
    count = 1
    for v in close_ns[1:]:
        v = int(v)
        if v - last == interval_ns:
            count += 1
        else:
            runs.append({"start_ns": start, "end_ns": last, "slots": count})
            start = v
            count = 1
        last = v
    runs.append({"start_ns": start, "end_ns": last, "slots": count})
    return runs


def _ns_per_week() -> int:
    return 7 * NS_PER_DAY_NS


def _monday_offset_ns() -> int:
    # 1970-01-01 was a Thursday; Monday 00:00Z timestamps satisfy
    # ns % week == 4 days.
    return 4 * NS_PER_DAY_NS


def ceil_to_monday_00z_ns(t_ns: int) -> int:
    """First Monday 00:00:00Z instant strictly at-or-after ``t_ns``."""
    week = _ns_per_week()
    off = _monday_offset_ns()
    r = int(t_ns) % week
    delta = off - r
    if delta < 0:
        delta += week
    return int(t_ns) + delta


def warmup_first_served_stamp_ns(
    close_ns: Sequence[int],
    days: int,
    *,
    interval_ns: int = BAR_INTERVAL_NS,
) -> Optional[int]:
    """Earliest Monday 00:00Z decision stamp whose ``days``-day trailing
    formation window is fully covered by completed bars (no missing slots).

    Returns ``None`` when no stamp in the local history can be served.
    """
    need_ns = int(days) * NS_PER_DAY_NS
    for run in contiguous_bar_runs(close_ns, interval_ns):
        if run["slots"] * interval_ns < need_ns:
            continue
        # The earliest needed COMPLETED close inside the formation window
        # (T - days, T] is T - need + interval; it must fall at or after the
        # run start.
        earliest_origin = run["start_ns"] + need_ns - int(interval_ns)
        if earliest_origin > run["end_ns"]:
            continue
        stamp = ceil_to_monday_00z_ns(earliest_origin)
        if stamp <= run["end_ns"]:
            return stamp
    return None


def warmup_report(
    close_ns: Sequence[int],
    warmup_days: Sequence[int],
    *,
    interval_ns: int = BAR_INTERVAL_NS,
    window_start_ns: Optional[int] = None,
) -> dict[str, Any]:
    """Warmup satisfiability from local data, per horizon.

    ``window_start_ns`` (when given) splits the history into pre-window bars
    (close at or before the window start -- usable warmup for stamps at the
    window head) and total history.  A horizon is satisfiable AT THE WINDOW
    START iff ``warmup_first_served_stamp_ns <= window_start + one week``
    (the first decision stamp is the first Monday strictly after start).
    """
    if window_start_ns is None:
        first_stamp_ns: Optional[int] = None
    else:
        # Decision stamps are Mondays 00:00Z strictly after the window start.
        first_stamp_ns = ceil_to_monday_00z_ns(int(window_start_ns) + 1)
    pre_window = [
        v for v in close_ns if window_start_ns is None or v <= window_start_ns
    ]
    out: dict[str, Any] = {
        "first_decision_stamp_ns": first_stamp_ns,
        "first_decision_stamp_iso": (
            ns_to_iso_utc(first_stamp_ns) if first_stamp_ns else None
        ),
        "pre_window_bars": len(pre_window),
        "total_bars": len(close_ns),
    }
    for days in warmup_days:
        served = warmup_first_served_stamp_ns(close_ns, int(days), interval_ns=interval_ns)
        served_pre = (
            warmup_first_served_stamp_ns(pre_window, int(days), interval_ns=interval_ns)
            if pre_window
            else None
        )
        out[f"days_{int(days)}"] = {
            "required_slots": int(days) * (NS_PER_DAY_NS // interval_ns),
            "first_served_stamp_iso": ns_to_iso_utc(served) if served else None,
            "satisfiable_from_pre_window_history": bool(
                served_pre is not None
                and first_stamp_ns is not None
                and served_pre <= first_stamp_ns
            ),
            "first_served_from_pre_window_iso": (
                ns_to_iso_utc(served_pre) if served_pre else None
            ),
        }
    return out


def inventory_bars(
    bars_root: str,
    symbol: str,
    *,
    window_start_ns: int,
    window_end_ns: int,
    interval_ns: int = BAR_INTERVAL_NS,
) -> dict[str, Any]:
    """Loader-selected bar inventory for one symbol."""
    paths = bar_parquet_paths(bars_root, symbol)
    inv: dict[str, Any] = {
        "symbol": symbol,
        "parquet_files": [os.path.basename(p) for p in paths],
        "parquet_sha256": {os.path.basename(p): sha256_file(p) for p in paths},
    }
    if not paths:
        inv.update(
            {
                "present": False,
                "window": _slot_report([], window_start_ns, window_end_ns, interval_ns),
                "global_gaps": {"gap_count": 0, "missing_slots_total": 0, "gaps": []},
                "warmup": {},
                "first_bar_close_ns": None,
                "last_bar_close_ns": None,
                "rows": 0,
            }
        )
        return inv
    close_ns = load_bar_close_ns(paths)
    snapped, snap_info = snap_bar_closes_to_slots(close_ns, interval_ns)
    if len(set(snapped)) != len(snapped):
        raise ValueError(
            f"{symbol}: two bar closes snap to the same 15m slot boundary"
        )
    close_ns = sorted(set(snapped))
    inv.update(
        {
            "present": True,
            "rows": len(close_ns),
            "close_stamp_snap": snap_info,
            "first_bar_close_ns": int(close_ns[0]),
            "first_bar_close_iso": ns_to_iso_utc(close_ns[0]),
            "last_bar_close_ns": int(close_ns[-1]),
            "last_bar_close_iso": ns_to_iso_utc(close_ns[-1]),
            "window": _slot_report(
                close_ns, window_start_ns, window_end_ns, interval_ns
            ),
            "global_gaps": bar_gaps_global(close_ns, interval_ns),
            "warmup": warmup_report(
                close_ns,
                (28, 56, 90),
                interval_ns=interval_ns,
                window_start_ns=window_start_ns,
            ),
        }
    )
    return inv


# --------------------------------------------------------------------------
# Inventory: funding (native exchange settlements).
# --------------------------------------------------------------------------


def load_funding_times_ns(path: str) -> list[int]:
    """Settlement timestamps (ns) from a funding bundle JSON (sorted, unique)."""
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    rows = payload.get("rows") or []
    times: set[int] = set()
    for row in rows:
        ts = row.get("fundingTime")
        if ts is None:
            raise ValueError(f"funding row without fundingTime in {path}")
        ms = int(ts)
        times.add(ms * 1_000_000)
    return sorted(times)


def snap_funding_times_to_hour(
    times_ns: Sequence[int],
) -> "tuple[list[int], dict[str, int]]":
    """Snap settlement stamps to the UTC hour grid they live on.

    Binance ``fundingTime`` values carry a few-millisecond jitter around the
    exact 00:00/08:00/16:00Z (or 4-hourly) boundaries; PIT comparisons by
    exact equality would silently drop boundary settlements.  Each stamp is
    rounded to its nearest hour, which repairs the jitter without moving any
    genuine settlement (real spacing is hours, jitter is milliseconds).
    """
    hour_ns = 3600 * _NS_PER_S
    snapped = [int(round(int(t) / hour_ns)) * hour_ns for t in times_ns]
    out: list[int] = []
    seen: set[int] = set()
    jitter_events = 0
    for orig, s in zip(times_ns, snapped):
        if orig != s:
            jitter_events += 1
        if s not in seen:
            seen.add(s)
            out.append(s)
    return sorted(out), {"raw": len(times_ns), "snapped": len(out), "jitter_repairs": jitter_events}


def funding_cadence_clusters_ns(
    times_ns: Sequence[int],
) -> "dict[int, int]":
    """Histogram of settlement spacings rounded to the nearest hour."""
    from collections import Counter

    hour_ns = 3600 * _NS_PER_S
    diffs = [int(b) - int(a) for a, b in zip(times_ns, times_ns[1:])]
    clusters: Counter[int] = Counter()
    for d in diffs:
        if d > 0:
            clusters[max(1, int(round(d / hour_ns)))] += 1
    return {k * hour_ns: v for k, v in sorted(clusters.items())}


def inventory_funding(
    funding_bundles: Sequence[tuple[str, str]],
    symbol: str,
    *,
    window_start_ns: int,
    window_end_ns: int,
) -> dict[str, Any]:
    """Funding inventory for one symbol across candidate bundle roots.

    ``funding_bundles`` is an ordered sequence of ``(label, root)``; the first
    bundle holding the symbol is the primary source; later bundles are
    recorded for reference (PIT assembly must never mix duplicate
    settlements -- the loader de-duplicates by hour-snapped timestamp).

    Gap accounting: when the settlement cadence is homogeneous the missing
    slot count at that cadence is exact; when the symbol mixed cadences
    (e.g. 4h and 8h phases) a strict grid would produce false positives, so
    the report carries the cadence clusters and the largest internal
    settlement-to-settlement spacing instead.
    """
    inv: dict[str, Any] = {"symbol": symbol, "bundles": {}}
    primary_times: list[int] = []
    primary_label: Optional[str] = None
    for label, root in funding_bundles:
        path = os.path.join(root, symbol, "funding.json")
        entry: dict[str, Any] = {"path_exists": os.path.exists(path)}
        if os.path.exists(path):
            entry["sha256"] = sha256_file(path)
            times, snap_info = snap_funding_times_to_hour(load_funding_times_ns(path))
            entry["settlements"] = len(times)
            entry["snap"] = snap_info
            if times:
                entry["first_iso"] = ns_to_iso_utc(times[0])
                entry["last_iso"] = ns_to_iso_utc(times[-1])
            if primary_label is None and times:
                primary_times, primary_label = times, label
        inv["bundles"][label] = entry
    inv["primary_bundle"] = primary_label
    inv["present"] = primary_label is not None
    times = primary_times
    if not times:
        inv.update(
            {
                "present": False,
                "window": {
                    "settlements_in_window": 0,
                    "missing_slots_at_cadence": None,
                    "gap_runs_total": None,
                },
            }
        )
        return inv
    clusters = funding_cadence_clusters_ns(times)
    inv["cadence_clusters_ns"] = {
        str(k): v for k, v in clusters.items()
    }
    homogeneous = len(clusters) == 1
    finest = min(clusters) if clusters else None
    cadence = next(iter(clusters)) if homogeneous else finest
    present = sorted(t for t in times if window_start_ns < t <= window_end_ns)
    report: dict[str, Any] = {}
    if present:
        head_gap_ns = present[0] - window_start_ns
        tail_gap_ns = window_end_ns - present[-1]
        # A coverage hole is any settlement spacing strictly larger than the
        # symbol's finest observed cadence.  For a homogeneous cadence this
        # is exactly the missing-slot count; for a cadence-mixing symbol the
        # spacings above the finest cadence are listed as suspect so the
        # consumer can separate genuine phase changes from lost settlements.
        holes: list[dict[str, Any]] = []
        if finest:
            for a, b in zip(present, present[1:]):
                if b - a > finest:
                    holes.append(
                        {
                            "before_ns": int(a),
                            "before_iso": ns_to_iso_utc(a),
                            "after_ns": int(b),
                            "after_iso": ns_to_iso_utc(b),
                            "hours": round((b - a) / 3.6e12, 3),
                        }
                    )
        missing_slots: Optional[int] = None
        if homogeneous and cadence:
            missing_slots = len(holes) if holes else 0
        report = {
            "first_settlement_iso": ns_to_iso_utc(present[0]),
            "last_settlement_iso": ns_to_iso_utc(present[-1]),
            "settlements_in_window": len(present),
            "head_gap_ns": head_gap_ns,
            "head_gap_hours": round(head_gap_ns / 3.6e12, 3),
            "tail_gap_ns": tail_gap_ns,
            "tail_gap_hours": round(tail_gap_ns / 3.6e12, 3),
            "max_internal_gap_hours": (
                round(max((b - a) for a, b in zip(present, present[1:])) / 3.6e12, 3)
                if len(present) > 1
                else 0.0
            ),
            "cadence_homogeneous": homogeneous,
            "cadence_ns": cadence,
            "finest_cadence_ns": finest,
            "missing_slots_at_cadence": missing_slots,
            "coverage_hole_count": len(holes),
            "coverage_holes": holes[:20],
        }
    else:
        report = {
            "first_settlement_iso": None,
            "last_settlement_iso": None,
            "settlements_in_window": 0,
            "cadence_homogeneous": homogeneous,
            "cadence_ns": cadence,
            "missing_slots_at_cadence": None,
            "gap_runs_total": None,
        }
    inv["window"] = report
    return inv


# --------------------------------------------------------------------------
# Inventory: OI daily coverage (vs the V11 staging report) and instrument
# metadata.
# --------------------------------------------------------------------------


def inventory_oi_symbol(
    parquet_path: str,
    *,
    expected_first_day: str,
    expected_last_day: str,
) -> dict[str, Any]:
    """Loader-selected daily OI coverage for one consolidated parquet."""
    import pandas as pd

    table = pq.read_table(parquet_path, columns=["create_time"])
    days = table.column("create_time").to_pylist()
    # Each row is a UTC date string at the day's last 5m observation; the
    # consolidated bundle stores one row per present day.
    date_keys = sorted({str(d)[:10] for d in days})
    gaps: list[str] = []
    if date_keys:
        import datetime as _dt

        cur = _dt.date.fromisoformat(date_keys[0])
        end = _dt.date.fromisoformat(date_keys[-1])
        key_set = set(date_keys)
        while cur <= end:
            k = cur.isoformat()
            if k not in key_set:
                gaps.append(k)
            cur += _dt.timedelta(days=1)
    return {
        "rows": len(days),
        "days_present": len(date_keys),
        "first_day": date_keys[0] if date_keys else None,
        "last_day": date_keys[-1] if date_keys else None,
        "expected_first_day": expected_first_day,
        "expected_last_day": expected_last_day,
        "internal_gap_days": len(gaps),
        "gap_days": gaps[:20],
        "sha256": sha256_file(parquet_path),
    }


def read_instrument_metadata(perp_root: str, symbol: str) -> dict[str, Any]:
    """Instrument metadata (tick size, precision, fees) from crypto_perpetual."""
    sym_dir = os.path.join(perp_root, f"{symbol}-PERP.BINANCE")
    if not os.path.isdir(sym_dir):
        return {"present": False}
    paths = sorted(
        os.path.join(sym_dir, n) for n in os.listdir(sym_dir) if n.endswith(".parquet")
    )
    if not paths:
        return {"present": False}
    path = paths[0]
    row = pq.read_table(path).to_pandas().iloc[0]

    def _s(v: Any) -> Optional[str]:
        try:
            return None if v is None else str(v)
        except Exception:
            return None

    try:
        tick = float(row["price_increment"])
    except Exception:
        tick = float("nan")
    return {
        "present": True,
        "instrument_id": _s(row["id"]),
        "price_increment_tick_size": tick,
        "price_precision": int(row["price_precision"]),
        "size_precision": int(row["size_precision"]),
        "size_increment": _s(row["size_increment"]),
        "maker_fee": _s(row["maker_fee"]),
        "taker_fee": _s(row["taker_fee"]),
        "is_inverse": bool(row["is_inverse"]),
        "metadata_parquet_sha256": sha256_file(path),
    }


# --------------------------------------------------------------------------
# Default local data roots (workspace ROOT -- gitignored; NEVER copied into
# the repo).
# --------------------------------------------------------------------------

WORKSPACE_ROOT = "/Users/hoangminhlong/my-quantitative"
CATALOG_DATA_ROOT = os.path.join(WORKSPACE_ROOT, "catalog_live_crypto", "data")
BARS_ROOT = os.path.join(CATALOG_DATA_ROOT, "binance_bar")
PERP_ROOT = os.path.join(CATALOG_DATA_ROOT, "crypto_perpetual")
FUNDING_BUNDLES: tuple[tuple[str, str], ...] = (
    ("scan_2026", os.path.join(WORKSPACE_ROOT, "funding_data", "scan_2026")),
    (
        "20240820_20260821",
        os.path.join(WORKSPACE_ROOT, "funding_data", "20240820_20260821"),
    ),
)
OI_CONSOLIDATED_ROOT = os.path.join(WORKSPACE_ROOT, "oi_data", "consolidated")
OI_STAGING_REPORT_PATH = os.path.join(WORKSPACE_ROOT, "oi_data", "staging_report.json")


def iter_required_symbols() -> Iterable[str]:
    return tuple(REQUIRED_SYMBOLS)
