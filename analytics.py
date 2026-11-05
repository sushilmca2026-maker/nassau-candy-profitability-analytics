"""Analytics layer for Project 2: Product Line Profitability & Margin Performance (Nassau Candy).
Pure pandas (no Streamlit), so every number can be tested and reused in notebooks."""
import pandas as pd


def load_candy(path, fizzy_to_other=True):
    """Load, validate and clean the Nassau Candy dataset. Returns (df, notes)."""
    df = pd.read_csv(path)
    notes = []
    for c in ["Division", "Product Name", "Region", "Ship Mode"]:
        df[c] = df[c].str.strip()
    df["Product Name"] = df["Product Name"].str.replace("Wonka Bar -Scrum", "Wonka Bar - Scrum", regex=False)
    notes.append("Standardized product labels (e.g. 'Wonka Bar - Scrumdiddlyumptious').")

    bad = (df["Sales"] <= 0) | (df["Units"] <= 0) | (df["Gross Profit"] < 0)
    removed = int(bad.sum())
    df = df[~bad].copy()
    mismatch = int(((df["Sales"] - df["Cost"] - df["Gross Profit"]).abs() > 0.02).sum())
    notes.append(f"Validated {len(df):,} rows ({removed} removed): no zero/negative sales, units or profit; "
                 f"Gross Profit = Sales - Cost on every row (mismatches: {mismatch}); no missing values.")

    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True)
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True)
    df["Ship Lag Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
    lo, hi = df["Ship Lag Days"].min(), df["Ship Lag Days"].max()
    df["Ship Date Valid"] = df["Ship Lag Days"] <= 365
    if lo > 365:
        notes.append(f"WARNING: ship dates are {lo / 365:.1f}-{hi / 365:.1f} years after order dates "
                     "(unrealistic). Shipping fields are excluded from all profitability conclusions.")
    id_year = pd.to_numeric(df["Order ID"].str.extract(r"^[A-Z]+-(\d{4})")[0])
    df["OrderID Year Mismatch"] = id_year != df["Order Date"].dt.year
    n_bad = int(df["OrderID Year Mismatch"].sum())
    if n_bad:
        notes.append(f"The year inside Order ID differs from the Order Date year on {n_bad:,} rows; "
                     "Order Date is used for all time analysis.")
    if fizzy_to_other:
        df.loc[df["Product Name"] == "Fizzy Lifting Drinks", "Division"] = "Other"
        notes.append("Fizzy Lifting Drinks moved from Sugar to Other to match the project brief.")
    notes.append("Each product has one fixed unit price and cost, so product-level margin never changes "
                 "over time; monthly overall margin varies only through product mix.")
    df["Gross Margin %"] = df["Gross Profit"] / df["Sales"] * 100
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    df["Order Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    return df, notes


def _safe(a, b):
    return float(a / b * 100) if b else float("nan")


def overall(df):
    s, p, u, c = (df[x].sum() for x in ["Sales", "Gross Profit", "Units", "Cost"])
    return {"Sales": s, "Profit": p, "Units": u, "Cost": c, "Gross Margin %": _safe(p, s),
            "Profit per Unit": float(p / u) if u else float("nan"), "Rows": len(df)}


def product_table(df):
    g = df.groupby(["Product Name", "Division"]).agg(
        Sales=("Sales", "sum"), Cost=("Cost", "sum"), Profit=("Gross Profit", "sum"),
        Units=("Units", "sum"), Rows=("Sales", "size")).reset_index()
    ts, tp = g.Sales.sum(), g.Profit.sum()
    g["Gross Margin %"] = g.Profit / g.Sales * 100
    g["Profit per Unit"] = g.Profit / g.Units
    g["Revenue Contribution %"] = g.Sales / ts * 100 if ts else 0.0
    g["Profit Contribution %"] = g.Profit / tp * 100 if tp else 0.0
    g["Cost % of Sales"] = g.Cost / g.Sales * 100
    return g.sort_values("Profit", ascending=False).reset_index(drop=True)


def division_table(df):
    g = df.groupby("Division").agg(Sales=("Sales", "sum"), Profit=("Gross Profit", "sum"),
                                   Units=("Units", "sum"), Rows=("Sales", "size")).reset_index()
    g["Gross Margin %"] = g.Profit / g.Sales * 100
    g["Revenue Share %"] = g.Sales / g.Sales.sum() * 100
    g["Profit Share %"] = g.Profit / g.Profit.sum() * 100
    g["Share Gap (pts)"] = g["Profit Share %"] - g["Revenue Share %"]
    return g


def quadrant(pt, margin_threshold=50.0):
    """Classify products: high/low sales (vs median product sales) x high/low margin (vs threshold)."""
    med = pt.Sales.median()
    def q(r):
        hs, hm = r.Sales >= med, r["Gross Margin %"] >= margin_threshold
        return ("High sales / high margin" if hs and hm else "High sales / low margin" if hs
                else "Low sales / high margin" if hm else "Low sales / low margin")
    out = pt.copy()
    out["Quadrant"] = out.apply(q, axis=1)
    return out


def pareto(pt, by="Profit"):
    """Cumulative contribution after sorting products by Sales or Profit."""
    p = pt.sort_values(by, ascending=False).reset_index(drop=True)
    p["Rank"] = p.index + 1
    p["Cumulative %"] = p[by].cumsum() / p[by].sum() * 100
    p["In top 80%"] = (p["Cumulative %"].shift(fill_value=0) < 80)
    return p


def dependency(pt):
    """Concentration indicators: products needed for 80%, top-N share and HHI of profit."""
    ps, pr = pareto(pt, "Sales"), pareto(pt, "Profit")
    sh = pt.Profit / pt.Profit.sum()
    return {"products": len(pt), "products_for_80_revenue": int(ps["In top 80%"].sum()),
            "products_for_80_profit": int(pr["In top 80%"].sum()),
            "top1_profit_share": float(pr[:1].Profit.sum() / pt.Profit.sum() * 100),
            "top5_profit_share": float(pr[:5].Profit.sum() / pt.Profit.sum() * 100),
            "profit_hhi": float((sh ** 2).sum() * 10000)}


def margin_flags(pt, threshold):
    """Flag products below the margin threshold and suggest an action (rule-based, not a forecast)."""
    out = pt.copy()
    def act(r):
        if r["Gross Margin %"] >= threshold:
            return "OK"
        a = ["Cost renegotiation / repricing (urgent)" if r["Gross Margin %"] < 20 else "Repricing review"]
        if r["Profit Contribution %"] < 0.1:
            a.append("Discontinuation review")
        return " + ".join(a)
    out["Flag"] = out.apply(act, axis=1)
    return out


def monthly_margin(df):
    m = df.groupby("Order Month")[["Sales", "Gross Profit"]].sum()
    m["Margin %"] = m["Gross Profit"] / m["Sales"] * 100
    return m.reset_index()


def margin_volatility(df):
    """Std-dev of monthly overall margin (points) and of each product's monthly margin."""
    m = monthly_margin(df)["Margin %"]
    pm = df.groupby(["Product Name", "Order Month"])[["Sales", "Gross Profit"]].sum()
    pm["m"] = pm["Gross Profit"] / pm["Sales"] * 100
    per = pm.groupby("Product Name")["m"].std().fillna(0).round(4).rename("Monthly margin std (pts)").reset_index()
    return float(m.std()) if len(m) > 1 else 0.0, per
