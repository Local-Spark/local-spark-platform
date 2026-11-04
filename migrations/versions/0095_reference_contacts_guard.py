"""Inactive, cycle-deduplicated Place ID contacts effects.

There is no runtime writer, claim grant, provider integration or cleanup here.
One lookup owns one attempted effect until a later reconciler can prove a
conclusive failure and safely add retry attempts.
"""

from alembic import op

revision = "0095_reference_contacts_guard"
down_revision = "0094_reference_context_loader"
branch_labels = None
depends_on = None

_CLAIM = "uuid,uuid,uuid,uuid,text,uuid,bigint,text,text,text,text"


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_provider_effects,reference_provider_tariffs IN ACCESS EXCLUSIVE MODE")
    op.execute("ALTER TABLE reference_provider_tariffs DROP CONSTRAINT reference_provider_tariff_charge_class")
    op.execute("""ALTER TABLE reference_provider_tariffs ADD CONSTRAINT reference_provider_tariff_charge_class CHECK(
      (provider='google' AND (field_mask LIKE 'places.%' OR field_mask LIKE 'geocode-v4:results.%')) OR
      (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$') OR
      (provider='apify' AND field_mask ~ '^apify-(instagram-feed|place-contacts):[0-9]+[.][0-9]+[.][0-9]+$'))""")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_provider_check")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effect_charge_class")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_jev_parent")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_provider_check
      CHECK(provider IN ('google','jev','apify')),
      ADD CONSTRAINT reference_provider_effect_charge_class CHECK(
        (provider='google' AND field_mask LIKE 'places.%') OR
        (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$') OR
        (provider='apify' AND field_mask ~ '^apify-place-contacts:[0-9]+[.][0-9]+[.][0-9]+$')),
      ADD CONSTRAINT reference_provider_jev_parent CHECK(
        (provider='google' AND parent_google_effect_id IS NULL AND
          (source_batch_mac IS NULL OR source_batch_mac ~ '^[0-9a-f]{64}$')) OR
        (provider IN ('jev','apify') AND parent_google_effect_id IS NOT NULL
          AND source_batch_mac IS NOT NULL AND source_batch_mac ~ '^[0-9a-f]{64}$'))""")
    # Fixed-size digest avoids indexing an opaque 2,048-character UTF-8 ID.
    # A digest collision is rejected by the unique index, never treated as an
    # identical Place ID; the future writer must surface that failure explicitly.
    op.execute("""CREATE FUNCTION public.reference_place_id_sha256(value text) RETURNS bytea
      LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE SET search_path=pg_catalog AS $$
        SELECT sha256(convert_to(value,'UTF8')) $$""")
    # The older tables indexed the full UTF-8 ID. Their 2,048-character
    # allowance can exceed PostgreSQL's B-tree row size for multibyte text.
    for table, columns, index in (
        ("reference_provider_places", "tenant_id, business_id, place_id", "reference_places_place_digest"),
        (
            "reference_filtered_batch_candidates",
            "tenant_id, business_id, batch_id, place_id",
            "reference_filtered_place_digest",
        ),
    ):
        op.execute(f"""DO $$ DECLARE constraint_name text; BEGIN
          SELECT conname INTO constraint_name FROM pg_constraint
          WHERE conrelid='public.{table}'::regclass AND contype='u'
            AND pg_get_constraintdef(oid)='UNIQUE ({columns})';
          IF constraint_name IS NULL THEN RAISE EXCEPTION 'REFERENCE_PLACE_ID_CONSTRAINT_MISSING'; END IF;
          EXECUTE format('ALTER TABLE public.{table} DROP CONSTRAINT %I',constraint_name);
        END $$""")
        prefix = "tenant_id,business_id,batch_id" if "batch_id" in columns else "tenant_id,business_id"
        op.execute(f"CREATE UNIQUE INDEX {index} ON {table}({prefix},public.reference_place_id_sha256(place_id))")
    op.execute("""CREATE TABLE reference_contacts_lookups (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),cycle_id uuid NOT NULL,search_id uuid NOT NULL,
      batch_id uuid NOT NULL,candidate_id uuid NOT NULL,
      place_id text NOT NULL CHECK(length(place_id) BETWEEN 1 AND 2048),
      PRIMARY KEY(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,cycle_id) REFERENCES reference_real_cycles(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,search_id) REFERENCES reference_provider_searches(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,batch_id,candidate_id)
        REFERENCES reference_private_shortlist(tenant_id,business_id,batch_id,candidate_id))""")
    op.execute("""CREATE UNIQUE INDEX reference_contacts_cycle_place
      ON reference_contacts_lookups(tenant_id,business_id,cycle_id,public.reference_place_id_sha256(place_id))""")
    op.execute("""CREATE TABLE reference_contacts_effect_links (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,lookup_id uuid NOT NULL,effect_id uuid NOT NULL,
      PRIMARY KEY(tenant_id,business_id,effect_id),UNIQUE(tenant_id,business_id,lookup_id),
      FOREIGN KEY(tenant_id,business_id,lookup_id) REFERENCES reference_contacts_lookups(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,effect_id) REFERENCES reference_provider_effects(tenant_id,business_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    op.execute(f"""CREATE POLICY reference_contacts_shortlist_event ON outbox_events FOR SELECT
      TO meu_braco_direito_reference_ledger USING(tenant_id={tenant}
        AND event_type='reference.private_shortlist_prepared' AND payload->>'actor_id'={actor}::text)""")
    for table in ("reference_contacts_lookups", "reference_contacts_effect_links"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY reference_contacts_ledger ON {table} TO meu_braco_direito_reference_ledger
          USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_reference_ledger")
    op.execute("""GRANT UPDATE(place_id) ON reference_contacts_lookups TO meu_braco_direito_reference_ledger""")
    op.execute("""CREATE FUNCTION public.reference_contacts_claim(
      p_business uuid,p_lookup uuid,p_effect uuid,p_event uuid,p_mac text,p_pilot uuid,p_amount bigint,
      p_key text,p_tariff text,p_credential text,p_class text)
      RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid;
        l public.reference_contacts_lookups%ROWTYPE; e public.reference_provider_effects%ROWTYPE;
        b public.reference_filtered_batches%ROWTYPE; g public.reference_provider_effects%ROWTYPE;
        j public.reference_provider_effects%ROWTYPE; s public.reference_provider_searches%ROWTYPE;
        current_version bigint;
      BEGIN
        IF t IS NULL OR a IS NULL OR p_business IS NULL OR p_lookup IS NULL OR p_effect IS NULL
          OR p_event IS NULL OR p_mac IS NULL OR p_mac !~ '^[0-9a-f]{64}$' OR p_pilot IS NULL THEN
          RAISE EXCEPTION 'REFERENCE_CONTACTS_INTENT_INVALID'; END IF;
        SELECT * INTO l FROM public.reference_contacts_lookups WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_lookup;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='apify' AND purpose='discovery';
        IF l.id IS NULL OR e.id IS NULL OR e.request_event_id IS DISTINCT FROM p_event
          OR NOT EXISTS(SELECT 1 FROM public.reference_contacts_effect_links x WHERE x.tenant_id=t
            AND x.business_id=p_business AND x.lookup_id=l.id AND x.effect_id=e.id) THEN
          RAISE EXCEPTION 'REFERENCE_CONTACTS_INTENT_INVALID'; END IF;
        IF e.state<>'pending' THEN
          RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,l.search_id,p_pilot,
            p_amount,p_key,p_tariff,p_credential,p_class);
        END IF;
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT version INTO current_version FROM public.business_context_heads
          WHERE tenant_id=t AND business_id=p_business FOR SHARE;
        PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
        SELECT * INTO l FROM public.reference_contacts_lookups WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_lookup FOR SHARE;
        SELECT * INTO b FROM public.reference_filtered_batches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=l.batch_id AND search_id=l.search_id;
        PERFORM 1 FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND id IN (p_effect,b.google_effect_id,b.jev_effect_id) ORDER BY id FOR UPDATE;
        SELECT * INTO e FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=p_effect AND provider='apify' AND purpose='discovery';
        IF e.state<>'pending' THEN
          RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,l.search_id,p_pilot,
            p_amount,p_key,p_tariff,p_credential,p_class);
        END IF;
        SELECT * INTO s FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=l.search_id;
        SELECT * INTO g FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=b.google_effect_id AND provider='google';
        SELECT * INTO j FROM public.reference_provider_effects WHERE tenant_id=t AND business_id=p_business
          AND actor_id=a AND id=b.jev_effect_id AND provider='jev' AND purpose='discovery';
        IF l.id IS NULL OR b.id IS NULL OR s.id IS NULL OR g.id IS NULL OR j.id IS NULL
          OR current_version IS DISTINCT FROM s.context_version OR s.cycle_id IS DISTINCT FROM l.cycle_id
          OR e.search_id IS DISTINCT FROM s.id OR e.pilot_id IS DISTINCT FROM p_pilot
          OR b.context_version IS DISTINCT FROM s.context_version
          OR g.search_id IS DISTINCT FROM s.id OR j.search_id IS DISTINCT FROM s.id
          OR g.pilot_id IS DISTINCT FROM p_pilot OR j.pilot_id IS DISTINCT FROM p_pilot
          OR e.parent_google_effect_id IS DISTINCT FROM g.id OR e.source_batch_mac IS DISTINCT FROM b.source_batch_mac
          OR g.source_batch_mac IS DISTINCT FROM b.source_batch_mac
          OR j.source_batch_mac IS DISTINCT FROM b.source_batch_mac OR j.parent_google_effect_id IS DISTINCT FROM g.id
          OR g.state<>'completed_filtered' OR j.state<>'completed_filtered'
          OR NOT EXISTS(SELECT 1 FROM public.reference_private_shortlist_headers h
            JOIN public.outbox_events o ON o.tenant_id=h.tenant_id AND o.id=h.event_id
              AND o.event_type='reference.private_shortlist_prepared' AND o.payload=jsonb_build_object(
                'business_id',p_business::text,'actor_id',a::text,'operation_id',h.operation_id::text)
            WHERE h.tenant_id=t AND h.business_id=p_business AND h.batch_id=b.id AND h.actor_id=a)
          OR NOT EXISTS(SELECT 1 FROM public.reference_private_shortlist q
            JOIN public.reference_filtered_batch_candidates c ON c.tenant_id=q.tenant_id
              AND c.business_id=q.business_id AND c.batch_id=q.batch_id AND c.candidate_id=q.candidate_id
            WHERE q.tenant_id=t AND q.business_id=p_business AND q.batch_id=b.id AND q.candidate_id=l.candidate_id
              AND c.place_id=l.place_id) THEN RAISE EXCEPTION 'REFERENCE_CONTACTS_SOURCE_INVALID'; END IF;
        RETURN public.reference_provider_claim(p_effect,p_event,p_mac,p_business,s.id,p_pilot,
          p_amount,p_key,p_tariff,p_credential,p_class);
      END $$""")
    op.execute(f"ALTER FUNCTION public.reference_contacts_claim({_CLAIM}) OWNER TO meu_braco_direito_reference_ledger")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.reference_contacts_claim({_CLAIM}) FROM PUBLIC,meu_braco_direito_correlator"
    )


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute(
        "LOCK TABLE reference_contacts_effect_links,reference_contacts_lookups,reference_provider_effects "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_contacts_lookups) OR
      EXISTS(SELECT 1 FROM reference_provider_effects WHERE provider='apify') OR
      EXISTS(SELECT 1 FROM reference_provider_tariffs WHERE field_mask LIKE 'apify-place-contacts:%') THEN
      RAISE EXCEPTION 'REFERENCE_CONTACTS_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_provider_places WHERE octet_length(place_id)>2300)
      OR EXISTS(SELECT 1 FROM reference_filtered_batch_candidates WHERE octet_length(place_id)>2300) THEN
      RAISE EXCEPTION 'REFERENCE_PLACE_ID_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute(f"DROP FUNCTION public.reference_contacts_claim({_CLAIM})")
    op.execute("DROP POLICY reference_contacts_shortlist_event ON outbox_events")
    op.execute("DROP TABLE reference_contacts_effect_links,reference_contacts_lookups")
    op.execute("DROP INDEX reference_places_place_digest,reference_filtered_place_digest")
    op.execute("""ALTER TABLE reference_provider_places ADD CONSTRAINT reference_provider_places_place_id_unique
      UNIQUE(tenant_id,business_id,place_id)""")
    op.execute("""ALTER TABLE reference_filtered_batch_candidates ADD CONSTRAINT reference_filtered_place_id_unique
      UNIQUE(tenant_id,business_id,batch_id,place_id)""")
    op.execute("DROP FUNCTION public.reference_place_id_sha256(text)")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_jev_parent")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effect_charge_class")
    op.execute("ALTER TABLE reference_provider_effects DROP CONSTRAINT reference_provider_effects_provider_check")
    op.execute("""ALTER TABLE reference_provider_effects ADD CONSTRAINT reference_provider_effects_provider_check
      CHECK(provider IN ('google','jev')),
      ADD CONSTRAINT reference_provider_effect_charge_class CHECK(
        (provider='google' AND field_mask LIKE 'places.%') OR
        (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$')),
      ADD CONSTRAINT reference_provider_jev_parent CHECK(
        (provider='google' AND parent_google_effect_id IS NULL AND
          (source_batch_mac IS NULL OR source_batch_mac ~ '^[0-9a-f]{64}$')) OR
        (provider='jev' AND parent_google_effect_id IS NOT NULL AND source_batch_mac IS NOT NULL
          AND source_batch_mac ~ '^[0-9a-f]{64}$'))""")
    op.execute("ALTER TABLE reference_provider_tariffs DROP CONSTRAINT reference_provider_tariff_charge_class")
    op.execute("""ALTER TABLE reference_provider_tariffs ADD CONSTRAINT reference_provider_tariff_charge_class CHECK(
      (provider='google' AND (field_mask LIKE 'places.%' OR field_mask LIKE 'geocode-v4:results.%')) OR
      (provider='jev' AND field_mask ~ '^jev-model:[a-zA-Z0-9_.-]{1,120}$') OR
      (provider='apify' AND field_mask ~ '^apify-instagram-feed:[0-9]+[.][0-9]+[.][0-9]+$'))""")
