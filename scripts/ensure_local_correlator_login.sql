-- Development-only bootstrap for a PostgreSQL volume created before F02.2b.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_router') THEN
    CREATE ROLE meu_braco_direito_router LOGIN PASSWORD 'meu-braco-direito-router-password' NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;
GRANT meu_braco_direito_correlator TO meu_braco_direito_router;
