const { pool } = require("../db/pool");

// generated_at is the forecast's source market hour, not worker execution time.
async function getLatestSuccessfulForecastSource() {
  const { rows } = await pool.query(`
      SELECT generated_at AS forecast_source_at
      FROM prediction_runs
      WHERE status = 'success'
      ORDER BY generated_at DESC
      LIMIT 1
    `);

  return rows[0] ?? null;
}

module.exports = {
  getLatestSuccessfulForecastSource,
};
