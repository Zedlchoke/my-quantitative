"""REPLAY_NOT_PROSPECTIVE rehearsal for the E-phase worker.

INTERNAL PAPER ONLY: keyless public network reads (Binance fapi public
endpoints); no keys, no accounts, no orders.

What this script does (dispatch packet, phase E rehearsal):
- builds the SAME three production ForwardExecutors as the worker, but
  in the explicit ``REPLAY_NOT_PROSPECTIVE`` namespace (start_guard's
  opt-in replay label; never a default) under its own runtime root
  INSIDE this control directory
  (e/replay_rehearsal/runtime/) — physically separated from the
  PROSPECTIVE ledger root by start_guard;
- weekly families (ILLIQ, PREMFADE) replay their MOST RECENT Monday
  00:00:00Z decision; CARRY replays YESTERDAY 00:00:00Z;
- runs each executor's real ``run_due`` against the REAL
  KeylessBinanceFuturesClient at (decision + 16 minutes) with
  from_utc = decision, so EXACTLY that one decision is due AND its
  first post-decision fill bar is complete (decision + 15m, +60s
  margin);
- writes per-family evidence into
  e/replay_rehearsal/rehearsal_evidence.json: {decision_utc,
  records_written, event_ids, data_status, accounting_status,
  risk_status, ledger_sha256, ledger_bytes} + an overall verdict +
  fetched_at; a LOUD UNAVAILABLE_FAIL_CLOSED block is recorded per
  family when the network/data fails, and the rehearsal verdict is
  then BLOCKED (reported honestly, never faked);
- labels EVERY ledger file and the evidence with
  ``REPLAY_NOT_PROSPECTIVE``.

NO shadow-start is needed (the forward-only bound is not applied in
the replay namespace by design; start_guard.assert_forward is a no-op
there and the replay ledger root is physically separate).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKTREE_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
for path in (HERE, WORKTREE_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from research.shadow_v1 import events, ledger, start_guard  # noqa: E402
from research.shadow_v1.data_feed import KeylessBinanceFuturesClient  # noqa: E402

import shadow_worker  # noqa: E402  (same directory)

LABEL = start_guard.NAMESPACE_REPLAY
REPLAY_RUNTIME_ROOT = os.path.join(HERE, "replay_rehearsal", "runtime")
EVIDENCE_PATH = os.path.join(HERE, "replay_rehearsal", "rehearsal_evidence.json")

FILL_BAR_MARGIN = dt.timedelta(minutes=16)  # 15m fill bar + 60s margin


def _iso(moment: dt.datetime) -> str:
    return start_guard.to_iso_z(moment)


def most_recent_monday_0000z(now: dt.datetime) -> dt.datetime:
    day = now.astimezone(dt.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return day - dt.timedelta(days=day.weekday())


def yesterday_0000z(now: dt.datetime) -> dt.datetime:
    day = now.astimezone(dt.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return day - dt.timedelta(days=1)


def _ledger_digest(path: str):
    raw = ledger.read_raw_bytes(path)
    if raw is None:
        return None, 0
    return hashlib.sha256(raw).hexdigest(), len(raw)


def _label_ledger_file(path: str) -> str:
    label_path = f"{path}.{LABEL}.label"
    with open(label_path, "w", encoding="utf-8") as handle:
        handle.write(
            f"{LABEL}\n"
            "REPLAY ONLY — these bytes are NOT prospective evidence.\n"
            f"ledger_sha256: {(_ledger_digest(path)[0] or 'EMPTY')}\n"
        )
    return label_path


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    fetched_at = _iso(now)

    # Defense in depth (C2): the replay runtime root must be disjoint
    # from any PROSPECTIVE runtime root.
    start_guard.assert_roots_disjoint(
        os.path.join(WORKTREE_ROOT, "results", "prospective_shadow_v1"),
        REPLAY_RUNTIME_ROOT,
    )

    decisions = {
        shadow_worker.FAMILY_ILLIQ: most_recent_monday_0000z(now),
        shadow_worker.FAMILY_PREMFADE: most_recent_monday_0000z(now),
        shadow_worker.FAMILY_CARRY: yesterday_0000z(now),
    }

    executors = shadow_worker.build_executors(
        REPLAY_RUNTIME_ROOT,
        None,  # NO shadow-start needed: explicit REPLAY_NOT_PROSPECTIVE
        feed=KeylessBinanceFuturesClient(),
        namespace=LABEL,
    )

    families_evidence = {}
    overall_ok = True
    findings_present = False
    for family_id in shadow_worker.FAMILY_ORDER:  # FIXED order
        executor = executors[family_id]
        assert executor.namespace == LABEL
        decision = decisions[family_id]
        decision_iso = _iso(decision)
        run_now_iso = _iso(decision + FILL_BAR_MARGIN)
        entry = {
            "label": LABEL,
            "decision_utc": decision_iso,
            "run_now_utc": run_now_iso,
            "records_written": 0,
            "event_ids": [],
            "data_status": None,
            "accounting_status": None,
            "risk_status": None,
            "ledger_path": executor.ledger_file,
            "ledger_sha256": None,
            "ledger_bytes": 0,
            "config_digest": executor.config_digest,
            "cost_regime_digest": executor.cost_regime_digest,
            "unavailable_fail_closed": None,
            "verdict": None,
        }
        try:
            result = executor.run_due(run_now_iso, from_utc=decision_iso)
            records = ledger.scan_events(executor.ledger_file)
            entry["records_written"] = len(records)
            entry["event_ids"] = [rec["event_id"] for rec in records]
            if records:
                record = records[-1]
                entry["data_status"] = record.get("data_status")
                entry["accounting_status"] = record.get("accounting_status")
                entry["risk_status"] = record.get("risk_status")
            digest, size = _ledger_digest(executor.ledger_file)
            entry["ledger_sha256"] = digest
            entry["ledger_bytes"] = size
            entry["ledger_label_file"] = _label_ledger_file(executor.ledger_file)

            if entry["records_written"] != 1:
                entry["verdict"] = "UNAVAILABLE_FAIL_CLOSED"
                entry["unavailable_fail_closed"] = {
                    "reason": (
                        f"expected exactly 1 replay record, got "
                        f"{entry['records_written']}; run_due result: "
                        f"executed={result.get('executed')}, "
                        f"data_blocked={result.get('data_blocked')}, "
                        f"pending_fill_bar={result.get('pending_fill_bar')}"
                    )
                }
            elif entry["data_status"] != events.DATA_STATUS_OK:
                entry["verdict"] = "UNAVAILABLE_FAIL_CLOSED"
                entry["unavailable_fail_closed"] = {
                    "reason": (
                        "network/data unavailable: the replay decision "
                        f"recorded data_status={entry['data_status']}"
                    )
                }
            elif (
                entry["accounting_status"] != events.ACCOUNTING_STATUS_OK
                or entry["risk_status"] != events.RISK_STATUS_OK
            ):
                # The decision EXECUTED against real data and is recorded
                # honestly, but a frozen engine status is fail-closed
                # (e.g. the no-leverage guard refusing a gross-1.0 book's
                # tail short) — a finding, never silently passed.
                entry["verdict"] = "EXECUTED_WITH_FAIL_CLOSED_STATUS"
            else:
                entry["verdict"] = "EXECUTED_OK"
            if entry["verdict"] == "UNAVAILABLE_FAIL_CLOSED":
                overall_ok = False
            if entry["verdict"] == "EXECUTED_WITH_FAIL_CLOSED_STATUS":
                findings_present = True
        except Exception as exc:  # noqa: BLE001 - loud honest evidence
            overall_ok = False
            entry["verdict"] = "UNAVAILABLE_FAIL_CLOSED"
            entry["unavailable_fail_closed"] = {
                "reason": f"{type(exc).__name__}: {exc}"
            }
        families_evidence[family_id] = entry
        print(
            f"[{LABEL}] {family_id}: decision={decision_iso} "
            f"verdict={entry['verdict']} records={entry['records_written']} "
            f"data={entry['data_status']} risk={entry['risk_status']} "
            f"accounting={entry['accounting_status']}"
        )
        if entry["unavailable_fail_closed"]:
            print(
                f"!! {family_id} UNAVAILABLE_FAIL_CLOSED: "
                f"{entry['unavailable_fail_closed']['reason']}",
                file=sys.stderr,
            )

    evidence = {
        "schema": "shv1_replay_rehearsal_evidence@1",
        "label": LABEL,
        "replay_label_rule": (
            "REPLAY_NOT_PROSPECTIVE - replay of historical windows is "
            "visibly non-prospective; these ledger bytes are NOT "
            "prospective evidence (identity manifest replay_label_rule)."
        ),
        "cycle_id": events.CYCLE_ID,
        "fetched_at": fetched_at,
        "runtime_root": REPLAY_RUNTIME_ROOT,
        "prospective_root_checked_disjoint": os.path.join(
            WORKTREE_ROOT, "results", "prospective_shadow_v1"
        ),
        "code_freeze_sha": shadow_worker.CODE_FREEZE_SHA,
        "tick_mappings": {
            family_id: {
                "per_symbol": executors[family_id].tick_size_map,
                "tick_size_default": executors[family_id].tick_size_default,
            }
            for family_id in shadow_worker.FAMILY_ORDER
        },
        "families": families_evidence,
        "verdict": (
            "PASS" if overall_ok and not findings_present
            else ("BLOCKED" if not overall_ok else "PASS_WITH_FINDINGS")
        ),
        "verdict_legend": (
            "PASS: every family executed its replay decision with "
            "data/risk/accounting all OK. PASS_WITH_FINDINGS: every family "
            "executed, but at least one carries a frozen fail-closed engine "
            "status (recorded honestly; e.g. the no-leverage guard refusing "
            "a gross-1.0 book's tail short). BLOCKED: at least one family "
            "could not execute (network/data UNAVAILABLE_FAIL_CLOSED)."
        ),
    }
    os.makedirs(os.path.dirname(EVIDENCE_PATH), exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"[{LABEL}] evidence written: {EVIDENCE_PATH}")
    print(f"[{LABEL}] REHEARSAL VERDICT: {evidence['verdict']}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
