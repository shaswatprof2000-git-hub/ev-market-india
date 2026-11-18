"""
India EV Market Study - answers to the 10 primary research questions
====================================================================

Runs on the cleaned files in data/cleaned/ and writes:
    analysis/PRIMARY_ANSWERS.md     readable answers (use to cross-check Power BI)
    analysis/q01_... .. q10_... csv one table per question

Usage (from the repo root, after clean_data.py):
    python scripts/analysis.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FY = "fiscal_year"


def load(clean: Path):
    d = pd.read_csv(clean / "dim_date.csv", parse_dates=["date"])
    s = pd.read_csv(clean / "fact_state_sales.csv", parse_dates=["date"]).merge(d, on="date")
    m = pd.read_csv(clean / "fact_maker_sales.csv", parse_dates=["date"]).merge(d, on="date")
    c = pd.read_csv(clean / "dim_vehicle_category.csv")
    return s, m, c


def cagr(end, start, years):
    return (end / start) ** (1 / years) - 1


def pct(x, nd=2):
    return f"{x * 100:.{nd}f}%"


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(out)


def penetration(df, by):
    g = df.groupby(by)[["electric_vehicles_sold", "total_vehicles_sold"]].sum()
    g["penetration"] = g["electric_vehicles_sold"] / g["total_vehicles_sold"]
    return g


def run(clean: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    s, m, cat = load(clean)
    md = ["# Primary Research Questions - Answers", "",
          "Computed by `scripts/analysis.py` from `data/cleaned/`. Fiscal years run April-March "
          "(FY2024 = Apr-2023 to Mar-2024). Penetration = EV sold / total vehicles sold.", ""]

    def section(n, title, table, note=""):
        table.to_csv(out / f"q{n:02d}.csv", index=False)
        md.extend([f"## Q{n}. {title}", "", md_table(table), ""])
        if note:
            md.extend([note, ""])

    # Q1 ------------------------------------------------------------------
    w2 = m[(m.vehicle_category == "2-Wheelers") & (~m.is_others_bucket)]
    rows = []
    for fy in (2023, 2024):
        t = w2[w2[FY] == fy].groupby("maker").electric_vehicles_sold.sum()
        t = t[t > 0].sort_values(ascending=False)
        for rank, (mk, v) in enumerate(t.head(3).items(), 1):
            rows.append(dict(fiscal_year=f"FY{fy}", group="Top 3", rank=rank, maker=mk, units=f"{v:,}"))
        for rank, (mk, v) in enumerate(t.tail(3)[::-1].items(), 1):
            rows.append(dict(fiscal_year=f"FY{fy}", group="Bottom 3", rank=rank, maker=mk, units=f"{v:,}"))
    section(1, "Top 3 and bottom 3 makers (2-wheelers), FY2023 and FY2024", pd.DataFrame(rows),
            "'Others' bucket excluded. Bottom 3 is among makers listed in that year; the source "
            "lists a different set of small makers in FY2024 (BGauss, Battre, Kinetic Green) than in FY2023.")

    # Q2 ------------------------------------------------------------------
    p24 = penetration(s[s[FY] == 2024], ["vehicle_category", "state"]).reset_index()
    rows = []
    for c in ("2-Wheelers", "4-Wheelers"):
        t = p24[p24.vehicle_category == c].nlargest(5, "penetration")
        for rank, r in enumerate(t.itertuples(), 1):
            rows.append(dict(category=c, rank=rank, state=r.state, ev_sold=f"{r.electric_vehicles_sold:,}",
                             total_sold=f"{r.total_vehicles_sold:,}", penetration=pct(r.penetration)))
    section(2, "Top 5 states by EV penetration in FY2024", pd.DataFrame(rows),
            "Kerala 4W uses the corrected Jan-2024 total (see reports/DATA_CLEANING_REPORT.md); "
            "with the raw value Kerala's 4W FY2024 penetration would be overstated.")

    # Q3 ------------------------------------------------------------------
    pc = penetration(s, ["state", "vehicle_category", FY])["penetration"].unstack()
    po = penetration(s, ["state", FY])["penetration"].unstack()
    po["vehicle_category"] = "All (2W + 4W)"
    po = po.set_index("vehicle_category", append=True)
    allp = pd.concat([pc, po])
    dec = allp[allp[2024] < allp[2022]].copy()
    dec["change_pp"] = (dec[2024] - dec[2022]) * 100
    t = dec.reset_index().rename(columns={2022: "FY2022", 2023: "FY2023", 2024: "FY2024"})
    for c in ("FY2022", "FY2023", "FY2024"):
        t[c] = t[c].map(pct)
    t["change_pp"] = t["change_pp"].map(lambda x: f"{x:+.2f} pp")
    t = t[["state", "vehicle_category", "FY2022", "FY2023", "FY2024", "change_pp"]]
    n_all = (dec.index.get_level_values("vehicle_category") == "All (2W + 4W)").sum()
    note = ("No state declined on a combined 2W + 4W basis. " if n_all == 0 else
            f"{n_all} state(s) declined on a combined 2W + 4W basis. ")
    note += ("The category-level declines are in very small markets (monthly totals in the hundreds), "
             "so treat them as noise-prone rather than a trend.")
    section(3, "States with declining EV penetration, FY2022 -> FY2024", t, note)

    # Q4 ------------------------------------------------------------------
    w4 = m[m.vehicle_category == "4-Wheelers"]
    top5_4w = w4.groupby("maker").electric_vehicles_sold.sum().nlargest(5).index.tolist()
    q = (w4[w4.maker.isin(top5_4w)].groupby(["fy_quarter", "maker"]).electric_vehicles_sold.sum()
         .unstack()[top5_4w].reset_index())
    q.to_csv(out / "q04_quarterly_long.csv", index=False)
    for c in top5_4w:
        q[c] = q[c].map(lambda v: f"{int(v):,}")
    section(4, "Quarterly sales, top 5 4-wheeler EV makers (FY2022-FY2024)", q,
            f"Top 5 by total FY2022-24 4W EV units: {', '.join(top5_4w)}.")

    # Q5 ------------------------------------------------------------------
    dk = s[(s[FY] == 2024) & s.state.isin(["Delhi", "Karnataka"])]
    a = penetration(dk, ["state", "vehicle_category"]).reset_index()
    b = penetration(dk, ["state"]).reset_index().assign(vehicle_category="All (2W + 4W)")
    t = pd.concat([a, b]).sort_values(["vehicle_category", "state"])
    t = t.assign(ev_sold=t.electric_vehicles_sold.map("{:,}".format),
                 total_sold=t.total_vehicles_sold.map("{:,}".format),
                 penetration=t.penetration.map(pct))[["vehicle_category", "state", "ev_sold", "total_sold", "penetration"]]
    section(5, "Delhi vs Karnataka, FY2024", t)

    # Q6 ------------------------------------------------------------------
    f = w4[w4[FY].isin([2022, 2024])].groupby(["maker", FY]).electric_vehicles_sold.sum().unstack()
    f = f.loc[top5_4w]
    f["cagr"] = cagr(f[2024], f[2022], 2)
    t = f.reset_index().rename(columns={2022: "FY2022 units", 2024: "FY2024 units"})
    t["FY2022 units"] = t["FY2022 units"].map("{:,}".format)
    t["FY2024 units"] = t["FY2024 units"].map("{:,}".format)
    t["cagr"] = t["cagr"].map(lambda x: pct(x, 1))
    section(6, "CAGR of 4-wheeler EV units, top 5 makers, FY2022 -> FY2024", t,
            "CAGR = (FY2024 / FY2022)^(1/2) - 1. Top 5 = same five makers as Q4.")

    # Q7 ------------------------------------------------------------------
    tv = s.groupby(["state", FY]).total_vehicles_sold.sum().unstack()
    tv["cagr"] = cagr(tv[2024], tv[2022], 2)
    t = tv.nlargest(10, "cagr").reset_index()
    t.insert(0, "rank", range(1, len(t) + 1))
    t = t.assign(**{"FY2022": t[2022].map("{:,}".format), "FY2024": t[2024].map("{:,}".format),
                    "cagr": t["cagr"].map(lambda x: pct(x, 1))})[["rank", "state", "FY2022", "FY2024", "cagr"]]
    section(7, "Top 10 states by CAGR in total vehicles sold, FY2022 -> FY2024", t,
            "Total vehicles = EV + non-EV, both categories. Source gaps: Odisha's FY2024 is missing "
            "March-2024 (CAGR understated); Andaman & Nicobar's FY2022 is missing June-2021 4W "
            "(CAGR slightly overstated).")

    # Q8 ------------------------------------------------------------------
    mo = s.groupby(["fiscal_month_num", "month_name"]).electric_vehicles_sold.sum().reset_index()
    tot = mo.electric_vehicles_sold.sum()
    mo["share_of_3yr_sales"] = (mo.electric_vehicles_sold / tot).map(lambda x: pct(x, 1))
    by_year = s.groupby(["month_name", FY]).electric_vehicles_sold.sum().unstack()
    mo = mo.merge(by_year, left_on="month_name", right_index=True)
    peak = mo.nlargest(3, "electric_vehicles_sold").month_name.tolist()
    low = mo.nsmallest(3, "electric_vehicles_sold").month_name.tolist()
    t = mo.rename(columns={2022: "FY2022", 2023: "FY2023", 2024: "FY2024",
                           "electric_vehicles_sold": "ev_sold_3yr"}).drop(columns="fiscal_month_num")
    for c in ("ev_sold_3yr", "FY2022", "FY2023", "FY2024"):
        t[c] = t[c].map("{:,}".format)
    section(8, "Peak and low months for EV sales (FY2022-FY2024 combined)", t,
            f"Peak months: {', '.join(peak)}. Low months: {', '.join(low)}. "
            "March benefits from fiscal-year-end buying; April-June FY2022 was hit by the COVID-19 second wave.")

    # Q9 ------------------------------------------------------------------
    po24 = penetration(s[s[FY] == 2024], ["state"])
    top10 = po24.nlargest(10, "penetration").index
    ev = s[s.state.isin(top10)].groupby(["state", FY]).electric_vehicles_sold.sum().unstack()
    ev["cagr_22_24"] = cagr(ev[2024], ev[2022], 2)
    ev["projected_fy2030"] = ev[2024] * (1 + ev["cagr_22_24"]) ** 6
    ev["penetration_fy2024"] = po24.loc[ev.index, "penetration"]
    ev = ev.loc[top10].reset_index()
    t = pd.DataFrame({
        "state": ev.state,
        "penetration_fy2024": ev.penetration_fy2024.map(pct),
        "ev_fy2022": ev[2022].map("{:,}".format),
        "ev_fy2024": ev[2024].map("{:,}".format),
        "cagr_22_24": ev.cagr_22_24.map(lambda x: pct(x, 1)),
        "projected_ev_fy2030": ev.projected_fy2030.map(lambda x: f"{x:,.0f}"),
    })
    section(9, "Projected FY2030 EV sales, top 10 states by FY2024 penetration", t,
            "Projection = FY2024 EV units x (1 + CAGR FY22->24)^6. Two years of very high early-adoption "
            "growth compounded over six more years gives unrealistically large numbers; present this as "
            "the mechanical answer the question asks for and pair it with a capped-growth scenario in the deck.")

    # Q10 -----------------------------------------------------------------
    price = cat.set_index("vehicle_category").avg_unit_price_inr
    units = s.groupby(["vehicle_category", FY]).electric_vehicles_sold.sum().unstack()
    rev = units.mul(price, axis=0)
    rev.loc["Total (2W + 4W)"] = rev.sum()
    rows = []
    for c, r in rev.iterrows():
        rows.append(dict(category=c,
                         **{f"revenue FY{y} (Rs crore)": f"{r[y] / 1e7:,.0f}" for y in (2022, 2023, 2024)},
                         **{"growth FY22->FY24": pct(r[2024] / r[2022] - 1, 1),
                            "growth FY23->FY24": pct(r[2024] / r[2023] - 1, 1)}))
    section(10, "Estimated EV revenue growth (assumed average unit price)", pd.DataFrame(rows),
            f"Assumed prices: 2W Rs {price['2-Wheelers']:,}, 4W Rs {price['4-Wheelers']:,} "
            "(change in data/cleaned/dim_vehicle_category.csv). With a fixed price, revenue growth per "
            "category equals unit growth. 1 crore = 10 million.")

    (out / "PRIMARY_ANSWERS.md").write_text("\n".join(md), encoding="utf-8")
    print("Wrote", out / "PRIMARY_ANSWERS.md")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--clean", type=Path, default=ROOT / "data" / "cleaned")
    p.add_argument("--out", type=Path, default=ROOT / "analysis")
    a = p.parse_args()
    run(a.clean, a.out)
