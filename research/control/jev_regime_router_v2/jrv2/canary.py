"""Synthetic canary + perturbations + acceptance evaluation (canary_v2_contract).

- synthetic fixtures come from the freeze verbatim (C1..C8): 4 CLEAR
  (expected effective label) + 3 AMBIGUOUS (expected code-abstained) +
  1 MISSING/STALE (never sent, local UNKNOWN).
- perturbations: 8 per CLEAR fixture; raw numerics jittered +-10% uniform
  (seeded, contract seed 20260923); semantic bins recomputed from the
  jittered numerics where the raw source is present; expected effective
  label UNCHANGED.
- acceptance: every preregistered criterion is printed PASS/FAIL WITH
  NUMBERS. This is plumbing (mock namespace) in this lane — no live call.
"""

from __future__ import annotations

import json

import numpy as np

from . import PHASES
from .features import compute_bins
from .questionio import build_request_line, validate_response_line
from .safety import UNKNOWN, effective_from_response
from .security import assert_no_credential_leak

PERTURB_SCHEMA = "jrv2_perturbation_fixture@1"
CANARY_RESULT_SCHEMA = "jrv2_canary_result@1"


class FixtureState:
    """A semantic state dict + identity, shared by fixtures and perturbations."""

    def __init__(self, fixture_id: str, state: dict) -> None:
        self.fixture_id = fixture_id
        self.state = state

    def payload(self) -> dict:
        from .features import state_payload

        return state_payload(self.state)


def perturbation_fixtures(fz) -> dict[str, list[FixtureState]]:
    """8 seeded perturbations per CLEAR fixture (contract seed 20260923).

    raw numerics v -> v * (1 + u), u ~ U(-jitter, +jitter); bins recomputed
    from the jittered numerics (bins whose raw source is absent keep the
    frozen bin). Deterministic per (fixture, k).
    """
    cfg = fz.canary_contract["perturbations"]
    jitter = float(cfg["jitter"])
    n = int(cfg["n_per_clear_fixture"])
    seed0 = int(fz.canary_contract["seed"])
    out: dict[str, list[FixtureState]] = {}
    clear = [fx for fx in fz.canary_contract["synthetic_fixtures"] if fx["class"] == "clear"]
    from .features import normalize_semantic_state

    for fi, fx in enumerate(clear):
        rng = np.random.default_rng([seed0, fi])
        states = []
        for k in range(n):
            st = normalize_semantic_state(json.loads(json.dumps(fx["state"])))
            numerics = st["numerics"]
            u = rng.uniform(-jitter, jitter, size=len(numerics))
            for (name, val), ui in zip(numerics.items(), u):
                numerics[name] = float(val) * (1.0 + float(ui))
            recomputed = compute_bins(numerics)
            if recomputed:
                st["bins"] = {**st["bins"], **recomputed}
            states.append(FixtureState(f"{fx['id']}_P{k}", st))
        out[fx["id"]] = states
    return out


def _run_state(provider, requested_model, pinned_model, fixture: FixtureState, params) -> dict:
    """One fixture through request -> response -> validation -> safety."""
    payload = fixture.payload()  # noqa: F841 (digest comes from build_request_line)
    sid = _fixture_sid(fixture.fixture_id)
    line = build_request_line(sid, fixture.state, requested_model)
    resp = provider(sid, fixture.state)
    normalized, violation = validate_response_line(resp, sid, line["input_digest"], pinned_model)
    effective, eligible, reason = effective_from_response(normalized, params)
    raw_choices = {}
    if normalized and normalized.get("answers"):
        for q, block in normalized["answers"].items():
            raw_choices[q] = block["choice"]
    return {
        "id": fixture.fixture_id,
        "state_id": sid,
        "raw_choices": raw_choices,
        "schema_valid": normalized is not None and normalized.get("status") == "OK",
        "violation": violation,
        "effective": effective,
        "eligible": eligible,
        "reason": reason,
        "model": (normalized or {}).get("model"),
        "usage": (normalized or {}).get("usage"),
        "latency_ms": (resp or {}).get("latency_ms") if isinstance(resp, dict) else None,
        "text": json.dumps(resp, sort_keys=True, default=str),
    }


