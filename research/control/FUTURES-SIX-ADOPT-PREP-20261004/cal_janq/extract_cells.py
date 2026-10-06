#!/usr/bin/env python
"""CAL-JANQ extraction: build calendar_delta.json + legality_validation.json.

Law: only dated official values from hash-verified archived official captures.
No IMM/3rd-Wednesday rule derivation, no family transplants (class-level
advisory rows are recorded verbatim and are NOT mapped to product codes).
Q5 sibling bytes are re-verified per-use (sha256 + this lane's own parsers).
"""
import gzip
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pypdf
import xlrd

LANE = Path(__file__).resolve().parent
CAP = LANE / "captures"
Q5_CAP = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
    "research/control/FUTURES-P3-QUARANTINE-20261004/cal_permitted/captures"
)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

MC = {"H": "Q1", "M": "Q2", "U": "Q3", "Z": "Q4"}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log_line_for(name: str) -> dict:
    for line in (LANE / "fetch_log.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("capture") == f"captures/{name}":
            return {"log_line_url": r["url"], "log_attempt_outcome": r["outcome"],
                    "log_bytes": r.get("bytes"), "log_utc": r["utc"]}
    raise KeyError(name)


# ---------------------------------------------------------------- captures + expected sha
XLS_2024 = Q5_CAP / "pcal_69_6j_dl_20240904.xls"          # Q5 capture
XLS_2025 = CAP / "pcal_69_6j_dl_20251104.xls"             # this lane
PCA_37 = Q5_CAP / "pcal_37_6a_20230916051415.json"        # Q5 capture
NQ = {t: CAP / f"pcal_146_nq_{t}.json" for t in ("20260304", "20260414", "20260710")}
ADV = {
    "mlk": CAP / "adv_ml_2026_20251013.pdf",
    "pres": CAP / "adv_pres_2026_20251013.pdf",
    "gf": CAP / "adv_gf_2026_20251013.pdf",
    "mem": CAP / "adv_mem_2026_20251013.pdf",
    "jun": CAP / "adv_jun_2026_20251013.pdf",
    "jul4": CAP / "adv_jul4_2026_20251013.pdf",
    "lab": CAP / "adv_lab_2026_20251013.pdf",
    "xmas": CAP / "adv_xmas_2026_20251013.pdf",
    "nye": CAP / "adv_nye_2026_20251013.pdf",
}

VERIFY = {
    "pcal_69_6j_dl_20240904.xls (sibling Q5)": "09a85ef700d02a3f8d58f2d2d13c3157af200b516b133903d3173d38280aee18",
    "pcal_37_6a_20230916051415.json (sibling Q5)": "dad89c317110271cba5c62abd60fb14ece7772aaa104ddb1bb742b461a7b9741",
    "pcal_69_6j_dl_20251104.xls (this lane)": "f4ed45136c76de6d5f116f562d0ea7cb63847d039c222b7aedd09b9392285a45",
    "pcal_146_nq_20260304.json (this lane)": "e49da345cf2aeae4c49d1198e26aaf0737a5186882791b8d2a14bc70b2a16f5d",
    "pcal_146_nq_20260414.json (this lane)": "8a2ccb6f55845e3644c5bbf6cf2b9e74a66637e4c5c279737478fe1ec3e06059",
    "pcal_146_nq_20260710.json (this lane)": "e626a285b959582a2f0262ef874fceb3c25f12c5d178bec17e66b2a69d5b7e62",
}


def verify_all() -> dict:
    out = {}
    for label, want in VERIFY.items():
        p = Q5_CAP / label.split(" (")[0] if "sibling" in label else CAP / label.split(" (")[0]
        got = sha(p)
        out[label] = {"sha256": got, "expected": want, "match": got == want}
        if got != want:
            raise SystemExit(f"SHA MISMATCH {label}: {got} != {want}")
    return out


# ---------------------------------------------------------------- 6J XLS parse
def parse_6j_xls(p: Path) -> dict:
    sh = xlrd.open_workbook(str(p)).sheet_by_index(0)
    hdr = None
    rows = {}
    for i in range(sh.nrows):
        vals = [sh.cell_value(i, j) for j in range(sh.ncols)]
        if vals[0] == "Contract Month":
            hdr = vals
            continue
        if hdr is None or not vals[0]:
            continue
        code = str(vals[1]).strip()
        lt = str(vals[3]).strip()
        rows[code] = {"last_trade": lt, "description": str(vals[0]).strip()}
    return {"sheet_name": sh.name, "n_data_rows": len(rows), "rows": rows}


def qcell(code, lt, sources):
    my = code[2:]
    year = 2000 + int(my[1:])
    q = MC.get(my[0])
    return f"{year}{q}", {
        "status": "OBTAINED", "contract": code, "last_trade_date": lt,
        "last_trade_as_published": lt, "sources": sources,
    }


def build_6j_2026():
    a, b = parse_6j_xls(XLS_2024), parse_6j_xls(XLS_2025)
    src24 = {"path": "sibling:FUTURES-P3-QUARANTINE-20261004/cal_permitted/captures/pcal_69_6j_dl_20240904.xls",
             "sha256": sha(XLS_2024), "wayback_ts": "2024-09-04T18:09:31Z", "sheet": a["sheet_name"],
             "this_lane_reverify": "sha256 match + own xlrd parse (per-use re-verify)",
             "lane_fetch_log": "sibling Q5 fetch_log.jsonl line 77"}
    src25 = {"path": "captures/pcal_69_6j_dl_20251104.xls (this lane)", "sha256": sha(XLS_2025),
             "wayback_ts": "2025-11-04T08:42:17Z", "sheet": b["sheet_name"], **log_line_for("pcal_69_6j_dl_20251104.xls")}
    out = {}
    for code in ("J1H26", "J1M26", "J1U26", "J1Z26"):
        v24, v25 = a["rows"][code]["last_trade"], b["rows"][code]["last_trade"]
        cell, val = qcell(code, v24, [src24, src25])
        val["cross_vintage_agreement"] = (v24 == v25)
        val["second_vintage_last_trade"] = v25
        out[cell] = val
    return out, a, b


def build_6a_2026():
    rows = json.loads(PCA_37.read_text())
    src = {"path": "sibling:FUTURES-P3-QUARANTINE-20261004/cal_permitted/captures/pcal_37_6a_20230916051415.json",
           "sha256": sha(PCA_37), "wayback_ts": "2023-09-16T05:14:15Z",
           "this_lane_reverify": "sha256 match + own json parse (per-use re-verify)",
           "lane_fetch_log": "sibling Q5 fetch_log.jsonl lines 75/78"}
    out = {}
    for code in ("ADH26", "ADM26", "ADU26", "ADZ26"):
        r = next(x for x in rows if x["productCode"] == code)
        cell, val = qcell(code, r["lastTrade"], [src])
        val["cross_vintage_agreement"] = None
        val["vintage_note"] = "single archived vintage (2023-09-16 crawl); no second snapshot exists in CDX"
        out[cell] = val
    return out


def build_nq_expiry():
    srcs = {}
    for t, p in NQ.items():
        raw = p.read_bytes()
        rows = json.loads(gzip.decompress(raw))
        srcs[t] = {"path": f"captures/{p.name} (this lane)", "sha256": sha(p),
                   "wayback_ts": {"20260304": "2026-03-04T04:42:04Z", "20260414": "2026-04-14T10:40:10Z",
                                  "20260710": "2026-07-10T16:21:38Z"}[t],
                   "transport_note": "body served gzip; decompressed locally then json-parsed",
                   **log_line_for(p.name)}
    data = {t: {r["productCode"]: r.get("lastTrade") for r in json.loads(gzip.decompress(p.read_bytes()))}
            for t, p in NQ.items()}
    out = {}
    for code in ("NQH26", "NQM26", "NQU26", "NQZ26"):
        vals = {t: v.get(code) for t, v in data.items() if code in v}
        uniq = set(vals.values())
        cell = f"2026{MC[code[2]]}"
        out[cell] = {
            "status": "OBTAINED", "contract": code,
            "last_trade_date": sorted(uniq)[0], "last_trade_as_published": sorted(uniq)[0],
            "sources": [srcs[t] for t in sorted(vals)],
            "captures_carrying_row": sorted(vals),
            "cross_vintage_agreement": len(uniq) == 1,
        }
    return out


# ---------------------------------------------------------------- advisories
def flat_pdf(p: Path) -> str:
    return re.sub(r"\s+", " ", " ".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(p)).pages)).strip()


