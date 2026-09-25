#!/usr/bin/env python
"""ILLIQ-LOSS-MECH-V1 phase-1 locked runner (bootstrap/Lead session).

Executes EXACTLY the 8 frozen cells of Amendment A1 A1-7 under the machine
wide heavy lock (acquired here, released on exit). Each cell runs in a
subprocess with sys.path = frozen engine root only (package-isolation).
After cells: computes the frozen verdicts of A1-4 (H-A) and A1-6 (H-B incl.
INV coherence) from the artifact ledgers, writes phase1_status.json +
phase1_verdict.json. Nothing scores, nothing prospective, no variants beyond
the census; FAIL terminates its hypothesis (no iteration).

Run: .venv/bin/python research/control/illiq_loss_mech_v1/phase1_cells.py
(from the cycle worktree root).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/hoangminhlong/my-quantitative")
WORKTREE = ROOT / ".worktrees/illiq-loss-mech-v1/integration"
CTRL = WORKTREE / "research/control/illiq_loss_mech_v1"
CHR3F = ROOT / ".worktrees/crypto-historical-replication-3f-v1/integration/research/control/crypto_historical_replication_3f_v1"
CATALOG = CHR3F / "catalog_live_crypto_b20"  # catalog root with data/binance_bar
B20 = CHR3F / "catalog_live_crypto_b20/data/binance_bar"
SCAN = CHR3F / "funding_data_scan/scan_2026"
VENV_PY = ROOT / ".venv/bin/python"

sys.path.insert(0, str(ROOT))
from research.governance import heavy_lock  # noqa: E402

ANCHOR = "ILLIQ-AMIHUD-28D-W"
INV = "ILLIQ-AMIHUD-28D-W-INV"
WINDOWS = {
    "Y2022": {"window_start": "2021-12-27T00:00:00Z", "window_end": "2022-12-26T00:00:00Z",
              "fold_first": "2022-01-03", "fold_last": "2022-12-26"},
    "Y2023": {"window_start": "2022-12-26T00:00:00Z", "window_end": "2023-12-25T00:00:00Z",
              "fold_first": "2023-01-02", "fold_last": "2023-12-25"},
}
# A1-7 census — exact, ordered; AGE has no Y2022 cell (VOID_BY_CONSTRUCTION)
CELLS = [
    ("C1_BASE_ANCHOR_Y2022", "Y2022", ANCHOR, "BASELINE"),
    ("C2_BASE_ANCHOR_Y2023", "Y2023", ANCHOR, "BASELINE"),
    ("C3_BASE_INV_Y2022", "Y2022", INV, "BASELINE"),
    ("C4_BASE_INV_Y2023", "Y2023", INV, "BASELINE"),
    ("C5_V2AGE_Y2023", "Y2023", ANCHOR, "V2_AGE"),
    ("C6_V2HEDGE_Y2022", "Y2022", ANCHOR, "V2_HEDGE"),
    ("C7_V2HEDGE_Y2023", "Y2023", ANCHOR, "V2_HEDGE"),
    ("C8_INV_V2HEDGE_Y2023", "Y2023", INV, "V2_HEDGE"),
]
DECILE_TAIL_MAX_RATIO = 0.70      # A1-6(i)
MIN_NONFALLBACK_PER_FOLD = 13     # A1-6(iii)
DELTA_MAX = -0.03                 # A1-4 frozen bar (directional)
MIN_YOUNG_POSITIONS = 20          # A1-4 guard
MAX_SKIP_STAMPS_SHARE = 0.20      # A1-4 guard


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def first_bar_ns(symbol: str) -> int:
    d = B20 / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(d.glob("*.parquet"))
    head = files[0].name.split("_")[0]
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})", head)
    import datetime as dt
    return int(dt.datetime(*(int(g) for g in m.groups()),
                            tzinfo=dt.timezone.utc).timestamp() * 1e9)


def run_cells() -> dict:
    status = {"started_utc": utcnow(), "cells": []}
    for cell_id, fold, arm, variant in CELLS:
        if cell_id == "C5_V2AGE_Y2023":
            status["cells"].append({"cell": cell_id, "skipped": "NOT_RUN_VOID_CONSTRUCTION (Amendment A2: A4 universe has zero sub-365d names on Y2023; age filter is a no-op)"})
            continue
        w = WINDOWS[fold]
        out_dir = CTRL / "illiq_cells" / cell_id
        if (out_dir / "results/artifact.json").is_file():
            status["cells"].append({"cell": cell_id, "skipped": "artifact_exists"})
            continue
        cmd = [str(VENV_PY), str(CTRL / "lm_cell_runner.py"),
               "--window-start", w["window_start"], "--window-end", w["window_end"],
               "--arm-id", arm, "--variant", variant, "--out", str(out_dir),
               "--catalog", str(CATALOG), "--funding-scan", str(SCAN)]
        t0 = utcnow()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        art = out_dir / "results/artifact.json"
        row = {"cell": cell_id, "fold": fold, "arm": arm, "variant": variant,
               "started_utc": t0, "finished_utc": utcnow(),
               "rc": proc.returncode,
               "stdout": proc.stdout.strip()[-400:], "stderr_tail": proc.stderr.strip()[-800:],
               "artifact": str(art) if art.is_file() else None,
               "artifact_sha256_16": file_sha256(art)[:16] if art.is_file() else None}
        status["cells"].append(row)
        (CTRL / "phase1_status.json").write_text(json.dumps(status, indent=1, ensure_ascii=False))
        print(json.dumps(row), flush=True)
        if proc.returncode != 0 or not art.is_file():
            raise SystemExit(f"CELL_FAILED {cell_id} rc={proc.returncode}")
    status["finished_utc"] = utcnow()
    (CTRL / "phase1_status.json").write_text(json.dumps(status, indent=1, ensure_ascii=False))
    return status


def load(cell_id: str) -> dict:
    return json.load(open(CTRL / "illiq_cells" / cell_id / "results/artifact.json"))


def verdicts() -> dict:
    DAY = 86_400_000_000_000
    arts = {cid: load(cid) for cid, *_ in CELLS
            if cid != "C5_V2AGE_Y2023"}  # NOT_RUN_VOID_CONSTRUCTION (A2)
    out: dict = {"computed_utc": utcnow(), "frozen_bars": {
        "delta_max": DELTA_MAX, "decile_tail_max_ratio": DECILE_TAIL_MAX_RATIO,
        "min_nonfallback_per_fold": MIN_NONFALLBACK_PER_FOLD,
        "min_young_positions": MIN_YOUNG_POSITIONS,
        "max_skip_stamps_share": MAX_SKIP_STAMPS_SHARE}}

    # ---- headline table ----
    out["headline"] = {}
    for cid, a in arts.items():
        pm = a["portfolio_metrics"]
        out["headline"][cid] = {"net": round(pm["net_return_sum"], 6),
                                "mdd": round(pm["max_drawdown"], 6),
                                "pf": round(pm["position_pf"], 6),
                                "funding": round(pm["funding_sum"], 6),
                                "n_positions": pm["n_positions"],
                                "scored": a["scored"]}

    # ---- H-A (A1-4): delta on Y2023 baseline ANCHOR; Y2022 void check ----
    def ha_delta(art: dict, fold_start_probe: str):
        fbn = {s: first_bar_ns(s)
               for s in set(art["universe"]) | {p["symbol"] for p in art["positions"]}}
        young = defaultdict(float)
        old = defaultdict(float)
        counts = {"young_n": 0, "old_n": 0}
        for p in art["positions"]:
            if p["signed_weight"] <= 0:
                continue  # long leg only
            age = (p["entry_ns"] - fbn.get(p["symbol"], 0)) / DAY
            if age < 365.0:
                young["net"] += p["net_pnl_per_unit"]
                counts["young_n"] += 1
            else:
                old["net"] += p["net_pnl_per_unit"]
                counts["old_n"] += 1
        return young.get("net", 0.0) - old.get("net", 0.0), counts

    delta22, c22 = ha_delta(arts["C1_BASE_ANCHOR_Y2022"], None)
    delta23, c23 = ha_delta(arts["C2_BASE_ANCHOR_Y2023"], None)
    skip_share_23 = (sum(1 for b in arts["C2_BASE_ANCHOR_Y2023"]["books"]
                         if b.get("status") != "OK")
                     / max(1, len(arts["C2_BASE_ANCHOR_Y2023"]["books"])))
    out["H_A"] = {
        "Y2022": {"delta": round(delta22, 6), **c22,
                  "verdict": "VOID_BY_CONSTRUCTION" if c22["young_n"] == 0 else "MEASURED"},
        "Y2023": {"delta": round(delta23, 6), **c23,
                  "young_n_ge_20": c23["young_n"] >= MIN_YOUNG_POSITIONS,
                  "skip_share": round(skip_share_23, 4)},
    }
    guards = (c23["young_n"] >= MIN_YOUNG_POSITIONS
              and skip_share_23 <= MAX_SKIP_STAMPS_SHARE
              and not arts["C2_BASE_ANCHOR_Y2023"]["book_summary"]["cap_breaches"])
    # A2: no v2-age cell executed (C5 NOT_RUN_VOID); H-A has no executable
    # surface in phase-1 — verdict is the honest INCONCLUSIVE, never a claim.
    out["H_A"]["fold_sign_flips_to_negative"] = None
    out["H_A"]["verdict"] = "INCONCLUSIVE_VOID_CONSTRUCTION"
    out["H_A"]["verdict_basis"] = (
        "Amendment A2: A4 universe law leaves zero sub-365d names on both fresh "
        f"folds (young_n Y2022={c22['young_n']}, Y2023={c23['young_n']}); no v2-age cell "
        "executed; delta measurements are structural zeros. Owner option: Y2023-H2 "
        "window pair via separate amendment + fresh GO.")

    # ---- H-B (A1-6) ----
    def weekly_short_leg(art: dict) -> dict:
        # positions exit 8 days after their closing decision stamp
        # (1d execution lag + 7d holding): bucket by that decision stamp.
        per = defaultdict(float)
        for p in art["positions"]:
            if p["signed_weight"] < 0:
                per[p["exit_ns"] - 8 * 86_400_000_000_000] += p["net_pnl_per_unit"]
        return dict(per)

    def fold_of_ns(ns: int, fold_members: dict) -> str:
        for label, members in fold_members.items():
            if ns in members:
                return label
        return "?"

    def tail_stats(art: dict):
        # fold membership: fold_attribution is keyed by fold index (int);
        # map indices to sorted fold labels (F0,F1,F2)
        attr = art["fold_attribution"]
        labels = sorted({m["fold_label"] for m in art["fold_metrics"]})
        stamps_by_fold = {labels[int(k)]: set(v) for k, v in attr.items()}
        wk = weekly_short_leg(art)
        per_fold_tail = {}
        engagement = {}
        books = art["books"]
        fb_by_ns = {b["decision_ns"]: b for b in books}
        for label, stamp_set in stamps_by_fold.items():
            vals = sorted(v for ns, v in wk.items() if ns in stamp_set and v < 0)
            k = max(1, math.ceil(0.1 * max(1, len(vals))))
            tail = sum(vals[:k]) / k if vals else None
            nf = sum(1 for ns in stamp_set
                     if fb_by_ns.get(ns, {}).get("diagnostics", {})
                     .get("spread_fallback") is False)
            per_fold_tail[label] = {"worst_decile_mean": round(tail, 6) if tail is not None else None,
                                    "n_negative_weeks": len(vals), "n_weeks": len(stamp_set)}
            engagement[label] = nf
        return per_fold_tail, engagement

    hb = {"Y2022": {}, "Y2023": {}}
    for fold, base_cid, hedge_cid in (("Y2022", "C1_BASE_ANCHOR_Y2022", "C6_V2HEDGE_Y2022"),
                                      ("Y2023", "C2_BASE_ANCHOR_Y2023", "C7_V2HEDGE_Y2023")):
        tb, eb = tail_stats(arts[base_cid])
        th, eh = tail_stats(arts[hedge_cid])
        per_fold = {}
        for label in sorted(tb):
            base_tail = tb[label]["worst_decile_mean"]
            hedge_tail = th[label]["worst_decile_mean"]
            ratio = (hedge_tail / base_tail) if (base_tail and hedge_tail and base_tail < 0) else None
            per_fold[label] = {
                "base_tail": base_tail, "hedge_tail": hedge_tail,
                "ratio": round(ratio, 4) if ratio is not None else None,
                "tail_pass": ratio is not None and ratio <= DECILE_TAIL_MAX_RATIO,
                "engagement_nonfallback": {"base": eb[label], "hedge": eh[label]},
                "engagement_pass": eh[label] >= MIN_NONFALLBACK_PER_FOLD,
            }
        # fold net sign preservation hedge vs baseline
        fm_b = {m["fold_label"]: m["net_return_sum"] for m in arts[base_cid]["fold_metrics"]}
        fm_h = {m["fold_label"]: m["net_return_sum"] for m in arts[hedge_cid]["fold_metrics"]}
        for label in per_fold:
            per_fold[label]["sign_preserved"] = (
                (fm_b[label] > 0) == (fm_h[label] > 0))
        hb[fold] = {"per_fold": per_fold,
                    "fold_nets_base": {k: round(v, 6) for k, v in fm_b.items()},
                    "fold_nets_hedge": {k: round(v, 6) for k, v in fm_h.items()}}
    out["H_B"] = hb
    all_tail = all(f["tail_pass"] for f in hb["Y2022"]["per_fold"].values()) and \
        all(f["tail_pass"] for f in hb["Y2023"]["per_fold"].values())
    all_sign = all(f["sign_preserved"] for f in hb["Y2022"]["per_fold"].values()) and \
        all(f["sign_preserved"] for f in hb["Y2023"]["per_fold"].values())
    all_eng = all(f["engagement_pass"] for f in hb["Y2022"]["per_fold"].values()) and \
        all(f["engagement_pass"] for f in hb["Y2023"]["per_fold"].values())
    # A1-6 reading (recorded): engagement <13 stamps/fold = test powerless on
    # that fold => INCONCLUSIVE (the more specific (iii) clause); only
    # DIRECTIONAL failures on engaged folds falsify (tail ratio > bar, sign
    # flip, or INV coherence (a)/(b)).
    directional_fail = any(
        f["tail_pass"] is False and f["engagement_pass"] for f in
        list(hb["Y2022"]["per_fold"].values()) + list(hb["Y2023"]["per_fold"].values())
    ) or not all_sign
    if directional_fail:
        out["H_B"]["verdict"] = "FAIL"
    elif not all_eng:
        out["H_B"]["verdict"] = "INCONCLUSIVE"
        out["H_B"]["verdict_basis"] = ("engagement < 13 non-fallback stamps per fold "
                                       "on the 13-name A4 universe (A1-6 iii); "
                                       "no directional violation measured")
    else:
        out["H_B"]["verdict"] = "PASS"

    # ---- INV coherence (A1-6, Y2023: cells 4 vs 8) ----
    inv_base_net = arts["C4_BASE_INV_Y2023"]["portfolio_metrics"]["net_return_sum"]
    inv_hedge_net = arts["C8_INV_V2HEDGE_Y2023"]["portfolio_metrics"]["net_return_sum"]
    tb4, _ = tail_stats(arts["C4_BASE_INV_Y2023"])
    tb8, e8 = tail_stats(arts["C8_INV_V2HEDGE_Y2023"])
    inv_ratios = {}
    for label in sorted(tb4):
        b, h = tb4[label]["worst_decile_mean"], tb8[label]["worst_decile_mean"]
        if b and h and b < 0:
            inv_ratios[label] = round(h / b, 4)
    improved_gt30 = any(r < DECILE_TAIL_MAX_RATIO for r in inv_ratios.values())
    inv_directional_bad = (((inv_base_net > 0) != (inv_hedge_net > 0))
                           or improved_gt30)
    out["INV_COHERENCE"] = {
        "sign_preserved": (inv_base_net > 0) == (inv_hedge_net > 0),
        "inv_base_net": round(inv_base_net, 6),
        "inv_hedge_net": round(inv_hedge_net, 6),
        "tail_ratios_by_fold": inv_ratios,
        "tail_improved_gt30pct": improved_gt30,
        "engagement_hedge": e8,
        "verdict": ("FAIL" if inv_directional_bad else
                    "INCONCLUSIVE" if any(v < MIN_NONFALLBACK_PER_FOLD for v in e8.values())
                    else "PASS"),
        "verdict_basis": "directional FAIL iff sign flips or INV tail improved >30% "
                         "(generic-deleveraging guard); engagement shortfall => "
                         "INCONCLUSIVE per A1-6(iii)",
    }

    # ---- H-B final override: INV FAIL falsifies H-B (A1-6) ----
    if out["INV_COHERENCE"]["verdict"] == "FAIL":
        out["H_B"]["verdict"] = "FAIL"
        out["H_B"]["verdict_basis"] = (out["H_B"].get("verdict_basis") or "") + \
            "; INV coherence FAIL (A1-6)"
    (CTRL / "phase1_verdict.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    return out


def main() -> int:
    with heavy_lock.acquire(
        cycle_id="ILLIQ-LOSS-MECH-V1",
        role="phase1-cells",
        worktree=str(WORKTREE),
        command=[str(VENV_PY), "research/control/illiq_loss_mech_v1/phase1_cells.py"],
        expected_artifacts=[str(CTRL / "phase1_status.json"),
                            str(CTRL / "phase1_verdict.json")],
    ):
        run_cells()
        v = verdicts()
    print(json.dumps({"H_A": v["H_A"]["verdict"], "H_B": v["H_B"]["verdict"],
                      "INV_COHERENCE": v["INV_COHERENCE"]["verdict"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
