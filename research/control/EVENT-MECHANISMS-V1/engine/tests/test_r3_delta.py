"""E6(f) — r3-canonical delta tests (G3_FREEZE_ADDENDUM_r3 + D-1/D-2).

Covers the remediation laws:
- D-1  A2 entry = first session OPEN strictly after the acceptance instant
       (no A1-style direction session; direction_session null);
- D-2  div/split tables resolve case-insensitively (normalized stems);
- AMB-1  weekend acceptances are anchor members, stratum label WKND;
- AMB-6  unpriced A2 rows drop+count (no imputation — a2_inputs);
- AMB-7  unfillable EXIT rolls forward; exhaustion = last bar + delisting;
- AMB-9  fold assignment by ET-local acceptance date;
- AMB-11 direction tie => excluded + counted;
- AMB-15 CA window = full calendar interval [entry..exit] (ex-dates need
         not be session dates).
"""
import json
import math
from datetime import date, timedelta

import pytest

from emv1 import clock
from emv1 import config as C
from emv1.panel import NameSeries
from emv1.book import build_decision, corp_action_in_window, resolve_entry_open_anchored
from emv1.arms import build_a1_arms, ARM_DEFS
from emv1.loaders import load_corp_actions


def make_ns(ticker, d0, d1, open_price=10.0, up=True, volumes=None):
    ns = NameSeries(ticker)
    d = date.fromisoformat(d0)
    end = date.fromisoformat(d1)
    i = 0
    while d <= end:
        if d.weekday() < 5:
            ds = d.isoformat()
            ns.dates.append(ds)
            ns.idx[ds] = len(ns.dates) - 1
            o = open_price
            c = open_price + (1.0 if up else -0.5)
            ns.open.append(o)
            ns.high.append(max(o, c) + 0.5)
            ns.low.append(min(o, c) - 0.5)
            ns.close.append(c)
            v = volumes[i] if volumes else 1_000_000.0
            ns.vol.append(v)
            ns.dv.append(c * v)
            ns.fill_ok.append(v > 0)
            i += 1
        d += timedelta(days=1)
    return ns


class MiniPanel:
    def __init__(self, ns):
        self.names = {ns.ticker: ns}

    def get(self, t):
        return self.names.get(t)


def build(ns, acceptance_utc, hold=5, corp_actions=None, arm="A1-ANCHOR",
          direction_override=None):
    inst = clock.parse_acceptance_utc(acceptance_utc)
    et, off = clock.to_et(inst)
    stratum, is_weekend = clock.stratum_of(et)
    return build_decision(
        event_id="T", family_id=C.FAMILY_A2 if direction_override else C.FAMILY_A1,
        arm_id="A2-ANCHOR" if direction_override else arm,
        cik="CIK0000000001", ticker="TEST", form="10-Q",
        acceptance_utc=acceptance_utc, instant_et=et,
        hold_sessions=hold, panel=MiniPanel(ns),
        corp_actions=corp_actions or {}, stratum=stratum,
        bucket=stratum, is_weekend=is_weekend,
        direction_override=direction_override)


# ---------------------------------------------------------------- D-1 ----
def test_d1_a2_entry_open_anchored_s4_acceptance():
    """Monday 22:30Z (18:30 ET, S4): A1-style would direction Mon + entry
    Tue; A2 law enters at the FIRST OPEN strictly after = Tue open."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z", hold=5,
                     direction_override="LONG")
    assert exc is None and rec is not None
    assert rec["direction_session"] is None          # no A1-style session
    assert rec["direction"] == "LONG"
    assert rec["entry_session"] == "2024-06-11"      # Tue = first open after
    assert rec["exit_session"] == "2024-06-17"       # +4 sessions


def test_d1_a2_entry_open_anchored_s1_acceptance_same_day():
    """Tuesday 13:00Z (09:00 ET, S1 pre-open): first open strictly after is
    the SAME day's 09:30 open — the A1-style law would have entered Wed."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    rec, _ = build(ns, "2024-06-11T13:00:00.000Z", hold=5,
                   direction_override="LONG")
    assert rec["entry_session"] == "2024-06-11"
    assert rec["direction_session"] is None


