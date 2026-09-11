"""CRYPTO-NG2 D2 measurement library: NOVELTY + FEASIBILITY + IDENTIFIABILITY.

Measured on the frozen S4 H1 panels (3 symbols, 2025-08-22T00..2026-08-21T23)
consumed ONLY through the ng1 cycle plane adapter (CADS resolve verify-on-read,
digest-pinned; import-only reuse of research/assets/crypto_ng1).  Every number
this module produces is one of:

  * pooled Pearson/Spearman |rho| between a proposal's declared D2 series
    (per-decision GROSS return vector per its frozen representation_identity,
    funding transfers included verbatim where the representation books them)
    and a veto-panel shadow / dead-form shadow / in-family control arm
    evaluated on the same decision grid;
  * decision counts, fill counts, settlement-grid coverage, calendar facts;
  * margins to the frozen 0.20 veto bar and the 0.98 identifiability bar.

NO expectancy, NO profit factor, NO PnL, NO aggregate of returns is computed
or emitted anywhere (outcome-leak ban for the D2 lane).

Cost invariance (why gross returns suffice): the declared per-decision
after-cost return is r_net = r - 2*c with a CONSTANT c per arm.  Pearson
is invariant to additive shifts of either argument; Spearman is invariant to
any strictly monotone transform.  Therefore rho(r_net, v) == rho(r, v) for
every veto series v and every tier constant c: the novelty measurement needs
no cost constant and none is invented here.

Funding transfers are part of the DECLARED gross series (A5 representation:
r = d*(exit/entry - 1) + transfer), so they enter the measured vectors
verbatim, never as a direction input.
"""

from __future__ import annotations

import json
import math
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

# Import-only reuse of the NG1 D2 library (29-shape veto panel builders,
# plane-panel parsing, statistics, calendar arithmetic).  Read-only.
from research.assets.crypto_ng1.d2 import measure as N1

SCHEMA_LIB = "crypto_ng2/d2_measure@1"

#: Frozen novelty bar (plan section 1; P-2 margins recorded).
VETO_BAR = N1.VETO_BAR                      # 0.20

#: Frozen identifiability twin bar: a clock shadow / placebo whose pooled
#: |rho| vs the anchor reaches 0.98 is a lagged twin of the anchor (the
#: SFV12-A5-H1 0.9923 failure class) and the battery is uninterpretable.
IDENT_BAR = 0.98

#: Q-6 recent-window policy (dispatch packet): last 6 calendar months of the
#: panel window; A4 floor >= 6 recent anchor decisions per proposal, A5 floor
#: >= 100 recent instants x 3 symbols = 300 recent anchor decisions (the A5
#: floor applies to the measured funded counts once the settlement grid is
#: evidenced by the pull).
Q6_RECENT_WINDOW_MONTHS = 6
Q6_ANCHOR_FLOOR_A4 = 6
Q6_ANCHOR_FLOOR_A5_DECISIONS = 300

#: Minimum aligned pairs for a rho decision number (inherited NG1 guard,
#: scaled to the cycle's own Q-6 floor).
MIN_PAIRS = N1.MIN_PAIRS                    # 8

SYMBOLS = N1.SYMBOLS

PANEL_WINDOW_START = N1.PANEL_WINDOW_START
PANEL_WINDOW_END = N1.PANEL_WINDOW_END

#: Settlement-grid clock (frozen A5 representation): 8h grid 00/08/16 UTC.
FUNDING_GRID_HOURS = (0, 8, 16)
FUNDING_GRID_STEP_H = 8

#: Eligible grid instants per symbol (frozen): every 8h-grid instant whose
#: full family bar range B-7..B+3 lies inside the panel.  First = the 08:00
#: instant of the first panel day (the 00:00 instant needs pre-panel bars ->
#: INELIGIBLE_WARMUP), last = 2026-08-21T16:00Z.  365 days x 3 - 1 = 1,094.
GRID_FIRST_INSTANT = "2025-08-22T08:00:00Z"
GRID_LAST_INSTANT = "2026-08-21T16:00:00Z"
GRID_ELIGIBLE_HYPOTHESIS_PER_SYMBOL = 1094

#: Keyless endpoint proven at P0 (p0_funding_probe.json): per-response cap
#: 500 rows observed against a requested limit of 1000; etiquette <= 1
#: request / 0.5 s with bounded backoff.
FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
FUNDING_REQUEST_LIMIT = 1000
FUNDING_OBSERVED_CAP = 500
FUNDING_ETIQUETTE_SLEEP_S = 0.55
FUNDING_RETRIES = 3
FUNDING_BACKOFF_S = 5.0

_S0_START_MS = int(PANEL_WINDOW_START.timestamp() * 1000)
_S0_END_MS = int((PANEL_WINDOW_END + timedelta(hours=1)).timestamp() * 1000) - 1

assert _S0_START_MS == 1755820800000 and _S0_END_MS == 1787356799999

