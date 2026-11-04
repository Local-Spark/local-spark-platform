"""Preserve late Apify receipts and block admission on a true accounting overrun."""

from alembic import op

revision = "0111_apify_cost_revisions"
down_revision = "0110_reference_generation"
branch_labels = None
depends_on = None
_ROLE = "meu_braco_direito_reference_ledger"
_CONTACTS_SIGNATURE = "reference_contacts_record_cost(uuid,uuid,uuid,text,bigint)"
_FEED_SIGNATURE = "reference_feed_record_terminal_cost(uuid,uuid,uuid,bigint)"
_HELPER = "reference_apply_apify_receipt(uuid,uuid,uuid,bigint)"


def _replace(signature, before, after):
    old, new = before.replace("'", "''"), after.replace("'", "''")
    op.execute(f"""DO $$ DECLARE definition text; BEGIN
      SELECT pg_get_functiondef('public.{signature}'::regprocedure) INTO definition;
      IF position('{old}' IN definition)=0 THEN RAISE EXCEPTION 'APIFY_RECEIPT_WRITER_CHANGED'; END IF;
      EXECUTE replace(definition,'{old}','{new}'); END $$""")


def _pilot_constraint(expression):
    op.execute(f"""DO $$ DECLARE constraint_name text; BEGIN
      SELECT conname INTO STRICT constraint_name FROM pg_constraint
        WHERE conrelid='public.reference_provider_pilots'::regclass AND contype='c'
          AND position('reserved_usd_micros' IN pg_get_constraintdef(oid))>0;
      EXECUTE format('ALTER TABLE public.reference_provider_pilots DROP CONSTRAINT %I',constraint_name);
      EXECUTE format('ALTER TABLE public.reference_provider_pilots ADD CONSTRAINT %I CHECK ({expression})',
        constraint_name);
    END $$""")


def upgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    # The cap gates admission. Observed expense must remain representable even
    # when a previously released estimate allowed its headroom to be reused.
    _pilot_constraint("reserved_usd_micros>=0")
    op.execute(f"GRANT UPDATE(active) ON reference_provider_pilots TO {_ROLE}")
    op.execute("""CREATE TABLE reference_apify_cost_receipts(
      id uuid PRIMARY KEY,tenant_id uuid NOT NULL,business_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),effect_id uuid NOT NULL,
      reservation_id uuid NOT NULL REFERENCES reference_cost_reservations(id),
      previous_usd_micros bigint CHECK(previous_usd_micros>=0),
      reported_usd_micros bigint NOT NULL CHECK(reported_usd_micros BETWEEN 0 AND 1000000000000),
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros>0),
      block_reason text CHECK(block_reason IN ('reservation','pilot','policy','monthly','provider_monthly',
        'search','provider_search')),
      observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(tenant_id,effect_id,reported_usd_micros),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,id) REFERENCES outbox_events(tenant_id,id) DEFERRABLE INITIALLY DEFERRED,
      CHECK(previous_usd_micros IS NULL OR reported_usd_micros>previous_usd_micros))""")
    op.execute("ALTER TABLE reference_apify_cost_receipts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reference_apify_cost_receipts FORCE ROW LEVEL SECURITY")
    op.execute(f"""CREATE POLICY apify_cost_receipt_ledger ON reference_apify_cost_receipts TO {_ROLE}
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND actor_id=nullif(current_setting('app.actor_id',true),'')::uuid)""")
    op.execute(f"GRANT SELECT,INSERT ON reference_apify_cost_receipts TO {_ROLE}")
    op.execute(_APPLY)
    op.execute(f"ALTER FUNCTION public.{_HELPER} OWNER TO {_ROLE}")
    op.execute(f"REVOKE ALL ON FUNCTION public.{_HELPER} FROM PUBLIC")
    _replace(_CONTACTS_SIGNATURE, _CONTACTS_BEFORE, _CONTACTS_AFTER)
    _replace(_FEED_SIGNATURE, _FEED_BEFORE, _FEED_AFTER)


