#!/usr/bin/env python
"""scored_runner_v2.py — symbol-parameterized SCORED RUNNER V2 for
FUTURES-5SYM-PRESCORED-20261005 (NQ / 6E / 6B / 6J / 6A; ES retained as a
compatibility contract).

PREP INFRASTRUCTURE LAW: this runner is built for FUTURE registered cycles.
In THIS build it HARD-REFUSES the real governance dir unconditionally
(`--allow-real-governance` is itself refused — hard-compiled), so every run
that gets past preflight is, by construction, a synthetic-sandbox run stamped
SYNTHETIC-SANDBOX. The refusal behavior is production behavior and is tested
(test_refusals.py, test_isolation.py).

Lineage: adapted + hardened from the FUTURES-ES-PB1-V1 gate-6 scored runner
(extract: exec/_upstream_scored_runner.py, FAIL-record revision c17ab2bf;
spec: exec/_upstream_scored_runner_spec.md). The two upstream finalization
defects are FIXED here and proven by tests:

  BUG1-class (upstream: lock release raises => exit 0 + EXECUTION_COMPLETE +
  lock_released_status FINISHED, status written outside the try merely
  because release was CALLED):
    HERE: release is ALWAYS attempted (including on exception paths); a
    release that raises is recorded as a finalization failure and the run
    ends FAILED / non-zero with lock_released_status RELEASE_RAISED. The
    terminal status is computed AFTER release from measured evidence — never
    from "release was called". Proven by T11 (--test-fault fail_release).

  BUG2-class (upstream: terminal handoff write raises => exit 0 +
  EXECUTION_COMPLETE without the terminal artifact; same class for the
  ledger-summary path):
    HERE: the terminal handoff JSON, the ledger summary, the publication
    step and FINAL_STATUS.json are all guarded; a failure in ANY of them
    forces FAILED / non-zero; "EXECUTION_COMPLETE" appears in an output only
    when EVERY mandatory step (including lock release and every
    finalization write) succeeded. Proven by T12 (--test-fault
    fail_handoff_write), T13 (--test-fault fail_publication) and the
    fail_ledger_summary fault.

Refusal law (all pre-computation; each writes FINAL_STATUS.json + a REFUSED
ledger row (counts_observed=false) + refusal_record.json, exit non-zero):
  REFUSED_BAD_ARGS                      malformed/missing CLI arguments
  REFUSED_ALLOW_REAL_GOVERNANCE_DISABLED  --allow-real-governance (dead law)
  REFUSED_REAL_GOVERNANCE_DIR           governance/output path resolves to
                                        the real governance dir / real
                                        CYCLE_REGISTRY.json / real plans dir
  REFUSED_REGISTRY_MISMATCH             registry unreadable, malformed, or
                                        cycle-id absent (+ declared-branch
                                        mismatch)
  REFUSED_NO_GO_ARTIFACT                GO file absent
  REFUSED_GO_ARTIFACT_INVALID           GO unparseable / schema wrong
  REFUSED_GO_CYCLE_MISMATCH             GO names a different cycle-id
  REFUSED_GO_NOT_OWNER_TYPED            delegation markers or typed_by
                                        != OWNER (upstream lineage)
  REFUSED_GO_PHRASE_MISMATCH            verbatim != byte-exact
                                        "GO <CYCLE-ID> SCORED EXECUTION"
  REFUSED_NO_AUTHORITY                  authority file absent
  REFUSED_AUTHORITY_INVALID             authority content invalid
  REFUSED_CONTRACTS_INVALID             symbol_contracts.json missing/bad
  REFUSED_INPUT_MANIFEST_INVALID        manifest unreadable/malformed
  REFUSED_MISSING_PRIOR_ARTIFACT        required prior artifact absent (T19)
  REFUSED_INPUT_DRIFT                   re-hashed input sha mismatch (T6)
  REFUSED_SPEC_INVALID                  SPEC packet malformed
  REFUSED_COST_MANIFEST_INVALID         cost manifest malformed
  REFUSED_STALE_IN_PROGRESS             stale IN_PROGRESS marker and
                                        --resume-with-recovery-check absent
                                        or failing integrity checks (T20)
  REFUSED_LOCK_DRIFT                    lock file free but a RUNNING registry
                                        row exists (bookkeeping drift)
  NOT_RUN_RESOURCE_CONFLICT             heavy lock held (exit 75, T8)

Failure codes (non-zero exit 3, FINAL_STATUS failed_step set):
  FAILED_POST_ACQUIRE_FOREIGN_ROW / FAILED_POST_ACQUIRE_LOST_FLOCK (T9),
  FAILED_COMPUTE, FAILED_LEDGER_APPEND, FAILED_TWIN_MISMATCH (T15, with
  reconciliation_report.json), FAILED_PUBLICATION (T13, quarantine marker,
  observed denominator preserved), FAILED_LEDGER_SUMMARY, FAILED_LOCK_RELEASE
  (BUG1 proof, T11), FAILED_HANDOFF_WRITE (BUG2 proof, T12),
  FAILED_FINAL_STATUS_WRITE, FAILED_UNCAUGHT (T10-class).

Exit codes: 0 = EXECUTION_COMPLETE (every mandatory step measured done);
2 = REFUSED_*; 3 = FAILED_*; 75 = NOT_RUN_RESOURCE_CONFLICT. Never a silent
pass: every non-success path exits non-zero with a machine-readable
FINAL_STATUS.json.

Ledger law: append-only JSONL, reopened and appended (never truncated);
identity-ID idempotency — a TRIAL whose identity_id already has a TRIAL row
is skipped and recorded as a DUPLICATE_RETRY row (never recomputed into the
observed denominator); observed (distinct TRIAL identity ids) and published
counters are tracked separately; publication failure keeps the observed
denominator in the ledger and writes a quarantine marker.

Determinism: no wall-clock fields in any artifact; money rounded to 6dp;
fills at next-bar open rounded to the era tick grid; identical inputs give
byte-identical trial/fold records (the reproduction twin asserts this).

INTENT EXECUTION MODE (wave-4 WIRING-FIX, schema
futures_5sym_prescored/intent_packet@1): the positional spec_packet@1 above
remains the ACCOUNTING-TEST encoding; the intent packet is the REAL
intent-execution seam. It carries the adapter-declared trade timeline
VERBATIM — per-intent direction, signal/decision/entry/exit timestamps,
declared fill prices and exit reason (horizon | stop_loss | session_close) —
and EVERY intent executes as ITS OWN trade (mixed directions inside one
identity both execute; ordering preserved) through the SAME accounting law
as compute_all: entry-bar era law, tick-grid fill rounding, per-side cost
formula, 6dp money, fold membership from the packet's own folds, warmup and
calendar-exclusion law from the packet. The fixture bars are the EXECUTION
TIMELINE ONLY (date -> bar index for fold/warmup/exclusion law); fill prices
come from the intent records, never from a re-encoded price series. The
same CLI, authority gates, lock lifecycle, twin, ledger idempotency,
publication and finalization law apply unchanged; a zero-intent identity is
a spec-valid processed anchor (TRIAL row, observed denominator counts it).
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
import sys
import uuid
from datetime import date
from pathlib import Path

CYCLE_ID_DEFAULT = "FUTURES-5SYM-PRESCORED-20261005"
ENGINE_VERSION = "runner_v2@1"
SANDBOX_STAMP = "SYNTHETIC-SANDBOX"

# --- real-root authority paths: hard-refused targets (PREP build) ----------
REAL_GOVERNANCE_DIR = "/Users/hoangminhlong/.my-quantitative-governance"
REAL_ROOT_REGISTRY = "/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json"
REAL_PLANS_DIR = os.path.dirname(REAL_ROOT_REGISTRY)

EXIT_OK, EXIT_REFUSED, EXIT_FAILED, EXIT_CONFLICT = 0, 2, 3, 75

DELEGATION_MARKERS = ("delegat", "on behalf of", "thay mặt", "proxy")

MANDATORY_STEPS = [
    "preflight", "lock_acquire", "post_acquire_recheck", "compute",
    "ledger_append", "twin_verify", "publication", "ledger_summary",
    "lock_release", "handoff_write", "final_status_write",
]

KNOWN_FAULTS = {
    "fail_release", "fail_handoff_write", "fail_publication",
    "fail_ledger_summary", "force_twin_drift", "post_acquire_foreign_row",
    "mid_run_exception",
}

LEDGER_SCHEMA = "futures_5sym_prescored/ledger_row@1"
INTENT_PACKET_SCHEMA = "futures_5sym_prescored/intent_packet@1"
INTENT_EXIT_REASONS = ("horizon", "stop_loss", "take_profit", "session_close")


def canonical_go_phrase(cycle_id: str) -> str:
    return f"GO {cycle_id} SCORED EXECUTION"


# ------------------------------------------------------------------ errors

class SandboxTestFault(Exception):
    """A --test-fault injection fired (sandbox-only by construction)."""

    def __init__(self, name: str, step: str):
        super().__init__(f"injected test fault {name!r} at step {step!r}")
        self.name, self.step = name, step


class AbortRun(Exception):
    """Run-level abort AFTER lock acquisition (post-acquire recheck)."""

    def __init__(self, code: str, step: str, detail: dict):
        super().__init__(code)
        self.code, self.step, self.detail = code, step, detail


class Refusal(Exception):
    """A preflight refusal gate fired (pre-computation, pre-lock)."""

    def __init__(self, code: str, detail: dict):
        super().__init__(code)
        self.code, self.detail = code, detail


# ---------------------------------------------------------------- utilities

def sha256_file(path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_json(path):
    p = Path(path)
    if not p.is_file():
        return None, f"missing file {p}"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        return None, f"unreadable/unparseable {p}: {exc}"


def walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v)


def atomic_write_json(path, obj) -> None:
    """tmp-file + os.replace atomic write (fault injection happens in the
    caller via inject(), BEFORE this is reached, mirroring a mid-write
    OSError at the boundary)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(
        json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    os.replace(tmp, p)


def resolve_under(manifest_dir: str, path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(manifest_dir, path)


# ------------------------------------------------------------- fault inject

def inject(faults: set, name: str, step: str) -> None:
    if name in faults:
        raise SandboxTestFault(name, step)


# --------------------------------------------------------- symbol contracts

class ContractError(Exception):
    pass


def load_symbol_contracts(path: str) -> dict:
    data, err = load_json(path)
    if err:
        raise ContractError(err)
    if data.get("schema") != "futures_5sym_prescored/symbol_contracts@1":
        raise ContractError(f"schema {data.get('schema')!r} unexpected")
    contracts = data.get("contracts")
    if not isinstance(contracts, dict) or not contracts:
        raise ContractError("no contracts table")
    for sym, c in contracts.items():
        if not isinstance(c.get("era_table"), list) or not c["era_table"]:
            raise ContractError(f"{sym}: empty era_table")
        eras = []
        for e in c["era_table"]:
            try:
                frm = date.fromisoformat(e["effective_from"])
            except (KeyError, ValueError) as exc:
                raise ContractError(f"{sym}: bad era effective_from: {exc}")
            for k in ("tick_size", "tick_value_usd", "multiplier"):
                if not isinstance(e.get(k), (int, float)) or e[k] <= 0:
                    raise ContractError(f"{sym}: era {e.get('era')} bad {k}")
            eras.append((frm, e))
        eras.sort(key=lambda x: x[0])
        c["_eras_sorted"] = eras
        if c.get("long_base_sign") != 1:
            raise ContractError(f"{sym}: long_base_sign must be +1 in this "
                                "build (runner invariant)")
    return data


def era_for(contract: dict, ts: date) -> dict:
    """LAST era whose effective_from <= ts (inclusive)."""
    chosen = contract["_eras_sorted"][0][1]
    for frm, era in contract["_eras_sorted"]:
        if frm <= ts:
            chosen = era
        else:
            break
    return chosen


def round_to_tick(px: float, tick: float) -> float:
    return round(round(px / tick) * tick, 10)


# ------------------------------------------------------------- data loading

class FixtureError(Exception):
    pass


def load_fixture_csv(path: str) -> list[dict]:
    bars = []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                bars.append({
                    "ts": date.fromisoformat(row["ts"].strip()),
                    "open": float(row["open"]), "high": float(row["high"]),
                    "low": float(row["low"]), "close": float(row["close"]),
                })
    except (OSError, KeyError, ValueError) as exc:
        raise FixtureError(f"{path}: {exc}")
    if not bars:
        raise FixtureError(f"{path}: zero bars")
    return bars


# ------------------------------------------------------------------- engine

class SpecError(Exception):
    pass


def _r6(x: float) -> float:
    return round(x, 6)


def compute_all(spec: dict, bars_by_symbol: dict, contracts_doc: dict,
                cost_manifest: dict, faults: set) -> dict:
    """Deterministic engine pass. Fills at next-bar open rounded to the era
    tick grid; cost per side = fee(tier) + (spread+slip ticks)*tick_value(era);
    gross PnL per the contract pnl_law. Pure: no shared mutable state — the
    reproduction twin calls this again on the same inputs."""
    contracts = contracts_doc["contracts"]
    fee_by_tier = cost_manifest["fee_per_side_usd_by_tier"]
    spread_by = cost_manifest["spread_ticks_by_stress"]
    slip_by = cost_manifest["slip_ticks_by_stress"]

    identities = spec["identities"]
    folds = sorted(spec["folds"], key=lambda f: f["start_bar"])

    id_records = {}
    for ident in identities:
        iid, sym = ident["identity_id"], ident["symbol"]
        contract = contracts[sym]
        bars = bars_by_symbol[sym]
        n = len(bars)
        hold = int(ident["hold_bars"])
        if hold < 1:
            raise SpecError(f"{iid}: hold_bars must be >= 1")
        fee = float(fee_by_tier[ident["cost_tier"]])
        stress_key = f"{float(ident['stress']):.1f}"
        if stress_key not in spread_by or stress_key not in slip_by:
            raise SpecError(f"{iid}: stress {stress_key} not in cost manifest")
        spread_t = float(spread_by[stress_key])
        slip_t = float(slip_by[stress_key])

        if ident["arm"] == "long-if-bar-up":
            direction, signal_ok = 1, (lambda b: b["close"] > b["open"])
        elif ident["arm"] == "short-if-bar-down":
            direction, signal_ok = -1, (lambda b: b["close"] < b["open"])
        else:
            raise SpecError(f"{iid}: unknown arm {ident['arm']!r}")

        fold_recs, tot_trades = [], 0
        tot_gross = tot_cost = tot_net = 0.0
        for fold in folds:
            trades, skipped = [], 0
            f_gross = f_cost = f_net = 0.0
            for i in range(fold["start_bar"],
                           min(fold["end_bar"], n - 1 - hold)):
                if not signal_ok(bars[i]):
                    continue
                i_exit = i + 1 + hold
                if i_exit >= n:
                    skipped += 1
                    continue
                entry_ts, exit_ts = bars[i + 1]["ts"], bars[i_exit]["ts"]
                era = era_for(contract, entry_ts)
                tick = float(era["tick_size"])
                tval = float(era["tick_value_usd"])
                usd_per_unit = tval / tick
                entry_px = round_to_tick(bars[i + 1]["open"], tick)
                exit_px = round_to_tick(bars[i_exit]["open"], tick)
                gross = direction * (exit_px - entry_px) * usd_per_unit
                cost_side = fee + (spread_t + slip_t) * tval
                cost = 2.0 * cost_side
                net = gross - cost
                trades.append({
                    "i_signal": i, "i_entry": i + 1, "i_exit": i_exit,
                    "entry_ts": entry_ts.isoformat(),
                    "exit_ts": exit_ts.isoformat(),
                    "entry_price": entry_px, "exit_price": exit_px,
                    "direction": direction, "era": era["era"],
                    "tick_size": tick, "tick_value_usd": tval,
                    "gross_pnl_usd": _r6(gross), "cost_usd": _r6(cost),
                    "net_pnl_usd": _r6(net),
                })
                f_gross += gross
                f_cost += cost
                f_net += net
            tot_trades += len(trades)
            tot_gross += f_gross
            tot_cost += f_cost
            tot_net += f_net
            fold_recs.append({
                "fold_id": fold["fold_id"], "n_trades": len(trades),
                "n_skipped_no_exit": skipped,
                "gross_pnl_usd": _r6(f_gross), "cost_usd": _r6(f_cost),
                "net_pnl_usd": _r6(f_net), "trades": trades,
            })
        id_records[iid] = {
            "record_type": "TRIAL", "identity_id": iid, "symbol": sym,
            "arm": ident["arm"], "cost_tier": ident["cost_tier"],
            "stress": float(ident["stress"]), "hold_bars": hold,
            "folds": fold_recs,
            "totals": {"n_trades": tot_trades, "gross_pnl_usd": _r6(tot_gross),
                       "cost_usd": _r6(tot_cost), "net_pnl_usd": _r6(tot_net)},
            "engine_version": ENGINE_VERSION,
        }

    fold_records = {}
    for fold in folds:
        fid = fold["fold_id"]
        per_id = {iid: {"n_trades": r_f["n_trades"],
                        "gross_pnl_usd": r_f["gross_pnl_usd"],
                        "cost_usd": r_f["cost_usd"],
                        "net_pnl_usd": r_f["net_pnl_usd"]}
                  for iid, rec in id_records.items()
                  for r_f in rec["folds"] if r_f["fold_id"] == fid}
        fold_records[fid] = {
            "fold_id": fid, "identity_count": len(per_id),
            "n_trades": sum(v["n_trades"] for v in per_id.values()),
            "gross_pnl_usd": _r6(sum(v["gross_pnl_usd"]
                                     for v in per_id.values())),
            "cost_usd": _r6(sum(v["cost_usd"] for v in per_id.values())),
            "net_pnl_usd": _r6(sum(v["net_pnl_usd"]
                                   for v in per_id.values())),
            "by_identity": per_id,
        }
    return {"identities": id_records, "folds": fold_records}


# ------------------------------------------------------ intent-mode engine

def _iso_d(s, what: str) -> date:
    try:
        return date.fromisoformat(str(s).strip())
    except (TypeError, ValueError):
        raise SpecError(f"{what}: bad ISO date {s!r}")


def validate_intent_spec(spec: dict, contracts_doc: dict, cost_manifest: dict,
                         bar_counts: dict,
                         bars_by_symbol: dict | None = None) -> None:
    """Fail-closed validation for futures_5sym_prescored/intent_packet@1.
    Same refusal surface as validate_spec (SpecError -> REFUSED_SPEC_INVALID);
    everything here is PRE-COMPUTATION (pre-lock, zero denominator)."""
    if spec.get("schema") != INTENT_PACKET_SCHEMA:
        raise SpecError(f"schema {spec.get('schema')!r} unexpected")
    if spec.get("provenance") != "SYNTHETIC":
        raise SpecError("intent packet provenance must be 'SYNTHETIC' in "
                        "this PREP build (real-data execution NOT_RUN; "
                        "existing law)")
    if not isinstance(spec.get("identities"), list) or not spec["identities"]:
        raise SpecError("identities must be a non-empty list")
    if not isinstance(spec.get("folds"), list) or not spec["folds"]:
        raise SpecError("folds must be a non-empty list")
    contracts = contracts_doc["contracts"]
    fee_by_tier = cost_manifest.get("fee_per_side_usd_by_tier")
    spread_by = cost_manifest.get("spread_ticks_by_stress")
    slip_by = cost_manifest.get("slip_ticks_by_stress")
    if not isinstance(fee_by_tier, dict) or not fee_by_tier:
        raise SpecError("cost manifest: fee_per_side_usd_by_tier missing")
    if not isinstance(spread_by, dict) or not isinstance(slip_by, dict):
        raise SpecError("cost manifest: spread/slip stress tables missing")
    warmup = spec.get("warmup_bars", 0)
    if not isinstance(warmup, int) or isinstance(warmup, bool) or warmup < 0:
        raise SpecError("warmup_bars must be int >= 0")
    excl = spec.get("calendar_excluded_dates") or []
    if not isinstance(excl, list):
        raise SpecError("calendar_excluded_dates must be a list")
    excl_set = set()
    for d in excl:
        dd = _iso_d(d, "calendar_excluded_dates")
        if dd in excl_set:
            raise SpecError(f"duplicate calendar exclusion {d!r}")
        excl_set.add(dd)
    folds = sorted(spec["folds"], key=lambda f: f["start_bar"])
    fold_ids = set()
    prev_end = None
    for fold in folds:
        fid = fold.get("fold_id")
        if not fid or fid in fold_ids:
            raise SpecError(f"fold id missing/duplicate: {fid!r}")
        fold_ids.add(fid)
        s, e = fold.get("start_bar"), fold.get("end_bar")
        if not isinstance(s, int) or not isinstance(e, int) or s < 0 or e <= s:
            raise SpecError(f"fold {fid}: bad start/end bars")
        if prev_end is not None and s < prev_end:
            raise SpecError(f"fold {fid}: overlaps the previous fold — a "
                            "trade at the seam must land in EXACTLY one fold")
        prev_end = e
        if s < warmup:
            raise SpecError(f"fold {fid} starts at {s} before warmup_bars "
                            f"{warmup} — the warmup region must be fold-free")
    seen_ids = set()
    for ident in spec["identities"]:
        iid = ident.get("identity_id")
        if not iid or iid in seen_ids:
            raise SpecError(f"identity id missing/duplicate: {iid!r}")
        seen_ids.add(iid)
        sym = ident.get("symbol")
        if sym not in contracts:
            raise SpecError(f"{iid}: symbol {sym!r} not in symbol contracts")
        if ident.get("cost_tier") not in fee_by_tier:
            raise SpecError(f"{iid}: cost tier {ident.get('cost_tier')!r} "
                            "not in cost manifest")
        try:
            sk = f"{float(ident.get('stress')):.1f}"
        except (TypeError, ValueError):
            raise SpecError(f"{iid}: bad stress {ident.get('stress')!r}")
        if sk not in spread_by or sk not in slip_by:
            raise SpecError(f"{iid}: stress {sk} not in cost manifest")
        horizon = ident.get("holding_horizon_bars")
        if not isinstance(horizon, int) or isinstance(horizon, bool) or \
                horizon < 1:
            raise SpecError(f"{iid}: holding_horizon_bars must be int >= 1")
        intents = ident.get("intents")
        if not isinstance(intents, list):
            raise SpecError(f"{iid}: intents must be a list (an empty list "
                            "is a legal zero-trade anchor)")
        n = bar_counts.get(sym)
        if n is None:
            raise SpecError(f"{iid}: no fixture bars for {sym}")
        for fold in folds:
            if fold["end_bar"] > n:
                raise SpecError(f"fold {fold['fold_id']} end "
                                f"{fold['end_bar']} exceeds {sym} bar count "
                                f"{n}")
        date_index = None
        if bars_by_symbol is not None:
            bars = bars_by_symbol[sym]
            date_index = {}
            for b in bars:
                if b["ts"] in date_index:
                    raise SpecError(f"{sym}: duplicate bar date {b['ts']}")
                date_index[b["ts"]] = None
        for pos, it in enumerate(intents):
            if not isinstance(it, dict):
                raise SpecError(f"{iid}: intent {pos} must be an object")
            if it.get("intent_seq") != pos:
                raise SpecError(f"{iid}: intent {pos} has intent_seq "
                                f"{it.get('intent_seq')!r} — submission "
                                "order must be 0..n-1 with no reordering")
            if it.get("direction") not in (1, -1):
                raise SpecError(f"{iid}: intent {pos} direction must be +/-1")
            if it.get("exit_reason") not in INTENT_EXIT_REASONS:
                raise SpecError(f"{iid}: intent {pos} exit_reason "
                                f"{it.get('exit_reason')!r} not in "
                                f"{INTENT_EXIT_REASONS}")
            sig_d = _iso_d(it.get("signal_ts"), f"{iid} intent {pos} signal_ts")
            e_d = _iso_d(it.get("entry_ts"), f"{iid} intent {pos} entry_ts")
            x_d = _iso_d(it.get("exit_ts"), f"{iid} intent {pos} exit_ts")
            if not (sig_d <= e_d <= x_d):
                raise SpecError(f"{iid}: intent {pos} timestamps must satisfy "
                                "signal_ts <= entry_ts <= exit_ts")
            for k in ("entry_price", "exit_price"):
                v = it.get(k)
                if not isinstance(v, (int, float)) or isinstance(v, bool) \
                        or not (v > 0):
                    raise SpecError(f"{iid}: intent {pos} {k} must be a "
                                    "positive number")
            if date_index is None:
                continue
            if e_d not in date_index and e_d not in excl_set:
                raise SpecError(f"{iid}: intent {pos} entry_ts {e_d} is "
                                "neither a panel bar date nor a declared "
                                "calendar exclusion")
            if e_d in date_index and x_d not in date_index:
                raise SpecError(f"{iid}: intent {pos} exit_ts {x_d} is not a "
                                "panel bar date")
            if e_d in date_index and x_d in date_index:
                eb = _panel_index(bars_by_symbol[sym], e_d)
                xb = _panel_index(bars_by_symbol[sym], x_d)
                if not (eb <= xb <= eb + horizon):
                    raise SpecError(f"{iid}: intent {pos} exit bar {xb} "
                                    f"outside the holding window "
                                    f"[{eb}, {eb + horizon}]")
                if it.get("exit_reason") == "horizon" and xb != eb + horizon:
                    raise SpecError(f"{iid}: intent {pos} exit_reason "
                                    "'horizon' requires exit bar == entry "
                                    f"bar + holding_horizon_bars "
                                    f"({eb + horizon}), got {xb}")


def _panel_index(bars: list, d: date) -> int:
    for i, b in enumerate(bars):
        if b["ts"] == d:
            return i
    raise SpecError(f"date {d} not in panel")


def compute_intents(spec: dict, bars_by_symbol: dict, contracts_doc: dict,
                    cost_manifest: dict, faults: set) -> dict:
    """Deterministic INTENT-MODE engine pass. Every wired intent executes as
    ITS OWN trade: per-intent direction, timestamps and declared fills
    preserved verbatim in the journal; ordering preserved; accounting
    IDENTICAL to compute_all (entry-bar era law, tick-grid rounding, per-side
    cost formula, 6dp money). Pure: the reproduction twin calls it again."""
    contracts = contracts_doc["contracts"]
    fee_by_tier = cost_manifest["fee_per_side_usd_by_tier"]
    spread_by = cost_manifest["spread_ticks_by_stress"]
    slip_by = cost_manifest["slip_ticks_by_stress"]

    identities = spec["identities"]
    folds = sorted(spec["folds"], key=lambda f: f["start_bar"])
    warmup = int(spec.get("warmup_bars") or 0)
    excluded_dates = {_iso_d(d, "calendar_excluded_dates")
                      for d in (spec.get("calendar_excluded_dates") or [])}

    id_records = {}
    for ident in identities:
        iid, sym = ident["identity_id"], ident["symbol"]
        contract = contracts[sym]
        bars = bars_by_symbol[sym]
        date_index = {b["ts"]: i for i, b in enumerate(bars)}
        fee = float(fee_by_tier[ident["cost_tier"]])
        stress_key = f"{float(ident['stress']):.1f}"
        spread_t = float(spread_by[stress_key])
        slip_t = float(slip_by[stress_key])
        horizon = int(ident["holding_horizon_bars"])

        journal, excluded = [], []
        for seq, it in enumerate(ident["intents"]):
            direction = int(it["direction"])
            reason = it["exit_reason"]
            sig_s, e_s, x_s = it["signal_ts"], it["entry_ts"], it["exit_ts"]
            e_d = _iso_d(e_s, f"{iid} intent {seq} entry_ts")
            if e_d in excluded_dates:
                excluded.append({"intent_seq": seq, "direction": direction,
                                 "reason": "calendar_excluded",
                                 "entry_ts": e_s, "signal_ts": sig_s,
                                 "exit_ts": x_s})
                continue
            eb = date_index[e_d]
            if eb < warmup or eb < folds[0]["start_bar"]:
                excluded.append({"intent_seq": seq, "direction": direction,
                                 "reason": "warmup", "entry_ts": e_s,
                                 "signal_ts": sig_s, "exit_ts": x_s,
                                 "entry_bar": eb})
                continue
            fid = None
            for fold in folds:
                if fold["start_bar"] <= eb < fold["end_bar"]:
                    fid = fold["fold_id"]
                    break
            if fid is None:
                raise SpecError(f"{iid}: intent {seq} entry bar {eb} is in "
                                "no fold — fold law must cover every "
                                "executable bar")
            xb = date_index[_iso_d(x_s, f"{iid} intent {seq} exit_ts")]
            era = era_for(contract, e_d)
            tick = float(era["tick_size"])
            tval = float(era["tick_value_usd"])
            usd_per_unit = tval / tick
            entry_px = round_to_tick(float(it["entry_price"]), tick)
            exit_px = round_to_tick(float(it["exit_price"]), tick)
            gross = direction * (exit_px - entry_px) * usd_per_unit
            cost_side = fee + (spread_t + slip_t) * tval
            cost = 2.0 * cost_side
            net = gross - cost
            journal.append({
                "intent_seq": seq, "direction": direction,
                "signal_ts": sig_s, "entry_ts": e_s, "exit_ts": x_s,
                "entry_bar": eb, "exit_bar": xb,
                "entry_price": entry_px, "exit_price": exit_px,
                "exit_reason": reason, "fold_id": fid,
                "era": era["era"], "tick_size": tick, "tick_value_usd": tval,
                "gross_pnl_usd": _r6(gross), "cost_usd": _r6(cost),
                "net_pnl_usd": _r6(net),
            })

        fold_recs = []
        for fold in folds:
            fid = fold["fold_id"]
            f_trades = [t for t in journal if t["fold_id"] == fid]
            f_excl = [x for x in excluded
                      if x.get("entry_bar") is not None
                      and fold["start_bar"] <= x["entry_bar"] < fold["end_bar"]]
            fold_recs.append({
                "fold_id": fid, "n_trades": len(f_trades),
                "n_excluded": len(f_excl), "n_skipped_no_exit": 0,
                "gross_pnl_usd": _r6(sum(t["gross_pnl_usd"]
                                         for t in f_trades)),
                "cost_usd": _r6(sum(t["cost_usd"] for t in f_trades)),
                "net_pnl_usd": _r6(sum(t["net_pnl_usd"]
                                       for t in f_trades)),
                "trades": f_trades,
            })
        id_records[iid] = {
            "record_type": "TRIAL", "identity_id": iid, "symbol": sym,
            "mode": "intent", "cost_tier": ident["cost_tier"],
            "stress": float(ident["stress"]),
            "holding_horizon_bars": horizon,
            "warmup_bars": warmup,
            "n_intents_declared": len(ident["intents"]),
            "journal": journal, "excluded_intents": excluded,
            "folds": fold_recs,
            "totals": {"n_trades": len(journal),
                       "n_excluded": len(excluded),
                       "gross_pnl_usd": _r6(sum(t["gross_pnl_usd"]
                                                for t in journal)),
                       "cost_usd": _r6(sum(t["cost_usd"]
                                           for t in journal)),
                       "net_pnl_usd": _r6(sum(t["net_pnl_usd"]
                                              for t in journal))},
            "engine_version": ENGINE_VERSION,
        }

    fold_records = {}
    for fold in folds:
        fid = fold["fold_id"]
        per_id = {iid: {"n_trades": r_f["n_trades"],
                        "gross_pnl_usd": r_f["gross_pnl_usd"],
                        "cost_usd": r_f["cost_usd"],
                        "net_pnl_usd": r_f["net_pnl_usd"]}
                  for iid, rec in id_records.items()
                  for r_f in rec["folds"] if r_f["fold_id"] == fid}
        fold_records[fid] = {
            "fold_id": fid, "identity_count": len(per_id),
            "n_trades": sum(v["n_trades"] for v in per_id.values()),
            "gross_pnl_usd": _r6(sum(v["gross_pnl_usd"]
                                     for v in per_id.values())),
            "cost_usd": _r6(sum(v["cost_usd"] for v in per_id.values())),
            "net_pnl_usd": _r6(sum(v["net_pnl_usd"]
                                   for v in per_id.values())),
            "by_identity": per_id,
        }
    return {"identities": id_records, "folds": fold_records}


def structural_diff(a, b, path="$", out=None, cap=20):
    out = [] if out is None else out
    if len(out) >= cap:
        return out
    if type(a) is not type(b):
        out.append(f"{path}: type {type(a).__name__} != {type(b).__name__}")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{path}.{k}: missing in twin-a")
            elif k not in b:
                out.append(f"{path}.{k}: missing in twin-b")
            else:
                structural_diff(a[k], b[k], f"{path}.{k}", out, cap)
            if len(out) >= cap:
                break
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: len {len(a)} != {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                structural_diff(x, y, f"{path}[{i}]", out, cap)
                if len(out) >= cap:
                    break
    elif a != b:
        out.append(f"{path}: {a!r} != {b!r}")
    return out


# --------------------------------------------------------------------- lock

class HeavyLock:
    """Sandbox-canonical heavy lock: flock on <dir>/heavy.lock + a RUNNING
    row in <dir>/heavy_registry.json. Post-acquire recheck re-reads the
    registry (no foreign RUNNING row) and proves the flock is still held.
    Release is ALWAYS attempted; a release that raises propagates as a
    finalization failure (BUG1-class fix) — never force-unlocked."""

    def __init__(self, lock_dir: str, cycle_id: str):
        self.lock_dir = Path(lock_dir)
        self.lock_path = self.lock_dir / "heavy.lock"
        self.registry_path = self.lock_dir / "heavy_registry.json"
        self.cycle_id = cycle_id
        self.fd = None
        self.row = None
        self.acquired = False
        self.released_status = None  # RELEASED | RELEASE_RAISED | None

    # -- state -----------------------------------------------------------
    def _read_rows(self) -> list:
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            rows = data.get("rows", [])
            return rows if isinstance(rows, list) else []
        except (OSError, json.JSONDecodeError, AttributeError):
            return []

    def _write_rows(self, rows: list) -> None:
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.registry_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"schema":
                                   "futures_5sym_prescored/heavy_registry@1",
                                   "rows": rows}, indent=1) + "\n",
                       encoding="utf-8")
        os.replace(tmp, self.registry_path)

    def _flock_held_by_other(self) -> bool:
        try:
            fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o644)
        except OSError:
            return False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            return False
        except OSError:
            return True
        finally:
            os.close(fd)

    def inspect(self) -> dict:
        """FREE | HELD | DRIFT (lock free + RUNNING row present)."""
        if self._flock_held_by_other():
            return {"state": "HELD", "rows": self._read_rows()}
        running = [r for r in self._read_rows() if r.get("status") == "RUNNING"]
        if running:
            return {"state": "DRIFT", "rows": running}
        return {"state": "FREE", "rows": []}

    # -- lifecycle -------------------------------------------------------
    def acquire(self) -> None:
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o644)
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.row = {"cycle_id": self.cycle_id, "pid": os.getpid(),
                    "role": "EXEC", "status": "RUNNING",
                    "nonce": uuid.uuid4().hex[:12]}
        rows = [r for r in self._read_rows() if r.get("status") != "RUNNING"]
        rows.append(self.row)
        self._write_rows(rows)
        self.acquired = True

    def post_acquire_recheck(self, faults: set) -> None:
        if "post_acquire_foreign_row" in faults:
            rows = self._read_rows()
            rows.append({"cycle_id": "FOREIGN-PROBE-CYCLE", "pid": 999999999,
                         "role": "PROBE", "status": "RUNNING",
                         "nonce": "ffffffffffff"})
            self._write_rows(rows)
        rows = self._read_rows()
        foreign = [r for r in rows
                   if r.get("status") == "RUNNING"
                   and (r.get("nonce") != self.row["nonce"]
                        or r.get("cycle_id") != self.cycle_id
                        or r.get("pid") != os.getpid())]
        if foreign:
            raise AbortRun("FAILED_POST_ACQUIRE_FOREIGN_ROW",
                           "post_acquire_recheck",
                           {"foreign_rows": foreign})
        # fresh fd: an ACQUIRE here would mean our own hold was lost
        fd2 = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            try:
                fcntl.flock(fd2, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd2, fcntl.LOCK_UN)
                raise AbortRun("FAILED_POST_ACQUIRE_LOST_FLOCK",
                               "post_acquire_recheck",
                               {"reason": "a second descriptor acquired the "
                                          "flock — our hold was lost"})
            except OSError:
                pass  # EAGAIN: still held (by us) — hold proven
        finally:
            os.close(fd2)

    def release(self) -> None:
        """Remove our registry row, then unlock. Raises on failure — the
        caller (run flow) turns that into a finalization failure (BUG1 law);
        never force-unlocks, never kills, never deletes the lock file."""
        rows = [r for r in self._read_rows()
                if r.get("nonce") != self.row["nonce"]]
        self._write_rows(rows)
        fcntl.flock(self.fd, fcntl.LOCK_UN)

    def close_fd(self) -> None:
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None


