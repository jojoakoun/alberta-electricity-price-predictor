const { pool } = require("../db/pool");

/**
 * Store one anonymous product-usage event.
 *
 * The table intentionally excludes IP addresses, user agents,
 * location data, names, emails, and browser fingerprints.
 */
async function createAnalyticsEvent({
  eventType,
  page,
  sessionId,
  appVersion,
}) {
  const { rows } = await pool.query(
    `
      INSERT INTO analytics_events (
        event_type,
        page,
        session_id,
        app_version
      )
      VALUES ($1, $2, $3, $4)
      RETURNING id, created_at;
    `,
    [
      eventType,
      page,
      sessionId,
      appVersion,
    ],
  );

  return rows[0];
}

/**
 * Return a compact private usage summary.
 *
 * A session is an anonymous browser identifier. It represents
 * an approximate visitor, not a verified individual person.
 */
async function getAnalyticsSummary() {
  const [
    overviewResult,
    pageResult,
    eventResult,
    hourlyResult,
    returningResult,
    latestRunResult,
  ] = await Promise.all([
    pool.query(`
      SELECT
        COUNT(*) FILTER (
          WHERE event_type = 'page_view'
        )::integer AS total_visits,

        COUNT(
          DISTINCT session_id
        )::integer AS unique_sessions,

        COUNT(*) FILTER (
          WHERE event_type = 'page_view'
            AND created_at >= CURRENT_DATE
        )::integer AS today_visits,

        MAX(created_at) AS last_visit_utc
      FROM analytics_events;
    `),

    pool.query(`
      SELECT
        page,
        COUNT(*)::integer AS visit_count
      FROM analytics_events
      WHERE event_type = 'page_view'
      GROUP BY page
      ORDER BY page;
    `),

    pool.query(`
      SELECT
        event_type,
        COUNT(*)::integer AS event_count
      FROM analytics_events
      GROUP BY event_type
      ORDER BY event_type;
    `),

    pool.query(`
      SELECT
        EXTRACT(HOUR FROM created_at AT TIME ZONE 'UTC')::integer
          AS hour_utc,
        COUNT(*)::integer AS visit_count
      FROM analytics_events
      WHERE event_type = 'page_view'
      GROUP BY hour_utc
      ORDER BY hour_utc;
    `),

    pool.query(`
      SELECT COUNT(*)::integer AS returning_sessions_today
      FROM (
        SELECT session_id
        FROM analytics_events
        WHERE event_type = 'page_view'
          AND created_at >= CURRENT_DATE
        GROUP BY session_id
        HAVING COUNT(*) > 1
      ) AS returning_sessions;
    `),

    pool.query(`
      SELECT generated_at
      FROM prediction_runs
      WHERE status = 'success'
      ORDER BY generated_at DESC, id DESC
      LIMIT 1;
    `),
  ]);

  return {
    overview: overviewResult.rows[0],
    pages: pageResult.rows,
    events: eventResult.rows,
    hourlyDistribution: hourlyResult.rows,
    returningSessionsToday:
      returningResult.rows[0]?.returning_sessions_today ?? 0,
    latestPredictionRunUtc:
      latestRunResult.rows[0]?.generated_at ?? null,
  };
}

module.exports = {
  createAnalyticsEvent,
  getAnalyticsSummary,
};
