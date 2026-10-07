# test_realpath_predict.py — WNBA-WINPROB-2026-REMAINDER-V1 · Lane
# WNBA-REALPATH. Proves the REAL data path: pinned-snapshot completed rows ->
# B1-WNBA verbatim rating stream (completed-only state at the batch anchor) ->
# pre-tip probabilities for the remaining slate.
#
#   (a) synthetic-teams replay determinism (byte-stable state_digest across
#       runs and across input orderings) + verbatim equivalence to the pinned
#       engine bytes (read-only import of arms.py, sha 82263eab…, re-hashed
#       in-suite);
#   (b) stream-state law: state excludes any completed row with tip >= the
#       batch anchor (STRICT, mutation test — future-dated injected rows leave
#       state_digest unchanged; a pre-anchor row changes it);
#   (c) REAL path: REAL completed rows + REAL upcoming fixture ids from the
#       pinned snapshot (sha-verified against the 0ed97faf… pin). Real engine
#       p values are computed IN MEMORY ONLY — no assertion inspects them,
#       nothing is printed, logged, or persisted — and they are OVERWRITTEN
#       with synthetic placeholders before any further use. Disclosed here and
#       in REALPATH_PROOF.md.
#   (d) anchor-law unit tests: anchor_for_game exactness (dispatch pins
#       401918297 -> 2026-10-07T17:20:00Z, 401918298 -> 2026-10-07T19:20:00Z
#       partial-batch form), strict/exclusive boundary, fail-closed
#       validation, per-game anchors and ET-day gates vs FREEZE_PACKET §5.
#
# NO real-game probability is stored or committed anywhere by this file.

import csv
import hashlib
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import predict as P  # noqa: E402  (research/papertrade_wnba26/predict.py, flat import via conftest)

# ---------------------------------------------------------------- pinned engine (read-only)
FROZEN_ENGINE_DIR = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1"
    "/integration/lanes/T_SELECT")
ARMS_SHA256 = ("82263eab713258b09ef920500a56d1fbf"
               "36ef9b9b8ea20965c6b4fd99b04cdd3")
try:
    sys.path.insert(0, str(FROZEN_ENGINE_DIR))
    import arms  # noqa: E402  (pinned arms.py, READ-ONLY import)
    _HAS_ARMS = (
        hashlib.sha256((FROZEN_ENGINE_DIR / "arms.py").read_bytes()).hexdigest()
        == ARMS_SHA256)
except Exception:  # pragma: no cover - frozen tree unavailable
    arms = None  # type: ignore[assignment]
    _HAS_ARMS = False

# ---------------------------------------------------------------- pinned snapshot (read-only)
SNAPSHOT_PATH = Path(os.path.expanduser(
    "~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261007/"
    "wnba_schedule_2026.csv"))
SNAPSHOT_SHA256 = ("0ed97fafa4392a38f2467e5a588b0a8713ec"
                   "e835ec7cb4fb96a48f8761d05f26")
# Remaining-slate fixture ids (FREEZE_PACKET §5 census — ids only).
EXPECTED_UPCOMING_IDS = {str(g) for g in range(401918297, 401918312)}
POSTPONED_GAME_ID = "401857072"  # STATUS_POSTPONED, no result, excluded by law


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _syn_row(gid, tip, season, hid, aid, hs, as_, *, neutral=False,
             status="STATUS_FINAL", hab="HAB", aab="AAB"):
    """Synthetic row in the REAL pinned-snapshot schema (all values fabricated)."""
    return {
        "game_id": str(gid), "id": str(gid), "date": tip, "season": str(season),
        "home_id": str(hid), "away_id": str(aid),
        "home_abbreviation": hab, "away_abbreviation": aab,
        "home_score": str(hs), "away_score": str(as_),
        "status_type_name": status,
        "neutral_site": "true" if neutral else "false",
    }


