"""Stage-B PORTFOLIO ASSEMBLY — PC12A (TRAIN folds ONLY, label TRAIN-ONLY).

Turns the Stage-A survivor slate into ONE frozen portfolio policy. Laws:

- TRAIN-ONLY partition (wave-2 arithmetic, unchanged): every PnL window is
  [first campaign Friday, fold_k.train_end] of the frozen 8-fold expanding
  walk-forward; the stream ends at fold 7's train_end (2025-06-20), 14 days
  before test fold 7 starts (2025-07-04); test folds and the sealed 26w
  tail are NEVER computed on. Asserted here and in
  tests/test_pc12a_stageB.py.
- The portfolio engine nets legs PER-ASSET (L4 risk-weight vote over the
  legs' standing desired units, truncated to +/-1 lot), applies the
  Stage-B frozen L5 caps (per-asset net + co-movement cluster; every
  multi-leg cluster of this slate is single-asset, asserted at freeze) and
  the L6 cost guard (shared across the symbol engines, PIT-windowed).
  Ties and supermajority blocks mean "asset FLAT this decision" per
  architecture §4 — the flatten EXECUTES (risk-reducing close,
  guard-exempt). Disclosed deviation from the dry-run engine's
  early-return (which left the book unchanged on ties; no-PnL engine,
  never fired solo).
- E2-strict eligibility (variant axis): fold-boundary recompute of the
  leg's paper (sum-of-legs) expectancy over the trailing <=2 COMPLETED
  folds; <= 0 -> the leg stands aside (desire zeroed) until the next
  fold boundary. Prior-fold data only — never current-fold PnL (E5 /
  GROUPING_PROPOSAL 3.6; feature ids pass the blacklist).
- <=8 variants over {eligibility baseline vs +E2} x {full-vote vs
  supermajority-2/3 netting} x {architecture-default vs TRAIN-tightened
  caps}. ONE winner by the frozen deflated TRAIN objective; no iteration
  beyond the grid (selection-on-test by stealth is the named failure
  mode; the grid is closed).
- Objective (frozen, PASS_BARS_V2 §4 obj semantics): weekly portfolio
  equity over the fold-7 TRAIN prefix,
  obj = netPnL - W*SR0*sigma_w - 1.0*maxDD  (== W*(SR_hat - SR0)*sigma_w
  - maxDD), SR0 from the FULL ledger to date (N arms / N_eff clusters /
  V of the diag legs' weekly Sharpes). Degenerate (never trades) ->
  obj = -maxDD (= 0). Negative/degenerate winners are frozen anyway with
  the honest label.
- Ledger budget: 8 B-VARIANT rows + 1 freeze row, appended only at the
  end of a fully successful orchestration (stop line 1400 of 1500).

Usage (modes; orchestrate runs everything under the machine-wide heavy
lock):
    .venv/bin/python -m research.pc12a.run_stageb --mode inputs
    .venv/bin/python -m research.pc12a.run_stageb --mode ladder
    .venv/bin/python -m research.pc12a.run_stageb --mode variant --variant V1
    .venv/bin/python -m research.pc12a.run_stageb --mode select
    .venv/bin/python -m research.pc12a.run_stageb --mode repro --variant V1
    .venv/bin/python -m research.pc12a.run_stageb --mode freeze
    .venv/bin/python -m research.pc12a.run_stageb --mode orchestrate
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

from . import calendar_service as cal
from . import legs as _legs
from . import panels as _panels
from . import policy as _pol
from . import run_diag as rd
from . import run_dry as _rd

UTC = dt.timezone.utc
CYCLE = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
INITIAL_CASH = 100_000.0          # per-symbol virtual sub-account (book law)
RESIDUAL_TOL = 1e-6
LABEL = "TRAIN-ONLY"
GAMMA = 0.5772156649015329        # Euler-Mascheroni (PASS_BARS_V2 §5)
EUL = 2.718281828459045
ROOT_CHECKOUT = "/Users/hoangminhlong/my-quantitative"
WORKTREE = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
            "portfolio-composite-12assets-100k-v1/integration")
CONTROL = os.path.join(WORKTREE, "research", "control", CYCLE)
LEDGER_PATH = os.path.join(CONTROL, "TRIAL_LEDGER.jsonl")
DIAG_DIR = os.path.join(CONTROL, "diagnostics")
STAGEB_DIR = os.path.join(DIAG_DIR, "stageb")
POLICY_DIR = os.path.join(CONTROL, "policy")
INPUTS_PATH = os.path.join(STAGEB_DIR, "POLICY_INPUTS.json")
LEGS_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "legs_config")

# frozen grid (dispatch law: AT MOST 8; this IS the whole grid)
VARIANT_GRID: List[Dict] = [
    {"variant_id": f"V{i}", "eligibility": e, "netting": n, "caps": c}
    for i, (e, n, c) in enumerate([
        ("base", "full", "default"),
        ("base", "full", "tight"),
        ("base", "super", "default"),
        ("base", "super", "tight"),
        ("e2strict", "full", "default"),
        ("e2strict", "full", "tight"),
        ("e2strict", "super", "default"),
        ("e2strict", "super", "tight"),
    ], start=1)
]

SUPERMAJORITY_SHARE = 2.0 / 3.0   # conservative-netting threshold (frozen)
E2_TRAILING_FOLDS = 2             # completed folds in the trailing window
CLUSTER_CORR_THRESHOLD = 0.5      # |corr| >= .5 -> same co-movement cluster
COLOSS_TIGHTEN_THRESHOLD = 0.15   # cluster co-loss rate tightening trigger
TIGHT_PER_ASSET_NET_UNITS = 50_000  # half lot (tightened per-asset net cap)
DD_PENALTY_LAMBDA = 1.0           # objective DD penalty weight (frozen)


def _dump(path: str, obj: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, sort_keys=True, indent=1)
        fh.write("\n")


def _now() -> str:
    return dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# 1. Survivor reconciliation (from the ledger, never hardcoded)
# ---------------------------------------------------------------------------


def reconcile_survivors(ledger_path: str = LEDGER_PATH) -> Dict:
    rows = [json.loads(l) for l in open(ledger_path, encoding="utf-8")]
    diag = [r for r in rows if r["stage"] == "A-DIAG"]
    main_legs = {r["corpus_gid"] for r in diag if r.get("pass_tag") == "MAIN"}
    killed = {r["corpus_gid"] for r in diag
              if r["result"] == "COST_DOMINATED"}
    no_entries = {r["corpus_gid"] for r in diag
                  if r["result"] == "NO_ENTRIES_TRAIN"}
    survivors = sorted(main_legs - killed - no_entries)
    fold7 = {}
    for r in diag:
        if (r.get("pass_tag") == "MAIN" and r.get("fold_id") == 7
                and r["corpus_gid"] in survivors):
            fold7[r["corpus_gid"]] = r
    if len(survivors) < 3:
        raise RuntimeError(
            f"BLOCKED_NO_SLATE: {len(survivors)} survivors < 3 (owner "
            f"decision needed; a policy over <3 legs is not a portfolio)")
    if len(survivors) > 12:
        raise RuntimeError(
            f"survivor set {len(survivors)} > 12: apply the frozen "
            f"selection priority and document the cut (not expected here)")
    return {
        "n_diag_legs": len(main_legs),
        "n_cost_dominated": len(killed),
        "n_no_entries": len(no_entries),
        "survivors": survivors,
        "per_leg": [
            {"leg_id": g,
             "sleeve_id": fold7[g]["sleeve_id"],
             "cluster_id_config": fold7[g]["cluster_id"],
             "outcome_exposed_label": fold7[g]["outcome_exposed_label"],
             "arm_config_digest": fold7[g]["arm_config_digest"],
             "fold7_train_net_usd": fold7[g]["net_pnl_usd"],
             "fold7_train_cost_usd": fold7[g]["cost_total_usd"],
             "fold7_n_trades": fold7[g]["n_trades"]}
            for g in survivors],
    }


# ---------------------------------------------------------------------------
# 2. Cluster map freeze (TRAIN co-movement only)
# ---------------------------------------------------------------------------


def _union_find(pairs: List[Tuple[str, str]], nodes: List[str]) -> Dict:
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    clusters: Dict[str, List[str]] = {}
    for n in nodes:
        clusters.setdefault(find(n), []).append(n)
    return {k: sorted(v) for k, v in sorted(clusters.items())}


def freeze_cluster_map(comp_path: str, survivors: List[str]) -> Dict:
    """|corr| >= 0.5 on the fold-7 TRAIN pairwise weekly-equity correlation
    -> same cluster (union-find over survivor pairs); else singleton."""
    body = json.load(open(comp_path, encoding="utf-8"))
    pairs = body["folds"]["7"]["pairs"]
    same: List[Tuple[str, str]] = []
    evidence = []
    for key, v in pairs.items():
        a, b = key.split("|")
        if a not in survivors or b not in survivors:
            continue
        corr = v.get("corr")
        evidence.append({"pair": key, "corr": corr,
                         "co_loss_weeks": v["co_loss_weeks"],
                         "n_weeks": v["n_weeks"]})
        if corr is not None and abs(corr) >= CLUSTER_CORR_THRESHOLD:
            same.append((a, b))
    grouped = _union_find(same, sorted(survivors))
    named = {}
    for members in grouped.values():
        name = ("CM:" + members[0]) if len(members) > 1 else ("SG:" + members[0])
        named[name] = members
    return {"rule": ("|corr| >= 0.5 on fold-7 TRAIN pairwise weekly-equity "
                     "correlations (COMPLEMENTARITY_TRAIN.json), union-find; "
                     "otherwise singleton"),
            "threshold": CLUSTER_CORR_THRESHOLD,
            "fold": 7,
            "clusters": named,
            "survivor_pair_evidence": sorted(
                evidence, key=lambda e: -(abs(e["corr"]) if e["corr"]
                                          is not None else 0.0))}


# ---------------------------------------------------------------------------
# 3. L5 caps freeze (TRAIN co-drawdown) + objective inputs (SR0 from ledger)
# ---------------------------------------------------------------------------


def _solo_series(diag_dir: str) -> Dict[str, Dict[str, float]]:
    """leg_id -> {date: friday equity} on the fold-7 TRAIN prefix."""
    out = {}
    for fn in sorted(os.listdir(diag_dir)):
        if not (fn.startswith("DIAG_MAIN_") and fn.endswith(".json")):
            continue
        body = json.load(open(os.path.join(diag_dir, fn), encoding="utf-8"))
        for leg in body["legs"]:
            out[leg["leg_id"]] = leg["folds"][-1]["friday_equity"]
    return out


def _weekly_pnl(series: Dict[str, float]) -> List[float]:
    ks = sorted(series)
    return [series[ks[i]] - series[ks[i - 1]] for i in range(1, len(ks))]


def _max_dd(equities: List[float]) -> float:
    peak = equities[0] if equities else 0.0
    dd = 0.0
    for e in equities:
        peak = max(peak, e)
        dd = max(dd, peak - e)
    return dd


def _survivor_cfgs(survivors: List[str]) -> Dict[str, Dict]:
    cfgs = _legs.load_leg_configs(LEGS_CONFIG_DIR)
    return {c.get("class_candidate_id") or c["corpus_gid"]: c
            for c in cfgs if (c.get("class_candidate_id")
                              or c["corpus_gid"]) in set(survivors)}


def freeze_caps(cluster_out: Dict, survivors: List[str],
                diag_dir: str) -> Dict:
    """Co-drawdown analysis -> default (architecture §5 unit-space starting
    points) vs TRAIN-tightened caps. Rule (frozen): a multi-leg co-movement
    cluster whose max pairwise TRAIN co-loss rate >= 15% of TRAIN weeks has
    the per-asset net cap tightened to 50,000 units (half lot) on every
    asset carrying its legs, and the cluster net cap set to 50,000."""
    ev = cluster_out["survivor_pair_evidence"]
    n_weeks = max((e["n_weeks"] for e in ev), default=0)
    cfgs = _survivor_cfgs(survivors)
    tight_clusters = {}
    for name, members in cluster_out["clusters"].items():
        if len(members) < 2:
            continue
        member_set = set(members)
        pair_stats = [e for e in ev
                      if set(e["pair"].split("|")) <= member_set]
        if not pair_stats:
            continue
        worst = max(pair_stats, key=lambda e: e["co_loss_weeks"])
        rate = worst["co_loss_weeks"] / n_weeks if n_weeks else 0.0
        symbols = sorted({cfgs[m]["symbol"] for m in members})
        if len(symbols) > 1:
            raise RuntimeError(
                f"multi-asset co-movement cluster {name}: the Stage-B cap "
                f"law assumes single-asset clusters; amend before freeze")
        if rate >= COLOSS_TIGHTEN_THRESHOLD:
            tight_clusters[name] = {
                "members": members, "symbol": symbols[0],
                "max_co_loss_weeks": worst["co_loss_weeks"],
                "max_co_loss_rate": round(rate, 4),
                "worst_pair": worst["pair"]}
    tight_assets = sorted({tc["symbol"] for tc in tight_clusters.values()})
    # cluster-level combined-DD vs sum-of-DDs evidence (TRAIN, solo series)
    series = _solo_series(diag_dir)

    def _leg_dd(leg: str) -> float:
        fe = series.get(leg, {})
        return _max_dd([INITIAL_CASH] + [fe[d] for d in sorted(fe)])

    dd_evidence = []
    for name, members in cluster_out["clusters"].items():
        if len(members) < 2:
            continue
        dates = sorted(set().union(*[set(series.get(m, {}))
                                     for m in members]))
        combined = [INITIAL_CASH + sum(series[m].get(d, INITIAL_CASH)
                                       - INITIAL_CASH for m in members)
                    for d in dates]
        dd_evidence.append({
            "cluster": name, "members": members,
            "cluster_combined_dd_usd": round(_max_dd(combined), 2),
            "sum_of_individual_dd_usd": round(sum(_leg_dd(m)
                                                  for m in members), 2)})
    assets = sorted({c["symbol"] for c in cfgs.values()})
    return {
        "default": {
            "per_asset_net_units": {s: 100_000 for s in assets},
            "cluster_net_units": {name: 100_000 for name in
                                  cluster_out["clusters"]},
            "note": ("architecture §5 unit-space starting points: per-asset "
                     "one-way net = 1 lot (the registered skeleton cap)")},
        "tight": {
            "per_asset_net_units": {
                s: (TIGHT_PER_ASSET_NET_UNITS if s in tight_assets else 100_000)
                for s in assets},
            "cluster_net_units": {
                name: (TIGHT_PER_ASSET_NET_UNITS if name in tight_clusters
                       else 100_000)
                for name in cluster_out["clusters"]},
            "evidence": {"tight_clusters": tight_clusters,
                         "tight_assets": tight_assets,
                         "dd_evidence": dd_evidence,
                         "rule": ("multi-leg cluster with max pairwise TRAIN "
                                  "co-loss rate >= 15% of TRAIN weeks -> "
                                  "per-asset net cap 50k units on its asset "
                                  "+ cluster net cap 50k units")}},
    }


def freeze_sr0(ledger_path: str = LEDGER_PATH,
               diag_dir: str = DIAG_DIR) -> Dict:
    """DSR null inputs from the FULL ledger to date (PASS_BARS_V2 §5):
    N = completed deduped trials (distinct arm digests — arms, not rows);
    N_eff = distinct (sleeve, cluster-config) families + 1 for the Stage-B
    policy-variant family; V = population variance of the diag legs' weekly
    Sharpes on the fold-7 TRAIN prefix (zero-variance series excluded,
    disclosed)."""
    rows = [json.loads(l) for l in open(ledger_path, encoding="utf-8")]
    n_arms = len({r["arm_config_digest"] for r in rows})
    n_eff = len({(r.get("sleeve_id"), r.get("cluster_id")) for r in rows}) + 1
    series = _solo_series(diag_dir)
    sharpes = []
    for leg, fe in sorted(series.items()):
        rs = _weekly_pnl(fe)
        if len(rs) >= 3 and statistics.pstdev(rs) > 0:
            sharpes.append(statistics.fmean(rs) / statistics.pstdev(rs))
    v = statistics.pvariance(sharpes)
    nd = statistics.NormalDist()
    e_max = ((1 - GAMMA) * nd.inv_cdf(1 - 1 / n_eff)
             + GAMMA * nd.inv_cdf(1 - 1 / (n_eff * EUL)))
    sr0 = math.sqrt(v) * e_max
    return {
        "n_ledger_rows": len(rows), "n_arms_deduped": n_arms,
        "n_eff_clusters": n_eff, "n_sharpe_legs": len(sharpes),
        "n_series_legs": len(series), "v_trial_sharpes": round(v, 8),
        "e_max_null": round(e_max, 6), "sr0": round(sr0, 6),
        "gamma": GAMMA,
        "formula": ("E[max]=(1-g)*Phi^-1(1-1/N_eff)+g*Phi^-1(1-1/(N_eff*e));"
                    " SR0=sqrt(V)*E[max] (weekly, non-annualized)")}


# ---------------------------------------------------------------------------
# 4. Portfolio TRAIN engine (per-symbol books netted per-asset)
# ---------------------------------------------------------------------------


def clamp_l5(target: int, symbol: str, caps_cfg: Dict) -> Tuple[int,
                                                                Optional[str]]:
    """Per-asset net cap + cluster caps of the clusters whose legs trade
    this symbol (single-asset clusters; asserted at freeze)."""
    cap = caps_cfg["per_asset_net_units"].get(symbol, 100_000)
    for cid, symbols in caps_cfg.get("cluster_symbols", {}).items():
        if symbol in symbols:
            cap = min(cap, caps_cfg["cluster_net_units"][cid])
    if abs(target) > cap:
        return (cap if target > 0 else -cap), f"L5: cap {cap} units"
    return target, None


def e2_window_stats(paper_net: Dict[int, float],
                    paper_decisions: Dict[int, int],
                    paper_cost: Dict[int, float],
                    fold_by_id: Dict[int, "cal.Fold"],
                    boundary: "cal.Fold",
                    trailing: int = E2_TRAILING_FOLDS
                    ) -> Optional[float]:
    """Paper (sum-of-legs) expectancy per decision over the trailing
    `trailing` COMPLETED folds at a fold boundary; None when no decisions
    (statistic undefined -> leg stays ON, fail-open disclosed)."""
    done = [fk for fk in sorted(paper_net)
            if fold_by_id[fk].train_end <= boundary.train_end]
    window = done[-trailing:]
    decs = sum(paper_decisions.get(fk, 0) for fk in window)
    if not decs:
        return None
    nets = sum(paper_net.get(fk, 0.0) - paper_cost.get(fk, 0.0)
               for fk in window)
    return nets / decs


class SupermajorityNetting(_pol.Netting):
    """Conservative netting: the net target is taken only when the agreeing
    share |sum(d)| / sum|d| >= 2/3 (computed on the RAW vote sum — the
    +/-1-lot truncation is sizing, not disagreement); otherwise the asset
    stands FLAT this decision (SUPERMAJORITY_BLOCK, blocked-signal row)."""

    def net(self, desires: Dict[str, int]):
        out = super().net(desires)
        total_w = sum(abs(v) for v in desires.values())
        raw = sum(desires.values())
        if (total_w > 0 and out.net_target_units != 0
                and abs(raw) / total_w < SUPERMAJORITY_SHARE):
            return _pol.NettingOutcome(0, False, dict(desires), out.offsets)
        return out


class PortfolioEngine(rd.DiagEngine):
    """Multi-leg symbol engine: L4 netting across the symbol's legs with the
    variant's netting rule, L5 Stage-B caps, shared L6 guard; fold snapshots
    + Friday equity as in wave 2 (exact prefix aggregates)."""

    def __init__(self, symbol: str, cfgs: List[Dict], store, folds, tier,
                 variant: Dict, caps_cfg: Dict, guard: _pol.CostGuard):
        report = {"legs": {},
                  "cost_bill_totals_usd": {"spread_once": 0.0, "slip": 0.0,
                                           "slip_gap_excess": 0.0,
                                           "commission": 0.0, "swap": 0.0},
                  "blocked_reason_histogram": {}}
        for c in cfgs:
            lid = c.get("class_candidate_id") or c["corpus_gid"]
            report["legs"][lid] = {"decisions": 0, "votes": {},
                                   "fills_by_outcome": {}}
        args = rd._Args(folds[0].train_start, folds[-1].train_end, tier)
        _rd.SymbolEngine.__init__(self, symbol, cfgs, args, rd._DiagJournal(),
                                  guard, report)
        self.journal.engine = self
        self.diag_window_end = folds[-1].train_end
        self.diag_store = store
        self.fold_by_end = {f.train_end: f for f in folds}
        self._fold_by_id = {f.fold_id: f for f in folds}
        self.snapshots = {f.fold_id: rd.FoldSnapshot(f) for f in folds}
        self._captured_fills: List[Dict] = []
        self._staged_fills: List[Dict] = []
        self._captured_swaps: List[Dict] = []
        self._friday_equity: Dict[dt.date, float] = {}
        self._now_ts: Optional[dt.datetime] = None
        self._swap_ts: Optional[dt.datetime] = None
        self.variant = variant
        self.caps_cfg = caps_cfg
        self.netting = (SupermajorityNetting()
                        if variant["netting"] == "super" else _pol.Netting())
        # E2-strict paper (sum-of-legs shadow) book, prior folds only
        self._prev_desires = {lid: 0 for lid in self.leg_desires}
        self._paper_mark_prev: Optional[float] = None
        self._paper_fold_net: Dict[str, Dict[int, float]] = {
            lid: {} for lid in self.leg_desires}
        self._paper_fold_decisions: Dict[str, Dict[int, int]] = {
            lid: {} for lid in self.leg_desires}
        self._paper_cost_by_fold: Dict[str, Dict[int, float]] = {
            lid: {} for lid in self.leg_desires}
        self._current_fold_idx: Optional[int] = None
        self._e2_off: Dict[str, bool] = {lid: False
                                         for lid in self.leg_desires}
        self.e2_events: Dict[str, int] = {lid: 0 for lid in self.leg_desires}
        # kernel capture (staged-fill discipline as wave 2)
        orig_fill = self.kernel.price_ordinary_fill
        orig_swap = self.kernel.swap_usd

        def cap_fill(side, delta_units, bid_open, ask_open):
            fq = orig_fill(side, delta_units, bid_open, ask_open)
            signed = delta_units if side == "buy" else -delta_units
            self._staged_fills.append({
                "ts": self._now_ts, "delta": signed, "fq": fq,
                "commission": self.kernel.commission(
                    delta_units, fq.fill_price)})
            return fq

        def cap_swap(units_abs, mult, mid):
            usd = orig_swap(units_abs, mult, mid)
            if units_abs:
                self._captured_swaps.append({"ts": self._swap_ts,
                                             "usd": usd})
            return usd

        self.kernel.price_ordinary_fill = cap_fill
        self.kernel.swap_usd = cap_swap

    def _commit_staged_fill(self) -> None:
        if self._staged_fills:
            self._captured_fills.append(self._staged_fills[-1])
            self._staged_fills.clear()

    # -- day loop ------------------------------------------------------------

    def _fold_idx_at(self, date: dt.date) -> int:
        for f in sorted(self.fold_by_end.values(),
                        key=lambda x: x.train_end):
            if date <= f.train_end:
                return f.fold_id
        return max(self.fold_by_end,
                   key=lambda k: self.fold_by_end[k].train_end)

    def _process_day(self, day, date):
        self._swap_ts = dt.datetime.combine(date, dt.time(22, 0), tzinfo=UTC)
        self._current_fold_idx = self._fold_idx_at(date)
        _rd.SymbolEngine._process_day(self, day, date)
        mark = self.last_mid_close
        if mark is not None and date.strftime("%a") == "Fri":
            self._friday_equity[date] = self.cash \
                + self.book_units * float(mark)
            if self._paper_mark_prev is not None:
                fk = self._current_fold_idx
                for lid, des in self.leg_desires.items():
                    net = self._paper_fold_net[lid].get(fk, 0.0) \
                        + des * (float(mark) - self._paper_mark_prev)
                    self._paper_fold_net[lid][fk] = net
            self._paper_mark_prev = float(mark)
        fold = self.fold_by_end.get(date)
        if fold is not None:
            self._take_snapshot(fold)
            if self.variant["eligibility"] == "e2strict":
                self._e2_boundary(fold)

    def _e2_boundary(self, fold) -> None:
        """Recompute E2 states from COMPLETED prior folds only (fold-lock
        law): trailing <=2 completed folds' paper expectancy per decision
        <= 0 -> stand aside (desire zeroed) until the next boundary."""
        for lid in self.leg_desires:
            _pol.assert_features_lawful(
                [f"e2_paper_expectancy_prior_folds:{lid}"])
            exp = e2_window_stats(self._paper_fold_net[lid],
                                  self._paper_fold_decisions[lid],
                                  self._paper_cost_by_fold[lid],
                                  self._fold_by_id, fold)
            off = exp is not None and exp <= 0.0
            if off and not self._e2_off[lid]:
                self.e2_events[lid] += 1
            self._e2_off[lid] = off

    def _take_snapshot(self, fold) -> None:
        snap = self.snapshots[fold.fold_id]
        snap.n_decisions = sum(v["decisions"]
                               for v in self.report["legs"].values())
        end_ts = dt.datetime.combine(fold.train_end, dt.time(23, 59, 59),
                                     tzinfo=UTC)
        snap.fills = [f for f in self._captured_fills if f["ts"] <= end_ts]
        snap.swaps = [s for s in self._captured_swaps if s["ts"] <= end_ts]
        snap.mark = float(self.last_mid_close or 0.0)
        snap.units = int(self.book_units)
        snap.cash = float(self.cash)
        snap.friday_equity = {d: v for d, v in self._friday_equity.items()
                              if d <= fold.train_end}

    # -- decisions: eligibility (E1/E3/E4 + variant E2), L4 netting,
    #    L5 caps, L6 guard, fills. Ties/blocks -> target FLAT EXECUTED
    #    (architecture §4; deviation from the dry-run early-return,
    #    disclosed).
    # ----------------------------------------------------------------------

    def _apply_decisions(self, decisions, ts, day, m):
        self._now_ts = ts
        try:
            self._apply_decisions_stageb(decisions, ts, day, m)
        finally:
            self._paper_charge_switching(day, m)
            self._staged_fills.clear()

    def _apply_decisions_stageb(self, decisions, ts, day, m) -> None:
        if self.first_decision_ts is None:
            for st in self.leg_stats.values():
                st.leg_start_ts = ts
            self.first_decision_ts = ts
        eligible: Dict = {}
        for lid in sorted(decisions):
            dec = decisions[lid]
            st = self.leg_stats[lid]
            st.decisions_total += 1
            self.report["legs"][lid]["decisions"] += 1
            v = self.report["legs"][lid]["votes"]
            v[str(dec.vote)] = v.get(str(dec.vote), 0) + 1
            fk = self._current_fold_idx
            if fk is not None:
                self._paper_fold_decisions[lid][fk] = \
                    self._paper_fold_decisions[lid].get(fk, 0) + 1
            if self.variant["eligibility"] == "e2strict" and self._e2_off[lid]:
                self.leg_desires[lid] = 0
                self._leg_outcome(lid, "E2_STAND_ASIDE")
                self._hist("E2_STAND_ASIDE")
                continue
            elig = self.eligibility.evaluate(lid, st,
                                             dec.feature_pit_snapshot, ts)
            if elig.state != "ON":
                outcome = {"E1": "BLOCKED_FLOOR", "E3": "BLOCKED_STALE",
                           "E4": "BLOCKED_COST_BUDGET"}.get(
                               elig.rule_id or "", "BLOCKED_FLOOR")
                self._leg_outcome(lid, outcome)
                self._hist(outcome)
                continue
            eligible[lid] = dec
            self.leg_desires[lid] = dec.desired_units
        if not decisions:
            return
        if not eligible:
            # frozen engine law (run_dry): no eligible leg this decision ->
            # no action; standing desires and the book stay unchanged
            return

        net = self.netting.net(dict(self.leg_desires))
        block_reason = None
        if net.tie_zero:
            block_reason = "L4 tie: nonzero votes net to 0 -> asset FLAT"
            for lid in eligible:
                self._leg_outcome(lid, "NETTED_TO_ZERO")
                self._hist("NETTED_TO_ZERO")
        elif (self.variant["netting"] == "super"
              and net.net_target_units == 0
              and any(dv != 0 for dv in self.leg_desires.values())):
            block_reason = ("L4 supermajority: agreeing share < 2/3 -> "
                            "asset FLAT this decision")
            for lid in eligible:
                self._leg_outcome(lid, "SUPERMAJORITY_BLOCK")
                self._hist("SUPERMAJORITY_BLOCK")
        target = int(net.net_target_units)

        # L5: per-asset net cap + cluster caps (single-asset clusters)
        clamped, cap_reason = clamp_l5(target, self.symbol, self.caps_cfg)
        if clamped != target:
            for lid in eligible:
                self._leg_outcome(lid, "BLOCKED_RISK_CAP")
                self._hist("BLOCKED_RISK_CAP")
        target = int(clamped)
        delta = int(round(target - self.book_units))
        if delta == 0:
            return

        # L6 cost guard (shared across symbols; PIT windowed)
        if m >= 0:
            bid_c, ask_c = float(day.bid.close[m]), float(day.ask.close[m])
        else:
            agg = self.prev_day_agg or {}
            c = agg.get("day_close", self.last_mid_close or 1.0)
            bid_c = agg.get("last_bid_close", c)
            ask_c = agg.get("last_ask_close", c)
        side = "buy" if delta > 0 else "sell"
        est = self.kernel.estimate_all_in(side, abs(delta), bid_c, ask_c)
        verdict = self.guard.evaluate(ts, int(self.book_units), target,
                                      est["est_total_usd"])
        if not verdict.allow:
            for lid in eligible:
                self._leg_outcome(lid, "DEFERRED_COST_GUARD")
                self._hist("DEFERRED_COST_GUARD")
            return

        fb = self._fill_bar_index(day, m)
        if fb is None:
            for lid in eligible:
                self._leg_outcome(lid, "UNAVAILABLE_FILL_BAR")
                self._hist("UNAVAILABLE_FILL_BAR")
            return
        fq = self.kernel.price_ordinary_fill(side, abs(delta),
                                             float(day.bid.open[fb]),
                                             float(day.ask.open[fb]))
        commission = self.kernel.commission(abs(delta), fq.fill_price)
        spread_pips = (float(day.ask.open[fb])
                       - float(day.bid.open[fb])) / self.kernel.pip
        w4 = _pol.w4_check({f"{self.symbol}_mid_range": fq.mid_at_fill,
                            "spread_pips_max": spread_pips})
        if w4 is not None:
            for lid in eligible:
                self._leg_outcome(lid, "KILLSWITCH_FLAT")
                self._hist("W4_UNSEEN_STRUCTURE")
            return
        ts_fill = dt.datetime.combine(ts.date(), dt.time(0, 0), tzinfo=UTC) \
            + dt.timedelta(minutes=fb)
        self.book_units += delta
        if delta > 0:
            self.cash -= delta * fq.fill_price + commission
        else:
            self.cash += (-delta) * fq.fill_price - commission
        self.order_seq += 1
        cost_total = (fq.spread_once_usd
                      + fq.slip_beyond_halfspread_usd + commission)
        self.report["cost_bill_totals_usd"]["spread_once"] += \
            fq.spread_once_usd
        self.report["cost_bill_totals_usd"]["slip"] += \
            fq.slip_beyond_halfspread_usd
        self.report["cost_bill_totals_usd"]["commission"] += commission
        if fq.gap_excess_pips > 0:
            self.report["cost_bill_totals_usd"]["slip_gap_excess"] += \
                fq.gap_excess_pips * self.kernel.pip * abs(delta)
        self.guard.record_spend(ts, cost_total)
        for lid in sorted(eligible):
            self._leg_outcome(lid, "FILLED")
            st = self.leg_stats[lid]
            st.decision_events.append(ts)
            st.decision_count_trailing += 1
            st.cost_events.append((ts, cost_total * self._leg_share(lid)))
        self.journal.write("NET_ORDER", {
            "order_id": f"{self.symbol}-o{self.order_seq:05d}",
            "order_kind": (eligible[min(eligible)].order_kind
                           or "OPEN"),
            "ts_fill_utc": ts_fill.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "symbol": self.symbol, "side": side, "delta_units": delta,
            "net_target_units": net.net_target_units,
            "block_reason": block_reason,
            "contributing_legs": sorted(eligible),
            "units_after": self.book_units,
            "cost_total_usd": round(cost_total, 6)})

    def _paper_charge_switching(self, day, m) -> None:
        """Paper (sum-of-legs) switching cost on desire changes, priced at
        the decision path's quotes (bar closes; midnight decisions use the
        first tradable bar's opens — the same bars the real fills use)."""
        if day is None:
            return
        bid_c = ask_c = None
        if m is not None and m >= 0:
            bid_c, ask_c = float(day.bid.close[m]), float(day.ask.close[m])
        else:
            tradable = day.tradable_mask()
            for mm in range(len(tradable)):
                if tradable[mm] and day.bid.open[mm] > 0:
                    bid_c, ask_c = (float(day.bid.open[mm]),
                                    float(day.ask.open[mm]))
                    break
        if bid_c is None:
            return
        fk = self._current_fold_idx
        if fk is None:
            return
        for lid, des in self.leg_desires.items():
            delta = des - self._prev_desires[lid]
            if delta != 0:
                side = "buy" if delta > 0 else "sell"
                est = self.kernel.estimate_all_in(side, abs(delta),
                                                  bid_c, ask_c)
                self._paper_cost_by_fold[lid][fk] = \
                    self._paper_cost_by_fold[lid].get(fk, 0.0) \
                    + est["est_total_usd"]
            self._prev_desires[lid] = des

    def _hist(self, key: str) -> None:
        h = self.report["blocked_reason_histogram"]
        h[key] = h.get(key, 0) + 1

    def _leg_outcome(self, lid: str, outcome: str) -> None:
        d = self.report["legs"][lid]["fills_by_outcome"]
        d[outcome] = d.get(outcome, 0) + 1


