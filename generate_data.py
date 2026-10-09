"""
Synthetic LTC pharmacy prescription fill results dataset generator.

Generates a realistic (but fully fictional) dataset of prescription fills
from an automated dispensing (SynMed-style) pharmacy floor, with
deliberately seeded patterns so the analysis has something real to
discover:

  1. Night shift has a meaningfully higher fill-error rate than day/evening.
  2. "Look-alike/sound-alike" (LASA) medications have a higher error rate
     than other drug categories.
  3. Error rate rises as daily fill volume increases (high-volume days
     strain accuracy).

None of this is real company data — all names, facilities, and IDs are
fictional/generated.
"""

import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(7)
random.seed(7)

N_FILLS = 4500
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 6, 30)

FACILITIES = [f"House {c}" for c in "ABCDEFGH"]
SHIFTS = ["Day", "Evening", "Night"]
SHIFT_WEIGHTS = [45, 35, 20]  # night shift runs leaner staffing / lower volume

DRUG_CATEGORIES = {
    "Antibiotics": ["Amoxicillin", "Azithromycin", "Ciprofloxacin"],
    "Anticoagulants": ["Warfarin", "Apixaban", "Rivaroxaban"],
    "Antidiabetics": ["Metformin", "Insulin Glargine", "Glipizide"],
    "Cardiovascular": ["Lisinopril", "Atorvastatin", "Metoprolol"],
    "Pain Management": ["Gabapentin", "Acetaminophen", "Tramadol"],
    "Psychiatric": ["Sertraline", "Quetiapine", "Trazodone"],
    # Deliberately flagged LASA (look-alike/sound-alike) category
    "LASA Risk": ["Hydroxyzine/Hydralazine", "Clonidine/Klonopin", "Lamictal/Labetalol"],
}

ERROR_TYPES = [
    "Wrong Count",
    "Wrong Medication",
    "Mislabeled Canister",
    "Missed Fill",
    "Wrong Strength",
]

def random_date():
    delta_days = (END_DATE - START_DATE).days
    return START_DATE + timedelta(days=random.randint(0, delta_days))

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

# Pre-generate daily fill volume (fills per house per day) to drive
# the volume -> error-rate pattern
daily_volume_lookup = {}

rows = []
for i in range(N_FILLS):
    fill_id = f"FIL-{200000 + i}"
    fill_date = random_date()
    house = random.choice(FACILITIES)
    shift = weighted_choice(SHIFTS, SHIFT_WEIGHTS)
    category = random.choice(list(DRUG_CATEGORIES.keys()))
    medication = random.choice(DRUG_CATEGORIES[category])

    # simulate a daily volume for this house/date (used for pattern 3)
    key = (house, fill_date.date())
    if key not in daily_volume_lookup:
        daily_volume_lookup[key] = random.randint(15, 95)
    daily_volume = daily_volume_lookup[key]

    # --- base error rate ---
    base_error_rate = 0.06

    # --- seeded pattern 1: Night shift has higher error rate ---
    if shift == "Night":
        base_error_rate += 0.07

    # --- seeded pattern 2: LASA category has higher error rate ---
    if category == "LASA Risk":
        base_error_rate += 0.09

    # --- seeded pattern 3: high daily volume raises error rate ---
    if daily_volume > 70:
        base_error_rate += 0.08
    elif daily_volume > 50:
        base_error_rate += 0.03

    is_error = random.random() < base_error_rate

    if is_error:
        if category == "LASA Risk":
            error_type = weighted_choice(
                ERROR_TYPES, weights=[15, 45, 15, 10, 15]  # mostly wrong medication
            )
        elif shift == "Night":
            error_type = weighted_choice(
                ERROR_TYPES, weights=[30, 15, 25, 20, 10]  # more mislabeling/counts, lower staffing checks
            )
        else:
            error_type = random.choice(ERROR_TYPES)
        caught_before_dispense = random.random() < 0.78
        resolution_minutes = max(2, round(random.gauss(22, 9), 1))
    else:
        error_type = None
        caught_before_dispense = None
        resolution_minutes = 0.0

    turnaround_minutes = max(3, round(random.gauss(18, 6) + (daily_volume > 70) * 6, 1))

    rows.append({
        "fill_id": fill_id,
        "fill_date": fill_date.strftime("%Y-%m-%d"),
        "day_of_week": fill_date.strftime("%A"),
        "house": house,
        "shift": shift,
        "drug_category": category,
        "medication": medication,
        "daily_house_volume": daily_volume,
        "turnaround_minutes": turnaround_minutes,
        "is_error": is_error,
        "error_type": error_type,
        "caught_before_dispense": caught_before_dispense,
        "error_resolution_minutes": resolution_minutes,
    })

df = pd.DataFrame(rows)
df = df.sort_values("fill_date").reset_index(drop=True)
df.to_csv("fills_data.csv", index=False)

print(f"Generated {len(df)} rows -> fills_data.csv")
print(f"Overall error rate: {df['is_error'].mean():.1%}")
print(df.groupby('shift')['is_error'].mean().sort_values(ascending=False))