#: Census instants declared verbatim in the D1 proposals (P-12 cross-check
#: against p0_calendar_census_ng2.json; mismatch is fail-closed).
DECLARED_CPI_INSTANTS = [
    "2025-09-11T12:30:00Z", "2025-10-24T12:30:00Z", "2025-12-18T13:30:00Z",
    "2026-01-13T13:30:00Z", "2026-02-13T13:30:00Z", "2026-03-11T12:30:00Z",
    "2026-04-10T12:30:00Z", "2026-05-12T12:30:00Z", "2026-06-10T12:30:00Z",
    "2026-07-14T12:30:00Z", "2026-08-12T12:30:00Z",
]
DECLARED_NFP_INSTANTS = [
    "2025-09-05T12:30:00Z", "2025-11-20T13:30:00Z", "2025-12-16T13:30:00Z",
    "2026-01-09T13:30:00Z", "2026-02-11T13:30:00Z", "2026-03-06T13:30:00Z",
    "2026-04-03T12:30:00Z", "2026-05-08T12:30:00Z", "2026-06-05T12:30:00Z",
    "2026-07-02T12:30:00Z", "2026-08-07T12:30:00Z",
]

#: Dead ng1 FOMC-form ancestry (rebuilt as shadows on the ng2 decision grids):
#: CNG1-A4-P1 anchor rule = sign(imb on the announcement bar);
#: CNG1-A4-P2 anchor rule = sign(press over A-4..A-1).
DEAD_FORM_IDS = ("cng2_dead_fomc_a4p1", "cng2_dead_fomc_a4p2")

#: NG2 required veto set = the inherited 29-shape panel + the funding-LEVEL
#: shadow rebuilt from THIS cycle's pull (3 symbols) + the two dead FOMC-form
#: return shadows.  A5 proposals additionally carry the in-family
#: CTL-FUNDLEVEL arm pair (declared F3 in-family clause).
NG2_REQUIRED_VETOES = list(N1.REQUIRED_VETOES) + [
    "cng2_funding_level_pull",
    "cng2_dead_fomc_a4p1",
    "cng2_dead_fomc_a4p2",
]

HYPS = ["CNG2-A4-P1", "CNG2-A4-P2", "CNG2-A5-P1", "CNG2-A5-P2"]


# --------------------------------------------------------------------------- #
# 1. census loading (fail-closed)
# --------------------------------------------------------------------------- #

def _norm_instant(t: str) -> str:
    """Normalize an ISO instant to the frozen 'YYYY-MM-DDTHH:MM:SSZ' form
    (the census artifact emits isoformat offsets like '+00:00')."""
    t = t.replace("+00:00", "Z")
    if not t.endswith("Z"):
        raise ValueError(f"non-UTC instant refused: {t!r}")
    return t


def load_census_instants(census_path: str | Path) -> dict:
    """Extract the CPI/NFP instant lists from p0_calendar_census_ng2.json and
    cross-check them against the D1 proposals' declared verbatim lists."""
    d = json.loads(Path(census_path).read_text())
    if d.get("schema") != "crypto_ng2_run/p0_calendar_census_ng2@1":
        raise ValueError(f"unexpected census schema: {d.get('schema')!r}")
    inst = d.get("instants", [])
    got = {"CPI": [], "NFP": []}
    for row in inst:
        s = row.get("series")
        if s not in got:
            raise ValueError(f"unexpected census series {s!r}")
        got[s].append(_norm_instant(row["instant_utc"]))
    for s in got:
        got[s].sort()
    checks = {
        "cpi_count_11": len(got["CPI"]) == 11,
        "nfp_count_11": len(got["NFP"]) == 11,
        "cpi_matches_proposal_declaration": (
            got["CPI"] == sorted(DECLARED_CPI_INSTANTS)),
        "nfp_matches_proposal_declaration": (
            got["NFP"] == sorted(DECLARED_NFP_INSTANTS)),
        "all_instants_830_et_print_clock": all(
            t[11:13] in ("12", "13") and t[14:] == "30:00Z"
            for s in ("CPI", "NFP") for t in got[s]),
        "all_instants_inside_panel_window": all(
            PANEL_WINDOW_START
            <= N1.parse_instant(t) <= PANEL_WINDOW_END
            for s in ("CPI", "NFP") for t in got[s]),
        "cpi_nfp_date_disjoint": N1.date_disjoint(
            [t[:10] for t in got["CPI"]],
            [t[:10] for t in got["NFP"]])["disjoint"],
    }
    if not all(checks.values()):
        raise ValueError(f"census fail-closed check failed: {checks}")
    return {"instants": got, "checks": checks,
            "census_sha_input": str(census_path)}


# --------------------------------------------------------------------------- #
# 2. funding settlement pull (keyless endpoint, etiquette + backoff)
# --------------------------------------------------------------------------- #

