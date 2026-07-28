exports.up = (pgm) => {
  // Store only anonymous product-usage events.
  pgm.sql(`
    CREATE TABLE IF NOT EXISTS analytics_events (
      id BIGSERIAL PRIMARY KEY,
      event_type TEXT NOT NULL,
      page TEXT NOT NULL,
      session_id TEXT NOT NULL,
      app_version TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  `);

  // Keep database values aligned with the application contract.
  pgm.sql(`
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'analytics_events_event_type_check'
      ) THEN
        ALTER TABLE analytics_events
        ADD CONSTRAINT analytics_events_event_type_check
        CHECK (event_type IN ('page_view', 'refresh'));
      END IF;

      IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'analytics_events_page_check'
      ) THEN
        ALTER TABLE analytics_events
        ADD CONSTRAINT analytics_events_page_check
        CHECK (page IN ('now', 'today', 'learn', 'project'));
      END IF;

      IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'analytics_events_session_id_length_check'
      ) THEN
        ALTER TABLE analytics_events
        ADD CONSTRAINT analytics_events_session_id_length_check
        CHECK (
          char_length(session_id) BETWEEN 16 AND 128
        );
      END IF;

      IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'analytics_events_app_version_length_check'
      ) THEN
        ALTER TABLE analytics_events
        ADD CONSTRAINT analytics_events_app_version_length_check
        CHECK (
          app_version IS NULL
          OR char_length(app_version) <= 80
        );
      END IF;
    END
    $$;
  `);

  pgm.sql(`
    CREATE INDEX IF NOT EXISTS
      analytics_events_created_at_index
    ON analytics_events (created_at DESC);
  `);

  pgm.sql(`
    CREATE INDEX IF NOT EXISTS
      analytics_events_session_id_index
    ON analytics_events (session_id);
  `);

  pgm.sql(`
    CREATE INDEX IF NOT EXISTS
      analytics_events_page_event_type_index
    ON analytics_events (page, event_type);
  `);
};

exports.down = (pgm) => {
  pgm.dropTable("analytics_events", {
    ifExists: true,
    cascade: true,
  });
};
