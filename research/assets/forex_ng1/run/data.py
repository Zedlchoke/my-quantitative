"""Pinned-input environment loader for the FOREX-NG1 I-phase runners.

Everything is VERIFY-ON-READ and fail-closed:

- announcement census      sha256-pinned (e8a35d23...);
- spot series              pin-manifest sha256 verify-on-read through
                           ``research.assets.forex_ng1.spot_series``;
- common grid              recomputed from the served calendars and
                           cross-checked against the committed grid census
                           (1842 days);
- vintaged CPI legs        consumed exactly as at D2: S2 manifest via the
                           plane adapter (CADS resolve verify-on-read) +
                           staged bytes verified against the manifest
                           pins; US leg via consume_via_plane;
- DGS10 control series     vintaged bytes pinned from V8 committed
                           evidence (see ``ctlpin``); the ctl pin manifest
                           is verified and then the bytes re-hashed.

The loader is injectable for tests: every root path can be overridden.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1 import plane_adapter as pa    # noqa: E402
from research.assets.forex_ng1.d2 import events as E         # noqa: E402
from research.assets.forex_ng1.d2.series import (            # noqa: E402
    ECONOMY_SERIES, VintagedSeries, parse_realtime_observations,
)
from research.assets.forex_ng1.spot_series import (          # noqa: E402
    S0_WINDOW_END, S0_WINDOW_START, common_weekday_grid,
    load_pin_manifest, resolve_all_pairs,
)

from research.assets.forex_ng1.run import config as C        # noqa: E402

#: READ-ONLY inherited staging (D2 lanes' own roots; never written).
DEFAULT_V9_ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/"
                   "forex-free-v9/integration")
DEFAULT_VINTAGED_DIR = os.path.join(DEFAULT_V9_ROOT,
                                    "data_raw/forex_free_v9_cpi")
DEFAULT_SCRATCH = "/tmp/forex_ng1_i_scratch"

#: Local untracked copies (never committed; data_raw/ is not gitignored
#: in this worktree, so raw bytes stay UNTRACKED by staging discipline).
DEFAULT_SPOT_DATA_DIR = os.path.join(REPO_ROOT, "data_raw/forex_ng1_spot")
DEFAULT_DGS10_PATH = os.path.join(REPO_ROOT, "data_raw/forex_ng1_ctl",
                                  "DGS10.json")
DEFAULT_CTL_PIN = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/i/ctl_dgs10_pin.json")
DEFAULT_GRID_CENSUS = os.path.join(
    REPO_ROOT, "research/control/forex_ng1_run/p1_spot/"
               "spot_grid_census.json")

DGS10_SHA256_PIN = ("03dde429ba022e6d011ae3a61323124e38c5a3fac"
                    "888b492823406a51c4c4aa0")

GRID_CENSUS_DAYS_PIN = 1842


class EnvError(Exception):
    """Fail-closed environment verification error."""


@dataclass
class RunEnv:
    """Everything a cell needs, with provenance for the dry-run report."""
    census: dict
    events: list                      # first releases, pit_notes excluded
    order_state: dict
    grid: list                        # common grid days (date)
    grid_index: dict                  # date -> index
    series_by_eco: dict               # economy -> VintagedSeries
    dgs10_rows: list                  # parsed realtime rows
    spot_sha256: dict
    provenance: dict = field(default_factory=dict)


def _resolve_spot_dir(spot_data_dir: str | None) -> str:
    if spot_data_dir is not None:
        return spot_data_dir
    if os.path.isdir(DEFAULT_SPOT_DATA_DIR) and all(
            os.path.exists(os.path.join(DEFAULT_SPOT_DATA_DIR, f))
            for f in ("GBPUSD.json", "USDCAD.json", "AUDUSD.json",
                      "NZDUSD.json")):
        return DEFAULT_SPOT_DATA_DIR
    manifest = load_pin_manifest(C.DEFAULT_PROPOSAL_PATHS and os.path.join(
        C.DEFAULT_CONTROL_DIR, "p1_spot/spot_pin_manifest.json"))
    first = next(iter(manifest["files"].values()))
    pinned_dir = os.path.dirname(first["copy_path_absolute"])
    if os.path.isdir(pinned_dir):
        return pinned_dir
    raise EnvError("no pinned spot bytes found (fail-closed)")


def load_env(census_path: str | None = None,
             spot_manifest_path: str | None = None,
             spot_data_dir: str | None = None,
             grid_census_path: str | None = None,
             vintaged_dir: str | None = None,
             scratch_dir: str | None = None,
             cads_root: str | None = None,
             dgs10_path: str | None = None,
             ctl_pin_path: str | None = None,
             verify_census_sha: bool = True) -> RunEnv:
    """Load and verify every pinned input.  ``verify_census_sha=False``
    exists ONLY for synthetic test fixtures."""
    census_path = census_path or os.path.join(
        C.DEFAULT_CONTROL_DIR, "p0_announcement_census.json")
    spot_manifest_path = spot_manifest_path or os.path.join(
        C.DEFAULT_CONTROL_DIR, "p1_spot/spot_pin_manifest.json")
    grid_census_path = grid_census_path or DEFAULT_GRID_CENSUS
    vintaged_dir = vintaged_dir or DEFAULT_VINTAGED_DIR
    scratch_dir = scratch_dir or DEFAULT_SCRATCH
    cads_root = cads_root or pa.DEFAULT_CADS_STORE_ROOT
    dgs10_path = dgs10_path or DEFAULT_DGS10_PATH
    ctl_pin_path = ctl_pin_path or DEFAULT_CTL_PIN
    prov: dict = {}

    # -- census ---------------------------------------------------------- #
    census = E.load_census(census_path, verify_sha=verify_census_sha)
    events = E.first_release_events(census)
    state = E.order_state(events)
    prov["census"] = {
        "path": census_path,
        "sha256": None if not verify_census_sha else E.CENSUS_SHA256_PIN,
        "first_release_events": len(events),
        "order_counts": state["counts"],
    }

    # -- spot + grid ------------------------------------------------------ #
    serieses = resolve_all_pairs(spot_manifest_path,
                                 _resolve_spot_dir(spot_data_dir))
    grid = common_weekday_grid(serieses, S0_WINDOW_START, S0_WINDOW_END)
    with open(grid_census_path, "r", encoding="utf-8") as fh:
        grid_census = json.load(fh)
    census_days = grid_census["common_grid"]["grid_days"]
    if len(grid) != census_days or census_days != GRID_CENSUS_DAYS_PIN:
        raise EnvError(
            f"grid recompute mismatch: {len(grid)} vs census "
            f"{census_days} (pin {GRID_CENSUS_DAYS_PIN})")
    prov["spot"] = {
        "manifest": spot_manifest_path,
        "data_dir": _resolve_spot_dir(spot_data_dir),
        "resolved_sha256": {p: s.sha256 for p, s in serieses.items()},
        "grid_days": len(grid),
    }

    # -- vintaged CPI legs (D2 consume path) ------------------------------ #
    registry = pa.load_registry()
    ga4 = pa.ga4_granted()
    s2_manifest = pa.consume_s2_manifest(cads_root, registry, ga4)
    local_paths = {
        rec["file"]: os.path.join(vintaged_dir, rec["file"])
        for rec in s2_manifest["series"].values()
        if rec["file"].startswith("fred_vintaged/")
    }
    us_entry = pa.consume_via_plane(
        registry, cads_root, "S3:forex-announcement-ledger",
        "US/fred_cpiaucsl_rt.json", scratch_dir, ga4)
    local_paths[s2_manifest["series"]["CPIAUCSL"]["file"]] = \
        us_entry.scratch_path
    verify = pa.verify_s2_files(s2_manifest, local_paths)
    failed = [k for k, v in verify.items() if not v["match"]]
    if failed:
        raise EnvError(f"vintaged leg sha mismatch: {failed}")
    series_by_eco: dict[str, VintagedSeries] = {}
    for eco, series_id in ECONOMY_SERIES.items():
        rel = s2_manifest["series"][series_id]["file"]
        path = (us_entry.scratch_path if rel.startswith("US/")
                else os.path.join(vintaged_dir, rel))
        with open(path, "rb") as fh:
            payload = json.load(fh)
        observations = (payload["observations"]
                        if isinstance(payload, dict) else payload)
        rows = parse_realtime_observations(observations)
        series_by_eco[eco] = VintagedSeries(series_id=series_id, rows=rows)
    prov["vintaged"] = {
        "s2_manifest_address": pa.S2_PINNED_ADDRESS,
        "staging_root": vintaged_dir,
        "spacing": {e: vs.spacing for e, vs in series_by_eco.items()},
        "us_leg": {"via": "consume_via_plane",
                   "query_verdict": us_entry.query_verdict},
    }

    # -- DGS10 control bytes ---------------------------------------------- #
    dgs_sha = C.sha256_file(dgs10_path)
    with open(ctl_pin_path, "r", encoding="utf-8") as fh:
        ctl_pin = json.load(fh)
    pinned = ctl_pin["dgs10"]["sha256"]
    if dgs_sha != pinned or pinned != DGS10_SHA256_PIN:
        raise EnvError(
            f"DGS10 bytes drift: {dgs_sha} != pin {pinned} "
            f"(canonical {DGS10_SHA256_PIN})")
    with open(dgs10_path, "rb") as fh:
        payload = json.load(fh)
    observations = (payload["observations"]
                    if isinstance(payload, dict) else payload)
    dgs10_rows = parse_realtime_observations(observations)
    prov["dgs10_ctl"] = {
        "path": dgs10_path,
        "sha256": dgs_sha,
        "ctl_pin": ctl_pin_path,
        "pin_manifest_sha256": ctl_pin["v8_staged_vintaged_manifest"][
            "sha256"],
        "rows": len(dgs10_rows),
    }

    return RunEnv(
        census=census, events=events, order_state=state, grid=grid,
        grid_index={d: i for i, d in enumerate(grid)},
        series_by_eco=series_by_eco, dgs10_rows=dgs10_rows,
        spot_sha256=prov["spot"]["resolved_sha256"], provenance=prov)
