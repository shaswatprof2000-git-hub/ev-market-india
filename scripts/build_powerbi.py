"""
Builds the Power BI hand-off from the cleaned data:

    powerbi/EV_Market_Study.pbip                 open this in Power BI Desktop (Windows)
    powerbi/EV_Market_Study.SemanticModel/       tables, relationships, DAX measures
    powerbi/EV_Market_Study.Report/              report shell with 5 blank pages
    powerbi/measures.dax                         every measure, for copy-paste / manual build

The semantic model loads the CSVs from a Power Query parameter `DataFolder`.
Default: C:\\ev-market-india\\data\\cleaned\\  (change it in Transform data > Edit parameters).

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
DEFAULT_FOLDER = "C:\\ev-market-india\\data\\cleaned\\"

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

PAGES = ["1 Overview", "2 Makers (Q1, Q4, Q6)", "3 States (Q2, Q3, Q5, Q7)",
         "4 Seasonality (Q8)", "5 Projections & Revenue (Q9, Q10)"]


def m_query(table: str, cols: dict) -> list[str]:
    types = ", ".join(f'{{"{c}", {T[k][0]}}}' for c, k in cols.items())
    return [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "{table}.csv"), '
        '[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
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


def build_report() -> dict:
    sections = [{
        "config": "{}",
        "displayName": name,
        "displayOption": 1,
        "filters": "[]",
        "height": 720.0,
        "name": f"ReportSection{i}",
        "ordinal": i,
        "visualContainers": [],
        "width": 1280.0,
    } for i, name in enumerate(PAGES)]
    config = {"version": "5.43", "themeCollection": {}, "activeSectionIndex": 0,
              "defaultDrillFilterOtherVisuals": True, "settings": {}}
    return {"config": json.dumps(config), "layoutOptimization": 0, "sections": sections}


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
    rp = OUT / f"{NAME}.Report"
    write_json(OUT / f"{NAME}.pbip",
               {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                "settings": {"enableAutoRecovery": True}})
    write_json(sm / "definition.pbism", {"version": "1.0", "settings": {}})
    write_json(sm / "model.bim", build_model())
    write_json(rp / "definition.pbir",
               {"version": "1.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"},
                                                       "byConnection": None}})
    write_json(rp / "report.json", build_report())
    write_measures_dax(OUT / "measures.dax")
    n = sum(len(v) for v in MEASURES.values())
    print(f"Power BI project written to {OUT}  ({len(TABLES)} tables, {len(RELATIONSHIPS)} relationships, {n} measures)")


if __name__ == "__main__":
    main()
