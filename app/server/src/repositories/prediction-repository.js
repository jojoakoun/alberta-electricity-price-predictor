const { pool } = require("../db/pool");

// Selecting one run first prevents the API from mixing horizons generated from
// different source market hours. The service validates the five-horizon set.
async function getLatestPredictions() {
  const { rows } = await pool.query(`
    WITH latest_run AS (
      SELECT
        id,
        generated_at,
        detail
      FROM prediction_runs
      WHERE status = 'success'
        AND generated_at <= DATE_TRUNC('hour', CURRENT_TIMESTAMP)
      ORDER BY generated_at DESC, id DESC
      LIMIT 1
    )
    SELECT
      p.horizon_hours,
      p.target_time_utc,
      p.predicted_price,
      p.recommendation,
      p.explanation,
      lr.generated_at,
      lr.detail AS run_detail
    FROM latest_run AS lr
    INNER JOIN predictions AS p
      ON p.prediction_run_id = lr.id
    ORDER BY p.horizon_hours ASC;
  `);

  return rows;
}

module.exports = {
  getLatestPredictions,
};
