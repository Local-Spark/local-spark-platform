"""Extend the inactive reference-effect ledger to Jev, with the same pilot cap."""

from alembic import op

revision = "0078_reference_jev_guard"
down_revision = "0077_reference_places_empty"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("LOCK TABLE reference_provider_effects,reference_provider_tariffs IN ACCESS EXCLUSIVE MODE")
    op.execute("ALTER TABLE reference_provider_tariffs DROP CONSTRAINT reference_provider_tariffs_provider_check")
    op.execute("""ALTER TABLE reference_provider_tariffs ADD CONSTRAINT reference_provider_tariffs_provider_check
      CHECK(provider IN ('google','jev'))""")
    op.execute("""ALTER TABLE reference_provider_tariffs ADD CONSTRAINT reference_provider_tariff_charge_class CHECK(
      (provider='google' AND field_mask LIKE 'places.%') OR
      (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$'))""")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_provider_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_provider_check
      CHECK(provider IN ('google','jev'))""")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effect_charge_class CHECK(
      (provider='google' AND field_mask LIKE 'places.%') OR
      (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$'))""")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_empty_only_google
      CHECK(state<>'completed_empty' OR provider='google')""")
    op.execute("""ALTER TABLE reference_provider_effects ADD COLUMN parent_google_effect_id uuid,
      ADD COLUMN source_batch_mac char(64),
      ADD CONSTRAINT reference_provider_jev_parent CHECK(
        (provider='google' AND parent_google_effect_id IS NULL AND source_batch_mac IS NULL) OR
        (provider='jev' AND parent_google_effect_id IS NOT NULL AND source_batch_mac IS NOT NULL
          AND source_batch_mac ~ '^[0-9a-f]{64}$')),
      ADD FOREIGN KEY(tenant_id,business_id,parent_google_effect_id)
        REFERENCES reference_provider_effects(tenant_id,business_id,id)""")
    # A worker must go through a provider-specific wrapper; otherwise it could
    # bypass the parent Google fence when claiming a Jev effect.
    op.execute("""REVOKE EXECUTE ON FUNCTION
      public.reference_provider_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text)
      FROM meu_braco_direito_correlator""")
    op.execute("""CREATE FUNCTION public.reference_google_claim(
      p_effect uuid,p_event uuid,p_mac text,p_business uuid,p_search uuid,p_pilot uuid,
      p_amount bigint,p_key text,p_tariff text,p_credential text,p_mask text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE;
      BEGIN
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND actor_id=a
          AND business_id=p_business AND id=p_effect AND provider='google';
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_INTENT_INVALID'; END IF;
        IF e.state<>'pending' THEN
          RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
            p_amount,p_key,p_tariff,p_credential,p_mask);
        END IF;
        IF NOT public.lock_reference_cost_owner() THEN
          RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
            p_amount,p_key,p_tariff,p_credential,p_mask);
        END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        PERFORM 1 FROM public.reference_provider_effects WHERE tenant_id=t AND actor_id=a
          AND business_id=p_business AND id=p_effect AND provider='google' FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_INTENT_INVALID'; END IF;
        RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
          p_amount,p_key,p_tariff,p_credential,p_mask);
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_google_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("""REVOKE ALL ON FUNCTION
      public.reference_google_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text) FROM PUBLIC""")
    op.execute("""GRANT EXECUTE ON FUNCTION
      public.reference_google_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text)
      TO meu_braco_direito_correlator""")
    op.execute("""CREATE FUNCTION public.reference_jev_claim(
      p_effect uuid,p_event uuid,p_mac text,p_business uuid,p_search uuid,p_pilot uuid,
      p_amount bigint,p_key text,p_tariff text,p_credential text,p_mask text,
      p_parent uuid,p_parent_token uuid,p_batch_mac text,p_context_version bigint)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        e public.reference_provider_effects%ROWTYPE; parent public.reference_provider_effects%ROWTYPE;
      BEGIN
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND actor_id=a
          AND business_id=p_business AND id=p_effect AND provider='jev';
        IF NOT FOUND OR e.parent_google_effect_id IS DISTINCT FROM p_parent
          OR e.source_batch_mac IS DISTINCT FROM p_batch_mac THEN
          RAISE EXCEPTION 'REFERENCE_JEV_PARENT_INVALID'; END IF;
        IF e.state<>'pending' THEN
          RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
            p_amount,p_key,p_tariff,p_credential,p_mask);
        END IF;
        IF NOT public.lock_reference_cost_owner() THEN
          SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND actor_id=a
            AND business_id=p_business AND id=p_effect AND provider='jev';
          IF FOUND AND e.state<>'pending' AND e.parent_google_effect_id IS NOT DISTINCT FROM p_parent
            AND e.source_batch_mac IS NOT DISTINCT FROM p_batch_mac THEN
            RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
              p_amount,p_key,p_tariff,p_credential,p_mask);
          END IF;
          RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE';
        END IF;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND actor_id=a
          AND business_id=p_business AND id=p_effect AND provider='jev' FOR SHARE;
        IF NOT FOUND OR e.parent_google_effect_id IS DISTINCT FROM p_parent
          OR e.source_batch_mac IS DISTINCT FROM p_batch_mac THEN
          RAISE EXCEPTION 'REFERENCE_JEV_PARENT_INVALID'; END IF;
        SELECT * INTO parent FROM public.reference_provider_effects WHERE tenant_id=t AND actor_id=a
          AND business_id=p_business AND id=p_parent AND provider='google' FOR SHARE;
        IF NOT FOUND OR parent.state<>'running' OR parent.executor_token IS DISTINCT FROM p_parent_token
          OR parent.search_id IS DISTINCT FROM p_search OR parent.pilot_id IS DISTINCT FROM p_pilot THEN
          RAISE EXCEPTION 'REFERENCE_JEV_PARENT_INVALID'; END IF;
        PERFORM 1 FROM public.reference_provider_searches WHERE tenant_id=t AND actor_id=a
          AND business_id=p_business AND id=p_search AND context_version=p_context_version FOR SHARE;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_JEV_PARENT_INVALID'; END IF;
        RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
          p_amount,p_key,p_tariff,p_credential,p_mask);
      END $$""")
    op.execute("""ALTER FUNCTION public.reference_jev_claim(
      uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,text,bigint)
      OWNER TO meu_braco_direito_reference_ledger""")
    op.execute("""REVOKE ALL ON FUNCTION public.reference_jev_claim(
      uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,text,bigint) FROM PUBLIC""")
    op.execute("""GRANT EXECUTE ON FUNCTION public.reference_jev_claim(
      uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,text,bigint)
      TO meu_braco_direito_correlator""")


