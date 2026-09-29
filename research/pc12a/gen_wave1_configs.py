#!/usr/bin/env python
"""One-shot generator of the 64 wave-1 T1 leg configs (run once, output
committed). Params are frozen verbatim from the corpus texts; legs with
at least one declared default carry param_source='triage_default' and a
note naming it. 9 legs are PARKED (missing cross inputs) — see the
wave-1 handoff.
"""
import json
import os

CYCLE = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
SLEEVE = "POOL_B_TRIAGE"
COST_STAGED = "PANEL_VENUE_C1_MEASURED_PLUS_U2U3U4U5_DECLARED"
COST_UNSTAGED = "PANEL_VENUE_UNSTAGED_DECLARED_TBD"
PIP = {"EURUSD": 0.0001, "GBPUSD": 0.0001, "USDJPY": 0.01,
       "AUDUSD": 0.0001, "USDCAD": 0.0001}
FAM = {"A-TREND": "trend", "B-MEANREV": "meanrev", "C-BREAKOUT": "breakout",
       "E-SESSION": "calendar", "G-XASSET": "xasset", "I-STATARB": "statarb",
       "J-REGIME_OPT": "regime", "H-POSITIONING": "positioning"}

elig = json.load(open("/tmp/t1_elig.json"))  # gid -> (mech_key, label, family, horizon)


def cfg(gid, symbol, archetype, clock, params, pit, param_source,
        notes, warmup=None):
    mech_key, label, family, horizon = elig[gid]
    unit_params = {"unit_base_units": 10000, "pip_size": PIP[symbol]}
    if warmup is not None:
        unit_params["warmup_trading_days"] = warmup
    staged = symbol in ("EURUSD", "GBPUSD", "USDJPY")
    out = {
        "cycle_id": CYCLE,
        "sleeve_id": SLEEVE,
        "corpus_gid": gid,
        "family_id": family,
        "mech_key": mech_key,
        "archetype": archetype,
        "clock": clock,
        "symbol": symbol,
        "pit_join_list": pit,
        "cost_tier": COST_STAGED if staged else COST_UNSTAGED,
        "outcome_exposed_label": label,
        "cluster_id": f"{FAM[family]}_{horizon.lower()}",
        "params": {**params, **unit_params},
        "param_source": param_source,
        "notes": notes,
        "corpus_source_ref":
            f"FOREX-UNIFIED-STRATEGY-BRAINSTORM-V1/symbols/{symbol}.md#{gid.split('-')[1]}",
    }
    return out


D = "DAILY_00UTC_M1FILL"
M = "INTRADAY_M1_M1FILL"
D1 = lambda s: [f"{s}_D1_AGGREGATE"]  # noqa: E731
M1 = lambda s: [f"{s}_M1_BIDASK_VOL", "TZDATA_SESSIONS"]  # noqa: E731

LEGS = []

