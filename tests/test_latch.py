import unittest

from latch_boundary import BoundaryRefusal, Latch
from latch_boundary.ledger import HashLedger


class LatchTests(unittest.TestCase):
    def setUp(self):
        self.latch = Latch()
        self.latch.submit_candidate(
            candidate_id="J-1",
            proposition="Escalate case",
            source="model-x",
            confidence=0.99,
            evidence_refs=("e:1",),
        )

    def adopt(self):
        return self.latch.adopt(
            candidate_id="J-1",
            adopter_id="reviewer-1",
            adopter_kind="human",
            authority_ref="role:controller",
            scope="routing",
            basis_refs=("policy:1",),
        )

    def test_high_confidence_is_not_reliance_authority(self):
        with self.assertRaisesRegex(BoundaryRefusal, "not been explicitly adopted"):
            self.latch.rely(
                candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:1"
            )

    def test_model_cannot_self_adopt(self):
        with self.assertRaisesRegex(BoundaryRefusal, "cannot adopt itself"):
            self.latch.adopt(
                candidate_id="J-1",
                adopter_id="model-x",
                adopter_kind="model",
                authority_ref="generated:yes",
                scope="routing",
                basis_refs=("confidence:0.99",),
            )

    def test_adoption_requires_authority(self):
        with self.assertRaisesRegex(BoundaryRefusal, "authority_ref"):
            self.latch.adopt(
                candidate_id="J-1",
                adopter_id="reviewer-1",
                adopter_kind="human",
                authority_ref="",
                scope="routing",
                basis_refs=("policy:1",),
            )

    def test_adoption_requires_basis(self):
        with self.assertRaisesRegex(BoundaryRefusal, "basis_ref"):
            self.latch.adopt(
                candidate_id="J-1",
                adopter_id="reviewer-1",
                adopter_kind="human",
                authority_ref="role:controller",
                scope="routing",
                basis_refs=(),
            )

    def test_adopted_judgement_can_be_relied_on_in_scope(self):
        adoption = self.adopt()
        receipt = self.latch.rely(
            candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:1"
        )
        self.assertEqual(receipt.adoption_id, adoption.adoption_id)

    def test_scope_mismatch_is_blocked(self):
        self.adopt()
        with self.assertRaisesRegex(BoundaryRefusal, "does not match"):
            self.latch.rely(
                candidate_id="J-1", relying_actor="notifier", purpose="notify", scope="customer-contact", action_ref="a:2"
            )

    def test_challenge_suspends_reliance(self):
        self.adopt()
        self.latch.challenge(candidate_id="J-1", challenger_id="qa", reason="conflicting evidence")
        with self.assertRaisesRegex(BoundaryRefusal, "contested"):
            self.latch.rely(
                candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:2"
            )

    def test_ambiguous_uphold_outcome_is_rejected(self):
        self.adopt()
        challenge = self.latch.challenge(candidate_id="J-1", challenger_id="qa", reason="conflicting evidence")
        with self.assertRaisesRegex(BoundaryRefusal, "reaffirm"):
            self.latch.resolve_challenge(
                challenge_id=challenge.challenge_id,
                resolver_id="reviewer-2",
                outcome="uphold",
                resolution="ambiguous outcome should not be accepted",
            )

    def test_reaffirmed_challenge_restores_prior_adoption(self):
        self.adopt()
        c = self.latch.challenge(candidate_id="J-1", challenger_id="qa", reason="conflicting evidence")
        self.latch.resolve_challenge(
            challenge_id=c.challenge_id, resolver_id="reviewer-2", outcome="reaffirm", resolution="evidence resolved"
        )
        receipt = self.latch.rely(
            candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:3"
        )
        self.assertTrue(receipt.receipt_id.startswith("rely_"))

    def test_reliance_stays_suspended_until_all_challenges_are_resolved(self):
        self.adopt()
        first = self.latch.challenge(candidate_id="J-1", challenger_id="qa-1", reason="conflicting evidence")
        second = self.latch.challenge(candidate_id="J-1", challenger_id="qa-2", reason="source provenance disputed")

        self.latch.resolve_challenge(
            challenge_id=first.challenge_id,
            resolver_id="reviewer-2",
            outcome="reaffirm",
            resolution="first concern resolved",
        )

        self.assertEqual(self.latch.status("J-1")["candidate"]["status"], "contested")
        self.assertEqual(len(self.latch.status("J-1")["open_challenges"]), 1)
        with self.assertRaisesRegex(BoundaryRefusal, "unresolved challenges"):
            self.latch.rely(
                candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:multi-1"
            )

        self.latch.resolve_challenge(
            challenge_id=second.challenge_id,
            resolver_id="reviewer-3",
            outcome="reaffirm",
            resolution="second concern resolved",
        )

        self.assertEqual(self.latch.status("J-1")["candidate"]["status"], "adopted")
        receipt = self.latch.rely(
            candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:multi-2"
        )
        self.assertTrue(receipt.receipt_id.startswith("rely_"))

    def test_withdrawal_remains_terminal_when_sibling_challenge_is_later_reaffirmed(self):
        self.adopt()
        withdraw_challenge = self.latch.challenge(candidate_id="J-1", challenger_id="qa-1", reason="invalid source")
        sibling = self.latch.challenge(candidate_id="J-1", challenger_id="qa-2", reason="separate provenance concern")

        self.latch.resolve_challenge(
            challenge_id=withdraw_challenge.challenge_id,
            resolver_id="reviewer-2",
            outcome="withdraw",
            resolution="source invalidates the judgement",
        )
        self.assertEqual(self.latch.status("J-1")["candidate"]["status"], "withdrawn")

        self.latch.resolve_challenge(
            challenge_id=sibling.challenge_id,
            resolver_id="reviewer-3",
            outcome="reaffirm",
            resolution="separate concern resolved",
        )
        self.assertEqual(self.latch.status("J-1")["candidate"]["status"], "withdrawn")
        self.assertIsNone(self.latch.status("J-1")["active_adoption"])

    def test_withdrawn_challenge_revokes_reliance(self):
        self.adopt()
        c = self.latch.challenge(candidate_id="J-1", challenger_id="qa", reason="bad input")
        self.latch.resolve_challenge(
            challenge_id=c.challenge_id, resolver_id="reviewer-2", outcome="withdraw", resolution="input invalid"
        )
        with self.assertRaisesRegex(BoundaryRefusal, "not been explicitly adopted"):
            self.latch.rely(
                candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:4"
            )

    def test_duplicate_active_adoption_is_refused(self):
        self.adopt()
        with self.assertRaisesRegex(BoundaryRefusal, "already has active adoption"):
            self.adopt()

    def test_ledger_verifies(self):
        self.adopt()
        self.latch.rely(candidate_id="J-1", relying_actor="router", purpose="route", scope="routing", action_ref="a:1")
        ok, message = self.latch.ledger.verify()
        self.assertTrue(ok, message)

    def test_tampered_ledger_fails_verification(self):
        self.adopt()
        entries = [dict(x) for x in self.latch.ledger.entries]
        entries[0] = dict(entries[0])
        entries[0]["payload"] = dict(entries[0]["payload"])
        entries[0]["payload"]["proposition"] = "tampered"
        ok, _ = HashLedger.from_entries(entries).verify()
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
