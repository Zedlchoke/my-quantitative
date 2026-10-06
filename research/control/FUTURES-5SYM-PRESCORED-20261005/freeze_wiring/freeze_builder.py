#!/usr/bin/env python
"""freeze_builder.py — deterministic per-symbol FREEZE BUILDER for
FUTURES-5SYM-PRESCORED-20261005 (LANE-FREEZE-WIRING, wave 3, PREP-only).

SCOPE LAW (binding): the builder NEVER touches real data in this round.
`--input-manifest` points at SYNTHETIC manifests generated under sandbox temp
dirs; the REAL manifests are specified in the per-symbol FREEZE_BUILDER_SPEC
dossiers (nq/FREEZE_BUILDER_SPEC_NQ.md, fx_eb/FREEZE_BUILDER_SPEC_6E_6B.md,
fx_ja/FREEZE_BUILDER_SPEC_6J_6A.md) and their invocation is NOT_RUN in this
round (D9/PB2/PB3/ceilings all unsigned). Everything this builder emits is a
sandbox bundle stamped SYNTHETIC-SANDBOX and is NOT a research result.

GATE-0 (authority, fail-closed, evaluated BEFORE anything is read from the
input manifest; each refusal has its own exit code and always produces a
FINAL status artifact at --final-status-out; the bundle output dir is NEVER
created on refusal — "writes nothing" law, FREEZE_BUILDER_SPEC_NQ §0):

  symbol   required authority artifacts (all must parse + validate)
  -------  -----------------------------------------------------------
  NQ       d9_ratification@1  (decision ADOPT-D9-OptionA; meas_nq refusal
                              law mirrored: meas_nq/m2_f3_rebuild_harness
                              REFUSED_D9_UNSIGNED, exit 20 class)
           ceiling@1          (identity-table binding; owner option A/B/C)
  6E, 6B   pb2_lift@1         (P5-OD1 PB2 lift)
           ceiling@1
  6A       pb3_lift@1         (P5-D5 activation chain, step 1)
           d8_ratification@1  (decision ADOPT-D8-OptionA; measured
                               2020-11-20/23 tick-era boundary ratification)
           d9_ratification@1  (cease-guard standing law)
           ceiling@1
  6J       6j_ceiling@1       (P5-D1: names option J-A/J-B/J-C AND the
                               clock-shadow reading (a)/(b))
           ceiling@1          (identity-table binding)

  Refusal codes / exit codes (distinct per class):
    REFUSED_BAD_ARGS                        2
    REFUSED_GATE0_NQ_D9_UNSIGNED           21
    REFUSED_GATE0_CEILING_UNSIGNED         22
    REFUSED_GATE0_PB2_UNSIGNED             23
    REFUSED_GATE0_PB3_UNSIGNED             24
    REFUSED_GATE0_D8_UNSIGNED              25
    REFUSED_GATE0_6J_CEILING_UNSIGNED      26
    REFUSED_INPUT_DRIFT                    27
    REFUSED_GATE0_ARTIFACT_INVALID         29
    REFUSED_INPUT_MISSING                  30
    REFUSED_MANIFEST_INVALID               31

After GATE-0 passes, GATE-1 re-hashes EVERY manifest input (path + expected
sha256 [+ bytes]); any drift or missing file refuses (never silent reuse,
FREEZE_BUILDER_SPEC_NQ GATE-1 law). Then the bundle is emitted into
--out-dir (created only at that point):

  freeze_manifest_<SYM>.json      every input digest + params + the sha256 of
                                  this builder's own source (builder_code_sha256)
                                  + gate evidence + generated_at == --epoch
                                  (NEVER wallclock) + content_stamp (sha256 over
                                  the sorted input digests + params + code sha —
                                  content-derived determinism stamp)
  frozen_identity_table_<SYM>.json   verbatim copy of the identity_table input
  frozen_exclusion_calendar_<SYM>.json  verbatim copy of the exclusion_calendar
                                        input (calendar/exclusion table)

Determinism: identical manifest bytes + identical gate artifact bytes +
identical --epoch give byte-identical bundles (sorted keys; no wall-clock
fields anywhere). --epoch is REQUIRED: without it the builder refuses
(REFUSED_BAD_ARGS) rather than stamping wallclock.

CLI:
  python freeze_builder.py \
    --symbol NQ \
    --input-manifest <sandbox>/freeze_input_manifest.json \
    --gate-artifact d9=<sandbox>/d9.json --gate-artifact ceiling=<sandbox>/ceiling.json \
    --epoch 2026-10-05T00:00:00Z \
    --out-dir <sandbox>/out/bundle \
    --final-status-out <sandbox>/out/FREEZE_FINAL_STATUS.<label>.json \
    [--run-label label]

Exit codes: see table above; 0 = FREEZE_BUNDLE_COMPLETE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

CYCLE_ID = "FUTURES-5SYM-PRESCORED-20261005"
SANDBOX_STAMP = "SYNTHETIC-SANDBOX"
MANIFEST_SCHEMA = "futures_5sym_prescored/freeze_input_manifest@1"
BUNDLE_SCHEMA = "futures_5sym_prescored/freeze_manifest@1"
STATUS_SCHEMA = "futures_5sym_prescored/freeze_builder_final_status@1"

EXIT_OK = 0
EXIT_BAD_ARGS = 2

# GATE-0 refusal codes -> dedicated exit codes (fail-closed, distinct).
GATE_REFUSALS = {
    "REFUSED_GATE0_NQ_D9_UNSIGNED": 21,
    "REFUSED_GATE0_CEILING_UNSIGNED": 22,
    "REFUSED_GATE0_PB2_UNSIGNED": 23,
    "REFUSED_GATE0_PB3_UNSIGNED": 24,
    "REFUSED_GATE0_D8_UNSIGNED": 25,
    "REFUSED_GATE0_6J_CEILING_UNSIGNED": 26,
    "REFUSED_INPUT_DRIFT": 27,
    "REFUSED_GATE0_ARTIFACT_INVALID": 29,
    "REFUSED_INPUT_MISSING": 30,
    "REFUSED_MANIFEST_INVALID": 31,
}

# Per-symbol GATE-0 authority matrix: gate name -> artifact schema validator.
# Order matters (first failure wins) and is the meas_nq-law order: the D9/
# PB2/PB3 decision gates precede the ceiling binding.
SYMBOL_GATES: dict[str, list[tuple[str, str]]] = {
    "NQ": [("d9", "d9_ratification@1"), ("ceiling", "ceiling@1")],
    "6E": [("pb2", "pb2_lift@1"), ("ceiling", "ceiling@1")],
    "6B": [("pb2", "pb2_lift@1"), ("ceiling", "ceiling@1")],
    "6J": [("six_je_ceiling", "6j_ceiling@1"), ("ceiling", "ceiling@1")],
    "6A": [("pb3", "pb3_lift@1"), ("d8", "d8_ratification@1"),
           ("d9", "d9_ratification@1"), ("ceiling", "ceiling@1")],
}

VALID_ROLES = {
    "panel", "chain", "calendar", "exclusion_table", "cost_manifest",
    "spec_packet", "identity_table", "ceiling_table",
}
REQUIRED_ROLES = {"panel", "chain", "calendar", "exclusion_table",
                  "cost_manifest", "identity_table"}


def sha256_file(path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False)
            + "\n").encode("utf-8")


class GateRefusal(Exception):
    def __init__(self, code: str, detail: dict):
        super().__init__(code)
        self.code, self.detail = code, detail

    @property
    def exit_code(self) -> int:
        return GATE_REFUSALS.get(self.code, 2)


# --------------------------------------------------------- GATE-0 validators

def _require(cond: bool, code: str, detail: dict) -> None:
    if not cond:
        raise GateRefusal(code, detail)


def _signed_owner(art: dict) -> bool:
    return art.get("typed_by_owner") is True


def _validate_gate_artifact(gate: str, schema: str, art) -> dict:
    """Schema validators mirroring the meas_nq d9_ratification@1 refusal law:
    exact schema string, owner-typed signature, and decision/option fields
    where the law names them."""
    code = "REFUSED_GATE0_ARTIFACT_INVALID"
    _require(isinstance(art, dict), code, {"gate": gate,
                                           "error": "artifact unparseable or not an object"})
    _require(art.get("schema") == schema, code, {
        "gate": gate, "expected_schema": schema,
        "got_schema": art.get("schema")})
    _require(_signed_owner(art), code, {
        "gate": gate, "error": "artifact not owner-typed (typed_by_owner != true)"})
    if schema == "d9_ratification@1":
        _require(art.get("decision") == "ADOPT-D9-OptionA", code, {
            "gate": gate, "expected_decision": "ADOPT-D9-OptionA",
            "got_decision": art.get("decision"),
            "law": "meas_nq refusal law: unsigned or non-OptionA ADOPT-D9 "
                   "refuses the freeze (default = UNSIGNED)"})
    if schema == "d8_ratification@1":
        _require(art.get("decision") == "ADOPT-D8-OptionA", code, {
            "gate": gate, "expected_decision": "ADOPT-D8-OptionA",
            "got_decision": art.get("decision"),
            "law": "P5-D5 chain: ADOPT-D8 ratifies the measured 2020-11-20/23 "
                   "6A tick-era boundary (Option A); Option B demands the "
                   "exchange document and does not activate"})
    if schema == "6j_ceiling@1":
        _require(art.get("option") in ("J-A", "J-B", "J-C"), code, {
            "gate": gate, "expected_option": "J-A | J-B | J-C",
            "got_option": art.get("option"),
            "law": "P5-D1: the 6J ceiling signature must name ONE option "
                   "J-A(29)/J-B(36)/J-C(33|40)"})
        _require(art.get("clock_shadow_reading") in ("a", "b"), code, {
            "gate": gate, "expected_clock_shadow_reading": "a | b",
            "got": art.get("clock_shadow_reading"),
            "law": "P5-D1: the signature must name the clock-shadow reading "
                   "(a) shadow-inside-controls or (b) additive +1/family block"})
    if schema == "ceiling@1":
        _require(isinstance(art.get("option"), str) and art["option"], code, {
            "gate": gate, "error": "ceiling option name missing"})
        _require(isinstance(art.get("ceiling"), int) and art["ceiling"] > 0, code, {
            "gate": gate, "error": "ceiling must be a positive int"})
        _require(isinstance(art.get("identity_table"), dict), code, {
            "gate": gate,
            "error": "identity-table binding missing (ceiling@1 must name the "
                     "identity table it caps: {name, sha256})"})
        it = art["identity_table"]
        _require(isinstance(it.get("name"), str) and
                 isinstance(it.get("sha256"), str) and len(it["sha256"]) == 64, code, {
            "gate": gate, "error": "identity_table binding malformed "
                                   "({name, sha256} required)"})
    return art


def gate0(symbol: str, gate_paths: dict[str, str]) -> dict:
    """Evaluate GATE-0 for one symbol. Returns gate evidence dict; raises
    GateRefusal on the FIRST failing gate (fail-closed, ordered)."""
    _require(symbol in SYMBOL_GATES, "REFUSED_MANIFEST_INVALID",
             {"error": f"unsupported symbol {symbol!r}",
              "supported": sorted(SYMBOL_GATES)})
    evidence = {"gates": [], "artifacts": {}}
    for gate, schema in SYMBOL_GATES[symbol]:
        p = gate_paths.get(gate)
        _require(p, {
            "d9": "REFUSED_GATE0_NQ_D9_UNSIGNED",
            "pb2": "REFUSED_GATE0_PB2_UNSIGNED",
            "pb3": "REFUSED_GATE0_PB3_UNSIGNED",
            "d8": "REFUSED_GATE0_D8_UNSIGNED",
            "six_je_ceiling": "REFUSED_GATE0_6J_CEILING_UNSIGNED",
            "ceiling": "REFUSED_GATE0_CEILING_UNSIGNED",
        }[gate], {
            "gate": gate, "expected_schema": schema,
            "law": {
                "d9": "ADOPT-D9 (cease-guard standing law + cache_v3 "
                      "canonicalization) is UNSIGNED — meas_nq refusal law "
                      "mirrored: default = UNSIGNED, never inferred",
                "pb2": "PB2 HOLD stands for 6E/6B (P5-OD1) — no pb2_lift@1 "
                       "artifact; no FX-EB freeze",
                "pb3": "6A stays PB3 PARK (P5-D5 step 1 unsigned) — "
                       "BLOCKED_PB3_PARK posture",
                "d8": "ADOPT-D8 unratified (P5-D5 step 2) — "
                      "BLOCKED_D8_UNRATIFIED posture",
                "six_je_ceiling": "No 6J ceiling exists anywhere (P5-D1) — "
                                  "BLOCKED_NO_CEILING posture; builder refuses",
                "ceiling": "owner ceiling (identity-table binding) unsigned — "
                           "no identity enumeration may be frozen",
            }[gate]})
        art, err = _load_json(p)
        _require(err is None, "REFUSED_GATE0_ARTIFACT_INVALID",
                 {"gate": gate, "path": p, "error": err})
        _validate_gate_artifact(gate, schema, art)
        evidence["gates"].append({"gate": gate, "schema": schema,
                                  "status": "PASSED"})
        evidence["artifacts"][gate] = {"path": str(p),
                                       "sha256": sha256_file(p)}
    return evidence


def _load_json(path: str):
    p = Path(path)
    if not p.is_file():
        return None, f"missing file {p}"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        return None, f"unreadable/unparseable {p}: {exc}"


# ------------------------------------------------------------------ GATE-1

def gate1_rehash(manifest: dict, manifest_dir: str) -> list[dict]:
    """Re-hash EVERY manifest input; drift or missing file refuses (never
    silent reuse). Returns the verified digest table."""
    inputs = manifest.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise GateRefusal("REFUSED_MANIFEST_INVALID",
                          {"error": "inputs[] missing or empty"})
    seen_roles = set()
    verified = []
    for ent in inputs:
        if not isinstance(ent, dict) or not all(
                k in ent for k in ("role", "path", "sha256")):
            raise GateRefusal("REFUSED_MANIFEST_INVALID",
                              {"error": "input entry missing role/path/sha256",
                               "entry": ent})
        role, rel = ent["role"], ent["path"]
        _require(role in VALID_ROLES, "REFUSED_MANIFEST_INVALID",
                 {"error": f"unknown input role {role!r}",
                  "valid_roles": sorted(VALID_ROLES)})
        seen_roles.add(role)
        p = rel if os.path.isabs(rel) else os.path.join(manifest_dir, rel)
        got = sha256_file(p)
        if got is None:
            raise GateRefusal("REFUSED_INPUT_MISSING",
                              {"role": role, "path": p})
        if got != ent["sha256"]:
            raise GateRefusal("REFUSED_INPUT_DRIFT", {
                "role": role, "path": p,
                "expected_sha256": ent["sha256"], "actual_sha256": got,
                "law": "GATE-1: any digest drift refuses the freeze — never "
                       "silent reuse (FREEZE_BUILDER_SPEC_NQ §1 law)"})
        row = {"role": role, "path": rel, "sha256": got,
               "bytes": os.path.getsize(p)}
        if ent.get("bytes") is not None and int(ent["bytes"]) != row["bytes"]:
            raise GateRefusal("REFUSED_INPUT_DRIFT", {
                "role": role, "path": p, "expected_bytes": ent["bytes"],
                "actual_bytes": row["bytes"]})
        verified.append(row)
    missing = REQUIRED_ROLES - seen_roles
    _require(not missing, "REFUSED_MANIFEST_INVALID", {
        "error": f"required input roles missing: {sorted(missing)}",
        "required_roles": sorted(REQUIRED_ROLES)})
    return verified


# ----------------------------------------------------------------- builder

def build_bundle(symbol: str, manifest: dict, manifest_dir: str,
                 verified: list[dict], gate_evidence: dict, epoch: str,
                 out_dir: str, builder_source: str) -> dict:
    """Emit the sandbox FREEZE BUNDLE. Deterministic: sorted keys, no
    wallclock; content_stamp is content-derived."""
    identity_rows = [r for r in verified if r["role"] == "identity_table"]
    cal_rows = [r for r in verified if r["role"] in ("calendar", "exclusion_table")]
    it_path = os.path.join(manifest_dir, identity_rows[0]["path"])
    it_data, err = _load_json(it_path)
    if err:
        raise GateRefusal("REFUSED_INPUT_DRIFT",
                          {"role": "identity_table", "path": it_path,
                           "error": f"identity table unparseable at emit: {err}"})
    if len(cal_rows) < 1:
        raise GateRefusal("REFUSED_MANIFEST_INVALID",
                          {"error": "at least one calendar/exclusion_table "
                                    "input is required",
                           "found": len(cal_rows)})
    frozen_cal = {}
    for row in cal_rows:
        cal_path = os.path.join(manifest_dir, row["path"])
        cal_data, err = _load_json(cal_path)
        if err:
            raise GateRefusal("REFUSED_INPUT_DRIFT",
                              {"role": row["role"], "path": cal_path,
                               "error": f"calendar unparseable at emit: {err}"})
        frozen_cal[row["role"]] = cal_data

    params = dict(manifest.get("params") or {})
    params.setdefault("symbol", symbol)
    params.setdefault("sandbox_stamp", SANDBOX_STAMP)
    code_sha = sha256_file(builder_source)
    input_digests = sorted(
        [{"role": r["role"], "path": r["path"], "sha256": r["sha256"],
          "bytes": r["bytes"]} for r in verified],
        key=lambda r: (r["role"], r["path"]))
    content_stamp = sha256_bytes(canonical_json({
        "inputs": input_digests, "params": params, "code_sha256": code_sha,
        "epoch": epoch, "cycle_id": CYCLE_ID, "symbol": symbol}))

    frozen_manifest = {
        "schema": BUNDLE_SCHEMA,
        "cycle_id": CYCLE_ID,
        "symbol": symbol,
        "sandbox_stamp": SANDBOX_STAMP,
        "generated_at": epoch,
        "content_stamp_sha256": content_stamp,
        "builder_code_sha256": code_sha,
        "input_digests": input_digests,
        "params": params,
        "gate0_evidence": gate_evidence,
        "identity_table_binding": {
            "name": (it_data.get("name") if isinstance(it_data, dict) else None)
            or Path(it_path).name,
            "sha256": identity_rows[0]["sha256"]},
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"freeze_manifest_{symbol}.json").write_bytes(
        canonical_json(frozen_manifest))
    (out / f"frozen_identity_table_{symbol}.json").write_bytes(
        canonical_json(it_data))
    (out / f"frozen_exclusion_calendar_{symbol}.json").write_bytes(
        canonical_json(frozen_cal))
    return frozen_manifest


# ------------------------------------------------- cease-guard chain law
# CEASE_GUARD_STANDARD.md §2 shape (synthetic evaluation only in this round):
# switch date = max(volume-crossover, cease-floor); the cease-floor fires on
# the first date the naive held contract has NO bars (violation). The guard
# variant must differ from the naive chain EXACTLY on the guarded date and
# after — never before (the test embeds a 6A-style violation day).

def cease_guard_chain(naive_chain: list[dict],
                      sessions_with_bars: set) -> dict:
    """naive_chain rows: {'date','held','next'} sorted by date.
    sessions_with_bars: set of (date, contract) pairs — the dates each
    candidate contract actually has bars. The cease-floor fires on the first
    date the naive held contract has NO bars (violation); from that date the
    guarded chain carries the NEXT contract. Returns both variants + first
    divergence date. Pure, deterministic."""
    naive = [(r["date"], r["held"]) for r in naive_chain]
    guarded = []
    floor_fire = None
    for r in naive_chain:
        d, held, nxt = r["date"], r["held"], r["next"]
        if floor_fire is None and (d, held) not in sessions_with_bars and nxt:
            floor_fire = d
        if floor_fire is not None and d >= floor_fire and nxt:
            guarded.append((d, nxt))
        else:
            guarded.append((d, held))
    first_diff = next((d for (d, a), (_, b) in zip(naive, guarded) if a != b),
                      None)
    return {"naive": naive, "guarded": guarded, "cease_floor_first_fire": floor_fire,
            "first_divergence_date": first_diff}


# ------------------------------------------------------------------- main

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="deterministic per-symbol freeze builder (sandbox bundles "
                    "only in this PREP round; real manifests NOT_RUN)")
    ap.add_argument("--symbol", required=True,
                    help="NQ | 6E | 6B | 6J | 6A")
    ap.add_argument("--input-manifest", required=True,
                    help="freeze input manifest JSON (SYNTHETIC in this round)")
    ap.add_argument("--gate-artifact", action="append", default=[],
                    help="gate artifact as name=path; repeatable "
                         "(d9=, pb2=, pb3=, d8=, six_je_ceiling=, ceiling=)")
    ap.add_argument("--epoch", required=True,
                    help="determinism stamp (e.g. 2026-10-05T00:00:00Z); "
                         "REQUIRED — the builder never reads the wallclock")
    ap.add_argument("--out-dir", required=True,
                    help="bundle output dir (created ONLY on success)")
    ap.add_argument("--final-status-out", required=True,
                    help="FINAL status artifact path (ALWAYS written, even "
                         "on refusal)")
    ap.add_argument("--run-label", default="freeze1")
    return ap


def write_status(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(canonical_json(payload))


def main(argv=None) -> int:
    ns = build_arg_parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    builder_source = str(Path(__file__).resolve())
    status_path = ns.final_status_out
    try:
        if ns.symbol not in SYMBOL_GATES:
            raise GateRefusal("REFUSED_MANIFEST_INVALID",
                              {"error": f"unsupported symbol {ns.symbol!r}"})
        gate_paths = {}
        for ent in ns.gate_artifact:
            if "=" not in ent:
                raise GateRefusal("REFUSED_BAD_ARGS",
                                  {"error": f"--gate-artifact must be name=path: {ent!r}"})
            k, v = ent.split("=", 1)
            gate_paths[k] = v
        manifest, err = _load_json(ns.input_manifest)
        if err or not isinstance(manifest, dict):
            raise GateRefusal("REFUSED_MANIFEST_INVALID",
                              {"path": ns.input_manifest, "error": err})
        if manifest.get("schema") != MANIFEST_SCHEMA:
            raise GateRefusal("REFUSED_MANIFEST_INVALID", {
                "path": ns.input_manifest,
                "expected_schema": MANIFEST_SCHEMA,
                "got_schema": manifest.get("schema")})
        if manifest.get("cycle_id") != CYCLE_ID:
            raise GateRefusal("REFUSED_MANIFEST_INVALID",
                              {"error": "manifest cycle_id mismatch",
                               "expected": CYCLE_ID,
                               "got": manifest.get("cycle_id")})
        if manifest.get("symbol") != ns.symbol:
            raise GateRefusal("REFUSED_MANIFEST_INVALID", {
                "error": "manifest symbol != --symbol",
                "manifest_symbol": manifest.get("symbol"),
                "arg_symbol": ns.symbol})

        # GATE-0 first (authority) — nothing in the input set is consumed yet.
        gate_evidence = gate0(ns.symbol, gate_paths)
        # GATE-1: re-hash every input (drift refuses).
        verified = gate1_rehash(manifest,
                                os.path.dirname(os.path.abspath(ns.input_manifest)))
        # Emit the bundle (out dir created only here).
        frozen = build_bundle(ns.symbol, manifest,
                              os.path.dirname(os.path.abspath(ns.input_manifest)),
                              verified, gate_evidence, ns.epoch, ns.out_dir,
                              builder_source)
        write_status(status_path, {
            "schema": STATUS_SCHEMA, "cycle_id": CYCLE_ID,
            "run_label": ns.run_label, "symbol": ns.symbol,
            "status": "FREEZE_BUNDLE_COMPLETE", "exit_code": EXIT_OK,
            "refusal_code": None, "gates": gate_evidence["gates"],
            "inputs_consumed": len(verified),
            "bundle_dir": str(ns.out_dir),
            "bundle": {
                "manifest": f"freeze_manifest_{ns.symbol}.json",
                "identity_table": f"frozen_identity_table_{ns.symbol}.json",
                "exclusion_calendar": f"frozen_exclusion_calendar_{ns.symbol}.json"},
            "content_stamp_sha256": frozen["content_stamp_sha256"],
            "generated_at": ns.epoch, "sandbox_stamp": SANDBOX_STAMP,
            "round_law": "SYNTHETIC-SANDBOX ONLY in this PREP round; real "
                         "manifest invocation NOT_RUN"})
        return EXIT_OK
    except GateRefusal as exc:
        write_status(status_path, {
            "schema": STATUS_SCHEMA, "cycle_id": CYCLE_ID,
            "run_label": ns.run_label, "symbol": ns.symbol,
            "status": exc.code, "exit_code": exc.exit_code,
            "refusal_code": exc.code, "refusal_detail": exc.detail,
            "inputs_consumed": 0, "bundle_dir": None,
            "sandbox_stamp": SANDBOX_STAMP,
            "law": "fail-closed: no bundle output dir was created; the FINAL "
                   "status artifact is the ONLY artifact (advisory, never a "
                   "gate pass)"})
        print(f"REFUSED: {exc.code} — "
              f"{json.dumps(exc.detail, ensure_ascii=False)[:600]}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
