#!/usr/bin/env python
"""Lane FX-JA-READINESS — session/holiday hole census for the readiness cells:
6J missing weekday sessions in 2023, and 6A weekday coverage of Mar/Jun 2023.
Raw-panel union per CT trade date (any 6J / 6A symbol counts). No PnL.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_ja_lib import OUTRIGHT_RE, add_session, jdump, load_slice  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))


def weekday_sessions(symbol: str, roots: list[str], t0: str, t1: str) -> dict:
    df = load_slice(roots, t0, t1, OUTRIGHT_RE[symbol])
    df = add_session(df)
    have = sorted({d for d in df["session_date"].unique()})
    have_set = set(have)
    alldays = pd.bdate_range(t0, t1)  # Mon-Fri calendar
    missing = [d.date() for d in alldays if d.date() not in have_set
               and d <= pd.Timestamp(have[-1])]
    # group missing into runs with weekday names
    miss = [{"date": str(d), "weekday": d.strftime("%a")} for d in missing]
    return {
        "symbol": symbol,
        "window": [t0, t1],
        "n_traded_weekday_sessions": len(have),
        "first_session": str(have[0]), "last_session": str(have[-1]),
        "n_missing_weekdays": len(miss),
        "missing_weekdays": miss,
    }


if __name__ == "__main__":
    out = {
        "schema": "fx_ja_session_holes@1",
        "task": "FUTURES-SIX-READINESS-20261004 / FX-JA-READINESS (session/holiday cells)",
        "note": ("raw-panel union per CT trade date; a weekday with zero bars "
                 "in ANY 6J/6A symbol = exchange-level absence (holiday or "
                 "chain artifact)"),
        "6J_2023": weekday_sessions("6J", ["AV1R-O1M-6J-BACKFILL"],
                                    "2023-01-01", "2023-12-31"),
        "6A_Mar_Jun_2023": {
            "March_2023": weekday_sessions("6A", ["AV1R-O1M-6A-BACKFILL"],
                                           "2023-03-01", "2023-03-31"),
            "June_2023": weekday_sessions("6A", ["AV1R-O1M-6A-BACKFILL"],
                                          "2023-06-01", "2023-06-30"),
        },
    }
    jdump(out, os.path.join(OUT, "session_holes_2023.json"))
