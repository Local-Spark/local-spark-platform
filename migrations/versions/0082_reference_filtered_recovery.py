"""Expose only a completed effect's identity for safe acknowledgement recovery."""

from alembic import op

revision = "0082_reference_filtered_recovery"
down_revision = "0081_reference_filtered_fence"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE FUNCTION public.reference_filtered_recovery(
      p_business uuid,p_search uuid,p_google uuid,p_google_event uuid)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        effect_state text; batch_id uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_google IS NULL
          OR p_google_event IS NULL THEN RAISE EXCEPTION 'REFERENCE_RECOVERY_INVALID'; END IF;
        SELECT g.state INTO effect_state FROM public.reference_provider_effects g
          WHERE g.tenant_id=t AND g.business_id=p_business AND g.actor_id=a AND g.id=p_google
            AND g.search_id=p_search AND g.provider='google';
        IF NOT FOUND OR NOT EXISTS(SELECT 1 FROM public.outbox_events o
          WHERE o.id=p_google_event AND o.tenant_id=t AND o.event_type='reference.provider_effect_requested'
            AND o.payload=jsonb_build_object('business_id',p_business::text,'actor_id',a::text,
                                             'operation_id',p_google::text)) THEN
          RAISE EXCEPTION 'REFERENCE_RECOVERY_INVALID'; END IF;
        IF effect_state='completed_empty' THEN
          RETURN jsonb_build_object('state','empty','batch_id',NULL); END IF;
        IF effect_state='completed_filtered' THEN
          SELECT b.id INTO batch_id FROM public.reference_filtered_batches b
            JOIN public.reference_provider_effects j ON j.tenant_id=b.tenant_id AND j.business_id=b.business_id
              AND j.id=b.jev_effect_id AND j.provider='jev' AND j.state='completed_filtered'
            WHERE b.tenant_id=t AND b.business_id=p_business AND b.actor_id=a AND b.search_id=p_search
              AND b.google_effect_id=p_google;
          IF FOUND THEN RETURN jsonb_build_object('state','filtered','batch_id',batch_id); END IF;
        END IF;
        RETURN NULL;
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_filtered_recovery(uuid,uuid,uuid,uuid)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("REVOKE ALL ON FUNCTION public.reference_filtered_recovery(uuid,uuid,uuid,uuid) FROM PUBLIC")
    op.execute("""GRANT EXECUTE ON FUNCTION public.reference_filtered_recovery(uuid,uuid,uuid,uuid)
      TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("DROP FUNCTION public.reference_filtered_recovery(uuid,uuid,uuid,uuid)")
