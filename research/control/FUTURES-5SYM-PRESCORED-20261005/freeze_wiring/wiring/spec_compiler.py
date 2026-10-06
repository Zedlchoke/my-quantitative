"""spec_compiler.py — POSITIONAL ACCOUNTING-TEST COMPILER (encoding:
"POSITIONAL_ACCOUNTING_TEST_ONLY") for adapter order-intent records ->
UNMODIFIED exec/scored_runner_v2.py frozen inputs.

SCOPE LAW (wave-4 WIRING-FIX): this module is the ACCOUNTING-TEST encoding
ONLY. It lays each identity's trades out in one fabricated positional block
[signal, entry, filler, exit] with hold_bars=2 and a synthetic F-COMPILED
fold — the compiled dates are NOT the adapter's strategy timeline and the
encoding is NOT a strategy execution. It must never again silently encode a
multi-intent group: any group with MORE THAN ONE intent, or with mixed
directions, is refused (REFUSED_POSITIONAL_SCOPE, exit 46).

The REAL INTENT-EXECUTION SEAM is wiring/intent_executor.py +
futures_5sym_prescored/intent_packet@1: every wired intent executes as its
own trade (per-intent direction/timestamps/fills preserved, ordering
preserved) through the SAME runner accounting/twin/ledger/publication path.
See freeze_wiring/wiring/INTENT_SEAM_SPEC.md.

RUNNER INVARIANCE LAW (unchanged): this module never modifies exec/ runner
files. Per identity  ->  one runner invocation (one spec packet, one fixture
CSV, one cost manifest, one sandbox governance dir, one shared ledger).

Compilation rules (fail-closed; each refusal = own exit code + status
artifact):
  C0  POSITIONAL SCOPE: >1 intent in a group, or mixed directions, REFUSES
      (REFUSED_POSITIONAL_SCOPE) — the positional encoding cannot represent
      a multi-leg identity (this is the seam defect of wave-3, fixed by
      refusal here and by the intent seam for real execution).
  C1  POSITIONAL ENCODING: the runner carries ONE hold_bars per identity, so
      the compiler lays the single trade out in one uniform block
      [signal, entry, filler, exit] (hold_bars = 2). The adapter's real
      calendar distances are NOT preserved as bars — the compiled trade
      carries the adapter-DECLARED entry/exit prices positionally (exit bar
      OPEN = adapter exit price), and the expected per-trade math is exact on
      prices / direction / era / costs (asserted by tests). Intraday adapter
      trades (entry_date == exit_date) are legal; the intent dates are used
      for the ERA label only.
  C2  entry/exit prices must sit on the symbol contract's ERA tick grid
      (REFUSED_COMPILE_PRICE_OFF_GRID, exit 42).
  C3  a cost manifest calibrated to one 6A era refuses identities whose
      ENTRY date resolves to another era (REFUSED_COMPILE_COST_ERA_MISMATCH,
      exit 41) — the runner itself would silently apply the entry-era tick
      value; the wiring refuses at compile time instead (6A D8 era law
      carrier). refuse_cost_era_mismatch() is the explicit gate callers run
      when the compiled manifest is era-1-calibrated.
  C4  direction +1 -> arm "long-if-bar-up"; direction -1 ->
      "short-if-bar-down". Every non-signal bar is price-NEUTRAL
      (close == open) so the runner's signal predicate fires exactly at the
      adapter-declared trade positions and nowhere else.
  C5  an identity with zero resolvable intents is not compiled
      (REFUSED_COMPILE_NO_TRADES, exit 43) — it stays a wiring gap, never a
      fabricated denominator. (Intent-mode zero-trade anchors are legal —
      they are a different, SPEC-declared object; see intent_executor.py.)
  C6  ERA LABEL law: the compiled entry bar's synthetic date must resolve to
      the SAME era as the intent's entry_date
      (REFUSED_COMPILE_ERA_LABEL_MISMATCH, exit 45) — the runner's entry-era
      lookup must bind the era the adapter declared.

Cost encoding: the runner computes cost_side = fee(tier) +
(spread_ticks(stress) + slip_ticks(stress)) * tick_value_usd(era). Adapters
declare USD ladders (fee_all_in + spread_usd + slip_usd by tier). Because a
compiled run is per-identity and era-calibrated (C3), the compiler encodes:
  fee_by_tier        = fee_all_in for all tiers (tier selection happens by
                       compiling the identity's own slip into slip_ticks)
  slip_ticks(stress) = slip_usd(tier) / tick_value_usd(calibrated era)
  spread_ticks(str.) = spread_usd      / tick_value_usd(calibrated era)
so the runner reproduces the adapter-declared USD cost exactly (asserted by
tests via expected_net_usd).

Determinism: identical intents + identical epoch give byte-identical
compiled fixtures/specs (sorted keys; dates generated from a fixed base by
simple +1-day steps; no wallclock).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

CYCLE_ID = "FUTURES-5SYM-PRESCORED-20261005"
COMPILE_STATUS_SCHEMA = "futures_5sym_prescored/wired_compile_status@1"
GROUP_MANIFEST_SCHEMA = "futures_5sym_prescored/wired_compile_group@1"

EXIT_OK = 0
COMPILE_REFUSALS = {
    "REFUSED_COMPILE_COST_ERA_MISMATCH": 41,
    "REFUSED_COMPILE_PRICE_OFF_GRID": 42,
    "REFUSED_COMPILE_NO_TRADES": 43,
    "REFUSED_COMPILE_INTENT_INVALID": 44,
    "REFUSED_COMPILE_ERA_LABEL_MISMATCH": 45,
    "REFUSED_POSITIONAL_SCOPE": 46,
}
POSITIONAL_ENCODING = "POSITIONAL_ACCOUNTING_TEST_ONLY"

WIRING_DIR = Path(__file__).resolve().parents[1]     # .../freeze_wiring
CYCLE_DIR = WIRING_DIR.parent                        # .../FUTURES-5SYM-...
EXEC_DIR = CYCLE_DIR / "exec"
RUNNER = EXEC_DIR / "scored_runner_v2.py"
CONTRACTS = EXEC_DIR / "symbol_contracts.json"
PREP_WORKTREE = CYCLE_DIR.parents[2]  # .../.worktrees/futures-5sym-prescored/prep
PY = sys.executable


class CompileRefusal(Exception):
    def __init__(self, code: str, detail: dict):
        super().__init__(code)
        self.code, self.detail = code, detail

    @property
    def exit_code(self) -> int:
        return COMPILE_REFUSALS.get(self.code, 2)


def sha256_file(path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def canonical_json(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False)
            + "\n").encode("utf-8")


def load_contracts(path: str | None = None) -> dict:
    p = Path(path or CONTRACTS)
    data = json.loads(p.read_text(encoding="utf-8"))
    return data


def era_for_date(contracts_doc: dict, symbol: str, d: str) -> dict:
    """LAST era row whose effective_from <= d (runner entry-era law)."""
    rows = contracts_doc["contracts"][symbol]["era_table"]
    chosen = rows[0]
    for r in sorted(rows, key=lambda r: r["effective_from"]):
        if r["effective_from"] <= d:
            chosen = r
    return chosen


def on_grid(px: float, tick: float) -> bool:
    return abs(px / tick - round(px / tick)) < 1e-9


def round_to_tick(px: float, tick: float) -> float:
    return round(round(px / tick) * tick, 10)


# ---------------------------------------------------------------- cost law

def compiled_cost_manifest(symbol: str, era: dict, tier: str, stress: float,
                           cost_usd_law: dict) -> dict:
    """Encode the adapter's USD cost ladder into the runner's tick/fee shape
    for ONE (symbol, era, tier) calibration (see module docstring)."""
    tval = float(era["tick_value_usd"])
    fee = float(cost_usd_law["fee_all_in_usd"])
    slip_usd = float(cost_usd_law["slip_usd_by_tier"][tier])
    spread_usd = float(cost_usd_law["spread_usd"])
    return {
        "fee_per_side_usd_by_tier": {"S1": fee, "S2": fee, "S3": fee},
        "spread_ticks_by_stress": {
            "1.0": round(spread_usd / tval, 6),
            "1.5": round(spread_usd * 1.5 / tval, 6),
            "2.0": round(spread_usd * 2.0 / tval, 6)},
        "slip_ticks_by_stress": {
            "1.0": round(slip_usd / tval, 6),
            "1.5": round(slip_usd * 1.5 / tval, 6),
            "2.0": round(slip_usd * 2.0 / tval, 6)},
        "calibrated_era": era["era"],
        "calibrated_symbol": symbol,
        "calibration_note": "USD ladder -> ticks at the calibrated era's "
                            "tick_value_usd; a mismatched entry era refuses "
                            "at compile time (C3)",
    }


def expected_net_usd(intent: dict, era: dict, cost_manifest: dict) -> float:
    """Mirror of the runner's accounting for one compiled trade."""
    tick = float(era["tick_size"])
    tval = float(era["tick_value_usd"])
    entry = round_to_tick(intent["entry_price"], tick)
    exit_ = round_to_tick(intent["exit_price"], tick)
    gross = intent["direction"] * (exit_ - entry) * (tval / tick)
    sk = f"{float(intent['stress']):.1f}"
    fee = float(cost_manifest["fee_per_side_usd_by_tier"][intent["cost_tier"]])
    cost_side = fee + (float(cost_manifest["spread_ticks_by_stress"][sk])
                       + float(cost_manifest["slip_ticks_by_stress"][sk])) * tval
    return round(gross - 2.0 * cost_side, 6)


