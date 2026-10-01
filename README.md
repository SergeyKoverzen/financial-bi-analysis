# Financial BI Analysis — Apple, Microsoft & Amazon

## Overview

This project demonstrates an end-to-end financial BI workflow using real public financial data from the U.S. Securities and Exchange Commission (SEC).

The project covers the complete analytical pipeline:

**SEC financial data → Python data preparation → PostgreSQL → SQL analytical layer → Power BI**

The analysis focuses on three major public companies:

- Apple
- Microsoft
- Amazon

The goal is to transform raw financial data into a structured analytical dataset and an interactive Power BI dashboard for financial performance analysis.

---

## Dashboard

### Interactive Power BI Dashboard

[Open Interactive Power BI Dashboard](#)

> Replace the link above with the public Power BI report link after publishing the dashboard.

### Dashboard Pages

The Power BI report contains two analytical pages:

#### 1. Financial Overview

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
