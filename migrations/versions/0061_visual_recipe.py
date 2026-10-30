"""Bind the experimental full-piece recipe to each visual preview."""

from alembic import op

revision = "0061_visual_recipe"
down_revision = "0060_visual_skill_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE media_previews
      ADD COLUMN visual_recipe text NOT NULL DEFAULT 'legacy_overlay',
      ADD CONSTRAINT media_preview_visual_recipe CHECK (
        visual_recipe='legacy_overlay' OR
        (visual_recipe='full_piece_v1' AND generation_mode IN ('visual_ai','visual_fake')))""")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_preview_visual_skill")
    op.execute("""ALTER TABLE media_previews ADD CONSTRAINT media_preview_visual_skill CHECK (
      (visual_skill_id IS NULL AND visual_skill_sha256 IS NULL) OR
      (generation_mode IN ('visual_ai','visual_fake') AND visual_skill_id IS NOT NULL
       AND visual_skill_id IN ('instagram-feed-v1','instagram-story-v1')
       AND visual_skill_sha256 IS NOT NULL AND visual_skill_sha256 ~ '^[0-9a-f]{64}$'))""")
    op.execute("""ALTER TABLE visual_ai_attempts ADD CONSTRAINT visual_attempt_trace_binding_unique
      UNIQUE(tenant_id,business_id,preview_id,actor_id,operation_id,request_hash)""")
    op.execute("""ALTER TABLE editorial_proposals ADD CONSTRAINT editorial_trace_binding_unique
      UNIQUE(tenant_id,business_id,id,actor_id)""")
    op.execute("""CREATE TABLE visual_request_traces (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, preview_id uuid NOT NULL,
      actor_id uuid NOT NULL, operation_id uuid NOT NULL, request_hash char(64) NOT NULL,
      ciphertext text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,preview_id), UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,preview_id,actor_id,operation_id,request_hash)
        REFERENCES visual_ai_attempts(tenant_id,business_id,preview_id,actor_id,operation_id,request_hash)
        ON DELETE CASCADE,
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("ALTER TABLE visual_request_traces ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE visual_request_traces FORCE ROW LEVEL SECURITY")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    op.execute(f"""CREATE POLICY owner_visual_request_trace ON visual_request_traces FOR SELECT
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})""")
    op.execute(f"""CREATE POLICY worker_visual_request_trace ON visual_request_traces
      TO meu_braco_direito_correlator USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
    op.execute("GRANT SELECT ON visual_request_traces TO meu_braco_direito_app")
    op.execute("GRANT SELECT,INSERT ON visual_request_traces TO meu_braco_direito_correlator")
    op.execute("""CREATE TABLE editorial_request_traces (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      proposal_id uuid NOT NULL,
      actor_id uuid NOT NULL, request_hash char(64) NOT NULL, ciphertext text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(tenant_id,proposal_id),
      FOREIGN KEY(tenant_id,business_id,proposal_id,actor_id)
        REFERENCES editorial_proposals(tenant_id,business_id,id,actor_id) ON DELETE CASCADE,
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("ALTER TABLE editorial_request_traces ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE editorial_request_traces FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY owner_editorial_request_trace ON editorial_request_traces FOR SELECT
      TO meu_braco_direito_app USING(tenant_id={tenant} AND {owner})""")
    op.execute(f"""CREATE POLICY worker_editorial_request_trace ON editorial_request_traces
      TO meu_braco_direito_correlator USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
    op.execute("GRANT SELECT ON editorial_request_traces TO meu_braco_direito_app")
    op.execute("GRANT SELECT,INSERT ON editorial_request_traces TO meu_braco_direito_correlator")
    op.execute("""ALTER TABLE content_deliveries ADD COLUMN visual_review_confirmation jsonb,
      ADD CONSTRAINT content_delivery_visual_review_object CHECK
        (visual_review_confirmation IS NULL OR jsonb_typeof(visual_review_confirmation)='object')""")
    op.execute("GRANT UPDATE(visual_review_confirmation) ON content_deliveries TO meu_braco_direito_app")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM media_previews WHERE visual_recipe='full_piece_v1')
        OR EXISTS(SELECT 1 FROM visual_request_traces)
        OR EXISTS(SELECT 1 FROM editorial_request_traces)
        OR EXISTS(SELECT 1 FROM content_deliveries WHERE visual_review_confirmation IS NOT NULL) THEN
        RAISE EXCEPTION 'FULL_PIECE_PREVIEWS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("DROP TABLE editorial_request_traces")
    op.execute("DROP TABLE visual_request_traces")
    op.execute("ALTER TABLE editorial_proposals DROP CONSTRAINT editorial_trace_binding_unique")
    op.execute("ALTER TABLE visual_ai_attempts DROP CONSTRAINT visual_attempt_trace_binding_unique")
    op.execute("REVOKE UPDATE(visual_review_confirmation) ON content_deliveries FROM meu_braco_direito_app")
    op.execute("ALTER TABLE content_deliveries DROP CONSTRAINT content_delivery_visual_review_object")
    op.execute("ALTER TABLE content_deliveries DROP COLUMN visual_review_confirmation")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_preview_visual_recipe")
    op.execute("ALTER TABLE media_previews DROP COLUMN visual_recipe")
    op.execute("ALTER TABLE media_previews DROP CONSTRAINT media_preview_visual_skill")
    op.execute("""ALTER TABLE media_previews ADD CONSTRAINT media_preview_visual_skill CHECK (
      (visual_skill_id IS NULL AND visual_skill_sha256 IS NULL) OR
      (generation_mode='visual_ai' AND visual_skill_id IS NOT NULL
       AND visual_skill_id IN ('instagram-feed-v1','instagram-story-v1')
       AND visual_skill_sha256 IS NOT NULL AND visual_skill_sha256 ~ '^[0-9a-f]{64}$'))""")
