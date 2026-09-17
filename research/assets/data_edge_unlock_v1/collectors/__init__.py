"""DATA-EDGE-UNLOCK-V1 prospective WebSocket collectors (lane C).

Authority:
- plans/PLAN_data_edge_unlock_v1.md section 4 (this cycle's Lane C contract),
- the ADOPTED base specification
  research/control/ng6_ng7_ng4_dossiers_2026-09/cng4-a3-prospective-contract-dossier.json
  (schema cng4_a3_prospective_contract@1), with cycle-specific overrides
  frozen in research/control/data_edge_unlock_v1/lane_c/c_collection_contract.json
  (schema deu_c_collection_contract@1) BEFORE any socket was opened.

Implementation adapted from the CRYPTO-NG4 lane A8 collectors
(research/control/crypto_ng4_run/collectors/ on branch orca/crypto-ng4-integration),
re-used under the cycle plan's explicit encouragement, with attribution in each
module header.  Wire formats are the MEASURED FDF-V1 census shapes.

Cycle-specific changes vs CNG4:
- NEW governed data root ~/.my-quantitative-data/data-edge-unlock-v1/raw
  (no prior cycle's root is read or written);
- PID files + heartbeat/liveness state live ONLY in the data root runtime dir
  (NEVER under research/ -- the CRYPTO-NG4 tracked-PID-file incident);
- cycle floor is 14 consecutive UTC days (the CNG4 60-day floor is the
  successor's bar, restated in the contract);
- Coinbase l2_data is re-attempted keyless (CNG4 degradation), Deribit trades
  are gated on the one permitted <=120s pre-start protocol census.

Collectors are LIGHT long-running daemons (plan hygiene): never the
machine-wide heavy lock; heartbeats carry bytes-written + payload-shape
counters (LESSONS Q-13); inode-check on append handles; payload-shape
mismatch fails LOUD.  Data collectors only -- no trading endpoints, no auth,
no orders, no PnL, keyless public market-data endpoints.
"""

from __future__ import annotations

CONTRACT_SCHEMA = "deu_c_collection_contract@1"
CYCLE_ID = "DATA-EDGE-UNLOCK-V1"

# Frozen instrument identity (base contract freeze field 1, adopted verbatim).
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

# Cycle event-regime constants (S4-frozen, base contract field 12; used by the
# REVIEW stage, not by the collector itself -- recorded here for one source).
STRESS_RV24 = {"BTC": 0.0542, "ETH": 0.1042}
