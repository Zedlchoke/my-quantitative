"""expwitch_refusal — the EXPWITCH-NQ leg refusal stub (no adapter exists).

LAW (SPEC_NQ.md s.8.1; NQ_K6_GATES.md s.2; IDENTITY_BUDGET_NQ.md s.1/s.3;
RUNNER_COMPAT_NQ.md RC-6.3; GAPS_AND_DECISIONS_NQ.md P5-NQ5):
the EXPWITCH-NQ leg is DEAD-AT-GATE — F5-K6 part (ii) FAILED at its
pre-declared condition (35/66 expiry-Friday held sessions carry RTH 15-minute
gaps; 34 x 15 min, 1 x 14 min; the 15-min gap signature is a panel-wide
property of the committed 1m data 2013-2021, vendor-granularity era-wide).
Per the anti-cherry-pick law the fail is recorded and NEVER re-tuned; the
family never enters scoring on the NQ leg; no EXPWITCH-NQ identity may be
minted without the owner's P5-NQ5 data-plane ruling plus a fresh family-law
path. Option NQ-D (43) consequently has no lawful path in this packet.

This module is the ONLY EXPWITCH artifact in adapt_nq/: any identity request
refuses with code EXPWITCH_DEAD_AT_GATE. There is no adapter, no fixtures,
no tests beyond the refusal proof.
"""
from __future__ import annotations

EXPWITCH_DEAD_AT_GATE = "EXPWITCH_DEAD_AT_GATE"

_REFUSAL_RECORD = {
    "code": EXPWITCH_DEAD_AT_GATE,
    "leg": "EXPWITCH-NQ",
    "disposition": "DEAD-AT-GATE — excluded from every slate; NOT re-litigated",
    "basis": [
        "SPEC_NQ.md s.8.1 (pre-declared consequence clause)",
        "NQ_K6_GATES.md s.2 (F5-K6 part (ii) FAIL: 35/66 expiry Fridays, "
        "34x15min + 1x14min RTH gaps; ordinary-Friday declared-diagnostic 46/80)",
        "IDENTITY_BUDGET_NQ.md s.1/s.3 (no IDs minted; census +7/+12 lines are "
        "published history, not consumable)",
        "RUNNER_COMPAT_NQ.md RC-6.3 (runner MUST refuse any EXPWITCH-NQ identity)",
        "GAPS_AND_DECISIONS_NQ.md P5-NQ5 (owner data-plane route; unsigned)",
    ],
    "owner_slot": "P5-NQ5 (open — data-plane decision, never a lane parameter)",
    "options_blocked": ["NQ-D (43) has no lawful path in this packet"],
    "note": ("requesting code may not convert this refusal into a gate pass; "
             "the refusal itself is the only artifact"),
}


class ExpwitchDeadAtGate(Exception):
    """Raised for ANY EXPWITCH identity request. Code: EXPWITCH_DEAD_AT_GATE."""

    code = EXPWITCH_DEAD_AT_GATE

    def __init__(self, detail: str = ""):
        self.detail = detail
        super().__init__(
            "EXPWITCH-NQ leg DEAD-AT-GATE — identity request refused"
            + (f": {detail}" if detail else ""))

    def record(self) -> dict:
        out = dict(_REFUSAL_RECORD)
        if self.detail:
            out = {**out, "detail": self.detail}
        return out


def request_expwitch_identity(identity_id: str | None = None, **_kwargs) -> dict:
    """Any EXPWITCH identity request refuses. Raises; never returns an identity.

    `identity_id` is accepted and recorded in the refusal detail only — no ID
    grammar for this leg exists lawfully (IDENTITY_BUDGET_NQ.md s.3).
    """
    raise ExpwitchDeadAtGate(
        f"request_expwitch_identity(identity_id={identity_id!r}): the leg is "
        f"DEAD-AT-GATE; no EXPWITCH-NQ identity exists or may be minted (P5-NQ5 open)")


def request_expwitch(*_args, **kwargs) -> dict:
    """Non-raising twin: returns the structured refusal record (advisory only)."""
    try:
        request_expwitch_identity(**kwargs)
    except ExpwitchDeadAtGate as exc:
        return exc.record()
    raise AssertionError("unreachable: the stub always refuses")


class ExpwitchStub:
    """Object-form stub mirroring the per-family adapter surface shape, so a
    caller wiring adapters by name hits an explicit refusal instead of an
    AttributeError. Every method refuses."""

    family = "ESNQ-F5 (EXPWITCH NQ leg)"
    dead_at_gate = True

    def build_observables(self, *_a, **_k) -> dict:
        raise ExpwitchDeadAtGate("build_observables: no adapter exists for a DEAD-AT-GATE leg")

    def signal(self, *_a, **_k) -> dict:
        raise ExpwitchDeadAtGate("signal: no adapter exists for a DEAD-AT-GATE leg")

    def order_intent(self, *_a, **_k) -> dict:
        raise ExpwitchDeadAtGate("order_intent: no adapter exists for a DEAD-AT-GATE leg")

    def apply_exclusions(self, *_a, **_k) -> dict:
        raise ExpwitchDeadAtGate("apply_exclusions: no adapter exists for a DEAD-AT-GATE leg")

    @staticmethod
    def refusal_record() -> dict:
        return dict(_REFUSAL_RECORD)
