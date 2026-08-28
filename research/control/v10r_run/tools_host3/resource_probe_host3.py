"""Host-3 G17 resource probe: Windows port of the frozen probe's arithmetic.

The frozen probe (research/cache_resource_measure_v10.py --probe-resource)
is Unix-bound (`import resource`, vm_stat, ru_maxrss) and cannot execute on
this Windows host. This port keeps the frozen formula EXACTLY by calling the
frozen `ResourceGovernorV10` / `resolve_final_cap` arithmetic from
research/resource_governor_v10.py unchanged, and ports only the two
measurement sources:

* available RAM: ctypes GlobalMemoryStatusEx ullAvailPhys (conservative
  "available physical", Windows counterpart of vm_stat
  free+inactive+speculative);
* peak worker RAM: a child process runs ONE M01-style pass
  (research.panel.build_daily_closes + cross-sectional ranks over the real
  staged catalog, the same workload the frozen child executes) while the
  parent polls the child's RSS every 100 ms (ru_maxrss unavailable on
  Windows; polling can only understate the peak, which is conservative in
  the safe direction for the cap's numerator... it raises measured peak
  confidence only via a 1.15 documented safety multiplier applied to the
  observed peak before the frozen formula is applied).

Verdict keys mirror the frozen artifact. OWNER_CEILING for the R3 phase is 1
(owner_amendment_ceiling_v10r.json scopes 3 to R4/V11 only).
"""

from __future__ import annotations

import ctypes
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
EXEC = Path(r"C:\Users\ROYAL\exec-v10-R1c")
PY = REPO / ".venv/Scripts/python.exe"
OUT = REPO / "research/control/v10r_run/resource_cap_report_host3.json"
CATALOG = "catalog_live_crypto"
WINDOW_START = "2025-08-21T00:00:00Z"
WINDOW_END = "2026-08-21T00:00:00Z"
RESERVED_GB = 2.0
OWNER_CEILING_R3 = 1
PEAK_SAFETY = 1.15  # documented conservative multiplier for poll-based peak

sys.path.insert(0, str(EXEC))  # frozen W3 code for the governor arithmetic

CHILD = '''
import sys, json
sys.path.insert(0, r"{exec}")
from research.panel import build_daily_closes
import yaml, pandas as pd
syms = yaml.safe_load(open("config/research_scan_top20.yaml"))
symbols = list(syms["market"]["symbols"])
closes = build_daily_closes("{catalog}", symbols, "{ws}", "{we}")
frame = pd.DataFrame({{s: pd.Series([c for _, c in v]) for s, v in closes.items()}})
rets = frame.pct_change()
ranks = rets.rank(axis=1)
print(json.dumps({{"symbols": len(closes), "rows": int(len(frame)), "rank_cols": int(ranks.shape[1])}}))
'''.format(exec=str(EXEC), catalog=CATALOG, ws=WINDOW_START, we=WINDOW_END)


def available_ram_gb() -> tuple[float, str]:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return 0.0, "GlobalMemoryStatusEx_failed_fail_closed"
    return st.ullAvailPhys / (1024**3), "GlobalMemoryStatusEx ullAvailPhys (win port of vm_stat free+inactive+speculative)"


def total_ram_gb() -> tuple[float, str]:
    import psutil

    return psutil.virtual_memory().total / (1024**3), "psutil total (win port of sysctl hw.memsize)"


