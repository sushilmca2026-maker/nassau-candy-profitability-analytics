"""Streamlit dashboard: Product Line Profitability & Margin Performance Analysis (Nassau Candy)."""
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as an

st.set_page_config(page_title="Nassau Candy Profitability", page_icon="🍬", layout="wide")
DATA = Path(__file__).parent / "data" / "Nassau_Candy_Distributor.csv"


@st.cache_data
def get_data(path):
    return an.load_candy(path)


df_all, notes = get_data(str(DATA))
money = lambda v: f"${v:,.0f}"

st.title("🍬 Product Line Profitability & Margin Performance")
st.caption("Nassau Candy Distributor | 15 products, 3 divisions | shipping fields excluded (unreliable dates)")

# ---------------- Sidebar filters ----------------
sb = st.sidebar
sb.header("Filters")
dmin, dmax = df_all["Order Date"].min().date(), df_all["Order Date"].max().date()
rng = sb.date_input("Order date range", (dmin, dmax), min_value=dmin, max_value=dmax)
start, end = (rng[0], rng[1]) if len(rng) == 2 else (dmin, dmax)
divs = sb.multiselect("Division", sorted(df_all.Division.unique()), default=sorted(df_all.Division.unique()))
thr = sb.slider("Margin threshold (%)", 0, 100, 50, help="Products below this margin are flagged as risks")
search = sb.text_input("Product search", "")
only_low = sb.checkbox("Show only products below threshold")

df = df_all[(df_all["Order Date"].dt.date >= start) & (df_all["Order Date"].dt.date <= end)
            & df_all.Division.isin(divs)]
if search.strip():
    df = df[df["Product Name"].str.contains(search.strip(), case=False, regex=False)]
if df.empty:
    st.warning("No data for the current filters. Widen the date range, divisions or search.")
    st.stop()
pt = an.product_table(df)
flags = an.margin_flags(pt, thr)
if only_low:
    flags = flags[flags.Flag != "OK"]
o = an.overall(df)

c = st.columns(5)
c[0].metric("Sales", money(o["Sales"]))
c[1].metric("Gross profit", money(o["Profit"]))
c[2].metric("Weighted gross margin", f"{o['Gross Margin %']:.2f}%")
c[3].metric("Profit per unit", f"${o['Profit per Unit']:.2f}")
c[4].metric("Order lines", f"{o['Rows']:,}")

tabs = st.tabs(["1. Product Profitability", "2. Division Performance", "3. Cost vs Margin",
                "4. Profit Concentration", "5. Margin Over Time", "6. Data Quality"])

# ---------------- 1. Product profitability ----------------
with tabs[0]:
    show = ["Product Name", "Division", "Sales", "Profit", "Gross Margin %", "Profit per Unit",
            "Revenue Contribution %", "Profit Contribution %"]
    st.subheader("Product margin leaderboard")
    sort = st.selectbox("Rank by", ["Profit", "Gross Margin %", "Sales", "Profit per Unit"])
    board = flags.sort_values(sort, ascending=False)
    st.dataframe(board[show].round(2))
    left, right = st.columns(2)
    left.plotly_chart(px.bar(board.sort_values("Profit"), x="Profit", y="Product Name", orientation="h",
                             color="Division", title="Profit contribution by product"))
    right.plotly_chart(px.bar(board.sort_values("Gross Margin %"), x="Gross Margin %", y="Product Name",
                              orientation="h", color="Division", title="Gross margin % by product"))
    q = an.quadrant(pt, thr)
    st.subheader("Product quadrants")
    st.caption("High/low sales = above/below the median product sales; high/low margin = above/below the threshold.")
    st.dataframe(q[["Product Name", "Quadrant", "Sales", "Gross Margin %"]].sort_values("Quadrant").round(2))
    st.download_button("Download product table (CSV)", flags.to_csv(index=False).encode(),
                       "product_profitability.csv", "text/csv")

