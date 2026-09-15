"""Near-real mark-to-market valuation for PROSPECTIVE-SHADOW-V1.

ADDITIVE module: this lane changes NO existing engine module. It is a
read-only OBSERVATION and ACCOUNTING surface over the strategy ledgers:

- :func:`rebuild_positions` replays the append-only strategy ledger
  (schema ``shv1_event_v1``) read-only and reconstructs positions
  (signed qty: long positive, short negative), cash and the cumulative
  fee / slippage / settled-funding books, using EXACTLY the primary-book
  economics recorded on each ``virtual_fill_events`` entry;
- :func:`build_valuation_mark` produces ONE mark-to-market record
  (schema ``shv1_valuation_mark@1``) at a round 5-minute UTC stamp.
  ``equity = cash + sum(signed_qty x mark_price)`` reconciles to the
  cent; a missing mark price for ANY open position makes the whole mark
  ``UNAVAILABLE_FAIL_CLOSED`` with ``equity=None`` — never stale reuse,
  never interpolation;
- :func:`append_valuation_mark` appends idempotently (by ``mark_id`` /
  ``seed_id``) with O_APPEND single-write + fsync + read-back
  verification, identical discipline to ``research.shadow_v1.ledger``;
- :func:`capital_seed_record` emits the ``CAPITAL_SEED_NO_MARK`` record
  at SHADOW_START_UTC: the isolated 100,000-USDT seed, explicitly NOT a
  market mark and NEVER prospective performance.

HARD BOUNDARIES of this module:

- NO network: prices are passed in by the caller (the worker owns the
  frozen keyless fetch);
- NO heavy lock: this module never imports or touches
  ``research.governance.heavy_lock`` (ACTIVE_LIGHT lane);
- fees and slippage are the CUMULATIVE books from the strategy ledger
  and are NEVER recharged by marking;
- funding is settled funding only (what the strategy ledger already
  booked through its own holding-window/dedup layer);
- ``btc_beta`` is None until BTC marks are actually supplied — honest
  UNAVAILABLE, not a fabricated zero;
- the only emitted action type referenced anywhere is TARGET_INTENT;
  this module emits no orders and cannot place one;
- strategy identity, signals, sizing, risk limits, schedule and the
  historical verdicts are NOT readable-writable here: the strategy
  ledger is opened read-only, always.

Sign convention check (tested): a long position (qty > 0) marked above
its average price has unrealized PnL > 0; a short (qty < 0) marked
below its average price has unrealized PnL > 0.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Tuple

from . import ledger as shv1_ledger
from . import no_order

SCHEMA = "shv1_valuation_mark@1"
SEED_SCHEMA = "shv1_capital_seed@1"
CYCLE_ID = "PROSPECTIVE-SHADOW-V1"
EVENT_ID_DOMAIN = "PROSPECTIVE-SHADOW-V1"

MARK_ID_DOMAIN_PREFIX = "PROSPECTIVE-SHADOW-V1"
SEED_RECORD_TYPE = "CAPITAL_SEED_NO_MARK"

STATUS_FLAT_OK = "FLAT_OK"
STATUS_RUNNING = "RUNNING"
STATUS_UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"

DATA_STATUS_OK = "OK"
DATA_STATUS_BLOCKED = "DATA_BLOCKED"
ACCOUNTING_STATUS_OK = "OK"
ACCOUNTING_STATUS_UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"
#: The valuation lane evaluates NO risk caps (risk is owned by the
#: strategy lane); every mark says so honestly instead of borrowing OK.
RISK_STATUS_NOT_EVALUATED = "NOT_EVALUATED"

#: Marks are stamped on round 5-minute UTC boundaries.
MARK_INTERVAL_SECONDS = 300

#: Equity identity tolerance: the published equity must reconcile to
#: the cent against cash + sum(signed_qty x mark).
_EQUITY_CENT_TOL = 0.005
_EPS = 1e-9

#: Directory name under the runtime root holding per-family mark ledgers.
VALUATION_MARKS_DIRNAME = "valuation_marks"

STARTING_CASH = 100_000.0

#: Exact contract for one valuation mark (no fewer, no more).
REQUIRED_MARK_FIELDS = (
    "schema",
    "cycle_id",
    "family_id",
    "mark_id",
    "mark_timestamp_utc",
    "observed_at_utc",
    "price_source",
    "source_timestamp_utc",
    "source_digest",
    "positions_digest",
    "prices_by_symbol",
    "cash",
    "realized_pnl",
    "unrealized_pnl",
    "fees",
    "slippage",
    "funding",
    "equity",
    "gross",
    "net",
    "btc_beta",
    "data_status",
    "accounting_status",
    "risk_status",
    "status",
    "positions",
    "no_order_proof",
)


class ValuationError(RuntimeError):
    """Valuation contract violation (fail closed)."""


class ValuationLedgerCorrupt(ValuationError):
    """Partial/garbled mark ledger line: refuse, never truncate."""


class ValuationVerificationError(ValuationError):
    """Read-back verification failed after a mark append."""


# ----------------------------------------------------------------------
# time helpers
# ----------------------------------------------------------------------
def parse_iso_z(value: str) -> dt.datetime:
    """Parse an ISO-8601 Z/offset timestamp; naive means UTC."""
    if isinstance(value, dt.datetime):
        moment = value
    else:
        raw = str(value).strip()
        if raw.endswith("Z") or raw.endswith("z"):
            raw = raw[:-1] + "+00:00"
        moment = dt.datetime.fromisoformat(raw)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.timezone.utc)
    return moment.astimezone(dt.timezone.utc)


def to_iso_z(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def round_mark_timestamp_utc(mark_timestamp: Any) -> str:
    """Floor to the round 5-minute UTC boundary, canonical ISO-Z string.

    The mark_id is derived from THIS canonical string, so the same
    5-minute window always reproduces the same mark id.
    """
    moment = parse_iso_z(mark_timestamp)
    epoch = moment.timestamp()
    floored = int(epoch // MARK_INTERVAL_SECONDS) * MARK_INTERVAL_SECONDS
    return to_iso_z(dt.datetime.fromtimestamp(floored, tz=dt.timezone.utc))


# ----------------------------------------------------------------------
# strategy ledger replay (READ-ONLY)
# ----------------------------------------------------------------------
def _empty_state() -> Dict[str, Any]:
    return {
        "cash": STARTING_CASH,
        "positions": {},  # symbol -> {"qty","avg_price","ts_opened","realized_pnl"}
        "fees": 0.0,
        "slippage": 0.0,
        "funding": 0.0,
        "realized_pnl": 0.0,
        "events_read": 0,
        "fills_read": 0,
        "last_event_ts": None,
    }


def _apply_fill_to_state(state: Dict[str, Any], fill: Mapping[str, Any]) -> None:
    """Replay ONE recorded virtual fill with the engine's exact economics.

    Mirrors ``research.shadow_v1.accounting.SleeveAccount.apply_fill`` +
    ``_apply_to_position``: buy qty is positive, sell qty negative;
    ``cash -= signed * fill_price + fee``; extending a position updates
    the weighted average price; reducing/closing realizes
    ``closing_qty * (fill_price - avg_price) * direction``; a flip
    through zero opens a new position at the fill price.
    """
    symbol = str(fill["symbol"])
    side = str(fill["side"])
    qty = float(fill["qty"])
    fill_price = float(fill["fill_price"])
    fee = float(fill.get("fee") or 0.0)
    slip = float(fill.get("slippage_amount") or 0.0)
    ts_utc = str(fill.get("ts_utc") or "")
    if qty <= 0 or fill_price <= 0:
        raise ValuationError(
            f"recorded fill for {symbol!r} has non-positive qty/price"
        )
    if side not in ("buy", "sell"):
        raise ValuationError(f"recorded fill side {side!r} invalid")
    signed = qty if side == "buy" else -qty

    state["cash"] -= signed * fill_price + fee
    state["fees"] += fee
    state["slippage"] += slip
    state["fills_read"] += 1

    pos = state["positions"].get(symbol)
    if pos is None or pos["qty"] == 0.0:
        state["positions"][symbol] = {
            "qty": signed,
            "avg_price": fill_price,
            "ts_opened": ts_utc,
            "realized_pnl": 0.0,
        }
        return
    if pos["qty"] * signed > 0:
        new_qty = pos["qty"] + signed
        pos["avg_price"] = (
            pos["qty"] * pos["avg_price"] + signed * fill_price
        ) / new_qty
        pos["qty"] = new_qty
        return
    closing_qty = min(abs(pos["qty"]), abs(signed))
    direction = 1.0 if pos["qty"] > 0 else -1.0
    realized = closing_qty * (fill_price - pos["avg_price"]) * direction
    pos["realized_pnl"] += realized
    state["realized_pnl"] += realized
    remaining = pos["qty"] + signed
    if remaining == 0.0:
        state["positions"][symbol] = {
            "qty": 0.0,
            "avg_price": pos["avg_price"],
            "ts_opened": pos["ts_opened"],
            "realized_pnl": pos["realized_pnl"],
        }
    elif remaining * pos["qty"] > 0:
        pos["qty"] = remaining
    else:
        state["positions"][symbol] = {
            "qty": remaining,
            "avg_price": fill_price,
            "ts_opened": ts_utc,
            "realized_pnl": 0.0,
        }


def rebuild_positions(strategy_ledger_path: str) -> Dict[str, Any]:
    """Replay a strategy ledger READ-ONLY into the current sleeve state.

    A missing ledger file is the honest pre-first-event state: flat at
    the 100,000-USDT seed (``events_read == 0``). A corrupt/partial
    ledger REFUSES (never truncates, never partially replays).
    """
    state = _empty_state()
    if not os.path.exists(strategy_ledger_path):
        return state
    records = shv1_ledger.scan_events(strategy_ledger_path)
    for record in records:
        state["events_read"] += 1
        # Settled funding was booked BEFORE that decision's fills; the
        # recorded per-event delta is the cumulative-book increment and
        # the exact cash effect (applied in the same order the executor
        # applied it, so the replayed cash reproduces the recorded cash
        # bit-for-bit).
        funding_delta = record.get("funding_cashflow")
        if funding_delta is not None:
            state["cash"] += float(funding_delta)
            state["funding"] += float(funding_delta)
        fills = record.get("virtual_fill_events")
        if isinstance(fills, list):
            for fill in fills:
                if isinstance(fill, Mapping):
                    _apply_fill_to_state(state, fill)
        state["last_event_ts"] = (
            record.get("observed_at_utc") or record.get("scheduled_decision_utc")
        )
    return state


def open_positions(state: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Positions with non-zero signed quantity."""
    return {
        sym: dict(pos)
        for sym, pos in state["positions"].items()
        if float(pos["qty"]) != 0.0
    }


