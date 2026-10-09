-- ============================================================
-- Prescription Fill Accuracy Analysis
-- Dataset: fills (synthetic LTC pharmacy fill results, Jan-Jun 2026)
-- ============================================================

-- 1. Overall fill error rate
SELECT
    COUNT(*) AS total_fills,
    SUM(is_error) AS total_errors,
    ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
FROM fills;

-- 2. Error rate by shift
SELECT
    shift,
    COUNT(*) AS total_fills,
    SUM(is_error) AS errors,
    ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
FROM fills
GROUP BY shift
ORDER BY error_rate_pct DESC;

-- 3. Error rate by drug category
SELECT
    drug_category,
    COUNT(*) AS total_fills,
    SUM(is_error) AS errors,
    ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
FROM fills
GROUP BY drug_category
ORDER BY error_rate_pct DESC;

-- 4. Error type breakdown, Night shift specifically
--    (drills into the shift flagged in query #2)
SELECT
    error_type,
    COUNT(*) AS occurrences,
    ROUND(100.0 * COUNT(*) / (SELECT SUM(is_error) FROM fills WHERE shift = 'Night'), 1) AS pct_of_night_errors
FROM fills
WHERE is_error = 1 AND shift = 'Night'
GROUP BY error_type
ORDER BY occurrences DESC;

-- 5. Error rate by daily house volume bucket
--    (tests whether high-volume days strain accuracy)
SELECT
    CASE
        WHEN daily_house_volume <= 50 THEN 'Low (<=50)'
        WHEN daily_house_volume <= 70 THEN 'Medium (51-70)'
        ELSE 'High (71+)'
    END AS volume_bucket,
    COUNT(*) AS total_fills,
    SUM(is_error) AS errors,
    ROUND(100.0 * SUM(is_error) / COUNT(*), 1) AS error_rate_pct
FROM fills
GROUP BY volume_bucket
ORDER BY error_rate_pct DESC;

-- 6. Error type breakdown, overall
SELECT
    error_type,
    COUNT(*) AS occurrences,
    ROUND(100.0 * COUNT(*) / (SELECT SUM(is_error) FROM fills), 1) AS pct_of_errors
FROM fills
WHERE is_error = 1
GROUP BY error_type
ORDER BY occurrences DESC;

-- 7. Errors caught before dispense vs. not (a patient-safety metric)
SELECT
    CASE WHEN caught_before_dispense = 1 THEN 'Caught Before Dispense'
         ELSE 'Not Caught Before Dispense' END AS catch_status,
    COUNT(*) AS error_count,
    ROUND(100.0 * COUNT(*) / (SELECT SUM(is_error) FROM fills), 1) AS pct_of_errors
FROM fills
WHERE is_error = 1
GROUP BY catch_status;

-- 8. Average turnaround time by house
SELECT
    house,
    COUNT(*) AS total_fills,
    ROUND(AVG(turnaround_minutes), 1) AS avg_turnaround_minutes
FROM fills
GROUP BY house
ORDER BY avg_turnaround_minutes DESC;