def adv_src(key: str) -> dict:
    p = ADV[key]
    names = {"mlk": "mlk-day-holiday-settlement-times-2026.pdf", "pres": "presidents-day-holiday-settlement-times-2026.pdf",
             "gf": "good-friday-holiday-settlement-times-2026.pdf", "mem": "memorial-day-holiday-settlement-times-2026.pdf",
             "jun": "juneteenth-day-settlement-times-2026.pdf", "jul4": "us-independence-day-settlement-times-2026.pdf",
             "lab": "labor-day-holiday-settlement-times-2026.pdf", "xmas": "christmas-holiday-settlement-times-2026.pdf",
             "nye": "new-years-eve-holiday-settlement-times-2027.pdf"}
    ts = {"mlk": "20251013214732", "pres": "20251013214715", "gf": "20251013214632", "mem": "20251013214653",
          "jun": "20251013214651", "jul4": "20251013214657", "lab": "20251013214712", "xmas": "20251013214715",
          "nye": "20251013214642"}[key]
    return {"advisory_file": names[key], "wayback_ts": ts, "capture": f"captures/{p.name} (this lane)",
            "sha256": sha(p), "source": "ARCHIVED_OFFICIAL (cmegroup.com tools-information/holiday-calendar/files/2026/)",
            **log_line_for(p.name)}


