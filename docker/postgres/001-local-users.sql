-- Development-only credentials. Never mount this initializer in production.
CREATE ROLE meu_braco_direito_runtime LOGIN PASSWORD 'meu-braco-direito-app-password' NOSUPERUSER NOBYPASSRLS;
CREATE ROLE meu_braco_direito_delivery LOGIN PASSWORD 'meu-braco-direito-relay-password' NOSUPERUSER NOBYPASSRLS;
CREATE ROLE meu_braco_direito_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE meu_braco_direito_relay NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT meu_braco_direito_app TO meu_braco_direito_runtime;
GRANT meu_braco_direito_relay TO meu_braco_direito_delivery;
CREATE ROLE meu_braco_direito_identity LOGIN PASSWORD 'meu-braco-direito-auth-password' NOSUPERUSER NOBYPASSRLS;
CREATE ROLE meu_braco_direito_payments LOGIN PASSWORD 'meu-braco-direito-billing-password' NOSUPERUSER NOBYPASSRLS;
CREATE ROLE meu_braco_direito_meta NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE meu_braco_direito_ingest LOGIN PASSWORD 'meu-braco-direito-meta-password' NOSUPERUSER NOBYPASSRLS;
GRANT meu_braco_direito_meta TO meu_braco_direito_ingest;
CREATE ROLE meu_braco_direito_correlator NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE meu_braco_direito_router LOGIN PASSWORD 'meu-braco-direito-router-password' NOSUPERUSER NOBYPASSRLS;
GRANT meu_braco_direito_correlator TO meu_braco_direito_router;
CREATE DATABASE meu_braco_direito_platform_test;
