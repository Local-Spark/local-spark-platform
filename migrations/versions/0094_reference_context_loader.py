"""Provide only the authorized versioned inputs to a reference activity."""

from alembic import op

revision = "0094_reference_context_loader"
down_revision = "0093_reference_feed_resources"
branch_labels = None
depends_on = None


def upgrade():
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_search_event_ledger ON outbox_events FOR SELECT
      TO meu_braco_direito_reference_ledger USING(tenant_id={tenant}
      AND event_type='reference.provider_search_requested' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_load_search_context(p_business uuid,p_search uuid,p_event uuid)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        s public.reference_provider_searches%ROWTYPE; doc jsonb; version bigint;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_search IS NULL OR p_event IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT h.version,v.document INTO version,doc FROM public.business_context_heads h
          JOIN public.business_context_versions v
            ON (v.tenant_id,v.business_id,v.version)=(h.tenant_id,h.business_id,h.version)
          WHERE h.tenant_id=t AND h.business_id=p_business FOR SHARE OF h;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_search AND state='pending' AND radius_occupied FOR SHARE;
        IF NOT FOUND OR s.cycle_id IS NULL OR s.request_event_id IS DISTINCT FROM p_event
          OR s.identity_key_version IS NULL OR NOT EXISTS(SELECT 1 FROM public.outbox_events o
            WHERE o.tenant_id=t AND o.id=p_event AND o.event_type='reference.provider_search_requested'
              AND o.payload=jsonb_build_object('business_id',p_business::text,'actor_id',a::text,
                'operation_id',s.operation_id::text)) THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        IF version IS DISTINCT FROM s.context_version
          OR doc#>>'{preferences,reference_search,scope}' IS DISTINCT FROM 'local'
          OR doc#>'{preferences,reference_search,radius_km}' IS DISTINCT FROM to_jsonb(s.radius_km)
          OR doc#>>'{preferences,reference_search,origin,method}' IS DISTINCT FROM 'device'
          OR doc#>'{preferences,reference_search,origin,coordinates,confirmed}' IS DISTINCT FROM 'true'::jsonb
          OR jsonb_typeof(doc#>'{preferences,reference_search,origin,coordinates,latitude}') IS DISTINCT FROM 'number'
          OR jsonb_typeof(doc#>'{preferences,reference_search,origin,coordinates,longitude}') IS DISTINCT FROM 'number'
          OR jsonb_typeof(doc#>'{preferences,business_terms}') IS DISTINCT FROM 'array' THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_LOAD_INVALID'; END IF;
        RETURN jsonb_build_object('operation_id',s.operation_id,'context_version',s.context_version,
          'radius_km',s.radius_km,'identity_key_version',s.identity_key_version,'request_mac',s.request_mac,
          'latitude',doc#>'{preferences,reference_search,origin,coordinates,latitude}',
          'longitude',doc#>'{preferences,reference_search,origin,coordinates,longitude}',
          'business_terms',doc#>'{preferences,business_terms}',
          'business_description',doc#>'{preferences,business_characteristics}');
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_load_search_context(uuid,uuid,uuid)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("REVOKE ALL ON FUNCTION public.reference_load_search_context(uuid,uuid,uuid) FROM PUBLIC")
    op.execute("""GRANT EXECUTE ON FUNCTION public.reference_load_search_context(uuid,uuid,uuid)
      TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("DROP FUNCTION public.reference_load_search_context(uuid,uuid,uuid)")
    op.execute("DROP POLICY reference_search_event_ledger ON outbox_events")
