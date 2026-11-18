# Primary Research Questions - Answers

Computed by `scripts/analysis.py` from `data/cleaned/`. Fiscal years run April-March (FY2024 = Apr-2023 to Mar-2024). Penetration = EV sold / total vehicles sold.

## Q1. Top 3 and bottom 3 makers (2-wheelers), FY2023 and FY2024

| fiscal_year | group | rank | maker | units |
|---|---|---|---|---|
| FY2023 | Top 3 | 1 | Ola Electric | 152,583 |
| FY2023 | Top 3 | 2 | Okinawa | 96,945 |
| FY2023 | Top 3 | 3 | Hero Electric | 88,993 |
| FY2023 | Bottom 3 | 1 | Jitendra | 8,563 |
| FY2023 | Bottom 3 | 2 | Being | 11,018 |
| FY2023 | Bottom 3 | 3 | Pure EV | 11,556 |
| FY2024 | Top 3 | 1 | Ola Electric | 322,489 |
| FY2024 | Top 3 | 2 | TVS | 180,743 |
| FY2024 | Top 3 | 3 | Ather | 107,552 |
| FY2024 | Bottom 3 | 1 | Battre Electric | 4,841 |
| FY2024 | Bottom 3 | 2 | Revolt | 7,254 |
| FY2024 | Bottom 3 | 3 | Kinetic Green | 9,585 |

'Others' bucket excluded. Bottom 3 is among makers listed in that year; the source lists a different set of small makers in FY2024 (BGauss, Battre, Kinetic Green) than in FY2023.

## Q2. Top 5 states by EV penetration in FY2024

| category | rank | state | ev_sold | total_sold | penetration |
|---|---|---|---|---|---|
| 2-Wheelers | 1 | Goa | 9,768 | 54,290 | 17.99% |
| 2-Wheelers | 2 | Kerala | 64,769 | 478,887 | 13.52% |
| 2-Wheelers | 3 | Karnataka | 148,111 | 1,279,767 | 11.57% |
| 2-Wheelers | 4 | Maharashtra | 183,052 | 1,817,343 | 10.07% |
| 2-Wheelers | 5 | Delhi | 38,094 | 405,218 | 9.40% |
| 4-Wheelers | 1 | Kerala | 9,169 | 172,109 | 5.33% |
| 4-Wheelers | 2 | Chandigarh | 1,020 | 22,651 | 4.50% |
| 4-Wheelers | 3 | Delhi | 8,630 | 201,130 | 4.29% |
| 4-Wheelers | 4 | Karnataka | 12,878 | 302,221 | 4.26% |
| 4-Wheelers | 5 | Goa | 1,031 | 24,234 | 4.25% |

Kerala 4W uses the corrected Jan-2024 total (see reports/DATA_CLEANING_REPORT.md); with the raw value Kerala's 4W FY2024 penetration would be overstated.

## Q3. States with declining EV penetration, FY2022 -> FY2024

| state | vehicle_category | FY2022 | FY2023 | FY2024 | change_pp |
|---|---|---|---|---|---|
| Andaman & Nicobar | 4-Wheelers | 1.88% | 0.34% | 0.77% | -1.11 pp |
| Ladakh | 2-Wheelers | 4.48% | 0.73% | 4.06% | -0.41 pp |

No state declined on a combined 2W + 4W basis. The category-level declines are in very small markets (monthly totals in the hundreds), so treat them as noise-prone rather than a trend.

## Q4. Quarterly sales, top 5 4-wheeler EV makers (FY2022-FY2024)

| fy_quarter | Tata Motors | Mahindra & Mahindra | MG Motor | BYD India | Hyundai Motor |
|---|---|---|---|---|---|
| FY2022-Q1 | 1,031 | 355 | 285 | 0 | 25 |
| FY2022-Q2 | 2,052 | 651 | 798 | 0 | 34 |
| FY2022-Q3 | 3,791 | 1,383 | 411 | 1 | 25 |
| FY2022-Q4 | 5,834 | 1,653 | 153 | 32 | 26 |
| FY2023-Q1 | 5,675 | 2,020 | 531 | 81 | 75 |
| FY2023-Q2 | 6,192 | 3,164 | 635 | 113 | 155 |
| FY2023-Q3 | 6,651 | 3,378 | 1,165 | 103 | 191 |
| FY2023-Q4 | 9,528 | 5,243 | 946 | 623 | 155 |
| FY2024-Q1 | 7,247 | 10,911 | 1,493 | 406 | 292 |
| FY2024-Q2 | 10,337 | 5,855 | 2,524 | 310 | 390 |
| FY2024-Q3 | 13,236 | 4,264 | 2,190 | 350 | 370 |
| FY2024-Q4 | 17,361 | 2,316 | 2,622 | 400 | 338 |

Top 5 by total FY2022-24 4W EV units: Tata Motors, Mahindra & Mahindra, MG Motor, BYD India, Hyundai Motor.

## Q5. Delhi vs Karnataka, FY2024

| vehicle_category | state | ev_sold | total_sold | penetration |
|---|---|---|---|---|
| 2-Wheelers | Delhi | 38,094 | 405,218 | 9.40% |
| 2-Wheelers | Karnataka | 148,111 | 1,279,767 | 11.57% |
| 4-Wheelers | Delhi | 8,630 | 201,130 | 4.29% |
| 4-Wheelers | Karnataka | 12,878 | 302,221 | 4.26% |
| All (2W + 4W) | Delhi | 46,724 | 606,348 | 7.71% |
| All (2W + 4W) | Karnataka | 160,989 | 1,581,988 | 10.18% |

