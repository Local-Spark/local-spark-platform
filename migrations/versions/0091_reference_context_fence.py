"""Reject new provider effects if their private business context changed."""

from alembic import op

revision = "0091_reference_context_fence"
down_revision = "0090_reference_geocoding_ledger"
branch_labels = None
depends_on = None

_GOOGLE_INTENT = "uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,bigint"
_JEV_INTENT = "uuid,uuid,uuid,uuid,uuid,uuid,uuid,text,text,text,text,text,bigint,text,bigint"
_GOOGLE_CLAIM = "uuid,uuid,text,uuid,uuid,uuid,bigint,text,text,text,text"
_JEV_CLAIM = _GOOGLE_CLAIM + ",uuid,uuid,text,bigint"
_RECO_CLAIM = _GOOGLE_CLAIM + ",uuid,uuid,uuid,text,bigint"
_GEOCODE_CLAIM = _GOOGLE_INTENT


def _wrap(name, signature, params, args, before, exposed):
    op.execute(f"ALTER FUNCTION public.{name}({signature}) RENAME TO {name}_context_inner")
    op.execute(
        f"REVOKE ALL ON FUNCTION public.{name}_context_inner({signature}) FROM PUBLIC,meu_braco_direito_correlator"
    )
    op.execute(f"""CREATE FUNCTION public.{name}({params}) RETURNS {("uuid" if "intent" in name else "jsonb")}
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE t uuid := nullif(current_setting('app.tenant_id',true),'')::uuid;
        a uuid := nullif(current_setting('app.actor_id',true),'')::uuid; current_version bigint; effect_state text;
      BEGIN
        {before}
        RETURN public.{name}_context_inner({args});
      END $$""")
    op.execute(f"ALTER FUNCTION public.{name}({signature}) OWNER TO meu_braco_direito_reference_ledger")
    op.execute(f"REVOKE ALL ON FUNCTION public.{name}({signature}) FROM PUBLIC,meu_braco_direito_correlator")
    if exposed:
        op.execute(f"GRANT EXECUTE ON FUNCTION public.{name}({signature}) TO meu_braco_direito_correlator")


def _intent_check(effect):
    return f"""IF NOT EXISTS(SELECT 1 FROM public.reference_provider_effects WHERE tenant_id=t
          AND business_id=p_business AND actor_id=a AND id={effect}) THEN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        IF NOT EXISTS(SELECT 1 FROM public.reference_provider_effects WHERE tenant_id=t
          AND business_id=p_business AND actor_id=a AND id={effect}) THEN
          PERFORM 1 FROM public.reference_provider_searches WHERE tenant_id=t AND business_id=p_business
            AND actor_id=a AND id=p_search AND context_version=p_context AND state='pending';
          IF NOT FOUND THEN RAISE EXCEPTION 'REFERENCE_PROVIDER_SEARCH_INACTIVE'; END IF;
        END IF;
        SELECT version INTO current_version FROM public.business_context_heads
          WHERE tenant_id=t AND business_id=p_business FOR SHARE;
        IF NOT EXISTS(SELECT 1 FROM public.reference_provider_effects WHERE tenant_id=t
          AND business_id=p_business AND actor_id=a AND id={effect})
          AND current_version IS DISTINCT FROM p_context THEN RAISE EXCEPTION 'REFERENCE_CONTEXT_STALE'; END IF;
      END IF;"""


def _claim_check(table, expected):
    return f"""SELECT state INTO effect_state FROM public.{table} WHERE tenant_id=t
        AND business_id=p_business AND actor_id=a AND id=p_effect;
      IF effect_state='pending' THEN
        IF NOT public.lock_reference_cost_owner() THEN RAISE EXCEPTION 'REFERENCE_OWNER_INACTIVE'; END IF;
        SELECT version INTO current_version FROM public.business_context_heads
          WHERE tenant_id=t AND business_id=p_business FOR SHARE;
        SELECT state INTO effect_state FROM public.{table} WHERE tenant_id=t
          AND business_id=p_business AND actor_id=a AND id=p_effect;
        IF effect_state='pending' AND current_version IS DISTINCT FROM ({expected}) THEN
          RAISE EXCEPTION 'REFERENCE_CONTEXT_STALE'; END IF;
      END IF;"""


