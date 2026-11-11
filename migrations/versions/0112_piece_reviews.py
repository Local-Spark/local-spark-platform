"""Private immutable piece versions and review without publication."""

from alembic import op

revision = "0112_piece_reviews"
down_revision = "0111_apify_cost_revisions"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') OR event_type IN (''content.piece_ready'',''content.piece_decided''))';
    END $$""")
    op.execute("""ALTER TABLE media_previews ADD CONSTRAINT media_preview_piece_scope
      UNIQUE(tenant_id,business_id,id)""")
    op.execute("""CREATE TABLE content_pieces (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      simulated boolean NOT NULL DEFAULT false,
      format text NOT NULL CHECK(format IN ('photo','story','reel','story_video','carousel_motion')),
      current_version_id uuid NOT NULL, approved_version_id uuid,
      state text NOT NULL CHECK(state IN ('ready_for_review','changes_requested','approved')),
      source_preview_id uuid,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,id), UNIQUE(tenant_id,business_id,source_preview_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,source_preview_id) REFERENCES media_previews(tenant_id,business_id,id),
      CONSTRAINT piece_approval_requires_version CHECK(state<>'approved' OR
        (approved_version_id IS NOT NULL AND approved_version_id=current_version_id)))""")
    op.execute("""CREATE TABLE content_piece_versions (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, piece_id uuid NOT NULL, id uuid NOT NULL,
      number integer NOT NULL CHECK(number>0), parent_id uuid,
      operation_id uuid NOT NULL, request_hash char(64) NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,piece_id,id),
      UNIQUE(tenant_id,operation_id), UNIQUE(tenant_id,business_id,piece_id,number),
      FOREIGN KEY(tenant_id,business_id,piece_id) REFERENCES content_pieces(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,piece_id,parent_id)
        REFERENCES content_piece_versions(tenant_id,business_id,piece_id,id))""")
    for column in ("current_version_id", "approved_version_id"):
        op.execute(f"""ALTER TABLE content_pieces ADD CONSTRAINT piece_{column}_fk
          FOREIGN KEY(tenant_id,business_id,id,{column})
          REFERENCES content_piece_versions(tenant_id,business_id,piece_id,id)
          DEFERRABLE INITIALLY DEFERRED""")
    op.execute("""CREATE TABLE content_piece_artifacts (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, piece_id uuid NOT NULL, version_id uuid NOT NULL,
      id uuid NOT NULL, position integer NOT NULL CHECK(position BETWEEN 0 AND 19),
      object_key text NOT NULL, sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
      mime_type text NOT NULL CHECK(mime_type IN ('image/png','image/jpeg','video/mp4')),
      size_bytes bigint NOT NULL CHECK(size_bytes>0 AND size_bytes<=52428800),
      PRIMARY KEY(tenant_id,business_id,piece_id,version_id,id),
      UNIQUE(tenant_id,business_id,piece_id,version_id,position),
      FOREIGN KEY(tenant_id,business_id,piece_id,version_id)
        REFERENCES content_piece_versions(tenant_id,business_id,piece_id,id))""")
    op.execute("""CREATE TABLE content_piece_decisions (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, piece_id uuid NOT NULL, version_id uuid NOT NULL,
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      decision text NOT NULL CHECK(decision IN ('approve','request_changes')),
      request_hash char(64) NOT NULL, confirmation jsonb NOT NULL, note_ciphertext text,
      page_positions jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,piece_id,version_id)
        REFERENCES content_piece_versions(tenant_id,business_id,piece_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("content_pieces", "content_piece_versions", "content_piece_artifacts", "content_piece_decisions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY piece_owner ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute("""GRANT UPDATE(current_version_id,approved_version_id,state,updated_at)
      ON content_pieces TO meu_braco_direito_app""")


def downgrade():
    # Retain event vocabulary so historical outbox identities remain readable.
    op.execute("ALTER TABLE content_pieces DROP CONSTRAINT piece_current_version_id_fk")
    op.execute("ALTER TABLE content_pieces DROP CONSTRAINT piece_approved_version_id_fk")
    for table in ("content_piece_decisions", "content_piece_artifacts", "content_piece_versions", "content_pieces"):
        op.execute(f"DROP TABLE {table}")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_preview_piece_scope")