def class_rows(flat: str) -> list:
    """Verbatim class-level settlement-time rows, one row per class marker.
    NEVER mapped to product codes."""
    markers = [
        "CME Group December 2yr, 3yr and 5yr Treasury Interest Rate Products",
        "CME Group December Yield Treasury Futures",
        "CME Group Interest Rate Products",
        "Agricultural Products", "Interest Rate Products", "FX Products",
        "Real Estate and Weather Products", "Equity & Crypto Products",
        "Metal Products", "Energy Products", "ClearPort Products",
    ]
    hits = []
    for mname in markers:
        for m in re.finditer(re.escape(mname), flat):
            hits.append((m.start(), mname))
    # drop hits starting inside an earlier longer-marker hit
    hits.sort()
    filtered = []
    for pos, name in hits:
        if filtered and pos < filtered[-1][0] + len(filtered[-1][1]):
            continue
        filtered.append((pos, name))
    stops = [m.start() for m in re.finditer(r"Note:|If you have any questions|\*Dates", flat)]

    def next_stop(after: int) -> int:
        for s in stops:
            if s > after:
                return s
        return len(flat)

    rows = []
    for i, (pos, name) in enumerate(filtered):
        end = filtered[i + 1][0] if i + 1 < len(filtered) else next_stop(pos)
        seg = flat[pos:min(end, next_stop(pos))].strip().rstrip(",")
        rows.append({"class": name, "verbatim": seg[:400]})
    return rows


WINDOWS_2026 = {
    "2026-01-18": ("mlk", "Monday January 19, 2026"),
    "2026-02-15": ("pres", "Monday February 16, 2026"),
    "2026-04-01": ("gf", None),
    "2026-05-24": ("mem", "Monday May 25, 2026"),
    "2026-06-17": ("jun", "Friday June 19, 2026"),
    "2026-07-02": ("jul4", "Friday, July 3, 2026"),
    "2026-09-06": ("lab", "Monday, September 7, 2026"),
    "2026-12-23": ("xmas", "Friday December 25, 2026"),
    "2026-12-24": ("xmas", "Friday December 25, 2026"),
    "2026-12-30": ("nye", None),
}


def build_deviation_windows():
    flats = {k: flat_pdf(p) for k, p in ADV.items()}
    out = {}
    for w, (key, closure_date) in WINDOWS_2026.items():
        flat = flats[key]
        src = adv_src(key)
        rows = class_rows(flat)
        normal = bool(re.search(r"will settle at their normal times", flat))
        pending = bool(re.search(r"Settlement Times are Pending", flat))
        if pending:
            status = "NOT_OBTAINED"
            reason = ("only archived vintage (2025-10-13 crawl) states settlement times 'Pending the BLS "
                      "announcement'; no later archived capture of this advisory URL (CDX single-row); "
                      "live cmegroup.com BLOCKED per standing evidence")
        elif rows:
            status = "OBTAINED_ADVISORY_CLASS_LEVEL"
        elif normal:
            status = "OBTAINED_ADVISORY_NORMAL_OR_CLOSURE_ONLY"
        else:
            status = "NOT_OBTAINED"
            reason = "no parseable dated row"
        cell = {"window_first_event_date": w, "status": status, "advisory": src,
                "verbatim_class_level_rows": rows, "closure_note_verbatim":
                    (f"CME Group will not derive or disseminate settlement prices on {closure_date}"
                     if closure_date else None),
                "product_code_level_row": "NOT_OBTAINED (no product-code session row exists in any permitted-route capture; see absence chain)",
                "mapping_law": "class-level rows are NOT mapped to NQ/6J/6A product codes (family transplant forbidden)"}
        if status == "NOT_OBTAINED":
            cell["reason"] = reason
        out[w] = cell
    return out


