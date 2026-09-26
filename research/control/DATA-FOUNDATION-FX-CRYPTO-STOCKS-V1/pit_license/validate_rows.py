#!/usr/bin/env python
"""validate_rows.py — stdlib-only validator for DFV1 authority rows.

Contract: authority_row_schema.json (dfv1_authority_row@1), instantiated from
plans/PLAN_data_foundation_fx_crypto_stocks_v1.md section 5 + COMMON.md.

Usage:
    .venv/bin/python validate_rows.py <inventory.jsonl> [schema.json]

Defaults: schema.json is resolved next to this file. Exit code 0 = all rows
valid; 1 = at least one row invalid (each violation printed to stdout).
No third-party imports; no network; no filesystem writes.
"""
from __future__ import annotations

import json
import os
import re
import sys

SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA = os.path.join(SCHEMA_DIR, "authority_row_schema.json")

ASSET_CLASSES = ["forex", "crypto", "stocks", "rates", "vol", "commodities", "shared"]
MANIFEST_VERIFIES = [
    "ALL_MATCH", "MISMATCH", "NO_MANIFEST", "NOT_RUN",
    "SAMPLED", "INHERITED_NOT_REHASHED_LIVE_OWNER",
]
MEASURED_FROM = ["bytes", "metadata", "stated"]
STATUSES = [
    "AVAILABLE_VALIDATED", "AVAILABLE_UNVALIDATED",
    "BLOCKED_LICENSE", "BLOCKED_ACCOUNT", "BLOCKED_COST",
    "BLOCKED_STORAGE", "BLOCKED_TRANSPORT", "NOT_RUN",
]
EXPOSURES = ["OUTCOME_EXPOSED", "UNOPENED", "MIXED", "NOT_APPLICABLE"]
EVENT_TIME = ["present", "absent", "approx"]
REPRODUCIBLE = ["yes", "partial", "no"]

TOP_REQUIRED = [
    "dataset_id", "asset_class", "source", "local_presence", "coverage",
    "timing", "timezone", "quality", "economics", "costs", "status",
    "status_evidence",
]
DATASET_ID_RE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


def _err(rows_errors, line_no, dataset_id, msg):
    rows_errors.append(f"line {line_no} [{dataset_id}]: {msg}")


