"""Terminal identity contract v2 tests (plan PLAN_market_data_plane_v2r1 §12, A4).

Every test builds its own SYNTHETIC git repo in tmp_path (git init -q; commits
with inline -c user.name/-c user.email; read-only validator; no network). The
validator under test is READ-ONLY: it must never write a file and never
require a repin commit — repeated runs at the same tip are idempotent.

Frozen required behavior (§12.1):
  - a TERMINAL row declares TERMINAL_ANCHOR identity (head == anchor) and the
    live branch tip is resolved per-run — no self-referential repin loop;
  - evidence-only descendants on the frozen allowlist PASS; own-scope paths
    outside the allowlist FAIL HIGH; historical event lines are append-only
    (deletions/reorderings FAIL);
  - SCOPED semantics (A4-r2): the row polices ITS OWN evidence — paths in its
    control/audit dirs + registry surfaces are OWN-SCOPE and must match the
    allowlist; research/wayfinder/HYPOTHESIS_LEDGER.md and
    research/wayfinder/SURVIVORS.md are PROTECTED-GLOBAL and fail HIGH for
    every row; everything else (other cycles' code/tests/plans — e.g. the
    successor cycle's implementation above an OLD anchor, plan §12.2) is
    FOREIGN-SCOPE: never a finding, only listed in foreign_scope_paths;
  - the audits tree carries NO "_run" suffix (research/audits/<cycle>/),
    unlike the control tree (research/control/<cycle>_run/);
  - legacy TERMINAL rows without the declaration get a visible MEDIUM
    compatibility finding — never silently normalized, never auto-passed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import terminal_identity as ti  # noqa: E402

CYCLE_ID = "TEST-CYCLE-V1"
CYCLE_DIR = ti.derive_cycle_dir(CYCLE_ID)  # test_cycle_v1_run (control tree)
CYCLE_AUDIT_DIR = ti.derive_audit_dir(CYCLE_ID)  # test_cycle_v1 (audits tree)
CYCLE_CONTROL = f"research/control/{CYCLE_DIR}"
CYCLE_AUDITS = f"research/audits/{CYCLE_AUDIT_DIR}"
JOURNAL = "plans/CYCLE_REGISTRY.events.jsonl"


# ----------------------------------------------------------------- helpers

def _git(repo, *args, check=True):
    proc = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"git {args} failed: {proc.stderr.strip()}")
    return proc


def _commit(repo, relpath, content, msg):
    """One inline-identity commit; returns the new HEAD sha."""
    path = Path(repo) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    _git(repo, "add", relpath)
    _git(repo, "-c", "user.name=A4 Test", "-c", "user.email=a4@test.invalid",
         "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """A synthetic repo: seed commit, then the audited ANCHOR commit."""
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "-c", "init.defaultBranch=main", "init", "-q")
    _commit(r, "README.md", "seed\n", "seed")
    return r


@pytest.fixture
def anchor(repo):
    """The audited terminal anchor: the last code/evidence commit."""
    return _commit(repo, "research/impl.py", "VERSION = 1\n", "audited anchor")


@pytest.fixture
def make_anchor(repo):
    """Anchor factory: seeds files that must exist AT the anchor commit
    (historical event logs, journals), then takes the audited anchor."""
    def _make(*seed):
        for rel, content in seed:
            _commit(repo, rel, content, "pre-anchor seed")
        return _commit(repo, "research/impl.py", "VERSION = 1\n",
                       "audited anchor")
    return _make


def _row(anchor_sha, **over):
    row = {
        "cycle_id": CYCLE_ID,
        "lifecycle": "TERMINAL",
        "head": anchor_sha,
        "head_semantics": ti.HEAD_SEMANTICS,
        "terminal_anchor_sha": anchor_sha,
        "post_terminal_policy": ti.POST_TERMINAL_POLICY,
    }
    row.update(over)
    return row


def _validate(repo, row, branch_tip, **kw):
    kw.setdefault("cycle_id", row.get("cycle_id", CYCLE_ID))
    return ti.validate_terminal_identity(row, branch_tip, repo, **kw)


def _kinds(result):
    return [f["kind"] for f in result["findings"]]


# ------------------------------------------------- the mandatory PASS matrix

def test_active_row_head_equals_tip_is_pass_context(repo, anchor):
    """Active-style rows are informational: identity semantics don't apply,
    zero findings, live tip still surfaced."""
    tip = _commit(repo, "research/impl.py", "VERSION = 2\n", "active work")
    result = _validate(repo, {"cycle_id": CYCLE_ID, "lifecycle": "ACTIVE_LIGHT",
                              "head": tip}, tip)
    assert result["findings"] == []
    assert result["branch_tip"] == tip
    assert result["terminal_anchor_sha"] is None
    assert result["descendant_commits"] == []


def test_terminal_anchor_equals_tip_passes_with_zero_findings(repo, anchor):
    result = _validate(repo, _row(anchor), anchor)
    assert result == {"findings": [], "branch_tip": anchor,
                      "terminal_anchor_sha": anchor,
                      "descendant_commits": [],
                      "foreign_scope_paths": []}


def test_anchor_ancestor_plus_allowed_addendum_commit_passes(repo, anchor):
    tip = _commit(repo, f"{CYCLE_CONTROL}/terminal_addendum.json",
                  '{"schema": "mdp_terminal_addendum@1"}\n', "evidence only")
    result = _validate(repo, _row(anchor), tip)
    assert result["findings"] == []
    assert result["descendant_commits"] == [tip]
    assert result["branch_tip"] == tip


def test_anchor_ancestor_plus_registry_journal_commit_passes(repo, anchor):
    """Canonical registry surfaces are allowlisted (approved writer output)."""
    tip = anchor
    for rel, body in (
            ("plans/CYCLE_REGISTRY.json", '{"schema": "cycle_registry@1"}\n'),
            (JOURNAL, '{"event": "REGISTRY_SAVED"}\n'),
            ("plans/ACTIVE_CYCLES.json", '{"schema": "active_cycles_projection@1"}\n')):
        tip = _commit(repo, rel, body, "registry writer output")
    result = _validate(repo, _row(anchor), tip)
    assert result["findings"] == []
    assert result["foreign_scope_paths"] == []
    assert len(result["descendant_commits"]) == 3
    assert result["descendant_commits"][-1] == tip


def test_real_world_v2_shape_registry_plus_appended_cycle_event_log_passes(
        repo, make_anchor):
    """The actual MARKET-DATA-PLANE-V2 shape: the cycle event log exists at
    the anchor and descendants APPEND to it and touch ONLY the registry
    surfaces — zero findings, and no repin commit is needed."""
    log = f"{CYCLE_CONTROL}/event_log.jsonl"
    anchor = make_anchor((log, '{"event": "P9_TERMINAL"}\n'))
    tip = _commit(repo, log,
                  '{"event": "P9_TERMINAL"}\n{"event": "P10_HEAD_REPIN"}\n',
                  "append evidence")
    tip = _commit(repo, "plans/CYCLE_REGISTRY.json",
                  '{"rows": 1}\n', "registry writer output")
    result = _validate(repo, _row(anchor), tip)
    assert result["findings"] == []
    assert len(result["descendant_commits"]) == 2


def test_audit_surface_descendant_passes(repo, anchor):
    """The audits tree carries NO _run suffix: research/audits/test_cycle_v1/
    is the row's own audit evidence (own-scope, allowlisted)."""
    tip = _commit(repo, f"{CYCLE_AUDITS}/a7_verdict.json",
                  '{"high": 0}\n', "audit artifact")
    result = _validate(repo, _row(anchor), tip)
    assert result["findings"] == []
    assert result["foreign_scope_paths"] == []


