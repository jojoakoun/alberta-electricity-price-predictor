const express = require("express");

const { getToday } = require("../services/today-service");

const router = express.Router();

// Return the five genuine forecasts from the latest successful run.
router.get("/today", async (req, res, next) => {
  try {
    const today = await getToday();

    if (!today) {
      return res.status(404).json({
        error: {
          code: "PREDICTIONS_NOT_FOUND",
          message: "No predictions are available.",
        },
      });
    }

    return res.status(200).json(today);
  } catch (error) {
    return next(error);
  }
});

module.exports = {
  todayRouter: router,
};
