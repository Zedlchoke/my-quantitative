"""FOREX-FREE-V3 accounting kernel package (V3-P1, A2 lane).

Factory-only: synthetic fixtures only, no PnL on real market data, no
network, no new data authority.  Conventions are inherited unchanged from
the frozen V2 kernel (research/assets/forex_free_v2/accounting.py) and this
cycle adds the MANDATORY F1 remediation (V3 lessons register V3-L1 /
V3-L2): stress-tier cost multipliers applied to BOOKED stress PnL, with a
hand-computed fixture proving tier 1.5 and tier 2.0 differ from base, and
the dual price-only / financing-adjusted book -- see
:mod:`research.assets.forex_free_v3.accounting`.
"""
