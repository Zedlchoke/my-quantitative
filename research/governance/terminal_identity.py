"""Terminal identity contract v2 (plan PLAN_market_data_plane_v2r1 §12, lane A4).

FROZEN SEMANTIC DECISION (§12.1): a commit cannot contain its own SHA, so a
TERMINAL registry row that pins ``head`` to the LIVE integration branch tip
forces a repin commit for every reconciliation — and that repin commit is
itself a new tip, re-breaking the check. Structural self-reference. From V2R1:

    terminal_anchor_sha = the last commit containing the code/evidence the
                          auditor (A7) audited
    branch_tip          = resolved LIVE whenever the validator runs

Persisting a requirement that branch_tip == a SHA inside the branch-tip
commit is FORBIDDEN by design. A TERMINAL row instead declares explicit,
additive semantics on the cycle_registry@1 row (rows without them stay valid
legacy rows):

    {"head": <terminal_anchor_sha>,
     "head_semantics": "TERMINAL_ANCHOR",
     "terminal_anchor_sha": <same 40-hex SHA>,
     "post_terminal_policy": "ALLOWLISTED_APPEND_ONLY_DESCENDANTS"}

Post-terminal descendants (evidence-only closure commits) are permitted only
on the DEFAULT ALLOWLIST (§12.2, overridable by an explicit param):

    research/control/<cycle_dir>/**          reconciliation/addendum/gate evidence
    research/audits/<cycle_dir>/**           independent audit artifacts
    plans/CYCLE_REGISTRY.json                canonical registry (approved writer)
    plans/CYCLE_REGISTRY.events.jsonl        canonical journal (append-only)
    plans/ACTIVE_CYCLES.json                 canonical projection (generated)

``<cycle_dir>`` derives from ``cycle_id`` by lowercasing + dashes -> underscores
+ the "_run" suffix (MARKET-DATA-PLANE-V2 -> market_data_plane_v2_run), with an
explicit override param. Code, tests, fixtures, plans (other than the registry
surfaces), ledgers/denominators/S1/survivor files, research results and
historical event lines are NEVER allowlisted: if V2R1 changes code/tests after
an old anchor, it needs a NEW anchor after A7 — the allowlist cannot hide an
implementation change.

Public API (frozen):
    validate_terminal_identity(registry_row, branch_tip, repo_root, *,
                               cycle_id, event_log_relpath=None,
                               terminal_report_head=None, allowlist=None,
                               cycle_dir=None) -> dict
        {"findings": [{"kind","severity","detail"}, ...],
         "branch_tip": <live tip actually used, always surfaced>,
         "terminal_anchor_sha": <anchor from the row, or None>,
         "descendant_commits": [shas strictly after the anchor, oldest first]}

    declare-side writer lives in governance.cycle_registry
    (declare_terminal_identity); this module is read-only.

Read-only: this module never writes a file; every git invocation is a
read-only subcommand (rev-parse/cat-file/merge-base/diff/rev-list/show) with
an explicit ``-C repo_root``.
"""
from __future__ import annotations

import fnmatch
import re
import subprocess

HEAD_SEMANTICS = "TERMINAL_ANCHOR"
POST_TERMINAL_POLICY = "ALLOWLISTED_APPEND_ONLY_DESCENDANTS"
IDENTITY_FIELDS = ("head_semantics", "terminal_anchor_sha", "post_terminal_policy")

REGISTRY_SURFACE_PATHS = (
    "plans/CYCLE_REGISTRY.json",
    "plans/CYCLE_REGISTRY.events.jsonl",
    "plans/ACTIVE_CYCLES.json",
)

_HEX40 = re.compile(r"^[0-9a-f]{40}$")

SEVERITY = {
    "TERMINAL_IDENTITY_ROW_MALFORMED": "HIGH",
    "TERMINAL_IDENTITY_MALFORMED_SHA": "HIGH",
    "TERMINAL_IDENTITY_ANCHOR_MISSING": "HIGH",
    "TERMINAL_IDENTITY_NOT_ANCESTOR": "HIGH",
    "TERMINAL_IDENTITY_BRANCH_MISSING": "HIGH",
    "TERMINAL_IDENTITY_REPORT_MISMATCH": "HIGH",
    "TERMINAL_IDENTITY_FORBIDDEN_PATH": "HIGH",
    "TERMINAL_IDENTITY_EVENT_LOG_REWRITTEN": "HIGH",
    "TERMINAL_IDENTITY_UNDECLARED": "MEDIUM",  # legacy-row compatibility finding
}

