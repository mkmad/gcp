# Overview

In today's competitive environment, organizations need to quickly and easily make decisions based on real-time data. Datastream for BigQuery features seamless replication from operational database sources such as AlloyDB, MySQL, PostgreSQL, and Oracle, directly into BigQuery, Google Cloud's serverless data warehouse. With a serverless, auto-scaling architecture, Datastream allows you to easily set up an ELT (Extract, Load, Transform) pipeline for low-latency data replication enabling real-time insights.

In this hands-on lab you'll deploy Cloud SQL for PostgreSQL database and import a sample data set using the gcloud command line. In the UI you will create and start a Datastream stream and replicate data into BigQuery.

Although you can easily copy and paste commands from the lab to the appropriate place, students should type the commands themselves to reinforce their understanding of the core concepts

# Objectives

- Prepare a Cloud SQL for PostgreSQL instance using the Google Cloud Console
- Import data into the Cloud SQL instance
- Create a Datastream connection profile for the PostgreSQL database
- Create a Datastream connection profile for the BigQuery destination
- Create a Datastream stream and start replication
- Validate that the existing data and changes are replicated correctly into BigQuery

# Create a database for replication

- enable the Cloud SQL API:

```
gcloud services enable sqladmin.googleapis.com
```

- create a Cloud SQL for PostgreSQL database instance:

```
POSTGRES_INSTANCE=postgres-db
DATASTREAM_IPS=IP_ADDRESS
gcloud sql instances create ${POSTGRES_INSTANCE} \
    --database-version=POSTGRES_14 \
    --cpu=2 --memory=10GB \
    --authorized-networks=${DATASTREAM_IPS} \
    --region=REGION \
    --root-password pwd \
    --database-flags=cloudsql.logical_decoding=on
```

# Populate the database with sample data

- Connect to the PostgreSQL database

```
gcloud sql connect postgres-db --user=postgres
```

- create a sample schema and table:

```
CREATE SCHEMA IF NOT EXISTS test;

CREATE TABLE IF NOT EXISTS test.example_table (
id  SERIAL PRIMARY KEY,
text_col VARCHAR(50),
int_col INT,
date_col TIMESTAMP
);

<!-- 
This command modifies settings related to logical replication in a PostgreSQL database.
It's specifically focused on how to identify rows in the table called "example_table" 
(within the "test" schema) when updates or deletes need to be replicated to other 
PostgreSQL databases. 
-->
ALTER TABLE test.example_table REPLICA IDENTITY DEFAULT; 


- insert sample data into the table (1 row):
INSERT INTO test.example_table (text_col, int_col, date_col) VALUES
('hello', 0, '2020-01-01 00:00:00'),
('goodbye', 1, NULL),
('name', -987, NOW()),
('other', 2786, '2021-01-01 00:00:00');
```

# Configure the database for replication

```
CREATE PUBLICATION test_publication FOR ALL TABLES;
ALTER USER POSTGRES WITH REPLICATION;
SELECT PG_CREATE_LOGICAL_REPLICATION_SLOT('test_replication', 'pgoutput');
```

# Create the Datastream resources and start replication

- From the Navigation menu, go to Analytics > Datastream > Connection Profiles

### CreateCreate two connection profiles, one for the PostgreSQL source, and another for the BigQuery destination.

1. PostgreSQL connection profile

    - In the Cloud console, navigate to the Connection Profiles tab and click Create Profile.
    - Select the PostgreSQL connection profile type.
    - Use postgres-cp as the name and ID of the connection profile.
    - Enter the database connection details:
        * The IP and port of the Cloud SQL instance created earlier
        * Region: <REGION>
        * Username: postgres
        * Password: pwd
        * Database: postgres
    - Leave the encryption as NONE, and click CONTINUE.
    - Select the IP allowlisting connectivity method, and click Continue.
    - Click RUN TEST to make sure that Datastream can reach the database.
    - Click Create.

2. BigQuery connection profile

    - In the Cloud console, navigate to the Connection Profiles tab and click Create Profile.
    - Select the BigQuery connection profile type.
    - Use bigquery-cp as the name and ID of the connection profile.
    - Region <REGION>
    - Click Create.

