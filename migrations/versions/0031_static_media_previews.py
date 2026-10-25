"""Durable, tenant-scoped requests and private artifacts for static previews."""

from alembic import op

revision = "0031_static_media_previews"
down_revision = "0030_editorial_script_review"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE media_previews (
      id uuid PRIMARY KEY,
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      proposal_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      operation_id uuid NOT NULL, request_hash char(64) NOT NULL,
      render_key char(64) NOT NULL, template_version integer NOT NULL DEFAULT 1,
      context_version integer NOT NULL,
      source_asset_id uuid,
      fact_ids jsonb NOT NULL,
      state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','rendering','completed','failed','purging')),
      error_code text, object_key text, sha256 char(64),
      width integer, height integer,
      attempts integer NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 3),
      dispatch_owner uuid, dispatch_lease_until timestamptz,
      dispatch_fence bigint NOT NULL DEFAULT 0,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      expires_at timestamptz NOT NULL,
      UNIQUE(tenant_id,business_id,operation_id),
      UNIQUE(tenant_id,business_id,render_key),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("CREATE INDEX media_previews_due ON media_previews(state,created_at,id)")
    op.execute("CREATE INDEX media_previews_owner ON media_previews(tenant_id,business_id,created_at DESC)")
    op.execute("CREATE INDEX media_previews_expiry ON media_previews(expires_at,id)")
    op.execute(
        "CREATE INDEX media_previews_source ON media_previews(source_asset_id) WHERE source_asset_id IS NOT NULL"
    )
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE media_previews ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE media_previews FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_media_previews ON media_previews TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""CREATE POLICY worker_media_previews ON media_previews TO meu_braco_direito_correlator
      USING(true) WITH CHECK(true)""")
    op.execute("GRANT SELECT,INSERT ON media_previews TO meu_braco_direito_app")
    op.execute("""GRANT SELECT,DELETE,UPDATE(state,error_code,object_key,sha256,width,height,attempts,
      dispatch_owner,dispatch_lease_until,dispatch_fence,updated_at)
      ON media_previews TO meu_braco_direito_correlator""")
    op.execute("GRANT SELECT(name) ON businesses TO meu_braco_direito_correlator")
    op.execute("GRANT SELECT(brand_color) ON business_profiles TO meu_braco_direito_correlator")
    op.execute("""CREATE POLICY worker_context_head ON business_context_heads FOR SELECT
      TO meu_braco_direito_correlator USING(true)""")
    op.execute("""GRANT SELECT(tenant_id,business_id,version) ON business_context_heads
      TO meu_braco_direito_correlator""")


def downgrade():
    op.execute(
        "REVOKE SELECT(tenant_id,business_id,version) ON business_context_heads FROM meu_braco_direito_correlator"
    )
    op.execute("DROP POLICY worker_context_head ON business_context_heads")
    op.execute("REVOKE SELECT(brand_color) ON business_profiles FROM meu_braco_direito_correlator")
    op.execute("REVOKE SELECT(name) ON businesses FROM meu_braco_direito_correlator")
    op.execute("DROP TABLE media_previews")
