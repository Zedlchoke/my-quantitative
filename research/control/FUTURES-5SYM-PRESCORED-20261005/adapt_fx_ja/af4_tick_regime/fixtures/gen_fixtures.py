"""gen_fixtures — AF4 tick-regime panels, 6A + same-date 6J control (synthetic).

Same date set on both symbols; engineered to reproduce the D-2 step-test
substrate at fixture scale:
  6A era-1 day (2020-06-02): 1e-04 grid, close-to-close step 1e-04 = $10.00
  6A era-2 day (2024-05-06): 5e-05 grid, close-to-close step 5e-05 = $5.00
    -> 6A USD-step ratio era2/era1 = 0.50 (ticks ratio 1.00)
  6J both days: constant 5e-07 grid, step 5e-07 = $6.25
    -> 6J USD-step ratio = 1.00 (the constant-tick control)
"""
from __future__ import annotations

import json
from pathlib import Path

import fx_common as fc
import fx_fixture_kit as kit

HERE = Path(__file__).resolve().parent
DATES = ["2020-06-02", "2024-05-06"]   # era-1 day + era-2 day (same-date set)


def build_panel(symbol: str) -> dict:
    bars, sessions = [], []
    for sd in DATES:
        if symbol == "6A":
            tick = fc.sixa_tick(sd)
            step = tick                       # close-to-close = 1 tick
            base = 0.6900 if fc.sixa_era_for_date(sd) == "era1" else 0.6700
            contract = "6AM0" if fc.sixa_era_for_date(sd) == "era1" else "6AM4"
        else:
            tick = fc.SIXJ_TICK
            step = tick
            base = 0.0065000
            contract = "6JM0" if sd == DATES[0] else "6JM4"
        day = kit.walk_session(sd, kit.at_local(sd, 0, 0, fc.JST),
                               kit.at_local(sd, 1, 0, fc.JST),
                               base, step, 100, contract, tick=tick)
        bars.extend(day)
        sessions.append(kit.session_agg(
            sd, open_=float(day[0]["open"]), high=max(float(b["high"]) for b in day),
            low=min(float(b["low"]) for b in day), close=float(day[-1]["close"]),
            volume=sum(int(b["volume"]) for b in day),
            last_bar_utc=day[-1]["ts"], contract=contract))
    return {
        "schema": "adapt_fx_ja/synthetic_panel@1",
        "provenance": "SYNTHETIC",
        "symbol": symbol,
        "family": "AF4",
        "contingency": "CONTINGENCY-PB3-PARK (SPEC_6A_CONTINGENCY banner)",
        "contract": {"tick_size": tick if symbol == "6A" else fc.SIXJ_TICK,
                     "multiplier": fc.SIXA_MULTIPLIER if symbol == "6A"
                     else fc.SIXJ_MULTIPLIER},
        "sessions": sessions,
        "bars": bars,
    }


def main() -> None:
    for symbol in ("6A", "6J"):
        panel = build_panel(symbol)
        name = "af4_panel_6a.json" if symbol == "6A" else "af4_panel_6j.json"
        with open(HERE / name, "w", encoding="utf-8") as fh:
            json.dump(panel, fh, indent=0)
        print(symbol, "bars", len(panel["bars"]), "sessions",
              len(panel["sessions"]))


if __name__ == "__main__":
    main()
