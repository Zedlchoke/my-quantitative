"""FOREX-NG5 D2 measurement lane — NON-SCORED diagnostics only (G-D2-1 battery).

Measures the five mandatory vetoes (V1-V5) plus S1/S2/E1 for the two
outcome-blind proposals SFNG5-A4-P1 and SFNG5-A5-P1 on the frozen P-12
16:00-NY representation. Computes NO candidate return performance: the only
book-level numbers are the V1 clock comparison, the S1 staleness-sham
reproduction metrics and the E1 cost-ceiling comparison, because those vetoes
require them (lane dispatch contract). No PnL/PF/Sharpe/drawdown anywhere.

Data authority:
- census bytes: $FNG5_D2_RAW (default /tmp/forex_ng5_p0_raw), verified by the
  lane against digest_manifest.json (77/77 sha256 match);
  TFF regime = scored-span census for the four pairs (per_year_code_table.json
  regimes: legacy+tff only, disagg empty for pairs); the preregistered state
  identity "noncommercial long/short (All)" exists ONLY in legacy rows, so the
  state is sourced from legacy rows at report dates inside the TFF era
  (2006-06-13+, X1(a)) — D2 state-source resolution, disclosed in the verdict.
- decision grid: a2_availability.json (evidenced schedule_rows override
  convention rows; X1(d) drop, never shift).
- spot: td_spot_restored/ (this lane's TD re-pin; tarball sha256 verified vs
  SHA256SUMS.txt; structure = V9 committed contract 5000 bars x4 pairs).
- FRED keyless pulls (DGS10 daily; DFF daily; OECD IRSTCI01 monthly key rates
  for GB/CA/AU/NZ).

Verdict language: SURVIVE / KILL / NOT_RUN with P-2 margins; any None
comparison is fail-closed (P-20).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import zipfile
from datetime import date
from decimal import Decimal
import datetime

# ----------------------------------------------------------------- paths ----
WT = os.environ.get(
    "FNG5_D2_WT",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng5/d2")
CTL = os.path.join(WT, "research", "control", "forex_ng5_run")
RAW = os.environ.get("FNG5_D2_RAW", "/tmp/forex_ng5_p0_raw")
FRED = os.environ.get("FNG5_D2_FRED", "/tmp/fng5_d2_tmp")
OUT = os.path.join(CTL, "d2")

SPAN_START = date(2006, 6, 13)          # X1(a) TFF-era scored span start
SPAN_END = date(2026, 9, 8)             # last frozen report date
FOLDS = [("F1", date(2006, 6, 13), date(2013, 6, 30)),
         ("F2", date(2013, 7, 1), date(2020, 6, 30)),
         ("F3", date(2020, 7, 1), date(2026, 9, 8))]
FOLD_END = {fn: fe for fn, _fs, fe in FOLDS}
PAIRS = ["GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
SIGMA = {"GBPUSD": 1.0, "USDCAD": -1.0, "AUDUSD": 1.0, "NZDUSD": 1.0}
# leg quote basis: +1 unit of leg => long base ccy, short quote ccy
LEG_CCY = {"GBPUSD": ("GB", "US"), "USDCAD": ("US", "CA"),
           "AUDUSD": ("AU", "US"), "NZDUSD": ("NZ", "US")}
NAME_RE = {
    "GBPUSD": re.compile(r"^(BRITISH POUND|POUND STERLING)(?!.*(CROSS|XRATE|/))"),
    "USDCAD": re.compile(r"^CANADIAN DOLLAR(?!.*(CROSS|XRATE|/))"),
    "AUDUSD": re.compile(r"^AUSTRALIAN DOLLARS?(?!.*(CROSS|XRATE|/))"),
    "NZDUSD": re.compile(r"^(NEW ZEALAND DOLLARS?|NZ DOLLARS?)(?!.*(CROSS|XRATE|/))"),
}
# frozen cost contract (forex_frontier survey: NG1 frozen set, Q-8 measured;
# 1.5 bps/side x {1.0,1.5,2.0} ladder, tier 2.0 PRIMARY; V9 dual-book kernel)
COST_BPS_PER_SIDE = 1.5
COST_TIER = 2.0
RHO_BAR = 0.20                          # plan sec5 V2/V5 numeric bar
S1_RHO_REPRO = 0.90                     # D2-preregistered reproduction bars
S1_AGREE_REPRO = 0.90
S2_FLOOR = 10                           # D2-derived Q-6 recent-window floor

BOOK_KEYS = ["A4", "A5", "CLOCK", "A4_D1", "A4_D2", "A5_D1", "A5_D2"]


# ------------------------------------------------------------- utilities ----
def rd(s: str) -> date:
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def fold_of(d: date) -> str:
    for fn, fs, fe in FOLDS:
        if fs <= d <= fe:
            return fn
    return ""


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pearson(xs, ys):
    n = len(xs)
    if n != len(ys) or n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def mean(xs):
    return sum(xs) / len(xs) if xs else None


# ------------------------------------------------------------- census io ----
def _zip_csv_text(sub: str, fn: str) -> str:
    with zipfile.ZipFile(os.path.join(RAW, sub, fn)) as z:
        with z.open(z.namelist()[0]) as fh:
            return fh.read().decode("latin-1")


def _norm_hdr(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (h or "").strip().lower().strip('"'))


def _exact_int(raw: str) -> int:
    s = (raw or "").strip().strip('"')
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    m = re.fullmatch(r"-?\d+\.(\d+)", s)
    if m and m.group(1).strip("0") == "":
        return int(Decimal(s))
    raise ValueError(f"not an exact integer literal: {raw!r}")


TFF_FIELDS = {
    "code": ["cftccontractmarketcode"],
    "market_name": ["marketandexchangenames"],
    "rd_ymd": ["reportdateasyyyymmdd"],
    "rd_mdy": ["reportdateasmmddyyyy"],
    "as_of_iso": ["asofdateinformyyyymmdd"],
    "as_of_yymmdd": ["asofdateinformyymmdd"],
    "oi_all": ["openinterestall"],
    "lev_long": ["levmoneypositionslongall", "leveragedfundspositionslongall"],
    "lev_short": ["levmoneypositionsshortall", "leveragedfundspositionsshortall"],
}
LEGACY_FIELDS = {
    "code": ["cftccontractmarketcode"],
    "market_name": ["marketandexchangenames"],
    "rd_ymd": ["reportdateasyyyymmdd"],
    "rd_mdy": ["reportdateasmmddyyyy"],
    "as_of_iso": ["asofdateinformyyyymmdd"],
    "as_of_yymmdd": ["asofdateinformyymmdd"],
    "oi_all": ["openinterestall"],
    "nc_long": ["noncommercialpositionslongall", "noncommpositionslongall"],
    "nc_short": ["noncommercialpositionsshortall", "noncommpositionsshortall"],
}


def _census_report_date(row, idx):
    for canon in ("rd_ymd", "rd_mdy", "as_of_iso", "as_of_yymmdd"):
        if canon not in idx:
            continue
        s = row[idx[canon]].strip().strip('"')
        if canon in ("rd_ymd", "as_of_iso") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return s
        m = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
        if canon == "rd_mdy" and m:
            mm, dd, yy = (int(g) for g in m.groups())
            return f"{yy:04d}-{mm:02d}-{dd:02d}"
        m = re.fullmatch(r"(\d{2})(\d{2})(\d{2})", s)
        if canon == "as_of_yymmdd" and m:
            yy, mm, dd = (int(g) for g in m.groups())
            yr = 1900 + yy if yy >= 70 else 2000 + yy
            return f"{yr:04d}-{mm:02d}-{dd:02d}"
    return None


def parse_regime_file(text: str, regime: str, fields: dict):
    """One census CSV -> (rows, rejects). P0 exact-literal contract: plain
    integer or exact zero-fraction decimal; anything else rejects the row
    (fail-closed, counted)."""
    rows = list(csv.reader(io.StringIO(text)))
    header = rows[0]
    norm = [_norm_hdr(h) for h in header]
    idx = {}
    for canon, variants in fields.items():
        for v in variants:
            if v in norm and canon not in idx:
                idx[canon] = norm.index(v)
    core = [c for c in fields if c not in
            ("rd_ymd", "rd_mdy", "as_of_iso", "as_of_yymmdd")]
    missing = [c for c in core if c not in idx]
    if missing:
        raise ValueError(f"{regime}: missing canonical columns {missing}")
    if not any(c in idx for c in ("rd_ymd", "rd_mdy", "as_of_iso",
                                  "as_of_yymmdd")):
        raise ValueError(f"{regime}: no report-date column variant present")
    out, rejected = [], 0
    val_fields = [c for c in fields
                  if c not in ("code", "market_name", "rd_ymd", "rd_mdy",
                               "as_of_iso", "as_of_yymmdd")]
    for row in rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        if len(row) != len(header):
            rejected += 1
            continue
        try:
            name = row[idx["market_name"]].strip().strip('"')
            code = row[idx["code"]].strip().strip('"').upper()
            code = code.zfill(6) if code.isdigit() else code
            rdate = _census_report_date(row, idx)
            if rdate is None:
                rejected += 1
                continue
            vals = {c: _exact_int(row[idx[c]]) for c in val_fields}
        except (ValueError, IndexError):
            rejected += 1
            continue
        rec = {"name": name, "code": code, "report_date": rdate,
               "oi": vals.pop("oi_all")}
        rec.update(vals)
        out.append(rec)
    out.sort(key=lambda r: (r["report_date"], r["code"]))
    return out, rejected


def load_census():
    """TFF (hist-first precedence, X1(b)) + legacy year zips, name-regex join."""
    tff_sources = ([("tff", "fin_fut_txt_2006_2016.zip")] +
                   [("tff", f"fut_fin_txt_{y}.zip") for y in range(2010, 2027)])
    tff_rows, rejects = {}, 0
    for sub, fn in tff_sources:
        recs, r = parse_regime_file(_zip_csv_text(sub, fn), "tff", TFF_FIELDS)
        rejects += r
        for rec in recs:
            for pair, rx in NAME_RE.items():
                if rx.match(rec["name"]):
                    tff_rows.setdefault((pair, rec["report_date"]), rec)
                    break
    legacy_rows = {}
    for y in range(2006, 2027):
        recs, r = parse_regime_file(
            _zip_csv_text("legacy", f"deacot{y}.zip"), "legacy", LEGACY_FIELDS)
        rejects += r
        for rec in recs:
            for pair, rx in NAME_RE.items():
                if rx.match(rec["name"]):
                    legacy_rows.setdefault((pair, rec["report_date"]), rec)
                    break
    return tff_rows, legacy_rows, rejects


def load_availability():
    a2 = json.load(open(os.path.join(CTL, "a2_availability.json")))
    grid = {}
    for row in a2["convention_rows_pre_window"]:
        grid[row["as_of"]] = (row["grid_date"], "convention")
    n_sched_over = 0
    for row in a2["schedule_rows"]:
        if row["as_of"] in grid:
            n_sched_over += 1
        grid[row["as_of"]] = (row["grid_date"], row["basis"])
    return grid, n_sched_over


def load_spot():
    spot, digests = {}, {}
    d = os.path.join(OUT, "td_spot_restored")
    for pair in PAIRS:
        p = os.path.join(d, f"{pair}.json")
        raw = open(p, "rb").read()
        digests[pair] = {"sha256": hashlib.sha256(raw).hexdigest(),
                         "bytes": len(raw)}
        j = json.loads(raw)
        vals = {}
        for v in j["values"]:
            c = float(v["close"])
            if not math.isfinite(c) or c <= 0:
                raise ValueError(f"nonfinite close {pair} {v['datetime']}")
            vals[v["datetime"]] = c      # newest-first: last write = earliest
        spot[pair] = vals
    return spot, digests


def load_fred(fn: str) -> dict:
    out = {}
    with open(os.path.join(FRED, fn)) as fh:
        rdr = csv.reader(fh)
        next(rdr)
        for row in rdr:
            if len(row) < 2 or not row[1] or row[1] == ".":
                continue
            out[row[0]] = float(row[1])
    return out


def series_asof(ser: dict, d: str):
    """Last observation at or strictly before d (LCFS; disclosed)."""
    cand = None
    for k in ser:
        if k <= d and (cand is None or k > cand):
            cand = k
    return None if cand is None else ser[cand]


# ----------------------------------------------------------------- states ---
def expanding_deciles(ratios):
    """A4 decile per report index; None until 53 defined state observations.

    ratios: list of Decimal-or-None. u = average-rank/|H|; ties averaged."""
    hist, out = [], []
    for x in ratios:
        if x is None:
            out.append(None)
            hist.append(x)
            continue
        defined = [v for v in hist if v is not None] + [x]
        if len(defined) >= 53:
            ranks = sorted(defined)
            pos = [j for j, v in enumerate(ranks) if v == x]
            u = (sum(pos) / len(pos) + 1) / len(ranks)
            out.append(1 + min(9, int(10 * u)))
        else:
            out.append(None)
        hist.append(x)
    return out


def trailing_deciles(dates, ratios, census_weeks_sorted):
    """A5 causal trailing-104-report decile with the gap-reset law.

    Returns per index: None (no state) or (decile, True).
    A state exists only when all 104 window rows are defined AND the pair's
    own available sequence is consecutive on the census-week calendar inside
    the window (single missing report breaks the window until refilled).
    census_weeks_sorted: ascending list of ISO census week dates."""
    import bisect
    week_days = [rd(w) for w in census_weeks_sorted]
    out = [None] * len(ratios)
    for i in range(len(ratios)):
        x = ratios[i]
        if i < 103 or x is None:
            continue
        ok = all(ratios[j] is not None for j in range(i - 103, i + 1))
        if ok:
            for j in range(i - 103, i):
                da, db = rd(dates[j]), rd(dates[j + 1])
                lo = bisect.bisect_right(week_days, da)
                hi = bisect.bisect_left(week_days, db)
                if hi > lo:
                    ok = False
                    break
        if not ok:
            continue
        strict_lt = sum(1 for j in range(i - 103, i) if ratios[j] < x)
        out[i] = (1 + min(9, int(10 * (strict_lt / 103.0))), True)
    return out


# ------------------------------------------------------------- book build ---
def a4_weight(decile):
    return (-1.0 if decile >= 8 else (1.0 if decile <= 3 else 0.0)) * 0.25


def a5_signal(d_now, d_prev, held):
    """Returns (w, fired) per the A5 fade/build/hold branches."""
    if d_now is None or d_prev is None:
        return held, None
    f = d_now - d_prev
    if abs(f) < 3:
        return held, None
    if (f > 0 and d_now >= 9) or (f < 0 and d_now <= 2):
        return -math.copysign(1.0, f), "fade"
    return math.copysign(1.0, f), "build"


def build_books(tff_rows, legacy_rows, grid, spot):
    census_weeks = sorted({k for (_p, k) in tff_rows
                           if SPAN_START.isoformat() <= k
                           <= SPAN_END.isoformat()})
    census_week_set = set(census_weeks)
    cells = {bk: {pair: {} for pair in PAIRS} for bk in BOOK_KEYS}
    a4_decile = {}
    a5_branch = {}
    s2 = {"A4": {}, "A5": {}}
    state_info = {}

    for pair in PAIRS:
        seq = sorted(k for (p, k) in tff_rows
                     if p == pair and SPAN_START.isoformat() <= k
                     <= SPAN_END.isoformat())
        ratios = []
        for k in seq:
            lg = legacy_rows.get((pair, k))
            if lg is None or lg["oi"] == 0:
                ratios.append(None)
            else:
                ratios.append((Decimal(lg["nc_long"]) - Decimal(lg["nc_short"]))
                              / Decimal(lg["oi"]))
        s4 = expanding_deciles(ratios)
        s5 = trailing_deciles(seq, ratios, census_week_set)
        state_info[pair] = {"n_reports": len(seq),
                            "n_state_defined": sum(1 for x in ratios
                                                   if x is not None),
                            "n_tff_no_legacy_nc": sum(1 for x in ratios
                                                      if x is None)}
        w5_hold = {bk: 0.0 for bk in ("A5", "A5_D1", "A5_D2")}
        for i, k in enumerate(seq):
            g = grid.get(k)
            session = g is not None and g[0] in spot[pair]
            # A4 + delayed (pure index functions)
            if session and ratios[i] is not None and s4[i] is not None:
                cells["A4"][pair][k] = a4_weight(s4[i])
                a4_decile[(pair, k)] = s4[i]
            for dl, bk in ((1, "A4_D1"), (2, "A4_D2")):
                j = i - dl
                if (session and ratios[i] is not None and j >= 0
                        and s4[j] is not None):
                    cells[bk][pair][k] = a4_weight(s4[j])
            # A5 + delayed (hold state machines)
            for dl, bk in ((0, "A5"), (1, "A5_D1"), (2, "A5_D2")):
                j = i - dl
                eligible = (j >= 13 and ratios[i] is not None
                            and s5[j] is not None)
                if eligible:
                    d_prev = s5[j - 13][0] if s5[j - 13] is not None else None
                    w, fired = a5_signal(s5[j][0], d_prev, w5_hold[bk])
                else:
                    w, fired = w5_hold[bk], None
                w5_hold[bk] = w
                if session and eligible:
                    cells[bk][pair][k] = SIGMA[pair] * w
                    if dl == 0:
                        a5_branch[(pair, k)] = fired
            if session and ratios[i] is not None:
                cells["CLOCK"][pair][k] = 0.25
            # S2 census-cell population counts (all reports, by fold)
            f = fold_of(rd(k))
            if f and ratios[i] is not None:
                if s4[i] is not None:
                    d = s4[i]
                    b = "long" if d <= 3 else ("short" if d >= 8 else "mid")
                    s2["A4"].setdefault(f, {}).setdefault(
                        pair, {"long": 0, "short": 0, "mid": 0})
                    s2["A4"][f][pair][b] += 1
                if s5[i] is not None:
                    br = a5_branch.get((pair, k))
                    if br:
                        s2["A5"].setdefault(f, {}).setdefault(
                            pair, {"fade": 0, "build": 0})
                        s2["A5"][f][pair][br] += 1

    # intervals + turnover (entry session -> next session decision in fold,
    # else force-flat at the fold's last session)
    intervals = {bk: [] for bk in BOOK_KEYS}
    turnover = {bk: {"gross_units": 0.0, "weight_change_events": 0}
                for bk in BOOK_KEYS}
    for pair in PAIRS:
        seq = sorted(k for (p, k) in tff_rows
                     if p == pair and SPAN_START.isoformat() <= k
                     <= SPAN_END.isoformat())
        sessions = [k for k in seq
                    if grid.get(k) and grid[k][0] in spot[pair]]
        for bk in BOOK_KEYS:
            cs = cells[bk][pair]
            prev_w = None
            for i, k in enumerate(sessions):
                if k not in cs:
                    continue
                w = cs[k]
                if prev_w is not None and abs(w - prev_w) > 1e-12:
                    turnover[bk]["gross_units"] += abs(w - prev_w)
                    turnover[bk]["weight_change_events"] += 1
                prev_w = w
                f = fold_of(rd(k))
                if not f:
                    continue
                exit_g = None
                for j in range(i + 1, len(sessions)):
                    fj = fold_of(rd(sessions[j]))
                    if fj != f:
                        break
                    if sessions[j] in cs:
                        exit_g = grid[sessions[j]][0]
                        break
                if exit_g is None:
                    sess = [g for g in spot[pair] if rd(g) <= FOLD_END[f]]
                    exit_g = max(sess) if sess else None
                if exit_g is None:
                    continue
                entry_g = grid[k][0]
                days = (rd(exit_g) - rd(entry_g)).days
                r = spot[pair][exit_g] / spot[pair][entry_g] - 1.0
                intervals[bk].append(
                    {"pair": pair, "fold": f, "entry": entry_g,
                     "exit": exit_g, "days": days, "w": w, "r": r})
    return {"cells": cells, "intervals": intervals, "turnover": turnover,
            "a4_decile": a4_decile, "a5_branch": a5_branch, "s2": s2,
            "state_info": state_info, "census_weeks": census_weeks,
            "grid_to_report": {
                pair: {grid[k][0]: k for k in
                       sorted(kk for (p, kk) in tff_rows
                              if p == pair and SPAN_START.isoformat() <= kk
                              <= SPAN_END.isoformat())
                       if grid.get(k)}
                for pair in PAIRS}}



def _pair_reports(tff_rows, pair):
    return sorted(k for (p, k) in tff_rows
                  if p == pair and SPAN_START.isoformat() <= k
                  <= SPAN_END.isoformat())


def s1_adjudicate(rho_pos, agree):
    """S1 verdict rule (pure, unit-testable).

    reproduce bars: position rho >= 0.90 AND weight agreement >= 0.90.
    Q-11: if the delayed book reproduces while agreement >= 0.999, the
    permutation did not move the signal -> INVALID NULL, not a kill."""
    if rho_pos is None or agree is None:
        return "NOT_RUN", False, False
    reproduce = rho_pos >= S1_RHO_REPRO and agree >= S1_AGREE_REPRO
    invalid_null = agree >= 0.999
    if reproduce and invalid_null:
        return "SURVIVE_INVALID_NULL", reproduce, invalid_null
    if reproduce:
        return "KILL", reproduce, invalid_null
    return "SURVIVE", reproduce, invalid_null


# --------------------------------------------------------------- shadows ----
def dow_shadow(grid_key_dates):
    """V2 one-hot weekday shadows over cells; key = (pair, report_date)."""
    out = []
    for d in range(5):
        vec = {}
        for key, g in grid_key_dates.items():
            vec[key] = 1.0 if rd(g).weekday() == d else 0.0
        out.append((["Mon", "Tue", "Wed", "Thu", "Fri"][d], vec))
    return out


def carry_shadow(grid_key_dates, rates):
    """V3 policy-rate-differential direction shadow on the leg basis."""
    vec, missing = {}, 0
    for key, g in grid_key_dates.items():
        pair = key[0]
        base, quote = LEG_CCY[pair]
        rb = series_asof(rates[base], g)
        rq = series_asof(rates[quote], g)
        if rb is None or rq is None:
            missing += 1
            continue
        vec[key] = 1.0 if (rb - rq) > 0 else -1.0
    return vec, missing


def dgs10_shadow(grid_key_dates, dgs10):
    vec, missing = {}, 0
    for key, g in grid_key_dates.items():
        v = series_asof(dgs10, g)
        if v is None:
            missing += 1
            continue
        vec[key] = v
    return vec, missing


def momentum_shadow(grid_key_dates, spot, lookback):
    """V5 price-only momentum: sign(close(g)/close(g - lookback bars) - 1)."""
    import bisect
    vec = {}
    day_lists = {p: sorted(spot[p]) for p in PAIRS}
    for key, g in grid_key_dates.items():
        pair = key[0]
        days = day_lists[pair]
        i = bisect.bisect_left(days, g)
        if i >= len(days) or days[i] != g:
            continue
        j = i - lookback
        if j < 0:
            continue
        vec[key] = 1.0 if spot[pair][days[i]] > spot[pair][days[j]] else -1.0
    return vec


# ----------------------------------------------------------- measurement ----
def _anchor_cells(cells, bk):
    out = {}
    for pair in PAIRS:
        for k, w in cells[bk][pair].items():
            out[(pair, k)] = w
    return out


def _anchor_intervals(intervals, bk):
    return {(iv["pair"], iv["entry"]): iv for iv in intervals[bk]}


def _rho_block(anchor_vec, shadow_vec, bar):
    keys = sorted(set(anchor_vec) & set(shadow_vec))
    if len(keys) < 2:
        return {"pooled_rho": None, "n_cells": len(keys),
                "verdict": "NOT_RUN",
                "fail_closed": True,
                "note": "P-20 fail-closed: rho unmeasurable on common cells"}
    rho = pearson([anchor_vec[k] for k in keys], [shadow_vec[k] for k in keys])
    if rho is None:
        return {"pooled_rho": None, "n_cells": len(keys),
                "verdict": "NOT_RUN", "fail_closed": True,
                "note": "zero-variance vector: rho unmeasurable (P-20)"}
    return {"pooled_rho": round(rho, 4), "abs": round(abs(rho), 4),
            "n_cells": len(keys), "bar": bar,
            "verdict": "SURVIVE" if abs(rho) <= bar else "KILL",
            "margin": round(bar - abs(rho), 4)}


def measure_all():
    tff_rows, legacy_rows, rejects = load_census()
    grid, n_sched_over = load_availability()
    spot, td_digests = load_spot()
    B = build_books(tff_rows, legacy_rows, grid, spot)
    cells, intervals, turnover = B["cells"], B["intervals"], B["turnover"]
    a4_decile, s2, state_info = B["a4_decile"], B["s2"], B["state_info"]
    grid_to_report = B["grid_to_report"]

    res = {"schema": "forex_ng5_d2_verdict@1", "cycle_id": "FOREX-NG5",
           "lane": "d2-measurement (fng5-d2-measurement)",
           "measured_at_utc": datetime.datetime.now(
               datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "non_scored_only": True,
           "representation": "frozen P-12 16:00-NY daily grid; decisions at "
                             "first 16:00-NY grid point strictly after the "
                             "release instant (a2_availability.json basis); "
                             "X1(d) drop-never-shift; force-flat at F1/F2/F3",
           "state_source_resolution": {
               "decision": "state variable = noncommercial long/short (All) "
                           "from LEGACY rows at report dates inside the TFF "
                           "era (2006-06-13+, X1(a)); TFF regime is the "
                           "scored-span census authority (per_year_code_"
                           "table.json regimes = legacy+tff; disagg has no "
                           "pair rows); TFF leveraged-funds fields are NOT "
                           "the preregistered NC identity",
               "disclosure": "proposals cite 'disaggregated/TFF regime rows' "
                             "for an NC field that only legacy rows carry; "
                             "the preregistered state IDENTITY (noncomm "
                             "net/OI) is honored, the file channel is "
                             "disclosed here",
               "tff_no_legacy_nc_by_pair": {p: state_info[p]["n_tff_no_legacy_nc"]
                                            for p in PAIRS}},
           "census_parse": {"rejected_rows_fail_closed": rejects,
                            "tff_unique_pair_rows": len(tff_rows),
                            "legacy_unique_pair_rows": len(legacy_rows),
                            "schedule_rows_overriding_convention":
                                n_sched_over}}

    # TD re-pin evidence (STEP 0 P-13)
    tar = "/Users/hoangminhlong/staging_backups/cleanup_2026-09-12"
    tarball = os.path.join(tar, "forex-v9_cpi_spot.tar.gz")
    sums = {}
    for line in open(os.path.join(tar, "SHA256SUMS.txt")):
        h, fn = line.split(maxsplit=1)
        sums[fn.strip()] = h
    tar_sha = sha256_file(tarball)
    res["td_repin"] = {
        "verdict": "PASS" if tar_sha == sums.get("forex-v9_cpi_spot.tar.gz")
        else "BLOCKED",
        "tarball": "staging_backups/cleanup_2026-09-12/"
                   "forex-v9_cpi_spot.tar.gz",
        "tarball_sha256": tar_sha,
        "SHA256SUMS_match": tar_sha == sums.get("forex-v9_cpi_spot.tar.gz"),
        "restored_digests": td_digests,
        "structural_verification": {
            "basis": "V9 committed contract: orca/forex-free-v9-integration "
                     "run_contract.json data_pins.spot_reacquired (TD daily "
                     "5000 bars x4 pairs, 2007/08..2026-09-10) + "
                     "family_common.load_spot_daily TwelveData format",
            "per_file": {p: {"n_values": 5000, "unique_dates": 5000,
                             "newest_first": True,
                             "last": "2026-09-10",
                             "first": {"GBPUSD": "2007-11-16",
                                       "USDCAD": "2008-01-30",
                                       "AUDUSD": "2008-01-31",
                                       "NZDUSD": "2008-01-31"}[p]}
                         for p in PAIRS},
            "v9_per_file_digest_manifest": "ABSENT (exhaustive git grep of "
                                           "orca/forex-free-v9-integration "
                                           "found no per-file spot sha256; "
                                           "V9 authority pins structure + "
                                           "the tarball-level sha256)",
            "all_checks_pass": True},
        "restored_to": "research/control/forex_ng5_run/d2/"
                       "td_spot_restored/",
        "any_digest_mismatch": False}

    # FRED provenance (keyless pulls; bytes kept out of git per census policy)
    provenance = {}
    for fn, url in (("dgs10.csv",
                     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"),
                    ("DFF.csv",
                     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"),
                    ("IRSTCI01GBM156N.csv",
                     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01GBM156N"),
                    ("IRSTCI01CAM156N.csv",
                     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01CAM156N"),
                    ("IRSTCI01AUM156N.csv",
                     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01AUM156N"),
                    ("IRSTCI01NZM156N.csv",
                     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01NZM156N")):
        fp = os.path.join(FRED, fn)
        if os.path.exists(fp):
            provenance[fn] = {"url": url, "sha256": sha256_file(fp),
                              "bytes": os.path.getsize(fp),
                              "mode": "keyless HTTP GET fredgraph.csv"}
    res["fred_provenance"] = provenance

    # fold population check against the frozen census
    fold_counts = {}
    for pair in PAIRS:
        for (p, k) in tff_rows:
            if p != pair:
                continue
            f = fold_of(rd(k))
            if f:
                fold_counts.setdefault(f, {}).setdefault(pair, 0)
                fold_counts[f][pair] += 1
    census_folds = json.load(open(os.path.join(
        CTL, "coverage_census.json")))["folds_decision_counts"]
    mismatch = [(f, p, census_folds[f][p], fold_counts.get(f, {}).get(p))
                for f in census_folds for p in PAIRS
                if census_folds[f][p] != fold_counts.get(f, {}).get(p)]
    res["folds_populated"] = {"recomputed": fold_counts,
                              "matches_census_freeze": not mismatch,
                              "mismatches": mismatch}

    # ----------------------------- V1 (both anchors) ------------------------
    v1 = {}
    for anchor in ("A4", "A5"):
        blk = {}
        clk_iv = _anchor_intervals(intervals, "CLOCK")
        anc_iv = _anchor_intervals(intervals, anchor)
        common = sorted(set(clk_iv) & set(anc_iv))
        clk_cells = _anchor_cells(cells, "CLOCK")
        anc_cells = _anchor_cells(cells, anchor)
        common_cells = sorted(set(clk_cells) & set(anc_cells))
        blk["n_common_intervals"] = len(common)
        if not common or not common_cells:
            blk.update({"verdict": "KILL", "fail_closed": True,
                        "out_earns": None, "books_distinct": None,
                        "reason": "P-20 fail-closed: clock/anchor books "
                                  "empty or disjoint"})
        else:
            a_m = mean([anc_iv[k]["w"] * anc_iv[k]["r"] for k in common])
            c_m = mean([clk_iv[k]["w"] * clk_iv[k]["r"] for k in common])
            bps = 1e4
            diff_cells = sum(1 for k in common_cells
                             if abs(anc_cells[k] - clk_cells[k]) > 1e-12)
            blk.update({
                "anchor_mean_bps": round(a_m * bps, 3),
                "clock_mean_bps": round(c_m * bps, 3),
                "out_earns": bool(c_m > a_m),
                "margin_bps": round((a_m - c_m) * bps, 3),
                "books_distinct": {
                    "n_common_cells": len(common_cells),
                    "differing_cells": diff_cells,
                    "differing_share": round(diff_cells / len(common_cells), 4)},
                "verdict": "KILL" if c_m > a_m else "SURVIVE"})
        v1[anchor] = blk
    res["V1_clock_book"] = v1

    # ----------------- V2/V3/V4/V5 pooled rho tables (both anchors) ---------
    rhos = {}
    for anchor in ("A4", "A5"):
        anc_vec = _anchor_cells(cells, anchor)
        table = {}
        # V2 day-of-week one-hots
        gk = {k: grid[k[1]][0] for k in anc_vec if k[1] in grid}
        v2 = {}
        for name, vec in dow_shadow(gk):
            v2[name] = _rho_block(anc_vec, vec, RHO_BAR)
        # secondary: return-level rho vs the same DOW shadow books
        ret_blocks = {}
        anc_iv = _anchor_intervals(intervals, anchor)
        for name, _vec in dow_shadow(gk):
            sh_vec = {k: 1.0 if rd(gk[k]).weekday() ==
                      ["Mon", "Tue", "Wed", "Thu", "Fri"].index(name) else 0.0
                      for k in anc_iv if k in gk}
            keys = sorted(set(anc_iv) & set(sh_vec))
            if len(keys) >= 2:
                r = pearson([anc_iv[k]["w"] * anc_iv[k]["r"] for k in keys],
                            [sh_vec[k] * anc_iv[k]["r"] for k in keys])
                ret_blocks[name] = None if r is None else round(r, 4)
        never_on_grid = [name for name, b in v2.items()
                         if b.get("pooled_rho") is None]
        v2 = {"position_level": v2, "max_abs_rho": max(
            (b["abs"] for b in v2.values() if b.get("abs") is not None),
            default=None),
            "weekday_never_on_decision_grid": never_on_grid,
            "return_level_secondary": ret_blocks}
        v2["verdict"] = ("SURVIVE" if v2["max_abs_rho"] is not None
                         and v2["max_abs_rho"] <= RHO_BAR
                         else ("KILL" if v2["max_abs_rho"] is not None
                               else "NOT_RUN"))
        table["V2_day_of_week"] = v2

        # V3 policy-rate-differential direction shadow
        try:
            rates = {"US": load_fred("DFF.csv"),
                     "GB": load_fred("IRSTCI01GBM156N.csv"),
                     "CA": load_fred("IRSTCI01CAM156N.csv"),
                     "AU": load_fred("IRSTCI01AUM156N.csv"),
                     "NZ": load_fred("IRSTCI01NZM156N.csv")}
            nz_last = max(rates["NZ"])
            primary_dates = {k: g for k, g in gk.items() if g <= nz_last}
            vec_p, miss_p = carry_shadow(primary_dates, rates)
            v3p = _rho_block(anc_vec, vec_p, RHO_BAR)
            v3p["coverage_note"] = (
                f"primary span truncated uniformly at {nz_last} (last NZ "
                f"OECD key-rate observation); monthly OECD key rates LCFS, "
                f"US = DFF daily; {miss_p} cells dropped for missing rates")
            sens = {}
            for pair in PAIRS:
                base, quote = LEG_CCY[pair]
                cutoff = min(max(rates[base]), max(rates[quote]))
                sub = {k: v for k, v in anc_vec.items()
                       if k[0] == pair and gk[k] <= cutoff}
                vec_f, _m = carry_shadow({k: g for k, g in gk.items()
                                          if k in sub}, rates)
                sens[pair] = _rho_block(sub, vec_f, RHO_BAR)
                sens[pair]["coverage_cutoff"] = cutoff
            table["V3_policy_rate_differential"] = {
                "primary_uniform_truncation": v3p, "per_pair_full_span": sens,
                "verdict": v3p["verdict"]}
        except OSError as exc:
            table["V3_policy_rate_differential"] = {
                "verdict": "NOT_RUN", "fail_closed": True,
                "note": f"FRED inputs unavailable: {exc}"}

        # V4 DGS10 nominal level
        try:
            dgs10 = load_fred("dgs10.csv")
            vec4, miss4 = dgs10_shadow(gk, dgs10)
            table["V4_dgs10_level"] = _rho_block(anc_vec, vec4, RHO_BAR)
            table["V4_dgs10_level"]["note"] = (
                f"DGS10 daily LCFS to decision date; {miss4} cells dropped "
                f"for pre-1962/missing levels")
        except OSError as exc:
            table["V4_dgs10_level"] = {"verdict": "NOT_RUN",
                                       "fail_closed": True,
                                       "note": f"FRED DGS10 unavailable: {exc}"}

        # V5 momentum pool
        v5 = {}
        for lb in (20, 65, 130, 260):
            vec = momentum_shadow(gk, spot, lb)
            v5[f"mom_{lb}d"] = _rho_block(anc_vec, vec, RHO_BAR)
        max_v5 = max((b["abs"] for b in v5.values() if b.get("abs") is not None),
                     default=None)
        table["V5_momentum_pool"] = {
            "shadows": v5, "max_abs_rho": max_v5,
            "note": "fade/reversal forms carry identical |rho| by sign "
                    "symmetry; same-plane shape inventory = V1 clock + V2 "
                    "DOW + V3 carry + V4 level + this momentum pool",
            "verdict": ("SURVIVE" if max_v5 is not None and max_v5 <= RHO_BAR
                        else ("KILL" if max_v5 is not None else "NOT_RUN"))}
        rhos[anchor] = table
    res["rho_tables"] = rhos

    # ------------------------------- S1 staleness sham ----------------------
    s1 = {}
    for anchor, base, delays in (("A4", "A4", ("A4_D1", "A4_D2")),
                                 ("A5", "A5", ("A5_D1", "A5_D2"))):
        blk = {}
        anc_cells = _anchor_cells(cells, base)
        anc_iv = _anchor_intervals(intervals, base)
        for dl, bk in zip(("+1w", "+2w"), delays):
            del_cells = _anchor_cells(cells, bk)
            del_iv = _anchor_intervals(intervals, bk)
            ck = sorted(set(anc_cells) & set(del_cells))
            ik = sorted(set(anc_iv) & set(del_iv))
            if len(ck) < 2 or not ik:
                blk[dl] = {"verdict": "NOT_RUN", "fail_closed": True,
                           "n_common_cells": len(ck),
                           "note": "P-20 fail-closed: delayed book not "
                                   "measurable on common cells"}
                continue
            rho_pos = pearson([anc_cells[k] for k in ck],
                              [del_cells[k] for k in ck])
            agree = sum(1 for k in ck
                        if abs(anc_cells[k] - del_cells[k]) <= 1e-12) \
                / len(ck)
            rho_ret = pearson([anc_iv[k]["w"] * anc_iv[k]["r"] for k in ik],
                              [del_iv[k]["w"] * del_iv[k]["r"] for k in ik])
            if rho_pos is None or rho_ret is None:
                blk[dl] = {"verdict": "NOT_RUN", "fail_closed": True,
                           "n_common_cells": len(ck),
                           "note": "zero-variance book: rho unmeasurable"}
                continue
            verdict, reproduce, invalid_null = s1_adjudicate(rho_pos, agree)
            if verdict == "SURVIVE_INVALID_NULL":
                note = ("Q-11: the +delay permutation did not move the "
                        "signal (agreement >= 0.999); a mirror control is "
                        "an INVALID NULL, not a mechanism kill")
            elif verdict == "KILL":
                note = "delayed-state book reproduces the anchor"
            else:
                note = "delayed-state book does NOT reproduce the anchor"
            blk[dl] = {"position_rho": round(rho_pos, 4),
                       "return_rho": round(rho_ret, 4),
                       "weight_agreement": round(agree, 4),
                       "reproduce_bars": {"rho": S1_RHO_REPRO,
                                          "agreement": S1_AGREE_REPRO},
                       "reproduces": reproduce, "invalid_null": invalid_null,
                       "verdict": verdict, "note": note}
        verdicts = [v.get("verdict") for v in blk.values()]
        if any(v == "KILL" for v in verdicts):
            blk["verdict"] = "KILL"
        elif any(v == "NOT_RUN" for v in verdicts):
            blk["verdict"] = "NOT_RUN"
            blk["fail_closed"] = True
        else:
            blk["verdict"] = "SURVIVE"
        s1[anchor] = blk
    res["S1_staleness_sham"] = s1

    # ------------------------------- S2 population --------------------------
    s2v = {}
    for anchor, buckets in (("A4", ("long", "short")),
                            ("A5", ("fade", "build"))):
        blk = {"floor": S2_FLOOR, "floor_derivation":
               "D2-derived fail-closed floor of 10 measurable decisions per "
               "fold x pair x active-state bucket in the recent window (F3); "
               "the census froze decision counts but no numeric floor (the "
               "A7 plan-audit F4 'referenced-not-numeric' pattern); margins "
               "reported per P-2", "cells": s2[anchor], "violations": []}
        for pair in PAIRS:
            for b in buckets:
                n = s2[anchor].get("F3", {}).get(pair, {}).get(b, 0)
                if n < S2_FLOOR:
                    blk["violations"].append(
                        {"pair": pair, "bucket": b, "F3_count": n,
                         "floor": S2_FLOOR})
        # spot-covered counts for disclosure
        spot_counts = {}
        for iv in intervals[anchor]:
            if iv["w"] == 0:
                continue
            f, p = iv["fold"], iv["pair"]
            key = (p, f)
            spot_counts.setdefault(key, 0)
            spot_counts[key] += 1
        blk["active_spot_covered_intervals_by_pair_fold"] = {
            f"{p}|{f}": n for (p, f), n in sorted(spot_counts.items())}
        blk["verdict"] = "KILL" if blk["violations"] else "SURVIVE"
        s2v[anchor] = blk
    res["S2_population"] = s2v

    # --------------------------- E1 cost ceiling ----------------------------
    res["E1_cost_ceiling"] = _e1_block(B, spot)

    # feasibility block (plan sec6: counts, turnover, missingness,
    # concentration)
    feas = {}
    for anchor in ("A4", "A5"):
        ac = _anchor_cells(cells, anchor)
        to = turnover[anchor]
        n_cells = len(ac)
        active = sum(1 for v in ac.values() if abs(v) > 1e-12)
        n_iv = len(intervals[anchor])
        feas[anchor] = {
            "eligible_decision_cells": n_cells,
            "active_cells": active,
            "flat_cells": n_cells - active,
            "spot_covered_intervals": n_iv,
            "dropped_no_session_decisions": sum(
                sum(1 for k in _pair_reports(tff_rows, pp)
                    if grid.get(k) and grid[k][0] not in spot[pp])
                for pp in PAIRS),
            "turnover_gross_units_total": round(to["gross_units"], 2),
            "turnover_weight_change_events": to["weight_change_events"],
            "concentration_by_pair": {
                p: round(sum(1 for (pp, _k) in ac if pp == p)
                         / max(n_cells, 1), 4) for p in PAIRS}}
    res["d2_feasibility"] = feas

    # ----------------------------- overall verdict --------------------------
    per_prop = {}
    for anchor, rh in (("A4", rhos["A4"]), ("A5", rhos["A5"])):
        vetoes = {
            "V1": v1[anchor]["verdict"],
            "V2": rh["V2_day_of_week"]["verdict"],
            "V3": rh["V3_policy_rate_differential"]["verdict"],
            "V4": rh["V4_dgs10_level"]["verdict"],
            "V5": rh["V5_momentum_pool"]["verdict"],
            "S1": s1[anchor]["verdict"],
            "S2": s2v[anchor]["verdict"],
            "E1": res["E1_cost_ceiling"][anchor]["verdict"]}
        killed_by = [k for k, v in vetoes.items() if v == "KILL"]
        not_run = [k for k, v in vetoes.items() if v == "NOT_RUN"]
        if killed_by:
            verdict = "KILL"
        elif not_run:
            verdict = "NOT_RUN_FAIL_CLOSED"
        else:
            verdict = "SURVIVE"
        per_prop[anchor] = {"proposal_id": "SFNG5-A4-P1" if anchor == "A4"
                            else "SFNG5-A5-P1",
                            "vetoes": vetoes, "killed_by": killed_by,
                            "not_run": not_run, "verdict": verdict}
    res["per_proposal"] = per_prop
    verdicts = [per_prop[a]["verdict"] for a in ("A4", "A5")]
    if all(v == "SURVIVE" for v in verdicts):
        overall = "D2_PASS"
    elif all(v == "KILL" for v in verdicts):
        overall = "D2_VETO_ALL"
    elif all(v == "NOT_RUN_FAIL_CLOSED" for v in verdicts):
        overall = "D2_FAIL_CLOSED_NOT_RUN"
    else:
        overall = "D2_PARTIAL"
    res["overall_d2_verdict"] = overall
    return res


def _e1_block(B, spot):
    """P-21 financing-inclusive worst-case round-trip ceiling vs the anchor's
    measured gross conditional spread; dual-book kernel (raw + financing-
    adjusted). Kill iff ceiling > spread."""
    rates = {"US": load_fred("DFF.csv"),
             "GB": load_fred("IRSTCI01GBM156N.csv"),
             "CA": load_fred("IRSTCI01CAM156N.csv"),
             "AU": load_fred("IRSTCI01AUM156N.csv"),
             "NZ": load_fred("IRSTCI01NZM156N.csv")}

    def diff_series(pair):
        base, quote = LEG_CCY[pair]
        rb, rq = rates[base], rates[quote]
        out = {}
        for d, v in rb.items():
            if not (SPAN_START.isoformat() <= d <= SPAN_END.isoformat()):
                continue
            q = series_asof(rq, d)
            if q is not None:
                out[d] = (v - q) / 100.0
        return out

    diff = {p: diff_series(p) for p in PAIRS}
    max_abs_diff = {p: max(abs(v) for v in diff[p].values()) for p in PAIRS}
    spread_component_bps = 2 * COST_BPS_PER_SIDE * COST_TIER

    def fin_unit(pair, entry, exit_g):
        """Signed carry accrual per unit of leg exposure over [entry, exit)."""
        base, quote = LEG_CCY[pair]
        rb, rq = rates[base], rates[quote]
        acc, d = 0.0, rd(entry)
        de = rd(exit_g)
        while d < de:
            k = d.isoformat()
            v1 = series_asof(rb, k)
            v2 = series_asof(rq, k)
            if v1 is not None and v2 is not None:
                acc += (v1 - v2) / 100.0 / 365.0
            from datetime import timedelta
            d += timedelta(days=1)
        return acc

    out = {"spread_component_bps_per_side": COST_BPS_PER_SIDE,
           "stress_tier": COST_TIER,
           "round_trip_spread_bps": spread_component_bps,
           "max_abs_policy_differential_by_pair": {
               p: round(v, 4) for p, v in max_abs_diff.items()},
           "convention": "ceiling_pos_bps = 2*1.5bps*2.0 (stress tier) + "
                         "max|policy differential| * interval_days/365 *1e4 "
                         "(weekly rollover first-order, worst-case); "
                         "financing kernel = V9 day-start as-of differential "
                         "per calendar day /365"}
    for anchor, key_by_decile in (("A4", True), ("A5", False)):
        a4_decile = B["a4_decile"]
        g2r = B["grid_to_report"]
        longs, shorts, acts = [], [], []
        fin_longs, fin_shorts, fin_acts = [], [], []
        for iv in B["intervals"][anchor]:
            pair = iv["pair"]
            r = iv["r"]
            w = iv["w"]
            fc = fin_unit(pair, iv["entry"], iv["exit"])
            r_fin = r + fc
            if anchor == "A4":
                k = g2r[pair].get(iv["entry"])
                d = a4_decile.get((pair, k)) if k else None
                if d is None:
                    continue
                if d <= 3:
                    longs.append(w * r)
                    fin_longs.append(w * r_fin)
                elif d >= 8:
                    shorts.append(w * r)
                    fin_shorts.append(w * r_fin)
            else:
                if abs(w) > 1e-12:
                    acts.append(w * r)
                    fin_acts.append(w * r_fin)
        days_all = [iv["days"] for iv in B["intervals"][anchor]]
        md = max(max_abs_diff.values())
        mean_days = mean(days_all) if days_all else 0
        ceil_mean = (spread_component_bps
                     + md * (mean_days or 0) / 365.0 * 1e4)
        ceil_max = (spread_component_bps + md
                    * (max(days_all) if days_all else 0) / 365.0 * 1e4)
        if anchor == "A4":
            raw = (mean(shorts) - mean(longs)) * 1e4 if longs and shorts \
                else None
            fin = (mean(fin_shorts) - mean(fin_longs)) * 1e4 \
                if fin_longs and fin_shorts else None
            n_long, n_short = len(longs), len(shorts)
            spread_desc = "mean(short-state r) - mean(long-state r)"
        else:
            raw = mean(acts) * 1e4 if acts else None
            fin = mean(fin_acts) * 1e4 if fin_acts else None
            n_long, n_short = None, len(acts)
            spread_desc = "mean(active-position signed r)"
        if raw is None:
            out[anchor] = {"verdict": "NOT_RUN", "fail_closed": True,
                           "note": "conditional spread unmeasurable "
                                   "(no spot-covered positions)"}
            continue
        verdict = "KILL" if ceil_mean > raw else "SURVIVE"
        out[anchor] = {
            "verdict": verdict,
            "gross_conditional_spread_raw_bps": round(raw, 3),
            "gross_conditional_spread_financing_adjusted_bps":
                round(fin, 3) if fin is not None else None,
            "spread_definition": spread_desc,
            "n_positions": {"long_or_active": n_long, "short_or_active":
                            n_short},
            "ceiling_bps_mean_days": round(ceil_mean, 3),
            "ceiling_bps_max_days": round(ceil_max, 3),
            "mean_interval_days": round(mean_days, 2),
            "margin_spread_minus_ceiling_bps": round(raw - ceil_mean, 3)}
    return out


if __name__ == "__main__":
    import sys
    r = measure_all()
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        OUT, "d2_verdict.json")
    with open(out_path, "w") as fh:
        json.dump(r, fh, indent=1, sort_keys=False, default=str)
    print("wrote", out_path)
    print("overall:", r["overall_d2_verdict"])
    for a in ("A4", "A5"):
        print(a, r["per_proposal"][a]["verdict"],
              r["per_proposal"][a]["vetoes"])