_EVENT_LOG_BASENAME = "event_log.jsonl"
_JOURNAL_REL = "plans/CYCLE_REGISTRY.events.jsonl"


# ------------------------------------------------------------------ helpers

def _finding(kind: str, detail: str) -> dict:
    return {"kind": kind, "severity": SEVERITY[kind], "detail": detail}


def derive_cycle_dir(cycle_id: str) -> str:
    """MARKET-DATA-PLANE-V2 -> market_data_plane_v2_run (frozen §12.2)."""
    return str(cycle_id).strip().lower().replace("-", "_") + "_run"


def default_allowlist(cycle_dir: str) -> tuple:
    """The frozen §12.2 allowlist for one cycle. Never contains code/tests/
    plans-other-than-registry/ledgers/research results."""
    return (
        f"research/control/{cycle_dir}/**",
        f"research/audits/{cycle_dir}/**",
    ) + REGISTRY_SURFACE_PATHS


def _git(repo_root: str, *args: str, binary: bool = False):
    out = subprocess.run(["git", "-C", repo_root, *args], capture_output=True)
    if binary:
        return out.returncode, out.stdout
    return out.returncode, out.stdout.decode("utf-8", "replace").strip()


def resolve_branch_tip(repo_root) -> "str | None":
    """Live branch tip via ``git rev-parse HEAD``; None when unresolvable."""
    rc, out = _git(str(repo_root), "rev-parse", "HEAD")
    return out if rc == 0 and _HEX40.match(out) else None


def _commit_exists(repo_root: str, sha: str) -> bool:
    rc, _ = _git(repo_root, "cat-file", "-e", f"{sha}^{{commit}}")
    return rc == 0


def _is_ancestor(repo_root: str, ancestor: str, descendant: str) -> bool:
    rc, _ = _git(repo_root, "merge-base", "--is-ancestor", ancestor, descendant)
    return rc == 0


def _changed_paths(repo_root: str, frm: str, to: str) -> list:
    rc, out = _git(repo_root, "diff", "--name-only", frm, to)
    if rc != 0:
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def _descendant_commits(repo_root: str, anchor: str, tip: str) -> list:
    """Commits reachable from tip but not from the anchor, oldest first."""
    rc, out = _git(repo_root, "rev-list", "--reverse", f"{anchor}..{tip}")
    if rc != 0:
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def _blob_lines(repo_root: str, rev: str, path: str) -> list:
    """The file's lines at a revision (bytes split on newlines); [] if absent."""
    rc, out = _git(repo_root, "show", f"{rev}:{path}", binary=True)
    if rc != 0:
        return []
    return out.splitlines()


def _is_line_prefix(anchor_lines: list, tip_lines: list) -> bool:
    """Append-only: the anchor version must be a line-wise byte-prefix of the
    tip version. Deletions, reorderings and rewrites fail."""
    if len(tip_lines) < len(anchor_lines):
        return False
    return anchor_lines == tip_lines[:len(anchor_lines)]


def _event_log_paths(changed: list, cycle_dir: str,
                     event_log_relpath: "str | None") -> list:
    """Changed files that are append-only event logs: the cycle's event_log
    (when named, and any event_log.jsonl under the cycle dir) plus the
    canonical registry journal."""
    paths = []
    cycle_prefix = f"research/control/{cycle_dir}/"
    for path in changed:
        if path == _JOURNAL_REL:
            paths.append(path)
        elif event_log_relpath and path == event_log_relpath:
            paths.append(path)
        elif path.startswith(cycle_prefix) and \
                path.rsplit("/", 1)[-1] == _EVENT_LOG_BASENAME:
            paths.append(path)
    return sorted(set(paths))


def _result(findings: list, branch_tip, anchor, descendants: list) -> dict:
    return {
        "findings": findings,
        "branch_tip": branch_tip,
        "terminal_anchor_sha": anchor,
        "descendant_commits": descendants,
    }


# ---------------------------------------------------------------- public API

