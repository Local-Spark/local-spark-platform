"""Owner-readable parent for future reference provider searches.

No runtime role can create or update these rows yet. Dispatch and budget
enforcement need a separate reviewed integration before providers are enabled.
"""

from alembic import op

revision = "0074_reference_places_effect"
down_revision = "0073_reference_score_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_provider_searches (
      id uuid NOT NULL,
      tenant_id uuid NOT NULL,
      business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      operation_id uuid NOT NULL,
      context_version bigint NOT NULL,
      request_mac char(64) NOT NULL CHECK(request_mac ~ '^[0-9a-f]{64}$'),
      state text NOT NULL CHECK(state IN ('pending','completed','failed','uncertain','cancelled','stale')),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      completed_at timestamptz,
      PRIMARY KEY(tenant_id,business_id,id),
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,context_version)
        REFERENCES business_context_versions(tenant_id,business_id,version))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE reference_provider_searches ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_provider_searches FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_reference_provider_search ON reference_provider_searches
      FOR SELECT TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT ON reference_provider_searches TO meu_braco_direito_app")


def downgrade():
    op.execute("LOCK TABLE reference_provider_searches IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_provider_searches) THEN
        RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCHES_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP TABLE reference_provider_searches")
