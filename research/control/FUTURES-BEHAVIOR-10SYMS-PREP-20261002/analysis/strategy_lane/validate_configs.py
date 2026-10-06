#!/usr/bin/env python3
"""validate_configs.py — STRATEGY-CONFIGS lane, FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Validates configs/symbols/*.yaml (10) + configs/pilot_nq_cl.yaml against
configs/schema.json (restricted JSON-Schema subset, see schema.schema_dialect)
plus cross-config integrity checks:

  1. restricted-subset structural validation ($ref/#/definitions, type, const,
     enum, required, properties, additionalProperties, items, minItems, pattern
     via re.fullmatch)
  2. expected symbol set = {NQ ES CL NG GC SI 6E 6J 6B 6A}, one file each
  3. dossier_sha256 == actual sha256 of dossiers/{SYM}_DOSSIER.md
  4. hypothesis id/symbol consistency + uniqueness
  5. requirement classes within schema vocabularies (corpus + external)
  6. rank integrity: unique 1..N AND equal to the deterministic re-derivation
     from feasibility fields (acquisition_cost, mechanization, dossier order) —
     the declared rank rule (feasibility, explicitly NOT PnL)
  7. param-gap id scoping (gap ids belong to their hypothesis)
  8. scored_run blocks always disclose REGISTRATION_REQUIRED_FOR_SCORED_RUN
  9. pilot: legs reference existing hypotheses; param_gaps_ref resolve;
     controls complete (flat / always-on x2 / single-leg x2 / leave-one-leg
     FULL_PATH / on-off accounting / TB TRAIN_ONLY / cost stress x3 /
     entry-delay slots / roll A/B / AMBIGUOUS_ORDER law); trial arithmetic
     (2 x 1 x 2 x 3 x 2 x 3 = 72 primary + 5 baselines + 2 ablations = 79)

Pure stdlib + PyYAML. No data access, no network, deterministic.
Exit 0 = PASS, 1 = FAIL. Report JSON written to
analysis/strategy_lane/validate_configs_report.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

CYCLE = Path(__file__).resolve().parents[2]   # .../FUTURES-BEHAVIOR-10SYMS-PREP-20261002
CONFIGS = CYCLE / "configs"
SYMBOLS_DIR = CONFIGS / "symbols"
PILOT = CONFIGS / "pilot_nq_cl.yaml"
SCHEMA_PATH = CONFIGS / "schema.json"
REPORT_PATH = CYCLE / "analysis" / "strategy_lane" / "validate_configs_report.json"

EXPECTED_SYMBOLS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]

ACQ_ORDER = {"in_hand_now": 0, "free_public": 1, "owner_declaration": 2, "vendor_paid": 3}
MECH_ORDER = {"high": 2, "medium": 1, "low": 0}


class VErr(Exception):
    pass


def resolve_ref(schema_doc: dict, ref: str) -> dict:
    assert ref.startswith("#/"), f"only local $ref supported: {ref}"
    node = schema_doc
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def validate(node, schema, path: str, schema_doc: dict, errors: list) -> None:
    """Restricted JSON-Schema subset validator (see schema.schema_dialect)."""
    try:
        if "$ref" in schema:
            validate(node, resolve_ref(schema_doc, schema["$ref"]), path, schema_doc, errors)
            return
        t = schema.get("type")
        if t == "object":
            if not isinstance(node, dict):
                raise VErr(f"expected object, got {type(node).__name__}")
            for req in schema.get("required", []):
                if req not in node:
                    raise VErr(f"missing required property '{req}'")
            props = schema.get("properties", {})
            if schema.get("additionalProperties") is False:
                for k in node:
                    if k not in props:
                        raise VErr(f"additional property '{k}' not allowed")
            for k, sub in props.items():
                if k in node:
                    validate(node[k], sub, f"{path}.{k}", schema_doc, errors)
        elif t == "array":
            if not isinstance(node, list):
                raise VErr(f"expected array, got {type(node).__name__}")
            if len(node) < schema.get("minItems", 0):
                raise VErr(f"array shorter than minItems={schema.get('minItems')}")
            if "items" in schema:
                for i, item in enumerate(node):
                    validate(item, schema["items"], f"{path}[{i}]", schema_doc, errors)
        elif t == "string":
            if not isinstance(node, str):
                raise VErr(f"expected string, got {type(node).__name__}")
            if "pattern" in schema and not re.fullmatch(schema["pattern"], node):
                raise VErr(f"string {node!r} does not match pattern {schema['pattern']!r}")
        elif t == "integer":
            if not isinstance(node, int) or isinstance(node, bool):
                raise VErr(f"expected integer, got {type(node).__name__}")
        elif t == "number":
            if not isinstance(node, (int, float)) or isinstance(node, bool):
                raise VErr(f"expected number, got {type(node).__name__}")
        elif t == "boolean":
            if not isinstance(node, bool):
                raise VErr(f"expected boolean, got {type(node).__name__}")
        if "const" in schema and node != schema["const"]:
            raise VErr(f"const mismatch: expected {schema['const']!r}, got {node!r}")
        if "enum" in schema and node not in schema["enum"]:
            raise VErr(f"enum mismatch: {node!r} not in {schema['enum']}")
    except VErr as e:
        errors.append(f"{path}: {e}")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def derive_ranks(hyps: list) -> dict:
    """Deterministic rank re-derivation per the schema's rank_rule."""
    keyed = []
    for h in hyps:
        num = int(re.fullmatch(r"[A-Z0-9]{2}-H([1-9])", h["id"]).group(1))
        key = (ACQ_ORDER[h["feasibility"]["acquisition_cost"]],
               -MECH_ORDER[h["feasibility"]["mechanization"]],
               num)
        keyed.append((key, h["id"]))
    keyed.sort()
    return {hid: i + 1 for i, (_, hid) in enumerate(keyed)}


