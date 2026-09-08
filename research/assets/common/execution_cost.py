"""Execution-cost interface (owner: A2, PLAN_stocks.md section 6).

Commission / spread / slippage / impact interface shared by all asset
classes.  Every model carries an explicit, immutable
:class:`CostModelId`; manifests and instruments reference that id, never a
default cost model.  Estimates are neutral :class:`ExecutionCostEstimate`
records with non-negative, finite cost components.
"""

from __future__ import annotations

import abc
import math
from dataclasses import dataclass
from typing import Any, Mapping

from research.assets.common.contracts import (
    canonical_json,
    canonical_payload,
    require_finite_float,
    require_token,
)


@dataclass(frozen=True)
class CostModelId:
    """Explicit immutable cost-model identifier.

    Wrap the id string once; the frozen dataclass makes accidental mutation
    impossible and gives equality/hash by value for contract comparison.
    """

    value: str

    def __post_init__(self) -> None:
        require_token(self.value, "CostModelId.value")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, kw_only=True)
class ExecutionCostEstimate:
    """Neutral per-fill cost estimate; every component is >= 0 and finite."""

    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    spread_cost: float
    slippage_cost: float
    impact_cost: float
    currency: str
    cost_model_id: str

    def __post_init__(self) -> None:
        require_token(self.symbol, "symbol")
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"side must be BUY or SELL, got {self.side!r}")
        for name in ("quantity", "price"):
            require_finite_float(getattr(self, name), name)
        if float(self.quantity) <= 0:
            raise ValueError(f"quantity must be > 0, got {self.quantity!r}")
        if float(self.price) <= 0:
            raise ValueError(f"price must be > 0, got {self.price!r}")
        for name in ("commission", "spread_cost", "slippage_cost", "impact_cost"):
            require_finite_float(getattr(self, name), name)
            if float(getattr(self, name)) < 0:
                raise ValueError(f"{name} must be >= 0, got {getattr(self, name)!r}")
        require_token(self.currency, "currency")
        require_token(self.cost_model_id, "cost_model_id")

    def total(self) -> float:
        """Sum of the four cost components (carry is never baked in here)."""
        return math.fsum((
            float(self.commission),
            float(self.spread_cost),
            float(self.slippage_cost),
            float(self.impact_cost),
        ))

    def canonical_payload(self) -> dict[str, Any]:
        return canonical_payload(self)

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_payload())


def parse_cost_estimate(payload: Mapping[str, Any]) -> ExecutionCostEstimate:
    """Rebuild an :class:`ExecutionCostEstimate` from its canonical payload."""
    return ExecutionCostEstimate(
        symbol=payload["symbol"],
        side=payload["side"],
        quantity=payload["quantity"],
        price=payload["price"],
        commission=payload["commission"],
        spread_cost=payload["spread_cost"],
        slippage_cost=payload["slippage_cost"],
        impact_cost=payload["impact_cost"],
        currency=payload["currency"],
        cost_model_id=payload["cost_model_id"],
    )


class ExecutionCostModel(abc.ABC):
    """Interface implemented per asset class / venue."""

    @property
    @abc.abstractmethod
    def model_id(self) -> CostModelId:
        """The immutable id referenced by manifests and instrument specs."""

    @abc.abstractmethod
    def estimate(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        context: Mapping[str, Any] | None = None,
    ) -> ExecutionCostEstimate:
        """Cost estimate for one fill under this model."""
