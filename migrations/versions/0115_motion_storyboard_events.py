"""Allow durable storyboard lifecycle events omitted by 0114."""

from alembic import op

revision = "0115_motion_storyboard_events"
down_revision = "0114_motion_storyboards"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO STRICT previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') OR event_type IN (''motion.storyboard_ready'',''motion.storyboard_decided'',
        ''motion.storyboard_approved'',''motion.storyboard_reconciled''))';
    END $$""")


def downgrade():
    # Never delete durable history to make a downgrade succeed. PostgreSQL rejects
    # this restriction if storyboard events exist; the migration is transactional.
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO STRICT previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') AND event_type NOT IN (''motion.storyboard_ready'',''motion.storyboard_decided'',
        ''motion.storyboard_approved'',''motion.storyboard_reconciled''))';
    END $$""")
