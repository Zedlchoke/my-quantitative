"""FOREX-NG4 P0 EZ HICP vintaged census decision module.

The plan (plans/PLAN_forex_ng4.md sec 2-3) funds the EZ economy on
PINNED VINTAGED EZ HICP with "V8-measured FULL S0 coverage" claimed by
the V8 final verdicts.  This module measures, fail-closed, whether that
claim can be RE-MEASURED on pinned bytes in this cycle:

1. WHICH series: the V8 evidence names ``CP0000EZ19M086NEST`` (Euro area
   (19 countries) HICP, all items, index; FRED/OECD MEI-derived).  The
   dispatch packet suggested ``EZCPIALLMINMEI``; that id appears in NO
   manifest in the repo -- the correction is recorded with evidence.
2. WHERE the vintaged bytes would live: the pinned V9 staging set
   ``data_raw/forex_free_v9_cpi/fred_vintaged/`` (GB/CA/AU/NZ only, the
   ng1-ng3 pin chain) -- plus an exhaustive filename search across the
   repo for the manifest-pinned file name.
3. WHAT remains if the bytes are absent: only COMMITTED V8 DERIVED
   artifacts (staged manifest entry with sha256 + row counts, dense
   vintage map r2 lag/revision samples, earliest-vintage bound).  These
   are derived stats recorded by V8 at its measurement time -- they are
   EVIDENCE ABOUT the archive, never a re-measurement of it.

Decision law (mission invariant): missing evidence is NOT_RUN, never an
inferred PASS.  If the vintaged bytes are not resolvable:

- the realtime-window coverage census in S0, the first-print/revision
  split (ng2/ng3 standards), the A4 print-event count (floor >= 30) and
  the A5 EZ-vs-US differential months (floor >= 12) are all NOT_RUN;
- the census status is BLOCKED_DATA with the honest blocker:
  EZ vintaged ingest needs an owner / A3-lane decision;
- if a current-vintage DOI file exists anywhere, it may be measured
  RETROSPECTIVE_ONLY (disclosed as unsuitable for PIT decisions) -- if
  none exists, that too is recorded NOT_RUN (honest).
"""

from __future__ import annotations

import json
import os
from typing import Mapping, Sequence

#: The EZ HICP series the V8 evidence actually pinned.
EZ_SERIES_ID = "CP0000EZ19M086NEST"
EZ_SERIES_FILE = f"{EZ_SERIES_ID}.json"
EZ_SERIES_KIND = "ez_hicp monthly (Euro area 19 HICP all-items index, FRED/OECD MEI-derived)"

#: The id suggested by the dispatch packet -- recorded because the
#: correction is itself P0 evidence (it appears in NO manifest).
DISPATCH_SUGGESTED_SERIES_ID = "EZCPIALLMINMEI"

#: Frozen floors (plan section 3, ng2/ng3 law inherited).
EZ_PRINT_EVENT_FLOOR = 30          # A4: EZ print events with full windows
EZ_US_DIFFERENTIAL_FLOOR = 12      # A5: EZ-vs-US differential months

#: Where the pinned vintaged staging actually lives (READ-ONLY).
V9_VINTAGED_DIR = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "forex-free-v9/integration/data_raw/"
                   "forex_free_v9_cpi/fred_vintaged")

#: Committed V8 evidence (READ-ONLY).
V8_RUN_CONTROL = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
                  "forex-free-v9/integration/research/control/"
                  "forex_free_v8_run")
V8_STAGED_MANIFEST = os.path.join(V8_RUN_CONTROL,
                                  "staged_vintaged_manifest.json")
V8_DENSE_MAP_R2 = os.path.join(V8_RUN_CONTROL,
                               "p0_dense_vintage_map_v8_r2.json")
V8_EARLIEST_VINTAGE = os.path.join(V8_RUN_CONTROL,
                                   "p0_earliest_vintage_v8.json")
V8_FINAL_VERDICTS = os.path.join(V8_RUN_CONTROL,
                                 "p0_verdicts_final_v8.json")

#: Additional roots searched exhaustively for the pinned file name (all
#: READ-ONLY evidence areas).
EXTRA_SEARCH_ROOTS = (
    "/Users/hoangminhlong/my-quantitative/data_raw",
    "/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store/objects",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng1",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng2",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng3",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng4",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v8",
    "/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v9",
)

#: S0 window for realtime-coverage accounting (ng4 plane law).
S0_WINDOW = ("2018-04-04", "2025-04-30")


