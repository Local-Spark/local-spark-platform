"""Private production admission and review boundaries; no customer quota writes."""

from alembic import op

revision = "0125_creation_lab_pipeline"
down_revision = "0124_creation_lab_results"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE creation_lab_runs ADD COLUMN snapshot_trace_id uuid REFERENCES creation_lab_trace(id),
      ADD COLUMN execution_event_id uuid, ADD COLUMN start_hash char(64), ADD COLUMN source_fingerprint char(64)""")
    op.execute(
        "GRANT UPDATE(snapshot_trace_id,start_hash,source_fingerprint,execution_event_id) ON creation_lab_runs TO meu_braco_direito_app"
    )
    op.execute("""CREATE TABLE creation_lab_checkpoints (
      run_id uuid NOT NULL REFERENCES creation_lab_runs(id),stage text NOT NULL
        CHECK(stage IN ('plan','render','storyboard','editorial','catalog')),
      trace_id uuid NOT NULL REFERENCES creation_lab_trace(id),content_sha256 char(64) NOT NULL,
      decision text CHECK(decision IN ('approve','reject')),decision_hash char(64),
      decision_trace_id uuid REFERENCES creation_lab_trace(id),consumed boolean NOT NULL DEFAULT false,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),PRIMARY KEY(run_id,stage))""")
    op.execute("ALTER TABLE creation_lab_checkpoints ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE creation_lab_checkpoints FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY lab_private ON creation_lab_checkpoints TO meu_braco_direito_app
      USING(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))
      WITH CHECK(EXISTS(SELECT 1 FROM creation_lab_runs r WHERE r.id=run_id))""")
    op.execute(
        "GRANT SELECT,INSERT,UPDATE(decision,decision_hash,decision_trace_id,consumed) ON creation_lab_checkpoints TO meu_braco_direito_app"
    )
    op.execute("""CREATE POLICY lab_context_read ON business_brand_kit_logos FOR SELECT TO meu_braco_direito_app
      USING(public.creation_lab_read_scope(tenant_id,business_id))""")
    for table in (
        "business_catalog_heads",
        "business_catalog_versions",
        "business_offerings",
        "business_offering_promotions",
        "intent_jev_consents",
    ):
        op.execute(
            f"CREATE POLICY lab_context_read ON {table} FOR SELECT TO meu_braco_direito_app USING(public.creation_lab_read_scope(tenant_id,business_id))"
        )
    op.execute(REFERENCE_READER)
    op.execute("REVOKE ALL ON FUNCTION creation_lab_reference_context(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION creation_lab_reference_context(uuid) TO meu_braco_direito_app")
    op.execute("""DO $$ DECLARE previous text; BEGIN
      SELECT pg_get_expr(conbin,conrelid) INTO previous FROM pg_constraint
        WHERE conrelid='outbox_events'::regclass AND conname='outbox_events_event_type_check';
      ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_event_type_check;
      EXECUTE 'ALTER TABLE outbox_events ADD CONSTRAINT outbox_events_event_type_check CHECK ((' ||
        previous || ') OR event_type IN (''creation_lab.requested'',''creation_lab.plan_approved'',
        ''creation_lab.render_approved'',''creation_lab.storyboard_approved'',''creation_lab.editorial_approved'',''creation_lab.catalog_approved''))';
    END $$""")


def downgrade():
    op.execute("DROP FUNCTION creation_lab_reference_context(uuid)")
    op.execute("DROP POLICY lab_context_read ON business_brand_kit_logos")
    for table in (
        "business_catalog_heads",
        "business_catalog_versions",
        "business_offerings",
        "business_offering_promotions",
        "intent_jev_consents",
    ):
        op.execute(f"DROP POLICY lab_context_read ON {table}")
    op.execute("DROP TABLE creation_lab_checkpoints")
    op.execute(
        "ALTER TABLE creation_lab_runs DROP COLUMN execution_event_id,DROP COLUMN snapshot_trace_id,DROP COLUMN start_hash,DROP COLUMN source_fingerprint"
    )