_APPLY = """CREATE FUNCTION public.reference_apply_apify_receipt(
  p_business uuid,p_effect uuid,p_reservation uuid,p_actual bigint) RETURNS void
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;
    a uuid:=nullif(current_setting('app.actor_id',true),'')::uuid;
    r public.reference_cost_reservations%ROWTYPE;pilot public.reference_provider_pilots%ROWTYPE;
    pol public.reference_cost_policies%ROWTYPE;pp public.reference_cost_policy_providers%ROWTYPE;
    old_cost bigint;previous_used bigint;release_hold bigint;changed integer;receipt uuid;
    blocked text;cm date;used numeric;provider_used numeric;kind text;
  BEGIN
    IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70));
    SELECT * INTO r FROM public.reference_cost_reservations WHERE tenant_id=t AND business_id=p_business
      AND actor_id=a AND id=p_reservation AND effect_id=p_effect AND provider='apify' FOR UPDATE;
    IF r.id IS NULL OR p_actual IS NULL OR p_actual NOT BETWEEN 0 AND 1000000000000 THEN
      RAISE EXCEPTION 'APIFY_RECEIPT_INVALID'; END IF;
    IF r.feed_window_id IS NOT NULL THEN
      kind:='feed';
      SELECT reported_cost_usd_micros INTO old_cost FROM reference_feed_resources
        WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND effect_id=p_effect FOR UPDATE;
    ELSE
      kind:='contacts';
      SELECT reported_cost_usd_micros INTO old_cost FROM reference_contacts_runs
        WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND effect_id=p_effect FOR UPDATE;
    END IF;
    IF NOT FOUND THEN RAISE EXCEPTION 'APIFY_RECEIPT_RUN_INVALID'; END IF;
    IF r.state='completed' THEN
      IF old_cost IS DISTINCT FROM r.actual_usd_micros OR old_cost IS NULL OR p_actual<old_cost THEN
        RAISE EXCEPTION '%_RECEIPT_CONFLICT',CASE WHEN kind='feed' THEN 'REFERENCE_FEED' ELSE 'CONTACTS' END; END IF;
      IF p_actual=old_cost THEN RETURN; END IF;
      previous_used:=old_cost;release_hold:=0;
    ELSE
      IF r.state NOT IN ('claimed','uncertain') OR old_cost IS NOT NULL OR r.actual_usd_micros IS NOT NULL THEN
        RAISE EXCEPTION '%_RECEIPT_CONFLICT',CASE WHEN kind='feed' THEN 'REFERENCE_FEED' ELSE 'CONTACTS' END; END IF;
      previous_used:=r.reserved_usd_micros;release_hold:=r.reserved_usd_micros;
    END IF;
    UPDATE reference_provider_pilots
      SET reserved_usd_micros=reserved_usd_micros-previous_used+p_actual
      WHERE id=r.pilot_id AND reserved_usd_micros>=previous_used RETURNING * INTO pilot;
    IF pilot.id IS NULL THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
    UPDATE reference_cost_monthly
      SET committed_usd_micros=committed_usd_micros-previous_used+p_actual,
        outstanding_usd_micros=outstanding_usd_micros-release_hold
      WHERE month=r.month AND provider IN ('all','apify') AND committed_usd_micros>=previous_used
        AND outstanding_usd_micros>=release_hold;
    GET DIAGNOSTICS changed=ROW_COUNT;
    IF changed<>2 THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
    UPDATE reference_cost_reservations SET state='completed',actual_usd_micros=p_actual,
      updated_at=clock_timestamp() WHERE tenant_id=t AND id=r.id;
    IF kind='feed' THEN
      UPDATE reference_feed_resources SET reported_cost_usd_micros=p_actual
        WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect;
    ELSE
      UPDATE reference_contacts_runs SET reported_cost_usd_micros=p_actual
        WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect;
    END IF;
    IF p_actual>r.reserved_usd_micros THEN blocked:='reservation';
    ELSIF pilot.reserved_usd_micros>pilot.cap_usd_micros THEN blocked:='pilot'; END IF;
    SELECT p.* INTO pol FROM reference_cost_policy_head h JOIN reference_cost_policies p ON p.id=h.policy_id
      WHERE h.singleton;
    SELECT * INTO pp FROM reference_cost_policy_providers WHERE policy_id=pol.id AND provider='apify';
    IF blocked IS NULL AND (pol.id IS NULL OR pp.policy_id IS NULL) THEN blocked:='policy'; END IF;
    IF blocked IS NULL THEN
      cm:=date_trunc('month',clock_timestamp() AT TIME ZONE pol.timezone)::date;
      SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
        INTO used FROM reference_cost_monthly WHERE provider='all';
      SELECT coalesce(sum(CASE WHEN month=cm THEN committed_usd_micros ELSE outstanding_usd_micros END),0)
        INTO provider_used FROM reference_cost_monthly WHERE provider='apify';
      IF used>pol.monthly_total THEN blocked:='monthly';
      ELSIF provider_used>pp.monthly_total THEN blocked:='provider_monthly'; END IF;
    END IF;
    IF blocked IS NULL THEN
      IF r.feed_window_id IS NOT NULL THEN
        SELECT coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END),0),
          coalesce(sum(CASE WHEN state='completed' THEN actual_usd_micros ELSE reserved_usd_micros END)
            FILTER(WHERE provider='apify'),0) INTO used,provider_used FROM reference_cost_reservations
          WHERE tenant_id=t AND business_id=p_business AND feed_window_id=r.feed_window_id;
      ELSE
        SELECT usage.total_used,usage.provider_used INTO used,provider_used
          FROM public.reference_search_cost_usage(p_business,r.provider_search_id,'apify') usage;
      END IF;
      IF used>pol.per_search THEN blocked:='search';
      ELSIF provider_used>pp.per_search THEN blocked:='provider_search'; END IF;
    END IF;
    IF blocked IS NOT NULL THEN UPDATE reference_provider_pilots SET active=false WHERE id=r.pilot_id; END IF;
    receipt:=gen_random_uuid();
    INSERT INTO reference_apify_cost_receipts(id,tenant_id,business_id,actor_id,effect_id,reservation_id,
      previous_usd_micros,reported_usd_micros,reserved_usd_micros,block_reason)
      VALUES(receipt,t,p_business,a,p_effect,r.id,old_cost,p_actual,r.reserved_usd_micros,blocked);
    INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
      VALUES(t,a,CASE WHEN old_cost IS NULL THEN p_effect ELSE receipt END,
        CASE WHEN old_cost IS NOT NULL THEN 'reference.apify_cost_revised'
          WHEN kind='feed' THEN 'reference.feed_cost_reported' ELSE 'reference.contacts_cost_reported' END,r.id);
    IF blocked IS NOT NULL THEN
      INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
        VALUES(t,a,receipt,'reference.pilot_blocked_by_cost',r.pilot_id); END IF;
    INSERT INTO outbox_events(id,tenant_id,event_type,payload) VALUES(receipt,t,'reference.provider_cost_changed',
      jsonb_build_object('business_id',p_business::text,'actor_id',a::text,'operation_id',receipt::text));
  END $$"""


