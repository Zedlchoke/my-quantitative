"""test_successor_synthetic.py — S_SYNTH lane, cycle NFL-WINPROB-NG-SCORED-V1.

Successor-level SYNTHETIC tests layered on the ported ledger tool
(`research/control/NFL-WINPROB-NG-SCORED-V1/ledger/nfl_ng_ledger.py`, byte-identical
port of the predecessor `nfl_ng_ledger@1`) and the AS-FROZEN selection machinery
(`lanes/T_SELECT/arms.py` / `select.py`, imported UNMODIFIED; sha256s asserted below
against the freeze packet §9 values).

Everything here is SYNTHETIC: fabricated lineages (``SY*``), fabricated game ids
(``SYNTH_*``), fabricated digests, far-future fabricated kickoffs. No real NFL team,
game, schedule row, or pbp row is read; no outcome metric is computed anywhere.

Covers (per DISPATCH_S_SYNTH.md task 2):
  a. designed-null prediction equivalence (C1 beta=0, C2 lambda=0 & h=0,
     C3 theta=0, C4 delta=0 — each p_home BIT-IDENTICAL to B1*, max |dp| == 0.0)
     on 4 synthetic game streams;
  b. frozen-config determinism (C3 theta=50 twice -> byte-identical outputs);
  c. as-of canary (a result with kickoff >= prediction time is absent from the
     prediction inputs — asserted at the replay-batch level AND the
     input-assembly level);
  d. timestamp law (recorded_at >= kickoff rejected) + margin law:
     the tool exposes NO margin config -> tool-level >=6h margin is
     NOT_RUN_MARGIN_CONFIG; the >=6h capture margin is enforced caller-side
     by sandbox_dryrun.enforce_capture_margin and tested here;
  e. hash-chain tamper (flip ONE byte in a sandbox ledger copy -> validation
     fails loudly: verify_chain flags the row, append and scoring fail closed).

Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
      lanes/S_SYNTH/test_successor_synthetic.py -v
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Paths + frozen-module loading (UNMODIFIED as-frozen code only)
# ---------------------------------------------------------------------------
WORKTREE = Path(__file__).resolve().parent.parent.parent  # .../integration
T_SELECT = WORKTREE / "lanes" / "T_SELECT"
PORT_DIR = WORKTREE / "research" / "control" / "NFL-WINPROB-NG-SCORED-V1" / "ledger"
LANE_DIR = Path(__file__).resolve().parent

# Freeze-packet §9 / §5 pinned digests (FREEZE_PACKET.md; freeze_digests.json).
FROZEN_SHA = {
    "arms.py": "19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8",
    "select.py": "8f733d456e895959924df84f295b92b0292c4713eac2499b3f10b21bf66f4628",
    "boot.py": "0674b95fd7a4aa736e2a50821b1acd29606b8f30583cab6f46553433c1b0887a",
}
PORTED_LEDGER_SHA = "6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c"

# The freeze GENESIS digest — referenced ONLY to assert the sandbox genesis
# differs from it (never written into any row/sidecar).
FREEZE_GENESIS_DIGEST = "ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # required: dataclass processing resolves cls.__module__
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


ledger = _load_module("s_synth_ported_ledger", PORT_DIR / "nfl_ng_ledger.py")
arms = _load_module("s_synth_frozen_arms", T_SELECT / "arms.py")
tsel_select = _load_module("s_synth_frozen_select", T_SELECT / "select.py")
tsel_select._load_heavy()  # bind select.arms/boot per the module's own loader (no I/O)
dryrun = _load_module("s_synth_dryrun", LANE_DIR / "sandbox_dryrun.py")


# ---------------------------------------------------------------------------
# SYNTHETIC fixtures
# ---------------------------------------------------------------------------
UTC = dt.timezone.utc


def synth_gameset(key, n_lineages, seasons, rounds, batch):
    """Deterministic synthetic GameSet (no RNG, no real data).

    Streams of fabricated games among fabricated lineages ``SY<key>NN``:
    each season/round every lineage hosts exactly one game; kickoffs come in
    same-kickoff batches of size ``batch`` (exercises the PROTOCOL §0.1 law);
    every ``batch``-th game is neutral-site; ~4/9 of results are fabricated
    ties (S=0.5 update law). Kickoff order is sorted by construction.
    """
    lineages = [f"SY{key}{i:02d}" for i in range(n_lineages)]
    base = int(dt.datetime(2100, 1, 1, tzinfo=UTC).timestamp())
    rows = []
    gid = 0
    total = n_lineages * rounds * len(seasons)
    n_slots = (total + batch - 1) // batch  # ceil; gid is global across seasons
    for si, season in enumerate(seasons):
        for r in range(rounds):
            for i in range(n_lineages):
                j = (i + r + 1) % n_lineages
                assert j != i
                slot = gid // batch
                assert slot < n_slots
                kick_ns = (base + si * 300 * 86400 + slot * 43200) * 10**9
                v = (gid * 37 + si * 11 + r * 3) % 9
                s_home = 1.0 if v < 4 else (0.5 if v == 4 else 0.0)
                rows.append(
                    dict(
                        kickoff_ns=kick_ns,
                        kickoff_date=dt.datetime.fromtimestamp(
                            kick_ns / 10**9, UTC
                        ).date().isoformat(),
                        home=lineages[i],
                        away=lineages[j],
                        s_home=s_home,
                        y_bin=1.0 if s_home == 1.0 else 0.0,
                        is_tie=s_home == 0.5,
                        is_reg=True,
                        is_neutral=(gid % 13 == 0),
                        season=season,
                        week=r + 1,
                        game_id=f"SYNTH_{key}_{season}_G{gid:04d}",
                    )
                )
                gid += 1
    col = lambda name, dtype: np.array([g[name] for g in rows], dtype=dtype)
    return arms.GameSet(
        df=None,
        kickoff_ns=col("kickoff_ns", np.int64),
        kickoff_date=col("kickoff_date", object),
        home=col("home", object),
        away=col("away", object),
        s_home=col("s_home", float),
        y_bin=col("y_bin", float),
        is_tie=col("is_tie", bool),
        is_reg=col("is_reg", bool),
        is_neutral=col("is_neutral", bool),
        season=col("season", np.int64),
        week=col("week", np.int64),
        game_id=col("game_id", object),
        quarantined_columns=[],
        n_dropped_over_ceiling=0,
        n_pre_dropped=0,
    )


def nonzero_z_table(seasons, lineages):
    """Nonzero synthetic offseason z values (proves theta=0 never leaks z)."""
    zt = {}
    for s in seasons[1:]:
        for i, lg in enumerate(lineages):
            z = ((i % 5) + 1) * 0.25 * (1.0 if i % 2 == 0 else -1.0)
            assert z != 0.0
            zt[(s, lg)] = z
    return zt


STREAMS = {
    "A": dict(n_lineages=8, seasons=(2101, 2102, 2103), rounds=4, batch=2),
    "B": dict(n_lineages=12, seasons=(2101, 2102), rounds=3, batch=3),
    "C": dict(n_lineages=6, seasons=(2101, 2102, 2103, 2104), rounds=5, batch=1),
    "D": dict(n_lineages=10, seasons=(2101, 2102, 2103), rounds=3, batch=4),
}


def b1_star_p(gs):
    recs = arms.replay_elo(gs)
    return recs, np.array([r.e_home for r in recs], dtype=float)


# ---------------------------------------------------------------------------
# (0) frozen-code identity
# ---------------------------------------------------------------------------


def test_frozen_code_and_port_digests_match_freeze():
    for fname, sha in FROZEN_SHA.items():
        assert _sha256_file(T_SELECT / fname) == sha, f"{fname} is not the frozen bytes"
    assert _sha256_file(PORT_DIR / "nfl_ng_ledger.py") == PORTED_LEDGER_SHA


# ---------------------------------------------------------------------------
# (a) Designed-null prediction equivalence vs B1* (max |dp| == 0.0, bit-exact)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stream_key", sorted(STREAMS))
def test_designed_null_equivalence_vs_b1_star(stream_key):
    gs = synth_gameset(stream_key, **STREAMS[stream_key])
    recs, p_b1 = b1_star_p(gs)
    assert len(p_b1) == len(gs.kickoff_ns) >= 2 * STREAMS[stream_key]["n_lineages"]

    zt = nonzero_z_table(
        STREAMS[stream_key]["seasons"],
        [f"SY{stream_key}{i:02d}" for i in range(STREAMS[stream_key]["n_lineages"])],
    )

    # C1, beta = 0 (formula from frozen select.p_stream)
    cfg_c1 = tsel_select.Cfg("C1_B000", "C1", {"beta": 0.0}, 0, "designed_null")
    p_c1 = tsel_select.p_stream(cfg_c1, {"records": recs})
    # C2, lambda = 0 AND h = 0 (frozen arms.replay_c2)
    p_c2 = arms.replay_c2(recs, 0.0, 1.0 / 3.0, 0.0)
    # C3, theta = 0 with NONZERO synthetic z present (frozen arms.replay_elo)
    recs_c3 = arms.replay_elo(gs, z_table=zt, theta=0.0)
    p_c3 = np.array([r.e_home for r in recs_c3], dtype=float)
    # C4, delta = 0 (formula from frozen select.p_stream)
    cfg_c4 = tsel_select.Cfg("C4_D000", "C4", {"delta": 0.0}, 0, "designed_null")
    p_c4 = tsel_select.p_stream(cfg_c4, {"records": recs})

    for name, p in (("C1_B000", p_c1), ("C2_NULL", p_c2), ("C3_T000", p_c3), ("C4_D000", p_c4)):
        assert float(np.max(np.abs(p - p_b1))) == 0.0, f"{name} on stream {stream_key}: max|dp| != 0"
        assert p.tobytes() == p_b1.tobytes(), f"{name} on stream {stream_key}: not bit-identical"


def test_designed_null_is_not_vacuous_nonzero_configs_differ():
    """Power check: the SAME frozen formulas with their first nonzero grid
    values DO move p_home away from B1* on the same streams (the equivalence
    above is a real equivalence, not a tautology)."""
    for stream_key in ("A", "B"):
        gs = synth_gameset(stream_key, **STREAMS[stream_key])
        recs, p_b1 = b1_star_p(gs)
        lineages = [f"SY{stream_key}{i:02d}" for i in range(STREAMS[stream_key]["n_lineages"])]
        zt = nonzero_z_table(STREAMS[stream_key]["seasons"], lineages)

        p_c1 = tsel_select.p_stream(
            tsel_select.Cfg("C1_B025", "C1", {"beta": 25.0}, 1, "candidate"),
            {"records": recs},
        )
        p_c2 = arms.replay_c2(recs, 0.25, 1.0 / 3.0, 25.0)
        recs_c3 = arms.replay_elo(gs, z_table=zt, theta=50.0)
        p_c3 = np.array([r.e_home for r in recs_c3], dtype=float)
        p_c4 = tsel_select.p_stream(
            tsel_select.Cfg("C4_D025", "C4", {"delta": 25.0}, 1, "gate_only"),
            {"records": recs},
        )
        assert float(np.max(np.abs(p_c1 - p_b1))) > 0.0
        assert float(np.max(np.abs(p_c2 - p_b1))) > 0.0
        assert float(np.max(np.abs(p_c3 - p_b1))) > 0.0
        assert float(np.max(np.abs(p_c4 - p_b1))) > 0.0


# ---------------------------------------------------------------------------
# (b) Frozen-config determinism: C3 theta=50 twice -> byte-identical
# ---------------------------------------------------------------------------


def _serialize_records(recs) -> bytes:
    payload = [
        {f: getattr(r, f) for f in r.__dataclass_fields__}
        for r in recs
    ]
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_c3_theta50_determinism_run_twice_byte_identical(tmp_path):
    gs = synth_gameset("A", **STREAMS["A"])
    lineages = [f"SYA{i:02d}" for i in range(STREAMS["A"]["n_lineages"])]
    zt = nonzero_z_table(STREAMS["A"]["seasons"], lineages)

    recs1 = arms.replay_elo(gs, z_table=zt, theta=50.0)
    recs2 = arms.replay_elo(gs, z_table=zt, theta=50.0)
    b1 = _serialize_records(recs1)
    b2 = _serialize_records(recs2)
    assert b1 == b2
    assert hashlib.sha256(b1).hexdigest() == hashlib.sha256(b2).hexdigest()

    p1 = np.array([r.e_home for r in recs1], dtype=float)
    p2 = np.array([r.e_home for r in recs2], dtype=float)
    assert p1.tobytes() == p2.tobytes()

    # persisted artifacts byte-identical across runs
    f1 = tmp_path / "run1.bin"
    f2 = tmp_path / "run2.bin"
    f1.write_bytes(b1)
    f2.write_bytes(b2)
    assert f1.read_bytes() == f2.read_bytes()


# ---------------------------------------------------------------------------
# (c) As-of canary: results with kickoff >= prediction time are absent from
#     the prediction inputs (replay level + input-assembly level)
# ---------------------------------------------------------------------------


def _canary_streams():
    """Small explicit stream: 4 lineages, warmup games, target game X at
    kickoff T, canary games at kickoff == T and kickoff == T + 1 day."""
    lgs = ["SYC00", "SYC01", "SYC02", "SYC03"]
    base = int(dt.datetime(2100, 6, 1, tzinfo=UTC).timestamp())
    warm = []
    gid = 0
    for r in range(3):  # season 2101 warmup
        for i in range(4):
            j = (i + r + 1) % 4
            warm.append(dict(
                kickoff_ns=(base + r * 7 * 86400 + gid * 3600) * 10**9,
                home=lgs[i], away=lgs[j],
                s_home=1.0 if (gid % 3 == 0) else 0.0,
                season=2101, week=r + 1, game_id=f"SYNTH_CAN_WARM_{gid:03d}",
                is_neutral=False,
            ))
            gid += 1
    t_ns = (base + 300 * 86400) * 10**9
    target = dict(kickoff_ns=t_ns, home=lgs[0], away=lgs[1], s_home=1.0,
                  season=2102, week=1, game_id="SYNTH_CAN_TARGET", is_neutral=False)
    can_same = dict(kickoff_ns=t_ns, home=lgs[2], away=lgs[3], s_home=1.0,
                    season=2102, week=1, game_id="SYNTH_CANARY_SAME_KICK", is_neutral=False)
    can_later = dict(kickoff_ns=t_ns + 86400 * 10**9, home=lgs[2], away=lgs[3], s_home=1.0,
                     season=2102, week=1, game_id="SYNTH_CANARY_LATER_KICK", is_neutral=False)
    return warm, target, can_same, can_later


def _mini_gameset(games):
    games = sorted(games, key=lambda g: g["kickoff_ns"])
    col = lambda name, dtype: np.array([g[name] for g in games], dtype=dtype)
    n = len(games)
    return arms.GameSet(
        df=None,
        kickoff_ns=col("kickoff_ns", np.int64),
        kickoff_date=np.array([
            dt.datetime.fromtimestamp(g["kickoff_ns"] / 10**9, UTC).date().isoformat()
            for g in games
        ], dtype=object),
        home=col("home", object),
        away=col("away", object),
        s_home=col("s_home", float),
        y_bin=col("s_home", float),
        is_tie=np.zeros(n, dtype=bool),
        is_reg=np.ones(n, dtype=bool),
        is_neutral=col("is_neutral", bool),
        season=col("season", np.int64),
        week=col("week", np.int64),
        game_id=col("game_id", object),
        quarantined_columns=[],
        n_dropped_over_ceiling=0,
        n_pre_dropped=0,
    )


def _target_record(gs, target_id="SYNTH_CAN_TARGET"):
    for r in arms.replay_elo(gs):
        if r.game_id == target_id:
            return r
    raise AssertionError("target game missing from replay")


def test_asof_same_kickoff_canary_absent_from_prediction_inputs():
    warm, target, can_same, _ = _canary_streams()
    base = _mini_gameset(warm + [target])
    with_canary_s1 = _mini_gameset(warm + [target, {**can_same, "s_home": 1.0}])
    with_canary_s0 = _mini_gameset(warm + [target, {**can_same, "s_home": 0.0}])

    rx, r1, r0 = _target_record(base), _target_record(with_canary_s1), _target_record(with_canary_s0)
    for attr in ("r_home", "r_away", "e_home", "e_away"):
        assert getattr(rx, attr) == getattr(r1, attr) == getattr(r0, attr), (
            f"same-kickoff canary leaked into the target's prediction inputs via {attr}"
        )


def test_asof_later_kickoff_canary_absent_from_prediction_inputs():
    warm, target, _, can_later = _canary_streams()
    base = _mini_gameset(warm + [target])
    with_later = _mini_gameset(warm + [target, can_later])
    rx, rl = _target_record(base), _target_record(with_later)
    for attr in ("r_home", "r_away", "e_home", "e_away"):
        assert getattr(rx, attr) == getattr(rl, attr), (
            f"later-kickoff canary leaked into the target's prediction inputs via {attr}"
        )


def test_asof_input_builder_excludes_kickoff_at_or_after_prediction_time():
    warm, target, can_same, can_later = _canary_streams()
    t_pred_ns = target["kickoff_ns"] - 6 * 3600 * 10**9  # prediction recorded 6h before kickoff

    events = warm + [target, can_same, can_later]
    inputs = dryrun.prediction_inputs_asof(events, t_pred_ns)
    ids = {e["game_id"] for e in inputs}
    assert "SYNTH_CAN_TARGET" not in ids          # kickoff > t_pred -> future
    assert "SYNTH_CANARY_SAME_KICK" not in ids    # canary at kickoff == T > t_pred
    assert "SYNTH_CANARY_LATER_KICK" not in ids   # canary at kickoff > T
    assert ids == {g["game_id"] for g in warm}    # only strictly-prior games enter
    # injecting the canaries changed nothing about the admitted set
    inputs_clean = dryrun.prediction_inputs_asof(warm, t_pred_ns)
    assert {e["game_id"] for e in inputs_clean} == ids


# ---------------------------------------------------------------------------
# (d) Timestamp law + capture-margin law
# ---------------------------------------------------------------------------


def _tmp_sandbox_ledger(tmp_path, cycle="SANDBOX-TEST", season=2100):
    genesis = hashlib.sha256(
        json.dumps(
            {"cycle_id": cycle, "kind": "SANDBOX_SYNTHETIC_GENESIS", "season": season},
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    path = tmp_path / f"predictions_{cycle}_{season}.jsonl"  # tool §1 filename law
    ledger.create_ledger(path, genesis, cycle, season,
                         created_at_utc="2100-01-01T00:00:00Z")
    return path, genesis, cycle


def _sandbox_row(path, genesis, cycle, **over):
    rows = ledger.load_rows(path)
    prev = f"GENESIS:{genesis}" if not rows else rows[-1]["row_hash"]
    kickoff = over.pop("kickoff_utc", "2100-10-10T19:00:00Z")
    row = {
        "schema_version": "nfl_ng_ledger@1",
        "cycle_id": cycle,
        "game_id": "SYNTH_TST_G01",
        "season": 2100,
        "game_type": "REG",
        "home_team": "SYT01",
        "away_team": "SYT02",
        "kickoff_utc": kickoff,
        "recorded_at_utc": over.pop("recorded_at_utc", "2100-10-10T00:00:00Z"),
        "arm_id": "B0",
        "arm_config_digest": "aa" * 32,
        "model_version": "SYNTHCOMMIT-SANDBOX+SYNTHPIPE-SANDBOX",
        "inputs_digest": "bb" * 32,
        "p_home": "0.571399",
        "recorded_by": "S_SYNTH_TEST_RECORDER",
        "prev_row_hash": prev,
    }
    row.update(over)
    return ledger.append(path, row)


def test_tool_rejects_recorded_at_at_or_after_kickoff(tmp_path):
    path, genesis, cycle = _tmp_sandbox_ledger(tmp_path)
    with pytest.raises(ledger.LedgerValidationError, match="R2"):
        _sandbox_row(path, genesis, cycle, recorded_at_utc="2100-10-10T19:00:00Z")  # == kickoff
    path2, genesis2, cycle2 = _tmp_sandbox_ledger(tmp_path, cycle="SANDBOX-TEST2")
    with pytest.raises(ledger.LedgerValidationError, match="R2"):
        _sandbox_row(path2, genesis2, cycle2, recorded_at_utc="2100-10-10T19:00:01Z")  # > kickoff
    # and the strict law accepts one second before
    _sandbox_row(path2, genesis2, cycle2, recorded_at_utc="2100-10-10T18:59:59Z")
    assert ledger.verify_chain(path2) == []


def test_tool_has_no_margin_config_not_run_margin_config():
    """Margin-law disposition: the ported tool enforces ONLY the strict
    recorded_at < kickoff law; no >=6h margin knob exists -> the tool-level
    margin check is NOT_RUN_MARGIN_CONFIG (recorded in VERDICT_TABLE.md).
    The only 'margin' occurrence in the ported source is the R8 no-outcome
    vocabulary token inside OUTCOME_BLOCKLIST."""
    params = list(inspect.signature(ledger.append).parameters)
    assert params == ["path", "row"], "append grew parameters — re-audit the margin law"
    assert list(inspect.signature(ledger.create_ledger).parameters) == [
        "path", "genesis_digest", "cycle_id", "season", "arm_registry",
        "freeze_utc", "created_at_utc",
    ]
    margin_like = [n for n in dir(ledger) if "margin" in n.lower() and n != "OUTCOME_BLOCKLIST"]
    assert margin_like == [], f"unexpected margin config appeared: {margin_like}"
    src = (PORT_DIR / "nfl_ng_ledger.py").read_text(encoding="utf-8")
    occurrences = [l for l in src.splitlines() if "margin" in l.lower()]
    assert occurrences == ['    "margin",  # dispatch blocklist'], (
        f"'margin' appears outside the R8 OUTCOME_BLOCKLIST vocabulary: {occurrences}"
    )


def test_caller_side_six_hour_capture_margin_enforced():
    first_kick = "2030-09-12T17:00:00Z"
    # 7+ days early: accepted
    dryrun.enforce_capture_margin("2030-09-05T12:00:00Z", first_kick)
    # exactly 6h: accepted (margin law is >= 6h)
    dryrun.enforce_capture_margin("2030-09-12T11:00:00Z", first_kick)
    # 5h59m: rejected loudly
    with pytest.raises(dryrun.SandboxError, match="capture margin law"):
        dryrun.enforce_capture_margin("2030-09-12T11:01:00Z", first_kick)
    # recorded after the first kickoff: rejected
    with pytest.raises(dryrun.SandboxError, match="capture margin law"):
        dryrun.enforce_capture_margin("2030-09-13T00:00:00Z", first_kick)


# ---------------------------------------------------------------------------
# (e) Hash-chain tamper: one flipped byte -> loud failure everywhere
# ---------------------------------------------------------------------------


def _flip_p_home_digit(path: Path, occurrence: int) -> int:
    """Flip exactly ONE byte: a fractional digit inside the ``occurrence``-th
    ``"p_home":"`` value (0-based, file order). The byte stays a digit so the
    line remains parseable JSON and the break is detected by hash, not parse."""
    data = bytearray(path.read_bytes())
    needle = b'"p_home":"'
    idx = data.find(needle)
    for _ in range(occurrence):
        idx = data.find(needle, idx + 1)
    assert idx != -1
    digit_pos = idx + len(needle) + 2  # skip leading 0.
    old, new = (0x35, 0x36) if data[digit_pos] == 0x35 else (0x36, 0x35)
    data[digit_pos] = new
    path.write_bytes(bytes(data))
    return idx


def test_single_byte_flip_breaks_chain_loudly_last_row(tmp_path):
    path, genesis, cycle = _tmp_sandbox_ledger(tmp_path)
    _sandbox_row(path, genesis, cycle, game_id="SYNTH_TST_G01")
    _sandbox_row(path, genesis, cycle, game_id="SYNTH_TST_G02", arm_id="B1_STAR",
                 recorded_at_utc="2100-10-10T00:00:01Z")
    assert ledger.verify_chain(path) == []
    n_rows = len(ledger.load_rows(path))
    _flip_p_home_digit(path, occurrence=n_rows - 1)  # flip ONE byte in the LAST row
    broken = ledger.verify_chain(path)
    assert broken == [n_rows - 1], f"expected exactly the tampered row flagged, got {broken}"
    with pytest.raises(ledger.LedgerIntegrityError):
        ledger.append(path, {
            "schema_version": "nfl_ng_ledger@1", "cycle_id": "SANDBOX-TEST",
            "game_id": "SYNTH_TST_G03", "season": 2100, "game_type": "REG",
            "home_team": "SYT03", "away_team": "SYT04",
            "kickoff_utc": "2100-10-11T19:00:00Z",
            "recorded_at_utc": "2100-10-11T00:00:00Z",
            "arm_id": "C3", "arm_config_digest": "aa" * 32,
            "model_version": "SYNTHCOMMIT-SANDBOX+SYNTHPIPE-SANDBOX",
            "inputs_digest": "bb" * 32, "p_home": "0.571399",
            "recorded_by": "S_SYNTH_TEST_RECORDER",
            "prev_row_hash": ledger.load_rows(path)[-1]["row_hash"],
        })
    with pytest.raises(ledger.LedgerIntegrityError, match="broken"):
        ledger.validate_for_scoring(
            path,
            {"SYNTH_TST_G01": "2100-10-10T19:00:00Z", "SYNTH_TST_G02": "2100-10-10T19:00:00Z"},
            freeze_utc="2100-10-01T00:00:00Z",
        )


def test_single_byte_flip_breaks_chain_loudly_first_row(tmp_path):
    path, genesis, cycle = _tmp_sandbox_ledger(tmp_path, cycle="SANDBOX-TEST3")
    _sandbox_row(path, genesis, cycle, game_id="SYNTH_TST_G01")
    _sandbox_row(path, genesis, cycle, game_id="SYNTH_TST_G02", arm_id="B1_STAR",
                 recorded_at_utc="2100-10-10T00:00:01Z")
    _flip_p_home_digit(path, occurrence=0)  # flip ONE byte in the FIRST row
    broken = ledger.verify_chain(path)
    assert broken == [0]


# ---------------------------------------------------------------------------
# Sandbox genesis discipline (binds the dry-run's GENESIS law)
# ---------------------------------------------------------------------------


def test_sandbox_genesis_digest_is_64hex_and_never_the_freeze_genesis():
    d = dryrun.sandbox_genesis_digest()
    assert len(d) == 64 and all(c in "0123456789abcdef" for c in d)
    assert d != FREEZE_GENESIS_DIGEST
    assert d != FREEZE_GENESIS_DIGEST[:32] + "0" * 32
    # the freeze GENESIS digest appears nowhere in the sandbox genesis descriptor
    desc = json.dumps(dryrun.SANDBOX_GENESIS_DESCRIPTOR, sort_keys=True, separators=(",", ":"))
    assert FREEZE_GENESIS_DIGEST not in desc
    assert "GENESIS:" + FREEZE_GENESIS_DIGEST not in desc