# ============================== GBPUSD (28) ==============================
LEGS += [
    cfg("GBPUSD-S001", "GBPUSD", "donchian_trail", D,
        {"entry_donchian": 20, "atr_n": 14, "trail_atr_mult": 2.5},
        D1("GBPUSD"), "corpus_verbatim",
        "S1: Donchian-20 close entry; ATR(14) unit risk declared as fixed "
        "single-unit (sizing policy = Stage-B overlay); trailing 2.5xATR.",
        warmup=30),
    cfg("GBPUSD-S002", "GBPUSD", "london_persistence", M,
        {"atr_d_n": 14},
        M1("GBPUSD"), "triage_default",
        "S2: 07:00-09:00 London sign, |ret|>0.3xATR-daily filter, 09:30 "
        "entry, range stop, 16:00 London exit. DECLARED DEFAULT: ATR-daily "
        "= ATR(14) D1 (period not literal in corpus text); EURUSD "
        "same-sign coupling declared-off (exemplar-precedent).",
        warmup=20),
    cfg("GBPUSD-S003", "GBPUSD", "adx_ema_rider",
        "INTRADAY_H4_M1FILL", {"bar_minutes": 240},
        M1("GBPUSD"), "corpus_verbatim",
        "S3: ADX(14) H4>25 + EMA20/50 H4 aligned; EMA20 pullback (bar "
        "straddling EMA20) entry; chandelier 3xATR(H4); gilt-2Y coupling "
        "declared-off (rates input not staged).",
        warmup=30),
    cfg("GBPUSD-S004", "GBPUSD", "weekly_ma_regime", D, {},
        D1("GBPUSD"), "corpus_verbatim",
        "S4: weekly MA5/MA20 regime, weekly rebalance (decision on the "
        "Friday close bar), stop on weekly close through MA20; carry-sign "
        "coupling declared-off.",
        warmup=115),
    cfg("GBPUSD-S007", "GBPUSD", "keltner_break", "INTRADAY_H4_M1FILL",
        {"bar_minutes": 240},
        M1("GBPUSD"), "corpus_verbatim",
        "S7: H4 Keltner(EMA20, 2.5xATR(14,H4)) breakout; stop half channel "
        "(1.25 ATR); target 3R; DECLARED: 30-day timeout exit (corpus has "
        "no exit timeout). RV-percentile coupling declared-off.",
        warmup=40),
    cfg("GBPUSD-S011", "GBPUSD", "session_range_rule", M,
        {"session_mode": "asian_fake_break"},
        M1("GBPUSD"), "corpus_verbatim",
        "S11: Asian range 00:00-06:00 UTC; pierce then close back inside "
        "before 09:00 UTC; fade to mid; stop +2 pip outside fake extreme; "
        "DECLARED: midday flat (12:00 UTC) exit (corpus has none).",
        warmup=15),
    cfg("GBPUSD-S012", "GBPUSD", "rsi2_barclock", "INTRADAY_H1_M1FILL",
        {"bar_minutes": 60, "rsi_lo": 5.0, "rsi_hi": 95.0,
         "filter_mode": "proximity", "ema_filter_n": 200, "prox_band": 0.01,
         "stop_atr_mult": 1.2, "exit_bars": 8},
        M1("GBPUSD"), "corpus_verbatim",
        "S12: RSI(2) H1 <5/>95 only within +/-1% of the 200-period H1 "
        "mean; exit RSI2 at 50 or 8 bars; stop 1.2xATR(H1); vol-percentile "
        "coupling declared-off.",
        warmup=25),
    cfg("GBPUSD-S013", "GBPUSD", "session_range_rule", M,
        {"session_mode": "bb_m15_asia_snap", "confirm_bar_minutes": 15},
        M1("GBPUSD"), "corpus_verbatim",
        "S13: M15 close outside BB(20,2) within 22:00-05:00 UTC, next bar "
        "back inside; target mid-band; stop half BB width; DECLARED: 08:00 "
        "UTC session flat (corpus has none).",
        warmup=15),
    cfg("GBPUSD-S014", "GBPUSD", "round_number_fade", "INTRADAY_H4_M1FILL",
        {"bar_minutes": 240, "touch_window_days": 10, "min_touches": 3,
         "stop_pips": 15.0, "target_pips": 50.0, "level_step_pips": 50.0},
        M1("GBPUSD"), "triage_default",
        "S14: >=3rd test of .00/.50 within 10d without an H4 close "
        "through; fade; stop 15 pip outside; target 50 pip. DECLARED "
        "DEFAULT: a 'test' = an H4 bar spanning the level with close "
        "within half a level-step (touch definition not literal).",
        warmup=15),
    cfg("GBPUSD-S016", "GBPUSD", "session_range_rule", M,
        {"session_mode": "monday_gap_gbp", "gap_pips": 25.0},
        M1("GBPUSD"), "corpus_verbatim",
        "S16: Monday gap >25 pip vs the Friday close (Friday 22:00 close "
        "declared = Friday day close); entry in the Sunday 22:30 UTC "
        "reopen window (falls back to the first Monday tradable bar when "
        "no Sunday panel day exists); stop half gap; target Friday close; "
        "DECLARED: late-Monday flat timeout.",
        warmup=10),
    cfg("GBPUSD-S017", "GBPUSD", "session_range_rule", M,
        {"session_mode": "ny_vwap_reversion"},
        M1("GBPUSD"), "corpus_verbatim",
        "S17: 15:30-18:30 London outside session-VWAP +/-2 sigma; fade to "
        "VWAP; stop +1 sigma; session flat at window end by construction.",
        warmup=15),
    cfg("GBPUSD-S019", "GBPUSD", "cross_z", D,
        {"cross_mode": "eurgbp_anchor", "z_window": 30, "z_entry": 2.0,
         "usd_flat_ratio": 0.3, "stop_atr": 1.0},
        D1("GBPUSD") + ["EURUSD_D1_AGGREGATE"], "corpus_verbatim",
        "S19: EURGBP z(30d) beyond +/-2 with |EURUSD 5d| < 0.3x|EURGBP 5d|"
        "; fade GBPUSD toward z=1; stop 1xATR(14); EURGBP derived as "
        "EURUSD/GBPUSD daily closes (triage: derivable).",
        warmup=45),
    cfg("GBPUSD-S021", "GBPUSD", "session_range_rule", M,
        {"session_mode": "london_box_orb", "confirm_bar_minutes": 5,
         "time_frame": "Europe/London", "box_window": [420, 480],
         "after_minute_utc": 480, "flat_minute_utc": 690,
         "target_r_mult": 1.5},
        M1("GBPUSD"), "corpus_verbatim",
        "S21: 07:00-08:00 London box; M5 close outside + 2-bar no-reentry; "
        "stop mid-box; target 1.5R; time-exit 11:30 London; UK-data-day "
        "box variant inactive until calendar staged (triage).",
        warmup=15),
    cfg("GBPUSD-S023", "GBPUSD", "nr7_m30_break", M,
        {"nr7_days": 7},
        M1("GBPUSD"), "corpus_verbatim",
        "S23: NR7/inside-day + next-day 30m close break of the day range; "
        "stop mid-range; target 2R; DECLARED: 21:00 UTC day-end flat.",
        warmup=15),
    cfg("GBPUSD-S024", "GBPUSD", "session_range_rule", M,
        {"session_mode": "london_box_orb", "confirm_bar_minutes": 15,
         "time_frame": "utc", "box_window": [810, 870],
         "after_minute_utc": 885, "flat_minute_utc": 1140,
         "target_r_mult": 1.5},
        M1("GBPUSD"), "triage_default",
        "S24: 13:30-14:30 UTC box; M15 close outside after 14:45 UTC; stop "
        "mid-box; exit 19:00 UTC. DECLARED DEFAULT: target = 1.5R "
        "projection (corpus 'day-range extreme' target not literal).",
        warmup=15),
    cfg("GBPUSD-S025", "GBPUSD", "session_range_rule", M,
        {"session_mode": "asian_break_retest", "confirm_bar_minutes": 15,
         "collect_window_utc": [0, 360], "break_frame": "Europe/London",
         "break_window": [420, 510]},
        M1("GBPUSD"), "corpus_verbatim",
        "S25: Asian range 00:00-06:00 UTC; break 07:00-08:30 London; M15 "
        "retest-hold within 3 bars; stop 5 pip inside range; target 1x "
        "range height; DECLARED: 16:00 UTC flat.",
        warmup=15),
    cfg("GBPUSD-S028", "GBPUSD", "h1_pdh_pdl", "INTRADAY_H1_M1FILL",
        {"bar_minutes": 60, "session_mode": "after_1400_london",
         "stop_mode": "level_measured"},
        M1("GBPUSD"), "corpus_verbatim",
        "S28: H1 close beyond PDH/PDL after 14:00 London; stop on re-entry "
        "into the range (the broken level); target measured move 1x "
        "day-range; EURUSD-confirm coupling declared-off.",
        warmup=20),
    cfg("GBPUSD-S029", "GBPUSD", "session_range_rule", M,
        {"session_mode": "midweek_range_break", "confirm_bar_minutes": 30},
        M1("GBPUSD"), "corpus_verbatim",
        "S29: break of the Mon-Tue range on Wednesday London; M30 entry; "
        "stop opposite edge; exit Friday 16:00 London; 2R target (trail "
        "declared as the fixed 2R).",
        warmup=15),
    cfg("GBPUSD-S042", "GBPUSD", "session_range_rule", M,
        {"session_mode": "friday_late_fade", "stop_pips": 30.0},
        M1("GBPUSD"), "corpus_verbatim",
        "S42: Friday 18:30+ UTC |week-move| > 1.5x weekly ATR; fade; stop "
        "30 pip; flat pre-21:30 UTC. DECLARED week-move window = week "
        "open (first Monday bar) to decision time; weekly ATR = mean TR "
        "of the last 2 completed weeks.",
        warmup=15),
    cfg("GBPUSD-S048", "GBPUSD", "regime_gate", D,
        {"gate_mode": "weekday"},
        D1("GBPUSD") + ["TZDATA_WEEKDAYS"], "triage_default",
        "S48: weekday family-allocation gate; DECLARED DEFAULT standalone "
        "mapping (gate role): Mon/Fri take the MR side of the prior day's "
        "move, Tue-Thu the trend side; flat on zero prior-day move.",
        warmup=5),
    cfg("GBPUSD-S063", "GBPUSD", "cross_z", D,
        {"cross_mode": "ratio_router", "idio_ratio": 2.0, "usd_ratio": 0.5},
        D1("GBPUSD") + ["EURUSD_D1_AGGREGATE"], "corpus_verbatim",
        "S63: 5d |ret| ratio EURGBP vs EURUSD routes signals (idio>2 "
        "GBP-driver -> Cable momentum; <0.5 USD-driver -> EURUSD "
        "momentum proxy); gate role, DECLARED standalone mapping.",
        warmup=15),
    cfg("GBPUSD-S065", "GBPUSD", "h1_pdh_pdl", "INTRADAY_H1_M1FILL",
        {"bar_minutes": 60, "session_mode": "any", "stop_mode": "level_2r",
         "require_eurusd_confirm": True},
        M1("GBPUSD") + ["EURUSD_D1_AGGREGATE"], "triage_default",
        "S65: Cable PDH/PDL break requires a same-side EURUSD prior-day "
        "band break (double confirm); stop single-side invalidation (the "
        "broken level); target 2R. DECLARED DEFAULT: the EURUSD "
        "same-side break = prior EURUSD day CLOSED beyond the day-before "
        "high/low (daily-feed proxy for an intraday band break).",
        warmup=20),
    cfg("GBPUSD-S083", "GBPUSD", "cross_z", D,
        {"cross_mode": "beta_router", "beta_window": 60, "band_lo": 0.75,
         "band_hi": 1.05, "outside_days": 10},
        D1("GBPUSD") + ["EURUSD_D1_AGGREGATE"], "corpus_verbatim",
        "S83: 60d Cable/EURUSD beta outside [0.75,1.05] for 10 days; "
        "router/gate role; DECLARED standalone mapping: idio regime "
        "trades GBP-side 20d momentum, USD regime trades EURUSD 20d "
        "momentum.",
        warmup=75),
    cfg("GBPUSD-S084", "GBPUSD", "ar_persistence_gate",
        "INTRADAY_H1_M1FILL",
        {"bar_minutes": 60, "ar_window": 120, "coef_min": 0.1},
        M1("GBPUSD"), "triage_default",
        "S84: rolling 120h AR(1) sign with |coef|>0.1 persistence gate; "
        "estimator = OLS AR(1) slope on H1 log returns (standard, per "
        "triage). DECLARED standalone mapping: coef>+0.1 follow the last "
        "hour's sign, coef<-0.1 fade it, else flat.",
        warmup=15),
    cfg("GBPUSD-S086", "GBPUSD", "usdjpy_momentum_gate",
        "INTRADAY_H1_M1FILL",
        {"bar_minutes": 60},
        M1("GBPUSD") + ["USDJPY_D1_AGGREGATE"], "triage_default",
        "S86: USDJPY 4h risk-momentum gate for Cable continuation. "
        "MECHANIZATION_DEVIATION (visible in arm identity): the VIX>20 "
        "regime coupling is NOT computable on this checkout (no VIX "
        "series staged) and is declared OFF; DECLARED momentum definition "
        "= USDJPY D1 EMA20 vs EMA50 (4h momentum proxied on the daily "
        "feed); stop 3xATR(14,D1) declared.",
        warmup=60),
    cfg("GBPUSD-S087", "GBPUSD", "cross_z", D,
        {"cross_mode": "z_alignment", "z_window": 20, "z_entry": 1.8,
         "z_target": 2.8},
        D1("GBPUSD") + ["EURUSD_D1_AGGREGATE"], "corpus_verbatim",
        "S87: EURGBP z(20d) and Cable z(20d) same GBP-meaning sign, |z|>1.8 "
        "both; join toward z 2.8; stop on one-leg z-flip.",
        warmup=45),
    cfg("GBPUSD-S090", "GBPUSD", "session_range_rule", M,
        {"session_mode": "sweep_reclaim", "confirm_bar_minutes": 5},
        M1("GBPUSD"), "triage_default",
        "S90: M5 sweep of the Asian/overnight extreme + reclaim within 2 "
        "bars in 07:00-10:00 London + volume spike; stop +2 pip outside "
        "sweep. DECLARED DEFAULTS: spike = M5 volume >1.5x the median of "
        "the trailing 20 M5 bars (relative units, audit-lawful); target = "
        "Asian-range mid (VWAP-priority honored as the range mid "
        "proxy); midday flat.",
        warmup=15),
    cfg("GBPUSD-S091", "GBPUSD", "regime_gate", D,
        {"gate_mode": "rv_trio", "band_lo": 30.0, "band_hi": 70.0},
        D1("GBPUSD"), "triage_default",
        "S91: RV20 1y-percentile master switch: <30 MR side, >70 trend "
        "side, middle half-size; RV estimator DECLARED = 20d log-return "
        "stdev annualized, percentile over trailing 252 realizations.",
        warmup=280),
]

