"""Keep quarantined continuation failures distinct from an earlier request failure."""

from alembic import op

revision = "0116_motion_failure_identity"
down_revision = "0115_motion_storyboard_events"
branch_labels = None
depends_on = None


def definition(audit_operation):
    return f"""CREATE OR REPLACE FUNCTION motion_quarantine_request(p_tenant uuid,p_business uuid,p_request uuid,
      p_actor uuid,p_token uuid,p_code text,p_event uuid) RETURNS boolean
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE operation uuid;
      BEGIN
        IF p_tenant IS DISTINCT FROM nullif(current_setting('app.tenant_id',true),'')::uuid
          OR p_actor IS DISTINCT FROM nullif(current_setting('app.actor_id',true),'')::uuid
          OR p_code !~ '^[A-Z0-9_]{{1,100}}$' THEN RETURN false; END IF;
        UPDATE public.motion_requests SET state='uncertain',failure_code=p_code,finished_at=clock_timestamp()
          WHERE tenant_id=p_tenant AND business_id=p_business AND id=p_request AND actor_id=p_actor
            AND execution_token=p_token AND state='running' RETURNING operation_id INTO operation;
        IF NOT FOUND THEN RETURN false; END IF;
        INSERT INTO public.audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(p_tenant,p_actor,{audit_operation},'motion.failed',p_business);
        INSERT INTO public.outbox_events(id,tenant_id,event_type,payload)
          VALUES(p_event,p_tenant,'motion.failed',jsonb_build_object('business_id',p_business,
            'actor_id',p_actor,'operation_id',operation));
        RETURN true;
      END $$"""


def upgrade():
    op.execute(definition("p_event"))


def downgrade():
    op.execute(definition("operation"))
