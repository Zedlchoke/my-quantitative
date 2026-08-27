"""V10P-R G2 blockers F2/G-H06 (full-pipeline cache proof) + G17 (one resource cap).

F2 contract
-----------
The ONLY admissible cache proof measures RAW READS on a FULL representative
pipeline against the REAL catalog -- never a synthetic/unit-test workload:

* workload = ``research.panel.build_daily_closes`` (the production loader used
  by ``load_bars_15m``/``_read_bars``) across EVERY staged catalog symbol and
  the frozen V10 window, executed ``workload.passes`` times over the SAME
  inputs, followed by deterministic cross-sectional pct-ranks per UTC day;
* instrumentation wraps ``pyarrow.parquet.read_table`` AS SEEN FROM
  ``research.panel`` (single primitive behind ``research.panel._read_bars``),
  counting every invocation in BOTH modes; nothing inside ``research.panel``
  itself is modified -- the wrapper is installed at runtime into the module
  namespace only;
* cached runs go through :class:`research.cache_v10.ProcessLocalCache` keyed by
  :func:`research.cache_v10.make_cache_key`, so adoption semantics stay the
  audited H06 ones;
* thresholds are PREREGISTERED below, before any measurement;
* the decision layer is a PURE function over measurement payloads so tests can
  exercise every branch with mocked measurements, while the raw-read numbers
  themselves can only come from running this script with ``--probe-cache``;
* without a real probe run the artifact records
  ``UNAVAILABLE_FAIL_CLOSED`` (never PASS unmeasured).

Verdicts: ``PASS`` (measured, every gate met -> enable=true),
``DISABLED_FAIL_CLOSED`` (measured but a gate failed, or the measurement could
not complete safely -> enable=false, correctness unaffected),
``FAIL`` (measured evidence of INCORRECTNESS, i.e. byte-parity break),
``UNAVAILABLE_FAIL_CLOSED`` (never measured).

G17 contract
------------
One authoritative cap. ``final_cap = min(owner_ceiling=1, measured_safe_cap)``
where ``measured_safe_cap = floor((available - reserved)/peak_worker)`` is
re-measured TODAY: available RAM reuses
:func:`research.resource_governor_v10.measure_available_ram_gb`; peak worker
RAM is the actual peak RSS of one real M01-style daily-closes pipeline executed
in a dedicated child process. A stale formula result (0) and an owner ceiling
(1) map onto the single reconciled number; if the measurement yields 0 the
cap IS 0 (no local scored launch) and is NOT overridden.

Host discipline: children run sequentially (never concurrently), the parent
process stays small, and a preregistered RSS fraction of currently-available
RAM aborts the cache proof fail-closed instead of risking host memory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

#: Script-path execution support: allow ``python research/<script>.py``.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

__all__ = [
    "MODULE_TAG",
    "PREREGISTERED_THRESHOLDS",
    "PRODUCER_ROLE",
    "OWNER_CEILING_HEAVY_WORKERS",
    "DEFAULT_CATALOG_PATH",
    "WINDOW_START_ISO",
    "WINDOW_END_ISO",
    "evaluate_cache_decision",
    "resolve_final_cap",
    "write_unavailable_artifacts",
]

MODULE_TAG = "v10p.g2.cache_resource.v1"
ARTIFACT_CACHE_DECISION = "cache_decision_v10"
ARTIFACT_RESOURCE_CAP = "resource_cap_report_v10"
PRODUCER_ROLE = "G2"
#: Frozen bootstrap commit of sprint V10P-R (PLAN.md section 2).
BOOTSTRAP_SHA = "5bb1a90551c8f7823773af713316a45e0ca070cd"

VALID_VERDICTS = ("PASS", "DISABLED_FAIL_CLOSED", "FAIL", "UNAVAILABLE_FAIL_CLOSED")

DEFAULT_CATALOG_PATH = "catalog"
WINDOW_START_ISO = "2025-07-22"
WINDOW_END_ISO = "2026-08-21"
BAR_TYPE_LABEL = "15-MINUTE-LAST-EXTERNAL"
FUNDING_MODEL_LABEL = "staged_per_symbol_v10_native_cadence"

#: ---------------------------------------------------------------------------
#: PREREGISTERED THRESHOLDS -- declared before any measurement is taken.
#: --------------------------------------------------------------------------- #
PREREGISTERED_THRESHOLDS: dict[str, Any] = {
    #: Mirrors research.cache_v10.SharedCacheMergeGate.MAX_RAW_READS_FULL_STRESS:
    #: a cached full pipeline may invoke the raw parquet reader at most twice.
    "max_raw_reads_cached": 2,
    #: Strict improvement rule of the old raw_bars_max_two_loads gate family:
    #: cached raw reads must be STRICTLY fewer than the uncached baseline.
    "require_strict_raw_read_improvement": True,
    #: Mirrors SharedCacheMergeGate.MIN_WALL_TIME_REDUCTION (strict target).
    "min_wall_time_reduction": 0.30,
    #: How many times the representative pipeline repeats the identical workload.
    "workload_passes": 3,
    #: Cache-ON child peak RSS may not exceed this fraction of the available RAM
    #: measured immediately before the probe (host-protection bound).
    "cached_rss_max_fraction_of_available": 0.50,
    #: Never even start measuring below this availability (fail closed early).
    "min_available_ram_gb_to_probe": 1.00,
    #: Child hard wall clock (seconds); exceeding it disables, not passes.
    "child_timeout_s": 300,
}

#: G17 owner directive ceiling (recorded in
#: research/control/v10_hardened_run/resource_cap_report.json).
OWNER_CEILING_HEAVY_WORKERS = 1
#: research.resource_governor_v10.MIN_RESERVED_RAM_GB must always be respected.
RESERVED_RAM_GB = 2.0


# --------------------------------------------------------------------------- #
# small shared helpers
# --------------------------------------------------------------------------- #
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def head_sha(repo_root: str | Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def normalize_rss_bytes(raw_rss: int) -> int:
    """``ru_maxrss`` is bytes on macOS, KiB on Linux."""
    value = int(raw_rss)
    return value if sys.platform == "darwin" else value * 1024


def peak_rss_gb_self() -> float:
    return normalize_rss_bytes(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / (1024 ** 3)


def peak_rss_gb_children() -> float:
    return normalize_rss_bytes(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss) / (1024 ** 3)


# --------------------------------------------------------------------------- #
# raw-read instrumentation (runtime-only wrap of research.panel.pq)
# --------------------------------------------------------------------------- #
class RawReadCounter:
    """Counting shim installed into ``research.panel``'s pyarrow namespace."""

    how_counted = (
        "count of pyarrow.parquet.read_table invocations made by "
        "research.panel._read_bars (one call per symbol-load pass); the shim "
        "delegates to the real reader and is restored after the workload"
    )

    def __init__(self, real_module_pq: Any = None) -> None:
        self.real = real_module_pq
        self.read_table_calls = 0
        if real_module_pq is not None:
            self._proxy_cls = self._build_proxy_cls()

    @staticmethod
    def _build_proxy_cls():
        class _Proxy:
            def __init__(self, inner: "RawReadCounter", target: Any) -> None:
                self._inner = inner
                self._target = target

            def read_table(self, *args: Any, **kwargs: Any):
                self._inner.read_table_calls += 1
                return self._target.read_table(*args, **kwargs)

            def __getattr__(self, name: str):  # noqa: D105
                return getattr(self._target, name)

        return _Proxy

    def __enter__(self) -> "RawReadCounter":
        import research.panel as panel_module

        if self.real is None:  # deferred: importing the module imports pyarrow
            self.real = panel_module.pq
            self._proxy_cls = type(self)._build_proxy_cls()
        self._panel_module = panel_module
        self._original = panel_module.pq
        panel_module.pq = self._proxy_cls(self, self._original)
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self._panel_module.pq = self._original


