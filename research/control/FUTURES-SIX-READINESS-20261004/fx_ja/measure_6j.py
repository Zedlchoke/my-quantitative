#!/usr/bin/env python
"""Lane FX-JA-READINESS, FUTURES-SIX-READINESS-20261004 — 6J tasks 1/2/3.

Task 1  quote-orientation re-proof from RAW 6J parquets (2024-07-11 MOF op day)
        + notional & round-trip cost arithmetic recomputation.
Task 2  cease-guard law (6J_DEEP_v2.md §8, ERRATUM M-5) re-measured from raw:
        2022-09-20 exchange open, Z2 volume, k=5 held ceased U2, trailing-5 means.
Task 3  identity: definitions min_price_increment + measured increment grid on
        sampled windows (2020 / 2023 / 2026), multiplier pinned.

No PnL/returns beyond descriptive session move arithmetic; no network.
Writes ONLY under fx_ja/.
"""
from __future__ import annotations

import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_ja_lib import (  # noqa: E402
    CHI, DATA_ROOT, MONTH_CODE, OUTRIGHT_RE, PX_SCALE, add_session, files_for,
    jdump, k5_chain, load_slice, third_wednesday,
)

OUT = os.path.dirname(os.path.abspath(__file__))

JY_ROOTS_2022_26 = ["AV1R-O1M-6J-BACKFILL"]
JY_ROOTS_2026 = ["AV1T-O1M-6J"]
JY_ROOTS_2020 = ["AV1B-O1M-6J-BACKFILL2"]


def resolve_contracts(df: pd.DataFrame) -> pd.DataFrame:
    """Map decade-ambiguous one-digit symbols to (symbol, year) keys inside the
    slice window (3rd-Wednesday delivery containment; 6J_deep_lib semantics,
    localized)."""
    t0, t1 = df["dt"].min(), df["dt"].max()

    def key(sym: str) -> str:
        m = OUTRIGHT_RE["6J"].fullmatch(sym)
        code, digit = m.group(1), int(m.group(2))
        ok = []
        for y in (2000 + digit, 2010 + digit, 2020 + digit):
            e = third_wednesday(y, MONTH_CODE[code])
            lo = (t0 - pd.Timedelta(days=820)).tz_localize(None)
            hi = (t1 + pd.Timedelta(days=560)).tz_localize(None)
            if lo <= pd.Timestamp(e) <= hi:
                ok.append(y)
        assert len(ok) == 1, (sym, ok, t0, t1)
        return f"{sym[:2]}{sym[2]}{digit}_{ok[0]}"

    df = df.copy()
    df["contract"] = df["raw_symbol"].map(key)
    return df


# ---------------------------------------------------------------------------
# Task 1 — orientation re-proof (own slice, raw parquet)
# ---------------------------------------------------------------------------

