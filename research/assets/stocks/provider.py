"""Provider adapter interface and entitlement policy (owner: A3).

PLAN_stocks.md section 2 freezes the source policy: preferred providers are
an owner-authorized point-in-time provider, then Databento, then IB, then
owner-supplied Parquet/CSV.  No entitlement exists in this sprint, therefore
this module ships NO real provider implementation — only the interface and a
fail-closed entitlement policy:

* :data:`NO_ENTITLEMENT_FAIL_CLOSED` is the default entitlement status of
  every adapter; an adapter that cannot prove a verified entitlement can
  never claim authority;
* data from free convenience APIs is :data:`DIAGNOSTIC_ONLY` by structure
  and can NEVER satisfy an authority requirement, no matter what record is
  attached to it;
* every adapter must publish a strict
  :class:`EntitlementRequirement` — the exact record a real entitlement
  check would have to produce (credentials, permissions, verification
  procedure, licensed scope, vendor documentation);
* ``provider_id`` and ``provider_schema_digest`` are mandatory identity
  fields wired into the asset-neutral contract
  (``research.assets.common.contracts.AssetExperimentContract``).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from research.assets.common.contracts import (
    canonical_json,
    require_digest_hex,
    require_token,
    sha256_text,
)

# --- data tiers ------------------------------------------------------------- #
AUTHORITY = "AUTHORITY"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"

# --- entitlement statuses ----------------------------------------------------- #
#: Default status of every adapter: no entitlement exists, so every authority
#: request fails closed.  A verified entitlement must be attached explicitly
#: as an :class:`EntitlementRecord` by an out-of-band check that this sprint
#: cannot perform (no provider entitlement exists).
NO_ENTITLEMENT_FAIL_CLOSED = "NO_ENTITLEMENT_FAIL_CLOSED"
ENTITLEMENT_VERIFIED = "ENTITLEMENT_VERIFIED"

# --- source classes ----------------------------------------------------------- #
SOURCE_OWNER_ENTITLED_PIT = "OWNER_ENTITLED_PIT"
SOURCE_VENDOR_ENTITLED = "VENDOR_ENTITLED"
SOURCE_FREE_CONVENIENCE = "FREE_CONVENIENCE"

AUTHORITY_CAPABLE_SOURCE_CLASSES = frozenset(
    {SOURCE_OWNER_ENTITLED_PIT, SOURCE_VENDOR_ENTITLED}
)

#: Licensed scope a real entitlement must cover before any PIT equity research
#: result may claim authority (PLAN_stocks.md section 7 A3 data contract).
REQUIRED_LICENSE_SCOPE = (
    "PIT_SECURITY_MASTER",
    "DELISTINGS",
    "CORPORATE_ACTIONS",
    "HISTORY_WITH_ADJUSTMENTS",
)


class ProviderError(Exception):
    """Base error for provider/entitlement policy violations."""


class EntitlementError(ProviderError):
    """An authority request cannot be satisfied (fail closed)."""


class DiagnosticDataCannotSatisfyAuthorityError(EntitlementError):
    """Free-convenience data is DIAGNOSTIC_ONLY and can never be authority."""


@dataclass(frozen=True)
class EntitlementRequirement:
    """Strict record of what a REAL entitlement check would require.

    This is documentation-as-contract: an adapter without an entitlement must
    still be able to state exactly what the missing check looks like, so a
    future integration cannot quietly substitute a weaker check.
    """

    provider_id: str
    provider_schema_digest: str
    source_class: str
    required_credentials: tuple[str, ...]
    required_permissions: tuple[str, ...]
    verification_procedure: str
    licensed_scope: tuple[str, ...]
    vendor_documentation: tuple[str, ...]

    def __post_init__(self) -> None:
        require_token(self.provider_id, "provider_id")
        require_digest_hex(self.provider_schema_digest, "provider_schema_digest")
        if self.source_class not in (
            SOURCE_OWNER_ENTITLED_PIT,
            SOURCE_VENDOR_ENTITLED,
            SOURCE_FREE_CONVENIENCE,
        ):
            raise ValueError(f"unknown source_class {self.source_class!r}")
        for field_name in ("required_credentials", "required_permissions"):
            value = getattr(self, field_name)
            if not value or not all(isinstance(v, str) and v.strip() for v in value):
                raise ValueError(f"{field_name} must be a non-empty tuple of tokens")
        if not isinstance(self.verification_procedure, str) or not self.verification_procedure.strip():
            raise ValueError("verification_procedure must be a non-empty description")
        if not self.licensed_scope or not all(
            isinstance(v, str) and v.strip() for v in self.licensed_scope
        ):
            raise ValueError("licensed_scope must be a non-empty tuple of tokens")
        if not self.vendor_documentation or not all(
            isinstance(v, str) and v.strip() for v in self.vendor_documentation
        ):
            raise ValueError("vendor_documentation must be a non-empty tuple of references")
        if self.source_class == SOURCE_FREE_CONVENIENCE:
            # Free convenience APIs must document that their scope can never
            # cover the authority requirements.
            overlap = set(self.licensed_scope) & set(REQUIRED_LICENSE_SCOPE)
            if overlap:
                raise ValueError(
                    "FREE_CONVENIENCE source must not declare authority scope "
                    f"{sorted(overlap)}; free convenience data is DIAGNOSTIC_ONLY"
                )

    def canonical_json(self) -> str:
        return canonical_json(
            {
                "schema": "entitlement_requirement",
                "provider_id": self.provider_id,
                "provider_schema_digest": self.provider_schema_digest,
                "source_class": self.source_class,
                "required_credentials": list(self.required_credentials),
                "required_permissions": list(self.required_permissions),
                "verification_procedure": self.verification_procedure,
                "licensed_scope": list(self.licensed_scope),
                "vendor_documentation": list(self.vendor_documentation),
            }
        )


@dataclass(frozen=True)
class EntitlementRecord:
    """Out-of-band proof that a real entitlement check succeeded.

    Producing one of these is NOT possible inside this sprint (no provider
    entitlement exists); the dataclass only defines the shape a future,
    real check must fill.  The record must cover the full
    :data:`REQUIRED_LICENSE_SCOPE` — partial entitlements fail closed.
    """

    provider_id: str
    provider_schema_digest: str
    verified_at: datetime
    evidence: tuple[str, ...]
    licensed_scope: tuple[str, ...]

    def __post_init__(self) -> None:
        require_token(self.provider_id, "provider_id")
        require_digest_hex(self.provider_schema_digest, "provider_schema_digest")
        if not isinstance(self.verified_at, datetime) or self.verified_at.tzinfo is None:
            raise ValueError("verified_at must be a tz-aware datetime")
        if not self.evidence or not all(isinstance(v, str) and v.strip() for v in self.evidence):
            raise ValueError("evidence must be a non-empty tuple of tokens")
        missing = [s for s in REQUIRED_LICENSE_SCOPE if s not in self.licensed_scope]
        if missing:
            raise ValueError(
                f"entitlement record does not cover required license scope: {missing}"
            )


class ProviderAdapter(abc.ABC):
    """Abstract provider interface with a fail-closed entitlement policy.

    There is deliberately NO method that fetches data: this sprint has no
    entitlement, and a fetch-capable adapter would invite exactly the
    free-API-as-authority shortcut the plan forbids.  Concrete data access
    arrives only through the local, owner-supplied loader
    (:mod:`research.assets.stocks.loader`).
    """

    #: Class-level default so an adapter that never attaches a record is
    #: unentitled by construction.
    _entitlement_record: EntitlementRecord | None = None

    @property
    @abc.abstractmethod
    def provider_id(self) -> str:
        """Stable provider identifier (contract field ``provider_id``)."""

    @property
    @abc.abstractmethod
    def provider_schema_digest(self) -> str:
        """sha256 over the provider's schema/adjustment documentation digest."""

    @property
    @abc.abstractmethod
    def source_class(self) -> str:
        """One of SOURCE_OWNER_ENTITLED_PIT / SOURCE_VENDOR_ENTITLED / SOURCE_FREE_CONVENIENCE."""

    @abc.abstractmethod
    def entitlement_requirement(self) -> EntitlementRequirement:
        """The strict record a real entitlement check would have to produce."""

    @property
    def entitlement_status(self) -> str:
        if self._entitlement_record is not None:
            return ENTITLEMENT_VERIFIED
        return NO_ENTITLEMENT_FAIL_CLOSED

    @property
    def entitlement_evidence(self) -> EntitlementRecord | None:
        return self._entitlement_record

    def attach_entitlement_record(self, record: EntitlementRecord) -> None:
        """Attach an out-of-band entitlement proof (validated, fail-closed)."""
        if not isinstance(record, EntitlementRecord):
            raise EntitlementError("entitlement record has the wrong type")
        if record.provider_id != self.provider_id:
            raise EntitlementError(
                f"entitlement record is for provider {record.provider_id!r}, "
                f"adapter is {self.provider_id!r}"
            )
        if record.provider_schema_digest != self.provider_schema_digest:
            raise EntitlementError(
                "entitlement record schema digest does not match the adapter's "
                f"provider_schema_digest ({record.provider_schema_digest} != "
                f"{self.provider_schema_digest})"
            )
        if self.source_class not in AUTHORITY_CAPABLE_SOURCE_CLASSES:
            raise EntitlementError(
                f"source class {self.source_class!r} can never be entitled; "
                "free convenience sources are DIAGNOSTIC_ONLY by structure"
            )
        object.__setattr__(self, "_entitlement_record", record)

    def data_tier(self) -> str:
        """AUTHORITY only with a verified entitlement on an authority-capable source."""
        if (
            self.source_class in AUTHORITY_CAPABLE_SOURCE_CLASSES
            and self.entitlement_status == ENTITLEMENT_VERIFIED
            and self._entitlement_record is not None
        ):
            return AUTHORITY
        return DIAGNOSTIC_ONLY

    def require_authority(self, *, purpose: str) -> None:
        """Fail closed unless this adapter may satisfy an authority requirement."""
        if not isinstance(purpose, str) or not purpose.strip():
            raise EntitlementError("purpose must be a non-empty description")
        if self.source_class == SOURCE_FREE_CONVENIENCE:
            raise DiagnosticDataCannotSatisfyAuthorityError(
                f"provider {self.provider_id!r} is a free convenience source: its "
                "data is DIAGNOSTIC_ONLY and can never satisfy authority "
                f"(purpose={purpose!r})"
            )
        record = self._entitlement_record
        if self.entitlement_status != ENTITLEMENT_VERIFIED or record is None:
            raise EntitlementError(
                f"provider {self.provider_id!r} has entitlement status "
                f"{NO_ENTITLEMENT_FAIL_CLOSED}; a verified EntitlementRecord from "
                f"a real entitlement check is required for purpose={purpose!r}"
            )
        if record.provider_id != self.provider_id or (
            record.provider_schema_digest != self.provider_schema_digest
        ):
            raise EntitlementError(
                "attached entitlement record no longer matches the adapter identity"
            )

    def provenance(self) -> dict[str, str]:
        """Manifest-ready provenance fields (contract field names)."""
        return {
            "provider_id": self.provider_id,
            "provider_schema_digest": self.provider_schema_digest,
            "entitlement_status": self.entitlement_status,
            "data_tier": self.data_tier(),
        }


