"""Pure calculations and answer evaluation for The Receivables Challenge."""

from __future__ import annotations

from collections.abc import Mapping

from receivables_challenge.case_data import (
    AGING_BUCKETS,
    AGING_DECISIONS,
    AGING_LOSS_RATES,
    BEGINNING_ALLOWANCE,
    BEGINNING_NET_ACCOUNTS_RECEIVABLE,
    CLAIM_DECISIONS,
    CREDIT_DECISIONS,
    INVOICES,
    MANAGEMENT_DECISIONS,
    NET_CREDIT_SALES,
    PERCENTAGE_OF_RECEIVABLES_RATE,
    REPORTING_DECISIONS,
    VALUATION_BENEFIT_CORRECT,
)


def format_currency(value: int | float) -> str:
    """Format a whole-dollar amount for student-facing display."""

    rounded = round(value)
    if rounded < 0:
        return f"-${abs(rounded):,.0f}"
    return f"${rounded:,.0f}"


def decision_by_id(item_id: str):
    """Find any sequential case decision by its stable identifier."""

    for collection in (
        CLAIM_DECISIONS,
        CREDIT_DECISIONS,
        AGING_DECISIONS,
        REPORTING_DECISIONS,
        MANAGEMENT_DECISIONS,
    ):
        for item in collection:
            if item.id == item_id:
                return item
    raise KeyError(item_id)


def evaluate_decision(item_id: str, selected: str) -> dict[str, object]:
    item = decision_by_id(item_id)
    return {
        "correct": selected == item.correct,
        "selected": selected,
        "expected": item.correct,
        "explanation": item.explanation,
        "account_effect": item.account_effect,
        "statement_effect": item.statement_effect,
    }


def invoice_by_id(invoice_id: str):
    return next(invoice for invoice in INVOICES if invoice.id == invoice_id)


def evaluate_aging(responses: Mapping[str, str]) -> dict[str, dict[str, object]]:
    results = {}
    for invoice in INVOICES:
        selected = responses.get(invoice.id, "")
        results[invoice.id] = {
            "customer": invoice.customer,
            "selected": selected,
            "expected": invoice.correct_bucket,
            "correct": selected == invoice.correct_bucket,
        }
    return results


def aging_totals() -> dict[str, int]:
    totals = {bucket: 0 for bucket in AGING_BUCKETS}
    for invoice in INVOICES:
        totals[invoice.correct_bucket] += invoice.balance
    return totals


def gross_accounts_receivable() -> int:
    return sum(invoice.balance for invoice in INVOICES)


def aging_allowance_rows() -> list[dict[str, object]]:
    rows = []
    totals = aging_totals()
    for bucket in AGING_BUCKETS:
        balance = totals[bucket]
        rate = AGING_LOSS_RATES[bucket]
        rows.append(
            {
                "Age category": bucket,
                "Receivables": balance,
                "Estimated loss rate": rate,
                "Estimated uncollectible": round(balance * rate),
            }
        )
    return rows


def required_ending_allowance() -> int:
    return sum(int(row["Estimated uncollectible"]) for row in aging_allowance_rows())


def percentage_of_receivables_estimate() -> int:
    return round(gross_accounts_receivable() * PERCENTAGE_OF_RECEIVABLES_RATE)


def valuation_values() -> dict[str, int]:
    required = required_ending_allowance()
    increase = required - BEGINNING_ALLOWANCE
    return {
        "ending_allowance": required,
        "allowance_increase": increase,
        "bad_debt_increase": increase,
        "net_realizable_value": gross_accounts_receivable() - required,
    }


def evaluate_valuation(responses: Mapping[str, int], benefit: str) -> dict[str, object]:
    expected = valuation_values()
    fields = {
        key: {
            "submitted": int(responses.get(key, 0)),
            "expected": value,
            "correct": int(responses.get(key, 0)) == value,
        }
        for key, value in expected.items()
    }
    return {
        "fields": fields,
        "benefit": {
            "submitted": benefit,
            "expected": VALUATION_BENEFIT_CORRECT,
            "correct": benefit == VALUATION_BENEFIT_CORRECT,
        },
        "correct": all(result["correct"] for result in fields.values())
        and benefit == VALUATION_BENEFIT_CORRECT,
    }


def writeoff_comparison(amount: int = 14_000) -> dict[str, int]:
    values = valuation_values()
    gross_before = gross_accounts_receivable()
    allowance_before = values["ending_allowance"]
    gross_after = gross_before - amount
    allowance_after = allowance_before - amount
    return {
        "gross_before": gross_before,
        "allowance_before": allowance_before,
        "net_before": gross_before - allowance_before,
        "gross_after": gross_after,
        "allowance_after": allowance_after,
        "net_after": gross_after - allowance_after,
    }


def average_net_accounts_receivable() -> float:
    ending = valuation_values()["net_realizable_value"]
    return (BEGINNING_NET_ACCOUNTS_RECEIVABLE + ending) / 2


def receivables_turnover() -> float:
    return NET_CREDIT_SALES / average_net_accounts_receivable()


def average_collection_period() -> float:
    return 365 / receivables_turnover()


def dashboard_metrics() -> dict[str, int | float]:
    totals = aging_totals()
    gross = gross_accounts_receivable()
    overdue = gross - totals["Current"]
    over_60 = totals["61-90 days past due"] + totals["More than 90 days past due"]
    return {
        "gross_receivables": gross,
        "net_receivables": valuation_values()["net_realizable_value"],
        "overdue_amount": overdue,
        "overdue_percent": overdue / gross,
        "over_60_amount": over_60,
        "turnover": receivables_turnover(),
        "collection_period": average_collection_period(),
    }
