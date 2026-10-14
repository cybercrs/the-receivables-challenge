"""Export original teaching content/presentation and independent Python test oracles.

Python is build/test tooling only. The delivered site uses HTML/CSS/JavaScript.
"""

from __future__ import annotations

import hashlib
import json
import sys
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from browser.build import shared_source  # noqa: E402
from receivables_challenge import case_data as case, engine, progress  # noqa: E402

GROUPS = [
    (1, "claim", "c", "ci", "cr", case.CLAIM_DECISIONS),
    (2, "credit", "d", "di", "dr", case.CREDIT_DECISIONS),
    (3, "aging", "a", "ai", "ar", case.AGING_DECISIONS),
    (5, "reporting", "r", "ri", "rr", case.REPORTING_DECISIONS),
    (6, "management", "m", "mi", "mr", case.MANAGEMENT_DECISIONS),
]
RENDERERS = [
    "render_briefing",
    "render_claims_stage",
    "render_credit_stage",
    "render_aging_stage",
    "render_valuation_stage",
    "render_reporting_stage",
    "render_management_stage",
    "render_completion",
]


class State(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class Container:
    def __init__(self, recorder, node):
        self.recorder, self.node = recorder, node

    def __enter__(self):
        self.recorder.stack.append(self.node["children"])
        return self

    def __exit__(self, *args):
        self.recorder.stack.pop()

    def metric(self, label, value, **kwargs):
        self.node["children"].append(
            {"kind": "metric", "label": label, "value": value, **kwargs}
        )


class Recorder:
    def __init__(self):
        self.session_state = State()
        self.stack = [[]]

    def node(self, kind, **kwargs):
        item = {"kind": kind, **kwargs}
        self.stack[-1].append(item)
        return item

    def set_page_config(self, **kwargs):
        pass

    def markdown(self, text, unsafe_allow_html=False):
        self.node("html" if unsafe_allow_html else "markdown", text=text.strip())

    def __getattr__(self, kind):
        if kind in {
            "header",
            "subheader",
            "write",
            "success",
            "warning",
            "info",
            "caption",
        }:
            return lambda text: self.node(kind, text=text.replace(r"\$", "$"))
        raise AttributeError(kind)

    def dataframe(self, rows, **kwargs):
        self.node("table", rows=rows)

    def progress(self, value, text):
        self.node("progress", value=value, text=text)

    def radio(self, label, options, **kwargs):
        self.node(
            "radio", label=label.replace(r"\$", "$"), options=options, key=kwargs["key"]
        )
        index = kwargs.get("index")
        return options[index] if index is not None else None

    def number_input(self, label, **kwargs):
        self.node(
            "number",
            label=label,
            key=kwargs["key"],
            min=kwargs["min_value"],
            max=kwargs["max_value"],
            step=kwargs["step"],
        )
        return kwargs.get("value", 0)

    def button(self, label, **kwargs):
        self.node("button", label=label, key=kwargs.get("key"))
        return False

    def columns(self, count):
        count = count if isinstance(count, int) else len(count)
        node = self.node("columns", children=[])
        columns = []
        for _ in range(count):
            item = {"kind": "column", "children": []}
            node["children"].append(item)
            columns.append(Container(self, item))
        return columns

    def expander(self, label):
        return Container(
            self, self.node("details", label=label.replace(r"\$", "$"), children=[])
        )

    @contextmanager
    def capture(self):
        self.stack = [[]]
        yield self.stack[0]


def state_at(stage, index=0, status="unanswered"):
    state = State(progress.activity_defaults())
    state.rc_shuffle_seed = 0
    state.rc_stage = stage
    for group_stage, prefix, _draft, _idx, _responses, items in GROUPS:
        key = f"rc_{prefix}_index"
        state[key] = (
            len(items) - 1
            if group_stage < stage
            else index
            if group_stage == stage
            else 0
        )
        responses = {}
        for i, item in enumerate(items):
            if group_stage < stage or (group_stage == stage and i < index):
                responses[item.id] = item.correct
            elif group_stage == stage and i == index and status != "unanswered":
                responses[item.id] = (
                    item.correct
                    if status == "correct"
                    else next(x for x in item.options if x != item.correct)
                )
        state[f"rc_{prefix}_responses"] = responses
    if stage > 4 or (stage == 4 and status != "unanswered"):
        state.rc_valuation_submitted = True
        state.rc_valuation_responses = (
            engine.valuation_values()
            if stage > 4 or status == "correct"
            else {key: 0 for key, _ in case.VALUATION_FIELDS}
        )
        state.rc_valuation_benefit = (
            case.VALUATION_BENEFIT_CORRECT
            if stage > 4 or status == "correct"
            else case.VALUATION_BENEFIT_OPTIONS[1]
        )
    return state


AGING_TEXT = {
    "Box 1 is in the Current row under Receivables.": "Box 1 is in the Current column on the Accounts receivable row.",
    "Box 2 is in the 61-90 days past due row under Estimated loss rate.": "Box 2 is in the 61-90 days past due column on the Estimated loss rate row.",
    "Box 3 is in the More than 90 days past due row under Estimated uncollectible.": "Box 3 is in the More than 90 days past due column on the Estimated uncollectible row.",
    "Box 4 is the total of the Estimated uncollectible column.": "Box 4 is the total on the Estimated uncollectible row.",
    "The receivables column groups outstanding customer claims by age.": "The Accounts receivable row groups outstanding customer claims across age-bucket columns.",
}


def native_aging_words(value):
    if isinstance(value, str):
        for old, new in AGING_TEXT.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [native_aging_words(item) for item in value]
    if isinstance(value, dict):
        return {key: native_aging_words(item) for key, item in value.items()}
    return value


def native_schedule(source_rows):
    """Conventional horizontal schedule, including totals and original cell markers."""
    metrics = [
        ("Accounts receivable", "Receivables"),
        ("Estimated loss rate", "Estimated loss rate"),
        ("Estimated uncollectible", "Estimated uncollectible"),
    ]
    return [
        {"Measure": label, **{row["Age category"]: row[key] for row in source_rows}}
        for label, key in metrics
    ]


def native_screen(events, stage, schedule):
    """Apply requested native-only curriculum changes; never modify the old renderer."""
    revised = []
    for node in events:
        if stage == 3:
            node = native_aging_words(node)
        if stage in (3, 4) and node["kind"] == "table":
            node = {
                "kind": "table",
                "rows": schedule,
                "fixedRows": True,
                "orientation": "age-buckets-across",
            }
        if stage == 4:
            if (
                node["kind"] == "number"
                and node["key"] == "widget_valuation_ending_allowance"
            ):
                continue
            if (
                node["kind"] == "html"
                and "feedback-label" in node["text"]
                and "Required ending Allowance for Doubtful Accounts" in node["text"]
            ):
                continue
            if node["kind"] == "caption" and node["text"].startswith(
                "Method comparison:"
            ):
                continue
            if node["kind"] == "write" and node["text"].startswith(
                "Use the aging result"
            ):
                node = {
                    "kind": "write",
                    "text": "Use the full aging schedule, including its totals, to determine the adjustment, the related account increases, and net realizable value reported after the bad debt adjustment.",
                }
        if (
            stage == 7
            and node["kind"] == "details"
            and node["label"].startswith("Why did aging produce")
        ):
            node = {
                "kind": "details",
                "label": "How can aging be more informative than a single flat loss-rate estimate?",
                "children": [
                    {
                        "kind": "write",
                        "text": "One alternative is a single flat-rate estimate: apply the same estimated loss rate to all receivables. As an illustration, 8% of $118,000 gives a $9,440 allowance estimate.",
                    },
                    {
                        "kind": "write",
                        "text": "The aging schedule instead applies a different estimated loss rate to each age group, producing the $22,180 total shown in the schedule. Older invoices often have a different collection risk than newer invoices.",
                    },
                    {
                        "kind": "write",
                        "text": "When the age-specific rates are well supported by collection evidence, aging can give a more informative estimate of the mix of collection risks. Neither approach guarantees accuracy: both are estimates that should be checked against subsequent collections and updated as conditions change.",
                    },
                ],
            }
        revised.append(node)
    return revised


def export():
    recorder = Recorder()
    namespace = {}
    with patch.dict(sys.modules, {"streamlit": recorder}):
        exec(compile(shared_source(), "original_renderer", "exec"), namespace)
    positions = [{"stage": 0, "index": 0}]
    for stage in range(1, 7):
        items = next((g[-1] for g in GROUPS if g[0] == stage), [None])
        positions.extend({"stage": stage, "index": i} for i in range(len(items)))
    positions.append({"stage": 7, "index": 0})
    schedule = native_schedule(namespace["completed_aging_schedule"]())
    screens = []
    for position in positions:
        variants = {}
        for status in ["unanswered", "wrong", "correct"]:
            recorder.session_state = state_at(**position, status=status)
            with recorder.capture() as events:
                namespace[RENDERERS[position["stage"]]]()
            variants[status] = native_screen(events, position["stage"], schedule)
        screens.append({**position, "variants": variants})
    with recorder.capture() as hero:
        namespace["render_hero"]()
    data = {
        "source": "81f1411b256f635b7c31698b81a32c68b91ca4fa",
        "company": case.COMPANY_NAME,
        "date": case.REPORTING_DATE,
        "groups": [
            {
                "stage": stage,
                "prefix": prefix,
                "draft": draft,
                "indexKey": idx,
                "responseKey": responses,
                "items": [
                    native_aging_words(asdict(x)) if stage == 3 else asdict(x)
                    for x in items
                ],
            }
            for stage, prefix, draft, idx, responses, items in GROUPS
        ],
        "invoices": [asdict(x) for x in case.INVOICES],
        "buckets": case.AGING_BUCKETS,
        "rates": case.AGING_LOSS_RATES,
        "beginningAllowance": case.BEGINNING_ALLOWANCE,
        "percentageRate": case.PERCENTAGE_OF_RECEIVABLES_RATE,
        "creditSales": case.NET_CREDIT_SALES,
        "beginningNet": case.BEGINNING_NET_ACCOUNTS_RECEIVABLE,
        "valuationFields": [
            field for field in case.VALUATION_FIELDS if field[0] != "ending_allowance"
        ],
        "legacyValuationFields": case.VALUATION_FIELDS,
        "nativeRevision": "2026-10-14-aging-horizontal",
        "benefitOptions": case.VALUATION_BENEFIT_OPTIONS,
        "benefitCorrect": case.VALUATION_BENEFIT_CORRECT,
        "stages": namespace["STAGE_LABELS"],
        "hero": hero,
        "positions": positions,
        "screens": screens,
    }
    here = Path(__file__).resolve().parent
    (here / "content.js").write_text(
        "// Generated from unchanged Python sources with native-only curriculum overrides.\nexport const DATA = "
        + json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        + ";\n"
    )
    css = namespace["APP_CSS"].replace("<style>", "").replace("</style>", "")
    (here / "original.css").write_text(css.strip() + "\n")
    fixtures = {
        "calculations": {
            "agingTotals": engine.aging_totals(),
            "agingRows": engine.aging_allowance_rows(),
            "gross": engine.gross_accounts_receivable(),
            "required": engine.required_ending_allowance(),
            "percentage": engine.percentage_of_receivables_estimate(),
            "valuation": engine.valuation_values(),
            "writeoff": [
                engine.writeoff_comparison(n) for n in [0, 1, 14000, 22180, 118000]
            ],
            "dashboard": engine.dashboard_metrics(),
        },
        "currency": [
            [x, engine.format_currency(x)]
            for x in [-1000.5, -2.5, -1.5, -0.5, 0, 0.5, 1.5, 2.5, 999.5, 1000.5]
        ],
        "snapshots": [],
        "shuffles": [],
    }
    for stage in range(8):
        state = state_at(
            stage, status="wrong" if stage in [1, 2, 3, 4, 5, 6] else "correct"
        )
        payload = progress.snapshot_from_state(state)
        progress.validate_snapshot(payload)
        fixtures["snapshots"].append(
            {"token": progress.encode_state(state), "payload": payload}
        )
    for seed in [0, 1, 42, 2**53 + 1, 2**63 - 1]:
        recorder.session_state.rc_shuffle_seed = seed
        for _stage, prefix, _draft, _idx, _responses, items in GROUPS:
            for item in items:
                salt = f"{prefix}-answer-order:{item.id}"
                fixtures["shuffles"].append(
                    {
                        "seed": str(seed),
                        "salt": salt,
                        "input": item.options,
                        "output": namespace["shuffled"](item.options, salt),
                    }
                )
        fixtures["shuffles"].append(
            {
                "seed": str(seed),
                "salt": "valuation-benefit-order",
                "input": case.VALUATION_BENEFIT_OPTIONS,
                "output": namespace["shuffled"](
                    case.VALUATION_BENEFIT_OPTIONS, "valuation-benefit-order"
                ),
            }
        )
    (here / "tests/python-oracles.json").write_text(
        json.dumps(fixtures, ensure_ascii=True, indent=2) + "\n"
    )
    manifest = {
        "source": data["source"],
        "choice_decisions": sum(len(g[-1]) for g in GROUPS),
        "pages": len(positions),
        "screen_variants": len(screens) * 3,
        "native_checkpoints": sum(len(g[-1]) for g in GROUPS)
        + len(data["valuationFields"])
        + 1,
        "native_only_overrides": [
            "horizontal full aging schedules",
            "remove redundant allowance target",
            "introduce flat rate only in debrief",
        ],
        "app_owned_assets": [],
        "generated_sha256": {
            name: hashlib.sha256((here / name).read_bytes()).hexdigest()
            for name in ["content.js", "original.css"]
        },
    }
    (here / "tests/content-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    export()