def _synthetic_corpus():
    """Fabricated 2-season corpus: 8 teams, five-game tip batches (shared
    tips), a neutral-site row, a season boundary (gamma reversion)."""
    rows = []
    gid = 900001
    for season, start in ((2025, "2025-06-01T23:00:00Z"),
                          (2026, "2026-05-10T23:00:00Z")):
        start_dt = _t(start)
        for wk in range(6):
            tip = P._fmt_tip(start_dt + timedelta(days=7 * wk))
            for sl, (h, a) in enumerate(((1, 2), (3, 4), (5, 6), (7, 8))):
                hs = ((wk + sl) % 5 + 1) % 7 + 90
                as_ = (wk + sl) % 7 + 90
                if hs == as_:
                    hs += 1
                rows.append(_syn_row(gid, tip, season, h, a, hs, as_,
                                     hab=f"T{h}", aab=f"T{a}"))
                gid += 1
            # second game of the same tip batch: different pair, same tip
            rows.append(_syn_row(gid, tip, season, 2, 5,
                                 101 + wk % 3, 95 + wk % 2, hab="T2", aab="T5"))
            gid += 1
        rows.append(_syn_row(gid, P._fmt_tip(start_dt + timedelta(days=40)),
                             season, 6, 7, 103, 99, neutral=True,
                             hab="T6", aab="T7"))
        gid += 1
    upcoming = [
        _syn_row(990001, "2026-10-07T23:30:00Z", 2026, 1, 3, 0, 0,
                 status="STATUS_SCHEDULED", hab="T1", aab="T3"),
        _syn_row(990002, "2026-10-08T01:30:00Z", 2026, 4, 2, 0, 0,
                 status="STATUS_SCHEDULED", hab="T4", aab="T2"),
        _syn_row(990003, "2026-10-14T04:00:00Z", 2026, 3, 1, 0, 0,
                 status="STATUS_SCHEDULED", hab="T3", aab="T1"),
        _syn_row(990004, "2026-10-14T04:00:00Z", 2026, 8, 6, 0, 0,
                 status="STATUS_SCHEDULED", hab="T8", aab="T6"),
    ]
    return rows, upcoming


# ---------------------------------------------------------------- (a) determinism
def test_a_synthetic_replay_determinism_byte_stable():
    """Two runs over identical synthetic inputs produce byte-identical
    prediction entries, including state_digest."""
    rows, upcoming = _synthetic_corpus()
    p1 = P.wnba26_predict(rows, upcoming)
    rows2, upcoming2 = _synthetic_corpus()
    p2 = P.wnba26_predict(rows2, upcoming2)
    assert p1 == p2
    assert len({e["state_digest"] for e in p1}) == 1  # one shared completed state
    assert all(e["model_id"] == "B1_WNBA" for e in p1)
    assert all(e["constants"] == {"K": 32, "HCA": 50, "gamma": 0.65}
               for e in p1)
    # same-tip fixtures share one snapshot: 990003/990004 both tip 04:00Z
    digests = {e["match_id"]: e["state_digest"] for e in p1}
    assert digests["990003"] == digests["990004"]
    assert all(len(e["state_digest"]) == 64 for e in p1)


def test_a_input_order_invariance():
    """Shuffling the completed-row input order must not move the state
    (ordering law enforced inside the replay: (tip, game_id))."""
    rows, upcoming = _synthetic_corpus()
    base = P.wnba26_predict(rows, upcoming)
    shuffled = list(rows)
    random.Random(20261006).shuffle(shuffled)
    assert P.wnba26_predict(shuffled, upcoming) == base


@pytest.mark.skipif(not _HAS_ARMS, reason="pinned arms.py unavailable")
def test_a_verbatim_equivalence_to_pinned_engine():
    """The predict.py stream reproduces the pinned engine bytes bit-for-bit:
    identical p_home stream and identical final ratings on the same synthetic
    corpus (parent arm path k=32 / hca=50 / gamma=0.65)."""
    rows, _ = _synthetic_corpus()
    games = [P._normalize_game(r) for r in rows]
    games.sort(key=lambda g: (g["tip"], g["game_id"]))
    my_preds, my_state = P.replay_stream(games)
    arms_preds, arms_meta = arms.run_stream(games, k=32, hca=50.0, gamma=0.65)
    assert len(my_preds) == len(arms_preds)
    for mine, frozen in zip(my_preds, arms_preds):
        assert mine["game_id"] == frozen["game_id"]
        assert mine["tip"] == frozen["tip"]
        assert mine["p_home"] == frozen["p_home"]  # bit-for-bit float equality
    assert my_state.r == arms_meta["final_ratings"]


# ---------------------------------------------------------------- (b) state law
def test_b_state_excludes_future_completed_rows():
    """Mutation test: injecting result-present completed rows dated at/after
    the batch anchors must leave state_digest (and every synthetic prediction)
    unchanged. The two synthetic anchors are 2026-10-07T17:20:00Z (ET day
    10-07) and 2026-10-13T21:50:00Z (ET day 10-14); injections sit at/after
    the LATER anchor so the law is tested against every entry's state."""
    rows, upcoming = _synthetic_corpus()
    base = P.wnba26_predict(rows, upcoming)
    mutated = rows + [
        # tip > every anchor (== the 10-14 fixtures' own tip)
        _syn_row(995001, "2026-10-14T04:00:00Z", 2026, 1, 4, 120, 100,
                 hab="T1", aab="T4"),
        # tip == the later day anchor: STRICT boundary, excluded too
        _syn_row(995002, "2026-10-13T21:50:00Z", 2026, 2, 3, 110, 108,
                 hab="T2", aab="T3"),
    ]
    after = P.wnba26_predict(mutated, upcoming)
    assert after == base  # digests AND values unchanged (synthetic corpus)


