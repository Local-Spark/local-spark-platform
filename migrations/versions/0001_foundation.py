"""Shared tables, mandatory RLS, narrow relay role and transactional event foundations."""

from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_app') THEN
            CREATE ROLE meu_braco_direito_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_relay') THEN
            CREATE ROLE meu_braco_direito_relay NOLOGIN NOSUPERUSER NOBYPASSRLS;
        END IF;
    END $$""")
    op.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA public TO meu_braco_direito_app, meu_braco_direito_relay")
    statements = [
        """CREATE TABLE tenants (
            id uuid PRIMARY KEY, name varchar(120) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now())""",
        """CREATE TABLE memberships (
            tenant_id uuid NOT NULL REFERENCES tenants(id), actor_id uuid NOT NULL,
            role text NOT NULL CHECK(role IN ('owner','editor','viewer')),
            active boolean NOT NULL DEFAULT true, PRIMARY KEY(tenant_id, actor_id))""",
        """CREATE TABLE businesses (
            id uuid NOT NULL, tenant_id uuid NOT NULL REFERENCES tenants(id),
            name varchar(120) NOT NULL CHECK(length(trim(name)) > 0), timezone text NOT NULL,
            row_version bigint NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY(tenant_id, id))""",
        """CREATE TABLE idempotency_records (
            tenant_id uuid NOT NULL REFERENCES tenants(id), scope text NOT NULL,
            key varchar(128) NOT NULL, request_hash char(64) NOT NULL, operation_id uuid NOT NULL,
            response jsonb, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,scope,key))""",
        """CREATE TABLE outbox_events (
            id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id),
            event_type text NOT NULL CHECK(event_type='business.created'), payload jsonb NOT NULL,
            state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','leased','delivered','failed')),
            available_at timestamptz NOT NULL DEFAULT now(), lease_until timestamptz, owner_id uuid,
            fencing_token bigint NOT NULL DEFAULT 0, attempts integer NOT NULL DEFAULT 0,
            delivered_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(tenant_id,id))""",
        """CREATE TABLE audit_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES tenants(id),
            actor_id uuid NOT NULL, operation_id uuid NOT NULL, action text NOT NULL,
            resource_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(tenant_id,operation_id,action))""",
        """CREATE TABLE processed_events (
            tenant_id uuid NOT NULL REFERENCES tenants(id), event_id uuid NOT NULL,
            processed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,event_id),
            FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""",
        "CREATE INDEX businesses_tenant_cursor ON businesses(tenant_id,id)",
        "CREATE INDEX outbox_pending ON outbox_events(available_at,id) WHERE state IN ('pending','leased')",
    ]
    for statement in statements:
        op.execute(statement)
    for table in (
        "tenants",
        "memberships",
        "businesses",
        "idempotency_records",
        "outbox_events",
        "audit_events",
        "processed_events",
    ):
        column = "id" if table == "tenants" else "tenant_id"
        predicate = f"{column} = nullif(current_setting('app.tenant_id',true),'')::uuid"
        if table == "memberships":
            predicate += " AND actor_id = nullif(current_setting('app.actor_id',true),'')::uuid"
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} TO meu_braco_direito_app "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
    op.execute("GRANT SELECT ON tenants, memberships, alembic_version TO meu_braco_direito_app")
    op.execute("GRANT SELECT, INSERT ON businesses, audit_events, processed_events TO meu_braco_direito_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON idempotency_records, outbox_events TO meu_braco_direito_app")
    op.execute("GRANT SELECT, UPDATE ON outbox_events TO meu_braco_direito_relay")
    op.execute(
        "CREATE POLICY relay_delivery ON outbox_events TO meu_braco_direito_relay USING (true) WITH CHECK (true)"
    )


def downgrade():
    for table in (
        "processed_events",
        "audit_events",
        "outbox_events",
        "idempotency_records",
        "businesses",
        "memberships",
        "tenants",
    ):
        op.execute(f"DROP TABLE {table}")
    # Roles are operational resources and deliberately survive schema rollback.