# ---------------------------------------------------------------------------
# 5. Variant runner + objective
# ---------------------------------------------------------------------------


def run_variant(variant: Dict, inputs: Dict, folds: List[cal.Fold],
                tier: float = 1.0) -> Tuple[Dict, List[Tuple[dt.datetime,
                                                            float]]]:
    caps_key = "tight" if variant["caps"] == "tight" else "default"
    caps_cfg = dict(inputs["caps"][caps_key])
    cfgs_all = _survivor_cfgs(inputs["survivors"])
    caps_cfg["cluster_symbols"] = {
        cid: sorted({cfgs_all[m]["symbol"] for m in members
                     if m in cfgs_all})
        for cid, members in inputs["cluster_map"]["clusters"].items()}
    by_symbol: Dict[str, List[Dict]] = {}
    for lid, c in sorted(cfgs_all.items()):
        by_symbol.setdefault(c["symbol"], []).append(c)
    guard = _pol.CostGuard(
        _pol.CostGuardState(cap_usd=inputs["guard"]["cap_usd"]))
    per_symbol = {}
    digests = {}
    for symbol in sorted(by_symbol):
        store = _panels.PanelStore()
        digests[symbol] = rd._symbol_digest(store, symbol, folds)
        eng = PortfolioEngine(symbol, by_symbol[symbol], store, folds, tier,
                              variant, caps_cfg, guard)
        eng.run(store)
        finalized = []
        for f in folds:
            snap = eng.snapshots[f.fold_id]
            eps = rd._episodes(snap.fills)
            fin = snap.finalize(eps)
            assert abs(fin["residual_usd"]) < RESIDUAL_TOL, \
                f"{symbol} fold {f.fold_id} residual {fin['residual_usd']}"
            finalized.append(fin)
        per_symbol[symbol] = {
            "folds": finalized,
            "friday_equity_fold7": {
                d.isoformat(): v for d, v in
                eng.snapshots[folds[-1].fold_id].friday_equity.items()},
            "blocked_reason_histogram":
                eng.report["blocked_reason_histogram"],
            "cost_bill_totals_usd": eng.report["cost_bill_totals_usd"],
            "e2_events": eng.e2_events}
    pf_folds = []
    for f in folds:
        agg = {"fold_id": f.fold_id,
               "train_window": [f.train_start.isoformat(),
                                f.train_end.isoformat()],
               "net_pnl_usd": 0.0, "gross_pnl_usd": 0.0,
               "cost_total_usd": 0.0, "n_fills": 0, "n_entries": 0,
               "n_decisions": 0}
        for symbol in sorted(per_symbol):
            ff = per_symbol[symbol]["folds"][f.fold_id]
            agg["net_pnl_usd"] += ff["net_pnl_usd"]
            agg["gross_pnl_usd"] += ff["gross_pnl_usd"]
            agg["cost_total_usd"] += ff["cost_total_usd"]
            agg["n_fills"] += ff["n_fills"]
            agg["n_entries"] += ff["n_entries"]
            agg["n_decisions"] += ff["n_decisions"]
        for k in ("net_pnl_usd", "gross_pnl_usd", "cost_total_usd"):
            agg[k] = round(agg[k], 6)
        pf_folds.append(agg)
    weekly = _portfolio_weekly(per_symbol)
    obj = train_objective(weekly, inputs["sr0"]["sr0"])
    hist: Dict[str, int] = {}
    for symbol in sorted(per_symbol):
        for k, v in per_symbol[symbol]["blocked_reason_histogram"].items():
            hist[k] = hist.get(k, 0) + v
    e2 = ({s: per_symbol[s]["e2_events"] for s in sorted(per_symbol)}
          if variant["eligibility"] == "e2strict" else None)
    res = {
        "schema": "pc12a_stageb_variant@1", "label": LABEL,
        "variant_id": variant["variant_id"], "variant_config": variant,
        "tier": tier, "max_train_end": folds[-1].train_end.isoformat(),
        "data_digests": digests,
        "folds": pf_folds,
        "weekly_equity_fold7": {d: round(v, 6) for d, v in weekly.items()},
        "objective": obj,
        "blocked_reason_histogram": hist,
        "guard": {"cap_usd": inputs["guard"]["cap_usd"],
                  "n_events": len(guard.state.spend),
                  "total_spend_usd": round(
                      sum(c for _, c in guard.state.spend), 2)},
        "e2_stand_aside_events": e2,
        "per_symbol_folds": {s: per_symbol[s]["folds"]
                             for s in sorted(per_symbol)},
        "code_digest": _rd._code_digest()}
    return res, list(guard.state.spend)


