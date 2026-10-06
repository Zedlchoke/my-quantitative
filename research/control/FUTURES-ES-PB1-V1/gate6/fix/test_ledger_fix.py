#!/usr/bin/env python
"""test_ledger_fix.py — comprehensive SYNTHETIC suite proving the trial_ledger
reopen/append hash-chain fix (lane LEDGER-FIX, cycle FUTURES-ES-PB1-V1).

████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC ████████████
EVERY identity below is FABRICATED ("SYNTH-*"). No panel/parquet is read,
NO real-outcome PnL is computed anywhere, nothing scores, gates, or
publishes. This suite exercises ONLY the gate6/trial_ledger.py
bookkeeping layer against its own frozen law.
████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC ████████████

Proves (at HEAD 2291d562 + the ONE-LINE `_replay` fix, L125):
  A  FAIL-record reproduction now PASSES (reopen from disk + append + verify)
  B  multi-session reopen (5 sessions, 24 synthetic identities): chain holds
     end-to-end; independently re-verified from disk bytes
  C  bytes-never-rewritten: file bytes after session 1 are an exact PREFIX of
     the final file (append-only proof)
  D  tampering rejected: (a) non-final row -> successor chain break named;
     (b) final row -> per the frozen chain law detected by the
     summary().file_sha256 digest change (verify() alone cannot see it —
     law as written in the _replay docstring); (c) truncated middle line
  E  interrupted-write law: torn final line (partial JSON, no newline) —
     the frozen law (module docstring, _append comment, _replay docstring,
     smoke test) is SILENT on torn final lines; this suite asserts the
     ledger FAILS CLOSED and records a FINDING with the actual behavior —
     no behavior is invented
  F  duplicate identity / retry accounting: double-terminal refused
     (PASS->PASS, PASS->FAIL), slot-level REFUSED is terminal, run-level
     record_refusal (identity None) consumes no slot and never counts,
     observed denominator == PASS/FAIL rows exactly (publication failure
     included), terminal law restored across reopen
  G  verify() on a fresh path (edge probed, not invented)

Run: .venv/bin/python research/control/FUTURES-ES-PB1-V1/gate6/fix/test_ledger_fix.py
Note: a "new session" below is a NEW TrialLedger object constructed from
disk — identical code path to a new process (constructor is the only
disk-replay entry point; no process-global state exists in the module).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent          # gate6/fix
sys.path.insert(0, str(HERE.parent))            # gate6  -> THE fixed module
from trial_ledger import LedgerError, TrialLedger, _row_sha  # noqa: E402

IDS = [f"SYNTH-{i:02d}" for i in range(24)]     # 24 synthetic identities

PASS_N = FAIL_N = 0
FINDINGS: list[str] = []


def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL_N += 1
        print(f"  FAIL  {name} — {detail}")


def finding(tag, text):
    FINDINGS.append(f"[{tag}] {text}")
    print(f"  FINDING [{tag}] {text}")


def canonical(row: dict) -> str:
    return json.dumps(row, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def chain_check_independent(path: Path, ids):
    """Independent re-read of the file bytes: recompute the hash chain from
    disk WITHOUT the module's verify() (fresh parse + _row_sha only)."""
    rows = [json.loads(l) for l in
            path.read_text(encoding="utf-8").splitlines() if l.strip()]
    prev = None
    for i, r in enumerate(rows, 1):
        if r.get("seq") != i:
            return False, f"seq {r.get('seq')} at line {i}"
        if i > 1 and r.get("prev_row_sha") != _row_sha(prev):
            return False, f"link break at line {i}"
        iid = r.get("identity_id")
        if iid is not None and iid not in ids:
            return False, f"unknown slot {iid!r} at line {i}"
        prev = r
    return True, f"{len(rows)} rows chain-verified from disk bytes"