class EZCensusError(Exception):
    """Census bookkeeping error (fail-closed)."""


def _walk_match(root: str, file_name: str) -> list[str]:
    """Case-insensitive filename match under root (skips .git)."""
    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.lower() == file_name.lower():
                hits.append(os.path.join(dirpath, fn))
    return hits


def find_ez_bytes(vintaged_dir: str = V9_VINTAGED_DIR,
                  search_roots: Sequence[str] = EXTRA_SEARCH_ROOTS,
                  ) -> dict:
    """Exhaustive byte search for the pinned EZ vintaged file."""
    pinned_dir_listing = sorted(
        fn for fn in os.listdir(vintaged_dir)
        if fn.endswith(".json")) if os.path.isdir(vintaged_dir) else None
    in_pinned_dir = (pinned_dir_listing is not None
                     and EZ_SERIES_FILE in pinned_dir_listing)
    elsewhere: list[str] = []
    for root in search_roots:
        if os.path.exists(root):
            elsewhere.extend(_walk_match(root, EZ_SERIES_FILE))
    elsewhere = sorted(set(elsewhere))
    return {
        "series_file": EZ_SERIES_FILE,
        "pinned_vintaged_dir": vintaged_dir,
        "pinned_dir_listing": pinned_dir_listing,
        "in_pinned_vintaged_dir": in_pinned_dir,
        "matches_elsewhere": elsewhere,
        "bytes_resolvable": in_pinned_dir or bool(elsewhere),
        "search_law": ("exhaustive case-insensitive filename walk of the "
                       "pinned V9 vintaged dir + every READ-ONLY evidence "
                       "root (git dirs skipped); the manifest sha256 is "
                       "only verifiable against found bytes"),
    }


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def extract_v8_derived_evidence(
        staged_manifest_path: str = V8_STAGED_MANIFEST,
        dense_map_path: str = V8_DENSE_MAP_R2,
        earliest_path: str = V8_EARLIEST_VINTAGE,
        final_verdicts_path: str = V8_FINAL_VERDICTS,
        s0_window: tuple[str, str] = S0_WINDOW) -> dict:
    """Pull the committed V8 DERIVED evidence for the EZ series.

    Everything here was computed by V8 at ITS measurement time from bytes
    that are no longer resolvable: it is evidence ABOUT the archive, not
    a re-measurement (labeled as such everywhere it is recorded).
    """
    manifest = _load_json(staged_manifest_path)
    entry = manifest.get("series", {}).get(EZ_SERIES_ID)
    if entry is None:
        raise EZCensusError(
            f"{EZ_SERIES_ID} missing from the V8 staged manifest")
    dense = _load_json(dense_map_path)
    dz = dense.get("series", {}).get(EZ_SERIES_ID, {})
    earliest = _load_json(earliest_path).get(EZ_SERIES_ID, {})
    verdict_row = None
    for row in _load_json(final_verdicts_path).get("final_verdicts", []):
        if row.get("series") == EZ_SERIES_ID:
            verdict_row = row
            break
    lag_samples = dz.get("lag_samples", [])
    in_s0 = [
        s for s in lag_samples
        if s0_window[0] <= str(s.get("first_available")) <= s0_window[1]]
    return {
        "label": ("COMMITTED V8 DERIVED STATS -- recorded by V8 at its "
                  "measurement time; NOT a re-measurement on bytes and "
                  "never usable as a floor PASS"),
        "v8_staged_manifest_entry": {
            "file": entry.get("file"),
            "sha256": entry.get("sha256"),
            "binding_rows": entry.get("binding_rows"),
            "distinct_obs_dates": entry.get("distinct_obs_dates"),
            "obs_first": entry.get("obs_first"),
            "obs_last": entry.get("obs_last"),
            "retrieval_window": manifest.get("retrieval", {}),
        },
        "v8_dense_map_r2": {
            "lag_samples": lag_samples,
            "lag_sample_count": len(lag_samples),
            "lag_samples_first_available_inside_s0": len(in_s0),
            "lag_days_range": (
                [min(s["lag_days"] for s in lag_samples),
                 max(s["lag_days"] for s in lag_samples)]
                if lag_samples else None),
            "revision_samples": dz.get("revision_samples", []),
            "recorded_errors": dz.get("errors", []),
        },
        "v8_earliest_vintage": earliest,
        "v8_final_verdict_row": verdict_row,
        "v8_claim_being_remeasured": (
            (verdict_row or {}).get("s0_funding")
            or "row not found in p0_verdicts_final_v8.json"),
    }


