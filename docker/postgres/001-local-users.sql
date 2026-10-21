-- Development-only credentials. Never mount this initializer in production.
CREATE ROLE local_spark_runtime LOGIN PASSWORD 'local-spark-app-password' NOSUPERUSER NOBYPASSRLS;
CREATE ROLE local_spark_delivery LOGIN PASSWORD 'local-spark-relay-password' NOSUPERUSER NOBYPASSRLS;
CREATE ROLE local_spark_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE local_spark_relay NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT local_spark_app TO local_spark_runtime;
GRANT local_spark_relay TO local_spark_delivery;
CREATE ROLE local_spark_identity LOGIN PASSWORD 'local-spark-auth-password' NOSUPERUSER NOBYPASSRLS;
CREATE ROLE local_spark_payments LOGIN PASSWORD 'local-spark-billing-password' NOSUPERUSER NOBYPASSRLS;
CREATE DATABASE local_spark_platform_test;