# --------------------------------------------------------------------------- #
# the representative FULL pipeline (real catalog bars, no synthetic data)
# --------------------------------------------------------------------------- #
def discover_catalog_symbols(catalog_path: str | Path) -> list[str]:
    """Base symbols behind the staged bar-type dirs of the REAL catalog."""
    root = Path(catalog_path) / "data" / "binance_bar"
    if not root.is_dir():
        raise FileNotFoundError(f"catalog missing bar dir: {root}")
    symbols: set[str] = set()
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        suffix = f"-{BAR_TYPE_LABEL}"
        if child.name.endswith(suffix):
            symbols.add(child.name[: -len(suffix)].split("-PERP")[0])
    if not symbols:
        raise FileNotFoundError(f"no staged bar types under {root}")
    return sorted(symbols)


def hash_catalog(catalog_path: str | Path) -> tuple[dict[str, str], int]:
    """SHA-256 of every parquet part of the catalog slice we measure."""
    root = Path(catalog_path) / "data" / "binance_bar"
    hashes: dict[str, str] = {}
    total_bytes = 0
    for path in sorted(root.rglob("*.parquet")):
        rel = path.relative_to(Path(catalog_path)).as_posix()
        hashes[rel] = sha256_file(path)
        total_bytes += path.stat().st_size
    return hashes, total_bytes


def cross_sectional_pct_ranks(panel: Mapping[str, Sequence[tuple[int, float]]]) -> dict[str, dict[str, float]]:
    """Deterministic descending pct-rank of daily closes per UTC day."""
    import pandas as pd

    frame = pd.DataFrame(
        {sym: dict(values or []) for sym, values in panel.items()}
    ).dropna(how="all")
    ranked = frame.rank(axis=1, ascending=False, pct=True)
    ranked.index = [pd.Timestamp(ts, unit="ns", tz="UTC").strftime("%Y-%m-%d") for ts in ranked.index]
    ranked = ranked.sort_index().loc[:, sorted(ranked.columns)]
    out: dict[str, dict[str, float]] = {}
    for day, row in ranked.iterrows():
        out[str(day)] = {
            sym: (None if pd.isna(val) else round(float(val), 12))
            for sym, val in row.items()
        }
    return out


def run_representative_pipeline(
    *,
    catalog_path: str | Path,
    window_start_iso: str,
    window_end_iso: str,
    cache_mode: str,
    passes: int,
) -> dict[str, Any]:
    """Execute the full loader->rank pipeline ``passes`` times, count raw reads.

    This is the ONLY place allowed to produce raw-read evidence: it really
    opens the staged parquet parts through ``research.panel._read_bars``.
    """
    from research.cache_v10 import ProcessLocalCache, make_cache_key
    from research.panel import build_daily_closes

    started = time.perf_counter()
    symbols = discover_catalog_symbols(catalog_path)
    catalog_hashes, catalog_bytes = hash_catalog(catalog_path)
    cache = ProcessLocalCache() if cache_mode == "on" else None
    key = make_cache_key(
        data_catalog_hash=sha256_json(catalog_hashes),
        symbols=symbols,
        window_start=window_start_iso,
        window_end=window_end_iso,
        bar_type=BAR_TYPE_LABEL,
        funding_model=FUNDING_MODEL_LABEL,
        signal_inputs={"pipeline": "daily_closes_pct_rank"},
    )
    per_pass: list[dict[str, Any]] = []
    last_panel: dict[str, list[tuple[int, float]]] | None = None
    with RawReadCounter(sys.modules.get("pyarrow.parquet")) as counting:
        for pass_index in range(1, int(passes) + 1):
            hits_before = -1
            panel = None
            if cache is not None:
                found = cache.get(key)
                if found is not None:
                    panel = found
                    hits_before = 1
            reads_before = counting.read_table_calls
            if panel is None:
                panel = build_daily_closes(
                    catalog_path, symbols, window_start_iso, window_end_iso
                )
                if cache is not None:
                    cache.put(key, panel)
            reads_this_pass = counting.read_table_calls - reads_before
            ranks = cross_sectional_pct_ranks(panel)
            per_pass.append(
                {
                    "pass": pass_index,
                    "raw_reads_this_pass": reads_this_pass,
                    "cache_hit": bool(cache is not None and hits_before == 1),
                    "symbols_obs": {
                        sym: len(panel.get(sym) or []) for sym in sorted(panel)
                    },
                    "rank_days": len(ranks),
                    "ranks_sha256": sha256_json(ranks),
                }
            )
            last_panel = panel
    wall_s = time.perf_counter() - started
    assert last_panel is not None
    return {
        "mode": cache_mode,
        "raw_reads_total": counting.read_table_calls,
        "per_pass": per_pass,
        "wall_time_s": round(wall_s, 4),
        "peak_rss_gb": peak_rss_gb_self(),
        "rows_last_pass": sum(len(v or []) for v in last_panel.values()),
        "symbols": symbols,
        "catalog_bytes": catalog_bytes,
        "catalog_input_hashes": {
            "combined_sha256": sha256_json(catalog_hashes),
            "files": catalog_hashes,
        },
        "result_sha256": per_pass[-1]["ranks_sha256"],
        "all_pass_digests_equal": len({p["ranks_sha256"] for p in per_pass}) == 1,
        "how_counted": RawReadCounter.how_counted,
        "cache_key": key if cache is not None else None,
        "cache_stats": cache.stats() if cache is not None else None,
    }