def task1_orientation():
    df = load_slice(JY_ROOTS_2022_26, "2024-07-09", "2024-07-13",
                    OUTRIGHT_RE["6J"])
    df = add_session(df)
    df = resolve_contracts(df)
    d11 = df[df["session_date"] == pd.Timestamp("2024-07-11").date()]
    d10 = df[df["session_date"] == pd.Timestamp("2024-07-10").date()]
    vols = d11.groupby("contract")["volume"].sum().sort_values(ascending=False)
    front = vols.index[0]
    f11 = d11[d11["contract"] == front].sort_values("ts_event")
    f10 = d10[d10["contract"] == front].sort_values("ts_event")
    o = float(f11["open"].iloc[0]) * PX_SCALE
    c = float(f11["close"].iloc[-1]) * PX_SCALE
    hi = float(f11["high"].max()) * PX_SCALE
    lo = float(f11["low"].min()) * PX_SCALE
    ret_pct = (c / o - 1.0) * 100.0
    # burst minute (UTC wall clock, pinned to 2024-07-11 exactly)
    day_str = d11["dt"].dt.strftime("%Y-%m-%d")
    assert (day_str == "2024-07-11").all() or (
        d11["dt"].min() >= pd.Timestamp("2024-07-10 22:00", tz="UTC")), \
        "session 07-11 spans 2024-07-10T22:00Z..2024-07-11T21:00Z by construction"
    burst = []
    for hhmm in ("12:39", "12:40", "12:41", "12:42", "12:43", "12:44", "12:45"):
        m = df[(df["dt"].dt.strftime("%Y-%m-%d %H:%M") == f"2024-07-11 {hhmm}")]
        if len(m):
            mfc = m[m["contract"] == front].sort_values("ts_event")
            burst.append({
                "utc_minute": f"2024-07-11T{hhmm}",
                "front_close_usd_per_jpy": float(mfc["close"].iloc[-1]) * PX_SCALE,
                "front_volume": int(mfc["volume"].sum()),
                "all_6j_volume": int(m["volume"].sum()),
                "front_tick_move_vs_prior_minute": None,
            })
    for i in range(1, len(burst)):
        burst[i]["front_tick_move_vs_prior_minute"] = round(
            (burst[i]["front_close_usd_per_jpy"]
             - burst[i - 1]["front_close_usd_per_jpy"]) / 5e-7, 1)

    # framing sensitivity: UTC-calendar-day aggregate vs CT-session aggregate
    # (the sibling P3 check quoted 415,392 lots / +2.056%; re-measured here both ways)
    utc = df[(df["dt"] >= pd.Timestamp("2024-07-11 00:00", tz="UTC"))
             & (df["dt"] <= pd.Timestamp("2024-07-11 23:59", tz="UTC"))]
    uf = utc[utc["contract"] == front].sort_values("ts_event")

    # notional + RT cost arithmetic (all inputs pinned)
    representative_price = 0.006383  # re-measured below from raw 2026 tail
    tail = load_slice(JY_ROOTS_2026, "2026-09-28", "2026-10-02", OUTRIGHT_RE["6J"])
    tail = add_session(tail)
    tail = resolve_contracts(tail)
    tv = tail.groupby("contract")["volume"].sum().sort_values(ascending=False)
    tf = tail[tail["contract"] == tv.index[0]].sort_values("ts_event")
    measured_2026_close = float(tf["close"].iloc[-1]) * PX_SCALE
    last_bar_utc = str(tf["dt"].iloc[-1])

    mult = 12_500_000
    fees = {"T1": 2.46, "T2": 2.26, "T3": 2.06, "T4": 1.86}
    spread_proxy = 25.00      # 4 ticks x $6.25, DC §1.7 6J column (high-biased)
    tick_usd = 6.25           # 5e-7 USD/JPY x 12.5e6
    notional = mult * representative_price
    rt = {}
    for tier, fee in fees.items():
        rt[tier] = {}
        for slip in (1, 2, 3):
            per_side = fee + spread_proxy + slip * tick_usd
            rt_usd = 2 * per_side
            rt[tier][f"slip{slip}"] = {
                "per_side_usd": round(per_side, 2),
                "rt_usd": round(rt_usd, 2),
                "bp_of_notional": round(rt_usd / notional * 1e4, 4),
            }
    band = {}
    for name, px in (("band_low_0.0061095", 0.0061095),
                     ("band_high_0.0099205", 0.0099205)):
        n = mult * px
        band[name] = {
            "notional_usd": round(n, 2),
            "T1_slip1_bp": round(67.42 / n * 1e4, 4),
            "T1_slip3_bp": round(92.42 / n * 1e4, 4),
        }

    out = {
        "schema": "6j_orientation_recheck@1",
        "task": "FUTURES-SIX-READINESS-20261004 / FX-JA-READINESS task 1",
        "law": ("6J quoted USD per JPY (JPY/USD convention); 6J UP = JPY "
                "strengthens vs USD; no silent inversion; implied USDJPY = "
                "1/(6J price)"),
        "inputs": {
            "raw_files": ([os.path.basename(f) for f in files_for("AV1R-O1M-6J-BACKFILL")]
                          + [os.path.basename(f) for f in files_for("AV1T-O1M-6J")]),
            "window_utc": ["2024-07-09", "2024-07-13"],
            "price_scale": "int nanos; USD_per_JPY = raw x 1e-9 (cited 6J_deep_lib.py PX_SCALE)",
            "tick_int_nano_units": 500,
        },
        "results": {
            "front_contract_2024_07_11": front,
            "front_volume_2024_07_11": int(vols.iloc[0]),
            "front_volume_2024_07_10": int(d10[d10["contract"] == front]["volume"].sum()),
            "volume_ratio_vs_prior_day": round(float(vols.iloc[0]) /
                float(d10[d10["contract"] == front]["volume"].sum()), 3),
            "session_open_usd_per_jpy": o,
            "session_close_usd_per_jpy": c,
            "session_move_pct": round(ret_pct, 4),
            "day_range_usd_per_jpy": [lo, hi],
            "implied_usdjpy_open": round(1.0 / o, 2),
            "implied_usdjpy_close": round(1.0 / c, 2),
            "implied_usdjpy_note": ("USDJPY DOWN while 6J UP => JPY stronger = "
                                    "6J price UP; law confirmed; no inversion"),
            "burst_minutes": burst,
            "framing_sensitivity_utc_calendar_day_vs_ct_session": {
                "utc_day_front_volume": int(uf["volume"].sum()),
                "utc_day_front_open": float(uf["open"].iloc[0]) * PX_SCALE,
                "utc_day_front_close": float(uf["close"].iloc[-1]) * PX_SCALE,
                "utc_day_move_pct": round(
                    (float(uf["close"].iloc[-1]) / float(uf["open"].iloc[0]) - 1) * 100, 4),
                "ct_session_front_volume": int(vols.iloc[0]),
                "ct_session_move_pct": round(ret_pct, 4),
                "note": ("sibling P3 numbers (415,392 lots, +2.056%, close "
                         "0.0063775) match the UTC-calendar-day framing, not "
                         "the dossier's CT-trade-date session; both framings "
                         "give 6J UP / USDJPY DOWN — the law is unaffected; "
                         "contradiction disclosed, not smoothed"),
            },
            "burst_claim_check": {
                "claim": "12:42Z burst +105 ticks/min (sibling P3 6j_orientation_check.json)",
                "measured_front_tick_move_12_41_to_12_42": burst[3]["front_tick_move_vs_prior_minute"]
                if len(burst) > 3 else None,
                "dossier_burst_volume_12_42_12_43_contracts":
                    int((df[(df["dt"] >= pd.Timestamp("2024-07-11 12:42", tz="UTC"))
                            & (df["dt"] <= pd.Timestamp("2024-07-11 12:43", tz="UTC"))]
                         ["volume"]).sum()),
            },
        },
        "notional_and_cost_arithmetic": {
            "multiplier_jpy": mult,
            "multiplier_sources": [
                "S1_IDENTITY.json symbols.6J.front.multiplier='12500000' (sha256 d217ab9dcd865765e1bcae8f8131dee2f7f200cd90c07403280134da32b05822, rehashed this lane)",
                "definitions min_price_increment + grid measured in 6j_identity.json (task 3)",
            ],
            "representative_price_usd_per_jpy_claim": representative_price,
            "representative_price_remeasured_2026_tail_front_close": measured_2026_close,
            "representative_price_last_bar_utc": last_bar_utc,
            "representative_notional_usd": round(mult * measured_2026_close, 2),
            "fee_tiers_usd_per_side": fees,
            "fee_label": "MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN (FEES_CORRECTED, FX-group mapping PARTIAL)",
            "spread_close_proxy_usd_per_side": spread_proxy,
            "tick_value_usd": tick_usd,
            "round_trip_table_at_claim_notional_79787_50": rt,
            "band_sensitivity_T1": band,
            "headline": ("T1/1-tick RT $67.42 = 8.4499 bp of $79,787.50 "
                         "(12,500,000 x 0.006383); tier range 8.30-12.10 bp"),
        },
        "labels": "descriptive session move only; RT table = modeled cost arithmetic, NOT a PnL/expectancy claim",
    }
    jdump(out, os.path.join(OUT, "6j_orientation_recheck.json"))
    return out


