"""Evidence taxonomy shared by every module.

Every quantitative claim inside this package must be tagged. Missing evidence
is NOT_RUN, never an inferred PASS. No module may silently coerce a NOT_RUN
into a number.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EvidenceTag(str, Enum):
    FACT = "FACT"            # sourced: primary source + access date
    OBSERVED = "OBSERVED"    # computed from raw data (script, sample, window)
    POSTULATED = "POSTULATED"  # mechanism reasoning, no measurement
    NOT_RUN = "NOT_RUN"      # unmeasured / not attempted


class CostProvenance(str, Enum):
    PUBLISHED = "PUBLISHED"  # vendor/exchange published schedule (document-class)
    MEASURED = "MEASURED"    # measured by us from raw data, window recorded
    DECLARED = "DECLARED"    # owner-declared assumption, explicitly recorded
    NOT_RUN = "NOT_RUN"      # no value; must never be fabricated


class PolicyError(RuntimeError):
    """Raised when code attempts something the research-conduct rules forbid.

    Distinct from ordinary bugs: these are intentional hard stops for
    PIT violations, fake measured costs, additive leg-PnL attribution,
    performance-based fold suppression, silent under-purging, etc.
    """


@dataclass(frozen=True)
class Evidence:
    """A tagged claim. `source` is required for FACT; `script`+`window` for
    OBSERVED; optional note elsewhere."""
    tag: EvidenceTag
    source: str | None = None
    accessed_utc: str | None = None
    script: str | None = None
    window: str | None = None
    note: str | None = None

    def to_dict(self) -> dict:
        return {
            "tag": self.tag.value,
            "source": self.source,
            "accessed_utc": self.accessed_utc,
            "script": self.script,
            "window": self.window,
            "note": self.note,
        }

    def validate(self) -> "Evidence":
        if self.tag is EvidenceTag.FACT and not (self.source and self.accessed_utc):
            raise PolicyError("FACT claims require source + accessed_utc")
        if self.tag is EvidenceTag.OBSERVED and not (self.script and self.window):
            raise PolicyError("OBSERVED claims require script + window")
        return self


NOT_RUN = Evidence(tag=EvidenceTag.NOT_RUN)


def require_not_placeholder(value, what: str) -> None:
    if value is None:
        raise PolicyError(
            f"{what} is NOT_RUN (no value). Fabricating a number is forbidden; "
            "declare the assumption explicitly or measure it."
        )
