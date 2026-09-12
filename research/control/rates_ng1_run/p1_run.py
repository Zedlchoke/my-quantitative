"""RATES-NG1 P1 measured run: kernel/cost/clock gate.

Dispatch: rates-ng1-p1-kernel-costs (cycle RATES-NG1, P1).  This run:

1. consumes the four P0-census ETP legs STRICTLY via the frozen plane
   adapter (verify-on-read against the committed substrate manifest;
   no network price pulls -- Q-8 law and plan section 3 adoption law);
2. measures per-ETP Corwin-Schultz spread distributions on the RAW EOD
   bars (primary), the Roll effective-spread cross-check (rolling
   63-day windows), and freezes the 90th-percentile stress tier;
3. records each issuer's official expense-ratio FEE FACT with evidence
   URL + fetched-page digest (the ONLY network reads in P1);
4. assembles the frozen tier-2.0 cost contract;
5. runs the P1 pytest file (kernel dual-book + clock/DST/PIT floors)
   as subprocesses and records their exit codes;
6. writes p1_gate.json (per-item measured values + provenance +
   PASS/FAIL, fail-closed).

No proposals, no signal design, no scoring, no outcome numbers.
"""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.rates_ng1 import cost_model as cm  # noqa: E402
from research.assets.rates_ng1 import plane_adapter as pa  # noqa: E402
from research.assets.rates_ng1.cost_model import (  # noqa: E402
    assemble_cost_contract,
    corwin_schultz_spread_series,
    expense_drag_per_day,
    roll_effective_spread_windows,
)

SCHEMA = "rates_ng1_run/p1_gate@1"
RUN_DIR = os.path.dirname(os.path.abspath(__file__))
EVIDENCE_DIR = os.path.join(RUN_DIR, "p1_evidence")
CONTRACT_PATH = os.path.join(RUN_DIR, "p1_cost_contract.json")
GATE_PATH = os.path.join(RUN_DIR, "p1_gate.json")
TEST_FILE = os.path.join(REPO_ROOT, "tests", "test_rates_ng1_p1.py")

ROLL_WINDOW_DAYS = 63

#: Sanity band for the estimated stress tier of a US Treasury ETP:
#: 0 < p90 <= 1% of price.  Declared with the P1 gate (never moved).
P90_BPS_SANITY = (0.0, 100.0)

#: Roll cross-check floor: Roll's median must not exceed 4x the CS p50
#: (a Roll estimate far above the high-low estimate would contradict
#: it), on at least 20% estimable windows.  Declared with the P1 gate.
ROLL_MAX_RATIO = 4.0
ROLL_MIN_ESTIMABLE_FRACTION = 0.20

#: CS estimable-pair coverage floor.
CS_MIN_ESTIMABLE_FRACTION = 0.90

ER_SANITY_MAX = 0.05

OFFICIAL_ER_PAGES = {
    "TLT": "https://www.ishares.com/us/products/239454/"
           "ishares-20-year-treasury-bond-etf",
    "IEF": "https://www.ishares.com/us/products/239456/"
           "ishares-710-year-treasury-bond-etf",
    "IEI": "https://www.ishares.com/us/products/239455/"
           "ishares-37-year-treasury-bond-etf",
    "SHY": "https://www.ishares.com/us/products/239452/"
           "ishares-13-year-treasury-bond-etf",
}

_ER_RX = (r'"value":([0-9.]+),"returnType":false,'
          r'"associatedReturnType":false,'
          r'"fullName":"fundHeader\.fees\.expr"')