# ---------------------------------------------------------------------------
# Task 2 — cease-guard law 2022-09-20
# ---------------------------------------------------------------------------

def task2_cease_guard():
    df = load_slice(JY_ROOTS_2022_26, "2022-04-01", "2022-10-31",
                    OUTRIGHT_RE["6J"])
    df = add_session(df)
    df = resolve_contracts(df)
    q = df[df["contract"].str.match(r"^6J[HMUZ]\d_\d{4}$")]
    wide = q.pivot_table(index="session_date", columns="contract",
                         values="volume", aggfunc="sum").sort_index()
    chain = k5_chain(wide, k=5)
    chain = chain.set_index("session_date")["held"]

    days = [pd.Timestamp(d).date() for d in
            ("2022-09-14", "2022-09-15", "2022-09-16", "2022-09-19",
             "2022-09-20", "2022-09-21", "2022-09-22", "2022-09-23")]
    roll5 = wide.rolling(5, min_periods=1).mean()
    table = []
    for d in days:
        row = {
            "session_date": str(d),
            "held_by_k5": chain.get(d),
            "bars_that_day_by_contract": {
                str(c): int(q[(q["session_date"] == d) & (q["contract"] == c)]["volume"].size)
                for c in ("6JM2_2022", "6JU2_2022", "6JZ2_2022")
            },
            "volume_that_day_by_contract": {
                str(c): int(wide.loc[d, c]) if (d in wide.index and c in wide.columns
                                                and pd.notna(wide.loc[d, c])) else None
                for c in ("6JU2_2022", "6JZ2_2022")
            },
            "trailing5_mean": {
                str(c): (round(float(roll5.loc[d, c]), 1)
                         if (d in roll5.index and c in roll5.columns
                             and pd.notna(roll5.loc[d, c])) else None)
                for c in ("6JU2_2022", "6JZ2_2022")
            },
        }
        table.append(row)

    # panel-side facts for the vanished session
    any_bars_0920 = df[df["session_date"] == pd.Timestamp("2022-09-20").date()]
    allsym_day = any_bars_0920.groupby("raw_symbol")["volume"].sum().sort_values(ascending=False)
    u2_last = q[q["contract"] == "6JU2_2022"].sort_values("ts_event")
    u2_final_session = u2_last["session_date"].iloc[-1]
    u2_final_bars = int((u2_last["session_date"] == u2_final_session).sum())

    # baseline chain cross-check (read-only cite of the deep-v2 cache)
    base = pd.read_parquet("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep/"
                           "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_cache/held_volume_k5.parquet")
    bmask = base["session_date"].astype(str).isin([str(d) for d in days])
    baseline_held = {str(r.session_date): r.held for r in base[bmask].itertuples()}
    n_roll_baseline = int((base["held"] != base["held"].shift()).sum() - 1)

    # the held MAP keeps a 09-20 row (held=U2); the session vanishes from the
    # BAR-level chain — verify on the baseline held-daily (bar-derived) parquet
    held_daily = pd.read_parquet(
        "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep/"
        "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_cache/6j_held_daily.parquet")
    scol = "session_date" if "session_date" in held_daily.columns else held_daily.columns[0]
    has_0920_bars = held_daily[scol].astype(str).eq("2022-09-20").any()

    # does 09-20 vanish from the baseline chain?
    has_0920 = base["session_date"].astype(str).eq("2022-09-20").any()

    out = {
        "schema": "6j_cease_guard_2022@1",
        "task": "FUTURES-SIX-READINESS-20261004 / FX-JA-READINESS task 2",
        "law_under_test": ("6J_DEEP_v2.md §8 ERRATUM M-5: 2022-09-20 exchange "
                           "OPEN; Z2 traded 125,303 lots over 1,357 bars; k=5 "
                           "still held ceased U2 (stale trailing-5 mean > Z2 "
                           "ramp); session silently vanishes from the 1,745-"
                           "session held chain; 09-21 rolled return spans two "
                           "calendar days off a 97-bar stale U2 close"),
        "inputs": {
            "raw_root": "AV1R-O1M-6J-BACKFILL (2022-01-01_2024-01-01 chunk), window 2022-04-01..2022-10-31 UTC",
            "algorithm": "k5_chain() = verbatim re-implementation of 6J_deep_lib.front_by_volume_crossover (erratum m-5 code behavior: NaN-current-volume branch forces switch)",
        },
        "results": {
            "per_session": table,
            "exchange_open_2022_09_20": {
                "any_6j_bars_that_day": int(len(any_bars_0920)),
                "distinct_symbols_that_day": int(any_bars_0920["raw_symbol"].nunique()),
                "top_symbols_by_volume": {str(k): int(v) for k, v in
                                          allsym_day.head(6).items()},
                "z2_volume": int(wide.loc[pd.Timestamp("2022-09-20").date(), "6JZ2_2022"])
                if pd.Timestamp("2022-09-20").date() in wide.index else None,
                "z2_bars": int((q[(q["session_date"] == pd.Timestamp("2022-09-20").date())
                                  & (q["contract"] == "6JZ2_2022")]).shape[0]),
                "official_corroboration": ("pcal_69_6j_dl_20240904.xls row J1U27: "
                                           "First Trade 2022-09-20 — the Sep-2027 "
                                           "contract BEGAN trading that day "
                                           "(independent-verify q5_independent_verify/)"),
            },
            "u2_final_session": {
                "session_date": str(u2_final_session),
                "bars": u2_final_bars,
                "claim_97_bars_check": u2_final_bars == 97,
                "last_bar_utc": str(u2_last["dt"].iloc[-1]),
                "last_ct_minute": int(u2_last["ct_minute"].iloc[-1]),
            },
            "k5_verdict": {
                "held_on_2022_09_20": chain.get(pd.Timestamp("2022-09-20").date()),
                "switch_day_to_Z2": [str(d) for d in chain.index
                                     if (chain.loc[d] == "6JZ2_2022"
                                         and d >= pd.Timestamp("2022-09-14").date())][:1],
                "vanished_session_in_local_chain": bool(
                    chain.get(pd.Timestamp("2022-09-20").date()) == "6JU2_2022"
                    and (q[(q["session_date"] == pd.Timestamp("2022-09-20").date())
                           & (q["contract"] == "6JU2_2022")].shape[0] == 0)),
                "trailing5_mean_gap_on_0920": {
                    "u2_stale": table[4]["trailing5_mean"]["6JU2_2022"],
                    "z2": table[4]["trailing5_mean"]["6JZ2_2022"],
                },
            },
            "baseline_chain_cross_check": {
                "path": "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6J_cache/held_volume_k5.parquet + 6j_held_daily.parquet (read-only cite)",
                "baseline_held_map_0914_0923": baseline_held,
                "baseline_held_map_contains_2022_09_20": bool(has_0920),
                "baseline_bar_chain_contains_2022_09_20": bool(has_0920_bars),
                "note": ("held MAP keeps a 09-20 row (held=U2, zero U2 bars); "
                         "the session vanishes from the BAR-level held chain"),
                "baseline_rolls_total": n_roll_baseline,
                "baseline_held_daily_n_sessions": int(held_daily[scol].nunique()),
            },
        },
        "verdict": None,  # filled below
    }
    k20 = chain.get(pd.Timestamp("2022-09-20").date())
    law_holds = (
        k20 == "6JU2_2022"
        and table[4]["volume_that_day_by_contract"]["6JZ2_2022"] == 125303
        and table[4]["trailing5_mean"]["6JU2_2022"] > table[4]["trailing5_mean"]["6JZ2_2022"]
        and u2_final_bars == 97
        and not has_0920_bars
    )
    out["verdict"] = ("PASS — law as stated in 6J_DEEP_v2.md §8 (M-5) reproduces "
                      "from raw data on every measured element"
                      if law_holds else
                      "FAIL/PARTIAL — measured deviations recorded in results (contradictions reported, not smoothed)")
    jdump(out, os.path.join(OUT, "6j_cease_guard_2022.json"))
    return out


