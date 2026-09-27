"""R2-3 sequencing + R2-2 bar-law book construction, shared by A1 / A2.

A1 (per G3 anchor + R2-3):
    direction_session = first session whose 16:00 ET close occurs STRICTLY
    after the acceptance instant (per name);
    entry  = open of the NEXT session after the direction session;
    exit   = close of session entry+H-1 (H raw sessions);
    insufficient sessions -> exit at last bar, DELISTING_EXIT.

A2 (per G3 anchor + R2-3):
    entry  = first session whose 09:30 ET open occurs STRICTLY after the
    acceptance instant; hold/exit same convention.

R2-2: any div/split ex-date inside [entry .. exit] -> event excluded.
B1 (raw-close ratio >= 9, both directions) and X1 (volume 0) make a bar
unfillable: at ENTRY the event is excluded+counted; at EXIT the exit rolls
forward to the next fillable bar (my pre-registered reading, see
ambiguities.md AMB-07), exhausting to the last bar if none remains.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .divsplits import ExDateIndex
from .panel import NamePanel, PanelStore
from .tzlaw import parse_acceptance


@dataclass
class SequencingResult:
    status: str                          # BOOKED | EXCLUDED | DROPPED
    reason: str | None = None            # exclusion/drop reason code
    direction_session: str | None = None
    direction: int | None = None         # sign(raw close - raw open): 1/-1/0
    entry_session: str | None = None
    entry_price: float | None = None
    exit_session: str | None = None
    exit_price: float | None = None
    delisting_exit: bool = False
    exit_rolled: bool = False
    ca_detail: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _hold_exit_index(entry_idx: int, hold: int, n_sessions: int) -> tuple[int, bool]:
    """(exit index, delisting_exit) under entry+H-1 with truncation to last bar."""
    exit_idx = entry_idx + hold - 1
    if exit_idx >= n_sessions:
        return n_sessions - 1, True
    return exit_idx, False


def _roll_exit_forward(panel: NamePanel, exit_idx: int) -> tuple[int, bool]:
    """Roll past unfillable exit bars; give up at panel end (keeps last bar)."""
    i = exit_idx
    while i < len(panel.dates) and not panel.fillable(panel.dates[i]):
        i += 1
    if i >= len(panel.dates):
        return len(panel.dates) - 1, False
    return i, True


def build_event_record(
    panel: NamePanel,
    exdates: ExDateIndex,
    acceptance_utc: str,
    hold: int,
    direction_rule: str,           # "a1" (close-anchored) | "a2" (open-anchored)
) -> SequencingResult:
    inst = parse_acceptance(acceptance_utc)
    epoch = int(inst.timestamp())

    # ---- direction session + direction --------------------------------
    if direction_rule == "a1":
        d_session = panel.first_session_with_close_after(epoch)
    elif direction_rule == "a2":
        # A2 anchors record no direction session (long-only, no A1-style
        # direction session); entry is open-anchored.
        d_session = None
    else:
        raise ValueError(direction_rule)

    # ---- entry session --------------------------------------------------
    if direction_rule == "a1":
        if d_session is None:
            return SequencingResult(status="DROPPED", reason="NO_POST_ACCEPTANCE_SESSION")
        entry = panel.next_session_after(d_session)
        if entry is None:
            return SequencingResult(status="DROPPED", reason="NO_ENTRY_SESSION")
        direction = _sign(panel.close[panel.index[d_session]] - panel.open[panel.index[d_session]])
    else:
        entry = panel.first_session_with_open_after(epoch)
        if entry is None:
            return SequencingResult(status="DROPPED", reason="NO_ENTRY_SESSION")
        direction = 1  # long-only book

    entry_idx = panel.index[entry]
    entry_laws = panel.bar_laws(entry)
    if entry_laws.extreme_print:
        return SequencingResult(status="EXCLUDED", reason="B1_ENTRY_EXTREME_PRINT")
    if entry_laws.zero_volume:
        return SequencingResult(status="EXCLUDED", reason="X1_ENTRY_ZERO_VOLUME")

    # ---- nominal exit ----------------------------------------------------
    exit_idx, delisting = _hold_exit_index(entry_idx, hold, len(panel.dates))

    # ---- exit fillability (B1/X1 roll-forward) ---------------------------
    notes: list[str] = []
    exit_rolled = False
    if not panel.fillable(panel.dates[exit_idx]):
        rolled_idx, rolled_ok = _roll_exit_forward(panel, exit_idx)
        if rolled_ok and rolled_idx != exit_idx:
            exit_idx = rolled_idx
            exit_rolled = True
            notes.append("EXIT_ROLLED_B1X1")
        elif not rolled_ok:
            delisting = True
            notes.append("EXIT_ROLL_EXHAUSTED_AT_LAST_BAR")

    # ---- R2-2 corporate-action exclusion on the FINAL window -------------
    ca = exdates.contamination(panel.ticker, panel.dates[entry_idx], panel.dates[exit_idx])
    if ca["contaminated"]:
        return SequencingResult(status="EXCLUDED", reason="CA_EXCLUSION",
                                entry_session=panel.dates[entry_idx],
                                exit_session=panel.dates[exit_idx],
                                delisting_exit=delisting, ca_detail=ca)

    return SequencingResult(
        status="BOOKED",
        direction_session=d_session,
        direction=direction,
        entry_session=panel.dates[entry_idx],
        entry_price=panel.open[entry_idx],
        exit_session=panel.dates[exit_idx],
        exit_price=panel.close[exit_idx],
        delisting_exit=delisting,
        exit_rolled=exit_rolled,
        ca_detail=ca,
        notes=notes,
    )


def _sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0
