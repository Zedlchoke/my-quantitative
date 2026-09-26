"""ERP1-TRACKB-COHORT-1 — M1 gate law + PIT fixtures (F-2 battery M-1..M-5).

Implements the frozen decision law (TRIAL_FREEZE_v1.json + FN-1):
  epoch   = first 1h bar with open_time >= Friday 00:00 UTC
  gate    = mean settled fundingRate over trailing 90d (settle <= T) x
            settlements-per-hold  >=  C*(H) = 45.0 bps  (anchor; 50/60
            sensitivity reported, margin-to-fail mandatory)
NO PnL anywhere in this module: it produces decision-state series and
fixture verdicts only (GO-1 falsifier scope).
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CYC = ROOT / "research/control/ERP1-TRACKB-COHORT-1"
DATA = CYC / "data_local"
HOUR_MS = 3_600_000
C_STAR = {"28d": 45.0, "35d": 45.0, "42d": 45.0}
SETTLEMENTS_PER_HOLD = {"28d": 84, "35d": 105, "42d": 126}
RECENT_WINDOW_MS = 90 * 24 * HOUR_MS * 1000 // 24 * 24  # 90d in ms


def ms(x: int | str) -> int:
    return int(x)


# ---------- loaders ----------

def load_funding() -> list[dict]:
    payload = json.loads((DATA / "funding/BTCUSDT/funding.json").read_text())
    rows = [{"t": int(r["fundingTime"]), "r": float(str(r["fundingRate"]))}
            for r in payload["rows"]]
    rows.sort(key=lambda x: x["t"])
    return rows


def _norm_ms(v: int) -> int:
    """Normalize kline stamps to ms. Binance vision spot monthly klines
    switched to MICROSECOND open_time from 2025 — detected by magnitude
    (>1e14 => us). Recorded as battery incident I-2; without this the
    epoch grid silently truncates at 2024-12-27 (ms-guard drops us rows)."""
    v = int(v)
    return v // 1000 if v > 100_000_000_000_000 else v


def _kline_rows(zips: list[Path]):
    out = []
    for z in sorted(zips):
        with zipfile.ZipFile(z) as zf:
            name = zf.namelist()[0]
            text = zf.read(name).decode()
        rdr = csv.reader(io.StringIO(text))
        for row in rdr:
            if not row or not row[0].strip() or not row[0][0].isdigit():
                continue  # header/blank
            out.append({"open": _norm_ms(row[0]), "close_t": _norm_ms(row[6]),
                        "o": float(row[1]), "h": float(row[2]),
                        "l": float(row[3]), "c": float(row[4])})
    out.sort(key=lambda x: x["open"])
    return out


def load_spot() -> list[dict]:
    return _kline_rows(sorted((DATA / "spot_1h").glob("spot_1h-*.zip")))


def load_perp() -> list[dict]:
    return _kline_rows(sorted((DATA / "perp_1h").glob("perp_1h-*.zip")))


def dev_bounds_ms() -> tuple[int, int]:
    lo = int(datetime(2020, 7, 18, tzinfo=timezone.utc).timestamp() * 1000)
    hi = int(datetime(2026, 8, 21, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
    return lo, hi


# ---------- the frozen gate law (M-1 independent-form: array-free bisect form) ----------

def expected_carry_bps(funding: list[dict], T_ms: int, hold: str) -> float | None:
    """Mean settled rate over trailing 90d at T, in bps x settlements-per-hold.

    Strict PIT: only settlements with t <= T enter. Returns None when the
    90d window holds fewer than 60 settlements (insufficient coverage ->
    FLAT by fail-closed law).
    """
    import bisect
    ts = [f["t"] for f in funding]
    hi = bisect.bisect_right(ts, T_ms)
    lo = bisect.bisect_left(ts, T_ms - 90 * 86_400_000)
    window = funding[lo:hi]
    if len(window) < 60:
        return None
    mean_rate = sum(f["r"] for f in window) / len(window)
    return mean_rate * 1e4 * SETTLEMENTS_PER_HOLD[hold]  # rate -> bps, x settlements


def gate_state(funding: list[dict], T_ms: int, hold: str) -> str:
    ec = expected_carry_bps(funding, T_ms, hold)
    if ec is None:
        return "FLAT"
    return "LONG_CARRY" if ec >= C_STAR[hold] else "FLAT"


# ---------- epochs ----------

def weekly_epochs(bars: list[dict], lo_ms: int, hi_ms: int) -> list[int]:
    """First 1h bar open_time >= Friday 00:00 UTC inside [lo, hi]."""
    out, seen = [], set()
    for b in bars:
        t = b["open"]
        if t < lo_ms or t > hi_ms:
            continue
        dt = datetime.fromtimestamp(t / 1000, tz=timezone.utc)
        if dt.weekday() != 4 or dt.hour != 0:  # Friday 00:00
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    out.sort()
    return out


# ---------- M-fixtures (P-18 battery) ----------

def m1_independent_equivalence() -> dict:
    """M-1: from-scratch windowed-mean vs the bisect implementation."""
    funding = load_funding()
    T = int(datetime(2024, 1, 5, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    # from-scratch naive loop (different algorithm, same semantics)
    w = [f["r"] for f in funding if T - 90 * 86_400_000 <= f["t"] <= T]
    naive = (sum(w) / len(w)) * 1e4 * 105
    fast = expected_carry_bps(funding, T, "35d")
    ok = abs(naive - fast) < 1e-9
    return {"fixture": "M-1", "verdict": "PASS" if ok else "FAIL",
            "naive": naive, "fast": fast, "n_window": len(w)}


def m2_nonvacuity_shift() -> dict:
    """M-2: one-epoch information delay must be able to move the state
    (>=2% of epochs change when the decision window ends at the PREVIOUS
    epoch, T-7d). Fixture v2 — the v1 drop-last-settlement probe was a
    defective operationalization (recorded as incident; it measured
    marginal-data sensitivity, not an index shift)."""
    funding = load_funding()
    lo, hi = dev_bounds_ms()
    epochs = weekly_epochs(load_spot(), lo, hi)
    import bisect
    ts = [f["t"] for f in funding]

    def delayed_state(T: int) -> str:
        cut = bisect.bisect_right(ts, T - 7 * 86_400_000)  # info as of prior epoch
        window = funding[max(0, bisect.bisect_left(ts, T - 7 * 86_400_000 - 90 * 86_400_000)):cut]
        if len(window) < 60:
            return "FLAT"
        mean_rate = sum(f["r"] for f in window) / len(window)
        ec = mean_rate * 1e4 * 105
        return "LONG_CARRY" if ec >= C_STAR["35d"] else "FLAT"

    full = [gate_state(funding, t, "35d") for t in epochs]
    delayed = [delayed_state(t) for t in epochs]
    diff = sum(1 for a, b in zip(full, delayed) if a != b)
    share = diff / max(1, len(epochs))
    nonconst = len(set(full)) > 1
    return {"fixture": "M-2 (v2 one-epoch delay)", "verdict": "PASS" if (share >= 0.02 and nonconst) else "KILL_VACUOUS_MUTATION",
            "epochs": len(epochs), "moved_under_delay": diff, "share": round(share, 4),
            "state_series_nonconstant": nonconst}


def m3_truncation_replay() -> dict:
    """M-3 (P-18): replay on panels truncated at each decision time MUST be
    byte-identical to the full-panel state series (settled-only law)."""
    funding = load_funding()
    lo, hi = dev_bounds_ms()
    epochs = weekly_epochs(load_spot(), lo, hi)
    full = [gate_state(funding, t, "35d") for t in epochs]
    bad = 0
    for t, expected in zip(epochs, full):
        import bisect
        ts = [f["t"] for f in funding]
        cut = bisect.bisect_right(ts, t)
        truncated = funding[:cut]
        if gate_state(truncated, t, "35d") != expected:
            bad += 1
    return {"fixture": "M-3", "verdict": "PASS" if bad == 0 else "KILL_PIT_SEAM",
            "epochs": len(epochs), "mismatches": bad}


def m4_seam_disclosure() -> dict:
    """M-4: kline stamps/headers normalized; basis channels separated."""
    spot, perp = load_spot(), load_perp()
    def has_header(z: Path) -> bool:
        with zipfile.ZipFile(z) as zf:
            first = zf.read(zf.namelist()[0]).decode().splitlines()[0]
        return not first.split(",")[0].strip().isdigit()
    s_h = has_header(sorted((DATA / "spot_1h").glob("*2024-01*"))[0])
    p_h = has_header(sorted((DATA / "perp_1h").glob("*2024-01*"))[0])
    # both series must be open-time stamped 1h grids
    grid_ok = all((b["open"] % HOUR_MS) == 0 for b in spot[:500] + perp[:500])
    return {"fixture": "M-4", "verdict": "PASS" if grid_ok else "FAIL",
            "spot_zip_header": s_h, "perp_zip_header": p_h,
            "open_time_grid_1h": grid_ok,
            "disclosure": "vision klines open-time stamped; catalog close-stamped LAST bars NOT used; funding premium (mark/index) channel not consumed by the gate"}


def m5_no_same_bar_statistic() -> dict:
    """M-5: a settlement 1ms AFTER epoch T must not change T's state.
    Fixture v2 — SINGLE poison per probed epoch (the v1 multi-poison design
    cross-contaminated trailing windows with earlier epochs' poison — a
    fixture defect, recorded as incident, not a gate leak)."""
    funding = load_funding()
    lo, hi = dev_bounds_ms()
    epochs = weekly_epochs(load_spot(), lo, hi)[10:60]
    base = [gate_state(funding, t, "35d") for t in epochs]
    bad = 0
    for t, expected in zip(epochs, base):
        merged = sorted(funding + [{"t": t + 1, "r": 0.01}], key=lambda x: x["t"])
        if gate_state(merged, t, "35d") != expected:
            bad += 1
    near = sum(1 for t in epochs if any(abs(f["t"] - t) <= 1 for f in funding))
    return {"fixture": "M-5 (v2 single-poison)", "verdict": "PASS" if bad == 0 else "KILL_PIT_SEAM",
            "epochs_probed": len(epochs), "state_changes_from_future_settlement": bad,
            "epochs_with_settlement_exactly_at_T": near}


def decision_state_series(hold: str = "35d") -> list[dict]:
    """The F-1 rho input: {epoch_ms, state} on the dev window."""
    funding = load_funding()
    lo, hi = dev_bounds_ms()
    epochs = weekly_epochs(load_spot(), lo, hi)
    return [{"t": t, "d": gate_state(funding, t, hold),
             "ec_bps": expected_carry_bps(funding, t, hold)} for t in epochs]


def f6_feasibility() -> dict:
    """F-6: nearest-window gate-fire counts + hold populations (no PnL)."""
    series = decision_state_series("35d")
    recent = [s for s in series
              if s["t"] >= int(datetime(2026, 2, 21, tzinfo=timezone.utc).timestamp() * 1000)]
    last6m_fires = sum(1 for s in recent if s["d"] == "LONG_CARRY")
    total_fires = sum(1 for s in series if s["d"] == "LONG_CARRY")
    # non-overlapping hold population over the full dev window
    holds, cursor = 0, -1
    for s in series:
        if s["d"] == "LONG_CARRY" and s["t"] > cursor:
            holds += 1
            cursor = s["t"] + 35 * 86_400_000
    return {"fixture": "F-6", "epochs_total": len(series),
            "gate_fires_total": total_fires,
            "gate_fires_last_6m": last6m_fires,
            "non_overlap_holds_35d": holds,
            "g5_floor_holds": 40,
            "population_note": "G5 needs >=52 epochs AND >=40 closed holds AND bootstrap CI; counts only, no PnL"}


def f3_control_construction() -> dict:
    """F-3: entry-timing permutation control — constructibility + non-vacuity
    facts, honestly measured. The frozen >=90%-differ predicate (sparse-firing
    template) is structurally unreachable for a persistent gate (any
    permutation of 181-of-232 positions overlaps by chance); this is
    DISCLOSED for skeptic/owner adjudication, not silently waived. The
    load-bearing nulls actually available pre-PnL: one-epoch delay (M-2)
    and threshold sensitivity. No PnL."""
    import random
    series = decision_state_series("35d")
    n = len(series)
    fire_idx = [i for i, s in enumerate(series) if s["d"] == "LONG_CARRY"]
    rng = random.Random(56532041819335)  # frozen permutation seed
    perm_idx = set(rng.sample(range(n), len(fire_idx)))
    anchor_idx = set(fire_idx)
    union = len(anchor_idx | perm_idx)
    jaccard_dist = 1 - len(anchor_idx & perm_idx) / union
    chance_overlap = len(anchor_idx) ** 2 / n  # expected |A∩B| for uniform permutation
    chance_jd = 1 - chance_overlap / (2 * len(anchor_idx) - chance_overlap)
    occupancy = len(fire_idx) / n
    # threshold sensitivity: states at C* 45 vs 50 vs 60
    sens = {}
    for cstar in (45.0, 50.0, 60.0):
        fires = sum(1 for s in series if s["ec_bps"] is not None and s["ec_bps"] >= cstar)
        sens[str(cstar)] = fires
    return {"fixture": "F-3", "construction": "CONSTRUCTIBLE",
            "occupancy": round(occupancy, 3),
            "occupancy_band_frozen": [0.10, 0.40],
            "occupancy_band_verdict": "BAND_EXCEEDED_persistent_gate_DISCLOSED_for_adjudication",
            "permuted_vs_anchor_jaccard_distance": round(jaccard_dist, 3),
            "chance_level_jaccard_distance": round(chance_jd, 3),
            "frozen_ge90_differ_predicate": "STRUCTURALLY_UNREACHABLE_for_persistent_gate_DISCLOSED",
            "threshold_sensitivity_fires": sens,
            "both_states_present": len(anchor_idx) not in (0, n),
            "verdict": "CONSTRUCTIBLE_WITH_TWO_DISCLOSED_PREDICATE_DEVIATIONS"}


if __name__ == "__main__":
    out = {"m1": m1_independent_equivalence(),
           "m2": m2_nonvacuity_shift(),
           "m3": m3_truncation_replay(),
           "m4": m4_seam_disclosure(),
           "m5": m5_no_same_bar_statistic(),
           "f3": f3_control_construction(),
           "f6": f6_feasibility()}
    print(json.dumps(out, indent=1))
    series = decision_state_series("35d")
    (CYC / "artifacts").mkdir(exist_ok=True)
    (CYC / "artifacts/decision_state_M1_ANCHOR_35d.jsonl").write_text(
        "\n".join(json.dumps(s) for s in series))
    print("state series written:", len(series), "epochs")
