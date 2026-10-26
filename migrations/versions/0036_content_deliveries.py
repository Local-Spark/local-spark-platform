"""Private candidate messages and exact-version approval for local publishing."""

from alembic import op

revision = "0036_content_deliveries"
down_revision = "0035_candidate_previews"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE content_deliveries (
      id uuid PRIMARY KEY,
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      source_event_id uuid NOT NULL UNIQUE,
      preview_id uuid UNIQUE,
      kind text NOT NULL CHECK(kind IN ('candidate','clarification')),
      recipient_hash char(64) NOT NULL, recipient_ciphertext text NOT NULL,
      message_body text NOT NULL, provider_message_id text NOT NULL UNIQUE,
      delivery_state text NOT NULL DEFAULT 'delivered'
        CHECK(delivery_state IN ('delivered','failed','uncertain')),
      decision_state text CHECK(decision_state IN ('pending','approved','changes_requested','expired')),
      decision_operation_id uuid UNIQUE, decision_request_hash char(64), review_note text,
      approved_sha256 char(64), approval_digest char(64), caption text,
      scheduled_at timestamptz,
      publish_state text CHECK(publish_state IN ('pending','dispatching','published','unknown','failed')),
      publication_id text UNIQUE,
      publish_owner uuid, publish_lease_until timestamptz,
      publish_fence bigint NOT NULL DEFAULT 0,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      expires_at timestamptz NOT NULL,
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      CHECK((kind='candidate' AND preview_id IS NOT NULL AND decision_state IS NOT NULL)
         OR (kind='clarification' AND preview_id IS NULL AND decision_state IS NULL))
    )""")
    op.execute("CREATE INDEX content_deliveries_due ON content_deliveries(publish_state,scheduled_at,id)")
    op.execute("CREATE INDEX content_deliveries_owner ON content_deliveries(tenant_id,business_id,created_at DESC)")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute("ALTER TABLE content_deliveries ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE content_deliveries FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_content_deliveries ON content_deliveries TO meu_braco_direito_app
      USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""CREATE POLICY worker_content_deliveries ON content_deliveries TO meu_braco_direito_correlator
      USING(true) WITH CHECK(true)""")
    op.execute("GRANT SELECT ON content_deliveries TO meu_braco_direito_app")
    op.execute("""GRANT UPDATE(decision_state,decision_operation_id,decision_request_hash,
      review_note,approved_sha256,approval_digest,
      scheduled_at,publish_state,updated_at) ON content_deliveries TO meu_braco_direito_app""")
    op.execute("GRANT SELECT,INSERT,UPDATE ON content_deliveries TO meu_braco_direito_correlator")


def downgrade():
    op.execute("DROP TABLE content_deliveries")
