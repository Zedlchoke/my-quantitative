"""Identity pinning: adapters must equal the identity manifest verbatim.

Reads research/control/prospective_shadow_v1/identity/identity_recovery.json
(the sole identity authority) and, for every adapter:
- asserts the pinned class constants equal the manifest values verbatim
  (family ids, historical family ids, verdict labels, anchor arm ids);
- asserts the frozen config derivation reproduces the manifest's
  score-affecting numbers (windows, caps, weight bounds, universe);
- asserts adapters REFUSE to start with a config that disagrees with
  the manifest (validate raises IdentityConfigError);
- asserts missing required engine parameters fail closed.
"""

import copy
import json
from pathlib import Path

import pytest

from research.shadow_v1 import scheduler
from research.shadow_v1.families import (
    FAMILY_REGISTRY,
    BasislvPremfadeAdapter,
    IlliqAmihudAdapter,
    IdentityConfigError,
    XsectFundCarryAdapter,
)

WORKTREE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    WORKTREE_ROOT
    / "research"
    / "control"
    / "prospective_shadow_v1"
    / "identity"
    / "identity_recovery.json"
)

ILLIQ_ENGINE = {
    "min_listing_age_days": 7.0,
    "min_daily_dollar_volume": 1_000.0,
    "btc_beta_tolerance": 1e-6,
    "hard_gross_cap": 1.0,
    "hard_abs_net_cap": 0.0,
}

ALL_ADAPTERS = (IlliqAmihudAdapter, BasislvPremfadeAdapter, XsectFundCarryAdapter)


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text())


def manifest_entry(cls):
    family_id = cls.MANIFEST_FAMILY_ID
    for entry in load_manifest()["families"]:
        if entry["family_id"] == family_id:
            return entry
    raise AssertionError(f"family {family_id} not found in identity manifest")


def build(cls, entry, engine=None):
    config = cls.build_config(entry, engine or {})
    return cls(config, entry)


# ----------------------------------------------------------------------
# verdict labels are not rewritable
# ----------------------------------------------------------------------
def test_historical_verdict_labels_match_manifest_verbatim():
    expected = {
        IlliqAmihudAdapter: "V11_FAMILY_REJECT",
        BasislvPremfadeAdapter: "V14_FAMILY_REJECT",
        XsectFundCarryAdapter: "CANDIDATE_FAIL",
    }
    for cls, label in expected.items():
        entry = manifest_entry(cls)
        assert cls.HISTORICAL_VERDICT_LABEL == label
        assert entry["historical_verdict_label"] == label


def test_all_three_labels_are_the_frozen_set():
    labels = {cls.HISTORICAL_VERDICT_LABEL for cls in ALL_ADAPTERS}
    assert labels == {"V11_FAMILY_REJECT", "V14_FAMILY_REJECT", "CANDIDATE_FAIL"}


# ----------------------------------------------------------------------
# pinned identity strings per adapter
# ----------------------------------------------------------------------
def test_illiq_identity_constants_match_manifest():
    entry = manifest_entry(IlliqAmihudAdapter)
    params = entry["score_affecting_parameters"]
    assert IlliqAmihudAdapter.FAMILY_ID == entry["family_id"] == "ILLIQ-AMIHUD-28D-W"
    assert (
        IlliqAmihudAdapter.HISTORICAL_FAMILY_ID
        == entry["historical_family_id"]
        == "A8-V11-ILLIQ-AMIHUD"
    )
    assert IlliqAmihudAdapter.ARM_ID == params["anchor_arm_id"]
    assert IlliqAmihudAdapter.DECISION_CLOCK == "WEEKLY_MONDAY_00Z"
    assert "Mondays 00:00:00Z" in params["decision_clock"]


def test_premfade_identity_constants_match_manifest():
    entry = manifest_entry(BasislvPremfadeAdapter)
    params = entry["score_affecting_parameters"]
    assert (
        BasislvPremfadeAdapter.FAMILY_ID == entry["family_id"] == "BASISLV-PREMFADE-28D"
    )
    assert (
        BasislvPremfadeAdapter.HISTORICAL_FAMILY_ID
        == entry["historical_family_id"]
        == "A14-V14-A5-BASISLV-PREMFADE"
    )
    assert BasislvPremfadeAdapter.ARM_ID == params["anchor_arm_id"] == "BASISLV-PREMFADE-28D"
    assert BasislvPremfadeAdapter.DECISION_CLOCK == "WEEKLY_MONDAY_00Z"