# ------------------------------------------------------- scoped path semantics

@pytest.mark.parametrize("relpath", [
    "research/wayfinder/HYPOTHESIS_LEDGER.md",
    "research/wayfinder/SURVIVORS.md",
])
def test_protected_global_paths_fail_high_for_any_row(repo, anchor, relpath):
    """PROTECTED-GLOBAL: the hypothesis ledger and the survivor denominator
    can never be touched after ANY terminal anchor — HIGH regardless of any
    allowlist override."""
    tip = _commit(repo, relpath, "tamper\n", "post-terminal ledger edit")
    for allowlist_override in (None, ["**"]):
        result = _validate(repo, _row(anchor), tip,
                           allowlist=allowlist_override)
        assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH"], \
            allowlist_override
        finding = result["findings"][0]
        assert finding["severity"] == "HIGH"
        assert relpath in finding["detail"]


def test_protected_global_touch_covered_by_successor_anchor_is_informational(
        repo):
    """SUCCESSOR-ANCHOR RULE (plan §12.2): a ledger touch already covered by
    a SUCCESSOR's declared terminal anchor is the successor row's business —
    informational (listed) for the old row, still a HIGH for uncovered
    tampering at every row, and the guard fails closed (no exemption) when
    the canonical registry is unreadable."""
    ledger = "research/wayfinder/HYPOTHESIS_LEDGER.md"
    _commit(repo, ledger, "row: v0\n", "pre-anchor ledger seed")
    anchor_old = _commit(repo, "research/impl.py", "VERSION = 1\n",
                         "old audited anchor")
    touch = _commit(repo, ledger, "row: v0\nrow: v1\n",
                    "successor-cycle close-sync")
    anchor_new = _commit(repo, "research/impl2.py", "VERSION = 2\n",
                         "successor audited anchor")
    plans = repo / "plans"
    plans.mkdir(exist_ok=True)
    registry = {
        "schema": "cycle_registry@1",
        "cycles": [
            {"cycle_id": "OLD", "lifecycle": "TERMINAL",
             "head_semantics": ti.HEAD_SEMANTICS,
             "terminal_anchor_sha": anchor_old},
            {"cycle_id": "NEW", "lifecycle": "TERMINAL",
             "head_semantics": ti.HEAD_SEMANTICS,
             "terminal_anchor_sha": anchor_new},
        ],
    }
    (plans / "CYCLE_REGISTRY.json").write_text(json.dumps(registry))
    # the old row's range contains the ledger touch, but it is covered by
    # the successor anchor -> zero findings, listed informationally
    # (alongside the successor's own implementation, also foreign)
    result = _validate(repo, _row(anchor_old), anchor_new)
    assert result["findings"] == []
    assert result["foreign_scope_paths"] == sorted(
        ["research/impl2.py", ledger])
    # uncovered tampering above the frontier fires for EVERY row
    later = _commit(repo, ledger, "row: v0\nrow: v1\nrow: v2\n",
                    "uncovered tamper")
    for anchor in (anchor_old, anchor_new):
        result = _validate(repo, _row(anchor), later)
        assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH"], anchor
        assert result["findings"][0]["severity"] == "HIGH"
    # fail closed: an unreadable registry means NO exemptions at all
    (plans / "CYCLE_REGISTRY.json").write_text("{oops")
    result = _validate(repo, _row(anchor_old), anchor_new)
    assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH"]


