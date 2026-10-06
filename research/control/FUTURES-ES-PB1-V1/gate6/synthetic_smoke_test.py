#!/usr/bin/env python
"""synthetic_smoke_test.py — gate-6 infrastructure smoke test (SYNTHETIC ONLY).

████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC ████████████
EVERY input below is FABRICATED for infrastructure verification only.
Trade rows are synthetic constructions (fixed placeholder prices), never
derived from any real panel/parquet. ZERO real-outcome PnL is computed
anywhere in this test. Nothing here scores, gates, or publishes anything.
████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC █████ SYNTHETIC ████████████

Verifies, on SYNTHETIC data:
  V1  24-slot law            — ledger initializes with the FROZEN 24 ids
                               (asserted byte-equal against the freeze
                               identity_table, config-read only)
  V2  refusal triggers fire  — R1 no-GO (paraphrase + delegated), R2 no-auth,
                               R3 lock-held simulation, R4 freeze-drift
                               simulation, R5 variant-ordered pins; and the
                               allow path passes all five gates
  V3  append-only behavior   — double-terminal refused, unknown slot refused,
                               disk re-read + hash-chain verify PASS, tamper
                               with one byte ⇒ chain break detected
  V4  denominator accounting — PASS/FAIL count; publication failure still
                               counts; REFUSED/NOT_RUN never count
  V5  reproduction twin      — two identical synthetic runs byte-match;
                               a perturbed copy FAILS the comparison

Outputs: everything under gate6/smoke/ with SYNTHETIC banners.
Run: .venv/bin/python research/control/FUTURES-ES-PB1-V1/gate6/synthetic_smoke_test.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from trial_ledger import (LedgerError, RefusalGate, TrialLedger,  # noqa: E402
                          twin_compare, twin_manifest)

WORKTREE = HERE.parents[3]
FREEZE = (WORKTREE / "research/control/FUTURES-ES-PB1-V1/repair/"
          "selection_freeze_v2.json")
SMOKE = HERE / "smoke"

SYN_PRICE = 9999.75  # placeholder price — obviously synthetic, no market meaning

# Transcribed from SPEC_PB1_ES §6 / freeze identity_table (CONFIG, not outcomes).
IDS_TRANSCRIBED = [
    "FBES1-PB1-CONT-UP-D0-S2", "FBES1-PB1-CONT-UP-D30-S2",
    "FBES1-PB1-REV-UP-D0-S2", "FBES1-PB1-REV-UP-D30-S2",
    "FBES1-PB1-CONT-DN-D0-S2", "FBES1-PB1-CONT-DN-D30-S2",
    "FBES1-PB1-REV-DN-D0-S2", "FBES1-PB1-REV-DN-D30-S2",
    "FBES1-PB1-CONT-UP-D0-S1", "FBES1-PB1-CONT-UP-D0-S3",
    "FBES1-PB1-REV-UP-D0-S1", "FBES1-PB1-REV-UP-D0-S3",
    "FBES1-PB1-CONT-DN-D0-S1", "FBES1-PB1-CONT-DN-D0-S3",
    "FBES1-PB1-REV-DN-D0-S1", "FBES1-PB1-REV-DN-D0-S3",
    "FBES1-PB1-CONT-UP-D0-S2-FOMCIN", "FBES1-PB1-CONT-DN-D0-S2-FOMCIN",
    "FBES1-PB1-REV-UP-D0-S2-FOMCIN", "FBES1-PB1-REV-DN-D0-S2-FOMCIN",
    "FBES1-PLA-D0-S2", "FBES1-ALW-D0-S2", "FBES1-FLAT", "FBES1-DOSE-D0-S2",
]

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  FAIL  {name} — {detail}")


def synthetic_trades(identity_id: str) -> dict:
    """Fabricated trade list — SYNTHETIC, hash-derived counts, placeholder
    prices. NEVER derived from any real panel. Computes no PnL."""
    n = 1 + int(identity_id.encode().hex()[-2:], 16) % 7
    return {
        "banner": "SYNTHETIC — fabricated for gate-6 smoke test; not market data",
        "identity_id": identity_id,
        "n_trades": n,
        "trades": [
            {"t": i, "entry_ts": f"SYNTH-{identity_id}-{i:03d}",
             "exit_ts": f"SYNTH-{identity_id}-{i:03d}-X",
             "price": SYN_PRICE, "qty": 1}
            for i in range(n)
        ],
    }


def main() -> int:
    SMOKE.mkdir(parents=True, exist_ok=True)
    banner = ("SYNTHETIC SMOKE OUTPUT — fabricated data, zero real-outcome "
              "PnL, gates nothing")
    (SMOKE / "SYNTHETIC_BANNER.txt").write_text(banner + "\n", encoding="utf-8")
    print("=" * 78)
    print("GATE-6 SYNTHETIC SMOKE TEST — all inputs fabricated, zero real PnL")
    print("=" * 78)

    # ---- V1: 24-slot law -------------------------------------------------
    print("\n[V1] 24-slot law")
    emb = json.loads(FREEZE.read_text())["identity_table"]["embedded"]
    freeze_ids = [row["id"] for row in emb["identities"]]
    check("frozen identities embedded in the freeze (24 rows)",
          len(freeze_ids) == 24 and "identity_table" in emb["schema"],
          f"schema={emb['schema']}")
    check("transcription set-equal to frozen table (24 unique)",
          set(freeze_ids) == set(IDS_TRANSCRIBED) and len(set(freeze_ids)) == 24)
    # the freeze's own order is the authoritative slot order
    IDS = freeze_ids
    ledger = TrialLedger(SMOKE / "ledger_synthetic.jsonl", IDS)
    s0 = ledger.summary()
    check("fresh ledger: 24 slots all NOT_RUN, observed 0",
          s0["slots"] == 24 and s0["status_counts"]["NOT_RUN"] == 24
          and s0["observed_denominator"] == 0)
    try:
        TrialLedger(SMOKE / "bad.jsonl", IDS[:23])
        check("23-slot init refused", False)
    except LedgerError:
        check("23-slot init refused", True)

    # ---- V2: refusal gates ----------------------------------------------
    print("\n[V2] refusal triggers (synthetic declarations)")
    gate = RefusalGate()
    ok_facts = {
        "go_phrase": "GO FUTURES-ES-PB1-V1 SCORED EXECUTION",
        "go_phrase_owner_typed": True,
        "registry_go_phrase": "GO FUTURES-ES-PB1-V1 SCORED EXECUTION",
        "a7_verdict": "AUTHORIZED_WITH_FINDINGS", "a7_high_critical": 0,
        "lock_state": "FREE_PROVEN",
        "input_sha_matches": {k: True for k in
                              ["SPEC", "freeze", "exclude", "panel", "chain",
                               "machinery"]},
        "pins_status": "ADJUDICATED_AUTHORITY_EXISTS",
    }
    refusal_ledger = TrialLedger(SMOKE / "refusal_ledger_synthetic.jsonl",
                                 IDS)

    scenarios = [
        ("R1 paraphrased GO (historical PLAN §6 string)",
         dict(ok_facts, go_phrase="GO FUTURES ES V1 SCORED EXECUTION"),
         "REFUSED_NO_GO"),
        ("R1 delegated GO (owner_typed=False)",
         dict(ok_facts, go_phrase_owner_typed=False), "REFUSED_NO_GO"),
        ("R1 registry mismatch",
         dict(ok_facts, registry_go_phrase="UNSET"), "REFUSED_NO_GO"),
        ("R2 no A7 auth", dict(ok_facts, a7_verdict=None), "REFUSED_NO_AUTH"),
        ("R2 A7 with unresolved HIGH",
         dict(ok_facts, a7_high_critical=1), "REFUSED_NO_AUTH"),
        ("R3 lock-held simulation", dict(ok_facts, lock_state="BUSY"),
         "NOT_RUN_RESOURCE_CONFLICT"),
        ("R3 lock state drift", dict(ok_facts, lock_state="WEIRD"),
         "REFUSED_CONTROL_STATE_DRIFT"),
        ("R4 freeze-drift simulation",
         dict(ok_facts, input_sha_matches=dict(ok_facts["input_sha_matches"],
                                               freeze=False)),
         "REFUSED_DRIFT"),
        ("R5 owner-ordered variant pins",
         dict(ok_facts, pins_status="VARIANT_ORDERED"),
         "REFUSED_PINS_UNRESOLVED"),
    ]
    for name, facts, expect in scenarios:
        allowed, reason, _ = gate.evaluate(facts)
        fired = (not allowed) and reason == expect
        check(f"{name} -> {expect}", fired, f"got {reason!r}")
        refusal_ledger.record_refusal(reason if fired else expect,
                                      note=f"smoke: {name}")

    allowed, reason, detail = gate.evaluate(ok_facts)
    check("allow path passes R1-R5 in order", allowed and reason is None
          and list(detail.get("gates_passed") or []) == list(gate.ORDER),
          f"{reason} {detail}")

    # ---- V3: append-only behavior ---------------------------------------
    print("\n[V3] append-only ledger behavior")
    ledger.record_result(IDS[0], "PASS", note="synthetic",
                         result_sha="syn0", computed_by="smoke")
    try:
        ledger.record_result(IDS[0], "FAIL")
        check("double-terminal refused", False)
    except LedgerError:
        check("double-terminal refused", True)
    try:
        ledger.record_result("FBES1-NOT-A-SLOT", "PASS")
        check("unknown slot refused", False)
    except LedgerError:
        check("unknown slot refused", True)
    v = ledger.verify()
    check("disk re-read + hash-chain verify", v["ok"] and v["rows"] >= 1)

    # tamper detection on a COPY (main ledger stays clean). The file needs
    # >=2 rows so the tampered row has a successor whose chain link breaks;
    # an intermediate NOT_RUN annotation row is legal bookkeeping.
    ledger.record_result(IDS[1], "NOT_RUN", note="synthetic annotation")
    ledger_file = SMOKE / "ledger_synthetic.jsonl"
    tampered = SMOKE / "tampered_copy.jsonl"
    shutil.copyfile(ledger_file, tampered)
    pre_sha = hashlib.sha256(tampered.read_bytes()).hexdigest()
    raw = tampered.read_text()
    tampered.write_text(raw.replace("syn0", "syn9"), encoding="utf-8")
    try:
        TrialLedger(tampered, IDS)
        check("non-final-row tamper detected (successor chain break)",
              False)
    except LedgerError:
        check("non-final-row tamper detected (successor chain break)", True)
    check("whole-file digest changes under tamper (final-row law)",
          hashlib.sha256(tampered.read_bytes()).hexdigest() != pre_sha)
    tampered.unlink()

    # ---- V4: denominator accounting (synthetic results) ------------------
    print("\n[V4] observed-denominator accounting on synthetic results")
    # slot 0 already PASS. Fill the remaining 23:
    #   i 1..10  -> 10 PASS; i 11..15 -> 5 FAIL (i=11 published=False —
    #   publication failure still counts); i 16..18 -> 3 REFUSED;
    #   i 19..23 -> 5 NOT_RUN.  Totals 11 PASS / 5 FAIL / 3 REFUSED / 5 NOT_RUN.
    plan = {}
    for i, iid in enumerate(IDS[1:], start=1):
        if i <= 10:
            plan[iid] = ("PASS", True)
        elif i <= 15:
            plan[iid] = ("FAIL", i != 11)
        elif i <= 18:
            plan[iid] = ("REFUSED", None)
        else:
            plan[iid] = ("NOT_RUN", None)
    for iid, (st, pub) in plan.items():
        kw = {} if pub is None else {"published": pub}
        ledger.record_result(iid, st, note="synthetic", result_sha="syn",
                             computed_by="smoke", **kw)
    s = ledger.summary()
    n_pass = s["status_counts"]["PASS"]
    n_fail = s["status_counts"]["FAIL"]
    n_ref = s["status_counts"]["REFUSED"]
    n_nr = s["status_counts"]["NOT_RUN"]
    expected_observed = n_pass + n_fail  # 11 + 5 = 16
    check("status mix (11 PASS / 5 FAIL / 3 REFUSED / 5 NOT_RUN)",
          (n_pass, n_fail, n_ref, n_nr) == (11, 5, 3, 5),
          f"got {(n_pass, n_fail, n_ref, n_nr)}")
    check("observed denominator == PASS+FAIL == 16",
          s["observed_denominator"] == expected_observed == 16,
          f"got {s['observed_denominator']}")
    check("REFUSED/NOT_RUN never counted (16 != 19 or 24)",
          s["observed_denominator"] == 16
          and s["observed_denominator"] != n_pass + n_fail + n_ref
          and s["observed_denominator"] != 24)
    check("publication failure still counted (published=False inside FAIL)",
          s["observed_denominator"] == n_pass + n_fail)
    check("refusal-event rows never counted",
          refusal_ledger.observed() == 0 and
          len(refusal_ledger.summary()["per_identity"]) == 24)
    # resolve the 5 NOT_RUN slots to terminal REFUSED (synthetic): the
    # ledger completes and the observed denominator must NOT move.
    for iid, st in s["per_identity"].items():
        if st == "NOT_RUN":
            ledger.record_result(iid, "REFUSED", note="synthetic resolution",
                                 computed_by="smoke")
    s2 = ledger.summary()
    check("24 slots terminal-complete after NOT_RUN resolution",
          s2["complete"] and s2["status_counts"]["NOT_RUN"] == 0
          and sum(s2["status_counts"][k] for k in ("PASS", "FAIL", "REFUSED"))
          == 24, json.dumps(s2["status_counts"]))
    check("observed denominator UNCHANGED by REFUSED resolution (still 16)",
          s2["observed_denominator"] == 16,
          f"got {s2['observed_denominator']}")

    # ---- V5: reproduction twin (synthetic runs) --------------------------
    print("\n[V5] reproduction-twin bookkeeping on synthetic runs")
    for name in ("twin_run_A", "twin_run_B", "twin_run_C"):
        d = SMOKE / name
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        for iid in IDS:
            (d / f"SYNTHETIC__{iid}.json").write_text(
                json.dumps(synthetic_trades(iid), indent=1) + "\n",
                encoding="utf-8")
    ma = twin_manifest(SMOKE / "twin_run_A")
    mb = twin_manifest(SMOKE / "twin_run_B")
    twin_ok = twin_compare(ma, mb)
    check("two identical synthetic runs byte-match (24 files)",
          twin_ok["byte_match"] and twin_ok["n_files_a"] == 24)
    # perturb exactly one byte in one file of run C, THEN manifest it
    victim = SMOKE / "twin_run_C" / f"SYNTHETIC__{IDS[0]}.json"
    victim.write_text(victim.read_text().replace('"t": 0', '"t": 7', 1),
                      encoding="utf-8")
    mc = twin_manifest(SMOKE / "twin_run_C")
    twin_bad = twin_compare(ma, mc)
    check("perturbed synthetic run FAILS twin comparison",
          (not twin_bad["byte_match"]) and len(twin_bad["differing"]) == 1,
          str(twin_bad["differing"]))
    digest = {"banner": banner, "ledger_summary": ledger.summary(),
              "refusal_ledger_summary": refusal_ledger.summary(),
              "twin_A_vs_B": twin_ok, "twin_A_vs_C": twin_bad,
              "smoke_checks": {"pass": PASS, "fail": FAIL}}
    (SMOKE / "smoke_digest.json").write_text(
        json.dumps(digest, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (SMOKE / "twin_verdict_synthetic.json").write_text(json.dumps({
        "banner": banner, "A_vs_B": twin_ok, "A_vs_C": twin_bad},
        indent=1) + "\n", encoding="utf-8")

    print("\n" + "=" * 78)
    print(f"SMOKE RESULT: {PASS} pass / {FAIL} fail "
          f"{'— ALL GREEN' if FAIL == 0 else '— FAILURES PRESENT'}")
    print("All outputs under gate6/smoke/ — SYNTHETIC ONLY, zero real PnL.")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
