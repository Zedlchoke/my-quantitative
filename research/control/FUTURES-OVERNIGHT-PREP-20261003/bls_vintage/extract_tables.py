#!/usr/bin/env python3
"""Extract schedule tables + any alert/notice text from captured BLS archived pages.
Writes captures/extracted_tables.json
"""
import json
import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(BASE, "captures")

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def rows_from(body: str):
    """Return list of (reference_month_text, release_date_text, release_time_text)."""
    # main table: <table class="release-list">
    m = re.search(r'<table class="release-list">(.*?)</table>', body, re.S)
    if not m:
        return []
    tbl = m.group(1)
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tbl, re.S):
        cells = [re.sub(r'<[^>]+>', '', c).strip()
                 for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if len(cells) >= 3:
            rows.append((cells[0], cells[1], cells[2]))
        elif len(cells) == 2:
            rows.append((cells[0], cells[1], ""))
    return rows


def notices_from(body: str):
    """Heuristic notice text: alert/emphasis blocks, shutdown/delay/update wording."""
    found = []
    # strip scripts/styles
    b = re.sub(r'<script.*?</script>', ' ', body, flags=re.S)
    b = re.sub(r'<style.*?</style>', ' ', b, flags=re.S)
    b = re.sub(r'<!--.*?-->', ' ', b, flags=re.S)
    # explicit notice containers
    for cls in ("alert", "notice", "banner", "message", "emergency", "warning"):
        for m in re.finditer(r'<[^>]*class="[^"]*%s[^"]*"[^>]*>(.*?)</div>' % cls, b, re.S | re.I):
            txt = re.sub(r'<[^>]+>', ' ', m.group(1))
            txt = re.sub(r'\s+', ' ', txt).strip()
            if txt:
                found.append((f"class~{cls}", txt[:600]))
    # keyword scan in visible text
    vis = re.sub(r'<[^>]+>', ' ', b)
    vis = re.sub(r'&nbsp;?', ' ', vis)
    vis = re.sub(r'&#8217;', "'", vis)
    vis = re.sub(r'&amp;', '&', vis)
    vis = re.sub(r'\s+', ' ', vis)
    for kw in ("lapse in appropriation", "government shutdown", "shutdown",
               "delayed", "delay", "rescheduled", "postponed",
               "schedule has been updated", "revised schedule", "schedule change",
               "will not be published", "will not be released", "unavailable"):
        for m in re.finditer(re.escape(kw), vis, re.I):
            s = max(0, m.start() - 260)
            found.append((f"kw:{kw}", vis[s:m.end() + 260].strip()))
    # dedupe
    out = []
    seen = set()
    for tag, txt in found:
        k = txt[:120]
        if k not in seen:
            seen.add(k)
            out.append({"where": tag, "text": txt})
    return out


def main():
    result = {}
    for path in sorted(glob.glob(os.path.join(CAP, "wb_*.htm"))):
        name = os.path.basename(path)
        body = open(path, encoding="utf-8", errors="replace").read()
        t = re.search(r'<title>(.*?)</title>', body, re.S)
        ts = re.match(r'wb_(\d{14})_', name).group(1)
        series = "cpi" if name.endswith("_cpi.htm") else "empsit"
        result[name] = {
            "snapshot_ts": ts,
            "series": series,
            "title": t.group(1).strip() if t else None,
            "rows": [
                {"ref": r[0], "date": r[1], "time": r[2]} for r in rows_from(body)
            ],
            "notices": notices_from(body),
        }
    with open(os.path.join(CAP, "extracted_tables.json"), "w") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    for name, d in result.items():
        print(f"== {name} | {d['title']}")
        for r in d["rows"]:
            print(f"   {r['ref']:<16} -> {r['date']:<16} {r['time']}")
        if d["notices"]:
            for n in d["notices"]:
                print(f"   NOTICE[{n['where']}]: {n['text'][:300]}")
        print()


if __name__ == "__main__":
    main()
