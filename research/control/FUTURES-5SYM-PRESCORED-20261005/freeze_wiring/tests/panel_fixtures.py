"""panel_fixtures — deterministic synthetic panels for the wiring proofs.

Everything here is engineered synthetic data (SYNTHETIC provenance); no real
market data is touched anywhere (PREP-only round). Shapes mirror the adapter
lanes' own fixture kits:
  adapt_nq/synthetic_panel@1   (CT-stamped 1m bars, 0.25 grid)
  adapt_fx_ja/synthetic_panel@1 (UTC-stamped 1m bars, JST window bucketing)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
JST = ZoneInfo("Asia/Tokyo")
UTC = timezone.utc


def _weekdays(start: str, n: int) -> list[str]:
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


# ------------------------------------------------------------------ NQ panel

def nq_session_bar(session_date: str, hh: int, mm: int, o: float, h: float,
                   lo: float, c: float, contract: str) -> dict:
    dt = datetime.fromisoformat(session_date).replace(
        hour=hh, minute=mm, tzinfo=CT)
    return {"ts": dt.isoformat(), "open": o, "high": h, "low": lo, "close": c,
            "volume": 8_000, "session_date": session_date,
            "contract": contract}


def nq_session_agg(session_date: str, *, open_: float, high: float, low: float,
                   close: float, last_bar_ct: str = "15:59",
                   contract: str = "NQM3_2023") -> dict:
    return {"session_date": session_date, "open": open_, "high": high,
            "low": low, "close": close, "volume": 250_000,
            "rth_core_coverage": 1.0, "last_bar_ct": last_bar_ct,
            "contract": contract}


def build_nq_panel() -> tuple[dict, dict]:
    """UP + DN FOMC-14:00ET sessions on a 60-point-ATR warmup (ATR(20)=60.0).

    UP session 2023-06-14: anchor 13:00 o 15000.00 c 15006.00 (tail UP);
      13:01..15:58 flat 15010.00; last bar 15:59 o 15010 c 15050.
    DN session 2023-07-26: anchor 13:00 o 15000.00 c 14994.00 (tail DN);
      13:01..15:58 flat 14990.00; last bar 15:59 o 14990 c 14950.
    """
    contract = "NQM3_2023"
    warm = _weekdays("2023-05-15", 66)
    sessions = [nq_session_agg(s, open_=14900.0, high=14930.0, low=14870.0,
                               close=14900.0, contract=contract)
                for s in warm]
    bars: list[dict] = []
    up_day, dn_day = "2023-06-14", "2023-07-26"
    sessions.append(nq_session_agg(up_day, open_=15000.0, high=15050.0,
                                   low=15000.0, close=15050.0,
                                   contract=contract))
    sessions.append(nq_session_agg(dn_day, open_=15000.0, high=15000.0,
                                   low=14950.0, close=14950.0,
                                   contract=contract))
    for day, anchor_c, flat, final_c in ((up_day, 15006.00, 15010.00, 15050.00),
                                         (dn_day, 14994.00, 14990.00, 14950.00)):
        bars.append(nq_session_bar(day, 13, 0, 15000.00,
                                   max(15000.00, anchor_c),
                                   min(15000.00, anchor_c), anchor_c, contract))
        for m in range(13 * 60 + 1, 15 * 60 + 58):
            hh, mm = divmod(m, 60)
            bars.append(nq_session_bar(day, hh, mm, flat, flat, flat, flat,
                                       contract))
        bars.append(nq_session_bar(day, 15, 59, flat, max(flat, final_c),
                                   min(flat, final_c), final_c, contract))
    sessions.sort(key=lambda s: s["session_date"])
    bars.sort(key=lambda b: b["ts"])
    panel = {"schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
             "contract": contract, "symbol": "NQ",
             "sessions": sessions, "bars": bars}
    calendar = {"fomc_statements": [
        {"date": up_day, "time_et": "14:00",
         "statement_file": "monetary20230614a.htm"},
        {"date": dn_day, "time_et": "14:00",
         "statement_file": "monetary20230726a.htm"}]}
    return panel, calendar


# ------------------------------------------------------------------ 6J panel

def jst_bar(session_date: str, hh: int, mm: int, o: float, h: float, lo: float,
            c: float, contract: str) -> dict:
    d = date.fromisoformat(session_date)
    dt = datetime(d.year, d.month, d.day, hh, mm, tzinfo=JST).astimezone(UTC)
    return {"ts": dt.isoformat(), "open": o, "high": h, "low": lo, "close": c,
            "volume": 1_000, "session_date": session_date,
            "contract": contract}


def build_6j_panel() -> tuple[dict, dict]:
    """21 MPM event sessions (window range 0.000050 -> window ATR(20) equal)
    + one non-event session. The FINAL event session is the yen-STRENGTHENING
    UP window: 12:00 JST open 0.006500 -> 15:29 JST close 0.006550; entry
    15:30 JST bar open 0.006550; flat to 16:29; last bar 16:30 close 0.006575.

    6J quote law: USD per JPY — a RISING quoted number = yen STRONG; a long
    (DRIFT-UP) must book POSITIVE PnL on this panel (T18-class sign proof).
    """
    contract = "6JZ3_2023"
    day0 = date(2023, 9, 4)   # Monday
    event_days = []
    d = day0
    while len(event_days) < 21:
        if d.weekday() < 5:
            event_days.append(d.isoformat())
        d += timedelta(days=1)
    non_event_day = (date.fromisoformat(event_days[-1]) + timedelta(days=1))
    while non_event_day.weekday() >= 5:
        non_event_day += timedelta(days=1)
    non_event_day = non_event_day.isoformat()

    sessions, bars = [], []
    up_day = event_days[-1]

    def add_session(day: str, *, w_open: float, w_close: float, entry_px: float,
                    last_o: float, last_c: float, is_event: bool) -> None:
        sessions.append({
            "session_date": day,
            "open": w_open, "high": max(w_open, w_close), "low": min(w_open, w_close),
            "close": last_c, "volume": 10_000, "rth_core_coverage": 1.0,
            "last_bar_utc": jst_bar(day, 16, 30, last_o, max(last_o, last_c),
                                    min(last_o, last_c), last_c,
                                    contract)["ts"],
            "window_ranges": {"mpm": round(abs(w_close - w_open), 10)},
            "contract": contract})
        if day not in (up_day, non_event_day):
            return  # aggregate-only sessions (window ATR history)
        bars.append(jst_bar(day, 12, 0, w_open, max(w_open, w_open),
                            w_open, w_open, contract))
        # flat window interior to the window-close bar
        bars.append(jst_bar(day, 15, 29, w_close - 0.000025, w_close,
                            w_close - 0.000025, w_close, contract))
        for m in range(15 * 60 + 30, 16 * 60 + 30):
            hh, mm = divmod(m, 60)
            bars.append(jst_bar(day, hh, mm, entry_px, entry_px, entry_px,
                                entry_px, contract))
        bars.append(jst_bar(day, 16, 30, last_o, max(last_o, last_c),
                            min(last_o, last_c), last_c, contract))

    for day in event_days[:-1]:
        # prior events carry a +0.000050 window range (window ATR(20) law)
        add_session(day, w_open=0.006500, w_close=0.006550, entry_px=0.006500,
                    last_o=0.006500, last_c=0.006500, is_event=True)
    # the yen-strengthening UP window session
    add_session(up_day, w_open=0.006500, w_close=0.006550, entry_px=0.006550,
                last_o=0.006550, last_c=0.006575, is_event=True)
    # one non-event session (flat window; controls route here)
    add_session(non_event_day, w_open=0.006500, w_close=0.006500,
                entry_px=0.006500, last_o=0.006500, last_c=0.006500,
                is_event=False)

    panel = {"schema": "adapt_fx_ja/synthetic_panel@1", "provenance": "SYNTHETIC",
             "symbol": "6J", "contract": contract,
             "sessions": sessions, "bars": bars}
    calendar = {"boj_mpm_dates": list(event_days)}
    return panel, calendar


# 6J compiled cost law (COST_CONTRACT_6J_6A s.1/s.3 constants; MODELED labels)
COST_LAW_6J = {"fee_all_in_usd": 2.46, "spread_usd": 25.00,
               "slip_usd_by_tier": {"S1": 6.25, "S2": 12.50, "S3": 18.75}}
