"""COMMODITIES-NG1 D1 gate tests (task commodities-ng1-d1-proposals).

Laws under test
---------------
1. Frozen template fields: every D1 proposal carries proposal_id/lane/title,
   a mechanism with a FORCED participant, a decision_rule_family (parameters
   symbolic until D2/S), a representation_identity (P-12) citing committed
   P0/P1/P2 artifacts by sha256, an ancestry_risk_statement naming the three
   kill-candidate shadows, a control_battery_spec with the MANDATORY
   price-only shadow + release-clock shadow + shifted-release placebo, a
   feasibility_citation (P2 per-pair census; transaction-only legs excluded),
   and one preregistered falsification_rule.
2. Blindness law (absolute): NO outcome numbers anywhere. The negative scan
   asserts (a) zero outcome-metric vocabulary outside negated contexts and
   (b) zero numeric leaves outside the declared citation containers.
   The scanner is itself tested against synthetic violating fixtures.
3. Structural integrity: every (path, sha256) citation pair inside a proposal
   resolves to a real committed artifact whose on-disk sha256 matches.
4. d1_gate.json: per-proposal completeness verdicts + negative-scan verdict,
   consistent with the artifacts on disk.

NO outcome measurement exists in D1; a correct REJECT_ALL at D2 is a
successful run. This test file computes no returns and conditions nothing.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
RUN_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run"
D1_DIR = RUN_DIR / "d1"
PROPOSALS_DIR = D1_DIR / "proposals"
GATE_PATH = D1_DIR / "d1_gate.json"

CYCLE_ID = "COMMODITIES-NG1"
TASK_ID = "commodities-ng1-d1-proposals"
SCHEMA_PROPOSAL = "commodities_ng1_run/d1_proposal@1"
SCHEMA_GATE = "commodities_ng1_run/d1_gate@1"
BASE_SHA = "853f4fe4a5496034efa1367e0be4efd875b629ac"

EXPECTED_IDS = {
    "COMMNG1-A4-P1": "A4",
    "COMMNG1-A4-P2": "A4",
    "COMMNG1-A5-P1": "A5",
    "COMMNG1-A5-P2": "A5",
}

REQUIRED_FIELDS = (
    "schema", "cycle_id", "task_id", "proposal_id", "lane", "title",
    "authored_utc", "base_sha", "blindness_declaration", "mechanism",
    "decision_rule_family", "representation_identity",
    "ancestry_risk_statement", "control_battery_spec",
    "feasibility_citation", "falsification_rule",
)

REQUIRED_SHADOWS = {"momentum_63s", "generic_dow_tue", "v16_close_displace_fade"}
KILLER_ROLES = {"PRICE_ONLY_SHADOW", "RELEASE_CLOCK_SHADOW", "SHIFTED_RELEASE_PLACEBO"}
MANDATORY_ARM_ROLES = {"ANCHOR"} | KILLER_ROLES

P2_GATE_SHA = "ee32c9df86c3f33126d3899fad62f74cb880f654970791cf260e59e4652b973c"
P1_COST_SHA = "5929ed4300246d0dad4335995d39415454313dd5ef47edf5380fb529fa154631"

# P2 item3: transaction-only fail-closed legs (expense NOT_MEASURED).
EXPECTED_TX_ONLY_LEGS = {"BAR", "CPER", "PALL", "PPLT", "SGOL", "SIVR", "UNG", "USL", "USO"}
EXPECTED_EXCLUDED_PAIRS = {
    "023651/UNG", "067651/USL", "067651/USO", "075651/PALL", "076651/PPLT",
    "084691/SIVR", "085692/CPER", "088691/BAR", "088691/SGOL",
}
EXPECTED_BOOKABLE_PAIRS = {
    "001602/DBA", "001602/WEAT", "002602/CORN", "002602/DBA", "005602/DBA",
    "005602/SOYB", "067651/DBO", "080732/CANE", "084691/SLV", "088691/GLD",
    "088691/IAU",
}

# Outcome-metric vocabulary. A match inside a NEGATED context is not an
# outcome claim ("no PnL", "no expectancies", "never a return") and is
# ignored by the negation guard below.
BANNED_TOKEN_PATTERNS = [
    r"\bsharpe\b",
    r"\bsortino\b",
    r"\bcalmar\b",
    r"\bpnl\b",
    r"\bprofit",
    r"\bexpectanc",
    r"\bhit[_ ]?rate\b",
    r"\bwin[_ ]?rate\b",
    r"\bdrawdown\b",
    r"\bcagr\b",
    r"\bt[_ ]?stat\b",
    r"\bp[_ ]?value\b",
    r"\balpha\b",
    r"\binformation[_ ]?ratio\b",
    r"\b(expected|mean|total|annualized|cum)[_ ]?returns?\b",
    r"\bedge[_ ]?bps\b",
]
_NEGATION_GUARD = re.compile(
    r"(?:\bno\b|\bnot\b|\bnever\b|\bwithout\b|\bzero\b)[\s-]+(?:[\w.,-]+\s+){0,2}$",
    re.IGNORECASE,
)

# Numeric leaves are allowed ONLY inside these citation containers
# (structural census/cost facts committed upstream; never outcomes).
NUMERIC_ALLOWED_ROOTS = (
    "feasibility_citation",
    "representation_identity.grid.census_facts",
    "representation_identity.series.cot_series.census_facts",
)

# (key_a, key_b) pairs inside one dict where key_b must be the sha256 of the
# file at relative path key_a.
CITATION_PAIR_KEYS = (
    ("path", "sha256"),
    ("source", "source_sha256"),
    ("census", "census_sha256"),
    ("code", "code_sha256"),
    ("clock_code", "clock_code_sha256"),
    ("raw_manifest", "raw_manifest_sha256"),
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_leaves(obj, path=""):
    """Yield (json_path, value) for every scalar leaf."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_leaves(v, f"{path}[{i}]")
    else:
        yield path, obj