def test_own_scope_violation_still_fires_high(repo, anchor):
    """OWN-SCOPE paths (the row's own control/audit dirs + registry surfaces)
    MUST match the allowlist: with the default allowlist evidence-only
    additions pass, but with an allowlist that does not sanction the path the
    HIGH fires exactly as before (here: an implementation-looking file under
    the row's own control and audit scope, plus a tampered registry
    surface)."""
    impl = _commit(repo, f"{CYCLE_CONTROL}/impl.py", "VERSION = 2\n",
                   "own-scope implementation-looking change")
    restricted = [f"{CYCLE_CONTROL}/event_log.jsonl"]
    result = _validate(repo, _row(anchor), impl, allowlist=restricted)
    assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH"]
    assert result["findings"][0]["severity"] == "HIGH"
    assert f"{CYCLE_CONTROL}/impl.py" in result["findings"][0]["detail"]

    audit_impl = _commit(repo, f"{CYCLE_AUDITS}/impl.py", "VERSION = 2\n",
                         "own-scope audit-dir change")
    result = _validate(repo, _row(anchor), audit_impl,
                       allowlist=[f"{CYCLE_CONTROL}/**"])
    assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH"]

    registry_tamper = _commit(repo, "plans/CYCLE_REGISTRY.json",
                              '{"schema": "cycle_registry@1", "tampered": 1}\n',
                              "registry surface tamper")
    result = _validate(repo, _row(anchor), registry_tamper,
                       allowlist=[f"{CYCLE_CONTROL}/**"])
    # the diff since the anchor spans all three own-scope changes; the
    # control-dir impl is sanctioned, the audit-dir impl and the tampered
    # registry surface are not
    assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH",
                              "TERMINAL_IDENTITY_FORBIDDEN_PATH"]
    details = "\n".join(f["detail"] for f in result["findings"])
    assert f"{CYCLE_AUDITS}/impl.py" in details
    assert "plans/CYCLE_REGISTRY.json" in details
    # ...while the DEFAULT allowlist sanctions plain own-scope evidence
    assert _validate(repo, _row(anchor), impl)["findings"] == []


