"""Long/flat signal-event reducer: EVENTS AND HOLDS ONLY.

This is counting infrastructure for the plan section 11 signal-path dry-run
and the calendar-defect gates. It consumes a target-position stream (1=long,
0=flat) and emits fill events and hold-time statistics. It contains NO
returns, NO equity and NO PnL path (enforced by the hygiene test).

No-op law is structural: consecutive equal targets produce ZERO fills —
same-direction label noise can never generate a fill. There is no holding-age
condition of any kind: the only force-flattenable event is a target change.
"""

from typing import Dict, List, Sequence, Tuple

Fills = List[Tuple[str, int]]  # (kind, session_index); kind in {"ENTER","EXIT"}


def reduce_events(targets: Sequence[int]) -> Dict[str, object]:
    """Reduce a target stream to entry/exit events and hold-time stats.

    - A fill happens ONLY where target[i] != target[i-1].
    - Fold/window force-flat is expressed by the CALLER appending a 0 at the
      window end; the reducer never invents exits.
    - Unknown-label hysteresis (keep previous position) is the CALLER's job;
      the reducer sees only the resolved target stream.
    """
    if not targets:
        return {"fills": [], "entry_events": 0, "exit_events": 0,
                "no_op_opportunities": 0, "no_op_fills": None,
                "holds_sessions": [], "long_sessions": int(sum(targets))}
    fills: Fills = []
    holds: List[int] = []
    enter_i = None
    prev = int(targets[0])
    if prev == 1:
        enter_i = 0
        fills.append(("ENTER", 0))
    for i in range(1, len(targets)):
        cur = int(targets[i])
        if cur == prev:
            continue  # no-op law: same target => zero fills
        if cur == 1:
            enter_i = i
            fills.append(("ENTER", i))
        else:
            if enter_i is None:
                raise ValueError("EXIT without open ENTER (invalid target stream)")
            holds.append(i - enter_i)
            enter_i = None
            fills.append(("EXIT", i))
        prev = cur
    open_at_end = enter_i is not None
    return {
        "fills": fills,
        "entry_events": sum(1 for k, _ in fills if k == "ENTER"),
        "exit_events": sum(1 for k, _ in fills if k == "EXIT"),
        "no_op_opportunities": sum(
            1 for i in range(1, len(targets)) if int(targets[i]) == int(targets[i - 1])
        ),
        "no_op_fills": 0,  # structural: impossible by construction
        "holds_sessions": holds,
        "long_sessions": int(sum(int(t) for t in targets)),
        "still_open_at_stream_end": open_at_end,
    }


def labels_to_targets(labels: Sequence[str], mapping: Dict[str, int],
                      unknown_keeps_previous: bool = True,
                      unknown_token: str = "TRANSITION_UNKNOWN") -> List[int]:
    """Resolve a label stream to a target stream.

    unknown_keeps_previous=True is STATE hysteresis (hold the last resolved
    position through uncertainty); it is not a holding-duration condition and
    never opens or closes a position by itself.
    """
    out: List[int] = []
    last = 0
    for lab in labels:
        if lab == unknown_token and unknown_keeps_previous:
            out.append(last)
            continue
        if lab not in mapping:
            raise ValueError(f"unmapped label: {lab}")
        last = int(mapping[lab])
        out.append(last)
    return out
