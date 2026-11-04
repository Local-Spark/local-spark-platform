"""Tenant-bound anonymous fixtures for local discovery simulation."""

from alembic import op

revision = "0066_reference_candidates"
down_revision = "0065_reference_discovery"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE reference_discoveries
      ADD CONSTRAINT reference_discoveries_tenant_business_id UNIQUE(tenant_id,business_id,id)""")
    op.execute("""CREATE TABLE reference_discovery_candidates (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      discovery_id uuid NOT NULL, fixture_number smallint NOT NULL CHECK(fixture_number BETWEEN 1 AND 3),
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(tenant_id,business_id,discovery_id,fixture_number),
      FOREIGN KEY(tenant_id,business_id,discovery_id)
        REFERENCES reference_discoveries(tenant_id,business_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE reference_discovery_candidates ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_discovery_candidates FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_access ON reference_discovery_candidates TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT,INSERT ON reference_discovery_candidates TO meu_braco_direito_app")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_discovery_candidates) THEN
        RAISE EXCEPTION 'REFERENCE_CANDIDATES_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("DROP TABLE reference_discovery_candidates")
    op.execute("ALTER TABLE reference_discoveries DROP CONSTRAINT reference_discoveries_tenant_business_id")