def _funding_fetch(url: str, timeout: float = 60.0):
    """Real fetch (urllib).  Tests inject a fake."""
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def pull_funding_symbol(symbol: str, start_ms: int = _S0_START_MS,
                        end_ms: int = _S0_END_MS,
                        fetch: Callable[[str], list] = _funding_fetch,
                        sleep: Callable[[float], None] = time.sleep
                        ) -> tuple[list[dict], dict]:
    """Paginate the keyless fapi fundingRate endpoint for one symbol over
    the full panel window.  Returns (rows, report).  Fail-closed: exhaustion
    of retries raises (the caller records BLOCKED_DATA, never a partial pass).
    """
    rows: list[dict] = []
    pages = 0
    cursor = start_ms
    while cursor <= end_ms:
        url = (f"{FUNDING_URL}?symbol={symbol}&startTime={cursor}"
               f"&endTime={end_ms}&limit={FUNDING_REQUEST_LIMIT}")
        last_exc = None
        batch = None
        for attempt in range(FUNDING_RETRIES):
            try:
                batch = fetch(url)
                break
            except Exception as exc:                 # noqa: BLE001
                last_exc = exc
                sleep(FUNDING_BACKOFF_S * (attempt + 1))
        if batch is None:
            raise RuntimeError(
                f"funding pull failed for {symbol} at cursor {cursor}: "
                f"{last_exc}") from last_exc
        pages += 1
        if not batch:
            break
        for r in batch:
            if not (start_ms <= r["fundingTime"] <= end_ms):
                continue
            rows.append({"fundingTime": int(r["fundingTime"]),
                         "fundingRate": str(r["fundingRate"]),
                         "rateType": r.get("rateType"),
                         "markPrice": r.get("markPrice")})
        tail = int(batch[-1]["fundingTime"])
        nxt = tail + 1
        if nxt <= cursor:                            # defensive: no progress
            raise RuntimeError(
                f"funding pagination stalled for {symbol} at {tail}")
        cursor = nxt
        if tail >= end_ms:
            break
        sleep(FUNDING_ETIQUETTE_SLEEP_S)             # <= 1 req / 0.5 s
    rows.sort(key=lambda r: r["fundingTime"])
    report = {"symbol": symbol, "pages": pages, "rows": len(rows),
              "first_funding_time_ms": rows[0]["fundingTime"] if rows else None,
              "last_funding_time_ms": rows[-1]["fundingTime"] if rows else None}
    return rows, report


def pull_funding_all(symbols: list[str] = None, **kw) -> tuple[dict, dict]:
    symbols = symbols or SYMBOLS
    out, reports = {}, {}
    for s in symbols:
        rows, rep = pull_funding_symbol(s, **kw)
        out[s] = rows
        reports[s] = rep
    return out, reports


# --------------------------------------------------------------------------- #
# 3. settlement evidence (grid matching, fail-closed)
# --------------------------------------------------------------------------- #

def eligible_grid_instants() -> list[datetime]:
    """The 1,094 eligible 8h-grid instants 2025-08-22T08:00Z..2026-08-21T16:00Z."""
    out = []
    t = N1.parse_instant(GRID_FIRST_INSTANT)
    last = N1.parse_instant(GRID_LAST_INSTANT)
    while t <= last:
        assert t.hour in FUNDING_GRID_HOURS
        out.append(t)
        t += timedelta(hours=FUNDING_GRID_STEP_H)
    assert len(out) == GRID_ELIGIBLE_HYPOTHESIS_PER_SYMBOL
    return out


def _floor_hour_ms(ms: int) -> datetime:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0)


@dataclass
class FundingEvidence:
    """Settlement series folded onto the frozen 8h grid, fail-closed."""
    symbol: str
    rows_total: int
    rate_by_grid_hour: dict[str, float] = field(default_factory=dict)
    raw_rows: list[tuple[int, float]] = field(default_factory=list)
    off_grid_rows: list[dict] = field(default_factory=list)
    duplicate_grid_hours: list[dict] = field(default_factory=list)
    non_increasing: list[dict] = field(default_factory=list)
    first_time_ms: Optional[int] = None
    last_time_ms: Optional[int] = None

    def rate_at(self, grid_hour: str) -> Optional[float]:
        return self.rate_by_grid_hour.get(grid_hour)

    def report(self) -> dict:
        eligible = [N1.fmt_hour(t) for t in eligible_grid_instants()]
        evidenced = [h for h in eligible if h in self.rate_by_grid_hour]
        missing = [h for h in eligible if h not in self.rate_by_grid_hour]
        return {
            "symbol": self.symbol,
            "rows_in_window": self.rows_total,
            "span_ms": [self.first_time_ms, self.last_time_ms],
            "eligible_grid_instants": len(eligible),
            "evidenced_grid_instants": len(evidenced),
            "unevidenced_grid_instants": len(missing),
            "unevidenced_list_head": missing[:12],
            "off_grid_rows": len(self.off_grid_rows),
            "off_grid_list_head": self.off_grid_rows[:12],
            "duplicate_grid_hours": len(self.duplicate_grid_hours),
            "non_increasing_pairs": len(self.non_increasing),
            "grid_hypothesis_1094": len(eligible) == 1094,
        }


