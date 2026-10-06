"""intent_contract.py — normalized order-intent schema for the wiring seam.

Every family adapter (adapt_nq/*, adapt_fx_eb/*, adapt_fx_ja/*) produces
lane-shaped order-intent records. The wiring normalizes them into
`futures_5sym_prescored/wired_intent@1` before compilation:

  {
    "schema": "futures_5sym_prescored/wired_intent@1",
    "identity_id":  <draft identity id, verbatim>,
    "symbol":       "NQ" | "6E" | "6B" | "6J" | "6A",
    "family":       <adapter family label, e.g. NQ-F1 / FX-F1 / JF1>,
    "direction":    +1 | -1,
    "entry_date":   "YYYY-MM-DD"   (runner bars are date-keyed),
    "exit_date":    "YYYY-MM-DD"   (entry < exit),
    "entry_price":  float (on the symbol tick grid),
    "exit_price":   float (on the symbol tick grid),
    "cost_tier":    "S1" | "S2" | "S3",
    "stress":       1.0 | 1.5 | 2.0,
    "source_adapter": <lane>/<family adapter module path>,
    "provenance":   "SYNTHETIC" (real-data paths never reach this seam),
    "labels":       [...] (adapter-declared labels carried verbatim),
    # --- intent-seam fields (wave-4 WIRING-FIX; optional, additive) --------
    "signal_ts":    "YYYY-MM-DD" (decision timestamp; default = the day
                    before entry_date),
    "exit_reason":  "horizon" | "stop_loss" | "take_profit" | "session_close"
                    (default "horizon"; adapter spellings SL / TP /
                    SESSION_CLOSE / HORIZON_CLOSE are canonicalized via
                    EXIT_REASON_ALIASES; the intent-execution seam carries
                    it verbatim into the trade journal and the runner
                    validates the declared exit against the identity's
                    holding horizon — stop_loss/take_profit/session_close
                    may close same-bar or early, horizon must close exactly
                    at entry_bar + holding_horizon_bars)
  }

Compile law (fail-closed, enforced by spec_compiler):
  C1  hold-gap uniformity: an identity's trades must all share one
      (exit_date - entry_date) bar gap; a variance raises
      REFUSED_COMPILE_HOLD_GAP_VARIANCE (the runner spec_packet@1 carries one
      hold_bars per identity — a variance is NOT silently split or dropped).
  C2  entry/exit prices must sit on the symbol's era tick grid.
  C3  era-calibrated cost manifests refuse mismatched entry eras
      (REFUSED_COMPILE_COST_ERA_MISMATCH).
  C4  direction +1 compiles to arm "long-if-bar-up", -1 to
      "short-if-bar-down" (the runner's two legal arms).
"""
from __future__ import annotations

INTENT_SCHEMA = "futures_5sym_prescored/wired_intent@1"
# Canonical seam vocabulary (mirrors the runner's INTENT_EXIT_REASONS).
INTENT_EXIT_REASONS = ("horizon", "stop_loss", "take_profit", "session_close")
# Adapter-lane vocabulary -> seam canonical (the wiring is the translator;
# class/function adapters emit SL/TP/SESSION_CLOSE/HORIZON_CLOSE spellings).
EXIT_REASON_ALIASES = {
    "HORIZON": "horizon", "HORIZON_CLOSE": "horizon", "HORIZON_EXIT": "horizon",
    "SL": "stop_loss", "STOP_LOSS": "stop_loss",
    "TP": "take_profit", "TAKE_PROFIT": "take_profit",
    "SESSION_CLOSE": "session_close", "SESSION": "session_close",
}


def canon_exit_reason(value) -> str:
    if value is None:
        return "horizon"
    s = str(value).strip().upper()
    if s in EXIT_REASON_ALIASES:
        return EXIT_REASON_ALIASES[s]
    if s in {r.upper() for r in INTENT_EXIT_REASONS}:
        return s.lower()
    raise ValueError(f"exit_reason must be one of {INTENT_EXIT_REASONS} "
                     f"(adapter aliases {sorted(EXIT_REASON_ALIASES)}), "
                     f"got {value!r}")


