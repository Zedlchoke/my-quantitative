#!/usr/bin/env python3
"""V5-P0a AU/ABS + NZ/StatsNZ per-print CPI release evidence builders.

AU: fetch every CPI release page listed in the official ABS sitemap (the site's
full discoverable set; pre-2023 quarterlies 404 and are recorded as not
discoverable), parse the official 'Released DD/MM/YYYY' field.

NZ: fetch every CPI quarter release page discovered in the official Stats NZ
sitemap, parse the machine-readable 'PublicationDate' field.

Keyless official channels only; paced 3s.
"""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
UA = "my-quantitative-research/1.0 (keyless official evidence probe)"


def fetch(url, out: Path):
    r = subprocess.run(
        ["curl", "-sS", "--http1.1", "-L", "--max-time", "60", "-A", UA,
         "-o", str(out), "-w", "%{http_code} %{size_download}", url],
        capture_output=True, text=True, timeout=90)
    parts = r.stdout.split()
    return int(parts[0]), int(parts[1])


def build_au():
    arc = BASE / "cpi_calendar_archives" / "AU" / "releases"
    arc.mkdir(parents=True, exist_ok=True)
    urls = [l.strip() for l in
            (BASE / "cpi_calendar_archives" / "AU" / "abs_cpi_urls_all.txt").read_text().splitlines()
            if l.strip()]
    rows = []
    for i, u in enumerate(urls):
        slug = u.rstrip("/").rsplit("/", 1)[-1]
        out = arc / f"abs_cpi_{slug}.html"
        if not out.exists():
            code, size = fetch(u, out)
            time.sleep(3)
        else:
            code, size = 200, out.stat().st_size
        if code != 200:
            rows.append({"slug": slug, "class": "UNEVIDENCED", "http_code": code})
            print(f"AU [{i+1}/{len(urls)}] {slug}: HTTP {code}", flush=True)
            continue
        h = out.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?i)Released[^0-9]{0,40}(\d{2})/(\d{2})/(\d{4})", h)
        if m:
            d, mo, y = m.groups()
            rel = f"{y}-{mo}-{d}"
        else:
            rel = None
        rows.append({
            "slug": slug,
            "class": "EVIDENCED" if rel else "UNEVIDENCED",
            "release_date": rel,
            "source_url": u,
            "archive_path": str(out.relative_to(BASE)),
            "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "http_code": code,
        })
        print(f"AU [{i+1}/{len(urls)}] {slug}: {rel}", flush=True)
    (BASE / "au_abs_cpi_release_dates.json").write_text(json.dumps(rows, indent=1))
    print(f"AU DONE: {sum(1 for r in rows if r['class']=='EVIDENCED')}/{len(rows)}", flush=True)


def build_nz():
    arc = BASE / "cpi_calendar_archives" / "NZ" / "releases"
    arc.mkdir(parents=True, exist_ok=True)
    urls = [l.strip() for l in
            (BASE / "cpi_calendar_archives" / "NZ" / "nz_cpi_release_urls.txt").read_text().splitlines()
            if l.strip()]
    rows = []
    for i, u in enumerate(urls):
        slug = u.rstrip("/").rsplit("/", 1)[-1]
        out = arc / f"statsnz_cpi_{slug}.html"
        if not out.exists():
            code, size = fetch(u, out)
            time.sleep(3)
        else:
            code, size = 200, out.stat().st_size
        if code != 200:
            rows.append({"slug": slug, "class": "UNEVIDENCED", "http_code": code})
            print(f"NZ [{i+1}/{len(urls)}] {slug}: HTTP {code}", flush=True)
            continue
        h = out.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"PublicationDate&quot;:&quot;(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})", h)
        if m:
            rel, tm = m.group(1), m.group(2)
        else:
            rel, tm = None, None
        rows.append({
            "slug": slug,
            "class": "EVIDENCED" if rel else "UNEVIDENCED",
            "release_date": rel,
            "release_time_local": tm,
            "source_url": u,
            "archive_path": str(out.relative_to(BASE)),
            "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "http_code": code,
        })
        print(f"NZ [{i+1}/{len(urls)}] {slug}: {rel} {tm}", flush=True)
    (BASE / "nz_statsnz_cpi_release_dates.json").write_text(json.dumps(rows, indent=1))
    print(f"NZ DONE: {sum(1 for r in rows if r['class']=='EVIDENCED')}/{len(rows)}", flush=True)


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "au":
        build_au()
    else:
        build_nz()
