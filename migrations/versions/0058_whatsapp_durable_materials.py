"""Preserve associated WhatsApp materials without automatic expiry."""

from alembic import op

revision = "0058_whatsapp_durable_materials"
down_revision = "0057_one_business_per_tenant"
branch_labels = None
depends_on = None


def upgrade():
    # Existing requests or leases may indicate an object deletion already in progress.
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM whatsapp_material_assets
                WHERE delete_requested_at IS NOT NULL OR delete_owner IS NOT NULL
                   OR delete_lease_until IS NOT NULL) THEN
        RAISE EXCEPTION 'WHATSAPP_MATERIAL_PENDING_DELETE_REQUIRES_REVIEW';
      END IF;
    END $$""")
    op.execute("ALTER TABLE whatsapp_material_assets ALTER COLUMN expires_at DROP NOT NULL")
    op.execute("ALTER TABLE whatsapp_material_assets ALTER COLUMN expires_at DROP DEFAULT")
    op.execute("ALTER TABLE whatsapp_material_events ALTER COLUMN expires_at DROP NOT NULL")
    op.execute("UPDATE whatsapp_material_assets SET expires_at=NULL WHERE delete_requested_at IS NULL")
    op.execute("UPDATE whatsapp_material_events SET expires_at=NULL")


def downgrade():
    # Never assign an arbitrary lifetime to data protected by this migration.
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM whatsapp_material_assets WHERE expires_at IS NULL)
         OR EXISTS(SELECT 1 FROM whatsapp_material_events WHERE expires_at IS NULL) THEN
        RAISE EXCEPTION 'DURABLE_MATERIALS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("ALTER TABLE whatsapp_material_assets ALTER COLUMN expires_at SET NOT NULL")
    op.execute("ALTER TABLE whatsapp_material_assets ALTER COLUMN expires_at SET DEFAULT now()+interval '30 days'")
    op.execute("ALTER TABLE whatsapp_material_events ALTER COLUMN expires_at SET NOT NULL")
