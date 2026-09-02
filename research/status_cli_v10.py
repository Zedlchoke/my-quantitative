"""V10 read-only worker status CLI (sprint V9H H01/H02 companion).

Prints one row per worker record found in a controller state dir:

    TRIAL  PHASE  STATE  PID  HB_AGE_S  LOG_AGE_S  EXIT  NOTE

* Reads ONLY the state-dir JSON records (plus optional exact-pid
  ``ps -p PID -o lstart=`` identity verification behind --check-identity).
* A heartbeat older than STALE_HEARTBEAT_THRESHOLD_S (45 s) on a
  non-terminal record is shown as ``WARNING: stale — may be alive``.
  Staleness NEVER claims death and never mutates anything.
* ``--json`` emits the same rows as a JSON list for tooling.

This CLI is strictly read-only: it writes nothing anywhere.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from research.runtime_controller_v10 import (
    ACTIVE_STATE,
    STALE_HEARTBEAT_THRESHOLD_S,
    WorkerController,
    ps_identity,
)

_COLUMNS = ("TRIAL", "PHASE", "STATE", "PID", "HB_AGE_S", "LOG_AGE_S", "EXIT", "NOTE")
_WIDTHS = (24, 9, 22, 7, 9, 9, 10, 40)
_STALE_NOTE = "WARNING: stale — may be alive"


def _fmt_age(age_s: Optional[float]) -> str:
    if age_s is None:
        return "-"
    return f"{age_s:.0f}s"


def _exit_info(record: Dict[str, Any]) -> str:
    code = record.get("exit_code")
    sig = record.get("exit_signal")
    if code is not None:
        return f"code={code}"
    if sig is not None:
        return f"sig={sig}"
    return "-"


def collect_rows(
    state_dir: Path,
    *,
    stale_threshold_s: float = STALE_HEARTBEAT_THRESHOLD_S,
    check_identity: bool = False,
) -> List[Dict[str, Any]]:
    """Build status rows purely from records; no process probing by default."""
    controller = WorkerController(state_dir)
    rows: List[Dict[str, Any]] = []
    for record in controller.load_records():
        trial_id = str(record.get("trial_id"))
        terminal = WorkerController.is_terminal(record)
        hb_age = controller.heartbeat_age_s(trial_id, record=record)
        log_age = controller.last_log_age_s(record)
        note_parts: List[str] = []
        if not terminal and hb_age is not None and hb_age > stale_threshold_s:
            note_parts.append(_STALE_NOTE)
        identity_state = None
        if check_identity and not terminal:
            live = ps_identity(int(record.get("pid", -1)))
            if live is None:
                # Not visible to an exact-pid probe. This is NOT proof of
                # death; report conservatively.
                identity_state = "invisible-to-exact-pid-probe (not proof of death)"
            elif live[0] == record.get("posix_start_identity") and live[1] == int(
                record.get("pgid", -1)
            ):
                identity_state = "identity-ok"
            else:
                identity_state = "IDENTITY-MISMATCH"
            note_parts.append(identity_state)
        rows.append(
            {
                "trial_id": trial_id,
                "phase": record.get("phase"),
                "state": record.get("terminal_state") or ACTIVE_STATE,
                "pid": record.get("pid"),
                "pgid": record.get("pgid"),
                "heartbeat_age_s": round(hb_age, 3) if hb_age is not None else None,
                "last_log_age_s": round(log_age, 3) if log_age is not None else None,
                "stale_heartbeat": bool(note_parts) and any(_STALE_NOTE == p for p in note_parts),
                "exit": _exit_info(record),
                "terminal": terminal,
                "note": "; ".join(note_parts),
            }
        )
    return rows


def format_table(rows: List[Dict[str, Any]]) -> str:
    lines = [" ".join(col.ljust(w) for col, w in zip(_COLUMNS, _WIDTHS)).rstrip()]
    lines.append(" ".join("-" * w for w in _WIDTHS))
    for row in rows:
        cells = (
            str(row["trial_id"]),
            str(row["phase"]),
            str(row["state"]),
            str(row["pid"]),
            _fmt_age(row["heartbeat_age_s"]),
            _fmt_age(row["last_log_age_s"]),
            str(row["exit"]),
            str(row["note"]),
        )
        lines.append(" ".join(c.ljust(w) for c, w in zip(cells, _WIDTHS)).rstrip())
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="research.status_cli_v10",
        description="Read-only V10 worker status table from a controller state dir.",
    )
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--json", action="store_true", help="emit rows as JSON instead of a table")
    parser.add_argument(
        "--check-identity",
        action="store_true",
        help="additionally verify live identity of RUNNING workers via exact-pid `ps -o lstart=`",
    )
    parser.add_argument("--stale-threshold-s", type=float, default=STALE_HEARTBEAT_THRESHOLD_S)
    args = parser.parse_args(argv)

    rows = collect_rows(
        Path(args.state_dir),
        stale_threshold_s=args.stale_threshold_s,
        check_identity=args.check_identity,
    )
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(format_table(rows))
        print(f"\n{len(rows)} record(s); stale threshold {args.stale_threshold_s:.0f}s; "
              f"read-only view — stale heartbeats are NOT proof of death.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
