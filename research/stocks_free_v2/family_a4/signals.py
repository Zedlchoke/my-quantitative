"""Signals for the frozen ``A4_XSEC_ETF_RELATIVE_MOMENTUM`` family (Z5/A6).

SCHEDULE-ONLY.  This module computes the frozen cross-sectional momentum
features and the per-arm ranking from INJECTED total-return series; it never
computes returns of the strategy, PnL, PF or any scored metric.

Everything numeric here is read from the frozen, read-only spec
``research/proposals/stocks_free_v2/a4_z3_relative_momentum_spec.json``
(sha256 of exact file bytes:
``98d5307c3c3810a236f230475b190b34bd38461461cc7ea0a5ebdf38741416fa``).
Numeric constants that the spec states only in prose (252/21 window, top-3,
35% cap, 253-session readiness) are extracted from the spec text with strict
regexes and fail closed when absent, so a drifted spec can never silently
re-freeze different constants.

Spec anchors for each extracted constant (quoted):

- momentum score: ``"mom_i(t) = P^TR_i(t-21) / P^TR_i(t-252) - 1"``.
- volatility: ``"sigma_i(t) = sample standard deviation of daily log TR
  returns over sessions [t-252, t-21] (the same formation window, 231 daily
  observations)"``.
- readiness: ``"a decision at t is VALID for ETF i only if the full
  253-session TR window [t-252, t] exists in accepted coverage"``.
- selection size: ``"rank by mom_i(t) descending, hold top 3 equal-weight"``.
- cap: ``"per-ETF weight cap 35% of gross for all arms"``.
- control: ``"with the ranking sign REVERSED: hold the BOTTOM 3 sectors by
  mom_i(t)"`` (identical everything else — buffers are forbidden so the
  control differs from the anchor by the ranking sign only).
- ties: ``"deterministic tie-break: ascending symbol; no randomization"``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Mapping, Sequence

FAMILY_ID = "A4_XSEC_ETF_RELATIVE_MOMENTUM"

FROZEN_SPEC_REL_PATH = (
    "research/proposals/stocks_free_v2/a4_z3_relative_momentum_spec.json"
)
# sha256 of the exact file bytes of the frozen spec JSON (recorded by the Z3
# A4 lane in research/audits/stocks_free_v2/z3_a4/digests.json and in the
# frozen selection_free.json).  Recomputed and asserted by the tests.
FROZEN_SPEC_FILE_SHA256 = (
    "98d5307c3c3810a236f230475b190b34bd38461461cc7ea0a5ebdf38741416fa"
)

ARM_ID_ANCHOR = "ARM_A4_ANCHOR_MOM121_EQW_TOP3"
ARM_ID_NEIGHBOUR = "ARM_A4_NEIGHBOR_VOLADJ_MOM121_INVVOL_TOP3"
ARM_ID_NEGCTRL = "ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121"
ARM_IDS = (ARM_ID_ANCHOR, ARM_ID_NEIGHBOUR, ARM_ID_NEGCTRL)

SCORE_MOM = "mom"
SCORE_MRA = "mra"
WEIGHT_EQUAL = "equal"
WEIGHT_INVERSE_VOL = "inverse_vol"


def canonical_json(payload: object) -> str:
    """Canonical JSON text (sorted keys, tight separators, ASCII)."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )


def arm_config_digest(spec: Mapping[str, object]) -> str:
    """Canonical sha256 over the frozen spec JSON (double-generation stable).

    The digest is taken over the *canonical* JSON rendering of the parsed
    spec (sorted keys, tight separators), so it is independent of the file's
    whitespace while pinning every frozen value.
    """
    return hashlib.sha256(canonical_json(dict(spec)).encode("utf-8")).hexdigest()


def spec_file_sha256(spec_bytes: bytes) -> str:
    """sha256 of the exact spec file bytes (frozen-artifact identity)."""
    return hashlib.sha256(spec_bytes).hexdigest()


