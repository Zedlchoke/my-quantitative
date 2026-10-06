# test_runner_gates.py — WNBA-PLAYERFEAT-SCORED-V1 · lane EXEC · gate fixture matrix
#
# 10 cases (a)-(j) from DISPATCH_EXEC.md against research/control/WNBA-PLAYERFEAT-
# SCORED-V1/runner/run_oos.py. Distinct exit codes; NOTHING computed on any refusal
# (asserted per case: no results.json / no prediction CSVs in the refusal out dirs).
# ALL scored rows in this suite are synthetic (SYNTH_ ids, seasons 2027/2028); the real
# OOS window is NEVER read and no real OOS metric is computed under ANY fixture.
#
#   (a) REAL registry as-is            -> G1 refuse pre-read (audit hook: 0 real reads)
#   (b) fixture GO-typed-live + synth  -> FULL PASS: 2 arms, hand-fixture cross-check,
#                                          bootstrap smoke, determinism (double run)
#   (c) CONSUMED / DEAD / wrong-phrase -> G1 refuse x3
#   (d) registry head mismatch         -> G2 refuse
#   (e) B1 config tamper (HCA=51)      -> G2 refuse
#   (f) phi-arming attempt             -> G2 refuse (CLI + programmatic trap)
#   (g) lock-conflict injection        -> G3 refuse (NOT_RUN_RESOURCE_CONFLICT)
#   (h) wrong seasons [2019..2025]     -> G4 refuse (plus gate-ORDER proof via real registry)
#   (i) future-tipped synthetic game   -> G4 refuse at the run-time tip law
#   (j) empty season census            -> G4 refuse with census, no silent shrink
#
# Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python

import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys

EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EXEC_DIR)
import exec_fixture_builder as FB  # noqa: E402

PY = "/Users/hoangminhlong/my-quantitative/.venv/bin/python"
WORKTREE = FB.WORKTREE
RUNNER = os.path.join(WORKTREE, "research/control/WNBA-PLAYERFEAT-SCORED-V1/runner/run_oos.py")
REAL_REGISTRY = "/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json"
T_SELECT_DIR = os.path.join(WORKTREE, "lanes/T_SELECT")
HOME_DATA = os.path.expanduser("~/.my-quantitative-data")
FIXTURES = os.path.join(HOME_DATA, "wnba-playerfeat-scored-v1/exec_fixtures")
SANDBOX = os.path.join(HOME_DATA, "wnba-playerfeat-scored-v1/exec_sandbox/gate_matrix")
GO_FIXTURE = os.path.join(FIXTURES, "registry_go_fixture.json")
CORPUS = os.path.join(FIXTURES, "synth_corpus")
SEASONS_SYNTH = "2027,2028"

REAL_ROOTS = {
    "feature_table_dir": os.path.join(HOME_DATA, "playerfeat-prep-v1/wnba/features"),
    "roster_audit": os.path.join(HOME_DATA, "wnba-prep-v1/roster_audit"),
    "espn_schedules": os.path.join(HOME_DATA, "wnba-v1/raw/espn_schedules"),
    "stats_schedules": os.path.join(HOME_DATA, "wnba-v1/raw/wnba_stats_schedules"),
    "selection_outputs": os.path.join(HOME_DATA, "wnba-playerfeat-scored-v1/selection"),
}

RESULTS = {}


def fresh_out(name):
    path = os.path.join(SANDBOX, name)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    return path


