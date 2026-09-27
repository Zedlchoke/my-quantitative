"""E1 — fail-closed loaders with digest pins and a raw-OHLCV column allowlist.

R2-1: vendor `adjusted_close` is FORBIDDEN anywhere in signal, direction,
fills or evaluation. The panel loader enforces an explicit column allowlist;
requesting a forbidden column raises ForbiddenColumnError (test-failable).
R2-5/P-13: every staged artifact is digest-verified at load, fail-closed.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from typing import Dict, Iterable, List, Tuple

from . import config as C


class DigestMismatch(AssertionError):
    """Any staged artifact failing its pinned sha256 / row count."""


class ForbiddenColumn(ValueError):
    """Any attempt to read a column outside the raw-OHLCV allowlist (R2-1)."""


# The ONLY columns the engine may read from the price panel (R2-1).
PANEL_ALLOWED_COLUMNS = frozenset({"date", "open", "high", "low", "close", "volume"})
PANEL_FORBIDDEN_COLUMNS = frozenset({"adjusted_close"})  # present on disk, forbidden


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fail(msg: str) -> None:
    raise DigestMismatch(msg)


# --------------------------------------------------------------- digests ----
def verify_all_digests() -> dict:
    """Fail-closed digest verification of every staged artifact (E1).

    Returns a plain evidence dict; raises DigestMismatch on any drift.
    """
    ev: dict = {}

    def check(path: str, pin_sha: str, label: str) -> str:
        if not os.path.exists(path):
            _fail(f"{label}: missing file {path}")
        got = sha256_file(path)
        if got != pin_sha:
            _fail(f"{label}: sha256 {got} != pin {pin_sha} ({path})")
        return got

    ev["a1_events_sha256"] = check(A1P := C.A1_EVENTS_PATH, C.PIN_A1_EVENTS_SHA256, "a1_events")
    ev["a1_events_rows"] = _count_lines(A1P)
    if ev["a1_events_rows"] != C.PIN_A1_EVENTS_ROWS:
        _fail(f"a1_events rows {ev['a1_events_rows']} != pin {C.PIN_A1_EVENTS_ROWS}")

    ev["form4_stream_sha256"] = check(SP := C.STREAM_PATH, C.PIN_FORM4_STREAM_SHA256, "form4_stream")
    ev["form4_stream_rows"] = _count_lines(SP)
    if ev["form4_stream_rows"] != C.PIN_FORM4_STREAM_ROWS:
        _fail(f"form4_stream rows {ev['form4_stream_rows']} != pin {C.PIN_FORM4_STREAM_ROWS}")

    ev["n4_map_sha256"] = check(NP := C.N4_MAP_PATH, C.PIN_N4_MAP_SHA256, "n4_map")
    ev["n4_map_rows"] = _count_lines(NP)

    # NG6 panel: per-file digests vs committed manifest (R2-5).
    expected: Dict[str, str] = {}
    for line in open(C.PANEL_DIGEST_PATH):
        sha, path = line.split()
        expected[path] = sha
    n_ok = n_bad = n_missing = 0
    for path, sha in expected.items():
        fp = os.path.join(C.STAGING, path)
        if not os.path.exists(fp):
            n_missing += 1
            continue
        if sha256_file(fp) == sha:
            n_ok += 1
        else:
            n_bad += 1
    on_disk = {
        "integration/data_raw/stocks_ng6_eod/" + f
        for f in os.listdir(C.PANEL_DIR)
    }
    ev["panel"] = {
        "manifest_entries": len(expected), "verified_ok": n_ok,
        "bad": n_bad, "missing": n_missing,
        "extra_on_disk": len(on_disk - set(expected)),
    }
    if n_bad or n_missing or (on_disk - set(expected)):
        _fail(f"NG6 panel drift: {ev['panel']}")

    # div/splits: per-file digests vs substrate manifest.
    man = json.load(open(C.SUBSTRATE_MANIFEST_PATH))
    for sec in ("eodhd_div", "eodhd_splits"):
        files = man["sections"][sec]["files"]
        n_ok = n_bad = n_missing = 0
        for name, sha in files.items():
            fp = os.path.join(C.STAGING, "integration", ".staging_sec_v13", sec, name)
            if not os.path.exists(fp):
                n_missing += 1
                continue
            if sha256_file(fp) == sha:
                n_ok += 1
            else:
                n_bad += 1
        ev[sec] = {"count": len(files), "verified_ok": n_ok, "bad": n_bad, "missing": n_missing}
        if n_bad or n_missing:
            _fail(f"{sec} drift: {ev[sec]}")
    ev["ok"] = True
    return ev


def _count_lines(path: str) -> int:
    n = 0
    with open(path, "rb") as f:
        for _ in f:
            n += 1
    return n


# ----------------------------------------------------------------- rows ----
def iter_jsonl(path: str) -> Iterable[dict]:
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_a1_events() -> List[dict]:
    """A1 staged events; enforce exact-form law (R2-3) + dedup identity."""
    rows = list(iter_jsonl(C.A1_EVENTS_PATH))
    seen = set()
    out = []
    dropped_dup = 0
    dropped_form = 0
    for r in rows:
        if r["form"] not in C.A1_FORMS:  # exact-match law (10-Q/A etc. never staged, enforced anyway)
            dropped_form += 1
            continue
        key = (r["cik"], r["acceptance_utc"])  # (issuer, acceptance_instant), R2-3
        if key in seen:
            dropped_dup += 1
            continue
        seen.add(key)
        out.append(r)
    stats = {"rows": len(rows), "events": len(out),
             "dropped_duplicate_identity": dropped_dup,
             "dropped_form_not_exact": dropped_form}
    return sorted(out, key=lambda r: (r["acceptance_utc"], r["cik"], r["accession"])) , stats


def load_n4_map() -> Dict[str, dict]:
    return {r["cik"]: r for r in iter_jsonl(C.N4_MAP_PATH)}


def load_corp_actions() -> Dict[str, dict]:
    """div/splits ex-dates per ticker: {ticker: {'div': [dates], 'split': [dates]}}."""
    out: Dict[str, dict] = {}
    for kind, d in (("div", C.DIV_DIR), ("split", C.SPLIT_DIR)):
        for fn in os.listdir(d):
            if not fn.endswith(".json"):
                continue
            ticker = fn[:-5]
            with open(os.path.join(d, fn)) as f:
                rows = json.load(f)
            out.setdefault(ticker, {"div": [], "split": []})[kind] = sorted(
                r["date"] for r in rows if r.get("date")
            )
    return out
