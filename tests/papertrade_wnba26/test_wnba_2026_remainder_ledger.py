# test_wnba_2026_remainder_ledger.py — Lane W26 synthetic suite (port of the
# 2027 PREP lane's test_wnba_prospective_ledger.py, 46 test functions +
# adversarial probes; source cycle WNBA-WINPROB-PROSPECTIVE-PREP-V1
# lanes/L_LEDGER, 57 pytest items green). SYNTHETIC ONLY: every fixture is
# fabricated; no real game, no real prediction, no metric on outcomes.
#
# Port adaptations (wnba_2026_remainder_ledger@1):
#   * window law: season == 2026 exact, game_type == "POST" only;
#   * batch law: STRICTLY earlier than T0-6h10m (anchor is an exclusive
#     deadline — the frozen 2027 law was inclusive at exactly 6h);
#   * DST fixtures moved to 2026 (spring-forward 2026-03-08, fall-back
#     2026-11-01);
#   * new pin test (47): frozen engine + data artifact sha256 pins re-measured.
#
# Run (worktree cwd):
#   /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
#       tests/papertrade_wnba26/test_wnba_2026_remainder_ledger.py -q

import json
from pathlib import Path

import pytest

import wnba_2026_remainder_ledger as L

CYCLE = "SYN-W26-CYCLE"
GENESIS = "a" * 64


def new_ledger(tmp_path: Path, season: int = 2026,
               name: str = None, **kw) -> Path:
    name = name or f"predictions_{CYCLE}_{season}.jsonl"
    L.create_ledger(tmp_path / name, GENESIS, CYCLE, season, **kw)
    return tmp_path / name


def make_row(**over) -> dict:
    """Synthetic row: 2026-05-14 first tip 23:00Z (ET 2026-05-14 19:00 EDT);
    recorded 2026-05-14T10:00:00Z = 13h before tip (batch-law clean)."""
    row = {
        "schema_version": L.SCHEMA_VERSION,
        "cycle_id": CYCLE,
        "game_id": "SYN-G1",
        "season": 2026,
        "game_type": "POST",
        "home_team": "SYN-A",
        "away_team": "SYN-B",
        "tip_utc": "2026-05-14T23:00:00Z",
        "local_date": "2026-05-14",
        "recorded_at_utc": "2026-05-14T10:00:00Z",
        "arm_id": "B1-WNBA",
        "arm_config_digest": "b" * 64,
        "model_version": "syn-model-1",
        "inputs_digest": "c" * 64,
        "p_home": "0.541234",
        "recorded_by": "SYN-RECORDER",
        "prev_row_hash": None,
        "row_hash": None,
    }
    row.update(over)
    if "row_hash" not in over:
        row.pop("row_hash", None)
    return row


def tail_parent(path: Path) -> str:
    rows = L.load_rows(path)
    return L.GENESIS_PREFIX + GENESIS if not rows else rows[-1]["row_hash"]


def add_row(path: Path, **over) -> dict:
    row = make_row(**{**over,
                      "prev_row_hash": over.get("prev_row_hash",
                                                tail_parent(path))})
    (written,) = L.append_batch(path, [row])
    return written