REFERENCE_READER = "CREATE FUNCTION public.creation_lab_reference_context(p_business uuid) RETURNS jsonb\n  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$\n  DECLARE t uuid:=nullif(current_setting('app.tenant_id',true),'')::uuid;\n    item record;learn public.reference_learning_results%ROWTYPE;last_window public.reference_feed_windows%ROWTYPE;\n    selected jsonb:='[]'::jsonb;learnings jsonb:='[]'::jsonb;state text;\n  BEGIN\n    IF NOT public.creation_lab_read_scope(t,p_business) THEN\n      RAISE EXCEPTION 'CREATION_LAB_ACCESS_DENIED'; END IF;\n    IF EXISTS(SELECT 1 FROM public.reference_current_learning_selection(p_business) c\n      LEFT JOIN public.reference_learning_heads h ON h.tenant_id=t AND h.business_id=p_business\n        AND h.reference_id=c.reference_id AND h.selected\n      LEFT JOIN public.reference_learning_associations a ON a.tenant_id=t AND a.business_id=p_business\n        AND a.reference_id=c.reference_id AND a.version=h.version\n      WHERE h.reference_id IS NULL OR a.reference_id IS NULL OR a.instagram_handle IS DISTINCT FROM c.profile)\n      THEN RAISE EXCEPTION 'CREATION_LAB_REFERENCES_NOT_SYNCHRONIZED'; END IF;\n    FOR item IN SELECT c.*,h.version FROM public.reference_current_learning_selection(p_business) c\n      JOIN public.reference_learning_heads h ON h.tenant_id=t AND h.business_id=p_business\n        AND h.reference_id=c.reference_id AND h.selected ORDER BY c.reference_id LOOP\n      SELECT * INTO learn FROM public.reference_learning_results WHERE tenant_id=t AND business_id=p_business\n        AND reference_id=item.reference_id AND association_version=item.version AND status IN ('completed','partial')\n        ORDER BY created_at DESC,window_id DESC LIMIT 1;\n      SELECT * INTO last_window FROM public.reference_feed_windows WHERE tenant_id=t AND business_id=p_business\n        AND reference_id=item.reference_id AND association_version=item.version\n        AND scheduled_at<=clock_timestamp() ORDER BY scheduled_at DESC LIMIT 1;\n      state:=CASE WHEN learn.window_id IS NOT NULL THEN learn.status\n        WHEN item.profile IS NULL OR last_window.status IN ('blocked','unavailable') THEN 'unavailable'\n        WHEN EXISTS(SELECT 1 FROM reference_feed_effects e WHERE e.tenant_id=t AND e.business_id=p_business\n          AND e.window_id=last_window.id AND e.state='uncertain' AND NOT EXISTS(\n            SELECT 1 FROM reference_feed_resources r WHERE(r.tenant_id,r.business_id,r.effect_id)=\n              (e.tenant_id,e.business_id,e.id))) THEN 'unavailable' \n        WHEN EXISTS(SELECT 1 FROM public.reference_feed_effects e WHERE e.tenant_id=t AND e.business_id=p_business\n          AND e.window_id=last_window.id) THEN 'pending' ELSE 'not_requested' END;\n      selected:=selected||jsonb_build_array(jsonb_build_object('reference_id',item.reference_id,\n        'association_version',item.version,'source',item.source,'instagram_handle',item.profile,'note',item.note,\n        'score',item.score,'similarity',item.similarity,'analysis_status',state));\n      IF learn.window_id IS NOT NULL THEN\n        learnings:=learnings||jsonb_build_array(jsonb_build_object('reference_id',item.reference_id,\n          'association_version',item.version,'analysis_id',learn.window_id,'source','instagram_feed',\n          'status',learn.status,'patterns',learn.patterns)); END IF;\n    END LOOP;\n    RETURN jsonb_build_object('version',1,'selected',selected,'learnings',learnings);\n  END $$"
