const express = require("express");

const {
  getLatestSuccessfulForecastSource,
} = require("../repositories/prediction-run-repository");

const router = express.Router();

// generated_at is the forecast's source market hour, not worker execution time.
router.get("/health", async (req, res) => {
  try {
    const latestForecastSource =
      await getLatestSuccessfulForecastSource();

    res.status(200).json({
      status: "ok",
      latestForecastSourceAt:
        latestForecastSource?.forecast_source_at
        ?? null,
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