def main() -> int:
    report = {"validator": "analysis/strategy_lane/validate_configs.py",
              "schema": str(SCHEMA_PATH.relative_to(CYCLE)),
              "files": [], "cross_checks": [], "errors": [], "warnings": [],
              "summary": {}}
    errors: list[str] = report["errors"]
    warnings: list[str] = report["warnings"]

    schema_doc = json.loads(SCHEMA_PATH.read_text())
    vocab = schema_doc["vocabularies"]
    all_classes = set(vocab["corpus_requirement_classes"]) | set(vocab["external_requirement_classes"])

    symbol_files = sorted(SYMBOLS_DIR.glob("*.yaml"))
    got_symbols = sorted(p.stem for p in symbol_files)
    if got_symbols != sorted(EXPECTED_SYMBOLS):
        errors.append(f"symbol file set mismatch: {got_symbols} != {sorted(EXPECTED_SYMBOLS)}")

    all_hyp_ids = set()
    per_symbol = {}

    for p in symbol_files:
        entry = {"file": str(p.relative_to(CYCLE)), "errors": [], "n_hypotheses": 0}
        cfg = yaml.safe_load(p.read_text())
        validate(cfg, schema_doc["definitions"]["symbol_config"],
                 str(p.relative_to(CYCLE)), schema_doc, entry["errors"])
        errors.extend(entry["errors"])
        if entry["errors"]:
            report["files"].append(entry)
            if isinstance(cfg, dict) and cfg.get("symbol"):
                per_symbol[cfg["symbol"]] = cfg
            continue

        sym = cfg["symbol"]
        if sym != p.stem:
            entry["errors"].append(f"symbol {sym} != filename stem {p.stem}")

        dossier = CYCLE / cfg["source_dossier"]
        if not dossier.exists():
            entry["errors"].append(f"dossier missing: {cfg['source_dossier']}")
        else:
            actual = sha256_file(dossier)
            if actual != cfg["dossier_sha256"]:
                entry["errors"].append(
                    f"dossier_sha256 mismatch for {sym}: {cfg['dossier_sha256']} != {actual}")

        hyps = cfg["hypotheses"]
        entry["n_hypotheses"] = len(hyps)
        ids = [h["id"] for h in hyps]
        if len(set(ids)) != len(ids):
            entry["errors"].append(f"duplicate hypothesis ids: {ids}")
        for h in hyps:
            if not h["id"].startswith(f"{sym}-"):
                entry["errors"].append(f"{h['id']} does not match symbol {sym}")
            if h["id"] in all_hyp_ids:
                entry["errors"].append(f"hypothesis id {h['id']} duplicated across files")
            all_hyp_ids.add(h["id"])
            if h["mechanism_class"] != "POSTULATED":
                entry["errors"].append(f"{h['id']}: mechanism_class must be POSTULATED")
            if not h["pit_trigger"]["mechanizable"] and h["minimal_test"]["kind"] not in (
                    "none_structurally_blocked",):
                warnings.append(f"{h['id']}: pit_trigger not mechanizable - verify minimal test kind")
            for tb_key in ("minimal_test", "scored_run"):
                for r in h[tb_key]["requirements"]:
                    if r["class"] not in all_classes:
                        entry["errors"].append(
                            f"{h['id']}.{tb_key}: unknown requirement class {r['class']}")
                    if not r["symbols"]:
                        entry["errors"].append(f"{h['id']}.{tb_key}: empty symbols")
            if "REGISTRATION_REQUIRED_FOR_SCORED_RUN" not in h["scored_run"]["nondata_blockers"]:
                entry["errors"].append(
                    f"{h['id']}: scored_run.nondata_blockers must disclose "
                    "REGISTRATION_REQUIRED_FOR_SCORED_RUN")
            for gap in h["param_gaps"]:
                if not gap["id"].startswith(h["id"] + "-"):
                    entry["errors"].append(
                        f"param gap {gap['id']} not scoped to {h['id']}")

        ranks = {h["rank"] for h in hyps}
        n = len(hyps)
        if ranks != set(range(1, n + 1)):
            entry["errors"].append(f"{sym}: ranks {sorted(ranks)} != 1..{n}")
        derived = derive_ranks(hyps)
        for h in hyps:
            if h["rank"] != derived[h["id"]]:
                entry["errors"].append(
                    f"{sym}: rank of {h['id']} is {h['rank']} but feasibility-derived "
                    f"rank is {derived[h['id']]} (rank rule: acquisition_cost, then "
                    "mechanization desc, then dossier order)")
        errors.extend(entry["errors"])
        per_symbol[sym] = cfg
        report["files"].append(entry)

    # ---------------- pilot ----------------
    pilot_entry = {"file": str(PILOT.relative_to(CYCLE)), "errors": [], "n_legs": 0}
    pilot = yaml.safe_load(PILOT.read_text())
    validate(pilot, schema_doc["definitions"]["pilot_config"],
             str(PILOT.relative_to(CYCLE)), schema_doc, pilot_entry["errors"])
    errors.extend(pilot_entry["errors"])
    if not pilot_entry["errors"]:
        pilot_entry["n_legs"] = len(pilot["legs"])
        gap_ids = set()
        for sym in ("NQ", "CL"):
            for h in per_symbol[sym]["hypotheses"]:
                gap_ids.update(g["id"] for g in h["param_gaps"])
        for leg in pilot["legs"]:
            if leg["hypothesis_id"] not in all_hyp_ids:
                pilot_entry["errors"].append(
                    f"pilot leg {leg['leg_id']}: unknown hypothesis {leg['hypothesis_id']}")
            sym = leg["symbol"]
            if sym not in per_symbol:
                pilot_entry["errors"].append(
                    f"pilot leg {leg['leg_id']}: symbol config {sym} failed to load - see above")
                continue
            if not leg["hypothesis_id"].startswith(f"{sym}-"):
                pilot_entry["errors"].append(
                    f"pilot leg {leg['leg_id']}: hypothesis {leg['hypothesis_id']} "
                    f"not a {sym} hypothesis")
            for ref in leg["param_gaps_ref"]:
                if ref not in gap_ids:
                    pilot_entry["errors"].append(
                        f"pilot leg {leg['leg_id']}: param_gaps_ref {ref} unresolved")
        ta = pilot["trial_accounting_declaration"]
        expect_primary = 2 * 1 * 2 * 3 * 2 * 3
        if ta["primary_cells"] != expect_primary:
            pilot_entry["errors"].append(
                f"pilot primary_cells {ta['primary_cells']} != formula result {expect_primary}")
        b = ta["baselines"]
        ab = ta["ablations"]
        total = (ta["primary_cells"] + b["flat"] + b["always_on"] + b["single_leg"]
                 + ab["leave_one_leg"])
        if ta["total_declared_trials"] != total:
            pilot_entry["errors"].append(
                f"pilot total_declared_trials {ta['total_declared_trials']} != {total}")
        if pilot["controls"]["leave_one_leg"]["mode"] != "FULL_PATH_RERUN":
            pilot_entry["errors"].append("leave_one_leg must be FULL_PATH_RERUN")
        if pilot["seed_protocol"]["master_seed"] != 20261002:
            pilot_entry["errors"].append("master seed must be 20261002")
        if sorted(pilot["variants"]["cost_stress"]) != [1.0, 1.5, 2.0]:
            pilot_entry["errors"].append("cost stress must be [1.0, 1.5, 2.0]")
        if pilot["variants"]["entry_delay_sessions"] != [0, 1, 2]:
            pilot_entry["errors"].append("entry delay slots must be [0, 1, 2]")
        errors.extend(pilot_entry["errors"])
    report["files"].append(pilot_entry)

    n_hyps = sum(e.get("n_hypotheses", 0) for e in report["files"])
    report["summary"] = {
        "symbol_configs": len(symbol_files),
        "pilot_configs": 1,
        "hypotheses_total": n_hyps,
        "errors": len(errors),
        "warnings": len(warnings),
        "verdict": "PASS" if not errors else "FAIL",
        "rank_rule": "feasibility (acquisition_cost -> mechanization desc -> dossier order), explicitly NOT PnL",
        "dossier_hash_check": "every configs/symbols/*.yaml dossier_sha256 re-verified against the dossier file",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=1, sort_keys=False) + "\n")
    print(json.dumps(report["summary"], indent=1))
    if errors:
        print(f"\nFAIL — {len(errors)} error(s):", file=sys.stderr)
        for e in errors[:40]:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("\nPASS — all configs valid against configs/schema.json + cross-checks")
    print(f"report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
