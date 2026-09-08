"""V9 P0c: extend the multi-vintage SEC panel to dead filers' CIKs.

PLAN_stocks_v9.md sec 3 P0c. The frozen V8 panel (sha256 1cb115d3...,
1 row per filed vintage, V6 multi-vintage semantics) covers the 410 alive
filers only; the V9 dead leg needs the same PIT fact semantics for the
death cohort. This script:

  pull-companyfacts  fetches SEC XBRL companyfacts per dead CIK into the
                     gitignored staging dir (resumable, fail-closed sidecars)
  emit               builds the NEW panel file:
                       prefix = frozen V8 panel bytes (hash-verified before
                       use, never modified),
                       suffix = dead-filer rows in the identical V6 row
                       schema {e,s,f,u,v,eff,avail[,evd]}, emitted through
                       the inherited data_fusion SecAdapter + sec_sanitize
                       machinery (the F1-remedy lane's own code path),
                       deterministically sorted among themselves.
                     The new file is a NEW artifact with a NEW sha256; the
                     V8 hash stays frozen evidence and is never overwritten.

Usage:
  python -m research.assets.stocks.p0c_v9_panel_extend pull-companyfacts
  python -m research.assets.stocks.p0c_v9_panel_extend emit
"""

import hashlib
import json
import os
import sys
import time
import urllib.request
import datetime

from research.assets.stocks.sec_sanitize import (
    SANITIZER_VERSION,
    chunk_companyfacts,
    sanitize_companyfacts,
)

CONTROL = "research/control/stocks_free_v9_run"
COHORT = f"{CONTROL}/cohort_v9.json"
FACTS_DIR = ".staging_sec_v9/companyfacts"
V8_PANEL = os.environ.get(
    "V8_PANEL_PATH",
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v8/integration/.staging_sec_v8/multivintage_panel.jsonl",
)
V8_PANEL_SHA = "1cb115d3dbb563cbc6ec4b1ce78ef2347b4538b23fc9e3232e38b1f9d16cdd40"
PANEL_OUT = ".staging_sec_v9/multivintage_panel.jsonl"
MANIFEST_OUT = f"{CONTROL}/p0c_v9_panel_manifest.json"
UA_SEC = "Research my-quantitative@example.com"  # see p0a_v9_death_census UA note


def _get(url, timeout=90, attempts=4):
    last = None
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": UA_SEC, "Accept-Encoding": "gzip, deflate"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    data = gzip.decompress(data)
            return data
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):
                time.sleep(2 * (2 ** i))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            time.sleep(2 * (2 ** i))
    raise last


def pull_companyfacts():
    cohort = json.load(open(COHORT))
    dead = cohort["members"]["DEAD_EVIDENCED"]
    os.makedirs(FACTS_DIR, exist_ok=True)
    pulled = skipped = failed = absent = 0
    for m in dead:
        cik = m["cik"]
        out = f"{FACTS_DIR}/{cik}.json"
        if os.path.exists(out) and os.path.getsize(out) > 2:
            skipped += 1
            continue
        try:
            data = _get(f"https://data.sec.gov/api/xbrl/companyfacts/{cik}.json")
        except urllib.error.HTTPError as e:
            if e.code == 404:  # no XBRL facts at all: recorded absence, not an error
                with open(out, "w") as f:
                    f.write("{}")
                absent += 1
                continue
            with open(f"{FACTS_DIR}/{cik}.FAILED", "w") as f:
                f.write(f"HTTP {e.code}\n")
            failed += 1
            continue
        except Exception as e:  # noqa: BLE001 - recorded fail-closed sidecar
            with open(f"{FACTS_DIR}/{cik}.FAILED", "w") as f:
                f.write(f"{type(e).__name__}: {e}\n")
            failed += 1
            continue
        with open(out, "wb") as f:
            f.write(data)
        pulled += 1
        time.sleep(0.25)
    print(json.dumps({"pulled": pulled, "skipped": skipped, "failed": failed,
                      "facts_absent_404": absent, "total_dead": len(dead)}))