def rewrite_line(path: Path, idx: int, mutate) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[idx])
    mutate(row)
    lines[idx] = json.dumps(row, separators=(",", ":"), ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def batch_rows(day, tips_utc, **common) -> list:
    rows = []
    for i, tip in enumerate(tips_utc):
        rows.append(make_row(game_id=f"SYN-{day}-{i}", tip_utc=tip,
                             local_date=day, **common))
    return rows


# ---------------------------------------------------------------- 1-6 schema/genesis
def test_01_happy_path_batch_append_and_verify(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14",
                      ["2026-05-14T23:00:00Z", "2026-05-15T00:30:00Z"])
    # prev_row_hash left null -> tool auto-chains the batch sequentially
    written = L.append_batch(p, rows)
    assert len(written) == 2
    assert written[1]["prev_row_hash"] == written[0]["row_hash"]
    assert L.verify_chain(p) == []


def test_02_row_hash_is_sha256_of_canonical_without_row_hash(tmp_path):
    p = new_ledger(tmp_path)
    row = add_row(p)
    content = {f: row[f] for f in L.FIELD_ORDER if f != "row_hash"}
    assert row["row_hash"] == L.sha256_hex(L.canonical_json(content))


def test_03_hash_independent_of_caller_key_order(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    pa = new_ledger(tmp_path / "a")
    pb = new_ledger(tmp_path / "b")
    row = make_row(prev_row_hash=tail_parent(pa))
    shuffled = {k: row[k] for k in reversed(list(row))}
    (a,) = L.append_batch(pa, [row])
    (b,) = L.append_batch(pb, [shuffled])
    assert a["row_hash"] == b["row_hash"]


def test_04_field_set_is_closed_18_fields(tmp_path):
    p = new_ledger(tmp_path)
    row = make_row(prev_row_hash=tail_parent(p))
    row["bogus_extra"] = 1
    with pytest.raises(L.LedgerValidationError, match="closed 18-field"):
        L.append_batch(p, [row])


def test_05_genesis_sidecar_self_hash_and_refusal_to_recreate(tmp_path):
    p = new_ledger(tmp_path)
    rec = L.load_genesis(p)
    assert rec["genesis_digest"] == GENESIS
    with pytest.raises(L.LedgerValidationError, match="refusing to create"):
        L.create_ledger(p, GENESIS, CYCLE, 2026)


def test_06_filename_law_and_window_season(tmp_path):
    with pytest.raises(L.LedgerValidationError, match="filename law"):
        L.create_ledger(tmp_path / "wrong_name.jsonl", GENESIS, CYCLE, 2026)
    with pytest.raises(L.LedgerValidationError, match="exactly 2026"):
        L.create_ledger(tmp_path / f"predictions_{CYCLE}_2027.jsonl",
                        GENESIS, CYCLE, 2027)
    with pytest.raises(L.LedgerValidationError, match="exactly 2026"):
        L.create_ledger(tmp_path / f"predictions_{CYCLE}_2025.jsonl",
                        GENESIS, CYCLE, 2025)


# ---------------------------------------------------------------- 7-13 timestamp law
def test_07_reject_recorded_at_equal_to_tip(tmp_path):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError, match="STRICTLY"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p),
                                    recorded_at_utc="2026-05-14T23:00:00Z")])


def test_08_reject_recorded_at_after_tip(tmp_path):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError, match="STRICTLY"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p),
                                    recorded_at_utc="2026-05-14T23:00:01Z")])


def test_09_strict_inequality_one_second_before_tip_is_valid_row_but_fails_batch_law(tmp_path):
    p = new_ledger(tmp_path)
    # row law (< tip) holds at 1s before tip, but the T0-6h10m batch-anchor law refuses
    with pytest.raises(L.LedgerValidationError, match="day-batch law"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p),
                                    recorded_at_utc="2026-05-14T22:59:59Z")])


@pytest.mark.parametrize("bad", ["not-a-date", "2026-05-14 23:00:00Z",
                                 "2026-05-14T23:00:00", "2026-13-01T00:00:00Z",
                                 "2026-05-14T23:00:00+00:00", 12345])
def test_10_reject_malformed_timestamps(tmp_path, bad):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p), tip_utc=bad)])


def test_11_local_date_law_et_conversion(tmp_path):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError, match="local_date law"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p),
                                    local_date="2026-05-15")])


def test_12_utc_midnight_crossing_et_day_key(tmp_path):
    # 03:00Z is 23:00 ET the PREVIOUS day -> local_date must be the earlier date
    assert L.et_local_date(
        L.parse_iso_z("2026-06-02T03:00:00Z")).isoformat() == "2026-06-01"


