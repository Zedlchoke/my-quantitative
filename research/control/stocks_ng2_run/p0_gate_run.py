#!/usr/bin/env python
"""STOCKS-NG2 P0 gate driver (lane p0: data authority + census).

Stages (argparse):
  --stage fetch : P-7 canaries first (must FAIL as expected, else the
                  mass fetch aborts fail-closed), then the targeted
                  EDGAR 4/A re-ingest for every pinned-cohort 4/A
                  accession (3,062 targets; keyless; UA 'Research
                  my-quantitative@example.com'; <= 2 req/s etiquette,
                  backoff, crash-safe resume via fetch state).
  --stage gate  : everything, in order (default):
                  1. authority + plane adoption (frozen S1 set, reuse
                     of the ng1 plane adapter, refusal path proven);
                  2. S1 pins re-verify: direct digests + FULL re-hash
                     of every pinned substrate file (345,150 XML +
                     4,336 eodhd div/splits + 410 submissions) -- the
                     same pass builds the originals match-key index;
                  3. canaries + targeted re-ingest (resumes state from
                     --stage fetch; near-instant when complete);
                  4. amendment census on the extended substrate with
                     the frozen floor (>= 200 resolvable);
                  5. EODHD field-family-2 probe (short-interests,
                     existing entitlement, fail-closed honest verdict);
                  6. per-lane verdicts -> p0_gate.json.

Verdict law (identical to ng1): P0 PASS | BLOCKED_DATA, fail-closed;
a census floor unmet kills its LANE at P2, it does not block P0.
CANDIDATE_NOT_AUTHORIZED on the EODHD family is an honest lane verdict,
not a gate failure.  Exit code 0 iff PASS.
"""

from __future__ import annotations

import argparse
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
    ConsumptionRefused, PIN_FORM4_STREAM_SHA256,
    PIN_SUBSTRATE_MANIFEST_SHA256, StocksNG1Plane,
)
from research.assets.stocks_ng1.censuses import verify_aux_sections  # noqa: E402
from research.assets.stocks_ng2.form4a_ingest import (  # noqa: E402
    MIN_INTERVAL_SECONDS, USER_AGENT, build_manifest, build_targets,
    canary_checks, fetch_targets,
)
from research.assets.stocks_ng2.extended_census import (  # noqa: E402
    census_amendments, census_b_floor_evaluation, scan_originals,
    well_formed_sample,
)
from research.assets.stocks_ng2 import eodhd_probe  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "stocks_ng2_run/p0_gate@1"

DATA_RAW_FORM4A = os.path.join(_REPO, "data_raw", "form4a")
FETCH_STATE = os.path.join(_REPO, "data_raw", "form4a_fetch_state.jsonl")
V13_MANIFEST_PATH = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v13/"
    "integration/research/control/stocks_free_v13_run/substrate_manifest.json")

COMMAND_GATE = (f"cd {_REPO} && /Users/hoangminhlong/my-quantitative/"
                f".venv/bin/python research/control/stocks_ng2_run/"
                f"p0_gate_run.py --stage gate")
COMMAND_FETCH = (COMMAND_GATE.replace("--stage gate", "--stage fetch"))

DISPATCH_SHA = "400048457ed453a9cc824d35a83c76259ad94e47"


def _dump(name: str, obj: dict) -> str:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------ #
# stage: fetch (canaries + targeted re-ingest)
# ------------------------------------------------------------------ #

