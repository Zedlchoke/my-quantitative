"""Scored evaluation runner — NFL-WINPROB-SCORED-V1 (two-key gated).

Adapted from the NBA v2 runner (remediation round 3): kickoff-grain as-of
law, TIE LAW (ties excluded from scoring/training rows, counts disclosed),
test seasons 2019..2025, NFL feature columns, NFL GO phrase.

v2 per AMENDMENT_1 (pre-outcome remediation): plain `elo_diff` column (B1-a
stream) required; per-fold AND pooled reliability/slope/paired-CI emitted;
§6 T1-T3/R1-R3 + hypothesis verdicts computed; hardened launch gates (pinned
paths, required ledger, fixed results dir, structured GO record, clean tree,
A7 artifact, FREE lock). Synthetic selftest exercises the same core.

LAUNCH LAW: refuses real data unless every gate passes; exit 3 on refusal.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import sys

from .protocol import (
    ARMS, LOGIT_L2, RNG_SEED, TEST_SEASONS,
    brier, calibration_slope, fit_logistic, log_loss,
    paired_block_bootstrap_delta, predict_logistic, reliability_bins,
)

GO_PHRASE = "GO NFL WINPROB SCORED V1 EVALUATION"
CYCLE_ID = "NFL-WINPROB-SCORED-V1"
RESEARCHCTL = ["/Users/hoangminhlong/my-quantitative/.venv/bin/python",
               "/Users/hoangminhlong/my-quantitative/research/researchctl.py", "locks", "inspect"]

REGISTERED_COMPARISONS = [
    ("B2-a", "B1*"), ("B2-a", "B0"), ("B1*", "B0"),
    ("B1-b", "B1-a"), ("B1-d", "B1-c"), ("B2-a", "B2-b"), ("B2-a", "B2-c"),
    # H1 falsification rule requires all four B1 arms vs B0 (protocol sec1);
    # comparisons are not arms — the 9-arm trial budget is unchanged.
    ("B1-a", "B0"), ("B1-b", "B0"), ("B1-c", "B0"), ("B1-d", "B0"),
]
FEATURE_COLS = ["elo_diff", "rest_diff", "short_week_home", "short_week_away", "form_home", "form_away"]
B1_ARMS = [a.arm_id for a in ARMS if a.kind == "B1"]


# ---------------------------------------------------------------- loading

def load_rows(games_csv: str, features_csv: str):
    games = {}
    with open(games_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            games[r["game_id"]] = {
                "season": int(r["season"]), "date": r["kickoff_utc"][:10],
                "is_playoffs": r["is_playoffs"] == "True",
                "home_win": r["home_win"] == "True",
                "tie": r["tie"] == "True",
            }
    rows = []
    with open(features_csv, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        header = set(rdr.fieldnames or [])
        need = set(FEATURE_COLS) | {f"p_home_{a}" for a in B1_ARMS} | {"game_id"}
        missing = need - header
        if missing:
            raise KeyError(f"features.csv missing columns: {sorted(missing)}")
        for r in rdr:
            g = games[r["game_id"]]
            rows.append({
                "src_game_id": r["game_id"], "date": g["date"], "tie": g["tie"],
                "season": g["season"], "is_playoffs": g["is_playoffs"],
                "home_win": g["home_win"],
                "features": {c: float(r[c]) for c in FEATURE_COLS},
                "p_b1": {a: float(r[f"p_home_{a}"]) for a in B1_ARMS},
            })
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


def _std(feat, stats, cols):
    return [1.0] + [(feat[c] - stats[c][0]) / stats[c][1] for c in cols]


def _metrics(ps, ys):
    return {"n": len(ps), "log_loss": log_loss(ps, ys), "brier": brier(ps, ys),
            "reliability": reliability_bins(ps, ys), "calibration_slope": calibration_slope(ps, ys)}


def run_evaluation(rows, n_boot: int = 10_000):
    """Pure function -> full result tree incl. per-fold+pooled metrics,
    registered paired comparisons (per fold AND pooled), §6 gate verdicts and
    hypothesis verdicts. Deterministic (seeded bootstrap)."""
    fold_list = []
    for s in TEST_SEASONS:
        train = [r for r in rows if r["season"] < s and not r["is_playoffs"] and not r["tie"]]
        test_rs = [r for r in rows if r["season"] == s and not r["is_playoffs"] and not r["tie"]]
        test_po = [r for r in rows if r["season"] == s and r["is_playoffs"] and not r["tie"]]
        n_ties_fold = sum(1 for r in rows if r["season"] == s and r["tie"])
        if not train or not test_rs:
            raise ValueError(f"fold {s}: empty train or primary test")
        fold_list.append((s, train, test_rs, test_po, n_ties_fold))

    state = {a.arm_id: {"fold_rs": {}, "fold_po": {}} for a in ARMS}
    fold_meta = {}
    for s, train, test_rs, test_po, n_ties_fold in fold_list:
        b0_p = sum(1 for r in train if r["home_win"]) / len(train)
        fold_meta[s] = {"b0_rate_train": b0_p, "n_train": len(train),
                        "n_rs": len(test_rs), "n_po": len(test_po),
                        "n_ties_excluded_disclosed": n_ties_fold}
        for arm in ARMS:
            if arm.kind == "B0":
                def pred(r, _p=b0_p):
                    return _p
            elif arm.kind == "B1":
                def pred(r, _a=arm.arm_id):
                    return r["p_b1"][_a]
            else:
                cols = list(arm.features)
                stats = _fit_standardizer(train, cols)
                w = fit_logistic([_std(r["features"], stats, cols) for r in train],
                                 [1.0 if r["home_win"] else 0.0 for r in train], l2=LOGIT_L2)

                def pred(r, _w=w, _st=stats, _c=cols):
                    return predict_logistic(_w, _std(r["features"], _st, _c))
            st = state[arm.arm_id]
            ps = [pred(r) for r in test_rs]
            ys = [1 if r["home_win"] else 0 for r in test_rs]
            ds = [r["date"] for r in test_rs]
            st["fold_rs"][s] = (ps, ys, ds)
            if test_po:
                st["fold_po"][s] = ([pred(r) for r in test_po],
                                    [1 if r["home_win"] else 0 for r in test_po])

    def pooled(d):
        return ([p for s in d for p in d[s][0]], [y for s in d for y in d[s][1]],
                [x for s in d for x in d[s][2]])

    arms_out, pooled_arrays = {}, {}
    for arm in ARMS:
        st = state[arm.arm_id]
        ps, ys, ds = pooled(st["fold_rs"])
        pooled_arrays[arm.arm_id] = (ps, ys, ds)
        folds_out = {str(s): _metrics(*st["fold_rs"][s][:2]) for s in fold_meta}
        if st["fold_po"]:
            po_ps = [p for s in st["fold_po"] for p in st["fold_po"][s][0]]
            po_ys = [y for s in st["fold_po"] for y in st["fold_po"][s][1]]
            po = _metrics(po_ps, po_ys)
        else:
            po = None
        arms_out[arm.arm_id] = {
            "kind": arm.kind, "spec": {"K": arm.K, "HCA": arm.HCA, "features": list(arm.features)},
            "pooled_rs": _metrics(ps, ys), "folds": folds_out,
            "pooled_playoffs_separate": po,
        }

    b1star = min(B1_ARMS, key=lambda a: arms_out[a]["pooled_rs"]["log_loss"])

    def resolve(x):
        return b1star if x == "B1*" else x

    comparisons = {"pooled": {}, "per_fold": {}}
    for arm_id, ref in REGISTERED_COMPARISONS:
        ra, rr = resolve(arm_id), resolve(ref)
        key = f"{arm_id}_vs_{ref}"
        pa, ya, da = pooled_arrays[ra]
        pr, yr, dr = pooled_arrays[rr]
        if not (ya == yr and da == dr):
            raise ValueError(f"comparison {key}: game sets differ")
        mean, lo, hi = paired_block_bootstrap_delta(pa, pr, ya, da, n_resamples=n_boot)
        comparisons["pooled"][key] = {"delta_log_loss": mean, "ci95_lo": lo, "ci95_hi": hi,
                                      "n": len(ya), "sign_note": "negative favors the arm"}
        comparisons["per_fold"][key] = {}
        for s in fold_meta:
            fa, fb = state[ra]["fold_rs"][s], state[rr]["fold_rs"][s]
            m, l, h = paired_block_bootstrap_delta(fa[0], fb[0], fa[1], fa[2], n_resamples=n_boot)
            comparisons["per_fold"][key][str(s)] = {"delta_log_loss": m, "ci95_lo": l, "ci95_hi": h,
                                                    "n": fa[1].__len__()}

    def ci(key):
        return comparisons["pooled"][key]

    def arm_favors(key):
        return ci(key)["ci95_hi"] < 0

    def ref_favors(key):
        return ci(key)["ci95_lo"] > 0

    ll = {a: arms_out[a]["pooled_rs"]["log_loss"] for a in arms_out}
    slope_b2a = arms_out["B2-a"]["pooled_rs"]["calibration_slope"]
    b2a_beats_b1star_folds = sum(
        1 for s in fold_meta
        if comparisons["per_fold"]["B2-a_vs_B1*"][str(s)]["delta_log_loss"] < 0)
    b2a_brier_worse_than_b0_folds = [
        str(s) for s in fold_meta
        if arms_out["B2-a"]["folds"][str(s)]["brier"] > arms_out["B0"]["folds"][str(s)]["brier"]]

    verdicts = {
        "T1_discriminative_gain": {
            "pooled_ci_below_0": arm_favors("B2-a_vs_B1*"),
            "folds_negative": f"{b2a_beats_b1star_folds}/{len(fold_meta)} (need >= half)",
            "PASS": arm_favors("B2-a_vs_B1*") and b2a_beats_b1star_folds >= (len(fold_meta) + 1) // 2},
        "T2_calibration": {"slope": slope_b2a, "band": [0.85, 1.15],
                           "PASS": 0.85 <= slope_b2a <= 1.15},
        "T3_floor_safety": {
            "no_fold_brier_worse_than_B0": not b2a_brier_worse_than_b0_folds,
            "folds_flagged": b2a_brier_worse_than_b0_folds,
            "pooled_ci_below_0_vs_B0": arm_favors("B2-a_vs_B0"),
            "PASS": (not b2a_brier_worse_than_b0_folds) and arm_favors("B2-a_vs_B0")},
        "B1star": b1star, "pooled_log_losses": ll,
    }
    verdicts["PROGRAM_PASS"] = all(verdicts[k]["PASS"] for k in ("T1_discriminative_gain", "T2_calibration", "T3_floor_safety"))
    r1 = not arm_favors("B1*_vs_B0")            # CI includes 0 or ref-favored
    r2 = ref_favors("B2-a_vs_B0")
    r3 = ref_favors("B2-a_vs_B1*") and not (0.85 <= slope_b2a <= 1.15)
    verdicts["REJECT"] = {"R1_no_elo_gain_vs_B0": r1, "R2_candidate_worse_than_B0": r2,
                          "R3_degradation_and_miscalibration": r3, "ANY": r1 or r2 or r3}
    decisive = [k for k in comparisons["pooled"] if arm_favors(k) or ref_favors(k)]
    verdicts["INCONCLUSIVE"] = (not verdicts["PROGRAM_PASS"] and not verdicts["REJECT"]["ANY"]
                                and 0.85 <= slope_b2a <= 1.15)
    verdicts["hypotheses"] = {
        "H1_dynamic_strength": {
            "rule": "REJECT iff no B1 arm beats B0 (all 4 CIs include 0 or favor B0)",
            "REJECT": all(not arm_favors(f"{a}_vs_B0") for a in B1_ARMS if a == b1star) or
                      all(not arm_favors(f"{a}_vs_B0") for a in B1_ARMS),
            "evidence": {f"{a}_vs_B0": {"ci": [ci(f'{a}_vs_B0')['ci95_lo'], ci(f'{a}_vs_B0')['ci95_hi']],
                                        "favors_arm": arm_favors(f"{a}_vs_B0")} for a in B1_ARMS}},
        "H2_home_court": {
            "rule": "REJECT iff for both K, CI of (K,100)vs(K,0) includes 0 or favors HCA=0",
            "REJECT": all(not arm_favors(k) for k in ("B1-b_vs_B1-a", "B1-d_vs_B1-c")),
            "evidence": {k: {"ci": [ci(k)["ci95_lo"], ci(k)["ci95_hi"]], "favors_arm": arm_favors(k)}
                         for k in ("B1-b_vs_B1-a", "B1-d_vs_B1-c")}},
        "H3_rest_schedule": {
            "rule": "REJECT iff CI of B2-a vs B2-b includes 0 or favors B2-b",
            "REJECT": not arm_favors("B2-a_vs_B2-b"),
            "evidence": {"ci": [ci("B2-a_vs_B2-b")["ci95_lo"], ci("B2-a_vs_B2-b")["ci95_hi"]],
                         "favors_arm": arm_favors("B2-a_vs_B2-b")}},
    }

    return {"cycle_id": CYCLE_ID, "test_seasons": list(TEST_SEASONS), "fold_meta": fold_meta,
            "arms": arms_out, "comparisons": comparisons, "verdicts": verdicts,
            "language_law": "calibration language only; no PnL/betting/edge vocabulary"}


# ---------------------------------------------------------------- gates v2

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


def _allowed_path(p, allow):
    for a in allow:
        if a.endswith("/**") and p.startswith(a[:-2]):
            return True
        if p == a:
            return True
    return False


def _code_drift_reasons(changed, allowlist):
    """Pure helper: given changed paths (post-freeze diff) + allowlist, return
    drift reasons. Immutable code prefix is nfl_winprob/ (NBA remnant fixed)."""
    reasons = []
    code = [p for p in changed if p.startswith("nfl_winprob/")]
    if code:
        reasons.append(f"CODE DRIFT (nfl_winprob/ immutable): {code[:5]}")
    bad = [p for p in changed if not _allowed_path(p, allowlist)]
    if bad:
        reasons.append(f"post-freeze drift outside allowlist: {bad[:5]}")
    return reasons


def check_launch_gates(worktree, manifest_path, go_record_path, games=None, features=None):
    reasons = []
    try:
        with open(manifest_path, encoding="utf-8") as f:
            m = json.load(f)
    except Exception as e:  # noqa: BLE001
        return False, [f"freeze manifest unreadable: {e}"]
    if m.get("cycle_id") != CYCLE_ID or m.get("schema") != "nfl_winprob_scored_freeze@1":
        reasons.append("manifest cycle_id/schema mismatch (need freeze v2 post-AMENDMENT_1)")
    # pinned inputs
    pin_g, pin_f = m.get("pinned_games"), m.get("pinned_features")
    if not (pin_g and pin_f):
        reasons.append("manifest missing pinned_games/pinned_features")
    else:
        if games is not None and os.path.abspath(games) != pin_g:
            reasons.append(f"--games {games} != pinned {pin_g}")
        if features is not None and os.path.abspath(features) != pin_f:
            reasons.append(f"--features {features} != pinned {pin_f}")
        for name, p in (("games", pin_g), ("features", pin_f)):
            if not os.path.exists(p):
                reasons.append(f"pinned {name} missing: {p}")
    for name, meta in m.get("data", {}).items():
        if os.path.exists(meta["path"]) and _sha256_file(meta["path"]) != meta["sha256"]:
            reasons.append(f"data hash mismatch: {name}")
    # code immutability since freeze
    base = m.get("code_freeze_sha")
    if not base:
        reasons.append("manifest missing code_freeze_sha")
    else:
        try:
            changed = [p for p in _git(["diff", "--name-only", base, "HEAD"], worktree).splitlines() if p]
            reasons.extend(_code_drift_reasons(changed, m.get("post_freeze_allowlist", [])))
            if _git(["status", "--porcelain"], worktree):
                reasons.append("worktree dirty at launch")
        except RuntimeError as e:
            reasons.append(f"git gate check failed: {e}")
    # A7 artifact
    a7 = m.get("a7_report_path")
    if not a7 or not os.path.exists(a7):
        reasons.append(f"A7 prelaunch report missing: {a7}")
    else:
        with open(a7, encoding="utf-8") as f:
            if "A7_PRELAUNCH_AUTHORIZED" not in f.read():
                reasons.append("A7 report does not carry A7_PRELAUNCH_AUTHORIZED")
    # heavy lock free
    try:
        out = subprocess.run(RESEARCHCTL, capture_output=True, text=True, check=True).stdout
        if '"FREE_PROVEN"' not in out:
            reasons.append(f"heavy lock not FREE_PROVEN: {out[:120]}")
    except Exception as e:  # noqa: BLE001
        reasons.append(f"lock check failed: {e}")
    # structured GO record
    if not go_record_path or not os.path.exists(go_record_path):
        reasons.append(f"no GO record: {go_record_path!r} (owner must type the phrase at this cycle's own gate after A7)")
    else:
        try:
            with open(go_record_path, encoding="utf-8") as f:
                rec = json.load(f)
            if rec.get("phrase") != GO_PHRASE:
                reasons.append("GO record phrase mismatch")
            if rec.get("cycle_id") != CYCLE_ID:
                reasons.append("GO record cycle mismatch")
            if rec.get("typed_by") != "owner":
                reasons.append("GO record typed_by != owner")
            if not rec.get("typed_at"):
                reasons.append("GO record missing typed_at")
        except Exception as e:  # noqa: BLE001
            reasons.append(f"GO record not valid structured JSON: {e}")
    return (not reasons), reasons


# ---------------------------------------------------------------- selftest

def synthetic_selftest() -> dict:
    import random
    rng = random.Random(RNG_SEED)
    strengths = {f"T{i}": rng.gauss(0, 100) for i in range(8)}
    rows = []
    order = 0
    for season in range(2012, 2027):
        for day in range(1, 60):
            date = f"{season}-01-{day:02d}"
            for _ in range(3):
                i, j = rng.sample(range(8), 2)
                order += 1
                diff = strengths[f"T{i}"] - strengths[f"T{j}"] + 60
                rows.append({
                    "src_game_id": f"S{order:06d}", "date": date, "season": season,
                    "is_playoffs": day > 50, "tie": rng.random() < 0.002,
                    "home_win": rng.random() < 1.0 / (1.0 + 10 ** (-diff / 400.0)),
                    "features": {c: rng.gauss(0, 1) for c in FEATURE_COLS},
                    "p_b1": {a: 1.0 / (1.0 + 10 ** (-(diff) / 400.0)) for a in B1_ARMS},
                })
    summary = run_evaluation(rows, n_boot=300)
    v = summary["verdicts"]
    assert len(summary["arms"]) == 9 and len(summary["comparisons"]["pooled"]) == 11
    assert set(summary["comparisons"]["per_fold"]["B2-a_vs_B1*"]) == {str(x) for x in TEST_SEASONS}
    assert all("reliability" in f and "calibration_slope" in f
               for a in summary["arms"].values() for f in a["folds"].values())
    assert isinstance(v["PROGRAM_PASS"], bool) and isinstance(v["REJECT"]["ANY"], bool)
    assert isinstance(v["hypotheses"]["H3_rest_schedule"]["REJECT"], bool)
    s2 = run_evaluation(rows, n_boot=300)
    assert s2["comparisons"]["pooled"] == summary["comparisons"]["pooled"]
    return summary


# ---------------------------------------------------------------- ledger + CLI

def append_trial_rows(ledger_path, summary, repro=False):
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
                "schema": "nfl_winprob_trial_ledger@1", "cycle_id": CYCLE_ID,
                "arm_id": arm_id, "status": "COMPUTED",
                "computed_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                "pooled_rs_log_loss": entry["pooled_rs"]["log_loss"],
                "pooled_rs_brier": entry["pooled_rs"]["brier"],
                "pooled_rs_n": entry["pooled_rs"]["n"],
                "class": "REPRO" if (arm_id in computed and repro) else "PRIMARY",
            }) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games"), ap.add_argument("--features")
    ap.add_argument("--worktree", default=os.getcwd())
    ap.add_argument("--freeze-manifest", required=True)
    ap.add_argument("--go-record", required=True)
    ap.add_argument("--ledger")
    ap.add_argument("--synthetic-selftest", action="store_true")
    ap.add_argument("--repro", action="store_true")
    args = ap.parse_args()

    if args.synthetic_selftest:
        summary = synthetic_selftest()
        print("SELFTEST PASS: 9 arms, 11 comparisons (pooled+per-fold), verdicts emitted, "
              "fold reliability/slope present, bootstrap deterministic; no real data touched.")
        print(json.dumps({"PROGRAM_PASS": summary["verdicts"]["PROGRAM_PASS"],
                          "REJECT": summary["verdicts"]["REJECT"]["ANY"]}, indent=1))
        return 0

    with open(args.freeze_manifest, encoding="utf-8") as f:
        m = json.load(f)
    ledger = args.ledger or m.get("ledger_path")
    out_dir = m.get("results_dir")
    ok, reasons = check_launch_gates(args.worktree, args.freeze_manifest, args.go_record,
                                     games=args.games, features=args.features)
    if not ok:
        print("REFUSED — launch gates failed:", file=sys.stderr)
        for r in reasons:
            print("  -", r, file=sys.stderr)
        return 3
    if not ledger or not out_dir:
        print("REFUSED — manifest missing ledger_path/results_dir", file=sys.stderr)
        return 3

    rows = load_rows(args.games or m["pinned_games"], args.features or m["pinned_features"])
    summary = run_evaluation(rows)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "scored_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    append_trial_rows(ledger, summary, repro=args.repro)
    print(json.dumps({"b1star": summary["verdicts"]["B1star"],
                      "PROGRAM_PASS": summary["verdicts"]["PROGRAM_PASS"],
                      "REJECT": summary["verdicts"]["REJECT"]["ANY"], "out": out_path}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