def peak_worker_gb() -> tuple[float, str, dict]:
    import psutil

    child_path = REPO / "research/control/v10r_run/tools_host3/_probe_child_workload.py"
    child_path.write_text(CHILD)
    proc = subprocess.Popen(
        [str(PY), str(child_path)],
        cwd=str(EXEC),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    ps = psutil.Process(proc.pid)
    peak = 0.0
    t0 = time.time()
    out_lines = []
    while proc.poll() is None:
        try:
            rss = ps.memory_info().rss
            for ch in ps.children(recursive=True):
                try:
                    rss += ch.memory_info().rss
                except psutil.Error:
                    pass
            peak = max(peak, rss)
        except psutil.Error:
            pass
        if time.time() - t0 > 600:
            proc.kill()
            break
        time.sleep(0.1)
    rest = proc.stdout.read() if proc.stdout else ""
    out_lines = [ln for ln in (rest or "").splitlines() if ln.strip().startswith("{")]
    summary = json.loads(out_lines[-1]) if out_lines else {}
    if peak <= 0 or proc.returncode != 0:
        return 0.0, "child_workload_failed_fail_closed", {"rc": proc.returncode, "tail": (rest or "")[-400:]}
    observed = peak / (1024**3)
    return observed * PEAK_SAFETY, f"rss poll 100ms x{PEAK_SAFETY} safety (win port of ru_maxrss child)", {
        "observed_peak_gb": round(observed, 4), "child_summary": summary,
    }


def main() -> int:
    from research.resource_governor_v10 import ResourceGovernorV10, MIN_RESERVED_RAM_GB

    avail, avail_method = available_ram_gb()
    total, total_method = total_ram_gb()
    payload: dict = {
        "artifact": "resource_cap_report_host3",
        "producer_role": "A1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "port_note": "frozen probe Unix-bound on Windows; frozen governor arithmetic used unchanged, "
        "only measurement sources ported (see module docstring)",
        "environment": {
            "available_ram_gb": round(avail, 4),
            "available_method": avail_method,
            "total_ram_gb": round(total, 4),
            "total_method": total_method,
        },
        "reserved_ram_gb": RESERVED_GB,
        "floor_constraint": f"MIN_RESERVED_RAM_GB={MIN_RESERVED_RAM_GB}",
    }
    if avail <= 0:
        payload.update({"verdict": "UNAVAILABLE_FAIL_CLOSED", "measured": False,
                        "final_cap": None, "measured_safe_cap": 0,
                        "local_scored_launch_allowed": False})
        OUT.write_text(json.dumps(payload, indent=1))
        print("VERDICT: UNAVAILABLE_FAIL_CLOSED (available unreadable)")
        return 2
    peak, peak_method, peak_detail = peak_worker_gb()
    payload["peak_worker"] = {"value_gb": round(peak, 4), "method": peak_method, **peak_detail}
    if peak <= 0:
        payload.update({"verdict": "UNAVAILABLE_FAIL_CLOSED", "measured": False,
                        "final_cap": None, "measured_safe_cap": 0,
                        "local_scored_launch_allowed": False})
        OUT.write_text(json.dumps(payload, indent=1))
        print("VERDICT: UNAVAILABLE_FAIL_CLOSED (peak unmeasurable)")
        return 2
    gov = ResourceGovernorV10(
        contract_cap=10_000,  # uncapped probe: measured_safe_cap only
        reserved_ram_gb=max(RESERVED_GB, MIN_RESERVED_RAM_GB),
        measured_peak_worker_ram_gb=peak,
        available_ram_gb=avail,
        available_method=avail_method,
    )
    measured_safe_cap = int(gov.effective_heavy_workers)
    # Frozen H05 rule inside effective_heavy_workers: caps >=2 require the
    # consecutive safe two-worker probe streak, else forced to 1.
    raw_ram_cap = int(gov.ram_cap_workers)
    final_cap_r3 = min(OWNER_CEILING_R3, measured_safe_cap)
    payload.update({
        "verdict": "PASS" if measured_safe_cap > 0 else "MEASURED_SAFE_CAP_ZERO",
        "measured": True,
        "measured_safe_cap": measured_safe_cap,
        "raw_ram_cap_workers": raw_ram_cap,
        "h05_promotion_unlocked": bool(gov._promotion_unlocked()),
        "final_cap_r3_m01": final_cap_r3,
        "final_cap_r4_v11_ceiling3": min(3, measured_safe_cap),
        "local_scored_launch_allowed": final_cap_r3 > 0,
        "reasons": ["authoritative_single_value_frozen_today_from_direct_measurement (host3 port)"],
    })
    OUT.write_text(json.dumps(payload, indent=1))
    print(json.dumps({k: payload[k] for k in ("verdict", "measured_safe_cap", "final_cap_r3_m01",
                                              "final_cap_r4_v11_ceiling3", "environment", "peak_worker")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
