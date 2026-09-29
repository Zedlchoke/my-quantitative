"""BTC-COMBO6 orchestration: verified corpus -> per-leg signals -> engine
per leg per stress tier -> aggregate -> metrics -> verdicts -> artifacts.

Two runners:
- build_dry(): sanitized payload ONLY (counts, digests, replay proof).
  ABSOLUTE BAN inside dry artifacts: no PnL / profit factor / equity /
  win-rate / drawdown / expectancy / return values at ANY nesting depth.
- build_scored(): full metrics + trades + verdict bars + baselines, per
  stress tier; appends scored_outcome rows to TRIAL_LEDGER.jsonl.

Determinism: no RNG anywhere; two invocations produce byte-identical
canonical content (generated_utc is kept OUTSIDE hashed content).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import data, engine, signals, spec

DRY_SCHEMA = "btcombo6/dry_run@1"
SCORED_SCHEMA = "btcombo6/scored@1"
LEDGER_HEADER_SCHEMA = "btcombo6/trial_ledger@1"
LEDGER_ROW_SCHEMA = "btcombo6/trial_ledger_row@1"
BUDGET_MAX_SCORED_CELLS = 12
GO_PHRASE = "GO BTC COMBO6 SCORED V1 SCORED EXECUTION"
FREEZE_COMMIT_PLACEHOLDER = "PENDING_FREEZE"

BANNED_SUBSTRINGS = ["pnl", "profit_factor", "equity", "win_rate",
                     "drawdown", "expectancy", "return"]

PIT_DISCLOSURE = (
    "RETROSPECTIVE_SNAPSHOT: Vision klines are retrospective exchange "
    "snapshots without per-bar publication timestamps; frozen house "
    "convention (PSV1) — bar knowable at close, first executable fill at "
    "next 5m bar open."
)


def scan_banned(text: str) -> list[str]:
    """Case-insensitive scan for banned substrings (dry-run leak guard)."""
    low = text.lower()
    return [b for b in BANNED_SUBSTRINGS if b in low]


def trades_serializable(trades: list[dict]) -> list[dict]:
    out = []
    for tr in trades:
        out.append({
            "leg": tr["leg"], "fold": tr["fold"],
            "signal_ts": tr["signal_ts"].isoformat(),
            "fill_ts": tr["fill_ts"].isoformat(),
            "fill_px": float(tr["fill_px"]),
            "exit_ts": tr["exit_ts"].isoformat(),
            "exit_px": float(tr["exit_px"]),
            "exit_reason": tr["exit_reason"],
            "qty": float(tr["qty"]),
            "gross_pnl": float(tr["gross_pnl"]),
            "entry_fee": float(tr["entry_fee"]),
            "exit_fee": float(tr["exit_fee"]),
            "fees": float(tr["fees"]),
            "funding": float(tr["funding"]),
            "net_pnl": float(tr["net_pnl"]),
        })
    return out


def leg_record_id(leg_id: str, corpus_digest: str) -> str:
    payload = {
        "leg_spec": spec.LEGS[leg_id],
        "corpus_digest": corpus_digest,
        "fold_calendar": spec.fold_calendar_block(),
        "cost_kernel": spec.cost_kernel_block(),
        "engine_version": spec.ENGINE_VERSION,
    }
    return data.sha256_hex(data.canonical_json(payload))


def build_decisions(m5: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {leg: signals.leg_decisions(leg, m5) for leg in spec.LEG_IDS}


def _funding_census(funding: pd.DataFrame) -> dict:
    in_win = ((funding["ts"] >= spec.F1_START)
              & (funding["ts"] < spec.EVAL_END))
    return {
        "events_total": int(len(funding)),
        "events_in_eval_window": int(in_win.sum()),
        "interval_hours": 8,
        "ts_convention": "floored to 8h slot (measured jitter <=47ms)",
        "stress": "none (measured, signed, unstressed)",
    }


def _guard_sealed(result: dict, eval_end) -> None:
    """Fail loud on any sealed-tail leak or accounting break."""
    for tr in result["trades"]:
        if not (tr["fill_ts"] < eval_end and tr["exit_ts"] < eval_end):
            raise AssertionError(f"sealed leak in trade: {tr}")
    if len(result["equity"]):
        if result["equity"].index.max() >= eval_end:
            raise AssertionError("equity mark at/after eval_end")
        if result.get("open_at_frame_end") is None:
            recon = result["equity"].iloc[-1] - spec.SLEEVE_START_EQUITY \
                - sum(tr["net_pnl"] for tr in result["trades"])
            if abs(recon) > 1e-6:
                raise AssertionError(
                    f"{result['leg']}: equity/PnL reconciliation broke by {recon}")


def run_tier(m5: pd.DataFrame, funding: pd.DataFrame,
             decisions: dict[str, pd.DataFrame], stress: float) -> dict:
    """Full per-tier computation: 6 legs + combo + baselines (metrics only)."""
    leg_results = {}
    leg_metrics = {}
    for leg in spec.LEG_IDS:
        res = engine.run_leg(leg, spec.LEGS[leg], decisions[leg], m5,
                             stress=stress, funding=funding)
        _guard_sealed(res, spec.EVAL_END)
        mets = engine.metrics_from(res["trades"], res["equity"],
                                   spec.SLEEVE_START_EQUITY)
        leg_results[leg] = res
        leg_metrics[leg] = mets

    combo_trades = [tr for leg in spec.LEG_IDS for tr in leg_results[leg]["trades"]]
    combo_equity = sum(leg_results[leg]["equity"] for leg in spec.LEG_IDS)
    combo_equity.name = "ts"
    combo_metrics = engine.metrics_from(combo_trades, combo_equity,
                                        spec.COMBO_START_EQUITY)

    b1 = engine.always_long_baseline(m5, stress=stress, funding=funding)
    leg_fold_nets = {leg: {fn: v["net_pnl"] for fn, v in mets["per_fold"].items()}
                     for leg, mets in leg_metrics.items()}
    b3 = engine.best_leg_prior_baseline(leg_fold_nets)

    return {
        "stress": float(stress),
        "leg_results": leg_results,
        "leg_metrics": leg_metrics,
        "combo_trades": combo_trades,
        "combo_equity": combo_equity,
        "combo_metrics": combo_metrics,
        "b1": b1,
        "b3": b3,
    }


# ---------------------------------------------------------------------------
# DRY mode (sanitized)
# ---------------------------------------------------------------------------

def build_dry_core(corpus: dict, decisions: dict[str, pd.DataFrame]) -> dict:
    """Deterministic dry payload WITHOUT generated_utc/replay blocks."""
    digest = corpus["corpus_digest"]
    legs_block = {}
    for leg in spec.LEG_IDS:
        res = engine.run_leg(leg, spec.LEGS[leg], decisions[leg],
                             corpus["m5"], stress=1.0, funding=corpus["funding"])
        _guard_sealed(res, spec.EVAL_END)
        cnt = res["counters"]
        per_fold: dict[str, int] = {}
        for f in spec.FOLDS:
            per_fold[f["fold"]] = 0
        for tr in res["trades"]:
            per_fold[tr["fold"]] += 1
        legs_block[leg] = {
            "record_id": leg_record_id(leg, digest),
            "family": spec.LEGS[leg]["name"],
            "clock": spec.LEGS[leg]["clock"],
            "tp": spec.LEGS[leg]["tp"],
            "sl": spec.LEGS[leg]["sl"],
            "decision_count": cnt["decisions_seen"],
            "enter_signal_count": cnt["enter_signals_seen"],
            "entries_filled": cnt["entries_filled"],
            "entries_deferred": cnt["entries_deferred"],
            "entries_expired_at_fold_boundary": cnt["entries_expired_at_fold_boundary"],
            "entries_dropped_no_bar": cnt["entries_dropped_no_bar"],
            "signals_discarded_while_long": cnt["signals_discarded_while_long"],
            "total_trades": int(len(res["trades"])),
            "per_fold_trades": per_fold,
            "non_vacuous": bool(len(res["trades"]) >= spec.MIN_TRADES_NON_VACUOUS),
            "signal_digest": signals.signal_digest(decisions[leg]),
            "signal_digest_spec": (
                "sha256 over b'btcombo6/signal_digest@1' + little-endian "
                "int64 epoch-seconds of every decision_ts + uint8 enter flags"),
        }
    return {
        "schema": DRY_SCHEMA,
        "mode": "dry",
        "cycle_id": spec.CYCLE_ID,
        "engine_version": spec.ENGINE_VERSION,
        "corpus_digest": digest,
        "pit_disclosure": PIT_DISCLOSURE,
        "fold_calendar": spec.fold_calendar_block(),
        "cost_kernel": spec.cost_kernel_block(),
        "gap_census": corpus["gap_census"],
        "funding_census": _funding_census(corpus["funding"]),
        "legs": legs_block,
    }


def build_dry(worktree_root: str | Path) -> dict:
    """Full dry artifact: core computed TWICE in-process (replay proof),
    banned-substring scan, generated_utc added last."""
    corpus = data.load_corpus(worktree_root)
    core1 = build_dry_core(corpus, build_decisions(corpus["m5"]))
    core2 = build_dry_core(corpus, build_decisions(corpus["m5"]))
    b1 = data.canonical_json(core1)
    b2 = data.canonical_json(core2)
    d1, d2 = data.sha256_hex(b1), data.sha256_hex(b2)
    payload = dict(core1)
    payload["generated_utc"] = pd.Timestamp.now(tz="UTC").strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    payload["replay"] = {
        "first_digest": d1,
        "second_digest": d2,
        "identical": bool(d1 == d2),
        "scope": "signals + engine + assembly recomputed twice in-process on "
                 "the same digest-verified corpus bytes",
    }
    violations = scan_banned(json.dumps(payload, sort_keys=True))
    payload["banned_key_scan"] = {
        # NOTE: the banned substring list itself is NOT serialized — writing
        # the words into the artifact would make the artifact contain them.
        "banned_key_count": len(BANNED_SUBSTRINGS),
        "violations": violations,
    }
    payload["replay_ok"] = bool(d1 == d2)
    payload["leak_scan_ok"] = bool(not violations)
    return payload


# ---------------------------------------------------------------------------
# SCORED mode
# ---------------------------------------------------------------------------

def _combo_net_at(tier_results: dict[float, dict], stress: float) -> float:
    return float(tier_results[stress]["combo_metrics"]["net_pnl"])


def build_scored_payloads(worktree_root: str | Path) -> dict:
    """All three stress tiers; verdicts + content digests per tier."""
    corpus = data.load_corpus(worktree_root)
    decisions = build_decisions(corpus["m5"])
    tier_results = {s: run_tier(corpus["m5"], corpus["funding"], decisions, s)
                    for s in spec.STRESS_TIERS}
    combo_net_s15 = _combo_net_at(tier_results, 1.5)

    payloads = {}
    for stress in spec.STRESS_TIERS:
        tr = tier_results[stress]
        legs_block = {}
        for leg in spec.LEG_IDS:
            mets = dict(tr["leg_metrics"][leg])
            legs_block[leg] = {
                "spec": dict(spec.LEGS[leg]),
                "metrics": mets,
                "verdict": engine.leg_verdict(mets),
                "counters": tr["leg_results"][leg]["counters"],
                "open_at_frame_end": (
                    None if tr["leg_results"][leg]["open_at_frame_end"] is None
                    else {k: (v.isoformat() if isinstance(v, pd.Timestamp)
                              else (float(v) if isinstance(v, float) else v))
                          for k, v in
                          tr["leg_results"][leg]["open_at_frame_end"].items()}),
                "trades": trades_serializable(
                    tr["leg_results"][leg]["trades"]),
            }
        combo_metrics = dict(tr["combo_metrics"])
        combo_metrics["combo_net_stress_1_5"] = combo_net_s15
        b1 = tr["b1"]
        combo_verdict = engine.combo_verdict(
            combo_metrics,
            [tr["leg_metrics"][leg] for leg in spec.LEG_IDS],
            b1["net_pnl"])
        payload = {
            "schema": SCORED_SCHEMA,
            "mode": "scored",
            "cycle_id": spec.CYCLE_ID,
            "engine_version": spec.ENGINE_VERSION,
            "stress": float(stress),
            "cost_kernel": {**spec.cost_kernel_block(),
                            "stress_multiplier": float(stress),
                            "cost_per_side_decimal": spec.cost_per_side(stress)},
            "corpus_digest": corpus["corpus_digest"],
            "pit_disclosure": PIT_DISCLOSURE,
            "fold_calendar": spec.fold_calendar_block(),
            "gap_census": corpus["gap_census"],
            "funding_census": _funding_census(corpus["funding"]),
            "legs": legs_block,
            "combo": {
                "metrics": combo_metrics,
                "verdict": combo_verdict,
                "per_fold_trades": {fn: sum(
                    legs_block[leg]["metrics"]["per_fold"][fn]["trades"]
                    for leg in spec.LEG_IDS) for fn in spec.FOLD_NAMES},
                "trades": trades_serializable(tr["combo_trades"]),
            },
            "baselines": {
                "B0_flat": {
                    "net": 0.0,
                    "disclosure": "sanity identity: aggregate flat at 60000",
                },
                "B1_always_long": {
                    "net_pnl": b1["net_pnl"],
                    "open": b1["open"],
                    "empty": b1.get("empty", False),
                    "fill_ts": b1.get("fill_ts", pd.NaT).isoformat()
                    if isinstance(b1.get("fill_ts"), pd.Timestamp) else None,
                    "fill_px": b1.get("fill_px"),
                    "qty": b1.get("qty"),
                    "entry_fee": b1.get("entry_fee"),
                    "exit_fee": b1.get("exit_fee"),
                    "gross_pnl": b1.get("gross_pnl"),
                    "funding_cost": b1.get("funding_cost"),
                    "max_dd_usd": (float((b1["equity"].cummax()
                                          - b1["equity"]).max())
                                   if len(b1["equity"]) else 0.0),
                    "disclosure": "single $10k position from F1 open held to "
                                  "the EVAL wall; wall exit priced at last "
                                  "in-window 5m close (sealed tail never "
                                  "evaluated); same fee kernel + funding",
                },
                "B3_best_leg_prior": tr["b3"],
            },
        }
        content = {k: v for k, v in payload.items()
                   if k not in ("generated_utc", "content_sha256")}
        payload["generated_utc"] = pd.Timestamp.now(tz="UTC").strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        payload["content_sha256"] = data.sha256_hex(
            data.canonical_json(content))
        payloads[stress] = payload
    return payloads


def _stress_key(s: float) -> str:
    return f"{s:.1f}"


def write_scored_artifacts(worktree_root: str | Path, payloads: dict) -> dict:
    root = Path(worktree_root)
    scored_dir = root / spec.SCORED_DIR_REL
    scored_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for stress, payload in payloads.items():
        p = scored_dir / f"btcombo6_scored_stress{_stress_key(stress)}.json"
        p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        written[stress] = p
    return written


def update_ledger(worktree_root: str | Path, payloads: dict) -> Path:
    """TRIAL_LEDGER.jsonl: one header row + one scored_outcome row per CELL
    (6 legs + 1 combo = 7 cells). Rows are keyed by cell (recomputation
    replaces the row, denominator counts unique cells computed)."""
    root = Path(worktree_root)
    ledger = root / spec.LEDGER_REL
    ledger.parent.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ")

    existing_rows: list[dict] = []
    header_meta = {"created_utc": now}
    if ledger.exists():
        lines = [ln for ln in ledger.read_text().splitlines() if ln.strip()]
        for ln in lines:
            row = json.loads(ln)
            if row.get("schema") == LEDGER_HEADER_SCHEMA:
                header_meta["created_utc"] = row.get("created_utc", now)
            elif row.get("schema") == LEDGER_ROW_SCHEMA:
                existing_rows.append(row)
    by_cell = {r["cell"]: r for r in existing_rows}

    for cell in list(spec.LEG_IDS) + ["COMBO"]:
        if cell == "COMBO":
            stress_block = {}
            for stress, payload in payloads.items():
                stress_block[_stress_key(stress)] = {
                    "net_pnl": payload["combo"]["metrics"]["net_pnl"],
                    "trade_count": payload["combo"]["metrics"]["trade_count"],
                }
            verdict = payloads[1.0]["combo"]["verdict"]
            trades_total = payloads[1.0]["combo"]["metrics"]["trade_count"]
            cell_kind = "combo"
        else:
            stress_block = {}
            for stress, payload in payloads.items():
                stress_block[_stress_key(stress)] = {
                    "net_pnl": payload["legs"][cell]["metrics"]["net_pnl"],
                    "trade_count": payload["legs"][cell]["metrics"]["trade_count"],
                }
            verdict = payloads[1.0]["legs"][cell]["verdict"]
            trades_total = payloads[1.0]["legs"][cell]["metrics"]["trade_count"]
            cell_kind = "leg"
        by_cell[cell] = {
            "schema": LEDGER_ROW_SCHEMA,
            "row_type": "scored_outcome",
            "cell": cell,
            "cell_kind": cell_kind,
            "stress": stress_block,
            "verdict": verdict,
            "trades_total": int(trades_total),
            "generated_utc": now,
            "scored_content_sha256": {
                _stress_key(s): payloads[s]["content_sha256"]
                for s in payloads},
        }

    rows = [by_cell[c] for c in sorted(by_cell)]
    observed = len(rows)
    published = sum(1 for r in rows if r.get("row_type") == "scored_outcome")
    header = {
        "schema": LEDGER_HEADER_SCHEMA,
        "row_type": "header",
        "observed_scored_denominator": observed,
        "published_scored_denominator": published,
        "budget_max_scored_cells": BUDGET_MAX_SCORED_CELLS,
        "go_phrase": GO_PHRASE,
        "freeze_commit": FREEZE_COMMIT_PLACEHOLDER,
        "created_utc": header_meta["created_utc"],
        "updated_utc": now,
    }
    tmp = ledger.with_suffix(".jsonl.tmp")
    tmp.write_text("".join(json.dumps(r, sort_keys=True) + "\n"
                           for r in [header] + rows))
    tmp.replace(ledger)
    return ledger
