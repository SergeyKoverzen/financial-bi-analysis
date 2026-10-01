# Financial BI Analysis — Apple, Microsoft & Amazon

An end-to-end financial BI pipeline built on real public financial data from the U.S. Securities and Exchange Commission (SEC) — not synthetic or sample data.

## Overview

This project is part of my transition from financial accounting and data analysis toward analytics engineering: instead of just building a dashboard, 
it focuses on the full data pipeline behind it — ingestion, validation, modeling, and a clean SQL analytical layer that any BI tool could sit on top of.

The project covers the complete analytical pipeline:

**SEC EDGAR financial data → Python data preparation → PostgreSQL → SQL analytical layer → Power BI**

Why SEC EDGAR

Rather than using a synthetic or Kaggle dataset, this project pulls real, structured XBRL financial data directly from SEC EDGAR's Company Facts API for three public companies:

Apple Inc.
Microsoft Corporation
Amazon.com, Inc.

Working with SEC data introduces real-world data engineering problems that a clean sample dataset wouldn't: inconsistent XBRL tags across companies and fiscal years, 
restated figures, missing periods, and unit/scale mismatches — all of which had to be handled in the ingestion and transformation layer before the data was analysis-ready.

---

## Dashboard

### Interactive Power BI Dashboard

[Open Interactive Power BI Dashboard](#)

> Replace the link above with the public Power BI report link after publishing the dashboard.

### Dashboard Pages

The Power BI report contains two analytical pages:

#### 1. Financial Overview [Open Dashboard](/powerbi/financial-overview.jpg)

Provides a cross-company overview of:

- Revenue
- Gross Profit
- Operating Income
- Net Income
- Gross Margin
- Operating Margin
- Net Margin
- Revenue trends

Companies can be compared across fiscal years using interactive filters.

#### 2. Company Deep Dive

Provides a detailed analysis of the selected company:

- Latest fiscal year financial results
- Revenue and profitability trends
- Gross Margin
- Operating Margin
- Net Margin
- Cash
- Assets
- Equity
- Liabilities
- Long-Term Debt
- Operating Cash Flow
- Dynamic company narrative

The page is controlled by a company selector, allowing the same analytical framework to be used for Apple, Microsoft and Amazon.

---

## Business Questions

The dashboard is designed to answer questions such as:

- How has revenue changed over time?
- How profitable is each company?
- How have gross, operating and net margins evolved?
- How does operating cash flow compare with reported profit?
- How have assets, equity and liabilities changed?
- How has long-term debt changed over time?
- How does the selected company compare with the other companies?
- What are the latest fiscal-year financial results?

---

## Skills Demonstrated

This project was deliberately scoped to show analytics-engineering practices, not just dashboard-building:

Data ingestion from a real external API (SEC EDGAR), including handling nested/inconsistent JSON
Layered SQL data modeling (staging → wide → KPI → BI-ready), rather than one monolithic query
Python for extraction, cleaning and transformation (Pandas)
PostgreSQL as the analytical database
Power BI for the final presentation layer, including a dynamic, selector-driven narrative page

---

## Data Source

The project uses real public financial data from:

**U.S. Securities and Exchange Commission (SEC) EDGAR / Company Facts**

The source provides structured XBRL financial information reported by public companies.

Companies analyzed:

- Apple Inc.
- Microsoft Corporation
- Amazon.com, Inc.

No synthetic financial data was used for the main analysis.

---

## Data Pipeline

```text
SEC Company Facts
       │
       ▼
Python ingestion
       │
       ▼
Data validation & transformation
       │
       ▼
CSV analytical datasets
       │
       ▼
PostgreSQL
       │
       ├── staging.financials
       │
       ▼
SQL analytical layer
       │
       ├── analytics.financials_wide
       ├── analytics.financial_kpis
       └── analytics.bi_financials
       │
       ▼
Power BI
       │
       ├── Financial Overview
       └── Company Deep Dive
