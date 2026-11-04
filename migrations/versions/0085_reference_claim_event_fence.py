"""Tie provider claims to the specific event created with each intent."""

from alembic import op

revision = "0085_reference_claim_event_fence"
down_revision = "0084_reference_google_intent"
branch_labels = None
depends_on = None

_GOOGLE = "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text"
_JEV = _GOOGLE + ",uuid,uuid,text,bigint"


def upgrade():
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    for provider, signature in (("google", _GOOGLE), ("jev", _JEV)):
        op.execute(
            f"ALTER FUNCTION public.reference_{provider}_claim({signature}) RENAME TO reference_{provider}_claim_inner"
        )
        op.execute(
            f"REVOKE ALL ON FUNCTION public.reference_{provider}_claim_inner({signature}) "
            "FROM PUBLIC,meu_braco_direito_correlator"
        )
        extra = (
            ",p_parent uuid,p_parent_token uuid,p_batch_mac text,p_context_version bigint" if provider == "jev" else ""
        )
        forwarded = ",p_parent,p_parent_token,p_batch_mac,p_context_version" if provider == "jev" else ""
        op.execute(f"""CREATE FUNCTION public.reference_{provider}_claim(
          p_effect uuid,p_event uuid,p_mac text,p_business uuid,p_search uuid,p_pilot uuid,
          p_amount bigint,p_key text,p_tariff text,p_credential text,p_mask text{extra})
          RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
          DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
            a uuid := nullif(current_setting('app.actor_id',true),'')::uuid; expected uuid;
          BEGIN
            SELECT request_event_id INTO expected FROM public.reference_provider_effects
              WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND id=p_effect AND provider='{provider}';
            IF NOT FOUND OR (expected IS NOT NULL AND expected IS DISTINCT FROM p_event) THEN
              RAISE EXCEPTION 'REFERENCE_PROVIDER_EVENT_INVALID'; END IF;
            RETURN public.reference_{provider}_claim_inner(p_effect,p_event,p_mac,p_business,p_search,p_pilot,
              p_amount,p_key,p_tariff,p_credential,p_mask{forwarded});
          END $$""")
        op.execute(
            f"ALTER FUNCTION public.reference_{provider}_claim({signature}) OWNER TO meu_braco_direito_reference_ledger"
        )
        op.execute(f"REVOKE ALL ON FUNCTION public.reference_{provider}_claim({signature}) FROM PUBLIC")
        op.execute(
            f"GRANT EXECUTE ON FUNCTION public.reference_{provider}_claim({signature}) TO meu_braco_direito_correlator"
        )


def downgrade():
    op.execute("LOCK TABLE reference_provider_effects IN ACCESS EXCLUSIVE MODE")
    for provider, signature in (("google", _GOOGLE), ("jev", _JEV)):
        op.execute(f"DROP FUNCTION public.reference_{provider}_claim({signature})")
        op.execute(
            f"ALTER FUNCTION public.reference_{provider}_claim_inner({signature}) RENAME TO reference_{provider}_claim"
        )
        op.execute(f"REVOKE ALL ON FUNCTION public.reference_{provider}_claim({signature}) FROM PUBLIC")
        op.execute(
            f"GRANT EXECUTE ON FUNCTION public.reference_{provider}_claim({signature}) TO meu_braco_direito_correlator"
        )
