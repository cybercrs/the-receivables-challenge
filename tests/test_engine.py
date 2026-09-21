import unittest

from receivables_challenge.case_data import (
    AGING_BUCKETS,
    AGING_DECISIONS,
    CREDIT_DECISIONS,
    INVOICES,
    MANAGEMENT_DECISIONS,
    REPORTING_DECISIONS,
    VALUATION_BENEFIT_CORRECT,
    VALUATION_FIELDS,
)
from receivables_challenge.engine import (
    aging_totals,
    average_collection_period,
    dashboard_metrics,
    evaluate_aging,
    evaluate_decision,
    evaluate_valuation,
    gross_accounts_receivable,
    percentage_of_receivables_estimate,
    receivables_turnover,
    required_ending_allowance,
    valuation_values,
    writeoff_comparison,
)


class ReceivablesEngineTests(unittest.TestCase):
    def test_aging_schedule_reconciles_to_gross_receivables(self):
        totals = aging_totals()
        self.assertEqual(list(totals), list(AGING_BUCKETS))
        self.assertEqual(sum(totals.values()), 118_000)
        self.assertEqual(gross_accounts_receivable(), 118_000)
        self.assertEqual(totals["More than 90 days past due"], 14_000)

    def test_aging_estimate_and_account_increases(self):
        self.assertEqual(required_ending_allowance(), 22_180)
        self.assertEqual(
            valuation_values(),
            {
                "ending_allowance": 22_180,
                "allowance_increase": 18_180,
                "bad_debt_increase": 18_180,
                "net_realizable_value": 95_820,
            },
        )
        self.assertEqual(percentage_of_receivables_estimate(), 9_440)

    def test_specific_writeoff_preserves_net_realizable_value(self):
        comparison = writeoff_comparison()
        self.assertEqual(comparison["gross_before"] - comparison["gross_after"], 14_000)
        self.assertEqual(comparison["allowance_before"] - comparison["allowance_after"], 14_000)
        self.assertEqual(comparison["allowance_after"], 8_180)
        self.assertEqual(comparison["net_before"], 95_820)
        self.assertEqual(comparison["net_after"], 95_820)

    def test_liquidity_metrics(self):
        self.assertAlmostEqual(receivables_turnover(), 6.9002, places=3)
        self.assertAlmostEqual(average_collection_period(), 52.8966, places=3)
        metrics = dashboard_metrics()
        self.assertEqual(metrics["over_60_amount"], 32_000)
        self.assertAlmostEqual(metrics["overdue_percent"], 82_000 / 118_000)

    def test_decision_evaluation_includes_both_effects(self):
        result = evaluate_decision("service_on_account", "Accounts receivable")
        self.assertTrue(result["correct"])
        self.assertIn("increases", result["account_effect"])
        self.assertIn("net income", result["statement_effect"])

    def test_aging_and_valuation_evaluation(self):
        aging = {invoice.id: invoice.correct_bucket for invoice in INVOICES}
        self.assertTrue(all(item["correct"] for item in evaluate_aging(aging).values()))
        result = evaluate_valuation(valuation_values(), VALUATION_BENEFIT_CORRECT)
        self.assertTrue(result["correct"])

    def test_refined_learning_tasks_match_course_scope(self):
        self.assertEqual(len(AGING_DECISIONS), 4)
        self.assertTrue(all("credit decision" not in item.prompt.lower() for item in CREDIT_DECISIONS))
        self.assertNotIn("writeoff_control", {item.id for item in REPORTING_DECISIONS})
        bad_debt = next(item for item in REPORTING_DECISIONS if item.id == "bad_debt_location")
        self.assertEqual(bad_debt.correct, "Operating expense")
        balance_sheet = next(item for item in REPORTING_DECISIONS if item.id == "balance_sheet")
        self.assertTrue(any("disclose the allowance only in the notes" in option for option in balance_sheet.options))
        nrv_label = dict(VALUATION_FIELDS)["net_realizable_value"]
        self.assertIn("balance sheet after the bad debt adjustment", nrv_label)
        self.assertTrue(all("rounded" not in item.prompt.lower() for item in MANAGEMENT_DECISIONS))


if __name__ == "__main__":
    unittest.main()
