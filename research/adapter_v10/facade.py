"""Frozen QA-contract facade over the generic adapter (sprint V10P-R, A1 integration).

This module is the surface the independent acceptance lane imports:
``ADAPTER_INTERFACE_VERSION``, :class:`GenericRunnerV10`,
:func:`checked_funding_accrual`, :func:`cache_decision`,
:func:`resource_cap_report`, :func:`validate_resource_cap_report`.

It is a thin, additive layer over the G1 modules already merged (protocol /
converters / metrics / stress / benchmarks / publish / runner): every semantic
below is the frozen QA contract, expressed with the repo's own primitives
(``contract_v10`` floors, ``pit_hooks_v10`` settlement normalisation,
``global_ledger`` append-only publication).  Nothing here reinterprets a
contract sentence; anything ambiguous is refused (fail closed) instead of
guessed.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from research.adapter_v10.converters import normalise_target_book
from research.adapter_v10.hashes import payload_sha256
from research.adapter_v10.protocol import (
    DEFAULT_WEIGHT_CAP_MAX,
    ContractViolation,
    FillStatusVocabulary,
)
from research.cache_v10 import SharedCacheMergeGate
from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    STRESS_MATRIX_V10,
    TAKER_FEE_FLOOR_BPS_V10,
)
from research.global_ledger import append_verified, snapshot
from research.pit_hooks_v10 import normalize_info_series

#: Version of the interface frozen by the independent acceptance lane.
ADAPTER_INTERFACE_VERSION = "v10.adapter.interface.v1"

#: Frozen terminal-boundary vocabulary of the repo's rebalance schedules
#: (mirrored verbatim; parity with the panel module is asserted by tests so a
#: drift can never pass silently while generic paths stay family-import free).
FORCE_FLAT_STATUS = "FORCE_FLAT"
FORCE_FLAT_REASON = "force_flat_final_scored_window_boundary"

#: Verdicts that represent a passing scored cell (anything else must not be
#: published -- a partial/failed pre-score is never a publication).
SCORE_PASSING_VERDICTS: tuple[str, ...] = ("PASS", "CELL_RESULT")
PUBLISHED_CELL_KIND = "CELL_RESULT"
SIGN_CONVENTION_LONG_PAYS_POSITIVE = "LONG_PAYS_POSITIVE_RATE"

#: Environment flags that must never override an absent cache decision.
CACHE_ENV_FLAGS: tuple[str, ...] = ("V10_CACHE_ENABLED", "ORCA_V10_CACHE_ENABLED")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _json_safe(value: Any) -> Any:
    """Recursively normalise into plain JSON containers (deterministic)."""
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractViolation("non-finite float cannot be serialised")
        return value
    if hasattr(value, "__dict__") and not callable(value):
        return _json_safe(dict(vars(value)))
    return str(value)


def _round_or_none(value: Optional[float], digits: int = 12) -> Optional[float]:
    return None if value is None else round(float(value), digits)


def _mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return math.fsum(values) / len(values)


def _profit_factor(values: Sequence[float]) -> tuple[Optional[float], bool]:
    """``sum(wins)/abs(sum(losses))``; undefined (never faked) with no loss."""
    if not values:
        return None, True
    wins = math.fsum(v for v in values if v > 0.0)
    losses = abs(math.fsum(v for v in values if v <= 0.0))
    if losses == 0.0:
        return None, True
    return wins / losses, False


def _relative_max_drawdown(values: Sequence[float]) -> float:
    """Worst relative decline of the compounded equity path (``1 - eq/peak``)."""
    equity, peak, worst = 1.0, 1.0, 0.0
    for value in values:
        equity *= 1.0 + float(value)
        peak = max(peak, equity)
        worst = max(worst, 1.0 - equity / peak)
    return worst


def _stress_signature(stress: Any, *, default_ticks: int) -> dict[str, Any]:
    """Effective stress parameters (frozen defaults, never looser)."""
    signature: dict[str, Any] = {
        "fee_multiplier": 1.0,
        "tick_slip_ticks": int(default_ticks),
        "event_delay_events": 0,
        "drop_symbols": [],
        "dropped_fold_index": None,
    }
    if stress is None:
        return signature
    if hasattr(stress, "fee_multiplier"):
        signature["fee_multiplier"] = float(stress.fee_multiplier)
        signature["tick_slip_ticks"] = int(stress.tick_slip_ticks)
        signature["event_delay_events"] = int(stress.event_delay_events)
        signature["drop_symbols"] = [str(s) for s in (stress.drop_symbols or ())]
        signature["dropped_fold_index"] = stress.dropped_fold_index
        return signature
    if isinstance(stress, Mapping):
        signature["fee_multiplier"] = float(stress.get("fee_multiplier", 1.0))
        signature["tick_slip_ticks"] = int(
            stress.get("tick_slip_ticks", signature["tick_slip_ticks"])
        )
        signature["event_delay_events"] = int(stress.get("event_delay_events", 0))
        signature["drop_symbols"] = [str(s) for s in (stress.get("drop_symbols") or ())]
        signature["dropped_fold_index"] = stress.get("dropped_fold_index")
        return signature
    raise ContractViolation(f"unsupported stress object: {type(stress)!r}")


def _load_optional_payload(payload_or_path: Any) -> tuple[Optional[Mapping[str, Any]], str]:
    """Resolve a decision payload, a JSON path, or an absent decision."""
    if payload_or_path is None:
        return None, "absent"
    if isinstance(payload_or_path, Mapping):
        return dict(payload_or_path), "inline_payload"
    if isinstance(payload_or_path, (str, Path)):
        text = str(payload_or_path).strip()
        if not text:
            return None, "absent"
        path = Path(text)
        if not path.is_file():
            return None, f"path_not_found:{text}"
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ContractViolation(f"unreadable decision artifact {text}: {exc}") from exc
        if not isinstance(loaded, Mapping):
            raise ContractViolation(f"decision artifact not an object: {text}")
        return dict(loaded), f"file:{text}"
    raise ContractViolation(
        f"unsupported payload/path type: {type(payload_or_path)!r}"
    )


def _require_payload(payload_or_path: Any) -> Mapping[str, Any]:
    payload, source = _load_optional_payload(payload_or_path)
    if payload is None:
        raise ContractViolation(
            f"required decision payload unavailable (source={source})"
        )
    return payload


def _finite_positive(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0.0
    )


# --------------------------------------------------------------------------- #
# Facade class
# --------------------------------------------------------------------------- #
class GenericRunnerV10:
    """Strategy-facing driver for the frozen BG-1/BG-2/BG-4/BG-5/BG-6 contract.

    ``strategy`` must expose ``strategy_id``, ``config`` and
    ``schedule_provider`` through the plugin protocol (no family identifiers,
    ever); ``config`` carries the cohort/window/cap/cost floors for this run.
    """

    def __init__(self, *, strategy: Any, config: Optional[Mapping[str, Any]] = None) -> None:
        if strategy is None:
            raise ContractViolation("strategy is required")
        strategy_id = getattr(strategy, "strategy_id", None)
        if not isinstance(strategy_id, str) or not strategy_id.strip():
            raise ContractViolation("strategy.strategy_id must be a non-empty string")
        if not hasattr(strategy, "schedule_provider"):
            raise ContractViolation("strategy.schedule_provider is required")
        resolved_config = config if config is not None else getattr(strategy, "config", None)
        if not isinstance(resolved_config, Mapping):
            raise ContractViolation("config must be a mapping")
        self._strategy = strategy
        self._config = dict(resolved_config)
        self.strategy_id = str(strategy_id)
        self.schedule_provider = getattr(strategy, "schedule_provider")

    # ------------------------------------------------------------------ #
    # BG-1 fold metrics
    # ------------------------------------------------------------------ #
    def compute_fold_metrics(
        self, unit_gross_returns_by_fold: Mapping[str, Sequence[float]]
    ) -> dict[str, Any]:
        """Fold-level expectancy / PF / MDD plus the pooled aggregate.

        Frozen conventions: expectancy is the arithmetic mean of unit-gross net
        returns; profit factor is ``sum(wins)/abs(sum(losses))`` (flagged
        undefined, never faked, when no losing day exists); max drawdown is the
        worst relative decline of the compounded equity path.
        """
        if not isinstance(unit_gross_returns_by_fold, Mapping) or not unit_gross_returns_by_fold:
            raise ContractViolation("unit_gross_returns_by_fold must be a non-empty mapping")
        folds: list[dict[str, Any]] = []
        pooled: list[float] = []
        for fold_id, returns in unit_gross_returns_by_fold.items():
            values = [float(v) for v in returns]
            if not values:
                raise ContractViolation(f"fold {fold_id!r} carries no returns")
            if any(not math.isfinite(v) for v in values):
                raise ContractViolation(f"fold {fold_id!r} carries a non-finite return")
            factor, undefined = _profit_factor(values)
            pooled.extend(values)
            folds.append(
                {
                    "fold_id": str(fold_id),
                    "n_days": len(values),
                    "expectancy": _mean(values),
                    "profit_factor": factor,
                    "profit_factor_is_undefined": undefined,
                    "max_drawdown": _relative_max_drawdown(values),
                    "net_return_sum": math.fsum(values),
                }
            )
            del returns
        factor, undefined = _profit_factor(pooled)
        aggregate = {
            "fold_id": "POOLED",
            "n_days": len(pooled),
            "expectancy": _mean(pooled),
            "profit_factor": factor,
            "profit_factor_is_undefined": undefined,
            "max_drawdown": _relative_max_drawdown(pooled),
            "net_return_sum": math.fsum(pooled),
        }
        return {
            "folds": folds,
            "aggregate": aggregate,
            "payload_sha256": payload_sha256({"folds": folds, "aggregate": aggregate}),
        }

    # ------------------------------------------------------------------ #
    # BG-2 target book -> fill / scoring payload
    # ------------------------------------------------------------------ #
    def convert_target_book(
        self,
        decision_ns: int,
        target_book: Any,
        prior_weights: Optional[Mapping[str, float]] = None,
        events: Optional[Mapping[str, Any]] = None,
        tick_sizes: Optional[Mapping[str, float]] = None,
        stress: Any = None,
        force_flat_boundary_ns: Optional[int] = None,
    ) -> dict[str, Any]:
        """One decision instant -> fill-level payload (frozen vocabulary).

        ``events`` maps symbol -> fill event (``price`` / ``fill_open_ns`` /
        ``fill_bar_close_ns`` / ``event_offset``) as produced by the repo's
        strict-later fill resolver. At the force-flat boundary the supplied
        targets are IGNORED: every leg's target becomes 0 and the whole prior
        book is closed with the frozen reason code.
        """
        decision = int(decision_ns)
        is_force_flat = (
            force_flat_boundary_ns is not None and int(force_flat_boundary_ns) == decision
        )
        cap = float(self._config.get("cap", DEFAULT_WEIGHT_CAP_MAX))
        book = normalise_target_book(
            target_book if not is_force_flat else {}, decision_ns=decision, cap_max=cap
        )
        targets = book.as_mapping()
        prior = {
            str(sym): float(weight)
            for sym, weight in dict(prior_weights or {}).items()
        }
        signature = _stress_signature(
            stress,
            default_ticks=int(
                self._config.get("adverse_tick_slip", ADVERSE_TICKS_SLIPPAGE_FLOOR_V10)
            ),
        )
        fee_bps = float(self._config.get("taker_fee_bps", TAKER_FEE_FLOOR_BPS_V10))
        ticks_map = {str(k): float(v) for k, v in (tick_sizes or {}).items()}

        def _rate(symbol: str, price: float) -> float:
            rate = fee_bps * 1e-4 * float(signature["fee_multiplier"])
            slip = int(signature["tick_slip_ticks"])
            if slip:
                size = ticks_map.get(symbol)
                if size is None or not _finite_positive(size):
                    raise ContractViolation(
                        f"tick slippage requested without a positive tick_size for {symbol}"
                    )
                rate += slip * size / float(price)
            return rate

        fills: list[dict[str, Any]] = []
        turnover = 0.0
        cost = 0.0
        for symbol in sorted(set(prior) | set(targets)):
            target = float(targets.get(symbol, 0.0))
            prior_weight = float(prior.get(symbol, 0.0))
            delta = target - prior_weight
            turnover += abs(delta)
            event = (events or {}).get(symbol)
            row: dict[str, Any] = {
                "symbol": symbol,
                "decision_ns": decision,
                "target_weight": round(target, 12),
                "prior_weight": round(prior_weight, 12),
                "signed_weight_change": round(delta, 12),
                "event_offset": 0,
                "price": None,
                "fill_open_ns": None,
                "fill_bar_close_ns": None,
                "status": FillStatusVocabulary.NO_EVENT,
                "applied": False,
            }
            if abs(delta) > 0.0 and event is None:
                raise ContractViolation(
                    f"no strict-later fill event for {symbol} at {decision}; "
                    "an unfilled leg can never be silently scored"
                )
            if event is not None:
                price = float(getattr(event, "price"))
                if not _finite_positive(price):
                    raise ContractViolation(f"invalid fill price for {symbol}: {price!r}")
                row.update(
                    {
                        "status": FillStatusVocabulary.APPLIED,
                        "applied": True,
                        "price": price,
                        "fill_open_ns": int(getattr(event, "fill_open_ns")),
                        "fill_bar_close_ns": int(getattr(event, "fill_bar_close_ns")),
                        "event_offset": int(getattr(event, "event_offset", 0)),
                    }
                )
                if abs(delta) > 0.0:
                    cost += abs(delta) * _rate(symbol, price)
            fills.append(row)

        return {
            "decision_ns": decision,
            "is_force_flat_boundary": bool(is_force_flat),
            "force_flat_reason": FORCE_FLAT_REASON if is_force_flat else None,
            "fills": fills,
            "weights": {sym: round(w, 12) for sym, w in sorted(targets.items()) if w != 0.0},
            "turnover_one_side": round(turnover, 12),
            "cost_per_unit_gross": round(cost, 12),
            "gross_realised": round(math.fsum(abs(w) for w in targets.values()), 12),
            "net_exposure": round(math.fsum(targets.values()), 12),
            "stress": signature,
            "cap_max": cap,
        }

    # ------------------------------------------------------------------ #
    # BG-2 schedule finalisation
    # ------------------------------------------------------------------ #
    def schedule(self, scenario: Mapping[str, Any]) -> dict[str, Any]:
        """Ensure the schedule ends with the mandatory terminal force-flat row."""
        if not isinstance(scenario, Mapping):
            raise ContractViolation("scenario must be a mapping with rows")
        rows = [dict(row) for row in (scenario.get("rows") or [])]
        boundary = scenario.get("final_boundary_ns")
        if not rows:
            raise ContractViolation("scenario needs at least one opening row")
        if boundary is None:
            raise ContractViolation("scenario needs final_boundary_ns")
        boundary = int(boundary)
        last = rows[-1]
        if str(last.get("action", "")) != FORCE_FLAT_STATUS:
            closing = self._closing_fills(last)
            rows.append(
                {
                    "action": FORCE_FLAT_STATUS,
                    "decision_ns": boundary,
                    "status": FORCE_FLAT_STATUS,
                    "reason_code": FORCE_FLAT_REASON,
                    "weights": [],
                    "fills": closing,
                    "turnover_one_side": round(
                        math.fsum(abs(float(leg["prior_weight"])) for leg in closing), 12
                    ),
                    "carried_forward": False,
                }
            )
        else:
            last["action"] = FORCE_FLAT_STATUS
            last["reason_code"] = FORCE_FLAT_REASON
            last["weights"] = []
        return {
            "schema_version": ADAPTER_INTERFACE_VERSION,
            "rows": rows,
            "final_boundary_ns": boundary,
            "n_rows": len(rows),
        }

    @staticmethod
    def _closing_fills(opening_row: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Close-out fills for the prior book, priced from the opening sweep."""
        weights = dict(opening_row.get("weights") or [])
        prices = {
            str(entry.get("symbol")): entry.get("price")
            for entry in (opening_row.get("fills") or [])
            if isinstance(entry, Mapping) and entry.get("symbol") is not None
        }
        closing: list[dict[str, Any]] = []
        for symbol, weight in sorted(weights.items()):
            prior_weight = float(weight)
            price = prices.get(str(symbol))
            closing.append(
                {
                    "symbol": str(symbol),
                    "decision_ns": int(opening_row.get("decision_ns", 0)),
                    "target_weight": 0.0,
                    "prior_weight": round(prior_weight, 12),
                    "signed_weight_change": round(-prior_weight, 12),
                    "event_offset": 0,
                    "price": None if price is None else float(price),
                    "fill_open_ns": None,
                    "fill_bar_close_ns": None,
                    "status": FillStatusVocabulary.APPLIED if price is not None else FillStatusVocabulary.NO_EVENT,
                    "applied": price is not None,
                }
            )
        return closing

    def finalise_schedule_payload(self, schedule: Mapping[str, Any]) -> dict[str, Any]:
        """Deterministic artifact payload for one schedule (stable hash).

        Frozen invariant: the payload is the JSON-normalised schedule ITSELF, so
        ``payload_sha256(schedule) == payload_sha256(finalised)`` by construction
        and no key is ever added or dropped on the way out.
        """
        if not isinstance(schedule, Mapping):
            raise ContractViolation("schedule must be a mapping")
        return _json_safe(schedule)

    # ------------------------------------------------------------------ #
    # BG-4 stress surface
    # ------------------------------------------------------------------ #
    def stress_variants(
        self, cohort: Sequence[str], fold_labels: Sequence[str]
    ) -> list[dict[str, Any]]:
        """Full preregistered surface: baseline + the frozen five, expanded."""
        symbols = sorted({str(sym) for sym in cohort})
        labels = [str(label) for label in fold_labels]
        if not symbols:
            raise ContractViolation("stress surface needs a non-empty cohort")
        if not labels:
            raise ContractViolation("stress surface needs fold labels")
        ticks = int(self._config.get("adverse_tick_slip", ADVERSE_TICKS_SLIPPAGE_FLOOR_V10))
        base = {
            "fee_multiplier": 1.0,
            "tick_slip_ticks": ticks,
            "event_delay_events": 0,
            "drop_symbols": [],
            "dropped_fold_index": None,
        }
        variants: list[dict[str, Any]] = [
            {"id": "baseline", "family": "baseline", "stress": dict(base)},
            {
                "id": "fee_slippage_x1_5",
                "family": "fee_slippage_x1_5",
                "stress": {**base, "fee_multiplier": 1.5},
            },
            {
                "id": "plus_2_ticks",
                "family": "plus_2_ticks",
                "stress": {**base, "tick_slip_ticks": ticks + 2},
            },
            {
                "id": "plus_1_event_delay",
                "family": "plus_1_event_delay",
                "stress": {**base, "event_delay_events": 1},
            },
        ]
        for symbol in symbols:
            variants.append(
                {
                    "id": f"drop_one_symbol:{symbol}",
                    "family": "drop_one_symbol",
                    "stress": {**base, "drop_symbols": [symbol]},
                }
            )
        for index, label in enumerate(labels):
            variants.append(
                {
                    "id": f"drop_one_fold:{label}",
                    "family": "drop_one_fold",
                    "stress": {**base, "dropped_fold_index": index},
                }
            )
        families = {variant["family"] for variant in variants}
        if families != {"baseline", *STRESS_MATRIX_V10}:
            raise ContractViolation(f"stress surface drifted: {sorted(families)}")
        return variants

    def finalize_stress(
        self,
        results_by_variant_id: Mapping[str, Any],
        required_ids: Sequence[str],
    ) -> dict[str, Any]:
        """Refuse to finalise unless every required cell is present and only it."""
        required = [str(vid) for vid in required_ids]
        if not required:
            raise ContractViolation("no required stress variants declared")
        missing = [vid for vid in required if vid not in results_by_variant_id]
        if missing:
            raise ContractViolation(f"missing stress variants: {sorted(missing)}")
        undeclared = sorted(set(map(str, results_by_variant_id)) - set(required))
        if undeclared:
            raise ContractViolation(f"undeclared stress cells present: {undeclared}")
        for variant_id in required:
            result = results_by_variant_id[variant_id]
            if not isinstance(result, Mapping):
                raise ContractViolation(f"variant {variant_id} result must be a mapping")
            declared = result.get("variant_id", variant_id)
            if str(declared) != variant_id:
                raise ContractViolation(
                    f"variant id mismatch: key {variant_id} declares {declared!r}"
                )
        return {
            "finalized": True,
            "n_variants": len(required),
            "variant_ids": list(required),
            "payload_sha256": payload_sha256(list(results_by_variant_id[vid] for vid in required)),
        }

    # ------------------------------------------------------------------ #
    # BG-5 benchmarks
    # ------------------------------------------------------------------ #
    def flat_hard_benchmark(self, n_days: int) -> dict[str, Any]:
        """Hard gate: zero-position flat book, exactly zero everywhere."""
        days = int(n_days)
        if days <= 0:
            raise ContractViolation("flat benchmark needs a positive day count")
        series = [0.0 for _ in range(days)]
        return {
            "benchmark": "flat_hard",
            "role": "hard_gate",
            "enters_denominator": False,
            "n_days": days,
            "daily_unit_gross_return": series,
            "total_return": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": None,
            "profit_factor_is_undefined": True,
        }

    def context_benchmark(
        self,
        kind: str,
        *,
        daily_pnl: Sequence[float],
        daily_gross_exposure: Sequence[float],
        daily_net_exposure: Sequence[float],
        benchmark_daily_return: Sequence[float],
    ) -> dict[str, Any]:
        """Context-only benchmark series (never scored, never a gate)."""
        pnl = [float(v) for v in daily_pnl]
        gross = [float(v) for v in daily_gross_exposure]
        net = [float(v) for v in daily_net_exposure]
        benchmark = [float(v) for v in benchmark_daily_return]
        lengths = {len(pnl), len(gross), len(net), len(benchmark)}
        if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
            raise ContractViolation(
                f"context benchmark series must be equal non-zero lengths, got {sorted(lengths)}"
            )
        if any(g == 0.0 for g in gross):
            raise ContractViolation("zero gross exposure cannot normalise a context series")
        if str(kind) == "btc_beta_neutral":
            series = [
                p / g - b * n / g for p, g, n, b in zip(pnl, gross, net, benchmark)
            ]
            definition = "pnl/gross - benchmark*net/gross"
        elif str(kind) == "buy_and_hold":
            series = list(benchmark)
            definition = "benchmark series itself (context only)"
        else:
            raise ContractViolation(
                f"unknown context benchmark kind {kind!r}; "
                "expected 'btc_beta_neutral' or 'buy_and_hold'"
            )
        if any(not math.isfinite(v) for v in series):
            raise ContractViolation("context benchmark produced a non-finite value")
        return {
            "benchmark": str(kind),
            "role": "context_only",
            "enters_denominator": False,
            "definition": definition,
            "daily_unit_gross_return": series,
            "n_days": len(series),
        }

    # ------------------------------------------------------------------ #
    # BG-6 publication
    # ------------------------------------------------------------------ #
    def publish_trial(self, entry: Mapping[str, Any], ledger_path: Any = None) -> dict[str, Any]:
        """Exactly-once publication of one scored cell (see :func:`publish_trial`)."""
        return publish_trial(entry, ledger_path=ledger_path)

    def denominator(self, ledger_path: Any = None) -> int:
        """Number of published scored cells (a rerun can never double-count)."""
        return denominator(ledger_path=ledger_path)


