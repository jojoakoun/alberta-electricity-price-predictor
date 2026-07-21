const express = require("express");

const { pool } = require("../db/pool");

const router = express.Router();

// generated_at is the forecast's source market hour, not worker execution time.
router.get("/health", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT generated_at AS forecast_source_at
      FROM prediction_runs
      WHERE status = 'success'
      ORDER BY generated_at DESC
      LIMIT 1
    `);

    res.status(200).json({
      status: "ok",
      latestForecastSourceAt: result.rows[0]?.forecast_source_at ?? null,
      dbOk: true,
    });
  } catch {
    res.status(503).json({
      status: "error",
      latestForecastSourceAt: null,
      dbOk: false,
    });
  }
});

module.exports = {
  healthRouter: router,
};
