"""Allow the explicit, one-time storyboard recapture lifecycle."""

from alembic import op

revision = "0117_motion_recapture_events"
down_revision = "0116_motion_failure_identity"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO STRICT previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') OR event_type IN (''motion.storyboard_recapture_requested'',
        ''motion.storyboard_recapture_started''))';
    END $$""")


def downgrade():
    # Never delete durable history to make a downgrade succeed. PostgreSQL rejects
    # this restriction if storyboard events exist; the migration is transactional.
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO STRICT previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') AND event_type NOT IN (''motion.storyboard_recapture_requested'',
        ''motion.storyboard_recapture_started''))';
    END $$""")
