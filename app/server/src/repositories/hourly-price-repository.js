const { pool } = require("../db/pool");

const MARKET_CONTEXT_LOOKBACK_HOURS = 24 * 30;

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
  getRecentFinalizedPrices,
};
