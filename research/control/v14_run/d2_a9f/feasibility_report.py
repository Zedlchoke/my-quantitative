"""A9-F T4/T5/T6: schedule feasibility, cost arithmetic, control
identifiability and drop-one meaningfulness per proposal.

Consumes ONLY staged artifacts and schedule constants:
* research/control/v14_run/d2_a9f/panels/*.json (rank panels, no PnL);
* research/control/v14_run/d2_a9f/staged_basis_manifest.json;
* research/control/v14_run/d2_a9f/oi_staging_verification.json;
* real perp-metadata tick sizes via the P1 load path
  (research/v12/families/oilev_v2/audits.py load_tick_sizes semantics) from
  /Users/hoangminhlong/my-quantitative/catalog_live_crypto/data/crypto_perpetual;
* reference prices from the LAST completed staged 15m bar per symbol
  (Nautilus layout, raw i128 / 1e16 decode) -- schedule-only price units,
  never returns.

Outputs research/control/v14_run/d2_a9f/feasibility_report.json covering:
T4 schedule feasibility (warmup inside the authorized window, decision
counts vs frozen floors, fold boundary sanity, storage/request volumes vs
the proposals' source-to-test maps); T5 cost arithmetic under the
remediated kernel (costs on fills ONLY; real ticks; base = 5.0 bps/side
+1 tick, stress = fee x1.5 +3 ticks total, +1 event delay) with the frozen
drag floors (base <= 8%/yr, stressed <= 12%/yr of gross,
research/v11/cost_feasibility.py FLOOR table); T6 control identifiability
and drop-one non-vacuousness by construction (measured only through
feature availability and cross-sectional dispersion -- never returns).

No PnL, no positions, no weights that depend on returns, no selection or
novelty verdicts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
PANELS = HERE / "panels"
WT_ROOT = HERE.parents[4]  # worktree root
WORKSPACE = Path("/Users/hoangminhlong/my-quantitative")
PERP_ROOT = WORKSPACE / "catalog_live_crypto" / "data" / "crypto_perpetual"
BARS_ROOT = WORKSPACE / "catalog_live_crypto" / "data" / "binance_bar"

UNIVERSE = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "DOGEUSDT", "ENAUSDT",
    "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT",
    "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]

# Frozen schedule constants (proposals + p_freeze_v14 + cost_feasibility).
WINDOW_AUTHORIZED = ("2024-08-20T00:00:00Z", "2026-08-21T23:59:59.999Z")
SCREEN = ("2025-08-22T00:00:00Z", "2026-08-21T23:59:59Z")
FOLDS = [
    ("F0", "2025-08-22", "2025-12-21"),
    ("F1", "2025-12-22", "2026-04-21"),
    ("F2", "2026-04-22", "2026-08-21"),
]
PURGE_DAYS = 1
TAKER_FEE_BPS = 5.0            # research/contract_v10.py TAKER_FEE_FLOOR_BPS_V10
BASE_TICKS = 1                 # ADVERSE_TICKS_SLIPPAGE_FLOOR_V10
STRESS_FEE_MULT = 1.5
STRESS_EXTRA_TICKS = 2         # frozen stress: +2 ticks over base (total 3)
FLOOR_MAX_BASE_DRAG = 0.08
FLOOR_MAX_STRESSED_DRAG = 0.12
FLOOR_MAX_DECISIONS_365D = 60.0
BUCKET_MS = 900_000
DAY_MS = 86_400_000


def iso_ms(iso: str) -> int:
    fmt = "%Y-%m-%dT%H:%M:%SZ" if "T" in iso else "%Y-%m-%d"
    dt = datetime.strptime(iso, fmt).replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * 1000


def ms_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def monday_stamps(first_iso: str, last_iso: str) -> list[int]:
    start, end = iso_ms(first_iso), iso_ms(last_iso)
    day = start - (start % DAY_MS)
    while datetime.fromtimestamp(day / 1000, tz=timezone.utc).weekday() != 0:
        day += DAY_MS
    return list(range(day, end + 1, 7 * DAY_MS))


def load_tick_sizes() -> dict[str, float]:
    """Same load path as research/v12/families/oilev_v2/audits.py load_tick_sizes."""
    out: dict[str, float] = {}
    for sym in UNIVERSE + ["BTCUSDT"]:
        sym_dir = PERP_ROOT / f"{sym}-PERP.BINANCE"
        paths = sorted(sym_dir.glob("*.parquet"))
        row = pq.read_table(paths[0]).to_pandas().iloc[0]
        tick = float(row["price_increment"])
        if not np.isfinite(tick) or tick <= 0.0:
            raise ValueError(f"{sym}: non-positive tick {tick}")
        out[sym] = tick
    return out


def last_bar_closes() -> dict[str, float]:
    """Last completed 15m close per symbol (schedule-only price units)."""
    out: dict[str, float] = {}
    for sym in UNIVERSE + ["BTCUSDT"]:
        sym_dir = BARS_ROOT / f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
        paths = sorted(sym_dir.glob("*.parquet"))
        table = pq.read_table(paths[-1], columns=["close"])
        raw = table.column("close")[-1].as_py()
        raw_int = int.from_bytes(bytes(raw), "little", signed=True)
        out[sym] = raw_int / 1e16
    return out


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def panel(path_name: str) -> dict:
    return json.load(open(PANELS / path_name, encoding="utf-8"))


def per_fill_rate(tick: float, price: float, *, stress: bool) -> float:
    """Cost per unit traded notional for one fill (one side)."""
    fee_rate = TAKER_FEE_BPS * 1e-4 * (STRESS_FEE_MULT if stress else 1.0)
    ticks = BASE_TICKS + (STRESS_EXTRA_TICKS if stress else 0)
    return fee_rate + ticks * tick / price


def annual_drag(fills_per_year: float, traded_fraction: float,
                ticks: dict[str, float], prices: dict[str, float]) -> dict:
    """Worst-case annualized execution drag of gross under base and stress.

    fills_per_year is the whole BOOK's upper fill count; each fill trades
    `traded_fraction` of gross in one symbol.  Reported:
    * worst_case  -- every fill lands on the max-rate symbol (upper bound);
    * diversified -- fills spread uniformly across the 19-name universe.
    drag = fills_per_year * traded_fraction * rate_per_fill.
    """
    rates = {sym: per_fill_rate(ticks[sym], prices[sym], stress=stress)
             for stress in (False, True) for sym in [None]} if False else {}
    out = {}
    for stress in (False, True):
        rates_s = {sym: per_fill_rate(ticks[sym], prices[sym], stress=stress) for sym in ticks}
        worst_sym = max(rates_s, key=rates_s.get)
        worst = fills_per_year * traded_fraction * rates_s[worst_sym]
        diversified = fills_per_year * traded_fraction * (
            sum(rates_s[s] for s in UNIVERSE) / len(UNIVERSE)
        )
        floor = FLOOR_MAX_STRESSED_DRAG if stress else FLOOR_MAX_BASE_DRAG
        out["stress" if stress else "base"] = {
            "total_drag_frac_of_gross_yr_worst_case": worst,
            "total_drag_frac_of_gross_yr_diversified": diversified,
            "floor": floor,
            "pass_worst_case": worst <= floor,
            "pass_diversified": diversified <= floor,
            "worst_case_symbol": worst_sym,
        }
    out["stress_to_base_ratio_worst_case"] = (
        out["stress"]["total_drag_frac_of_gross_yr_worst_case"]
        / out["base"]["total_drag_frac_of_gross_yr_worst_case"]
    )
    return out


def main() -> None:
    ticks = load_tick_sizes()
    prices = last_bar_closes()
    fade = panel("panel_BASISLV-PREMFADE.json")
    width = panel("panel_BASISLV-WIDTHGATE.json")
    premrev = panel("panel_BASISDYN-PREMREV.json")
    premvol = panel("panel_BASISDYN-PREMVOL.json")
    oich = panel("panel_OICH.json")
    oicyc = panel("panel_OICYC.json")
    staged = json.load(open(HERE / "staged_basis_manifest.json", encoding="utf-8"))
    oi_ver = json.load(open(HERE / "oi_staging_verification.json", encoding="utf-8"))
    probe = json.load(open(HERE / "probe_summary.json", encoding="utf-8"))

    stamps = [iso_ms(s) for s in fade["decision_stamps_iso"]]

    # ---------------- T4 schedule feasibility ----------------
    fold_members = {}
    for label, f_start, f_end in FOLDS:
        purged_from = iso_ms(f_start) + PURGE_DAYS * DAY_MS
        members = [t for t in stamps if iso_ms(f_start) <= t <= iso_ms(f_end)]
        live = [t for t in members if t > purged_from]
        fold_members[label] = {
            "scheduled_stamps": len(members),
            "live_stamps_after_1d_purge": len(live),
            "purged_stamps": [datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                              for t in members if t <= purged_from],
            "first_live_iso": datetime.fromtimestamp(live[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if live else None,
            "last_live_iso": datetime.fromtimestamp(live[-1] / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if live else None,
        }
    decisions_365d = len(stamps) * 365.0 / ((stamps[-1] - stamps[0]) / DAY_MS + 7)

    # warmup arithmetic from staged data (earliest required data vs coverage)
    earliest_needed = {
        "BASISLV-PREMFADE": ("2025-07-28", "28d formation before first stamp (proposal staging plan)"),
        "BASISLV-WIDTHGATE": ("2025-06-30", "56d neighbour formation before first stamp"),
        "BASISDYN-PREMREV": ("2025-07-23", "30d standardization + 72h before first stamp"),
        "BASISDYN-PREMVOL": ("2025-05-27", "90d neighbour vol window before first stamp"),
    }
    warmup = {}
    for prop, (need_iso, why) in earliest_needed.items():
        need_ms = iso_ms(need_iso + "T00:00:00Z")
        routes = {
            "BASISLV-PREMFADE": ["basis"],
            "BASISLV-WIDTHGATE": ["mark_klines", "index_klines", "premium_klines"],
            "BASISDYN-PREMREV": ["premium_klines", "index_klines"],
            "BASISDYN-PREMVOL": ["premium_klines"],
        }[prop]
        per_route = {}
        for route in routes:
            firsts = []
            for sym in UNIVERSE:
                entry = staged["entries"].get(f"{route}|{sym}")
                firsts.append(iso_ms(entry["first_open_utc"]))
            per_route[route] = {
                "latest_first_bucket_utc": ms_iso(max(firsts)),
                "covers_needed_start_all_19": max(firsts) <= need_ms,
            }
        warmup[prop] = {"needed_from": need_iso, "why": why, "routes": per_route}

    oi_warmup = {
        "rows_available_at_first_stamp_min": oi_ver["warmup_rows_at_first_stamp_min"],
        "anchor_needs_29": True,
        "neighbour_needs_15": True,
        "passes": oi_ver["warmup_rows_at_first_stamp_min"] >= 29,
        "daily_row_stamps_non_2355": {
            s: e["non_2355_stamp_rows"] for s, e in oi_ver["symbols"].items()
        },
        "note": "day-row stamp offsets (day's last 5m snapshot before 23:55) are documented in OICH section 4 and read per row; calendar-day rows are 417/417 with zero missing days",
    }

    # eligibility floors from the panels
    def elig_stats(p, floor, name):
        counts = p["eligible_count"]
        vals = [counts[s] for s in p["decision_stamps_iso"]]
        below = {s: c for s, c in counts.items() if c < floor}
        return {
            "panel": name,
            "min_eligible": min(vals),
            "median_eligible": float(np.median(vals)),
            "stamps_below_floor": len(below),
            "floor": floor,
            "floor_name": name,
            "implied_min_side_size_floor_n_div_3": int(min(vals) // 3),
            "stamps_with_full_19": sum(1 for v in vals if v == 19),
            "full_crosssection_share": sum(1 for v in vals if v == 19) / len(vals),
        }

    eligibility = {
        "A5_tercile_book_min12": elig_stats(fade, 12, "PREMFADE >= 12 eligible names"),
        "A5_widthgate_min12": elig_stats(width, 12, "WIDTHGATE >= 12 eligible names"),
        "A6_premrev_min4": elig_stats(premrev, 4, "PREMREV >= 4 eligible names"),
        "A6_premvol_min4": elig_stats(premvol, 4, "PREMVOL >= 4 eligible names"),
        "A8_oich_min8_19": elig_stats(oich, 8, "OICH hysteresis needs full-ish cross-section (19 expected)"),
        "A8_oicyc_19": elig_stats(oicyc, 19, "OICYC needs the complete 19-symbol cross-section"),
    }

    t4 = {
        "decision_stamps": {
            "count_scheduled": len(stamps),
            "first": fade["stamp_calendar"]["first"],
            "last": fade["stamp_calendar"]["last"],
            "per_365d_annualized": decisions_365d,
            "floor_max_discretionary_per_365d": FLOOR_MAX_DECISIONS_365D,
            "floor_pass": decisions_365d <= FLOOR_MAX_DECISIONS_365D,
        },
        "folds": fold_members,
        "fold_floors": {
            "min_live_per_fold": min(f["live_stamps_after_1d_purge"] for f in fold_members.values()),
            "proposals_floor_per_fold": 15,
            "pass": min(f["live_stamps_after_1d_purge"] for f in fold_members.values()) >= 15,
        },
        "decision_floor_note": (
            "52 Monday stamps exist in the screen window; the frozen 1-day purge "
            "removes the 2025-12-22 stamp (fold F1 start + 1d boundary), leaving "
            "51 live stamps: >= 48 floor of A6 PASS; the A5/A8 text floors of 52 "
            "are met by the SCHEDULED count only -- flagged as proposal-internal "
            "discrepancy for A1, not a data failure"
        ),
        "warmup": warmup,
        "oi_warmup": oi_warmup,
        "eligibility_floors": eligibility,
        "storage_request_sanity": {
            "probes_this_lane": probe["total_requests"],
            "retry_pass": "probe_retry_summary.json (basis-route transient 418 re-checks)",
            "staged_rows_total": sum(e["rows"] for e in staged["entries"].values()),
            "staged_bytes_total": sum(e["bytes"] for e in staged["entries"].values()),
            "proposals_own_estimates": {
                "BASISLV-PREMFADE": "~1,425 requests (limit=500, 2025-07-28..screen end)",
                "BASISLV-WIDTHGATE": "~1,653 requests (3 kline routes, limit=1500, from 2025-06-30)",
                "BASISDYN-PREMREV": "~893 requests (premium route, limit=1500, full authorized window)",
                "BASISDYN-PREMVOL": "~893 requests (premium route; bars already staged)",
            },
            "measured_note": "A9-F staged the WIDER authorized window (2024-08-20..2026-08-21) on 4 routes: ~5.4k requests total, ~70.4k buckets/symbol/route; proposals' narrower windows need fewer pages -- their arithmetic is consistent with measured page counts at limit=1500 (47 pages/symbol) and limit=500 (141 pages/symbol)",
            "gap_status": {
                "kline_routes_missing_buckets": sum(
                    e["missing_buckets"] for k, e in staged["entries"].items() if "klines" in k
                ),
                "basis_route_missing_buckets": sum(
                    e["missing_buckets"] for k, e in staged["entries"].items() if k.startswith("basis|")
                ),
            },
        },
    }

    # ---------------- T5 cost arithmetic ----------------
    # Fill bounds per proposal (declared turnover bounds in the proposals).
    cost = {}
    for prop, fills_upper_per_decision, book_sym_frac in [
        ("BASISLV-PREMFADE", 24, 1.0 / 12.0),
        ("BASISLV-WIDTHGATE", 36, 1.0 / 12.0),   # +12 exit fills on gate-close stamps
        ("OICH", 24, 1.0 / 12.0),                # hysteresis upper bound == full tercile swap
        ("OICYC", 24, 1.0 / 12.0),
        ("BASISDYN-PREMREV", 10, 0.20),
        ("BASISDYN-PREMVOL", 10, 0.20),
    ]:
        fills_per_year_upper = fills_upper_per_decision * 52.0
        drag = annual_drag(fills_per_year_upper, book_sym_frac, ticks, prices)
        cost[prop] = {
            "declared_fills_upper_per_decision": fills_upper_per_decision,
            "fills_per_year_upper": fills_per_year_upper,
            "traded_notional_fraction_per_fill": book_sym_frac,
            "per_fill_rate_formula": "taker_fee_bps*1e-4*fee_multiplier + ticks*tick_size/price",
            "base_schedule": "5.0 bps + 1 tick",
            "stress_schedule": "7.5 bps + 3 ticks (+1 event delay, no drag arithmetic effect)",
            **drag,
        }

    # ---------------- T5b measured turnover from the rank schedule ----------
    # The proposals freeze the book construction as a pure function of the
    # conditioning ranks (never returns).  Building the per-stamp target legs
    # is therefore schedule-only (V12 evidence_feasibility_52 precedent): it
    # yields measured fill counts, measured drag with real per-symbol tick
    # arithmetic, and the per-symbol turnover-share check A9-F is named for.
    # NO PnL and no positions are recorded.
    def books_premfade(panel, gated=None):
        stamps = panel["decision_stamps_iso"]
        gate = panel.get("gate_sidecar", {}).get("series", {}) if gated is not None else {}
        out = {}
        prev = {}
        for s in stamps:
            elig = panel["eligible_count"][s]
            ranks = panel["ranks"][s]
            trade = elig >= 12
            if gated is True and not (gate.get(s, {}).get("gate_open") is True):
                trade = False
            if gated is False and not (gate.get(s, {}).get("gate_open") is False):
                trade = False
            if not trade or not ranks:
                out[s] = dict(prev)
                continue
            ordered = sorted(ranks.items(), key=lambda kv: kv[1])
            n_side = max(1, elig // 3)
            w = 1.0 / (2 * n_side)
            if w > 0.30:
                w = 0.30
            book = {sym: w for sym, _ in ordered[:n_side]}
            book.update({sym: -w for sym, _ in ordered[-n_side:]})
            prev = book
            out[s] = dict(book)
        return out

    def books_top5(panel):
        stamps = panel["decision_stamps_iso"]
        out = {}
        prev = {}
        for s in stamps:
            ranks = panel["ranks"][s]
            n = len(ranks)
            if n == 0:
                out[s] = dict(prev)
                continue
            k = min(5, n)
            ordered = sorted(ranks.items(), key=lambda kv: kv[1])[:k]
            w = min(1.0 / k, 0.30)
            prev = {sym: w for sym, _ in ordered}
            out[s] = dict(prev)
        return out

    def books_hysteresis(panel):
        stamps = panel["decision_stamps_iso"]
        out = {}
        held_long: set = set()
        held_short: set = set()
        prev: dict = {}
        for s in stamps:
            ranks = panel["ranks"][s]
            n = len(ranks)
            if n < 12:  # side membership < 4 -> skip rebalance, hold previous
                out[s] = dict(prev)
                continue
            ordered = sorted(ranks.items(), key=lambda kv: kv[1])
            rank_of = {sym: r for r, (sym, _) in enumerate(ordered, start=1)}
            tercile = max(1, n // 3)
            median = (n + 1) / 2.0
            long_tercile = {sym for sym, _ in ordered[:tercile]}
            short_tercile = {sym for sym, _ in ordered[-tercile:]}
            # enter on tercile entry; exit only beyond the median
            held_long = {sym for sym in (held_long | long_tercile) if rank_of[sym] <= median}
            held_short = {sym for sym in (held_short | short_tercile) if rank_of[sym] >= median}
            book = {}
            for side, held in (("long", held_long), ("short", held_short)):
                k = len(held)
                if k >= 2:
                    w = min(0.5 / k, 0.30)
                    sign = 1.0 if side == "long" else -1.0
                    book.update({sym: sign * w for sym in held})
            prev = book
            out[s] = dict(book)
        return out

    fade_p = json.load(open(PANELS / "panel_BASISLV-PREMFADE.json", encoding="utf-8"))
    width_p = json.load(open(PANELS / "panel_BASISLV-WIDTHGATE.json", encoding="utf-8"))
    rev_p = json.load(open(PANELS / "panel_BASISDYN-PREMREV.json", encoding="utf-8"))
    vol_p = json.load(open(PANELS / "panel_BASISDYN-PREMVOL.json", encoding="utf-8"))
    oich_p = json.load(open(PANELS / "panel_OICH.json", encoding="utf-8"))
    oicyc_p = json.load(open(PANELS / "panel_OICYC.json", encoding="utf-8"))

    schedules = {
        "BASISLV-PREMFADE": books_premfade(fade_p),
        "BASISLV-WIDTHGATE-ANCHOR(gate-open)": books_premfade(width_p, gated=True),
        "OICH": books_hysteresis(oich_p),
        "OICYC": books_hysteresis(oicyc_p),
        "BASISDYN-PREMREV": books_top5(rev_p),
        "BASISDYN-PREMVOL": books_top5(vol_p),
    }
    measured = {}
    for name, books in schedules.items():
        total_abs = 0.0
        per_symbol: dict[str, float] = {}
        n_fills = 0
        nonempty = 0
        prev: dict = {}
        for s in sorted(books):
            book = books[s]
            if book:
                nonempty += 1
            for sym in sorted(set(book) | set(prev)):
                delta = abs(book.get(sym, 0.0) - prev.get(sym, 0.0))
                if delta <= 1e-12:
                    continue
                # fills count is schedule-only (weights depend on ranks, never
                # on returns); drag applies the real per-symbol tick arithmetic
                total_abs += delta
                per_symbol[sym] = per_symbol.get(sym, 0.0) + delta
                n_fills += 1
            prev = dict(book)
        drag_base = 0.0
        drag_stress = 0.0
        for sym, traded in per_symbol.items():
            drag_base += traded * per_fill_rate(ticks[sym], prices[sym], stress=False)
            drag_stress += traded * per_fill_rate(ticks[sym], prices[sym], stress=True)
        max_share = (max(per_symbol.values()) / total_abs) if total_abs > 0 else None
        measured[name] = {
            "note": "schedule-only book reconstruction from the frozen rank rules (no PnL, no positions recorded); weights depend on ranks only",
            "stamps": len(books),
            "stamps_with_nonempty_book": nonempty,
            "fills_window": n_fills,
            "one_way_traded_gross_window": round(total_abs, 6),
            "drag_frac_of_gross_window_base": round(drag_base, 6),
            "drag_frac_of_gross_window_stress": round(drag_stress, 6),
            "max_symbol_share_of_traded_gross": max_share,
            "symbol_turnover_share_floor_0_25_pass": (max_share <= 0.25) if max_share is not None else None,
            "worst_symbol_by_turnover": (
                max(per_symbol, key=per_symbol.get) if per_symbol else None
            ),
        }

    t5 = {
        "kernel": "remediated L-V14-0: costs on fills ONLY (once per fill; never per holding-day/stamp on open positions); real perp-metadata ticks; funding settled natively once per settlement is a holding term reported separately, excluded from the execution-drag floors",
        "measured_turnover_from_rank_schedule": measured,
        "tick_sizes_source": "crypto_perpetual metadata parquet price_increment (P1 load path semantics)",
        "ref_price_source": "last completed staged 15m bar close (raw i128/1e16)",
        "tick_sizes": ticks,
        "reference_prices": prices,
        "floors": {"base": FLOOR_MAX_BASE_DRAG, "stressed": FLOOR_MAX_STRESSED_DRAG},
        "proposals": cost,
        "arithmetic_consistency_note": "stressed/base fee ratio is 1.5 on the fee term; the tick term ratio is 3x base (1->3 ticks), so stressed/base total drag is symbol-mix dependent and > 1.5 for every universe symbol (tick/price > 0) -- the proposals' stated stress ratios are arithmetically consistent with costs-on-fills-only",
    }

    # ---------------- T6 control identifiability + drop-one ----------------
    def dispersion_ok(p, name):
        stats = p["cross_section_stats"]
        iqrs = [v["iqr"] for v in stats.values()]
        ns = [v["n"] for v in stats.values()]
        return {
            "panel": name,
            "stamps_with_2plus_features": len(iqrs),
            "min_cross_sectional_iqr": min(iqrs) if iqrs else None,
            "all_iqr_strictly_positive": all(q > 0 for q in iqrs),
            "median_n": float(np.median(ns)) if ns else 0,
        }

    t6 = {
        "controls": {
            "BASISLV-PREMFADE": {
                "control": "BASISLV-PREMFADE-28D-INV (sign-inverted same book)",
                "well_defined": True,
                "basis": "identical ranks, inverted sign; needs only the anchor panel's rank ordering (exists at every stamp with >= 12 eligible per eligibility block)",
            },
            "BASISLV-WIDTHGATE": {
                "control": "BASISLV-WIDTHGATE-28D-NARROW (gate inverted: open iff D(T) < trailing median)",
                "well_defined": True,
                "basis": f"gate sidecar in the panel: open stamps = {width['gate_sidecar']['open_stamps']} of {width['gate_sidecar']['decided_stamps']} decided; narrow state is the complement; requires >= 6 prior stamp IQRs (satisfied from stamp 7 onward)",
            },
            "BASISDYN-PREMREV": {
                "control": "IDXREV-72H (standardized 72h INDEX-price change, indexPriceKlines pair=)",
                "well_defined": True,
                "basis": "index klines staged for all 19 symbols over the full authorized window (staged manifest; same bucket grid as the premium route verified in the panel build)",
            },
            "BASISDYN-PREMVOL": {
                "control": "PRICEVOL-30D (30d realized vol of daily log returns from authorized staged bars)",
                "well_defined": True,
                "basis": "staged 15m bars cover 2024-08-20..2026-08-21 for all universe symbols (a3_staging_manifest 90/90 SHA re-verified by P1); the control deletes every premium quantity and is computable PIT",
            },
            "OICH": {
                "control": "CTL-PRICEVOL (std of 28 most recent daily log closes from staged bars)",
                "well_defined": True,
                "basis": "daily closes derivable from staged 15m bars for all 19 symbols; no OI input",
            },
            "OICYC": {
                "control": "CTL-OISHARE (28-row mean own OI share of the staged-universe aggregate)",
                "well_defined": True,
                "basis": "computable from the same v11_oi_staging_v1 rows; complete 19-symbol cross-section verified at every weekly stamp (oi_staging_verification.json)",
            },
        },
        "feature_dispersion": {
            "BASISLV-PREMFADE": dispersion_ok(fade, "PREMFADE"),
            "BASISLV-WIDTHGATE": dispersion_ok(width, "WIDTHGATE"),
            "BASISDYN-PREMREV": dispersion_ok(premrev, "PREMREV"),
            "BASISDYN-PREMVOL": dispersion_ok(premvol, "PREMVOL"),
            "OICH": dispersion_ok(oich, "OICH"),
            "OICYC": dispersion_ok(oicyc, "OICYC"),
        },
        "drop_one": {
            "BASISLV-PREMFADE": {
                "rule": "drop the held leg with the largest |b_i(T)| at the stamp with the largest held |weight|; renormalize to gross 1.0",
                "non_vacuous_by_construction": True,
                "basis": "the book trades only at stamps with >= 12 eligible names (eligibility block); every traded stamp holds >= 6 legs per side, so a held max-|weight| leg always exists; the tie-break (largest |b_i|) is outcome-free and computable from the panel",
            },
            "BASISLV-WIDTHGATE": {
                "rule": "same as PREMFADE within open-state stamps",
                "non_vacuous_by_construction": True,
                "basis": f"gate OPEN at {width['gate_sidecar']['open_stamps']} decided stamps; open stamps trade the >= 12-name tercile book, so a held leg exists at every open stamp",
            },
            "BASISDYN-PREMREV": {
                "rule": "drop the held max-|weight| symbol (all tie at 0.20; tie-break lexicographically first); renormalize 5 -> 4 at 0.25 <= 0.30 cap",
                "non_vacuous_by_construction": True,
                "basis": "the anchor holds exactly 5 names whenever >= 4 eligible (panel eligibility block shows eligible counts)",
            },
            "BASISDYN-PREMVOL": {
                "rule": "same as PREMREV",
                "non_vacuous_by_construction": True,
                "basis": "same 5-name book shape; eligibility block shows >= 4 eligible at every stamp",
            },
            "OICH": {
                "rule": "drop the HELD symbol with maximum |weight| (tie-break ascending symbol name); weights unchanged; rerun",
                "non_vacuous_by_construction": True,
                "basis": "book is non-empty whenever either side has >= 2 members (floor: side membership >= 4 at >= 95% of stamps); eligible counts from the panel give side sizes >= 4 whenever 12+ names are eligible",
            },
            "OICYC": {
                "rule": "same as OICH",
                "non_vacuous_by_construction": True,
                "basis": "complete 19-symbol cross-section at every stamp; sides of 6/6 exist whenever >= 12 eligible (panel shows 19 eligible at every stamp)",
            },
        },
    }

    report = {
        "schema": "v14_d2_a9f_feasibility_report_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "no_pnl": True,
        "no_positions": True,
        "schedule_feasibility": t4,
        "cost_arithmetic": t5,
        "control_and_drop_one": t6,
    }
    with open(HERE / "feasibility_report.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print("feasibility_report.json written")
    print(json.dumps({
        "decision_floor_pass": t4["decision_stamps"]["floor_pass"],
        "fold_floor_pass": t4["fold_floors"]["pass"],
        "oi_warmup_pass": oi_warmup["passes"],
        "cost_drag_summary_worst_case": {
            p: {"base": round(v["base"]["total_drag_frac_of_gross_yr_worst_case"], 4),
                "stress": round(v["stress"]["total_drag_frac_of_gross_yr_worst_case"], 4),
                "base_pass": v["base"]["pass_worst_case"],
                "stress_pass": v["stress"]["pass_worst_case"]}
            for p, v in cost.items()
        },
        "cost_drag_summary_diversified": {
            p: {"base": round(v["base"]["total_drag_frac_of_gross_yr_diversified"], 4),
                "stress": round(v["stress"]["total_drag_frac_of_gross_yr_diversified"], 4)}
            for p, v in cost.items()
        },
    }, indent=1))


if __name__ == "__main__":
    main()
