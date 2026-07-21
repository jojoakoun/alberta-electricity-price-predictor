const express = require("express");

const { getNow } = require("../services/now-service");

const router = express.Router();

// Now is derived from finalized observed market data, not a prediction run.
router.get("/now", async (req, res, next) => {
  try {
    const response = await getNow();

    if (!response) {
      return res.status(404).json({
        error: "No finalized observed price is available.",
      });
    }

    return res.status(200).json(response);
  } catch (error) {
    return next(error);
  }
});

module.exports = {
  nowRouter: router,
};