# --------------------------------------------------------------------------- #
# DECISION LAYER (pure functions -- unit-tested with mocked measurements)
# --------------------------------------------------------------------------- #
def evaluate_cache_decision(
    preregistered: Mapping[str, Any],
    *,
    uncached: Mapping[str, Any] | None = None,
    cached: Mapping[str, Any] | None = None,
    available_ram_gb_before: float | None = None,
) -> dict[str, Any]:
    """Pure gate over measurement payloads. Never raises; absence fails closed."""
    reasons: list[str] = []
    failed_correctness = False
    measurements_ok = isinstance(uncached, Mapping) and isinstance(cached, Mapping)

    def _num(mapping: Any, field: str) -> float | None:
        if not isinstance(mapping, Mapping):
            return None
        value = mapping.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        value = float(value)
        return value if math.isfinite(value) and value >= 0 else None

    wall_uncached = _num(uncached, "wall_time_s")
    wall_cached = _num(cached, "wall_time_s")
    reads_uncached = _num(uncached, "raw_reads_total")
    reads_cached = _num(cached, "raw_reads_total")
    rss_cached = _num(cached, "peak_rss_gb")

    parity_ok: bool | None = None
    if measurements_ok:
        digests_match = (
            str(uncached.get("result_sha256")) != "None"
            and uncached.get("result_sha256") == cached.get("result_sha256")
        )
        sequence_match = (
            [p.get("ranks_sha256") for p in uncached.get("per_pass", [])]
            == [p.get("ranks_sha256") for p in cached.get("per_pass", [])]
        )
        inputs_match = (
            uncached.get("symbols") == cached.get("symbols")
            and uncached.get("catalog_bytes") == cached.get("catalog_bytes")
        )
        stability_ok = bool(cached.get("all_pass_digests_equal"))
        parity_ok = bool(digests_match and sequence_match and inputs_match and stability_ok)
        if not parity_ok:
            failed_correctness = True
            detail = []
            if not digests_match:
                detail.append("final_rank_digest_mismatch")
            if not sequence_match:
                detail.append("per_pass_rank_sequence_mismatch")
            if not inputs_match:
                detail.append("input_surface_mismatch")
            if not stability_ok:
                detail.append("cached_run_not_deterministic_across_passes")
            reasons.append("byte_parity_broken:" + "+".join(detail))

    max_reads = int(preregistered["max_raw_reads_cached"])
    if reads_cached is None or reads_uncached is None:
        reasons.append("raw_read_measurement_missing_or_non_numeric")
    else:
        if reads_cached > max_reads:
            reasons.append(f"raw_reads_budget_exceeded:{int(reads_cached)}>{max_reads}")
        if preregistered["require_strict_raw_read_improvement"] \
                and reads_cached >= reads_uncached:
            reasons.append(
                f"no_strict_raw_read_improvement:{int(reads_cached)}>="
                f"{int(reads_uncached)}"
            )
    if available_ram_gb_before is None or rss_cached is None:
        if cached is not None:
            reasons.append("rss_guard_unevaluable_measurement_incomplete")
    else:
        budget = available_ram_gb_before * float(
            preregistered["cached_rss_max_fraction_of_available"]
        )
        if rss_cached > budget:
            reasons.append(
                f"cached_rss_exceeds_host_guard:{rss_cached:.4f}>{budget:.4f}GiB"
            )

    wall_reduction: float | None = None
    if wall_uncached and wall_cached is not None:
        wall_reduction = (wall_uncached - wall_cached) / wall_uncached
        if wall_reduction < float(preregistered["min_wall_time_reduction"]):
            reasons.append(
                f"wall_time_reduction_below_target:{wall_reduction:.6f}<"
                f"{preregistered['min_wall_time_reduction']}"
            )
    elif cached is not None:
        reasons.append("wall_time_reduction_unknown")

    if failed_correctness:
        verdict = "FAIL"
    elif reasons:
        verdict = "DISABLED_FAIL_CLOSED"
    else:
        verdict = "PASS"
    enable = verdict == "PASS"
    return {
        "verdict": verdict,
        "enable": enable,
        "reasons": reasons,
        "parity_proof": parity_ok,
        "metrics": {
            "raw_reads_uncached": reads_uncached,
            "raw_reads_cached": reads_cached,
            "max_raw_reads_cached_preregistered": max_reads,
            "strict_improvement_required": bool(
                preregistered["require_strict_raw_read_improvement"]
            ),
            "wall_time_reduction": (
                None if wall_reduction is None else round(wall_reduction, 6)
            ),
            "min_wall_time_reduction_preregistered": float(
                preregistered["min_wall_time_reduction"]
            ),
            "cached_peak_rss_gb": rss_cached,
            "available_ram_gb_before_probe": (
                None if available_ram_gb_before is None
                else round(float(available_ram_gb_before), 4)
            ),
        },
    }


def resolve_final_cap(
    *,
    owner_ceiling: int,
    available_ram_gb: float,
    reserved_ram_gb: float = RESERVED_RAM_GB,
    measured_peak_worker_ram_gb: float,
    prior_frozen_cap: int | None = None,
) -> dict[str, Any]:
    """G17 arithmetic: ``final = min(owner_ceiling, measured_safe_cap[, prior])``.

    Monotone lower-only clamp: more available RAM can never push ``final`` above
    the owner ceiling, less RAM can only decrease it, and a previously frozen
    value can only be lowered again (never silently raised).
    """
    peak = float(measured_peak_worker_ram_gb)
    if not math.isfinite(peak) or peak <= 0:
        raise ValueError("measured_peak_worker_ram_gb must be positive")
    headroom = float(available_ram_gb) - float(reserved_ram_gb)
    measured_safe_cap = int(math.floor(headroom / peak)) if headroom > 0 else 0
    candidates = [int(owner_ceiling), measured_safe_cap]
    if prior_frozen_cap is not None:
        candidates.append(int(prior_frozen_cap))
    final_cap = max(0, min(candidates))
    return {
        "headroom_gb": round(headroom, 4),
        "measured_safe_cap": measured_safe_cap,
        "formula_cap_no_owner_ceiling": measured_safe_cap,
        "owner_ceiling": int(owner_ceiling),
        "prior_frozen_cap": prior_frozen_cap,
        "final_cap": final_cap,
        "reserves_reserve_floor": float(reserved_ram_gb),
        "monotone_clamp_applied": prior_frozen_cap is not None,
        "local_scored_launch_allowed": final_cap > 0,
    }