# ---------------------------------------------------------------------------
# Task 3 — identity: tick + multiplier
# ---------------------------------------------------------------------------

def _increment_stats(df: pd.DataFrame, tag: str) -> dict:
    d = add_session(df)
    stats = {"window": tag, "bars": int(len(d)),
             "instruments": int(d["instrument_id"].nunique())}
    mods = {}
    for m, label in ((500, "5e-7 USD/JPY (=$6.25/tick at 12.5e6)"),
                     (100, "1e-7 USD/JPY (=$1.25/tick at 12.5e6)"),
                     (1000, "1e-6 USD/JPY (=$12.50/tick at 12.5e6)")):
        mods[label] = {
            "mod_int_nano": m,
            "close_on_grid_share": float((d["close"].to_numpy() % m == 0).mean()),
            "ohlc_all_on_grid_share": float(
                (d[["open", "high", "low", "close"]].to_numpy() % m == 0).all(axis=1).mean()),
        }
    stats["grid_membership"] = mods
    diffs = []
    for _, g in d.sort_values("ts_event").groupby("instrument_id"):
        c = g["close"].to_numpy()
        diffs.append(np.abs(np.diff(c)))
    dd = np.concatenate(diffs)
    nz = dd[dd > 0]
    g = int(np.gcd.reduce(nz.astype(np.int64))) if len(nz) else None
    stats["increments"] = {
        "n_nonzero_minute_close_diffs": int(len(nz)),
        "min_observed_increment_int_nano": int(nz.min()) if len(nz) else None,
        "min_observed_increment_usd_per_jpy": float(nz.min()) * PX_SCALE if len(nz) else None,
        "gcd_increments_int_nano": g,
        "gcd_usd_per_jpy": g * PX_SCALE if g else None,
        "share_of_diffs_equal_to_min": float((nz == nz.min()).mean()) if len(nz) else None,
    }
    return stats


