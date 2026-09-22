"""Safety layer + persistence — CODE-OWNED abstention (V2 core law).

NO DOUBLE ABSTENTION: the provider never sees an UNKNOWN option (the phase
question carries exactly the 4 schema phases; a static test proves the
built criteria). TRANSITION_UNKNOWN is produced ONLY by this module.

effective regime algorithm (safety_persistence_contract.json):
  provider ok AND phase_conf >= 0.50 AND phase_margin >= 0.20 AND hierarchy
  consistent (question_contract consistency_law, incl. prior-direction
  rules) -> phase label; else TRANSITION_UNKNOWN.

consistency law (question_contract.json, verbatim — DESIGN TRIAL #1 revision
2026-09-22, canary-informed, pre-historical, within the preregistered
2-revision budget; trial #0 evidence preserved in runtime/live/):
  TREND + UP -> UPTREND                 TREND + DOWN -> DOWNTREND
  TREND + NEUTRAL -> contradiction      RANGE + phase UPTREND/DOWNTREND -> contradiction
  RANGE lineage law (residual-direction reading, Wyckoff):
    prior DOWN  + direction DOWN or NEUTRAL -> ACCUMULATION
    prior UP    + direction UP   or NEUTRAL -> DISTRIBUTION
    prior DOWN  + direction UP                 -> contradiction
    prior UP    + direction DOWN               -> contradiction
    prior NEUTRAL/none (any direction)         -> contradiction
  phase ACCUMULATION requires prior DOWN; DISTRIBUTION requires prior UP.
Trial #0 lesson: the model reads range phases with a residual direction
(RANGE+DOWN+ACCUMULATION); demanding NEUTRAL mislabeled correct answers.

Confidence/margin thresholds are NEVER lowered to force trades
(no_forced_trades_law).

Persistence machine: IDENTICAL to the V1 frozen machine
(params 0.50/0.20/confirm 2/dwell 6/cooldown 3) applied to EFFECTIVE
labels. Pinned semantics (V1 golden table):
- UNKNOWN-candidates never switch the persisted state and never become one.
- Initial state TRANSITION_UNKNOWN, bars_in_current 0; leaving it needs
  min_dwell too.
- Candidacy: directional effective label != current, not in cooldown;
  candidate must equal the label on each of confirm_bars consecutive bars.
- Switch: streak >= confirm_bars AND bars_in_current >= min_dwell; on
  switch all other directional labels enter cooldown for `cooldown` bars.
- bars_in_current increments every bar; resets only on switch.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import DIRECTIONS, PHASES, STRUCTURES

UNKNOWN = "TRANSITION_UNKNOWN"
DIRECTIONAL = PHASES  # effective labels eligible for persistence


# ---------------------------------------------------------------------------
# hierarchy consistency
# ---------------------------------------------------------------------------


def expected_phase(structure: str, direction: str, prior_direction: str) -> str | None:
    """Expected phase from structure x direction x prior, or None on
    structural contradiction (before phase is even consulted).

    DESIGN TRIAL #1 (revised law): a RANGE inherits its lineage from the
    prior direction and may carry a RESIDUAL direction of the same sign
    (downside pressure weakening = DOWN residual inside ACCUMULATION) or
    NEUTRAL; the opposite residual contradicts the lineage."""
    if structure not in STRUCTURES or direction not in DIRECTIONS:
        return None
    if structure == "TREND":
        if direction == "UP":
            return "UPTREND"
        if direction == "DOWN":
            return "DOWNTREND"
        return None  # TREND + NEUTRAL -> contradiction
    # RANGE: lineage law
    pd = prior_direction if prior_direction in ("UP", "DOWN", "NEUTRAL") else "NEUTRAL"
    if pd == "DOWN":
        return "ACCUMULATION" if direction in ("DOWN", "NEUTRAL") else None
    if pd == "UP":
        return "DISTRIBUTION" if direction in ("UP", "NEUTRAL") else None
    return None  # prior NEUTRAL/none: lineage unknown -> contradiction


def phase_prior_consistent(phase: str, prior_direction: str) -> bool:
    """ACCUMULATION requires prior DOWN; DISTRIBUTION requires prior UP."""
    if phase == "ACCUMULATION":
        return prior_direction == "DOWN"
    if phase == "DISTRIBUTION":
        return prior_direction == "UP"
    return True


def evaluate_consistency(
    structure: str, direction: str, phase: str, prior_direction: str
) -> tuple[bool, str]:
    """Full consistency law. Returns (ok, reason). ok=True -> phase is the
    expected effective label; ok=False -> code-owned TRANSITION_UNKNOWN."""
    if structure not in STRUCTURES:
        return False, "structure_not_in_schema"
    if direction not in DIRECTIONS:
        return False, "direction_not_in_schema"
    if phase not in PHASES:
        return False, "phase_not_in_schema"
    exp = expected_phase(structure, direction, prior_direction)
    if exp is None:
        return False, "contradiction_structure_direction_prior"
    if phase != exp:
        return False, "phase_disagrees_with_structure_direction"
    if not phase_prior_consistent(phase, prior_direction):
        return False, "phase_requires_opposite_prior_direction"
    return True, "consistent"


# ---------------------------------------------------------------------------
# effective regime from a validated response
# ---------------------------------------------------------------------------


def effective_from_response(response: dict | None, params: dict) -> tuple[str, bool, str]:
    """Map a validated jrv2_question_io@1 response to (effective label,
    eligible, reason). Any failure is a code-owned UNKNOWN-candidate.

    reason: 'ok' | 'no_response' | 'status_<X>' | 'low_confidence' |
    'low_margin' | <consistency reason>.
    """
    if response is None:
        return UNKNOWN, False, "no_response"
    if response.get("status") != "OK":
        return UNKNOWN, False, f"status_{response.get('status', 'MISSING')}"
    answers = response.get("answers") or {}
    ph = answers.get("phase") or {}
    phase = ph.get("choice")
    probs = ph.get("probabilities") or {}
    conf = ph.get("confidence")
    if phase not in PHASES:
        return UNKNOWN, False, "phase_not_in_schema"
    vals = sorted((float(probs[l]) for l in PHASES if isinstance(probs.get(l), (int, float))), reverse=True)
    if len(vals) != len(PHASES):
        return UNKNOWN, False, "phase_probabilities_invalid"
    if not isinstance(conf, (int, float)) or conf != conf:
        return UNKNOWN, False, "phase_confidence_invalid"
    margin = vals[0] - vals[1]
    if float(conf) < params["min_confidence"]:
        return UNKNOWN, False, "low_confidence"
    if margin < params["min_margin"]:
        return UNKNOWN, False, "low_margin"
    st = (answers.get("structure") or {}).get("choice")
    dr = (answers.get("direction") or {}).get("choice")
    pd = _prior_direction_of(response)
    ok, reason = evaluate_consistency(st, dr, phase, pd)
    if not ok:
        return UNKNOWN, False, reason
    return phase, True, "ok"


def _prior_direction_of(response: dict) -> str:
    """The prior_direction carried by the state this response answered.

    The request state carries it; the adapter echoes it on the response
    (`prior_direction`) so the safety layer is self-contained per line.
    Falls back to NEUTRAL semantics when absent.
    """
    pd = response.get("prior_direction")
    return pd if isinstance(pd, str) else "none"


# ---------------------------------------------------------------------------
# persistence machine (identical to V1 frozen law)
# ---------------------------------------------------------------------------


@dataclass
class PersistedBar:
    bar_index: int
    raw_label: str  # effective label; UNKNOWN-candidates surface as TRANSITION_UNKNOWN
    eligible: bool
    persisted: str  # persisted state AFTER this bar
    switched: bool
    bars_in_current: int


@dataclass
class PersistenceState:
    min_confidence: float = 0.50
    min_margin: float = 0.20
    confirm_bars: int = 2
    min_dwell: int = 6
    cooldown: int = 3
    current: str = UNKNOWN
    bars_in_current: int = 0
    cand_label: str | None = None
    cand_count: int = 0
    cooldown_until: dict = field(default_factory=dict)  # label -> expiry bar
    _bar: int = 0


def step(state: PersistenceState, raw: str, eligible: bool) -> bool:
    """Advance the machine one persisted bar. Returns True if it switched.

    Cooldowns are expiry-based: a label failing at switch time (bar t) is
    barred from candidacy for exactly the next `cooldown` bars
    (t+1 .. t+cooldown) and eligible again at t+cooldown+1.
    """
    t = state._bar
    state._bar += 1

    switched = False
    candidate_ok = (
        eligible
        and raw in DIRECTIONAL
        and raw != state.current
        and state.cooldown_until.get(raw, -1) < t
    )
    if candidate_ok:
        if state.cand_label == raw:
            state.cand_count += 1
        else:
            state.cand_label = raw
            state.cand_count = 1
        if state.cand_count >= state.confirm_bars and state.bars_in_current >= state.min_dwell:
            state.current = raw
            state.bars_in_current = 0
            switched = True
            state.cand_label = None
            state.cand_count = 0
            for lab in DIRECTIONAL:
                if lab != raw:
                    state.cooldown_until[lab] = t + state.cooldown
    if not switched:
        state.bars_in_current += 1
    continuing = candidate_ok and not switched and state.cand_label == raw
    if not continuing:
        # raw == current, or an UNKNOWN-candidate, or a cooled/different
        # label: any of these breaks a confirmation streak
        state.cand_label = None
        state.cand_count = 0
    return switched


def run_persistence(raw_stream: list, params: dict) -> list[PersistedBar]:
    """Apply the machine to any per-bar effective-label stream.

    Stream items: None, {'label': str|None, 'eligible': bool}, or a
    validated response dict (has 'status' — routed through
    effective_from_response).
    """
    st = PersistenceState(
        min_confidence=params["min_confidence"],
        min_margin=params["min_margin"],
        confirm_bars=params["confirm_bars"],
        min_dwell=params["min_dwell"],
        cooldown=params["cooldown"],
    )
    out = []
    for i, item in enumerate(raw_stream):
        if item is None:
            raw, eligible = UNKNOWN, False
        elif isinstance(item, dict) and "status" in item:
            raw, eligible, _ = effective_from_response(item, params)
        else:
            lab = item.get("label")
            eligible = bool(item.get("eligible", False))
            raw = lab if (eligible and lab in DIRECTIONAL) else UNKNOWN
        switched = step(st, raw, eligible)
        out.append(
            PersistedBar(
                bar_index=i,
                raw_label=raw,
                eligible=eligible,
                persisted=st.current,
                switched=switched,
                bars_in_current=st.bars_in_current,
            )
        )
    return out


def persisted_labels(persisted: list[PersistedBar]) -> list[str]:
    return [p.persisted for p in persisted]
