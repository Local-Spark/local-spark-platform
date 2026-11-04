"""Owner-indicated Instagram references, isolated from confirmed business facts."""

from alembic import op

revision = "0062_owner_references"
down_revision = "0061_visual_recipe"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE owner_references (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), instagram_handle varchar(30) NOT NULL,
      note varchar(500), created_at timestamptz NOT NULL DEFAULT now(), removed_at timestamptz,
      UNIQUE(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE UNIQUE INDEX owner_reference_active_handle
      ON owner_references(tenant_id,business_id,instagram_handle) WHERE removed_at IS NULL""")
    op.execute("""CREATE TABLE owner_reference_operations (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, operation_id uuid NOT NULL,
      reference_id uuid NOT NULL, request_hash char(64) NOT NULL,
      PRIMARY KEY(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,reference_id) REFERENCES owner_references(tenant_id,business_id,id)
        DEFERRABLE INITIALLY DEFERRED)""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("owner_references", "owner_reference_operations"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_access ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT,INSERT,UPDATE(removed_at) ON owner_references TO meu_braco_direito_app")
    op.execute("GRANT SELECT,INSERT ON owner_reference_operations TO meu_braco_direito_app")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM owner_references) THEN
        RAISE EXCEPTION 'OWNER_REFERENCES_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("DROP TABLE owner_reference_operations")
    op.execute("DROP TABLE owner_references")
