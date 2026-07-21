const { pool } = require("../db/pool");

const MARKET_CONTEXT_LOOKBACK_HOURS = 24 * 30;

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

// Forecast-only rows are excluded because Now must describe an observed price.
async function getLatestFinalizedPrice() {
  const { rows } = await pool.query(`
    SELECT
      datetime_utc,
      actual_price
    FROM hourly_prices
    WHERE actual_price IS NOT NULL
    ORDER BY datetime_utc DESC
    LIMIT 1;
  `);

  return rows[0] ?? null;
}

// Bound the query to the documented 30-day distribution used for market
// context; the outer order keeps the repository result chronological.
async function getRecentFinalizedPrices(
  limit = MARKET_CONTEXT_LOOKBACK_HOURS,
) {
  const { rows } = await pool.query(
    `
      SELECT actual_price
      FROM (
        SELECT
          datetime_utc,
          actual_price
        FROM hourly_prices
        WHERE actual_price IS NOT NULL
        ORDER BY datetime_utc DESC
        LIMIT $1
      ) AS recent
      ORDER BY datetime_utc ASC;
    `,
    [limit],
  );

  return rows;
}

module.exports = {
  getLatestFinalizedPrice,
  getLatestPredictions,
  getRecentFinalizedPrices,
};
