"""LIVE-DATA-GATEWAY-V1 — local single-owner market-data gateway.

Platform cycle (plans/PLAN_live_data_gateway_v1.md). Keyless public
Binance fapi data ONLY: one WebSocket mark-price stream + one coalesced,
cached, circuit-broken REST surface, fanned out to local consumers on
127.0.0.1. No strategy, no orders, no credentials, no S1, no scored
compute — data plane only, fail closed everywhere.
"""

__version__ = "1.0.0"
GATEWAY_SCHEMA = "ldgv1_gateway@1"
