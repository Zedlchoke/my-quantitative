"""A7 independent recompute (read-only on evidence; writes only its report).

Own parsers for TD snapshot JSON and SSGA xlsx (zipfile+stdlib XML). Rule
modules (calendar/partition/cohort) are imported ONLY for frozen semantics;
every number below is computed here from the raw staged files.
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z2-a7")
sys.path.insert(0, str(WT))

from research.assets.stocks.calendar import (  # noqa: E402
    ET_ZONE,
    USEquityRegularCalendar,
    US_EQUITY_REGULAR_V1,
)
from research.stocks_free_v1.partition import (  # noqa: E402
    SealedPathFilter,
    freeze_partition,
)

SNAP = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/staging-td/snapshot2010")
COHORT_STAGE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v1/staging-cohort")
DIST_XLSX = COHORT_STAGE / "spdr-etf-historical-distributions.xlsx"
NAV_XLSX = COHORT_STAGE / "navhist-us-en-spy.xlsx"

W_START, W_END = date(2018, 1, 2), date(2026, 8, 27)
S0_START = date(2018, 4, 4)

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
TAG = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


# ---------------- own parsers ---------------- #
def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def xlsx_rows(path: Path) -> list[list[str]]:
    z = zipfile.ZipFile(path)
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(TAG + "t")))
    names = [n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)]
    names.sort()
    sh = ET.fromstring(z.read(names[0]))
    out: list[list[str]] = []
    for row in sh.iter(TAG + "row"):
        cells: list[str] = []
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if v is None:
                cells.append("")
            elif c.get("t") == "s":
                cells.append(shared[int(v.text)])
            else:
                cells.append(v.text or "")
        out.append(cells)
    return out


def parse_distributions(ticker: str) -> dict[date, float]:
    """SSGA distributions workbook -> {ex_date: dividend+STCG+LTCG per share}."""
    rows = xlsx_rows(DIST_XLSX)
    out: dict[date, float] = {}
    for r in rows[1:]:
        if len(r) < 9 or (r[1].strip() if len(r) > 1 else "") != ticker:
            continue
        try:
            m, d, y = r[3].strip().split("/")
            exd = date(int(y), int(m), int(d))
            amt = sum(float(x) for x in (r[6], r[7], r[8]) if x.strip())
        except (ValueError, IndexError):
            continue
        out[exd] = out.get(exd, 0.0) + amt
    return out


def parse_nav_hist() -> dict[date, float]:
    """navhist-us-en-spy.xlsx -> {date: nav} (dd-Mon-yyyy in col A)."""
    out: dict[date, float] = {}
    for r in xlsx_rows(NAV_XLSX):
        if not r or not r[0].strip():
            continue
        m = re.fullmatch(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", r[0].strip())
        if not m:
            continue
        months = {n: i for i, n in enumerate(
            ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
             "Sep", "Oct", "Nov", "Dec"), 1)}
        d = date(int(m.group(3)), months[m.group(2)], int(m.group(1)))
        try:
            out[d] = float(r[1].strip())
        except (ValueError, IndexError):
            continue
    return out


def parse_td(path: Path) -> dict[date, dict]:
    d = json.loads(path.read_text())
    return {date.fromisoformat(v["datetime"]): v for v in d["values"]}


def sessions(cal: USEquityRegularCalendar, s: date, e: date) -> list[date]:
    return [x.start_utc.astimezone(ET_ZONE).date()
            for x in cal.sessions_in_range(s, e)]


R = {"schema": "stocks_free_v2_a7/recompute@1"}

# ---------------- 3a: SPY price vs reconstructed TR vs NAV-TR ---------------- #
cal = US_EQUITY_REGULAR_V1
sess = sessions(cal, W_START, W_END)
R["window_sessions"] = len(sess)

spy = parse_td(SNAP / "SPY_none_p1.json")
spy_adj = parse_td(SNAP / "SPY_all_p1.json")
dist = parse_distributions("SPY")
nav = parse_nav_hist()

first, last = sess[0], sess[-1]
price_growth = float(spy[last]["close"]) / float(spy[first]["close"])

tr = 1.0
tr_level: dict[date, float] = {first: 1.0}
miss_dist = []
for prev, cur in zip(sess, sess[1:]):
    r = float(spy[cur]["close"]) / float(spy[prev]["close"])
    if cur in dist:
        r = (float(spy[cur]["close"]) + dist[cur]) / float(spy[prev]["close"])
    tr *= r
    tr_level[cur] = tr

# NAV-TR chain over all NAV dates in window (f_t = (nav_t + dist_t)/nav_{t-1})
nav_dates = sorted(nav)
navtr = 1.0
nav_in_win = [d for d in nav_dates if first <= d <= last]
for prev, cur in zip(nav_in_win, nav_in_win[1:]):
    num = nav[cur] + dist.get(cur, 0.0)
    navtr *= num / nav[prev]

tr_year: dict[int, float] = {}
yg = 1.0
for prev, cur in zip(sess, sess[1:]):
    r = tr_level[cur] / tr_level[prev]
    yg *= r
    if cur.year != prev.year:
        tr_year[prev.year] = yg
        yg = 1.0
tr_year[cur.year] = yg

# TD-adjusted growth over the same window (context only, NOT authority)
td_adj_growth = float(spy_adj[last]["close"]) / float(spy_adj[first]["close"])

R["spy"] = {
    "window": [first.isoformat(), last.isoformat()],
    "price_growth": round(price_growth, 6),
    "price_return_pct": round((price_growth - 1) * 100, 2),
    "recon_tr_growth_issuer": round(tr, 6),
    "nav_tr_growth": round(navtr, 6),
    "abs_divergence_recon_vs_nav": round(abs(tr - navtr), 6),
    "abs_divergence_pct": round(abs(tr - navtr) * 100, 3),
    "td_adjusted_growth_nonauthority": round(td_adj_growth, 6),
    "div_recon_vs_td_adj": round(abs(tr - td_adj_growth), 6),
    "spy_dist_events_in_window": len([d for d in dist if first <= d <= last]),
    "nav_rows_total": len(nav),
    "nav_rows_in_window": len(nav_in_win),
}

# --- gate-number reproduction over the exact DA2 window (2018-01-02..2026-08-28)
# DA2 probe payloads live in the staging-td root (sha256 prefixes recorded in
# da2_evidence.json); verify prefixes, then reproduce the recorded numbers.
STAGE_ROOT = SNAP.parent
d2_files = {"SPY_none_p1.json": "cec9c8642e292129", "SPY_adj_p1.json": "0479c2d253cc6e23"}
d2_prefix_ok = {n: sha256(STAGE_ROOT / n).startswith(p) for n, p in d2_files.items()}
spy_d2 = parse_td(STAGE_ROOT / "SPY_none_p1.json")
spy_adj_d2 = parse_td(STAGE_ROOT / "SPY_adj_p1.json")
D2_END = date(2026, 8, 28)
d2_sess = [d for d in sorted(spy_d2) if W_START <= d <= D2_END]
d2_first, d2_last = d2_sess[0], d2_sess[-1]
d2_nav = [d for d in nav_dates if W_START <= d <= D2_END]
navtr_d2 = 1.0
for prev, cur in zip(d2_nav, d2_nav[1:]):
    navtr_d2 *= (nav[cur] + dist.get(cur, 0.0)) / nav[prev]
price_d2 = float(spy_d2[d2_last]["close"]) / float(spy_d2[d2_first]["close"])
adj_d2 = float(spy_adj_d2[d2_last]["close"]) / float(spy_adj_d2[d2_first]["close"])
recon_d2 = 1.0
for p, c in zip(d2_sess, d2_sess[1:]):
    recon_d2 *= (float(spy_d2[c]["close"]) + dist.get(c, 0.0)) / float(spy_d2[p]["close"])
R["da2_gate_reproduction"] = {
    "window": ["2018-01-02", "2026-08-28"],
    "probe_payload_prefixes_ok": d2_prefix_ok,
    "td_price_growth": round(price_d2, 6),
    "td_adjusted_growth": round(adj_d2, 6),
    "ssga_nav_tr_growth": round(navtr_d2, 6),
    "abs_div_adj_vs_nav": round(abs(adj_d2 - navtr_d2), 6),
    "abs_div_recon_issuer_vs_nav": round(abs(recon_d2 - navtr_d2), 6),
}

# ---------------- 3b: XLK TD-implied steps vs issuer ---------------- #
xk_none = parse_td(SNAP / "XLK_none_p1.json")
xk_all = parse_td(SNAP / "XLK_all_p1.json")
xk_dist = parse_distributions("XLK")
dates = sorted(set(xk_none) & set(xk_all))
ratio = {d: float(xk_all[d]["close"]) / float(xk_none[d]["close"]) for d in dates}
steps = []
for a, b in zip(dates, dates[1:]):
    if abs(ratio[b] / ratio[a] - 1.0) > 1e-6:  # genuine adjustment step, not float noise
        y = 1.0 - ratio[a] / ratio[b]  # ratio grows forward; factor applies to pre-ex rows
        raw_prev = float(xk_none[a]["close"])
        steps.append({
            "step_after": a.isoformat(), "first_adj_date": b.isoformat(),
            "implied_yield": round(y, 8),
            "implied_dollars": round(y * raw_prev, 6),
            "issuer_ex_date": b.isoformat(),
            "issuer_amount": round(xk_dist.get(b, 0.0), 6),
            "ratio_implied_over_issuer": round(y * raw_prev / xk_dist[b], 4) if xk_dist.get(b) else None,
        })
matched = sum(1 for s_ in steps if s_["issuer_amount"] and 0.9 <= s_["ratio_implied_over_issuer"] <= 1.1)
doubled = sum(1 for s_ in steps if s_["issuer_amount"] and 1.7 <= s_["ratio_implied_over_issuer"] <= 2.3)
unmatched = [s_ for s_ in steps if not s_["issuer_amount"]]
R["xlk_td_steps"] = {
    "n_steps": len(steps), "n_1x_issuer": matched, "n_2x_issuer": doubled,
    "n_no_issuer_match": len(unmatched),
    "doubled_sample": [s_ for s_ in steps if 1.7 <= (s_["ratio_implied_over_issuer"] or 0) <= 2.3][:6],
    "unmatched_detail": [
        {"first_adj_date": s_["first_adj_date"], "implied_dollars": s_["implied_dollars"],
         "issuer_amount_on_that_date": s_["issuer_amount"],
         "issuer_amount_prev_or_next_day": [
             round(xk_dist.get(date.fromisoformat(s_["first_adj_date"]) - __import__("datetime").timedelta(days=dd), 0.0), 6)
             for dd in (1, 2, 3, 4)]}
        for s_ in unmatched[:20]],
    "issuer_events_in_window": len([d for d in xk_dist if first <= d <= last]),
}

# XLK recon TR with issuer amounts vs (counterfactual) TD-implied amounts
def recon_tr(none_map, dist_map, ss):
    g = 1.0
    for p, c in zip(ss, ss[1:]):
        r = float(none_map[c]["close"]) / float(none_map[p]["close"])
        if c in dist_map:
            r = (float(none_map[c]["close"]) + dist_map[c]) / float(none_map[p]["close"])
        g *= r
    return g

xk_sessions = [d for d in sess if d in xk_none]
td_implied_amt = {date.fromisoformat(s_["first_adj_date"]): s_["implied_dollars"] for s_ in steps}
R["xlk_tr"] = {
    "recon_growth_issuer": round(recon_tr(xk_none, xk_dist, xk_sessions), 6),
    "counterfactual_growth_td_implied": round(recon_tr(xk_none, td_implied_amt, xk_sessions), 6),
    "price_growth": round(float(xk_none[xk_sessions[-1]]["close"]) / float(xk_none[xk_sessions[0]]["close"]), 6),
}

# ---------------- 3c: census spot-check SPY + XLC ---------------- #
def bars_from(path, ws, we):
    d = parse_td(path)
    return {k: v for k, v in d.items() if ws <= k <= we}

def sane(v):
    o, h, l, c, vol = (float(v["open"]), float(v["high"]), float(v["low"]),
                       float(v["close"]), float(v["volume"]))
    return (o > 0 and l > 0 and c > 0 and vol >= 0 and h >= l
            and h >= max(o, c) and l <= min(o, c))

warmed = sessions(cal, date(2017, 6, 7), S0_START)
warmed_start = warmed[len(warmed) - 1 - 63]  # 63 sessions before S0 start (2018-04-04)
R["warmed_s0_start"] = warmed_start.isoformat()
R["warmed_matches_coverage_start"] = warmed_start == W_START

for sym, fname, inc_expected in (("SPY", "SPY_none_p1.json", None), ("XLC", "XLC_none_p1.json", None)):
    bars = bars_from(SNAP / fname, W_START, W_END)
    missing = [d for d in sess if d not in bars]
    insane = [d for d in bars if not sane(bars[d])]
    dup = len(bars) - len(set(bars))
    dv = sorted(float(bars[d]["close"]) * float(bars[d]["volume"]) for d in bars if d not in missing)
    all_dates = sorted(parse_td(SNAP / fname))
    inc = all_dates[0]
    # next-session executability (except final session)
    nxt_fail = 0
    for i, day in enumerate(sess):
        if i == len(sess) - 1:
            continue
        nd = sessions(cal, day, day + __import__("datetime").timedelta(days=10))
        nd = nd[1] if len(nd) > 1 else None
        if nd is None or nd not in bars or float(bars[nd]["close"]) <= 0:
            nxt_fail += 1
    tr_ok = all(float(x["close"]) > 0 for x in bars.values())  # recon TR points exist where close+issuer dist exists
    R.setdefault("census_spotcheck", {})[sym] = {
        "first_bar_in_snapshot": inc.isoformat(),
        "bars_in_window": len(bars), "missing_sessions": len(missing),
        "first_missing": [d.isoformat() for d in missing[:3]],
        "insane": len(insane), "duplicates": dup,
        "median_dollar_volume_usd": round(statistics.median(dv), 0),
        "floor_met": statistics.median(dv) >= 10_000_000.0,
        "next_session_failures": nxt_fail,
        "inception_before_warmed_start": inc < warmed_start,
    }

# cohort digest recompute (canonical semantics from frozen rule module)
from research.stocks_free_v1.cohort import (  # noqa: E402
    ACCEPTED,
    ALL_CHECKS_PASSED,
    CANDIDATE_SEEDS,
    CensusRow,
    canonical_cohort_digest,
)
roles = dict(CANDIDATE_SEEDS)
accepted = [("SPY", "2010-01-04"), ("XLK", "2010-01-04"), ("XLE", "2010-01-04"),
            ("XLF", "2010-01-04"), ("XLV", "2010-01-04"), ("XLI", "2010-01-04"),
            ("XLP", "2010-01-04"), ("XLY", "2010-01-04"), ("XLU", "2010-01-04"),
            ("XLB", "2010-01-04"), ("XLRE", "2015-10-08")]
rows = [CensusRow(symbol=s, role=roles[s], decision=ACCEPTED,
                  reasons=(ALL_CHECKS_PASSED,), checks=(),
                  inception_date=date.fromisoformat(i))
        for s, i in sorted(accepted)]
R["cohort_digest_recompute"] = canonical_cohort_digest(
    rows, window_start=W_START, window_end=W_END, warmup_sessions=63,
    dollar_volume_floor=10_000_000.0)

# ---------------- 4: partition derivation + SealedPathFilter ---------------- #
part = freeze_partition(coverage_start=W_START, coverage_end=W_END, calendar=cal)
R["partition"] = {
    "warmup": [part.warmup_start.isoformat(), part.warmup_end.isoformat()],
    "s0": [part.s0_start.isoformat(), part.s0_end.isoformat()],
    "s1": [part.s1_start.isoformat(), part.s1_end.isoformat()],
    "s0_complete_years": part.s0_complete_years,
    "s0_minimum_years_met": part.s0_minimum_years_met,
    "warmup_sessions": part.warmup_sessions,
    "folds": [(f.fold_id, f.start.isoformat(), f.end.isoformat(), f.scored_end.isoformat()) for f in part.folds],
}
allow = SealedPathFilter(allowed_roots=(str(WT / "data"),),
                         sealed_roots=(str(WT / "data" / "s1_root"),),
                         sealed_date_range=part.s1_start and (part.s1_start, part.s1_end))
R["sealed_filter"] = {
    "deny_s1_root": allow.reason_denied(WT / "data" / "s1_root" / "bars.csv"),
    "deny_embedded_s1_date": allow.reason_denied(WT / "data" / "daily" / "2026-03-05.csv"),
    "deny_boundary_start": allow.reason_denied(WT / "data" / "daily" / "2025-08-01.csv"),
    "deny_boundary_end": allow.reason_denied(WT / "data" / "daily" / "2026-07-31.csv"),
    "allow_s0_date": allow.reason_denied(WT / "data" / "daily" / "2025-07-31.csv"),
    "allow_normal": allow.reason_denied(WT / "data" / "daily" / "2019-01-02.csv"),
}

# ---------------- staged hashes recompute ---------------- #
man = json.loads((WT / "research/control/stocks_free_v2_run/snapshot_manifest.json").read_text())
hash_ok, hash_bad = [], []
for name, want in man["files"].items():
    got = sha256(SNAP / name)
    (hash_ok if got == want else hash_bad).append(name)
R["hashes"] = {"files_checked": len(man["files"]), "all_match": not hash_bad, "mismatched": hash_bad,
               "dist_workbook_sha256": sha256(DIST_XLSX),
               "dist_workbook_prefix_match": sha256(DIST_XLSX).startswith(man["issuer_evidence"]["spdr_distributions_sha256_prefix"]),
               "nav_workbook_sha256": sha256(NAV_XLSX)}

Path(__file__).with_name("recompute_result.json").write_text(json.dumps(R, indent=2))
print(json.dumps(R, indent=2))
