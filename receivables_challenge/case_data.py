"""Fictional Chapter 8 case content and student-facing choices."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    id: str
    document: str
    title: str
    story: str
    prompt: str
    options: tuple[str, ...]
    correct: str
    explanation: str
    account_effect: str
    statement_effect: str


@dataclass(frozen=True)
class Invoice:
    id: str
    customer: str
    balance: int
    timing: str
    days_past_due: int
    correct_bucket: str


COMPANY_NAME = "Gem City Event Services"
REPORTING_DATE = "June 30"

RECEIVABLE_TYPES = (
    "Accounts receivable",
    "Notes receivable",
    "Other receivable",
)

AGING_BUCKETS = (
    "Current",
    "1-30 days past due",
    "31-60 days past due",
    "61-90 days past due",
    "More than 90 days past due",
)

CLAIM_DECISIONS = (
    Decision(
        id="service_on_account",
        document="Customer invoice",
        title="A completed event has not been paid",
        story=(
            "Gem City completed $12,000 of event services for a business customer. "
            "The customer was billed and will pay next month."
        ),
        prompt="Which type of receivable increases?",
        options=RECEIVABLE_TYPES,
        correct="Accounts receivable",
        explanation=(
            "The customer owes an amount arising from an ordinary sale of services on account."
        ),
        account_effect="Accounts Receivable increases $12,000; Service Revenue increases $12,000.",
        statement_effect="Current assets, revenue, and net income increase $12,000.",
    ),
    Decision(
        id="customer_note",
        document="Signed 90-day agreement",
        title="An overdue customer signs a formal promise",
        story=(
            "A customer replaces an $8,000 overdue account balance with a written, "
            "interest-bearing promise to pay in 90 days."
        ),
        prompt="Which type of receivable now represents the claim?",
        options=RECEIVABLE_TYPES,
        correct="Notes receivable",
        explanation=(
            "A formal written promise with a stated payment date is a note receivable."
        ),
        account_effect="Notes Receivable increases $8,000; Accounts Receivable decreases $8,000.",
        statement_effect="The form of the asset changes, but total assets do not change on that date.",
    ),
    Decision(
        id="employee_advance",
        document="Employee advance request",
        title="An employee receives a travel advance",
        story=(
            "Gem City advances $1,200 to an employee for an upcoming conference. "
            "The employee must repay any unused amount."
        ),
        prompt="How should the amount owed by the employee be classified?",
        options=RECEIVABLE_TYPES,
        correct="Other receivable",
        explanation=(
            "The claim did not arise from a customer sale and is therefore an other receivable."
        ),
        account_effect="Other Receivables increases $1,200; Cash decreases $1,200.",
        statement_effect="One asset increases while another decreases, so total assets do not change.",
    ),
    Decision(
        id="interest_earned",
        document="Interest calculation",
        title="Interest has been earned but not collected",
        story=(
            "$300 of interest has accumulated on customer notes by June 30. "
            "The interest will be collected later."
        ),
        prompt="Which type of receivable includes the interest claim?",
        options=RECEIVABLE_TYPES,
        correct="Other receivable",
        explanation=(
            "Interest receivable is reported separately from the customer principal and is an other receivable."
        ),
        account_effect="Interest Receivable increases $300; Interest Revenue increases $300.",
        statement_effect="Assets, other revenue, and net income increase $300.",
    ),
    Decision(
        id="sales_return",
        document="Credit memo",
        title="A customer receives a sales return",
        story=(
            "A customer returns $1,500 of an earlier purchase made on account. "
            "Gem City reduces the amount the customer must pay."
        ),
        prompt="Which type of receivable is reduced?",
        options=RECEIVABLE_TYPES,
        correct="Accounts receivable",
        explanation=(
            "The original amount arose from a normal credit sale, so the return reduces accounts receivable."
        ),
        account_effect="Accounts Receivable decreases $1,500; Sales Returns and Allowances increases $1,500.",
        statement_effect="Current assets, net sales, and net income decrease $1,500.",
    ),
)


CREDIT_DECISIONS = (
    Decision(
        id="school_district",
        document="Credit application",
        title="Miami Valley School District",
        story=(
            "Five years in business, strong payment history, modest order, and stable public funding."
        ),
        prompt="What is the best credit decision?",
        options=(
            "Approve standard credit terms",
            "Approve only a small limit with shorter terms",
            "Require payment before providing services",
        ),
        correct="Approve standard credit terms",
        explanation=(
            "The customer has a strong payment record and manageable exposure. Standard terms protect sales without adding unusual risk."
        ),
        account_effect="Future approved sales can increase Accounts Receivable until the customer pays.",
        statement_effect="A balanced policy can support revenue while keeping collection risk reasonable.",
    ),
    Decision(
        id="startup_festival",
        document="Credit application",
        title="First-Year Festival LLC",
        story=(
            "No operating history, no business credit record, a large first order, and most funding depends on ticket sales next month."
        ),
        prompt="What is the best credit decision?",
        options=(
            "Approve standard credit terms",
            "Approve only a small limit with shorter terms",
            "Require payment before providing services",
        ),
        correct="Require payment before providing services",
        explanation=(
            "The requested exposure is large and repayment depends on an uncertain future event. Requiring payment avoids an unsupported credit risk."
        ),
        account_effect="Requiring payment prevents a high-risk Accounts Receivable balance from arising.",
        statement_effect="The company may give up some sales, but it protects cash and reduces expected losses.",
    ),
    Decision(
        id="late_repeat_customer",
        document="Customer history",
        title="Riverfront Promotions",
        story=(
            "A repeat customer places profitable orders but usually pays 15 to 25 days late. "
            "Its latest financial information is stable."
        ),
        prompt="What is the best credit decision?",
        options=(
            "Approve standard credit terms",
            "Approve only a small limit with shorter terms",
            "Require payment before providing services",
        ),
        correct="Approve only a small limit with shorter terms",
        explanation=(
            "A controlled limit and shorter terms preserve the relationship while responding to the documented late-payment pattern."
        ),
        account_effect="A lower limit caps the amount that can remain in Accounts Receivable.",
        statement_effect="The policy balances profitable sales against liquidity and collection risk.",
    ),
)


INVOICES = (
    Invoice(
        id="gem_city_arena",
        customer="Gem City Arena",
        balance=36_000,
        timing="Due July 10; not yet due",
        days_past_due=0,
        correct_bucket="Current",
    ),
    Invoice(
        id="flyer_fitness",
        customer="Flyer Fitness",
        balance=28_000,
        timing="6 days past due",
        days_past_due=6,
        correct_bucket="1-30 days past due",
    ),
    Invoice(
        id="miami_valley_events",
        customer="Miami Valley Events",
        balance=22_000,
        timing="38 days past due",
        days_past_due=38,
        correct_bucket="31-60 days past due",
    ),
    Invoice(
        id="riverfront_supply",
        customer="Riverfront Supply",
        balance=18_000,
        timing="72 days past due",
        days_past_due=72,
        correct_bucket="61-90 days past due",
    ),
    Invoice(
        id="buckeye_hospitality",
        customer="Buckeye Hospitality",
        balance=14_000,
        timing="105 days past due",
        days_past_due=105,
        correct_bucket="More than 90 days past due",
    ),
)


AGING_LOSS_RATES = {
    "Current": 0.01,
    "1-30 days past due": 0.04,
    "31-60 days past due": 0.10,
    "61-90 days past due": 0.25,
    "More than 90 days past due": 1.00,
}

BEGINNING_ALLOWANCE = 4_000
PERCENTAGE_OF_RECEIVABLES_RATE = 0.08
NET_CREDIT_SALES = 648_000
BEGINNING_NET_ACCOUNTS_RECEIVABLE = 92_000


REPORTING_DECISIONS = (
    Decision(
        id="writeoff_accounts",
        document="Authorized write-off",
        title="Buckeye Hospitality will not pay",
        story=(
            "Independent management approval has been obtained to write off the customer's $14,000 balance."
        ),
        prompt="How do the two receivable accounts change?",
        options=(
            "Accounts Receivable decreases $14,000; Allowance for Doubtful Accounts decreases $14,000",
            "Accounts Receivable decreases $14,000; Bad Debt Expense increases $14,000",
            "Cash decreases $14,000; Accounts Receivable decreases $14,000",
        ),
        correct="Accounts Receivable decreases $14,000; Allowance for Doubtful Accounts decreases $14,000",
        explanation=(
            "The expected loss was recognized earlier through the allowance. The specific write-off now reduces the customer balance and the allowance."
        ),
        account_effect="Gross Accounts Receivable and the Allowance each decrease $14,000.",
        statement_effect="Net realizable value remains $95,820 immediately before and after the write-off.",
    ),
    Decision(
        id="writeoff_control",
        document="Control policy",
        title="Who should approve a write-off?",
        story=(
            "Gem City wants to prevent premature write-offs and concealment of cash collection problems."
        ),
        prompt="Which approval policy is strongest?",
        options=(
            "The employee who receives customer cash should approve it",
            "A manager without daily cash or receivables duties should approve it",
            "Any employee may approve it when the customer is more than 90 days late",
        ),
        correct="A manager without daily cash or receivables duties should approve it",
        explanation=(
            "Independent approval and separation from cash and receivables duties reduce the risk of error or misuse."
        ),
        account_effect="Only authorized customer balances are removed from Accounts Receivable and the Allowance.",
        statement_effect="A strong control supports reliable receivables reporting.",
    ),
    Decision(
        id="balance_sheet",
        document="June 30 balance sheet",
        title="Present the customer receivables",
        story="Gem City must show both the recorded claims and the amount expected to be collected.",
        prompt="Which presentation is appropriate?",
        options=(
            "Current assets: gross Accounts Receivable less Allowance for Doubtful Accounts equals net Accounts Receivable",
            "Current assets: report only gross Accounts Receivable and omit the allowance",
            "Operating expenses: report the entire customer balance as an expense",
        ),
        correct="Current assets: gross Accounts Receivable less Allowance for Doubtful Accounts equals net Accounts Receivable",
        explanation=(
            "Users need the gross claim, the estimated uncollectible amount, and the resulting cash realizable value."
        ),
        account_effect="Accounts Receivable remains at its gross amount and the Allowance is shown as a reduction.",
        statement_effect="The balance sheet reports net Accounts Receivable of $95,820 before the specific write-off.",
    ),
    Decision(
        id="bad_debt_location",
        document="June income statement",
        title="Locate bad debt expense",
        story="The period's expected customer credit losses are part of operating the sales function.",
        prompt="Where should Bad Debt Expense appear?",
        options=(
            "Selling expense within operating expenses",
            "Current assets",
            "Other revenues and gains",
        ),
        correct="Selling expense within operating expenses",
        explanation="Bad debt expense is reported as a selling expense in operating expenses.",
        account_effect="Bad Debt Expense has increased by the amount needed to reach the required ending allowance.",
        statement_effect="Operating expenses increase and net income decreases.",
    ),
    Decision(
        id="interest_location",
        document="June income statement",
        title="Locate interest revenue",
        story="Gem City earned interest from formal customer notes rather than from its main event-service operations.",
        prompt="Where should Interest Revenue appear?",
        options=(
            "Sales revenue",
            "Other revenues and gains outside operating income",
            "Current liabilities",
        ),
        correct="Other revenues and gains outside operating income",
        explanation="Interest revenue is reported outside the operating section because it is not part of the company's main revenue activity.",
        account_effect="Interest Revenue increases as interest is earned.",
        statement_effect="Other revenue and net income increase.",
    ),
    Decision(
        id="risk_disclosure",
        document="Notes to the financial statements",
        title="Collection risk is becoming significant",
        story="The balance more than 90 days past due has risen sharply and one large customer is in financial distress.",
        prompt="What should Gem City do in its external reporting?",
        options=(
            "Discuss the significant collection risk in the notes",
            "Wait until every affected customer formally defaults",
            "Remove all overdue balances without explanation",
        ),
        correct="Discuss the significant collection risk in the notes",
        explanation="Significant receivables risk should be explained so users can understand the uncertainty surrounding collection.",
        account_effect="The recorded balances remain supported by the company's estimate and customer evidence.",
        statement_effect="The notes add information needed to interpret the reported receivables.",
    ),
)


MANAGEMENT_DECISIONS = (
    Decision(
        id="turnover",
        document="Liquidity dashboard",
        title="How often were receivables collected?",
        story=(
            "Net credit sales were $648,000. Beginning net Accounts Receivable was $92,000, "
            "and ending net Accounts Receivable is $95,820."
        ),
        prompt="What is the accounts receivable turnover, rounded to one decimal place?",
        options=("5.5 times", "6.9 times", "7.4 times"),
        correct="6.9 times",
        explanation="Average net Accounts Receivable is $93,910. Dividing $648,000 by $93,910 gives approximately 6.9 times.",
        account_effect="The ratio connects net credit sales with the average net amount invested in customer receivables.",
        statement_effect="A higher turnover generally indicates faster conversion of receivables into cash.",
    ),
    Decision(
        id="collection_period",
        document="Liquidity dashboard",
        title="How long does collection take?",
        story="Gem City's accounts receivable turnover is approximately 6.9 times.",
        prompt="What is the average collection period, rounded to the nearest half day?",
        options=("30.0 days", "45.0 days", "52.9 days"),
        correct="52.9 days",
        explanation="Dividing 365 days by approximately 6.9 gives an average collection period of about 52.9 days.",
        account_effect="Slow collection keeps more resources tied up in Accounts Receivable.",
        statement_effect="The ratio does not change reported balances, but it helps users interpret liquidity.",
    ),
    Decision(
        id="terms_comparison",
        document="Credit policy",
        title="Compare performance with the terms",
        story="Gem City's standard payment period is 30 days, but the average collection period is about 52.9 days.",
        prompt="What does the comparison suggest?",
        options=(
            "Collections appear effective because 52.9 days is longer than 30 days",
            "Collections need attention because the average period substantially exceeds the stated terms",
            "No conclusion is possible because credit terms never affect collection analysis",
        ),
        correct="Collections need attention because the average period substantially exceeds the stated terms",
        explanation="The collection period should not greatly exceed the time customers are allowed to pay.",
        account_effect="Late collection leaves Accounts Receivable outstanding longer and delays Cash increases.",
        statement_effect="The comparison helps evaluate the effectiveness of credit and collection policies.",
    ),
    Decision(
        id="urgent_cash",
        document="Treasurer request",
        title="Cash is needed next week",
        story="Gem City needs immediate cash from receivables already on its books and cannot wait for customers to pay.",
        prompt="Which action most directly produces immediate cash?",
        options=(
            "Sell selected receivables to a factor",
            "Extend every customer's payment period",
            "Increase the estimated allowance",
        ),
        correct="Sell selected receivables to a factor",
        explanation="Factoring exchanges receivables for immediate cash at a discount, shortening the cash-to-cash cycle.",
        account_effect="Cash increases immediately while the receivables sold are removed; a factoring cost is recognized.",
        statement_effect="Liquidity improves immediately, but the discount reduces income.",
    ),
    Decision(
        id="dashboard_focus",
        document="Customer analytics",
        title="Direct the collection team",
        story="The dashboard shows $32,000 is more than 60 days past due, including $14,000 beyond 90 days.",
        prompt="Which use of the dashboard is most valuable now?",
        options=(
            "Focus collection work on the oldest and highest-risk customer balances",
            "Contact only customers whose invoices are current",
            "Ignore customer detail and review total sales only",
        ),
        correct="Focus collection work on the oldest and highest-risk customer balances",
        explanation="Aging and customer-level detail help management target the balances most likely to delay cash or become uncollectible.",
        account_effect="Successful follow-up decreases Accounts Receivable and increases Cash.",
        statement_effect="Targeted collection can improve liquidity without automatically reducing sales to reliable customers.",
    ),
    Decision(
        id="balanced_plan",
        document="Board recommendation",
        title="Choose a balanced receivables plan",
        story="Management wants stronger cash flow without unnecessarily driving away reliable customers.",
        prompt="Which recommendation best balances sales, liquidity, and collection risk?",
        options=(
            "Stop offering credit to every customer",
            "Keep competitive terms, strengthen risk screening, target overdue accounts, and test an early-payment discount",
            "Extend every due date and wait for customers to pay voluntarily",
        ),
        correct="Keep competitive terms, strengthen risk screening, target overdue accounts, and test an early-payment discount",
        explanation="The balanced plan addresses who receives credit, payment incentives, monitoring, and collection follow-up without treating every customer as equally risky.",
        account_effect="Better policy should convert Accounts Receivable to Cash sooner while limiting future high-risk balances.",
        statement_effect="The goal is stronger liquidity with an acceptable balance among revenue, collection cost, and expected losses.",
    ),
)


VALUATION_FIELDS = (
    ("ending_allowance", "Required ending Allowance for Doubtful Accounts"),
    ("allowance_increase", "Increase needed in the Allowance"),
    ("bad_debt_increase", "Increase in Bad Debt Expense"),
    ("net_realizable_value", "Net realizable value of Accounts Receivable"),
)
