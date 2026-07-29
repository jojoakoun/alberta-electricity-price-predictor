const { pool } = require("../db/pool");

const MARKET_CONTEXT_LOOKBACK_HOURS = 24 * 30;

/**
 * Return the best market-price value for the current UTC hour.
 *
 * Preference order:
 * 1. finalized actual price for the current hour;
 * 2. AESO forecast price for the current hour;
 * 3. latest finalized actual price as an explicit fallback.
 */
async function getCurrentMarketPrice(
  viewedAt = new Date(),
) {
  const viewedDate = new Date(viewedAt);

  if (Number.isNaN(viewedDate.getTime())) {
    throw new TypeError(
      "Current market price requires a valid viewedAt date.",
    );
  }

  const { rows } = await pool.query(
    `
      WITH requested_hour AS (
        SELECT date_trunc(
          'hour',
          $1::timestamptz
        ) AS datetime_utc
      ),
      current_hour_price AS (
        SELECT
          hourly.datetime_utc,
          CASE
            WHEN hourly.actual_price IS NOT NULL
              THEN hourly.actual_price
            ELSE hourly.forecast_price
          END AS price,
          CASE
            WHEN hourly.actual_price IS NOT NULL
              THEN 'actual'
            ELSE 'forecast'
          END AS price_kind
        FROM hourly_prices AS hourly
        INNER JOIN requested_hour
          ON requested_hour.datetime_utc
            = hourly.datetime_utc
        WHERE
          hourly.actual_price IS NOT NULL
          OR hourly.forecast_price IS NOT NULL
      ),
      latest_finalized_price AS (
        SELECT
          hourly.datetime_utc,
          hourly.actual_price AS price,
          'fallback_actual' AS price_kind
        FROM hourly_prices AS hourly
        WHERE hourly.actual_price IS NOT NULL
        ORDER BY hourly.datetime_utc DESC
        LIMIT 1
      )
      SELECT
        datetime_utc,
        price,
        price_kind
      FROM current_hour_price

      UNION ALL

      SELECT
        datetime_utc,
        price,
        price_kind
      FROM latest_finalized_price
      WHERE NOT EXISTS (
        SELECT 1
        FROM current_hour_price
      )

      LIMIT 1;
    `,
    [
      viewedDate.toISOString(),
    ],
  );

  console.log(
    "DEBUG_HOURLY_QUERY",
    JSON.stringify({
      rowCount: rows.length,
      firstRow: rows[0] ?? null,
    }),
  );

  return rows[0] ?? null;
}

// Historical market context must use finalized observations only.
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
  getCurrentMarketPrice,
  getLatestFinalizedPrice,
  getRecentFinalizedPrices,
};