# --------------------------------------------------------------------------- #
# artifacts
# --------------------------------------------------------------------------- #
def _artifact_base(command: Sequence[str], exit_code: int, repo_root: Path) -> dict[str, Any]:
    script_paths = [
        repo_root / "research" / "cache_resource_measure_v10.py",
        repo_root / "research" / "funding_settlements_v10.py",
        repo_root / "research" / "panel.py",
        repo_root / "research" / "cache_v10.py",
        repo_root / "research" / "funding_pit.py",
        repo_root / "research" / "resource_governor_v10.py",
        repo_root / "research" / "portfolio_engine.py",
        repo_root / "PLAN.md",
        repo_root / "CONTINUE.md",
    ]
    return {
        "schema_version": MODULE_TAG,
        "generated_at": utc_now_iso(),
        "bootstrap_sha": BOOTSTRAP_SHA,
        "head_sha": head_sha(repo_root),
        "producer_role": PRODUCER_ROLE,
        "command": list(command),
        "exit_code": exit_code,
        "host": {"platform": platform.platform(), "python": sys.version.split()[0]},
        "input_hashes": {
            p.name: (sha256_file(p) if p.exists() else "MISSING")
            for p in script_paths
        },
    }


def write_unavailable_artifacts(
    command: Sequence[str],
    *,
    repo_root: Path,
    out_dir: Path,
    reasons: Sequence[str],
    overwrite_existing: bool = False,
) -> int:
    """Default mode: never claim PASS without a real measurement.

    A previously MEASURED artifact is never silently downgraded to
    ``UNAVAILABLE_FAIL_CLOSED`` by an unmeasured invocation: unless
    ``overwrite_existing`` is explicitly requested, the existing evidence is
    preserved and the caller is told the run changed nothing.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if not overwrite_existing:
        preserved = [
            name
            for name in ("cache_decision_v10.json", "resource_cap_report_v10.json")
            if (out_dir / name).exists()
            and _is_measured_artifact(out_dir / name)
        ]
        if preserved:
            print(
                "UNMEASURED run refused to overwrite measured artifacts: "
                + ", ".join(preserved)
                + " (pass --force-unavailable to downgrade explicitly)"
            )
            return 3
    base = _artifact_base(command, 2, repo_root)
    payload_common = dict(base)
    payload_common.update(
        {
            "verdict": "UNAVAILABLE_FAIL_CLOSED",
            "enable": False,
            "reasons": list(reasons),
            "preregistered_thresholds": PREREGISTERED_THRESHOLDS,
            "measured": False,
        }
    )
    (out_dir / "cache_decision_v10.json").write_text(
        json.dumps({**payload_common, "artifact": ARTIFACT_CACHE_DECISION}, indent=2, sort_keys=True) + "\n"
    )
    cap_payload = {**base}
    cap_payload.update(
        {
            "artifact": ARTIFACT_RESOURCE_CAP,
            "verdict": "UNAVAILABLE_FAIL_CLOSED",
            "reasons": [
                "cap_not_measured_today_refusing_to_freeze_from_stale_evidence",
                *list(reasons),
            ],
            "measured": False,
            "owner_ceiling_heavy_workers": OWNER_CEILING_HEAVY_WORKERS,
            "reserved_ram_gb": RESERVED_RAM_GB,
            "final_cap": None,
            "local_scored_launch_allowed": False,
        }
    )
    (out_dir / "resource_cap_report_v10.json").write_text(
        json.dumps(cap_payload, indent=2, sort_keys=True) + "\n"
    )
    return 2


# --------------------------------------------------------------------------- #
# probe orchestration
# --------------------------------------------------------------------------- #
def _child_argv(mode: str, out_path: Path, args: argparse.Namespace, passes: int) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child-cache",
        mode,
        "--out",
        str(out_path),
        "--catalog",
        args.catalog,
        "--window-start",
        args.window_start,
        "--window-end",
        args.window_end,
        "--passes",
        str(passes),
    ]


def _spawn_child(
    argv: list[str], timeout_s: int, stage: str, report_path: Path | None
) -> tuple[dict[str, Any] | None, list[str]]:
    problems: list[str] = []
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return None, [f"child_wall_clock_exceeded:{stage}:{timeout_s}s"]
    except OSError as exc:
        return None, [f"child_spawn_failed:{stage}:{exc}"]
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-3:]
        return None, [f"child_failed:{stage}:rc={proc.returncode}:{' | '.join(tail)}"]
    try:
        # The child writes its measurement report to a file (argv --out); stdout
        # stays empty for the internal mode so nothing depends on its honesty.
        assert report_path is not None
        return json.loads(Path(report_path).read_text()), problems
    except (OSError, json.JSONDecodeError, AssertionError) as exc:
        return None, [f"child_report_unreadable:{stage}:{exc}"]


def probe_cache(args: argparse.Namespace, repo_root: Path, out_dir: Path) -> tuple[int, dict[str, Any]]:
    """Run the strict full-pipeline cache proof; write cache_decision_v10.json."""
    from research.resource_governor_v10 import measure_available_ram_gb

    command = [sys.executable, str(Path(__file__).name), "--probe-cache"]
    passes = int(PREREGISTERED_THRESHOLDS["workload_passes"])
    threshold_report = dict(PREREGISTERED_THRESHOLDS)

    out_dir.mkdir(parents=True, exist_ok=True)
    available_gb, available_method = measure_available_ram_gb()
    base = _artifact_base(command, 0, repo_root)
    # Child measurement reports live in a scratch dir outside the repo so the
    # artifact tree stays exactly on the G2 write allowlist; their content is
    # embedded verbatim in the artifact below.
    child_tmp = Path(tempfile.mkdtemp(prefix="g2_children_"))

    failure_exit = 1
    if available_gb < float(threshold_report["min_available_ram_gb_to_probe"]):
        payload = {
            **base,
            "artifact": ARTIFACT_CACHE_DECISION,
            "verdict": "DISABLED_FAIL_CLOSED",
            "enable": False,
            "measured": False,
            "reasons": [
                f"insufficient_host_memory_to_probe:{available_gb:.4f}<"
                f"{threshold_report['min_available_ram_gb_to_probe']}GiB"
            ],
            "preregistered_thresholds": threshold_report,
            "environment": {
                "available_ram_gb_before_probe": round(available_gb, 4),
                "available_method": available_method,
            },
        }
        _write_json(out_dir / "cache_decision_v10.json", payload)
        return failure_exit, payload

    report_off = child_tmp / "off.json"
    report_on = child_tmp / "on.json"
    uncached, problems_off = _spawn_child(
        _child_argv("off", report_off, args, passes),
        int(threshold_report["child_timeout_s"]),
        "uncached",
        report_off,
    )
    cached, problems_on = _spawn_child(
        _child_argv("on", report_on, args, passes),
        int(threshold_report["child_timeout_s"]),
        "cached",
        report_on,
    )
    measurement_problems = problems_off + problems_on
    decision = evaluate_cache_decision(
        threshold_report,
        uncached=uncached,
        cached=cached,
        available_ram_gb_before=available_gb,
    )
    if measurement_problems:
        # An incomplete/unsafe measurement can NEVER become PASS: degrade to
        # disabled-fail-closed unless correctness already returned FAIL.
        decision["reasons"] = list(decision["reasons"]) + measurement_problems
        if decision["verdict"] == "PASS":
            decision["verdict"] = "DISABLED_FAIL_CLOSED"
            decision["enable"] = False

    catalog_hashes = (uncached or {}).get("catalog_input_hashes") or {}
    payload = {
        **base,
        "input_hashes": {
            **base["input_hashes"],
            **{
                f"catalog:{rel}": digest
                for rel, digest in sorted(catalog_hashes.get("files", {}).items())
            },
        },
        "catalog_input_hashes_combined": catalog_hashes.get("combined_sha256"),
        "artifact": ARTIFACT_CACHE_DECISION,
        "verdict": decision["verdict"],
        "enable": decision["enable"],
        "measured": True,
        "reasons": decision["reasons"],
        "proofs": {"byte_parity": decision["parity_proof"]},
        "metrics": decision["metrics"],
        "preregistered_thresholds": threshold_report,
        "environment": {
            "available_ram_gb_before_probe": round(available_gb, 4),
            "available_method": available_method,
        },
        "workload": {
            "description": (
                "research.panel.build_daily_closes over ALL staged catalog "
                "symbols x frozen window, repeated workload.passes times, then "
                "cross-sectional descending pct-rank per UTC day"
            ),
            "catalog_path": str(args.catalog),
            "symbols": (cached or uncached or {}).get("symbols"),
            "window_start": args.window_start,
            "window_end": args.window_end,
            "passes": passes,
            "rows_last_pass": (uncached or {}).get("rows_last_pass"),
            "how_counted": RawReadCounter.how_counted,
        },
        "measurements": {
            "uncached": _strip_heavy(uncached),
            "cached": _strip_heavy(cached),
        },
        "decision_layer_version": 1,
    }
    exit_code = {
        "PASS": 0,
        "DISABLED_FAIL_CLOSED": 1,
        "FAIL": 1,
        "UNAVAILABLE_FAIL_CLOSED": 2,
    }[decision["verdict"]]
    payload["exit_code"] = exit_code
    _write_json(out_dir / "cache_decision_v10.json", payload)
    shutil.rmtree(child_tmp, ignore_errors=True)
    return exit_code, payload


def probe_resource_cap(
    args: argparse.Namespace, repo_root: Path, out_dir: Path
) -> tuple[int, dict[str, Any]]:
    """G17: re-measure today, freeze exactly one authoritative cap."""
    from research.resource_governor_v10 import (
        MIN_RESERVED_RAM_GB,
        measure_available_ram_gb,
        measure_total_ram_gb,
    )

    command = [sys.executable, str(Path(__file__).name), "--probe-resource"]
    out_dir.mkdir(parents=True, exist_ok=True)
    base = _artifact_base(command, 0, repo_root)
    available_gb, available_method = measure_available_ram_gb()
    total_gb, total_method = measure_total_ram_gb()
    child_tmp = Path(tempfile.mkdtemp(prefix="g2_children_"))

    prior_report = repo_root / "research" / "control" / "v10_hardened_run" / "resource_cap_report.json"
    prior_frozen = None
    if prior_report.exists():
        try:
            stored = json.loads(prior_report.read_text())
            stored_effective = stored.get("governor_state", {}).get("effective_heavy_workers")
            prior_frozen = None if stored_effective is None else int(stored_effective)
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            prior_frozen = None

    if available_gb <= 0:
        payload = {
            **base,
            "artifact": ARTIFACT_RESOURCE_CAP,
            "verdict": "UNAVAILABLE_FAIL_CLOSED",
            "reasons": [f"available_ram_unreadable_fail_closed:{available_method}"],
            "measured": False,
            "reserved_ram_gb": RESERVED_RAM_GB,
            "final_cap": None,
            "local_scored_launch_allowed": False,
        }
        _write_json(out_dir / "resource_cap_report_v10.json", payload)
        return 2, payload

    workload_argv = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child-cache",
        "off",
        "--out",
        str(child_tmp / "peak_worker.json"),
        "--catalog",
        args.catalog,
        "--window-start",
        args.window_start,
        "--window-end",
        args.window_end,
        "--passes",
        "1",
    ]
    peak_report = child_tmp / "peak_worker.json"
    peak_payload, problems = _spawn_child(
        workload_argv,
        int(PREREGISTERED_THRESHOLDS["child_timeout_s"]),
        "peak_worker",
        peak_report,
    )
    peak_children_secondary = peak_rss_gb_children()

    if peak_payload is None or float(peak_payload.get("peak_rss_gb", 0.0)) <= 0:
        payload = {
            **base,
            "artifact": ARTIFACT_RESOURCE_CAP,
            "verdict": "UNAVAILABLE_FAIL_CLOSED",
            "reasons": ["peak_worker_rss_unmeasurable_fail_closed", *problems],
            "measured": False,
            "reserved_ram_gb": RESERVED_RAM_GB,
            "final_cap": None,
            "local_scored_launch_allowed": False,
            "environment": {
                "available_ram_gb": round(available_gb, 4),
                "available_method": available_method,
            },
        }
        _write_json(out_dir / "resource_cap_report_v10.json", payload)
        return 2, payload

    peak_worker_gb = float(peak_payload["peak_rss_gb"])
    catalog_hashes = peak_payload.get("catalog_input_hashes") or {}
    base["input_hashes"] = {
        **base["input_hashes"],
        **{
            f"catalog:{rel}": digest
            for rel, digest in sorted(catalog_hashes.get("files", {}).items())
        },
    }
    base["catalog_input_hashes_combined"] = catalog_hashes.get("combined_sha256")
    resolved = resolve_final_cap(
        owner_ceiling=OWNER_CEILING_HEAVY_WORKERS,
        available_ram_gb=available_gb,
        reserved_ram_gb=max(RESERVED_RAM_GB, MIN_RESERVED_RAM_GB),
        measured_peak_worker_ram_gb=peak_worker_gb,
        prior_frozen_cap=prior_frozen,
    )
    reasons = [
        "authoritative_single_value_frozen_today_from_direct_measurement"
        if resolved["measured_safe_cap"] > 0
        else "measured_safe_cap_zero_fail_closed_no_local_scored_launch"
    ] + problems

    payload = {
        **base,
        "artifact": ARTIFACT_RESOURCE_CAP,
        "verdict": "PASS",
        "reasons": reasons,
        "measured": True,
        "measured_at_utc": utc_now_iso(),
        "method_sources": {
            "available_ram": {
                "value_gb": round(available_gb, 4),
                "source_function": "research.resource_governor_v10.measure_available_ram_gb",
                "method_detail": available_method,
            },
            "total_ram_gb": {"value_gb": round(total_gb, 4), "method": total_method},
            "peak_worker_ram": {
                "value_gb": round(peak_worker_gb, 4),
                "method": (
                    "peak ru_maxrss (macOS: bytes) reported by a dedicated child "
                    "process that ran ONE M01-style research.panel."
                    "build_daily_closes pass + cross-sectional ranks over the "
                    "real catalog; read back from disk"
                ),
                "child_row_count": peak_payload.get("rows_last_pass"),
                "secondary_parent_reading_getrusage_children_gb": round(
                    peak_children_secondary, 4
                ),
            },
            "reserved_ram_gb": {
                "value_gb": RESERVED_RAM_GB,
                "floor_constraint": "research.resource_governor_v10.MIN_RESERVED_RAM_GB",
            },
        },
        "arithmetic": resolved,
        "final_cap": resolved["final_cap"],
        "effective_heavy_workers": resolved["final_cap"],
        "owner_ceiling_heavy_workers": OWNER_CEILING_HEAVY_WORKERS,
        "local_scored_launch_allowed": resolved["local_scored_launch_allowed"],
        "capacity_outcome": (
            f"NO_LOCAL_SCORED_LAUNCH (final_cap={resolved['final_cap']}; "
            "measured_safe_cap=0 is preserved, never overridden)"
            if not resolved["local_scored_launch_allowed"]
            else f"LOCAL_SCORED_LAUNCH_ALLOWED_AT_CAP={resolved['final_cap']}"
        ),
        "fail_closed_rule": "if measured_safe_cap == 0 then final_cap == 0 and NO local scored launch (never overridden)",
        "conflict_resolution": {
            "formerly_disagreeing_values": {
                "v10h_formula_result": 0,
                "formula_source": "floor((avail 1.5665GB - reserved 2GB)/peak 1.25GB) measured 2026-08-27T04:21Z",
                "owner_directive_ceiling": OWNER_CEILING_HEAVY_WORKERS,
                "directive_basis": (
                    "3/3 two-worker probes safe during wave R-A3; recorded in "
                    "research/control/v10_hardened_run/resource_cap_report.json"
                ),
            },
            "resolution_rule": "final_cap = min(owner_ceiling=1, measured_safe_cap remeasured today[, prior frozen value])",
            "today_measured_safe_cap": resolved["measured_safe_cap"],
            "today_headroom_gb": resolved["headroom_gb"],
            "why_conflict_resolved": (
                "The v10H formula produced 0 because availability then sat BELOW "
                "the 2GB reserve while its configured worst-case peak (1.25GB) "
                "exceeded any feasible headroom; the owner ceiling of 1 was a "
                "supervisory bound on top of safe probes, not a RAM measurement. "
                "Today's direct re-measurement replaces BOTH: the residual RAM "
                "headroom bounds the ceiling from below, the owner ceiling binds "
                "it from above, and the single frozen number is their minimum, "
                "with the stored v10H freeze preserved untouched as history."
            ),
            "prior_frozen_cap_preserved_as_history": prior_frozen,
            "prior_report_path": prior_report.relative_to(repo_root).as_posix()
            if prior_report.exists()
            else "MISSING",
        },
        "monotone_clamp": {
            "rule": "lower-only: a later report may keep or lower final_cap, never raise it above owner_ceiling",
            "applied_prior_clamp": resolved["monotone_clamp_applied"],
        },
    }
    # Exit code reflects whether the FREEZE was performed, not whether the
    # number allows launching: the authoritative signals are final_cap and
    # local_scored_launch_allowed below.
    exit_code = 0 if payload["verdict"] == "PASS" else 2
    payload["exit_code"] = exit_code
    payload["exit_code_semantics"] = (
        "0 = cap measured and frozen today (value may legally be 0); "
        "2 = could not measure (artifact UNAVAILABLE_FAIL_CLOSED)"
    )
    payload["reasons"].append(
        f"final_cap_frozen={resolved['final_cap']}"
        + ("" if resolved["final_cap"] else " (NO local scored launch)")
    )
    _write_json(out_dir / "resource_cap_report_v10.json", payload)
    shutil.rmtree(child_tmp, ignore_errors=True)
    return exit_code, payload


AUDIT_TEST_FILES = (
    "tests/test_g2_funding_v10.py",
    "tests/test_g2_cache_resource_v10.py",
)


def run_blocker_tests(repo_root: Path) -> dict[str, Any]:
    """Run the G2 test files once each and record honest pass/fail counts."""
    import re as _re

    results: dict[str, Any] = {}
    for rel in AUDIT_TEST_FILES:
        started = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", rel],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=600,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            results[rel] = {
                "exit_code": None,
                "error": f"pytest_spawn_failed:{exc}",
                "wall_time_s": round(time.perf_counter() - started, 3),
            }
            continue
        tail = (proc.stdout or "").strip().splitlines()
        summary = tail[-1] if tail else ""
        parsed: dict[str, int] = {}
        for name in ("passed", "failed", "skipped", "error"):
            match = _re.search(rf"(\d+)\s+{name}", summary)
            if match:
                parsed[name] = int(match.group(1))
        results[rel] = {
            "exit_code": proc.returncode,
            "summary_line": summary,
            "counts": parsed,
            "wall_time_s": round(time.perf_counter() - started, 3),
            "output_tail": tail[-6:],
        }
    return results


def emit_audit(
    args: argparse.Namespace, repo_root: Path, out_dir: Path
) -> tuple[int, dict[str, Any]]:
    """Assemble research/audits/v10/g2_funding_resource_validation.json."""
    command = [sys.executable, str(Path(__file__).name), "--emit-audit"]
    audit_dir = repo_root / "research" / "audits" / "v10"
    audit_dir.mkdir(parents=True, exist_ok=True)

    funding_tests = run_blocker_tests(repo_root)
    funding_ok = all(
        entry.get("exit_code") == 0 for entry in funding_tests.values()
    ) and bool(funding_tests)

    cache_doc: dict[str, Any] | None = None
    cap_doc: dict[str, Any] | None = None
    cache_path = out_dir / "cache_decision_v10.json"
    cap_path = out_dir / "resource_cap_report_v10.json"
    missing: list[str] = []
    if cache_path.exists():
        cache_doc = json.loads(cache_path.read_text())
    else:
        missing.append(cache_path.name)
    if cap_path.exists():
        cap_doc = json.loads(cap_path.read_text())
    else:
        missing.append(cap_path.name)

    blockers: dict[str, Any] = {
        "BG3": {
            "blocker": "BG3 staged per-symbol funding -> execution schedule/holding-span accrual",
            "verdict": "PASS" if funding_ok else "FAIL",
            "reasons": (
                [
                    "generic loader reuses research.funding_pit.load_funding_bundle layout (no duplicated staging logic)",
                    "settlement cadence taken per symbol from staged stamps; unknown first interval skipped, never imputed (no 8h assumption)",
                    "PIT gate publish_ns <= observed_through_ns enforced before accrual",
                    "accrual restricted to holding span with held_fraction = overlap/native-interval",
                ]
                if funding_ok
                else ["g2 funding test suite failed: see blocker_tests"]
            ),
            "evidence": {
                "module": "research/funding_settlements_v10.py",
                "tests": AUDIT_TEST_FILES[0],
                "sign_convention": "LONG_PAYS_POSITIVE_RATE",
            },
        },
        "G15": {
            "blocker": "G15 independent numeric funding-accrual reconciliation",
            "verdict": "PASS" if funding_ok else "FAIL",
            "reasons": (
                [
                    "expected accrual values are hard-coded hand computations of rate * notional * held_fraction",
                    "no internal helper imported to derive expected values (tests derive literals only)",
                    "long and short mirrored fixtures, positive and negative rates, partial and full epochs",
                    "heterogeneous cadence fixture (8h vs 12h) asserts per-symbol settlement boundaries",
                    "PIT bounds: late publication, unknown first interval, entry/exit seams, outside-span exclusion",
                ]
                if funding_ok
                else ["g2 funding test suite failed: see blocker_tests"]
            ),
            "evidence": {"tests": AUDIT_TEST_FILES[0], "independence": "hard-coded expected literals"},
        },
        "F2": {
            "blocker": "F2/G-H06 strict full-pipeline cache proof (or disable fail-closed)",
            "verdict": (
                cache_doc.get("verdict") if cache_doc else "UNAVAILABLE_FAIL_CLOSED"
            ),
            "reasons": (
                list(cache_doc.get("reasons", []))
                if cache_doc
                else ["cache_decision_v10.json missing: never measured"]
            ),
            "evidence": {
                "artifact": "research/cache_decision_v10.json",
                "measured": bool(cache_doc and cache_doc.get("measured")),
                "raw_reads_cached": (cache_doc or {}).get("metrics", {}).get(
                    "raw_reads_cached"
                ),
                "raw_reads_uncached": (cache_doc or {}).get("metrics", {}).get(
                    "raw_reads_uncached"
                ),
                "byte_parity": (cache_doc or {}).get("proofs", {}).get("byte_parity"),
                "workload": (cache_doc or {}).get("workload"),
            },
        },
        "G17": {
            "blocker": "G17 one authoritative resource cap",
            "verdict": (
                cap_doc.get("verdict") if cap_doc else "UNAVAILABLE_FAIL_CLOSED"
            ),
            "reasons": (
                list(cap_doc.get("reasons", []))
                if cap_doc
                else ["resource_cap_report_v10.json missing: never measured"]
            ),
            "evidence": {
                "artifact": "research/resource_cap_report_v10.json",
                "final_cap": (cap_doc or {}).get("final_cap"),
                "capacity_outcome": (cap_doc or {}).get("capacity_outcome"),
                "measured_safe_cap": (cap_doc or {}).get("arithmetic", {}).get(
                    "measured_safe_cap"
                ),
                "local_scored_launch_allowed": (cap_doc or {}).get(
                    "local_scored_launch_allowed"
                ),
            },
        },
    }

    order = {"FAIL": 3, "UNAVAILABLE_FAIL_CLOSED": 2, "DISABLED_FAIL_CLOSED": 1, "PASS": 0}
    verdicts = [b["verdict"] for b in blockers.values()]
    if not funding_ok:
        overall = "FAIL"
    elif "FAIL" in verdicts:
        overall = "FAIL"
    elif "UNAVAILABLE_FAIL_CLOSED" in verdicts:
        overall = "UNAVAILABLE_FAIL_CLOSED"
    elif "DISABLED_FAIL_CLOSED" in verdicts:
        overall = "DISABLED_FAIL_CLOSED"
    else:
        overall = "PASS"
    reasons: list[str] = [f"overall={overall}"]
    if missing:
        reasons.append(f"artifact_missing_unmeasured:{','.join(sorted(missing))}")
    for name, verdict in zip(blockers, verdicts):
        reasons.append(f"{name}={verdict}")

    cap_allowed = (cap_doc or {}).get("local_scored_launch_allowed")
    payload = {
        "schema_version": MODULE_TAG,
        "artifact": "g2_funding_resource_validation",
        "launch_authorization": (
            "NONE: final_cap=0 -> no local scored launch (fail closed)"
            if cap_allowed is False
            else "NOT_GRANTED_BY_G2: cap artifact absent or permissive; launch authority stays with A1"
        ),
        "generated_at": utc_now_iso(),
        "bootstrap_sha": BOOTSTRAP_SHA,
        "head_sha": head_sha(repo_root),
        "producer_role": PRODUCER_ROLE,
        "command": list(command),
        "exit_code": 0 if overall == "PASS" else (2 if overall == "UNAVAILABLE_FAIL_CLOSED" else 1),
        "verdict": overall,
        "reasons": reasons or [f"overall={overall}"],
        "blockers": blockers,
        "blocker_tests": funding_tests,
        "blockers_nonpass_are_fail_closed": True,
        "scope_note": (
            "BG3/G15 deliver the loader+accrual contract and schedule adapters as a "
            "wrap-around module; production wiring into research/portfolio_engine.py "
            "is intentionally untouched (outside the G2 allowlist) and stays with "
            "the runner integrator (A1/G1)."
        ),
        "limitations": [
            "F2 measurement reflects THIS host's instantaneous memory pressure; re-run before scored waves",
            "G17 cap is re-measured value, valid for today only; lower-only monotone rule applies to later reports",
            "catalog exposes 2 staged symbols (BTCUSDT, ETHUSDT); the representative pipeline loads the entire real staged slice",
        ],
        "input_hashes": {
            **_artifact_base(command, 0, repo_root)["input_hashes"],
            **_catalog_hashes_from(cache_doc),
        },
    }
    _write_json(audit_dir / "g2_funding_resource_validation.json", payload)
    return payload["exit_code"], payload


def _strip_heavy(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    slim = dict(payload)
    slim.pop("catalog_bytes", None)
    return slim


def _catalog_hashes_from(doc: Mapping[str, Any] | None) -> dict[str, str]:
    """Pull ``catalog:<relpath>`` entries out of a measured artifact."""
    if not isinstance(doc, Mapping):
        return {}
    hashes = doc.get("input_hashes")
    if not isinstance(hashes, Mapping):
        return {}
    return {
        key: value
        for key, value in sorted(hashes.items())
        if key.startswith("catalog:") and isinstance(value, str)
    }


def _is_measured_artifact(path: Path) -> bool:
    try:
        return bool(json.loads(path.read_text()).get("measured"))
    except (OSError, json.JSONDecodeError):
        return False


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=os.getcwd())
    parser.add_argument("--out-dir", default=None, help="artifact directory (default <repo>/research)")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--window-start", default=WINDOW_START_ISO)
    parser.add_argument("--window-end", default=WINDOW_END_ISO)
    parser.add_argument(
        "--probe-cache",
        action="store_true",
        help="run the strict full-pipeline cache measurement (real reads)",
    )
    parser.add_argument(
        "--probe-resource",
        action="store_true",
        help="measure RAM + peak worker RAM and freeze the authoritative cap",
    )
    parser.add_argument("--probe-all", action="store_true", help="both probes sequentially")
    parser.add_argument(
        "--force-unavailable",
        action="store_true",
        help="let an UNMEASURED run overwrite previously measured artifacts",
    )
    parser.add_argument(
        "--emit-audit",
        action="store_true",
        help="assemble research/audits/v10/g2_funding_resource_validation.json",
    )
    parser.add_argument(
        "--print-verdicts",
        action="store_true",
        help="print one-line verdicts for CI/log consumption",
    )
    parser.add_argument(
        "--child-cache",
        choices=("on", "off"),
        default=None,
        help=argparse.SUPPRESS,  # internal: isolated measurement child
    )
    parser.add_argument("--out", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--passes", type=int, default=None, help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # NB: pass argv straight through -- passing an empty list would make
    # argparse ignore the process command line entirely.
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "research"

    if args.child_cache is not None:  # internal child mode
        passes = int(args.passes or PREREGISTERED_THRESHOLDS["workload_passes"])
        report = run_representative_pipeline(
            catalog_path=args.catalog,
            window_start_iso=args.window_start,
            window_end_iso=args.window_end,
            cache_mode=args.child_cache,
            passes=passes,
        )
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(json.dumps(report, sort_keys=True))
        return 0

    overall = 0
    launched = (
        args.probe_all
        or args.probe_cache
        or args.probe_resource
        or getattr(args, "emit_audit", False)
    )
    if getattr(args, "emit_audit", False):
        code, payload = emit_audit(args, repo_root, out_dir)
        overall |= code
        if args.print_verdicts:
            print(
                f"AUDIT verdict={payload['verdict']} "
                + " ".join(f"{k}={v['verdict']}" for k, v in payload["blockers"].items())
            )
        if not (args.probe_all or args.probe_cache or args.probe_resource):
            return overall
    if not launched:
        exit_code = write_unavailable_artifacts(
            [sys.executable, Path(__file__).name],
            repo_root=repo_root,
            out_dir=out_dir,
            reasons=[
                "no_probe_requested_measurements_absent_never_claim_pass",
                "run --probe-cache / --probe-resource (or --probe-all) to measure",
            ],
            overwrite_existing=bool(args.force_unavailable),
        )
        if exit_code != 3:
            print(
                "wrote UNAVAILABLE_FAIL_CLOSED artifacts (no measurement requested)"
            )
        if args.print_verdicts:
            print("BLOCKER=F2 verdict=UNAVAILABLE_FAIL_CLOSED enable=False")
            print("BLOCKER=G17 verdict=UNAVAILABLE_FAIL_CLOSED final_cap=<unresolved>")
        return exit_code

    overall = 0
    if args.probe_all or args.probe_cache:
        code, payload = probe_cache(args, repo_root, out_dir)
        overall |= code
        if args.print_verdicts:
            m = payload.get("metrics", {})
            print(
                f"BLOCKER=F2 verdict={payload['verdict']} enable={payload['enable']} "
                f"raw_reads_cached={m.get('raw_reads_cached')} "
                f"raw_reads_uncached={m.get('raw_reads_uncached')} "
                f"parity={payload.get('proofs', {}).get('byte_parity')} "
                f"wall_reduction={m.get('wall_time_reduction')} "
                f"reasons={payload['reasons']}"
            )
    if args.probe_all or args.probe_resource:
        code, payload = probe_resource_cap(args, repo_root, out_dir)
        overall |= code
        if args.print_verdicts:
            print(
                f"BLOCKER=G17 verdict={payload['verdict']} "
                f"final_cap={payload.get('final_cap')} "
                f"measured_safe_cap={payload.get('arithmetic', {}).get('measured_safe_cap')} "
                f"headroom_gb={payload.get('arithmetic', {}).get('headroom_gb')} "
                f"launch_allowed={payload.get('local_scored_launch_allowed')}"
            )
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
