---Since the basic profiling and transformation are already performed on Databricks, we will just push this view into ADLS as external table
---Since we already have the database olist-ecommerce, we are ignoring the create database as per CETAS syntax


CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'xxxxx';

CREATE DATABASE SCOPED CREDENTIAL [yyyyy] WITH IDENTITY = 'Managed Identity';
GO

CREATE EXTERNAL FILE FORMAT [ParquetFF] WITH (
    FORMAT_TYPE = PARQUET,
    DATA_COMPRESSION = 'org.apache.hadoop.io.compress.SnappyCodec'
);
GO

CREATE EXTERNAL DATA SOURCE gold WITH (
    LOCATION = 'https://sachinolistecommerce.dfs.core.windows.net/olist-ecommerce/gold/',
    CREDENTIAL = [yyyy]
);
GO

CREATE EXTERNAL TABLE gold.finals WITH (
        LOCATION = 'serving_layer',
        DATA_SOURCE = [gold],
        FILE_FORMAT = [ParquetFF]
) AS
SELECT * FROM gold.final
GO