DEFAULT_COST_USD_LAW = {
    # MODELED / UNDER REVIEW (COST_CONTRACT_NQ.md s.3/§4 shape; adapter
    # nq_common.cost_per_side_usd ladder A); synthetic-only consumption.
    "fee_all_in_usd": 2.25,
    "spread_usd": 16.25,
    "slip_usd_by_tier": {"S1": 5.00, "S2": 10.00, "S3": 15.00},
}


# ---------------------------------------------------------------- compiler

def _write_fixture(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["ts", "open", "high", "low", "close"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ("ts", "open", "high", "low", "close")})


def compile_identity_run(intent: dict, out_dir: str, *,
                         contracts_doc: dict | None = None,
                         cost_usd_law: dict | None = None,
                         epoch: str = "1970-01-01T00:00:00Z",
                         base_date: str = "2021-01-04") -> dict:
    """Compile ONE wired intent into one runnable runner invocation set under
    out_dir: fixture.csv, spec_packet.json, cost_manifest.json,
    input_manifest.json. Returns the compile record (paths + expected math).
    Multi-trade identities: pass intents list to compile_identity_group."""
    return compile_identity_group([intent], out_dir,
                                  contracts_doc=contracts_doc,
                                  cost_usd_law=cost_usd_law, epoch=epoch,
                                  base_date=base_date)