## Q6. CAGR of 4-wheeler EV units, top 5 makers, FY2022 -> FY2024

| maker | FY2022 units | FY2024 units | cagr |
|---|---|---|---|
| Tata Motors | 12,708 | 48,181 | 94.7% |
| Mahindra & Mahindra | 4,042 | 23,346 | 140.3% |
| MG Motor | 1,647 | 8,829 | 131.5% |
| BYD India | 33 | 1,466 | 566.5% |
| Hyundai Motor | 110 | 1,390 | 255.5% |

CAGR = (FY2024 / FY2022)^(1/2) - 1. Top 5 = same five makers as Q4.

## Q7. Top 10 states by CAGR in total vehicles sold, FY2022 -> FY2024

| rank | state | FY2022 | FY2024 | cagr |
|---|---|---|---|---|
| 1 | Meghalaya | 22,193 | 36,628 | 28.5% |
| 2 | Goa | 48,372 | 78,524 | 27.4% |
| 3 | Karnataka | 1,007,894 | 1,581,988 | 25.3% |
| 4 | Delhi | 401,540 | 606,348 | 22.9% |
| 5 | Rajasthan | 880,985 | 1,300,476 | 21.5% |
| 6 | Gujarat | 1,094,872 | 1,590,987 | 20.5% |
| 7 | Assam | 379,450 | 547,626 | 20.1% |
| 8 | Mizoram | 19,439 | 27,422 | 18.8% |
| 9 | Arunachal Pradesh | 19,929 | 27,892 | 18.3% |
| 10 | Andaman & Nicobar | 5,148 | 7,203 | 18.3% |

Total vehicles = EV + non-EV, both categories. Source gaps: Odisha's FY2024 is missing March-2024 (CAGR understated); Andaman & Nicobar's FY2022 is missing June-2021 4W (CAGR slightly overstated).

## Q8. Peak and low months for EV sales (FY2022-FY2024 combined)

| month_name | ev_sold_3yr | share_of_3yr_sales | FY2022 | FY2023 | FY2024 |
|---|---|---|---|---|---|
| April | 134,657 | 6.5% | 6,315 | 55,524 | 72,818 |
| May | 159,869 | 7.7% | 1,499 | 45,373 | 112,997 |
| June | 106,709 | 5.2% | 5,487 | 47,591 | 53,631 |
| July | 127,426 | 6.2% | 15,794 | 50,010 | 61,622 |
| August | 141,961 | 6.9% | 17,153 | 55,584 | 69,224 |
| September | 145,972 | 7.1% | 19,351 | 56,828 | 69,793 |
| October | 185,185 | 9.0% | 22,190 | 81,162 | 81,833 |
| November | 205,196 | 9.9% | 26,159 | 80,752 | 98,285 |
| December | 180,401 | 8.7% | 29,241 | 68,475 | 82,685 |
| January | 189,099 | 9.2% | 31,672 | 68,116 | 89,311 |
| February | 198,049 | 9.6% | 38,171 | 70,827 | 89,051 |
| March | 291,587 | 14.1% | 58,118 | 95,126 | 138,343 |

Peak months: March, November, February. Low months: June, July, April. March benefits from fiscal-year-end buying; April-June FY2022 was hit by the COVID-19 second wave.

## Q9. Projected FY2030 EV sales, top 10 states by FY2024 penetration

| state | penetration_fy2024 | ev_fy2022 | ev_fy2024 | cagr_22_24 | projected_ev_fy2030 |
|---|---|---|---|---|---|
| Goa | 13.75% | 1,778 | 10,799 | 146.4% | 2,419,574 |
| Kerala | 11.36% | 13,639 | 73,938 | 132.8% | 11,779,401 |
| Karnataka | 10.18% | 43,111 | 160,989 | 93.2% | 8,383,406 |
| Maharashtra | 8.60% | 48,374 | 197,169 | 101.9% | 13,351,146 |
| Delhi | 7.71% | 16,535 | 46,724 | 68.1% | 1,054,259 |
| Chandigarh | 6.37% | 411 | 2,877 | 164.6% | 986,811 |
| Odisha | 6.33% | 9,498 | 39,118 | 102.9% | 2,732,814 |
| Chhattisgarh | 5.67% | 4,534 | 28,540 | 150.9% | 7,118,219 |
| Tamil Nadu | 5.49% | 36,863 | 94,314 | 60.0% | 1,579,547 |
| Puducherry | 5.37% | 734 | 3,098 | 105.4% | 232,936 |

Projection = FY2024 EV units x (1 + CAGR FY22->24)^6. Two years of very high early-adoption growth compounded over six more years gives unrealistically large numbers; present this as the mechanical answer the question asks for and pair it with a capped-growth scenario in the deck.

## Q10. Estimated EV revenue growth (assumed average unit price)

| category | revenue FY2022 (Rs crore) | revenue FY2023 (Rs crore) | revenue FY2024 (Rs crore) | growth FY22->FY24 | growth FY23->FY24 |
|---|---|---|---|---|---|
| 2-Wheelers | 2,147 | 6,187 | 7,928 | 269.3% | 28.1% |
| 4-Wheelers | 2,787 | 7,120 | 13,035 | 367.8% | 83.1% |
| Total (2W + 4W) | 4,933 | 13,307 | 20,963 | 324.9% | 57.5% |

Assumed prices: 2W Rs 85,000, 4W Rs 1,500,000 (change in data/cleaned/dim_vehicle_category.csv). With a fixed price, revenue growth per category equals unit growth. 1 crore = 10 million.
