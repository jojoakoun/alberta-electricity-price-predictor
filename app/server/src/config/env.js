const path = require("node:path");
const dotenv = require("dotenv");

dotenv.config({
  path: path.resolve(__dirname, "../../../../.env"),
  quiet: true,
});

function parsePort(value) {
  const port = Number.parseInt(value, 10);

  if (
    !Number.isInteger(port)
    || port < 1
    || port > 65535
  ) {
    throw new Error(
      "PORT must be an integer between 1 and 65535.",
    );
  }

  return port;
}

function parseDatabaseUrl(nodeEnv, value) {
  const databaseUrl = value?.trim() || "";

  if (
    nodeEnv === "production"
    && !databaseUrl
  ) {
    throw new Error(
      "DATABASE_URL is required in production.",
    );
  }

  return databaseUrl;
}

function createEnv(source = process.env) {
  const nodeEnv = source.NODE_ENV || "development";

  return Object.freeze({
    nodeEnv,
    host:
      source.API_HOST
      || (
        nodeEnv === "production"
          ? "0.0.0.0"
          : "127.0.0.1"
      ),
    port: parsePort(
      source.PORT
      || source.API_PORT
      || "8000",
    ),
    corsOrigin:
      source.CORS_ORIGIN
      || "http://localhost:5173",
    logLevel: source.LOG_LEVEL || "info",
    databaseUrl: parseDatabaseUrl(
      nodeEnv,
      source.DATABASE_URL,
    ),
  });
}

const env = createEnv();

module.exports = {
  createEnv,
  env,
};
