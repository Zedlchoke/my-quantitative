"""NFL scored-runner tests: tie law, fold isolation, output completeness,
gates, ledger, selftest + REAL-CSV path (schema/rows only, NO metrics)."""
import json
import os
import random

import pytest

from nfl_winprob.protocol import ARMS, TEST_SEASONS
from nfl_winprob.run_evaluation import (
    CYCLE_ID, GO_PHRASE, REGISTERED_COMPARISONS, append_trial_rows,
    check_launch_gates, load_rows, run_evaluation, synthetic_selftest,
)

FEATURE_COLS = ["elo_diff", "rest_diff", "short_week_home", "short_week_away", "form_home", "form_away"]


def make_rows(seed=7):
    rng = random.Random(seed)
    rows = []
    order = 0
    for season in range(2012, 2027):
        for week in range(1, 18):
            for _ in range(4):
                order += 1
                rows.append({
                    "src_game_id": f"R{order:06d}",
                    "date": f"{season}-10-{(week % 28) + 1:02d}",
                    "season": season, "is_playoffs": week > 16,
                    "home_win": rng.random() < 0.57,
                    "tie": rng.random() < 0.002,
                    "features": {c: rng.gauss(0, 1) for c in FEATURE_COLS},
                    "p_b1": {f"B1-{s}": 0.55 for s in ("a", "b", "c", "d")},
                })
    return rows


def test_tie_law_excluded_and_disclosed():
    rows = make_rows()
    s = run_evaluation(rows, n_boot=50)
    n_ties = sum(1 for r in rows if r["tie"] and r["season"] in TEST_SEASONS)
    disclosed = sum(s["fold_meta"][x]["n_ties_excluded_disclosed"] for x in TEST_SEASONS)
    assert disclosed == n_ties
    # B0 train rate excludes ties (train filter)
    for season in TEST_SEASONS:
        train = [r for r in rows if r["season"] < season and not r["is_playoffs"] and not r["tie"]]
        rate = sum(1 for r in train if r["home_win"]) / len(train)
        assert abs(s["fold_meta"][season]["b0_rate_train"] - rate) < 1e-12


def test_output_completeness():
    s = run_evaluation(make_rows(), n_boot=50)
    assert len(s["arms"]) == 9 and len(s["comparisons"]["pooled"]) == 11 == len(REGISTERED_COMPARISONS)
    for arm in s["arms"].values():
        assert "reliability" in arm["pooled_rs"] and "calibration_slope" in arm["pooled_rs"]
        for f in arm["folds"].values():
            assert "reliability" in f and "calibration_slope" in f
    v = s["verdicts"]
    assert isinstance(v["PROGRAM_PASS"], bool) and isinstance(v["REJECT"]["ANY"], bool)
    for h in ("H1_dynamic_strength", "H2_home_court", "H3_rest_schedule"):
        assert isinstance(v["hypotheses"][h]["REJECT"], bool)


def test_synthetic_selftest():
    summary = synthetic_selftest()
    assert len(summary["arms"]) == 9 and len(summary["comparisons"]["pooled"]) == 11


def test_launch_gates(tmp_path):
    mfile = tmp_path / "FREEZE_MANIFEST.json"
    mfile.write_text(json.dumps({
        "schema": "nfl_winprob_scored_freeze@1", "cycle_id": CYCLE_ID,
        "code_freeze_sha": "0" * 40, "post_freeze_allowlist": ["research/control/**"],
        "pinned_games": "/nonexistent.csv", "pinned_features": "/nonexistent.csv", "data": {},
    }))
    ok, reasons = check_launch_gates(str(tmp_path), str(mfile), None, games="/elsewhere.csv")
    assert not ok and "GO record" in " ".join(reasons) and "pinned" in " ".join(reasons)


def test_ledger(tmp_path):
    ledger = tmp_path / "LEDGER.jsonl"
    s = run_evaluation(make_rows(), n_boot=50)
    append_trial_rows(str(ledger), s)
    append_trial_rows(str(ledger), s)
    rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    assert len(rows) == 9


def test_go_phrase_form():
    assert GO_PHRASE == "GO NFL WINPROB SCORED V1 EVALUATION"
    assert CYCLE_ID == "NFL-WINPROB-SCORED-V1"


# ---- REAL-CSV path (schema/row-count/load only; NO outcome metric) --------

DATA = os.path.expanduser("~/.my-quantitative-data/nfl-nflverse-v1/derived")
GAMES = os.path.join(DATA, "games_nfl.csv")
FEATURES = os.path.join(DATA, "features_nfl.csv")

pytestmark_real = pytest.mark.skipif(not (os.path.exists(GAMES) and os.path.exists(FEATURES)),
                                     reason="derived NFL files absent")


@pytestmark_real
def test_real_features_header():
    import csv as _csv
    with open(FEATURES, newline="", encoding="utf-8") as f:
        header = next(_csv.reader(f))
    assert "elo_diff" in header
    for arm in ("B1-a", "B1-b", "B1-c", "B1-d"):
        assert f"elo_diff_{arm}" in header and f"p_home_{arm}" in header
    assert not any(tok in header for tok in ("spread", "moneyline", "home_win", "pts"))


@pytestmark_real
def test_real_csv_load_and_split_counts():
    rows = load_rows(GAMES, FEATURES)
    assert len(rows) == 7066
    reg = sum(1 for r in rows if not r["is_playoffs"])
    post = sum(1 for r in rows if r["is_playoffs"])
    assert reg == 6768 and post == 298
    trs = sum(1 for r in rows if r["season"] in TEST_SEASONS and not r["is_playoffs"] and not r["tie"])
    tpo = sum(1 for r in rows if r["season"] in TEST_SEASONS and r["is_playoffs"] and not r["tie"])
    ties = sum(1 for r in rows if r["season"] in TEST_SEASONS and r["tie"])
    assert trs == 1865 and tpo == 89 and ties == 6   # 1871 raw RS incl 6 ties (TIE LAW excludes them)
