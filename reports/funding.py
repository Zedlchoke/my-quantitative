"""Auditable post-trade funding accounting for Binance perpetual backtests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pandas as pd

from data.derivatives import funding_cashflow


@dataclass(frozen=True)
class FundingAudit:
    cashflows: pd.DataFrame
    adjusted_positions: pd.DataFrame
    summary: dict[str, object]


def _decimal_number(value: object) -> Decimal:
    text = str(value).strip()
    if not text:
        return Decimal("0")
    return Decimal(text.split()[0])


def _timestamp_ns(value: object) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text or text in {"0", "NaT", "None"}:
        return 0
    if text.isdigit():
        return int(text)
    return int(pd.Timestamp(text).value)


def _raw_symbol(instrument_id: object) -> str:
    value = str(instrument_id).split(".", 1)[0]
    return value.removesuffix("-PERP")


def _load_bundle(root: Path, symbol: str) -> dict:
    path = root / symbol / "funding.json"
    if not path.exists():
        raise ValueError(f"Missing funding bundle for {symbol}: {path}")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    required = {"requested_start_ms", "requested_end_ms", "rows"}
    missing = required.difference(payload)
    if missing:
        raise ValueError(f"Funding bundle {path} missing audit metadata: {sorted(missing)}")
    return payload


def _pnl_stats(values: list[Decimal], suffix: str) -> dict[str, float | int]:
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value <= 0]
    total = sum(values, Decimal("0"))
    gross_win = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))
    return {
        "trades": len(values),
        f"pnl_{suffix}": float(total),
        f"expectancy_{suffix}": float(total / len(values)) if values else 0.0,
        f"profit_factor_{suffix}": (
            float(gross_win / gross_loss) if gross_loss else float("inf")
        ),
        f"win_rate_{suffix}": len(wins) / len(values) if values else 0.0,
    }


def build_funding_audit(positions: pd.DataFrame, funding_data_path: str | Path) -> FundingAudit:
    """Apply historical funding settlements to a Nautilus positions report."""
    if positions.empty:
        empty = pd.DataFrame()
        return FundingAudit(
            cashflows=empty,
            adjusted_positions=positions.copy(),
            summary={
                "funding_data_path": str(Path(funding_data_path)),
                "funding_paid": 0.0,
                "funding_received": 0.0,
                "funding_net": 0.0,
                "positions_with_funding": 0,
                "funding_settlements": 0,
                "coverage": {},
                **_pnl_stats([], "before_funding"),
                **_pnl_stats([], "after_funding"),
            },
        )

    root = Path(funding_data_path)
    work = positions.copy()
    if "position_id" not in work.columns:
        index_name = work.index.name or "index"
        work = work.reset_index().rename(columns={index_name: "position_id"})
    if "position_id" not in work.columns:
        raise ValueError("Funding accounting requires a position_id column or index")
    required_columns = {
        "instrument_id",
        "entry",
        "peak_qty",
        "ts_opened",
        "ts_closed",
        "realized_pnl",
    }
    missing_columns = required_columns.difference(work.columns)
    if missing_columns:
        raise ValueError(
            f"Funding accounting missing position columns: {sorted(missing_columns)}",
        )
    entries = work["entry"].astype(str).str.upper()
    unsupported_entries = sorted(set(entries).difference({"BUY", "SELL"}))
    if unsupported_entries:
        raise ValueError(
            f"Funding accounting requires BUY/SELL entries, got: {unsupported_entries}",
        )
    work["_symbol"] = work["instrument_id"].map(_raw_symbol)
    work["_opened_ns"] = work["ts_opened"].map(_timestamp_ns)
    work["_closed_ns"] = work["ts_closed"].map(_timestamp_ns)
    if (work["_opened_ns"] <= 0).any() or (work["_closed_ns"] <= 0).any():
        raise ValueError("Funding accounting requires closed positions with valid timestamps")

    cashflow_rows: list[dict[str, object]] = []
    by_position: dict[object, Decimal] = {}
    counts: dict[object, int] = {}
    coverage: dict[str, dict[str, object]] = {}
    for symbol, group in work.groupby("_symbol", sort=True):
        payload = _load_bundle(root, symbol)
        requested_start_ms = int(payload["requested_start_ms"])
        requested_end_ms = int(payload["requested_end_ms"])
        position_start_ms = int(group["_opened_ns"].min()) // 1_000_000
        position_end_ms = int(group["_closed_ns"].max()) // 1_000_000
        complete = requested_start_ms <= position_start_ms and requested_end_ms >= position_end_ms
        coverage[symbol] = {
            "requested_start_ms": requested_start_ms,
            "requested_end_ms": requested_end_ms,
            "position_start_ms": position_start_ms,
            "position_end_ms": position_end_ms,
            "funding_rows": len(payload["rows"]),
            "complete": complete,
        }
        if not complete:
            raise ValueError(
                f"Funding coverage incomplete for {symbol}: "
                f"bundle={requested_start_ms}..{requested_end_ms}, "
                f"positions={position_start_ms}..{position_end_ms}",
            )

        settlements = sorted(payload["rows"], key=lambda row: int(row["fundingTime"]))
        for _, position in group.iterrows():
            side = "LONG" if str(position["entry"]).upper() == "BUY" else "SHORT"
            quantity = _decimal_number(position["peak_qty"])
            if quantity <= 0:
                raise ValueError(
                    f"Funding accounting requires positive peak_qty for {position['position_id']}",
                )
            opened_ns = int(position["_opened_ns"])
            closed_ns = int(position["_closed_ns"])
            for settlement in settlements:
                funding_time_ms = int(settlement["fundingTime"])
                funding_time_ns = funding_time_ms * 1_000_000
                if funding_time_ns < opened_ns:
                    continue
                if funding_time_ns >= closed_ns:
                    break
                rate = Decimal(str(settlement["fundingRate"]))
                mark_price = Decimal(str(settlement["markPrice"]))
                if mark_price <= 0:
                    raise ValueError(
                        f"Funding accounting requires positive markPrice for {symbol} "
                        f"at {funding_time_ms}",
                    )
                notional = quantity * mark_price
                cashflow = funding_cashflow(
                    side=side,
                    position_notional=notional,
                    funding_rate=rate,
                )
                position_id = position["position_id"]
                by_position[position_id] = by_position.get(position_id, Decimal("0")) + cashflow
                counts[position_id] = counts.get(position_id, 0) + 1
                cashflow_rows.append(
                    {
                        "position_id": position_id,
                        "symbol": symbol,
                        "funding_time_ms": funding_time_ms,
                        "funding_time": pd.Timestamp(funding_time_ms, unit="ms", tz="UTC"),
                        "side": side,
                        "quantity": float(quantity),
                        "mark_price": float(mark_price),
                        "position_notional": float(notional),
                        "funding_rate": float(rate),
                        "cashflow": float(cashflow),
                    },
                )

    cashflows = pd.DataFrame(cashflow_rows)
    adjusted = work.drop(columns=["_symbol", "_opened_ns", "_closed_ns"]).copy()
    adjusted["funding_net"] = [float(by_position.get(pid, Decimal("0"))) for pid in adjusted["position_id"]]
    adjusted["funding_settlements"] = [counts.get(pid, 0) for pid in adjusted["position_id"]]
    realized = [_decimal_number(value) for value in adjusted["realized_pnl"]]
    adjusted_values = [
        pnl + by_position.get(pid, Decimal("0"))
        for pnl, pid in zip(realized, adjusted["position_id"], strict=True)
    ]
    adjusted["realized_pnl_after_funding"] = [float(value) for value in adjusted_values]

    net = sum(by_position.values(), Decimal("0"))
    paid = abs(sum((value for value in by_position.values() if value < 0), Decimal("0")))
    received = sum((value for value in by_position.values() if value > 0), Decimal("0"))
    summary: dict[str, object] = {
        "funding_data_path": str(root),
        "funding_paid": float(paid),
        "funding_received": float(received),
        "funding_net": float(net),
        "positions_with_funding": len(by_position),
        "funding_settlements": len(cashflow_rows),
        "coverage": coverage,
        **_pnl_stats(realized, "before_funding"),
        **_pnl_stats(adjusted_values, "after_funding"),
    }
    return FundingAudit(cashflows=cashflows, adjusted_positions=adjusted, summary=summary)
