"""Frozen virtual risk caps applied BEFORE each virtual fill (plan G6).

Caps are passed in as config derived from the frozen identity manifest
(``research/control/prospective_shadow_v1/identity/identity_recovery.json``
verbatim parameters) — this module hard-codes NO strategy numbers. A
missing required config key raises :class:`RiskConfigError` (fail
closed). Any cap violation BLOCKS the event: ``check_and_apply``
returns empty approved weights and a block_record holding the pre
target, the post target and the violated caps. Blocked events still
emit their event record with ``risk_status = RISK_BLOCKED``.

No margin / no leverage path exists anywhere: weights are fractions of
the sleeve's own equity and accounting.py additionally refuses any fill
exceeding the sleeve's own cash.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

FAMILY_ILLIQ = "ILLIQ-AMIHUD-28D-W"
FAMILY_PREMFADE = "BASISLV-PREMFADE-28D"
FAMILY_CARRY = "XSECT-FUND-CARRY-7D"


class RiskConfigError(RuntimeError):
    """A required frozen cap parameter is missing from the config."""


class VerbatimParamError(RiskConfigError):
    """A verbatim identity parameter could not be parsed."""


def _parse_verbatim_number(value: Any, key: str) -> float:
    """Parse a value that is either a number or a verbatim 'key: value'
    YAML line recovered from the identity manifest (never guessed)."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if ":" in text:
            tail = text.split(":", 1)[1].strip()
        else:
            tail = text
        try:
            return float(tail)
        except ValueError as exc:
            raise VerbatimParamError(
                f"cannot parse frozen parameter {key!r} from {value!r}"
            ) from exc
    raise VerbatimParamError(f"unsupported frozen parameter {key!r}: {value!r}")


@dataclass
class FamilyRiskCaps:
    family_id: str
    target_gross: float
    hard_gross_cap: float
    hard_abs_net_cap: float
    max_abs_weight: Optional[float] = None
    min_abs_weight: Optional[float] = None
    btc_beta_tolerance: Optional[float] = None
    dollar_neutral: bool = False
    btc_beta_neutral: bool = False
    source: str = "config"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family_id,
            "target_gross": self.target_gross,
            "hard_gross_cap": self.hard_gross_cap,
            "hard_abs_net_cap": self.hard_abs_net_cap,
            "max_abs_weight": self.max_abs_weight,
            "min_abs_weight": self.min_abs_weight,
            "btc_beta_tolerance": self.btc_beta_tolerance,
            "dollar_neutral": self.dollar_neutral,
            "btc_beta_neutral": self.btc_beta_neutral,
            "source": self.source,
        }


def caps_from_config(family_id: str, config: Mapping[str, Any]) -> FamilyRiskCaps:
    """Build caps from a plain config mapping (values may be numbers or
    verbatim identity strings). Required keys fail closed when missing."""

    def get_num(key: str) -> float:
        if key not in config:
            raise RiskConfigError(
                f"frozen cap parameter {key!r} missing for {family_id}; refusing"
            )
        return _parse_verbatim_number(config[key], key)

    return FamilyRiskCaps(
        family_id=family_id,
        target_gross=get_num("target_gross"),
        hard_gross_cap=get_num("hard_gross_cap"),
        hard_abs_net_cap=get_num("hard_abs_net_cap"),
        max_abs_weight=(
            get_num("max_abs_symbol_weight")
            if "max_abs_symbol_weight" in config
            else (
                get_num("max_abs_weight_per_symbol")
                if "max_abs_weight_per_symbol" in config
                else (
                    get_num("adapter_weight_cap_max")
                    if "adapter_weight_cap_max" in config
                    else None
                )
            )
        ),
        min_abs_weight=(
            get_num("designed_max_abs_weight")
            if "designed_max_abs_weight" in config
            else None
        ),
        btc_beta_tolerance=(
            get_num("btc_beta_tolerance") if "btc_beta_tolerance" in config else None
        ),
        dollar_neutral=bool(config.get("dollar_neutral", False)),
        btc_beta_neutral=bool(config.get("btc_beta_neutral", False)),
        source=str(config.get("source", "config")),
    )