def _portfolio_weekly(per_symbol: Dict) -> Dict[str, float]:
    """Portfolio Friday equity: 100k + sum of per-symbol sub-account PnL,
    each symbol forward-filled from its own last Friday mark."""
    dates = sorted(set().union(*[set(v["friday_equity_fold7"])
                                 for v in per_symbol.values()]))
    out: Dict[str, float] = {}
    last = {s: INITIAL_CASH for s in per_symbol}
    for d in dates:
        eq = 100_000.0
        for s in sorted(per_symbol):
            fe = per_symbol[s]["friday_equity_fold7"]
            if d in fe:
                last[s] = fe[d]
            eq += last[s] - INITIAL_CASH
        out[d] = eq
    return out


def train_objective(weekly: Dict[str, float], sr0: float) -> Dict:
    """Frozen Stage-B objective (PASS_BARS_V2 §4 obj): deflated net PnL
    with DD penalty on the fold-7 TRAIN weekly portfolio path:
    obj = W*(SR_hat - SR0)*sigma_w - lambda*maxDD, lambda = 1.0
    (== netPnL - W*SR0*sigma_w - maxDD). Degenerate (sigma_w == 0):
    SR_hat := 0, deflated term 0."""
    dates = sorted(weekly)
    eq = [weekly[d] for d in dates]
    rs = [eq[i] - eq[i - 1] for i in range(1, len(eq))]
    n = len(rs)
    net = (eq[-1] - eq[0]) if eq else 0.0
    maxdd = _max_dd(eq)
    if n >= 2 and statistics.pstdev(rs) > 0:
        std = statistics.pstdev(rs)
        sr = statistics.fmean(rs) / std
    else:
        std, sr = 0.0, 0.0
    defl = n * sr0 * std
    obj = net - defl - DD_PENALTY_LAMBDA * maxdd
    return {"n_weeks": n, "net_pnl_usd": round(net, 6),
            "max_dd_usd": round(maxdd, 6),
            "weekly_mean_usd": round(statistics.fmean(rs), 6)
            if rs else 0.0,
            "weekly_std_usd": round(std, 6), "sr_hat": round(sr, 6),
            "sr0": sr0, "deflation_term_usd": round(defl, 6),
            "dd_penalty_usd": round(DD_PENALTY_LAMBDA * maxdd, 6),
            "objective_usd": round(obj, 6),
            "degenerate": std == 0.0}