def build_funding_evidence(symbol: str, rows: list[dict]) -> FundingEvidence:
    """Fold settlement rows onto the 8h grid (tolerance = same hour bar,
    absorbing the observed boundary+1ms quirk).  Off-grid settlements are
    recorded as incidents, never silently folded."""
    ev = FundingEvidence(symbol=symbol, rows_total=len(rows))
    prev_ms = None
    for r in rows:
        ms = int(r["fundingTime"])
        rate = float(r["fundingRate"])
        if prev_ms is not None and ms <= prev_ms:
            ev.non_increasing.append({"fundingTime": ms,
                                      "prev": prev_ms})
        prev_ms = ms
        if ev.first_time_ms is None or ms < ev.first_time_ms:
            ev.first_time_ms = ms
        if ev.last_time_ms is None or ms > ev.last_time_ms:
            ev.last_time_ms = ms
        ev.raw_rows.append((ms, rate))
        hour_dt = _floor_hour_ms(ms)
        if hour_dt.hour not in FUNDING_GRID_HOURS:
            ev.off_grid_rows.append(
                {"fundingTime": ms,
                 "utc": datetime.fromtimestamp(
                     ms / 1000.0, tz=timezone.utc).isoformat(),
                 "fundingRate": r["fundingRate"]})
            continue
        key = N1.fmt_hour(hour_dt)
        if key in ev.rate_by_grid_hour:
            ev.duplicate_grid_hours.append({"grid_hour": key,
                                            "fundingTime": ms})
            continue
        ev.rate_by_grid_hour[key] = rate
    return ev


# --------------------------------------------------------------------------- #
# 4. decision rows (exact representation identities, gross returns)
# --------------------------------------------------------------------------- #

@dataclass
class NG2Decision:
    symbol: str
    instant: str                 # ISO Z clock event (census instant / S)
    decision_ts: str             # ISO Z bar close at which the decision lands
    decision_bar: str            # hour key of the bar closed at decision
    decision_date: str           # UTC date of the decision bar (daily veto key)
    proj_day: str                # daily-projection key (instant's UTC date)
    role: str                    # anchor | neighbour | control | shadow | placebo
    arm_id: str
    status: str                  # FUNDED | UNFUNDED_SKIP | UNMEASURED_BAR |
                                 # BLOCKED_MISSING_BAR |
                                 # UNFUNDED_SKIP_NO_SETTLEMENT
    direction: Optional[int] = None
    entry_bar: Optional[str] = None
    exit_bar: Optional[str] = None
    transfer: Optional[float] = None    # booked settlement transfer (A5 arms)
    r_gross: Optional[float] = None     # cost-shift invariant for rho


def _bar_ok(b) -> bool:
    return b is not None and isinstance(b.get("last_price"), (int, float)) \
        and math.isfinite(b["last_price"]) and b["last_price"] > 0.0


def _sign(x: Optional[float]) -> Optional[int]:
    if x is None:
        return None
    return 1 if x > 0 else (-1 if x < 0 else 0)


def _mk_row(panel, sym, instant, dec_bar, role, arm_id, d,
            entry_bar, exit_bar, transfer=None) -> NG2Decision:
    """Assemble one decision row; fill-bar integrity and tie handling are
    fail-closed per the proposals (UNMEASURED_BAR for feature misses,
    BLOCKED_MISSING_BAR for fill misses, UNFUNDED_SKIP for exact ties)."""
    row = NG2Decision(
        symbol=sym, instant=instant,
        decision_ts=N1.fmt_hour(N1.parse_hour(dec_bar)
                                + timedelta(hours=1)) + ":00:00Z",
        decision_bar=dec_bar, decision_date=dec_bar[:10],
        proj_day=instant[:10], role=role, arm_id=arm_id,
        status="FUNDED")
    if d is None:
        row.status = "UNMEASURED_BAR"
        return row
    eb, xb = panel.bar(entry_bar), panel.bar(exit_bar)
    if not _bar_ok(eb) or not _bar_ok(xb):
        row.status = "BLOCKED_MISSING_BAR"
        return row
    if d == 0:
        row.status = "UNFUNDED_SKIP"
        return row
    row.direction = d
    row.entry_bar, row.exit_bar = entry_bar, exit_bar
    r = d * (xb["last_price"] / eb["last_price"] - 1.0)
    if transfer is not None:
        r += transfer
        row.transfer = transfer
    row.r_gross = r
    return row


def _press_over(panel, anchor_bar: str, k_start: int, k_end: int):
    """Bounded net-pressure ratio over bars anchor_bar+k_start..+k_end."""
    num = den = 0.0
    for k in range(k_start, k_end + 1):
        b = panel.bar_offset(anchor_bar, k)
        if b is None:
            return None, True
        num += b["buy_quote"] - b["sell_quote"]
        den += b["quote_total"]
    if den == 0.0:
        return None, False
    return num / den, False


# ---- A4 (census-clock families) ------------------------------------------- #

def _a4_reaction_sign(panel, a_bar: str, hyp: str):
    """Direction rule on the announcement bar A.  P1 = price reaction sign;
    P2 = taker-quote imbalance sign.  None -> UNMEASURED_BAR, 0 -> tie."""
    if hyp == "CNG2-A4-P1":
        prev, cur = panel.bar_offset(a_bar, -1), panel.bar(a_bar)
        if not _bar_ok(prev) or not _bar_ok(cur):
            return None
        return _sign(cur["last_price"] / prev["last_price"] - 1.0)
    bar = panel.bar(a_bar)
    if bar is None or bar["quote_total"] == 0.0:
        return None
    return _sign((bar["buy_quote"] - bar["sell_quote"])
                 / bar["quote_total"])


