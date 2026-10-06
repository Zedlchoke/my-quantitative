#!/usr/bin/env python3
"""finalize_analysis.py — offline (ZERO network). Computes:
  - per-package disk-gate verdicts from the measured disk snapshot + billables
  - per-hypothesis vendor-data support per package (A / A-v1 / B / C)
  - coverage table rows
Writes analysis_summary.json beside coverage_results.json.

POST-AUDIT REVISION (audit/acq_skeptic/ACQ_SKEPTIC_AUDIT.md, 2026-10-02):
  MAJOR-1 — depth floors are now evaluated on EACH REQUIREMENT's symbols,
  not the hypothesis's own root: a requirement on symbols outside the
  10-root corpus (CL-H3's [RB, HO] legs, CL.yaml daily_trades_per_contract)
  is UNSUPPORTED in every package. Correct counts: B 40 SUPPORTED /
  2 UNSUPPORTED (SI-H2, CL-H3); C 41 / 1 (CL-H3).
  MINOR-1 — floor policy is now explicit and dual-reported: LITERAL floors
  bind where the yaml states an explicit quantifier (SI-H2 >=10y -> 120m;
  NG-H1 >=5y -> 60m; NG-H4 >=3y -> 36m; 6E-H5 'M1 depth >=2019' -> 93m
  from 2019-01-01 to package end); vague text ('several years',
  'multi-year', '>=2y') binds at the 24m DAILY_BT admission bar. Headline
  = LITERAL policy (conservative-evidence law); the 24m-default policy is
  reported alongside (only A-v1 differs: 31 vs 30 SUPPORTED).
This rerun does NOT rewrite coverage_results.json (per-line values already
correct and audit-verified 41/41; only asserts the two totals patches).
"""
import datetime as dt
import glob
import json
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CTRL = HERE.parent
RESULTS = json.loads((HERE / "coverage_results.json").read_text())
GB = 1e9

ROOTS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]


def window_months(start: str, end: str) -> float:
    s = dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    return round((e - s).days / 30.4375, 2)


PKG_OHLCV_MONTHS = {}
for pkg, tag in (("A", "A2-O1M-"), ("A_variant_24m_floor", "A-O1M-"),
                 ("B", "B-O1M-")):
    d = {}
    for ln in RESULTS["packages"][pkg]["lines"]:
        if ln["schema"] == "ohlcv-1m" and ln["line_id"].startswith(tag):
            root = ln["line_id"][len(tag):]
            d[root] = window_months(ln["start"], ln["end"])
    PKG_OHLCV_MONTHS[pkg] = d
PKG_OHLCV_MONTHS["C"] = {r: window_months("2010-06-06", "2026-10-02")
                         for r in ROOTS}

PKG_HAS_BBO_NQ = {"A": None, "A_variant_24m_floor": None,
                  "B": ("2024-10-01", "2026-10-01"),
                  "C": ("2010-06-06", "2026-10-02")}
PKG_HAS_BBO_CL = {"A": None, "A_variant_24m_floor": None,
                  "B": "ROLLWINDOWS", "C": "ROLLWINDOWS"}

# Floor policies (months). Explicit UNAMBIGUOUS yaml quantifiers bind in
# BOTH policies (SI-H2 '>=10y', NG-H1 '>=5y'); the two policies differ only
# on the audit-flagged floors whose literal text exceeds the 24m bar:
# NG-H4 '>=3y' -> 36m and 6E-H5 'M1 depth >=2019' -> 93m (2019-01-01..
# 2026-10). LITERAL = those bind (HEADLINE, conservative-evidence law);
# DEFAULT24 = 24m DAILY_BT admission bar everywhere (comparison; equals the
# original pre-audit policy). Vague floor text ('several years',
# 'multi-year', '>=2y') binds at DEFAULT24 in both.
FLOOR_BASE = {  # explicit quantifiers, unambiguous, bind in both policies
    ("daily_trades_per_contract", "SI-H2"): 120,   # '>=10y two-leg daily'
    ("minute_trades_m1", "NG-H1"): 60,             # 'M1 >=5y'
}
FLOOR_LITERAL_EXTRA = {  # audit MINOR-1: literal text > 24m default
    ("daily_trades_per_contract", "NG-H4"): 36,    # '>=3y true volume'
    ("full_session_globex_intraday", "6E-H5"): 93, # 'M1 depth >=2019'
}
DEFAULT_FLOOR = {"daily_trades_per_contract": 24,
                 "minute_trades_m1": 24,
                 "full_session_globex_intraday": 24,
                 "synchronous_bbo": 24}

VENDOR_CLASSES = {"daily_trades_per_contract", "minute_trades_m1",
                  "full_session_globex_intraday", "synchronous_bbo"}

