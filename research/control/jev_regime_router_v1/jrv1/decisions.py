"""Decision boundary for jrv1: cache reader, schema validation, merging.

Boundary schema `jrv1_decision_io@1` (JSONL), amended per amendment_1
(A7-1 F1, producer-digest echo law):
- request line  {schema, state_id, state, requested_model, input_digest}
  where input_digest is computed by the PRODUCER (Python) from its stored
  state + requested_model via its canonical_json.
- response line {schema, state_id, status, regime?, probabilities?,
  confidence?, model?, request_id?, input_digest, latency_ms, error_class?}
  where input_digest is the VERBATIM ECHO of the request digest (TS never
  recomputes it — a single canonicalization authority avoids the measured
  cross-language float-formatting divergence).

input_digest = sha256(canonical_json(state) || requested_model) — computed by
the producer only; Python ingest recomputes from its own state (authoritative)
and compares to the echoed digest; mismatch = SCHEMA_ERROR ->
TRANSITION_UNKNOWN + incident.

Validation law (violations are COUNTED and the decision becomes
TRANSITION_UNKNOWN; never a crash, never a pass-through):
- status must be one of OK|TIMEOUT|PROVIDER_ERROR|SCHEMA_ERROR|LOCAL_INVALID
- free-text regime (not one of the 5 frozen labels) -> SCHEMA_ERROR -> UNKNOWN
- probabilities must cover all 5 labels, be non-negative and sum to 1±0.01
  -> otherwise UNKNOWN
- model must equal the pinned model whenever a pin exists
- one call per state_id; the cache is append-only and immutable: a duplicate
  request for the same state_id is an incident (identical duplicate ignored,
  divergent duplicate flagged).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from . import DECISION_IO_SCHEMA, LABELS
from .features import state_payload
from .freezes import Freezes, canonical_json
from .persistence import UNKNOWN, PersistedBar, PersistenceState, raw_from_response, step
from .security import safe_open

ALLOWED_STATUS = ("OK", "TIMEOUT", "PROVIDER_ERROR", "SCHEMA_ERROR", "LOCAL_INVALID")
DIGEST_SEPARATOR = ""  # canonical_json(state) || requested_model, no separator


def compute_input_digest(state: dict, requested_model: str) -> str:
    return hashlib.sha256(
        (canonical_json(state) + requested_model).encode("utf-8")
    ).hexdigest()


def validate_response_line(
    line: dict,
    expected_state_id: str,
    expected_digest: str,
    pinned_model: str | None = None,
) -> tuple[dict | None, str | None]:
    """Validate one response line. Returns (normalized|None, violation|None).

    normalized = {'state_id','status','regime','probabilities','confidence'}
    with any violation coerced to status SCHEMA_ERROR (decision UNKNOWN).
    """
    if line.get("schema") != DECISION_IO_SCHEMA:
        return _bad(line, expected_state_id, "schema_field")
    if line.get("state_id") != expected_state_id:
        return _bad(line, expected_state_id, "state_id_mismatch")
    if line.get("input_digest") != expected_digest:
        return _bad(line, expected_state_id, "input_digest_mismatch")
    status = line.get("status")
    if status not in ALLOWED_STATUS:
        return _bad(line, expected_state_id, "bad_status")
    if status != "OK":
        return _normalized(line, expected_state_id, status, None, None, None), None
    regime = line.get("regime")
    if regime not in LABELS:
        return _bad(line, expected_state_id, "free_text_regime")
    probs = line.get("probabilities")
    if not isinstance(probs, dict):
        return _bad(line, expected_state_id, "missing_probabilities")
    vals = []
    for lab in LABELS:
        v = probs.get(lab)
        if not isinstance(v, (int, float)) or v != v or v < 0:
            return _bad(line, expected_state_id, "bad_probabilities")
        vals.append(float(v))
    if abs(sum(vals) - 1.0) > 0.01:
        return _bad(line, expected_state_id, "probability_sum")
    if pinned_model is not None and line.get("model") != pinned_model:
        return _bad(line, expected_state_id, "model_pin_mismatch")
    conf = line.get("confidence")
    if not isinstance(conf, (int, float)) or conf != conf:
        return _bad(line, expected_state_id, "bad_confidence")
    return (
        _normalized(line, expected_state_id, "OK", regime, {l: float(v) for l, v in zip(LABELS, vals)}, float(conf)),
        None,
    )


def _normalized(line, state_id, status, regime, probs, conf) -> dict:
    return {
        "state_id": state_id,
        "status": status,
        "regime": regime,
        "probabilities": probs,
        "confidence": conf,
    }


def _bad(line, state_id, violation) -> tuple[dict, str]:
    return (
        _normalized(line, state_id, "SCHEMA_ERROR", None, None, None),
        violation,
    )


class DecisionStore:
    """Append-only decision cache (runtime/decisions_<asset>.jsonl)."""

    def __init__(self) -> None:
        self.by_state_id: dict[str, dict] = {}
        self.incidents: list[dict] = []
        self.lines_seen = 0

    def ingest_line(self, line: dict) -> None:
        self.lines_seen += 1
        sid = line.get("state_id")
        if not isinstance(sid, str) or len(sid) != 16:
            self.incidents.append({"type": "bad_state_id", "line": self.lines_seen})
            return
        if sid in self.by_state_id:
            self.incidents.append(
                {
                    "type": "duplicate_request",
                    "state_id": sid,
                    "identical": self.by_state_id[sid] == line,
                }
            )
            return
        self.by_state_id[sid] = line

    @classmethod
    def load(cls, path: str | Path) -> "DecisionStore":
        store = cls()
        p = Path(path)
        if not p.exists():
            return store
        with safe_open(p, "rb") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    line = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    store.incidents.append({"type": "corrupt_line", "line": store.lines_seen + 1})
                    continue
                store.ingest_line(line)
        return store

    def append(self, path: str | Path, line: dict) -> None:
        """Append-only write; refuses to rewrite an existing state_id."""
        sid = line.get("state_id")
        if sid in self.by_state_id:
            raise ValueError(f"cache immutability: state {sid} already present")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with safe_open(p, "ab") as f:
            f.write((json.dumps(line, sort_keys=True) + "\n").encode("utf-8"))
        self.ingest_line(line)


class Timeline:
    """Persisted regime timeline over regime bars (from warmup)."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    @property
    def ts(self) -> list[int]:
        return [r["regime_bar_close_ns"] for r in self.rows]

    @property
    def persisted(self) -> list[str]:
        return [r["persisted"] for r in self.rows]

    @property
    def raw(self) -> list[str]:
        return [r["raw"] for r in self.rows]

    def stats(self) -> dict:
        n = len(self.rows)
        switches = sum(1 for r in self.rows if r["switched"])
        occ: dict[str, int] = {l: 0 for l in LABELS}
        for r in self.rows:
            occ[r["persisted"]] += 1
        unknown = sum(1 for r in self.rows if r["raw"] == UNKNOWN)
        return {
            "n_decisions": n,
            "switches": switches,
            "occupancy": {k: v / n if n else 0.0 for k, v in occ.items()},
            "raw_unknown_share": unknown / n if n else 0.0,
            "incidents": sum(len(r.get("violations", [])) for r in self.rows),
        }


