"""Append-only owner edits of generated scripts with a compare-and-swap head."""

from alembic import op

revision = "0033_editorial_script_versions"
down_revision = "0032_video_previews"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE editorial_proposals ADD COLUMN script_version integer NOT NULL
      DEFAULT 1 CHECK(script_version>=1)""")
    op.execute("""GRANT UPDATE(document,script_version,updated_at)
      ON editorial_proposals TO meu_braco_direito_app""")
    op.execute("""CREATE TABLE editorial_script_versions (
      proposal_id uuid NOT NULL REFERENCES editorial_proposals(id) ON DELETE CASCADE,
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      version integer NOT NULL CHECK(version>=1),
      document jsonb NOT NULL, document_hash char(64) NOT NULL,
      context_version integer NOT NULL,
      source_asset_id uuid,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      operation_id uuid, request_hash char(64),
      review_state text CHECK(review_state IN ('accepted','changes_requested')),
      review_operation_id uuid, review_hash char(64),
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(proposal_id,version),
      UNIQUE(tenant_id,business_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE INDEX editorial_script_versions_business
      ON editorial_script_versions(tenant_id,business_id,proposal_id,version)""")
    op.execute("""ALTER TABLE media_previews ADD COLUMN script_version integer NOT NULL
      DEFAULT 1 CHECK(script_version>=1)""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE editorial_script_versions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE editorial_script_versions FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_script_versions ON editorial_script_versions
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})
      WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(review_state,review_operation_id,review_hash)
      ON editorial_script_versions TO meu_braco_direito_app""")


def downgrade():
    op.execute("ALTER TABLE media_previews DROP COLUMN script_version")
    op.execute("DROP TABLE editorial_script_versions")
    op.execute("""REVOKE UPDATE(document,script_version,updated_at)
      ON editorial_proposals FROM meu_braco_direito_app""")
    op.execute("ALTER TABLE editorial_proposals DROP COLUMN script_version")