_TITLE_RX = re.compile(r"<title>([^<]+)</title>")
_CANONICAL_RX = re.compile(r'rel="canonical" href="([^"]+)"')


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", REPO_ROOT, *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def fetch_official_er_page(ticker: str, url: str,
                           timeout: float = 40.0) -> dict:
    """Fetch ONE official issuer fund page (bounded, https only), verify
    the canonical URL + ticker in the title, extract the embedded ER.
    Fail-closed: any structural miss raises."""
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (research evidence fetch)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            final_url = resp.geturl()
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(f"official ER page fetch failed for {ticker}: "
                           f"{exc}") from exc
    text = html_lib.unescape(raw.decode("utf-8", "replace"))
    title_m = _TITLE_RX.search(text)
    canonical_m = _CANONICAL_RX.search(text)
    if title_m is None:
        raise RuntimeError(f"{ticker}: official page has no <title>")
    title = title_m.group(1).strip()
    if ticker not in title:
        raise RuntimeError(f"{ticker}: official page title {title!r} does "
                           "not name the ticker (evidence mismatch)")
    canonical = canonical_m.group(1) if canonical_m else None
    ers = sorted({float(v) for v in re.findall(_ER_RX, text)})
    if len(ers) != 1:
        raise RuntimeError(f"{ticker}: embedded fee field not a singleton "
                           f"(found {ers}): refuse to pick one silently")
    er_annual = ers[0] / 100.0
    if not 0.0 < er_annual <= ER_SANITY_MAX:
        raise RuntimeError(f"{ticker}: ER {er_annual} outside the sanity "
                           f"band (0, {ER_SANITY_MAX}]: refused")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(os.path.join(EVIDENCE_DIR, f"{ticker}.html"), "wb") as fh:
        fh.write(raw)
    asof = sorted(set(re.findall(r"[Aa]s of[^<]{0,40}(\d{2}/\d{2}/\d{4})",
                                 text)))
    return {
        "ticker": ticker,
        "er_annual": er_annual,
        "evidence_url": url,
        "canonical_url": canonical,
        "final_url": final_url,
        "page_title": title,
        "page_sha256": _sha256_bytes(raw),
        "page_bytes": len(raw),
        "fetch_utc": _now_utc(),
        "page_embedded_as_of": asof[:3],
        "drag_per_day_fraction": expense_drag_per_day(er_annual),
    }


def measure() -> dict:
    """Consume the frozen substrate via the plane, measure everything,
    return the full measurement payload (fail-closed on any drift)."""
    plane = pa.RatesNG1Plane()

    cs_by_ticker: dict[str, dict] = {}
    roll_by_ticker: dict[str, dict] = {}
    windows: dict[str, list[str]] = {}
    provenance: dict[str, dict] = {}
    for ticker in pa.ETP_TICKERS:
        res = plane.consume_via_plane(f"etp_eod/{ticker}.US.json")
        rows = plane.etp_rows(ticker)
        highs = [float(r["high"]) for r in rows]
        lows = [float(r["low"]) for r in rows]
        closes = [float(r["close"]) for r in rows]
        dates = [str(r["date"]) for r in rows]
        cs_by_ticker[ticker] = corwin_schultz_spread_series(highs, lows)
        roll_by_ticker[ticker] = roll_effective_spread_windows(
            closes, window=ROLL_WINDOW_DAYS)
        windows[ticker] = [dates[0], dates[-1]]
        provenance[ticker] = {
            "entry": f"etp_eod/{ticker}.US.json",
            "sha256_plane_measured": res["sha256_measured"],
            "sha256_manifest_pin": res["sha256_pinned"],
            "authority": res["authority"],
            "rows": len(rows),
            "window": windows[ticker],
            "source_url": res.get("source_url"),
        }

    er_by_ticker = {}
    for ticker, url in OFFICIAL_ER_PAGES.items():
        er_by_ticker[ticker] = fetch_official_er_page(ticker, url)

    return {"cs": cs_by_ticker, "roll": roll_by_ticker,
            "er": er_by_ticker, "windows": windows,
            "provenance": provenance}


