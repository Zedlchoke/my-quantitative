#!/usr/bin/env python
"""CRYPTO-NG1 P0 adoption runner (lane p0, task crypto-ng1-p0-adoption).

Runs, measures and publishes:

1. S4 re-pin verification through the plane adapter (frozen digests,
   CADS resolve verify-on-read; mismatch => BLOCKED_DATA, no repair);
2. panel bounds via the manifest-verified query plane (frozen DuckDB
   query over CADS-resolved bytes);
3. bounded shadow-parity pilot (plane read vs direct CADS-object read)
   on panel_BTCUSDT_h1.csv and panel_SOLUSDT_h1.csv;
4. announcement-instant calendar census (official keyless sources,
   mandatory canaries) -> p0_calendar_census.json;
5. OPTIONAL keyless funding-rate endpoint re-proof -> p0_funding_reproof.json
   (BLOCKED_NOT_CONSUMED on failure; never blocks);
6. the cycle's P0 test command (pytest tests/test_crypto_ng1_p0.py).

Publishes p0_gate.json with per-section command/exit-code/observed/
margin/evidence and a verdict derived ONLY from what actually ran.

Exit codes: 0 = PASS, 3 = BLOCKED_DATA (digest/store/census/tests), 4 =
usage/internal error.  The CADS store is used READ-ONLY.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _REPO_ROOT)

from research.assets.crypto_ng1 import calendar_census  # noqa: E402
from research.assets.crypto_ng1.plane_adapter import (  # noqa: E402
    FROZEN_S4_ENTRIES, CryptoNG1Plane, PlaneConsumptionRefused,
    PlaneDataBlocked,
)

SCHEMA = "crypto_ng1_run/p0_gate@1"
VENV_PYTHON = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
ARTIFACT_DIR = os.path.join(_REPO_ROOT, "research", "control",
                            "crypto_ng1_run")
DEFAULT_STORE_ROOT = (
    "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store")
PANEL_ORDER = [
    "staging_v17/panel_BTCUSDT_h1.csv",
    "staging_v17/panel_ETHUSDT_h1.csv",
    "staging_v17/panel_SOLUSDT_h1.csv",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store-root", default=DEFAULT_STORE_ROOT)
    ap.add_argument("--skip-tests", action="store_true",
                    help="do not run the pytest command (recorded NOT_RUN)")
    args = ap.parse_args()

    measured_utc = _now()
    runner_cmd = (f"{VENV_PYTHON} research/control/crypto_ng1_run/"
                  f"run_p0_adoption.py")
    gate: dict = {
        "schema": SCHEMA,
        "task_id": "crypto-ng1-p0-adoption",
        "cycle_id": "CRYPTO_NG1",
        "lane": "p0",
        "measured_utc": measured_utc,
        "worktree": _REPO_ROOT,
        "cads_store_root": os.path.abspath(args.store_root),
        "cads_store_mode": "READ-ONLY",
        "sections": {},
        "verdict_basis": [],
    }

    blocker: str | None = None

    # ---- git identity of the measured checkout ----------------------- #
    git = {"head_sha": None, "branch": None}
    try:
        git["head_sha"] = subprocess.run(
            ["git", "-C", _REPO_ROOT, "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        git["branch"] = subprocess.run(
            ["git", "-C", _REPO_ROOT, "branch", "--show-current"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        git["error"] = str(exc)
    gate["git"] = git

    # ---- adapter init -------------------------------------------------- #
    try:
        plane = CryptoNG1Plane(store_root=args.store_root)
    except PlaneDataBlocked as exc:
        gate["sections"]["adapter_init"] = {
            "command": runner_cmd, "exit_code": 3,
            "observed": f"{exc.reason}: {exc}", "margin": None,
            "verdict": "BLOCKED_DATA",
            "evidence_path": None}
        gate["verdict"] = "BLOCKED_DATA"
        gate["verdict_basis"].append(f"adapter init: {exc.reason}")
        _write_json(os.path.join(ARTIFACT_DIR, "p0_gate.json"), gate)
        print(json.dumps({"verdict": gate["verdict"],
                          "blocker": str(exc)}, indent=1))
        return 3

    # ---- 1. S4 re-pin verify through the adapter ----------------------- #
    repin_entries: dict[str, dict] = {}
    repin_ok = True
    for entry_name, meta in FROZEN_S4_ENTRIES.items():
        row: dict = {
            "series": meta["series"],
            "frozen_sha256": meta["sha256"],
            "command": f"{runner_cmd} (section s4_repin:{entry_name})",
        }
        try:
            res = plane.consume(entry_name)
            row.update({
                "exit_code": 0,
                "pin_series": res["series_pinned"],
                "cads_address": res["cads_address"],
                "measured_sha256": res["sha256_measured"],
                "bytes": res["bytes"],
                "authority_verdict": res["verdict"],
                "observed": (f"address==frozen==measured "
                             f"{res['sha256_measured']}"),
                "margin": "exact digest match",
                "verdict": "PASS",
            })
        except (PlaneDataBlocked, PlaneConsumptionRefused) as exc:
            reason = getattr(exc, "reason", "REFUSED")
            row.update({
                "exit_code": 3, "observed": str(exc), "margin": None,
                "verdict": f"BLOCKED ({reason})",
            })
            repin_ok = False
            blocker = blocker or f"s4_repin {entry_name}: {exc}"
        repin_entries[entry_name] = row
    gate["sections"]["s4_repin"] = {
        "command": f"{runner_cmd} (section s4_repin)",
        "exit_code": 0 if repin_ok else 3,
        "observed": {k: v.get("observed") for k, v in repin_entries.items()},
        "margin": ("all 5 frozen digests exact" if repin_ok
                   else "digest/path mismatch (fail-closed)"),
        "verdict": "PASS" if repin_ok else "BLOCKED_DATA",
        "entries": repin_entries,
        "evidence_path": "research/control/crypto_ng1_run/p0_gate.json",
    }
    gate["verdict_basis"].append(
        f"s4_repin={'PASS' if repin_ok else 'BLOCKED_DATA'}")

    # ---- 2. panel bounds via manifest-verified query -------------------- #
    bounds_rows: dict[str, dict] = {}
    bounds_ok = repin_ok
    manifest_window: list[str] | None = None
    for entry_name in PANEL_ORDER:
        row = {"command": f"{runner_cmd} (section panel_bounds:{entry_name})"}
        try:
            q = plane.query_panel_bounds(entry_name)
            row.update({
                "exit_code": 0 if q["query_verdict"] == "SUCCESS" else 3,
                "query_verdict": q["query_verdict"],
                "query_identity": q["identity"],
                "rows": q["rows"],
                "result_digest": q["result_digest"],
                "observed": q["rows"],
                "margin": "frozen query SUCCESS; schema enforced",
                "verdict": "PASS" if q["query_verdict"] == "SUCCESS"
                           else "BLOCKED_DATA",
            })
            if q["query_verdict"] != "SUCCESS":
                bounds_ok = False
                blocker = blocker or f"panel_bounds {entry_name}: {q['reason']}"
        except (PlaneDataBlocked, PlaneConsumptionRefused) as exc:
            row.update({"exit_code": 3, "observed": str(exc),
                        "verdict": "BLOCKED_DATA"})
            bounds_ok = False
            blocker = blocker or f"panel_bounds {entry_name}: {exc}"
        bounds_rows[entry_name] = row
    # manifest window (authoritative cross-check) via the plane as well
    try:
        manifest = json.loads(
            plane.consume("staging_v17/panel_manifest.json")["data"])
        manifest_window = manifest.get("window")
    except (PlaneDataBlocked, PlaneConsumptionRefused) as exc:
        bounds_ok = False
        blocker = blocker or f"panel_manifest: {exc}"
    gate["sections"]["panel_bounds"] = {
        "command": f"{runner_cmd} (section panel_bounds)",
        "exit_code": 0 if bounds_ok else 3,
        "observed": {"manifest_window": manifest_window,
                     "panels": {k: v.get("observed")
                                for k, v in bounds_rows.items()}},
        "margin": "manifest window vs measured plane bounds",
        "verdict": "PASS" if bounds_ok else "BLOCKED_DATA",
        "entries": bounds_rows,
        "evidence_path": "research/control/crypto_ng1_run/p0_gate.json",
    }
    gate["verdict_basis"].append(
        f"panel_bounds={'PASS' if bounds_ok else 'BLOCKED_DATA'}")

    # ---- 3. shadow parity (bounded pilot) ------------------------------- #
    parity_rows: dict[str, dict] = {}
    parity_ok = repin_ok
    for entry_name in ("staging_v17/panel_BTCUSDT_h1.csv",
                       "staging_v17/panel_SOLUSDT_h1.csv"):
        row = {"command": f"{runner_cmd} (section shadow_parity:{entry_name})"}
        try:
            p = plane.shadow_parity(entry_name)
            row.update({
                "exit_code": 0 if p["identical"] else 3,
                "plane_sha256": p["plane_sha256"],
                "direct_sha256": p["direct_sha256"],
                "bytes": p["bytes"],
                "observed": (f"plane {p['plane_sha256']} vs direct "
                             f"{p['direct_sha256']}"),
                "margin": "0 (identical)" if p["identical"] else "digests differ",
                "verdict": "PASS" if p["identical"] else "BLOCKED_DATA",
            })
            if not p["identical"]:
                parity_ok = False
                blocker = blocker or f"shadow_parity {entry_name} mismatch"
        except (PlaneDataBlocked, PlaneConsumptionRefused) as exc:
            row.update({"exit_code": 3, "observed": str(exc),
                        "verdict": "BLOCKED_DATA"})
            parity_ok = False
            blocker = blocker or f"shadow_parity {entry_name}: {exc}"
        parity_rows[entry_name] = row
    gate["sections"]["shadow_parity"] = {
        "command": f"{runner_cmd} (section shadow_parity)",
        "exit_code": 0 if parity_ok else 3,
        "observed": {k: v.get("observed") for k, v in parity_rows.items()},
        "margin": "sha256(plane read) == sha256(direct CADS-object read)",
        "verdict": "PASS" if parity_ok else "BLOCKED_DATA",
        "entries": parity_rows,
        "evidence_path": "research/control/crypto_ng1_run/p0_gate.json",
    }
    gate["verdict_basis"].append(
        f"shadow_parity={'PASS' if parity_ok else 'BLOCKED_DATA'}")

    # ---- 4. calendar census --------------------------------------------- #
    census_path = os.path.join(ARTIFACT_DIR, "p0_calendar_census.json")
    census: dict
    if manifest_window and bounds_ok:
        window_start = date.fromisoformat(manifest_window[0])
        window_end = date.fromisoformat(manifest_window[1])
        census = calendar_census.run_census(
            window_start, window_end, verdict_fn=plane.verdict)
    else:
        census = {
            "schema": calendar_census.SCHEMA,
            "measured_utc": _now(),
            "verdict": "NOT_RUN_NO_WINDOW",
            "reason": "panel window not measurable (upstream section blocked)",
        }
    _write_json(census_path, census)
    census_section = {
        "command": f"{runner_cmd} (section calendar_census)",
        "exit_code": (0 if census.get("verdict") in
                      ("PASS", "PASS_WITH_BLS_BLOCKED") else 3),
        "observed": {"verdict": census.get("verdict"),
                     "instant_count": census.get("instant_count"),
                     "meetings_in_window": census.get("meetings_in_window"),
                     "sources": census.get("sources", {}).get("bls", {}).get(
                         "status")},
        "margin": (f"{census.get('instant_count')} instants with official "
                   "publication timestamps; canaries all PASS"),
        "verdict": ("PASS" if census.get("verdict") in
                    ("PASS", "PASS_WITH_BLS_BLOCKED") else "BLOCKED_DATA"),
        "evidence_path": "research/control/crypto_ng1_run/p0_calendar_census.json",
    }
    gate["sections"]["calendar_census"] = census_section
    gate["verdict_basis"].append(
        f"calendar_census={census.get('verdict')}")
    if census_section["verdict"] != "PASS":
        blocker = blocker or f"calendar_census {census.get('verdict')}"

    # ---- 5. funding re-proof (optional, non-blocking) -------------------- #
    funding = calendar_census.funding_reproof(
        ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    funding_path = os.path.join(ARTIFACT_DIR, "p0_funding_reproof.json")
    _write_json(funding_path, funding)
    gate["sections"]["funding_reproof"] = {
        "command": f"{runner_cmd} (section funding_reproof)",
        "exit_code": 0,   # optional probe: never blocks
        "observed": {"status": funding["status"],
                     "symbols_ok": [p["symbol"] for p in funding["probes"]
                                    if p["ok"]]},
        "margin": "optional; BLOCKED_NOT_CONSUMED allowed by design",
        "verdict": "NON_BLOCKING",
        "evidence_path": "research/control/crypto_ng1_run/p0_funding_reproof.json",
    }
    gate["verdict_basis"].append(
        f"funding_reproof={funding['status']} (optional)")

    # ---- 6. series-name canaries through the adapter --------------------- #
    canary_rows = []
    for fake in ("S4:binance-funding-settlements", "S9:not-a-real-series"):
        try:
            plane.resolve_entry(fake, "x.csv", expected_sha256=None)
            canary_rows.append({"series": fake, "refused": False,
                                "verdict": "FAIL"})
        except PlaneConsumptionRefused as exc:
            canary_rows.append({"series": fake, "refused": True,
                                "reason": str(exc)[:140],
                                "verdict": "PASS"})
        except PlaneDataBlocked as exc:
            # unknown series are refused at the verdict gate; a blocked
            # verdict is also a refusal (fail-closed)
            canary_rows.append({"series": fake, "refused": True,
                                "reason": f"{exc.reason}: {exc}"[:140],
                                "verdict": "PASS"})
    canaries_ok = all(r["verdict"] == "PASS" for r in canary_rows)
    gate["sections"]["series_name_canaries"] = {
        "command": f"{runner_cmd} (section series_name_canaries)",
        "exit_code": 0 if canaries_ok else 3,
        "observed": canary_rows,
        "margin": "2 nonexistent series both refused (P-7)",
        "verdict": "PASS" if canaries_ok else "BLOCKED_DATA",
        "evidence_path": "research/control/crypto_ng1_run/p0_gate.json",
    }
    gate["verdict_basis"].append(
        f"series_name_canaries={'PASS' if canaries_ok else 'FAIL'}")
    if not canaries_ok:
        blocker = blocker or "series canary produced a consume"

    # ---- 7. tests --------------------------------------------------------- #
    if args.skip_tests:
        gate["sections"]["tests"] = {
            "command": f"cd {_REPO_ROOT} && {VENV_PYTHON} -m pytest "
                       "tests/test_crypto_ng1_p0.py -q",
            "exit_code": None, "verdict": "NOT_RUN (--skip-tests)",
        }
        tests_ok = False
    else:
        cmd = [VENV_PYTHON, "-m", "pytest", "tests/test_crypto_ng1_p0.py",
               "-q"]
        proc = subprocess.run(cmd, cwd=_REPO_ROOT, capture_output=True,
                              text=True)
        tests_ok = proc.returncode == 0
        gate["sections"]["tests"] = {
            "command": f"cd {_REPO_ROOT} && {VENV_PYTHON} -m pytest "
                       "tests/test_crypto_ng1_p0.py -q",
            "exit_code": proc.returncode,
            "observed": (proc.stdout or "").strip().splitlines()[-3:],
            "margin": "pytest exit code",
            "verdict": "PASS" if tests_ok else "FAIL",
        }
    gate["verdict_basis"].append(f"tests={'PASS' if tests_ok else 'FAIL'}")

    # ---- verdict ---------------------------------------------------------- #
    gate["verdict"] = "PASS" if (
        repin_ok and bounds_ok and parity_ok and canaries_ok and tests_ok
        and census_section["verdict"] == "PASS"
    ) else "BLOCKED_DATA"
    if gate["verdict"] != "PASS":
        gate["blocker"] = blocker or "see sections"
    gate["census"] = {"path": "research/control/crypto_ng1_run/"
                              "p0_calendar_census.json",
                      "verdict": census.get("verdict")}
    gate["funding"] = {"path": "research/control/crypto_ng1_run/"
                               "p0_funding_reproof.json",
                       "status": funding["status"]}
    _write_json(os.path.join(ARTIFACT_DIR, "p0_gate.json"), gate)
    print(json.dumps({"verdict": gate["verdict"],
                      "blocker": gate.get("blocker"),
                      "census": census.get("verdict"),
                      "instants": census.get("instant_count"),
                      "funding": funding["status"],
                      "tests": "PASS" if tests_ok else "FAIL"},
                     indent=1))
    return 0 if gate["verdict"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
