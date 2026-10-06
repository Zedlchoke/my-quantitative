"""HDD/CDD population weights - PRE-DECLARATION (never tuned).

Defined BEFORE any analytical use per dispatch invariant:
"HDD/CDD weights defined BEFORE any use, never tuned on PnL."

Weighting scheme (fixed ex ante, 2026-10-02, by NONPRICE-DATA-ACQUISITION):
- Unit of aggregation: NOAA climate division (NClimDiv), CONUS.
- State population shares: US Census resident population, 2010 Decennial +
  2020 Decennial (the two census anchors spanning the window); a series year
  uses the NEAREST PRIOR census anchor (2010 for 2010-2019, 2020 for 2020+)
  -> knowable in real time, never revised by later census.
- Within-state equal division weighting (division populations are not in the
  NClimDiv files); this coarse scheme is DECLARED and fixed.
- HDD = max(0, 65 - Tmean_F); CDD = max(0, Tmean_F - 65), monthly mean-temp
  basis from climdiv-tavg (monthly approximation disclosed: daily station
  aggregation would be finer; the declared scheme uses the official NClimDiv
  monthly divisional means).

NO parameter in this file may be changed after any hypothesis result is
computed with it (frozen-by-declaration).
"""

# Census 2010/2020 resident population by state (US Census, public domain).
# Sourced values are loaded at normalize time from noaa/ncei state-code
# mapping + a fixed census table; the mapping below is state FIPS -> (name).
STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}

# Census resident population (thousands), 2010 Decennial (April 1, 2010) and
# 2020 Decennial (April 1, 2020), by state FIPS. Source: US Census Bureau
# decennial counts (public). Values below are the official apportionment
# counts (2010) and 2020 redistricting counts (P.L. 94-171).
CENSUS_POP_THOUSANDS = {
    "2010": {
        "01": 4779736, "02": 710231, "04": 6392017, "05": 2915918,
        "06": 37253956, "08": 5029196, "09": 3574097, "10": 897934,
        "11": 601723, "12": 18801310, "13": 9687653, "15": 1360301,
        "16": 1567582, "17": 12830632, "18": 6483802, "19": 3046355,
        "20": 2853118, "21": 4339367, "22": 4533372, "23": 1328361,
        "24": 5773552, "25": 6547629, "26": 9883640, "27": 5303925,
        "28": 2967297, "29": 5988927, "30": 989415, "31": 1826341,
        "32": 2700551, "33": 1316470, "34": 8791894, "35": 2059179,
        "36": 19378102, "37": 9535483, "38": 672591, "39": 11536504,
        "40": 3751351, "41": 3831074, "42": 12702379, "44": 1052567,
        "45": 4625364, "46": 814180, "47": 6346105, "48": 25145561,
        "49": 2763885, "50": 625741, "51": 8001024, "53": 6724540,
        "54": 1852994, "55": 5686986, "56": 563626,
    },
    "2020": {
        "01": 5024279, "02": 733391, "04": 7151502, "05": 3011524,
        "06": 39538223, "08": 5773714, "09": 3605944, "10": 989948,
        "11": 689545, "12": 21538187, "13": 10711908, "15": 1455271,
        "16": 1839106, "17": 12812508, "18": 6785528, "19": 3190369,
        "20": 2937880, "21": 4505836, "22": 4657757, "23": 1362359,
        "24": 6177224, "25": 7029917, "26": 10077331, "27": 5706494,
        "28": 2961279, "29": 6154913, "30": 1084225, "31": 1961504,
        "32": 3104614, "33": 1377529, "34": 9288994, "35": 2117522,
        "36": 20201249, "37": 10439388, "38": 779094, "39": 11799448,
        "40": 3959353, "41": 4237256, "42": 13002700, "44": 1097379,
        "45": 5118425, "46": 886667, "47": 6910840, "48": 29145505,
        "49": 3271616, "50": 643077, "51": 8631393, "53": 7705281,
        "54": 1793716, "55": 5893718, "56": 576851,
    },
}


def census_anchor_for_year(year: int) -> str:
    """Nearest PRIOR census anchor (real-time knowable, revision-free)."""
    return "2010" if year < 2020 else "2020"


def state_weight(state_fips: str, year: int) -> float:
    pop = CENSUS_POP_THOUSANDS[census_anchor_for_year(year)][state_fips]
    total = sum(CENSUS_POP_THOUSANDS[census_anchor_for_year(year)].values())
    return pop / total
