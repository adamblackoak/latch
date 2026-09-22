from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from .ledger import HashLedger
from .models import Adoption, CandidateJudgment, Challenge, RelianceReceipt


class BoundaryRefusal(ValueError):
    """Raised when a caller tries to cross the adoption/reliance boundary without standing."""


class Latch:
    """A deliberately small governed boundary around machine-generated judgement."""

    def __init__(self, ledger: HashLedger | None = None) -> None:
        self.ledger = ledger or HashLedger()
        self.candidates: dict[str, CandidateJudgment] = {}
        self.adoptions: dict[str, Adoption] = {}
        self.challenges: dict[str, Challenge] = {}
        self.receipts: dict[str, RelianceReceipt] = {}

    def submit_candidate(
        self,
        *,
        candidate_id: str,
        proposition: str,
        source: str,
        confidence: float | None = None,
        evidence_refs: tuple[str, ...] = (),
    ) -> CandidateJudgment:
        if candidate_id in self.candidates:
            raise BoundaryRefusal(f"candidate {candidate_id!r} already exists")
        if confidence is not None and not 0 <= confidence <= 1:
            raise BoundaryRefusal("confidence must be between 0 and 1")
        candidate = CandidateJudgment(
            candidate_id=candidate_id,
            proposition=proposition,
            source=source,
            confidence=confidence,
            evidence_refs=evidence_refs,
        )
        self.candidates[candidate_id] = candidate
        self.ledger.append("candidate.submitted", candidate.to_dict())
        return candidate

    def adopt(
        self,
        *,
        candidate_id: str,
        adopter_id: str,
        adopter_kind: str,
        authority_ref: str,
        scope: str,
        basis_refs: tuple[str, ...],
    ) -> Adoption:
        candidate = self._candidate(candidate_id)
        if candidate.status == "withdrawn":
            raise BoundaryRefusal("withdrawn candidate cannot be adopted")
        if candidate.status == "contested":
            raise BoundaryRefusal("contested candidate cannot be adopted until challenge is resolved")
        if adopter_kind not in {"human", "service", "committee"}:
            raise BoundaryRefusal("model output cannot adopt itself")
        if not authority_ref.strip():
            raise BoundaryRefusal("adoption requires an explicit authority_ref")
        if not scope.strip():
            raise BoundaryRefusal("adoption requires a defined scope")
        if not basis_refs:
            raise BoundaryRefusal("adoption requires at least one basis_ref")

        existing = self._active_adoption_for(candidate_id)
        if existing:
            raise BoundaryRefusal(f"candidate already has active adoption {existing.adoption_id}")

        adoption = Adoption(
            adoption_id=f"adopt_{uuid4().hex[:12]}",
            candidate_id=candidate_id,
            adopter_id=adopter_id,
            adopter_kind=adopter_kind,  # type: ignore[arg-type]
            authority_ref=authority_ref,
            scope=scope,
            basis_refs=basis_refs,
        )
        self.adoptions[adoption.adoption_id] = adoption
        self.candidates[candidate_id] = replace(candidate, status="adopted")
        self.ledger.append("candidate.adopted", adoption.to_dict())
        return adoption

    def challenge(self, *, candidate_id: str, challenger_id: str, reason: str) -> Challenge:
        candidate = self._candidate(candidate_id)
        if candidate.status == "withdrawn":
            raise BoundaryRefusal("withdrawn candidate cannot be challenged")
        if not reason.strip():
            raise BoundaryRefusal("challenge requires a reason")
        challenge = Challenge(
            challenge_id=f"challenge_{uuid4().hex[:12]}",
            candidate_id=candidate_id,
            challenger_id=challenger_id,
            reason=reason,
        )
        self.challenges[challenge.challenge_id] = challenge
        self.candidates[candidate_id] = replace(candidate, status="contested")
        self.ledger.append("candidate.challenged", challenge.to_dict())
        return challenge

    def resolve_challenge(
        self,
        *,
        challenge_id: str,
        resolver_id: str,
        outcome: str,
        resolution: str,
    ) -> Challenge:
        if challenge_id not in self.challenges:
            raise BoundaryRefusal(f"unknown challenge {challenge_id!r}")
        challenge = self.challenges[challenge_id]
        if challenge.resolved:
            raise BoundaryRefusal("challenge already resolved")
        if outcome not in {"reaffirm", "withdraw"}:
            raise BoundaryRefusal("outcome must be 'reaffirm' or 'withdraw'")
        if not resolution.strip():
            raise BoundaryRefusal("resolution text is required")

        resolved = replace(challenge, resolved=True, resolution=resolution)
        self.challenges[challenge_id] = resolved
        candidate = self._candidate(challenge.candidate_id)

        if outcome == "withdraw":
            self._deactivate_adoption(candidate.candidate_id)
            new_status = "withdrawn"
        elif candidate.status == "withdrawn":
            new_status = "withdrawn"
        elif self._has_open_challenges(candidate.candidate_id):
            new_status = "contested"
        else:
            new_status = "adopted" if self._active_adoption_for(candidate.candidate_id) else "candidate"
        self.candidates[candidate.candidate_id] = replace(candidate, status=new_status)  # type: ignore[arg-type]
        self.ledger.append(
            "challenge.resolved",
            {
                **resolved.to_dict(),
                "resolver_id": resolver_id,
                "outcome": outcome,
            },
        )
        return resolved

    def rely(
        self,
        *,
        candidate_id: str,
        relying_actor: str,
        purpose: str,
        scope: str,
        action_ref: str,
    ) -> RelianceReceipt:
        candidate = self._candidate(candidate_id)
        if self._has_open_challenges(candidate_id):
            raise BoundaryRefusal("candidate is contested: unresolved challenges make it ineligible for reliance")
        if candidate.status == "contested":
            raise BoundaryRefusal("contested candidate is not eligible for reliance")
        if candidate.status != "adopted":
            raise BoundaryRefusal("candidate has not been explicitly adopted")
        adoption = self._active_adoption_for(candidate_id)
        if not adoption:
            raise BoundaryRefusal("no active adoption exists")
        if scope != adoption.scope:
            raise BoundaryRefusal(f"reliance scope {scope!r} does not match adopted scope {adoption.scope!r}")
        if not purpose.strip() or not action_ref.strip():
            raise BoundaryRefusal("reliance requires purpose and action_ref")

        receipt = RelianceReceipt(
            receipt_id=f"rely_{uuid4().hex[:12]}",
            candidate_id=candidate_id,
            adoption_id=adoption.adoption_id,
            relying_actor=relying_actor,
            purpose=purpose,
            scope=scope,
            action_ref=action_ref,
        )
        self.receipts[receipt.receipt_id] = receipt
        self.ledger.append("judgement.relied", receipt.to_dict())
        return receipt

    def status(self, candidate_id: str) -> dict[str, object]:
        candidate = self._candidate(candidate_id)
        adoption = self._active_adoption_for(candidate_id)
        open_challenges = [
            x.to_dict() for x in self.challenges.values() if x.candidate_id == candidate_id and not x.resolved
        ]
        receipts = [x.to_dict() for x in self.receipts.values() if x.candidate_id == candidate_id]
        return {
            "candidate": candidate.to_dict(),
            "active_adoption": adoption.to_dict() if adoption else None,
            "open_challenges": open_challenges,
            "reliance_receipts": receipts,
        }

    def _candidate(self, candidate_id: str) -> CandidateJudgment:
        try:
            return self.candidates[candidate_id]
        except KeyError as exc:
            raise BoundaryRefusal(f"unknown candidate {candidate_id!r}") from exc

    def _active_adoption_for(self, candidate_id: str) -> Adoption | None:
        for adoption in self.adoptions.values():
            if adoption.candidate_id == candidate_id and adoption.active:
                return adoption
        return None

    def _has_open_challenges(self, candidate_id: str) -> bool:
        return any(
            challenge.candidate_id == candidate_id and not challenge.resolved
            for challenge in self.challenges.values()
        )

    def _deactivate_adoption(self, candidate_id: str) -> None:
        adoption = self._active_adoption_for(candidate_id)
        if adoption:
            self.adoptions[adoption.adoption_id] = replace(adoption, active=False)
