const crypto = require("node:crypto");
const express = require("express");

const {
  getPrivateAnalytics,
} = require("../services/private-analytics-service");

const router = express.Router();

function keysMatch(receivedKey, configuredKey) {
  const received = Buffer.from(
    String(receivedKey ?? ""),
  );

  const configured = Buffer.from(
    String(configuredKey ?? ""),
  );

  if (
    received.length === 0
    || received.length !== configured.length
  ) {
    return false;
  }

  return crypto.timingSafeEqual(
    received,
    configured,
  );
}

router.get(
  "/private/analytics",
  async (request, response, next) => {
    const configuredKey = (
      request.app.get("analyticsPrivateKey")
      ?? ""
    );

    if (!configuredKey) {
      return response.status(503).json({
        error: {
          code: "PRIVATE_ANALYTICS_UNAVAILABLE",
          message: "Private analytics is not configured.",
        },
      });
    }

    if (
      !keysMatch(
        request.get("X-Analytics-Key"),
        configuredKey,
      )
    ) {
      return response.status(401).json({
        error: {
          code: "UNAUTHORIZED",
          message: "A valid private analytics key is required.",
        },
      });
    }

    try {
      const analytics =
        await getPrivateAnalytics();

      return response.status(200).json(
        analytics,
      );
    } catch (error) {
      return next(error);
    }
  },
);

module.exports = {
  keysMatch,
  privateAnalyticsRouter: router,
};
