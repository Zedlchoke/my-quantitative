"""Sequential replay loop (A7-1 F2) — the ONLY legal bulk decision mechanism.

Law (amendment to the bulk runbook, A7-1 F2): ``prepare-requests`` batch mode
carries provisional priors (f17 depends on prior decisions, which depend on
the calls), so any naive batch bulk would fail-close to ~all-UNKNOWN at
scoring and the fixpoint re-call is impossible under one-call-per-state cache
immutability. The only correct design is a STRICT sequential per-state loop:

  for each decision state t in order:
    1. build the state with prior_regime = persisted regime in force at t-1
       (recomputed from persistence after EVERY merged response),
    2. emit ONE request line (with the producer-computed input_digest,
       amendment_1),
    3. invoke the TS adapter once for that single state (subprocess; cache
       first: the adapter replay-reads its own cache; the decision cache is
       consulted BEFORE the call so an interrupted run resumes exactly),
    4. read the single response line, validate it against the authoritative
       local digest recompute, ingest + persist it, advance persistence,
    5. continue.

Cache-first resume: a state already present in the decision cache is never
re-called; its cached line is re-validated against the current recomputed
digest (a stale/divergent cached line fail-closes to SCHEMA_ERROR incident,
never silently accepted).

Adapter exit != 0 is a HARD FAIL (non-zero exit, loud error): no silent
partial bulk. States already ingested before the failure remain in the
append-only decision cache (that is the resume mechanism, not a silent
partial).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from . import DECISION_IO_SCHEMA
from .decisions import (
    DecisionStore,
    compute_input_digest,
    validate_response_line,
)
from .features import state_payload
from .freezes import Freezes
from .persistence import UNKNOWN, PersistenceState, raw_from_response, step
from .security import safe_open

REPLAY_MOCK_MODEL = "mock-pin-1"
REPLAY_PROGRESS_SCHEMA = "jrv1_replay_progress@1"
REPLAY_RESULT_SCHEMA = "jrv1_replay_result@1"


class ReplayError(RuntimeError):
    """Hard failure of the sequential replay loop (adapter crashed, bad I/O)."""


def _invoke_adapter(
    node_bin: str,
    adapter_ts: Path,
    request_file: Path,
    out_file: Path,
    cache_dir: Path,
    mock: bool,
    requested_model: str,
) -> None:
    cmd = [
        node_bin,
        str(adapter_ts),
        "--requests",
        str(request_file),
        "--out",
        str(out_file),
        "--cache",
        str(cache_dir),
        "--model",
        requested_model,
    ]
    if mock:
        cmd.append("--mock")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # HARD FAIL: never continue past a broken adapter; stderr is adapter
        # chatter (redaction-safe by adapter law) — include a trimmed tail.
        tail = "\n".join(proc.stderr.strip().split("\n")[-5:])
        raise ReplayError(
            f"adapter exited {proc.returncode} for request {request_file.name}; "
            f"aborting replay (no silent partial). stderr tail:\n{tail}"
        )


def run_replay(
    fz: Freezes,
    asset: str,
    regime_bars,
    feats,
    requested_model: str,
    pinned_model: str | None,
    mock: bool,
    decisions_path: str | Path,
    adapter_cache_dir: str | Path,
    tmp_dir: str | Path,
    node_bin: str = "node",
    adapter_ts: str | Path | None = None,
    limit: int | None = None,
    progress_every: int = 100,
    progress=None,
) -> dict:
    """Strictly sequential per-state decision loop through the TS adapter.

    See module docstring for the law. Returns a result dict with per-state
    rows (state_id, prior_regime, persisted_after, status, sent) and incident
    counters; ``digest_mismatches`` must be 0 for a sound run.
    """
    if adapter_ts is None:
        adapter_ts = fz.cycle_dir / "adapter" / "src" / "adapter.ts"
    adapter_ts = Path(adapter_ts)
    if not adapter_ts.exists():
        raise ReplayError(f"adapter not found: {adapter_ts}")
    decisions_path = Path(decisions_path)
    adapter_cache_dir = Path(adapter_cache_dir)
    tmp_dir = Path(tmp_dir)
    for d in (tmp_dir, adapter_cache_dir, decisions_path.parent):
        d.mkdir(parents=True, exist_ok=True)

    params = fz.persistence_params()
    st = PersistenceState(**params)
    store = DecisionStore.load(decisions_path)
    prior_incidents = len(store.incidents)

    request_file = tmp_dir / "req_1line.jsonl"
    out_file = tmp_dir / "resp_1line.jsonl"

    warmup = fz.feature_contract["warmup_regime_bars"]
    rows: list[dict] = []
    n_sent = 0
    n_cached = 0
    n_local_invalid = 0
    incidents: list[dict] = []
    prior: str | None = None  # persisted regime in force at t-1

    def _progress(k: int) -> None:
        if progress is not None:
            progress(
                {
                    "schema": REPLAY_PROGRESS_SCHEMA,
                    "asset": asset,
                    "mock": mock,
                    "n_processed": k,
                    "n_sent": n_sent,
                    "n_cached": n_cached,
                    "n_local_invalid": n_local_invalid,
                    "n_incidents": len(incidents),
                }
            )

    processed = 0
    for t in range(warmup, feats.T):
        if limit is not None and processed >= limit:
            break
        vec = feats.vector_at(t)
        ts_close = int(regime_bars.ts_close[t])
        sid = fz.state_id(asset, ts_close)
        if vec is None:
            # LOCAL_INVALID states are NEVER sent (frozen law)
            n_local_invalid += 1
            switched = step(st, UNKNOWN, False)
            rows.append(
                {
                    "state_id": sid,
                    "bar_index": t,
                    "prior_regime": prior,
                    "status": "LOCAL_INVALID",
                    "persisted_after": st.current,
                    "switched": switched,
                    "sent": False,
                    "cached": False,
                }
            )
            prior = st.current
            processed += 1
            if processed % progress_every == 0:
                _progress(processed)
            continue

        payload = state_payload(
            {
                "feature_vector": vec,
                "prior_regime": prior,
                "local_invalid": False,
            }
        )
        digest = compute_input_digest(payload, requested_model)
        cached_line = store.by_state_id.get(sid)
        if cached_line is not None:
            # cache-first resume: never re-call; re-validate against the
            # CURRENT authoritative recompute (stale line -> incident)
            normalized, violation = validate_response_line(cached_line, sid, digest, pinned_model)
            sent, cached = False, True
            n_cached += 1
        else:
            line = {
                "schema": DECISION_IO_SCHEMA,
                "state_id": sid,
                "state": payload,
                "requested_model": requested_model,
                "input_digest": digest,
            }
            with safe_open(request_file, "w") as f:
                f.write(json.dumps(line, sort_keys=True) + "\n")
            if out_file.exists():
                out_file.unlink()
            _invoke_adapter(
                node_bin, adapter_ts, request_file, out_file, adapter_cache_dir,
                mock, requested_model,
            )
            with safe_open(out_file, "rb") as f:
                out_lines = [ln for ln in f.read().decode("utf-8").split("\n") if ln.strip()]
            if len(out_lines) != 1:
                raise ReplayError(
                    f"adapter returned {len(out_lines)} response lines for state {sid} (expected 1)"
                )
            line = json.loads(out_lines[0])
            normalized, violation = validate_response_line(line, sid, digest, pinned_model)
            store.append(decisions_path, line)  # append-only; refuses rewrites
            sent, cached = True, False
            n_sent += 1
        if violation is not None:
            incidents.append({"state_id": sid, "type": violation})
        raw, eligible = raw_from_response(normalized, params)
        switched = step(st, raw, eligible)
        rows.append(
            {
                "state_id": sid,
                "bar_index": t,
                "prior_regime": prior,
                "status": (normalized or {}).get("status", "MISSING"),
                "persisted_after": st.current,
                "switched": switched,
                "sent": sent,
                "cached": cached,
            }
        )
        prior = st.current
        processed += 1
        if processed % progress_every == 0:
            _progress(processed)

    new_incidents = store.incidents[prior_incidents:]
    return {
        "schema": REPLAY_RESULT_SCHEMA,
        "asset": asset,
        "mock": mock,
        "adapter_model": requested_model,
        "n_states": processed,
        "n_sent": n_sent,
        "n_cached": n_cached,
        "n_local_invalid": n_local_invalid,
        "n_incidents": len(incidents),
        "digest_mismatches": sum(1 for i in incidents if i["type"] == "input_digest_mismatch"),
        "cache_incidents": [
            {"state_id": i.get("state_id"), "type": i.get("type")} for i in new_incidents
        ],
        "incidents": incidents,
        "rows": rows,
        "decisions_path": str(decisions_path),
    }


def fixture_request_lines(fz: Freezes, requested_model: str) -> list[dict]:
    """Request lines for the frozen synthetic canaries (prepare-requests
    --fixtures-only): FIXED priors from the freeze, NO persistence dependency.

    LOCAL_INVALID fixtures (vector null) are never serialized for a provider.
    state_id is a deterministic opaque fixture tag: sha256('JRV1-fixture:'+id)[:16].
    """
    lines = []
    for fx in fz.canary_fixtures["fixtures"]:
        if fx["vector"] is None:
            continue
        payload = {
            "feature_vector": [float(x) for x in fx["vector"]],
            "prior_regime": fx["prior_regime"],
        }
        sid = hashlib.sha256(("JRV1-fixture:" + fx["id"]).encode("utf-8")).hexdigest()[:16]
        lines.append(
            {
                "schema": DECISION_IO_SCHEMA,
                "state_id": sid,
                "state": payload,
                "requested_model": requested_model,
                "input_digest": compute_input_digest(payload, requested_model),
            }
        )
    return lines
