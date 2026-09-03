"""S0/S1 isolation proofs: S0 reads allowed, EVERY S1 access denied.

Path-level and date-level denial in the style of the V2 harness
``s1_denied``, plus the sealed-reader guarantees.  ALL fixtures here are
synthetic (tmp_path payloads and synthetic paths); no real S1 data is ever
opened by this suite.  A recording-open test proves the lane's reader never
even opens an S1-shaped path.
"""

from __future__ import annotations

import builtins
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.stocks_free_v3.authority import (
    S0_END,
    S0_START,
    S1_END,
    S1_START,
    SNAPSHOT_PINS,
    WARMUP_END,
    WARMUP_START,
)
from research.stocks_free_v3.isolation import (
    S0WindowPolicy,
    S1Seal,
    S1SealError,
    SealedSnapshotReader,
)


@pytest.fixture()
def seal() -> S1Seal:
    return S1Seal(S1_START, S1_END)


@pytest.fixture()
def policy() -> S0WindowPolicy:
    return S0WindowPolicy()


# --- date-level denial ------------------------------------------------------------ #


def test_every_s1_date_denied_every_s0_date_allowed(seal: S1Seal) -> None:
    day = date(2018, 1, 1)
    last = date(2026, 12, 31)
    while day <= last:
        if S1_START <= day <= S1_END:
            assert seal.denies_date(day), f"S1 date {day} must be denied"
        else:
            assert not seal.denies_date(day), f"non-S1 date {day} must be allowed"
        day += timedelta(days=1)


def test_s1_boundaries_are_exact(seal: S1Seal) -> None:
    assert not seal.denies_date(S0_END)  # 2025-07-31: last S0 day, allowed
    assert seal.denies_date(S1_START)  # 2025-08-01: first sealed day
    assert seal.denies_date(S1_END)  # 2026-07-31: last sealed day
    assert not seal.denies_date(date(2026, 8, 1))  # after the seal ends


def test_require_unsealed_date_raises_with_reason(seal: S1Seal) -> None:
    with pytest.raises(S1SealError, match="2025-12-05"):
        seal.require_unsealed_date(date(2025, 12, 5))


def test_seal_rejects_inverted_window() -> None:
    with pytest.raises(ValueError):
        S1Seal(date(2026, 7, 31), date(2025, 8, 1))


# --- path-level denial ------------------------------------------------------------ #


@pytest.mark.parametrize(
    "path",
    [
        "data/s1/SPY.json",
        "data/S1/SPY.json",
        "/abs/root/s1/x.parquet",
        "s1",
        "runs/s1.parquet",  # sealed 's1.'-prefixed segment
        "s1_SPY_2025.json",
        "s1-SPY.json",
        "out/s1_/x.csv",  # sealed 's1_'-prefixed segment
        "notes/s1_study.md",  # filename carries the sealed 's1_' prefix
        "snapshots/2025-08/SPY_none.json",  # sealed month token
        "snapshots/2025-12/XLK.json",  # sealed month token (split month)
        "snapshots/2026-07/SPY_none.json",  # last sealed month
        "bars/2025-08-01.json",  # first sealed date
        "bars/2025-12-05.json",  # split provenance date inside S1
        "bars/2026-07-31.json",  # last sealed date
        "bars/20250801.dat",  # compact sealed date
        "bars/20260731.dat",
        "C:\\data\\s1\\SPY.json",  # windows separators normalized
    ],
)
def test_s1_shaped_paths_denied(seal: S1Seal, path: str) -> None:
    reason = seal.denies_path(path)
    assert reason is not None, f"{path} must be denied"
    with pytest.raises(S1SealError):
        seal.check_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "SPY_none_p1.json",
        "data/SPY_none_p1.json",
        "bars/2018-04-04.json",  # S0 start
        "bars/2025-07-31.json",  # S0 end
        "bars/2024-12-31.json",
        "data/s10/bars.parquet",  # 's10' is not the 's1' segment
        "data/s0/SPY.json",
        "runs/2025-07/month.parquet",  # month token 2025-07 is S0, allowed
        "bars/2026-08-27.json",  # after the seal
        "notes/study_s1.md",  # 's1' inside the filename body is not a marker
    ],
)
def test_non_s1_paths_allowed(seal: S1Seal, path: str) -> None:
    assert seal.denies_path(path) is None, f"{path} must be readable"


