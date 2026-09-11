"""CRYPTO-NG2 P0 census runner (lane p0, task crypto-ng2-p0-census).

Sections:
  1. s4_repin      -- re-verify the frozen S4 plane through the INHERITED
                      ng1 adapter (``research.assets.crypto_ng1.
                      plane_adapter.CryptoNG1Plane``, import-only reuse):
                      all 5 frozen digests must satisfy
                      address == frozen == measured sha256;
  2. panel_bounds  -- manifest-verified frozen query per panel; bounds and
                      row counts must reconcile with the panel manifest
                      window;
  3. shadow_parity -- plane read vs direct CADS-object read (2 panels);
  4. bls_census    -- CPI/NFP instants from official BLS schedule pages
                      (browser-class plan; curl-class measured; honest
                      BLOCKED_PER_SOURCE when denied -- zero fabrication);
  5. funding_probe -- keyless fapi fundingRate availability (non-blocking);
  6. series_name_canaries -- nonexistent series must be refused (P-7);
  7. tests         -- targeted pytest file (tests/test_crypto_ng2_p0.py).

Writes research/control/crypto_ng2_run/{p0_bls_census.json,
p0_funding_probe.json,p0_gate.json}.  Exit 0 iff every hard section is
consistent; a BLOCKED_PER_SOURCE census is an honest recorded outcome
(gate verdict PASS_WITH_BLS_BLOCKED: lane A4 dies at P0 per plan
section 2, lane A5 continues), never a fabricated PASS.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _REPO_ROOT)

from research.assets.crypto_ng1.plane_adapter import (  # noqa: E402
    CryptoNG1Plane, FROZEN_S4_ENTRIES)
from research.assets.crypto_ng2 import bls_census  # noqa: E402

WORKTREE = _REPO_ROOT
OUT_DIR = os.path.join(WORKTREE, "research", "control", "crypto_ng2_run")
WINDOW_START, WINDOW_END = date(2025, 8, 22), date(2026, 8, 21)
PANEL_ENTRIES = [
    "staging_v17/panel_BTCUSDT_h1.csv",
    "staging_v17/panel_ETHUSDT_h1.csv",
    "staging_v17/panel_SOLUSDT_h1.csv",
]
TEST_CMD = [sys.executable, "-m", "pytest", "tests/test_crypto_ng2_p0.py",
            "-q"]

#: manual pre-run curl probes of the official BLS pages (disclosed in the
#: gate method notes; timestamps were not captured, so none are claimed)
PRE_RUN_MANUAL_PROBES = [
    {"url": "https://www.bls.gov/schedule/news_release/cpi.htm",
     "http_status": 403, "title": "Access Denied"},
    {"url": "https://www.bls.gov/schedule/news_release/empsit.htm",
     "http_status": 403, "title": "Access Denied"},
    {"url": "https://www.bls.gov/bls/news-release/cpi.htm",
     "http_status": 403, "title": "Access Denied"},
]

_SECTION_CMD = f"{sys.executable} research/control/crypto_ng2_run/run_p0_census.py (section {{}})"


def _write_json(name: str, payload: dict) -> str:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=False)
        fh.write("\n")
    return path


def section_s4_repin(plane: CryptoNG1Plane) -> dict:
    observed, entries = {}, {}
    for entry, meta in FROZEN_S4_ENTRIES.items():
        res = plane.consume(entry)
        ok = (res["cads_address"] == meta["sha256"]
              and res["sha256_measured"] == meta["sha256"])
        observed[entry] = (f"address==frozen==measured "
                           f"{res['sha256_measured']}")
        entries[entry] = {
            "series": meta["series"],
            "frozen_sha256": meta["sha256"],
            "command": _SECTION_CMD.format(f"s4_repin:{entry}"),
            "exit_code": 0 if ok else 1,
            "pin_series": res["series_pinned"],
            "cads_address": res["cads_address"],
            "measured_sha256": res["sha256_measured"],
            "bytes": res["bytes"],
            "authority_verdict": res["verdict"],
            "observed": (f"address==frozen==measured "
                         f"{res['sha256_measured']}"),
            "margin": "exact digest match" if ok else "DIGEST MISMATCH",
            "verdict": "PASS" if ok else "FAIL",
        }
        if not ok:
            raise SystemExit(f"s4_repin FAILED for {entry}: {entries[entry]}")
    return {
        "command": _SECTION_CMD.format("s4_repin"),
        "exit_code": 0,
        "observed": observed,
        "margin": f"all {len(FROZEN_S4_ENTRIES)} frozen digests exact "
                  "(inherited ng1 adapter, import-only reuse)",
        "verdict": "PASS",
        "entries": entries,
        "evidence_path": "research/control/crypto_ng2_run/p0_gate.json",
    }


def section_panel_bounds(plane: CryptoNG1Plane) -> dict:
    manifest_res = plane.consume("staging_v17/panel_manifest.json")
    manifest = json.loads(manifest_res["data"])
    win = manifest["window"]
    if [win[0], win[1]] != [WINDOW_START.isoformat(),
                            WINDOW_END.isoformat()]:
        raise SystemExit(f"manifest window {win} != cycle window")
    hours_expected = ((date.fromisoformat(win[1]) - date.fromisoformat(win[0]))
                      .days + 1) * 24
    entries, observed = {}, {}
    for entry in PANEL_ENTRIES:
        out = plane.query_panel_bounds(entry)
        sym, n_rows, first, last = out["rows"][0]
        ok = (out["query_verdict"] == "SUCCESS" and n_rows == hours_expected
              and first[:10] == win[0] and last[:10] == win[1])
        observed[entry] = [sym, n_rows, first, last]
        entries[entry] = {
            "command": _SECTION_CMD.format(f"panel_bounds:{entry}"),
            "exit_code": 0 if ok else 1,
            "query_verdict": out["query_verdict"],
            "query_identity": out["identity"],
            "rows": out["rows"],
            "result_digest": out["result_digest"],
            "observed": out["rows"],
            "margin": (f"SUCCESS; {n_rows} rows == {hours_expected} window "
                       "hours; bounds == manifest window" if ok
                       else "BOUNDS/COUNT MISMATCH"),
            "verdict": "PASS" if ok else "FAIL",
        }
        if not ok:
            raise SystemExit(f"panel_bounds FAILED for {entry}: {entries[entry]}")
    return {
        "command": _SECTION_CMD.format("panel_bounds"),
        "exit_code": 0,
        "observed": {"manifest_window": win, "panels": observed},
        "margin": "manifest window vs measured plane bounds + row counts",
        "verdict": "PASS",
        "entries": entries,
        "evidence_path": "research/control/crypto_ng2_run/p0_gate.json",
    }


def section_shadow_parity(plane: CryptoNG1Plane) -> dict:
    entries, observed = {}, {}
    for entry in PANEL_ENTRIES[:1] + PANEL_ENTRIES[2:]:   # BTC + SOL (ng1 shape)
        p = plane.shadow_parity(entry)
        ok = p["identical"]
        observed[entry] = (f"plane {p['plane_sha256']} vs direct "
                           f"{p['direct_sha256']}")
        entries[entry] = {
            "command": _SECTION_CMD.format(f"shadow_parity:{entry}"),
            "exit_code": 0 if ok else 1,
            "plane_sha256": p["plane_sha256"],
            "direct_sha256": p["direct_sha256"],
            "bytes": p["bytes"],
            "observed": observed[entry],
            "margin": "0 (identical)" if ok else "SHADOW MISMATCH",
            "verdict": "PASS" if ok else "FAIL",
        }
        if not ok:
            raise SystemExit(f"shadow_parity FAILED for {entry}")
    return {
        "command": _SECTION_CMD.format("shadow_parity"),
        "exit_code": 0,
        "observed": observed,
        "margin": "sha256(plane read) == sha256(direct CADS-object read)",
        "verdict": "PASS",
        "entries": entries,
        "evidence_path": "research/control/crypto_ng2_run/p0_gate.json",
    }


def section_series_canaries(plane: CryptoNG1Plane) -> dict:
    probes = [
        {"series": "S9:bls-cpi-instants-fabricated",
         "expected": "REFUSED (not GRANTED)"},
        {"series": "S4:binance-funding-settlements",
         "expected": "REFUSED (not GRANTED)"},
    ]
    observed = []
    for probe in probes:
        v = plane.verdict(probe["series"])
        refused = v != "GRANTED"
        observed.append({**probe, "observed": f"verdict={v!r}",
                         "refused": refused,
                         "verdict": "PASS" if refused else "FAIL"})
        if not refused:
            raise SystemExit(f"series canary FAILED (granted!): {probe}")
    return {
        "command": _SECTION_CMD.format("series_name_canaries"),
        "exit_code": 0,
        "observed": observed,
        "margin": "nonexistent series refused (P-7)",
        "verdict": "PASS",
        "evidence_path": "research/control/crypto_ng2_run/p0_gate.json",
    }


def section_tests() -> dict:
    proc = subprocess.run(TEST_CMD, cwd=WORKTREE, capture_output=True,
                          text=True, timeout=600)
    tail = [ln for ln in (proc.stdout + proc.stderr).splitlines() if ln][-3:]
    ok = proc.returncode == 0
    return {
        "command": f"cd {WORKTREE} && {' '.join(TEST_CMD)}",
        "exit_code": proc.returncode,
        "observed": tail,
        "margin": "pytest exit code (targeted file only)",
        "verdict": "PASS" if ok else "FAIL",
    }


def main() -> int:
    measured_utc = datetime.now(timezone.utc).isoformat()
    plane = CryptoNG1Plane()

    s4 = section_s4_repin(plane)
    bounds = section_panel_bounds(plane)
    parity = section_shadow_parity(plane)

    census = bls_census.run_bls_census(
        WINDOW_START, WINDOW_END, verdict_fn=plane.verdict)
    census_path = _write_json("p0_bls_census.json", census)

    funding = bls_census.funding_probe(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    funding_path = _write_json("p0_funding_probe.json", funding)

    canaries = section_series_canaries(plane)
    tests = section_tests()

    census_section = {
        "command": _SECTION_CMD.format("bls_census"),
        "exit_code": 0,
        "observed": {
            "verdict": census["verdict"],
            "instant_count": census["instant_count"],
            "sources": {k: v["status"] for k, v in census["sources"].items()},
            "method_chain": {k: v["status"]
                             for k, v in census["method_chain"].items()},
        },
        "margin": "instants only from official schedule rows; blocked "
                  "sources fabricate nothing (plan section 2: A4 dies at "
                  "P0, A5 may continue)",
        "verdict": ("PASS" if census["verdict"] == "PASS"
                    else "PASS_WITH_BLS_BLOCKED"
                    if census["verdict"] == "BLOCKED_PER_SOURCE"
                    else "FAIL"),
        "evidence_path": "research/control/crypto_ng2_run/p0_bls_census.json",
    }
    funding_section = {
        "command": _SECTION_CMD.format("funding_probe"),
        "exit_code": 0,
        "observed": {
            "status": funding["status"],
            "symbols_ok": [p["symbol"] for p in funding["probes"] if p["ok"]],
        },
        "margin": "optional; BLOCKED_NOT_CONSUMED allowed by design",
        "verdict": "NON_BLOCKING",
        "evidence_path": "research/control/crypto_ng2_run/p0_funding_probe.json",
    }

    hard_ok = all(s["verdict"] in ("PASS", "PASS_WITH_BLS_BLOCKED",
                                   "NON_BLOCKING")
                  for s in (s4, bounds, parity, census_section, canaries,
                            tests)) and tests["exit_code"] == 0

    if not hard_ok:
        gate_verdict = "BLOCKED_DATA"
    elif census["verdict"] == "PASS":
        gate_verdict = "PASS"
    elif census["verdict"] == "BLOCKED_PER_SOURCE":
        gate_verdict = "PASS_WITH_BLS_BLOCKED"
    else:
        gate_verdict = "FAIL"

    head_sha = subprocess.run(["git", "-C", WORKTREE, "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    branch = subprocess.run(
        ["git", "-C", WORKTREE, "branch", "--show-current"],
        capture_output=True, text=True, check=True).stdout.strip()

    gate = {
        "schema": "crypto_ng2_run/p0_gate@1",
        "task_id": "crypto-ng2-p0-census",
        "cycle_id": "CRYPTO-NG2",
        "lane": "p0",
        "measured_utc": measured_utc,
        "worktree": WORKTREE,
        "cads_store_root": plane.store_root,
        "cads_store_mode": "READ-ONLY",
        "window": {"start": WINDOW_START.isoformat(),
                   "end": WINDOW_END.isoformat()},
        "sections": {
            "s4_repin": s4,
            "panel_bounds": bounds,
            "shadow_parity": parity,
            "bls_census": census_section,
            "funding_probe": funding_section,
            "series_name_canaries": canaries,
            "tests": tests,
        },
        "method_notes": {
            "s4_plane": "inherited ng1 plane_adapter consumed by import "
                        "only (research/assets/crypto_ng1/plane_adapter.py "
                        "unmodified)",
            "bls_retrieval": "browser-class chain per plan section 3; "
                             "webfetch_tool and browser_use_skill NOT_RUN "
                             "in-lane (see census method_chain reasons); "
                             "curl-class measured and denied 403",
            "pre_run_manual_probes": PRE_RUN_MANUAL_PROBES,
        },
        "verdict_basis": [
            f"s4_repin={s4['verdict']}",
            f"panel_bounds={bounds['verdict']}",
            f"shadow_parity={parity['verdict']}",
            f"bls_census={census['verdict']}",
            f"funding_probe={funding['status']} (optional)",
            f"series_name_canaries={canaries['verdict']}",
            f"tests={tests['verdict']} (exit {tests['exit_code']})",
        ],
        "git": {"head_sha": head_sha, "branch": branch},
        "verdict": gate_verdict,
        "census": {"path": "research/control/crypto_ng2_run/p0_bls_census.json",
                   "verdict": census["verdict"],
                   "instant_count": census["instant_count"]},
        "funding": {"path": "research/control/crypto_ng2_run/"
                            "p0_funding_probe.json",
                    "status": funding["status"]},
    }
    _write_json("p0_gate.json", gate)

    print(f"gate verdict: {gate_verdict}")
    print(f"census: {census['verdict']} ({census['instant_count']} instants) "
          f"-> {census_path}")
    print(f"funding: {funding['status']} -> {funding_path}")
    for row in tests["observed"]:
        print(f"tests: {row}")
    return 0 if hard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