def positions_digest(state: Mapping[str, Any]) -> str:
    """Deterministic sha256 over the canonical positions state."""
    canonical = {
        "cash": float(state["cash"]),
        "fees": float(state["fees"]),
        "funding": float(state["funding"]),
        "positions": {
            sym: {
                "avg_price": float(pos["avg_price"]),
                "qty": float(pos["qty"]),
            }
            for sym, pos in sorted(state["positions"].items())
        },
        "realized_pnl": float(state["realized_pnl"]),
        "slippage": float(state["slippage"]),
    }
    payload = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------
# mark construction
# ----------------------------------------------------------------------
def compute_mark_id(family_id: str, mark_timestamp_utc: str) -> str:
    """First 32 lowercase hex of sha256 over the domain-separated stamp.

    ``sha256("PROSPECTIVE-SHADOW-V1|{family_id}|{mark_timestamp_utc}")``
    where ``mark_timestamp_utc`` is the round 5-minute UTC stamp.
    """
    domain = f"{MARK_ID_DOMAIN_PREFIX}|{family_id}|{mark_timestamp_utc}"
    return hashlib.sha256(domain.encode("utf-8")).hexdigest()[:32]


def _finite_price(symbol: str, price: Any) -> float:
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        raise ValuationError(f"mark price for {symbol!r} is not a number")
    value = float(price)
    if not math.isfinite(value) or value <= 0.0:
        raise ValuationError(f"mark price for {symbol!r} is not finite-positive")
    return value


