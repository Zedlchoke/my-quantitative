"""Append-only hash-chained journal (journal_row@1) — PC12A impl lane.

JOURNAL_SCHEMA §1: one JSONL row per order-lifecycle event; hash-chained per
run (``prev_row_sha256``); nothing is ever edited after write; corrections
are NEW rows carrying ``corrects_row_id``. No mutation APIs exist.

Row kinds written by the dry-run pipeline (RGC-INC-1 law: the dry run
carries decision counts, fill counts and cost bills ONLY — outcome blocks
never carry PnL fields in a dry run):

- ``DECISION`` — decision-time block (ts, ids, PIT snapshot, vote, desired
  units, eligibility/risk/portfolio state).
- ``NET_ORDER`` — an executed net order with the fill block (fill price,
  spread-once cell id, U3 band id, commission) and position delta.
- ``BLOCK``    — blocked signal (outcome BLOCKED_*): decision-state
  snapshot ONLY, fill/cost fields NULL, zero cash/position effect.
- ``DEFER``    — DEFERRED_COST_GUARD with the guard block and the
  pre-commit estimate (journaled, never charged).
- ``NETTED_TO_ZERO`` — tie rows (nonzero votes, net 0; asset FLAT).
- ``SWAP``     — dated accrual rows with the Wed x3 flag.
- ``TWIN``     — ONOFF counterfactual twin (GROUPING_PROPOSAL §4.2):
  ``twin_of_order_id`` + ``would_*`` fields on the shadow always-on book.

Outcome enum (frozen): FILLED | BLOCKED_STALE | BLOCKED_FLOOR |
BLOCKED_COST_BUDGET | BLOCKED_RISK_CAP | NETTED_TO_ZERO |
DEFERRED_COST_GUARD | KILLSWITCH_FLAT | UNAVAILABLE_FILL_BAR
(A7-prelaunch F-3 remediation: the no-fill-bar fail-closed path journals
the precise outcome instead of overloading BLOCKED_STALE; zero rows of
this kind exist in the frozen full-window journal — the path never fired —
so no committed artifact changes).
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List, Optional

SCHEMA = "journal_row@1"

OUTCOME_ENUM = (
    "FILLED",
    "BLOCKED_STALE",
    "BLOCKED_FLOOR",
    "BLOCKED_COST_BUDGET",
    "BLOCKED_RISK_CAP",
    "NETTED_TO_ZERO",
    "DEFERRED_COST_GUARD",
    "KILLSWITCH_FLAT",
    "UNAVAILABLE_FILL_BAR",  # A7-prelaunch F-3 remediation (see docstring)
)

ROW_KINDS = ("HEADER", "DECISION", "NET_ORDER", "BLOCK", "DEFER",
             "NETTED_TO_ZERO", "SWAP", "TWIN")

# Fields that must be present-and-None (never 0) on blocked/deferred/tie
# rows (FILL_ACCOUNTING_SPEC §8: "Fill fields are NULL (absent), never
# zero").
NULL_FILL_FIELDS = ("ts_fill_utc", "fill_price", "spread_once_usd",
                    "slip_beyond_halfspread_usd", "commission_usd",
                    "cash_delta_usd")


def _canonical(row: Dict) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


class JournalError(RuntimeError):
    pass


class JournalWriter:
    """Append-only JSONL with a per-run sha256 chain.

    The chain: row N stores ``prev_row_sha256`` = digest of row N-1 (as
    written, minus its own ``row_sha256``) and ``row_sha256`` = digest of
    itself minus ``row_sha256``. Tampering with any row breaks every later
    link (verified by :func:`verify_chain`).
    """

    def __init__(self, path: str, run_id: str, meta: Optional[Dict] = None):
        self.path = path
        self.run_id = run_id
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            raise JournalError(f"refusing to append onto existing journal "
                               f"{path} (append-only = one run per file)")
        self._n = 0
        self._last_digest: Optional[str] = None
        self._fh = open(path, "w", encoding="utf-8")
        header = {"schema": SCHEMA, "row_kind": "HEADER", "run_id": run_id,
                  "meta": meta or {}}
        self._write_raw(header, chain=False)

    # -- writing -------------------------------------------------------------

    def _write_raw(self, row: Dict, chain: bool = True) -> Dict:
        row = dict(row)
        row["schema"] = SCHEMA
        row["run_id"] = self.run_id
        row["seq"] = self._n
        if chain:
            row["prev_row_sha256"] = self._last_digest
        body = {k: v for k, v in row.items() if k != "row_sha256"}
        digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        row["row_sha256"] = digest
        self._fh.write(_canonical(row) + "\n")
        self._fh.flush()
        self._last_digest = digest
        self._n += 1
        return row

    def write(self, row_kind: str, fields: Dict) -> Dict:
        if row_kind not in ROW_KINDS:
            raise JournalError(f"unknown row_kind {row_kind}")
        outcome = fields.get("outcome")
        if outcome is not None and outcome not in OUTCOME_ENUM:
            raise JournalError(f"outcome {outcome} not in frozen enum")
        if row_kind in ("BLOCK", "DEFER", "NETTED_TO_ZERO"):
            for f in NULL_FILL_FIELDS:
                if f in fields and fields[f] is not None:
                    raise JournalError(
                        f"{row_kind} row carries non-NULL fill field {f}")
            # A7-prelaunch F-2 remediation: absent fill fields are NULL,
            # never 0.0 (FILL_ACCOUNTING_SPEC §8) — the old setdefault(0.0)
            # wrote a fabricated zero.
            fields.setdefault("cash_delta_usd", None)
        row = {"row_kind": row_kind}
        row.update(fields)
        return self._write_raw(row)

    def write_correction(self, corrects_row_id: str, row_kind: str,
                         fields: Dict) -> Dict:
        """Corrections are NEW rows pointing at the row they correct."""
        fields = dict(fields)
        fields["corrects_row_id"] = corrects_row_id
        return self.write(row_kind, fields)

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "JournalWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @property
    def n_rows(self) -> int:
        return self._n


def read_rows(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def verify_chain(path: str) -> Dict:
    """Recompute the chain; any tamper/truncation is reported.

    Verification-lane hardening: the HEADER's self-hash is recomputed too
    (it roots the chain but its own fields -- e.g. the run meta -- were
    previously taken on faith; a tampered header went undetected).
    """
    rows = read_rows(path)
    prev: Optional[str] = None
    for i, row in enumerate(rows):
        if i == 0:
            if row.get("row_kind") != "HEADER":
                return {"ok": False, "first_bad_seq": row.get("seq"),
                        "reason": "first row is not HEADER"}
            body = {k: v for k, v in row.items() if k != "row_sha256"}
            digest = hashlib.sha256(
                _canonical(body).encode("utf-8")).hexdigest()
            if digest != row.get("row_sha256"):
                return {"ok": False, "first_bad_seq": row.get("seq"),
                        "reason": "row_sha256 mismatch (field tampered)"}
            prev = row.get("row_sha256")  # the header roots the chain
            continue
        if row.get("prev_row_sha256") != prev:
            return {"ok": False, "first_bad_seq": row.get("seq"),
                    "reason": "prev_row_sha256 mismatch"}
        body = {k: v for k, v in row.items() if k != "row_sha256"}
        digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        if digest != row.get("row_sha256"):
            return {"ok": False, "first_bad_seq": row.get("seq"),
                    "reason": "row_sha256 mismatch (field tampered)"}
        prev = row["row_sha256"]
    return {"ok": True, "n_rows": len(rows)}


# ---------------------------------------------------------------------------
# Row builders (shared by the dry-run engine and tests)
# ---------------------------------------------------------------------------


def decision_row(*, ts_decision_utc: str, fold_id, cycle_id, sleeve_id,
                 leg_id, symbol, family_id, mech_key, outcome_exposed_label,
                 cluster_id, direction_vote, desired_risk_units,
                 entry_reason_code, eligibility_state, risk_rule_state,
                 portfolio_state, feature_pit_snapshot,
                 eligibility_rule_id=None, onoff_features=None) -> Dict:
    """Decision-time block (JOURNAL_SCHEMA §1) + GROUPING_PROPOSAL §4.2
    additions (eligibility_rule_id, onoff_features digest)."""
    return {
        "ts_decision_utc": ts_decision_utc, "fold_id": fold_id,
        "cycle_id": cycle_id, "sleeve_id": sleeve_id, "leg_id": leg_id,
        "symbol": symbol, "family_id": family_id, "mech_key": mech_key,
        "outcome_exposed_label": outcome_exposed_label,
        "cluster_id": cluster_id,
        "feature_pit_snapshot": feature_pit_snapshot,
        "direction_vote": direction_vote,
        "desired_risk_units": desired_risk_units,
        "entry_reason_code": entry_reason_code,
        "eligibility_state": eligibility_state,
        "risk_rule_state": risk_rule_state,
        "portfolio_state": portfolio_state,
        "eligibility_rule_id": eligibility_rule_id,
        "onoff_features": onoff_features,
    }


def net_order_row(*, order_id, order_kind, ts_fill_utc, symbol, side,
                  delta_units, fill_price, quoted_side, mid_at_fill,
                  spread_once_usd, slip_beyond_halfspread_usd,
                  cross_cost_usd, commission_usd, cell_id, u3_band_id,
                  venue_model, units_after, contributing_legs,
                  cash_delta_usd, graded=False, gap_excess_usd=None) -> Dict:
    # A7-prelaunch F-2 remediation: NET_ORDER rows carry the §7 per-event
    # cash delta (=-delta*fill -/+ commission, sign per side) — derivable
    # from existing fields, hence leaks nothing new under RGC-INC-1.
    return {
        "order_id": order_id, "order_kind": order_kind,
        "ts_fill_utc": ts_fill_utc, "symbol": symbol, "side": side,
        "delta_units": delta_units, "fill_price": fill_price,
        "fill_side_quote": "ask" if side == "buy" else "bid",
        "quoted_side": quoted_side, "mid_at_fill": mid_at_fill,
        "spread_once_usd": spread_once_usd,
        "slip_beyond_halfspread_usd": slip_beyond_halfspread_usd,
        "cross_cost_usd": cross_cost_usd, "commission_usd": commission_usd,
        "spread_pips_charged": cell_id, "slippage_beyond_spread": u3_band_id,
        "venue_model": venue_model, "units_after": units_after,
        "contributing_legs": contributing_legs, "graded": graded,
        "gap_excess_usd": gap_excess_usd,
        "cash_delta_usd": cash_delta_usd,
    }


def blocked_row(*, outcome, blocked_reason_detail, decision_fields) -> Dict:
    """BLOCKED_*/NETTED_TO_ZERO/DEFERRED rows: snapshot ONLY, no fill block."""
    row = dict(decision_fields)
    row["outcome"] = outcome
    row["blocked_reason_detail"] = blocked_reason_detail
    return row


def twin_row(*, twin_of_order_id, would_fill_price, would_spread_once_usd,
             would_slip_usd, would_commission_usd, decision_fields) -> Dict:
    """ONOFF counterfactual twin (GROUPING_PROPOSAL §4.2): the always-on
    twin's would-* values under the identical kernel. Appendix-only row —
    never a policy row edit."""
    row = dict(decision_fields)
    row["counterfactual"] = True
    row["twin_of_order_id"] = twin_of_order_id
    row["would_fill_price"] = would_fill_price
    row["would_spread_once_usd"] = would_spread_once_usd
    row["would_slip_usd"] = would_slip_usd
    row["would_commission_usd"] = would_commission_usd
    return row


def swap_row(*, ts_utc, symbol, weekday_utc, units_abs, multiplier,
             swap_usd, wed_x3, units_after) -> Dict:
    return {"ts_utc": ts_utc, "symbol": symbol, "weekday_utc": weekday_utc,
            "units_abs": units_abs, "multiplier": multiplier,
            "swap_usd": swap_usd, "wed_x3": wed_x3,
            "units_after": units_after}
