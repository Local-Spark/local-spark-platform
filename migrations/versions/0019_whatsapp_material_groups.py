"""Keep stable tenant-scoped message group identities after raw inbox expiry."""

from alembic import op

revision = "0019_whatsapp_groups"
down_revision = "0018_whatsapp_upload_intents"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE whatsapp_material_events ADD COLUMN group_id uuid")
    op.execute("ALTER TABLE whatsapp_material_assets ADD COLUMN group_id uuid")
    op.execute("UPDATE whatsapp_material_events SET group_id=id WHERE group_id IS NULL")
    op.execute("UPDATE whatsapp_material_assets SET group_id=id WHERE group_id IS NULL")
    op.execute("CREATE INDEX whatsapp_asset_group ON whatsapp_material_assets(tenant_id,business_id,group_id)")
    op.execute("GRANT SELECT(group_id) ON whatsapp_material_events TO meu_braco_direito_app")


def downgrade():
    op.execute("REVOKE SELECT(group_id) ON whatsapp_material_events FROM meu_braco_direito_app")
    op.execute("DROP INDEX whatsapp_asset_group")
    op.execute("ALTER TABLE whatsapp_material_assets DROP COLUMN group_id")
    op.execute("ALTER TABLE whatsapp_material_events DROP COLUMN group_id")