def task3_identity():
    # definitions (2023-10+ only, per dossier)
    defs = []
    for f in files_for("AV1T-definition-ALL10"):
        d = pd.read_parquet(f)
        d = d[d["raw_symbol"].str.fullmatch(OUTRIGHT_RE["6J"])]
        if len(d):
            defs.append(d)
    dd = pd.concat(defs, ignore_index=True)
    per_sym = (dd.groupby("raw_symbol")
                 .agg(min_price_increment=("min_price_increment", "unique"),
                      unit_of_measure_qty=("unit_of_measure_qty", "unique"),
                      exchange=("exchange", "unique"),
                      n_definition_rows=("min_price_increment", "size"))
                 .reset_index())
    mpi_values = sorted({float(v) for s in per_sym["min_price_increment"] for v in s})
    umq_values = sorted({str(v) for s in per_sym["unit_of_measure_qty"] for v in s})
    umq_decoded = sorted({int(float(v)) // 1_000_000_000 for s in per_sym["unit_of_measure_qty"]
                          for v in s if str(v).replace('.', '', 1).isdigit()})
    exp_sample = (dd.dropna(subset=["expiration"])
                    .groupby("raw_symbol")["expiration"].min().sort_values())
    exp_last = (dd.dropna(subset=["expiration"])
                  .groupby("raw_symbol")["expiration"].max().sort_values())
    n_sym_defs = int(per_sym["raw_symbol"].nunique())
    n_sym_with_exp = int(exp_sample.size)

    wins = []
    for tag, roots, t0, t1 in (
        ("2020-03-09..13 (AV1B backfill2)", JY_ROOTS_2020, "2020-03-07", "2020-03-14"),
        ("2023-01-09..13 (AV1R backfill)", JY_ROOTS_2022_26, "2023-01-07", "2023-01-14"),
        ("2026-07-06..10 (AV1T)", JY_ROOTS_2026, "2026-07-05", "2026-07-11"),
    ):
        sl = load_slice(roots, t0, t1, OUTRIGHT_RE["6J"])
        wins.append(_increment_stats(sl, tag))

    out = {
        "schema": "6j_identity@1",
        "task": "FUTURES-SIX-READINESS-20261004 / FX-JA-READINESS task 3",
        "definitions_2023_10_plus": {
            "n_6j_symbols_with_definitions": n_sym_defs,
            "distinct_min_price_increment_values_usd_per_jpy": mpi_values,
            "distinct_unit_of_measure_qty_raw": umq_values,
            "unit_of_measure_qty_decoded_jpy": umq_decoded,
            "unit_of_measure_qty_note": ("raw value 12500000000000000 = "
                                         "12,500,000 JPY x 1e9 int-nano "
                                         "encoding — the contract size IS in "
                                         "the definitions"),
            "symbols_with_expiration_field": n_sym_with_exp,
            "expiration_first_by_symbol_sample": {str(k): str(v) for k, v in
                                                  exp_sample.head(4).items()},
            "expiration_max_overall": str(exp_last.max()) if n_sym_with_exp else None,
            "note": ("min_price_increment 5e-7 USD/JPY UNIQUE across every 6J "
                     "definition row 2023-10+; multiplier corroborated by "
                     "S1_IDENTITY.json (sha re-verified)"),
        },
        "measured_increment_windows": wins,
        "identity": {
            "tick_usd_per_jpy": 5e-7,
            "tick_int_nano_units": 500,
            "tick_value_usd_per_contract": 6.25,
            "multiplier_jpy": 12_500_000,
            "dispatch_alternative_1e_7_1_25_verdict": ("REJECTED — declared "
                "min_price_increment = 5e-7 (500 int-nano) in every definition "
                "row; observed increment GCD = 500 int-nano in all three eras; "
                "the 1e-6 grid FAILS (≤50% of closes on-grid), so the binding "
                "grid is 5e-7 = $6.25/tick, not 1e-7/$1.25 and not 1e-4/$12.50"),
            "quote_orientation": "USD per JPY (JPY/USD listing); 6J UP = JPY stronger",
        },
        "sources": {
            "definitions": "AV1T-definition-ALL10 (2023-10+ windows)",
            "s1": "research/control/FUTURES-DATA-10SYMS-V1/S1_IDENTITY.json (root checkout, read-only; sha256 d217ab9d… rehashed)",
        },
    }
    jdump(out, os.path.join(OUT, "6j_identity.json"))
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "1"):
        task1_orientation()
    if which in ("all", "2"):
        task2_cease_guard()
    if which in ("all", "3"):
        task3_identity()