def _records_for(path):
    """Yield SecAdapter records for one companyfacts file (inherited machinery)."""
    from research.data_fusion.adapters.base import RawResponse, RequestSpec
    from research.data_fusion.adapters.sec import SecAdapter

    raw_bytes = open(path, "rb").read()
    payload = json.loads(raw_bytes)
    if not payload:
        return  # recorded 404 absence
    sanitized, _stats = sanitize_companyfacts(payload)
    adapter = SecAdapter()
    request = RequestSpec(
        source_id="SEC_EDGAR",
        url=f"https://data.sec.gov/api/xbrl/companyfacts/{os.path.basename(path).removesuffix('.json')}.json",
    )
    for _tag, chunk_body in chunk_companyfacts(sanitized):
        response = RawResponse(
            request_id=request.request_id(),
            url=request.full_url(),
            status=200,
            reason="OK",
            headers=(("content-type", "application/json"),),
            body=chunk_body,
            retrieved_time_utc=datetime.datetime.now(datetime.timezone.utc),
        )
        yield from adapter.parse_company_facts(response).records


def emit():
    from research.assets.stocks.p0a_multivintage import parse_iso_utc

    # 1. verify the frozen V8 panel bytes before reuse (fail closed)
    v8_bytes = open(V8_PANEL, "rb").read()
    actual = hashlib.sha256(v8_bytes).hexdigest()
    if actual != V8_PANEL_SHA:
        raise SystemExit(f"frozen V8 panel hash mismatch: {actual} - fail closed")
    if not v8_bytes.endswith(b"\n"):
        raise SystemExit("frozen V8 panel does not end with a newline - refusing to append")

    cohort = json.load(open(COHORT))
    dead = cohort["members"]["DEAD_EVIDENCED"]
    sector_of = {m["cik"]: m.get("sector") or "" for m in dead}

    rows = []
    per_cik = {}
    facts_absent = []
    for m in dead:
        cik = m["cik"]
        path = f"{FACTS_DIR}/{cik}.json"
        if not os.path.exists(path):
            facts_absent.append(cik)
            continue
        n = 0
        for record in _records_for(path):
            eff_raw = record.effective_time_utc
            eff_day = (parse_iso_utc(str(eff_raw)) if eff_raw else parse_iso_utc(str(record.event_time_utc))).date()
            avail_day = parse_iso_utc(str(record.available_time_utc)).date()
            row = {
                "e": cik,
                "s": sector_of.get(cik, ""),
                "f": record.field,
                "u": record.unit,
                "v": record.value,
                "eff": eff_day.isoformat(),
                "avail": avail_day.isoformat(),
            }
            ev_day = parse_iso_utc(str(record.event_time_utc)).date()
            if ev_day != eff_day:
                row["evd"] = ev_day.isoformat()
            rows.append(row)
            n += 1
        per_cik[cik] = n

    rows.sort(key=lambda r: (r["e"], r["f"], r["eff"], r["avail"], str(r["v"])))
    os.makedirs(os.path.dirname(PANEL_OUT), exist_ok=True)
    with open(PANEL_OUT, "wb") as out:
        out.write(v8_bytes)
        for r in rows:
            out.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
            out.write(b"\n")
    new_sha = hashlib.sha256(open(PANEL_OUT, "rb").read()).hexdigest()
    facts_manifest = {
        "schema": "stocks_free_v9_run/p0c_v9_panel_manifest@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (PLAN_stocks_v9 sec3 P0c)",
        "parent_panel": {
            "path_source": V8_PANEL,
            "sha256": actual,
            "role": "frozen V8 evidence, byte-identical prefix; never modified",
        },
        "panel_out": PANEL_OUT,
        "panel_out_sha256": new_sha,
        "panel_rows_dead_appended": len(rows),
        "per_cik_rows": per_cik,
        "dead_ciks_total": len(dead),
        "companyfacts_files_missing": facts_absent,
        "facts_absent_sha_note": "companyfacts payloads absent (no XBRL) are recorded in per_cik_rows as 0 or in companyfacts_files_missing",
        "sector_rule": "P0b SIC->SPDR-sector map; UNMAPPED filers carry empty s and are excluded from sector grouping downstream (count recorded)",
        "row_schema": "identical to stocks_free_v6_run/p0a_multivintage_panel_manifest@1 row_schema",
        "normalizer": SANITIZER_VERSION,
        "raw_companyfacts_hashes": {
            fn: hashlib.sha256(open(os.path.join(FACTS_DIR, fn), "rb").read()).hexdigest()
            for fn in sorted(os.listdir(FACTS_DIR)) if fn.endswith(".json")
        },
    }
    json.dump(facts_manifest, open(MANIFEST_OUT, "w"), indent=1)
    print(json.dumps({"dead_rows": len(rows), "new_panel_sha256": new_sha,
                      "ciks_with_rows": sum(1 for n in per_cik.values() if n),
                      "manifest": MANIFEST_OUT}))


if __name__ == "__main__":
    {"pull-companyfacts": pull_companyfacts, "emit": emit}[sys.argv[1]]()
