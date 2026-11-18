"""
India EV Market Study - data cleaning pipeline
==============================================

Reads the three raw CSVs in data/raw/, fixes every data-quality issue found
during profiling, and writes a Power BI-ready star schema to data/cleaned/:

    dim_date.csv              36 months, fiscal year/quarter + sort keys
    dim_state.csv             34 states/UTs, region, map-friendly names
    dim_maker.csv             26 makers, cleaned display names
    dim_vehicle_category.csv  2-Wheelers / 4-Wheelers + assumed avg price
    fact_state_sales.csv      monthly EV + total sales by state & category
    fact_maker_sales.csv      monthly EV sales by maker & category

It also writes reports/data_quality_log.csv and reports/DATA_CLEANING_REPORT.md.

Usage (from the repo root):
    python scripts/clean_data.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Reference mappings
# ---------------------------------------------------------------------------

# Same state spelled two ways in the raw file.
STATE_FIXES = {
    "Andaman & Nicobar Island": "Andaman & Nicobar",
}

# Names Power BI's map visual geocodes reliably (use with Country = India).
STATE_MAP_NAME = {
    "Andaman & Nicobar": "Andaman and Nicobar Islands",
    "DNH and DD": "Dadra and Nagar Haveli and Daman and Diu",
}

# Zonal-council style regions; Telangana is not present in the source data.
STATE_REGION = {
    "Chandigarh": "North", "Delhi": "North", "Haryana": "North",
    "Himachal Pradesh": "North", "Jammu and Kashmir": "North", "Ladakh": "North",
    "Punjab": "North", "Rajasthan": "North",
    "Chhattisgarh": "Central", "Madhya Pradesh": "Central",
    "Uttar Pradesh": "Central", "Uttarakhand": "Central",
    "Bihar": "East", "Jharkhand": "East", "Odisha": "East", "West Bengal": "East",
    "Goa": "West", "Gujarat": "West", "Maharashtra": "West", "DNH and DD": "West",
    "Andhra Pradesh": "South", "Karnataka": "South", "Kerala": "South",
    "Tamil Nadu": "South", "Puducherry": "South",
    "Arunachal Pradesh": "North-East", "Assam": "North-East", "Manipur": "North-East",
    "Meghalaya": "North-East", "Mizoram": "North-East", "Nagaland": "North-East",
    "Sikkim": "North-East", "Tripura": "North-East",
    "Andaman & Nicobar": "Islands",
}

UNION_TERRITORIES = {
    "Andaman & Nicobar", "Chandigarh", "DNH and DD", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Puducherry",
}

# Raw maker name -> clean display name (fixes typo + mixed casing).
MAKER_FIXES = {
    "OLA ELECTRIC": "Ola Electric", "OKAYA EV": "Okaya EV",
    "HERO ELECTRIC": "Hero Electric", "OKINAWA": "Okinawa", "AMPERE": "Ampere",
    "ATHER": "Ather", "PURE EV": "Pure EV", "TVS": "TVS", "REVOLT": "Revolt",
    "BAJAJ": "Bajaj", "BEING": "Being", "JITENDRA": "Jitendra", "OTHERS": "Others",
    "BGAUSS": "BGauss", "BATTRE ELECTRIC": "Battre Electric",
    "KINETIC GREEN": "Kinetic Green",
    "Mercedes -Benz AG": "Mercedes-Benz AG", "KIA Motors": "Kia Motors",
}

# Assumed average ex-showroom price per unit (used for revenue questions).
AVG_UNIT_PRICE_INR = {"2-Wheelers": 85_000, "4-Wheelers": 1_500_000}

DATE_FMT = "%d-%b-%y"  # raw format, e.g. 01-Apr-21


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DQLog:
    """Collects one row per data-quality finding."""

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, dataset, issue, action, rows_affected, detail=""):
        self.rows.append(dict(dataset=dataset, issue=issue, action=action,
                              rows_affected=int(rows_affected), detail=detail))

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


def read_raw(path: Path) -> pd.DataFrame:
    # utf-8-sig strips the byte-order mark found at the start of the state file
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip().lower() for c in df.columns]
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].astype(str).str.strip()
    return df


def parse_date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, format=DATE_FMT, errors="raise")


# ---------------------------------------------------------------------------
# Cleaning steps
# ---------------------------------------------------------------------------

def clean_dim_date(raw: pd.DataFrame, log: DQLog) -> pd.DataFrame:
    d = raw.copy()
    d["date"] = parse_date(d["date"])
    # Validate the supplied fiscal year/quarter (Indian FY: April-March)
    fy_calc = d["date"].dt.year + (d["date"].dt.month >= 4).astype(int)
    q_calc = "Q" + (((d["date"].dt.month - 4) % 12) // 3 + 1).astype(str)
    bad = (fy_calc != d["fiscal_year"]) | (q_calc != d["quarter"])
    log.add("dim_date", "Fiscal year / quarter validated against Apr-Mar calendar",
            "None needed" if bad.sum() == 0 else "Recomputed", bad.sum())
    d["fiscal_year"], d["quarter"] = fy_calc, q_calc
    log.add("dim_date", "Date stored as text DD-MMM-YY", "Converted to ISO date (yyyy-mm-dd)",
            len(d))

    d = d.sort_values("date").reset_index(drop=True)
    d["fy_label"] = "FY" + d["fiscal_year"].astype(str)
    d["fy_quarter"] = d["fy_label"] + "-" + d["quarter"]
    d["fy_quarter_sort"] = d["fiscal_year"] * 10 + d["quarter"].str[1].astype(int)
    d["calendar_year"] = d["date"].dt.year
    d["month_num"] = d["date"].dt.month
    d["month_name"] = d["date"].dt.strftime("%B")
    d["month_short"] = d["date"].dt.strftime("%b")
    d["fiscal_month_num"] = (d["month_num"] - 4) % 12 + 1  # Apr = 1 ... Mar = 12
    d["month_year"] = d["date"].dt.strftime("%b-%Y")
    d["month_year_sort"] = d["calendar_year"] * 100 + d["month_num"]
    return d[["date", "fiscal_year", "fy_label", "quarter", "fy_quarter", "fy_quarter_sort",
              "calendar_year", "month_num", "month_name", "month_short",
              "fiscal_month_num", "month_year", "month_year_sort"]]


def clean_state_sales(raw: pd.DataFrame, log: DQLog) -> pd.DataFrame:
    s = raw.copy()
    log.add("state_sales", "UTF-8 byte-order mark in header", "Stripped on read", 0,
            "Header 'date' was read as '\\ufeffdate' without this")
    s["date"] = parse_date(s["date"])

    n = s["state"].isin(STATE_FIXES).sum()
    s["state"] = s["state"].replace(STATE_FIXES)
    log.add("state_sales", "Same state spelled two ways",
            "Renamed 'Andaman & Nicobar Island' -> 'Andaman & Nicobar'", n,
            "Raw file used both spellings; Jan-2024 used the short form")

    key = ["date", "state", "vehicle_category"]
    dups = s.duplicated(key).sum()
    log.add("state_sales", "Duplicate date/state/category keys after renaming",
            "None found" if dups == 0 else "Aggregated", dups)
    if dups:
        s = s.groupby(key, as_index=False)[["electric_vehicles_sold", "total_vehicles_sold"]].sum()

    # Completeness check against the full 36 months x states x 2 categories grid
    grid = pd.MultiIndex.from_product(
        [sorted(s["date"].unique()), sorted(s["state"].unique()), sorted(s["vehicle_category"].unique())],
        names=key)
    missing = grid.difference(s.set_index(key).index)
    detail = "; ".join(f"{st} {c} {d:%b-%Y}" for d, st, c in missing)
    log.add("state_sales", "Missing month rows in source", "Left missing (not invented) - noted for analysis",
            len(missing), detail)

    # Row where EV sales exceed total sales -> total is a data-entry error
    s = s.sort_values(key).reset_index(drop=True)
    s["total_vehicles_sold_raw"] = s["total_vehicles_sold"]
    s["is_imputed"] = False
    s["dq_note"] = ""
    bad = s.index[s["electric_vehicles_sold"] > s["total_vehicles_sold"]]
    for i in bad:
        r = s.loc[i]
        series = s[(s["state"] == r["state"]) & (s["vehicle_category"] == r["vehicle_category"])]
        prev_ = series[series["date"] == r["date"] - pd.DateOffset(months=1)]["total_vehicles_sold"]
        next_ = series[series["date"] == r["date"] + pd.DateOffset(months=1)]["total_vehicles_sold"]
        neighbours = pd.concat([prev_, next_])
        new_total = int(round(neighbours.mean()))
        s.loc[i, "total_vehicles_sold"] = new_total
        s.loc[i, "is_imputed"] = True
        s.loc[i, "dq_note"] = (f"total_vehicles_sold was {r['total_vehicles_sold']} (< EV sold "
                               f"{r['electric_vehicles_sold']}); replaced with mean of adjacent months")
        log.add("state_sales", "EV sold > total vehicles sold (impossible)",
                f"Total imputed = mean of previous & next month = {new_total:,}", 1,
                f"{r['state']} {r['vehicle_category']} {r['date']:%b-%Y}: EV {r['electric_vehicles_sold']} "
                f"vs total {r['total_vehicles_sold']}; EV value kept (it reconciles with maker file)")

    # Values that look odd but are real - documented, not changed
    log.add("state_sales", "Very low totals in May/Jun-2021 across many states",
            "Kept - genuine (COVID-19 second-wave lockdowns)",
            ((s["date"].dt.year == 2021) & s["date"].dt.month.isin([5, 6])).sum())
    log.add("state_sales", "Chandigarh 2W penetration 55% in Mar-2023",
            "Kept - genuine (Chandigarh halted petrol 2W registrations from Feb-2023 under its EV policy)", 1)
    log.add("state_sales", "Ladakh / small UTs with single- or double-digit monthly totals",
            "Kept - genuine small markets; treat their penetration % with caution", 0)

    neg = (s[["electric_vehicles_sold", "total_vehicles_sold"]] < 0).any(axis=1).sum()
    log.add("state_sales", "Negative values", "None found", neg)
    log.add("state_sales", "Telangana not present in source data", "Noted - cannot be analysed", 0)

    s["non_ev_sold"] = s["total_vehicles_sold"] - s["electric_vehicles_sold"]
    return s[["date", "state", "vehicle_category", "electric_vehicles_sold", "total_vehicles_sold",
              "non_ev_sold", "total_vehicles_sold_raw", "is_imputed", "dq_note"]]


def clean_maker_sales(raw: pd.DataFrame, log: DQLog) -> pd.DataFrame:
    m = raw.copy()
    m["date"] = parse_date(m["date"])
    m["maker_raw"] = m["maker"]
    changed = m["maker"].isin(MAKER_FIXES) & (m["maker"].map(MAKER_FIXES) != m["maker"])
    m["maker"] = m["maker"].replace(MAKER_FIXES)
    log.add("maker_sales", "Maker names: typo ('Mercedes -Benz AG') and ALL-CAPS 2W names",
            "Standardised to one clean display name per maker (raw kept in dim_maker.maker_raw)",
            changed.sum())

    key = ["date", "vehicle_category", "maker"]
    dups = m.duplicated(key).sum()
    log.add("maker_sales", "Duplicate date/category/maker keys",
            "None found" if dups == 0 else "Aggregated", dups)
    if dups:
        m = m.groupby(key, as_index=False)["electric_vehicles_sold"].sum()

    zeros = (m["electric_vehicles_sold"] == 0).sum()
    log.add("maker_sales", "Explicit zero-sales rows (mostly months before a maker's launch)",
            "Kept - harmless for totals; exclude zero bases when computing CAGR", zeros,
            "Ola Electric Apr-Nov 2021, Kia/PCA/Volvo/BMW/BYD early months, etc.")
    log.add("maker_sales", "Maker list changes by fiscal year",
            "Noted - Being, Jitendra, Pure EV absent in FY2024; BGauss, Battre, Kinetic Green "
            "only in FY2024 (small makers are likely rolled into 'Others' in other years)", 0)
    m["is_others_bucket"] = m["maker"].eq("Others")
    return m.sort_values(key).reset_index(drop=True)[
        ["date", "vehicle_category", "maker", "electric_vehicles_sold", "is_others_bucket"]]


def build_dim_state(fact: pd.DataFrame) -> pd.DataFrame:
    states = sorted(fact["state"].unique())
    missing = [s for s in states if s not in STATE_REGION]
    if missing:
        raise ValueError(f"No region mapping for: {missing}")
    return pd.DataFrame({
        "state": states,
        "state_map_name": [STATE_MAP_NAME.get(s, s) for s in states],
        "region": [STATE_REGION[s] for s in states],
        "state_type": ["Union Territory" if s in UNION_TERRITORIES else "State" for s in states],
        "country": "India",
    })


def build_dim_maker(raw: pd.DataFrame, fact: pd.DataFrame) -> pd.DataFrame:
    pairs = raw[["maker", "vehicle_category"]].drop_duplicates().rename(columns={"maker": "maker_raw"})
    pairs["maker"] = pairs["maker_raw"].replace(MAKER_FIXES)
    first = fact[fact["electric_vehicles_sold"] > 0].groupby("maker")["date"].min().rename("first_sale_month")
    out = pairs.merge(first, on="maker", how="left").sort_values(["vehicle_category", "maker"])
    return out[["maker", "maker_raw", "vehicle_category", "first_sale_month"]].reset_index(drop=True)


def build_dim_category() -> pd.DataFrame:
    return pd.DataFrame({
        "vehicle_category": list(AVG_UNIT_PRICE_INR),
        "category_short": ["2W", "4W"],
        "avg_unit_price_inr": list(AVG_UNIT_PRICE_INR.values()),
    })


def reconcile(state_fact: pd.DataFrame, maker_fact: pd.DataFrame, log: DQLog) -> None:
    a = state_fact.groupby(["date", "vehicle_category"])["electric_vehicles_sold"].sum()
    b = maker_fact.groupby(["date", "vehicle_category"])["electric_vehicles_sold"].sum()
    diff = (a - b).abs()
    log.add("cross-file", "EV totals: state file vs maker file, per month & category",
            "Match exactly" if diff.max() == 0 else "Mismatch - investigate", (diff > 0).sum(),
            f"{len(diff)} month-category pairs compared; max abs difference = {int(diff.max())}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def write_report(log_df: pd.DataFrame, outputs: dict[str, pd.DataFrame], raw_counts: dict, path: Path):
    lines = ["# Data Cleaning Report - India EV Market Study", "",
             "Generated by `scripts/clean_data.py`. Raw files are untouched in `data/raw/`; "
             "everything below describes how `data/cleaned/` was produced.", "",
             "## Row counts", "", "| File | Rows |", "|---|---|"]
    for k, v in raw_counts.items():
        lines.append(f"| raw/{k} | {v:,} |")
    for k, v in outputs.items():
        lines.append(f"| cleaned/{k}.csv | {len(v):,} |")
    lines += ["", "## Issues found and actions taken", "",
              "| Dataset | Issue | Action | Rows | Detail |", "|---|---|---|---|---|"]
    for r in log_df.itertuples():
        lines.append(f"| {r.dataset} | {r.issue} | {r.action} | {r.rows_affected} | {r.detail} |")
    lines += ["", "## Cleaned model (star schema)", "",
              "```",
              "dim_date (date) ──────────┬──< fact_state_sales >── dim_state (state)",
              "                          └──< fact_maker_sales >── dim_maker (maker)",
              "dim_vehicle_category ─────┴── both facts on vehicle_category",
              "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(raw_dir: Path, out_dir: Path, report_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    log = DQLog()

    raw_state = read_raw(raw_dir / "electric_vehicle_sales_by_state.csv")
    raw_maker = read_raw(raw_dir / "electric_vehicle_sales_by_makers.csv")
    raw_date = read_raw(raw_dir / "dim_date.csv")
    raw_counts = {"electric_vehicle_sales_by_state.csv": len(raw_state),
                  "electric_vehicle_sales_by_makers.csv": len(raw_maker),
                  "dim_date.csv": len(raw_date)}

    for name, df in [("state_sales", raw_state), ("maker_sales", raw_maker), ("dim_date", raw_date)]:
        log.add(name, "Null values", "None found" if df.isna().sum().sum() == 0 else "Investigate",
                df.isna().any(axis=1).sum())
        log.add(name, "Fully duplicated rows", "None found" if df.duplicated().sum() == 0 else "Dropped",
                df.duplicated().sum())

    dim_date = clean_dim_date(raw_date, log)
    fact_state = clean_state_sales(raw_state, log)
    fact_maker = clean_maker_sales(raw_maker, log)
    reconcile(fact_state, fact_maker, log)

    # Every fact date must exist in dim_date
    for name, f in [("fact_state_sales", fact_state), ("fact_maker_sales", fact_maker)]:
        orphan = ~f["date"].isin(dim_date["date"])
        if orphan.any():
            raise ValueError(f"{name} has {orphan.sum()} dates not in dim_date")

    outputs = {
        "dim_date": dim_date,
        "dim_state": build_dim_state(fact_state),
        "dim_maker": build_dim_maker(raw_maker, fact_maker),
        "dim_vehicle_category": build_dim_category(),
        "fact_state_sales": fact_state,
        "fact_maker_sales": fact_maker,
    }
    for name, df in outputs.items():
        df.to_csv(out_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d")

    log_df = log.frame()
    log_df.to_csv(report_dir / "data_quality_log.csv", index=False)
    write_report(log_df, outputs, raw_counts, report_dir / "DATA_CLEANING_REPORT.md")

    print("Cleaned files written to", out_dir)
    for name, df in outputs.items():
        print(f"  {name:<22} {len(df):>5} rows")
    print(f"Data-quality log: {len(log_df)} checks -> {report_dir / 'data_quality_log.csv'}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw", type=Path, default=ROOT / "data" / "raw")
    p.add_argument("--out", type=Path, default=ROOT / "data" / "cleaned")
    p.add_argument("--reports", type=Path, default=ROOT / "reports")
    a = p.parse_args()
    main(a.raw, a.out, a.reports)
