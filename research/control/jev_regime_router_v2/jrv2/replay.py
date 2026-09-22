"""Sequential replay loop + historical preview (V1 F2 law carried over).

REPLAY — the ONLY legal bulk decision mechanism (V1 A7-1 F2 law): a STRICT
sequential per-state loop:
  for each decision state t in order:
    1. build the NAMED SEMANTIC STATE with prior fields = persisted effective
       regime in force at t-1 (recomputed from the persistence machine after
       EVERY merged response),
    2. emit ONE request line (producer-computed input_digest, amendment_1),
    3. invoke the TS adapter once for that single state (subprocess; cache
       first; the decision cache is consulted BEFORE the call so an
       interrupted run resumes exactly),
    4. validate the response (three typed questions), ingest + persist,
       advance safety + persistence,
    5. continue.
Adapter exit != 0 is a HARD FAIL (no silent partial bulk). Cache-first
resume: cached lines are re-validated against the CURRENT recomputed digest.

PREVIEW (canary_v2_contract historical preview): classification-only, no
PnL, <= 100 BTC_H1 states sampled by the preregistered timestamp rule
i_k = floor(k*8567/100), k=0..99 (dedup). prior fields of sampled state k
are taken from the last SAMPLED predecessor (preview-only approximation;
bulk uses the strict sequential law). Collapse criteria FAIL-STOP with
measured numbers: any single effective label > 90% OR effective
TRANSITION_UNKNOWN > 80%.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from . import QUESTION_IO_SCHEMA
from .questionio import (
    DecisionStore,
    compute_input_digest,
    validate_response_line,
)
from .features import semantic_state, state_payload
from .freezes import Freezes
from .safety import UNKNOWN, PersistenceState, effective_from_response, step
from .security import safe_open

REPLAY_PROGRESS_SCHEMA = "jrv2_replay_progress@1"
REPLAY_RESULT_SCHEMA = "jrv2_replay_result@1"
PREVIEW_RESULT_SCHEMA = "jrv2_preview_result@1"


class ReplayError(RuntimeError):
    """Hard failure of the sequential replay loop (adapter crashed, bad I/O)."""


class PreviewCollapse(RuntimeError):
    """Preview collapse criteria fired: STOP, no bulk (measured numbers in payload)."""

    def __init__(self, payload: dict) -> None:
        super().__init__("PREVIEW_COLLAPSE_STOP")
        self.payload = payload


def preview_indices_rule(n_decisions: int, n_preview: int) -> list[int]:
    """Preregistered sampling rule i_k = floor(k*n/n_preview), k=0..n-1, dedup,
    ascending. Must reproduce the frozen preview_indices for (8567, 100)."""
    return sorted({int(k * n_decisions / n_preview) for k in range(n_preview)})


def _invoke_adapter(
    node_bin: str,
    adapter_ts: Path,
    request_file: Path,
    out_file: Path,
    cache_dir: Path,
    mock: bool,
    requested_model: str,
) -> str:
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
        tail = "\n".join(proc.stderr.strip().split("\n")[-5:])
        raise ReplayError(
            f"adapter exited {proc.returncode} for request {request_file.name}; "
            f"aborting replay (no silent partial). stderr tail:\n{tail}"
        )
    # cost evidence law: the adapter's stdout summary JSON (usage + counters)
    # is preserved verbatim — one append-only line per adapter invocation.
    return proc.stdout


def run_replay(
    fz: Freezes,
    cell: str,
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
    """Strictly sequential per-state decision loop through the TS adapter."""
    from . import CELLS

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
    summaries_path = decisions_path.parent / f"adapter_summaries_{cell}.jsonl"
    n_summaries = 0

    asset = CELLS[cell]["asset"]
    warmup = fz.warmup(cell)
    rows: list[dict] = []
    n_sent = 0
    n_cached = 0
    n_local_invalid = 0
    incidents: list[dict] = []
    persisted_by_index: list[str | None] = [None] * feats.T

    def _progress(k: int) -> None:
        if progress is not None:
            progress(
                {
                    "schema": REPLAY_PROGRESS_SCHEMA,
                    "cell": cell,
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
        ts_close = int(regime_bars.ts_close[t])
        sid = fz.state_id(asset, ts_close)
        state = semantic_state(
            asset, fz, regime_bars, t, feats,
            persisted_by_index[t - 1] if t > 0 else None,
        )
        if state is None:
            # LOCAL_INVALID states are NEVER sent (frozen law)
            n_local_invalid += 1
            switched = step(st, UNKNOWN, False)
            persisted_by_index[t] = st.current
            rows.append(
                {
                    "state_id": sid,
                    "bar_index": t,
                    "prior_structure": "none",
                    "prior_direction": "none",
                    "status": "LOCAL_INVALID",
                    "effective": UNKNOWN,
                    "persisted_after": st.current,
                    "switched": switched,
                    "sent": False,
                    "cached": False,
                }
            )
            processed += 1
            if processed % progress_every == 0:
                _progress(processed)
            continue

        payload = state_payload(state)
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
                "schema": QUESTION_IO_SCHEMA,
                "state_id": sid,
                "state": payload,
                "requested_model": requested_model,
                "input_digest": digest,
            }
            with safe_open(request_file, "w") as f:
                f.write(json.dumps(line, sort_keys=True) + "\n")
            if out_file.exists():
                out_file.unlink()
            adapter_stdout = _invoke_adapter(
                node_bin, adapter_ts, request_file, out_file, adapter_cache_dir,
                mock, requested_model,
            )
            summary_text = (adapter_stdout or "").strip()
            if summary_text:
                for chunk in summary_text.split("\n"):
                    if chunk.strip():
                        with safe_open(summaries_path, "a") as f:
                            f.write(chunk.strip() + "\n")
                        n_summaries += 1
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
        label, eligible, reason = effective_from_response(normalized, params)
        switched = step(st, label, eligible)
        persisted_by_index[t] = st.current
        rows.append(
            {
                "state_id": sid,
                "bar_index": t,
                "prior_structure": payload["prior_structure"],
                "prior_direction": payload["prior_direction"],
                "status": (normalized or {}).get("status", "MISSING"),
                "effective": label,
                "effective_reason": reason,
                "persisted_after": st.current,
                "switched": switched,
                "sent": sent,
                "cached": cached,
            }
        )
        processed += 1
        if processed % progress_every == 0:
            _progress(processed)

    new_incidents = store.incidents[prior_incidents:]
    return {
        "schema": REPLAY_RESULT_SCHEMA,
        "cell": cell,
        "mock": mock,
        "adapter_model": requested_model,
        "n_states": processed,
        "n_sent": n_sent,
        "n_cached": n_cached,
        "n_local_invalid": n_local_invalid,
        "n_incidents": len(incidents),
        "n_adapter_summaries": n_summaries,
        "adapter_summaries_path": str(summaries_path),
        "digest_mismatches": sum(1 for i in incidents if i["type"] == "input_digest_mismatch"),
        "cache_incidents": [
            {"state_id": i.get("state_id"), "type": i.get("type")} for i in new_incidents
        ],
        "incidents": incidents,
        "rows": rows,
        "decisions_path": str(decisions_path),
    }


# ---------------------------------------------------------------------------
# historical preview (canary_v2_contract)
# ---------------------------------------------------------------------------


def run_preview(
    fz: Freezes,
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
) -> dict:
    """Classification-only historical preview over the 100 preregistered
    BTC_H1 states. Fail-stops via PreviewCollapse when a collapse criterion
    fires (measured numbers in the payload)."""
    from . import CELLS

    preview = fz.canary_contract["historical_preview"]
    cell = preview["cell"]
    n_decisions = int(fz.fold_contract["cells"][cell]["evaluable_decisions"])
    rule_indices = preview_indices_rule(n_decisions, preview["max_states"])
    frozen = preview["preview_indices"]
    if rule_indices != sorted(frozen):
        raise ReplayError(
            "preview sampling rule does not reproduce the frozen preview_indices"
        )

    asset = CELLS[cell]["asset"]
    warmup = fz.warmup(cell)
    params = fz.persistence_params()
    st = PersistenceState(**params)
    store = DecisionStore.load(decisions_path)
    prior_incidents = len(store.incidents)

    if adapter_ts is None:
        adapter_ts = fz.cycle_dir / "adapter" / "src" / "adapter.ts"
    request_file = Path(tmp_dir) / "preview_req_1line.jsonl"
    out_file = Path(tmp_dir) / "preview_resp_1line.jsonl"
    for d in (Path(tmp_dir), Path(adapter_cache_dir), Path(decisions_path).parent):
        d.mkdir(parents=True, exist_ok=True)

    rows = []
    n_sent = 0
    n_cached = 0
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    total_latency_ms = 0.0
    for j, idx in enumerate(rule_indices):
        t = warmup + idx
        if t >= feats.T:
            raise ReplayError(f"preview index {idx} outside decision range")
        ts_close = int(regime_bars.ts_close[t])
        sid = fz.state_id(asset, ts_close)
        # preview-only prior approximation: last SAMPLED predecessor
        prior = st.current if rows else None
        state = semantic_state(asset, fz, regime_bars, t, feats, prior)
        if state is None:
            label, eligible = UNKNOWN, False
            rows.append({"k": j, "index": idx, "state_id": sid, "effective": label, "sent": False})
            step(st, label, eligible)
            continue
        payload = state_payload(state)
        digest = compute_input_digest(payload, requested_model)
        cached_line = store.by_state_id.get(sid)
        if cached_line is not None:
            normalized, violation = validate_response_line(cached_line, sid, digest, pinned_model)
            n_cached += 1
        else:
            line = {
                "schema": QUESTION_IO_SCHEMA,
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
                node_bin, Path(adapter_ts), request_file, out_file,
                Path(adapter_cache_dir), mock, requested_model,
            )
            with safe_open(out_file, "rb") as f:
                out_lines = [ln for ln in f.read().decode("utf-8").split("\n") if ln.strip()]
            if len(out_lines) != 1:
                raise ReplayError(f"preview: expected 1 response line for {sid}")
            line = json.loads(out_lines[0])
            normalized, violation = validate_response_line(line, sid, digest, pinned_model)
            store.append(decisions_path, line)
            n_sent += 1
        if normalized and normalized.get("usage"):
            total_usage["input_tokens"] += int(normalized["usage"]["input_tokens"])
            total_usage["output_tokens"] += int(normalized["usage"]["output_tokens"])
        label, eligible, reason = effective_from_response(normalized, params)
        step(st, label, eligible)
        rows.append(
            {
                "k": j,
                "index": idx,
                "state_id": sid,
                "effective": label,
                "effective_reason": reason,
                "persisted_after": st.current,
                "violation": violation,
                "sent": True,
            }
        )

    n = len(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["effective"]] = counts.get(r["effective"], 0) + 1
    shares = {k: v / n for k, v in counts.items()}
    unknown_share = shares.get(UNKNOWN, 0.0)
    max_label, max_share = max(shares.items(), key=lambda kv: kv[1])
    collapse_checks = [
        {
            "criterion": "any_single_effective_label > 0.90",
            "measured": {"label": max_label, "share": max_share},
            "fired": bool(max_share > 0.90),
        },
        {
            "criterion": "effective_TRANSITION_UNKNOWN > 0.80",
            "measured": {"share": unknown_share},
            "fired": bool(unknown_share > 0.80),
        },
    ]
    result = {
        "schema": PREVIEW_RESULT_SCHEMA,
        "cell": cell,
        "mock": mock,
        "n_sampled": n,
        "sampling_rule": preview["sampling_rule"],
        "prior_rule": preview["prior_rule"],
        "classification_only": True,
        "effective_label_counts": counts,
        "effective_label_shares": shares,
        "usage_totals": total_usage,
        "total_latency_ms": total_latency_ms + _latencies_of(rows),
        "new_incidents": store.incidents[prior_incidents:],
        "collapse_checks": collapse_checks,
        "collapsed": any(c["fired"] for c in collapse_checks),
        "decisions_path": str(decisions_path),
        "rows": rows,
    }
    if result["collapsed"]:
        raise PreviewCollapse(result)
    return result


def _latencies_of(rows: list[dict]) -> float:
    return 0.0  # latency accumulates from adapter summaries in the caller


def fixture_request_lines(fz: Freezes, requested_model: str) -> list[dict]:
    """Request lines for the frozen synthetic canaries: FIXED priors from the
    freeze, NO persistence dependency. LOCAL_INVALID fixtures (state null)
    are never serialized for a provider. state_id is a deterministic opaque
    fixture tag: sha256('JRV2-fixture:'+id)[:16]."""
    from .features import normalize_semantic_state

    lines = []
    for fx in fz.canary_contract["synthetic_fixtures"]:
        if fx["state"] is None:
            continue
        payload = normalize_semantic_state(fx["state"])
        sid = hashlib.sha256(("JRV2-fixture:" + fx["id"]).encode("utf-8")).hexdigest()[:16]
        lines.append(
            {
                "schema": QUESTION_IO_SCHEMA,
                "state_id": sid,
                "state": payload,
                "requested_model": requested_model,
                "input_digest": compute_input_digest(payload, requested_model),
            }
        )
    return lines