# ============================== USDJPY (13) ==============================
LEGS += [
    cfg("USDJPY-S002", "USDJPY", "ma_adx_regime", D, {},
        D1("USDJPY"), "corpus_verbatim",
        "S2: MA50>MA200 + ADX(14)>25 regime; 20d-swing stop; exit ADX<20 "
        "twice consecutively; rate-diff coupling declared-off.",
        warmup=230),
    cfg("USDJPY-S003", "USDJPY", "ts_momentum", D,
        {"lookbacks": [252], "skip_days": 21, "vol_target_annual": 0.10,
         "rebalance": "monthly"},
        D1("USDJPY"), "corpus_verbatim",
        "S3: 12-month return skipping the most recent month; vol-target "
        "10% annualized; monthly rebalance; RV20 sizing declared "
        "(vol estimate window 20d).",
        warmup=290),
    cfg("USDJPY-S009", "USDJPY", "turtle_pyramid", D,
        {"entry_donchian": 20, "atr_n": 20, "max_units": 4},
        D1("USDJPY"), "corpus_verbatim",
        "S9: turtle pyramiding 0.5N unit risk -> single 10k units per "
        "pyramid step (units quantized to whole 10k lots; 0.5% risk "
        "sizing = Stage-B overlay); add per 1N max 4 units; cluster stop "
        "entry-2N; trail 2N; vol-percentile coupling declared-off.",
        warmup=60),
    cfg("USDJPY-S014", "USDJPY", "rsi2_barclock", "INTRADAY_H4_M1FILL",
        {"bar_minutes": 240, "rsi_lo": 5.0, "rsi_hi": 95.0,
         "filter_mode": "ema200", "ema_filter_n": 200, "stop_atr_mult": 1.0,
         "exit_bars": 8},
        M1("USDJPY"), "corpus_verbatim",
        "S14: RSI2<5 on H4 with price above 200EMA(H4) -> long; >95 below "
        "-> short; exit RSI2 crosses 50 or 8 bars; stop 1xATR(H4); "
        "BoJ/FOMC-week coupling declared-off.",
        warmup=230),
    cfg("USDJPY-S017", "USDJPY", "session_range_rule", M,
        {"session_mode": "asia_vwap_recross"},
        M1("USDJPY"), "triage_default",
        "S17: Asia (00:00-09:00 JST) move >0.8xATR20(D1) + VWAP recross "
        "in the first 90 London minutes; stop outside London H/L "
        "(DECLARED: stop at the Asia extreme +/-2 pip; London-window "
        "flat at 10:30 London); target Tokyo open; UST coupling "
        "declared-off.",
        warmup=30),
    cfg("USDJPY-S018", "USDJPY", "session_range_rule", M,
        {"session_mode": "monday_gap_jpy"},
        M1("USDJPY"), "corpus_verbatim",
        "S18: Monday gap vs Friday close >0.5xATR(H1) (ATR(H1) = mean TR "
        "of the last 60 M1 bars); fade at Monday Tokyo open; stop 0.6x "
        "gap outside; target 50% gap; Tokyo-session window exit.",
        warmup=10),
    cfg("USDJPY-S022", "USDJPY", "session_range_rule", M,
        {"session_mode": "ny_orb", "confirm_bar_minutes": 5},
        M1("USDJPY"), "corpus_verbatim",
        "S22: NY 30-min opening range 08:30-09:00 ET; break on M5 close; "
        "stop opposite OR edge; trail 1xATR(H1); flat 15:00 ET; "
        "data-surprise coupling declared-off.",
        warmup=10),
    cfg("USDJPY-S023", "USDJPY", "bb_squeeze_break", D,
        {"bb_n": 20, "bb_k": 2.0, "bbw_pct_max": 10.0, "bbw_window": 120,
         "stop_mode": "opposite_band", "target_squeeze_mult": 2.0},
        D1("USDJPY"), "corpus_verbatim",
        "S23: BBW < P10 of 120d + D1 close outside BB(20,2) on expansion; "
        "stop opposite band; target 2x squeeze width; UST direction "
        "coupling declared-off (triage).",
        warmup=140),
    cfg("USDJPY-S026", "USDJPY", "h1_pdh_pdl", "INTRADAY_H1_M1FILL",
        {"bar_minutes": 60, "session_mode": "london_ny",
         "stop_mode": "atr_half"},
        M1("USDJPY"), "corpus_verbatim",
        "S26: H1 close through PDH/PDL in London or NY; stop 0.5xATR(H1) "
        "inside; target 1xATR(D1) extension.",
        warmup=20),
    cfg("USDJPY-S029", "USDJPY", "atr_ratio_break", D,
        {"atr_fast": 5, "atr_slow": 20, "break_days": 10},
        D1("USDJPY"), "corpus_verbatim",
        "S29: ATR5/ATR20 >1.5 + 10-day H/L break; stop 1.5xATR5; exit "
        "ratio<1.0; own-price RSI(14)>55/<45 confirm; MOF-day exclusion "
        "inactive until archive staged (triage).",
        warmup=30),
    cfg("USDJPY-S044", "USDJPY", "calendar_season", D,
        {"window_mode": "fixed_dates", "entry_on": [3, 10],
         "exit_after": [3, 31], "size_mult": 0.5,
         "stop_atr_week_mult": 1.5},
        D1("USDJPY"), "corpus_verbatim",
        "S44: short from 10/03 yearly at 0.5x size; exit 31/03; stop "
        "1.5xATR-week (5d ATR); Fed-event coupling declared-off.",
        warmup=30),
    cfg("USDJPY-S045", "USDJPY", "calendar_season", D,
        {"window_mode": "september_week"},
        D1("USDJPY"), "triage_default",
        "S45: last-Sep-week short bias after 5 weak sessions; "
        "DECLARED DEFAULT: 'weak' = negative 5-session close-to-close "
        "return; 5-session hold; 1xATR-week stop.",
        warmup=30),
    cfg("USDJPY-S050", "USDJPY", "hour_of_day_drift", M,
        {"slot_minutes": 30, "t_min": 3.0, "fdr_q": 0.05,
         "rolling_window_trading_days": 750},
        M1("USDJPY"), "triage_default",
        "S50: M30 hour-of-day drift; t>3 after FDR on rolling 3y; drift "
        "entry at slot start / exit at slot end; stop 0.5xATR(M30). "
        "DECLARED DEFAULTS (triage 'declare FDR method'): FDR = "
        "Benjamini-Hochberg step-up at q=0.05 over the 48 half-hour "
        "slots, normal-approximation p-values; event-hour exclusion "
        "inactive until calendar staged (triage).",
        warmup=760),
]