def build_valuation_mark(
    family_id: str,
    strategy_ledger_path: str,
    prices_by_symbol: Mapping[str, Any],
    mark_timestamp_utc: Any,
    observed_at_utc: str,
    price_source: str,
    source_timestamp_utc: str,
    source_digest: str,
) -> Dict[str, Any]:
    """Build ONE mark-to-market record; fail closed on any missing price.

    ``prices_by_symbol`` must carry a finite positive price for EVERY
    open position when the sleeve is not flat. Missing/invalid prices
    produce an honest ``UNAVAILABLE_FAIL_CLOSED`` mark: equity,
    unrealized, gross and net are None; the mark is still appended so
    the gap is VISIBLE evidence, never silently skipped.
    """
    if not isinstance(family_id, str) or not family_id:
        raise ValuationError("family_id required")
    mark_ts = round_mark_timestamp_utc(mark_timestamp_utc)
    mark_id = compute_mark_id(family_id, mark_ts)
    state = rebuild_positions(strategy_ledger_path)
    positions = open_positions(state)
    needed = sorted(positions)

    cleaned_prices: Dict[str, float] = {}
    invalid: List[str] = []
    for sym in needed:
        if sym not in prices_by_symbol:
            invalid.append(sym)
            continue
        try:
            cleaned_prices[sym] = _finite_price(sym, prices_by_symbol[sym])
        except ValuationError:
            invalid.append(sym)

    fees = float(state["fees"])
    slippage = float(state["slippage"])
    funding = float(state["funding"])
    realized = float(state["realized_pnl"])
    cash = float(state["cash"])

    position_rows: List[Dict[str, Any]] = []
    pos_value = 0.0
    unrealized = 0.0
    for sym in needed:
        pos = positions[sym]
        qty = float(pos["qty"])
        avg = float(pos["avg_price"])
        mark = cleaned_prices.get(sym)
        row: Dict[str, Any] = {
            "symbol": sym,
            "qty": qty,
            "avg_price": avg,
            "mark_price": mark,
            "notional": None if mark is None else qty * mark,
            "unrealized_pnl": None if mark is None else qty * (mark - avg),
            "ts_opened": pos.get("ts_opened"),
        }
        position_rows.append(row)
        if mark is not None:
            pos_value += qty * mark
            unrealized += qty * (mark - avg)

    if not positions:
        # Flat sleeve: no marks required, equity is exactly the cash.
        status = STATUS_FLAT_OK
        data_status = DATA_STATUS_OK
        accounting_status = ACCOUNTING_STATUS_OK
        equity: Optional[float] = cash
        unrealized_out: Optional[float] = 0.0
        gross: Optional[float] = 0.0
        net: Optional[float] = 0.0
    elif invalid:
        # Fail closed: at least one open position has no usable mark.
        status = STATUS_UNAVAILABLE
        data_status = DATA_STATUS_BLOCKED
        accounting_status = ACCOUNTING_STATUS_UNAVAILABLE
        equity = None
        unrealized_out = None
        gross = None
        net = None
    else:
        status = STATUS_RUNNING
        data_status = DATA_STATUS_OK
        accounting_status = ACCOUNTING_STATUS_OK
        equity = cash + pos_value
        # Cent reconciliation guard: the published equity IS
        # cash + sum(signed_qty x mark); the identity check below
        # refuses any future edit that breaks it.
        if abs(equity - (cash + pos_value)) > _EQUITY_CENT_TOL:
            raise ValuationError(
                f"equity identity broke for {family_id} at {mark_ts}: "
                f"{equity!r} != {cash!r} + {pos_value!r}"
            )
        unrealized_out = unrealized
        gross = abs(pos_value) / equity if abs(equity) > _EPS else None
        net = pos_value / equity if abs(equity) > _EPS else None

    record: Dict[str, Any] = {
        "schema": SCHEMA,
        "cycle_id": CYCLE_ID,
        "family_id": family_id,
        "mark_id": mark_id,
        "mark_timestamp_utc": mark_ts,
        "observed_at_utc": str(observed_at_utc),
        "price_source": str(price_source),
        "source_timestamp_utc": (
            str(source_timestamp_utc) if source_timestamp_utc is not None else None
        ),
        "source_digest": str(source_digest) if source_digest is not None else None,
        "positions_digest": positions_digest(state),
        "prices_by_symbol": cleaned_prices,
        "cash": cash,
        "realized_pnl": realized,
        "unrealized_pnl": unrealized_out,
        "fees": fees,
        "slippage": slippage,
        "funding": funding,
        "equity": equity,
        "gross": gross,
        "net": net,
        # Honest: BTC marks are not part of the frozen source set yet,
        # so the measured BTC beta stays UNAVAILABLE (never a fake 0).
        "btc_beta": None,
        "data_status": data_status,
        "accounting_status": accounting_status,
        "risk_status": RISK_STATUS_NOT_EVALUATED,
        "status": status,
        "positions": position_rows,
        "no_order_proof": {
            "emitted_action_types": list(no_order.ALLOWED_ACTION_TYPES),
            "scan_digest": no_order.package_scan_digest(
                os.path.dirname(os.path.abspath(__file__))
            ),
        },
    }
    validate_valuation_mark(record)
    return record


