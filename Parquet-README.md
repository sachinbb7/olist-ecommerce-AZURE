# **Ingest .parquet to ADF — use *Binary* format (not Parquet)**

**To ingest the `.parquet` file to ADF, use the format as `Binary` instead of `Parquet`.**
This tells ADF to treat the HTTP source as opaque bytes (no parsing) so you can stage the file to a seekable store (Blob/ADLS) that supports random reads.

---

# **Recommended ADF pipeline fix (two-copy approach)**

## **Create these datasets**

* **Source dataset (HTTP)** — connector: **HTTP (or REST)**.
  **Set format = `Binary`** (not Parquet or Delimited). Point this to your raw GitHub URL.
  **Why:** ADF will download the raw bytes without trying to parse them.

* **Staging dataset (Blob or ADLS Gen2)** — connector: **Azure Blob Storage** or **Azure Data Lake Storage Gen2**.
  **Set format = `Binary`**. Choose the container/folder where you’ll temporarily store the file.

* **Final dataset (ADLS / Blob)** — connector: **ADLS/Blob**.

  * If final file should be **Parquet**, configure this dataset as **Parquet**.
  * If final file should be **CSV**, configure this dataset as **DelimitedText** (CSV).

---

# **Pipeline arrangement**

## **Copy Activity #1 — *HTTP → Staging***

* **Source:** HTTP dataset; **format = Binary**.
* **Sink:** Staging dataset (Blob/ADLS); **format = Binary**.
* **Purpose:** **move the raw file into a storage system that supports random reads and preview**.
  This is a **binary copy** — **no parsing, no schema mapping**.

## **Copy Activity #2 — *Staging → ADLS final***

* **Source:** Staged file on Blob/ADLS (dataset format = **Parquet**).
* **Sink:** Final dataset (Parquet or **CSV/DelimitedText** depending on your goal).
* If converting **Parquet → CSV**, set the Sink dataset format to **DelimitedText** and configure column mappings (or rely on Auto-mapping).
* **Now ADF can preview, parse and transform because the source is storage that supports range reads.**

---

# **Why this works**

* **ADF preview/parsing and some connectors require random byte-range reads.**
* **Blob/ADLS support byte-range (seekable) reads; many HTTP servers (including raw GitHub URLs) do not.**
* **Staging gives ADF a seekable source** so Parquet metadata/footer and row groups can be accessed correctly.

---

**Tip:** Use a deterministic staged path (or pipeline parameter) for the staged blob (e.g. `staging/olist_geolocation_dataset.parquet`) so Copy #2 can reliably find the file.
