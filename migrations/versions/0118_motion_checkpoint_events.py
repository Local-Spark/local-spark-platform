"""Enable explicit pre-implementation/pre-render decisions in the existing outbox."""

from alembic import op

revision = "0118_motion_checkpoint_events"
down_revision = "0117_motion_recapture_events"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO STRICT previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') OR event_type IN (''motion.plan_ready'',''motion.plan_approved'',
        ''motion.render_ready'',''motion.render_approved''))';
    END $$""")


def downgrade():
    # Never delete audit/outbox history to force a downgrade.
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO STRICT previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') AND event_type NOT IN (''motion.plan_ready'',''motion.plan_approved'',
        ''motion.render_ready'',''motion.render_approved''))';
    END $$""")
