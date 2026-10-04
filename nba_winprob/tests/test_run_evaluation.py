"""Runner v2 tests: fold isolation, train-only standardization, B0/B1 wiring,
per-fold outputs + verdicts, gates v2, ledger discipline, synthetic selftest."""
import json
import random

import pytest

from nba_winprob.protocol import ARMS, RNG_SEED, TEST_SEASONS
from nba_winprob.run_evaluation import (
    CYCLE_ID, GO_PHRASE, REGISTERED_COMPARISONS, append_trial_rows,
    check_launch_gates, load_rows, run_evaluation, synthetic_selftest,
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


def test_b0_refit_and_fold_isolation():
    rows = make_rows()
    s = run_evaluation(rows, n_boot=50)
    for season in TEST_SEASONS:
        train = [r for r in rows if r["season"] < season and not r["is_playoffs"]]
        rate = sum(1 for r in train if r["home_win"]) / len(train)
        assert abs(s["fold_meta"][season]["b0_rate_train"] - rate) < 1e-12
    rows2 = [dict(r) for r in rows] + [dict(r, season=2030) for r in make_rows(seed=11)[:50]]
    s2 = run_evaluation(rows2, n_boot=50)
    for season in TEST_SEASONS:
        assert s2["fold_meta"][season]["b0_rate_train"] == s["fold_meta"][season]["b0_rate_train"]


def test_b1_uses_precomputed_columns():
    rows = make_rows()
    for r in rows:
        r["p_b1"]["B1-b"] = 0.25
    s = run_evaluation(rows, n_boot=50)
    ys = [1 if r["home_win"] else 0 for r in rows
          if r["season"] in TEST_SEASONS and not r["is_playoffs"]]
    exp = sum((0.25 - y) ** 2 for y in ys) / len(ys)
    assert abs(s["arms"]["B1-b"]["pooled_rs"]["brier"] - exp) < 1e-9


def test_b2_train_only_standardization():
    s1 = run_evaluation(make_rows(), n_boot=50)
    rows2 = [dict(r) for r in make_rows()]
    for r in rows2:
        if r["season"] in TEST_SEASONS:
            r["features"] = {k: v + 5.0 for k, v in r["features"].items()}
    s2 = run_evaluation(rows2, n_boot=50)
    assert s1["verdicts"]["B1star"] == s2["verdicts"]["B1star"]
    assert s1["arms"]["B2-a"]["pooled_rs"]["log_loss"] != s2["arms"]["B2-a"]["pooled_rs"]["log_loss"]


def test_output_completeness_v2():
    s = run_evaluation(make_rows(), n_boot=50)
    assert len(s["arms"]) == 9
    # per-fold AND pooled reliability + slope for every arm
    for arm in s["arms"].values():
        assert "reliability" in arm["pooled_rs"] and "calibration_slope" in arm["pooled_rs"]
        for f in arm["folds"].values():
            assert "reliability" in f and "calibration_slope" in f
    # 11 registered comparisons, pooled AND per fold
    assert len(s["comparisons"]["pooled"]) == 11 == len(REGISTERED_COMPARISONS)
    for key in s["comparisons"]["pooled"]:
        assert set(s["comparisons"]["per_fold"][key]) == {str(x) for x in TEST_SEASONS}
    # verdicts emitted
    v = s["verdicts"]
    for k in ("T1_discriminative_gain", "T2_calibration", "T3_floor_safety"):
        assert isinstance(v[k]["PASS"], bool)
    assert isinstance(v["PROGRAM_PASS"], bool) and isinstance(v["REJECT"]["ANY"], bool)
    for h in ("H1_dynamic_strength", "H2_home_court", "H3_rest_schedule"):
        assert isinstance(v["hypotheses"][h]["REJECT"], bool)


def test_playoffs_reported_separately():
    s = run_evaluation(make_rows(), n_boot=50)
    assert s["arms"]["B2-a"]["pooled_playoffs_separate"]["n"] > 0


def test_synthetic_selftest_end_to_end():
    summary = synthetic_selftest()
    assert len(summary["arms"]) == 9 and len(summary["comparisons"]["pooled"]) == 11


def test_launch_gates_v2(tmp_path):
    mfile = tmp_path / "FREEZE_MANIFEST.json"
    mfile.write_text(json.dumps({
        "schema": "nba_winprob_scored_freeze@2", "cycle_id": CYCLE_ID,
        "code_freeze_sha": "0" * 40, "post_freeze_allowlist": ["research/control/**"],
        "pinned_games": "/nonexistent/games.csv", "pinned_features": "/nonexistent/features.csv",
        "data": {},
    }))
    ok, reasons = check_launch_gates(str(tmp_path), str(mfile), None,
                                     games="/somewhere/else.csv")
    assert not ok
    txt = " ".join(reasons)
    assert "GO record" in txt and "pinned" in txt and "A7" in txt
    go = tmp_path / "GO.json"
    go.write_text(json.dumps({"phrase": "WRONG PHRASE", "cycle_id": CYCLE_ID,
                              "typed_by": "owner", "typed_at": "2026-01-01T00:00:00Z"}))
    ok2, reasons2 = check_launch_gates(str(tmp_path), str(mfile), str(go))
    assert not ok2 and any("phrase" in r for r in reasons2)


def test_go_phrase_form():
    assert GO_PHRASE == "GO NBA WINPROB SCORED V1 EVALUATION"
    assert CYCLE_ID == "NBA-WINPROB-SCORED-V1"


def test_ledger_no_duplicate_primary(tmp_path):
    ledger = tmp_path / "TRIAL_LEDGER.jsonl"
    s = run_evaluation(make_rows(), n_boot=50)
    append_trial_rows(str(ledger), s)
    append_trial_rows(str(ledger), s)
    rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    assert len(rows) == 9 and all(r["class"] == "PRIMARY" for r in rows)
    append_trial_rows(str(ledger), s, repro=True)
    rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    assert len(rows) == 18 and sum(1 for r in rows if r["class"] == "REPRO") == 9


def test_load_rows_schema_guard(tmp_path):
    gf = tmp_path / "games.csv"
    ff = tmp_path / "features.csv"
    gf.write_text("src_game_id,season,date,is_playoffs,home_win\nX1,2010,2010-01-01,False,True\n")
    ff.write_text("src_game_id,rest_diff\nX1,0\n")  # missing elo_diff etc.
    with pytest.raises(KeyError):
        load_rows(str(gf), str(ff))