# ------------------------------------------------------------------- ledger

class Ledger:
    """Append-only JSONL. reopen/append, never truncate. seq = max+1."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.rows: list[dict] = []
        self._scan()

    def _scan(self) -> None:
        self.rows = []
        if not self.path.is_file():
            return
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                self.rows.append(json.loads(line))

    def integrity_errors(self) -> list[str]:
        errs = []
        if not self.path.is_file():
            return errs
        with open(self.path, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    errs.append(f"line {i}: {exc}")
        return errs

    def _append(self, row: dict) -> None:
        seq = max((r.get("seq", 0) for r in self.rows), default=0) + 1
        row = dict(row, seq=seq)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False)
                     + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self.rows.append(row)
        return row

    def record_refusal(self, reason: str, note: str) -> dict:
        return self._append({"schema": LEDGER_SCHEMA, "row_type": "REFUSED",
                             "counts_observed": False, "identity_id": None,
                             "payload": {"reason": reason, "note": note}})

    def record_abort(self, code: str, detail: dict) -> dict:
        return self._append({"schema": LEDGER_SCHEMA, "row_type": "ABORT",
                             "counts_observed": False, "identity_id": None,
                             "payload": {"code": code, "detail": detail}})

    def trial_identity_ids(self) -> set:
        return {r["identity_id"] for r in self.rows
                if r.get("row_type") == "TRIAL" and r.get("identity_id")}

    def append_trials(self, spec: dict, computed: dict, provenance: dict,
                      faults: set) -> dict:
        """Identity-ID idempotency: existing identity => DUPLICATE_RETRY row,
        never recomputed, observed unchanged."""
        existing = self.trial_identity_ids()
        added, retried = [], []
        for iid, rec in computed["identities"].items():
            if iid in existing:
                retried.append(iid)
                self._append({"schema": LEDGER_SCHEMA,
                              "row_type": "DUPLICATE_RETRY",
                              "counts_observed": False, "identity_id": iid,
                              "payload": {"note": "identity already observed; "
                                                  "skipped, not recomputed"}})
                continue
            payload = dict(rec, provenance=provenance)
            self._append({"schema": LEDGER_SCHEMA, "row_type": "TRIAL",
                          "counts_observed": True, "identity_id": iid,
                          "payload": payload})
            existing.add(iid)
            added.append(iid)
            if "mid_run_exception" in faults and len(added) == 1 and \
                    not retried:
                raise RuntimeError("injected mid-run exception during "
                                   "ledger append")
        observed = self.trial_identity_ids()
        for fid, frec in computed["folds"].items():
            self._append({"schema": LEDGER_SCHEMA, "row_type": "FOLD",
                          "counts_observed": False, "identity_id": None,
                          "payload": dict(frec)})
        return {"added": added, "retried": retried,
                "observed_identity_count": len(observed)}

    def summary(self) -> dict:
        counts = {}
        for r in self.rows:
            counts[r["row_type"]] = counts.get(r["row_type"], 0) + 1
        return {"schema": "futures_5sym_prescored/ledger_summary@1",
                "row_type_counts": counts,
                "observed_identity_count": len(self.trial_identity_ids()),
                "total_rows": len(self.rows),
                "ledger_sha256": sha256_file(self.path)}


# -------------------------------------------------------------- run state

class RunState:
    def __init__(self, cycle_id: str, run_label: str):
        self.cycle_id = cycle_id
        self.run_label = run_label
        self.failures: list[dict] = []       # {code, step, detail}
        self.finalization_failures: list[str] = []
        self.mandatory = {s: False for s in MANDATORY_STEPS}
        self.refusals: list[str] = []
        self.failure_code = None
        self.failed_step = None
        self.computation_complete = False
        self.observed_count = 0
        self.published_count = None
        self.lock_acquired = False
        self.lock_released_status = None
        self.handoff = None

    def fail(self, code: str, step: str, detail) -> None:
        self.failures.append({"code": code, "step": step,
                              "detail": detail})
        if self.failure_code is None:
            self.failure_code, self.failed_step = code, step

    def finfail(self, msg: str) -> None:
        self.finalization_failures.append(msg)

    def core_complete(self) -> bool:
        """Every step UP TO the terminal handoff is measured done and clean.
        The handoff/final-status steps are excluded here (they cannot be
        done yet); terminal_state() still requires them for success."""
        return (not self.refusals and not self.failures
                and not self.finalization_failures
                and all(v for k, v in self.mandatory.items()
                        if k not in ("handoff_write", "final_status_write")))

    def terminal_state(self, ignore_missing=()) -> tuple[str, int]:
        if self.refusals:
            code = self.refusals[-1]
            rc = EXIT_CONFLICT if code == "NOT_RUN_RESOURCE_CONFLICT" \
                else EXIT_REFUSED
            return ("NOT_RUN_RESOURCE_CONFLICT" if rc == EXIT_CONFLICT
                    else "REFUSED"), rc
        if self.failures:
            return "FAILED", EXIT_FAILED
        if self.finalization_failures:
            return "FAILED", EXIT_FAILED
        done = all(v for k, v in self.mandatory.items()
                   if k not in ignore_missing)
        if done:
            return "EXECUTION_COMPLETE", EXIT_OK
        return "FAILED", EXIT_FAILED  # mandatory step missing => not success


# ------------------------------------------------------------------- main

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="FUTURES-5SYM-PRESCORED scored runner V2 (PREP "
                    "infrastructure; refuses the real governance dir)")
    for flag, help_ in [
        ("--cycle-id", f"cycle id (default {CYCLE_ID_DEFAULT})"),
        ("--governance-dir", "governance dir (sandbox; real dir refused)"),
        ("--go-artifact", "GO artifact JSON path"),
        ("--authority-file", "authority pack JSON path"),
        ("--input-manifest", "frozen input manifest JSON"),
        ("--spec-packet", "frozen SPEC packet JSON"),
        ("--cost-manifest", "frozen cost manifest JSON"),
        ("--symbol-contracts", "symbol contract specs JSON"),
        ("--ledger", "append-only trial ledger JSONL (sandbox)"),
        ("--run-dir", "run output directory (sandbox)"),
        ("--final-status-out", "FINAL_STATUS.json output path (sandbox)"),
        ("--run-label", "run label (default run1)"),
    ]:
        ap.add_argument(flag, default=None, help=help_)
    ap.add_argument("--allow-real-governance", action="store_true",
                    help="DEAD LAW in this PREP build: always refused")
    ap.add_argument("--resume-with-recovery-check", action="store_true",
                    help="allow a stale IN_PROGRESS marker after integrity "
                         "checks (marker parseable + ledger lines all "
                         "parseable)")
    ap.add_argument("--test-fault", default=None,
                    help="comma-separated fault names (sandbox-only): "
                         + ",".join(sorted(KNOWN_FAULTS)))
    return ap


def under(real: str, p: str) -> bool:
    rp = os.path.realpath(os.path.abspath(p))
    rr = os.path.realpath(os.path.abspath(real))
    return rp == rr or rp.startswith(rr + os.sep)


def check_real_governance(args) -> list[str]:
    """Dedicated sandbox-governance-dir refusal: any of the governance dir,
    the registry path, or the sandbox outputs resolving into the real
    governance dir / real plans dir / real root registry => refuse."""
    v = []
    gov = args["governance_dir"]
    if gov and under(REAL_GOVERNANCE_DIR, gov):
        v.append(f"governance-dir resolves under {REAL_GOVERNANCE_DIR}")
    if gov and under(REAL_PLANS_DIR, gov):
        v.append(f"governance-dir resolves under the real plans dir "
                 f"{REAL_PLANS_DIR}")
    reg = args["registry_json"]
    if reg and (under(REAL_GOVERNANCE_DIR, reg) or
                os.path.realpath(os.path.abspath(reg)) ==
                os.path.realpath(REAL_ROOT_REGISTRY)):
        v.append(f"registry path resolves to the real root registry "
                 f"{REAL_ROOT_REGISTRY}")
    for key in ("ledger", "run_dir", "final_status_out"):
        p = args[key]
        if p and under(REAL_GOVERNANCE_DIR, p):
            v.append(f"{key} resolves under {REAL_GOVERNANCE_DIR}")
    return v


def validate_spec(spec: dict, contracts_doc: dict, cost_manifest: dict,
                  bar_counts: dict) -> None:
    if spec.get("schema") != "futures_5sym_prescored/spec_packet@1":
        raise SpecError(f"schema {spec.get('schema')!r} unexpected")
    if not isinstance(spec.get("identities"), list) or \
            not spec["identities"]:
        raise SpecError("identities must be a non-empty list")
    if not isinstance(spec.get("folds"), list) or not spec["folds"]:
        raise SpecError("folds must be a non-empty list")
    contracts = contracts_doc["contracts"]
    fee_by_tier = cost_manifest.get("fee_per_side_usd_by_tier")
    spread_by = cost_manifest.get("spread_ticks_by_stress")
    slip_by = cost_manifest.get("slip_ticks_by_stress")
    if not isinstance(fee_by_tier, dict) or not fee_by_tier:
        raise SpecError("cost manifest: fee_per_side_usd_by_tier missing")
    if not isinstance(spread_by, dict) or not isinstance(slip_by, dict):
        raise SpecError("cost manifest: spread/slip stress tables missing")
    seen_ids = set()
    fold_ids = set()
    for fold in spec["folds"]:
        fid = fold.get("fold_id")
        if not fid or fid in fold_ids:
            raise SpecError(f"fold id missing/duplicate: {fid!r}")
        fold_ids.add(fid)
        s, e = fold.get("start_bar"), fold.get("end_bar")
        if not isinstance(s, int) or not isinstance(e, int) or s < 0 or \
                e <= s:
            raise SpecError(f"fold {fid}: bad start/end bars")
    for ident in spec["identities"]:
        iid = ident.get("identity_id")
        if not iid or iid in seen_ids:
            raise SpecError(f"identity id missing/duplicate: {iid!r}")
        seen_ids.add(iid)
        sym = ident.get("symbol")
        if sym not in contracts:
            raise SpecError(f"{iid}: symbol {sym!r} not in symbol contracts")
        if ident.get("arm") not in ("long-if-bar-up", "short-if-bar-down"):
            raise SpecError(f"{iid}: unknown arm {ident.get('arm')!r}")
        if ident.get("cost_tier") not in fee_by_tier:
            raise SpecError(f"{iid}: cost tier {ident.get('cost_tier')!r} "
                            "not in cost manifest")
        try:
            sk = f"{float(ident.get('stress')):.1f}"
        except (TypeError, ValueError):
            raise SpecError(f"{iid}: bad stress {ident.get('stress')!r}")
        if sk not in spread_by or sk not in slip_by:
            raise SpecError(f"{iid}: stress {sk} not in cost manifest")
        hold = ident.get("hold_bars")
        if not isinstance(hold, int) or hold < 1:
            raise SpecError(f"{iid}: hold_bars must be int >= 1")
        n = bar_counts.get(sym)
        if n is None:
            raise SpecError(f"{iid}: no fixture bars for {sym}")
        for fold in spec["folds"]:
            if fold["end_bar"] > n:
                raise SpecError(f"fold {fold['fold_id']} end "
                                f"{fold['end_bar']} exceeds {sym} bar count "
                                f"{n}")


def guarded_main(args, S: RunState) -> int:
    faults = args["faults"]
    gov = args["governance_dir"]

    # ---- 0. dead-law flag: --allow-real-governance is hard-refused --------
    if args["allow_real_governance"]:
        S.refusals.append("REFUSED_ALLOW_REAL_GOVERNANCE_DISABLED")
        raise Refusal("REFUSED_ALLOW_REAL_GOVERNANCE_DISABLED", {
            "law": "--allow-real-governance is hard-compiled to refuse in "
                   "this PREP build; there is no code path that touches the "
                   "real governance dir"})

    # ---- 1. sandbox-governance-dir violation (before ANY read/write) ------
    viol = check_real_governance(args)
    if viol:
        S.refusals.append("REFUSED_REAL_GOVERNANCE_DIR")
        raise Refusal("REFUSED_REAL_GOVERNANCE_DIR", {
            "law": "this PREP build refuses the real governance dir and the "
                   "real root registry unconditionally; all execution is "
                   "synthetic-sandbox only",
            "violations": viol})
    S.mandatory["preflight"] = True  # reached the sandbox path

    # ---- 2. registry (cycle row must exist) -------------------------------
    reg_data, err = load_json(args["registry_json"])
    if err:
        S.refusals.append("REFUSED_REGISTRY_MISMATCH")
        raise Refusal("REFUSED_REGISTRY_MISMATCH",
                      {"registry": args["registry_json"],
                       "error": err})
    rows = reg_data.get("cycles") if isinstance(reg_data, dict) else None
    if not isinstance(rows, list):
        S.refusals.append("REFUSED_REGISTRY_MISMATCH")
        raise Refusal("REFUSED_REGISTRY_MISMATCH",
                      {"registry": args["registry_json"],
                       "error": "no cycles array"})
    mine = [r for r in rows if isinstance(r, dict)
            and r.get("cycle_id") == args["cycle_id"]]
    if not mine:
        S.refusals.append("REFUSED_REGISTRY_MISMATCH")
        raise Refusal("REFUSED_REGISTRY_MISMATCH", {
            "registry": args["registry_json"],
            "error": f"cycle-id {args['cycle_id']!r} absent from registry",
            "registered_cycle_ids": sorted(
                r.get("cycle_id") for r in rows if isinstance(r, dict))})
    row = mine[0]
    if row.get("branch") is not None:
        import subprocess
        br = subprocess.run(
            ["git", "-C", args["worktree"], "rev-parse", "--abbrev-ref",
             "HEAD"] if args.get("worktree") else ["git", "rev-parse",
                                                   "--abbrev-ref", "HEAD"],
            capture_output=True, text=True)
        if br.returncode == 0 and br.stdout.strip() != row["branch"]:
            S.refusals.append("REFUSED_REGISTRY_MISMATCH")
            raise Refusal("REFUSED_REGISTRY_MISMATCH", {
                "error": "registry row branch mismatch",
                "row_branch": row["branch"],
                "actual_branch": br.stdout.strip()})

    # ---- 3. GO artifact ----------------------------------------------------
    go_path = args["go_artifact"]
    if not Path(go_path).is_file():
        S.refusals.append("REFUSED_NO_GO_ARTIFACT")
        raise Refusal("REFUSED_NO_GO_ARTIFACT", {
            "artifact": go_path,
            "note": "typed owner GO has not been recorded (expected pre-GO "
                    "state)"})
    go, err = load_json(go_path)
    if err or go.get("schema") != "futures_5sym_prescored/go_recorded@1":
        S.refusals.append("REFUSED_GO_ARTIFACT_INVALID")
        raise Refusal("REFUSED_GO_ARTIFACT_INVALID",
                      {"artifact": go_path, "error": err})
    if go.get("cycle_id") != args["cycle_id"]:
        S.refusals.append("REFUSED_GO_CYCLE_MISMATCH")
        raise Refusal("REFUSED_GO_CYCLE_MISMATCH", {
            "artifact": go_path,
            "go_cycle_id": go.get("cycle_id"),
            "expected": args["cycle_id"]})
    k2 = go.get("key_owner_go")
    if not isinstance(k2, dict):
        S.refusals.append("REFUSED_GO_ARTIFACT_INVALID")
        raise Refusal("REFUSED_GO_ARTIFACT_INVALID",
                      {"error": "missing key_owner_go object"})
    for s in walk_strings(go):
        low = s.lower()
        for marker in DELEGATION_MARKERS:
            if marker in low:
                S.refusals.append("REFUSED_GO_NOT_OWNER_TYPED")
                raise Refusal("REFUSED_GO_NOT_OWNER_TYPED", {
                    "delegation_marker": marker,
                    "lineage": "upstream test case 3a-c "
                               "(_upstream_test_runner_refusals.py)"})
    if k2.get("typed_by_owner") is not True or k2.get("typed_by") != "OWNER":
        S.refusals.append("REFUSED_GO_NOT_OWNER_TYPED")
        raise Refusal("REFUSED_GO_NOT_OWNER_TYPED", {
            "typed_by_owner": k2.get("typed_by_owner"),
            "typed_by": k2.get("typed_by")})
    want_phrase = canonical_go_phrase(args["cycle_id"])
    if k2.get("verbatim") != want_phrase:  # byte equality: no trim/case-fold
        S.refusals.append("REFUSED_GO_PHRASE_MISMATCH")
        raise Refusal("REFUSED_GO_PHRASE_MISMATCH", {
            "got": k2.get("verbatim"), "expected": want_phrase,
            "note": "paraphrase/alias dies unconsumed (byte-exact law)"})

    # ---- 4. authority file -------------------------------------------------
    auth_path = args["authority_file"]
    if not Path(auth_path).is_file():
        S.refusals.append("REFUSED_NO_AUTHORITY")
        raise Refusal("REFUSED_NO_AUTHORITY", {"path": auth_path})
    auth, err = load_json(auth_path)
    if err or auth.get("cycle_id") != args["cycle_id"] or \
            auth.get("typed_by_owner") is not True:
        S.refusals.append("REFUSED_AUTHORITY_INVALID")
        raise Refusal("REFUSED_AUTHORITY_INVALID",
                      {"path": auth_path, "error": err,
                       "cycle_id": None if auth is None
                       else auth.get("cycle_id")})

    # ---- 5. symbol contracts ------------------------------------------------
    try:
        contracts_doc = load_symbol_contracts(args["symbol_contracts"])
    except ContractError as exc:
        S.refusals.append("REFUSED_CONTRACTS_INVALID")
        raise Refusal("REFUSED_CONTRACTS_INVALID",
                      {"path": args["symbol_contracts"],
                       "error": str(exc)})

    # ---- 6. input manifest + drift + prior artifacts ------------------------
    manifest, err = load_json(args["input_manifest"])
    if err or manifest.get("schema") != \
            "futures_5sym_prescored/input_manifest@1":
        S.refusals.append("REFUSED_INPUT_MANIFEST_INVALID")
        raise Refusal("REFUSED_INPUT_MANIFEST_INVALID",
                      {"path": args["input_manifest"], "error": err})
    if manifest.get("cycle_id") != args["cycle_id"]:
        S.refusals.append("REFUSED_INPUT_MANIFEST_INVALID")
        raise Refusal("REFUSED_INPUT_MANIFEST_INVALID",
                      {"error": "manifest cycle_id mismatch"})
    mdir = os.path.dirname(os.path.abspath(args["input_manifest"]))

    for pa in manifest.get("prior_artifacts") or []:
        p = resolve_under(mdir, pa["path"])
        if not Path(p).is_file():
            S.refusals.append("REFUSED_MISSING_PRIOR_ARTIFACT")
            raise Refusal("REFUSED_MISSING_PRIOR_ARTIFACT",
                          {"name": pa.get("name"), "path": p})
        if pa.get("sha256") and sha256_file(p) != pa["sha256"]:
            S.refusals.append("REFUSED_INPUT_DRIFT")
            raise Refusal("REFUSED_INPUT_DRIFT",
                          {"artifact": p, "pin": "prior_artifact",
                           "name": pa.get("name")})

    # manifest sha pins on the frozen SPEC / cost / contracts inputs
    for pin_key, pin_path in (
            ("spec_packet_sha256", args["spec_packet"]),
            ("cost_manifest_sha256", args["cost_manifest"]),
            ("symbol_contracts_sha256", args["symbol_contracts"])):
        want = manifest.get(pin_key)
        if want is not None and sha256_file(pin_path) != want:
            S.refusals.append("REFUSED_INPUT_DRIFT")
            raise Refusal("REFUSED_INPUT_DRIFT",
                          {"pin": pin_key, "artifact": pin_path,
                           "expected_sha256": want,
                           "actual_sha256": sha256_file(pin_path)})

    fixtures = []
    bars_by_symbol, bar_counts = {}, {}
    for fx in manifest["fixtures"]:
        p = resolve_under(mdir, fx["path"])
        got = sha256_file(p)
        if got != fx.get("sha256"):
            S.refusals.append("REFUSED_INPUT_DRIFT")
            raise Refusal("REFUSED_INPUT_DRIFT", {
                "artifact": p, "expected_sha256": fx.get("sha256"),
                "actual_sha256": got})
        try:
            bars = load_fixture_csv(p)
        except FixtureError as exc:
            S.refusals.append("REFUSED_INPUT_DRIFT")
            raise Refusal("REFUSED_INPUT_DRIFT",
                          {"artifact": p, "error": str(exc)})
        if fx.get("bars_expected") is not None and \
                len(bars) != fx["bars_expected"]:
            S.refusals.append("REFUSED_INPUT_DRIFT")
            raise Refusal("REFUSED_INPUT_DRIFT", {
                "artifact": p, "bars_expected": fx["bars_expected"],
                "bars_actual": len(bars)})
        fixtures.append(fx)
        bars_by_symbol[fx["symbol"]] = bars
        bar_counts[fx["symbol"]] = len(bars)

    spec, err = load_json(args["spec_packet"])
    if err:
        S.refusals.append("REFUSED_SPEC_INVALID")
        raise Refusal("REFUSED_SPEC_INVALID",
                      {"path": args["spec_packet"], "error": err})
    cost, err = load_json(args["cost_manifest"])
    if err:
        S.refusals.append("REFUSED_COST_MANIFEST_INVALID")
        raise Refusal("REFUSED_COST_MANIFEST_INVALID",
                      {"path": args["cost_manifest"], "error": err})
    # schema dispatch: intent_packet@1 = REAL intent-execution seam (wave-4
    # WIRING-FIX); spec_packet@1 = positional accounting-test encoding. Both
    # run through the identical authority/lock/twin/ledger/publication law.
    intent_mode = spec.get("schema") == INTENT_PACKET_SCHEMA
    try:
        if intent_mode:
            validate_intent_spec(spec, contracts_doc, cost, bar_counts,
                                 bars_by_symbol=bars_by_symbol)
        else:
            validate_spec(spec, contracts_doc, cost, bar_counts)
    except SpecError as exc:
        S.refusals.append("REFUSED_SPEC_INVALID")
        raise Refusal("REFUSED_SPEC_INVALID",
                      {"path": args["spec_packet"], "error": str(exc)})

    # ---- 7. stale IN_PROGRESS marker (recovery law, CYCLE-scoped) ----------
    # ANY IN_PROGRESS marker under the runs root blocks ANY new run of this
    # cycle until --resume-with-recovery-check passes integrity checks
    # (every marker parseable + every existing ledger line complete JSON).
    # A successful run cleans ALL cycle markers (the recovery run adopts
    # them). Never appended-to: a ledger failing integrity is never written.
    runs_root = Path(args["run_dir"]).parent
    stale_markers = sorted(runs_root.glob("*/IN_PROGRESS.json"))
    marker_path = Path(args["run_dir"]) / "IN_PROGRESS.json"
    if stale_markers:
        ok, detail = recovery_integrity_check(stale_markers[0],
                                              args["ledger"],
                                              args["cycle_id"],
                                              args["run_label"])
        for m in stale_markers[1:]:
            m_ok, m_err = load_json(m)
            if m_err:
                ok, detail = False, {"marker_error": f"{m}: {m_err}"}
        if not args["resume_with_recovery_check"] or not ok:
            S.refusals.append("REFUSED_STALE_IN_PROGRESS")
            raise Refusal("REFUSED_STALE_IN_PROGRESS", {
                "stale_markers": [str(m) for m in stale_markers],
                "recovery_check_passed": ok,
                "recovery_detail": detail,
                "rule": "a stale IN_PROGRESS marker requires "
                        "--resume-with-recovery-check AND integrity: every "
                        "marker must be parseable and every existing ledger "
                        "line must be complete JSON (no torn write); then "
                        "the run resumes with identity-ID dedupe"})

    # ---- 8. heavy lock pre-check --------------------------------------------
    lock = HeavyLock(os.path.join(gov, "lock_runtime"), args["cycle_id"])
    state = lock.inspect()
    if state["state"] == "HELD":
        S.refusals.append("NOT_RUN_RESOURCE_CONFLICT")
        raise Refusal("NOT_RUN_RESOURCE_CONFLICT", {
            "lock_dir": str(lock.lock_dir),
            "note": "flock held by another process — zero denominator "
                    "consumed"})
    if state["state"] == "DRIFT":
        S.refusals.append("REFUSED_LOCK_DRIFT")
        raise Refusal("REFUSED_LOCK_DRIFT", {
            "lock_dir": str(lock.lock_dir),
            "running_rows": state["rows"],
            "note": "lock file free while RUNNING registry rows exist — "
                    "bookkeeping drift; reclaim is not this runner's job"})

    # ---- 9. compute inputs (read-only parse done above) ----------------------
    ledger = Ledger(args["ledger"])
    provenance = {
        "input_manifest_sha256": sha256_file(args["input_manifest"]),
        "spec_packet_sha256": sha256_file(args["spec_packet"]),
        "cost_manifest_sha256": sha256_file(args["cost_manifest"]),
        "symbol_contracts_sha256": sha256_file(args["symbol_contracts"]),
        "fixture_sha256": {fx["symbol"]: fx["sha256"] for fx in fixtures},
    }

    # ---- 10. guarded execution; release ALWAYS attempted ---------------------
    try:
        lock.acquire()
        S.lock_acquired = True
        S.mandatory["lock_acquire"] = True

        lock.post_acquire_recheck(faults)
        S.mandatory["post_acquire_recheck"] = True

        atomic_write_json(marker_path, {
            "cycle_id": args["cycle_id"], "run_label": args["run_label"],
            "pid": os.getpid(), "engine_version": ENGINE_VERSION})

        # compute (pass 1) — same engine family for both schemas; the twin
        # (pass 2, faults never injected) runs the SAME compute function.
        compute_fn = compute_intents if intent_mode else compute_all
        computed = compute_fn(spec, bars_by_symbol, contracts_doc, cost,
                              faults)
        S.computation_complete = True
        S.mandatory["compute"] = True

        # reproduction twin (pass 2, same inputs, fresh pass)
        twin = compute_fn(spec, bars_by_symbol, contracts_doc, cost,
                          set())  # faults never injected in the twin
        if "force_twin_drift" in faults and twin["identities"]:
            first = sorted(twin["identities"])[0]
            twin["identities"][first]["totals"]["net_pnl_usd"] = \
                _r6(twin["identities"][first]["totals"]["net_pnl_usd"]
                    + 0.01)
        diffs = structural_diff(computed, twin)
        recon = {
            "schema": "futures_5sym_prescored/reconciliation_report@1",
            "match": not diffs, "diff_count": len(diffs),
            "diffs_sample": diffs[:20],
            "identity_count": len(computed["identities"]),
            "fold_count": len(computed["folds"]),
            "engine_version": ENGINE_VERSION}
        atomic_write_json(Path(args["run_dir"]) /
                          "reconciliation_report.json", recon)
        if diffs:
            raise AbortRun("FAILED_TWIN_MISMATCH", "twin_verify",
                           {"diff_count": len(diffs),
                            "report": "reconciliation_report.json"})
        S.mandatory["twin_verify"] = True

        # ledger append (identity-ID idempotency)
        append_res = ledger.append_trials(spec, computed, provenance, faults)
        S.observed_count = append_res["observed_identity_count"]
        S.mandatory["ledger_append"] = True

        # publication (observed denominator already counted; failure keeps
        # it and quarantines)
        try:
            inject(faults, "fail_publication", "publication")
            pub = {
                "schema": "futures_5sym_prescored/published_summary@1",
                "cycle_id": args["cycle_id"],
                "run_label": args["run_label"],
                "observed_identity_count": S.observed_count,
                "published_identity_count": S.observed_count,
                "published_identity_ids": sorted(append_res["added"]),
                "duplicate_retry_ids": sorted(append_res["retried"]),
                "fold_records": computed["folds"],
                "sandbox_stamp": SANDBOX_STAMP}
            atomic_write_json(Path(args["run_dir"]) /
                              "published_summary.json", pub)
            S.published_count = S.observed_count
            ledger._append({"schema": LEDGER_SCHEMA,
                            "row_type": "PUBLICATION",
                            "counts_observed": False, "identity_id": None,
                            "payload": {"published_identity_count":
                                        S.published_count}})
        except SandboxTestFault:
            Path(args["run_dir"]).mkdir(parents=True, exist_ok=True)
            atomic_write_json(Path(args["run_dir"]) /
                              "PUBLICATION_QUARANTINE.json", {
                "schema":
                "futures_5sym_prescored/publication_quarantine@1",
                "reason": "FAILED_PUBLICATION",
                "observed_identity_count": S.observed_count,
                "note": "observed rows stand in the ledger; published "
                        "summary withheld"})
            raise
        S.mandatory["publication"] = True

        # ledger summary (BUG2-class sibling path)
        inject(faults, "fail_ledger_summary", "ledger_summary")
        atomic_write_json(Path(args["run_dir"]) / "ledger_summary.json",
                          ledger.summary())
        S.mandatory["ledger_summary"] = True

        # IN_PROGRESS marker cleanup BEFORE the terminal handoff: a failed
        # cleanup keeps the marker (next run demands recovery) and denies
        # EXECUTION_COMPLETE — markers never outlive a success. CYCLE-scoped:
        # the recovery run adopts every marker under the runs root.
        for m in runs_root.glob("*/IN_PROGRESS.json"):
            m.unlink()

    except SandboxTestFault as exc:
        S.fail(f"FAILED_{exc.step.upper()}", exc.step, str(exc))
        _abort_ledger_row(ledger, S)
    except AbortRun as exc:
        S.fail(exc.code, exc.step, exc.detail)
        _abort_ledger_row(ledger, S, code=exc.code, detail=exc.detail)
    except Exception as exc:  # noqa: BLE001 — fail closed, never silent
        S.fail("FAILED_UNCAUGHT", "execution",
               f"{type(exc).__name__}: {exc}")
        _abort_ledger_row(ledger, S)
    finally:
        # BUG1-class fix: release ALWAYS attempted, even on exception; a
        # release that raises is a finalization failure — the terminal
        # status is computed AFTER this block from measured evidence.
        if lock.acquired:
            try:
                inject(faults, "fail_release", "lock_release")
                lock.release()
                S.lock_released_status = "RELEASED"
            except SandboxTestFault as exc:
                S.lock_released_status = "RELEASE_RAISED"
                S.finfail(f"lock release fault-injected: {exc}")
                S.fail("FAILED_LOCK_RELEASE", "lock_release",
                       "injected release failure (BUG1-class proof)")
            except Exception as exc:  # noqa: BLE001
                S.lock_released_status = "RELEASE_RAISED"
                S.finfail(f"lock release raised: {exc!r}")
                S.fail("FAILED_LOCK_RELEASE", "lock_release", repr(exc))
            finally:
                lock.close_fd()
        else:
            lock.close_fd()
        S.mandatory["lock_release"] = S.lock_released_status == "RELEASED"

    # ---- 11. terminal handoff — written ONLY after release measured OK ------
    # BUG2-class fix: a handoff write failure can never leave a success.
    if S.core_complete():
        try:
            inject(faults, "fail_handoff_write", "handoff_write")
            handoff = {
                "schema": "futures_5sym_prescored/terminal_handoff@1",
                "cycle_id": args["cycle_id"],
                "run_label": args["run_label"],
                "status": "EXECUTION_COMPLETE",
                "computation_complete": True,
                "mandatory_steps": dict(S.mandatory),
                "observed_identity_count": S.observed_count,
                "published_identity_count": S.published_count,
                "twin": {"match": True},
                "lock": {"acquired": True,
                         "released_status": S.lock_released_status},
                "artifacts": {
                    "ledger": {"path": args["ledger"],
                               "sha256": sha256_file(args["ledger"])},
                    "published_summary": {
                        "path": str(Path(args["run_dir"]) /
                                    "published_summary.json"),
                        "sha256": sha256_file(
                            Path(args["run_dir"]) /
                            "published_summary.json")},
                    "ledger_summary": {
                        "path": str(Path(args["run_dir"]) /
                                    "ledger_summary.json"),
                        "sha256": sha256_file(
                            Path(args["run_dir"]) / "ledger_summary.json")},
                    "reconciliation_report": {
                        "path": str(Path(args["run_dir"]) /
                                    "reconciliation_report.json"),
                        "sha256": sha256_file(
                            Path(args["run_dir"]) /
                            "reconciliation_report.json")}},
                "command_argv": args["_argv"],
                "engine_version": ENGINE_VERSION,
                "sandbox_stamp": SANDBOX_STAMP}
            atomic_write_json(Path(args["run_dir"]) / "handoff.json",
                              handoff)
            S.handoff = handoff
            S.mandatory["handoff_write"] = True
        except SandboxTestFault as exc:
            S.fail("FAILED_HANDOFF_WRITE", "handoff_write", str(exc))
            S.finfail("terminal handoff write fault-injected")
        except Exception as exc:  # noqa: BLE001
            S.fail("FAILED_HANDOFF_WRITE", "handoff_write", repr(exc))
            S.finfail(f"terminal handoff write raised: {exc!r}")

    return terminal_exit(args, S)


def _abort_ledger_row(ledger: Ledger, S: RunState, code=None,
                      detail=None) -> None:
    try:
        ledger.record_abort(code or (S.failure_code or "FAILED"), detail or
                            {"step": S.failed_step})
    except Exception:  # noqa: BLE001 — evidence best-effort, never masks
        pass


def terminal_exit(args, S: RunState) -> int:
    """Compute the terminal status AFTER release, write FINAL_STATUS.json
    (guarded; a final-status write failure forces non-zero — BUG2 class),
    print the one-line verdict. Returns the exit code. final_status_write
    is excluded from the success precondition at compute time (it cannot
    have happened yet); its own failure path forces FAILED/non-zero below."""
    status, rc = S.terminal_state(ignore_missing=("final_status_write",))
    final = {
        "schema": "futures_5sym_prescored/final_status@1",
        "cycle_id": args["cycle_id"], "run_label": args["run_label"],
        "status": status, "exit_code": rc,
        "failed_step": S.failed_step,
        "failure_code": S.failure_code,
        "refusal_code": S.refusals[-1] if S.refusals else None,
        "refusals": list(S.refusals),
        "computation_complete": S.computation_complete,
        "mandatory_steps": dict(S.mandatory),
        "finalization_failures": list(S.finalization_failures),
        "lock": {"acquired": S.lock_acquired,
                 "released_status": S.lock_released_status,
                 "lock_dir": (str(Path(args["governance_dir"]) /
                                  "lock_runtime")
                              if args.get("governance_dir") else None)},
        "observed_identity_count": S.observed_count,
        "published_identity_count": S.published_count,
        "failures": [{"code": f["code"], "step": f["step"],
                      "detail": str(f["detail"])[:400]}
                     for f in S.failures],
        "handoff_written": S.handoff is not None,
        "engine_version": ENGINE_VERSION,
        "sandbox_stamp": SANDBOX_STAMP,
        "determinism_note": "no wall-clock fields",
    }
    # isolation guard: when final_status_out ITSELF resolves into the real
    # governance dir, writing FINAL_STATUS there would violate the very law
    # being enforced — the refusal stands; the evidence falls back to the
    # sandbox run dir.
    if under(REAL_GOVERNANCE_DIR, args["final_status_out"]):
        print("REFUSED_REAL_GOVERNANCE_DIR: final_status_out resolves under "
              "the real governance dir; no FINAL_STATUS written there "
              "(writing it would violate the isolation law)", file=sys.stderr)
        try:
            atomic_write_json(
                Path(args["run_dir"] or ".") /
                "FINAL_STATUS.emergency.json", final)
        except Exception:  # noqa: BLE001
            pass
        return EXIT_REFUSED
    try:
        atomic_write_json(args["final_status_out"], final)
        S.mandatory["final_status_write"] = True
        final["mandatory_steps"] = dict(S.mandatory)
        atomic_write_json(args["final_status_out"], final)  # evidence refresh
    except Exception as exc:  # noqa: BLE001 — BUG2-class: never exit 0
        final["status"] = "FAILED"
        final["exit_code"] = EXIT_FAILED
        final["failed_step"] = S.failed_step or "final_status_write"
        final["failure_code"] = S.failure_code or "FAILED_FINAL_STATUS_WRITE"
        final["finalization_failures"] = (
            list(S.finalization_failures) +
            [f"FINAL_STATUS write failed: {exc!r}"])
        final["final_status_write_failed"] = True
        rc = EXIT_FAILED
        try:
            fallback = Path(args["run_dir"] or ".") / \
                "FINAL_STATUS.emergency.json"
            fallback.write_text(
                json.dumps(final, indent=1, sort_keys=True) + "\n",
                encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    print(f"RUNNER_V2 terminal_status={final['status']} "
          f"exit={final['exit_code']} "
          f"refusal={final['refusal_code'] or '-'} "
          f"failed_step={final['failed_step'] or '-'}")
    return final["exit_code"]


def ledger_integrity_errors(path: str) -> list[str]:
    """Line-by-line completeness check; NEVER raises on torn lines."""
    errs = []
    p = Path(path)
    if not p.is_file():
        return errs
    with open(p, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                errs.append(f"line {i}: {exc}")
    return errs


def recovery_integrity_check(marker_path: Path, ledger_path: str,
                             cycle_id: str, run_label: str) -> tuple:
    marker, err = load_json(marker_path)
    if err:
        return False, {"marker_error": err}
    if marker.get("cycle_id") != cycle_id:
        return False, {"marker_error": "cycle_id mismatch"}
    errs = ledger_integrity_errors(ledger_path)
    if errs:
        return False, {"ledger_torn_lines": errs[:5]}
    return True, {"note": "marker parseable + ledger lines all complete "
                          "JSON; resume with identity-ID dedupe"}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ns = build_arg_parser().parse_args(argv)
    args = {"cycle_id": ns.cycle_id or CYCLE_ID_DEFAULT,
            "governance_dir": ns.governance_dir,
            "go_artifact": ns.go_artifact,
            "authority_file": ns.authority_file,
            "input_manifest": ns.input_manifest,
            "spec_packet": ns.spec_packet,
            "cost_manifest": ns.cost_manifest,
            "symbol_contracts": ns.symbol_contracts or str(
                Path(__file__).resolve().parent / "symbol_contracts.json"),
            "ledger": ns.ledger,
            "run_dir": ns.run_dir,
            "final_status_out": ns.final_status_out,
            "run_label": ns.run_label or "run1",
            "allow_real_governance": ns.allow_real_governance,
            "resume_with_recovery_check": ns.resume_with_recovery_check,
            "registry_json": (os.path.join(ns.governance_dir,
                                           "CYCLE_REGISTRY.json")
                              if ns.governance_dir else None),
            "worktree": os.environ.get("RUNNER_V2_WORKTREE"),
            "faults": set(),
            "_argv": argv}
    if ns.test_fault:
        names = [x.strip() for x in ns.test_fault.split(",") if x.strip()]
        unknown = [x for x in names if x not in KNOWN_FAULTS]
        if unknown:
            print(f"REFUSED_BAD_ARGS: unknown --test-fault {unknown}",
                  file=sys.stderr)
            return EXIT_REFUSED
        args["faults"] = set(names)
        if ns.allow_real_governance:
            print("REFUSED_BAD_ARGS: --test-fault never combines with "
                  "--allow-real-governance", file=sys.stderr)
            return EXIT_REFUSED

    S = RunState(args["cycle_id"], args["run_label"])

    required = ("governance_dir", "go_artifact", "authority_file",
                "input_manifest", "spec_packet", "cost_manifest",
                "ledger", "run_dir", "final_status_out")
    missing = [k for k in required if not args[k]]
    if missing:
        print(f"REFUSED_BAD_ARGS: missing required args {missing}",
              file=sys.stderr)
        # FINAL_STATUS cannot be placed without final_status_out; if the
        # caller gave one, still record the refusal there.
        if args["final_status_out"]:
            S.refusals.append("REFUSED_BAD_ARGS")
            try:
                terminal_exit(args, S)
            except Exception:  # noqa: BLE001
                pass
        return EXIT_REFUSED

    try:
        return guarded_main(args, S)
    except Refusal as exc:
        S.refusals.append(exc.code) if exc.code not in S.refusals else None
        S.mandatory["preflight"] = True
        rc = terminal_exit(args, S)
        # refusal evidence: REFUSED ledger row + refusal_record.json.
        # ISOLATION LAW: the refusal_record path derives from the
        # final_status parent — when that resolves into the real governance
        # dir the record falls back to the (validated-safe) run dir instead;
        # the real dir is NEVER written. The two evidence writes are
        # independent: a ledger that fails integrity (torn lines) never
        # blocks the refusal_record, and vice versa.
        rr_parent = Path(args["final_status_out"]).parent
        if under(REAL_GOVERNANCE_DIR, str(rr_parent)):
            rr_parent = Path(args["run_dir"])
        ledger_error = None
        try:
            ledger = Ledger(args["ledger"])
            ledger.record_refusal(exc.code, json.dumps(
                exc.detail, sort_keys=True, ensure_ascii=False)[:2000])
        except Exception as ledger_exc:  # noqa: BLE001
            ledger_error = ledger_exc
            print(f"TECHNICAL: refusal ledger recording failed: "
                  f"{ledger_exc!r}", file=sys.stderr)
        try:
            atomic_write_json(
                rr_parent / "refusal_record.json",
                {"schema": "futures_5sym_prescored/refusal_record@1",
                 "cycle_id": args["cycle_id"], "reason": exc.code,
                 "detail": exc.detail, "sandbox_stamp": SANDBOX_STAMP,
                 "ledger_error": None if ledger_error is None
                 else repr(ledger_error)[:300]})
        except Exception as rr_exc:  # noqa: BLE001
            print(f"TECHNICAL: refusal_record write failed: {rr_exc!r}",
                  file=sys.stderr)
        print(f"REFUSED: {exc.code} — "
              f"{json.dumps(exc.detail, ensure_ascii=False)[:800]}",
              file=sys.stderr)
        return rc
    except SandboxTestFault as exc:
        S.fail(f"FAILED_{exc.step.upper()}", exc.step, str(exc))
        return terminal_exit(args, S)
    except Exception as exc:  # noqa: BLE001
        S.fail("FAILED_UNCAUGHT", "runner", f"{type(exc).__name__}: {exc}")
        return terminal_exit(args, S)


if __name__ == "__main__":
    raise SystemExit(main())
