"""Regime persistence state machine, verbatim from persistence_contract.json.

Params (frozen): min_confidence 0.50, min_margin 0.20, confirm_bars 2,
min_dwell 6, cooldown 3.

Pinned semantics (hand-computed golden table in tests):
- raw = top1 label when status==OK and confidence>=min_confidence and
  p1-p2>=min_margin; otherwise an UNKNOWN-candidate (errors, LOCAL_INVALID,
  low confidence/margin, schema violations all land here).
- UNKNOWN-candidates NEVER switch the persisted state and never become one.
- Initial state = TRANSITION_UNKNOWN, bars_in_current=0. A switch therefore
  requires >=min_dwell bars in the current state first (also true for leaving
  the initial UNKNOWN).
- Candidacy: a directional raw label != current, not in cooldown. The label
  must equal raw on each of `confirm_bars` consecutive persisted bars
  (candidate must equal raw on each confirm bar, else reset).
- Switch condition: streak >= confirm_bars AND bars_in_current >= min_dwell.
- On switch: bars_in_current=0; every directional label except the newly
  persisted one counts as a failed candidate and is barred from candidacy
  for the next `cooldown` persisted bars ("failed candidates enter cooldown").
- bars_in_current increments on every bar the state stays in force (including
  UNKNOWN-candidate bars); resets only on switch.
- Output per bar = persisted state AFTER processing that bar.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import LABELS

UNKNOWN = "TRANSITION_UNKNOWN"
DIRECTIONAL = tuple(l for l in LABELS if l != UNKNOWN)


@dataclass
class PersistedBar:
    bar_index: int
    raw_label: str  # UNKNOWN-candidates surface as TRANSITION_UNKNOWN
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


def raw_from_response(response: dict | None, params: dict) -> tuple[str, bool]:
    """Map a decision-io response line to (raw label, eligible flag).

    (UNKNOWN, False) for any error/missing/ineligible case; (top1, True) only
    when status==OK, regime is a supported directional label, confidence >=
    min_confidence, probabilities valid (all 5, non-negative, sum 1±0.01) and
    p1-p2 >= min_margin.
    """
    if response is None:
        return UNKNOWN, False
    if response.get("status") != "OK":
        return UNKNOWN, False
    regime = response.get("regime")
    probs = response.get("probabilities")
    if regime not in DIRECTIONAL or not isinstance(probs, dict):
        return UNKNOWN, False
    vals = []
    for lab in LABELS:
        v = probs.get(lab)
        if not isinstance(v, (int, float)) or v != v or v < 0:
            return UNKNOWN, False
        vals.append(float(v))
    if abs(sum(vals) - 1.0) > 0.01:
        return UNKNOWN, False
    conf = response.get("confidence")
    if not isinstance(conf, (int, float)) or conf != conf:
        return UNKNOWN, False
    srt = sorted(vals, reverse=True)
    if float(conf) < params["min_confidence"] or (srt[0] - srt[1]) < params["min_margin"]:
        return UNKNOWN, False
    return regime, True


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
        # label: any of these breaks a confirmation streak ("candidate must
        # equal raw on each of the confirm bars, else reset").
        state.cand_label = None
        state.cand_count = 0
    return switched


def run_persistence(raw_stream: list, params: dict) -> list[PersistedBar]:
    """Apply the machine to any per-bar raw stream.

    Stream items: None, a decision-io response dict (has 'status'), or
    {'label': str|None, 'eligible': bool}.
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
            raw, eligible = raw_from_response(item, params)
        else:
            lab = item.get("label")
            eligible = bool(item.get("eligible", False))
            raw = lab if (eligible and lab in LABELS) else UNKNOWN
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
