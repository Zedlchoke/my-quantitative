#!/usr/bin/env python
"""FOREX-NG4 D2 measurement runner (novelty / feasibility /
identifiability).  NO expectancy, PnL or profit factor is computed
anywhere in this runner; the only cross-book quantities are Spearman
rho between signed exposure schedules, event/decision counts, and cost
ceilings under the REFERENCED proxy ladder (1.5 bps/side, tier 2.0 --
EURUSD Q-8 constants NOT_YET_MEASURED by this cycle's P1 kernel lane,
so the proposal-law cost verdict stays NOT_RUN fail-closed).

Measured (P-12: code AND representation commit together, before any
number is cited):

1. NOVELTY -- pooled max |rho| of each ng4 proposal's anchor schedule
   on its CORRECT representation (EURUSD 5-pair extended grid; the EZ
   restricted stream with the v2-day PIT clock for A4; the EZ-US
   restricted differential months with the max-v2 clock for A5) vs the
   veto panel: the ng1 25-shape panel rebuilt on the 5-pair plane (8
   committed FXFV8 shapes + V4 commodity bloc + 2 committed FXFV7
   books + spillover/lead-lag rebuilds with EURUSD restored per the
   true V7 plane + generics incl. EURUSD) PLUS the declared
   kill-candidate shadows rebuilt from the committed ng1/ng3 D1
   proposal identities (ng1 A4 print-deviation + acceleration with the
   US-event leg extended to EURUSD; ng1 A5-P1 release-order, ng3 A5-P1
   differential, ng3 A5-P2 transfer rebuilt verbatim on their own
   funded pairs -- no EURUSD leg exists in those identities, recorded
   honestly as NO_SHARED_PAIRS rows) and the V9 PPP-deviation form
   rebuilt on EURUSD from the FAMILY_FAILURES row spec.  Bar 0.20,
   margins recorded (P-2).  A veto shape that cannot be BUILT fails
   closed; a shape that shares no pair with the EURUSD anchor is an
   honest unmeasurable row, never a silent drop.
2. FEASIBILITY -- Q-6 recent window (last 24 calendar months of S0):
   MEASURED with NO floor frozen (plans/PLAN_forex_ng4.md sec 3
   freezes floors only on the A4 total 30 and A5 join total 12; the
   ng3 >= 15 recent floor was CA-specific and is never inferred onto
   EZ -- the thin structure is disclosed for the S rubric).  Totals
   re-measured against the D1 declarations (37 EZ restricted events /
   16 differential months) incl. cohort structure, fired counts vs the
   D1 BLIND priors and the vacuous-book law.
3. IDENTIFIABILITY -- CTL-PPPANCESTRY vs the A5 anchors (>= 0.98 kills
   pre-score; Q-11 null validity recorded), CTL-V7NODIFF disclosure
   (the ng3-A5-P1 death mode), CTL-V7RECAP vs the A4 anchors, and A4
   nominal separability vs the committed FXFV8 DGS10-level shapes PLUS
   the exact-spec CTL-DGS10LEVEL z252 shape built from the pinned DGS10
   vintaged bytes (P-13 chain verified at P0) under the ng4 EURUSD
   sign law.

Outputs (committed with the code):
- research/control/forex_ng4_run/d2/d2_novelty_panel_ng4.json
- research/control/forex_ng4_run/d2/d2_feasibility_ng4.json
- research/control/forex_ng4_run/d1/feasibility/feasibility_summary.json

Usage:
    .venv/bin/python research/control/forex_ng4_run/d2/d2_run.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from datetime import date, datetime, timezone

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng4/d2"
if WORKTREE not in sys.path:
    sys.path.insert(0, WORKTREE)

from research.assets.forex_ng1 import plane_adapter as pa   # noqa: E402
from research.assets.forex_ng1 import spot_series as ss     # noqa: E402
from research.assets.forex_ng1.d2 import books as B         # noqa: E402
from research.assets.forex_ng1.d2 import events as E        # noqa: E402
from research.assets.forex_ng1.d2 import rho as R           # noqa: E402
from research.assets.forex_ng1.d2.series import (           # noqa: E402
    ECONOMY_SERIES, VintagedSeries, parse_realtime_observations,
)
from research.assets.forex_ng3 import revision_series as rs  # noqa: E402
from research.assets.forex_ng3.d2 import books as N3        # noqa: E402
from research.assets.forex_ng4 import ez_vintaged as ezv    # noqa: E402
from research.assets.forex_ng4 import wide_pull as wp       # noqa: E402
from research.assets.forex_ng4.d2 import books as N4        # noqa: E402

# --------------------------------------------------------------------------- #
# pinned inputs (READ-ONLY; every digest recorded in the outputs)
# --------------------------------------------------------------------------- #

CADS_ROOT = pa.DEFAULT_CADS_STORE_ROOT
US_RT_CADS_ADDRESS = (
    "7f18ec982374ce4dfb235f53f001327793df8e1c0077d31206de25aa3455ac94")
V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
           "forex-free-v9/integration")            # READ-ONLY inheritance
VINTAGED_DIR = os.path.join(V9_ROOT, "data_raw/forex_free_v9_cpi")
V8_EVIDENCE_PATH = os.path.join(
    V9_ROOT, "research/control/forex_free_v8_run/d2/evidence/"
             "schedule_cells_proposals_v8.json")
V7_ANCESTORS_PATH = os.path.join(
    V9_ROOT, "research/control/forex_free_v7_run/d2/a7_novelty/"
             "evidence/schedule_cells_ancestors.json")
V7_PROPOSALS_PATH = os.path.join(
    V9_ROOT, "research/control/forex_free_v7_run/"
             "a7_prelaunch_evidence_r2/novelty_rerun_evidence/"
             "schedule_cells_proposals_v7.json")

#: the ng4 pinned EZ wide-window bytes live UNTRACKED in the cycle's
#: integration worktree (the p0c lane's pin dir); read-only inheritance
NG4_INTEGRATION_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
                        "forex-ng4/integration")
EZ_WIDE_PIN_DIR = os.path.join(NG4_INTEGRATION_ROOT,
                               "data_raw/forex_ng4_ez")
EZ_WIDE_MANIFEST_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng4_run/p0c_wide_window_manifest.json")
EZ_WIDE_MANIFEST_SHA_PIN = (
    "47e4d642f0568f9b4cd774508700862d08e40a8109b81a65f1262fb15f4d39f8")

NG4_CENSUS_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng4_run/p0c_wide_window_census.json")
NG4_CENSUS_SHA_PIN = ("6471b8bed8ccf04c9163318fd27b8c4bc407d57d6d3fd6cdc"
                      "10acd768250cdeb")
NG1_CENSUS_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/p0_announcement_census.json")
NG3_CENSUS_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng3_run/p0_revision_census.json")
NG3_CENSUS_SHA_PIN = ("0fc108631e6b4bb2111c3528b873e68505ab2b46247d5e39cb"
                      "a24a12ff35017f")
NG1_SPOT_MANIFEST_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng1_run/p1_spot/"
              "spot_pin_manifest.json")
NG4_SPOT_MANIFEST_PATH = os.path.join(
    WORKTREE, "research/control/forex_ng4_run/p0_spot_pin_manifest.json")
NG4_SPOT_MANIFEST_SHA_PIN = (
    "3949445abf5ec882884715aeccce459ee26987a60227331dea85482e2e92918d")

DGS10_SOURCE_PATH = (
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v8/"
    "integration/research/control/forex_free_v8_run/staged_vintaged/"
    "DGS10.json")
DGS10_SHA_PIN = ("03dde429ba022e6d011ae3a61323124e38c5a3fac888b492823406a"
                 "51c4c4aa0")

GRID_LAW_DAYS = 1842
S0_WINDOW = (date(2018, 4, 4), date(2025, 4, 30))
SHARED_PAIRS = list(N4.PLANE_PAIRS)

#: The D1 proposals are the frozen P-12 measurement contracts; the ng1
#: and ng3 D1 proposals are the frozen identity authority for the
#: kill-candidate shadows (sha256-pinned, fail-closed on drift).
PROPOSAL_SPECS = {
    "FXNG4-A4-P1": {
        "path": "research/control/forex_ng4_run/d1/proposals/"
                "proposal_A4_P1.json",
        "sha256": ("644d1710a368ec32d9d77bb03a26b4957e77ab580b2cf45452ae"
                   "af38e5dd306e"),
    },
    "FXNG4-A4-P2": {
        "path": "research/control/forex_ng4_run/d1/proposals/"
                "proposal_A4_P2.json",
        "sha256": ("150a0bfca0df04ee52e8120f9ce42149cd51ea486b4050df658c"
                   "357b7d0cea06"),
    },
    "FXNG4-A5-P1": {
        "path": "research/control/forex_ng4_run/d1/proposals/"
                "proposal_A5_P1.json",
        "sha256": ("e2b1f47102700ac4ff32bf5de98ffcd7a8c93b9df4d5bdf4031b"
                   "1260634a342e"),
    },
    "FXNG4-A5-P2": {
        "path": "research/control/forex_ng4_run/d1/proposals/"
                "proposal_A5_P2.json",
        "sha256": ("72c95075d8698b672a2f016b42da0257d05ed17b8469743f55d5"
                   "1cab518a1d45"),
    },
    "FXNG1-A4-P1": {
        "path": "research/control/forex_ng1_run/d1/proposals/"
                "proposal_A4_P1.json",
        "sha256": ("240af78dfbf2c1c92ad9122e5317a4d33e31a8e8f99ed84d8983"
                   "15159f7d8234"),
    },
    "FXNG1-A4-P2": {
        "path": "research/control/forex_ng1_run/d1/proposals/"
                "proposal_A4_P2.json",
        "sha256": ("b1208b83879c46d51a1394c92c23850379ca31116a69b371d7a6"
                   "711d7747f63f"),
    },
    "FXNG1-A5-P1": {
        "path": "research/control/forex_ng1_run/d1/proposals/"
                "proposal_A5_P1.json",
        "sha256": ("33c0ad74e618df944f6d54422d6651be912f7cfdda443b38df7d"
                   "b48b5ff65020"),
    },
    "FXNG3-A5-P1": {
        "path": "research/control/forex_ng3_run/d1/proposals/"
                "proposal_A5_P1.json",
        "sha256": ("e062840b1f0e165033e1f95a999608e432f66291e648b23936b7"
                   "da39189679c2"),
    },
    "FXNG3-A5-P2": {
        "path": "research/control/forex_ng3_run/d1/proposals/"
                "proposal_A5_P2.json",
        "sha256": ("8f458b91b8b767c2ba091c721e0ed4d0d16fd11e75bffccda4b3"
                   "b5fc13bef447"),
    },
}

OUT_NOVELTY = os.path.join(
    WORKTREE, "research/control/forex_ng4_run/d2/d2_novelty_panel_ng4.json")
OUT_FEAS = os.path.join(
    WORKTREE, "research/control/forex_ng4_run/d2/d2_feasibility_ng4.json")
OUT_FEAS_SUMMARY = os.path.join(
    WORKTREE, "research/control/forex_ng4_run/d1/feasibility/"
              "feasibility_summary.json")

CODE_FILES = [
    "research/assets/forex_ng4/d2/__init__.py",
    "research/assets/forex_ng4/d2/books.py",
    "research/control/forex_ng4_run/d2/d2_run.py",
    "tests/test_forex_ng4_d2.py",
]

#: D1-declared counts (re-measured and compared; the fired-count priors
#: were declared BLIND at D1 and are measured here, never pre-judged).
DECLARED = {
    "FXNG4-A4-P1": {
        "restricted_events": 37,
        "cohort_2015_03_2017_11": 20, "obs_2018_02_2018_12": 11,
        "obs_2017_12": 1,
        "later_months": ["2020-09", "2020-10", "2023-01", "2023-04",
                         "2024-02"],
        "q6_recent_v2_basis": 2,
        "fired_prior": "BLIND 19-30 of 37 at 50-80% pass",
    },
    "FXNG4-A4-P2": {
        "restricted_events": 37,
        "q6_recent_v2_basis": 2,
        "fired_prior": "BLIND 19-30 of 37 at 50-80% pass",
    },
    "FXNG4-A5-P1": {
        "differential_months": 16,
        "by_year": {"2018": 11, "2020": 2, "2023": 2, "2024": 1},
        "ez_only_months": 21, "us_restricted_events": 84,
        "q6_ez_stream_v2_basis": 2,
        "fired_prior": "BLIND 2-10 of 16 (opposition share unmeasured)",
    },
    "FXNG4-A5-P2": {
        "differential_months": 16,
        "by_year": {"2018": 11, "2020": 2, "2023": 2, "2024": 1},
        "fired_prior": "BLIND 6-13 of 16 at 40-80% gate pass",
    },
}

COST_BPS_PER_SIDE = 1.5
COST_TIER = 2.0


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: str, payload: dict) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    return sha256_file(path)


def load_proposal(pid: str) -> tuple[dict, str]:
    spec = PROPOSAL_SPECS[pid]
    path = os.path.join(WORKTREE, spec["path"])
    digest = sha256_file(path)
    if digest != spec["sha256"]:
        raise SystemExit(f"proposal {pid} sha drift: {digest}")
    with open(path, "rb") as fh:
        return json.load(fh), digest


# --------------------------------------------------------------------------- #
# 1. pinned inputs
# --------------------------------------------------------------------------- #

def load_pinned_inputs() -> dict:
    prov: dict = {}

    # ng4 p0c wide-window census (verify-on-read sha pin)
    ng4_sha = sha256_file(NG4_CENSUS_PATH)
    if ng4_sha != NG4_CENSUS_SHA_PIN:
        raise SystemExit(f"ng4 census sha drift: {ng4_sha}")
    ng4_census = json.load(open(NG4_CENSUS_PATH, encoding="utf-8"))
    prov["ng4_census"] = {"path": NG4_CENSUS_PATH, "sha256": ng4_sha}

    # EZ wide-window pinned bytes: committed manifest sha pin + the
    # module's own verify-on-read (pages + merged == merge(pages))
    wide_manifest_sha = sha256_file(EZ_WIDE_MANIFEST_PATH)
    if wide_manifest_sha != EZ_WIDE_MANIFEST_SHA_PIN:
        raise SystemExit(f"EZ wide manifest sha drift: {wide_manifest_sha}")
    wide_payload, wide_rows = wp.load_pinned_wide(EZ_WIDE_MANIFEST_PATH,
                                                  EZ_WIDE_PIN_DIR)
    prov["ez_wide"] = {
        "manifest_path": EZ_WIDE_MANIFEST_PATH,
        "manifest_sha256": wide_manifest_sha,
        "pin_dir": EZ_WIDE_PIN_DIR,
        "rows": len(wide_rows),
        "verify_on_read": "PASS (load_pinned_wide re-hashed every page + "
                          "the merged document, re-merged and required "
                          "byte-equality, then re-ran the wide-response "
                          "canaries)",
    }

    # ng1 announcement census (kill shadows + V7 rebuild input)
    ng1_census = E.load_census(NG1_CENSUS_PATH)
    prov["ng1_census"] = {"path": NG1_CENSUS_PATH,
                          "sha256": E.CENSUS_SHA256_PIN}

    # ng3 revision census (ng3 kill shadows input)
    ng3_sha = sha256_file(NG3_CENSUS_PATH)
    if ng3_sha != NG3_CENSUS_SHA_PIN:
        raise SystemExit(f"ng3 census sha drift: {ng3_sha}")
    ng3_census = json.load(open(NG3_CENSUS_PATH, encoding="utf-8"))
    prov["ng3_census"] = {"path": NG3_CENSUS_PATH, "sha256": ng3_sha}

    # spot: 4 funded pairs (ng1 manifest) + EURUSD (ng4 manifest),
    # verify-on-read; grid law 1842 days, EURUSD removes no day
    ng1_manifest = ss.load_pin_manifest(NG1_SPOT_MANIFEST_PATH)
    first_entry = next(iter(ng1_manifest["files"].values()))
    funded_dir = os.path.dirname(first_entry["copy_path_absolute"])
    if not os.path.isdir(funded_dir):
        funded_dir = os.path.join(WORKTREE, "data_raw/forex_ng1_spot")
    funded = ss.resolve_all_pairs(NG1_SPOT_MANIFEST_PATH, funded_dir)
    ng4_manifest_sha = sha256_file(NG4_SPOT_MANIFEST_PATH)
    if ng4_manifest_sha != NG4_SPOT_MANIFEST_SHA_PIN:
        raise SystemExit(f"ng4 spot manifest sha drift: {ng4_manifest_sha}")
    with open(NG4_SPOT_MANIFEST_PATH, "r", encoding="utf-8") as fh:
        ng4_manifest = json.load(fh)
    eurusd_entry = ng4_manifest["files"]["EURUSD"]
    eurusd_path = eurusd_entry["copy_path_absolute"]
    if not os.path.exists(eurusd_path):
        eurusd_path = os.path.join(WORKTREE, "data_raw/forex_ng4_spot",
                                   "EURUSD.json")
    eurusd_sha = sha256_file(eurusd_path)
    if eurusd_sha != eurusd_entry["copy_sha256"]:
        raise SystemExit(f"EURUSD pinned bytes sha drift: {eurusd_sha}")
    with open(eurusd_path, "r", encoding="utf-8") as fh:
        eurusd_payload = json.load(fh)
    eurusd_bars = ss.parse_spot_payload(eurusd_payload, "EURUSD")
    eurusd_days = tuple(b["date"] for b in eurusd_bars)
    eurusd = ss.SpotSeries(
        pair="EURUSD", bars=len(eurusd_bars), first_day=eurusd_days[0],
        last_day=eurusd_days[-1], days=eurusd_days,
        closes={b["date"]: b["close"] for b in eurusd_bars},
        sha256=eurusd_sha)
    serieses = {**funded, "EURUSD": eurusd}
    grid4 = ss.common_weekday_grid(funded, S0_WINDOW[0], S0_WINDOW[1])
    grid5 = ss.common_weekday_grid(serieses, S0_WINDOW[0], S0_WINDOW[1])
    if len(grid4) != GRID_LAW_DAYS:
        raise SystemExit(f"4-pair grid recompute mismatch: {len(grid4)}")
    if grid5 != grid4:
        raise SystemExit("grid_extension_5pair law violated: EURUSD "
                         f"removed {len(set(grid4) - set(grid5))} days")
    prov["spot"] = {
        "ng1_manifest_path": NG1_SPOT_MANIFEST_PATH,
        "ng4_manifest_path": NG4_SPOT_MANIFEST_PATH,
        "ng4_manifest_sha256": ng4_manifest_sha,
        "funded_data_dir": funded_dir,
        "eurusd_pinned_path": eurusd_path,
        "resolved_sha256": {p: s.sha256 for p, s in serieses.items()},
        "bars": {p: s.bars for p, s in serieses.items()},
        "grid_days_4pair": len(grid4),
        "grid_days_5pair": len(grid5),
        "days_removed_by_eurusd": len(set(grid4) - set(grid5)),
        "verify_on_read": "PASS (SpotIntegrityError would have raised)",
    }

    # EZ + US legs: EZ from the pinned wide-window bytes; US from the
    # pinned CADS realtime archive (address == sha256 of bytes)
    us_object = os.path.join(CADS_ROOT, "objects",
                             US_RT_CADS_ADDRESS[:2], US_RT_CADS_ADDRESS)
    with open(us_object, "rb") as fh:
        us_raw = fh.read()
    if hashlib.sha256(us_raw).hexdigest() != US_RT_CADS_ADDRESS:
        raise SystemExit("CADS verify-on-read failed for the US rt archive")
    us_payload = json.loads(us_raw.decode("utf-8"))
    ez_series = VintagedSeries(
        series_id=ezv.SERIES_ID,
        rows=parse_realtime_observations(wide_payload["observations"]))
    us_observations = (us_payload["observations"]
                       if isinstance(us_payload, dict) else us_payload)
    us_series = VintagedSeries(
        series_id="CPIAUCSL",
        rows=parse_realtime_observations(us_observations))
    us_rows = pa.parse_fred_vintaged(us_payload)
    prov["legs"] = {
        "EZ": {"source": "p0c wide-window pinned bytes (CP0000EZ19M086NEST)",
               "rows": len(wide_rows), "spacing": ez_series.spacing},
        "US": {"source": "CADS object 7f18ec98... (address == sha256)",
               "rows": len(us_rows), "spacing": us_series.spacing},
    }

    # ng1 vintaged legs (kill shadows + V7 spillover rebuilds): S2
    # manifest via CADS (GRANTED gate), staging bytes verified
    registry = pa.load_registry()
    ga4 = pa.ga4_granted()
    s2_manifest = pa.consume_s2_manifest(CADS_ROOT, registry, ga4)
    local_paths = {
        rec["file"]: os.path.join(VINTAGED_DIR, name)
        for name, rec in s2_manifest["series"].items()
        if rec["file"].startswith("fred_vintaged/")
        for name in [rec["file"]]
    }
    local_paths["US/fred_cpiaucsl_rt.json"] = us_object
    verify = pa.verify_s2_files(s2_manifest, local_paths)
    failed = [k for k, v in verify.items() if not v["match"]]
    if failed:
        raise SystemExit(f"vintaged leg sha mismatch: {failed}")
    prov["vintaged"] = {
        "s2_manifest_address": pa.S2_PINNED_ADDRESS,
        "staging_root": VINTAGED_DIR,
        "verify": {k: {"file": v["file"], "pinned_sha256": v["pinned_sha256"],
                       "match": v["match"]}
                   for k, v in verify.items()},
    }
    rows_by_eco: dict[str, list] = {}
    series_by_eco: dict[str, VintagedSeries] = {}
    for eco, series_id in ECONOMY_SERIES.items():
        rel = s2_manifest["series"][series_id]["file"]
        path = (us_object if rel.startswith("US/")
                else os.path.join(VINTAGED_DIR, rel))
        payload = json.load(open(path, "rb"))
        observations = (payload["observations"]
                        if isinstance(payload, dict) else payload)
        rows_by_eco[eco] = pa.parse_fred_vintaged(observations)
        series_by_eco[eco] = VintagedSeries(
            series_id=series_id, rows=parse_realtime_observations(
                observations))
    prov["vintaged"]["spacing"] = {
        eco: vs.spacing for eco, vs in series_by_eco.items()}

    # DGS10 pinned bytes (P-13 chain verified at ng3 P0; re-hash here)
    dgs10_sha = sha256_file(DGS10_SOURCE_PATH)
    if dgs10_sha != DGS10_SHA_PIN:
        raise SystemExit(f"DGS10 bytes sha drift: {dgs10_sha}")
    dgs10_payload = json.load(open(DGS10_SOURCE_PATH, "rb"))
    dgs10_rows = pa.parse_fred_vintaged(dgs10_payload)
    prov["dgs10"] = {"path": DGS10_SOURCE_PATH, "sha256": dgs10_sha,
                     "rows": len(dgs10_rows)}

    # committed ancestor evidence (READ-ONLY inheritance)
    v8_books, v8_prov = B.load_committed_cells(V8_EVIDENCE_PATH)
    v7a_books, v7a_prov = B.load_committed_cells(V7_ANCESTORS_PATH)
    v7p_books, v7p_prov = B.load_committed_cells(V7_PROPOSALS_PATH)
    prov["committed_evidence"] = {
        "v8_proposals": v8_prov, "v7_ancestors": v7a_prov,
        "v7_proposals_rerun": v7p_prov,
    }

    # the frozen P-12 representation identities (ng4 + ng1/ng3 shadow
    # authority), sha-pinned fail-closed
    proposals = {}
    for pid in PROPOSAL_SPECS:
        prop, digest = load_proposal(pid)
        proposals[pid] = {
            "hypothesis_id": prop["hypothesis_id"],
            "representation_id":
                prop["representation_identity"]["representation_id"],
            "identity_fields": prop["representation_identity"][
                "identity_fields"],
            "source": PROPOSAL_SPECS[pid]["path"],
            "sha256": digest,
        }
    prov["proposals"] = proposals

    return {"ng4_census": ng4_census, "ng1_census": ng1_census,
            "ng3_census": ng3_census, "grid": grid5,
            "serieses": serieses, "ez_series": ez_series,
            "us_series": us_series, "us_rows": us_rows,
            "wide_rows": wide_rows, "rows_by_eco": rows_by_eco,
            "series_by_eco": series_by_eco, "dgs10_rows": dgs10_rows,
            "provenance": prov,
            "committed": {"v8": v8_books, "v7a": v7a_books,
                          "v7p": v7p_books}}


# --------------------------------------------------------------------------- #
# 2. streams (re-measured, census-reconciled)
# --------------------------------------------------------------------------- #

def build_streams(env: dict) -> dict:
    # EZ restricted stream on the wide-window true-vintage bytes
    ez_stream = rs.build_restricted_stream("EZ", env["wide_rows"])
    us_stream = rs.build_restricted_stream("US", env["us_rows"])
    ez_restricted = ez_stream["restricted"]
    us_restricted = us_stream["restricted"]

    recon = {}
    for eco, stream, declared in (
            ("EZ", ez_stream, env["ng4_census"]["streams"][
                "restricted_events"]),
            ("US", us_stream, env["ng4_census"]["us_side_context"][
                "restricted_events"])):
        recon[eco] = {"census": declared,
                      "d2_rebuild": len(stream["restricted"]),
                      "match": declared == len(stream["restricted"])}
        if not recon[eco]["match"]:
            raise SystemExit(f"restricted rebuild != census for {eco}: "
                             f"{recon[eco]}")

    # EZ-US differential months (the census join law, machinery import)
    diff = ezv.ez_us_differential_months(ez_restricted, us_restricted)
    census_months = env["ng4_census"]["differential"]["differential_months"]
    if diff["differential_months"] != census_months:
        raise SystemExit("differential join rebuild != census months")
    lookup = N3.month_event_lookup({"EZ": ez_restricted,
                                    "US": us_restricted})

    # ng3 restricted streams + CA-anchored join (ng3 kill shadows)
    ng3_streams = {eco: rs.build_restricted_stream(eco, rows)
                   for eco, rows in env["rows_by_eco"].items()}
    ng3_restricted = {e: s["restricted"] for e, s in ng3_streams.items()}
    ng3_census_counts = env["ng3_census"]["legs"]
    ng3_recon = {}
    for eco in sorted(ng3_restricted):
        declared = ng3_census_counts[eco]["restricted_events"]
        ng3_recon[eco] = {"census": declared,
                          "d2_rebuild": len(ng3_restricted[eco]),
                          "match": declared == len(ng3_restricted[eco])}
        if not ng3_recon[eco]["match"]:
            raise SystemExit(f"ng3 restricted rebuild != census for "
                             f"{eco}: {ng3_recon[eco]}")
    ng3_diff = rs.restricted_differential_months(ng3_restricted)
    ng3_lookup = N3.month_event_lookup(ng3_restricted)
    ng3_transfer = [(m, leg) for m in ng3_diff["sorted_month_keys"]
                    for leg in ng3_diff["months"][m][1:]
                    if leg in N3.LEG_PAIR]

    return {"ez_restricted": ez_restricted, "us_restricted": us_restricted,
            "diff": diff, "lookup": lookup,
            "reconciliation": recon,
            "ng3_restricted": ng3_restricted, "ng3_diff": ng3_diff,
            "ng3_lookup": ng3_lookup, "ng3_transfer": ng3_transfer,
            "ng3_reconciliation": ng3_recon}


# --------------------------------------------------------------------------- #
# 3. books (anchors, controls, kill shadows, veto panel)
# --------------------------------------------------------------------------- #

def build_all_books(env: dict, streams: dict) -> dict:
    grid = env["grid"]
    grid_index = {d: i for i, d in enumerate(grid)}
    grid_iso = [d.isoformat() for d in grid]
    window_end = S0_WINDOW[1]
    ez_restricted = streams["ez_restricted"]
    diff_months = streams["diff"]["differential_months"]
    lookup = streams["lookup"]
    ez_series = env["ez_series"]

    # --- ng4 anchors + identifiability controls ---------------------- #
    a4p1 = N4.build_ng4_a4_book("FXNG4-A4-P1-ANCHOR", "anchor",
                                "s1_seasonal_naive", N4.A4P1_THRESHOLD_PP,
                                ez_restricted, ez_series, grid, grid_index,
                                window_end)
    a4p2 = N4.build_ng4_a4_book("FXNG4-A4-P2-ANCHOR", "anchor",
                                "s2_trailing_yoy", N4.A4P2_THRESHOLD_PP,
                                ez_restricted, ez_series, grid, grid_index,
                                window_end)
    a4p1_recap = N4.build_ng4_a4_book("FXNG4-A4-P1-CTL-V7RECAP", "v7recap",
                                      "s1_seasonal_naive",
                                      N4.A4P1_THRESHOLD_PP, ez_restricted,
                                      ez_series, grid, grid_index,
                                      window_end)
    a4p2_recap = N4.build_ng4_a4_book("FXNG4-A4-P2-CTL-V7RECAP", "v7recap",
                                      "s2_trailing_yoy",
                                      N4.A4P2_THRESHOLD_PP, ez_restricted,
                                      ez_series, grid, grid_index,
                                      window_end)

    a5p1 = N4.build_ng4_a5_book("FXNG4-A5-P1-ANCHOR", "anchor_p1",
                                diff_months, lookup, grid, grid_index,
                                window_end)
    a5p2 = N4.build_ng4_a5_book("FXNG4-A5-P2-ANCHOR", "anchor_p2",
                                diff_months, lookup, grid, grid_index,
                                window_end)
    a5p1_nodiff = N4.build_ng4_a5_book("FXNG4-A5-P1-CTL-V7NODIFF",
                                       "v7nodiff_p1", diff_months, lookup,
                                       grid, grid_index, window_end)
    a5p2_nodiff = N4.build_ng4_a5_book("FXNG4-A5-P2-CTL-V7NODIFF",
                                       "v7nodiff_p2", diff_months, lookup,
                                       grid, grid_index, window_end)
    a5p1_ppp = N4.build_ng4_ppp_ancestry_control(
        "FXNG4-A5-P1-CTL-PPPANCESTRY", a5p1, ez_restricted, grid,
        grid_index)
    a5p2_ppp = N4.build_ng4_ppp_ancestry_control(
        "FXNG4-A5-P2-CTL-PPPANCESTRY", a5p2, ez_restricted, grid,
        grid_index)

    # A4 exact-spec CTL-DGS10LEVEL (ng4 EURUSD sign law)
    levels = N3.dgs10_grid_levels(env["dgs10_rows"], grid)
    dgs10_a4p1 = N4.build_ng4_dgs10_z252_book(
        "FXNG4-A4-P1-CTL-DGS10LEVEL-EXACT", a4p1, levels, grid, grid_index)
    dgs10_a4p2 = N4.build_ng4_dgs10_z252_book(
        "FXNG4-A4-P2-CTL-DGS10LEVEL-EXACT", a4p2, levels, grid, grid_index)

    # --- kill-candidate shadows (declared by the D1 proposals) ------- #
    ng1_events = E.first_release_events(env["ng1_census"])
    state = E.order_state(ng1_events)
    kill_ng1_a4p1 = N4.build_ng1_a4_kill_shadow(
        "FXNG1-A4-P1-print-deviation-shadow", "s1_seasonal_naive", 0.10,
        ng1_events, env["series_by_eco"], grid, grid_index, window_end)
    kill_ng1_a4p2 = N4.build_ng1_a4_kill_shadow(
        "FXNG1-A4-P2-acceleration-shadow", "s2_trailing_yoy", 0.15,
        ng1_events, env["series_by_eco"], grid, grid_index, window_end)
    kill_ng1_a5p1 = B.build_a5p1_book("FXNG1-A5-P1-release-order-shadow",
                                      "anchor", state,
                                      env["series_by_eco"], grid, grid_index,
                                      window_end, threshold=0.10)
    kill_ng3_a5p1 = N3.build_ng3_a5p1_book(
        "FXNG3-A5-P1-differential-shadow", "anchor",
        streams["ng3_diff"]["months"], streams["ng3_lookup"], grid,
        grid_index, window_end, gate_pp=0.02)
    kill_ng3_a5p2 = N3.build_ng3_a5p2_book(
        "FXNG3-A5-P2-transfer-shadow", "anchor", streams["ng3_transfer"],
        streams["ng3_lookup"], grid, grid_index, window_end, gate_pp=0.02)
    kill_v9_ppp = N4.build_v9_ppp_shadow(
        "FXFV9-A5-PPP-deviation-shadow-eurusd",
        env["serieses"]["EURUSD"].closes, ez_series, env["us_series"],
        grid, grid_index, window_end)

    kill_shadows = {
        "FXNG1-A4-P1-print-deviation-shadow": kill_ng1_a4p1,
        "FXNG1-A4-P2-acceleration-shadow": kill_ng1_a4p2,
        "FXNG1-A5-P1-release-order-shadow": kill_ng1_a5p1,
        "FXNG3-A5-P1-differential-shadow": kill_ng3_a5p1,
        "FXNG3-A5-P2-transfer-shadow": kill_ng3_a5p2,
        "FXFV9-A5-PPP-deviation-shadow-eurusd": kill_v9_ppp,
    }

    # --- the veto panel: ng1 25-shape panel rebuilt on the 5-pair plane
    closes = {p: s.closes for p, s in env["serieses"].items()}
    v8_names = ["FXFV8-A5-P1-anchor", "FXFV8-A5-P1-neighbour-z504",
                "FXFV8-A5-P1-control-dgs10",
                "FXFV8-A4-P2-neighbour-sham7d", "FXFV8-A4-P2-anchor",
                "FXFV8-A4-P2-control-dgs10", "FXFV8-A4-P1-anchor",
                "FXFV8-A4-P1-control-dgs10"]
    panel: dict[str, dict] = {}
    for n in v8_names:
        if n in env["committed"]["v8"]:
            panel[n] = env["committed"]["v8"][n]
    panel["V4_commodity_bloc_exposure"] = env["committed"]["v7a"][
        "V4_commodity_bloc_exposure"]
    panel["FXFV7-A4-P1_anchor_k4_committed"] = env["committed"]["v7p"][
        "FXFV7-A4-P1_anchor_k4"]
    panel["FXFV7-A6-P2_anchor_q80_committed"] = env["committed"]["v7p"][
        "FXFV7-A6-P2_anchor_q80"]
    panel.update(N4.build_v7_spillover_shadows_5pair(
        ng1_events, env["series_by_eco"], grid, grid_index, window_end))
    panel.update(N4.build_v7_leadlag_shadows_5pair(closes, grid, grid_index))
    panel.update(N4.build_generic_shapes_5pair(closes, grid, grid_index))
    panel_names_rebuilt = sorted(panel)
    panel.update(kill_shadows)

    return {"anchors": {"FXNG4-A4-P1": a4p1, "FXNG4-A4-P2": a4p2,
                        "FXNG4-A5-P1": a5p1, "FXNG4-A5-P2": a5p2},
            "ident_controls": {
                "FXNG4-A4-P1": {"CTL-V7RECAP": a4p1_recap},
                "FXNG4-A4-P2": {"CTL-V7RECAP": a4p2_recap},
                "FXNG4-A5-P1": {"CTL-PPPANCESTRY": a5p1_ppp,
                                "CTL-V7NODIFF": a5p1_nodiff},
                "FXNG4-A5-P2": {"CTL-PPPANCESTRY": a5p2_ppp,
                                "CTL-V7NODIFF": a5p2_nodiff}},
            "dgs10_exact": {"FXNG4-A4-P1": dgs10_a4p1,
                            "FXNG4-A4-P2": dgs10_a4p2},
            "kill_shadows": kill_shadows,
            "panel": panel, "panel_names_rebuilt": panel_names_rebuilt,
            "grid_iso": grid_iso, "levels": levels}


# --------------------------------------------------------------------------- #
# 4. novelty panel
# --------------------------------------------------------------------------- #

def novelty_panel(env: dict, built: dict) -> dict:
    anchors = built["anchors"]
    grid_iso = built["grid_iso"]
    panel = built["panel"]
    results = {}
    for pid, anchor in anchors.items():
        comparisons = {}
        for vname, veto in panel.items():
            comparisons[vname] = R.compare_schedules(
                anchor["cells"], veto["cells"], grid_iso, SHARED_PAIRS)
        pooled = R.pooled_max_abs_rho(comparisons)
        margins = {}
        for row in pooled["rows"]:
            r = row["max_abs_rho"]
            margins[row["veto"]] = (None if r is None
                                    else round(N4.NOVELTY_BAR - r, 4))
        kill_rows = {k: comparisons[k] for k in built["kill_shadows"]}
        unmeasurable = sorted(
            k for k, v in comparisons.items()
            if v.get("max_abs_rho") is None)
        results[pid] = {
            "anchor_active_cells": anchor["meta"]["active_cells"],
            "pooled": pooled,
            "margins_to_bar": margins,
            "kill_candidate_shapes": {
                k: {"max_abs_rho": v.get("max_abs_rho"),
                    "verdict": v.get("verdict")} for k, v in kill_rows.items()},
            "unmeasurable_rows": unmeasurable,
            "unmeasurable_disclosure": (
                "rows whose schedule shares no pair with the EURUSD-only "
                "anchor on the frozen shared-pair machinery (verdict "
                "NO_SHARED_PAIRS or a constant vector): recorded honestly, "
                "never silently dropped, never counted as PASS; the "
                "EURUSD-plane coverage of those axes is carried by the "
                "ng1 A4 US-leg shadows (print-deviation/acceleration), the "
                "V9 PPP-deviation EURUSD rebuild and the in-book "
                "identifiability controls"),
            "per_veto": comparisons,
        }

    cross = {}
    for pid_a, pid_b in (("FXNG4-A4-P1", "FXNG4-A4-P2"),
                         ("FXNG4-A5-P1", "FXNG4-A5-P2"),
                         ("FXNG4-A4-P1", "FXNG4-A5-P1")):
        cmp = R.compare_schedules(anchors[pid_a]["cells"],
                                  anchors[pid_b]["cells"], grid_iso,
                                  SHARED_PAIRS)
        cross[f"{pid_a}_vs_{pid_b}"] = cmp

    return {"bar": N4.NOVELTY_BAR,
            "panel_names": sorted(panel),
            "panel_names_rebuilt_5pair": built["panel_names_rebuilt"],
            "added_kill_candidate_shapes": sorted(built["kill_shadows"]),
            "results": results,
            "cross_proposal_collapse": cross,
            "method": {
                "representation": "signed exposure cells date|pair on the "
                                  "frozen daily 16:00-NY 5-pair common grid "
                                  f"({GRID_LAW_DAYS} days "
                                  f"{S0_WINDOW[0].isoformat()}.."
                                  f"{S0_WINDOW[1].isoformat()}; EURUSD "
                                  "removes no day, p0_gate "
                                  "grid_extension_5pair law); exposure "
                                  "cells i..i+H-1; netting sign-of-sum",
                "variants": ["cellwise_signed_full_grid",
                             "cellwise_union_active",
                             "netsigned_union_dates_shared_pairs"],
                "rho": "Spearman, average-tie ranks, |rho| pooled max "
                       "over panel x variants; global sign flips of a "
                       "shape leave |rho| unchanged",
                "shared_pairs": SHARED_PAIRS,
                "panel_composition": "the ng1 25-shape panel rebuilt on "
                                     "the 5-pair ng4 plane (8 committed "
                                     "FXFV8 shapes -- V8's 7-pair books "
                                     "carry EURUSD cells natively; V4 "
                                     "commodity bloc + committed FXFV7 "
                                     "A6-P2 carried verbatim, no EURUSD "
                                     "leg, honest NO_SHARED_PAIRS rows; 2 "
                                     "spillover rebuilds with EURUSD "
                                     "restored as a destination per the "
                                     "true V7 plane; 5 lead-lag rebuilds "
                                     "incl. the EURUSD-leader TRUE V7 "
                                     "form; 8 generics incl. EURUSD) + 6 "
                                     "declared kill-candidate shadows "
                                     "(ng1 A4 print-deviation + "
                                     "acceleration with the US-event leg "
                                     "extended to EURUSD -- adaptation "
                                     "disclosed; ng1 A5-P1 release-order, "
                                     "ng3 A5-P1 differential, ng3 A5-P2 "
                                     "transfer rebuilt VERBATIM on their "
                                     "own funded pairs, no EURUSD leg "
                                     "exists in those identities, honest "
                                     "NO_SHARED_PAIRS rows; the V9 "
                                     "PPP-deviation form rebuilt on "
                                     "EURUSD from the FAMILY_FAILURES row "
                                     "spec + the V9 P2 clocks census "
                                     "state definition)",
            }}


# --------------------------------------------------------------------------- #
# 5. feasibility + identifiability + verdicts
# --------------------------------------------------------------------------- #

def a9f_ceiling(book: dict, years: float) -> dict:
    m = book["meta"]
    fired = m.get("fired_events", m.get("months_gate_passed",
                                        m.get("pair_decisions_fired", 0)))
    fills = 2 * fired
    per_side = COST_BPS_PER_SIDE * COST_TIER
    return {
        "ladder": "REFERENCED proxy 1.5 bps/side, stress tier 2.0 "
                  "(V2/V8 precedent; EURUSD Q-8 measured constants "
                  "NOT_YET_MEASURED by the P1 kernel lane -> the "
                  "proposal-law cost verdict stays NOT_RUN fail-closed)",
        "fired_positions": fired,
        "total_fills": fills,
        "cost_bps_per_side_referenced": per_side,
        "cost_bps_round_trip_per_position": 2 * per_side,
        "total_cost_ceiling_bps_per_unit_notional": fills * per_side,
        "fired_positions_per_year": (round(fired / years, 3)
                                     if years else None),
        "holds_grid_days": m.get("hold_grid_days"),
    }


def identifiability(built: dict) -> dict:
    grid_iso = built["grid_iso"]
    out = {"kill_bar": N4.IDENTIFIABILITY_KILL,
           "kill_controls": {"FXNG4-A4": "CTL-V7RECAP (plan sec1 "
                                         "MANDATORY: EZ prints are "
                                         "reaction forms)",
                             "FXNG4-A5": "CTL-PPPANCESTRY (kill-candidate "
                                         "#1, the V9 PPP re-clock test)"},
           "results": {}}

    def _signs(book):
        return {s: list(book["cells"].values()).count(s)
                for s in (1, -1)}

    for pid, controls in built["ident_controls"].items():
        anchor = built["anchors"][pid]
        entry: dict = {"controls": {}}
        kill_name, kill_rho = None, None
        primary = ("CTL-PPPANCESTRY" if pid.startswith("FXNG4-A5")
                   else "CTL-V7RECAP")
        for cname, cbook in controls.items():
            cmp = R.compare_schedules(anchor["cells"], cbook["cells"],
                                      grid_iso, SHARED_PAIRS)
            r = cmp.get("max_abs_rho")
            entry["controls"][cname] = {
                "comparison": cmp,
                "control_vs_anchor_max_abs_rho": r,
                "control_meta": {k: v for k, v in cbook["meta"].items()
                                 if k in ("fired_events", "months_total",
                                          "months_gate_passed",
                                          "source_fired_events",
                                          "dropped_insufficient_priors",
                                          "dropped_no_position_band",
                                          "dropped_insufficient_history",
                                          "sign_counts",
                                          "events_total",
                                          "events_in_window")},
                "q11_null_validity": N4.q11_null_validity(
                    r, cname, _signs(anchor), _signs(cbook),
                    cmp.get("verdict")),
            }
            if cname == primary and r is not None:
                kill_name, kill_rho = cname, r
        entry["primary_kill_control"] = primary
        entry["primary_control_vs_anchor_max_abs_rho"] = kill_rho
        entry["kill_pre_score"] = bool(kill_rho is not None
                                       and kill_rho
                                       >= N4.IDENTIFIABILITY_KILL)
        out["results"][pid] = entry

    # A4 nominal separability: committed V8 DGS10-level shapes + the
    # exact-spec z252 book from the pinned DGS10 bytes (EURUSD law)
    committed_dgs10 = [
        ("FXFV8-A5-P1-control-dgs10", built["panel"][
            "FXFV8-A5-P1-control-dgs10"]),
        ("FXFV8-A4-P1-control-dgs10", built["panel"][
            "FXFV8-A4-P1-control-dgs10"]),
        ("FXFV8-A4-P2-control-dgs10", built["panel"][
            "FXFV8-A4-P2-control-dgs10"]),
    ]
    for pid in ("FXNG4-A4-P1", "FXNG4-A4-P2"):
        anchor = built["anchors"][pid]
        entry = out["results"][pid]
        entry["nominal_separability"] = {}
        worst = None
        for name, shape in committed_dgs10:
            cmp = R.compare_schedules(anchor["cells"], shape["cells"],
                                      grid_iso, SHARED_PAIRS)
            entry["nominal_separability"][name] = {
                "max_abs_rho": cmp.get("max_abs_rho"),
                "verdict": cmp.get("verdict")}
            r = cmp.get("max_abs_rho")
            if r is not None and (worst is None or r > worst):
                worst = r
        entry["nominal_separability_max_abs_rho"] = worst
        exact = built["dgs10_exact"][pid]
        cmp = R.compare_schedules(anchor["cells"], exact["cells"],
                                  grid_iso, SHARED_PAIRS)
        entry["exact_spec_ctl_dgs10"] = {
            "comparison": cmp,
            "meta": exact["meta"],
            "note": "exact-spec CTL-DGS10LEVEL (trailing 252-grid-day "
                    "median of the pinned vintaged DGS10 level, as-of "
                    "reads, sign = +1 LONG EURUSD iff below median) on "
                    "the anchor's own fired days; P-13 chain bytes "
                    "(03dde429...) re-hashed by this runner",
        }
    return out


def feasibility(env, streams, built, novelty) -> dict:
    anchors = built["anchors"]
    s0_years = (S0_WINDOW[1] - S0_WINDOW[0]).days / 365.25
    ez_restricted = streams["ez_restricted"]
    diff = streams["diff"]
    ez_recent = rs.restricted_recent_events(ez_restricted)

    # cohort structure re-measured from the rebuild
    obs_months = sorted(e.obs_month for e in ez_restricted)
    cohort = [m for m in obs_months
              if "2015-03" <= m[:7] <= "2017-11"]
    obs_2018 = [m for m in obs_months if "2018-02" <= m[:7] <= "2018-12"]
    obs_2017_12 = [m for m in obs_months if m[:7] == "2017-12"]
    later = [m[:7] for m in obs_months if m[:7] >= "2018-01"
             and not ("2018-02" <= m[:7] <= "2018-12")]
    diff_years: Counter = Counter(m[:4] for m in
                                  diff["differential_months"])

    measured_totals = {
        "FXNG4-A4-P1": {
            "restricted_events": len(ez_restricted),
            "obs_months_span": [obs_months[0][:7], obs_months[-1][:7]],
            "cohort_2015_03_2017_11": len(cohort),
            "obs_2018_02_2018_12": len(obs_2018),
            "obs_2017_12": len(obs_2017_12),
            "later_months": later,
            "q6_recent_v2_basis": ez_recent["count"],
            "events_in_window": anchors["FXNG4-A4-P1"]["meta"][
                "events_in_window"],
            "fired_events": anchors["FXNG4-A4-P1"]["meta"]["fired_events"],
            "below_threshold": anchors["FXNG4-A4-P1"]["meta"][
                "below_threshold"],
            "events_failed_closed": anchors["FXNG4-A4-P1"]["meta"][
                "events_failed_closed"],
            "ctl_v7recap_fired": built["ident_controls"][
                "FXNG4-A4-P1"]["CTL-V7RECAP"]["meta"]["fired_events"],
        },
        "FXNG4-A4-P2": {
            "restricted_events": len(ez_restricted),
            "q6_recent_v2_basis": ez_recent["count"],
            "events_in_window": anchors["FXNG4-A4-P2"]["meta"][
                "events_in_window"],
            "fired_events": anchors["FXNG4-A4-P2"]["meta"]["fired_events"],
            "below_threshold": anchors["FXNG4-A4-P2"]["meta"][
                "below_threshold"],
            "ctl_v7recap_fired": built["ident_controls"][
                "FXNG4-A4-P2"]["CTL-V7RECAP"]["meta"]["fired_events"],
        },
        "FXNG4-A5-P1": {
            "differential_months": diff["total"],
            "by_year": dict(sorted(diff_years.items())),
            "ez_only_months": (len(diff["ez_restricted_months"])
                               - diff["total"]),
            "us_restricted_events": len(streams["us_restricted"]),
            "q6_ez_stream_v2_basis": ez_recent["count"],
            "months_opposed": anchors["FXNG4-A5-P1"]["meta"][
                "months_opposed"],
            "months_agreed": anchors["FXNG4-A5-P1"]["meta"][
                "months_agreed"],
            "fired_events": anchors["FXNG4-A5-P1"]["meta"][
                "months_gate_passed"],
            "q6_recent_obs_basis": anchors["FXNG4-A5-P1"]["meta"][
                "recent_months_obs_basis"],
            "q6_recent_avail_basis": anchors["FXNG4-A5-P1"]["meta"][
                "recent_months_avail_basis"],
            "q6_recent_entry_basis": anchors["FXNG4-A5-P1"]["meta"][
                "recent_months_entry_basis"],
            "ctl_v7nodiff_fired": built["ident_controls"][
                "FXNG4-A5-P1"]["CTL-V7NODIFF"]["meta"][
                "months_gate_passed"],
            "ctl_pppancestry_fired": built["ident_controls"][
                "FXNG4-A5-P1"]["CTL-PPPANCESTRY"]["meta"]["fired_events"],
        },
        "FXNG4-A5-P2": {
            "differential_months": diff["total"],
            "by_year": dict(sorted(diff_years.items())),
            "fired_events": anchors["FXNG4-A5-P2"]["meta"][
                "months_gate_passed"],
            "gate_failed": anchors["FXNG4-A5-P2"]["meta"][
                "months_gate_failed"],
            "q6_recent_obs_basis": anchors["FXNG4-A5-P2"]["meta"][
                "recent_months_obs_basis"],
            "q6_recent_avail_basis": anchors["FXNG4-A5-P2"]["meta"][
                "recent_months_avail_basis"],
            "q6_recent_entry_basis": anchors["FXNG4-A5-P2"]["meta"][
                "recent_months_entry_basis"],
            "ctl_v7nodiff_fired": built["ident_controls"][
                "FXNG4-A5-P2"]["CTL-V7NODIFF"]["meta"][
                "months_gate_passed"],
            "ctl_pppancestry_fired": built["ident_controls"][
                "FXNG4-A5-P2"]["CTL-PPPANCESTRY"]["meta"]["fired_events"],
        },
    }
    declared_checks = {}
    for pid, dec in DECLARED.items():
        got = measured_totals[pid]
        match = {}
        for k, dv in dec.items():
            if isinstance(dv, str):        # BLIND priors stay disclosed
                match[k] = "BLIND_BY_DECLARATION_measured_now"
            elif k == "later_months":
                match[k] = dv == got.get(k)
            elif k == "by_year":
                match[k] = dv == got.get(k)
            else:
                match[k] = dv == got.get(k)
        declared_checks[pid] = {"declared": dec, "measured": got,
                                "match": match,
                                "note": "declared values cite the "
                                        "committed D1 proposals "
                                        "(sha256-pinned in the novelty "
                                        "output); fired priors were "
                                        "declared BLIND at D1 and are "
                                        "measured here for the first time"}

    ident = identifiability(built)

    # structural disclosures: entry-day stacking, sign counts
    struct = {}
    for pid, book in anchors.items():
        cells = book["cells"]
        struct[pid] = {
            "distinct_active_grid_days": len({k.split("|")[0]
                                              for k in cells}),
            "active_cells": len(cells),
            "sign_counts": {s: list(cells.values()).count(s)
                            for s in (1, -1)},
            "fired_events": book["meta"].get(
                "fired_events", book["meta"].get("months_gate_passed")),
            "dropped_tail_entries": book["meta"].get(
                "dropped_tail_entries"),
        }

    verdicts = {}
    for pid, anchor in anchors.items():
        nov = novelty["results"][pid]["pooled"]["max_pooled_abs_rho"]
        fired = anchor["meta"].get(
            "fired_events", anchor["meta"].get("months_gate_passed", 0))
        kill_rho = ident["results"][pid]["primary_control_vs_anchor_"
                                         "max_abs_rho"]
        verdicts[pid] = N4.proposal_verdict(
            novelty_max_abs_rho=nov,
            empty_book=(fired == 0),
            identifiability_kill=kill_rho,
            kill_control_name=ident["results"][pid]["primary_kill_control"])

    q6 = {
        "window": [N4.RECENT_WINDOW_START.isoformat(),
                   N4.RECENT_WINDOW_END.isoformat()],
        "law": N4.Q6_VERDICT_LAW,
        "plan_sec3_check": "plans/PLAN_forex_ng4.md sec 3 read at this "
                           "checkout: floors frozen ONLY on A4 EZ print "
                           "events >= 30 and A5 EZ-US differential months "
                           ">= 12 (both re-measured in "
                           "totals_vs_declared); NO recent-window floor "
                           "exists for ng4 -- the ng3 >= 15 recent floor "
                           "was CA-specific and is not inferred",
        "FXNG4-A4-P1": N4.evaluate_q6_no_floor(
            ez_recent["count"], "EZ restricted events with v2 "
                                "availability day in window (p0c census "
                                "law)"),
        "FXNG4-A4-P2": N4.evaluate_q6_no_floor(
            ez_recent["count"], "EZ restricted events with v2 "
                                "availability day in window (p0c census "
                                "law)"),
        "FXNG4-A5-P1": N4.evaluate_q6_no_floor(
            anchors["FXNG4-A5-P1"]["meta"]["recent_months_avail_basis"],
            "differential months with A(m) = max(v2_EZ, v2_US) in window; "
            "obs-month basis measured "
            f"{anchors['FXNG4-A5-P1']['meta']['recent_months_obs_basis']} "
            "(structurally 0: no differential obs month after 2024-02) "
            "and entry-day basis "
            f"{anchors['FXNG4-A5-P1']['meta']['recent_months_entry_basis']} "
            "disclosed"),
        "FXNG4-A5-P2": N4.evaluate_q6_no_floor(
            anchors["FXNG4-A5-P2"]["meta"]["recent_months_avail_basis"],
            "differential months with A(m) = max(v2_EZ, v2_US) in window; "
            "obs-month basis measured "
            f"{anchors['FXNG4-A5-P2']['meta']['recent_months_obs_basis']} "
            "and entry-day basis "
            f"{anchors['FXNG4-A5-P2']['meta']['recent_months_entry_basis']} "
            "disclosed"),
        "thin_disclosure": "the recent window is structurally thin (A4 "
                           f"measured {ez_recent['count']} EZ events; the "
                           "differential stream has no obs month after "
                           "2024-02): disclosed for the S selection rubric, "
                           "never repaired by re-parameterization, never "
                           "converted into a verdict (no floor frozen)",
    }

    return {
        "schema": "forex_ng4_run/d2_feasibility@1",
        "q6_recent_window": q6,
        "totals_vs_declared": declared_checks,
        "restricted_rebuild_vs_census": {
            "ng4": streams["reconciliation"],
            "ng3_shadows": streams["ng3_reconciliation"],
            "differential_join_months_match_census": True},
        "floors_total": {
            "a4_ez_print_events": {"measured": len(ez_restricted),
                                   "floor": 30,
                                   "margin": len(ez_restricted) - 30,
                                   "verdict": ("PASS" if len(ez_restricted)
                                               >= 30 else "FAIL")},
            "a5_ez_us_differential_months": {
                "measured": diff["total"], "floor": 12,
                "margin": diff["total"] - 12,
                "verdict": "PASS" if diff["total"] >= 12 else "FAIL"},
            "law": "plan sec 3 frozen TOTAL floors (p0c gate basis); "
                   "re-measured at D2 from the pinned bytes"},
        "structural_disclosures": {
            "books": struct,
            "note": "the EZ restricted stream's v2 availability days "
                    "cluster in vintage bursts (32 of 37 events have v2 "
                    "days <= 2019, D1 declared concentration risk), so "
                    "events stack onto few distinct entry grid days and "
                    "same-day positions net sign-of-sum (P-12 cell law); "
                    "rho over such stacked books is measured exactly as "
                    "the frozen machinery defines it, with per-variant "
                    "sample sizes recorded in the novelty panel",
        },
        "a9f_cost_ceiling_referenced": {
            pid: a9f_ceiling(book, s0_years)
            for pid, book in anchors.items()},
        "identifiability": ident,
        "verdicts": verdicts,
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    started = utcnow_iso()
    env = load_pinned_inputs()
    streams = build_streams(env)
    built = build_all_books(env, streams)

    novelty = {
        "schema": "forex_ng4_run/d2_novelty_panel@1",
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-d2-measurement",
        "measured_utc": started,
        "no_expectancy_law": "NO expectancy/PnL/PF computed in this "
                             "lane; rho is measured between signal "
                             "schedules only",
        "proposal_representation_identities": {
            pid: {"hypothesis_id": p["hypothesis_id"],
                  "representation_id": p["representation_id"],
                  "source": p["source"], "sha256": p["sha256"]}
            for pid, p in env["provenance"]["proposals"].items()},
        "restricted_rebuild_vs_census": {
            "ng4": streams["reconciliation"],
            "ng3_shadows": streams["ng3_reconciliation"]},
        "representation_identity": {
            "grid": "daily 16:00 America/New_York 5-pair common weekday "
                    f"grid, {GRID_LAW_DAYS} days "
                    f"{S0_WINDOW[0].isoformat()}..{S0_WINDOW[1].isoformat()} "
                    "(recomputed from the pinned spot bytes; EURUSD "
                    "removes no day -- grid_extension_5pair law)",
            "cells": "signed exposure date|pair, entry i..i+H-1, "
                     "netting sign-of-sum (identical to the ng1/ng3 D2 "
                     "convention, reused via import)",
            "entry_clock": "D(e) = first common-grid day strictly after "
                           "EOD(v2.realtime_start) (A4: the EZ v2-day PIT "
                           "law) / after EOD(max(v2_EZ, v2_US)) (A5: the "
                           "max-v2 law); front convention for pre-window "
                           "A(m) is the first grid instant (the proposals' "
                           "declared convention)",
            "surprises": "A4-P1 s1 = 100*(I_print_v1/(I(m-1)*I(m-12)/"
                         "I(m-13))-1), predictor vintaged as-of D(e); "
                         "A4-P2 s2 trailing-YoY form; A5-P1 opposition of "
                         "sign(R_EZ)/sign(R_US); A5-P2 D = R_EZ - R_US "
                         "with R_X = 100*(I_v2/I_v1-1) on restricted "
                         "events",
        },
        "provenance": env["provenance"],
    }
    panel = novelty_panel(env, built)
    novelty.update(panel)

    feas = feasibility(env, streams, built, panel)
    feas["measured_utc"] = started
    feas["cycle_id"] = "FOREX-NG4"
    feas["task_id"] = "forex-ng4-d2-measurement"

    summary = {
        "schema": "forex_ng4_run/d1_feasibility_summary@1",
        "cycle_id": "FOREX-NG4",
        "task_id": "forex-ng4-d2-measurement",
        "measured_utc": started,
        "source": "research/control/forex_ng4_run/d2/"
                  "d2_feasibility_ng4.json + d2_novelty_panel_ng4.json",
        "recent_window": [N4.RECENT_WINDOW_START.isoformat(),
                          N4.RECENT_WINDOW_END.isoformat()],
        "floors": {"FXNG4-A4-P1": {"total": 30, "recent": None},
                   "FXNG4-A4-P2": {"total": 30, "recent": None},
                   "FXNG4-A5-P1": {"total": 12, "recent": None},
                   "FXNG4-A5-P2": {"total": 12, "recent": None}},
        "q6_law": N4.Q6_VERDICT_LAW,
        "proposals": {},
    }
    for pid, anchor in built["anchors"].items():
        q = feas["q6_recent_window"][pid]
        nov = panel["results"][pid]["pooled"]
        ident_ctl = feas["identifiability"]["results"].get(pid, {})
        summary["proposals"][pid] = {
            "recent_measured": q["measured"], "floor": q["floor"],
            "q6_verdict": q["verdict"],
            "total_floor_pass": (
                feas["floors_total"][
                    "a4_ez_print_events" if pid.startswith("FXNG4-A4")
                    else "a5_ez_us_differential_months"]["verdict"]
                == "PASS"),
            "fired_events": anchor["meta"].get(
                "fired_events",
                anchor["meta"].get("months_gate_passed")),
            "novelty_max_pooled_abs_rho": nov["max_pooled_abs_rho"],
            "novelty_worst": nov["worst"],
            "novelty_pass": (nov["max_pooled_abs_rho"] is not None
                             and nov["max_pooled_abs_rho"]
                             <= N4.NOVELTY_BAR),
            "kill_candidate_shape_rho": {
                k: v["max_abs_rho"]
                for k, v in panel["results"][pid][
                    "kill_candidate_shapes"].items()},
            "identifiability_primary_control":
                ident_ctl.get("primary_kill_control"),
            "identifiability_control_vs_anchor":
                ident_ctl.get("primary_control_vs_anchor_max_abs_rho"),
            "a9f_cost_ceiling_bps_total":
                feas["a9f_cost_ceiling_referenced"][pid][
                    "total_cost_ceiling_bps_per_unit_notional"],
            "verdict": feas["verdicts"][pid],
        }
    cross = panel["cross_proposal_collapse"]
    summary["cross_proposal_collapse"] = {
        k: v.get("max_abs_rho") for k, v in cross.items()}

    code_shas = {rel: sha256_file(os.path.join(WORKTREE, rel))
                 for rel in CODE_FILES}
    novelty["code_sha256"] = code_shas
    feas["code_sha256"] = code_shas
    summary["code_sha256"] = code_shas

    p1 = write_json(OUT_NOVELTY, novelty)
    p2 = write_json(OUT_FEAS, feas)
    p3 = write_json(OUT_FEAS_SUMMARY, summary)
    print("novelty  ->", OUT_NOVELTY, p1[:16])
    print("feas    ->", OUT_FEAS, p2[:16])
    print("summary ->", OUT_FEAS_SUMMARY, p3[:16])
    for pid, verdict in feas["verdicts"].items():
        nov = panel["results"][pid]["pooled"]
        print(f"{pid}: {verdict}  (novelty max|rho|="
              f"{nov['max_pooled_abs_rho']} worst={nov['worst']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
