"""CRYPTO-NG3 D2 measurement lane -- non-scored veto diagnostics.

Scope (plan sections 5-6, read-only authority):
  X1 ancestry rho vs the full crypto shape inventory incl the NG2 29-shape triad
  X2 OI/funding dead forms (OILEV-V2 + NG2 dead-form envelope)
  X3 tape-fitted issuance proxy (fitting rule DECLARED BEFORE any rho is measured)
  X4 clock/dow geometry (Q-7 clock-only shadow)
  X5 null validity: delayed-state (+1d/+3d) and shuffled-within-month nulls must
     MOVE the signal; INVALID-NULL verdicts explicit (Q-11)
  F1 P-21 cost ceiling on the frozen crypto band/funding schedule (dual book:
  raw / financing-adjusted), with the proposals' declared turnover
  Q-6 recent-window population counts per fold; C6 strata as declared strata

PNL BAN: this lane computes and reports NO candidate return performance, PnL,
PF, Sharpe or drawdown.  The only return vectors materialized are the
control-book comparisons the preregistered vetoes require: per-decision anchor
gross window returns vs same-bet shadow books rendered over the anchor's own
entry/exit bars, pooled Pearson/Spearman rho.

All conventions are fixed BEFORE any rho is measured (P-12 frozen
representation); this code is the declaration.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# frozen constants
# ---------------------------------------------------------------------------

SCHEMA = "crypto_ng3_d2_verdict@1"
CYCLE_ID = "CRYPTO-NG3"
TASK_ID = "cng3-d2-measurement"

PANEL_FIRST = date(2025, 8, 22)
PANEL_LAST = date(2025, 8, 22) + timedelta(days=364)   # 2026-08-21, 365 panel days
PANEL_FIRST_DT = datetime(2025, 8, 22)
MARGIN_DAY = date(2026, 8, 22)                          # census coverage only
FOLDS = {                                               # C10 frozen
    "fold1": (date(2025, 8, 22), date(2026, 1, 14)),
    "fold2": (date(2026, 1, 15), date(2026, 5, 3)),
    "fold3": (date(2026, 5, 4), date(2026, 8, 22)),
}
NET_EXTREME_DAYS = {                                    # C6 P99 rule, frozen
    date(2025, 8, 28), date(2025, 9, 18), date(2025, 10, 14), date(2025, 10, 16),
}
USDT_ETH_ZERO_EVENT_DAYS = 339      # C6 declared sparse stratum (reported only)

RHO_BAR = 0.20                      # X1-X4 pooled |rho| kill bar (plan sec 5)
MIN_PAIRS = 8                       # NG2 kernel: n >= 8 else UNMEASURED
IDENTIFIABILITY_BAR = 0.98          # Q-11 / NG2 kernel: shifted placebo < 0.98
N_SHUFFLES = 200
SHUFFLE_SEED = 0

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

A4_L, A4_W, A4_TH, A4_HOLD = 7, 63, 0.75, 3
A4_FOLD_FLOOR = 20
A5_L, A5_MIN_TRAILING, A5_Q, A5_HOLD = 60, 20, 0.95, 5
A5_FOLD_FLOOR = 4

F1_ROUND_TRIP_BPS = 24.0
F1_TIER = "2.0"
F1_BAND_SOURCE = (
    "referenced frozen: research/control/v17_run/d2_a9f_feasibility_v17.json "
    "per_proposal.*.cost_ceiling ('per-event round trip tier2.0 ~= 24bps'), "
    "re-affirmed by the NG2 kernel (d2_feasibility_ng2.json cost_ceiling_reference)"
)
Q6_RECENT_WINDOW = (date(2026, 2, 21), date(2026, 8, 21))

X3_RULE_DECLARED = (
    "TAPE-FITTED ISSUANCE PROXY -- single mechanical rule, declared BEFORE any rho "
    "was measured: per symbol s and panel day d, tape_pressure[s,d] = sign(ret[s,d]) "
    "* (dvol[s,d] / median(dvol[s, prior 60 panel days strictly before d])) "
    "(|return|-conditioned volume z-scale mapped to the flow sign conventions of the "
    "proposals' own falsifier text); panel proxy P[d] = mean_s tape_pressure[s,d]. "
    "Binding kill test: pooled |rho| between the proxy book rendered over each "
    "anchor's own decision windows and the anchor's book return vector > 0.20 for "
    "EITHER anchor => KILL (the census adds nothing). Two mechanical renderings of "
    "the same declared proxy are measured and BOTH must clear: (a) proxy state at "
    "the decision date held over the window; (b) native-grain compounding of P over "
    "the held days vs the anchor's own window return. Diagnostics (non-binding): "
    "contemporaneous and 1-day-lagged rho(P_d, net_d), episode/A4 sign agreement."
)

SHADOW_RENDERING_DECLARED = (
    "Same-bet shadow rendering (declared before measurement): each inventory shape "
    "is rendered over the anchor's EXACT entry/exit bars. Day-defined shapes are "
    "evaluated at the decision date D (entry bar's UTC date) and held to exit: "
    "book = shape_D * R_window. Hour-defined shapes (v17_wkndliq_flag, "
    "v17_silres_event, generic_session_*, v17_oicascade_event) are evaluated per bar "
    "at native grain and compounded over the held hourly returns. Pooled Pearson + "
    "Spearman (average-rank ties) over per-decision per-symbol rows in symbol-major "
    "chronological order; bar |rho| > 0.20; pairs need n >= 8 and non-zero variance "
    "on both sides else UNMEASURED with reason."
)

BLOCKED_LEG_REASON = (
    "NOT_RUN_BLOCKED: the frozen funding-rate series bytes (NG2 "
    "data_raw/cng2_funding/funding_history.json sha256 "
    "38ad6faf2fcbf6c80f31241d426afc61837d5886cccccb8c1cd4f566ac0cdab1, untracked) "
    "are not present in any accessible storage (NG2 d2 worktree cleaned) and this "
    "lane's budget forbids network pulls; the leg is recorded NOT_RUN_BLOCKED, "
    "never inferred PASS."
)

BLOCKED_SHAPES = ["v17_fundjump_funding_level", "cng2_funding_level_pull"]

CLOCK_SHAPES = [f"generic_dow_{k}" for k in range(7)] + [
    "generic_weekend_flag", "v17_wkndliq_flag",
    "generic_session_us", "generic_session_eu", "generic_session_asia"]
DEAD_OI_SHAPES = ["v17_oi_level", "v17_oicascade_event"]   # OILEV-V2 class
ALL_DAY_SHAPES = ["v16_close_displace_fade", "v16_runpersist", "generic_tsmom28",
                  "generic_dvol_level_log", "generic_dvol_shock", "v17proxy_run_imb",
                  "v17proxy_taker_sat", "v17proxy_ret", "v17proxy_amihud",
                  "v17proxy_avg_ticket_ratio", "v17proxy_elite", "v17_attn_phase",
                  "v17_ticket_breadth", "v17_oi_level"] + \
                 [f"generic_dow_{k}" for k in range(7)] + ["generic_weekend_flag"]
ALL_HOUR_SHAPES = ["v17_wkndliq_flag", "v17_silres_event", "generic_session_us",
                   "generic_session_eu", "generic_session_asia", "v17_oicascade_event"]

# frozen CADS object digests (platform_v3 PA3 gate, S4:binance-daily-h1-panels;
# identical digests pinned in the committed NG2 d2_novelty_panel_ng2.json inputs)
CADS_DIGESTS = {
    "panel_BTCUSDT_h1": "111c1a2d6d62e26c1874bb428c10216e4926ae37ab0102ca098849ca25f5e7b1",
    "panel_ETHUSDT_h1": "ebd487a69404a1104d9123584c93af044a2796c338185d8466599b9f34bb440b",
    "panel_SOLUSDT_h1": "c4ca0b6eb719122054abec2a03fcac20d3f7794c5bf6d3c546ee6db1cb6e2107",
    "oi_series_reduced": "f26a61e45a0f79322140c66a1a8862b6d933e0a831d7559af459ef638fbefbd3",
}
FUNDING_DIGEST_ABSENT = "38ad6faf2fcbf6c80f31241d426afc61837d5886cccccb8c1cd4f566ac0cdab1"

OI_START = datetime(2025, 4, 25)   # V17 pull geometry, H4 snapshots


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fold_of(d: date) -> str | None:
    for name, (a, b) in FOLDS.items():
        if a <= d <= b:
            return name
    return None


def pearson(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 2 or x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _avg_ranks(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(v.size, dtype=float)
    sv = v[order]
    i = 0
    while i < sv.size:
        j = i
        while j + 1 < sv.size and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return float("nan")
    return pearson(_avg_ranks(x), _avg_ranks(y))


def rho_pair(x, y) -> dict:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = int(x.size)
    if n < MIN_PAIRS:
        return {"n_pairs": n, "pearson": None, "spearman": None, "max_abs_rho": None,
                "margin_to_bar": None, "status": "UNMEASURED_LOW_N"}
    if x.std() == 0 or y.std() == 0:
        return {"n_pairs": n, "pearson": None, "spearman": None, "max_abs_rho": None,
                "margin_to_bar": None, "status": "UNMEASURED_ZERO_VARIANCE"}
    p, s = pearson(x, y), spearman(x, y)
    m = max(abs(p), abs(s))
    return {"n_pairs": n, "pearson": round(p, 6), "spearman": round(s, 6),
            "max_abs_rho": round(m, 6), "margin_to_bar": round(RHO_BAR - m, 6),
            "status": "VETO" if m > RHO_BAR else "MEASURED"}


# ---------------------------------------------------------------------------
# census / anchor construction
# ---------------------------------------------------------------------------

def load_day_rows(path: Path) -> tuple[list[date], np.ndarray]:
    """Frozen all-class USDC-ETHEREUM daily net series (units = USDC)."""
    rows = json.loads(path.read_text())
    days, nets = [], []
    for r in rows:
        if r["issuer"] != "USDC_ETHEREUM":
            raise ValueError(f"unexpected issuer row {r['issuer']}")
        if not r["identity_ok"]:
            raise ValueError(f"C9 identity_ok=false on {r['day']}")
        y, m, dd = (int(x) for x in r["day"].split("-"))
        days.append(date(y, m, dd))
        nets.append(float(r["net"]))
    order = np.argsort([d.toordinal() for d in days])
    return [days[i] for i in order], np.asarray(nets)[order]


def build_a4(days: list[date], net: np.ndarray) -> dict:
    """SCNG3-A4-P1 anchor state, exactly per the frozen formula.

    S_t = sum of the last 7 daily nets; z_t standardized on the 63 prior S values
    (strictly before t); e_t in {-1,0,+1} at |z| >= 0.75; decidable only when all
    7 base days, all 63 prior S values and sigma > 0 exist.
    """
    n = len(days)
    S = np.full(n, np.nan)
    for i in range(A4_L - 1, n):
        S[i] = net[i - A4_L + 1:i + 1].sum()
    z = np.full(n, np.nan)
    e = np.zeros(n, dtype=int)
    decidable = np.zeros(n, dtype=bool)
    # The proposal pins "First decidable panel day = panel-day index 70 =
    # 2025-10-31"; the pure formula consequence (t-63 >= A4_L-1) would admit
    # index 69 (2025-10-30) one day earlier.  The pinned date governs (the more
    # specific frozen statement; can only remove decisions, never add) and the
    # discrepancy is disclosed in the verdict.
    first = max(A4_L - 1 + A4_W, A4_W + A4_L)
    for i in range(first, n):
        w = S[i - A4_W:i]
        if np.isnan(w).any():
            continue
        sd = w.std(ddof=1)
        if not sd > 0:
            continue
        z[i] = (S[i] - w.mean()) / sd
        decidable[i] = True
        if z[i] >= A4_TH:
            e[i] = 1
        elif z[i] <= -A4_TH:
            e[i] = -1
    return {"S": S, "z": z, "e": e, "decidable": decidable}


def a4_decisions(days: list[date], a4: dict) -> list[dict]:
    """Eligible A4 decisions: non-flat, decision day not C6-excluded, entry/exit
    are panel days inside the decision's fold; margin day never entry/exit."""
    out = []
    for i, d in enumerate(days):
        if d > PANEL_LAST or not a4["decidable"][i] or a4["e"][i] == 0:
            continue
        entry, exit_ = i + 1, i + A4_HOLD + 1
        if exit_ > len(days) - 1:
            continue
        de, dx = days[entry], days[exit_]
        if de > PANEL_LAST or dx > PANEL_LAST or MARGIN_DAY in (de, dx):
            continue
        if fold_of(d) != fold_of(dx):
            continue
        if d in NET_EXTREME_DAYS:
            continue
        out.append({"i": i, "day": d, "e": int(a4["e"][i]), "z": float(a4["z"][i]),
                    "entry_idx": entry, "exit_idx": exit_, "fold": fold_of(d)})
    return out