class UnentitledDiagnosticStub(ProviderAdapter):
    """The ONLY shipped concrete adapter: explicitly unentitled, diagnostic-only.

    This is a placeholder that documents the missing entitlement; it is not a
    real provider implementation and can never become one implicitly.
    """

    _STUB_SCHEMA_DOC = (
        "unentitled-diagnostic-stub:schema-v1:no-real-provider-implementation"
    )

    @property
    def provider_id(self) -> str:
        return "UNENTITLED_DIAGNOSTIC_STUB"

    @property
    def provider_schema_digest(self) -> str:
        return sha256_text(self._STUB_SCHEMA_DOC)

    @property
    def source_class(self) -> str:
        return SOURCE_FREE_CONVENIENCE

    def entitlement_requirement(self) -> EntitlementRequirement:
        return EntitlementRequirement(
            provider_id=self.provider_id,
            provider_schema_digest=self.provider_schema_digest,
            source_class=self.source_class,
            required_credentials=(
                "OWNER_LICENSE_KEY",
                "PROVIDER_ACCOUNT_ID",
            ),
            required_permissions=(
                "EQUITY_PIT_HISTORY",
                "DELISTED_SECURITIES",
                "CORPORATE_ACTIONS",
                "SECURITY_MASTER",
            ),
            verification_procedure=(
                "A real entitlement check queries the vendor's authorization API "
                "with the owner credentials, records the returned permission scope "
                "verbatim, and stores it as an EntitlementRecord. Free convenience "
                "endpoints can never substitute for this check."
            ),
            licensed_scope=("LATE_DELAYED_DATA_ONLY",),  # free convenience: never authority scope
            vendor_documentation=(
                "PLAN_stocks.md section 2 (source and adapter policy)",
                "https://nautilustrader.io/docs/latest/concepts/instruments/equity/",
                "https://nautilustrader.io/docs/latest/integrations/",
                "provider-specific schema and adjustment documentation (to be pinned "
                "when an entitlement exists)",
            ),
        )


def require_authority_capable(adapter: ProviderAdapter, *, purpose: str) -> None:
    """Module-level helper: fail closed unless ``adapter`` is authority-capable."""
    adapter.require_authority(purpose=purpose)


def provider_identity_payload(adapter: ProviderAdapter) -> dict[str, Any]:
    """Canonical identity payload for manifests (provider_id + schema digest)."""
    return {
        "provider_id": adapter.provider_id,
        "provider_schema_digest": adapter.provider_schema_digest,
        "source_class": adapter.source_class,
    }
