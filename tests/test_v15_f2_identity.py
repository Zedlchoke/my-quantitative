"""V15 I lane (i-family-2) -- TAKER-SAT frozen identity + authority pins.

Pins (all BEFORE any cell has run anywhere in the cycle; budget 0/6):

* the five frozen authorities on disk hash EXACTLY to the sha256s recorded
  in ``frozen_identity.PINNED_AUTHORITY_SHA256`` (proposal_P1, selection
  freeze, p3 freeze, amendment 1, probe verdict);
* the three SELECTED arm ids are the selection-freeze names; the per-arm
  ``arm_config_digest`` recorded at implementation time equals the digest
  recomputed from the frozen identity payload (pairwise unique);
* the frozen constants quoted verbatim from the authorities (cap 0.30,
  weight 0.10, gross 1.0, min available 10, lag 3 days, windows 10/20,
  fee 5.0 bps, stress x1.5 / +2 ticks / +1 delay, folds, hole rule, funding
  cap, defect dates);
* the frozen 20-symbol binding universe;
* fail-closed discipline: unknown arm/tier refused and ``run_arm(scored=
  True)`` REFUSES (no scored flags from the implementation lane).

No data file is read, nothing is scored.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.adapter_v10.protocol import ContractViolation
from research.v15.families.taker_sat import arms
from research.v15.families.taker_sat import runner as runner_mod
from research.v15.families.taker_sat.frozen_identity import (
    ANCHOR_ARM,
    ARM_CONFIG_IDS,
    ARM_IDS,
    ARM_ROLES,
    BASE_SLIP_TICKS,
    CAP_MAX,
    CHURN_FLOOR_C,
    CONTROL_ARM,
    FOLDS,
    FUNDING_RATE_ABS_CAP,
    GLOBAL_DEFECT_DATES,
    GROSS_MAX,
    LAG_DAYS,
    LOG_CLIP_ABS,
    MIN_AVAILABLE,
    NEIGHBOUR_ARM,
    N_SIDE,
    PINNED_AUTHORITY_SHA256,
    PROPOSAL_ARM_IDS,
    RATIO_CLIP_HI,
    RATIO_CLIP_LO,
    REBALANCE_DAYS,
    STRESS_DELAY_DAYS,
    STRESS_FEE_MULTIPLIER,
    STRESS_SLIP_TICKS,
    TAKER_FEE_BPS,
    TAKER_SAT_ARM_CONFIG_DIGESTS,
    UNIVERSE,
    WEIGHT_PER_NAME,
    WINDOW_DAYS_ANCHOR,
    WINDOW_DAYS_NEIGHBOUR,
    frozen_arm_digest_report,
    frozen_identity,
    verify_pinned_authorities,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_v15f2_pinned_authorities_match_disk():
    report = verify_pinned_authorities(REPO_ROOT)
    assert set(report) == set(PINNED_AUTHORITY_SHA256)
    for name, entry in report.items():
        assert entry["match"] is True, name
        assert entry["observed_sha256"] == PINNED_AUTHORITY_SHA256[name]["sha256"]


def test_v15f2_proposal_sha256_is_the_frozen_pin():
    proposal = json.loads(
        (REPO_ROOT / "research/control/v15_run/d1/a6/proposal_P1.json").read_text()
    )
    assert proposal["hypothesis_id"] == "A6-V15-P1"
    assert proposal["universe"] == list(UNIVERSE)
    selection = json.loads(
        (REPO_ROOT / "research/control/v15_run/selection_freeze_v15.json").read_text()
    )
    family = next(
        f
        for f in selection["selected_families"]
        if f["family_id"] == "A6-V15-F1-TAKER-SAT"
    )
    assert family["proposal_sha256"] == PINNED_AUTHORITY_SHA256["proposal_P1"]["sha256"]
    assert family["arms"][0] == "A6-F1-ANCHOR-SAT"
    assert family["arms"][2].startswith("A6-F1-CTL-RAWSAT")


def test_v15f2_arm_ids_roles_and_digest_pins():
    assert ARM_IDS == ("A6-F1-ANCHOR-SAT", "A6-F1-CTL-RAWSAT", "A6-F1-NEIGHBOR")
    assert ARM_ROLES[ANCHOR_ARM] == "anchor"
    assert ARM_ROLES[NEIGHBOUR_ARM] == "neighbour"
    assert ARM_ROLES[CONTROL_ARM] == "causal_negative_control"
    assert PROPOSAL_ARM_IDS[ANCHOR_ARM] == "A6-V15-P1-ANCHOR"
    report = frozen_arm_digest_report()
    assert len(report) == 3
    for arm in ARM_IDS:
        assert report[arm]["match"] is True, arm
        assert report[arm]["computed_from_identity"] == TAKER_SAT_ARM_CONFIG_DIGESTS[arm]
    digests = [report[arm]["computed_from_identity"] for arm in ARM_IDS]
    assert len(set(digests)) == 3, "arm digests must be pairwise unique"
    assert ARM_CONFIG_IDS == {
        ANCHOR_ARM: "SAT-W10",
        NEIGHBOUR_ARM: "SAT-W20",
        CONTROL_ARM: "RAWSAT-W10",
    }


def test_v15f2_arm_specs_are_structurally_distinct():
    anchor = arms.arm_spec(ANCHOR_ARM)
    neighbour = arms.arm_spec(NEIGHBOUR_ARM)
    control = arms.arm_spec(CONTROL_ARM)
    # single-knob horizon variant: identical everything except the window
    assert neighbour["with_churn"] == anchor["with_churn"] is True
    assert neighbour["window_days"] == WINDOW_DAYS_NEIGHBOUR
    assert anchor["window_days"] == WINDOW_DAYS_ANCHOR
    # the control DELETES the churn denominator: no OI input at all
    assert control["with_churn"] is False
    assert control["window_days"] == anchor["window_days"]
    assert arms.is_control_arm(CONTROL_ARM)
    assert not arms.is_control_arm(ANCHOR_ARM)


def test_v15f2_frozen_constants_quoted_from_authorities():
    assert (RATIO_CLIP_LO, RATIO_CLIP_HI) == (0.2, 5.0)
    assert LOG_CLIP_ABS == 1.609
    assert CHURN_FLOOR_C == 0.02
    assert LAG_DAYS == 3
    assert (WINDOW_DAYS_ANCHOR, WINDOW_DAYS_NEIGHBOUR) == (10, 21)
    assert N_SIDE == 5
    assert WEIGHT_PER_NAME == 0.10
    assert CAP_MAX == 0.30
    assert GROSS_MAX == 1.0
    assert MIN_AVAILABLE == 10
    assert REBALANCE_DAYS == 5
    assert TAKER_FEE_BPS == 5.0
    assert BASE_SLIP_TICKS == 1
    assert STRESS_FEE_MULTIPLIER == 1.5
    assert STRESS_SLIP_TICKS == BASE_SLIP_TICKS + 2 == 3
    assert STRESS_DELAY_DAYS == 1
    assert FUNDING_RATE_ABS_CAP == 0.0375
    assert GLOBAL_DEFECT_DATES == frozenset(
        {"2025-07-21", "2025-07-22", "2025-08-29", "2026-08-12"}
    )


def test_v15f2_frozen_folds_and_universe():
    assert FOLDS == (
        ("F0", "2025-08-22", "2025-12-21"),
        ("F1", "2025-12-21", "2026-04-21"),
        ("F2", "2026-04-21", "2026-08-22"),
    )
    assert len(UNIVERSE) == 20
    assert len(set(UNIVERSE)) == 20
    proposal = json.loads(
        (REPO_ROOT / "research/control/v15_run/d1/a6/proposal_P1.json").read_text()
    )
    assert sorted(proposal["universe"]) == sorted(UNIVERSE)


def test_v15f2_frozen_schedule_facts():
    from research.v15.families.taker_sat import book

    boundaries = book.schedule()
    decisions = [b for b in boundaries if b["kind"] == "decision"]
    flats = [b for b in boundaries if b["kind"] == "force_flat"]
    assert [b["fold_label"] for b in flats] == ["F0", "F1", "F2"]
    iso = [book.fold_of_instant(b["instant_ns"]) for b in boundaries]
    assert iso == [b["fold_label"] for b in boundaries]
    from research.v11.families.oilever_delev.strategy import iso_utc

    flat_iso = [iso_utc(b["instant_ns"])[:10] for b in flats]
    # force-flat covers the last covered date of each fold (the purge day)
    assert flat_iso == ["2025-12-20", "2026-04-20", "2026-08-21"]
    counts = {label: 0 for label in ("F0", "F1", "F2")}
    for b in decisions:
        counts[b["fold_label"]] += 1
    assert counts == {"F0": 24, "F1": 24, "F2": 25}
    # every decision sits strictly before its fold's purge day and is
    # exactly 5 calendar days from its fold start
    day_ns = 86_400_000_000_000
    for label, start_date, _end in FOLDS:
        from research.v11.families.oilever_delev.strategy import parse_iso_utc

        start = parse_iso_utc(f"{start_date}T00:00:00Z")
        members = [b["instant_ns"] for b in decisions if b["fold_label"] == label]
        assert members[0] == start
        for stamp in members:
            assert (stamp - start) % (5 * day_ns) == 0
        flat_ns = next(
            b["instant_ns"] for b in flats if b["fold_label"] == label
        )
        assert members[-1] < flat_ns
    assert iso_utc(decisions[0]["instant_ns"]) == "2025-08-22T00:00:00Z"
    assert iso_utc(decisions[23]["instant_ns"]) == "2025-12-15T00:00:00Z"
    assert iso_utc(decisions[-1]["instant_ns"]) == "2026-08-19T00:00:00Z"


def test_v15f2_staged_root_artifact_matches_identity(tmp_path):
    payload = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "research/v15/families/taker_sat/staged_root.json"
        ).read_text()
    )
    assert payload["family_id"] == "A6-V15-F1-TAKER-SAT"
    assert payload["no_pnl_computed"] is True
    assert payload["loader_contract"]["lag_days"] == 3
    assert payload["loader_contract"]["global_defect_date_exclusions"] == [
        "2025-07-21",
        "2025-07-22",
        "2025-08-29",
        "2026-08-12",
    ]
    assert payload["pinned_authorities_sha256"]["proposal_P1"] == (
        PINNED_AUTHORITY_SHA256["proposal_P1"]["sha256"]
    )
    assert payload["arm_config_digests"]["A6-F1-ANCHOR-SAT"] == (
        TAKER_SAT_ARM_CONFIG_DIGESTS[ANCHOR_ARM]
    )
    assert Path(payload["data_root"]).name == "parquet"


def test_v15f2_unknown_arm_and_unknown_tier_refused(tmp_path):
    with pytest.raises(ContractViolation):
        arms.arm_spec("NOT-AN-ARM")
    with pytest.raises(ContractViolation):
        runner_mod.run_arm("NOT-AN-ARM", tmp_path)
    with pytest.raises(ContractViolation):
        runner_mod.run_arm(ANCHOR_ARM, tmp_path, stress_tier="extreme")


def test_v15f2_scored_guard_is_driver_owned_not_in_family():
    """A1-ordered pre-score remediation: the family package records the
    ``scored`` flag verbatim and carries NO unconditional scored refusal;
    the guard lives at the driver (--publish/--expect-head + ledger chain).
    """
    from research.v15.families.taker_sat.frozen_identity import (
        SCORED_GUARD_REMEDIATION_NOTE,
    )

    assert SCORED_GUARD_REMEDIATION_NOTE == (
        "scored-guard remediation A1-ordered pre-score (driver-owned guard; "
        "V14-aligned); budget still 0/6"
    )
    for arm in ARM_IDS:
        config = frozen_identity(arm).config
        assert "run_arm(scored=...) records the flag verbatim" in config[
            "scored_flag_semantics"
        ]
        assert config["scored_guard_remediation"] == SCORED_GUARD_REMEDIATION_NOTE
        assert not hasattr(runner_mod, "ScoredExecutionForbidden"), (
            "the in-family unconditional scored refusal must stay removed"
        )
    staged_root = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "research/v15/families/taker_sat/staged_root.json"
        ).read_text()
    )
    assert staged_root["scored_guard_remediation"] == SCORED_GUARD_REMEDIATION_NOTE
