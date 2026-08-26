"""V9 VOL-SHOCK signal family: volume-shock-conditioned continuation (A3).

Dollar volume per UTC day per symbol is aggregated from raw 15m bars
(``sum(close x volume)`` per day) either from a dependency-injected
series or, on the real data path, via :func:`load_daily_dollar_volume`
mirroring ``research.panel.load_bars_15m`` access. Everything entering a
Monday ``00:00 UTC`` cutoff decision is STRICTLY BEFORE that cutoff.

Volume shock at a cutoff (reference day = latest completed day strictly
before the cutoff):

    shock_i = dv[t_ref] / mean(dv[t_ref - 20d .. t_ref - 1d])

i.e. today-minus-1d dollar volume over the mean of the previous 20 days
EXCLUDING the reference day itself. Fewer than ``21`` usable observations
leaves the symbol ineligible.

Per-stamp universe: the TOP ``6`` symbols by shock among the traded set
(negative control ``XSECT-VOLSHK-CTRL`` / ``reverse=True`` selects the
BOTTOM-6 by shock instead), gated at ``shock >= 1.5`` -- if no selected
symbol clears the threshold the whole book is FLAT for that stamp.
Among shocked symbols with a usable trailing 3d return:

    LONG  the 2 highest 3d returns   (continuation)
    SHORT the 2 lowest 3d returns

taken disjointly from opposite ends of the deterministic
``(return, symbol asc)`` ranking. With fewer than ``2 x positions``
candidates the sides split the shocked set (long side takes the ceil
half) so a candidate can never sit on both sides. Each filled slot
carries a frozen ``+-0.20`` gross; at most ``4`` slots => ``0.80``
maximum gross, with fewer eligible symbols simply filling fewer slots.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from research.v9_ts_trend import DAY_NS

SHOCK_THRESHOLD = 1.5
DV_BASELINE_DAYS = 20
RETURN_LOOKBACK_DAYS = 3
UNIVERSE_TOP_N = 6
POSITIONS_PER_SIDE = 2
SLOT_GROSS = 0.20


def aggregate_daily_dollar_volume(
    bars: Sequence[Sequence[float]],
) -> list[tuple[int, float]]:
    """Sum ``close * volume`` per UTC day from 15m bar tuples.

    Bars are ``(ts_ns, open, high, low, close, volume)`` rows (any extra
    columns ignored); output is ``[(day_start_ns, dollar_volume)]`` sorted
    ascending with one entry per day having at least one bar.
    """
    per_day: dict[int, float] = {}
    for row in bars or []:
        ts = int(row[0])
        close = float(row[4])
        volume = float(row[5])
        if volume < 0.0:
            continue
        per_day[ts // DAY_NS] = per_day.get(ts // DAY_NS, 0.0) + close * volume
    return [(day * DAY_NS, round(dv, 12)) for day, dv in sorted(per_day.items())]


def load_daily_dollar_volume(
    catalog_path: str,
    symbol: str,
    window_start_iso: str,
    window_end_iso: str,
) -> list[tuple[int, float]]:
    """PIT-safe daily dollar-volume series read straight from the catalog.

    Mirrors the ``research.panel`` bar access (same parquet layout, same
    window bounds semantics); callers slice strictly-before-cutoff when
    scoring so loading the full panel window stays leak-free.
    """
    from research.panel import load_bars_15m

    bars = load_bars_15m(catalog_path, [symbol], window_start_iso,
                         window_end_iso).get(symbol) or []
    return aggregate_daily_dollar_volume(bars)


def _window_slice(
    series: Sequence[tuple[int, float]] | None,
    *,
    cutoff_ns: int,
) -> list[tuple[int, float]]:
    return sorted(
        (int(ts), float(v))
        for ts, v in (series or [])
        if int(ts) < int(cutoff_ns)
    )


def shock_ratios(
    *,
    dollar_volume: Mapping[str, Sequence[tuple[int, float]]],
    signal_cutoff_ns: int,
    baseline_days: int = DV_BASELINE_DAYS,
) -> dict[str, float | None]:
    """Per-symbol shock ratio at the cutoff (``None`` = insufficient history).

    Reference observation is the LATEST dollar-volume day strictly before
    the cutoff; the baseline is the mean of the ``baseline_days``
    observations immediately preceding it (reference excluded).
    """
    cutoff_ns = int(signal_cutoff_ns)
    need = int(baseline_days) + 1
    out: dict[str, float | None] = {}
    for sym in sorted(dollar_volume or {}):
        history = _window_slice(dollar_volume.get(sym), cutoff_ns=cutoff_ns)
        if len(history) < need:
            out[sym] = None
            continue
        ref_dv = history[-1][1]
        baseline = history[-need:-1]
        base_mean = sum(v for _, v in baseline) / len(baseline)
        out[sym] = None if base_mean <= 0.0 else round(ref_dv / base_mean, 12)
    return out


def three_day_returns(
    *,
    daily_closes: Mapping[str, list[tuple[int, float]]],
    signal_cutoff_ns: int,
    lookback_days: int = RETURN_LOOKBACK_DAYS,
) -> dict[str, float | None]:
    """Trailing ``lookback_days`` close-to-close returns (strictly before)."""
    from research.v9_ts_trend import trailing_return

    cutoff_ns = int(signal_cutoff_ns)
    return {
        sym: trailing_return(
            daily_closes.get(sym),
            cutoff_ns=cutoff_ns,
            lookback_days=int(lookback_days),
        )
        for sym in sorted(daily_closes or {})
    }


def select_shocked_universe(
    shocks: Mapping[str, float | None],
    *,
    universe_top_n: int = UNIVERSE_TOP_N,
    shock_threshold: float = SHOCK_THRESHOLD,
    reverse: bool = False,
) -> list[str]:
    """Top/bottom-``universe_top_n`` by shock, gated at ``shock_threshold``.

    Ranking is deterministic: shock descending (ascending under the
    bottom-N control), ties by symbol ascending at a 1e-12 rounding
    tolerance. Symbols without a usable shock never rank. Selected names
    still must clear ``>= shock_threshold`` to count as shocked.
    """
    eligible = sorted(
        (sym for sym, ratio in shocks.items() if ratio is not None),
        key=lambda s: (-round(float(shocks[s]), 12), s),
    )
    ranked = sorted(eligible, reverse=bool(reverse))
    universe = ranked[:max(0, int(universe_top_n))]
    threshold = float(shock_threshold)
    return [s for s in universe if float(shocks[s]) >= threshold]


def compute_targets(
    *,
    daily_closes: Mapping[str, list[tuple[int, float]]],
    dollar_volume: Mapping[str, Sequence[tuple[int, float]]],
    signal_cutoff_ns: int,
    traded_symbols: Sequence[str],
    shock_threshold: float = SHOCK_THRESHOLD,
    dv_baseline_days: int = DV_BASELINE_DAYS,
    return_lookback_days: int = RETURN_LOOKBACK_DAYS,
    universe_top_n: int = UNIVERSE_TOP_N,
    positions_per_side: int = POSITIONS_PER_SIDE,
    slot_gross: float = SLOT_GROSS,
    reverse: bool = False,
) -> dict:
    """VOL-SHOCK target book: {"status", "longs", "shorts"} (V9 contract).

    Universe-per-stamp = top-6-by-shock (bottom-6 under ``reverse``) among
    the traded symbols, gated at ``shock >= shock_threshold``; among the
    shocked, long the 2 highest / short the 2 lowest trailing
    ``return_lookback_days`` returns, ``+-slot_gross`` per filled slot.
    """
    symbols = sorted(dict.fromkeys(str(s) for s in traded_symbols))
    if not symbols:
        return {"status": "SKIP_INCOMPLETE",
                "reason_code": "v9_vol_shock_empty_universe"}

    cutoff_ns = int(signal_cutoff_ns)
    volumes = {
        sym: list((dollar_volume or {}).get(sym) or []) for sym in symbols
    }
    shocks = shock_ratios(
        dollar_volume=volumes,
        signal_cutoff_ns=cutoff_ns,
        baseline_days=int(dv_baseline_days),
    )
    universe = select_shocked_universe(
        {sym: shocks.get(sym) for sym in symbols},
        universe_top_n=int(universe_top_n),
        shock_threshold=float(shock_threshold),
        reverse=reverse,
    )
    if not universe:
        return {"status": "OK", "longs": [], "shorts": []}

    returns = three_day_returns(
        daily_closes=daily_closes,
        signal_cutoff_ns=cutoff_ns,
        lookback_days=int(return_lookback_days),
    )
    candidates = sorted(
        (sym for sym in universe if returns.get(sym) is not None),
        key=lambda s: (round(float(returns[s]), 12), s),
    )
    top_n = max(0, int(positions_per_side))
    n = len(candidates)
    if n >= 2 * top_n:
        long_count = short_count = top_n
    else:
        long_count = n - n // 2
        short_count = n // 2
    # Highest returns longed (ties: symbol ascending); lowest shorted from
    # the opposite end -- disjoint by construction (l_count + s_count <= n).
    longs = list(reversed(candidates))[:long_count]
    shorts = [s for s in candidates[:short_count] if s not in set(longs)]

    slot = float(slot_gross)
    longs_out = [[s, round(slot, 12)] for s in longs]
    shorts_out = [[s, round(-slot, 12)] for s in sorted(shorts)]
    return {"status": "OK", "longs": longs_out, "shorts": shorts_out}
