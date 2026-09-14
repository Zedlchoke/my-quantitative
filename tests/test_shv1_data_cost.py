"""Tests for PROSPECTIVE-SHADOW-V1 P2 data/cost freeze (shv1-p2-data-cost-freeze).

Contract under test:
- data_manifest.json and cost_regime_manifest.json exist and are internally
  consistent with the archived raw bytes they cite (sha256 recomputed here).
- every family carries universe + PIT + warmup coverage evidence.
- the family-3 forward-warmup condition is present and binding.
- cost_regime_digest recomputes from the CURRENT_CONSERVATIVE_COST block.
- missing files, and UNAVAILABLE_FAIL_CLOSED markers hidden inside
  authorized-source (measured) blocks, fail loudly. Unavailable evidence must
  be surfaced via its own UNAVAILABLE evidence_class, never smuggled into a
  measured block.
"""
import hashlib
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DC_DIR = os.path.join(
    REPO_ROOT, "research", "control", "prospective_shadow_v1", "data_cost"
)
RAW_DIR = os.path.join(DC_DIR, "raw")
DATA_MANIFEST_PATH = os.path.join(DC_DIR, "data_manifest.json")
COST_MANIFEST_PATH = os.path.join(DC_DIR, "cost_regime_manifest.json")

MEASURED_PREFIX = "MEASURED"
UNAVAILABLE_MARKER = "UNAVAILABLE_FAIL_CLOSED"


def _load(path):
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def data_manifest():
    assert os.path.isfile(DATA_MANIFEST_PATH), (
        f"MISSING required deliverable: {DATA_MANIFEST_PATH}"
    )
    return _load(DATA_MANIFEST_PATH)


@pytest.fixture(scope="module")
def cost_manifest():
    assert os.path.isfile(COST_MANIFEST_PATH), (
        f"MISSING required deliverable: {COST_MANIFEST_PATH}"
    )
    return _load(COST_MANIFEST_PATH)


# --------------------------------------------------------------------------
# archived raw bytes integrity
# --------------------------------------------------------------------------

def _iter_cited_fetches(node, out):
    """Collect every dict that looks like an archived-fetch citation."""
    if isinstance(node, dict):
        if (
            isinstance(node.get("sha256"), str)
            and isinstance(node.get("file"), str)
            and "url" in node
        ):
            out.append(node)
        for v in node.values():
            _iter_cited_fetches(v, out)
    elif isinstance(node, list):
        for v in node:
            _iter_cited_fetches(v, out)


def test_every_cited_raw_file_exists_with_matching_sha256(data_manifest, cost_manifest):
    cited = []
    for manifest in (data_manifest, cost_manifest):
        _iter_cited_fetches(manifest, cited)
    assert len(cited) >= 20, (
        f"expected a substantial archive of measured fetches, found {len(cited)}"
    )
    problems = []
    for ref in cited:
        rel = ref["file"]
        assert rel.startswith("raw/"), f"cited file escapes raw/: {rel}"
        path = os.path.join(DC_DIR, rel)
        if not os.path.isfile(path):
            problems.append(f"MISSING file cited by manifest: {rel}")
            continue
        actual = _sha256_file(path)
        if actual != ref["sha256"]:
            problems.append(
                f"SHA256 MISMATCH for {rel}: manifest={ref['sha256']} actual={actual}"
            )
    assert not problems, (
        "archived-byte integrity failures (loud, never hidden):\n"
        + "\n".join(problems)
    )


def test_fetch_index_matches_files_on_disk():
    idx_path = os.path.join(RAW_DIR, "_fetch_index.json")
    assert os.path.isfile(idx_path), f"MISSING fetch index: {idx_path}"
    idx = _load(idx_path)
    assert idx["no_credentials_used"] is True
    assert idx["all_keyless_public_gets"] is True
    problems = []
    for rec in idx["fetches"]:
        path = os.path.join(RAW_DIR, rec["path"])
        if not os.path.isfile(path):
            problems.append(f"MISSING indexed file: {rec['path']}")
            continue
        if _sha256_file(path) != rec["sha256"]:
            problems.append(f"SHA256 MISMATCH for indexed file: {rec['path']}")
    assert not problems, "\n".join(problems)