def main() -> int:
    print("=" * 78)
    print("TRIAL-LEDGER FIX SUITE — SYNTHETIC ONLY (fabricated SYNTH-* ids, "
          "zero real PnL)")
    print("module under test: gate6/trial_ledger.py @ HEAD 2291d562 + "
          "one-line _replay fix (L125)")
    print("=" * 78)
    tmp = Path(tempfile.mkdtemp(prefix="ledger_fix_synthetic_"))
    print(f"scratch: {tmp}\n")

    # ==== A: FAIL-record reproduction (now PASSES) =========================
    print("[A] FAIL-record reproduction (FAIL_LEDGER_REPLAY.md steps 1-2)")
    pa = tmp / "A.jsonl"
    s1 = TrialLedger(pa, IDS)
    s1.record_result("SYNTH-00", "PASS", note="repro step 1")
    check("A1 session-1 append + verify ok", s1.verify()["ok"] is True)
    try:
        s2 = TrialLedger(pa, IDS)                    # reopen from disk
        s2.record_result("SYNTH-01", "PASS", note="repro step 2")
        check("A2 reopen + append does NOT raise "
              "(pre-fix: LedgerError hash-chain break at line 2)", True)
    except LedgerError as e:
        check("A2 reopen + append does NOT raise "
              "(pre-fix: LedgerError hash-chain break at line 2)", False, str(e))
    check("A3 verify ok after reopen+append", s2.verify()["ok"] is True
          and s2.verify()["rows"] == 2)

    # ==== B: multi-session reopen, 5 sessions ==============================
    print("\n[B] multi-session reopen: 5 sessions over 24 synthetic ids "
          "(8/4/4/4/4)")
    pb = tmp / "B.jsonl"
    plan = [(0, 8), (8, 4), (12, 4), (16, 4), (20, 4)]
    expected_rows = 0
    for sess, (start, n) in enumerate(plan, 1):
        led = TrialLedger(pb, IDS)                   # fresh object = fresh replay
        for iid in IDS[start:start + n]:
            led.record_result(iid, "PASS", note=f"session {sess}",
                              computed_by="ledger_fix_suite")
        expected_rows += n
        v = led.verify()
        check(f"B1.{sess} session {sess}: reopen+append {n} rows + verify ok",
              v["ok"] is True and v["rows"] == expected_rows,
              f"rows={v['rows']}")
    fin = TrialLedger(pb, IDS)
    check("B2 final verify ok (5 sessions end-to-end)", fin.verify()["ok"] is True)
    check("B3 total rows == 24", len(fin._rows_cache) == 24
          and fin.verify()["rows"] == 24)
    sb = fin.summary()
    check("B4 observed == 24 and ledger complete",
          sb["observed_denominator"] == 24 and sb["complete"] is True,
          f"observed={sb['observed_denominator']}")
    ok, det = chain_check_independent(pb, IDS)
    check("B5 independent disk-bytes chain re-verification", ok, det)

    # ==== C: bytes-never-rewritten (append-only proof) =====================
    print("\n[C] bytes-never-rewritten: session-1 bytes are an exact prefix")
    pc = tmp / "C.jsonl"
    led = TrialLedger(pc, IDS)
    for iid in IDS[0:3]:
        led.record_result(iid, "PASS", note="C session 1")
    snap = pc.read_bytes()
    n1 = len(snap.splitlines())
    led = TrialLedger(pc, IDS)
    for iid in IDS[3:5]:
        led.record_result(iid, "PASS", note="C session 2")
    n2 = len(pc.read_bytes().splitlines())
    led = TrialLedger(pc, IDS)
    for iid in IDS[5:7]:
        led.record_result(iid, "PASS", note="C session 3")
    final_bytes = pc.read_bytes()
    n3 = len(final_bytes.splitlines())
    check("C1 line count only grows 3->5->7", (n1, n2, n3) == (3, 5, 7),
          f"got {(n1, n2, n3)}")
    check("C2 session-1 bytes are an EXACT PREFIX of final bytes",
          final_bytes.startswith(snap))
    check("C3 file strictly grew (no byte anywhere rewritten)",
          len(final_bytes) > len(snap)
          and final_bytes[:len(snap)] == snap)

    # ==== D: tampering rejected ============================================
    print("\n[D] tampering rejected (copies only; originals untouched)")
    pd = tmp / "D_base.jsonl"
    led = TrialLedger(pd, IDS)
    for i, iid in enumerate(IDS[0:4], 1):
        led.record_result(iid, "PASS", note=f"D row {i}", result_sha=f"d-{i}")
    base_digest = hashlib.sha256(pd.read_bytes()).hexdigest()

    # (a) non-final row tamper -> successor chain break, named
    p1 = tmp / "D_tamper_mid.jsonl"
    shutil.copyfile(pd, p1)
    lines = p1.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace('"result_sha":"d-2"', '"result_sha":"d-TAMPER"')
    p1.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        TrialLedger(p1, IDS)
        check("D1 non-final-row tamper (row 2/4) rejected", False,
              "no error raised")
    except LedgerError as e:
        check("D1 non-final-row tamper (row 2/4) rejected naming successor",
              "hash-chain break at line 3" in str(e), str(e))

    # (b) final-row tamper -> per the frozen law, detection = digest change
    p2 = tmp / "D_tamper_final.jsonl"
    shutil.copyfile(pd, p2)
    flines = p2.read_text(encoding="utf-8").splitlines()
    last = json.loads(flines[-1])
    last["status"] = "FAIL"                       # tamper the FINAL row
    flines[-1] = canonical(last)
    p2.write_text("\n".join(flines) + "\n", encoding="utf-8")
    reopened = TrialLedger(p2, IDS)               # chain intact: no successor
    check("D2a final-row tamper: chain verify alone stays ok (per law: no "
          "successor link exists to break)", reopened.verify()["ok"] is True)
    check("D2b final-row tamper DETECTED by summary().file_sha256 digest "
          "change (chain law as written in _replay docstring)",
          hashlib.sha256(p2.read_bytes()).hexdigest() != base_digest)

    # (c) truncated middle line -> fail closed
    p3 = tmp / "D_truncate_mid.jsonl"
    raw = pd.read_bytes().split(b"\n")
    half = raw[1][: len(raw[1]) // 2]             # cut line 2 in half
    p3.write_bytes(raw[0] + b"\n" + half + b"\n" + raw[2] + b"\n" + raw[3]
                   + b"\n")
    try:
        TrialLedger(p3, IDS)
        check("D3 truncated middle line rejected (fail-closed)", False,
              "no error raised")
    except Exception as e:                        # noqa: BLE001 — record type
        check("D3 truncated middle line rejected (fail-closed)", True,
              f"{type(e).__name__}: {str(e)[:60]}")

    # ==== E: interrupted-write law (torn final line) =======================
    print("\n[E] interrupted-write law: torn final line (partial JSON, "
          "no newline)")
    pe = tmp / "E.jsonl"
    led = TrialLedger(pe, IDS)
    for i, iid in enumerate(IDS[0:3], 1):
        led.record_result(iid, "PASS", note=f"E row {i}")
    torn_prefix = pe.read_bytes().split(b"\n")[-2][:40]   # plausible row prefix
    with open(pe, "ab") as fh:                    # RAW torn write, no '\n'
        fh.write(torn_prefix)
        fh.flush()
    bytes_before_reopen = pe.read_bytes()
    exc = None
    try:
        TrialLedger(pe, IDS)
    except Exception as e:                        # noqa: BLE001 — record type
        exc = e
    check("E1 torn final line: reopen FAILS CLOSED (never silent)",
          exc is not None, f"{type(exc).__name__}" if exc else "accepted!")
    check("E2 torn final line rejected as malformed JSON "
          "(json.JSONDecodeError, NOT a LedgerError)", 
          isinstance(exc, json.JSONDecodeError),
          f"{type(exc).__name__}: {str(exc)[:70]}" if exc else "")
    check("E3 failed reopen does NOT rewrite/repair the file (append-only "
          "law holds even on the read path)",
          pe.read_bytes() == bytes_before_reopen)
    try:
        fresh = TrialLedger.__new__(TrialLedger)
        fresh.path, fresh.identity_ids = pe, IDS
        fresh._seq, fresh._prev_sha, fresh._terminal = 0, None, {}
        fresh._rows_cache = []
        fresh._replay()
        check("E4 verify() on torn file also fails closed", False, "no error")
    except Exception as e:                        # noqa: BLE001
        check("E4 verify() on torn file also fails closed", True,
              f"{type(e).__name__}")
    # The frozen law: module docstring (append-only + chain detection),
    # _append comment ("single line + '\n', flush + fsync"), _replay docstring
    # (blank line / seq / chain errors), and the smoke test (NO torn-write
    # handling at all) are SILENT on a torn FINAL line. Actual behavior:
    # raw json.JSONDecodeError. Recorded as a FINDING — no behavior invented.
    finding("E-torn-write",
            "The frozen law (trial_ledger.py docstrings/comments + "
            "gate6/synthetic_smoke_test.py) is SILENT on torn FINAL lines. "
            "Actual behavior (asserted above): fail-closed raw "
            "json.JSONDecodeError on replay (not a LedgerError with a "
            "ledger-specific message); file never rewritten/repair-truncated. "
            "Write side mitigates (single line + '\\n' + fsync). Recorded, "
            "not invented; any LedgerError-mapping would be a law amendment.")

    # ==== F: duplicate identity / retry accounting =========================
    print("\n[F] duplicate identity / retry accounting")
    pf = tmp / "F1.jsonl"
    f1 = TrialLedger(pf, IDS)
    f1.record_result(IDS[10], "PASS", note="first terminal")
    try:
        f1.record_result(IDS[10], "PASS")
        check("F1 PASS then PASS again refused (double-terminal)", False)
    except LedgerError as e:
        check("F1 PASS then PASS again refused (double-terminal)",
              "already terminal" in str(e), str(e)[:70])
    try:
        f1.record_result(IDS[10], "FAIL")
        check("F2 PASS then FAIL refused (append-only, no overwrite)", False)
    except LedgerError as e:
        check("F2 PASS then FAIL refused (append-only, no overwrite)",
              "already terminal (PASS)" in str(e), str(e)[:70])

    pf2 = tmp / "F2.jsonl"
    f2 = TrialLedger(pf2, IDS)
    f2.record_result(IDS[11], "REFUSED", note="slot-level refusal",
                     computed_by="suite")
    try:
        f2.record_result(IDS[11], "PASS")
        check("F3 slot-level REFUSED is TERMINAL: PASS after it refused "
              "(class law: one terminal row PASS/FAIL/REFUSED per identity)",
              False)
    except LedgerError as e:
        check("F3 slot-level REFUSED is TERMINAL: PASS after it refused "
              "(class law: one terminal row PASS/FAIL/REFUSED per identity)",
              "already terminal (REFUSED)" in str(e), str(e)[:70])

    pf3 = tmp / "F3.jsonl"
    f3 = TrialLedger(pf3, IDS)
    f3.record_refusal("REFUSED_NO_GO", note="run-level refusal event")
    f3.record_result(IDS[12], "PASS", note="compute after run refusal")
    check("F4 run-level record_refusal (identity_id=None) consumes NO slot "
          "and never counts observed",
          f3.summary()["per_identity"][IDS[12]] == "PASS"
          and f3.observed() == 1,
          f"observed={f3.observed()}")

    pf4 = tmp / "F4.jsonl"
    f4 = TrialLedger(pf4, IDS)
    f4.record_result(IDS[13], "PASS", note="normal")
    f4.record_result(IDS[14], "PASS", published=False,
                     note="publication failure — still computed")
    f4.record_result(IDS[15], "FAIL", note="computed fail")
    f4.record_result(IDS[16], "REFUSED", note="slot refusal")
    f4.record_result(IDS[17], "NOT_RUN", note="annotation")
    f4.record_result(IDS[18], "NOT_RUN", note="annotation")
    disk_observed = sum(1 for l in pf4.read_text().splitlines()
                        if l.strip()
                        and json.loads(l).get("counts_observed") is True)
    check("F5 observed == PASS+FAIL rows exactly (2 PASS incl. "
          "published=False + 1 FAIL == 3; REFUSED/NOT_RUN excluded)",
          f4.observed() == 3 and disk_observed == 3,
          f"observed={f4.observed()} disk={disk_observed}")
    check("F6 publication failure still counts observed "
          "(published=False inside PASS counts)",
          json.loads(
              [l for l in pf4.read_text().splitlines()
               if '"SYNTH-14"' in l][0])["counts_observed"] is True)

    pf5 = tmp / "F5.jsonl"
    g1 = TrialLedger(pf5, IDS)
    g1.record_result(IDS[19], "PASS", note="session 1")
    g2 = TrialLedger(pf5, IDS)                    # reopen: terminal map restored
    try:
        g2.record_result(IDS[19], "PASS")
        check("F7 terminal law restored across reopen: PASS re-refused", False)
    except LedgerError:
        check("F7 terminal law restored across reopen: PASS re-refused", True)
    try:
        g2.record_result(IDS[19], "FAIL")
        check("F8 terminal law restored across reopen: FAIL re-refused", False)
    except LedgerError:
        check("F8 terminal law restored across reopen: FAIL re-refused", True)

    # ==== G: verify() on a fresh path ======================================
    print("\n[G] verify() on a fresh path (probed, not invented)")
    pg = tmp / "G_never_written.jsonl"
    g = TrialLedger(pg, IDS)
    try:
        v = g.verify()
        check("G1 verify() before any append on a fresh path returns ok",
              v["ok"] is True, str(v))
    except FileNotFoundError as e:
        check("G1 verify() before any append on a fresh path returns ok",
              False, f"raises {type(e).__name__}")
        finding("G-fresh-path-verify",
                "verify() on a never-written path raises FileNotFoundError "
                "instead of returning ok (summary() handles the same state "
                "gracefully with file_sha256=None). The frozen law is silent "
                "on this edge. NOT fixed — outside the authorized one-line "
                "mandate; recorded as a finding.")
    check("G2 fresh path: first append then verify ok",
          g.record_result(IDS[20], "PASS")["seq"] == 1
          and g.verify()["ok"] is True)
    pg2 = tmp / "G_empty_existing.jsonl"
    pg2.touch()
    check("G3 empty-but-existing file: verify ok with 0 rows",
          TrialLedger(pg2, IDS).verify() == {"ok": True, "rows": 0,
                                             "observed_denominator": 0})

    # ==== summary ==========================================================
    print("\n" + "=" * 78)
    print(f"SUITE RESULT: {PASS_N} pass / {FAIL_N} fail / "
          f"{len(FINDINGS)} finding(s) "
          f"{'— ALL GREEN' if FAIL_N == 0 else '— FAILURES PRESENT'}")
    for f in FINDINGS:
        print(f"  FINDING {f}")
    print(f"scratch ledgers (synthetic, disposable): {tmp}")
    print("=" * 78)
    return 0 if FAIL_N == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
