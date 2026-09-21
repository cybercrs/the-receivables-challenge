import re
import unittest

from streamlit.testing.v1 import AppTest

from receivables_challenge.case_data import (
    AGING_DECISIONS,
    CLAIM_DECISIONS,
    CREDIT_DECISIONS,
    MANAGEMENT_DECISIONS,
    REPORTING_DECISIONS,
    VALUATION_BENEFIT_CORRECT,
    VALUATION_FIELDS,
)
from receivables_challenge.engine import valuation_values
from receivables_challenge.progress import (
    SNAPSHOT_PARAM,
    activity_defaults,
    decode_snapshot,
    encode_state,
)


def button(app: AppTest, label: str):
    return next(item for item in app.button if item.label == label)


def assert_feedback_dollars_are_escaped(test_case, app):
    for collection in (app.success, app.warning, app.info, app.caption):
        for item in collection:
            test_case.assertIsNone(re.search(r"(?<!\\)\$", str(item.value)), item.value)


class PerfectReceivablesFlowTests(unittest.TestCase):
    def test_dollar_amounts_in_feedback_are_escaped(self):
        state = activity_defaults()
        state["rc_stage"] = 5
        state["rc_claim_index"] = len(CLAIM_DECISIONS) - 1
        state["rc_claim_responses"] = {item.id: item.correct for item in CLAIM_DECISIONS}
        state["rc_credit_index"] = len(CREDIT_DECISIONS) - 1
        state["rc_credit_responses"] = {item.id: item.correct for item in CREDIT_DECISIONS}
        state["rc_aging_index"] = len(AGING_DECISIONS) - 1
        state["rc_aging_responses"] = {item.id: item.correct for item in AGING_DECISIONS}
        state["rc_valuation_responses"] = valuation_values()
        state["rc_valuation_benefit"] = VALUATION_BENEFIT_CORRECT
        state["rc_valuation_submitted"] = True

        app = AppTest.from_file("streamlit_app.py", default_timeout=90)
        app.query_params[SNAPSHOT_PARAM] = encode_state(state)
        app.run()
        item = REPORTING_DECISIONS[0]
        wrong = next(option for option in item.options if option != item.correct)
        app.radio(key=f"widget_reporting_{item.id}").set_value(wrong)
        button(app, "Check the reporting decision").click().run()

        assert_feedback_dollars_are_escaped(self, app)

    def test_draft_restores_and_wrong_answer_revises_in_one_check(self):
        app = AppTest.from_file("streamlit_app.py", default_timeout=90).run()
        button(app, "Open the receivables file").click().run()
        item = CLAIM_DECISIONS[0]
        wrong = next(option for option in item.options if option != item.correct)

        self.assertNotEqual(app.radio(key=f"widget_claim_{item.id}").options, list(item.options))
        app.radio(key=f"widget_claim_{item.id}").set_value(wrong).run()
        saved_value = app.query_params[SNAPSHOT_PARAM]
        saved = decode_snapshot(saved_value[0] if isinstance(saved_value, list) else saved_value)
        self.assertEqual(saved["rc_drafts"]["claims"][item.id], wrong)

        button(app, "Check the claim").click().run()
        self.assertTrue(any(item.label == "Check revised response" for item in app.button))
        app.radio(key=f"widget_claim_{item.id}").set_value(item.correct)
        button(app, "Check revised response").click().run()

        self.assertEqual(app.session_state.rc_claim_responses[item.id], item.correct)
        self.assertTrue(any(item.label == "Continue" for item in app.button))

    def test_complete_case_reaches_debrief_with_allowed_reasoning(self):
        app = AppTest.from_file("streamlit_app.py", default_timeout=90).run()
        self.assertFalse(app.exception)
        button(app, "Open the receivables file").click().run()

        for item in CLAIM_DECISIONS:
            app.radio(key=f"widget_claim_{item.id}").set_value(item.correct)
            button(app, "Check the claim").click().run()
            button(app, "Continue").click().run()

        for item in CREDIT_DECISIONS:
            app.radio(key=f"widget_credit_{item.id}").set_value(item.correct)
            button(app, "Check the tradeoff").click().run()
            button(app, "Continue").click().run()

        for item in AGING_DECISIONS:
            app.radio(key=f"widget_aging_{item.id}").set_value(item.correct)
            button(app, "Check the interpretation").click().run()
            button(app, "Continue").click().run()

        self.assertEqual(len(app.dataframe), 1)
        valuation_schedule = app.dataframe[0].value
        self.assertEqual(len(valuation_schedule), 5)
        self.assertNotIn("Total", valuation_schedule["Age category"].tolist())
        self.assertTrue(
            all("$22,180" not in str(item.value) for item in app.markdown),
            "Step 4 should require students to total the aging estimates.",
        )

        expected = valuation_values()
        for key, _label in VALUATION_FIELDS:
            app.number_input(key=f"widget_valuation_{key}").set_value(expected[key])
        app.radio(key="widget_valuation_benefit").set_value(VALUATION_BENEFIT_CORRECT)
        button(app, "Check the valuation").click().run()
        button(app, "Continue to reporting").click().run()

        for item in REPORTING_DECISIONS:
            app.radio(key=f"widget_reporting_{item.id}").set_value(item.correct)
            button(app, "Check the reporting decision").click().run()
            button(app, "Continue").click().run()

        for item in MANAGEMENT_DECISIONS:
            app.radio(key=f"widget_management_{item.id}").set_value(item.correct)
            button(app, "Check the management decision").click().run()
            label = "Finish the case" if item is MANAGEMENT_DECISIONS[-1] else "Continue"
            button(app, label).click().run()

        self.assertFalse(app.exception)
        self.assertTrue(any("Case complete" in item.value for item in app.success))
        self.assertIn("final mastery: complete", "\n".join(item.value for item in app.caption).lower())
        self.assertEqual(len(app.expander), 4)
        self.assertTrue(all(item.label.endswith("?") for item in app.expander))

        rendered = "\n".join(item.value for item in app.markdown).lower()
        self.assertNotIn("chapter 8", rendered)
        for banned in (r"\bdebits?\b", r"\bjournal entries?\b", r"\bledger\b", r"\bposting\b"):
            self.assertIsNone(re.search(banned, rendered), banned)

        saved_value = app.query_params[SNAPSHOT_PARAM]
        saved = decode_snapshot(saved_value[0] if isinstance(saved_value, list) else saved_value)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["rc_stage"], 7)
        self.assertEqual(len(saved["rc_management_responses"]), len(MANAGEMENT_DECISIONS))


if __name__ == "__main__":
    unittest.main()
