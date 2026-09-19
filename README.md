# The Receivables Challenge

The Receivables Challenge is a Chapter 8 Streamlit case for an introductory accounting course. Students follow one fictional company's receivables from the original claim through credit decisions, aging, valuation, write-offs, financial-statement presentation, liquidity analysis, and collection strategy.

The activity uses account increases and decreases, ending account balances, and financial-statement effects. It does not require bookkeeping mechanics that are outside the course.

## Student flow

1. Claims
2. Credit
3. Aging
4. Valuation
5. Reporting
6. Management

Progress is stored anonymously in a validated query parameter. No login, database, secrets, or student-identifying information is required.

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
