from __future__ import annotations

import json
from pathlib import Path

from .engine import BoundaryRefusal, Latch
from .ledger import HashLedger


def run_demo(ledger_path: str | Path | None = None) -> dict[str, object]:
    ledger = HashLedger(ledger_path) if ledger_path else HashLedger()
    latch = Latch(ledger)

    candidate = latch.submit_candidate(
        candidate_id="J-0042",
        proposition="Escalate the account for enhanced review.",
        source="risk-model-v7",
        confidence=0.97,
        evidence_refs=("case:8841", "feature-set:2026-09-22"),
    )

    blocked_before_adoption = None
    try:
        latch.rely(
            candidate_id=candidate.candidate_id,
            relying_actor="workflow-router",
            purpose="route case",
            scope="case-routing",
            action_ref="route:queue-enhanced-review",
        )
    except BoundaryRefusal as exc:
        blocked_before_adoption = str(exc)

    self_adoption_blocked = None
    try:
        latch.adopt(
            candidate_id=candidate.candidate_id,
            adopter_id="risk-model-v7",
            adopter_kind="model",
            authority_ref="generated:approval",
            scope="case-routing",
            basis_refs=("model:confidence:0.97",),
        )
    except BoundaryRefusal as exc:
        self_adoption_blocked = str(exc)

    adoption = latch.adopt(
        candidate_id=candidate.candidate_id,
        adopter_id="ops-reviewer-17",
        adopter_kind="human",
        authority_ref="role:enhanced-review-controller",
        scope="case-routing",
        basis_refs=("case:8841", "policy:ER-12"),
    )

    first_receipt = latch.rely(
        candidate_id=candidate.candidate_id,
        relying_actor="workflow-router",
        purpose="route case",
        scope="case-routing",
        action_ref="route:queue-enhanced-review",
    )

    challenge = latch.challenge(
        candidate_id=candidate.candidate_id,
        challenger_id="qa-reviewer-3",
        reason="New evidence conflicts with one of the input features.",
    )

    blocked_while_contested = None
    try:
        latch.rely(
            candidate_id=candidate.candidate_id,
            relying_actor="workflow-router",
            purpose="send downstream notification",
            scope="case-routing",
            action_ref="notify:enhanced-review",
        )
    except BoundaryRefusal as exc:
        blocked_while_contested = str(exc)

    latch.resolve_challenge(
        challenge_id=challenge.challenge_id,
        resolver_id="ops-reviewer-22",
        outcome="reaffirm",
        resolution="Conflicting feature was stale; authoritative source confirms the escalation basis.",
    )

    second_receipt = latch.rely(
        candidate_id=candidate.candidate_id,
        relying_actor="workflow-router",
        purpose="send downstream notification",
        scope="case-routing",
        action_ref="notify:enhanced-review",
    )

    verified, verification = ledger.verify()
    return {
        "candidate_confidence": candidate.confidence,
        "blocked_before_adoption": blocked_before_adoption,
        "self_adoption_blocked": self_adoption_blocked,
        "adoption_id": adoption.adoption_id,
        "first_reliance_receipt": first_receipt.receipt_id,
        "blocked_while_contested": blocked_while_contested,
        "second_reliance_receipt": second_receipt.receipt_id,
        "final_status": latch.status(candidate.candidate_id)["candidate"],
        "ledger_verified": verified,
        "ledger_verification": verification,
        "event_count": len(ledger.entries),
    }


def format_demo(result: dict[str, object]) -> str:
    return json.dumps(result, indent=2, sort_keys=True)
