"""Permit durable reference events awaiting a future consumer."""

from alembic import op

revision = "0064_reference_outbox"
down_revision = "0063_reference_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type IN ('business.created','brand_kit.changed','reference.created','reference.removed'))""")


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM outbox_events WHERE event_type IN ('reference.created','reference.removed')) THEN
        RAISE EXCEPTION 'REFERENCE_EVENTS_PREVENT_AUTOMATIC_DOWNGRADE';
      END IF;
    END $$""")
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check")
    op.execute("""ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check
      CHECK(event_type IN ('business.created','brand_kit.changed'))""")
