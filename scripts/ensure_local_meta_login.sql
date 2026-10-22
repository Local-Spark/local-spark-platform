-- Development-only, idempotent bootstrap for an existing PostgreSQL volume.
-- Run as the local cluster administrator; never use this password in staging/production.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_meta') THEN
    CREATE ROLE meu_braco_direito_meta NOLOGIN NOSUPERUSER NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_ingest') THEN
    CREATE ROLE meu_braco_direito_ingest LOGIN PASSWORD 'meu-braco-direito-meta-password' NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;
GRANT meu_braco_direito_meta TO meu_braco_direito_ingest;
