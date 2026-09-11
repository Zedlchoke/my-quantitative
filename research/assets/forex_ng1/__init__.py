"""FOREX-NG1 asset plane: P0 data authority + platform v3 adoption.

Consumption of the frozen S2/S3 set happens ONLY via
``research.assets.forex_ng1.plane_adapter.consume_via_plane`` (plan
section 3 adoption law): AuthorityRegistry GRANTED check -> CADS resolve
verify-on-read -> manifest-verified query. Fail-closed everywhere.
"""

from research.assets.forex_ng1.plane_adapter import (  # noqa: F401
    CALENDAR_PINS,
    ConsumptionRefused,
    ConsumedObject,
    EMU_LEDGER_PIN,
    S2_PINNED_ADDRESS,
    S3_ENTRY_NAMES,
    VintageRow,
    VintageStructureError,
    au_instants,
    build_census,
    ca_instants,
    census_lookup_instant,
    consume_s2_manifest,
    consume_via_plane,
    first_appearance,
    ga4_granted,
    gb_instants,
    gb_ref_period,
    latest_vintage_by_month,
    load_calendar,
    load_registry,
    normalize_instant_utc,
    parse_ca_tidy,
    parse_fred_vintaged,
    parse_ons_d7bt,
    parse_statcan_zip,
    quarter_first_month_from_end,
    us_instants,
    verify_s2_files,
    vintage_structure_proof,
)

__all__ = [
    "CALENDAR_PINS",
    "ConsumptionRefused", "ConsumedObject", "EMU_LEDGER_PIN",
    "S2_PINNED_ADDRESS", "S3_ENTRY_NAMES", "VintageRow",
    "VintageStructureError", "au_instants", "build_census",
    "ca_instants", "census_lookup_instant", "consume_s2_manifest",
    "consume_via_plane", "first_appearance", "ga4_granted",
    "gb_instants", "gb_ref_period", "latest_vintage_by_month",
    "load_calendar", "load_registry", "normalize_instant_utc",
    "parse_ca_tidy", "parse_fred_vintaged", "parse_ons_d7bt",
    "parse_statcan_zip", "quarter_first_month_from_end", "us_instants",
    "verify_s2_files", "vintage_structure_proof",
]