def test_foreign_scope_descendant_paths_are_not_findings_for_this_row(
        repo, anchor):
    """FOREIGN-SCOPE (the real-lineage shape): other cycles' code/tests/
    plans and shared implementation above an OLD anchor are the successor's
    own row+anchor business (plan §12.2, forward-only migration) — ZERO
    findings for this row, but the paths are listed in foreign_scope_paths
    for operator visibility."""
    foreign = [
        "research/governance/terminal_identity.py",      # implementation
        "tests/test_terminal_identity.py",               # tests
        "tests/fixtures/bars.parquet",                   # fixtures
        "plans/foo.md",                                  # non-registry plan
        "research/control/other_cycle_v2_run/state.json",   # another cycle
        "research/audits/other_cycle_v2_run/verdict.json",  # another cycle
        "results/survivors.csv",                         # research results
    ]
    tip = anchor
    for rel in foreign:
        tip = _commit(repo, rel, "successor work\n", "foreign-scope change")
    result = _validate(repo, _row(anchor), tip)
    assert result["findings"] == []
    assert result["foreign_scope_paths"] == sorted(foreign)
    assert len(result["descendant_commits"]) == len(foreign)
    assert result["branch_tip"] == tip


def test_foreign_scope_paths_empty_for_own_scope_only_changes(repo, anchor):
    tip = _commit(repo, f"{CYCLE_CONTROL}/terminal_addendum.json", "{}\n",
                  "evidence only")
    assert _validate(repo, _row(anchor), tip)["foreign_scope_paths"] == []


def test_default_allowlist_freeze():
    """The frozen §12.2 default: cycle evidence + audits + registry surfaces
    ONLY — never code/tests/plans-docs/ledgers/results. Convention (A4-r2):
    the control tree carries the _run suffix, the audits tree does NOT."""
    allowed = ti.default_allowlist(CYCLE_DIR)
    assert set(allowed) == {
        f"research/control/{CYCLE_DIR}/**",
        f"research/audits/{CYCLE_AUDIT_DIR}/**",
        "plans/CYCLE_REGISTRY.json",
        "plans/CYCLE_REGISTRY.events.jsonl",
        "plans/ACTIVE_CYCLES.json",
    }
    assert not any(p.endswith(".py") or p.endswith(".md")
                   for p in allowed if not p.startswith("research/"))
    # explicit audit_dir wins; single-arg call falls back to dropping _run
    assert ti.default_allowlist("market_data_plane_v2r1_run") == \
        ti.default_allowlist("market_data_plane_v2r1_run",
                             audit_dir="market_data_plane_v2r1")
    assert f"research/audits/market_data_plane_v2r1/**" in \
        ti.default_allowlist("market_data_plane_v2r1_run")
    assert ti.default_allowlist("x", audit_dir="y") == (
        "research/control/x/**", "research/audits/y/**") + \
        ti.REGISTRY_SURFACE_PATHS