def run_fetch_stage() -> int:
    plane = StocksNG1Plane()
    manifest = plane.plane_manifest()["manifest"]
    subs_dir = os.path.join(plane.substrate_root, "submissions_alive")
    targets = build_targets(subs_dir)
    print(json.dumps({"stage": "fetch", "targets": len(targets)}))

    canaries = canary_checks()
    _dump("p0_fetch_canaries.json", {
        "schema": "stocks_ng2_run/p0_fetch_canaries@1",
        "measured_utc": _now(), "user_agent": USER_AGENT,
        "etiquette": {"min_request_interval_s": MIN_INTERVAL_SECONDS,
                      "ceiling_req_per_s": 2},
        **canaries})
    if not canaries["all_failed_as_expected"]:
        print(json.dumps({"stage": "fetch", "aborted": True,
                          "reason": "canary positive anomaly: a "
                                    "never-existed accession or dead CIK "
                                    "served data -- fail-closed, no mass "
                                    "fetch"}))
        return 2

    t0 = time.time()
    summary = fetch_targets(targets, DATA_RAW_FORM4A, FETCH_STATE)
    summary.update(measured_utc=_now(), seconds=round(time.time() - t0, 1),
                   user_agent=USER_AGENT,
                   etiquette={"min_request_interval_s":
                              MIN_INTERVAL_SECONDS,
                              "ceiling_req_per_s": 2,
                              "backoff_s": [10, 30, 60],
                              "max_attempts_per_url": 4})
    _dump("p0_fetch_summary.json", {
        "schema": "stocks_ng2_run/p0_fetch_summary@1", **summary})
    print(json.dumps({"stage": "fetch", "summary": {
        k: v for k, v in summary.items() if k != "etiquette"}}))
    return 0 if not summary["blocked_partial"] else 3


