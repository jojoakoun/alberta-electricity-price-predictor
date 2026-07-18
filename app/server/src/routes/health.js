const express = require("express");

const router = express.Router();

// Return a minimal API liveness response.
router.get("/health", (req, res) => {
  res.status(200).json({
    status: "ok",
  });
});

module.exports = { healthRouter: router };