# --------------------------------------------------------------------------- #
# G15 checked funding accrual
# --------------------------------------------------------------------------- #
def _holding_span(holding: Any) -> tuple[str, float, int, int]:
    symbol = str(
        getattr(holding, "symbol", None)
        or (holding.get("symbol") if isinstance(holding, Mapping) else None)
        or ""
    )
    if not symbol:
        raise ContractViolation("holding span without a symbol")
    weight = getattr(holding, "signed_weight", None)
    if weight is None:
        weight = getattr(holding, "weight", None)
    if weight is None and isinstance(holding, Mapping):
        weight = holding.get("signed_weight", holding.get("weight", holding.get("qty")))
    if weight is None:
        weight = getattr(holding, "qty", None)
    if weight is None:
        raise ContractViolation(f"holding span {symbol} without a signed weight")
    start = getattr(holding, "start_ns", None)
    end = getattr(holding, "end_ns", None)
    if start is None and isinstance(holding, Mapping):
        start = holding.get("start_ns")
    if end is None and isinstance(holding, Mapping):
        end = holding.get("end_ns")
    if start is None or end is None:
        raise ContractViolation(f"holding span {symbol} without start/end stamps")
    return symbol, float(weight), int(start), int(end)


def _labelled_settlement_series(
    settlements: Any,
) -> tuple[Optional[dict[str, list[Any]]], list[Any]]:
    """Split a settlement input into per-symbol series, or a shared flat series.

    Accepted forms, most explicit first:

    * ``{symbol: [point, ...]}`` -- per-symbol native series (heterogeneous
      settlement cadences are then honoured exactly per instrument);
    * a sequence of points that each carry a symbol (mapping with ``symbol`` or
      ``(symbol, ts, rate)`` triples);
    * a sequence of unlabelled points -- a SHARED series that accrues to every
      leg held across each instant (the adapter refuses to invent a symbol
      attribution it was never given).
    """
    if isinstance(settlements, Mapping):
        labelled: dict[str, list[Any]] = {}
        for symbol, series in settlements.items():
            labelled[str(symbol)] = list(normalize_info_series(list(series)))
        return labelled, []
    points = list(settlements)
    if points and all(_point_symbol(point) is not None for point in points):
        labelled = {}
        for point in points:
            labelled.setdefault(str(_point_symbol(point)), []).append(point)
        return {
            symbol: list(normalize_info_series(series))
            for symbol, series in labelled.items()
        }, []
    return None, list(normalize_info_series(points))


