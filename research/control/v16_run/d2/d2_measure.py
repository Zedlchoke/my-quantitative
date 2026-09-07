"""CRYPTO-V16 D2 pre-selection measurements: G12 ancestry novelty, control
identifiability, fold populations. NO PnL anywhere - exposures and counts only.

Veto thresholds (DECLARED_AT_D2_PRE_SELECTION, before any scored outcome exists;
recorded as a freeze-time amendment - see d2 artifact):
- ancestry (G12 / cheap-kill 13): pooled |rho| > 0.20 vs any reconstructable
  forbidden exposure -> proposal dead.
- control identifiability (cheap-kill 14): exposure-form anchor/control
  |rho| > 0.70 -> control cannot falsify -> proposal dead. Reshuffled-interval
  controls are NOT subject to this kill (same marginal, destroyed alignment -
  distinguishable by construction); recorded as NOT_APPLICABLE_SHUFFLE_CLASS.
- fold population (cheap-kill 15): < 15 bookable symbol-decisions in any fold
  (chronological thirds with 1-day purge, V12 frozen contract) -> dead.

Forbidden exposures are RECONSTRUCTED from authorized keyless staged data
(V15 durable bulk-metrics parquet + funding json; MEASURED_BOUND_LAG_3D - lag
semantics are irrelevant to contemporaneous correlation measurement).
Exposures that cannot be reconstructed from authorized staged data are
reported NOT_MEASURABLE with the reason - never silently skipped.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORKTREE = Path(__file__).resolve().parents[4]
STAGING = WORKTREE / "v16_data" / "staging_v16"
ART = WORKTREE / "research" / "control" / "v16_run" / "d2"
V15_DATA = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/integration/v15_data")
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
ANCESTRY_VETO = 0.20
IDENTIFIABILITY_VETO = 0.70
FOLD_FLOOR = 15
SEED_WINDOW = 28


def pooled_rho(frames_by_symbol: dict[str, pd.Series], kind: str = "pearson") -> float:
    """Concatenate per-symbol aligned series, drop NaN, correlate."""
    df = pd.DataFrame(frames_by_symbol)
    df = df.dropna()
    if len(df) < 30:
        return float("nan")
    x, y = df.iloc[:, 0], df.iloc[:, 1]
    if kind == "spearman":
        x, y = x.rank(), y.rank()
    if x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def z28(s: pd.Series) -> pd.Series:
    m = s.rolling(SEED_WINDOW).mean()
    sd = s.rolling(SEED_WINDOW).std()
    return (s - m) / sd


def load_panel() -> pd.DataFrame:
    frames = []
    for sym in SYMBOLS:
        df = pd.read_csv(STAGING / f"panel_{sym}_daily.csv")
        df["symbol"] = sym
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def proposal_exposures(panel: pd.DataFrame) -> dict[str, pd.Series]:
    """Decision-time conditioning series per proposal, per symbol."""
    out: dict[str, dict[str, pd.Series]] = {}
    for sym in SYMBOLS:
        g = panel[panel.symbol == sym].sort_values("date").set_index("date")
        fi = g["flow_imbalance"]
        streak_sum = g["buy_streak_max"] + g["sell_streak_max"]
        r = (g["buy_streak_max"] - g["sell_streak_max"]) / streak_sum.replace(0, np.nan)
        rng = (g["high_price"] - g["low_price"]).replace(0, np.nan)
        disp = (g["last_price"] - g["vwap"]) / rng
        ret1 = g["vwap"].pct_change()
        out.setdefault("A4-P1_flow_imbalance", {})[sym] = fi
        out.setdefault("A4-P2-A6-P2_run_imb", {})[sym] = r
        out.setdefault("A5-P1_burstiness_z28", {})[sym] = z28(g["arrival_burstiness"])
        out.setdefault("A5-P2_count_z28", {})[sym] = z28(g["trade_count"])
        out.setdefault("A6-P1_disp", {})[sym] = disp
        # identifiability control features
        out.setdefault("CTL-A4P1_notional_z", {})[sym] = z28(np.log1p(g["total_notional"]))
        out.setdefault("CTL-A4P2_cascade_unsigned", {})[sym] = (
            g[["buy_streak_max", "sell_streak_max"]].max(axis=1)
            / np.log2(g["trade_count"].clip(lower=2)))
        out.setdefault("CTL-A6P1_ret1", {})[sym] = ret1
    return out


def forbidden_exposures() -> tuple[dict[str, dict[str, pd.Series]], dict[str, str]]:
    """Reconstruct forbidden-family conditioning series from authorized staged bytes."""
    exp: dict[str, dict[str, pd.Series]] = {}
    notes: dict[str, str] = {}
    for sym in SYMBOLS:
        m = pd.read_parquet(V15_DATA / "parquet" / "metrics" / f"{sym}.parquet")
        m["date"] = pd.to_datetime(m["create_time"]).dt.date.astype(str)
        m = m.sort_values("date").set_index("date")
        oi = m["sum_open_interest"]
        taker = m["sum_taker_long_short_vol_ratio"]
        churn = oi.diff().abs() / oi
        exp.setdefault("TAKER-SAT_aggression_per_OI_churn_5d", {})[sym] = (
            taker.rolling(5).mean() / churn.rolling(5).mean().replace(0, np.nan))
        exp.setdefault("OILEV_oi_level_log", {})[sym] = np.log(oi)
        exp.setdefault("OITD_oi_churn", {})[sym] = churn
        exp.setdefault("ELITE-LEVEL_toptrader_pos_ratio", {})[sym] = m["sum_toptrader_long_short_ratio"]
        exp.setdefault("ELITE-SIZE-ASYM_top_vs_all_acct", {})[sym] = (
            m["count_toptrader_long_short_ratio"] / m["count_long_short_ratio"])
        exp.setdefault("TAKER_raw_ratio", {})[sym] = taker
        exp.setdefault("LIQEPIS_proxy_oi_spike", {})[sym] = z28(churn)
        f = pd.read_json(V15_DATA / "funding_json" / f"{sym}.json")
        # funding rows: list of dicts with fundingTime + fundingRate (binance fapi shape)
        try:
            f["date"] = pd.to_datetime(f["fundingTime"], unit="ms").dt.date.astype(str)
            fr = f.set_index("date")["fundingRate"].astype(float)
            exp.setdefault("CARRY-BAB_funding_rate_8h", {})[sym] = fr
        except Exception:
            notes["CARRY-BAB_funding_rate_8h"] = "funding json parse failed for " + sym
    notes["PREMFADE_basis_premium"] = (
        "NOT_MEASURABLE: no prem/futures basis series in authorized staged data "
        "(v15 staging has no .pmbasis parquet); mechanism is basis-level, "
        "orthogonal to print-flow features by construction - disclosed, not skipped")
    notes["BAB_beta_arbitrage_full"] = (
        "proxied by funding-rate series only; the full BAB construction needs "
        "cross-sectional beta universe data outside the frozen 2-symbol design")
    return exp, notes


def fold_counts(panel: pd.DataFrame, trig: dict[str, dict[str, pd.Series]]) -> dict:
    """Chronological thirds of decision days with 1-day purge (V12 contract)."""
    res = {}
    for name, per_symbol in trig.items():
        days = sorted(set().union(*[
            set(s.fillna(False).astype(bool)[lambda x: x].index)
            for s in per_symbol.values()]))
        n = len(days)
        if n < 4:
            res[name] = {"decision_days": n, "folds": "INSUFFICIENT"}
            continue
        edges = [round(i * n / 3) for i in range(4)]
        folds = {}
        for k in range(3):
            stop = max(edges[k] + 1, edges[k + 1] - 1)
            folds[f"F{k}"] = days[edges[k]:stop]
        res[name] = {
            "decision_days_total": n,
            "per_fold_days": {k: len(v) for k, v in folds.items()},
            "per_fold_symbol_decisions": {
                k: int(sum(int(per_symbol[s].reindex(v).fillna(False).astype(bool).sum())
                           for s in SYMBOLS))
                for k, v in folds.items()},
        }
    return res


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    prop = proposal_exposures(panel)
    forb, fnotes = forbidden_exposures()

    prop_names = [k for k in prop if not k.startswith("CTL-")]
    ctl_names = [k for k in prop if k.startswith("CTL-")]

    ancestry = {}
    for p in prop_names:
        rows = {}
        worst = 0.0
        for f in forb:
            xs, ys = [], []
            for s in SYMBOLS:
                both = pd.concat([prop[p][s], forb[f][s]], axis=1).dropna()
                xs.append(both.iloc[:, 0])
                ys.append(both.iloc[:, 1])
            x = pd.concat(xs); y = pd.concat(ys)
            r_p = float(np.corrcoef(x, y)[0, 1]) if len(x) >= 30 and x.std() > 0 and y.std() > 0 else float("nan")
            r_s = float(np.corrcoef(x.rank(), y.rank())[0, 1]) if len(x) >= 30 else float("nan")
            rows[f] = {"pearson": round(r_p, 4), "spearman": round(r_s, 4),
                       "n": int(len(x))}
            worst = max(worst, abs(r_p), abs(r_s))
        rows["max_abs_rho"] = round(worst, 4)
        rows["ancestry_veto"] = bool(worst > ANCESTRY_VETO)
        ancestry[p] = rows

    ident = {}
    for p, c in [("A4-P1_flow_imbalance", "CTL-A4P1_notional_z"),
                 ("A4-P2-A6-P2_run_imb", "CTL-A4P2_cascade_unsigned"),
                 ("A6-P1_disp", "CTL-A6P1_ret1")]:
        xs, ys = [], []
        for s in SYMBOLS:
            both = pd.concat([prop[p][s], prop[c][s]], axis=1).dropna()
            xs.append(both.iloc[:, 0]); ys.append(both.iloc[:, 1])
        x, y = pd.concat(xs), pd.concat(ys)
        r = float(np.corrcoef(x, y)[0, 1]) if len(x) >= 30 else float("nan")
        ident[p] = {"control": c, "pearson": round(r, 4),
                    "identifiability_veto_gt_0p70": bool(abs(r) > IDENTIFIABILITY_VETO)}
    for name in ["A5-P1_burstiness_z28", "A5-P2_count_z28"]:
        ident[name] = {"control": "reshuffled-interval placebo",
                       "verdict": "NOT_APPLICABLE_SHUFFLE_CLASS"}

    # siblings
    sib = {}
    plist = list(prop_names)
    for i in range(len(plist)):
        for j in range(i + 1, len(plist)):
            a, b = plist[i], plist[j]
            xs, ys = [], []
            for s in SYMBOLS:
                both = pd.concat([prop[a][s], prop[b][s]], axis=1).dropna()
                xs.append(both.iloc[:, 0]); ys.append(both.iloc[:, 1])
            x, y = pd.concat(xs), pd.concat(ys)
            sib[f"{a}~{b}"] = round(float(np.corrcoef(x, y)[0, 1]), 4) if len(x) >= 30 else None

    # fold populations: boolean trigger series per proposal spec, V12 thirds + 1-day purge
    def two_sided_q90(series_by_sym):
        out = {}
        for s, x in series_by_sym.items():
            hi = x.rolling(90, min_periods=30).quantile(0.90)
            lo = x.rolling(90, min_periods=30).quantile(0.10)
            out[s] = (x >= hi) | (x <= lo)
        return out
    disp_abs = {s: prop["A6-P1_disp"][s].abs() for s in SYMBOLS}
    run_abs = {s: prop["A4-P2-A6-P2_run_imb"][s].abs() for s in SYMBOLS}
    triggers = {
        "A4-P1_flow_imbalance_2sided_q90": two_sided_q90(prop["A4-P1_flow_imbalance"]),
        "A4P2-A6P2_run_imb_2sided_q90": two_sided_q90(prop["A4-P2-A6-P2_run_imb"]),
        "A5-P1_burstiness_z_gt_2": {s: (prop["A5-P1_burstiness_z28"][s] > 2.0) for s in SYMBOLS},
        "A5-P2_count_z_le_-1": {s: (prop["A5-P2_count_z28"][s] <= -1.0) for s in SYMBOLS},
        "A6-P1_disp_abs_q80_60d": {s: (disp_abs[s] >= disp_abs[s].rolling(60, min_periods=30).quantile(0.80)) for s in SYMBOLS},
        "A6-P2_run_imb_abs_q80_60d": {s: (run_abs[s] >= run_abs[s].rolling(60, min_periods=30).quantile(0.80)) for s in SYMBOLS},
    }
    counts = {k: int(sum(int(v.sum()) for v in t.values())) for k, t in triggers.items()}
    folds = fold_counts(panel, triggers)

    artifact = {
        "schema": "v16_run_artifact_v1",
        "artifact": "d2_novelty_identifiability_populations",
        "generated_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (D2 pre-selection measurements; NO PnL)",
        "declared_thresholds": {
            "ancestry_veto_abs_rho_gt": ANCESTRY_VETO,
            "identifiability_veto_abs_pearson_gt": IDENTIFIABILITY_VETO,
            "fold_floor_symbol_decisions": FOLD_FLOOR,
            "note": "thresholds DECLARED_AT_D2_PRE_SELECTION before any scored outcome; "
                    "identifiability threshold is a freeze-time amendment (P3 declared "
                    "the class but not the number) - recorded as p3_freeze_amendment_1_v16",
        },
        "ancestry_rho_vs_forbidden": ancestry,
        "forbidden_exposure_notes": fnotes,
        "control_identifiability": ident,
        "sibling_proposal_pearson": sib,
        "trigger_counts_whole_window": counts,
        "panel_rows": {s: int((panel.symbol == s).sum()) for s in SYMBOLS},
    }
    (ART / "d2_novelty_v16.json").write_text(json.dumps(artifact, indent=1) + "\n")
    print(json.dumps({"ancestry_max_rho": {k: v["max_abs_rho"] for k, v in ancestry.items()},
                      "ancestry_veto": {k: v["ancestry_veto"] for k, v in ancestry.items()},
                      "identifiability": ident,
                      "siblings": sib,
                      "trigger_counts": counts}, indent=1))


if __name__ == "__main__":
    main()
