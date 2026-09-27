"""R2-2 corporate-action (dividend / split) ex-date index.

Ex-dates come from the restored EODHD div/splits tables (field `date` =
ex-date on both tables, per lane_s measured schema).  File stems differ
from panel stems by letter case for 79 names (e.g. `EV_OLD2` vs
`EV_old2`), so resolution is case-insensitive; SPY (benchmark, not a
cohort member) has no div/splits file.
"""

from __future__ import annotations

import json
import os


class ExDateIndex:
    def __init__(self, div_dir: str, splits_dir: str):
        self.div_dir = div_dir
        self.splits_dir = splits_dir
        self._div_stems = {f[:-5].lower(): os.path.join(div_dir, f)
                           for f in os.listdir(div_dir) if f.endswith(".json")}
        self._split_stems = {f[:-5].lower(): os.path.join(splits_dir, f)
                             for f in os.listdir(splits_dir) if f.endswith(".json")}
        self._cache: dict[str, tuple[set[str], set[str]]] = {}

    def _lookup(self, stems: dict[str, str], ticker: str) -> str | None:
        want = ticker.lower()
        if want in stems:
            return stems[want]
        return None

    def ex_dates(self, ticker: str) -> tuple[set[str], set[str]]:
        """(dividend ex-dates, split ex-dates) for a panel ticker."""
        if ticker not in self._cache:
            divs: set[str] = set()
            splits: set[str] = set()
            p = self._lookup(self._div_stems, ticker)
            if p:
                with open(p) as fh:
                    divs = {r["date"] for r in json.load(fh)}
            p = self._lookup(self._split_stems, ticker)
            if p:
                with open(p) as fh:
                    splits = {r["date"] for r in json.load(fh)}
            self._cache[ticker] = (divs, splits)
        return self._cache[ticker]

    def contamination(self, ticker: str, start_date: str, end_date: str) -> dict:
        """R2-2 check: any div/split ex-date inside the inclusive window
        [start_date .. end_date] (calendar-interval compare, ex-dates need
        not be session dates themselves)."""
        divs, splits = self.ex_dates(ticker)
        hit_div = sorted(d for d in divs if start_date <= d <= end_date)
        hit_split = sorted(d for d in splits if start_date <= d <= end_date)
        return {
            "contaminated": bool(hit_div or hit_split),
            "div_ex_dates": hit_div,
            "split_ex_dates": hit_split,
        }
