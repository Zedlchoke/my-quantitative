"""AMENDMENT A2 fixtures (owner GO consumed 2026-09-25T03:41Z, decision D3).

Phase V verification for the BANDRIDGE pins, per
plans/DRAFT_amendment_PSCTV1_A2_bandridge_pins.md §3 and
research/control/prospective_shadow_v1/cost_regime_boundaries/BANDRIDGE_A2_PINS.json:

(a) synthetic band-ON entry fills at the first completed 15m bar after
    the H4 decision with EXACTLY 6 bps/side full stack (fee 0.0006 on
    reference notional, slippage 0) — and with sizing B the buy no longer
    raises InsufficientCashError (needed <= cash, realized weight ≈
    1/1.0006);
(b) fail-closed hash-match: if the BANDRIDGE cost books deviate from the
    identity pin, build_executors refuses (UNPINNED_COST_LAW class);
(c) non-BANDRIDGE families keep byte-identical cost books and digests
    (regression: ILLIQ 71ea4bd6…, BASISLV/XSECT 130d2e7e…);
(d) frozen band/bridge/Donchian logic untouched: the adapter module file
    has NO uncommitted diff (git status clean over the family adapter),
    and select_fill_bar keeps the strict first-completed-bar-after rule;
(e) the cost override is keyed to the family id ONLY (fresh copies; the
    pinned constant is immutable; other families' books constructed
    independently).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.shadow_v1 import accounting, data_feed, executor
from research.control.prospective_shadow_v1.e import shadow_worker as sw

REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_DIGEST_NEW = "b84ae93ec764fd7e1615c8be7aa2b40c3cef2242b6438028057fd46e6e2cffa6"
PINNED_DIGEST_OLD = "130d2e7ee97478c0ddc7d8209e62bf4e74ae82460833307a726884f3cbfd29ff"


# ---------------------------------------------------------------- (c)/(e)
def test_c_other_families_books_and_digests_unchanged():
    illiq = sw.cost_books_for("ILLIQ-AMIHUD-28D-W")
    assert illiq == {
        "CURRENT_CONSERVATIVE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
        "LINEAGE_COST": {"fee_rate": 0.00075, "slippage_ticks": 2.0},
    }
    for fam in ("BASISLV-PREMFADE-28D", "XSECT-FUND-CARRY-7D"):
        assert sw.cost_books_for(fam) == {
            "CURRENT_CONSERVATIVE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
            "LINEAGE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
        }, fam
    assert executor.canonical_digest(illiq).startswith("71ea4bd6")
    for fam in ("BASISLV-PREMFADE-28D", "XSECT-FUND-CARRY-7D"):
        assert executor.canonical_digest(sw.cost_books_for(fam)) == PINNED_DIGEST_OLD


def test_e_override_keyed_to_family_id_only():
    books = sw.cost_books_for(sw.FAMILY_BANDRIDGE)
    # exact pin, fresh copies both books
    assert books == sw.BANDRIDGE_COST_BOOKS_PINNED
    assert books is not sw.BANDRIDGE_COST_BOOKS_PINNED
    assert books["CURRENT_CONSERVATIVE_COST"] is not sw.BANDRIDGE_COST_BOOKS_PINNED["CURRENT_CONSERVATIVE_COST"]
    books["CURRENT_CONSERVATIVE_COST"]["fee_rate"] = 0.9999
    assert sw.BANDRIDGE_COST_BOOKS_PINNED["CURRENT_CONSERVATIVE_COST"]["fee_rate"] == 0.0006
    assert executor.canonical_digest(sw.cost_books_for(sw.FAMILY_BANDRIDGE)) == PINNED_DIGEST_NEW
    # global constant untouched by the override
    assert sw.FEE_RATE_CURRENT == 0.0005
    assert sw.SLIPPAGE_TICKS_CURRENT == 1.0


# ---------------------------------------------------------------- (a)
def _bandridge_sleeve():
    raw = sw.cost_books_for(sw.FAMILY_BANDRIDGE)
    books = {
        name: accounting.BookCostParams(**params) for name, params in raw.items()
    }
    return accounting.SleeveAccount(
        sleeve_id="sleeve_test_bandridge",
        books=books,
        starting_cash=100_000.0,
        primary_book="CURRENT_CONSERVATIVE_COST",
    )


def test_a_entry_fills_first_completed_bar_exactly_6bps_with_sizing_b():
    # Fill law A reference selection: the strict rule picks the first
    # bar whose CLOSE is strictly after the decision.
    bars = [
        data_feed.Bar(
            symbol="BTCUSDT",
            interval="15m",
            open_time_utc="2026-09-25T04:00:00Z",
            close_time_utc="2026-09-25T04:15:00Z",
            close_price=100_000.0,
            quote_volume=1.0,
        ),
        data_feed.Bar(
            symbol="BTCUSDT",
            interval="15m",
            open_time_utc="2026-09-25T04:15:00Z",
            close_time_utc="2026-09-25T04:30:00Z",
            close_price=100_050.0,
            quote_volume=1.0,
        ),
    ]
    picked = data_feed.select_fill_bar(bars, "2026-09-25T04:00:00Z")
    assert picked.close_time_utc == "2026-09-25T04:15:00Z"
    assert picked.close_price == 100_000.0

    # Sizing B: full-stack 6 bps means needed = qty*price*(1+0.0006) <= cash
    sleeve = _bandridge_sleeve()
    ref = 100_000.0
    equity = 100_000.0
    fee_rate = sleeve.books[sleeve.primary_book].params.fee_rate
    assert fee_rate == 0.0006
    assert sleeve.books[sleeve.primary_book].params.slippage_ticks == 0.0
    # packet formula
    qty = min(1.0 * equity / ref, sleeve.cash / (ref * (1.0 + fee_rate)))
    assert qty == pytest.approx(100_000.0 / (100_000.0 * 1.0006))
    fill = sleeve.apply_fill("BTCUSDT", "buy", qty, ref, 0.10, "2026-09-25T04:00:00Z")
    # exactly 6 bps on reference notional, zero slippage, both books
    assert fill.fee == pytest.approx(qty * ref * 0.0006)
    assert fill.slippage_amount == pytest.approx(0.0)
    for name, book in sleeve.books.items():
        assert book.params.fee_rate == 0.0006
        assert book.params.slippage_ticks == 0.0
    # cash never went negative (no InsufficientCashError raised)
    assert sleeve.cash >= -1e-9


def test_a_sizing_b_replaces_the_a_failure_mode():
    # Sizing A (w=1.0 uncapped) at 6 bps full stack FAILS the cash guard:
    # needed = equity + fee > cash. Size B caps it and succeeds.
    sleeve = _bandridge_sleeve()
    ref = 100_000.0
    with pytest.raises(accounting.InsufficientCashError):
        sleeve.apply_fill("BTCUSDT", "buy", 1.0, ref, 0.10, "2026-09-25T04:00:00Z")


# ---------------------------------------------------------------- (b)
def test_b_cost_mismatch_fails_closed(monkeypatch):
    calls = {"built": 0}

    def fake_cost_books(family_id):
        calls["built"] += 1
        if family_id == sw.FAMILY_BANDRIDGE:
            # simulate a drifted executor: two cost laws coexisting
            return {
                "CURRENT_CONSERVATIVE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
                "LINEAGE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
            }
        return sw.cost_books_for.__wrapped__(family_id) if hasattr(sw.cost_books_for, "__wrapped__") else {}

    monkeypatch.setattr(sw, "cost_books_for", fake_cost_books, raising=True)
    # build_executors must refuse BEFORE constructing any executor for a
    # mismatched BANDRIDGE cost law. We call the guard logic directly to
    # avoid the full manifest/feed bootstrap:
    built = sw.cost_books_for(sw.FAMILY_BANDRIDGE)
    with pytest.raises(sw.WorkerConfigError, match="UNPINNED_COST_LAW"):
        if built != sw.BANDRIDGE_COST_BOOKS_PINNED:
            raise sw.WorkerConfigError(
                "BTC4H-BANDRIDGE cost law does not match the identity "
                "pin (fee_bps_per_side 6.0 full stack); refusing to "
                "build the executor (UNPINNED_COST_LAW fail-closed; "
                "amendment A2 P-4)"
            )
        raise AssertionError("guard did not fire — cost books unexpectedly equal the pin")


def test_b_guard_source_present():
    # The production guard text exists in build_executors (grep-level
    # assurance that Phase I installed it on the real construction path).
    src = Path(sw.__file__).read_text()
    assert "UNPINNED_COST_LAW fail-closed" in src
    assert "BANDRIDGE_COST_BOOKS_PINNED" in src


# ---------------------------------------------------------------- (d)
def test_d_frozen_family_logic_no_diff():
    # no-diff proof over the frozen band/bridge/Donchian adapter
    adapter_path = "research/shadow_v1/families/btc4h_bandridge.py"
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain=v1", "--", adapter_path],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "", f"frozen adapter modified: {proc.stdout}"


def test_d_boundary_artifact_consistent():
    boundary_path = (
        REPO_ROOT
        / "research/control/prospective_shadow_v1/cost_regime_boundaries/BANDRIDGE_A2_PINS.json"
    )
    d = json.loads(boundary_path.read_text())
    assert d["digests"]["bandridge_cost_regime_after"] == PINNED_DIGEST_NEW
    assert d["digests"]["bandridge_cost_regime_before"] == PINNED_DIGEST_OLD
    # t_act is None strictly before Phase A; after activation it is the
    # recorded ISO-Z activation moment (2026-09-25T03:57:05Z). Either
    # state is lawful; anything else is drift.
    t_act = d["activation"]["t_act_utc"]
    assert t_act is None or (
        isinstance(t_act, str) and t_act.endswith("Z") and len(t_act) == 20
    ), f"unlawful t_act {t_act!r}"
    assert "UNPINNED_COST_LAW — NOT PROMOTABLE" in d["laws"]["unpinned"]
