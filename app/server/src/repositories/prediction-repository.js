const { pool } = require("../db/pool");

// Read the five predictions from one coherent successful worker run.
async function getLatestPredictions() {
  const { rows } = await pool.query(`
    WITH latest_run AS (
      SELECT
        id,
        generated_at
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
      lr.generated_at
    FROM latest_run AS lr
    INNER JOIN predictions AS p
      ON p.prediction_run_id = lr.id
    ORDER BY p.horizon_hours ASC;
  `);

  return rows;
}

// Read the latest finalized market price for the Now page.
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

// Read recent finalized prices for consumer-facing market context.
async function getRecentFinalizedPrices(limit = 720) {
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
