"""Versioned kit applied to a business and private owner-approved logos."""

from alembic import op

revision = "0037_brand_kits"
down_revision = "0036_content_deliveries"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE business_brand_kit_heads (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      version integer NOT NULL DEFAULT 0 CHECK(version>=0),
      confirmed_version integer CHECK(confirmed_version>0 AND confirmed_version<=version),
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE business_brand_kit_versions (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      version integer NOT NULL CHECK(version>0),
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash char(64) NOT NULL, state text NOT NULL CHECK(state IN ('draft','confirmed')),
      document jsonb NOT NULL, response jsonb,
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,version),
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES business_brand_kit_heads(tenant_id,business_id))""")
    op.execute("""CREATE TABLE business_brand_kit_logos (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash char(64) NOT NULL, object_key text NOT NULL UNIQUE,
      sha256 char(64) NOT NULL, mime_type text NOT NULL CHECK(mime_type='image/png'),
      size_bytes integer NOT NULL CHECK(size_bytes>0 AND size_bytes<=4194304),
      state text NOT NULL CHECK(state IN ('pending','ready','deleting')),
      upload_lease_until timestamptz,
      delete_owner uuid, delete_lease_until timestamptz,
      delete_fencing_token bigint NOT NULL DEFAULT 0,
      rights_scope text NOT NULL CHECK(rights_scope='business_brand_confirmed'),
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("business_brand_kit_heads", "business_brand_kit_versions", "business_brand_kit_logos"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_brand_kit ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(version,confirmed_version)
      ON business_brand_kit_heads TO meu_braco_direito_app""")
    op.execute("GRANT SELECT,INSERT,UPDATE(response) ON business_brand_kit_versions TO meu_braco_direito_app")
    op.execute("""GRANT SELECT,INSERT,DELETE,
      UPDATE(state,upload_lease_until,delete_owner,delete_lease_until,delete_fencing_token)
      ON business_brand_kit_logos TO meu_braco_direito_app""")
    op.execute("ALTER TABLE editorial_proposals ADD COLUMN brand_kit_version integer")
    op.execute("ALTER TABLE editorial_proposals ADD COLUMN brand_kit_document jsonb")
    op.execute("""ALTER TABLE editorial_proposals ADD CONSTRAINT proposal_brand_kit_snapshot
      CHECK((brand_kit_version IS NULL AND brand_kit_document IS NULL)
        OR (brand_kit_version>0 AND brand_kit_document IS NOT NULL))""")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type IN ('business.created','brand_kit.changed'))""")


def downgrade():
    op.execute("ALTER TABLE editorial_proposals DROP CONSTRAINT proposal_brand_kit_snapshot")
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN brand_kit_document")
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN brand_kit_version")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type='business.created')""")
    op.execute("DROP TABLE business_brand_kit_logos")
    op.execute("DROP TABLE business_brand_kit_versions")
    op.execute("DROP TABLE business_brand_kit_heads")
