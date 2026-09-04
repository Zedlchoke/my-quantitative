"""V13 cycle packages (cycle CRYPTO-V13).

Family implementation lanes live under :mod:`research.v13.families`.  No
module in this package computes a scored outcome by itself; Phase I lanes
deliver frozen, schedule-only machinery whose scored execution is gated by
the V13 run contract (research/control/v13_run/run_contract.json).
"""
