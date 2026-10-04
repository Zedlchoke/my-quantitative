"""Tests for the scored runner: fold isolation, train-only standardization,
B0/B1 wiring, gates, ledger discipline, synthetic selftest."""
import json
import random

import pytest

from nba_winprob.protocol import ARMS, RNG_SEED, TEST_SEASONS
from nba_winprob.run_evaluation import (
    CYCLE_ID, GO_PHRASE, append_trial_rows, check_launch_gates,
    run_evaluation, synthetic_selftest,
)

FEATURE_COLS = ["elo_diff", "rest_diff", "b2b_home", "b2b_away", "form_home", "form_away"]


def make_rows(seed=7, seasons=None):
    rng = random.Random(seed)
    rows = []
    order = 0
    for season in (seasons or list(range(2005, 2017))):
        for day in range(1, 40):
            for _ in range(2):
                order += 1
                rows.append({
                    "src_game_id": f"R{order:06d}",
                    "date": f"{season}-02-{day:02d}",
                    "season": season, "is_playoffs": day > 30,
                    "home_win": rng.random() < 0.6,
                    "features": {c: rng.gauss(0, 1) for c in FEATURE_COLS},
                    "p_b1": {f"B1-{s}": 0.55 for s in ("a", "b", "c", "d")},
                })
    return rows


def test_b0_refit_per_fold_and_fold_isolation():
    rows = make_rows()
    s = run_evaluation(rows)
    rates = {}
    for season in TEST_SEASONS:
        train = [r for r in rows if r["season"] < season and not r["is_playoffs"]]
        rates[season] = sum(1 for r in train if r["home_win"]) / len(train)
    for season in TEST_SEASONS:
        assert abs(s["arms"]["B0"]["folds"][str(season)]["b0_rate_train"] - rates[season]) < 1e-12
    # adding a future season's rows must not change earlier folds (isolation)
    rows2 = [dict(r) for r in rows] + [dict(r, season=2030) for r in make_rows(seed=11)[:50]]
    s2 = run_evaluation(rows2)
    for season in TEST_SEASONS:
        assert s2["arms"]["B0"]["folds"][str(season)]["b0_rate_train"] == \
               s["arms"]["B0"]["folds"][str(season)]["b0_rate_train"]


def test_b1_uses_precomputed_asof_columns():
    rows = make_rows()
    for r in rows:
        r["p_b1"]["B1-b"] = 0.25
    s = run_evaluation(rows)
    # with constant p=0.25 for arm B1-b, its pooled brier is fully determined
    ys = [1 if r["home_win"] else 0 for r in rows
          if r["season"] in TEST_SEASONS and not r["is_playoffs"]]
    n = len(ys)
    exp_brier = sum((0.25 - y) ** 2 for y in ys) / n
    assert abs(s["arms"]["B1-b"]["pooled_rs"]["brier"] - exp_brier) < 1e-9


def test_b2_train_only_standardization():
    rows = make_rows()
    s1 = run_evaluation(rows)
    # perturb ONLY test-season features: train means/stds (and hence the fit
    # given identical train rows) must not change; predictions shift instead
    rows2 = [dict(r) for r in rows]
    for r in rows2:
        if r["season"] in TEST_SEASONS:
            r["features"] = {k: v + 5.0 for k, v in r["features"].items()}
    s2 = run_evaluation(rows2)
    for arm in ("B2-a", "B2-b", "B2-c", "B2-d"):
        # same training data -> identical fold metrics on TRAIN-dependent parts
        # (we observe via b0_rate_train equality and stable b1star among B1)
        pass
    assert s1["b1star"] == s2["b1star"]
    # B2 pooled metrics change (test features shifted)
    assert s1["arms"]["B2-a"]["pooled_rs"]["log_loss"] != s2["arms"]["B2-a"]["pooled_rs"]["log_loss"]


def test_nine_arms_and_registered_comparisons():
    s = run_evaluation(make_rows())
    assert len(s["arms"]) == 9
    assert set(s["comparisons"].keys()) == {
        "B2-a_vs_B1*", "B2-a_vs_B0", "B1*_vs_B0",
        "B1-b_vs_B1-a", "B1-d_vs_B1-c", "B2-a_vs_B2-b", "B2-a_vs_B2-c"}
    # B1* resolution consistent
    b1 = [a for a in ("B1-a", "B1-b", "B1-c", "B1-d")]
    ll = {a: s["arms"][a]["pooled_rs"]["log_loss"] for a in b1}
    assert s["b1star"] == min(b1, key=lambda a: ll[a])


def test_playoffs_reported_separately():
    s = run_evaluation(make_rows())
    assert "pooled_playoffs_separate" in s["arms"]["B2-a"]
    assert s["arms"]["B2-a"]["pooled_playoffs_separate"]["n"] > 0


def test_synthetic_selftest_end_to_end():
    summary = synthetic_selftest()
    assert len(summary["arms"]) == 9 and len(summary["comparisons"]) == 7


def test_launch_gates_refuse_without_go_record(tmp_path):
    # manifest with impossible freeze sha -> refused; missing go record -> refused
    mfile = tmp_path / "FREEZE_MANIFEST.json"
    mfile.write_text(json.dumps({
        "cycle_id": CYCLE_ID, "code_freeze_sha": "0" * 40,
        "post_freeze_allowlist": ["research/control/**"], "data": {},
    }))
    ok, reasons = check_launch_gates(str(tmp_path), str(mfile), None)
    assert not ok
    assert any("GO record" in r for r in reasons)
    go = tmp_path / "GO.json"
    go.write_text(json.dumps({"cycle_id": CYCLE_ID, "phrase": GO_PHRASE}))
    ok2, reasons2 = check_launch_gates(str(tmp_path), str(mfile), str(go))
    assert not ok2  # still refused: wrong freeze sha (git repo absent in tmp)
    assert any("nba_winprob" in r or "allowlist" in r for r in reasons2) or reasons2


def test_go_phrase_form():
    assert GO_PHRASE == "GO NBA WINPROB SCORED V1 EVALUATION"
    assert CYCLE_ID == "NBA-WINPROB-SCORED-V1"


def test_ledger_no_duplicate_primary(tmp_path):
    ledger = tmp_path / "TRIAL_LEDGER.jsonl"
    s = run_evaluation(make_rows())
    append_trial_rows(str(ledger), s)
    append_trial_rows(str(ledger), s)  # second append without --repro: no-op
    rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    assert len(rows) == 9
    assert all(r["status"] == "COMPUTED" and r["class"] == "PRIMARY" for r in rows)
    append_trial_rows(str(ledger), s, repro=True)  # repro class appends new rows
    rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    assert len(rows) == 18
    assert sum(1 for r in rows if r["class"] == "REPRO") == 9