def test_fetch_urls_are_keyless_public_https():
    idx = _load(os.path.join(RAW_DIR, "_fetch_index.json"))
    forbidden_fragments = (
        "apiKey", "api_key", "API_KEY", "signature=", "X-MBX-APIKEY",
        "recvWindow", "testnet", "Bearer", "token=",
    )
    for rec in idx["fetches"]:
        url = rec["url"]
        assert url.startswith("https://"), f"non-https fetch: {url}"
        for frag in forbidden_fragments:
            assert frag not in url, f"keyed/signed-looking fetch forbidden: {url}"
    assert data_access_class_is_internal_paper()


def data_access_class_is_internal_paper():
    dm = _load(DATA_MANIFEST_PATH)
    return dm["access_class"] == "INTERNAL_PAPER_ONLY_KEYLESS_PUBLIC_GETS" and (
        dm["no_api_key_no_account_no_orders"] is True
    )


# --------------------------------------------------------------------------
# per-family completeness
# --------------------------------------------------------------------------

EXPECTED_FAMILIES = {
    "ILLIQ-AMIHUD-28D-W": "sleeve_illiq_amihud",
    "BASISLV-PREMFADE-28D": "sleeve_basislv_premfade",
    "XSECT-FUND-CARRY-7D": "sleeve_xsect_fund_carry",
}


def test_every_family_has_universe_pit_warmup_endpoints(data_manifest):
    fams = {f["family_id"]: f for f in data_manifest["families"]}
    assert set(fams) == set(EXPECTED_FAMILIES), (
        f"family set drift: {sorted(fams)} vs {sorted(EXPECTED_FAMILIES)}"
    )
    for family_id, sleeve in EXPECTED_FAMILIES.items():
        fam = fams[family_id]
        # identity lineage
        assert fam["sleeve"] == sleeve
        assert fam["historical_family_id"]
        # universe block
        uni = fam["universe"]
        assert uni.get("identity_manifest_verbatim") or uni.get(
            "identity_manifest_verbatim_traded_universe"
        ), f"{family_id}: universe must quote the identity manifest verbatim"
        assert "enumeration_status" in uni
        # data requirements
        assert fam["data_requirements"]["forward_spec"]
        # endpoints with measured bytes
        assert fam["endpoints"], f"{family_id}: no endpoints recorded"
        for ep in fam["endpoints"]:
            assert ep["keyless"] is True, f"{family_id}: endpoint not keyless"
            assert ep["evidence_class"].startswith(MEASURED_PREFIX), (
                f"{family_id}: endpoint {ep['name']} lacks measured evidence"
            )
            assert ep["archived_fetches"], (
                f"{family_id}: endpoint {ep['name']} has no archived fetches"
            )
        # PIT rule
        pit = fam["pit_rule"]
        assert "decision_clock" in pit
        assert "STRICTLY BEFORE" in pit["feature_eligibility"]
        assert pit["no_intra_bar_optimism"] is True
        if family_id in ("ILLIQ-AMIHUD-28D-W", "BASISLV-PREMFADE-28D"):
            assert "STRICTLY AFTER" in pit["virtual_fill_rule"]
        else:
            assert "funding_settlement_semantics" in pit
            sem = pit["funding_settlement_semantics"]
            assert "ts_opened <= fundingTime < ts_closed" in sem["effective_scope"]
            assert "event_time" in sem and "available_time" in sem
        # warmup coverage measured
        warm = fam["warmup_coverage"]
        assert warm["requirement_days"] == (7 if family_id == "XSECT-FUND-CARRY-7D" else 28)
        assert warm["measured_spotcheck"], f"{family_id}: warmup coverage unmeasured"
        assert warm["verdict"].startswith("MEASURED_CAPABLE")
        # license evidence class present
        assert fam["license_evidence"]["evidence_class"].startswith(MEASURED_PREFIX)
        assert fam["license_evidence"]["claim_limit"] == "no authorized-beyond-measured claim"