def test_13_scoring_rejects_malformed_actual_tip(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    with pytest.raises(L.LedgerValidationError):
        L.validate_for_scoring(p, {"SYN-G1": "garbage"})


# ---------------------------------------------------------------- 14-21 daily-batch law
def test_14_batch_exactly_at_anchor_refused(tmp_path):
    # 2026-REMAINDER strict boundary: the anchor T0-6h10m is an EXCLUSIVE
    # deadline (frozen 2027 law was inclusive at exactly 6h — disclosed change).
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z"])
    rows[0]["recorded_at_utc"] = "2026-05-14T16:50:00Z"  # exactly 6h10m
    rows[0]["prev_row_hash"] = tail_parent(p)
    with pytest.raises(L.LedgerValidationError, match="STRICTLY before the batch"):
        L.append_batch(p, rows)
    assert p.read_text(encoding="utf-8") == ""


def test_15_batch_1s_past_anchor_refused(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z"])
    rows[0]["recorded_at_utc"] = "2026-05-14T16:50:01Z"  # 1s past the anchor
    rows[0]["prev_row_hash"] = tail_parent(p)
    with pytest.raises(L.LedgerValidationError, match="day-batch law"):
        L.append_batch(p, rows)


def test_15b_batch_1s_inside_anchor_accepted(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z"])
    rows[0]["recorded_at_utc"] = "2026-05-14T16:49:59Z"  # 1s inside the anchor
    rows[0]["prev_row_hash"] = tail_parent(p)
    assert len(L.append_batch(p, rows)) == 1


def test_16_batch_law_uses_first_tip_of_day_not_each_row(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z",
                                     "2026-05-15T02:00:00Z"])
    # all recorded at T-7h relative to the FIRST tip: row 2 is 10.5h before its
    # own tip but the law keys on the day's first tip -> valid; auto-chained
    for r in rows:
        r["recorded_at_utc"] = "2026-05-14T16:00:00Z"
    assert len(L.append_batch(p, rows)) == 2


def test_17_batch_mixed_et_days_refused(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z"])
    rows += batch_rows("2026-05-15", ["2026-05-15T23:00:00Z"])
    for r in rows:
        r["prev_row_hash"] = tail_parent(p)
    with pytest.raises(L.LedgerValidationError, match="exactly one ET local_date"):
        L.append_batch(p, rows)


def test_18_second_batch_same_et_day_refused_no_backfill(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z"])
    rows[0]["prev_row_hash"] = tail_parent(p)
    L.append_batch(p, rows)
    late = batch_rows("2026-05-14", ["2026-05-14T20:00:00Z"])
    late[0]["game_id"] = "SYN-LATE-1"
    late[0]["recorded_at_utc"] = "2026-05-14T10:00:00Z"
    late[0]["prev_row_hash"] = tail_parent(p)
    with pytest.raises(L.LedgerValidationError, match="already has"):
        L.append_batch(p, late)


def test_19_empty_batch_refused(tmp_path):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError, match="non-empty"):
        L.append_batch(p, [])


def test_20_batch_is_atomic_nothing_written_on_refusal(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z", "2026-05-15T01:00:00Z"])
    for r in rows:
        r["prev_row_hash"] = tail_parent(p)
    rows[1]["recorded_at_utc"] = "2026-05-14T22:00:00Z"  # 1h before FIRST tip
    # -> past the T0-6h10m anchor; batch law fires and NOTHING is written
    with pytest.raises(L.LedgerValidationError, match="day-batch law"):
        L.append_batch(p, rows)
    assert p.read_text(encoding="utf-8") == ""


def test_21_dst_spring_forward_et_day_key(tmp_path):
    # 2026-03-08 07:00Z = 03:00 EDT (spring-forward day, ET-4 active)
    assert L.et_local_date(
        L.parse_iso_z("2026-03-08T07:00:00Z")).isoformat() == "2026-03-08"
    # 2026-11-01 06:00Z = 01:00 EST (fall-back day, ET-5 active)
    assert L.et_local_date(
        L.parse_iso_z("2026-11-01T06:00:00Z")).isoformat() == "2026-11-01"


# ---------------------------------------------------------------- 22-28 row laws
def test_22_reject_outcome_key_injection(tmp_path):
    # defense-in-depth: the no-outcome law fires on any key match (unit level),
    # and the append path refuses an injected-key row (closed field set fires
    # first — either refusal is fail-closed).
    p = new_ledger(tmp_path)
    row = make_row(prev_row_hash=tail_parent(p))
    row["home_score_hint"] = "5"
    with pytest.raises(L.LedgerValidationError):
        L.append_batch(p, [row])
    probe = make_row()
    probe["home_score_hint"] = "5"
    assert L._has_outcome_key(probe) == "home_score_hint"


@pytest.mark.parametrize("bad", ["0.5", "0.5000000", "1.000000", "0.000000",
                                 "-0.500000", 0.5, "0,500000"])
def test_23_reject_p_home_format_and_domain(tmp_path, bad):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p), p_home=bad)])