# ---------------------------------------------------------------------------
# 6. CLI modes
# ---------------------------------------------------------------------------


def _load_inputs() -> Dict:
    return json.load(open(INPUTS_PATH, encoding="utf-8"))


def _mode_inputs() -> Dict:
    surv = reconcile_survivors()
    cluster = freeze_cluster_map(
        os.path.join(DIAG_DIR, "COMPLEMENTARITY_TRAIN.json"),
        surv["survivors"])
    caps = freeze_caps(cluster, surv["survivors"], DIAG_DIR)
    sr0 = freeze_sr0()
    inputs = {
        "schema": "pc12a_stageb_inputs@1", "label": LABEL,
        "frozen_utc": _now(),
        "survivor_reconciliation": surv,
        "survivors": surv["survivors"],
        "cluster_map": cluster,
        "caps": caps,
        "sr0": sr0,
        "guard": {"window_days": 28, "cap_usd": None,
                  "source": "pending ladder pass"},
        "variant_grid": VARIANT_GRID,
        "objective_law": {
            "formula": ("obj = netPnL_TRAIN - W*SR0*sigma_w - 1.0*maxDD_TRAIN"
                        " (== W*(SR_hat-SR0)*sigma_w - maxDD), weekly marks,"
                        " fold-7 TRAIN prefix"),
            "dd_penalty_lambda": DD_PENALTY_LAMBDA},
        "engine_semantics": {
            "tie_or_block": ("asset FLAT this decision, flatten EXECUTES "
                             "(architecture §4; disclosed deviation from "
                             "the dry-run early-return)"),
            "e2": ("fold-boundary recompute over trailing <=2 completed "
                   "folds of the leg's paper (sum-of-legs) expectancy; "
                   "<= 0 -> stand aside (desire 0) until next boundary"),
            "supermajority": ("agreeing share |sum d|/sum|d| >= 2/3 "
                              "required to hold the net target, else FLAT")}}
    _dump(INPUTS_PATH, inputs)
    print(json.dumps({"mode": "inputs", "survivors": len(surv["survivors"]),
                      "clusters": {k: len(v) for k, v in
                                   cluster["clusters"].items()},
                      "sr0": sr0["sr0"]}))
    return inputs


