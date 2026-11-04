"""Private, fixture-only effect intentions and consumed projections."""

from alembic import op

revision = "0072_reference_effect_simulation"
down_revision = "0071_reference_cost_policy"
branch_labels = None
depends_on = None


def upgrade():
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    own = f"tenant_id={tenant} AND actor_id={actor}"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} AND m.actor_id={actor} "
        "AND m.active AND m.role='owner')"
    )
    op.execute("""CREATE TABLE reference_simulated_effects (
      id uuid NOT NULL, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      discovery_id uuid NOT NULL REFERENCES reference_discoveries(id),
      fixture text NOT NULL CHECK(fixture IN ('fixture_place_1','fixture_profile_1','fixture_jev_1')),
      provider text NOT NULL CHECK(provider IN ('google','apify','jev')),
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros BETWEEN 1 AND 1000000000000),
      request_mac char(64) NOT NULL,
      state text NOT NULL CHECK(state IN ('pending','simulated','uncertain','cancelled')),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,id), FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    for table in ("reference_simulated_effects",):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY owner_access ON {table} TO meu_braco_direito_app USING({own} AND {owner}) "
            f"WITH CHECK({own} AND {owner})"
        )
        op.execute(
            f"CREATE POLICY worker_access ON {table} TO meu_braco_direito_correlator USING({own}) WITH CHECK({own})"
        )
    op.execute("GRANT SELECT,INSERT ON reference_simulated_effects TO meu_braco_direito_app")
    op.execute("GRANT SELECT,UPDATE(state) ON reference_simulated_effects TO meu_braco_direito_correlator")
    op.execute(f"""CREATE POLICY ledger_effect_read ON reference_simulated_effects FOR SELECT
      TO meu_braco_direito_reference_ledger USING({own})""")
    op.execute("GRANT SELECT ON reference_simulated_effects TO meu_braco_direito_reference_ledger")
    for table in ("reference_effect_projection", "reference_cost_projection"):
        op.execute(f"""CREATE TABLE {table} (
          tenant_id uuid NOT NULL, actor_id uuid NOT NULL, business_id uuid NOT NULL, effect_id uuid NOT NULL,
          state text NOT NULL, updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
          PRIMARY KEY(tenant_id,effect_id), FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY worker_access ON {table} TO meu_braco_direito_correlator USING({own}) WITH CHECK({own})"
        )
        op.execute(f"GRANT SELECT,INSERT,UPDATE(state,updated_at) ON {table} TO meu_braco_direito_correlator")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed','reference.effect_requested','reference.effect_completed','reference.cost_changed'))""")
    new_events = "('reference.effect_requested','reference.effect_completed','reference.cost_changed')"
    op.execute(f"""CREATE POLICY reference_effect_worker_events ON outbox_events FOR SELECT
      TO meu_braco_direito_correlator USING(tenant_id={tenant} AND event_type IN {new_events} AND
      payload->>'actor_id'={actor}::text)""")
    op.execute(f"""CREATE POLICY reference_effect_worker_emit ON outbox_events FOR INSERT
      TO meu_braco_direito_correlator WITH CHECK(tenant_id={tenant} AND event_type='reference.effect_completed' AND
      payload->>'actor_id'={actor}::text)""")
    op.execute("GRANT INSERT ON outbox_events TO meu_braco_direito_correlator")
    op.execute(f"""CREATE POLICY reference_effect_processed ON processed_events TO meu_braco_direito_correlator
      USING(tenant_id={tenant} AND EXISTS(SELECT 1 FROM outbox_events e WHERE e.id=event_id AND
        e.tenant_id={tenant} AND e.event_type IN {new_events} AND e.payload->>'actor_id'={actor}::text))
      WITH CHECK(tenant_id={tenant} AND EXISTS(SELECT 1 FROM outbox_events e WHERE e.id=event_id AND
        e.tenant_id={tenant} AND e.event_type IN {new_events} AND e.payload->>'actor_id'={actor}::text))""")
    op.execute("GRANT INSERT ON outbox_events TO meu_braco_direito_reference_ledger")
    op.execute(f"""CREATE POLICY reference_cost_emit ON outbox_events FOR INSERT TO meu_braco_direito_reference_ledger
      WITH CHECK(tenant_id={tenant} AND event_type='reference.cost_changed' AND payload->>'actor_id'={actor}::text)""")
    op.execute("""CREATE FUNCTION public.reference_cost_emit_change() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF (TG_OP='INSERT' OR OLD.state<>NEW.state) AND EXISTS(
          SELECT 1 FROM public.reference_simulated_effects e WHERE e.id=NEW.effect_id AND
            e.tenant_id=NEW.tenant_id AND e.actor_id=NEW.actor_id AND e.business_id=NEW.business_id) THEN
          INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
            VALUES(gen_random_uuid(),NEW.tenant_id,'reference.cost_changed',jsonb_build_object(
              'business_id',NEW.business_id::text,'actor_id',NEW.actor_id::text,'operation_id',NEW.effect_id::text));
        END IF;
        RETURN NEW;
      END $$""")
    op.execute("ALTER FUNCTION public.reference_cost_emit_change() OWNER TO meu_braco_direito_reference_ledger")
    op.execute("REVOKE ALL ON FUNCTION public.reference_cost_emit_change() FROM PUBLIC")
    op.execute("""CREATE TRIGGER reference_cost_emit AFTER INSERT OR UPDATE OF state ON reference_cost_reservations
      FOR EACH ROW EXECUTE FUNCTION public.reference_cost_emit_change()""")


def downgrade():
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_simulated_effects) OR EXISTS(SELECT 1 FROM outbox_events
        WHERE event_type IN ('reference.effect_requested','reference.effect_completed','reference.cost_changed')) THEN
        RAISE EXCEPTION 'REFERENCE_EFFECT_EVENTS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("DROP TRIGGER reference_cost_emit ON reference_cost_reservations")
    op.execute("DROP FUNCTION public.reference_cost_emit_change()")
    op.execute("DROP POLICY reference_cost_emit ON outbox_events")
    op.execute("REVOKE INSERT ON outbox_events FROM meu_braco_direito_reference_ledger")
    op.execute("DROP POLICY reference_effect_processed ON processed_events")
    op.execute("DROP POLICY reference_effect_worker_emit ON outbox_events")
    op.execute("DROP POLICY reference_effect_worker_events ON outbox_events")
    op.execute("REVOKE INSERT ON outbox_events FROM meu_braco_direito_correlator")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN
      ('business.created','brand_kit.changed','reference.created','reference.removed','reference.search_requested',
       'reference.selection_confirmed'))""")
    op.execute("DROP TABLE reference_cost_projection,reference_effect_projection,reference_simulated_effects")
