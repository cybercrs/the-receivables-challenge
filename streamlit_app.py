"""Student-facing Streamlit application for The Receivables Challenge."""

from __future__ import annotations

import hashlib
import random
from html import escape

import streamlit as st

from receivables_challenge.case_data import (
    AGING_DECISIONS,
    BEGINNING_ALLOWANCE,
    CLAIM_DECISIONS,
    COMPANY_NAME,
    CREDIT_DECISIONS,
    MANAGEMENT_DECISIONS,
    PERCENTAGE_OF_RECEIVABLES_RATE,
    REPORTING_DATE,
    REPORTING_DECISIONS,
    VALUATION_BENEFIT_OPTIONS,
    VALUATION_FIELDS,
)
from receivables_challenge.engine import (
    aging_allowance_rows,
    dashboard_metrics,
    evaluate_decision,
    evaluate_valuation,
    format_currency,
    gross_accounts_receivable,
    percentage_of_receivables_estimate,
    valuation_values,
    writeoff_comparison,
)
from receivables_challenge.progress import (
    SNAPSHOT_PARAM,
    activity_defaults,
    record_attempt,
    reset_saved_progress,
    restore_session_state,
    score_summary,
    sync_progress_query,
)


st.set_page_config(
    page_title="The Receivables Challenge",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


UD_RED = "#CE0037"
UD_BLUE = "#003087"
INK = "#14213D"
MUTED = "#59677A"
SURFACE = "#FFFFFF"
BACKGROUND = "#F4F7FB"
SUCCESS = "#137A4B"
WARNING = "#986000"
GOLD = "#F3B61F"


APP_CSS = f"""
<style>
    :root {{
        --ud-red: {UD_RED};
        --ud-blue: {UD_BLUE};
        --ink: {INK};
        --muted: {MUTED};
        --surface: {SURFACE};
        --background: {BACKGROUND};
        --success: {SUCCESS};
        --warning: {WARNING};
        --gold: {GOLD};
    }}

    .stApp {{ background: var(--background); }}
    [data-testid="stHeaderActionElements"] {{ display: none; }}
    [data-testid="stToolbar"] {{ visibility: hidden; height: 0; }}
    [data-testid="stDecoration"] {{ background: var(--ud-red); }}
    .block-container {{ max-width: 1180px; padding-top: 1.35rem; padding-bottom: 4rem; }}

    h1, h2, h3 {{ color: var(--ink); letter-spacing: -0.02em; }}
    p, li, label {{ color: var(--ink); }}

    .hero {{
        background:
            radial-gradient(circle at 91% 8%, rgba(243, 182, 31, 0.30), transparent 25%),
            linear-gradient(125deg, #001F55 0%, var(--ud-blue) 60%, #164E91 100%);
        border-top: 7px solid var(--ud-red);
        border-radius: 18px;
        box-shadow: 0 16px 38px rgba(0, 48, 135, 0.17);
        margin-bottom: 1rem;
        padding: 2rem 2.2rem 1.8rem;
    }}
    .hero-kicker {{ color: #FFFFFF; font-size: 0.8rem; font-weight: 850; letter-spacing: 0.13em; }}
    .hero h1 {{ color: #FFFFFF; font-size: clamp(2.15rem, 5vw, 3.7rem); margin: 0.15rem 0 0; }}
    .hero p {{ color: #F1F5FF; font-size: 1.08rem; margin: 0.65rem 0 0; max-width: 840px; }}
    .hero strong {{ color: var(--gold); }}

    .stage-row {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 0.38rem; margin: 0 0 1.3rem; }}
    .stage-pill {{
        background: #E6EAF1; border: 1px solid #D3D9E4; border-radius: 999px;
        color: #5C6879; font-size: 0.71rem; font-weight: 760; padding: 0.46rem 0.42rem; text-align: center;
    }}
    .stage-pill.complete {{ background: #E5F3EB; border-color: #A5D2B9; color: #0A653D; }}
    .stage-pill.active {{ background: var(--ud-red); border-color: var(--ud-red); color: #FFFFFF; }}

    .eyebrow {{ color: var(--ud-red); font-size: 0.78rem; font-weight: 850; letter-spacing: 0.1em; text-transform: uppercase; }}
    .lead {{ color: var(--muted); font-size: 1.07rem; max-width: 900px; }}
    .card {{
        background: var(--surface); border: 1px solid #D9E0EA; border-left: 7px solid var(--ud-blue);
        border-radius: 14px; box-shadow: 0 8px 22px rgba(20, 33, 61, 0.06);
        margin: 0.75rem 0 1rem; padding: 1.15rem 1.3rem;
    }}
    .card .document {{ color: var(--ud-blue); font-size: 0.78rem; font-weight: 850; letter-spacing: 0.06em; text-transform: uppercase; }}
    .card h3 {{ margin: 0.28rem 0 0.48rem; }}
    .card p {{ font-size: 1.04rem; margin: 0; }}

    .concept-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.72rem; margin: 1rem 0 1.3rem; }}
    .concept-card {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 13px; padding: 1rem; }}
    .concept-card strong {{ color: var(--ud-blue); display: block; margin: 0.2rem 0; }}
    .concept-number {{ color: var(--ud-red); font-size: 1.15rem; font-weight: 900; }}
    .concept-card span {{ color: var(--muted); font-size: 0.9rem; }}

    .metric-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.65rem; margin: 0.9rem 0 1.1rem; }}
    .metric-box {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 12px; padding: 0.85rem; text-align: center; }}
    .metric-box strong {{ color: var(--ud-blue); display: block; font-size: 1.42rem; }}
    .metric-box span {{ color: var(--muted); font-size: 0.8rem; }}

    .feedback-row {{
        align-items: flex-start; background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 10px;
        display: flex; gap: 1rem; justify-content: space-between; margin: 0.42rem 0; padding: 0.7rem 0.82rem;
    }}
    .feedback-row.correct {{ border-left: 5px solid var(--success); }}
    .feedback-row.review {{ border-left: 5px solid var(--warning); }}
    .feedback-label {{ font-weight: 780; }}
    .feedback-detail {{ color: var(--muted); font-size: 0.9rem; margin-top: 0.12rem; }}
    .feedback-value {{ font-variant-numeric: tabular-nums; text-align: right; }}

    .effect-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.65rem; margin: 0.7rem 0; }}
    .effect-box {{ background: #EEF4FF; border: 1px solid #C6D7F2; border-radius: 11px; padding: 0.82rem 0.95rem; }}
    .effect-box span {{ color: var(--muted); display: block; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; }}
    .effect-box strong {{ color: var(--ud-blue); display: block; font-size: 0.95rem; margin-top: 0.25rem; }}

    .formula {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 12px; margin: 0.7rem 0 1rem; padding: 0.95rem 1.1rem; }}
    .formula strong {{ color: var(--ud-blue); }}
    .principle {{ background: #FFF5F7; border-left: 5px solid var(--ud-red); border-radius: 9px; margin: 0.7rem 0; padding: 0.82rem 0.95rem; }}
    .principle strong {{ color: var(--ud-red); }}

    .stButton > button, .stFormSubmitButton > button {{ border-radius: 9px; font-weight: 760; min-height: 2.7rem; }}
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{ background: var(--ud-red); border-color: var(--ud-red); color: #FFFFFF; }}
    .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {{ background: #A9002E; border-color: #A9002E; color: #FFFFFF; }}
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primaryFormSubmit"] {{ background: var(--ud-red); border-color: var(--ud-red); color: #FFFFFF; }}
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primaryFormSubmit"] p {{ color: #FFFFFF !important; }}

    @media (max-width: 820px) {{
        .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
        .hero {{ padding: 1.4rem 1.2rem; }}
        .stage-row {{ grid-template-columns: 1fr; }}
        .stage-pill {{ display: none; }}
        .stage-pill.active {{ display: block; }}
        .concept-grid, .metric-grid, .effect-grid {{ grid-template-columns: 1fr; }}
        .feedback-row {{ display: block; }}
        .feedback-value {{ margin-top: 0.3rem; text-align: left; }}
    }}
</style>
"""


STAGE_LABELS = ("Brief", "1. Claims", "2. Credit", "3. Aging", "4. Value", "5. Report", "6. Manage", "Complete")


def initialize_state() -> None:
    if "rc_restore_attempted" not in st.session_state:
        restored = restore_session_state(st.session_state, st.query_params.get(SNAPSHOT_PARAM))
        st.session_state.rc_restore_attempted = True
        if restored:
            st.session_state.rc_scroll_to_top = True
    for key, value in activity_defaults().items():
        if key not in st.session_state:
            st.session_state[key] = value


def restart_activity() -> None:
    reset_saved_progress(st.session_state, st.query_params)
    st.session_state.rc_scroll_to_top = True


def set_stage(stage: int) -> None:
    st.session_state.rc_stage = stage
    st.session_state.rc_scroll_to_top = True


def advance_item(index_key: str, count: int, next_stage: int) -> None:
    index = int(st.session_state[index_key])
    if index >= count - 1:
        set_stage(next_stage)
    else:
        st.session_state[index_key] = index + 1
        st.session_state.rc_scroll_to_top = True


def selected_index(options: tuple | list, selected: str | None) -> int | None:
    return list(options).index(selected) if selected in options else None


def shuffled(items: tuple | list, salt: str) -> list:
    """Return a stable per-student order that survives reruns and refreshes."""

    digest = hashlib.sha256(f"{st.session_state.rc_shuffle_seed}:{salt}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    ordered = list(items)
    rng.shuffle(ordered)
    if len(ordered) > 1 and ordered == list(items):
        ordered = ordered[1:] + ordered[:1]
    return ordered


def save_simple_draft(group: str, item_id: str, widget_key: str) -> None:
    drafts = {key: dict(value) for key, value in st.session_state.rc_drafts.items()}
    group_answers = dict(drafts[group])
    value = st.session_state.get(widget_key)
    if value is None:
        group_answers.pop(item_id, None)
    else:
        group_answers[item_id] = str(value)
    drafts[group] = group_answers
    st.session_state.rc_drafts = drafts


def save_valuation_draft(answer_key: str, widget_key: str) -> None:
    drafts = {key: dict(value) for key, value in st.session_state.rc_drafts.items()}
    valuation = dict(drafts["valuation"])
    value = st.session_state.get(widget_key)
    if answer_key == "benefit":
        if value is None:
            valuation.pop(answer_key, None)
        else:
            valuation[answer_key] = str(value)
    else:
        valuation[answer_key] = int(value or 0)
    drafts["valuation"] = valuation
    st.session_state.rc_drafts = drafts


def escape_dollar_markdown(value: object) -> str:
    """Keep dollar signs in student-facing Markdown from starting inline math."""

    return str(value).replace("$", r"\$")


def render_scroll_reset() -> None:
    """Reset after navigation without overriding student-initiated scrolling."""

    if not st.session_state.pop("rc_scroll_to_top", False):
        return
    st.iframe(
        """
        <script>
        (() => {
          const parent = window.parent;
          const main = parent.document.querySelector('section[data-testid="stMain"]');
          if (!main) return;
          let cancelled = false;
          let finished = false;
          const scrollingKeys = new Set(['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' ']);
          const cancel = () => { cancelled = true; cleanup(); };
          const cancelKey = (event) => { if (scrollingKeys.has(event.key)) cancel(); };
          const cleanup = () => {
            parent.removeEventListener('wheel', cancel);
            parent.removeEventListener('touchstart', cancel);
            parent.removeEventListener('keydown', cancelKey);
          };
          const reset = () => {
            if (finished) return;
            finished = true;
            if (!cancelled) main.scrollTo({ top: 0, left: 0, behavior: 'auto' });
            cleanup();
          };
          parent.addEventListener('wheel', cancel, { passive: true });
          parent.addEventListener('touchstart', cancel, { passive: true });
          parent.addEventListener('keydown', cancelKey);
          parent.requestAnimationFrame(() => parent.requestAnimationFrame(reset));
          parent.setTimeout(reset, 120);
        })();
        </script>
        """,
        height=1,
        tab_index=-1,
    )


def store_simple_answer(map_key: str, item_id: str, selected: str, score_key: str, correct: bool) -> None:
    responses = dict(st.session_state[map_key])
    responses[item_id] = selected
    st.session_state[map_key] = responses
    record_attempt(st.session_state, score_key, correct)


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-kicker">RECEIVABLES DECISION CASE</div>
          <h1>The Receivables Challenge</h1>
          <p><strong>Sales are up, but cash is tight.</strong> Follow each claim from the original transaction to collection, estimation, reporting, and management action.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stage_row() -> None:
    current = int(st.session_state.rc_stage)
    pills = []
    for index, label in enumerate(STAGE_LABELS):
        status = "complete" if index < current else "active" if index == current else ""
        pills.append(f'<div class="stage-pill {status}">{escape(label)}</div>')
    st.markdown(f'<div class="stage-row">{"".join(pills)}</div>', unsafe_allow_html=True)


def render_card(document: str, title: str, story: str) -> None:
    st.markdown(
        f"""
        <div class="card">
          <div class="document">{escape(document)}</div>
          <h3>{escape(title)}</h3>
          <p>{escape(story)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feedback_row(label: str, correct: bool, detail: str, value: str = "") -> None:
    status = "correct" if correct else "review"
    symbol = "Correct" if correct else "Review"
    st.markdown(
        f"""
        <div class="feedback-row {status}">
          <div><div class="feedback-label">{escape(label)} - {symbol}</div><div class="feedback-detail">{escape(detail)}</div></div>
          <div class="feedback-value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_effects(account_effect: str, statement_effect: str) -> None:
    st.markdown(
        f"""
        <div class="effect-grid">
          <div class="effect-box"><span>Account change</span><strong>{escape(account_effect)}</strong></div>
          <div class="effect-box"><span>Financial statement effect</span><strong>{escape(statement_effect)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_briefing() -> None:
    st.markdown('<div class="eyebrow">Receivables command center</div>', unsafe_allow_html=True)
    st.header("Can strong sales still create a cash problem?")
    st.markdown(
        f'<p class="lead">You are the receivables team for {escape(COMPANY_NAME)}. Management needs a reliable {escape(REPORTING_DATE)} report and a plan that improves collection without driving away dependable customers.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="concept-grid">
          <div class="concept-card"><div class="concept-number">01</div><strong>Classify the claims</strong><span>Separate accounts, notes, and other receivables.</span></div>
          <div class="concept-card"><div class="concept-number">02</div><strong>Estimate collection</strong><span>Build an aging schedule and determine cash realizable value.</span></div>
          <div class="concept-card"><div class="concept-number">03</div><strong>Report faithfully</strong><span>Trace account changes, ending balances, and statement presentation.</span></div>
          <div class="concept-card"><div class="concept-number">04</div><strong>Manage for cash</strong><span>Use ratios, customer evidence, discounts, and factoring decisions.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="principle"><strong>Your reasoning tools:</strong> determine whether each account increases or decreases, calculate ending balances, and explain the financial-statement effect.</div>
        """,
        unsafe_allow_html=True,
    )
    st.button("Open the receivables file", type="primary", width="stretch", on_click=set_stage, args=(1,))


def render_sequential_stage(
    *,
    eyebrow: str,
    header: str,
    introduction: str,
    items,
    index_key: str,
    responses_key: str,
    score_prefix: str,
    next_stage: int,
    submit_label: str,
) -> None:
    index = int(st.session_state[index_key])
    item = items[index]
    st.markdown(f'<div class="eyebrow">{escape(eyebrow)}</div>', unsafe_allow_html=True)
    st.header(header)
    st.write(introduction)
    st.progress((index + 1) / len(items), text=f"Decision {index + 1} of {len(items)}")
    render_card(item.document, item.title, item.story)

    response = st.session_state[responses_key].get(item.id)
    result = evaluate_decision(item.id, response) if response is not None else None
    if result is None or not result["correct"]:
        if result is not None:
            st.warning(escape_dollar_markdown(f"Review this evidence. {result['explanation']}"))
            st.caption(escape_dollar_markdown(f"Best response: {result['expected']}"))
            render_effects(str(result["account_effect"]), str(result["statement_effect"]))
            st.info("Change your choice below, then check the revised response.")
        draft_group = {"claim": "claims", "credit": "credit", "aging": "aging"}[score_prefix]
        draft = st.session_state.rc_drafts[draft_group].get(item.id)
        options = shuffled(item.options, f"{score_prefix}-answer-order:{item.id}")
        widget_key = f"widget_{score_prefix}_{item.id}"
        selected = st.radio(
            escape_dollar_markdown(item.prompt),
            options,
            index=selected_index(options, draft),
            format_func=escape_dollar_markdown,
            key=widget_key,
            on_change=save_simple_draft,
            args=(draft_group, item.id, widget_key),
        )
        button_label = "Check revised response" if response is not None else submit_label
        if st.button(button_label, type="primary", width="stretch"):
            if selected is None:
                st.warning("Choose a response before checking your reasoning.")
            else:
                selected = str(selected)
                save_simple_draft(draft_group, item.id, widget_key)
                result = evaluate_decision(item.id, selected)
                store_simple_answer(
                    responses_key,
                    item.id,
                    selected,
                    f"{score_prefix}:{item.id}",
                    bool(result["correct"]),
                )
                st.rerun()
    else:
        st.success(escape_dollar_markdown(f"Correct. {result['explanation']}"))
        render_effects(str(result["account_effect"]), str(result["statement_effect"]))
        st.button(
            "Continue",
            type="primary",
            width="stretch",
            on_click=advance_item,
            args=(index_key, len(items), next_stage),
        )


def render_claims_stage() -> None:
    render_sequential_stage(
        eyebrow="Step 1 of the receivables chain",
        header="Identify the claim and its effects",
        introduction="Classify each amount, then connect it to the accounts and financial statements.",
        items=CLAIM_DECISIONS,
        index_key="rc_claim_index",
        responses_key="rc_claim_responses",
        score_prefix="claim",
        next_stage=2,
        submit_label="Check the claim",
    )


def render_credit_stage() -> None:
    render_sequential_stage(
        eyebrow="Step 2 of the receivables chain",
        header="Evaluate the tradeoffs in credit terms",
        introduction="Compare how payment windows and early-payment discounts can affect sales, cash timing, and collection risk.",
        items=CREDIT_DECISIONS,
        index_key="rc_credit_index",
        responses_key="rc_credit_responses",
        score_prefix="credit",
        next_stage=3,
        submit_label="Check the tradeoff",
    )


def completed_aging_schedule() -> list[dict[str, str]]:
    """Build the one student-facing schedule with four labeled cells."""

    display_rows = []
    for row in aging_allowance_rows():
        category = str(row["Age category"])
        receivables = format_currency(int(row["Receivables"]))
        rate = f"{float(row['Estimated loss rate']):.0%}"
        estimate = format_currency(int(row["Estimated uncollectible"]))
        if category == "Current":
            receivables = f"[1] {receivables}"
        if category == "61-90 days past due":
            rate = f"[2] {rate}"
        if category == "More than 90 days past due":
            estimate = f"[3] {estimate}"
        display_rows.append(
            {
                "Age category": category,
                "Receivables": receivables,
                "Estimated loss rate": rate,
                "Estimated uncollectible": estimate,
            }
        )
    display_rows.append(
        {
            "Age category": "Total",
            "Receivables": format_currency(gross_accounts_receivable()),
            "Estimated loss rate": "-",
            "Estimated uncollectible": f"[4] {format_currency(valuation_values()['ending_allowance'])}",
        }
    )
    return display_rows


def render_aging_stage() -> None:
    index = int(st.session_state.rc_aging_index)
    item = AGING_DECISIONS[index]
    st.markdown('<div class="eyebrow">Step 3 of the receivables chain</div>', unsafe_allow_html=True)
    st.header("Interpret a completed aging schedule")
    st.write("The schedule is complete. Use the four numbered cells to explain what the figures mean and how they support the allowance estimate.")
    st.dataframe(completed_aging_schedule(), width="stretch", hide_index=True)
    st.progress((index + 1) / len(AGING_DECISIONS), text=f"Aging interpretation {index + 1} of {len(AGING_DECISIONS)}")
    render_card(item.document, item.title, item.story)

    response = st.session_state.rc_aging_responses.get(item.id)
    result = evaluate_decision(item.id, response) if response is not None else None
    if result is None or not result["correct"]:
        if result is not None:
            st.warning(escape_dollar_markdown(f"Review this interpretation. {result['explanation']}"))
            st.caption(escape_dollar_markdown(f"Best response: {result['expected']}"))
            render_effects(str(result["account_effect"]), str(result["statement_effect"]))
            st.info("Change your choice below, then check the revised interpretation.")
        draft = st.session_state.rc_drafts["aging"].get(item.id)
        options = shuffled(item.options, f"aging-answer-order:{item.id}")
        widget_key = f"widget_aging_{item.id}"
        selected = st.radio(
            escape_dollar_markdown(item.prompt),
            options,
            index=selected_index(options, draft),
            format_func=escape_dollar_markdown,
            key=widget_key,
            on_change=save_simple_draft,
            args=("aging", item.id, widget_key),
        )
        button_label = "Check revised interpretation" if response is not None else "Check the interpretation"
        if st.button(button_label, type="primary", width="stretch"):
            if selected is None:
                st.warning("Choose a response before checking your reasoning.")
            else:
                selected = str(selected)
                save_simple_draft("aging", item.id, widget_key)
                checked = evaluate_decision(item.id, selected)
                store_simple_answer(
                    "rc_aging_responses",
                    item.id,
                    selected,
                    f"aging:{item.id}",
                    bool(checked["correct"]),
                )
                st.rerun()
    else:
        st.success(escape_dollar_markdown(f"Correct. {result['explanation']}"))
        render_effects(str(result["account_effect"]), str(result["statement_effect"]))
        st.button(
            "Continue",
            type="primary",
            width="stretch",
            on_click=advance_item,
            args=("rc_aging_index", len(AGING_DECISIONS), 4),
        )


def render_valuation_stage() -> None:
    st.markdown('<div class="eyebrow">Step 4 of the receivables chain</div>', unsafe_allow_html=True)
    st.header("Determine the balance-sheet net realizable value")
    st.write("Use the aging result to determine the required allowance, the related account increases, and the net realizable value reported after the bad debt adjustment.")

    display_rows = []
    for row in aging_allowance_rows():
        display_rows.append(
            {
                "Age category": row["Age category"],
                "Receivables": format_currency(int(row["Receivables"])),
                "Estimated loss rate": f"{float(row['Estimated loss rate']):.0%}",
                "Estimated uncollectible": format_currency(int(row["Estimated uncollectible"])),
            }
        )
    st.dataframe(display_rows, width="stretch", hide_index=True)
    st.markdown(
        f"""
        <div class="formula"><strong>Starting point:</strong> Gross Accounts Receivable is {format_currency(gross_accounts_receivable())}. The Allowance currently has an unadjusted balance of {format_currency(BEGINNING_ALLOWANCE)} before the aging estimate is applied.</div>
        """,
        unsafe_allow_html=True,
    )

    prior_submission = dict(st.session_state.rc_valuation_responses)
    prior_benefit = str(st.session_state.rc_valuation_benefit)
    result = evaluate_valuation(prior_submission, prior_benefit) if st.session_state.rc_valuation_submitted else None
    valuation_correct = bool(result) and bool(result["correct"])
    if result:
        labels = dict(VALUATION_FIELDS)
        for key, field_result in result["fields"].items():
            render_feedback_row(
                labels[key],
                bool(field_result["correct"]),
                f"Your answer: {format_currency(prior_submission[key])}. Use the aging estimate and the existing allowance balance.",
                f"Correct amount: {format_currency(int(field_result['expected']))}",
            )
        render_feedback_row(
            "Benefit of aging",
            bool(result["benefit"]["correct"]),
            f"Your answer: {prior_benefit}",
            f"Best response: {result['benefit']['expected']}",
        )
        if valuation_correct:
            expected = valuation_values()
            st.success("Valuation complete. The balance sheet will report receivables at the amount management expects to collect in cash after the bad debt adjustment.")
            st.markdown(
                f"""
                <div class="principle"><strong>Account and statement effects:</strong> Allowance for Doubtful Accounts increases {format_currency(expected['allowance_increase'])}. Bad Debt Expense increases by the same amount. Net Accounts Receivable and total assets decrease by that amount.</div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(
                escape_dollar_markdown(
                    f"Method comparison: the percentage-of-receivables estimate is "
                    f"{format_currency(gross_accounts_receivable())} x {PERCENTAGE_OF_RECEIVABLES_RATE:.0%} "
                    f"= {format_currency(percentage_of_receivables_estimate())}. The aging estimate is the sum of the "
                    f"age-group estimates, {format_currency(expected['ending_allowance'])}."
                )
            )
            st.button("Continue to reporting", type="primary", width="stretch", on_click=set_stage, args=(5,))
        else:
            st.warning("Some amounts or the conceptual response need revision. Follow the allowance from its current balance to its required ending balance, then determine balance-sheet net realizable value.")
            st.info("Change any amount or the conceptual response below, then check the revised valuation.")

    if not valuation_correct:
        draft = dict(st.session_state.rc_drafts["valuation"])
        responses = {}
        for key, label in VALUATION_FIELDS:
            widget_key = f"widget_valuation_{key}"
            responses[key] = int(
                st.number_input(
                    label,
                    min_value=0,
                    max_value=10_000_000,
                    value=int(draft.get(key, 0)),
                    step=100,
                    key=widget_key,
                    on_change=save_valuation_draft,
                    args=(key, widget_key),
                )
            )
        benefit_options = shuffled(VALUATION_BENEFIT_OPTIONS, "valuation-benefit-order")
        benefit = st.radio(
            "What is a key benefit of using an aging schedule to estimate uncollectible accounts?",
            benefit_options,
            index=selected_index(benefit_options, draft.get("benefit")),
            format_func=escape_dollar_markdown,
            key="widget_valuation_benefit",
            on_change=save_valuation_draft,
            args=("benefit", "widget_valuation_benefit"),
        )
        button_label = "Check revised valuation" if result else "Check the valuation"
        if st.button(button_label, type="primary", width="stretch"):
            if benefit is None:
                st.warning("Choose a response about aging before checking the valuation.")
            else:
                drafts = {key: dict(value) for key, value in st.session_state.rc_drafts.items()}
                drafts["valuation"] = {**responses, "benefit": str(benefit)}
                st.session_state.rc_drafts = drafts
                checked = evaluate_valuation(responses, str(benefit))
                for key, _label in VALUATION_FIELDS:
                    score_key = f"valuation:{key}"
                    if score_key not in st.session_state.rc_first_pass or prior_submission.get(key) != responses[key]:
                        record_attempt(st.session_state, score_key, bool(checked["fields"][key]["correct"]))
                if "valuation:benefit" not in st.session_state.rc_first_pass or prior_benefit != benefit:
                    record_attempt(st.session_state, "valuation:benefit", bool(checked["benefit"]["correct"]))
                st.session_state.rc_valuation_responses = responses
                st.session_state.rc_valuation_benefit = str(benefit)
                st.session_state.rc_valuation_submitted = True
                st.rerun()


def render_writeoff_visual() -> None:
    comparison = writeoff_comparison()
    st.subheader("Why cash realizable value does not change")
    before, after = st.columns(2)
    before.metric("Before write-off - gross receivables", format_currency(comparison["gross_before"]))
    before.metric("Before write-off - allowance", format_currency(comparison["allowance_before"]))
    before.metric("Before write-off - net receivables", format_currency(comparison["net_before"]))
    after.metric("After write-off - gross receivables", format_currency(comparison["gross_after"]), delta=format_currency(-14_000))
    after.metric("After write-off - allowance", format_currency(comparison["allowance_after"]), delta=format_currency(-14_000))
    after.metric("After write-off - net receivables", format_currency(comparison["net_after"]), delta="$0")


def render_reporting_stage() -> None:
    index = int(st.session_state.rc_reporting_index)
    item = REPORTING_DECISIONS[index]
    st.markdown('<div class="eyebrow">Step 5 of the receivables chain</div>', unsafe_allow_html=True)
    st.header("Write off and report the receivables")
    st.write("Trace the effect of a specific write-off, then choose the appropriate financial-statement presentation for each receivables-related item.")
    st.progress((index + 1) / len(REPORTING_DECISIONS), text=f"Reporting decision {index + 1} of {len(REPORTING_DECISIONS)}")
    render_card(item.document, item.title, item.story)
    response = st.session_state.rc_reporting_responses.get(item.id)
    result = evaluate_decision(item.id, response) if response is not None else None

    if result is None or not result["correct"]:
        if result is not None:
            st.warning(escape_dollar_markdown(f"Review the reporting purpose. {result['explanation']}"))
            st.caption(escape_dollar_markdown(f"Best response: {result['expected']}"))
            render_effects(str(result["account_effect"]), str(result["statement_effect"]))
            st.info("Change your choice below, then check the revised reporting decision.")
        draft = st.session_state.rc_drafts["reporting"].get(item.id)
        options = shuffled(item.options, f"reporting-answer-order:{item.id}")
        widget_key = f"widget_reporting_{item.id}"
        selected = st.radio(
            escape_dollar_markdown(item.prompt),
            options,
            index=selected_index(options, draft),
            format_func=escape_dollar_markdown,
            key=widget_key,
            on_change=save_simple_draft,
            args=("reporting", item.id, widget_key),
        )
        button_label = "Check revised reporting decision" if response is not None else "Check the reporting decision"
        if st.button(button_label, type="primary", width="stretch"):
            if selected is None:
                st.warning("Choose a response before checking your reasoning.")
            else:
                selected = str(selected)
                save_simple_draft("reporting", item.id, widget_key)
                result = evaluate_decision(item.id, selected)
                store_simple_answer(
                    "rc_reporting_responses",
                    item.id,
                    selected,
                    f"reporting:{item.id}",
                    bool(result["correct"]),
                )
                st.rerun()
    else:
        st.success(escape_dollar_markdown(f"Correct. {result['explanation']}"))
        if item.id == "writeoff_accounts":
            render_writeoff_visual()
        else:
            render_effects(str(result["account_effect"]), str(result["statement_effect"]))
        st.button(
            "Continue",
            type="primary",
            width="stretch",
            on_click=advance_item,
            args=("rc_reporting_index", len(REPORTING_DECISIONS), 6),
        )


def render_dashboard() -> None:
    metrics = dashboard_metrics()
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-box"><strong>{format_currency(metrics['gross_receivables'])}</strong><span>Gross receivables</span></div>
          <div class="metric-box"><strong>{format_currency(metrics['net_receivables'])}</strong><span>Net receivables</span></div>
          <div class="metric-box"><strong>{float(metrics['overdue_percent']):.0%}</strong><span>Past due</span></div>
          <div class="metric-box"><strong>{float(metrics['turnover']):.1f}x</strong><span>Receivables turnover</span></div>
          <div class="metric-box"><strong>{float(metrics['collection_period']):.1f} days</strong><span>Average collection period</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def category_score(prefix: str, count: int) -> str:
    first_pass = st.session_state.rc_first_pass
    correct = sum(1 for key, value in first_pass.items() if key.startswith(prefix) and value)
    return f"{correct}/{count}"


def render_completion() -> None:
    score = score_summary(st.session_state)
    st.success("Case complete. The receivables now tell one connected story from the original claim to collection and management action.")
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-box"><strong>{category_score('claim:', len(CLAIM_DECISIONS))}</strong><span>Claims first pass</span></div>
          <div class="metric-box"><strong>{category_score('credit:', len(CREDIT_DECISIONS))}</strong><span>Credit first pass</span></div>
          <div class="metric-box"><strong>{category_score('aging:', len(AGING_DECISIONS))}</strong><span>Aging first pass</span></div>
          <div class="metric-box"><strong>{category_score('reporting:', len(REPORTING_DECISIONS))}</strong><span>Reporting first pass</span></div>
          <div class="metric-box"><strong>{category_score('management:', len(MANAGEMENT_DECISIONS))}</strong><span>Management first pass</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    valuation_count = len(VALUATION_FIELDS) + 1
    st.caption(
        f"Valuation first pass: {category_score('valuation:', valuation_count)} | "
        f"All first-pass decisions: {score['correct']} of {score['total']} | "
        f"Practice revisions used: {score['revisions']} | Final mastery: complete"
    )
    st.subheader("The complete receivables chain")
    st.markdown(
        """
        1. Identify the type of claim and when it arises.
        2. Evaluate how credit terms affect sales, cash timing, and collection risk.
        3. Interpret the amounts, loss rates, and totals in a completed aging schedule.
        4. Estimate the allowance and determine balance-sheet net realizable value after the bad debt adjustment.
        5. Apply authorized write-offs without changing the already estimated net receivables.
        6. Present receivables, bad debt expense, interest revenue, and collection risk clearly.
        7. Use turnover, collection period, customer analytics, discounts, and factoring to improve cash flow.
        """
    )
    st.subheader("Discuss with your team")
    comparison_question = escape_dollar_markdown(
        f"Why did aging produce a {format_currency(valuation_values()['ending_allowance'])} allowance estimate, "
        f"compared with {format_currency(percentage_of_receivables_estimate())} using "
        f"{PERCENTAGE_OF_RECEIVABLES_RATE:.0%} of {format_currency(gross_accounts_receivable())} gross receivables?"
    )
    with st.expander(comparison_question):
        st.write(
            "The aging calculation applies different estimated loss rates to each age group, including higher rates for older balances. "
            "The simple percentage calculation applies the same 8% rate to the entire gross receivables balance, so it does not reflect "
            "the concentration of receivables in higher-risk age groups."
        )
    with st.expander("Why did the specific write-off not change net Accounts Receivable?"):
        st.write(
            "Gross Accounts Receivable and the Allowance for Doubtful Accounts decreased by the same amount. "
            "Because both sides of the net calculation fell equally, net Accounts Receivable stayed the same."
        )
    with st.expander("Which management action would improve cash fastest, and what would it cost?"):
        st.write(
            "Selling selected receivables to a factor would produce cash immediately. The company would incur a factoring cost, "
            "so the cash received and income would be lower than if customers paid the full balances."
        )
    with st.expander("Why would denying credit to every customer be a poor solution even if it eliminated collection risk?"):
        st.write(
            "It could prevent profitable credit sales and push dependable customers toward competitors. A balanced policy can support sales "
            "while using screening, monitoring, and collection follow-up to manage risk."
        )


def render_management_stage() -> None:
    index = int(st.session_state.rc_management_index)
    item = MANAGEMENT_DECISIONS[index]
    st.markdown('<div class="eyebrow">Step 6 of the receivables chain</div>', unsafe_allow_html=True)
    st.header("Manage receivables for cash and sustainable sales")
    st.write("Use the dashboard to evaluate liquidity, target collection work, and recommend a balanced policy.")
    render_dashboard()
    st.progress((index + 1) / len(MANAGEMENT_DECISIONS), text=f"Management decision {index + 1} of {len(MANAGEMENT_DECISIONS)}")
    render_card(item.document, item.title, item.story)
    response = st.session_state.rc_management_responses.get(item.id)
    result = evaluate_decision(item.id, response) if response is not None else None

    if result is None or not result["correct"]:
        if result is not None:
            st.warning(escape_dollar_markdown(f"Review the evidence and tradeoff. {result['explanation']}"))
            st.caption(escape_dollar_markdown(f"Best response: {result['expected']}"))
            render_effects(str(result["account_effect"]), str(result["statement_effect"]))
            st.info("Change your choice below, then check the revised management decision.")
        draft = st.session_state.rc_drafts["management"].get(item.id)
        options = shuffled(item.options, f"management-answer-order:{item.id}")
        widget_key = f"widget_management_{item.id}"
        selected = st.radio(
            escape_dollar_markdown(item.prompt),
            options,
            index=selected_index(options, draft),
            format_func=escape_dollar_markdown,
            key=widget_key,
            on_change=save_simple_draft,
            args=("management", item.id, widget_key),
        )
        button_label = "Check revised management decision" if response is not None else "Check the management decision"
        if st.button(button_label, type="primary", width="stretch"):
            if selected is None:
                st.warning("Choose a response before checking your reasoning.")
            else:
                selected = str(selected)
                save_simple_draft("management", item.id, widget_key)
                result = evaluate_decision(item.id, selected)
                store_simple_answer(
                    "rc_management_responses",
                    item.id,
                    selected,
                    f"management:{item.id}",
                    bool(result["correct"]),
                )
                st.rerun()
    else:
        st.success(escape_dollar_markdown(f"Sound decision. {result['explanation']}"))
        render_effects(str(result["account_effect"]), str(result["statement_effect"]))
        label = "Finish the case" if index == len(MANAGEMENT_DECISIONS) - 1 else "Continue"
        st.button(
            label,
            type="primary",
            width="stretch",
            on_click=advance_item,
            args=("rc_management_index", len(MANAGEMENT_DECISIONS), 7),
        )


initialize_state()
st.markdown(APP_CSS, unsafe_allow_html=True)
render_hero()
top_left, top_right = st.columns([5, 1])
with top_right:
    st.button("Start over", width="stretch", on_click=restart_activity)
render_stage_row()

stage = int(st.session_state.rc_stage)
if stage == 0:
    render_briefing()
elif stage == 1:
    render_claims_stage()
elif stage == 2:
    render_credit_stage()
elif stage == 3:
    render_aging_stage()
elif stage == 4:
    render_valuation_stage()
elif stage == 5:
    render_reporting_stage()
elif stage == 6:
    render_management_stage()
else:
    render_completion()

sync_progress_query(st.session_state, st.query_params)
render_scroll_reset()