def _percentile(vals: List[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = q * (len(s) - 1)
    lo, hi = int(math.floor(idx)), int(math.ceil(idx))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (idx - lo)


def _trailing28d_series(spends: List[Tuple[dt.datetime, float]],
                        window_days: int = 28) -> List[float]:
    """Trailing-window spend evaluated at every spend instant, PIT-strict
    (only spends <= the instant enter the sum; same law as the guard)."""
    out = []
    for i, (ts, _) in enumerate(spends):
        wstart = ts - dt.timedelta(days=window_days)
        out.append(sum(c for t, c in spends[:i + 1] if wstart < t <= ts))
    return out


def _mode_ladder() -> None:
    inputs = _load_inputs()
    folds = cal.fold_calendar()
    ladder_variant = {"variant_id": "LADDER", "eligibility": "base",
                      "netting": "full", "caps": "default"}
    work = json.loads(json.dumps(inputs))     # deep copy
    work["guard"] = dict(work["guard"])
    work["guard"]["cap_usd"] = float("inf")
    res, spends = run_variant(ladder_variant, work, folds)
    vals = _trailing28d_series(spends)
    p90 = _percentile(vals, 0.90)
    p50 = _percentile(vals, 0.50)
    inputs["guard"] = {
        "window_days": 28,
        "cap_usd": round(p90, 2),
        "source": ("TRAIN switching-cost ladder: p90 of the trailing-28d "
                   "state-change spend series on the LADDER pass (base "
                   "eligibility, full netting, default caps, guard "
                   "disabled), measured over "
                   f"{len(vals)} spend instants"),
        "ladder": {"n_events": len(vals),
                   "p50_trailing28d_usd": round(p50, 2),
                   "p90_trailing28d_usd": round(p90, 2),
                   "total_spend_usd": round(sum(c for _, c in spends), 2)}}
    _dump(INPUTS_PATH, inputs)
    _dump(os.path.join(STAGEB_DIR, "LADDER.json"),
          {"schema": "pc12a_stageb_ladder@1", "label": LABEL,
           "variant": ladder_variant, "folds": res["folds"],
           "objective": res["objective"], "guard": inputs["guard"],
           "code_digest": res["code_digest"], "data_digests":
               res["data_digests"]})
    print(json.dumps({"mode": "ladder", "p90": round(p90, 2),
                      "p50": round(p50, 2), "n": len(vals)}))


def _mode_variant(vid: str, suffix: str = "") -> None:
    inputs = _load_inputs()
    variant = next(v for v in VARIANT_GRID if v["variant_id"] == vid)
    folds = cal.fold_calendar()
    t0 = time.time()
    res, _spends = run_variant(variant, inputs, folds)
    path = os.path.join(STAGEB_DIR, f"VARIANT_{vid}{suffix}.json")
    _dump(path, res)
    print(json.dumps({"mode": "variant", "variant": vid,
                      "obj": res["objective"]["objective_usd"],
                      "net": res["objective"]["net_pnl_usd"],
                      "maxdd": res["objective"]["max_dd_usd"],
                      "elapsed": round(time.time() - t0, 1)}))


def _mode_repro(vid: str) -> None:
    _mode_variant(vid, suffix="_REPRO")
    a = open(os.path.join(STAGEB_DIR, f"VARIANT_{vid}.json"), "rb").read()
    b = open(os.path.join(STAGEB_DIR, f"VARIANT_{vid}_REPRO.json"),
             "rb").read()
    print(json.dumps({"mode": "repro", "variant": vid,
                      "byte_identical": a == b}))


def _mode_select() -> Dict:
    ranking = []
    for v in VARIANT_GRID:
        body = json.load(open(os.path.join(
            STAGEB_DIR, f"VARIANT_{v['variant_id']}.json"),
            encoding="utf-8"))
        ranking.append({"variant_id": v["variant_id"],
                        "objective_usd": body["objective"]["objective_usd"],
                        "net_pnl_usd": body["objective"]["net_pnl_usd"],
                        "max_dd_usd": body["objective"]["max_dd_usd"],
                        "sr_hat": body["objective"]["sr_hat"],
                        "degenerate": body["objective"]["degenerate"]})
    ranked = sorted(ranking,
                    key=lambda x: (-x["objective_usd"], -x["net_pnl_usd"],
                                   x["max_dd_usd"], x["variant_id"]))
    sel = {"schema": "pc12a_stageb_selection@1", "label": LABEL,
           "tie_break": ("higher objective, then higher net, then lower "
                         "maxDD, then variant id"),
           "ranking": ranked, "winner": ranked[0]["variant_id"]}
    _dump(os.path.join(STAGEB_DIR, "SELECTION.json"), sel)
    print(json.dumps({"mode": "select", "winner": sel["winner"],
                      "ranking": ranked}))
    return sel


def _mode_freeze() -> Dict:
    inputs = _load_inputs()
    sel = json.load(open(os.path.join(STAGEB_DIR, "SELECTION.json"),
                         encoding="utf-8"))
    winner = sel["winner"]
    wbody = json.load(open(os.path.join(STAGEB_DIR,
                                        f"VARIANT_{winner}.json"),
                           encoding="utf-8"))
    repro_path = os.path.join(STAGEB_DIR, f"VARIANT_{winner}_REPRO.json")
    repro_ident = None
    if os.path.exists(repro_path):
        repro_ident = (open(os.path.join(STAGEB_DIR,
                                         f"VARIANT_{winner}.json"),
                            "rb").read()
                       == open(repro_path, "rb").read())
    surv = inputs["survivor_reconciliation"]
    caps_key = ("tight" if wbody["variant_config"]["caps"] == "tight"
                else "default")
    frozen = {
        "schema": "pc12a_policy_frozen@1",
        "cycle_id": CYCLE,
        "label": LABEL,
        "frozen_utc": _now(),
        "slate": surv["per_leg"],
        "slate_size": len(surv["survivors"]),
        "cluster_map": inputs["cluster_map"],
        "caps": inputs["caps"][caps_key],
        "caps_variant": caps_key,
        "guard": inputs["guard"],
        "eligibility": {
            "E1": {"min_decisions_26w":
                   _pol.Eligibility.E1_MIN_DECISIONS_26W,
                   "arm_weeks": _pol.Eligibility.E1_ARM_WEEKS},
            "E3": "fail-closed PIT staleness/availability (skeleton law)",
            "E4": {"window_days": _pol.Eligibility.E4_WINDOW_DAYS,
                   "cap_usd_per_leg": _pol.Eligibility.E4_CAP_USD},
            "E2": ({"rule": ("fold-boundary trailing <=2 completed folds "
                             "paper expectancy per decision <= 0 -> stand "
                             "aside (desire 0) until next boundary"),
                    "trailing_folds": E2_TRAILING_FOLDS}
                   if wbody["variant_config"]["eligibility"] == "e2strict"
                   else None),
            "E5": "no PnL-feedback inside the current fold (invariant)"},
        "netting": {
            "rule": wbody["variant_config"]["netting"],
            "semantics": ("full-vote: net = sum(desires) truncated to "
                          "+/-1 lot; supermajority: agreeing share >= 2/3 "
                          "required else FLAT; tie/block -> FLAT EXECUTED"),
            "supermajority_share": SUPERMAJORITY_SHARE},
        "variant_id": winner,
        "variant_config": wbody["variant_config"],
        "selection_statistic": wbody["objective"],
        "selection_ranking": sel["ranking"],
        "selection_tie_break": sel["tie_break"],
        "sr0_inputs": inputs["sr0"],
        "objective_law": inputs["objective_law"],
        "code_digest": wbody["code_digest"],
        "data_digests": wbody["data_digests"],
        "determinism": {"winner_byte_identical_rerun": repro_ident},
        "engine_semantics": inputs["engine_semantics"]}
    blob = json.dumps(frozen, sort_keys=True)
    frozen["policy_digest"] = hashlib.sha256(blob.encode()).hexdigest()
    _dump(os.path.join(POLICY_DIR, "POLICY_FROZEN.json"), frozen)
    print(json.dumps({"mode": "freeze", "winner": winner,
                      "policy_digest": frozen["policy_digest"],
                      "repro_identical": repro_ident}))
    return frozen


# -- ledger ----------------------------------------------------------------


def append_stageb_rows(frozen: Dict, ledger_path: str = LEDGER_PATH,
                       stop_at: int = 1400) -> int:
    folds = cal.fold_calendar()
    train_window = [folds[0].train_start.isoformat(),
                    folds[-1].train_end.isoformat()]
    n_have = rd._ledger_len(ledger_path)
    rows: List[Dict] = []
    now = _now()

    def _row(base: Dict) -> Dict:
        out = dict(base)
        out["row_id"] = f"BSTG-W1-{n_have + 1 + len(rows):04d}"
        out.setdefault("cycle_id", CYCLE)
        out.setdefault("fold_scope", "TRAIN_ONLY")
        out.setdefault("label", LABEL)
        out.setdefault("sleeve_id", "PORTFOLIO_POLICY")
        out.setdefault("cluster_id", "portfolio")
        out.setdefault("fold_id", 7)
        out.setdefault("train_window", train_window)
        out.setdefault("tier", 1.0)
        out["recorded_utc"] = now
        return out

    for rank in frozen["selection_ranking"]:
        vid = rank["variant_id"]
        vcfg = next(v for v in VARIANT_GRID if v["variant_id"] == vid)
        digest = hashlib.sha256(
            json.dumps(vcfg, sort_keys=True).encode()).hexdigest()
        rows.append(_row({
            "stage": "B-VARIANT", "corpus_gid": f"B-{vid}",
            "arm_config_digest": digest,
            "outcome_exposed_label": "TRAIN_ONLY_POLICY_VARIANT",
            "pass_tag": "VARIANT", "result": "B_VARIANT_TRAINED",
            "objective_usd": rank["objective_usd"],
            "net_pnl_usd": rank["net_pnl_usd"],
            "max_dd_usd": rank["max_dd_usd"],
            "sr_hat": rank["sr_hat"],
            "sr0": frozen["sr0_inputs"]["sr0"],
            "degenerate": rank["degenerate"],
            "detail": (f"Stage-B variant {vid} (elig={vcfg['eligibility']},"
                       f" netting={vcfg['netting']}, caps={vcfg['caps']}) "
                       f"trained on the 8-fold expanding TRAIN prefix; "
                       f"selected="
                       f"{'YES' if vid == frozen['variant_id'] else 'no'}")}))
    rows.append(_row({
        "stage": "B-FREEZE", "corpus_gid": f"B-{frozen['variant_id']}",
        "arm_config_digest": frozen["policy_digest"],
        "outcome_exposed_label": "POLICY_FROZEN_TRAIN_ONLY",
        "pass_tag": "FREEZE", "result": "POLICY_FROZEN",
        "objective_usd": frozen["selection_statistic"]["objective_usd"],
        "net_pnl_usd": frozen["selection_statistic"]["net_pnl_usd"],
        "max_dd_usd": frozen["selection_statistic"]["max_dd_usd"],
        "detail": (f"winner {frozen['variant_id']} frozen to "
                   f"policy/POLICY_FROZEN.json (slate "
                   f"{frozen['slate_size']} legs, cluster map "
                   f"{len(frozen['cluster_map']['clusters'])} clusters, "
                   f"guard cap {frozen['guard']['cap_usd']} USD); "
                   f"TRAIN-only outcome-bearing, Stage-C consumes under "
                   f"its own gates")}))
    if n_have + len(rows) > stop_at:
        raise rd.LedgerBudgetExceeded(
            f"append of {len(rows)} would take the ledger from {n_have} "
            f"past stop line {stop_at}")
    with open(ledger_path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return n_have + len(rows)


# -- heavy lock ------------------------------------------------------------


def _take_lock(command: List[str]):
    gov = os.path.join(ROOT_CHECKOUT, "research")
    if gov not in sys.path:
        sys.path.insert(0, gov)
    from governance import heavy_lock

    return heavy_lock.acquire(
        cycle_id=CYCLE, role="stage-b-portfolio-train", worktree=WORKTREE,
        command=command,
        expected_artifacts=[
            "research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/policy/"
            "POLICY_FROZEN.json"])


# -- orchestration ---------------------------------------------------------


def _spawn(cmd: List[str], log_path: str) -> subprocess.Popen:
    log = open(log_path, "a", encoding="utf-8")
    log.write(f"\n=== {' '.join(cmd)} @{_now()}\n")
    log.flush()
    return subprocess.Popen(cmd, stdout=log, stderr=log, cwd=WORKTREE)


def _run_sync(cmd: List[str], log_path: str) -> int:
    p = _spawn(cmd, log_path)
    return p.wait()


PY = [os.path.join(ROOT_CHECKOUT, ".venv", "bin", "python"), "-m",
      "research.pc12a.run_stageb"]


def _mode_orchestrate(parallel: int = 4) -> None:
    os.makedirs(STAGEB_DIR, exist_ok=True)
    log = os.path.join(STAGEB_DIR, "ORCHESTRATOR_LOG.txt")
    lock = _take_lock(PY + ["--mode", "orchestrate"])
    t0 = time.time()
    winner = None
    try:
        for step in (["--mode", "inputs"], ["--mode", "ladder"]):
            rc = _run_sync(PY + step, log)
            if rc != 0:
                raise RuntimeError(f"step {step} failed rc={rc}")
        queue = [v["variant_id"] for v in VARIANT_GRID]
        running: Dict[str, subprocess.Popen] = {}
        codes: Dict[str, int] = {}
        while queue or running:
            while queue and len(running) < parallel:
                vid = queue.pop(0)
                running[vid] = _spawn(
                    PY + ["--mode", "variant", "--variant", vid],
                    os.path.join(STAGEB_DIR, f"VARIANT_{vid}.log"))
            time.sleep(5)
            for vid in list(running):
                rc = running[vid].poll()
                if rc is not None:
                    codes[vid] = rc
                    del running[vid]
        failed = [v for v, c in codes.items() if c != 0]
        if failed:
            raise RuntimeError(f"variant runs failed: {failed}")
        rc = _run_sync(PY + ["--mode", "select"], log)
        if rc != 0:
            raise RuntimeError("select failed")
        sel = json.load(open(os.path.join(STAGEB_DIR, "SELECTION.json"),
                             encoding="utf-8"))
        winner = sel["winner"]
        rc = _run_sync(PY + ["--mode", "repro", "--variant", winner], log)
        if rc != 0:
            raise RuntimeError("repro failed")
        rc = _run_sync(PY + ["--mode", "freeze"], log)
        if rc != 0:
            raise RuntimeError("freeze failed")
        frozen = json.load(open(os.path.join(POLICY_DIR,
                                             "POLICY_FROZEN.json"),
                                encoding="utf-8"))
        total = append_stageb_rows(frozen)
        print(json.dumps({"mode": "orchestrate", "done": True,
                          "winner": frozen["variant_id"],
                          "ledger_total": total,
                          "elapsed": round(time.time() - t0, 1)}))
    except BaseException:
        if lock is not None:
            lock.release(status="FAILED", note=f"winner={winner}")
            lock = None
        raise
    finally:
        if lock is not None:
            lock.release(status="FINISHED", note=f"winner={winner}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PC12A Stage-B assembly")
    ap.add_argument("--mode", required=True,
                    choices=["inputs", "ladder", "variant", "select",
                             "repro", "freeze", "orchestrate"])
    ap.add_argument("--variant", default=None)
    args = ap.parse_args(argv)
    if args.mode == "inputs":
        _mode_inputs()
    elif args.mode == "ladder":
        _mode_ladder()
    elif args.mode == "variant":
        _mode_variant(args.variant)
    elif args.mode == "repro":
        _mode_repro(args.variant)
    elif args.mode == "select":
        _mode_select()
    elif args.mode == "freeze":
        _mode_freeze()
    elif args.mode == "orchestrate":
        _mode_orchestrate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
