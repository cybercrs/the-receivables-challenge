"""Known teaching cases used by the actual browser walkthrough."""

from receivables_challenge import case_data as data, engine
from receivables_challenge.progress import (
    decode_snapshot as decode_snapshot,
    score_summary as score_summary,
)
from browser.navigation import POSITIONS as POSITIONS


def choice(items, check, final="Continue"):
    return {"kind": "choice", "items": items, "check": check, "final": final}


def numbers(values, fields, prefix, check, final=None, radios=()):
    return {
        "kind": "numbers",
        "values": values,
        "fields": fields,
        "prefix": prefix,
        "check": check,
        "final": final,
        "radios": radios,
    }


START = "Open the receivables file"
PLAN = [
    choice(data.CLAIM_DECISIONS, "Check the claim"),
    choice(data.CREDIT_DECISIONS, "Check the tradeoff"),
    choice(data.AGING_DECISIONS, "Check the interpretation"),
    numbers(
        engine.valuation_values(),
        data.VALUATION_FIELDS,
        "widget_valuation_",
        "Check the valuation",
        "Continue to reporting",
        [("widget_valuation_benefit", data.VALUATION_BENEFIT_CORRECT)],
    ),
    choice(data.REPORTING_DECISIONS, "Check the reporting decision"),
    choice(
        data.MANAGEMENT_DECISIONS, "Check the management decision", "Finish the case"
    ),
]
