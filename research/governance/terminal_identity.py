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
    research/audits/<audit_dir>/**           independent audit artifacts
    plans/CYCLE_REGISTRY.json                canonical registry (approved writer)
    plans/CYCLE_REGISTRY.events.jsonl        canonical journal (append-only)
    plans/ACTIVE_CYCLES.json                 canonical projection (generated)

``<cycle_dir>`` derives from ``cycle_id`` by lowercasing + dashes -> underscores
+ the "_run" suffix (MARKET-DATA-PLANE-V2 -> market_data_plane_v2_run) — the
control dirs convention. ``<audit_dir>`` is the same derivation WITHOUT the
"_run" suffix (MARKET-DATA-PLANE-V2R1 -> market_data_plane_v2r1), matching the
repo convention research/audits/market_data_plane_v2r1/ (A4-r2 fix: the audits
tree never carries the _run suffix). Explicit ``cycle_dir=``/``audit_dir=``
override params win over both derivations. The allowlist itself never
contains code/tests/plan-file patterns — only the two evidence dirs and the
three registry surfaces.

SCOPED PATH SEMANTICS (A4-r2 fix): a terminal row polices ITS OWN
post-terminal evidence. Each changed path in the anchor..tip diff is
classified:

    PROTECTED-GLOBAL  research/wayfinder/HYPOTHESIS_LEDGER.md and
                      research/wayfinder/SURVIVORS.md — a descendant diff
                      touching one of them is TERMINAL_IDENTITY_FORBIDDEN_PATH
                      HIGH for EVERY row, never allowlist-sanctionable
                      (ledger/denominator/S1-adjacent protection, plan rule
                      6). SUCCESSOR-ANCHOR RULE (plan §12.2): a touch that is
                      already covered by a SUCCESSOR's declared terminal
                      anchor (another TERMINAL_ANCHOR row in the canonical
                      registry) is the successor row's business, not this
                      row's — it is listed informationally in
                      foreign_scope_paths instead of firing here. The
                      successor anchors are read from
                      plans/CYCLE_REGISTRY.json under repo_root (read-only,
                      best-effort: an unreadable/malformed registry yields no
                      exemptions, so the guard fails closed);
    OWN-SCOPE         paths matching the row's own control-dir / audit-dir
                      scope patterns or the canonical registry surfaces —
                      these MUST match the allowlist (evidence-only), else
                      TERMINAL_IDENTITY_FORBIDDEN_PATH HIGH exactly as before;
    FOREIGN-SCOPE     everything else — other cycles' code/tests/plans and
                      shared implementation. NOT a finding for this row;
                      listed in the result's ``foreign_scope_paths`` for
                      operator visibility.

SUCCESSOR-ANCHOR RULE (plan §12.2): implementation/tests changes above an OLD
anchor belong to the successor cycle and are covered by the successor's OWN
row + anchor (forward-only migration) — the old row does not judge them. The
cure for a genuine post-anchor change inside a cycle's own scope is a NEW
anchor after A7 re-audit, written ONCE via
``cycle_registry.redeclare_terminal_identity``, which verifies the old anchor
is a git ANCESTOR of the new one: migrations only ever move forward and are
never caused by validation itself (a repin loop is structurally impossible).

Public API (frozen):
    validate_terminal_identity(registry_row, branch_tip, repo_root, *,
                               cycle_id, event_log_relpath=None,
                               terminal_report_head=None, allowlist=None,
                               cycle_dir=None, audit_dir=None) -> dict
        {"findings": [{"kind","severity","detail"}, ...],
         "branch_tip": <live tip actually used, always surfaced>,
         "terminal_anchor_sha": <anchor from the row, or None>,
         "descendant_commits": [shas strictly after the anchor, oldest first],
         "foreign_scope_paths": [changed paths outside this row's scope]}

    derive_cycle_dir(cycle_id) / derive_audit_dir(cycle_id) /
    default_allowlist(cycle_dir, audit_dir=None)

    declare-side writers live in governance.cycle_registry
    (declare_terminal_identity, redeclare_terminal_identity); this module is
    read-only.

Read-only: this module never writes a file; every git invocation is a
read-only subcommand (rev-parse/cat-file/merge-base/diff/rev-list/show) with
an explicit ``-C repo_root``.
"""
from __future__ import annotations

import fnmatch
import json
import os
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

# A4-r2: global invariants no post-terminal descendant may ever touch, for
# ANY row and regardless of any allowlist override (ledger / denominator /
# S1-adjacent files, plan rule 6).
PROTECTED_GLOBAL_PATHS = (
    "research/wayfinder/HYPOTHESIS_LEDGER.md",
    "research/wayfinder/SURVIVORS.md",
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
_REGISTRY_REL = "plans/CYCLE_REGISTRY.json"


# ------------------------------------------------------------------ helpers

def _finding(kind: str, detail: str) -> dict:
    return {"kind": kind, "severity": SEVERITY[kind], "detail": detail}


def derive_cycle_dir(cycle_id: str) -> str:
    """Control dir: MARKET-DATA-PLANE-V2 -> market_data_plane_v2_run (§12.2)."""
    return str(cycle_id).strip().lower().replace("-", "_") + "_run"


def derive_audit_dir(cycle_id: str) -> str:
    """Audit dir: MARKET-DATA-PLANE-V2R1 -> market_data_plane_v2r1.

    Repo convention: research/audits/<cycle>/ carries NO "_run" suffix (the
    real artifacts live at research/audits/market_data_plane_v2r1/, while the
    control tree is research/control/market_data_plane_v2r1_run/)."""
    return str(cycle_id).strip().lower().replace("-", "_")


def _audit_dir_fallback(cycle_dir: str) -> str:
    """Inverse of the control-dir derivation: drop the _run suffix."""
    return cycle_dir[:-4] if cycle_dir.endswith("_run") else cycle_dir


def default_allowlist(cycle_dir: str, audit_dir: "str | None" = None) -> tuple:
    """The frozen §12.2 allowlist for one cycle: control evidence, audit
    artifacts and the registry surfaces ONLY — never code/tests/plans-docs/
    ledgers/results. Audit patterns use ``audit_dir`` (defaults to the
    cycle_dir with its "_run" suffix dropped)."""
    if audit_dir is None:
        audit_dir = _audit_dir_fallback(cycle_dir)
    return (
        f"research/control/{cycle_dir}/**",
        f"research/audits/{audit_dir}/**",
    ) + REGISTRY_SURFACE_PATHS


def _own_scope_patterns(cycle_dir: str, audit_dir: str) -> tuple:
    """The row's OWN evidence scope: its control dir, its audit dir and the
    canonical registry surfaces. Only own-scope paths are allowlist-policed."""
    return (
        f"research/control/{cycle_dir}/**",
        f"research/audits/{audit_dir}/**",
    ) + REGISTRY_SURFACE_PATHS


def _classify_path(path: str, own_scope: tuple) -> str:
    """'protected' | 'own' | 'foreign' for one changed path."""
    for protected in PROTECTED_GLOBAL_PATHS:
        if path == protected or path.startswith(protected + "/"):
            return "protected"
    if any(fnmatch.fnmatchcase(path, pat) for pat in own_scope):
        return "own"
    return "foreign"


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


def _touching_commits(repo_root: str, anchor: str, tip: str,
                      path: str) -> "list | None":
    """Descendant commits (anchor..tip) whose diff touches `path`, oldest
    first; None when git fails (callers fail closed on None)."""
    rc, out = _git(repo_root, "rev-list", "--reverse",
                   f"{anchor}..{tip}", "--", path)
    if rc != 0:
        return None
    return [ln for ln in out.splitlines() if ln.strip()]


def _declared_terminal_anchors(repo_root: str, exclude: "str | None") -> list:
    """Declared TERMINAL_ANCHOR anchors from the canonical registry under
    repo_root (read-only, best-effort), excluding `exclude`.

    Successor-anchor rule (plan §12.2): a post-terminal touch covered by a
    successor's audited anchor is the successor row's business. An
    unreadable/malformed registry yields [] — no exemptions, fail closed.
    """
    try:
        with open(os.path.join(repo_root, _REGISTRY_REL), "rb") as fh:
            data = json.loads(fh.read().decode("utf-8"))
    except (OSError, ValueError):
        return []
    anchors = set()
    for rec in (data.get("cycles") or []) if isinstance(data, dict) else []:
        if not isinstance(rec, dict):
            continue
        sha = rec.get("terminal_anchor_sha")
        if rec.get("head_semantics") == HEAD_SEMANTICS \
                and isinstance(sha, str) and _HEX40.match(sha) \
                and sha != exclude:
            anchors.add(sha)
    return sorted(anchors)


def _successor_covered(repo_root: str, commits: "list | None",
                       successor_anchors: list) -> bool:
    """True iff every touching commit is an ancestor of at least one
    successor's declared terminal anchor (unknown touches never count as
    covered — fail closed)."""
    if not commits or not successor_anchors:
        return False
    return all(any(_is_ancestor(repo_root, c, s) for s in successor_anchors)
               for c in commits)


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


def _result(findings: list, branch_tip, anchor, descendants: list,
            foreign_scope_paths: "list | None" = None) -> dict:
    return {
        "findings": findings,
        "branch_tip": branch_tip,
        "terminal_anchor_sha": anchor,
        "descendant_commits": descendants,
        "foreign_scope_paths": sorted(foreign_scope_paths or []),
    }


# ---------------------------------------------------------------- public API

def validate_terminal_identity(registry_row, branch_tip, repo_root, *,
                               cycle_id: "str | None" = None,
                               event_log_relpath: "str | None" = None,
                               terminal_report_head: "str | None" = None,
                               allowlist: "list | tuple | None" = None,
                               cycle_dir: "str | None" = None,
                               audit_dir: "str | None" = None) -> dict:
    """Validate a cycle row's terminal identity against the live branch tip.

    Fail-closed rules (plan §12.1):
      1. SHA grammar: 40 lowercase hex for head / terminal_anchor_sha;
      2. anchor exists (cat-file) and IS an ancestor of the live tip
         (merge-base --is-ancestor);
      3. terminal report/addendum binding is the CALLER's responsibility;
         pass ``terminal_report_head`` to cross-check it == anchor;
      4. the full diff anchor..branch_tip is inspected by changed path;
      5. path classification (A4-r2 scoped semantics): PROTECTED-GLOBAL paths
         (research/wayfinder/HYPOTHESIS_LEDGER.md, research/wayfinder/
         SURVIVORS.md) fail HIGH for every row unless the touch is already
         covered by a successor's declared terminal anchor (plan §12.2 —
         informational then); OWN-SCOPE paths (the row's own control/audit
         dirs + registry surfaces) must match the allowlist; FOREIGN-SCOPE
         paths are not findings for this row and are only listed in
         ``foreign_scope_paths``;
      6. HIGH fail when an own-scope descendant path is not on the
         allowlist, or when an event_log.jsonl under the cycle dir (or the
         canonical journal, or an explicitly named event log) loses the
         anchor version as its byte-prefix (line-wise) — historical event
         lines are append-only;
      7. HIGH fail on non-ancestor anchor, missing/malformed branch tip,
         malformed row (head != terminal_anchor_sha, unknown head_semantics,
         missing/unknown post_terminal_policy, partial/ambiguous declaration);
      8. NO staleness/penalty merely because evidence-only closure commits
         stand after the anchor (that is the whole point of the anchor);
      9. a legacy TERMINAL row WITHOUT head_semantics yields the visible
         MEDIUM compatibility finding TERMINAL_IDENTITY_UNDECLARED — never
         silently normalized, never auto-passed;
      10. the live branch tip is ALWAYS surfaced in the result.

    Foreign-scope changes above an old anchor (successor-cycle implementation,
    plan §12.2) are the successor's own row+anchor business: they are listed,
    never judged here, and the migration to a new anchor is forward-only via
    cycle_registry.redeclare_terminal_identity.

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
    if audit_dir is None:
        audit_dir = derive_audit_dir(cycle_id) if cycle_id \
            else _audit_dir_fallback(cycle_dir)

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
    foreign_scope_paths: list = []
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
            # rules 4-6: inspect the full diff anchor..tip by changed path,
            # scoped to this row's own evidence (A4-r2 semantics)
            descendants = _descendant_commits(repo_root, anchor, live_tip)
            changed = _changed_paths(repo_root, anchor, live_tip)
            allowed = tuple(allowlist) if allowlist is not None \
                else default_allowlist(cycle_dir, audit_dir)
            own_scope = _own_scope_patterns(cycle_dir, audit_dir)
            successor_anchors = None  # resolved lazily, only if ever needed
            for path in changed:
                scope = _classify_path(path, own_scope)
                if scope == "foreign":
                    # other cycles' code/tests/plans etc.: the successor's
                    # own row+anchor polices them (plan §12.2) — surface
                    # only, never a finding for THIS row.
                    foreign_scope_paths.append(path)
                    continue
                if scope == "protected":
                    if successor_anchors is None:
                        successor_anchors = _declared_terminal_anchors(
                            repo_root, exclude=anchor)
                    touching = _touching_commits(repo_root, anchor, live_tip,
                                                 path)
                    if _successor_covered(repo_root, touching,
                                          successor_anchors):
                        # successor-anchor rule (plan §12.2): the touch is
                        # already covered by a successor's audited anchor —
                        # the successor's own row polices it; informational
                        # here, never a finding for THIS row.
                        foreign_scope_paths.append(path)
                        continue
                    findings.append(_finding(
                        "TERMINAL_IDENTITY_FORBIDDEN_PATH",
                        f"post-terminal descendant commit(s) modify "
                        f"{path!r} which is a PROTECTED GLOBAL path "
                        f"{list(PROTECTED_GLOBAL_PATHS)} — the hypothesis "
                        "ledger / survivor denominator can never be edited "
                        "after any terminal anchor (never allowlist-"
                        "sanctionable); a corrected denominator requires a "
                        "new audited cycle"))
                    continue
                if not any(fnmatch.fnmatchcase(path, pat) for pat in allowed):
                    findings.append(_finding(
                        "TERMINAL_IDENTITY_FORBIDDEN_PATH",
                        f"post-terminal descendant commit(s) modify {path!r} "
                        f"inside this row's own evidence scope, which is "
                        f"outside the {POST_TERMINAL_POLICY!r} allowlist "
                        f"{list(allowed)} — own-scope evidence is append-"
                        "only; a substantive change needs a NEW anchor after "
                        "A7 audit, not an allowlist"))
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

    return _result(findings, live_tip, anchor, descendants,
                   foreign_scope_paths)


# ----------------------------------------------------------------- selfcheck

def _selfcheck() -> int:
    """Print the frozen contract; exit 0 when the frozen invariants hold."""
    assert HEAD_SEMANTICS == "TERMINAL_ANCHOR"
    assert POST_TERMINAL_POLICY == "ALLOWLISTED_APPEND_ONLY_DESCENDANTS"
    assert derive_cycle_dir("MARKET-DATA-PLANE-V2") == \
        "market_data_plane_v2_run"
    assert derive_audit_dir("MARKET-DATA-PLANE-V2R1") == \
        "market_data_plane_v2r1"
    allowed = default_allowlist(derive_cycle_dir("MARKET-DATA-PLANE-V2R1"))
    assert f"research/control/market_data_plane_v2r1_run/**" in allowed
    assert f"research/audits/market_data_plane_v2r1/**" in allowed  # no _run
    assert not any("_run/**" in p and p.startswith("research/audits/")
                   for p in allowed)
    for surface in REGISTRY_SURFACE_PATHS:
        assert surface in default_allowlist("x"), surface
    assert not any(p.startswith("research/") and p.endswith(".py")
                   for p in default_allowlist("x"))
    assert PROTECTED_GLOBAL_PATHS == (
        "research/wayfinder/HYPOTHESIS_LEDGER.md",
        "research/wayfinder/SURVIVORS.md")
    print("terminal_identity selfcheck OK: "
          f"head_semantics={HEAD_SEMANTICS} "
          f"post_terminal_policy={POST_TERMINAL_POLICY} "
          f"registry_surfaces={list(REGISTRY_SURFACE_PATHS)} "
          f"protected_global={list(PROTECTED_GLOBAL_PATHS)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_selfcheck())
