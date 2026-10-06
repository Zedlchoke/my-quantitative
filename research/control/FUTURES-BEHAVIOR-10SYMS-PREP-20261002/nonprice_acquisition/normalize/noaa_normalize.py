"""NOAA normalizer -> observed weather tidy + issued-forecast inventory.

1) climdiv observed monthly divisional temps (tavg/tmax/tmin) -> tidy with
   HDD/CDD derived using normalize/hdd_cdd_weights.py (PRE-DECLARED census
   weights; never tuned). OBSERVED data is outcome/regime context ONLY -
   never an entry feature (dispatch PIT law).
2) CPC issued 6-10/8-14 temp forecast zips -> inventory table: file, issue
   date (= issued_at), size, sha. ISSUED forecasts live in a SEPARATE table
   from observed (mandatory). Shapefile value extraction (probability grids)
   is follow-on typed work; the vintage structure (issue dates) is proven by
   the file set.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from hdd_cdd_weights import STATE_FIPS, state_weight

RAW = Path("/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms")
OUT = RAW / "normalized"


def _sha(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def parse_climdiv(fname: str, element: str) -> list[dict]:
    p = RAW / "noaa/ncei" / fname
    if not p.exists():
        return []
    rows = []
    prov = _sha(p)
    for line in p.read_text(errors="replace").splitlines():
        # format: state-div-elem-year block of 12 monthly values (fixed width)
        m = re.match(r"^\s*(\d{3})(\d{2})(\d{4})(\d{2})(.*)$", line)
        if not m:
            continue
        state, div, year, month, rest = m.groups()
        if state not in STATE_FIPS:
            continue
        val = float(rest[:6]) / 100.0 if rest[:6].strip() and rest[:6] != "-9999" and rest.strip() != "-99999" else None
        if val == -99.99:
            val = None
        rows.append({
            "series_id": f"NCLIMDIV_{element}",
            "observation_period": f"{year}-{month}-01",
            "state_fips": state,
            "state": STATE_FIPS[state],
            "division": int(div),
            "value_degF": val,
            "vintage_flag": "observed_latest_official",
            "provenance_sha256": prov,
        })
    return rows


def observed_hdd_cdd() -> None:
    """Official divisional HDD/CDD monthly files (climdiv-hddcdv / cddcdv).

    Format per line: 5-digit state-division code + 2-digit element + 4-digit
    year + 12 fixed-width monthly values (scaled x1 for degree days).
    tavg-derived approximation NOT used: NOAA publishes degree days directly.
    (tmax/tmin -inv variants skipped: >60MB station-inventory bundles, redundant.)
    """
    frames = []
    for pat, el in [("climdiv-hddcdv-v1.0.0-*", "HDD"), ("climdiv-cddcdv-v1.0.0-*", "CDD")]:
        cands = sorted((RAW / "noaa/ncei").glob(pat))
        if not cands:
            continue
        p = cands[-1]
        prov = _sha(p)
        rows = []
        for line in p.read_text(errors="replace").splitlines():
            # layout: state(2) division(3) element(1) year(4) then 12 x 5-wide values
            # (e.g. "0101251895" = state 01, division 012, element 5, year 1895)
            m = re.match(r"^\s*(\d{2})(\d{3})(\d{1})(\d{4})(.*)$", line)
            if not m:
                continue
            state, div, elem, year, rest = m.groups()
            if state not in STATE_FIPS:
                continue
            vals = [rest[i:i + 5] for i in range(0, 60, 5)]
            for i, v in enumerate(vals, start=1):
                try:
                    x = float(v)
                except ValueError:
                    continue
                if x == -99.99:
                    continue
                rows.append({
                    "series_id": f"NCLIMDIV_{el}",
                    "observation_period": f"{year}-{i:02d}-01",
                    "state_fips": state,
                    "state": STATE_FIPS[state],
                    "division": int(div),
                    "value": x,
                    "vintage_flag": "observed_official_noaa",
                    "provenance_sha256": prov,
                })
        frames.append(pd.DataFrame(rows))
    if not frames:
        print("no climdiv rows")
        return
    df = pd.concat(frames)
    # NOAA files carry the in-progress next month as preliminary - drop months
    # after the current month (2026-10) for the observed table (no future rows).
    df = df[df["observation_period"] <= "2026-10-01"]
    df["year"] = df["observation_period"].str[:4].astype(int)
    # PRE-DECLARED aggregation: census state weights (nearest prior census),
    # equal division weighting within state (see hdd_cdd_weights.py).
    ndiv = df.groupby("state")["division"].nunique()
    df["state_weight"] = df.apply(
        lambda r: state_weight(r["state_fips"], r["year"]) / ndiv[r["state"]], axis=1)
    df.to_parquet(OUT / "noaa_observed_divisions_tidy.parquet")
    agg = (df.assign(w=lambda d: d["state_weight"])
             .groupby("observation_period")
             .apply(lambda g: pd.Series({
                 "pop_weighted_hdd": g.loc[g["series_id"] == "NCLIMDIV_HDD", "value"].mul(g.loc[g["series_id"] == "NCLIMDIV_HDD", "w"]).sum(),
                 "pop_weighted_cdd": g.loc[g["series_id"] == "NCLIMDIV_CDD", "value"].mul(g.loc[g["series_id"] == "NCLIMDIV_CDD", "w"]).sum(),
             }), include_groups=False).reset_index())
    agg["series_id"] = "NCLIMDIV_POPWEIGHTED"
    agg["vintage_flag"] = "observed_official_weights_predeclared"
    agg["provenance_sha256"] = df["provenance_sha256"].iloc[0]
    agg.to_parquet(OUT / "noaa_observed_popweighted_hddcdd.parquet")
    print("observed division rows:", len(df), "agg months:", len(agg),
          agg["observation_period"].min(), "..", agg["observation_period"].max())


def issued_forecast_inventory() -> None:
    rows = []
    for sub, sid in [("noaa/cpc/610temp", "CPC_610DAY_TEMP_ISSUED"),
                     ("noaa/cpc/610temp_recent_weekly", "CPC_610DAY_TEMP_ISSUED_WEEKLY_SAMPLE"),
                     ("noaa/cpc/814temp_pilot", "CPC_814DAY_TEMP_ISSUED_PILOT")]:
        d = RAW / sub
        if not d.exists():
            continue
        for p in sorted(d.glob("*.zip")):
            m = re.search(r"(\d{8})", p.name)
            issue = (f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else None)
            rows.append({
                "series_id": sid,
                "observation_period": issue,  # issue date; valid window = issue+6..10 / +8..14
                "issued_at": issue,
                "valid_window": ("issue+6..10d" if "610" in sid else "issue+8..14d"),
                "vintage_flag": "issued_forecast_as_published",
                "file": p.name,
                "bytes": p.stat().st_size,
                "provenance_sha256": _sha(p),
            })
    if rows:
        df = pd.DataFrame(rows)
        df.to_parquet(OUT / "noaa_cpc_issued_forecast_inventory.parquet")
        print("issued forecast files:", len(df),
              df["issued_at"].min(), "..", df["issued_at"].max())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    observed_hdd_cdd()
    issued_forecast_inventory()


if __name__ == "__main__":
    main()