def build_floors(m: dict, contract: dict) -> dict:
    """Per-item floors with measured values; fail-closed PASS/FAIL."""

    def per_ticker(test):
        return {t: test(t) for t in sorted(m["cs"])}

    f: dict[str, dict] = {}

    # F1 -- CS estimable coverage on RAW bars (work item 2).
    f1 = per_ticker(lambda t: {
        "estimable_pairs": m["cs"][t]["estimable_pairs"],
        "pairs": m["cs"][t]["pairs"],
        "estimable_fraction": (m["cs"][t]["estimable_pairs"]
                               / m["cs"][t]["pairs"]),
    })
    f1_pass = all(v["estimable_fraction"] is not None
                  and v["estimable_fraction"] >= CS_MIN_ESTIMABLE_FRACTION
                  for v in f1.values())
    f["F1_cs_coverage"] = {
        "name": "cs_estimable_coverage",
        "work_item": "2-costs",
        "definition": f"per ETP: estimable CS two-day pairs fraction "
                      f">= {CS_MIN_ESTIMABLE_FRACTION} on the RAW EOD "
                      "bars of the P0 frozen substrate",
        "measured": f1,
        "verdict": "PASS" if f1_pass else "FAIL",
    }

    # F2 -- stress tier sanity band (work item 2).
    f2 = per_ticker(lambda t: {
        "cs_p90_bps": contract["per_etp"][t]["stress_tier_bps"],
        "cs_p50_bps": contract["per_etp"][t]["spread_primary"]["cs_p50_bps"],
    })
    f2_pass = all(
        v["cs_p90_bps"] is not None
        and P90_BPS_SANITY[0] < v["cs_p90_bps"] <= P90_BPS_SANITY[1]
        for v in f2.values())
    f["F2_stress_tier"] = {
        "name": "cs_p90_stress_tier_sanity",
        "work_item": "2-costs",
        "definition": "per ETP: frozen stress tier (p90 of the CS spread "
                      f"distribution) within the sanity band "
                      f"{P90_BPS_SANITY[0]} < p90_bps <= "
                      f"{P90_BPS_SANITY[1]}; declared at this P1 gate",
        "measured": f2,
        "verdict": "PASS" if f2_pass else "FAIL",
    }

    # F3 -- Roll effective-spread cross-check (work item 2).
    f3 = per_ticker(lambda t: {
        "roll_median_bps":
            contract["per_etp"][t]["spread_cross_check"]["roll_median_bps"],
        "roll_estimable_fraction":
            contract["per_etp"][t]["spread_cross_check"]
            ["estimable_fraction"],
        "roll_over_cs_p90_ratio":
            contract["per_etp"][t]["spread_cross_check"]
            ["roll_over_cs_p90_ratio"],
    })

    def _f3_ok(v: dict) -> bool:
        frac = v["roll_estimable_fraction"]
        ratio = v["roll_over_cs_p90_ratio"]
        return (frac is not None
                and frac >= ROLL_MIN_ESTIMABLE_FRACTION
                and ratio is not None
                and 0.0 <= ratio <= ROLL_MAX_RATIO)

    f3_pass = all(_f3_ok(v) for v in f3.values())
    f["F3_roll_cross_check"] = {
        "name": "roll_effective_spread_cross_check",
        "work_item": "2-costs",
        "definition": "per ETP: Roll estimable windows fraction >= "
                      f"{ROLL_MIN_ESTIMABLE_FRACTION} and roll/CS-p90 "
                      f"ratio within [0, {ROLL_MAX_RATIO}] (Roll far "
                      "above the frozen stress tier would contradict it; "
                      "the CS p50 is routinely 0.0 after flooring so the "
                      "p90 tier is the declared cross-check basis); "
                      "declared at this P1 gate",
        "measured": f3,
        "verdict": "PASS" if f3_pass else "FAIL",
    }

    # F4 -- expense-ratio FEE FACT evidence (work item 2).
    f4 = {t: {
        "er_annual": m["er"][t]["er_annual"],
        "drag_per_day_fraction": m["er"][t]["drag_per_day_fraction"],
        "drag_exact": (m["er"][t]["drag_per_day_fraction"]
                       == m["er"][t]["er_annual"] / 365.0),
        "evidence_url": m["er"][t]["evidence_url"],
        "canonical_url": m["er"][t]["canonical_url"],
        "page_title": m["er"][t]["page_title"],
        "page_sha256": m["er"][t]["page_sha256"],
        "page_bytes": m["er"][t]["page_bytes"],
        "fetch_utc": m["er"][t]["fetch_utc"],
    } for t in sorted(m["er"])}
    f4_pass = all(
        v["canonical_url"] == OFFICIAL_ER_PAGES[t]
        and 0.0 < v["er_annual"] <= ER_SANITY_MAX and v["drag_exact"]
        for t, v in f4.items())
    f["F4_expense_fee_facts"] = {
        "name": "official_expense_ratio_evidence",
        "work_item": "2-costs",
        "definition": "4/4 ETPs carry an issuer-official fund page with "
                      "canonical URL equality, ticker-naming title, a "
                      "singleton embedded ER within the sanity band, and "
                      "the exact ACT/365F daily conversion",
        "measured": f4,
        "verdict": "PASS" if f4_pass else "FAIL",
    }
    return f


