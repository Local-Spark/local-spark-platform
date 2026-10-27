"""Private operational USD cost reservations for visual generation."""

from alembic import op

revision = "0041_visual_cost_ledger"
down_revision = "0040_collection_photos"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE visual_cost_reservations (
      id uuid NOT NULL, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash char(64) NOT NULL, provider text NOT NULL CHECK(length(provider) BETWEEN 1 AND 80),
      model text NOT NULL CHECK(length(model) BETWEEN 1 AND 120),
      reserved_usd_micros bigint NOT NULL CHECK(reserved_usd_micros>0),
      actual_usd_micros bigint CHECK(actual_usd_micros>=0),
      state text NOT NULL CHECK(state IN ('submitted','completed','uncertain')),
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      CHECK((state='completed' AND actual_usd_micros IS NOT NULL) OR
            (state IN ('submitted','uncertain') AND actual_usd_micros IS NULL)))""")
    op.execute("CREATE INDEX visual_cost_reservations_month ON visual_cost_reservations(tenant_id,created_at)")
    op.execute("""CREATE TABLE visual_cost_events (
      id uuid PRIMARY KEY, tenant_id uuid NOT NULL, reservation_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id),
      action text NOT NULL CHECK(action IN ('reserved','uncertain','completed','over_reservation')),
      created_at timestamptz NOT NULL DEFAULT now(),
      FOREIGN KEY(tenant_id,reservation_id) REFERENCES visual_cost_reservations(tenant_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    for table in ("visual_cost_reservations", "visual_cost_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY worker_tenant ON {table} TO meu_braco_direito_correlator
          USING(tenant_id={tenant}) WITH CHECK(tenant_id={tenant})""")
    op.execute("""GRANT SELECT,INSERT,UPDATE(state,actual_usd_micros,updated_at)
      ON visual_cost_reservations TO meu_braco_direito_correlator""")
    op.execute("GRANT SELECT,INSERT ON visual_cost_events TO meu_braco_direito_correlator")


def downgrade():
    op.execute("DROP TABLE visual_cost_events")
    op.execute("DROP TABLE visual_cost_reservations")
