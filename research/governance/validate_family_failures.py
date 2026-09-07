"""Validator for research/wayfinder/FAMILY_FAILURES.jsonl — the failure memory.

Schema (family_failures/entry@1), one JSON object per line:

  schema              must equal "family_failures/entry@1"
  cycle_id            str, non-empty
  asset               one of crypto|stocks|forex|sprint
  family_id           str, unique across the registry
  family_title        str
  status              CLOSED | TERMINAL_PENDING
  verdict_class       SCIENTIFIC_REJECTION | DATA_BLOCK | SELECTION_REJECTION |
                      TECHABORT | PROCESS_INCIDENT | NOT_RUN_SUPERSEDED | null
                      (null iff status == TERMINAL_PENDING)
  no_quality_evidence bool — MUST be true iff verdict_class in
                      {TECHABORT, NOT_RUN_SUPERSEDED}: those classes carry no
                      evidence about family quality either way (owner
                      amendment 2026-09-07)
  primary_failure     {"code": ..., "detail": ...} — exactly one decisive
                      failure; null iff TERMINAL_PENDING; never guessed —
                      unrecoverable => code UNKNOWN_NOT_RECOVERABLE
  secondary_failures  list of {"code","detail"} (may be empty)
  measured_summary    str — the numbers the verdict rests on
  evidence            {"terminal_sha": 40-hex | null, "evidence_path": str|null,
                       "ledger_row": str} — at least one non-null
  unknown_fields      list of str — names of fields left unknown on purpose
  recorded_by / recorded_utc

Exit codes: 0 = PASS, 1 = FAIL (errors printed per line).

--verify <repo-root> additionally resolves every entry that carries both
terminal_sha and evidence_path against the git object store
(git cat-file -e <sha>:<path>) so a registry row can never silently point
at an artifact that does not exist at the cited terminal.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "family_failures/entry@1"

VERDICT_CLASSES = {
    "SCIENTIFIC_REJECTION",
    "DATA_BLOCK",
    "SELECTION_REJECTION",
    "TECHABORT",
    "PROCESS_INCIDENT",
    "NOT_RUN_SUPERSEDED",
}

# Base codes from FAMILY_PIPELINE.md section 9, plus the extensible codes
# added at seeding (Lead changelog note, 2026-09-07): SOURCE_ACCESS_OR_
# LICENSE_BLOCKED, COST_KERNEL_VIOLATION, RULE_TRANSFER_FAILED.
SIGNATURE_CODES = {
    "EXPECTANCY_NONPOSITIVE",
    "PF_BELOW_THRESHOLD",
    "STRESS_TIER_FAIL",
    "FOLD_CONCENTRATION_OVER_LIMIT",
    "FOLD_POPULATION_UNDER",
    "CONTROL_REPRODUCED_MECHANISM",
    "CONTROL_OUTEARNED_ANCHOR",
    "MECHANISM_SANITY_NULL",
    "ANCESTRY_RHO_BLOCK",
    "CONTROL_IDENTIFIABILITY_FAIL",
    "COVERAGE_INSUFFICIENT",
    "PIT_UNEVIDENCED",
    "DATA_AUTHORITY_INVALIDATED",
    "COST_DOMINATED",
    "MDD_OVER_CEILING",
    "INCREMENTAL_ALPHA_NEGATIVE",
    "ETF_SHARE_SECTOR_DROWNING",
    "SPY_EXCESS_ZERO_FOLDS",
    "ADAPTER_WEIGHT_INFEASIBLE",
    "VACUOUS_DRYRUN",
    "RESOURCE_QUOTA_BLOCK",
    "DIAGNOSTIC_CONTRACT_GAP",
    # extensible additions (seeded 2026-09-07)
    "SOURCE_ACCESS_OR_LICENSE_BLOCKED",
    "COST_KERNEL_VIOLATION",
    "RULE_TRANSFER_FAILED",
    "PROCESS_INCIDENT_DETAIL",
    "UNKNOWN_NOT_RECOVERABLE",
}

NO_QUALITY_CLASSES = {"TECHABORT", "NOT_RUN_SUPERSEDED"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_FIELDS = (
    "schema",
    "cycle_id",
    "asset",
    "family_id",
    "family_title",
    "status",
    "verdict_class",
    "no_quality_evidence",
    "primary_failure",
    "secondary_failures",
    "measured_summary",
    "evidence",
    "unknown_fields",
    "recorded_by",
    "recorded_utc",
)


def _check_failure(obj, errors, where):
    if not isinstance(obj, dict):
        errors.append(f"{where}: must be an object")
        return
    code = obj.get("code")
    if code not in SIGNATURE_CODES:
        errors.append(f"{where}: unknown signature code {code!r}")
    if not isinstance(obj.get("detail"), str) or not obj["detail"]:
        errors.append(f"{where}: detail must be a non-empty string")


def validate_entry(entry, line_no):
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"line {line_no}: missing field {field!r}")
    if errors:
        return errors
    if entry["schema"] != SCHEMA:
        errors.append(f"line {line_no}: schema must be {SCHEMA!r}")
    status = entry["status"]
    if status not in {"CLOSED", "TERMINAL_PENDING"}:
        errors.append(f"line {line_no}: bad status {status!r}")
    vc = entry["verdict_class"]
    if status == "TERMINAL_PENDING":
        if vc is not None:
            errors.append(f"line {line_no}: TERMINAL_PENDING must have null verdict_class")
        if entry["primary_failure"] is not None:
            errors.append(f"line {line_no}: TERMINAL_PENDING must not finalize failure fields")
        if entry["secondary_failures"]:
            errors.append(f"line {line_no}: TERMINAL_PENDING must not carry secondary failures")
        if entry["no_quality_evidence"] is not True:
            errors.append(f"line {line_no}: TERMINAL_PENDING must set no_quality_evidence=true")
    else:
        if vc not in VERDICT_CLASSES:
            errors.append(f"line {line_no}: bad verdict_class {vc!r}")
        expected_flag = vc in NO_QUALITY_CLASSES
        if entry["no_quality_evidence"] is not expected_flag:
            errors.append(
                f"line {line_no}: no_quality_evidence must be {expected_flag} "
                f"for verdict_class {vc}"
            )
        if entry["primary_failure"] is None:
            errors.append(f"line {line_no}: CLOSED entry requires primary_failure")
        else:
            _check_failure(entry["primary_failure"], errors, f"line {line_no}: primary_failure")
    for i, sec in enumerate(entry["secondary_failures"]):
        _check_failure(sec, errors, f"line {line_no}: secondary_failures[{i}]")
    ev = entry["evidence"]
    if not isinstance(ev, dict):
        errors.append(f"line {line_no}: evidence must be an object")
    else:
        if not (ev.get("evidence_path") or ev.get("ledger_row")):
            errors.append(f"line {line_no}: evidence needs evidence_path or ledger_row")
        sha = ev.get("terminal_sha")
        if sha is not None and (not isinstance(sha, str) or not SHA_RE.match(sha)):
            errors.append(f"line {line_no}: terminal_sha must be 40-hex or null")
        if sha is None and "terminal_sha" not in entry["unknown_fields"]:
            errors.append(
                f"line {line_no}: null terminal_sha must be declared in unknown_fields"
            )
    if entry["asset"] not in {"crypto", "stocks", "forex", "sprint"}:
        errors.append(f"line {line_no}: bad asset {entry['asset']!r}")
    return errors


def load_registry(path):
    entries, errors = [], []
    seen = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON ({exc})")
            continue
        errs = validate_entry(entry, line_no)
        errors.extend(errs)
        fid = entry.get("family_id")
        if fid in seen:
            errors.append(f"line {line_no}: duplicate family_id {fid!r} (first at {seen[fid]})")
        seen[fid] = line_no
        entries.append(entry)
    return entries, errors


def verify_against_git(entries, repo_root):
    errors = []
    for i, entry in enumerate(entries, 1):
        ev = entry.get("evidence") or {}
        sha, ev_path = ev.get("terminal_sha"), ev.get("evidence_path")
        if not sha or not ev_path:
            continue
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "-e", f"{sha}:{ev_path}"],
            capture_output=True,
        )
        if proc.returncode != 0:
            errors.append(
                f"entry {entry.get('family_id')}: {ev_path} not found at {sha[:7]}"
            )
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--verify", type=Path, metavar="REPO_ROOT", default=None)
    args = parser.parse_args(argv)

    entries, errors = load_registry(args.registry)
    if args.verify:
        errors.extend(verify_against_git(entries, args.verify))
    for err in errors:
        print(f"FAIL {err}", file=sys.stderr)
    print(
        f"family_failures: {len(entries)} entries, "
        f"{len(errors)} errors -> {'PASS' if not errors else 'FAIL'}"
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