def test_dir_derivations_are_two_distinct_conventions():
    """derive_cycle_dir keeps the frozen _run control convention; the new
    derive_audit_dir matches the audits tree WITHOUT the suffix."""
    assert ti.derive_cycle_dir("MARKET-DATA-PLANE-V2R1") == \
        "market_data_plane_v2r1_run"
    assert ti.derive_audit_dir("MARKET-DATA-PLANE-V2R1") == \
        "market_data_plane_v2r1"
    assert ti.derive_audit_dir("MARKET-DATA-PLANE-V2") == \
        "market_data_plane_v2"


def test_explicit_allowlist_override_param(repo, anchor):
    """An explicit allowlist param replaces the default entirely: the same
    own-scope evidence path that the default sanctions fails once the
    allowlist is replaced — and the override is not sticky."""
    tip = _commit(repo, f"{CYCLE_CONTROL}/addendum.json", "{}\n", "evidence")
    assert _validate(repo, _row(anchor), tip)["findings"] == []
    result = _validate(repo, _row(anchor), tip,
                       allowlist=["research/other_run/**"])
    assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH"]
    # ...and the override is not sticky: a fresh default run passes again
    assert _validate(repo, _row(anchor), tip)["findings"] == []


def test_cycle_dir_override_param(repo, anchor):
    """cycle_dir explicitly overrides the derived <cycle_id>_run scope: the
    overridden dir becomes the row's OWN scope, while without the override
    the same path is FOREIGN scope (listed, not a finding)."""
    tip = _commit(repo, f"{CYCLE_CONTROL}/impl.py", "tamper\n",
                  "own-scope impl under the overridden dir")
    restricted = [f"{CYCLE_CONTROL}/event_log.jsonl"]
    # override: the row's scope IS test_cycle_v1_run -> own-scope -> HIGH
    result = ti.validate_terminal_identity(
        _row(anchor), tip, repo, cycle_id="TOTALLY-OTHER-CYCLE",
        cycle_dir=CYCLE_DIR, allowlist=restricted)
    assert _kinds(result) == ["TERMINAL_IDENTITY_FORBIDDEN_PATH"]
    # without the override the derived dirs (totally_other_cycle_run /
    # totally_other_cycle) do not cover the path -> foreign scope
    result = ti.validate_terminal_identity(
        _row(anchor), tip, repo, cycle_id="TOTALLY-OTHER-CYCLE",
        allowlist=restricted)
    assert result["findings"] == []
    assert result["foreign_scope_paths"] == [f"{CYCLE_CONTROL}/impl.py"]


def test_audit_dir_override_param(repo, anchor):
    """audit_dir explicitly overrides the derived (no-_run) audits scope:
    the overridden dir becomes own-scope evidence, the derived dir's files
    become foreign-scope (listed only)."""
    tip = _commit(repo, f"{CYCLE_AUDITS}/a7_verdict.json", '{"high": 0}\n',
                  "audit artifact")
    result = ti.validate_terminal_identity(
        _row(anchor), tip, repo, cycle_id=CYCLE_ID, audit_dir="custom_audit")
    assert result["findings"] == []
    assert result["foreign_scope_paths"] == [f"{CYCLE_AUDITS}/a7_verdict.json"]
    # default derivation: the file is own-scope, not foreign
    result = _validate(repo, _row(anchor), tip)
    assert result["findings"] == []
    assert result["foreign_scope_paths"] == []