def compile_identity_group(intents: list[dict], out_dir: str, *,
                           contracts_doc: dict | None = None,
                           cost_usd_law: dict | None = None,
                           epoch: str = "1970-01-01T00:00:00Z",
                           base_date: str = "2021-01-04") -> dict:
    """Compile a list of intents (ALL one identity) into a single runner
    invocation set. Layout is positional (C1); era labels enforced (C6).
    POSITIONAL SCOPE (C0): groups with >1 intent or mixed directions REFUSE
    (REFUSED_POSITIONAL_SCOPE) — use wiring/intent_executor.py for real
    multi-intent execution."""
    contracts_doc = contracts_doc or load_contracts()
    cost_usd_law = cost_usd_law or dict(DEFAULT_COST_USD_LAW)
    out = Path(out_dir)
    if not intents:
        raise CompileRefusal("REFUSED_COMPILE_NO_TRADES",
                             {"error": "zero resolvable intents"})
    iid = intents[0]["identity_id"]
    symbols = {i["symbol"] for i in intents}
    if len(symbols) != 1:
        raise CompileRefusal("REFUSED_COMPILE_INTENT_INVALID",
                             {"error": f"mixed symbols in one identity: {symbols}"})
    symbol = symbols.pop()
    iids = {i["identity_id"] for i in intents}
    if len(iids) != 1:
        raise CompileRefusal("REFUSED_COMPILE_INTENT_INVALID",
                             {"error": "group spans multiple identities"})
    # C0 positional scope: this encoding represents exactly ONE trade.
    directions = sorted({int(i["direction"]) for i in intents})
    if len(intents) > 1 or len(directions) > 1:
        raise CompileRefusal("REFUSED_POSITIONAL_SCOPE", {
            "identity_id": iid,
            "n_intents": len(intents),
            "directions": directions,
            "encoding": POSITIONAL_ENCODING,
            "law": "the positional [signal,entry,filler,exit] encoding is "
                   "accounting-test-only and cannot represent a multi-intent "
                   "identity; mixed-direction/extra legs were SILENTLY "
                   "DROPPED before wave-4 (see "
                   "freeze_wiring/repro_mixed_direction/) — refusing now; "
                   "route multi-intent groups through "
                   "wiring/intent_executor.py (intent_packet@1)"})
    for i in intents:
        if i.get("schema") != "futures_5sym_prescored/wired_intent@1":
            raise CompileRefusal("REFUSED_COMPILE_INTENT_INVALID",
                                 {"error": f"bad intent schema {i.get('schema')!r}"})
        if i.get("provenance") != "SYNTHETIC":
            raise CompileRefusal("REFUSED_COMPILE_INTENT_INVALID", {
                "error": "non-SYNTHETIC provenance refused (real-data "
                         "execution NOT_RUN in this round)",
                "identity_id": i["identity_id"]})

    tier = intents[0]["cost_tier"]
    stress = float(intents[0]["stress"])
    # Cost calibration era: single-era groups calibrate to that era; a
    # multi-era group (6A boundary proof) calibrates to the FIRST era row and
    # callers demonstrate refuse_cost_era_mismatch() explicitly (C3).
    entry_eras = {era_for_date(contracts_doc, symbol, i["entry_date"])["era"]
                  for i in intents}
    if len(entry_eras) == 1:
        cal_era_name = next(iter(entry_eras))
        cal_era_date = next(i["entry_date"] for i in intents
                            if era_for_date(contracts_doc, symbol,
                                            i["entry_date"])["era"] == cal_era_name)
    else:
        cal_era_date = sorted(i["entry_date"] for i in intents)[0]
    cm = compiled_cost_manifest(
        symbol, era_for_date(contracts_doc, symbol, cal_era_date), tier,
        stress, cost_usd_law)

    # ---- panel layout: positional blocks [signal, entry, filler, exit],
    # signal = intent.entry_date - 1 day (C6), strictly increasing ts.
    hold = 2
    first_entry = min(date.fromisoformat(i["entry_date"]) for i in intents)
    cursor = min(date.fromisoformat(base_date), first_entry - timedelta(days=1))
    rows, expected = [], []
    for intent in sorted(intents, key=lambda i: i["entry_date"]):
        e_era = era_for_date(contracts_doc, symbol, intent["entry_date"])
        tick = float(e_era["tick_size"])
        if not on_grid(intent["entry_price"], tick) or \
                not on_grid(intent["exit_price"], tick):
            raise CompileRefusal("REFUSED_COMPILE_PRICE_OFF_GRID", {
                "identity_id": intent["identity_id"],
                "era": e_era["era"], "tick": tick,
                "entry_price": intent["entry_price"],
                "exit_price": intent["exit_price"]})
        entry_px = round_to_tick(intent["entry_price"], tick)
        exit_px = round_to_tick(intent["exit_price"], tick)
        sig_d = date.fromisoformat(intent["entry_date"]) - timedelta(days=1)
        if sig_d < cursor:
            sig_d = cursor
        # C6: walk the block forward until the compiled ENTRY date resolves
        # to the intent's declared era (ordering preserved; bounded search).
        entry_d = sig_d + timedelta(days=1)
        want_era = e_era["era"]
        for _ in range(400):
            if era_for_date(contracts_doc, symbol,
                            entry_d.isoformat())["era"] == want_era:
                break
            entry_d += timedelta(days=1)
        else:
            raise CompileRefusal("REFUSED_COMPILE_ERA_LABEL_MISMATCH", {
                "identity_id": intent["identity_id"],
                "intent_entry_date": intent["entry_date"],
                "intent_era": want_era,
                "search_started": sig_d.isoformat(),
                "law": "C6: no entry date in the intended era found after "
                       "the cursor — refusing instead of mislabeling"})
        sig_d = entry_d - timedelta(days=1)
        block_dates = [sig_d, entry_d, entry_d + timedelta(days=1),
                       entry_d + timedelta(days=2)]
        got_era = era_for_date(contracts_doc, symbol,
                               block_dates[1].isoformat())
        if got_era["era"] != want_era:
            raise CompileRefusal("REFUSED_COMPILE_ERA_LABEL_MISMATCH", {
                "identity_id": intent["identity_id"],
                "intent_entry_date": intent["entry_date"],
                "intent_era": want_era,
                "compiled_entry_date": block_dates[1].isoformat(),
                "compiled_era": got_era["era"],
                "law": "C6: the runner's entry-era lookup must bind the era "
                       "the adapter declared"})
        neutral = lambda px: {"open": px, "high": px, "low": px, "close": px}
        sig_open = 100.0
        sig_close = round(sig_open + intent["direction"] * tick, 10)
        rows.append({"ts": block_dates[0].isoformat(), **neutral(sig_open)})
        rows[-1]["close"] = sig_close
        rows[-1]["high"] = max(sig_open, sig_close)
        rows[-1]["low"] = min(sig_open, sig_close)
        rows.append({"ts": block_dates[1].isoformat(), **neutral(entry_px)})
        rows.append({"ts": block_dates[2].isoformat(), **neutral(entry_px)})
        rows.append({"ts": block_dates[3].isoformat(), **neutral(exit_px)})
        cursor = block_dates[3] + timedelta(days=1)
        expected.append({
            "intent_entry_date": intent["entry_date"],
            "compiled_entry_date": block_dates[1].isoformat(),
            "compiled_exit_date": block_dates[3].isoformat(),
            "entry_price": entry_px, "exit_price": exit_px,
            "direction": intent["direction"], "era": e_era["era"],
            "tick_size": tick,
            "tick_value_usd": float(e_era["tick_value_usd"]),
            "expected_net_pnl_usd": expected_net_usd(intent, e_era, cm)})

    out.mkdir(parents=True, exist_ok=True)
    fx_path = out / f"fixture_{_safe(iid)}.csv"
    _write_fixture(fx_path, rows)
    spec = {
        "schema": "futures_5sym_prescored/spec_packet@1",
        "encoding": POSITIONAL_ENCODING,
        "identities": [{
            "identity_id": iid, "symbol": symbol,
            "arm": ("long-if-bar-up" if intents[0]["direction"] == 1
                    else "short-if-bar-down"),
            "hold_bars": hold, "cost_tier": tier, "stress": stress}],
        "folds": [{"fold_id": "F-COMPILED", "start_bar": 0,
                   "end_bar": len(rows)}],
    }
    spec_path = out / f"spec_packet_{_safe(iid)}.json"
    spec_path.write_bytes(canonical_json(spec))
    cost_path = out / f"cost_manifest_{_safe(iid)}.json"
    cost_path.write_bytes(canonical_json(cm))
    n = len(rows)
    manifest = {
        "schema": "futures_5sym_prescored/input_manifest@1",
        "cycle_id": CYCLE_ID,
        "epoch": epoch,
        "fixtures": [{"symbol": symbol, "path": fx_path.name,
                      "sha256": sha256_file(fx_path), "bars_expected": n}],
        "spec_packet_sha256": sha256_file(spec_path),
        "cost_manifest_sha256": sha256_file(cost_path),
        "symbol_contracts_sha256": sha256_file(CONTRACTS),
    }
    manifest_path = out / f"input_manifest_{_safe(iid)}.json"
    manifest_path.write_bytes(canonical_json(manifest))
    return {"identity_id": iid, "symbol": symbol, "hold_bars": hold,
            "encoding": POSITIONAL_ENCODING,
            "out_dir": str(out), "fixture": str(fx_path),
            "spec_packet": str(spec_path), "cost_manifest": str(cost_path),
            "input_manifest": str(manifest_path),
            "n_bars": n, "expected_trades": expected,
            "calibrated_era": cm["calibrated_era"],
            "compiled_by": "freeze_wiring/wiring/spec_compiler.py"}


