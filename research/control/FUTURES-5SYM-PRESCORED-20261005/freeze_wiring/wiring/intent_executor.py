"""intent_executor.py — the REAL INTENT-EXECUTION SEAM for the wiring
(futures_5sym_prescored/intent_packet@1; wave-4 WIRING-FIX).

DEFECT THIS REPLACES (see freeze_wiring/repro_mixed_direction/ and
synth/ERRATUM_2_WIRING_CLAIMS.md): the positional compiler picked the runner
arm from intents[0]["direction"] and the positional runner path made ONE
trade per identity, silently dropping same-identity mixed-direction/extra
legs; the [signal, entry, filler, exit] / hold_bars=2 / F-COMPILED encoding
was accounting-test-only, not a strategy timeline.

THIS seam is the production intent-execution path. Execution law — every
rule flows from the intent records + the frozen SPEC packet into the
UNMODIFIED-runner intent-mode engine (same accounting/twin/ledger/
publication/authority path as the positional encoding):

  E1  ONE TRADE PER INTENT: every wired intent executes as its own trade.
      Per-intent direction (Long AND Short inside one identity both
      execute), per-intent signal/decision/entry/exit timestamps preserved
      verbatim in the journal and in the ledger TRIAL payload, submission
      ordering preserved. Identity ids and the identity table stay EXACTLY
      as declared — Long/Short are NEVER split into new identities.
  E2  SPEC LAW CARRIERS: folds come from the packet's own folds (never
      F-COMPILED); warmup_bars and calendar_excluded_dates are packet law;
      tick era comes from the ENTRY date via the frozen symbol contracts
      (6A $10/$5 at the 2020-11-23 era row); quote direction is the
      contract's long_base_sign=+1 law (6J USD-per-JPY); costs are the
      frozen cost manifest (per-side fee + (spread+slip ticks) * tick
      value at stress tiers); SL-priority same-bar and session-close exits
      are per-intent declared exit_reason values the engine validates
      against the identity's holding_horizon_bars.
  E3  ZERO-TRADE IDENTITIES: an identity declared with zero intents is a
      spec-valid processed anchor (TRIAL row, executed count 0, observed
      denominator counts it — semantics unchanged).
  E4  AUTHORITY GATES: non-SYNTHETIC provenance refuses at the wiring layer
      (REFUSED_COMPILE_INTENT_INVALID) and again in the runner
      (REFUSED_SPEC_INVALID); every real-data slot still refuses; the
      runner's GO/registry/authority/input-drift/lock/twin/publication/
      finalization gates apply unchanged (the seam adds no bypass).
  E5  ACCOUNTING REUSE: the builder writes NO accounting arithmetic of its
      own — fill rounding, era law, gross/cost/net and money rounding are
      the runner's compute_intents, sharing compute_all's formulas; the
      cost manifest is encoded by spec_compiler.compiled_cost_manifest
      (one USD->ticks implementation) and gated by the same C3
      era-calibration refusal.

Fail-closed builder refusals (CompileRefusal, distinct exit codes):
  REFUSED_COMPILE_INTENT_INVALID      schema/provenance/symbol/timeline law
  REFUSED_COMPILE_PRICE_OFF_GRID      declared fills off the entry-era grid
  REFUSED_COMPILE_COST_ERA_MISMATCH   cost manifest calibrated to a
                                      different era than an intent's entry
  REFUSED_COMPILE_NO_TRADES           zero identities / empty groups
  REFUSED_COMPILE_SPEC_LAW            folds/warmup/session-timeline law
                                      violations (C-law of the packet)

Determinism: identical inputs + identical epoch give byte-identical
packet/fixture/manifest artifacts (canonical_json; no wallclock).
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from . import intent_contract as ic
from . import spec_compiler as sc

INTENT_PACKET_SCHEMA = "futures_5sym_prescored/intent_packet@1"
INTENT_ENCODING = "INTENT_TIMELINE_VERBATIM"


class CompileRefusal(sc.CompileRefusal):
    pass


def _refuse(code: str, detail: dict) -> None:
    raise sc.CompileRefusal(code, detail)


# --------------------------------------------------------------- grouping

def group_intents(intents: list[dict], *,
                  horizons: dict[str, int] | None = None,
                  zero_trade_identities: list[dict] | None = None,
                  cost_tiers: dict[str, str] | None = None,
                  stresses: dict[str, float] | None = None) -> list[dict]:
    """Group a flat wired_intent@1 list by identity (first-appearance order
    preserved) into intent_groups. Optional per-identity metadata:
    horizons/cost_tiers/stresses dicts and explicit zero-trade anchors
    ({"identity_id", "symbol"})."""
    horizons = horizons or {}
    cost_tiers = cost_tiers or {}
    stresses = stresses or {}
    groups: dict[str, dict] = {}
    order: list[str] = []
    for it in intents:
        iid = it["identity_id"]
        if iid not in groups:
            groups[iid] = {"identity_id": iid, "symbol": it["symbol"],
                           "intents": []}
            order.append(iid)
        groups[iid]["intents"].append(it)
    out = []
    for iid in order:
        g = groups[iid]
        g["holding_horizon_bars"] = int(horizons.get(iid, 1))
        g["cost_tier"] = cost_tiers.get(iid)
        g["stress"] = stresses.get(iid)
        out.append(g)
    for z in (zero_trade_identities or []):
        iid = z["identity_id"]
        if iid in groups:
            raise ValueError(f"{iid}: zero-trade anchor duplicates a group "
                             "with intents")
        out.append({"identity_id": iid, "symbol": z["symbol"],
                    "intents": [],
                    "holding_horizon_bars": int(z.get(
                        "holding_horizon_bars", 1)),
                    "cost_tier": cost_tiers.get(iid),
                    "stress": stresses.get(iid)})
    return out


# ----------------------------------------------------------- packet build

def _check_group_law(g: dict, contracts_doc: dict) -> None:
    iid = g["identity_id"]
    intents = g["intents"]
    symbols = {i["symbol"] for i in intents}
    if intents and symbols != {g["symbol"]}:
        _refuse("REFUSED_COMPILE_INTENT_INVALID", {
            "identity_id": iid,
            "error": f"intents span symbols {sorted(symbols)} but the group "
                     f"declares {g['symbol']!r}"})
    for i in intents:
        if i.get("schema") != ic.INTENT_SCHEMA:
            _refuse("REFUSED_COMPILE_INTENT_INVALID", {
                "identity_id": iid,
                "error": f"bad intent schema {i.get('schema')!r}"})
        if i.get("provenance") != "SYNTHETIC":
            _refuse("REFUSED_COMPILE_INTENT_INVALID", {
                "identity_id": iid,
                "error": f"non-SYNTHETIC provenance {i.get('provenance')!r} "
                         "refused (real-data execution NOT_RUN in this "
                         "round; existing law)",
                "source_adapter": i.get("source_adapter")})


def build_intent_run(groups: list[dict], session_bars: list[dict], *,
                     folds: list[dict], work_dir: str,
                     warmup_bars: int = 0,
                     calendar_excluded_dates: list[str] | None = None,
                     contracts_doc: dict | None = None,
                     cost_usd_law: dict | None = None,
                     calibrated_era: str | None = None,
                     epoch: str = "1970-01-01T00:00:00Z") -> dict:
    """Build ONE runnable intent-mode invocation set under work_dir:
    fixture.csv (the execution TIMELINE — session bars, one bar per session
    date; prices unused by the intent engine), intent_packet.json,
    cost_manifest.json, input_manifest.json. Fail-closed; see module
    docstring. Returns the compile record."""
    contracts_doc = contracts_doc or sc.load_contracts()
    cost_usd_law = cost_usd_law or dict(sc.DEFAULT_COST_USD_LAW)
    if not groups:
        _refuse("REFUSED_COMPILE_NO_TRADES",
                {"error": "zero identity groups"})
    if not session_bars:
        _refuse("REFUSED_COMPILE_SPEC_LAW",
                {"error": "empty session timeline"})

    # -- timeline law: ONE bar per session date. Adapter panels may carry
    # two aggregates for the same date (a warmup row + the authoritative
    # event-day override, e.g. adapt_nq warm sessions include the event
    # days); the LAST occurrence per date wins and the raw count is recorded
    # in the compile record (dedupe with evidence, never silent).
    by_date: dict[str, dict] = {}
    for b in session_bars:
        by_date[str(b["session_date"])] = b
    n_sessions_raw = len(session_bars)
    timeline = sorted(by_date)
    date_set = set(timeline)
    excl_set = {str(d) for d in (calendar_excluded_dates or [])}

    # -- per-group law ------------------------------------------------------
    for g in groups:
        _check_group_law(g, contracts_doc)
    symbols = sorted({g["symbol"] for g in groups})
    if len(symbols) != 1:
        _refuse("REFUSED_COMPILE_INTENT_INVALID", {
            "error": f"mixed symbols in one intent run: {symbols} — the "
                     "cost manifest tick table is per-symbol; run one "
                     "packet per symbol"})
    symbol = symbols[0]
    tiers = {g.get("cost_tier") or (g["intents"][0]["cost_tier"]
                                    if g["intents"] else None)
             for g in groups}
    stresses = {float(g.get("stress") or (g["intents"][0]["stress"]
                                          if g["intents"] else 1.0))
                for g in groups}
    if len(tiers) != 1 or None in tiers:
        _refuse("REFUSED_COMPILE_INTENT_INVALID", {
            "error": f"identities must share one cost tier per run, got "
                     f"{sorted(t for t in tiers if t)}"})
    if len(stresses) != 1:
        _refuse("REFUSED_COMPILE_INTENT_INVALID", {
            "error": f"identities must share one stress per run (one cost "
                     f"calibration), got {sorted(stresses)}"})
    tier = tiers.pop()
    stress = stresses.pop()

    # -- intent timeline + era law -----------------------------------------
    packet_intents_by_id: dict[str, list[dict]] = {}
    entry_eras: dict[str, str] = {}
    for g in groups:
        iid = g["identity_id"]
        rows = []
        for seq, i in enumerate(g["intents"]):
            e_d = i["entry_date"]
            x_d = i["exit_date"]
            e_era = sc.era_for_date(contracts_doc, symbol, e_d)
            tick = float(e_era["tick_size"])
            if not sc.on_grid(i["entry_price"], tick) or \
                    not sc.on_grid(i["exit_price"], tick):
                _refuse("REFUSED_COMPILE_PRICE_OFF_GRID", {
                    "identity_id": iid, "era": e_era["era"], "tick": tick,
                    "entry_price": i["entry_price"],
                    "exit_price": i["exit_price"]})
            if calibrated_era is not None and e_era["era"] != calibrated_era:
                _refuse("REFUSED_COMPILE_COST_ERA_MISMATCH", {
                    "identity_id": iid, "entry_date": e_d,
                    "entry_era": e_era["era"],
                    "calibrated_era": calibrated_era,
                    "law": "era-calibrated cost model must never price "
                           "another era's arms (6A D8 era-aware cost law)"})
            entry_eras[e_d] = e_era["era"]
            if e_d not in date_set and e_d not in excl_set:
                _refuse("REFUSED_COMPILE_INTENT_INVALID", {
                    "identity_id": iid, "entry_date": e_d,
                    "error": "entry date is neither a session date nor a "
                             "declared calendar exclusion"})
            if e_d in date_set and x_d not in date_set:
                _refuse("REFUSED_COMPILE_INTENT_INVALID", {
                    "identity_id": iid, "exit_date": x_d,
                    "error": "exit date is not a session date of the "
                             "frozen timeline"})
            sig_ts = i.get("signal_ts")
            if sig_ts is None:
                sig_ts = (date.fromisoformat(e_d)
                          - timedelta(days=1)).isoformat()
            rows.append({
                "intent_seq": seq,
                "direction": int(i["direction"]),
                "signal_ts": str(sig_ts),
                "entry_ts": e_d,
                "exit_ts": x_d,
                "entry_price": float(i["entry_price"]),
                "exit_price": float(i["exit_price"]),
                "exit_reason": i.get("exit_reason") or "horizon",
            })
        packet_intents_by_id[iid] = rows

    # -- cost calibration era: declared, or the earliest entry era ----------
    if calibrated_era is None:
        if entry_eras:
            calibrated_era = entry_eras[min(entry_eras)]
        else:
            calibrated_era = sc.era_for_date(
                contracts_doc, symbol, timeline[0])["era"]
    cal_era_row = sc.era_for_date(
        contracts_doc, symbol,
        next((d for d, e in entry_eras.items() if e == calibrated_era),
             timeline[0]))
    cm = sc.compiled_cost_manifest(symbol, cal_era_row, tier, stress,
                                   cost_usd_law)

    # -- fold law ------------------------------------------------------------
    if not folds:
        _refuse("REFUSED_COMPILE_SPEC_LAW", {"error": "folds must be a "
                                                     "non-empty list"})
    fs = sorted(folds, key=lambda f: f["start_bar"])
    prev_end = None
    for f in fs:
        s, e = f.get("start_bar"), f.get("end_bar")
        if not isinstance(s, int) or not isinstance(e, int) or s < 0 or \
                e <= s:
            _refuse("REFUSED_COMPILE_SPEC_LAW", {
                "fold": f.get("fold_id"), "error": f"bad start/end bars "
                                                   f"({s!r}, {e!r})"})
        if prev_end is not None and s < prev_end:
            _refuse("REFUSED_COMPILE_SPEC_LAW", {
                "fold": f.get("fold_id"),
                "error": "overlapping folds — a trade at the seam must land "
                         "in exactly one fold"})
        prev_end = e
        if e > len(timeline):
            _refuse("REFUSED_COMPILE_SPEC_LAW", {
                "fold": f.get("fold_id"), "end_bar": e,
                "error": f"exceeds the session timeline ({len(timeline)})"})
    if fs[0]["start_bar"] < int(warmup_bars):
        _refuse("REFUSED_COMPILE_SPEC_LAW", {
            "error": f"first fold starts at {fs[0]['start_bar']} before "
                     f"warmup_bars {warmup_bars} — the warmup region must "
                     "be fold-free"})

    # -- artifacts ------------------------------------------------------------
    out = Path(work_dir)
    out.mkdir(parents=True, exist_ok=True)
    fx_path = out / f"timeline_{sc._safe(symbol)}.csv"
    sc._write_fixture(fx_path, [
        {"ts": d, "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0}
        for d in timeline])
    identities = []
    for g in groups:
        g_tier = g.get("cost_tier") or tier
        g_stress = float(g.get("stress") if g.get("stress") is not None
                         else stress)
        identities.append({
            "identity_id": g["identity_id"], "symbol": g["symbol"],
            "cost_tier": g_tier, "stress": g_stress,
            "holding_horizon_bars": int(g.get("holding_horizon_bars", 1)),
            "intents": packet_intents_by_id[g["identity_id"]],
        })
    packet = {
        "schema": INTENT_PACKET_SCHEMA,
        "encoding": INTENT_ENCODING,
        "provenance": "SYNTHETIC",
        "warmup_bars": int(warmup_bars),
        "calendar_excluded_dates": sorted(excl_set),
        "identities": identities,
        "folds": [{"fold_id": f["fold_id"], "start_bar": f["start_bar"],
                   "end_bar": f["end_bar"]} for f in fs],
    }
    packet_path = out / "intent_packet.json"
    packet_path.write_bytes(sc.canonical_json(packet))
    cost_path = out / "cost_manifest.json"
    cost_path.write_bytes(sc.canonical_json(cm))
    n = len(timeline)
    manifest = {
        "schema": "futures_5sym_prescored/input_manifest@1",
        "cycle_id": sc.CYCLE_ID,
        "epoch": epoch,
        "fixtures": [{"symbol": symbol, "path": fx_path.name,
                      "sha256": sc.sha256_file(fx_path),
                      "bars_expected": n}],
        "spec_packet_sha256": sc.sha256_file(packet_path),
        "cost_manifest_sha256": sc.sha256_file(cost_path),
        "symbol_contracts_sha256": sc.sha256_file(sc.CONTRACTS),
    }
    manifest_path = out / "input_manifest.json"
    manifest_path.write_bytes(sc.canonical_json(manifest))
    return {
        "schema": INTENT_PACKET_SCHEMA, "encoding": INTENT_ENCODING,
        "identity_ids": [g["identity_id"] for g in groups],
        "symbol": symbol, "calibrated_era": calibrated_era,
        "warmup_bars": int(warmup_bars),
        "n_sessions": n,
        "n_sessions_raw": n_sessions_raw,
        "n_intents": sum(len(v) for v in packet_intents_by_id.values()),
        "out_dir": str(out), "timeline": str(fx_path),
        "intent_packet": str(packet_path), "cost_manifest": str(cost_path),
        "input_manifest": str(manifest_path),
        "built_by": "freeze_wiring/wiring/intent_executor.py",
    }


# ------------------------------------------------------------- run wrapper

def intent_and_run(groups, session_bars, *, folds, work_dir: str,
                   run_label: str, warmup_bars: int = 0,
                   calendar_excluded_dates: list[str] | None = None,
                   contracts_doc: dict | None = None,
                   cost_usd_law: dict | None = None,
                   calibrated_era: str | None = None,
                   epoch: str = "2026-10-05T00:00:00Z",
                   gov_kwargs: dict | None = None,
                   test_fault: str | None = None,
                   python: str | None = None) -> dict:
    """Full intent seam: build the intent_packet@1 run set -> sandbox
    authority -> the SAME UNMODIFIED-runner CLI (intent-mode dispatch inside
    exec/scored_runner_v2.py) -> collect ledger rows + per-identity journal.
    This is the function a future registered cycle calls per identity group,
    with the canonical lock around it (CANONICAL_INTEGRATION.md)."""
    if groups and isinstance(groups, list) and groups and \
            isinstance(groups[0], dict) and "schema" in groups[0]:
        groups = group_intents(groups)   # flat wired_intent list accepted
    comp = build_intent_run(
        groups, session_bars, folds=folds, work_dir=str(Path(work_dir)),
        warmup_bars=warmup_bars,
        calendar_excluded_dates=calendar_excluded_dates,
        contracts_doc=contracts_doc, cost_usd_law=cost_usd_law,
        calibrated_era=calibrated_era, epoch=epoch)
    work = Path(work_dir)
    gov = sc.make_sandbox_authority(str(work / "gov"), **(gov_kwargs or {}))
    res = sc.invoke_runner(
        input_manifest=comp["input_manifest"],
        spec_packet=comp["intent_packet"],
        cost_manifest=comp["cost_manifest"], gov=gov,
        ledger=str(work / "trial_ledger.jsonl"),
        run_dir=str(work / "runs" / run_label),
        final_status_out=str(work / f"FINAL_STATUS.{run_label}.json"),
        run_label=run_label, test_fault=test_fault, python=python)
    res["compile"] = comp
    res["ledger_rows"] = sc.read_ledger(str(work / "trial_ledger.jsonl"))
    res["trials"] = sc.trial_rows(str(work / "trial_ledger.jsonl"))
    res["journal"] = {t["identity_id"]: t["payload"].get("journal", [])
                      for t in res["trials"]}
    res["identity_records"] = {t["identity_id"]: t["payload"]
                               for t in res["trials"]}
    return res


def packet_of(comp: dict) -> dict:
    """Parse the built intent packet (test/audit convenience)."""
    return json.loads(Path(comp["intent_packet"]).read_text(
        encoding="utf-8"))
