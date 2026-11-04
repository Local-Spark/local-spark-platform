"""Enable filtered commit only after the fenced Google/Jev link exists.

The wrapper proves the stored link and delegates to the 0079 fence and replay
checks. A trusted activity is still required to derive its input from the two
provider responses. No network effect is enabled by this migration.
"""

from alembic import op

revision = "0081_reference_filtered_fence"
down_revision = "0080_reference_jev_intent"
branch_labels = None
depends_on = None

_SIGNATURE = "uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,bigint,jsonb"


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    op.execute(
        f"ALTER FUNCTION public.reference_filtered_commit({_SIGNATURE}) RENAME TO reference_filtered_commit_inner"
    )
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_filtered_commit_inner({_SIGNATURE}) FROM PUBLIC")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_filtered_commit_inner({_SIGNATURE}) FROM meu_braco_direito_correlator"
    )
    op.execute("""CREATE FUNCTION public.reference_filtered_commit(
      p_business uuid,p_search uuid,p_batch uuid,p_google uuid,p_google_event uuid,p_google_token uuid,
      p_jev uuid,p_jev_event uuid,p_jev_token uuid,p_source_mac text,p_context bigint,p_candidates jsonb)
      RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        google_mac text; jev_mac text; jev_event uuid; jev_parent uuid;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_google IS NULL OR p_jev IS NULL
          OR p_source_mac IS NULL OR p_source_mac !~ '^[0-9a-f]{64}$' OR p_jev_event IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_FILTERED_LINK_INVALID'; END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        PERFORM 1 FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND id IN (p_google,p_jev) ORDER BY id FOR UPDATE;
        SELECT g.source_batch_mac INTO google_mac FROM public.reference_provider_effects g
          WHERE g.tenant_id=t AND g.business_id=p_business AND g.actor_id=a AND g.id=p_google AND g.provider='google';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_FILTERED_LINK_INVALID'; END IF;
        SELECT j.source_batch_mac,j.request_event_id,j.parent_google_effect_id INTO jev_mac,jev_event,jev_parent
          FROM public.reference_provider_effects j WHERE j.tenant_id=t AND j.business_id=p_business
          AND j.actor_id=a AND j.id=p_jev AND j.provider='jev';
        IF NOT FOUND OR google_mac IS DISTINCT FROM p_source_mac OR jev_mac IS DISTINCT FROM p_source_mac
          OR jev_parent IS DISTINCT FROM p_google OR jev_event IS DISTINCT FROM p_jev_event THEN
          RAISE EXCEPTION 'REFERENCE_FILTERED_LINK_INVALID'; END IF;
        RETURN public.reference_filtered_commit_inner(p_business,p_search,p_batch,p_google,p_google_event,
          p_google_token,p_jev,p_jev_event,p_jev_token,p_source_mac,p_context,p_candidates);
      END $$""")
    op.execute(
        f"ALTER FUNCTION public.reference_filtered_commit({_SIGNATURE}) OWNER TO meu_braco_direito_reference_ledger"
    )
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_filtered_commit({_SIGNATURE}) FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION public.reference_filtered_commit({_SIGNATURE}) TO meu_braco_direito_correlator"
    )


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    op.execute(f"DROP FUNCTION public.reference_filtered_commit({_SIGNATURE})")
    op.execute(
        f"ALTER FUNCTION public.reference_filtered_commit_inner({_SIGNATURE}) RENAME TO reference_filtered_commit"
    )
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_filtered_commit({_SIGNATURE}) FROM PUBLIC")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_filtered_commit({_SIGNATURE}) FROM meu_braco_direito_correlator"
    )
