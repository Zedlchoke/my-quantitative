"""F3 terminal-consistency validator (MARKET-DATA-PLANE-V2 freeze, finding F3).

Compares a cycle's terminal report against the run-control artifacts that
trail it: state.json, heartbeat.json, worktree_manifest.json, the canonical
registry row, the integration branch tip, workers/gates and the append-only
event log. Empty findings list = consistent.

HISTORICAL BYTES RULE (freeze F3): stale files are NEVER edited. The bad
bytes stay visible forever; the correction layer is a terminal addendum:

    {"schema": "mdp_terminal_addendum@1",
     "cycle": <cycle id>,
     "supersedes_fields": [
         {"file": "state.json", "field": "phase",
          "stale_value": ..., "corrected_value": ...}, ...],
     "evidence": [...], "created_utc": ...}

An addendum entry covers a finding only when file+field match, the recorded
stale_value equals the value actually observed in the historical bytes, and
the corrected_value equals the value derived from the terminal artifacts
(exact for most fields; "a non-empty string" for the registry worktree path
and "starts with DEAD" for go_phrase_state, which no other artifact pins).
A partially-covering or wrong addendum leaves the findings standing: the
validator fails closed, never silently accepts a correction.

Public API (frozen):
    validate_terminal_consistency(terminal_report, state, heartbeat,
        worktree_manifest, registry_row, branch_tip, event_log_lines,
        addendum=None, identity_result=None) -> list[dict]
        # [{kind, severity, detail}, ...]
    check_v1_run_dir(run_dir, addendum=None) -> list[dict]

MDP-V2R1 A4 (plan §12): a registry row that declares
head_semantics "TERMINAL_ANCHOR" (+ terminal_anchor_sha) binds head to the
audited terminal anchor; evidence-only descendants standing after the anchor
are NOT registry staleness. Callers with repo context may pass
``identity_result`` (a governance.terminal_identity result) to fold deeper
ancestry/allowlist findings in; None keeps the historical behavior exactly.

Read-only: no file is ever written or repaired by this module.
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
from pathlib import Path

ADDENDUM_SCHEMA = "mdp_terminal_addendum@1"
EXPECTED_TERMINAL_PHASE = "P9_TERMINAL"
TERMINAL_LIFECYCLE = "TERMINAL"
GO_DEAD_PREFIX = "DEAD"

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

REPORT_REQUIRED = ("cycle", "verdict", "recorded_utc", "head_integration", "gates")

_SEVERITY = {
    "TERMINAL_REPORT_INVALID": "HIGH",
    "RUN_FILE_MISSING": "HIGH",
    "RUN_FILE_UNREADABLE": "HIGH",
    "STATE_PHASE_STALE": "HIGH",
    "STATE_HEAD_MISMATCH": "HIGH",
    "GATE_STATE_CONTRADICTION": "HIGH",
    "OPEN_GATES_CONTRADICTION": "HIGH",
    "HEARTBEAT_PHASE_STALE": "MEDIUM",
    "HEARTBEAT_STALE": "LOW",
    "PLANNED_LANE_STALE": "MEDIUM",
    "REGISTRY_ROW_MISSING": "HIGH",
    "REGISTRY_LIFECYCLE_STALE": "HIGH",
    "REGISTRY_HEAD_STALE": "HIGH",
    "REGISTRY_WORKTREE_MISSING": "MEDIUM",
    "REGISTRY_TERMINAL_WORKERS": "HIGH",
    "REGISTRY_GO_NOT_DEAD": "HIGH",
    "EVENT_LOG_MALFORMED": "HIGH",
    "ADDENDUM_INVALID": "HIGH",
}

# coverage rules per finding kind: how an addendum corrected_value is judged
_COVERAGE_EXACT = "exact"              # corrected_value == derived expected
_COVERAGE_NONEMPTY_STR = "nonempty_str"  # corrected_value is a non-empty string
_COVERAGE_DEAD_PREFIX = "dead_prefix"    # corrected_value startswith DEAD


# ------------------------------------------------------------------ helpers

def _finding(kind: str, file: str, field: str, observed, expected,
             detail: str, coverable: bool = True,
             coverage_rule: str = _COVERAGE_EXACT) -> dict:
    return {"kind": kind, "severity": _SEVERITY[kind], "detail": detail,
            "file": file, "field": field, "observed": observed,
            "expected": expected, "coverable": coverable,
            "coverage_rule": coverage_rule}


def _leading_status(value) -> str:
    s = str(value or "").strip().upper()
    for token in ("PASS", "PARTIAL", "FAILED", "FAIL", "PENDING",
                  "IN FLIGHT", "NOT RUN", "NOT_RUN", "BLOCKED"):
        if s.startswith(token):
            return token
    return s.split(" ", 1)[0] if s else ""


def _parse_utc(text) -> "datetime.datetime | None":
    if not isinstance(text, str) or not _UTC.match(text):
        return None
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)


# ------------------------------------------------------------- artifact checks

def _check_event_log(findings: list, event_log_lines) -> list:
    """Parse each JSONL line; malformed lines are findings. Returns events."""
    events = []
    for i, line in enumerate(event_log_lines or []):
        raw = line.rstrip("\n")
        if not raw.strip():
            continue  # trailing blank lines are not corruption
        try:
            obj = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            findings.append(_finding(
                "EVENT_LOG_MALFORMED", "event_log.jsonl", f"line[{i + 1}]",
                raw, "<valid append-only JSONL event with utc+event>",
                f"event_log.jsonl line {i + 1} is not valid JSON: {raw[:80]!r}",
                coverable=False))
            continue
        if not (isinstance(obj, dict) and isinstance(obj.get("utc"), str)
                and isinstance(obj.get("event"), str) and obj["event"]):
            findings.append(_finding(
                "EVENT_LOG_MALFORMED", "event_log.jsonl", f"line[{i + 1}]",
                raw, "<valid append-only JSONL event with utc+event>",
                f"event_log.jsonl line {i + 1} is not an event object "
                f"(utc+event): {raw[:80]!r}", coverable=False))
            continue
        events.append(obj)
    return events


def _check_terminal_report(findings: list, terminal_report) -> bool:
    ok = isinstance(terminal_report, dict)
    if ok:
        missing = [k for k in REPORT_REQUIRED if k not in terminal_report]
        if missing:
            ok = False
            detail = f"terminal report missing required keys {missing}"
        elif not isinstance(terminal_report["gates"], dict):
            ok = False
            detail = "terminal report gates must be an object"
        elif not (_HEX40.match(terminal_report["head_integration"] or "")
                  and isinstance(terminal_report["cycle"], str)
                  and _parse_utc(terminal_report["recorded_utc"])):
            ok = False
            detail = ("terminal report needs a 40-hex head_integration and a "
                      "UTC-Z recorded_utc")
    else:
        detail = "terminal report is not an object"
    if not ok:
        findings.append(_finding(
            "TERMINAL_REPORT_INVALID", "terminal_report.json", "report",
            "<unusable terminal report>", "<valid mdp_terminal_report@1>",
            f"{detail} - closure cannot be evaluated without it",
            coverable=False))
    return ok


def _expected_terminal_phase(events: list) -> str:
    """The last P9 event name in the log, else the frozen default."""
    for obj in reversed(events):
        if str(obj.get("event", "")).startswith("P9"):
            return obj["event"]
    return EXPECTED_TERMINAL_PHASE


def _check_state(findings: list, state: dict, report: dict,
                 expected_phase: str) -> None:
    if not isinstance(state, dict):
        state = {}
    phase = state.get("phase")
    if phase != expected_phase:
        findings.append(_finding(
            "STATE_PHASE_STALE", "state.json", "phase", phase, expected_phase,
            f"state.json phase {phase!r} contradicts the terminal close "
            f"({report['verdict']!r} recorded {report['recorded_utc']}); "
            f"expected {expected_phase!r} - correct via terminal addendum, "
            "never by editing the historical bytes"))
    head = state.get("head_integration")
    if head != report["head_integration"]:
        findings.append(_finding(
            "STATE_HEAD_MISMATCH", "state.json", "head_integration", head,
            report["head_integration"],
            f"state.json head_integration {head!r} != terminal report head "
            f"{report['head_integration']!r}"))

    # gates: every gate the report marks PASS must be PASS in state
    completed = state.get("completed_gates")
    completed = completed if isinstance(completed, dict) else {}
    for gate, report_value in report["gates"].items():
        if _leading_status(report_value) != "PASS":
            continue
        state_value = completed.get(gate)
        if _leading_status(state_value) != "PASS":
            findings.append(_finding(
                "GATE_STATE_CONTRADICTION", "state.json",
                f"completed_gates.{gate}", state_value, report_value,
                f"state.json completed_gates.{gate} = {state_value!r} "
                f"contradicts terminal report gates.{gate} = {report_value!r}"))

    # open_gates: must not still list gates the report marks PASS
    open_gates = state.get("open_gates")
    open_gates = open_gates if isinstance(open_gates, list) else []
    stale_open = [g for g in open_gates
                  if isinstance(g, str) and g in report["gates"]
                  and _leading_status(report["gates"][g]) == "PASS"]
    if stale_open:
        corrected_open = [g for g in open_gates if g not in stale_open]
        findings.append(_finding(
            "OPEN_GATES_CONTRADICTION", "state.json", "open_gates",
            open_gates, corrected_open,
            f"state.json open_gates still lists terminal-PASS gates "
            f"{stale_open} - expected {corrected_open!r}"))


def _check_heartbeat(findings: list, heartbeat: dict, report: dict,
                     expected_phase: str) -> None:
    if not isinstance(heartbeat, dict):
        heartbeat = {}
    phase = heartbeat.get("phase")
    if phase != expected_phase:
        findings.append(_finding(
            "HEARTBEAT_PHASE_STALE", "heartbeat.json", "phase", phase,
            expected_phase,
            f"heartbeat.json phase {phase!r} predates the terminal close; "
            f"expected {expected_phase!r} (staleness tolerated only via the "
            "terminal addendum)"))
    hb_utc = heartbeat.get("utc")
    recorded = report["recorded_utc"]
    hb_dt, rec_dt = _parse_utc(hb_utc), _parse_utc(recorded)
    if hb_dt is None or (rec_dt is not None and hb_dt < rec_dt):
        reason = ("unparseable" if hb_dt is None
                  else f"{hb_utc!r} is older than the terminal close "
                       f"{recorded!r}")
        findings.append(_finding(
            "HEARTBEAT_STALE", "heartbeat.json", "utc", hb_utc, recorded,
            f"heartbeat.json utc {reason}; at terminal the heartbeat must be "
            f"current with the terminal report ({recorded!r}) or covered by "
            "the addendum"))


def _check_manifest(findings: list, manifest: dict) -> None:
    if not isinstance(manifest, dict):
        manifest = {}
    planned = manifest.get("planned")
    planned = planned if isinstance(planned, list) else []
    for i, entry in enumerate(planned):
        label = entry.get("branch") or entry.get("path") or entry.get("owner") \
            if isinstance(entry, dict) else entry
        findings.append(_finding(
            "PLANNED_LANE_STALE", "worktree_manifest.json",
            f"planned[{i}]", entry, None,
            f"worktree_manifest.json planned lane {label!r} is still planned "
            "at terminal - all lanes are landed or accounted for by the "
            "terminal report; remove via addendum (corrected_value null)"))


def _check_registry(findings: list, registry_row, report: dict,
                    branch_tip) -> None:
    if registry_row is None:
        findings.append(_finding(
            "REGISTRY_ROW_MISSING", "registry", "row", None,
            "<canonical registry row present>",
            "no canonical registry row for the cycle - terminal "
            "reconciliation requires the row to exist (fix via researchctl "
            "cycle update, never by hand-editing)", coverable=False))
        return
    if not isinstance(registry_row, dict):
        registry_row = {}

    lifecycle = registry_row.get("lifecycle")
    if lifecycle != TERMINAL_LIFECYCLE:
        findings.append(_finding(
            "REGISTRY_LIFECYCLE_STALE", "registry", "lifecycle", lifecycle,
            TERMINAL_LIFECYCLE,
            f"registry lifecycle {lifecycle!r} != TERMINAL although the "
            "terminal report records closure"))

    workers = registry_row.get("workers")
    if workers != 0:
        findings.append(_finding(
            "REGISTRY_TERMINAL_WORKERS", "registry", "workers", workers, 0,
            f"registry lifecycle TERMINAL requires workers 0, got "
            f"{workers!r}"))

    go_state = registry_row.get("go_phrase_state")
    if not (isinstance(go_state, str) and go_state.startswith(GO_DEAD_PREFIX)):
        findings.append(_finding(
            "REGISTRY_GO_NOT_DEAD", "registry", "go_phrase_state", go_state,
            GO_DEAD_PREFIX,
            f"registry lifecycle TERMINAL requires a dead GO phrase state "
            f"(startswith {GO_DEAD_PREFIX!r}), got {go_state!r}",
            coverage_rule=_COVERAGE_DEAD_PREFIX))

    # head: the registry must carry the integration branch tip (or, when no
    # tip is resolvable, at least the terminal report head) — UNLESS the row
    # declares TERMINAL_ANCHOR identity (MDP-V2R1 A4): then head IS the
    # terminal anchor, and evidence-only descendants standing after the
    # anchor are NOT staleness (deeper ancestry/allowlist checking is
    # governance.terminal_identity's job, folded in via identity_result).
    head = registry_row.get("head")
    anchor = registry_row.get("terminal_anchor_sha")
    if (registry_row.get("head_semantics") == "TERMINAL_ANCHOR"
            and isinstance(anchor, str)):
        if head != anchor:
            findings.append(_finding(
                "REGISTRY_HEAD_STALE", "registry", "head", head, anchor,
                f"registry head {head!r} != declared terminal_anchor_sha "
                f"{anchor!r} (TERMINAL_ANCHOR identity binds head to the "
                "anchor; live branch descendants are judged by "
                "governance.terminal_identity, never by head repinning)"))
        return

    expected_head = branch_tip if branch_tip else report["head_integration"]
    if head != expected_head:
        findings.append(_finding(
            "REGISTRY_HEAD_STALE", "registry", "head", head, expected_head,
            f"registry head {head!r} != integration branch tip "
            f"{expected_head!r} (terminal reconciliation updates the row via "
            "researchctl cycle update with CAS+journal)"))

    worktree = registry_row.get("integration_worktree")
    if not (isinstance(worktree, str) and worktree.strip()):
        findings.append(_finding(
            "REGISTRY_WORKTREE_MISSING", "registry", "integration_worktree",
            worktree, "<non-empty historical worktree path>",
            "registry integration_worktree is empty - the historical "
            "worktree path must be recorded (non-empty) at terminal",
            coverage_rule=_COVERAGE_NONEMPTY_STR))


# ------------------------------------------------------------ addendum layer

def _validate_addendum(addendum, report: dict) -> list:
    problems = []
    if not isinstance(addendum, dict):
        return ["addendum must be an object"]
    if addendum.get("schema") != ADDENDUM_SCHEMA:
        problems.append(f"schema must be {ADDENDUM_SCHEMA!r}, "
                        f"got {addendum.get('schema')!r}")
    if addendum.get("cycle") != report.get("cycle"):
        problems.append(f"cycle {addendum.get('cycle')!r} does not bind the "
                        f"terminal report cycle {report.get('cycle')!r}")
    entries = addendum.get("supersedes_fields")
    if not (isinstance(entries, list) and entries):
        problems.append("supersedes_fields must be a non-empty list")
    else:
        for i, e in enumerate(entries):
            if not isinstance(e, dict):
                problems.append(f"supersedes_fields[{i}] must be an object")
                continue
            for key in ("file", "field", "stale_value", "corrected_value"):
                if key not in e:
                    problems.append(f"supersedes_fields[{i}] missing {key!r}")
            for key in ("file", "field"):
                if key in e and not isinstance(e[key], str):
                    problems.append(f"supersedes_fields[{i}].{key} must be "
                                    "a string")
    if not isinstance(addendum.get("evidence"), list):
        problems.append("evidence must be a list")
    if not _UTC.match(addendum.get("created_utc") or ""):
        problems.append("created_utc must be UTC ISO8601 Z-form")
    return problems


def _entry_covers(entry: dict, f: dict) -> bool:
    if (entry.get("file") != f["file"]) or (entry.get("field") != f["field"]):
        return False
    if entry.get("stale_value") != f["observed"]:
        return False
    corrected = entry.get("corrected_value")
    rule = f["coverage_rule"]
    if rule == _COVERAGE_NONEMPTY_STR:
        return isinstance(corrected, str) and bool(corrected.strip())
    if rule == _COVERAGE_DEAD_PREFIX:
        return isinstance(corrected, str) and \
            corrected.startswith(GO_DEAD_PREFIX)
    return corrected == f["expected"]


# ---------------------------------------------------------------- public API

def validate_terminal_consistency(terminal_report: dict, state: dict,
                                  heartbeat: dict, worktree_manifest: dict,
                                  registry_row: dict, branch_tip: str,
                                  event_log_lines: list,
                                  addendum: dict = None,
                                  identity_result: dict = None) -> list:
    """Reconcile a terminal cycle's artifacts. [] = consistent.

    Findings are [{"kind", "severity", "detail"}, ...]. A well-formed
    addendum that names every stale field with its exact observed stale
    value and the derived corrected value suppresses exactly those
    findings; anything less leaves them standing (fail closed). Inputs are
    never mutated and no file is ever written.

    MDP-V2R1 A4 hook: ``identity_result`` (a governance.terminal_identity
    validate_terminal_identity result dict) is optional; None (the default)
    keeps the historical behavior exactly. When provided, its findings are
    folded into the returned list AFTER addendum coverage — terminal identity
    violations are structural, never addendum-coverable (a new anchor after
    A7 audit is the only cure).
    """
    findings: list[dict] = []
    events = _check_event_log(findings, event_log_lines)
    report_ok = _check_terminal_report(findings, terminal_report)
    if report_ok:
        expected_phase = _expected_terminal_phase(events)
        _check_state(findings, state, terminal_report, expected_phase)
        _check_heartbeat(findings, heartbeat, terminal_report, expected_phase)
        _check_manifest(findings, worktree_manifest)
        _check_registry(findings, registry_row, terminal_report, branch_tip)

    if addendum is not None:
        problems = _validate_addendum(addendum, terminal_report or {})
        if problems:
            findings.append(_finding(
                "ADDENDUM_INVALID", "addendum", "schema",
                (addendum or {}).get("schema")
                if isinstance(addendum, dict) else "<not an object>",
                ADDENDUM_SCHEMA,
                "terminal addendum rejected, corrections NOT applied: "
                + "; ".join(problems), coverable=False))
        else:
            entries = addendum["supersedes_fields"]
            findings = [f for f in findings
                        if not (f["coverable"]
                                and any(_entry_covers(e, f)
                                        for e in entries))]

    out = [{"kind": f["kind"], "severity": f["severity"],
            "detail": f["detail"]} for f in findings]
    if identity_result is not None:
        out.extend({"kind": f.get("kind"), "severity": f.get("severity"),
                    "detail": f.get("detail")}
                   for f in (identity_result.get("findings") or []))
    return out


# ------------------------------------------------------------ run-dir loader

def _load_json(path: Path):
    try:
        return json.loads(path.read_bytes().decode("utf-8")), None
    except FileNotFoundError:
        return None, "missing"
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"unreadable: {exc}"


def _resolve_branch_tip(run_dir: Path, branch: str):
    """Best-effort branch tip via git; None when unresolvable (tests, bare dirs)."""
    for ref in (branch, "HEAD"):
        if not ref:
            continue
        out = subprocess.run(["git", "-C", str(run_dir), "rev-parse", ref],
                             capture_output=True, text=True)
        tip = out.stdout.strip()
        if out.returncode == 0 and _HEX40.match(tip):
            return tip
    return None


def check_v1_run_dir(run_dir: Path, addendum: dict = None) -> list:
    """Convenience loader for the real run-dir file shapes (read-only).

    Loads terminal_report/state/heartbeat/worktree_manifest/event_log from
    ``run_dir`` and the canonical registry row from
    ``<root>/plans/CYCLE_REGISTRY.json`` (root = run_dir.parents[2]);
    the branch tip is resolved with git when possible. Missing or
    unreadable files are themselves findings; the historical bytes are
    never modified.
    """
    run_dir = Path(run_dir)
    file_findings = []
    loaded = {}

    for name in ("terminal_report.json", "state.json", "heartbeat.json",
                 "worktree_manifest.json"):
        obj, err = _load_json(run_dir / name)
        if err == "missing":
            file_findings.append(_finding(
                "RUN_FILE_MISSING", name, "file", None,
                "<present run-control artifact>",
                f"{name} missing from run dir {run_dir}", coverable=False))
            obj = {}
        elif err is not None:
            file_findings.append(_finding(
                "RUN_FILE_UNREADABLE", name, "file", None,
                "<valid UTF-8 JSON>", f"{name}: {err}", coverable=False))
            obj = {}
        loaded[name] = obj

    lines, err = None, None
    log_path = run_dir / "event_log.jsonl"
    if not log_path.exists():
        file_findings.append(_finding(
            "RUN_FILE_MISSING", "event_log.jsonl", "file", None,
            "<present append-only event log>",
            f"event_log.jsonl missing from run dir {run_dir}",
            coverable=False))
        lines = []
    else:
        try:
            lines = log_path.read_bytes().decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            file_findings.append(_finding(
                "RUN_FILE_UNREADABLE", "event_log.jsonl", "file", None,
                "<valid UTF-8 JSONL>", f"event_log.jsonl: {exc}",
                coverable=False))
            lines = []

    # canonical registry row (root = <root>/research/control/<run_dir>)
    registry_row = None
    report = loaded["terminal_report.json"]
    if isinstance(report, dict) and isinstance(report.get("cycle"), str):
        registry, reg_err = _load_json(
            run_dir.parents[2] / "plans" / "CYCLE_REGISTRY.json")
        if reg_err is None and isinstance(registry, dict):
            for rec in registry.get("cycles", []) or []:
                if isinstance(rec, dict) \
                        and rec.get("cycle_id") == report["cycle"]:
                    registry_row = rec
                    break

    branch_tip = None
    if isinstance(registry_row, dict):
        branch_tip = _resolve_branch_tip(run_dir,
                                         registry_row.get("branch") or "")

    findings = file_findings + validate_terminal_consistency(
        loaded["terminal_report.json"], loaded["state.json"],
        loaded["heartbeat.json"], loaded["worktree_manifest.json"],
        registry_row, branch_tip, lines, addendum)
    return [{"kind": f["kind"], "severity": f["severity"],
             "detail": f["detail"]} for f in findings]
