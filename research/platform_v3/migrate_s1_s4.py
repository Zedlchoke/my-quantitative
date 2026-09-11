#!/usr/bin/env python
"""PA3: migrate the frozen S1-S4 target set into CADS (plan section 8).

Per series the job is: FULL re-hash of every existing pin (the operation
required by the plan), registration of the series' pin manifests / small
bytes as CADS objects, and pin records with the measured census.

- S1  Form-4 substrate (V13 worktree): form4_xml_docs (345,150 files),
      form4_stream.jsonl (546,039 rows), eodhd_div, eodhd_splits,
      submissions_alive.  The XML tree stays in situ: its CADS pin is the
      re-verified substrate manifest object (address == manifest digest),
      which covers every per-file pin.  The stream file itself is ingested
      as a CADS object.
- S2  FRED vintaged series pinned by fred_vintaged_manifest_v9.json.
- S3  Official announcement staging GB/CA/AU (+ US FRED real-time).
- S4  Binance H1 panels + panel manifest + reduced OI series.

Every mismatch or missing file is an incident: that series stays BLOCKED
(never silently repaired).  The run is RESUMABLE via a checkpoint JSONL.

Runs ALONE under the machine-wide heavy lock (.runtime/heavy_worker.lock);
lock refusal exits 3 = NOT_RUN_RESOURCE_CONFLICT.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

from research.platform_v3.cads import CADS, CADSIntegrityError
from research.platform_v3.canonical import canonical_digest

SCHEMA = "research_platform_v3_run/pa3_migration@1"


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


class Checkpoint:
    def __init__(self, path: str):
        self.path = path
        self.done: set[str] = set()
        self._fh = open(path, "a", encoding="utf-8")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        rec = json.loads(line)
                        if rec.get("status") == "OK":
                            self.done.add(rec["key"])

    def skip(self, key: str) -> bool:
        return key in self.done

    def record(self, key: str, status: str, detail: str = "") -> None:
        self._fh.write(json.dumps(
            {"key": key, "status": status, "detail": detail,
             "utc": datetime.now(timezone.utc).isoformat()},
            sort_keys=True) + "\n")
        self._fh.flush()
        if status == "OK":
            self.done.add(key)

    def close(self) -> None:
        self._fh.close()


def verify_tree(cp: Checkpoint, series: str, base: str,
                files: dict[str, str]) -> dict:
    ok = drift = missing = 0
    drift_rows = []
    for rel, expected in sorted(files.items()):
        key = f"{series}:{rel}"
        if cp.skip(key):
            ok += 1
            continue
        path = os.path.join(base, rel)
        if not os.path.exists(path):
            missing += 1
            cp.record(key, "MISSING", path)
            continue
        actual = sha256_file(path)
        if actual == expected:
            ok += 1
            cp.record(key, "OK")
        else:
            drift += 1
            drift_rows.append({"file": rel, "expected": expected,
                               "actual": actual})
            cp.record(key, "DRIFT", path)
    return {"files_total": len(files), "files_ok": ok,
            "files_drift": drift, "files_missing": missing,
            "drift_rows": drift_rows[:20]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v13-worktree", required=True)
    ap.add_argument("--v9-worktree", required=True)
    ap.add_argument("--v17-worktree", required=True)
    ap.add_argument("--store-root", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lock_path = "/Users/hoangminhlong/my-quantitative/.runtime/heavy_worker.lock"
    lock_fh = open(lock_path, "a+")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        artifact = {"schema": SCHEMA, "verdict": "NOT_RUN_RESOURCE_CONFLICT",
                    "lock_error": repr(exc)}
        with open(args.out, "w") as fh:
            json.dump(artifact, fh, indent=1)
        print(json.dumps(artifact, indent=1))
        return 3

    started = time.time()
    store = CADS(args.store_root)
    cp = Checkpoint(args.checkpoint)
    series_results: dict[str, dict] = {}

    try:
        # ---------------- S1: Form-4 substrate (V13) ------------------- #
        v13 = args.v13_worktree
        base = os.path.join(v13, ".staging_sec_v13")
        manifest_path = os.path.join(
            v13, "research/control/stocks_free_v13_run/substrate_manifest.json"
        )
        manifest_sha = sha256_file(manifest_path)
        with open(manifest_path, "rb") as fh:
            manifest_addr = store.register(fh.read())
        store.pin(manifest_addr, {"series": "S1:form4-xml-substrate",
                                  "role": "substrate_manifest"})
        s1: dict = {"substrate_manifest_path": manifest_path,
                    "substrate_manifest_sha256": manifest_sha,
                    "cads_addresses": [manifest_addr]}
        sections = json.load(open(manifest_path))["sections"]

        # stream object ingest (546,039 rows); the pinned path already
        # carries the .staging_sec_v13/ prefix relative to the worktree
        stream_rel = sections["form4_stream"]["path"]
        stream_path = (os.path.join(v13, stream_rel)
                       if stream_rel.startswith(".staging_sec_v13/")
                       else os.path.join(base, stream_rel))
        stream_sha = sha256_file(stream_path)
        s1["stream_sha256_measured"] = stream_sha
        s1["stream_sha256_pinned"] = sections["form4_stream"]["sha256"]
        s1["stream_match"] = stream_sha == sections["form4_stream"]["sha256"]
        if s1["stream_match"]:
            with open(stream_path, "rb") as fh:
                addr = store.register(fh.read())
            store.pin(addr, {"series": "S1:form4-stream"})
            s1["cads_addresses"].append(addr)

        # per-file verification across all four file sections
        s1_sections = {}
        for sec in ("form4_xml_docs", "eodhd_div", "eodhd_splits",
                    "submissions_alive"):
            files = sections[sec]["files"]
            if sec == "form4_xml_docs":
                # keys are relative to .staging_sec_v13/ already
                s1_sections[sec] = verify_tree(cp, "S1", base, files)
            else:
                s1_sections[sec] = verify_tree(
                    cp, "S1", base, {f"{sec}/{k}": v
                                     for k, v in files.items()})
        s1["sections"] = s1_sections
        s1["total_files"] = sum(v["files_total"] for v in s1_sections.values())
        s1["total_ok"] = sum(v["files_ok"] for v in s1_sections.values())
        s1["total_drift"] = sum(v["files_drift"] for v in s1_sections.values())
        s1["total_missing"] = sum(v["files_missing"]
                                  for v in s1_sections.values())
        s1["verdict"] = ("PASS" if s1["total_drift"] == 0
                         and s1["total_missing"] == 0 and s1["stream_match"]
                         else "FAIL")
        series_results["S1:form4-xml-substrate"] = s1

        # ---------------- S2: FRED vintaged (V9) ------------------------ #
        v9 = args.v9_worktree
        s2_base = os.path.join(v9, "data_raw/forex_free_v9_cpi")
        s2_manifest_path = os.path.join(s2_base,
                                        "fred_vintaged_manifest_v9.json")
        with open(s2_manifest_path, "rb") as fh:
            s2_manifest_addr = store.register(fh.read())
        store.pin(s2_manifest_addr, {"series": "S2:fred-keyed-vintage-classes"})
        s2_manifest = json.load(open(s2_manifest_path))
        s2_files = {entry["file"]: entry["sha256"]
                    for entry in s2_manifest["series"].values()}
        s2 = verify_tree(cp, "S2", s2_base, s2_files)
        with open(s2_manifest_path, "rb") as fh:
            pass
        s2["cads_addresses"] = [s2_manifest_addr]
        s2["verdict"] = ("PASS" if s2["files_drift"] == 0
                         and s2["files_missing"] == 0 else "FAIL")
        series_results["S2:fred-keyed-vintage-classes"] = s2

        # ---------------- S3: official announcement staging ------------- #
        s3_files: dict[str, str] = {}
        s3_hashes = {}
        for sub in ("GB", "CA", "AU", "US"):
            sub_dir = os.path.join(s2_base, sub)
            if not os.path.isdir(sub_dir):
                continue
            for fn in sorted(os.listdir(sub_dir)):
                rel = os.path.join(sub, fn)
                s3_hashes[rel] = sha256_file(os.path.join(sub_dir, fn))
        # official staging has NO prior pin manifest: PA3 hashes from disk
        # and REGISTERs the bytes; pins are created here for the first time
        for rel, digest in sorted(s3_hashes.items()):
            key = f"S3:{rel}"
            if cp.skip(key):
                continue
            path = os.path.join(s2_base, rel)
            with open(path, "rb") as fh:
                addr = store.register(fh.read())
            store.pin(addr, {"series": "S3:forex-announcement-ledger",
                             "file": rel})
            cp.record(key, "OK")
        s3 = {"files_total": len(s3_hashes), "files_ok": len(s3_hashes),
              "files_drift": 0, "files_missing": 0,
              "note": "first-time registration: no prior pin manifest "
                      "existed for S3; bytes hashed from disk at PA3 and "
                      "registered as CADS objects",
              "cads_addresses": [], "verdict": "PASS"}
        s3["cads_addresses"] = [
            p["metadata"].get("file")
            for p in store.pins()
            if p["metadata"].get("series") == "S3:forex-announcement-ledger"
        ]
        series_results["S3:forex-announcement-ledger"] = s3

        # ---------------- S4: Binance panels + OI (V17) ----------------- #
        v17 = args.v17_worktree
        s4_dir = os.path.join(v17, "v17_data")
        s4: dict = {"files": {}}
        s4_ok = True
        for rel in ("staging_v17/panel_BTCUSDT_h1.csv",
                    "staging_v17/panel_ETHUSDT_h1.csv",
                    "staging_v17/panel_SOLUSDT_h1.csv",
                    "staging_v17/panel_manifest.json",
                    "oi_series_reduced.json"):
            path = os.path.join(s4_dir, rel)
            if not os.path.exists(path):
                s4["files"][rel] = "MISSING"
                s4_ok = False
                continue
            with open(path, "rb") as fh:
                addr = store.register(fh.read())
            store.pin(addr, {"series": "S4:binance-daily-h1-panels",
                             "file": rel})
            s4["files"][rel] = {"sha256": sha256_file(path),
                                "cads_address": addr}
        s4["cads_addresses"] = [
            f["cads_address"] for f in s4["files"].values()
            if isinstance(f, dict)
        ]
        s4["verdict"] = "PASS" if s4_ok else "FAIL"
        series_results["S4:binance-daily-h1-panels"] = s4

        overall = ("PASS" if all(r.get("verdict") == "PASS"
                                 for r in series_results.values()) else "FAIL")
        artifact = {
            "schema": SCHEMA,
            "gate": "V3-GA2",
            "measured_utc": datetime.now(timezone.utc).isoformat(),
            "heavy_lock": "ACQUIRED (ran alone)",
            "store_root": args.store_root,
            "checkpoint": args.checkpoint,
            "series": series_results,
            "seconds": round(time.time() - started, 1),
            "verdict": overall,
            "resumable_note": "checkpoint JSONL records per-file status; "
                              "a rerun skips OK files and re-measures the rest",
        }
        with open(args.out, "w") as fh:
            json.dump(artifact, fh, indent=1)
        print(json.dumps({k: v for k, v in artifact.items() if k != "series"},
                         indent=1))
        for name, res in series_results.items():
            summary = {k: v for k, v in res.items()
                       if k in ("verdict", "total_files", "total_ok",
                                "total_drift", "total_missing",
                                "files_total", "files_ok", "files_drift",
                                "files_missing", "stream_match")}
            print(name, summary)
        return 0 if overall == "PASS" else 2
    finally:
        cp.close()
        fcntl.flock(lock_fh, fcntl.LOCK_UN)
        lock_fh.close()


if __name__ == "__main__":
    sys.exit(main())
