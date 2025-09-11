# Databricks notebook source
# MAGIC %md
# MAGIC ##Connecting to ADLS to access the data - SILVER Layer

# COMMAND ----------

spark

# COMMAND ----------

#building connection to retrieve data from ADLS

service_credential = "pf_8Q~6bAjVhNPTXJBKrLsYwicZFVx9_-xSQyaDz"
storage_account = "sachinolistecommerce"
application_id = "0eb10387-cd35-4894-b745-2c87d02d2081"
directory_id = "3e7a60e7-389d-4de9-8178-93c9598c0263"

spark.conf.set(f"fs.azure.account.auth.type.{storage_account}.dfs.core.windows.net", "OAuth")
spark.conf.set(f"fs.azure.account.oauth.provider.type.{storage_account}.dfs.core.windows.net", "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")
spark.conf.set(f"fs.azure.account.oauth2.client.id.{storage_account}.dfs.core.windows.net", application_id)
spark.conf.set(f"fs.azure.account.oauth2.client.secret.{storage_account}.dfs.core.windows.net", service_credential)
spark.conf.set(f"fs.azure.account.oauth2.client.endpoint.{storage_account}.dfs.core.windows.net", f"https://login.microsoftonline.com/{directory_id}/oauth2/token")

# COMMAND ----------

#creating common base path
base_path= "abfss://olist-ecommerce@sachinolistecommerce.dfs.core.windows.net/bronze/"

#defining paths
customers_path= base_path+"olist_customers_dataset.csv"
geolocation_path= base_path+"olist_geolocation_dataset.csv"
items_path= base_path+"olist_order_items_dataset.csv"
payments_path= base_path+"olist_order_payments_dataset.csv"
review_path= base_path+"olist_order_reviews_dataset.csv"
orders_path= base_path+"olist_orders_dataset.csv"
products_path= base_path+"olist_products_dataset.csv"
seller_path= base_path+"olist_sellers_dataset.csv"

#creating respective dataframes using spark
customers_df   = spark.read.csv(customers_path,   header=True, inferSchema=True)
geolocation_df = spark.read.csv(geolocation_path, header=True, inferSchema=True)
items_df       = spark.read.csv(items_path,       header=True, inferSchema=True)
review_df      = spark.read.csv(review_path,      header=True, inferSchema=True)
orders_df      = spark.read.csv(orders_path,      header=True, inferSchema=True)
payments_df    = spark.read.csv(payments_path,    header=True, inferSchema=True)
products_df    = spark.read.csv(products_path,    header=True, inferSchema=True)
sellers_df     = spark.read.csv(seller_path,     header=True, inferSchema=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ##**Ingesting Mongo data**

# COMMAND ----------

#importing mongo data from mongoDB

#either install mongo here or install mongo on "Compute- I've install on Compute"
import pymongo

# importing module
from pymongo import MongoClient

#mongoDB connection info -- update the info as per your mongoDB
hostname = "il-mpt.h.filess.io"
database = "aaaaaaak"
port = "61003"
username = "aaaaaaak"
password = "xxxxxxxxxx"

uri = "mongodb://" + username + ":" + password + "@" + hostname + ":" + port + "/" + database

# Connect with the portnumber and host
client = MongoClient(uri)

# Access database
mydatabase = client[database]
mydatabase

# COMMAND ----------

#to check list of collections/tables in the DB
mydatabase.list_collection_names

# COMMAND ----------

#convert mongo data to pandas

import pandas as pd

collection= mydatabase['product_categories']
mongo_df = pd.DataFrame(list(collection.find()))
print(f"Duplicate records : {mongo_df.duplicated().sum()}")
print(f"Null values : {mongo_df.isna().sum().sum()}")


# COMMAND ----------

#dropping _id from mongo data
mongo_df.drop("_id", inplace = True, axis=1 )

mongo_df

# COMMAND ----------

# MAGIC %md
# MAGIC ##**Data Cleaning**

# COMMAND ----------

#Creating custom function to read and understand the duplicates/null values and eventually remove them

from pyspark.sql import functions as F

def clean_dataframe(df, name):
    """
    Print duplicate row fraction and null% per column, then:
      - drop duplicate rows
      - drop rows where ALL columns are null
    Returns: cleaned Spark DataFrame
    """
    print(f"Cleaning {name}")
    total_rows = df.count()
    print(f"Total rows: {total_rows}")
    if total_rows == 0:
        print("Empty DataFrame; nothing to clean.")
        return df

    # duplicate rows fraction
    dedup_count = df.dropDuplicates().count()
    dup_fraction = (total_rows - dedup_count) / total_rows*100.0
    print(f"Duplicate percentage: {dup_fraction:.6f}")

    # null percentage per column
    null_exprs = [
        F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c)
        for c in df.columns
    ]
    null_counts_row = df.agg(*null_exprs).collect()[0].asDict()
    print("Null percentage per column:")
    for col_name, null_count in null_counts_row.items():
        print(f"  {col_name}: {null_count / total_rows:.6f}")

    # cleaning: drop duplicate rows and drop rows where ALL columns are null
    cleaned_df = df.dropDuplicates().na.drop("all")
    cleaned_count = cleaned_df.count()
    print(f"Rows after cleaning: {cleaned_count} (removed {total_rows - cleaned_count})\n")
    return cleaned_df

