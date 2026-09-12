"""RATES-NG1 D2 novelty measurement runner (P-12 commit-1 artifact).

Executes the D2 NOVELTY MEASUREMENT for the four D1 proposals and
writes the commit-2 results artifact ``d2_novelty_panel.json``.

P-12 execution order (dispatch packet rates-ng1-d2-novelty):
  1. commit-1 (this file and its siblings) is committed FIRST;
  2. THEN this runner is executed -- it freezes HEAD as the commit-1
     sha256 into the panel, builds every proposal and shadow
     decision-STATE series exactly as defined in d2_states.py under
     the frozen defaults in d2_frozen_defaults.py, and computes the
     paired Spearman/Pearson correlations;
  3. commit-2 carries the resulting panel.  NO rho number exists in
     any commit-1 file (enforced by tests/test_rates_ng1_d2.py).

Scope law: decision-STATE series correlation only.  No scored outcome,
no PnL, no cost-adjusted edge is computed or recorded anywhere.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.control.rates_ng1_run.d2 import d2_correlation as dc  # noqa: E402
from research.control.rates_ng1_run.d2 import d2_frozen_defaults as fd  # noqa: E402
from research.control.rates_ng1_run.d2 import d2_states as ds  # noqa: E402

SCHEMA = "rates_ng1_run/d2_novelty_panel@1"
TASK_ID = "rates-ng1-d2-novelty"
CYCLE_ID = "RATES-NG1"

#: Dispatch-packet BASE commit (the SHA the lane was frozen at).
BASE_SHA = "052e6c0f929adaf54fb3aea4c7d626251398a6b3"

#: commit-1 files pinned into the panel by content hash at run time.
COMMIT1_CODE_FILES = (
    "research/control/rates_ng1_run/d2/__init__.py",
    "research/control/rates_ng1_run/d2/d2_frozen_defaults.py",
    "research/control/rates_ng1_run/d2/d2_states.py",
    "research/control/rates_ng1_run/d2/d2_correlation.py",
    "research/control/rates_ng1_run/d2/d2_run.py",
    "research/control/rates_ng1_run/d2/d2_feasibility_renote.json",
)

#: Re-measured input artifact pins (paths relative to the repo root).
INPUT_PINS = (
    "research/control/rates_ng1_run/p2_grid_census.json",
    "research/control/rates_ng1_run/p2_auction_eligibility.json",
    "research/control/rates_ng1_run/p0_auction_census.json",
    "research/control/rates_ng1_run/substrate_manifest.json",
    "research/control/rates_ng1_run/d1/d1_gate.json",
    "research/control/rates_ng1_run/d1/proposals/RATESNG1-A4-P1.json",
    "research/control/rates_ng1_run/d1/proposals/RATESNG1-A4-P2.json",
    "research/control/rates_ng1_run/d1/proposals/RATESNG1-A5-P1.json",
    "research/control/rates_ng1_run/d1/proposals/RATESNG1-A5-P2.json",
)

PROPOSAL_STATE_KEYS = {
    "RATESNG1-A4-P1": "A4_P1_CONCENTRATION",
    "RATESNG1-A4-P2": "A4_P2_STAGE",
    "RATESNG1-A5-P1": "A5_P1_CURVATURE_GATED_SLOPE",
    "RATESNG1-A5-P2": "A5_P2_FRONT_VS_BELLY",
}
PROPOSAL_EVENT_BASED = {
    "RATESNG1-A4-P1": True,
    "RATESNG1-A4-P2": True,
    "RATESNG1-A5-P1": False,
    "RATESNG1-A5-P2": False,
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo_root: str) -> str:
    out = subprocess.run(
        ["git", "-C", repo_root, "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True)
    return out.stdout.strip()


def build_all_states(rep: dict) -> tuple[dict, dict]:
    """Build the five shadow series (shared representation) and the
    four proposal own-state series."""
    grid = rep["grid_dates"]
    instants = rep["instants"]
    level_fn = rep["level_fn"]

    shadows = {
        "dgs10_level_trailing_state": ds.shadow_dgs10_level_state(
            grid, instants, level_fn),
        "fx_reaction_direction": ds.shadow_reaction_direction_state(
            grid, instants, rep["event_indices"], level_fn),
        "fx_release_order": ds.shadow_release_order_state(
            grid, instants, rep["events"]),
        "momentum_63s": ds.shadow_momentum_63s_state(
            grid, instants, rep["leg_closes"]),
        "generic_dow_tue": ds.shadow_dow_tue_state(instants),
    }
    proposals = {
        "RATESNG1-A4-P1": ds.proposal_state_a4_p1(
            grid, instants, rep["events"]),
        "RATESNG1-A4-P2": ds.proposal_state_a4_p2(
            grid, instants, rep["events"]),
        "RATESNG1-A5-P1": ds.proposal_state_a5_p1(
            grid, instants, rep["curve_by_date"]),
        "RATESNG1-A5-P2": ds.proposal_state_a5_p2(
            instants, rep["curve_by_date"]),
    }
    return shadows, proposals


def _series_health(series: dict) -> dict:
    return {
        k: {
            "n_defined": sum(1 for v in v_series if v is not None),
            "n_total": len(v_series),
        }
        for k, v_series in series.items()
    }


def run_measurement(worktree_root: str,
                    output_path: str | None = None) -> dict:
    """Execute the measurement and write the commit-2 panel."""
    rep = ds.load_representation(worktree_root)
    commit1_sha = git_head(worktree_root)
    if commit1_sha == BASE_SHA:
        raise RuntimeError(
            "HEAD equals the dispatch BASE sha: commit-1 must exist "
            "before the measurement runs (P-12 order)")

    shadows, proposals = build_all_states(rep)

    proposal_blocks: dict = {}
    for pid in fd.PROPOSAL_IDS:
        own = proposals[pid]
        screens = {k: dc.shadow_screen(own, shadows[k])
                   for k in fd.SHADOW_KEYS}
        summary = dc.proposal_verdict(screens)
        proposal_blocks[pid] = {
            "lane": "A4" if PROPOSAL_EVENT_BASED[pid] else "A5",
            "event_based": PROPOSAL_EVENT_BASED[pid],
            "own_state_frozen_defaults_key": PROPOSAL_STATE_KEYS[pid],
            "own_state_health": _series_health({"own": own})["own"],
            "shadows": screens,
            "proposal_pooled_abs_rho": summary["proposal_pooled_abs_rho"],
            "margin_to_ceiling": summary["margin_to_ceiling"],
            "ceiling": float(fd.NOVELTY_ABS_RHO_CEILING),
            "unmeasurable_shadows": summary["unmeasurable_shadows"],
            "verdict": summary["verdict"],
        }

    with open(os.path.join(worktree_root, "research", "control",
                           "rates_ng1_run", "d2",
                           "d2_feasibility_renote.json"), "r",
              encoding="utf-8") as fh:
        renote = json.load(fh)

    measured_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    body = {
        "schema": SCHEMA,
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "base_sha": BASE_SHA,
        "commit_1_sha256": commit1_sha,
        "measurement_law": {
            "p12_order": ("commit-1 (code + frozen defaults, no rho) "
                          "-> measurement -> commit-2 (this panel)"),
            "scope": ("decision-STATE series correlation only: no "
                      "scored outcome, no PnL, no cost-adjusted edge "
                      "is computed or recorded"),
            "statistics": fd.CORRELATION_LAW["statistics"],
            "alignment": fd.CORRELATION_LAW["alignment"],
            "spearman_ties": fd.CORRELATION_LAW["spearman_ties"],
            "unmeasurable_rule": fd.CORRELATION_LAW["unmeasurable_rule"],
            "pooled_per_shadow": fd.CORRELATION_LAW["pooled_per_shadow"],
            "proposal_pooled": fd.CORRELATION_LAW["proposal_pooled"],
            "margin_definition": fd.CORRELATION_LAW["margin_definition"],
            "verdict_rule": fd.CORRELATION_LAW["verdict_rule"],
        },
        "representation": {
            "grid_census": "research/control/rates_ng1_run/p2_grid_census.json",
            "bookable_instants": len(rep["instants"]),
            "grid_sessions": len(rep["grid_dates"]),
            "bookable_window": [
                rep["instants"][0]["decision_session"],
                rep["instants"][-1]["decision_session"]],
            "event_mappings": len(rep["mappings"]),
            "shared_grid_note": (
                "all four D1 proposals pin the identical P2 common "
                "grid and instant set; the five shadow series are "
                "therefore reconstructed once on that shared "
                "representation and screened against each proposal's "
                "own frozen-default state series"),
        },
        "input_pins_sha256": {
            rel: sha256_file(os.path.join(worktree_root, rel))
            for rel in INPUT_PINS},
        "commit1_code_sha256": {
            rel: sha256_file(os.path.join(worktree_root, rel))
            for rel in COMMIT1_CODE_FILES},
        "series_health": {
            "shadows": _series_health(shadows),
            "proposals": _series_health(proposals),
        },
        "feasibility_renote": {
            "path": ("research/control/rates_ng1_run/d2/"
                     "d2_feasibility_renote.json"),
            "sha256": sha256_file(os.path.join(
                worktree_root, "research", "control", "rates_ng1_run",
                "d2", "d2_feasibility_renote.json")),
            "per_proposal": renote["proposals"],
        },
        "proposals": proposal_blocks,
    }
    body["results_body_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")).hexdigest()
    panel = dict(body)
    panel["measured_utc"] = measured_utc

    out = output_path or os.path.join(
        worktree_root, "research", "control", "rates_ng1_run", "d2",
        "d2_novelty_panel.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=1, sort_keys=False)
        fh.write("\n")
    return panel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree-root", default=REPO_ROOT)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)
    panel = run_measurement(os.path.abspath(args.worktree_root),
                            args.output)
    for pid, block in panel["proposals"].items():
        print(f"{pid}: pooled={block['proposal_pooled_abs_rho']} "
              f"margin={block['margin_to_ceiling']} "
              f"verdict={block['verdict']}")
    print("panel written:", panel["schema"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