# ---------------------------------------------------------------- absence chains
ABSENCE = {
    "6J_2023_quarters": {
        "cells": ["2023Q1", "2023Q2", "2023Q3", "2023Q4"],
        "status": "NOT_OBTAINED",
        "reason": "no archived 6J product-calendar capture was crawled in the pre-expiry window. Complete CDX "
                  "enumeration (this lane, no-collapse): ProductCalendar/Future/69 = 2015-09-18, 2017-05-06, "
                  "2017-07-28 only (pre-span; publish horizon ends years before 2023); Download.xls?productId=69 = "
                  "2024-09-04 and 2025-11-04 only (post-expiry; the Download service drops expired contracts, "
                  "verified: earliest row in both XLS = Sep-2024 contract). No rule derivation used.",
        "evidence": ["captures/cdx_future69.txt", "captures/cdx_dl69.txt"],
    },
    "6A_2023Q1_Q2": {
        "cells": ["2023Q1", "2023Q2"],
        "status": "NOT_OBTAINED",
        "reason": "no archived 6A product-calendar capture in the pre-expiry window. Complete CDX enumeration "
                  "(this lane, no-collapse): ProductCalendar/Future/37 = 2016-05-18, 2018-02-27, 2018-06-23 "
                  "(pre-span) and 2023-09-16 (post-expiry; first row = ADU23 Sep-2023, H23/M23 dropped); "
                  "Download.xls?productId=37 = ZERO archived captures (CDX 0-byte result on both attempts). "
                  "No rule derivation used.",
        "evidence": ["captures/cdx_future37.txt", "captures/cdx_dl37.txt (0 bytes, 2 attempts)"],
    },
    "trading_hours_by_product_ids_69_37_146": {
        "status": "NOT_OBTAINED",
        "reason": "zero archived trading-hours-by-product captures carry product ids 69 (6J), 37 (6A) or 146 (NQ). "
                  "Fresh CDX regex probe (id list contains 69|37|146) returned 0 rows; corroborated by sibling Q5 "
                  "full enumeration (799 urlkeys; only id variants 316,133,425,300,58,437,22,8478,5201,10191 / "
                  "133 / 133,219 / 167,133 / 318 / 5224).",
        "evidence": ["fetch_log.jsonl cdx_svc_ids probe (0 rows)",
                     "sibling:FUTURES-P3-QUARANTINE-20261004/cal_permitted/captures/cdx_services_tradinghours_full.txt"],
    },
    "trading_hours_holiday_download": {
        "status": "BLOCKED_TRANSPORT",
        "reason": "two archived captures exist in CDX (2025-04-22, 2025-08-29) but the Wayback edge returns "
                  "HTTP 403 on every replay style attempted: id_ curl (attempt 1), standard curl (attempt 2) for "
                  "each timestamp, plus WebFetch (attempt 1) on the first. Route stopped per transport law; no bypass.",
        "evidence": ["fetch_log.jsonl holiday_dl_* records (4x http=403, 42-byte bodies)", "WebFetch 403 (manual)"],
    },
    "nq_product_calendar_deviation_fields": {
        "status": "NOT_OBTAINED",
        "reason": "ProductCalendar/Future/146 JSON (3 vintages fetched and parsed) carries contract rows only "
                  "(productCode/lastTrade/firstTrade/contractMonth + delivery fields); zero holiday/deviation/"
                  "earlyClose keys. NQ ContractSpecs (sibling Q5 capture re-verified sha da986d21...) likewise "
                  "contains 0 occurrences of holiday/earlyClose/deviation/special keys (weekly template only).",
        "evidence": ["captures/pcal_146_nq_20260304.json", "captures/pcal_146_nq_20260414.json",
                     "captures/pcal_146_nq_20260710.json",
                     "sibling:.../cspecs_146_20260930171824.json (re-verified)"],
    },
    "advisories_no_product_code_rows": {
        "status": "NOT_OBTAINED",
        "reason": "all nine archived 2026 settlement-times advisories parsed full-text: ZERO occurrences of "
                  "NQ / MNQ / J1 / JPY / AUD / 6J / 6A product codes; all rows are class-level (FX Products, "
                  "Equity & Crypto Products, Interest Rate Products, ...).",
        "evidence": ["captures/adv_*.pdf (9 files)"],
    },
    "live_cmegroup": {
        "status": "BLOCKED_TRANSPORT",
        "reason": "live www.cmegroup.com endpoints connection-refused per round-1/Q5 standing evidence "
                  "(ECONNREFUSED / exit 7, multiple methods); not re-attempted this lane (standing block, "
                  "budget conservation).",
        "evidence": ["sibling Q5 fetch_log.jsonl lines 83-86"],
    },
}


