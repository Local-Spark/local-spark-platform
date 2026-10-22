"""Rename existing roles and product-owned identity labels without changing IDs or grants."""

from alembic import op
from sqlalchemy import text

revision = "0015_product_brand"
down_revision = "0014_whatsapp_channel_link"
branch_labels = None
depends_on = None

# Legacy names are necessary to upgrade databases created before the product rename.
ROLES = (
    "app",
    "relay",
    "auth",
    "billing",
    "meta",
    "correlator",
    "runtime",
    "delivery",
    "identity",
    "payments",
    "ingest",
    "router",
)


def upgrade():
    for suffix in ROLES:
        old, new = f"local_spark_{suffix}", f"meu_braco_direito_{suffix}"
        op.execute(f"""DO $$ BEGIN
          IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='{old}') THEN
            IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='{new}') THEN
              RAISE EXCEPTION 'Both legacy and product roles exist; resolve before migration';
            END IF;
            ALTER ROLE {old} RENAME TO {new};
          END IF;
        END $$""")
    op.execute("ALTER TABLE billing_checkouts ADD COLUMN IF NOT EXISTS provider_key_prefix text")
    op.execute(
        "UPDATE billing_checkouts SET provider_key_prefix='local-spark-checkout' WHERE provider_key_prefix IS NULL"
    )
    op.execute(
        "ALTER TABLE billing_checkouts ALTER COLUMN provider_key_prefix SET DEFAULT 'meu-braco-direito-checkout'"
    )
    op.execute("ALTER TABLE billing_checkouts ALTER COLUMN provider_key_prefix SET NOT NULL")
    op.execute("UPDATE user_accounts SET issuer='meu-braco-direito' WHERE issuer='local-spark'")
    for table in ("user_accounts", "auth_credentials"):
        op.execute(f"""UPDATE {table} SET email=replace(email,'@local-spark.local','@meu-braco-direito.local')
          WHERE email IN ('operator@local-spark.local','cliente@local-spark.local')""")
    op.execute("""UPDATE user_accounts SET display_name=replace(display_name,'Local Spark','Meu Braço Direito')
      WHERE display_name IN ('Equipe Local Spark','Cliente Local Spark')""")


def downgrade():
    # The brand is operational metadata, not a schema feature. Keep current role names
    # so older schema revisions in this checkout still address the same restricted roles.
    # Retain frozen provider keys too: a rollback must never duplicate an external checkout.
    op.execute(text("SELECT 1"))
