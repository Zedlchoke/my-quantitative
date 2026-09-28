#!/usr/bin/env python
"""Generate the tiny synthetic fixtures under tests/fixtures/.

Idempotent: re-running rewrites identical bytes. The generation rules are
closed-form so tests can re-derive expected OHLC values independently:

  scale = 1e5 (EURUSD points). For a minute m (minute-of-day):
      p(m)      = 119000 + m                  (bid open, integer points)
      bid:  o=p, c=p+1, low=p-1, high=p+2, vol=10.0
      ask:  o=p+2, c=p+3, low=p+1, high=p+4   (constant 2-point spread)
  Zero-volume "flat" minute (tests the tradable flag): 12:00 on 2021-11-07
  gets o=c=l=h=p, vol=0 on BOTH sides.

Fixture corpus layout (consumed via load_fx_m1(root=...)):

  bi5/EURUSD/M1/BID/2021-03-14.bi5   23 hours (02:00 hour absent — DST day)
  bi5/EURUSD/M1/ASK/2021-03-14.bi5
  bi5/EURUSD/M1/BID/2021-11-07.bi5   24 hours + one flat minute
  bi5/EURUSD/M1/ASK/2021-11-07.bi5
  bi5/EURUSD/M1/BID/2021-11-08.bi5   1 hour (00:00 only -> 25h span with 11-07)
  bi5/EURUSD/M1/ASK/2021-11-08.bi5
"""

import lzma
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")

SCALE = 100000  # EURUSD points per price unit


def build_side_day(minutes: set[int], side: str, flat_minutes: frozenset = frozenset()) -> bytes:
    recs = []
    for m in sorted(minutes):
        sec = m * 60
        p = 119000 + m
        flat = m in flat_minutes
        if flat:
            bid = (p, p, p, p)
            ask = (p + 2, p + 2, p + 2, p + 2)
            vol = 0.0
        else:
            bid = (p, p + 1, p - 1, p + 2)
            ask = (p + 2, p + 3, p + 1, p + 4)
            vol = 10.0
        o, c, lo, hi = bid if side == "BID" else ask
        recs.append(struct.pack(">5if", sec, o, c, lo, hi, vol))
    return lzma.compress(b"".join(recs))


def hour(h: int) -> set[int]:
    return set(range(h * 60, (h + 1) * 60))


def main() -> None:
    # --- macro fixtures -----------------------------------------------------
    mac = os.path.join(FIX, "macro")
    os.makedirs(mac, exist_ok=True)
    with open(os.path.join(mac, "dgs10_mini.csv"), "w", encoding="utf-8") as fh:
        fh.write(
            "observation_date,DGS10\n"
            "2026-01-01,4.23\n"
            "2026-01-02,.\n"
            "2026-01-05,4.31\n"
        )
    with open(os.path.join(mac, "effr_mini.json"), "w", encoding="utf-8") as fh:
        fh.write(
            '{"refRates": [\n'
            '  {"effectiveDate": "2026-01-01", "percentRate": "4.33", "revisionIndicator": false},\n'
            '  {"effectiveDate": "2026-01-02", "percentRate": "4.30", "revisionIndicator": true},\n'
            '  {"effectiveDate": "2026-01-05", "percentRate": 4.29, "revisionIndicator": false}\n'
            "]}\n"
        )
    with open(os.path.join(mac, "bad_header.csv"), "w", encoding="utf-8") as fh:
        fh.write("date,value\n2026-01-01,4.23\n")
    with open(os.path.join(mac, "bad_value.csv"), "w", encoding="utf-8") as fh:
        fh.write("observation_date,DGS10\n2026-01-01,oops\n")
    with open(os.path.join(mac, "bad_effr.json"), "w", encoding="utf-8") as fh:
        fh.write('[{"effectiveDate": "2026-01-01", "revisionIndicator": false}]')

    # --- bi5 corpus fixtures ------------------------------------------------
    day_0314 = set().union(*[hour(h) for h in range(24)]) - hour(2)  # 23 hours
    day_1107 = set().union(*[hour(h) for h in range(24)])            # 24 hours
    day_1108 = hour(0)                                               # 1 hour
    flat = {12 * 60}  # 12:00 zero-volume flat minute on 2021-11-07

    for sym_dir, days, flats in (
        ("BID", {"2021-03-14": day_0314, "2021-11-07": day_1107, "2021-11-08": day_1108},
         {"2021-11-07": flat}),
        ("ASK", {"2021-03-14": day_0314, "2021-11-07": day_1107, "2021-11-08": day_1108},
         {"2021-11-07": flat}),
    ):
        d = os.path.join(FIX, "bi5", "EURUSD", "M1", sym_dir)
        os.makedirs(d, exist_ok=True)
        for name, minutes in days.items():
            payload = build_side_day(minutes, sym_dir, flats.get(name, frozenset()))
            with open(os.path.join(d, f"{name}.bi5"), "wb") as fh:
                fh.write(payload)
            print(f"wrote {d}/{name}.bi5 ({len(minutes)} minutes, {len(payload)} bytes)")

    # corrupt payload: LZMA-valid but length not a multiple of 24
    d = os.path.join(FIX, "bi5", "corrupt")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "not24.bi5"), "wb") as fh:
        fh.write(lzma.compress(b"\x00" * 7))

    print("fixtures written under", FIX)


if __name__ == "__main__":
    main()
