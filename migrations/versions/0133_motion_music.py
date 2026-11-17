"""Private Music cache and durable monthly holds, shared by lab and production."""

from alembic import op

revision = "0133_motion_music"
down_revision = "0132_piece_feedback"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE motion_music (
      tenant_id uuid NOT NULL REFERENCES tenants(id), business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), operation_id uuid NOT NULL,
      cache_key text NOT NULL, reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros>=0),
      result_ciphertext text, ready boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      CHECK(length(cache_key)<=120), CHECK(length(result_ciphertext)<=3000000))""")
    op.execute("ALTER TABLE motion_music ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE motion_music FORCE ROW LEVEL SECURITY")
    scope = """tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
      AND (public.is_platform_staff() OR EXISTS(SELECT 1 FROM memberships m
        WHERE m.tenant_id=motion_music.tenant_id
        AND m.actor_id=nullif(current_setting('app.actor_id',true),'')::uuid AND m.role='owner' AND m.active))"""
    op.execute(f"""CREATE POLICY music_scope ON motion_music TO meu_braco_direito_app
      USING({scope}) WITH CHECK({scope} AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute("GRANT SELECT,INSERT,UPDATE(result_ciphertext,ready) ON motion_music TO meu_braco_direito_app")
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO previous FROM pg_constraint
      WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' || previous ||
      ') OR event_type IN (''motion.music_reserved'',''motion.music_ready''))'; END $$""")


def downgrade():
    raise RuntimeError("Preserve music identity, cache and cost holds")
