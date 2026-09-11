"""Tier-R availability + zero-mutation check for legacy cycle-state sources.

Reads the REAL LEGACY_SOURCES of research/governance/legacy_adapters.py under
main_repo_root() and records, per source: availability, size, sha256 before
and after a full adapter read (zero-mutation proof), and any read/parse
error. Writes a JSON artifact (--out PATH; printed to stdout when omitted).

Verdicts and exit codes (also recorded inside the artifact):
  0  PASS                     every declared source present, readable, and
                              provably unmutated by the read
  1  FAIL                     at least one PRESENT source is unreadable or
                              invalid (or bytes mutated during the read)
  3  NOT_RUN_DATA_UNAVAILABLE at least one declared source is absent and none
                              is unreadable (there is nothing to check)

Precedence: a present-but-unreadable source is a FAIL even when others are
absent — a corrupt file is a data-integrity finding; an absent file is only
an availability finding.

Contract: strictly read-only (never writes to any legacy file), offline (no
network, no provider access), no secrets in code or artifact. Running it
where the legacy worktrees were cleaned truthfully reports
NOT_RUN_DATA_UNAVAILABLE — that is a valid Tier-R outcome, not an error of
the check itself.
"""
from __future__ import annotations

import argparse
import datetime
import json
import platform
import subprocess
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH))

from governance import legacy_adapters  # noqa: E402

SCHEMA_ID = "legacy_state_tier_r_check@1"
EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_NOT_RUN = 3


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _code_sha(tree_root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(tree_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or "unavailable: empty output"
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"unavailable: {exc}"


def check_source(cycle_id: str, rel_path: str, root: Path) -> dict:
    """Availability + sha256 + read + zero-mutation proof for one source."""
    resolved = (root / rel_path).resolve()
    record = {
        "cycle_id": cycle_id,
        "declared_path": rel_path,
        "resolved_path": str(resolved),
        "present": False,
        "readable": False,
        "size_bytes": None,
        "sha256_before": None,
        "sha256_after": None,
        "zero_mutation": None,
        "error": None,
    }
    if not resolved.is_file():
        record["error"] = "absent (no bytes at the declared path)"
        return record
    record["present"] = True
    record["size_bytes"] = resolved.stat().st_size
    record["sha256_before"] = legacy_adapters.file_sha256(resolved)
    try:
        legacy_adapters.load_legacy_state(cycle_id, rel_path, source_root=root)
        record["readable"] = True
    except legacy_adapters.LegacySourceUnavailable as exc:
        record["error"] = exc.reason
    record["sha256_after"] = legacy_adapters.file_sha256(resolved)
    record["zero_mutation"] = record["sha256_before"] == record["sha256_after"]
    return record


def build_artifact(tree_root: Path) -> tuple:
    """Run the full check; return (artifact_dict, exit_code)."""
    root = legacy_adapters.main_repo_root()
    sources = [
        check_source(cid, rel, root)
        for cid, rel in legacy_adapters.LEGACY_SOURCES.items()
    ]
    present = [s for s in sources if s["present"]]
    readable = [s for s in present if s["readable"] and s["zero_mutation"]]
    unreadable = [s for s in present if not (s["readable"] and s["zero_mutation"])]
    absent = [s for s in sources if not s["present"]]

    # full adapter composition read (production path) when every source exists
    composition = None
    if not absent and not unreadable:
        heads = {cid: "0" * 40 for cid in legacy_adapters.LEGACY_SOURCES}
        try:
            legacy_adapters.build_registry_from_legacy(heads, source_root=root)
            composition = "ok: full build_registry_from_legacy read completed"
        except Exception as exc:  # composition failure is a FAIL finding
            composition = f"failed: {exc!r}"

    blockers = []
    for s in absent:
        blockers.append(f"{s['cycle_id']}: declared legacy source ABSENT at {s['resolved_path']}")
    for s in unreadable:
        blockers.append(
            f"{s['cycle_id']}: present but unreadable/invalid at {s['resolved_path']}: {s['error']}"
        )
        if s["zero_mutation"] is False:
            blockers.append(
                f"{s['cycle_id']}: bytes MUTATED during read "
                f"(sha256 {s['sha256_before']} -> {s['sha256_after']})"
            )
    if composition and composition.startswith("failed"):
        blockers.append(f"composition read: {composition}")

    if unreadable or (composition and composition.startswith("failed")):
        verdict, exit_code = "FAIL", EXIT_FAIL
    elif absent:
        verdict, exit_code = "NOT_RUN_DATA_UNAVAILABLE", EXIT_NOT_RUN
    else:
        verdict, exit_code = "PASS", EXIT_PASS

    artifact = {
        "schema": SCHEMA_ID,
        "generated_utc": _utc_now(),
        "command": "python scripts/legacy_state_tier_r_check.py [--out PATH]",
        "cwd": str(Path.cwd()),
        "code_sha": _code_sha(tree_root),
        "host_class": f"{platform.system()}-{platform.machine()}-py{sys.version_info.major}.{sys.version_info.minor}",
        "main_repo_root": str(root),
        "expected_inputs": [
            {"cycle_id": cid, "declared_path": rel,
             "resolved_path": str((root / rel).resolve())}
            for cid, rel in legacy_adapters.LEGACY_SOURCES.items()
        ],
        "sources": sources,
        "availability_census": {
            "expected": len(legacy_adapters.LEGACY_SOURCES),
            "present": len(present),
            "absent": len(absent),
            "unreadable_or_mutated": len(unreadable),
        },
        "zero_mutation": {
            "verified": all(s["zero_mutation"] for s in present),
            "detail": ("every present source hashed before and after a full "
                       "adapter read; before == after required"),
            "per_source": {s["cycle_id"]: [s["sha256_before"], s["sha256_after"]]
                           for s in present},
        },
        "composition_read": composition,
        "offline_no_secret": {
            "offline": True,
            "contains_secret": False,
            "basis": ("this check reads only the declared local files, hashes "
                      "bytes, and runs read-only git rev-parse; it performs no "
                      "network and no provider access and embeds no secrets"),
        },
        "verdict": verdict,
        "exit_code": exit_code,
        "blockers": blockers,
    }
    return artifact, exit_code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Tier-R availability + zero-mutation check for legacy "
                    "cycle-state sources (exit codes: 0 PASS, 1 FAIL, "
                    "3 NOT_RUN_DATA_UNAVAILABLE)."
    )
    parser.add_argument("--out", default=None,
                        help="Write the JSON artifact to PATH (default: stdout).")
    args = parser.parse_args(argv)

    tree_root = Path(__file__).resolve().parents[1]
    artifact, exit_code = build_artifact(tree_root)
    payload = json.dumps(artifact, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(f"tier-r artifact written: {out_path} (verdict {artifact['verdict']})",
              file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
