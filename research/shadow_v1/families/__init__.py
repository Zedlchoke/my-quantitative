"""PROSPECTIVE-SHADOW-V1 family adapters (plan phase I, lane A8).

Thin adapters around the recovered historical logic of the three frozen
families. Every adapter:

- pins its identity strings verbatim (family ids, historical family id,
  historical verdict label — the labels are NOT rewritable, per the
  identity manifest's verdict_labels_policy);
- loads ALL numeric parameters from a config dict built from the
  identity manifest
  (research/control/prospective_shadow_v1/identity/identity_recovery.json)
  and refuses to start when the config disagrees with the manifest
  entry (:func:`FamilyAdapter.validate_config`);
- exposes ``decide(data_snapshot, decision_utc, feature_cutoff_utc,
  previous_weights) -> DecisionProposal`` — a pure function over the
  snapshot that raises ``DataBlocked`` when required PIT-complete
  inputs are missing.

The adapters hold NO accounting logic, NO network code and NO
third-party imports. Orders do not exist here: the engine emits
TARGET_INTENT only and fills virtually through the shared A2 surface
(accounting.py / no_order.py). None of the three frozen families has a
native fixed-price stop-loss or take-profit rule (plan section 9.6);
exit policies are scheduled rebalance / rank removal / risk-cap block
only.

Registry: ``FAMILY_REGISTRY`` maps family_id -> adapter class.
Counterfactual diagnostics arms (56-day neighbours, inverted books,
reverse funding control) are deliberately NOT built; their arm_id
namespaces are only reserved as strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence

from research.shadow_v1.data_feed import DataBlocked

FAMILY_ILLIQ = "ILLIQ-AMIHUD-28D-W"
FAMILY_PREMFADE = "BASISLV-PREMFADE-28D"
FAMILY_CARRY = "XSECT-FUND-CARRY-7D"
FAMILY_BANDRIDGE = "BTC4H-BANDRIDGE"

DECISION_CLOCK_WEEKLY_MONDAY = "WEEKLY_MONDAY_00Z"
DECISION_CLOCK_DAILY = "DAILY_00Z"

#: Structural constant: completed 15-minute bars per UTC day.
BARS_PER_DAY_15M = 96


class IdentityConfigError(ValueError):
    """Adapter config disagrees with the identity manifest; refuse to start."""


_NUMERIC_PREFIX_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def parse_verbatim_number(value: Any, key: str) -> float:
    """Parse a frozen parameter that is a JSON number or a verbatim
    ``key: value`` YAML line recovered from the identity manifest.
    Trailing unit suffixes on the numeric tail (e.g. "24h") are allowed;
    the numeric prefix must still be strict."""
    if isinstance(value, bool):
        raise IdentityConfigError(f"boolean is not a numeric identity parameter: {key!r}")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        tail = text.split(":", 1)[1].strip() if ":" in text else text
        match = _NUMERIC_PREFIX_RE.match(tail)
        if match is None:
            raise IdentityConfigError(
                f"cannot parse frozen parameter {key!r} from {value!r}"
            )
        return float(match.group(0))
    raise IdentityConfigError(f"unsupported frozen parameter {key!r}: {value!r}")


def parse_verbatim_int_list(value: Any, key: str) -> list:
    """Parse a verbatim ``key: [a, b, c]`` YAML line (or a JSON list)."""
    if isinstance(value, (list, tuple)):
        return [int(v) for v in value]
    if isinstance(value, str):
        text = value.strip()
        tail = text.split(":", 1)[1].strip() if ":" in text else text
        if not (tail.startswith("[") and tail.endswith("]")):
            raise IdentityConfigError(f"cannot parse list parameter {key!r} from {value!r}")
        inner = tail[1:-1].strip()
        if not inner:
            return []
        try:
            return [int(piece.strip()) for piece in inner.split(",")]
        except ValueError as exc:
            raise IdentityConfigError(
                f"cannot parse list parameter {key!r} from {value!r}"
            ) from exc
    raise IdentityConfigError(f"unsupported list parameter {key!r}: {value!r}")


def parse_verbatim_symbol_list(value: Any, key: str) -> list:
    """Parse a verbatim ``key: [SYMUSDT, ...]`` YAML line, a JSON list, or
    a single bare symbol string (e.g. "BTCUSDT")."""
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value]
    if isinstance(value, str):
        text = value.strip()
        tail = text.split(":", 1)[1].strip() if ":" in text else text
        if not (tail.startswith("[") and tail.endswith("]")):
            return [tail]  # single bare symbol
        inner = tail[1:-1].strip()
        if not inner:
            return []
        return [piece.strip() for piece in inner.split(",")]
    raise IdentityConfigError(f"unsupported list parameter {key!r}: {value!r}")


def parse_leading_int(text: str, key: str) -> int:
    """Parse the leading integer of a verbatim manifest prose line."""
    digits = ""
    for ch in text.strip():
        if ch.isdigit():
            digits += ch
        else:
            break
    if not digits:
        raise IdentityConfigError(f"no leading integer in {key!r}: {text!r}")
    return int(digits)


@dataclass(frozen=True)
class FamilySnapshot:
    """PIT data slice handed to ``decide``.

    All sequences are completed-bar/bucket/settlement dicts as produced
    by the A2 data interface (data_feed.py). The adapter treats the
    snapshot as read-only and never fetches anything itself.

    - ``bars``: symbol -> completed 15m bars
      ({open_time_utc, close_time_utc, close_price, quote_volume}).
    - ``basis_buckets``: symbol -> completed 15m perp-vs-index buckets
      ({open_time_utc, close_time_utc, futures_price, index_price}).
    - ``funding_settlements``: symbol -> settled funding events
      ({funding_time_utc, funding_rate}). Price-only families never
      read this field (funding is booked by the engine, never a signal).
    - ``btc_betas``: optional per-symbol BTC betas for the beta-neutral
      illiquidity book diagnostics.
    - ``listing_utc``: optional PIT listing evidence (first completed
      bar per symbol); defaults to the earliest bar in ``bars``.
    """

    bars: Mapping[str, Sequence[Mapping[str, Any]]] = field(default_factory=dict)
    basis_buckets: Mapping[str, Sequence[Mapping[str, Any]]] = field(default_factory=dict)
    funding_settlements: Mapping[str, Sequence[Mapping[str, Any]]] = field(default_factory=dict)
    btc_betas: Optional[Mapping[str, float]] = None
    listing_utc: Optional[Mapping[str, str]] = None


@dataclass(frozen=True)
class DecisionProposal:
    """Pure output of ``decide``; the engine turns this into one event."""

    family_id: str
    arm_id: str
    eligible_symbols: tuple
    rejected_symbols_with_reason: Mapping[str, str]
    signal_values: Mapping[str, float]
    target_weights: Mapping[str, float]
    exit_policy: str
    decision_utc: str
    feature_cutoff_utc: str
    previous_weights: Mapping[str, float]
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


class FamilyAdapter:
    """Base class: identity pinning + manifest-validated config."""

    FAMILY_ID: str = ""
    HISTORICAL_FAMILY_ID: str = ""
    HISTORICAL_VERDICT_LABEL: str = ""
    ARM_ID: str = ""
    EXIT_POLICY: str = ""
    DECISION_CLOCK: str = ""
    HOLDING_PERIOD: str = ""

    #: family_id key expected in an identity manifest document.
    MANIFEST_FAMILY_ID: str = ""

    def __init__(self, config: Mapping[str, Any], identity_entry: Mapping[str, Any]):
        validated = self.validate_config(config, identity_entry)
        self.config = validated

    # -- config contract -------------------------------------------------
    @staticmethod
    def build_frozen(identity_params: Mapping[str, Any]) -> Dict[str, Any]:
        """Derive the frozen numeric config from verbatim manifest params."""
        raise NotImplementedError

    @classmethod
    def build_config(
        cls, identity_entry: Mapping[str, Any], engine_config: Optional[Mapping[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build the adapter config from one identity manifest family entry.

        ``engine_config`` carries engine-level run parameters that the
        manifest does not pin (numerical tolerances, PIT filter
        thresholds). Required engine keys fail closed in
        :meth:`validate_config`.
        """
        params = identity_entry.get("score_affecting_parameters")
        if not isinstance(params, Mapping) or not params:
            raise IdentityConfigError(
                f"{cls.FAMILY_ID}: identity entry has no score_affecting_parameters"
            )
        return {
            "frozen": cls.build_frozen(params),
            "engine": dict(engine_config or {}),
        }

    @classmethod
    def validate_config(
        cls, config: Mapping[str, Any], identity_entry: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Refuse to start unless config agrees with the manifest entry.

        Checks, in order:
        1. the entry's pinned identity strings equal the class constants;
        2. ``config["frozen"]`` equals a fresh derivation from the
           entry's verbatim score-affecting parameters;
        3. required engine keys are present (fail closed).
        """
        params = identity_entry.get("score_affecting_parameters")
        if not isinstance(params, Mapping) or not params:
            raise IdentityConfigError(
                f"{cls.FAMILY_ID}: identity entry has no score_affecting_parameters"
            )
        pinned = (
            ("family_id", cls.FAMILY_ID),
            ("historical_family_id", cls.HISTORICAL_FAMILY_ID),
            ("historical_verdict_label", cls.HISTORICAL_VERDICT_LABEL),
        )
        for key, expected in pinned:
            actual = identity_entry.get(key)
            if actual != expected:
                raise IdentityConfigError(
                    f"{cls.FAMILY_ID}: manifest entry {key}={actual!r} disagrees "
                    f"with pinned identity {expected!r}; refusing to start"
                )
        expected_frozen = cls.build_frozen(params)
        got_frozen = config.get("frozen") if isinstance(config, Mapping) else None
        if got_frozen != expected_frozen:
            raise IdentityConfigError(
                f"{cls.FAMILY_ID}: config frozen values disagree with the "
                f"identity manifest: config={got_frozen!r} expected={expected_frozen!r}"
            )
        engine = config.get("engine") if isinstance(config, Mapping) else None
        if not isinstance(engine, Mapping):
            raise IdentityConfigError(f"{cls.FAMILY_ID}: config missing 'engine' mapping")
        for key in cls.required_engine_keys():
            if key not in engine:
                raise IdentityConfigError(
                    f"{cls.FAMILY_ID}: required engine parameter {key!r} missing; "
                    "refusing to start"
                )
        return {"frozen": expected_frozen, "engine": dict(engine)}

    @classmethod
    def required_engine_keys(cls) -> tuple:
        """Engine-level config keys that must exist (fail closed)."""
        return ()

    @classmethod
    def from_identity_manifest(
        cls, manifest: Mapping[str, Any], engine_config: Optional[Mapping[str, Any]] = None
    ) -> "FamilyAdapter":
        """Locate this family's entry in the loaded identity manifest JSON
        and construct a validated adapter from it."""
        for entry in manifest.get("families", []):
            if entry.get("family_id") == cls.MANIFEST_FAMILY_ID:
                config = cls.build_config(entry, engine_config)
                return cls(config, entry)
        raise IdentityConfigError(
            f"{cls.FAMILY_ID}: family entry {cls.MANIFEST_FAMILY_ID!r} not found "
            "in identity manifest"
        )

    # -- decision --------------------------------------------------------
    def decide(
        self,
        data_snapshot: FamilySnapshot,
        decision_utc: str,
        feature_cutoff_utc: str,
        previous_weights: Optional[Mapping[str, float]] = None,
    ) -> DecisionProposal:
        raise NotImplementedError


from research.shadow_v1.families.illiq_amihud import IlliqAmihudAdapter  # noqa: E402
from research.shadow_v1.families.basislv_premfade import (  # noqa: E402
    BasislvPremfadeAdapter,
)
from research.shadow_v1.families.xsect_fund_carry import (  # noqa: E402
    XsectFundCarryAdapter,
)
from research.shadow_v1.families.btc4h_bandridge import (  # noqa: E402
    Btc4hBandridgeAdapter,
)

#: family_id -> adapter class (the three active anchor sleeves only).
FAMILY_REGISTRY: Dict[str, type] = {
    IlliqAmihudAdapter.FAMILY_ID: IlliqAmihudAdapter,
    BasislvPremfadeAdapter.FAMILY_ID: BasislvPremfadeAdapter,
    XsectFundCarryAdapter.FAMILY_ID: XsectFundCarryAdapter,
    Btc4hBandridgeAdapter.FAMILY_ID: Btc4hBandridgeAdapter,
}

__all__ = [
    "FamilySnapshot",
    "DecisionProposal",
    "FamilyAdapter",
    "IdentityConfigError",
    "DataBlocked",
    "FAMILY_REGISTRY",
    "FAMILY_ILLIQ",
    "FAMILY_PREMFADE",
    "FAMILY_CARRY",
    "DECISION_CLOCK_WEEKLY_MONDAY",
    "DECISION_CLOCK_DAILY",
    "IlliqAmihudAdapter",
    "BasislvPremfadeAdapter",
    "XsectFundCarryAdapter",
    "Btc4hBandridgeAdapter",
    "FAMILY_BANDRIDGE",
]
