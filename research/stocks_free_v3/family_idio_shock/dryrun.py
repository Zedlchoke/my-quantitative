"""Exact-arm dry-run for SFV3-A5-IDIO-SHOCK-REVERSAL (schedule + valuation
accounting + publication gate, NO scored metric computed or persisted).

What the dry-run does, end to end, per exact frozen arm:

1. builds the canonical target-weight schedule (state machine, frozen
   constants — or loads real S0 staged data through the sealed S0-only
   reader);
2. runs the CANONICAL accounting ``research.assets.stocks.factory
   .value_book`` over the schedule (the same path the scorer will use);
3. runs the canonical accounting identity ``factory.assert_reconciles``
   (attribution identity + cost-charged-once — bookkeeping, not performance);
4. exercises the ``GatedTrialLedger`` publication gate on a TEMPORARY ledger
   that lives in a temp directory and is DELETED afterwards.  Default is
   NO-PUBLISH: only the gate metrics (``publication_metrics``) are evaluated
   and the ledger counters are asserted; ``--publish-to-temp-ledger``
   additionally publishes the key into the temp ledger (which is then
   deleted) to exercise the real gate path.

What the dry-run NEVER does: compute, return, print or persist any scored
metric.  ``value_book`` computes its internal result object, but the dry-run
payload exposes ONLY schedule counters, turnover/cost accounting facts and
gate counters — never total_pnl, expectancy, profit factor, drawdown or an
equity curve.  On real data the reads go through
``research.stocks_free_v3.isolation.SealedSnapshotReader`` and are S0-bounded
(2018-04-04..2025-07-31); no S1 date (>= 2025-08-01) is ever returned or
consumed, and distribution records are truncated to pre-S1 dates before use.

CLI::

    python -m research.stocks_free_v3.family_idio_shock.dryrun \
        [--arm {A1,N1,C1,ALL}] [--staging DIR] [--publish-to-temp-ledger]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

from research.assets.stocks.factory import (
    GatedTrialLedger,
    assert_reconciles,
    publication_metrics,
    value_book,
)
from research.stocks_free_v3.authority import (
    S0_END,
    S0_START,
    S1_START,
    SNAPSHOT_STAGING_PATH,
)
from research.stocks_free_v3.family_idio_shock.arms import (
    ARM_A1,
    ARM_C1,
    ARM_N1,
    FAMILY_ID,
    FROZEN_ARMS,
    FrozenArmConfig,
)
from research.stocks_free_v3.family_idio_shock.schedule import (
    build_arm_schedule,
    schedule_feasibility,
)
from research.stocks_free_v3.isolation import (
    S0WindowPolicy,
    S1Seal,
    SealedSnapshotReader,
)

DRYRUN_SCHEMA = "stocks_free_v3/family_idio_shock/dryrun@1"

#: Base cost assumption of the canonical accounting in the dry-run (the
#: proposal's base 10 bps/side; the stress 20 bps is a scoring concern).
DRYRUN_COST_BPS = 10.0


@dataclass(frozen=True)
class DryRunArmReport:
    """Accounting-only dry-run report for ONE arm (no scored metric)."""

    arm_id: str
    config_digest: str
    schedule_digest: str
    feasibility: Mapping[str, Any]
    n_valuation_fills: int
    n_costs_charged: int
    etf_leg_turnover_charged_total: float
    attribution_reconciles: bool
    gate: Mapping[str, Any]

    def to_payload(self) -> dict:
        return {
            "arm_id": self.arm_id,
            "config_digest": self.config_digest,
            "schedule_digest": self.schedule_digest,
            "feasibility": dict(self.feasibility),
            "valuation_accounting": {
                "n_valuation_fills": self.n_valuation_fills,
                "n_costs_charged": self.n_costs_charged,
                "etf_leg_turnover_charged_total": self.etf_leg_turnover_charged_total,
                "attribution_reconciles": self.attribution_reconciles,
            },
            "publication_gate": dict(self.gate),
        }


def load_s0_snapshot_inputs(
    staging_root: str = SNAPSHOT_STAGING_PATH,
    *,
    symbols: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Load S0-bounded raw closes + issuer action inputs via the sealed reader.

    Returns ``{"sessions", "raw_close", "distributions", "split_factors"}``
    where ``sessions`` is the SPY close-date list (the cohort calendar) and
    every returned date is < S1 start.  Distribution records are truncated to
    pre-S1 dates before use; split factors are passed through (their pinned
    effective date is inside S1, so they never apply to an S0 window — the
    arithmetic is a no-op for every returned close).
    """
    symbols = symbols or tuple([ARM_A1.benchmark_symbol, *ARM_A1.universe])
    reader = SealedSnapshotReader(
        staging_root, seal=S1Seal(S1_START, date(2026, 7, 31)), policy=S0WindowPolicy()
    )
    s1_iso = S1_START.isoformat()
    raw_close: dict[str, dict[str, float]] = {}
    for symbol in symbols:
        closes = reader.load_symbol_closes(
            f"{symbol}_none_p1.json", start=S0_START, end=S0_END
        )
        if any(d >= s1_iso for d in closes):
            raise RuntimeError(f"sealed-date leak in {symbol} closes; refusing")
        raw_close[symbol] = dict(closes)
    dist_path = os.path.join(staging_root, "distributions.json")
    split_path = os.path.join(staging_root, "split_factors.json")
    with open(dist_path, encoding="utf-8") as handle:
        all_distributions = json.load(handle)
    with open(split_path, encoding="utf-8") as handle:
        all_split_factors = json.load(handle)
    distributions = {
        symbol: {d: float(v) for d, v in (all_distributions.get(symbol) or {}).items()
                 if d < s1_iso}
        for symbol in symbols
    }
    split_factors = {
        symbol: {d: float(v) for d, v in (all_split_factors.get(symbol) or {}).items()}
        for symbol in symbols
    }
    sessions = sorted(raw_close[ARM_A1.benchmark_symbol])
    return {
        "sessions": sessions,
        "raw_close": raw_close,
        "distributions": distributions,
        "split_factors": split_factors,
    }