def _iter_strings(obj, path=""):
    for p, v in _iter_leaves(obj, path):
        if isinstance(v, str):
            yield p, v


def _is_allowed_numeric_root(path: str) -> bool:
    return any(
        path == root or path.startswith(root + ".") or path.startswith(root + "[")
        for root in NUMERIC_ALLOWED_ROOTS
    )


def scan_outcome_tokens(obj) -> list[str]:
    """Return banned-token hits NOT inside a negated context."""
    hits = []
    for _path, text in _iter_strings(obj):
        low = text.lower()
        for pat in BANNED_TOKEN_PATTERNS:
            for m in re.finditer(pat, low):
                prefix = low[max(0, m.start() - 40):m.start()]
                if _NEGATION_GUARD.search(prefix):
                    continue
                hits.append(f"{pat} :: ...{text[max(0, m.start() - 30):m.end() + 30]}...")
    return hits


def scan_numeric_leaves(obj) -> list[str]:
    """Return numeric leaves outside the declared citation containers."""
    bad = []
    for path, value in _iter_leaves(obj):
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and not _is_allowed_numeric_root(path):
            bad.append(f"{path} = {value!r}")
    return bad


def citation_problems(obj) -> list[str]:
    """Every (path/census/code/..., *_sha256) pair must resolve on disk."""
    problems = []

    def walk(node):
        if isinstance(node, dict):
            for key_a, key_b in CITATION_PAIR_KEYS:
                if key_a in node and key_b in node:
                    ref, dig = node[key_a], node[key_b]
                    if isinstance(ref, str) and ref.startswith("research/"):
                        f = WORKTREE / ref
                        if not f.exists():
                            problems.append(f"missing cited artifact: {ref}")
                        elif not (isinstance(dig, str) and re.fullmatch(r"[0-9a-f]{64}", dig)):
                            problems.append(f"malformed sha256 for {ref}")
                        elif _sha256_file(f) != dig:
                            problems.append(f"sha256 mismatch for {ref}")
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(obj)
    return problems