# ------------------------------------------------------------------ #
# stage: gate (everything, resumes fetch state)
# ------------------------------------------------------------------ #

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("fetch", "gate"),
                        default="gate")
    args = parser.parse_args()
    if args.stage == "fetch":
        return run_fetch_stage()

    t0 = time.time()
    gate: dict = {
        "schema": SCHEMA, "gate": "P0", "cycle": "STOCKS-NG2",
        "lane": "p0", "measured_utc": _now(), "command": COMMAND_GATE,
        "worktree": _REPO, "dispatch_base_sha": DISPATCH_SHA,
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
            "bytes": manifest_out["bytes"],
            "sha256": manifest_out["sha256"]}
        adoption["consumed"]["form4_stream"] = {
            "resolved_address": stream_out["resolved_address"],
            "bytes": stream_out["bytes"],
            "sha256": stream_out["sha256"]}
        ok = (granted_ok and refused
              and manifest_out["sha256"] == PIN_SUBSTRATE_MANIFEST_SHA256
              and stream_out["sha256"] == PIN_FORM4_STREAM_SHA256)
        step("authority_plane_adoption", ok, {"detail": adoption})
        manifest = manifest_out["manifest"]
    except Exception as exc:  # fail-closed: no partial credit
        step("authority_plane_adoption", False,
             {"detail": adoption, "error": repr(exc)})
        _finish(gate, t0)
        return 1

    # ---------------- 2. S1 re-pin: direct + FULL re-hash ------------- #
    repin: dict = {
        "pinned_manifest_sha256": PIN_SUBSTRATE_MANIFEST_SHA256,
        "pinned_stream_sha256": PIN_FORM4_STREAM_SHA256,
        "inherited_pin_root": plane.substrate_root,
        "direct_paths": {"manifest": V13_MANIFEST_PATH,
                         "stream": plane.direct_stream_path},
        "method": ("FULL re-hash of every pinned substrate file "
                   "(no sampling; single pass) + originals match-key "
                   "index build for the extended amendment census"),
    }
    try:
        dm_sha = hashlib.sha256(
            open(V13_MANIFEST_PATH, "rb").read()).hexdigest()
        with open(plane.direct_stream_path, "rb") as fh:
            ds_sha = hashlib.sha256(fh.read()).hexdigest()
        repin["direct_manifest_sha256"] = dm_sha
        repin["direct_stream_sha256"] = ds_sha
        direct_ok = (dm_sha == PIN_SUBSTRATE_MANIFEST_SHA256
                     and ds_sha == PIN_FORM4_STREAM_SHA256)
        step("repin_direct_digests", direct_ok,
             {"detail": {"direct_manifest_sha256": dm_sha,
                         "direct_stream_sha256": ds_sha}})
    except Exception as exc:
        step("repin_direct_digests", False, {"error": repr(exc)})
        direct_ok = False

    try:
        full = scan_originals(manifest, plane.substrate_root)
        aux = verify_aux_sections(manifest, plane.substrate_root)
        original_index = full.pop("_original_index")  # keep for census
        repin["form4_xml_docs"] = full
        repin["aux_sections"] = aux
        eodhd_files = (aux["eodhd_div"]["files_total"]
                       + aux["eodhd_splits"]["files_total"])
        full_ok = (full["status"] == "OK"
                   and all(s["status"] == "OK" for s in aux.values())
                   and eodhd_files == 4336
                   and full["files_ok"] == 345150
                   and full["doc_type_distribution"] == {"4": 345150})
        step("repin_full_substrate", full_ok,
             {"files": {"form4_xml": full["files_total"],
                        "eodhd": eodhd_files, "submissions": 410},
              "original_index_size": full["original_index_size"]})
        gate.setdefault("evidence_paths", {})[
            "s1_repverify"] = _dump("p0_s1_repverify.json", {
                "schema": "stocks_ng2_run/p0_s1_repverify@1",
                "measured_utc": _now(), **repin})
    except Exception as exc:
        step("repin_full_substrate", False, {"error": repr(exc)})
        _finish(gate, t0)
        return 1

    # ---------------- 3. canaries + targeted re-ingest ---------------- #
    ingest: dict = {"user_agent": USER_AGENT,
                    "etiquette": {"min_request_interval_s":
                                  MIN_INTERVAL_SECONDS,
                                  "ceiling_req_per_s": 2},
                    "fetch_command": COMMAND_FETCH}
    try:
        targets = build_targets(
            os.path.join(plane.substrate_root, "submissions_alive"))
        ingest["targets"] = len(targets)
        ingest["targets_unique_accessions"] = len(
            {t["accession_nodash"] for t in targets})
        canaries = canary_checks()
        ingest["canaries"] = canaries
        canaries_ok = canaries["all_failed_as_expected"]
        step("p7_canaries", canaries_ok, {})
        if not canaries_ok:
            # fail-closed: no ingestion on a broken probe path
            ingest["fetch"] = {"skipped": "canary positive anomaly"}
            step("form4a_reingest", False,
                 {"reason": "canaries did not fail as expected"})
        else:
            fsum = fetch_targets(targets, DATA_RAW_FORM4A, FETCH_STATE)
            ingest["fetch"] = fsum
            mf = build_manifest(DATA_RAW_FORM4A, FETCH_STATE)
            mf_path = _dump("p0_form4a_ingest_manifest.json", {
                "schema": "stocks_ng2_run/p0_form4a_ingest_manifest@1",
                "measured_utc": _now(),
                "out_root": DATA_RAW_FORM4A,
                "fetch_state": FETCH_STATE, **mf})
            ingest["manifest_path"] = mf_path
            ingest["manifest_aggregate_sha256"] = mf["aggregate_sha256"]
            ingest["manifest_status"] = mf["status"]
            ingest["measured_utc"] = _now()
            gate.setdefault("evidence_paths", {})[
                "form4a_reingest"] = _dump(
                    "p0_form4a_reingest.json",
                    {"schema": "stocks_ng2_run/p0_form4a_reingest@1",
                     **{k: v for k, v in ingest.items()
                        if k != "manifest_path"}})
            fetched_all = (fsum["fetched_ok"] + fsum["not_found"]
                           + fsum["failed"] + fsum["resumed_done"]
                           == fsum["targets"])
            step("form4a_reingest",
                 fetched_all and not fsum["blocked_partial"]
                 and mf["status"] == "OK",
                 {"fetch_summary": {
                     k: v for k, v in fsum.items()
                     if k not in ("etiquette",)}})
    except Exception as exc:
        step("form4a_reingest", False, {"error": repr(exc)})

    # ---------------- 4. amendment census (extended substrate) -------- #
    census_ok = False
    try:
        census = census_amendments(DATA_RAW_FORM4A, FETCH_STATE,
                                   original_index)
        doc_paths = [
            os.path.join(DATA_RAW_FORM4A, r["cik"],
                         r["accession_nodash"], r["primary_file"])
            for r in census["amendment_rows"]]
        sample = well_formed_sample(doc_paths)
        floor = census_b_floor_evaluation(census)
        census_doc = {
            "schema": "stocks_ng2_run/p0_census_b_amendments_extended@1",
            "measured_utc": _now(), "census": census,
            "well_formed_sample_5": sample,
            "floor_evaluation": floor,
        }
        # trim heavy row lists for the committed artifact (counts kept)
        census_dump = json.loads(json.dumps(census_doc))
        for k in ("amendment_rows", "resolvable_rows",
                  "unresolvable_rows"):
            rows = census_dump["census"][k]
            census_dump["census"][k + "_count"] = len(rows)
            census_dump["census"][k] = rows[:50]
            census_dump["census"][k + "_trimmed"] = True
        cb_path = _dump("p0_census_b_amendments_extended.json",
                        census_dump)
        gate.setdefault("evidence_paths", {})["census_b_extended"] = cb_path
        census_ok = sample["all_well_formed"]
        step("census_amendments_extended", census_ok, {
            "amendment_docs": census["amendment_docs"],
            "amendments_with_resolvable_original":
                census["amendments_with_resolvable_original"],
            "fetched_non_xml": census["fetched_non_xml"],
            "malformed_xml_docs": census["malformed_xml_docs"],
            "unexpected_doc_types": census["unexpected_doc_types"],
            "well_formed_sample_all_ok": sample["all_well_formed"],
            "floor_met": floor["met"]})
        gate["census_floors"] = {"census_b_extended": floor}
    except Exception as exc:
        step("census_amendments_extended", False, {"error": repr(exc)})
        gate["census_floors"] = {"census_b_extended": {
            "error": repr(exc)}}

    # ---------------- 5. EODHD field-family-2 probe ------------------- #
    try:
        probe_doc = _run_eodhd_probe(manifest)
        gate.setdefault("evidence_paths", {})[
            "eodhd_short_interest"] = probe_doc["path"]
        step("eodhd_family2_probe", probe_doc["probe_completed"],
             {"entitlement_verdict": probe_doc["entitlement_verdict"],
              "coverage_50": probe_doc.get("coverage_50")})
        gate["eodhd_family2"] = {
            "entitlement_verdict": probe_doc["entitlement_verdict"],
            "family": "short-interests",
            "coverage_50": probe_doc.get("coverage_50")}
    except Exception as exc:
        step("eodhd_family2_probe", False, {"error": repr(exc)})
        gate["eodhd_family2"] = {"entitlement_verdict": "PROBE_ERROR",
                                 "error": repr(exc)}

    _finish(gate, t0)
    return 0 if gate["verdict"] == "PASS" else 1


