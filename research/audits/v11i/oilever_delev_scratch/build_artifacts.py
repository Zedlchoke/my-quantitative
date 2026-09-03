"""Build the three lane artifacts for A8-V11-OILEVER-DELEV (V11 lane I-3).

Schedule-only + dry-run: NO scored PnL, no result artifacts, budget untouched.

Outputs (research/audits/v11i/):

* ``oilever_delev_c1_fields.json`` -- C1 field verification: OI coverage per
  symbol per stamp under the frozen PIT rule (last COMPLETED row strictly
  before the stamp, staleness <= 48h fail closed), staged 15m bar coverage,
  native funding coverage, instrument tick sizes, PIT/execution clocks and
  per-stamp signal availability for the three frozen arms;
* ``oilever_delev_a3_gate.json`` -- schedule-only cost feasibility gate
  (research.v11.cost_feasibility) over the anchor arm's real schedule
  artifacts (target books, fill-price cost inputs, funding cadence);
* ``oilever_delev_a4_dryrun.json`` -- exact-arm dry-run
  (research.v11.exact_arm_dryrun) over the three frozen arms on synthetic
  data through the REAL adapter path: distinct identities, first publish +1,
  idempotent replay +0, collision refused, temporary ledger only.

All data reads are READ-ONLY against the staged snapshot.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

import pyarrow.parquet as pq  # noqa: E402

import research.adapter_v10.publish  # noqa: F401,E402  (circular-import order)
from research.adapter_v10.protocol import CostModel, SettlementPoint  # noqa: E402
from research.v11.cost_feasibility import (  # noqa: E402
    KIND_DISCRETIONARY,
    KIND_FORCED_FLAT,
    ScheduleArtifacts,
    ScheduleDecision,
    SignalAvailability,
    evaluate_schedule_cost_feasibility,
)
from research.v11.exact_arm_dryrun import run_exact_arm_dryrun  # noqa: E402
from research.v11.families.oilever_delev import OileverDelevPlugin  # noqa: E402
from research.v11.families.oilever_delev import strategy as st  # noqa: E402
from research.v11.families.oilever_delev.strategy import bar_open_ns  # noqa: E402

CATALOG = Path("/Users/hoangminhlong/my-quantitative/catalog_live_crypto")
OI_DIR = Path("/Users/hoangminhlong/my-quantitative/oi_data/consolidated")
FUNDING_DIR = Path("/Users/hoangminhlong/my-quantitative/funding_data/scan_2026")
OUT_DIR = REPO / "research" / "audits" / "v11i"

SCALE = 10**16
DAY_NS = st.DAY_NS
HOUR_NS = st.HOUR_NS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()


def load_bars(symbol: str):
    """Staged 15m bars: ts_event = completed-bar CLOSE stamp (repo convention)."""
    directory = CATALOG / "data" / "binance_bar" / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    table = pq.read_table(
        [str(path) for path in sorted(directory.rglob("*.parquet"))],
        columns=["ts_event", "open", "high", "low", "close", "quote_volume"],
    )
    ts = [int(v) for v in table.column("ts_event").to_pylist()]
    def _px(column: str) -> list[float]:
        return [
            float(int.from_bytes(v, "little", signed=True) / SCALE)
            for v in table.column(column).to_pylist()
        ]
    opens, highs = _px("open"), _px("high")
    lows, closes = _px("low"), _px("close")
    qv = [float(v) for v in table.column("quote_volume").to_pylist()]
    return (
        tuple(
            st.Bar(
                ts_event_ns=t,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=0.0,
                quote_volume=q,
            )
            for t, o, h, l, c, q in zip(ts, opens, highs, lows, closes, qv)
        ),
        ts,
        closes,
    )


def load_oi(symbol: str):
    """Consolidated OI parquet: (create_time UTC string, sum_open_interest)."""
    frame = pq.read_table(str(OI_DIR / f"{symbol}_oi.parquet")).to_pylist()
    series = []
    for row in frame:
        moment = datetime.strptime(str(row["create_time"]), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
        series.append((int(moment.timestamp()) * 1_000_000_000, float(row["sum_open_interest"])))
    series.sort(key=lambda item: item[0])
    return tuple(series)


def load_settlements(symbol: str):
    path = FUNDING_DIR / symbol / "funding.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = sorted(payload["rows"], key=lambda row: int(row["fundingTime"]))
    return tuple(
        SettlementPoint(publish_ts_ns=int(row["fundingTime"]) * 1_000_000, value=float(row["fundingRate"]))
        for row in rows
    )


def load_tick_sizes() -> dict[str, float]:
    ticks: dict[str, float] = {}
    for directory in sorted((CATALOG / "data" / "crypto_perpetual").iterdir()):
        table = pq.read_table([str(path) for path in sorted(directory.rglob("*.parquet"))])
        row = table.to_pylist()[0]
        ticks[str(row["id"])] = float(row["price_increment"])
    return ticks


def first_bar_close_strictly_after(ts: list[int], closes: list[float], stamp_ns: int):
    """First completed bar STRICTLY AFTER the decision (cost input only)."""
    import bisect

    idx = bisect.bisect_right(ts, int(stamp_ns))
    if idx >= len(ts) or ts[idx] - stamp_ns > DAY_NS:
        return None
    return float(closes[idx])


def main() -> int:
    head = git_head()
    symbols = sorted(path.name.split("_oi.parquet")[0] for path in OI_DIR.glob("*_oi.parquet"))
    assert len(symbols) == 20, symbols

    bars_by_symbol, oi_by_symbol, settles_by_symbol = {}, {}, {}
    bars_meta = {}
    for symbol in symbols:
        bars, ts, closes = load_bars(symbol)
        bars_by_symbol[symbol] = bars
        oi_by_symbol[symbol] = load_oi(symbol)
        settles_by_symbol[symbol] = load_settlements(symbol)
        bars_meta[symbol] = (ts, closes)

    raw_ticks = load_tick_sizes()
    tick_sizes = {symbol: raw_ticks[f"{symbol}-PERP.BINANCE"] for symbol in symbols}

    plugins = {
        arm_id: OileverDelevPlugin(
            arm_id=arm_id,
            bars_by_symbol={**bars_by_symbol},
            oi_by_symbol=oi_by_symbol,
            settlements_by_symbol=settles_by_symbol,
            tick_sizes=tick_sizes,
        )
        for arm_id in st.ARM_IDS
    }
    anchor = plugins[st.ANCHOR_ARM]
    schedule = anchor.schedule()
    instants = list(schedule.instants)
    universe = anchor.tradeable_universe()

    # ------------------------------------------------------------------ #
    # C1: field verification
    # ------------------------------------------------------------------ #
    staleness_matrix: dict[str, list] = {}
    oi_meta = {}
    for symbol in sorted(oi_by_symbol):
        series = oi_by_symbol[symbol]
        times = [t for t, _ in series]
        row_stale = []
        for instant in instants:
            import bisect

            idx = bisect.bisect_left(times, int(instant)) - 1
            staleness_h = None if idx < 0 else (instant - times[idx]) / HOUR_NS
            fresh = staleness_h is not None and staleness_h <= st.OI_MAX_STALENESS_HOURS
            row_stale.append(
                {
                    "stamp": st.iso_utc(instant),
                    "anchor_create_time": None if idx < 0 else st.iso_utc(times[idx]),
                    "staleness_hours": None if staleness_h is None else round(staleness_h, 6),
                    "pit_available": bool(fresh),
                }
            )
        staleness_matrix[symbol] = row_stale
        oi_meta[symbol] = {
            "rows": len(series),
            "first_create_time": st.iso_utc(series[0][0]),
            "last_create_time": st.iso_utc(series[-1][0]),
            "sha256": sha256_file(OI_DIR / f"{symbol}_oi.parquet"),
        }

    per_stamp = []
    for index, instant in enumerate(instants):
        row: dict = {
            "stamp": st.iso_utc(instant),
            "n_symbols_oi_pit_available": sum(
                1 for symbol in symbols if staleness_matrix[symbol][index]["pit_available"]
            ),
            "arms": {},
        }
        for arm_id, plugin in plugins.items():
            book = plugin.targets_at(int(instant), universe=universe, stress=plugin.baseline_stress())
            diag = book["diagnostics"]
            row["arms"][arm_id] = {
                "status": str(book["status"]),
                "n_eligible_dv": int(diag["n_eligible_dv"]),
                "n_complete": int(diag.get("n_complete", 0)),
            }
        per_stamp.append(row)

    available_stamps = sum(
        1 for row in per_stamp if row["arms"][st.ANCHOR_ARM]["status"] == st.STATUS_OK
    )

    c1 = {
        "schema": "v11i.oilever_delev.c1_fields.v1",
        "producer_role": "I-family-3",
        "generated_utc": "BUILD_TIME",
        "head_sha_at_build": head,
        "branch": "orca/v11i-family-3",
        "frozen_spec": "research/control/v11_run/selection_freeze_specs/A8-V11-OILEVER-DELEV.json",
        "frozen_spec_sha256": sha256_file(REPO / "research/control/v11_run/selection_freeze_specs/A8-V11-OILEVER-DELEV.json"),
        "pit_clock": {
            "decision_clock": st.DECISION_CLOCK,
            "oi_rule": (
                "the OI value used at a Monday 00:00:00Z stamp is the last "
                "COMPLETED 5m row strictly BEFORE the stamp; staleness > 48h "
                "marks the stamp UNAVAILABLE for that symbol (fail closed)"
            ),
            "oi_max_staleness_hours": st.OI_MAX_STALENESS_HOURS,
            "execution_lag": (
                "one declared execution lag: fills at the open of the 15m bar "
                "covering the decision instant (first allowed execution event "
                f"after availability; fill clock {st.FILL_CLOCK})"
            ),
            "completed_bar_features": (
                "trailing-28d return uses the last completed 15m bar strictly "
                "before the stamp and the last completed bar strictly before "
                "stamp-28d; never a bar at or after the stamp"
            ),
        },
        "window": {"start": st.WINDOW_START_ISO, "end": st.WINDOW_END_ISO},
        "schedule": {
            "n_instants": len(instants),
            "first": st.iso_utc(instants[0]),
            "last": st.iso_utc(instants[-1]),
            "cadence": "Mondays 00:00:00Z",
            "folds": [
                {"id": label, "start": start, "end": end}
                for label, start, end in st.FOLD_WINDOWS
            ],
        },
        "universe": {
            "symbols": symbols,
            "benchmark_excluded_context_only": st.BENCHMARK_SYMBOL,
            "eligibility_rule": (
                "PIT listing (>= 60d bar history), active (completed bar within "
                "48h), 28d daily dollar-volume median strictly above the "
                "cross-sectional median of the active set"
            ),
            "n_symbols": len(symbols),
        },
        "oi_coverage": {
            "source": str(OI_DIR),
            "per_symbol": oi_meta,
            "per_stamp_staleness": staleness_matrix,
            "stamps": len(instants),
            "max_observed_staleness_hours": round(
                max(
                    cell["staleness_hours"]
                    for symbol in symbols
                    for cell in staleness_matrix[symbol]
                    if cell["staleness_hours"] is not None
                ),
                6,
            ),
            "n_symbol_stamps_pit_available": sum(
                cell["pit_available"]
                for symbol in symbols
                for cell in staleness_matrix[symbol]
            ),
            "n_symbol_stamps_total": len(symbols) * len(instants),
        },
        "bars_coverage": {
            "source": str(CATALOG / "data" / "binance_bar"),
            "per_symbol": {
                symbol: {
                    "rows": len(bars_by_symbol[symbol]),
                    "first_ts": st.iso_utc(bars_by_symbol[symbol][0].ts_event_ns),
                    "last_ts": st.iso_utc(bars_by_symbol[symbol][-1].ts_event_ns),
                    "covers_all_52_stamps": all(
                        any(bar_open_ns(bar) <= instant < bar.ts_event_ns for bar in bars_by_symbol[symbol])
                        for instant in instants
                    ),
                }
                for symbol in symbols
            },
        },
        "funding_coverage": {
            "source": str(FUNDING_DIR),
            "per_symbol": {
                symbol: {
                    "rows": len(settles_by_symbol[symbol]),
                    "first_settle": st.iso_utc(settles_by_symbol[symbol][0].publish_ts_ns),
                    "last_settle": st.iso_utc(settles_by_symbol[symbol][-1].publish_ts_ns),
                }
                for symbol in symbols
            },
            "role": "native funding while held (cost line only, never a signal input)",
        },
        "instruments": {
            "tick_sizes_source": str(CATALOG / "data" / "crypto_perpetual"),
            "tick_sizes": {symbol: tick_sizes[symbol] for symbol in symbols},
            "taker_fee_floor_bps": st.TAKER_FEE_FLOOR_BPS,
            "adverse_tick_slip_floor": st.ADVERSE_TICK_SLIP_FLOOR,
        },
        "per_stamp_signal_availability": per_stamp,
        "anchor_available_stamps": available_stamps,
        "beta_context": {
            "definition": (
                "BTC-beta-neutral alpha context via the frozen 90d daily beta; "
                "BTCUSDT is benchmark-excluded (context-only, never a position)"
            ),
            "beta_window_days": st.BETA_WINDOW_DAYS,
            "beta_at_last_stamp": {
                symbol: st.beta_hedge_ratio(
                    bars_by_symbol[symbol], bars_by_symbol[st.BENCHMARK_SYMBOL], instants[-1]
                )
                for symbol in symbols
            },
        },
    }

    # ------------------------------------------------------------------ #
    # A3: schedule-only cost feasibility gate (anchor arm books)
    # ------------------------------------------------------------------ #
    decisions = {}
    fill_prices = {}
    availability = {}
    for index, instant in enumerate(instants):
        is_final = index == len(instants) - 1
        if is_final:
            decisions[int(instant)] = ScheduleDecision(
                instant_ns=int(instant), kind=KIND_FORCED_FLAT, weights={}
            )
            # The terminal edge is a FORCED_FLAT action (never a discretionary
            # open); the availability row below only records that the proposed
            # signal itself was computable there -- it opens no book.
            book = anchor.targets_at(int(instant), universe=universe, stress=anchor.baseline_stress())
        else:
            book = anchor.targets_at(int(instant), universe=universe, stress=anchor.baseline_stress())
            weights = {sym: float(w) for sym, w in book["weights"]}
            decisions[int(instant)] = ScheduleDecision(
                instant_ns=int(instant),
                kind=KIND_DISCRETIONARY,
                weights=weights,
            )
        availability[int(instant)] = SignalAvailability(
            instant_ns=int(instant),
            available=bool(book["status"] == st.STATUS_OK),
        )
        prices = {}
        for symbol in universe:
            ts, closes = bars_meta[symbol]
            price = first_bar_close_strictly_after(ts, closes, instant)
            if price is not None:
                prices[symbol] = price
        fill_prices[int(instant)] = prices

    cost_model = CostModel(
        taker_fee_bps=st.TAKER_FEE_FLOOR_BPS,
        adverse_tick_slip_floor=st.ADVERSE_TICK_SLIP_FLOOR,
        default_tick_sizes=dict(tick_sizes),
    )
    artifacts = ScheduleArtifacts(
        instants_ns=instants,
        decisions=decisions,
        fill_prices=fill_prices,
        settlements={symbol: settles_by_symbol[symbol] for symbol in universe},
        cost_model=cost_model,
        signal_availability=availability,
        source="research.v11.families.oilever_delev.strategy.weekly_mondays(anchor books)",
    )
    report = evaluate_schedule_cost_feasibility(artifacts)

    a3 = {
        "schema": "v11i.oilever_delev.a3_gate.v1",
        "producer_role": "I-family-3",
        "generated_utc": "BUILD_TIME",
        "head_sha_at_build": head,
        "arm_id": st.ANCHOR_ARM,
        "gate_source": "research.v11.cost_feasibility.evaluate_schedule_cost_feasibility (imported, not forked)",
        "verdict": report.verdict,
        "report": report.payload,
        "outcome_blind_attestation": {
            "schedule_only": True,
            "scored_pnl_computed": False,
            "note": (
                "gate consumed decision instants, target books, fill-price cost "
                "inputs, funding cadence and declared cost parameters only"
            ),
        },
    }

    # ------------------------------------------------------------------ #
    # A4: exact-arm dry-run (synthetic world through the REAL adapter path)
    # ------------------------------------------------------------------ #
    sys.path.insert(0, str(REPO / "tests"))
    import test_v11i_oilever_delev_frozen as fixture  # synthetic world builder

    world = fixture.build_world()
    synthetic = {
        "anchor": fixture.build_plugins(world)[st.ANCHOR_ARM],
        "neighbour": fixture.build_plugins(world)[st.NEIGHBOUR_ARM],
        "causal_control": fixture.build_plugins(world)[st.CONTROL_ARM],
    }
    ledger = Path(tempfile.gettempdir()) / "dryrun_oilever_delev_a4.jsonl"
    if ledger.exists():
        ledger.unlink()
    dryrun = run_exact_arm_dryrun(arms=synthetic, ledger_path=ledger)

    a4 = {
        "schema": "v11i.oilever_delev.a4_dryrun.v1",
        "producer_role": "I-family-3",
        "generated_utc": "BUILD_TIME",
        "head_sha_at_build": head,
        "dryrun_source": "research.v11.exact_arm_dryrun.run_exact_arm_dryrun (imported, not forked)",
        "ok": bool(dryrun["ok"]),
        "scored": False,
        "real_pnl": False,
        "arms_checked": {name: {"identity_digest": arm_config_digest_of(plugin)}
                         for name, plugin in synthetic.items()},
        "identity_distinctness": dryrun["identity_distinctness"],
        "stage_checklist": dryrun["stage_checklist"],
        "n_stages_ok": sum(1 for stage in dryrun["stages"] if stage["ok"]),
        "n_stages_total": len(dryrun["stages"]),
        "findings": dryrun["findings"],
        "arms": dryrun["arms"],
        "ledger": dryrun["ledger"],
        "frozen_digests_match": {
            arm: arm_config_digest_of(plugins[arm]) == FROZEN[arm] for arm in st.ARM_IDS
        },
    }

    # ------------------------------------------------------------------ #
    # Emit (stable, deterministic field order)
    # ------------------------------------------------------------------ #
    build_time = st.iso_utc(int(time.time_ns()))
    for artifact in (c1, a3, a4):
        artifact["generated_utc"] = build_time

    (OUT_DIR / "oilever_delev_c1_fields.json").write_text(
        json.dumps(c1, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "oilever_delev_a3_gate.json").write_text(
        json.dumps(a3, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "oilever_delev_a4_dryrun.json").write_text(
        json.dumps(a4, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        "C1  : oi_available",
        c1["oi_coverage"]["n_symbol_stamps_pit_available"],
        "/",
        c1["oi_coverage"]["n_symbol_stamps_total"],
        "max_staleness_h",
        c1["oi_coverage"]["max_observed_staleness_hours"],
        "anchor_available_stamps",
        available_stamps,
        "/",
        len(instants),
    )
    print(
        "A3  : verdict",
        report.verdict,
        {f["floor_id"]: f["status"] for f in report.payload["floors"]},
    )
    print(
        "A4  : ok",
        a4["ok"],
        "stages",
        a4["n_stages_ok"],
        "/",
        a4["n_stages_total"],
        "findings",
        len(a4["findings"]),
    )
    return 0 if (report.verdict == "PASS" and dryrun["ok"]) else 1


FROZEN = {
    "OILEV-FLOW-28D-W": "d05c2e702c8ce02f24b843c1bd92c66451effb8c8cb73a27bd8376112ddff29a",
    "OILEV-STOCK-56D-W": "a1f29b683a263ecdd052016862f6bebc9831d3bf5df5e4f5f0cd4b1c92bac24d",
    "OILEV-FLOW-28D-W-INV": "b64b314fd116258323d9b72a0633999fe3a7e71ac87a0516d3cf60b61d09a04f",
}


def arm_config_digest_of(plugin):
    from research.v11.publication_identity import arm_config_digest

    ident = plugin.identity()
    return arm_config_digest(ident, arm_id=ident.arm_id)


if __name__ == "__main__":
    raise SystemExit(main())
