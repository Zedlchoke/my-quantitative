"""CRYPTO-NG3 P0 census gate tests — fully OFFLINE (no network).

Proves the census library logic that the heavy run depends on: self-computed
keccak identity pins (C7, fail-closed), canonical normalization for the
cross-transport identity gate (C1), exact chunk partition (C3), conservation
arithmetic (C9), measured-identity netting classes (C5), composition flags
(C6), fold freeze (C10), verdict assembly and Decimal display exactness.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from research.assets.crypto_ng3 import census_lib as cl

FIXTURES = Path(__file__).resolve().parents[1] / "research" / "assets" / "crypto_ng3" / "fixtures"


def _load(name):
    return json.loads((FIXTURES / name).read_text())


# ---------------------------------------------------------------------------
# C7 — contract identity: own keccak, fail-closed pins
# ---------------------------------------------------------------------------
def test_keccak_standard_vectors():
    assert cl.keccak256(b"").hex() == \
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    assert cl.keccak256(b"abc").hex() == \
        "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45"
    assert cl.keccak256(b"The quick brown fox jumps over the lazy dog").hex() == \
        "4d741b6f1eb29cb2a9b9911c82f56fa8d73b04959d3d9d222895df6c0b28aa15"


def test_topic_pins_reproduced_from_own_keccak():
    out = cl.verify_pins()
    assert out["verdict"] == "PASS"
    assert out["computed"] == cl.PINNED_TOPICS
    # canonical Transfer topic — public constant cross-check
    assert cl.topic_of("Transfer(address,address,uint256)") == \
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    # pinned values match the frontier-probe observed topic bytes
    mint_ev = _load("mint_event_blockscout.json")
    assert mint_ev["topics"][0] == cl.PINNED_TOPICS[cl.MINT_SIG]
    burn_ev = _load("burn_event_blockscout.json")
    assert burn_ev["topics"][0] == cl.PINNED_TOPICS[cl.BURN_SIG]


def test_pin_mismatch_fails_closed(monkeypatch):
    tampered = dict(cl.PINNED_TOPICS)
    tampered[cl.MINT_SIG] = "0x" + "00" * 32
    monkeypatch.setattr(cl, "PINNED_TOPICS", tampered)
    with pytest.raises(cl.PinMismatch):
        cl.verify_pins()


def test_normalize_real_probe_events_exact():
    mint = cl.normalize_log(_load("mint_event_blockscout.json"))
    assert mint["issuer"] == "USDC_ETHEREUM" and mint["event"] == "MINT"
    assert mint["amount_units"] == 327024412
    assert cl.amount_to_units(mint["amount_units"]) == Decimal("327.024412")
    # topic1 is the low-cardinality minter field; the CCTP minter anchor
    assert mint["topic1"].endswith(cl.CCTP_TOKEN_MINTER[2:])
    burn = cl.normalize_log(_load("burn_event_blockscout.json"))
    assert burn["issuer"] == "USDC_ETHEREUM" and burn["event"] == "BURN"
    assert cl.amount_to_units(burn["amount_units"]) == Decimal("14394.380000")
    assert burn["topic1"].endswith(cl.TREASURY_ADDR[2:])


@pytest.mark.parametrize("mutate", [
    pytest.param(lambda lg: lg.update(address=cl.USDT_ADDR), id="wrong-address"),
    pytest.param(lambda lg: lg.update(topics=[cl.PINNED_TOPICS[cl.ISSUE_SIG]]), id="wrong-topic0"),
    pytest.param(lambda lg: lg.update(topics=[cl.PINNED_TOPICS[cl.MINT_SIG]]), id="wrong-topic-count"),
    pytest.param(lambda lg: lg.update(data="0x1234"), id="bad-data-length"),
])
def test_unknown_shapes_fail_closed(mutate):
    lg = _load("mint_event_blockscout.json")
    mutate(lg)
    with pytest.raises(cl.EventShapeViolation):
        cl.normalize_log(lg)


# ---------------------------------------------------------------------------
# C1 — cross-transport canonical identity (blockscout vs RPC envelope)
# ---------------------------------------------------------------------------
def test_blockscout_and_rpc_envelopes_canonicalize_identically():
    bs = cl.normalize_log(_load("mint_event_blockscout.json"))
    rpc = cl.normalize_log(_load("mint_event_rpc.json"))
    assert cl.canonical_bytes(bs) == cl.canonical_bytes(rpc)
    assert cl.event_set_digest([bs]) == cl.event_set_digest([rpc])
    # blockscout-only field (timeStamp) is carried but never enters the digest
    assert "block_ts" in bs and "block_ts" not in rpc


def test_event_set_digest_order_insensitive():
    evs = _load("census_events_sample.json")
    assert cl.event_set_digest(evs) == cl.event_set_digest(list(reversed(evs)))


# ---------------------------------------------------------------------------
# C3 — exact chunk partition
# ---------------------------------------------------------------------------
def test_day_partition_exact_multi_day():
    day_ranges = [("2025-08-22", 1000, 9000), ("2025-08-23", 9000, 16183)]
    chunks = cl.day_partition(day_ranges, 2000)
    ok, why = cl.coverage_ok(chunks, 1000, 16183)
    assert ok, why
    assert all(c["end"] - c["start"] <= 2000 for c in chunks)
    assert chunks[0]["day"] == "2025-08-22" and chunks[-1]["day"] == "2025-08-23"


def test_coverage_detects_gap_overlap_and_end_mismatch():
    good = [{"start": 0, "end": 10}, {"start": 10, "end": 20}]
    assert cl.coverage_ok(good, 0, 20)[0] is True
    gap = [{"start": 0, "end": 10}, {"start": 11, "end": 20}]
    assert cl.coverage_ok(gap, 0, 20)[0] is False
    overlap = [{"start": 0, "end": 11}, {"start": 10, "end": 20}]
    assert cl.coverage_ok(overlap, 0, 20)[0] is False
    short = [{"start": 0, "end": 10}, {"start": 10, "end": 19}]
    assert cl.coverage_ok(short, 0, 20)[0] is False


# ---------------------------------------------------------------------------
# C9 — conservation identity per window (exact integer arithmetic)
# ---------------------------------------------------------------------------
def test_day_rows_conservation_identity_exact():
    evs = _load("census_events_sample.json")
    usdc = cl.day_rows(evs, "USDC_ETHEREUM")
    assert len(usdc) == 2
    d1 = next(r for r in usdc if r["day"] == "2025-08-22")
    # 5000000000 + 1234567 mints - 1000000000 burns, exact
    assert d1["net_units"] == 5000000000 + 1234567 - 1000000000
    assert d1["net"] == str(cl.amount_to_units(d1["net_units"]))
    assert cl.conservation_breaks(usdc) == []
    usdt = cl.day_rows(evs, "USDT_ETHEREUM")
    d2 = next(r for r in usdt if r["day"] == "2025-08-23")
    assert d2["net_units"] == 1000000000000 - 400000000
    assert cl.conservation_breaks(usdt) == []


def test_conservation_break_is_reported_never_smoothed():
    rows = cl.day_rows(_load("census_events_sample.json"), "USDC_ETHEREUM")
    rows[0]["net_units"] += 1  # tamper
    breaks = cl.conservation_breaks(rows)
    assert len(breaks) == 1 and breaks[0]["day"] == rows[0]["day"]


def test_chunk_day_crossfoot_detects_drift():
    evs = _load("census_events_sample.json")
    usdc_rows = cl.day_rows(evs, "USDC_ETHEREUM")
    chunk_nets = [{"day": "2025-08-22", "issuer_net_units": {"USDC_ETHEREUM": 4001234567}},
                  {"day": "2025-08-23", "issuer_net_units": {"USDC_ETHEREUM": -2000000}}]
    assert cl.chunk_day_crossfoot(chunk_nets, usdc_rows, "USDC_ETHEREUM") == []
    chunk_nets[0]["issuer_net_units"]["USDC_ETHEREUM"] += 7
    breaks = cl.chunk_day_crossfoot(chunk_nets, usdc_rows, "USDC_ETHEREUM")
    assert len(breaks) == 1 and breaks[0]["day"] == "2025-08-22"


# ---------------------------------------------------------------------------
# C5 — identity netting measured, labels never asserted
# ---------------------------------------------------------------------------
def test_minter_table_and_classification_frozen_rule():
    evs = _load("census_events_sample.json")
    table = {r["address"]: r for r in cl.minter_table(evs)}
    assert set(table) == {cl.TREASURY_ADDR, cl.CCTP_TOKEN_MINTER}
    assert table[cl.TREASURY_ADDR]["mint_sum"] == 5000000000
    assert table[cl.TREASURY_ADDR]["burn_sum"] == 1000000000 + 2000000
    # treasury is the top burner -> dominant evidence
    total_mint = sum(r["mint_sum"] for r in table.values())
    evidence = {"dominant": table[cl.TREASURY_ADDR]["burn_sum"] >= max(
        r["burn_sum"] for r in table.values()) and table[cl.TREASURY_ADDR]["mint_sum"] * 4 >= total_mint}
    # contract-verified CCTP class
    assert cl.classify_address(cl.CCTP_TOKEN_MINTER,
                               {cl.CCTP_TOKEN_MINTER: True}, evidence) == "CCTP_TOKEN_MINTER"
    # an uncode'd address cannot claim the CCTP class (fail-closed label)
    assert cl.classify_address(cl.CCTP_TOKEN_MINTER,
                               {cl.CCTP_TOKEN_MINTER: False}, evidence) == "UNCLASSIFIED"
    assert cl.classify_address(cl.TREASURY_ADDR, {}, evidence) == "TREASURY_MEASURED_DOMINANT"
    # any other address (e.g. an exchange hot wallet) stays UNCLASSIFIED —
    # no PIT-evidenced labels exist, none may be asserted
    assert cl.classify_address("0x28c6c06298d514db089934071355e5743bf21d60",
                               {}, evidence) == "UNCLASSIFIED"


def test_minter_field_flip_check_detects_layout_change():
    evs = _load("census_events_sample.json")
    check = cl.minter_field_flip_check(evs)
    assert check["ok"] is True and check["topic1_distinct"] == 2 and check["topic2_distinct"] == 2
    # construct a real layout flip: minter field (topic1) becomes per-event
    # unique while the recipient field stays concentrated
    mint_t2 = {ev["topic1"] for ev in evs if ev["event"] == "MINT"}  # collapse recipients onto minter values
    real_flip = []
    n = 0
    for ev in evs:
        if ev["event"] == "MINT":
            ev = dict(ev)
            ev["topic1"] = f"0x{'00' * 12}{n:08x}{'00' * 12}"
            ev["topic2"] = sorted(mint_t2)[0]
            n += 1
        real_flip.append(ev)
    real_flip.append(dict(real_flip[0], topic1=f"0x{'00' * 12}{n:08x}{'00' * 12}",
                          block=999999, log_index=9))
    check2 = cl.minter_field_flip_check(real_flip)
    assert check2["ok"] is False  # topic1 cardinality now exceeds topic2


# ---------------------------------------------------------------------------
# C6 — composition flags
# ---------------------------------------------------------------------------
def test_net_extreme_days_p99_rule():
    # 99 regular days (distinct nets) + 1 extreme outlier: P99 rank lands on
    # the outlier exactly, so exactly one day flags
    rows = [{"day": f"d-{i:03d}", "issuer": "USDC_ETHEREUM",
             "net_units": 1_000_000 + i} for i in range(99)]
    rows.append({"day": "2026-01-01", "issuer": "USDC_ETHEREUM", "net_units": 900_000_000})
    flagged = cl.net_extreme_days(rows, "0.99")
    assert flagged == ["2026-01-01"]
    # a window of only zero-net days never flags
    assert cl.net_extreme_days([{"day": f"z-{i}", "issuer": "USDC_ETHEREUM",
                                 "net_units": 0} for i in range(50)], "0.99") == []


# ---------------------------------------------------------------------------
# C10 — fold freeze
# ---------------------------------------------------------------------------
def test_folds_partition_days_chronologically():
    days = [f"day-{i:03d}" for i in range(366)]
    folds = cl.fold_boundaries(days)
    assert [len(folds[k]) for k in ("fold1", "fold2", "fold3")] == [146, 109, 111]
    combined = folds["fold1"] + folds["fold2"] + folds["fold3"]
    assert combined == days  # chronological partition, no gaps, order kept


# ---------------------------------------------------------------------------
# Verdict assembly — fail-closed semantics
# ---------------------------------------------------------------------------
def test_overall_verdict_paths():
    ok = {g: {"verdict": "PASS"} for g in ("C1", "C2", "C3", "C4", "C5", "C6",
                                           "C7", "C8", "C9", "C10", "C11")}
    assert cl.overall_verdict(ok) == "P0_CENSUS_PASS"
    for broken in ("C1", "C3", "C9", "C7"):
        g = {k: {"verdict": "PASS"} for k in ok}
        g[broken] = {"verdict": "FAIL"}
        assert cl.overall_verdict(g) == "P0_CENSUS_BLOCKED_SOURCE"
    missing = {k: v for k, v in ok.items() if k != "C3"}
    assert cl.overall_verdict(missing) == "P0_CENSUS_BLOCKED_SOURCE"
    late = {k: v for k, v in ok.items()}
    late["C10"] = {"verdict": "FAIL"}
    assert cl.overall_verdict(late) == "P0_CENSUS_BLOCKED_DATA_OR_SELECTION"


# ---------------------------------------------------------------------------
# Decimal exactness — no binary float anywhere in census arithmetic
# ---------------------------------------------------------------------------
def test_amount_display_exact_decimal():
    assert cl.amount_to_units(1) == Decimal("0.000001")
    assert cl.amount_to_units(28746185016541) == Decimal("28746185.016541")
    assert str(cl.amount_to_units(327024412)) == "327.024412"
    # float round-trip would corrupt this value; Decimal must not
    assert cl.amount_to_units(50497424343509521) == Decimal("50497424343.509521")
