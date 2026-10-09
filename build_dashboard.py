import sqlite3
import pandas as pd
import xlsxwriter

conn = sqlite3.connect("fills.db")

overall = pd.read_sql_query("""
    SELECT COUNT(*) AS total_fills, SUM(is_error) AS total_errors,
           ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
    FROM fills;
""", conn)

by_shift = pd.read_sql_query("""
    SELECT shift, COUNT(*) AS total_fills, SUM(is_error) AS errors,
           ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
    FROM fills GROUP BY shift ORDER BY error_rate_pct DESC;
""", conn)

by_category = pd.read_sql_query("""
    SELECT drug_category, COUNT(*) AS total_fills, SUM(is_error) AS errors,
           ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
    FROM fills GROUP BY drug_category ORDER BY error_rate_pct DESC;
""", conn)

error_types = pd.read_sql_query("""
    SELECT error_type, COUNT(*) AS occurrences,
           ROUND(100.0 * COUNT(*) / (SELECT SUM(is_error) FROM fills), 1) AS pct_of_errors
    FROM fills WHERE is_error = 1
    GROUP BY error_type ORDER BY occurrences DESC;
""", conn)

volume_bucket = pd.read_sql_query("""
    SELECT CASE WHEN daily_house_volume <= 50 THEN 'Low (<=50)'
                WHEN daily_house_volume <= 70 THEN 'Medium (51-70)'
                ELSE 'High (71+)' END AS volume_bucket,
           ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
    FROM fills GROUP BY volume_bucket ORDER BY
        CASE volume_bucket WHEN 'Low (<=50)' THEN 1 WHEN 'Medium (51-70)' THEN 2 ELSE 3 END;
""", conn)

catch_status = pd.read_sql_query("""
    SELECT CASE WHEN caught_before_dispense = 1 THEN 'Caught Before Dispense'
                ELSE 'Not Caught Before Dispense' END AS catch_status,
           COUNT(*) AS error_count
    FROM fills WHERE is_error = 1 GROUP BY catch_status;
""", conn)

conn.close()

wb = xlsxwriter.Workbook("Prescription_Fill_Accuracy_Dashboard.xlsx")

# ---- formats ----
title_fmt = wb.add_format({"bold": True, "font_size": 16, "font_color": "#1F3864"})
subtitle_fmt = wb.add_format({"italic": True, "font_size": 10, "font_color": "#595959"})
header_fmt = wb.add_format({"bold": True, "bg_color": "#1F3864", "font_color": "white", "border": 1})
cell_fmt = wb.add_format({"border": 1})
kpi_label_fmt = wb.add_format({"font_size": 11, "font_color": "#595959"})
kpi_value_fmt = wb.add_format({"font_size": 24, "bold": True, "font_color": "#1F3864"})

# ============================================================
# Dashboard sheet
# ============================================================
ws = wb.add_worksheet("Dashboard")
ws.hide_gridlines(2)
ws.set_column("A:A", 2)
ws.set_column("B:J", 13)

ws.write("B2", "Prescription Fill Accuracy Dashboard", title_fmt)
ws.write("B3", "Synthetic LTC pharmacy fill data, Jan-Jun 2026 (n=4,500) — portfolio project", subtitle_fmt)

ws.write("B5", "Total Fills", kpi_label_fmt)
ws.write("B6", int(overall["total_fills"][0]), kpi_value_fmt)

ws.write("D5", "Total Errors", kpi_label_fmt)
ws.write("D6", int(overall["total_errors"][0]), kpi_value_fmt)

ws.write("F5", "Overall Error Rate", kpi_label_fmt)
ws.write("F6", f"{overall['error_rate_pct'][0]}%", kpi_value_fmt)

ws.write("H5", "Highest-Risk Shift", kpi_label_fmt)
ws.write("H6", by_shift.iloc[0]["shift"], kpi_value_fmt)

# Shift table + chart
ws.write("B9", "Error Rate by Shift", header_fmt)
r0 = 10
ws.write_row(r0, 1, ["Shift", "Total Fills", "Errors", "Error Rate %"], header_fmt)
for i, row in by_shift.iterrows():
    r = r0 + 1 + i
    ws.write(r, 1, row["shift"], cell_fmt)
    ws.write(r, 2, int(row["total_fills"]), cell_fmt)
    ws.write(r, 3, int(row["errors"]), cell_fmt)
    ws.write(r, 4, row["error_rate_pct"], cell_fmt)

chart1 = wb.add_chart({"type": "column"})
chart1.add_series({
    "name": "Error Rate %",
    "categories": ["Dashboard", r0 + 1, 1, r0 + len(by_shift), 1],
    "values": ["Dashboard", r0 + 1, 4, r0 + len(by_shift), 4],
    "fill": {"color": "#1F3864"},
})
chart1.set_title({"name": "Error Rate by Shift"})
chart1.set_legend({"none": True})
chart1.set_y_axis({"name": "Error Rate (%)"})
chart1.set_size({"width": 480, "height": 280})
ws.insert_chart("K9", chart1)

# Drug category table + chart
cat_start = r0 + len(by_shift) + 4
ws.write(cat_start - 1, 1, "Error Rate by Drug Category", header_fmt)
ws.write_row(cat_start, 1, ["Drug Category", "Total Fills", "Errors", "Error Rate %"], header_fmt)
for i, row in by_category.iterrows():
    r = cat_start + 1 + i
    ws.write(r, 1, row["drug_category"], cell_fmt)
    ws.write(r, 2, int(row["total_fills"]), cell_fmt)
    ws.write(r, 3, int(row["errors"]), cell_fmt)
    ws.write(r, 4, row["error_rate_pct"], cell_fmt)