def _run_eodhd_probe(manifest: dict) -> dict:
    """Entitlement probe with a known-good CONTROL endpoint first (the
    key never leaves this process):

      control dead  -> PROBE_INCONCLUSIVE (key/transport, not family);
      control alive + family 403/error-payload or all-404
                   -> CANDIDATE_NOT_AUTHORIZED (family not in the
                      entitlement; EODHD's gateway 404s unserved
                      families instead of a JSON 403);
      control alive + family serves -> 50-symbol coverage probe.
    """
    symbols = [k[:-5] for k in
               manifest["sections"]["eodhd_div"]["files"].keys()
               if k.endswith(".json")]
    key = eodhd_probe.load_api_key()
    control = eodhd_probe.control_probe(key)
    probe5_symbols = eodhd_probe.deterministic_sample(symbols, 5)
    probe5 = eodhd_probe.probe_symbols(probe5_symbols, key)
    doc: dict = {
        "schema": "stocks_ng2_run/p0_eodhd_short_interest@1",
        "measured_utc": _now(),
        "family": "short-interests",
        "endpoint": f"{eodhd_probe.EODHD_API_BASE}/short-interests/"
                    "{symbol}?api_token=<KEY>&fmt=json",
        "key_handling": ("programmatic .env load; value never echoed, "
                         "never written to any artifact"),
        "entitlement_control": {
            "endpoint": "GET /api/eod/AAPL.US (known-good for this "
                        "key at V13 time)",
            "http_status": control["http_status"],
            "alive": control["alive"]},
        "probe_5": probe5,
    }
    if not control["alive"]:
        doc["entitlement_verdict"] = "PROBE_INCONCLUSIVE_CONTROL_DEAD"
        doc["probe_completed"] = True
        return {"path": _dump("p0_eodhd_short_interest.json", doc),
                **doc}
    not_auth = any(r["class"] == "NOT_AUTHORIZED"
                   for r in probe5["rows"])
    not_served_404 = any(r["class"] == "FAMILY_NOT_SERVED_404"
                         for r in probe5["rows"])
    auth_classes = {"OK_NONEMPTY", "OK_EMPTY", "OK_OTHER_SHAPE"}
    if not_auth or not_served_404:
        doc["entitlement_verdict"] = "CANDIDATE_NOT_AUTHORIZED"
        doc["verdict_evidence"] = (
            "control endpoint answered 200 (key valid) while the "
            "short-interests endpoint answered "
            + ("an entitlement error" if not_auth else "404 on both "
               "symbol forms for every probed symbol")
            + " -- the entitlement does not serve this family")
        doc["probe_completed"] = True
    elif not all(r["class"] in auth_classes for r in probe5["rows"]):
        doc["entitlement_verdict"] = "PROBE_INCONCLUSIVE"
        doc["probe_completed"] = True
    else:
        probe50_symbols = eodhd_probe.deterministic_sample(symbols, 50)
        probe50 = eodhd_probe.probe_symbols(probe50_symbols, key)
        doc["probe_50"] = probe50
        evaluation = eodhd_probe.evaluate_family(probe50)
        doc["coverage_50"] = evaluation
        doc["entitlement_verdict"] = "PASS"
        doc["probe_completed"] = True
    return {"path": _dump("p0_eodhd_short_interest.json", doc), **doc}


