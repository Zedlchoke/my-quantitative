#!/usr/bin/env python3
"""V9 evidence archive: content-addressed bundle + hash manifest + restore verifier.

A2 role, sprint V9H->V10 Phase 0 (PLAN.md section 5). Preserves raw V9 execution
evidence from the git-ignored exec worktrees into an immutable content-addressed
bundle (blobs/<sha256[:2]>/<sha256>) with index.json + manifest.json, verifies
every hash independently, restores the full tree into a system temp dir, and
runs semantic checks of the V9 closeout invariants.

Read-only toward every evidence source. Restores never land in a git worktree.

Usage:
    python scripts/v9_evidence_archive.py inventory
    python scripts/v9_evidence_archive.py archive [--dest DIR]
    python scripts/v9_evidence_archive.py verify --bundle DIR [--restore-to DIR]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA_VERSION = 1
ARTIFACT = "v9_evidence_archive_manifest"
RETENTION_POLICY = (
    "retain until owner-approved cleanup; V9 worktrees must not be deleted"
)
BUNDLE_HASH_DEFINITION = (
    'sha256 over the UTF-8 string formed by newline-joining the sorted lines '
    '"<sha256>  <relpath>" (two spaces, sha256sum style); no trailing newline'
)
KNOWN_PINS = {
    "launch_sha": "206faf8aac5b3f7136001a45d3e7a3e85cb923e5",
    "attestation_sha256": (
        "c35b63f8f51604191a9b7c0812eda67535e19e6a0a5d085f1290c59dc5cde50a"
    ),
    "terminal_verdict": "V9_REJECT_ALL_MULTI_FAMILY",
}

WORKTREE = Path(__file__).resolve().parents[1]
R1 = Path("/Users/hoangminhlong/my-quantitative-v9-wt/exec-v9-r1")
R2 = Path("/Users/hoangminhlong/my-quantitative-v9-wt/exec-v9-r2")
MAIN_REPO = Path("/Users/hoangminhlong/my-quantitative")
INTEGRATION_V9 = Path("/Users/hoangminhlong/my-quantitative-v9-wt/integration-v9")

MAIN_TREE = "main-repo"
EXEC_TREE_NAMES = ("exec-v9-r1", "exec-v9-r2")
SCORED_TRIALS = {
    "exec-v9-r1": ["XSECT-TSTREND-L14", "XSECT-TSTREND-CTRL", "XSECT-VOLSHK-CTRL"],
    "exec-v9-r2": ["XSECT-TSTREND-L28", "XSECT-VOLSHK-S15"],
}
ALL_SCORED_TRIALS = sorted(SCORED_TRIALS["exec-v9-r1"] + SCORED_TRIALS["exec-v9-r2"])
EXPECTED_REPROS = {
    "exec-v9-r1": [
        "VERIFY-V9-TSTREND-L14", "VERIFY-V9-TSTREND-CTRL", "VERIFY-V9-VOLSHK-CTRL",
    ],
    "exec-v9-r2": ["VERIFY-V9-TSTREND-L28", "VERIFY-V9-VOLSHK-S15"],
}

ARCHIVE_DIRECTIVES = [
    ("exec-v9-r1", "results"),
    ("exec-v9-r2", "results"),
    ("exec-v9-r1", "research/audits/v9p"),
    ("exec-v9-r2", "research/audits/v9p"),
    ("exec-v9-r1", "data/v9_manifests"),
    ("exec-v9-r2", "data/v9_manifests"),
    (MAIN_TREE, "research/audits/v9"),
    (MAIN_TREE, "research/audits/v9p"),
    (MAIN_TREE, "research/control/v9_multifamily_run"),
]

TRIAL_REQUIRED_ARTIFACTS = (
    "final_gate_result.json",
    "canonical_metrics.json",
    "frozen/candidate.yaml",
    "frozen/config.yaml",
    "frozen/data_manifest.json",
    "frozen/universe.json",
)
GATE_METRIC_FILES = ("final_gate_result.json", "canonical_metrics.json")
FORBIDDEN_IN_TECHABORT = (
    "canonical_metrics.json",
    "scorecard.json",
    "final_scorecard.json",
    "final_gate_result.json",
    "gate_result.json",
)
SCORED_LEDGER_KEYS = {"sharpe", "sharpe_ratio", "total_pnl", "score", "final_score"}


def default_sources() -> dict[str, Path]:
    return {
        "exec-v9-r1": R1,
        "exec-v9-r2": R2,
        MAIN_TREE: MAIN_REPO,
    }


def utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_bundle_hash(rows: list[dict]) -> str:
    lines = sorted(f"{r['sha256']}  {r['relpath']}" for r in rows)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def yaml_scalar(text: str, key: str) -> str | None:
    m = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(.*?)\s*$", text)
    if not m:
        return None
    val = m.group(1).strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
        val = val[1:-1]
    return val or None


# --------------------------------------------------------------------------- #
# inventory
# --------------------------------------------------------------------------- #

def git_inventory(worktree: Path) -> dict:
    def git(*args: str) -> str:
        out = subprocess.run(
            ["git", "-C", str(worktree), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()

    dirty = [ln for ln in git("status", "--porcelain").splitlines() if ln.strip()]
    return {
        "head_sha": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current") or "(detached)",
        "dirty_files": len(dirty),
    }


def tree_inventory(tree: Path) -> dict:
    inv = {"path": str(tree.resolve())}
    try:
        inv.update(git_inventory(tree))
    except Exception as exc:
        inv.update({"head_sha": None, "git_error": repr(exc)})
    n_files = 0
    n_bytes = 0
    results = tree / "results"
    if results.is_dir():
        for p in results.rglob("*"):
            if p.is_file():
                n_files += 1
                try:
                    n_bytes += p.stat().st_size
                except OSError:
                    pass
    inv["results_bytes"] = n_bytes
    inv["results_file_count"] = n_files
    return inv


def collect_inventory() -> dict:
    report = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trees": [],
    }
    for name in EXEC_TREE_NAMES:
        row = {"name": name}
        row.update(tree_inventory(R1 if name == "exec-v9-r1" else R2))
        report["trees"].append(row)
    return report


def cmd_inventory(_args: argparse.Namespace) -> None:
    print(json.dumps(collect_inventory(), indent=2))


# --------------------------------------------------------------------------- #
# archive
# --------------------------------------------------------------------------- #

def role_for(rel_under_tree: str) -> str:
    parts = rel_under_tree.split("/")
    if parts[0] == "results":
        if len(parts) > 3 and parts[1] == "portfolio_v9":
            d = parts[2]
            if ".TECHABORT-" in d:
                return "techabort_zero_score_archive"
            if d in ALL_SCORED_TRIALS:
                return "scored_trial"
        if len(parts) > 3 and parts[1] == "reproduction_v9":
            return "reproduction"
        if parts[:3] == ["results", "registry", "shards"] and parts[-1].startswith("v9_"):
            return "registry_shard"
        if parts[:2] == ["results", "registry"]:
            return "registry_index"
        if parts[:2] == ["results", "matrix"]:
            return "matrix_summary"
        return "results_root_misc"
    if parts[:3] == ["research", "audits", "v9p"]:
        if parts[-1] == "baseline_root.json":
            return "prelaunch_baseline"
        if parts[-1] == "a7_prelaunch_attestation.json":
            return "prelaunch_attestation"
        return "prelaunch_audit_evidence"
    if parts[:2] == ["data", "v9_manifests"]:
        return "data_universe_manifest"
    if parts[:3] == ["research", "audits", "v9"]:
        return "audit_terminal"
    if parts[:2] == ["research", "control"]:
        return "control_lineage"
    return "misc"


def build_specs(sources: dict[str, Path]) -> list[dict]:
    specs: list[dict] = []
    seen: set[str] = set()
    for tree_name, subpath in ARCHIVE_DIRECTIVES:
        base = sources[tree_name]
        root = base / subpath
        if not root.is_dir():
            raise FileNotFoundError(f"missing evidence source directory: {root}")
        files = [p for p in root.rglob("*") if p.is_file()]
        if not files:
            raise FileNotFoundError(f"empty evidence source directory: {root}")
        for p in sorted(files):
            rel_under_tree = p.relative_to(base).as_posix()
            rel = f"{tree_name}/{rel_under_tree}"
            if rel in seen:
                raise ValueError(f"duplicate bundle relpath: {rel}")
            seen.add(rel)
            specs.append({
                "relpath": rel,
                "source_path": str(p.resolve()),
                "source_tree": tree_name,
                "role": role_for(rel_under_tree),
            })
    return specs


def write_blob(bundle_root: Path, src: Path, staging: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with open(src, "rb") as fi, open(staging, "wb") as fo:
        for chunk in iter(lambda: fi.read(1024 * 1024), b""):
            h.update(chunk)
            fo.write(chunk)
            size += len(chunk)
    digest = h.hexdigest()
    final = bundle_root / "blobs" / digest[:2] / digest
    if final.exists():
        staging.unlink()
    else:
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, final)
    return digest, size


def source_metadata(sources: dict[str, Path]) -> dict:
    trees = []
    for name in EXEC_TREE_NAMES:
        row = {"name": name}
        row.update(tree_inventory(sources[name]))
        trees.append(row)
    ctx: dict = {}
    try:
        ctx["main_repo_head_sha"] = git_inventory(sources[MAIN_TREE])["head_sha"]
    except Exception as exc:
        ctx["main_repo_head_sha"] = None
        ctx["main_repo_error"] = repr(exc)
    try:
        ctx["integration_v9_head_sha"] = git_inventory(INTEGRATION_V9)["head_sha"]
    except Exception as exc:
        ctx["integration_v9_head_sha"] = None
        ctx["integration_v9_error"] = repr(exc)
    return {"trees": trees, "context": ctx}


def cmd_archive(args: argparse.Namespace, sources: dict[str, Path] | None = None) -> dict:
    t0 = time.time()
    sources = sources if sources is not None else default_sources()
    stamp = utc_stamp()
    if args.dest:
        dest = Path(args.dest).resolve()
    else:
        dest = WORKTREE / "research_snapshots" / f"v9_closed_{stamp}"
    if dest.exists():
        raise SystemExit(f"refusing to overwrite existing destination: {dest}")
    (dest / "blobs").mkdir(parents=True)

    specs = build_specs(sources)
    staging_dir = dest / f".staging-{os.getpid()}"
    staging_dir.mkdir()
    rows: list[dict] = []
    total_bytes = 0
    try:
        for i, s in enumerate(specs):
            digest, size = write_blob(dest, Path(s["source_path"]), staging_dir / f"{i}.part")
            total_bytes += size
            rows.append({
                "relpath": s["relpath"],
                "source_path": s["source_path"],
                "source_tree": s["source_tree"],
                "role": s["role"],
                "size_bytes": size,
                "sha256": digest,
                "bundle_path": f"blobs/{digest[:2]}/{digest}",
            })
    finally:
        if staging_dir.exists():
            for leftover in staging_dir.iterdir():
                leftover.unlink()
            staging_dir.rmdir()

    rows.sort(key=lambda r: r["relpath"])
    index = {
        r["relpath"]: {
            "sha256": r["sha256"],
            "size": r["size_bytes"],
            "role": r["role"],
            "source_tree": r["source_tree"],
        }
        for r in rows
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact": ARTIFACT,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "retention_policy": RETENTION_POLICY,
        "bundle_hash_definition": BUNDLE_HASH_DEFINITION,
        "known_pins": KNOWN_PINS,
        "sources": source_metadata(sources),
        "bundle_hash": compute_bundle_hash(rows),
        "total_files": len(rows),
        "total_bytes": total_bytes,
        "files": rows,
    }
    (dest / "index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (dest / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "status": "ARCHIVED",
        "bundle": str(dest),
        "manifest": str(dest / "manifest.json"),
        "total_files": manifest["total_files"],
        "total_bytes": manifest["total_bytes"],
        "unique_blobs": len({r["bundle_path"] for r in rows}),
        "bundle_hash": manifest["bundle_hash"],
        "elapsed_s": round(time.time() - t0, 2),
    }
    print(json.dumps(summary, indent=2))
    return summary

# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #

def hash_all_blobs(bundle_root: Path) -> tuple[dict[str, str], list[str]]:
    blobs_dir = bundle_root / "blobs"
    hashes: dict[str, str] = {}
    for p in sorted(blobs_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(bundle_root).as_posix()
            hashes[rel] = sha256_file(p)
    return hashes, sorted(hashes)


def structural_verify(manifest: dict, index: dict, bundle_root: Path) -> dict:
    problems: list[str] = []
    rows = manifest["files"]

    recomputed = compute_bundle_hash(rows)
    if recomputed != manifest.get("bundle_hash"):
        problems.append(
            f"bundle_hash_mismatch: manifest={manifest.get('bundle_hash')} recomputed={recomputed}"
        )

    blob_hashes, actual_blobs = hash_all_blobs(bundle_root)
    referenced = {r["bundle_path"] for r in rows}
    for blob in sorted(referenced - set(actual_blobs)):
        problems.append(f"missing_blob: {blob}")
    for blob in sorted(set(actual_blobs) - referenced):
        problems.append(f"extra_blob_not_referenced_by_manifest: {blob}")

    bad_blobs = []
    for r in rows:
        got = blob_hashes.get(r["bundle_path"])
        if got is not None and got != r["sha256"]:
            bad_blobs.append(f"{r['bundle_path']}: expected {r['sha256']} got {got}")
    if bad_blobs:
        problems.append("blob_sha256_mismatch: " + "; ".join(bad_blobs[:10]))

    if set(index.keys()) != {r["relpath"] for r in rows}:
        missing_in_index = sorted({r["relpath"] for r in rows} - set(index.keys()))
        extra_in_index = sorted(set(index.keys()) - {r["relpath"] for r in rows})
        problems.append(
            f"index_manifest_keyset_mismatch: missing_in_index={missing_in_index[:5]} "
            f"extra_in_index={extra_in_index[:5]}"
        )
    else:
        for r in rows:
            ix = index[r["relpath"]]
            want = {
                "sha256": r["sha256"],
                "size": r["size_bytes"],
                "role": r["role"],
                "source_tree": r["source_tree"],
            }
            if ix != want:
                problems.append(f"index_manifest_row_mismatch[{r['relpath']}]: {ix} != {want}")

    return {
        "ok": not problems,
        "problems": problems,
        "recomputed_bundle_hash": recomputed,
        "unique_blobs_on_disk": len(actual_blobs),
    }


def restore_tree(manifest: dict, bundle_root: Path, restore_root: Path) -> dict:
    restore_root.mkdir(parents=True, exist_ok=True)
    matched = 0
    failed: list[dict] = []
    for r in manifest["files"]:
        src = bundle_root / r["bundle_path"]
        dst = restore_root / r["relpath"]
        if not src.is_file():
            failed.append({"relpath": r["relpath"], "error": "missing_blob"})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        if sha256_file(dst) == r["sha256"]:
            matched += 1
        else:
            failed.append({"relpath": r["relpath"], "error": "restored_byte_comparison_failed"})
    return {"matched": matched, "failed": failed, "restore_root": str(restore_root)}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_checks(restore_root: Path) -> dict:
    checks: dict[str, dict] = {}

    portfolio_roots = [
        restore_root / t / "results" / "portfolio_v9" for t in EXEC_TREE_NAMES
    ]
    all_dirs: list[Path] = []
    for pr in portfolio_roots:
        if pr.is_dir():
            all_dirs.extend(d for d in pr.iterdir() if d.is_dir())
    scored = sorted(d for d in all_dirs if ".TECHABORT-" not in d.name)
    techaborts = sorted(d for d in all_dirs if ".TECHABORT-" in d.name)

    expected_scored = {
        f"{t}/results/portfolio_v9/{trial}"
        for t in EXEC_TREE_NAMES
        for trial in SCORED_TRIALS[t]
    }
    actual_scored = {d.relative_to(restore_root).as_posix() for d in scored}
    trial_details = {}
    for d in scored:
        rel = d.relative_to(restore_root).as_posix()
        missing = [a for a in TRIAL_REQUIRED_ARTIFACTS if not (d / a).is_file()]
        unreadable = []
        for g in GATE_METRIC_FILES:
            try:
                _read_json(d / g)
            except Exception:
                unreadable.append(g)
        launch = d / "launch_manifest.yaml"
        launch_text = launch.read_text(encoding="utf-8") if launch.is_file() else ""
        pin = yaml_scalar(launch_text, "git_commit_at_launch")
        att_pin = yaml_scalar(launch_text, "attestation_sha256")
        base_pin = yaml_scalar(launch_text, "baseline_sha256")
        tree_name = rel.split("/", 1)[0]
        baseline_file = restore_root / tree_name / "research/audits/v9p/baseline_root.json"
        baseline_ok = False
        if base_pin and baseline_file.is_file():
            baseline_ok = sha256_file(baseline_file) == base_pin
        trial_details[rel] = {
            "required_artifacts_present": not missing,
            "missing_artifacts": missing,
            "gate_metrics_readable": not unreadable,
            "unreadable": unreadable,
            "launch_sha_pin_matches": pin == KNOWN_PINS["launch_sha"],
            "declared_attestation_pin_matches": att_pin == KNOWN_PINS["attestation_sha256"],
            "baseline_pin_matches_archived_baseline_bytes": baseline_ok,
        }
    checks["five_scored_trials_readable_with_pins"] = {
        "pass": (
            actual_scored == expected_scored
            and len(scored) == 5
            and all(
                v["required_artifacts_present"]
                and v["gate_metrics_readable"]
                and v["launch_sha_pin_matches"]
                and v["declared_attestation_pin_matches"]
                and v["baseline_pin_matches_archived_baseline_bytes"]
                for v in trial_details.values()
            )
        ),
        "trials": trial_details,
    }

    repro_expected = {
        f"{t}/results/reproduction_v9/{name}"
        for t in EXEC_TREE_NAMES
        for name in EXPECTED_REPROS[t]
    }
    repro_flat = sorted(
        p
        for t in EXEC_TREE_NAMES
        for p in (restore_root / t / "results" / "reproduction_v9").glob("VERIFY-V9-*")
        if p.is_dir()
    )
    actual_repros = {d.relative_to(restore_root).as_posix() for d in repro_flat}
    repro_details = {}
    for d in repro_flat:
        rel = d.relative_to(restore_root).as_posix()
        detail: dict = {"present": True}
        try:
            comp = _read_json(d / "comparison.json")
            detail["all_match"] = comp.get("all_match") is True
            detail["failed_checks_empty"] = comp.get("failed_checks", []) == []
            detail["checks_all_true"] = all(
                v is True for v in comp.get("checks", {}).values()
            ) if isinstance(comp.get("checks"), dict) else True
            _read_json(d / "reproduction_report.json")
            detail["report_readable"] = True
        except Exception as exc:
            detail["error"] = repr(exc)
            detail["all_match"] = False
        repro_details[rel] = detail
    checks["five_reproductions_all_match"] = {
        "pass": (
            actual_repros == repro_expected
            and len(repro_flat) == 5
            and all(
                v.get("all_match")
                and v.get("failed_checks_empty")
                and v.get("checks_all_true")
                and v.get("report_readable")
                for v in repro_details.values()
            )
        ),
        "reproductions": repro_details,
    }

    ta_details = {}
    for d in techaborts:
        rel = d.relative_to(restore_root).as_posix()
        offenders = [p.name for p in d.rglob("*") if p.is_file() and p.name in FORBIDDEN_IN_TECHABORT]
        ledger_rows = []
        for jf in d.rglob("*.jsonl"):
            for i, line in enumerate(jf.read_text(encoding="utf-8", errors="replace").splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                hit = sorted(k for k in SCORED_LEDGER_KEYS if row.get(k) is not None)
                if hit:
                    ledger_rows.append(f"{jf.relative_to(d).as_posix()}:{i}:{hit}")
        ta_details[rel] = {
            "scored_metric_files": offenders,
            "scored_ledger_rows": ledger_rows,
        }
    checks["techabort_archives_zero_score"] = {
        "pass": len(techaborts) == 2
        and all(
            not v["scored_metric_files"] and not v["scored_ledger_rows"]
            for v in ta_details.values()
        ),
        "archives": ta_details,
    }

    attest_details = {}
    attest_ok = True
    for t in EXEC_TREE_NAMES:
        v9p = restore_root / t / "research" / "audits" / "v9p"
        att = v9p / "a7_prelaunch_attestation.json"
        base = v9p / "baseline_root.json"
        detail: dict = {}
        try:
            _read_json(att)
            _read_json(base)
            detail["both_parse"] = True
            detail["attestation_sha256_matches_pin"] = sha256_file(att) == KNOWN_PINS["attestation_sha256"]
            detail["baseline_sha256"] = sha256_file(base)
        except Exception as exc:
            detail = {"both_parse": False, "error": repr(exc)}
        attest_details[t] = detail
        attest_ok = attest_ok and detail.get("both_parse") and detail.get(
            "attestation_sha256_matches_pin", False
        )
    checks["baseline_and_attestation_hashes_present"] = {"pass": attest_ok, "trees": attest_details}

    terminal = restore_root / MAIN_TREE / "research" / "audits" / "v9" / "a7_terminal_audit_v9.json"
    terminal_ok = False
    terminal_detail: dict = {"path": "main-repo/research/audits/v9/a7_terminal_audit_v9.json"}
    if terminal.is_file():
        text = terminal.read_text(encoding="utf-8", errors="replace")
        terminal_ok = KNOWN_PINS["terminal_verdict"] in text
        terminal_detail["contains_terminal_verdict"] = terminal_ok
    else:
        terminal_detail["present"] = False
    checks["terminal_verdict_evidence"] = {"pass": terminal_ok, "detail": terminal_detail}

    contract_budget = {}
    cb_ok = True
    main_v9p = restore_root / MAIN_TREE / "research" / "audits" / "v9p"
    for name in ("resolved_contract_v9.json", "v9_budget_freeze.json"):
        try:
            _read_json(main_v9p / name)
            contract_budget[name] = True
        except Exception:
            contract_budget[name] = False
            cb_ok = False
    for t in EXEC_TREE_NAMES:
        uni = restore_root / t / "data" / "v9_manifests" / "universe_selection_v9.json"
        try:
            _read_json(uni)
            contract_budget[f"{t}/universe_selection_v9.json"] = True
        except Exception:
            contract_budget[f"{t}/universe_selection_v9.json"] = False
            cb_ok = False
    checks["contract_budget_universe_data_manifests"] = {"pass": cb_ok, "files": contract_budget}

    shard_names = set()
    shard_ok = True
    for t in EXEC_TREE_NAMES:
        shard_dir = restore_root / t / "results" / "registry" / "shards"
        for trial in SCORED_TRIALS[t]:
            f = shard_dir / f"v9_{trial}.jsonl"
            if f.is_file() and f.stat().st_size > 0:
                shard_names.add(f"{t}/v9_{trial}.jsonl")
            else:
                shard_ok = False
    checks["registry_shards_for_all_five_trials"] = {
        "pass": shard_ok and len(shard_names) == 5,
        "shards": sorted(shard_names),
    }

    event_log = restore_root / MAIN_TREE / "research/control/v9_multifamily_run/event_log.jsonl"
    checks["control_event_log_present"] = {
        "pass": event_log.is_file() and event_log.stat().st_size > 0,
        "path": "main-repo/research/control/v9_multifamily_run/event_log.jsonl",
    }

    checks["all_pass"] = all(v.get("pass") is True for k, v in checks.items() if k != "all_pass")
    return checks


def cmd_verify(args: argparse.Namespace) -> None:
    t0 = time.time()
    bundle_root = Path(args.bundle).resolve()
    manifest = _read_json(bundle_root / "manifest.json")
    index = _read_json(bundle_root / "index.json")

    structure = structural_verify(manifest, index, bundle_root)

    if args.restore_to:
        restore_root = Path(args.restore_to).resolve()
        if restore_root.exists():
            raise SystemExit(
                f"refusing to overwrite existing restore dir: {restore_root}"
            )
    else:
        restore_root = Path(tempfile.mkdtemp(prefix="v9_restore_"))
    restoration = restore_tree(manifest, bundle_root, restore_root)
    semantic = semantic_checks(restore_root)

    verdict_pass = (
        structure["ok"]
        and not restoration["failed"]
        and restoration["matched"] == manifest["total_files"]
        and semantic["all_pass"]
    )
    report = {
        "verdict": "PASS" if verdict_pass else "FAIL",
        "artifact": manifest.get("artifact"),
        "bundle": str(bundle_root),
        "bundle_hash": manifest.get("bundle_hash"),
        "recomputed_bundle_hash": structure["recomputed_bundle_hash"],
        "restore_to": restoration["restore_root"],
        "elapsed_s": round(time.time() - t0, 2),
        "total_files": manifest["total_files"],
        "total_bytes": manifest["total_bytes"],
        "files_matched": restoration["matched"],
        "unique_blobs_on_disk": structure["unique_blobs_on_disk"],
        "structural_problems": structure["problems"],
        "restore_failures": restoration["failed"],
        "semantic_checks": {k: v for k, v in semantic.items() if k != "all_pass"},
        "semantic_all_pass": semantic["all_pass"],
        "limitations": [
            "verification proves byte-fidelity of the bundle vs its own manifest; "
            "source-vs-bundle equality is enforced at archive time by hash-on-write",
            "semantic checks validate the V9 closeout invariants on the restored copy",
        ],
    }
    print(json.dumps(report, indent=2))
    if report["verdict"] != "PASS":
        sys.exit(1)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp_inv = sub.add_parser("inventory", help="inventory both V9 exec worktrees")
    sp_inv.set_defaults(func=cmd_inventory)

    sp_arch = sub.add_parser("archive", help="build the content-addressed evidence bundle")
    sp_arch.add_argument("--dest", default=None, help="bundle destination directory")
    sp_arch.set_defaults(func=lambda a: cmd_archive(a))

    sp_ver = sub.add_parser("verify", help="verify a bundle and restore it to temp")
    sp_ver.add_argument("--bundle", required=True, help="bundle directory to verify")
    sp_ver.add_argument("--restore-to", default=None, help="restore target directory")
    sp_ver.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
