"""EIA normalizer -> tidy tables.

WNGSR archived issues (eia/wngsr/issues/*.html):
- Each file = one as-published weekly issue (vintage). Filename = issue date.
- Extracted: issue/release date (page header), working-gas total (Bcf),
  weekly net change, five-year-average comparison, and the embedded analyst
  survey (The Desk) median/range when present (free as-published consensus
  record - disclosed as EIA-reported survey, not a vendor consensus archive).
- PIT: observation = "as of Friday" prior week; release = issue date 10:30 ET
  (schedule FACT; holiday moves per archived schedule page).
WPSR archived issues (eia/wpsr/issues/*.html): same structure for crude/
Cushing/products narrative summary when present.

Vintage law: each issue file IS the vintage (as-published). Revisions between
issues are NOT reconstructed (EIA does not publish a vintage diff file) ->
vintage_flag='as_published_issue'.

ERRATUM 2026-10-02 (NONPRICE-FIX, audit finding M-1): the pre-fix
`net_change_bcf` used a first-mention grab of "net injection/withdrawal of X
Bcf" anywhere in the issue and agreed with an independent week-over-week
totals difference on only 62/537 comparable rows (~11.5%; audit's own window:
62/561, 11.1%) - misgrabs included market expectations, The Desk survey range
bounds, last-year and five-year-average values. REBUILT extraction
(table/section-anchored, validated, quarantined):
- Primary source = the issue's own stocks summary table ("Working gas in
  underground storage ... Total cur prior change"; 2001-03 era:
  "Total Lower 48 cur ... net-change prior"). The table's implied net change
  (cur - prior) must equal its printed change column (internal consistency)
  or the table is not trusted.
- Secondary source = section-anchored narrative: "Net injections into /
  withdrawals from storage|working gas totaled X Bcf" and (2004-15 era)
  "implied net injection/withdrawal (of|was|were) X Bcf". Regional sentences
  (East/Midwest/...) are excluded.
- Independent validation = week-over-week difference of consecutive issues'
  working-gas totals (gap 5-10 days). Agreement is reported by the runner.
  Rows whose anchored value still disagrees (tolerance 2 Bcf) without a
  table-evidenced prior-week revision are QUARANTINED: net_change_bcf set to
  null, net_change_flag='EXTRACT_LOW_CONFIDENCE', reason recorded. A wrong
  value is never silently kept.
- net_change_bcf is now SIGNED (+ injection / - withdrawal); the pre-fix
  column was an unsigned magnitude. The legacy first-mention value is kept
  (net_change_legacy_firstmention_bcf) for erratum transparency only.
- issue_date_raw (pre-fix: first "Month DD, YYYY" anywhere; unreliable) is
  kept for schema compatibility but superseded by issue_date, parsed from the
  page's "Release date:" header when present (issue_date_source records the
  provenance; 'filename' fallback is authoritative when header absent).
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path

import pandas as pd

RAW = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
OUT = RAW / "normalized"

MONTHS = ("January|February|March|April|May|June|July|August|September|"
          "October|November|December")

_MONTH_NUM = {m: i + 1 for i, m in enumerate(
    "January February March April May June July August September October "
    "November December".split())}


def _iso_from_header(mon: str, day: str, year: str) -> str:
    return f"{year}-{_MONTH_NUM[mon]:02d}-{int(day):02d}"

# ---- table/section-anchored net-change sources (M-1 rebuild) ----
# Modern stocks table: "Working gas in underground storage Stocks ... Region
# <date> <date> change ... Total cur prior change". Values may carry 'C'
# (reclassification) / 'R' (revised) flags and '-->' reclassification arrows
# (e.g. "Total 3,269 C --> 3,205 R --> 64"); dates are ISO (2014+) or M/DD/YY.
# The table's own current-date column is captured for staleness detection:
# some archived early-era issues reprint a table from an older week.
RE_STOCKS_TABLE = re.compile(
    r"[Ww]orking [Gg]as [Ii]n [Uu]nderground [Ss]torage\s+Stocks.{0,60}?Region\s+"
    r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2})\s+"
    r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2})\s+change.{0,400}?"
    r"\bTotal\s+([\d,]+)\s*(?:[CR])?\s*(?:-->)?\s*([\d,]+)\s*(?:[CR])?\s*(?:-->)?\s*"
    r"(-?[\d,]+)")
# Early-era summary table (2001-03): "All Volumes in BCF Current Stocks
# (Fri, M/D) ... Total Lower 48 cur 5yr pct net-change prior". NOTE (in-file
# disclosure): the early-table net-change column is the AGA Wednesday
# estimate; the narrative "implied" figure is EIA's derivation -> in-file
# conflicts in this era are real ambiguity, quarantined when no independent
# check exists.
RE_EARLY_TABLE_HDR = re.compile(r"Current Stocks\s*\(Fri,\s*(\d{1,2})/(\d{1,2})\)")
RE_EARLY_TABLE = re.compile(
    r"Total Lower 48\s+([\d,]+)\s+([\d,]+)\s+(-?[\d.]+%)\s+(-?[\d,]+)\s+([\d,]+)")
# Narrative (2016+): "Net injections into storage totaled X Bcf ..." /
# "The net withdrawals from working gas totaled X billion cubic feet (Bcf)...".
RE_NARR_TOTALED = re.compile(
    r"[Nn]et\s+(injections?|withdrawals?)\s+(?:into|from)\s+"
    r"(?:storage|working gas|underground storage)\s+totaled\s+([\d,]+)"
    r"\s*(?:billion cubic feet\s*)?\(?\s*Bcf")
# Narrative (2004-15): "The implied net withdrawal during the report week was
# X Bcf" / "Implied net withdrawals were X Bcf" / "implied net withdrawal from
# working gas of X Bcf".
RE_NARR_IMPLIED = re.compile(
    r"[Ii]mplied\s+net\s+(injections?|withdrawals?)[^.,]{0,60}?"
    r"(?:\bof\b|\bwas\b|\bwere\b)\s+([\d,]+)\s*Bcf")
# National working-gas totals from narrative/table (region rows and forecast
# phrasings excluded - pre-fix first-match could grab e.g. "working gas stocks
# in the Producing region totaled 1,188 Bcf" or "will total 1,320 Bcf").
RE_WG_TOTAL = re.compile(
    r"[Ww]orking (?:natural gas|gas) (?:stocks|inventories|gas stocks)"
    r"[^.]{0,80}?(?:totaled|total(?:s|led)?|decreased to|increased to|was|were)"
    r"\s+([\d,]+)\s+Bcf")
RE_REGION_WORDS = re.compile(
    r"\b(East|Midwest|West|Western|South Central|Mountain|Pacific|Producing|"
    r"region[s]?)\b")
# False-positive context markers for narrative candidates (pre = before match,
# post = after value): season-cumulative sentences, prior-week reprints,
# year-ago references, multi-week averages.
RE_FP_PRE = re.compile(
    r"(on average|average,|last year|year ago|year-ago|same week|these weeks|"
    r"so far|season[, ]|refill season|heating season|withdrawal season)")
RE_FP_POST = re.compile(
    r"(since [A-Z]|season|so far|these weeks|since the beginning)")
# Pre-fix first-mention grab (kept ONLY as net_change_legacy_firstmention_bcf).
RE_LEGACY_FIRSTMENTION = re.compile(
    r"(?:net (?:injections?|withdrawals?)) of\s+([\d,]+)\s+Bcf")


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _strip_tags(html: str) -> str:
    t = re.sub(r"<[^>]+>", " ", html)
    t = re.sub(r"&nbsp;", " ", t)
    t = re.sub(r"&amp;", "&", t)
    return re.sub(r"\s+", " ", t)


def _dir_signed(direction_word: str, magnitude: int) -> int:
    return magnitude if direction_word.startswith("injection") else -magnitude


def _narrative_candidates(text: str, pattern: re.Pattern, issue_date: str | None):
    """Ranked, filtered narrative candidates. Filters: regional sentences;
    season-cumulative / prior-week-reprint / year-ago / average contexts;
    candidates whose own 'week ending' date is not the issue's storage week
    (storage Friday falls 4-8 days before the release-Thursday issue date -
    a date ~2 weeks old is a prior-week reprint)."""
    import datetime as _dt
    cands = []
    for m in pattern.finditer(text):
        span = m.group(0)
        if RE_REGION_WORDS.search(span):
            continue
        pre = text[max(0, m.start() - 60):m.start()]
        post = text[m.end():m.end() + 100]
        if RE_FP_PRE.search(pre) or RE_FP_POST.search(post):
            continue
        if issue_date:
            wm = re.search(rf"week ending\s+({MONTHS})\s+(\d{{1,2}}),?\s*(\d{{4}})?",
                           pre + post)
            if wm:
                year = wm.group(3) or issue_date[:4]
                wd = _dt.date.fromisoformat(
                    _iso_from_header(wm.group(1), wm.group(2), year))
                age = (_dt.date.fromisoformat(issue_date) - wd).days
                if not (4 <= age <= 8):
                    continue
        cands.append((_dir_signed(m.group(1), int(m.group(2).replace(",", ""))),
                      "for the week" in post))
    for ranked, _ in sorted(cands, key=lambda c: not c[1]):  # week-marked first
        yield ranked


def _wg_total_filtered(text: str) -> int | None:
    """National working-gas total from narrative, region/forecast-filtered."""
    for m in RE_WG_TOTAL.finditer(text):
        span = m.group(0)
        if RE_REGION_WORDS.search(span) or "will total" in span:
            continue
        return int(m.group(1).replace(",", ""))
    return None


def _legacy_total(text: str) -> int | None:
    """Pre-fix fallback totals phrasing (kept for parse-rate continuity)."""
    m = re.search(r"[Ww]orking gas in storage (?:decreased|increased) to"
                  r"\s+([\d,]+)\s+Bcf", text)
    return int(m.group(1).replace(",", "")) if m else None


def _table_date(raw: str, issue_date: str | None):
    """Parse a table-header date (ISO or M/DD/YY) into ISO; None if the
    table's data week is not plausibly this issue's storage week (staleness
    guard: the Friday observation is 3-11 days before the issue date; the
    archived early era occasionally reprints an older week's table)."""
    import datetime as _dt
    if not issue_date:
        return None, None
    try:
        if "-" in raw:
            d = _dt.date.fromisoformat(raw)
        else:
            mm, dd, yy = (int(x) for x in raw.split("/"))
            d = _dt.date(2000 + yy, mm, dd)
    except ValueError:
        return None, None
    age = (_dt.date.fromisoformat(issue_date) - d).days
    return d.isoformat(), (3 <= age <= 11)


def _anchored_net_change(text: str, issue_date: str | None) -> dict:
    """Table/section-anchored weekly net change. Returns dict with candidate
    values per source; reconciliation happens in main() against the
    independent consecutive-totals derivation."""
    out = {"stocks_table": None, "stocks_table_cur": None,
           "stocks_table_prior": None, "early_table": None,
           "narrative": None, "narrative_source": None,
           "storage_week_ending": None, "table_stale": None}
    m = RE_STOCKS_TABLE.search(text)
    if m:
        cur_date, fresh = _table_date(m.group(1), issue_date)
        cur = int(m.group(3).replace(",", ""))
        prior = int(m.group(4).replace(",", ""))
        chg = int(m.group(5).replace(",", ""))
        if not fresh:
            out["table_stale"] = f"table dated {cur_date or m.group(1)} vs issue {issue_date}"
        elif cur - prior == chg:  # internal consistency law of the table itself
            out.update({"stocks_table": chg, "stocks_table_cur": cur,
                        "stocks_table_prior": prior,
                        "storage_week_ending": cur_date})
        else:
            out["stocks_table_inconsistent"] = (cur, prior, chg)
    m = RE_EARLY_TABLE.search(text)
    if m:
        hdr = RE_EARLY_TABLE_HDR.search(text)
        fresh = None  # None = undatable header; False = dated outside window
        if hdr and issue_date:
            import datetime as _dt
            mm, dd = int(hdr.group(1)), int(hdr.group(2))
            td = _dt.date.fromisoformat(issue_date)
            for yy in (td.year - 1, td.year):
                try:
                    age = (td - _dt.date(yy, mm, dd)).days
                except ValueError:
                    continue
                if 3 <= age <= 18:  # early era: Friday obs, Monday issue, AGA lag
                    fresh = True
                    break
            if fresh is not True:
                fresh = False
                out["table_stale"] = (out.get("table_stale") or "") + (
                    f"early table dated ({hdr.group(1)}/{hdr.group(2)}) vs "
                    f"issue {issue_date}")
        if fresh is not False:
            cur = int(m.group(1).replace(",", ""))
            chg = int(m.group(4).replace(",", ""))
            prior = int(m.group(5).replace(",", ""))
            if cur - prior == chg and out["stocks_table_cur"] is None:
                out.update({"early_table": chg, "stocks_table_cur": cur,
                            "stocks_table_prior": prior})
    for pattern, src in ((RE_NARR_TOTALED, "narrative_net_totaled"),
                         (RE_NARR_IMPLIED, "narrative_implied_net")):
        for val in _narrative_candidates(text, pattern, issue_date):
            out["narrative"], out["narrative_source"] = val, src
            break
        if out["narrative"] is not None:
            break
    return out


def parse_wngsr_issue(p: Path) -> dict | None:
    fname_date = p.stem  # e.g. 2026_01_22
    text = _strip_tags(p.read_text(errors="replace"))
    # Release date: prefer the page's own "Release date:" header (robust);
    # fall back to the filename date (authoritative), NEVER to a bare
    # first-mention "Month DD, YYYY" (pre-fix issue_date_raw was unreliable).
    m = re.search(rf"Release date:\s*({MONTHS})\s+(\d{{1,2}}),\s+(20\d\d)", text)
    if m:
        issue_date = _iso_from_header(m.group(1), m.group(2), m.group(3))
        issue_date_source = "release_date_header"
    else:
        issue_date = fname_date.replace("_", "-")
        issue_date_source = "filename"
    mw = re.search(rf"week ending\s+({MONTHS})\s+(\d{{1,2}}),\s+(20\d\d)", text)
    week_ending = (_iso_from_header(mw.group(1), mw.group(2), mw.group(3))
                   if mw else None)
    # legacy unreliable field kept for schema compatibility (see erratum)
    mraw = re.search(rf"({MONTHS})\s+(\d{{1,2}}),\s+(20\d\d)", text)
    out = {"file": p.name,
           "issue_date_raw": (f"{mraw.group(3)}-{mraw.group(1)}-{mraw.group(2)}"
                              if mraw else fname_date.replace("_", "-")),
           "issue_date": issue_date,
           "issue_date_source": issue_date_source,
           "observation_week_ending": week_ending,
           "provenance_sha256": _sha(p)}
    anc = _anchored_net_change(text, issue_date)
    # totals priority: the issue's own stocks table (authoritative Form
    # EIA-912 as-published), else region/forecast-filtered narrative, else
    # the legacy fallback phrasing
    out["working_gas_total_bcf"] = (anc["stocks_table_cur"]
                                    if anc["stocks_table_cur"] is not None
                                    else (_wg_total_filtered(text)
                                          or _legacy_total(text)))
    out["storage_week_ending"] = anc.get("storage_week_ending")
    out["table_stale_note"] = anc.get("table_stale") or None
    out["stocks_table_total_bcf"] = anc["stocks_table_cur"]
    out["stocks_table_prior_total_bcf"] = anc["stocks_table_prior"]
    out["net_change_source"] = None
    out["net_change_bcf"] = None
    if anc["stocks_table"] is not None:
        out["net_change_bcf"], out["net_change_source"] = anc["stocks_table"], "stocks_table"
    elif anc["early_table"] is not None:
        out["net_change_bcf"], out["net_change_source"] = anc["early_table"], "early_summary_table"
    elif anc["narrative"] is not None:
        out["net_change_bcf"], out["net_change_source"] = anc["narrative"], anc["narrative_source"]
    out["net_change_direction"] = ("injection" if (out["net_change_bcf"] or 0) > 0
                                   else "withdrawal" if (out["net_change_bcf"] or 0) < 0
                                   else None)
    out["net_change_flag"] = "NOT_PARSED" if out["net_change_bcf"] is None else "OK_UNCHECKED"
    out["net_change_quarantine_reason"] = None
    # pre-fix first-mention value, kept for erratum transparency ONLY
    ml = RE_LEGACY_FIRSTMENTION.search(text)
    out["net_change_legacy_firstmention_bcf"] = int(ml.group(1).replace(",", "")) if ml else None
    # narrative candidate recorded even when table wins (cross-evidence)
    out["net_change_narrative_bcf"] = anc["narrative"]
    mw = re.search(r"(?:median estimate of net (?:injections?|withdrawals?) of|median estimate of|expectations called for (?:a|an) (?:net )?(?:injection|withdrawal) of)\s+([\d,]+)\s*Bcf", text)
    out["survey_median_bcf"] = int(mw.group(1).replace(",", "")) if mw else None
    mr = re.search(r"estimates of the weekly net change[^?]*?ranged from net (injections?|withdrawals?) of\s+([\d,]+)\s+Bcf to\s+([\d,]+)\s*Bcf", text)
    if mr:
        out["survey_low_bcf"] = int(mr.group(2).replace(",", ""))
        out["survey_high_bcf"] = int(mr.group(3).replace(",", ""))
        out["survey_direction"] = mr.group(1)
    return out


def parse_wpsr_issue(p: Path) -> dict | None:
    text = _strip_tags(p.read_text(errors="replace"))
    m = re.search(rf"({MONTHS})\s+(\d{{1,2}}),\s+(20\d\d)", text)
    out = {"file": p.name,
          "issue_date_raw": f"{m.group(3)}-{m.group(1)}-{m.group(2)}" if m else None,
          "provenance_sha256": _sha(p)}
    mc = re.search(r"[Cc]rude oil (?:oil )?(?:inventories|stocks)[^.]{0,200}?([\d,\.]+)\s*million barrels", text)
    out["crude_mmbbl"] = float(mc.group(1).replace(",", "")) if mc else None
    mk = re.search(r"Cushing[^.]{0,200}?([\d,\.]+)\s*million barrels", text)
    out["cushing_mmbbl"] = float(mk.group(1).replace(",", "")) if mk else None
    return out


def parse_wpsr_tables() -> None:
    """Per-week as-published table CSVs (table1 crude+products stocks, table3
    refiner net production, table4 imports) + table13 Cushing PDFs."""
    import io as _io
    from pypdf import PdfReader
    rows = []
    d = RAW / "eia/wpsr/tables"
    for p in sorted(d.glob("*_ttable1.csv")):
        wk = p.name.split("_ttable1")[0]  # YYYY_MM_DD
        try:
            df = pd.read_csv(p, encoding="latin-1", engine="python", on_bad_lines="skip")
        except Exception:
            continue
        prov = _sha(p)
        def row_val(label):
            m = df[df["STUB_1"].astype(str).str.strip() == label]
            if len(m):
                return float(str(m.iloc[0, 1]).replace(",", ""))
            return None
        rows.append({
            "series_id": "WPSR_WEEKLY",
            "observation_period": f"{wk[:4]}-{wk[5:7]}-{wk[8:10]}",
            "crude_commercial_mmbbl": row_val("Commercial (Excluding SPR)"),
            "crude_total_incl_spr_mmbbl": row_val("Crude Oil"),
            "gasoline_total_mmbbl": row_val("Total Motor Gasoline"),
            "provenance_sha256": prov,
            "vintage_flag": "as_published_issue_table",
            "file": p.name,
        })
        # table4 = crude stocks by PAD + CUSHING (as-published)
        p4 = p.with_name(p.name.replace("_ttable1.csv", "_ttable4.csv"))
        if p4.exists():
            try:
                df4 = pd.read_csv(p4, encoding="latin-1", engine="python", on_bad_lines="skip")
                m4 = df4[df4["STUB_1"].astype(str).str.strip() == "Cushing"]
                if len(m4):
                    rows[-1]["cushing_crude_stocks_mmbbl"] = float(str(m4.iloc[0, 1]).replace(",", ""))
                rows[-1]["provenance_sha256_table4"] = _sha(p4)
            except Exception:
                pass
    if rows:
        pd.DataFrame(rows).to_parquet(OUT / "eia_wpsr_tables_tidy.parquet")
        got = pd.DataFrame(rows)
        print(f"wpsr table1 rows: {len(got)}; crude parsed: {got['crude_commercial_mmbbl'].notna().sum()}; "
              f"cushing parsed: {got['cushing_crude_stocks_mmbbl'].notna().sum() if 'cushing_crude_stocks_mmbbl' in got else 0}")
    # Cushing from table13 PDFs (text extraction; official as-published record)
    crows = []
    for p in sorted(d.glob("*_ttable13.pdf")):
        wk = p.name.split("_ttable13")[0]
        try:
            reader = PdfReader(str(p))
            text = " ".join((pg.extract_text() or "") for pg in reader.pages)
        except Exception:
            continue
        m = re.search(r"Cushing[^0-9\-]*([\d,]{4,9}(?:\.\d)?)", text)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            crows.append({
                "series_id": "WPSR_CUSHING_STOCKS_MMBBL",
                "observation_period": f"{wk[:4]}-{wk[5:7]}-{wk[8:10]}",
                "value": val,
                "vintage_flag": "as_published_issue_table_pdf",
                "provenance_sha256": _sha(p),
            })
    if crows:
        pd.DataFrame(crows).to_parquet(OUT / "eia_wpsr_cushing_tidy.parquet")
        print(f"wpsr cushing rows: {len(crows)}")


def _reconcile_wngsr_net_change(df: pd.DataFrame) -> pd.DataFrame:
    """Validate anchored net-change candidates against an INDEPENDENT
    derivation (week-over-week difference of consecutive issues' totals,
    gap<=10 days; totals prefer the stocks table, fall back to filtered
    narrative) and quarantine unresolved disagreements.

    Evidence rules (M-1 law: a wrong value is never silently kept):
    - modern stocks table (Form EIA-912 as-published, internally consistent
      cur-prior==change) is the primary value; a filtered national narrative
      that disagrees does not override it but IS disclosed
      (*_NARR_NONCORROB flags) unless it is the only source.
    - early-era table net-change is the AGA estimate while the narrative
      'implied' figure is EIA's derivation: with no independent check, an
      in-file conflict there is real ambiguity -> EXTRACT_LOW_CONFIDENCE.
    - |value - check| > 2 Bcf with no table-evidenced prior-week revision
      -> EXTRACT_LOW_CONFIDENCE (value nulled, candidates recorded)."""
    import datetime as _dt
    df = df.copy().sort_values("issue_date").reset_index(drop=True)

    def _tot(r):
        if r["stocks_table_total_bcf"] is not None and not pd.isna(r["stocks_table_total_bcf"]):
            return int(r["stocks_table_total_bcf"])
        if r["working_gas_total_bcf"] is not None and not pd.isna(r["working_gas_total_bcf"]):
            return int(r["working_gas_total_bcf"])
        return None

    checks, prev_tots = [], []
    prev_date, prev_tot = None, None
    for _, r in df.iterrows():
        d = _dt.date.fromisoformat(r["issue_date"])
        tot = _tot(r)
        near = prev_date is not None and (d - prev_date).days <= 10
        checks.append(tot - prev_tot if (near and tot is not None
                                         and prev_tot is not None) else None)
        prev_tots.append(prev_tot if near else None)
        prev_date, prev_tot = d, tot
    # implausible-check guard: a weekly net change beyond +/-400 Bcf is
    # physically impossible (record weekly withdrawal is -359); such a check
    # proves a totals misparse in one of the two issues -> invalidate the
    # CHECK (disclosed), never quarantine a value on its evidence alone.
    df["net_change_check_bcf"] = [
        None if (c is not None and abs(c) > 400) else c for c in checks]
    df["check_invalidated_note"] = [
        f"check {c:+d} implausible -> totals misparse suspected, check discarded"
        if (c is not None and abs(c) > 400) else None for c in checks]
    df["prev_issue_total_bcf"] = prev_tots

    TOL = 2  # Bcf; integer totals with occasional 'C' reclassification
    flags, reasons, notes, nulls = [], [], [], []
    for _, r in df.iterrows():
        val, chk, narr = (r["net_change_bcf"], r["net_change_check_bcf"],
                          r["net_change_narrative_bcf"])
        src = r["net_change_source"]
        narr_bad = (narr is not None and not pd.isna(narr)
                    and val is not None and not pd.isna(val)
                    and abs(abs(float(narr)) - abs(float(val))) > 1)
        if val is None or pd.isna(val):
            flags.append("NOT_PARSED"); reasons.append(None)
            notes.append(None); nulls.append(False)
            continue
        if chk is not None and not pd.isna(chk):
            if abs(float(val) - float(chk)) <= TOL:
                flags.append("OK_VERIFIED_TOTALS_DIFF_NARR_NONCORROB"
                             if narr_bad else "OK_VERIFIED_TOTALS_DIFF")
                reasons.append(None)
                notes.append(f"narrative {float(narr):+.0f} non-corroborating"
                             if narr_bad else None)
                nulls.append(False)
            else:
                prior_tbl, prev_pub = r["stocks_table_prior_total_bcf"], r["prev_issue_total_bcf"]
                revised = (prior_tbl is not None and not pd.isna(prior_tbl)
                           and prev_pub is not None and not pd.isna(prev_pub)
                           and int(prior_tbl) != int(prev_pub))
                if revised and src == "stocks_table":
                    flags.append("OK_PRIOR_WEEK_REVISED")
                    reasons.append(None)
                    notes.append(f"table prior {int(prior_tbl)} != prev-issue "
                                 f"total {int(prev_pub)} (as-published revision; "
                                 f"value kept, disclosed; check {float(chk):+.0f})")
                    nulls.append(False)
                else:
                    flags.append("EXTRACT_LOW_CONFIDENCE")
                    reasons.append(f"anchored {float(val):+.0f} (source {src}) vs "
                                   f"consecutive-totals diff {float(chk):+.0f} "
                                   f"(> {TOL} Bcf, no table-evidenced prior-week "
                                   f"revision; narrative candidate "
                                   f"{('%+.0f' % float(narr)) if narr is not None and not pd.isna(narr) else 'none'})")
                    notes.append(None)
                    nulls.append(True)
        else:
            if src in ("stocks_table",):
                flags.append("OK_TABLE_INTERNAL_NARR_NONCORROB"
                             if narr_bad else "OK_TABLE_INTERNAL")
                reasons.append(None)
                notes.append(f"narrative {float(narr):+.0f} non-corroborating, "
                             f"no cross-issue check available" if narr_bad else None)
                nulls.append(False)
            elif src == "early_summary_table":
                if narr_bad:
                    flags.append("EXTRACT_LOW_CONFIDENCE")
                    reasons.append(f"early-era in-file conflict: AGA-estimate table "
                                   f"{float(val):+.0f} vs EIA-implied narrative "
                                   f"{float(narr):+.0f}; no independent check "
                                   f"(totals unavailable) to adjudicate")
                    notes.append(None)
                    nulls.append(True)
                else:
                    flags.append("OK_TABLE_INTERNAL")
                    reasons.append(None); notes.append(None); nulls.append(False)
            else:  # narrative-only
                flags.append("OK_NARRATIVE_ONLY")
                reasons.append(None); notes.append(None); nulls.append(False)
    df["net_change_flag"] = flags
    df["net_change_quarantine_reason"] = reasons
    df["net_change_note"] = notes
    df.loc[nulls, "net_change_bcf"] = None

    # agreement reporting: before (legacy first-mention) vs after (anchored)
    cmp_rows = df[df["net_change_check_bcf"].notna()
                  & df["net_change_legacy_firstmention_bcf"].notna()]
    agree_before = (cmp_rows["net_change_legacy_firstmention_bcf"].astype(int)
                    == cmp_rows["net_change_check_bcf"].astype(int).abs()).sum()
    after = cmp_rows[cmp_rows["net_change_bcf"].notna()]
    agree_after = (after["net_change_bcf"].astype(float)
                   == after["net_change_check_bcf"].astype(float)).sum()
    print(f"wngsr net_change agreement vs consecutive-totals diff: "
          f"BEFORE (legacy first-mention, |unsigned|) {agree_before}/{len(cmp_rows)} "
          f"({agree_before / len(cmp_rows):.1%}); AFTER (anchored, signed) "
          f"{agree_after}/{len(after)} ({agree_after / len(after):.1%}) of "
          f"comparable rows with a kept value")
    return df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wngsr_dir = RAW / "eia/wngsr/issues"
    if wngsr_dir.exists():
        rows = [r for p in sorted(wngsr_dir.glob("*.html"))
                if (r := parse_wngsr_issue(p))]
        df = pd.DataFrame(rows)
        df = _reconcile_wngsr_net_change(df)
        df.to_parquet(OUT / "eia_wngsr_vintages_tidy.parquet")
        ok_total = df["working_gas_total_bcf"].notna().sum()
        ok_survey = df["survey_median_bcf"].notna().sum()
        print(f"wngsr issues parsed: {len(df)}; totals parsed: {ok_total}; survey median parsed: {ok_survey}")
        print("net_change flags:", df["net_change_flag"].value_counts().to_dict())
        print("net_change sources:", df["net_change_source"].value_counts(dropna=False).to_dict())
        if len(df):
            print("  files:", df["file"].iloc[0], "..", df["file"].iloc[-1])
    wpsr_dir = RAW / "eia/wpsr/issues"
    if wpsr_dir.exists():
        rows = [r for p in sorted(wpsr_dir.glob("*.html"))
                if (r := parse_wpsr_issue(p))]
        df2 = pd.DataFrame(rows)
        if len(df2):
            df2.to_parquet(OUT / "eia_wpsr_vintages_tidy.parquet")
            print(f"wpsr issues parsed: {len(df2)}; crude parsed: {df2['crude_mmbbl'].notna().sum()}; cushing parsed: {df2['cushing_mmbbl'].notna().sum()}")
    parse_wpsr_tables()


if __name__ == "__main__":
    main()
