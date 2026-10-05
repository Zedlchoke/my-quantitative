"""record_batch.py — PIPE lane recorder CLI, cycle NFL-WINPROB-NG-SCORED-V1.

The REAL prediction-record pipeline (research/control/NFL-WINPROB-NG-SCORED-V1/
recorder/), tested end-to-end on SYNTHETIC FIXTURES ONLY.

Modes
-----
--mode selftest        Hand-computed fixtures: margin arithmetic, kickoff-UTC
                       canonicalization (DST edges), state-carry counts +
                       hand-computed Elo, identical-kickoff exclusion,
                       future-score abort, p-format guard, fresh-pull guard,
                       combined-vs-warmup replay equivalence, arm-digest law.
--mode warmup-check    REAL smoke check of stages (a)+(b) on the frozen
                       registration snapshot with batch_time = now. Emits
                       AGGREGATE COUNTS ONLY (games per season, lineages, C3
                       prior applications, 2026 completed games absorbed).
                       ZERO per-game probability values for real games —
                       this mode never calls the predict stage.
--mode e2e-synth       END-TO-END on synthetic fixtures (SYNTH_ ids, 2027+
                       kickoffs, synthetic completed seasons so C3 priors
                       exercise): nominal week -> margin gate -> sandbox
                       ledger -> chain validation; margin-violation refusal
                       (nothing written); future-score abort (nothing
                       written); double-run byte-identical determinism.

ABSOLUTE LAWS (hard-wired, not optional):
  - p_home is computed ONLY for SYNTH_-prefixed synthetic games. The predict
    stage refuses any non-SYNTH_ game id.
  - No real prediction ledger is created; every ledger write goes to the
    --ledger-dir argument (sandbox in all lane runs).
  - No LL/metric is computed on ANY game during warmup (state-carry updates
    are not evaluation — FREEZE_ERRATUM_R2 STATE-CARRY law).
  - No git commands. Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import frozen_refs as frozen  # noqa: E402
import pipeline as rec_pipe  # noqa: E402
import priors as rec_priors  # noqa: E402
import schedule as rec_sched  # noqa: E402

TS_FMT = "%Y-%m-%dT%H:%M:%SZ"
LANE_DIR = _HOME_WORKTREE = frozen.WORKTREE / "lanes" / "PIPE"
RECORDER_SANDBOX = Path.home() / ".my-quantitative-data" / "nfl-ng-scored-v1" / "recorder_sandbox"
E2E_DIR = RECORDER_SANDBOX / "e2e"

# Sandbox ledger identity (clearly NOT the real cycle; tool §1 filename law)
SANDBOX_CYCLE = "NFL-WINPROB-NG-SCORED-V1-PIPETEST"
SANDBOX_SEASON = 2030
SANDBOX_FREEZE_UTC = "2030-09-01T00:00:00Z"
SANDBOX_RECORDED_BY = "PIPE-SANDBOX-RECORDER"
# S_SYNTH's sandbox genesis (kept distinct; its ledger is a different artifact)
S_SYNTH_SANDBOX_GENESIS = "e59ec10c61fa318969aa962589b8588f67b1f6aa6e36fd504b11e8e0b2d265b0"

SYNTH_GENESIS_DESCRIPTOR = {
    "schema": "nfl_ng_recorder_sandbox_genesis@1",
    "kind": "SANDBOX_SYNTHETIC_GENESIS_RECORDER",
    "cycle_id": SANDBOX_CYCLE,
    "season": SANDBOX_SEASON,
    "note": (
        "PIPE lane recorder sandbox genesis; synthetic games only (SYNTH_ ids, "
        "2027+ kickoffs); NOT the freeze GENESIS; no real prediction ledger is created"
    ),
}


def sandbox_genesis_digest() -> str:
    return frozen.sha256_text(frozen.canonical_json(SYNTH_GENESIS_DESCRIPTOR))


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime(TS_FMT)


def _assert_synth_only(games) -> None:
    """ABSOLUTE: the predict/append path accepts SYNTH_ games only. Any real
    (non-SYNTH_) game id reaching this point is a design bug -> STOP."""
    bad = [g["game_id"] for g in games if not str(g["game_id"]).startswith("SYNTH_")]
    if bad:
        raise RuntimeError(
            f"DESIGN BUG: non-synthetic game ids reached the prediction path: {bad[:5]}; STOP"
        )


# ===========================================================================
# --mode selftest — hand-computed fixtures
# ===========================================================================

def _tiny_warm_rows():
    """3 completed games, 4 lineages, hand-computable Elo stream (2028)."""
    def ns(day, hour):
        d = dt.datetime(2028, 1, day, hour, tzinfo=dt.timezone.utc)
        return int(d.timestamp()) * 10**9

    return [
        dict(kickoff_ns=ns(10, 17), home="SYT01", away="SYT02", s_home=1.0,
             season=2028, week=1, game_id="SYNTH_ST_G1", is_neutral=False),
        dict(kickoff_ns=ns(11, 17), home="SYT03", away="SYT04", s_home=0.5,
             season=2028, week=1, game_id="SYNTH_ST_G2", is_neutral=False),
        dict(kickoff_ns=ns(12, 17), home="SYT01", away="SYT03", s_home=0.0,
             season=2028, week=2, game_id="SYNTH_ST_G3", is_neutral=False),
    ]


def _tiny_target_rows():
    def ns(day, hour):
        d = dt.datetime(2029, 1, day, hour, tzinfo=dt.timezone.utc)
        return int(d.timestamp()) * 10**9

    t = ns(10, 17)
    return [
        dict(game_id="SYNTH_ST_T1", season=2029, week=1, game_type="REG",
             kickoff_ns=t, home_abbr="SYT01", away_abbr="SYT02",
             home_lg="SYT01", away_lg="SYT02", is_neutral=False),
        dict(game_id="SYNTH_ST_T2", season=2029, week=1, game_type="REG",
             kickoff_ns=t, home_abbr="SYT03", away_abbr="SYT04",
             home_lg="SYT03", away_lg="SYT04", is_neutral=False),
    ]


def _tiny_z(arms):
    """Nonzero synthetic prior E for target season 2029, standardized by the
    FROZEN arms.z_standardize (same standardization the real path uses)."""
    E = {"SYT01": 0.06, "SYT02": -0.02, "SYT03": 0.10, "SYT04": -0.08}
    z = arms.z_standardize(E)
    assert len(z) == 4 and all(v != 0.0 for v in z.values())
    return {(2029, lg): v for lg, v in z.items()}


def mode_selftest() -> dict:
    arms = frozen.load_frozen_arms()
    ledger = frozen.load_ledger_tool()
    rec_pipe.init_arm_digests(frozen)
    results = {}

    # (1) arm-param equality law: recomputed digests == freeze pins ----------
    digests = frozen.verify_arm_config_digests()
    assert digests == frozen.ARM_CONFIG_DIGESTS
    results["arm_digest_law"] = "PASS"

    # (2) margin arithmetic (hand) -------------------------------------------
    m = rec_pipe.check_margin("2026-10-08T18:15:00Z", "2026-10-09T00:15:00Z")
    assert abs(m - 6.0) < 1e-9, m  # exactly 6h: >= passes (boundary accepted)
    for rec, kick in (
        ("2026-10-08T18:15:01Z", "2026-10-09T00:15:00Z"),  # 5h59m59s
        ("2026-10-09T00:15:00Z", "2026-10-09T00:15:00Z"),  # 0h
        ("2026-10-09T01:00:00Z", "2026-10-09T00:15:00Z"),  # after kickoff
    ):
        try:
            rec_pipe.check_margin(rec, kick)
            raise AssertionError(f"margin check did NOT refuse {rec} -> {kick}")
        except rec_pipe.MarginRefusal:
            pass
    results["margin_arithmetic"] = "PASS (6h boundary accepted; 5h59m59s/0h/post-kickoff refused)"

    # (3) kickoff-UTC canonicalization (frozen arms.kickoff_utc, hand-derived)
    # ET offsets: EDT = UTC-4 (summer), EST = UTC-5 (winter); DST 2026 ends
    # Nov 1 02:00 local, so 13:00 local on Nov 1 is EST.
    cases = [
        (("2026-10-11", "13:30"), "2026-10-11T17:30:00Z"),  # London, EDT
        (("2026-10-08", "20:15"), "2026-10-09T00:15:00Z"),  # TB_DAL week-5 opener
        (("2026-11-01", "13:00"), "2026-11-01T18:00:00Z"),  # fall-back day -> EST
        (("2026-12-06", "13:00"), "2026-12-06T18:00:00Z"),  # winter EST
        (("2026-07-01", "12:00"), "2026-07-01T16:00:00Z"),  # summer EDT
    ]
    for (gd, gt), expected in cases:
        got = arms.kickoff_utc(gd, gt).strftime(TS_FMT)
        assert got == expected, f"kickoff_utc({gd!r},{gt!r}) = {got} != {expected}"
    results["kickoff_canonicalization"] = "PASS (EDT/EST/fall-back/night edges)"

    # (4) state-carry counts + hand-computed Elo ------------------------------
    warm = _tiny_warm_rows()
    gs = rec_sched.rows_to_gameset(arms, warm)
    recs = arms.replay_elo(gs)
    assert len(recs) == 3
    r1, r2, r3 = recs
    # hand Elo: g1 T1 beats T2 from 1500/1500 (e=0.5, K=40): +20/-20
    assert abs(r1.r_home - 1500.0) < 1e-12 and abs(r1.e_home - 0.5) < 1e-12
    # g2 tie from 1500/1500: e=0.5, S=0.5 -> no movement (hand: 0)
    # g3: T1 (1520) at home vs T3 (1500): e = sig(20/400); T3 wins (s_home=0)
    e_g3 = 1.0 / (1.0 + math.exp(-(20.0 / 400.0)))
    assert abs(r3.r_home - 1520.0) < 1e-12 and abs(r3.r_away - 1500.0) < 1e-12
    assert abs(r3.e_home - e_g3) < 1e-12
    # post-g3 updates (hand): T1 += 40*(0 - e_g3); T3 += 40*(1 - (1-e_g3))
    t1_after_g3 = 1520.0 + 40.0 * (0.0 - e_g3)
    t3_after_g3 = 1500.0 + 40.0 * (1.0 - e_g3)
    target = _tiny_target_rows()
    per_arm, _handles = rec_pipe.predict_target_week(arms, warm, target, _tiny_z(arms))
    # target prediction from the warmed state: T1 vs T2 at season 2029.
    # Hand computation MUST include the frozen lazy season reversion at the
    # lineages' first prediction of 2029: R <- 1500 + (2/3)(R - 1500).
    t1_after_g3 = 1520.0 + 40.0 * (0.0 - e_g3)
    t2_after_g1 = 1500.0 + 40.0 * (0.0 - 0.5)  # T2 lost as away (S=0, e=0.5) -> 1480
    r1_rev = 1500.0 + (2.0 / 3.0) * (t1_after_g3 - 1500.0)
    r2_rev = 1500.0 + (2.0 / 3.0) * (t2_after_g1 - 1500.0)
    expected_p = 1.0 / (1.0 + math.exp(-(r1_rev - r2_rev) / 400.0))
    assert abs(float(per_arm["B1_STAR"][0]) - expected_p) < 5e-7
    assert per_arm["B1_STAR"][0] == f"{expected_p:.6f}"
    # independent hand-check of the C3 target prediction (theta * z prior):
    # E = {T01 .06, T02 -.02, T03 .10, T04 -.08}; mean .015; population sd
    # sqrt((.045^2+.035^2+.085^2+.095^2)/4); z1 = .045/sd, z2 = -.035/sd.
    sd = math.sqrt((0.045 ** 2 + 0.035 ** 2 + 0.085 ** 2 + 0.095 ** 2) / 4.0)
    z1, z2 = 0.045 / sd, -0.035 / sd
    expected_c3 = 1.0 / (1.0 + math.exp(-((r1_rev + 50.0 * z1) - (r2_rev + 50.0 * z2)) / 400.0))
    assert per_arm["C3"][0] == f"{expected_c3:.6f}", (per_arm["C3"][0], expected_c3)
    assert per_arm["C3"][0] != per_arm["B1_STAR"][0]  # the prior term moves p
    assert per_arm["B0"] == [rec_pipe.B0_P_HOME_LEDGER, rec_pipe.B0_P_HOME_LEDGER]
    # warmup aggregates (counts only). The 3-game warmup stream covers ONE
    # season only, so no boundary prior can be counted inside it; the 2029
    # prior application is exercised by predict_target_week above (C3 != B1*).
    agg = rec_pipe.warmup_aggregates(arms, warm, _tiny_z(arms))
    assert agg["warmup_games"] == 3 and agg["lineages_initialized"] == 4
    assert agg["games_per_season"] == {"2028": 3}
    assert agg["record_counts_equal"] is True
    assert agg["c3_prior_applied_per_season"] == {}, agg["c3_prior_applied_per_season"]
    assert agg["c3_reversion_no_prior_per_season"] == {}
    # prior-COUNTING variant: extend the warmup stream with a first 2029 game
    # per lineage pair so every lineage's first 2029 prediction applies z.
    ns9 = int(dt.datetime(2029, 1, 5, tzinfo=dt.timezone.utc).timestamp()) * 10**9
    warm2 = warm + [
        dict(kickoff_ns=ns9, home="SYT01", away="SYT02", s_home=0.0, season=2029,
             week=1, game_id="SYNTH_ST_W2A", is_neutral=False),
        dict(kickoff_ns=ns9 + 3600 * 10**9, home="SYT03", away="SYT04", s_home=1.0,
             season=2029, week=1, game_id="SYNTH_ST_W2B", is_neutral=False),
    ]
    agg2 = rec_pipe.warmup_aggregates(arms, warm2, _tiny_z(arms))
    assert agg2["c3_prior_applied_per_season"] == {"2029": 4}, agg2["c3_prior_applied_per_season"]
    assert agg2["c3_reversion_no_prior_per_season"] == {}
    assert agg2["games_per_season"] == {"2028": 3, "2029": 2}
    results["state_carry_hand_elo"] = "PASS (1500->+20/-20; tie 0; g3 hand update; target p == hand formula; prior counts per boundary)"

    # (5) identical-kickoff exclusion inside the batch -------------------------
    # Target games share one kickoff. Three canaries on the frozen replay:
    #   a) flipping the placeholder label of T1 changes NOTHING about T1's own
    #      PREDICTION (e_home/ratings read pre-update),
    #   b) T1's prediction is unchanged whether T2 is present or absent
    #      (same-kickoff games never inform each other),
    #   c) in-batch predictions equal solo replays of each game.
    def _target_row(gid, s_ph):
        t = target[0]["kickoff_ns"]
        g = target[gid]
        return dict(kickoff_ns=t, home=g["home_lg"], away=g["away_lg"], s_home=s_ph,
                    season=2029, week=1, game_id=g["game_id"], is_neutral=False)

    t0 = target[0]["kickoff_ns"]
    assert target[1]["kickoff_ns"] == t0  # the two fixtures share a kickoff
    base_comb = warm + [_target_row(0, 0.0), _target_row(1, 0.0)]
    flip_comb = warm + [_target_row(0, 1.0), _target_row(1, 0.0)]   # label flip on T1
    solo0 = warm + [_target_row(0, 0.0)]
    solo1 = warm + [_target_row(1, 0.0)]
    zt = _tiny_z(arms)
    r_base = arms.replay_elo(rec_sched.rows_to_gameset(arms, base_comb), z_table=zt, theta=frozen.C3_THETA)
    r_flip = arms.replay_elo(rec_sched.rows_to_gameset(arms, flip_comb), z_table=zt, theta=frozen.C3_THETA)
    r_solo0 = arms.replay_elo(rec_sched.rows_to_gameset(arms, solo0), z_table=zt, theta=frozen.C3_THETA)
    r_solo1 = arms.replay_elo(rec_sched.rows_to_gameset(arms, solo1), z_table=zt, theta=frozen.C3_THETA)
    # T1's prediction (record -2 in the combined stream) identical everywhere
    a, f_, s0 = r_base[-2], r_flip[-2], r_solo0[-1]
    assert (a.e_home, a.r_home, a.r_away) == (f_.e_home, f_.r_home, f_.r_away) == (s0.e_home, s0.r_home, s0.r_away)
    # T2's prediction identical in-batch vs solo
    b_, s1_ = r_base[-1], r_solo1[-1]
    assert (b_.e_home, b_.r_home, b_.r_away) == (s1_.e_home, s1_.r_home, s1_.r_away)
    results["identical_kickoff_exclusion"] = "PASS (label-flip + absence + solo-vs-batch canaries)"

    # (6) abort-on-future-score (doctored snapshot rows) -----------------------
    import pandas as pd

    doctored = pd.DataFrame([
        dict(game_id="SYNTH_ST_OK", season=2029, week=1, game_type="REG",
             gameday="2029-01-01", gametime="12:00", home_team="SYT01",
             away_team="SYT02", home_score=float("nan"), away_score=float("nan"),
             location="Home"),
        dict(game_id="SYNTH_ST_BAD", season=2029, week=1, game_type="REG",
             gameday="2029-06-01", gametime="12:00", home_team="SYT03",
             away_team="SYT04", home_score=21.0, away_score=17.0,  # future + score
             location="Home"),
    ])
    doctored["kickoff_ns"] = [
        arms.kickoff_utc(gd, gt).value for gd, gt in zip(doctored["gameday"], doctored["gametime"])
    ]
    batch_ts = int(dt.datetime(2029, 1, 10, tzinfo=dt.timezone.utc).timestamp()) * 10**9
    class _S:  # minimal Schedule shim for the violation checker
        df = doctored
    bad = rec_sched.future_score_violations(_S(), batch_ts)
    assert bad == ["SYNTH_ST_BAD"], bad
    results["future_score_abort"] = "PASS (future row carrying a score detected -> abort list)"

    # (7) fresh-pull guard: refuses non-empty destination, never executed ------
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        Path(td, "x.txt").write_text("occupied")
        try:
            rec_sched.fetch_latest_schedule_snapshot(td)
            raise AssertionError("fresh-pull did NOT refuse a non-empty destination")
        except RuntimeError as e:
            assert "append-only" in str(e)
    assert "github.com/nflverse/nflverse-data/releases/download/schedules/games.csv" in (
        __import__("inspect").getsource(rec_sched.fetch_latest_schedule_snapshot)
    )
    results["fresh_pull_guard"] = "PASS (non-empty dest refused; public URL; not executed in any mode)"

    # (8) p-format guard --------------------------------------------------------
    assert rec_pipe.format_p_home(0.5118744) == "0.511874"
    for bad_v in (0.0, 1.0, -0.2, 1.0000001):
        try:
            rec_pipe.format_p_home(bad_v)
            raise AssertionError(f"format_p_home accepted {bad_v}")
        except RuntimeError:
            pass
    import re

    assert re.fullmatch(r"\d\.\d{6}", rec_pipe.format_p_home(0.9999994))
    results["p_format_guard"] = "PASS (6-dp strict (0,1); boundary rounding rejected)"

    # (9) combined-vs-warmup replay equivalence (prefix bit-identity) ----------
    comb = rec_sched.rows_to_gameset(
        arms, warm + [dict(kickoff_ns=target[0]["kickoff_ns"], home=target[0]["home_lg"],
                           away=target[0]["away_lg"], s_home=0.0, season=2029, week=1,
                           game_id="SYNTH_ST_T1", is_neutral=False)])
    zt = _tiny_z(arms)
    a = arms.replay_elo(rec_sched.rows_to_gameset(arms, warm), z_table=zt, theta=frozen.C3_THETA)
    b = arms.replay_elo(comb, z_table=zt, theta=frozen.C3_THETA)
    for ra_, rb_ in zip(a, b[: len(a)]):
        assert ra_ == rb_, "warmup prefix records diverged in the combined replay"
    results["combined_vs_warmup_equivalence"] = "PASS (C3 prefix records identical)"

    # (10) ledger tool identity + sandbox genesis distinctness ------------------
    assert frozen.sha256_file(frozen.LEDGER_TOOL_PATH) == frozen.LEDGER_TOOL_SHA256
    g = sandbox_genesis_digest()
    assert g != frozen.FREEZE_GENESIS_DIGEST_R1 and g != S_SYNTH_SANDBOX_GENESIS
    assert len(g) == 64
    results["frozen_tool_and_genesis_distinctness"] = "PASS"

    print("SELFTEST OK")
    print(json.dumps(results, indent=2, sort_keys=True))
    return results


# ===========================================================================
# Synthetic e2e fixtures (REAL games.csv format, SYNTH_ ids, 2027+ kickoffs)
# ===========================================================================

FIXTURE_COLUMNS = [
    "game_id", "season", "game_type", "week", "gameday", "weekday", "gametime",
    "away_team", "away_score", "home_team", "home_score", "location",
    "old_game_id", "stadium", "roof", "surface", "div_game",
    "spread_line", "total_line", "away_moneyline", "home_moneyline",
    "away_rest", "home_rest",
]
LINEAGES_N = 32
PRIOR_SEASONS = (2028, 2029)
TARGET_SEASON, TARGET_WEEK = 2030, 3


def _slot_local(season: int, slot: int) -> dt.datetime:
    base = {2028: dt.datetime(2028, 3, 5, 13, 0), 2029: dt.datetime(2029, 3, 4, 13, 0)}[season]
    return base + dt.timedelta(hours=12 * slot)


def _fixture_rows(arms):
    """Deterministic synthetic schedule rows in the REAL games.csv format:
    seasons 2028/2029 completed (6 rounds x 16 games, same-kickoff pairs,
    ties/neutral mixed), target week 2030 W3 (8 games in 4 same-kickoff
    batches). Kickoffs derived with the FROZEN arms.kickoff_utc (DST-aware)."""
    rows = []
    gid = 0
    for season in PRIOR_SEASONS:
        for r in range(1, 7):
            for i in range(16):
                j = (i + r) % LINEAGES_N
                assert j != i
                slot = gid // 2
                loc_dt = _slot_local(season, slot)
                v = (gid * 37 + 11 + (season - 2028) * 5) % 9
                s_home = 1.0 if v < 4 else (0.5 if v == 4 else 0.0)
                home_sc = 20 + (gid * 7) % 17
                if s_home == 1.0:
                    away_sc = home_sc - (3 + gid % 6)
                elif s_home == 0.5:
                    away_sc = home_sc
                else:
                    away_sc = home_sc + (3 + gid % 5)
                rows.append(dict(
                    game_id=f"SYNTH_{season}_R{r}_G{gid:03d}",
                    season=season, game_type="REG", week=r,
                    gameday=loc_dt.date().isoformat(), weekday=loc_dt.strftime("%A"),
                    gametime=loc_dt.strftime("%H:%M"),
                    away_team=f"SYT{j + 1:02d}", away_score=away_sc,
                    home_team=f"SYT{i + 1:02d}", home_score=home_sc,
                    location="Neutral" if gid % 13 == 0 else "Home",
                    old_game_id=str(2028000000 + gid), stadium="SYNTH_STADIUM",
                    roof="outdoors", surface="synthetic_grass", div_game=0,
                    spread_line=1.5, total_line=40.5,  # quarantine bait
                    away_moneyline=-110, home_moneyline=-110,  # quarantine bait
                    away_rest=7, home_rest=7,
                ))
                gid += 1
    assert gid == 192
    # target week: 8 games, 4 same-kickoff batches of 2, local ET slots
    t_slots = [(9, 12, 13, 0), (9, 12, 13, 0), (9, 12, 16, 15), (9, 12, 16, 15),
               (9, 13, 13, 0), (9, 13, 13, 0), (9, 13, 16, 15), (9, 13, 16, 15)]
    for n in range(8):
        i = n
        j = i + 8
        m, d, hh, mm = t_slots[n]
        loc_dt = dt.datetime(2030, m, d, hh, mm)
        rows.append(dict(
            game_id=f"SYNTH_2030_W{TARGET_WEEK}_G{n + 1:02d}",
            season=TARGET_SEASON, game_type="REG", week=TARGET_WEEK,
            gameday=loc_dt.date().isoformat(), weekday=loc_dt.strftime("%A"),
            gametime=loc_dt.strftime("%H:%M"),
            away_team=f"SYT{j + 1:02d}", away_score="",
            home_team=f"SYT{i + 1:02d}", home_score="",
            location="Home",
            old_game_id=str(2030000000 + n), stadium="SYNTH_STADIUM",
            roof="outdoors", surface="synthetic_grass", div_game=0,
            spread_line=2.5, total_line=41.5,
            away_moneyline=-105, home_moneyline=-115,
            away_rest=7, home_rest=7,
        ))
    return rows


def _write_fixture_csv(path, rows):
    import csv as _csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=FIXTURE_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _prior_e_table():
    entries = {}
    for s in PRIOR_SEASONS:
        entries[str(s)] = {
            f"SYT{i + 1:02d}": ((i * 17) % 23 - 11) * 0.03 for i in range(LINEAGES_N)
        }
    return {"schema": rec_priors.PRIOR_E_TABLE_SCHEMA, "entries": entries}


def _run_batch_scenario(arms, ledger, tag, schedule_csv, prior_json, batch_time_utc,
                        out_dir, expect_margin_refusal=False):
    """One full pipeline run on the synthetic fixtures (stages a-e)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = out_dir / f"predictions_{SANDBOX_CYCLE}_{SANDBOX_SEASON}.jsonl"
    sha = frozen.sha256_file(schedule_csv)
    sched = rec_sched.load_snapshot(arms, schedule_csv, sha)
    batch_ts = rec_sched.ns(batch_time_utc)
    # legality: future-with-score abort
    bad = rec_sched.future_score_violations(sched, batch_ts)
    if bad:
        raise rec_sched.FutureScoreAbort(f"future games carrying scores: {bad}")
    warm_rows, _fut_idx, counts = rec_sched.split_rows(sched, batch_ts)
    target_games, already = rec_pipe.select_target_games(
        sched, batch_ts, TARGET_SEASON, TARGET_WEEK
    )
    _assert_synth_only(target_games)
    first_kick = min(g["kickoff_ns"] for g in target_games)
    first_kick_iso = rec_sched.iso_of_ns(first_kick)
    # (d) margin BEFORE any write
    margin_h = rec_pipe.check_margin(batch_time_utc, first_kick_iso)
    # (b)+(c) priors + predict
    prior_e = rec_priors.load_prior_e_table(prior_json)
    z_table, per_target = rec_priors.synthesize_z_table(arms, prior_e)
    per_arm, _h = rec_pipe.predict_target_week(arms, warm_rows, target_games, z_table)
    if expect_margin_refusal:
        raise AssertionError("scenario expected a margin refusal but none raised")
    # (e) sandbox ledger append through the ported tool
    ledger.create_ledger(
        ledger_path,
        genesis_digest=sandbox_genesis_digest(),
        cycle_id=SANDBOX_CYCLE,
        season=SANDBOX_SEASON,
        arm_registry=list(frozen.FIELDED_ARMS),
        freeze_utc=SANDBOX_FREEZE_UTC,
        created_at_utc=SANDBOX_FREEZE_UTC,  # explicit: no wall-clock anywhere
    )
    inputs_digest = rec_pipe.inputs_digest_synth(
        sha, frozen.sha256_file(prior_json)
    )
    model_version = f"SYNTH-SANDBOX+{frozen.CODE_FREEZE_SHA}+{rec_pipe.recorder_config_digest(frozen)}"
    appended = rec_pipe.append_batch_to_ledger(
        ledger, ledger_path, sandbox_genesis_digest(), SANDBOX_CYCLE, SANDBOX_SEASON,
        SANDBOX_FREEZE_UTC, batch_time_utc, target_games, per_arm,
        inputs_digest, model_version, SANDBOX_RECORDED_BY,
    )
    broken = ledger.verify_chain(ledger_path, expected_genesis_digest=sandbox_genesis_digest())
    assert broken == [], f"chain broken: {broken}"
    return {
        "tag": tag,
        "fixture_sha": sha,
        "ledger_path": str(ledger_path),
        "rows": len(appended),
        "target_games": len(target_games),
        "already_completed_disclosed": len(already),
        "warmup_games": counts["warmup_completed_games"],
        "completed_per_season": counts["completed_per_season"],
        "first_kickoff_utc": first_kick_iso,
        "margin_hours": margin_h,
        "quarantined_columns": sched.quarantined_columns,
        "z_entries_per_target": {str(k): v for k, v in sorted(per_target.items())},
        "p_home_first_game": {a: per_arm[a][0] for a in frozen.FIELDED_ARMS},
    }