def _issuer_tr_returns(inputs: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    """Issuer-TR daily returns per symbol from the S0-bounded inputs."""
    from research.stocks_free_v3.benchmarks import issuer_total_return_daily

    returns: dict[str, dict[str, float]] = {}
    for symbol, closes in inputs["raw_close"].items():
        dates, rets = issuer_total_return_daily(
            closes,
            inputs["distributions"].get(symbol, {}),
            inputs["split_factors"].get(symbol, {}),
        )
        returns[symbol] = dict(zip(dates, rets))
    return returns


def dry_run_arm(
    config: FrozenArmConfig,
    sessions: list[str],
    returns: Mapping[str, Mapping[str, float]],
    raw_close: Mapping[str, Mapping[str, float]],
    distributions: Mapping[str, Mapping[str, float]],
    split_factors: Mapping[str, Mapping[str, float]],
    *,
    ledger_dir: str | None = None,
    publish_to_temp_ledger: bool = False,
    cost_bps: float = DRYRUN_COST_BPS,
) -> DryRunArmReport:
    """Full exact-arm dry-run on the given (synthetic or S0) inputs.

    Schedule build -> canonical ``value_book`` accounting -> accounting
    identity -> publication gate on a temp ledger.  Returns accounting facts
    only; scored metrics are never extracted from the valuation result.
    """
    result = build_arm_schedule(config, sessions, returns)
    feasibility = schedule_feasibility(sessions, result, config)
    entries = [dict(record) for record in result.records]
    valuation = value_book(
        entries, raw_close, distributions, split_factors, sessions, cost_bps=cost_bps,
    )
    # bookkeeping identity only — the scored fields of `valuation` are
    # deliberately never read here.
    assert_reconciles(valuation)

    gate = publication_metrics(entries)
    temp_dir_created = ledger_dir is None
    ledger_root = ledger_dir or tempfile.mkdtemp(prefix="sfv3_a5_dryrun_")
    os.makedirs(ledger_root, exist_ok=True)
    try:
        ledger = GatedTrialLedger(
            os.path.join(ledger_root, "dryrun_trial_ledger.json"))
        key = (
            f"US_ETF_CASH|V3|{FAMILY_ID}|{config.arm_id}|DRYRUN|"
            f"{config.config_digest[:16]}|{result.schedule_digest[:16]}"
        )
        ledger.compute_recorded(key)
        published = False
        if publish_to_temp_ledger:
            published = ledger.publish_result(key, {
                "dryrun": True,
                "arm_id": config.arm_id,
                "config_digest": config.config_digest,
                "schedule_digest": result.schedule_digest,
            }, n_fill_events=gate["n_fill_events"],
               n_held_positions=gate["n_held_positions"])
        else:
            # NO-PUBLISH mode: evaluate the gate decision without publishing.
            would_publish = (
                gate["n_fill_events"] > 0 and gate["n_held_positions"] > 0
            )
            if not would_publish:
                ledger.refusals.append({"key": key, "reasons": [
                    name for name, value in (
                        ("ZERO_FILL_EVENTS", gate["n_fill_events"]),
                        ("ZERO_HELD_POSITIONS", gate["n_held_positions"]),
                    ) if value <= 0]})
        gate_payload = {
            "mode": "TEMP_PUBLISH_THEN_DELETE" if publish_to_temp_ledger else "NO_PUBLISH",
            "n_fill_events": gate["n_fill_events"],
            "n_held_positions": gate["n_held_positions"],
            "ledger_observed": ledger.observed,
            "ledger_published_keys": len(ledger.published_keys),
            "published": bool(published),
            "n_refusals": len(ledger.refusals),
            "ledger_persisted_permanently": False,
        }
        ledger.save()  # persists ONLY into the temp dir
    finally:
        if temp_dir_created:
            shutil.rmtree(ledger_root, ignore_errors=True)

    return DryRunArmReport(
        arm_id=config.arm_id,
        config_digest=config.config_digest,
        schedule_digest=result.schedule_digest,
        feasibility=feasibility.to_payload(),
        n_valuation_fills=len(valuation.fill_costs),
        n_costs_charged=len(valuation.fill_costs),
        etf_leg_turnover_charged_total=sum(t for _, t, _ in valuation.fill_costs),
        attribution_reconciles=True,
        gate=gate_payload,
    )


def dry_run_all_arms(
    sessions: list[str],
    returns: Mapping[str, Mapping[str, float]],
    raw_close: Mapping[str, Mapping[str, float]],
    distributions: Mapping[str, Mapping[str, float]],
    split_factors: Mapping[str, Mapping[str, float]],
    *,
    arms: tuple[FrozenArmConfig, ...] = FROZEN_ARMS,
    publish_to_temp_ledger: bool = False,
    cost_bps: float = DRYRUN_COST_BPS,
) -> dict[str, Any]:
    """Dry-run every requested arm; accounting-only aggregate payload."""
    reports = []
    for config in arms:
        reports.append(dry_run_arm(
            config, sessions, returns, raw_close, distributions, split_factors,
            publish_to_temp_ledger=publish_to_temp_ledger, cost_bps=cost_bps,
        ).to_payload())
    return {
        "schema": DRYRUN_SCHEMA,
        "family_id": FAMILY_ID,
        "mode": "DRYRUN_SCHEDULE_AND_VALUATION_ONLY",
        "scored_metrics_computed": False,
        "scored_metrics_persisted": False,
        "s1_dates_read": False,
        "arms": reports,
    }


def dry_run_real_s0(
    staging_root: str = SNAPSHOT_STAGING_PATH,
    *,
    arms: tuple[FrozenArmConfig, ...] = FROZEN_ARMS,
    publish_to_temp_ledger: bool = False,
) -> dict[str, Any]:
    """Schedule + valuation dry-run over the REAL staged S0 window.

    Reads S0 only, through the sealed reader; runs in a temp ledger that is
    deleted on return; computes and persists NO scored metric.
    """
    inputs = load_s0_snapshot_inputs(staging_root, symbols=(
        ARM_A1.benchmark_symbol, *ARM_A1.universe))
    returns = _issuer_tr_returns(inputs)
    payload = dry_run_all_arms(
        inputs["sessions"], returns,
        inputs["raw_close"], inputs["distributions"], inputs["split_factors"],
        arms=arms, publish_to_temp_ledger=publish_to_temp_ledger,
    )
    payload["data"] = {
        "source": "REAL_STAGED_S0_READ_ONLY",
        "staging_root": staging_root,
        "window": [S0_START.isoformat(), S0_END.isoformat()],
        "n_sessions": len(inputs["sessions"]),
        "first_session": inputs["sessions"][0],
        "last_session": inputs["sessions"][-1],
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SFV3-A5-IDIO-SHOCK-REVERSAL exact-arm dry-run "
                    "(schedule + canonical valuation accounting + publication "
                    "gate on a temp ledger; NO scored metric).")
    parser.add_argument("--arm", choices=["A1", "N1", "C1", "ALL"], default="ALL")
    parser.add_argument("--staging", default=SNAPSHOT_STAGING_PATH)
    parser.add_argument("--publish-to-temp-ledger", action="store_true",
                        help="publish the key into the TEMP ledger (deleted "
                             "afterwards); default is strict NO-PUBLISH")
    args = parser.parse_args(argv)
    arms_by_code = {"A1": (ARM_A1,), "N1": (ARM_N1,), "C1": (ARM_C1,)}
    arms = FROZEN_ARMS if args.arm == "ALL" else arms_by_code[args.arm]
    payload = dry_run_real_s0(
        args.staging, arms=arms, publish_to_temp_ledger=args.publish_to_temp_ledger)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