def _safe(iid: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in iid)


def refuse_cost_era_mismatch(intents: list[dict], contracts_doc: dict,
                             calibrated_era: str) -> None:
    """C3: refuse when any intent's ENTRY era != the compiled manifest's
    calibrated era (6A era-1 cost model vs era-2-calibrated arms)."""
    for i in intents:
        e = era_for_date(contracts_doc, i["symbol"], i["entry_date"])
        if e["era"] != calibrated_era:
            raise CompileRefusal("REFUSED_COMPILE_COST_ERA_MISMATCH", {
                "identity_id": i["identity_id"],
                "entry_date": i["entry_date"], "entry_era": e["era"],
                "calibrated_era": calibrated_era,
                "law": "era-1-calibrated cost model must never price "
                       "era-2-calibrated arms (6A D8 era-aware cost law)"})


# -------------------------------------------------------- runner invocation

def make_sandbox_authority(gov_dir: str, *, cycle_id: str = CYCLE_ID,
                           branch: str | None = None,
                           go_present: bool = True,
                           go_phrase: str | None = None,
                           go_typed_by: str = "OWNER",
                           go_typed_by_owner: bool = True,
                           authority_valid: bool = True,
                           registry_cycle_present: bool = True,
                           registry_branch: str | None = None) -> dict:
    """Sandbox-only governance scaffolding for the unmodified runner.
    Fake authority is legal ONLY inside sandbox temp dirs."""
    g = Path(gov_dir)
    g.mkdir(parents=True, exist_ok=True)
    branch = branch or _current_branch()
    reg_row = {"cycle_id": cycle_id, "branch": branch,
               "lifecycle": "PREP"}
    if not registry_cycle_present:
        reg_row["cycle_id"] = "OTHER-CYCLE-NOT-OURS"
    if registry_branch is not None:
        reg_row["branch"] = registry_branch
    registry = {"schema": "futures_5sym_prescored/sandbox_registry@1",
                "cycles": [reg_row]}
    reg_path = g / "CYCLE_REGISTRY.json"
    reg_path.write_bytes(canonical_json(registry))
    go_path = g / "GO_RECORDED.json"
    if go_present:
        phrase = go_phrase if go_phrase is not None else \
            f"GO {cycle_id} SCORED EXECUTION"
        go = {"schema": "futures_5sym_prescored/go_recorded@1",
              "cycle_id": cycle_id,
              "key_owner_go": {"typed_by": go_typed_by,
                               "typed_by_owner": go_typed_by_owner,
                               "verbatim": phrase}}
        go_path.write_bytes(canonical_json(go))
    auth_dir = g / "authority"
    auth_dir.mkdir(exist_ok=True)
    auth_path = auth_dir / "authority_pack.json"
    if authority_valid:
        auth = {"cycle_id": cycle_id, "typed_by_owner": True}
    else:
        auth = {"cycle_id": cycle_id, "typed_by_owner": False}
    auth_path.write_bytes(canonical_json(auth))
    return {"governance_dir": str(g), "go_artifact": str(go_path),
            "authority_file": str(auth_path),
            "registry_json": str(reg_path)}


