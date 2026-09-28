"""Shared Portfolio 100K — V1 engine (epoch-2 design, PREVIEW only).

Owner directive 2026-09-25: ONE shadow portfolio with a single
100,000 USD-equivalent opening equity, replacing the per-sleeve-100k
model (PSCTV1 A1 2026-09-24) FROM A NEW ACTIVATION TIMESTAMP ONLY.

HARD LAWS (owner order, binding on this code):
- Epoch-1 journals/ledgers are append-only evidence. This module NEVER
  writes to any epoch-1 file; it only reads and hashes them.
- No epoch-1 PnL carries into epoch-2. No backfill. Epoch 2 is NOT a
  continuation of any epoch-1 track.
- Cutover is BLOCKED until the owner GO + open-position law + allocation
  are recorded in epoch_config.json (status ACTIVE) by the operator.
  Until then everything built here is labelled PREVIEW.
- Restart/replay idempotence: every derived number is recomputed from
  the immutable sources with deterministic dedup — running this twice
  must produce byte-identical output (tests pin this).
- USD and USDT are separate books joined ONLY by the declared
  usdt_usd_ref rate; this is a simulated paper portfolio, never a real
  broker account, and no transferability is assumed.
- Missing/corrupt data is UNAVAILABLE, never $0.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

SCHEMA = "shared_portfolio.portfolio_state@1"
CAL_SCHEMA = "shared_portfolio.pnl_calendar@1"

ROOT = Path("/Users/hoangminhlong/my-quantitative")
FX_DIR = ROOT / ".worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1"
PSV1_RESULTS = ROOT / ".worktrees/prospective-shadow-v1/integration/results/prospective_shadow_v1"
HERE = Path(__file__).resolve().parent
# frozen .app builds bundle a copy; the live config is the repo file
CONFIG_FALLBACK = ROOT / "research/control/SHARED-PORTFOLIO-100K-V1/epoch_config.json"

FX_PIP = 1e-4
FX_PIP_VALUE_PER_LOT = 10.0        # USD per pip per 1.0 lot (USD-quote majors)
FX_CONTRACT_UNITS = 100_000        # units of base ccy per lot
UNAVAILABLE = "UNAVAILABLE"
RECON_TOL_USD = 0.05               # decomposition residual tolerance

CRYPTO_SLEEVES = ["BTC4H-BANDRIDGE", "BASISLV-PREMFADE-28D",
                  "ILLIQ-AMIHUD-28D-W", "XSECT-FUND-CARRY-7D"]


# ----------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------
def sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def read_jsonl(path: Path) -> List[dict]:
    """Tolerant JSONL read: a partial trailing line (worker mid-append)
    is skipped, never fatal, never half-counted."""
    out: List[dict] = []
    try:
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
    except OSError:
        pass
    return out


def read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def day_key(ts_iso: str) -> str:
    """UTC day key from an ISO timestamp (first 10 chars, ISO-8601 UTC)."""
    return str(ts_iso)[:10]


def week_key(day: str) -> str:
    d = datetime.fromisoformat(day + "T00:00:00+00:00").date()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def month_key(day: str) -> str:
    return day[:7]


# ----------------------------------------------------------------------
# FX sleeve: replay the immutable shadow_journal.jsonl
# ----------------------------------------------------------------------
def fx_replay(journal_path: Path) -> Dict[str, Any]:
    """Deterministic replay of the FX journal (same dedup keys as the
    daemon's fx_shadow_core.replay_journal so a daemon restart can never
    double-count, and re-reading here can never invent a trade).

    Returns trades (closed round trips), open positions, realized by
    UTC day per pair, and integrity counters."""
    trades: List[dict] = []
    seen: set = set()
    realized_by_day: Dict[str, Dict[str, float]] = {}
    open_pos: Dict[str, dict] = {}
    fills_by_day: Dict[str, Dict[str, int]] = {}
    counters = {"events_read": 0, "events_bad": 0, "events_dup": 0}
    marks_last: Dict[str, dict] = {}

    for rec in read_jsonl(journal_path):
        counters["events_read"] += 1
        event = rec.get("event")
        if event in ("parity_selftest", "shadow_start", "boot_replay",
                     "day_roll", "day_anchor", "seq_probe"):
            continue  # meta events — never trades
        pair = str(rec.get("pair") or "")
        if event in ("fill_open",):
            if not pair:
                counters["events_bad"] += 1
                continue
            key = ("open", pair, rec.get("entry_ts"), rec.get("entry_px"))
            if key in seen:
                counters["events_dup"] += 1
                continue
            seen.add(key)
            open_pos[pair] = {
                "dir": int(rec.get("dir") or 0),
                "entry_px": rec.get("entry_px"),
                "entry_ts": rec.get("entry_ts"),
                "lots": rec.get("lots"),
            }
        elif event in ("fill_close", "force_flat"):
            if not pair:
                counters["events_bad"] += 1
                continue
            key = ("close", pair, rec.get("ts"), rec.get("exit_px"))
            if key in seen:
                counters["events_dup"] += 1
                continue
            seen.add(key)
            pnl = float(rec.get("pnl_usd") or 0.0)
            ts = str(rec.get("ts") or "")
            day = day_key(ts)
            realized_by_day.setdefault(day, {}).setdefault(pair, 0.0)
            realized_by_day[day][pair] += pnl
            fills_by_day.setdefault(day, {}).setdefault(pair, 0)
            fills_by_day[day][pair] += 1
            trades.append({
                "sleeve": "FX-RANGEFADE-2M", "pair": pair, "day_utc": day,
                "close_ts_utc": ts, "kind": event,
                "dir": int(rec.get("dir") or 0),
                "entry_px": rec.get("entry_px"), "exit_px": rec.get("exit_px"),
                "lots": rec.get("lots"), "pnl_usd": round(pnl, 2),
                "reason": rec.get("reason") or ("force-flat 20:00 UTC" if event == "force_flat" else ""),
            })
            open_pos.pop(pair, None)
        elif event == "bar_closed":
            if not pair:
                counters["events_bad"] += 1
                continue
            key = ("bar", pair, rec.get("bar_ts"))
            if key in seen:
                counters["events_dup"] += 1
                continue
            seen.add(key)
            marks_last[pair] = {"b_c": rec.get("b_c"), "bar_ts": rec.get("bar_ts")}
        else:
            counters["events_bad"] += 1

    realized_total = sum(sum(p.values()) for p in realized_by_day.values())
    trades.sort(key=lambda t: (t["close_ts_utc"], t["pair"]))
    return {
        "trades": trades,
        "open_positions": open_pos,
        "realized_usd": round(realized_total, 2),
        "realized_by_day": {d: dict(p) for d, p in sorted(realized_by_day.items())},
        "fills_by_day": fills_by_day,
        "integrity": counters,
    }


# ----------------------------------------------------------------------
# crypto sleeves: daily series from valuation marks (append-only)
# ----------------------------------------------------------------------
def crypto_daily_series(marks_path: Path) -> Dict[str, Any]:
    """One row per UTC day that HAS a mark: last mark of the day vs last
    mark of the previous available day.

    day_pnl = Δequity (authoritative). The decomposition
    (Δrealized + Δunrealized − Δfees − Δslippage + Δfunding) is CHECKED
    against Δequity; on |residual| > tolerance the day is flagged
    RECON_FAIL and the decomposition is withheld (fail-closed), while
    Δequity stays visible with the warning.

    A UTC day with NO mark on either boundary of its Δ is UNAVAILABLE —
    never $0. The Δ that spans a gap is attached to the day of the LATER
    mark and labelled GAP_SPAN with the gap length."""
    marks = read_jsonl(marks_path)
    per_day: Dict[str, dict] = {}
    file_first: Optional[dict] = None
    for m in marks:
        ts = str(m.get("mark_timestamp_utc") or m.get("observed_at_utc") or "")
        if not ts:
            continue
        if file_first is None and isinstance(m.get("equity"), (int, float)):
            file_first = m | {"mark_ts": ts}
        d = day_key(ts)
        prev = per_day.get(d)
        if prev is None or ts >= prev["mark_ts"]:
            per_day[d] = m | {"mark_ts": ts}
    days = sorted(per_day)
    rows: List[dict] = []
    prev: Optional[dict] = None
    for d in days:
        cur = per_day[d]
        eq = cur.get("equity")
        if prev is None:
            # earliest day in the file: attribute from the FILE's first mark
            # (same day by construction); anything before it is pre-history
            if (file_first is not None and day_key(file_first["mark_ts"]) == d
                    and isinstance(eq, (int, float))):
                first_eq = file_first["equity"]
                if abs(eq - first_eq) <= 1e-9:
                    rows.append({"day_utc": d, "status": "BASELINE", "equity": eq,
                                 "mark_ts": cur["mark_ts"]})
                else:
                    rows.append({
                        "day_utc": d, "status": "PARTIAL_OPEN",
                        "equity": eq, "day_pnl": round(eq - first_eq, 2),
                        "reason": ("baseline = first mark of the file inside this day; "
                                   "activity before that mark is not attributable to any day"),
                        "decomposition": None, "mark_ts": cur["mark_ts"]})
            else:
                rows.append({"day_utc": d, "status": "BASELINE", "equity": eq,
                             "mark_ts": cur["mark_ts"]})
            prev = cur
            continue
        eq_prev = prev.get("equity")
        if not (isinstance(eq, (int, float)) and isinstance(eq_prev, (int, float))):
            rows.append({"day_utc": d, "status": UNAVAILABLE,
                         "reason": "missing numeric equity on boundary mark",
                         "mark_ts": cur["mark_ts"]})
            prev = cur
            continue

        def delta(field: str) -> Optional[float]:
            a, b = prev.get(field), cur.get(field)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                return b - a
            return None

        day_pnl = eq - eq_prev
        d_real, d_unreal = delta("realized_pnl"), delta("unrealized_pnl")
        d_fees, d_fund = delta("fees"), delta("funding")
        d_slip = delta("slippage")
        status = "OK"
        decomposition = None
        if None not in (d_real, d_unreal, d_fees, d_fund):
            # Verified identity of the PSV1 valuation worker (tests pin it):
            #   equity = seed + realized_pnl + unrealized_pnl - fees + funding
            # slippage is tracked as an INFORMATIONAL column (already embedded
            # in avg_price); it is NOT a separate equity deduction.
            residual = day_pnl - (d_real + d_unreal - d_fees + d_fund)
            if abs(residual) <= RECON_TOL_USD:
                decomposition = {
                    "realized": round(d_real, 2), "unrealized_change": round(d_unreal, 2),
                    "fees": round(-d_fees, 2), "funding": round(d_fund, 2),
                    "slippage_info": round(-d_slip, 2) if d_slip is not None else None,
                    "residual_usd": round(residual, 4),
                }
            else:
                status = "RECON_FAIL"
        else:
            status = "PARTIAL_DECOMPOSITION"
        gap_hours = None
        t0 = _parse_utc(prev["mark_ts"])
        t1 = _parse_utc(cur["mark_ts"])
        # daily-boundary marks are naturally ~24h apart; only a boundary
        # gap beyond 26h means marks are actually MISSING in between —
        # that is the headline fact, so it overrides the softer
        # partial-decomposition label (RECON_FAIL stays strongest)
        if t0 and t1 and (t1 - t0) > timedelta(hours=26):
            gap_hours = round((t1 - t0).total_seconds() / 3600.0, 1)
            if status in ("OK", "PARTIAL_DECOMPOSITION"):
                status = "GAP_SPAN"
        positions = cur.get("positions") or []
        rows.append({
            "day_utc": d, "status": status, "equity": eq,
            "equity_prev": eq_prev, "day_pnl": round(day_pnl, 2),
            "decomposition": decomposition,
            "unrealized_eod": round(sum(
                (p.get("unrealized_pnl") or 0.0) for p in positions), 2) if positions else 0.0,
            "gross_notional": round(sum(
                abs(p.get("notional") or 0.0) for p in positions), 2) if positions else 0.0,
            "n_positions": len(positions),
            "mark_ts": cur["mark_ts"], "gap_span_hours": gap_hours,
        })
        prev = cur
    return {"rows": rows, "n_marks": len(marks),
            "last_mark": marks[-1] if marks else None}


def _parse_utc(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


# ----------------------------------------------------------------------
# portfolio assembly
# ----------------------------------------------------------------------
def _epoch2_block(fx: Dict[str, Any], crypto: Dict[str, Any],
                  cfg: Mapping[str, Any]) -> Dict[str, Any]:
    """Post-activation epoch-2 aggregation. Inert while PREVIEW.

    FX: journal closes at/after T_STAR (journal replay is already
    deduped). Crypto: baseline = the sleeve's first mark at/after
    T_STAR, last = latest such mark; PnL splits exactly at those marks.
    The operator's epoch-boundary rows remain the authoritative record
    of carried positions; this block never carries epoch-1 PnL."""
    ts = cfg.get("activation_ts_utc")
    if not ts:
        return {"pnl_total": None, "equity": None, "status": "NOT_ACTIVATED",
                "note": ("epoch-2 PnL không tồn tại trước owner GO; không backfill, "
                         "không chuyển kết quả cũ vào kỳ mới")}
    t0 = _parse_utc(str(ts))
    fx_trades = [t for t in fx["trades"]
                 if (_parse_utc(t["close_ts_utc"]) or t0) >= t0]
    fx_pnl = round(sum(t["pnl_usd"] for t in fx_trades), 2)
    sleeves: Dict[str, Any] = {}
    total = float(fx_pnl)
    for fam in CRYPTO_SLEEVES:
        marks = read_jsonl(PSV1_RESULTS / f"valuation_marks/{fam}.jsonl")
        stampeds = []
        for m in marks:
            mts = _parse_utc(str(m.get("mark_timestamp_utc")
                                 or m.get("observed_at_utc") or ""))
            if mts and mts >= t0 and isinstance(m.get("equity"), (int, float)):
                stampeds.append((mts, m["equity"]))
        if not stampeds:
            sleeves[fam] = {"pnl": None, "status": UNAVAILABLE,
                            "reason": "no mark at/after T_STAR yet"}
            continue
        base_eq = stampeds[0][1]
        last_eq = stampeds[-1][1]
        pnl = round(last_eq - base_eq, 2)
        total += last_eq - base_eq
        sleeves[fam] = {
            "pnl": pnl, "status": "OK",
            "baseline_mark_utc": stampeds[0][0].isoformat(),
            "note": "baseline = mark đầu tiên ≥ T_STAR; boundary row của operator là authority",
        }
    opening = float(cfg.get("opening_equity_usd_eq") or 100000.0)
    return {
        "activation_ts_utc": ts, "status": "ACTIVE",
        "opening_equity_usd_eq": opening,
        "pnl_total": round(total, 2), "equity": round(opening + total, 2),
        "fx_realized": fx_pnl, "fx_trades": len(fx_trades),
        "sleeves": sleeves,
        "note": "chỉ tính dữ liệu từ T_STAR trở đi; không carry PnL cũ, không backfill",
    }


def _validate_activation(cfg: Mapping[str, Any]) -> Tuple[dict, Optional[str]]:
    """Fail-closed activation gate (reviewer finding: a bare status flip
    must never activate). ACTIVE is honored ONLY when every owner GO
    field is present and internally consistent; otherwise the engine
    coerces to PREVIEW and reports why."""
    cfg = dict(cfg or {})
    if cfg.get("status") != "ACTIVE":
        return cfg, None
    problems = []
    ts = cfg.get("activation_ts_utc")
    if not ts or _parse_utc(str(ts)) is None:
        problems.append("activation_ts_utc missing/invalid ISO-8601")
    if cfg.get("open_position_law") not in ("FLAT_START", "REOPEN_AT_MARK"):
        problems.append("open_position_law not chosen (PENDING_OWNER)")
    alloc = cfg.get("allocation") or {}
    if alloc.get("mode") not in ((cfg.get("allocation") or {}).get("options") or {}):
        problems.append("allocation.mode not chosen (OWNER_DECISION)")
    if not cfg.get("rule_digest"):
        problems.append("rule_digest missing (freeze capital_rule + hash at GO)")
    if not cfg.get("review_log_sha256"):
        problems.append("review_log_sha256 missing (independent review not recorded)")
    if problems:
        cfg["status"] = "PREVIEW_FORCED"
        return cfg, "; ".join(problems)
    return cfg, None


def build_state(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Build the full PREVIEW portfolio state from the immutable sources.

    PREVIEW semantics (activation_ts is null until owner GO):
      - epoch-2 PnL/equity are NOT computed (would be invented) — they
        are reported as NOT_ACTIVATED.
      - epoch-1 streams are fully computed and clearly labelled epoch-1.
    """
    cfg, activation_error = _validate_activation(read_json(
        config_path or (HERE / "epoch_config.json")
        if (HERE / "epoch_config.json").exists() else CONFIG_FALLBACK))
    active = cfg.get("status") == "ACTIVE" and activation_error is None
    fx = fx_replay(FX_DIR / "shadow_journal.jsonl")
    fx_state = read_json(FX_DIR / "shadow_state.json") or {}
    crypto: Dict[str, Any] = {}
    for fam in CRYPTO_SLEEVES:
        crypto[fam] = crypto_daily_series(PSV1_RESULTS / f"valuation_marks/{fam}.jsonl")

    # ---- epoch-1 daily portfolio table (history view; USD-eq) ----------
    all_days = sorted(set(fx["realized_by_day"]) |
                      {r["day_utc"] for fam in crypto.values()
                       for r in fam["rows"] if r.get("day_utc")})
    history_days: List[dict] = []
    fx_cum = 100000.0  # FX book is flat at each 20:00 UTC force-flat boundary
    for d in all_days:
        row: Dict[str, Any] = {"day_utc": d, "sleeves": {}, "status": "OK"}
        total = 0.0
        fx_pairs = fx["realized_by_day"].get(d, {})
        n_rt = sum(fx["fills_by_day"].get(d, {}).values())
        fx_first_day = min(fx["realized_by_day"]) if fx["realized_by_day"] else None
        fx_status = "OK" if fx_pairs else (
            "NO_TRADE" if (fx_first_day and d >= fx_first_day) else "NOT_MOUNTED")
        fx_day_realized = round(sum(fx_pairs.values()), 2)
        fx_cum = round(fx_cum + fx_day_realized, 2)
        row["sleeves"]["FX-RANGEFADE-2M"] = {
            "day_realized_usd": fx_day_realized,
            "round_trips": n_rt,
            "status": fx_status,
            "equity_eod": fx_cum if (fx_first_day and d >= fx_first_day) else None,
        }
        total += fx_day_realized
        for fam in CRYPTO_SLEEVES:
            r = next((x for x in crypto[fam]["rows"] if x.get("day_utc") == d), None)
            if r is None:
                row["sleeves"][fam] = {"day_pnl": None, "status": UNAVAILABLE,
                                       "equity_eod": None,
                                       "reason": "no valuation mark on this UTC day boundary"}
                row["status"] = "PARTIAL"
            else:
                row["sleeves"][fam] = {"day_pnl": r.get("day_pnl"),
                                       "status": r.get("status"),
                                       "decomposition": r.get("decomposition"),
                                       "equity_eod": r.get("equity")}
                if r.get("status") not in ("OK", "BASELINE", "GAP_SPAN", "PARTIAL_OPEN"):
                    row["status"] = "PARTIAL"
                if r.get("day_pnl") is not None:
                    total += r["day_pnl"]
        row["total_day_pnl_usd_eq"] = round(total, 2)
        history_days.append(row)

    # ---- live sleeves (epoch-1 books, display-only) --------------------
    sleeves: Dict[str, Any] = {}
    usdt_ref = float((cfg.get("usdt_usd_ref") or {}).get("rate", 1.0))

    fx_acc = fx_state.get("account") or {}
    sleeves["FX-RANGEFADE-2M"] = {
        "currency": "USD", "epoch1_equity": fx_acc.get("equity"),
        "epoch1_realized": fx_acc.get("realized_usd"),
        "epoch1_unrealized": fx_acc.get("unrealized_usd"),
        "gross_notional": fx_acc.get("gross_exposure_usd"),
        "fees": UNAVAILABLE, "fees_note": "FX journal has no fee/slippage/funding fields — all FX PnL is GROSS/HYPOTHETICAL, never net",
        "positions": fx["open_positions"],
        "status": "OK" if fx_state.get("marks_fresh") else "STALE_MARKS",
    }
    for fam in CRYPTO_SLEEVES:
        last = crypto[fam].get("last_mark") or {}
        pos = last.get("positions") or []
        sleeves[fam] = {
            "currency": "USDT",
            "epoch1_equity": last.get("equity"),
            "epoch1_realized": last.get("realized_pnl"),
            "epoch1_unrealized": last.get("unrealized_pnl"),
            "gross_notional": round(sum(abs(p.get("notional") or 0.0) for p in pos), 2),
            "fees": last.get("fees"), "slippage": last.get("slippage"),
            "funding": last.get("funding"),
            "positions": [{"symbol": p.get("symbol"), "qty": p.get("qty"),
                           "notional": p.get("notional")} for p in pos],
            "status": last.get("status") or "NO_MARK",
            "mark_ts": last.get("mark_timestamp_utc"),
        }

    # ---- exposure (epoch-1 current books; same books that would carry) --
    fx_gross = float(sleeves["FX-RANGEFADE-2M"]["gross_notional"] or 0.0)
    fx_usd_dir = _fx_usd_directional(fx["open_positions"], fx_state)
    crypto_gross_usdt = sum(float(sleeves[f]["gross_notional"] or 0.0)
                            for f in CRYPTO_SLEEVES)
    crypto_gross_excluded_usdt = 0.0
    xsect = sleeves.get("XSECT-FUND-CARRY-7D") or {}
    if isinstance(xsect.get("gross_notional"), (int, float)):
        crypto_gross_excluded_usdt = float(xsect["gross_notional"])
    exposure = {
        "fx_gross_usd": round(fx_gross, 2),
        "fx_usd_directional_usd": fx_usd_dir,
        "crypto_gross_included_usdt": round(crypto_gross_usdt - crypto_gross_excluded_usdt, 2),
        "crypto_gross_excluded_xsect_usdt": round(crypto_gross_excluded_usdt, 2),
        "fx_leverage_on_100k": round(fx_gross / 100000.0, 3),
        "note": "epoch-1 books, display-only. XSECT shown separately: retired identity, run-off only.",
        "overlap_symbols_epoch2_sleeves": _overlap(crypto, ["BTC4H-BANDRIDGE", "BASISLV-PREMFADE-28D", "ILLIQ-AMIHUD-28D-W"]),
        "overlap_symbols_with_xsect_runoff": _overlap(crypto, CRYPTO_SLEEVES),
    }

    epoch1_sum = 0.0
    for sid, s in sleeves.items():
        eq = s.get("epoch1_equity")
        if isinstance(eq, (int, float)):
            rate = usdt_ref if s["currency"] == "USDT" else 1.0
            epoch1_sum += eq * rate

    src_files = _source_manifest()
    # epoch-2 aggregation ONLY for a validly ACTIVE config — a forced/
    # pending config must never produce epoch-2 numbers (fail-closed)
    e2 = (_epoch2_block(fx, crypto, cfg) if active else
          {"pnl_total": None, "equity": None, "status": "NOT_ACTIVATED",
           "note": ("epoch-2 PnL không tồn tại trước owner GO; không backfill, "
                    "không chuyển kết quả cũ vào kỳ mới")})

    return {
        "schema": SCHEMA,
        "mode": ("ACTIVE" if active else
                 ("PREVIEW_FORCED" if activation_error else "PREVIEW")),
        "activation_ts_utc": cfg.get("activation_ts_utc"),
        "epoch": 2,
        "epoch2": {
            "opening_equity_usd_eq": cfg.get("opening_equity_usd_eq"),
            "pnl_total": e2.get("pnl_total"),
            "equity": e2.get("equity"),
            "fx_realized": e2.get("fx_realized"),
            "fx_trades": e2.get("fx_trades"),
            "sleeves": e2.get("sleeves"),
            "status": e2.get("status"),
            "note": e2.get("note"),
            "open_position_law": cfg.get("open_position_law"),
            "activation_error": activation_error,
        },
        "epoch1": {
            "label": "LỊCH SỬ CŨ — KHÔNG cộng vào kỳ mới",
            "per_sleeve_100k_model_sum_usd_eq": round(epoch1_sum, 2),
            "note": ("Con số này là tổng 5 sách epoch-1 mỗi sách 100k — mô hình CŨ, "
                     "chỉ hiển thị trong tab lịch sử, không bao giờ là equity của portfolio mới"),
            "sleeves": sleeves,
            "history_days": history_days,
            "fx_integrity": fx["integrity"],
        },
        "sleeves_display": sleeves,
        "exposure": exposure,
        "capital_rule": cfg.get("capital_rule") or {},
        "allocation_options": (cfg.get("allocation") or {}).get("options", {}),
        "worker_status": _worker_status(),
        "source_manifest": src_files,
        "generated_note": "PREVIEW build (chưa activation). Chỉ ĐỌC nguồn epoch-1; ghi duy nhất vào out/ của control dir này.",
    }