def mode_e2e_synth() -> dict:
    arms = frozen.load_frozen_arms()
    ledger = frozen.load_ledger_tool()
    rec_pipe.init_arm_digests(frozen)
    evidence = {"mode": "e2e-synth", "ran_utc": now_iso()}

    # deterministic fixture generation (regenerated; bytes deterministic)
    if E2E_DIR.exists():
        shutil.rmtree(E2E_DIR)  # lane-owned sandbox only
    fx = E2E_DIR / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    rows = _fixture_rows(arms)
    games_csv = fx / "games.csv"
    _write_fixture_csv(games_csv, rows)
    prior_json = fx / "prior_e_table.json"
    prior_json.write_text(json.dumps(_prior_e_table(), sort_keys=True) + "\n", encoding="utf-8")
    fixture_sha = frozen.sha256_file(games_csv)
    prior_sha = frozen.sha256_file(prior_json)
    evidence["fixtures"] = {
        "games_csv": str(games_csv), "sha256": fixture_sha, "rows": len(rows),
        "prior_e_table": str(prior_json), "prior_sha256": prior_sha,
    }

    # scenario C fixture: doctored snapshot (future game with a score)
    doc_rows = [dict(r) for r in rows]
    for r in doc_rows:
        if r["game_id"] == "SYNTH_2030_W3_G01":
            r["home_score"], r["away_score"] = 21, 17
    doctored_csv = fx / "games_doctored_future_score.csv"
    _write_fixture_csv(doctored_csv, doc_rows)

    BATCH_OK = "2030-09-05T12:00:00Z"        # ~173h before first kickoff
    BATCH_LATE = "2030-09-12T11:01:00Z"      # 5h59m before first kickoff

    # --- scenario 1: nominal week, run twice, byte-identical -----------------
    runs = []
    for tag in ("run1", "run2"):
        res = _run_batch_scenario(arms, ledger, tag, games_csv, prior_json,
                                  BATCH_OK, E2E_DIR / tag)
        runs.append(res)
    b1 = (E2E_DIR / "run1" / f"predictions_{SANDBOX_CYCLE}_{SANDBOX_SEASON}.jsonl").read_bytes()
    b2 = (E2E_DIR / "run2" / f"predictions_{SANDBOX_CYCLE}_{SANDBOX_SEASON}.jsonl").read_bytes()
    s1 = (E2E_DIR / "run1" / f"predictions_{SANDBOX_CYCLE}_{SANDBOX_SEASON}.jsonl.genesis.json").read_bytes()
    s2 = (E2E_DIR / "run2" / f"predictions_{SANDBOX_CYCLE}_{SANDBOX_SEASON}.jsonl.genesis.json").read_bytes()
    assert b1 == b2, "determinism violation: ledger bytes differ across runs"
    assert s1 == s2, "determinism violation: genesis sidecar differs across runs"
    evidence["scenario1_nominal"] = {
        **{k: v for k, v in runs[0].items() if k != "tag"},
        "determinism_double_run": "BYTE-IDENTICAL (ledger + genesis sidecar)",
        "ledger_sha256": _sha(b1),
    }

    # --- scenario 2: margin-violation refusal (nothing written) --------------
    late_dir = E2E_DIR / "scenario2_margin_refusal"
    late_dir.mkdir(parents=True, exist_ok=True)
    refused = False
    try:
        _run_batch_scenario(arms, ledger, "scenario2", games_csv, prior_json,
                            BATCH_LATE, late_dir)
    except rec_pipe.MarginRefusal as e:
        refused = True
        evidence["scenario2_margin_refusal"] = {
            "refused": True, "message": str(e),
            "batch_time_utc": BATCH_LATE,
            "first_kickoff_utc": "2030-09-12T17:00:00Z",
        }
    assert refused, "margin-violation scenario did NOT refuse"
    leftovers = sorted(p.name for p in late_dir.iterdir())
    assert leftovers == [], f"margin refusal left files behind: {leftovers}"
    evidence["scenario2_margin_refusal"]["nothing_written"] = True

    # --- scenario 3: future-score abort (nothing written) ---------------------
    abort_dir = E2E_DIR / "scenario3_future_score_abort"
    abort_dir.mkdir(parents=True, exist_ok=True)
    aborted = False
    try:
        _run_batch_scenario(arms, ledger, "scenario3", doctored_csv, prior_json,
                            BATCH_OK, abort_dir)
    except rec_sched.FutureScoreAbort as e:
        aborted = True
        evidence["scenario3_future_score_abort"] = {"aborted": True, "message": str(e)}
    assert aborted, "future-score scenario did NOT abort"
    leftovers = sorted(p.name for p in abort_dir.iterdir())
    assert leftovers == [], f"abort left files behind: {leftovers}"
    evidence["scenario3_future_score_abort"]["nothing_written"] = True

    # --- chain + scoring-gate rehearsal on the run1 sandbox ledger ------------
    lp = E2E_DIR / "run1" / f"predictions_{SANDBOX_CYCLE}_{SANDBOX_SEASON}.jsonl"
    rows_ = ledger.load_rows(lp)
    assert len(rows_) == 8 * 3
    pairs = {(r["game_id"], r["arm_id"]) for r in rows_}
    assert len(pairs) == 24 and all(g.startswith("SYNTH_") for g, _ in pairs)
    actual = {r["game_id"]: r["kickoff_utc"] for r in rows_}
    report = ledger.validate_for_scoring(lp, actual, freeze_utc=SANDBOX_FREEZE_UTC)
    assert report["counts"] == {"VALID_PROSPECTIVE": 24}, report["counts"]
    assert report["freeze_check"] == "APPLIED" and not report["not_run_games"]
    evidence["chain_and_scoring_rehearsal"] = {
        "rows": len(rows_), "unique_pairs": len(pairs),
        "verify_chain": "[] (intact vs sandbox genesis)",
        "scoring_counts": report["counts"], "freeze_check": report["freeze_check"],
    }

    # --- sandbox hygiene: freeze genesis absent from every sandbox byte -------
    blob = b"".join(p.read_bytes() for p in E2E_DIR.rglob("*") if p.is_file())
    assert frozen.FREEZE_GENESIS_DIGEST_R1.encode() not in blob
    assert frozen.FREEZE_GENESIS_DIGEST_R1.encode() not in frozen.canonical_json(
        SYNTH_GENESIS_DESCRIPTOR
    ).encode()
    evidence["freeze_genesis_absent_from_sandbox_bytes"] = True

    # --- REAL prediction-ledger path absence (loud incident, delete nothing) --
    real_paths = [
        frozen.WORKTREE / "research/control/NFL-WINPROB-NG-SCORED-V1/ledger/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl",
        frozen.WORKTREE / "research/control/NFL-WINPROB-NG-SCORED-V1/ledger/prediction_ledger.jsonl",
        RECORDER_SANDBOX.parent / "predictions",
        RECORDER_SANDBOX.parent / "predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl",
        RECORDER_SANDBOX.parent / "prediction_ledger.jsonl",
    ]
    existing = [str(p) for p in real_paths if p.exists()]
    stray = sorted(str(p) for p in (frozen.WORKTREE / "research/control/NFL-WINPROB-NG-SCORED-V1/ledger").glob("*.jsonl"))
    if existing or stray:
        raise RuntimeError(
            f"INCIDENT: a REAL prediction-ledger path exists: existing={existing} stray={stray}; "
            "deleting nothing; STOP"
        )
    evidence["real_ledger_paths_existing"] = []
    evidence["real_ledger_paths_checked"] = [str(p) for p in real_paths]

    print("E2E-SYNTH OK")
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    LANE_DIR.mkdir(parents=True, exist_ok=True)
    (LANE_DIR / "e2e_synth_evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return evidence


def _sha(b: bytes) -> str:
    import hashlib

    return hashlib.sha256(b).hexdigest()


# ===========================================================================
# --mode warmup-check — REAL stages (a)+(b), aggregate counts ONLY
# ===========================================================================

def mode_warmup_check(schedule_path=None, schedule_sha=None) -> dict:
    arms = frozen.load_frozen_arms()
    rec_pipe.init_arm_digests(frozen)
    schedule_path = Path(schedule_path or frozen.SCHEDULE_SNAPSHOT_PATH)
    schedule_sha = schedule_sha or frozen.SCHEDULE_SNAPSHOT_SHA256
    batch_time = now_iso()
    batch_ts = rec_sched.ns(batch_time)

    # (a) schedule load — sha-pinned versioned snapshot
    sched = rec_sched.load_snapshot(arms, schedule_path, schedule_sha)

    # legality: any future game carrying a score = corrupt/stale snapshot -> ABORT
    bad = rec_sched.future_score_violations(sched, batch_ts)
    if bad:
        raise rec_sched.FutureScoreAbort(
            f"ABORT: {len(bad)} future game(s) carry scores (corrupt/stale snapshot): {bad[:10]}"
        )

    # (b) state warmup: completed games ONLY, aggregates only
    warm_rows, _fut_idx, counts = rec_sched.split_rows(sched, batch_ts)
    pbp_pins = rec_priors.verify_pbp_pins(frozen, frozen.PBP_DIRS_REAL)
    z_table, per_target = rec_priors.build_z_table_real(arms, frozen.PBP_DIRS_REAL)
    agg = rec_pipe.warmup_aggregates(arms, warm_rows, z_table)

    evidence = {
        "mode": "warmup-check",
        "ran_utc": batch_time,
        "law": "REAL smoke check of stages (a)+(b) ONLY; aggregate counts emitted; "
               "ZERO per-game probability values for real games (predict stage never called)",
        "schedule_snapshot": {
            "path": str(schedule_path),
            "sha256": sched.sha256,
            "rows_total": sched.n_rows_total,
            "dropped_pre_2000": sched.n_dropped_pre_2000,
            "dropped_preseason": sched.n_dropped_preseason,
            "season_min": sched.season_min,
            "season_max": sched.season_max,
            "quarantined_columns": sched.quarantined_columns,
        },
        "batch_time_utc": batch_time,
        "future_with_score_violations": 0,
        "completed_games_total": counts["warmup_completed_games"],
        "completed_per_season": counts["completed_per_season"],
        "in_progress_excluded": counts["in_progress_excluded"],
        "future_unplayed": counts["future_unplayed"],
        "games_2026_absorbed": counts["completed_per_season"].get("2026", 0),
        "warmup_replay": {
            "b1_star": "K=40 HCA=0 gamma=2/3 mu=1500 (frozen arms.replay_elo, no prior)",
            "c3": "theta=50 (C3_T050) with z priors (frozen arms.replay_elo)",
            "warmup_games": agg["warmup_games"],
            "lineages_initialized": agg["lineages_initialized"],
            "lineage_codes": agg["lineage_codes"],
            "c3_prior_applied_per_season": agg["c3_prior_applied_per_season"],
            "c3_reversion_no_prior_per_season": agg["c3_reversion_no_prior_per_season"],
            "z_table_entries": agg["z_table_entries"],
            "z_entries_per_target_season": {str(k): v for k, v in sorted(per_target.items())},
            "record_counts_equal": agg["record_counts_equal"],
        },
        "state_carry_input_pins_verified": {str(k): v for k, v in sorted(pbp_pins.items())},
        "arm_param_equality": "recomputed arm-config digests == freeze pins (frozen_refs.verify_arm_config_digests)",
        "probabilities_emitted": 0,
    }

    # asserts (loud)
    assert evidence["future_with_score_violations"] == 0
    assert agg["record_counts_equal"] is True
    assert agg["lineages_initialized"] == 32, agg["lineages_initialized"]
    assert agg["z_table_entries"] == sum(per_target.values())
    assert set(per_target) == set(range(2001, 2027)), sorted(per_target)[:3]
    assert counts["completed_per_season"].get("2026", 0) > 0
    assert sorted(sched.quarantined_columns) == sorted([
        "away_moneyline", "away_spread_odds", "home_moneyline", "home_spread_odds",
        "over_odds", "spread_line", "total", "total_line", "under_odds",
    ])

    print("WARMUP-CHECK OK (aggregates only; no probabilities)")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    LANE_DIR.mkdir(parents=True, exist_ok=True)
    (LANE_DIR / "warmup_check_evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return evidence


# ===========================================================================
# CLI
# ===========================================================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="NFL-WINPROB-NG-SCORED-V1 recorder (PIPE lane)")
    ap.add_argument("--mode", required=True, choices=["selftest", "warmup-check", "e2e-synth"])
    ap.add_argument("--schedule", default=None, help="games.csv snapshot path (default: frozen pin)")
    ap.add_argument("--schedule-sha", default=None, help="expected snapshot sha256 (default: frozen pin)")
    args = ap.parse_args(argv)

    if args.mode == "selftest":
        mode_selftest()
        return 0
    if args.mode == "e2e-synth":
        mode_e2e_synth()
        return 0
    if args.mode == "warmup-check":
        mode_warmup_check(args.schedule, args.schedule_sha)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