def test_24_accept_p_home_strict_open_boundaries(tmp_path):
    p = new_ledger(tmp_path)
    row = make_row(prev_row_hash=tail_parent(p), p_home="0.000001")
    assert len(L.append_batch(p, [row])) == 1
    row2 = make_row(game_id="SYN-G2", p_home="0.999999",
                    tip_utc="2026-05-15T23:00:00Z", local_date="2026-05-15",
                    prev_row_hash=tail_parent(p))
    assert len(L.append_batch(p, [row2])) == 1


def test_25_reject_duplicate_game_arm(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    # the day-batch law (one batch per ET day) fires first for the same day;
    # either refusal is correct fail-closed behavior
    with pytest.raises(L.LedgerValidationError, match="duplicate|already has"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p))])


def test_26_reject_arm_outside_frozen_registry(tmp_path):
    p = new_ledger(tmp_path, arm_registry=["B1-WNBA", "B0"])
    with pytest.raises(L.LedgerValidationError, match="arm registry law"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p),
                                    arm_id="NOT-FROZEN")])


def test_27_window_law_post_only_and_season_2026_only(tmp_path):
    p = new_ledger(tmp_path)
    # "PRE" fails the enum law first (fail-closed either way);
    # "REG" passes the enum and is refused by the POST-only window law.
    with pytest.raises(L.LedgerValidationError, match="game_type must be one of"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p),
                                    game_type="PRE")])
    with pytest.raises(L.LedgerValidationError, match="window law"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p),
                                    game_type="REG")])
    with pytest.raises(L.LedgerValidationError, match="window law"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p), season=2027)])
    with pytest.raises(L.LedgerValidationError, match="window law"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p), season=2025)])


def test_28_supplied_row_hash_must_match_recomputation(tmp_path):
    p = new_ledger(tmp_path)
    row = make_row(prev_row_hash=tail_parent(p), row_hash="f" * 64)
    with pytest.raises(L.LedgerValidationError, match="row_hash"):
        L.append_batch(p, [row])


# ---------------------------------------------------------------- 29-34 chain/tamper
def test_29_reject_wrong_chain_parent(tmp_path):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError, match="chain parent"):
        L.append_batch(p, [make_row(prev_row_hash="e" * 64)])


def test_30_reject_wrong_genesis_anchor_on_first_row(tmp_path):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError, match="chain parent"):
        L.append_batch(p, [make_row(prev_row_hash="GENESIS:" + "0" * 64)])


def test_31_append_fails_closed_without_genesis_binding(tmp_path):
    p = tmp_path / f"predictions_{CYCLE}_2026.jsonl"
    p.touch()
    with pytest.raises(L.LedgerIntegrityError, match="unbound"):
        L.append_batch(p, [make_row(prev_row_hash=tail_parent(p))])


