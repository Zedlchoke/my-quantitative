"""Scored evaluation runner — NBA-WINPROB-SCORED-V1 (two-key gated).

Implements the frozen protocol (lanes/C_protocol/PROTOCOL_EVAL.md sec2-6)
end to end: 9 arms x 7 folds (test seasons 2009..2015), B0 refit per fold,
B1 precomputed as-of predictions, B2 logistic with train-only standardization
+ L2, metrics (LL/Brier/reliability/slope), 7 registered paired comparisons
with date-clustered bootstrap, playoff segment reported separately, trial
ledger append.

LAUNCH LAW: refuses to touch REAL data unless (a) FREEZE_MANIFEST.json
validates (code freeze sha == git HEAD, no post-freeze drift outside the
allowlist, data hashes match) and (b) a GO record file contains the exact
phrase "GO NBA WINPROB SCORED V1 EVALUATION" for this cycle. Exit code 3 on
refusal. The synthetic selftest runs the identical core on synthetic rows
(no real outcomes) and is the only ungated execution path.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import random
import subprocess
import sys

from .protocol import (
    ARMS, LOGIT_L2, RNG_SEED, TEST_SEASONS,
    brier, calibration_slope, fit_logistic, log_loss,
    paired_block_bootstrap_delta, predict_logistic, reliability_bins,
)

GO_PHRASE = "GO NBA WINPROB SCORED V1 EVALUATION"
CYCLE_ID = "NBA-WINPROB-SCORED-V1"

REGISTERED_COMPARISONS = [
    ("B2-a", "B1*"), ("B2-a", "B0"), ("B1*", "B0"),
    ("B1-b", "B1-a"), ("B1-d", "B1-c"), ("B2-a", "B2-b"), ("B2-a", "B2-c"),
]

FEATURE_COLS = ["elo_diff", "rest_diff", "b2b_home", "b2b_away", "form_home", "form_away"]
B1_ARMS = [a.arm_id for a in ARMS if a.kind == "B1"]


# ---------------------------------------------------------------- loading

def load_rows(games_csv: str, features_csv: str):
    games = {}
    with open(games_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            games[r["src_game_id"]] = {
                "season": int(r["season"]),
                "date": r["date"],
                "is_playoffs": r["is_playoffs"] == "True",
                "home_win": r["home_win"] == "True",
            }
    rows = []
    with open(features_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            g = games[r["src_game_id"]]
            row = {
                "src_game_id": r["src_game_id"], "date": g["date"],
                "season": g["season"], "is_playoffs": g["is_playoffs"],
                "home_win": g["home_win"],
                "features": {c: float(r[c]) for c in FEATURE_COLS},
                "p_b1": {a: float(r[f"p_home_{a}"]) for a in B1_ARMS},
            }
            rows.append(row)
    return rows


# ---------------------------------------------------------------- core

def _fit_standardizer(train_rows, cols):
    stats = {}
    for c in cols:
        vals = [r["features"][c] for r in train_rows]
        mu = sum(vals) / len(vals)
        var = sum((v - mu) ** 2 for v in vals) / len(vals)
        stats[c] = (mu, math.sqrt(var) if var > 0 else 1.0)
    return stats


def _std(row_features, stats, cols):
    return [1.0] + [(row_features[c] - stats[c][0]) / stats[c][1] for c in cols]


def run_evaluation(rows):
    """Pure function: rows -> full result tree. No I/O. Deterministic."""
    folds = []
    for s in TEST_SEASONS:
        train = [r for r in rows if r["season"] < s and not r["is_playoffs"]]
        test_rs = [r for r in rows if r["season"] == s and not r["is_playoffs"]]
        test_po = [r for r in rows if r["season"] == s and r["is_playoffs"]]
        if not train or not test_rs:
            raise ValueError(f"fold {s}: empty train or primary test")
        folds.append((s, train, test_rs, test_po))

    arm_results = {a.arm_id: {"folds": {}, "pooled_rs": [], "pooled_po": []} for a in ARMS}
    for s, train, test_rs, test_po in folds:
        b0_p = (sum(1 for r in train if r["home_win"]) / len(train))
        for arm in ARMS:
            if arm.kind == "B0":
                pred = lambda r, _p=b0_p: _p
            elif arm.kind == "B1":
                pred = lambda r, _a=arm.arm_id: r["p_b1"][_a]
            else:
                cols = list(arm.features)
                stats = _fit_standardizer(train, cols)
                X = [_std(r["features"], stats, cols) for r in train]
                y = [1.0 if r["home_win"] else 0.0 for r in train]
                w = fit_logistic(X, y, l2=LOGIT_L2)
                pred = lambda r, _w=w, _st=stats, _c=cols: predict_logistic(_w, _std(r["features"], _st, _c))
            res = arm_results[arm.arm_id]
            for seg_name, seg in (("rs", test_rs), ("po", test_po)):
                if not seg:
                    continue
                ps = [pred(r) for r in seg]
                ys = [1 if r["home_win"] else 0 for r in seg]
                res["folds"].setdefault(s, {})[seg_name] = {
                    "n": len(seg),
                    "log_loss": log_loss(ps, ys),
                    "brier": brier(ps, ys),
                    "reliability": reliability_bins(ps, ys),
                }
                if seg_name == "rs":
                    res["pooled_rs"].append((ps, ys, [r["date"] for r in seg]))
                else:
                    res["pooled_po"].append((ps, ys, [r["date"] for r in seg]))
            res["folds"][s]["b0_rate_train"] = b0_p if arm.kind == "B0" else None

    summary = {"cycle_id": CYCLE_ID, "generated_by": "run_evaluation.run_evaluation",
               "test_seasons": list(TEST_SEASONS), "arms": {}, "comparisons": {}}
    for arm in ARMS:
        res = arm_results[arm.arm_id]
        ps = [p for seg in res["pooled_rs"] for p in seg[0]]
        ys = [y for seg in res["pooled_rs"] for y in seg[1]]
        ds = [d for seg in res["pooled_rs"] for d in seg[2]]
        entry = {
            "kind": arm.kind, "spec": {"K": arm.K, "HCA": arm.HCA, "features": list(arm.features)},
            "pooled_rs": {"n": len(ps), "log_loss": log_loss(ps, ys), "brier": brier(ps, ys),
                          "calibration_slope": calibration_slope(ps, ys)},
            "folds": {
                str(s): {
                    k: ({kk: vv for kk, vv in v.items() if kk != "reliability"}
                        if isinstance(v, dict) else v)
                    for k, v in res["folds"][s].items()
                    if k != "b0_rate_train" or v is not None
                }
                for s in TEST_SEASONS if s in res["folds"]
            },
        }
        po_ps = [p for seg in res["pooled_po"] for p in seg[0]]
        po_ys = [y for seg in res["pooled_po"] for y in seg[1]]
        if po_ps:
            entry["pooled_playoffs_separate"] = {"n": len(po_ps), "log_loss": log_loss(po_ps, po_ys),
                                                 "brier": brier(po_ps, po_ys)}
        entry["_arrays_rs"] = (ps, ys, ds)
        summary["arms"][arm.arm_id] = entry

    b1_pooled = {a: summary["arms"][a]["pooled_rs"]["log_loss"] for a in B1_ARMS}
    b1star = min(B1_ARMS, key=lambda a: b1_pooled[a])
    summary["b1star"] = b1star

    def resolve(ref):
        return b1star if ref == "B1*" else ref

    for arm_id, ref in REGISTERED_COMPARISONS:
        ra, rr = summary["arms"][resolve(arm_id)], summary["arms"][resolve(ref)]
        pa, ya, da = ra["_arrays_rs"]
        pr, yr, dr = rr["_arrays_rs"]
        assert (ya == yr) and (da == dr), "paired comparison on identical game sets"
        mean, lo, hi = paired_block_bootstrap_delta(pa, pr, ya, da)
        summary["comparisons"][f"{arm_id}_vs_{ref}"] = {
            "delta_log_loss": mean, "ci95_lo": lo, "ci95_hi": hi,
            "n": len(ya), "sign_note": "negative favors the arm",
        }
    for arm_id in summary["arms"]:
        summary["arms"][arm_id].pop("_arrays_rs", None)
    return summary


# ---------------------------------------------------------------- gates

def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(args, cwd):
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              check=True).stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {(e.stderr or '').strip()[:200]}") from None


def _allowed_path(p: str, allow) -> bool:
    for a in allow:
        if a.endswith("/**"):
            if p.startswith(a[:-2]):
                return True
        elif p == a:
            return True
    return False


def check_launch_gates(worktree: str, manifest_path: str, go_record_path: str | None):
    reasons = []
    try:
        with open(manifest_path, encoding="utf-8") as f:
            m = json.load(f)
    except Exception as e:  # noqa: BLE001
        return False, [f"freeze manifest unreadable: {e}"]
    if m.get("cycle_id") != CYCLE_ID:
        reasons.append("manifest cycle_id mismatch")
    base = m.get("code_freeze_sha")
    if not base:
        reasons.append("manifest missing code_freeze_sha")
    else:
        try:
            changed = [p for p in _git(["diff", "--name-only", base, "HEAD"], worktree).splitlines() if p]
        except RuntimeError as e:
            reasons.append(f"git gate check failed: {e}")
            changed = []
        code_drift = [p for p in changed if p.startswith("nba_winprob/")]
        if code_drift:
            reasons.append(f"CODE DRIFT after freeze (nba_winprob/ immutable): {code_drift[:5]}")
        bad = [p for p in changed if not _allowed_path(p, m.get("post_freeze_allowlist", []))]
        if bad:
            reasons.append(f"post-freeze drift outside allowlist: {bad[:5]}")
    for name, meta in m.get("data", {}).items():
        path = meta["path"]
        if not os.path.exists(path):
            reasons.append(f"data missing: {name} {path}")
        elif _sha256_file(path) != meta["sha256"]:
            reasons.append(f"data hash mismatch: {name}")
    if m.get("protocol_digest"):
        pd = _sha256_file(os.path.join(worktree, m["protocol_path"]))
        if pd != m["protocol_digest"]:
            reasons.append("protocol file changed after freeze")
    if not go_record_path or not os.path.exists(go_record_path):
        reasons.append(f"no GO record (this cycle requires the owner to type the phrase at its own gate after A7): {go_record_path!r}")
    else:
        with open(go_record_path, encoding="utf-8") as f:
            rec = f.read()
        if GO_PHRASE not in rec or CYCLE_ID not in rec:
            reasons.append("GO record malformed (phrase/cycle mismatch)")
    return (not reasons), reasons


# ---------------------------------------------------------------- synthetic selftest

def synthetic_selftest() -> dict:
    rng = random.Random(RNG_SEED)
    strengths = {f"T{i}": rng.gauss(0, 100) for i in range(8)}
    rows = []
    order = 0
    for season in range(2005, 2017):
        for day in range(1, 60):
            date = f"{season}-01-{day:02d}"
            for m in range(3):
                i, j = rng.sample(range(8), 2)
                order += 1
                diff = strengths[f"T{i}"] - strengths[f"T{j}"] + 60  # home edge
                p = 1.0 / (1.0 + 10 ** (-diff / 400.0))
                rows.append({
                    "src_game_id": f"S{order:06d}", "date": date, "season": season,
                    "is_playoffs": day > 50, "home_win": rng.random() < p,
                    "features": {c: rng.gauss(0, 1) for c in FEATURE_COLS},
                    "p_b1": {a: 1.0 / (1.0 + 10 ** (-(diff) / 400.0)) for a in B1_ARMS},
                })
    summary = run_evaluation(rows)
    assert len(summary["arms"]) == 9
    assert summary["b1star"] in B1_ARMS
    for arm_id, entry in summary["arms"].items():
        ll = entry["pooled_rs"]["log_loss"]
        assert 0.0 < ll < 1.5, (arm_id, ll)
    assert len(summary["comparisons"]) == 7
    for c in summary["comparisons"].values():
        assert c["ci95_lo"] <= c["delta_log_loss"] <= c["ci95_hi"]
    # determinism of the bootstrap under identical inputs
    s2 = run_evaluation(rows)
    assert s2["comparisons"] == summary["comparisons"]
    return summary


# ---------------------------------------------------------------- ledger

def append_trial_rows(ledger_path: str, summary: dict, repro: bool = False):
    existing = []
    if os.path.exists(ledger_path):
        with open(ledger_path, encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
    computed = {r["arm_id"] for r in existing if r.get("status") == "COMPUTED"}
    with open(ledger_path, "a", encoding="utf-8") as f:
        for arm_id, entry in summary["arms"].items():
            if arm_id in computed and not repro:
                continue
            f.write(json.dumps({
                "schema": "nba_winprob_trial_ledger@1", "cycle_id": CYCLE_ID,
                "arm_id": arm_id, "status": "COMPUTED",
                "computed_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                "pooled_rs_log_loss": entry["pooled_rs"]["log_loss"],
                "pooled_rs_brier": entry["pooled_rs"]["brier"],
                "pooled_rs_n": entry["pooled_rs"]["n"],
                "class": "REPRO" if (arm_id in computed and repro) else "PRIMARY",
            }) + "\n")


# ---------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games"), ap.add_argument("--features")
    ap.add_argument("--out", required=True)
    ap.add_argument("--worktree", default=os.getcwd())
    ap.add_argument("--freeze-manifest")
    ap.add_argument("--go-record")
    ap.add_argument("--ledger")
    ap.add_argument("--synthetic-selftest", action="store_true")
    ap.add_argument("--repro", action="store_true")
    args = ap.parse_args()

    if args.synthetic_selftest:
        summary = synthetic_selftest()
        print("SELFTEST PASS: 9 arms, 7 comparisons, bootstrap deterministic, "
              "no real data touched.")
        print(json.dumps({"b1star": summary["b1star"]}, indent=1))
        return 0

    ok, reasons = check_launch_gates(args.worktree, args.freeze_manifest, args.go_record)
    if not ok:
        print("REFUSED — launch gates failed:", file=sys.stderr)
        for r in reasons:
            print("  -", r, file=sys.stderr)
        return 3

    rows = load_rows(args.games, args.features)
    summary = run_evaluation(rows)
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "scored_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    if args.ledger:
        append_trial_rows(args.ledger, summary, repro=args.repro)
    print(json.dumps({"b1star": summary["b1star"], "out": out_path}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
