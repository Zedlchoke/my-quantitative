"""Artifact builders for the A8-V11-ILLIQ-AMIHUD implementation lane.

Three schedule/diagnostic-only artifacts (NEVER a scored result):

* C1 field verification  -> ``research/audits/v11i/illiq_amihud_c1_fields.json``
  (close + quote_volume coverage per staged symbol incl. sparse-volume
  symbols, funding cadence, tick sizes, PIT clock statement);
* A3 cost gate           -> ``research/audits/v11i/illiq_amihud_a3_gate.json``
  (schedule-only feasibility via the frozen
  :func:`research.v11.cost_feasibility.evaluate_schedule_cost_feasibility`);
* A4 exact-arm dry-run   -> ``research/audits/v11i/illiq_amihud_a4_dryrun.json``
  (the three frozen arms through the REAL adapter path on a SYNTHETIC frame:
  distinct identities, dummy-metrics publish + zero-delta replay into a
  namespaced temporary ledger; no real PnL anywhere).

All catalog/funding reads are READ-ONLY against the staged snapshot.
"""

from __future__ import annotations

import hashlib
import json
import math
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from research.adapter_v10.protocol import SettlementPoint, StrategyIdentity
from research.hyp_a8_m01 import read_bars_15m
from research.v11.cost_feasibility import (
    ScheduleArtifacts,
    ScheduleDecision,
    SignalAvailability,
    evaluate_schedule_cost_feasibility,
)
from research.v11.exact_arm_dryrun import run_exact_arm_dryrun
from research.v11.families.illiq_amihud.plugin import IlliqAmihudPlugin
from research.v11.families.illiq_amihud.strategy import (
    BENCHMARK_SYMBOL_EXCLUDED,
    DAY_NS,
    DECISION_CLOCK_TEXT,
    EXECUTION_LAG_DAYS,
    FAMILY_ID,
    FOLDS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    frozen_arm_config_digest,
    frozen_arm_ids,
    iso_date_ns,
)
from research.v11.publication_identity import trial_key_v2

PRODUCER_ROLE = "I-family-2"
SCHEMA_C1 = "v11i.illiq_amihud.c1_fields.v1"
SCHEMA_A3 = "v11i.illiq_amihud.a3_gate.v1"
SCHEMA_A4 = "v11i.illiq_amihud.a4_dryrun.v1"

CATALOG_PATH = "/Users/hoangminhlong/my-quantitative/catalog_live_crypto"
FUNDING_ROOT = "/Users/hoangminhlong/my-quantitative/funding_data/scan_2026"
#: Warmup starts early enough for the 90d beta + 56d formation at the first stamp.
PREWINDOW_START_ISO = "2025-04-01T00:00:00Z"
STAGED_SYMBOLS: Tuple[str, ...] = (
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
)

PIT_CLOCK_STATEMENT = (
    "Features are computed ONLY from completed 15m bars whose exchange CLOSE "
    "stamp (ts_event) is at or before the Monday 00:00:00Z decision stamp; "
    "daily UTC blocks are (D-k*1d, D-(k-1)*1d] by close stamp; the frozen 90d "
    "daily beta uses only completed daily blocks strictly before the stamp; "
    "execution fills at the first bar whose open instant covers "
    "decision + 24h declared lag (strictly after feature availability); "
    "native funding rows enter only via publish_ts_ns inside held spans "
    "(start, end]. No future bar, funding row or universe fact enters any "
    "decision; the tradeable universe is the fixed staged cohort minus the "
    "context-only BTCUSDT benchmark (no future universe selection)."
)


# --------------------------------------------------------------------------- #
# Staged-data readers (READ-ONLY)
# --------------------------------------------------------------------------- #
def load_staged_bars(
    *,
    catalog_path: str = CATALOG_PATH,
    symbols: Sequence[str] = STAGED_SYMBOLS,
    start_iso: str = PREWINDOW_START_ISO,
    end_iso: str = WINDOW_END_ISO,
) -> Dict[str, Tuple[Any, ...]]:
    return {
        str(sym): read_bars_15m(catalog_path, str(sym), start_iso, end_iso)
        for sym in symbols
    }