def test_carry_identity_constants_match_manifest():
    entry = manifest_entry(XsectFundCarryAdapter)
    params = entry["score_affecting_parameters"]
    assert XsectFundCarryAdapter.FAMILY_ID == entry["family_id"] == "XSECT-FUND-CARRY-7D"
    assert (
        XsectFundCarryAdapter.HISTORICAL_FAMILY_ID
        == entry["historical_family_id"]
        == "H-XSECT-FUNDING-CARRY-v1"
    )
    assert XsectFundCarryAdapter.ARM_ID == "XSECT-FUND-CARRY-7D"
    assert params["anchor_variant_recovered"].startswith("XSECT-FUND-CARRY-7D")
    assert XsectFundCarryAdapter.DECISION_CLOCK == "DAILY_00Z"


def test_registry_covers_exactly_the_scheduled_families():
    assert sorted(FAMILY_REGISTRY) == sorted(scheduler.FAMILY_SCHEDULES)
    assert (
        scheduler.FAMILY_SCHEDULES[IlliqAmihudAdapter.FAMILY_ID]
        == scheduler.FAMILY_SCHEDULES[BasislvPremfadeAdapter.FAMILY_ID]
        == scheduler.SCHEDULE_WEEKLY_MONDAY_0000Z
    )
    assert (
        scheduler.FAMILY_SCHEDULES[XsectFundCarryAdapter.FAMILY_ID]
        == scheduler.SCHEDULE_DAILY_0000Z
    )


# ----------------------------------------------------------------------
# frozen config derivation equals manifest numbers
# ----------------------------------------------------------------------
def test_illiq_frozen_windows_match_manifest():
    entry = manifest_entry(IlliqAmihudAdapter)
    params = entry["score_affecting_parameters"]
    frozen = IlliqAmihudAdapter.build_frozen(params)
    assert frozen["formation_days"] == params["formation_days"] == 28
    assert frozen["holding_days"] == params["holding_days"] == 7
    assert frozen["quintiles"] == 5
    assert frozen["expected_staged_universe_size"] == 20
    assert frozen["book_rule_verbatim"] == params["book"]
    assert frozen["universe_rule_verbatim"] == params["universe"]
    assert frozen["decision_clock_verbatim"] == params["decision_clock"]
    # counterfactual arms are reserved, never built
    assert frozen["neighbour_arm_id_reserved"] == "ILLIQ-AMIHUD-56D-W"
    assert frozen["control_arm_id_reserved"] == "ILLIQ-AMIHUD-28D-W-INV"
    assert frozen["dollar_neutral"] is True
    assert frozen["btc_beta_neutral"] is True
    assert frozen["gross_by_construction"] == 1.0


def test_premfade_frozen_caps_and_bounds_match_manifest():
    entry = manifest_entry(BasislvPremfadeAdapter)
    params = entry["score_affecting_parameters"]
    frozen = BasislvPremfadeAdapter.build_frozen(params)
    assert frozen["formation_buckets"] == params["anchor_formation_buckets"] == 2688
    assert frozen["formation_days"] == params["anchor_formation_days"] == 28
    assert frozen["min_eligible"] == params["min_eligible"] == 12
    assert frozen["gross"] == params["gross"] == 1.0
    assert frozen["designed_max_abs_weight"] == params["designed_max_abs_weight"] == 0.125
    assert frozen["adapter_weight_cap_max"] == params["adapter_weight_cap_max"] == 0.3
    assert frozen["tier_divisor"] == 3
    assert frozen["holding_days"] == params["holding_days"] == 7
    assert frozen["benchmark_symbols_excluded"] == ["BTCUSDT"]
    assert frozen["tie_break"] == params["tie_break"] == "symbol_id_ascending_on_equal_b_i"
    assert frozen["side_rule_verbatim"] == params["side_rule"]
    assert frozen["fill_rule_verbatim"] == params["fill_rule"]
    assert frozen["anchor_arm_config_id"] == params["anchor_arm_config_id"] == "28D-PREMIUM-LEVEL"


