
# Materialized Tables in Synapse using CETAS

This guide explains how **Materialized Tables** can be built in **Azure Synapse Analytics** using **CETAS (Create External Table As Select)**, and how the approach differs between **Dedicated SQL Pool** and **Serverless SQL Pool**.

---

## 🔹 What is a Materialized Table?
- A **Materialized Table** is a physical table where the **results of a query are pre-computed and stored**.  
- Queries against a materialized table are **much faster** than scanning raw data files repeatedly.  
- Unlike a normal view or external table:
  - **Regular View / External Table** → always fresh, but slower (scans files every query).  
  - **Materialized Table (via CETAS/CTAS)** → precomputed snapshot, much faster, but must be **refreshed manually**.

---

## 🔹 CETAS in Synapse

`CETAS` = **Create External Table As Select**.  
It allows you to:
1. Run a query over existing data.  
2. Write the query results out to **Azure Data Lake (ADLS/Blob)** as **Parquet/CSV**.  
3. Register an **External Table** pointing to those files.

This pattern **materializes the query output** into storage, so future queries just read the files instead of re-running the computation.

---

## 🔹 Serverless vs Dedicated Pools

### 1. Serverless SQL Pool
- Serverless is **pay-per-query** (charges per TB scanned).  
- External tables are **pointers to files** in ADLS.  
- You can use **CETAS** to materialize a heavy query into new Parquet files.  
- Pros:
  - Reduce costs by avoiding repeated full scans.  
  - Store optimized/partitioned data for reuse.  
- Cons:
  - Output is just files in ADLS (no true “managed” table).  
  - Must refresh manually when upstream data changes.  

**Example:**
```sql
-- Materialize customer-level aggregates into ADLS
CREATE EXTERNAL TABLE ext_customer_orders
WITH (
    LOCATION = 'gold/customer_orders/',
    DATA_SOURCE = GoldData,
    FILE_FORMAT = ParquetFormat
)
AS
SELECT customer_id, COUNT(*) AS total_orders, SUM(payment_value) AS total_spent
FROM OPENROWSET(
    BULK 'silver/*.parquet',
    DATA_SOURCE = 'GoldData',
    FORMAT = 'PARQUET'
) AS src
GROUP BY customer_id;
````

This writes Parquet files to `gold/customer_orders/` in ADLS and registers `ext_customer_orders`.

---

### 2. Dedicated SQL Pool

* Dedicated pools are **always-on provisioned resources**.
* Tables are **physically stored inside Synapse storage** (not just external pointers).
* To materialize data, you can use **CTAS** (Create Table As Select) or **CETAS** if writing to ADLS.
* Pros:

  * High performance, optimized storage (columnstore, distribution).
  * Supports indexing, partitioning, statistics.
* Cons:

  * Consumes dedicated pool storage.
  * You pay for provisioned compute, even if idle.

**Example (Dedicated CTAS):**

```sql
-- Materialize into a dedicated table
CREATE TABLE customer_orders
WITH (
    DISTRIBUTION = HASH(customer_id),
    CLUSTERED COLUMNSTORE INDEX
)
AS
SELECT customer_id, COUNT(*) AS total_orders, SUM(payment_value) AS total_spent
FROM orders
GROUP BY customer_id;
```

This creates a **materialized table inside Dedicated Pool storage** for high-performance querying.

---

## 🔹 When to Use CETAS / Materialized Tables

* Heavy aggregations or joins reused by many reports.
* Frequently accessed BI dashboards (avoid rescanning raw data).
* Scenarios where you want to **optimize cost/performance** trade-offs:

  * Use CETAS in **Serverless** to reduce TB scanned costs.
  * Use CTAS/CETAS in **Dedicated** to precompute facts for reporting.

---

## 🔹 Best Practices

1. **Partition outputs** (by date, region, etc.) to improve query pruning.
2. **Compress outputs** with Parquet or ORC for performance.
3. **Refresh strategy**:

   * Re-run CETAS daily/hourly to overwrite outputs.
   * Or write to versioned folders (`gold/customer_orders/2025-09-12/`) for snapshotting.
4. **Use Views on top of CETAS outputs** to provide consistent schema to consumers.
5. **Keep raw data read-only** (in `bronze` / `silver`) — only materialize to curated `gold`.

---

## 🔹 Summary

| Feature             | Serverless SQL Pool (CETAS) | Dedicated SQL Pool (CTAS / CETAS)        |
| ------------------- | --------------------------- | ---------------------------------------- |
| Storage location    | ADLS (external files)       | Synapse internal storage                 |
| Cost model          | Pay per TB scanned          | Pay per DWU hour (provisioned)           |
| Use case            | Materialize raw → curated   | High-performance, persistent tables      |
| Performance benefit | Avoid re-scanning raw files | Optimized storage, indexes, distribution |
| Refresh needed?     | Yes (manual or scheduled)   | Yes (ETL refresh or incremental load)    |

---

✅ **Rule of thumb**:

* Use **Serverless + CETAS** for *cheap, read-optimized snapshots* in ADLS.
* Use **Dedicated + CTAS/CETAS** for *high-performance managed tables* in Synapse storage.

```

---
