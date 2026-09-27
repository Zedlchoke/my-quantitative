"""Run lane_x book construction end-to-end, deterministically.

Usage:
    .venv/bin/python -m engine_x.run_books --worktree <integration root> --out <dir>

Writes: A1_anchor_book.jsonl.gz, A1_N2_book.jsonl.gz, A2_anchor_book.jsonl.gz,
exclusions per arm, census.json, run_manifest.json (input digests, sha of
every output).  Byte-determinism: sorted keys, sorted records, gzip mtime 0.
No aggregate of trade returns is computed anywhere (R2-6): populations,
exclusion counts and per-event prices only.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys

from .a1_books import build_a1_book
from .a2_books import build_a2_book
from .divsplits import ExDateIndex
from .panel import PanelStore

STAGED = ".staging_eventmech"
PANEL_DIR = os.path.join(STAGED, "integration", "data_raw", "stocks_ng6_eod")
DIV_DIR = os.path.join(STAGED, "integration", ".staging_sec_v13", "eodhd_div")
SPLITS_DIR = os.path.join(STAGED, "integration", ".staging_sec_v13", "eodhd_splits")
FORM4_XML_DIR = os.path.join(STAGED, "integration", ".staging_sec_v13", "form4_xml")
FORM4_STREAM = os.path.join(STAGED, "integration", ".staging_sec_v13", "form4_stream.jsonl")
A1_EVENTS = os.path.join(STAGED, "a1_events.jsonl")
N4_MAP = os.path.join(STAGED, "n4_map_v1.jsonl")
STAGED_SUMS = os.path.join(STAGED, "SHA256SUMS.staged.txt")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pins() -> dict:
    """Fail-closed digest check of the pinned staged artifacts (P-13 pattern)."""
    pins = {}
    for line in open(STAGED_SUMS):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, rel = line.partition("  ")
        pins[rel.strip()] = digest
    checked = {}
    for rel in (A1_EVENTS, N4_MAP, FORM4_STREAM):
        got = sha256_file(rel)
        want = pins.get(rel)
        checked[rel] = {"sha256": got, "pin": want, "match": (want is None or got == want)}
        if want is not None and got != want:
            raise SystemExit(f"DIGEST FAIL {rel}: {got} != {want}")
    return checked


def write_jsonl_gz(path: str, rows: list[dict]) -> None:
    payload = "".join(
        json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n" for r in rows
    ).encode("utf-8")
    with open(path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write(payload)


def write_json(path: str, obj) -> None:
    with open(path, "w") as fh:
        json.dump(obj, fh, sort_keys=True, indent=1)
        fh.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    os.chdir(args.worktree)

    pins = verify_pins()
    os.makedirs(args.out, exist_ok=True)

    panels = PanelStore(PANEL_DIR)
    exdates = ExDateIndex(DIV_DIR, SPLITS_DIR)

    # ---------------- A1 ----------------
    a1_anchor = build_a1_book(A1_EVENTS, panels, exdates, "anchor")
    a1_n2 = build_a1_book(A1_EVENTS, panels, exdates, "n2")

    # ---------------- A2 ----------------
    a2_records, a2_census, a2_excluded, a2_droplog = build_a2_book(
        FORM4_STREAM, FORM4_XML_DIR, N4_MAP, panels, exdates)

    # ---------------- persist ----------------
    outputs = {}
    for name, rows in (
        ("A1_anchor_book.jsonl.gz", a1_anchor.records),
        ("A1_N2_book.jsonl.gz", a1_n2.records),
        ("A2_anchor_book.jsonl.gz", a2_records),
    ):
        p = os.path.join(args.out, name)
        write_jsonl_gz(p, rows)
        outputs[name] = {"sha256": sha256_file(p), "records": len(rows)}

    exclusions = {
        "A1_anchor": {"excluded": a1_anchor.excluded, "dropped": a1_anchor.dropped},
        "A1_N2": {"excluded": a1_n2.excluded, "dropped": a1_n2.dropped},
        "A2_anchor": {"excluded": a2_excluded, "dropped": [], "join_drop_log": a2_droplog},
    }
    p = os.path.join(args.out, "exclusions.json.gz")
    write_jsonl_gz(p, [{"arm": k, **v} for k, v in sorted(exclusions.items())])
    outputs["exclusions.json.gz"] = {"sha256": sha256_file(p)}

    census = {
        "A1_anchor": a1_anchor.census,
        "A1_N2": a1_n2.census,
        "A2_anchor": a2_census,
    }
    # R2-2 CONTAMINATION_HIGH: CA exclusions > 40% of any fold's candidate events
    contamination = {}
    for arm, run_census in (("A1_anchor", a1_anchor.census),
                            ("A1_N2", a1_n2.census),
                            ("A2_anchor", a2_census)):
        per_fold_ca: dict[str, int] = {}
        src = exclusions[arm]["excluded"]
        for row in src:
            if row.get("reason") == "CA_EXCLUSION":
                per_fold_ca[row.get("fold", "?")] = per_fold_ca.get(row.get("fold", "?"), 0) + 1
        flags = {}
        for fold, n_ca in sorted(per_fold_ca.items()):
            booked = run_census["booked_by_fold"].get(fold, 0)
            denom = booked + n_ca  # fold candidates that reached CA check
            if denom and n_ca / denom > 0.40:
                flags[fold] = {"ca_excluded": n_ca, "denominator": denom,
                               "share": round(n_ca / denom, 4)}
        contamination[arm] = flags or "NONE"
    census["contamination_high_flags"] = contamination

    write_json(os.path.join(args.out, "census.json"), census)

    manifest = {
        "lane": "X (independent implementation)",
        "cycle": "EVENT-MECHANISMS-V1",
        "gate": "G5",
        "input_pins": pins,
        "panel_dir": PANEL_DIR,
        "params": {
            "A1_hold": 5, "A1_anchor_strata": ["S1", "S3", "S4"],
            "A1_N2_strata": ["S2"], "A2_hold": 10,
            "A2_buy_value_floor_usd": 100000.0,
            "direction_rule_A1": "first session close strictly after acceptance; entry next session open",
            "direction_rule_A2": "first session open strictly after acceptance",
            "CA_window": "inclusive [entry..exit], calendar-interval ex-date compare",
            "bar_laws": "B1 raw-close ratio >= 9 both directions; X1 volume 0; exit rolls forward",
        },
        "outputs": outputs,
        "r2_6_note": "no aggregate of trade returns computed; decision/fill records + population counts only",
    }
    write_json(os.path.join(args.out, "run_manifest.json"), manifest)
    print(json.dumps({k: v["records"] for k, v in outputs.items() if "records" in v}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