def completeness_problems(p: dict) -> list[str]:
    """Frozen template-field completeness for ONE proposal (D1 packet)."""
    probs = []
    add = probs.append

    for field in REQUIRED_FIELDS:
        if field not in p or not p[field]:
            add(f"missing/empty required field: {field}")
    if probs:
        return probs

    if p["schema"] != SCHEMA_PROPOSAL:
        add(f"schema != {SCHEMA_PROPOSAL}")
    if p["cycle_id"] != CYCLE_ID:
        add("cycle_id mismatch")
    if p["task_id"] != TASK_ID:
        add("task_id mismatch")
    if EXPECTED_IDS.get(p["proposal_id"]) != p["lane"]:
        add(f"proposal_id/lane mismatch: {p['proposal_id']} / {p['lane']}")
    if p["base_sha"] != BASE_SHA:
        add("base_sha != frozen dispatch BASE")

    blind = p["blindness_declaration"]
    if blind.get("status") != "OUTCOME_BLIND":
        add("blindness_declaration.status != OUTCOME_BLIND")
    if "no outcome numbers" not in blind.get("law", "").lower():
        add("blindness law does not declare the no-outcome-numbers rule")

    mech = p["mechanism"]
    if not isinstance(mech, dict) or len(mech.get("narrative", "")) < 200:
        add("mechanism narrative missing/too short")
    forced = mech.get("forced_participant") or {}
    late = mech.get("late_participant") or {}
    if not (forced.get("who") and forced.get("why_forced")) and not late:
        add("mechanism identifies neither a FORCED nor a LATE participant")
    if "symbolic" not in mech.get("state_definition_symbolic", "").lower():
        add("state_definition_symbolic missing")

    fam = p["decision_rule_family"]
    if "symbolic" not in fam.lower() or "frozen at d2/s" not in fam.lower():
        add("decision_rule_family must keep parameters symbolic until D2/S")

    ri = p["representation_identity"]
    for key in ("grid", "series", "decision_instant_law", "q16_instrument_declaration"):
        if key not in ri:
            add(f"representation_identity.{key} missing")
    grid = ri.get("grid", {})
    cf = grid.get("census_facts", {})
    if cf.get("source_sha256") != P2_GATE_SHA:
        add("grid census does not cite the P2 gate by sha256")
    if "15:30" not in grid.get("release_instant", ""):
        add("release clock (Friday 15:30 ET) not declared")
    if "strictly after" not in grid.get("decision_session", "").lower():
        add("strictly-after decision-session law not declared")
    if "v7 close+1" not in ri.get("decision_instant_law", {}).get("law", "").lower():
        add("V7 close+1 decision-instant law not declared")
    cot = ri.get("series", {}).get("cot_series", {})
    if "pit" not in cot.get("pit_guard", "").lower():
        add("CoT PIT guard not declared")
    etp = ri.get("series", {}).get("etp_legs", {})
    if "boundary" not in etp.get("split_boundary_law", "").lower():
        add("RAW-primary split-boundary law not declared")

    anc = p["ancestry_risk_statement"]
    shadows = {c.get("shadow") for c in anc.get("named_kill_candidates", [])}
    if shadows != REQUIRED_SHADOWS:
        add(f"ancestry shadows mismatch: {sorted(shadows)}")
    for c in anc.get("named_kill_candidates", []):
        if not c.get("why_different"):
            add(f"shadow without why_different: {c.get('shadow')}")

    bat = p["control_battery_spec"]
    arms = {a.get("role"): a for a in bat.get("arms", [])}
    if not MANDATORY_ARM_ROLES.issubset(arms):
        add(f"battery missing mandatory arms: {sorted(MANDATORY_ARM_ROLES - set(arms))}")
    law_l = bat.get("law", "").lower()
    if "q-11" not in law_l or "invalid" not in law_l:
        add("battery law lacks the Q-11 invalid-null distinction")
    for role in KILLER_ROLES:
        if "designated killer" not in arms.get(role, {}).get("kill_semantics", "").lower():
            add(f"{role} is not a designated killer")
    if "price-only" not in arms.get("PRICE_ONLY_SHADOW", {}).get("name", "").lower():
        add("PRICE_ONLY_SHADOW is not the mandatory price-only shadow")

    fe = p["feasibility_citation"]
    if not fe.get("floor_artifacts"):
        add("feasibility floor_artifacts missing")
    decl = fe.get("d1_bookable_set_declaration", {})
    if set(decl.get("excluded_transaction_only_legs", [])) != EXPECTED_TX_ONLY_LEGS:
        add("excluded transaction-only legs != the 9 P2 fail-closed legs")
    if set(decl.get("bookable_pairs", [])) != EXPECTED_BOOKABLE_PAIRS:
        add("bookable pair set mismatch")
    if set(decl.get("excluded_pairs", [])) != EXPECTED_EXCLUDED_PAIRS:
        add("excluded pair set mismatch")
    if not fe.get("cost_ceilings_cited"):
        add("cost ceilings not cited")

    fr = p["falsification_rule"]
    if not fr.get("statement", "").upper().startswith("KILL"):
        add("falsification_rule does not start with a concrete KILL condition")
    if "before any measurement" not in fr.get("declared_at", ""):
        add("falsification_rule not declared before any measurement")
    if set(fr.get("killer_controls", [])) != KILLER_ROLES:
        add("falsification killer_controls != the three designated killers")

    probs.extend(scan_outcome_tokens(p))
    probs.extend(scan_numeric_leaves(p))
    probs.extend(citation_problems(p))
    return probs


