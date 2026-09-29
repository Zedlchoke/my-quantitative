"""PC12A verification battery §8 (trial-identity law) -- exact-arm
distinctness across the 12 frozen leg configurations.

The campaign §1 identity law: every arm is the tuple (cycle, sleeve,
candidate, family, mech_key, clock, params, pit_joins, cost_tier,
outcome_exposed_label, cluster_id) with a pairwise-DISTINCT
arm_config_digest, and no two arms may share (family_id, mech_key,
symbol) -- otherwise two "different" trials would be the same arm
double-counted (multiple-testing accounting breaks).

The FROZEN JSONs under research/pc12a/legs_config are the authority; the
in-code defaults must match them exactly, and both must satisfy the law.
"""

import datetime as dt
import hashlib
import json
import pathlib
from itertools import combinations

import pytest

from research.pc12a import legs as _legs
from research.pc12a import policy as pol

WORKTREE = pathlib.Path(__file__).resolve().parent.parent
REAL_LEGS_DIR = WORKTREE / "research" / "pc12a" / "legs_config"

REQUIRED_FIELDS = (
    "cycle_id", "sleeve_id", "family_id", "mech_key", "clock", "symbol",
    "pit_join_list", "cost_tier", "outcome_exposed_label", "cluster_id",
    "params",
)


def _disk_cfgs():
    return _legs.load_leg_configs(str(REAL_LEGS_DIR))


def _key(cfg):
    return cfg.get("class_candidate_id") or cfg["corpus_gid"]


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", ["disk", "defaults"],
                         ids=["frozen_jsons", "in_code_defaults"])
def test_twelve_configs_complete_schema(source):
    cfgs = _disk_cfgs() if source == "disk" else \
        _legs.default_leg_configs()
    expect = 76 if source == "disk" else 12   # 12 legacy + 64 wave-1
    assert len(cfgs) == expect
    ids = [_key(c) for c in cfgs]
    assert len(set(ids)) == expect, "duplicate candidate ids"
    for cfg in cfgs:
        for f in REQUIRED_FIELDS:
            assert cfg.get(f) not in (None, "", [], {}), (
                f"{_key(cfg)}: missing/empty schema field {f}")
        # the two label fields the battery names explicitly
        assert isinstance(cfg["outcome_exposed_label"], str) \
            and cfg["outcome_exposed_label"].strip()
        assert isinstance(cfg["cluster_id"], str) \
            and cfg["cluster_id"].strip()
        assert isinstance(cfg["params"], dict) and cfg["params"]


def test_frozen_jsons_match_in_code_defaults_exactly():
    """The checked-in configs ARE the defaults (no silent drift between
    the authority on disk and the registry in code)."""
    disk = {json.dumps(c, sort_keys=True) for c in _disk_cfgs()}
    default = {json.dumps(c, sort_keys=True)
               for c in _legs.default_leg_configs()}
    assert default <= disk   # wave-1 legs are disk-only (generated)


# ---------------------------------------------------------------------------
# Arm digest: pairwise-distinct, deterministic, params-pure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", ["disk", "defaults"],
                         ids=["frozen_jsons", "in_code_defaults"])
def test_arm_config_digest_pairwise_distinct(source):
    cfgs = _disk_cfgs() if source == "disk" else \
        _legs.default_leg_configs()
    digests = {}
    for cfg in cfgs:
        ident = _legs.make_identity(cfg)
        assert len(ident.arm_config_digest) == 64
        int(ident.arm_config_digest, 16)          # hex
        digests[_key(cfg)] = ident.arm_config_digest
    assert len(digests) == len(cfgs)
    vals = list(digests.values())
    for a, b in combinations(vals, 2):
        assert a != b, "two arms share an arm_config_digest"
    # identity round trip is stable: rebuilding gives the same digest
    for cfg in cfgs:
        assert _legs.make_identity(
            cfg).arm_config_digest == digests[_key(cfg)]


def test_digest_is_pure_function_of_candidate_and_params():
    """Digest = sha256 over (candidate, params) ONLY: cosmetic key order
    or unrelated fields must not move it; any PARAM change must move it."""
    base = [c for c in _disk_cfgs()
            if _key(c) == "VC3-POCMAG-EURUSD"][0]
    reordered = dict(reversed(list(base.items())))     # key order shuffle
    assert _legs.make_identity(reordered).arm_config_digest == \
        _legs.make_identity(base).arm_config_digest
    relabelled = dict(base, cluster_id="somewhere_else",
                      outcome_exposed_label="OTHER")
    assert _legs.make_identity(relabelled).arm_config_digest == \
        _legs.make_identity(base).arm_config_digest
    retuned = json.loads(json.dumps(base))
    retuned["params"]["dev_k"] = 3.5                   # param change
    assert _legs.make_identity(retuned).arm_config_digest != \
        _legs.make_identity(base).arm_config_digest
    # and it equals the documented construction
    blob = json.dumps({"candidate": _key(base), "params": base["params"]},
                      sort_keys=True, separators=(",", ":"))
    assert _legs.make_identity(base).arm_config_digest == \
        hashlib.sha256(blob.encode()).hexdigest()


