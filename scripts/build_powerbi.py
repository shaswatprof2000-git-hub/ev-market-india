"""
Builds the Power BI hand-off from the cleaned data:

    powerbi/EV_Market_Study.pbip                 open this in Power BI Desktop (Windows)
    powerbi/EV_Market_Study.SemanticModel/       tables, relationships, DAX measures
    powerbi/EV_Market_Study.Report/              5-page dashboard, visuals pre-built (Q1-Q10)
    powerbi/EV_Market_Study_EmptyReport.pbip     same model, blank pages (fallback)
    powerbi/measures.dax                         every measure, for copy-paste / manual build

The semantic model loads the CSVs through a Power Query parameter `DataFolder`, which
defaults to this repo's data/cleaned/ folder on GitHub (raw URLs), so the project works
from any folder. Point it at a local folder in Transform data > Edit parameters.

Usage (from the repo root):
    python scripts/build_powerbi.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "cleaned"
OUT = ROOT / "powerbi"
NAME = "EV_Market_Study"
# Data loads straight from the public GitHub repo, so the .pbip works from any folder.
# To use local files instead, set DataFolder to e.g. C:\ev-market-india\data\cleaned\
DEFAULT_FOLDER = "https://raw.githubusercontent.com/shaswatprof2000-git-hub/ev-market-india/main/data/cleaned/"

# column -> (M type, TMSL dataType, formatString, summarizeBy, hidden, sortBy)
T = {
    "date": ("type date", "dateTime", "yyyy-mm-dd", "none"),
    "text": ("type text", "string", None, "none"),
    "int_key": ("Int64.Type", "int64", "0", "none"),
    "int_sum": ("Int64.Type", "int64", "#,0", "sum"),
    "bool": ("type logical", "boolean", None, "none"),
}

TABLES = {
    "dim_date": {
        "cols": {"date": "date", "fiscal_year": "int_key", "fy_label": "text", "quarter": "text",
                 "fy_quarter": "text", "fy_quarter_sort": "int_key", "calendar_year": "int_key",
                 "month_num": "int_key", "month_name": "text", "month_short": "text",
                 "fiscal_month_num": "int_key", "month_year": "text", "month_year_sort": "int_key"},
        "sort": {"month_name": "fiscal_month_num", "month_short": "fiscal_month_num",
                 "fy_quarter": "fy_quarter_sort", "month_year": "month_year_sort"},
        "hidden": {"fy_quarter_sort", "month_year_sort"},
        "date_table": True,
    },
    "dim_state": {
        "cols": {"state": "text", "state_map_name": "text", "region": "text",
                 "state_type": "text", "country": "text"},
        "categories": {"state_map_name": "StateOrProvince", "country": "Country"},
    },
    "dim_maker": {
        "cols": {"maker": "text", "maker_raw": "text", "vehicle_category": "text",
                 "first_sale_month": "date"},
    },
    "dim_vehicle_category": {
        "cols": {"vehicle_category": "text", "category_short": "text", "avg_unit_price_inr": "int_key"},
    },
    "fact_state_sales": {
        "cols": {"date": "date", "state": "text", "vehicle_category": "text",
                 "electric_vehicles_sold": "int_sum", "total_vehicles_sold": "int_sum",
                 "non_ev_sold": "int_sum", "total_vehicles_sold_raw": "int_sum",
                 "is_imputed": "bool", "dq_note": "text"},
        "hidden": {"date", "state", "vehicle_category", "total_vehicles_sold_raw"},
    },
    "fact_maker_sales": {
        "cols": {"date": "date", "vehicle_category": "text", "maker": "text",
                 "electric_vehicles_sold": "int_sum", "is_others_bucket": "bool"},
        "hidden": {"date", "vehicle_category", "maker"},
    },
}

RELATIONSHIPS = [
    ("fact_state_sales", "date", "dim_date", "date"),
    ("fact_state_sales", "state", "dim_state", "state"),
    ("fact_state_sales", "vehicle_category", "dim_vehicle_category", "vehicle_category"),
    ("fact_maker_sales", "date", "dim_date", "date"),
    ("fact_maker_sales", "maker", "dim_maker", "maker"),
    ("fact_maker_sales", "vehicle_category", "dim_vehicle_category", "vehicle_category"),
]

PCT, PCT1, NUM = "0.00%", "0.0%", "#,0"

# table -> list of (name, DAX, format, display folder)
MEASURES = {
    "fact_state_sales": [
        ("EV Sold", "SUM ( fact_state_sales[electric_vehicles_sold] )", NUM, "1 Volume"),
        ("Total Vehicles Sold", "SUM ( fact_state_sales[total_vehicles_sold] )", NUM, "1 Volume"),
        ("Non-EV Sold", "SUM ( fact_state_sales[non_ev_sold] )", NUM, "1 Volume"),
        ("EV Penetration %", "DIVIDE ( [EV Sold], [Total Vehicles Sold] )", PCT, "2 Penetration"),
        ("EV Sold FY2022", "CALCULATE ( [EV Sold], dim_date[fiscal_year] = 2022 )", NUM, "1 Volume"),
        ("EV Sold FY2023", "CALCULATE ( [EV Sold], dim_date[fiscal_year] = 2023 )", NUM, "1 Volume"),
        ("EV Sold FY2024", "CALCULATE ( [EV Sold], dim_date[fiscal_year] = 2024 )", NUM, "1 Volume"),
        ("Total Vehicles FY2022", "CALCULATE ( [Total Vehicles Sold], dim_date[fiscal_year] = 2022 )", NUM, "1 Volume"),
        ("Total Vehicles FY2024", "CALCULATE ( [Total Vehicles Sold], dim_date[fiscal_year] = 2024 )", NUM, "1 Volume"),
        ("Penetration FY2022", "CALCULATE ( [EV Penetration %], dim_date[fiscal_year] = 2022 )", PCT, "2 Penetration"),
        ("Penetration FY2023", "CALCULATE ( [EV Penetration %], dim_date[fiscal_year] = 2023 )", PCT, "2 Penetration"),
        ("Penetration FY2024", "CALCULATE ( [EV Penetration %], dim_date[fiscal_year] = 2024 )", PCT, "2 Penetration"),
        ("Penetration Change FY22-24",
         "IF ( NOT ISBLANK ( [Penetration FY2022] ), [Penetration FY2024] - [Penetration FY2022] )",
         "+0.00%;-0.00%;0.00%", "2 Penetration"),
        ("Penetration Declined FY22-24 Flag", "IF ( [Penetration Change FY22-24] < 0, 1, 0 )", "0", "2 Penetration"),
        ("EV CAGR FY22-24",
         "IF ( [EV Sold FY2022] > 0, ( [EV Sold FY2024] / [EV Sold FY2022] ) ^ ( 1 / 2 ) - 1 )", PCT1, "3 Growth"),
        ("Total Vehicles CAGR FY22-24",
         "IF ( [Total Vehicles FY2022] > 0, ( [Total Vehicles FY2024] / [Total Vehicles FY2022] ) ^ ( 1 / 2 ) - 1 )",
         PCT1, "3 Growth"),
        ("Projected EV Sales FY2030",
         "IF ( NOT ISBLANK ( [EV CAGR FY22-24] ), [EV Sold FY2024] * ( 1 + [EV CAGR FY22-24] ) ^ 6 )", NUM, "3 Growth"),
        ("EV Sold YoY %",
         "VAR fy = MAX ( dim_date[fiscal_year] )\n"
         "VAR prev = CALCULATE ( [EV Sold], REMOVEFILTERS ( dim_date[fy_label] ), dim_date[fiscal_year] = fy - 1 )\n"
         "RETURN IF ( prev > 0, DIVIDE ( [EV Sold], prev ) - 1 )", PCT1, "3 Growth"),
        ("EV Share of 3-Year Sales %",
         "DIVIDE ( [EV Sold], CALCULATE ( [EV Sold], REMOVEFILTERS ( dim_date ) ) )", PCT1, "3 Growth"),
        ("EV Revenue (INR)",
         "SUMX ( dim_vehicle_category, [EV Sold] * dim_vehicle_category[avg_unit_price_inr] )", NUM, "4 Revenue"),
        ("EV Revenue (Rs Cr)", "DIVIDE ( [EV Revenue (INR)], 10000000 )", "#,0", "4 Revenue"),
        ("Revenue FY2022 (Rs Cr)", "CALCULATE ( [EV Revenue (Rs Cr)], dim_date[fiscal_year] = 2022 )", "#,0", "4 Revenue"),
        ("Revenue FY2023 (Rs Cr)", "CALCULATE ( [EV Revenue (Rs Cr)], dim_date[fiscal_year] = 2023 )", "#,0", "4 Revenue"),
        ("Revenue FY2024 (Rs Cr)", "CALCULATE ( [EV Revenue (Rs Cr)], dim_date[fiscal_year] = 2024 )", "#,0", "4 Revenue"),
        ("Revenue Growth FY22-24", "DIVIDE ( [Revenue FY2024 (Rs Cr)], [Revenue FY2022 (Rs Cr)] ) - 1", PCT1, "4 Revenue"),
        ("Revenue Growth FY23-24", "DIVIDE ( [Revenue FY2024 (Rs Cr)], [Revenue FY2023 (Rs Cr)] ) - 1", PCT1, "4 Revenue"),
    ],
    "fact_maker_sales": [
        ("Maker EV Sold", "SUM ( fact_maker_sales[electric_vehicles_sold] )", NUM, "5 Makers"),
        ("Maker EV Sold FY2022", "CALCULATE ( [Maker EV Sold], dim_date[fiscal_year] = 2022 )", NUM, "5 Makers"),
        ("Maker EV Sold FY2023", "CALCULATE ( [Maker EV Sold], dim_date[fiscal_year] = 2023 )", NUM, "5 Makers"),
        ("Maker EV Sold FY2024", "CALCULATE ( [Maker EV Sold], dim_date[fiscal_year] = 2024 )", NUM, "5 Makers"),
        ("Maker CAGR FY22-24",
         "IF ( [Maker EV Sold FY2022] > 0, ( [Maker EV Sold FY2024] / [Maker EV Sold FY2022] ) ^ ( 1 / 2 ) - 1 )",
         PCT1, "5 Makers"),
        ("Maker Market Share %",
         "DIVIDE ( [Maker EV Sold], CALCULATE ( [Maker EV Sold], REMOVEFILTERS ( dim_maker ) ) )", PCT1, "5 Makers"),
    ],
}

# ---------------------------------------------------------------------------
# Dashboard measures: each returns a value only for the rows a question asks for
# (top/bottom N, declined states, Delhi vs Karnataka), so visuals need no filters.
# ---------------------------------------------------------------------------

DASH = "6 Dashboard"


def _rank_measure(base: str, over: str, n: int, order: str = "DESC", positive_only: bool = False) -> str:
    table = f"FILTER ( ALL ( {over} ), [{base}] > 0 )" if positive_only else f"ALL ( {over} )"
    cond = "v > 0" if positive_only else "NOT ISBLANK ( v )"
    return (f"VAR v = [{base}]\n"
            f"VAR r = RANKX ( {table}, [{base}], , {order} )\n"
            f"RETURN IF ( {cond} && r <= {n}, v )")


_TOP5_4W = ("VAR r = RANKX ( FILTER ( ALL ( dim_maker[maker] ), [4W Maker Sales All Years] > 0 ), "
            "[4W Maker Sales All Years], , DESC )\n"
            "VAR keep = HASONEVALUE ( dim_maker[maker] ) && [4W Maker Sales All Years] > 0 && r <= 5\n")
_DK = 'KEEPFILTERS ( dim_state[state] IN { "Delhi", "Karnataka" } )'
_T10 = "HASONEVALUE ( dim_state[state] ) && [Top 10 Penetration Rank FY2024] <= 10"

MEASURES["fact_state_sales"] += [
    ("2W Penetration FY2024", 'CALCULATE ( [EV Penetration %], dim_date[fiscal_year] = 2024, '
     'dim_vehicle_category[vehicle_category] = "2-Wheelers" )', PCT, DASH),
    ("4W Penetration FY2024", 'CALCULATE ( [EV Penetration %], dim_date[fiscal_year] = 2024, '
     'dim_vehicle_category[vehicle_category] = "4-Wheelers" )', PCT, DASH),
    ("Q2 Top 5 States 2W Penetration FY2024", _rank_measure("2W Penetration FY2024", "dim_state[state]", 5), PCT, DASH),
    ("Q2 Top 5 States 4W Penetration FY2024", _rank_measure("4W Penetration FY2024", "dim_state[state]", 5), PCT, DASH),
    ("Q3 Declined Penetration FY2022", "IF ( [Penetration Change FY22-24] < 0, [Penetration FY2022] )", PCT, DASH),
    ("Q3 Declined Penetration FY2024", "IF ( [Penetration Change FY22-24] < 0, [Penetration FY2024] )", PCT, DASH),
    ("Q3 Declined Change", "IF ( [Penetration Change FY22-24] < 0, [Penetration Change FY22-24] )",
     "+0.00%;-0.00%;0.00%", DASH),
    ("Q5 EV Sold FY2024 (Delhi, Karnataka)", f"CALCULATE ( [EV Sold FY2024], {_DK} )", NUM, DASH),
    ("Q5 Penetration FY2024 (Delhi, Karnataka)", f"CALCULATE ( [Penetration FY2024], {_DK} )", PCT, DASH),
    ("Q7 Top 10 States Total Vehicles CAGR",
     _rank_measure("Total Vehicles CAGR FY22-24", "dim_state[state]", 10), PCT1, DASH),
    ("Top 10 Penetration Rank FY2024", "RANKX ( ALL ( dim_state[state] ), [Penetration FY2024], , DESC )", "0", DASH),
    ("Q9 Penetration FY2024 (Top 10)", f"IF ( {_T10}, [Penetration FY2024] )", PCT, DASH),
    ("Q9 EV CAGR FY22-24 (Top 10)", f"IF ( {_T10}, [EV CAGR FY22-24] )", PCT1, DASH),
    ("Q9 Projected EV Sales FY2030 (Top 10)", f"IF ( {_T10}, [Projected EV Sales FY2030] )", NUM, DASH),
]

MEASURES["fact_maker_sales"] += [
    *[(f"2W Maker Sales FY{fy}",
       f'CALCULATE ( [Maker EV Sold], dim_date[fiscal_year] = {fy}, '
       f'dim_vehicle_category[vehicle_category] = "2-Wheelers", KEEPFILTERS ( dim_maker[maker] <> "Others" ) )',
       NUM, DASH) for fy in (2023, 2024)],
    *[(f"Q1 {label} 3 2W Makers FY{fy}",
       _rank_measure(f"2W Maker Sales FY{fy}", "dim_maker[maker]", 3, order, positive_only=True), NUM, DASH)
      for fy in (2023, 2024) for label, order in (("Top", "DESC"), ("Bottom", "ASC"))],
    ("4W Maker Sales All Years", 'CALCULATE ( [Maker EV Sold], REMOVEFILTERS ( dim_date ), '
     'dim_vehicle_category[vehicle_category] = "4-Wheelers" )', NUM, DASH),
    ("Q4 Top 5 4W Makers Sales", _TOP5_4W + 'RETURN IF ( keep, CALCULATE ( [Maker EV Sold], '
     'dim_vehicle_category[vehicle_category] = "4-Wheelers" ) )', NUM, DASH),
    ("Q6 Top 5 4W Makers CAGR FY22-24", _TOP5_4W + "RETURN IF ( keep, [Maker CAGR FY22-24] )", PCT1, DASH),
    ("Q6 Top 5 4W Makers Units FY2022", _TOP5_4W + "RETURN IF ( keep, [Maker EV Sold FY2022] )", NUM, DASH),
    ("Q6 Top 5 4W Makers Units FY2024", _TOP5_4W + "RETURN IF ( keep, [Maker EV Sold FY2024] )", NUM, DASH),
]

# ---------------------------------------------------------------------------
# Report pages and visuals (PBIR-legacy report.json)
# ---------------------------------------------------------------------------

ALIAS = {"fact_state_sales": "f", "fact_maker_sales": "m", "dim_date": "d", "dim_state": "s",
         "dim_maker": "k", "dim_vehicle_category": "c"}
CATEGORY_ROLES = {"Category", "Rows"}


def _is_measure(table: str, name: str) -> bool:
    return any(m[0] == name for m in MEASURES.get(table, []))


def _field(ref: str) -> dict:
    table, name = ref.split(".", 1)
    kind = "Measure" if _is_measure(table, name) else "Column"
    if kind == "Column" and name not in TABLES[table]["cols"]:
        raise KeyError(f"Unknown field {ref}")
    return {kind: {"Expression": {"SourceRef": {"Source": ALIAS[table]}}, "Property": name}}


def _lit(v: str) -> dict:
    return {"expr": {"Literal": {"Value": v}}}


def _text(s: str) -> dict:
    return _lit("'" + s.replace("'", "''") + "'")


def visual(vtype: str, x: int, y: int, w: int, h: int, roles: dict, title: str | None = None,
           order: tuple[str, bool] | None = None, labels: bool = False) -> dict:
    """roles: {"Category": ["dim_state.state"], "Y": ["fact_state_sales.EV Sold"], ...};
    order: (field_ref, descending)."""
    refs = list(dict.fromkeys(r for rs in roles.values() for r in rs))
    tables = list(dict.fromkeys(r.split(".", 1)[0] for r in refs))
    query = {
        "Version": 2,
        "From": [{"Name": ALIAS[t], "Entity": t, "Type": 0} for t in tables],
        "Select": [{**_field(r), "Name": r, "NativeReferenceName": r.split(".", 1)[1]} for r in refs],
    }
    if order:
        query["OrderBy"] = [{"Direction": 2 if order[1] else 1, "Expression": _field(order[0])}]
    sv = {
        "visualType": vtype,
        "projections": {role: [{"queryRef": r, **({"active": True} if role in CATEGORY_ROLES else {})}
                               for r in rs] for role, rs in roles.items()},
        "prototypeQuery": query,
        "drillFilterOtherVisuals": True,
    }
    if title:
        sv["vcObjects"] = {"title": [{"properties": {"show": _lit("true"), "text": _text(title)}}]}
    if labels:
        sv["objects"] = {"labels": [{"properties": {"show": _lit("true")}}]}
    return {"pos": (x, y, w, h), "singleVisual": sv}


def textbox(x: int, y: int, w: int, h: int, text: str, size: str = "18pt") -> dict:
    return {"pos": (x, y, w, h), "singleVisual": {
        "visualType": "textbox", "drillFilterOtherVisuals": True,
        "objects": {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": text, "textStyle": {"fontWeight": "bold", "fontSize": size}}]}]}}]}}}


F, M = "fact_state_sales", "fact_maker_sales"
D, S, K, C = "dim_date", "dim_state", "dim_maker", "dim_vehicle_category"

PAGE_VISUALS = {
    "1 Overview": [
        textbox(20, 10, 1020, 50, "India EV Market Study | FY2022-FY2024 | Source: Vahan"),
        visual("card", 20, 70, 245, 110, {"Values": [f"{F}.EV Sold"]}, "EV units sold"),
        visual("card", 275, 70, 245, 110, {"Values": [f"{F}.Total Vehicles Sold"]}, "Total vehicles sold"),
        visual("card", 530, 70, 245, 110, {"Values": [f"{F}.EV Penetration %"]}, "EV penetration"),
        visual("card", 785, 70, 245, 110, {"Values": [f"{F}.EV CAGR FY22-24"]}, "EV CAGR FY22-24"),
        visual("slicer", 1060, 70, 200, 140, {"Values": [f"{D}.fy_label"]}, "Fiscal year"),
        visual("slicer", 1060, 220, 200, 110, {"Values": [f"{C}.vehicle_category"]}, "Category"),
        visual("lineChart", 20, 195, 1020, 255,
               {"Category": [f"{D}.month_year"], "Y": [f"{F}.EV Sold"], "Series": [f"{C}.vehicle_category"]},
               "Monthly EV units sold", order=(f"{D}.month_year", False)),
        visual("lineChart", 20, 460, 1020, 250,
               {"Category": [f"{D}.month_year"], "Y": [f"{F}.EV Penetration %"], "Series": [f"{C}.vehicle_category"]},
               "Monthly EV penetration %", order=(f"{D}.month_year", False)),
    ],
    "2 Makers (Q1, Q4, Q6)": [
        textbox(20, 10, 1240, 50, "Makers: who leads, who's growing (Q1, Q4, Q6)"),
        *[visual("clusteredBarChart", x, y, 300, 210,
                 {"Category": [f"{K}.maker"], "Y": [f"{M}.Q1 {lab} 3 2W Makers FY{fy}"]},
                 f"Q1 {lab} 3 2W makers FY{fy}", order=(f"{M}.Q1 {lab} 3 2W Makers FY{fy}", lab == "Top"),
                 labels=True)
          for (x, lab) in ((20, "Top"), (330, "Bottom")) for (y, fy) in ((70, 2023), (290, 2024))],
        visual("lineChart", 650, 70, 610, 430,
               {"Category": [f"{D}.fy_quarter"], "Y": [f"{M}.Q4 Top 5 4W Makers Sales"], "Series": [f"{K}.maker"]},
               "Q4 Quarterly 4W EV sales, top 5 makers", order=(f"{D}.fy_quarter", False)),
        visual("tableEx", 20, 510, 620, 200,
               {"Values": [f"{K}.maker", f"{M}.Q6 Top 5 4W Makers Units FY2022",
                           f"{M}.Q6 Top 5 4W Makers Units FY2024", f"{M}.Q6 Top 5 4W Makers CAGR FY22-24"]},
               "Q6 CAGR of 4W units, top 5 makers", order=(f"{M}.Q6 Top 5 4W Makers Units FY2024", True)),
        visual("clusteredBarChart", 650, 510, 610, 200,
               {"Category": [f"{K}.maker"], "Y": [f"{M}.Q6 Top 5 4W Makers CAGR FY22-24"]},
               "Q6 CAGR FY22-24", order=(f"{M}.Q6 Top 5 4W Makers CAGR FY22-24", True), labels=True),
    ],
    "3 States (Q2, Q3, Q5, Q7)": [
        textbox(20, 10, 1240, 50, "States: where EVs are winning (Q2, Q3, Q5, Q7)"),
        visual("clusteredBarChart", 20, 70, 400, 300,
               {"Category": [f"{S}.state"], "Y": [f"{F}.Q2 Top 5 States 2W Penetration FY2024"]},
               "Q2 Top 5 states, 2W EV penetration FY2024",
               order=(f"{F}.Q2 Top 5 States 2W Penetration FY2024", True), labels=True),
        visual("clusteredBarChart", 430, 70, 400, 300,
               {"Category": [f"{S}.state"], "Y": [f"{F}.Q2 Top 5 States 4W Penetration FY2024"]},
               "Q2 Top 5 states, 4W EV penetration FY2024",
               order=(f"{F}.Q2 Top 5 States 4W Penetration FY2024", True), labels=True),
        visual("tableEx", 840, 70, 420, 300,
               {"Values": [f"{S}.state", f"{C}.vehicle_category", f"{F}.Q5 EV Sold FY2024 (Delhi, Karnataka)",
                           f"{F}.Q5 Penetration FY2024 (Delhi, Karnataka)"]},
               "Q5 Delhi vs Karnataka, FY2024", order=(f"{S}.state", False)),
        visual("tableEx", 20, 380, 500, 330,
               {"Values": [f"{S}.state", f"{C}.vehicle_category", f"{F}.Q3 Declined Penetration FY2022",
                           f"{F}.Q3 Declined Penetration FY2024", f"{F}.Q3 Declined Change"]},
               "Q3 Declining EV penetration, FY2022 to FY2024", order=(f"{F}.Q3 Declined Change", False)),
        visual("clusteredBarChart", 530, 380, 730, 330,
               {"Category": [f"{S}.state"], "Y": [f"{F}.Q7 Top 10 States Total Vehicles CAGR"]},
               "Q7 Top 10 states by CAGR in total vehicles sold, FY22-24",
               order=(f"{F}.Q7 Top 10 States Total Vehicles CAGR", True), labels=True),
    ],
    "4 Seasonality (Q8)": [
        textbox(20, 10, 1240, 50, "Seasonality: peak and low months (Q8)"),
        visual("clusteredColumnChart", 20, 70, 1240, 330,
               {"Category": [f"{D}.month_short"], "Y": [f"{F}.EV Sold"], "Series": [f"{D}.fy_label"]},
               "Q8 EV units sold by month (Apr to Mar), by fiscal year", order=(f"{D}.month_short", False)),
        visual("clusteredColumnChart", 20, 410, 1240, 300,
               {"Category": [f"{D}.month_short"], "Y": [f"{F}.EV Share of 3-Year Sales %"]},
               "Q8 Share of 3-year EV sales by month", order=(f"{D}.month_short", False), labels=True),
    ],
    "5 Projections & Revenue (Q9, Q10)": [
        textbox(20, 10, 1240, 50, "Projections and revenue (Q9, Q10)"),
        visual("tableEx", 20, 70, 620, 400,
               {"Values": [f"{S}.state", f"{F}.Q9 Penetration FY2024 (Top 10)", f"{F}.Q9 EV CAGR FY22-24 (Top 10)",
                           f"{F}.Q9 Projected EV Sales FY2030 (Top 10)"]},
               "Q9 Top 10 states by FY2024 penetration: projected FY2030 EV sales",
               order=(f"{F}.Q9 Penetration FY2024 (Top 10)", True)),
        visual("clusteredBarChart", 650, 70, 610, 400,
               {"Category": [f"{S}.state"], "Y": [f"{F}.Q9 Projected EV Sales FY2030 (Top 10)"]},
               "Q9 Projected FY2030 EV units (CAGR-based)",
               order=(f"{F}.Q9 Projected EV Sales FY2030 (Top 10)", True), labels=True),
        visual("tableEx", 20, 480, 1240, 230,
               {"Values": [f"{C}.vehicle_category", f"{F}.Revenue FY2022 (Rs Cr)", f"{F}.Revenue FY2023 (Rs Cr)",
                           f"{F}.Revenue FY2024 (Rs Cr)", f"{F}.Revenue Growth FY22-24", f"{F}.Revenue Growth FY23-24"]},
               "Q10 EV revenue (Rs crore; avg price 2W Rs 85,000, 4W Rs 15 lakh)"),
    ],
}


def _container(v: dict, z: int, page: str) -> dict:
    x, y, w, h = v["pos"]
    import hashlib
    name = hashlib.md5(f"{page}|{z}".encode()).hexdigest()[:20]
    cfg = {"name": name,
           "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z * 1000, "width": w, "height": h,
                                              "tabOrder": z * 1000}}],
           "singleVisual": v["singleVisual"]}
    return {"x": float(x), "y": float(y), "z": float(z * 1000), "width": float(w), "height": float(h),
            "config": json.dumps(cfg), "filters": "[]"}


def build_report(with_visuals: bool = True) -> dict:
    sections = []
    for i, (page, visuals) in enumerate(PAGE_VISUALS.items()):
        sections.append({
            "config": "{}",
            "displayName": page,
            "displayOption": 1,
            "filters": "[]",
            "height": 720.0,
            "name": f"ReportSection{i}",
            "ordinal": i,
            "visualContainers": [_container(v, z, page) for z, v in enumerate(visuals)] if with_visuals else [],
            "width": 1280.0,
        })
    config = {"version": "5.43", "themeCollection": {}, "activeSectionIndex": 0,
              "defaultDrillFilterOtherVisuals": True, "settings": {}}
    return {"config": json.dumps(config), "layoutOptimization": 0, "sections": sections}


def m_query(table: str, cols: dict) -> list[str]:
    types = ", ".join(f'{{"{c}", {T[k][0]}}}' for c, k in cols.items())
    return [
        "let",
        f'    FilePath = DataFolder & "{table}.csv",',
        '    Raw = if Text.StartsWith(DataFolder, "http") then Web.Contents(FilePath) else File.Contents(FilePath),',
        '    Source = Csv.Document(Raw, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")',
        "in",
        "    Typed",
    ]


def build_model() -> dict:
    tables = []
    for tname, spec in TABLES.items():
        header = pd.read_csv(CLEAN / f"{tname}.csv", nrows=0).columns.tolist()
        if header != list(spec["cols"]):
            raise ValueError(f"{tname}: CSV columns {header} != model columns {list(spec['cols'])}")
        cols = []
        for c, kind in spec["cols"].items():
            _, dtype, fmt, summ = T[kind]
            col = {"name": c, "dataType": dtype, "sourceColumn": c, "summarizeBy": summ}
            if fmt:
                col["formatString"] = fmt
            if c in spec.get("sort", {}):
                col["sortByColumn"] = spec["sort"][c]
            if c in spec.get("hidden", set()):
                col["isHidden"] = True
            if c in spec.get("categories", {}):
                col["dataCategory"] = spec["categories"][c]
            if spec.get("date_table") and c == "date":
                col["isKey"] = True
            cols.append(col)
        t = {
            "name": tname,
            "columns": cols,
            "partitions": [{"name": tname, "mode": "import",
                            "source": {"type": "m", "expression": m_query(tname, spec["cols"])}}],
        }
        if spec.get("date_table"):
            t["dataCategory"] = "Time"
        if tname in MEASURES:
            t["measures"] = [{"name": n, "expression": e.split("\n") if "\n" in e else e,
                              "formatString": f, "displayFolder": folder}
                             for n, e, f, folder in MEASURES[tname]]
        tables.append(t)

    rels = [{"name": f"{ft}_{fc}_{tt}", "fromTable": ft, "fromColumn": fc,
             "toTable": tt, "toColumn": tc} for ft, fc, tt, tc in RELATIONSHIPS]

    return {
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": rels,
            "expressions": [{
                "name": "DataFolder",
                "kind": "m",
                "expression": f'"{DEFAULT_FOLDER}" meta [IsParameterQuery = true, Type = "Text", '
                              'IsParameterQueryRequired = true]',
            }],
            "annotations": [{"name": "PBI_QueryOrder",
                             "value": json.dumps(["DataFolder", *TABLES.keys()])}],
        },
    }


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_measures_dax(path: Path) -> None:
    lines = ["// India EV Market Study - DAX measures",
             "// Generated by scripts/build_powerbi.py. In Power BI: select the table named in the",
             "// header, Modeling > New measure, paste one block at a time.", ""]
    for table, ms in MEASURES.items():
        lines += [f"// ===== Table: {table} =====", ""]
        for n, e, f, folder in ms:
            lines += [f"// Format: {f}   Folder: {folder}", f"{n} =", *("    " + x for x in e.split("\n")), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sm = OUT / f"{NAME}.SemanticModel"
    write_json(sm / "definition.pbism", {"version": "1.0", "settings": {}})
    write_json(sm / "model.bim", build_model())
    for pbip_name, with_visuals in [(NAME, True), (f"{NAME}_EmptyReport", False)]:
        report_name = f"{pbip_name}.Report"
        write_json(OUT / f"{pbip_name}.pbip",
                   {"version": "1.0", "artifacts": [{"report": {"path": report_name}}],
                    "settings": {"enableAutoRecovery": True}})
        write_json(OUT / report_name / "definition.pbir",
                   {"version": "1.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"},
                                                           "byConnection": None}})
        write_json(OUT / report_name / "report.json", build_report(with_visuals))
    write_measures_dax(OUT / "measures.dax")
    n = sum(len(v) for v in MEASURES.values())
    nv = sum(len(v) for v in PAGE_VISUALS.values())
    print(f"Power BI project written to {OUT}  ({len(TABLES)} tables, {len(RELATIONSHIPS)} relationships, "
          f"{n} measures, {nv} visuals on {len(PAGE_VISUALS)} pages)")


if __name__ == "__main__":
    main()