def sequential_timeline(
    asset: str,
    fz: Freezes,
    regime_bars,
    feats,
    provider,
    pinned_model: str | None = None,
    requested_model: str = "UNPINNED",
    strict: bool = True,
    request_sink: list | None = None,
) -> Timeline:
    """Authoritative sequential decision + persistence walk.

    provider(state_id, payload) -> response line dict | None.
    - LOCAL_INVALID states are NEVER sent (status LOCAL_INVALID, UNKNOWN).
    - prior_regime for bar t is the persisted state in force at t-1.
    - strict=True (scoring): a cache miss raises DecisionsIncomplete.
      strict=False (prepare mode): emits the request line and advances with
      an UNKNOWN-candidate; batch priors before a fixpoint re-run are
      provisional by construction (documented).
    """
    params = fz.persistence_params()
    st = PersistenceState(**params)
    prior_labels: list[str | None] = [None] * feats.T
    rows: list[dict] = []
    missing = 0
    for t in range(fz.feature_contract["warmup_regime_bars"], feats.T):
        vec = feats.vector_at(t)
        ts_close = int(regime_bars.ts_close[t])
        sid = fz.state_id(asset, ts_close)
        if vec is None:
            rows.append(
                {
                    "bar_index": t,
                    "regime_bar_close_ns": ts_close,
                    "state_id": sid,
                    "status": "LOCAL_INVALID",
                    "raw": UNKNOWN,
                    "eligible": False,
                    "persisted": st.current,
                    "switched": False,
                    "violations": [],
                }
            )
            prior_labels[t] = st.current
            continue
        payload = state_payload(
            {
                "feature_vector": vec,
                "prior_regime": prior_labels[t - 1] if t - 1 >= 0 else None,
                "local_invalid": False,
            }
        )
        digest = compute_input_digest(payload, requested_model)
        if request_sink is not None:
            request_sink.append(
                {
                    "schema": DECISION_IO_SCHEMA,
                    "state_id": sid,
                    "state": payload,
                    "requested_model": requested_model,
                    "input_digest": digest,
                }
            )
        line = provider(sid, payload)
        if line is None:
            missing += 1
            if strict:
                raise DecisionsIncomplete(
                    f"missing decision for state {sid} (bar {t})"
                )
            normalized, violation = None, "cache_miss"
            status = UNKNOWN
            eff = None
        else:
            normalized, violation = validate_response_line(line, sid, digest, pinned_model)
            eff = normalized
        raw, eligible = raw_from_response(eff, params)
        switched = step(st, raw, eligible)
        prior_labels[t] = st.current
        rows.append(
            {
                "bar_index": t,
                "regime_bar_close_ns": ts_close,
                "state_id": sid,
                "status": (eff or {}).get("status", "MISSING"),
                "raw": raw,
                "eligible": eligible,
                "persisted": st.current,
                "switched": switched,
                "violations": [violation] if violation else [],
            }
        )
    tl = Timeline(rows)
    tl.missing = missing
    return tl


class DecisionsIncomplete(RuntimeError):
    """Arm E/F scoring requires a complete decision cache (fail-closed)."""


class CacheProvider:
    """Provider backed by a DecisionStore; returns None on miss."""

    def __init__(self, store: DecisionStore) -> None:
        self.store = store

    def __call__(self, state_id: str, payload: dict) -> dict | None:
        return self.store.by_state_id.get(state_id)
