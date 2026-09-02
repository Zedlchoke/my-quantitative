"""V10 enforced resource governor (sprint V9H H05).

Freezes the heavy-worker concurrency from unscored measurements:

    effective_heavy_workers = min(
        contract_cap,
        floor((available_ram_gb - reserved_ram_gb) / measured_peak_worker_ram_gb)
    )

* ``reserved_ram_gb`` must be >= 2.0 GB (macOS/Orca reserve; validated,
  fails closed on smaller values).
* Available RAM is measured psutil-free:
  1. total physical memory via ``sysctl -n hw.memsize``;
  2. free estimate via ``vm_stat`` pages free+inactive+speculative
     (fallback: ``memory_pressure`` "System-wide memory free percentage",
     final fallback: 0.0 => nothing admissible, fail closed).
  Callers may inject ``available_ram_gb`` for deterministic tests/probes.
* ``admit_worker(active_count)`` raises :class:`OverCapacityError` when the
  worker N+1 would exceed the effective cap.
* Two-worker promotion rule: any effective cap >= 2 requires evidence of
  THREE consecutive safe two-worker probes (recorded outcomes); otherwise
  the cap is forced to 1.
* lower-only-after-pnl-seen: once ``pnl_visible`` is declared, the effective
  cap can only DECREASE (monotone clamp); promotion past the snapshot is
  refused.

State (probe records + pnl flag) persists atomically to an optional JSON
state file using tmp + fsync + os.replace, so probe evidence survives
restarts and is auditable.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

MIN_RESERVED_RAM_GB = 2.0
SAFE_PROBES_REQUIRED_FOR_TWO_WORKERS = 3
PROBE_TIMEOUT_S = 10.0
STATE_VERSION = 1


class GovernorError(RuntimeError):
    """Base error for resource-governor misuse or unsatisfiable freeze."""


class OverCapacityError(GovernorError):
    """Admission rejected: worker N+1 would exceed the effective cap."""


class PromotionLockedError(GovernorError):
    """Cap increase attempted after PnL was visible; only decreases allowed."""


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, path)


def _run_metric_cmd(cmd: Sequence[str]) -> Optional[str]:
    try:
        proc = subprocess.run(
            list(cmd), capture_output=True, text=True, timeout=PROBE_TIMEOUT_S
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def measure_total_ram_gb() -> Tuple[float, str]:
    out = _run_metric_cmd(["sysctl", "-n", "hw.memsize"])
    if out is None and sys.platform == "darwin":
        out = _run_metric_cmd(["/usr/sbin/sysctl", "-n", "hw.memsize"])
    if out:
        try:
            return int(out.strip()) / (1024 ** 3), "sysctl hw.memsize"
        except ValueError:
            pass
    return 0.0, "unknown_fail_closed"


def measure_available_ram_gb() -> Tuple[float, str]:
    """Psutil-free available-RAM estimate in GiB (documented method).

    Primary: vm_stat pages free+inactive+speculative * page size.
    Fallback: memory_pressure "System-wide memory free percentage".
    Fail-closed fallback: 0.0 (nothing admissible).
    """
    vm_out = _run_metric_cmd(["vm_stat"])
    page_size = 4096
    if vm_out:
        m = re.search(r"page size of (\d+) bytes", vm_out)
        if m:
            page_size = int(m.group(1))

        def _pages(label: str) -> int:
            mm = re.search(re.escape(label) + r":\s+(\d+)\.", vm_out)
            return int(mm.group(1)) if mm else 0

        free_pages = (
            _pages("Pages free")
            + _pages("Pages inactive")
            + _pages("Pages speculative")
        )
        if free_pages > 0:
            return free_pages * page_size / (1024 ** 3), "vm_stat free+inactive+speculative"
    mp_out = _run_metric_cmd(["memory_pressure"])
    if mp_out:
        m = re.search(r"System-wide memory free percentage:\s*(\d+)%", mp_out)
        if m:
            total_gb, _ = measure_total_ram_gb()
            if total_gb > 0:
                return total_gb * int(m.group(1)) / 100.0, "memory_pressure free %"
    return 0.0, "unknown_fail_closed"


class ResourceGovernorV10:
    """Enforced concurrency cap for heavy research workers."""

    def __init__(
        self,
        *,
        contract_cap: int,
        reserved_ram_gb: float = MIN_RESERVED_RAM_GB,
        measured_peak_worker_ram_gb: float,
        available_ram_gb: float,
        available_method: str = "injected",
        state_path: Optional[Union[str, Path]] = None,
        probe_records: Optional[List[Dict[str, Any]]] = None,
        pnl_visible: bool = False,
        cap_snapshot_at_pnl: Optional[int] = None,
    ) -> None:
        if not isinstance(contract_cap, int) or contract_cap < 1:
            raise GovernorError("contract_cap must be a positive integer")
        if reserved_ram_gb < MIN_RESERVED_RAM_GB:
            raise GovernorError(
                f"reserved_ram_gb must be >= {MIN_RESERVED_RAM_GB} GB (macOS/Orca reserve)"
            )
        if measured_peak_worker_ram_gb <= 0:
            raise GovernorError("measured_peak_worker_ram_gb must be positive")
        if available_ram_gb < 0:
            raise GovernorError("available_ram_gb must be non-negative")
        self.contract_cap = int(contract_cap)
        self.reserved_ram_gb = float(reserved_ram_gb)
        self.measured_peak_worker_ram_gb = float(measured_peak_worker_ram_gb)
        self.available_ram_gb = float(available_ram_gb)
        self.available_method = str(available_method)
        self.state_path = Path(state_path) if state_path is not None else None
        self.probe_records: List[Dict[str, Any]] = list(probe_records or [])
        self.pnl_visible = bool(pnl_visible)
        self.cap_snapshot_at_pnl = cap_snapshot_at_pnl

    # ------------------------------------------------------------------ freeze
    @property
    def ram_cap_workers(self) -> int:
        headroom = self.available_ram_gb - self.reserved_ram_gb
        if headroom <= 0:
            return 0
        return int(math.floor(headroom / self.measured_peak_worker_ram_gb))

    @property
    def consecutive_safe_two_worker_probes(self) -> int:
        streak = 0
        for probe in reversed(self.probe_records):
            if probe.get("safe"):
                streak += 1
            else:
                break
        return streak

    def _promotion_unlocked(self) -> bool:
        return self.consecutive_safe_two_worker_probes >= SAFE_PROBES_REQUIRED_FOR_TWO_WORKERS

    @property
    def effective_heavy_workers(self) -> int:
        cap = min(self.contract_cap, self.ram_cap_workers)
        if cap >= 2 and not self._promotion_unlocked():
            # Cap >= 2 REQUIRES the three consecutive safe two-worker probes;
            # otherwise the cap is forced down to 1 (H05).
            cap = min(cap, 1)
        if cap >= 2 and self.cap_snapshot_at_pnl is not None:
            # After PnL is visible the cap can only decrease, never increase.
            cap = min(cap, self.cap_snapshot_at_pnl)
        return max(0, cap)

    # -------------------------------------------------------------- admission
    def admit_worker(self, active_count: int) -> bool:
        """Admit worker N+1 unless ``active_count`` already reaches the cap."""
        if not isinstance(active_count, int) or active_count < 0:
            raise GovernorError("active_count must be a non-negative integer")
        cap = self.effective_heavy_workers
        if active_count >= cap:
            raise OverCapacityError(
                f"worker {active_count + 1} rejected: active={active_count} >= "
                f"effective_heavy_workers={cap} "
                f"(contract={self.contract_cap}, ram_cap={self.ram_cap_workers}, "
                f"promotion_unlocked={self._promotion_unlocked()})"
            )
        return True

    # ----------------------------------------------------------------- probes
    def record_two_worker_probe(
        self, *, safe: bool, detail: str = "", workers_active: int = 2
    ) -> Dict[str, Any]:
        """Record one explicit two-worker probe outcome (evidence list)."""
        if self.pnl_visible and safe:
            current = self.effective_heavy_workers
            if self.cap_snapshot_at_pnl is not None and current >= self.cap_snapshot_at_pnl:
                raise PromotionLockedError(
                    "cannot promote past cap snapshot taken when PnL became visible; "
                    "cap may only decrease now"
                )
        probe = {
            "utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
            "safe": bool(safe),
            "workers_active": int(workers_active),
            "detail": str(detail),
        }
        self.probe_records.append(probe)
        if self.state_path is not None:
            self.save_state()
        return probe

    def declare_pnl_visible(self, note: str = "") -> None:
        """Freeze the current effective cap as the monotone ceiling."""
        self.pnl_visible = True
        if self.cap_snapshot_at_pnl is None:
            self.cap_snapshot_at_pnl = self.effective_heavy_workers
        if self.state_path is not None:
            self.save_state()

    def set_contract_cap(self, cap: int) -> None:
        """Lower (or raise pre-PnL) the contractual cap; post-PnL raises are
        clamped by the snapshot so the cap can only decrease."""
        if not isinstance(cap, int) or cap < 1:
            raise GovernorError("contract_cap must be a positive integer")
        self.contract_cap = cap
        if self.state_path is not None:
            self.save_state()

    # ------------------------------------------------------------------ state
    def describe(self) -> Dict[str, Any]:
        return {
            "version": STATE_VERSION,
            "contract_cap": self.contract_cap,
            "reserved_ram_gb": self.reserved_ram_gb,
            "measured_peak_worker_ram_gb": self.measured_peak_worker_ram_gb,
            "available_ram_gb": round(self.available_ram_gb, 4),
            "available_method": self.available_method,
            "ram_cap_workers": self.ram_cap_workers,
            "effective_heavy_workers": self.effective_heavy_workers,
            "consecutive_safe_two_worker_probes": self.consecutive_safe_two_worker_probes,
            "probes_required_for_two_workers": SAFE_PROBES_REQUIRED_FOR_TWO_WORKERS,
            "pnl_visible": self.pnl_visible,
            "cap_snapshot_at_pnl": self.cap_snapshot_at_pnl,
            "probe_records": list(self.probe_records),
        }

    def save_state(self) -> None:
        if self.state_path is None:
            raise GovernorError("no state_path configured")
        atomic_write_json(self.state_path, self.describe())

    @classmethod
    def load_state(cls, state_path: Union[str, Path]) -> "ResourceGovernorV10":
        with open(state_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls(
            contract_cap=payload["contract_cap"],
            reserved_ram_gb=payload["reserved_ram_gb"],
            measured_peak_worker_ram_gb=payload["measured_peak_worker_ram_gb"],
            available_ram_gb=payload["available_ram_gb"],
            available_method=payload.get("available_method", "restored"),
            state_path=state_path,
            probe_records=list(payload.get("probe_records", [])),
            pnl_visible=bool(payload.get("pnl_visible", False)),
            cap_snapshot_at_pnl=payload.get("cap_snapshot_at_pnl"),
        )


def freeze(
    cap_contract: int,
    reserved_ram_gb: float = MIN_RESERVED_RAM_GB,
    measured_peak_worker_ram_gb: float = 0.0,
    *,
    available_ram_gb: Optional[float] = None,
    state_path: Optional[Union[str, Path]] = None,
) -> ResourceGovernorV10:
    """Freeze the effective heavy-worker cap from unscored measurements.

    Signature matches PLAN H05: freeze(cap_contract, reserved_ram_gb>=2,
    measured_peak_worker_ram_gb).  When ``available_ram_gb`` is omitted it is
    measured live (see :func:`measure_available_ram_gb` for the documented,
    psutil-free method).
    """
    if measured_peak_worker_ram_gb is None or float(measured_peak_worker_ram_gb) <= 0:
        raise GovernorError("measured_peak_worker_ram_gb must be a positive number")
    if available_ram_gb is None:
        available_ram_gb, available_method = measure_available_ram_gb()
    else:
        available_method = "injected"
    governor = ResourceGovernorV10(
        contract_cap=cap_contract,
        reserved_ram_gb=reserved_ram_gb,
        measured_peak_worker_ram_gb=float(measured_peak_worker_ram_gb),
        available_ram_gb=float(available_ram_gb),
        available_method=available_method,
        state_path=state_path,
    )
    if state_path is not None:
        governor.save_state()
    return governor