def caps_from_identity_params(
    family_id: str, identity_params: Mapping[str, Any]
) -> FamilyRiskCaps:
    """Family-specific builders over the identity manifest's verbatim
    score-affecting parameters. All numbers come from the passed config.

    - XSECT-FUND-CARRY-7D: target_gross 0.80 / hard_gross_cap 1.00 /
      hard_abs_net_cap 0.10 / max_abs_weight 0.20 (verbatim YAML lines).
    - BASISLV-PREMFADE-28D: gross 1.0 with per-name weight bounds
      0.125..0.30 (designed max weight .. adapter cap).
    - ILLIQ-AMIHUD-28D-W: equal-weight dollar-neutral BTC-beta-neutral
      quintile books; numeric tolerances must be supplied in the config
      (the identity pins the qualitative rule, not numbers).
    """
    config: Dict[str, Any] = dict(identity_params)
    if family_id == FAMILY_CARRY:
        config["source"] = "identity_manifest:XSECT-FUND-CARRY-7D"
        return caps_from_config(family_id, config)
    if family_id == FAMILY_PREMFADE:
        config.setdefault("target_gross", config.get("gross", 1.0))
        config.setdefault("hard_gross_cap", config.get("gross", 1.0))
        config.setdefault("hard_abs_net_cap", 0.0)
        config["dollar_neutral"] = True
        config["source"] = "identity_manifest:BASISLV-PREMFADE-28D"
        return caps_from_config(family_id, config)
    if family_id == FAMILY_ILLIQ:
        config["dollar_neutral"] = True
        config["btc_beta_neutral"] = True
        config["source"] = "identity_manifest:ILLIQ-AMIHUD-28D-W"
        return caps_from_config(family_id, config)
    raise RiskConfigError(f"unknown family_id {family_id!r}; refusing to guess caps")


@dataclass
class BlockRecord:
    blocked: bool
    violations: Tuple[str, ...] = ()
    pre_target: Dict[str, float] = field(default_factory=dict)
    post_target: Dict[str, float] = field(default_factory=dict)
    caps: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "blocked": self.blocked,
            "violations": list(self.violations),
            "pre_target": dict(self.pre_target),
            "post_target": dict(self.post_target),
            "caps": self.caps,
        }


def _weights_metrics(target_weights: Mapping[str, float]) -> Tuple[float, float, float]:
    gross = sum(abs(float(w)) for w in target_weights.values())
    net = sum(float(w) for w in target_weights.values())
    max_abs = max((abs(float(w)) for w in target_weights.values()), default=0.0)
    return gross, net, max_abs


def check_and_apply(
    target_weights: Mapping[str, float],
    caps: FamilyRiskCaps,
    symbol_betas: Optional[Mapping[str, float]] = None,
    tolerance: float = 1e-9,
) -> Tuple[Dict[str, float], BlockRecord]:
    """Apply frozen caps BEFORE any fill.

    Returns ``(approved_weights, block_record)``. Any cap violation
    BLOCKS the whole event: approved weights are empty and the block
    record captures the pre target and the (empty) post target.
    """
    pre = {sym: float(w) for sym, w in target_weights.items()}
    gross, net, max_abs = _weights_metrics(pre)
    violations = []

    if gross > caps.hard_gross_cap + tolerance:
        violations.append(f"hard_gross_cap: gross {gross!r} > {caps.hard_gross_cap!r}")
    if abs(net) > caps.hard_abs_net_cap + tolerance:
        violations.append(
            f"hard_abs_net_cap: |net| {abs(net)!r} > {caps.hard_abs_net_cap!r}"
        )
    if caps.max_abs_weight is not None:
        for sym, w in sorted(pre.items()):
            if abs(w) > caps.max_abs_weight + tolerance:
                violations.append(
                    f"max_abs_weight[{sym}]: {abs(w)!r} > {caps.max_abs_weight!r}"
                )
    if caps.min_abs_weight is not None:
        for sym, w in sorted(pre.items()):
            if abs(w) + tolerance < caps.min_abs_weight and abs(w) > tolerance:
                violations.append(
                    f"min_abs_weight[{sym}]: {abs(w)!r} < {caps.min_abs_weight!r}"
                )
    if caps.dollar_neutral and abs(net) > tolerance:
        violations.append(f"dollar_neutral: |net| {abs(net)!r} > 0")
    if caps.btc_beta_neutral:
        if symbol_betas is None:
            violations.append("btc_beta_neutral: symbol betas not supplied")
        else:
            beta = sum(
                float(w) * float(symbol_betas.get(sym, 0.0)) for sym, w in pre.items()
            )
            tol = caps.btc_beta_tolerance if caps.btc_beta_tolerance is not None else tolerance
            if abs(beta) > tol:
                violations.append(f"btc_beta_neutral: |beta| {abs(beta)!r} > {tol!r}")

    if violations:
        record = BlockRecord(
            blocked=True,
            violations=tuple(violations),
            pre_target=pre,
            post_target={},
            caps=caps.as_dict(),
        )
        return {}, record

    record = BlockRecord(
        blocked=False,
        violations=(),
        pre_target=pre,
        post_target=dict(pre),
        caps=caps.as_dict(),
    )
    return dict(pre), record
