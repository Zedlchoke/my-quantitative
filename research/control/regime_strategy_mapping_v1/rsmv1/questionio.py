"""Decision boundary for jrv2: schema validation, digests, append-only cache.

Boundary schema `jrv2_question_io@1` (JSONL), one systemOne call per state
carrying THREE typed questions (structure 2-choice, direction 3-choice,
phase 4-choice FORCED — the model can never abstain):

- request line  {schema, state_id, state, requested_model, input_digest}
  where state is the NAMED SEMANTIC STATE
  {bins, numerics, prior_structure, prior_direction} and input_digest is
  computed by the PRODUCER (Python) from its canonical_json(state) ||
  requested_model (V1 amendment_1 law — single canonicalization authority).
- response line {schema, state_id, status,
  answers?{structure,direction,phase each {choice,probabilities,confidence}},
  model?, request_id?, input_digest, latency_ms,
  usage?{input_tokens,output_tokens}, prior_direction?, error_class?,
  cached?, mock?, namespace?}

input_digest is the VERBATIM ECHO of the request digest (TS never
recomputes it); Python ingest recomputes from its own state (authoritative)
and compares — mismatch = SCHEMA_ERROR -> code UNKNOWN + incident.

Validation law (violations are COUNTED and the decision becomes
TRANSITION_UNKNOWN via the safety layer; never a crash, never a pass-through):
- status must be one of OK|TIMEOUT|PROVIDER_ERROR|SCHEMA_ERROR|LOCAL_INVALID
- phase choice MUST be one of the 4 schema phases; any fifth label,
  TRANSITION_UNKNOWN or UNKNOWN-equivalent is a SCHEMA_ERROR
  (forced-choice law)
- each question's probabilities must cover exactly its option set, be
  non-negative and sum to 1 +/- 0.01
- model must equal the pinned model whenever a pin exists
- usage (input/output tokens) must be present on OK responses
  (persisted per response — V1 design note fixed)
- cache is append-only and immutable: a duplicate request for the same
  state_id is an incident (identical duplicate ignored, divergent flagged).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import DIRECTIONS, PHASES, QUESTION_IO_SCHEMA, STRUCTURES
from .features import state_payload
from .freezes import Freezes, canonical_json
from .security import safe_open

ALLOWED_STATUS = ("OK", "TIMEOUT", "PROVIDER_ERROR", "SCHEMA_ERROR", "LOCAL_INVALID")
DIGEST_SEPARATOR = ""  # canonical_json(state) || requested_model, no separator

QUESTION_OPTIONS = {
    "structure": STRUCTURES,
    "direction": DIRECTIONS,
    "phase": PHASES,
}
# Labels that must NEVER appear as a provider choice (no-double-abstention).
FORBIDDEN_PHASE_LABELS = ("TRANSITION_UNKNOWN", "UNKNOWN", "UNCLEAR", "ABSTAIN")


def compute_input_digest(state: dict, requested_model: str) -> str:
    return hashlib.sha256(
        (canonical_json(state) + requested_model).encode("utf-8")
    ).hexdigest()


def build_request_line(
    state_id: str, state: dict, requested_model: str
) -> dict:
    """Producer-side request line with the producer-computed digest."""
    return {
        "schema": QUESTION_IO_SCHEMA,
        "state_id": state_id,
        "state": state_payload(state),
        "requested_model": requested_model,
        "input_digest": compute_input_digest(state_payload(state), requested_model),
    }


def _normalized(line, state_id, status) -> dict:
    return {
        "state_id": state_id,
        "status": status,
        "answers": None,
        "model": None,
        "request_id": None,
        "usage": None,
        # prior_direction echo (state lineage, like the digest echo) — the
        # safety layer's consistency law needs it per line
        "prior_direction": line.get("prior_direction"),
    }


def _bad(line, state_id, violation) -> tuple[dict, str]:
    out = _normalized(line, state_id, "SCHEMA_ERROR")
    return out, violation


def _check_answer_block(block, options) -> str | None:
    """Validate one typed answer block; returns violation or None."""
    if not isinstance(block, dict):
        return "answer_block_missing"
    choice = block.get("choice")
    if not isinstance(choice, str) or choice not in options:
        return "choice_not_in_schema"
    probs = block.get("probabilities")
    if not isinstance(probs, dict):
        return "missing_probabilities"
    if set(probs.keys()) != set(options):
        return "probabilities_option_set_mismatch"
    vals = []
    for k in options:
        v = probs[k]
        if not isinstance(v, (int, float)) or v != v or v < 0:
            return "bad_probabilities"
        vals.append(float(v))
    if abs(sum(vals) - 1.0) > 0.01:
        return "probability_sum"
    conf = block.get("confidence")
    if not isinstance(conf, (int, float)) or conf != conf:
        return "bad_confidence"
    return None


def validate_response_line(
    line: dict,
    expected_state_id: str,
    expected_digest: str,
    pinned_model: str | None = None,
) -> tuple[dict | None, str | None]:
    """Validate one response line. Returns (normalized|None, violation|None).

    normalized = {'state_id','status','answers','model','request_id','usage'}
    with any violation coerced to status SCHEMA_ERROR (decision UNKNOWN via
    the safety layer).
    """
    if line.get("schema") != QUESTION_IO_SCHEMA:
        return _bad(line, expected_state_id, "schema_field")
    if line.get("state_id") != expected_state_id:
        return _bad(line, expected_state_id, "state_id_mismatch")
    if line.get("input_digest") != expected_digest:
        return _bad(line, expected_state_id, "input_digest_mismatch")
    status = line.get("status")
    if status not in ALLOWED_STATUS:
        return _bad(line, expected_state_id, "bad_status")
    if status != "OK":
        out = _normalized(line, expected_state_id, status)
        out["usage"] = _usage_of(line)
        return out, None
    if pinned_model is not None and line.get("model") != pinned_model:
        return _bad(line, expected_state_id, "model_pin_mismatch")
    answers = line.get("answers")
    if not isinstance(answers, dict):
        return _bad(line, expected_state_id, "missing_answers")
    if set(answers.keys()) != {"structure", "direction", "phase"}:
        return _bad(line, expected_state_id, "answers_question_set_mismatch")
    for qname, options in QUESTION_OPTIONS.items():
        violation = _check_answer_block(answers.get(qname), options)
        if violation is not None:
            return _bad(line, expected_state_id, f"{qname}_{violation}")
    # forced-choice law, explicit: no UNKNOWN-equivalent anywhere as a choice
    for qname in QUESTION_OPTIONS:
        ch = answers[qname].get("choice")
        if qname == "phase" and ch in FORBIDDEN_PHASE_LABELS:
            return _bad(line, expected_state_id, "forbidden_unknown_phase_option")
    usage = _usage_of(line)
    if usage is None:
        return _bad(line, expected_state_id, "missing_usage")
    out = _normalized(line, expected_state_id, "OK")
    out["answers"] = answers
    out["model"] = line.get("model")
    out["request_id"] = line.get("request_id")
    out["usage"] = usage
    return out, None


def _usage_of(line: dict) -> dict | None:
    u = line.get("usage")
    if not isinstance(u, dict):
        return None
    it, ot = u.get("input_tokens"), u.get("output_tokens")
    if not isinstance(it, (int, float)) or not isinstance(ot, (int, float)):
        return None
    if it != it or ot != ot or it < 0 or ot < 0:
        return None
    return {"input_tokens": it, "output_tokens": ot}


class DecisionStore:
    """Append-only decision cache (runtime/decisions_<cell>.jsonl)."""

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
    """Persisted effective-regime timeline over regime bars (from warmup)."""

    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    @property
    def ts(self) -> list[int]:
        return [r["regime_bar_close_ns"] for r in self.rows]

    @property
    def persisted(self) -> list[str]:
        return [r["persisted"] for r in self.rows]

    @property
    def effective(self) -> list[str]:
        return [r["effective"] for r in self.rows]

    def stats(self) -> dict:
        from . import LABELS

        n = len(self.rows)
        switches = sum(1 for r in self.rows if r["switched"])
        occ: dict[str, int] = {l: 0 for l in LABELS}
        for r in self.rows:
            occ[r["persisted"]] += 1
        unknown = sum(1 for r in self.rows if r["effective"] == "TRANSITION_UNKNOWN")
        return {
            "n_decisions": n,
            "switches": switches,
            "occupancy": {k: v / n if n else 0.0 for k, v in occ.items()},
            "effective_unknown_share": unknown / n if n else 0.0,
            "incidents": sum(len(r.get("violations", [])) for r in self.rows),
        }


class DecisionsIncomplete(RuntimeError):
    """Arm scoring requires a complete decision cache (fail-closed)."""


class CacheProvider:
    """Provider backed by a DecisionStore; returns None on miss."""

    def __init__(self, store: DecisionStore) -> None:
        self.store = store

    def __call__(self, state_id: str, state: dict) -> dict | None:
        return self.store.by_state_id.get(state_id)


def sequential_timeline(
    cell: str,
    fz: Freezes,
    regime_bars,
    feats,
    provider,
    pinned_model: str | None = None,
    requested_model: str = "UNPINNED",
    strict: bool = True,
    request_sink: list | None = None,
):
    """Authoritative STRICT SEQUENTIAL decision + safety + persistence walk.

    provider(state_id, state) -> response line dict | None.
    - LOCAL_INVALID states are NEVER sent (status LOCAL_INVALID, UNKNOWN).
    - prior fields for bar t derive from the persisted state in force at t-1
      (recomputed after EVERY merged response — V1 F2 law).
    - strict=True (scoring): a cache miss raises DecisionsIncomplete.
      strict=False (build/mock mode): advances with an UNKNOWN-candidate.
    """
    from .data import Bars  # noqa: F401  (typing only)
    from .safety import UNKNOWN, PersistenceState, effective_from_response, step
    from .features import semantic_state

    params = fz.persistence_params()
    st = PersistenceState(**params)
    persisted_by_index: list[str | None] = [None] * feats.T
    rows: list[dict] = []
    missing = 0
    warmup = _warmup_for(cell, fz)
    asset = _asset_for(cell, fz)
    for t in range(warmup, feats.T):
        ts_close = int(regime_bars.ts_close[t])
        sid = fz.state_id(asset, ts_close)
        # build the semantic state with prior = persisted in force at t-1
        state = semantic_state(
            asset, fz, regime_bars, t, feats,
            persisted_by_index[t - 1] if t > 0 else None,
        )
        if state is None:
            rows.append(
                {
                    "bar_index": t,
                    "regime_bar_close_ns": ts_close,
                    "state_id": sid,
                    "status": "LOCAL_INVALID",
                    "effective": UNKNOWN,
                    "eligible": False,
                    "persisted": st.current,
                    "switched": False,
                    "violations": [],
                }
            )
            persisted_by_index[t] = st.current
            continue
        payload = state_payload(state)
        digest = compute_input_digest(payload, requested_model)
        if request_sink is not None:
            request_sink.append(build_request_line(sid, state, requested_model))
        line = provider(sid, state)
        if line is None:
            missing += 1
            if strict:
                raise DecisionsIncomplete(f"missing decision for state {sid} (bar {t})")
            normalized, violation = None, "cache_miss"
            eff = None
        else:
            normalized, violation = validate_response_line(line, sid, digest, pinned_model)
            eff = normalized
        label, eligible, reason = effective_from_response(eff, params)
        switched = step(st, label, eligible)
        persisted_by_index[t] = st.current
        rows.append(
            {
                "bar_index": t,
                "regime_bar_close_ns": ts_close,
                "state_id": sid,
                "status": (eff or {}).get("status", "MISSING"),
                "effective": label,
                "effective_reason": reason,
                "eligible": eligible,
                "persisted": st.current,
                "switched": switched,
                "violations": [violation] if violation else [],
            }
        )
    tl = Timeline(rows)
    tl.missing = missing
    return tl


def _asset_for(cell: str, fz: Freezes) -> str:
    from . import CELLS

    return CELLS[cell]["asset"]


def _warmup_for(cell: str, fz: Freezes) -> int:
    return fz.warmup(cell)
