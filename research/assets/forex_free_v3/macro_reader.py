"""FOREX-FREE-V3 macro reader: thin as-of policy-rate helper for family lanes.

This is the ONLY macro access path a V3 family module is allowed.  It wraps
the adopted P0 point-in-time core (``research.data_fusion.pit.select_asof``)
so a family reads ECB/BIS policy-rate vintages with availability gating and
FAILS CLOSED when the vintage data is absent:

* ``MacroDataBlocked`` (reason ``BLOCKED_DATA``) is raised when a required
  vintage file or rate-area series is missing entirely.  A missing series is
  never silently replaced by an empty book.
* ``policy_rate(area, decision_ts)`` returns the most recent observation
  whose ``available_time_utc <= decision_ts`` (and whose effective date, when
  recorded, is ``<= decision_ts``) or ``None`` when no eligible vintage
  exists at that instant -- the NO_EVAL fail-closed semantics both selected
  proposals freeze ("never backfilled").
* The reader NEVER computes, interpolates or fill-forwards a rate.  It only
  selects what the vintages authorize at the decision instant.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Mapping

from research.assets.forex.conversion import parse_utc_timestamp
from research.data_fusion.models import NormalizedRecord, require_utc
from research.data_fusion.pit import select_asof

__all__ = ["BLOCKED_DATA", "MacroDataBlocked", "PolicyRateReader", "MacroReader"]

BLOCKED_DATA = "BLOCKED_DATA"

_DATETIME_FIELDS = (
    "event_time_utc",
    "available_time_utc",
    "effective_time_utc",
    "vintage_time_utc",
    "retrieved_time_utc",
)


class MacroDataBlocked(RuntimeError):
    """A required macro vintage input is missing; the run fails closed."""

    reason = BLOCKED_DATA

    def __init__(self, detail: str) -> None:
        super().__init__(f"{BLOCKED_DATA}: {detail}")
        self.detail = detail


def _record_from_payload(payload: Mapping[str, Any]) -> NormalizedRecord:
    """Rebuild one NormalizedRecord from its canonical payload (JSON-safe)."""
    values = dict(payload)
    for field in _DATETIME_FIELDS:
        raw = values.get(field)
        if raw is None:
            continue
        values[field] = parse_utc_timestamp(raw, field=field)
    return NormalizedRecord(**values)


class PolicyRateReader:
    """Availability-gated as-of reader over one rate area per vintage series."""

    def __init__(self, series_by_area: Mapping[str, list]) -> None:
        self._series: dict[str, list[NormalizedRecord]] = {
            str(area): list(records) for area, records in series_by_area.items()
        }

    def policy_rate(self, area: str, decision_ts: str | datetime,
                    *, require_effective: bool = True) -> float | None:
        """As-of policy rate for ``area`` at ``decision_ts``; ``None`` = NO_EVAL.

        A decision at T never reads a row whose available_time_utc > T
        (P0 regression-pinned semantics, enforced by ``select_asof``).
        """
        records = self._series.get(area)
        if records is None:
            raise MacroDataBlocked(f"no policy-rate vintage series for area {area!r}")
        decision = require_utc(
            decision_ts if isinstance(decision_ts, datetime)
            else parse_utc_timestamp(decision_ts, field="decision_ts"),
            "decision_ts",
        )
        winner = select_asof(records, decision, require_effective=require_effective)
        if winner is None:
            return None
        try:
            return float(winner.value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise MacroDataBlocked(
                f"policy-rate value for area {area!r} at {decision.isoformat()} is not numeric"
            ) from exc

    def differential(self, base_area: str, quote_area: str,
                     decision_ts: str | datetime) -> float | None:
        """``r_base - r_quote`` as annualized decimals; ``None`` = NO_EVAL."""
        base = self.policy_rate(base_area, decision_ts)
        if base is None:
            return None
        quote = self.policy_rate(quote_area, decision_ts)
        if quote is None:
            return None
        return base - quote

    @classmethod
    def from_data_paths(cls, data_paths: Mapping[str, Any]) -> "PolicyRateReader":
        """Constructor form of :func:`from_data_paths` (fail-closed BLOCKED_DATA)."""
        return from_data_paths(data_paths)


# Backwards-friendly alias used by the runner contract.
MacroReader = PolicyRateReader


def from_data_paths(data_paths: Mapping[str, Any]) -> PolicyRateReader:
    """Build a reader from the runner's ``data_paths`` dict; fail closed.

    Expected shape::

        data_paths = {"macro_vintages": {"US": "<path>.json", "EMU": "<path>.json", ...}}

    Each JSON file holds a list of NormalizedRecord canonical payloads (the
    exact bytes the P0 adapters publish).  A missing ``macro_vintages`` key,
    a missing file, or an unparsable file raises ``MacroDataBlocked``
    (``BLOCKED_DATA``) -- never an empty series.
    """
    macro = data_paths.get("macro_vintages")
    if not isinstance(macro, Mapping) or not macro:
        raise MacroDataBlocked("data_paths is missing the 'macro_vintages' mapping")
    series: dict[str, list[NormalizedRecord]] = {}
    for area, path in macro.items():
        if not os.path.exists(path):
            raise MacroDataBlocked(f"vintage file for area {area!r} not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payloads = json.load(handle)
        except (OSError, ValueError) as exc:
            raise MacroDataBlocked(f"vintage file for area {area!r} is unreadable: {path} ({exc})") from exc
        if isinstance(payloads, Mapping):
            payloads = [payloads]
        if not isinstance(payloads, list) or not payloads:
            raise MacroDataBlocked(f"vintage file for area {area!r} holds no records: {path}")
        try:
            series[str(area)] = [_record_from_payload(p) for p in payloads]
        except (TypeError, ValueError) as exc:
            raise MacroDataBlocked(
                f"vintage payload for area {area!r} failed normalization: {exc}"
            ) from exc
    return PolicyRateReader(series)