def _finish(gate: dict, t0: float) -> None:
    gate["seconds"] = round(time.time() - t0, 1)
    gate["tests"] = [{
        "command": ("cd " + _REPO + " && /Users/hoangminhlong/"
                    "quantitative/.venv/bin/python -m pytest "
                    "tests/test_stocks_ng2_p0.py -q"),
        "recorded_in_handoff": True}]
    # ---- per-lane verdicts (floors unmet kill lanes at P2, not P0) -- #
    lane_verdicts: dict[str, str] = {}
    steps_ok = {s["step"]: s["ok"] for s in gate["steps"]}
    floors = gate.get("census_floors", {})
    cb = floors.get("census_b_extended", {})
    reingest_ok = all(steps_ok.get(k, False) for k in (
        "authority_plane_adoption", "repin_direct_digests",
        "repin_full_substrate", "p7_canaries", "form4a_reingest",
        "census_amendments_extended"))
    if reingest_ok and cb.get("met"):
        lane_verdicts["A4_amendment_reingest"] = "PASS"
    elif reingest_ok:
        lane_verdicts["A4_amendment_reingest"] = "FLOOR_UNMET_DIES_P2"
    else:
        lane_verdicts["A4_amendment_reingest"] = "BLOCKED_DATA"
    fam = gate.get("eodhd_family2", {})
    if fam.get("entitlement_verdict") == "PASS":
        lane_verdicts["A5_eodhd_family2"] = "PASS"
    elif fam.get("entitlement_verdict") == "CANDIDATE_NOT_AUTHORIZED":
        lane_verdicts["A5_eodhd_family2"] = "CANDIDATE_NOT_AUTHORIZED"
    else:
        lane_verdicts["A5_eodhd_family2"] = "BLOCKED_DATA"
    gate["lane_verdicts"] = lane_verdicts
    gate["lane_verdict_law"] = (
        "A4: PASS iff re-ingest+S1+canaries+census OK and floor >= 200 "
        "resolvable; unmet floor kills lane A4 at P2 (P0 still passes). "
        "A5: PASS iff the entitlement serves the family; "
        "CANDIDATE_NOT_AUTHORIZED kills lane A5 at P2 (honest, not a "
        "gate failure)")

    if "verdict" not in gate:
        gate["verdict"] = "PASS" if not gate["blocking"] else "BLOCKED_DATA"
        if gate["blocking"]:
            gate["verdict_reason"] = (
                "blocking steps: " + ", ".join(gate["blocking"]))
    with open(os.path.join(OUT_DIR, "p0_gate.json"), "w") as fh:
        json.dump(gate, fh, indent=1, sort_keys=True)
    print(json.dumps({"verdict": gate["verdict"],
                      "lane_verdicts": lane_verdicts,
                      "blocking": gate["blocking"],
                      "seconds": gate["seconds"]}, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
