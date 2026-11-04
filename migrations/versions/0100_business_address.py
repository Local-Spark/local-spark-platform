"""Owner-declared shop address with durable, immutable versions."""

from alembic import op

revision = "0100_business_address"
down_revision = "0099_similarity_snapshot"
branch_labels = None
depends_on = None

_EVENTS = (
    "business.created",
    "brand_kit.changed",
    "reference.created",
    "reference.removed",
    "reference.search_requested",
    "reference.selection_confirmed",
    "reference.effect_requested",
    "reference.effect_completed",
    "reference.cost_changed",
    "reference.provider_effect_requested",
    "reference.provider_cost_changed",
    "reference.provider_effect_completed",
    "reference.provider_search_requested",
    "reference.provider_search_cancelled",
    "reference.real_selection_confirmed",
    "reference.private_shortlist_prepared",
    "reference.feed_resources_recorded",
    "reference.contacts_not_dispatched",
    "reference.contacts_retry_authorized",
    "reference.similarity_snapshot_recorded",
)


def _event_constraint(events):
    values = ",".join("'" + value + "'" for value in events)
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute(
        "ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK(event_type IN (" + values + "))"
    )


def upgrade():
    op.execute("""CREATE TABLE business_address_versions (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,version bigint NOT NULL CHECK(version>0),
      address jsonb NOT NULL CHECK(jsonb_typeof(address)='object'
        AND address ?& ARRAY['street','number','city','state_code']
        AND address - ARRAY['street','number','city','state_code','neighborhood','complement','postal_code']='{}'::jsonb
        AND jsonb_typeof(address->'street')='string' AND length(address->>'street') BETWEEN 1 AND 120
        AND jsonb_typeof(address->'number')='string' AND length(address->>'number') BETWEEN 1 AND 30
        AND jsonb_typeof(address->'city')='string' AND length(address->>'city') BETWEEN 1 AND 120
        AND jsonb_typeof(address->'state_code')='string' AND length(address->>'state_code')=2),
      actor_id uuid NOT NULL REFERENCES user_accounts(id),operation_id uuid NOT NULL,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,version),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE business_address_heads (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,version bigint NOT NULL,
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id,version)
        REFERENCES business_address_versions(tenant_id,business_id,version))""")
    op.execute("""CREATE TABLE business_address_operations (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,operation_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash text NOT NULL CHECK(request_hash ~ '^[0-9a-f]{64}$'),
      version bigint NOT NULL,event_id uuid NOT NULL,
      PRIMARY KEY(tenant_id,business_id,operation_id),
      UNIQUE(tenant_id,business_id,operation_id,actor_id,version),
      UNIQUE(tenant_id,event_id),
      FOREIGN KEY(tenant_id,business_id,version) REFERENCES business_address_versions(tenant_id,business_id,version),
      FOREIGN KEY(tenant_id,event_id) REFERENCES outbox_events(tenant_id,id))""")
    op.execute("""ALTER TABLE business_address_versions ADD CONSTRAINT business_address_source_operation
      FOREIGN KEY(tenant_id,business_id,operation_id,actor_id,version)
      REFERENCES business_address_operations(tenant_id,business_id,operation_id,actor_id,version)
      DEFERRABLE INITIALLY DEFERRED""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"tenant_id={tenant} AND EXISTS(SELECT 1 FROM memberships m JOIN user_accounts u ON u.id=m.actor_id "
        f"WHERE m.tenant_id={tenant} AND m.actor_id={actor} AND m.role='owner' AND m.active AND u.active)"
    )
    for table in ("business_address_versions", "business_address_heads", "business_address_operations"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY shop_owner ON {table} TO meu_braco_direito_app USING({owner}) WITH CHECK({owner})")
        op.execute(f"GRANT SELECT,INSERT ON {table} TO meu_braco_direito_app")
    op.execute("GRANT UPDATE(version) ON business_address_heads TO meu_braco_direito_app")
    op.execute("GRANT EXECUTE ON FUNCTION public.lock_reference_cost_owner() TO meu_braco_direito_app")
    _event_constraint((*_EVENTS, "business.address_saved"))


def downgrade():
    op.execute(
        "LOCK TABLE business_address_heads,business_address_versions,business_address_operations "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM business_address_versions) OR
      EXISTS(SELECT 1 FROM business_address_operations) OR
      EXISTS(SELECT 1 FROM outbox_events WHERE event_type='business.address_saved') THEN
      RAISE EXCEPTION 'BUSINESS_ADDRESS_PREVENTS_AUTOMATIC_DOWNGRADE'; END IF; END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute("ALTER TABLE business_address_versions DROP CONSTRAINT business_address_source_operation")
    op.execute("DROP TABLE business_address_heads,business_address_operations,business_address_versions")
    op.execute("REVOKE EXECUTE ON FUNCTION public.lock_reference_cost_owner() FROM meu_braco_direito_app")
    _event_constraint(_EVENTS)
