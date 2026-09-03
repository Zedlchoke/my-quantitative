"""Hand-computed goldens for FXFV1-A3-P2 (family-2, late-NY fade).

Every value below is derived BY HAND from the frozen spec
(research/proposals/forex_free_v1/a3_lane/proposal_2.json) with the
arithmetic shown in comments.  Nothing here calls the module under test;
tests compare module outputs against these closed forms.

Reference clock facts (zoneinfo truth, EST = UTC-5, EDT = UTC-4):
* NY open 08:00: EST 13:00Z (e.g. Wed 2020-02-26), EDT 12:00Z (e.g. Wed 2020-07-08).
* 17:00 NY rollover: EST 22:00Z, EDT 21:00Z.
* Flatten bar (ends 16:00 NY, strictly < rollover): EST end 21:00Z, EDT end 20:00Z.
* Tokyo open 09:00 Asia/Tokyo (UTC+9, no DST): always ..:00Z on the same
  UTC date (Tue 2020-02-25 09:00 JST = 2020-02-25T00:00:00Z).
* US DST 2020: spring-forward Sun 2020-03-08, fall-back Sun 2020-11-01.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# sigma20 golden (used by the z-threshold scenarios)
#
# Fixture: the 20 trailing daily rollover-to-rollover log returns alternate
# exactly +a / -a with a = 0.001 (ten of each, any 20 consecutive terms of a
# strictly alternating +/-a sequence contain ten of each).
#   mean          = (10*0.001 + 10*(-0.001)) / 20 = 0
#   sum sq dev    = 20 * (0.001)**2 = 2.0e-5
#   sample var    = 2.0e-5 / (n-1) = 2.0e-5 / 19 = 1.052631578947368...e-6
#   sigma20       = sqrt(2.0e-5 / 19) = 0.001 * sqrt(20/19)
#                 = 1.0259783520851542e-3
# ---------------------------------------------------------------------------
SIGMA_A = 0.001
GOLDEN_SIGMA20 = SIGMA_A * math.sqrt(20.0 / 19.0)

# ---------------------------------------------------------------------------
# z-threshold goldens (signal day Wed 2020-02-26, EST)
#
# Trigger fixture: p0 = close of the bar ending at NY open = 1.0000
# (bar opening 2020-02-26T12:00:00Z, EST); the four NY-session bars open
# 13Z/14Z/15Z/16Z and p4 = close of the 4th = 1.0020.
#   r = p4/p0 - 1 = 1.0020/1.0000 - 1 = 0.002 (exact)
#   z = r/sigma  = 0.002 / (0.001*sqrt(20/19))
#                = 2*sqrt(19/20) = 1.9493588689617943  >= 1.0 -> TRIGGER
# Anchor fades the extension: r > 0 -> position -1 (short).
# Sign-flipped control: position +1 (long).
# ---------------------------------------------------------------------------
GOLDEN_R_BIG = 0.002
GOLDEN_Z_BIG = 0.002 / (SIGMA_A * math.sqrt(20.0 / 19.0))          # 1.9493588689617943
GOLDEN_DIR_ANCHOR = -1
GOLDEN_DIR_CONTROL = +1

# Sub-threshold fixture: p4 = 1.0005 -> r = 0.0005
#   z = 0.0005 / (0.001*sqrt(20/19)) = 0.48733971724044857 < 1.0 -> no trade
GOLDEN_R_SMALL = 0.0005
GOLDEN_Z_SMALL = 0.0005 / (SIGMA_A * math.sqrt(20.0 / 19.0))       # 0.48733971724044857

# Warm-up: with fewer than 21 prior trading-day closes (< 20 returns) the
# day is NO_TRADE / WARMUP, fail-closed; r and z are not even computed.

# ---------------------------------------------------------------------------
# Cost / cashflow goldens on the small triggered scenario (EST day)
#
# Fills (frozen, conservative close-to-close):
#   entry bar opens 17:00Z (12:00 NY EST), closes 18:00Z (13:00 NY) -> px 1.0025
#   S3 delay: entry bar opens 18:00Z (13:00 NY), closes 19:00Z (14:00 NY) -> px 1.0022
#   flatten bar opens 20:00Z (15:00 NY), closes 21:00Z (16:00 NY)  -> px 1.0010
#     (21:00Z < EST rollover 22:00Z, strictly before 17:00 NY)
#
# Anchor gross (short): -(1.0010/1.0025 - 1) = (1.0025-1.0010)/1.0025
#                       = 0.0015/1.0025 = 0.0014962593516209477
# Control gross (long): +(1.0010/1.0025 - 1) = -0.0015/1.0025
# S3 anchor gross:      -(1.0010/1.0022 - 1) = 0.0012/1.0022
#                       = 0.0011973653961279185
#
# Costs (frozen 1.5 bps/side x tier, every fill):
#   tier 1.0: round trip = 2*1.5*1.0 = 3.0 bps  = 0.00030 in return
#   tier 1.5: round trip = 2*1.5*1.5 = 4.5 bps  = 0.00045 in return
#   tier 2.0: round trip = 2*1.5*2.0 = 6.0 bps  = 0.00060 in return
# ---------------------------------------------------------------------------
GOLDEN_ENTRY_PX = 1.0025
GOLDEN_ENTRY_PX_S3 = 1.0022
GOLDEN_EXIT_PX = 1.0010

GOLDEN_GROSS_ANCHOR = 0.0015 / 1.0025          #  0.0014962593516209477
GOLDEN_GROSS_CONTROL = -0.0015 / 1.0025        # -0.0014962593516209477
GOLDEN_GROSS_ANCHOR_S3 = 0.0012 / 1.0022       #  0.0011973653961279185

GOLDEN_COST_RT_T1 = 3.0 * 1.0 / 1e4            # 0.0003  (3.0 bps)
GOLDEN_COST_RT_T2 = 3.0 * 1.5 / 1e4            # 0.00045 (4.5 bps)
GOLDEN_COST_RT_T3 = 3.0 * 2.0 / 1e4            # 0.0006  (6.0 bps)

GOLDEN_NET_T1 = GOLDEN_GROSS_ANCHOR - GOLDEN_COST_RT_T1    # 0.0011962593516209477
GOLDEN_NET_T2 = GOLDEN_GROSS_ANCHOR - GOLDEN_COST_RT_T2    # 0.0010462593516209477
GOLDEN_NET_T3 = GOLDEN_GROSS_ANCHOR_S3 - GOLDEN_COST_RT_T3  # 0.0005973653961279185

# ---------------------------------------------------------------------------
# DST / flatten-clock goldens (anchor arm, triggered scenario)
#
# Spring transition 2020 (Sun 2020-03-08):
#   Fri 2020-03-06 (EST): NY open 13:00Z; signal bar ends 17:00Z;
#     entry fill 18:00Z; rollover 22:00Z; flatten bar END = 21:00Z (< 22:00Z).
#   Mon 2020-03-09 (EDT): NY open 12:00Z; signal bar ends 16:00Z;
#     entry fill 17:00Z; rollover 21:00Z; flatten bar END = 20:00Z (< 21:00Z).
# Fall transition 2020 (Sun 2020-11-01):
#   Fri 2020-10-30 (EDT): flatten bar END = 20:00Z.
#   Mon 2020-11-02 (EST): flatten bar END = 21:00Z.
# The flatten bar is uniformly the bar ending 16:00 New York wall clock.
# ---------------------------------------------------------------------------
GOLDEN_SPRING = {
    "est_day": "2020-03-06",
    "edt_day": "2020-03-09",
    "est_ny_open": "2020-03-06T13:00:00Z",
    "edt_ny_open": "2020-03-09T12:00:00Z",
    "est_entry_fill": "2020-03-06T18:00:00Z",
    "edt_entry_fill": "2020-03-09T17:00:00Z",
    "est_exit_end": "2020-03-06T21:00:00Z",
    "edt_exit_end": "2020-03-09T20:00:00Z",
    "est_rollover": "2020-03-06T22:00:00Z",
    "edt_rollover": "2020-03-09T21:00:00Z",
}
GOLDEN_FALL = {
    "edt_day": "2020-10-30",
    "est_day": "2020-11-02",
    "edt_entry_fill": "2020-10-30T17:00:00Z",
    "est_entry_fill": "2020-11-02T18:00:00Z",
    "edt_exit_end": "2020-10-30T20:00:00Z",
    "est_exit_end": "2020-11-02T21:00:00Z",
}

# ---------------------------------------------------------------------------
# Tokyo-open neighbour golden (Tue 2020-02-25, Tokyo session)
#   Tokyo open 09:00 JST = 2020-02-25T00:00:00Z; p0 bar opens 2020-02-24T23:00Z
#   (Tokyo 08:00); session bars open 00Z..03Z; signal public 04:00Z
#   (13:00 Tokyo); entry bar opens 04:00Z, fill 05:00:00Z (14:00 Tokyo).
#   Flatten: first 17:00 NY strictly after fill = Tue 17:00 EST = 22:00Z;
#   flatten bar END = 21:00Z (16:00 NY Tuesday), strictly < rollover.
#   Same r = 0.002 and same 20-day NY-rollover sigma series -> same
#   z = 1.9493588689617943, fade position -1.
# ---------------------------------------------------------------------------
GOLDEN_NEIGHBOUR = {
    "day": "2020-02-25",
    "p0_open": "2020-02-24T23:00:00Z",
    "signal_ts": "2020-02-25T04:00:00Z",
    "entry_fill": "2020-02-25T05:00:00Z",
    "exit_end": "2020-02-25T21:00:00Z",
    "rollover": "2020-02-25T22:00:00Z",
    "r": 0.002,
    "z": GOLDEN_Z_BIG,
    "direction": -1,
}

# ---------------------------------------------------------------------------
# Warm-up boundary golden: 20 prior returns need 21 prior trading-day closes;
# a signal day with only k < 21 prior closes available is NO_TRADE/WARMUP.
# ---------------------------------------------------------------------------
GOLDEN_SIGMA_REQUIRED_PRIOR_CLOSES = 21
