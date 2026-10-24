"""Track Meta delivery receipts, staff review and bounded owner acknowledgments."""

from alembic import op

revision = "0029_whatsapp_delivery"
down_revision = "0028_editorial_replies"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE editorial_whatsapp_replies
      ADD COLUMN delivery_state text NOT NULL DEFAULT 'awaiting_receipt'
        CHECK(delivery_state IN ('awaiting_receipt','sent','failed','delivered','read')),
      ADD COLUMN delivery_at timestamptz,
      ADD COLUMN provider_error_code varchar(32),
      ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT now(),
      ADD COLUMN review_outcome text CHECK(review_outcome IN ('investigating','closed_no_retry')),
      ADD COLUMN reviewed_at timestamptz,
      ADD COLUMN reviewed_by uuid REFERENCES user_accounts(id),
      ADD COLUMN ack_state text CHECK(ack_state IN
        ('pending','submitting','accepted','uncertain','failed','expired')),
      ADD COLUMN ack_provider_message_id text UNIQUE,
      ADD COLUMN ack_error_code text,
      ADD COLUMN ack_attempted_at timestamptz,
      ADD COLUMN ack_accepted_at timestamptz,
      ADD COLUMN ack_delivery_state text NOT NULL DEFAULT 'awaiting_receipt'
        CHECK(ack_delivery_state IN ('awaiting_receipt','sent','failed','delivered','read')),
      ADD COLUMN ack_delivery_at timestamptz,
      ADD COLUMN ack_provider_error_code varchar(32),
      ADD COLUMN ack_next_attempt_at timestamptz NOT NULL DEFAULT now()""")
    op.execute("CREATE INDEX editorial_whatsapp_reply_quota ON editorial_whatsapp_replies(tenant_id,attempted_at)")
    op.execute("CREATE INDEX editorial_whatsapp_ack_quota ON editorial_whatsapp_replies(tenant_id,ack_attempted_at)")
    op.execute("""CREATE INDEX editorial_whatsapp_ack_pending ON editorial_whatsapp_replies(created_at,id)
      WHERE ack_state='pending'""")
    op.execute("""GRANT UPDATE(delivery_state,delivery_at,provider_error_code,next_attempt_at,
      ack_state,ack_provider_message_id,ack_error_code,ack_attempted_at,ack_accepted_at,
      ack_delivery_state,ack_delivery_at,ack_provider_error_code,ack_next_attempt_at)
      ON editorial_whatsapp_replies TO meu_braco_direito_correlator""")
    op.execute("""CREATE FUNCTION public.enqueue_whatsapp_ack(p_decision uuid)
      RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE v_actor uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
      BEGIN
        IF v_actor IS NULL OR NOT EXISTS (
          SELECT 1 FROM public.editorial_conversation_decisions d
          JOIN public.memberships m ON m.tenant_id=d.tenant_id AND m.actor_id=v_actor
          WHERE d.id=p_decision AND d.actor_id=v_actor AND d.state IN ('confirmed','discarded')
            AND m.role='owner' AND m.active) THEN
          RETURN false;
        END IF;
        UPDATE public.editorial_whatsapp_replies r SET ack_state='pending'
          WHERE r.id=p_decision AND r.state='accepted' AND r.expires_at>now()
            AND r.ack_state IS NULL AND r.delivery_state<>'failed';
        RETURN FOUND;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION public.enqueue_whatsapp_ack(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.enqueue_whatsapp_ack(uuid) TO meu_braco_direito_app")
    op.execute("""CREATE FUNCTION public.admin_whatsapp_replies(p_tenant uuid,p_limit integer)
      RETURNS TABLE(id uuid,tenant_id uuid,business_id uuid,state text,delivery_state text,
        error_code text,provider_error_code varchar(32),attempted_at timestamptz,
        accepted_at timestamptz,delivery_at timestamptz,expires_at timestamptz,
        review_outcome text,reviewed_at timestamptz,ack_state text,ack_delivery_state text,
        ack_error_code text,ack_provider_error_code varchar(32),ack_attempted_at timestamptz)
      LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF NOT public.is_platform_staff() THEN
          RAISE EXCEPTION 'Staff access required' USING ERRCODE='42501';
        END IF;
        IF p_limit IS NULL OR p_limit<1 OR p_limit>100 THEN
          RAISE EXCEPTION 'Invalid limit' USING ERRCODE='22023';
        END IF;
        RETURN QUERY SELECT r.id,r.tenant_id,r.business_id,r.state,r.delivery_state,
          r.error_code,r.provider_error_code,r.attempted_at,r.accepted_at,r.delivery_at,
          r.expires_at,r.review_outcome,r.reviewed_at,r.ack_state,r.ack_delivery_state,
          r.ack_error_code,r.ack_provider_error_code,r.ack_attempted_at
          FROM public.editorial_whatsapp_replies r
          WHERE (p_tenant IS NULL OR r.tenant_id=p_tenant)
            AND (r.state IN ('uncertain','failed') OR r.delivery_state='failed'
              OR r.ack_state IN ('uncertain','failed') OR r.ack_delivery_state='failed'
              OR (r.state='accepted' AND r.delivery_state NOT IN ('delivered','read')
                AND r.accepted_at<now()-interval '15 minutes')
              OR (r.ack_state='accepted' AND r.ack_delivery_state NOT IN ('delivered','read')
                AND r.ack_accepted_at<now()-interval '15 minutes'))
          ORDER BY r.created_at DESC,r.id DESC LIMIT p_limit;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION public.admin_whatsapp_replies(uuid,integer) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.admin_whatsapp_replies(uuid,integer) TO meu_braco_direito_app")
    op.execute("""CREATE FUNCTION public.admin_review_whatsapp_reply(p_reply uuid,p_outcome text)
      RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE v_actor uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
      BEGIN
        IF NOT public.is_platform_staff() THEN
          RAISE EXCEPTION 'Staff access required' USING ERRCODE='42501';
        END IF;
        IF p_outcome IS NULL OR p_outcome NOT IN ('investigating','closed_no_retry') THEN
          RAISE EXCEPTION 'Invalid review outcome' USING ERRCODE='22023';
        END IF;
        UPDATE public.editorial_whatsapp_replies r
          SET review_outcome=p_outcome,reviewed_at=now(),reviewed_by=v_actor
          WHERE r.id=p_reply AND (r.state IN ('uncertain','failed') OR r.delivery_state='failed'
            OR r.ack_state IN ('uncertain','failed') OR r.ack_delivery_state='failed'
            OR (r.state='accepted' AND r.delivery_state NOT IN ('delivered','read')
              AND r.accepted_at<now()-interval '15 minutes')
            OR (r.ack_state='accepted' AND r.ack_delivery_state NOT IN ('delivered','read')
              AND r.ack_accepted_at<now()-interval '15 minutes'));
        RETURN FOUND;
      END $$""")
    op.execute("REVOKE ALL ON FUNCTION public.admin_review_whatsapp_reply(uuid,text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.admin_review_whatsapp_reply(uuid,text) TO meu_braco_direito_app")


def downgrade():
    op.execute("DROP FUNCTION public.admin_review_whatsapp_reply(uuid,text)")
    op.execute("DROP FUNCTION public.admin_whatsapp_replies(uuid,integer)")
    op.execute("DROP FUNCTION public.enqueue_whatsapp_ack(uuid)")
    op.execute("DROP INDEX editorial_whatsapp_ack_pending")
    op.execute("DROP INDEX editorial_whatsapp_ack_quota")
    op.execute("DROP INDEX editorial_whatsapp_reply_quota")
    for column in (
        "delivery_state",
        "delivery_at",
        "provider_error_code",
        "next_attempt_at",
        "review_outcome",
        "reviewed_at",
        "reviewed_by",
        "ack_state",
        "ack_provider_message_id",
        "ack_error_code",
        "ack_attempted_at",
        "ack_accepted_at",
        "ack_delivery_state",
        "ack_delivery_at",
        "ack_provider_error_code",
        "ack_next_attempt_at",
    ):
        op.execute(f"ALTER TABLE editorial_whatsapp_replies DROP COLUMN {column}")
