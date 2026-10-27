"""Private owner-confirmed catalog projections and immutable operation snapshots."""

from alembic import op

revision = "0039_business_catalog"
down_revision = "0038_retire_billing_outbox"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE business_catalog_heads (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,
      version integer NOT NULL DEFAULT 0 CHECK(version>=0),
      PRIMARY KEY(tenant_id,business_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE business_catalog_versions (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,version integer NOT NULL CHECK(version>0),
      operation_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash char(64) NOT NULL,document jsonb NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,version),UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES business_catalog_heads(tenant_id,business_id))""")
    op.execute("""CREATE TABLE business_offerings (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('product','service')),
      state text NOT NULL CHECK(state IN ('draft','active','archived')),
      name varchar(120) NOT NULL CHECK(length(trim(name))>0),description text,category varchar(120),
      aliases jsonb NOT NULL DEFAULT '[]' CHECK(jsonb_typeof(aliases)='array'),
      position integer NOT NULL DEFAULT 0 CHECK(position>=0),
      price_minor bigint CHECK(price_minor>=0),currency text NOT NULL DEFAULT 'BRL' CHECK(currency='BRL'),
      price_valid_until date,duration_minutes integer CHECK(duration_minutes>0),booking_instructions text,
      version integer NOT NULL,PRIMARY KEY(tenant_id,business_id,id),
      CHECK((price_minor IS NULL)=(price_valid_until IS NULL)),
      CHECK(kind='service' OR (duration_minutes IS NULL AND booking_instructions IS NULL)),
      FOREIGN KEY(tenant_id,business_id,version)
        REFERENCES business_catalog_versions(tenant_id,business_id,version))""")
    op.execute("""CREATE TABLE business_offering_promotions (
      tenant_id uuid NOT NULL,business_id uuid NOT NULL,id uuid NOT NULL,offering_id uuid NOT NULL,
      title varchar(120) NOT NULL CHECK(length(trim(title))>0),description text,
      state text NOT NULL CHECK(state IN ('draft','active','archived')),
      price_minor bigint CHECK(price_minor>=0),starts_at timestamptz NOT NULL,ends_at timestamptz NOT NULL,
      version integer NOT NULL,PRIMARY KEY(tenant_id,business_id,id),CHECK(ends_at>starts_at),
      FOREIGN KEY(tenant_id,business_id,offering_id) REFERENCES business_offerings(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,version)
        REFERENCES business_catalog_versions(tenant_id,business_id,version))""")
    op.execute("CREATE INDEX business_offerings_state ON business_offerings(tenant_id,business_id,state,position,id)")
    op.execute("""CREATE INDEX business_promotions_validity
      ON business_offering_promotions(tenant_id,business_id,state,starts_at,ends_at)""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in (
        "business_catalog_heads",
        "business_catalog_versions",
        "business_offerings",
        "business_offering_promotions",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_business_catalog ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("GRANT SELECT,INSERT,UPDATE(version) ON business_catalog_heads TO meu_braco_direito_app")
    op.execute("GRANT SELECT,INSERT ON business_catalog_versions TO meu_braco_direito_app")
    op.execute("""GRANT SELECT,INSERT,
      UPDATE(kind,state,name,description,category,aliases,position,price_minor,currency,price_valid_until,
        duration_minutes,booking_instructions,version)
      ON business_offerings TO meu_braco_direito_app""")
    op.execute("""GRANT SELECT,INSERT,
      UPDATE(offering_id,title,description,state,price_minor,starts_at,ends_at,version)
      ON business_offering_promotions TO meu_braco_direito_app""")


def downgrade():
    op.execute("DROP TABLE business_offering_promotions")
    op.execute("DROP TABLE business_offerings")
    op.execute("DROP TABLE business_catalog_versions")
    op.execute("DROP TABLE business_catalog_heads")