# ============================== EURUSD (9) ==============================
LEGS += [
    cfg("EURUSD-S003", "EURUSD", "ts_momentum", D,
        {"lookbacks": [126], "skip_days": 0, "vol_target_annual": 0.10,
         "rebalance": "monthly"},
        D1("EURUSD"), "triage_default",
        "S3: 6-month return sign; monthly rebalance; vol-target sizing. "
        "DECLARED DEFAULT: the corpus 'size inversely ATR(60)' is "
        "mechanized as inverse RV20 annualized (same intent, one "
        "estimator); policy-quadrant coupling declared-off.",
        warmup=150),
    cfg("EURUSD-S012", "EURUSD", "rsi2_barclock", "INTRADAY_H1_M1FILL",
        {"bar_minutes": 60, "rsi_lo": 5.0, "rsi_hi": 95.0,
         "filter_mode": "ema200", "ema_filter_n": 200, "stop_atr_mult": 1.0,
         "exit_bars": 8, "pivot_pips": 15, "adx_d_max": 25.0},
        M1("EURUSD"), "triage_default",
        "S12: RSI(2) H1 <5/>95 within 15 pip of the weekly pivot or a "
        ".00/.50 round number + ADX(D)<25; target EMA9(H1); stop "
        "1xATR(H1). DECLARED DEFAULTS: weekly pivot = classic "
        "(pH+pL+pC)/3 of the prior week; round number = nearest 50-pip "
        "multiple; 2-ENTRY scaling declared OFF (single unit); "
        "macro-slope coupling declared-off.",
        warmup=25),
    cfg("EURUSD-S013", "EURUSD", "h4_zscore", "INTRADAY_H4_M1FILL",
        {"bar_minutes": 240},
        M1("EURUSD"), "corpus_verbatim",
        "S13: H4 z=(close-SMA20)/sigma20 beyond +/-2 with ADX(14,H4)<20; "
        "target SMA20; stop 2.8 sigma; event-week coupling declared-off.",
        warmup=45),
    cfg("EURUSD-S020", "EURUSD", "session_range_rule", M,
        {"session_mode": "tokyo_bb_eu", "confirm_bar_minutes": 5,
         "bbw_pct_max": 40.0, "bbw_window": 2880, "stop_pips": 6.0,
         "max_per_night": 3},
        M1("EURUSD"), "triage_default",
        "S20: BB(40,2) M5 01:00-06:00 UTC; fade band touch when BBW "
        "percentile <40; target mid-band; stop 6 pip; max 3/night. "
        "DECLARED DEFAULT: BBW percentile window = trailing 2880 M5 "
        "bars (10 trading days of window bars); headline-regime "
        "coupling declared-off.",
        warmup=55),
    cfg("EURUSD-S024", "EURUSD", "nr7_stop_orders", M,
        {"stop_pad_pips": 3.0},
        M1("EURUSD"), "corpus_verbatim",
        "S24: NR7 or 2 consecutive inside days -> next-day stop orders "
        "both sides of the day range +3 pip (intrabar M1 mid touch); "
        "trail 2xATR(10); event coupling declared-off.",
        warmup=15),
    cfg("EURUSD-S027", "EURUSD", "atr_ratio_h4", "INTRADAY_H4_M1FILL",
        {"bar_minutes": 240},
        M1("EURUSD"), "corpus_verbatim",
        "S27: ATR(5)/ATR(50) H4 crossing 1.5 from below 1.0; enter the "
        "expansion candle's direction; stop 1xATR(5,H4) ratcheted; exit "
        "ratio<1.0 (declared trail).",
        warmup=30),
    cfg("EURUSD-S044", "EURUSD", "calendar_season", D,
        {"window_mode": "final_week_quarter", "qtd_threshold": -0.03},
        D1("EURUSD"), "corpus_verbatim",
        "S44: QTD EURUSD <-3% into the final week of the quarter -> "
        "light long; exit the first business day of the new quarter.",
        warmup=70),
    cfg("EURUSD-S046", "EURUSD", "calendar_season", D,
        {"window_mode": "month_turn", "window_days": 2,
         "max_hold_sessions": 4},
        D1("EURUSD") + ["TZDATA_WEEKDAYS"], "corpus_verbatim",
        "S46: 4 sessions around the month-turn (2 before + 2 after), "
        "bias = prior-month sign (continuation); hold <=4 sessions.",
        warmup=50),
    cfg("EURUSD-S091", "EURUSD", "regime_gate", D,
        {"gate_mode": "rv_band", "band_lo": 20.0, "band_hi": 80.0},
        D1("EURUSD"), "triage_default",
        "S91: 20d RV percentile gate: 20-80 trend-on / <20 MR / >80 flat. "
        "DECLARED DEFAULTS: RV estimator = 20d log-return stdev "
        "annualized over trailing 252 realizations; gate states mapped "
        "standalone (trend = 20d momentum, MR = fade of it).",
        warmup=280),
]