def test_warmup_measurements_actually_meet_requirements(data_manifest):
    fams = {f["family_id"]: f for f in data_manifest["families"]}
    for row in fams["ILLIQ-AMIHUD-28D-W"]["warmup_coverage"]["measured_spotcheck"]:
        assert row["covers_28d"] is True and row["bars_measured"] >= 2688
    full_rows = [
        r for r in fams["BASISLV-PREMFADE-28D"]["warmup_coverage"]["measured_spotcheck"]
        if r["covers_28d"]
    ]
    assert len(full_rows) >= 2, "need at least two pairs walked across the full 28d"
    for row in fams["XSECT-FUND-CARRY-7D"]["warmup_coverage"]["measured_spotcheck"]:
        assert row["covers_7d"] is True and row["history_days_covered"] >= 7.0
    traded = fams["XSECT-FUND-CARRY-7D"]["universe"]["exact_symbols_frozen_here"]
    measured_syms = {
        r["symbol"]
        for r in fams["XSECT-FUND-CARRY-7D"]["warmup_coverage"]["measured_spotcheck"]
    }
    assert set(traded).issubset(measured_syms), (
        "family-3 traded universe not fully covered by measured funding history"
    )
    assert "BTCUSDT" in measured_syms, "BTC benchmark context funding history missing"


def test_family3_forward_warmup_condition_present(data_manifest):
    fams = {f["family_id"]: f for f in data_manifest["families"]}
    pol = fams["XSECT-FUND-CARRY-7D"].get("forward_warmup_policy")
    assert pol, "family-3 forward_warmup_policy condition missing"
    assert pol["historical_seed_prohibited"] is True
    assert "fresh forward fill/warmup declared" in pol["family3_condition"]
    assert "must NOT seed the forward book" in pol["family3_condition"]
    assert pol["replay_label"] == "REPLAY_NOT_PROSPECTIVE"
    assert "REPLAY_NOT_PROSPECTIVE" in pol["replay_label_rule_verbatim_from_identity"]


# --------------------------------------------------------------------------
# cost regime freeze
# --------------------------------------------------------------------------

