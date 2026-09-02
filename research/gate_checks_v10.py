"""Machine-readable V9H gate evaluator (A10, sprint V9H→V10 wave-H2).

Produces atomic evidence rows consumed later by A7/A1:

    [{gate, verdict, evidence_refs, measured}, ...]

Verdicts are exactly ``PASS``, ``FAIL`` or ``UNAVAILABLE_FAIL_CLOSED``
(missing/uncertain evidence is a closed gate, never a pass).

Covered gates (PLAN.md §6 "V9H gates H01–H14"):

* ``G-H03`` — non-null-timeouts scan: static AST check over the allowlisted
  subprocess layers (``research/runtime_controller_v10.py``,
  ``research/reproduction_stream_v10.py``): no blocking subprocess call
  without an explicit non-null timeout, no literal ``timeout=None``, and the
  frozen timing contracts must exist and be positive.
* ``G-H05`` — governor freeze record present + internally consistent: the
  stored freeze record is INDEPENDENTLY recomputed from its inputs (RAM cap
  arithmetic, three-probe promotion rule, post-PnL monotone clamp) and any
  disagreement FAILS; missing/unreadable state is UNAVAILABLE_FAIL_CLOSED.
* ``G-H06`` — cache parity proof object: byte parity + independent
  reproduction all-match + raw-read budget ≤2 + ≥30% wall-time reduction,
  evaluated fail-closed through :class:`research.cache_v10.SharedCacheMergeGate`.
* ``G-H08`` — adversarial matrix items mapping (all 20 items must be
  explicitly passing; explicit failures are FAIL, gaps are
  UNAVAILABLE_FAIL_CLOSED).
* ``G-H12`` — golden parity record: TS-TREND/VOLSHOCK golden digests must be
  equal across roots and well-formed SHA-256 hex.

CLI (works from the worktree root):

    python -m research.gate_checks_v10 --gates all --out results/gates.json \
        [--evidence-dir DIR]     # DIR/<gate_id>.json supplies per-gate evidence

Stdlib only; no network; never mutates production modules.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

PASS = "PASS"
FAIL = "FAIL"
UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"

DEFAULT_SOURCES_GH03 = (
    REPO_ROOT / "research" / "runtime_controller_v10.py",
    REPO_ROOT / "research" / "reproduction_stream_v10.py",
)

FROZEN_TIMING_CONSTANTS = {
    "runtime_controller_v10.py": ("DEFAULT_TERM_GRACE_S", "DEFAULT_HEARTBEAT_INTERVAL_S"),
    "reproduction_stream_v10.py": ("TERM_GRACE_S",),
}

BLOCKING_SUBPROCESS_FUNCS = frozenset({"run", "call", "check_output", "check_call"})

H08_ITEM_COUNT = 20

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

Row = Dict[str, Any]


# ------------------------------------------------------------------ helpers
def _row(gate: str, verdict: str, evidence_refs: List[str], measured: Dict[str, Any]) -> Row:
    return {
        "gate": gate,
        "verdict": verdict,
        "evidence_refs": evidence_refs,
        "measured": measured,
    }


def _load_evidence_dict(evidence: Any) -> Tuple[Optional[Dict[str, Any]], str]:
    if isinstance(evidence, Mapping):
        return dict(evidence), ""
    if isinstance(evidence, (str, Path)):
        path = Path(evidence)
        if not path.is_file():
            return None, f"evidence file missing: {path}"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return None, f"evidence unreadable: {exc}"
        if not isinstance(payload, dict):
            return None, f"evidence not a JSON object: {path}"
        return payload, ""
    return None, f"unsupported evidence type: {type(evidence).__name__}"


# -------------------------------------------------------------------- G-H03
def _callee_parts(node: ast.Call) -> Tuple[Optional[str], Optional[str]]:
    func = node.func
    if isinstance(func, ast.Attribute):
        base = func.value.id if isinstance(func.value, ast.Name) else None
        return base, func.attr
    if isinstance(func, ast.Name):
        return None, func.id
    return None, None


def _subprocess_blocking_calls(tree: ast.Module) -> List[Tuple[ast.Call, str]]:
    """Yield (call, display) for subprocess.* blocking-wait calls."""
    imported_from_subprocess: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                imported_from_subprocess.add(alias.asname or alias.name)
    found: List[Tuple[ast.Call, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        base, attr = _callee_parts(node)
        name = attr or ""
        if name not in BLOCKING_SUBPROCESS_FUNCS:
            continue
        if base == "subprocess" or (base is None and name in imported_from_subprocess):
            found.append((node, f"{base or 'subprocess'}.{name}"))
    return found


def _is_none_const(expr: Optional[ast.expr]) -> bool:
    return isinstance(expr, ast.Constant) and expr.value is None


def _numeric_consts_named(tree: ast.Module) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target_name = node.targets[0].id
            value_node = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value is not None
        ):
            target_name = node.target.id
            value_node = node.value
        else:
            continue
        if (
            isinstance(value_node, ast.Constant)
            and isinstance(value_node.value, (int, float))
            and not isinstance(value_node.value, bool)
        ):
            out.setdefault(target_name, float(value_node.value))
    return out


def evaluate_gate_h03(evidence: Mapping[str, Any]) -> Row:
    sources: List[Path] = [Path(p) for p in evidence.get("sources", [])]
    sources.extend(DEFAULT_SOURCES_GH03)
    refs = [str(p) for p in sources]
    files_measured: List[Dict[str, Any]] = []
    violations: List[str] = []

    for source in sources:
        if not source.is_file():
            return _row("G-H03", UNAVAILABLE, refs, {"reason": f"source missing: {source}"})
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        except SyntaxError as exc:
            return _row("G-H03", UNAVAILABLE, refs, {"reason": f"unparseable source {source}: {exc}"})

        file_violations: List[str] = []
        for call, display in _subprocess_blocking_calls(tree):
            timeout_kw = next((k for k in call.keywords if k.arg == "timeout"), None)
            line = getattr(call, "lineno", -1)
            if timeout_kw is None:
                file_violations.append(f"{source.name}:{line}: {display}() without timeout")
            elif _is_none_const(timeout_kw.value):
                file_violations.append(f"{source.name}:{line}: {display}(timeout=None)")
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "timeout" and _is_none_const(node.value):
                line = getattr(getattr(node, "value", None), "lineno", -1)
                file_violations.append(f"{source.name}:{line}: literal timeout=None kwarg")
        consts = _numeric_consts_named(tree)
        for const_name in FROZEN_TIMING_CONSTANTS.get(source.name, ()):
            value = consts.get(const_name)
            if value is None:
                file_violations.append(f"{source.name}: frozen constant {const_name} missing")
            elif value <= 0:
                file_violations.append(
                    f"{source.name}: frozen constant {const_name}={value} not positive"
                )
        violations.extend(file_violations)
        files_measured.append({"path": str(source), "violations": list(file_violations)})

    verdict = PASS if not violations else FAIL
    return _row(
        "G-H03",
        verdict,
        refs,
        {"files_scanned": len(files_measured), "violations": violations, "files": files_measured},
    )


# -------------------------------------------------------------------- G-H05
def _recompute_governor(state: Mapping[str, Any]) -> Dict[str, Any]:
    reserved = float(state["reserved_ram_gb"])
    available = float(state["available_ram_gb"])
    peak = float(state["measured_peak_worker_ram_gb"])
    contract = int(state["contract_cap"])
    headroom = available - reserved
    ram_cap = 0 if headroom <= 0 else int(math.floor(headroom / peak))
    streak = 0
    for probe in reversed(list(state.get("probe_records") or [])):
        if probe.get("safe"):
            streak += 1
        else:
            break
    effective = min(contract, ram_cap)
    if effective >= 2 and streak < 3:
        effective = min(effective, 1)
    snapshot = state.get("cap_snapshot_at_pnl")
    if effective >= 2 and snapshot is not None:
        effective = min(effective, int(snapshot))
    return {
        "ram_cap_workers": max(0, ram_cap),
        "consecutive_safe_two_worker_probes": streak,
        "effective_heavy_workers_recomputed": max(0, effective),
    }


def evaluate_gate_h05(evidence: Mapping[str, Any]) -> Row:
    if "governor_state_path" in evidence:
        path = Path(str(evidence["governor_state_path"]))
        if not path.is_file():
            return _row(
                "G-H05", UNAVAILABLE, [str(path)], {"reason": f"governor state missing: {path}"}
            )
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return _row("G-H05", UNAVAILABLE, [str(path)], {"reason": f"unreadable: {exc}"})
        refs = [str(path)]
    elif "governor_state" in evidence:
        state = evidence["governor_state"]
        refs = ["inline:governor_state"]
    else:
        return _row("G-H05", UNAVAILABLE, [], {"reason": "no governor freeze record supplied"})
    if not isinstance(state, dict):
        return _row("G-H05", UNAVAILABLE, refs, {"reason": "freeze record not an object"})

    reasons: List[str] = []
    try:
        recomputed = _recompute_governor(state)
    except (KeyError, TypeError, ValueError) as exc:
        return _row("G-H05", UNAVAILABLE, refs, {"reason": f"incomplete freeze record: {exc}"})

    if float(state.get("reserved_ram_gb", 0)) < 2.0:
        reasons.append("reserved_ram_gb_below_2gb_reserve")
    if float(state.get("measured_peak_worker_ram_gb", 0)) <= 0:
        reasons.append("measured_peak_worker_ram_gb_not_positive")
    if float(state.get("available_ram_gb", -1)) < 0:
        reasons.append("available_ram_gb_negative")
    if int(state.get("contract_cap", 0)) < 1:
        reasons.append("contract_cap_not_positive_int")
    if state.get("ram_cap_workers") != recomputed["ram_cap_workers"]:
        reasons.append(
            f"ram_cap_mismatch:stored={state.get('ram_cap_workers')}"
            f":recomputed={recomputed['ram_cap_workers']}"
        )
    if state.get("consecutive_safe_two_worker_probes") != recomputed[
        "consecutive_safe_two_worker_probes"
    ]:
        reasons.append("probe_streak_mismatch")
    if state.get("effective_heavy_workers") != recomputed["effective_heavy_workers_recomputed"]:
        reasons.append(
            f"effective_cap_mismatch:stored={state.get('effective_heavy_workers')}"
            f":recomputed={recomputed['effective_heavy_workers_recomputed']}"
        )

    verdict = PASS if not reasons else FAIL
    return _row(
        "G-H05",
        verdict,
        refs,
        {"reasons": reasons, "recomputed": recomputed, "stored_effective_heavy_workers": state.get("effective_heavy_workers")},
    )


# -------------------------------------------------------------------- G-H06
_HARD_FAIL_REASON_PREFIXES = (
    "artifact_manifest_mismatch",
    "parity_proof_false",
    "independent_reproduction_not_all_match",
    "raw_reads_budget_exceeded",
    "raw_reads_counter_negative",
    "wall_time_reduction_below_target",
    "pnl_visible_posture_change_forbidden",
)


def evaluate_gate_h06(evidence: Mapping[str, Any]) -> Row:
    from research.cache_v10 import SharedCacheMergeGate

    gate = SharedCacheMergeGate()
    kwargs: Dict[str, Any] = {}
    parity_why: Optional[str] = None
    refs: List[str] = []
    if "parity_dirs" in evidence:
        dirs = evidence["parity_dirs"]
        if not (isinstance(dirs, (list, tuple)) and len(dirs) == 2):
            return _row("G-H06", UNAVAILABLE, [], {"reason": "parity_dirs must be [on_dir, off_dir]"})
        refs = [str(dirs[0]), str(dirs[1])]
        parity, why = gate.parity_from_dirs(dirs[0], dirs[1])
        kwargs["parity_proof"] = parity
        parity_why = why
    else:
        proof = evidence.get("proof")
        if not isinstance(proof, Mapping):
            return _row("G-H06", UNAVAILABLE, [], {"reason": "no cache parity proof object supplied"})
        refs = ["inline:proof"]
        allowed = (
            "parity_proof", "repro_all_match", "raw_reads",
            "wall_time_cached_s", "wall_time_uncached_s",
        )
        kwargs = {key: proof[key] for key in allowed if key in proof}

    decision = gate.evaluate(strict=True, **kwargs)
    reasons = list(decision["reasons"])
    if parity_why:
        reasons.append(parity_why)

    if decision["adopted"]:
        return _row("G-H06", PASS, refs, {"proofs": decision["proofs"], "metrics": decision["metrics"]})
    hard_failure = any(
        reason.startswith(prefix)
        for reason in reasons
        for prefix in _HARD_FAIL_REASON_PREFIXES
    )
    if hard_failure:
        return _row(
            "G-H06", FAIL, refs,
            {"reasons": reasons, "proofs": decision["proofs"], "metrics": decision["metrics"]},
        )
    return _row(
        "G-H06", UNAVAILABLE, refs,
        {"reasons": reasons, "proofs": decision["proofs"], "metrics": decision["metrics"]},
    )


# -------------------------------------------------------------------- G-H08
def evaluate_gate_h08(evidence: Mapping[str, Any]) -> Row:
    items_raw: Any = evidence.get("items", evidence)
    if not isinstance(items_raw, Mapping):
        return _row("G-H08", UNAVAILABLE, [], {"reason": "no H08 items mapping supplied"})
    items: Dict[int, str] = {}
    for key, value in items_raw.items():
        try:
            item_no = int(key)
        except (TypeError, ValueError):
            continue
        items[item_no] = str(value).strip().upper()

    failed = sorted(no for no, status in items.items() if status == "FAIL")
    unknown = sorted(no for no, status in items.items() if status not in ("PASS", "FAIL"))
    missing = sorted(set(range(1, H08_ITEM_COUNT + 1)) - set(items))
    passing = sorted(
        no for no, status in items.items() if status == "PASS" and 1 <= no <= H08_ITEM_COUNT
    )
    refs = [f"h08_item_{no}" for no in sorted(items)]

    if failed:
        return _row("G-H08", FAIL, refs, {"failed_items": failed, "passing_items": passing})
    if missing or unknown:
        return _row(
            "G-H08",
            UNAVAILABLE,
            refs,
            {"missing_items": missing, "unknown_status_items": unknown, "passing_items": passing},
        )
    if len(passing) != H08_ITEM_COUNT:
        return _row("G-H08", UNAVAILABLE, refs, {"passing_items": passing})
    return _row("G-H08", PASS, refs, {"passing_items": passing})


# -------------------------------------------------------------------- G-H12
def _sha_pairs(evidence: Mapping[str, Any]) -> List[Dict[str, str]]:
    pairs: List[Dict[str, str]] = []
    raw = evidence.get("pairs")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        for entry in raw:
            if isinstance(entry, Mapping):
                pairs.append(
                    {
                        "label": str(entry.get("label", f"pair_{len(pairs) + 1}")),
                        "a": str(entry.get("sha_root_a", "")),
                        "b": str(entry.get("sha_root_b", "")),
                    }
                )
        if pairs:
            return pairs
    if "sha_root_a" in evidence or "sha_root_b" in evidence:
        pairs.append(
            {
                "label": str(evidence.get("label", "golden")),
                "a": str(evidence.get("sha_root_a", "")),
                "b": str(evidence.get("sha_root_b", "")),
            }
        )
    return pairs


def evaluate_gate_h12(evidence: Mapping[str, Any]) -> Row:
    pairs = _sha_pairs(evidence)
    if not pairs:
        return _row("G-H12", UNAVAILABLE, [], {"reason": "no golden parity pairs supplied"})
    refs = [f"{pair['label']}:{pair['a'][:16]}" for pair in pairs]
    malformed = [
        pair["label"]
        for pair in pairs
        if not SHA256_HEX_RE.match(pair["a"].lower()) or not SHA256_HEX_RE.match(pair["b"].lower())
    ]
    mismatched = [pair["label"] for pair in pairs if pair["a"].lower() != pair["b"].lower()]
    if malformed:
        return _row("G-H12", UNAVAILABLE, refs, {"malformed_sha_labels": malformed})
    if mismatched:
        return _row("G-H12", FAIL, refs, {"mismatched_labels": mismatched})
    return _row("G-H12", PASS, refs, {"labels": [pair["label"] for pair in pairs]})


# ----------------------------------------------------------------- registry
EVALUATORS: Dict[str, Callable[[Mapping[str, Any]], Row]] = {
    "G-H03": evaluate_gate_h03,
    "G-H05": evaluate_gate_h05,
    "G-H06": evaluate_gate_h06,
    "G-H08": evaluate_gate_h08,
    "G-H12": evaluate_gate_h12,
}


def evaluate_gate(gate_id: str, evidence: Optional[Mapping[str, Any]] = None) -> Row:
    """Evaluate one V9H gate and return its machine-readable evidence row."""
    evaluator = EVALUATORS.get(gate_id)
    if evaluator is None:
        raise ValueError(f"unknown gate id {gate_id!r}; known: {sorted(EVALUATORS)}")
    return evaluator(evidence or {})


def evaluate_gates(gate_ids: Sequence[str], evidence_by_gate: Mapping[str, Mapping[str, Any]]) -> List[Row]:
    return [evaluate_gate(gate_id, evidence_by_gate.get(gate_id)) for gate_id in gate_ids]


def write_rows_atomically(path: Path, rows: Sequence[Row]) -> None:
    """tmp + fsync + os.replace so A7/A1 never observe a torn rows file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    data = json.dumps(list(rows), indent=2, sort_keys=True) + "\n"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, path)
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        pass
    finally:
        os.close(dir_fd)