def _point_symbol(point: Any) -> Optional[str]:
    if isinstance(point, Mapping):
        value = point.get("symbol")
    elif isinstance(point, (tuple, list)) and len(point) >= 3 and isinstance(point[0], str):
        value = point[0]
    else:
        value = getattr(point, "symbol", None)
    return None if value is None or str(value) == "" else str(value)


def checked_funding_accrual(
    holdings: Iterable[Any],
    settlements: Any,
    coverage_required: bool = True,
) -> dict[str, Any]:
    """Native funding accrual over held spans, with coverage accounting.

    Only settlement instants strictly inside ``(start_ns, end_ns]`` accrue; a
    long leg (positive weight) PAYS a positive rate and a short leg RECEIVES
    it, i.e. ``cashflow = -signed_weight * rate`` per unit of unit-gross
    capital. A span with no settlement inside it is MARKED
    (``UNAVAILABLE_FAIL_CLOSED``, no cashflows emitted) when
    ``coverage_required`` is set -- uncovered accrual is never silently zero.

    Settlement attribution is explicit: per-symbol series (mapping, or points
    carrying a symbol) accrue to their own instrument only; an UNLABELLED flat
    series is shared by every held leg, because the adapter will never invent a
    symbol attribution it was not given.
    """
    labelled, flat_points = _labelled_settlement_series(settlements)
    shared_points = flat_points
    series_mode = "per_symbol" if labelled is not None else "shared_flat_series"
    spans = [_holding_span(holding) for holding in holdings]
    flows: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    for symbol, weight, start, end in spans:
        if labelled is not None:
            points = labelled.get(symbol, [])
        else:
            points = shared_points
        inside = [point for point in points if start < point.publish_ts_ns <= end]
        if not inside:
            unavailable.append({"symbol": symbol, "start_ns": start, "end_ns": end})
            continue
        for point in inside:
            rate = float(point.value)
            cashflow = -weight * rate
            flows.append(
                {
                    "symbol": symbol,
                    "settle_ts_ns": int(point.publish_ts_ns),
                    "rate": rate,
                    "signed_weight": weight,
                    "cashflow_per_unit_capital": cashflow + 0.0,
                    "sign_convention": SIGN_CONVENTION_LONG_PAYS_POSITIVE,
                }
            )
    flows.sort(key=lambda row: (row["settle_ts_ns"], row["symbol"]))
    coverage = {
        "is_complete": not unavailable,
        "unavailable_spans": unavailable,
        "n_spans": len(spans),
        "series_mode": series_mode,
        "rule": "settlement_ts_in_half_open_span_start_exclusive_end_inclusive",
    }
    complete = not unavailable
    if unavailable and coverage_required:
        return {
            "cashflows": [],
            "coverage": coverage,
            "sign_convention": SIGN_CONVENTION_LONG_PAYS_POSITIVE,
            "status": "UNAVAILABLE_FAIL_CLOSED",
            "n_flows": 0,
        }
    return {
        "cashflows": flows,
        "coverage": coverage,
        "sign_convention": SIGN_CONVENTION_LONG_PAYS_POSITIVE,
        "status": "OK" if complete else "PARTIAL_COVERAGE_REPORTED",
        "n_flows": len(flows),
        "cashflow_total": math.fsum(row["cashflow_per_unit_capital"] for row in flows),
    }