def _fx_usd_directional(open_pos: Mapping[str, dict], fx_state: Mapping[str, Any]) -> float:
    """USD-directional exposure of open FX legs: LONG base ccy = SHORT USD
    of notional base-units × price; SHORT base = LONG USD."""
    total = 0.0
    for pair, p in open_pos.items():
        lots = float(p.get("lots") or 0)
        units = lots * FX_CONTRACT_UNITS
        mark = _pair_mark(fx_state, pair)
        if mark is None:
            continue
        sign = 1.0 if int(p.get("dir") or 0) > 0 else -1.0
        # long base ccy  -> short USD  (negative USD exposure)
        total += -sign * units * mark
    return round(total, 2)


def _pair_mark(fx_state: Mapping[str, Any], pair: str) -> Optional[float]:
    sl = (fx_state.get("sleeves") or {}).get(pair) or {}
    mark = sl.get("mark") or {}
    bid = mark.get("bid")
    return float(bid) if isinstance(bid, (int, float)) else None


def _overlap(crypto: Mapping[str, Any], fams: List[str]) -> List[dict]:
    """Symbols held by more than one listed sleeve right now."""
    hold: Dict[str, List[str]] = {}
    for fam in fams:
        last = (crypto.get(fam) or {}).get("last_mark") or {}
        for p in last.get("positions") or []:
            hold.setdefault(str(p.get("symbol")), []).append(fam)
    return [{"symbol": s, "sleeves": v} for s, v in sorted(hold.items()) if len(v) > 1]


