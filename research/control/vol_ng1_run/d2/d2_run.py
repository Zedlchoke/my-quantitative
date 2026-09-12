#!/usr/bin/env python
"""VOL-NG1 D2 novelty runner (task vol-ng1-d2-novelty, P-12 two-commit law).

RUN ONLY AFTER the code commit (commit-1: this file + d2_novelty.py +
tests, frozen parameters, NO numbers).  Consumes ONLY the committed
frozen substrate through the cycle's read-only plane adapter (NO
network), rebuilds the P2 common grid + bookable instants, reconstructs
each proposal's decision-state series at the FROZEN default parameters
and each of the five ancestry kill-shadows ON THE PROPOSAL'S OWN
DECLARED REPRESENTATION, and writes ``d2_novelty_panel.json`` (the
commit-2 results artifact) with per-proposal x per-shadow Spearman AND
Pearson decision-state correlations, pooled |rho| margins and
ELIGIBLE/VETO verdicts.

Q-6 NO-PnL: decision-STATE series only; no returns conditional on
states, no scoring, no outcome numbers anywhere in the measurement.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.vol_ng1 import feasibility as fb            # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa          # noqa: E402
from research.control.vol_ng1_run import p2_run as p2r           # noqa: E402
from research.control.vol_ng1_run.d2 import d2_novelty as dn     # noqa: E402

SCHEMA = "vol_ng1_run/d2_novelty_panel@1"
OUT_DIR = os.path.join(REPO_ROOT, "research", "control", "vol_ng1_run", "d2")
PANEL_PATH = os.path.join(OUT_DIR, "d2_novelty_panel.json")
D1_GATE_PATH = os.path.join(REPO_ROOT, "research", "control",
                            "vol_ng1_run", "d1", "d1_gate.json")
P2_GATE_PATH = p2r.GATE_PATH

TEST_COMMAND = (f"cd {REPO_ROOT} && {sys.executable} -m pytest "
                "tests/test_vol_ng1_d2.py -q")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False, default=str)
        fh.write("\n")


def git_state() -> dict:
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", REPO_ROOT, *args],
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    return {"branch": git("branch", "--show-current"),
            "head_sha_code_commit": git("rev-parse", "HEAD")}


def round12(v):
    return None if v is None else round(float(v), 12)


def load_proposals_with_identity() -> list[dict]:
    """The four D1 proposals, sha256-verified against the committed
    d1_gate records (fail-closed on any drift)."""
    with open(D1_GATE_PATH, "r", encoding="utf-8") as fh:
        d1 = json.load(fh)
    recorded = {p["proposal_id"]: p for p in d1["proposals"]}
    out = []
    for pid in sorted(recorded):
        rec = recorded[pid]
        path = os.path.join(REPO_ROOT, rec["path"])
        measured = sha256_file(path)
        if measured != rec["sha256"]:
            raise dn.D2NoveltyError(
                f"proposal {pid} sha256 drift: measured {measured} != "
                f"d1_gate recorded {rec['sha256']} (fail-closed)")
        with open(path, "r", encoding="utf-8") as fh:
            prop = json.load(fh)
        shadows = prop["ancestry_risk_statement"]["kill_candidate_shadows"]
        if sorted(shadows) != sorted(dn.SHADOW_IDS):
            raise dn.D2NoveltyError(
                f"{pid}: declared kill shadows {shadows} != the frozen "
                f"D2 shadow set {list(dn.SHADOW_IDS)}")
        out.append({"proposal_id": pid, "path": rec["path"],
                    "sha256": measured, "doc": prop})
    return out


def build_context(grid: list[str], bookable: list[str],
                  index_closes: dict, adj: dict) -> dict:
    return {
        "grid": grid,
        "instants": bookable,
        "index": index_closes,
        "adj": adj,
        "leg_subset": None,      # set per proposal
        "proxy_leg": fb.PROXY_LEG,
        "proxy_lookback_sessions": fb.PROXY_LOOKBACK_SESSIONS,
        "proxy_annualization": fb.PROXY_ANNUALIZATION,
    }


def feasibility_renote(proposal: dict, a4: dict, a5: dict,
                       p2_sha: str, bookable: list[str]) -> dict:
    """Per-proposal feasibility RE-NOTE at D2: the measurement-window
    instants exist, cited to the P2 census (the packet's citation
    requirement); re-measured here and equality-checked."""
    pid = proposal["proposal_id"]
    renote = {
        "instants_exist": True,
        "note": ("measurement-window instants exist at D2: the frozen "
                 "P2 bookable grid carries a valid decision instant at "
                 "every measured point of this proposal's representation"),
        "n_bookable_instants_remeasured": len(bookable),
        "d2_measurement_window": [bookable[0], bookable[-1]],
        "p2_census_citation": {
            "source": ("research/control/vol_ng1_run/p2_gate.json "
                       "sections.a4_term_structure_slope"),
            "p2_gate_json_sha256_remeasured": p2_sha,
            "p2_lane_verdict": a4["verdict"],
            "p2_bookable_instants": a4["bookable_instants"],
            "p2_first_bookable_instant": a4["first_bookable_instant"],
            "p2_last_bookable_instant": a4["last_bookable_instant"],
            "p2_coverage_primary": a4["coverage_primary"],
            "frozen_floor_min_bookable_instants":
                a4["frozen_floors"]["min_bookable_instants"],
            "frozen_floor_min_coverage":
                a4["frozen_floors"]["min_coverage"],
        },
    }
    if pid.startswith("VOLNG1-A5"):
        renote["p2_a5_census_citation"] = {
            "source": ("research/control/vol_ng1_run/p2_gate.json "
                       "sections.a5_risk_premium"),
            "p2_lane_verdict": a5["verdict"],
            "p2_bookable_instants_state_computable":
                a5["bookable_instants_state_computable"],
            "frozen_floor_min_bookable_computable_instants":
                a5["frozen_floor"]["min_bookable_computable_instants"],
        }
    matches = (len(bookable) == a4["bookable_instants"]
               and bookable[0] == a4["first_bookable_instant"]
               and bookable[-1] == a4["last_bookable_instant"])
    renote["matches_p2_census"] = bool(matches)
    if not matches:
        raise dn.D2NoveltyError(
            f"{pid}: D2 re-measured bookable grid drifts from the P2 "
            "census (fail-closed)")
    return renote


def measure_proposal(proposal: dict, ctx: dict, a4: dict, a5: dict,
                     p2_sha: str) -> dict:
    pid = proposal["proposal_id"]
    ctx = dict(ctx)
    ctx["leg_subset"] = dn.PROPOSAL_LEG_SUBSETS[pid]
    builder = dn.PROPOSAL_BUILDERS[pid]
    state, _meta = builder(ctx)
    instants = ctx["instants"]

    shadow_rows = []
    for sid in dn.SHADOW_IDS:
        try:
            shadow_state = dn.SHADOW_BUILDERS[sid](ctx)
        except dn.D2NoveltyError as exc:
            shadow_rows.append({
                "shadow_id": sid,
                "mapped_form": dn.SHADOW_MAPPINGS[sid],
                "leg_subset": list(ctx["leg_subset"]),
                "status": dn.STATUS_UNMEASURABLE,
                "n_bookable_instants": len(instants),
                "n_invalid_dropped": None,
                "n_used": None,
                "spearman": None, "pearson": None, "pooled_abs_max": None,
                "margin_to_gate": None,
                "shadow_state_distribution": {},
                "note": f"lawful reconstruction refused: {exc}",
                "documented_inapplicability": None,
            })
            continue
        row = dn.correlate_on_overlap(state, shadow_state, instants)
        row.update({
            "shadow_id": sid,
            "mapped_form": dn.SHADOW_MAPPINGS[sid],
            "leg_subset": list(ctx["leg_subset"]),
            "shadow_state_distribution": dn.state_distribution(
                shadow_state, instants),
            "margin_to_gate": (None if row["pooled_abs_max"] is None else
                               round12(dn.FROZEN_DEFAULTS["margin_abs_rho"]
                                       - row["pooled_abs_max"])),
            "documented_inapplicability": None,
        })
        for k in ("spearman", "pearson", "pooled_abs_max"):
            row[k] = round12(row[k])
        # canonical key order
        shadow_rows.append({
            "shadow_id": sid,
            "mapped_form": row["mapped_form"],
            "leg_subset": row["leg_subset"],
            "status": row["status"],
            "n_bookable_instants": row["n_bookable_instants"],
            "n_invalid_dropped": row["n_invalid_dropped"],
            "n_used": row["n_used"],
            "spearman": row["spearman"],
            "pearson": row["pearson"],
            "pooled_abs_max": row["pooled_abs_max"],
            "margin_to_gate": row["margin_to_gate"],
            "shadow_state_distribution": row["shadow_state_distribution"],
            "note": row["note"],
            "documented_inapplicability":
                row["documented_inapplicability"],
        })

    verdict = dn.proposal_verdict(shadow_rows)
    doc = proposal["doc"]
    entry = {
        "proposal_id": pid,
        "path": proposal["path"],
        "sha256": proposal["sha256"],
        "lane": doc["lane"],
        "family_id": doc["decision_rule_family"]["family_id"],
        "decision_axis": dn.PROPOSAL_AXIS[pid],
        "axis_encoding_note": (
            "short-vol pole +1 / flat 0 / long-vol pole -1; for "
            "VOLNG1-A5-P2 the bucket-allocation axis is encoded on the "
            "same poles by its own declared semantics (front bucket = "
            "the short-vol roll-carry pole, mid bucket = the "
            "protection pole)"),
        "frozen_defaults_used": {
            "leg_subset": list(ctx["leg_subset"]),
            "proxy_leg": ctx["proxy_leg"],
            "proxy_lookback_sessions": ctx["proxy_lookback_sessions"],
            "mid_reference_leg": dn.FROZEN_DEFAULTS[
                "a5p2_mid_reference_leg"] if pid == "VOLNG1-A5-P2" else None,
            "law": "all parameters frozen at the declared neutral "
                   "defaults in the code commit BEFORE any rho was "
                   "computed; no threshold moves after any number",
        },
        "structural_limitation_verbatim_match_p2": (
            self_limitation_check(doc) if pid.startswith("VOLNG1-A5")
            else None),
        "n_bookable_instants": len(instants),
        "decision_state_distribution": dn.state_distribution(state, instants),
        "feasibility_renote": feasibility_renote(proposal, a4, a5, p2_sha,
                                                 instants),
        "shadows": shadow_rows,
        "pooled_abs_max": round12(verdict["pooled_abs_max"]),
        "margin_to_gate": round12(verdict["margin_to_gate"]),
        "verdict": verdict["verdict"],
        "veto_reasons": verdict["veto_reasons"],
    }
    return entry


def self_limitation_check(doc: dict) -> bool:
    """A5 proposals must carry the P2 C8 structural limitation VERBATIM
    (equality-checked against the committed p2_gate text)."""
    declared = doc.get("structural_limitation_p2_gate_c8_verbatim")
    return declared == fb.A5_LIMITATION_TEXT


def main() -> int:
    started = now_utc()
    plane = pa.VolNg1Plane()
    sub = p2r.consume_substrate(plane)
    adj, evlaw = p2r.event_adjusted_legs(sub)

    # frozen representation: re-measure the P2 census, equality-checked
    grid = fb.common_grid(sub["index_closes"], adj)
    window = fb.window_sessions(grid)
    bookable, tail = fb.bookable_sessions(grid, window)
    a4 = fb.a4_lane(grid)
    granted = {s: plane.verdict(s) for s in sorted(pa.FROZEN_TARGET_SET)}
    a5 = fb.a5_lane(grid, adj[fb.PROXY_LEG], granted)

    with open(P2_GATE_PATH, "r", encoding="utf-8") as fh:
        p2_gate = json.load(fh)
    p2_sha = sha256_file(P2_GATE_PATH)
    cited_sha = p2_gate["artifact_hashes_cited"]["p0_gate_json_sha256"]
    p0_sha = sha256_file(p2r.P0_GATE_PATH)
    if p0_sha != cited_sha:
        raise dn.D2NoveltyError(
            f"P0 gate digest drift: {p0_sha} != cited {cited_sha}")
    if a4["bookable_instants"] != \
            p2_gate["sections"]["a4_term_structure_slope"][
                "bookable_instants"] \
            or a4["coverage_primary"] != \
            p2_gate["sections"]["a4_term_structure_slope"][
                "coverage_primary"]:
        raise dn.D2NoveltyError(
            "A4 census drift vs committed p2_gate (fail-closed)")
    if a5["bookable_instants_state_computable"] != \
            p2_gate["sections"]["a5_risk_premium"][
                "bookable_instants_state_computable"]:
        raise dn.D2NoveltyError(
            "A5 computability drift vs committed p2_gate (fail-closed)")

    proposals = load_proposals_with_identity()
    ctx = build_context(grid, bookable, sub["index_closes"], adj)

    proposal_entries = [
        measure_proposal(p, ctx, a4, a5, p2_sha) for p in proposals]

    verdicts = {e["proposal_id"]: e["verdict"]
                for e in proposal_entries}
    panel = {
        "schema": SCHEMA,
        "task_id": dn.TASK_ID,
        "cycle_id": dn.CYCLE_ID,
        "lane": "d2",
        "invocation": "lead-bg-vol-d2",
        "question": (
            "D2 NOVELTY selection gate: does any ancestry kill-shadow "
            "decision-state correlate with a proposal's own "
            "frozen-default decision-state beyond the frozen margin on "
            "the proposal's own declared representation?"),
        "measured_utc": started,
        "published_utc": now_utc(),
        "worktree": REPO_ROOT,
        "git": git_state(),
        "law": {
            "p12_two_commits": (
                "commit-1 = code + frozen parameters + shadow "
                "definitions (NO numbers); commit-2 = this panel"),
            "margin": dn.FROZEN_DEFAULTS["margin_abs_rho"],
            "margin_law": "pooled |rho| <= 0.20 == ELIGIBLE, else VETO",
            "pooled_law": "per shadow pooled = max(|spearman|, "
                          "|pearson|); proposal pooled = max over "
                          "shadows",
            "fail_closed_law": (
                "an unmeasurable shadow makes the proposal "
                "VETO_PENDING unless provably inapplicable "
                "(documented); absence is never PASS; an uncomputable "
                "state is INVALID and refused, never coerced (Q-11)"),
            "no_pnl_law": (
                "decision-STATE series correlation only; no scored "
                "outcomes, no PnL numbers anywhere (Q-6)"),
            "freeze_law": (
                "all D1-symbolic parameters frozen at declared neutral "
                "defaults in the code commit BEFORE any rho was "
                "computed; the A5-P2 mid-bucket extension froze in the "
                "same commit"),
        },
        "frozen_parameter_freeze": {
            "frozen_in": "commit-1 (research/control/vol_ng1_run/d2/"
                         "d2_novelty.py)",
            "head_sha_at_measurement": git_state()[
                "head_sha_code_commit"],
            "defaults": dn.FROZEN_DEFAULTS,
            "shadow_mappings": dn.SHADOW_MAPPINGS,
            "leg_subsets": {k: list(v) for k, v in
                            dn.PROPOSAL_LEG_SUBSETS.items()},
            "axis_encodings": dn.PROPOSAL_AXIS,
        },
        "consumed_via_plane": {
            "etp_digests": sub["etp_digests"],
            "index_digests": sub["index_digests"],
            "network_reads": 0,
            "store_write_ops": 0,
        },
        "artifact_hashes_cited": {
            "p0_gate_json_sha256": p0_sha,
            "p1_gate_json_sha256": sha256_file(p2r.P1_GATE_PATH),
            "p1_cost_contract_json_sha256":
                sha256_file(p2r.CONTRACT_PATH),
            "p2_gate_json_sha256": p2_sha,
            "d1_gate_json_sha256": sha256_file(D1_GATE_PATH),
            "corp_actions_py_sha256": sha256_file(
                os.path.join(REPO_ROOT, "research", "assets", "vol_ng1",
                             "corp_actions.py")),
        },
        "representation_checks": {
            "definition": "the P2 common grid: strict intersection of "
                          "VIX9D x VIX x VIX3M with the event-adjusted "
                          "closes of ALL SIX living ETP legs",
            "consumption_law": evlaw["consumption_law"],
            "event_layer_max_abs_mechanical_residual":
                evlaw["max_abs_mechanical_residual"],
            "inventory_total_steps": evlaw["inventory_total_steps"],
            "grid_sessions_total": len(grid),
            "window_sessions_post_2015": len(window),
            "warmup_carveout_sessions": fb.WARMUP_SESSIONS,
            "first_bookable_instant": bookable[0],
            "last_bookable_instant": bookable[-1],
            "v7_tail_refused_sessions": tail,
            "bookable_instants": len(bookable),
            "a4_lane_verdict": a4["verdict"],
            "a5_lane_verdict": a5["verdict"],
            "matches_p2_census": True,
            "granted_series_verdicts": granted,
        },
        "proposals": proposal_entries,
        "summary": {
            "verdicts": verdicts,
            "eligible": sorted(k for k, v in verdicts.items()
                               if v == "ELIGIBLE"),
            "veto": sorted(k for k, v in verdicts.items()
                           if v == "VETO"),
            "veto_pending": sorted(k for k, v in verdicts.items()
                                   if v == "VETO_PENDING"),
        },
        "test_command": TEST_COMMAND,
        "test_verdict_note": (
            "the packet test command (tests/test_vol_ng1_d2.py) is run "
            "against the committed panel after the results commit; its "
            "authoritative exit_code is recorded in the D2 structured "
            "handoff (the panel cannot embed its own post-commit test "
            "run)"),
        "no_pnl_note": (
            "this panel contains decision-state correlations only: no "
            "returns conditional on states, no expectancies, no "
            "scoring, no PnL numbers (Q-6)"),
    }
    write_json(PANEL_PATH, panel)
    print(f"d2_novelty_panel written: {PANEL_PATH}")
    for pid, v in verdicts.items():
        entry = next(e for e in proposal_entries if e["proposal_id"] == pid)
        print(f"  {pid}: {v} pooled={entry['pooled_abs_max']} "
              f"margin={entry['margin_to_gate']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dn.D2NoveltyError as exc:
        print(f"D2 FAIL-CLOSED: {exc!r}", file=sys.stderr)
        raise SystemExit(3)
    except Exception as exc:  # noqa: BLE001 -- fail-closed runner
        print(f"D2 ERROR: {exc!r}", file=sys.stderr)
        raise SystemExit(3)