# --- S0 window policy -------------------------------------------------------------- #


def test_s0_window_allows_full_s0_and_rejects_around_it(policy: S0WindowPolicy) -> None:
    assert policy.allows_window(S0_START, S0_END)
    assert policy.allows_window(date(2018, 4, 4), date(2018, 4, 4))
    assert policy.allows_window(date(2025, 7, 31), date(2025, 7, 31))
    assert not policy.allows_window(date(2025, 7, 31), S1_START)  # touches S1
    assert not policy.allows_window(S1_START, S1_END)
    assert not policy.allows_window(date(2018, 1, 2), WARMUP_END)  # warmup is not S0
    assert not policy.allows_window(date(2017, 1, 1), date(2018, 1, 2))
    assert not policy.allows_window(S0_END, date(2026, 8, 27))


def test_warmup_is_not_s1_but_not_s0_either(seal: S1Seal, policy: S0WindowPolicy) -> None:
    """Warmup dates are unsealed (not S1) yet not valid S0 read windows."""
    assert not seal.denies_date(WARMUP_START)
    assert not policy.allows_window(WARMUP_START, WARMUP_END)


def test_require_s0_window_raises(policy: S0WindowPolicy) -> None:
    with pytest.raises(S1SealError, match="not fully inside S0"):
        policy.require_s0_window(date(2025, 7, 1), date(2025, 8, 1))


# --- sealed reader over synthetic fixtures ------------------------------------------ #


def _synthetic_symbol_file(
    tmp_path: Path, name: str, rows: list[dict[str, object]]
) -> str:
    payload = {
        "meta": {
            "symbol": name.split("_", 1)[0],
            "interval": "1day",
            "currency": "USD",
            "exchange": "NYSE",
            "mic_code": "ARCX",
        },
        "status": "ok",
        "values": rows,
    }
    text = json.dumps(payload)
    (tmp_path / name).write_text(text, encoding="utf-8")
    return name


