"""SYNTHETIC tests for nfl_ng_ledger (schema nfl_ng_ledger@1).

Every game id, team id, digest, probability and timestamp below is FABRICATED
(teams ``TEAM_X``/``TEAM_Y``/``TEAM_Z``, ids ``2026_W01_TEAMX_TEAMY``…,
digests ``aa…``/``bb…``).  No real NFL team, game, or prediction appears; no
outcome metric is computed.  PREP-only evidence for cycle
NFL-WINPROB-NG-PREP-V1 lane E_LEDGER.

Run:  .venv/bin/python -m pytest research/control/NFL-WINPROB-NG-PREP-V1/ledger/test_ledger_synthetic.py -v
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("nfl_ng_ledger", _HERE / "nfl_ng_ledger.py")
nfl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nfl)

# ---- SYNTHETIC constants (nothing real) ------------------------------------
GENESIS = "3f" * 32
OTHER_GENESIS = "9c" * 32
CYCLE = "SYN-CYCLE"
SEASON = 2026
ARMS = ["B0", "B1_STAR", "RESERVE"]
GAME1 = "2026_W01_TEAMX_TEAMY"
GAME2 = "2026_W01_TEAMZ_TEAMX"
GAME3 = "2026_W02_TEAMY_TEAMZ"
KICK1 = "2026-09-10T00:15:00Z"
REC1 = "2026-09-09T18:00:00Z"
RECORDER = "SYN-RECORDER-E"
P_HOME = "0.542317"


def new_ledger(tmp_path: Path, name: str = "predictions_SYN-CYCLE_2026.jsonl", **kw) -> Path:
    path = tmp_path / name
    nfl.create_ledger(
        path,
        kw.pop("genesis", GENESIS),
        kw.pop("cycle_id", CYCLE),
        kw.pop("season", SEASON),
        **kw,
    )
    return path


def make_row(**over):
    row = {
        "schema_version": "nfl_ng_ledger@1",
        "cycle_id": CYCLE,
        "game_id": GAME1,
        "season": SEASON,
        "game_type": "REG",
        "home_team": "TEAM_X",
        "away_team": "TEAM_Y",
        "kickoff_utc": KICK1,
        "recorded_at_utc": REC1,
        "arm_id": "B0",
        "arm_config_digest": "aa" * 32,
        "model_version": "SYNTHCOMMIT00000000000000000000+SYNTHPIPE0000",
        "inputs_digest": "bb" * 32,
        "p_home": P_HOME,
        "recorded_by": RECORDER,
        "prev_row_hash": None,
    }
    row.update(over)
    return row


def tail_parent(path: Path) -> str:
    rows = nfl.load_rows(path)
    if not rows:
        return "GENESIS:" + nfl.load_genesis(path)["genesis_digest"]
    return rows[-1]["row_hash"]


def add_row(path: Path, **over):
    row = make_row()
    row["prev_row_hash"] = over.pop("prev_row_hash", tail_parent(path))
    row.update(over)
    return nfl.append(path, row)


def rewrite_line(path: Path, idx: int, mutate) -> None:
    """Simulate a competent attacker: edit one line and recompute ONLY that
    line's stored row_hash so its own rehash matches (chain must still flag)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[idx])
    mutate(row)
    row["row_hash"] = nfl.compute_row_hash(row, nfl.FIELD_ORDER)
    lines[idx] = nfl.canonical_json(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Happy path, canonical hashing, determinism
# ---------------------------------------------------------------------------


def test_happy_path_append_and_verify(tmp_path):
    path = new_ledger(tmp_path)
    r1 = add_row(path, arm_id="B0")
    r2 = add_row(path, arm_id="B1_STAR", recorded_at_utc="2026-09-09T18:00:01Z")
    r3 = add_row(path, game_id=GAME2, home_team="TEAM_Z", away_team="TEAM_X",
                 kickoff_utc="2026-09-13T17:00:00Z")
    assert r2["prev_row_hash"] == r1["row_hash"]
    assert r3["prev_row_hash"] == r2["row_hash"]
    assert nfl.verify_chain(path) == []
    # §1: line 1 anchors to GENESIS:<digest>
    first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert first["prev_row_hash"] == "GENESIS:" + GENESIS


def test_row_hash_is_sha256_of_canonical_without_row_hash(tmp_path):
    path = new_ledger(tmp_path)
    stored = add_row(path)
    line_row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    content = {f: line_row[f] for f in nfl.FIELD_ORDER if f != "row_hash"}
    expected = nfl.sha256_hex(nfl.canonical_json(content))
    assert line_row["row_hash"] == expected == stored["row_hash"]
    # canonical order is the §2 binding field order in the written line
    assert list(line_row.keys()) == nfl.FIELD_ORDER


def test_hash_independent_of_caller_key_order_and_byte_deterministic(tmp_path):
    a = new_ledger(tmp_path, name="predictions_SYN-CYCLE_2026.jsonl")
    b = tmp_path / "b" / "predictions_SYN-CYCLE_2026.jsonl"
    b.parent.mkdir()
    nfl.create_ledger(b, GENESIS, CYCLE, SEASON)
    row = make_row(prev_row_hash="GENESIS:" + GENESIS)
    shuffled = {k: row[k] for k in reversed(list(row.keys()))}
    ra = nfl.append(a, row)
    rb = nfl.append(b, shuffled)
    assert ra["row_hash"] == rb["row_hash"]
    # predictions carry no wall-clock: identical batches ⇒ byte-identical files
    assert a.read_bytes() == b.read_bytes()


# ---------------------------------------------------------------------------
# Append-time rejections (R1/R2/R5/R6/R7/R8 structure)
# ---------------------------------------------------------------------------


def test_reject_recorded_at_equal_to_kickoff(tmp_path):
    path = new_ledger(tmp_path)
    with pytest.raises(nfl.LedgerValidationError, match="R2"):
        add_row(path, prev_row_hash="GENESIS:" + GENESIS, recorded_at_utc=KICK1)


def test_reject_recorded_at_after_kickoff(tmp_path):
    path = new_ledger(tmp_path)
    with pytest.raises(nfl.LedgerValidationError, match="R2"):
        add_row(path, prev_row_hash="GENESIS:" + GENESIS,
                recorded_at_utc="2026-09-10T01:00:00Z")


@pytest.mark.parametrize("bad", [
    "2026-09-09T18:00:00",          # naive, no Z
    "2026-09-09T18:00:00+00:00",    # offset instead of Z
    "2026-13-09T18:00:00Z",         # month 13
    "2026-09-09 18:00:00Z",         # missing T
    "2026-09-09T18:00:00.500Z",     # fractional seconds not in schema form
    "",
])
def test_reject_malformed_timestamps(tmp_path, bad):
    path = new_ledger(tmp_path)
    with pytest.raises(nfl.LedgerValidationError):
        add_row(path, prev_row_hash="GENESIS:" + GENESIS, recorded_at_utc=bad)


def test_reject_outcome_key_injection(tmp_path):
    path = new_ledger(tmp_path)
    for extra in ({"home_score": "27"}, {"Winner": "TEAM_X"}, {"final_margin": "4"},
                  {"notes": "innocuous extra field"}):
        row = make_row(prev_row_hash="GENESIS:" + GENESIS)
        row.update(extra)
        with pytest.raises(nfl.LedgerValidationError) as err:
            nfl.append(path, row)
        assert ("outcome" in str(err.value).lower()) or ("closed" in str(err.value).lower())
    # defense-in-depth: blocklist matcher itself, case-insensitive substring
    assert nfl._has_outcome_key({"HOME_SCORE": 1}) == "HOME_SCORE"
    assert nfl._has_outcome_key({"kickoff_utc": KICK1, "p_home": P_HOME}) is None


def test_reject_duplicate_game_arm(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    with pytest.raises(nfl.LedgerValidationError, match="R5"):
        add_row(path, recorded_at_utc="2026-09-09T18:00:05Z")  # same (GAME1, B0)


def test_reject_wrong_chain_parent(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    with pytest.raises(nfl.LedgerValidationError, match="chain parent"):
        add_row(path, prev_row_hash="0" * 64, arm_id="B1_STAR")


def test_reject_wrong_genesis_anchor_on_first_row(tmp_path):
    path = new_ledger(tmp_path)
    with pytest.raises(nfl.LedgerValidationError, match="chain parent"):
        add_row(path, prev_row_hash="GENESIS:" + OTHER_GENESIS)


@pytest.mark.parametrize("bad", [
    "0.54231",       # 5 dp
    "0.5423170",     # 7 dp
    0.5,             # float, not string
    "1.000000",      # strict upper bound violated
    "0.000000",      # strict lower bound violated
    "-0.542317",     # negative
    ".542317",       # no leading digit
    "0.5",           # 1 dp
    "2.000000",      # > 1
])
def test_reject_p_home_format_and_domain(tmp_path, bad):
    path = new_ledger(tmp_path)
    with pytest.raises(nfl.LedgerValidationError, match="p_home"):
        add_row(path, prev_row_hash="GENESIS:" + GENESIS, p_home=bad)


def test_accept_p_home_strict_open_boundaries(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS, p_home="0.000001")
    add_row(path, prev_row_hash=tail_parent(path), arm_id="B1_STAR", p_home="0.999999",
            recorded_at_utc="2026-09-09T18:00:01Z")
    assert nfl.verify_chain(path) == []


def test_reject_arm_outside_frozen_registry(tmp_path):
    path = new_ledger(tmp_path, arm_registry=ARMS)
    with pytest.raises(nfl.LedgerValidationError, match="R4"):
        add_row(path, prev_row_hash="GENESIS:" + GENESIS, arm_id="C3")
    # with no registry bound, the enumeration is the freeze packet's concern
    unreg_dir = tmp_path / "unreg"
    unreg_dir.mkdir()
    path2 = new_ledger(unreg_dir)
    add_row(path2, prev_row_hash="GENESIS:" + GENESIS, arm_id="C3")


def test_reject_bad_enums_and_season(tmp_path):
    path = new_ledger(tmp_path)
    for over in ({"game_type": "PRE"}, {"game_type": "WILD"}, {"season": 2025},
                 {"season": "2026"}, {"schema_version": "nfl_ng_ledger@2"}):
        with pytest.raises(nfl.LedgerValidationError):
            add_row(path, prev_row_hash="GENESIS:" + GENESIS, **over)


def test_supplied_row_hash_must_match_recomputation(tmp_path):
    path = new_ledger(tmp_path)
    row = make_row(prev_row_hash="GENESIS:" + GENESIS, row_hash="ab" * 32)
    with pytest.raises(nfl.LedgerValidationError, match="row_hash"):
        nfl.append(path, row)


# ---------------------------------------------------------------------------
# Verification: tamper detection, genesis binding (R1/R9)
# ---------------------------------------------------------------------------


def test_verify_flags_tampered_line_and_scoring_fails_closed(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    add_row(path, arm_id="B1_STAR", recorded_at_utc="2026-09-09T18:00:01Z")
    add_row(path, game_id=GAME2, home_team="TEAM_Z", away_team="TEAM_X",
            kickoff_utc="2026-09-13T17:00:00Z")
    # tamper p_home in line 1, keep the stored row_hash
    lines = path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["p_home"] = "0.999999"
    lines[1] = nfl.canonical_json(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert nfl.verify_chain(path) == [1]
    with pytest.raises(nfl.LedgerIntegrityError, match="broken"):
        nfl.validate_for_scoring(path, {GAME1: KICK1, GAME2: "2026-09-13T17:00:00Z"})


def test_verify_flags_competent_tamper_with_recomputed_hash(tmp_path):
    """A tamperer who recomputes the edited line's own hash is still caught by
    the CHILD's linkage (R1 breaks from the edited point forward)."""
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    add_row(path, arm_id="B1_STAR", recorded_at_utc="2026-09-09T18:00:01Z")
    add_row(path, game_id=GAME2, home_team="TEAM_Z", away_team="TEAM_X",
            kickoff_utc="2026-09-13T17:00:00Z", recorded_at_utc="2026-09-09T18:00:02Z")
    rewrite_line(path, 1, lambda r: r.update(p_home="0.111111"))
    assert nfl.verify_chain(path) == [2]  # line 2's prev no longer matches the rewritten parent
    # fail-closed: the ledger refuses further appends while doubtful
    with pytest.raises(nfl.LedgerIntegrityError, match="linkage"):
        add_row(path, game_id=GAME3, home_team="TEAM_Y", away_team="TEAM_Z",
                kickoff_utc="2026-09-14T17:00:00Z")


def test_verify_flags_genesis_anchor_tamper(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    add_row(path, arm_id="B1_STAR", recorded_at_utc="2026-09-09T18:00:01Z")
    # competent attacker rewrites the anchor and recomputes line 0's hash
    rewrite_line(path, 0, lambda r: r.update(prev_row_hash="GENESIS:" + OTHER_GENESIS))
    broken = nfl.verify_chain(path)
    assert 0 in broken and 1 in broken  # anchor wrong AND child linkage broken
    with pytest.raises(nfl.LedgerIntegrityError, match="genesis"):
        nfl.verify_chain(path, expected_genesis_digest=OTHER_GENESIS)


def test_verify_flags_blank_and_foreign_lines(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    original = path.read_text(encoding="utf-8").splitlines()
    tail = tail_parent(path)
    # blank line injected between rows
    path.write_text("\n".join(original[:1] + [""] + original[1:]) + "\n", encoding="utf-8")
    broken = nfl.verify_chain(path)
    assert 1 in broken  # blank line itself breaks; the re-appended row duplicates (game, arm)
    # foreign row carrying an outcome key (shape break; any stored hash)
    foreign = make_row(game_id=GAME3, prev_row_hash=tail)
    foreign.pop("p_home")
    foreign["home_score"] = "27"
    foreign["row_hash"] = "cd" * 32
    path.write_text("\n".join(original[:1] + [nfl.canonical_json(foreign)]) + "\n", encoding="utf-8")
    assert nfl.verify_chain(path) == [1]


# ---------------------------------------------------------------------------
# Genesis discipline (create/refuse/tamper)
# ---------------------------------------------------------------------------


def test_create_refuses_existing_and_filename_law(tmp_path):
    path = new_ledger(tmp_path)
    with pytest.raises(nfl.LedgerValidationError, match="already exists"):
        nfl.create_ledger(path, GENESIS, CYCLE, SEASON)
    with pytest.raises(nfl.LedgerValidationError, match="filename"):
        new_ledger(tmp_path, name="foo.jsonl")
    with pytest.raises(nfl.LedgerValidationError, match="genesis_digest"):
        new_ledger(tmp_path, name="predictions_SYN-CYCLE_2027.jsonl", cycle_id=CYCLE,
                   season=2027, genesis="ZZ" * 32)


def test_append_fails_closed_without_genesis_binding(tmp_path):
    bare = tmp_path / "predictions_SYN-CYCLE_2026.jsonl"
    bare.touch()
    with pytest.raises(nfl.LedgerIntegrityError, match="genesis"):
        add_row(bare)
    # tampered genesis record (digest swapped) is refused
    tdir = tmp_path / "tampered"
    tdir.mkdir()
    path = new_ledger(tdir)
    sidecar = Path(str(path) + ".genesis.json")
    record = json.loads(sidecar.read_text(encoding="utf-8"))
    record["genesis_digest"] = OTHER_GENESIS
    sidecar.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(nfl.LedgerIntegrityError, match="self_hash"):
        nfl.load_genesis(path)


# ---------------------------------------------------------------------------
# Postponement / cancellation (PROTOCOL §4 semantics)
# ---------------------------------------------------------------------------


def test_postpone_later_rows_stay_valid_and_notice_emitted(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    add_row(path, arm_id="B1_STAR", recorded_at_utc="2026-09-09T18:00:01Z")
    notice = nfl.postpone(path, GAME1, "2026-09-11T00:15:00Z",
                          "SYNTHETIC weather postponement",
                          noticed_at_utc="2026-09-09T20:00:00Z", recorded_by=RECORDER)
    assert notice["row_type"] == "POSTPONEMENT_NOTICE"
    assert notice["affected_row_indices"] == []  # move is later than every recorded_at
    assert nfl.verify_chain(path) == []
    report = nfl.validate_for_scoring(path, {GAME1: "2026-09-11T00:15:00Z"},
                                      freeze_utc="2026-09-01T00:00:00Z")
    assert [v["verdict"] for v in report["rows"]] == ["VALID_PROSPECTIVE", "VALID_PROSPECTIVE"]
    # disclosure lives in the tamper-evident file itself
    types = [r.get("row_type") for r in nfl.load_rows(path)]
    assert "POSTPONEMENT_NOTICE" in types


def test_postpone_earlier_past_record_marks_invalid(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)  # recorded 18:00Z
    notice = nfl.postpone(path, GAME1, "2026-09-09T12:00:00Z",
                          "SYNTHETIC schedule move earlier",
                          noticed_at_utc="2026-09-09T20:00:00Z", recorded_by=RECORDER)
    assert notice["affected_row_indices"] == [0]  # row 0 recorded after the new kickoff
    assert nfl.verify_chain(path) == []
    report = nfl.validate_for_scoring(path, {GAME1: "2026-09-09T12:00:00Z"},
                                      freeze_utc="2026-09-01T00:00:00Z")
    assert report["rows"][0]["verdict"] == "INVALID_PROSPECTIVE"
    assert report["counts"] == {"INVALID_PROSPECTIVE": 1}
    assert report["aggregate_eligible_rows"] == 0


def test_cancel_not_scored_cancelled(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    notice = nfl.cancel(path, GAME1, "SYNTHETIC cancellation", noticed_at_utc="2026-09-09T21:00:00Z",
                        recorded_by=RECORDER)
    assert notice["row_type"] == "CANCELLATION_NOTICE"
    assert notice["affected_row_indices"] == [0]
    assert nfl.verify_chain(path) == []
    # notice-derived classification (caller passes no cancelled_games)
    report = nfl.validate_for_scoring(path, {GAME1: KICK1})
    assert report["rows"][0]["verdict"] == "NOT_SCORED_CANCELLED"
    assert GAME1 in report["cancelled_games"]
    # caller-supplied status classifies identically
    report2 = nfl.validate_for_scoring(path, {GAME1: KICK1}, cancelled_games={GAME1})
    assert report2["rows"][0]["verdict"] == "NOT_SCORED_CANCELLED"


def test_postpone_requires_metadata_when_game_has_no_rows(tmp_path):
    path = new_ledger(tmp_path)
    with pytest.raises(nfl.LedgerValidationError, match="game_meta"):
        nfl.postpone(path, GAME3, "2026-09-20T17:00:00Z", "SYNTHETIC", recorded_by=RECORDER)
    notice = nfl.postpone(
        path, GAME3, "2026-09-20T17:00:00Z", "SYNTHETIC",
        prior_kickoff_utc="2026-09-20T20:00:00Z",
        game_meta={"season": SEASON, "game_type": "REG",
                   "home_team": "TEAM_Y", "away_team": "TEAM_Z"},
        noticed_at_utc="2026-09-14T18:00:00Z", recorded_by=RECORDER,
    )
    assert notice["affected_row_indices"] == []
    assert nfl.verify_chain(path) == []


# ---------------------------------------------------------------------------
# Scoring-time classification (R2 actual-kickoff gate, R10 classes)
# ---------------------------------------------------------------------------


def test_scoring_not_run_game_level_and_freeze_writeoff(tmp_path):
    path = new_ledger(tmp_path, freeze_utc="2026-09-20T00:00:00Z")
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)  # GAME1, actual 09-10 < freeze
    add_row(path, game_id=GAME2, home_team="TEAM_Z", away_team="TEAM_X",
            kickoff_utc="2026-09-25T17:00:00Z", recorded_at_utc="2026-09-24T18:00:00Z")
    report = nfl.validate_for_scoring(
        path,
        {GAME1: KICK1, GAME2: "2026-09-25T17:00:00Z", GAME3: "2026-09-27T17:00:00Z"},
    )
    by_game = {v["game_id"]: v["verdict"] for v in report["rows"]}
    assert by_game[GAME1] == "NOT_RUN"  # played before the freeze: permanent write-off
    assert by_game[GAME2] == "VALID_PROSPECTIVE"
    assert report["not_run_games"] == [GAME3]  # played, inside window, but no row: never inferred PASS
    assert report["freeze_check"] == "APPLIED"


def test_scoring_no_actual_data_and_retro_boundary(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)  # recorded 18:00Z
    # actual == recorded ⇒ not strictly after ⇒ INVALID (boundary)
    report = nfl.validate_for_scoring(path, {GAME1: REC1})
    assert report["rows"][0]["verdict"] == "INVALID_PROSPECTIVE"
    # game absent from the actual-kickoff input ⇒ unresolved, excluded
    report2 = nfl.validate_for_scoring(path, {})
    assert report2["rows"][0]["verdict"] == "NOT_SCORED_NO_ACTUAL_DATA"
    assert report2["aggregate_eligible_rows"] == 0
    assert report2["freeze_check"] == "SKIPPED"


def test_scoring_rejects_malformed_actual_kickoff(tmp_path):
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    with pytest.raises(nfl.LedgerValidationError, match="actual_kickoffs"):
        nfl.validate_for_scoring(path, {GAME1: "2026-09-10 00:15:00"})


def test_full_week_batch_scenario_end_to_end(tmp_path):
    """SYNTHETIC weekly batch: 3 games × 2 arms appended before first kickoff,
    one postponement later (rows stay valid), one cancellation, verify + score."""
    path = new_ledger(tmp_path)
    add_row(path, prev_row_hash="GENESIS:" + GENESIS)
    add_row(path, arm_id="B1_STAR", recorded_at_utc="2026-09-09T18:00:01Z")
    add_row(path, game_id=GAME2, home_team="TEAM_Z", away_team="TEAM_X",
            kickoff_utc="2026-09-13T17:00:00Z", arm_id="RESERVE")
    add_row(path, game_id=GAME2, home_team="TEAM_Z", away_team="TEAM_X",
            kickoff_utc="2026-09-13T17:00:00Z", arm_id="B0",
            recorded_at_utc="2026-09-09T18:00:03Z")
    add_row(path, game_id=GAME3, home_team="TEAM_Y", away_team="TEAM_Z",
            kickoff_utc="2026-09-14T17:00:00Z", arm_id="B0",
            recorded_at_utc="2026-09-09T18:00:04Z")
    nfl.postpone(path, GAME2, "2026-09-13T19:00:00Z", "SYNTHETIC flex",
                 noticed_at_utc="2026-09-09T20:00:00Z", recorded_by=RECORDER)
    nfl.cancel(path, GAME3, "SYNTHETIC cancellation",
               noticed_at_utc="2026-09-09T20:30:00Z", recorded_by=RECORDER)
    assert nfl.verify_chain(path) == []
    report = nfl.validate_for_scoring(
        path,
        {GAME1: KICK1, GAME2: "2026-09-13T19:00:00Z", GAME3: "2026-09-14T17:00:00Z"},
        freeze_utc="2026-09-01T00:00:00Z",
    )
    verdicts = {(v["game_id"], v["arm_id"]): v["verdict"] for v in report["rows"]}
    assert verdicts == {
        (GAME1, "B0"): "VALID_PROSPECTIVE",
        (GAME1, "B1_STAR"): "VALID_PROSPECTIVE",
        (GAME2, "RESERVE"): "VALID_PROSPECTIVE",
        (GAME2, "B0"): "VALID_PROSPECTIVE",
        (GAME3, "B0"): "NOT_SCORED_CANCELLED",
    }
    assert report["counts"] == {
        "VALID_PROSPECTIVE": 4,
        "NOT_SCORED_CANCELLED": 1,
    }
    assert report["aggregate_eligible_rows"] == 4
