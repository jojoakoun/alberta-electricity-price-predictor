const express = require("express");

const {
  AnalyticsValidationError,
  recordAnalyticsEvent,
} = require("../services/analytics-service");

const router = express.Router();

router.post(
  "/analytics/events",
  async (request, response, next) => {
    try {
      await recordAnalyticsEvent(
        request.body,
      );

      return response.status(201).json({
        recorded: true,
      });
    } catch (error) {
      if (
        error instanceof AnalyticsValidationError
      ) {
        return response.status(400).json({
          error: {
            code: "INVALID_ANALYTICS_EVENT",
            message: error.message,
          },
        });
      }

      return next(error);
    }
  },
);

module.exports = {
  analyticsRouter: router,
};