def test_d1_a2_mid_session_acceptance_enters_next_day():
    """Tue 15:00 ET (19:00Z, S2 in-session): Tue 09:30 open is BEFORE the
    instant -> first open strictly after = Wed."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    rec, _ = build(ns, "2024-06-11T19:00:00.000Z", hold=5,
                   direction_override="LONG")
    assert rec["entry_session"] == "2024-06-12"


def test_d1_a2_exactly_at_open_resolves_next_session():
    """Open boundary is strict (r3 AMB-10): acceptance exactly 09:30 ET
    cannot enter that session."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    status, entry_i = resolve_entry_open_anchored(ns, clock.session_open_instant(date(2024, 6, 11)))
    assert status == "OK" and ns.dates[entry_i] == "2024-06-12"


# ---------------------------------------------------------------- D-2 ----
def test_d2_corp_action_lookup_case_insensitive(tmp_path, monkeypatch):
    """A div file whose stem casefold-matches but differs by letter case
    resolves (the 79-file D-2 defect class)."""
    div = tmp_path / "div"
    spl = tmp_path / "split"
    div.mkdir()
    spl.mkdir()
    (div / "ev_old2.json").write_text(json.dumps([{"date": "2024-05-10"}]))
    (spl / "ev_old2.json").write_text(json.dumps([]))
    monkeypatch.setattr(C, "DIV_DIR", str(div))
    monkeypatch.setattr(C, "SPLIT_DIR", str(spl))
    census = {}
    ca = load_corp_actions(census)
    assert ca["ev_old2"]["div"] == ["2024-05-10"]
    assert census["files"] == 2
    # case-insensitive window hit for the panel-spelled ticker
    assert corp_action_in_window(ca, "EV_OLD2", ["2024-05-08", "2024-05-12"]) is True
    assert corp_action_in_window(ca, "EV_OLD2", ["2024-05-11", "2024-05-12"]) is False


# --------------------------------------------------------------- AMB-1 ----
def test_amb1_weekend_acceptance_is_anchor_member_stratum_wknd():
    """Weekend acceptance joins the unmonitored set with stratum label
    WKND (r3 AMB-1); N2 (monitored S2) still excludes it."""
    ns = make_ns("TEST", "2025-01-02", "2025-04-30")
    events = [{"cik": "1", "ticker": "TEST", "form": "10-Q",
               "accession": "ACC", "acceptance_utc": "2025-03-09T22:30:00.000Z",
               "filing_date": "2025-03-09"}]  # Sunday 18:30 ET
    records, exclusions = build_a1_arms(events, MiniPanel(ns), {}, n4=None)
    anchor = [r for r in records if r["arm_id"] == "A1-ANCHOR"]
    n2 = [r for r in records if r["arm_id"] == "A1-N2"]
    assert len(anchor) == 1 and not n2
    assert anchor[0]["stratum"] == "WKND"
    assert anchor[0]["bucket"] == "WKND"
    assert anchor[0]["is_weekend"] is True


# --------------------------------------------------------------- AMB-7 ----
def test_amb7_exit_roll_forward_records_note():
    """Exit bar unfillable (volume 0) -> exit rolls to the next clean bar;
    the record discloses EXIT_ROLLED_B1X1; no exclusion."""
    vols = [1_000_000.0] * 70
    ns = make_ns("TEST", "2024-04-01", "2024-06-30", volumes=vols)
    exit_i = ns.idx["2024-06-18"]  # nominal H=5 exit from entry 06-12
    ns.vol[exit_i] = 0.0
    ns.fill_ok[exit_i] = False
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z")
    assert rec is not None and exc is None
    assert rec["exit_session"] == "2024-06-19"
    assert rec["exclusions_applied"] == ["EXIT_ROLLED_B1X1"]
    assert rec["delisting_exit"] is False


def test_amb7_exit_roll_exhaustion_at_last_bar():
    """Whole tail unfillable -> exit at the last bar flagged delisting_exit
    with EXIT_ROLL_EXHAUSTED_AT_LAST_BAR."""
    vols = [1_000_000.0] * 70
    ns = make_ns("TEST", "2024-04-01", "2024-06-30", volumes=vols)
    for d in ns.dates[ns.idx["2024-06-18"]:]:
        i = ns.idx[d]
        ns.vol[i] = 0.0
        ns.fill_ok[i] = False
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z")
    assert rec is not None and exc is None
    assert rec["exit_session"] == ns.dates[-1]
    assert rec["delisting_exit"] is True
    assert rec["exclusions_applied"] == ["EXIT_ROLL_EXHAUSTED_AT_LAST_BAR"]


