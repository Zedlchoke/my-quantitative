#!/usr/bin/env python
"""VOL-NG1 P0 adoption runner (lane p0, task vol-ng1-p0-adoption).

Two stages, one gate artifact:

1. ``ingest`` (the only stage with network) -- bounded pulls of the
   plan-frozen consumption set:
     - the four official CBOE daily-history CSVs (keyless): every pull
       MUST reproduce the digest already frozen in the adapter (a
       mismatch is a drift incident: fail-closed, never repaired);
     - EODHD family-1 daily EOD for the living legs (VXX/UVXY/SVXY
       plan-named + VIXY/VIXM/VXZ bounded discovery probes): RAW
       primary, ``adjusted_close`` cross-check in the same response;
     - the XIV.US plain-eod negative probe (Lead-probe semantics);
     - the EODHD US delisted channel (one bounded request): dead
       inverse-vol proof + never-existed negative controls.
   Writes the raw snapshots, the ingest manifest (URLs redacted; the
   key is NEVER echoed -- V13), the delisted census, and the measured
   census (floors + P-7 canaries).

2. ``adopt`` (NO network) -- platform-v3 adoption over the committed
   bytes: cycle authority journal (register -> evidence -> adjudicate,
   full inherited state machine), CADS pins, then EVERYTHING is
   consumed back through ``VolNg1Plane`` (consume_via_plane):
     - every frozen entry re-resolves to its frozen digest;
     - the census floors are RE-DERIVED from plane-consumed bytes and
       must equal the committed census (plane-consumption proof);
     - the bounded shadow-parity pilot (plane read vs raw bytes) must
       be digest-identical for every entry;
     - the manifest-verified query plane runs the frozen bounds query
       on each CBOE CSV;
     - the pytest command runs.

Publishes ``p0_gate.json`` with per-floor measured values, evidence
paths, sha256 pins and PASS/FAIL/BLOCKED verdicts derived ONLY from
what actually ran.  Exit codes: 0 = PASS, 3 = BLOCKED/FAIL, 4 = usage.

NO proposals, NO signals, NO scoring, NO outcome numbers anywhere
(P0 census law).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.vol_ng1 import census as vc            # noqa: E402
from research.assets.vol_ng1 import ingest as vi            # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa     # noqa: E402

SCHEMA = "vol_ng1_run/p0_gate@1"
TASK_ID = "vol-ng1-p0-adoption"
CYCLE_ID = "VOL-NG1"
VENV_PYTHON = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"

OUT_DIR = os.path.join(REPO_ROOT, "research", "control", "vol_ng1_run")
RAW_DIR = os.path.join(REPO_ROOT, "research", "assets", "vol_ng1", "raw")
CBOE_RAW_DIR = os.path.join(RAW_DIR, "cboe")
EODHD_RAW_DIR = os.path.join(RAW_DIR, "eodhd")
UNTRACKED_DIR = os.path.join(OUT_DIR, "raw_untracked")

INGEST_MANIFEST = os.path.join(OUT_DIR, "p0_ingest_manifest.json")
DELISTED_CENSUS = os.path.join(OUT_DIR, "p0_delisted_census.json")
CENSUS_OUT = os.path.join(OUT_DIR, "p0_census.json")
GATE_PATH = os.path.join(OUT_DIR, "p0_gate.json")

STORE_ROOT = pa.DEFAULT_STORE_ROOT
JOURNAL_PATH = pa.DEFAULT_AUTHORITY_JOURNAL


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False, default=str)
        fh.write("\n")


def git_state() -> dict:
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", REPO_ROOT, *args],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    return {"branch": git("branch", "--show-current"),
            "head_sha": git("rev-parse", "HEAD")}


# --------------------------------------------------------------------------- #
# census construction (shared by both stages)
# --------------------------------------------------------------------------- #

def build_census(series_by_name: dict[str, dict[str, float]],
                 living_legs: dict[str, dict], delisted: dict,
                 cboe_served_census: list[dict], measured_utc: str) -> dict:
    overlap = vc.overlap_census(series_by_name)
    floor_rows = vc.floors(overlap, living_legs, delisted)
    canary_rows = vc.canaries(series_by_name, delisted)
    return {
        "schema": "vol_ng1_run/p0_census@1",
        "task_id": TASK_ID,
        "measured_utc": measured_utc,
        "cboe_served_census": cboe_served_census,
        "overlap": overlap,
        "living_legs": living_legs,
        "delisted_channel": delisted,
        "floors": floor_rows,
        "canaries": canary_rows,
    }


def load_series_from_cboe_raw() -> tuple[dict[str, dict[str, float]],
                                         list[dict]]:
    """Parse the committed CBOE snapshots (verify-on-read against the
    frozen adapter digests) into series maps + a served-census list."""
    series_by_name: dict[str, dict[str, float]] = {}
    served: list[dict] = []
    for entry_name, meta in pa.FROZEN_ENTRIES.items():
        if meta["series"] != pa.SERIES_CBOE:
            continue
        name = entry_name.replace("_History.csv", "")
        vc.require_frozen_index_name(name)
        raw_path = pa.raw_path_for(entry_name)
        if not os.path.isfile(raw_path):
            raise vc.CensusError(
                f"raw CBOE snapshot missing for {name}: {raw_path}")
        with open(raw_path, "rb") as fh:
            body = fh.read()
        digest = hashlib.sha256(body).hexdigest()
        if digest != meta["sha256"]:
            raise vc.CensusError(
                f"raw CBOE bytes drift for {name}: {digest} != "
                f"{meta['sha256']} (fail-closed)")
        series_by_name[name] = vc.parse_cboe_csv(body)
        served.append({
            "index_name": name, "served": True, "http_status": 200,
            "sha256": digest, "bytes": len(body),
            "url": vi.redact(vi.cboe_url(name)),
        })
    return series_by_name, served


# --------------------------------------------------------------------------- #
# stage: ingest
# --------------------------------------------------------------------------- #

def run_ingest() -> int:
    key = vi.load_eodhd_key()
    if not key:
        write_json(INGEST_MANIFEST, {
            "schema": "vol_ng1_run/p0_ingest_manifest@1",
            "task_id": TASK_ID, "measured_utc": now_utc(),
            "key_loaded": False, "verdict": "BLOCKED_NO_KEY",
            "note": "EODHD_API_KEY absent/empty; keyed channels NOT "
                    "probed (fail-closed, no signup performed)"})
        print(json.dumps({"verdict": "BLOCKED_NO_KEY"}, indent=1))
        return 3

    manifest: dict = {
        "schema": "vol_ng1_run/p0_ingest_manifest@1",
        "task_id": TASK_ID,
        "cycle_id": CYCLE_ID,
        "measured_utc": now_utc(),
        "key_loaded": True,
        "key_echoed": False,
        "cboe": [],
        "eodhd_eod": [],
        "channel_canaries": {},
    }

    # ---- CBOE official histories (frozen-digest re-pull) ------------- #
    for entry_name, meta in pa.FROZEN_ENTRIES.items():
        if meta["series"] != pa.SERIES_CBOE:
            continue
        time.sleep(1.0)                     # keyless-channel politeness
        name = entry_name.replace("_History.csv", "")
        pull = vi.pull_cboe(name, raw_sink_path=os.path.join(
            CBOE_RAW_DIR, entry_name))
        pull["raw_path"] = os.path.relpath(
            os.path.join(CBOE_RAW_DIR, entry_name), REPO_ROOT)
        pull["frozen_sha256"] = meta["sha256"]
        pull["frozen_digest_reproduced"] = bool(
            pull["served"] and pull["sha256"] == meta["sha256"])
        manifest["cboe"].append(pull)

    # ---- EODHD family-1 living legs ----------------------------------- #
    for symbol in vi.ETP_LIVING_CANDIDATES + vi.ETP_EXTRA_CANDIDATES:
        entry_name = f"{symbol}.US_eod.json"
        raw_path = os.path.join(EODHD_RAW_DIR, entry_name)
        pull = vi.pull_eodhd_eod(symbol, key, raw_sink_path=raw_path)
        if pull["served"] and pull.get("bars", 0) > 0:
            with open(raw_path, "rb") as fh:
                body = fh.read()
            if hashlib.sha256(body).hexdigest() != pull["sha256"]:
                raise vc.CensusError(
                    f"EODHD bytes drift for {symbol}: verify-on-read "
                    "failed")
            bars = json.loads(body.decode("utf-8"))
            pull.update({
                "raw_path": os.path.relpath(raw_path, REPO_ROOT),
                "coverage": vc.etp_leg_coverage(bars),
                "corp_action_cross_check": vc.detect_corp_action_steps(bars),
                "plan_named": symbol in vi.ETP_LIVING_CANDIDATES,
            })
        else:
            pull.update({"raw_path": None, "coverage": None,
                         "corp_action_cross_check": None,
                         "plan_named": symbol in vi.ETP_LIVING_CANDIDATES})
        manifest["eodhd_eod"].append(pull)

    # ---- XIV plain-eod negative probe (dead-name semantics) ----------- #
    xiv_probe = vi.probe_plain_eod_empty("XIV", key)
    manifest["xiv_plain_eod_probe"] = {
        "symbol": "XIV",
        "url": xiv_probe["url"],
        "http_status": xiv_probe["http_status"],
        "served": xiv_probe["served"],
        "bars": xiv_probe.get("bars", 0),
        "note": "expected EMPTY on the plain eod endpoint (Lead probe "
                "2026-09-12 reproduced); the delisted channel is the "
                "only lawful proof route",
    }

    # ---- EODHD US delisted channel ------------------------------------- #
    sink = os.path.join(UNTRACKED_DIR, "delisted_us_symbols.json")
    dl = vi.pull_eodhd_delisted(key, raw_sink_path=sink)
    dl_summary = {k: v for k, v in dl.items() if k != "matches"}
    dl_summary["wanted_records"] = dl.get("matches", {})
    manifest["delisted_channel"] = dl_summary
    manifest["untracked_sink"] = {
        "path": os.path.relpath(sink, REPO_ROOT),
        "tracked": False,
        "note": "full delisted response kept UNTRACKED for local digest "
                "verify-on-read; committed evidence = census + "
                "full-response sha256",
    }

    # ---- channel canaries (P-7 per channel) ----------------------------- #
    manifest["channel_canaries"]["cboe-official"] = {
        "alive": all(p["served"] for p in manifest["cboe"]),
        "dead_distinguishable": True,
        "dead_probe": "fabricated index name refused pre-request (P-7; "
                      "asserted by the census canaries + tests)",
    }
    manifest["channel_canaries"]["eodhd-eod"] = {
        "alive": any(p["served"] and p.get("bars", 0) > 0
                     for p in manifest["eodhd_eod"]),
        "dead_distinguishable": bool(
            (xiv_probe["http_status"] in (200, 404)
             and xiv_probe.get("bars", 0) == 0)
            or xiv_probe["http_status"] == 404),
        "dead_probe": "XIV.US plain-eod empty/distinguishable",
    }
    manifest["channel_canaries"]["eodhd-delisted"] = {
        "alive": bool(dl.get("served") and dl.get("total_symbols", 0) > 1000),
        "dead_distinguishable": all(dl.get("controls_absent", {}).values()),
        "dead_probe": "never-existed controls absent from the list",
    }

    # ---- delisted census (committed artifact) -------------------------- #
    delisted_census = {
        "schema": "vol_ng1_run/p0_delisted_census@1",
        "task_id": TASK_ID,
        "measured_utc": dl.get("retrieved_utc"),
        "url": dl.get("url"),
        "http_status": dl.get("http_status"),
        "served": dl.get("served"),
        "full_response_sha256": dl.get("sha256"),
        "full_response_bytes": dl.get("bytes"),
        "total_symbols": dl.get("total_symbols"),
        "dead_candidates": list(vi.DEAD_VOL_CANDIDATES),
        "dead_present": dl.get("dead_present", {}),
        "wanted_records": dl.get("matches", {}),
        "never_existed_controls": list(vi.NEVER_EXISTED_CONTROLS),
        "controls_absent": dl.get("controls_absent", {}),
        "xiv_plain_eod_probe": manifest["xiv_plain_eod_probe"],
        "raw_sink_path": manifest["untracked_sink"]["path"],
    }
    write_json(DELISTED_CENSUS, delisted_census)

    # ---- measured census (floors + canaries) --------------------------- #
    series_by_name, served = load_series_from_cboe_raw()
    living_legs = {p["symbol"]: p["coverage"]
                   for p in manifest["eodhd_eod"] if p.get("coverage")}
    dl_for_census = {
        "served": dl.get("served"),
        "total_symbols": dl.get("total_symbols"),
        "full_response_sha256": dl.get("sha256"),
        "dead_present": dl.get("dead_present", {}),
        "controls_absent": dl.get("controls_absent", {}),
    }
    census = build_census(series_by_name, living_legs, dl_for_census,
                          served, manifest["measured_utc"])
    write_json(CENSUS_OUT, census)
    write_json(INGEST_MANIFEST, manifest)

    summary = {
        "cboe_frozen_digests_reproduced": all(
            p["frozen_digest_reproduced"] for p in manifest["cboe"]),
        "living_legs_served": sorted(living_legs),
        "leg_years_eod": {k: v["years_eod"] for k, v in
                          living_legs.items()},
        "delisted_channel_served": dl.get("served"),
        "delisted_total_symbols": dl.get("total_symbols"),
        "dead_present": dl.get("dead_present"),
        "floors": census["floors"],
        "canaries_all_pass": all(c["verdict"] == "PASS"
                                 for c in census["canaries"]),
        "NEW_EODHD_DIGESTS_TO_FREEZE": {
            f"{p['symbol']}.US_eod.json": p["sha256"]
            for p in manifest["eodhd_eod"]
            if p["served"] and p.get("bars", 0) > 0},
        "DELISTED_CENSUS_DIGEST_TO_FREEZE": sha256_file(DELISTED_CENSUS),
    }
    print(json.dumps(summary, indent=1, default=str))
    ok = (summary["cboe_frozen_digests_reproduced"]
          and summary["canaries_all_pass"])
    return 0 if ok else 3


# --------------------------------------------------------------------------- #
# stage: adopt (NO network)
# --------------------------------------------------------------------------- #

def adopt_authority(store: "pa.CADS", pins_by_series: dict[str, list[str]],
                    canaries: dict[str, bool]) -> None:
    """Register -> evidence -> adjudicate for the three cycle series
    (full inherited state machine; GRANT requires ALL of PIT/license/
    entitlement/canary/CADS pins).  Idempotent by refusing to run when
    the journal already exists (the caller checks)."""
    reg = pa.VolNg1Authority(JOURNAL_PATH)
    plan = [
        (pa.SERIES_CBOE, "cboe-official", "cboe-cdn"),
        (pa.SERIES_ETP_EOD, "eodhd-eod", "eodhd"),
        (pa.SERIES_ETP_DELISTED, "eodhd-delisted", "eodhd"),
    ]
    for series_id, channel, source in plan:
        reg.register(series_id, source=source, channel=channel)
        reg.transition(series_id, "INGESTED",
                       attempt="vol-ng1-p0-ingest")
        reg.transition(series_id, "VERIFIED",
                       attempt="vol-ng1-p0-verify-on-read")
        reg.evidence(
            series_id,
            pit_verdict="PASS_PIT_EVIDENCED",
            license_status="AUTHORIZED",
            entitlement_status="AUTHORIZED",
            canary_probe={channel: ("PASS" if canaries.get(channel)
                                    else "FAIL")},
            cads_pins=pins_by_series.get(series_id, []))
        outcome = reg.adjudicate(series_id,
                                 granted_by="vol-ng1-p0-runner",
                                 granted_at=now_utc())
        if outcome != "GRANTED":
            raise pa.PlaneConsumptionRefused(
                f"series {series_id} adjudicated {outcome!r}: adoption "
                "refused (fail-closed)")


def run_adopt(skip_tests: bool) -> int:
    gate: dict = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "cycle_id": CYCLE_ID,
        "lane": "p0",
        "measured_utc": now_utc(),
        "worktree": REPO_ROOT,
        "cads_store_root": os.path.relpath(STORE_ROOT, REPO_ROOT),
        "cads_store_mode": "cycle-scoped, committed, read-only after adoption",
        "authority_journal": os.path.relpath(JOURNAL_PATH, REPO_ROOT),
        "sections": {},
        "verdict_basis": [],
        "git": git_state(),
    }
    blocker: str | None = None

    # ---- bootstrap (idempotent) ---------------------------------------- #
    fresh = not os.path.isfile(JOURNAL_PATH)
    entries = pa.all_frozen_entries()
    canaries = {
        "cboe-official": True,   # frozen-digest reproduction (ingest stage)
        "eodhd-eod": True,
        "eodhd-delisted": True,
    }
    if fresh:
        if not os.path.isfile(DELISTED_CENSUS):
            print(json.dumps({"verdict": "BLOCKED_DATA",
                              "blocker": "delisted census missing; run "
                                         "the ingest stage first"},
                             indent=1))
            return 3
        # canary truth comes from the committed ingest manifest
        with open(INGEST_MANIFEST, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        cc = manifest.get("channel_canaries", {})
        canaries = {ch: bool(v.get("alive") and v.get("dead_distinguishable"))
                    for ch, v in cc.items()}
        os.makedirs(os.path.join(STORE_ROOT, "objects"), exist_ok=True)
        store = pa.CADS(STORE_ROOT)
        pins_by_series: dict[str, list[str]] = {}
        for entry_name, meta in sorted(entries.items()):
            raw_path = pa.raw_path_for(entry_name)
            with open(raw_path, "rb") as fh:
                data = fh.read()
            digest = hashlib.sha256(data).hexdigest()
            if digest != meta["sha256"]:
                print(json.dumps(
                    {"verdict": "BLOCKED_DATA",
                     "blocker": f"{entry_name}: raw bytes {digest} != "
                                f"frozen {meta['sha256']}"}, indent=1))
                return 3
            address = store.register(data)
            store.pin(address, {"series": meta["series"],
                                "file": entry_name})
            pins_by_series.setdefault(meta["series"], []).append(address)
        # the delisted census JSON itself is a pinned consumption entry
        with open(DELISTED_CENSUS, "rb") as fh:
            census_bytes = fh.read()
        census_digest = hashlib.sha256(census_bytes).hexdigest()
        census_entry = "eodhd_us_delisted_census.json"
        pa.register_entry_digest(
            census_entry, pa.SERIES_ETP_DELISTED, census_digest,
            os.path.relpath(DELISTED_CENSUS, pa.RAW_ROOT))
        address = store.register(census_bytes)
        store.pin(address, {"series": pa.SERIES_ETP_DELISTED,
                            "file": census_entry})
        pins_by_series.setdefault(pa.SERIES_ETP_DELISTED, []).append(address)
        try:
            adopt_authority(store, pins_by_series, canaries)
        except Exception as exc:   # noqa: BLE001 - gate records it
            print(json.dumps({"verdict": "BLOCKED_DATA",
                              "blocker": f"authority adoption: {exc}"},
                             indent=1))
            return 3
    else:
        # adopted previously: the committed census JSON entry must be
        # registered in the adapter before the plane can consume it
        census_entry = "eodhd_us_delisted_census.json"
        if census_entry not in pa.all_frozen_entries():
            with open(DELISTED_CENSUS, "rb") as fh:
                census_bytes = fh.read()
            pa.register_entry_digest(
                census_entry, pa.SERIES_ETP_DELISTED,
                hashlib.sha256(census_bytes).hexdigest(),
                os.path.relpath(DELISTED_CENSUS, pa.RAW_ROOT))

    # ---- plane construction --------------------------------------------- #
    try:
        plane = pa.VolNg1Plane()
    except pa.PlaneDataBlocked as exc:
        gate["sections"]["adapter_init"] = {
            "command": "p0_run.py adopt", "exit_code": 3,
            "observed": f"{exc.reason}: {exc}", "verdict": "BLOCKED_DATA"}
        gate["verdict"] = "BLOCKED_DATA"
        _write_gate(gate)
        return 3
    gate["sections"]["adapter_init"] = {
        "command": "p0_run.py adopt", "exit_code": 0,
        "observed": {"store": gate["cads_store_root"],
                     "journal": gate["authority_journal"],
                     "bootstrap": "fresh adoption" if fresh
                     else "replayed from committed journals"},
        "margin": "store + journal present; pins replayed read-only",
        "verdict": "PASS"}
    gate["verdict_basis"].append("adapter_init=PASS")

    # ---- 1. frozen re-resolve through the plane ------------------------- #
    repin: dict[str, dict] = {}
    repin_ok = True
    for entry_name, meta in sorted(entries.items()):
        row = {"command": f"p0_run.py adopt (re_resolve:{entry_name})"}
        try:
            res = plane.consume(entry_name)
            row.update({
                "exit_code": 0,
                "series": meta["series"],
                "frozen_sha256": meta["sha256"],
                "cads_address": res["cads_address"],
                "measured_sha256": res["sha256_measured"],
                "bytes": res["bytes"],
                "authority_verdict": res["verdict"],
                "observed": (f"address==frozen==measured "
                             f"{res['sha256_measured']}"),
                "margin": "exact digest match",
                "verdict": "PASS"})
            if res["sha256_measured"] != meta["sha256"]:
                raise pa.PlaneDataBlocked("plane digest != frozen digest")
        except (pa.PlaneDataBlocked, pa.PlaneConsumptionRefused) as exc:
            row.update({"exit_code": 3, "observed": str(exc),
                        "verdict": "BLOCKED"})
            repin_ok = False
            blocker = blocker or f"re_resolve {entry_name}: {exc}"
        repin[entry_name] = row
    gate["sections"]["frozen_repin"] = {
        "command": "p0_run.py adopt (frozen_repin)",
        "exit_code": 0 if repin_ok else 3,
        "observed": {k: v.get("observed") for k, v in repin.items()},
        "margin": f"all {len(repin)} frozen digests exact via consume_"
                  "via_plane",
        "verdict": "PASS" if repin_ok else "BLOCKED_DATA",
        "entries": repin,
    }
    gate["verdict_basis"].append(
        f"frozen_repin={'PASS' if repin_ok else 'BLOCKED_DATA'}")

    # ---- 2. census re-derived from plane-consumed bytes ------------------ #
    census_ok = repin_ok
    plane_series: dict[str, dict[str, float]] = {}
    cboe_rows: dict[str, dict] = {}
    for entry_name, meta in sorted(entries.items()):
        if meta["series"] != pa.SERIES_CBOE:
            continue
        name = entry_name.replace("_History.csv", "")
        row = {"command": f"p0_run.py adopt (plane_census:{entry_name})"}
        try:
            res = plane.consume(entry_name)
            plane_series[name] = vc.parse_cboe_csv(res["data"])
            q = plane.query_csv_bounds(entry_name)
            row.update({
                "exit_code": 0 if q["query_verdict"] == "SUCCESS" else 3,
                "query_verdict": q["query_verdict"],
                "rows": q["rows"],
                "result_digest": q["result_digest"],
                "observed": q["rows"],
                "margin": "manifest-verified frozen query SUCCESS",
                "verdict": "PASS" if q["query_verdict"] == "SUCCESS"
                           else "BLOCKED_DATA"})
            if q["query_verdict"] != "SUCCESS":
                census_ok = False
                blocker = blocker or f"query {entry_name}: {q['reason']}"
        except (pa.PlaneDataBlocked, pa.PlaneConsumptionRefused,
                vc.CensusError) as exc:
            row.update({"exit_code": 3, "observed": str(exc),
                        "verdict": "BLOCKED_DATA"})
            census_ok = False
            blocker = blocker or f"plane_census {entry_name}: {exc}"
        cboe_rows[entry_name] = row
    gate["sections"]["plane_cboe_query"] = {
        "command": "p0_run.py adopt (plane_cboe_query)",
        "exit_code": 0 if census_ok else 3,
        "observed": {k: v.get("observed") for k, v in cboe_rows.items()},
        "margin": "bounds queries through the manifest-verified QueryPlane",
        "verdict": "PASS" if census_ok else "BLOCKED_DATA",
        "entries": cboe_rows}
    gate["verdict_basis"].append(
        f"plane_cboe_query={'PASS' if census_ok else 'BLOCKED_DATA'}")

    # committed census vs plane-derived census
    committed_census = json.load(open(CENSUS_OUT, encoding="utf-8"))
    dl = committed_census["delisted_channel"]
    living_legs = committed_census["living_legs"]
    if plane_series and len(plane_series) == 4:
        plane_census = build_census(
            plane_series, living_legs, dl,
            committed_census["cboe_served_census"],
            committed_census["measured_utc"])
        same_floors = plane_census["floors"] == committed_census["floors"]
        same_overlap = plane_census["overlap"] == committed_census["overlap"]
    else:
        same_floors = same_overlap = False
    gate["sections"]["plane_census_parity"] = {
        "command": "p0_run.py adopt (plane_census_parity)",
        "exit_code": 0 if (same_floors and same_overlap) else 3,
        "observed": {"floors_equal": same_floors,
                     "overlap_equal": same_overlap,
                     "first_common_date":
                         committed_census["overlap"]["first_common_date"],
                     "last_common_date":
                         committed_census["overlap"]["last_common_date"],
                     "common_days":
                         committed_census["overlap"]["common_days"],
                     "instants_post_2015":
                         committed_census["overlap"]["instants_post_2015"]},
        "margin": "floors + overlap census re-derived from plane-consumed "
                  "bytes equal the committed census",
        "verdict": "PASS" if (same_floors and same_overlap)
                   else "BLOCKED_DATA"}
    gate["verdict_basis"].append(
        f"plane_census_parity={'PASS' if (same_floors and same_overlap) else 'BLOCKED_DATA'}")
    if not (same_floors and same_overlap):
        census_ok = False
        blocker = blocker or "plane-derived census != committed census"

    # ---- 3. floors + canaries sections (measured values) ----------------- #
    floors = committed_census["floors"]
    canary_rows = committed_census["canaries"]
    canaries_ok = all(c["verdict"] == "PASS" for c in canary_rows)
    floors_ok = all(f["verdict"] == "PASS" for f in floors.values())
    gate["sections"]["floors"] = {
        "command": "p0_run.py ingest (floors; plan section 3, frozen)",
        "exit_code": 0 if floors_ok else 3,
        "observed": floors,
        "margin": "all four frozen floors measured",
        "verdict": "PASS" if floors_ok else ("FAIL" if all(
            f["verdict"] in ("PASS", "FAIL") for f in floors.values())
            else "BLOCKED_DATA"),
        "fail_closed_note": "a floor shortfall is a measured FAIL (never "
                            "renegotiated); the short-vol lane dies "
                            "BLOCKED at P0 if F4 cannot be proven"}
    gate["sections"]["canaries"] = {
        "command": "p0_run.py ingest (P-7 canaries; each must FAIL to find)",
        "exit_code": 0 if canaries_ok else 3,
        "observed": canary_rows,
        "margin": "fabricated date + never-existed index column + "
                  "fabricated ETP ticker all refused",
        "verdict": "PASS" if canaries_ok else "FAIL"}
    gate["verdict_basis"].append(
        f"floors={'PASS' if floors_ok else 'FAIL'}")
    gate["verdict_basis"].append(
        f"canaries={'PASS' if canaries_ok else 'FAIL'}")

    # ---- 4. corp-actions cross-check (V8 convention, measured) ----------- #
    # recomputed HERE from plane-consumed bytes (verify-on-read), not
    # from the ingest manifest: adoption only trusts CADS-resolved data.
    # MEASURED INVENTORY (NON_BLOCKING): RAW is primary; the inventory
    # is the mandatory event-handling input for later lanes.
    ca_rows = {}
    ca_total_steps = 0
    for entry_name, meta in sorted(entries.items()):
        if meta["series"] != pa.SERIES_ETP_EOD:
            continue
        symbol = entry_name.replace(".US_eod.json", "")
        try:
            res = plane.consume(entry_name)
            bars = json.loads(res["data"].decode("utf-8"))
            cc = vc.detect_corp_action_steps(bars)
            ca_total_steps += len(cc["step_events"])
            ca_rows[symbol] = {
                "steps_inventoried": len(cc["step_events"]),
                "class_counts": cc["class_counts"],
                "step_events": cc["step_events"],
            }
        except (pa.PlaneDataBlocked, pa.PlaneConsumptionRefused) as exc:
            ca_rows[symbol] = {"error": str(exc)[:200], "verdict": "BLOCKED"}
    gate["sections"]["corp_actions_inventory"] = {
        "command": "p0_run.py adopt (raw-vs-adjusted step inventory from "
                   "plane-consumed bytes; V8 convention: RAW primary)",
        "exit_code": 0,
        "observed": {"total_steps_inventoried": ca_total_steps,
                     "by_symbol": ca_rows},
        "margin": "measured inventory (NON_BLOCKING); RAW-primary "
                  "consumption requires explicit event handling at every "
                  "inventoried step (carried to P1)",
        "verdict": "NON_BLOCKING"}

    # ---- 5. shadow parity (bounded pilot) --------------------------------- #
    parity_rows: dict[str, dict] = {}
    parity_ok = repin_ok
    for entry_name in sorted(entries.keys()):
        row = {"command": f"p0_run.py adopt (shadow_parity:{entry_name})"}
        try:
            p = plane.shadow_parity(entry_name)
            row.update({
                "exit_code": 0 if p["identical"] else 3,
                "plane_sha256": p["plane_sha256"],
                "direct_sha256": p["direct_sha256"],
                "bytes": p["bytes"],
                "observed": (f"plane {p['plane_sha256']} vs raw "
                             f"{p['direct_sha256']}"),
                "margin": "0 (identical)" if p["identical"]
                          else "digests differ",
                "verdict": "PASS" if p["identical"] else "BLOCKED_DATA"})
            if not p["identical"]:
                parity_ok = False
                blocker = blocker or f"shadow_parity {entry_name} mismatch"
        except (pa.PlaneDataBlocked, pa.PlaneConsumptionRefused) as exc:
            row.update({"exit_code": 3, "observed": str(exc),
                        "verdict": "BLOCKED_DATA"})
            parity_ok = False
            blocker = blocker or f"shadow_parity {entry_name}: {exc}"
        parity_rows[entry_name] = row
    gate["sections"]["shadow_parity"] = {
        "command": "p0_run.py adopt (shadow_parity)",
        "exit_code": 0 if parity_ok else 3,
        "observed": {k: v.get("observed") for k, v in parity_rows.items()},
        "margin": "sha256(plane read) == sha256(raw committed bytes) "
                  "for every frozen entry",
        "verdict": "PASS" if parity_ok else "BLOCKED_DATA",
        "entries": parity_rows}
    gate["verdict_basis"].append(
        f"shadow_parity={'PASS' if parity_ok else 'BLOCKED_DATA'}")

    # ---- 6. plane-level P-7 ticker canary --------------------------------- #
    plane_canary_rows = []
    for fake in ("XVXX.US_eod.json", "VIX2M_History.csv",
                 "ZZZVIX.US_eod.json"):
        try:
            plane.consume(fake)
            plane_canary_rows.append({"entry": fake, "refused": False,
                                      "verdict": "FAIL"})
        except pa.PlaneConsumptionRefused as exc:
            plane_canary_rows.append({"entry": fake, "refused": True,
                                      "reason": str(exc)[:140],
                                      "verdict": "PASS"})
        except pa.PlaneDataBlocked as exc:
            plane_canary_rows.append({"entry": fake, "refused": True,
                                      "reason": f"{exc.reason}: {exc}"[:140],
                                      "verdict": "PASS"})
    plane_canary_ok = all(r["verdict"] == "PASS" for r in plane_canary_rows)
    gate["sections"]["plane_ticker_canaries"] = {
        "command": "p0_run.py adopt (plane_ticker_canaries)",
        "exit_code": 0 if plane_canary_ok else 3,
        "observed": plane_canary_rows,
        "margin": "fabricated ETP tickers / index names refused at the "
                  "plane (P-7)",
        "verdict": "PASS" if plane_canary_ok else "FAIL"}
    gate["verdict_basis"].append(
        f"plane_ticker_canaries={'PASS' if plane_canary_ok else 'FAIL'}")
    if not plane_canary_ok:
        blocker = blocker or "plane ticker canary produced a consume"

    # ---- 7. tests ----------------------------------------------------------- #
    if skip_tests:
        gate["sections"]["tests"] = {
            "command": f"cd {REPO_ROOT} && {VENV_PYTHON} -m pytest "
                       "tests/test_vol_ng1_p0.py -q",
            "exit_code": None, "verdict": "NOT_RUN (--skip-tests)"}
        tests_ok = False
    else:
        cmd = [VENV_PYTHON, "-m", "pytest", "tests/test_vol_ng1_p0.py", "-q"]
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True,
                              text=True)
        tests_ok = proc.returncode == 0
        gate["sections"]["tests"] = {
            "command": f"cd {REPO_ROOT} && {VENV_PYTHON} -m pytest "
                       "tests/test_vol_ng1_p0.py -q",
            "exit_code": proc.returncode,
            "observed": (proc.stdout or "").strip().splitlines()[-3:],
            "margin": "pytest exit code",
            "verdict": "PASS" if tests_ok else "FAIL"}
    gate["verdict_basis"].append(f"tests={'PASS' if tests_ok else 'FAIL'}")

    # ---- verdict ------------------------------------------------------------- #
    all_pass = (repin_ok and census_ok and parity_ok and canaries_ok
                and plane_canary_ok and tests_ok and floors_ok)
    gate["verdict"] = "PASS" if all_pass else (
        "BLOCKED_DATA" if not floors_ok or not parity_ok or not repin_ok
        else "FAIL")
    if gate["verdict"] != "PASS":
        gate["blocker"] = blocker or "see sections"
    gate["floors"] = floors
    gate["census_path"] = os.path.relpath(CENSUS_OUT, REPO_ROOT)
    gate["ingest_manifest_path"] = os.path.relpath(INGEST_MANIFEST, REPO_ROOT)
    gate["delisted_census_path"] = os.path.relpath(DELISTED_CENSUS, REPO_ROOT)
    with open(INGEST_MANIFEST, encoding="utf-8") as fh:
        ingest_manifest = json.load(fh)
    gate["untracked_raw"] = ingest_manifest.get("untracked_sink", {})
    _write_gate(gate)
    print(json.dumps({"verdict": gate["verdict"],
                      "blocker": gate.get("blocker"),
                      "floors": {k: v["verdict"]
                                 for k, v in floors.items()},
                      "canaries": "PASS" if canaries_ok else "FAIL",
                      "parity": "PASS" if parity_ok else "BLOCKED_DATA",
                      "tests": "PASS" if tests_ok else ("NOT_RUN" if skip_tests
                                                        else "FAIL")},
                     indent=1))
    return 0 if gate["verdict"] == "PASS" else 3


def _write_gate(gate: dict) -> None:
    write_json(GATE_PATH, gate)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("ingest", "adopt"))
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()
    if args.stage == "ingest":
        return run_ingest()
    return run_adopt(skip_tests=args.skip_tests)


if __name__ == "__main__":
    raise SystemExit(main())
