"""journal_row@1 writer adapted to the DAILY exploratory clock (G9 prep).

Laws implemented mechanically (PLAN_DAILY_SUCCESSOR_DRAFT.md §6):

- append-only, hash-chained JSONL (``prev_row_sha256`` -> ``row_sha256``,
  canonical JSON, sha256); nothing is ever edited after write; the
  genesis header carries the schema ids and the governing law tags;
- EVERY order intent is journaled — trades AND blocked signals — with
  the frozen outcome enum
  ``FILLED | BLOCKED_STALE | BLOCKED_FLOOR | BLOCKED_COST_BUDGET |
    BLOCKED_RISK_CAP | NETTED_TO_ZERO | DEFERRED_COST_GUARD |
    KILLSWITCH_FLAT | UNAVAILABLE_FILL_BAR``
  (JOURNAL_SCHEMA §1 + the DAILY plan's UNAVAILABLE_FILL_BAR fail-closed
  typing). Blocked rows carry the decision-time block ONLY — fill fields
  are ABSENT, never zero (FILL_ACCOUNTING_SPEC §8);
- ``feature_pit_snapshot``: one entry per input with
  ``{input_id, consumed_bar_date, available_time_utc, value_digest,
  max_age_ok}`` and the OI-1 law enforced at write time:
  ``available_time_utc`` MUST be the NEXT BUSINESS DAY after the
  consumed D1 bar's close (weekend-skip; a holiday calendar is a
  registration-freeze item, disclosed — none is modeled at prep);
- per-fill ``cash_delta_quoteccy`` + ``cash_delta_usd`` WITH the
  conversion row (``fx_conversion`` block: quote ccy, same-bar
  rate, rate source ts, convention REALIZATION_SAME_BAR@1), plus
  per-night ``swap_financing`` rows with the Wed x3 flag;
- the RGC-INC-1 leak-law self-scan is BUILT INTO the writer and enforced
  on EVERY row in dry mode (and at this stage always): no key named like
  a performance field may appear anywhere in a row — a poisoned field
  (e.g. a PnL/equity-delta key) fails the write. Prep-stage outputs are
  identities, decision counts, cost bills and bookkeeping state only.

Determinism: rows contain NO wall-clock timestamps (sequence numbers and
event timestamps only), so identical inputs produce byte-identical
journals.

This writer is exercised on synthetic fixtures only; no real panel, no
scored computation (OI-2 blocker stands).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, IO, List, Optional

SCHEMA_ID = "journal_row@1"
SCHEMA_ADAPTER = "daily_exploratory_prep@1"
GENESIS_PREV = "0" * 64

RECORD_KIND_HEADER = "JOURNAL_HEADER"
RECORD_KIND_TRADE = "TRADE_ROW"
RECORD_KIND_BLOCKED = "BLOCKED_ROW"

OUTCOME_FILLED = "FILLED"
OUTCOME_BLOCKED_STALE = "BLOCKED_STALE"
OUTCOME_BLOCKED_FLOOR = "BLOCKED_FLOOR"
OUTCOME_BLOCKED_COST_BUDGET = "BLOCKED_COST_BUDGET"
OUTCOME_BLOCKED_RISK_CAP = "BLOCKED_RISK_CAP"
OUTCOME_NETTED_TO_ZERO = "NETTED_TO_ZERO"
OUTCOME_DEFERRED_COST_GUARD = "DEFERRED_COST_GUARD"
OUTCOME_KILLSWITCH_FLAT = "KILLSWITCH_FLAT"
OUTCOME_UNAVAILABLE_FILL_BAR = "UNAVAILABLE_FILL_BAR"

#: Frozen outcome enum (JOURNAL_SCHEMA §1 + DAILY plan §5 fail-closed law).
OUTCOMES = frozenset({
    OUTCOME_FILLED,
    OUTCOME_BLOCKED_STALE,
    OUTCOME_BLOCKED_FLOOR,
    OUTCOME_BLOCKED_COST_BUDGET,
    OUTCOME_BLOCKED_RISK_CAP,
    OUTCOME_NETTED_TO_ZERO,
    OUTCOME_DEFERRED_COST_GUARD,
    OUTCOME_KILLSWITCH_FLAT,
    OUTCOME_UNAVAILABLE_FILL_BAR,
})
BLOCKED_OUTCOMES = OUTCOMES - {OUTCOME_FILLED}

#: Fill-block keys that MUST be absent on blocked rows (spec §8).
#: ``order_kind`` is the ONE exception: a DEFERRED_COST_GUARD row carries
#: ``order_kind="DEFER"`` + the guard block + the pre-commit estimate
#: (spec §8) — execution defers, the decision block stays.
_FILL_BLOCK_KEYS = frozenset({
    "order_id", "ts_fill_utc", "fill_price",
    "fill_side_quote", "spread_pips_charged", "slippage_beyond_spread",
    "venue_model", "commission", "swap_financing",
    "cash_delta_quoteccy", "cash_delta_usd", "fx_conversion",
    "quoted_side_price", "mid_at_fill",
})

#: Required fill-block keys on FILLED rows.
_REQUIRED_FILL_KEYS = frozenset({
    "order_id", "order_kind", "ts_fill_utc", "fill_price",
    "fill_side_quote", "spread_pips_charged", "slippage_beyond_spread",
    "venue_model", "commission", "cash_delta_quoteccy",
    "cash_delta_usd", "fx_conversion",
})

#: Consistency gate for the conversion row (USD amounts; float view of
#: exact-decimal books — 1e-9 abs is far below any real inconsistency).
CASH_ROUNDTRIP_TOLERANCE = 1e-9

#: Decision-block keys required on EVERY row (trade or blocked).
_REQUIRED_DECISION_KEYS = frozenset({
    "ts_decision_utc", "fold_id", "cycle_id", "sleeve_id", "symbol",
    "family_id", "mech_key", "feature_pit_snapshot", "direction_vote",
    "desired_risk_units", "entry_reason_code", "eligibility_state",
})

_REQUIRED_PIT_ENTRY_KEYS = frozenset({
    "input_id", "consumed_bar_date", "available_time_utc",
    "value_digest", "max_age_ok",
})

# ---------------------------------------------------------------------------
# RGC-INC-1 leak law: forbidden key vocabulary
# ---------------------------------------------------------------------------

#: Substrings matched against the alnum-normalized lowercase key — catch
#: net_pnl, gross_pnl, pnl_usd, equity_delta/equity-delta/equityDelta,
#: profit_factor, sharpe_x, max_drawdown, equity_curve, returns, cagr, ...
FORBIDDEN_KEY_SUBSTRINGS = (
    "pnl", "profit", "sharpe", "drawdown", "equitydelta", "equitycurve",
    "return", "cagr", "calmar", "sortino", "winrate", "equitychange",
)

#: Exact tokens additionally banned (short forms that substring matching
#: cannot catch without false positives).
FORBIDDEN_KEY_TOKENS = frozenset({"pf", "pnl", "ret", "rets", "dd", "pl"})


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _tokenize_key(key: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", key.lower()) if t]


def scan_keys_for_leaks(obj) -> List[str]:
    """Recursive forbidden-key scan over a row's keys.

    Returns the list of offending key paths (empty = leak-clean). Lists
    are descended, dict keys are tested, values are never scanned (the
    law forbids performance FIELDS, not prose)."""
    offending: List[str] = []

    def _walk(node, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                here = f"{path}.{k}" if path else str(k)
                norm = _normalize_key(str(k))
                if any(s in norm for s in FORBIDDEN_KEY_SUBSTRINGS):
                    offending.append(here)
                elif any(t in FORBIDDEN_KEY_TOKENS for t in _tokenize_key(str(k))):
                    offending.append(here)
                _walk(v, here)
        elif isinstance(node, (list, tuple)):
            for i, v in enumerate(node):
                _walk(v, f"{path}[{i}]")

    _walk(obj, "")
    return offending


class LeakLawViolation(Exception):
    """RGC-INC-1: a forbidden (performance-named) key appeared in a row."""


class JournalValidationError(Exception):
    """Row violates the frozen journal_row@1 DAILY adapter laws."""


class JournalIntegrityError(Exception):
    """Hash-chain / append-only violation (tamper detected)."""


# ---------------------------------------------------------------------------
# OI-1 next-business-day law
# ---------------------------------------------------------------------------

def next_business_day(iso_date: str) -> str:
    """Next business day after a consumed D1 bar's session date.

    Weekend-skip ONLY: a holiday calendar is a registration-freeze item
    and none is modeled at prep (disclosed limitation; the freeze names
    one or the typed fallback law applies)."""
    d = date.fromisoformat(iso_date) + timedelta(days=1)
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d += timedelta(days=1)
    return d.isoformat()


def _check_pit_snapshot(snapshot) -> None:
    if not isinstance(snapshot, list) or not snapshot:
        raise JournalValidationError(
            "feature_pit_snapshot must be a non-empty list (one entry per input)"
        )
    for i, entry in enumerate(snapshot):
        if not isinstance(entry, dict):
            raise JournalValidationError(f"pit entry {i} must be an object")
        missing = _REQUIRED_PIT_ENTRY_KEYS - set(entry)
        if missing:
            raise JournalValidationError(
                f"pit entry {i} missing {sorted(missing)}"
            )
        consumed = entry["consumed_bar_date"]
        available = str(entry["available_time_utc"])
        expected_date = next_business_day(consumed)
        if not available.startswith(expected_date):
            raise JournalValidationError(
                f"OI-1 law violated for input {entry['input_id']!r}: "
                f"available_time_utc {available!r} must start with next "
                f"business day {expected_date!r} after consumed bar "
                f"{consumed!r}"
            )


# ---------------------------------------------------------------------------
# Canonical serialization + chain
# ---------------------------------------------------------------------------

def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def row_digest(row: Dict[str, object]) -> str:
    payload = {k: v for k, v in row.items() if k != "row_sha256"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_fill_consistency(row: Dict[str, object]) -> None:
    fx = row.get("fx_conversion")
    if not isinstance(fx, dict):
        raise JournalValidationError("fx_conversion must be an object")
    for k in ("quote_ccy", "rate_to_usd", "rate_source_ts", "convention"):
        if k not in fx:
            raise JournalValidationError(f"fx_conversion missing {k!r}")
    try:
        quote_delta = float(row["cash_delta_quoteccy"])
        usd_delta = float(row["cash_delta_usd"])
        rate = float(fx["rate_to_usd"])
    except (TypeError, ValueError) as exc:
        raise JournalValidationError(f"cash delta / rate not numeric: {exc}")
    if abs(quote_delta * rate - usd_delta) > CASH_ROUNDTRIP_TOLERANCE:
        raise JournalValidationError(
            "conversion row inconsistent: |cash_delta_quoteccy * rate "
            f"- cash_delta_usd| = {abs(quote_delta * rate - usd_delta)!r} "
            f"> {CASH_ROUNDTRIP_TOLERANCE}"
        )
    swaps = row.get("swap_financing")
    if swaps is not None:
        if not isinstance(swaps, list):
            raise JournalValidationError("swap_financing must be a list")
        for i, s in enumerate(swaps):
            if not isinstance(s, dict):
                raise JournalValidationError(f"swap row {i} must be an object")
            for k in ("accrual_ts", "multiplier", "wed_x3", "quote_amount",
                      "rate_to_usd", "usd_amount"):
                if k not in s:
                    raise JournalValidationError(
                        f"swap row {i} missing {k!r}"
                    )
            if bool(s["wed_x3"]) != (int(s["multiplier"]) == 3):
                raise JournalValidationError(
                    f"swap row {i}: wed_x3 flag inconsistent with multiplier"
                )


def _validate_row(row: Dict[str, object]) -> None:
    if not isinstance(row, dict):
        raise JournalValidationError("row must be a dict")
    # RGC-INC-1 leak law — ALWAYS enforced (dry-mode writer).
    leaks = scan_keys_for_leaks(row)
    if leaks:
        raise LeakLawViolation(
            "RGC-INC-1 violation: forbidden performance-named key(s) "
            f"{leaks} in row {row.get('row_id', '<unwritten>')!r}"
        )
    outcome = row.get("outcome")
    if outcome not in OUTCOMES:
        raise JournalValidationError(f"unknown outcome {outcome!r}")
    missing = _REQUIRED_DECISION_KEYS - set(row)
    if missing:
        raise JournalValidationError(f"row missing decision keys {sorted(missing)}")
    _check_pit_snapshot(row["feature_pit_snapshot"])
    if outcome == OUTCOME_FILLED:
        if row.get("record_kind") != RECORD_KIND_TRADE:
            raise JournalValidationError("FILLED rows must be TRADE_ROW")
        missing_fill = _REQUIRED_FILL_KEYS - set(row)
        if missing_fill:
            raise JournalValidationError(
                f"FILLED row missing fill keys {sorted(missing_fill)}"
            )
        _validate_fill_consistency(row)
    else:
        if row.get("record_kind") != RECORD_KIND_BLOCKED:
            raise JournalValidationError("blocked rows must be BLOCKED_ROW")
        present = _FILL_BLOCK_KEYS & set(row)
        if present:
            raise JournalValidationError(
                f"blocked row carries fill keys {sorted(present)} — fill "
                "fields must be ABSENT on blocked outcomes, never zero"
            )
        if "order_kind" in row and not (
            outcome == OUTCOME_DEFERRED_COST_GUARD
            and row["order_kind"] == "DEFER"
        ):
            raise JournalValidationError(
                "order_kind on a blocked row is lawful only as the DEFER "
                "block of a DEFERRED_COST_GUARD row (spec §8)"
            )
        if "blocked_reason_detail" not in row:
            raise JournalValidationError(
                "blocked row missing blocked_reason_detail"
            )


class DailyJournalWriter:
    """Append-only hash-chained journal for the DAILY exploratory prep.

    Opening an existing file CONTINUES its chain (append-only law);
    opening a new path writes the chained genesis header first. Every
    write validates the full row (leak law, outcome enum, blocked-row
    purity, PIT next-business-day law, conversion round-trip) BEFORE the
    line is appended.
    """

    def __init__(self, path: Path | str, *, cycle_id: str, fold_id: str,
                 run_label: str, dry_mode: bool = True):
        self.path = Path(path)
        self.cycle_id = cycle_id
        self.fold_id = fold_id
        self.run_label = run_label
        self.dry_mode = dry_mode
        self._seq = -1
        self._prev = GENESIS_PREV
        self._fh: Optional[IO[str]] = None
        if self.path.exists() and self.path.stat().st_size > 0:
            rows = self._read_all()
            self._seq = len(rows) - 1
            self._prev = rows[-1]["row_sha256"]  # type: ignore[index]
        else:
            self._fh = self.path.open("a", encoding="utf-8")
            self._write_raw({
                "record_kind": RECORD_KIND_HEADER,
                "schema": SCHEMA_ID,
                "schema_adapter": SCHEMA_ADAPTER,
                "cycle_id": cycle_id,
                "fold_id": fold_id,
                "run_label": run_label,
                "dry_mode": dry_mode,
                "laws": [
                    "APPEND_ONLY_HASH_CHAIN",
                    "RGC-INC-1_NO_PERF_FIELDS",
                    "OI-1_NEXT_BUSINESS_DAY",
                    "UNAVAILABLE_NE_0_FAIL_CLOSED",
                ],
            })

    # -- internals -----------------------------------------------------------

    def _read_all(self) -> List[Dict[str, object]]:
        if self._fh is not None:
            self._fh.flush()
        rows: List[Dict[str, object]] = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def _write_raw(self, row_without_chain: Dict[str, object]) -> str:
        if self._fh is None:
            self._fh = self.path.open("a", encoding="utf-8")
        self._seq += 1
        row = dict(row_without_chain)
        row["row_id"] = f"j{self._seq:06d}"
        row["prev_row_sha256"] = self._prev
        digest = row_digest(row)
        row["row_sha256"] = digest
        self._fh.write(canonical_json(row) + "\n")
        self._fh.flush()
        self._prev = digest
        return row["row_id"]

    # -- public API ----------------------------------------------------------

    def write_row(self, row: Dict[str, object]) -> str:
        """Validate then append one journal row; returns its row_id."""
        _validate_row(row)
        return self._write_raw(row)

    def write_rows(self, rows: List[Dict[str, object]]) -> List[str]:
        return [self.write_row(r) for r in rows]

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "DailyJournalWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- verification --------------------------------------------------------

    @staticmethod
    def verify_chain(path: Path | str) -> Dict[str, object]:
        """Tamper detection: recompute every row digest and every chain
        link. Raises JournalIntegrityError on ANY mismatch (content edit,
        deletion, reordering, truncation)."""
        p = Path(path)
        if not p.exists() or p.stat().st_size == 0:
            raise JournalIntegrityError(f"journal {p} missing or empty")
        prev = GENESIS_PREV
        n = 0
        with p.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise JournalIntegrityError(
                        f"line {lineno}: not JSON ({exc})"
                    ) from exc
                digest = row.pop("row_sha256", None)
                if digest is None:
                    raise JournalIntegrityError(
                        f"line {lineno}: row_sha256 missing"
                    )
                recomputed = row_digest(row)
                if recomputed != digest:
                    raise JournalIntegrityError(
                        f"line {lineno} ({row.get('row_id')}): digest "
                        f"mismatch — content tampered "
                        f"(stored {digest[:12]}..., recomputed "
                        f"{recomputed[:12]}...)"
                    )
                if row.get("prev_row_sha256") != prev:
                    raise JournalIntegrityError(
                        f"line {lineno} ({row.get('row_id')}): chain link "
                        "broken — row deleted/reordered/inserted"
                    )
                prev = digest
                n += 1
        return {"path": str(p), "rows": n, "ok": True}