def test_amb7_exit_roll_respects_fold_cap():
    """The roll never crosses the fold boundary (force-flat cap): a
    fold-clamped, unfillable exit exhausts AT the boundary bar."""
    vols = [1_000_000.0] * 200
    ns = make_ns("TEST", "2022-10-01", "2023-03-31", volumes=vols)
    for d in ("2022-12-27", "2022-12-28", "2022-12-29", "2022-12-30"):
        i = ns.idx[d]
        ns.vol[i] = 0.0
        ns.fill_ok[i] = False
    rec, exc = build(ns, "2022-12-20T22:30:00.000Z", hold=10)
    assert rec is not None and exc is None
    assert rec["forced_flat"] is True
    assert rec["exit_session"] == "2022-12-30"       # fold cap, never crossed
    assert rec["delisting_exit"] is True             # exhausted at the cap
    assert rec["exclusions_applied"] == ["EXIT_ROLL_EXHAUSTED_AT_LAST_BAR"]


# --------------------------------------------------------------- AMB-9 ----
def test_amb9_fold_by_et_local_date():
    """2021-01-01T04:00Z is 2020-12-31 23:00 ET -> F2 (UTC date would say F3)."""
    assert clock.fold_of_et("2021-01-01T04:00:00.000Z") == "F2"
    assert clock.fold_of_et("2021-01-01T14:00:00.000Z") == "F3"
    assert clock.fold_of_et("2018-01-01T04:00:00.000Z") == "F1"   # 2017-12-31 23:00 ET
    assert clock.fold_of_et("2018-01-01T14:00:00.000Z") == "F2"


# -------------------------------------------------------------- AMB-11 ----
def test_amb11_direction_tie_still_excluded_counted():
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    di = ns.idx["2024-06-11"]
    ns.close[di] = ns.open[di]
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z")
    assert rec is None and exc is not None
    assert exc["reason"] == "ZERO_DIRECTION_SESSION_MOVE"


# -------------------------------------------------------------- AMB-15 ----
def test_amb15_ca_calendar_interval_non_session_exdate():
    """An ex-date on a NON-SESSION day (Saturday 2024-06-15) inside the
    window interval contaminates; one after the exit does not."""
    ns = make_ns("TEST", "2024-04-01", "2024-06-30")
    ca = {"TEST": {"div": ["2024-06-15"], "split": []}}  # Saturday, no bar
    rec, exc = build(ns, "2024-06-10T22:30:00.000Z", corp_actions=ca)
    assert rec is None and exc is not None
    assert exc["reason"] == "CORP_ACTION_IN_WINDOW"
    ca2 = {"TEST": {"div": ["2024-06-16"], "split": []}}  # Sunday AFTER exit 06-18? no: 06-16 is Sunday inside
    # exit for this event is 2024-06-18 (Tue); 06-16 is inside -> excluded too
    rec2, exc2 = build(ns, "2024-06-10T22:30:00.000Z", corp_actions=ca2)
    assert rec2 is None and exc2 is not None
    ca3 = {"TEST": {"div": ["2024-06-19"], "split": []}}  # day after exit
    rec3, exc3 = build(ns, "2024-06-10T22:30:00.000Z", corp_actions=ca3)
    assert rec3 is not None and exc3 is None


def test_amb6_unpriced_a2_rows_drop_not_imputed():
    """a2_inputs semantics (r3 AMB-6): a P-row whose XML has no priced
    transaction is dropped and counted UNPRICED — never panel-imputed."""
    from emv1.a2_inputs import build_a2_issuer_days
    rows = [{"cik": "1", "accession": "ACC1", "acceptance": "2024-01-02T15:00:00.000Z",
             "filing_date": "2024-01-02", "transaction_date": "2024-01-02",
             "transaction_code": "P", "direction": "A", "shares": "5000",
             "owner_cik": None, "owner_name": "BOSS", "table": "nonDerivative"}]
    xml = {"ACC1": {"owners": [{"isDirector": "1", "isOfficer": None,
                                "isTenPercentOwner": None, "officerTitle": None}],
                    "plan_flag": None,
                    "txns": [{"shares": "5000", "price": None}]}}
    events, stats = build_a2_issuer_days(rows, {"ACC1": "4"}, xml, {"1"})
    assert events == []
    assert stats["drops"].get("UNPRICED") == 1
