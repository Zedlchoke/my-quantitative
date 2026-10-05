"""priors.py — PIPE lane recorder, cycle NFL-WINPROB-NG-SCORED-V1.

C3 boundary priors for the recorder state-carry law.

The SELECTION caps are permanent (lanes/T_SELECT arms.py: SEASON_MAX_GAMES=2018,
SEASON_MAX_PBP=2017) and are NOT touched. The RECORDER is a separate consumer
with its own load law (FREEZE_ERRATUM_R2, STATE-CARRY): it builds prior-season
EPA z values for target seasons 2019-2026 from prior-season REG pbp 2018-2025,
on top of the TRAIN-era priors 2001-2018 from pbp 2000-2017 (frozen A_DATA
manifest). The pbp files are STATE-CARRY INPUTS — pinned, read-only.

Frozen-code reuse (dispatch law: import, do not copy-fork; document any
unavoidable copy):
  - z standardization IS the frozen function: arms.z_standardize (population sd,
    ddof=0, across the lineages present in the prior season) — imported and
    called, never re-implemented.
  - The per-season E aggregation below MIRRORS the inner loop of the frozen
    arms.build_z_table (lanes/T_SELECT/arms.py, lines 383-403: REG rows only,
    both team attributions present and in LINEAGE_ALL, epa non-null;
    off_pp = sum(epa)/count over posteam; def_pp = -sum(epa)/count over
    defteam; E = 0.5*(off_pp + def_pp)). A direct call is impractical because
    the frozen function hard-caps its season loop at SEASON_MAX_PBP=2017
    (selection law) and takes a single directory. The recorder's loop is the
    minimal extension (season range 2000..2025, multi-directory lookup); the
    formula itself is transcribed 1:1 from those lines, and standardization is
    delegated to the frozen function.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

# Synthetic prior-table schema (e2e fixtures only — pbp-free z inputs)
PRIOR_E_TABLE_SCHEMA = "nfl_ng_scored_v1_prior_e_table@1"


def pbp_path_for(pbp_dirs, year: int) -> Path:
    """First-hit directory lookup: raw_pbp_2000_2017 -> raw_pbp_2018_2020 -> archive."""
    for d in pbp_dirs:
        p = Path(d) / f"play_by_play_{year}.parquet"
        if p.is_file():
            return p
    raise FileNotFoundError(f"no pbp parquet for season {year} in {list(map(str, pbp_dirs))}")


def verify_pbp_pins(frozen, dirs, seasons_2000_2017: bool = True) -> dict:
    """Pin verification over the state-carry pbp inputs (loud mismatch = stop).
    2018-2025 against the PIPE pins; 2000-2017 against the A_DATA binding
    manifest (provenance/pbp_download_log.tsv)."""
    import hashlib

    def sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    checked = {}
    for year, pin in {**frozen.PBP_2018_2020_SHA256, **frozen.PBP_2021_2025_SHA256}.items():
        p = pbp_path_for(dirs, year)
        got = sha(p)
        if got != pin:
            raise RuntimeError(f"pbp {year} pin violated: {got} != {pin}; STOP")
        checked[year] = got
    if seasons_2000_2017:
        with open(frozen.PBP_2000_2017_MANIFEST_TSV) as f:
            for row in csv.DictReader(f, delimiter="\t"):
                year = int(row["season"])
                p = pbp_path_for(dirs, year)
                got = sha(p)
                if got != row["sha256"]:
                    raise RuntimeError(f"pbp {year} A_DATA pin violated: {got}; STOP")
                checked[year] = got
    return checked


def _season_E(tbl) -> dict:
    """Per-season E map — E_i = 0.5*(off EPA/play + def EPA-allowed/play) over
    REG plays with both attributions set and epa non-null.

    MIRRORS lanes/T_SELECT/arms.py::build_z_table lines 383-403 (see module
    docstring; formula transcribed 1:1, loop restructured for the recorder's
    extended season range / multi-directory inputs).
    """
    reg = tbl[tbl["season_type"] == "REG"]
    pt = reg["posteam"].astype("string")
    dt_ = reg["defteam"].astype("string")
    m = reg[
        pt.notna() & (pt.str.strip() != "") & pt.isin(_LINEAGE_ALL)
        & dt_.notna() & (dt_.str.strip() != "") & dt_.isin(_LINEAGE_ALL)
        & reg["epa"].notna()
    ]
    off = m.groupby(m["posteam"], observed=True)["epa"].agg(["sum", "count"])
    dfn = m.groupby(m["defteam"], observed=True)["epa"].agg(["sum", "count"])
    E = {}
    for lg in set(off.index) | set(dfn.index):
        o = off.loc[lg]
        off_pp = float(o["sum"]) / float(o["count"])
        if lg in dfn.index and float(dfn.loc[lg, "count"]) > 0:
            d = dfn.loc[lg]
            def_pp = -float(d["sum"]) / float(d["count"])
        else:
            def_pp = 0.0
        E[lg] = 0.5 * (off_pp + def_pp)
    return E


_LINEAGE_ALL = None  # set by build_z_table_real from the frozen module


def build_z_table_real(arms, pbp_dirs, first_season: int = 2000, last_season: int = 2025):
    """z table for target seasons first+1 .. last+1 from prior-season REG pbp.

    Reads ONLY the 5 aggregation columns; asserts each file's `season` values
    equal the filename year (stale/foreign file = loud stop). Standardization
    is the frozen arms.z_standardize. No probabilities are produced here.
    Returns (z_table, z_entries_per_target_season).
    """
    import pyarrow.parquet as pq

    global _LINEAGE_ALL
    _LINEAGE_ALL = set(arms.LINEAGE_ALL)
    per_season: dict[int, dict] = {}
    for year in range(first_season, last_season + 1):
        path = pbp_path_for(pbp_dirs, year)
        tbl = pq.read_table(
            str(path), columns=["season", "season_type", "posteam", "defteam", "epa"]
        ).to_pandas()
        seasons_in_file = set(tbl["season"].unique().tolist())
        if seasons_in_file != {year}:
            raise RuntimeError(f"pbp {path} carries seasons {sorted(seasons_in_file)} != {{{year}}}; STOP")
        per_season[year] = _season_E(tbl)
    z_table: dict[tuple[int, str], float] = {}
    per_target: dict[int, int] = {}
    for s in range(first_season + 1, last_season + 2):
        zs = arms.z_standardize(per_season.get(s - 1, {}))
        per_target[s] = len(zs)
        for lg, z in zs.items():
            z_table[(s, lg)] = z
    return z_table, per_target


def load_prior_e_table(path):
    """Synthetic pbp-free prior table (e2e fixtures): {"<target_season>":
    {"<lineage>": E_value}} — E values standardized by the FROZEN
    arms.z_standardize at synthesis time (see synthesize_z_table)."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema") != PRIOR_E_TABLE_SCHEMA:
        raise ValueError(f"prior table schema {doc.get('schema')!r} != {PRIOR_E_TABLE_SCHEMA}")
    return {int(s): {lg: float(v) for lg, v in m.items()} for s, m in doc["entries"].items()}


def synthesize_z_table(arms, prior_e: dict[int, dict]):
    """{target_season: E map} -> {(season, lineage): z} via the frozen
    arms.z_standardize (the exact standardization the real path uses)."""
    z_table = {}
    per_target = {}
    for s in sorted(prior_e):
        zs = arms.z_standardize(prior_e[s])
        per_target[s + 1] = len(zs)
        for lg, z in zs.items():
            z_table[(s + 1, lg)] = z
    return z_table, per_target
