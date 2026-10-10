"""App-specific reached pages; review never changes the canonical snapshot."""

from receivables_challenge.case_data import (
    AGING_DECISIONS,
    CLAIM_DECISIONS,
    CREDIT_DECISIONS,
    MANAGEMENT_DECISIONS,
    REPORTING_DECISIONS,
)
from receivables_challenge import engine

VIEW_KEY = "rc_browser_view"
VIEW_PARAM = "view"
STAGE_KEY = "rc_stage"
SCROLL_KEY = "rc_scroll_to_top"
RENDERERS = (
    "render_briefing",
    "render_claims_stage",
    "render_credit_stage",
    "render_aging_stage",
    "render_valuation_stage",
    "render_reporting_stage",
    "render_management_stage",
    "render_completion",
)
GROUPS = {
    1: (CLAIM_DECISIONS, "rc_claim_index", "rc_claim_responses"),
    2: (CREDIT_DECISIONS, "rc_credit_index", "rc_credit_responses"),
    3: (AGING_DECISIONS, "rc_aging_index", "rc_aging_responses"),
    5: (REPORTING_DECISIONS, "rc_reporting_index", "rc_reporting_responses"),
    6: (MANAGEMENT_DECISIONS, "rc_management_index", "rc_management_responses"),
}
POSITIONS = [(0, None, 0)]
for stage in range(1, len(RENDERERS) - 1):
    group = GROUPS.get(stage)
    POSITIONS.extend(
        (stage, group[1] if group else None, index)
        for index in range(len(group[0]) if group else 1)
    )
POSITIONS.append((len(RENDERERS) - 1, None, 0))


def frontier(state):
    stage = state[STAGE_KEY]
    key = GROUPS[stage][1] if stage in GROUPS else None
    return POSITIONS.index((stage, key, state[key] if key else 0))


def restore_view(state, raw):
    try:
        view = int(raw) if isinstance(raw, str) else -1
    except ValueError:
        view = -1
    state[VIEW_KEY] = view if 0 <= view <= frontier(state) else frontier(state)


def move(state, direction):
    if direction not in (-1, 1):
        raise ValueError("Direction must be Back or Forward")
    target = state[VIEW_KEY] + direction
    if not 0 <= target <= frontier(state):
        return False
    state[VIEW_KEY] = target
    state[SCROLL_KEY] = True
    return True


def can_advance(state):
    if state[VIEW_KEY] != frontier(state):
        return False
    stage = state[STAGE_KEY]
    if stage == 0:
        return True
    if stage == 4:
        return (
            state["rc_valuation_submitted"]
            and engine.evaluate_valuation(
                state["rc_valuation_responses"], state["rc_valuation_benefit"]
            )["correct"]
        )
    if stage not in GROUPS:
        return False
    items, key, responses = GROUPS[stage]
    item = items[state[key]]
    return state[responses].get(item.id) == item.correct


def advance(state):
    if not can_advance(state):
        return False
    target = state[VIEW_KEY] + 1
    stage, key, index = POSITIONS[target]
    state[STAGE_KEY] = stage
    if key:
        state[key] = index
    state[VIEW_KEY] = target
    state[SCROLL_KEY] = True
    return True