@pytest.fixture(scope="module")
def proposals() -> dict:
    out = {}
    for pid in EXPECTED_IDS:
        path = PROPOSALS_DIR / f"{pid}.json"
        out[pid] = json.loads(path.read_text())
    return out


# --------------------------------------------------------------------------
# 1. existence + frozen template fields
# --------------------------------------------------------------------------

def test_all_four_proposals_exist_and_parse():
    for pid in EXPECTED_IDS:
        path = PROPOSALS_DIR / f"{pid}.json"
        assert path.is_file(), f"missing proposal: {path}"
        obj = json.loads(path.read_text())
        assert obj["proposal_id"] == pid


def test_frozen_template_fields(proposals):
    for pid, p in proposals.items():
        assert p["schema"] == SCHEMA_PROPOSAL
        assert p["cycle_id"] == CYCLE_ID
        assert p["task_id"] == TASK_ID
        assert p["proposal_id"] == pid
        assert p["lane"] == EXPECTED_IDS[pid]
        assert p["base_sha"] == BASE_SHA
        assert isinstance(p["title"], str) and len(p["title"]) > 20
        assert set(p) >= set(REQUIRED_FIELDS)


def test_lane_coverage_two_per_lane(proposals):
    lanes = {}
    for pid, p in proposals.items():
        lanes.setdefault(p["lane"], []).append(pid)
    assert sorted(lanes) == ["A4", "A5"]
    assert all(len(v) == 2 for v in lanes.values())


def test_dispatch_base_is_ancestor_of_head():
    r = subprocess.run(
        ["git", "-C", str(WORKTREE), "merge-base", "--is-ancestor", BASE_SHA, "HEAD"],
        capture_output=True,
    )
    assert r.returncode == 0, "frozen dispatch BASE is not an ancestor of HEAD"


# --------------------------------------------------------------------------
# 2. mechanism, family, representation identity
# --------------------------------------------------------------------------

def test_mechanism_declares_forced_participant(proposals):
    for pid, p in proposals.items():
        forced = p["mechanism"]["forced_participant"]
        assert forced["who"] and forced["why_forced"], pid
        assert "symbolic" in p["mechanism"]["state_definition_symbolic"].lower()


def test_decision_rule_family_symbolic_until_d2s(proposals):
    for pid, p in proposals.items():
        fam = p["decision_rule_family"].lower()
        assert "symbolic" in fam and "frozen at d2/s" in fam, pid


def test_representation_identity_p12_citations(proposals):
    for pid, p in proposals.items():
        ri = p["representation_identity"]
        cf = ri["grid"]["census_facts"]
        assert cf["source_sha256"] == P2_GATE_SHA
        assert "15:30" in ri["grid"]["release_instant"]
        assert "strictly after" in ri["grid"]["decision_session"].lower()
        assert "v7 close+1" in ri["decision_instant_law"]["law"].lower()
        cot = ri["series"]["cot_series"]
        assert "pit" in cot["pit_guard"].lower()
        assert cot["census_sha256"] == (
            "4d7fabfc8106f283b4f67869657553daf5ba50e3e8f43c6ce9e473e33d81a0f1")
        etp = ri["series"]["etp_legs"]
        assert etp["census_sha256"] == (
            "8d9344ad36a39f9e6ef6e2e4a22a5cc896ad3b324e5c4594f68d71099afb9c1c")
        assert "boundary" in etp["split_boundary_law"].lower()
        q16law = ri["q16_instrument_declaration"]["law"].lower()
        assert "q16" in q16law.replace("-", "") or "q-16" in q16law


def test_cited_artifacts_match_on_disk(proposals):
    for pid, p in proposals.items():
        probs = citation_problems(p)
        assert not probs, f"{pid}: {probs}"


# --------------------------------------------------------------------------
# 3. ancestry, battery, feasibility, falsification
# --------------------------------------------------------------------------

def test_ancestry_names_all_three_kill_candidates(proposals):
    for pid, p in proposals.items():
        shadows = {c["shadow"] for c in p["ancestry_risk_statement"]["named_kill_candidates"]}
        assert shadows == REQUIRED_SHADOWS, pid


def test_control_battery_mandatory_arms(proposals):
    for pid, p in proposals.items():
        arms = {a["role"]: a for a in p["control_battery_spec"]["arms"]}
        assert MANDATORY_ARM_ROLES <= set(arms), pid
        assert "price-only" in arms["PRICE_ONLY_SHADOW"]["name"].lower()
        assert "q-11" in p["control_battery_spec"]["law"].lower()
        assert "never selectable" in arms["CLAIRVOYANT"]["kill_semantics"].lower()


