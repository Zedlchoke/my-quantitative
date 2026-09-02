"""Resource governor tests (sprint V9H H05; PLAN §6.H08 items 13-14).

H08 item -> test id map:
    13 test_h08_13_over_cap_admission_rejected
    14 test_h08_14_governor_lowers_cap_when_ram_insufficient

Plus: two-worker promotion rule (3 consecutive safe probes), unsafe-probe
reset, PnL-visibility monotone lock, fail-closed zero headroom, persisted
probe evidence, and the psutil-free RAM measurement sanity on darwin.
Deterministic: available RAM is injected; no machine-state dependence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from research.resource_governor_v10 import (
    MIN_RESERVED_RAM_GB,
    OverCapacityError,
    PromotionLockedError,
    ResourceGovernorV10,
    freeze,
    measure_available_ram_gb,
    measure_total_ram_gb,
)


def make_gov(**overrides: Any) -> ResourceGovernorV10:
    kwargs: Dict[str, Any] = {
        "contract_cap": 4,
        "reserved_ram_gb": 2.0,
        "measured_peak_worker_ram_gb": 1.0,
        "available_ram_gb": 16.0,
        "available_method": "injected-test",
    }
    kwargs.update(overrides)
    return ResourceGovernorV10(**kwargs)


# ------------------------------------------------------------------- H08-14
def test_h08_14_governor_lowers_cap_when_ram_insufficient() -> None:
    # RAM formula alone would allow 3, but cap>=2 needs probe evidence first:
    # forced to 1 until three consecutive safe two-worker probes exist.
    gov = freeze(4, 2.0, 2.0, available_ram_gb=8.0)
    assert gov.ram_cap_workers == 3
    assert gov.effective_heavy_workers == 1  # promotion gate forces down
    for _ in range(3):
        gov.record_two_worker_probe(safe=True, detail="unscored ram probe")
    assert gov.effective_heavy_workers == 3  # now min(contract=4, ram=3)
    assert gov.effective_heavy_workers < gov.contract_cap  # RAM lowered it

    # Extreme pressure: headroom for zero workers fails closed at 0.
    starved = make_gov(available_ram_gb=3.0, measured_peak_worker_ram_gb=2.0)
    assert starved.ram_cap_workers == 0
    assert starved.effective_heavy_workers == 0


# ------------------------------------------------------------------- H08-13
def test_h08_13_over_cap_admission_rejected() -> None:
    gov = make_gov(contract_cap=1, available_ram_gb=16.0)
    assert gov.effective_heavy_workers == 1
    assert gov.admit_worker(0) is True  # worker 1 fits under cap 1
    with pytest.raises(OverCapacityError) as err:
        gov.admit_worker(1)  # worker N+1 rejected at the cap
    assert "effective_heavy_workers=1" in str(err.value)

    # With promotion unlocked, cap 2 admits a second worker but not a third.
    promoted = make_gov(contract_cap=2)
    for _ in range(3):
        promoted.record_two_worker_probe(safe=True)
    assert promoted.effective_heavy_workers == 2
    assert promoted.admit_worker(1) is True
    with pytest.raises(OverCapacityError):
        promoted.admit_worker(2)


def test_freeze_validates_contract_fail_closed() -> None:
    with pytest.raises(Exception) as reserved_err:
        freeze(2, 1.0, 1.0, available_ram_gb=16.0)  # reserve below 2 GB forbidden
    assert str(MIN_RESERVED_RAM_GB) in str(reserved_err.value)
    with pytest.raises(Exception):
        freeze(2, 2.0, 0.0, available_ram_gb=16.0)  # peak worker ram must be > 0
    with pytest.raises(Exception):
        make_gov(contract_cap=0)
    with pytest.raises(Exception):
        make_gov(contract_cap=1, available_ram_gb=-1.0)


def test_two_worker_promotion_requires_three_consecutive_safe_probes(tmp_path: Path) -> None:
    state_path = tmp_path / "governor_state.json"
    gov = freeze(
        2, 2.0, 1.0,
        available_ram_gb=16.0,
        state_path=state_path,
    )
    assert gov.effective_heavy_workers == 1  # forced cap=1 without evidence
    gov.record_two_worker_probe(safe=True, workers_active=2)
    gov.record_two_worker_probe(safe=True, workers_active=2)
    assert gov.consecutive_safe_two_worker_probes == 2
    assert gov.effective_heavy_workers == 1  # still short of three
    gov.record_two_worker_probe(safe=False, detail="pressure spike", workers_active=2)
    assert gov.consecutive_safe_two_worker_probes == 0  # unsafe resets streak
    assert gov.effective_heavy_workers == 1
    for i in range(3):
        gov.record_two_worker_probe(safe=True, detail=f"probe-{i}", workers_active=2)
    assert gov.effective_heavy_workers == 2  # evidence complete -> promoted
    assert len(gov.probe_records) == 6
    # Probe evidence persists atomically and survives reload.
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(payload["probe_records"]) == 6
    restored = ResourceGovernorV10.load_state(state_path)
    assert restored.effective_heavy_workers == 2
    assert restored.consecutive_safe_two_worker_probes == 3


def test_pnl_visible_locks_cap_monotone_down_only(tmp_path: Path) -> None:
    state_path = tmp_path / "gov_pnl.json"
    gov = freeze(3, 2.0, 1.0, available_ram_gb=8.0, state_path=state_path)
    for _ in range(3):
        gov.record_two_worker_probe(safe=True)
    assert gov.effective_heavy_workers == 3  # probes unlock min(contract=3, ram=6)
    gov.declare_pnl_visible(note="scored metrics viewed")
    assert gov.cap_snapshot_at_pnl == 3
    # More RAM arrives afterwards: cap may NOT increase past the snapshot.
    gov.available_ram_gb = 64.0
    gov.contract_cap = 5
    assert gov.effective_heavy_workers == 3  # may NOT increase past the snapshot
    with pytest.raises(PromotionLockedError):
        gov.record_two_worker_probe(safe=True)
    # Decreasing stays allowed at all times.
    gov.set_contract_cap(1)
    assert gov.effective_heavy_workers == 1
    restored = ResourceGovernorV10.load_state(state_path)
    assert restored.pnl_visible is True and restored.cap_snapshot_at_pnl == 3
    assert restored.effective_heavy_workers <= 3


@pytest.mark.skipif(sys.platform != "darwin", reason="vm_stat/sysctl method is macOS")
def test_ram_measurement_darwin_documented_and_positive() -> None:
    total_gb, total_method = measure_total_ram_gb()
    avail_gb, avail_method = measure_available_ram_gb()
    assert total_gb > 4.0 and "hw.memsize" in total_method
    assert avail_method.startswith(("vm_stat", "memory_pressure"))
