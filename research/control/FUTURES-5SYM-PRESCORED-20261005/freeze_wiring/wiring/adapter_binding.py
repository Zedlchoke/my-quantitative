"""adapter_binding.py — adapter discovery + lane binding for the wiring seam.

The family-adapter lanes (adapt_nq/, adapt_fx_eb/, adapt_fx_ja/) are written
by PARALLEL lanes. This module is the wiring-side registry:

  WIRED_FAMILIES   every family adapter that EXISTS at wiring time and is
                   bound (module import + interface shim proven by the test
                   suite). Each entry carries the lane that owns it.
  PENDING_WIRING   family slots whose adapter has NOT landed (lane named);
                   they compile NOTHING and never fabricate a denominator.

The runner proof path per family:
  adapter.order_intent(...) records  --normalize-->  wired_intent@1
    --compile_identity_group-->  frozen spec packet + fixtures manifest
    --invoke unmodified exec/scored_runner_v2.py-->  ledger rows.

6A carries NO family adapter (SPEC_6A_CONTINGENCY is a parked 26-ID packet
gated on pb3_lift@1 + d8/d9): its 6A boundary proofs run through the
spec_compiler with compiler-declared intents; the 6A family slots are
PENDING_WIRING (lane: ADAPT-FXJA / owner contingency).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[2]   # .../FUTURES-5SYM-...
ADAPT_DIR = CYCLE_DIR / "adapt_nq"
ADAPT_FXEB_DIR = CYCLE_DIR / "adapt_fx_eb"
ADAPT_FXJA_DIR = CYCLE_DIR / "adapt_fx_ja"

# ----------------------------------------------------------------- registry

# kind="class"    : adapter module exposes a class with
#                   order_intent(panel, calendar, identity_id, session_date,
#                   asof=None, ...) -> record  (NQ F1-F3, JF1)
# kind="function" : module exposes module-level
#                   build_observables/signal/order_intent (FXEB F1-F3)
WIRED_FAMILIES = [
    {"family": "NQ-F1", "lane": "ADAPT-NQ", "symbols": ["NQ"],
     "lane_dir": ADAPT_DIR, "module": "f1_fomc_era/adapter.py",
     "kind": "class", "cls": "FomcEraAdapter"},
    {"family": "NQ-F2", "lane": "ADAPT-NQ", "symbols": ["NQ"],
     "lane_dir": ADAPT_DIR, "module": "f2_macro_0730/adapter.py",
     "kind": "class", "cls": "Macro0730Adapter"},
    {"family": "NQ-F3", "lane": "ADAPT-NQ", "symbols": ["NQ"],
     "lane_dir": ADAPT_DIR, "module": "f3_run_rev/adapter.py",
     "kind": "class", "cls": "RunRevAdapter"},
    {"family": "NQ-F4", "lane": "ADAPT-NQ", "symbols": ["NQ"],
     "lane_dir": ADAPT_DIR, "module": "f4_rollwk/adapter.py",
     "kind": "class", "cls": "RollWkAdapter"},
    {"family": "FX-F1", "lane": "ADAPT-FXEB", "symbols": ["6E", "6B"],
     "lane_dir": ADAPT_FXEB_DIR, "module": "f1_london_range/adapter.py",
     "kind": "function"},
    {"family": "FX-F2", "lane": "ADAPT-FXEB", "symbols": ["6E", "6B"],
     "lane_dir": ADAPT_FXEB_DIR, "module": "f2_policy_decision/adapter.py",
     "kind": "function"},
    {"family": "FX-F3", "lane": "ADAPT-FXEB", "symbols": ["6E", "6B"],
     "lane_dir": ADAPT_FXEB_DIR, "module": "f3_us0830/adapter.py",
     "kind": "function"},
    {"family": "FX-F4", "lane": "ADAPT-FXEB", "symbols": ["6E", "6B"],
     "lane_dir": ADAPT_FXEB_DIR, "module": "f4_reopen_gap/adapter.py",
     "kind": "function"},
    {"family": "FX-F5", "lane": "ADAPT-FXEB", "symbols": ["6E", "6B"],
     "lane_dir": ADAPT_FXEB_DIR, "module": "f5_cip_overlay/adapter.py",
     "kind": "function"},
    {"family": "FX-F6", "lane": "ADAPT-FXEB", "symbols": ["6E", "6B"],
     "lane_dir": ADAPT_FXEB_DIR, "module": "f6_cot_overlay/adapter.py",
     "kind": "function"},
    {"family": "RMM-FXEB", "lane": "ADAPT-FXEB", "symbols": ["6E", "6B"],
     "lane_dir": ADAPT_FXEB_DIR, "module": "rmm_roll_migration/adapter.py",
     "kind": "function"},
    {"family": "JF1", "lane": "ADAPT-FXJA", "symbols": ["6J"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "jf1_boj_mpm/adapter.py",
     "kind": "class", "cls": "JF1Adapter"},
    {"family": "JF2", "lane": "ADAPT-FXJA", "symbols": ["6J"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "jf2_mof_regime/adapter.py",
     "kind": "class", "cls": "JF2Adapter"},
    {"family": "JF3", "lane": "ADAPT-FXJA", "symbols": ["6J"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "jf3_tokyo_morning/adapter.py",
     "kind": "class", "cls": "JF3Adapter"},
    {"family": "RMM6J", "lane": "ADAPT-FXJA", "symbols": ["6J"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "rmm_6j_leg/adapter.py",
     "kind": "class", "cls": "RMM6JAdapter"},
    {"family": "AF1", "lane": "ADAPT-FXJA", "symbols": ["6A"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "af1_rba/adapter.py",
     "kind": "class", "cls": "AF1Adapter"},
    {"family": "AF3", "lane": "ADAPT-FXJA", "symbols": ["6A"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "af3_bimodal/adapter.py",
     "kind": "class", "cls": "AF3Adapter"},
    {"family": "AF4", "lane": "ADAPT-FXJA", "symbols": ["6A"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "af4_tick_regime/adapter.py",
     "kind": "class", "cls": "AF4Adapter"},
    {"family": "RMM6A", "lane": "ADAPT-FXJA", "symbols": ["6A"],
     "lane_dir": ADAPT_FXJA_DIR, "module": "rmm_6a_leg/adapter.py",
     "kind": "class", "cls": "RMM6AAdapter"},
]

# Nothing is PENDING at the adapter-module level as of the final bind pass:
# every family adapter module present under adapt_nq/, adapt_fx_eb/ and
# adapt_fx_ja/ is registered above and import-proven by the test suite.
PENDING_WIRING = []

# Families whose EXECUTION is authority-gated even though the adapter module
# is wired (fail-closed slots; not wiring gaps):
AUTHORITY_GATED = [
    {"families": ["AF1", "AF3", "AF4", "RMM6A"],
     "gate": "6A activation chain P5-D5: PB3 lift -> ADOPT-D8 ratification "
             "-> ADOPT-D9 cease-guard standard (-> D2 fee A7 -> calendar "
             "ruling); contingency machinery, real-data paths refuse"},
    {"families": ["FX-F1", "FX-F2", "FX-F3", "FX-F4", "FX-F5", "FX-F6",
                  "RMM-FXEB"],
     "gate": "PB2 HOLD P5-OD1 (lift required); FX-F5 additionally carries "
             "RefusedPendingEvidence vintage-quantification; RMM-FXEB Role-B "
             "legality gated on the owner DC s.1.3 ruling"},
    {"families": ["JF1", "JF2", "JF3", "RMM6J"],
     "gate": "owner 6J ceiling P5-D1 (option J-A/J-B/J-C + clock-shadow "
             "reading) unsigned; builder refuses BLOCKED_NO_CEILING"},
    {"families": ["NQ-F1", "NQ-F2", "NQ-F3", "NQ-F4"],
     "gate": "P5-NQ1 (ADOPT-D9) + P5-NQ2 (ceiling) unsigned; synthetic-only "
             "provenance gate binds every adapter entry"},
]


def discovery_snapshot() -> dict:
    """Machine-readable wiring coverage (handoff + report input)."""
    wired = []
    for f in WIRED_FAMILIES:
        p = Path(f["lane_dir"]) / f["module"]
        wired.append({**{k: v for k, v in f.items()
                         if k not in ("lane_dir",)},
                      "module_path": str(p), "exists": p.is_file()})
    return {"wired": wired, "pending_wiring": PENDING_WIRING,
            "authority_gated": AUTHORITY_GATED}


# ----------------------------------------------------------------- loading

def load_family_module(entry: dict):
    """Import a family adapter module from its lane dir. The lane's own
    common module (nq_common / fx_common) is imported FIRST under a
    lane-unique name and temporarily bound as the plain name in sys.modules
    while the adapter executes — two lanes both name their common module
    `fx_common`, and without this scoping the second lane would silently
    bind the first lane's module (cross-lane contamination). The binding is
    restored after exec; the adapter keeps a reference to ITS lane's module."""
    lane_dir = str(entry["lane_dir"])
    if lane_dir not in sys.path:
        sys.path.insert(0, lane_dir)
    common_name = "nq_common" if entry["lane"] == "ADAPT-NQ" else "fx_common"
    unique = f"wired_common_{entry['lane']}"
    if unique not in sys.modules:
        spec_c = importlib.util.spec_from_file_location(
            unique, str(Path(entry["lane_dir"]) / f"{common_name}.py"))
        mod_c = importlib.util.module_from_spec(spec_c)
        sys.modules[unique] = mod_c
        saved = sys.modules.get(common_name)
        sys.modules[common_name] = mod_c   # bind BEFORE adapter exec
        try:
            spec_c.loader.exec_module(mod_c)
        finally:
            if saved is not None:
                sys.modules[common_name] = saved
            else:
                sys.modules.pop(common_name, None)
    lane_common = sys.modules[unique]
    sys.modules[common_name] = lane_common  # bind for the adapter exec below
    try:
        mod_path = Path(entry["lane_dir"]) / entry["module"]
        name = "wired_" + "_".join(
            p.strip("/.") for p in
            (entry["lane"] + "_" + entry["module"]).split("/"))
        spec = importlib.util.spec_from_file_location(name, mod_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load adapter module {mod_path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop(common_name, None)  # restore neutral state
    return mod


# ------------------------------------------------------------------ shims

def collect_class_intents(entry: dict, panel: dict, calendar: dict,
                          asof=None) -> list[dict]:
    """class-adapter shim: drive order_intent over DRAFT_IDS x sessions and
    normalize resolvable trades into wired_intent@1 records."""
    from . import intent_contract as ic
    mod = load_family_module(entry)
    adapter = getattr(mod, entry["cls"])()
    ids = list(mod.DRAFT_IDS)
    symbol = entry["symbols"][0]
    sessions = sorted({b["session_date"] for b in panel["bars"]})
    src = f"{Path(entry['lane_dir']).name}/{entry['module']}"
    out = []
    for iid in ids:
        for sd in sessions:
            rec = adapter.order_intent(panel, calendar, iid, sd, asof=asof)
            if rec.get("no_trade"):
                continue
            if rec.get("exit_ref_price") is None or \
                    (rec.get("ts_exit") or rec.get("exit_ts")) is None:
                continue  # PENDING_UPTO_ASOF: not a declared completed trade
            out.append(ic.intent_from_class_adapter(
                rec, source_adapter=src, default_symbol=symbol))
    return out


def collect_fxeb_intents(entry: dict, panel: dict, calendar: dict,
                         sym: str) -> list[dict]:
    """function-adapter shim (adapt_fx_eb): build_observables -> signal ->
    order_intent per session per declared identity."""
    from . import intent_contract as ic
    mod = load_family_module(entry)
    src = f"{Path(entry['lane_dir']).name}/{entry['module']}"
    out = []
    for s in panel["sessions"]:
        sd = s["session_date"]
        obs = mod.build_observables(panel, calendar, sym, sd)
        excl = mod.apply_exclusions(panel, calendar, sym)
        sig = mod.signal(obs, sd, excl, sym, calendar, panel)
        for iid in sig.get("identity_draft_ids", []):
            rec = mod.order_intent(panel, obs, sig, iid, sym)
            if rec.get("status") != "ORDER_INTENT":
                continue
            if rec.get("exit_px_model") is None:
                continue
            out.append(ic.intent_from_function_adapter(rec, source_adapter=src))
    return out


def collect_intents(entry: dict, panel: dict, calendar: dict, *,
                    sym: str | None = None, asof=None) -> list[dict]:
    if entry["kind"] == "class":
        return collect_class_intents(entry, panel, calendar, asof=asof)
    if entry["kind"] == "function":
        return collect_fxeb_intents(entry, panel, calendar,
                                    sym or entry["symbols"][0])
    raise ValueError(f"unknown adapter kind {entry['kind']!r}")


def find_family(family: str) -> dict | None:
    for e in WIRED_FAMILIES:
        if e["family"] == family:
            return e
    return None