def load_frozen_spec(repo_root: str | Path | None = None) -> dict:
    """Load the frozen spec JSON (config artifact, never market data)."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    path = Path(repo_root) / FROZEN_SPEC_REL_PATH
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def _extract(pattern: str, text: str, label: str) -> str:
    """Fail-closed single-match extraction from spec prose."""
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise ValueError(
            f"frozen spec constant {label!r}: expected exactly one match for "
            f"{pattern!r}, found {len(matches)}; refusing to guess"
        )
    return matches[0]


@dataclass(frozen=True)
class SpecConstants:
    """Numeric constants extracted from the frozen spec (fail-closed)."""

    formation_sessions: int          # 252 (~12 months formation)
    skip_sessions: int               # 21  (~1 month skip)
    readiness_sessions: int          # 253 (full window [t-252, t])
    sigma_observations: int          # 231 daily log TR returns
    top_n: int                       # 3
    per_etf_cap: float               # 0.35
    rankable: tuple[str, ...]        # the 10 sector ETFs (spec list)
    base_case_cost_bps: float        # 7 bps one-way (DECLARED, never applied here)

    def __post_init__(self) -> None:
        if self.readiness_sessions != self.formation_sessions + 1:
            raise ValueError(
                "frozen spec inconsistency: readiness window "
                f"{self.readiness_sessions} != formation {self.formation_sessions} + 1"
            )
        if self.sigma_observations != self.formation_sessions - self.skip_sessions:
            raise ValueError(
                "frozen spec inconsistency: sigma observations "
                f"{self.sigma_observations} != formation - skip"
            )
        if len(set(self.rankable)) != len(self.rankable) or not self.rankable:
            raise ValueError("frozen spec rankable cross-section must be unique/non-empty")
        if not 0.0 < self.per_etf_cap <= 1.0:
            raise ValueError("frozen spec per-ETF cap must lie in (0, 1]")


def parse_spec_constants(spec: Mapping[str, object]) -> SpecConstants:
    """Extract the frozen numeric constants from the spec (fail-closed)."""
    features = spec["feature_definitions"]
    portfolio = spec["portfolio_construction"]
    anchor_def = next(
        arm["definition"] for arm in spec["arms"] if arm["arm_id"] == ARM_ID_ANCHOR
    )

    skip_raw = _extract(
        r"\(t-(\d+)\)\s*/\s*P\^TR_i\(t-(\d+)\)",
        features["momentum_score_raw"],
        "momentum_score_raw window",
    )
    skip_sessions, formation_sessions = (int(part) for part in skip_raw)
    readiness_sessions = int(
        _extract(r"full\s+(\d+)-session TR window", features["data_readiness_rule"], "readiness")
    )
    sigma_obs = int(
        _extract(r"(\d+) daily observations", features["volatility_score"], "sigma observations")
    )
    top_n = int(_extract(r"hold top (\d+) equal-weight", anchor_def, "top_n"))
    cap_pct = float(
        _extract(
            r"(\d+(?:\.\d+)?)%\s+of gross",
            portfolio["per_etf_weight_cap"],
            "per-ETF cap",
        )
    )
    cost_bps = float(
        _extract(
            r"(\d+(?:\.\d+)?) bps one-way",
            spec["costs_and_delay"]["base_case_cost"],
            "base case cost",
        )
    )
    rankable = tuple(spec["cohort"]["rankable_cross_section_10"])
    return SpecConstants(
        formation_sessions=formation_sessions,
        skip_sessions=skip_sessions,
        readiness_sessions=readiness_sessions,
        sigma_observations=sigma_obs,
        top_n=top_n,
        per_etf_cap=cap_pct / 100.0,
        rankable=rankable,
        base_case_cost_bps=cost_bps,
    )


def parse_force_flat_dates(spec: Mapping[str, object]) -> tuple[str, ...]:
    """Force-flat event dates (ISO strings) parsed from the frozen spec.

    Spec: ``"S0_FOLD_1 scored_end 2020-09-01 close"`` ... and
    ``"S0 terminal 2025-07-31 close"`` — one date per event string.
    """
    events = spec["warmup_folds_terminal"]["force_flat_events"]
    dates = []
    for event in events:
        found = re.findall(r"(\d{4}-\d{2}-\d{2})", event)
        if len(found) != 1:
            raise ValueError(f"force-flat event {event!r} must carry exactly one date")
        dates.append(found[0])
    if len(set(dates)) != len(dates):
        raise ValueError("force-flat events must carry distinct dates")
    return tuple(sorted(dates))


@dataclass(frozen=True)
class ArmConfig:
    """One frozen arm configuration (one shared code path, parameterized).

    The negative control is the anchor with ``ranking_sign`` flipped and
    nothing else (spec: buffers forbidden so the difference is the ranking
    sign only).
    """

    arm_id: str
    role: str
    score: str                    # SCORE_MOM | SCORE_MRA
    ranking_sign: int             # +1 rank descending (top-N); -1 ascending (bottom-N)
    weighting: str                # WEIGHT_EQUAL | WEIGHT_INVERSE_VOL
    top_n: int
    per_etf_cap: float
    formation_sessions: int
    skip_sessions: int
    readiness_sessions: int

    def __post_init__(self) -> None:
        if self.score not in (SCORE_MOM, SCORE_MRA):
            raise ValueError(f"unknown score {self.score!r}")
        if self.ranking_sign not in (1, -1):
            raise ValueError("ranking_sign must be +1 or -1")
        if self.weighting not in (WEIGHT_EQUAL, WEIGHT_INVERSE_VOL):
            raise ValueError(f"unknown weighting {self.weighting!r}")

    def structural_fields(self) -> dict[str, object]:
        """All frozen fields (used by the sign-flip structural test)."""
        return {f.name: getattr(self, f.name) for f in fields(self)}


def build_arm_configs(spec: Mapping[str, object]) -> tuple[ArmConfig, ArmConfig, ArmConfig]:
    """The three preregistered arms, generically from the frozen spec."""
    consts = parse_spec_constants(spec)
    roles = {arm["arm_id"]: arm.get("role", "") for arm in spec["arms"]}
    missing = [arm_id for arm_id in ARM_IDS if arm_id not in roles]
    if missing:
        raise ValueError(f"frozen spec is missing arm definitions: {missing}")

    def _make(arm_id: str, role: str, score: str, sign: int, weighting: str) -> ArmConfig:
        return ArmConfig(
            arm_id=arm_id,
            role=role,
            score=score,
            ranking_sign=sign,
            weighting=weighting,
            top_n=consts.top_n,
            per_etf_cap=consts.per_etf_cap,
            formation_sessions=consts.formation_sessions,
            skip_sessions=consts.skip_sessions,
            readiness_sessions=consts.readiness_sessions,
        )

    anchor = _make(
        ARM_ID_ANCHOR, roles[ARM_ID_ANCHOR], SCORE_MOM, +1, WEIGHT_EQUAL
    )
    neighbour = _make(
        ARM_ID_NEIGHBOUR, roles[ARM_ID_NEIGHBOUR], SCORE_MRA, +1, WEIGHT_INVERSE_VOL
    )
    # Control: the anchor with the ranking sign REVERSED, nothing else.
    control = _make(
        ARM_ID_NEGCTRL, roles[ARM_ID_NEGCTRL], SCORE_MOM, -1, WEIGHT_EQUAL
    )
    return anchor, neighbour, control


def control_differs_only_in_ranking_sign(
    anchor: ArmConfig, control: ArmConfig
) -> bool:
    """Structural identity check required by the frozen spec."""
    a, c = anchor.structural_fields(), control.structural_fields()
    if set(a) != set(c):
        return False
    differing = {key for key in a if a[key] != c[key]}
    return differing == {"arm_id", "role", "ranking_sign"} and (
        control.ranking_sign == -anchor.ranking_sign
    )


@dataclass(frozen=True)
class SymbolFeatures:
    """Frozen features for one symbol at one decision session."""

    symbol: str
    ready: bool
    mom: float | None = None
    sigma: float | None = None
    mra: float | None = None
    not_ready_reason: str | None = None


def compute_symbol_features(
    tr: Mapping[str, float],
    sessions: Sequence[str],
    index: int,
    formation_sessions: int,
    skip_sessions: int,
    symbol: str,
) -> SymbolFeatures:
    """Features for ``symbol`` at decision session ``sessions[index]``.

    ``tr`` maps ISO session date -> cumulative total-return index level for
    the symbol (injected; built upstream as raw closes x issuer split
    factors + distributions, amended FD2).  Uses strictly completed bars:

    - ``mom = P(t-skip) / P(t-formation) - 1`` (both strictly before t),
    - ``sigma`` = sample std (ddof=1) of the ``formation - skip`` daily log
      TR returns over sessions ``[t-formation, t-skip]``,
    - ``mra = mom / sigma``.
    """
    need = formation_sessions + 1  # window [t-formation, t] inclusive
    if index + 1 < need:
        return SymbolFeatures(
            symbol=symbol,
            ready=False,
            not_ready_reason="INSUFFICIENT_LOOKBACK",
        )
    window = [sessions[index - formation_sessions + k] for k in range(need)]
    levels: list[float] = []
    for day in window:
        value = tr.get(day)
        if value is None or not math.isfinite(value) or value <= 0.0:
            return SymbolFeatures(
                symbol=symbol,
                ready=False,
                not_ready_reason=f"TR_WINDOW_HOLE:{day}",
            )
        levels.append(float(value))
    # levels[0] is session t-formation; levels[formation - skip] is t-skip.
    p_skip = levels[formation_sessions - skip_sessions]
    p_formation = levels[0]
    mom = p_skip / p_formation - 1.0
    # Daily log TR returns with session labels [t-formation+1 .. t-skip]:
    # 231 observations (spec: "the same formation window, 231 daily
    # observations"), each using only bars strictly before t.
    log_returns = [
        math.log(levels[k + 1] / levels[k])
        for k in range(formation_sessions - skip_sessions)
    ]
    sigma = _sample_std(log_returns)
    mra = (mom / sigma) if sigma > 0.0 else None
    return SymbolFeatures(
        symbol=symbol, ready=True, mom=mom, sigma=sigma, mra=mra
    )


def _sample_std(values: Sequence[float]) -> float:
    """Sample standard deviation (ddof=1); 0.0 for a constant series."""
    n = len(values)
    if n < 2:
        raise ValueError("sample std needs at least two observations")
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(max(var, 0.0))


def score_of(features: SymbolFeatures, score: str) -> float | None:
    """The arm's ranking score, or None when not computable for the arm."""
    if score == SCORE_MOM:
        return features.mom
    if score == SCORE_MRA:
        return features.mra  # None when sigma <= 0: fail closed, no ranking
    raise ValueError(f"unknown score {score!r}")


def rank_select(
    features_by_symbol: Mapping[str, SymbolFeatures],
    config: ArmConfig,
) -> tuple[str, ...]:
    """Shared selection path for ALL three arms (one code path).

    Rankable = ready symbols whose score is computable (a symbol with zero
    sigma is excluded from the neighbour's mra ranking — deterministic,
    fail-closed; not expected in S0 per the spec).  Ordering: by
    ``ranking_sign * score`` descending, ties broken by ascending symbol
    (spec ties rule); the control is the SAME ranking with the sign flipped.
    """
    ranked: list[tuple[float, str]] = []
    for symbol in sorted(features_by_symbol):
        score = score_of(features_by_symbol[symbol], config.score)
        if score is None or not math.isfinite(score):
            continue
        ranked.append((config.ranking_sign * score, symbol))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return tuple(symbol for _, symbol in ranked[: config.top_n])
