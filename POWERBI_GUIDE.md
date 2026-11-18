# Power BI Guide (for Windows + Power BI Desktop)

Everything is cleaned already. The data lives in `data/cleaned/`; the model is in `powerbi/`.

## 1. Get the files

Clone the repo into `C:\` so the default data path works without changes:

```powershell
cd C:\
git clone https://github.com/shaswatprof2000-git-hub/ev-market-india.git
```

(No git? On GitHub click **Code → Download ZIP** and extract so the folder is `C:\ev-market-india`.)

## 2. Option A: open the ready-made project (recommended)

1. Double-click `C:\ev-market-india\powerbi\EV_Market_Study.pbip`.
   If Power BI won't open `.pbip` files, turn on **File → Options and settings → Options →
   Preview features → Power BI Project (.pbip) save option**, restart, and try again.
2. If you cloned somewhere other than `C:\ev-market-india`: **Home → Transform data → Edit
   parameters → DataFolder** and set it to your `...\data\cleaned\` folder. It must end in `\`.
3. **Home → Refresh.**
4. Check the numbers (section 5), then build visuals (section 4).
5. To share a single file: **File → Save as → .pbix**.

What's already in the model:
- 6 tables, 6 relationships (one-to-many, single direction)
- `dim_date` marked as the date table; months sort Apr→Mar; quarters sort chronologically
- `dim_state[state_map_name]` + `country` set as geography for map visuals
- 32 DAX measures in display folders (Volume, Penetration, Growth, Revenue, Makers)
- 5 blank report pages named after the questions they answer

## 3. Option B: build manually (if the .pbip won't open)

1. **Get data → Text/CSV** and load all 6 files from `data/cleaned/`. Check the types:
   `date` = Date, sales columns = Whole number, everything else as detected.
2. **Model view** → create these relationships (Many-to-one, single direction):

| From (many) | To (one) |
|---|---|
| fact_state_sales[date] | dim_date[date] |
| fact_state_sales[state] | dim_state[state] |
| fact_state_sales[vehicle_category] | dim_vehicle_category[vehicle_category] |
| fact_maker_sales[date] | dim_date[date] |
| fact_maker_sales[maker] | dim_maker[maker] |
| fact_maker_sales[vehicle_category] | dim_vehicle_category[vehicle_category] |

   Do **not** relate `dim_maker` to `dim_vehicle_category` (it would create an ambiguous path).
3. Select `dim_date` → **Mark as date table** → column `date`.
4. Sort by column: `month_name` and `month_short` by `fiscal_month_num`; `fy_quarter` by
   `fy_quarter_sort`; `month_year` by `month_year_sort`.
5. Open `powerbi/measures.dax` and create each measure on the table named in its section.

## 4. Dashboard plan (one page per theme)

Always use fields from the **dim_** tables for axes and slicers. Put a `dim_vehicle_category`
slicer and an `fy_label` slicer on every page (sync slicers).

**Page 1: Overview**
- Cards: `EV Sold`, `Total Vehicles Sold`, `EV Penetration %`, `EV CAGR FY22-24`
- Line chart: `month_year` × `EV Sold`, legend `vehicle_category`
- Line chart: `month_year` × `EV Penetration %`

**Page 2: Makers (Q1, Q4, Q6)**
- Q1: bar chart `maker` × `Maker EV Sold`; filters: category = 2-Wheelers, fiscal_year = 2023
  (duplicate for 2024), maker ≠ Others; Top N = 3 for top, Bottom N = 3 for bottom
- Q4: line chart `fy_quarter` × `Maker EV Sold`, legend `maker`; category = 4-Wheelers; maker
  Top N = 5 by `Maker EV Sold`
- Q6: table `maker`, `Maker EV Sold FY2022`, `Maker EV Sold FY2024`, `Maker CAGR FY22-24`
  (4-Wheelers, top 5)
- Donut: `maker` × `Maker Market Share %` (FY2024)

**Page 3: States (Q2, Q3, Q5, Q7)**
- Q2: bar chart `state` × `EV Penetration %`, fiscal_year = 2024, Top N = 5, one per category
- Q3: table `state`, `vehicle_category`, `Penetration FY2022`, `Penetration FY2024`,
  `Penetration Change FY22-24`; visual filter `Penetration Declined FY22-24 Flag` = 1
- Q5: clustered bar `vehicle_category` × `EV Sold` and `EV Penetration %`, state = Delhi, Karnataka
- Q7: bar chart `state` × `Total Vehicles CAGR FY22-24`, Top N = 10
- Filled map: `dim_state[state_map_name]` coloured by `EV Penetration %`

**Page 4: Seasonality (Q8)**
- Column chart `month_short` × `EV Sold` (sorts Apr→Mar), legend `fy_label`
- Optional: same with `EV Share of 3-Year Sales %`

**Page 5: Projections & Revenue (Q9, Q10)**
- Q9: table `state`, `Penetration FY2024`, `EV CAGR FY22-24`, `Projected EV Sales FY2030`;
  Top N = 10 by `Penetration FY2024`
- Q10: matrix rows `vehicle_category`; values `Revenue FY2022 (Rs Cr)`,
  `Revenue FY2023 (Rs Cr)`, `Revenue FY2024 (Rs Cr)`, `Revenue Growth FY22-24`,
  `Revenue Growth FY23-24`
- Average prices assumed: 2W ₹85,000, 4W ₹15,00,000 (edit `data/cleaned/dim_vehicle_category.csv`, then refresh)

## 5. Check the numbers after refresh

These should match exactly (no slicers applied):

| Check | Expected |
|---|---|
| `EV Sold` (all years) | 2,066,111 |
| `Maker EV Sold` (all years) | 2,066,111 |
| `Total Vehicles Sold` (all years) | 57,233,134 |
| `EV Sold FY2024` | 1,019,593 |
| `Penetration FY2024` | 4.81% |
| `EV Sold FY2024`, 4-Wheelers | 86,901 |

Every question's answer is in `analysis/PRIMARY_ANSWERS.md`. Use it to confirm the visuals.

## 6. Notes for the presentation

- Kerala 4W Jan-2024 total was corrected (raw 164 < EV 734). Look for `is_imputed = TRUE` in `fact_state_sales`.
- Odisha has no March-2024 rows in the source, so Odisha FY2024 is 11 months.
- The Q9 projection compounds two years of early-adoption growth for six more years, so
  the numbers are very large. Present it with a more conservative scenario next to it.