# --------------------------------------------------------------------------- #
# F2 / G-H06 cache decision
# --------------------------------------------------------------------------- #
def cache_decision(payload_or_path: Any = None) -> dict[str, Any]:
    """Cache ON only with a complete, self-consistent decision artifact.

    An absent/empty/unreadable decision leaves the cache OFF, and no
    environment flag can ever turn it on: the decision, not the operator
    posture, is the authority.
    """
    payload, source = _load_optional_payload(payload_or_path)
    reasons: list[str] = []
    if payload is None or not payload:
        return {
            "enabled": False,
            "mode": "DISABLED_DECISION_ABSENT",
            "reasons": [f"cache decision absent or empty (source={source})"],
            "raw_reads_pair": None,
            "preregistered_budget_max_raw_reads": None,
            "decision_source": source,
            "env_flags_ignored": _env_flags_set(),
        }

    pair_raw = payload.get("raw_reads_pair")
    budget = payload.get("preregistered_budget_max_raw_reads")
    pair: Optional[dict[str, Any]] = None
    if isinstance(pair_raw, Mapping) and {"cached", "uncached"} <= set(pair_raw):
        cached, uncached = pair_raw["cached"], pair_raw["uncached"]
        if all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0
            for v in (cached, uncached)
        ):
            pair = {"cached": int(cached), "uncached": int(uncached)}

    if pair is None:
        reasons.append("raw_reads_pair missing or malformed")
    else:
        if pair["cached"] > pair["uncached"]:
            reasons.append(
                f"cached raw reads {pair['cached']} exceed uncached {pair['uncached']}: no cache win"
            )
    if not _finite_positive(budget):
        reasons.append("preregistered_budget_max_raw_reads missing or not positive")
    for field in ("parity_proof", "repro_all_match"):
        value = payload.get(field)
        if value is not True:
            reasons.append(f"{field} not true ({value!r})")

    enabled = not reasons
    if not enabled:
        mode = (
            "DISABLED_NO_CACHE_WIN"
            if pair is not None and pair["cached"] > pair["uncached"]
            else "DISABLED_DECISION_INSUFFICIENT"
        )
    else:
        mode = "ENABLED_CACHE"
        gate = SharedCacheMergeGate()
        evaluation = gate.evaluate(
            parity_proof=payload.get("parity_proof", False),
            repro_all_match=payload.get("repro_all_match", False),
            raw_reads=pair["uncached"] if pair else 0,
            wall_time_cached_s=float(payload.get("wall_time_cached_s", 0.0)),
            wall_time_uncached_s=float(payload.get("wall_time_uncached_s", 0.0)),
            strict=False,
        )
        if not evaluation["adopted"]:
            reasons.append(
                "advisory: SharedCacheMergeGate would not adopt this proof "
                f"({', '.join(evaluation['reasons'])})"
            )
    if _env_flags_set() and not enabled:
        reasons.append(
            "environment cache flags present but ignored: only the decision artifact enables the cache"
        )
    return {
        "enabled": enabled,
        "mode": mode,
        "reasons": reasons,
        "raw_reads_pair": pair,
        "preregistered_budget_max_raw_reads": budget,
        "decision_source": source,
        "env_flags_ignored": _env_flags_set(),
        "advisory_budget": (
            SharedCacheMergeGate.MAX_RAW_READS_FULL_STRESS
            if hasattr(SharedCacheMergeGate, "MAX_RAW_READS_FULL_STRESS")
            else None
        ),
    }


