const express = require("express");

const { getNow } = require("../services/now-service");

const router = express.Router();

// Return the current WattWise recommendation.
router.get("/now", async (req, res, next) => {
  try {
    const response = await getNow();

    if (!response) {
      return res.status(404).json({
        error: "No prediction is available.",
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