# ============================== AUDUSD (8 of 13) ==========================
LEGS += [
    cfg("AUDUSD-S002", "AUDUSD", "donchian_sar", D,
        {"entry_donchian": 20, "sar_donchian": 55, "adx_gate": 20.0},
        D1("AUDUSD"), "corpus_verbatim",
        "S2: Donchian 20/55 stop-and-reverse; ADX14>20 gate; 0.5% risk "
        "declared as fixed single-unit sizing (Stage-B overlay).",
        warmup=60),
    cfg("AUDUSD-S003", "AUDUSD", "adx_macd_persist", D, {},
        D1("AUDUSD"), "corpus_verbatim",
        "S3: ADX14(D1)>25 + MACD-hist same sign 3 bars; enter on the "
        "ADX cross of 25 in the MACD-hist direction; exit ADX<20; VIX "
        "coupling declared-off.",
        warmup=60),
    cfg("AUDUSD-S006", "AUDUSD", "ts_momentum", D,
        {"lookbacks": [63, 126, 252], "skip_days": 0,
         "vol_target_annual": 0.10, "rebalance": "weekly"},
        D1("AUDUSD"), "corpus_verbatim",
        "S6: sign(63/126/252d) majority vote; vol-target 10% annualized; "
        "weekly rebalance; DXY coupling declared-off.",
        warmup=280),
    cfg("AUDUSD-S023", "AUDUSD", "weekly_nr7_bracket", D, {},
        D1("AUDUSD") + ["TZDATA_WEEKDAYS"], "triage_default",
        "S23: weekly NR7 + 20-week-range half + Monday bracket toward the "
        "occupied half + stop inside the squeeze range. DECLARED "
        "DEFAULTS: bracket mechanized as an immediate Monday entry in "
        "the occupied half's direction; stop at the prior-week mid; "
        "holiday-week skip inactive until calendar staged (triage).",
        warmup=115),
    cfg("AUDUSD-S026", "AUDUSD", "bb_squeeze_break", D,
        {"bb_n": 20, "bb_k": 2.0, "bbw_pct_max": 15.0, "bbw_window": 120,
         "bbw_consec_days": 5, "stop_mode": "mid_band",
         "timeout_days": 8},
        D1("AUDUSD"), "corpus_verbatim",
        "S26: BBW percentile<15 for 5 consecutive days then D1 close "
        "outside BB(20,2); stop mid-band; 8-day timeout; RV-ratio "
        "coupling declared-off.",
        warmup=140),
    cfg("AUDUSD-S029", "AUDUSD", "weekly_h4_break", "INTRADAY_H4_M1FILL",
        {"bar_minutes": 240},
        M1("AUDUSD"), "corpus_verbatim",
        "S29: 2 consecutive H4 closes beyond the prior week's H/L; stop "
        "inside the prior week (at the broken edge); exit 2xATR-W1; "
        "S66 risk-gate coupling declared-off.",
        warmup=30),
    cfg("AUDUSD-S044", "AUDUSD", "calendar_season", D,
        {"window_mode": "fixed_dates", "entry_on": [6, 24],
         "exit_after": [7, 1], "size_mult": 1.0,
         "stop_atr_day_mult": 1.0},
        D1("AUDUSD") + ["TZDATA_WEEKDAYS"], "corpus_verbatim",
        "S44: long 24-28/06 (AU fiscal year-end repatriation); exit "
        "01-02/07; stop 1xATR-D1; FOMC/RBA-week skip inactive until "
        "calendar staged (triage).",
        warmup=30),
    cfg("AUDUSD-S096", "AUDUSD", "regime_gate", D,
        {"gate_mode": "vol_target_overlay", "target_vol": 0.10,
         "cap_mult": 3.0},
        D1("AUDUSD"), "triage_default",
        "S96: vol-target overlay size = target_vol/RV20 capped 3x; "
        "overlay role. DECLARED DEFAULTS: target vol = 10% annualized "
        "(not literal in text); RV20 = 20d log-return stdev annualized; "
        "direction = 20d momentum (overlay has no own view).",
        warmup=30),
]