# ---------------------------------------------------- FAIL: event log history

def _rewrite_log(repo, log, content):
    """One descendant commit rewriting an already-committed file; returns tip."""
    path = Path(repo) / log
    path.write_text(content)
    _git(repo, "add", log)
    _git(repo, "-c", "user.name=A4 Test", "-c", "user.email=a4@t.invalid",
         "commit", "-q", "-m", "log change")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_event_log_pure_append_passes(repo, make_anchor):
    log = f"{CYCLE_CONTROL}/event_log.jsonl"
    anchor = make_anchor((log, '{"event": "P9_TERMINAL"}\n'))
    tip = _commit(repo, log, '{"event": "P9_TERMINAL"}\n'
                             '{"event": "P10_CLOSE"}\n', "append only")
    result = _validate(repo, _row(anchor), tip)
    assert result["findings"] == []
    assert result["descendant_commits"] == [tip]


def test_event_log_line_deletion_fails(repo, make_anchor):
    log = f"{CYCLE_CONTROL}/event_log.jsonl"
    anchor = make_anchor(
        (log, '{"event": "P9_TERMINAL"}\n{"event": "P10_CLOSE"}\n'))
    tip = _rewrite_log(repo, log, '{"event": "P10_CLOSE"}\n'
                                  '{"event": "P11_LATE"}\n')
    result = _validate(repo, _row(anchor), tip)
    assert _kinds(result) == ["TERMINAL_IDENTITY_EVENT_LOG_REWRITTEN"]
    assert result["findings"][0]["severity"] == "HIGH"


def test_event_log_reordering_fails(repo, make_anchor):
    log = f"{CYCLE_CONTROL}/event_log.jsonl"
    anchor = make_anchor((log, '{"event": "A"}\n{"event": "B"}\n'))
    tip = _rewrite_log(repo, log, '{"event": "B"}\n{"event": "A"}\n')
    result = _validate(repo, _row(anchor), tip)
    assert _kinds(result) == ["TERMINAL_IDENTITY_EVENT_LOG_REWRITTEN"]


def test_event_log_created_after_anchor_is_new_evidence_not_rewrite(
        repo, anchor):
    """No historical version at the anchor -> nothing can be rewritten: a NEW
    event log (or a new file generally) inside the cycle dir is post-terminal
    evidence, allowed by the policy."""
    log = f"{CYCLE_CONTROL}/event_log.jsonl"
    tip = _commit(repo, log, '{"event": "POST_TERMINAL_ONLY"}\n', "new log")
    assert _validate(repo, _row(anchor), tip)["findings"] == []


def test_registry_journal_history_rewrite_fails(repo, make_anchor):
    """The canonical journal is append-only even though the path is
    allowlisted: rewriting its history lines fails."""
    anchor = make_anchor((JOURNAL, '{"event": "FIRST"}\n'))
    tip = _rewrite_log(repo, JOURNAL, '{"event": "SECOND"}\n')
    result = _validate(repo, _row(anchor), tip)
    assert _kinds(result) == ["TERMINAL_IDENTITY_EVENT_LOG_REWRITTEN"]


def test_event_log_relpath_outside_cycle_dir_checked(repo, make_anchor):
    """event_log_relpath names an event log outside the cycle dir: allowed by
    an explicit allowlist, but still append-only checked."""
    rel = "research/other_run/event_log.jsonl"
    anchor = make_anchor((rel, '{"event": "A"}\n'))
    tip = _rewrite_log(repo, rel, '{"event": "B"}\n')
    result = _validate(repo, _row(anchor), tip,
                       allowlist=["research/other_run/**"],
                       event_log_relpath=rel)
    assert _kinds(result) == ["TERMINAL_IDENTITY_EVENT_LOG_REWRITTEN"]


# ----------------------------------------------- FAIL: ancestry / sha grammar

