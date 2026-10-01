-- ============================================================
-- 01_financials_wide.sql
-- Financial BI Analysis
-- Transform staging financial data into a BI-friendly format
-- ============================================================

CREATE OR REPLACE VIEW analytics.financials_wide AS

SELECT
    company,
    fiscal_year,

    MAX(value) FILTER (
        WHERE metric = 'Revenue'
    ) AS revenue,

    MAX(value) FILTER (
        WHERE metric = 'Gross Profit'
    ) AS gross_profit,

    MAX(value) FILTER (
        WHERE metric = 'Operating Income'
    ) AS operating_income,

    MAX(value) FILTER (
        WHERE metric = 'Net Income'
    ) AS net_income,

    MAX(value) FILTER (
        WHERE metric = 'Operating Cash Flow'
    ) AS operating_cash_flow,

    MAX(value) FILTER (
        WHERE metric = 'Assets'
    ) AS assets,

    MAX(value) FILTER (
        WHERE metric = 'Liabilities'
    ) AS liabilities,

    MAX(value) FILTER (
        WHERE metric = 'Equity'
    ) AS equity,

    MAX(value) FILTER (
        WHERE metric = 'Cash'
    ) AS cash,

    MAX(value) FILTER (
        WHERE metric = 'Long Term Debt'
    ) AS long_term_debt

FROM staging.financials

GROUP BY
    company,
    fiscal_year;