# ============================== USDCAD (6 of 7) ===========================
LEGS += [
    cfg("USDCAD-S002", "USDCAD", "donchian_sar", D,
        {"entry_donchian": 20, "sar_donchian": 55},
        D1("USDCAD"), "corpus_verbatim",
        "S2: classic Donchian 20/55 stop-and-reverse, no filter (clean "
        "baseline); 0.5% risk declared as fixed single-unit sizing.",
        warmup=60),
    cfg("USDCAD-S004", "USDCAD", "ma200_dislocation", D,
        {"ma_n": 200, "atr_n": 200, "disloc_min": 2.0, "mom_days": 20},
        D1("USDCAD"), "corpus_verbatim",
        "S4: |price-200DMA|/ATR200 >2.0 + same-sign 20D momentum; stop "
        "halfway to the 200DMA; DECLARED exit: dislocation unwound "
        "(|dis|<1); oil-gate coupling declared-off.",
        warmup=230),
    cfg("USDCAD-S006", "USDCAD", "weekly_swing_break", D,
        {"bb_weeks": 20},
        D1("USDCAD"), "corpus_verbatim",
        "S6: weekly swing-high break + weekly close outside the "
        "mid-Bollinger(20,W1); entry next week; stop prior-week swing "
        "low; CB-week coupling declared-off.",
        warmup=115),
    cfg("USDCAD-S011", "USDCAD", "rsi2_daily_pullback", D,
        {"rsi_lo": 10.0, "rsi_hi": 90.0, "exit_lo": 60.0,
         "stop_atr_mult": 1.5},
        D1("USDCAD"), "corpus_verbatim",
        "S11: RSI(2)D <10 in a 200DMA uptrend -> long at next open; exit "
        "RSI2>60; stop 1.5xATR(14); mirrored short; oil-gate coupling "
        "declared-off.",
        warmup=230),
    cfg("USDCAD-S016", "USDCAD", "bb_lowvol_range", D,
        {"bb_n": 20, "bbw_pct_max": 20.0, "bbw_window": 120,
         "adx_max": 15.0},
        D1("USDCAD"), "triage_default",
        "S16: BBW percentile<20 + ADX<15 range regime; fade 2-sigma band "
        "touches to the mid; stop 1xATR(14). DECLARED DEFAULT: BBW "
        "percentile window = 120 days; event-week coupling declared-off.",
        warmup=140),
    cfg("USDCAD-S091", "USDCAD", "regime_gate", D,
        {"gate_mode": "rv_weight"},
        D1("USDCAD"), "triage_default",
        "S91: 20D RV percentile dynamic A-vs-B weighting; gate role. "
        "DECLARED DEFAULT weight map (triage 'declare weight map'): "
        "pct>50 trend-side (20d momentum long/short), pct<=50 flat; RV20 "
        "percentile over trailing 252d.",
        warmup=280),
]

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "legs_config")
os.makedirs(out_dir, exist_ok=True)
for c in LEGS:
    fn = os.path.join(out_dir, c["corpus_gid"] + ".json")
    with open(fn, "w", encoding="utf-8") as fh:
        json.dump(c, fh, sort_keys=True, indent=1)
        fh.write("\n")
print(f"wrote {len(LEGS)} configs to {out_dir}")