def downgrade():
    op.execute("LOCK TABLE reference_provider_effects,reference_provider_tariffs IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_provider_effects WHERE provider='jev') OR
         EXISTS(SELECT 1 FROM reference_provider_tariffs WHERE provider='jev') THEN
        RAISE EXCEPTION 'REFERENCE_JEV_GUARD_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("""DROP FUNCTION public.reference_jev_claim(
      uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text,uuid,uuid,text,bigint)""")
    op.execute(
        """DROP FUNCTION public.reference_google_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text)"""
    )
    op.execute("""GRANT EXECUTE ON FUNCTION
      public.reference_provider_claim(uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text)
      TO meu_braco_direito_correlator""")
    op.execute(
        "ALTER TABLE reference_provider_effects DROP COLUMN parent_google_effect_id,DROP COLUMN source_batch_mac"
    )
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_empty_only_google")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effect_charge_class")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_provider_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_provider_check
      CHECK(provider='google')""")
    op.execute("ALTER TABLE reference_provider_tariffs DROP CONSTRAINT reference_provider_tariff_charge_class")
    op.execute("ALTER TABLE reference_provider_tariffs DROP CONSTRAINT reference_provider_tariffs_provider_check")
    op.execute("""ALTER TABLE reference_provider_tariffs ADD CONSTRAINT reference_provider_tariffs_provider_check
      CHECK(provider='google')""")
