#!/usr/bin/env python
"""PB2 restate machine record + FX budget census recount (FX-EB-CALENDAR lane).

Census is a RECOUNT from the baseline hypo artifact (no new trials): re-read
fx_hypotheses.json, re-derive 36/family-leg arithmetic, re-extract the declared
strata contingency, and restate the no-ceiling convention.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep")
RC = WT / "research/control"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    court = RC / "FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/6e_6b/PB2_ANCESTRY_COURT_DRAFT.md"
    doc = {
        "schema": "fxeb_pb2_restate@1",
        "task_id": "FUTURES-SIX-READINESS-20261004",
        "lane": "FX-EB-CALENDAR",
        "generated_utc": NOW,
        "pb2_status": "HOLD by Co-Owner ruling — restated, NOT reopened, no new verdict text",
        "pointers": {
            "court_draft": {"path": str(court.relative_to(WT)), "sha256": sha256_file(court),
                            "key_line": "This court draft renders NO reopening verdict. PB2 remains HOLD."},
            "p3_quarantine_matrix": "sibling round FUTURES-P3-QUARANTINE-20261004 (read-only): cal_permitted T2 (6E 12/12, 6B 0/12 expiries 2023-2025) + verify/findings_final.json VF-12 (owner decision D1 context); quarantine/ capture values FORBIDDEN evidence until D1",
            "standing_rulings": ["PLAYBOOKS_DRAFT r5 section 2 HOLD", "NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER",
                                 "FX-F1 census contingency only (fx_hypotheses.json pb2_status)"],
        },
        "dependency_status_delta": {
            "court_d1_fx_holiday_calendar_6E": "was NOT_RUN at draft time; now 34/42 archived windows deviation-documented + 8 aged-out (holiday/holiday_deviation_6e_6b.json); 6B side remains 0/42 (NOT_OBTAINED, documented absence)",
            "court_d2_fee_table": "unchanged: MODELED / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW until owner-authorized A7 (packet READY-not-run)",
            "all_other_dependencies": "unchanged NOT_RUN (trigger census, per-pair dead books, placebo budget, BBO)",
        },
    }
    (RC / "FUTURES-SIX-READINESS-20261004/fx_eb/pb2/pb2_restate.json").write_text(json.dumps(doc, indent=1))

    # ---------------- census recount ----------------
    hyp_path = RC / "FUTURES-OVERNIGHT-PREP-20261003/hypo/6e_6b/fx_hypotheses.json"
    hyp = json.loads(hyp_path.read_text())
    census = hyp["trial_identity_census"]
    fams = {f["id"]: f for f in hyp["families"]}
    legs_base = sum(1 for fid in ("FX-F1", "FX-F2", "FX-F3", "FX-F4")
                    for s in fams[fid]["symbols"])
    per_leg = 2 * 2 * 3 * 3  # arms x tails x delays x tiers
    base_recount = legs_base * per_leg
    check = {
        "convention_restate": census["convention"],
        "per_family_leg_ids": per_leg,
        "base_family_legs": legs_base,
        "base_ids_recount": base_recount,
        "base_ids_declared": census["base_ids_if_all_families"],
        "base_match": base_recount == census["base_ids_if_all_families"],
        "per_family_census_ids_per_symbol_declared": {
            fid: fams[fid].get("census_ids_per_symbol") for fid in fams},
        "strata_overlay_contingency_declared": census["strata_overlay_contingency"],
        "strata_decomposition_note": "declared contingency in the artifact: F2 secondary strata (+36/stratum), F3 per-release-type splits + unclassified stratum, F4 Sunday stratum, F5/F6 regime overlays (36->72 on one host leg each); the artifact declares 360 at census level and its own per-family fields do not fully decompose it — restated as declared, not re-derived",
        "total_if_all_incl_strata": census["total_if_all_incl_strata"],
        "total_arithmetic_check": (base_recount + census["strata_overlay_contingency"]
                                   == census["total_if_all_incl_strata"]),
        "subset_6E_6B": "the ENTIRE 648 lives on 6E/6B: all six families' symbols are 6E/6B (F5 6B-primary + 6E-fragile, F6 6E-primary); the 6J/6A families are a separate census (hypo/6j_6a/jpy_aud_hypotheses.json) outside the FX-family number",
        "cap_status_restate": census["cap_status"],
        "controls_note": census["controls_not_counted"],
        "pb2_note": "FX-F1 census is contingency only (PB2 HOLD); recounted, not extended; zero new trials this lane",
        "source": {"path": str(hyp_path.relative_to(WT)), "sha256": sha256_file(hyp_path)},
    }
    out = RC / "FUTURES-SIX-READINESS-20261004/fx_eb/census/fx_census_recount.json"
    out.write_text(json.dumps({"schema": "fxeb_census_recount@1", "lane": "FX-EB-CALENDAR",
                               "task_id": "FUTURES-SIX-READINESS-20261004",
                               "generated_utc": NOW, "recount": check}, indent=1))
    print("base recount:", check["base_ids_recount"], "== declared:", check["base_match"])
    print("total arithmetic:", check["total_arithmetic_check"], "=", check["total_if_all_incl_strata"])


if __name__ == "__main__":
    main()
