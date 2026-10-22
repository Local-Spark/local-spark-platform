-- Development-only, idempotent bootstrap for an existing PostgreSQL volume.
-- Run as the local cluster administrator; never use this password in staging/production.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='local_spark_meta') THEN
    CREATE ROLE local_spark_meta NOLOGIN NOSUPERUSER NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='local_spark_ingest') THEN
    CREATE ROLE local_spark_ingest LOGIN PASSWORD 'local-spark-meta-password' NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;
GRANT local_spark_meta TO local_spark_ingest;