def build_a4_arm(panel, instants: list[str], hyp: str, arm: str,
                 ) -> list[NG2Decision]:
    """One A4 arm over the census instants of one symbol.

    anchor H=6; neighbour H=12; delay2 fills at A+2/A+2+H (H=6, direction
    still computed on A); clairvoyant direction = sign of the holding-window
    return (perfect foresight); clocklong direction = +1.
    """
    H = 6 if arm in ("anchor", "delay2", "clairvoyant", "clocklong") else 12
    out = []
    for inst in instants:
        dt = N1.parse_instant(inst)
        a = N1.fmt_hour(dt)                      # announcement bar A
        if arm == "clairvoyant":
            fwd, cur = panel.bar_offset(a, H), panel.bar(a)
            d = (None if not _bar_ok(fwd) or not _bar_ok(cur) else
                 _sign(fwd["last_price"] / cur["last_price"] - 1.0))
        elif arm == "clocklong":
            d = 1
        else:
            d = _a4_reaction_sign(panel, a, hyp)
        if arm == "delay2":
            entry, exit_ = N1.fmt_hour(dt + timedelta(hours=2)), \
                N1.fmt_hour(dt + timedelta(hours=2 + H))
        else:
            entry, exit_ = a, N1.fmt_hour(dt + timedelta(hours=H))
        role = {"anchor": "anchor", "neighbour": "neighbour"}.get(
            arm, "control" if arm in ("delay2", "clairvoyant") else "shadow")
        out.append(_mk_row(panel, panel.symbol, inst, a, role,
                           f"{hyp}-{arm.upper()}", d, entry, exit_))
    return out


def build_a4_shiftplus1(panel, instants: list[str], hyp: str
                        ) -> list[NG2Decision]:
    """CTL-SHIFTPLUS1: session i's decision row (direction and fills computed
    on session i's own bars) recorded at session i+1's census instant
    (k=+1 frozen; the first instant has no predecessor row -> 10 sham
    instants x 3 symbols = 30 decisions)."""
    sessions = sorted(instants)
    out = []
    for i in range(len(sessions) - 1):
        src, tgt = sessions[i], sessions[i + 1]
        dt = N1.parse_instant(src)
        a = N1.fmt_hour(dt)
        d = _a4_reaction_sign(panel, a, hyp)
        row = _mk_row(panel, panel.symbol, tgt, a, "placebo",
                      f"{hyp}-CTL-SHIFTPLUS1", d, a,
                      N1.fmt_hour(dt + timedelta(hours=6)))
        out.append(row)
    return out


# ---- A5 (settlement-grid families) ---------------------------------------- #

def build_a5_arm(panel, ev: FundingEvidence, hyp: str, arm: str
                 ) -> list[NG2Decision]:
    """One A5 arm over the eligible 8h-grid instants of one symbol.

    P1 anchor: d=sign(press B-4..B-2), entry close B-2 (S-1h), exit close B
    (S+1h), transfer = -d*rate(S) booked.  P2 anchor: d=-sign(press B-1..B),
    entry close B (S+1h), exit close B+3 (S+4h), no transfer.  See the frozen
    proposals for neighbour / placebo / clock shadow / fundlevel variants.
    """
    out = []
    for t in eligible_grid_instants():
        s_iso = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        b = N1.fmt_hour(t)                        # boundary bar B (open = S)
        rate = ev.rate_at(b)
        if rate is None:
            row = NG2Decision(
                symbol=panel.symbol, instant=s_iso,
                decision_ts=N1.fmt_hour(t + timedelta(hours=1)) + ":00:00Z",
                decision_bar=(b if hyp == "CNG2-A5-P2"
                              else N1.fmt_hour(t - timedelta(hours=2))),
                decision_date=b[:10], proj_day=s_iso[:10], role="anchor",
                arm_id=f"{hyp}-{arm.upper()}",
                status="UNFUNDED_SKIP_NO_SETTLEMENT")
            out.append(row)
            continue

        if hyp == "CNG2-A5-P1":
            # entry bar B-2, exit bar B, transfer booked for holds through S
            if arm == "anchor":
                p, blocked = _press_over(panel, b, -4, -2)
                d = None if blocked else _sign(p)
                entry, exit_ = -2, 0
            elif arm == "neighbour":                 # NEIGH-W6: B-7..B-2
                p, blocked = _press_over(panel, b, -7, -2)
                d = None if blocked else _sign(p)
                entry, exit_ = -2, 0
            elif arm == "placebo":                   # sham boundary S'=S-2h
                bp = N1.fmt_hour(t - timedelta(hours=2))
                p, blocked = _press_over(panel, bp, -4, -2)
                d = None if blocked else _sign(p)
                entry, exit_ = -4, -2                # [S-3h, S-1h), no xfer
            elif arm == "shadow":                    # clock-only, always long
                d = 1
                entry, exit_ = -2, 0
            elif arm == "fundlevel":                 # -sign(rate(S))
                d = -_sign(rate)
                entry, exit_ = -2, 0
            else:
                raise ValueError(arm)
            dec_bar = N1.fmt_hour(t + timedelta(hours=entry))
            transfer = None
            if arm in ("anchor", "neighbour", "shadow", "fundlevel"):
                transfer = -(d if d is not None else 0) * rate
            eb = N1.fmt_hour(t + timedelta(hours=entry))
            xb = N1.fmt_hour(t + timedelta(hours=exit_))
            out.append(_mk_row(panel, panel.symbol, s_iso, dec_bar,
                               _a5_role(arm), f"{hyp}-{arm.upper()}",
                               d, eb, xb, transfer))

        else:                                     # CNG2-A5-P2
            if arm == "anchor":
                p, blocked = _press_over(panel, b, -1, 0)
                d = None if blocked else -_sign(p)
                entry, exit_ = 0, 3
            elif arm == "neighbour":                 # NEIGH-H1: exit B+1
                p, blocked = _press_over(panel, b, -1, 0)
                d = None if blocked else -_sign(p)
                entry, exit_ = 0, 1
            elif arm == "placebo":                   # sham boundary S'=S-2h
                bp = N1.fmt_hour(t - timedelta(hours=2))
                p, blocked = _press_over(panel, bp, -1, 0)
                d = None if blocked else -_sign(p)
                entry, exit_ = -2, 1                 # [S-1h, S+2h) crosses S
            elif arm == "shadow":
                d = 1
                entry, exit_ = 0, 3
            elif arm == "fundlevel":
                d = -_sign(rate)
                entry, exit_ = 0, 3
            else:
                raise ValueError(arm)
            dec_bar = N1.fmt_hour(t + timedelta(hours=0 if arm != "placebo"
                                                else -2))
            transfer = None
            if arm == "placebo":                     # books the true-S xfer
                transfer = -(d if d is not None else 0) * rate
            eb = N1.fmt_hour(t + timedelta(hours=entry))
            xb = N1.fmt_hour(t + timedelta(hours=exit_))
            out.append(_mk_row(panel, panel.symbol, s_iso, dec_bar,
                               _a5_role(arm), f"{hyp}-{arm.upper()}",
                               d, eb, xb, transfer))
    return out


