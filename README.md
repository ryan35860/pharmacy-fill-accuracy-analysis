# Prescription Fill Accuracy Analysis

A self-directed data analysis project examining fill-error patterns in a
long-term care (LTC) pharmacy automated dispensing dataset, built to apply
SQL and Excel analytics skills to a pharmacy-operations problem.

**Note on data:** This project uses a fully synthetic dataset generated with
Python/Faker (`generate_data.py`). No real patient, house, or facility
data is used or referenced anywhere in this project.

## Problem

LTC pharmacies fill high volumes of prescriptions daily through automated
dispensing systems (e.g., SynMed-style canister dispensing). Fill errors —
wrong medication, wrong count, mislabeled canisters — carry real patient
safety risk, and most pharmacies track them but don't always analyze *where*
and *why* they cluster. Understanding those patterns is what turns "we had
an error" into an actual process fix.

## Approach

1. **Generated a synthetic dataset** (`generate_data.py`) of 4,500
   prescription fills across 8 houses, 3 shifts, and 7 drug categories
   (including a flagged "LASA Risk" — look-alike/sound-alike medication
   category) over a 6-month period, with a few realistic patterns
   deliberately seeded in so the analysis has something genuine to find.
2. **Loaded the data into SQLite** and wrote a set of analysis queries
   (`analysis.sql`) covering: overall error rate, error rate by shift and
   drug category, error type breakdown (overall and drilled into the
   highest-risk shift), error rate by daily fill volume, and the share of
   errors caught before dispense.
3. **Built an Excel dashboard** (`Prescription_Fill_Accuracy_Dashboard.xlsx`)
   with KPI tiles, four charts, and a written Key Findings tab translating
   the numbers into recommendations.

## Key Findings

**1. Night shift has a meaningfully higher error rate.**
Night shift fills error at 16.0% vs. 10.6% for both Day and Evening shifts
— roughly 50% higher than either. Night-shift errors skew toward "Wrong
Count" (27.9%) and "Mislabeled Canister" (20.7%), pointing to a
staffing-level or verification gap rather than a knowledge gap.

**2. Look-alike/sound-alike (LASA) medications carry the highest error
rate by far.**
The LASA Risk category errors at 19.2% — nearly double the next-highest
category (11.6%) — with "Wrong Medication" as the dominant error type
within it, consistent with known LASA risk in pharmacy practice.

**3. Error rate climbs sharply on high-volume days.**
8.5% on low-volume days (≤50 fills) → 12.0% on medium-volume days → 16.0%
on high-volume days (71+ fills) — nearly double the low-volume rate.

**4. Most errors are caught before dispense, but ~1 in 5 are not.**
79.2% of errors are caught before reaching the patient, but 20.8% (109 of
524 errors) are not — a patient-safety metric worth tracking independently
of the overall error rate.

## Recommendations

- Add a second-check verification step for night-shift fills, or evaluate
  night-shift staffing ratios against fill volume.
- Apply tall-man lettering, physical separation, or barcode-verification
  gating specifically for the LASA medication list.
- Use daily fill volume as an early-warning signal to trigger added
  staffing or slower, more deliberate verification on high-volume days.
- Track "errors not caught before dispense" as its own KPI, separate from
  the overall error rate.

## Files

| File | Description |
|---|---|
| `generate_data.py` | Generates the synthetic fill-results dataset |
| `fills_data.csv` | The generated dataset (4,500 rows) |
| `analysis.sql` | SQL queries used for the analysis |
| `build_dashboard.py` | Builds the Excel dashboard from the data |
| `Prescription_Fill_Accuracy_Dashboard.xlsx` | Final dashboard — KPIs, charts, findings |

## Tools used

Python (pandas, Faker), SQLite/SQL, Excel (XlsxWriter)

## Background

Built by Ryan Nguyen, a dual-state licensed Registered Pharmacy Technician
currently working in long-term care pharmacy floor operations (automated
dispensing systems), as a self-directed project to apply SQL/Excel skills
to real pharmacy workflow problems while pursuing pharmacy
informatics/analytics roles.