def test_feasibility_citation_excludes_transaction_only_legs(proposals):
    for pid, p in proposals.items():
        decl = p["feasibility_citation"]["d1_bookable_set_declaration"]
        assert set(decl["excluded_transaction_only_legs"]) == EXPECTED_TX_ONLY_LEGS
        assert set(decl["bookable_pairs"]) == EXPECTED_BOOKABLE_PAIRS
        assert set(decl["excluded_pairs"]) == EXPECTED_EXCLUDED_PAIRS
        ceils = p["feasibility_citation"]["cost_ceilings_cited"]
        legs = {row["leg"] for row in ceils["per_leg_worst_case_round_trip_ceiling_bps"]}
        assert legs == {s.split("/")[1] for s in EXPECTED_BOOKABLE_PAIRS}


def test_falsification_rule_concrete(proposals):
    for pid, p in proposals.items():
        fr = p["falsification_rule"]
        assert fr["statement"].upper().startswith("KILL")
        assert set(fr["killer_controls"]) == KILLER_ROLES
        assert "before any measurement" in fr["declared_at"]


# --------------------------------------------------------------------------
# 4. blindness negative scan (committed artifacts + synthetic fixtures)
# --------------------------------------------------------------------------

def test_negative_scan_no_outcome_tokens(proposals):
    for pid, p in proposals.items():
        hits = scan_outcome_tokens(p)
        assert not hits, f"{pid} outcome-token hits: {hits}"


def test_negative_scan_no_numeric_leaves_outside_citations(proposals):
    for pid, p in proposals.items():
        bad = scan_numeric_leaves(p)
        assert not bad, f"{pid} numeric leaves outside citation roots: {bad}"


def test_negation_guard_lets_negated_contexts_pass():
    assert not scan_outcome_tokens({"a": "this gate contains no PnL and no expectancies"})
    assert not scan_outcome_tokens({"a": "declared with no returns conditional on states"})


def test_scanner_detects_violations_synthetic():
    malicious = {
        "a": "the anchor earns a sharpe of 1.44 with pnl +5 percent",
        "b": "expectancy per trade positive",
        "c": {"deep": {"x": 3.14}},
        "d": {"path": "research/control/commodities_ng1_run/p2_gate.json",
              "sha256": "0" * 64},
    }
    tok = scan_outcome_tokens(malicious)
    assert any("sharpe" in h for h in tok)
    assert any("pnl" in h for h in tok)
    assert any("expectanc" in h for h in tok)
    bad = scan_numeric_leaves(malicious)
    assert any("c.deep.x" in b for b in bad)
    probs = citation_problems(malicious)
    assert any("sha256 mismatch" in q for q in probs)


