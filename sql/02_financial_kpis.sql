-- ============================================================
-- 02_financial_kpis.sql
-- Financial BI Analysis
-- Calculate financial KPIs for BI reporting
-- ============================================================


-- ============================================================
-- 1. Financial KPI layer
-- ============================================================

CREATE OR REPLACE VIEW analytics.financial_kpis AS

WITH base AS (

    SELECT
        company,
        fiscal_year,
        revenue,
        gross_profit,
        operating_income,
        net_income,
        operating_cash_flow,
        assets,
        liabilities,
        equity,
        cash,
        long_term_debt,

        LAG(revenue) OVER (
            PARTITION BY company
            ORDER BY fiscal_year
        ) AS previous_revenue

    FROM analytics.financials_wide
)

SELECT
    company,
    fiscal_year,

    revenue,
    gross_profit,
    operating_income,
    net_income,
    operating_cash_flow,

    assets,
    liabilities,
    equity,
    cash,
    long_term_debt,

    -- Revenue growth
    CASE
        WHEN previous_revenue IS NULL
             OR previous_revenue = 0
        THEN NULL
        ELSE
            (revenue - previous_revenue)
            / previous_revenue * 100
    END AS revenue_growth_yoy_pct,

    -- Gross margin
    CASE
        WHEN revenue IS NULL
             OR revenue = 0
        THEN NULL
        ELSE
            gross_profit / revenue * 100
    END AS gross_margin_pct,

    -- Operating margin
    CASE
        WHEN revenue IS NULL
             OR revenue = 0
        THEN NULL
        ELSE
            operating_income / revenue * 100
    END AS operating_margin_pct,

    -- Net margin
    CASE
        WHEN revenue IS NULL
             OR revenue = 0
        THEN NULL
        ELSE
            net_income / revenue * 100
    END AS net_margin_pct,

    -- Operating cash flow margin
    CASE
        WHEN revenue IS NULL
             OR revenue = 0
        THEN NULL
        ELSE
            operating_cash_flow / revenue * 100
    END AS ocf_margin_pct,

    -- Debt to equity
    CASE
        WHEN equity IS NULL
             OR equity = 0
        THEN NULL
        ELSE
            long_term_debt / equity
    END AS debt_to_equity,

    -- Return on assets
    CASE
        WHEN assets IS NULL
             OR assets = 0
        THEN NULL
        ELSE
            net_income / assets * 100
    END AS roa_pct,

    -- Return on equity
    CASE
        WHEN equity IS NULL
             OR equity = 0
        THEN NULL
        ELSE
            net_income / equity * 100
    END AS roe_pct

FROM base;


-- ============================================================
-- 2. Final Power BI dataset
-- ============================================================

CREATE OR REPLACE VIEW analytics.bi_financials AS

SELECT
    company,
    fiscal_year,

    revenue,
    gross_profit,
    operating_income,
    net_income,
    operating_cash_flow,

    assets,
    liabilities,
    equity,
    cash,
    long_term_debt,

    revenue_growth_yoy_pct,
    gross_margin_pct,
    operating_margin_pct,
    net_margin_pct,
    ocf_margin_pct,
    debt_to_equity,
    roa_pct,
    roe_pct

FROM analytics.financial_kpis;
