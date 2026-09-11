"""CRYPTO-NG2 P0b fold runner (lane p0b, task crypto-ng2-p0b-fold).

Folds the controller-channel raw BLS schedules
(``research/control/crypto_ng2_run/controller_fetch/bls_schedules_raw.json``,
committed verbatim by the A1 lead via main-agent WebFetch) through the
lane's fail-closed parser (``research.assets.crypto_ng2.bls_census.
fold_controller_raw``) into ``p0_calendar_census_ng2.json``:

- every instant {series CPI|NFP, ref_month, release_date, instant_utc at
  08:30 America/New_York DST-correct, source schedule|archive, file
  evidence when the archive carries it};
- only instants inside the panel window 2025-08-22T00..2026-08-21T23 UTC;
- non-published months (Oct-2025 CPI + empsit "2025 lapse") recorded
  excluded_with_reason, never fabricated;
- schedule/archive rows sharing a ref_month must agree on the date
  (mismatch -> fail-closed record, both refused);
- the ng2-p0 canary set re-run on the fold path (2 fabricated days +
  nonexistent series: fold-registry refusal + inherited plane authority
  probe when the read-only plane is available);
- updates ``p0_gate.json`` with a ``p0b`` section (census verdict, lane
  A4 REOPENED) while keeping every p0 section untouched;
- runs the targeted test file ``tests/test_crypto_ng2_p0.py``.

Exit 0 iff the fold census PASSes and the targeted tests PASS.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _REPO_ROOT)

from research.assets.crypto_ng1.plane_adapter import (  # noqa: E402
    CryptoNG1Plane, PlaneDataBlocked)
from research.assets.crypto_ng2 import bls_census  # noqa: E402

WORKTREE = _REPO_ROOT
OUT_DIR = os.path.join(WORKTREE, "research", "control", "crypto_ng2_run")
RAW_PATH = os.path.join(OUT_DIR, "controller_fetch", "bls_schedules_raw.json")
CENSUS_NAME = "p0_calendar_census_ng2.json"
GATE_NAME = "p0_gate.json"
WINDOW_START, WINDOW_END = date(2025, 8, 22), date(2026, 8, 21)
TEST_CMD = [sys.executable, "-m", "pytest", "tests/test_crypto_ng2_p0.py",
            "-q"]

#: sections owned by the p0 run that must survive this update untouched
_OLD_P0_SECTIONS = ("s4_repin", "panel_bounds", "shadow_parity", "bls_census",
                    "funding_probe", "series_name_canaries", "tests")

#: dispatch packet's independent expectation (approximate, for
#: reconciliation only -- measurement is always the parser's, never this)
_EXPECTED_APPROX = {"CPI": 11, "NFP": 13}


def _write_json(name: str, payload: dict) -> str:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=False)
        fh.write("\n")
    return path


def _load_plane():
    """Read-only inherited plane for the authority series canary (the same
    probe the p0 run used).  Unavailability is recorded honestly and never
    blocks: the fold-registry refusal canary covers the fold path."""
    try:
        plane = CryptoNG1Plane()
        return plane.verdict, {"status": "MEASURED",
                               "store_root": plane.store_root,
                               "note": "read-only inherited ng1 plane "
                                       "(import-only reuse)"}
    except PlaneDataBlocked as exc:
        return None, {"status": "NOT_RUN",
                      "reason": f"plane unavailable: {exc}"}


def _run_tests() -> dict:
    proc = subprocess.run(TEST_CMD, cwd=WORKTREE, capture_output=True,
                          text=True, timeout=600)
    tail = [ln for ln in (proc.stdout + proc.stderr).splitlines() if ln][-3:]
    return {
        "command": f"cd {WORKTREE} && {' '.join(TEST_CMD)}",
        "exit_code": proc.returncode,
        "observed": tail,
        "margin": "pytest exit code (targeted file only)",
        "verdict": "PASS" if proc.returncode == 0 else "FAIL",
    }


def main() -> int:
    measured_utc = datetime.now(timezone.utc).isoformat()

    with open(RAW_PATH, "rb") as fh:
        raw_bytes = fh.read()
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    raw = json.loads(raw_bytes.decode("utf-8"))
    if raw.get("schema") != bls_census.CONTROLLER_RAW_SCHEMA:
        raise SystemExit(f"raw input schema {raw.get('schema')!r} != "
                         f"{bls_census.CONTROLLER_RAW_SCHEMA!r}: refusing")

    verdict_fn, plane_meta = _load_plane()
    census = bls_census.fold_controller_raw(
        raw, WINDOW_START, WINDOW_END, verdict_fn=verdict_fn,
        now_utc=measured_utc,
        input_meta={
            "path": "research/control/crypto_ng2_run/controller_fetch/"
                    "bls_schedules_raw.json",
            "sha256": raw_sha256,
            "bytes": len(raw_bytes),
        })
    if verdict_fn is None:
        census["canaries"]["authority_series_probe"]["plane_meta"] = plane_meta
    census_path = _write_json(CENSUS_NAME, census)

    tests = _run_tests()

    head_sha = subprocess.run(["git", "-C", WORKTREE, "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    branch = subprocess.run(["git", "-C", WORKTREE, "branch",
                             "--show-current"], capture_output=True, text=True,
                            check=True).stdout.strip()

    counts = census["counts"]
    excluded = [f"{e['series']} {e['ref_month']}: {e['reason']}"
                for e in census["excluded_with_reason"]]
    recon = {}
    for series, approx in _EXPECTED_APPROX.items():
        entry = {"dispatch_expectation_approx": approx,
                 "measured": counts[series]}
        if counts[series] == approx:
            entry["match"] = True
        else:
            entry["match"] = False
            entry["note"] = (
                "measured by the parser from the raw verbatim; the dispatch "
                "expectation is approximate and NO row was fabricated to "
                "close any gap")
        recon[series] = entry
    recon["NFP"]["gap_note"] = (
        "the two candidate extras named by the dispatch (a release inside "
        "the 2025-08 window-start span; a late-Sept 2025 release) do not "
        "exist in the controller raw verbatim: the empsit archive starts at "
        "ref 2025-08 released 2025-09-05 (counted) and the Sept-2025 late "
        "release was 2025-11-20 (counted)")

    p0b_ok = census["verdict"] == "PASS" and tests["exit_code"] == 0
    p0b_section = {
        "task_id": "crypto-ng2-p0b-fold",
        "lane": "p0b",
        "command": f"{sys.executable} research/control/crypto_ng2_run/"
                   "run_p0b_fold.py",
        "exit_code": 0 if p0b_ok else 1,
        "measured_utc": measured_utc,
        "measured_at_head_sha": head_sha,
        "observed": {
            "verdict": census["verdict"],
            "instant_count": census["instant_count"],
            "counts": counts,
            "excluded_months": excluded,
            "outside_window_rows": len(census["outside_window_rows"]),
            "fail_closed_rows": len(census["fail_closed"]),
            "cross_validation": {
                k: {"matched": len(v["matched"]),
                    "mismatched": len(v["mismatched"])}
                for k, v in census["cross_validation"].items()},
            "canaries": {
                "fabricated_days": [f["verdict"] for f in
                                    census["canaries"]["fabricated_days"]],
                "fold_registry_series_probe":
                    census["canaries"]["fold_registry_series_probe"]["verdict"],
                "authority_series_probe":
                    census["canaries"]["authority_series_probe"]["verdict"]},
            "method_chain": {k: v["status"] for k, v in
                             census["method_chain"].items()},
        },
        "expectation_reconciliation": recon,
        "plane_authority_canary": plane_meta,
        "lane_a4_status": "REOPENED" if p0b_ok else census["verdict"],
        "margin": "every instant re-derived in-lane from the raw verbatim "
                  "rows (DST-correct 8:30 America/New_York -> UTC); "
                  "non-published months recorded excluded_with_reason; "
                  "schedule/archive date agreement enforced; zero "
                  "fabrication",
        "verdict": "PASS" if p0b_ok else "FAIL",
        "evidence_path": f"research/control/crypto_ng2_run/{CENSUS_NAME}",
        "raw_input": {"path": "research/control/crypto_ng2_run/"
                              "controller_fetch/bls_schedules_raw.json",
                      "sha256": raw_sha256},
        "tests": tests,
    }

    # ---- gate update: add p0b, keep every p0 section untouched --------- #
    gate_path = os.path.join(OUT_DIR, GATE_NAME)
    with open(gate_path, encoding="utf-8") as fh:
        gate = json.load(fh)
    if gate.get("schema") != "crypto_ng2_run/p0_gate@1":
        raise SystemExit(f"unexpected gate schema {gate.get('schema')!r}")
    missing = [s for s in _OLD_P0_SECTIONS if s not in gate.get("sections", {})]
    if missing:
        raise SystemExit(f"gate lost p0 sections {missing}: refusing")
    gate["sections"]["p0b"] = p0b_section
    gate["verdict_basis"] = list(gate.get("verdict_basis", [])) + [
        f"p0b_census_fold={census['verdict']} "
        f"({census['instant_count']} instants: "
        f"CPI {counts['CPI']} + NFP {counts['NFP']}; lane A4 REOPENED "
        "via controller-fetch + lane-parser-validated chain)"]
    gate["method_notes"]["p0b_fold"] = (
        "controller-channel raw (A1 lead main-agent WebFetch, committed "
        "verbatim) folded through the lane fail-closed parser "
        "(bls_census.fold_controller_raw); instants re-derived, not copied; "
        "non-published Oct-2025 months excluded_with_reason; p0 sections "
        "above remain the honest record of the p0 run (curl-class "
        "BLOCKED_PER_SOURCE at that time)")
    gate["census_fold"] = {
        "path": f"research/control/crypto_ng2_run/{CENSUS_NAME}",
        "verdict": census["verdict"],
        "instant_count": census["instant_count"],
        "counts": counts,
        "raw_input_sha256": raw_sha256,
        "lane_a4_status": "REOPENED" if p0b_ok else census["verdict"],
    }
    # the BLS-blocked condition recorded at p0 is superseded by the p0b
    # fold census (controller channel + lane parser validation)
    gate["verdict"] = "PASS" if p0b_ok else "FAIL"
    _write_json(GATE_NAME, gate)

    print(f"fold census: {census['verdict']} "
          f"({census['instant_count']} instants: "
          f"CPI {counts['CPI']}, NFP {counts['NFP']}) -> {census_path}")
    for row in excluded:
        print(f"excluded: {row}")
    print(f"cross-validation: "
          + json.dumps(p0b_section["observed"]["cross_validation"]))
    for row in tests["observed"]:
        print(f"tests: {row}")
    print(f"gate: sections.p0b verdict {p0b_section['verdict']}, "
          f"gate verdict {gate['verdict']}")
    return 0 if p0b_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
