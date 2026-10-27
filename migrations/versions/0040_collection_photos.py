"""Private collection photos, durable object intents and immutable metadata versions."""

from alembic import op

revision = "0040_collection_photos"
down_revision = "0039_business_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE business_collection_photos (
      id uuid NOT NULL, tenant_id uuid NOT NULL, business_id uuid NOT NULL,
      operation_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES user_accounts(id),
      request_hash char(64) NOT NULL, object_key text NOT NULL UNIQUE,
      sha256 char(64), source_sha256 char(64), mime_type text, size_bytes integer,
      title text NOT NULL CHECK(length(title) BETWEEN 1 AND 160),
      item_id uuid, space_kind text CHECK(space_kind IN ('facade','counter','room','environment')),
      sort_order integer NOT NULL CHECK(sort_order BETWEEN 0 AND 9999),
      status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived')),
      version integer NOT NULL DEFAULT 0 CHECK(version>=0),
      state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','ready','deleting','deleted')),
      source text NOT NULL CHECK(source IN ('upload','whatsapp')),
      source_material_id uuid,
      rights_scope text NOT NULL CHECK(rights_scope='business_collection_confirmed'),
      upload_owner uuid, upload_lease_until timestamptz,
      delete_owner uuid, delete_lease_until timestamptz,
      delete_fencing_token bigint NOT NULL DEFAULT 0,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,id),
      UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id) REFERENCES businesses(tenant_id,id),
      FOREIGN KEY(tenant_id,business_id,item_id) REFERENCES business_offerings(tenant_id,business_id,id),
      CHECK((item_id IS NOT NULL)::integer+(space_kind IS NOT NULL)::integer=1),
      CHECK((source='upload' AND source_material_id IS NULL) OR
            (source='whatsapp' AND source_material_id IS NOT NULL)),
      CHECK(state<>'ready' OR (version>0 AND sha256 IS NOT NULL AND mime_type='image/png'
            AND size_bytes>0 AND size_bytes<=8388608)))""")
    op.execute("""CREATE INDEX collection_photos_gallery
      ON business_collection_photos(tenant_id,business_id,sort_order,id) WHERE state='ready'""")
    op.execute("""CREATE TABLE business_collection_photo_versions (
      tenant_id uuid NOT NULL, business_id uuid NOT NULL, photo_id uuid NOT NULL,
      version integer NOT NULL CHECK(version>0), operation_id uuid NOT NULL,
      actor_id uuid NOT NULL REFERENCES user_accounts(id), request_hash char(64) NOT NULL,
      action text NOT NULL CHECK(action IN ('uploaded','promoted','updated','deleted')),
      document jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(tenant_id,business_id,photo_id,version),
      UNIQUE(tenant_id,operation_id),
      FOREIGN KEY(tenant_id,business_id,photo_id)
        REFERENCES business_collection_photos(tenant_id,business_id,id))""")
    tenant = "nullif(current_setting('app.tenant_id',true),'')::uuid"
    actor = "nullif(current_setting('app.actor_id',true),'')::uuid"
    owner = (
        f"EXISTS(SELECT 1 FROM memberships m WHERE m.tenant_id={tenant} "
        f"AND m.actor_id={actor} AND m.role='owner' AND m.active)"
    )
    for table in ("business_collection_photos", "business_collection_photo_versions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""CREATE POLICY owner_collection_photo ON {table} TO meu_braco_direito_app
          USING(tenant_id={tenant} AND {owner}) WITH CHECK(tenant_id={tenant} AND {owner})""")
    op.execute("""GRANT SELECT,INSERT,
      UPDATE(title,item_id,space_kind,sort_order,status,version,state,sha256,mime_type,size_bytes,
             source_sha256,updated_at,upload_owner,upload_lease_until,delete_owner,delete_lease_until,delete_fencing_token)
      ON business_collection_photos TO meu_braco_direito_app""")
    op.execute("GRANT SELECT,INSERT ON business_collection_photo_versions TO meu_braco_direito_app")


def downgrade():
    op.execute("DROP TABLE business_collection_photo_versions")
    op.execute("DROP TABLE business_collection_photos")
