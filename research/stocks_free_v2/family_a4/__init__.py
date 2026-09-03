"""Frozen family ``A4_XSEC_ETF_RELATIVE_MOMENTUM`` (Z5 lane, producer A6).

Schedule-only implementation of the three preregistered arms of the frozen
spec ``research/proposals/stocks_free_v2/a4_z3_relative_momentum_spec.json``:

- ``ARM_A4_ANCHOR_MOM121_EQW_TOP3`` (ANCHOR): 12-1 TR momentum, top-3
  equal-weight;
- ``ARM_A4_NEIGHBOR_VOLADJ_MOM121_INVVOL_TOP3`` (NEIGHBOUR): momentum /
  formation-window realized vol ranking, top-3, inverse-vol weights with the
  frozen 35% per-ETF cap;
- ``ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121`` (CAUSAL NEGATIVE CONTROL): the
  anchor with the ranking sign REVERSED (bottom-3), nothing else.

One shared code path (features -> rank -> weight -> book) is parameterized
by the arm config; every numeric constant is extracted fail-closed from the
frozen spec.  Output is decision/target books + a schedule summary only:
this family module never computes returns, PnL, PF or any scored metric.
"""

from .portfolio import (
    SERIALIZATION_DP,
    BookEntry,
    TargetBookStream,
    normalize_capped,
    turnover_one_way,
    weight_book,
)
from .schedule import (
    DecisionSlot,
    FamilyInputs,
    PartitionSpec,
    build_decision_slots,
    force_flat_events,
    fold_id_for_date,
    generate_target_book,
)
from .signals import (
    ARM_ID_ANCHOR,
    ARM_ID_NEGCTRL,
    ARM_ID_NEIGHBOUR,
    ARM_IDS,
    FROZEN_SPEC_FILE_SHA256,
    FROZEN_SPEC_REL_PATH,
    FAMILY_ID,
    ArmConfig,
    SpecConstants,
    SymbolFeatures,
    arm_config_digest,
    build_arm_configs,
    canonical_json,
    compute_symbol_features,
    control_differs_only_in_ranking_sign,
    load_frozen_spec,
    parse_force_flat_dates,
    parse_spec_constants,
    rank_select,
    score_of,
    spec_file_sha256,
)

__all__ = [
    "ARM_ID_ANCHOR",
    "ARM_ID_NEGCTRL",
    "ARM_ID_NEIGHBOUR",
    "ARM_IDS",
    "ArmConfig",
    "BookEntry",
    "DecisionSlot",
    "FAMILY_ID",
    "FamilyInputs",
    "FROZEN_SPEC_FILE_SHA256",
    "FROZEN_SPEC_REL_PATH",
    "PartitionSpec",
    "SERIALIZATION_DP",
    "SpecConstants",
    "SymbolFeatures",
    "TargetBookStream",
    "arm_config_digest",
    "build_arm_configs",
    "build_decision_slots",
    "canonical_json",
    "compute_symbol_features",
    "control_differs_only_in_ranking_sign",
    "force_flat_events",
    "fold_id_for_date",
    "generate_target_book",
    "load_frozen_spec",
    "normalize_capped",
    "parse_force_flat_dates",
    "parse_spec_constants",
    "rank_select",
    "score_of",
    "spec_file_sha256",
    "turnover_one_way",
    "weight_book",
]