def load_funding_settlements(
    *,
    funding_root: str = FUNDING_ROOT,
    symbols: Sequence[str] = STAGED_SYMBOLS,
    end_ns: Optional[int] = None,
) -> Dict[str, Tuple[SettlementPoint, ...]]:
    """Native funding rows -> SettlementPoints (publish_ts = fundingTime)."""
    limit = int(end_ns) if end_ns is not None else parse_window_end_ns()
    out: Dict[str, Tuple[SettlementPoint, ...]] = {}
    for sym in symbols:
        path = Path(funding_root) / str(sym) / "funding.json"
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        rows = doc.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"funding bundle for {sym} has no rows")
        points = []
        for row in rows:
            publish_ts_ns = int(row["fundingTime"]) * 1_000_000
            if publish_ts_ns > limit:
                continue
            points.append(
                SettlementPoint(
                    publish_ts_ns=publish_ts_ns,
                    value=float(row["fundingRate"]),
                    kind="info",
                )
            )
        points.sort(key=lambda p: p.publish_ts_ns)
        out[str(sym)] = tuple(points)
    return out


def load_tick_sizes(
    *,
    catalog_path: str = CATALOG_PATH,
    symbols: Sequence[str] = STAGED_SYMBOLS,
) -> Dict[str, float]:
    """Frozen instrument tick sizes (price_increment) from the staged defs."""
    import pyarrow.parquet as pq

    out: Dict[str, float] = {}
    for sym in symbols:
        directory = Path(catalog_path) / "data" / "crypto_perpetual" / f"{sym}-PERP.BINANCE"
        files = sorted(directory.rglob("*.parquet"))
        if not files:
            raise ValueError(f"no instrument definition for {sym}")
        table = pq.read_table(files[0], columns=["price_increment"])
        raw = table.column("price_increment")[0].as_py()
        tick = float(str(raw))
        if not math.isfinite(tick) or tick <= 0.0:
            raise ValueError(f"non-positive tick size for {sym}")
        out[str(sym)] = tick
    return out


def parse_window_end_ns() -> int:
    from research.v11.families.illiq_amihud.strategy import parse_iso_utc_ns

    return parse_iso_utc_ns(WINDOW_END_ISO)


# --------------------------------------------------------------------------- #
# C1 field verification
# --------------------------------------------------------------------------- #
def _slot_coverage(bars: Sequence[Any]) -> Dict[str, Any]:
    """15m slot coverage between the first and last bar close stamp."""
    if not bars:
        return {
            "first_close_ns": None,
            "last_close_ns": None,
            "n_bars": 0,
            "slot_coverage_fraction": None,
            "missing_15m_slots": None,
        }
    first = min(int(b.ts_event_ns) for b in bars)
    last = max(int(b.ts_event_ns) for b in bars)
    n_slots = (last - first) // (15 * 60 * 1_000_000_000) + 1
    missing = n_slots - len(set(int(b.ts_event_ns) for b in bars))
    return {
        "first_close_ns": first,
        "last_close_ns": last,
        "n_bars": len(bars),
        "slot_coverage_fraction": round(len(bars) / n_slots, 9),
        "missing_15m_slots": int(missing),
    }


