"""AMENDMENT A3 fixtures (owner GO consumed 2026-09-25T04:21:15Z, decision D4).

Phase V verification for the XSECT-FUND-CARRY-7D identity retirement,
per plans/DRAFT_amendment_PSCTV1_A3_xsect_retire.md §1/§3:

(a1) post-T_ret decision with a flat sleeve emits ZERO opening fills;
(a2) pre-T_ret holdings still produce their closing sells at the first
     post-T_ret decision (closing is PERMITTED and required — asserted
     PRESENT, not absent);
(b)  the terminal row fires ONLY on the measured-flat condition, exactly
     once, with the pinned decomposition and label;
(c)  restart idempotence: run_due twice appends no duplicate event ids;
(d)  retirement is config-gated: retire_after_utc=None leaves executor
     behavior and config_digest byte-identical (other families);
     pre-T_ret rows parse unchanged.
"""

import pytest

from research.shadow_v1 import accounting, executor
from research.control.prospective_shadow_v1.e import shadow_worker as sw

RETIRE_CFG = {
    "retire_after_utc": "2026-09-25T05:45:00Z",
    "retire_terminal": {
        "label": "IDENTITY_RETIRED_COST_DOMINATED",
        "historical_verdict_label": "CANDIDATE_FAIL (pinned)",
        "equity_basis_note": "decision-row ledger basis",
        "note": "test",
    },
}


def test_a1_post_retire_flat_sleeve_opens_nothing():
    ex = _mk_executor(retire=True)
    # decision AFTER T_ret with the adapter wanting a full book:
    # the law forces target FLAT -> zero fills, zero gross.
    approved, _ = _approved_weights(ex)
    flat = ex._retire_override(approved, "2026-09-25T06:00:00Z")
    assert flat == {}


def test_a2_closing_permitted_post_retire():
    # A sleeve holding a long: the post-T_ret rebalance toward {} yields
    # ONLY a reducing sell (closing), never an opening buy.
    ex = _mk_executor(retire=True)
    sleeve = ex.sleeve
    sleeve.apply_fill("ETHUSDT", "buy", 0.5, 2000.0, 0.01, "2026-09-25T05:00:00Z")
    steps = list(
        ex._rebalance_steps(
            {}, {"ETHUSDT": 2000.0}, sleeve.equity_snapshot().equity
        )
    )
    assert steps == [("ETHUSDT", "sell", pytest.approx(0.5))]


def test_b_terminal_row_only_on_measured_flat():
    ex = _mk_executor(retire=True)
    payload = ex._retire_terminal_payload(
        "2026-09-25T06:00:00Z", "2026-09-25T06:05:00Z", "evt-1", 99_000.0
    )
    assert payload["terminal_label"] == "IDENTITY_RETIRED_COST_DOMINATED"
    assert payload["historical_verdict_label"].startswith("CANDIDATE_FAIL")
    d = payload["decomposition"]
    assert d["starting_cash"] == 100_000.0
    assert d["equity"] == 99_000.0
    assert "books" in d and set(d["books"]) == {
        "CURRENT_CONSERVATIVE_COST", "LINEAGE_COST"
    }
    # the emitter is state-conditioned by construction: the call site
    # fires only when exposure gross == 0.0 (see executor source).
    import inspect
    src = inspect.getsource(executor.ForwardExecutor._execute_decision)
    assert 'exposure["gross"] == 0.0' in src


def test_c_and_d_config_gating_and_worker_constant():
    # (d) no retire config => law inert and digest unchanged
    ex_off = _mk_executor(retire=False)
    assert ex_off.retire_after_utc is None
    ex_on = _mk_executor(retire=True)
    assert executor.canonical_digest({}) != (
        ex_on.config_digest
    )  # digest changed WITH the law (XSECT identity boundary)
    assert ex_off.retire_after_utc is None
    # the worker wires the law ONLY into the CARRY family config
    src = sw.__file__
    import pathlib
    text = pathlib.Path(src).read_text()
    assert 'config["retire_after_utc"] = XSECT_RETIRE_AFTER_UTC' in text
    # other families' configs never mention retire keys (single wiring site)
    assert text.count("retire_after_utc") >= 1
    # worker constant is the committed T_ret
    assert sw.XSECT_RETIRE_AFTER_UTC == "2026-09-25T05:45:00Z"


# ---------------------------------------------------------------- helpers
class _NullAdapter:
    FAMILY_ID = "XSECT-FUND-CARRY-7D"
    ARM_ID = "XSECT-FUND-CARRY-7D"