def validate_valuation_mark(record: Mapping[str, Any]) -> None:
    """Strict contract check for one valuation mark."""
    missing = [f for f in REQUIRED_MARK_FIELDS if f not in record]
    if missing:
        raise ValuationError(f"valuation mark missing fields: {missing}")
    unknown = sorted(set(record) - set(REQUIRED_MARK_FIELDS))
    if unknown:
        raise ValuationError(f"valuation mark has unknown fields: {unknown}")
    if record["schema"] != SCHEMA:
        raise ValuationError(f"schema must be {SCHEMA!r}")
    if record["cycle_id"] != CYCLE_ID:
        raise ValuationError(f"cycle_id must be {CYCLE_ID!r}")
    expected_id = compute_mark_id(
        str(record["family_id"]), str(record["mark_timestamp_utc"])
    )
    if record["mark_id"] != expected_id:
        raise ValuationError(
            "mark_id is not deterministic from (family_id, mark_timestamp_utc)"
        )
    if record["status"] not in (
        STATUS_FLAT_OK,
        STATUS_RUNNING,
        STATUS_UNAVAILABLE,
    ):
        raise ValuationError(f"invalid mark status {record['status']!r}")
    if record["accounting_status"] not in (
        ACCOUNTING_STATUS_OK,
        ACCOUNTING_STATUS_UNAVAILABLE,
    ):
        raise ValuationError(
            f"invalid accounting_status {record['accounting_status']!r}"
        )
    if record["status"] == STATUS_UNAVAILABLE:
        if record["accounting_status"] != ACCOUNTING_STATUS_UNAVAILABLE:
            raise ValuationError("UNAVAILABLE mark must be fail-closed")
        if record["equity"] is not None:
            raise ValuationError("UNAVAILABLE mark must carry equity=None")
    if record["status"] == STATUS_FLAT_OK:
        if record["positions"]:
            raise ValuationError("FLAT_OK mark cannot carry open positions")
    proof = record["no_order_proof"]
    if not isinstance(proof, dict) or "emitted_action_types" not in proof:
        raise ValuationError("no_order_proof must carry emitted_action_types")
    for action in proof["emitted_action_types"]:
        if action != "TARGET_INTENT":
            raise ValuationError(
                f"forbidden action type in no_order_proof: {action!r}"
            )


