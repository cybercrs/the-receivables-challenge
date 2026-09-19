"""Compact, validated, non-identifying progress snapshots."""

from __future__ import annotations

import base64
import json
import zlib
from collections.abc import MutableMapping
from typing import Any

from receivables_challenge.case_data import (
    AGING_BUCKETS,
    CLAIM_DECISIONS,
    CREDIT_DECISIONS,
    INVOICES,
    MANAGEMENT_DECISIONS,
    REPORTING_DECISIONS,
    VALUATION_FIELDS,
)
from receivables_challenge.engine import evaluate_valuation


SNAPSHOT_PARAM = "progress"
SNAPSHOT_VERSION = 1
MAX_TOKEN_LENGTH = 12_000
MAX_JSON_BYTES = 24_000
VALUATION_METHODS = ("Percentage of receivables", "Aging analysis")


def activity_defaults() -> dict[str, Any]:
    return {
        "rc_stage": 0,
        "rc_claim_index": 0,
        "rc_claim_responses": {},
        "rc_credit_index": 0,
        "rc_credit_responses": {},
        "rc_aging_responses": {},
        "rc_aging_submitted": False,
        "rc_valuation_responses": {},
        "rc_valuation_method": "",
        "rc_valuation_submitted": False,
        "rc_reporting_index": 0,
        "rc_reporting_responses": {},
        "rc_management_index": 0,
        "rc_management_responses": {},
        "rc_attempts": {},
        "rc_first_pass": {},
    }