def _a5_role(arm: str) -> str:
    return {"anchor": "anchor", "neighbour": "neighbour",
            "fundlevel": "control", "shadow": "shadow",
            "placebo": "placebo"}[arm]


A4_ARMS = ["anchor", "neighbour", "delay2", "clairvoyant", "clocklong"]
A5_ARMS = ["anchor", "neighbour", "fundlevel", "shadow", "placebo"]


def build_family(panels: dict, instants_by_series: dict,
                 ev_by_symbol: dict, hyp: str) -> dict[str, list[NG2Decision]]:
    """All arms of one proposal, pooled 3-symbol (symbol-major)."""
    out: dict[str, list[NG2Decision]] = {}
    if hyp in ("CNG2-A4-P1", "CNG2-A4-P2"):
        series = "CPI" if hyp == "CNG2-A4-P1" else "NFP"
        instants = instants_by_series[series]
        for arm in A4_ARMS:
            rows = []
            for sym in SYMBOLS:
                rows.extend(build_a4_arm(panels[sym], instants, hyp, arm))
            out[arm] = rows
        sham = []
        for sym in SYMBOLS:
            sham.extend(build_a4_shiftplus1(panels[sym], instants, hyp))
        out["shiftplus1"] = sham
    else:
        for arm in A5_ARMS:
            rows = []
            for sym in SYMBOLS:
                rows.extend(build_a5_arm(panels[sym], ev_by_symbol[sym],
                                         hyp, arm))
            out[arm] = rows
    return out


# --------------------------------------------------------------------------- #
# 5. veto additions (funding LEVEL from this cycle's pull + dead FOMC forms)
# --------------------------------------------------------------------------- #

def funding_level_veto_fn(ev_by_symbol: dict):
    """Hourly funding-LEVEL shadow: rate of the last settlement whose
    fundingTime <= decision bar close (3 symbols, this cycle's pull)."""
    series = {sym: sorted(ev.raw_rows)
              for sym, ev in ev_by_symbol.items()}

    def fn(sym, bar_hour, ts):
        if sym not in series or not series[sym]:
            return None
        arr = series[sym]
        lo, hi, ans = 0, len(arr) - 1, None
        while lo <= hi:
            mid = (lo + hi) // 2
            if arr[mid][0] <= ts:
                ans = arr[mid][1]
                lo = mid + 1
            else:
                hi = mid - 1
        return ans
    return fn


def dead_form_direction(panel, decision_bar: str, form: str):
    """Direction of a dead ng1 FOMC-form rule evaluated at an arbitrary
    decision bar (the form's own announcement bar = the decision bar)."""
    if form == "cng2_dead_fomc_a4p1":
        bar = panel.bar(decision_bar)
        if bar is None or bar["quote_total"] == 0.0:
            return None
        return _sign((bar["buy_quote"] - bar["sell_quote"])
                     / bar["quote_total"])
    if form == "cng2_dead_fomc_a4p2":
        p, blocked = _press_over(panel, decision_bar, -4, -1)
        return None if blocked else _sign(p)
    raise ValueError(form)