def _env_flags_set() -> list[str]:
    return [flag for flag in CACHE_ENV_FLAGS if os.environ.get(flag)]


# --------------------------------------------------------------------------- #
# G17 resource cap
# --------------------------------------------------------------------------- #
def validate_resource_cap_report(payload: Any) -> dict[str, Any]:
    """Validate one resource-cap artifact (exactly one integer final cap)."""
    reasons: list[str] = []
    if not isinstance(payload, Mapping) or not payload:
        return {
            "is_valid": False,
            "reasons": ["payload_empty_or_not_an_object"],
            "final_cap": None,
        }
    owner = payload.get("owner_ceiling")
    measured = payload.get("measured_safe_cap")
    final = payload.get("final_cap")

    for name, value in (("owner_ceiling", owner), ("measured_safe_cap", measured)):
        if value is None:
            reasons.append(f"missing_field:{name}")
        elif not isinstance(value, int) or isinstance(value, bool) or value < 0:
            reasons.append(f"{name}_must_be_non_negative_integer")
    if final is None:
        reasons.append("missing_field:final_cap")
    elif isinstance(final, (list, tuple, set)):
        reasons.append("final_cap_ambiguous_multiple_values")
    elif isinstance(final, bool):
        reasons.append("final_cap_must_be_integer")
    elif isinstance(final, float):
        reasons.append("final_cap_must_be_integer")
    elif not isinstance(final, int) or final < 0:
        reasons.append("final_cap_must_be_non_negative_integer")

    numeric_owner = owner if isinstance(owner, int) and not isinstance(owner, bool) else None
    numeric_measured = (
        measured if isinstance(measured, int) and not isinstance(measured, bool) else None
    )
    if numeric_owner is not None and numeric_measured is not None and isinstance(final, int) and not isinstance(final, bool):
        formula_cap = min(numeric_owner, numeric_measured)
        if final > numeric_measured:
            reasons.append(
                f"final_cap {final} exceeds measured_safe_cap {numeric_measured}"
            )
        if final != formula_cap:
            reasons.append(
                f"final_cap {final} must equal min(owner_ceiling, measured_safe_cap)={formula_cap}"
            )
    return {
        "is_valid": not reasons,
        "reasons": reasons,
        "final_cap": final if isinstance(final, int) and not isinstance(final, bool) else None,
        "cap_formula": "min(owner_ceiling, measured_safe_cap)",
    }


