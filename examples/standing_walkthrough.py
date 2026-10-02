"""Run the existing Latch boundary and retain a readable evidence trace.

Run from a checkout with Python 3.11+: python examples/standing_walkthrough.py
No model, remote service, or external action is called.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from latch_boundary import BoundaryRefusal, Latch
from latch_boundary.ledger import HashLedger


def run(output_dir: Path) -> dict:
    # Never append a second demonstration to an earlier retained run.
    output_dir.mkdir(parents=True, exist_ok=False)
    ledger = HashLedger(output_dir / "ledger.jsonl")
    boundary = Latch(ledger)
    boundary.submit_candidate(
        candidate_id="J-0042",
        proposition="Escalate the account for enhanced review.",
        source="risk-model-v7",
        confidence=0.97,
        evidence_refs=("case:8841", "feature-set:2026-09-22"),
    )
    rows = []

    def attempt(label, operation, expected):
        before = len(boundary.receipts)
        try:
            value = operation()
            outcome, detail = "ALLOWED", value.to_dict()
        except BoundaryRefusal as exc:
            outcome, detail = "REFUSED", str(exc)
        state = boundary.status("J-0042")
        row = {
            "step": label,
            "outcome": outcome,
            "expected": expected,
            "candidate_status": state["candidate"]["status"],
            "confidence": state["candidate"]["confidence"],
            "open_challenges": len(state["open_challenges"]),
            "new_receipts": len(boundary.receipts) - before,
            "total_receipts": len(boundary.receipts),
            "detail": detail,
        }
        rows.append(row)
        if outcome != expected:
            raise RuntimeError(f"Unexpected result in {label}: {outcome}")
        if outcome == "REFUSED" and row["new_receipts"]:
            raise RuntimeError(f"Refusal issued a receipt in {label}")
        return value if outcome == "ALLOWED" else None

    def rely(scope="case-routing"):
        return boundary.rely(
            candidate_id="J-0042", relying_actor="workflow-router",
            purpose="record eligibility for case routing", scope=scope,
            action_ref="demo:route-request",
        )

    attempt("Candidate at 97% confidence", rely, "REFUSED")
    attempt("Adoption with model kind", lambda: boundary.adopt(
        candidate_id="J-0042", adopter_id="risk-model-v7", adopter_kind="model",
        authority_ref="generated:approval", scope="case-routing",
        basis_refs=("confidence:0.97",),
    ), "REFUSED")
    boundary.adopt(
        candidate_id="J-0042", adopter_id="ops-reviewer-17", adopter_kind="human",
        authority_ref="role:enhanced-review-controller", scope="case-routing",
        basis_refs=("case:8841", "policy:ER-12"),
    )
    attempt("Adopted for case routing", rely, "ALLOWED")
    attempt("Attempt customer contact scope", lambda: rely("customer-contact"), "REFUSED")
    first = boundary.challenge(candidate_id="J-0042", challenger_id="qa-1", reason="Input feature disputed")
    second = boundary.challenge(candidate_id="J-0042", challenger_id="qa-2", reason="Source basis disputed")
    attempt("Two open challenges", rely, "REFUSED")
    boundary.resolve_challenge(challenge_id=first.challenge_id, resolver_id="reviewer-22", outcome="reaffirm", resolution="First concern resolved in the synthetic scenario")
    attempt("One challenge still open", rely, "REFUSED")
    boundary.resolve_challenge(challenge_id=second.challenge_id, resolver_id="reviewer-23", outcome="reaffirm", resolution="Second concern resolved in the synthetic scenario")
    attempt("Both challenges resolved", rely, "ALLOWED")
    final = boundary.challenge(candidate_id="J-0042", challenger_id="qa-3", reason="Basis withdrawn")
    boundary.resolve_challenge(challenge_id=final.challenge_id, resolver_id="reviewer-24", outcome="withdraw", resolution="Withdraw adoption in the synthetic scenario")
    attempt("Adoption withdrawn", rely, "REFUSED")

    ok, message = ledger.verify()
    if not ok:
        raise RuntimeError(message)
    files = [*sorted((ROOT / "src" / "latch_boundary").glob("*.py")), Path(__file__).resolve()]
    result = {
        "title": "When does an AI judgement become usable?",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "engine_baseline_commit": "2711ad534fcb0f60b5080aa875d579c424504d6a",
        "execution": "Fresh local execution of unchanged engine with this demonstration driver",
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "rows": rows,
        "receipt_count": len(boundary.receipts),
        "ledger": {"verified": ok, "message": message, "events": len(ledger.entries)},
        "limits": [
            "Synthetic declared confidence; no model inference or classification evaluation",
            "Local actor labels and authority references; no authenticated principal separation",
            "Receipts are recorded; no account routing, customer contact or external execution occurs",
            "Refusals are captured by this driver, not appended as refusal events by the engine",
            "Hash verification establishes internal chain consistency, not trusted external custody",
        ],
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Latch: confidence stays at 97%; eligibility changes.\n")
    for row in rows:
        print(f"{row['outcome']:7} | {row['step']} | new receipts: {row['new_receipts']}")
    print(f"\n{message}; {len(boundary.receipts)} reliance receipts.")
    print("No external action is performed. Evidence:", output_dir)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(".demo") / datetime.now(timezone.utc).strftime("standing-%Y%m%dT%H%M%S%fZ"))
    run(parser.parse_args().output_dir)
