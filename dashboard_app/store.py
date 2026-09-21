"""Snapshot store: incremental, fail-closed, read-only.

Refresh contract (dispatch §8):

- Every refresh stats the ledger/mark/heartbeat files first. When the
  (size, mtime_ns) fingerprint is unchanged the cached snapshot is
  served and NO history is re-read (the 30 s poll is nearly free).
- When bytes changed, the snapshot is rebuilt by the LIVE engine
  imported from the integration worktree — the exact code that writes
  the ledgers, so schema always matches and every fail-closed rule of
  the engine applies unchanged.
- A failed build (corrupt/partial JSONL being appended right now,
  schema violation, …) NEVER crashes the app and NEVER fabricates
  data: the last good snapshot stays on screen, the failure is
  reported in the status block, and the next cycle retries.
- The store never writes anything: restart can never double-count and
  ledger bytes are provably untouched (tests assert digests).
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .resolve import RuntimePaths
from .status import app_status, family_chip, load_heartbeat

_ENGINES: Dict[str, Any] = {}


class EngineLoadError(RuntimeError):
    pass


def load_engine(worktree: str) -> Any:
    """Import research.shadow_v1.dashboard.snapshot FROM the live
    integration worktree (not bundled, not vendored)."""
    worktree = os.path.abspath(worktree)
    cached = _ENGINES.get(worktree)
    if cached is not None:
        return cached
    if not os.path.isfile(
        os.path.join(worktree, "research", "shadow_v1", "dashboard", "snapshot.py")
    ):
        raise EngineLoadError(
            f"no dashboard engine under worktree {worktree}"
        )
    # Purge any research.* modules that may have been imported from a
    # different checkout, then insert the live worktree first.
    for name in [m for m in sys.modules if m == "research" or m.startswith("research.")]:
        del sys.modules[name]
    if worktree not in sys.path:
        sys.path.insert(0, worktree)
    try:
        module = importlib.import_module("research.shadow_v1.dashboard.snapshot")
    except Exception as exc:  # noqa: BLE001 - surfaced to the status block
        raise EngineLoadError(f"engine import failed: {exc}") from exc
    loaded_from = getattr(module, "__file__", "") or ""
    if os.path.abspath(loaded_from) != os.path.abspath(
        os.path.join(worktree, "research", "shadow_v1", "dashboard", "snapshot.py")
    ):
        raise EngineLoadError(
            f"engine loaded from unexpected path: {loaded_from}"
        )
    _ENGINES[worktree] = module
    return module


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fingerprint(paths: RuntimePaths) -> Tuple[Tuple[str, int, int], ...]:
    stats: List[Tuple[str, int, int]] = []
    for path in paths.fingerprint_files():
        try:
            st = os.stat(path)
            stats.append((path, st.st_size, st.st_mtime_ns))
        except OSError:
            stats.append((path, -1, -1))
    return tuple(stats)


def family_gross(fam_block: Mapping[str, Any]) -> Dict[str, Any]:
    """Gross exposure = Σ|notional| of open positions (dispatch §7).

    The canonical ``gross`` field inside old mark records was measured
    to disagree with the positions (0.0071 vs ≈84k of notional — the
    pre-remediation writer bug), so it fails verification and is NOT
    used; gross is computed from the official per-position notional
    fields of the engine snapshot.
    """
    positions = fam_block.get("positions") or []
    gross = None
    if isinstance(positions, list):
        # an empty positions list is an ESTABLISHED zero (flat), not
        # missing data; a missing/None list stays N/A.
        total = 0.0
        for pos in positions:
            notional = pos.get("notional") if isinstance(pos, dict) else None
            if isinstance(notional, (int, float)):
                total += abs(float(notional))
            else:
                total = None
                break
        gross = total
    equity = None
    mark = fam_block.get("latest_valid_mark")
    if isinstance(mark, dict) and isinstance(mark.get("equity"), (int, float)):
        equity = float(mark["equity"])
    pct = (gross / equity * 100.0) if gross is not None and equity else None
    return {
        "usd": gross,
        "pct": pct,
        "open_positions": len(positions) if isinstance(positions, list) else None,
        "method": "sum_abs_position_notional",
    }


def _realized_unrealized_totals(
    families: Mapping[str, Mapping[str, Any]]
) -> Dict[str, Any]:
    """Sum realized/unrealized across families ONLY when all three
    latest valid marks share one timestamp (strict-sum rule; mixed
    timestamps would be a made-up number -> N/A)."""
    marks: Dict[str, Dict[str, Any]] = {}
    for fid, fam in families.items():
        mark = fam.get("latest_valid_mark")
        if isinstance(mark, dict):
            marks[fid] = mark
    out: Dict[str, Any] = {
        "per_family": {
            fid: {
                "realized_pnl": m.get("realized_pnl"),
                "unrealized_pnl": m.get("unrealized_pnl"),
                "mark_timestamp_utc": m.get("mark_timestamp_utc"),
            }
            for fid, m in sorted(marks.items())
        },
        "realized_pnl": None,
        "unrealized_pnl": None,
        "mark_timestamp_utc": None,
        "reason": None,
    }
    if not marks:
        out["reason"] = "no valid mark"
        return out
    stamps = {str(m.get("mark_timestamp_utc")) for m in marks.values()}
    if len(stamps) != 1 or None in stamps:
        out["reason"] = (
            "mark timestamps của các family lệch nhau — không cộng tùy tiện (N/A)"
        )
        return out
    stamp = stamps.pop()
    realized = 0.0
    unrealized = 0.0
    for mark in marks.values():
        r = mark.get("realized_pnl")
        u = mark.get("unrealized_pnl")
        if not isinstance(r, (int, float)) or not isinstance(u, (int, float)):
            out["reason"] = "thiếu realized/unrealized ở mark mới nhất (N/A)"
            return out
        realized += float(r)
        unrealized += float(u)
    out.update(
        realized_pnl=realized,
        unrealized_pnl=unrealized,
        mark_timestamp_utc=stamp,
    )
    return out


class SnapshotStore:
    """Stat-keyed incremental cache over the live engine."""

    def __init__(self, paths: RuntimePaths, engine: Optional[Any] = None):
        self.paths = paths
        self._engine = engine
        self._lock = threading.Lock()
        self._snapshot: Optional[Dict[str, Any]] = None
        self._fingerprint: Optional[Tuple[Tuple[str, int, int], ...]] = None
        self._build_error: Optional[str] = None
        self._last_refresh_utc: Optional[str] = None
        self._last_ok_refresh_utc: Optional[str] = None
        self._rebuilds = 0
        self._cache_hits = 0
        self._shadow_start_utc = self._read_shadow_start()

    # -- engine -------------------------------------------------------
    @property
    def engine(self) -> Any:
        if self._engine is None:
            worktree = self.paths.worktree or self.paths.runtime_root
            self._engine = load_engine(worktree)
        return self._engine

    def _read_shadow_start(self) -> Optional[str]:
        obj, _err = load_heartbeat(self.paths.valuation_heartbeat_path)
        if isinstance(obj, dict):
            value = obj.get("shadow_start_utc")
            if isinstance(value, str) and value:
                return value
        return None

    # -- refresh ------------------------------------------------------
    def refresh(self, now_iso: Optional[str] = None) -> None:
        """One incremental refresh cycle (cheap when nothing changed)."""
        with self._lock:
            now_iso = now_iso or _now_iso()
            self._last_refresh_utc = now_iso
            fingerprint = _fingerprint(self.paths)
            if (
                self._snapshot is not None
                and self._build_error is None
                and fingerprint == self._fingerprint
            ):
                self._cache_hits += 1
                return
            try:
                engine = self.engine
                ledger_paths = engine.resolve_ledger_paths(self.paths.ledgers_dir)
                valuation_paths = engine.resolve_valuation_mark_paths(
                    self.paths.ledgers_dir
                )
                snapshot = engine.build_dashboard_snapshot(
                    ledger_paths,
                    now_iso,
                    identity_manifest_path=self.paths.identity_manifest,
                    shadow_start_utc=self._shadow_start_utc,
                    valuation_marks_by_family=valuation_paths,
                )
            except Exception as exc:  # noqa: BLE001 - fail-closed, keep old
                self._build_error = f"{type(exc).__name__}: {exc}"
                self._fingerprint = fingerprint
                return
            self._snapshot = dict(snapshot)
            self._fingerprint = fingerprint
            self._build_error = None
            self._last_ok_refresh_utc = now_iso
            self._rebuilds += 1

    # -- envelope -----------------------------------------------------
    def envelope(self, now_iso: Optional[str] = None,
                 now_dt: Optional[Any] = None) -> Dict[str, Any]:
        """The JSON served at /api/snapshot.json = engine snapshot + app block."""
        self.refresh(now_iso=now_iso)
        if now_dt is None:
            from datetime import datetime, timezone as _tz

            now_dt = datetime.now(_tz.utc)
        with self._lock:
            snapshot = self._snapshot
            build_error = self._build_error
            last_ok = self._last_ok_refresh_utc
            last_refresh = self._last_refresh_utc
            rebuilds = self._rebuilds
            cache_hits = self._cache_hits

        hb_obj, hb_err = load_heartbeat(self.paths.heartbeat_path)
        vhb_obj, vhb_err = load_heartbeat(self.paths.valuation_heartbeat_path)
        status = app_status(
            snapshot, build_error, hb_obj, hb_err, vhb_obj, vhb_err, now=now_dt
        )

        # Layout/file errors and per-family corruption are DATA ERROR:
        # the page still shows the last good snapshot, clearly labelled.
        # Corruption can surface in the strategy-ledger family blocks
        # AND in the valuation-mark family blocks — scan both.
        corruptions: Dict[str, str] = {}
        for section in ("families",):
            for fid, fam in ((snapshot or {}).get(section) or {}).items():
                reason = fam.get("corruption")
                if reason:
                    corruptions[f"{fid} (ledger)"] = str(reason)
        for fid, fam in (
            ((snapshot or {}).get("valuation") or {}).get("families") or {}
        ).items():
            reason = fam.get("corruption")
            if reason:
                corruptions[f"{fid} (marks)"] = str(reason)
        layout_errors: List[str] = []
        for label, path in (
            ("ledgers", self.paths.ledgers_dir),
            ("valuation_marks", self.paths.valuation_dir),
        ):
            if os.path.exists(path) and not os.path.isdir(path):
                layout_errors.append(f"{label} không phải thư mục: {path}")
        if layout_errors or corruptions:
            status = dict(status)
            status["state"] = "DATA ERROR"
            status["reasons"] = (
                layout_errors
                + [
                    f"corrupt: {fid}: {reason}"
                    for fid, reason in sorted(corruptions.items())
                ]
                + list(status.get("reasons") or [])
            )
            status["corruptions"] = corruptions
            status["layout_errors"] = layout_errors

        app: Dict[str, Any] = {
            "schema": "quant_shadow_dashboard_app_v1",
            "status": status,
            "last_refresh_utc": last_refresh,
            "last_ok_refresh_utc": last_ok,
            "engine_build_error": build_error,
            "rebuilds": rebuilds,
            "cache_hits": cache_hits,
            "read_only": True,
            "refresh_interval_seconds": 30,
            "paths": self.paths.describe(),
            "engine_source": getattr(self._engine, "__file__", None)
            or (
                os.path.join(
                    self.paths.worktree or "", "research", "shadow_v1",
                    "dashboard", "snapshot.py",
                )
                if self.paths.worktree
                else None
            ),
        }

        families: Dict[str, Any] = {}
        gross_combined = 0.0
        gross_seen = False
        held: Dict[str, List[str]] = {}
        if snapshot:
            valuation = snapshot.get("valuation") or {}
            fam_blocks = valuation.get("families") or {}
            heartbeat_per_family: Dict[str, Any] = (
                (hb_obj or {}).get("last_completed") or {}
            )
            for fid, fam in sorted(fam_blocks.items()):
                hb_row = heartbeat_per_family.get(fid) or {}
                families[fid] = {
                    "chip": family_chip(fam, hb_row.get("data_status")),
                    "gross": family_gross(fam),
                    "data_age_seconds": fam.get("data_age_seconds"),
                    "heartbeat_data_status": hb_row.get("data_status"),
                    "heartbeat_accounting_status": hb_row.get("accounting_status"),
                    "next_decision_utc": (
                        ((hb_obj or {}).get("next_decision_per_family") or {}
                         ).get(fid)
                    ),
                }
                positions = fam.get("positions") or []
                held[fid] = sorted(
                    {
                        str(p.get("symbol"))
                        for p in positions
                        if isinstance(p, dict) and p.get("symbol")
                    }
                )
                gross = families[fid]["gross"]["usd"]
                if gross is not None:
                    gross_combined += gross
                    gross_seen = True
            combined = valuation.get("combined") or {}
            equity = combined.get("equity")
            app["gross_combined"] = {
                "usd": gross_combined if gross_seen else None,
                "pct": (
                    gross_combined / float(equity) * 100.0
                    if gross_seen and isinstance(equity, (int, float)) and equity
                    else None
                ),
                "method": "sum over families of sum_abs_position_notional",
            }
            app["realized_unrealized_totals"] = _realized_unrealized_totals(
                fam_blocks
            )
            app["held_assets_by_family"] = held
            app["families"] = families
            app["counters"] = snapshot.get("counters")
            app["valuation_counters"] = valuation.get("counters")
            app["banners"] = snapshot.get("banners")
            app["sl_na"] = snapshot.get("sl_na")
            app["tp_na"] = snapshot.get("tp_na")
            app["timezone_default"] = snapshot.get("timezone_default")

        return {"snapshot": snapshot, "app": app}

    # -- accessors ----------------------------------------------------
    @property
    def snapshot(self) -> Optional[Dict[str, Any]]:
        return self._snapshot

    @property
    def build_error(self) -> Optional[str]:
        return self._build_error

    def trade_detail(self, trade_or_event_id: str) -> Optional[Dict[str, Any]]:
        if not self._snapshot:
            return None
        index = self._snapshot.get("trade_index") or {}
        if trade_or_event_id in index:
            return index[trade_or_event_id]
        event_index = self._snapshot.get("event_index") or {}
        return event_index.get(trade_or_event_id)
