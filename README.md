# Product Line Profitability & Margin Performance Analysis: Nassau Candy Distributor

An interactive Streamlit dashboard and a tested analytics layer that show which products and divisions really drive profit, which products are margin risks, and how dependent the business is on a few products. Built on the Nassau Candy dataset (10,194 order lines, 15 products, 3 divisions).

> Built during a Data Analyst internship at Unified Mentor. Profit findings use Sales, Cost and Gross Profit only; shipping fields are excluded because the ship dates in the source data are unrealistic.

## Key results

| Finding | Result |
|---|---|
| Weighted gross margin | 65.91% (sales 141,783.63, gross profit 93,442.80) |
| Profit per unit (overall) | 2.42 |
| Profit concentration | 5 of 15 products give 80% of revenue **and** 80% of profit; the top 5 give 95.06% of profit |
| Top 5 products | All Wonka chocolate bars (92.88% of sales) |
| Division margins | Chocolate 67.45%, Other 44.97%, Sugar 68.10% (Sugar has only 34 rows) |
| Biggest margin risk | Kazookles: 7.69% margin, price 3.25 vs cost 3.00, profit 0.25 per unit |
| Growth | Sales +44.6% from 2024 to 2025 with a stable margin (65.83% vs 65.96%) |

## Dashboard (6 tabs)

1. **Product Profitability**: margin leaderboard, profit and margin charts, product quadrants, CSV export
2. **Division Performance**: revenue vs profit, margin distribution by division
3. **Cost vs Margin**: cost-sales scatter, margin risk flags with suggested actions, price needed to reach a target margin
4. **Profit Concentration**: Pareto chart, dependency indicators (products for 80%, top-5 share, HHI)
5. **Margin Over Time**: monthly margin and volatility (with the fixed-price caveat)
6. **Data Quality**: validation notes and warnings

**Sidebar filters:** order date range, division, margin-threshold slider, product search, and "show only products below threshold".

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
pytest -q                          # verifies the headline numbers
```

## Project structure

```
app.py                 Streamlit dashboard
analytics.py           Validation, margins, Pareto, risk flags, quadrants (no Streamlit)
data/
  Nassau_Candy_Distributor.csv            Original dataset
  corrected/Nassau_Candy_Corrected.csv    Cleaned export with added columns
tests/test_project2.py Checks the headline numbers
docs/                  Corrected project details, walkthrough, Q&A, data-quality report, tech stack
```

## Data quality (read this)

* **Ship dates are unusable:** every order ships 904 to 1,642 days (2.5 to 4.5 years) after the order date. They are flagged and excluded from conclusions. Profit analysis is unaffected.
* **Order ID year** (2021 to 2024) never matches the Order Date year (2024 to 2025); Order Date is used.
* **Fizzy Lifting Drinks** is "Sugar" in the raw file but "Other" in the project brief. The app follows the brief; `load_candy(path, fizzy_to_other=False)` keeps the raw label (Other 44.84%, Sugar 66.61%).
* **Fixed prices and costs:** each product has one unit price and one unit cost, so product-level margin never changes over time; monthly margin changes only through product mix (64.54% to 66.75%, std 0.53 points).
* No missing values, no zero or negative sales, units or profit, and Gross Profit = Sales - Cost on every row.

## Assumptions

* **Margin threshold:** 50% by default (adjustable).
* **Risk rules:** margin under 20% = urgent repricing or cost renegotiation; under the threshold = repricing review; profit contribution under 0.1% adds a discontinuation review. These are rules, not a forecast.
* **Price needed for a target margin** = unit cost / (1 - target margin). It assumes demand does not change, which the data cannot confirm.

## Limitations

* The Sugar division has very few rows, so its results are weak evidence.
* Prices and costs never change, so the data cannot show how customers react to price changes.
* Findings are descriptive; shipping and delivery analysis needs the correct ship dates.

## Deploy on Streamlit Community Cloud

Push this repository to GitHub, create a new app, choose the repo, and set the main file to `app.py`.