def test_carry_frozen_universe_and_caps_match_manifest():
    entry = manifest_entry(XsectFundCarryAdapter)
    params = entry["score_affecting_parameters"]
    frozen = XsectFundCarryAdapter.build_frozen(params)
    assert frozen["traded_universe"] == [
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "DOGEUSDT",
        "LINKUSDT",
        "ADAUSDT",
    ]
    assert frozen["benchmark_context"] == "BTCUSDT"
    assert frozen["signal_clock"] == "daily_00_00_utc"
    assert frozen["lookback_days_options"] == [1, 3, 7]
    assert frozen["anchor_lookback_days"] == 7
    assert frozen["long_side_count"] == 2
    assert frozen["short_side_count"] == 2
    assert frozen["rebalance_hours"] == 24.0
    assert frozen["target_gross"] == 0.8
    assert frozen["hard_gross_cap"] == 1.0
    assert frozen["hard_abs_net_cap"] == 0.1
    assert frozen["max_abs_weight_per_symbol"] == 0.2
    assert frozen["purge_embargo_hours"] == 24.0
    assert frozen["negative_control_reserved"] == "reverse_funding_rank_3d"


# ----------------------------------------------------------------------
# adapters refuse configs that disagree with the manifest
# ----------------------------------------------------------------------
def test_adapters_start_with_manifest_derived_config():
    for cls in ALL_ADAPTERS:
        entry = manifest_entry(cls)
        engine = ILLIQ_ENGINE if cls is IlliqAmihudAdapter else {}
        adapter = build(cls, entry, engine)
        assert adapter.config["frozen"] == cls.build_frozen(entry["score_affecting_parameters"])


def test_adapters_refuse_tampered_frozen_config():
    for cls in ALL_ADAPTERS:
        entry = manifest_entry(cls)
        engine = ILLIQ_ENGINE if cls is IlliqAmihudAdapter else {}
        config = cls.build_config(entry, engine)
        key = next(iter(config["frozen"]))
        config["frozen"][key] = "TAMPERED"
        with pytest.raises(IdentityConfigError):
            cls(config, entry)


def test_adapters_refuse_entry_disagreeing_with_manifest():
    for cls, tamper_key, tamper_value in (
        (IlliqAmihudAdapter, "formation_days", 56),
        (BasislvPremfadeAdapter, "min_eligible", 10),
        (XsectFundCarryAdapter, "target_gross: 0.99", None),
    ):
        entry = manifest_entry(cls)
        engine = ILLIQ_ENGINE if cls is IlliqAmihudAdapter else {}
        config = cls.build_config(entry, engine)
        tampered = copy.deepcopy(entry)
        if tamper_value is None:
            # replace a verbatim YAML line with a disagreeing one
            real_key = next(
                k for k in tampered["score_affecting_parameters"] if k == "target_gross"
            )
            tampered["score_affecting_parameters"][real_key] = tamper_key
        else:
            target = next(
                k
                for k in tampered["score_affecting_parameters"]
                if k.endswith(tamper_key) or k == tamper_key
            )
            tampered["score_affecting_parameters"][target] = tamper_value
        with pytest.raises(IdentityConfigError):
            cls(config, tampered)


def test_adapters_refuse_tampered_verdict_label():
    for cls in ALL_ADAPTERS:
        entry = manifest_entry(cls)
        engine = ILLIQ_ENGINE if cls is IlliqAmihudAdapter else {}
        config = cls.build_config(entry, engine)
        tampered = copy.deepcopy(entry)
        tampered["historical_verdict_label"] = "NOT_THE_HISTORICAL_LABEL"
        with pytest.raises(IdentityConfigError):
            cls(config, tampered)


def test_adapters_refuse_missing_engine_parameters():
    entry = manifest_entry(IlliqAmihudAdapter)
    config = IlliqAmihudAdapter.build_config(entry, {})
    config["engine"] = {}
    with pytest.raises(IdentityConfigError):
        IlliqAmihudAdapter(config, entry)


def test_build_config_requires_score_affecting_parameters():
    for cls in ALL_ADAPTERS:
        with pytest.raises(IdentityConfigError):
            cls.build_config({"family_id": cls.FAMILY_ID}, {})


def test_from_identity_manifest_constructs_all_three():
    manifest = load_manifest()
    illiq = IlliqAmihudAdapter.from_identity_manifest(manifest, ILLIQ_ENGINE)
    premfade = BasislvPremfadeAdapter.from_identity_manifest(manifest)
    carry = XsectFundCarryAdapter.from_identity_manifest(manifest)
    assert illiq.FAMILY_ID == "ILLIQ-AMIHUD-28D-W"
    assert premfade.FAMILY_ID == "BASISLV-PREMFADE-28D"
    assert carry.FAMILY_ID == "XSECT-FUND-CARRY-7D"
    with pytest.raises(IdentityConfigError):
        IlliqAmihudAdapter.from_identity_manifest({"families": []}, ILLIQ_ENGINE)
