const path = require("node:path");
const dotenv = require("dotenv");

dotenv.config({
  path: path.resolve(__dirname, "../../../../.env"),
  quiet: true,
});

function parsePort(value) {
  const port = Number.parseInt(value, 10);

  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("API_PORT must be an integer between 1 and 65535.");
  }

  return port;
}

const env = Object.freeze({
  nodeEnv: process.env.NODE_ENV || "development",
  host: process.env.API_HOST || "127.0.0.1",
  port: parsePort(process.env.API_PORT || "8000"),
  corsOrigin: process.env.CORS_ORIGIN || "http://localhost:5173",
  logLevel: process.env.LOG_LEVEL || "info",
});

module.exports = { env };
