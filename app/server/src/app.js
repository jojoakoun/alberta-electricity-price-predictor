const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const pinoHttp = require("pino-http");

const { env } = require("./config/env");
const { errorHandler } = require("./middleware/error-handler");
const { notFoundHandler } = require("./middleware/not-found");

function createApp() {
  const app = express();

  app.disable("x-powered-by");

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

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = { createApp };
