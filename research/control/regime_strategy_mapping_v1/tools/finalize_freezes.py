#!/usr/bin/env python
"""A1 freeze finalization — converts lane PROPOSALS into FROZEN contracts.

Writes (idempotent, deterministic):
  freezes/specialist_library_freeze.json   (pins A4 proposal by sha256)
  freezes/rsmv1_arms_freeze.json           (A6 proposal + V2 pins filled)
  freezes/rsmv1_selection_freeze.json      (pins A6 proposal by sha256)
  freezes/rsmv1_turnover_freeze.json       (pins A6 proposal by sha256)
  freezes/rsmv1_evaluation_freeze.json     (pins A6 proposal by sha256)
  freezes/rsmv1_freeze_manifest.json       (sha256 of every frozen file)

The specialist/selection/turnover/evaluation PARAMETER sources of truth are
the pinned proposal files (copied verbatim, never edited); the freeze
wrappers add status + pins. Arms freeze is a full copy of the A6 proposal
with the V2 reference pins A6 was forbidden to read.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
FZ = CYCLE_DIR / "freezes"
V2 = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v2/"
    "integration/research/control/jev_regime_router_v2/runtime/scored"
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write(name: str, payload: dict) -> str:
    p = FZ / name
    p.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return sha(p)


def pin_wrapper(frozen_name: str, proposal_name: str, extra: dict) -> dict:
    prop = FZ / proposal_name
    d = sha(prop)
    payload = json.loads(prop.read_text())
    return {
        "schema": "rsmv1_freeze_wrapper@1",
        "frozen_contract": frozen_name,
        "status": "FROZEN",
        "frozen_at_utc": now(),
        "parameter_source_of_truth": {
            "file": f"freezes/{proposal_name}",
            "sha256": d,
            "law": "copied verbatim from the lane proposal; never edited; "
                   "any change requires a new freeze + fresh audit",
        },
        "proposed_by": payload.get("role"),
        "frozen_by": "A1",
        **extra,
    }


def main() -> int:
    manifest: dict[str, str] = {}

    # 1) specialist library (A4)
    prop = json.loads((FZ / "specialist_library_proposal.json").read_text())
    n_spec = sum(len(r["specialists"]) for r in prop["regimes"].values())
    assert n_spec == 6, f"library must stay at 6 specialists, got {n_spec}"
    w = pin_wrapper(
        "specialist_library_freeze.json", "specialist_library_proposal.json",
        {
            "bounds": {
                "max_specialists_per_regime": 2,
                "total_specialists": 6,
                "unk_policy": "FLAT fixed, not selectable",
                "spy_law": "long/flat only; shorts BTC-only",
                "counter_trend": "none (rejected alternatives recorded)",
            },
            "executable_mapping": "rsmv1.specialists.build_specs (verbatim params)",
        },
    )
    manifest["specialist_library_freeze.json"] = write(
        "specialist_library_freeze.json", w)

    # 2) arms freeze (A6 + V2 pins)
    arms = json.loads((FZ / "rsmv1_arms_freeze.proposal.json").read_text())
    pins = {}
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        p = V2 / cell / "JEV_ONLY_ROUTER" / "tier_1.json"
        t = json.loads(p.read_text())["totals"]
        pins[cell] = {
            "gross": t["gross_pnl"], "fee": t["costs_fee"],
            "slip": t["costs_slip"], "funding": t["costs_funding"],
            "net": t["net_pnl"], "trades": t["trades"],
            "artifact": f"V2 runtime/scored/{cell}/JEV_ONLY_ROUTER/tier_1.json",
            "artifact_sha256": sha(p),
        }
    arms["v2_reference_pins"] = {
        "b_engine_equivalence_v2_jev_only_tier1_totals_per_cell": pins,
        "v2_trade_count_pins": {"BTC_H1": 978, "BTC_H4": 1060, "SPY_D1": 343},
        "position_switch_count_definition":
            "number of COMPLETED TRADE RECORDS (position opens) — identical "
            "to the V2 trade-count pin semantics",
        "status": "PINNED_BY_A1_FROM_TERMINAL_V2 (read-only)",
    }
    arms["status"] = "FROZEN"
    arms["frozen_at_utc"] = now()
    arms["frozen_by"] = "A1 (pins) + A6 (design)"
    manifest["rsmv1_arms_freeze.json"] = write("rsmv1_arms_freeze.json", arms)

    # 3-5) selection / turnover / evaluation (A6, pin-by-digest wrappers)
    for frozen, proposal, extra in [
        ("rsmv1_selection_freeze.json", "rsmv1_selection_freeze.proposal.json",
         {"code_mapping": "rsmv1.selection (INNER floors 5/150, tie law)"}),
        ("rsmv1_turnover_freeze.json", "rsmv1_turnover_freeze.proposal.json",
         {"code_mapping": "rsmv1.turnover (BUFFER k=1, no-op law) + scored "
                          "fixed-point min-hold suppression"}),
        ("rsmv1_evaluation_freeze.json", "rsmv1_evaluation_freeze.proposal.json",
         {"code_mapping": "verdict evaluation in the terminal analysis"}),
    ]:
        w = pin_wrapper(frozen, proposal, extra)
        manifest[frozen] = write(frozen, w)

    # manifest
    m = {
        "schema": "rsmv1_freeze_manifest@1",
        "cycle": "REGIME-STRATEGY-MAPPING-V1",
        "frozen_at_utc": now(),
        "files": manifest,
        "input_contracts_v2": {
            "note": "the 10 V2 freeze files in freezes/ are READ-ONLY input "
                    "contracts reused from JEV-REGIME-ROUTER-V2 (verified by "
                    "their own V2 manifest); this manifest lists ONLY RSMV1 "
                    "frozen contracts",
        },
    }
    (FZ / "rsmv1_freeze_manifest.json").write_text(
        json.dumps(m, indent=1, sort_keys=True) + "\n")
    print(json.dumps(m, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
