# Azure Synapse vs Azure Databricks — Quick Guide for Data Analytics

**Purpose:** short, practical notes to help teams choose between **Azure Synapse Analytics** and **Azure Databricks**, plus a quick explanation of **Dedicated vs Serverless SQL pools** and recommended architecture patterns.

---

## Overview

- **Azure Synapse Analytics** — **enterprise analytics** platform combining data integration, dedicated MPP SQL (Dedicated SQL pool), serverless SQL (on-demand), Spark, pipelines, and BI-first features. Great for SQL-heavy reporting, Power BI, and consolidated Azure-native analytics workflows.

- **Azure Databricks** — **managed Apache Spark** platform (lakehouse) focused on data engineering, streaming, and **machine learning**. Features collaborative notebooks, Delta Lake, MLflow, and optimized Spark runtimes.

---

## When to use which

- **Choose Synapse** if:
  - You need **enterprise data warehousing / BI** with many SQL analysts.
  - Tight **Power BI** integration and predictable SQL performance matter.
  - You want both serverless ad-hoc queries and a provisioned MPP warehouse.

- **Choose Databricks** if:
  - You need **data science, ML, or streaming** workloads and collaborative notebooks.
  - You want to adopt a **Delta Lake / lakehouse** pattern for ACID and time-travel on files.
  - High-performance Spark optimizations (Autoloader, optimized runtime) are important.

---

## SQL options in Synapse

- **Dedicated SQL pool (provisioned)**
  - **What:** MPP (provisioned) data warehouse with reserved compute (DWUs / nodes).
  - **Best for:** predictable, low-latency BI reporting and large-scale analytical workloads.
  - **Cost model:** pay for provisioned compute (can pause/resume to save cost).

- **Serverless SQL pool (on-demand)**
  - **What:** query files directly in storage (ADLS/Blob) without provisioning compute.
  - **Best for:** ad-hoc exploration, discovery, and lightweight transformations.
  - **Cost model:** pay per data scanned (optimize by partitioning and file format).

---

## Common architecture patterns

- **Lakehouse (recommended for many orgs):**
  - Ingest & transform with **Databricks** → store curated data as **Delta** on ADLS Gen2 → expose to analytics (Databricks SQL or Synapse dedicated pool / external tables).
  - **Why:** Databricks for ETL/ML; Synapse for BI and serverless exploration.

- **Two-tier analytics:**
  - Use Databricks/Spark to build curated datasets. Load summary / star-schema tables into **Dedicated SQL pool** for fast BI.

- **Serverless for discovery:**
  - Use Synapse Serverless SQL for quick exploration over raw Parquet files; migrate heavy, frequent queries to Dedicated SQL or materialize into Delta tables.

---

## Performance & cost tips

- **Prefer columnar formats**: Parquet or Delta for storage; greatly reduces bytes scanned.
- **Partition** files by date or logical keys to reduce scan footprint.
- **Broadcast** small dimension tables in Spark to avoid big shuffles.
- **Autoscale / job clusters** in Databricks to reduce idle cluster costs.
- **Pause Dedicated SQL** when not in use; monitor DWU usage for right-sizing.

---

## Security & governance

- Both platforms support **Azure AD**, **Managed Identities**, **Private Endpoints**, and RBAC.
- **Databricks Unity Catalog** (if used) provides centralized governance; Synapse integrates with Purview and SQL security controls (row/column permissions).

---

## Quick decision checklist

- Need enterprise BI + Power BI analysts → **Synapse (Dedicated SQL)**  
- Need ML, notebooks, streaming, and lakehouse features → **Databricks**  
- Need both → **Databricks (processing + Delta)** + **Synapse (BI)** or **Databricks SQL** for reporting

---

## Useful links
- Azure Synapse: https://learn.microsoft.com/azure/synapse-analytics/  
- Azure Databricks: https://databricks.com/product/unified-data-analytics-platform

---

## How to use this repo
1. Read this README.  
2. Open `decision-flowchart.svg` to share the short decision flow in a README or docs.  
3. Populate `cost-comparison.md` with your expected workload numbers to compare costs.