def validate_row(row, line_no, errors, seen_ids):
    dsid = row.get("dataset_id", "<missing>")

    for field in TOP_REQUIRED:
        if field not in row:
            _err(errors, line_no, dsid, f"missing required field '{field}'")
    extra = set(row) - set(TOP_REQUIRED) - {"outcome_exposure"}
    if extra:
        _err(errors, line_no, dsid, f"unknown top-level fields: {sorted(extra)}")

    if not isinstance(row.get("dataset_id"), str) or not DATASET_ID_RE.match(
        row.get("dataset_id", "")
    ):
        _err(errors, line_no, dsid, "dataset_id must be snake_case")
    if row.get("dataset_id") in seen_ids:
        _err(errors, line_no, dsid, "duplicate dataset_id in file (R6)")
    seen_ids.add(row.get("dataset_id"))

    if row.get("asset_class") not in ASSET_CLASSES:
        _err(errors, line_no, dsid, f"asset_class must be one of {ASSET_CLASSES}")

    src = row.get("source") or {}
    for f in ("provider", "channel", "license_ruling"):
        if not isinstance(src.get(f), str) or not src.get(f):
            _err(errors, line_no, dsid, f"source.{f} required non-empty string")
    extra = set(src) - {"provider", "channel", "terms_url", "license_ruling"}
    if extra:
        _err(errors, line_no, dsid, f"unknown source fields: {sorted(extra)}")

    lp = row.get("local_presence") or {}
    for f in ("paths", "bytes", "manifest_path", "manifest_verify"):
        if f not in lp:
            _err(errors, line_no, dsid, f"local_presence.{f} required")
    if not isinstance(lp.get("paths"), list) or not all(
        isinstance(p, str) for p in lp.get("paths", [])
    ):
        _err(errors, line_no, dsid, "local_presence.paths must be a list of strings")
    if not isinstance(lp.get("bytes"), int) or isinstance(lp.get("bytes"), bool) or lp.get("bytes", 0) < 0:
        _err(errors, line_no, dsid, "local_presence.bytes must be a non-negative integer")
    if lp.get("manifest_verify") not in MANIFEST_VERIFIES:
        _err(errors, line_no, dsid, f"manifest_verify must be one of {MANIFEST_VERIFIES}")
    if lp.get("paths") and lp.get("bytes") == 0:
        _err(errors, line_no, dsid, "R4: paths non-empty but bytes == 0 (measure the corpus)")

    cov = row.get("coverage") or {}
    for f in ("instruments", "start", "end", "resolution", "measured_from"):
        if f not in cov:
            _err(errors, line_no, dsid, f"coverage.{f} required")
    if not isinstance(cov.get("instruments"), list) or not all(
        isinstance(i, str) for i in cov.get("instruments", [])
    ):
        _err(errors, line_no, dsid, "coverage.instruments must be a list of strings")
    if cov.get("measured_from") not in MEASURED_FROM:
        _err(errors, line_no, dsid, f"coverage.measured_from must be one of {MEASURED_FROM}")

    tim = row.get("timing") or {}
    for f in ("event_time", "available_at", "ingested_at", "revision_policy"):
        if f not in tim:
            _err(errors, line_no, dsid, f"timing.{f} required")
    if tim.get("event_time") not in EVENT_TIME:
        _err(errors, line_no, dsid, f"timing.event_time must be one of {EVENT_TIME}")

    tz = row.get("timezone") or {}
    for f in ("declared", "dst_evidence"):
        if f not in tz:
            _err(errors, line_no, dsid, f"timezone.{f} required")

    q = row.get("quality") or {}
    for f in ("missingness", "gaps", "duplicates", "cross_source_check"):
        if f not in q:
            _err(errors, line_no, dsid, f"quality.{f} required")

    eco = row.get("economics") or {}
    for f in ("hypotheses_opened", "prior_kill_fixed", "falsifying_control"):
        if f not in eco:
            _err(errors, line_no, dsid, f"economics.{f} required")
    if not isinstance(eco.get("hypotheses_opened"), list):
        _err(errors, line_no, dsid, "economics.hypotheses_opened must be a list")

    cost = row.get("costs") or {}
    for f in ("acquisition", "storage_bytes", "api_limits", "reproducible"):
        if f not in cost:
            _err(errors, line_no, dsid, f"costs.{f} required")
    if not isinstance(cost.get("storage_bytes"), int) or isinstance(cost.get("storage_bytes"), bool) or cost.get("storage_bytes", 0) < 0:
        _err(errors, line_no, dsid, "costs.storage_bytes must be a non-negative integer")
    if cost.get("reproducible") not in REPRODUCIBLE:
        _err(errors, line_no, dsid, f"costs.reproducible must be one of {REPRODUCIBLE}")

    if row.get("status") not in STATUSES:
        _err(errors, line_no, dsid, f"status must be one of {STATUSES}")
    if not isinstance(row.get("status_evidence"), str) or not row.get("status_evidence"):
        _err(errors, line_no, dsid, "status_evidence required non-empty string")

    # Cross-field rules
    if row.get("status") == "AVAILABLE_VALIDATED":
        if lp.get("manifest_verify") not in (
            "ALL_MATCH", "SAMPLED", "INHERITED_NOT_REHASHED_LIVE_OWNER"
        ):
            _err(errors, line_no, dsid,
                 "R1: AVAILABLE_VALIDATED requires manifest_verify in "
                 "[ALL_MATCH, SAMPLED, INHERITED_NOT_REHASHED_LIVE_OWNER]")
        if cov.get("measured_from") != "bytes":
            _err(errors, line_no, dsid,
                 "R1: AVAILABLE_VALIDATED requires coverage.measured_from == 'bytes' "
                 "(this-cycle re-measurement; file existence never implies PASS)")
    if str(row.get("status", "")).startswith("BLOCKED_"):
        ev = row.get("status_evidence", "")
        if "owner action" not in ev and "OWNER ACTION" not in ev and "owner-action" not in ev:
            _err(errors, line_no, dsid,
                 "R2: BLOCKED_* status_evidence must name the exact owner action that unblocks")
    if lp.get("manifest_verify") == "SAMPLED" and "sample" not in row.get("status_evidence", "").lower():
        _err(errors, line_no, dsid,
             "SAMPLED requires the sample size stated in status_evidence")
    if lp.get("manifest_verify") == "INHERITED_NOT_REHASHED_LIVE_OWNER":
        ev = row.get("status_evidence", "")
        if "INHERITED" not in ev and "inherited" not in ev:
            _err(errors, line_no, dsid,
                 "R3: INHERITED_NOT_REHASHED_LIVE_OWNER requires status_evidence naming the live owner + committed manifest")

    if "outcome_exposure" in row and row["outcome_exposure"] not in EXPOSURES:
        _err(errors, line_no, dsid, f"outcome_exposure must be one of {EXPOSURES}")
    if row.get("outcome_exposure") == "UNOPENED":
        ev = row.get("status_evidence", "") + " " + json.dumps(tim)
        if "seal" not in ev.lower() and "sealed" not in ev.lower() and "sealed" not in json.dumps(row).lower() and "prospective" not in ev.lower() and "holdout" not in ev.lower() and "UNOPENED" not in ev:
            _err(errors, line_no, dsid,
                 "R5: UNOPENED rows must cite the seal (S1 / sealed holdout manifest / prospective-only contract)")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    # Schema file is documentation-of-record; the enums live in this file by
    # construction (stdlib jsonschema is not available stdlib-only). Loading it
    # proves it parses; drift between the two files fails this load only if the
    # file is malformed.
    schema_path = argv[2] if len(argv) > 2 else DEFAULT_SCHEMA
    with open(schema_path, "r", encoding="utf-8") as fh:
        json.load(fh)

    errors = []
    n_rows = 0
    seen_ids = set()
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON ({exc})")
                continue
            if not isinstance(row, dict):
                errors.append(f"line {line_no}: row is not a JSON object")
                continue
            n_rows += 1
            validate_row(row, line_no, errors, seen_ids)

    if errors:
        print(f"INVALID: {n_rows} row(s), {len(errors)} violation(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"VALID: {n_rows} row(s) conform to dfv1_authority_row@1 ({os.path.basename(path)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