def _daily_volume_stats(bars: Sequence[Any]) -> Dict[str, Any]:
    """Daily UTC dollar-volume blocks over the staged range (sparse-volume scan).

    Sparse = a zero-volume day or a volume-collapse day (daily dollar volume
    below 1% of the symbol's own median) -- absolute, not a relative decile.
    """
    per_day: Dict[int, float] = {}
    for bar in bars:
        day = (int(bar.ts_event_ns) // DAY_NS) * DAY_NS
        per_day[day] = per_day.get(day, 0.0) + float(bar.quote_volume)
    days = sorted(per_day)
    volumes = [per_day[d] for d in days]
    volumes_sorted = sorted(volumes)
    median_dv = volumes_sorted[len(volumes_sorted) // 2] if volumes_sorted else 0.0
    zero_days = [d for d in days if per_day[d] <= 0.0]
    collapse_cut = 0.01 * median_dv
    collapse_days = [d for d in days if 0.0 < per_day[d] < collapse_cut]
    return {
        "n_daily_blocks": len(days),
        "n_zero_volume_days": len(zero_days),
        "zero_volume_day_starts_ns": zero_days[:20],
        "n_volume_collapse_days_below_1pct_of_median": len(collapse_days),
        "volume_collapse_day_starts_ns": collapse_days[:20],
        "median_daily_dollar_volume": median_dv,
        "min_daily_dollar_volume": volumes_sorted[0] if volumes_sorted else 0.0,
    }


def build_c1_audit() -> Dict[str, Any]:
    """C1 field verification over the staged snapshot (close + quote_volume)."""
    bars = load_staged_bars()
    funding = load_funding_settlements()
    ticks = load_tick_sizes()
    per_symbol: Dict[str, Any] = {}
    for sym in STAGED_SYMBOLS:
        symbol_bars = bars[sym]
        coverage = _slot_coverage(symbol_bars)
        volumes = _daily_volume_stats(symbol_bars)
        settlements = funding[sym]
        required_fields = {
            "close": all(
                float(b.close) > 0.0 and math.isfinite(float(b.close))
                for b in symbol_bars
            ),
            "quote_volume": all(
                math.isfinite(float(b.quote_volume)) for b in symbol_bars
            ),
        }
        per_symbol[sym] = {
            "role": (
                "context_only_benchmark"
                if sym == BENCHMARK_SYMBOL_EXCLUDED
                else "tradeable_candidate"
            ),
            "bar_fields_present": {
                "close": True,
                "quote_volume": True,
                "ts_event": True,
            },
            "required_field_values_valid": required_fields,
            **coverage,
            "daily_volume": volumes,
            "tick_size": ticks[sym],
            "funding": {
                "n_settlements": len(settlements),
                "first_publish_ts_ns": (
                    settlements[0].publish_ts_ns if settlements else None
                ),
                "last_publish_ts_ns": (
                    settlements[-1].publish_ts_ns if settlements else None
                ),
            },
        }
    usable = {
        sym: (
            stats["required_field_values_valid"]["close"]
            and stats["required_field_values_valid"]["quote_volume"]
            and stats["n_bars"] > 0
        )
        for sym, stats in per_symbol.items()
    }
    return {
        "schema_version": SCHEMA_C1,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "catalog_path": CATALOG_PATH,
        "funding_root": FUNDING_ROOT,
        "prewindow_start_iso": PREWINDOW_START_ISO,
        "window_start_iso": WINDOW_START_ISO,
        "window_end_iso": WINDOW_END_ISO,
        "n_staged_symbols": len(STAGED_SYMBOLS),
        "benchmark_symbol_excluded": BENCHMARK_SYMBOL_EXCLUDED,
        "per_symbol": per_symbol,
        "symbols_with_required_fields": sorted(s for s, ok in usable.items() if ok),
        "symbols_missing_required_fields": sorted(
            s for s, ok in usable.items() if not ok
        ),
        "sparse_volume_symbols": sorted(
            sym
            for sym in STAGED_SYMBOLS
            if per_symbol[sym]["daily_volume"]["n_volume_collapse_days_below_1pct_of_median"] > 0
            or per_symbol[sym]["daily_volume"]["n_zero_volume_days"] > 0
        ),
        "folds": [
            {"id": label, "start": start, "end": end}
            for label, start, end in FOLDS
        ],
        "decision_clock": DECISION_CLOCK_TEXT,
        "declared_execution_lag_days": EXECUTION_LAG_DAYS,
        "pit_clock_statement": PIT_CLOCK_STATEMENT,
        "verdict": "PASS" if all(usable.values()) else "FAIL",
    }


# --------------------------------------------------------------------------- #
# A3 schedule-only cost gate
# --------------------------------------------------------------------------- #
def build_a3_gate_payload() -> Dict[str, Any]:
    """Schedule-only cost feasibility gate over the REAL staged snapshot."""
    bars = load_staged_bars()
    funding = load_funding_settlements()
    ticks = load_tick_sizes()
    plugin = IlliqAmihudPlugin(
        bars_by_symbol=bars,
        arm_id="ILLIQ-AMIHUD-28D-W",
        tick_sizes=ticks,
        settle_points_by_symbol=funding,
    )
    schedule = plugin.schedule()
    universe = plugin.universe(plugin.baseline_stress())
    stamps = list(schedule.instants)
    fold_members = plugin.fold_instants()
    decisions: Dict[int, ScheduleDecision] = {}
    availability: Dict[int, SignalAvailability] = {}
    fill_prices: Dict[int, Dict[str, float]] = {}
    lag_ns = EXECUTION_LAG_DAYS * DAY_NS
    for stamp in stamps:
        book = plugin.targets_at(stamp, universe=universe, stress=plugin.baseline_stress())
        is_boundary = book.get("reason_code") == "FOLD_BOUNDARY_FORCE_FLAT"
        is_final = int(stamp) == int(stamps[-1])
        kind = "FORCED_FLAT" if (is_boundary or is_final) else "DISCRETIONARY"
        decisions[int(stamp)] = ScheduleDecision(
            instant_ns=int(stamp),
            kind=kind,
            weights={str(k): float(v) for k, v in (book.get("weights") or {}).items()},
        )
        availability[int(stamp)] = SignalAvailability(
            instant_ns=int(stamp),
            available=bool(book.get("status") == "OK" and book.get("weights")),
        )
        prices: Dict[str, float] = {}
        for sym in universe:
            event = plugin._fill_event(sym, int(stamp), 0)
            if event is not None and math.isfinite(event["price"]) and event["price"] > 0:
                prices[sym] = float(event["price"])
        fill_prices[int(stamp)] = prices
    artifacts = ScheduleArtifacts(
        instants_ns=stamps,
        decisions=decisions,
        fill_prices=fill_prices,
        settlements={sym: plugin.settlements(sym) for sym in universe},
        cost_model=plugin.cost_model(),
        signal_availability=availability,
        source="research.v11.families.illiq_amihud.audits.build_a3_gate_payload",
    )
    report = evaluate_schedule_cost_feasibility(artifacts)
    return {
        "schema_version": SCHEMA_A3,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "arm_id": "ILLIQ-AMIHUD-28D-W",
        "window_start_iso": WINDOW_START_ISO,
        "window_end_iso": WINDOW_END_ISO,
        "n_universe": len(universe),
        "universe": list(universe),
        "fold_instants": {k: list(v) for k, v in fold_members.items()},
        "verdict": report.verdict,
        "report": report.payload,
        "no_scored_pnl_attestation": {
            "scored_outcome_series_emitted": False,
            "artifact_contains_only": (
                "decision instants, target books, fill-price cost inputs, "
                "funding cadence counts, declared cost parameters"
            ),
        },
    }


# --------------------------------------------------------------------------- #
# A4 exact-arm dry-run (synthetic frame through the REAL adapter path)
# --------------------------------------------------------------------------- #
def _synthetic_bar(ts_event_ns: int, open_px: float, close_px: float, dv: float):
    from research.hyp_a8_m01 import M01Bar

    return M01Bar(
        ts_event_ns=int(ts_event_ns),
        ts_init_ns=int(ts_event_ns),
        open=float(open_px),
        high=float(max(open_px, close_px)),
        low=float(min(open_px, close_px)),
        close=float(close_px),
        volume=1.0,
        quote_volume=float(dv),
        count=1,
        taker_buy_quote_volume=float(dv) / 2.0,
    )


def build_synthetic_frame(
    *,
    n_symbols: int = 16,
    weeks: int = 52,
    warmup_days: int = 200,
    premium: float = 0.002,
) -> Tuple[Dict[str, Tuple[Any, ...]], Dict[str, Tuple[SettlementPoint, ...]]]:
    """Deterministic synthetic daily bars with a PLANTED illiquidity premium.

    Symbol ``i`` carries dollar volume decreasing in ``i`` (so the Amihud
    feature ranks illiquidity by ``i``) and, after warmup, a forward daily
    drift increasing in ``i`` -- the planted illiquidity premium.  Betas stay
    near 1 (returns load on a shared deterministic factor) so the frozen
    beta hedge is well conditioned on the fixture.
    """
    from research.v11.families.illiq_amihud.strategy import weekly_monday_stamps

    stamps = weekly_monday_stamps()
    start_day = (stamps[0] - warmup_days * DAY_NS) // DAY_NS
    n_days = warmup_days + weeks * 7 + 10
    close_stamp = lambda day: int((start_day + day) * DAY_NS) + DAY_NS - 15 * 60 * 1_000_000_000
    bars: Dict[str, Tuple[Any, ...]] = {}
    btc_px = 50000.0
    btc_seq: List[Any] = []
    btc_returns: List[float] = []
    for day in range(n_days):
        r = 0.004 * math.sin(0.7 * day) + 0.001 * ((day * 7) % 5 - 2) / 5.0
        btc_returns.append(r)
        nxt = btc_px * (1.0 + r)
        btc_seq.append(_synthetic_bar(close_stamp(day), btc_px, nxt, 1_000_000_000.0))
        btc_px = nxt
    bars[BENCHMARK_SYMBOL_EXCLUDED] = tuple(btc_seq)
    for i in range(n_symbols):
        sym = f"SYN{i:02d}"
        # betas mixed (not monotone in illiquidity) so the frozen hedge tilt
        # stays well inside (0, 1) on the fixture
        beta = 0.9 + 0.2 * (((i * 7) % 5) - 2) / 2.0
        px = 100.0 * (1.0 + (i % 5) * 0.2)
        seq: List[Any] = []
        for day in range(n_days):
            idio = 0.004 * math.sin(0.9 * day + 1.7 * i)
            r = beta * btc_returns[day] + idio
            if day >= warmup_days:
                r += premium * (i - (n_symbols - 1) / 2.0)
            nxt = px * (1.0 + r)
            dv = 50_000_000.0 / (1.0 + i)
            seq.append(_synthetic_bar(close_stamp(day), px, nxt, dv))
            px = nxt
        bars[sym] = tuple(seq)
    # deterministic funding cadence: 3 points per week inside every held span
    settlements: Dict[str, Tuple[SettlementPoint, ...]] = {}
    first_ns = stamps[0]
    last_ns = stamps[-1]
    for sym in bars:
        points: List[SettlementPoint] = []
        t = first_ns + DAY_NS // 2
        step = DAY_NS // 3
        index = 0
        while t <= last_ns + 2 * DAY_NS:
            points.append(
                SettlementPoint(
                    publish_ts_ns=int(t),
                    value=0.0001 * ((index % 3) - 1),
                    kind="info",
                )
            )
            t += step
            index += 1
        settlements[sym] = tuple(points)
    return bars, settlements


def build_dry_run_arms(
    *, n_symbols: int = 16
) -> Dict[str, IlliqAmihudPlugin]:
    """The three FROZEN arms on one shared synthetic frame.

    Keys are the dry-run harness role names (anchor / neighbour /
    causal_control); each value is the corresponding frozen plugin.
    """
    bars, settlements = build_synthetic_frame(n_symbols=n_symbols)
    ticks = {sym: 0.01 for sym in bars}
    role_by_arm = {
        "ILLIQ-AMIHUD-28D-W": "anchor",
        "ILLIQ-AMIHUD-56D-W": "neighbour",
        "ILLIQ-AMIHUD-28D-W-INV": "causal_control",
    }
    arms: Dict[str, IlliqAmihudPlugin] = {}
    for arm_id, role in role_by_arm.items():
        arms[role] = IlliqAmihudPlugin(
            bars_by_symbol=bars,
            arm_id=arm_id,
            tick_sizes=ticks,
            settle_points_by_symbol=settlements,
        )
    return arms


def _make_v2_identity_provider(role_to_arm: Mapping[str, str]):
    """Lane A2 v2 trial-key provider over the frozen identity (closure)."""

    def provider(arm_payload: Mapping[str, Any]) -> str:
        pub = dict(arm_payload["identity"])
        arm_config_id = str(pub["arm_config_id"])
        arm_id = str(role_to_arm[arm_config_id])
        identity = StrategyIdentity(
            strategy_id=str(pub["strategy_id"]),
            family_id=str(pub["family_id"]),
            arm_config_id=arm_config_id,
            direction=str(pub["direction"]),
            window_start_iso=str(pub["window_start_iso"]),
            window_end_iso=str(pub["window_end_iso"]),
            benchmark_symbols_excluded=tuple(pub.get("benchmark_symbols_excluded") or ()),
            funding_sign_convention=str(
                pub.get("funding_sign_convention") or "LONG_PAYS_POSITIVE_RATE"
            ),
            arm_id=arm_id,
            config=dict(pub.get("config") or {}),
        )
        return trial_key_v2(
            identity=identity,
            stress_signature=dict(arm_payload["stress_signature"]),
            arm_id=arm_id,
        )

    return provider


def build_a4_dryrun_payload() -> Dict[str, Any]:
    """Exact-arm dry-run: distinct frozen identities, publish + replay-zero."""
    arms = build_dry_run_arms()
    role_to_arm = {
        "anchor": "ILLIQ-AMIHUD-28D-W",
        "neighbour": "ILLIQ-AMIHUD-56D-W",
        "causal_negative_control": "ILLIQ-AMIHUD-28D-W-INV",
    }
    with tempfile.TemporaryDirectory(prefix="illiq_amihud_dryrun_") as tmp:
        ledger_path = Path(tmp) / "dryrun_illiq_amihud.jsonl"
        result = run_exact_arm_dryrun(
            ledger_path=ledger_path,
            arms=arms,
            identity_provider=_make_v2_identity_provider(role_to_arm),
        )
    frozen_digests = {arm_id: frozen_arm_config_digest(arm_id) for arm_id in frozen_arm_ids()}
    return {
        "schema_version": SCHEMA_A4,
        "producer_role": PRODUCER_ROLE,
        "family_id": FAMILY_ID,
        "role_to_arm": role_to_arm,
        "arm_config_digests": {arm_id: frozen_arm_config_digest(arm_id) for arm_id in frozen_arm_ids()},
        "frozen_arm_config_digests": frozen_digests,
        "dryrun": result,
        "no_real_pnl_attestation": {
            "real_pnl": False,
            "scored": False,
            "metrics_kind": result.get("dummy_metrics_kind"),
            "ledger_temporary": True,
        },
    }


# --------------------------------------------------------------------------- #
# CLI entry
# --------------------------------------------------------------------------- #
def _write(path: str | Path, payload: Mapping[str, Any]) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(payload), indent=1, sort_keys=True, default=str)
    target.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[4]
    audit_dir = repo_root / "research" / "audits" / "v11i"
    c1 = build_c1_audit()
    c1_sha = _write(audit_dir / "illiq_amihud_c1_fields.json", c1)
    print("C1:", c1["verdict"], "sha", c1_sha[:16])
    a3 = build_a3_gate_payload()
    a3_sha = _write(audit_dir / "illiq_amihud_a3_gate.json", a3)
    print("A3:", a3["verdict"], "sha", a3_sha[:16])
    a4 = build_a4_dryrun_payload()
    a4_sha = _write(audit_dir / "illiq_amihud_a4_dryrun.json", a4)
    print("A4:", "ok" if a4["dryrun"]["ok"] else "FAILED", "sha", a4_sha[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