def test_b_state_changes_with_pre_anchor_completed_row():
    """Complement: a genuinely new PRE-anchor completed row must change the
    digest (the digest actually tracks the completed-only state)."""
    rows, upcoming = _synthetic_corpus()
    base = P.wnba26_predict(rows, upcoming)
    mutated = rows + [_syn_row(995003, "2026-09-30T23:00:00Z", 2026, 5, 8,
                               101, 112, hab="T5", aab="T8")]
    after = P.wnba26_predict(mutated, upcoming)
    for b, a in zip(base, after):
        assert a["state_digest"] != b["state_digest"]


def test_b_non_final_row_never_enters_state():
    """A no-result row (STATUS_POSTPONED, 0-0) is excluded by the
    result-present law — never inferred as an outcome."""
    rows, upcoming = _synthetic_corpus()
    base = P.wnba26_predict(rows, upcoming)
    mutated = rows + [_syn_row(995004, "2026-09-29T23:00:00Z", 2026, 7, 1,
                               0, 0, status="STATUS_POSTPONED",
                               hab="T7", aab="T1")]
    assert P.wnba26_predict(mutated, upcoming) == base


# ---------------------------------------------------------------- (c) REAL path
def _load_snapshot():
    """Read-only load of the pinned snapshot; sha256-verified against the pin.
    Returns (completed_rows, upcoming_rows). Fails closed on pin mismatch."""
    if not SNAPSHOT_PATH.exists():
        pytest.skip("pinned snapshot not available (read-only data root)")
    digest = hashlib.sha256(SNAPSHOT_PATH.read_bytes()).hexdigest()
    assert digest == SNAPSHOT_SHA256, "pinned snapshot sha256 mismatch"
    with SNAPSHOT_PATH.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    completed = [r for r in rows if r["status_type_state"] == "post"]
    upcoming = [r for r in rows if r["status_type_state"] == "pre"]
    return completed, upcoming


def test_c_real_path_fixture_ids_and_digest_stability():
    """REAL completed rows + REAL upcoming fixture ids through the entry.

    GUARD (disclosed): the REAL engine p values computed here live only in
    memory; NO assertion inspects probability values, nothing is printed,
    logged, or persisted, and the values are OVERWRITTEN with synthetic
    placeholders before any further use. Only counts, fixture ids, tips and
    state digests (rating-table hashes, not probabilities) are asserted.
    """
    completed, upcoming = _load_snapshot()
    assert len(completed) == 345   # census: completed post rows = HISTORY
    assert len(upcoming) == 15     # census: remaining slate
    preds = P.wnba26_predict(completed, upcoming)
    # -- aggregate count only --
    assert len(preds) == 15
    assert {e["match_id"] for e in preds} == EXPECTED_UPCOMING_IDS
    assert all(e["model_id"] == "B1_WNBA" for e in preds)
    assert all(e["constants"] == {"K": 32, "HCA": 50, "gamma": 0.65}
               for e in preds)
    assert all(len(e["state_digest"]) == 64 for e in preds)
    # one shared completed-only state for the whole remaining slate
    assert len({e["state_digest"] for e in preds}) == 1
    # tips round-trip from the pinned rows (id -> tip plumbing)
    tip_by_id = {r["game_id"]: r["date"] for r in upcoming}
    for e in preds:
        assert e["tip_utc"] == P._fmt_tip(_t(tip_by_id[e["match_id"]]))
    # determinism on REAL data: second run byte-identical
    preds2 = P.wnba26_predict(completed, upcoming)
    assert preds == preds2
    # OVERWRITE with synthetic placeholders before any further use
    for e in preds:
        e["p_home"] = 0.5
        e["p_away"] = 0.5
    assert all(e["p_home"] == 0.5 and e["p_away"] == 0.5 for e in preds)
    # the entry list is the only container; no artifact has been written


def test_c_real_completed_census_composition():
    """Census composition (ids/status only — no probabilities): 345 post rows
    = 344 STATUS_FINAL (stream material) + 1 STATUS_POSTPONED (excluded)."""
    completed, upcoming = _load_snapshot()
    finals = [r for r in completed if r["status_type_name"] == "STATUS_FINAL"]
    postponed = [r for r in completed if r["status_type_name"] != "STATUS_FINAL"]
    assert len(completed) == 345 and len(finals) == 344 and len(postponed) == 1
    assert postponed[0]["game_id"] == POSTPONED_GAME_ID
    # every completed tip precedes the earliest remaining-slate anchor
    first_tips = P.day_first_tips([P._normalize_fixture(r) for r in upcoming])
    earliest_anchor = min(first_tips.values()) - P.ANCHOR_OFFSET
    assert all(P._tip_of(r) < earliest_anchor for r in completed)


