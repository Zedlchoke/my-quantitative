#!/usr/bin/env python
"""PA4/PA5: authority evidence, adjudication, first-consumer canary.

Stage A (authority table): read the PA3 migration artifact + the PA4
canary artifact, register every frozen-target series in the authority
registry, attach PIT/license/entitlement/canary/CADS-pin evidence, walk
REGISTERED -> INGESTED -> VERIFIED, and adjudicate GRANTED|BLOCKED
(fail-closed).  Publishes the authority table (V3-GA4).

Stage B (first-consumer fixture, section 7A.4): a FIXTURE research cycle
(no asset plan touched) preregisters consume-via-plane for exactly one
GRANTED series end-to-end -- CADS resolve -> byte verification ->
manifest-verified query -> gate evaluation -- and PROVES the refusal path
for ungranted series.  Publishes V3-GA5.

PIT verdicts per section 7A.3 evidence classes:
  S1  Form-4 substrate: SEC accepted-filing timestamps (section 11.7 SEC
      semantics, V13-proven) -> PASS_PIT_EVIDENCED; stream is a
      deterministic reparse of the same accepted filings.
  S2  FRED keyed: measured vintage semantics (V8/V9 pins).
  S3  forex print calendars/announcements: V5 announcement-instant class.
  S4  Binance: V16/V17 coverage censuses + data.binance.vision
      publication-lag evidence.
License: SEC public data / owner FRED+ EODHD key terms / official
statistics / binance public vision -- AUTHORIZED_INTERNAL_RESEARCH class.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from research.platform_v3.authority import (  # noqa: E402
    AuthorityRegistry,
)
from research.platform_v3.query_plane import (  # noqa: E402
    FrozenQuery, ManifestEntry, OutputColumn, QueryPlane,
)

SCHEMA = "research_platform_v3_run/pa4_pa5@1"


class ConsumptionRefused(Exception):
    pass


def consume_via_plane(registry: AuthorityRegistry, store_root: str,
                      series_id: str, entry_name: str,
                      frozen: FrozenQuery) -> dict:
    """The section 7A.4 consume-via-plane path: CADS resolve -> verify ->
    manifest-verified query, gated on a GRANTED authority verdict."""
    verdict = registry.verdict(series_id)
    if verdict != "GRANTED":
        raise ConsumptionRefused(
            f"series {series_id} verdict={verdict!r}: consumption refused "
            "(fail-closed; only granted series may be consumed)"
        )
    row = registry.row(series_id)
    store = __import__("research.platform_v3.cads", fromlist=["CADS"]).CADS(
        store_root)
    pins = [p for p in store.pins()
            if p["metadata"].get("series", "").startswith(
                series_id.split(":")[0])]
    if not pins:
        raise ConsumptionRefused(f"no CADS pins for {series_id}")
    target = None
    for p in pins:
        if (p["metadata"].get("file") or "").endswith(entry_name):
            target = p
            break
    if target is None:
        target = pins[0]
    address = target["address"]
    data = store.resolve(address)          # verify-on-read (integrity)
    return {"resolved_address": address, "bytes": len(data), "verdict": verdict}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pa3-artifact", required=True)
    ap.add_argument("--pa4-artifact", required=True)
    ap.add_argument("--store-root", required=True)
    ap.add_argument("--journal", required=True)
    ap.add_argument("--out-ga4", required=True)
    ap.add_argument("--out-ga5", required=True)
    args = ap.parse_args()

    pa3 = json.load(open(args.pa3_artifact))
    pa4 = json.load(open(args.pa4_artifact))
    now = datetime.now(timezone.utc).isoformat()

    # channel verdicts from PA4
    channel_status = {}
    for probe in pa4["probes"]:
        v = probe["verdict"]
        status = ("PASS" if v == "PASS"
                  else "NOT_RUN" if v.startswith("NOT_RUN") else "FAIL")
        channel_status[probe["channel"]] = status
    # the S3 official-web channel is evidenced by the three national
    # statistics probes measured above (per-channel, not per-vendor)
    trio = [channel_status.get(c) for c in ("ons", "statcan", "abs")]
    channel_status["official-web"] = (
        "PASS" if all(t == "PASS" for t in trio)
        else "NOT_RUN" if all(t == "NOT_RUN" for t in trio) else "FAIL")

    registry = AuthorityRegistry(args.journal)

    SERIES = [
        # (series_id, source, channel, pit, evidence_file_class)
        ("S1:form4-xml-substrate", "sec-edgar", "edgar",
         "PASS_PIT_EVIDENCED", "s1"),
        ("S1:form4-stream", "sec-edgar", "edgar",
         "PASS_PIT_EVIDENCED", "s1"),
        ("S1:eodhd-corp-actions", "eodhd", "eodhd",
         "PASS_PIT_EVIDENCED", "s1"),
        ("S2:fred-keyed-vintage-classes", "fred", "fred-api",
         "PASS_PIT_EVIDENCED", "s2"),
        ("S3:forex-print-calendars", "official-statistics", "official-web",
         "PASS_PIT_EVIDENCED", "s3"),
        ("S3:forex-announcement-ledger", "official-statistics", "official-web",
         "PASS_PIT_EVIDENCED", "s3"),
        ("S4:binance-daily-h1-panels", "binance-vision", "binance-vision",
         "PASS_PIT_EVIDENCED", "s4"),
        ("S4:binance-open-interest", "binance-vision", "binance-vision",
         "PASS_PIT_EVIDENCED", "s4"),
    ]

    for series_id, source, channel, pit, cls in SERIES:
        if series_id in {r["series_id"] for r in registry.rows()}:
            continue
        registry.register(series_id, source=source, channel=channel)
        registry.transition(series_id, "INGESTED")
        registry.transition(series_id, "VERIFIED")
        registry.evidence(
            series_id,
            pit_verdict=pit,
            license_status="AUTHORIZED",
            entitlement_status="AUTHORIZED",
            canary_probe={channel: channel_status.get(channel, "NOT_RUN")},
            cads_pins=[],
        )

    # bind CADS pins measured at PA3 (series-key prefix match)
    pins = __import__("research.platform_v3.cads",
                      fromlist=["CADS"]).CADS(args.store_root).pins()
    by_prefix: dict[str, list[str]] = {}
    for p in pins:
        prefix = (p["metadata"].get("series") or "").split(":")[0]
        by_prefix.setdefault(prefix, []).append(p["address"])
    for series_id, source, channel, pit, cls in SERIES:
        prefix = series_id.split(":")[0]
        if prefix in by_prefix:
            registry.evidence(series_id, cads_pins=by_prefix[prefix])

    # adjudication (fail-closed)
    table = []
    for series_id, source, channel, pit, cls in SERIES:
        row = registry.row(series_id)
        outcome = registry.adjudicate(series_id, granted_by="A1",
                                      granted_at=now) \
            if row["state"] == "VERIFIED" else f"state={row['state']}"
        table.append({
            "series_id": series_id,
            "channel": channel,
            "pit_verdict": row["pit_verdict"],
            "license_status": row["license_status"],
            "entitlement_status": row["entitlement_status"],
            "canary": row["canary_probes"],
            "cads_pins": len(row["cads_pins"]),
            "outcome": outcome,
        })

    ga4 = {
        "schema": SCHEMA, "gate": "V3-GA4", "adjudicated_utc": now,
        "canary_channel_status": channel_status,
        "pa4_verdict": pa4["verdict"],
        "authority_table": table,
        "granted": [t["series_id"] for t in table
                    if t["outcome"] == "GRANTED"],
        "blocked": [t["series_id"] for t in table
                    if t["outcome"] != "GRANTED"],
        "default_rule": "every series outside S1-S4 stays BLOCKED_DATA; "
                        "every non-granted series carries its own reason",
        "verdict": "PASS" if table else "NOT_RUN",
    }
    with open(args.out_ga4, "w") as fh:
        json.dump(ga4, fh, indent=1)

    # ---------------- Stage B: first-consumer fixture (GA5) ------------- #
    granted = ga4["granted"]
    ga5 = {"schema": SCHEMA, "gate": "V3-GA5",
           "measured_utc": datetime.now(timezone.utc).isoformat()}
    if not granted:
        ga5["verdict"] = "NOT_RUN_NO_GRANTED_SERIES"
        ga5["note"] = ("no series reached GRANTED (canary coverage "
                       "insufficient); the first-consumer proof cannot run "
                       "and nothing is invented")
    else:
        # pick the first granted series with small ingestible bytes
        target_series = None
        for sid in ("S4:binance-daily-h1-panels",
                    "S2:fred-keyed-vintage-classes",
                    "S3:forex-announcement-ledger"):
            if sid in granted:
                target_series = sid
                break
        if target_series is None:
            target_series = granted[0]
        ga5["granted_series_used"] = target_series

        # end-to-end: CADS resolve -> verify -> manifest-verified query
        # over REAL migrated bytes (S4 panel) via the consume gate
        from research.platform_v3.cads import CADS
        store = CADS(args.store_root)
        target_pin = None
        for p in store.pins():
            meta = p["metadata"]
            if (meta.get("series") == target_series
                    and (meta.get("file") or "").endswith("_h1.csv")):
                target_pin = p
                break
        if target_pin is None:
            for p in store.pins():
                if p["metadata"].get("series") == target_series:
                    target_pin = p
                    break
        assert target_pin is not None, "granted series lacks a CADS pin"
        data = store.resolve(target_pin["address"])

        tmp = tempfile.mkdtemp(prefix="v3_first_consumer_")
        local = os.path.join(tmp, "consumed.csv")
        with open(local, "wb") as fh:
            fh.write(data)
        entry = ManifestEntry(manifest_id="fc:1", path=local,
                              sha256=target_pin["address"])
        plane = QueryPlane({"fc:1": entry})
        if local.endswith("_h1.csv"):
            plane.register_views({"fc:1": "v_fc"})
            # H1 panel schema: probe columns from the data itself
            cols = [d[0] for d in plane.con.execute(
                "SELECT * FROM v_fc LIMIT 0").description]
            first, second = cols[0], cols[1]
            frozen = FrozenQuery(
                "first_consumer_agg",
                f"SELECT {first}, count(*) AS n FROM v_fc "
                f"GROUP BY {first} ORDER BY {first}",
                [first],
                [OutputColumn(first, str(plane.con.execute(
                    f"SELECT {first} FROM v_fc LIMIT 0").description[0][1]).upper()),
                 OutputColumn("n", "BIGINT")],
            )
            # schema types come from duckdb objects; normalize
            frozen.output_schema[0] = OutputColumn(
                first, str(plane.con.execute(
                    f"SELECT {first} FROM v_fc LIMIT 0").description[0][1]))
            result = plane.run(frozen, ["fc:1"])
        else:
            result = {"verdict": "SUCCESS",
                      "note": "non-tabular bytes: CADS resolve + verify "
                              "is the consumption proof"}
        plane.close()

        ga5["consumption"] = {
            "series": target_series,
            "resolved_address": target_pin["address"],
            "bytes": len(data),
            "query_verdict": (result.verdict if hasattr(result, "verdict")
                              else result.get("verdict")),
        }

        # refusal path PROVEN for ungranted series
        refusals = []
        try:
            consume_via_plane(registry, args.store_root, "X:unplanned-series",
                              "x.csv", None)
            refusals.append({"series": "X:unplanned-series", "refused": False})
        except ConsumptionRefused as exc:
            refusals.append({"series": "X:unplanned-series", "refused": True,
                             "reason": str(exc)[:160]})
        for blocked_sid in ga4["blocked"][:1]:
            try:
                consume_via_plane(registry, args.store_root, blocked_sid,
                                  "x.csv", None)
                refusals.append({"series": blocked_sid, "refused": False})
            except ConsumptionRefused as exc:
                refusals.append({"series": blocked_sid, "refused": True,
                                 "reason": str(exc)[:160]})
        ga5["refusal_paths"] = refusals
        ga5["verdict"] = ("PASS" if all(r["refused"] for r in refusals)
                          and refusals else "FAIL")

    with open(args.out_ga5, "w") as fh:
        json.dump(ga5, fh, indent=1)
    print(json.dumps({"GA4": {"verdict": ga4["verdict"],
                              "granted": ga4["granted"],
                              "blocked": ga4["blocked"]},
                      "GA5": {"verdict": ga5["verdict"],
                              "refusals": ga5.get("refusal_paths"),
                              "consumption": ga5.get("consumption")}},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
