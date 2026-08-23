from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import pandas as pd

from reports.funding import build_funding_audit


def _ns(value: str) -> int:
    return pd.Timestamp(value).value


class FundingAccountingTests(TestCase):
    def _write_bundle(self, root: Path, *, start_ms: int, end_ms: int) -> None:
        path = root / "SOLUSDT"
        path.mkdir(parents=True)
        payload = {
            "requested_start_ms": start_ms,
            "requested_end_ms": end_ms,
            "rows": [
                {
                    "fundingTime": int(pd.Timestamp("2026-01-01T08:00:00Z").timestamp() * 1000),
                    "fundingRate": "0.001",
                    "markPrice": "100",
                },
                {
                    "fundingTime": int(pd.Timestamp("2026-01-01T16:00:00Z").timestamp() * 1000),
                    "fundingRate": "0.001",
                    "markPrice": "100",
                },
            ],
        }
        (path / "funding.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_applies_settlements_only_while_position_is_open(self) -> None:
        positions = pd.DataFrame(
            [
                {
                    "position_id": "long",
                    "instrument_id": "SOLUSDT-PERP.BINANCE",
                    "entry": "BUY",
                    "peak_qty": "2",
                    "ts_opened": "2026-01-01T00:00:00Z",
                    "ts_closed": "2026-01-01T09:00:00Z",
                    "realized_pnl": "10 USDT",
                },
                {
                    "position_id": "short",
                    "instrument_id": "SOLUSDT-PERP.BINANCE",
                    "entry": "SELL",
                    "peak_qty": "0.5",
                    "ts_opened": "2026-01-01T07:00:00Z",
                    "ts_closed": "2026-01-01T17:00:00Z",
                    "realized_pnl": "-2 USDT",
                },
            ],
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_bundle(
                root,
                start_ms=_ns("2026-01-01T00:00:00Z") // 1_000_000,
                end_ms=_ns("2026-01-01T17:00:00Z") // 1_000_000,
            )
            audit = build_funding_audit(positions, root)

        self.assertEqual(len(audit.cashflows), 3)
        by_position = audit.cashflows.groupby("position_id")["cashflow"].sum().to_dict()
        self.assertAlmostEqual(by_position["long"], -0.2)
        self.assertAlmostEqual(by_position["short"], 0.1)
        self.assertAlmostEqual(audit.summary["funding_net"], -0.1)
        self.assertAlmostEqual(audit.summary["pnl_after_funding"], 7.9)

    def test_settlement_at_close_is_excluded(self) -> None:
        positions = pd.DataFrame(
            [
                {
                    "position_id": "closed-at-boundary",
                    "instrument_id": "SOLUSDT-PERP.BINANCE",
                    "entry": "BUY",
                    "peak_qty": "1",
                    "ts_opened": "2026-01-01T00:00:00Z",
                    "ts_closed": "2026-01-01T08:00:00Z",
                    "realized_pnl": "1 USDT",
                },
            ],
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_bundle(
                root,
                start_ms=_ns("2026-01-01T00:00:00Z") // 1_000_000,
                end_ms=_ns("2026-01-01T08:00:00Z") // 1_000_000,
            )
            audit = build_funding_audit(positions, root)

        self.assertTrue(audit.cashflows.empty)
        self.assertEqual(audit.summary["funding_net"], 0.0)

    def test_accepts_nautilus_position_id_index(self) -> None:
        positions = pd.DataFrame(
            [
                {
                    "position_id": "indexed-position",
                    "instrument_id": "SOLUSDT-PERP.BINANCE",
                    "entry": "BUY",
                    "peak_qty": "1",
                    "ts_opened": "2026-01-01T00:00:00Z",
                    "ts_closed": "2026-01-01T09:00:00Z",
                    "realized_pnl": "1 USDT",
                },
            ],
        ).set_index("position_id")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_bundle(
                root,
                start_ms=_ns("2026-01-01T00:00:00Z") // 1_000_000,
                end_ms=_ns("2026-01-01T09:00:00Z") // 1_000_000,
            )
            audit = build_funding_audit(positions, root)

        self.assertEqual(audit.adjusted_positions.iloc[0]["position_id"], "indexed-position")

    def test_fails_closed_when_bundle_does_not_cover_positions(self) -> None:
        positions = pd.DataFrame(
            [
                {
                    "position_id": "p1",
                    "instrument_id": "SOLUSDT-PERP.BINANCE",
                    "entry": "BUY",
                    "peak_qty": "1",
                    "ts_opened": "2026-01-01T00:00:00Z",
                    "ts_closed": "2026-01-02T00:00:00Z",
                    "realized_pnl": "1 USDT",
                },
            ],
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_bundle(
                root,
                start_ms=_ns("2026-01-01T01:00:00Z") // 1_000_000,
                end_ms=_ns("2026-01-01T23:00:00Z") // 1_000_000,
            )
            with self.assertRaises(ValueError):
                build_funding_audit(positions, root)

    def test_rejects_unknown_position_entry(self) -> None:
        positions = pd.DataFrame(
            [
                {
                    "position_id": "p1",
                    "instrument_id": "SOLUSDT-PERP.BINANCE",
                    "entry": "HOLD",
                    "peak_qty": "1",
                    "ts_opened": "2026-01-01T00:00:00Z",
                    "ts_closed": "2026-01-01T09:00:00Z",
                    "realized_pnl": "1 USDT",
                },
            ],
        )
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "BUY/SELL"):
                build_funding_audit(positions, Path(tmp))

    def test_empty_positions_have_complete_zero_summary(self) -> None:
        audit = build_funding_audit(pd.DataFrame(), "unused")

        self.assertEqual(audit.summary["trades"], 0)
        self.assertEqual(audit.summary["funding_net"], 0.0)
        self.assertEqual(audit.summary["pnl_after_funding"], 0.0)
        self.assertEqual(audit.summary["profit_factor_after_funding"], float("inf"))