def resource_cap_report(payload_or_path: Any = None) -> dict[str, Any]:
    """One authoritative cap: ``final_cap = min(owner_ceiling, measured_safe_cap)``."""
    payload = _require_payload(payload_or_path)
    validation = validate_resource_cap_report(payload)
    if not validation["is_valid"]:
        raise ContractViolation(
            "resource cap artifact rejected: " + "; ".join(validation["reasons"])
        )
    owner = int(payload["owner_ceiling"])
    measured = int(payload["measured_safe_cap"])
    final_cap = min(owner, measured)
    report = _json_safe(payload)
    report.update(
        {
            "owner_ceiling": owner,
            "measured_safe_cap": measured,
            "final_cap": final_cap,
            "cap_formula": "min(owner_ceiling, measured_safe_cap)",
            "scored_launch_allowed": final_cap > 0,
            "cap_note": (
                "cap 0 means NO local scored launch, never an override"
                if final_cap == 0
                else "effective heavy-worker ceiling"
            ),
        }
    )
    return report


# --------------------------------------------------------------------------- #
# BG-6 module-level publication helpers
# --------------------------------------------------------------------------- #
_VOLATILE_ENTRY_KEYS = ("appended_at", "published_at", "published_by")


def _trial_identity(entry: Mapping[str, Any]) -> str:
    """Content identity of one trial (stable across reruns of the same cell)."""
    payload = {str(k): entry[k] for k in sorted(entry) if k not in _VOLATILE_ENTRY_KEYS}
    return payload_sha256(payload)


