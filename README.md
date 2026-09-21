# The Receivables Challenge

The Receivables Challenge is a Streamlit learning experience for introductory accounting. Students follow one fictional company's receivables from the original claim through credit-term tradeoffs, interpretation of a completed aging schedule, valuation, write-offs, financial-statement presentation, liquidity analysis, and collection strategy.

The activity uses account increases and decreases, ending account balances, and financial-statement effects. It does not require bookkeeping mechanics that are outside the course.

## Student flow

1. Claims
2. Credit
3. Aging
4. Valuation
5. Reporting
6. Management

Progress is stored anonymously in a validated query parameter. It preserves the current step, submitted work, unfinished selections, and each student's randomized answer order. Students can refresh or bookmark the current URL and resume, while **Start over** replaces the saved state with a fresh activity. Navigation to a new step also resets the content area to the top. No login, database, secrets, or student-identifying information is required.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Verify

```bash
python -m unittest discover -s tests -v
python -m py_compile streamlit_app.py receivables_challenge/*.py
```
