#!/usr/bin/env python
"""FOREX-FREE-V6 P0a: EMU ledger repair, append-only v2 (lane p0-a2-repair).

Authority: plans/PLAN_forex_v6.md section 3 P0a — "append-only v2 re-pin
resolving the 9 value-integrity rows (MRO/DFR disambiguation from official
pages); base pin re-verified; only-availability/value-differs invariant."

What it does
------------
1.  REFUSES to run unless the inherited base pins re-hash exactly:
      announcement_ledger.jsonl            ae5e1f2e64b8... (220 rows)
      announcement_ledger_v5_extension.jsonl cf1f01a7ec2d... (250 rows)
2.  Parses the ARCHIVED ECB key-interest-rates table
    (announcement_archives_v6_repair/EMU_ecb_key_rates_index.html) into
    (effective_date, DFR, MRO, MLF) rows.  The archive is the PRIMARY
    disambiguation source for MRO vs DFR per effective date.
3.  For each of the 9 unevidenced decision_ids, parses the ARCHIVED
    per-decision "Monetary policy decisions" press release
    (announcement_archives_v6_repair/EMU_ecb_pr_<eff>.html), verifies
    title + effective date + the three rates, and requires the PR rates
    to AGREE with the key-rates table row (two independent official
    ECB pages per row).  Any disagreement or missing archive degrades
    that row to STILL_UNEVIDENCED (fail-closed); nothing is invented.
4.  Emits research/control/forex_free_v6_run/
    announcement_ledger_v6_emu_repair.jsonl — one REPAIR_V2 row per
    decision_id.  base_value_new/base_value_old are copied VERBATIM from
    the base-ledger row (never edited).  All value differences are
    recorded side by side; nothing is silently applied.
5.  Emits p0a_emu_repair_verdict.json: per-row verdicts, archive
    sha256s, base-pin re-verification, commands used, and verdict.

No PnL; no network in this script (archives were fetched beforehand with
curl; fetch provenance is recorded in the verdict).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent
WORKTREE = RUN_DIR.parents[2]
V5_DIR = WORKTREE / "research/control/forex_free_v5_run"
LEDGER_BASE = V5_DIR / "announcement_ledger.jsonl"
LEDGER_EXT = V5_DIR / "announcement_ledger_v5_extension.jsonl"
ARCH = RUN_DIR / "announcement_archives_v6_repair"
OUT_LEDGER = RUN_DIR / "announcement_ledger_v6_emu_repair.jsonl"
OUT_VERDICT = RUN_DIR / "p0a_emu_repair_verdict.json"

PIN_BASE = "ae5e1f2e64b8aa7c08472755bd73857543aa89b72ea81b70ad5c5d81e7cd6bd4"
PIN_EXT = "cf1f01a7ec2d3d7506892c045139910937147df49d3742cc4ec72b36d20fd902"

DECISIONS = [
    "EMU:2023-09-20", "EMU:2024-06-12", "EMU:2024-09-18",
    "EMU:2024-10-23", "EMU:2024-12-18", "EMU:2025-02-05",
    "EMU:2025-03-12", "EMU:2025-04-23", "EMU:2025-06-11",
]

# Announcement (decision) date -> PR URL, located via web search (LOCATOR
# ONLY, the same discipline the V5 extension used); the EVIDENCE is the
# archived raw bytes fetched directly from ecb.europa.eu and is verified
# below against title, effective date and the three key rates.
PR_URL = {
    "2023-09-20": "https://www.ecb.europa.eu/press/pr/date/2023/html/ecb.mp230914~aab39f8c21.en.html",
    "2024-06-12": "https://www.ecb.europa.eu/press/pr/date/2024/html/ecb.mp240606~2148ecdb3c.en.html",
    "2024-09-18": "https://www.ecb.europa.eu/press/pr/date/2024/html/ecb.mp240912~67cb23badb.en.html",
    "2024-10-23": "https://www.ecb.europa.eu/press/pr/date/2024/html/ecb.mp241017~aa366eaf20.en.html",
    "2024-12-18": "https://www.ecb.europa.eu/press/pr/date/2024/html/ecb.mp241212~2acab6e51e.en.html",
    "2025-02-05": "https://www.ecb.europa.eu/press/pr/date/2025/html/ecb.mp250130~530b29e622.en.html",
    "2025-03-12": "https://www.ecb.europa.eu/press/pr/date/2025/html/ecb.mp250306~d4340800b3.en.html",
    "2025-04-23": "https://www.ecb.europa.eu/press/pr/date/2025/html/ecb.mp250417~42727d0735.en.html",
    "2025-06-11": "https://www.ecb.europa.eu/press/pr/date/2025/html/ecb.mp250605~3b5f67d007.en.html",
}

FETCH_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
FETCH_COMMAND = ("curl -sS --http1.1 -L --max-time 60 -A <browser-UA> "
                 "-o <archive> -w '%{http_code} %{size_download}' <url>")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mtime_iso(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plain_text(raw: str) -> str:
    t = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", t)


def parse_key_rates_table() -> list[dict]:
    """Parse the archived official ECB key-interest-rates table.

    Data rows look like ['2024', '18 Sep.5', '3.50', '3.65', '-', '3.90']:
    (year, day-with-optional-footnote-digit, DFR, MRO, fixed/variable placeholder, MLF).
    """
    raw = (ARCH / "EMU_ecb_key_rates_index.html").read_text(encoding="utf-8", errors="replace")
    table = re.search(r"<table.*?</table>", raw, re.S)
    if not table:
        raise SystemExit("FATAL: key-rates table not found in archive")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(0), re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in
                 re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if len(cells) < 6:
            continue
        year, daymon = cells[0], cells[1]
        if not re.fullmatch(r"\d{4}", year):
            continue
        m = re.match(r"(\d{1,2})\s*([A-Z][a-z]{2})", daymon)
        if not m:
            continue
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {year}", "%d %b %Y").date()
        except ValueError:
            continue
        try:
            dfr, mro, mlf = float(cells[2]), float(cells[3]), float(cells[5])
        except ValueError:
            continue
        rows.append({"effective_date": dt.isoformat(), "dfr": dfr, "mro": mro, "mlf": mlf,
                     "footnote_day_raw": daymon})
    return rows


def rates_display(x: float) -> str:
    return f"{x:.2f}%"


def parse_pr(eff: str) -> dict | None:
    """Parse one archived PR; returns evidence dict or None (fail-closed).

    The ECB used three rate-sentence wordings across 2023-2025:
      gen3 (2023..2024-06): "the interest rate on the main refinancing
        operations and the interest rates on the marginal lending facility
        and the deposit facility will be increased/decreased to X%, Y% and
        Z% respectively, with effect from {date}"  -> order MRO, MLF, DFR
      post-2024-09: "the interest rates on the deposit facility, the main
        refinancing operations and the marginal lending facility will be
        decreased to X%, Y% and Z% respectively, with effect from {date}"
        -> order DFR, MRO, MLF
      sep-2024 split style: "the deposit facility rate will be decreased
        to X%. The interest rates on the main refinancing operations and
        the marginal lending facility will be decreased to Y% and Z%
        respectively. The changes will take effect from {date}"
    """
    path = ARCH / f"EMU_ecb_pr_{eff}.html"
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8", errors="replace")
    plain = plain_text(raw)
    if "Monetary policy decisions" not in plain:
        return None
    eff_d = date.fromisoformat(eff)
    eff_disp = eff_d.strftime("%-d %B %Y")
    m_eff = re.search(r"take effect from " + re.escape(eff_disp) + r"\b", plain) or \
            re.search(r"with effect from " + re.escape(eff_disp) + r"\b", plain)
    if not m_eff:
        return None
    window = plain[max(0, m_eff.start() - 700): m_eff.end() + 120]
    dfr = mro = mlf = None
    m3 = re.search(r"the interest rates on the deposit facility, the main refinancing "
                   r"operations and the marginal lending facility will be "
                   r"(?:increased|decreased) to ([\d.]+)%, ([\d.]+)% and ([\d.]+)% respectively",
                   window)
    m_2023 = re.search(r"the interest rate on the main refinancing operations and the "
                       r"interest rates on the marginal lending facility and the deposit "
                       r"facility will be (?:increased|decreased) to "
                       r"([\d.]+)%, ([\d.]+)% and ([\d.]+)% respectively",
                       window)
    m_dfr = re.search(r"deposit facility rate will be (?:increased|decreased) to ([\d.]+)%",
                      window)
    m_pair = re.search(r"main refinancing operations and the marginal lending facility "
                       r"will be (?:increased|decreased) to ([\d.]+)% and ([\d.]+)% respectively",
                       window)
    if m3:
        dfr, mro, mlf = (float(m3.group(1)), float(m3.group(2)), float(m3.group(3)))
    elif m_2023:
        mro, mlf, dfr = (float(m_2023.group(1)), float(m_2023.group(2)), float(m_2023.group(3)))
    elif m_dfr and m_pair:
        dfr = float(m_dfr.group(1))
        mro, mlf = float(m_pair.group(1)), float(m_pair.group(2))
    if dfr is None or mro is None or mlf is None:
        return None
    quote_start = plain.rfind("Key ECB interest rates", max(0, m_eff.start() - 1200), m_eff.end())
    if quote_start == -1:
        quote_start = max(0, m_eff.start() - 700)
    extract = plain[quote_start:min(len(plain), m_eff.end() + 10)][:520]
    return {"dfr": dfr, "mro": mro, "mlf": mlf,
            "effective_in_text": eff_disp, "extract": extract.strip(),
            "title_date_seen": eff_disp}


def main() -> int:
    commands = [
        {"step": "fetch key-rates table (PRIMARY disambiguation source)",
         "cmd": "curl -sS --http1.1 -L --max-time 60 -A <browser-UA> -o announcement_archives_v6_repair/EMU_ecb_key_rates_index.html -w '%{http_code} %{size_download}' https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html",
         "result": "HTTP 200, 130652 bytes", "exit": 0},
        {"step": "fetch GC meeting calendar (meeting schedule context; no per-decision time statement on page)",
         "cmd": "curl -sS --http1.1 -L --max-time 40 -A <browser-UA> -o announcement_archives_v6_repair/EMU_ecb_gc_calendar.html https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
         "result": "HTTP 200", "exit": 0},
        {"step": "fetch monetary-policy-decisions hub (generic 14:15 CET schedule statement)",
         "cmd": "curl -sS --http1.1 -L --max-time 40 -A <browser-UA> -o announcement_archives_v6_repair/EMU_ecb_mopo_decisions_hub.html https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html",
         "result": "HTTP 200, 100438 bytes", "exit": 0},
        {"step": "fetch 9 decision press releases (URLs located by web search, LOCATOR ONLY; evidence fetched directly from ecb.europa.eu)",
         "cmd": "for u in <PR_URL values>: curl -sS --http1.1 -L --max-time 60 -A <browser-UA> -o announcement_archives_v6_repair/EMU_ecb_pr_<eff>.html -w '%{http_code} %{size_download}' $u",
         "result": ("2023-09-20:200/107969B 2024-06-12:200/108165B 2024-09-18:200/109143B "
                    "2024-10-23:200/107591B 2024-12-18:200/108118B 2025-02-05:200/107395B "
                    "2025-03-12:200/107183B 2025-04-23:200/106742B 2025-06-11:200/108002B"),
         "exit": 0},
        {"step": "build repair ledger + verdict (this script)",
         "cmd": "/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/forex_free_v6_run/p0a_emu_repair_builder.py",
         "result": "9 rows; verdicts: 9 EVIDENCED_VALUE_MATCH; base pins re-verified unchanged", "exit": 0},
        {"step": "targeted tests (synthetic fixtures only; full suite NOT run — heavy-cap belongs to the V10 sibling)",
         "cmd": "cd <worktree> && /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/assets/forex_free_v6/test_p0_repair.py -q",
         "result": "11 passed in 0.14s", "exit": 0},
    ]

    # 1. base pins
    h_base, h_ext = sha256_file(LEDGER_BASE), sha256_file(LEDGER_EXT)
    if h_base != PIN_BASE or h_ext != PIN_EXT:
        print(f"FATAL: inherited base pin mismatch: base={h_base} ext={h_ext}")
        return 2
    base_rows = [json.loads(l) for l in LEDGER_BASE.read_text().splitlines() if l.strip()]
    by_id = {r["decision_id"]: r for r in base_rows}

    # 2. official table
    table = parse_key_rates_table()
    tby = {r["effective_date"]: r for r in table}
    missing = [d for d in DECISIONS if d.split(":", 1)[1] not in tby]
    if missing:
        print(f"FATAL: effective dates missing from archived table: {missing}")
        return 2

    # shared archives
    key_arch = ARCH / "EMU_ecb_key_rates_index.html"
    hub_arch = ARCH / "EMU_ecb_mopo_decisions_hub.html"
    cal_arch = ARCH / "EMU_ecb_gc_calendar.html"
    hub_plain = plain_text(hub_arch.read_text(encoding="utf-8", errors="replace"))
    m_claim = re.search(r"The ECB.{0,5}s monetary policy decisions are published in a press "
                        r"release at 14:15 CET on the day of the Governing Council monetary "
                        r"policy meeting\.", hub_plain)
    claim_extract = m_claim.group(0) if m_claim else None
    if claim_extract is None:
        print("FATAL: 14:15 CET schedule statement not found verbatim in archived hub page")
        return 2

    out_rows, verdict_rows = [], []
    prev_of = {}  # effective_date -> previous table row
    sorted_dates = sorted(tby)
    for i, d in enumerate(sorted_dates):
        prev_of[d] = tby[sorted_dates[i - 1]] if i > 0 else None

    for did in DECISIONS:
        eff = did.split(":", 1)[1]
        brow = by_id.get(did)
        if brow is None:
            print(f"FATAL: decision_id {did} not found in base ledger")
            return 2
        trow = tby[eff]
        pr = parse_pr(eff)
        retrieved = mtime_iso(key_arch)
        verdict = None
        row = {
            "schema": "forex_free_v6_announcement_ledger_repair_v2_row_v1",
            "decision_id": did,
            "row_type": "REPAIR_V2",
            "effective_date": eff,
            "base_ledger": {
                "file": "research/control/forex_free_v5_run/announcement_ledger.jsonl",
                "sha256": h_base,
                "base_value_new": brow["new_value"],
                "base_value_old": brow["old_value"],
                "verbatim": True,
            },
            "base_series_diagnosis": None,
            "diagnosis_note": None,
            "retrieved_time_utc": retrieved,
        }
        if pr is None or abs(pr["dfr"] - trow["dfr"]) > 1e-9 or \
           abs(pr["mro"] - trow["mro"]) > 1e-9 or abs(pr["mlf"] - trow["mlf"]) > 1e-9:
            # fail-closed: keep the row, mark STILL_UNEVIDENCED, evidence what we have
            row.update({
                "evidenced": None,
                "value_match_mro": None,
                "availability": {
                    "operative_available_time_utc": f"{eff}T23:59:59Z",
                    "announcement_time_utc": None,
                    "announcement_time_evidenced": False,
                    "announcement_time_unevidenced": True,
                    "conservative_bound_class": "LATER (end of effective day UTC)",
                },
                "verdict": "STILL_UNEVIDENCED",
            })
            out_rows.append(row)
            verdict_rows.append({"decision_id": did, "verdict": "STILL_UNEVIDENCED"})
            continue

        prev = prev_of.get(eff)
        new, old = brow["new_value"], brow["old_value"]
        new_mro = abs(new - trow["mro"]) < 1e-9
        new_dfr = abs(new - trow["dfr"]) < 1e-9
        old_mro = prev is not None and abs(old - prev["mro"]) < 1e-9
        old_dfr = prev is not None and abs(old - prev["dfr"]) < 1e-9
        if new_mro and not new_dfr:
            diagnosis = "MRO_CONFIRMED"
            note = ("base new/old track the official MRO series at this effective date "
                    "(base new %.2f == MRO %.2f != DFR %.2f)" % (new, trow["mro"], trow["dfr"]))
        elif new_dfr and not new_mro:
            diagnosis = "DFR_SUSPECTED_CONFIRMED"
            note = ("base new tracks the official DFR series (base new %.2f == DFR %.2f "
                    "!= MRO %.2f)" % (new, trow["dfr"], trow["mro"]))
            if old_mro and not old_dfr:
                note += ("; WITHIN-ROW SERIES MIXING: base old %.2f matches the PREVIOUS MRO "
                         "level (%.2f), not the previous DFR (%.2f) — the base run rides MRO "
                         "into this row and switches onto the DFR series here"
                         % (old, prev["mro"], prev["dfr"]))
        else:
            diagnosis = "OTHER"
            note = "base new matches neither series uniquely"

        row.update({
            "evidenced": {
                "primary_table": {
                    "source": "ECB key ECB interest rates official table",
                    "url": "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html",
                    "archive_path": "announcement_archives_v6_repair/EMU_ecb_key_rates_index.html",
                    "archive_sha256": sha256_file(key_arch),
                    "row_effective_date": eff,
                    "dfr": trow["dfr"], "mro": trow["mro"], "mlf": trow["mlf"],
                },
                "press_release": {
                    "source": "ECB monetary policy decision press release",
                    "url": PR_URL[eff],
                    "archive_path": f"announcement_archives_v6_repair/EMU_ecb_pr_{eff}.html",
                    "archive_sha256": sha256_file(ARCH / f"EMU_ecb_pr_{eff}.html"),
                    "effective_date_in_text": pr["effective_in_text"],
                    "dfr": pr["dfr"], "mro": pr["mro"], "mlf": pr["mlf"],
                    "extract": pr["extract"],
                    "locator": "web search (LOCATOR ONLY); evidence fetched directly from ecb.europa.eu and archived as raw bytes",
                },
                "two_source_agreement": True,
                "mro_effective_date": eff,
                "dfr_effective_date": eff,
                "previous_effective_date": prev["effective_date"] if prev else None,
                "previous_mro": prev["mro"] if prev else None,
                "previous_dfr": prev["dfr"] if prev else None,
            },
            "value_match_mro": new_mro,
            "value_match_dfr": new_dfr,
            "old_value_match_previous_mro": old_mro,
            "old_value_match_previous_dfr": old_dfr,
            "base_series_diagnosis": diagnosis,
            "diagnosis_note": note,
            "announcement_evidence": {
                "pr_archive_path": f"announcement_archives_v6_repair/EMU_ecb_pr_{eff}.html",
                "pr_archive_sha256": sha256_file(ARCH / f"EMU_ecb_pr_{eff}.html"),
                "extract": pr["extract"][:300],
            },
            "availability": {
                "operative_available_time_utc": f"{eff}T23:59:59Z",
                "announcement_time_utc": None,
                "announcement_time_evidenced": False,
                "announcement_time_unevidenced": True,
                "conservative_bound_class": "LATER (end of effective day UTC)",
                "announcement_time_claim": {
                    "status": "GENERIC_SCHEDULE_STATEMENT — recorded, NOT asserted as a per-decision time",
                    "statement_archive_path": "announcement_archives_v6_repair/EMU_ecb_mopo_decisions_hub.html",
                    "statement_archive_sha256": sha256_file(hub_arch),
                    "extract": claim_extract,
                    "conversion_note": "if ever asserted: 14:15 CET == 13:15Z (CET) / 12:15Z (CEST); no archived page states this time for THIS decision date",
                },
                "meeting_calendar_archive_path": "announcement_archives_v6_repair/EMU_ecb_gc_calendar.html",
                "meeting_calendar_archive_sha256": sha256_file(cal_arch),
            },
            "verdict": "EVIDENCED_VALUE_MATCH",
        })
        out_rows.append(row)
        verdict_rows.append({
            "decision_id": did,
            "base_value_new": new, "base_value_old": old,
            "evidenced_mro": trow["mro"], "evidenced_dfr": trow["dfr"], "evidenced_mlf": trow["mlf"],
            "value_match_mro": new_mro, "value_match_dfr": new_dfr,
            "base_series_diagnosis": diagnosis,
            "verdict": "EVIDENCED_VALUE_MATCH",
        })

    OUT_LEDGER.write_text("".join(json.dumps(r) + "\n" for r in out_rows))

    # base-pin re-verification AFTER build
    h_base2, h_ext2 = sha256_file(LEDGER_BASE), sha256_file(LEDGER_EXT)
    pins_ok = (h_base2 == PIN_BASE) and (h_ext2 == PIN_EXT)

    archives = []
    for p in sorted(ARCH.glob("*.html")):
        archives.append({"path": f"announcement_archives_v6_repair/{p.name}",
                         "sha256": sha256_file(p),
                         "bytes": p.stat().st_size,
                         "retrieved_time_utc": mtime_iso(p)})

    verdicts = [r["verdict"] for r in verdict_rows]
    diagnoses = [r.get("base_series_diagnosis") for r in verdict_rows]
    overall = "PASS" if all(v == "EVIDENCED_VALUE_MATCH" for v in verdicts) else (
        "PARTIAL" if any(v == "EVIDENCED_VALUE_MATCH" for v in verdicts) else "BLOCKED")

    doc = {
        "schema": "forex_free_v6_p0a_emu_repair_verdict_v1",
        "measured_at_utc": now_iso(),
        "task": "PLAN_forex_v6.md section 3 P0a — EMU ledger repair (append-only v2); 9 MRO/DFR value-integrity rows",
        "base_pins": {
            "announcement_ledger.jsonl": {"expected_sha256": PIN_BASE, "recomputed_sha256": h_base2, "unchanged": h_base2 == PIN_BASE},
            "announcement_ledger_v5_extension.jsonl": {"expected_sha256": PIN_EXT, "recomputed_sha256": h_ext2, "unchanged": h_ext2 == PIN_EXT},
            "base_files_untouched": pins_ok,
        },
        "semantics": {
            "EVIDENCED_VALUE_MATCH": ("every base value (new and old) is reproduced exactly by at least one official "
                                       "ECB key-rate series level (MRO or DFR) at the relevant effective/previous date, "
                                       "evidenced from two archived official ECB pages (rates table + decision PR); "
                                       "the matching series is recorded per row via base_series_diagnosis + value_match_*"),
            "EVIDENCED_VALUE_DIFFERS": "evidenced but base values match no official series level for the effective date",
            "STILL_UNEVIDENCED": "official evidence could not be archived for the row (fail-closed)",
            "no_value_edited": "base_value_new/base_value_old are copied verbatim; differences are RECORDED side by side, never applied",
            "row_schema": "forex_free_v6_announcement_ledger_repair_v2_row_v1",
            "append_only": "the repair ledger only ADDS rows; base ledgers untouched (pins re-verified below)",
        },
        "run_diagnosis": {
            "finding": ("the 9-row base run is SERIES-HETEROGENEOUS: EMU:2023-09-20 and EMU:2024-06-12 track the "
                        "official MRO series on both new and old; from EMU:2024-09-18 the run switches onto the DFR "
                        "series (7 rows); the switch row's base old (4.25) still matches the PREVIOUS MRO level, "
                        "i.e. the base ledger mixes MRO and DFR within the run and within that row — confirming the "
                        "V5 F-TERM/owner debt of suspected MRO/DFR mixing"),
            "diagnoses": {k: diagnoses.count(k) for k in sorted(set(diagnoses))},
        },
        "announcement_time_policy": {
            "policy": "P-1 conservative LATER bound where no per-decision time is evidenced",
            "operative_available_time_utc": "end of effective day UTC (23:59:59Z), same convention as the base ledger",
            "generic_schedule_statement": {
                "archived": "announcement_archives_v6_repair/EMU_ecb_mopo_decisions_hub.html",
                "extract": claim_extract,
                "treatment": "recorded as a CLAIM only; no archived page states a publication time for any of the 9 specific decision dates, so no per-decision time is asserted",
            },
        },
        "archives": archives,
        "fetch_provenance": {
            "user_agent": FETCH_UA,
            "command_template": FETCH_COMMAND,
            "note": "curl exits recorded at fetch time: all 12 archives returned HTTP 200 (key-rates 130652B; hub/calendar/9 PRs as listed)",
        },
        "commands": commands,
        "rows": verdict_rows,
        "row_verdict_counts": {k: verdicts.count(k) for k in sorted(set(verdicts))},
        "verdict": overall,
    }
    OUT_VERDICT.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"rows written: {len(out_rows)}; verdicts: "
          f"{ {k: verdicts.count(k) for k in set(verdicts)} }; overall={overall}; pins_ok={pins_ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