# ---------------------------------------------------------------- (d) anchor law
def test_d_anchor_for_game_exact_and_strict():
    day_first = _t("2026-10-07T23:30:00Z")
    assert P.anchor_for_game(_t("2026-10-07T23:30:00Z"), day_first) == \
        _t("2026-10-07T17:20:00Z")
    # same ET day, later tip (SF2 01:30Z) -> same full-slate day anchor
    assert P.anchor_for_game(_t("2026-10-08T01:30:00Z"), day_first) == \
        _t("2026-10-07T17:20:00Z")
    # partial-batch form: the game's own tip is the day's first tip
    assert P.anchor_for_game(_t("2026-10-08T01:30:00Z"),
                             _t("2026-10-08T01:30:00Z")) == \
        _t("2026-10-07T19:20:00Z")
    # fail-closed: inconsistent day / inverted first-tip
    with pytest.raises(ValueError):
        P.anchor_for_game(_t("2026-10-09T23:30:00Z"), day_first)
    with pytest.raises(ValueError):
        P.anchor_for_game(_t("2026-10-07T20:00:00Z"),
                          _t("2026-10-07T23:30:00Z"))


def test_d_per_game_anchor_offset():
    assert P.per_game_anchor(_t("2026-10-07T23:30:00Z")) == \
        _t("2026-10-07T17:20:00Z")
    assert P.per_game_anchor(_t("2026-10-08T01:30:00Z")) == \
        _t("2026-10-07T19:20:00Z")
    assert P.ANCHOR_OFFSET == timedelta(hours=6, minutes=10)


@pytest.mark.skipif(not SNAPSHOT_PATH.exists(),
                    reason="pinned snapshot not available")
def test_d_real_slate_anchors_match_freeze_packet():
    """All 15 per-game anchors and the 11 ET-day gates reproduce the
    FREEZE_PACKET §5 tables exactly (timestamps only)."""
    _, upcoming = _load_snapshot()
    fixtures = [P._normalize_fixture(r) for r in upcoming]
    per_game = {
        "401918297": "2026-10-07T17:20:00Z", "401918298": "2026-10-07T19:20:00Z",
        "401918299": "2026-10-09T17:20:00Z", "401918300": "2026-10-09T19:20:00Z",
        "401918301": "2026-10-11T11:50:00Z", "401918302": "2026-10-10T21:50:00Z",
        "401918303": "2026-10-13T21:50:00Z", "401918304": "2026-10-13T21:50:00Z",
        "401918305": "2026-10-17T13:20:00Z", "401918306": "2026-10-19T17:50:00Z",
        "401918307": "2026-10-22T17:50:00Z", "401918308": "2026-10-24T13:20:00Z",
        "401918309": "2026-10-26T17:50:00Z", "401918310": "2026-10-29T17:50:00Z",
        "401918311": "2026-10-31T17:50:00Z",
    }
    for f in fixtures:
        assert P._fmt_tip(P.per_game_anchor(f["tip"])) == per_game[f["match_id"]]
    day_gates = {
        "2026-10-07": "2026-10-07T17:20:00Z", "2026-10-09": "2026-10-09T17:20:00Z",
        "2026-10-11": "2026-10-10T21:50:00Z", "2026-10-14": "2026-10-13T21:50:00Z",
        "2026-10-17": "2026-10-17T13:20:00Z", "2026-10-19": "2026-10-19T17:50:00Z",
        "2026-10-22": "2026-10-22T17:50:00Z", "2026-10-24": "2026-10-24T13:20:00Z",
        "2026-10-26": "2026-10-26T17:50:00Z", "2026-10-29": "2026-10-29T17:50:00Z",
        "2026-10-31": "2026-10-31T17:50:00Z",
    }
    first_tips = P.day_first_tips(fixtures)
    assert len(first_tips) == 11
    for day, gate in day_gates.items():
        day_key = datetime.strptime(day, "%Y-%m-%d").date()
        assert P._fmt_tip(first_tips[day_key] - P.ANCHOR_OFFSET) == gate


def test_d_et_day_grouping_synthetic():
    """2026-10-08T01:30Z is ET 2026-10-07 (the SF2 doubleheader law)."""
    fixtures = [
        {"tip": _t("2026-10-07T23:30:00Z"), "match_id": "a"},
        {"tip": _t("2026-10-08T01:30:00Z"), "match_id": "b"},
    ]
    first = P.day_first_tips(fixtures)
    assert len(first) == 1
    (day, tip), = first.items()
    assert day.isoformat() == "2026-10-07"
    assert tip == _t("2026-10-07T23:30:00Z")