def _current_branch() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(PREP_WORKTREE), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=30)
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001 — sandbox scaffolding best-effort
        return "unknown"


def invoke_runner(*, input_manifest: str, spec_packet: str, cost_manifest: str,
                  gov: dict, ledger: str, run_dir: str, final_status_out: str,
                  run_label: str = "wired1", test_fault: str | None = None,
                  extra_args: list[str] | None = None,
                  python: str | None = None) -> dict:
    """Drive the UNMODIFIED exec/scored_runner_v2.py CLI on compiled inputs.
    Returns {exit_code, stdout, stderr, final_status (parsed or None)}."""
    argv = [python or PY, str(RUNNER),
            "--cycle-id", CYCLE_ID,
            "--governance-dir", gov["governance_dir"],
            "--go-artifact", gov["go_artifact"],
            "--authority-file", gov["authority_file"],
            "--input-manifest", input_manifest,
            "--spec-packet", spec_packet,
            "--cost-manifest", cost_manifest,
            "--symbol-contracts", str(CONTRACTS),
            "--ledger", ledger,
            "--run-dir", run_dir,
            "--final-status-out", final_status_out,
            "--run-label", run_label]
    if test_fault:
        argv += ["--test-fault", test_fault]
    if extra_args:
        argv += extra_args
    env = dict(os.environ)
    env["RUNNER_V2_WORKTREE"] = str(PREP_WORKTREE)
    proc = subprocess.run(argv, capture_output=True, text=True, env=env,
                          timeout=120)
    fs = None
    if Path(final_status_out).is_file():
        try:
            fs = json.loads(Path(final_status_out).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fs = None
    return {"exit_code": proc.returncode, "stdout": proc.stdout,
            "stderr": proc.stderr, "final_status": fs}


def read_ledger(path: str) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def trial_rows(path: str) -> list[dict]:
    return [r for r in read_ledger(path) if r.get("row_type") == "TRIAL"]


def compile_and_run(intents: list[dict], work_dir: str, *, run_label: str,
                    contracts_doc: dict | None = None,
                    cost_usd_law: dict | None = None,
                    test_fault: str | None = None,
                    gov_kwargs: dict | None = None,
                    epoch: str = "2026-10-05T00:00:00Z",
                    python: str | None = None) -> dict:
    """Full seam (POSITIONAL, accounting-test only): compile one identity
    group -> sandbox authority -> run the unmodified runner -> collect ledger
    rows. Single-intent groups only (C0: REFUSED_POSITIONAL_SCOPE otherwise);
    real multi-intent execution is wiring/intent_executor.intent_and_run.
    A future registered cycle calls intent_and_run per identity, with the
    canonical lock around it (see CANONICAL_INTEGRATION.md)."""
    comp = compile_identity_group(intents, work_dir,
                                  contracts_doc=contracts_doc,
                                  cost_usd_law=cost_usd_law, epoch=epoch)
    work = Path(work_dir)
    gov = make_sandbox_authority(str(work / "gov"), **(gov_kwargs or {}))
    res = invoke_runner(
        input_manifest=comp["input_manifest"], spec_packet=comp["spec_packet"],
        cost_manifest=comp["cost_manifest"], gov=gov,
        ledger=str(work / "trial_ledger.jsonl"),
        run_dir=str(work / "runs" / run_label),
        final_status_out=str(work / f"FINAL_STATUS.{run_label}.json"),
        run_label=run_label, test_fault=test_fault, python=python)
    res["compile"] = comp
    res["ledger_rows"] = read_ledger(str(work / "trial_ledger.jsonl"))
    res["trials"] = trial_rows(str(work / "trial_ledger.jsonl"))
    return res