def normalize_intent(*, identity_id: str, symbol: str, family: str,
                     direction: int, entry_date: str, exit_date: str,
                     entry_price: float, exit_price: float,
                     cost_tier: str = "S2", stress: float = 1.0,
                     source_adapter: str, provenance: str = "SYNTHETIC",
                     labels: list | None = None,
                     signal_ts: str | None = None,
                     exit_reason: str = "horizon") -> dict:
    if direction not in (1, -1):
        raise ValueError(f"direction must be +/-1, got {direction!r}")
    if cost_tier not in ("S1", "S2", "S3"):
        raise ValueError(f"cost_tier must be S1/S2/S3, got {cost_tier!r}")
    if stress not in (1.0, 1.5, 2.0):
        raise ValueError(f"stress must be 1.0/1.5/2.0, got {stress!r}")
    if exit_reason not in INTENT_EXIT_REASONS:
        exit_reason = canon_exit_reason(exit_reason)
    if not (entry_date <= exit_date):
        raise ValueError(f"entry_date {entry_date} must not follow exit_date "
                         f"{exit_date} (intraday trades carry equal dates)")
    rec = {
        "schema": INTENT_SCHEMA,
        "identity_id": identity_id,
        "symbol": symbol,
        "family": family,
        "direction": int(direction),
        "signal_ts": str(signal_ts) if signal_ts is not None else None,
        "entry_date": entry_date,
        "exit_date": exit_date,
        "entry_price": float(entry_price),
        "exit_price": float(exit_price),
        "exit_reason": exit_reason,
        "cost_tier": cost_tier,
        "stress": float(stress),
        "source_adapter": source_adapter,
        "provenance": provenance,
        "labels": list(labels or []),
    }
    return rec


def intent_from_class_adapter(rec: dict, *, source_adapter: str,
                              default_symbol: str | None = None) -> dict:
    """Normalize a class-adapter (NQ F1-F3 / JF1) order_intent record.
    Class adapters expose direction/side, entry_ref_price/exit_ref_price and
    ISO timestamps; the runner needs dates only. Key spellings differ across
    lanes (NQ: ts_exit; JF1: exit_ts) — both accepted."""
    if rec.get("no_trade"):
        raise ValueError(f"{rec.get('identity_id')}: NO-TRADE intent is not "
                         "compilable (no declared order)")
    direction = rec.get("direction")
    if direction is None:
        side = (rec.get("side") or "").upper()
        direction = {"BUY": 1, "SELL": -1}.get(side)
    symbol = rec.get("symbol") or default_symbol
    exit_ts = rec.get("ts_exit") or rec.get("exit_ts")
    exit_px = rec.get("exit_ref_price")
    if exit_ts is None or exit_px is None:
        raise ValueError(f"{rec.get('identity_id')}: intent exit not "
                         f"resolved (ts={exit_ts!r}, px={exit_px!r})")
    return normalize_intent(
        identity_id=rec["identity_id"], symbol=symbol,
        family=rec.get("family") or "", direction=direction,
        entry_date=str(rec["ts_entry"])[:10],
        exit_date=str(exit_ts)[:10],
        entry_price=float(rec["entry_ref_price"]),
        exit_price=float(exit_px),
        cost_tier=(rec.get("cost_tier") or "S2"),
        stress=1.0,
        source_adapter=source_adapter,
        labels=rec.get("labels"),
        signal_ts=rec.get("signal_ts"),
        exit_reason=rec.get("exit_reason"))


def intent_from_function_adapter(rec: dict, *, source_adapter: str) -> dict:
    """Normalize a function-adapter (FXEB F1-F3) order_intent record."""
    if rec.get("status") != "ORDER_INTENT":
        raise ValueError(f"{rec.get('identity_id')}: status "
                         f"{rec.get('status')!r} is not compilable")
    direction = 1 if rec.get("side") == "BUY" else -1
    entry_ts = rec["entry_ts_intent"]
    exit_ts = rec["exit_ts_intent"]
    return normalize_intent(
        identity_id=rec["identity_id"], symbol=rec["symbol"],
        family=rec.get("family") or "", direction=direction,
        entry_date=str(entry_ts)[:10], exit_date=str(exit_ts)[:10],
        entry_price=float(rec["entry_px_intent"]),
        exit_price=float(rec["exit_px_model"]),
        cost_tier=(rec.get("tier") or "S2"),
        stress=1.0,
        source_adapter=source_adapter,
        labels=[rec.get("proposed")] if rec.get("proposed") else None,
        signal_ts=rec.get("signal_ts"),
        exit_reason=rec.get("exit_reason"))