def test_32_verify_flags_bit_flip_tamper_and_scoring_fails_closed(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    rewrite_line(p, 0, lambda r: r.update(p_home="0.999999"))
    broken = L.verify_chain(p)
    assert broken and broken[0] == 0
    with pytest.raises(L.LedgerIntegrityError, match="fail-closed"):
        L.validate_for_scoring(p, {"SYN-G1": "2026-05-15T02:00:00Z"})


def test_33_verify_flags_competent_tamper_with_recomputed_hash(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    add_row(p, game_id="SYN-G2", tip_utc="2026-05-15T23:00:00Z",
            local_date="2026-05-15")

    def mutate(r):
        r["p_home"] = "0.123456"
        r["row_hash"] = L.compute_row_hash(r, L.FIELD_ORDER)
    rewrite_line(p, 0, mutate)
    broken = L.verify_chain(p)
    assert 1 in broken  # row 1's prev now points at the stale row-0 hash


def test_34_verify_flags_blank_and_foreign_lines(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    lines = p.read_text(encoding="utf-8").splitlines()
    p.write_text(lines[0] + "\nnot-json\n", encoding="utf-8")
    assert L.verify_chain(p) == [1]
    p.write_text(lines[0] + "\n\n", encoding="utf-8")
    assert L.verify_chain(p) == [1]


# ---------------------------------------------------------------- 35-39 notices
def test_35_postpone_later_rows_stay_valid(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    L.postpone(p, "SYN-G1", "2026-05-20T23:00:00Z", "synthetic flex",
               recorded_by="SYN-RECORDER")
    res = L.validate_for_scoring(p, {"SYN-G1": "2026-05-20T23:00:00Z"})
    assert res["counts"].get(L.VALID_PROSPECTIVE) == 1


def test_36_postpone_earlier_past_record_marks_invalid(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)  # recorded 10:00Z
    L.postpone(p, "SYN-G1", "2026-05-14T09:00:00Z", "synthetic earlier move",
               recorded_by="SYN-RECORDER")
    res = L.validate_for_scoring(p, {"SYN-G1": "2026-05-14T09:00:00Z"})
    assert res["counts"].get(L.INVALID_PROSPECTIVE) == 1


def test_37_cancel_not_scored_cancelled(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    L.cancel(p, "SYN-G1", "synthetic cancellation", recorded_by="SYN-RECORDER")
    res = L.validate_for_scoring(p, {})
    assert res["counts"].get(L.NOT_SCORED_CANCELLED) == 1


def test_38_notice_chain_is_hashed_and_tamper_detected(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    n = L.postpone(p, "SYN-G1", "2026-05-21T23:00:00Z", "synthetic flex",
                   recorded_by="SYN-RECORDER")
    assert n["row_hash"] and L.verify_chain(p) == []
    rewrite_line(p, 1, lambda r: r.update(reason="tampered"))
    assert L.verify_chain(p) == [1]


def test_39_postpone_requires_metadata_when_game_has_no_rows(tmp_path):
    p = new_ledger(tmp_path)
    with pytest.raises(L.LedgerValidationError, match="prior_tip_utc"):
        L.postpone(p, "SYN-NOPE", "2026-05-21T23:00:00Z", "x",
                   recorded_by="SYN-RECORDER")
    n = L.postpone(p, "SYN-NOPE", "2026-05-21T23:00:00Z", "x",
                   prior_tip_utc="2026-05-20T23:00:00Z",
                   game_meta={"season": 2026, "game_type": "POST",
                              "home_team": "SYN-A", "away_team": "SYN-B"},
                   recorded_by="SYN-RECORDER")
    assert n["row_hash"]


def test_40_no_real_ledger_file_exists_in_lane_or_repo(tmp_path):
    # boundary law: this round writes no real ledger anywhere — the REAL
    # predictions_WNBA-WINPROB-2026-REMAINDER-V1_2026.jsonl is created ONLY
    # after the owner typed the cycle GO.
    import subprocess
    wt = Path(__file__).resolve().parents[2]
    out = subprocess.run(["git", "-C", str(wt), "ls-files"],
                         capture_output=True, text=True).stdout
    assert "predictions_WNBA-WINPROB-2026-REMAINDER-V1" not in out
    assert not list((wt / "research/control/WNBA-WINPROB-2026-REMAINDER-V1")
                    .rglob("predictions_*.jsonl"))


# ---------------------------------------------------------------- 41-46 scoring classes
def test_41_valid_prospective_happy_scoring(tmp_path):
    p = new_ledger(tmp_path, freeze_utc="2026-05-01T00:00:00Z")
    add_row(p)
    res = L.validate_for_scoring(p, {"SYN-G1": "2026-05-14T23:00:00Z"})
    assert res["counts"] == {L.VALID_PROSPECTIVE: 1}
    assert res["aggregate_eligible_rows"] == 1


def test_42_retro_injection_actual_equals_recorded_is_invalid(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    res = L.validate_for_scoring(p, {"SYN-G1": "2026-05-14T10:00:00Z"})
    assert res["counts"].get(L.INVALID_PROSPECTIVE) == 1


def test_43_played_before_freeze_is_not_run(tmp_path):
    p = new_ledger(tmp_path, freeze_utc="2026-06-01T00:00:00Z")
    add_row(p)  # tip 2026-05-14 < freeze
    res = L.validate_for_scoring(p, {"SYN-G1": "2026-05-14T23:00:00Z"})
    assert res["counts"].get(L.NOT_RUN) == 1


def test_44_no_actual_data_and_not_run_games_census(tmp_path):
    p = new_ledger(tmp_path)
    add_row(p)
    res = L.validate_for_scoring(p, {"SYN-G1": "2026-05-14T23:00:00Z",
                                     "SYN-MISSING": "2026-05-16T23:00:00Z"})
    assert res["not_run_games"] == ["SYN-MISSING"]
    row = [v for v in res["rows"] if v["game_id"] == "SYN-G1"][0]
    assert row["verdict"] == L.VALID_PROSPECTIVE


def test_45_batch_of_full_slate_end_to_end(tmp_path):
    p = new_ledger(tmp_path, freeze_utc="2026-05-01T00:00:00Z",
                   arm_registry=["B0", "B1-WNBA"])
    tips = ["2026-06-01T23:00:00Z", "2026-06-01T23:30:00Z",
            "2026-06-02T00:00:00Z", "2026-06-02T00:30:00Z",
            "2026-06-02T01:00:00Z", "2026-06-02T01:30:00Z"]  # 6-game slate, one ET day
    rows = batch_rows("2026-06-01", tips)
    for r in rows:
        r["recorded_at_utc"] = "2026-06-01T12:00:00Z"  # 11h before first tip
    # prev left null -> auto-chain within the batch
    assert len(L.append_batch(p, rows)) == 6
    actual = {r["game_id"]: r["tip_utc"] for r in rows}
    res = L.validate_for_scoring(p, actual)
    assert res["counts"] == {L.VALID_PROSPECTIVE: 6}
    assert res["not_run_games"] == []
    assert L.verify_chain(p) == []


def test_46_recorded_days_early_is_allowed_lead_time(tmp_path):
    p = new_ledger(tmp_path)
    rows = batch_rows("2026-05-14", ["2026-05-14T23:00:00Z"])
    rows[0]["recorded_at_utc"] = "2026-05-12T00:00:00Z"  # days ahead: > anchor holds
    rows[0]["prev_row_hash"] = tail_parent(p)
    assert len(L.append_batch(p, [rows[0]])) == 1


# ---------------------------------------------------------------- 47 freeze pins
def test_47_freeze_sha_pins_remeasured():
    """Re-measure the frozen engine + data artifact pins at run time.

    Any mismatch = BLOCKED_TOOLING condition surfaced loudly (fail, never skip).
    Pins per the 2026-REMAINDER dispatch + FREEZE_PACKET (ERRATUM_R1 engine
    pins, PREP data pins)."""
    import hashlib
    import os

    def sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    frozen_engine = Path(
        "/Users/hoangminhlong/my-quantitative/.worktrees/wnba-playerfeat-scored-v1"
        "/integration/lanes/T_SELECT")
    pins = {
        frozen_engine / "arms.py":
            "82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3",
        frozen_engine / "harness.py":
            "b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e",
        Path(os.path.expanduser(
            "~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/"
            "wnba_player_features_2002_2026.parquet")):
            "ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf",
        Path(os.path.expanduser(
            "~/.my-quantitative-data/wnba-prep-v1/extensions/"
            "wnba_schedule_crosswalk_2026.csv")):
            "e4115f04d45d3bc7fb9b43eca9c5babd26185e2ecf51e65bc3b66bf02aa6eea6",
        Path(os.path.expanduser(
            "~/.my-quantitative-data/wnba-v1/raw/ATTRIBUTION.md")):
            "1068e5c7aae614347550266da94d067f38c7c2cc9b569e685cfed3aced301f5a",
    }
    for path, pin in pins.items():
        assert path.exists(), f"BLOCKED_TOOLING: pinned artifact missing: {path}"
        measured = sha256_file(path)
        assert measured == pin, (
            f"BLOCKED_TOOLING: sha pin mismatch for {path.name}: "
            f"measured {measured} != pinned {pin}")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
