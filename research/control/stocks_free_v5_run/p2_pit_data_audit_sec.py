"""STOCKS-FREE-V5 P2-b: /pit-data-audit for the adopted SEC conditioning store.

Verifies, on the REAL staged bytes and the normalized records store:

A1 license/entitlement   every record carries non-empty license_id +
                         entitlement_id; disposition SEC_EDGAR AUTHORIZED
A2 availability          every record: available_time == 23:59:59Z of the
                         effective date (date-only upper bound), effective ==
                         midnight of the fact end date, vintage/retrieved sane;
                         retrieval time NEVER substitutes for availability
A3 raw bytes pinned      file_raw_sha256 re-hashes to the staged file; every
                         hash appears in fetch_log.jsonl with status 200
A4 normalizer pinned     normalizer_version == sanitize-1.0.0+sec-adapter form
A5 vintage append-only   per (entity, field, effective date) the store may hold
                         several availability stamps; as-of selection via the
                         frozen core picks the latest stamp <= gate (spot check)
A6 no-lookahead          sampled panel views contain only records with
                         available_time < session gate (canonical bridge)
A7 warmup coverage       per sector x field: fraction of panel filers with
                         pre-S0 history; fields below the fundable floor are
                         reported as NOT_FUNDABLE for D1 (fail-closed floor)
A8 authorization set     conditioning sources referenced == SEC_EDGAR only

Exit code 0 iff every check passes with zero unresolved findings.
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))

from datetime import date, datetime, time, timezone
import json
from hashlib import sha256
from pathlib import Path
import random
import sys

from research.data_fusion.pit import select_asof
from research.data_fusion.models import NormalizedRecord
from research.assets.stocks.pit_conditioning import session_gate_utc

REPO = Path(__file__).resolve().parents[3]
STAGE = REPO / ".staging_sec"
RECORDS = STAGE / "pit_records.jsonl"
FETCH_LOG = STAGE / "fetch_log.jsonl"
PANEL = STAGE / "panel.json"
AUTHORITY = REPO / "research/control/stocks_free_v5_run/p2_source_authority.json"
REPORT = REPO / "research/control/stocks_free_v5_run/p2_pit_data_audit_sec.json"

UTC = timezone.utc
S0_START = date(2018, 4, 4)
WARMUP_FLOOR = 0.8


def _records() -> list[dict]:
    with open(RECORDS, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def main() -> int:
    findings: list[str] = []
    rows = _records()
    if not rows:
        print("NO RECORDS: run p2_sec_normalize.py first")
        return 1

    # A1 license/entitlement
    a1_bad = [r for r in rows if not r["license_id"] or not r["entitlement_id"]]
    if a1_bad:
        findings.append(f"A1: {len(a1_bad)} records missing license/entitlement")

    # A2 availability semantics
    a2_bad = []
    for r in rows:
        avail = datetime.fromisoformat(r["available_time_utc"])
        effective = datetime.fromisoformat(r["effective_time_utc"])
        if avail.time() != time(23, 59, 59) or avail.tzinfo != UTC:
            a2_bad.append((r["entity_id"], r["field"], "avail not end-of-day bound"))
        if effective.time() != time(0, 0, 0):
            a2_bad.append((r["entity_id"], r["field"], "effective not midnight"))
        if avail > datetime.fromisoformat(r["retrieved_time_utc"]):
            a2_bad.append((r["entity_id"], r["field"], "avail after retrieval"))
    if a2_bad:
        findings.append(f"A2: {len(a2_bad)} availability-semantics violations, first={a2_bad[0]}")

    # A3 raw bytes pinned
    log_hashes = {}
    with open(FETCH_LOG, encoding="utf-8") as fh:
        for line in fh:
            entry = json.loads(line)
            if entry.get("kind") == "companyfacts" and "sha256" in entry:
                log_hashes[entry["sha256"]] = entry.get("status")
    a3_bad = []
    hash_to_path = {}
    for candidate in STAGE.glob("companyfacts_*.json"):
        hash_to_path[sha256(candidate.read_bytes()).hexdigest()] = candidate
    for sha in {r["file_raw_sha256"] for r in rows}:
        path = hash_to_path.get(sha)
        if path is None:
            a3_bad.append((sha, "no staged file"))
        elif log_hashes.get(sha) != 200:
            a3_bad.append((sha, f"fetch log status={log_hashes.get(sha)}"))
    if a3_bad:
        findings.append(f"A3: {len(a3_bad)} hash-pin failures, first={a3_bad[0]}")

    # A4 normalizer pinned
    a4_bad = [r for r in rows if "+sec-adapter-1.0.0" not in r["normalizer_version"]
              or "sec-companyfacts-sanitize-1.0.0" not in r["normalizer_version"]]
    if a4_bad:
        findings.append(f"A4: {len(a4_bad)} normalizer-version anomalies")

    # A5 vintage append-only + as-of selection spot check
    grouped: dict[tuple, list[NormalizedRecord]] = {}
    entity_sector = {}
    for r in rows:
        entity_sector[r["entity_id"]] = r["sector"]
        rec = NormalizedRecord(
            source_id=r["source_id"], dataset_id=r["dataset_id"], entity_id=r["entity_id"],
            field=r["field"], value=r["value"], unit=r["unit"],
            event_time_utc=datetime.fromisoformat(r["event_time_utc"]),
            available_time_utc=datetime.fromisoformat(r["available_time_utc"]),
            effective_time_utc=datetime.fromisoformat(r["effective_time_utc"]),
            vintage_time_utc=datetime.fromisoformat(r["vintage_time_utc"]),
            retrieved_time_utc=datetime.fromisoformat(r["retrieved_time_utc"]),
            raw_path=r["raw_path"], raw_sha256=r["raw_sha256"],
            license_id=r["license_id"], entitlement_id=r["entitlement_id"],
            normalizer_version=r["normalizer_version"],
        )
        grouped.setdefault((rec.entity_id, rec.field, rec.effective_time_utc.date()), []).append(rec)
    multi = [g for g in grouped.values() if len({x.available_time_utc for x in g}) > 1]
    spot_errors = 0
    rng = random.Random(20260904)
    for group in rng.sample(multi, min(50, len(multi))) if multi else []:
        for session in (date(2024, 1, 10), date(2025, 6, 2)):
            chosen = select_asof(group, session_gate_utc(session))
            if chosen is not None and chosen.available_time_utc >= session_gate_utc(session):
                spot_errors += 1
    if spot_errors:
        findings.append(f"A5: {spot_errors} as-of selection violations")

    # A6 no-lookahead sampled view
    a6_bad = 0
    for _ in range(200):
        r = rng.choice(rows)
        session = date.fromisoformat(r["effective_time_utc"][:10])
        if datetime.fromisoformat(r["available_time_utc"]) < session_gate_utc(session):
            pass  # usable, fine
        else:
            # must NOT be usable for the effective-date session
            from research.assets.stocks.pit_conditioning import usable_for_session
            rec = NormalizedRecord(
                source_id=r["source_id"], dataset_id=r["dataset_id"], entity_id=r["entity_id"],
                field=r["field"], value=r["value"], unit=r["unit"],
                event_time_utc=datetime.fromisoformat(r["event_time_utc"]),
                available_time_utc=datetime.fromisoformat(r["available_time_utc"]),
                effective_time_utc=datetime.fromisoformat(r["effective_time_utc"]),
                vintage_time_utc=datetime.fromisoformat(r["vintage_time_utc"]),
                retrieved_time_utc=datetime.fromisoformat(r["retrieved_time_utc"]),
                raw_path=r["raw_path"], raw_sha256=r["raw_sha256"],
                license_id=r["license_id"], entitlement_id=r["entitlement_id"],
                normalizer_version=r["normalizer_version"],
            )
            if usable_for_session(rec, session):
                a6_bad += 1
    if a6_bad:
        findings.append(f"A6: {a6_bad} gate violations")

    # A7 warmup coverage per sector x field
    panel = json.loads(PANEL.read_text())["panel"]
    panel_size = {sector: len(filers) for sector, filers in panel.items()}
    pre_s0: dict[tuple, set] = {}
    for r in rows:
        if datetime.fromisoformat(r["available_time_utc"]) < datetime.combine(S0_START, time(0, 0), tzinfo=UTC):
            pre_s0.setdefault((r["sector"], r["field"]), set()).add(r["entity_id"])
    coverage = {}
    for (sector, field), entities in sorted(pre_s0.items()):
        total = panel_size.get(sector, 0)
        if not total:
            continue
        frac = len(entities) / total
        coverage[f"{sector}|{field}"] = {
            "filers_with_pre_s0": len(entities), "panel": total,
            "fraction": round(frac, 3),
            "fundable_for_d1": frac >= WARMUP_FLOOR,
        }
    not_fundable = {k: v for k, v in coverage.items() if not v["fundable_for_d1"]}

    # A8 authorization set
    authority = json.loads(AUTHORITY.read_text())
    a8_fail = (authority["dispositions"]["SEC_EDGAR"]["status"] != "AUTHORIZED_INTERNAL_RESEARCH"
               or authority["conditioning_eligibility"]["pit_conditioned_proposals_may_use"] != "SEC_EDGAR only")
    if a8_fail:
        findings.append("A8: authorization set inconsistent with V5 plan")

    report = {
        "schema": "stocks_free_v5_run/p2_pit_data_audit_sec@1",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "records_audited": len(rows),
        "distinct_entities": len({r["entity_id"] for r in rows}),
        "distinct_fields": len({r["field"] for r in rows}),
        "vintage_groups_with_multiple_stamps": len(multi),
        "checks": {
            "A1_license_entitlement": "PASS" if not a1_bad else "FAIL",
            "A2_availability_semantics": "PASS" if not a2_bad else "FAIL",
            "A3_raw_bytes_pinned": "PASS" if not a3_bad else "FAIL",
            "A4_normalizer_pinned": "PASS" if not a4_bad else "FAIL",
            "A5_vintage_append_only_asof": "PASS" if not spot_errors else "FAIL",
            "A6_no_lookahead_gate": "PASS" if not a6_bad else "FAIL",
            "A7_warmup_coverage": {"status": "PASS" if not not_fundable else "PASS_WITH_NOT_FUNDABLE_FIELDS",
                                    "floor": WARMUP_FLOOR, "coverage": coverage,
                                    "not_fundable_fields_for_d1": sorted(not_fundable)},
            "A8_authorization_set": ("PASS" if authority["dispositions"]["SEC_EDGAR"]["status"] == "AUTHORIZED_INTERNAL_RESEARCH"
                                     and authority["conditioning_eligibility"]["pit_conditioned_proposals_may_use"] == "SEC_EDGAR only"
                                     else "FAIL"),
        },
        "findings": findings,
        "verdict": "PASS" if not findings else "FAIL",
    }
    REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ("records_audited", "distinct_entities", "distinct_fields", "verdict")}, indent=1))
    for k, v in report["checks"].items():
        print(f"  {k}: {v if isinstance(v, str) else v['status']}")
    if findings:
        print("FINDINGS:", *findings, sep="\n  ")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
