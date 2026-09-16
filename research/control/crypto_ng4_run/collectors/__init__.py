"""CRYPTO-NG4 prospective WebSocket collectors (lane A8, cycle CRYPTO-NG4).

Authority: plans/PLAN_crypto_ng4.md §7 and the frozen A3 contract
research/control/ng6_ng7_ng4_dossiers_2026-09/cng4-a3-prospective-contract-dossier.json
(schema cng4_a3_prospective_contract@1).  Wire formats are the MEASURED
FDF-V1 census shapes (aiohttp client, one JSON object per raw line:
{recv_utc, channel, seq, payload}).

Collectors are LIGHT long-running daemons (plan §7 hygiene): never the
machine-wide heavy lock; heartbeats carrying bytes-written + payload-shape
counts; inode-check on append handles; payload-shape mismatch fails LOUD.
Data collectors only — no trading endpoints, no auth, no orders.
"""

from __future__ import annotations

CONTRACT_SCHEMA = "cng4_a3_prospective_contract@1"
CYCLE_ID = "CRYPTO-NG4"

# Frozen instrument identity (contract freeze field 1).
VENUES = ("coinbase", "kraken", "deribit")

INSTRUMENTS = {
    "coinbase": ["BTC-USD", "ETH-USD"],
    "kraken": ["PF_XBTUSD", "PF_ETHUSD"],
    "deribit": ["BTC-PERPETUAL", "ETH-PERPETUAL"],
}

ENDPOINTS = {
    "coinbase": "wss://advanced-trade-ws.coinbase.com",
    "kraken": "wss://futures.kraken.com/ws/v1",
    "deribit": "wss://www.deribit.com/ws/api/v2",
}
