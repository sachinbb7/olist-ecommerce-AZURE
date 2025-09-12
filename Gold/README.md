# Grant Synapse access to ADLS (container-level) — Quick README

**Purpose:** Simple, copy-paste steps to grant an **Azure Synapse workspace** read access to a specific **Blob/ADLS Gen2 container** using Azure Portal (Managed Identity). Use this in your repo README so others can follow quickly.

---

# Prerequisites

* You are an **Owner** or have rights to assign roles on the subscription/resource.
* You have an **Azure Synapse workspace** (system-assigned or user-assigned managed identity).
* Know the target **Storage Account** and **Container** names.

---

# Steps (Portal) — assign Blob role at the *container* level

1. **Open the container**

   * Portal → **Storage accounts** → select your storage account.
   * In the storage account menu: **Blob service → Containers**.
   * Click the container you want Synapse to read (e.g., `gold`).

2. **Open Access control (IAM)**

   * With the container selected, click **Access control (IAM)**.

3. **Add role assignment**

   * Click **+ Add → Add role assignment**.

4. **Choose role**

   * For read-only access choose **Storage Blob Data Reader**.
   * For read + write choose **Storage Blob Data Contributor**.

5. **Assign access to the Synapse managed identity**

   * **Option A – If you see "Assign access to: Managed identity":**

     * Set **Assign access to = Managed identity** → **Select members** → choose your **Synapse workspace** → **Review + assign** → **Assign**.
   * **Option B – If you see "Assign access to: Azure AD user, group or service principal":**

     * Keep **Assign access to = Azure AD user, group, or service principal** → **Select members** → search/select your **Synapse workspace (managed identity)** → **Review + assign** → **Assign**.

> **Tip:** Assigning at the **container** scope is recommended to limit access. You can also assign at storage account scope if broader access is needed.

---

# Wait and verify

* **Wait \~5–15 minutes** for RBAC propagation.
* **Verify with Synapse Spark notebook** (after propagation):

```python
# PySpark in Synapse notebook
df = spark.read.format("parquet").load("abfss://<container>@<storage-account>.dfs.core.windows.net/gold/")
display(df.limit(3))
```

* **Or verify with Serverless SQL** by creating a database scoped credential (Managed Identity) and an external data source, then querying.

---

# If ADLS Gen2 (Hierarchical Namespace) is enabled — set ACLs

If HNS is enabled you must also set POSIX ACLs so Synapse identity can list/read directories.

**CLI example (give read+execute on `gold` recursively):**

```bash
# replace variables accordingly
STORAGE_ACCOUNT=<storage-account-name>
CONTAINER=<container-name>
MI_OBJECT_ID=<synapse-managed-identity-object-id>

az storage fs access set-recursive \
  --account-name $STORAGE_ACCOUNT \
  --file-system $CONTAINER \
  --path "gold" \
  --acl "user:$MI_OBJECT_ID:rx,default:user:$MI_OBJECT_ID:rx" \
  --auth-mode login
```

* `rx` on directories allows list + enter; file entries need `r` to read contents. Use `set-recursive` to apply down the folder tree.

---

# Quick troubleshooting & gotchas

* If you see **403**: re-check role scope (container vs account) and ACLs (for HNS).
* If storage has **firewall / private endpoint**: create a **Managed Private Endpoint** from Synapse to the storage account or ensure Synapse workspace network access is allowed.
* If using a **user-assigned managed identity**, select that identity instead of the system one.
* After RBAC/ACL changes, allow **5–15 minutes** for propagation before testing.

---

# Summary (one-liner)

**Grant the Synapse workspace managed identity `Storage Blob Data Reader` on the container (Portal → Container → Access control → Add role assignment), set ADLS ACLs if HNS is enabled, wait \~5–15 minutes, then verify from Synapse with Spark or Serverless SQL.**

---
