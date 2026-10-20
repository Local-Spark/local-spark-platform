# Working agreement

Read `docs/PROJECT.md`, `docs/SDD.md` and the active phase SDD in `docs/phases/`
before changing code. Update those documents and `docs/CHANGELOG.md` with scope,
decisions, validation and remaining work in the same change.

- Follow Spotlight-style `app/core`, `app/api/v1`, `app/schemas`, `app/services`.
  Do not introduce its private packages, credentials or schema-per-tenant approach.
- Business logic belongs to services; adapters and routes do not own competing rules.
- Runtime uses PostgreSQL with RLS and restricted roles. Never rely only on a tenant header.
- Every asynchronous effect has a durable operation/event identity. Transactional
  changes include audit/outbox. No network calls while holding row locks.
- Temporal owns workflow execution. Do not add Celery, RabbitMQ or another runner
  for the same processes. No IO inside deterministic workflow functions.
- Add meaningful unit and integration tests. `make ci` must pass with coverage 100%
  including branches. Do not exclude production modules merely to raise coverage.
- Database tests require a dedicated database ending in `_test` and restricted runtime
  logins. Never clean or migrate a user's existing project database for these tests.
- Public/paid API, publication and identity generation require explicitly configured
  credentials and budgets. Foundation tests use local services, never customer content.
- No secrets in git, images, stdout logs or test reports. Logs use stable events and
  allowlisted structured fields; audit and cost ledger remain durable data.
- Inspect existing user changes and do not overwrite them. Never modify `spotlight-api`
  just to implement this new project.
- Features merge in small reviewable slices. A deployed foundation is not a completed v0.