def dead_form_shadow_returns(panels: dict, decisions: list[NG2Decision],
                             form: str) -> list[Optional[float]]:
    """Per-decision return of a dead FOMC-form book rendered on the measured
    proposal's own fills (same entry/exit bars as each decision row): the
    strict 'same bet' test -- two books differing only by direction rule."""
    out = []
    for d in decisions:
        if d.status != "FUNDED" or d.entry_bar is None:
            out.append(None)
            continue
        dd = dead_form_direction(panels[d.symbol], d.decision_bar, form)
        if dd is None or dd == 0:
            out.append(None)
            continue
        eb = panels[d.symbol].bar(d.entry_bar)
        xb = panels[d.symbol].bar(d.exit_bar)
        if not _bar_ok(eb) or not _bar_ok(xb):
            out.append(None)
            continue
        out.append(dd * (xb["last_price"] / eb["last_price"] - 1.0))
    return out


def ng2_novelty_verdict(pairs: dict, build_failures: dict) -> dict:
    """Mechanical proposal-level novelty verdict over the NG2 required set
    (fail-closed on unbuilt required vetoes; VETO on any measured pair)."""
    missing = [v for v in NG2_REQUIRED_VETOES if v in build_failures]
    if missing:
        return {"novelty_verdict": "INELIGIBLE_FAIL_CLOSED",
                "reason": "required veto(s) could not be rebuilt: "
                          + ", ".join(missing),
                "worst_pair": None, "worst_abs_rho": None,
                "margin_to_bar": None, "vetoed_pairs": []}
    measured = {k: v for k, v in pairs.items() if v["status"] == "MEASURED"}
    vetoed = [k for k, v in measured.items() if v["pair_verdict"] == "VETO"]
    if measured:
        worst = max(measured.items(), key=lambda kv: kv[1]["max_abs_rho"])
        return {"novelty_verdict": ("VETO_MEASURED" if vetoed
                                    else "NOVELTY_PASS"),
                "vetoed_pairs": vetoed,
                "worst_pair": worst[0],
                "worst_abs_rho": worst[1]["max_abs_rho"],
                "margin_to_bar": worst[1]["margin_to_bar"]}
    return {"novelty_verdict": "INELIGIBLE_FAIL_CLOSED",
            "reason": "no veto pair measurable on the declared grid",
            "worst_pair": None, "worst_abs_rho": None,
            "margin_to_bar": None, "vetoed_pairs": []}


# --------------------------------------------------------------------------- #
# 6. identifiability (clock shadow / placebo twin check) + F5
# --------------------------------------------------------------------------- #

def _funded_map(rows: list[NG2Decision]) -> dict:
    return {(d.symbol, d.instant): d.r_gross
            for d in rows if d.status == "FUNDED" and d.r_gross is not None}


def rho_on_shared_keys(rows_a, rows_b, min_pairs: int = MIN_PAIRS) -> dict:
    ka, kb = _funded_map(rows_a), _funded_map(rows_b)
    shared = sorted(k for k in ka if k in kb)
    xs = [ka[k] for k in shared]
    ys = [kb[k] for k in shared]
    res = N1.rho_pair_status(xs, ys, min_pairs=min_pairs)
    return {"shared_grid_keys": len(shared),
            "n_a_funded": len(ka), "n_b_funded": len(kb),
            "pair": res}


def identifiability(anchor, shadow, placebo) -> dict:
    """Twin check: the clock shadow (shares the anchor grid) and the placebo
    (shared keys where they exist) must stay BELOW 0.98 pooled |rho|; a twin
    control makes the battery uninterpretable (fail-closed)."""
    sh = rho_on_shared_keys(anchor, shadow)
    pl = rho_on_shared_keys(anchor, placebo)
    worst = None
    for name, blk in (("clock_shadow", sh), ("placebo", pl)):
        m = blk["pair"]["max_abs_rho"]
        if m is not None and (worst is None or m > worst[1]):
            worst = (name, m)
    twin = bool(worst is not None and worst[1] >= IDENT_BAR)
    return {
        "bar": IDENT_BAR,
        "clock_shadow_rho": sh,
        "placebo_rho": pl,
        "worst_arm": worst[0] if worst else None,
        "worst_abs_rho": worst[1] if worst else None,
        "margin_to_bar": (None if worst is None
                          else round(IDENT_BAR - worst[1], 6)),
        "status": ("IDENTIFIABILITY_FAIL_CONTROL_TWIN" if twin
                   else ("MEASURED" if worst else "NOT_COMPUTABLE")),
        "verdict": "FAIL" if twin else ("PASS" if worst else "UNMEASURED"),
    }


def daily_projection(rows: list[NG2Decision]) -> dict[tuple[str, str], float]:
    """Symbol-day sum of per-decision gross returns (projection key = the
    clock instant's UTC date, so P1 and P2 aggregate onto the same days)."""
    acc: dict[tuple[str, str], float] = {}
    for d in rows:
        if d.status != "FUNDED" or d.r_gross is None:
            continue
        k = (d.symbol, d.proj_day)
        acc[k] = acc.get(k, 0.0) + d.r_gross
    return acc