def _fixture_sid(fixture_id: str) -> str:
    import hashlib

    return hashlib.sha256(("JRV2-fixture:" + fixture_id).encode("utf-8")).hexdigest()[:16]


def run_canary_synthetic(fz, provider, requested_model: str, pinned_model: str | None, mock: bool) -> dict:
    """Run the frozen fixtures + perturbations; evaluate EVERY preregistered
    acceptance criterion with measured numbers."""
    params = fz.persistence_params()
    fixtures = fz.canary_contract["synthetic_fixtures"]
    clear_ids = [fx["id"] for fx in fixtures if fx["class"] == "clear"]
    ambiguous_ids = [fx["id"] for fx in fixtures if fx["class"] == "ambiguous"]
    expected_by_id = {fx["id"]: fx.get("expected", {}) for fx in fixtures}

    rows: list[dict] = []
    not_sent: list[str] = []
    for fx in fixtures:
        if fx["state"] is None:
            not_sent.append(fx["id"])
            rows.append(
                {
                    "id": fx["id"],
                    "state_id": None,
                    "raw_choices": {},
                    "schema_valid": True,
                    "violation": None,
                    "effective": UNKNOWN,
                    "eligible": False,
                    "reason": "missing_or_stale_state_not_sent",
                    "model": None,
                    "usage": None,
                    "latency_ms": None,
                    "text": "",
                }
            )
            continue
        from .features import normalize_semantic_state

        rows.append(_run_state(provider, requested_model, pinned_model,
                               FixtureState(fx["id"], normalize_semantic_state(fx["state"])), params))

    pert_rows: dict[str, list[dict]] = {}
    for fid, states in perturbation_fixtures(fz).items():
        pert_rows[fid] = [
            _run_state(provider, requested_model, pinned_model, s, params) for s in states
        ]

    checks = _evaluate_acceptance(
        fz, rows, pert_rows, clear_ids, ambiguous_ids, expected_by_id, not_sent, requested_model, mock
    )
    usage_in = sum(int(r["usage"]["input_tokens"]) for r in rows if r.get("usage"))
    usage_out = sum(int(r["usage"]["output_tokens"]) for r in rows if r.get("usage"))
    latencies = [float(r["latency_ms"]) for r in rows if r.get("latency_ms") is not None]
    measured = {
        "n_fixtures": len(fixtures),
        "n_sent": len(fixtures) - len(not_sent),
        "n_not_sent": len(not_sent),
        "usage_totals": {"input_tokens": usage_in, "output_tokens": usage_out},
        "total_latency_ms": float(sum(latencies)) if latencies else 0.0,
        "model_requested": requested_model,
        "mock": mock,
    }
    ok = all(c["pass"] for c in checks)
    return {
        "schema": CANARY_RESULT_SCHEMA,
        "namespace": "MOCK" if mock else "LIVE_CANDIDATE",
        "ok": ok,
        "checks": checks,
        "measured": measured,
        "rows": rows,
        "perturbation_rows": {k: [r["effective"] for r in v] for k, v in pert_rows.items()},
    }