def test_non_ancestor_anchor_fails(repo, anchor):
    _git(repo, "checkout", "-q", "--orphan", "stray")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=A4 Test", "-c", "user.email=a4@t.invalid",
         "commit", "-q", "-m", "orphan root")
    stray = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "checkout", "-q", "main")
    tip = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert stray != tip
    result = _validate(repo, _row(stray), tip)
    assert _kinds(result) == ["TERMINAL_IDENTITY_NOT_ANCESTOR"]
    assert result["findings"][0]["severity"] == "HIGH"


def test_nonexistent_anchor_fails(repo, anchor):
    tip = anchor
    result = _validate(repo, _row("f" * 40), tip)
    assert _kinds(result) == ["TERMINAL_IDENTITY_ANCHOR_MISSING"]


@pytest.mark.parametrize("bad", ["41bf9b1", "NOPE", "F" * 40, ""])
def test_malformed_anchor_sha_fails(repo, anchor, bad):
    result = _validate(repo, _row(anchor, terminal_anchor_sha=bad), anchor)
    assert "TERMINAL_IDENTITY_MALFORMED_SHA" in _kinds(result)
    assert all(f["severity"] == "HIGH" for f in result["findings"])


def test_missing_terminal_anchor_sha_fails(repo, anchor):
    row = _row(anchor)
    del row["terminal_anchor_sha"]
    result = _validate(repo, row, anchor)
    assert "TERMINAL_IDENTITY_MALFORMED_SHA" in _kinds(result)
    # with no usable anchor the ancestry/diff checks are not reachable,
    # but the failure is still a HIGH finding (fail closed, not a pass)
    assert all(f["severity"] == "HIGH" for f in result["findings"])


def test_malformed_branch_tip_fails(repo, anchor):
    result = _validate(repo, _row(anchor), "not-a-sha")
    assert _kinds(result) == ["TERMINAL_IDENTITY_BRANCH_MISSING"]
    result = _validate(repo, _row(anchor), "ABC" + "0" * 37)
    assert _kinds(result) == ["TERMINAL_IDENTITY_BRANCH_MISSING"]


def test_missing_branch_unresolvable_repo_fails(tmp_path, anchor):
    bare = tmp_path / "not_a_repo"
    bare.mkdir()
    result = _validate(bare, _row(anchor), None)
    assert _kinds(result) == ["TERMINAL_IDENTITY_BRANCH_MISSING"]


def test_live_tip_resolved_when_branch_tip_omitted(repo, anchor):
    """branch_tip=None on a real repo resolves HEAD live (rule 10)."""
    result = _validate(repo, _row(anchor), None)
    assert result["findings"] == []
    assert result["branch_tip"] == anchor


# ------------------------------------------------------- FAIL: row malformed

def test_row_head_mismatch_anchor_fails(repo, anchor):
    row = _row(anchor, head="b" * 40)
    result = _validate(repo, row, anchor)
    assert _kinds(result) == ["TERMINAL_IDENTITY_ROW_MALFORMED"]
    assert anchor in result["findings"][0]["detail"]
    assert "b" * 40 in result["findings"][0]["detail"]


def test_unknown_head_semantics_fails(repo, anchor):
    result = _validate(repo, _row(anchor, head_semantics="LIVE_TIP"), anchor)
    assert "TERMINAL_IDENTITY_ROW_MALFORMED" in _kinds(result)


def test_missing_post_terminal_policy_fails(repo, anchor):
    row = _row(anchor)
    del row["post_terminal_policy"]
    assert "TERMINAL_IDENTITY_ROW_MALFORMED" in \
        _kinds(_validate(repo, row, anchor))


def test_unknown_post_terminal_policy_fails(repo, anchor):
    result = _validate(repo, _row(anchor, post_terminal_policy="ANYTHING"), anchor)
    assert "TERMINAL_IDENTITY_ROW_MALFORMED" in _kinds(result)