# ---------------------------------------------------------------------- CLI
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="research.gate_checks_v10",
        description="V9H gate evaluator producing atomic evidence rows (A10).",
    )
    parser.add_argument(
        "--gates",
        default="all",
        help="comma-separated gate ids or 'all' (default: all)",
    )
    parser.add_argument("--out", required=True, help="output JSON rows path (written atomically)")
    parser.add_argument(
        "--evidence-dir",
        default=None,
        help="optional dir holding <gate_id>.json evidence payloads",
    )
    args = parser.parse_args(argv)

    if args.gates.strip().lower() == "all":
        gate_ids = list(EVALUATORS)
    else:
        gate_ids = [token.strip().upper() for token in args.gates.split(",") if token.strip()]
        unknown = [gate for gate in gate_ids if gate not in EVALUATORS]
        if unknown:
            parser.error(f"unknown gate id(s): {unknown}; known: {sorted(EVALUATORS)}")

    evidence_by_gate: Dict[str, Mapping[str, Any]] = {}
    if args.evidence_dir:
        evidence_dir = Path(args.evidence_dir)
        for gate_id in gate_ids:
            candidate = evidence_dir / f"{gate_id}.json"
            if candidate.is_file():
                try:
                    loaded = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    loaded = None
                if isinstance(loaded, dict):
                    evidence_by_gate[gate_id] = loaded

    rows = evaluate_gates(gate_ids, evidence_by_gate)
    write_rows_atomically(Path(args.out), rows)
    print(json.dumps(rows, indent=2, sort_keys=True))
    return 0 if all(row["verdict"] == PASS for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
