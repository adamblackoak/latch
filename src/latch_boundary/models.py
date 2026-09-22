from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CandidateJudgment:
    candidate_id: str
    proposition: str
    source: str
    confidence: float | None = None
    evidence_refs: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)
    status: Literal["candidate", "adopted", "contested", "withdrawn"] = "candidate"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence_refs"] = list(self.evidence_refs)
        return d


@dataclass(frozen=True)
class Adoption:
    adoption_id: str
    candidate_id: str
    adopter_id: str
    adopter_kind: Literal["human", "service", "committee"]
    authority_ref: str
    scope: str
    basis_refs: tuple[str, ...]
    adopted_at: str = field(default_factory=utc_now)
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["basis_refs"] = list(self.basis_refs)
        return d


@dataclass(frozen=True)
class Challenge:
    challenge_id: str
    candidate_id: str
    challenger_id: str
    reason: str
    raised_at: str = field(default_factory=utc_now)
    resolved: bool = False
    resolution: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RelianceReceipt:
    receipt_id: str
    candidate_id: str
    adoption_id: str
    relying_actor: str
    purpose: str
    scope: str
    action_ref: str
    relied_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
