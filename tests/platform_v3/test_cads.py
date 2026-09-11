"""V3 CADS tests (plan section 7A.1 + PA2 acceptance)."""

import threading

import pytest

from research.platform_v3.cads import (
    CADS,
    CADSError,
    CADSIntegrityError,
    ControlStateDrift,
)


def test_register_idempotent(tmp_path):
    store = CADS(str(tmp_path / "store"))
    a1 = store.register(b"hello")
    a2 = store.register(b"hello")
    assert a1 == a2
    assert len([e for e in store.events() if e["event"] == "REGISTER"]) == 1
    assert store.verify(a1) == "PRESENT_VERIFIED"


def test_resolve_verifies_every_time(tmp_path):
    store = CADS(str(tmp_path / "store"))
    a = store.register(b"x" * 1000)
    assert store.resolve(a) == b"x" * 1000


def test_corruption_detected_fail_closed(tmp_path):
    store = CADS(str(tmp_path / "store"))
    a = store.register(b"payload")
    obj = store._object_path(a)
    with open(obj, "wb") as fh:
        fh.write(b"PAYLOAD")  # corrupt in place
    assert store.verify(a) == "PRESENT_CORRUPT"
    with pytest.raises(CADSIntegrityError):
        store.resolve(a)


def test_restore_from_backup(tmp_path):
    store = CADS(str(tmp_path / "store"))
    a = store.register(b"restore-me")
    backup = tmp_path / "backup.bin"
    backup.write_bytes(b"restore-me")
    obj = store._object_path(a)
    with open(obj, "wb") as fh:
        fh.write(b"corrupted!")
    store.restore(a, str(backup))
    assert store.resolve(a) == b"restore-me"


def test_restore_refuses_mismatched_backup(tmp_path):
    store = CADS(str(tmp_path / "store"))
    a = store.register(b"true-bytes")
    backup = tmp_path / "wrong.bin"
    backup.write_bytes(b"wrong-bytes")
    with pytest.raises(CADSIntegrityError):
        store.restore(a, str(backup))


def test_concurrent_register_same_bytes(tmp_path):
    store = CADS(str(tmp_path / "store"))
    results = []
    errors = []

    def worker():
        try:
            results.append(store.register(b"shared-bytes"))
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(set(results)) == 1  # one address, idempotent
    assert store.verify(results[0]) == "PRESENT_VERIFIED"


def test_malformed_journal_is_control_state_drift(tmp_path):
    store = CADS(str(tmp_path / "store"))
    store.register(b"a")
    with open(store.events_path, "a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    with pytest.raises(ControlStateDrift):
        store.events()


def test_pin_absent_object_refused(tmp_path):
    store = CADS(str(tmp_path / "store"))
    with pytest.raises(CADSError):
        store.pin("a" * 64, {"series": "s"})


def test_address_malformed_refused(tmp_path):
    store = CADS(str(tmp_path / "store"))
    with pytest.raises(CADSError):
        store.resolve("not-an-address")