def build_a5(days: list[date], net: np.ndarray) -> dict:
    """SCNG3-A5-P1 anchor episodes, exactly per the frozen formula.

    scale_d = median(|net|, trailing <=60 panel days strictly before d, >=20
    valid); b_d = |net_d|/scale_d; theta_d = empirical 0.95 quantile (linear
    interpolation) of b_j over the same trailing window; trigger when
    b_d >= theta_d AND no open position AND days_since_last_trigger > H=5.
    Sign +1 on net-burn bursts (net_d < 0), -1 on net-mint bursts.  Zero-flow
    days are VALID observations (net = 0 exactly, b_d = 0, never trigger).
    b_j is defined from panel index A5_MIN_TRAILING; theta_d needs >= 20 defined
    b_j, so the first evaluable day is index 40 (conservative warmup reading).
    """
    n = len(days)
    abs_net = np.abs(net)
    b = np.full(n, np.nan)
    for d in range(A5_MIN_TRAILING, n):
        lo = max(0, d - A5_L)
        scale = float(np.median(abs_net[lo:d]))
        if scale > 0:
            b[d] = abs_net[d] / scale
    episodes = []
    last_trigger = -10 ** 9
    void_counts: dict[str, int] = {}
    candidates = 0
    for d in range(A5_MIN_TRAILING, n):
        lo = max(0, d - A5_L)
        bj = b[lo:d]
        bj = bj[~np.isnan(bj)]
        if bj.size < A5_MIN_TRAILING:
            continue
        theta = float(np.quantile(bj, A5_Q))
        if not b[d] >= theta:
            continue
        candidates += 1
        entry, exit_ = d + 1, d + A5_HOLD + 1
        void = None
        if entry <= last_trigger + A5_HOLD:
            void = "REFRACTORY"
        elif exit_ > len(days) - 1 or days[exit_] > PANEL_LAST or days[exit_] == MARGIN_DAY:
            void = "BOUNDARY_VOID"
        elif days[d] in NET_EXTREME_DAYS:
            void = "EXCLUDED_BY_C6"
        elif fold_of(days[d]) != fold_of(days[exit_]):
            void = "BOUNDARY_VOID_FOLD"
        if void:
            void_counts[void] = void_counts.get(void, 0) + 1
            continue
        episodes.append({"i": d, "d": d, "day": days[d], "sign": 1 if net[d] < 0 else -1,
                         "net": float(net[d]), "b": float(b[d]), "theta": theta,
                         "entry_idx": entry, "exit_idx": exit_, "fold": fold_of(days[d])})
        last_trigger = d
    return {"b": b, "episodes": episodes, "void_counts": void_counts,
            "crossing_candidates": candidates}