def downgrade():
    op.execute("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))")
    op.execute("LOCK TABLE reference_apify_cost_receipts IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security=off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM reference_apify_cost_receipts) OR
      EXISTS(SELECT 1 FROM reference_provider_pilots WHERE reserved_usd_micros>cap_usd_micros) THEN
      RAISE EXCEPTION 'APIFY_RECEIPTS_PREVENT_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security=on")
    _replace(_CONTACTS_SIGNATURE, _CONTACTS_AFTER, _CONTACTS_BEFORE)
    _replace(_FEED_SIGNATURE, _FEED_AFTER, _FEED_BEFORE)
    op.execute(f"DROP FUNCTION public.{_HELPER}")
    op.execute("DROP TABLE reference_apify_cost_receipts")
    op.execute(f"REVOKE UPDATE(active) ON reference_provider_pilots FROM {_ROLE}")
    _pilot_constraint("reserved_usd_micros BETWEEN 0 AND cap_usd_micros")


_CONTACTS_BEFORE = """        IF r.id IS NULL OR p_actual IS NULL OR p_actual<0 OR p_actual>r.reserved_usd_micros THEN
          RAISE EXCEPTION 'CONTACTS_RECEIPT_INVALID'; END IF;
        IF old_cost IS NOT NULL THEN
          IF old_cost IS DISTINCT FROM p_actual OR r.state<>'completed' OR r.actual_usd_micros<>p_actual THEN
            RAISE EXCEPTION 'CONTACTS_RECEIPT_CONFLICT'; END IF;
          RETURN;
        END IF;
        IF r.state NOT IN ('claimed','uncertain') THEN RAISE EXCEPTION 'CONTACTS_RECEIPT_CONFLICT'; END IF;
        UPDATE public.reference_provider_pilots
          SET reserved_usd_micros=reserved_usd_micros-r.reserved_usd_micros+p_actual
          WHERE id=r.pilot_id AND reserved_usd_micros>=r.reserved_usd_micros;
        IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
        UPDATE public.reference_cost_monthly
          SET committed_usd_micros=committed_usd_micros-r.reserved_usd_micros+p_actual,
              outstanding_usd_micros=outstanding_usd_micros-r.reserved_usd_micros
          WHERE month=r.month AND provider IN ('all','apify')
            AND committed_usd_micros>=r.reserved_usd_micros AND outstanding_usd_micros>=r.reserved_usd_micros;
        GET DIAGNOSTICS changed=ROW_COUNT;
        IF changed<>2 THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
        UPDATE public.reference_cost_reservations SET state='completed',actual_usd_micros=p_actual,
          updated_at=clock_timestamp() WHERE tenant_id=t AND id=r.id;
        UPDATE public.reference_contacts_runs SET reported_cost_usd_micros=p_actual
          WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(t,a,p_effect,'reference.contacts_cost_reported',r.id);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(gen_random_uuid(),t,'reference.provider_cost_changed',jsonb_build_object(
            'business_id',p_business::text,'actor_id',a::text,'operation_id',p_effect::text));"""
_CONTACTS_AFTER = """        IF r.id IS NULL OR p_actual IS NULL OR p_actual<0 OR p_actual>1000000000000 THEN
          RAISE EXCEPTION 'CONTACTS_RECEIPT_INVALID'; END IF;
        PERFORM public.reference_apply_apify_receipt(p_business,p_effect,r.id,p_actual);"""
_FEED_BEFORE = """          IF p_actual<0 OR p_actual>r.reserved_usd_micros THEN
            RAISE EXCEPTION 'REFERENCE_FEED_RECEIPT_INVALID'; END IF;
          IF old_cost IS NOT NULL THEN
            IF old_cost IS DISTINCT FROM p_actual OR r.state<>'completed' OR r.actual_usd_micros<>p_actual THEN
              RAISE EXCEPTION 'REFERENCE_FEED_RECEIPT_CONFLICT'; END IF;
            RETURN;
          END IF;
          IF r.state NOT IN ('claimed','uncertain') THEN RAISE EXCEPTION 'REFERENCE_FEED_RECEIPT_CONFLICT'; END IF;
          UPDATE public.reference_provider_pilots
            SET reserved_usd_micros=reserved_usd_micros-r.reserved_usd_micros+p_actual
            WHERE id=r.pilot_id AND reserved_usd_micros>=r.reserved_usd_micros;
          IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
          UPDATE public.reference_cost_monthly
            SET committed_usd_micros=committed_usd_micros-r.reserved_usd_micros+p_actual,
                outstanding_usd_micros=outstanding_usd_micros-r.reserved_usd_micros
            WHERE month=r.month AND provider IN ('all','apify')
              AND committed_usd_micros>=r.reserved_usd_micros AND outstanding_usd_micros>=r.reserved_usd_micros;
          GET DIAGNOSTICS changed=ROW_COUNT;
          IF changed<>2 THEN RAISE EXCEPTION 'REFERENCE_MONTHLY_INCONSISTENT'; END IF;
          UPDATE public.reference_cost_reservations SET state='completed',actual_usd_micros=p_actual,
            updated_at=clock_timestamp() WHERE tenant_id=t AND business_id=p_business AND id=r.id;
          UPDATE public.reference_feed_resources SET reported_cost_usd_micros=p_actual
            WHERE tenant_id=t AND business_id=p_business AND effect_id=p_effect;"""
_FEED_AFTER = """          IF p_actual<0 OR p_actual>1000000000000 THEN
            RAISE EXCEPTION 'REFERENCE_FEED_RECEIPT_INVALID'; END IF;
          PERFORM public.reference_apply_apify_receipt(p_business,p_effect,r.id,p_actual);
          RETURN;"""
