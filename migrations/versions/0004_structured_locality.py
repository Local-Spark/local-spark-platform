"""Optional structured localities, preserving existing profiles and replay hashes."""

from alembic import op

revision = "0004_structured_locality"
down_revision = "0003_native_auth"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE business_profiles ADD COLUMN state_code varchar(2), ADD COLUMN city_ibge_code varchar(7)")
    op.execute("""ALTER TABLE business_profiles ADD CONSTRAINT profile_locality_pair CHECK (
      (state_code IS NULL AND city_ibge_code IS NULL) OR
      (state_code IS NOT NULL AND city_ibge_code IS NOT NULL
       AND state_code ~ '^[A-Z]{2}$' AND city_ibge_code ~ '^[0-9]{7}$'))""")


def downgrade():
    op.execute("ALTER TABLE business_profiles DROP CONSTRAINT profile_locality_pair")
    op.execute("ALTER TABLE business_profiles DROP COLUMN city_ibge_code, DROP COLUMN state_code")
