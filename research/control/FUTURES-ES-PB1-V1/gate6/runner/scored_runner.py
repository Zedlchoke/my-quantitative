#!/usr/bin/env python
"""scored_runner.py — FUTURES-ES-PB1-V1 gate-6 scored runner (contract v2
+ v2.1 addendum: the real execution path).

Operative launch contract: gate6/runner/LAUNCH_CONTRACT_V2.md (+ .json, the
pin source). Supersedes gate6/scored_runner_spec.md (v1, HISTORY — it pointed
at the superseded freeze v2 / builder v2.1 / withdrawn DONOR_LAW_CARRYOVER).

PRE-GO LAW: this runner REFUSES to compute scored outcomes unless EVERY
refusal gate (R0 registry, R1 GO, R2 auth, R3 heavy lock, R4 drift,
R5 adjudication) passes against the typed owner GO artifact. Today — with no
GO artifact at the cycle's gate — the runner refuses. When all gates pass,
the runner delegates to the REAL execution path in scored_executor.py
(heavy-lock lifecycle with post-acquire TOCTOU re-verification, machinery-
of-record computation via final/dryrun_builder_v3.py, per-identity terminal
rows in the FIXED 24-slot ledger, per-identity outputs + reconciliation,
byte-identical reproduction twin, terminal-audit handoff, fail-closed law).
The pre-GO "WOULD EXECUTE" STUB is REMOVED (withdrawal record:
GO_READY_WITHDRAWAL.md); the stub string no longer exists in this file.

SANDBOX ISOLATION LAW (--sandbox-root): synthetic test fixtures and fault
injection live ONLY under an explicit sandbox root. When set: (a) authority
inputs (GO artifact, registry row copy, contract, freeze/panel paths, ledger,
lock runtime) resolve under the sandbox; (b) every output carries the
SYNTHETIC-SANDBOX stamp; (c) combining --sandbox-root with any real-root
authority path REFUSES; (d) the production default (no flag) uses ONLY the
real paths + real authority — any production-mode path override that would
let execution proceed is refused (anti-bypass guard); (e) a sandbox run
cannot write the real ledger, the real registry, or the machine-wide
heavy-lock runtime.

Ledger law: run-level refusals are recorded via the FIXED gate6/trial_ledger.py
(imported, never reimplemented; its sha is re-verified at startup) as REFUSED
rows with identity_id=None; REFUSED never increments the observed denominator.
--preflight-only mode writes NOTHING (except the optional deterministic
--manifest-out) and performs read-only existence+sha checks on the REAL
authority paths — never outcome computation, never a parquet parse.

PIN-ENFORCE law (fix3, 2026-10-05 — closes F-V1/F-V2; dispatch
PIN-ENFORCE): ONE live-operative-pin definition everywhere —
live_operative_pins() = base pins + every v2_*_addendum's new_pins,
superseded BY ARTIFACT PATH (later addendum wins); history rows are
evidence-only, never gate inputs. The execution gate refuses whenever
check_drift.pass is false REGARDLESS of which pin mismatched (explicit
fail-closed line; the RefusalGate facts — now built from the full LIVE set —
are not the only path). The post-acquire TOCTOU re-verify closure is built
over the FULL LIVE pin set (the executor's base-only TOCTOU_PIN_NAMES tuple
is removed). At the execution boundary the modules ACTUALLY imported (the
runner's own __file__ and scored_executor.__file__) are hashed against
their live pins — path equality AND sha equality; mismatch refuses before
computation.

Exit codes: 0 = EXECUTION_COMPLETE (or preflight wiring green);
2 = REFUSED_* ; 75 = NOT_RUN_RESOURCE_CONFLICT ; 3 = technical failure or
terminal execution failure (TWIN_MISMATCH / PUBLICATION_FAILURE /
COMPUTE_FAILURE / RECONCILIATION_FAILURE / ABORTED_SANDBOX_FAULT) ;
4 = FINALIZATION_FAILURE (executor D-7, pending ratification: the
computation may have completed but the evidentiary closure — ledger
summary / lock release / terminal handoff — failed) — never a silent pass.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CYCLE_ID = "FUTURES-ES-PB1-V1"
CANONICAL_GO_PHRASE = "GO FUTURES-ES-PB1-V1 SCORED EXECUTION"
DEFAULT_WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
ROOT_REGISTRY = "/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json"

RUNNER_DIR = Path(__file__).resolve().parent
DEFAULT_CONTRACT = RUNNER_DIR / "LAUNCH_CONTRACT_V2.json"

# delegation markers — a GO carrying any of these is NOT an owner GO
DELEGATION_MARKERS = ("delegat", "on behalf of", "thay mặt", "proxy")

EXIT_OK, EXIT_REFUSED, EXIT_TECHNICAL, EXIT_CONFLICT = 0, 2, 3, 75


# ---------------------------------------------------------------- utilities

def sha256_file(path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    import hashlib
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None  # unreadable pin => None => drift fail (PIN-ENFORCE law 6)


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


def git_out(args: list[str], worktree: str):
    """Read-only git query against the worktree -> (stdout, rc, err)."""
    try:
        out = subprocess.run(
            ["git", "-C", worktree] + args, capture_output=True, text=True,
            timeout=20)
        return out.stdout.strip(), out.returncode, out.stderr.strip()[:300]
    except (OSError, subprocess.SubprocessError) as exc:
        return None, -1, str(exc)[:300]


# ------------------------------------------------- canonical lock inspect
#
# Reimplementation of governance.heavy_lock.inspect() with an INJECTABLE
# runtime dir (the canonical function hardcodes machine_runtime_dir(), which
# makes the real lock untestable). The decision tree is the canonical one,
# step for step, and is DELEGATED to the governance module's own primitives
# (_load_registry / flock_state / _pid_alive / process_start_token) — never a
# weaker check. Default runtime == the canonical machine-wide runtime.

def lock_inspect(runtime_dir: str | None = None) -> dict:
    from governance import heavy_lock  # <worktree>/research on sys.path

    runtime = (Path(runtime_dir) if runtime_dir
               else Path(heavy_lock.machine_runtime_dir()))
    lock_path = runtime / heavy_lock.LOCK_NAME
    registry_path = runtime / heavy_lock.REGISTRY_NAME

    row, err = heavy_lock._load_registry(registry_path)
    if err is not None:
        return {"verdict": heavy_lock.VERDICT_DRIFT,
                "reason": f"registry malformed ({err}) — fail closed, "
                          "preserved for inspection"}
    flock = heavy_lock.flock_state(lock_path)
    if row is None:
        if flock == "free":
            return {"verdict": heavy_lock.VERDICT_FREE_PROVEN,
                    "reason": "no registry row and the lock file is not flocked"}
        return {"verdict": heavy_lock.VERDICT_DRIFT,
                "reason": "lock file is flocked but no registry row exists — "
                          "holder unknown"}
    status = row.get("status")
    pid = row.get("pid")
    if status != "RUNNING":
        return {"verdict": heavy_lock.VERDICT_DRIFT,
                "reason": f"registry row status {status!r} (not RUNNING) — "
                          "bookkeeping contradicts a clean lock state"}
    if not isinstance(pid, int):
        return {"verdict": heavy_lock.VERDICT_DRIFT,
                "reason": "malformed RUNNING row (pid missing or not an int)"}
    alive = heavy_lock._pid_alive(pid)
    live_token = heavy_lock.process_start_token(pid) if alive else None
    row_token = row.get("process_start_token")
    token_match = bool(alive and live_token and row_token
                       and live_token == row_token)
    if alive and token_match and flock == "held":
        return {"verdict": heavy_lock.VERDICT_HELD_PROVEN,
                "reason": f"pid {pid} alive, process-start token matches the "
                          f"registry row, and the flock is held "
                          f"({row.get('cycle_id')}/{row.get('role')})"}
    if not alive:
        return {"verdict": heavy_lock.VERDICT_DRIFT,
                "reason": f"RUNNING registry row pid {pid} is dead — stale "
                          "registry (reclaim only per round-2 discipline)"}
    if not row_token or live_token is None:
        return {"verdict": heavy_lock.VERDICT_DRIFT,
                "reason": "pid alive with missing or unrecoverable "
                          "process-start token — liveness unverifiable"}
    if not token_match:
        return {"verdict": heavy_lock.VERDICT_DRIFT,
                "reason": f"process-start token mismatch for pid {pid} "
                          "(PID reuse or stale registry row)"}
    return {"verdict": heavy_lock.VERDICT_DRIFT,
            "reason": "pid alive + token match while the flock is free — "
                      "bookkeeping contradicts the OS"}


# ------------------------------------------------------------- R0 registry

def check_registry(worktree: str, registry_path: str) -> dict:
    """The runner reads the registry row ITSELF — no caller booleans."""
    out = {"gate": "R0", "pass": False, "registry_path": registry_path}
    row, err = load_json(registry_path)
    if err:
        return dict(out, failure=f"registry unreadable: {err}")
    rows = row.get("cycles") if isinstance(row, dict) else row
    if not isinstance(rows, list):
        return dict(out, failure="registry malformed (no cycles array)")
    mine = [r for r in rows if isinstance(r, dict)
            and r.get("cycle_id") == CYCLE_ID]
    if not mine:
        return dict(out, failure=f"no registry row for {CYCLE_ID}")
    r = mine[0]
    out["row_stable_fields"] = {k: r.get(k) for k in
                                ("cycle_id", "branch", "head", "go_phrase",
                                 "go_phrase_state", "lifecycle", "phase")}

    branch, rc, err = git_out(["rev-parse", "--abbrev-ref", "HEAD"], worktree)
    if rc != 0:
        return dict(out, failure=f"git branch query failed: {err}")
    head, rc, err = git_out(["rev-parse", "HEAD"], worktree)
    if rc != 0:
        return dict(out, failure=f"git HEAD query failed: {err}")
    out["actual_branch"], out["actual_head"] = branch, head

    if r.get("branch") != branch:
        return dict(out, failure=f"registry branch {r.get('branch')!r} != "
                                 f"actual {branch!r}")
    if r.get("go_phrase") != CANONICAL_GO_PHRASE:
        return dict(out, failure="registry go_phrase is not byte-exact the "
                                 "canonical phrase")
    row_head = r.get("head")
    if row_head == head:
        out["head_check"] = "MATCH"
        out["pass"] = True
        return out
    # head differs: rc==0 => proper ancestor (disclosed N-1 lag character);
    # rc!=0 (not an ancestor, or the row head is not even a valid commit —
    # both are ROW evidence, i.e. control-plane divergence).
    _, rc, err = git_out(["merge-base", "--is-ancestor",
                          str(row_head), head], worktree)
    if rc == 0:
        out["head_check"] = "LAG_ANCESTOR"
        out["must_reconcile_before_go"] = True
        out["note"] = ("registry head is a proper git ancestor of the actual "
                       "HEAD — the disclosed N-1 head-lag character "
                       "(researchctl doctor HEAD_MISMATCH LOW); FAILS the "
                       "execution gate until the controller reconciles the "
                       "registry via its own tooling")
        return out
    out["head_check"] = "DIVERGED"
    out["failure"] = ("registry head is NOT an ancestor of the actual HEAD "
                      f"(git merge-base rc={rc}: {err or 'not an ancestor'}) "
                      "— proven control-plane divergence")
    return out


# --------------------------------------------------------------- R1 GO

def check_go(go_artifact: str, registry_row: dict | None,
             a7_digest_pin_sha: str, a7_digest_path: str) -> dict:
    out = {"gate": "R1", "pass": False, "artifact": go_artifact,
           "verbatim": None}
    if not Path(go_artifact).is_file():
        return dict(out, absent=True,
                    failure="GO artifact ABSENT — typed owner GO has not "
                            "been recorded at this cycle's gate (the expected "
                            "pre-GO state)")
    art, err = load_json(go_artifact)
    if err:
        return dict(out, failure=f"GO artifact unparseable: {err}")
    out["artifact_schema"] = art.get("schema")
    if art.get("cycle_id") != CYCLE_ID:
        return dict(out, failure=f"GO artifact cycle_id {art.get('cycle_id')!r}"
                                 f" != {CYCLE_ID!r}")
    k2 = art.get("key_2_owner_go")
    if not isinstance(k2, dict):
        return dict(out, failure="GO artifact missing key_2_owner_go object")
    verbatim = k2.get("verbatim")
    out["verbatim"] = verbatim
    if verbatim != CANONICAL_GO_PHRASE:  # BYTE equality: no trim, no case-fold
        return dict(out, paraphrase=True,
                    failure=f"GO verbatim is not byte-equal the canonical "
                            f"phrase (paraphrase/alias dies unconsumed): "
                            f"got {verbatim!r}")
    if k2.get("typed_by_owner") is not True:
        return dict(out, delegated=True,
                    failure="key_2_owner_go.typed_by_owner is not true — "
                            "owner-only law")
    if k2.get("typed_by") != "OWNER":
        return dict(out, delegated=True,
                    failure=f"key_2_owner_go.typed_by {k2.get('typed_by')!r} "
                            "!= 'OWNER' — delegation dies")
    for s in walk_strings(art):
        low = s.lower()
        for marker in DELEGATION_MARKERS:
            if marker in low:
                return dict(out, delegated=True,
                            failure=f"delegation marker {marker!r} present in "
                                    "the GO artifact — a delegated GO is not "
                                    "an owner GO")
    k1 = art.get("key_1_a7_prelaunch")
    if not isinstance(k1, dict):
        return dict(out, failure="GO artifact missing key_1_a7_prelaunch — "
                                 "cannot prove the GO is not early")
    if k1.get("sha256") != a7_digest_pin_sha:
        return dict(out, early=True,
                    failure=f"GO key_1 sha {str(k1.get('sha256'))[:16]}… is "
                            f"not the operative A7-v3 digest sha "
                            f"({a7_digest_pin_sha[:16]}… from {a7_digest_path}) "
                            "— an early/superseded GO dies unconsumed")
    if registry_row is not None:
        if registry_row.get("go_phrase") != CANONICAL_GO_PHRASE:
            return dict(out, failure="registry go_phrase is inconsistent with "
                                     "the GO artifact")
    out["pass"] = True
    return out


# --------------------------------------------------------------- R2 auth

def check_auth(a7_md_path: str, a7_digest_path: str, contract: dict) -> dict:
    out = {"gate": "R2", "pass": False}
    pins = {p["name"]: p for p in contract["pins"]}
    for name, path in (("a7_prelaunch_v3_md", a7_md_path),
                       ("a7_prelaunch_v3_digest", a7_digest_path)):
        got = sha256_file(path)
        want = pins[name]["sha256"]
        out[f"sha_{name}"] = {"expected": want, "actual": got,
                              "match": got == want}
        if got != want:
            return dict(out, failure=f"{name} sha mismatch/missing at {path}")
    digest, err = load_json(a7_digest_path)
    if err:
        return dict(out, failure=f"A7 digest unreadable: {err}")
    if digest.get("cycle_id") != CYCLE_ID:
        return dict(out, failure="A7 digest cycle_id mismatch")
    verdict = digest.get("verdict")
    tally = digest.get("severity_tally", {})
    want_verdict = contract["embedded_laws"]["a7_v3_required_verdict"]
    max_unres = contract["embedded_laws"]["a7_v3_max_unresolved"]
    out["verdict"], out["severity_tally"] = verdict, tally
    unresolved = sum(tally.get(k, 0) for k in max_unres)
    out["unresolved_critical_high_medium"] = unresolved
    if verdict != want_verdict:
        return dict(out, failure=f"A7-v3 verdict {verdict!r} != "
                                 f"{want_verdict!r} (R2 non-inheritance: v1/v2 "
                                 "verdicts are history)")
    if unresolved != 0:
        return dict(out, failure=f"A7-v3 has {unresolved} unresolved "
                                 "CRITICAL/HIGH/MEDIUM")
    out["pass"] = True
    return out


# --------------------------------------------------------------- R4 drift


def live_operative_pins(contract: dict) -> tuple:
    """PIN-ENFORCE law 1 — the ONE live-operative-pin law (closes F-V1/F-V2).

    live    = the base pins PLUS every ``v2_*_addendum``'s new_pins, deduped
              BY ARTIFACT PATH with the LATER addendum winning (a re-pinned
              artifact's newest row IS the live law; earlier rows of the
              same path are demoted to history). Every entry carries
              ``_source`` (``base`` or the addendum key) for diagnostics.
    history = every demoted row PLUS the contract's explicit ``*_HISTORY``
              rows — EVIDENCE ONLY: never a gate input, never a live-file
              check, never able to flip a verdict.

    Returns (live, history). R4 diagnostics (F-V1) split these cleanly so a
    live addendum pin and its superseded twins are BOTH visible with no
    name clobber, and the execution gate, the sandbox path resolver and the
    post-acquire TOCTOU re-verify all consume the SAME live list.
    """
    addendum_keys = sorted(k for k in contract
                           if k.startswith("v2_") and k.endswith("_addendum"))
    by_path: dict = {}
    history: list = []

    def demote(row: dict, note: str) -> None:
        h = dict(row)
        h["_status"] = "HISTORY_SUPERSEDED"
        h["_supersedes_note"] = note
        history.append(h)

    for source in ["base"] + addendum_keys:
        group = (contract["pins"] if source == "base"
                 else contract[source].get("new_pins", []))
        for pin in group:
            path = pin["path"]
            if path in by_path:
                old = by_path.pop(path)
                demote(old, f"same artifact re-pinned by a later addendum "
                            f"(now pinned as {pin['name']}) — the LATER row "
                            f"is the live law; this row is recorded, never "
                            f"live-checked")
            row = dict(pin)
            row["_source"] = source
            by_path[path] = row

    live = []
    for pin in by_path.values():
        if pin["name"].endswith("_HISTORY"):
            demote(pin, "explicit contract HISTORY row — recorded as "
                        "evidence, never a live-file check")
        else:
            live.append(pin)
    return live, history


def operative_pins(contract: dict) -> list:
    """Compatibility wrapper: the live pins followed by the history rows
    (history entries carry ``_status`` starting with HISTORY). New code
    MUST consume live_operative_pins() so history stays evidence-only."""
    live, history = live_operative_pins(contract)
    return live + history

def check_drift(contract: dict, worktree: str, paths: dict) -> dict:
    """Re-hash every pin from the given (default: real) paths + freeze
    round-trips. Hash-only — never a parquet parse, never a compute.

    PIN-ENFORCE law 5 (F-V1): the output splits ``pins_live`` (the gate
    inputs — name -> {path, expected, actual, match, source_addendum}) from
    ``pins_history`` (evidence-only — name -> {expected, supersedes_note,
    entries[]}). A live addendum pin and its superseded twins are BOTH
    visible with no name clobber. Missing/unreadable live pins fail closed
    with the pin named (law 6). The legacy merged ``pins`` view is kept for
    older consumers; live rows win it."""
    out = {"gate": "R4", "pass": False, "pins_live": {}, "pins_history": {},
           "pins": {}, "round_trips": {}}
    live, history = live_operative_pins(contract)
    mismatches = []
    for pin in history:
        name = pin["name"]
        entry = {"expected": pin["sha256"],
                 "source_addendum": pin.get("_source", "base"),
                 "supersedes_note": pin.get("_supersedes_note")
                 or "superseded — evidence only, never a live-file check"}
        if name == "a7_adjudicated_freeze_bytes_HISTORY":
            entry["supersedes_note"] = (
                "A7-v3-adjudicated bytes, superseded by the operative "
                "0b0d269a… via the two disclosed display-only "
                "corrections (F-1 + VP3-L1); recorded as history, "
                "not a live-file check")
        hist = out["pins_history"].setdefault(name, {"entries": []})
        hist["entries"].append(entry)
        hist["expected"] = entry["expected"]
        hist["supersedes_note"] = entry["supersedes_note"]
        hist["source_addendum"] = entry["source_addendum"]
        out["pins"][name] = dict(entry, status="HISTORY")
    for pin in live:
        name = pin["name"]
        if name in out["pins_live"]:
            # a contract defect, not a diagnostic choice: two live rows
            # sharing a name would make gate facts ambiguous — fail closed
            mismatches.append(f"duplicate_live_pin_name:{name}")
            out["pins_live"][name] = {
                "path": None, "expected": None, "actual": None,
                "match": False,
                "source_addendum": pin.get("_source", "base"),
                "error": "duplicate live pin name — contract defect"}
        else:
            path = paths.get(f"pin:{name}") or os.path.join(worktree,
                                                            pin["path"])
            got = sha256_file(path)
            ok = got is not None and got == pin["sha256"]
            out["pins_live"][name] = {"path": path,
                                      "expected": pin["sha256"],
                                      "actual": got, "match": ok,
                                      "source_addendum":
                                      pin.get("_source", "base")}
            if got is None:
                out["pins_live"][name]["error"] = \
                    "pin file MISSING or UNREADABLE — fail closed"
        out["pins"][name] = out["pins_live"][name]  # legacy view; live wins
        if not out["pins_live"][name]["match"]:
            mismatches.append(name)

    fz, err = load_json(paths["freeze"])
    if err:
        mismatches.append("freeze_parse")
        out["round_trips"]["freeze_parse"] = err
    else:
        want_ids = contract["embedded_laws"]["identity_ids"]
        try:
            live_ids = [x["id"] for x in
                        fz["identity_table"]["embedded"]["identities"]]
        except (KeyError, TypeError) as exc:
            live_ids = None
            out["round_trips"]["identity_ids"] = f"unparseable: {exc}"
        ids_ok = live_ids == want_ids
        out["round_trips"]["identity_ids_byte_exact"] = ids_ok
        if not ids_ok:
            mismatches.append("identity_ids")

        excl_sha_field = (fz.get("exclude_list") or {}).get("sha256")
        excl_actual = sha256_file(paths["exclude"])
        excl_ok = excl_sha_field is not None and \
            excl_sha_field == excl_actual
        out["round_trips"]["exclude_list_sha_round_trip"] = excl_ok
        if not excl_ok:
            mismatches.append("exclude_round_trip")

        dl = fz.get("donor_law") or {}
        sup = dl.get("supersedes") or {}
        carry_pin = next(p["sha256"] for p in contract["pins"]
                         if p["name"] == "donor_law_carryover_HISTORY")
        donor_ok = ("A7-SPEC-M5" in json.dumps(dl, ensure_ascii=False)
                    and str(sup.get("path", ""))
                    .endswith("DONOR_LAW_CARRYOVER.md")
                    and sup.get("sha256") == carry_pin)
        out["round_trips"]["donor_law_flag_based_carryover_withdrawn"] = \
            donor_ok
        if not donor_ok:
            mismatches.append("donor_law")

        try:
            cce = fz["cost_contract"]["embedded"]
            tbl = cce["effective_cost_table_es"]
            want = contract["embedded_laws"]["cost_contract"]
            cost_ok = (str(cce.get("chosen_variant", "")).startswith("A")
                       and tbl["all_in_per_side"] == want["all_in_per_side_usd"]
                       and tbl["round_trip"] == want["round_trip_usd"]
                       and tbl["fees_per_side"] == want["fees_per_side_usd"])
            out["round_trips"]["cost_variant_A"] = cost_ok
        except (KeyError, TypeError) as exc:
            cost_ok = False
            out["round_trips"]["cost_variant_A"] = f"unparseable: {exc}"
        if not cost_ok:
            mismatches.append("cost_contract")

        fz_text = json.dumps(fz, ensure_ascii=False)
        ban_ok = all(str(v) in fz_text for v in
                     contract["embedded_laws"]["cost_contract"]
                     ["forbidden_retired_values"])
        out["round_trips"]["forbidden_values_ban_present"] = ban_ok
        if not ban_ok:
            mismatches.append("forbidden_values_law")

        ev = fz.get("fold_structure") or {}
        folds_field = ev.get("folds")
        fold_ids = (sorted(folds_field.keys())
                    if isinstance(folds_field, dict)
                    else sorted(x.get("fold_id", x.get("fold"))
                                for x in (folds_field or [])))
        eval_ok = (ev.get("total_eval_sessions")
                   == contract["embedded_laws"]["eval_sessions_total"]
                   and fold_ids == sorted(contract["embedded_laws"]["folds"]))
        out["round_trips"]["eval_surface_2921_F1_F4"] = eval_ok
        if not eval_ok:
            mismatches.append("eval_surface")

        op_sha = next(p["sha256"] for p in contract["pins"]
                      if p["name"] == "operative_freeze_v3")
        pin_md = Path(paths["pin:operative_freeze_pin_md"])
        pin_text = pin_md.read_text(encoding="utf-8") if pin_md.is_file() \
            else ""
        pin_ok = op_sha in pin_text
        out["round_trips"]["operative_pin_carries_operative_sha"] = pin_ok
        if not pin_ok:
            mismatches.append("operative_freeze_pin")

    tl_sha = sha256_file(paths["trial_ledger_module"])
    tl_want = next(p["sha256"] for p in contract["pins"]
                   if p["name"] == "trial_ledger_fixed")
    out["round_trips"]["trial_ledger_fixed_sha"] = tl_sha == tl_want
    if tl_sha != tl_want:
        mismatches.append("trial_ledger_fixed")

    out["mismatched_pins"] = sorted(set(mismatches))
    out["pass"] = not mismatches
    return out


# --------------------------------------------------------------- R5 pins

def check_adjudication(da45_json_path: str) -> dict:
    out = {"gate": "R5", "pass": False, "path": da45_json_path}
    d, err = load_json(da45_json_path)
    if err:
        return dict(out, failure=f"da45_decisions unreadable: {err}")
    pins = {p.get("id"): p for p in d.get("pins", []) if isinstance(p, dict)}
    statuses = {}
    for pid in ("D-A4", "D-A5"):
        p = pins.get(pid) or {}
        statuses[pid] = p.get("authority_verdict")
        if p.get("authority_verdict") != "AUTHORITY_EXISTS":
            return dict(out, pins_status="UNRESOLVED",
                        failure=f"{pid} authority_verdict "
                                f"{p.get('authority_verdict')!r} != "
                                "'AUTHORITY_EXISTS' — adjudication not "
                                "standing")
    out["pins_status"] = "ADJUDICATED_AUTHORITY_EXISTS"
    out["authority_verdicts"] = statuses
    out["pass"] = True
    return out


# ------------------------------------------------- PIN-ENFORCE enforcement
#
# Both enforcement sites are module-level so the test suite can drive them
# at the enforcement site (behavioral proof), while main() wires them into
# the production path unchanged.

def build_reverify_closure(contract: dict, worktree: str, registry_path: str,
                           paths: dict, pins_live: list, go_resolved: str,
                           registry_row: dict | None, a7_digest_sha: str,
                           a7_digest_path: str):
    """PIN-ENFORCE law 3 — the post-acquire TOCTOU guard.

    Builds the closure the executor calls AFTER the heavy lock is acquired.
    It re-verifies the GO artifact, the registry head and the FULL LIVE pin
    set (path + sha taken from the contract, resolved the SAME way
    check_drift resolves them: sandbox paths dict first, then the
    worktree-relative contract path). This replaces the former base-only
    hardcoded scored_executor.TOCTOU_PIN_NAMES tuple (removed; F-V2 root
    cause 2). Missing/unreadable pins are named drifts (fail closed)."""
    def reverify_authority() -> list:
        drifts = []
        go2 = check_go(go_resolved, registry_row, a7_digest_sha,
                       a7_digest_path)
        if not go2.get("pass"):
            drifts.append(f"GO re-verify failed: {go2.get('failure')}")
        reg2 = check_registry(worktree, registry_path)
        if not reg2.get("pass") or reg2.get("head_check") != "MATCH":
            drifts.append(f"registry re-verify failed: "
                          f"head={reg2.get('head_check')} "
                          f"err={reg2.get('failure')}")
        for pin in pins_live:
            name = pin["name"]
            path = paths.get(f"pin:{name}") or os.path.join(worktree,
                                                            pin["path"])
            got = sha256_file(path)
            if got is None:
                drifts.append(f"pin {name} MISSING/UNREADABLE post-acquire "
                              f"at {path}")
            elif got != pin["sha256"]:
                drifts.append(f"pin {name} drift post-acquire (sha mismatch "
                              f"at {path})")
        return drifts

    return reverify_authority


def self_integrity_violations(contract: dict, worktree: str,
                              runner_file: str, executor_file: str) -> list:
    """PIN-ENFORCE law 4 — self-integrity binding at the execution boundary.

    The bytes ACTUALLY imported/executed (the runner's own ``__file__`` and
    ``scored_executor.__file__``) must each be the live contract pin of
    their artifact: PATH equality (realpath — catches path tricks and
    modules imported from a shadow/stale location) AND sha equality
    (catches replaced bytes behind a live path). A module the contract does
    not pin at its resolved path is itself a violation — fail closed.
    Module identities come from ``__file__``; their pins are found BY
    PATH — no pin name is hardcoded."""
    live, _history = live_operative_pins(contract)
    by_rel = {}
    for pin in live:
        by_rel.setdefault(os.path.normpath(pin["path"]).replace("\\", "/"),
                          pin)
    violations = []
    wt_abs = os.path.realpath(os.path.abspath(worktree))
    for label, module_file in (("scored_runner", runner_file),
                               ("scored_executor", executor_file)):
        absf = os.path.realpath(os.path.abspath(module_file))
        rel = os.path.normpath(os.path.relpath(absf, wt_abs)).replace(
            "\\", "/")
        pin = by_rel.get(rel)
        if pin is None:
            violations.append(
                f"{label}: executing module {absf} is not pinned by the "
                f"live contract at its resolved path ({rel}) — fail closed")
            continue
        got = sha256_file(absf)
        if got is None:
            violations.append(f"{label}: executing module bytes unreadable "
                              f"at {absf}")
        elif got != pin["sha256"]:
            violations.append(
                f"{label}: executing module sha "
                f"{(got or '')[:12]}… != live pin {pin['sha256'][:12]}… "
                f"for {pin['path']} — stale import or replaced bytes")
        expected = os.path.realpath(os.path.join(wt_abs, pin["path"]))
        if absf != expected:
            violations.append(f"{label}: imported module path {absf} != "
                              f"pinned artifact path {expected} "
                              f"(path trick)")
    return violations


# ------------------------------------------------------------- CLI / main

DEFAULT_RELS = {
    "pin:operative_freeze_v3": "research/control/FUTURES-ES-PB1-V1/final/selection_freeze_v3.json",
    "pin:operative_freeze_pin_md": "research/control/FUTURES-ES-PB1-V1/final/OPERATIVE_FREEZE_PIN.md",
    "pin:exclude_list_v3": "research/control/FUTURES-ES-PB1-V1/final/exclude_list_v3.json",
    "pin:machinery_builder_v3": "research/control/FUTURES-ES-PB1-V1/final/dryrun_builder_v3.py",
    "pin:build_freeze_v3": "research/control/FUTURES-ES-PB1-V1/final/build_freeze_v3.py",
    "pin:make_builder_v3": "research/control/FUTURES-ES-PB1-V1/final/make_builder_v3.py",
    "pin:a7_prelaunch_v3_md": "research/control/FUTURES-ES-PB1-V1/a7_v3/A7_PRELAUNCH_V3.md",
    "pin:a7_prelaunch_v3_digest": "research/control/FUTURES-ES-PB1-V1/a7_v3/a7_prelaunch_v3_digest.json",
    "pin:spec_pb1_es": "research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md",
    "pin:pinned_panel_es_1m_outright": "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet",
    "pin:held_chain_es_chain_T5": "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_chain_T5.parquet",
    "pin:identity_table_source": "research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/identity_table_24.json",
    "pin:prego_repair_recorded": "research/control/FUTURES-ES-PB1-V1/auth/PREGO_REPAIR_RECORDED.json",
    "pin:holiday_pdf_equity_evidence": "research/control/FUTURES-ES-PB1-V1/holiday/pdf_equity_evidence_2011_2015.json",
    "pin:da45_decision_packet": "research/control/FUTURES-ES-PB1-V1/pins2/DA45_DECISION_PACKET.md",
    "pin:da45_decisions": "research/control/FUTURES-ES-PB1-V1/pins2/da45_decisions.json",
    "pin:fail_donor_violation_record": "research/control/FUTURES-ES-PB1-V1/repair/FAIL_DONOR_VIOLATION.md",
    "pin:donor_law_carryover_HISTORY": "research/control/FUTURES-ES-PB1-V1/repair/DONOR_LAW_CARRYOVER.md",
    "pin:trial_ledger_fixed": "research/control/FUTURES-ES-PB1-V1/gate6/trial_ledger.py",
}

# named CLI overrides -> the pin key they replace + the alias key check_drift uses
OVERRIDE_KEYS = {
    "freeze": ("pin:operative_freeze_v3", "freeze"),
    "exclude": ("pin:exclude_list_v3", "exclude"),
    "builder": ("pin:machinery_builder_v3", None),
    "a7-md": ("pin:a7_prelaunch_v3_md", None),
    "a7-digest": ("pin:a7_prelaunch_v3_digest", None),
    "spec": ("pin:spec_pb1_es", None),
    "panel": ("pin:pinned_panel_es_1m_outright", None),
    "chain": ("pin:held_chain_es_chain_T5", None),
    "idtable": ("pin:identity_table_source", None),
    "da45-json": ("pin:da45_decisions", None),
}


DEFAULT_LEDGER_REL = ("research/control/FUTURES-ES-PB1-V1/gate6/ledger/"
                      "trial_ledger.jsonl")
DEFAULT_GO_REL = ("research/control/FUTURES-ES-PB1-V1/auth/"
                  "GO_RECORDED.json")


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="FUTURES-ES-PB1-V1 gate-6 scored runner (contract v2 + "
                    "v2.1 real execution path; pre-GO: refuses without the "
                    "typed owner GO artifact)")
    ap.add_argument("--preflight-only", action="store_true",
                    help="read-only wiring check; performs zero writes "
                         "except the optional --manifest-out; never computes "
                         "outcomes")
    ap.add_argument("--manifest-out",
                    help="write the deterministic preflight manifest JSON "
                         "here (no wall-clock fields; twin-reproducible)")
    ap.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    ap.add_argument("--worktree", default=DEFAULT_WORKTREE)
    ap.add_argument("--registry-path", default=ROOT_REGISTRY)
    ap.add_argument("--go-artifact",
                    default="research/control/FUTURES-ES-PB1-V1/auth/"
                            "GO_RECORDED.json",
                    help="GO artifact path (absolute, or worktree-relative)")
    ap.add_argument("--ledger-path",
                    default="research/control/FUTURES-ES-PB1-V1/gate6/ledger/"
                            "trial_ledger.jsonl",
                    help="24-slot ledger (execution mode only; "
                         "worktree-relative or absolute)")
    ap.add_argument("--refusal-record-path", default=None,
                    help="refusal_record.json path (default: next to ledger)")
    ap.add_argument("--lock-runtime-dir", default=None,
                    help="heavy-lock runtime dir override (tests only; "
                         "default = canonical machine-wide runtime)")
    ap.add_argument("--trial-ledger-module-path", default=None,
                    help="override path of gate6/trial_ledger.py (drift "
                         "checks re-hash THIS path against the pin)")
    ap.add_argument("--sandbox-root", default=None,
                    help="SYNTHETIC-SANDBOX root for test fixtures + fault "
                         "injection; when set, ALL authority inputs and "
                         "outputs must resolve under this directory (the "
                         "sandbox cannot touch the real ledger, registry or "
                         "machine-wide lock). Default (no flag) = production "
                         "paths + real authority only")
    ap.add_argument("--run-label", default="run",
                    help="run label; the execution run dir is "
                         "<sandbox-root|ledger parent>/runs/<label>")
    ap.add_argument("--sandbox-fault", default=None,
                    help=argparse.SUPPRESS)  # sandbox-only fault injection
    for name in OVERRIDE_KEYS:
        ap.add_argument(f"--{name}-path", default=None,
                        help=f"override path for {name} (default: the "
                             f"contract-pinned real path)")
    return ap


def sandbox_isolation_violations(resolved: dict, sroot: str) -> list[str]:
    """Law (c)/(e): in sandbox mode EVERY authority/output path must resolve
    under the sandbox root. Returns the violating keys."""
    real = os.path.realpath(sroot)

    def inside(p):
        rp = os.path.realpath(os.path.abspath(p))
        return rp == real or rp.startswith(real + os.sep)

    return sorted(k for k, p in resolved.items() if p and not inside(p))


def production_authority_violations(args, go_resolved: str,
                                    ledger_resolved: str) -> list[str]:
    """Law (d): production-default scored execution runs ONLY against the
    unoverridden real authority paths — any override that reaches the
    execution branch is a test bypass and dies here (refusals that fail
    gates BEFORE this point are unaffected)."""
    v = []
    if os.path.abspath(args.contract) != os.path.abspath(str(DEFAULT_CONTRACT)):
        v.append("contract override")
    if os.path.abspath(args.registry_path) != os.path.abspath(ROOT_REGISTRY):
        v.append("registry-path override")
    if os.path.abspath(go_resolved) != \
            os.path.abspath(os.path.join(args.worktree, DEFAULT_GO_REL)):
        v.append("go-artifact override")
    if os.path.abspath(ledger_resolved) != \
            os.path.abspath(os.path.join(args.worktree, DEFAULT_LEDGER_REL)):
        v.append("ledger-path override")
    if args.lock_runtime_dir is not None:
        v.append("lock-runtime-dir override (lock bypass)")
    if args.refusal_record_path is not None:
        v.append("refusal-record-path override")
    if args.trial_ledger_module_path is not None:
        v.append("trial-ledger-module-path override")
    for name in OVERRIDE_KEYS:
        if getattr(args, f"{name.replace('-', '_')}_path") is not None:
            v.append(f"{name}-path override")
    return v


def apply_path_overrides(paths: dict, args) -> dict:
    """Apply the named CLI override paths to a resolved paths dict (the
    alias/keys logic is shared by the production and sandbox resolutions)."""
    for name, val in (("freeze", args.freeze_path),
                      ("exclude", args.exclude_path),
                      ("builder", args.builder_path),
                      ("a7-md", args.a7_md_path),
                      ("a7-digest", args.a7_digest_path),
                      ("spec", args.spec_path),
                      ("panel", args.panel_path),
                      ("chain", args.chain_path),
                      ("idtable", args.idtable_path),
                      ("da45-json", args.da45_json_path),
                      ("trial_ledger_module",
                       args.trial_ledger_module_path)):
        if val:
            pin_key = OVERRIDE_KEYS.get(name, (None, None))[0] or \
                ({"trial_ledger_module": "pin:trial_ledger_fixed"}
                 .get(name))
            paths[pin_key] = val
            if name in ("freeze", "exclude"):
                paths[name] = val
            if name == "trial_ledger_module":
                paths["trial_ledger_module"] = val
    return paths


def resolve_paths(args) -> dict:
    paths = {k: os.path.join(args.worktree, rel)
             for k, rel in DEFAULT_RELS.items()}
    paths["freeze"] = paths["pin:operative_freeze_v3"]
    paths["exclude"] = paths["pin:exclude_list_v3"]
    paths["trial_ledger_module"] = paths["pin:trial_ledger_fixed"]
    return apply_path_overrides(paths, args)


def write_manifest(args, manifest: dict) -> None:
    if not args.manifest_out:
        return
    mp = Path(args.manifest_out)
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(
        json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False)
        + "\n", encoding="utf-8")


def resolve_sandbox_paths(sroot: str, contract: dict) -> dict:
    """Sandbox-mode authority paths: every LIVE operative pin resolves under
    the sandbox root using the SANDBOX contract's own pin paths (mirrored
    layout). History rows are evidence-only — never resolved, never checked."""
    live, _history = live_operative_pins(contract)
    paths = {}
    for pin in live:
        paths[f"pin:{pin['name']}"] = os.path.join(sroot, pin["path"])
    paths["freeze"] = paths["pin:operative_freeze_v3"]
    paths["exclude"] = paths["pin:exclude_list_v3"]
    paths["trial_ledger_module"] = paths["pin:trial_ledger_fixed"]
    return paths


def _refuse_sandbox_isolation(args, sroot: str, violations: list[str]) -> int:
    """Isolation refusal: recorded ONLY under the sandbox (the violated
    real-root path is never written)."""
    detail = {"gate": "SANDBOX-ISOLATION",
              "law": "--sandbox-root must not be combined with any real-root "
                     "authority path; a sandbox run resolves ALL authority "
                     "inputs/outputs under the sandbox root only",
              "violations": violations}
    sys.path.insert(0, os.path.join(args.worktree, "research"))
    sys.path.insert(0, str(RUNNER_DIR.parent))
    ledger_error, recorded = None, None
    ledger_path = os.path.join(sroot, "ledger", "trial_ledger.jsonl")
    try:
        import trial_ledger  # noqa: E402
        ids = load_json(DEFAULT_CONTRACT)[0]["embedded_laws"]["identity_ids"]
        led = trial_ledger.TrialLedger(ledger_path, ids)
        recorded = led.record_refusal(
            "REFUSED_CONTROL_STATE_DRIFT",
            note=json.dumps(dict(detail, sandbox_stamp="SYNTHETIC-SANDBOX"),
                            sort_keys=True, ensure_ascii=False)[:2000])
    except Exception as exc:  # noqa: BLE001
        ledger_error = str(exc)[:400]
    try:
        Path(sroot).mkdir(parents=True, exist_ok=True)
        (Path(sroot) / "refusal_record.json").write_text(json.dumps(
            {"schema": "futures_es_pb1_v1/refusal_record@2",
             "cycle_id": CYCLE_ID, "reason": "REFUSED_CONTROL_STATE_DRIFT",
             "detail": detail, "sandbox_stamp": "SYNTHETIC-SANDBOX",
             "ledger_row": recorded, "ledger_error": ledger_error},
            indent=1, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8")
    except OSError as exc:
        ledger_error = ledger_error or f"refusal_record write failed: {exc}"
    print(f"REFUSED: SANDBOX-ISOLATION — {json.dumps(detail, ensure_ascii=False)}",
          file=sys.stderr)
    if ledger_error:
        print(f"TECHNICAL: isolation refusal recording failed: {ledger_error}",
              file=sys.stderr)
        return EXIT_TECHNICAL
    return EXIT_REFUSED


def sandbox_setup(args):
    """Sandbox-mode resolution + isolation validation (law a/c/e).

    Returns (sroot, violations, setup_error). Mutates args with the sandbox
    defaults ONLY when the isolation check passes."""
    sroot = os.path.realpath(os.path.abspath(args.sandbox_root))
    if args.preflight_only:
        return sroot, ["preflight-only mode"], (
            "--preflight-only is the REAL-wiring read-only mode and cannot "
            "be combined with --sandbox-root")
    real_default_ledger = os.path.join(args.worktree, DEFAULT_LEDGER_REL)
    args_ledger_abs = args.ledger_path \
        if os.path.isabs(args.ledger_path) \
        else os.path.join(args.worktree, args.ledger_path)
    ledger_resolved = args_ledger_abs \
        if args_ledger_abs != real_default_ledger \
        else os.path.join(sroot, "ledger", "trial_ledger.jsonl")
    resolved = {
        "contract": args.contract,
        "registry-path": args.registry_path,
        "go-artifact": args.go_artifact if os.path.isabs(args.go_artifact)
        else os.path.join(args.worktree, args.go_artifact),
        "ledger-path": ledger_resolved,
        "run-root": os.path.join(sroot, "runs", args.run_label),
    }
    if args.lock_runtime_dir:
        resolved["lock-runtime-dir"] = args.lock_runtime_dir
    if args.refusal_record_path:
        resolved["refusal-record-path"] = args.refusal_record_path
    if args.manifest_out:
        resolved["manifest-out"] = args.manifest_out
    if args.trial_ledger_module_path:
        resolved["trial-ledger-module-path"] = args.trial_ledger_module_path
    for name in OVERRIDE_KEYS:
        val = getattr(args, f"{name.replace('-', '_')}_path")
        if val:
            resolved[f"{name}-path"] = val
    violations = sandbox_isolation_violations(resolved, sroot)
    if violations:
        return sroot, violations, None
    # sandbox defaults: everything the executor needs lives in the box
    args.ledger_path = ledger_resolved
    if not args.lock_runtime_dir:
        args.lock_runtime_dir = os.path.join(sroot, "heavy_runtime")
    return sroot, [], None


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)

    # ---- SANDBOX ISOLATION LAW (a/c/e) — resolve + validate FIRST
    sandbox_mode = args.sandbox_root is not None
    sroot = None
    if sandbox_mode:
        try:
            sroot, violations, setup_error = sandbox_setup(args)
        except Exception as exc:  # noqa: BLE001 — a broken sandbox setup is
            # a technical failure, never a leaked traceback
            print(f"TECHNICAL: sandbox setup failed: {exc!r}", file=sys.stderr)
            return EXIT_TECHNICAL
        if setup_error:
            print(f"REFUSED: {setup_error}", file=sys.stderr)
            return EXIT_REFUSED
        if violations:
            return _refuse_sandbox_isolation(args, sroot, violations)

    contract, err = load_json(args.contract)
    if err:
        print(f"TECHNICAL: launch contract unreadable: {err}", file=sys.stderr)
        return EXIT_TECHNICAL
    if contract.get("schema") != "futures_es_pb1_v1/launch_contract@2":
        print("TECHNICAL: contract schema is not launch_contract@2",
              file=sys.stderr)
        return EXIT_TECHNICAL
    if contract.get("go_authority", {}).get(
            "canonical_go_phrase") != CANONICAL_GO_PHRASE:
        print("TECHNICAL: contract canonical GO phrase != runner canonical "
              "phrase", file=sys.stderr)
        return EXIT_TECHNICAL

    # governance + the FIXED trial ledger on sys.path
    sys.path.insert(0, os.path.join(args.worktree, "research"))
    sys.path.insert(0, str(RUNNER_DIR.parent))  # gate6/ for trial_ledger
    try:
        import trial_ledger  # noqa: E402
    except ImportError as exc:
        print(f"TECHNICAL: cannot import gate6/trial_ledger.py: {exc}",
              file=sys.stderr)
        return EXIT_TECHNICAL
    if trial_ledger.CANONICAL_GO_PHRASE != CANONICAL_GO_PHRASE:
        print("TECHNICAL: trial_ledger.CANONICAL_GO_PHRASE mismatch",
              file=sys.stderr)
        return EXIT_TECHNICAL

    pins_live, pins_history = live_operative_pins(contract)
    pins_by_name = {p["name"]: p for p in pins_live}
    if sandbox_mode:
        paths = apply_path_overrides(
            resolve_sandbox_paths(sroot, contract), args)
    else:
        paths = resolve_paths(args)

    manifest = {
        "schema": "futures_es_pb1_v1/runner_preflight@2",
        "cycle_id": CYCLE_ID,
        "contract": args.contract,
        "contract_sha256": sha256_file(args.contract),
        "worktree": args.worktree,
        "preflight_only": bool(args.preflight_only),
        "determinism_note": "no wall-clock fields; two runs are "
                            "byte-identical given stable machine state",
    }

    # ---- R0 registry (the runner reads it ITSELF)
    reg = check_registry(args.worktree, args.registry_path)
    manifest["registry_check"] = reg
    registry_row = reg.get("row_stable_fields")

    # ---- R2 auth
    auth = check_auth(paths["pin:a7_prelaunch_v3_md"],
                      paths["pin:a7_prelaunch_v3_digest"], contract)
    manifest["auth_check"] = auth

    # ---- R3 lock (canonical decision tree, injectable runtime dir)
    lock = lock_inspect(args.lock_runtime_dir)
    manifest["lock_check"] = {"verdict": lock["verdict"],
                              "reason": lock["reason"],
                              "runtime_dir": args.lock_runtime_dir or
                              "canonical machine runtime"}

    # ---- R4 drift
    drift = check_drift(contract, args.worktree, paths)
    manifest["drift_check"] = drift

    # ---- R5 adjudication
    adj = check_adjudication(paths["pin:da45_decisions"])
    manifest["adjudication_check"] = adj

    # ---- R1 GO (registry consistency + operative A7-v3 digest binding)
    go = check_go(
        args.go_artifact if os.path.isabs(args.go_artifact) else
        os.path.join(args.worktree, args.go_artifact),
        registry_row,
        pins_by_name["a7_prelaunch_v3_digest"]["sha256"],
        paths["pin:a7_prelaunch_v3_digest"])
    manifest["go_check"] = go

    # ---- the FIXED RefusalGate decides R1–R5
    lock_state = {"HELD_PROVEN": "BUSY", "FREE_PROVEN": "FREE_PROVEN",
                  "CONTROL_STATE_DRIFT": "DRIFT"}.get(lock["verdict"], "DRIFT")
    input_sha_matches = {
        # PIN-ENFORCE law 2: built from the FULL LIVE pin set (base + every
        # addendum; NO hardcoded names) — every live pin name maps to its
        # match, so addendum drift reaches the gate facts too.
        name: bool(row.get("match"))
        for name, row in drift["pins_live"].items()}
    for k, v in drift["round_trips"].items():
        input_sha_matches[f"round_trip:{k}"] = v is True
    facts = {
        "go_phrase": go.get("verbatim"),
        "go_phrase_owner_typed": bool(go.get("pass")),
        "registry_go_phrase": (registry_row or {}).get("go_phrase"),
        "a7_verdict": auth.get("verdict"),
        "a7_high_critical": auth.get("unresolved_critical_high_medium", 99),
        "lock_state": lock_state,
        "input_sha_matches": input_sha_matches,
        "pins_status": adj.get("pins_status", "UNRESOLVED"),
    }
    allowed, reason, detail = trial_ledger.RefusalGate().evaluate(facts)
    manifest["refusal_gate"] = {"allowed": allowed, "reason": reason,
                                "detail": detail}

    # ---- R0 folds in ahead of the gate's verdict (registry law)
    if not reg.get("pass") and reg.get("failure"):
        allowed, reason = False, "REFUSED_CONTROL_STATE_DRIFT"
        detail = {"gate": "R0", "registry_failure": reg.get("failure"),
                  "head_check": reg.get("head_check")}
    elif reg.get("head_check") in ("LAG_ANCESTOR", "DIVERGED"):
        allowed, reason = False, "REFUSED_CONTROL_STATE_DRIFT"
        detail = {"gate": "R0", "head_check": reg.get("head_check"),
                  "row_head": (registry_row or {}).get("head"),
                  "actual_head": reg.get("actual_head"),
                  "is_ancestor": reg.get("head_check") == "LAG_ANCESTOR",
                  "law": "execution requires row.head == actual HEAD; an "
                         "ancestor-lag is reconciled by the controller via "
                         "the registry's own tooling before scored execution"}
    elif allowed and not drift.get("pass"):
        # PIN-ENFORCE law 2 (closes F-V2): check_drift.pass is ITSELF an
        # enforcement input at the execution gate — when every other gate
        # would allow the run, a false drift REFUSES REGARDLESS of which
        # pin mismatched (base or addendum) and regardless of what the
        # RefusalGate facts carried. The gate facts are NOT the only path
        # to REFUSED_DRIFT.
        allowed, reason = False, "REFUSED_DRIFT"
        detail = {"gate": "R4-drift-failclosed",
                  "law": "the execution gate refuses whenever check_drift "
                         "reports pass=false — base and addendum pins "
                         "alike; the RefusalGate facts are not the only "
                         "enforcement path",
                  "mismatched_pins": drift.get("mismatched_pins")}
    # merge the specific check diagnostics into the recorded refusal detail
    # (the generic gate detail alone would lose the WHY for forensics)
    if not allowed:
        detail = dict(detail or {})
        if reason == "REFUSED_NO_GO" and not go.get("pass"):
            detail["go_failure"] = go.get("failure")
        elif reason == "REFUSED_NO_AUTH" and not auth.get("pass"):
            detail["auth_failure"] = auth.get("failure")
        elif reason == "REFUSED_DRIFT":
            detail["mismatched_pins"] = drift.get("mismatched_pins")
        elif reason == "REFUSED_PINS_UNRESOLVED" and not adj.get("pass"):
            detail["adjudication_failure"] = adj.get("failure")
    manifest["gate_verdict"] = {"allowed": allowed, "reason": reason,
                                "detail": detail,
                                "r0_head_check": reg.get("head_check"),
                                "r0_pass": bool(reg.get("pass"))}

    # ---- preflight: read-only wiring verdict, no ledger writes
    if args.preflight_only:
        wiring = []
        if not drift.get("pass"):
            wiring.append("REFUSED_DRIFT")
        if not auth.get("pass"):
            wiring.append("REFUSED_NO_AUTH")
        if lock["verdict"] == "HELD_PROVEN":
            wiring.append("NOT_RUN_RESOURCE_CONFLICT")
        elif lock["verdict"] != "FREE_PROVEN":
            wiring.append("REFUSED_CONTROL_STATE_DRIFT")
        if reg.get("failure") or reg.get("head_check") == "DIVERGED":
            wiring.append("REFUSED_CONTROL_STATE_DRIFT")
        manifest["wiring_failures"] = sorted(set(wiring))
        manifest["expected_pre_go_state"] = {
            "go_absent_is_expected": True,
            "gate_reason": reason,
            "registry_head_lag_exit_neutral":
                reg.get("head_check") == "LAG_ANCESTOR",
            "must_reconcile_before_go":
                bool(reg.get("must_reconcile_before_go")),
        }
        write_manifest(args, manifest)
        print(json.dumps(manifest, indent=1, sort_keys=True,
                         ensure_ascii=False))
        if wiring:
            print(f"PREFLIGHT WIRING FAILURES: {sorted(set(wiring))}",
                  file=sys.stderr)
            return EXIT_REFUSED
        print("PREFLIGHT: wiring touches real authority; all pins green; "
              f"gate verdict = {reason} (expected pre-GO)", file=sys.stderr)
        return EXIT_OK

    # ---- execution mode: refusals recorded per the FIXED ledger's law
    if not allowed:
        return _refuse(args, contract, reason, detail)

    # ---- ALL GATES PASSED — real scored execution (contract v2.1)
    go_resolved = args.go_artifact if os.path.isabs(args.go_artifact) else \
        os.path.join(args.worktree, args.go_artifact)
    ledger_resolved = args.ledger_path if os.path.isabs(args.ledger_path) \
        else os.path.join(args.worktree, args.ledger_path)
    if not sandbox_mode:
        guard = production_authority_violations(args, go_resolved,
                                                ledger_resolved)
        if guard:
            return _refuse(args, contract, "REFUSED_CONTROL_STATE_DRIFT",
                           {"gate": "PRODUCTION-DEFAULT-AUTHORITY",
                            "law": "production scored execution runs ONLY "
                                   "against the unoverridden real authority "
                                   "paths; any override reaching the "
                                   "execution branch is a test bypass and "
                                   "dies here (GO/registry/pins/ledger/lock "
                                   "must all be the real defaults)",
                            "violations": guard})
    fault = None
    if args.sandbox_fault:
        if not sandbox_mode:
            print("TECHNICAL: --sandbox-fault requires --sandbox-root",
                  file=sys.stderr)
            return EXIT_TECHNICAL
        try:
            fault = json.loads(args.sandbox_fault)
            if not isinstance(fault, dict):
                raise ValueError("fault must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"TECHNICAL: --sandbox-fault unparseable: {exc}",
                  file=sys.stderr)
            return EXIT_TECHNICAL

    # SANDBOX-ONLY fault: corrupt a pinned file between the pre-lock drift
    # check and the executor's post-acquire re-verify — the TOCTOU window.
    # The pin name comes from the fault spec (no hardcoded pin names in
    # production source); the tamper is a byte append under the sandbox.
    if fault and fault.get("type") == "tamper_after_gates":
        pin_name = str(fault.get("pin") or "")
        target = paths.get(f"pin:{pin_name}")
        if not target:
            print(f"TECHNICAL: tamper_after_gates fault names unknown pin "
                  f"{pin_name!r}", file=sys.stderr)
            return EXIT_TECHNICAL
        with open(target, "ab") as fh:
            fh.write(b'{"sandbox_fault": "tamper_after_gates"}\n')

    import scored_executor  # gate6/runner — the real execution path
    run_root = os.path.join(
        sroot if sandbox_mode else os.path.dirname(ledger_resolved),
        "runs", args.run_label)

    # PIN-ENFORCE law 4 — self-integrity binding AT the execution boundary:
    # hash the modules ACTUALLY imported (the runner's own __file__ and the
    # executor's) against their live contract pins — path equality AND sha
    # equality; any mismatch refuses BEFORE computation (ledger REFUSED row).
    si_violations = self_integrity_violations(
        contract, args.worktree,
        runner_file=os.path.abspath(__file__),
        executor_file=os.path.abspath(scored_executor.__file__))
    if si_violations:
        return _refuse(args, contract, "REFUSED_CONTROL_STATE_DRIFT",
                       {"gate": "SELF-INTEGRITY",
                        "law": "the executing runner/executor bytes must be "
                               "the live contract pins (path + sha); the "
                               "modules actually imported are hashed, not "
                               "assumed",
                        "violations": si_violations})

    # PIN-ENFORCE law 3 — TOCTOU guard closure over the FULL LIVE pin set:
    # re-verifies GO artifact + registry head + every live pin (path+sha
    # resolved exactly like check_drift) AFTER the heavy lock is acquired.
    # Replaces the former base-only scored_executor.TOCTOU_PIN_NAMES tuple
    # (removed from the executor — F-V2 root cause 2).
    reverify_authority = build_reverify_closure(
        contract, args.worktree, args.registry_path, paths, pins_live,
        go_resolved, registry_row,
        pins_by_name["a7_prelaunch_v3_digest"]["sha256"],
        paths["pin:a7_prelaunch_v3_digest"])

    cfg = {
        "cycle_id": CYCLE_ID,
        "sandbox_root": sroot,
        "worktree": args.worktree,
        "contract_path": args.contract,
        "builder_path": paths["pin:machinery_builder_v3"],
        "builder_pin_sha": pins_by_name["machinery_builder_v3"]["sha256"],
        "builder_overrides": (
            scored_executor.sandbox_builder_overrides(sroot, contract)
            if sandbox_mode else None),
        "identity_ids": contract["embedded_laws"]["identity_ids"],
        "ledger_path": ledger_resolved,
        "lock_runtime_dir": args.lock_runtime_dir,
        "run_root": run_root,
        "command": list(sys.argv),
        "fault": fault,
        "reverify_authority": reverify_authority,
    }
    rc, execution = scored_executor.run_scored_execution(cfg)
    manifest["execution"] = execution
    print(json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False))
    print(f"SCORED EXECUTION: verdict={execution.get('verdict')} "
          f"terminal_state={execution.get('terminal_state')} exit={rc}",
          file=sys.stderr)
    return rc


def _refuse(args, contract, reason, detail) -> int:
    """Record the refusal (ledger REFUSED row per the FIXED ledger's law +
    refusal_record.json) and exit non-zero. Never called in --preflight-only
    mode (preflight writes nothing)."""
    import trial_ledger  # already on sys.path (the FIXED module, sha-checked)
    exit_code = EXIT_CONFLICT if reason == "NOT_RUN_RESOURCE_CONFLICT" \
        else EXIT_REFUSED
    ledger_path = args.ledger_path if os.path.isabs(args.ledger_path) else \
        os.path.join(args.worktree, args.ledger_path)
    note = json.dumps({"reason": reason, "detail": detail}, sort_keys=True,
                      ensure_ascii=False)[:2000]
    recorded, ledger_error = None, None
    try:
        ledger = trial_ledger.TrialLedger(
            ledger_path, contract["embedded_laws"]["identity_ids"])
        recorded = ledger.record_refusal(reason, note=note)
    except Exception as exc:  # noqa: BLE001 — a ledger failure is technical,
        # never silently skipped
        ledger_error = str(exc)[:400]
    rr_path = args.refusal_record_path or str(
        Path(ledger_path).parent / "refusal_record.json")
    try:
        Path(rr_path).parent.mkdir(parents=True, exist_ok=True)
        Path(rr_path).write_text(json.dumps(
            {"schema": "futures_es_pb1_v1/refusal_record@2",
             "cycle_id": CYCLE_ID, "reason": reason, "detail": detail,
             "ledger_row": recorded, "ledger_error": ledger_error},
            indent=1, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8")
    except OSError as exc:
        ledger_error = ledger_error or f"refusal_record write failed: {exc}"
    print(f"REFUSED: {reason} — {json.dumps(detail, ensure_ascii=False)}",
          file=sys.stderr)
    if ledger_error:
        print(f"TECHNICAL: refusal ledger recording failed: {ledger_error}",
              file=sys.stderr)
        return EXIT_TECHNICAL
    print(f"refusal recorded: ledger={ledger_path} "
          f"row seq={(recorded or {}).get('seq')}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
