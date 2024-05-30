# Overview

In this lab, you learn how to use BigQuery to analyze billing data.

## Objectives

In this lab, you learn how to perform the following tasks:

- Sign in to BigQuery from the Cloud Console
- Create a dataset
- Create a table
- Import data from a billing CSV file stored in a bucket
- Run complex queries on a larger dataset


## Use BigQuery to import data

- In the Cloud Console, on the Navigation menu ( Navigation menu icon), click BigQuery.
- If prompted, click Done.
- Click on the View actions icon next to your project ID (starts with qwiklabs-gcp) and click Create dataset.
- Specify the following:
```
Dataset ID:	                                                imported_billing_data
Data location:	                                            US
Default maximum table age (check Enable table expiration):	1 days (Default maximum table age)
```
- Click Create Dataset. You should see `imported_billing_data` in the left pane.
- Click on the View actions icon next to your `imported_billing_data` dataset, and click Open and then click Create Table to create a new table.
- For Source, specify the following, and leave the remaining settings as their defaults:
```
Property	                    Value (type value or select option as specified)
Create table from:	            Google Cloud Storage
Select file from GCS bucket	    cloud-training/archinfra/export-billing-example.csv
File format	                    CSV
```
- For Destination, specify the following, and leave the remaining settings as their defaults:
```
Property	    Value (type value or select option as specified)
Table name	    sampleinfotable
Table type	    Native table
```
- Under Schema check Auto detect.
- Open Advanced options.
- Under Header rows to skip specify 1.
- Click Create Table. After the job is completed, the table appears below the dataset in the left pane.

## Examine the table

- Click sampleinfotable.
- Click Details. As you can see in Number of Rows, this is a relatively small table with 44 rows.
- Click Preview.
- Locate the row that has the Description: Network Internet Ingress from EMEA to Americas.
- Scroll to the Cost column.
- Locate the row that has the Description: Network Internet Egress from Americas to China.

# Compose a simple query

When you reference a table in a query, both the dataset ID and table ID must be specified; the project ID is optional.

All the information you need is available in the BigQuery interface. In the column on the left, you see the dataset ID (imported_billing_data) and table ID (sampleinfotable).
Recall that clicking on the table name brings up the Schema with all of the field names.

Now construct a simple query based on the Cost field.
- Click Compose New Query.
- Paste the following in Query Editor:
```
SELECT * FROM `imported_billing_data.sampleinfotable`
WHERE Cost > 0
```

# Analyze a large billing dataset with SQL

In the next activity, you use BigQuery to analyze a sample dataset with 22,537 lines of billing data.

```
Note: The cloud-training-prod-bucket.arch_infra.billing_data dataset used in this task is shared with the public. 
For more information on public datasets and how to share datasets with the public, refer to the BigQuery public datasets Guide.
```

- For New Query, paste the following in Query Editor, verify that the resulting table has 22,537 lines of billing data.
```
SELECT
  product,
  resource_type,
  start_time,
  end_time,
  cost,
  project_id,
  project_name,
  project_labels_key,
  currency,
  currency_conversion_rate,
  usage_amount,
  usage_unit
FROM
  `cloud-training-prod-bucket.arch_infra.billing_data`
```
- To find the latest 100 records where there were charges (cost > 0), for New Query, paste the following in Query Editor:
```
SELECT
  product,
  resource_type,
  start_time,
  end_time,
  cost,
  project_id,
  project_name,
  project_labels_key,
  currency,
  currency_conversion_rate,
  usage_amount,
  usage_unit
FROM
  `cloud-training-prod-bucket.arch_infra.billing_data`
WHERE
  Cost > 0
ORDER BY end_time DESC
LIMIT
  100
```
- To find the product with the most records in the billing data, for New Query, paste the following in Query Editor:
```
SELECT
  product,
  COUNT(*) AS billing_records
FROM
  `cloud-training-prod-bucket.arch_infra.billing_data`
GROUP BY
  product
ORDER BY billing_records DESC
```
- To find the most frequently used product costing more than 1 dollar, for New Query, paste the following in Query Editor:
```
SELECT
  product,
  COUNT(*) AS billing_records
FROM
  `cloud-training-prod-bucket.arch_infra.billing_data`
WHERE
  cost > 1
GROUP BY
  product
ORDER BY
  billing_records DESC
```
- To find the most commonly charged unit of measure, for Compose New Query, paste the following in Query Editor:
```
SELECT
  usage_unit,
  COUNT(*) AS billing_records
FROM
  `cloud-training-prod-bucket.arch_infra.billing_data`
WHERE cost > 0
GROUP BY
  usage_unit
ORDER BY
  billing_records DESC
```
- To find the product with the highest aggregate cost, for New Query, paste the following in Query Editor:
```
SELECT
  product,
  ROUND(SUM(cost),2) AS total_cost
FROM
  `cloud-training-prod-bucket.arch_infra.billing_data`
GROUP BY
  product
ORDER BY
  total_cost DESC
```
