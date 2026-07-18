const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const pinoHttp = require("pino-http");

const { env } = require("./config/env");
const { errorHandler } = require("./middleware/error-handler");
const { notFoundHandler } = require("./middleware/not-found");
const { healthRouter } = require("./routes/health");
const { nowRouter } = require("./routes/now");

function createApp() {
  const app = express();

  // Hide the Express signature from public responses.
  app.disable("x-powered-by");

  // Keep test output clean while preserving structured logs elsewhere.
  if (env.nodeEnv !== "test") {
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
      methods: ["GET"],
    }),
  );

  app.use(express.json({ limit: "16kb" }));

  app.use("/api/v1", healthRouter);
  app.use("/api/v1", nowRouter);

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = { createApp };
