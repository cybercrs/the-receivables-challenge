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
        id="longer_payment_window",
        document="Credit-terms comparison",
        title="A longer payment window",
        story=(
            "Gem City is comparing its usual 30-day payment period with a 60-day payment period."
        ),
        prompt="What is the clearest tradeoff of offering customers more time to pay?",
        options=(
            "It may support sales, but it can delay cash and keep receivables outstanding longer",
            "It increases cash immediately and eliminates collection risk",
            "It changes a customer account into a note receivable automatically",
        ),
        correct="It may support sales, but it can delay cash and keep receivables outstanding longer",
        explanation=(
            "More generous terms can make buying easier for customers, but the company waits longer for cash and remains exposed to collection risk."
        ),
        account_effect="Accounts Receivable may remain outstanding longer before Cash increases.",
        statement_effect="Sales may benefit, while liquidity can weaken and expected collection losses can rise.",
    ),
    Decision(
        id="shorter_payment_window",
        document="Credit-terms comparison",
        title="A shorter payment window",
        story=(
            "Gem City is evaluating what could happen if customers must pay sooner than under its current policy."
        ),
        prompt="Which statement best describes the likely tradeoff?",
        options=(
            "Cash may arrive sooner and risk may fall, but some customers may find the terms less attractive",
            "Revenue must increase because every customer will accept the shorter period",
            "The Allowance for Doubtful Accounts is no longer needed",
        ),
        correct="Cash may arrive sooner and risk may fall, but some customers may find the terms less attractive",
        explanation=(
            "Shorter terms can improve the timing of collection and reduce exposure, but overly restrictive terms can discourage otherwise profitable sales."
        ),
        account_effect="Accounts Receivable may convert to Cash sooner and remain outstanding for fewer days.",
        statement_effect="Liquidity may improve, but sales can be affected if customers prefer competitors' terms.",
    ),
    Decision(
        id="early_payment_discount",
        document="Credit-terms comparison",
        title="An early-payment discount",
        story=(
            "Gem City is considering a small discount for customers who pay early instead of waiting until the final due date."
        ),
        prompt="What is the primary benefit and cost of this feature?",
        options=(
            "It may speed collection, but the discount reduces the amount of revenue retained",
            "It delays collection, but it increases the amount every customer pays",
            "It removes receivables from the balance sheet before customers pay",
        ),
        correct="It may speed collection, but the discount reduces the amount of revenue retained",
        explanation=(
            "The company gives up a small portion of the selling price in exchange for receiving cash sooner from customers who take the discount."
        ),
        account_effect="Cash increases and Accounts Receivable decreases sooner when a customer pays early.",
        statement_effect="Liquidity can improve, while the discount reduces net sales and net income.",
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


AGING_DECISIONS = (
    Decision(
        id="box_1_current_balance",
        document="Completed aging schedule",
        title="Interpret box 1",
        story="Box 1 is in the Current row under Receivables.",
        prompt="What does the amount in box 1 represent?",
        options=(
            "The total open customer balances that are not yet past due at June 30",
            "The cash already collected from current customers during June",
            "The portion of current receivables expected to be uncollectible",
        ),
        correct="The total open customer balances that are not yet past due at June 30",
        explanation="The receivables column groups outstanding customer claims by age. Current balances have not yet passed their due dates.",
        account_effect="Box 1 is part of gross Accounts Receivable; it does not record a new account change.",
        statement_effect="The amount is included in current assets before the allowance is subtracted.",
    ),
    Decision(
        id="box_2_loss_rate",
        document="Completed aging schedule",
        title="Interpret box 2",
        story="Box 2 is in the 61-90 days past due row under Estimated loss rate.",
        prompt="What does the percentage in box 2 represent?",
        options=(
            "Management's estimate of the portion of that age group that will not be collected",
            "The percentage of customers whose invoices are exactly 61 days old",
            "The interest rate charged on every overdue customer balance",
        ),
        correct="Management's estimate of the portion of that age group that will not be collected",
        explanation="An aging schedule applies an estimated loss rate to each age group. The rate generally rises as balances become older.",
        account_effect="The percentage helps estimate the required Allowance balance; it does not change an account by itself.",
        statement_effect="The estimate supports the amount used to reduce gross receivables to net realizable value.",
    ),
    Decision(
        id="box_3_bucket_estimate",
        document="Completed aging schedule",
        title="Interpret box 3",
        story="Box 3 is in the More than 90 days past due row under Estimated uncollectible.",
        prompt="How should the amount in box 3 be interpreted?",
        options=(
            "It is this age group's contribution to the allowance estimate, not proof that a specific balance has already been written off",
            "It is cash that customers in this age group already paid",
            "It is Bad Debt Expense for the entire company before considering any other age group",
        ),
        correct="It is this age group's contribution to the allowance estimate, not proof that a specific balance has already been written off",
        explanation="The amount combines the balance in that age group with its estimated loss rate. The schedule estimates collection risk; it does not perform a specific write-off.",
        account_effect="The amount contributes to the required ending Allowance for Doubtful Accounts.",
        statement_effect="It helps determine the reduction from gross Accounts Receivable to net realizable value.",
    ),
    Decision(
        id="box_4_total_estimate",
        document="Completed aging schedule",
        title="Interpret box 4",
        story="Box 4 is the total of the Estimated uncollectible column.",
        prompt="How is the total in box 4 used in the allowance method?",
        options=(
            "It is the required ending Allowance balance after the bad debt adjustment",
            "It is automatically the amount of Bad Debt Expense for the period",
            "It is the ending gross Accounts Receivable balance",
        ),
        correct="It is the required ending Allowance balance after the bad debt adjustment",
        explanation="The aging total is the target ending allowance. The expense equals the increase needed to move the existing allowance to that target.",
        account_effect="Allowance for Doubtful Accounts must end at the box 4 total after adjustment.",
        statement_effect="The balance sheet subtracts that ending allowance from gross Accounts Receivable.",
    ),
)


VALUATION_BENEFIT_OPTIONS = (
    "It reflects that older receivables often have a different collection risk than newer receivables",
    "It guarantees the exact amount of cash the company will collect",
    "It eliminates the need to estimate an allowance balance",
    "It treats every overdue customer balance as an immediate write-off",
)

VALUATION_BENEFIT_CORRECT = VALUATION_BENEFIT_OPTIONS[0]

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
        id="balance_sheet",
        document="June 30 balance sheet",
        title="Review a proposed presentation",
        story="Gem City is preparing the current-assets section after completing its bad debt adjustment.",
        prompt="Which presentation is appropriate?",
        options=(
            "Current assets: gross Accounts Receivable less Allowance for Doubtful Accounts equals net Accounts Receivable",
            "Current assets: report gross Accounts Receivable and disclose the allowance in the notes without presenting it on the balance sheet",
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
        title="Review an expense classification",
        story="Gem City is preparing its income statement after updating the allowance estimate.",
        prompt="Where should Bad Debt Expense appear?",
        options=(
            "Operating expense",
            "Cost of goods sold",
            "Other expense outside operating income",
        ),
        correct="Operating expense",
        explanation="Bad debt expense is reported as an operating expense.",
        account_effect="Bad Debt Expense has increased by the amount needed to reach the required ending allowance.",
        statement_effect="Operating expenses increase and net income decreases.",
    ),
    Decision(
        id="interest_location",
        document="June income statement",
        title="Review a revenue classification",
        story="Gem City earned interest on customer notes during June.",
        prompt="Where should Interest Revenue appear?",
        options=(
            "Sales revenue",
            "Other revenues and gains outside operating income",
            "Operating expense",
        ),
        correct="Other revenues and gains outside operating income",
        explanation="Interest revenue is reported outside the operating section because it is not part of the company's main revenue activity.",
        account_effect="Interest Revenue increases as interest is earned.",
        statement_effect="Other revenue and net income increase.",
    ),
    Decision(
        id="risk_disclosure",
        document="Notes to the financial statements",
        title="Review a proposed disclosure",
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
        title="Read the turnover signal",
        story="Use the dashboard's turnover measure to interpret how receivables moved through the business during the year.",
        prompt="Which statement best interprets receivables turnover?",
        options=(
            "It indicates how often average net receivables were converted through credit sales and collection during the year",
            "It is the percentage of receivables that management expects not to collect",
            "It measures how much profit the company earned on each credit sale",
        ),
        correct="It indicates how often average net receivables were converted through credit sales and collection during the year",
        explanation="Receivables turnover relates net credit sales to average net Accounts Receivable and helps evaluate how quickly receivables move toward cash.",
        account_effect="The ratio connects net credit sales with the average net amount invested in customer receivables.",
        statement_effect="A higher turnover generally indicates faster conversion of receivables into cash.",
    ),
    Decision(
        id="collection_period",
        document="Credit policy comparison",
        title="Read the collection-cycle signal",
        story="Gem City's standard customer payment period is 30 days.",
        prompt="What concern is raised when that policy is compared with the dashboard?",
        options=(
            "Collection practices may need attention because average collection takes substantially longer than the stated payment period",
            "Gem City should extend its stated payment period to match current customer behavior before considering other collection actions",
            "Gem City should increase its allowance because the collection period establishes the amount that will be uncollectible",
        ),
        correct="Collection practices may need attention because average collection takes substantially longer than the stated payment period",
        explanation="An average collection period substantially longer than the stated terms suggests that collection performance needs attention.",
        account_effect="Slow collection keeps more resources tied up in Accounts Receivable.",
        statement_effect="The ratio does not change reported balances, but it helps users interpret liquidity.",
    ),
    Decision(
        id="urgent_cash",
        document="Treasurer request",
        title="Evaluate a short-term cash option",
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
        document="Follow-up planning",
        title="Choose the next management view",
        story="The summary dashboard identifies a collection concern but does not identify the customers creating it.",
        prompt="What additional information would be most useful before the team contacts customers?",
        options=(
            "Customer-by-customer aging details and recent payment history",
            "The total number of employees in every operating department",
            "The company's cash sales for the year with no customer detail",
        ),
        correct="Customer-by-customer aging details and recent payment history",
        explanation="Aging and customer-level detail help management target the balances most likely to delay cash or become uncollectible.",
        account_effect="Successful follow-up decreases Accounts Receivable and increases Cash.",
        statement_effect="Targeted collection can improve liquidity without automatically reducing sales to reliable customers.",
    ),
    Decision(
        id="balanced_plan",
        document="Board recommendation",
        title="Bring the evidence together",
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
    (
        "net_realizable_value",
        "Net realizable value of Accounts Receivable reported on the June 30 balance sheet after the bad debt adjustment",
    ),
)
