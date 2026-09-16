"""Write the D2 pre-rho formula pin (A7R3-F3 binding carry).

Pins the EXACT construction of the anchor and every shadow series BEFORE
any rho is computed.  Self-hashed.  After this artifact is committed, any
divergence between the measured series and these formulas makes D2
INVALID (fail-closed) — never PASS.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time

CTL = pathlib.Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng5/integration/research/control/stocks_ng5_run")


def main() -> int:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    pin = {
        "schema": "stocks_ng5_d2_pre_rho_formula_pin@1",
        "cycle_id": "STOCKS-NG5",
        "frozen_at_utc": ts,
        "authority_chain": [
            "plans/PLAN_stocks_ng5.md §5-§8 + §3 amendment (11 gates)",
            "d1_proposal_freeze.json (sha a59af382...)",
            "d2_shadow_inventory_freeze_v2.json (self_hash f3c33831...)",
            "p0_addendum_representation_reconciliation_v2.json (reindex, grid start 2006-04-28)",
            "A7 m0-implementation audit AUTHORIZED 0 HIGH/CRITICAL + A7R3-F3 binding carry",
        ],
        "law": "measured series MUST match these formulas exactly; any divergence => D2 INVALID/NOT_RUN, never PASS; thresholds immovable (0.20 pooled |rho|, M0 contract sha 8b5ee44b)",
        "grid": {
            "weekly_observation": "an ISO week yields ONE observation iff all four symbols have an adjusted close at the week's LAST available session date that week; observation values are the four adjusted closes at that date",
            "grid_start": "2006-04-28 (first complete weekly observation)",
            "hole_handling": "weeks failing the all-four rule yield NO observation (exactly one in-window: the ISO week containing 2008-11-28) — no imputation, no forward-fill; the anchor's book is SKIP-AND-HOLD across skipped decisions",
            "expected_size": "5,129 weekly-grid candidates collapse to 5,128 complete weekly observations... CORRECTION: 5,130 XNYS sessions / 5,129 sessions with all four symbols; weekly observations ~= 20 years x 52 - 1 skipped week, exact count recorded by the measurement run",
        },
        "conventions": {
            "zscore_104": "z(x)_t = (x_t - mean(trailing_104_complete_obs incl. t)) / std_population(trailing_104_complete_obs incl. t); undefined until 104 complete observations exist",
            "Lw_change": "chg_L(x)_t = x_t / x_{t-L} - 1 on complete weekly observations (L in complete observations: 13w = 13 obs, 52w = 52 obs)",
            "ax2_as_of_macro": "a macro observation dated d is AVAILABLE for decisions strictly after d+1 calendar day (conservative +1 day); the value used at decision t is the last observation with (obs_date + 1 day) <= t",
            "alignment": "each (anchor, shadow) rho is measured on the PAIRWISE overlap of their valid (post-warmup) observation sets; the overlap size is recorded per shadow; no re-windowing after seeing any number",
            "pooled_rho": "max(|weight-Pearson|, |weight-Spearman(midrank)|, |signal-rank-Spearman(midrank)|) via the M0 contract primary_comparisons; weights = sign(state) except the deterministic calendar shadows whose raw value IS both signal and sign state per the per-shadow spec",
            "kill_rule": "ANY shadow pooled_rho > 0.20 => ANCESTRY_VETO, selection empty, cycle closes 0/3",
        },
        "anchor": {
            "id": "ANCHOR-TREND-L13",
            "signal": "a_t = z104( chg_13w(spread)_t ), spread_t = log(qqew_adj/qqq_adj) + log(rsp_adj/spy_adj) at the observation date",
            "weights": "w_t = sign(a_t)",
        },
        "shadows": [
            {"id": "SH-A1-RELMOM-13W", "signal": "z104( chg_13w( log(QQQ_adj/SPY_adj) ) )", "weights": "sign(signal)"},
            {"id": "SH-A1b-RELMOM-52W", "signal": "z104( chg_52w( log(QQQ_adj/SPY_adj) ) )", "weights": "sign(signal)"},
            {"id": "SH-A2-ABSMOM-63D", "signal": "z104( QQQ total return over the trailing 63 SESSIONS ending at the observation date )", "weights": "sign(signal)"},
            {"id": "SH-A2b-ABSMOM-252D", "signal": "z104( QQQ total return over the trailing 252 SESSIONS )", "weights": "sign(signal)"},
            {"id": "SH-A3-VOLLEVEL-21S", "signal": "z104( population std of QQQ daily log returns over the trailing 21 SESSIONS )", "weights": "sign(signal)"},
            {"id": "SH-A3b-VOLLEVEL-52W", "signal": "z104( population std of QQQ daily log returns over the trailing 252 SESSIONS )", "weights": "sign(signal)"},
            {"id": "SH-A4-DOLLARVOL", "signal": "z104( median of QQQ dollar volume (adj_close*volume) over the trailing 63 SESSIONS )", "weights": "sign(signal)"},
            {"id": "SH-A5-DOW", "signal": "ordinal ISO weekday of the observation date (Mon=1..Fri=5), deterministic, NOT z-scored", "weights": "sign(signal-3) (above/below mid-week)"},
            {"id": "SH-A5b-WEEKPARITY", "signal": "+1 if ISO week number is odd else -1, deterministic, NOT z-scored", "weights": "= signal"},
            {"id": "SH-A5c-MONTHEND", "signal": "observation_date minus the nearest month-end calendar day, SIGNED in days (negative before month-end, positive after), deterministic, NOT z-scored", "weights": "sign(signal)"},
            {"id": "SH-A6-QQQHEAT", "signal": "z104( QQQ chg_13w return )", "weights": "sign(QQQ chg_13w return) — the R2/A6 decomposition book"},
            {"id": "SH-A7a-ROLLBETA-63S", "signal": "z104( rolling OLS beta of QQQ daily log returns on SPY daily log returns over the trailing 63 SESSIONS )", "weights": "sign(signal)"},
            {"id": "SH-A8a-DFII10-SHOCK-13W", "signal": "z104( chg_13w( DFII10 ) ) on the AX2-as-of weekly macro series", "weights": "sign(signal)"},
            {"id": "SH-A8b-DGS10-LEVEL-13W", "signal": "z104( DGS10 LEVEL ) on the AX2-as-of weekly macro series (the #14/#15 lineage shadow)", "weights": "sign(signal)"},
            {"id": "SH-A9-DIV-DECOMP", "signal": "TWO sub-shadows: (a) z104( chg_13w( price_only_spread ) ) with price_only_spread = log(QQEW_close/QQQ_close)+log(RSP_close/SPY_close) using UNADJUSTED closes; (b) z104( chg_13w( distribution_only ) ) with distribution_only = adjusted_spread - price_only_spread", "weights": "sign of each sub-shadow's signal; BOTH must clear 0.20 independently"},
            {"id": "SH-A9b-TRENDDEF-GEOM", "signal": "z104( QQQ chg_52w return )", "weights": "sign(QQQ chg_52w return) — the SFV2-A5 book geometry"},
            {"id": "SH-A10-MNQ-CAUSAL-TEMPLATE", "signal": "NO MEASUREMENT — binding template rule (no index-level causal rescue); carried in the verdict text", "weights": "n/a"},
        ],
        "feasibility_non_scored": {
            "decision_counts": "total + per-fold weekly decision counts (folds per fold_freeze.json mapped to the weekly grid)",
            "turnover": "fraction of consecutive decision pairs where w changes (per arm)",
            "cost_ceiling": "band A 10bps/fill (P0 measured), 2 fills/rotation, ~52 rotations/yr => ~1,040bps/yr base; stress 2.0 => ~2,080bps/yr; pre-registered in plan F6 — never re-derived",
            "no_returns": "D2 computes NO candidate returns/PnL/PF/Sharpe of the anchor anywhere",
        },
    }
    pin["self_hash_note"] = "self_hash = sha256 of this JSON with self_hash field empty"
    copy = dict(pin)
    copy["self_hash"] = ""
    blob = json.dumps(copy, indent=1, sort_keys=True).encode()
    pin["self_hash"] = hashlib.sha256(blob).hexdigest()
    out = CTL / "d2/d2_pre_rho_formula_pin.json"
    out.write_text(json.dumps(pin, indent=1, sort_keys=True) + "\n")
    print("pre-rho formula pin written; self_hash", pin["self_hash"][:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