def publish_trial(entry: Mapping[str, Any], ledger_path: Any = None) -> dict[str, Any]:
    """Publish one scored cell exactly once; refuse duplicates and non-scores.

    Order of refusal (nothing is ever written before every check passes):

    1. the entry must be a mapping with a non-empty ``experiment_id``;
    2. its ``verdict`` must be a score-passing verdict (a failed or partial
       pre-score is NEVER a publication);
    3. a scored cell must carry its score digest;
    4. the same trial identity must not already be in the ledger.
    """
    if not isinstance(entry, Mapping):
        raise ContractViolation("publish_trial entry must be a mapping")
    experiment_id = str(entry.get("experiment_id") or "").strip()
    if not experiment_id:
        raise ContractViolation("publish_trial requires a non-empty experiment_id")
    verdict = entry.get("verdict")
    if not isinstance(verdict, str) or verdict.strip() not in SCORE_PASSING_VERDICTS:
        raise ContractViolation(
            f"publish_trial refused: verdict {verdict!r} is not a score-passing "
            f"verdict {list(SCORE_PASSING_VERDICTS)}; a failed or partial pre-score "
            "is never published"
        )
    kind = entry.get("kind", PUBLISHED_CELL_KIND)
    if str(kind) != PUBLISHED_CELL_KIND:
        raise ContractViolation(
            f"publish_trial refused: kind {kind!r} is not {PUBLISHED_CELL_KIND}"
        )
    if not any(
        str(entry.get(field) or "").strip()
        for field in ("score_sha256", "experiment_digest", "payload_sha256")
    ):
        raise ContractViolation(
            "publish_trial refused: a scored cell must carry a score digest "
            "(score_sha256 / experiment_digest / payload_sha256)"
        )
    identity = _trial_identity(entry)
    state = snapshot(ledger_path)
    for row in state["rows"]:
        if row.get("trial_identity_sha256") == identity:
            raise ContractViolation(
                f"duplicate trial publish refused: experiment_id={experiment_id} "
                f"already published with identity {identity[:16]}"
            )
    stored_entry = dict(entry)
    stored_entry.setdefault("kind", PUBLISHED_CELL_KIND)
    stored_entry["trial_identity_sha256"] = identity
    stored_entry["published_by"] = "adapter_v10"
    stored = append_verified(stored_entry, ledger_path)
    after = snapshot(ledger_path)
    return {
        "published": True,
        "experiment_id": stored["experiment_id"],
        "trial_identity_sha256": identity,
        "denominator": denominator(ledger_path),
        "ledger_count_after": after["count"],
        "ledger_sha256_after": after["sha256"],
    }


def denominator(ledger_path: Any = None) -> int:
    """Count published scored cells; the denominator of the trial budget."""
    state = snapshot(ledger_path)
    return sum(
        1 for row in state["rows"] if str(row.get("kind")) == PUBLISHED_CELL_KIND
    )


__all__ = [
    "ADAPTER_INTERFACE_VERSION",
    "FORCE_FLAT_REASON",
    "FORCE_FLAT_STATUS",
    "GenericRunnerV10",
    "SCORE_PASSING_VERDICTS",
    "cache_decision",
    "checked_funding_accrual",
    "denominator",
    "publish_trial",
    "resource_cap_report",
    "validate_resource_cap_report",
]
