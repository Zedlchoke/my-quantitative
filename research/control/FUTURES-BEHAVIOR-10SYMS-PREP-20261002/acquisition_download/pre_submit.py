#!/usr/bin/env python3
"""pre_submit.py — submit every remaining PLANNED chunk now (owner-approved
rescope package) so the vendor batch queue works ahead of local QA.

Budget law: every chunk is get_cost-quoted before its submit; the running
committed total for the WHOLE package must stay <= $118 (hard stop) — the
full rescope package quotes at ~$105.81, so pre-submitting all chunks is a
single legal commitment of an owner-approved scope, NOT new scope.

Double-billing safety: before every submit, batch.list_jobs is scanned for
an existing job with EXACT same params (dataset/schema/symbols/start/end)
— found jobs are reused, never resubmitted. Ledger is SUBMITTED-first.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ACQ = Path(__file__).resolve().parent
sys.path.insert(0, str(ACQ))
import acq_pipeline as P  # noqa: E402


def main() -> int:
    manifest = json.loads(P.MANIFEST.read_text())
    plan = P.build_plan(manifest)
    led = P.load_ledger(plan)
    client = P.get_client()

    committed = sum(c["quote"]["get_cost"] for c in led["chunks"].values()
                    if c.get("state") in P.COMMITTED_STATES
                    and c.get("quote", {}).get("get_cost"))
    print(f"committed now: ${committed:.4f}")
    n = errors = 0
    for plan_chunk in sorted(plan, key=lambda c: (c["order"],
                                                  c["chunk_key"])):
        chunk = led["chunks"][plan_chunk["chunk_key"]]
        st = chunk.get("state", "PLANNED")
        if st != "PLANNED":
            continue
        try:
            q = P.quote_chunk(client, chunk)
        except Exception as exc:  # noqa: BLE001
            errors += 1
            chunk["quote_error_redacted"] = P.redact(str(exc))[:300]
            P.save_ledger(led)
            print(f"ERROR quoting {chunk['chunk_key']}: "
                  f"{P.redact(str(exc))[:160]}")
            if errors >= 3:
                print("ABORT: 3 quote errors")
                return 10
            continue
        chunk["quote"] = q
        committed += q["get_cost"]
        chunk["budget_before_submit"] = {
            "committed_usd": round(committed - q["get_cost"], 6),
            "chunk_cost_usd": q["get_cost"],
            "projected_usd": round(committed, 6)}
        if committed > P.LANE_HARD_STOP:
            chunk["state"] = "QUOTED"
            P.save_ledger(led)
            P.write_stop(led, "BUDGET_CEILING_REACHED",
                         f"pre-submit projected ${committed:.4f} > "
                         f"{P.LANE_HARD_STOP}")
            print("STOP: budget ceiling")
            return 10
        existing = P.find_existing_job(client, led, chunk)
        if existing:
            chunk["job_id"] = existing
            chunk["reused_existing_job"] = True
            chunk["state"] = "SUBMITTED"
            chunk["submitted_utc"] = P.now_utc()
            n += 1
            continue
        try:
            resp = P.submit_chunk(client, chunk)
        except Exception as exc:  # noqa: BLE001
            errors += 1
            chunk["submit_error_redacted"] = P.redact(str(exc))[:300]
            P.save_ledger(led)
            print(f"ERROR submitting {chunk['chunk_key']}: "
                  f"{P.redact(str(exc))[:160]}")
            if errors >= 3:
                print("ABORT: 3 errors")
                return 10
            continue
        chunk["job_id"] = resp.get("id") or resp.get("job_id")
        chunk["state"] = "SUBMITTED"
        chunk["submitted_utc"] = P.now_utc()
        n += 1
        P.save_ledger(led)  # SUBMITTED-first after every submit
        print(f"submitted {chunk['chunk_key']} job={chunk['job_id']} "
              f"cost=${q['get_cost']:.4f} committed=${committed:.4f}")
    P.save_ledger(led)
    print(f"pre-submitted {n} chunks ({errors} errors); total committed "
          f"${committed:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
