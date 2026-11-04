"""Read-only, tenant-bound storage for future sanitized reference results.

The application cannot insert or update these tables in this slice. A later
writer must validate its durable search and all contributing provider effects
before committing a result, auditing it and emitting an outbox event.
"""

from alembic import op

revision = "0075_reference_results_storage"
down_revision = "0074_reference_places_effect"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE reference_provider_places (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, id uuid NOT NULL,
      place_id text NOT NULL CHECK(length(place_id) BETWEEN 1 AND 2048 AND place_id=btrim(place_id)),
      PRIMARY KEY(tenant_id,business_id,id), UNIQUE(tenant_id,business_id,place_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id))""")
    op.execute("""CREATE TABLE reference_provider_results (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, id uuid NOT NULL, search_id uuid NOT NULL,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(tenant_id,business_id,id), UNIQUE(tenant_id,business_id,search_id),
      FOREIGN KEY(tenant_id,business_id,search_id)
        REFERENCES reference_provider_searches(tenant_id,business_id,id))""")
    op.execute("""CREATE TABLE reference_provider_result_candidates (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, result_id uuid NOT NULL, id uuid NOT NULL,
      place_id uuid NOT NULL, position smallint NOT NULL CHECK(position BETWEEN 1 AND 10),
      reputation_score numeric NOT NULL CHECK(reputation_score BETWEEN 0 AND 10),
      reputation_formula_version text NOT NULL CHECK(reputation_formula_version ~ '^[a-zA-Z0-9_.-]{1,64}$'),
      jev_recommendation_rank smallint CHECK(jev_recommendation_rank BETWEEN 1 AND 3),
      PRIMARY KEY(tenant_id,business_id,result_id,id),
      UNIQUE(tenant_id,business_id,result_id,position),
      UNIQUE(tenant_id,business_id,result_id,place_id),
      UNIQUE(tenant_id,business_id,result_id,jev_recommendation_rank),
      FOREIGN KEY(tenant_id,business_id,result_id) REFERENCES reference_provider_results(tenant_id,business_id,id),
      FOREIGN KEY(tenant_id,business_id,place_id) REFERENCES reference_provider_places(tenant_id,business_id,id))""")
    op.execute("""CREATE TABLE reference_provider_profile_options (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, result_id uuid NOT NULL, candidate_id uuid NOT NULL,
      instagram_handle text NOT NULL CHECK(
        instagram_handle ~ '^[a-z0-9_]([a-z0-9_.]{0,28}[a-z0-9_])?$'
        AND position('..' in instagram_handle)=0),
      source_position integer NOT NULL CHECK(source_position > 0),
      is_primary boolean NOT NULL DEFAULT false,
      source text NOT NULL CHECK(source='apify'),
      association_status text NOT NULL CHECK(association_status='unverified'),
      PRIMARY KEY(tenant_id,business_id,result_id,candidate_id,instagram_handle),
      UNIQUE(tenant_id,business_id,result_id,candidate_id,source_position),
      FOREIGN KEY(tenant_id,business_id,result_id,candidate_id)
        REFERENCES reference_provider_result_candidates(tenant_id,business_id,result_id,id))""")
    op.execute("""CREATE UNIQUE INDEX reference_provider_profile_one_primary
      ON reference_provider_profile_options(tenant_id,business_id,result_id,candidate_id) WHERE is_primary""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in (
        "reference_provider_places",
        "reference_provider_results",
        "reference_provider_result_candidates",
        "reference_provider_profile_options",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY owner_read ON {table} FOR SELECT TO meu_braco_direito_app "
            f"USING(tenant_id={tenant} AND {owner})"
        )
        op.execute(f"GRANT SELECT ON {table} TO meu_braco_direito_app")


def downgrade():
    tables = (
        "reference_provider_profile_options",
        "reference_provider_result_candidates",
        "reference_provider_results",
        "reference_provider_places",
    )
    op.execute(f"LOCK TABLE {','.join(tables)} IN ACCESS EXCLUSIVE MODE")
    op.execute("SET LOCAL row_security = off")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM reference_provider_profile_options) OR
         EXISTS(SELECT 1 FROM reference_provider_result_candidates) OR
         EXISTS(SELECT 1 FROM reference_provider_results) OR
         EXISTS(SELECT 1 FROM reference_provider_places) THEN
        RAISE EXCEPTION 'REFERENCE_PROVIDER_RESULTS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("SET LOCAL row_security = on")
    op.execute(f"DROP TABLE {','.join(tables)}")
