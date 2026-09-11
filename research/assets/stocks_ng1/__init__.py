"""STOCKS-NG1 asset package: platform v3 data-plane adoption (P0).

Consumption set (frozen, plan section 3): exactly the three GRANTED S1
series -- form4-xml-substrate, form4-stream, eodhd-corp-actions --
consumed ONLY via ``research.assets.stocks_ng1.plane_adapter`` (the
consume_via_plane shape: AuthorityRegistry GRANTED gate -> CADS resolve
verify-on-read -> manifest-verified query).  Nothing else in this
package touches the network or any worktree outside the inherited pin.
"""

from .plane_adapter import (  # noqa: F401
    CADS_STORE_ROOT_DEFAULT,
    ConsumptionRefused,
    FLAG_TAG_10B5_1,
    FLAG_TAG_EVIDENCE,
    MalformedForm4Error,
    StocksNG1Plane,
    SUBSTRATE_ROOT_DEFAULT,
    detect_10b5_1_flag,
)

__all__ = [
    "CADS_STORE_ROOT_DEFAULT",
    "ConsumptionRefused",
    "FLAG_TAG_10B5_1",
    "FLAG_TAG_EVIDENCE",
    "MalformedForm4Error",
    "StocksNG1Plane",
    "SUBSTRATE_ROOT_DEFAULT",
    "detect_10b5_1_flag",
]