def test_declared_identity_on_non_terminal_row_fails(repo, anchor):
    row = _row(anchor, lifecycle="ACTIVE_LIGHT")
    assert "TERMINAL_IDENTITY_ROW_MALFORMED" in \
        _kinds(_validate(repo, row, anchor))


# ------------------------------------------------- legacy row / compatibility

def test_undeclared_legacy_terminal_row_gets_visible_medium_finding(repo, anchor):
    """Legacy TERMINAL rows stay readable but are NEVER silently normalized:
    the MEDIUM TERMINAL_IDENTITY_UNDECLARED compatibility finding is visible
    and the live tip is still surfaced."""
    legacy = {"cycle_id": CYCLE_ID, "lifecycle": "TERMINAL", "head": anchor}
    result = _validate(repo, legacy, anchor)
    assert [(f["kind"], f["severity"]) for f in result["findings"]] == \
        [("TERMINAL_IDENTITY_UNDECLARED", "MEDIUM")]
    assert "declare_terminal_identity" in result["findings"][0]["detail"]
    assert result["branch_tip"] == anchor
    assert result["terminal_anchor_sha"] is None


def test_terminal_report_head_crosscheck(repo, anchor):
    ok = _validate(repo, _row(anchor), anchor,
                   terminal_report_head=anchor)
    assert ok["findings"] == []
    bad = _validate(repo, _row(anchor), anchor,
                    terminal_report_head="c" * 40)
    assert _kinds(bad) == ["TERMINAL_IDENTITY_REPORT_MISMATCH"]
    assert bad["findings"][0]["severity"] == "HIGH"


# ------------------------------------------------------- idempotence / shape

def test_repeated_validation_at_same_tip_needs_no_repin(repo, anchor):
    """Idempotence: two runs at the same tip give identical zero-finding
    results; the tip sha is unchanged (no new repin commit was created) and
    the worktree is untouched (read-only validator)."""
    tip = _commit(repo, f"{CYCLE_CONTROL}/addendum.json", "{}\n", "evidence")
    first = _validate(repo, _row(anchor), tip)
    second = _validate(repo, _row(anchor), tip)
    assert first == second
    assert first["findings"] == []
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == tip
    assert _git(repo, "status", "--porcelain=v1").stdout.strip() == ""
    # and one MORE run after the tip moved again — still zero findings,
    # still the same anchor (the whole point of TERMINAL_ANCHOR semantics)
    tip2 = _commit(repo, f"{CYCLE_CONTROL}/addendum2.json", "{}\n", "more evidence")
    again = _validate(repo, _row(anchor), tip2)
    assert again["findings"] == []
    assert again["descendant_commits"] == [tip, tip2]


def test_live_branch_tip_surfaced_in_every_result(repo, anchor):
    tip = _commit(repo, "research/tamper.py", "x\n", "forbidden")
    for row in (_row(anchor), _row(anchor, head="b" * 40),
                {"cycle_id": CYCLE_ID, "lifecycle": "TERMINAL", "head": anchor},
                {"cycle_id": CYCLE_ID, "lifecycle": "ACTIVE_LIGHT",
                 "head": tip}):
        result = _validate(repo, row, tip)
        assert result["branch_tip"] == tip, row


def test_result_shape_is_frozen(repo, anchor):
    result = _validate(repo, _row(anchor), anchor)
    assert set(result) == {"findings", "branch_tip", "terminal_anchor_sha",
                           "descendant_commits", "foreign_scope_paths"}
    assert result["foreign_scope_paths"] == []
    for f in result["findings"]:
        assert set(f) == {"kind", "severity", "detail"}


def test_missing_cycle_context_is_an_api_error(repo, anchor):
    with pytest.raises(ValueError):
        ti.validate_terminal_identity(_row(anchor), anchor, repo)


def test_selfcheck_cli_exits_zero():
    worktree = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "governance.terminal_identity", "--selfcheck"],
        cwd=str(worktree / "research"), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "selfcheck OK" in proc.stdout