def f5_daily_aggregated(series_a, series_b) -> dict:
    """F5 on the daily-aggregated (symbol-day) projection (the A5 frozen rule
    text); the per-decision shared-key rho is recorded alongside."""
    da, db = daily_projection(series_a), daily_projection(series_b)
    shared = sorted(k for k in da if k in db)
    res = N1.rho_pair_status([da[k] for k in shared], [db[k] for k in shared])
    per_dec = rho_on_shared_keys(series_a, series_b)
    return {
        "status": res["status"],
        "alignment": "symbol-day sums of per-decision gross returns "
                     "(projection key = settlement instant's UTC date)",
        "shared_days": len(shared),
        "daily": {"n_pairs": res["n_pairs"], "pearson": res["pearson"],
                  "spearman": res["spearman"], "max_abs_rho": res["max_abs_rho"],
                  "margin_to_bar": res["margin_to_bar"]},
        "per_decision_shared_keys": per_dec["shared_grid_keys"],
        "per_decision_max_abs_rho": per_dec["pair"]["max_abs_rho"],
        "f5_fired": bool(res["max_abs_rho"] is not None
                         and res["max_abs_rho"] > VETO_BAR),
    }


# --------------------------------------------------------------------------- #
# 7. feasibility (counts + ceilings only; no PnL)
# --------------------------------------------------------------------------- #

COST_REFERENCE = {
    "tier": "2.0",
    "round_trip_bps": 24.0,
    "source": ("inherited V17 d2_a9f_feasibility_v17.json (per_proposal."
               "*.cost_ceiling: 'per-event round trip tier2.0 ~= 24bps'); "
               "the NG2 kernel adoption re-measures the schedule; measured "
               "beats referenced"),
}


def _counts(anchor: list[NG2Decision]) -> dict:
    funded = [d for d in anchor if d.status == "FUNDED"]
    return {
        "instants": len({d.instant for d in anchor}),
        "symbols": len({d.symbol for d in anchor}),
        "rows_anchor": len(anchor),
        "funded_anchor": len(funded),
        "unfunded_tie_skips": sum(1 for d in anchor
                                  if d.status == "UNFUNDED_SKIP"),
        "unmeasured_bar": sum(1 for d in anchor
                              if d.status == "UNMEASURED_BAR"),
        "blocked_missing_bar": sum(1 for d in anchor
                                   if d.status == "BLOCKED_MISSING_BAR"),
        "no_settlement_skips": sum(1 for d in anchor
                                   if d.status
                                   == "UNFUNDED_SKIP_NO_SETTLEMENT"),
        "decision_dates": sorted({d.proj_day for d in anchor}),
    }


def feasibility_for(hyp: str, anchor: list[NG2Decision],
                    grid_report: Optional[dict] = None) -> dict:
    rstart, rend = N1.recent_window_bounds(Q6_RECENT_WINDOW_MONTHS)
    c = _counts(anchor)
    is_a5 = hyp.startswith("CNG2-A5")
    # A4 recent window keys on the decision bar's date; A5 keys on the
    # settlement instant's date (the settlement clock is the proposal's
    # object; P1's S-1h decision can fall on the prior UTC day).
    recent = [d for d in anchor
              if d.status == "FUNDED" and rstart <= d.proj_day <= rend]
    floor = Q6_ANCHOR_FLOOR_A5_DECISIONS if is_a5 else Q6_ANCHOR_FLOOR_A4
    recent_instants = len({d.instant for d in recent})
    fills_window = 2 * c["funded_anchor"]
    months_total = ((PANEL_WINDOW_END - PANEL_WINDOW_START).days + 1) / 30.4375
    out = {
        "total_window": c,
        "recent_window": {
            "definition": (f"last {Q6_RECENT_WINDOW_MONTHS} calendar months "
                           f"of the panel window: {rstart}..{rend} "
                           f"({'settlement-instant' if is_a5 else 'decision-'}"
                           "date within bounds)"),
            "start": rstart, "end": rend,
            "anchor_decisions": len(recent),
            "anchor_instants": recent_instants,
            "floor_decisions": floor,
            "verdict": "PASS" if len(recent) >= floor else "FAIL",
        },
        "turnover": {
            "fills_per_funded_decision": 2,
            "anchor_fills_per_window": fills_window,
            "anchor_fills_per_month_approx": round(
                fills_window / months_total, 2),
            "note": ("unit notional 1.0 per decision; entry+exit only; the "
                     "funding transfer is a cash exchange, NOT a fill and "
                     "not charged taker cost"),
        },
        "cost_ceiling_reference": dict(COST_REFERENCE),
        "a9f_verdict": (
            "TURNOVER_LOW_CEILING_REFERENCED: measured fills/window and the "
            "referenced tier-2.0 round-trip are recorded; the cost-vs-gross-"
            "move adjudication is the scoring lane's F4 gate and is NOT "
            "computed here (outcome-leak ban)"),
    }
    if is_a5:
        out["settlement_grid"] = grid_report
    return out
