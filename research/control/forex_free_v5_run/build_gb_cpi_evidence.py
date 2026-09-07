#!/usr/bin/env python3
"""V5-P0a GB/ONS per-print CPI release-date evidence builder.

Fetches every ONS 'Consumer price inflation, UK' bulletin page for reference
months 2018-01..2025-08 (S0 window 2018-04-04..2025-07-24 plus margin), parses
the official 'Release date:' field, archives bytes + sha256.

Keyless official channel only. Paced 4s to respect ONS rate limits (measured
429 at ~6 rapid requests; p7+ recovered with pacing).
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARC = BASE / "cpi_calendar_archives" / "GB" / "bulletins"
ARC.mkdir(parents=True, exist_ok=True)
UA = "my-quantitative-research/1.0 (keyless official evidence probe)"
LISTING = "https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/consumerpriceinflation/previousreleases"

MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def fetch(url, out: Path):
    r = subprocess.run(
        ["curl", "-sS", "-L", "--max-time", "60", "-A", UA, "-o", str(out), "-w",
         "%{http_code} %{size_download}", url],
        capture_output=True, text=True, timeout=90)
    parts = r.stdout.split()
    code, size = int(parts[0]), int(parts[1])
    return code, size


def main():
    # Step 1: discover slugs from the paginated official listing (paged 1..14,
    # already partially archived). Refetch here for a complete in-run listing.
    slugs = {}  # slug -> listing_page
    for p in range(1, 15):
        out = ARC / f"listing_p{p}.html"
        code, size = fetch(f"{LISTING}?q=&limit=10&sort=release_date&page={p}", out)
        print(f"listing p{p}: HTTP {code} {size}B", flush=True)
        if code == 429:
            time.sleep(30)
            code, size = fetch(f"{LISTING}?q=&limit=10&sort=release_date&page={p}", out)
            print(f"  retry p{p}: HTTP {code} {size}B", flush=True)
        if code != 200:
            print(f"  FATAL listing page {p} not 200", flush=True)
            sys.exit(2)
        html = out.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(
                r"consumerpriceinflation/([a-z]+20\d\d)", html):
            per = m.group(1)
            mm = re.match(r"([a-z]+)(\d{4})", per)
            if mm and mm.group(1) in MONTHS:
                slugs.setdefault(per, p)
        time.sleep(4)

    # Step 2: select reference months 2018-01..2025-08
    targets = []
    for per in sorted(slugs):
        mm = re.match(r"([a-z]+)(\d{4})", per)
        mo, yr = mm.group(1), int(mm.group(2))
        if 2018 <= yr <= 2025 and not (yr == 2025 and MONTHS.index(mo) > 7):
            targets.append(per)
    targets.sort(key=lambda per: (int(per[-4:]), MONTHS.index(per[:-4])))
    print(f"discovered {len(slugs)} bulletins total; {len(targets)} in target range", flush=True)

    # Step 3: fetch each bulletin page, parse Release date
    rows = []
    for i, per in enumerate(targets):
        out = ARC / f"bulletin_{per}.html"
        if out.exists() and out.stat().st_size > 20000:
            code, size = 200, out.stat().st_size
        else:
            code, size = fetch(
                f"https://www.ons.gov.uk/economy/inflationandpriceindices/"
                f"bulletins/consumerpriceinflation/{per}", out)
        if code == 429:
            time.sleep(30)
            code, size = fetch(
                f"https://www.ons.gov.uk/economy/inflationandpriceindices/"
                f"bulletins/consumerpriceinflation/{per}", out)
        if code != 200 or size < 20000:
            print(f"{per}: HTTP {code} {size}B UNEXPECTED", flush=True)
            rows.append({"reference_period": per, "class": "UNEVIDENCED",
                         "http_code": code, "note": "fetch failure, archived bytes kept"})
            time.sleep(4)
            continue
        html = out.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Release date:?\s*(?:</[^>]+>\s*<[^>]+>)?\s*"
                      r"(\d{1,2}\s+[A-Z][a-z]+\s+20\d\d)", html)
        nxt = re.search(r"Next release:?\s*(?:</[^>]+>\s*<[^>]+>)?\s*"
                        r"(\d{1,2}\s+[A-Z][a-z]+\s+20\d\d|Not scheduled)", html)
        rel = m.group(1) if m else None
        sha = hashlib.sha256(out.read_bytes()).hexdigest()
        rows.append({
            "reference_period": per,
            "class": "EVIDENCED" if rel else "UNEVIDENCED",
            "release_date_display": rel,
            "next_release_display": nxt.group(1) if nxt else None,
            "source_url": f"https://www.ons.gov.uk/economy/inflationandpriceindices/"
                          f"bulletins/consumerpriceinflation/{per}",
            "archive_path": str(out.relative_to(BASE)),
            "archive_sha256": sha,
            "http_code": code,
        })
        print(f"[{i+1}/{len(targets)}] {per}: {rel} ({code})", flush=True)
        time.sleep(4)

    (BASE / "gb_ons_cpi_release_dates.json").write_text(json.dumps(rows, indent=1))
    ev = [r for r in rows if r["class"] == "EVIDENCED"]
    print(f"DONE: {len(ev)}/{len(rows)} EVIDENCED", flush=True)


if __name__ == "__main__":
    main()