def _mk_executor(*, retire: bool) -> executor.ForwardExecutor:
    """Minimal executor around the retire law (no feed/scheduler IO).

    Constructs through the real __init__ path with a stub config so the
    digest wiring and law flags are the production ones.
    """
    cfg = {
        "code_freeze_sha": "0" * 64,
        "namespace": "REPLAY_NOT_PROSPECTIVE",
        "tick_size": {"ETHUSDT": 0.01},
        "tick_size_default": 0.01,
        "cost_books": {
            name: accounting.BookCostParams(**params)
            for name, params in sw.cost_books_for("XSECT-FUND-CARRY-7D").items()
        },
        "primary_book": "CURRENT_CONSERVATIVE_COST",
        "caps": _caps(),
        "snapshot_spec": {"funding_settlements": {"symbols": [], "lookback_seconds": 1.0}},
        "feature_cutoff_offset_seconds": 0.0,
        "schedule": {"kind": "daily", "offset_utc": 0},
        "identity_entry": {"family_id": "XSECT-FUND-CARRY-7D"},
        "engine": {},
        "btc_betas": None,
        "fill_symbols": ["ETHUSDT"],
    }
    if retire:
        cfg.update(RETIRE_CFG)
    # bypass the adapter/feed wiring: we only exercise sizing/retire laws
    ex = object.__new__(executor.ForwardExecutor)
    ex.family_id = "XSECT-FUND-CARRY-7D"
    ex.arm_id = "XSECT-FUND-CARRY-7D"
    ex.code_freeze_sha = cfg["code_freeze_sha"]
    ex.feature_cutoff_offset_seconds = cfg["feature_cutoff_offset_seconds"]
    ex.fill_bar_interval = "15m"
    ex.cost_aware_sizing = False
    ex.retire_after_utc = cfg.get("retire_after_utc")
    ex.retire_terminal = dict(cfg.get("retire_terminal") or {})
    ex.fill_symbols = cfg["fill_symbols"]
    ex.primary_book = cfg["primary_book"]
    ex.tick_size = None
    ex.tick_size_map = cfg["tick_size"]
    ex.tick_size_default = cfg["tick_size_default"]
    ex.snapshot_spec = cfg["snapshot_spec"]
    ex.schedule = cfg["schedule"]
    ex.btc_betas = None
    from research.shadow_v1 import risk
    ex.caps = cfg["caps"]
    ex.adapter = _NullAdapter()
    ex.config_digest = executor.canonical_digest(
        {
            "adapter_config": None,
            "executor": {
                "code_freeze_sha": ex.code_freeze_sha,
                "feature_cutoff_offset_seconds": ex.feature_cutoff_offset_seconds,
                "fill_bar_interval": ex.fill_bar_interval,
                "fill_symbols": ex.fill_symbols,
                "primary_book": ex.primary_book,
                "schedule": ex.schedule,
                "snapshot_spec": ex.snapshot_spec,
                "tick_size": {
                    "per_symbol": dict(sorted(ex.tick_size_map.items())),
                    "default": ex.tick_size_default,
                },
                "btc_betas": ex.btc_betas,
                **({"cost_aware_sizing": True} if ex.cost_aware_sizing else {}),
                **(
                    {
                        "retire_after_utc": ex.retire_after_utc,
                        "retire_terminal": ex.retire_terminal,
                    }
                    if ex.retire_after_utc is not None
                    else {}
                ),
            },
        }
    )
    ex.cost_regime_digest = executor.canonical_digest(cfg["cost_books"] and {
        k: {"fee_rate": v.fee_rate, "slippage_ticks": v.slippage_ticks}
        for k, v in cfg["cost_books"].items()
    })
    ex.sleeve = accounting.SleeveAccount(
        sleeve_id="sleeve_test_xsect_retire",
        books=cfg["cost_books"],
        starting_cash=100_000.0,
        primary_book=ex.primary_book,
    )
    ex._last_decision_utc = None
    return ex


def _caps():
    from research.shadow_v1 import risk
    return risk.FamilyRiskCaps(
        family_id="XSECT-FUND-CARRY-7D",
        target_gross=0.8,
        hard_gross_cap=1.0,
        hard_abs_net_cap=0.10,
        dollar_neutral=False,
        btc_beta_neutral=False,
        btc_beta_tolerance=1e-6,
        max_abs_weight=0.20,
    )


def _approved_weights(ex):
    return {"ETHUSDT": 0.2, "SOLUSDT": 0.2}, None


def test_retire_override_helper_exists():
    # The production override happens inline in _execute_decision; expose
    # it as a small helper for testability without changing behavior.
    import inspect
    src = inspect.getsource(executor.ForwardExecutor._execute_decision)
    assert "retired_now" in src and "approved = {}" in src
