-- ============================================================
-- 03_validation_checks.sql
-- Financial BI Analysis
-- Data quality and analytical layer validation
-- ============================================================


-- ============================================================
-- CHECK 1
-- Expected companies
-- ============================================================

SELECT DISTINCT company
FROM staging.financials
WHERE company NOT IN (
    'Apple',
    'Microsoft',
    'Amazon'
);


-- ============================================================
-- CHECK 2
-- Missing key fields
-- ============================================================

SELECT *
FROM staging.financials
WHERE company IS NULL
   OR fiscal_year IS NULL
   OR metric IS NULL
   OR value IS NULL;


-- ============================================================
-- CHECK 3
-- Duplicate financial observations
-- ============================================================

SELECT
    company,
    fiscal_year,
    metric,
    COUNT(*) AS duplicate_count
FROM staging.financials
GROUP BY
    company,
    fiscal_year,
    metric
HAVING COUNT(*) > 1;


-- ============================================================
-- CHECK 4
-- Invalid units
-- ============================================================

SELECT *
FROM staging.financials
WHERE unit <> 'USD'
   OR unit IS NULL;


-- ============================================================
-- CHECK 5
-- Invalid fiscal year
-- ============================================================

SELECT *
FROM staging.financials
WHERE fiscal_year < 2000
   OR fiscal_year > 2100;


-- ============================================================
-- CHECK 6
-- Analytical layer missing revenue
-- ============================================================

SELECT *
FROM analytics.financials_wide
WHERE revenue IS NULL;


-- ============================================================
-- CHECK 7
-- Analytical layer missing key profitability metrics
-- ============================================================

SELECT *
FROM analytics.financials_wide
WHERE gross_profit IS NULL
   OR operating_income IS NULL
   OR net_income IS NULL;


-- ============================================================
-- CHECK 8
-- Gross margin calculation
-- ============================================================

SELECT
    company,
    fiscal_year,
    revenue,
    gross_profit,
    gross_profit / NULLIF(revenue, 0) * 100
        AS expected_gross_margin
FROM analytics.financials_kpis
WHERE revenue IS NOT NULL
  AND gross_profit IS NOT NULL
  AND ABS(
        gross_profit / NULLIF(revenue, 0) * 100
        - gross_margin_pct
      ) > 0.01;


-- ============================================================
-- CHECK 9
-- Operating margin calculation
-- ============================================================

SELECT
    company,
    fiscal_year
FROM analytics.financial_kpis
WHERE revenue IS NOT NULL
  AND operating_income IS NOT NULL
  AND ABS(
        operating_income / NULLIF(revenue, 0) * 100
        - operating_margin_pct
      ) > 0.01;


-- ============================================================
-- CHECK 10
-- Net margin calculation
-- ============================================================

SELECT
    company,
    fiscal_year
FROM analytics.financial_kpis
WHERE revenue IS NOT NULL
  AND net_income IS NOT NULL
  AND ABS(
        net_income / NULLIF(revenue, 0) * 100
        - net_margin_pct
      ) > 0.01;


-- ============================================================
-- CHECK 11
-- OCF margin calculation
-- ============================================================

SELECT
    company,
    fiscal_year
FROM analytics.financial_kpis
WHERE revenue IS NOT NULL
  AND operating_cash_flow IS NOT NULL
  AND ABS(
        operating_cash_flow / NULLIF(revenue, 0) * 100
        - ocf_margin_pct
      ) > 0.01;


-- ============================================================
-- CHECK 12
-- Debt-to-equity calculation
-- ============================================================

SELECT
    company,
    fiscal_year
FROM analytics.financial_kpis
WHERE equity IS NOT NULL
  AND long_term_debt IS NOT NULL
  AND ABS(
        long_term_debt / NULLIF(equity, 0)
        - debt_to_equity
      ) > 0.01;


-- ============================================================
-- CHECK 13
-- ROA calculation
-- ============================================================

SELECT
    company,
    fiscal_year
FROM analytics.financial_kpis
WHERE assets IS NOT NULL
  AND net_income IS NOT NULL
  AND ABS(
        net_income / NULLIF(assets, 0) * 100
        - roa_pct
      ) > 0.01;


-- ============================================================
-- CHECK 14
-- ROE calculation
-- ============================================================

SELECT
    company,
    fiscal_year
FROM analytics.financial_kpis
WHERE equity IS NOT NULL
  AND net_income IS NOT NULL
  AND ABS(
        net_income / NULLIF(equity, 0) * 100
        - roe_pct
      ) > 0.01;


-- ============================================================
-- CHECK 15
-- Final dataset overview
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT company) AS companies,
    MIN(fiscal_year) AS first_fiscal_year,
    MAX(fiscal_year) AS last_fiscal_year
FROM analytics.bi_financials;


-- ============================================================
-- CHECK 16
-- Rows by company
-- ============================================================

SELECT
    company,
    COUNT(*) AS rows
FROM analytics.bi_financials
GROUP BY company
ORDER BY company;