def ez_census_decision(
        byte_search: Mapping,
        v8_derived: Mapping,
        current_vintage_search: Mapping,
        us_side_context: Mapping | None = None,
        ) -> dict:
    """The fail-closed census decision from the measured inputs.

    ``current_vintage_search`` must carry ``bytes_resolvable`` (a DOI
    current-vintage file search) -- when False the RETROSPECTIVE_ONLY
    fallback is itself NOT_RUN.
    """
    bytes_ok = bool(byte_search.get("bytes_resolvable"))
    current_ok = bool(current_vintage_search.get("bytes_resolvable"))
    problems: list[str] = []
    if not bytes_ok:
        problems.append(
            f"vintaged EZ HICP bytes ({EZ_SERIES_FILE}) are NOT in the "
            "pinned set: the V8 staged-manifest sha256 entry "
            f"{(v8_derived.get('v8_staged_manifest_entry') or {}).get('sha256')} "
            "cannot be verified against any resolvable bytes (exhaustive "
            "search recorded); every PIT/vintage measurement on EZ is "
            "NOT_RUN; EZ vintaged ingest needs an owner / A3-lane "
            "decision")
    if not current_ok:
        problems.append(
            "no current-vintage DOI file for the EZ series is resolvable "
            "either: the RETROSPECTIVE_ONLY fallback measurement is "
            "NOT_RUN (honest, not skipped silently)")
    floors = {
        "a4_ez_print_events": {
            "measured": None, "floor": EZ_PRINT_EVENT_FLOOR,
            "verdict": "NOT_RUN",
            "law": "EZ print events with full realtime availability "
                   "windows inside S0 (ng2/ng3 restricted first-print "
                   "standard); requires vintaged bytes"},
        "a5_ez_us_differential_months": {
            "measured": None, "floor": EZ_US_DIFFERENTIAL_FLOOR,
            "verdict": "NOT_RUN",
            "law": "obs months carrying BOTH an EZ restricted event and "
                   "a US restricted event (US leg measurable on pinned "
                   "bytes; EZ leg requires vintaged bytes)"},
    }
    status = "VINTAGED_BYTES_NOT_IN_PINNED_SET" if not bytes_ok else "MEASURABLE"
    if current_ok and not bytes_ok:
        status = "RETROSPECTIVE_ONLY_POSSIBLE"   # measured by the caller
    return {
        "series_identification": {
            "ez_series_id": EZ_SERIES_ID,
            "ez_series_kind": EZ_SERIES_KIND,
            "dispatch_suggested_series_id": DISPATCH_SUGGESTED_SERIES_ID,
            "dispatch_id_correction": (
                f"{DISPATCH_SUGGESTED_SERIES_ID} appears in NO manifest "
                "or census artifact anywhere in the repo (measured); the "
                "EZ HICP series the V8 evidence pinned and the ng4 plane "
                f"needs is {EZ_SERIES_ID}"),
        },
        "bytes_search": dict(byte_search),
        "v8_derived_evidence": dict(v8_derived),
        "current_vintage_search": dict(current_vintage_search),
        "floors": floors,
        "us_side_context": dict(us_side_context or {}),
        "status": status,
        "blockers": problems,
        "verdict": "BLOCKED_DATA" if problems else "MEASURABLE",
        "decision_law": (
            "mission invariant: missing evidence is NOT_RUN, never an "
            "inferred PASS; the committed V8 derived stats are evidence "
            "ABOUT the lost archive (they motivate an ingest), never a "
            "floor PASS; EZ vintaged ingest needs an owner / A3-lane "
            "decision before any EZ lane can measure"),
    }


def find_current_vintage_doi(search_roots: Sequence[str] = (
        EXTRA_SEARCH_ROOTS + (V9_VINTAGED_DIR,)),
        series_id: str = EZ_SERIES_ID) -> dict:
    """Search for any current-vintage (non-vintaged archive) file for the
    EZ series (a DOI/FRED current snapshot); used only to decide whether
    a RETROSPECTIVE_ONLY measurement is even possible."""
    hits: list[str] = []
    for root in search_roots:
        if os.path.exists(root):
            hits.extend(_walk_match(root, f"{series_id}.json"))
    return {
        "series_file": f"{series_id}.json",
        "matches": sorted(set(hits)),
        "bytes_resolvable": bool(hits),
        "law": ("current-vintage bytes may be measured "
                "RETROSPECTIVE_ONLY (disclosed as unsuitable for PIT "
                "decisions); absence makes even that fallback NOT_RUN"),
    }
