"""Owner-initiated, sender-proven WhatsApp channel linking."""

from alembic import op

revision = "0014_whatsapp_channel_link"
down_revision = "0013_whatsapp_inbox"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE whatsapp_inbox ADD COLUMN sender_hash char(64)")
    op.execute("""CREATE INDEX whatsapp_inbox_sender_recent ON whatsapp_inbox(sender_hash,received_at DESC)
      WHERE event_kind='message' AND sender_hash IS NOT NULL""")
    op.execute("""CREATE TABLE whatsapp_link_challenges (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_id uuid NOT NULL, token_hash char(64) NOT NULL UNIQUE,
      sender_hash char(64) NOT NULL,
      state text NOT NULL CHECK(state IN ('pending','linked','cancelled')),
      created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL,
      linked_at timestamptz,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES business_profiles(tenant_id,business_id))""")
    op.execute("""CREATE TABLE whatsapp_channel_links (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      sender_hash char(64) NOT NULL, proof_event_id uuid NOT NULL,
      active boolean NOT NULL DEFAULT true,
      linked_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES business_profiles(tenant_id,business_id))""")
    op.execute("CREATE UNIQUE INDEX whatsapp_one_active_sender ON whatsapp_channel_links(sender_hash) WHERE active")
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    for table in ("whatsapp_link_challenges", "whatsapp_channel_links"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_channel ON {table} TO local_spark_app
          USING(tenant_id={tenant} AND EXISTS(SELECT 1 FROM memberships m
            WHERE m.tenant_id={table}.tenant_id AND m.actor_id={actor}
              AND m.role='owner' AND m.active))
          WITH CHECK(tenant_id={tenant} AND EXISTS(SELECT 1 FROM memberships m
            WHERE m.tenant_id={table}.tenant_id AND m.actor_id={actor}
              AND m.role='owner' AND m.active))""")
        op.execute(f"GRANT SELECT,INSERT,UPDATE ON {table} TO local_spark_app")


def downgrade():
    op.execute("DROP TABLE whatsapp_channel_links")
    op.execute("DROP TABLE whatsapp_link_challenges")
    op.execute("DROP INDEX whatsapp_inbox_sender_recent")
    op.execute("ALTER TABLE whatsapp_inbox DROP COLUMN sender_hash")
