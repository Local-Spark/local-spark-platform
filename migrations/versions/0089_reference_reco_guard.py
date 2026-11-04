"""Inactive budget guard for a second, shortlist-bound Jev effect.

No runtime grant admits or claims recommendation effects yet: creating their
intents requires an evidenced shortlist writer and a trusted activity. The
ordinary Jev claim explicitly rejects this separate effect purpose.
"""

from alembic import op

revision = "0089_reference_reco_guard"
down_revision = "0088_reference_real_selection"
branch_labels = None
depends_on = None

_JEV = "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,text,bigint"
_RECO = "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,uuid,text,bigint"


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    op.execute("""ALTER TABLE reference_provider_effects ADD COLUMN purpose text NOT NULL DEFAULT 'discovery',
      ADD COLUMN recommendation_batch_id uuid, ADD COLUMN shortlist_mac char(64),
      ADD CONSTRAINT reference_effect_purpose CHECK(
        (purpose='discovery' AND recommendation_batch_id IS NULL AND shortlist_mac IS NULL) OR
        (purpose='recommendation' AND provider='jev' AND recommendation_batch_id IS NOT NULL
          AND shortlist_mac IS NOT NULL AND shortlist_mac ~ '^[0-9a-f]{64}$')),
      ADD FOREIGN KEY(tenant_id,business_id,recommendation_batch_id)
        REFERENCES reference_filtered_batches(tenant_id,business_id,id)""")
    op.execute("DROP INDEX reference_one_jev_intent_per_google")
    op.execute("""CREATE UNIQUE INDEX reference_one_jev_intent_per_google
      ON reference_provider_effects(tenant_id,business_id,parent_google_effect_id,purpose) WHERE provider='jev'""")
    op.execute(f"ALTER FUNCTION public.reference_jev_claim({_JEV}) RENAME TO reference_jev_claim_discovery_inner")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_jev_claim_discovery_inner({_JEV}) "
        "FROM PUBLIC,meu_braco_direito_correlator"
    )
    op.execute("""CREATE FUNCTION public.reference_jev_claim(
      p_effect uuid,p_event uuid,p_mac text,p_business uuid,p_search uuid,p_pilot uuid,
      p_amount bigint,p_key text,p_tariff text,p_credential text,p_mask text,
      p_parent uuid,p_parent_token uuid,p_batch_mac text,p_context_version bigint)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
      BEGIN
        IF NOT EXISTS(SELECT 1 FROM public.reference_provider_effects e WHERE e.tenant_id=t
          AND e.business_id=p_business AND e.actor_id=a AND e.id=p_effect AND e.provider='jev'
          AND e.purpose='discovery') THEN RAISE EXCEPTION 'REFERENCE_JEV_PURPOSE_INVALID'; END IF;
        RETURN public.reference_jev_claim_discovery_inner(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
          p_amount,p_key,p_tariff,p_credential,p_mask,p_parent,p_parent_token,p_batch_mac,p_context_version);
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_jev_claim({_JEV}) OWNER TO meu_braco_direito_reference_ledger")
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_jev_claim({_JEV}) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.reference_jev_claim({_JEV}) TO meu_braco_direito_correlator")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_reco_ledger ON reference_private_shortlist
      FOR SELECT TO meu_braco_direito_reference_ledger USING(tenant_id={tenant})""")
    op.execute("GRANT SELECT ON reference_private_shortlist TO meu_braco_direito_reference_ledger")
    op.execute("""CREATE FUNCTION public.reference_reco_claim(
      p_effect uuid,p_event uuid,p_mac text,p_business uuid,p_search uuid,p_pilot uuid,
      p_amount bigint,p_key text,p_tariff text,p_credential text,p_mask text,
      p_google uuid,p_similarity uuid,p_batch uuid,p_shortlist_mac text,p_context bigint)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; g public.reference_provider_effects%ROWTYPE;
        j public.reference_provider_effects%ROWTYPE; b public.reference_filtered_batches%ROWTYPE; n int;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_effect IS NULL OR p_event IS NULL
          OR p_search IS NULL OR p_pilot IS NULL OR p_google IS NULL OR p_similarity IS NULL OR p_batch IS NULL
          OR p_shortlist_mac IS NULL OR p_shortlist_mac !~ '^[0-9a-f]{64}$' OR p_context IS NULL OR p_context<1
          OR p_effect IN (p_google,p_similarity) OR p_google=p_similarity THEN
          RAISE EXCEPTION 'REFERENCE_RECO_INTENT_INVALID'; END IF;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='jev' AND purpose='recommendation';
        IF NOT FOUND OR e.recommendation_batch_id IS DISTINCT FROM p_batch
          OR e.shortlist_mac IS DISTINCT FROM p_shortlist_mac OR e.request_event_id IS DISTINCT FROM p_event
          OR e.parent_google_effect_id IS DISTINCT FROM p_google THEN
          RAISE EXCEPTION 'REFERENCE_RECO_INTENT_INVALID'; END IF;
        IF e.state='pending' AND NOT public.lock_reference_cost_owner() THEN
          SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
            AND actor_id=a AND id=p_effect AND provider='jev' AND purpose='recommendation';
          IF NOT FOUND OR e.state='pending' THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        PERFORM 1 FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND id IN (p_effect,p_google,p_similarity) ORDER BY id FOR UPDATE;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='jev' AND purpose='recommendation';
        SELECT * INTO g FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_google AND provider='google' AND purpose='discovery';
        SELECT * INTO j FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_similarity AND provider='jev' AND purpose='discovery';
        SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_batch;
        IF e.id IS NULL OR g.id IS NULL OR j.id IS NULL OR b.id IS NULL
          OR e.recommendation_batch_id IS DISTINCT FROM p_batch OR e.shortlist_mac IS DISTINCT FROM p_shortlist_mac
          OR e.request_event_id IS DISTINCT FROM p_event OR e.parent_google_effect_id IS DISTINCT FROM g.id
          OR e.search_id IS DISTINCT FROM p_search OR e.pilot_id IS DISTINCT FROM p_pilot
          OR g.state<>'completed_filtered' OR j.state<>'completed_filtered'
          OR b.google_effect_id IS DISTINCT FROM g.id OR b.jev_effect_id IS DISTINCT FROM j.id
          OR b.search_id IS DISTINCT FROM p_search OR b.context_version IS DISTINCT FROM p_context
          OR b.source_batch_mac IS DISTINCT FROM e.source_batch_mac
          OR b.source_batch_mac IS DISTINCT FROM g.source_batch_mac
          OR b.source_batch_mac IS DISTINCT FROM j.source_batch_mac
          OR j.parent_google_effect_id IS DISTINCT FROM g.id OR j.search_id IS DISTINCT FROM p_search
          OR g.search_id IS DISTINCT FROM p_search OR g.pilot_id IS DISTINCT FROM p_pilot
          OR j.pilot_id IS DISTINCT FROM p_pilot THEN RAISE EXCEPTION 'REFERENCE_RECO_LINK_INVALID'; END IF;
        SELECT count(*) INTO n FROM public.reference_private_shortlist WHERE tenant_id=t
          AND business_id=p_business AND batch_id=p_batch;
        IF n NOT BETWEEN 1 AND 10 THEN RAISE EXCEPTION 'REFERENCE_RECO_SHORTLIST_INVALID'; END IF;
        RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
          p_amount,p_key,p_tariff,p_credential,p_mask);
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_reco_claim({_RECO}) OWNER TO meu_braco_direito_reference_ledger")
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_reco_claim({_RECO}) FROM PUBLIC,meu_braco_direito_correlator")


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_provider_effects WHERE purpose='recommendation') THEN
      RAISE EXCEPTION 'REFERENCE_RECO_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute(f"DROP FUNCTION public.reference_reco_claim({_RECO})")
    op.execute("REVOKE SELECT ON reference_private_shortlist FROM meu_braco_direito_reference_ledger")
    op.execute("DROP POLICY reference_reco_ledger ON reference_private_shortlist")
    op.execute(f"DROP FUNCTION public.reference_jev_claim({_JEV})")
    op.execute(f"ALTER FUNCTION public.reference_jev_claim_discovery_inner({_JEV}) RENAME TO reference_jev_claim")
    op.execute(f"REVOKE ALL ON FUNCTION public.reference_jev_claim({_JEV}) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION public.reference_jev_claim({_JEV}) TO meu_braco_direito_correlator")
    op.execute("DROP INDEX reference_one_jev_intent_per_google")
    op.execute("""CREATE UNIQUE INDEX reference_one_jev_intent_per_google
      ON reference_provider_effects(tenant_id,business_id,parent_google_effect_id) WHERE provider='jev'""")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_effect_purpose")
    op.execute(
        "ALTER TABLE reference_provider_effects DROP COLUMN purpose, DROP COLUMN recommendation_batch_id, "
        "DROP COLUMN shortlist_mac"
    )
