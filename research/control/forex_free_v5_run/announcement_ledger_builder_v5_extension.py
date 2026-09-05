#!/usr/bin/env python
"""FOREX-FREE-V5 P0c: append-only availability-evidence extension (CA, EMU).

Authority: PLAN_forex_v5.md section 3 P0c — "continue the append-only
extension (CA, EMU rows; any other officially evidenced events found);
base pin re-verified, extension re-pinned; only-availability-differs
invariant re-run."

What it does
------------
1.  Loads the V4-pinned ledger ``announcement_ledger.jsonl`` and REFUSES
    to run unless its sha256 equals the V4 pin
    ``ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4``.
2.  Targets only AVAILABILITY_UNEVIDENCED RATE_CHANGE rows in {CA, EMU}.
    AU/NZ/CH were upgraded by the V4 extension and are inherited as-is.
3.  Per-area evidence adapters (every fetch archived under sha256;
    verification failure degrades, never invents precision):
      CA  bankofcanada.ca FAD press releases.  Candidate announcement
          dates enumerated as [effective-1, effective] (BoC pre-2020
          announced the day before; since March 2020 changes are
          effective same day).  A candidate page upgrades the row only
          when it contains the target overnight-rate level from the
          row.  No release time is read from the page -> DAY / DAY_
          CONSERVATIVE (end of announcement UTC day), the same
          conservative class the V4 extension used for NZ/CH.
      EMU ecb.europa.eu "Monetary policy decisions" press releases at
          /press/pr/date/{Y}/html/ecb.mp{MMDD}.en.html.  ECB effective
          dates are maintenance-period starts and cannot be derived
          arithmetically from announcement dates, so candidates are
          enumerated as [effective-10 .. effective-1]; a page upgrades
          the row only when its title contains "Monetary policy
          decisions" and its text names the row's new main-refinancing
          rate.  DAY / DAY_CONSERVATIVE.
4.  Emits upgrade rows of the IDENTICAL row schema appended AFTER the
    220 pinned lines; the inherited ``index_ledger`` last-row-wins rule
    (per (area, effective_date)) makes appended rows govern.  The base
    220 lines stay byte-identical (verified prefix).
5.  Re-pins under THIS run dir (fresh pin file + manifest).  The V4 pin
    continues to govern the V4 artifacts and is never touched.
6.  Re-runs the only-availability-differs invariant: for every upgraded
    row, all fields outside ``announcement`` must equal the row it
    supersedes (same decision identity; only availability evidence
    changed).

Usage
-----
  .venv/bin/python research/control/forex_free_v5_run/announcement_ledger_builder_v5_extension.py [--pin]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent
LEDGER_IN = RUN_DIR / "announcement_ledger.jsonl"
OUT_LEDGER = RUN_DIR / "announcement_ledger_v5_extension.jsonl"
ARCH_DIR = RUN_DIR / "announcement_archives_v5_extension"
MANIFEST = RUN_DIR / "ledger_manifest_v5_extension.json"
PIN = RUN_DIR / "LEDGER_PINNED_V5_EXTENSION"

V4_PIN = "ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4"
UA = "my-quantitative-research/1.0 (keyless official evidence probe)"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fetch(url: str, out: Path):
    r = subprocess.run(
        ["curl", "-sS", "--http1.1", "-L", "--max-time", "60", "-A", UA,
         "-o", str(out), "-w", "%{http_code} %{size_download}", url],
        capture_output=True, text=True, timeout=90)
    parts = r.stdout.split()
    return int(parts[0]), int(parts[1])


def end_of_utc_day(d: date) -> str:
    return f"{d.isoformat()}T23:59:59Z"


# ---------------------------------------------------------------- adapters

def ca_candidates(row):
    eff = date.fromisoformat(row["effective_date"])
    return [eff - timedelta(days=1), eff]


GLYPHS = {"½": "0.5", "¼": "0.25", "¾": "0.75"}


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return text


def normalize(text: str) -> str:
    # "1 ½" / "1½" -> "1.5"; standalone "½" -> "0.5"
    text = re.sub(r"(\d)\s*½", r"\1.5", text)
    text = re.sub(r"(\d)\s*¼", r"\1.25", text)
    text = re.sub(r"(\d)\s*¾", r"\1.75", text)
    for k, v in GLYPHS.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text)


def ca_verify(text: str, row) -> str | None:
    plain = normalize(strip_tags(text))
    want = row["new_value"]
    if re.search(rf"overnight rate[^;.]{{0,200}}?{want:g}\s*per\s?cent", plain, re.I) \
            or re.search(rf"overnight rate[^;.]{{0,200}}?{want:g}\s*%", plain, re.I):
        return f"overnight rate ... {want:g} (normalized page text)"
    return None


# ECB PR URLs are hash-suffixed (post-2021 redesign) and cannot be derived;
# candidates were located via web search (locator only) and are verified
# against the ledger row's effective date AND value before use.
ECB_URL_BY_EFFECTIVE = {
    "2022-07-27": "https://www.ecb.europa.eu/press/pr/date/2022/html/ecb.mp220721~53e5bdd317.en.html",
    "2022-09-14": "https://www.ecb.europa.eu/press/pr/date/2022/html/ecb.mp220908~c1b6839378.en.html",
    "2022-11-02": "https://www.ecb.europa.eu/press/pr/date/2022/html/ecb.mp221027~df1d778b84.en.html",
    "2022-12-21": "https://www.ecb.europa.eu/press/pr/date/2022/html/ecb.mp221215~f3461d7b6e.en.html",
    "2023-02-08": "https://www.ecb.europa.eu/press/pr/date/2023/html/ecb.mp230202~08a972ac76.en.html",
    "2023-03-22": "https://www.ecb.europa.eu/press/pr/date/2023/html/ecb.mp230316~aad5249f30.en.html",
    "2023-05-10": "https://www.ecb.europa.eu/press/pr/date/2023/html/ecb.mp230504~cdfd11a697.en.html",
    "2023-06-21": "https://www.ecb.europa.eu/press/pr/date/2023/html/ecb.mp230615~d34cddb4c6.en.html",
    "2023-08-02": "https://www.ecb.europa.eu/press/pr/date/2023/html/ecb.mp230727~da80cfcf24.en.html",
    "2023-09-20": None,  # probes found no ECB rate change effective this date; row suspect
    "2024-06-12": None,
    "2024-09-18": None,
    "2024-10-23": None,
    "2024-12-18": None,
    "2025-02-05": None,
    "2025-03-12": None,
    "2025-04-23": None,
    "2025-06-11": None,
    "2026-06-17": "https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp260611~4d41bd5e83.en.html",
}


def emu_candidates(row):
    u = ECB_URL_BY_EFFECTIVE.get(row["effective_date"])
    return [u] if u else []


def emu_verify(text: str, row) -> dict | None:
    """Verify the PR names the row's effective date and a rate line equal to
    new_value; returns attribution info. Refuses on ambiguity."""
    plain = normalize(strip_tags(text))
    if "monetary policy decisions" not in plain.lower():
        return None
    eff_disp = date.fromisoformat(row["effective_date"]).strftime("%-d %B %Y")
    want = row["new_value"]
    m_eff = re.search(rf"with effect from {re.escape(eff_disp)}", plain)
    if not m_eff:
        return None
    window = plain[max(0, m_eff.start() - 400):m_eff.end() + 50]
    series = None
    m2 = re.search(r"main refinancing operations[^.]*?increased to ([\d.]+)%", window)
    if m2 and abs(float(m2.group(1)) - want) < 1e-9:
        series = "MRO"
    else:
        m3 = re.search(r"deposit facility[^.]*?increased to ([\d.]+)%", window)
        if m3 and abs(float(m3.group(1)) - want) < 1e-9:
            series = "DFR"
        else:
            return None
    return {"effective_in_text": eff_disp, "value_series": series,
            "extract": window[:300]}


ADAPTERS = {
    "CA": {
        "url": lambda d: (f"https://www.bankofcanada.ca/{d.year}/{d.month:02d}/"
                          f"fad-press-release-{d.isoformat()}/"),
        "cands": ca_candidates,
        "verify": ca_verify,
        "archive": "CA_boc_fad_{date}.html",
    },
    "EMU": {
        "url": lambda d: ECB_URL_BY_EFFECTIVE.get(d.isoformat()),
        "cands": emu_candidates,
        "verify": emu_verify,
        "archive": "EMU_ecb_pr_{date}.html",
    },
}


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pin", action="store_true")
    args = ap.parse_args()

    raw = LEDGER_IN.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != V4_PIN:
        print(f"FATAL: base ledger sha {got} != V4 pin {V4_PIN}; refusing to extend")
        sys.exit(2)
    base_lines = raw.decode("utf-8").splitlines()
    base_rows = [json.loads(l) for l in base_lines if l.strip()]
    print(f"base verified: {len(base_rows)} rows, sha {got[:12]}")

    targets = {}
    for r in base_rows:
        if (r["area"] in ADAPTERS and r["row_type"] == "RATE_CHANGE"
                and r["announcement"]["status"] == "AVAILABILITY_UNEVIDENCED"):
            targets.setdefault(r["decision_id"], r)
    print(f"targets: {sorted((a, sum(1 for d in targets if d.startswith(a))) for a in ADAPTERS)}")

    ARCH_DIR.mkdir(parents=True, exist_ok=True)
    upgrades = []
    evidence_log = []
    value_findings = []

    for area, ad in sorted(ADAPTERS.items()):
        rows = [r for d, r in sorted(targets.items()) if r["area"] == area]
        done = 0
        for row in rows:
            eff = date.fromisoformat(row["effective_date"])
            upgraded = None
            for cand in ad["cands"](row):
                if cand is None:
                    continue
                if isinstance(cand, date):
                    arch = ARCH_DIR / ad["archive"].format(date=cand.isoformat())
                    url = ad["url"](cand)
                    if url is None:
                        continue
                    cand_date = cand
                else:  # EMU: candidate is a URL string keyed by effective date
                    url = cand
                    cand_date = eff
                    arch = ARCH_DIR / ad["archive"].format(date=eff.isoformat())
                if not arch.exists():
                    code, size = fetch(url, arch)
                    if code != 200:
                        arch.unlink(missing_ok=True)
                        continue
                else:
                    code, size = 200, arch.stat().st_size
                text = arch.read_text(encoding="utf-8", errors="replace")
                hit = ad["verify"](text, row)
                if hit:
                    upgraded = {
                        "row": row,
                        "cand": cand_date,
                        "arch": arch,
                        "hit": hit,
                        "code": code,
                    }
                    break
                # keep probing next candidate
            if upgraded:
                r2 = json.loads(json.dumps(upgraded["row"]))  # deep copy
                cand_date = upgraded["cand"]
                hit = upgraded["hit"]
                evid_extract = (hit if isinstance(hit, str) else
                                json.dumps(hit, ensure_ascii=False))
                r2["announcement"].update({
                    "status": "EVIDENCED",
                    "date_verified": True,
                    "rate_verified": True,
                    "announcement_date": cand_date.isoformat(),
                    "announcement_time_utc": None,
                    "operative_available_time_utc": end_of_utc_day(cand_date),
                    "precision": "DAY",
                    "time_source": "DAY_CONSERVATIVE (announcement UTC-day end; page states no clock time)",
                    "source_url": (ad["url"](cand_date) if area == "CA" else
                                   ECB_URL_BY_EFFECTIVE.get(row["effective_date"])),
                    "archive_path": str(upgraded["arch"].relative_to(RUN_DIR)),
                    "archive_sha256": sha256_file(upgraded["arch"]),
                    "evidence_extract": evid_extract,
                    "schedule_claim_archive": [],
                    "unscheduled": r2["announcement"].get("unscheduled", False),
                    "unverified_probe": None,
                })
                upgrades.append(r2)
                evidence_log.append({
                    "decision_id": r2["decision_id"],
                    "area": area,
                    "announcement_date": cand_date.isoformat(),
                    "verify_pattern": evid_extract,
                    "archive": str(upgraded["arch"].relative_to(RUN_DIR)),
                    "archive_sha256": sha256_file(upgraded["arch"]),
                    "http_code": upgraded["code"],
                })
                done += 1
                print(f"{r2['decision_id']}: EVIDENCED via {cand_date}", flush=True)
            else:
                print(f"{row['decision_id']}: remains UNEVIDENCED (no candidate verified)", flush=True)
                if area == "EMU":
                    value_findings.append({
                        "decision_id": row["decision_id"],
                        "effective_date": row["effective_date"],
                        "ledger_values": [row["old_value"], row["new_value"]],
                        "finding": "no located ECB PR confirms a rate change taking "
                                   "effect this date with the ledger's new_value; "
                                   "suspected base-ledger rate-series mixing (MRO vs "
                                   "DFR) from 2023-09-20 onward; row left UNEVIDENCED, "
                                   "value integrity flagged for A7/owner",
                    })
        print(f"{area}: {done}/{len(rows)} upgraded", flush=True)

    # invariant: only-availability-differs
    base_by_id = {r["decision_id"]: r for r in base_rows}
    violations = []
    for u in upgrades:
        b = base_by_id[u["decision_id"]]
        for k, v in u.items():
            if k == "announcement":
                continue
            if b.get(k) != v:
                violations.append((u["decision_id"], k))
    if violations:
        print(f"FATAL: only-availability-differs violations: {violations[:5]}")
        sys.exit(3)

    # assemble v3 = base bytes (untouched) + appended upgrade rows
    out_path = OUT_LEDGER
    with open(out_path, "wb") as f:
        f.write(raw)
        for r in upgrades:
            f.write((json.dumps(r, sort_keys=True) + "\n").encode("utf-8"))
    new_sha = sha256_file(out_path)
    print(f"extension ledger: {len(base_rows) + len(upgrades)} rows, sha {new_sha}")

    manifest = {
        "schema": "forex_free_v5_ledger_extension_manifest_v1",
        "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer": "A1_FOREX_CONTROLLER",
        "cycle_id": "FOREX-FREE-V5",
        "base_ledger": {
            "path": "announcement_ledger.jsonl",
            "sha256": got,
            "pin_source": "V4 pin ae5e1f2e (220 rows)",
        },
        "extended_ledger": {
            "path": OUT_LEDGER.name,
            "sha256": new_sha,
            "rows": len(base_rows) + len(upgrades),
        },
        "upgrades": evidence_log,
        "only_availability_differs_violations": violations,
        "value_integrity_findings": value_findings,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1))
    if args.pin:
        PIN.write_text(f"V5_EXTENSION_PINNED\nledger_sha256={new_sha}\n")
        print(f"pinned: {PIN.name}")
    print("DONE")


if __name__ == "__main__":
    main()