@pytest.fixture()
def synthetic_snapshot(tmp_path: Path):
    """A snapshot file that contains BOTH S0 rows and sealed S1 rows."""
    rows = [
        {"datetime": "2025-08-01", "open": "9", "high": "9", "low": "9", "close": "9", "volume": "1"},
        {"datetime": "2025-07-31", "open": "8", "high": "8", "low": "8", "close": "8", "volume": "1"},
        {"datetime": "2025-07-30", "open": "7", "high": "7", "low": "7", "close": "7", "volume": "1"},
        {"datetime": "2018-04-04", "open": "1", "high": "1", "low": "1", "close": "1", "volume": "1"},
    ]
    name = "FAKE_none_p1.json"
    text = json.dumps({"meta": {"symbol": "FAKE", "interval": "1day", "currency": "USD", "exchange": "NYSE", "mic_code": "ARCX"}, "status": "ok", "values": rows})
    (tmp_path / name).write_text(text, encoding="utf-8")
    import research.stocks_free_v3.isolation as isolation

    saved = dict(isolation.SNAPSHOT_PINS)
    isolation.SNAPSHOT_PINS[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    yield tmp_path, name
    isolation.SNAPSHOT_PINS.clear()
    isolation.SNAPSHOT_PINS.update(saved)


def _reader(root: Path) -> SealedSnapshotReader:
    return SealedSnapshotReader(
        root, seal=S1Seal(S1_START, S1_END), policy=S0WindowPolicy()
    )


def test_reader_truncates_s1_rows_from_a_shared_file(synthetic_snapshot) -> None:
    root, name = synthetic_snapshot
    loaded = _reader(root).load_symbol_file(
        name, start=date(2018, 4, 4), end=S0_END
    )
    returned_dates = [row["datetime"] for row in loaded["values"]]
    assert returned_dates == ["2018-04-04", "2025-07-30", "2025-07-31"]
    assert "2025-08-01" not in returned_dates  # sealed row never surfaces


def test_reader_closes_mapping_is_s0_only_and_sorted(synthetic_snapshot) -> None:
    root, name = synthetic_snapshot
    closes = _reader(root).load_symbol_closes(name, start=date(2018, 4, 4), end=S0_END)
    assert list(closes) == ["2018-04-04", "2025-07-30", "2025-07-31"]
    assert set(closes) == {"2018-04-04", "2025-07-30", "2025-07-31"}


def test_reader_refuses_window_touching_s1(synthetic_snapshot) -> None:
    root, name = synthetic_snapshot
    reader = _reader(root)
    with pytest.raises(S1SealError):
        reader.load_symbol_file(name, start=date(2025, 7, 1), end=date(2025, 8, 1))


def test_reader_refuses_s1_shaped_path(tmp_path: Path) -> None:
    reader = _reader(tmp_path)
    with pytest.raises(S1SealError):
        reader.resolve("nested/s1/SPY.json")


def test_reader_refuses_unpinned_file(tmp_path: Path) -> None:
    (tmp_path / "UNPINNED.json").write_text("{}", encoding="utf-8")
    reader = _reader(tmp_path)
    with pytest.raises(S1SealError, match="unpinned"):
        reader.load_symbol_file("UNPINNED.json", start=S0_START, end=S0_END)


def test_reader_refuses_tampered_file(synthetic_snapshot) -> None:
    root, name = synthetic_snapshot
    (root / name).write_text("{}", encoding="utf-8")  # tamper after pinning
    with pytest.raises(S1SealError, match="checksum mismatch"):
        _reader(root).load_symbol_file(name, start=S0_START, end=S0_END)


def test_reader_refuses_root_escape(tmp_path: Path) -> None:
    reader = _reader(tmp_path)
    with pytest.raises(S1SealError, match="escape"):
        reader.resolve("../outside.json")


def test_reader_requires_existing_root(tmp_path: Path) -> None:
    with pytest.raises(S1SealError):
        _reader(tmp_path / "does_not_exist")


def test_reader_provenance_closes_restricted(synthetic_snapshot) -> None:
    """Provenance closes exist ONLY for split symbols at the pinned dates."""
    root, name = synthetic_snapshot
    reader = _reader(root)
    with pytest.raises(S1SealError, match="split symbols"):
        reader.read_provenance_closes(name)  # FAKE is not a split symbol


def test_provenance_dates_are_the_pinned_pair_only(synthetic_snapshot) -> None:
    root, name = synthetic_snapshot
    with pytest.raises(S1SealError, match="restricted"):
        _reader(root).read_provenance_closes(name, dates=("2025-08-01",))


# --- the lane never even OPENS an S1-shaped path ------------------------------------- #


def test_lane_filesystem_reads_never_touch_s1_paths(
    synthetic_snapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Record every builtin-open target made through the reader; assert that
    none of them is an S1-shaped path, even when S1-shaped files sit nearby."""
    root, name = synthetic_snapshot
    (root / "s1" / "SPY_2025-08.json").parent.mkdir(exist_ok=True)
    (root / "s1" / "SPY_2025-08.json").write_text("{}", encoding="utf-8")
    (root / "s1_SPY.json").write_text("{}", encoding="utf-8")

    opened: list[str] = []
    real_open = builtins.open

    def recording_open(file, mode="r", *args, **kwargs):  # type: ignore[no-untyped-def]
        opened.append(str(file))
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", recording_open)
    reader = _reader(root)
    seal = S1Seal(S1_START, S1_END)
    reader.load_symbol_file(name, start=S0_START, end=S0_END)
    reader.load_symbol_closes(name, start=S0_START, end=S0_END)
    monkeypatch.undo()

    assert opened, "the reader must have opened the pinned file"
    for target in opened:
        assert seal.denies_path(target) is None, (
            f"lane opened an S1-shaped path: {target}"
        )
    assert not any("s1" in Path(t).parts or Path(t).name.startswith("s1_") for t in opened)


def test_seal_digest_is_stable(seal: S1Seal) -> None:
    assert seal.definition_digest() == seal.definition_digest()
    assert len(seal.definition_digest()) == 64