# ---------------------------------------------------------------- main
def main():
    vfy = verify_all()
    j26, a24, a25 = build_6j_2026()
    a26 = build_6a_2026()
    nq26 = build_nq_expiry()
    dev = build_deviation_windows()

    not_obt = lambda q, r: {"status": "NOT_OBTAINED", "reason": r}
    ABS = ABSENCE
    j23 = {q: not_obt(q, ABS["6J_2023_quarters"]["reason"]) for q in ("2023Q1", "2023Q2", "2023Q3", "2023Q4")}
    a23 = {q: not_obt(q, ABS["6A_2023Q1_Q2"]["reason"]) for q in ("2023Q1", "2023Q2")}

    n_j = sum(1 for c in {**j23, **j26}.values() if c["status"] == "OBTAINED")
    n_a = sum(1 for c in {**a23, **a26}.values() if c["status"] == "OBTAINED")
    n_dev_class = sum(1 for c in dev.values() if c["status"] == "OBTAINED_ADVISORY_CLASS_LEVEL")
    n_dev_prod = sum(1 for c in dev.values() if c.get("product_code_level_row") == "OBTAINED")

    delta = {
        "schema": "cal_janq_calendar_delta@1",
        "task_id": "CAL-JANQ",
        "cycle_id": "FUTURES-SIX-ADOPT-PREP-20261004",
        "lane": "CAL-JANQ (calendar-search-lane)",
        "generated_utc": NOW,
        "law": [
            "only dated values read from hash-verified archived official capture bytes (own parsers)",
            "IMM / third-Wednesday / third-Friday rule derivation FORBIDDEN and not used",
            "family transplants forbidden: advisory class-level rows recorded verbatim, never mapped to NQ/6J/6A codes",
            "NOT_OBTAINED never inferred; every NOT_OBTAINED carries explicit absence evidence",
            "transport law: WebFetch / web_reader / web.archive.org / plain curl only; <=2 attempts/URL/method; blocks => BLOCKED_TRANSPORT + stop",
            "Q5 sibling bytes re-verified per use (sha256 vs sibling fetch log + this lane's parser)",
        ],
        "dispatch_baseline": {
            "source": "dispatch packet (owner Việc 2 / D12 continuation)",
            "before": {"6J_expiry": "58/68", "6A_expiry": "62/68", "NQ_deviation_windows_product_code": "0"},
            "grid_definition": "68/code = quarterly expiry cells 2010-2026 (17y x 4); same grid as round-1 FX-EB accounting",
        },
        "after": {
            "6J_expiry": f"{58 + n_j}/68 (2023-2026 subgrid: {n_j}/8; remaining 2026 residual of dispatch 10-missing accounting outside this lane's bounded scope, flagged to owner)",
            "6A_expiry": f"{62 + n_a}/68 (2023-2026 subgrid: {n_a}/6; residual = exactly 2023Q1/Q2)",
            "NQ_deviation_windows_product_code": f"{n_dev_prod}/10 (unchanged 0; class-level advisory evidence obtained for {n_dev_class}/10 windows, recorded separately, not mapped to codes)",
        },
        "J1_expiry": {  # J1 = official 6J contract-code prefix observed in the XLS product-code column
            "quarters_2023": j23,
            "quarters_2026": j26,
            "attempted_scope_note": "6J dispatch missing = 10 cells; bounded scope = 2023 (4) + 2026 (4); the identity of the other 2 missing cells is not determinable from this lane's captures and is NOT inferred",
        },
        "AD_expiry": {"quarters_2023H1": a23, "quarters_2026": a26},
        "NQ_expiry_2026": nq26,
        "NQ_holiday_deviation_windows_2026": dev,
        "sixJ_holiday_windows_2023_2026": {
            "grid": "42-window deviation grid per round-1 cell_definition (2022-12-31 + 10x2023 + 10x2024 + 11x2025 + 10x2026)",
            "product_code_level": "NOT_OBTAINED 0/42 for 6J AND 6A (absence: trading_hours_by_product_ids_69_37_146)",
            "sixA_holiday_windows": "same verdict as 6J (no archived capture carries id 37)",
            "advisory_crossref_2026": "2026 windows carry class-level advisory rows (FX rows exist only for Christmas Eve 12/24/2026); see NQ_holiday_deviation_windows_2026 — not mapped to codes",
        },
        "absence_and_blocks": ABSENCE,
        "budget": {
            "limit": 35, "used": 28,
            "breakdown": {"cdx_probes": 8, "snapshot_fetches": 19, "webfetch_method_check": 1},
            "per_url_method_cap": "<=2 enforced (holiday-download: 2 curl + 1 WebFetch per timestamp max; all others <=2)",
        },
        "corrections_to_prior_rounds": [
            "Dispatch/round-1 claim '6J 2026 quarters CONFIRMED ABSENT from pcal_69_6j_dl_*.xls' is CONTRADICTED by this lane's own parse: J1H26/M26/U26/Z26 rows with last-trade dates ARE present in the re-verified Q5 XLS @2024-09-04 and corroborated by the new @2025-11-04 XLS (identical values). Only the 2023 quarters are absent from that capture (expired-contract drop).",
            "Dispatch/round-1 claim 'pcal_37_6a_*.json exhausted' is accurate for 2023Q1/Q2 but incomplete for 2026: the re-verified Sep-2023 capture carries ADH26/ADM26/ADU26/ADZ26 with full last-trade dates; these were not previously credited.",
        ],
    }

    legality = {
        "schema": "cal_janq_legality_validation@1",
        "generated_utc": NOW,
        "transport_law_compliance": {
            "permitted_methods_used": ["plain curl (web.archive.org CDX + snapshots)", "WebFetch (single route check)"],
            "non_permitted_methods_used": [],
            "blocks_recorded_as_blocked_transport": ["trading-hours-holiday-download (archive-edge 403; route stopped)"],
            "max_attempts_per_url_method": "2 (verified from fetch_log.jsonl: no URL/method pair exceeds 2)",
            "budget_used": 28, "budget_limit": 35,
        },
        "capture_chain": [],
        "q5_sibling_per_use_reverify": {
            "law": "P3 SNI-swap evidence forbidden; Q5 data only after independent verify; new uses re-verify per use",
            "records": vfy,
            "method": "shasum -a 256 + this lane's xlrd/json parsers; expected shas taken from sibling fetch_log.jsonl lines 75/77/78",
        },
        "derivation_prohibitions": {
            "imm_rule_derivation": "not used",
            "family_transplants": "class-level advisory rows kept verbatim; product-code mapping not performed",
            "current_calendar_inference": "not used; all values are as-published snapshots with vintage notes",
        },
        "write_boundary": {
            "allowed": ["research/control/FUTURES-SIX-ADOPT-PREP-20261004/cal_janq/**",
                        "dispatch/handoff_CAL-JANQ.json"],
            "git_commands": "exactly one: git rev-parse HEAD (actual_start_sha); no add/commit/push",
        },
    }
    for label, p in [("pcal_69_6j_dl_20251104.xls", XLS_2025), ("pcal_146_nq_20260304.json", NQ["20260304"]),
                     ("pcal_146_nq_20260414.json", NQ["20260414"]), ("pcal_146_nq_20260710.json", NQ["20260710"]),
                     ("pcal_69_6j_dl_20240904.xls (sibling)", XLS_2024), ("pcal_37_6a_20230916051415.json (sibling)", PCA_37)]:
        legality["capture_chain"].append({"capture": str(p), "sha256": sha(p), "role": label})
    for k, p in ADV.items():
        legality["capture_chain"].append({"capture": str(p), "sha256": sha(p), "role": f"advisory {k} (2026 window)"})

    (LANE / "calendar_delta.json").write_text(json.dumps(delta, indent=1))
    (LANE / "legality_validation.json").write_text(json.dumps(legality, indent=1))
    print("6J 2023-2026 obtained:", n_j, "->", f"{58+n_j}/68")
    print("6A 2023-2026 obtained:", n_a, "->", f"{62+n_a}/68")
    print("NQ 2026 expiry cells:", sum(1 for c in nq26.values() if c["status"] == "OBTAINED"))
    print("NQ deviation windows: product-code", n_dev_prod, "/ class-level", n_dev_class, "/10")
    print("captures hashed:", len(legality["capture_chain"]))


if __name__ == "__main__":
    main()
