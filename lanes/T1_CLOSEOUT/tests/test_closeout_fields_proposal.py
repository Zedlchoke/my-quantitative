"""Tests for the T1 closeout-fields proposal, run against a COPY of the live
registry (tmpdir). Never touches the live registry."""
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path("/Users/hoangminhlong/my-quantitative")
LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
sys.path.insert(0, str(REPO / "research"))

from closeout_fields_proposal import update_closeout_fields  # noqa: E402


@pytest.fixture()
def reg_copy(tmp_path):
    dst = tmp_path / "CYCLE_REGISTRY.json"
    shutil.copy(REPO / "plans/CYCLE_REGISTRY.json", dst)
    (tmp_path / "CYCLE_REGISTRY.events.jsonl").write_text("")
    return dst


def _read(path):
    return json.loads(Path(path).read_text())


def test_budget_used_updates_with_journal(reg_copy):
    changes = update_closeout_fields(reg_copy, "NBA-WINPROB-SCORED-V1",
                                     budget_used=9, reason="test")
    assert changes and changes[0]["field"] == "budget.used"
    rec = [c for c in _read(reg_copy)["cycles"] if c["cycle_id"] == "NBA-WINPROB-SCORED-V1"][0]
    assert rec["budget"]["used"] == 9 and rec["budget"]["max"] == 9
    ev = (Path(reg_copy).parent / "CYCLE_REGISTRY.events.jsonl").read_text()
    assert "CYCLE_CLOSEOUT_FIELD_SYNC" in ev and "budget.used" in ev


def test_no_other_fields_touched(reg_copy):
    before = _read(reg_copy)
    update_closeout_fields(reg_copy, "NFL-WINPROB-SCORED-V1", budget_used=9)
    after = _read(reg_copy)
    for rec_b, rec_a in zip(before["cycles"], after["cycles"]):
        if rec_b["cycle_id"] == "NFL-WINPROB-SCORED-V1":
            assert rec_a["budget"]["used"] == 9
            rb, ra = dict(rec_b), dict(rec_a)
            rb["budget"] = {**rb["budget"], "used": 9}
            rb.pop("updated_at_utc", None); ra.pop("updated_at_utc", None)
            rb.pop("write_token", None); ra.pop("write_token", None)
            assert rb == ra


def test_validation_fails_closed(reg_copy):
    with pytest.raises(ValueError):
        update_closeze_invalid = update_closeout_fields(reg_copy, "NBA-WINPROB-SCORED-V1",
                                                        budget_used=10)  # > max 9
    with pytest.raises(ValueError):
        update_closeout_fields(reg_copy, "NBA-WINPROB-SCORED-V1", budget_used=-1)
    with pytest.raises(ValueError):
        update_closeout_fields(reg_copy, "NBA-WINPROB-SCORED-V1", s0="HALF")
    with pytest.raises(Exception):
        update_closeout_fields(reg_copy, "NO-SUCH-CYCLE", budget_used=1)


def test_noop_writes_nothing(reg_copy):
    before_bytes = Path(reg_copy).read_bytes()
    changes = update_closeout_fields(reg_copy, "NBA-WINPROB-SCORED-V1",
                                     budget_used=0)  # already 0 (stale) -> no-op
    assert changes == []
    assert Path(reg_copy).read_bytes() == before_bytes


def test_s0_update(reg_copy):
    changes = update_closeout_fields(reg_copy, "NBA-WINPROB-SCORED-V1", s0="CLOSED")
    assert changes and changes[0]["field"] == "s0"
    rec = [c for c in _read(reg_copy)["cycles"] if c["cycle_id"] == "NBA-WINPROB-SCORED-V1"][0]
    assert rec["s0"] == "CLOSED"
