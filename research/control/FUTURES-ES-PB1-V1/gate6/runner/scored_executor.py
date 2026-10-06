#!/usr/bin/env python
"""scored_executor.py — the REAL scored execution path for
FUTURES-ES-PB1-V1 (cycle FUTURES-ES-PB1-V1, gate 6), replacing the
pre-GO "WOULD EXECUTE" stub of scored_runner.py (withdrawal record:
gate6/runner/GO_READY_WITHDRAWAL.md).

This module is imported by scored_runner.py and is invoked ONLY after every
authority gate (R0 registry, R1 GO, R2 auth, R3 lock, R4 drift, R5
adjudication) has passed. It implements LAUNCH_CONTRACT_V2 §4 (execution
law) + the §v2.1 addendum:

  1. LOCK LIFECYCLE — acquire via the CANONICAL governance mechanism
     (governance.heavy_lock.acquire; this module never reimplements it).
     In --sandbox-root mode the canonical runtime dir is redirected under
     the sandbox for the duration of the run (restored in `finally`);
     in production mode the machine-wide runtime is used untouched.
     AFTER acquire, the caller-supplied `reverify_authority` closure
     re-checks the GO artifact, the registry head and EVERY live operative
     pin (the closure is built by the runner from the contract's full live
     pin set — PIN-ENFORCE law 3; the former base-only TOCTOU_PIN_NAMES
     tuple is removed). Release happens in `finally` ALWAYS (FINISHED /
     FAILED / TECHABORT), exceptions included. Lock held at acquire =>
     NOT_RUN_RESOURCE_CONFLICT (ledger REFUSED row, exit 75).

  2. COMPUTATION — the machinery of record final/dryrun_builder_v3.py is
     IMPORTED (never forked): load_inputs / build_sessions / derive_state /
     parse_identity / simulate / c1_sign / check_cost_sample /
     check_warmup_regression are called from the pinned module. Production
     runs the pinned module verbatim (real pinned inputs); sandbox runs exec
     the SAME source into a module namespace whose location constants
     (WT / ES_CACHE / PIN_PANEL / PIN_CHAIN / PIN_SPEC) resolve to the
     synthetic sandbox fixtures — the simulation logic is byte-identical.

  3. LEDGER — the FIXED gate6/trial_ledger.py (sha-pinned) opens the
     24-slot ledger. Every scientifically computed result is recorded to
     the observed denominator (PASS / FAIL) even when publication fails
     (published=false). Per-identity terminal rows exactly once. On a
     retry after an interrupted run, the ledger replay already knows the
     terminal slots: the retry SKIPS them (never recomputes, never
     double-counts, never mints identities), copying the prior run's
     published bytes after verifying the recorded result_sha.

  4. PUBLICATION + RECONCILIATION — per-identity output files + trades
     index + summary under a run dir; a reconciliation summary against the
     frozen identity table; any mismatch => fail closed.

  5. REPRODUCTION TWIN — a second independent pass (fresh machinery module
     instance, fresh input load, separate output dir) must be byte-identical
     (determinism law). Twin mismatch => terminal state TWIN_MISMATCH,
     NEVER success.

  6. TERMINAL HANDOFF — a terminal-audit descriptor (paths + shas of run
     outputs, ledger, twin manifests, verdict) is written for the post-GO
     terminal A7.

  7. FAIL-CLOSED — any computation / ledger / publication / twin failure
     => non-zero exit + terminal state recorded; success is NEVER returned
     for incomplete execution. Finalization failures (D-7: ledger summary /
     lock release / terminal-handoff / runtime-restore cleanup) can likewise
     NEVER keep a success verdict: a computation-complete run whose
     finalization failed ends FINALIZATION_FAILURE with a non-zero exit,
     never EXECUTION_COMPLETE.

  8. SANDBOX ISOLATION — fault injection (`fault` config) is REFUSED
     unless sandbox mode is active; every sandbox output carries the
     SYNTHETIC-SANDBOX stamp; the sandbox ledger/lock live under the
     sandbox root, so a sandbox run cannot write the real ledger, real
     registry, or the machine-wide heavy-lock runtime.

Exit codes (runner contract v2/v2.1): 0 EXECUTION_COMPLETE; 2 refusal
(gates / TOCTOU drift / isolation); 75 NOT_RUN_RESOURCE_CONFLICT; 3
terminal execution failure (TWIN_MISMATCH, PUBLICATION_FAILURE,
COMPUTE_FAILURE, RECONCILIATION_FAILURE, PRIOR_TERMINAL_OUTPUT_MISSING,
ABORTED_SANDBOX_FAULT); 4 FINALIZATION_FAILURE (D-7, pending
ratification: the computation may have completed but the evidentiary
closure — ledger summary / lock release / terminal handoff — failed;
never a success).

PRE-GO LAW is unchanged: with no typed owner GO at this cycle's gate the
runner refuses before this module is ever reached. No real scored outcome
exists today.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CYCLE_ID = "FUTURES-ES-PB1-V1"
LOCK_ROLE = "SCORED-EXECUTION"

EXIT_OK, EXIT_REFUSED, EXIT_FAILURE, EXIT_CONFLICT = 0, 2, 3, 75
# D-7 [IMPLEMENTED-DEFAULT-PENDING-RATIFICATION]: finalization failures are
# a distinct class from exit 3 (terminal EXECUTION failure — the computation
# itself failed): a finalization failure means the computation may have
# completed but the evidentiary closure failed. Exit 4 keeps the two
# machine-distinguishable; no prior contract code used 4.
EXIT_FINALIZATION = 4

SANDBOX_STAMP = "SYNTHETIC-SANDBOX"
RUN_CLASS_SANDBOX = "SYNTHETIC-SANDBOX"
RUN_CLASS_PRODUCTION = "SCORED-EXECUTION"

TERMINAL_COMPLETE = "EXECUTION_COMPLETE"
TERMINAL_TWIN_MISMATCH = "TWIN_MISMATCH"
TERMINAL_PUBLICATION = "PUBLICATION_FAILURE"
TERMINAL_COMPUTE = "COMPUTE_FAILURE"
TERMINAL_RECONCILIATION = "RECONCILIATION_FAILURE"
TERMINAL_PRIOR_MISSING = "PRIOR_TERMINAL_OUTPUT_MISSING"
TERMINAL_ABORTED = "ABORTED_SANDBOX_FAULT"
TERMINAL_CONFLICT = "NOT_RUN_RESOURCE_CONFLICT"
TERMINAL_DRIFT = "REFUSED_CONTROL_STATE_DRIFT"
# D-7: single finalization-failure class state, consistent with the D-6
# reason-class naming convention; the per-stage detail (ledger_summary /
# lock_release / runtime_restore / terminal_handoff) lives in the run's
# `finalization_failures[]` list (several cleanup steps can fail in one
# run, and the cleanup-order law requires collecting ALL of them). The
# SPEC §9 `*_BLOCKED_<reason>` names are pre-decided A7 TERMINAL-AUDIT
# outcomes — a different vocabulary layer the runner must never select —
# so they do not govern executor states; the registered plan carries no
# executor terminal vocabulary of its own (D-7 records this authority gap).
TERMINAL_FINALIZATION = "FINALIZATION_FAILURE"

SCHEMA_HANDOFF = "futures_es_pb1_v1/terminal_audit_handoff@1"
SCHEMA_RUN_MANIFEST = "futures_es_pb1_v1/scored_run_manifest@1"

# PIN-ENFORCE (fix3, 2026-10-05): the former base-only hardcoded
# TOCTOU_PIN_NAMES tuple is REMOVED. The post-acquire re-verify closure is
# built by the runner (scored_runner.build_reverify_closure) over the FULL
# LIVE contract pin set — base + every addendum, path-keyed supersession —
# resolved exactly the way check_drift resolves pins (F-V2 root cause 2
# closed; see fix3/PIN_ENFORCE_REPORT.md). The executor only ever calls the
# caller-supplied closure.


class SandboxFaultError(RuntimeError):
    """Sandbox-only injected fault (never constructible in production)."""


class ExecutorRefusal(Exception):
    """Run-level refusal after the gates: recorded as a ledger REFUSED row."""

    def __init__(self, reason: str, detail: dict, exit_code: int):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail
        self.exit_code = exit_code


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    return sha256_bytes(p.read_bytes())


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------- sandbox isolation

def resolve_lock_runtime(sandbox_root: str | None) -> str | None:
    """Lock runtime resolution — the isolation boundary for the lock.

    None (production default) => None, meaning the canonical machine-wide
    governance runtime is used untouched (no patch, no bypass).
    A sandbox root => a runtime INSIDE the sandbox, so sandbox runs can
    never touch the real machine-wide heavy-lock state.
    """
    if sandbox_root is None:
        return None
    return str(Path(sandbox_root) / "heavy_runtime")


def _patch_sandbox_lock_runtime(runtime_dir: str):
    """Sandbox-only: point the CANONICAL governance lock runtime at the
    sandbox runtime for the duration of a run. Returns the restore callable.

    The acquire code path itself is governance.heavy_lock.acquire,
    verbatim — only the runtime LOCATION is redirected, exactly like the
    runner's read-only inspect gate accepts an injectable runtime dir for
    tests. This function is only ever called from the sandbox branch of
    run_scored_execution (asserted by the test suite via AST)."""
    from governance import heavy_lock  # <worktree>/research on sys.path

    prev = heavy_lock.RUNTIME_DIRNAME
    heavy_lock.RUNTIME_DIRNAME = Path(runtime_dir)

    def restore():
        heavy_lock.RUNTIME_DIRNAME = prev

    return restore


# ------------------------------------------------------- machinery loading

def load_builder_module(builder_path: str, overrides: dict | None = None):
    """Load the machinery of record (final/dryrun_builder_v3.py) by
    executing ITS OWN SOURCE into a module namespace. Production runs use
    the pinned file with NO overrides (verbatim constants => real pinned
    inputs, sha-asserted by the builder's own load_inputs). Sandbox runs
    override ONLY the location/pin constants (WT, ES_CACHE, PIN_SPEC,
    PIN_PANEL, PIN_CHAIN) to the synthetic fixtures — every function
    (load_inputs, build_sessions, derive_state, parse_identity, simulate,
    c1_sign, check_cost_sample, check_warmup_regression) is the pinned
    machinery's own code, never a fork."""
    path = os.fspath(builder_path)
    name = "dryrun_builder_v3_scored_exec"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load machinery of record at {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # top level defines constants + functions only
    if overrides:
        for key, val in overrides.items():
            setattr(mod, key, val)
    return mod


def sandbox_builder_overrides(sandbox_root: str, contract: dict) -> dict:
    """Sandbox overrides derived FROM the sandbox contract pins (no fixture
    path is ever hardcoded in this module)."""
    pins = {p["name"]: p for p in contract["pins"]}
    return {
        "WT": str(sandbox_root),
        "ES_CACHE": str(Path(sandbox_root) / "research/control/"
                        "FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache"),
        "PIN_SPEC": pins["spec_pb1_es"]["sha256"],
        "PIN_PANEL": pins["pinned_panel_es_1m_outright"]["sha256"],
        "PIN_CHAIN": pins["held_chain_es_chain_T5"]["sha256"],
    }


# ------------------------------------------------------------- one pass

class _PassResult:
    __slots__ = ("label", "out_dir", "computed", "skipped_terminal",
                 "publication_failures", "compute_failures",
                 "prior_output_missing", "results", "integrity",
                 "manifest")


def _write_atomic(path: Path, data: bytes):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _identity_record(builder, inp, st, sessions, iid: str, run_class: str,
                     contract_path: str, builder_sha: str) -> dict:
    """One identity's scored output record. Publication formatting adapted
    from the machinery's run_pass record shape (same fields); the
    mechanics come from builder.simulate / builder.parse_identity."""
    cfg_i = builder.parse_identity(iid)
    rec, _session_set = builder.simulate(iid, cfg_i, st, inp, sessions)
    header = {
        "run_class": run_class,
        "cycle_id": CYCLE_ID,
        "law": ("scored execution per LAUNCH_CONTRACT_V2 (§4 + §v2.1): "
                "machinery of record final/dryrun_builder_v3.py, mechanics "
                "unchanged; FIRST PnL computation, outcome-blind until now"),
        "contract_sha256": sha256_file(contract_path),
        "builder_sha256": builder_sha,
        "sandbox_stamp": SANDBOX_STAMP if run_class == RUN_CLASS_SANDBOX else None,
        "generated_utc": builder.GENERATED_UTC,
        "identity_id": iid,
        "arm_class": cfg_i["klass"],
        "delay_min": cfg_i.get("delay"),
        "cost_tier": cfg_i.get("tier"),
        "mechanics_citations": dict(builder.CITATIONS),
        "implementation_pins": [
            "D-A1 q80 numpy.percentile linear",
            "D-A2 C2 long hold-to-close",
            "D-A3 C1 sha256 seed 20261002",
            "D-A4 chain-wide strict-past windows",
            "D-A5 costs as USD lines"],
        "totals": {
            "n_sessions_in_set": rec["n_sessions"],
            "n_trades": len(rec["trades"]),
            "skips": rec["skips"],
            "n_trades_per_fold": rec["fold_n"],
        },
        "trades": rec["trades"],
    }
    return header


def _run_pass(builder, builder_sha: str, inp: dict, st: dict, sessions: dict,
              *, cfg: dict, label: str, write_ledger: bool,
              ledger, prior_outputs: dict, fault: dict | None) -> _PassResult:
    """One full computation pass over the frozen identity table.

    write_ledger=True  => the compute pass: per-identity terminal rows
                          exactly once (skipping already-terminal slots on
                          a retry — never recompute, never double-count).
    write_ledger=False => the reproduction twin: everything recomputed
                          independently, ledger untouched.
    """
    out_dir = Path(cfg["run_root"]) / label
    out_dir.mkdir(parents=True, exist_ok=True)
    res = _PassResult()
    res.label = label
    res.out_dir = str(out_dir)
    res.computed = []
    res.skipped_terminal = []
    res.publication_failures = []
    res.compute_failures = []
    res.prior_output_missing = []
    res.results = {}

    ids = list(inp["ids"])
    run_class = RUN_CLASS_SANDBOX if cfg.get("sandbox") else RUN_CLASS_PRODUCTION
    fault = fault or {}
    fault_type = fault.get("type")
    nonlocal_ro = [False]

    def _publish(iid: str, record: dict) -> tuple[bool, bytes]:
        data = json.dumps(record, sort_keys=True,
                          ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if fault_type == "publication" and fault.get("identity") == iid \
                and not nonlocal_ro[0]:
            os.chmod(out_dir, 0o555)  # injected: publication becomes impossible
            nonlocal_ro[0] = True
        with open(out_dir / f"{iid}.json", "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        return True, data

    try:
        for pos, iid in enumerate(ids):
            # ---- interrupted-run law: terminal slots are SKIPPED (never
            # recomputed, never double-counted); their prior published bytes
            # are copied after sha verification. A terminal slot whose prior
            # bytes are unavailable is reported missing (fail-closed at
            # reconciliation) — it is NEVER recomputed.
            if write_ledger and iid in prior_outputs:
                prior = prior_outputs[iid]
                if not prior.get("run_dir") or not prior.get("file"):
                    res.prior_output_missing.append(
                        {"identity_id": iid,
                         "why": "terminal slot has no copyable prior output "
                                "(never recomputed)"})
                    continue
                src = Path(prior["run_dir"]) / prior["file"]
                try:
                    data = src.read_bytes()
                except OSError:
                    res.prior_output_missing.append(
                        {"identity_id": iid, "why": f"prior output unreadable: {src}"})
                    continue
                if sha256_bytes(data) != prior.get("result_sha"):
                    res.prior_output_missing.append(
                        {"identity_id": iid, "why": "prior output sha mismatch"})
                    continue
                with open(out_dir / f"{iid}.json", "wb") as fh:
                    fh.write(data)
                res.skipped_terminal.append(iid)
                res.results[iid] = json.loads(data)
                continue

            # ---- sandbox-only fault injection (loudly guarded)
            if fault_type == "abort" and len(res.computed) == fault["after_k"]:
                raise SandboxFaultError(
                    f"sandbox fault injection: abort after "
                    f"{fault['after_k']} identities")
            if fault_type == "exception" and \
                    len(res.computed) == fault.get("at_index", 0):
                raise RuntimeError(
                    "sandbox fault injection: executor exception "
                    "mid-computation")

            # ---- compute (machinery of record, never forked)
            try:
                record = _identity_record(builder, inp, st, sessions, iid,
                                          run_class, cfg["contract_path"],
                                          builder_sha)
                status, published = "PASS", None
            except SandboxFaultError:
                raise
            except Exception as exc:  # noqa: BLE001 — a defective identity is
                # still a COMPUTED result: FAIL row, observed denominator
                res.computed.append(iid)
                res.compute_failures.append(
                    {"identity_id": iid, "error": repr(exc)[:400]})
                if write_ledger:
                    ledger.record_result(
                        iid, "FAIL", published=False, result_sha=None,
                        note=json.dumps({"pass": label, "stage": "compute",
                                         "sandbox_stamp":
                                         SANDBOX_STAMP if cfg.get("sandbox") else None},
                                        sort_keys=True),
                        computed_by="scored_executor")
                continue

            # ---- publish (failure still counts observed, published=false)
            try:
                _, data = _publish(iid, record)
                published = True
            except SandboxFaultError:
                raise
            except OSError as exc:
                published = False
                res.publication_failures.append(
                    {"identity_id": iid, "error": repr(exc)[:200]})
                data = json.dumps(record, sort_keys=True, ensure_ascii=False,
                                  separators=(",", ":")).encode("utf-8")
            res.computed.append(iid)
            res.results[iid] = record
            if write_ledger:
                ledger.record_result(
                    iid, status, published=published,
                    result_sha=sha256_bytes(data),
                    note=json.dumps({"run_dir": res.out_dir,
                                     "file": f"{iid}.json",
                                     "pass": label,
                                     "sandbox_stamp":
                                     SANDBOX_STAMP if cfg.get("sandbox") else None},
                                    sort_keys=True),
                    computed_by="scored_executor")

        # ---- trades index + summary (mirror of the machinery's run_pass
        # publication shape, stamped for this run class). Publication of
        # these files obeys the same law: a write failure is recorded as a
        # publication failure (the pass still completes fail-closed).
        index = {iid: [[t["session_date"], t["fill_bar_utc"], t["exit_bar_utc"]]
                       for t in res.results[iid]["trades"]]
                 for iid in ids if iid in res.results}
        integrity = {}
        try:
            cs = builder.check_cost_sample(res.results, inp, 20)
            cs["verdict"] = "PASS" if cs["all_match"] else "FAIL"
            integrity["cost_recompute_sample"] = cs
        except Exception as exc:  # noqa: BLE001
            integrity["cost_recompute_sample"] = {"verdict": "FAIL",
                                                  "error": repr(exc)[:200]}
        try:
            wr = builder.check_warmup_regression(res.results, inp)
            integrity["warmup_regression"] = wr
        except Exception as exc:  # noqa: BLE001
            integrity["warmup_regression"] = {"verdict": "FAIL",
                                              "error": repr(exc)[:200]}
        res.integrity = integrity
        summary = {
            "run_class": run_class,
            "sandbox_stamp": SANDBOX_STAMP if cfg.get("sandbox") else None,
            "generated_utc": builder.GENERATED_UTC,
            "panel_stats": cfg.get("panel_stats"),
            "validation": st["validation"],
            "per_identity": {iid: {
                "n_sessions_in_set": res.results[iid]["totals"]["n_sessions_in_set"],
                "n_trades": res.results[iid]["totals"]["n_trades"],
                "n_trades_per_fold": res.results[iid]["totals"]["n_trades_per_fold"],
                "skips": res.results[iid]["totals"]["skips"],
            } for iid in ids if iid in res.results},
            "integrity": integrity,
        }
        for fname, blob in (
                ("trades_index.json",
                 json.dumps({"run_class": run_class,
                             "sandbox_stamp":
                             SANDBOX_STAMP if cfg.get("sandbox") else None,
                             "generated_utc": builder.GENERATED_UTC,
                             "index": index},
                            sort_keys=True, ensure_ascii=False)
                 .encode("utf-8")),
                ("summary.json",
                 json.dumps(summary, indent=1, sort_keys=True,
                            ensure_ascii=False).encode("utf-8"))):
            try:
                _write_atomic(Path(out_dir) / fname, blob)
            except OSError as exc:
                res.publication_failures.append(
                    {"identity_id": None, "file": fname,
                     "error": repr(exc)[:200]})
    finally:
        if nonlocal_ro[0]:
            os.chmod(out_dir, 0o755)  # restore the injected read-only dir
    return res


# ------------------------------------------------------------- orchestration

def _reconcile(cfg: dict, ids_frozen: list[str], pass_a: _PassResult,
               ledger, prior_output_missing: list) -> dict:
    """Reconciliation summary: outputs vs the frozen identity table
    (order+set), ledger terminal state vs the 24-slot law."""
    out_dir = Path(pass_a.out_dir)
    on_disk = sorted(p.name for p in out_dir.glob("*.json")
                     if p.name not in ("trades_index.json", "summary.json"))
    expected = sorted(f"{iid}.json" for iid in ids_frozen)
    files_match = on_disk == expected
    summary = ledger.summary()
    identity_rows = [r for r in ledger._rows_cache if r.get("identity_id")]
    terminal_ids = sorted(iid for iid, s in ledger._terminal.items())
    all_terminal = terminal_ids == sorted(ids_frozen)
    no_double = len(identity_rows) == len(terminal_ids)
    integrity_ok = all(
        block.get("verdict") == "PASS"
        for block in (pass_a.integrity or {}).values()
        if isinstance(block, dict) and "verdict" in block)
    ok = (files_match and all_terminal and no_double
          and not prior_output_missing and integrity_ok)
    return {
        "schema": "futures_es_pb1_v1/reconciliation@1",
        "sandbox_stamp": SANDBOX_STAMP if cfg.get("sandbox") else None,
        "frozen_identity_ids": ids_frozen,
        "output_files": on_disk,
        "output_files_match_frozen_table": files_match,
        "ledger_summary": summary,
        "terminal_ids_exact_once": all_terminal,
        "identity_rows_equal_terminal_count": no_double,
        "prior_output_missing": prior_output_missing,
        "integrity_checks": {k: (v or {}).get("verdict")
                             for k, v in (pass_a.integrity or {}).items()},
        "pass": bool(ok),
    }


def run_scored_execution(cfg: dict) -> tuple[int, dict]:
    """Full scored execution under the machine-wide heavy lock.

    Returns (exit_code, terminal_record). Fail-closed: exit 0 ONLY for
    EXECUTION_COMPLETE (24 observed rows, all published, twin byte-match,
    reconciliation pass).
    """
    sandbox = bool(cfg.get("sandbox_root"))
    cfg["sandbox"] = sandbox  # single source of truth for the output stamps
    fault = cfg.get("fault") or {}
    if fault and not sandbox:
        raise AssertionError(
            "fault injection is SANDBOX-ONLY and was requested in "
            "production mode — refused by construction")
    run_root = Path(cfg["run_root"])
    run_root.mkdir(parents=True, exist_ok=True)
    started_utc = _utcnow()

    terminal = {
        "schema": SCHEMA_RUN_MANIFEST,
        "cycle_id": CYCLE_ID,
        "sandbox": sandbox,
        "sandbox_stamp": SANDBOX_STAMP if sandbox else None,
        "run_root": str(run_root),
        "started_utc": started_utc,
        "verdict": None,
        "terminal_state": None,
        # D-7: the computation phase and the finalization phase are
        # DISTINGUISHED. computation_complete=True means the computation +
        # twin + reconciliation phase ran to completion and produced a
        # verdict; the finalization verdict lives in finalization_failures[]
        # / lock_released_status / the handoff-write outcome. A
        # computation-complete run with a finalization failure is a FAILURE,
        # never EXECUTION_COMPLETE.
        "computation_complete": False,
        "finalization_failures": [],
        "failure_reasons": [],
        "exit_code": None,
    }

    from governance import heavy_lock  # canonical lock module (sys.path set by runner)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # gate6/
    import trial_ledger  # the FIXED ledger module (sha-pinned by the contract)

    handle = None
    restore_runtime = None
    release_status = "FAILED"
    ledger = None

    def _refuse(exc: ExecutorRefusal) -> tuple[int, dict]:
        try:
            led = trial_ledger.TrialLedger(cfg["ledger_path"],
                                           cfg["identity_ids"])
            row = led.record_refusal(
                exc.reason,
                note=json.dumps(dict(exc.detail, sandbox_stamp=SANDBOX_STAMP
                                     if sandbox else None),
                                sort_keys=True, ensure_ascii=False)[:2000])
            terminal["refusal_row"] = row
        except Exception as led_exc:  # noqa: BLE001 — never hide the refusal
            terminal["refusal_ledger_error"] = repr(led_exc)[:300]
        terminal["verdict"] = exc.reason
        terminal["terminal_state"] = exc.reason
        terminal["exit_code"] = exc.exit_code
        return exc.exit_code, terminal

    try:
        # ---- 1. LOCK LIFECYCLE (canonical acquire; sandbox runtime redirect)
        rt = cfg.get("lock_runtime_dir") or resolve_lock_runtime(
            cfg.get("sandbox_root"))
        if cfg.get("sandbox_root") is not None:
            restore_runtime = _patch_sandbox_lock_runtime(rt)
        try:
            handle = heavy_lock.acquire(
                cycle_id=CYCLE_ID, role=LOCK_ROLE,
                worktree=cfg["worktree"], command=list(cfg["command"]),
                expected_artifacts=[str(cfg["ledger_path"])])
        except heavy_lock.LockBusyError as exc:
            terminal["lock"] = {"acquired": False,
                                "runtime": str(rt or "canonical"),
                                "reason": repr(exc)[:300]}
            return _refuse(ExecutorRefusal(
                "NOT_RUN_RESOURCE_CONFLICT",
                {"gate": "R3-executor", "law": "one heavy job machine-wide; "
                 "never wait, never kill a foreign worker",
                 "detail": repr(exc)[:300]}, EXIT_CONFLICT))
        except heavy_lock.HeavyLockError as exc:
            terminal["lock"] = {"acquired": False,
                                "runtime": str(rt or "canonical"),
                                "reason": repr(exc)[:300]}
            return _refuse(ExecutorRefusal(
                "REFUSED_CONTROL_STATE_DRIFT",
                {"gate": "R3-executor", "detail": repr(exc)[:300]},
                EXIT_REFUSED))
        terminal["lock"] = {"acquired": True, "role": LOCK_ROLE,
                            "runtime": str(rt or "canonical machine runtime"),
                            "pid": os.getpid()}

        # ---- 2. TOCTOU guard: re-verify authority AFTER acquire
        drifts = list(cfg["reverify_authority"]() or [])
        if drifts:
            return _refuse(ExecutorRefusal(
                "REFUSED_CONTROL_STATE_DRIFT",
                {"gate": "TOCTOU-post-acquire", "drifts": drifts,
                 "law": "GO artifact, registry head and input hashes are "
                        "re-verified after the heavy lock is acquired"},
                EXIT_REFUSED))

        # ---- 3. machinery + inputs
        builder_sha = sha256_file(cfg["builder_path"])
        if builder_sha != cfg["builder_pin_sha"]:
            return _refuse(ExecutorRefusal(
                "REFUSED_CONTROL_STATE_DRIFT",
                {"gate": "machinery", "detail": "builder sha drift vs pin",
                 "expected": cfg["builder_pin_sha"], "actual": builder_sha},
                EXIT_REFUSED))
        builder = load_builder_module(
            cfg["builder_path"], cfg.get("builder_overrides"))
        inp = builder.load_inputs()
        ids_frozen = list(cfg["identity_ids"])
        if list(inp["ids"]) != ids_frozen:
            return _refuse(ExecutorRefusal(
                "REFUSED_CONTROL_STATE_DRIFT",
                {"gate": "identity-table",
                 "detail": "machinery-derived identity ids != frozen "
                           "contract table (order+set)",
                 "machinery_ids": list(inp["ids"])[:30]}, EXIT_REFUSED))

        # ---- 4. ledger open (replay knows terminal slots)
        ledger = trial_ledger.TrialLedger(cfg["ledger_path"], ids_frozen)
        prior_outputs = {}
        for iid, status in ledger._terminal.items():
            row = next((r for r in reversed(ledger._rows_cache)
                        if r.get("identity_id") == iid), None)
            note = {}
            try:
                note = json.loads(row.get("note") or "{}") if row else {}
            except json.JSONDecodeError:
                note = {}
            if isinstance(note, dict) and note.get("run_dir") \
                    and note.get("file"):
                prior_outputs[iid] = {"run_dir": note["run_dir"],
                                      "file": note["file"],
                                      "result_sha": row.get("result_sha"),
                                      "status": status}
            else:
                prior_outputs[iid] = {"run_dir": None, "file": None,
                                      "result_sha": row.get("result_sha")
                                      if row else None,
                                      "status": status}
        terminal["ledger_replay"] = {
            "prior_terminal": sorted(ledger._terminal),
            "observed_before_run": ledger.observed()}

        # ---- 5. compute pass A (single-shot reads happen here, under lock)
        sessions, panel_stats = builder.build_sessions(inp)
        st = builder.derive_state(inp, sessions)
        if not st["counts_ok"]:
            raise RuntimeError(
                "fold eval-set derivation mismatch vs selection_freeze "
                "(counts_ok=false)")
        cfg["panel_stats"] = panel_stats
        pass_a = _run_pass(builder, builder_sha, inp, st, sessions,
                           cfg=cfg, label="pass_a", write_ledger=True,
                           ledger=ledger,
                           prior_outputs=prior_outputs,
                           fault=fault)
        terminal["pass_a"] = {
            "out_dir": pass_a.out_dir,
            "computed": pass_a.computed,
            "skipped_terminal": pass_a.skipped_terminal,
            "publication_failures": pass_a.publication_failures,
            "compute_failures": pass_a.compute_failures,
            "prior_output_missing": pass_a.prior_output_missing,
        }

        # ---- 6. reproduction twin (fresh machinery instance, fresh input
        # load, separate output dir; ledger untouched)
        builder_b = load_builder_module(
            cfg["builder_path"], cfg.get("builder_overrides"))
        inp_b = builder_b.load_inputs()
        sessions_b, panel_stats_b = builder_b.build_sessions(inp_b)
        st_b = builder_b.derive_state(inp_b, sessions_b)
        cfg_b = dict(cfg)
        cfg_b["panel_stats"] = panel_stats_b
        pass_b = _run_pass(builder_b, builder_sha, inp_b, st_b, sessions_b,
                           cfg=cfg_b, label="pass_b", write_ledger=False,
                           ledger=None, prior_outputs={},
                           fault=fault if fault.get("type") == "twin_perturb"
                           else {})
        # injected twin perturbation: corrupt one published byte-stream
        if fault.get("type") == "twin_perturb":
            tgt = Path(pass_b.out_dir) / f"{fault['identity']}.json"
            raw = bytearray(tgt.read_bytes())
            raw[-2] = raw[-2] ^ 0x01  # flip one bit near the end
            tgt.write_bytes(bytes(raw))
        terminal["pass_b"] = {"out_dir": pass_b.out_dir,
                              "computed": pass_b.computed}

        # ---- 7. twin compare (G8 byte-match over the two output dirs)
        man_a = trial_ledger.twin_manifest(pass_a.out_dir)
        man_b = trial_ledger.twin_manifest(pass_b.out_dir)
        cmpres = trial_ledger.twin_compare(man_a, man_b)
        manifest_path = Path(run_root) / "twin_manifests.json"
        _write_atomic(manifest_path, json.dumps(
            {"pass_a": man_a, "pass_b": man_b, "compare": cmpres},
            indent=1, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        terminal["twin_compare"] = cmpres
        terminal["twin_manifests_path"] = str(manifest_path)

        # ---- 8. reconciliation
        recon = _reconcile(cfg, ids_frozen, pass_a, ledger,
                           pass_a.prior_output_missing)
        recon_path = Path(run_root) / "reconciliation.json"
        _write_atomic(recon_path, json.dumps(
            recon, indent=1, sort_keys=True, ensure_ascii=False)
            .encode("utf-8"))
        terminal["reconciliation_path"] = str(recon_path)
        terminal["reconciliation_pass"] = bool(recon["pass"])

        # ---- 9. terminal verdict (fail-closed law)
        reasons = []
        if pass_a.compute_failures or pass_b.compute_failures:
            reasons.append(TERMINAL_COMPUTE)
        if pass_a.publication_failures or pass_a.prior_output_missing:
            reasons.append(TERMINAL_PUBLICATION if
                           pass_a.publication_failures else
                           TERMINAL_PRIOR_MISSING)
        if not cmpres["byte_match"]:
            reasons.append(TERMINAL_TWIN_MISMATCH)
        if not recon["pass"]:
            reasons.append(TERMINAL_RECONCILIATION)
        summary = ledger.summary()
        if summary["observed_denominator"] != 24:
            reasons.append(TERMINAL_RECONCILIATION)
        terminal["failure_reasons"] = reasons
        # the computation+verify phase ran to completion either way; its
        # verdict is `reasons` — this flag is NOT the final verdict
        terminal["computation_complete"] = True
        if reasons:
            terminal["verdict"] = "EXECUTION_FAILED"
            terminal["terminal_state"] = reasons[0]
            terminal["exit_code"] = EXIT_FAILURE
        else:
            terminal["verdict"] = "EXECUTION_COMPLETE"
            terminal["terminal_state"] = TERMINAL_COMPLETE
            terminal["exit_code"] = EXIT_OK
            release_status = "FINISHED"
        terminal["ledger_summary"] = summary

    except SandboxFaultError as exc:
        terminal["failure_reasons"] = [TERMINAL_ABORTED]
        terminal["verdict"] = "EXECUTION_FAILED"
        terminal["terminal_state"] = TERMINAL_ABORTED
        terminal["exit_code"] = EXIT_FAILURE
        terminal["abort_reason"] = repr(exc)[:300]
        release_status = "TECHABORT"
    except Exception as exc:  # noqa: BLE001 — fail closed, always terminal
        terminal["failure_reasons"] = [TERMINAL_COMPUTE]
        terminal["verdict"] = "EXECUTION_FAILED"
        terminal["terminal_state"] = TERMINAL_COMPUTE
        terminal["exit_code"] = EXIT_FAILURE
        terminal["exception"] = repr(exc)[:1000]
        release_status = "FAILED"
    finally:
        # ---- 10. finalization cleanup in strict evidence order (D-7 law).
        # Every cleanup step runs in its OWN try and owns its errors: a
        # failure of one step is collected into finalization_failures[] and
        # can never mask the original execution error, never skip the
        # remaining cleanup, and never keep a success verdict. Ledger bytes,
        # the observed denominator and the computed results are NEVER
        # rewritten here (retry law untouched).
        terminal["finished_utc"] = _utcnow()
        if terminal.get("exit_code") is None:
            terminal["exit_code"] = EXIT_FAILURE
            terminal["terminal_state"] = terminal.get("terminal_state") \
                or TERMINAL_COMPUTE
        if terminal.get("exit_code") != EXIT_OK:
            release_status = ("TECHABORT"
                              if terminal.get("terminal_state") ==
                              TERMINAL_ABORTED else "FAILED")
        finalization_failures = terminal["finalization_failures"]

        # (a) ledger summary + file sha — a failure here is a finalization
        # failure (non-zero exit); rows already written stand and the bytes
        # are untouched
        try:
            if ledger is not None:
                terminal["ledger_summary"] = ledger.summary()
                terminal["ledger_file_sha256"] = sha256_file(
                    cfg["ledger_path"])
        except Exception as led_exc:  # noqa: BLE001
            terminal["ledger_summary_error"] = repr(led_exc)[:300]
            finalization_failures.append(
                {"stage": "ledger_summary", "error": repr(led_exc)[:300]})

        # (b) lock release — EVIDENCE LAW: `lock_released_status` is set
        # ONLY from measured evidence. A normal return claims the intended
        # FINISHED/FAILED/TECHABORT status; a RAISE never claims released —
        # the ACTUAL lock state is re-checked through the canonical
        # read-only heavy_lock.inspect() against the SAME runtime dir
        # (pre-restore) and recorded as evidence, and the run fails closed.
        # Never force-unlock, never kill workers, never delete lock files.
        if handle is not None:
            try:
                handle.release(status=release_status,
                               note=json.dumps(
                                   {"terminal_state":
                                    terminal.get("terminal_state"),
                                    "exit_code": terminal.get("exit_code")},
                                   sort_keys=True)[:500])
                terminal["lock_released_status"] = release_status
            except Exception as rel_exc:  # noqa: BLE001
                terminal["lock_release_error"] = repr(rel_exc)[:300]
                try:
                    terminal["lock_inspect_after_release_failure"] = \
                        heavy_lock.inspect()
                except Exception as insp_exc:  # noqa: BLE001
                    terminal["lock_inspect_after_release_failure"] = {
                        "verdict": "INSPECT_ERROR",
                        "reason": repr(insp_exc)[:300]}
                terminal["lock_released_status"] = "UNVERIFIED_RELEASE_RAISED"
                finalization_failures.append(
                    {"stage": "lock_release", "error": repr(rel_exc)[:300],
                     "lock_released_status": "UNVERIFIED_RELEASE_RAISED",
                     "inspect_verdict": (terminal[
                         "lock_inspect_after_release_failure"] or {})
                     .get("verdict")})

        # (c) runtime restore — its own try: cannot mask (a)/(b), cannot
        # skip (d)/(e); the sandbox redirect is always un-patched
        if restore_runtime is not None:
            try:
                restore_runtime()
            except Exception as rst_exc:  # noqa: BLE001
                terminal["runtime_restore_error"] = repr(rst_exc)[:300]
                finalization_failures.append(
                    {"stage": "runtime_restore",
                     "error": repr(rst_exc)[:300]})

        # (d) finalization verdict fixup — BEFORE the handoff write so the
        # handoff carries the final verdict. A computation-complete run
        # with any finalization failure becomes FINALIZATION_FAILURE
        # (exit 4), NEVER EXECUTION_COMPLETE. An already-failed run keeps
        # its original terminal state (the original error is never masked);
        # its finalization dimension lives in finalization_failures[].
        # Refusal exits (2/75) stand unchanged (non-zero, fail-closed).
        if finalization_failures and \
                terminal.get("exit_code") == EXIT_OK:
            terminal["verdict"] = "EXECUTION_FAILED"
            terminal["terminal_state"] = TERMINAL_FINALIZATION
            terminal["failure_reasons"] = [TERMINAL_FINALIZATION]
            terminal["exit_code"] = EXIT_FINALIZATION

        # (e) terminal handoff — the handoff carries the FINAL verdict. A
        # write failure (OSError) is a finalization failure: non-zero exit,
        # `terminal_handoff_path` is NEVER claimed, best-effort fallback
        # diagnostics are attempted under terminal_handoff_ERROR.json with
        # whatever fields serialize — and if even that fails, the record
        # exists IN-MEMORY ONLY (the returned terminal dict is the
        # last-resort record; no artifact existence is ever claimed).
        handoff_path = Path(cfg["run_root"]) / "terminal_handoff.json"
        handoff = dict(terminal)
        handoff["schema"] = SCHEMA_HANDOFF
        handoff["next_hook"] = "post-GO terminal A7"
        try:
            _write_atomic(handoff_path, json.dumps(
                handoff, indent=1, sort_keys=True, ensure_ascii=False)
                .encode("utf-8"))
            terminal["terminal_handoff_path"] = str(handoff_path)
        except OSError as exc:
            terminal["terminal_handoff_error"] = repr(exc)[:300]
            finalization_failures.append(
                {"stage": "terminal_handoff", "error": repr(exc)[:300]})
            # the handoff failure is itself a finalization failure: apply
            # the same verdict fixup if the run was otherwise clean
            if terminal.get("exit_code") == EXIT_OK:
                terminal["verdict"] = "EXECUTION_FAILED"
                terminal["terminal_state"] = TERMINAL_FINALIZATION
                terminal["failure_reasons"] = [TERMINAL_FINALIZATION]
                terminal["exit_code"] = EXIT_FINALIZATION
            # keep the fallback copy consistent with the fixed-up verdict
            for _k in ("verdict", "terminal_state", "failure_reasons",
                       "exit_code"):
                handoff[_k] = terminal.get(_k)
            handoff["terminal_handoff_error"] = \
                terminal["terminal_handoff_error"]
            handoff["terminal_handoff_primary_path_unclaimed"] = True
            try:
                fallback_path = Path(cfg["run_root"]) / \
                    "terminal_handoff_ERROR.json"
                _write_atomic(fallback_path, json.dumps(
                    handoff, indent=1, sort_keys=True, ensure_ascii=False,
                    default=str).encode("utf-8"))
                terminal["terminal_handoff_fallback_path"] = \
                    str(fallback_path)
            except Exception as fb_exc:  # noqa: BLE001 — in-memory only
                terminal["terminal_handoff_fallback_error"] = \
                    repr(fb_exc)[:300]
                terminal["terminal_handoff_recorded"] = "IN_MEMORY_ONLY"

    return int(terminal["exit_code"]), terminal