def validate_terminal_identity(registry_row, branch_tip, repo_root, *,
                               cycle_id: "str | None" = None,
                               event_log_relpath: "str | None" = None,
                               terminal_report_head: "str | None" = None,
                               allowlist: "list | tuple | None" = None,
                               cycle_dir: "str | None" = None) -> dict:
    """Validate a cycle row's terminal identity against the live branch tip.

    Fail-closed rules (plan §12.1):
      1. SHA grammar: 40 lowercase hex for head / terminal_anchor_sha;
      2. anchor exists (cat-file) and IS an ancestor of the live tip
         (merge-base --is-ancestor);
      3. terminal report/addendum binding is the CALLER's responsibility;
         pass ``terminal_report_head`` to cross-check it == anchor;
      4. the full diff anchor..branch_tip is inspected by changed path;
      5. only allowlisted append-only descendant paths are permitted
         (DEFAULT allowlist is frozen, ``allowlist=`` overrides explicitly);
      6. HIGH fail when a descendant modifies implementation, tests,
         fixtures, plans (other than the registry surfaces), ledger /
         denominator / S1 / survivor files, research results, or historical
         event lines — an event_log.jsonl under the cycle dir (and the
         canonical journal) must keep the anchor version as a byte-prefix
         (line-wise) of the tip version;
      7. HIGH fail on non-ancestor anchor, missing/malformed branch tip,
         malformed row (head != terminal_anchor_sha, unknown head_semantics,
         missing/unknown post_terminal_policy, partial/ambiguous declaration);
      8. NO staleness/penalty merely because evidence-only closure commits
         stand after the anchor (that is the whole point of the anchor);
      9. a legacy TERMINAL row WITHOUT head_semantics yields the visible
         MEDIUM compatibility finding TERMINAL_IDENTITY_UNDECLARED — never
         silently normalized, never auto-passed;
      10. the live branch tip is ALWAYS surfaced in the result.

    Idempotent: no state is written, so repeated runs at the same tip return
    identical results and never require a new repin commit.
    """
    repo_root = str(repo_root)
    if cycle_dir is None:
        if not cycle_id:
            raise ValueError(
                "validate_terminal_identity: cycle_id (or explicit cycle_dir) "
                "is required to scope the descendant allowlist")
        cycle_dir = derive_cycle_dir(cycle_id)

    row = registry_row if isinstance(registry_row, dict) else {}

    # rule 10: resolve the live tip first; it is surfaced in every result.
    live_tip = branch_tip if branch_tip else resolve_branch_tip(repo_root)
    tip_ok = isinstance(live_tip, str) and bool(_HEX40.match(live_tip))
    if branch_tip and not tip_ok:
        live_tip = None

    lifecycle = row.get("lifecycle")
    declared = any(k in row for k in IDENTITY_FIELDS)

    if not declared:
        if lifecycle == "TERMINAL":
            findings = [_finding(
                "TERMINAL_IDENTITY_UNDECLARED",
                f"TERMINAL row {row.get('cycle_id', '?')!r} carries no "
                f"head_semantics declaration: legacy rows pin head to a "
                "branch tip that moves, so every reconciliation re-breaks "
                "the check. Declare TERMINAL_ANCHOR identity via "
                "cycle_registry.declare_terminal_identity (never normalize "
                "silently).")]
            return _result(findings, live_tip, None, [])
        # non-terminal rows and rows with nothing to validate: PASS context
        # (informational — terminal identity semantics do not apply).
        return _result([], live_tip, None, [])

    findings: list = []
    anchor = row.get("terminal_anchor_sha")
    head = row.get("head")

    # rule 1 + 7: strict shape of a declared row
    if row.get("head_semantics") != HEAD_SEMANTICS:
        findings.append(_finding(
            "TERMINAL_IDENTITY_ROW_MALFORMED",
            f"unknown head_semantics {row.get('head_semantics')!r} — the only "
            f"declared semantics is {HEAD_SEMANTICS!r}"))
    if not (isinstance(anchor, str) and _HEX40.match(anchor)):
        findings.append(_finding(
            "TERMINAL_IDENTITY_MALFORMED_SHA",
            f"terminal_anchor_sha {anchor!r} is not a 40-lowercase-hex sha"))
        anchor = None
    if not (isinstance(head, str) and _HEX40.match(head)):
        findings.append(_finding(
            "TERMINAL_IDENTITY_MALFORMED_SHA",
            f"head {head!r} is not a 40-lowercase-hex sha"))
    elif anchor is not None and head != anchor:
        findings.append(_finding(
            "TERMINAL_IDENTITY_ROW_MALFORMED",
            f"head {head!r} != terminal_anchor_sha {anchor!r} — under "
            f"{HEAD_SEMANTICS!r} the row head IS the terminal anchor"))
    if row.get("post_terminal_policy") != POST_TERMINAL_POLICY:
        findings.append(_finding(
            "TERMINAL_IDENTITY_ROW_MALFORMED",
            f"post_terminal_policy must be {POST_TERMINAL_POLICY!r} when "
            f"present/declared, got {row.get('post_terminal_policy')!r}"))
    if lifecycle != "TERMINAL":
        findings.append(_finding(
            "TERMINAL_IDENTITY_ROW_MALFORMED",
            f"terminal identity declared on a non-TERMINAL row "
            f"(lifecycle {lifecycle!r}) — identity semantics apply only to "
            "closed cycles"))

    # rule 3: optional terminal report cross-check
    if terminal_report_head is not None and terminal_report_head != anchor:
        findings.append(_finding(
            "TERMINAL_IDENTITY_REPORT_MISMATCH",
            f"terminal report head {terminal_report_head!r} does not bind the "
            f"terminal anchor {anchor!r} — the report must be audited against "
            "the same commit the row declares"))

    descendants: list = []
    if anchor is not None:
        if not tip_ok:
            findings.append(_finding(
                "TERMINAL_IDENTITY_BRANCH_MISSING",
                f"live branch tip unresolvable "
                f"(branch_tip={branch_tip!r}, git rev-parse HEAD failed under "
                f"{repo_root}) — ancestry cannot be judged"))
        elif not _commit_exists(repo_root, anchor):
            findings.append(_finding(
                "TERMINAL_IDENTITY_ANCHOR_MISSING",
                f"terminal anchor {anchor} does not exist as a commit under "
                f"{repo_root}"))
        elif not _is_ancestor(repo_root, anchor, live_tip):
            findings.append(_finding(
                "TERMINAL_IDENTITY_NOT_ANCESTOR",
                f"terminal anchor {anchor} is NOT an ancestor of the live "
                f"branch tip {live_tip} — the row points outside the branch "
                "history (fail closed)"))
        else:
            # rules 4-6: inspect the full diff anchor..tip by changed path
            descendants = _descendant_commits(repo_root, anchor, live_tip)
            changed = _changed_paths(repo_root, anchor, live_tip)
            allowed = tuple(allowlist) if allowlist is not None \
                else default_allowlist(cycle_dir)
            for path in changed:
                if not any(fnmatch.fnmatchcase(path, pat) for pat in allowed):
                    findings.append(_finding(
                        "TERMINAL_IDENTITY_FORBIDDEN_PATH",
                        f"post-terminal descendant commit(s) modify {path!r} "
                        f"which is outside the {POST_TERMINAL_POLICY!r} "
                        f"allowlist {list(allowed)} — code/tests/plans/"
                        "ledger/results changes after the anchor need a NEW "
                        "anchor after A7 audit, not an allowlist"))
            for path in _event_log_paths(changed, cycle_dir,
                                         event_log_relpath):
                if not _is_line_prefix(_blob_lines(repo_root, anchor, path),
                                       _blob_lines(repo_root, live_tip, path)):
                    findings.append(_finding(
                        "TERMINAL_IDENTITY_EVENT_LOG_REWRITTEN",
                        f"event log {path!r} changed after the anchor but the "
                        f"anchor version is not a byte-prefix (line-wise) of "
                        f"the tip version — historical event lines are "
                        "append-only; deletions/reorderings fail"))

    return _result(findings, live_tip, anchor, descendants)


# ----------------------------------------------------------------- selfcheck

def _selfcheck() -> int:
    """Print the frozen contract; exit 0 when the frozen invariants hold."""
    assert HEAD_SEMANTICS == "TERMINAL_ANCHOR"
    assert POST_TERMINAL_POLICY == "ALLOWLISTED_APPEND_ONLY_DESCENDANTS"
    assert derive_cycle_dir("MARKET-DATA-PLANE-V2") == \
        "market_data_plane_v2_run"
    for surface in REGISTRY_SURFACE_PATHS:
        assert surface in default_allowlist("x"), surface
    assert not any(p.startswith("research/") and p.endswith(".py")
                   for p in default_allowlist("x"))
    print("terminal_identity selfcheck OK: "
          f"head_semantics={HEAD_SEMANTICS} "
          f"post_terminal_policy={POST_TERMINAL_POLICY} "
          f"registry_surfaces={list(REGISTRY_SURFACE_PATHS)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_selfcheck())