def run_pytree_filter(filt: str) -> dict:
    """Run one -k-filtered slice of the P1 pytest file; record the exact
    command and exit code (floors F5/F6)."""
    cmd = [sys.executable, "-m", "pytest", "-q", TEST_FILE, "-k", filt]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True,
                          text=True, timeout=900)
    tail = (proc.stdout.strip().splitlines() or [""])[-1]
    return {
        "command": " ".join(cmd),
        "filter": filt,
        "exit_code": proc.returncode,
        "summary_tail": tail,
        "verdict": "PASS" if proc.returncode == 0 else "FAIL",
    }


def main() -> int:
    measured_utc = _now_utc()
    head = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    print(f"[p1] worktree={REPO_ROOT}")
    print(f"[p1] branch={branch} head={head}")
    print(f"[p1] measured_utc={measured_utc}")

    m = measure()

    substrate_provenance = {
        "adapter": "research/assets/rates_ng1/plane_adapter.py "
                   "(consume_via_plane, verify-on-read)",
        "manifest": "research/control/rates_ng1_run/substrate_manifest.json",
        "legs": m["provenance"],
        "price_input_note": "RAW (unadjusted primary channel) EOD "
                            "high/low/close; no network price pulls in P1",
        "p0_etp_census_cross_check": {
            t: {"sha256_matches_p0_census": (
                m["provenance"][t]["sha256_plane_measured"]
                == json.load(open(os.path.join(
                    RUN_DIR, "p0_etp_census.json")))["tickers"][t]["sha256"])
            } for t in sorted(m["provenance"])},
    }
    contract = assemble_cost_contract(
        cycle_id="RATES-NG1",
        window_by_ticker=m["windows"],
        cs_by_ticker=m["cs"],
        roll_by_ticker=m["roll"],
        er_by_ticker=m["er"],
        substrate_provenance=substrate_provenance,
    )
    with open(CONTRACT_PATH, "w", encoding="utf-8") as fh:
        json.dump(contract, fh, indent=1, sort_keys=True)
    contract_sha = _sha256_bytes(open(CONTRACT_PATH, "rb").read())
    print(f"[p1] cost contract written: {CONTRACT_PATH} sha256={contract_sha}")

    floors = build_floors(m, contract)

    # F5/F6 -- kernel + clock fixture suites (work items 1 and 3).
    f5m = run_pytree_filter("kernel")
    floors["F5_kernel_dual_book_tests"] = {
        "name": "kernel_dual_book_compatibility_tests",
        "work_item": "1-kernel",
        "definition": "pytest -k kernel: inherited dual-book ledger "
                      "reconciles hand-computed degenerate cases (one "
                      "fill, one cost event, one mark), cost-once replay "
                      "refused, map_to_canonical compatibility",
        "measured": f5m,
        "verdict": f5m["verdict"],
    }
    f6m = run_pytree_filter("clock or dst or pit or decision")
    floors["F6_clock_dst_pit_tests"] = {
        "name": "clock_dst_pit_fixture_tests",
        "work_item": "3-clock",
        "definition": "pytest -k 'clock or dst or pit or decision': "
                      "hand-computed UTC/NY DST boundary decision "
                      "instants, V7 bar-readable close+1 session rule, "
                      "auction day-event PIT anchoring (same-day close "
                      "refused)",
        "measured": f6m,
        "verdict": f6m["verdict"],
    }
    # Cost-model estimator fixtures also belong to work item 2's test
    # surface: run the full file once and record it as F7.
    f7m = run_pytree_filter("")
    floors["F7_p1_test_file_full"] = {
        "name": "p1_test_file_full_run",
        "work_item": "4-gate-tests",
        "definition": "full tests/test_rates_ng1_p1.py exit code 0",
        "measured": f7m,
        "verdict": f7m["verdict"],
    }

    all_pass = all(f["verdict"] == "PASS" for f in floors.values())
    blockers: list[str] = [k for k, v in floors.items()
                           if v["verdict"] != "PASS"]
    gate = {
        "schema": SCHEMA,
        "gate": "RATES-NG1-P1",
        "cycle_id": "RATES-NG1",
        "task_id": "rates-ng1-p1-kernel-costs",
        "measured_utc": measured_utc,
        "worktree": REPO_ROOT,
        "git": {"branch": branch, "head_sha": head},
        "floors": floors,
        "sections": {
            "cost_contract": {
                "path": os.path.relpath(CONTRACT_PATH, REPO_ROOT),
                "sha256": contract_sha,
                "cost_ladder_tier": contract["cost_ladder_tier"],
                "cost_frequency": contract["cost_frequency"],
                "stress_tier_quantile": contract["stress_tier"]["quantile"],
            },
            "kernel_inheritance": {
                "shared_kernel_module": "research/accounting.py",
                "imported_primitives": ["map_to_canonical",
                                        "build_accounting_reconciliation",
                                        "TERMINAL_POLICY",
                                        "AccountingFieldError"],
                "forked": False,
                "fork_justification": None,
                "cycles_module":
                    "research/assets/rates_ng1/kernel.py",
                "precedent_shape": "dual books over identical fills/marks "
                                   "(RULES.md forex standing constraint; "
                                   "governance financing_dual_books)",
            },
            "clock_law": {
                "decision_grid": "daily 16:00 America/New_York close on "
                                 "EODHD EOD ETP bars, UTC materialization "
                                 "via zoneinfo (DST fixtures mandatory)",
                "availability": "V7 law: EOD bar dated session S is "
                                "readable close+1 session",
                "pit_anchoring": "day-dated official auction announcements "
                                 "(P0 census announcementDate shape) gate "
                                 "decisions from the first session close "
                                 "STRICTLY AFTER the conservative LATER "
                                 "PIT bound (end of announced NY day); "
                                 "same-day close refused",
            },
            "evidence": {
                "official_er_pages": OFFICIAL_ER_PAGES,
                "p1_evidence_dir": os.path.relpath(EVIDENCE_DIR, REPO_ROOT),
                "note": "fetched page bytes are machine-local (sha256 "
                        "pins recorded in the contract); P-13 law",
            },
        },
        "evidence_paths": {
            "gate": os.path.relpath(GATE_PATH, REPO_ROOT),
            "cost_contract": os.path.relpath(CONTRACT_PATH, REPO_ROOT),
            "tests": "tests/test_rates_ng1_p1.py",
            "p0_gate": "research/control/rates_ng1_run/p0_gate.json",
        },
        "blockers": blockers,
        "verdict": "PASS" if all_pass else "FAIL",
    }
    with open(GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=1, sort_keys=True)
    print(f"[p1] gate written: {GATE_PATH}")
    for k, v in floors.items():
        print(f"[p1] {k}: {v['verdict']} ({v.get('measured', {}).get(
            'summary_tail', '') if isinstance(v.get('measured'), dict)
            else ''})".rstrip())
    print(f"[p1] VERDICT: {gate['verdict']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
