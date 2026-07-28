const path = require("node:path");

const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const pinoHttp = require("pino-http");

const { env } = require("./config/env");
const {
  errorHandler,
} = require("./middleware/error-handler");
const {
  notFoundHandler,
} = require("./middleware/not-found");
const {
  analyticsRouter,
} = require("./routes/analytics");
const { healthRouter } = require("./routes/health");
const { nowRouter } = require("./routes/now");
const {
  privateAnalyticsRouter,
} = require("./routes/private-analytics");
const { todayRouter } = require("./routes/today");

const DEFAULT_CLIENT_DIST_PATH = path.resolve(
  __dirname,
  "../../client/dist",
);

function createApp({
  nodeEnv = env.nodeEnv,
  clientDistPath =
    DEFAULT_CLIENT_DIST_PATH,
  enableRequestLogging =
    nodeEnv !== "test",
  analyticsPrivateKey =
    env.analyticsPrivateKey,
} = {}) {
  const app = express();

  app.disable("x-powered-by");

  // Store the secret in application state so tests can inject
  // a temporary value without changing process environment.
  app.set(
    "analyticsPrivateKey",
    analyticsPrivateKey,
  );

  if (enableRequestLogging) {
    app.use(
      pinoHttp({
        level: env.logLevel,
      }),
    );
  }

  app.use(helmet());

  app.use(
    cors({
      origin: env.corsOrigin,
      methods: ["GET", "POST"],
    }),
  );

  app.use(
    express.json({
      limit: "16kb",
    }),
  );

  app.use("/api/v1", healthRouter);
  app.use("/api/v1", nowRouter);
  app.use("/api/v1", todayRouter);
  app.use("/api/v1", analyticsRouter);
  app.use(
    "/api/v1",
    privateAnalyticsRouter,
  );

  if (nodeEnv === "production") {
    const clientIndexPath = path.join(
      clientDistPath,
      "index.html",
    );

    app.use(
      express.static(
        clientDistPath,
        {
          index: false,
        },
      ),
    );

    // Only browser routes receive the SPA entry point.
    // Unknown API paths continue to the JSON 404 handler.
    app.use(
      (
        request,
        response,
        next,
      ) => {
        if (
          request.method !== "GET"
          || request.path.startsWith(
            "/api/",
          )
        ) {
          next();
          return;
        }

        response.sendFile(
          clientIndexPath,
          (error) => {
            if (error) {
              next(error);
            }
          },
        );
      },
    );
  }

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = {
  createApp,
};
