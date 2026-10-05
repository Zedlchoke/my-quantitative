"""frozen_refs.py — PIPE lane recorder, cycle NFL-WINPROB-NG-SCORED-V1.

Read-only references to the FROZEN code and the freeze constants. Nothing here
modifies any frozen file. Every frozen import is sha256-checked against the
freeze pins at load (loud drift = stop).

Frozen inputs (never edited by this lane):
  - lanes/T_SELECT/arms.py            sha256 19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8
      (FREEZE_PACKET.md §9; imported for kickoff_utc, lineage, LINEAGE_MAP/ALL,
       GameSet, batches, replay_elo, z_standardize, sig/elo_expected/elo_update/
       season_revert — the as-frozen state-carry machinery)
  - research/control/NFL-WINPROB-NG-SCORED-V1/ledger/nfl_ng_ledger.py
      sha256 6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c
      (byte-identical port of nfl_ng_ledger@1; FREEZE_PACKET.md §5)

Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[4]  # .../integration
FROZEN_ARMS_PATH = WORKTREE / "lanes" / "T_SELECT" / "arms.py"
LEDGER_TOOL_PATH = (
    WORKTREE / "research" / "control" / "NFL-WINPROB-NG-SCORED-V1" / "ledger" / "nfl_ng_ledger.py"
)

# ---------------------------------------------------------------------------
# Freeze pins (FREEZE_PACKET.md §1/§5/§9, freeze_digests.json)
# ---------------------------------------------------------------------------
FROZEN_ARMS_SHA256 = "19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8"
LEDGER_TOOL_SHA256 = "6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c"
CODE_FREEZE_SHA = "7ec4c539394e68538f74df327d85fa2a477c6eb7"  # CODE_FREEZE_ADDENDUM.md
FREEZE_GENESIS_DIGEST_R1 = (
    "ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7"
)
FREEZE_PACKET_SHA256 = "9978a950cfa52f531c6cc1ccf650ca46cfcecb5a0d38c8468f6a66381ef70f6e"

FIELDED_ARMS = ("B0", "B1_STAR", "C3")  # FREEZE_PACKET.md §1 (registry order: sorted)
DIAGNOSTIC_ARM = "C3_TWIN"  # report-only, never fielded, never appended

# Frozen arm constants (B1*: K=40, HCA=0, gamma=2/3, mu=1500; C3: theta=50, C3_T050)
B1STAR_K = 40.0
B1STAR_HCA = 0.0
B1STAR_GAMMA = 2.0 / 3.0
B1STAR_MU = 1500.0
C3_THETA = 50.0
B0_P_HOME_FROZEN = "0.571399049390"   # 12-dp frozen form (FREEZE_PACKET.md §1)
B0_P_HOME_LEDGER = "0.571399"          # same value at the ledger R6 6-dp precision
MARGIN_HOURS = 6.0                     # FREEZE_PACKET.md §4 capture rule

# Canonical arm-config strings VERBATIM from FREEZE_PACKET.md §1.1 (schema
# nfl_ng_scored_v1_arm_config@1; sorted keys, separators , and :, no whitespace,
# ensure_ascii=false). Embedded read-only so the recorder can re-verify the
# digest equality law (arm params are frozen constants, never re-typed here).
ARM_CONFIG_CANONICAL = {
    "B0": '{"arm_id":"B0","arm_schema":"nfl_ng_scored_v1_arm_config@1","cycle_id":"NFL-WINPROB-NG-SCORED-V1","p_home":"0.571399049390","p_home_derivation":"2765_home_wins_of_4839_non_tie_REG_rows_TRAIN_2000_2018","selection_status":"exempt_intercept_only","slot":1,"spec_type":"constant"}',
    "B1_STAR": '{"arm_id":"B1_STAR","arm_schema":"nfl_ng_scored_v1_arm_config@1","cycle_id":"NFL-WINPROB-NG-SCORED-V1","frozen_from":"NFL-WINPROB-SCORED-V1","gamma":"2/3","hca":0,"k":40,"mu":1500,"selection_status":"exempt_baseline_law","slot":2,"spec_type":"own_elo","tie_update":"S_0.5"}',
    "C3": '{"arm_id":"C3","arm_schema":"nfl_ng_scored_v1_arm_config@1","config_id":"C3_T050","cycle_id":"NFL-WINPROB-NG-SCORED-V1","gamma":"2/3","hca":0,"k":40,"mu":1500,"pit_class":"PASS_PIT_SEASON_GRAIN","prior_entries":574,"prior_formula":"0.5*(off_EPA_per_play+def_EPA_per_play_allowed)","prior_pbp_seasons":"2000_2017","prior_role":"offseason_only_train_only","prior_source":"nflverse_pbp_frozen_snapshot","season_start_rule":"R_i=1500+gamma*(R_i-1500)+theta*z_i","selection_status":"selected_C3_T050","slot":5,"spec_type":"own_elo_plus_offseason_epa_prior","theta":50.0,"z_boundaries":"2001_2018","z_standardization":"(E-mean)/sd_across_32_lineages"}',
    "C3_TWIN": '{"arm_id":"C3_TWIN","arm_schema":"nfl_ng_scored_v1_arm_config@1","budget_arm":false,"control_name":"time_shuffled_epa_prior_twin","cycle_id":"NFL-WINPROB-NG-SCORED-V1","parent_arm":"C3","parent_config_id":"C3_T050","role":"diagnostic_negative_control","seed":20261005,"shuffle_rule":"shuffle_z_across_lineages_at_each_season_boundary_preserving_marginals","slot":"diagnostic","theta":50.0}',
}
ARM_CONFIG_DIGESTS = {
    "B0": "bea17ae49a33e460912aa9bdf9c0266da22d81c5168e4490e35194e49a2154aa",
    "B1_STAR": "5c97475c5df745056429e3eb075386e9b4f85729dbb9722eaf409f4b7fcbf32a",
    "C3": "f7cde49880ee1f413f740c97a45ae4b863c017bf148326e116a7058126ecc74e",
    "C3_TWIN": "c86b3710ba1621adc879ad83222457969a395b810554241234cdf4c237036361",
}

# ---------------------------------------------------------------------------
# Versioned schedule snapshot pin (FREEZE_PACKET.md §3; registration-time freeze)
# ---------------------------------------------------------------------------
SCHEDULE_SNAPSHOT_PATH = Path.home() / ".my-quantitative-data" / "nfl-ng-scored-v1" / "raw_schedules_fresh" / "games.csv"
SCHEDULE_SNAPSHOT_SHA256 = "486d72273c0d9650756176fc016a0852c65ad6f030f443805c20cb35e387a9fc"
SCHEDULE_SNAPSHOT_BYTES = 2182513
SCHEDULE_RELEASE_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
)

# pbp state-carry input locations (2000-2017 pinned by A_DATA manifest; 2018-2020
# downloaded by this lane; 2021-2025 predecessor archive, read-only)
PBP_DIR_2000_2017 = Path.home() / ".my-quantitative-data" / "nfl-ng-scored-v1" / "raw_pbp_2000_2017"
PBP_DIR_2018_2020 = Path.home() / ".my-quantitative-data" / "nfl-ng-scored-v1" / "raw_pbp_2018_2020"
PBP_DIR_2021_2025 = Path.home() / ".my-quantitative-data" / "nfl-nflverse-v1" / "raw"
PBP_DIRS_REAL = (PBP_DIR_2000_2017, PBP_DIR_2018_2020, PBP_DIR_2021_2025)

# pbp 2018-2020 pins (downloaded by lane PIPE 2026-10-05T11:58Z; raw_pbp_2018_2020/DOWNLOAD_MANIFEST.json)
PBP_2018_2020_SHA256 = {
    2018: "2e6f2dce7c7ebd46e985cabe0c17eb72b39a77f98cb4478409294f50b5820150",
    2019: "60c3067017db2d28a78f66a79b657268be8578d9a5288e6a827efdcd7fe42540",
    2020: "8889f5d8782b5c5dce3c3644acdc0322b228a7e9cb13fa36cbac250e260e9f60",
}
PBP_2021_2025_SHA256 = {
    2021: "333ad34378e5339d5172717cc83378e908daf02c8699416ab3e17c2ec10f78d8",
    2022: "931121d8897779d7944e2a293e92ed8799c8e5cceef84096ac42339003fedc09",
    2023: "bd3484731408def6b0ec93225bba2bd7b2c65769ca707a2b9444d891abdc6776",
    2024: "3fd2896bc0b911b615142d2f1fabae54a4bbba5ab7b73b28187b118ef8af6a3b",
    2025: "c6ecedd6d678cc37ed316b23ef84ee1ec6abb69c514bb11868a7ebd5a367df29",
}
PBP_2000_2017_MANIFEST_TSV = (
    Path.home() / ".my-quantitative-data" / "nfl-ng-scored-v1" / "provenance" / "pbp_download_log.tsv"
)
LICENSE_SHA256_PIN = "2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111"


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_arm_config_digests() -> dict:
    """Arm-param equality law: recompute each frozen arm-config digest from the
    §1.1 canonical strings and compare with the freeze pins. Any mismatch is a
    STOP (the params the recorder would consume are not the frozen params)."""
    out = {}
    for arm, canon in ARM_CONFIG_CANONICAL.items():
        got = sha256_text(canon)
        if got != ARM_CONFIG_DIGESTS[arm]:
            raise RuntimeError(
                f"arm-config digest mismatch for {arm}: recomputed {got} != freeze "
                f"{ARM_CONFIG_DIGESTS[arm]} — frozen params drifted; STOP"
            )
        out[arm] = got
    return out


def load_frozen_arms():
    """Import lanes/T_SELECT/arms.py read-only, asserting the freeze-packet §9
    sha256 first. Returns the module (functions used as-frozen)."""
    got = sha256_file(FROZEN_ARMS_PATH)
    if got != FROZEN_ARMS_SHA256:
        raise RuntimeError(
            f"frozen arms.py drifted: sha256 {got} != {FROZEN_ARMS_SHA256}; STOP"
        )
    spec = importlib.util.spec_from_file_location("recorder_frozen_arms", FROZEN_ARMS_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["recorder_frozen_arms"] = mod  # dataclass resolution needs sys.modules
    spec.loader.exec_module(mod)
    # arm-constant equality law: the module's machinery constants must equal the
    # frozen B1* params (K=40, HCA=0 via absence of any hca term, gamma=2/3, mu=1500).
    assert float(mod.K_BASE) == B1STAR_K, "K_BASE != 40.0"
    assert float(mod.GAMMA) == B1STAR_GAMMA, "GAMMA != 2/3"
    assert float(mod.ELO_INIT) == B1STAR_MU, "ELO_INIT != 1500.0"
    assert mod.LINEAGE_MAP == {"SD": "LAC", "STL": "LA", "OAK": "LV"}, "lineage map drifted"
    return mod


def load_ledger_tool():
    """Import the ported nfl_ng_ledger@1 tool read-only, asserting its pinned
    sha256 (byte-identical port of the predecessor; FREEZE_PACKET.md §5)."""
    got = sha256_file(LEDGER_TOOL_PATH)
    if got != LEDGER_TOOL_SHA256:
        raise RuntimeError(
            f"ported ledger tool drifted: sha256 {got} != {LEDGER_TOOL_SHA256}; STOP"
        )
    spec = importlib.util.spec_from_file_location("recorder_ledger_tool", LEDGER_TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["recorder_ledger_tool"] = mod
    spec.loader.exec_module(mod)
    return mod