def upgrade():
    op.execute("LOCK TABLE reference_provider_effects,reference_geocode_effects IN ACCESS EXCLUSIVE MODE")
    _wrap(
        "reference_google_intent",
        _GOOGLE_INTENT,
        "p_business uuid,p_search uuid,p_effect uuid,p_event uuid,p_pilot uuid,p_mac text,p_key text,"
        "p_tariff text,p_credential text,p_mask text,p_amount bigint,p_context bigint",
        "p_business,p_search,p_effect,p_event,p_pilot,p_mac,p_key,p_tariff,p_credential,p_mask,p_amount,p_context",
        _intent_check("p_effect"),
        True,
    )
    _wrap(
        "reference_jev_intent",
        _JEV_INTENT,
        "p_business uuid,p_search uuid,p_google uuid,p_google_event uuid,p_google_token uuid,p_jev uuid,"
        "p_jev_event uuid,p_mac text,p_key text,p_tariff text,p_credential text,p_charge text,p_amount bigint,"
        "p_batch text,p_context bigint",
        "p_business,p_search,p_google,p_google_event,p_google_token,p_jev,p_jev_event,p_mac,p_key,p_tariff,"
        "p_credential,p_charge,p_amount,p_batch,p_context",
        _intent_check("p_jev"),
        True,
    )
    common_params = (
        "p_effect uuid,p_event uuid,p_mac text,p_business uuid,p_search uuid,p_pilot uuid,p_amount bigint,"
        "p_key text,p_tariff text,p_credential text,p_mask text"
    )
    common_args = "p_effect,p_event,p_mac,p_business,p_search,p_pilot,p_amount,p_key,p_tariff,p_credential,p_mask"
    search_context = (
        "SELECT context_version FROM public.reference_provider_searches WHERE tenant_id=t "
        "AND business_id=p_business AND actor_id=a AND id=p_search"
    )
    _wrap(
        "reference_google_claim",
        _GOOGLE_CLAIM,
        common_params,
        common_args,
        _claim_check("reference_provider_effects", search_context),
        True,
    )
    _wrap(
        "reference_jev_claim",
        _JEV_CLAIM,
        common_params + ",p_parent uuid,p_parent_token uuid,p_batch_mac text,p_context_version bigint",
        common_args + ",p_parent,p_parent_token,p_batch_mac,p_context_version",
        _claim_check("reference_provider_effects", search_context),
        True,
    )
    _wrap(
        "reference_reco_claim",
        _RECO_CLAIM,
        common_params + ",p_google uuid,p_similarity uuid,p_batch uuid,p_shortlist_mac text,p_context bigint",
        common_args + ",p_google,p_similarity,p_batch,p_shortlist_mac,p_context",
        _claim_check("reference_provider_effects", search_context),
        False,
    )
    _wrap(
        "reference_geocode_claim",
        _GEOCODE_CLAIM,
        "p_business uuid,p_effect uuid,p_event uuid,p_origin uuid,p_pilot uuid,p_mac text,"
        "p_key text,p_tariff text,p_credential text,p_class text,p_amount bigint,p_context bigint",
        "p_business,p_effect,p_event,p_origin,p_pilot,p_mac,p_key,p_tariff,p_credential,p_class,p_amount,p_context",
        _claim_check(
            "reference_geocode_effects",
            "SELECT context_version FROM public.reference_geocode_origins "
            "WHERE tenant_id=t AND business_id=p_business AND actor_id=a AND id=p_origin",
        ),
        False,
    )


def downgrade():
    op.execute("LOCK TABLE reference_provider_effects,reference_geocode_effects IN ACCESS EXCLUSIVE MODE")
    for name, signature, exposed in (
        ("reference_google_intent", _GOOGLE_INTENT, True),
        ("reference_jev_intent", _JEV_INTENT, True),
        ("reference_google_claim", _GOOGLE_CLAIM, True),
        ("reference_jev_claim", _JEV_CLAIM, True),
        ("reference_reco_claim", _RECO_CLAIM, False),
        ("reference_geocode_claim", _GEOCODE_CLAIM, False),
    ):
        op.execute(f"DROP FUNCTION public.{name}({signature})")
        op.execute(f"ALTER FUNCTION public.{name}_context_inner({signature}) RENAME TO {name}")
        op.execute(f"REVOKE ALL ON FUNCTION public.{name}({signature}) FROM PUBLIC,meu_braco_direito_correlator")
        if exposed:
            op.execute(f"GRANT EXECUTE ON FUNCTION public.{name}({signature}) TO meu_braco_direito_correlator")
