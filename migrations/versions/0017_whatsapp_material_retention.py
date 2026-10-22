"""Bounded material retention and durable object deletion."""

from alembic import op

revision = "0017_whatsapp_retention"
down_revision = "0016_whatsapp_material"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE whatsapp_material_assets ADD COLUMN expires_at timestamptz")
    op.execute("UPDATE whatsapp_material_assets SET expires_at=created_at+interval '30 days'")
    op.execute("ALTER TABLE whatsapp_material_assets ALTER COLUMN expires_at SET NOT NULL")
    op.execute("ALTER TABLE whatsapp_material_assets ALTER COLUMN expires_at SET DEFAULT now()+interval '30 days'")
    op.execute("ALTER TABLE whatsapp_material_assets ADD COLUMN delete_requested_at timestamptz")
    op.execute("ALTER TABLE whatsapp_material_assets ADD COLUMN delete_lease_until timestamptz")
    op.execute("ALTER TABLE whatsapp_material_assets ADD COLUMN delete_owner uuid")
    op.execute("ALTER TABLE whatsapp_material_assets ADD COLUMN delete_fencing_token bigint NOT NULL DEFAULT 0")
    op.execute("CREATE INDEX whatsapp_assets_purge_due ON whatsapp_material_assets(expires_at,id)")
    op.execute(
        "CREATE INDEX whatsapp_assets_delete_requested ON whatsapp_material_assets(delete_requested_at,id) "
        "WHERE delete_requested_at IS NOT NULL"
    )
    op.execute("""CREATE POLICY owner_asset_delete ON whatsapp_material_assets FOR UPDATE
      TO meu_braco_direito_app
      USING(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid
        AND EXISTS(SELECT 1 FROM memberships m
          WHERE m.tenant_id=whatsapp_material_assets.tenant_id
            AND m.actor_id=nullif(current_setting('app.actor_id',true),'')::uuid
            AND m.role='owner' AND m.active))
      WITH CHECK(tenant_id=nullif(current_setting('app.tenant_id',true),'')::uuid)""")
    op.execute("GRANT UPDATE(delete_requested_at) ON whatsapp_material_assets TO meu_braco_direito_app")
    op.execute(
        "GRANT UPDATE(delete_lease_until,delete_owner,delete_fencing_token) "
        "ON whatsapp_material_assets TO meu_braco_direito_correlator"
    )
    op.execute(
        "GRANT DELETE ON whatsapp_material_assets,whatsapp_material_events,whatsapp_inbox "
        "TO meu_braco_direito_correlator"
    )
    op.execute("DROP POLICY correlator_inbox ON whatsapp_inbox")
    op.execute("""CREATE POLICY correlator_inbox_read ON whatsapp_inbox FOR SELECT
      TO meu_braco_direito_correlator USING(true)""")
    op.execute("""CREATE POLICY correlator_inbox_update ON whatsapp_inbox FOR UPDATE
      TO meu_braco_direito_correlator USING(true) WITH CHECK(true)""")
    op.execute("""CREATE POLICY correlator_inbox_expiry ON whatsapp_inbox FOR DELETE
      TO meu_braco_direito_correlator USING(expires_at<now() OR EXISTS (
        SELECT 1 FROM whatsapp_material_assets a WHERE a.id=whatsapp_inbox.id
          AND (a.delete_requested_at IS NOT NULL OR a.expires_at<=now())))""")


def downgrade():
    op.execute("DROP POLICY correlator_inbox_expiry ON whatsapp_inbox")
    op.execute("DROP POLICY correlator_inbox_update ON whatsapp_inbox")
    op.execute("DROP POLICY correlator_inbox_read ON whatsapp_inbox")
    op.execute("""CREATE POLICY correlator_inbox ON whatsapp_inbox TO meu_braco_direito_correlator
      USING(true) WITH CHECK(true)""")
    op.execute(
        "REVOKE DELETE ON whatsapp_material_assets,whatsapp_material_events,whatsapp_inbox "
        "FROM meu_braco_direito_correlator"
    )
    op.execute(
        "REVOKE UPDATE(delete_lease_until,delete_owner,delete_fencing_token) "
        "ON whatsapp_material_assets FROM meu_braco_direito_correlator"
    )
    op.execute("REVOKE UPDATE(delete_requested_at) ON whatsapp_material_assets FROM meu_braco_direito_app")
    op.execute("DROP POLICY owner_asset_delete ON whatsapp_material_assets")
    op.execute("DROP INDEX whatsapp_assets_purge_due")
    op.execute("DROP INDEX whatsapp_assets_delete_requested")
    for column in ("delete_fencing_token", "delete_owner", "delete_lease_until", "delete_requested_at", "expires_at"):
        op.execute(f"ALTER TABLE whatsapp_material_assets DROP COLUMN {column}")