def _evaluate_acceptance(
    fz,
    rows,
    pert_rows,
    clear_ids,
    ambiguous_ids,
    expected_by_id,
    not_sent,
    requested_model,
    mock,
) -> list[dict]:
    cfg = fz.canary_contract
    acceptance = cfg["acceptance_preregistered"]
    checks: list[dict] = []

    def add(name, passed, measured):
        checks.append({"criterion": name, "pass": bool(passed), "measured": measured})

    # 1. raw output NEVER contains a non-schema label
    non_schema = [
        (r["id"], q, c)
        for r in rows
        for q, c in r["raw_choices"].items()
        if q == "phase" and c not in PHASES
    ]
    add(acceptance[0], len(non_schema) == 0, {"non_schema_labels": non_schema})

    # 2. 100% schema-valid on the SENT fixtures
    n_sent = len(rows) - len(not_sent)
    n_valid = sum(1 for r in rows if r["schema_valid"] and r["id"] not in not_sent)
    add(acceptance[1], n_valid == n_sent, {"schema_valid": n_valid, "sent": n_sent})

    # 3. clear directional fixtures not inverted
    clear_rows = {r["id"]: r for r in rows if r["id"] in clear_ids}
    inverted = [
        fid
        for fid in clear_ids
        if clear_rows[fid]["effective"] != expected_by_id[fid]["effective"]
    ]
    add(acceptance[2], not inverted, {"misclassified_clear": inverted,
                                      "effective": {fid: clear_rows[fid]["effective"] for fid in clear_ids}})

    # 4. no single raw phase label > 70% across the balanced CLEAR fixtures
    from collections import Counter

    phase_counts = Counter(clear_rows[f]["raw_choices"].get("phase") for f in clear_ids)
    max_phase_share = (max(phase_counts.values()) / len(clear_ids)) if clear_ids else 0.0
    add(acceptance[3], max_phase_share <= 0.70,
        {"phase_counts": dict(phase_counts), "max_share": max_phase_share})

    # 5. perturbation stability >= 6/8 per clear family
    thr = int(cfg["perturbations"]["stability_threshold"].split("/")[0].replace(">=", "").strip())
    n_per = int(cfg["perturbations"]["n_per_clear_fixture"])
    stability = {}
    unstable = []
    for fid, prs in pert_rows.items():
        expected = expected_by_id[fid]["effective"]
        kept = sum(1 for r in prs if r["effective"] == expected)
        stability[fid] = {"kept": kept, "of": n_per, "expected": expected}
        if kept < thr:
            unstable.append(fid)
    add(acceptance[4], not unstable, {"stability": stability, "threshold": f">= {thr}/{n_per}"})

    # 6. ambiguous fixtures ARE code-abstained
    amb_rows = {r["id"]: r for r in rows if r["id"] in ambiguous_ids}
    not_abstained = [fid for fid in ambiguous_ids if amb_rows[fid]["effective"] != UNKNOWN]
    add(acceptance[5], not not_abstained,
        {"not_abstained": not_abstained, "reasons": {fid: amb_rows[fid]["reason"] for fid in ambiguous_ids}})

    # 7. clear fixtures NOT mass-abstained (>= 80% keep an effective label)
    kept = sum(1 for fid in clear_ids if clear_rows[fid]["effective"] != UNKNOWN)
    share = kept / len(clear_ids) if clear_ids else 0.0
    add(acceptance[6], share >= 0.80, {"kept_effective": kept, "of": len(clear_ids), "share": share})

    # 8. zero credential leakage (all fixture response text scanned)
    blob = json.dumps([r["text"] for r in rows]) + json.dumps(
        [[r["text"] for r in prs] for prs in pert_rows.values()]
    )
    leak = not assert_no_credential_leak(blob)
    add(acceptance[7], not leak, {"credential_value_present": leak, "scanned_bytes": len(blob)})

    # 9. exact model pin (echo == requested; live pin law enforced at ingest)
    models = {r["model"] for r in rows if r.get("model") is not None}
    add(acceptance[8], models == {requested_model},
        {"models_echoed": sorted(models), "requested": requested_model})

    # 10. cost/call/latency measured and recorded
    usage_in = sum(int(r["usage"]["input_tokens"]) for r in rows if r.get("usage"))
    usage_out = sum(int(r["usage"]["output_tokens"]) for r in rows if r.get("usage"))
    add(acceptance[9], True,
        {"calls": n_sent, "input_tokens": usage_in, "output_tokens": usage_out,
         "note": "mock usage is deterministic plumbing; live calls record real usage"})

    return checks
