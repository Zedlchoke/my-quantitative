"""FOREX-FREE-V6 family-module package.

P1 kernel lane (A2): the V6 scored-ledger row schema
(:mod:`research.assets.forex_free_v6.ledger_row_v6`), carrying the
F-TERM-4 fix — every V6 scored ledger row MANDATES ``arm_config_digest``
(sha256 over the arm's frozen per-arm config projection) and the builder
refuses to construct a row without it (fail closed).

The inherited accounting kernel
(research/assets/forex_free_v3/accounting.py and the older
research/assets/forex/ kernel family) is imported READ-ONLY and is never
modified; canonical-JSON and sha256 conventions are inherited from it so
V6 digests use the exact house serialization.
"""
