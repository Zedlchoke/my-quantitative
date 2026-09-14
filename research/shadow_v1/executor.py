"""PRODUCTION forward executor (condition C1; resolves F1/F3/F6).

Composes the frozen pipeline INSIDE the no-order scan surface for one
family per executor instance:

    start_guard.assert_forward  ->  deterministic event_id (events.py)
    ->  ledger idempotency skip  ->  PIT fetch via data_feed
    (DATA_BLOCKED on gaps, same semantics as scheduler.py)
    ->  adapter.decide  ->  risk.check_and_apply BEFORE any fill
    ->  SleeveAccount virtual fills at the frozen fill rule
    (first completed bar strictly after the decision; buy at
    ref + ticks*tick, sell at ref - ticks*tick)
    ->  settled funding booked once while held
    ->  ONE plan section 8 event record appended atomically with
    TARGET_INTENT-only action types and the no_order_proof digest.

This module is INTERNAL_PAPER_ONLY: no keys, no network calls of its
own (the injected feed owns transport), no order routing — the only
emitted action type is TARGET_INTENT and fills are virtual.

POLICY: REDUCING_SELL_NETS_POSITION (condition C1, audit finding F3)
    A sell that reduces or closes an existing LONG position nets against
    that position: the only requirement is the position-size check
    (sell qty <= current long qty, enforced in accounting.apply_fill);
    the proceeds credit cash after fees/slippage. A reducing sell is NOT
    required to carry full sell-notional cash/gross headroom — the prior
    guard overcounted post-trade gross by the reduction and could refuse
    valid rebalance sells in fully-invested gross-1.0 books. Opening or
    increasing sells (new shorts), including sells that flip through
    zero (qty > current long qty), still pass the UNCHANGED no-margin /
    no-leverage cash and gross checks. Both cost books always keep
    identical quantities (shared position/cash mutation in accounting).
    There is NO execution buffer and NO sell slicing in production: the
    rehearsal-only COST_BUFFER/DUST/slicing parameters of the smoke
    harness are deliberately not carried over (audit F1/ADJ3).

FEATURE-CUTOFF CONVENTION (F6 pin)
    Bars/basis buckets are fetched with ``cutoff = decision_utc -
    feature_cutoff_offset_seconds`` so only bars whose canonical close
    is STRICTLY BEFORE the decision enter the snapshot — the same
    strict-inequality rule as ``data_feed.feature_eligible_bucket``;
    the feed-level ``close <= cutoff`` boundary can therefore never
    leak a decision-boundary bar. ``feature_cutoff_offset_seconds``
    is a REQUIRED config value (fail closed when missing): set it to
    900 (one frozen 15m interval) for bar/bucket families. Settled
    funding eligibility is ``fundingTime < decision`` strictly, so
    funding fetches always use ``cutoff = decision_utc`` itself.

FILL-BAR AVAILABILITY
    A due decision whose first post-decision bar has not completed yet
    (``now < decision + interval``) is NOT executed and NOT recorded; it
    stays due and is executed by a later ``run_due`` (nothing is
    committed, so no slot is consumed by the future). A genuine gap in
    the completed-bar record raises ``DataBlocked`` and is converted to
    a DATA_BLOCKED record under the deterministic event_id (consumed,
    never re-executed — audit ADJ1 semantics).

EQUITY IDENTITY / MARK GAPS / COUNTERS
    Equity identity is asserted on every sleeve mutation by
    accounting.py (fail-closed IDENTITY_MISMATCH); mark gaps stay
    UNAVAILABLE_FAIL_CLOSED with no interpolation; the four counters
    (decision / order_intent / fill / closed_position) remain separate;
    there is no margin and no leverage anywhere.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

from . import (
    accounting,
    data_feed,
    events,
    ledger,
    no_order,
    risk,
    scheduler,
    start_guard,
)
from .families import FAMILY_REGISTRY, FamilyAdapter, FamilySnapshot

#: Absolute path of this package: the no-order scan surface.
PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))

DEFAULT_NAMESPACE = start_guard.NAMESPACE_PROSPECTIVE

_ALLOWED_SCHEDULES = (
    scheduler.SCHEDULE_WEEKLY_MONDAY_0000Z,
    scheduler.SCHEDULE_DAILY_0000Z,
)

_SNAPSHOT_KINDS = ("bars", "basis_buckets", "funding_settlements")


class ExecutorError(RuntimeError):
    """Production executor misconfiguration or contract violation."""


class _FillBarPending(Exception):
    """Internal: the first post-decision bar has not completed yet."""


def canonical_digest(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutorError(message)


def _validate_snapshot_spec(spec: Mapping[str, Any]) -> Dict[str, Any]:
    _require(
        isinstance(spec, Mapping) and len(spec) >= 1,
        "snapshot_spec must be a non-empty mapping",
    )
    validated: Dict[str, Any] = {}
    for kind, sub in spec.items():
        _require(
            kind in _SNAPSHOT_KINDS,
            f"snapshot_spec kind {kind!r} not one of {list(_SNAPSHOT_KINDS)}",
        )
        _require(
            isinstance(sub, Mapping), f"snapshot_spec[{kind!r}] must be a mapping"
        )
        symbols = sub.get("symbols")
        _require(
            isinstance(symbols, (list, tuple)) and len(symbols) >= 1,
            f"snapshot_spec[{kind!r}].symbols must be a non-empty list",
        )
        lookback = sub.get("lookback_seconds")
        _require(
            isinstance(lookback, (int, float)) and float(lookback) > 0,
            f"snapshot_spec[{kind!r}].lookback_seconds must be positive",
        )
        entry: Dict[str, Any] = {
            "symbols": [str(s) for s in symbols],
            "lookback_seconds": float(lookback),
        }
        if kind in ("bars", "basis_buckets"):
            interval = sub.get("interval")
            _require(
                interval in data_feed.INTERVAL_MS,
                f"snapshot_spec[{kind!r}].interval {interval!r} unsupported",
            )
            entry["interval"] = interval
        validated[kind] = entry
    return validated


class ForwardExecutor:
    """Production forward executor for ONE family (one isolated sleeve).

    Parameters
    ----------
    family_id:
        The family this executor runs; must match the adapter identity.
    config:
        Frozen run configuration. Required keys (fail closed):
        ``code_freeze_sha`` (str), ``tick_size`` (float > 0),
        ``cost_books`` ({name: {fee_rate, slippage_ticks}}),
        ``caps`` (a risk.FamilyRiskCaps for this family),
        ``snapshot_spec`` (see :func:`_validate_snapshot_spec`),
        ``feature_cutoff_offset_seconds`` (float >= 0, the F6 pin),
        ``schedule`` (a frozen scheduler schedule, used by run_due).
        Exactly one of ``adapter`` (a constructed FamilyAdapter) or
        ``identity_entry`` (a manifest entry; the adapter is built from
        FAMILY_REGISTRY). Optional: ``namespace`` (default PROSPECTIVE),
        ``starting_cash`` (default 100,000 USDT), ``primary_book``
        (default CURRENT_CONSERVATIVE_COST), ``btc_betas`` mapping,
        ``fill_bar_interval`` (default "15m"), ``fill_symbols``.
    runtime_root:
        Root under which the namespace-separated ledger directory lives.
    feed:
        PIT data surface exposing the data_feed fetch methods
        (``get_completed_bars`` / ``get_basis_buckets`` /
        ``get_settled_funding``). The production feed wraps
        KeylessBinanceFuturesClient; tests may inject an in-memory feed.
    shadow_start_utc:
        SHADOW_START_UTC (ISO-Z). REQUIRED for the PROSPECTIVE namespace
        (refused at construction when missing); optional for the
        explicit REPLAY_NOT_PROSPECTIVE namespace.
    """

    def __init__(
        self,
        family_id: str,
        config: Mapping[str, Any],
        runtime_root: str,
        feed: Any,
        shadow_start_utc: Optional[str],
    ):
        _require(
            isinstance(config, Mapping), "config must be a mapping (fail closed)"
        )
        self.family_id = str(family_id)
        self.feed = feed
        self.namespace = str(config.get("namespace", DEFAULT_NAMESPACE))
        _require(
            self.namespace in start_guard.KNOWN_NAMESPACES,
            f"namespace {self.namespace!r} is not one of "
            f"{list(start_guard.KNOWN_NAMESPACES)}",
        )
        self.shadow_start_utc = shadow_start_utc
        if self.namespace == start_guard.NAMESPACE_PROSPECTIVE:
            # Fail closed at construction: a PROSPECTIVE executor without
            # an explicit start can never legally run.
            if shadow_start_utc is None:
                raise start_guard.StartGuardError(
                    "PROSPECTIVE ForwardExecutor requires shadow_start_utc "
                    "(SHADOW_START_UTC); refusing to construct"
                )
            start_guard.parse_moment(shadow_start_utc)

        for key in (
            "code_freeze_sha",
            "tick_size",
            "cost_books",
            "caps",
            "snapshot_spec",
            "feature_cutoff_offset_seconds",
            "schedule",
        ):
            _require(key in config, f"required config key {key!r} missing")

        self.code_freeze_sha = str(config["code_freeze_sha"])
        _require(bool(self.code_freeze_sha), "code_freeze_sha must be non-empty")

        tick = config["tick_size"]
        _require(
            isinstance(tick, (int, float)) and float(tick) > 0,
            "tick_size must be a positive number",
        )
        self.tick_size = float(tick)

        offset = config["feature_cutoff_offset_seconds"]
        _require(
            isinstance(offset, (int, float)) and float(offset) >= 0,
            "feature_cutoff_offset_seconds must be a number >= 0 (F6 pin)",
        )
        self.feature_cutoff_offset_seconds = float(offset)

        schedule = config["schedule"]
        _require(
            schedule in _ALLOWED_SCHEDULES,
            f"schedule {schedule!r} not one of {list(_ALLOWED_SCHEDULES)}",
        )
        self.schedule = schedule

        books_cfg = config["cost_books"]
        _require(
            isinstance(books_cfg, Mapping) and len(books_cfg) >= 1,
            "cost_books must be a non-empty mapping",
        )
        books: Dict[str, accounting.BookCostParams] = {}
        for name, params in books_cfg.items():
            _require(
                isinstance(params, Mapping)
                and "fee_rate" in params
                and "slippage_ticks" in params,
                f"cost book {name!r} needs fee_rate and slippage_ticks",
            )
            books[str(name)] = accounting.BookCostParams(
                fee_rate=float(params["fee_rate"]),
                slippage_ticks=float(params["slippage_ticks"]),
            )
        self.cost_books_cfg: Dict[str, Dict[str, float]] = {
            str(name): {
                "fee_rate": float(p["fee_rate"]),
                "slippage_ticks": float(p["slippage_ticks"]),
            }
            for name, p in books_cfg.items()
        }

        self.primary_book = str(
            config.get("primary_book", accounting.DEFAULT_PRIMARY_BOOK)
        )
        _require(
            self.primary_book in books,
            f"primary_book {self.primary_book!r} not among cost books",
        )

        self.snapshot_spec = _validate_snapshot_spec(config["snapshot_spec"])

        self.fill_bar_interval = str(config.get("fill_bar_interval", "15m"))
        _require(
            self.fill_bar_interval in data_feed.INTERVAL_MS,
            f"fill_bar_interval {self.fill_bar_interval!r} unsupported",
        )
        if "fill_symbols" in config:
            fill_symbols = [str(s) for s in config["fill_symbols"]]
        elif "bars" in self.snapshot_spec:
            fill_symbols = list(self.snapshot_spec["bars"]["symbols"])
        elif "basis_buckets" in self.snapshot_spec:
            fill_symbols = list(self.snapshot_spec["basis_buckets"]["symbols"])
        else:
            raise ExecutorError(
                "fill symbol universe not derivable: provide config "
                "'fill_symbols' or a bars/basis_buckets snapshot_spec"
            )
        _require(len(fill_symbols) >= 1, "fill symbol universe must be non-empty")
        self.fill_symbols = fill_symbols

        self.btc_betas = config.get("btc_betas")
        if self.btc_betas is not None:
            self.btc_betas = {str(k): float(v) for k, v in dict(self.btc_betas).items()}

        caps = config["caps"]
        _require(
            isinstance(caps, risk.FamilyRiskCaps),
            "caps must be a risk.FamilyRiskCaps instance (fail closed)",
        )
        _require(
            caps.family_id == self.family_id,
            f"caps family_id {caps.family_id!r} != executor family_id "
            f"{self.family_id!r}",
        )
        self.caps = caps

        adapter = config.get("adapter")
        identity_entry = config.get("identity_entry")
        if adapter is not None and identity_entry is not None:
            raise ExecutorError(
                "pass either 'adapter' or 'identity_entry', not both"
            )
        if adapter is None:
            _require(
                identity_entry is not None,
                "config needs an 'adapter' or an 'identity_entry'",
            )
            _require(
                self.family_id in FAMILY_REGISTRY,
                f"family {self.family_id!r} not in FAMILY_REGISTRY",
            )
            cls = FAMILY_REGISTRY[self.family_id]
            built = cls.build_config(identity_entry, config.get("engine", {}))
            adapter = cls(built, identity_entry)
        _require(
            isinstance(adapter, FamilyAdapter),
            "adapter must be a families.FamilyAdapter instance",
        )
        _require(
            adapter.FAMILY_ID == self.family_id,
            f"adapter FAMILY_ID {adapter.FAMILY_ID!r} != {self.family_id!r}",
        )
        self.adapter = adapter
        self.arm_id = str(adapter.ARM_ID)

        self.config_digest = canonical_digest(
            {
                "adapter_config": getattr(adapter, "config", None),
                "executor": {
                    "code_freeze_sha": self.code_freeze_sha,
                    "feature_cutoff_offset_seconds": self.feature_cutoff_offset_seconds,
                    "fill_bar_interval": self.fill_bar_interval,
                    "fill_symbols": self.fill_symbols,
                    "primary_book": self.primary_book,
                    "schedule": self.schedule,
                    "snapshot_spec": self.snapshot_spec,
                    "tick_size": self.tick_size,
                    "btc_betas": self.btc_betas,
                },
            }
        )
        self.cost_regime_digest = canonical_digest(self.cost_books_cfg)

        self.sleeve = accounting.SleeveAccount(
            sleeve_id=f"sleeve_{self.family_id}",
            books=books,
            starting_cash=float(config.get("starting_cash", 100_000.0)),
            primary_book=self.primary_book,
        )

        self.ledger_file = ledger.ledger_path(
            start_guard.ledger_root(runtime_root, self.namespace), self.family_id
        )

        self._last_decision_utc: Optional[str] = None

    # ------------------------------------------------------------------
    # run loop
    # ------------------------------------------------------------------
    def run_due(self, now_utc, *, from_utc=None) -> Dict[str, Any]:
        """Execute every due decision of the family up to ``now_utc``.

        Due decisions are the frozen decision-clock stamps in
        ``[from_utc, now_utc)``. ``from_utc`` defaults to
        SHADOW_START_UTC in the PROSPECTIVE namespace and is REQUIRED in
        the REPLAY_NOT_PROSPECTIVE namespace. Each decision passes
        ``start_guard.assert_forward`` before anything runs; decisions
        already in the ledger are skipped idempotently.
        """
        now = start_guard.parse_moment(now_utc)
        result: Dict[str, Any] = {
            "family_id": self.family_id,
            "namespace": self.namespace,
            "now_utc": start_guard.to_iso_z(now),
            "due": [],
            "executed": [],
            "emitted": 0,
            "data_blocked": 0,
            "risk_blocked": 0,
            "accounting_fail_closed": 0,
            "skipped_existing": 0,
            "pending_fill_bar": [],
            "ledger_path": self.ledger_file,
            "ledger_digest": ledger.ledger_digest(self.ledger_file),
        }

        if from_utc is not None:
            effective_from = start_guard.to_iso_z(start_guard.parse_moment(from_utc))
        elif self.namespace == start_guard.NAMESPACE_PROSPECTIVE:
            effective_from = start_guard.to_iso_z(
                start_guard.parse_moment(self.shadow_start_utc)
            )
        else:
            raise ExecutorError(
                "REPLAY_NOT_PROSPECTIVE run_due requires an explicit from_utc"
            )

        if start_guard.parse_moment(effective_from) > now:
            return result  # nothing can be due yet (pre-activation quiet no-op)

        due = scheduler.pending_decisions(
            self.family_id, effective_from, result["now_utc"], schedule=self.schedule
        )
        result["due"] = list(due)
        known_ids = ledger.event_ids(self.ledger_file)

        for scheduled_utc in due:
            # Defense in depth: every decision passes the forward-only
            # guard even though the window already starts at the floor.
            start_guard.assert_forward(
                scheduled_utc, self.shadow_start_utc, self.namespace
            )
            event_id = events.compute_event_id(
                self.family_id, self.arm_id, scheduled_utc
            )
            if event_id in known_ids:
                result["skipped_existing"] += 1
                continue
            record, outcome = self._execute_decision(
                scheduled_utc, event_id, observed_at_utc=result["now_utc"]
            )
            if record is None:
                result["pending_fill_bar"].append(scheduled_utc)
                continue
            if ledger.append_event(self.ledger_file, record) == "appended":
                known_ids.add(event_id)
                result["executed"].append(event_id)
                if outcome == "data_blocked":
                    result["data_blocked"] += 1
                elif outcome == "risk_blocked":
                    result["risk_blocked"] += 1
                elif outcome == "accounting_fail_closed":
                    result["accounting_fail_closed"] += 1
                else:
                    result["emitted"] += 1

        result["ledger_digest"] = ledger.ledger_digest(self.ledger_file)
        return result

    def __call__(
        self, family_id: str, scheduled_decision_utc: str, event_id: str
    ) -> Dict[str, Any]:
        """scheduler.run_once-compatible single-decision execution."""
        if family_id != self.family_id:
            raise ExecutorError(
                f"executor is bound to {self.family_id!r}, got {family_id!r}"
            )
        start_guard.assert_forward(
            scheduled_decision_utc, self.shadow_start_utc, self.namespace
        )
        record, _outcome = self._execute_decision(
            scheduled_decision_utc, event_id, observed_at_utc=scheduled_decision_utc
        )
        if record is None:
            # Older driver semantics: an unavailable fill bar is data that
            # is not there yet -> DataBlocked (the driver converts it to a
            # DATA_BLOCKED record). run_due is the production loop and
            # leaves the decision pending instead.
            raise data_feed.DataBlocked(
                "fill bar not yet complete for decision "
                f"{scheduled_decision_utc}"
            )
        return record

    # ------------------------------------------------------------------
    # data composition
    # ------------------------------------------------------------------
    def _feature_cutoff(self, decision_utc: str) -> str:
        decision_dt = data_feed.parse_iso_z(decision_utc)
        cutoff_dt = decision_dt - dt.timedelta(
            seconds=self.feature_cutoff_offset_seconds
        )
        return scheduler.to_iso_z(cutoff_dt)

    @staticmethod
    def _bar_row(bar: data_feed.Bar) -> Dict[str, Any]:
        return {
            "open_time_utc": bar.open_time_utc,
            "close_time_utc": bar.close_time_utc,
            "close_price": bar.close_price,
            "quote_volume": bar.quote_volume,
        }

    @staticmethod
    def _bucket_row(bucket: data_feed.BasisBucket) -> Dict[str, Any]:
        return {
            "open_time_utc": bucket.open_time_utc,
            "close_time_utc": bucket.close_time_utc,
            "futures_price": bucket.futures_price,
            "index_price": bucket.index_price,
            "basis": bucket.basis,
            "basis_rate": bucket.basis_rate,
        }

    @staticmethod
    def _funding_row(settlement: data_feed.FundingSettlement) -> Dict[str, Any]:
        row: Dict[str, Any] = {
            "funding_time_utc": settlement.funding_time_utc,
            "funding_rate": settlement.funding_rate,
        }
        if settlement.mark_price is not None:
            row["mark_price"] = settlement.mark_price
        return row

    def _fetch_snapshot(
        self, decision_utc: str, feature_cutoff_utc: str
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """PIT snapshot per the frozen spec; DataBlocked on any gap."""
        decision_dt = data_feed.parse_iso_z(decision_utc)
        payload: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
            "bars": {},
            "basis_buckets": {},
            "funding_settlements": {},
        }
        for kind, spec in self.snapshot_spec.items():
            start_exclusive = scheduler.to_iso_z(
                decision_dt - dt.timedelta(seconds=spec["lookback_seconds"])
            )
            for symbol in spec["symbols"]:
                if kind == "bars":
                    interval_ms = data_feed.INTERVAL_MS[spec["interval"]]
                    # completeness end = last OPEN whose close <= cutoff
                    # (require_complete_bars walks open times).
                    completeness_end = scheduler.to_iso_z(
                        data_feed.parse_iso_z(feature_cutoff_utc)
                        - dt.timedelta(milliseconds=interval_ms)
                    )
                    bars = self.feed.get_completed_bars(
                        symbol,
                        spec["interval"],
                        start_exclusive,
                        feature_cutoff_utc,
                        feature_cutoff_utc,
                    )
                    # Fail closed on gaps (scheduler/DataBlocked semantics).
                    data_feed.require_complete_bars(
                        bars, spec["interval"], start_exclusive, completeness_end
                    )
                    payload["bars"][symbol] = [self._bar_row(b) for b in bars]
                elif kind == "basis_buckets":
                    interval_ms = data_feed.INTERVAL_MS[spec["interval"]]
                    completeness_end = scheduler.to_iso_z(
                        data_feed.parse_iso_z(feature_cutoff_utc)
                        - dt.timedelta(milliseconds=interval_ms)
                    )
                    buckets = self.feed.get_basis_buckets(
                        symbol,
                        start_exclusive,
                        feature_cutoff_utc,
                        feature_cutoff_utc,
                        period=spec["interval"],
                    )
                    data_feed.require_complete_bars(
                        buckets, spec["interval"], start_exclusive, completeness_end
                    )
                    payload["basis_buckets"][symbol] = [
                        self._bucket_row(b) for b in buckets
                    ]
                else:  # funding_settlements; usable iff fundingTime < decision
                    settlements = self.feed.get_settled_funding(
                        symbol, start_exclusive, decision_utc, decision_utc
                    )
                    payload["funding_settlements"][symbol] = [
                        self._funding_row(s) for s in settlements
                    ]
        return payload

    def _fetch_fill_references(
        self, decision_utc: str, observed_at_utc: str
    ) -> Dict[str, float]:
        """Fill reference per symbol: close of the first completed bar
        STRICTLY after the decision (frozen fill rule). Raises
        :class:`_FillBarPending` when the first post-decision bar has not
        completed yet, and ``DataBlocked`` on a genuine gap."""
        decision_dt = data_feed.parse_iso_z(decision_utc)
        now_dt = start_guard.parse_moment(observed_at_utc)
        step = dt.timedelta(milliseconds=data_feed.INTERVAL_MS[self.fill_bar_interval])
        if now_dt < decision_dt + step:
            raise _FillBarPending(
                f"first post-decision bar for {decision_utc} completes at "
                f"{scheduler.to_iso_z(decision_dt + step)}"
            )
        refs: Dict[str, float] = {}
        # start one interval before the decision so the bar OPENING at the
        # decision stamp (canonical close = decision + interval, i.e. the
        # first close strictly after the decision) is fetchable; the
        # pre-decision bar is excluded by select_fill_bar's strict rule.
        window_start = scheduler.to_iso_z(decision_dt - step)
        # completeness end = last OPEN whose close <= now
        completeness_end = scheduler.to_iso_z(now_dt - step)
        for symbol in self.fill_symbols:
            bars = self.feed.get_completed_bars(
                symbol,
                self.fill_bar_interval,
                window_start,
                observed_at_utc,
                observed_at_utc,
            )
            data_feed.require_complete_bars(
                bars, self.fill_bar_interval, window_start, completeness_end
            )
            fill_bar = data_feed.select_fill_bar(bars, decision_utc)
            refs[symbol] = float(fill_bar.close_price)
        return refs

    def _fetch_booking_funding_rows(
        self, decision_utc: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Settled-funding rows for BOOKING (fundingTime <= decision).

        Symbols: the snapshot_spec funding universe plus every currently
        held position (a price-only family's held positions still settle
        funding). Window start: the earliest relevant bound (last
        executed decision / earliest open position) — the accounting
        layer enforces the exact holding window and dedups repeats, so a
        generous fetch is always safe.
        """
        symbols = set(
            self.snapshot_spec.get("funding_settlements", {}).get("symbols", [])
        )
        symbols |= {
            symbol for symbol, pos in self.sleeve.positions.items() if pos.qty != 0.0
        }
        if not symbols:
            return {}
        bounds = [
            pos.ts_opened
            for pos in self.sleeve.positions.values()
            if pos.qty != 0.0
        ]
        if self._last_decision_utc is not None:
            bounds.append(self._last_decision_utc)
        if not bounds:
            return {}  # nothing has ever been held: nothing can be due
        start_exclusive = min(bounds)
        rows: Dict[str, List[Dict[str, Any]]] = {}
        for symbol in sorted(symbols):
            settlements = self.feed.get_settled_funding(
                symbol, start_exclusive, decision_utc, decision_utc
            )
            rows[symbol] = [self._funding_row(s) for s in settlements]
        return rows

    # ------------------------------------------------------------------
    # execution of one decision
    # ------------------------------------------------------------------
    def _execute_decision(
        self, decision_utc: str, event_id: str, *, observed_at_utc: str
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        feature_cutoff = self._feature_cutoff(decision_utc)
        try:
            snapshot_payload = self._fetch_snapshot(decision_utc, feature_cutoff)
            fill_refs = self._fetch_fill_references(decision_utc, observed_at_utc)
            booking_rows = self._fetch_booking_funding_rows(decision_utc)
        except _FillBarPending:
            return None, "pending_fill_bar"
        except data_feed.DataBlocked as exc:
            return (
                self._build_blocked_record(
                    decision_utc, event_id, observed_at_utc, feature_cutoff, exc
                ),
                "data_blocked",
            )

        snapshot = FamilySnapshot(
            bars=snapshot_payload["bars"],
            basis_buckets=snapshot_payload["basis_buckets"],
            funding_settlements=snapshot_payload["funding_settlements"],
            btc_betas=self.btc_betas,
        )

        sleeve = self.sleeve
        sleeve.record_decision()
        sleeve.record_order_intent()
        sleeve.update_marks(fill_refs, decision_utc)
        equity_before = sleeve.equity_snapshot(decision_utc).equity
        funding_delta = self._book_settled_funding(booking_rows, fill_refs)
        equity_after_funding = sleeve.equity_snapshot().equity
        book = sleeve.books[self.primary_book]
        fee_before = book.fee
        slippage_before = book.slippage

        previous_weights = dict(sleeve.exposure_snapshot().get("weights", {}))
        proposal = self.adapter.decide(
            snapshot, decision_utc, feature_cutoff, previous_weights
        )

        approved, block = risk.check_and_apply(
            proposal.target_weights, self.caps, self.btc_betas
        )
        risk_status = (
            events.RISK_STATUS_BLOCKED if block.blocked else events.RISK_STATUS_OK
        )
        final_weights: Dict[str, float] = {}
        fills: List[accounting.VirtualFillEvent] = []
        accounting_status = events.ACCOUNTING_STATUS_OK
        outcome = "emitted"
        if block.blocked:
            outcome = "risk_blocked"
        else:
            final_weights = dict(approved)
            try:
                for symbol, side, qty in self._rebalance_steps(approved, fill_refs):
                    fills.append(
                        sleeve.apply_fill(
                            symbol,
                            side,
                            qty,
                            fill_refs[symbol],
                            self.tick_size,
                            decision_utc,
                        )
                    )
            except accounting.AccountingError:
                # Fail closed, record honestly: fills that DID occur are
                # recorded exactly as they occurred; the event is marked
                # UNAVAILABLE_FAIL_CLOSED (no leverage is ever permitted).
                accounting_status = events.ACCOUNTING_STATUS_UNAVAILABLE
                outcome = "accounting_fail_closed"
        self._last_decision_utc = decision_utc

        equity_after = sleeve.equity_snapshot(decision_utc).equity
        exposure = sleeve.exposure_snapshot(self.btc_betas)

        intent = no_order.emit_target_intent(
            cycle_id=events.CYCLE_ID,
            family_id=self.family_id,
            arm_id=self.arm_id,
            event_id=event_id,
            generated_utc=decision_utc,
            target_weights=final_weights,
            note="internal paper TARGET_INTENT (virtual fill path)",
        )
        if intent["action_type"] != "TARGET_INTENT":
            raise ExecutorError("only TARGET_INTENT may be emitted")

        digest_payload = dict(snapshot_payload)
        digest_payload["fill_bars"] = {
            symbol: fill_refs[symbol] for symbol in sorted(fill_refs)
        }
        digest_payload["booking_funding_settlements"] = booking_rows

        record = events.build_event(
            family_id=self.family_id,
            arm_id=self.arm_id,
            scheduled_decision_utc=decision_utc,
            observed_at_utc=observed_at_utc,
            feature_cutoff_utc=feature_cutoff,
            data_snapshot_digest=canonical_digest(digest_payload),
            code_freeze_sha=self.code_freeze_sha,
            config_digest=self.config_digest,
            cost_regime_digest=self.cost_regime_digest,
            eligible_symbols=list(proposal.eligible_symbols),
            rejected_symbols_with_reason=dict(proposal.rejected_symbols_with_reason),
            signal_values=dict(proposal.signal_values),
            target_weights=final_weights,
            previous_weights=previous_weights,
            virtual_fill_events=[f.as_dict() for f in fills],
            fee=book.fee - fee_before,
            slippage=book.slippage - slippage_before,
            funding_cashflow=funding_delta,
            price_pnl=(
                equity_after - equity_after_funding
                if equity_after is not None and equity_after_funding is not None
                else None
            ),
            total_pnl=(
                equity_after - equity_before
                if equity_after is not None and equity_before is not None
                else None
            ),
            cash=sleeve.cash,
            equity=equity_after,
            gross=exposure["gross"],
            net=exposure["net"],
            btc_beta=exposure["btc_beta"],
            data_status=events.DATA_STATUS_OK,
            accounting_status=accounting_status,
            risk_status=risk_status,
            no_order_proof=no_order.no_order_proof(PACKAGE_ROOT),
        )
        return record, outcome

    def _build_blocked_record(
        self,
        decision_utc: str,
        event_id: str,
        observed_at_utc: str,
        feature_cutoff_utc: str,
        exc: Exception,
    ) -> Dict[str, Any]:
        return events.build_data_blocked_event(
            family_id=self.family_id,
            arm_id=self.arm_id,
            scheduled_decision_utc=decision_utc,
            observed_at_utc=observed_at_utc,
            feature_cutoff_utc=feature_cutoff_utc,
            code_freeze_sha=self.code_freeze_sha,
            config_digest=self.config_digest,
            cost_regime_digest=self.cost_regime_digest,
            blocked_reason=str(exc),
        )

    # ------------------------------------------------------------------
    # funding + rebalance
    # ------------------------------------------------------------------
    def _book_settled_funding(
        self,
        booking_rows: Mapping[str, List[Dict[str, Any]]],
        fill_refs: Mapping[str, float],
    ) -> float:
        """Book settled funding once per settlement while held.

        The accounting layer enforces the holding window
        (ts_opened <= fundingTime < ts_closed) and dedups repeated
        bookings; the notional uses the sleeve's current mark.
        """
        total = 0.0
        for symbol in sorted(booking_rows):
            for row in booking_rows[symbol]:
                pos = self.sleeve.positions.get(symbol)
                if pos is not None and pos.last_mark is not None:
                    mark: Optional[float] = float(pos.last_mark)
                else:
                    mark = fill_refs.get(symbol)
                result = self.sleeve.apply_funding(
                    symbol,
                    str(row["funding_time_utc"]),
                    float(row["funding_rate"]),
                    mark,
                )
                if result.booked:
                    total += result.cashflow
        return total

    def _rebalance_steps(
        self, approved_weights: Mapping[str, float], fill_refs: Mapping[str, float]
    ) -> Iterator[Tuple[str, str, float]]:
        """Deterministic rebalance plan toward the approved target book.

        Phase order: reduce longs -> cover shorts -> open longs ->
        open shorts (each phase symbol-sorted). Reducing sells net
        against the position (POLICY: REDUCING_SELL_NETS_POSITION);
        new-short sells reach the unchanged no-leverage guards in
        accounting.apply_fill. There is NO execution buffer and NO
        slicing: every step trades the exact delta.
        """
        equity = self.sleeve.equity_snapshot().equity
        if equity is None:
            raise accounting.MarkGapError(
                "equity unavailable (mark gap); rebalance refused"
            )
        desired: Dict[str, float] = {}
        for symbol, weight in approved_weights.items():
            w = float(weight)
            if w == 0.0:
                continue
            if symbol not in fill_refs:
                raise ExecutorError(f"no fill reference for target symbol {symbol!r}")
            desired[symbol] = w * equity / fill_refs[symbol]
        current = {
            symbol: pos.qty
            for symbol, pos in self.sleeve.positions.items()
            if pos.qty != 0.0
        }

        reduce_longs: List[Tuple[str, float]] = []
        cover_shorts: List[Tuple[str, float]] = []
        open_longs: List[Tuple[str, float]] = []
        open_shorts: List[Tuple[str, float]] = []
        for symbol in sorted(set(desired) | set(current)):
            target_qty = desired.get(symbol, 0.0)
            cur_qty = current.get(symbol, 0.0)
            delta = target_qty - cur_qty
            if delta == 0.0:
                continue
            if delta > 0.0:
                if cur_qty < 0.0:
                    cover = min(delta, -cur_qty)  # buy back toward flat
                    cover_shorts.append((symbol, cover))
                    remainder = delta - cover
                else:
                    remainder = delta
                if remainder > 0.0:
                    open_longs.append((symbol, remainder))
            else:
                if cur_qty > 0.0:
                    trim = min(-delta, cur_qty)  # sell the long toward flat
                    reduce_longs.append((symbol, trim))
                    remainder = -delta - trim
                else:
                    remainder = -delta
                if remainder > 0.0:
                    open_shorts.append((symbol, remainder))

        for symbol, qty in reduce_longs:
            yield symbol, "sell", qty
        for symbol, qty in cover_shorts:
            yield symbol, "buy", qty
        for symbol, qty in open_longs:
            yield symbol, "buy", qty
        for symbol, qty in open_shorts:
            yield symbol, "sell", qty
