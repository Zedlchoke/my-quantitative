"""No-order safety boundary (plan section 2, G4).

This engine is INTERNAL_PAPER_ONLY. The only emitted action type is
``TARGET_INTENT`` plus internal virtual fills. There is no order-routing
credential, broker client, write permission or callable deployment path.

``emit_target_intent`` is pure: no network, no side effects.

``assert_no_order_surface(package_root)`` recursively scans package
source for forbidden strings/imports (venue SDKs, order verbs, secret /
credential usage, environment secret reads) and raises on ANY hit. The
forbidden literals are assembled from fragments so this module's own
source stays scannable-clean.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

ALLOWED_ACTION_TYPES: Tuple[str, ...] = ("TARGET_INTENT",)

# Each forbidden literal is assembled so this source file never contains
# the literal itself (rule ids included); the scanner still checks real
# files for the assembled literals.
_FORBIDDEN_FRAGMENTS: Tuple[Tuple[str, str, str], ...] = (
    ("sdk_cc_module", "cc", "xt"),
    ("import_venue_sdk", "import ", "binance"),
    ("from_venue_sdk", "from ", "binance"),
    ("venue_sdk_client", "binance", ".client"),
    ("venue_sdk_pkg", "python-", "binance"),
    ("http_post_verb", "requests", ".post"),
    ("http_put_verb", "requests", ".put"),
    ("http_delete_verb", "requests", ".delete"),
    ("order_verb_create", "create", "_order"),
    ("order_verb_place", "place", "_order"),
    ("order_verb_submit", "submit", "_order"),
    ("order_verb_cancel", "cancel", "_order"),
    ("order_verb_new", "new", "_order"),
    ("credential_id_literal", "api", "_key"),
    ("credential_secret_literal", "api", "_secret"),
    ("key_material_literal", "secret", "_key"),
    ("env_secret_read", "os.", "environ"),
)

SCAN_EXTENSIONS = (".py", ".json")


class NoOrderViolationError(RuntimeError):
    """A forbidden order/credential surface was found. Fail closed."""


@dataclass(frozen=True)
class TargetIntent:
    """The only externally visible action this engine may emit."""

    schema: str
    cycle_id: str
    family_id: str
    arm_id: str
    event_id: str
    generated_utc: str
    action_type: str
    target_weights: Dict[str, float]
    note: str = ""


def emit_target_intent(
    *,
    cycle_id: str,
    family_id: str,
    arm_id: str,
    event_id: str,
    generated_utc: str,
    target_weights: Dict[str, float],
    note: str = "",
) -> Dict[str, Any]:
    """Pure intent record: no network, no side effects, no order path."""
    if target_weights is None:
        raise ValueError("target_weights required")
    intent = TargetIntent(
        schema="shv1_target_intent_v1",
        cycle_id=cycle_id,
        family_id=family_id,
        arm_id=arm_id,
        event_id=event_id,
        generated_utc=generated_utc,
        action_type="TARGET_INTENT",
        target_weights={k: float(v) for k, v in target_weights.items()},
        note=note,
    )
    return {
        "schema": intent.schema,
        "cycle_id": intent.cycle_id,
        "family_id": intent.family_id,
        "arm_id": intent.arm_id,
        "event_id": intent.event_id,
        "generated_utc": intent.generated_utc,
        "action_type": intent.action_type,
        "target_weights": intent.target_weights,
        "note": intent.note,
    }


def forbidden_patterns() -> List[Tuple[str, str]]:
    """(rule_id, literal) pairs the scanner refuses to find in source."""
    return [(rule_id, a + b) for rule_id, a, b in _FORBIDDEN_FRAGMENTS]


def scan_paths(package_root: str) -> List[str]:
    found: List[str] = []
    for dirpath, dirnames, filenames in os.walk(package_root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for filename in sorted(filenames):
            if filename.endswith(SCAN_EXTENSIONS):
                found.append(os.path.join(dirpath, filename))
    return sorted(found)


def scan_for_forbidden_surface(root: str) -> List[Dict[str, str]]:
    """Return all hits under root (empty list = clean)."""
    hits: List[Dict[str, str]] = []
    patterns = forbidden_patterns()
    for path in scan_paths(root):
        try:
            with open(path, "r", encoding="utf-8", errors="strict") as fh:
                for lineno, line in enumerate(fh, start=1):
                    lowered = line.lower()
                    for rule_id, literal in patterns:
                        if literal.lower() in lowered:
                            hits.append(
                                {
                                    "file": os.path.relpath(path, root),
                                    "line": str(lineno),
                                    "rule_id": rule_id,
                                    "literal": literal,
                                }
                            )
        except UnicodeDecodeError as exc:
            hits.append(
                {
                    "file": os.path.relpath(path, root),
                    "line": "0",
                    "rule_id": "undecodable_file",
                    "literal": str(exc),
                }
            )
    return hits


def assert_no_order_surface(package_root: str) -> Dict[str, Any]:
    """Raise NoOrderViolationError on ANY forbidden surface under root."""
    hits = scan_for_forbidden_surface(package_root)
    if hits:
        rendered = "; ".join(
            f"{h['file']}:{h['line']}[{h['rule_id']}]" for h in hits[:20]
        )
        raise NoOrderViolationError(
            f"forbidden order/credential surface found ({len(hits)} hit(s)): "
            f"{rendered}"
        )
    return {
        "root": package_root,
        "files_scanned": len(scan_paths(package_root)),
        "hits": 0,
        "verdict": "NO_ORDER_SURFACE_CLEAN",
    }


def package_scan_digest(package_root: str) -> str:
    """Deterministic sha256 over the package's scanned files."""
    entries: List[str] = []
    for path in scan_paths(package_root):
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        rel = os.path.relpath(path, package_root)
        entries.append(f"{rel}:{digest}")
    canonical = "\n".join(sorted(entries))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def no_order_proof(package_root: str) -> Dict[str, Any]:
    """Value for every event record's ``no_order_proof`` field."""
    return {
        "emitted_action_types": list(ALLOWED_ACTION_TYPES),
        "scan_digest": package_scan_digest(package_root),
    }