def test_cost_regime_digest_recomputes(cost_manifest):
    block = cost_manifest["current_conservative_cost"]
    canonical = json.dumps(
        block, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    assert digest == cost_manifest["cost_regime_digest"], (
        "cost_regime_digest does not recompute from CURRENT_CONSERVATIVE_COST "
        f"({digest} != {cost_manifest['cost_regime_digest']})"
    )
    assert len(cost_manifest["cost_regime_digest"]) == 64


def test_current_conservative_cost_block_is_complete_and_frozen(cost_manifest):
    ccc = cost_manifest["current_conservative_cost"]
    assert ccc["taker_fee"]["taker_fee_rate"] > 0
    assert ccc["taker_fee"]["frozen"] is True
    ticks = ccc["tick_sizes_usdt_perp"]
    required = {"ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
                "LINKUSDT", "ADAUSDT", "BTCUSDT"}
    assert required.issubset(ticks), f"missing measured tick sizes: {required - set(ticks)}"
    assert ccc["slippage_model"]["ticks_per_virtual_fill"] == 1
    assert ccc["slippage_model"]["direction"] == "adverse_to_side"
    assert "the fill bar's price" in ccc["slippage_model"]["reference_price"]
    fs = ccc["funding_settlement_convention"]
    assert "ts_opened <= fundingTime < ts_closed" in fs["booking"]
    assert "long pays" in fs["sign_convention"] and "short receives" in fs["sign_convention"]
    lat = ccc["latency_assumption"]
    assert "strictly after the decision timestamp" in lat["rule"]
    assert lat["decision_clocks"]["families_1_2"].startswith("weekly Monday")
    assert lat["decision_clocks"]["family_3"].startswith("daily")
    imm = ccc["immutability"]
    assert imm["costs_cannot_move_during_run"] is True
    assert "dated cost-regime boundary" in imm["venue_fee_change_protocol"]
    assert "never an in-place rewrite" in imm["venue_fee_change_protocol"]


def test_lineage_cost_quotes_present_per_family(cost_manifest):
    per_family = cost_manifest["lineage_cost"]["per_family"]
    assert set(per_family) == set(EXPECTED_FAMILIES)
    for family_id, entry in per_family.items():
        assert entry["pointer"].startswith("identity_recovery.json")
        assert entry["upstream_file"]
        quotes = entry.get("verbatim_quote") or entry.get("verbatim_quotes")
        assert quotes, f"{family_id}: LINEAGE_COST verbatim quote missing"


# --------------------------------------------------------------------------
# fail-closed surfacing of unavailable evidence
# --------------------------------------------------------------------------

def _nearest_evidence_class_chain(node, path_to_node):
    """Return (evidence_class, where) for nearest ancestor with evidence_class."""
    chain = path_to_node + [node]
    for candidate in reversed(chain):
        if isinstance(candidate, dict) and "evidence_class" in candidate:
            return candidate["evidence_class"], candidate
    return None, None


def _walk_strings(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, path + (i,))
    elif isinstance(node, str):
        yield path, node


def _assert_no_hidden_unavailable(manifest, name):
    """UNAVAILABLE_FAIL_CLOSED markers must live only inside blocks whose own
    evidence_class declares them unavailable. A marker inside an
    authorized-source (measured) block, or floating with no declaring block,
    fails loudly: unavailable evidence must be surfaced, never hidden."""
    violations = []
    stack = []

    def visit(node):
        stack.append(node)
        if isinstance(node, dict):
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)
        elif isinstance(node, str) and UNAVAILABLE_MARKER in node:
            evidence_class, holder = _nearest_evidence_class_chain(node, stack[:-1])
            if evidence_class is None or not evidence_class.startswith("UNAVAILABLE"):
                violations.append(
                    f"{name}: {UNAVAILABLE_MARKER} inside non-unavailable block "
                    f"(nearest evidence_class={evidence_class!r})"
                )
        stack.pop()

    visit(manifest)
    assert not violations, (
        "UNAVAILABLE evidence is hidden inside authorized-source blocks "
        "(surface it with its own UNAVAILABLE evidence_class + registry entry):\n"
        + "\n".join(violations)
    )


def test_unavailable_markers_are_surfaced_not_hidden(data_manifest, cost_manifest):
    _assert_no_hidden_unavailable(data_manifest, "data_manifest.json")
    _assert_no_hidden_unavailable(cost_manifest, "cost_regime_manifest.json")


def test_unavailable_items_are_registered_in_registry(data_manifest):
    registry = data_manifest["unavailable_evidence"]
    assert isinstance(registry, list)
    for entry in registry:
        assert entry["evidence_class"].startswith("UNAVAILABLE")
        assert entry["probe"]["sha256"]
        assert entry["reason"]
    # the fee-schedule unavailability must be registered (it drives the
    # declared conservative fallback in the cost manifest)
    items = json.dumps(registry)
    assert "fee" in items.lower(), "fee-schedule unavailability not registered"
    cm = _load(COST_MANIFEST_PATH)
    assert cm["current_conservative_cost"]["taker_fee"]["evidence_class"].startswith(
        "UNAVAILABLE"
    ), "taker fee fallback must be honestly marked unavailable-fallback"
    assert cm["current_conservative_cost"]["taker_fee"][
        "no_authorized_beyond_measured_claim"
    ] is True
