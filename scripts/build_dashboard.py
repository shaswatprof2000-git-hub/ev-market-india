"""
Builds a dashboard that GitHub renders directly (no Power BI needed):

    dashboard/*.png   one chart per question
    DASHBOARD.md      charts + answers, opens on github.com

Usage (from the repo root, after clean_data.py):
    python scripts/build_dashboard.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLEAN, OUT = ROOT / "data" / "cleaned", ROOT / "dashboard"
FY = "fiscal_year"

# Validated categorical palette (light mode): fixed slot order, never cycled.
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
CAT = {"2-Wheelers": SLOTS[0], "4-Wheelers": SLOTS[1]}  # category colour follows the entity everywhere
ALL = "#474641"        # single-series "all categories" ink
MUTED = "#c9c8c2"      # de-emphasised marks
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e7e6e2"

plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"], "font.size": 10, "axes.titlesize": 12.5,
    "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.titlepad": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False,
    "lines.linewidth": 2, "figure.dpi": 150,
})


def load():
    d = pd.read_csv(CLEAN / "dim_date.csv", parse_dates=["date"])
    s = pd.read_csv(CLEAN / "fact_state_sales.csv", parse_dates=["date"]).merge(d, on="date")
    m = pd.read_csv(CLEAN / "fact_maker_sales.csv", parse_dates=["date"]).merge(d, on="date")
    c = pd.read_csv(CLEAN / "dim_vehicle_category.csv")
    return s, m, c


def pen(df, by):
    g = df.groupby(by)[["electric_vehicles_sold", "total_vehicles_sold"]].sum()
    return g["electric_vehicles_sold"] / g["total_vehicles_sold"]


def cagr(end, start, n=2):
    return (end / start) ** (1 / n) - 1


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return f"dashboard/{name}"


def hbar(ax, labels, values, colors, fmt, title=None):
    y = range(len(labels))[::-1]
    ax.barh(list(y), values, color=colors, height=0.62, edgecolor=SURFACE, linewidth=2)
    ax.set_yticks(list(y), labels)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: fmt(v)))
    vmax = max(values)
    for yi, v in zip(y, values):
        ax.text(v + vmax * 0.015, yi, fmt(v), va="center", fontsize=9, color=INK)
    ax.set_xlim(0, vmax * 1.18)
    if title:
        ax.set_title(title)


def p1(x, _=None):
    return f"{x * 100:.1f}%"


def p0(x, _=None):
    return f"{x * 100:.0f}%"


def n0(x, _=None):
    return f"{x:,.0f}"


def mn(x, _=None):
    return f"{x / 1e6:.1f}M" if x >= 1e6 else (f"{x / 1e3:.0f}K" if x else "0")


def build():
    OUT.mkdir(exist_ok=True)
    s, m, cat = load()
    md, charts = [], {}

    # ---- KPIs
    by_fy = s.groupby(FY)[["electric_vehicles_sold", "total_vehicles_sold"]].sum()
    by_fy["pen"] = by_fy.iloc[:, 0] / by_fy.iloc[:, 1]

    # ---- Overview: small multiples (units, then penetration by category)
    mon = s.groupby("date")["electric_vehicles_sold"].sum()
    pmon = pen(s, ["date", "vehicle_category"]).unstack()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True, gridspec_kw={"hspace": 0.35})
    a1.plot(mon.index, mon.values, color=ALL)
    a1.yaxis.set_major_formatter(mtick.FuncFormatter(mn))
    a1.set_title("Monthly EV units sold: annual volume nearly quadrupled, FY2022 to FY2024")
    a1.annotate(f"Mar-2024: {mon.iloc[-1]:,.0f}", (mon.index[-1], mon.iloc[-1]), xytext=(-110, 0),
                textcoords="offset points", va="center", fontsize=9, color=INK2)
    for c in pmon.columns:
        a2.plot(pmon.index, pmon[c], color=CAT[c], label=c)
        a2.annotate(f"{c} {pmon[c].iloc[-1] * 100:.1f}%", (pmon.index[-1], pmon[c].iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
    a2.yaxis.set_major_formatter(mtick.FuncFormatter(p0))
    a2.set_title("EV penetration: two-wheelers lead, four-wheelers are catching up")
    a2.legend(loc="upper left", ncols=2)
    charts["overview"] = save(fig, "00_overview.png")

    # ---- Q1
    w2 = m[(m.vehicle_category == "2-Wheelers") & (m.maker != "Others")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"wspace": 0.55})
    q1 = {}
    for ax, fy in zip(axes, (2023, 2024)):
        t = w2[w2[FY] == fy].groupby("maker").electric_vehicles_sold.sum()
        t = t[t > 0].sort_values(ascending=False)
        top, bot = t.index[:3].tolist(), t.index[-3:].tolist()
        q1[fy] = (top, bot, t)
        colors = [SLOTS[0] if k in top else SLOTS[1] if k in bot else MUTED for k in t.index]
        hbar(ax, t.index.tolist(), t.values.tolist(), colors, mn, f"FY{fy}")
    fig.suptitle("Q1  2-wheeler makers: top 3 (blue) and bottom 3 (orange)", x=0.02, ha="left",
                 fontweight="semibold", fontsize=12.5, y=1.02)
    charts["q1"] = save(fig, "q01_2w_makers.png")

    # ---- Q2
    p24 = pen(s[s[FY] == 2024], ["vehicle_category", "state"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={"wspace": 0.5})
    q2 = {}
    for ax, c in zip(axes, ("2-Wheelers", "4-Wheelers")):
        t = p24[c].nlargest(5)
        q2[c] = t
        hbar(ax, t.index.tolist(), t.values.tolist(), [CAT[c]] * 5, p1, c)
    fig.suptitle("Q2  Top 5 states by EV penetration, FY2024", x=0.02, ha="left",
                 fontweight="semibold", fontsize=12.5, y=1.04)
    charts["q2"] = save(fig, "q02_top_states_penetration.png")

    # ---- Q4 + Q6 (same maker -> same colour)
    w4 = m[m.vehicle_category == "4-Wheelers"]
    top5 = w4.groupby("maker").electric_vehicles_sold.sum().nlargest(5).index.tolist()
    mcol = dict(zip(top5, SLOTS))
    q = w4[w4.maker.isin(top5)].groupby(["fy_quarter", "maker"]).electric_vehicles_sold.sum().unstack()[top5]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = range(len(q))
    for mk in top5:
        ax.plot(list(x), q[mk].values, color=mcol[mk], marker="o", markersize=4, label=mk)
    for mk in top5[:2]:  # selective direct labels: only the two lines that separate cleanly
        ax.annotate(f"{q[mk].iloc[-1]:,.0f}", (len(q) - 1, q[mk].iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=INK)
    ax.set_xticks(list(x), [i.replace("FY20", "FY") for i in q.index], rotation=0, fontsize=8.5)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(n0))
    ax.set_xlim(-0.3, len(q) - 0.2)
    ax.set_title("Q4  Quarterly 4W EV units, top 5 makers: Tata pulls away; Mahindra peaked in FY24-Q1",
                 pad=34)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=5, fontsize=9)
    charts["q4"] = save(fig, "q04_4w_makers_quarterly.png")

    f = w4[w4[FY].isin([2022, 2024])].groupby(["maker", FY]).electric_vehicles_sold.sum().unstack().loc[top5]
    f["cagr"] = cagr(f[2024], f[2022])
    f6 = f.sort_values("cagr", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 3.2))
    hbar(ax, f6.index.tolist(), f6["cagr"].tolist(), [mcol[k] for k in f6.index], p0,
         "Q6  CAGR of 4W EV units FY2022 to FY2024, top 5 makers")
    charts["q6"] = save(fig, "q06_4w_makers_cagr.png")

    # ---- Q5
    dk = s[(s[FY] == 2024) & s.state.isin(["Delhi", "Karnataka"])]
    p5 = pen(dk, ["vehicle_category", "state"]).unstack()
    p5.loc["All (2W + 4W)"] = pen(dk, ["state"])
    u5 = dk.groupby(["vehicle_category", "state"]).electric_vehicles_sold.sum().unstack()
    u5.loc["All (2W + 4W)"] = dk.groupby("state").electric_vehicles_sold.sum()
    scol = {"Delhi": SLOTS[6], "Karnataka": SLOTS[2]}
    fig, ax = plt.subplots(figsize=(10, 3.6))
    w, xs = 0.36, range(len(p5))
    for i, st in enumerate(["Delhi", "Karnataka"]):
        xx = [v + (i - 0.5) * w for v in xs]
        ax.bar(xx, p5[st], width=w, color=scol[st], label=st, edgecolor=SURFACE, linewidth=2)
        for xi, v in zip(xx, p5[st]):
            ax.text(xi, v + 0.002, p1(v), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(list(xs), p5.index)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(p0))
    ax.set_ylim(0, p5.values.max() * 1.3)
    ax.legend(loc="upper center", ncols=2)
    ax.set_title("Q5  Delhi vs Karnataka, FY2024 EV penetration")
    charts["q5"] = save(fig, "q05_delhi_vs_karnataka.png")

    # ---- Q7
    tv = s.groupby(["state", FY]).total_vehicles_sold.sum().unstack()
    tv["cagr"] = cagr(tv[2024], tv[2022])
    t7 = tv.nlargest(10, "cagr")
    fig, ax = plt.subplots(figsize=(10, 4.2))
    hbar(ax, t7.index.tolist(), t7["cagr"].tolist(), [ALL] * 10, p1,
         "Q7  Top 10 states by CAGR in total vehicles sold, FY2022 to FY2024")
    charts["q7"] = save(fig, "q07_states_total_cagr.png")

    # ---- Q8
    mo = s.groupby(["fiscal_month_num", "month_short"]).electric_vehicles_sold.sum().reset_index()
    mo["share"] = mo.electric_vehicles_sold / mo.electric_vehicles_sold.sum()
    peak = mo.nlargest(3, "share").month_short.tolist()
    low = mo.nsmallest(3, "share").month_short.tolist()
    colors = [SLOTS[0] if k in peak else SLOTS[1] if k in low else MUTED for k in mo.month_short]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.bar(mo.month_short, mo.share, color=colors, width=0.62, edgecolor=SURFACE, linewidth=2)
    for xi, (k, v) in enumerate(zip(mo.month_short, mo.share)):
        if k in peak or k in low:
            ax.text(xi, v + 0.002, p1(v), ha="center", va="bottom", fontsize=9)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(p0))
    ax.set_title(f"Q8  Share of FY2022-24 EV sales by month: peaks {', '.join(peak)} (blue); "
                 f"lows {', '.join(low)} (orange)")
    charts["q8"] = save(fig, "q08_seasonality.png")

    # ---- Q9
    po24 = pen(s[s[FY] == 2024], ["state"])
    top10 = po24.nlargest(10).index
    ev = s[s.state.isin(top10)].groupby(["state", FY]).electric_vehicles_sold.sum().unstack()
    ev["cagr"] = cagr(ev[2024], ev[2022])
    ev["proj"] = ev[2024] * (1 + ev["cagr"]) ** 6
    ev["pen"] = po24
    ev = ev.loc[top10]
    e9 = ev.sort_values("proj", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    hbar(ax, e9.index.tolist(), e9["proj"].tolist(), [ALL] * 10, mn,
         "Q9  Projected FY2030 EV units, top 10 states by FY2024 penetration (CAGR-based)")
    charts["q9"] = save(fig, "q09_projection_2030.png")

    # ---- Q10
    price = cat.set_index("vehicle_category").avg_unit_price_inr
    units = s.groupby(["vehicle_category", FY]).electric_vehicles_sold.sum().unstack()
    rev = units.mul(price, axis=0) / 1e7
    fig, ax = plt.subplots(figsize=(10, 3.6))
    w, xs = 0.36, range(3)
    for i, c in enumerate(rev.index):
        xx = [v + (i - 0.5) * w for v in xs]
        ax.bar(xx, rev.loc[c], width=w, color=CAT[c], label=c, edgecolor=SURFACE, linewidth=2)
        for xi, v in zip(xx, rev.loc[c]):
            ax.text(xi, v + 150, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(list(xs), [f"FY{y}" for y in rev.columns])
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(n0))
    ax.set_ylabel("Rs crore")
    ax.legend(loc="upper left", ncols=2)
    ax.set_title("Q10  Estimated EV revenue (Rs crore): 4W out-earns 2W every year, and the gap widened")
    charts["q10"] = save(fig, "q10_revenue.png")

    # ---- Markdown
    def tbl(rows, header):
        return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
                         + ["| " + " | ".join(map(str, r)) + " |" for r in rows])

    t = by_fy
    md += [
        "# India EV Market Study: Dashboard",
        "",
        "AtliQ Motors India market study, FY2022 to FY2024 (fiscal year = April to March). "
        "Source: Vahan registrations, cleaned with `scripts/clean_data.py`. "
        "Interactive version: `powerbi/EV_Market_Study.pbip` (see [POWERBI_GUIDE.md](POWERBI_GUIDE.md)).",
        "",
        tbl([[f"FY{fy}", f"{int(r.electric_vehicles_sold):,}", f"{int(r.total_vehicles_sold):,}",
              f"{r.pen * 100:.2f}%"]
             for fy, r in t.iterrows()], ["Fiscal year", "EV units", "All vehicles", "EV penetration"]),
        "",
        f"![Overview]({charts['overview']})",
        "",
        "## Q1. Top 3 and bottom 3 two-wheeler makers",
        "",
        f"![Q1]({charts['q1']})",
        "",
        tbl([[f"FY{fy}", ", ".join(q1[fy][0]), ", ".join(q1[fy][1][::-1])] for fy in (2023, 2024)],
            ["Year", "Top 3 (high to low)", "Bottom 3 (low to high)"]),
        "",
        "'Others' excluded. Ola Electric leads both years; TVS and Ather replaced Okinawa and Hero Electric in FY2024.",
        "",
        "## Q2. Top 5 states by EV penetration, FY2024",
        "",
        f"![Q2]({charts['q2']})",
        "",
        tbl([[i + 1, q2['2-Wheelers'].index[i], p1(q2['2-Wheelers'].iloc[i]),
              q2['4-Wheelers'].index[i], p1(q2['4-Wheelers'].iloc[i])] for i in range(5)],
            ["Rank", "2W state", "2W penetration", "4W state", "4W penetration"]),
        "",
        "## Q3. States with declining penetration, FY2022 to FY2024",
        "",
        "No state declined on a combined 2W + 4W basis. Within one category, two very small markets slipped: "
        "**Ladakh 2W** (4.48% to 4.06%) and **Andaman & Nicobar 4W** (1.88% to 0.77%). "
        "Their monthly volumes are in the hundreds, so treat this as noise rather than a trend.",
        "",
        "## Q4. Quarterly trend, top 5 four-wheeler makers",
        "",
        f"![Q4]({charts['q4']})",
        "",
        "## Q5. Delhi vs Karnataka, FY2024",
        "",
        f"![Q5]({charts['q5']})",
        "",
        tbl([[c, f"{u5.loc[c, 'Delhi']:,}", p1(p5.loc[c, 'Delhi']), f"{u5.loc[c, 'Karnataka']:,}",
              p1(p5.loc[c, 'Karnataka'])] for c in p5.index],
            ["Category", "Delhi EV units", "Delhi penetration", "Karnataka EV units", "Karnataka penetration"]),
        "",
        "Karnataka sells 3.4x Delhi's EV volume and leads on 2W penetration; 4W penetration is level.",
        "",
        "## Q6. CAGR of 4W units, top 5 makers, FY2022 to FY2024",
        "",
        f"![Q6]({charts['q6']})",
        "",
        tbl([[k, f"{int(r[2022]):,}", f"{int(r[2024]):,}", p1(r.cagr)] for k, r in f6.iterrows()],
            ["Maker", "FY2022 units", "FY2024 units", "CAGR"]),
        "",
        "## Q7. Top 10 states by CAGR in total vehicles sold",
        "",
        f"![Q7]({charts['q7']})",
        "",
        "Odisha's FY2024 lacks March-2024 in the source data, so its CAGR is understated.",
        "",
        "## Q8. Peak and low months",
        "",
        f"![Q8]({charts['q8']})",
        "",
        f"Peak: **{', '.join(peak)}** (fiscal year-end buying, festive season). "
        f"Low: **{', '.join(low)}** (start of the fiscal year; FY2022 was also hit by the COVID-19 second wave).",
        "",
        "## Q9. Projected FY2030 EV sales, top 10 states by penetration",
        "",
        f"![Q9]({charts['q9']})",
        "",
        tbl([[k, p1(r.pen), f"{int(r[2024]):,}", p0(r.cagr), f"{r.proj:,.0f}"] for k, r in ev.iterrows()],
            ["State", "Penetration FY2024", "EV units FY2024", "CAGR FY22-24", "Projected FY2030"]),
        "",
        "Projection = FY2024 units x (1 + CAGR)^6. Early-adoption growth rates will not hold for six more "
        "years, so read this as an upper bound.",
        "",
        "## Q10. Estimated revenue growth",
        "",
        f"![Q10]({charts['q10']})",
        "",
        tbl([[c, f"{rev.loc[c, 2022]:,.0f}", f"{rev.loc[c, 2023]:,.0f}", f"{rev.loc[c, 2024]:,.0f}",
              p0(rev.loc[c, 2024] / rev.loc[c, 2022] - 1), p0(rev.loc[c, 2024] / rev.loc[c, 2023] - 1)]
             for c in rev.index],
            ["Category", "FY2022 (Rs cr)", "FY2023 (Rs cr)", "FY2024 (Rs cr)", "Growth FY22-24", "Growth FY23-24"]),
        "",
        f"Assumed average price: 2W Rs {price['2-Wheelers']:,}, 4W Rs {price['4-Wheelers']:,}.",
        "",
        "---",
        "Full tables: [analysis/PRIMARY_ANSWERS.md](analysis/PRIMARY_ANSWERS.md) · "
        "Cleaning log: [reports/DATA_CLEANING_REPORT.md](reports/DATA_CLEANING_REPORT.md)",
        "",
    ]
    (ROOT / "DASHBOARD.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote DASHBOARD.md and {len(charts)} charts to {OUT}")


if __name__ == "__main__":
    build()
