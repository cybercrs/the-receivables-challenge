import base64
import json
import unittest
import zlib

from receivables_challenge.case_data import (
    CLAIM_DECISIONS,
    CREDIT_DECISIONS,
    INVOICES,
    MANAGEMENT_DECISIONS,
    REPORTING_DECISIONS,
)
from receivables_challenge.engine import valuation_values
from receivables_challenge.progress import (
    SNAPSHOT_PARAM,
    activity_defaults,
    decode_snapshot,
    encode_state,
    record_attempt,
    reset_saved_progress,
    restore_session_state,
    score_summary,
    snapshot_from_state,
)


def encode_raw(payload):
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(zlib.compress(raw)).decode("ascii").rstrip("=")


def completed_state():
    state = activity_defaults()
    state["rc_stage"] = 7
    state["rc_claim_index"] = len(CLAIM_DECISIONS) - 1
    state["rc_claim_responses"] = {item.id: item.correct for item in CLAIM_DECISIONS}
    state["rc_credit_index"] = len(CREDIT_DECISIONS) - 1
    state["rc_credit_responses"] = {item.id: item.correct for item in CREDIT_DECISIONS}
    state["rc_aging_responses"] = {invoice.id: invoice.correct_bucket for invoice in INVOICES}
    state["rc_aging_submitted"] = True
    state["rc_valuation_responses"] = valuation_values()
    state["rc_valuation_method"] = "Aging analysis"
    state["rc_valuation_submitted"] = True
    state["rc_reporting_index"] = len(REPORTING_DECISIONS) - 1
    state["rc_reporting_responses"] = {item.id: item.correct for item in REPORTING_DECISIONS}
    state["rc_management_index"] = len(MANAGEMENT_DECISIONS) - 1
    state["rc_management_responses"] = {item.id: item.correct for item in MANAGEMENT_DECISIONS}
    return state


class ProgressSnapshotTests(unittest.TestCase):
    def test_round_trip_completed_progress(self):
        state = completed_state()
        token = encode_state(state)
        restored = decode_snapshot(token)
        self.assertIsNotNone(restored)
        self.assertEqual(restored["rc_stage"], 7)
        self.assertEqual(restored["rc_valuation_responses"]["ending_allowance"], 22_180)
        self.assertNotIn("name", token.lower())
        self.assertNotIn("email", token.lower())

    def test_current_incorrect_answer_can_be_restored_for_revision(self):
        state = activity_defaults()
        state["rc_stage"] = 1
        first = CLAIM_DECISIONS[0]
        state["rc_claim_responses"] = {first.id: first.options[-1]}
        record_attempt(state, f"claim:{first.id}", False)
        restored = decode_snapshot(encode_state(state))
        self.assertIsNotNone(restored)
        self.assertFalse(restored["rc_first_pass"][f"claim:{first.id}"])

    def test_unsubmitted_draft_and_shuffle_seed_survive_refresh(self):
        state = activity_defaults()
        state["rc_stage"] = 1
        state["rc_shuffle_seed"] = 34108
        first = CLAIM_DECISIONS[0]
        state["rc_drafts"]["claims"][first.id] = first.correct

        restored = decode_snapshot(encode_state(state))

        self.assertIsNotNone(restored)
        self.assertEqual(restored["rc_shuffle_seed"], 34108)
        self.assertEqual(restored["rc_drafts"]["claims"][first.id], first.correct)

    def test_partial_valuation_draft_survives_refresh(self):
        state = activity_defaults()
        state["rc_stage"] = 4
        state["rc_claim_index"] = len(CLAIM_DECISIONS) - 1
        state["rc_claim_responses"] = {item.id: item.correct for item in CLAIM_DECISIONS}
        state["rc_credit_index"] = len(CREDIT_DECISIONS) - 1
        state["rc_credit_responses"] = {item.id: item.correct for item in CREDIT_DECISIONS}
        state["rc_aging_responses"] = {invoice.id: invoice.correct_bucket for invoice in INVOICES}
        state["rc_aging_submitted"] = True
        state["rc_drafts"]["valuation"] = {
            "ending_allowance": 22_180,
            "method": "Aging analysis",
        }

        restored = decode_snapshot(encode_state(state))

        self.assertIsNotNone(restored)
        self.assertEqual(restored["rc_drafts"]["valuation"]["ending_allowance"], 22_180)
        self.assertEqual(restored["rc_drafts"]["valuation"]["method"], "Aging analysis")

    def test_future_draft_is_rejected(self):
        state = activity_defaults()
        state["rc_stage"] = 1
        item = MANAGEMENT_DECISIONS[0]
        state["rc_drafts"]["management"][item.id] = item.correct
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_skipped_stage_is_rejected(self):
        state = activity_defaults()
        state["rc_stage"] = 4
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_tampered_completed_valuation_is_rejected(self):
        state = completed_state()
        state["rc_valuation_responses"]["ending_allowance"] = 9_440
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_malformed_and_oversized_tokens_are_rejected(self):
        self.assertIsNone(decode_snapshot("not-a-valid-token"))
        self.assertIsNone(decode_snapshot("x" * 16_001))

    def test_unknown_snapshot_keys_are_rejected(self):
        raw = snapshot_from_state(activity_defaults())
        raw["unexpected"] = True
        self.assertIsNone(decode_snapshot(encode_raw(raw)))

    def test_restore_reset_and_score_summary(self):
        destination = {}
        self.assertTrue(restore_session_state(destination, encode_state(completed_state())))
        self.assertEqual(destination["rc_stage"], 7)

        query = {}
        reset_saved_progress(destination, query)
        self.assertEqual(destination["rc_stage"], 0)
        self.assertEqual(destination["rc_claim_responses"], {})
        self.assertIn(SNAPSHOT_PARAM, query)
        self.assertIsNotNone(decode_snapshot(query[SNAPSHOT_PARAM]))

        state = activity_defaults()
        record_attempt(state, "claim:service_on_account", False)
        record_attempt(state, "claim:service_on_account", True)
        record_attempt(state, "claim:customer_note", True)
        score = score_summary(state)
        self.assertEqual(score["attempted"], 2)
        self.assertEqual(score["correct"], 1)
        self.assertEqual(score["revisions"], 1)


if __name__ == "__main__":
    unittest.main()