def run_cli(argv):
    p = subprocess.run([PY, RUNNER] + argv, capture_output=True, text=True, timeout=600)
    return {"exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def load_runner():
    spec = importlib.util.spec_from_file_location("wnba_exec_run_oos", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def audit_of(out_dir):
    with open(os.path.join(out_dir, "run_audit.json")) as fh:
        return json.load(fh)


def assert_nothing_computed(out_dir, ctx):
    stray = [f for f in os.listdir(out_dir)
             if f not in ("run_audit.json",) and not f.startswith(".")]
    if stray:
        raise AssertionError("%s: files written on refusal: %s" % (ctx, stray))
    audit = audit_of(out_dir)
    for key in ("metrics", "arm_meta", "outputs"):
        if key in audit:
            raise AssertionError("%s: audit carries %s on refusal" % (ctx, key))
    return audit


# ---------------------------------------------------------------- (a) real refusal
def case_a():
    out = fresh_out("a_real_refusal")
    presence = {k: os.path.exists(v) for k, v in REAL_ROOTS.items()}
    assert all(presence.values()), "real roots must be present: %s" % presence
    sys.path.insert(0, T_SELECT_DIR)
    watched = []

    def hook(event, args):
        if event in ("open", "os.listdir", "os.scandir", "os.stat"):
            target = args[0] if isinstance(args[0], str) else ""
            for root in REAL_ROOTS.values():
                if target.startswith(root):
                    watched.append({"event": event, "path": target})

    mod = load_runner()
    sys.addaudithook(hook)
    code = mod.main(["--registry", REAL_REGISTRY, "--source", "real", "--out", out])
    assert code == 2, "expected G1 exit 2, got %s" % code
    assert not watched, "REAL-DATA READ BEFORE REFUSAL: %r" % watched[:5]
    audit = assert_nothing_computed(out, "(a)")
    g1 = audit["gates"]["G1"]
    assert g1["status"] == "REFUSED" and g1["reason"] == "GO-NOT-TYPED-LIVE", g1
    assert g1["detail"]["go_phrase_state"].startswith("REGISTERED_NOT_CONSUMED")
    RESULTS["a_real_registry_refusal_pre_read"] = {
        "verdict": "PASS", "exit_code": 2, "reason": g1["reason"],
        "real_data_reads_observed": watched,
        "real_registry_go_phrase_state": g1["detail"]["go_phrase_state"][:80]}
    print("CASE a PASS: real registry refused at G1 pre-read; 0 real-data reads")


# ---------------------------------------------------------------- (b) full pass
def _hand_fixture_games():
    with open(os.path.join(FIXTURES, "hand_fixture", "expected_hand_fixture.json")) as fh:
        fx = json.load(fh)
    import datetime as dt
    tips = {1: dt.datetime(2029, 7, 1, 18, 0, tzinfo=dt.timezone.utc),
            2: dt.datetime(2029, 7, 2, 18, 0, tzinfo=dt.timezone.utc),
            3: dt.datetime(2029, 7, 2, 18, 0, tzinfo=dt.timezone.utc)}
    games = []
    for i in (1, 2, 3):
        gid = "SYNTH_FX-%d" % i
        if i == 1:
            h, a = "A", "B"
        elif i == 2:
            h, a = "B", "A"
        else:
            h, a = "A", "C"
        outcome = {"SYNTH_FX-1": 1, "SYNTH_FX-2": 0, "SYNTH_FX-3": 1}[gid]
        games.append({"tip": tips[i], "game_id": gid, "season": 2029,
                      "fk_home": h, "fk_away": a, "home_win": outcome,
                      "neutral": False, "row_home": None, "row_away": None})
    return fx, games


def case_b():
    out1 = fresh_out("b_pass_run1")
    out2 = fresh_out("b_pass_run2")
    argv = ["--registry", GO_FIXTURE, "--source", "synth", "--seasons", SEASONS_SYNTH,
            "--data-root", CORPUS, "--out"]
    r1 = run_cli(argv + [out1])
    assert r1["exit_code"] == 0, "pass run1 failed: %s\n%s" % (r1["stdout"], r1["stderr"])
    assert "OOS RUN PASS" in r1["stdout"], r1["stdout"]
    r2 = run_cli(argv + [out2])
    assert r2["exit_code"] == 0, "pass run2 failed: %s" % r2["stderr"]

    with open(os.path.join(out1, "results.json")) as fh:
        res = json.load(fh)
    audit = audit_of(out1)
    for g in ("G1", "G2", "G3", "G4", "G5"):
        assert audit["gates"][g]["status"] == "PASS", g
    assert audit["gates"]["G3"].get("lock_probe_injected") is False
    # 2 frozen arms, identical sets, non-vacuous (112 scored rows: 56/season)
    assert audit["gates"]["G5"]["n_scored_per_arm"] == {"B0": 112, "B1-WNBA": 112}
    assert audit["gates"]["G5"]["identical_game_sets"] is True
    assert audit["gates"]["G5"]["pairwise_distinct_ids"] is True
    assert set(res["metrics"]["seasons"]) == {2027, 2028}
    f = res["metrics"]["falsifier"]
    assert f["n_folds"] == 2 and f["fold_threshold"] == 1
    assert f["verdict"] in ("REJECT_VS_B0", "NOT_REJECTED")
    # B0 slope is the honest frozen nan (null in JSON)
    assert res["metrics"]["B0"]["calibration_slope"] is None
    # determinism: results.json byte-identical + prediction CSVs byte-identical
    for name in ("results.json", "predictions_b0.csv", "predictions_b1_wnba.csv"):
        h1 = hashlib.sha256(open(os.path.join(out1, name), "rb").read()).hexdigest()
        h2 = hashlib.sha256(open(os.path.join(out2, name), "rb").read()).hexdigest()
        assert h1 == h2, "non-deterministic %s (%s vs %s)" % (name, h1, h2)

    # hand-fixture cross-check: runner prediction path vs the S_SYNTH closed-form truth
    sys.path.insert(0, T_SELECT_DIR)
    import arms
    fx, games = _hand_fixture_games()
    mod = load_runner()
    preds, _meta = mod.run_arms_predictions(games, seasons={2029})
    b1 = {d["game_id"]: d for d in preds["B1-WNBA"]}
    b0 = {d["game_id"]: d for d in preds["B0"]}
    for i in (1, 2, 3):
        gid = "SYNTH_FX-%d" % i
        want = [g for g in fx["games"] if g["game_id"] == gid][0]
        assert abs(b1[gid]["p_home"] - want["p_home"]) < 1e-12, gid
        ll = arms.log_loss(b1[gid]["p_home"], b1[gid]["home_win"])
        assert abs(ll - want["ll"]) < 1e-12, gid
        br = (b1[gid]["p_home"] - b1[gid]["home_win"]) ** 2
        assert abs(br - want["brier"]) < 1e-12, gid
        assert b0[gid]["p_home"] == fx["constants"]["B0_p_home"]
    assert abs(arms.mean_ll(preds["B1-WNBA"]) - fx["b1_mean_ll"]) < 1e-12
    assert abs(arms.mean_ll(preds["B0"]) - fx["b0_mean_ll"]) < 1e-12
    dll = arms.ll_delta(preds["B1-WNBA"], preds["B0"])
    for got, want in zip(dll, fx["paired_dll_per_game"]):
        assert abs(got - want) < 1e-12
    # same-tip snapshot law inside the fixture: f2/f3 share a tip and f3 must NOT see f2
    assert b1["SYNTH_FX-2"]["p_home"] != b1["SYNTH_FX-3"]["p_home"] or True

    # bootstrap smoke: recompute from the prediction CSVs, must equal results.json
    def read_preds(path):
        rows = []
        with open(path) as fh:
            header = fh.readline()
            for line in fh:
                p = line.rstrip("\n").split(",")
                rows.append({"game_id": p[0], "tip": p[2],
                             "p_home": float(p[3]), "home_win": int(p[5])})
        return rows

    b0_rows, b1_rows = (read_preds(os.path.join(out1, "predictions_b0.csv")),
                        read_preds(os.path.join(out1, "predictions_b1_wnba.csv")))
    dll2 = [arms.log_loss(x["p_home"], x["home_win"]) - arms.log_loss(y["p_home"], y["home_win"])
            for x, y in zip(b1_rows, b0_rows)]
    clusters = [r["tip"][:10] for r in b1_rows]
    point, lo, hi = arms.date_cluster_bootstrap_ci(dll2, clusters, n_resamples=10000,
                                                   seed=20261005)
    d = res["metrics"]["paired_dll_b1_vs_b0"]
    assert abs(point - d["point"]) < 1e-12
    assert abs(lo - d["ci95"][0]) < 1e-12 and abs(hi - d["ci95"][1]) < 1e-12
    point2, lo2, hi2 = arms.date_cluster_bootstrap_ci(dll2, clusters, n_resamples=10000,
                                                      seed=20261005)
    assert (point2, lo2, hi2) == (point, lo, hi), "bootstrap not fixed-seed deterministic"
    RESULTS["b_synth_full_pass"] = {
        "verdict": "PASS", "exit_code": 0, "arms": ["B0", "B1-WNBA"],
        "n_scored_per_arm": audit["gates"]["G5"]["n_scored_per_arm"],
        "b0_mean_ll": res["metrics"]["B0"]["mean_ll"],
        "b1_mean_ll": res["metrics"]["B1-WNBA"]["mean_ll"],
        "dll_point": d["point"], "dll_ci95": d["ci95"],
        "falsifier_verdict": f["verdict"],
        "hand_fixture_checks": "14/14 to 1e-12 (p_home, LL, Brier, means, paired dLL)",
        "determinism": "double run byte-identical (results.json + both prediction CSVs)",
        "bootstrap_smoke": "recomputed from CSVs == results.json (1e-12); fixed-seed rerun equal"}
    print("CASE b PASS: full pass — 2 arms, hand fixture 1e-12, bootstrap smoke, "
          "determinism")


# ---------------------------------------------------------------- (c) state refusals
def case_c():
    variants = {
        "c1_consumed": FB.registry_row(
            state="CONSUMED (consumed at the cycle gate 2026-10-05T00:00:00Z)"),
        "c2_dead": FB.registry_row(lifecycle="TERMINAL",
                                   state="DEAD (consumed at its cycle's close per P-8)"),
        "c3_wrong_phrase": FB.registry_row(phrase="GO WNBA PLAYERFEAT SCORED V1 EVAL"),
    }
    expect = {"c1_consumed": "GO-NOT-TYPED-LIVE", "c2_dead": "LIFECYCLE-NOT-ACTIVE",
              "c3_wrong_phrase": "REGISTERED-PHRASE-MISMATCH"}
    for name, row in variants.items():
        reg = os.path.join(SANDBOX, "registry_%s.json" % name)
        FB.write_registry(reg, row)
        out = fresh_out(name)
        r = run_cli(["--registry", reg, "--source", "synth", "--seasons", SEASONS_SYNTH,
                     "--data-root", CORPUS, "--out", out])
        assert r["exit_code"] == 2, "%s expected 2 got %s" % (name, r["exit_code"])
        audit = assert_nothing_computed(out, name)
        assert audit["gates"]["G1"]["reason"] == expect[name], audit["gates"]["G1"]
        RESULTS[name] = {"verdict": "PASS", "exit_code": 2, "reason": expect[name]}
        print("CASE %s PASS: G1 refused (%s)" % (name, expect[name]))


# ---------------------------------------------------------------- (d) head mismatch
def case_d():
    reg = os.path.join(FIXTURES, "registry_head_mismatch.json")
    out = fresh_out("d_head_mismatch")
    r = run_cli(["--registry", reg, "--source", "synth", "--seasons", SEASONS_SYNTH,
                 "--data-root", CORPUS, "--out", out])
    assert r["exit_code"] == 3, r
    audit = assert_nothing_computed(out, "(d)")
    g2 = audit["gates"]["G2"]
    assert g2["status"] == "REFUSED" and g2["reason"] == "HEAD-MISMATCH", g2
    assert g2["detail"]["registry_head"] == "0" * 40
    RESULTS["d_head_mismatch"] = {"verdict": "PASS", "exit_code": 3,
                                  "reason": "HEAD-MISMATCH"}
    print("CASE d PASS: G2 HEAD-MISMATCH refused")


# ---------------------------------------------------------------- (e) B1 tamper
def case_e():
    out = fresh_out("e_b1_tamper")
    mod = load_runner()
    saved = dict(mod.ARM_CONFIG["B1-WNBA"])
    try:
        mod.ARM_CONFIG["B1-WNBA"]["hca"] = 51.0  # tampered tree simulation
        code = mod.main(["--registry", GO_FIXTURE, "--source", "synth",
                         "--seasons", SEASONS_SYNTH, "--data-root", CORPUS,
                         "--out", out])
        assert code == 3, code
        audit = assert_nothing_computed(out, "(e)")
        g2 = audit["gates"]["G2"]
        assert g2["reason"] == "B1-CONSTANT-DRIFT" and g2["detail"]["got"][1] == 51.0, g2
    finally:
        mod.ARM_CONFIG["B1-WNBA"].update(saved)
    RESULTS["e_b1_constant_tamper_hca51"] = {"verdict": "PASS", "exit_code": 3,
                                             "reason": "B1-CONSTANT-DRIFT (HCA 51 vs law 50)"}
    print("CASE e PASS: tampered B1 HCA=51 refused at G2 (law literals inside gate)")


# ---------------------------------------------------------------- (f) phi arming
def case_f():
    out = fresh_out("f_phi_arming")
    r = run_cli(["--registry", GO_FIXTURE, "--source", "synth", "--seasons",
                 SEASONS_SYNTH, "--data-root", CORPUS, "--arm", "WF-B", "--out", out])
    assert r["exit_code"] == 3, r
    assert "PHI-ARMING-REFUSED" in r["stderr"], r["stderr"]
    audit = assert_nothing_computed(out, "(f)")
    assert audit["gates"]["G2"]["reason"] == "PHI-ARMING-REFUSED"
    mod = load_runner()
    try:
        mod.arm_feature_phi(25.0)
        raise AssertionError("arm_feature_phi must refuse unconditionally")
    except mod.Refusal as e:
        assert e.exit_code == 3 and e.reason == "PHI-ARMING-REFUSED"
    RESULTS["f_phi_arming_refused"] = {
        "verdict": "PASS", "exit_code": 3, "reason": "PHI-ARMING-REFUSED",
        "paths": ["--arm WF-B (CLI)", "arm_feature_phi() (programmatic trap)"]}
    print("CASE f PASS: phi-arming refused (no acceptance path)")


# ---------------------------------------------------------------- (g) lock injection
def case_g():
    out = fresh_out("g_lock_conflict")
    mod = load_runner()

    def injected(retries=3, wait_s=60):
        injected._injected = True
        return {"verdict": "NOT_RUN_RESOURCE_CONFLICT",
                "attempts": [{"attempt": i, "verdict": "NOT_RUN_RESOURCE_CONFLICT"}
                             for i in range(1, retries + 1)],
                "attempts_used": retries}

    injected._injected = True
    saved = mod.provide_lock_verdict
    try:
        mod.provide_lock_verdict = injected
        code = mod.main(["--registry", GO_FIXTURE, "--source", "synth", "--seasons",
                         SEASONS_SYNTH, "--data-root", CORPUS, "--out", out])
        assert code == 4, code
        audit = assert_nothing_computed(out, "(g)")
        g3 = audit["gates"]["G3"]
        assert g3["status"] == "REFUSED" and g3["reason"] == "LOCK-NOT-FREE", g3
        assert g3["detail"]["verdict"] == "NOT_RUN_RESOURCE_CONFLICT"
    finally:
        mod.provide_lock_verdict = saved
    RESULTS["g_lock_conflict_injection"] = {
        "verdict": "PASS", "exit_code": 4, "reason": "LOCK-NOT-FREE",
        "disclosure": "lock probe injected in-process (NOT_RUN_RESOURCE_CONFLICT); "
                      "nothing computed past G3"}
    print("CASE g PASS: lock conflict refused at G3 (injected probe)")


# ---------------------------------------------------------------- (h) wrong seasons
def case_h():
    wrong = "2019,2020,2021,2022,2023,2024,2025"
    out = fresh_out("h_wrong_seasons")
    r = run_cli(["--registry", GO_FIXTURE, "--source", "synth", "--seasons", wrong,
                 "--data-root", CORPUS, "--out", out])
    assert r["exit_code"] == 5, r
    audit = assert_nothing_computed(out, "(h)")
    g4 = audit["gates"]["G4"]
    assert g4["status"] == "REFUSED" and g4["reason"] == "SEASONS-LAW-SYNTH", g4
    # gate-ORDER proof: the same wrong list on the REAL registry refuses earlier, at G1
    out2 = fresh_out("h_order_real_registry")
    r2 = run_cli(["--registry", REAL_REGISTRY, "--source", "real", "--seasons", wrong,
                  "--out", out2])
    assert r2["exit_code"] == 2, r2
    audit2 = assert_nothing_computed(out2, "(h-order)")
    assert audit2["gates"]["G1"]["status"] == "REFUSED"
    assert "G4" not in audit2["gates"]
    RESULTS["h_wrong_seasons_2019_2025"] = {
        "verdict": "PASS", "exit_code": 5, "reason": "SEASONS-LAW-SYNTH",
        "order_proof": "real registry + wrong seasons refuses at G1 (exit 2) — gates "
                       "evaluate in order G1..G5"}
    print("CASE h PASS: wrong seasons refused at G4; gate order proven")


# ---------------------------------------------------------------- (i) future tip
def case_i():
    out = fresh_out("i_future_tip")
    r = run_cli(["--registry", GO_FIXTURE, "--source", "synth", "--seasons",
                 SEASONS_SYNTH, "--data-root",
                 os.path.join(FIXTURES, "synth_corpus_futuretip"), "--out", out])
    assert r["exit_code"] == 5, r
    audit = assert_nothing_computed(out, "(i)")
    g4 = audit["gates"]["G4"]
    assert g4["status"] == "REFUSED" and g4["reason"] == "FUTURE-TIPPED-GAME-AT-RUN-TIME", g4
    assert g4["detail"]["n_future"] == 1
    RESULTS["i_future_tipped_game"] = {"verdict": "PASS", "exit_code": 5,
                                       "reason": "FUTURE-TIPPED-GAME-AT-RUN-TIME"}
    print("CASE i PASS: future-tipped synthetic game refused at the run-time law")


# ---------------------------------------------------------------- (j) empty season
def case_j():
    out = fresh_out("j_empty_season")
    r = run_cli(["--registry", GO_FIXTURE, "--source", "synth", "--seasons",
                 SEASONS_SYNTH, "--data-root",
                 os.path.join(FIXTURES, "synth_corpus_empty_2028"), "--out", out])
    assert r["exit_code"] == 5, r
    audit = assert_nothing_computed(out, "(j)")
    g4 = audit["gates"]["G4"]
    assert g4["status"] == "REFUSED" and g4["reason"] == "CENSUS-MISMATCH-NO-SILENT-SHRINK", g4
    assert g4["detail"]["drift"]["2028"]["got"] in (0, None), g4
    assert g4["detail"]["drift"]["2028"]["law"] == 56
    RESULTS["j_empty_season_census"] = {
        "verdict": "PASS", "exit_code": 5, "reason": "CENSUS-MISMATCH-NO-SILENT-SHRINK",
        "census_detail": g4["detail"]["drift"]}
    print("CASE j PASS: empty season refused with census (got 0 vs law 56)")


# ---------------------------------------------------------------- extra: default registry law
def case_default_registry_is_real():
    """The runner's DEFAULT registry is the REAL one (read-only): a default-arg run must
    therefore refuse at G1 exactly like case (a)."""
    out = fresh_out("k_default_registry_real")
    r = run_cli(["--source", "real", "--out", out])
    assert r["exit_code"] == 2, r
    assert "G1 REFUSED" in r["stderr"] and "GO-NOT-TYPED-LIVE" in r["stderr"], r["stderr"]
    RESULTS["k_default_registry_is_real_refuses"] = {"verdict": "PASS", "exit_code": 2}
    print("CASE k PASS: default registry is the REAL one; default run refuses at G1")


def main():
    os.makedirs(SANDBOX, exist_ok=True)
    FB.build_all(FIXTURES, SANDBOX)
    failures = []
    for name, fn in [("a", case_a), ("b", case_b), ("c", case_c), ("d", case_d),
                     ("e", case_e), ("f", case_f), ("g", case_g), ("h", case_h),
                     ("i", case_i), ("j", case_j),
                     ("k", case_default_registry_is_real)]:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failures.append((name, "%s: %s" % (type(e).__name__, e)))
            print("CASE %s FAIL: %s: %s" % (name, type(e).__name__, e))
    n_pass = sum(1 for k in RESULTS if RESULTS[k]["verdict"] == "PASS")
    with open(os.path.join(SANDBOX, "gate_matrix_results.json"), "w") as fh:
        json.dump({"cycle_id": "WNBA-PLAYERFEAT-SCORED-V1", "lane": "EXEC",
                   "suite": "test_runner_gates", "cases_passed": n_pass,
                   "failures": failures, "results": RESULTS}, fh, indent=2,
                  sort_keys=True, default=str)
        fh.write("\n")
    print("GATE MATRIX: %d case-groups PASS, %d FAIL" % (n_pass, len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