# ---------------- 2. Division performance ----------------
with tabs[1]:
    dv = an.division_table(df)
    left, right = st.columns(2)
    long = dv.melt(id_vars="Division", value_vars=["Sales", "Profit"], var_name="Measure", value_name="USD")
    left.plotly_chart(px.bar(long, x="Division", y="USD", color="Measure", barmode="group",
                             title="Revenue vs profit by division"))
    right.plotly_chart(px.box(df, x="Division", y="Gross Margin %", color="Division",
                              title="Margin distribution by division (order lines)"))
    st.dataframe(dv.round(2))
    weak = dv[dv["Gross Margin %"] < thr]
    if len(weak):
        st.warning("Division(s) below the margin threshold: " + ", ".join(weak.Division))
    st.caption("Sugar has very few rows, so its results are statistically weak.")

# ---------------- 3. Cost vs margin diagnostics ----------------
with tabs[2]:
    fl = an.margin_flags(pt, thr)
    fig = px.scatter(fl, x="Cost", y="Sales", size="Units", color="Division", hover_name="Product Name",
                     title="Cost vs sales by product (bubble size = units)")
    top = max(fl.Cost.max(), fl.Sales.max())
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", name="Break-even (sales = cost)"))
    st.plotly_chart(fig)
    st.subheader("Margin risk flags")
    risk = fl[fl.Flag != "OK"]
    if risk.empty:
        st.success("No products fall below the margin threshold.")
    else:
        st.dataframe(risk[["Product Name", "Division", "Sales", "Profit", "Gross Margin %",
                           "Cost % of Sales", "Profit Contribution %", "Flag"]].round(2))
        st.info("Rules: margin under 20% = urgent repricing / cost renegotiation; under the threshold = repricing "
                "review; profit contribution under 0.1% adds a discontinuation review. Rule-based, not a forecast.")
    pick = st.selectbox("Price needed to hit the threshold margin", fl["Product Name"])
    r = fl[fl["Product Name"] == pick].iloc[0]
    u_cost = r.Cost / r.Units
    if thr < 100:
        st.write(f"Unit cost {u_cost:.2f}; unit price {r.Sales / r.Units:.2f}; price for a {thr}% margin "
                 f"at this cost = **{u_cost / (1 - thr / 100):.2f}**.")

# ---------------- 4. Profit concentration ----------------
with tabs[3]:
    dep = an.dependency(pt)
    c = st.columns(4)
    c[0].metric("Products for 80% of revenue", f"{dep['products_for_80_revenue']} of {dep['products']}")
    c[1].metric("Products for 80% of profit", f"{dep['products_for_80_profit']} of {dep['products']}")
    c[2].metric("Top-5 profit share", f"{dep['top5_profit_share']:.2f}%")
    c[3].metric("Profit HHI", f"{dep['profit_hhi']:,.0f}", help="Above 2,500 = highly concentrated; 1,500-2,500 = moderate")
    by = st.radio("Pareto by", ["Profit", "Sales"], horizontal=True)
    pr = an.pareto(pt, by)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=pr["Product Name"], y=pr[by], name=by))
    fig.add_trace(go.Scatter(x=pr["Product Name"], y=pr["Cumulative %"], name="Cumulative %", yaxis="y2", mode="lines+markers"))
    fig.update_layout(title=f"Pareto of {by.lower()} by product", yaxis2=dict(overlaying="y", side="right", range=[0, 105]))
    st.plotly_chart(fig)
    if dep["products"] > 5 and dep["top5_profit_share"] > 80:
        st.warning(f"High dependency risk: the top 5 products produce {dep['top5_profit_share']:.1f}% of profit.")
    st.dataframe(pr[["Rank", "Product Name", by, "Cumulative %", "In top 80%"]].round(2))

# ---------------- 5. Margin over time ----------------
with tabs[4]:
    mm = an.monthly_margin(df)
    st.plotly_chart(px.line(mm, x="Order Month", y="Margin %", markers=True,
                            title="Overall monthly gross margin (%) - varies only through product mix"))
    sd, per = an.margin_volatility(df)
    st.metric("Monthly margin volatility (std-dev, points)", f"{sd:.2f}")
    st.dataframe(per)
    st.info("Product-level margin volatility is zero because each product has a fixed unit price and cost.")

# ---------------- 6. Data quality ----------------
with tabs[5]:
    st.subheader("Data quality notes")
    for note in notes:
        st.write("•", note)
