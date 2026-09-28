"""Portfolio ONE read model — two-sleeve minimal view (gate A preview).

Builds the single-account state for PhorecOne from VERIFIED primitives in
portfolio_lib (fx_replay, crypto_daily_series, activation gate, hashing).
Design laws (owner directive 2026-09-25, v2):

- Adapter-based: exactly the sleeves listed in epoch_config.adapters
  are mounted. NO auto-discovery, NO auto-mount — an unknown id in the
  registry raises (fail-closed), adding a strategy is an explicit config
  entry + written adapter + owner GO.
- ONE account: opening equity 100,000 USD-eq; epoch-2 PnL from 0 at T*;
  epoch-1 books are reference/evidence only and are never summed into
  the new account.
- USD and USDT are separate books joined by the DECLARED usdt_usd_ref
  (1:1 REPORTING ASSUMPTION — label travels with every number).
- Read-only: this module writes nothing anywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import portfolio_lib as pl  # noqa: E402

SCHEMA = "portfolio_one.state@1"

BANDRIDGE_STATE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                       "btc-h4-band-risk-v1/integration/research/control/"
                       "btc_h4_band_risk_v1/shadow_bandridge/state.json")
BANDRIDGE_LEDGER = BANDRIDGE_STATE.parent / "ledger.jsonl"
EPOCH1_BANDRIDGE_LEDGER = pl.PSV1_RESULTS / "ledgers/BTC4H-BANDRIDGE.jsonl"

SLEEVE_META = {
    "FX-RANGEFADE-2M": {
        "section": "Forex", "currency": "USD",
        "class": "KEEP_PROSPECTIVE · NOT_PROMOTABLE",
        "note": ("EURUSD+GBPUSD · 1.5 lot/cặp · chốt phẳng 20:00 UTC · PnL "
                 "GROSS/HYPOTHETICAL (journal chưa có commission/slippage/funding; "
                 "spread ngầm trong giá fill đối diện) — tuyệt đối không gọi là net. "
                 "Khoảng trống cost/USD-exposure: chờ A1-controls GO."),
    },
    "BTC4H-BANDRIDGE": {
        "section": "Crypto", "currency": "USDT",
        "class": "CONDITIONAL_KEEP · A2 PHASE A ACTIVATED",
        "note": ("Donchian 30/15 + band gate, H4 · sizing B + fill law A + 6 bps/side "
                 "(A2, T_act=2026-09-25T03:57:05Z) áp trên vốn sleeve $50,000 "
                 "(sleeve-fenced) · USDT=USD 1:1 là GIẢ ĐỊNH BÁO CÁO."),
    },
}


# ----------------------------------------------------------------------
# adapters
# ----------------------------------------------------------------------
class SleeveAdapter:
    """Base adapter. A sleeve is VISIBLE only through one of these; the
    registry is an explicit allowlist (epoch_config.adapters)."""

    sleeve_id = "?"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        entry = next((s for s in config.get("sleeves", [])
                      if s.get("sleeve_id") == self.sleeve_id), None)
        if entry is None:
            raise ValueError(f"sleeve {self.sleeve_id} not declared in epoch_config")
        self.entry = entry
        self.meta = SLEEVE_META[self.sleeve_id]

    def data_status(self) -> Dict[str, Any]:
        raise NotImplementedError

    def open_positions(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def pending_orders(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def closed_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def pnl_reference(self) -> Dict[str, Any]:
        raise NotImplementedError


class FxAdapter(SleeveAdapter):
    """FX-RANGEFADE-2M — reads the verified FX primitives."""

    sleeve_id = "FX-RANGEFADE-2M"

    def __init__(self, config: Dict[str, Any], journal_path: Optional[Path] = None,
                 state_path: Optional[Path] = None, hb_path: Optional[Path] = None):
        super().__init__(config)
        self.journal_path = journal_path or (pl.FX_DIR / "shadow_journal.jsonl")
        self.state_path = state_path or (pl.FX_DIR / "shadow_state.json")
        self.hb_path = hb_path or (pl.FX_DIR / "daemon_heartbeat.json")

    def replay(self) -> Dict[str, Any]:
        return pl.fx_replay(self.journal_path)

    def state(self) -> Dict[str, Any]:
        return pl.read_json(self.state_path) or {}

    def data_status(self) -> Dict[str, Any]:
        st = self.state()
        return {"status": "OK" if st.get("marks_fresh") else "STALE_MARKS",
                "marks_fresh": st.get("marks_fresh"),
                "data_stale": st.get("data_stale"),
                "updated_utc": st.get("updated_utc"),
                "heartbeat": pl.read_json(self.hb_path)}

    def open_positions(self) -> List[Dict[str, Any]]:
        st = self.state()
        out = []
        for pair, sl in (st.get("sleeves") or {}).items():
            if sl.get("position") in ("LONG", "SHORT"):
                out.append({"pair": pair, "side": sl["position"],
                            "lots": sl.get("lots"), "entry_px": sl.get("entry_px"),
                            "entry_ts": sl.get("entry_ts"),
                            "unrealized_usd": sl.get("unrealized_usd"),
                            "mark": sl.get("mark")})
        return out

    def pending_orders(self) -> List[Dict[str, Any]]:
        # FX law: signal on closed H1 bar → fill at next H1 open; nothing rests.
        return []

    def pending_note(self) -> str:
        return "Không có lệnh chờ theo luật: fill ngay tại H1 open sau bar đóng."

    def closed_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.replay()["trades"][-limit:]

    def pnl_reference(self) -> Dict[str, Any]:
        acc = self.state().get("account") or {}
        return {"epoch1_equity": acc.get("equity"),
                "realized": acc.get("realized_usd"),
                "unrealized": acc.get("unrealized_usd"),
                "gross_notional": acc.get("gross_exposure_usd"),
                "fees": None,
                "fees_note": "không có trường phí trong journal — GROSS/HYPOTHETICAL"}


class BandridgeAdapter(SleeveAdapter):
    """BTC4H-BANDRIDGE — PSV1 sleeve 4 marks + band-risk worktree state."""

    sleeve_id = "BTC4H-BANDRIDGE"

    def __init__(self, config: Dict[str, Any], marks_path: Optional[Path] = None,
                 state_path: Optional[Path] = None, ledger_path: Optional[Path] = None):
        super().__init__(config)
        self.marks_path = marks_path or (pl.PSV1_RESULTS /
                                         "valuation_marks/BTC4H-BANDRIDGE.jsonl")
        self.state_path = state_path or BANDRIDGE_STATE
        self.ledger_path = ledger_path or BANDRIDGE_LEDGER

    def daily(self) -> Dict[str, Any]:
        return pl.crypto_daily_series(self.marks_path)

    def state(self) -> Dict[str, Any]:
        return pl.read_json(self.state_path) or {}

    def data_status(self) -> Dict[str, Any]:
        last = self.daily()["last_mark"] or {}
        return {"status": last.get("status") or "NO_MARK",
                "mark_ts": last.get("mark_timestamp_utc"),
                "n_marks": self.daily()["n_marks"],
                "accounting_status": last.get("accounting_status"),
                "data_status": last.get("data_status")}

    def open_positions(self) -> List[Dict[str, Any]]:
        last = self.daily()["last_mark"] or {}
        out = []
        for p in last.get("positions") or []:
            out.append({"symbol": p.get("symbol"),
                        "side": "LONG" if (p.get("qty") or 0) > 0 else "SHORT",
                        "qty": p.get("qty"), "entry_px": p.get("avg_price"),
                        "mark_px": p.get("mark_price"),
                        "notional_usdt": p.get("notional"),
                        "unrealized_usdt": p.get("unrealized_pnl"),
                        "ts_opened": p.get("ts_opened")})
        return out

    def pending_orders(self) -> List[Dict[str, Any]]:
        st = self.state()
        pending = st.get("pending")
        if not pending:
            return []
        return [{"raw": pending}]

    def pending_note(self) -> str:
        st = self.state()
        if st.get("pending"):
            return "Có intent chờ fill theo fill law A (15m bar kế tiếp)."
        return "Không có lệnh chờ (state.pending = null)."

    def closed_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        # band-risk worktree ledger holds per-fill rows (currently empty —
        # no fill has ever happened); PSV1 decision ledger is history.
        rows = pl.read_jsonl(self.ledger_path)
        return rows[-limit:]

    def pnl_reference(self) -> Dict[str, Any]:
        last = self.daily()["last_mark"] or {}
        return {"epoch1_equity": last.get("equity"),
                "realized": last.get("realized_pnl"),
                "unrealized": last.get("unrealized_pnl"),
                "gross_notional": last.get("gross"),
                "fees": last.get("fees"),
                "funding": last.get("funding")}


def mount_adapters(config: Dict[str, Any]) -> Dict[str, SleeveAdapter]:
    """Explicit allowlist mount — the ONLY way a sleeve becomes visible."""
    registry = (config.get("adapters") or {}).get("registry_default") or []
    known = {FxAdapter.sleeve_id: FxAdapter, BandridgeAdapter.sleeve_id: BandridgeAdapter}
    mounted: Dict[str, SleeveAdapter] = {}
    for sid in registry:
        if sid not in known:
            # fail-closed: an unknown id in the registry is a config error,
            # never a silent skip and never an auto-mount
            raise ValueError(f"no adapter for registered sleeve '{sid}'")
        mounted[sid] = known[sid](config)
    return mounted


# ----------------------------------------------------------------------
# portfolio assembly
# ----------------------------------------------------------------------
def build_one_state(config_path: Optional[Path] = None) -> Dict[str, Any]:
    cfg, activation_error = pl._validate_activation(pl.read_json(
        config_path or (pl.HERE / "epoch_config.json")
        if (pl.HERE / "epoch_config.json").exists() else pl.CONFIG_FALLBACK))
    active = cfg.get("status") == "ACTIVE" and activation_error is None
    adapters = mount_adapters(cfg)
    fx: FxAdapter = adapters["FX-RANGEFADE-2M"]
    br: BandridgeAdapter = adapters["BTC4H-BANDRIDGE"]
    ref = float((cfg.get("usdt_usd_ref") or {}).get("rate", 1.0))

    fx_rep = fx.replay()
    fx_state = fx.state()
    br_daily = br.daily()
    br_state = br.state()

    # ---- calendar (epoch-1 reference history, two sleeves) --------------
    br_days = {r["day_utc"]: r for r in br_daily["rows"]}
    days = sorted(set(fx_rep["realized_by_day"]) | set(br_days))
    history_days = []
    for d in days:
        fx_pairs = fx_rep["realized_by_day"].get(d, {})
        br_row = br_days.get(d)
        total = sum(fx_pairs.values())
        if br_row and br_row.get("day_pnl") is not None:
            total += br_row["day_pnl"]
        history_days.append({
            "day_utc": d,
            "total_day_pnl_usd_eq": round(total, 2),
            "sleeves": {
                "FX-RANGEFADE-2M": {
                    "day_realized_usd": round(sum(fx_pairs.values()), 2),
                    "round_trips": sum(fx_rep["fills_by_day"].get(d, {}).values()),
                    "status": ("OK" if fx_pairs else "NO_TRADE")},
                "BTC4H-BANDRIDGE": (
                    {"day_pnl": br_row.get("day_pnl"), "status": br_row.get("status"),
                     "decomposition": br_row.get("decomposition")}
                    if br_row else
                    {"day_pnl": None, "status": pl.UNAVAILABLE,
                     "reason": "no valuation mark on this UTC day"}),
            },
        })

    # ---- epoch-2 (inert until ACTIVE) -----------------------------------
    if active:
        e2 = _epoch2_two_sleeves(cfg, fx, br, fx_rep, br_daily)
    else:
        e2 = {"status": "NOT_ACTIVATED", "pnl_total": None, "equity": None,
              "sleeves": None,
              "note": ("epoch-2 chưa tồn tại trước owner GO — baseline $100,000, "
                       "PnL $0 tại T*; không backfill, không cộng sách cũ")}

    # ---- live account view ----------------------------------------------
    fx_gross = float((fx.pnl_reference().get("gross_notional") or 0.0))
    br_last = br_daily["last_mark"] or {}
    br_gross = sum(abs(p.get("notional") or 0.0)
                   for p in (br_last.get("positions") or []))
    account = {
        "opening_equity_usd_eq": cfg.get("opening_equity_usd_eq"),
        "usdt_usd_ref": cfg.get("usdt_usd_ref"),
        "epoch2": e2,
        "gross_exposure_usd_eq": round(fx_gross + br_gross * ref, 2),
        "fx_gross_usd": round(fx_gross, 2),
        "bandridge_gross_usdt": round(br_gross, 2),
        "epoch1_reference": {
            "label": "sách cũ epoch-1 — tham chiếu, KHÔNG cộng vào tài khoản mới",
            "fx_equity": fx.pnl_reference()["epoch1_equity"],
            "bandridge_equity": br_last.get("equity")},
        "caps": (cfg.get("capital_rule") or {}).get("caps_proposal_from_sizing_audit"),
    }

    sleeves_out = {}
    for sid, ad in adapters.items():
        sleeves_out[sid] = {
            "meta": ad.meta,
            "sleeve_capital_usd_eq": ad.entry.get("sleeve_capital_usd_eq"),
            "data_status": ad.data_status(),
            "open_positions": ad.open_positions(),
            "pending_orders": ad.pending_orders(),
            "pending_note": ad.pending_note(),
            "closed_trades": ad.closed_trades(),
            "pnl_reference": ad.pnl_reference(),
        }

    return {
        "schema": SCHEMA,
        "mode": ("ACTIVE" if active else
                 ("PREVIEW_FORCED" if activation_error else "PREVIEW")),
        "activation_error": activation_error,
        "activation_ts_utc": cfg.get("activation_ts_utc"),
        "open_position_law": cfg.get("open_position_law"),
        "epoch": 2,
        "account": account,
        "sleeves": sleeves_out,
        "history_days": history_days,
        "worker_status": pl._worker_status(),
        "source_manifest": _manifest(cfg, fx, br),
    }


def _fx_trades_with_open_ts(journal_path: Path) -> List[dict]:
    """Pair each deduped close with its opening timestamp (journal close
    rows carry no entry_ts). Same dedup keys as the verified replay."""
    seen = set()
    open_ts: Dict[str, str] = {}
    trades: List[dict] = []
    for rec in pl.read_jsonl(journal_path):
        event = rec.get("event")
        pair = str(rec.get("pair") or "")
        if event == "fill_open":
            key = ("open", pair, rec.get("entry_ts"), rec.get("entry_px"))
            if key in seen:
                continue
            seen.add(key)
            open_ts[pair] = str(rec.get("ts") or "")
        elif event in ("fill_close", "force_flat"):
            key = ("close", pair, rec.get("ts"), rec.get("exit_px"))
            if key in seen:
                continue
            seen.add(key)
            trades.append({
                "pair": pair, "close_ts_utc": str(rec.get("ts") or ""),
                "open_ts_utc": open_ts.get(pair),
                "dir": int(rec.get("dir") or 0), "lots": rec.get("lots"),
                "entry_px": rec.get("entry_px"), "exit_px": rec.get("exit_px"),
                "pnl_usd": float(rec.get("pnl_usd") or 0.0),
                "reason": rec.get("reason"),
            })
    return trades


def _boundary_rows(cfg: Dict[str, Any]) -> List[dict]:
    """Operator-written REOPEN_AT_MARK boundary manifest (epoch-2 basis
    marks), if it exists. The engine never invents these."""
    for cand in sorted((pl.HERE / "out").glob("boundary_*.jsonl")):
        rows = pl.read_jsonl(cand)
        if rows and rows[0].get("activation_ts_utc") == cfg.get("activation_ts_utc"):
            return rows
    return []


def _epoch2_two_sleeves(cfg: Dict[str, Any], fx: "FxAdapter",
                        br: "BandridgeAdapter", fx_rep: Dict[str, Any],
                        br_daily: Dict[str, Any]) -> Dict[str, Any]:
    """Post-activation aggregation honoring the approved open-position
    law. FLAT_START: a pre-T* open closing post-T* belongs ENTIRELY to
    epoch-1. REOPEN_AT_MARK: its epoch-2 PnL is (close − boundary mark);
    without the operator's boundary manifest that part is UNAVAILABLE —
    never silently 0, never pre-T* PnL booked into epoch-2."""
    t0 = pl._parse_utc(str(cfg.get("activation_ts_utc")))
    law = cfg.get("open_position_law")
    carried: List[dict] = []
    new_trades: List[dict] = []
    for t in _fx_trades_with_open_ts(fx.journal_path):
        cts = pl._parse_utc(t["close_ts_utc"]) or t0
        if cts < t0:
            continue
        ots = pl._parse_utc(t.get("open_ts_utc") or "")
        (new_trades if (ots and ots >= t0) else carried).append(t)

    fx_pnl = round(sum(t["pnl_usd"] for t in new_trades), 2)
    carried_status, carried_note = "OK", ""
    carried_pnl = 0.0
    if carried:
        if law == "FLAT_START":
            carried_note = ("FLAT_START: %d lệnh mở trước T* đóng sau T* — toàn bộ "
                            "PnL của chúng thuộc sách epoch-1." % len(carried))
        elif law == "REOPEN_AT_MARK":
            boundary = _boundary_rows(cfg)
            bmark = {r.get("pair"): r.get("boundary_mark") for r in boundary}
            have = [t for t in carried if t["pair"] in bmark]
            if boundary and len(have) == len(carried):
                for t in have:
                    carried_pnl += ((t["exit_px"] - bmark[t["pair"]])
                                    * t["dir"] * 1.5 / 1e-4 * 10.0)
                carried_note = "REOPEN_AT_MARK: epoch-2 chỉ tính (close − boundary mark)."
            else:
                carried_status = pl.UNAVAILABLE
                carried_note = ("REOPEN_AT_MARK nhưng thiếu boundary manifest cho "
                                "%d/%d vị thế kéo sang — phần này UNAVAILABLE, "
                                "không giả $0." % (len(carried) - len(have), len(carried)))
        else:
            carried_status = pl.UNAVAILABLE
            carried_note = "open_position_law chưa được duyệt."
    fx_pnl = round(fx_pnl + carried_pnl, 2)

    stampeds = []
    for m in pl.read_jsonl(br.marks_path):
        mts = pl._parse_utc(str(m.get("mark_timestamp_utc")
                                or m.get("observed_at_utc") or ""))
        if mts and mts >= t0 and isinstance(m.get("equity"), (int, float)):
            stampeds.append((mts, m["equity"]))
    if stampeds:
        br_pnl: Optional[float] = round(stampeds[-1][1] - stampeds[0][1], 2)
        br_status = "OK"
    else:
        br_pnl = None
        br_status = pl.UNAVAILABLE

    parts = [fx_pnl] + ([br_pnl] if br_pnl is not None else [])
    total = round(sum(parts), 2)
    opening = float(cfg.get("opening_equity_usd_eq") or 100000.0)
    status = ("ACTIVE" if (carried_status == "OK" and br_status == "OK")
              else "ACTIVE_PARTIAL")
    return {
        "activation_ts_utc": cfg.get("activation_ts_utc"),
        "status": status,
        "opening_equity_usd_eq": opening,
        "pnl_total": total,
        "equity": round(opening + total, 2),
        "sleeves": {
            "FX-RANGEFADE-2M": {"pnl": fx_pnl, "trades": len(new_trades),
                                "carried_status": carried_status,
                                "carried_note": carried_note},
            "BTC4H-BANDRIDGE": {"pnl": br_pnl, "status": br_status,
                                "note": ("baseline = mark đầu tiên ≥ T_STAR; boundary "
                                         "row của operator là authority") if br_pnl is not None
                                else "chưa có mark ≥ T_STAR"},
        },
        "note": ("chỉ tính dữ liệu từ T_STAR trở đi theo luật vị thế mở đã duyệt; "
                 "không carry PnL cũ, không backfill"),
    }


def _manifest(cfg: Dict[str, Any], fx: FxAdapter, br: BandridgeAdapter) -> List[dict]:
    files = [fx.journal_path, fx.state_path, fx.hb_path, br.marks_path,
             br.state_path, br.ledger_path, EPOCH1_BANDRIDGE_LEDGER,
             pl.HERE / "epoch_config.json"]
    return [{"path": str(p), "sha256": pl.sha256_file(p),
             "bytes": p.stat().st_size if p.exists() else None} for p in files]