def test_completeness_checker_passes_synthetic_and_detects_removal():
    good = {
        "schema": SCHEMA_PROPOSAL,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "proposal_id": "COMMNG1-A4-P1",
        "lane": "A4",
        "title": "synthetic fixture title long enough for the checker",
        "authored_utc": "2026-09-12T00:00:00+00:00",
        "base_sha": BASE_SHA,
        "blindness_declaration": {
            "status": "OUTCOME_BLIND",
            "law": "contains no outcome numbers",
        },
        "mechanism": {
            "narrative": "x" * 250,
            "forced_participant": {"who": "hedger", "why_forced": "inventory"},
            "state_definition_symbolic": "window w is SYMBOLIC",
        },
        "decision_rule_family": "family with parameters symbolic, frozen at D2/S",
        "representation_identity": {
            "grid": {
                "release_instant": "Friday 15:30 America/New_York",
                "decision_session": "first session STRICTLY AFTER the release date",
                "census_facts": {"source_sha256": P2_GATE_SHA},
            },
            "series": {
                "cot_series": {
                    "pit_guard": "PIT guard refuses early reads",
                    "census_sha256": "4d7fabfc8106f283b4f67869657553daf5ba50e3e8f43c6ce9e473e33d81a0f1",
                },
                "etp_legs": {
                    "split_boundary_law": "share-base-boundary windows excluded",
                    "census_sha256": "8d9344ad36a39f9e6ef6e2e4a22a5cc896ad3b324e5c4594f68d71099afb9c1c",
                },
            },
            "decision_instant_law": {"law": "V7 close+1 readability law"},
            "q16_instrument_declaration": {"law": "Q16 drag is part of the mechanism"},
        },
        "ancestry_risk_statement": {
            "named_kill_candidates": [
                {"shadow": s, "why_different": "differs"} for s in sorted(REQUIRED_SHADOWS)
            ],
        },
        "control_battery_spec": {
            "law": "invalid vs null DISTINCTLY (Q-11) on every arm",
            "arms": [
                {"role": "ANCHOR", "name": "anchor"},
                {"role": "PRICE_ONLY_SHADOW", "name": "price-only shadow",
                 "kill_semantics": "DESIGNATED KILLER: out-earns the anchor"},
                {"role": "RELEASE_CLOCK_SHADOW", "name": "clock shadow",
                 "kill_semantics": "DESIGNATED KILLER: out-earns the anchor"},
                {"role": "SHIFTED_RELEASE_PLACEBO", "name": "placebo",
                 "kill_semantics": "DESIGNATED KILLER: out-earns the anchor"},
                {"role": "CLAIRVOYANT", "name": "ceiling",
                 "kill_semantics": "NEVER selectable at S"},
            ],
        },
        "feasibility_citation": {
            "floor_artifacts": [{"path": "research/control/commodities_ng1_run/p2_gate.json",
                                 "sha256": P2_GATE_SHA}],
            "d1_bookable_set_declaration": {
                "excluded_transaction_only_legs": sorted(EXPECTED_TX_ONLY_LEGS),
                "bookable_pairs": sorted(EXPECTED_BOOKABLE_PAIRS),
                "excluded_pairs": sorted(EXPECTED_EXCLUDED_PAIRS),
            },
            "cost_ceilings_cited": {"per_leg_worst_case_round_trip_ceiling_bps": []},
        },
        "falsification_rule": {
            "statement": "KILL if any designated killer out-earns the anchor",
            "declared_at": "D1, before any measurement",
            "killer_controls": sorted(KILLER_ROLES),
        },
    }
    assert completeness_problems(good) == []

    for removed in ("control_battery_spec", "falsification_rule", "mechanism"):
        broken = json.loads(json.dumps(good))
        del broken[removed]
        assert completeness_problems(broken), f"removal of {removed} not detected"

    broken = json.loads(json.dumps(good))
    broken["ancestry_risk_statement"]["named_kill_candidates"] = \
        broken["ancestry_risk_statement"]["named_kill_candidates"][:1]
    assert any("ancestry shadows mismatch" in q for q in completeness_problems(broken))

    broken = json.loads(json.dumps(good))
    broken["decision_rule_family"] = "thresholds are 0.5 and 2.0, fixed"
    assert any("symbolic" in q for q in completeness_problems(broken))


# --------------------------------------------------------------------------
# 5. d1_gate.json
# --------------------------------------------------------------------------

def test_d1_gate_consistent(proposals):
    assert GATE_PATH.is_file(), f"missing gate: {GATE_PATH}"
    gate = json.loads(GATE_PATH.read_text())
    assert gate["schema"] == SCHEMA_GATE
    assert gate["cycle_id"] == CYCLE_ID
    assert gate["task_id"] == TASK_ID
    assert gate["final_verdict"] == "PASS"
    assert gate["base_sha"] == BASE_SHA

    gate_props = gate["proposals"]
    assert set(gate_props) == set(EXPECTED_IDS)
    for pid, entry in gate_props.items():
        assert entry["verdict"] == "COMPLETE", pid
        assert entry["sha256"] == _sha256_file(PROPOSALS_DIR / f"{pid}.json"), pid
        assert all(entry["completeness"].values()), pid

    ns = gate["negative_scan"]
    assert ns["passed"] is True
    assert ns["banned_token_hits"] == []
    assert ns["numeric_leaf_violations"] == []
    assert ns["banned_token_patterns"] == BANNED_TOKEN_PATTERNS
    assert tuple(ns["numeric_leaf_allowlist_roots"]) == NUMERIC_ALLOWED_ROOTS
    assert set(ns["scan_scope"]) == {f"d1/proposals/{pid}.json" for pid in EXPECTED_IDS}

    # the gate's own prose is bound by the same token law (patterns excepted)
    prose = {k: v for k, v in gate.items() if k != "negative_scan"}
    assert not scan_outcome_tokens(prose)
    assert not scan_numeric_leaves(prose)


def test_test_command_recorded():
    gate = json.loads(GATE_PATH.read_text())
    assert "pytest tests/test_commodities_ng1_d1.py" in gate["test_command"]
    assert gate["test_command"].startswith("cd " + str(WORKTREE))
