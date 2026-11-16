"""Version-bound feedback and private approval of laboratory pieces."""

from alembic import op

revision = "0132_piece_feedback"
down_revision = "0131_message_creation_funding"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE content_piece_versions ADD COLUMN creative_context_ciphertext text")
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO previous FROM pg_constraint
      WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' || previous ||
      ') OR event_type IN (''content.feedback_recorded'',''content.feedback_removed'',''creation_lab.piece_approved''))'; END $$""")
    op.execute("""CREATE TABLE content_piece_feedback (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      piece_id uuid NOT NULL, version_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      operation_id uuid NOT NULL, request_hash char(64) NOT NULL, note_ciphertext text NOT NULL,
      active boolean NOT NULL DEFAULT true, created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(tenant_id,actor_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,piece_id,version_id) REFERENCES content_piece_versions(tenant_id,business_id,piece_id,id))""")
    op.execute("""CREATE TABLE content_feedback_invitations (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      piece_id uuid NOT NULL, version_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      recipient_hash text NOT NULL, provider_message_id text NOT NULL UNIQUE,
      simulated boolean NOT NULL DEFAULT true CHECK(simulated),
      created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL DEFAULT now()+interval '7 days',
      UNIQUE(tenant_id,business_id,piece_id,version_id,actor_id),
      FOREIGN KEY(tenant_id,business_id,piece_id,version_id) REFERENCES content_piece_versions(tenant_id,business_id,piece_id,id))""")
    for table in ("content_piece_feedback", "content_feedback_invitations"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY feedback_owner ON {table} TO meu_braco_direito_app
          USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
          AND public.message_creation_owned(tenant_id,nullif(current_setting('app.actor_id',true),'')::uuid))
          WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
          AND public.message_creation_owned(tenant_id,nullif(current_setting('app.actor_id',true),'')::uuid)
          AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute("DROP POLICY feedback_owner ON content_piece_feedback")
    owner = "tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid AND public.message_creation_owned(tenant_id,nullif(current_setting('app.actor_id',true),'')::uuid)"
    op.execute(
        f"CREATE POLICY feedback_read ON content_piece_feedback FOR SELECT TO meu_braco_direito_app USING({owner})"
    )
    op.execute(
        f"CREATE POLICY feedback_write ON content_piece_feedback FOR INSERT TO meu_braco_direito_app WITH CHECK({owner} AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)"
    )
    op.execute(
        f"CREATE POLICY feedback_remove ON content_piece_feedback FOR UPDATE TO meu_braco_direito_app USING({owner}) WITH CHECK({owner})"
    )
    op.execute("GRANT UPDATE(active) ON content_piece_feedback TO meu_braco_direito_app")
    op.execute("""CREATE TABLE creation_lab_approvals (
      version_id uuid PRIMARY KEY REFERENCES creation_lab_versions(id), run_id uuid NOT NULL REFERENCES creation_lab_runs(id),
      actor_id uuid NOT NULL REFERENCES user_accounts(id), operation_id uuid NOT NULL,
      sha256 char(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(actor_id,operation_id))""")
    op.execute("ALTER TABLE creation_lab_approvals ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE creation_lab_approvals FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY lab_approval_admin ON creation_lab_approvals TO meu_braco_direito_app
      USING(public.is_platform_staff() AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(public.is_platform_staff() AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
        AND EXISTS(SELECT 1 FROM creation_lab_runs r JOIN creation_lab_versions v ON v.run_id=r.id
          WHERE r.id=creation_lab_approvals.run_id AND r.origin='lab' AND r.state='completed' AND r.actor_id=creation_lab_approvals.actor_id
          AND v.id=creation_lab_approvals.version_id AND v.sha256=creation_lab_approvals.sha256))""")
    op.execute("GRANT SELECT,INSERT ON creation_lab_approvals TO meu_braco_direito_app")


def downgrade():
    raise RuntimeError("Preserve approvals and customer feedback; rollback requires a reviewed data migration")
