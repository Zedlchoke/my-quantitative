"""RATES-NG1 D1 validator and gate builder (dispatch: rates-ng1-d1-proposals).

Outcome-blind proposal validation for the D1 phase:

1. FROZEN-FIELD COMPLETENESS: every proposal must carry the 8 frozen
   template fields from the dispatch packet (proposal_id / lane / title,
   mechanism, decision_rule_family, representation_identity,
   ancestry_risk_statement, control_battery_spec, feasibility_citation,
   falsification_rule) as non-empty values;
2. BLINDNESS NEGATIVE SCAN: NO outcome numbers may appear in any
   proposal file.  Enforced two ways:
   a. forbidden-token regexes over the raw file text (metric vocabulary
     such as expectancy/pnl/sharpe/hit-rate/win-rate/CAGR/drawdown/
     profit-factor/bare "return(s)"/alpha);
   b. a numeric-leaf allowlist: every numeric leaf in the parsed JSON
     must sit under an allowlisted KEY NAME (structural census counts,
     frozen cost-projection constants, frozen rubric constants).  Any
     numeric leaf under any other key name is a violation.
3. BATTERY COMPOSITION per lane (plan section 6):
   A4: ANCHOR + DELAY_PAIR + CLAIRVOYANT + CLOCK_ONLY_SHADOW
       + SHIFTED_CALENDAR_PLACEBO;
   A5: ANCHOR + LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL + CLOCK_ONLY_SHADOW
       + PLACEBO;
4. PIN VERIFICATION: every {"path": ..., "sha256": ...} object inside a
   proposal must match a re-hash of the named file on disk.

`build_gate` derives the committed d1_gate.json deterministically from
the committed proposal files; the tests re-derive and compare.  This
module computes no outcome statistic of any kind.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

WORKTREE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RUN_DIR = os.path.join(
    WORKTREE, "research", "control", "rates_ng1_run")
D1_DIR = os.path.join(RUN_DIR, "d1")
PROPOSALS_DIR = os.path.join(D1_DIR, "proposals")
GATE_PATH = os.path.join(D1_DIR, "d1_gate.json")

SCHEMA_PROPOSAL = "rates_ng1_run/d1_proposal@1"
SCHEMA_GATE = "rates_ng1_run/d1_gate@1"
GATE_SCHEMA_VERSION = 1

CYCLE_ID = "RATES-NG1"
TASK_ID = "rates-ng1-d1-proposals"
BASE_SHA = "59b8de30c435bb44e1a3d93c6b2cc41e04cb8217"

PROPOSAL_IDS = [
    "RATESNG1-A4-P1",
    "RATESNG1-A4-P2",
    "RATESNG1-A5-P1",
    "RATESNG1-A5-P2",
]

#: The 8 frozen template fields from the dispatch packet, mapped to the
#: concrete top-level keys each proposal must carry (field 1 expands to
#: three identity keys).
REQUIRED_KEYS = [
    "proposal_id",
    "lane",
    "title",
    "mechanism",
    "decision_rule_family",
    "representation_identity",
    "ancestry_risk_statement",
    "control_battery_spec",
    "feasibility_citation",
    "falsification_rule",
]

#: Forbidden outcome-metric vocabulary (case-insensitive, raw-text
#: regexes).  A proposal is a DECLARATION; none of this vocabulary has
#: any legitimate use in it.
FORBIDDEN_TOKEN_REGEXES = [
    r"expectanc",
    r"\bpnls?\b",
    r"sharpe",
    r"hit[_ ]?rate",
    r"win[_ ]?rate",
    r"\bcagr\b",
    r"drawdown",
    r"profit[_ ]?factor",
    r"\breturns?\b",
    r"total[_ ]?return",
    r"mean[_ ]?return",
    r"av(?:g|erage)[_ ]?return",
    r"excess[_ ]?return",
    r"equity[_ ]?curve",
    r"\balpha\b",
]

#: Every numeric leaf in a proposal must live under one of these KEY
#: NAMES.  They cover exactly three classes of committed structural
#: fact: P0/P2 census counts, frozen cost-projection constants (P1
#: contract tier 2.0 / P2 gate ceilings), and frozen rubric constants
#: from plan section 6.  Anything else numeric is a violation.
NUMERIC_LEAF_ALLOWLIST = frozenset({
    # P2 common-grid census structure
    "bookable_count",
    "grid_session_count",
    "coverage_fraction",
    "warmup_sessions",
    # P2 auction eligibility census structure
    "event_count",
    "events_bill",
    "events_note",
    "events_bond",
    # S5 curve census structure
    "years_pulled",
    "rows",
    # frozen cost-projection constants (P1 contract / P2 gate)
    "stress_tier_bps",
    "worst_case_round_trip_ceiling_bps",
    "holding_trading_days",
    "calendar_days_charged",
    # frozen rubric constants (plan section 6)
    "novelty_abs_rho_ceiling",
    "cell_budget",
    "arms_per_family_max",
    "families_max",
    "min_bookable_instants",
    "min_grid_eligible_events",
    "min_coverage_fraction",
    # d1_gate bookkeeping (never proposals, harmless here)
    "schema_version",
    "proposals_scanned",
    "files_scanned",
    "forbidden_token_hits",
    "numeric_leaf_violations",
    "files_with_outcome_numbers",
})

#: Required battery arm roles per lane (plan section 6 + packet).
BATTERY_ROLE_REQUIREMENTS = {
    "A4": frozenset({
        "ANCHOR",
        "DELAY_PAIR",
        "CLAIRVOYANT",
        "CLOCK_ONLY_SHADOW",
        "SHIFTED_CALENDAR_PLACEBO",
    }),
    "A5": frozenset({
        "ANCHOR",
        "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL",
        "CLOCK_ONLY_SHADOW",
        "PLACEBO",
    }),
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk_numeric_leaves(obj, path: str = ""):
    """Yield (path, key, value) for every numeric leaf (bool excluded)."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            yield from _walk_numeric_leaves(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            yield from _walk_numeric_leaves(val, f"{path}[{i}]")
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, (int, float)):
        key = path.rsplit(".", 1)[-1].split("[")[0]
        yield path, key, obj


