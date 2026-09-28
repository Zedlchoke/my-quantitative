"""Shared Portfolio 100K V1 — engine tests.

These pin the reconciliation and safety laws. They read REAL epoch-1
sources read-only and SYNTHETIC fixtures written to tmp_path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import portfolio_lib as pl  # noqa: E402


# ----------------------------------------------------------------------
# FX replay
# ----------------------------------------------------------------------
def test_fx_replay_idempotent_under_full_duplication(tmp_path):
    src = pl.FX_DIR / "shadow_journal.jsonl"
    lines = src.read_text().splitlines()
    meta = {"parity_selftest", "shadow_start", "boot_replay", "day_roll",
            "day_anchor", "seq_probe"}
    n_meta = sum(1 for l in lines if json.loads(l).get("event") in meta)
    n_events = len(lines) - n_meta
    dup = tmp_path / "dup.jsonl"
    dup.write_text("\n".join(lines + lines) + "\n")  # every event twice
    a = pl.fx_replay(src)
    b = pl.fx_replay(dup)
    assert b["integrity"]["events_dup"] == n_events  # every event dups exactly once
    assert b["trades"] == a["trades"]
    assert b["realized_by_day"] == a["realized_by_day"]
    assert b["open_positions"] == a["open_positions"]
    assert b["realized_usd"] == a["realized_usd"]


def test_fx_force_flat_attribution_by_utc_day(tmp_path):
    j = tmp_path / "j.jsonl"
    rows = [
        {"event": "shadow_start", "ts": "2026-09-24T00:00:00+00:00"},
        {"event": "fill_open", "pair": "EURUSD", "dir": 1, "entry_px": 1.10,
         "entry_ts": 1790282400, "lots": 1.5, "ts": "2026-09-24T02:00:00+00:00"},
        {"event": "force_flat", "pair": "EURUSD", "dir": 1, "entry_px": 1.10,
         "exit_px": 1.1010, "pnl_usd": 150.0, "ts": "2026-09-24T20:00:05+00:00"},
        {"event": "fill_open", "pair": "GBPUSD", "dir": -1, "entry_px": 1.32,
         "entry_ts": 1790368800, "lots": 1.5, "ts": "2026-09-25T02:00:00+00:00"},
        {"event": "fill_close", "pair": "GBPUSD", "dir": -1, "entry_px": 1.32,
         "exit_px": 1.3180, "pnl_usd": 300.0, "reason": "signal",
         "ts": "2026-09-25T15:00:00+00:00"},
    ]
    j.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    r = pl.fx_replay(j)
    assert r["integrity"]["events_bad"] == 0
    assert r["realized_by_day"]["2026-09-24"] == {"EURUSD": 150.0}
    assert r["realized_by_day"]["2026-09-25"] == {"GBPUSD": 300.0}
    assert r["open_positions"] == {}  # both closed
    assert [t["kind"] for t in r["trades"]] == ["force_flat", "fill_close"]


def test_fx_open_position_survives_replay(tmp_path):
    j = tmp_path / "j.jsonl"
    rows = [
        {"event": "fill_open", "pair": "EURUSD", "dir": -1, "entry_px": 1.13,
         "entry_ts": 1790282400, "lots": 1.5, "ts": "2026-09-24T02:00:00+00:00"},
    ]
    j.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    r = pl.fx_replay(j)
    assert r["open_positions"]["EURUSD"]["dir"] == -1
    assert r["realized_by_day"] == {}


# ----------------------------------------------------------------------
# crypto series — real sources + synthetic
# ----------------------------------------------------------------------
def test_psv1_equity_identity_holds_on_real_marks():
    """Pinned worker identity: equity = seed + realized + unrealized
    − fees + funding (slippage informational). Any day failing this is
    RECON_FAIL and must withhold the decomposition (fail-closed)."""
    for fam in pl.CRYPTO_SLEEVES:
        s = pl.crypto_daily_series(pl.PSV1_RESULTS / f"valuation_marks/{fam}.jsonl")
        assert s["rows"], fam
        for r in s["rows"]:
            if r["status"] in ("OK", "GAP_SPAN"):
                d = r["decomposition"]
                assert d is not None
                assert abs(d["residual_usd"]) <= pl.RECON_TOL_USD
            elif r["status"] == "RECON_FAIL":
                assert r["decomposition"] is None

def test_missing_boundary_day_is_unavailable_not_zero(tmp_path):
    m = tmp_path / "f.jsonl"
    rows = [
        {"mark_timestamp_utc": "2026-09-20T23:55:00Z", "equity": 100000.0,
         "realized_pnl": 0.0, "unrealized_pnl": 0.0, "fees": 0.0,
         "slippage": 0.0, "funding": 0.0, "positions": []},
        # 09-21 completely missing
        {"mark_timestamp_utc": "2026-09-22T23:55:00Z", "equity": 100050.0,
         "realized_pnl": 60.0, "unrealized_pnl": -10.0, "fees": 0.0,
         "slippage": 0.0, "funding": 0.0, "positions": []},
    ]
    m.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    s = pl.crypto_daily_series(m)
    assert s["rows"][0]["status"] == "BASELINE"
    gap = s["rows"][1]
    assert gap["status"] == "GAP_SPAN"  # Δequity spans the gap, labelled
    assert gap["gap_span_hours"] and gap["gap_span_hours"] > 40
    # a day with NO later mark at all must not be invented by the caller:
    assert all(r["day_utc"] in ("2026-09-20", "2026-09-22") for r in s["rows"])


def test_corrupt_partial_line_is_skipped(tmp_path):
    m = tmp_path / "f.jsonl"
    m.write_text(
        json.dumps({"mark_timestamp_utc": "2026-09-20T23:55:00Z", "equity": 100000.0,
                    "realized_pnl": 0.0, "unrealized_pnl": 0.0, "fees": 0.0,
                    "slippage": 0.0, "funding": 0.0, "positions": []}) + "\n"
        + '{"mark_timestamp_utc": "2026-09-21T23:55:00Z", "equity": 1000' + "\n")
    s = pl.crypto_daily_series(m)
    assert len(s["rows"]) == 1 and s["rows"][0]["status"] == "BASELINE"


# ----------------------------------------------------------------------
# portfolio assembly
# ----------------------------------------------------------------------
def test_state_activation_state_uses_explicit_config(tmp_path):
    """Engine must honor whatever the explicit config says: PENDING →
    PREVIEW with no epoch-2 numbers; the live config is post-activation
    ACTIVE (pinned in test_one_app.test_default_config_is_activated)."""
    base = json.loads((HERE / "epoch_config.json").read_text())
    base["status"] = "PENDING_OWNER_GO"
    p = tmp_path / "pending.json"
    p.write_text(json.dumps(base))
    s = pl.build_state(p)
    assert s["mode"] == "PREVIEW"
    assert s["epoch2"]["pnl_total"] is None
    assert s["epoch2"]["opening_equity_usd_eq"] == 100000.0
    # per-sleeve-100k sum is the OLD model's number and must NOT equal 100k
    assert s["epoch1"]["per_sleeve_100k_model_sum_usd_eq"] > 400000


def test_build_state_deterministic():
    a = json.dumps(pl.build_state(), sort_keys=True)
    b = json.dumps(pl.build_state(), sort_keys=True)
    assert a == b


def test_history_calendar_reconciles_to_sleeve_equity_deltas():
    """Σ history day PnL per crypto sleeve == last equity − file's first
    mark equity (first day is PARTIAL_OPEN from the file's own first
    mark), within rounding."""
    s = pl.build_state()
    hist = s["epoch1"]["history_days"]
    assert hist
    fam = "XSECT-FUND-CARRY-7D"
    marks = pl.read_jsonl(pl.PSV1_RESULTS / f"valuation_marks/{fam}.jsonl")
    # baseline = first TIMESTAMPED mark with numeric equity (a timestamp-less
    # leading mark belongs to no UTC day and is deliberately unattributed)
    first = next(m for m in marks
                 if (str(m.get("mark_timestamp_utc") or m.get("observed_at_utc") or "")
                     and isinstance(m.get("equity"), (int, float))))
    last_eq = marks[-1]["equity"]
    day_sum = sum((d["sleeves"][fam].get("day_pnl") or 0.0) for d in hist)
    assert abs(day_sum - (last_eq - first["equity"])) < 0.05, fam


def test_fx_history_matches_journal_total():
    s = pl.build_state()
    fx_sum = sum(d["sleeves"]["FX-RANGEFADE-2M"]["day_realized_usd"]
                 for d in s["epoch1"]["history_days"])
    replay = pl.fx_replay(pl.FX_DIR / "shadow_journal.jsonl")
    assert abs(fx_sum - replay["realized_usd"]) < 0.01


# ----------------------------------------------------------------------
# capital rule
# ----------------------------------------------------------------------
CAPS = {"cap_total_gross_pct_equity": 250, "cap_fx_gross_pct_equity": 150,
        "cap_crypto_gross_pct_equity": 150}
ORDER = ["FX-RANGEFADE-2M", "BTC4H-BANDRIDGE", "BASISLV-PREMFADE-28D",
         "ILLIQ-AMIHUD-28D-W"]


def test_capital_rule_allow_scale_block():
    # room for everything
    d = pl.apply_capital_rule(100000.0, 0.0, 0.0, 1.0, ORDER,
                              "FX-RANGEFADE-2M", 150000.0, CAPS)
    assert d["decision"] == "ALLOW"
    # FX over class cap → scaled to headroom (never negative)
    d = pl.apply_capital_rule(100000.0, 100000.0, 0.0, 1.0, ORDER,
                              "FX-RANGEFADE-2M", 100000.0, CAPS)
    assert d["decision"] == "SCALED" and abs(d["scaled_add_usd_eq"] - 50000.0) < 1
    # zero headroom → BLOCK
    d = pl.apply_capital_rule(100000.0, 150000.0, 0.0, 1.0, ORDER,
                              "FX-RANGEFADE-2M", 10000.0, CAPS)
    assert d["decision"] == "BLOCK"
    # unknown sleeve → BLOCK (fail-closed)
    d = pl.apply_capital_rule(100000.0, 0.0, 0.0, 1.0, ORDER,
                              "MYSTERY-SLEEVE", 1000.0, CAPS)
    assert d["decision"] == "BLOCK"


def test_capital_rule_deterministic_and_pnl_free():
    args = (100000.0, 50000.0, 30000.0, 1.0, ORDER, "ILLIQ-AMIHUD-28D-W", 80000.0, CAPS)
    assert pl.apply_capital_rule(*args) == pl.apply_capital_rule(*args)


def test_capital_rule_cross_class_total_cap_binds():
    """R3 must bind on the aggregate: FX 120k + crypto 120k USDT + new
    crypto 20k → total 260k > 250% cap even though the crypto CLASS cap
    (150k) still has room → scaled to the total headroom of 10k."""
    d = pl.apply_capital_rule(100000.0, 120000.0, 120000.0, 1.0, ORDER,
                              "ILLIQ-AMIHUD-28D-W", 20000.0, CAPS)
    assert d["decision"] == "SCALED"
    assert abs(d["scaled_add_usd_eq"] - 10000.0) < 1e-6


def test_capital_rule_min_unit_block_fx_and_crypto():
    # FX: $10 headroom left, request $1,000 → scaled below min unit → BLOCK
    d = pl.apply_capital_rule(100000.0, 149990.0, 0.0, 1.0, ORDER,
                              "FX-RANGEFADE-2M", 1000.0, CAPS)
    assert d["decision"] == "BLOCK" and "min unit" in d["reason"]
    # crypto: 5 USDT headroom, request 100 USDT → below 10 USDT min → BLOCK
    d = pl.apply_capital_rule(100000.0, 0.0, 149995.0, 1.0, ORDER,
                              "BANDRIDGE-PLACEHOLDER" if False else "BTC4H-BANDRIDGE",
                              100.0, CAPS)
    assert d["decision"] == "BLOCK" and "min unit" in d["reason"]


def test_usdt_ref_moves_crypto_headroom():
    """USD/USDT conversion is a real input: ref 1.02 shrinks crypto
    headroom in USD-eq terms."""
    a = pl.apply_capital_rule(100000.0, 0.0, 140000.0, 1.00, ORDER,
                              "ILLIQ-AMIHUD-28D-W", 15000.0, CAPS)
    b = pl.apply_capital_rule(100000.0, 0.0, 140000.0, 1.02, ORDER,
                              "ILLIQ-AMIHUD-28D-W", 15000.0, CAPS)
    assert a["decision"] == "SCALED" and abs(a["scaled_add_usd_eq"] - 10000.0) < 1e-6
    assert b["decision"] == "SCALED" and abs(b["scaled_add_usd_eq"] - 7200.0) < 1e-6


def test_activation_is_fail_closed_until_all_go_fields_present(tmp_path):
    base = json.loads((HERE / "epoch_config.json").read_text())
    # flip status alone → must NOT activate
    bad = dict(base, status="ACTIVE", activation_ts_utc=None,
           open_position_law="PENDING_OWNER", rule_digest=None,
           review_log_sha256=None,
           allocation=dict(base["allocation"], mode="OWNER_DECISION"))
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(bad))
    s = pl.build_state(p)
    assert s["mode"] == "PREVIEW_FORCED"
    assert s["epoch2"]["activation_error"]
    assert s["epoch2"]["pnl_total"] is None
    # all gate fields present → engine accepts ACTIVE and computes epoch-2
    good = dict(base, status="ACTIVE", activation_ts_utc="2026-09-25T00:00:00Z",
                open_position_law="REOPEN_AT_MARK",
                allocation=dict(base["allocation"], mode="EQUAL_2WAY"),
                rule_digest="deadbeef", review_log_sha256="cafebabe")
    p.write_text(json.dumps(good))
    s = pl.build_state(p)
    assert s["mode"] == "ACTIVE"
    assert s["epoch2"]["status"] == "ACTIVE"
    assert s["epoch2"]["opening_equity_usd_eq"] == 100000.0
    assert s["epoch2"]["activation_error"] is None


def test_epoch2_only_counts_post_activation_data(tmp_path):
    """With T_STAR = now, epoch-2 FX realized must be ≤ epoch-1 total and
    deterministic; with a FUTURE T_STAR everything is zero/UNAVAILABLE."""
    base = json.loads((HERE / "epoch_config.json").read_text())
    good = dict(base, status="ACTIVE", activation_ts_utc="2099-01-01T00:00:00Z",
                open_position_law="FLAT_START",
                allocation=dict(base["allocation"], mode="EQUAL_2WAY"),
                rule_digest="x", review_log_sha256="y")
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(good))
    s = pl.build_state(p)
    assert s["epoch2"]["fx_realized"] == 0.0
    assert s["epoch2"]["pnl_total"] == 0.0
    for fam in ("BASISLV-PREMFADE-28D",):
        assert s["epoch2"]["sleeves"][fam]["pnl"] is None  # no mark ≥ 2099 yet


def test_synthetic_recon_fail_withholds_decomposition(tmp_path):
    m = tmp_path / "f.jsonl"
    rows = [
        {"mark_timestamp_utc": "2026-09-20T23:55:00Z", "equity": 100000.0,
         "realized_pnl": 0.0, "unrealized_pnl": 0.0, "fees": 0.0,
         "slippage": 0.0, "funding": 0.0, "positions": []},
        # equity delta +500 but components only explain +10 → RECON_FAIL
        {"mark_timestamp_utc": "2026-09-21T23:55:00Z", "equity": 100500.0,
         "realized_pnl": 0.0, "unrealized_pnl": 10.0, "fees": 0.0,
         "slippage": 0.0, "funding": 0.0, "positions": []},
    ]
    m.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    s = pl.crypto_daily_series(m)
    r = s["rows"][1]
    assert r["status"] == "RECON_FAIL"
    assert r["decomposition"] is None          # withheld, fail-closed
    assert r["day_pnl"] == 500.0               # Δequity still visible


# ----------------------------------------------------------------------
# safety: no order surface anywhere in the new servers
# ----------------------------------------------------------------------
def test_no_order_surface_in_new_servers():
    banned = ["POST", "put(order", "place_order", "submit_order", "broker",
              "api.binance.com/api", "send_order", "websocket order"]
    for f in [HERE / "phorec2/serve_phorec2.py", HERE / "crypto_view2.py"]:
        text = f.read_text().lower()
        for b in banned:
            assert b.lower() not in text, f"{f.name} contains banned token {b}"
        assert "do_post" not in text  # GET-only servers
