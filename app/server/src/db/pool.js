const { Pool } = require("pg");

const { env } = require("../config/env");

function createPool(connectionString = env.databaseUrl) {
  if (!connectionString) {
    throw new Error("DATABASE_URL is required.");
  }

  return new Pool({
    connectionString,
    max: 10,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
  });
}

module.exports = { createPool };
