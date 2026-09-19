import re
import unittest

from streamlit.testing.v1 import AppTest

from receivables_challenge.case_data import (
    CLAIM_DECISIONS,
    CREDIT_DECISIONS,
    INVOICES,
    MANAGEMENT_DECISIONS,
    REPORTING_DECISIONS,
    VALUATION_FIELDS,
)
from receivables_challenge.engine import valuation_values
from receivables_challenge.progress import SNAPSHOT_PARAM, decode_snapshot


def button(app: AppTest, label: str):
    return next(item for item in app.button if item.label == label)


class PerfectReceivablesFlowTests(unittest.TestCase):
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
            button(app, "Evaluate the customer").click().run()
            button(app, "Continue").click().run()

        for invoice in INVOICES:
            app.selectbox(key=f"widget_aging_{invoice.id}").set_value(invoice.correct_bucket)
        button(app, "Check the aging schedule").click().run()
        button(app, "Continue to valuation").click().run()

        expected = valuation_values()
        for key, _label in VALUATION_FIELDS:
            app.number_input(key=f"widget_valuation_{key}").set_value(expected[key])
        app.radio(key="widget_valuation_method").set_value("Aging analysis")
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

        rendered = "\n".join(item.value for item in app.markdown).lower()
        for banned in (r"\bdebits?\b", r"\bjournal entries?\b", r"\bledger\b", r"\bposting\b"):
            self.assertIsNone(re.search(banned, rendered), banned)

        saved_value = app.query_params[SNAPSHOT_PARAM]
        saved = decode_snapshot(saved_value[0] if isinstance(saved_value, list) else saved_value)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["rc_stage"], 7)
        self.assertEqual(len(saved["rc_management_responses"]), len(MANAGEMENT_DECISIONS))


if __name__ == "__main__":
    unittest.main()