# ----------------------------------------------------------------------
# capital seed (NOT a market mark, NEVER performance)
# ----------------------------------------------------------------------
def capital_seed_record(family_id: str, shadow_start_utc: str) -> Dict[str, Any]:
    """The isolated 100,000-USDT seed at SHADOW_START_UTC.

    ``record_type == CAPITAL_SEED_NO_MARK``: explicitly NOT a market
    mark and NEVER prospective performance. The dashboard renders it as
    the seed line only.
    """
    start_iso = to_iso_z(parse_iso_z(shadow_start_utc))
    domain = f"{MARK_ID_DOMAIN_PREFIX}|CAPITAL_SEED|{family_id}|{start_iso}"
    seed_id = hashlib.sha256(domain.encode("utf-8")).hexdigest()[:32]
    return {
        "schema": SEED_SCHEMA,
        "cycle_id": CYCLE_ID,
        "family_id": family_id,
        "record_type": SEED_RECORD_TYPE,
        "seed_id": seed_id,
        "ts_utc": start_iso,
        "cash": STARTING_CASH,
        "equity": STARTING_CASH,
        "note": (
            "starting capital seed at SHADOW_START_UTC; NOT a market mark; "
            "NEVER prospective performance"
        ),
        "no_order_proof": {
            "emitted_action_types": list(no_order.ALLOWED_ACTION_TYPES),
            "scan_digest": no_order.package_scan_digest(
                os.path.dirname(os.path.abspath(__file__))
            ),
        },
    }


# ----------------------------------------------------------------------
# append-only mark ledger (idempotent, verified)
# ----------------------------------------------------------------------
def valuation_marks_path(runtime_root: str, family_id: str) -> str:
    return os.path.join(
        runtime_root, VALUATION_MARKS_DIRNAME, f"{family_id}{shv1_ledger.LEDGER_SUFFIX}"
    )