def _encode(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def _decode(token: str) -> object:
    padding = "=" * (-len(token) % 4)
    compressed = base64.b64decode(token + padding, altchars=b"-_", validate=True)
    decompressor = zlib.decompressobj()
    raw = decompressor.decompress(compressed, MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES or decompressor.unconsumed_tail:
        raise ValueError("Snapshot is too large")
    raw += decompressor.flush(MAX_JSON_BYTES + 1 - len(raw))
    if len(raw) > MAX_JSON_BYTES or decompressor.unused_data:
        raise ValueError("Snapshot is invalid")
    return json.loads(raw.decode("utf-8"))


def _require_index(value: object, count: int) -> int:
    if type(value) is not int or not 0 <= value < count:
        raise ValueError("Invalid activity index")
    return value


def _answer_prefix(raw: object, items) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError("Answers must be an object")
    ids = [item.id for item in items]
    if set(raw) != set(ids[: len(raw)]):
        raise ValueError("Answers must follow the activity order")
    normalized = {}
    for item in items[: len(raw)]:
        value = raw[item.id]
        if not isinstance(value, str) or value not in item.options:
            raise ValueError("Unknown answer")
        normalized[item.id] = value
    return normalized


def _validate_aging(raw: object, submitted: bool) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError("Aging answers must be an object")
    ids = {invoice.id for invoice in INVOICES}
    if set(raw) - ids:
        raise ValueError("Unknown invoice")
    if submitted and set(raw) != ids:
        raise ValueError("Submitted aging schedule is incomplete")
    normalized = {}
    for key, value in raw.items():
        if not isinstance(value, str) or value not in AGING_BUCKETS:
            raise ValueError("Unknown aging category")
        normalized[key] = value
    return normalized


def _validate_valuation(raw: object, submitted: bool) -> dict[str, int]:
    if not isinstance(raw, dict):
        raise ValueError("Valuation answers must be an object")
    keys = {key for key, _label in VALUATION_FIELDS}
    if set(raw) - keys:
        raise ValueError("Unknown valuation field")
    if submitted and set(raw) != keys:
        raise ValueError("Submitted valuation is incomplete")
    normalized = {}
    for key, value in raw.items():
        if type(value) is not int or not 0 <= value <= 10_000_000:
            raise ValueError("Invalid valuation amount")
        normalized[key] = value
    return normalized


def _valid_score_keys() -> set[str]:
    keys = {f"claim:{item.id}" for item in CLAIM_DECISIONS}
    keys |= {f"credit:{item.id}" for item in CREDIT_DECISIONS}
    keys |= {f"aging:{invoice.id}" for invoice in INVOICES}
    keys |= {f"valuation:{key}" for key, _label in VALUATION_FIELDS}
    keys.add("valuation:method")
    keys |= {f"reporting:{item.id}" for item in REPORTING_DECISIONS}
    keys |= {f"management:{item.id}" for item in MANAGEMENT_DECISIONS}
    return keys


def _all_correct(responses: dict[str, str], items) -> bool:
    return len(responses) == len(items) and all(responses[item.id] == item.correct for item in items)


def validate_snapshot(raw: object) -> dict[str, Any]:
    expected_keys = {
        "v", "s", "ci", "cr", "di", "dr", "ar", "as", "vr", "vm", "vs",
        "ri", "rr", "mi", "mr", "at", "fp",
    }
    if not isinstance(raw, dict) or set(raw) != expected_keys or raw["v"] != SNAPSHOT_VERSION:
        raise ValueError("Unsupported snapshot")

    stage = raw["s"]
    if type(stage) is not int or not 0 <= stage <= 7:
        raise ValueError("Invalid stage")

    claim_index = _require_index(raw["ci"], len(CLAIM_DECISIONS))
    credit_index = _require_index(raw["di"], len(CREDIT_DECISIONS))
    reporting_index = _require_index(raw["ri"], len(REPORTING_DECISIONS))
    management_index = _require_index(raw["mi"], len(MANAGEMENT_DECISIONS))

    claims = _answer_prefix(raw["cr"], CLAIM_DECISIONS)
    credits = _answer_prefix(raw["dr"], CREDIT_DECISIONS)
    reporting = _answer_prefix(raw["rr"], REPORTING_DECISIONS)
    management = _answer_prefix(raw["mr"], MANAGEMENT_DECISIONS)

    aging_submitted = raw["as"]
    valuation_submitted = raw["vs"]
    if type(aging_submitted) is not bool or type(valuation_submitted) is not bool:
        raise ValueError("Invalid submission status")
    aging = _validate_aging(raw["ar"], aging_submitted)
    valuation = _validate_valuation(raw["vr"], valuation_submitted)
    method = raw["vm"]
    if not isinstance(method, str) or method not in ("", *VALUATION_METHODS):
        raise ValueError("Invalid valuation method")
    if valuation_submitted and method not in VALUATION_METHODS:
        raise ValueError("Submitted valuation method is missing")

    if not isinstance(raw["at"], dict) or not isinstance(raw["fp"], dict):
        raise ValueError("Invalid score history")
    valid_score_keys = _valid_score_keys()
    attempts = {}
    for key, value in raw["at"].items():
        if key not in valid_score_keys or type(value) is not int or not 1 <= value <= 99:
            raise ValueError("Invalid attempt history")
        attempts[key] = value
    first_pass = {}
    for key, value in raw["fp"].items():
        if key not in valid_score_keys or type(value) is not bool:
            raise ValueError("Invalid first-pass history")
        first_pass[key] = value

    if stage == 0 and any((claims, credits, aging, valuation, reporting, management)):
        raise ValueError("Briefing cannot contain activity answers")
    if stage < 2 and credits:
        raise ValueError("Credit decisions appear too early")
    if stage < 3 and (aging or aging_submitted):
        raise ValueError("Aging work appears too early")
    if stage < 4 and (valuation or method or valuation_submitted):
        raise ValueError("Valuation work appears too early")
    if stage < 5 and reporting:
        raise ValueError("Reporting decisions appear too early")
    if stage < 6 and management:
        raise ValueError("Management decisions appear too early")

    if stage >= 2 and not _all_correct(claims, CLAIM_DECISIONS):
        raise ValueError("Claims stage is incomplete")
    if stage >= 3 and not _all_correct(credits, CREDIT_DECISIONS):
        raise ValueError("Credit stage is incomplete")
    if stage >= 4:
        if not aging_submitted or any(aging.get(invoice.id) != invoice.correct_bucket for invoice in INVOICES):
            raise ValueError("Aging stage is unresolved")
    if stage >= 5:
        valuation_result = evaluate_valuation(valuation, method)
        if not valuation_submitted or not valuation_result["correct"]:
            raise ValueError("Valuation stage is unresolved")
    if stage >= 6 and not _all_correct(reporting, REPORTING_DECISIONS):
        raise ValueError("Reporting stage is incomplete")
    if stage >= 7 and not _all_correct(management, MANAGEMENT_DECISIONS):
        raise ValueError("Management stage is incomplete")

    for item in CLAIM_DECISIONS[:claim_index]:
        if claims.get(item.id) != item.correct:
            raise ValueError("A prior claim answer is unresolved")
    for item in CREDIT_DECISIONS[:credit_index]:
        if credits.get(item.id) != item.correct:
            raise ValueError("A prior credit answer is unresolved")
    for item in REPORTING_DECISIONS[:reporting_index]:
        if reporting.get(item.id) != item.correct:
            raise ValueError("A prior reporting answer is unresolved")
    for item in MANAGEMENT_DECISIONS[:management_index]:
        if management.get(item.id) != item.correct:
            raise ValueError("A prior management answer is unresolved")

    if stage == 1 and len(claims) not in {claim_index, claim_index + 1}:
        raise ValueError("Claim position is inconsistent")
    if stage >= 2 and claim_index != len(CLAIM_DECISIONS) - 1:
        raise ValueError("Completed claim position is invalid")
    if stage == 2 and len(credits) not in {credit_index, credit_index + 1}:
        raise ValueError("Credit position is inconsistent")
    if stage >= 3 and credit_index != len(CREDIT_DECISIONS) - 1:
        raise ValueError("Completed credit position is invalid")
    if stage == 5 and len(reporting) not in {reporting_index, reporting_index + 1}:
        raise ValueError("Reporting position is inconsistent")
    if stage >= 6 and reporting_index != len(REPORTING_DECISIONS) - 1:
        raise ValueError("Completed reporting position is invalid")
    if stage == 6 and len(management) not in {management_index, management_index + 1}:
        raise ValueError("Management position is inconsistent")
    if stage >= 7 and management_index != len(MANAGEMENT_DECISIONS) - 1:
        raise ValueError("Completed management position is invalid")

    return {
        "rc_stage": stage,
        "rc_claim_index": claim_index,
        "rc_claim_responses": claims,
        "rc_credit_index": credit_index,
        "rc_credit_responses": credits,
        "rc_aging_responses": aging,
        "rc_aging_submitted": aging_submitted,
        "rc_valuation_responses": valuation,
        "rc_valuation_method": method,
        "rc_valuation_submitted": valuation_submitted,
        "rc_reporting_index": reporting_index,
        "rc_reporting_responses": reporting,
        "rc_management_index": management_index,
        "rc_management_responses": management,
        "rc_attempts": attempts,
        "rc_first_pass": first_pass,
    }


def snapshot_from_state(state: MutableMapping[str, Any]) -> dict[str, Any]:
    return {
        "v": SNAPSHOT_VERSION,
        "s": state["rc_stage"],
        "ci": state["rc_claim_index"],
        "cr": state["rc_claim_responses"],
        "di": state["rc_credit_index"],
        "dr": state["rc_credit_responses"],
        "ar": state["rc_aging_responses"],
        "as": state["rc_aging_submitted"],
        "vr": state["rc_valuation_responses"],
        "vm": state["rc_valuation_method"],
        "vs": state["rc_valuation_submitted"],
        "ri": state["rc_reporting_index"],
        "rr": state["rc_reporting_responses"],
        "mi": state["rc_management_index"],
        "mr": state["rc_management_responses"],
        "at": state["rc_attempts"],
        "fp": state["rc_first_pass"],
    }


def encode_state(state: MutableMapping[str, Any]) -> str:
    return _encode(snapshot_from_state(state))


def decode_snapshot(token: object) -> dict[str, Any] | None:
    if not isinstance(token, str) or not token or len(token) > MAX_TOKEN_LENGTH:
        return None
    try:
        return validate_snapshot(_decode(token))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, zlib.error):
        return None


def restore_session_state(state: MutableMapping[str, Any], token: object) -> bool:
    restored = decode_snapshot(token)
    if restored is None:
        return False
    state.update(restored)
    return True


def sync_progress_query(state: MutableMapping[str, Any], query_params: MutableMapping[str, Any]) -> None:
    token = encode_state(state)
    current = query_params.get(SNAPSHOT_PARAM)
    if isinstance(current, list):
        current = current[0] if current else None
    if current != token:
        query_params[SNAPSHOT_PARAM] = token


def reset_saved_progress(state: MutableMapping[str, Any], query_params: MutableMapping[str, Any]) -> None:
    for key in list(state):
        if key.startswith("rc_") or key.startswith("widget_"):
            del state[key]
    state.update(activity_defaults())
    query_params[SNAPSHOT_PARAM] = encode_state(state)


def record_attempt(state: MutableMapping[str, Any], score_key: str, correct: bool) -> None:
    attempts = dict(state["rc_attempts"])
    first_pass = dict(state["rc_first_pass"])
    attempts[score_key] = attempts.get(score_key, 0) + 1
    if score_key not in first_pass:
        first_pass[score_key] = bool(correct)
    state["rc_attempts"] = attempts
    state["rc_first_pass"] = first_pass


def score_summary(state: MutableMapping[str, Any]) -> dict[str, int]:
    first_pass = state.get("rc_first_pass", {})
    total = len(_valid_score_keys())
    attempted = len(first_pass)
    correct = sum(1 for value in first_pass.values() if value)
    revisions = sum(max(0, value - 1) for value in state.get("rc_attempts", {}).values())
    return {
        "correct": correct,
        "attempted": attempted,
        "total": total,
        "revisions": revisions,
    }