def forbidden_token_scan(raw_text: str) -> list[str]:
    """Return the forbidden-token regexes that hit the raw text."""
    hits = []
    for pattern in FORBIDDEN_TOKEN_REGEXES:
        if re.search(pattern, raw_text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def numeric_leaf_violations(obj) -> list[dict]:
    """Return every numeric leaf whose key name is not allowlisted."""
    out = []
    for path, key, _val in _walk_numeric_leaves(obj):
        if key not in NUMERIC_LEAF_ALLOWLIST:
            out.append({"path": path, "key": key})
    return out


def pin_violations(obj, worktree: str = WORKTREE) -> list[dict]:
    """Every object with BOTH 'path' and 'sha256' must match disk."""
    out = []
    if isinstance(obj, dict):
        if "path" in obj and "sha256" in obj:
            p = os.path.join(worktree, str(obj["path"]))
            if not os.path.isfile(p):
                out.append({"path": obj["path"], "error": "MISSING_FILE"})
            elif sha256_file(p) != obj["sha256"]:
                out.append({"path": obj["path"], "error": "SHA_MISMATCH"})
        for val in obj.values():
            out.extend(pin_violations(val, worktree))
    elif isinstance(obj, list):
        for val in obj:
            out.extend(pin_violations(val, worktree))
    return out


def completeness_violations(obj) -> list[str]:
    """Missing/empty required frozen template fields (+ schema/id laws)."""
    out = []
    for key in REQUIRED_KEYS:
        if key not in obj:
            out.append(f"MISSING_FIELD:{key}")
        elif obj[key] in (None, "", {}, []):
            out.append(f"EMPTY_FIELD:{key}")
    if obj.get("schema") != SCHEMA_PROPOSAL:
        out.append(f"BAD_SCHEMA:{obj.get('schema')!r}")
    if obj.get("cycle_id") != CYCLE_ID:
        out.append(f"BAD_CYCLE_ID:{obj.get('cycle_id')!r}")
    if obj.get("base_sha") != BASE_SHA:
        out.append(f"BAD_BASE_SHA:{obj.get('base_sha')!r}")
    blind = obj.get("blindness_declaration")
    if not isinstance(blind, dict) or blind.get("status") != "OUTCOME_BLIND":
        out.append("BAD_BLINDNESS_DECLARATION")
    return out


def battery_violations(obj) -> list[str]:
    """Missing battery arm roles for the proposal's lane."""
    lane = obj.get("lane")
    if lane not in BATTERY_ROLE_REQUIREMENTS:
        return [f"BAD_LANE:{lane!r}"]
    battery = obj.get("control_battery_spec")
    arms = battery.get("arms") if isinstance(battery, dict) else None
    if not isinstance(arms, list) or not arms:
        return ["BAD_BATTERY:arms"]
    roles = {a.get("role") for a in arms if isinstance(a, dict)}
    missing = BATTERY_ROLE_REQUIREMENTS[lane] - roles
    return [f"MISSING_ARM_ROLE:{r}" for r in sorted(missing)]


def validate_proposal_obj(obj, worktree: str = WORKTREE) -> dict:
    """Full structural validation of one parsed proposal (incl. pins)."""
    comp = completeness_violations(obj)
    bat = battery_violations(obj) if not comp else []
    return {
        "completeness_violations": comp,
        "battery_violations": bat,
        "numeric_leaf_violations": numeric_leaf_violations(obj),
        "pin_violations": pin_violations(obj, worktree),
    }


def validate_proposal_file(path: str, worktree: str = WORKTREE) -> dict:
    """Load one committed proposal file and run every check."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    obj = json.loads(raw)
    tokens = forbidden_token_scan(raw)
    res = validate_proposal_obj(obj, worktree)
    res["forbidden_token_hits"] = tokens
    res["verdict"] = "PASS" if not (
        res["completeness_violations"]
        or res["battery_violations"]
        or res["numeric_leaf_violations"]
        or res["forbidden_token_hits"]
        or res["pin_violations"]
    ) else "FAIL"
    return res


def build_gate(authored_utc: str, worktree: str = WORKTREE) -> dict:
    """Derive the committed d1_gate.json from the proposal files."""
    files = []
    total_token_hits = 0
    total_leaf_violations = 0
    files_with_outcome_numbers = 0
    for pid in PROPOSAL_IDS:
        rel = os.path.join("research/control/rates_ng1_run/d1/proposals",
                           f"{pid}.json")
        full = os.path.join(worktree, rel)
        res = validate_proposal_file(full, worktree)
        obj = json.load(open(full, encoding="utf-8"))
        comp = {
            k: "PRESENT"
            if (k in obj and obj[k] not in (None, "", {}, []))
            else "MISSING"
            for k in REQUIRED_KEYS
        }
        files.append({
            "proposal_id": pid,
            "path": rel,
            "sha256": sha256_file(full),
            "schema": obj.get("schema"),
            "lane": obj.get("lane"),
            "title": obj.get("title"),
            "frozen_fields": comp,
            "missing_fields": [
                k for k, v in comp.items() if v == "MISSING"],
            "completeness_verdict":
                "PASS" if not res["completeness_violations"] else "FAIL",
            "battery_verdict":
                "PASS" if not res["battery_violations"] else "FAIL",
            "forbidden_token_hits": res["forbidden_token_hits"],
            "numeric_leaf_violations": [
                v["path"] for v in res["numeric_leaf_violations"]],
            "pin_violations": res["pin_violations"],
            "verdict": res["verdict"],
        })
        total_token_hits += len(res["forbidden_token_hits"])
        total_leaf_violations += len(res["numeric_leaf_violations"])
        if res["forbidden_token_hits"] or res["numeric_leaf_violations"]:
            files_with_outcome_numbers += 1
    gate_verdict = "PASS" if all(f["verdict"] == "PASS" for f in files) \
        else "FAIL"
    return {
        "schema": SCHEMA_GATE,
        "schema_version": GATE_SCHEMA_VERSION,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "base_sha": BASE_SHA,
        "authored_utc": authored_utc,
        "required_frozen_fields": {
            "template_field_1_identity": ["proposal_id", "lane", "title"],
            "template_field_2_mechanism": ["mechanism"],
            "template_field_3_rule_family": ["decision_rule_family"],
            "template_field_4_representation_identity":
                ["representation_identity"],
            "template_field_5_ancestry_risk": ["ancestry_risk_statement"],
            "template_field_6_control_battery": ["control_battery_spec"],
            "template_field_7_feasibility": ["feasibility_citation"],
            "template_field_8_falsification": ["falsification_rule"],
        },
        "battery_role_requirements": {
            lane: sorted(roles)
            for lane, roles in BATTERY_ROLE_REQUIREMENTS.items()
        },
        "proposal_files": files,
        "blindness_negative_scan": {
            "method": (
                "two-layer scan per proposal file: (a) forbidden "
                "outcome-metric token regexes over the raw text; "
                "(b) numeric-leaf allowlist -- every numeric leaf must "
                "sit under a key name in the frozen allowlist (P0/P2 "
                "census counts, frozen cost-projection constants, "
                "frozen rubric constants); any other numeric leaf is a "
                "violation.  NO outcome number of any kind may appear."
            ),
            "proposals_scanned": len(files),
            "files_scanned": len(files),
            "forbidden_token_hits": total_token_hits,
            "numeric_leaf_violations": total_leaf_violations,
            "files_with_outcome_numbers": files_with_outcome_numbers,
            "verdict": "PASS" if gate_verdict == "PASS" else "FAIL",
        },
        "verdict": gate_verdict,
    }


def write_gate(authored_utc: str, worktree: str = WORKTREE) -> dict:
    gate = build_gate(authored_utc, worktree)
    with open(GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=1, sort_keys=False)
        fh.write("\n")
    return gate


if __name__ == "__main__":
    import datetime

    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds")
    g = write_gate(stamp)
    print(json.dumps({
        "schema": g["schema"],
        "verdict": g["verdict"],
        "negative_scan": g["blindness_negative_scan"],
        "per_proposal": [
            {"proposal_id": f["proposal_id"], "verdict": f["verdict"]}
            for f in g["proposal_files"]
        ],
    }, indent=1))