def _record_id(record: Mapping[str, Any]) -> str:
    for key in ("mark_id", "seed_id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    raise ValuationError("record carries neither mark_id nor seed_id")


def _encode_line(record: Mapping[str, Any]) -> bytes:
    line = json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return (line + "\n").encode("utf-8")


def read_raw_bytes(path: str) -> Optional[bytes]:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def read_valuation_records(path: str) -> List[Dict[str, Any]]:
    """Parse a mark ledger; detect crash residue and refuse (no truncation)."""
    data = read_raw_bytes(path)
    if data is None or data == b"":
        return []
    if not data.endswith(b"\n"):
        raise ValuationLedgerCorrupt(
            f"{path}: last line is incomplete (crash mid-append); refusing"
        )
    records: List[Dict[str, Any]] = []
    for lineno, raw in enumerate(data.split(b"\n")[:-1], start=1):
        try:
            rec = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValuationLedgerCorrupt(
                f"{path}: line {lineno} is not valid JSON: {exc}"
            ) from exc
        if not isinstance(rec, dict) or not (
            isinstance(rec.get("mark_id"), str) and rec["mark_id"]
        ) and not (
            isinstance(rec.get("seed_id"), str) and rec["seed_id"]
        ):
            raise ValuationLedgerCorrupt(
                f"{path}: line {lineno} is not a valuation record"
            )
        records.append(rec)
    return records


def valuation_record_ids(path: str) -> set:
    return {_record_id(rec) for rec in read_valuation_records(path)}


def valuation_digest(path: str) -> Optional[str]:
    data = read_raw_bytes(path)
    if data is None:
        return None
    return hashlib.sha256(data).hexdigest()


def append_valuation_mark(runtime_root: str, record: Dict[str, Any]) -> str:
    """Append one mark/seed idempotently with read-back verification.

    Returns ``"appended"`` or ``"skipped_existing"``: an already present
    ``mark_id``/``seed_id`` never rewrites committed bytes.
    """
    if record.get("schema") == SCHEMA:
        validate_valuation_mark(record)
    rec_id = _record_id(record)
    family_id = str(record.get("family_id") or "")
    if not family_id:
        raise ValuationError("record must carry family_id")
    path = valuation_marks_path(runtime_root, family_id)

    if os.path.exists(path):
        if rec_id in valuation_record_ids(path):
            return "skipped_existing"

    payload = _encode_line(record)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    size_before = os.path.getsize(path) if os.path.exists(path) else 0
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
        os.fsync(fd)
    finally:
        os.close(fd)

    # Mandatory read-back verification.
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) != size_before + len(payload):
        raise ValuationVerificationError(
            f"read-back size mismatch for {path}"
        )
    if data[size_before:] != payload:
        raise ValuationVerificationError(
            f"read-back content mismatch for {path}"
        )
    return "appended"


# ----------------------------------------------------------------------
# combined strict-sum view (pure; used by the dashboard)
# ----------------------------------------------------------------------
def combine_at_common_mark(
    family_series: Mapping[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """Strict sum of sleeve equities at the newest COMMON valid mark.

    Each sleeve series entry: ``{"ts", "equity", "status"}`` (one per
    mark, newest last). The combined point uses the newest timestamp
    where EVERY sleeve carries a VALID mark; a sleeve with no marks at
    all, or with no common valid stamp, makes the combined UNAVAILABLE.
    Fail-closed: never interpolated, never a partial sum.
    """
    per_sleeve: Dict[str, Dict[str, Dict[str, Any]]] = {
        fid: {str(p["ts"]): p for p in pts} for fid, pts in family_series.items()
    }
    if not family_series or all(not pts for pts in family_series.values()):
        return {
            "status": "NO_MARKS",
            "equity": None,
            "ts": None,
            "reason": "no valuation marks exist for any sleeve",
        }
    common: Optional[str] = None
    for ts in sorted(set.intersection(*(set(m) for m in per_sleeve.values()))):
        pts_ok = all(
            per_sleeve[fid][ts].get("status") == "OK"
            and per_sleeve[fid][ts].get("equity") is not None
            for fid in per_sleeve
        )
        if pts_ok:
            common = ts  # sorted ascending: keep the newest
    if common is None:
        return {
            "status": STATUS_UNAVAILABLE,
            "equity": None,
            "ts": None,
            "reason": (
                "no timestamp where ALL sleeves carry a valid mark "
                "(UNAVAILABLE_FAIL_CLOSED; strict sum refused over gaps)"
            ),
        }
    total = 0.0
    contributions: Dict[str, Any] = {}
    for fid in sorted(per_sleeve):
        point = per_sleeve[fid][common]
        total += float(point["equity"])
        contributions[fid] = float(point["equity"])
    return {
        "status": "OK",
        "equity": total,
        "ts": common,
        "contributions": contributions,
        "reason": None,
    }