# ---------------------------------------------------------------------------
# frozen panel data (CADS objects; digests verified on load)
# ---------------------------------------------------------------------------

def slot_of(day: date, hour: int = 0) -> int:
    return (day - PANEL_FIRST).days * 24 + hour


class Panels:
    """Frozen S4 Binance H1 panels, read-only from content-addressed storage."""

    def __init__(self, store: Path):
        self.store = Path(store)
        self.consumed: list[dict] = []
        self.slot_close: dict[str, np.ndarray] = {}
        self.daily: dict[str, dict] = {}
        self._row_cache: dict[str, dict] = {}
        for sym in SYMBOLS:
            raw = self._read(CADS_DIGESTS[f"panel_{sym}_h1"])
            self._load_symbol(sym, raw)
        self.oi = self._load_oi(self._read(CADS_DIGESTS["oi_series_reduced"]))
        self.cascade = {s: self._build_cascade(s) for s in SYMBOLS}
        self.silres = {s: self._build_silres(s) for s in SYMBOLS}

    # -- io ---------------------------------------------------------------

    def _read(self, digest: str) -> bytes:
        p = self.store / "objects" / digest[:2] / digest
        raw = p.read_bytes()
        if sha256_bytes(raw) != digest:
            raise ValueError(f"digest mismatch on pinned object {digest[:12]}")
        if not any(c["object_sha256"] == digest for c in self.consumed):
            self.consumed.append({"object_sha256": digest, "bytes": len(raw),
                                  "path_readonly": str(p), "sha256_verified": True})
        return raw

    def _load_symbol(self, sym: str, raw: bytes) -> None:
        rows = list(csv.DictReader(raw.decode().splitlines()))
        closes = np.full(365 * 24, np.nan)
        gaps = np.zeros(365 * 24)
        ntr = np.zeros(365 * 24, dtype=int)
        firsts = np.zeros(365 * 24)
        agg: dict[date, dict] = {}
        for r in rows:
            if r["symbol"] != sym:
                raise ValueError(f"symbol mismatch in panel {sym}")
            day = date.fromisoformat(r["day_utc"])
            hour = int(r["hour_utc"][11:13])
            k = slot_of(day, hour)
            closes[k] = float(r["last_price"])
            gaps[k] = float(r["entry_gap_s"])
            ntr[k] = int(r["n_trades"])
            firsts[k] = float(r["first_price"])
            a = agg.setdefault(day, {"vwap_n": 0.0, "vwap_d": 0, "quote": 0.0,
                                     "n_trades": 0, "buy_qty": 0.0, "sell_qty": 0.0,
                                     "buy_count": 0, "max_run_buy": 0, "max_run_sell": 0,
                                     "elite": 0.0, "last": None})
            a["quote"] += float(r["quote_total"])
            a["n_trades"] += int(r["n_trades"])
            a["buy_qty"] += float(r["buy_qty"])
            a["sell_qty"] += float(r["sell_qty"])
            a["buy_count"] += int(r["buy_count"])
            a["max_run_buy"] = max(a["max_run_buy"], int(r["max_run_buy"]))
            a["max_run_sell"] = max(a["max_run_sell"], int(r["max_run_sell"]))
            a["elite"] += float(r["max_trade_quote"])
            a["vwap_n"] += float(r["vwap"]) * int(r["n_trades"])
            a["vwap_d"] += int(r["n_trades"])
            if hour == 23:
                a["last"] = float(r["last_price"])
        if np.isnan(closes).any():
            raise ValueError(f"non-contiguous hourly grid for {sym}")
        self.slot_close[sym] = closes
        self._row_cache[sym] = {"entry_gap_s": gaps, "n_trades": ntr, "first_price": firsts}
        daily = {}
        prev_close = None
        for d in sorted(agg):
            a = agg[d]
            ret = (a["last"] / prev_close - 1.0) if prev_close else None
            daily[d] = {
                "close": a["last"], "ret": ret,
                "logret": math.log(a["last"] / prev_close) if prev_close else None,
                "dvol": a["quote"], "n_trades": a["n_trades"],
                "buy_qty": a["buy_qty"], "sell_qty": a["sell_qty"],
                "buy_count": a["buy_count"],
                "max_run_buy": a["max_run_buy"], "max_run_sell": a["max_run_sell"],
                "elite": a["elite"],
                "vwap": a["vwap_n"] / a["vwap_d"] if a["vwap_d"] else float("nan"),
                "avg_ticket": a["quote"] / a["n_trades"] if a["n_trades"] else float("nan"),
            }
            prev_close = a["last"]
        self.daily[sym] = daily

    def _load_oi(self, raw: bytes) -> dict:
        d = json.loads(raw)
        if sorted(d) != sorted(SYMBOLS):
            raise ValueError("OI series symbols != frozen 3")
        self.consumed[-1]["geometry"] = "2904 H4 snapshots from 2025-04-25T00:00:00+00:00"
        return d

    # -- lookups ----------------------------------------------------------

    def close(self, sym: str, day: date) -> float:
        return self.daily[sym][day]["close"]

    def window_return(self, sym: str, d_entry: date, d_exit: date) -> float:
        """Entry close d_entry 23:00 -> exit close d_exit 23:00."""
        return self.close(sym, d_exit) / self.close(sym, d_entry) - 1.0

    def held_hour_returns(self, sym: str, d_entry: date, d_exit: date) -> tuple[np.ndarray, int, int]:
        """Hourly close-to-close returns strictly after the entry close through the
        exit close: slots [s_entry+1 .. s_exit] with s = slot(day, 23)."""
        c = self.slot_close[sym]
        a, b = slot_of(d_entry, 23), slot_of(d_exit, 23)
        r = c[a + 1:b + 1] / c[a:b] - 1.0
        return r, a + 1, b

    def hour_flags(self, sym: str, a: int, b: int) -> dict[str, np.ndarray]:
        """Precomputed flag arrays over slots [a..b] for the hour-grain shapes."""
        out: dict[str, np.ndarray] = {}
        for k in range(a, b + 1):
            day = PANEL_FIRST + timedelta(days=k // 24)
            hour = k % 24
            out.setdefault("v17_wkndliq_flag", []).append(
                -1.0 if (day.weekday() == 4 and hour >= 22) or day.weekday() >= 5 else 0.0)
            out.setdefault("generic_session_us", []).append(1.0 if 13 <= hour <= 21 else 0.0)
            out.setdefault("generic_session_eu", []).append(1.0 if 7 <= hour <= 15 else 0.0)
            out.setdefault("generic_session_asia", []).append(1.0 if 0 <= hour <= 7 else 0.0)
            out.setdefault("v17_oicascade_event", []).append(1.0 if self.cascade[sym][k] else 0.0)
            out.setdefault("v17_silres_event", []).append(float(self.silres[sym][k]))
        return {name: np.array(v) for name, v in out.items()}

    # -- silres (precomputed once per symbol) -------------------------------

    def _build_silres(self, sym: str) -> np.ndarray:
        """dir(b)*1[entry_gap_s >= Q90(prev720) and n_trades >= 1.5*median(prev720)]."""
        c = self.slot_close[sym]
        rows = self._row_cache[sym]
        gaps, ntr, firsts = rows["entry_gap_s"], rows["n_trades"], rows["first_price"]
        flags = np.zeros(c.size)
        for k in range(720, c.size):
            q90 = float(np.quantile(gaps[k - 720:k], 0.90))
            med = float(np.median(ntr[k - 720:k]))
            if gaps[k] >= q90 and ntr[k] >= 1.5 * med:
                dirn = c[k] - firsts[k]
                if dirn != 0:
                    flags[k] = 1.0 if dirn > 0 else -1.0
        return flags

    # -- oicascade (precomputed once per symbol) -----------------------------

    def _build_cascade(self, sym: str) -> np.ndarray:
        """+1 for the 24h following an H4 close whose 24h OI change <= P10 of the
        past 720 H4 changes AND 24h panel return < 0 (per-symbol)."""
        oi = np.asarray(self.oi[sym], dtype=float)
        n_h4 = oi.size
        chg = np.full(n_h4, np.nan)
        chg[6:] = oi[6:] / oi[:-6] - 1.0
        c = self.slot_close[sym]
        flags = np.zeros(c.size, dtype=bool)
        for k in range(726, n_h4):
            win = chg[k - 720:k]
            if np.isnan(win).any():
                continue
            p10 = float(np.quantile(win, 0.10))
            if not chg[k] <= p10:
                continue
            close_dt = OI_START + timedelta(hours=4 * (k + 1))
            prev_dt = close_dt - timedelta(hours=24)
            s_hi = int((close_dt - PANEL_FIRST_DT).total_seconds() // 3600) - 1
            s_lo = int((prev_dt - PANEL_FIRST_DT).total_seconds() // 3600) - 1
            if s_lo < 0 or s_hi >= c.size or s_hi - s_lo != 24:
                continue
            r24 = c[s_hi] / c[s_lo] - 1.0
            if r24 < 0:
                lo = s_hi + 1
                hi = min(s_hi + 24, c.size - 1)
                flags[lo:hi + 1] = True
        return flags


# ---------------------------------------------------------------------------
# day-level shape inventory (29-shape triad + NG2 funding-level additions)
# ---------------------------------------------------------------------------

def build_daily_shapes(panels: Panels) -> dict:
    """Day-level shape values per symbol per decision date D."""
    shapes = {s: {} for s in SYMBOLS}
    for s in SYMBOLS:
        daily = panels.daily[s]
        ds = sorted(daily)
        dvol = {d: daily[d]["dvol"] for d in ds}
        closes = {d: daily[d]["close"] for d in ds}
        for i, d in enumerate(ds):
            row = daily[d]
            v: dict[str, float] = {}
            v["v16_close_displace_fade"] = (row["close"] - row["vwap"]) / row["vwap"] if row["vwap"] else float("nan")
            rs = row["max_run_buy"] + row["max_run_sell"]
            v["v16_runpersist"] = (row["max_run_buy"] - row["max_run_sell"]) / rs if rs else float("nan")
            v["generic_tsmom28"] = (sum(math.log(closes[ds[k]] / closes[ds[k - 1]])
                                        for k in range(i - 27, i + 1)) if i >= 28 else float("nan"))
            v["generic_dvol_level_log"] = math.log(row["dvol"]) if row["dvol"] > 0 else float("nan")
            prev21 = [dvol[ds[k]] for k in range(max(0, i - 21), i)]
            v["generic_dvol_shock"] = row["dvol"] / float(np.median(prev21)) if prev21 else float("nan")
            bq, sq = row["buy_qty"], row["sell_qty"]
            v["v17proxy_run_imb"] = (bq - sq) / (bq + sq) if (bq + sq) else float("nan")
            v["v17proxy_taker_sat"] = row["buy_count"] / row["n_trades"] if row["n_trades"] else float("nan")
            v["v17proxy_ret"] = row["logret"] if row["logret"] is not None else float("nan")
            v["v17proxy_amihud"] = abs(row["ret"]) / row["dvol"] * 1e9 if row["ret"] and row["dvol"] else float("nan")
            prev60 = [daily[ds[k]]["avg_ticket"] for k in range(max(0, i - 60), i)
                      if not math.isnan(daily[ds[k]]["avg_ticket"])]
            med = float(np.median(prev60)) if prev60 else float("nan")
            v["v17proxy_avg_ticket_ratio"] = (row["avg_ticket"] / med
                                              if med and med > 0 and not math.isnan(row["avg_ticket"])
                                              else float("nan"))
            v["v17proxy_elite"] = row["elite"]
            for k in range(7):
                v[f"generic_dow_{k}"] = 1.0 if d.weekday() == k else 0.0
            v["generic_weekend_flag"] = 1.0 if d.weekday() >= 5 else 0.0
            v["v17_oi_level"] = float(panels.oi[s][slot_of(d, 23) // 4])
            v["v17_attn_phase"] = float("nan")
            v["v17_ticket_breadth"] = float("nan")
            shapes[s][d] = v
    # cross-symbol market-state series, day t-1 convention (single series per date)
    def session_counts(s: str, d: date) -> tuple[float, float]:
        n = panels._row_cache[s]["n_trades"]
        base = slot_of(d)
        us = tot = 0
        for h in range(24):
            k = base + h
            if k >= n.size:
                continue
            tot += int(n[k])
            if 14 <= h <= 21:
                us += int(n[k])
        return float(us), float(tot)

    majors = ["BTCUSDT", "ETHUSDT"]
    med_cache: dict[tuple, float] = {}
    for s in SYMBOLS:
        for d in sorted(panels.daily[s]):
            prev = d - timedelta(days=1)
            if prev < PANEL_FIRST:
                continue
            us1, tot1 = session_counts("SOLUSDT", prev)
            mj_us = mj_tot = 0.0
            for m in majors:
                u, t = session_counts(m, prev)
                mj_us += u
                mj_tot += t
            shapes[s][d]["v17_attn_phase"] = (us1 / tot1 - mj_us / mj_tot) if tot1 and mj_tot else float("nan")
            med = {}
            for x in SYMBOLS:
                ck = (x, prev)
                if ck not in med_cache:
                    pre = [panels.daily[x][k2]["avg_ticket"] for k2 in sorted(panels.daily[x])
                           if k2 < prev and not math.isnan(panels.daily[x][k2]["avg_ticket"])][-60:]
                    med_cache[ck] = float(np.median(pre)) if pre else float("nan")
                med[x] = med_cache[ck]
            rp = panels.daily["SOLUSDT"].get(prev)
            if rp and rp["n_trades"] and med["SOLUSDT"] and not math.isnan(med["SOLUSDT"]):
                num = rp["avg_ticket"] / med["SOLUSDT"]
                den = []
                for m in majors:
                    rpm = panels.daily[m].get(prev)
                    if rpm and rpm["n_trades"] and med[m] and not math.isnan(med[m]):
                        den.append(rpm["avg_ticket"] / med[m])
                shapes[s][d]["v17_ticket_breadth"] = num / (sum(den) / len(den)) if den else float("nan")
            else:
                shapes[s][d]["v17_ticket_breadth"] = float("nan")
    return shapes


# ---------------------------------------------------------------------------
# pooled same-bet books vs anchor book
# ---------------------------------------------------------------------------

def build_books(panels: Panels, decisions: list[dict], days: list[date],
                sign_key: str, shapes: dict, anchor_vec: dict, raw_vec: dict) -> dict:
    """shadow_book / anchor_book value pairs per shape over the anchor's rows.

    anchor_vec[(d, sym)] = sign * R_window (the anchor's book value);
    raw_vec[(d, sym)] = R_window (unsigned window return).  A day shape renders
    as shape_D * R_window; hour shapes compound flags over the held hourly
    returns; the anchor side is the signed book value.
    """
    acc: dict[str, tuple[list, list]] = {}
    for dec in decisions:
        d = dec["day"]
        d_entry, d_exit = days[dec["entry_idx"]], days[dec["exit_idx"]]
        for sym in SYMBOLS:
            key = (d, sym)
            if key not in anchor_vec:
                continue
            R_raw = raw_vec[key]
            A = anchor_vec[key]
            svals = shapes[sym].get(d, {})
            for name in ALL_DAY_SHAPES:
                val = svals.get(name, float("nan"))
                if isinstance(val, float) and math.isnan(val):
                    continue
                x, y = acc.setdefault(name, ([], []))
                x.append(val * R_raw)
                y.append(A)
            r, a, b = panels.held_hour_returns(sym, d_entry, d_exit)
            flags = panels.hour_flags(sym, a, b)
            for name in ALL_HOUR_SHAPES:
                fl = flags.get(name)
                if fl is None or fl.size != r.size:
                    continue
                x, y = acc.setdefault(name, ([], []))
                x.append(float(np.sum(fl * r)))
                y.append(A)
    return {name: (np.asarray(x), np.asarray(y)) for name, (x, y) in acc.items()}


# ---------------------------------------------------------------------------
# X3 tape-fitted issuance proxy (rule declared above)
# ---------------------------------------------------------------------------

def build_x3_proxy(panels: Panels) -> dict:
    P: dict[date, float] = {}
    tape: dict[str, dict] = {s: {} for s in SYMBOLS}
    for s in SYMBOLS:
        daily = panels.daily[s]
        ds = sorted(daily)
        for i, d in enumerate(ds):
            r = daily[d]["ret"]
            prev = [daily[ds[k]]["dvol"] for k in range(max(0, i - 60), i)]
            med = float(np.median(prev)) if prev else float("nan")
            if r is None or not med or med <= 0 or daily[d]["dvol"] <= 0 or math.isnan(med):
                tape[s][d] = float("nan")
            else:
                tape[s][d] = (1.0 if r > 0 else -1.0 if r < 0 else 0.0) * daily[d]["dvol"] / med
    for d in sorted(panels.daily["BTCUSDT"]):
        vals = [tape[s][d] for s in SYMBOLS if not math.isnan(tape[s].get(d, float("nan")))]
        P[d] = float(np.mean(vals)) if vals else float("nan")
    return P


def x3_books(panels: Panels, decisions: list[dict], days: list[date],
             sign_key: str, anchor_vec: dict, raw_vec: dict, P: dict) -> dict:
    x_state, y_state = [], []
    x_native, y_native = [], []
    for dec in decisions:
        d = dec["day"]
        sgn = dec[sign_key]
        d_entry, d_exit = days[dec["entry_idx"]], days[dec["exit_idx"]]
        held = [days[k] for k in range(dec["entry_idx"] + 1, dec["exit_idx"] + 1)]
        for sym in SYMBOLS:
            key = (d, sym)
            if key not in anchor_vec:
                continue
            R_raw = raw_vec[key]
            A = anchor_vec[key]
            if not math.isnan(P.get(d, float("nan"))):
                x_state.append(P[d] * R_raw)
                y_state.append(A)
            ok = True
            acc_p = 0.0
            for hd in held:
                row = panels.daily[sym].get(hd)
                if row is None or row["ret"] is None or math.isnan(P.get(hd, float("nan"))):
                    ok = False
                    break
                acc_p += P[hd] * row["ret"]
            if ok:
                x_native.append(acc_p)
                y_native.append(A)
    return {
        "proxy_state_held": rho_pair(x_state, y_state),
        "proxy_native_compound": rho_pair(x_native, y_native),
    }


def x3_diagnostics(days, net, P, episodes, decisions_a4) -> dict:
    panel_days = [d for d in days if d <= PANEL_LAST]
    net_by_day = dict(zip(days, net))
    pv = [P.get(d, float("nan")) for d in panel_days]
    nv = [float(net_by_day[d]) for d in panel_days]
    ok = [k for k in range(1, len(pv))
          if not (math.isnan(pv[k]) or math.isnan(pv[k - 1]))]
    vals = [1 if (P.get(ep["day"], float("nan")) < 0) == (ep["sign"] > 0) else 0
            for ep in episodes if not math.isnan(P.get(ep["day"], float("nan")))]
    vals4 = [1 if (P.get(dc["day"], float("nan")) > 0) == (dc["e"] > 0) else 0
             for dc in decisions_a4 if not math.isnan(P.get(dc["day"], float("nan")))]
    return {
        "rho_P_net_contemp": rho_pair([pv[k] for k in ok], [nv[k] for k in ok]),
        "rho_P_lag1_net": rho_pair([pv[k - 1] for k in ok], [nv[k] for k in ok]),
        "a5_episode_sign_agreement": {"n": len(vals),
                                      "frac": round(sum(vals) / len(vals), 6) if vals else None,
                                      "note": "A5 convention: +1 on net-burn bursts (net_d < 0)"},
        "a4_sign_agreement": {"n": len(vals4),
                              "frac": round(sum(vals4) / len(vals4), 6) if vals4 else None,
                              "note": "A4 declared identity: expansion -> long"},
    }


# ---------------------------------------------------------------------------
# X5 nulls
# ---------------------------------------------------------------------------

def _with_valid(p: dict) -> dict:
    """Q-11 explicit verdict on a null row: |rho| < identifiability bar."""
    out = dict(p)
    if p.get("max_abs_rho") is None:
        out["valid"] = None
    else:
        out["valid"] = bool(p["max_abs_rho"] < IDENTIFIABILITY_BAR)
    return out


def a4_delayed_null(a4, decisions, anchor_vec, raw_vec, k: int) -> dict:
    x, y = [], []
    for dec in decisions:
        i_src = dec["i"] - k
        e_src = int(a4["e"][i_src]) if i_src >= 0 and a4["decidable"][i_src] else 0
        for sym in SYMBOLS:
            key = (dec["day"], sym)
            if key not in anchor_vec:
                continue
            x.append(e_src * raw_vec[key])
            y.append(anchor_vec[key])
    return _with_valid(rho_pair(x, y))


def a4_shuffled_null(a4, decisions, anchor_vec, raw_vec,
                     n_draws=N_SHUFFLES, seed=SHUFFLE_SEED) -> dict:
    rng = np.random.default_rng(seed)
    months: dict[str, list[int]] = {}
    for dec in decisions:
        months.setdefault(dec["day"].strftime("%Y-%m"), []).append(dec["i"])
    e_by_idx = {dec["i"]: int(dec["e"]) for dec in decisions}
    n_nonflat = sum(1 for dec in decisions if dec["e"] != 0)
    rhos, agreements = [], []
    for _ in range(n_draws):
        e_perm = dict(e_by_idx)
        for idxs in months.values():
            vals = [e_by_idx[i] for i in idxs]
            perm = rng.permutation(len(idxs))
            for j, i in enumerate(idxs):
                e_perm[i] = vals[perm[j]]
        x, y, agree, tot = [], [], 0, 0
        for dec in decisions:
            for sym in SYMBOLS:
                key = (dec["day"], sym)
                if key not in anchor_vec:
                    continue
                ep = e_perm[dec["i"]]
                x.append(ep * raw_vec[key])
                y.append(anchor_vec[key])
                agree += int(ep != 0 and ep == dec["e"])
                tot += int(ep != 0)
        p = rho_pair(x, y)
        if p["max_abs_rho"] is not None:
            rhos.append(p["max_abs_rho"])
            agreements.append(agree / max(1, tot))
    max_rho = max(rhos) if rhos else None
    out = {"n_draws": n_draws, "seed": seed,
           "max_abs_rho": round(max_rho, 6) if max_rho is not None else None,
           "mean_abs_rho": round(float(np.mean(rhos)), 6) if rhos else None,
           "direction_agreement_mean": round(float(np.mean(agreements)), 6) if agreements else None}
    out["valid"] = bool(max_rho is not None and max_rho < IDENTIFIABILITY_BAR)
    return out


def a5_delayed_null(panels, days, episodes, anchor_vec, raw_vec, k: int) -> dict:
    x, y = [], []
    for ep in episodes:
        for sym in SYMBOLS:
            key = (ep["day"], sym)
            if key not in anchor_vec:
                continue
            e2, x2 = ep["entry_idx"] + k, ep["exit_idx"] + k
            if x2 > len(days) - 1 or days[x2] > PANEL_LAST or days[x2] == MARGIN_DAY:
                val = 0.0
            else:
                val = ep["sign"] * panels.window_return(sym, days[e2], days[x2])
            x.append(val)
            y.append(anchor_vec[key])
    return _with_valid(rho_pair(x, y))


def a5_shuffled_null(panels, days, episodes, anchor_vec, raw_vec,
                     n_draws=N_SHUFFLES, seed=SHUFFLE_SEED) -> dict:
    rng = np.random.default_rng(seed)
    decidable = [i for i, d in enumerate(days)
                 if PANEL_FIRST <= d <= PANEL_LAST and d not in NET_EXTREME_DAYS
                 and i + A5_HOLD + 1 <= len(days) - 1
                 and days[i + A5_HOLD + 1] <= PANEL_LAST and days[i + A5_HOLD + 1] != MARGIN_DAY]
    months: dict[str, list[int]] = {}
    for i in decidable:
        months.setdefault(days[i].strftime("%Y-%m"), []).append(i)
    ep_by_month: dict[str, list] = {}
    for ep in episodes:
        ep_by_month.setdefault(ep["day"].strftime("%Y-%m"), []).append(ep)
    rhos = []
    for _ in range(n_draws):
        null_days: dict[int, int] = {}
        for m, eps in ep_by_month.items():
            pool = months.get(m, [])
            if not pool:
                continue
            k = min(len(eps), len(pool))
            picks = rng.choice(len(pool), size=k, replace=False)
            signs = [ep["sign"] for ep in rng.permutation(eps)]
            for j, pj in enumerate(picks):
                null_days[pool[pj]] = signs[j]
        x, y = [], []
        for ep in episodes:
            for sym in SYMBOLS:
                key = (ep["day"], sym)
                if key not in anchor_vec:
                    continue
                sgn = null_days.get(ep["i"])
                if sgn is None:
                    val = 0.0
                else:
                    val = sgn * raw_vec[key]
                x.append(val)
                y.append(anchor_vec[key])
        p = rho_pair(x, y)
        if p["max_abs_rho"] is not None:
            rhos.append(p["max_abs_rho"])
    max_rho = max(rhos) if rhos else None
    out = {"n_draws": n_draws, "seed": seed,
           "max_abs_rho": round(max_rho, 6) if max_rho is not None else None,
           "mean_abs_rho": round(float(np.mean(rhos)), 6) if rhos else None}
    out["valid"] = bool(max_rho is not None and max_rho < IDENTIFIABILITY_BAR)
    return out


# ---------------------------------------------------------------------------
# calendar geometry (X4 diagnostics; binding bar = clock-shape rho)
# ---------------------------------------------------------------------------

def calendar_geometry(decisions, episodes) -> dict:
    def by_weekday(rows):
        out = {k: 0 for k in range(7)}
        for r in rows:
            out[r["day"].weekday()] += 1
        return out
    return {
        "a4_eligible_decisions_by_weekday": by_weekday(decisions),
        "a5_traded_episodes_by_weekday": by_weekday(episodes),
        "note": ("calendar-distribution diagnostics; the binding X4 bar is the "
                 "pooled rho of the clock-only shapes (dow/session/wkndliq) vs "
                 "the anchor book at |rho| > 0.20"),
    }


# ---------------------------------------------------------------------------
# verdict assembly
# ---------------------------------------------------------------------------

def worst_row(table: dict, names: list[str]) -> tuple[dict | None, str | None]:
    worst, worst_name = None, None
    for name in names:
        row = table.get(name)
        if row is None or row["max_abs_rho"] is None:
            continue
        if worst is None or row["max_abs_rho"] > worst["max_abs_rho"]:
            worst, worst_name = row, name
    return worst, worst_name


def veto_x1(table: dict) -> dict:
    measured = {k: v for k, v in table.items() if v["max_abs_rho"] is not None}
    vetoed = {k: v for k, v in measured.items() if v["status"] == "VETO"}
    worst, worst_name = worst_row(table, list(measured))
    out = {
        "inventory_total": 30,
        "measured_shapes": len(measured),
        "blocked_shapes": BLOCKED_SHAPES,
        "blocked_reason": BLOCKED_LEG_REASON,
        "vetoed_shapes": {k: v for k, v in vetoed.items()},
        "worst_measured": {"shape": worst_name, **(worst or {})},
    }
    if vetoed:
        out["verdict"] = "KILL"
        out["margin"] = round(RHO_BAR - worst["max_abs_rho"], 6)
    else:
        out["verdict"] = "NOT_RUN_BLOCKED_PARTIAL"
        out["margin"] = round(RHO_BAR - (worst["max_abs_rho"] or 0.0), 6)
        out["fail_closed_note"] = ("all measured legs under the 0.20 bar; 2 "
                                   "funding-level legs NOT_RUN_BLOCKED -> cannot "
                                   "be claimed SURVIVE (fail-closed)")
    return out


def veto_x2(table: dict) -> dict:
    sub = {k: table.get(k) for k in DEAD_OI_SHAPES}
    out = {"oilev_v2_and_dead_form_envelope": sub,
           "funding_level_legs": {k: {"status": "NOT_RUN_BLOCKED",
                                      "reason": BLOCKED_LEG_REASON}
                                  for k in BLOCKED_SHAPES}}
    vetoed = [k for k, v in sub.items() if v and v["status"] == "VETO"]
    worst, worst_name = worst_row(table, DEAD_OI_SHAPES)
    out["worst_measured"] = {"shape": worst_name, **(worst or {})}
    if vetoed:
        out["verdict"] = "KILL"
        out["margin"] = round(RHO_BAR - worst["max_abs_rho"], 6)
    else:
        out["verdict"] = "NOT_RUN_BLOCKED_PARTIAL"
        out["margin"] = round(RHO_BAR - (worst["max_abs_rho"] or 0.0), 6)
    return out


def veto_x3(x3: dict, diag: dict | None = None) -> dict:
    worst = None
    for key in ("proxy_state_held", "proxy_native_compound"):
        p = x3[key]
        if p["max_abs_rho"] is not None and (worst is None or p["max_abs_rho"] > worst["max_abs_rho"]):
            worst = p
    out = {"rule": X3_RULE_DECLARED, **x3,
           "diagnostics_non_binding": diag or {}}
    if worst is None or worst["status"].startswith("UNMEASURED"):
        out["verdict"] = "UNMEASURED"
        out["margin"] = None
        return out
    if worst["status"] == "VETO":
        out["verdict"] = "KILL"
        out["margin"] = round(RHO_BAR - worst["max_abs_rho"], 6)
    else:
        out["verdict"] = "SURVIVE"
        out["margin"] = round(RHO_BAR - worst["max_abs_rho"], 6)
    return out


def veto_x4(table: dict, cal: dict) -> dict:
    worst, worst_name = worst_row(table, CLOCK_SHAPES)
    out = {"clock_shapes": {k: table.get(k) for k in CLOCK_SHAPES},
           "calendar_geometry": cal,
           "worst_measured": {"shape": worst_name, **(worst or {})}}
    if worst is None:
        out["verdict"] = "UNMEASURED"
        out["margin"] = None
        return out
    if worst["status"] == "VETO":
        out["verdict"] = "KILL"
        out["margin"] = round(RHO_BAR - worst["max_abs_rho"], 6)
    else:
        out["verdict"] = "SURVIVE"
        out["margin"] = round(RHO_BAR - worst["max_abs_rho"], 6)
    return out


def veto_x5(nulls: dict) -> dict:
    out = {"nulls": nulls, "identifiability_bar": IDENTIFIABILITY_BAR}
    invalid = [k for k, v in nulls.items() if v.get("valid") is False]
    unmeasured = [k for k, v in nulls.items() if v.get("valid") is None]
    if invalid:
        out["verdict"] = "INVALID_NULL_KILL"
        out["margin"] = round(IDENTIFIABILITY_BAR - max(v["max_abs_rho"] or 0 for k, v in nulls.items() if v.get("valid") is False), 6)
        out["invalid_nulls_explicit"] = invalid
    elif unmeasured:
        out["verdict"] = "UNMEASURED"
        out["margin"] = None
        out["unmeasured_nulls"] = unmeasured
    else:
        worst = max(v["max_abs_rho"] for v in nulls.values())
        out["verdict"] = "VALID_NULL_SURVIVE"
        out["margin"] = round(IDENTIFIABILITY_BAR - worst, 6)
    return out


def veto_f1(measured_rts_per_year: float, declared: dict) -> dict:
    raw_annual_bps = round(F1_ROUND_TRIP_BPS * measured_rts_per_year, 4)
    return {
        "tier": F1_TIER,
        "round_trip_bps_frozen_band": F1_ROUND_TRIP_BPS,
        "band_source": F1_BAND_SOURCE,
        "declared_turnover": declared,
        "measured_round_trips_per_year": round(measured_rts_per_year, 4),
        "raw_book_annual_ceiling_bps": raw_annual_bps,
        "financing_adjusted_book": {"status": "NOT_RUN_BLOCKED",
                                    "reason": BLOCKED_LEG_REASON},
        "verdict": "NOT_RUN_BLOCKED_PARTIAL",
        "margin_note": ("raw book ceiling measured and chargeable within the "
                        "frozen band; the financing-adjusted book needs the "
                        "frozen funding series (blocked) -> fail-closed; the "
                        "cost-vs-edge adjudication is the scoring lane's gate "
                        "and is NOT computed here (outcome-leak ban)"),
    }


def q6_population(decisions, episodes, n_decidable_a4: int) -> dict:
    def counts(rows):
        out = {}
        for r in rows:
            out[r["fold"]] = out.get(r["fold"], 0) + 1
        return {f: out.get(f, 0) for f in ("fold1", "fold2", "fold3")}
    rec_dec = [r for r in decisions if Q6_RECENT_WINDOW[0] <= r["day"] <= Q6_RECENT_WINDOW[1]]
    rec_ep = [r for r in episodes if Q6_RECENT_WINDOW[0] <= r["day"] <= Q6_RECENT_WINDOW[1]]
    return {
        "recent_window_definition": f"last 6 calendar months {Q6_RECENT_WINDOW[0]}..{Q6_RECENT_WINDOW[1]}",
        "a4": {"per_fold_eligible_decisions": counts(decisions),
               "per_fold_floor": A4_FOLD_FLOOR,
               "decidable_days_total_state_incl_margin": n_decidable_a4,
               "recent_window_eligible": len(rec_dec)},
        "a5": {"per_fold_traded_episodes": counts(episodes),
               "per_fold_floor": A5_FOLD_FLOOR,
               "recent_window_episodes": len(rec_ep)},
    }


def c6_strata(days, decisions, episodes, a5_voids) -> dict:
    ex_dec = [r for r in decisions if r["day"] in NET_EXTREME_DAYS]
    return {
        "net_extreme_days_frozen": sorted(str(d) for d in NET_EXTREME_DAYS),
        "exclusion_rule": ("days carrying a C6 NET_EXTREME flag are excluded from "
                           "D2 training/validation but retained in the census"),
        "a4_decisions_on_excluded_days": len(ex_dec),
        "a5_triggers_voided_by_c6": a5_voids.get("EXCLUDED_BY_C6", 0),
        "usdt_eth_zero_event_days": USDT_ETH_ZERO_EVENT_DAYS,
        "usdt_eth_stratum_note": ("declared sparse stratum; never zero-imputed; "
                                  "not in the anchor (USDC-ETHEREUM only)"),
        "cctp_stratum": "present (frozen minter_table.json; declared stratum, never silently netted)",
    }
