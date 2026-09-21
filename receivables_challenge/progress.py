"""Compact, validated, non-identifying progress snapshots."""

from __future__ import annotations

import base64
import json
import secrets
import zlib
from collections.abc import MutableMapping
from typing import Any

from receivables_challenge.case_data import (
    AGING_DECISIONS,
    CLAIM_DECISIONS,
    CREDIT_DECISIONS,
    MANAGEMENT_DECISIONS,
    REPORTING_DECISIONS,
    VALUATION_BENEFIT_OPTIONS,
    VALUATION_FIELDS,
)
from receivables_challenge.engine import evaluate_valuation


SNAPSHOT_PARAM = "progress"
SNAPSHOT_VERSION = 3
MAX_TOKEN_LENGTH = 16_000
MAX_JSON_BYTES = 32_000


def activity_defaults() -> dict[str, Any]:
    return {
        "rc_stage": 0,
        "rc_shuffle_seed": secrets.randbits(63),
        "rc_drafts": {
            "claims": {},
            "credit": {},
            "aging": {},
            "valuation": {},
            "reporting": {},
            "management": {},
        },
        "rc_claim_index": 0,
        "rc_claim_responses": {},
        "rc_credit_index": 0,
        "rc_credit_responses": {},
        "rc_aging_index": 0,
        "rc_aging_responses": {},
        "rc_valuation_responses": {},
        "rc_valuation_benefit": "",
        "rc_valuation_submitted": False,
        "rc_reporting_index": 0,
        "rc_reporting_responses": {},
        "rc_management_index": 0,
        "rc_management_responses": {},
        "rc_attempts": {},
        "rc_first_pass": {},
        "rc_scroll_to_top": False,
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


def _validate_simple_draft(raw: object, items, current_index: int) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError("Draft answers must be an object")
    ids = [item.id for item in items]
    allowed_ids = set(ids[: current_index + 1])
    if set(raw) - allowed_ids:
        raise ValueError("Draft answers are out of sequence")
    normalized = {}
    for item in items:
        if item.id not in raw:
            continue
        value = raw[item.id]
        if not isinstance(value, str) or value not in item.options:
            raise ValueError("Invalid draft answer")
        normalized[item.id] = value
    return normalized


def _validate_valuation_draft(raw: object) -> dict[str, int | str]:
    if not isinstance(raw, dict):
        raise ValueError("Valuation draft must be an object")
    field_keys = {key for key, _label in VALUATION_FIELDS}
    if set(raw) - (field_keys | {"benefit"}):
        raise ValueError("Unknown valuation draft field")
    normalized: dict[str, int | str] = {}
    for key, value in raw.items():
        if key == "benefit":
            if not isinstance(value, str) or value not in VALUATION_BENEFIT_OPTIONS:
                raise ValueError("Invalid valuation benefit draft")
            normalized[key] = value
        else:
            if type(value) is not int or not 0 <= value <= 10_000_000:
                raise ValueError("Invalid valuation amount draft")
            normalized[key] = value
    return normalized


def _valid_score_keys() -> set[str]:
    keys = {f"claim:{item.id}" for item in CLAIM_DECISIONS}
    keys |= {f"credit:{item.id}" for item in CREDIT_DECISIONS}
    keys |= {f"aging:{item.id}" for item in AGING_DECISIONS}
    keys |= {f"valuation:{key}" for key, _label in VALUATION_FIELDS}
    keys.add("valuation:benefit")
    keys |= {f"reporting:{item.id}" for item in REPORTING_DECISIONS}
    keys |= {f"management:{item.id}" for item in MANAGEMENT_DECISIONS}
    return keys


def _all_correct(responses: dict[str, str], items) -> bool:
    return len(responses) == len(items) and all(responses[item.id] == item.correct for item in items)


def validate_snapshot(raw: object) -> dict[str, Any]:
    expected_keys = {
        "v", "s", "z", "d", "ci", "cr", "di", "dr", "ai", "ar", "vr", "vb", "vs",
        "ri", "rr", "mi", "mr", "at", "fp",
    }
    if not isinstance(raw, dict) or set(raw) != expected_keys or raw["v"] != SNAPSHOT_VERSION:
        raise ValueError("Unsupported snapshot")

    stage = raw["s"]
    if type(stage) is not int or not 0 <= stage <= 7:
        raise ValueError("Invalid stage")
    shuffle_seed = raw["z"]
    if type(shuffle_seed) is not int or not 0 <= shuffle_seed < 2**63:
        raise ValueError("Invalid shuffle seed")

    claim_index = _require_index(raw["ci"], len(CLAIM_DECISIONS))
    credit_index = _require_index(raw["di"], len(CREDIT_DECISIONS))
    aging_index = _require_index(raw["ai"], len(AGING_DECISIONS))
    reporting_index = _require_index(raw["ri"], len(REPORTING_DECISIONS))
    management_index = _require_index(raw["mi"], len(MANAGEMENT_DECISIONS))

    claims = _answer_prefix(raw["cr"], CLAIM_DECISIONS)
    credits = _answer_prefix(raw["dr"], CREDIT_DECISIONS)
    aging = _answer_prefix(raw["ar"], AGING_DECISIONS)
    reporting = _answer_prefix(raw["rr"], REPORTING_DECISIONS)
    management = _answer_prefix(raw["mr"], MANAGEMENT_DECISIONS)

    raw_drafts = raw["d"]
    if not isinstance(raw_drafts, dict) or set(raw_drafts) != {"c", "d", "a", "v", "r", "m"}:
        raise ValueError("Invalid draft groups")
    drafts = {
        "claims": _validate_simple_draft(raw_drafts["c"], CLAIM_DECISIONS, claim_index),
        "credit": _validate_simple_draft(raw_drafts["d"], CREDIT_DECISIONS, credit_index),
        "aging": _validate_simple_draft(raw_drafts["a"], AGING_DECISIONS, aging_index),
        "valuation": _validate_valuation_draft(raw_drafts["v"]),
        "reporting": _validate_simple_draft(raw_drafts["r"], REPORTING_DECISIONS, reporting_index),
        "management": _validate_simple_draft(raw_drafts["m"], MANAGEMENT_DECISIONS, management_index),
    }
    minimum_stages = {"claims": 1, "credit": 2, "aging": 3, "valuation": 4, "reporting": 5, "management": 6}
    for group, minimum_stage in minimum_stages.items():
        if stage < minimum_stage and drafts[group]:
            raise ValueError("Future draft is not allowed")

    valuation_submitted = raw["vs"]
    if type(valuation_submitted) is not bool:
        raise ValueError("Invalid submission status")
    valuation = _validate_valuation(raw["vr"], valuation_submitted)
    benefit = raw["vb"]
    if not isinstance(benefit, str) or benefit not in ("", *VALUATION_BENEFIT_OPTIONS):
        raise ValueError("Invalid valuation benefit")
    if valuation_submitted and benefit not in VALUATION_BENEFIT_OPTIONS:
        raise ValueError("Submitted valuation benefit is missing")

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
    if stage < 3 and aging:
        raise ValueError("Aging work appears too early")
    if stage < 4 and (valuation or benefit or valuation_submitted):
        raise ValueError("Valuation work appears too early")
    if stage < 5 and reporting:
        raise ValueError("Reporting decisions appear too early")
    if stage < 6 and management:
        raise ValueError("Management decisions appear too early")

    if stage >= 2 and not _all_correct(claims, CLAIM_DECISIONS):
        raise ValueError("Claims stage is incomplete")
    if stage >= 3 and not _all_correct(credits, CREDIT_DECISIONS):
        raise ValueError("Credit stage is incomplete")
    if stage >= 4 and not _all_correct(aging, AGING_DECISIONS):
        raise ValueError("Aging stage is unresolved")
    if stage >= 5:
        valuation_result = evaluate_valuation(valuation, benefit)
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
    for item in AGING_DECISIONS[:aging_index]:
        if aging.get(item.id) != item.correct:
            raise ValueError("A prior aging answer is unresolved")
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
    if stage == 3 and len(aging) not in {aging_index, aging_index + 1}:
        raise ValueError("Aging position is inconsistent")
    if stage >= 4 and aging_index != len(AGING_DECISIONS) - 1:
        raise ValueError("Completed aging position is invalid")
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
        "rc_shuffle_seed": shuffle_seed,
        "rc_drafts": drafts,
        "rc_claim_index": claim_index,
        "rc_claim_responses": claims,
        "rc_credit_index": credit_index,
        "rc_credit_responses": credits,
        "rc_aging_index": aging_index,
        "rc_aging_responses": aging,
        "rc_valuation_responses": valuation,
        "rc_valuation_benefit": benefit,
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
        "z": state["rc_shuffle_seed"],
        "d": {
            "c": state["rc_drafts"]["claims"],
            "d": state["rc_drafts"]["credit"],
            "a": state["rc_drafts"]["aging"],
            "v": state["rc_drafts"]["valuation"],
            "r": state["rc_drafts"]["reporting"],
            "m": state["rc_drafts"]["management"],
        },
        "ci": state["rc_claim_index"],
        "cr": state["rc_claim_responses"],
        "di": state["rc_credit_index"],
        "dr": state["rc_credit_responses"],
        "ai": state["rc_aging_index"],
        "ar": state["rc_aging_responses"],
        "vr": state["rc_valuation_responses"],
        "vb": state["rc_valuation_benefit"],
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