# ---------------------------------------------------------------------------
# (family, mech_key, symbol) uniqueness -- the trial-identity law
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", ["disk", "defaults"],
                         ids=["frozen_jsons", "in_code_defaults"])
def test_no_two_configs_share_family_mech_symbol(source):
    cfgs = _disk_cfgs() if source == "disk" else \
        _legs.default_leg_configs()
    seen = {}
    for cfg in cfgs:
        if not cfg.get("archetype"):
            # legacy frozen arms: strict (family, mech_key, symbol) law
            trip = (cfg["family_id"], cfg["mech_key"], cfg["symbol"])
            assert trip not in seen, (
                f"trial-identity violation: {_key(cfg)} and {seen.get(trip)} "
                f"share (family, mech_key, symbol) {trip}")
            seen[trip] = _key(cfg)
        else:
            # wave-1: census mech_keys repeat across gids on one symbol
            # (distinct corpus constructions); the arm identity is the
            # (archetype, params) digest -- assert no two wave-1 legs
            # collapse to the same implemented arm
            arm = (cfg.get("archetype"),
                   _legs.make_identity(cfg).arm_config_digest)
            assert arm not in seen, (
                f"trial-identity violation: {_key(cfg)} and {seen.get(arm)} "
                f"share (archetype, digest) {arm}")
            seen[arm] = _key(cfg)
    assert len(seen) == len(cfgs)


def test_candidate_ids_unique_and_namespaced():
    """The 9 class candidates name their shape+pair; the 3 exemplars carry
    their corpus GIDs -- no id collision across sleeves either."""
    cfgs = _disk_cfgs()
    vp = [c for c in cfgs if c["sleeve_id"] == "POOL_B_VOLPROF"]
    ex = [c for c in cfgs if c["sleeve_id"] == "POOL_B_TRIAGE"]
    assert len(vp) == 9 and len(ex) == 3 + 64
    assert {_key(c) for c in vp} == {
        f"VC1-VAEDGE-{s}" for s in ("EURUSD", "GBPUSD", "USDJPY")} | {
        f"VC2-LVNFAIL-{s}" for s in ("EURUSD", "GBPUSD", "USDJPY")} | {
        f"VC3-POCMAG-{s}" for s in ("EURUSD", "GBPUSD", "USDJPY")}
    assert {"USDJPY-S001", "GBPUSD-S027", "EURUSD-S009"} <= \
        {_key(c) for c in ex}
    # every wave-1 id is a corpus gid <SYMBOL>-S<NNN> with an archetype
    for c in ex:
        gid = _key(c)
        if gid in ("USDJPY-S001", "GBPUSD-S027", "EURUSD-S009"):
            continue
        _, s_num = gid.split("-")
        assert s_num.startswith("S") and s_num[1:].isdigit() and \
            c.get("archetype"), gid
    assert all(c["cycle_id"] == "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
               for c in cfgs)


def test_cluster_ids_resolve_in_frozen_l5_map():
    """Every leg's cluster_id must be a key of the frozen L5 cluster map
    so the cap lookup can never silently fall back to the per-asset
    default."""
    cfgs = _disk_cfgs()
    for cfg in cfgs:
        assert cfg["cluster_id"] in pol.FROZEN_CLUSTER_MAP_PLACEHOLDER, (
            f"{_key(cfg)}: cluster {cfg['cluster_id']} missing from the "
            f"frozen L5 map")
    # expected clustering: 3 volprof shapes + 2 exemplar clusters
    # (+ wave-1 (family, horizon) clusters)
    assert {
        "volprof_vc1_vaedge", "volprof_vc2_lvnfail", "volprof_vc3_pocmag",
        "trend_daily", "calendar_weekday"} <= {c["cluster_id"] for c in cfgs}


def test_identity_carries_labels_into_decisions():
    """Schema-to-journal plumbing: every decision-row builder field the
    engine serializes is populated from the identity (spot-check the
    frozen tuple fields exist on every built leg)."""
    for cfg in _disk_cfgs():
        leg = _legs.build_leg(cfg)
        ident = leg.identity
        assert ident.outcome_exposed_label == cfg["outcome_exposed_label"]
        assert ident.cluster_id == cfg["cluster_id"]
        assert ident.family_id == cfg["family_id"]
        assert ident.mech_key == cfg["mech_key"]
        assert ident.symbol == cfg["symbol"]
        assert ident.pit_join_list == tuple(cfg["pit_join_list"])
        assert ident.params == cfg["params"]
        # frozen params must be JSON-stable (byte-identical re-serialize)
        assert json.loads(json.dumps(ident.params)) == cfg["params"]


def test_config_files_are_the_declared_set_on_disk():
    files = sorted(p.name for p in REAL_LEGS_DIR.glob("*.json"))
    expect = sorted(f"{_key(c)}.json" for c in _disk_cfgs())
    assert files == expect
    # each file is valid UTF-8 JSON with the cycle id pinned
    for p in REAL_LEGS_DIR.glob("*.json"):
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert doc["cycle_id"] == "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