# Apply to your DataFrames
orders_df_clean = clean_dataframe(orders_df, "orders_df")
items_df_clean = clean_dataframe(items_df, "items_df")
products_df_clean = clean_dataframe(products_df, "products_df")
payments_df_clean = clean_dataframe(payments_df, "payments_df")
review_df_clean = clean_dataframe(review_df, "review_df")
customers_df_clean = clean_dataframe(customers_df, "customers_df")
geolocation_df_clean = clean_dataframe(geolocation_df, "geolocation_df")
sellers_df_clean = clean_dataframe(sellers_df, "sellers_df")


# COMMAND ----------

# MAGIC %md
# MAGIC ##**Validate dtype**

# COMMAND ----------

#convert the datetime columns to datetime format
review_df_clean.withColumn("review_creation_date", F.to_date(F.col("review_creation_date"), "yyyy-MM-dd")).withColumn("review_answer_timestamp", F.to_date(F.col("review_answer_timestamp"), "yyyy-MM-dd"))


# COMMAND ----------

# MAGIC %md
# MAGIC ###**Feature Engineering**

# COMMAND ----------

#check Delivery and delays 

orders_df_clean = orders_df_clean.withColumn("delay_days", F.datediff(F.col("order_delivered_customer_date"), F.col("order_estimated_delivery_date")))
orders_df_clean = orders_df_clean.withColumn("actual_delivery_time", F.datediff(F.col("order_delivered_customer_date"), F.col("order_purchase_timestamp")))
orders_df_clean = orders_df_clean.withColumn("estimated_delivery_time", F.datediff(F.col("order_estimated_delivery_date"), F.col("order_purchase_timestamp")))
orders_df_clean = orders_df_clean.withColumn("delay_percentage", F.round(F.col("delay")/F.col("estimated_delivery_time"),2)) 
orders_df_clean =  orders_df_clean.withColumn("delay", F.col("delay_days") > 0)

display(orders_df_clean)

# COMMAND ----------

# MAGIC %md
# MAGIC ##Joining

# COMMAND ----------

#Joining the tables as per the Olist- Schema.png

orders_customers_df = orders_df_clean.join(
    customers_df_clean,
    orders_df_clean.customer_id == customers_df_clean.customer_id,
    "left"
).drop(customers_df_clean.customer_id)


orders_payments_df = orders_customers_df.join(
    payments_df_clean,
    orders_customers_df["order_id"] == payments_df_clean["order_id"],
    "left"
).drop(payments_df_clean.order_id)

orders_items_df = orders_payments_df.join(
    items_df_clean,
    orders_payments_df["order_id"] == items_df_clean["order_id"],
    "left"
).drop(items_df_clean.order_id)

orders_products_df = orders_items_df.join(
    products_df_clean,
    orders_items_df["product_id"] == products_df_clean["product_id"],
    "left"
).drop(products_df_clean.product_id)

final_df = orders_products_df.join(
    sellers_df_clean,
    orders_products_df["seller_id"] == sellers_df_clean["seller_id"],
    "left"
).drop(sellers_df_clean.seller_id)



# COMMAND ----------

display(final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC **Join Mongo data to retrieve product category name in English**

# COMMAND ----------



# Convert the Pandas DataFrame to a Spark DataFrame
spark_mongo_df = spark.createDataFrame(mongo_df)

# Perform the join operation
final_df = final_df.join(
    spark_mongo_df,
    on="product_category_name",
    how="left"
).drop(spark_mongo_df.product_category_name)

display(final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##**Store the Transformed Data in Silver layer**

# COMMAND ----------

#Make sure to always use alias to avoid duplicate columns or delete the duplicate records before storing the data
final_df.columns

# COMMAND ----------

silver_base_path= "abfss://olist-ecommerce@sachinolistecommerce.dfs.core.windows.net/silver/"

# Save the DataFrame as a table
final_df.write.mode("overwrite").saveAsTable("transformed_df")

# Write the DataFrame to a parquet file
final_df.write.mode("overwrite").parquet(silver_base_path)