"""Checks the headline numbers against the dataset. Run from the repo root: pytest -q"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analytics as an  # noqa: E402

DATA = ROOT / "data" / "Nassau_Candy_Distributor.csv"


def _load(**kw):
    return an.load_candy(DATA, **kw)


def test_overall_numbers():
    df, _ = _load()
    o = an.overall(df)
    assert o["Rows"] == 10194 and df["Product Name"].nunique() == 15 and df.Division.nunique() == 3
    assert round(o["Sales"], 2) == 141783.63 and round(o["Profit"], 2) == 93442.80
    assert round(o["Gross Margin %"], 2) == 65.91 and round(o["Profit per Unit"], 2) == 2.42
    assert (df["Sales"] - df["Cost"] - df["Gross Profit"]).abs().max() < 0.02


def test_products_pareto_and_flags():
    df, _ = _load()
    pt = an.product_table(df)
    dep = an.dependency(pt)
    assert dep["products_for_80_revenue"] == 5 and dep["products_for_80_profit"] == 5
    assert round(dep["top5_profit_share"], 2) == 95.06
    kz = pt[pt["Product Name"] == "Kazookles"].iloc[0]
    assert round(kz["Gross Margin %"], 2) == 7.69 and kz["Rows"] == 96 and round(kz["Profit per Unit"], 2) == 0.25
    flags = an.margin_flags(pt, 50).set_index("Product Name")["Flag"]
    assert "urgent" in flags["Kazookles"] and "Discontinuation" in flags["Kazookles"]
    assert flags["Wonka Bar - Milk Chocolate"] == "OK"
    q = an.quadrant(pt, 50).set_index("Product Name")["Quadrant"]
    assert q["Kazookles"] == "High sales / low margin"


def test_divisions():
    df, _ = _load()
    dv = an.division_table(df).set_index("Division")
    assert round(dv.loc["Chocolate", "Gross Margin %"], 2) == 67.45
    assert round(dv.loc["Other", "Gross Margin %"], 2) == 44.97
    raw, _ = _load(fizzy_to_other=False)
    assert round(an.division_table(raw).set_index("Division").loc["Other", "Gross Margin %"], 2) == 44.84


def test_data_quality_flags():
    df, notes = _load()
    assert not df["Ship Date Valid"].any() and df["Ship Lag Days"].min() == 904 and df["Ship Lag Days"].max() == 1642
    assert df["OrderID Year Mismatch"].all()
    assert any("WARNING" in n for n in notes)
    sd, per = an.margin_volatility(df)
    assert per["Monthly margin std (pts)"].max() < 1e-6      # fixed price and cost per product
    assert 0.4 < sd < 0.7 and round(an.monthly_margin(df)["Margin %"].min(), 2) == 64.54