def _worker_status() -> dict:
    out: Dict[str, Any] = {}
    hb = read_json(FX_DIR / "daemon_heartbeat.json") or {}
    out["fx_daemon"] = {"heartbeat_utc": hb.get("pid_heartbeat_utc"),
                        "fresh_threshold_s": 90}
    sh = PSV1_RESULTS / "runtime"
    out["psv1_decision"] = read_json(sh / "heartbeat.json")
    out["psv1_valuation"] = read_json(sh / "valuation_heartbeat.json")
    return out


def _source_manifest() -> List[dict]:
    files = [FX_DIR / "shadow_journal.jsonl", FX_DIR / "shadow_state.json",
             FX_DIR / "equity_curve.json"] + \
            [PSV1_RESULTS / f"valuation_marks/{f}.jsonl" for f in CRYPTO_SLEEVES] + \
            [PSV1_RESULTS / f"ledgers/{f}.jsonl" for f in CRYPTO_SLEEVES]
    out = []
    for p in files:
        out.append({"path": str(p), "sha256": sha256_file(p),
                    "bytes": p.stat().st_size if p.exists() else None})
    return out


# ----------------------------------------------------------------------
# capital rule engine (frozen law, performance-independent)
# ----------------------------------------------------------------------
def apply_capital_rule(portfolio_equity: float, fx_gross: float,
                       crypto_gross_usdt: float, usdt_ref: float,
                       priority_order: List[str], sleeve: str,
                       add_gross_usd_eq: float, caps: Mapping[str, float],
                       min_fx_lot: float = 0.10, min_crypto_notional: float = 10.0
                       ) -> Dict[str, Any]:
    """R1–R5 of epoch_config.capital_rule. Deterministic, no PnL input.

    Returns an execution decision: ALLOW / SCALED / BLOCK with the
    resulting exposure — used by the dashboard's capital panel and by
    tests. It does NOT place anything anywhere."""
    if sleeve not in priority_order:
        return {"decision": "BLOCK", "reason": "sleeve not in frozen priority order"}
    cap_total = portfolio_equity * caps.get("cap_total_gross_pct_equity", 250) / 100.0
    cap_fx = portfolio_equity * caps.get("cap_fx_gross_pct_equity", 150) / 100.0
    cap_cr = portfolio_equity * caps.get("cap_crypto_gross_pct_equity", 150) / 100.0
    is_fx = sleeve == "FX-RANGEFADE-2M"
    cur_class = fx_gross if is_fx else crypto_gross_usdt * usdt_ref
    # R3 binds on the CROSS-CLASS aggregate too (reviewer finding: a
    # class-only headroom let total exceed cap_total)
    cur_total = fx_gross + crypto_gross_usdt * usdt_ref
    cap_class = cap_fx if is_fx else cap_cr
    headroom = max(0.0, min(cap_class - cur_class, cap_total - cur_total))
    if add_gross_usd_eq <= headroom + 1e-9:
        return {"decision": "ALLOW", "requested_usd_eq": round(add_gross_usd_eq, 2),
                "headroom_before": round(headroom, 2)}
    if headroom <= 0:
        return {"decision": "BLOCK", "reason": "no class/total headroom (R3/R4)",
                "headroom": 0.0}
    scale = headroom / add_gross_usd_eq
    if is_fx:
        # min FX unit expressed conservatively at GBPUSD-type price:
        # 0.10 lot × 100,000 × ~1.35 ≈ $13,500 (declared constant; the
        # daemon is the authority for real fills)
        min_fx_unit_usd_eq = min_fx_lot * FX_CONTRACT_UNITS * 1.35
        scaled_usd = add_gross_usd_eq * scale
        if scaled_usd < min_fx_unit_usd_eq:
            return {"decision": "BLOCK", "reason": "scaled below min unit 0.10 lot (R4)",
                    "scale": round(scale, 4)}
        return {"decision": "SCALED", "scale": round(scale, 4),
                "scaled_add_usd_eq": round(headroom, 2), "min_unit": "0.10 lot"}
    scaled_notional = add_gross_usd_eq * scale
    if scaled_notional < min_crypto_notional:
        return {"decision": "BLOCK", "reason": "scaled below min unit 10 USDT (R4)",
                "scale": round(scale, 4)}
    return {"decision": "SCALED", "scale": round(scale, 4),
            "scaled_add_usd_eq": round(headroom, 2), "min_unit": "10 USDT notional"}
