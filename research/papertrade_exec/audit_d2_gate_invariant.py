#!/usr/bin/env python3
"""SPEC D2 — MUC 6 AUDIT SCRIPT (forward judgment; sha256 spec 06e204d2…).

Chay hang tuan boi coordinator (14 ngay dau sau T0; hang thang sau do):

    python -m research.papertrade_exec.audit_d2_gate_invariant \
        --data-root ~/.my-quantitative-data/sports-papertrade-exec-v1 \
        --t0 2026-10-26T00:00:00Z

Luat (dong lanh theo spec muc 6):
  * Quet moi dong DECISION co status BET_PAPER va decided_at_utc >= T0;
    KIEM LAI dinh nghia binding muc 2 TREN DU LIEU DIA (doc lai file
    opinion production, KHONG tin truong ai_gate mot minh).
  * Nguong giu: PASS khi va chi khi (a) so vi pham = 0, va battery muc 5
    van xanh khi chay lai cuoi ky (battery la viec rieng — script chi in
    nhac); vi pham bat ky (>0) = BUG: verdict PASS bi dinh chi, bao ngay.
  * Bao cao phai neu: n BET_PAPER da dat, n refusals (tu telemetry
    D2_REFUSED / gate_events DECISION_REFUSED_NO_OPINION_BOUND), n vi pham.
  * Vi pham KHONG duoc xoa khoi so (append-only; chi lam bang chung).
Exit code: 0 = PASS, 1 = BUG, 2 = loi dau vao.
KHONG ghi, khong sua bat ky file nao cua desk — chi doc.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research.papertrade_exec import d2_invariant as D2          # noqa: E402
from research.papertrade_exec import ai_gate_v2 as G             # noqa: E402


def _load_ledger_rows(data_root: Path) -> list[dict]:
    p = data_root / "ledger" / "paper_ledger.jsonl"
    rows = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _counters(data_root: Path) -> dict:
    """Refusals tu telemetry (counter rieng, muc 3.5) va gate_events."""
    tel = ref = 0
    base = data_root / "ai_review"
    tp = base / "telemetry.jsonl"
    if tp.exists():
        tel = sum(1 for l in tp.read_text().splitlines()
                  if l.strip() and json.loads(l).get("outcome")
                  == D2.D2_TELEMETRY_OUTCOME)
    gp = base / "gate_events.jsonl"
    if gp.exists():
        ref = sum(1 for l in gp.read_text().splitlines()
                  if l.strip() and json.loads(l).get("kind")
                  == D2.D2_REFUSAL_EVENT)
    return {"n_refusals_telemetry": tel, "n_refusals_gate_events": ref}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--t0", required=True,
                    help="ISO UTC cua thoi diem GO co hieu luc (spec muc 8)")
    ap.add_argument("--sandbox", action="store_true",
                    help="audit plane sandbox (mac dinh: real)")
    a = ap.parse_args()
    data_root = Path(a.data_root).expanduser()
    if not a.t0.endswith("Z"):
        print("BUG dau vao: --t0 phai la ISO UTC ket thuc bang Z")
        return 2

    rows = _load_ledger_rows(data_root)
    placed = [r for r in rows if r.get("type") == "DECISION"
              and r.get("status") == "BET_PAPER"
              and str(r.get("decided_at_utc", "")) >= a.t0]
    violations = []
    for r in placed:
        ok, code = D2.d2_binding_check(r, data_root, sandbox=a.sandbox)
        if not ok:
            violations.append({"match_id": r.get("match_id"),
                               "decided_at_utc": r.get("decided_at_utc"),
                               "row_sha256": r.get("row_sha256"),
                               "code": code})
    c = _counters(data_root)
    verdict = "PASS" if not violations else "BUG"
    report = {
        "spec": "SPEC_D2_GATE_INVARIANT_2026-10-26.md",
        "spec_sha256": D2.D2_SPEC_SHA256,
        "t0": a.t0, "plane": "sandbox" if a.sandbox else "real",
        "n_bet_paper_since_t0": len(placed),
        **c,
        "n_violations": len(violations),
        "violations": violations,
        "battery_note": ("PASS can them battery muc 5 xanh khi chay lai "
                         "cuoi ky (spec muc 6) — viec do ngoai script nay"),
        "never_exercised_note": (None if placed or c["n_refusals_telemetry"]
                                 else "bat bien chua tung duoc tap tren live"
                                 " (0 BET_PAPER, 0 refusals ke tu T0)"),
        "verdict": verdict,
    }
    print(json.dumps(report, indent=1, ensure_ascii=False, default=str))
    if verdict == "BUG":
        print("BUG theo luat audit thuong truc: verdict PASS bi dinh chi, "
              "bao ngay cho chu + coordinator; KHONG xoa dong vi pham khoi "
              "so.", file=sys.stderr)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