hyps = []
for f in sorted(glob.glob(str(CTRL / "configs" / "symbols" / "*.yaml"))):
    cfg = yaml.safe_load(Path(f).read_text())
    sym = cfg["symbol"]
    for h in cfg["hypotheses"]:
        needs = []
        for section in ("minimal_test", "scored_run"):
            for req in h.get(section, {}).get("requirements", []):
                if req.get("class") in VENDOR_CLASSES:
                    needs.append({"class": req["class"], "use": req.get("use"),
                                  "symbols": req.get("symbols", [sym])})
        needs = sorted({(n["class"], n["use"], tuple(n["symbols"]))
                        for n in needs})
        hyps.append({"id": h["id"], "symbol": sym, "rank": h.get("rank"),
                     "needs": [{"class": c, "use": u, "symbols": list(s)}
                               for c, u, s in needs]})


# ------------------------------------------------------- support verdicts ---

def requirement_supported(pkg, hyp_id, cls, symbols, policy):
    """MAJOR-1 fix: evaluate the floor on EVERY symbol of THIS requirement.
    A symbol outside the 10-root corpus is in NO package -> unsupported."""
    floor = DEFAULT_FLOOR[cls]
    if (cls, hyp_id) in FLOOR_BASE:
        floor = FLOOR_BASE[(cls, hyp_id)]
    if policy == "LITERAL" and (cls, hyp_id) in FLOOR_LITERAL_EXTRA:
        floor = FLOOR_LITERAL_EXTRA[(cls, hyp_id)]
    if cls == "synchronous_bbo":
        if "NQ" in symbols:
            w = PKG_HAS_BBO_NQ[pkg]
            return (w is not None,
                    "bbo-1m NQ continuous in package" if w else
                    "no bbo-1m line in package")
        if "CL" in symbols:
            w = PKG_HAS_BBO_CL[pkg]
            return (w is not None,
                    "CL bbo-1m roll-window lines in package" if w else
                    "no bbo-1m line in package")
        return False, "bbo not quoted for this symbol"
    fails = []
    for sym in symbols:
        if sym not in ROOTS:
            fails.append(f"{sym}: outside the 10-root corpus, in NO package")
            continue
        months = PKG_OHLCV_MONTHS[pkg].get(sym, 0)
        if months < floor:
            fails.append(f"{sym} ohlcv-1m {months}m < floor {floor}m")
    return (not fails, "; ".join(fails) if fails else
            f"all requirement symbols >= floor {floor}m")


def support_for_policy(policy):
    out = {}
    for pkg in ("A", "A_variant_24m_floor", "B", "C"):
        rows = {}
        for h in hyps:
            if not h["needs"]:
                rows[h["id"]] = {
                    "verdict": "NOT_VENDOR_GATED",
                    "reason": "no vendor data class in requirements"}
                continue
            fails = []
            for n in h["needs"]:
                ok, reason = requirement_supported(
                    pkg, h["id"], n["class"], n["symbols"], policy)
                if not ok:
                    fails.append(f"{n['class']}[{','.join(n['symbols'])}]: "
                                 f"{reason}")
            rows[h["id"]] = (
                {"verdict": "SUPPORTED",
                 "reason": "all vendor floors met"}
                if not fails else
                {"verdict": "UNSUPPORTED", "reason": "; ".join(fails)})
        out[pkg] = rows
    return out


support_literal = support_for_policy("LITERAL")
support_default24 = support_for_policy("DEFAULT24")

counts_literal = {pkg: dict(Counter(r["verdict"] for r in rows.values()))
                  for pkg, rows in support_literal.items()}
counts_default24 = {pkg: dict(Counter(r["verdict"] for r in rows.values()))
                    for pkg, rows in support_default24.items()}

# ------------------------------------------------------------ disk gate ----
snap = RESULTS["disk_snapshot"]["statvfs"]
avail_gb = snap["available_bytes"] / GB
usable_gb = avail_gb * 0.80
disk = {"available_gb_decimal": round(avail_gb, 2),
        "available_gib": snap["available_gib"],
        "usable_gb_decimal_at_20pct_reserve": round(usable_gb, 2),
        "assumptions": {
            "raw_on_disk_vs_billable": "ASSUMED 0.4-0.6 x billable (zstd; "
                "vendor claims compression without publishing ratios; "
                "manifest's assumption, measure at pilot)",
            "parquet_vs_billable": "ASSUMED 0.5-1.0 x billable",
            "scratch_peak_vs_raw": "ASSUMED <= 1.0 x raw-compressed "
                "(transient during transform)",
            "peak_concurrent": "raw_compressed + parquet + scratch",
            "reserve_interpretation": "20% of CURRENTLY-AVAILABLE space "
                "reserved (0.8 x available); volume already 89% full, so a "
                "'20% of volume' reading would permit nothing"},
        "packages": {}}


