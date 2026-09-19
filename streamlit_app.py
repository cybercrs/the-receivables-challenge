"""Student-facing Streamlit application for The Receivables Challenge."""

from __future__ import annotations

from html import escape

import altair as alt
import streamlit as st

from receivables_challenge.case_data import (
    AGING_BUCKETS,
    BEGINNING_ALLOWANCE,
    CLAIM_DECISIONS,
    COMPANY_NAME,
    CREDIT_DECISIONS,
    INVOICES,
    MANAGEMENT_DECISIONS,
    PERCENTAGE_OF_RECEIVABLES_RATE,
    REPORTING_DATE,
    REPORTING_DECISIONS,
    VALUATION_FIELDS,
)
from receivables_challenge.engine import (
    aging_allowance_rows,
    aging_totals,
    dashboard_metrics,
    evaluate_aging,
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


STAGE_LABELS = ("Briefing", "Claims", "Credit", "Aging", "Value", "Report", "Manage", "Debrief")


def initialize_state() -> None:
    if "rc_restore_attempted" not in st.session_state:
        restore_session_state(st.session_state, st.query_params.get(SNAPSHOT_PARAM))
        st.session_state.rc_restore_attempted = True
    for key, value in activity_defaults().items():
        if key not in st.session_state:
            st.session_state[key] = value


def restart_activity() -> None:
    reset_saved_progress(st.session_state, st.query_params)


def set_stage(stage: int) -> None:
    st.session_state.rc_stage = stage


def advance_item(index_key: str, count: int, next_stage: int) -> None:
    index = int(st.session_state[index_key])
    if index >= count - 1:
        set_stage(next_stage)
    else:
        st.session_state[index_key] = index + 1


def remove_response(map_key: str, item_id: str) -> None:
    responses = dict(st.session_state[map_key])
    responses.pop(item_id, None)
    st.session_state[map_key] = responses


def reopen_combined(submitted_key: str) -> None:
    st.session_state[submitted_key] = False


def store_simple_answer(map_key: str, item_id: str, selected: str, score_key: str, correct: bool) -> None:
    responses = dict(st.session_state[map_key])
    responses[item_id] = selected
    st.session_state[map_key] = responses
    record_attempt(st.session_state, score_key, correct)


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-kicker">CHAPTER 8 INTERACTIVE CASE</div>
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
        pills.append(f'<div class="stage-pill {status}">{index + 1}. {escape(label)}</div>')
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
        f'<p class="lead">You are the receivables team for {escape(COMPANY_NAME)}. Management needs a reliable June 30 report and a plan that improves collection without driving away dependable customers.</p>',
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
    if response is None:
        with st.form(f"decision_form_{score_prefix}_{item.id}"):
            selected = st.radio(
                item.prompt,
                item.options,
                index=None,
                key=f"widget_{score_prefix}_{item.id}",
            )
            submitted = st.form_submit_button(submit_label, type="primary", width="stretch")
        if submitted:
            if selected is None:
                st.warning("Choose a response before checking your reasoning.")
            else:
                result = evaluate_decision(item.id, selected)
                store_simple_answer(
                    responses_key,
                    item.id,
                    selected,
                    f"{score_prefix}:{item.id}",
                    bool(result["correct"]),
                )
                st.rerun()

    if response is not None:
        result = evaluate_decision(item.id, response)
        if result["correct"]:
            st.success(f"Correct. {result['explanation']}")
        else:
            st.warning(f"Review this evidence. {result['explanation']}")
            st.caption(f"Best response: {result['expected']}")
        render_effects(str(result["account_effect"]), str(result["statement_effect"]))
        if result["correct"]:
            st.button(
                "Continue",
                type="primary",
                width="stretch",
                on_click=advance_item,
                args=(index_key, len(items), next_stage),
            )
        else:
            st.button(
                "Revise my response",
                width="stretch",
                on_click=remove_response,
                args=(responses_key, item.id),
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
        header="Decide who receives credit",
        introduction="A policy that is too tight can lose sales. A policy that is too loose can create late payments and losses.",
        items=CREDIT_DECISIONS,
        index_key="rc_credit_index",
        responses_key="rc_credit_responses",
        score_prefix="credit",
        next_stage=3,
        submit_label="Evaluate the customer",
    )


def render_aging_chart() -> None:
    totals = aging_totals()
    chart_rows = [
        {"Age category": bucket, "Receivables": totals[bucket]}
        for bucket in AGING_BUCKETS
    ]
    chart = (
        alt.Chart(alt.Data(values=chart_rows))
        .mark_bar(color=UD_BLUE, cornerRadiusEnd=4)
        .encode(
            x=alt.X("Receivables:Q", title="Receivables", axis=alt.Axis(format="$,.0f")),
            y=alt.Y(
                "Age category:N",
                title=None,
                sort=list(AGING_BUCKETS),
                axis=alt.Axis(labelLimit=190),
            ),
            tooltip=[
                alt.Tooltip("Age category:N", title="Age category"),
                alt.Tooltip("Receivables:Q", title="Receivables", format="$,.0f"),
            ],
        )
        .properties(height=270)
    )
    st.altair_chart(chart, width="stretch")


def render_aging_stage() -> None:
    st.markdown('<div class="eyebrow">Step 3 of the receivables chain</div>', unsafe_allow_html=True)
    st.header("Build the aging schedule")
    st.write("Classify each open invoice by how long it has been unpaid. The same customer evidence will drive the allowance estimate and collection plan.")
    invoice_rows = [
        {
            "Customer": invoice.customer,
            "Balance": format_currency(invoice.balance),
            "Status at June 30": invoice.timing,
        }
        for invoice in INVOICES
    ]
    st.dataframe(invoice_rows, width="stretch", hide_index=True)

    if not st.session_state.rc_aging_submitted:
        prior = dict(st.session_state.rc_aging_responses)
        selections = {}
        options = ("Choose an age category", *AGING_BUCKETS)
        with st.form("aging_form"):
            for invoice in INVOICES:
                prior_value = prior.get(invoice.id, "Choose an age category")
                selections[invoice.id] = st.selectbox(
                    f"{invoice.customer} - {format_currency(invoice.balance)} - {invoice.timing}",
                    options,
                    index=options.index(prior_value),
                    key=f"widget_aging_{invoice.id}",
                )
            submitted = st.form_submit_button("Check the aging schedule", type="primary", width="stretch")
        if submitted:
            if any(value == "Choose an age category" for value in selections.values()):
                st.warning("Assign every invoice to an age category before checking the schedule.")
            else:
                previous = dict(st.session_state.rc_aging_responses)
                results = evaluate_aging(selections)
                for invoice in INVOICES:
                    key = f"aging:{invoice.id}"
                    if key not in st.session_state.rc_first_pass or previous.get(invoice.id) != selections[invoice.id]:
                        record_attempt(st.session_state, key, bool(results[invoice.id]["correct"]))
                st.session_state.rc_aging_responses = selections
                st.session_state.rc_aging_submitted = True
                st.rerun()

    if st.session_state.rc_aging_submitted:
        results = evaluate_aging(st.session_state.rc_aging_responses)
        all_correct = all(bool(result["correct"]) for result in results.values())
        for invoice in INVOICES:
            result = results[invoice.id]
            render_feedback_row(
                invoice.customer,
                bool(result["correct"]),
                "Use the invoice's status at June 30.",
                str(result["expected"]),
            )
        if all_correct:
            st.success("The aging schedule is complete. Older balances now receive visibly greater management attention.")
            render_aging_chart()
            st.button("Continue to valuation", type="primary", width="stretch", on_click=set_stage, args=(4,))
        else:
            st.warning("At least one invoice is in the wrong age category. Review the number of days past due.")
            st.button(
                "Revise the aging schedule",
                width="stretch",
                on_click=reopen_combined,
                args=("rc_aging_submitted",),
            )


def render_valuation_stage() -> None:
    st.markdown('<div class="eyebrow">Step 4 of the receivables chain</div>', unsafe_allow_html=True)
    st.header("Estimate what will be collected")
    st.write("Use the completed aging schedule to determine the required ending allowance, the account increases, and cash realizable value.")

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
        <div class="formula"><strong>Starting point:</strong> Gross Accounts Receivable is {format_currency(gross_accounts_receivable())}. The Allowance currently has an ending balance of {format_currency(BEGINNING_ALLOWANCE)} before this estimate is applied.</div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.rc_valuation_submitted:
        prior = dict(st.session_state.rc_valuation_responses)
        with st.form("valuation_form"):
            responses = {}
            for key, label in VALUATION_FIELDS:
                responses[key] = int(
                    st.number_input(
                        label,
                        min_value=0,
                        max_value=10_000_000,
                        value=int(prior.get(key, 0)),
                        step=100,
                        key=f"widget_valuation_{key}",
                    )
                )
            method = st.radio(
                "Which method responds most directly to the concentration of older invoices?",
                ("Percentage of receivables", "Aging analysis"),
                index=None,
                key="widget_valuation_method",
            )
            submitted = st.form_submit_button("Check the valuation", type="primary", width="stretch")
        if submitted:
            if method is None:
                st.warning("Choose an estimation method before checking the valuation.")
            else:
                previous = dict(st.session_state.rc_valuation_responses)
                result = evaluate_valuation(responses, method)
                for key, _label in VALUATION_FIELDS:
                    score_key = f"valuation:{key}"
                    if score_key not in st.session_state.rc_first_pass or previous.get(key) != responses[key]:
                        record_attempt(st.session_state, score_key, bool(result["fields"][key]["correct"]))
                if "valuation:method" not in st.session_state.rc_first_pass or st.session_state.rc_valuation_method != method:
                    record_attempt(st.session_state, "valuation:method", bool(result["method"]["correct"]))
                st.session_state.rc_valuation_responses = responses
                st.session_state.rc_valuation_method = method
                st.session_state.rc_valuation_submitted = True
                st.rerun()

    if st.session_state.rc_valuation_submitted:
        result = evaluate_valuation(st.session_state.rc_valuation_responses, st.session_state.rc_valuation_method)
        labels = dict(VALUATION_FIELDS)
        for key, field_result in result["fields"].items():
            render_feedback_row(
                labels[key],
                bool(field_result["correct"]),
                "Use the aging estimate and the existing allowance balance.",
                format_currency(int(field_result["expected"])),
            )
        render_feedback_row(
            "Method selection",
            bool(result["method"]["correct"]),
            "Older balances carry different expected loss rates.",
            str(result["method"]["expected"]),
        )
        if result["correct"]:
            expected = valuation_values()
            st.success("Valuation complete. The receivables are now stated at the amount management expects to collect in cash.")
            st.markdown(
                f"""
                <div class="principle"><strong>Account and statement effects:</strong> Allowance for Doubtful Accounts increases {format_currency(expected['allowance_increase'])}. Bad Debt Expense increases by the same amount. Net Accounts Receivable and total assets decrease by that amount.</div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(
                f"For comparison, an 8% percentage-of-receivables estimate would produce {format_currency(percentage_of_receivables_estimate())}, versus {format_currency(expected['ending_allowance'])} from the aging analysis."
            )
            st.button("Continue to reporting", type="primary", width="stretch", on_click=set_stage, args=(5,))
        else:
            st.warning("Some amounts or the method selection need revision. Follow the aging schedule from gross receivables to the required ending allowance.")
            st.button(
                "Revise the valuation",
                width="stretch",
                on_click=reopen_combined,
                args=("rc_valuation_submitted",),
            )


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
    st.write("Apply the allowance method, protect the write-off process, and place each amount where financial-statement users can understand it.")
    st.progress((index + 1) / len(REPORTING_DECISIONS), text=f"Reporting decision {index + 1} of {len(REPORTING_DECISIONS)}")
    render_card(item.document, item.title, item.story)
    response = st.session_state.rc_reporting_responses.get(item.id)

    if response is None:
        with st.form(f"reporting_form_{item.id}"):
            selected = st.radio(item.prompt, item.options, index=None, key=f"widget_reporting_{item.id}")
            submitted = st.form_submit_button("Check the reporting decision", type="primary", width="stretch")
        if submitted:
            if selected is None:
                st.warning("Choose a response before checking your reasoning.")
            else:
                result = evaluate_decision(item.id, selected)
                store_simple_answer(
                    "rc_reporting_responses",
                    item.id,
                    selected,
                    f"reporting:{item.id}",
                    bool(result["correct"]),
                )
                st.rerun()

    if response is not None:
        result = evaluate_decision(item.id, response)
        if result["correct"]:
            st.success(f"Correct. {result['explanation']}")
        else:
            st.warning(f"Review the reporting purpose. {result['explanation']}")
            st.caption(f"Best response: {result['expected']}")
        render_effects(str(result["account_effect"]), str(result["statement_effect"]))
        if result["correct"] and item.id == "writeoff_accounts":
            render_writeoff_visual()
        if result["correct"]:
            st.button(
                "Continue",
                type="primary",
                width="stretch",
                on_click=advance_item,
                args=("rc_reporting_index", len(REPORTING_DECISIONS), 6),
            )
        else:
            st.button(
                "Revise my reporting decision",
                width="stretch",
                on_click=remove_response,
                args=("rc_reporting_responses", item.id),
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
          <div class="metric-box"><strong>{category_score('aging:', len(INVOICES))}</strong><span>Aging first pass</span></div>
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
    st.subheader("The complete Chapter 8 chain")
    st.markdown(
        """
        1. Identify the type of claim and when it arises.
        2. Decide who should receive credit and under what conditions.
        3. Monitor unpaid invoices with an aging schedule.
        4. Estimate the allowance and calculate cash realizable value.
        5. Apply authorized write-offs without changing the already estimated net receivables.
        6. Present receivables, bad debt expense, interest revenue, and collection risk clearly.
        7. Use turnover, collection period, customer analytics, discounts, and factoring to improve cash flow.
        """
    )
    st.subheader("Debrief with your team")
    st.markdown(
        """
        - Why did the aging analysis produce a larger allowance than the simple percentage estimate?
        - Why did the specific write-off not change net Accounts Receivable?
        - Which management action would improve cash fastest, and what would it cost?
        - Why would denying credit to every customer be a poor solution even if it eliminated collection risk?
        """
    )
    st.button("Start over", width="stretch", on_click=restart_activity)


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

    if response is None:
        with st.form(f"management_form_{item.id}"):
            selected = st.radio(item.prompt, item.options, index=None, key=f"widget_management_{item.id}")
            submitted = st.form_submit_button("Check the management decision", type="primary", width="stretch")
        if submitted:
            if selected is None:
                st.warning("Choose a response before checking your reasoning.")
            else:
                result = evaluate_decision(item.id, selected)
                store_simple_answer(
                    "rc_management_responses",
                    item.id,
                    selected,
                    f"management:{item.id}",
                    bool(result["correct"]),
                )
                st.rerun()

    if response is not None:
        result = evaluate_decision(item.id, response)
        if result["correct"]:
            st.success(f"Sound decision. {result['explanation']}")
        else:
            st.warning(f"Review the evidence and tradeoff. {result['explanation']}")
            st.caption(f"Best response: {result['expected']}")
        render_effects(str(result["account_effect"]), str(result["statement_effect"]))
        if result["correct"]:
            label = "Finish the case" if index == len(MANAGEMENT_DECISIONS) - 1 else "Continue"
            st.button(
                label,
                type="primary",
                width="stretch",
                on_click=advance_item,
                args=("rc_management_index", len(MANAGEMENT_DECISIONS), 7),
            )
        else:
            st.button(
                "Revise my management decision",
                width="stretch",
                on_click=remove_response,
                args=("rc_management_responses", item.id),
            )


initialize_state()
st.markdown(APP_CSS, unsafe_allow_html=True)
render_hero()
render_stage_row()

with st.sidebar:
    st.header("The Receivables Challenge")
    st.write(f"Company: {COMPANY_NAME}")
    st.write(f"Reporting date: {REPORTING_DATE}")
    st.write("Progress is saved anonymously in this page's address so a refresh does not erase completed work.")
    st.button("Start over", width="stretch", on_click=restart_activity)

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
