"""Asset-neutral experiment/data contracts (owner: A2, PLAN_stocks.md section 6).

Rules frozen here:

* every new multi-asset manifest carries explicit ``asset_class``, ``venue``,
  ``calendar_id`` and ``cost_model_id`` plus provider provenance fields;
* there is NO default asset class, venue, calendar or cost model — a missing
  value is a construction error, never a silent fallback (in particular there
  is no 24/7 calendar default anywhere);
* position-PnL profit factor and return-series profit factor are strictly
  separate fields with separate validators, mirroring the
  ``position_pf`` vs ``stats_returns``-series distinction already present in
  ``research/protocol/metrics.py``;
* serialization is canonical (sorted keys, tight separators) so the
  canonical JSON of a contract is byte-stable across processes.

This module is self-contained (stdlib only) and never imports
``research.protocol`` — the asset-neutral boundary must not depend on the
historical crypto protocol implementation.  ``crypto_compat`` is the only
adapter allowed to read historical manifests.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

# --- asset-class vocabulary ------------------------------------------------ #
# Values are namespaced identifiers, never guessed.  Historical crypto
# experiments map to ``CRYPTO_PERP`` (see crypto_compat).
CRYPTO_PERP = "CRYPTO_PERP"
US_CASH_EQUITY = "US_CASH_EQUITY"
FX_SPOT = "FX_SPOT"

ASSET_CLASS_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+/@-]*$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def require_asset_class(value: Any, field: str = "asset_class") -> str:
    """Validate an asset-class token; raise ``ValueError`` when invalid."""
    if not isinstance(value, str) or not ASSET_CLASS_PATTERN.match(value):
        raise ValueError(
            f"{field} must match {ASSET_CLASS_PATTERN.pattern}, got {value!r}"
        )
    return value


def require_token(value: Any, field: str) -> str:
    """Validate a non-empty identifier token (venue, calendar_id, ...)."""
    if not isinstance(value, str) or not value.strip() or not _TOKEN_RE.match(value):
        raise ValueError(f"{field} must be a non-empty identifier token, got {value!r}")
    return value


def require_digest_hex(value: Any, field: str) -> str:
    """Validate a lowercase sha256 hex digest string."""
    if not isinstance(value, str) or not _DIGEST_RE.match(value):
        raise ValueError(f"{field} must be a 64-char lowercase sha256 hex, got {value!r}")
    return value


def require_finite_float(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a real number, got {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite, got {value!r}")
    if positive and number <= 0:
        raise ValueError(f"{field} must be > 0, got {value!r}")
    return number


# --- canonical serialization ----------------------------------------------- #
def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float cannot be canonicalized: {value!r}")
        return value
    if isinstance(value, MetricReading):
        return {"value": value.value, "reason": value.reason}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in value}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return canonical_payload(value)
    raise ValueError(f"value not canonicalizable: {type(value).__name__}")


def canonical_payload(obj: Any) -> dict[str, Any]:
    """JSON-safe dict of a dataclass with every field explicitly materialized."""
    if not dataclasses.is_dataclass(obj) or isinstance(obj, type):
        raise TypeError(f"canonical_payload expects a dataclass instance, got {type(obj)!r}")
    return {
        fld.name: _jsonable(getattr(obj, fld.name))
        for fld in dataclasses.fields(obj)
    }


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Byte-stable canonical JSON (sorted keys, tight separators, UTF-8)."""
    return json.dumps(_jsonable(dict(payload)), sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- metric readings -------------------------------------------------------- #
@dataclass(frozen=True)
class MetricReading:
    """A metric value or an explicit reason for its absence.

    Mirrors ``contracts.protocol.MetricValue`` semantics without importing it:
    a ``None`` value REQUIRES a non-empty reason; a known value must NOT
    carry a reason.  Silent ``0.0`` defaults are forbidden by construction.
    """

    value: float | None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.value is None:
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError("None metric value requires a non-empty reason")
        elif self.reason is not None:
            raise ValueError("a known metric value must not carry a reason")
        else:
            require_finite_float(self.value, "value")

    @classmethod
    def known(cls, value: float) -> "MetricReading":
        return cls(value=require_finite_float(value, "value"), reason=None)

    @classmethod
    def missing(cls, reason: str) -> "MetricReading":
        return cls(value=None, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "reason": self.reason}


# --- the asset-neutral experiment contract ---------------------------------- #
@dataclass(frozen=True, kw_only=True)
class AssetExperimentContract:
    """Asset-neutral experiment contract for a scored multi-asset cell.

    All identity fields are keyword-only (a positional swap of similarly
    typed fields cannot compile into a silent mistake) and validated.
    ``calendar_id`` references an id in the session-calendar registry; it is
    NEVER defaulted (no 24/7 fallback), and ``cost_model_id`` references an
    immutable :class:`~research.assets.common.execution_cost.CostModelId`.
    """

    schema_version: int = 1
    experiment_id: str
    asset_class: str
    venue: str
    calendar_id: str
    cost_model_id: str
    universe_digest: str
    family_id: str
    arm_id: str
    arm_config_digest: str
    calendar_version: str | None = None
    provider_id: str | None = None
    provider_schema_digest: str | None = None
    window_digest: str | None = None
    split_policy_digest: str | None = None
    benchmark_digest: str | None = None
    position_pnl_profit_factor: MetricReading | None = None
    return_series_profit_factor: MetricReading | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise ValueError("schema_version must be a positive int")
        require_token(self.experiment_id, "experiment_id")
        require_asset_class(self.asset_class)
        require_token(self.venue, "venue")
        require_token(self.calendar_id, "calendar_id")
        require_token(self.cost_model_id, "cost_model_id")
        require_digest_hex(self.universe_digest, "universe_digest")
        require_token(self.family_id, "family_id")
        require_token(self.arm_id, "arm_id")
        require_digest_hex(self.arm_config_digest, "arm_config_digest")
        for optional in (
            "calendar_version", "provider_id", "provider_schema_digest",
            "window_digest", "split_policy_digest", "benchmark_digest",
        ):
            value = getattr(self, optional)
            if value is not None:
                require_token(value, optional)
        for digest_field in (
            "provider_schema_digest", "window_digest",
            "split_policy_digest", "benchmark_digest",
        ):
            value = getattr(self, digest_field)
            if value is not None:
                require_digest_hex(value, digest_field)
        for pf_field in ("position_pnl_profit_factor", "return_series_profit_factor"):
            value = getattr(self, pf_field)
            if value is not None and not isinstance(value, MetricReading):
                raise ValueError(f"{pf_field} must be a MetricReading or None")

    def canonical_payload(self) -> dict[str, Any]:
        return canonical_payload(self)

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_payload())

    def assert_production_ready(self) -> None:
        """Fail-closed helper for real scoring runs (tests may skip it).

        Rejects TEST_ONLY calendars and missing provider provenance so a
        development stub can never be scored as if it were production data.
        """
        from research.assets.common.calendar import require_production_calendar_id

        require_production_calendar_id(self.calendar_id, context="AssetExperimentContract")
        missing = [
            name
            for name in ("provider_id", "provider_schema_digest")
            if getattr(self, name) is None
        ]
        if missing:
            raise ValueError(f"production contract requires non-null {sorted(missing)}")


@dataclass(frozen=True, kw_only=True)
class ScoredResultContract:
    """Scored outcome of one contract cell.

    The two profit factors are deliberately distinct, individually validated
    fields (mirroring ``research/protocol/metrics.py``: ``position_pf`` comes
    from the net position-PnL series while the return-series PF comes from
    the equity/stats-returns side).  They must never be collapsed into a
    single ``profit_factor`` value.
    """

    schema_version: int = 1
    experiment_id: str
    asset_class: str
    position_pnl_profit_factor: MetricReading
    return_series_profit_factor: MetricReading

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise ValueError("schema_version must be a positive int")
        require_token(self.experiment_id, "experiment_id")
        require_asset_class(self.asset_class)
        if not isinstance(self.position_pnl_profit_factor, MetricReading):
            raise ValueError("position_pnl_profit_factor must be a MetricReading")
        if not isinstance(self.return_series_profit_factor, MetricReading):
            raise ValueError("return_series_profit_factor must be a MetricReading")

    def canonical_payload(self) -> dict[str, Any]:
        return canonical_payload(self)

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_payload())
