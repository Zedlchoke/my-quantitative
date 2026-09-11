#!/usr/bin/env python
"""STOCKS-NG1 P0 gate driver (lane p0, data authority + adoption).

Runs, in order, and writes evidence under
research/control/stocks_ng1_run/ (this cycle's worktree):

  1. authority + adoption: consume_via_plane for the three frozen S1
     series (AuthorityRegistry GRANTED -> CADS resolve verify-on-read
     -> manifest-verified query);
  2. S1 re-pin verification: manifest digest 5d351623... , stream
     digest 6ac2cd5b..., full re-hash of every pinned substrate file
     (345,150 XML + 4,336 eodhd div/splits + 410 submissions) + the
     dispatch-mandated stratified 30-file XML sample (recorded even
     though full coverage supersedes it);
  3. shadow parity pilot: plane-read vs V13-direct-read digest equality
     on 3 deterministic entity-windows from the stream (+ full-object
     digest equality);
  4. OBSERVABLE CENSUS A (10b5-1 declared-plan flag) and CENSUS B
     (amendment/revision structure) with frozen floors.

Verdict: PASS | BLOCKED_DATA, fail-closed.  Exit code 0 iff PASS.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

_REPO = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
sys.path.insert(0, _REPO)

from research.assets.stocks_ng1.plane_adapter import (  # noqa: E402
    ConsumptionRefused, FLAG_TAG_10B5_1, FLAG_TAG_EVIDENCE,
    PIN_FORM4_STREAM_SHA256, PIN_SUBSTRATE_MANIFEST_SHA256,
    StocksNG1Plane,
)
from research.assets.stocks_ng1.censuses import (  # noqa: E402
    amendment_absence_crosscheck, census_a_floor_evaluation,
    census_b_floor_evaluation, flag_transaction_count, scan_substrate,
    verify_aux_sections,
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "stocks_ng1_run/p0_gate@1"

COMMAND = (f"cd {_REPO} && /Users/hoangminhlong/my-quantitative/.venv/bin/"
           f"python research/control/stocks_ng1_run/p0_gate_run.py")


def _dump(name: str, obj: dict) -> str:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    t0 = time.time()
    gate: dict = {
        "schema": SCHEMA, "gate": "P0", "cycle": "STOCKS-NG1",
        "lane": "p0", "measured_utc": _now(),
        "command": COMMAND,
        "worktree": _REPO,
        "dispatch_base_sha": "26accd83aa1eca4a70333995c87f5ce88939761c",
        "steps": [], "blocking": [],
    }

    def step(name: str, ok: bool, detail: dict) -> bool:
        entry = {"step": name, "ok": bool(ok)}
        entry.update(detail)
        gate["steps"].append(entry)
        if not ok:
            gate["blocking"].append(name)
        return ok

    # ---------------- 1. authority + plane adoption ------------------- #
    plane = StocksNG1Plane()
    adoption = {"series_verdicts": {}, "consumed": {}}
    try:
        for sid in ("S1:form4-xml-substrate", "S1:form4-stream",
                    "S1:eodhd-corp-actions"):
            adoption["series_verdicts"][sid] = plane.authority_verdict(sid)
        granted_ok = all(
            v == "GRANTED" for v in adoption["series_verdicts"].values())
        # refusal path: an ungranted series must refuse (fail-closed)
        try:
            plane.consume_via_plane("S1:not-a-series")
            refused = False
        except ConsumptionRefused:
            refused = True
        adoption["refusal_path_proven"] = refused
        adoption["refusal_probe_series"] = "S1:not-a-series"

        manifest_out = plane.plane_manifest()
        stream_out = plane.plane_stream()
        adoption["consumed"]["substrate_manifest"] = {
            "resolved_address": manifest_out["resolved_address"],
            "bytes": manifest_out["bytes"], "sha256": manifest_out["sha256"]}
        adoption["consumed"]["form4_stream"] = {
            "resolved_address": stream_out["resolved_address"],
            "bytes": stream_out["bytes"], "sha256": stream_out["sha256"]}
        # eodhd-corp-actions: pinned by the substrate manifest sections
        # eodhd_div+eodhd_splits (no separate CADS object); consumption
        # proof = manifest-verified query below (recorded honestly).
        ok = (granted_ok and refused
              and manifest_out["sha256"] == PIN_SUBSTRATE_MANIFEST_SHA256
              and stream_out["sha256"] == PIN_FORM4_STREAM_SHA256)
        step("authority_plane_adoption", ok, {"detail": adoption})
        manifest = manifest_out["manifest"]
    except Exception as exc:  # fail-closed: no partial credit
        step("authority_plane_adoption", False,
             {"detail": adoption, "error": repr(exc)})
        gate["verdict"] = "BLOCKED_DATA"
        gate["verdict_reason"] = f"adoption failed: {exc!r}"
        _finish(gate, t0)
        return 1

    # ---------------- 2. S1 re-pin verification ----------------------- #
    repin = {"pinned_manifest_sha256": PIN_SUBSTRATE_MANIFEST_SHA256,
             "pinned_stream_sha256": PIN_FORM4_STREAM_SHA256,
             "inherited_pin_root": plane.substrate_root,
             "direct_paths": {
                 "manifest": (
                     "/Users/hoangminhlong/my-quantitative/.worktrees/"
                     "stocks-free-v13/integration/research/control/"
                     "stocks_free_v13_run/substrate_manifest.json"),
                 "stream": plane.direct_stream_path}}
    try:
        v13_manifest_path = (
            "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13"
            "/integration/research/control/stocks_free_v13_run/"
            "substrate_manifest.json")
        dm_sha = hashlib.sha256(
            open(v13_manifest_path, "rb").read()).hexdigest()
        repin["direct_manifest_sha256"] = dm_sha
        with open(plane.direct_stream_path, "rb") as fh:
            ds_sha = hashlib.sha256(fh.read()).hexdigest()
        repin["direct_stream_sha256"] = ds_sha
        direct_ok = (dm_sha == PIN_SUBSTRATE_MANIFEST_SHA256
                     and ds_sha == PIN_FORM4_STREAM_SHA256)
        step("repin_direct_digests", direct_ok,
             {"detail": {"direct_manifest_sha256": dm_sha,
                         "direct_stream_sha256": ds_sha}})
    except Exception as exc:
        step("repin_direct_digests", False, {"error": repr(exc)})
        direct_ok = False

    # stream acceptance index (plane-read bytes, reused for parity)
    plane_rows = plane.load_stream_rows("plane")
    from research.assets.stocks_ng1.plane_adapter import (
        build_stream_acceptance_index)
    stream_index = build_stream_acceptance_index(plane_rows)
    repin["stream_unique_accessions"] = len(stream_index)
    repin["stream_rows"] = len(plane_rows)

    try:
        full = scan_substrate(manifest, plane.substrate_root, stream_index)
        aux = verify_aux_sections(manifest, plane.substrate_root)
        repin["form4_xml_docs"] = {k: v for k, v in full.items()
                                   if k not in ("census_a", "census_b")}
        repin["aux_sections"] = aux
        eodhd_files = (aux["eodhd_div"]["files_total"]
                       + aux["eodhd_splits"]["files_total"])
        repin["eodhd_div_plus_splits_files"] = eodhd_files
        full_ok = (full["status"] == "OK"
                   and all(s["status"] == "OK" for s in aux.values())
                   and eodhd_files == 4336
                   and full["files_ok"] == 345150)
        # dispatch-mandated stratified 30-file sample (superseded by full
        # coverage, recorded for method transparency)
        sample = _stratified_30(manifest, plane.substrate_root)
        repin["stratified_30_sample"] = sample
        sample_ok = all(r["status"] == "OK" for r in sample["rows"])
        step("repin_full_substrate", full_ok and sample_ok,
             {"method": ("FULL re-hash of every pinned file (no sampling "
                         "fallback needed; single pass ~2.8GB) + stratified "
                         "30-file XML sample recorded"),
              "files": {"form4_xml": full["files_total"],
                        "eodhd": eodhd_files, "submissions": 410}})
    except Exception as exc:
        step("repin_full_substrate", False, {"error": repr(exc)})
        full = None

    # ---------------- 3. shadow parity pilot -------------------------- #
    try:
        parity = _shadow_parity(plane, plane_rows)
        step("shadow_parity_pilot_3_windows",
             parity["all_equal"] and parity["full_object_equal"],
             {"detail": parity})
    except Exception as exc:
        parity = {"error": repr(exc)}
        step("shadow_parity_pilot_3_windows", False, {"detail": parity})

    # ---------------- 4. observable censuses -------------------------- #
    if full is None or full.get("status") != "OK":
        step("censuses_measured", False,
             {"error": "censuses invalid without an OK full-substrate "
                       "scan (fail-closed, no counts from a drifted or "
                       "missing substrate)"})
        gate["census_floors"] = {"error": "NOT_RUN: substrate scan not OK"}
        _finish(gate, t0)
        return 1
    try:
        ca = full["census_a"]
        cb = full["census_b"]
        declared = set(ca["declared_docs_post_2023"])
        tx = flag_transaction_count(plane_rows, declared)
        ca_floor = census_a_floor_evaluation(ca, tx["count"])
        cb_floor = census_b_floor_evaluation(cb)
        census_a = {"schema": "stocks_ng1_run/p0_census_a@1",
                    "measured_utc": _now(), "tag": FLAG_TAG_10B5_1,
                    "tag_evidence": FLAG_TAG_EVIDENCE,
                    "census": ca,
                    "flagged_transactions": tx,
                    "floor_evaluation": ca_floor,
                    "canary": {
                        "rule": "pre-2023 docs must have zero declared "
                                "10b5-1 flags (tag adopted post-2023)",
                        "declared_pre_2023":
                            ca["canary_pre_2023_declared"],
                        "anomaly_if_positive": True,
                        "finding": ("NO ANOMALY (count=0)"
                                    if ca["canary_pre_2023_declared"] == 0
                                    else "POSITIVE ANOMALY (dead-name "
                                         "canary tripped) -- recorded as "
                                         "finding, data NOT edited")}}
        census_b = {"schema": "stocks_ng1_run/p0_census_b@1",
                    "measured_utc": _now(), "census": cb,
                    "floor_evaluation": cb_floor}
        if cb["amendment_docs"] == 0:
            census_b["absence_crosscheck"] = amendment_absence_crosscheck(
                manifest, plane.substrate_root)
        ca_path = _dump("p0_census_a_10b5.json", census_a)
        cb_path = _dump("p0_census_b_amendments.json", census_b)
        repin_path = _dump("p0_substrate_repverify.json", repin)
        parity_path = _dump("p0_shadow_parity.json", parity)
        gate["evidence_paths"] = {
            "census_a": ca_path, "census_b": cb_path,
            "repin": repin_path, "parity": parity_path}
        step("censuses_measured", True,
             {"census_a_flagged_tx": tx["count"],
              "census_b_amendments": cb["amendment_docs"]})
        floors_not_met = []
        if not ca_floor["met"]:
            floors_not_met.append(
                "CENSUS_A floor unmet -> lane A4 dies at P2")
        if not cb_floor["met"]:
            floors_not_met.append(
                "CENSUS_B floor unmet -> lane A5 dies at P2")
        gate["census_floors"] = {"census_a": ca_floor,
                                 "census_b": cb_floor,
                                 "floors_not_met": floors_not_met}
    except Exception as exc:
        step("censuses_measured", False, {"error": repr(exc)})
        gate["census_floors"] = {"error": repr(exc)}

    _finish(gate, t0)
    return 0 if gate["verdict"] == "PASS" else 1


def _stratified_30(manifest: dict, substrate_root: str) -> dict:
    files = manifest["sections"]["form4_xml_docs"]["files"]
    keys = sorted(files)
    step = max(1, len(keys) // 30)
    picked = keys[::step][:30]
    rows = []
    for k in picked:
        # keys are staging-root relative ("form4_xml/...")
        path = os.path.join(substrate_root, k)
        if not os.path.isfile(path):
            rows.append({"key": k, "status": "MISSING"})
            continue
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        rows.append({"key": k, "status": "OK" if sha == files[k] else "DRIFT",
                     "measured": sha, "pinned": files[k]})
    return {"method": f"every {step}-th key of the sorted manifest "
                      "(deterministic stratified sample of 30)",
            "rows": rows, "ok": sum(1 for r in rows if r["status"] == "OK")}


def _shadow_parity(plane: StocksNG1Plane, plane_rows: list[dict]) -> dict:
    """3 deterministic entity-windows: plane-read vs direct-read digest
    equality, plus full-object digest equality."""
    window = ("2023-01-01", "2023-12-31")
    cand = {}
    for r in plane_rows:
        acc = r.get("acceptance") or ""
        if window[0] <= acc <= window[1] + "T23:59:59Z":
            cand.setdefault(r["cik"], 0)
            cand[r["cik"]] += 1
    qualified = sorted(c for c, n in cand.items() if n >= 20)
    if len(qualified) < 3:
        return {"all_equal": False,
                "reason": "fewer than 3 entities with >=20 rows in window"}
    picks = [qualified[0], qualified[len(qualified) // 2], qualified[-1]]
    direct_rows = plane.load_stream_rows("direct")
    samples = []
    for cik in picks:
        w_plane = StocksNG1Plane.stream_entity_window(
            plane_rows, cik, window[0], window[1])
        w_direct = StocksNG1Plane.stream_entity_window(
            direct_rows, cik, window[0], window[1])
        dp = StocksNG1Plane.canonical_rows_digest(w_plane)
        dd = StocksNG1Plane.canonical_rows_digest(w_direct)
        samples.append({"cik": cik, "window": list(window),
                        "rows_plane": len(w_plane),
                        "rows_direct": len(w_direct),
                        "digest_plane": dp, "digest_direct": dd,
                        "equal": dp == dd and len(w_plane) == len(w_direct)})
    direct_full: str
    with open(plane.direct_stream_path, "rb") as fh:
        direct_full = hashlib.sha256(fh.read()).hexdigest()
    return {
        "method": ("3 deterministic entity-windows (first/middle/last of "
                   "CIKs with >=20 rows in 2023) sliced identically from "
                   "plane-read (CADS resolve) and direct-read (inherited "
                   "pin file) stream bytes; canonical sorted-row digests"),
        "selection_rule": "sorted CIKs with >=20 rows in 2023 window; "
                          "indices 0, mid, last",
        "window": list(window),
        "samples": samples,
        "full_object_digest_plane": PIN_FORM4_STREAM_SHA256,
        "full_object_digest_direct": direct_full,
        "full_object_equal": direct_full == PIN_FORM4_STREAM_SHA256,
        "all_equal": all(s["equal"] for s in samples),
    }


def _finish(gate: dict, t0: float) -> None:
    gate["seconds"] = round(time.time() - t0, 1)
    gate["tests"] = [{
        "command": ("cd " + _REPO + " && /Users/hoangminhlong/my-"
                    "quantitative/.venv/bin/python -m pytest "
                    "tests/test_stocks_ng1_p0.py -q"),
        "recorded_in_handoff": True}]
    if "verdict" not in gate:
        gate["verdict"] = "PASS" if not gate["blocking"] else "BLOCKED_DATA"
        if gate["blocking"]:
            gate["verdict_reason"] = (
                "blocking steps: " + ", ".join(gate["blocking"]))
    # census floors unmet do NOT block P0 (lanes die at P2 instead)
    with open(os.path.join(OUT_DIR, "p0_gate.json"), "w") as fh:
        json.dump(gate, fh, indent=1, sort_keys=True)
    print(json.dumps({"verdict": gate["verdict"],
                      "blocking": gate["blocking"],
                      "seconds": gate["seconds"]}, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
