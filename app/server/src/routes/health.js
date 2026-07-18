const express = require("express");

const { pool } = require("../db/pool");

const router = express.Router();

// Confirm database access and report the latest successful worker run.
router.get("/health", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT generated_at
      FROM prediction_runs
      WHERE status = 'success'
      ORDER BY generated_at DESC
      LIMIT 1
    `);

    res.status(200).json({
      status: "ok",
      latestRunAt: result.rows[0]?.generated_at ?? null,
      dbOk: true,
    });
  } catch {
    res.status(503).json({
      status: "error",
      latestRunAt: null,
      dbOk: false,
    });
  }
});

module.exports = {
  healthRouter: router,
};