chart2 = wb.add_chart({"type": "bar"})
chart2.add_series({
    "name": "Error Rate %",
    "categories": ["Dashboard", cat_start + 1, 1, cat_start + len(by_category), 1],
    "values": ["Dashboard", cat_start + 1, 4, cat_start + len(by_category), 4],
    "fill": {"color": "#C00000"},
})
chart2.set_title({"name": "Error Rate by Drug Category"})
chart2.set_legend({"none": True})
chart2.set_size({"width": 480, "height": 280})
ws.insert_chart("K27", chart2)

# Error type breakdown + chart
err_start = cat_start + len(by_category) + 4
ws.write(err_start - 1, 1, "Error Type Breakdown (All Errors)", header_fmt)
ws.write_row(err_start, 1, ["Error Type", "Occurrences", "% of Errors"], header_fmt)
for i, row in error_types.iterrows():
    r = err_start + 1 + i
    ws.write(r, 1, row["error_type"], cell_fmt)
    ws.write(r, 2, int(row["occurrences"]), cell_fmt)
    ws.write(r, 3, row["pct_of_errors"], cell_fmt)

chart3 = wb.add_chart({"type": "pie"})
chart3.add_series({
    "name": "% of Errors",
    "categories": ["Dashboard", err_start + 1, 1, err_start + len(error_types), 1],
    "values": ["Dashboard", err_start + 1, 3, err_start + len(error_types), 3],
})
chart3.set_title({"name": "Error Type Breakdown"})
chart3.set_size({"width": 480, "height": 280})
ws.insert_chart("K46", chart3)

# Volume bucket table + chart
vol_start = err_start + len(error_types) + 4
ws.write(vol_start - 1, 1, "Error Rate by Daily House Volume", header_fmt)
ws.write_row(vol_start, 1, ["Volume Bucket", "Error Rate %"], header_fmt)
for i, row in volume_bucket.iterrows():
    r = vol_start + 1 + i
    ws.write(r, 1, row["volume_bucket"], cell_fmt)
    ws.write(r, 2, row["error_rate_pct"], cell_fmt)

chart4 = wb.add_chart({"type": "line"})
chart4.add_series({
    "name": "Error Rate %",
    "categories": ["Dashboard", vol_start + 1, 1, vol_start + len(volume_bucket), 1],
    "values": ["Dashboard", vol_start + 1, 2, vol_start + len(volume_bucket), 2],
    "line": {"color": "#BF8F00", "width": 2.5},
    "marker": {"type": "circle", "size": 6, "fill": {"color": "#BF8F00"}},
})
chart4.set_title({"name": "Error Rate vs. Daily House Volume"})
chart4.set_legend({"none": True})
chart4.set_y_axis({"name": "Error Rate (%)"})
chart4.set_size({"width": 480, "height": 280})
ws.insert_chart("K64", chart4)

# ============================================================
# Findings sheet
# ============================================================
ws2 = wb.add_worksheet("Key Findings")
ws2.hide_gridlines(2)
ws2.set_column("A:A", 2)
ws2.set_column("B:B", 92)

ws2.write("B2", "Key Findings & Recommendations", title_fmt)
ws2.write("B3", "Synthetic dataset — portfolio analysis project", subtitle_fmt)

findings = [
    ("1. Night shift has a meaningfully higher error rate.",
     "Night shift fills error at 16.0%, vs. 10.6% for both Day and Evening shifts — roughly 50% "
     "higher than either. Night-shift errors skew toward 'Wrong Count' (27.9%) and 'Mislabeled "
     "Canister' (20.7%), suggesting a staffing-level or fatigue-related verification gap rather "
     "than a knowledge gap."),
    ("   Recommendation:",
     "Add a second-check step for night-shift fills, or evaluate night-shift staffing ratios "
     "against fill volume."),
    ("", ""),
    ("2. LASA (look-alike/sound-alike) medications carry the highest error rate by far.",
     "The LASA Risk category errors at 19.2% — nearly double the next-highest category "
     "(Antidiabetics/Anticoagulants at 11.6%) — and 'Wrong Medication' is the dominant error type "
     "within it, consistent with known LASA risk in pharmacy practice."),
    ("   Recommendation:",
     "Apply tall-man lettering, physical separation, or barcode-verification gating specifically "
     "for the LASA medication list rather than a blanket policy change."),
    ("", ""),
    ("3. Error rate climbs sharply on high-volume days.",
     "Error rate is 8.5% on low-volume days (<=50 fills), 12.0% on medium-volume days, and jumps "
     "to 16.0% on high-volume days (71+ fills) — nearly double the low-volume rate."),
    ("   Recommendation:",
     "Use daily volume as an early-warning signal to trigger additional staffing or a slower, "
     "more deliberate verification process on predictably high-volume days."),
    ("", ""),
    ("4. Most errors are caught before dispense, but ~1 in 5 are not.",
     "79.2% of errors are caught before reaching the patient, but 20.8% (109 of 524 errors) are "
     "not caught before dispense — a patient-safety metric worth tracking independently of the "
     "overall error rate."),
]

row = 5
for label, text in findings:
    if label.startswith("   "):
        ws2.write(row, 1, label, wb.add_format({"bold": True, "italic": True, "indent": 1}))
    elif label == "":
        pass
    else:
        ws2.write(row, 1, label, wb.add_format({"bold": True, "font_size": 12, "font_color": "#1F3864"}))
    if text:
        row += 1
        ws2.write(row, 1, text, wb.add_format({"text_wrap": True}))
        ws2.set_row(row, 34)
    row += 1

wb.close()
print("Dashboard built: Prescription_Fill_Accuracy_Dashboard.xlsx")
