"""A8-V11-OILEVER-DELEV family package (lane I-3, V11 implementation wave).

The frozen contract lives in :mod:`.strategy`; the generic-adapter join lives
in :mod:`.plugin`.  Schedule-only lane: nothing here computes, exposes or
persists a scored outcome.
"""

from research.v11.families.oilever_delev.plugin import (
    OileverDelevPlugin,
    PLUGIN_SCHEMA,
)

__all__ = ["OileverDelevPlugin", "PLUGIN_SCHEMA"]