def disk_verdict(billable_gb):
    raw_lo, raw_hi = 0.4 * billable_gb, 0.6 * billable_gb
    pq_lo, pq_hi = 0.5 * billable_gb, 1.0 * billable_gb
    peak_lo = raw_lo + pq_lo + raw_lo
    peak_hi = raw_hi + pq_hi + raw_hi
    if peak_hi <= usable_gb:
        verdict = "FITS"
    elif peak_lo <= usable_gb:
        verdict = ("CONDITIONAL_FITS (only at favorable compression; no "
                   "headroom for over-run)")
    else:
        verdict = "DOES_NOT_FIT"
    return {"billable_gb": round(billable_gb, 2),
            "raw_on_disk_gb_assumed": [round(raw_lo, 2), round(raw_hi, 2)],
            "parquet_gb_assumed": [round(pq_lo, 2), round(pq_hi, 2)],
            "peak_usage_gb_assumed": [round(peak_lo, 2), round(peak_hi, 2)],
            "verdict": verdict}


disk["packages"]["PILOT (already queued, NQ/CL)"] = disk_verdict(2.1999)
for pkg, label in (("A", "pkgA (v2, ~$100 scenario)"),
                   ("A_variant_24m_floor", "pkgA-v1 variant (24m floor 8/10)"),
                   ("B", "pkgB (~$600 scenario)"),
                   ("C", "pkgC (longest feasible)")):
    disk["packages"][label] = disk_verdict(
        RESULTS["packages"][pkg]["totals"]["billable_gb_decimal"])

# Assert the already-applied totals patches are present (this rerun does not
# rewrite coverage_results.json; per-line values audit-verified 41/41).
tb = RESULTS["packages"]["B"]["totals"]
assert tb.get("lines_derived", 0) == 1 and tb.get("lines_failed") == 0 and \
    "totals_note" in tb, "expected pkgB totals patches missing"
assert "ohlcv1m_per_root_counts" in RESULTS["packages"]["C"], \
    "expected pkgC per-root counts patch missing"

summary = {
    "schema": "futures_behavior_10syms_acq_analysis@2",
    "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "post_audit_revision": {
        "source": "audit/acq_skeptic/ACQ_SKEPTIC_AUDIT.md (2026-10-02)",
        "major_1": "depth floors evaluated per REQUIREMENT symbols; "
                   "out-of-corpus legs (CL-H3 [RB,HO]) UNSUPPORTED everywhere",
        "minor_1": "floor policy dual-reported: LITERAL (headline; explicit "
                   "yaml quantifiers bind) vs DEFAULT24 (24m bar everywhere); "
                   "only A-v1 differs (30 vs 31 SUPPORTED)",
        "minor_2": "CL roll-window count = 96 (12/yr x 8y) everywhere incl. "
                   "the $1.25 DERIVED line",
        "minor_3": "coverage claims restated at band precision "
                   "(first-hit band 2010-06-06..2010-12-06)"},
    "floor_policy": {
        "headline": "LITERAL",
        "explicit_quantifiers_binding_in_both_policies_months": {
            f"{c}/{h}": m for (c, h), m in sorted(FLOOR_BASE.items())},
        "literal_only_overrides_months": {
            f"{c}/{h}": m for (c, h), m in sorted(FLOOR_LITERAL_EXTRA.items())},
        "default_floor_months": DEFAULT_FLOOR,
        "vague_text_rule": "'several years'/'multi-year'/'>=2y' bind at the "
                           "24m DAILY_BT admission bar (disclosed policy "
                           "choice, not a yaml literal)"},
    "hypothesis_support": support_literal,
    "hypothesis_support_counts": counts_literal,
    "hypothesis_support_counts_under_24m_default": counts_default24,
    "hypothesis_support_under_24m_default": support_default24,
    "disk_gate": disk,
    "pkg_ohlcv_months": PKG_OHLCV_MONTHS,
}
(HERE / "analysis_summary.json").write_text(json.dumps(summary, indent=1))

print("LITERAL policy counts (headline):", json.dumps(counts_literal))
print("DEFAULT24 policy counts (comparison):",
      json.dumps(counts_default24))
for pkg in ("B", "C"):
    unsup = [k for k, v in support_literal[pkg].items()
             if v["verdict"] == "UNSUPPORTED"]
    print(f"{pkg} UNSUPPORTED:", unsup)
print("A-v1 UNSUPPORTED (literal):",
      sorted(k for k, v in support_literal["A_variant_24m_floor"].items()
             if v["verdict"] == "UNSUPPORTED"))
print("disk verdicts:",
      {k: v["verdict"] for k, v in disk["packages"].items()})
print("wrote analysis_summary.json")
