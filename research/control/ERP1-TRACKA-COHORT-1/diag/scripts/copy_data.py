"""DIAG data copy + sha verification — ERP1-TRACKA-COHORT-1 (diag lane).

OWNER instruction 2026-09-26, DIAGNOSTIC_OUTCOME_EXPOSED lane. Copies the
read-only M1 BID/ASK day corpora (window 2021-01-01..2026-06-30; 2026-07+
ignored per the diagnostic window law) from the two named sources into the
diag namespace, verifying EVERY copied file's sha256 against the SOURCE
manifest before trusting (the dispatch requires a 20-file sample; this
copy loop verifies all files and additionally reports the 20-file random
sample result explicitly, seed-pinned).

Sources (read-only; never written):
  EURUSD: .../FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/
          (M1/{BID,ASK}/*.bi5 + m1_manifest.json)
  GBPUSD: .../FX-MAJORS-SEARCH-V1/data_local/GBPUSD/
          (M1/{BID,ASK}/*.bi5 + m1_manifest.json)

Both manifests are schema fxm.m1_manifest@1 with keys "M1/{SIDE}/{date}.bi5".
Output: diag/data_local/{EURUSD,GBPUSD}/ (files + copied manifest)
        diag/data_local/derived/copy_verify_{PAIR}.json
Exit 2 on ANY sha mismatch (BLOCKED_DIAG_DATA).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

DIAG = Path(__file__).resolve().parent.parent          # .../ERP1-TRACKA-COHORT-1/diag
WIN_START, WIN_END = "2021-01-01", "2026-06-30"
SAMPLE_N = 20
SAMPLE_SEED = 20260926

SOURCES = {
    "EURUSD": Path(
        "/Users/hoangminhlong/my-quantitative/.worktrees/"
        "fx-rangefade-2m-shadow-v1/research/control/"
        "FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD"),
    "GBPUSD": Path(
        "/Users/hoangminhlong/my-quantitative/.worktrees/"
        "fx-majors-search-v1/integration/research/control/"
        "FX-MAJORS-SEARCH-V1/data_local/GBPUSD"),
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def copy_pair(pair: str) -> dict:
    src = SOURCES[pair]
    src_man_path = src / "m1_manifest.json"
    man = json.loads(src_man_path.read_text())
    assert man["schema"] == "fxm.m1_manifest@1" and man["pair"] == pair, \
        f"BLOCKED_DIAG_DATA unexpected manifest schema for {pair}"
    files = man["files"]

    dst = DIAG / "data_local" / pair
    rep = {
        "pair": pair,
        "source": str(src),
        "source_manifest_sha256": sha256_file(src_man_path),
        "window": [WIN_START, WIN_END],
        "manifest_entries_total": len(files),
        "in_window_entries": 0,
        "copied_files": 0,
        "copied_bytes": 0,
        "sha_verified_ok": 0,
        "sha_mismatches": [],
        "missing_on_disk": [],
        "outside_window_skipped": 0,
        "sample": {"n": SAMPLE_N, "seed": SAMPLE_SEED, "ok": 0,
                   "mismatches": []},
        "verdict": "COPY_FAIL",
    }

    for key, ent in sorted(files.items()):
        # key = "M1/{SIDE}/{date}.bi5"
        parts = key.split("/")
        if len(parts) != 3 or parts[0] != "M1" or parts[1] not in ("BID", "ASK"):
            raise SystemExit(f"BLOCKED_DIAG_DATA unexpected manifest key {key}")
        date = parts[2][:-4]
        if not (WIN_START <= date <= WIN_END):
            rep["outside_window_skipped"] += 1
            continue
        rep["in_window_entries"] += 1
        s = src / parts[0] / parts[1] / parts[2]
        if not s.exists():
            rep["missing_on_disk"].append(key)
            continue
        h = sha256_file(s)
        if h != ent.get("sha256"):
            rep["sha_mismatches"].append({"key": key,
                                          "expected": ent.get("sha256"),
                                          "measured": h})
            continue
        d = dst / parts[1]
        d.mkdir(parents=True, exist_ok=True)
        if not (d / parts[2]).exists():
            shutil.copy2(s, d / parts[2])
        rep["copied_files"] += 1
        rep["copied_bytes"] += ent.get("bytes", 0)
        rep["sha_verified_ok"] += 1

    # the dispatch-mandated 20-file sample, seed-pinned (subsumed by the
    # full verification above; reported explicitly for the letter of the law)
    import random
    rng = random.Random(SAMPLE_SEED)
    keys = [k for k in files
            if WIN_START <= k.split("/")[2][:-4] <= WIN_END]
    sample_keys = sorted(rng.sample(keys, min(SAMPLE_N, len(keys))))
    for key in sample_keys:
        p = dst / Path(*key.split("/")[1:])   # drop the "M1" component
        ok = p.exists() and sha256_file(p) == files[key]["sha256"]
        if ok:
            rep["sample"]["ok"] += 1
        else:
            rep["sample"]["mismatches"].append(key)

    # copy the manifest itself (bytes-identical; its sha is recorded)
    shutil.copy2(src_man_path, dst / "m1_manifest.json")
    got = sha256_file(dst / "m1_manifest.json")
    rep["copied_manifest_sha256_matches_source"] = got == rep["source_manifest_sha256"]

    rep["verdict"] = (
        "COPY_VERIFIED" if not rep["sha_mismatches"]
        and not rep["missing_on_disk"]
        and rep["sample"]["ok"] == min(SAMPLE_N, len(keys))
        and rep["copied_manifest_sha256_matches_source"]
        else "COPY_FAIL")
    out = DIAG / "data_local" / "derived" / f"copy_verify_{pair}.json"
    out.write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in (
        "pair", "verdict", "copied_files", "sha_verified_ok",
        "sha_mismatches", "missing_on_disk", "outside_window_skipped",
        "sample", "source_manifest_sha256")}, indent=1))
    return rep


def main() -> int:
    ok = True
    for pair in SOURCES:
        rep = copy_pair(pair)
        ok = ok and rep["verdict"] == "COPY_VERIFIED"
    if not ok:
        print("BLOCKED_DIAG_DATA: corpus sha mismatch", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
