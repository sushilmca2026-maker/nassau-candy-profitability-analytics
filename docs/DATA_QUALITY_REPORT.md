# Data Quality Report: Nassau_Candy_Distributor.csv

## Checks that passed
| Check | Result |
|---|---|
| Rows / columns | 10,194 / 18 (all 18 fields in the brief are present) |
| Missing values | 0 |
| Zero or negative Sales, Units, Gross Profit | 0 |
| Gross Profit = Sales - Cost | True on every row |
| Products | 15, matching the brief's product list; Product ID and name are one-to-one |
| Order ID repeats | 1,645 (expected: one order holds several products) |

## Issues found
| Issue | Detail | Handling |
|---|---|---|
| Ship dates unrealistic | 904 to 1,642 days after the order date on all rows (order dates 2024-01-02 to 2025-12-31; ship dates 2026-06-30 to 2030-06-28) | Flagged; excluded from conclusions |
| Order ID year mismatch | ID years 2021-2024 vs order dates 2024-2025 on all 10,194 rows | Order Date is used |
| Fizzy Lifting Drinks | Sugar in the data, Other in the brief | Moved to Other (switchable) |
| Label spacing | "Wonka Bar -Scrumdiddlyumptious" | Standardized |
| Fixed price and cost | One unit price and cost per product | Product margin volatility = 0; monthly margin varies by mix only |
| Postal codes | Short codes likely lost leading zeros | Not used |
| Small division | Sugar = 34 rows, 348.73 in sales (after the Fizzy change) | Read results with care |

## Issues in the original brief (corrected in docs/Project2_Details_Corrected.docx)
1. The conclusion describes shipping route efficiency (copied from another project).
2. The Pareto section mentions "congestion-prone states or region".
3. Factory coordinates and the product-factory table are not needed for profitability.
4. "Product long namer" typo; "government stakeholders" does not fit.
5. Sales is described as "total sales value of order" but is the value of one product line.
6. "Margin volatility over time" has no caveat about fixed prices.
